"""E2E tests for MedicationStatement resource conversion (moodCode="EVN")."""

from __future__ import annotations

from ccda_to_fhir.types import JSONObject
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.constants import TemplateIds

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestHistoricalMedicationConversion:
    """E2E tests for C-CDA Medication Activity (EVN) to FHIR MedicationStatement conversion."""

    def test_converts_evn_medication_to_statement(self) -> None:
        """Test that moodCode='EVN' creates MedicationStatement, not MedicationRequest."""
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="evn-test-1"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88"
                      displayName="Lisinopril 10 MG Oral Tablet"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        # Should create MedicationStatement, not MedicationRequest
        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        assert med_statement["resourceType"] == "MedicationStatement"

        # Should NOT create MedicationRequest
        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is None

    def test_converts_medication_code(self) -> None:
        """Test that medication code is correctly converted."""
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="evn-test-2"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code code="197361" codeSystem="2.16.840.1.113883.6.88"
                      displayName="Lisinopril 10 MG Oral Tablet"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        assert "medicationCodeableConcept" in med_statement

        rxnorm = next(
            (c for c in med_statement["medicationCodeableConcept"]["coding"]
             if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm is not None
        assert rxnorm["code"] == "197361"
        assert rxnorm["display"] == "Lisinopril 10 MG Oral Tablet"

    def test_converts_status(self) -> None:
        """Test that status is correctly mapped to MedicationStatement status.

        Per C-CDA on FHIR IG: statusCode="completed" with past end date → FHIR "completed"
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="evn-test-3"/>
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
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        assert med_statement["status"] == "completed"

    def test_completed_status_with_ongoing_dates_maps_to_active(self) -> None:
        """Test that completed status with no end date correctly maps to active.

        Per C-CDA on FHIR IG: C-CDA statusCode="completed" may mean "prescription writing completed"
        not "medication administration completed". When no end date is present, the medication
        is ongoing and should map to FHIR "active".
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="evn-test-4"/>
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
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        # Completed with no end date → active (ongoing medication)
        assert med_statement["status"] == "active"

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
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="evn-future-test"/>
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
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        # Completed with future end date → active (ongoing medication)
        assert med_statement["status"] == "active"
