"""E2E tests for Smoking Status Observation resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

SOCIAL_HISTORY_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.17"


def _find_smoking_status_observation(bundle: dict[str, Any]) -> dict[str, Any] | None:
    """Find the smoking status Observation in the bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") == "72166-2":
                    return resource
    return None


class TestSmokingStatusConversion:
    """E2E tests for C-CDA Smoking Status Observation to FHIR Observation conversion."""

    def test_resource_type_is_observation(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that the resource type is Observation."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["resourceType"] == "Observation"

    def test_converts_status(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that status is correctly mapped to final."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["status"] == "final"

    def test_converts_category(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that category is set to social-history."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["category"][0]["coding"][0]["code"] == "social-history"
        assert observation["category"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

    def test_converts_code(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that observation code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "code" in observation
        loinc = next(
            (c for c in observation["code"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "72166-2"
        assert loinc["display"] == "Tobacco smoking status NHIS"

    def test_converts_effective_datetime(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "effectiveDateTime" in observation
        assert "2014-06-06" in observation["effectiveDateTime"]

    def test_converts_value_codeable_concept(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that CD value is converted to valueCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "valueCodeableConcept" in observation
        snomed = next(
            (c for c in observation["valueCodeableConcept"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "449868002"
        assert snomed["display"] == "Current every day smoker"

    def test_converts_identifier(
        self, ccda_smoking_status: str, fhir_smoking_status: dict[str, Any]
    ) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "identifier" in observation
        assert observation["identifier"][0]["value"] == "123456789"
