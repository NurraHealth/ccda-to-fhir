"""E2E tests for Condition resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

PROBLEMS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.5.1"


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestProblemConversion:
    """E2E tests for C-CDA Problem Concern Act to FHIR Condition conversion."""

    def test_converts_problem_code(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that the problem code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "code" in condition
        snomed = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "233604007"
        assert snomed["display"] == "Pneumonia"

    def test_converts_clinical_status(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that clinical status is correctly mapped from status observation."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "clinicalStatus" in condition
        assert condition["clinicalStatus"]["coding"][0]["code"] == "recurrence"

    def test_converts_category(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that category is set to problem-list-item."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "category" in condition
        assert condition["category"][0]["coding"][0]["code"] == "problem-list-item"

    def test_converts_onset_date(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that onset date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "onsetDateTime" in condition
        assert condition["onsetDateTime"] == "2012-08-06"

    def test_converts_onset_age(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that age at onset is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "onsetAge" in condition
        assert condition["onsetAge"]["value"] == 65
        assert condition["onsetAge"]["unit"] == "year"

    def test_converts_recorded_date(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that author time is converted to recordedDate."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recordedDate" in condition
        assert condition["recordedDate"] == "2014-01-04"

    def test_converts_icd_translations(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that ICD-9 and ICD-10 translations are included."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "code" in condition
        icd9 = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-9-cm"),
            None
        )
        assert icd9 is not None
        assert icd9["code"] == "486"

        icd10 = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"),
            None
        )
        assert icd10 is not None
        assert icd10["code"] == "J18.9"

    def test_converts_identifiers(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "identifier" in condition
        assert condition["identifier"][0]["value"] == "545069300001"

    def test_resource_type_is_condition(
        self, ccda_problem: str, fhir_problem: dict[str, Any]
    ) -> None:
        """Test that the resource type is Condition."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert condition["resourceType"] == "Condition"
