"""Integration tests for Procedure with nullFlavor codes and sections.

Per HL7 C-CDA Examples, sections with nullFlavor="NI" should have no entries.
Procedures with nullFlavor codes and no extractable text should be skipped.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

PROCEDURES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.7.1"


def _find_all_resources_in_bundle(
    bundle: JSONObject, resource_type: str
) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


def _create_document_with_nullflavor_section(section_content: str) -> str:
    """Create a C-CDA document with a section that has nullFlavor='NI'.

    Per HL7 C-CDA Examples, sections with nullFlavor="NI" should have no entries.
    This helper creates a document to test that entries in such sections are skipped.
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient-id"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson>
                <name><given>Test</given><family>Author</family></name>
            </assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.19.5"/>
                <name>Test Organization</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section nullFlavor="NI">
                    <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.2.7.1"/>
                    <templateId root="2.16.840.1.113883.10.20.22.2.7.1"/>
                    <id root="74d43216-2761-4d32-ae55-23bfee545df3"/>
                    <code code="47519-4" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
                    <title>Procedures</title>
                    <text>
                        <content>Surgical History</content>
                        <paragraph>None recorded.</paragraph>
                    </text>
                    """ + section_content + """
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""


class TestProcedureNullFlavor:
    """Tests for Procedure with nullFlavor codes.

    Per FHIR R4 spec, Procedure.code is required (1..1).
    Procedures with nullFlavor codes and no extractable text should be skipped.
    """

    def test_procedure_with_nullflavor_code_and_no_text_is_skipped(self) -> None:
        """Test that procedure observation with nullFlavor code and no text is skipped.

        Per FHIR R4: Procedure.code is required (1..1).
        When code has nullFlavor and no text is available, the procedure
        cannot be converted to valid FHIR and should be skipped.
        """
        ccda = """
<observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.13"/>
    <templateId root="2.16.840.1.113883.10.20.22.4.13"/>
    <id root="720e07e2-1df1-4c70-a687-63574ca115e4"/>
    <code nullFlavor="NI"/>
    <statusCode code="active"/>
    <effectiveTime nullFlavor="NI"/>
    <value nullFlavor="NI" xsi:type="CD"/>
</observation>
"""
        ccda_doc = wrap_in_ccda_document(ccda, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Procedure with nullFlavor code and no text should be skipped
        assert len(procedures) == 0, (
            "Procedure with nullFlavor code and no text should be skipped"
        )

    def test_procedure_activity_procedure_with_nullflavor_code_is_skipped(self) -> None:
        """Test that procedure activity procedure with nullFlavor code is skipped."""
        ccda = """
<procedure classCode="PROC" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.14"/>
    <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
    <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
    <code nullFlavor="NI"/>
    <statusCode code="completed"/>
    <effectiveTime nullFlavor="NI"/>
</procedure>
"""
        ccda_doc = wrap_in_ccda_document(ccda, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Procedure with nullFlavor code and no text should be skipped
        assert len(procedures) == 0, (
            "Procedure Activity Procedure with nullFlavor code should be skipped"
        )

    def test_procedure_activity_act_with_nullflavor_code_is_skipped(self) -> None:
        """Test that procedure activity act with nullFlavor code is skipped."""
        ccda = """
<act classCode="ACT" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.12"/>
    <templateId root="2.16.840.1.113883.10.20.22.4.12"/>
    <id root="act-nullflavor-1"/>
    <code nullFlavor="NI"/>
    <statusCode code="completed"/>
    <effectiveTime nullFlavor="NI"/>
</act>
"""
        ccda_doc = wrap_in_ccda_document(ccda, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Procedure with nullFlavor code and no text should be skipped
        assert len(procedures) == 0, (
            "Procedure Activity Act with nullFlavor code should be skipped"
        )

    def test_valid_procedure_is_created(self) -> None:
        """Test that procedure with valid code is created normally.

        This is a control test to ensure that valid procedures work as expected.
        """
        ccda = """
<procedure classCode="PROC" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.14"/>
    <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
    <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
    <code code="73761001" codeSystem="2.16.840.1.113883.6.96" displayName="Colonoscopy"/>
    <statusCode code="completed"/>
    <effectiveTime value="20230315"/>
</procedure>
"""
        ccda_doc = wrap_in_ccda_document(ccda, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Should have exactly one procedure
        assert len(procedures) == 1, "Should have one procedure"

        procedure = procedures[0]
        assert procedure["status"] == "completed"
        assert "code" in procedure
        assert procedure["code"]["coding"][0]["code"] == "73761001"
        assert procedure["code"]["coding"][0]["display"] == "Colonoscopy"


class TestSectionNullFlavor:
    """Tests for sections with nullFlavor="NI".

    Per HL7 C-CDA Examples, sections with nullFlavor="NI" should have no entries.
    If entries exist in such sections, they are malformed placeholder data and
    should be skipped.

    Reference: https://github.com/HL7/C-CDA-Examples/blob/master/General/No%20Section%20Information%20Problems/
    """

    def test_section_with_nullflavor_ni_skips_all_entries(self) -> None:
        """Test that entries in a section with nullFlavor='NI' are skipped.

        Per HL7 C-CDA Examples, a section with nullFlavor="NI" should have no entries.
        This tests the exact pattern from Greg's feedback - a Procedures section with
        nullFlavor="NI" containing placeholder observation entries.
        """
        entry_content = """
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.13"/>
                            <templateId root="2.16.840.1.113883.10.20.22.4.13"/>
                            <id root="720e07e2-1df1-4c70-a687-63574ca115e4"/>
                            <code nullFlavor="NI"/>
                            <statusCode code="active"/>
                            <effectiveTime nullFlavor="NI"/>
                            <value nullFlavor="NI" xsi:type="CD"/>
                        </observation>
                    </entry>
"""
        ccda_doc = _create_document_with_nullflavor_section(entry_content)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Section with nullFlavor="NI" should skip all entries
        assert len(procedures) == 0, (
            "Entries in section with nullFlavor='NI' should be skipped entirely"
        )

    def test_section_with_nullflavor_ni_skips_even_valid_entries(self) -> None:
        """Test that even valid entries in a nullFlavor='NI' section are skipped.

        If a section declares nullFlavor="NI", it means "no information".
        Even if there are entries with valid codes, they should be skipped
        because the section explicitly declares no information.
        """
        entry_content = """
                    <entry>
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId extension="2014-06-09" root="2.16.840.1.113883.10.20.22.4.14"/>
                            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
                            <code code="73761001" codeSystem="2.16.840.1.113883.6.96" displayName="Colonoscopy"/>
                            <statusCode code="completed"/>
                            <effectiveTime value="20230315"/>
                        </procedure>
                    </entry>
"""
        ccda_doc = _create_document_with_nullflavor_section(entry_content)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all procedures
        procedures = _find_all_resources_in_bundle(bundle, "Procedure")

        # Section with nullFlavor="NI" should skip all entries, even valid ones
        assert len(procedures) == 0, (
            "Even valid entries in section with nullFlavor='NI' should be skipped"
        )
