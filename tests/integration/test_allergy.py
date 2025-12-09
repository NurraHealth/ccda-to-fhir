"""E2E tests for AllergyIntolerance resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestAllergyConversion:
    """E2E tests for C-CDA Allergy Concern Act to FHIR AllergyIntolerance conversion."""

    def test_converts_allergy_code(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that the allergen code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "code" in allergy
        rxnorm_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm_coding is not None
        assert rxnorm_coding["code"] == "1191"
        assert rxnorm_coding["display"] == "Aspirin"

    def test_converts_clinical_status(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that clinical status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "clinicalStatus" in allergy
        assert allergy["clinicalStatus"]["coding"][0]["code"] == "active"
        assert allergy["clinicalStatus"]["coding"][0]["system"] == \
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"

    def test_converts_category(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that category is correctly determined."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "category" in allergy
        assert "medication" in allergy["category"]

    def test_converts_onset_date(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that onset date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "onsetDateTime" in allergy
        assert allergy["onsetDateTime"] == "2008-05-01"

    def test_converts_reaction_manifestation(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that reaction manifestation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) >= 1
        reaction = allergy["reaction"][0]
        assert "manifestation" in reaction

        snomed_coding = next(
            (c for c in reaction["manifestation"][0]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "247472004"
        assert snomed_coding["display"] == "Wheal"

    def test_converts_reaction_severity(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that reaction severity is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        reaction = allergy["reaction"][0]
        assert reaction["severity"] == "severe"

    def test_converts_identifiers(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "identifier" in allergy
        assert len(allergy["identifier"]) >= 1

    def test_converts_translation_codes(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that translation codes are included in code.coding."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "code" in allergy
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "293586001"

    def test_resource_type_is_allergy_intolerance(
        self, ccda_allergy: str, fhir_allergy: dict[str, Any]
    ) -> None:
        """Test that the resource type is AllergyIntolerance."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert allergy["resourceType"] == "AllergyIntolerance"
