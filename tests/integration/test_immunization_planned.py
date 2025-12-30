"""E2E tests for Planned Immunization (moodCode='INT') conversion to MedicationRequest."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

IMMUNIZATIONS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.2.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestPlannedImmunizationConversion:
    """E2E tests for C-CDA Planned Immunization Activity (INT) to FHIR MedicationRequest conversion."""

    def test_planned_immunization_creates_medication_request(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that planned immunization (moodCode='INT') creates MedicationRequest."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Should create MedicationRequest, not Immunization
        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert medication_request["resourceType"] == "MedicationRequest"

        # Should NOT create Immunization
        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is None

    def test_planned_immunization_has_correct_intent(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that planned immunization has intent='plan'."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        # moodCode='INT' should map to intent='plan'
        assert medication_request["intent"] == "plan"

    def test_planned_immunization_has_correct_status(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that planned immunization status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert medication_request["status"] == "active"

    def test_planned_immunization_has_vaccine_code(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that vaccine code is correctly converted in MedicationRequest.

        Note: The fixture has manufacturer organization, so it uses medicationReference.
        The code is in the Medication resource.
        """
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None

        # For complex medications (with manufacturer), check medicationReference
        if "medicationReference" in medication_request:
            medication = _find_resource_in_bundle(bundle, "Medication")
            assert medication is not None
            assert "code" in medication

            # Check for CVX code
            cvx = next(
                (c for c in medication["code"]["coding"]
                 if c.get("system") == "http://hl7.org/fhir/sid/cvx"),
                None
            )
            assert cvx is not None
            assert cvx["code"] == "140"
            assert cvx["display"] == "Influenza, seasonal, injectable, preservative free"
        # For simple medications, check medicationCodeableConcept
        elif "medicationCodeableConcept" in medication_request:
            # Check for CVX code
            cvx = next(
                (c for c in medication_request["medicationCodeableConcept"]["coding"]
                 if c.get("system") == "http://hl7.org/fhir/sid/cvx"),
                None
            )
            assert cvx is not None
            assert cvx["code"] == "140"
            assert cvx["display"] == "Influenza, seasonal, injectable, preservative free"
        else:
            assert False, "MedicationRequest must have either medicationReference or medicationCodeableConcept"

    def test_planned_immunization_has_ndc_translation(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that NDC translation codes are included."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None

        # For complex medications, check in Medication resource
        if "medicationReference" in medication_request:
            medication = _find_resource_in_bundle(bundle, "Medication")
            assert medication is not None

            # Check for NDC code
            ndc = next(
                (c for c in medication["code"]["coding"]
                 if c.get("system") == "http://hl7.org/fhir/sid/ndc"),
                None
            )
            assert ndc is not None
            assert ndc["code"] == "49281-0400-10"
        # For simple medications, check in MedicationRequest
        elif "medicationCodeableConcept" in medication_request:
            # Check for NDC code
            ndc = next(
                (c for c in medication_request["medicationCodeableConcept"]["coding"]
                 if c.get("system") == "http://hl7.org/fhir/sid/ndc"),
                None
            )
            assert ndc is not None
            assert ndc["code"] == "49281-0400-10"
        else:
            assert False, "MedicationRequest must have either medicationReference or medicationCodeableConcept"

    def test_planned_immunization_has_authored_on(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that authoredOn is set from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert "authoredOn" in medication_request
        assert medication_request["authoredOn"] == "2024-12-15"

    def test_planned_immunization_has_dosage_instructions(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that dosage instructions include route and dose."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert "dosageInstruction" in medication_request
        assert len(medication_request["dosageInstruction"]) > 0

        dosage = medication_request["dosageInstruction"][0]

        # Check route
        assert "route" in dosage
        assert dosage["route"]["coding"][0]["code"] == "C28161"

        # Check dose quantity
        assert "doseAndRate" in dosage
        assert len(dosage["doseAndRate"]) > 0
        dose_and_rate = dosage["doseAndRate"][0]
        assert "doseQuantity" in dose_and_rate
        assert dose_and_rate["doseQuantity"]["value"] == 0.5
        assert dose_and_rate["doseQuantity"]["unit"] == "mL"

    def test_planned_immunization_has_reason_code(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert "reasonCode" in medication_request
        assert len(medication_request["reasonCode"]) > 0
        assert medication_request["reasonCode"][0]["coding"][0]["code"] == "161511000"

    def test_planned_immunization_has_identifier(
        self, ccda_immunization_planned: str
    ) -> None:
        """Test that identifier is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_planned, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert medication_request is not None
        assert "identifier" in medication_request
        assert len(medication_request["identifier"]) > 0

        # Check identifier value
        identifier = medication_request["identifier"][0]
        assert "value" in identifier
        assert "f7f1ba43-c0ed-4b9b-9f12-f435d8ad8f93" in identifier["value"]

    def test_historical_immunization_still_creates_immunization_resource(
        self, ccda_immunization: str
    ) -> None:
        """Test that historical immunization (moodCode='EVN') still creates Immunization."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Should create Immunization, not MedicationRequest
        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["resourceType"] == "Immunization"

        # Should NOT create MedicationRequest for EVN mood
        medication_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        # Note: There might be MedicationRequest from medications section, so we check
        # that it's not related to the immunization
        if medication_request:
            # If there is a MedicationRequest, it should not have the immunization's vaccine code
            if "medicationCodeableConcept" in medication_request:
                cvx_codes = [
                    c["code"] for c in medication_request["medicationCodeableConcept"]["coding"]
                    if c.get("system") == "http://hl7.org/fhir/sid/cvx"
                ]
                # The historical immunization has CVX code 88, should not appear in MedicationRequest
                assert "88" not in cvx_codes
