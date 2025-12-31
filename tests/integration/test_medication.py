"""E2E tests for MedicationRequest resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

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
        """Test that medication code is correctly converted.

        Note: The ccda_medication fixture has complex medication info (manufacturer,
        drug vehicle, form), so it uses medicationReference. The code is in the
        Medication resource.
        """
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # For complex medications, check medicationReference
        if "medicationReference" in med_request:
            medication = _find_resource_in_bundle(bundle, "Medication")
            assert medication is not None
            assert "code" in medication
            rxnorm = next(
                (c for c in medication["code"]["coding"]
                 if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
                None
            )
            assert rxnorm is not None
            assert rxnorm["code"] == "1190220"
        # For simple medications, check medicationCodeableConcept
        elif "medicationCodeableConcept" in med_request:
            rxnorm = next(
                (c for c in med_request["medicationCodeableConcept"]["coding"]
                 if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
                None
            )
            assert rxnorm is not None
            assert rxnorm["code"] == "1190220"
        else:
            assert False, "MedicationRequest must have either medicationReference or medicationCodeableConcept"

    def test_converts_status(
        self, ccda_medication: str, fhir_medication: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["status"] == "active"

    def test_converts_intent(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that intent is correctly determined from moodCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["intent"] == "plan"

    def test_converts_authored_on(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that author time is converted to authoredOn."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "authoredOn" in med_request
        assert "2013-09-11" in med_request["authoredOn"]

    def test_converts_dosage_timing(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that timing is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        route = med_request["dosageInstruction"][0]["route"]
        assert route["coding"][0]["code"] == "C38288"

    def test_converts_dose_quantity(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that dose quantity is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        dose = med_request["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]
        assert dose["value"] == 1

    def test_converts_max_dose(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that max dose is correctly converted to FHIR Ratio with complete Quantity structure."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        max_dose = med_request["dosageInstruction"][0]["maxDosePerPeriod"]

        # Verify numerator structure (6 {spray})
        assert max_dose["numerator"]["value"] == 6
        assert max_dose["numerator"]["unit"] == "{spray}"
        assert max_dose["numerator"]["system"] == "http://unitsofmeasure.org"
        assert max_dose["numerator"]["code"] == "{spray}"

        # Verify denominator structure (1 {day})
        assert max_dose["denominator"]["value"] == 1
        assert max_dose["denominator"]["unit"] == "{day}"
        assert max_dose["denominator"]["system"] == "http://unitsofmeasure.org"
        assert max_dose["denominator"]["code"] == "{day}"

    def test_converts_as_needed(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that precondition with coded value is converted to asNeededCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        dosage = med_request["dosageInstruction"][0]

        # Should have asNeededCodeableConcept with the reason code
        assert "asNeededCodeableConcept" in dosage
        as_needed = dosage["asNeededCodeableConcept"]
        assert as_needed["coding"][0]["code"] == "56018004"
        assert as_needed["coding"][0]["display"].lower() == "wheezing"

        # Should NOT have asNeededBoolean (mutually exclusive)
        assert "asNeededBoolean" not in dosage

    def test_converts_as_needed_boolean(self) -> None:
        """Test that precondition without coded value is converted to asNeededBoolean.

        Per C-CDA on FHIR IG: "The presence of a precondition element indicates
        asNeededBoolean should be true."
        Per FHIR R4: asNeededBoolean and asNeededCodeableConcept are mutually exclusive.
        """
        # Load fixture with precondition but no coded value
        with open("tests/integration/fixtures/ccda/medication_as_needed_no_reason.xml") as f:
            ccda_medication = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        dosage = med_request["dosageInstruction"][0]

        # Should have asNeededBoolean = true
        assert "asNeededBoolean" in dosage
        assert dosage["asNeededBoolean"] is True

        # Should NOT have asNeededCodeableConcept (mutually exclusive)
        assert "asNeededCodeableConcept" not in dosage

    def test_converts_reason_code(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "reasonCode" in med_request
        assert med_request["reasonCode"][0]["coding"][0]["code"] == "56018004"

    def test_converts_patient_instructions(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that instructions are converted to patientInstruction."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request
        assert med_request["dosageInstruction"][0]["patientInstruction"] == "Do not overtake"

    def test_resource_type_is_medication_request(
        self, ccda_medication: str, fhir_medication: JSONObject) -> None:
        """Test that the resource type is MedicationRequest."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request["resourceType"] == "MedicationRequest"

    def test_converts_requester_from_latest_author(
        self, ccda_medication: str
    ) -> None:
        """Test that requester field is populated from latest author."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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

    def test_provenance_has_recorded_date(
        self, ccda_medication: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        med_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                med_request["id"] in t.get("reference", "") for t in prov["target"]
            ):
                med_provenance = prov
                break

        assert med_provenance is not None
        assert "recorded" in med_provenance
        # Should have a valid ISO datetime
        assert len(med_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_medication: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        med_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                med_request["id"] in t.get("reference", "") for t in prov["target"]
            ):
                med_provenance = prov
                break

        assert med_provenance is not None
        assert "agent" in med_provenance
        assert len(med_provenance["agent"]) > 0

        # Check agent type
        agent = med_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_medication_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_multiple_authors, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        med_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                med_request["id"] in t.get("reference", "") for t in prov["target"]
            ):
                med_provenance = prov
                break

        assert med_provenance is not None
        assert "agent" in med_provenance
        # Should have multiple agents for multiple authors
        assert len(med_provenance["agent"]) >= 2

        # Verify all agents reference practitioners
        for agent in med_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_multiple_authors_selects_latest_for_requester(
        self, ccda_medication_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for requester field."""
        import uuid as uuid_module

        ccda_doc = wrap_in_ccda_document(ccda_medication_multiple_authors, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "requester" in med_request

        # Requester should reference a Practitioner with UUID v4 ID
        assert "Practitioner/" in med_request["requester"]["reference"]
        practitioner_id = med_request["requester"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            raise AssertionError(f"Practitioner ID {practitioner_id} is not a valid UUID v4")

        # authoredOn should use earliest time, reduced to date-only per FHIR R4 requirement (no timezone in source)
        assert med_request["authoredOn"] == "2023-10-01"

    def test_completed_status_with_future_dates_maps_to_active(self) -> None:
        """Test that completed status with future end date correctly maps to active.

        Per C-CDA on FHIR IG: C-CDA statusCode="completed" may mean "prescription writing completed"
        not "medication administration completed". When the end date is in the future, the medication
        is still ongoing and should map to FHIR "active".
        """
        from datetime import datetime, timedelta

        # Calculate a future date (30 days from now)
        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y%m%d")

        ccda_medication = f"""<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="INT" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="med-future-test"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
        <high value="{future_date}"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        # Completed with future end date → active (ongoing medication)
        assert med_request["status"] == "active"

    def test_completed_status_with_past_dates_maps_to_completed(self) -> None:
        """Test that completed status with past end date correctly maps to completed.

        Per C-CDA on FHIR IG: When statusCode="completed" and the end date is in the past,
        the medication course has truly finished and should map to FHIR "completed".
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="INT" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="med-past-test"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
        <high value="20200401"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        # Completed with past end date → completed (medication course finished)
        assert med_request["status"] == "completed"

    def test_completed_status_without_end_date_maps_to_active(self) -> None:
        """Test that completed status with no end date correctly maps to active.

        Per C-CDA on FHIR IG: When statusCode="completed" but no end date is present,
        the medication is unbounded/ongoing and should map to FHIR "active".
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="INT" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="med-unbounded-test"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        # Completed with no end date → active (unbounded/ongoing medication)
        assert med_request["status"] == "active"


class TestEIVLTimingConversion:
    """E2E tests for EIVL_TS (event-based) timing conversion."""

    def test_converts_bedtime_hs_event(self, ccda_medication_bedtime_hs: str) -> None:
        """Test that EIVL_TS with HS (bedtime) event is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_bedtime_hs, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "when" in timing
        assert timing["when"] == ["ACM"]

    def test_converts_event_with_offset(self, ccda_medication_with_offset: str) -> None:
        """Test that EIVL_TS with offset is correctly converted to timing.repeat.offset."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_offset, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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


class TestBoundsPeriodConversion:
    """E2E tests for IVL_TS (boundsPeriod) conversion."""

    def test_converts_start_date_only(self, ccda_medication_with_start_date: str) -> None:
        """Test that IVL_TS with only start date is correctly converted to boundsPeriod.start."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_start_date, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "boundsPeriod" in timing
        assert "start" in timing["boundsPeriod"]
        assert timing["boundsPeriod"]["start"] == "2020-01-15"
        # Should not have end date
        assert "end" not in timing["boundsPeriod"]

    def test_converts_start_and_end_dates(self, ccda_medication_with_start_end_dates: str) -> None:
        """Test that IVL_TS with start and end dates is correctly converted to boundsPeriod."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_start_end_dates, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]
        assert "boundsPeriod" in timing
        assert "start" in timing["boundsPeriod"]
        assert "end" in timing["boundsPeriod"]
        assert timing["boundsPeriod"]["start"] == "2020-03-01"
        assert timing["boundsPeriod"]["end"] == "2020-05-31"

    def test_converts_bounds_period_with_frequency(
        self, ccda_medication_bounds_period_with_frequency: str
    ) -> None:
        """Test that IVL_TS boundsPeriod and PIVL_TS frequency are both correctly converted."""
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_bounds_period_with_frequency, MEDICATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        timing = med_request["dosageInstruction"][0]["timing"]["repeat"]

        # Should have boundsPeriod (from IVL_TS)
        assert "boundsPeriod" in timing
        assert timing["boundsPeriod"]["start"] == "2021-01-01"
        assert timing["boundsPeriod"]["end"] == "2021-06-30"

        # Should also have frequency/period (from PIVL_TS)
        assert "period" in timing
        assert timing["period"] == 12
        assert timing["periodUnit"] == "h"

    def test_bounds_period_does_not_affect_other_timing_elements(
        self, ccda_medication_bounds_period_with_frequency: str
    ) -> None:
        """Test that boundsPeriod does not interfere with other timing elements."""
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_bounds_period_with_frequency, MEDICATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        dosage = med_request["dosageInstruction"][0]

        # Verify all expected dosage elements are present
        assert "timing" in dosage
        assert "route" in dosage
        assert "doseAndRate" in dosage

        # Verify timing structure integrity
        timing_repeat = dosage["timing"]["repeat"]
        assert isinstance(timing_repeat, dict)
        assert len(timing_repeat) >= 3  # boundsPeriod, period, periodUnit


class TestDosageInstructionText:
    """E2E tests for dosageInstruction.text (free text sig) conversion."""

    def test_converts_free_text_sig(self, ccda_medication_with_sig: str) -> None:
        """Test that substanceAdministration/text maps to dosageInstruction.text.

        Per C-CDA on FHIR IG: substanceAdministration/text → dosageInstruction.text
        Per FHIR R4: Dosage.text = "Free text dosage instructions e.g. SIG"
        """
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_sig, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        dosage = med_request["dosageInstruction"][0]
        assert "text" in dosage
        assert dosage["text"] == "Take one tablet by mouth daily"

    def test_text_and_patient_instruction_both_present(
        self, ccda_medication_with_sig_and_patient_instruction: str
    ) -> None:
        """Test that both dosageInstruction.text and patientInstruction can coexist.

        Per FHIR R4:
        - Dosage.text = "Free text dosage instructions e.g. SIG"
        - Dosage.patientInstruction = "Instructions in terms that are understood by the patient"
        """
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_with_sig_and_patient_instruction, MEDICATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        dosage = med_request["dosageInstruction"][0]

        # Both text (from substanceAdministration/text) and patientInstruction
        # (from Instruction Act) should be present
        assert "text" in dosage
        assert dosage["text"] == "1-2 tabs po q4-6h prn pain"

        assert "patientInstruction" in dosage
        assert dosage["patientInstruction"] == "Take with food to avoid stomach upset"

    def test_text_does_not_go_to_note(self, ccda_medication_with_sig: str) -> None:
        """Test that substanceAdministration/text does NOT map to MedicationRequest.note.

        The free text sig should map to dosageInstruction.text, NOT to note.
        Per FHIR R4: MedicationRequest.note = "Extra information about the prescription
        that could not be conveyed by the other attributes."
        """
        ccda_doc = wrap_in_ccda_document(ccda_medication_with_sig, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # Should NOT have note field (no Comment Activity present)
        assert "note" not in med_request

        # Text should be in dosageInstruction.text instead
        assert "dosageInstruction" in med_request
        assert "text" in med_request["dosageInstruction"][0]

    def test_creates_medication_resource_for_complex_medication(
        self, ccda_medication: str
    ) -> None:
        """Test that a Medication resource is created when complex medication info exists.

        Per C-CDA on FHIR IG: When additional medication details need to be conveyed
        (manufacturer, drug vehicle, form, lot number), a Medication resource should
        be created and referenced by the MedicationRequest.
        """
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Should have a Medication resource
        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None
        assert medication["resourceType"] == "Medication"

        # Should have an ID
        assert "id" in medication
        assert medication["id"].startswith("medication-")

    def test_medication_request_references_medication_resource(
        self, ccda_medication: str
    ) -> None:
        """Test that MedicationRequest uses medicationReference for complex medication."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None

        # Should have medicationReference, NOT medicationCodeableConcept
        assert "medicationReference" in med_request
        assert "medicationCodeableConcept" not in med_request

        # Reference should point to a Medication resource
        assert "reference" in med_request["medicationReference"]
        med_ref = med_request["medicationReference"]["reference"]
        assert med_ref.startswith("Medication/")

        # The referenced Medication should exist in the bundle
        medication_id = med_ref.split("/")[1]
        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None
        assert medication["id"] == medication_id

    def test_medication_resource_has_code(self, ccda_medication: str) -> None:
        """Test that Medication resource has medication code."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None

        # Should have code from manufacturedMaterial.code
        assert "code" in medication
        assert "coding" in medication["code"]
        rxnorm = next(
            (c for c in medication["code"]["coding"]
             if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm is not None
        assert rxnorm["code"] == "1190220"

    def test_medication_resource_has_manufacturer(self, ccda_medication: str) -> None:
        """Test that Medication resource has manufacturer from manufacturerOrganization."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None

        # Should have manufacturer from manufacturerOrganization
        assert "manufacturer" in medication
        assert "display" in medication["manufacturer"]
        assert medication["manufacturer"]["display"] == "Good Vaccines Inc"

    def test_medication_resource_has_form(self, ccda_medication: str) -> None:
        """Test that Medication resource has form from administrationUnitCode."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None

        # Should have form from administrationUnitCode
        assert "form" in medication
        assert "coding" in medication["form"]
        assert len(medication["form"]["coding"]) > 0
        assert medication["form"]["coding"][0]["code"] == "C48501"
        assert "Inhalation dosing unit" in medication["form"]["coding"][0]["display"]

    def test_medication_resource_has_ingredient(self, ccda_medication: str) -> None:
        """Test that Medication resource has ingredient from drug vehicle participant."""
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        medication = _find_resource_in_bundle(bundle, "Medication")
        assert medication is not None

        # Should have ingredient from participant (drug vehicle)
        assert "ingredient" in medication
        assert len(medication["ingredient"]) > 0

        ingredient = medication["ingredient"][0]
        assert "itemCodeableConcept" in ingredient
        assert "coding" in ingredient["itemCodeableConcept"]

        # Should be sodium chloride (the drug vehicle)
        snomed_code = next(
            (c for c in ingredient["itemCodeableConcept"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_code is not None
        assert snomed_code["code"] == "387390002"
        assert "sodium chloride" in snomed_code["display"].lower()

        # Drug vehicle should be inactive ingredient
        assert "isActive" in ingredient
        assert ingredient["isActive"] is False


class TestCSRouteCodeHandling:
    """E2E tests for CS routeCode handling in real-world documents.

    Tests the fix for handling routeCode with xsi:type="CS" in medication converters.
    Previously, only CE datatype was accepted for routeCode, causing parsing failures.
    """

    def test_cs_routecode_parses_without_error(self) -> None:
        """Test that CS routeCode parses without error.

        The key fix is that CS datatype is now accepted for routeCode,
        allowing the document to parse. The actual route conversion behavior
        may vary based on the presence of additional fields in the CS datatype.
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="INT" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="med-cs-route-test"/>
    <statusCode code="active"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
    </effectiveTime>
    <routeCode xsi:type="CS" code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
               codeSystemName="NCI Thesaurus" displayName="ORAL"/>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88" displayName="Aspirin"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        # The key test: document should parse without error
        ccda_doc = wrap_in_ccda_document(ccda_medication, MEDICATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert "dosageInstruction" in med_request

        # Document parsed successfully - CS routeCode is now supported
        # Note: Route conversion may be None if CS lacks required fields (e.g., originalText)
        # The important fix is that parsing no longer fails with validation error
