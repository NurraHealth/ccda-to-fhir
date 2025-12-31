"""E2E tests for Sex (US Core) Patient extension conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestSexExtension:
    """E2E tests for Sex observation to US Core Sex extension conversion."""

    def test_converts_sex_extension_male(self) -> None:
        """Test that sex observation maps to Patient.extension (male)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="46098-0" displayName="Sex"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="M" displayName="Male"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have us-core-sex extension
        assert "extension" in patient
        sex_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
            None
        )
        assert sex_ext is not None
        assert sex_ext["valueCode"] == "M"

    def test_converts_sex_extension_female(self) -> None:
        """Test that sex observation maps to Patient.extension (female)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="46098-0" displayName="Sex"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="F" displayName="Female"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        sex_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
            None
        )
        assert sex_ext is not None
        assert sex_ext["valueCode"] == "F"

    def test_converts_sex_extension_unknown(self) -> None:
        """Test that sex observation maps to Patient.extension (unknown)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="46098-0" displayName="Sex"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="UNK" displayName="Unknown"
                   codeSystem="2.16.840.1.113883.5.1008"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        sex_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
            None
        )
        assert sex_ext is not None
        assert sex_ext["valueCode"] == "UNK"

    def test_sex_extension_url_is_correct(self) -> None:
        """Test that the sex extension uses the correct US Core URL."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="46098-0" displayName="Sex"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="M" displayName="Male"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Verify extension URL is exactly correct
        sex_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
            None
        )
        assert sex_ext is not None
        assert sex_ext["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"

    def test_sex_observation_does_not_create_observation_resource(self) -> None:
        """Test that sex observation does NOT create a separate Observation resource."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="46098-0" displayName="Sex"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="M" displayName="Male"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Should NOT create a separate Observation resource for sex
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        sex_observations = [
            obs for obs in observations
            if obs.get("code", {}).get("coding", [{}])[0].get("code") == "46098-0"
        ]
        assert len(sex_observations) == 0, "Sex should NOT create an Observation resource"

    def test_converts_all_three_social_history_extensions_together(self) -> None:
        """Test birth sex, gender identity, and sex all map to Patient extensions."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient-id" extension="test-patient-id"/>
            <patient>
                <name><family>Patient</family><given>Test</given></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson><name><family>Author</family><given>Test</given></name></assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                <name>Test Hospital</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                    <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"/>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
                            <code code="76689-9" displayName="Sex assigned at birth"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="F" displayName="Female"
                                   codeSystem="2.16.840.1.113883.5.1"/>
                        </observation>
                    </entry>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="76691-5" displayName="Gender identity"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="446151000124109"
                                   displayName="Identifies as male"
                                   codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entry>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="46098-0" displayName="Sex"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="M" displayName="Male"
                                   codeSystem="2.16.840.1.113883.5.1"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient

        # Check birth sex extension
        birthsex_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
            None
        )
        assert birthsex_ext is not None
        assert birthsex_ext["valueCode"] == "F"

        # Check gender identity extension
        gender_id_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
            None
        )
        assert gender_id_ext is not None
        coding = gender_id_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "446151000124109"

        # Check sex extension
        sex_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
            None
        )
        assert sex_ext is not None
        assert sex_ext["valueCode"] == "M"

        # Verify NO Observation resources created for any of these
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        social_history_obs_codes = set()
        for obs in observations:
            if obs.get("code", {}).get("coding"):
                for coding in obs["code"]["coding"]:
                    social_history_obs_codes.add(coding.get("code"))

        assert "76689-9" not in social_history_obs_codes, "Birth sex should be extension only"
        assert "76691-5" not in social_history_obs_codes, "Gender identity should be extension only"
        assert "46098-0" not in social_history_obs_codes, "Sex should be extension only"

    def test_no_sex_extension_when_not_present(self) -> None:
        """Test that sex extension is not added when observation is absent."""
        ccda_doc = wrap_in_ccda_document("")  # No social history section
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Check that sex extension is not present
        if "extension" in patient:
            sex_ext = next(
                (e for e in patient["extension"]
                 if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"),
                None
            )
            assert sex_ext is None
