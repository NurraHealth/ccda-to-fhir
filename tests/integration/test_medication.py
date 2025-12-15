"""E2E tests for MedicationRequest resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

MEDICATIONS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.1.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestMedicationConversion:
    """E2E tests for C-CDA Medication Activity to FHIR MedicationRequest conversion."""

    def test_converts_medication_code(
        self, ccda_medication: str, fhir_medication: JSONObject
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
        self, ccda_medication: str, fhir_medication: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["status"] == "active"

    def test_converts_intent(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that intent is correctly determined from moodCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["intent"] == "plan"

    def test_converts_authored_on(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that author time is converted to authoredOn."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "authoredOn" in med_request
        assert "2013-09-11" in med_request["authoredOn"]

    def test_converts_dosage_timing(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
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
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that route code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        route = med_request["dosageInstruction"][0]["route"]
        assert route["coding"][0]["code"] == "C38288"

    def test_converts_dose_quantity(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that dose quantity is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        dose = med_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
        assert dose["value"] == 1

    def test_converts_max_dose(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that max dose is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        max_dose = med_request["dosageInstruction"][0]["maxDosePerPeriod"]
        assert max_dose["numerator"]["value"] == 6

    def test_converts_as_needed(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that precondition is converted to asNeededCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        as_needed = med_request["dosageInstruction"][0]["asNeededCodeableConcept"]
        assert as_needed["coding"][0]["code"] == "56018004"

    def test_converts_reason_code(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "reasonCode" in med_request
        assert med_request["reasonCode"][0]["coding"][0]["code"] == "56018004"

    def test_converts_patient_instructions(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that instructions are converted to patientInstruction."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        assert med_request["dosageInstruction"][0]["patientInstruction"] == "Do not overtake"

    def test_resource_type_is_medication_request(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that the resource type is MedicationRequest."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["resourceType"] == "MedicationRequest"

    def test_converts_requester_from_latest_author(
        self, ccda_medication: str
    ) -> None:
        """Test that requester field is populated from latest author."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "requester" in med_request
        assert "reference" in med_request["requester"]
        assert med_request["requester"]["reference"].startswith("Practitioner/")

    def test_requester_and_provenance_reference_same_practitioner(
        self, ccda_medication: str
    ) -> None:
        """Test that requester and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "requester" in med_request
        requester_ref = med_request["requester"]["reference"]

        # Find Provenance for this medication request
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this medication request
        med_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                med_request["id"] in t.get("reference", "") for t in prov["target"]
            ):
                med_provenance = prov
                break

        assert med_provenance is not None
        # Verify Provenance agent references same practitioner
        assert "agent" in med_provenance
        assert len(med_provenance["agent"]) > 0
        # Latest author should be in Provenance agents
        agent_refs = [
            agent.get("who", {}).get("reference")
            for agent in med_provenance["agent"]
        ]
        assert requester_ref in agent_refs

    def test_multiple_authors_selects_latest_for_requester(
        self, ccda_medication_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for requester field."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_multiple_authors, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "requester" in med_request

        # Latest author is LATEST-MED-DOC (time: 20231210143000)
        # Not EARLY-MED-DOC (time: 20231001080000)
        assert "LATEST-MED-DOC" in med_request["requester"]["reference"]
        assert "EARLY-MED-DOC" not in med_request["requester"]["reference"]

        # authoredOn should still use earliest time
        assert med_request["authoredOn"] == "2023-10-01T08:00:00"


class TestEIVLTimingConversion:
    """E2E tests for EIVL_TS (event-based) timing conversion."""

    def test_converts_bedtime_hs_event(self, ccda_medication_bedtime_hs: str) -> None:
        """Test that EIVL_TS with HS (bedtime) event is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_bedtime_hs, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "when" in timing
        assert timing["when"] == ["HS"]

    def test_converts_before_breakfast_acm_event(
        self, ccda_medication_before_breakfast_acm: str
    ) -> None:
        """Test that EIVL_TS with ACM (before breakfast) event is correctly converted."""
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_before_breakfast_acm, MEDICATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "when" in timing
        assert timing["when"] == ["ACM"]

    def test_converts_event_with_offset(self, ccda_medication_with_offset: str) -> None:
        """Test that EIVL_TS with offset is correctly converted to timing.repeat.offset."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_offset, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "when" in timing
        assert timing["when"] == ["PCM"]  # after breakfast
        assert "offset" in timing
        assert timing["offset"] == 30  # 30 minutes

    def test_converts_combined_pivl_eivl_timing(
        self, ccda_medication_pivl_eivl_combined: str
    ) -> None:
        """Test that combined PIVL_TS and EIVL_TS timing is correctly converted."""
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_pivl_eivl_combined, MEDICATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]

        # Should have both PIVL (period) and EIVL (when) elements
        assert "period" in timing
        assert timing["period"] == 12
        assert timing["periodUnit"] == "h"

        assert "when" in timing
        assert timing["when"] == ["C"]  # with meals
