"""Unit tests for ClinicalDocument validation.

Tests C-CDA conformance validation for:
- US Realm Header (2.16.840.1.113883.10.20.22.1.1)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import ClinicalDocument
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestUSRealmHeaderValidation:
    """Tests for US Realm Header conformance validation."""

    def test_valid_us_realm_header(self) -> None:
        """Valid US Realm Header should pass all checks."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3"
                         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.2"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Summarization of Episode Note"/>
            <title>Continuity of Care Document</title>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                    <patient>
                        <name>
                            <given>John</given>
                            <family>Doe</family>
                        </name>
                    </patient>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Smith</family>
                        </name>
                    </assignedPerson>
                </assignedAuthor>
            </author>
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="2.16.840.1.113883.19.5"/>
                        <name>Good Health Clinic</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        </ClinicalDocument>
        """
        doc = parse_ccda_fragment(xml, ClinicalDocument)
        assert doc is not None
        assert doc.realm_code[0].code == "US"
        assert doc.type_id.root == "2.16.840.1.113883.1.3"

    def test_non_us_realm_document_skips_validation(self) -> None:
        """Document without US Realm Header template should skip validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <templateId root="1.2.3.4.5"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
        </ClinicalDocument>
        """
        # Should not raise validation error
        doc = parse_ccda_fragment(xml, ClinicalDocument)
        assert doc is not None

    def test_us_realm_header_missing_realm_code(self) -> None:
        """US Realm Header without realmCode should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*realmCode"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_wrong_realm_code(self) -> None:
        """US Realm Header with non-US realmCode should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="CA"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="realmCode SHALL be 'US'"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_type_id(self) -> None:
        """US Realm Header without typeId should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*typeId"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_wrong_type_id_root(self) -> None:
        """US Realm Header with wrong typeId root should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="1.2.3.4" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="typeId root SHALL be '2.16.840.1.113883.1.3'"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_wrong_type_id_extension(self) -> None:
        """US Realm Header with wrong typeId extension should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="WRONG"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="typeId extension SHALL be 'POCD_HD000040'"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_id(self) -> None:
        """US Realm Header without id should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*id"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_code(self) -> None:
        """US Realm Header without code should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_effective_time(self) -> None:
        """US Realm Header without effectiveTime should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_confidentiality_code(self) -> None:
        """US Realm Header without confidentialityCode should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*confidentialityCode"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_record_target(self) -> None:
        """US Realm Header without recordTarget should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*recordTarget"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_author(self) -> None:
        """US Realm Header without author should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
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
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*author"):
            parse_ccda_fragment(xml, ClinicalDocument)

    def test_us_realm_header_missing_custodian(self) -> None:
        """US Realm Header without custodian should fail validation."""
        xml = """
        <ClinicalDocument xmlns="urn:hl7-org:v3">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <recordTarget>
                <patientRole>
                    <id root="2.16.840.1.113883.19.5" extension="12345"/>
                </patientRole>
            </recordTarget>
            <author>
                <time value="20231201120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="999"/>
                </assignedAuthor>
            </author>
        </ClinicalDocument>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*custodian"):
            parse_ccda_fragment(xml, ClinicalDocument)
