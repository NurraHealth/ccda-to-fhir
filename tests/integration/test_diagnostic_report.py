"""Integration tests for DiagnosticReport resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


def _find_all_resources_in_bundle(bundle: JSONObject, resource_type: str) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


# Minimal valid observation component for Result Organizers
_MINIMAL_OBSERVATION_COMPONENT = """
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="minimal" extension="1"/>
                    <code code="2345-7" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="95" unit="mg/dL"/>
                </observation>
            </component>"""


class TestDiagnosticReportConversion:
    """Integration tests for C-CDA Result Organizer to FHIR DiagnosticReport conversion."""

    def test_converts_result_organizer_to_diagnostic_report(self) -> None:
        """Test that Result Organizer converts to DiagnosticReport."""
        result_organizer = """
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test-organizer" extension="12345"/>
            <code code="24323-8" displayName="Comprehensive metabolic 2000 panel"
                  codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231215"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="test-obs" extension="67890"/>
                    <code code="2345-7" displayName="Glucose"
                          codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="95" unit="mg/dL"/>
                </observation>
            </component>
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        diagnostic_report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert diagnostic_report is not None
        assert diagnostic_report["resourceType"] == "DiagnosticReport"

    def test_diagnostic_report_has_required_fields(self) -> None:
        """Test that DiagnosticReport has all required fields."""
        result_organizer = """
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test-organizer" extension="report-123"/>
            <code code="24323-8" displayName="Comprehensive metabolic 2000 panel"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231215"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="test-obs" extension="1"/>
                    <code code="2345-7" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="95" unit="mg/dL"/>
                </observation>
            </component>
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None

        # Required fields per FHIR spec
        assert "status" in dr
        assert dr["status"] == "final"
        assert "code" in dr
        assert "code" in dr["code"]["coding"][0]

    def test_diagnostic_report_status_mapping(self) -> None:
        """Test that C-CDA status codes map correctly to FHIR."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="status-test"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert dr["status"] == "final"  # completed → final

    def test_diagnostic_report_has_lab_category(self) -> None:
        """Test that DiagnosticReport has LAB category."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="cat-test"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert "category" in dr
        assert len(dr["category"]) > 0
        category_coding = dr["category"][0]["coding"][0]
        assert category_coding["code"] == "LAB"
        assert category_coding["display"] == "Laboratory"

    def test_diagnostic_report_code_from_organizer(self) -> None:
        """Test that panel code comes from Result Organizer."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="code-test"/>
            <code code="58410-2" displayName="Complete blood count panel"
                  codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
            <statusCode code="completed"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert "code" in dr
        coding = dr["code"]["coding"][0]
        assert coding["system"] == "http://loinc.org"
        assert coding["code"] == "58410-2"
        assert coding["display"] == "Complete blood count panel"

    def test_diagnostic_report_effective_datetime(self) -> None:
        """Test that effectiveTime maps to effectiveDateTime."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="time-test"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231225120000-0500"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert "effectiveDateTime" in dr
        # Should preserve date precision from C-CDA
        assert "2023-12-25" in dr["effectiveDateTime"]

    def test_diagnostic_report_contains_result_observations(self) -> None:
        """Test that DiagnosticReport contains result observations."""
        result_organizer = """
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="results-test"/>
            <code code="24323-8" displayName="CMP" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="obs" extension="glucose"/>
                    <code code="2345-7" displayName="Glucose" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="95" unit="mg/dL"/>
                </observation>
            </component>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="obs" extension="sodium"/>
                    <code code="2951-2" displayName="Sodium" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="140" unit="mmol/L"/>
                </observation>
            </component>
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None

        # Should have contained observations
        assert "contained" in dr
        assert len(dr["contained"]) == 2
        assert all(obs["resourceType"] == "Observation" for obs in dr["contained"])

        # Should have result references
        assert "result" in dr
        assert len(dr["result"]) == 2
        # References should point to contained resources
        assert all(ref["reference"].startswith("#") for ref in dr["result"])

    def test_diagnostic_report_observation_values(self) -> None:
        """Test that contained observations have correct values."""
        result_organizer = """
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="values-test"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="obs" extension="creatinine"/>
                    <code code="2160-0" displayName="Creatinine" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231215"/>
                    <value xsi:type="PQ" value="1.2" unit="mg/dL"/>
                </observation>
            </component>
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None

        obs = dr["contained"][0]
        assert obs["code"]["coding"][0]["code"] == "2160-0"
        assert obs["code"]["coding"][0]["display"] == "Creatinine"
        assert "valueQuantity" in obs
        assert obs["valueQuantity"]["value"] == 1.2
        assert obs["valueQuantity"]["unit"] == "mg/dL"

    def test_diagnostic_report_identifier(self) -> None:
        """Test that DiagnosticReport has identifier from organizer."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="2.16.840.1.113883.19.5" extension="LAB-2023-12345"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert "identifier" in dr
        assert len(dr["identifier"]) > 0
        identifier = dr["identifier"][0]
        assert "value" in identifier
        assert identifier["value"] == "LAB-2023-12345"

    def test_diagnostic_report_subject_reference(self) -> None:
        """Test that DiagnosticReport has subject reference to Patient."""
        result_organizer = f"""
        <organizer classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test" extension="subject-test"/>
            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            {_MINIMAL_OBSERVATION_COMPONENT}
        </organizer>
        """
        ccda_doc = wrap_in_ccda_document(
            result_organizer,
            section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
            section_code="30954-2"
        )
        bundle = convert_document(ccda_doc)

        dr = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert dr is not None
        assert "subject" in dr
        assert "reference" in dr["subject"]
        assert dr["subject"]["reference"].startswith("Patient/")

    def test_multiple_result_organizers_create_multiple_diagnostic_reports(self) -> None:
        """Test that multiple Result Organizers create multiple DiagnosticReports."""
        # Create custom document with two result organizers
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <id root="test-doc"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient"/>
            <patient>
                <name><family>Test</family><given>Patient</given></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson><name><family>Doc</family></name></assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="test-org"/>
                <name>Test Hospital</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
                    <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
                    <title>Results</title>
                    <entry>
                        <organizer classCode="CLUSTER" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
                            <id root="organizer1"/>
                            <code code="24323-8" codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <component>
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                    <id root="o1" extension="1"/>
                                    <code code="2345-7" codeSystem="2.16.840.1.113883.6.1"/>
                                    <statusCode code="completed"/>
                                    <effectiveTime value="20231215"/>
                                    <value xsi:type="PQ" value="95" unit="mg/dL"/>
                                </observation>
                            </component>
                        </organizer>
                    </entry>
                    <entry>
                        <organizer classCode="CLUSTER" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
                            <id root="organizer2"/>
                            <code code="58410-2" codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <component>
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                    <id root="o2" extension="1"/>
                                    <code code="6690-2" codeSystem="2.16.840.1.113883.6.1"/>
                                    <statusCode code="completed"/>
                                    <effectiveTime value="20231215"/>
                                    <value xsi:type="PQ" value="14" unit="g/dL"/>
                                </observation>
                            </component>
                        </organizer>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""
        bundle = convert_document(ccda_doc)

        diagnostic_reports = _find_all_resources_in_bundle(bundle, "DiagnosticReport")
        assert len(diagnostic_reports) == 2

        # Verify they have different codes
        codes = [dr["code"]["coding"][0]["code"] for dr in diagnostic_reports]
        assert "24323-8" in codes
        assert "58410-2" in codes
