"""E2E tests for MedicationRequest resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

MEDICATIONS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.1.1"


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestMedicationConversion:
    """E2E tests for C-CDA Medication Activity to FHIR MedicationRequest conversion."""

    def test_converts_medication_code(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that medication code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "medicationCodeableConcept" in med_request
        rxnorm = next(
            (c for c in med_request["medicationCodeableConcept"]["coding"]
             if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm is not None
        assert rxnorm["code"] == "1190220"

    def test_converts_status(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["status"] == "active"

    def test_converts_intent(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that intent is correctly determined from moodCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["intent"] == "plan"

    def test_converts_authored_on(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that author time is converted to authoredOn."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "authoredOn" in med_request
        assert "2013-09-11" in med_request["authoredOn"]

    def test_converts_dosage_timing(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that timing is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert timing["period"] == 4
        assert timing["periodMax"] == 6
        assert timing["periodUnit"] == "h"

    def test_converts_route(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that route code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        route = med_request["dosageInstruction"][0]["route"]
        assert route["coding"][0]["code"] == "C38288"

    def test_converts_dose_quantity(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that dose quantity is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        dose = med_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
        assert dose["value"] == 1

    def test_converts_max_dose(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that max dose is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        max_dose = med_request["dosageInstruction"][0]["maxDosePerPeriod"]
        assert max_dose["numerator"]["value"] == 6

    def test_converts_as_needed(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that precondition is converted to asNeededCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        as_needed = med_request["dosageInstruction"][0]["asNeededCodeableConcept"]
        assert as_needed["coding"][0]["code"] == "56018004"

    def test_converts_reason_code(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "reasonCode" in med_request
        assert med_request["reasonCode"][0]["coding"][0]["code"] == "56018004"

    def test_converts_patient_instructions(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that instructions are converted to patientInstruction."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        assert med_request["dosageInstruction"][0]["patientInstruction"] == "Do not overtake"

    def test_resource_type_is_medication_request(
        self, ccda_medication: str, fhir_medication: dict[str, Any]
    ) -> None:
        """Test that the resource type is MedicationRequest."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["resourceType"] == "MedicationRequest"
