"""E2E tests for No Known Allergies using negated concept codes."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestNoKnownAllergies:
    """E2E tests for No Known Allergies with negated concept codes."""

    def test_no_known_allergy_general_creates_correct_code(self) -> None:
        """Test that no known allergy creates SNOMED code 716186003."""
        with open("tests/integration/fixtures/ccda/no_known_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None, "AllergyIntolerance resource not found"

        # Verify negated concept code
        assert "code" in allergy
        assert "coding" in allergy["code"]
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "716186003"
        assert snomed_coding["display"] == "No known allergy"

    def test_no_known_drug_allergy_creates_correct_code(self) -> None:
        """Test that no known drug allergy creates SNOMED code 409137002."""
        with open("tests/integration/fixtures/ccda/no_known_drug_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None, "AllergyIntolerance resource not found"

        # Verify negated concept code
        assert "code" in allergy
        assert "coding" in allergy["code"]
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "409137002"
        assert snomed_coding["display"] == "No known drug allergy"

    def test_no_known_food_allergy_creates_correct_code(self) -> None:
        """Test that no known food allergy creates SNOMED code 429625007."""
        with open("tests/integration/fixtures/ccda/no_known_food_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None, "AllergyIntolerance resource not found"

        # Verify negated concept code
        assert "code" in allergy
        assert "coding" in allergy["code"]
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "429625007"
        assert snomed_coding["display"] == "No known food allergy"

    def test_no_known_environmental_allergy_creates_correct_code(self) -> None:
        """Test that no known environmental allergy creates SNOMED code 428607008."""
        with open("tests/integration/fixtures/ccda/no_known_environmental_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None, "AllergyIntolerance resource not found"

        # Verify negated concept code
        assert "code" in allergy
        assert "coding" in allergy["code"]
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "428607008"
        assert snomed_coding["display"] == "No known environmental allergy"

    def test_no_known_allergy_has_confirmed_verification_status(self) -> None:
        """Test that no known allergies have verificationStatus 'confirmed' (not 'refuted')."""
        with open("tests/integration/fixtures/ccda/no_known_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify verificationStatus is confirmed (not refuted)
        assert "verificationStatus" in allergy
        assert allergy["verificationStatus"]["coding"][0]["code"] == "confirmed"
        assert (
            allergy["verificationStatus"]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
        )

    def test_no_known_allergy_has_active_clinical_status(self) -> None:
        """Test that no known allergies have clinicalStatus 'active'."""
        with open("tests/integration/fixtures/ccda/no_known_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify clinicalStatus is active
        assert "clinicalStatus" in allergy
        assert allergy["clinicalStatus"]["coding"][0]["code"] == "active"
        assert (
            allergy["clinicalStatus"]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
        )

    def test_no_known_drug_allergy_has_correct_type_and_category(self) -> None:
        """Test that no known drug allergy has correct type and category."""
        with open("tests/integration/fixtures/ccda/no_known_drug_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify type and category from observation value
        assert "type" in allergy
        assert allergy["type"] == "allergy"
        assert "category" in allergy
        assert "medication" in allergy["category"]

    def test_no_known_food_allergy_has_correct_type_and_category(self) -> None:
        """Test that no known food allergy has correct type and category."""
        with open("tests/integration/fixtures/ccda/no_known_food_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify type and category from observation value
        assert "type" in allergy
        assert allergy["type"] == "allergy"
        assert "category" in allergy
        assert "food" in allergy["category"]

    def test_no_known_environmental_allergy_has_correct_type_and_category(self) -> None:
        """Test that no known environmental allergy has correct type and category."""
        with open("tests/integration/fixtures/ccda/no_known_environmental_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify type and category from observation value
        assert "type" in allergy
        assert allergy["type"] == "allergy"
        assert "category" in allergy
        assert "environment" in allergy["category"]

    def test_no_known_allergy_metadata_preserved(self) -> None:
        """Test that no known allergy preserves identifiers and other metadata."""
        with open("tests/integration/fixtures/ccda/no_known_allergy.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            allergy_xml,
            section_template_id=ALLERGIES_TEMPLATE_ID,
            section_code="48765-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify basic metadata
        assert allergy["resourceType"] == "AllergyIntolerance"
        assert "id" in allergy
        assert "identifier" in allergy
        assert "patient" in allergy
