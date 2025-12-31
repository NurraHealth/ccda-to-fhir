"""Integration tests for C-CDA document parsing and validation.

Tests complete C-CDA documents from real-world samples to ensure:
- Documents parse successfully end-to-end
- US Realm Header validation works
- Section and entry parsing works
- Template-based validation is applied
- Error handling works for invalid documents
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccda_to_fhir.ccda.models import ClinicalDocument
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda
from ccda_to_fhir.convert import convert_document

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestRealWorldDocuments:
    """Test parsing and conversion of real-world C-CDA documents."""

    def test_parse_practice_fusion_alice_newman(self) -> None:
        """Parse and convert complete Practice Fusion CCD for Alice Newman."""
        xml_path = FIXTURES_DIR / "practice_fusion_alice_newman.xml"
        xml = xml_path.read_text()

        # Should parse successfully
        doc = parse_ccda(xml)

        assert doc is not None
        assert isinstance(doc, ClinicalDocument)

        # Verify US Realm Header elements
        assert doc.realm_code is not None
        assert len(doc.realm_code) == 1
        assert doc.realm_code[0].code == "US"

        assert doc.type_id is not None
        assert doc.type_id.root == "2.16.840.1.113883.1.3"
        assert doc.type_id.extension == "POCD_HD000040"

        # Verify document identification
        assert doc.id is not None
        assert doc.code is not None
        assert doc.code.code == "34133-9"  # CCD document type

        # Verify header elements
        assert doc.effective_time is not None
        assert doc.confidentiality_code is not None
        assert doc.record_target is not None
        assert len(doc.record_target) >= 1

        # Verify patient information
        patient_role = doc.record_target[0].patient_role
        assert patient_role is not None
        assert patient_role.patient is not None
        assert patient_role.patient.name is not None
        assert len(patient_role.patient.name) >= 1

        # Verify author exists
        assert doc.author is not None
        assert len(doc.author) >= 1

        # Verify custodian exists
        assert doc.custodian is not None

        # Test conversion to FHIR
        bundle = convert_document(xml)["bundle"]

        assert bundle is not None
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert "entry" in bundle
        assert len(bundle["entry"]) > 0

        # First entry must be Composition
        first_resource = bundle["entry"][0]["resource"]
        assert first_resource["resourceType"] == "Composition"

        # Bundle should contain a Patient resource
        resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
        assert "Patient" in resource_types
        assert "Composition" in resource_types

    def test_parse_practice_fusion_jeremy_bates(self) -> None:
        """Parse and convert complete Practice Fusion CCD for Jeremy Bates."""
        xml_path = FIXTURES_DIR / "practice_fusion_jeremy_bates.xml"
        xml = xml_path.read_text()

        # Should parse successfully
        doc = parse_ccda(xml)

        assert doc is not None
        assert isinstance(doc, ClinicalDocument)

        # Verify it's a valid US Realm document
        assert doc.realm_code is not None
        assert doc.realm_code[0].code == "US"

        # Verify required header elements exist
        assert doc.id is not None
        assert doc.code is not None
        assert doc.effective_time is not None
        assert doc.confidentiality_code is not None
        assert doc.record_target is not None
        assert doc.author is not None
        assert doc.custodian is not None

        # Test conversion to FHIR
        bundle = convert_document(xml)["bundle"]

        assert bundle is not None
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert "entry" in bundle

        # First entry must be Composition
        first_resource = bundle["entry"][0]["resource"]
        assert first_resource["resourceType"] == "Composition"

        # Bundle should contain a Patient resource
        resource_types = [entry["resource"]["resourceType"] for entry in bundle["entry"]]
        assert "Patient" in resource_types


class TestDocumentSections:
    """Test that document sections parse correctly."""

    def test_document_has_component_section(self) -> None:
        """Verify document has structured body with sections."""
        xml_path = FIXTURES_DIR / "practice_fusion_alice_newman.xml"
        xml = xml_path.read_text()

        doc = parse_ccda(xml)

        # Most CCDs have a component with structuredBody
        assert doc.component is not None
        assert doc.component.structured_body is not None

        # Should have sections
        assert doc.component.structured_body.component is not None
        assert len(doc.component.structured_body.component) > 0

        # Each component should have a section
        for comp in doc.component.structured_body.component:
            assert comp.section is not None


class TestValidationErrors:
    """Test that validation errors are caught properly."""

    def test_invalid_realm_code_raises_error(self) -> None:
        """Document with invalid realmCode should fail validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="UK"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="123"/>
                    <patient>
                        <name><given>Test</given><family>Patient</family></name>
                    </patient>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="456"/>
                </assignedAuthor>
            </author>
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="2.16.840.1.113883.19.5"/>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError, match="realmCode SHALL be 'US'"):
            parse_ccda(xml)

    def test_missing_type_id_raises_error(self) -> None:
        """Document missing typeId should fail validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="US"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="123"/>
                    <patient>
                        <name><given>Test</given><family>Patient</family></name>
                    </patient>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="456"/>
                </assignedAuthor>
            </author>
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="2.16.840.1.113883.19.5"/>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError, match="SHALL contain exactly one.*typeId"):
            parse_ccda(xml)

    def test_missing_record_target_raises_error(self) -> None:
        """Document missing recordTarget should fail validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <author>
                <time value="20231201"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="456"/>
                </assignedAuthor>
            </author>
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="2.16.840.1.113883.19.5"/>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError, match="SHALL contain at least one.*recordTarget"):
            parse_ccda(xml)

    def test_missing_author_raises_error(self) -> None:
        """Document missing author should fail validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="123"/>
                    <patient>
                        <name><given>Test</given><family>Patient</family></name>
                    </patient>
                </patientRole>
            </recordTarget>
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="2.16.840.1.113883.19.5"/>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError, match="SHALL contain at least one.*author"):
            parse_ccda(xml)

    def test_missing_custodian_raises_error(self) -> None:
        """Document missing custodian should fail validation."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="123"/>
                    <patient>
                        <name><given>Test</given><family>Patient</family></name>
                    </patient>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="456"/>
                </assignedAuthor>
            </author>
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError, match="SHALL contain exactly one.*custodian"):
            parse_ccda(xml)


class TestMalformedDocuments:
    """Test error handling for malformed XML."""

    def test_invalid_xml_raises_error(self) -> None:
        """Malformed XML should raise MalformedXMLError."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"
        </ClinicalDocument>
        """

        with pytest.raises(MalformedXMLError):
            parse_ccda(xml)

    def test_empty_document_raises_error(self) -> None:
        """Empty document should raise error."""
        xml = ""

        with pytest.raises(MalformedXMLError):
            parse_ccda(xml)
