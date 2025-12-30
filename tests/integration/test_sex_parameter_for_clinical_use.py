"""E2E tests for Sex Parameter for Clinical Use Patient extension conversion."""

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


class TestSexParameterForClinicalUseExtension:
    """E2E tests for Sex Parameter for Clinical Use observation to Patient extension conversion."""

    def test_converts_spcu_extension_female_typical_by_loinc(self) -> None:
        """Test that SPCU observation maps to Patient extension (female-typical, LOINC match)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240101"/>
            <value xsi:type="CD" code="female-typical"
                   displayName="Apply female-typical setting or reference range"
                   codeSystem="2.16.840.1.113883.4.642.4.2038"/>
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

        # Should have patient-sexParameterForClinicalUse extension
        assert "extension" in patient
        spcu_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None

        # Check it's a complex extension with sub-extensions
        assert "extension" in spcu_ext

        # Check value sub-extension
        value_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "value"),
            None
        )
        assert value_ext is not None
        assert "valueCodeableConcept" in value_ext
        coding = value_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "female-typical"
        # Per FHIR R4B: CodeSystem canonical URI, not OID format
        assert coding["system"] == "http://hl7.org/fhir/sex-parameter-for-clinical-use"

        # Check period sub-extension
        period_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "period"),
            None
        )
        assert period_ext is not None
        assert "valuePeriod" in period_ext
        assert period_ext["valuePeriod"]["start"] == "2024-01-01"

    def test_converts_spcu_extension_male_typical_by_template(self) -> None:
        """Test that SPCU observation maps to Patient extension (male-typical, template match)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.513" extension="2025-05-01"/>
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240615120000-0500"/>
            <value xsi:type="CD" code="male-typical"
                   displayName="Apply male-typical setting or reference range"
                   codeSystem="2.16.840.1.113883.4.642.4.2038"/>
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

        spcu_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None

        value_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "value"),
            None
        )
        assert value_ext is not None
        coding = value_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "male-typical"

        # Check period with timestamp
        period_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "period"),
            None
        )
        assert period_ext is not None
        assert period_ext["valuePeriod"]["start"] == "2024-06-15T12:00:00-05:00"

    def test_spcu_extension_with_comment(self) -> None:
        """Test that SPCU extension includes comment from text element."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240101"/>
            <value xsi:type="CD" code="specified"
                   displayName="Apply specified setting or reference range"
                   codeSystem="2.16.840.1.113883.4.642.4.2038"/>
            <text value="Based on current hormone therapy and clinical presentation"/>
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

        spcu_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None

        # Check comment sub-extension
        comment_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "comment"),
            None
        )
        assert comment_ext is not None
        assert "valueString" in comment_ext
        assert comment_ext["valueString"] == "Based on current hormone therapy and clinical presentation"

    def test_spcu_extension_without_period(self) -> None:
        """Test that SPCU extension works without effectiveTime (no period)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="unknown" displayName="Unknown"
                   codeSystem="2.16.840.1.113883.4.642.4.1048"/>
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

        spcu_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None

        # Should have value but not period
        value_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "value"),
            None
        )
        assert value_ext is not None

        period_ext = next(
            (e for e in spcu_ext["extension"] if e["url"] == "period"),
            None
        )
        assert period_ext is None

    def test_spcu_extension_with_all_sub_extensions(self) -> None:
        """Test that SPCU extension can have value, period, and comment together."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240301"/>
            <value xsi:type="CD" code="female-typical"
                   displayName="Apply female-typical setting or reference range"
                   codeSystem="2.16.840.1.113883.4.642.4.2038"/>
            <text value="Post-transition, currently on HRT"/>
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

        spcu_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None

        # Should have all three sub-extensions
        value_ext = next((e for e in spcu_ext["extension"] if e["url"] == "value"), None)
        assert value_ext is not None

        period_ext = next((e for e in spcu_ext["extension"] if e["url"] == "period"), None)
        assert period_ext is not None

        comment_ext = next((e for e in spcu_ext["extension"] if e["url"] == "comment"), None)
        assert comment_ext is not None

    def test_spcu_observation_does_not_create_observation_resource(self) -> None:
        """Test that SPCU observation does NOT create a separate Observation resource."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240101"/>
            <value xsi:type="CD" code="female-typical"
                   displayName="Apply female-typical setting or reference range"
                   codeSystem="2.16.840.1.113883.4.642.4.2038"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Should NOT create a separate Observation resource for SPCU
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        spcu_observations = [
            obs for obs in observations
            if obs.get("code", {}).get("coding", [{}])[0].get("code") == "99501-9"
        ]
        assert len(spcu_observations) == 0, "SPCU should NOT create an Observation resource"

    def test_spcu_extension_url_is_correct(self) -> None:
        """Test that the SPCU extension uses the correct FHIR URL."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="99501-9" displayName="Sex parameter for clinical use"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="unknown" displayName="Unknown"
                   codeSystem="2.16.840.1.113883.4.642.4.1048"/>
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
        spcu_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
            None
        )
        assert spcu_ext is not None
        assert spcu_ext["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"

    def test_no_spcu_extension_when_not_present(self) -> None:
        """Test that SPCU extension is not added when observation is absent."""
        ccda_doc = wrap_in_ccda_document("")  # No social history section
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Check that SPCU extension is not present
        if "extension" in patient:
            spcu_ext = next(
                (e for e in patient["extension"]
                 if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"),
                None
            )
            assert spcu_ext is None
