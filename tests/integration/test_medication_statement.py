"""E2E tests for MedicationStatement resource conversion (moodCode="EVN")."""

from __future__ import annotations

from ccda_to_fhir.constants import TemplateIds
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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        # Completed with future end date → active (ongoing medication)
        assert med_statement["status"] == "active"

    def test_medication_with_nullflavor_code_uses_name(self) -> None:
        """Test that medication with nullFlavor code falls back to name.

        Per C-CDA spec: medication can be identified by code or name.
        When code has nullFlavor, the medication name should be used as text.

        This ensures FHIR R4 compliance: MedicationStatement.medication[x] is required (1..1).
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="nullflavor-test-1"/>
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
                <code nullFlavor="OTH">
                    <originalText>
                        <reference value="#med-name-123"/>
                    </originalText>
                </code>
                <name>methylprednisolone 4 mg tablets in a dose pack</name>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        assert "medicationCodeableConcept" in med_statement

        # Should have text from medication name (no coding since code has nullFlavor)
        med_concept = med_statement["medicationCodeableConcept"]
        assert "text" in med_concept
        assert med_concept["text"] == "methylprednisolone 4 mg tablets in a dose pack"

        # Should not have coding (code had nullFlavor)
        assert "coding" not in med_concept or len(med_concept.get("coding", [])) == 0

    def test_medication_with_nullflavor_code_and_originaltext(self) -> None:
        """Test that medication with nullFlavor code prefers originalText over name.

        Fallback precedence: code → originalText → name
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="nullflavor-test-2"/>
    <text>Aspirin 81mg daily</text>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
            <manufacturedMaterial>
                <code nullFlavor="OTH">
                    <originalText>Aspirin 81mg daily</originalText>
                </code>
                <name>Generic Aspirin</name>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_medication, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None
        assert "medicationCodeableConcept" in med_statement

        # Should prefer originalText over name
        med_concept = med_statement["medicationCodeableConcept"]
        assert "text" in med_concept
        assert med_concept["text"] == "Aspirin 81mg daily"


class TestPPD_PQDataType:
    """Tests for PPD_PQ (Parametric Probability Distribution of Physical Quantity) support.

    PPD_PQ is used in medication timing to express uncertainty/variability.
    Real-world example from McKesson Paragon: "every 5±1 hours"
    """

    def test_medication_timing_with_ppd_pq_period(self) -> None:
        """Test PIVL_TS with PPD_PQ period parsing.

        Real-world C-CDA from McKesson Paragon uses PPD_PQ to express
        medication timing with statistical distribution:
          <period xsi:type="PPD_PQ" value="5.00" unit="h">
            <standardDeviation value="1.00" unit="h"/>
          </period>

        This means "every 5±1 hours" (mean=5h, stddev=1h).

        In FHIR conversion, we preserve the base value/unit but lose the
        standard deviation (FHIR Timing doesn't support distributions).
        """
        ccda_medication = """<?xml version="1.0" encoding="UTF-8"?>
<substanceAdministration classCode="SBADM" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
    <id root="ppd-pq-test-1"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20200101"/>
        <high nullFlavor="UNK"/>
    </effectiveTime>
    <effectiveTime xsi:type="PIVL_TS" operator="A" institutionSpecified="true">
        <period xsi:type="PPD_PQ" value="5.00" unit="h">
            <standardDeviation value="1.00" unit="h"/>
        </period>
    </effectiveTime>
    <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
               displayName="Oral" codeSystemName="NCI Thesaurus"/>
    <doseQuantity value="35" unit="mg"/>
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
        bundle = convert_document(ccda_doc)["bundle"]

        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")
        assert med_statement is not None

        # Should have dosage with timing
        assert "dosage" in med_statement
        assert len(med_statement["dosage"]) > 0

        dosage = med_statement["dosage"][0]
        assert "timing" in dosage

        # Should have timing with repeat period
        timing = dosage["timing"]
        assert "repeat" in timing

        repeat = timing["repeat"]
        # Should preserve the period value (5) and unit (h)
        assert "period" in repeat
        assert repeat["period"] == 5.0
        assert "periodUnit" in repeat
        assert repeat["periodUnit"] == "h"

        # Note: standardDeviation is lost in FHIR conversion
        # FHIR Timing doesn't support probability distributions


class TestMedicationStatementMissingMedication:
    """Tests for MedicationStatement with missing or incomplete medication information."""

    def test_medication_with_no_code_uses_fallback_text(self) -> None:
        """Test that MedicationStatement with no code/text uses fallback.

        Real-world C-CDA documents may have medication activities with no code
        or original text in the manufactured material. FHIR R4B requires
        medicationCodeableConcept or medicationReference. This test verifies
        we provide a fallback CodeableConcept with text to satisfy validation.
        """
        ccda_doc = wrap_in_ccda_document(
            """<substanceAdministration classCode="SBADM" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
                <id root="1.2.3.4.5" extension="med-123"/>
                <statusCode code="completed"/>
                <effectiveTime xsi:type="IVL_TS">
                    <low value="20230101"/>
                </effectiveTime>
                <doseQuantity value="1"/>
                <consumable>
                    <manufacturedProduct>
                        <manufacturedMaterial>
                            <!-- Code with nullFlavor (no actual code value) and no name -->
                            <code nullFlavor="UNK"/>
                        </manufacturedMaterial>
                    </manufacturedProduct>
                </consumable>
            </substanceAdministration>""",
            TemplateIds.MEDICATIONS_SECTION
        )

        bundle = convert_document(ccda_doc)["bundle"]
        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")

        assert med_statement is not None
        assert "medicationCodeableConcept" in med_statement, "Should have medicationCodeableConcept"

        # Should have fallback text
        assert "text" in med_statement["medicationCodeableConcept"]
        assert med_statement["medicationCodeableConcept"]["text"] == "Medication information not available"

        # Should not have any coding (no code available)
        assert "coding" not in med_statement["medicationCodeableConcept"] or \
               len(med_statement["medicationCodeableConcept"].get("coding", [])) == 0


class TestMedicationStatementIDSanitization:
    """Tests for MedicationStatement resource ID sanitization."""

    def test_sanitizes_id_with_slashes(self) -> None:
        """Test that medication statement IDs with slash characters are sanitized.

        Real-world C-CDA documents may have IDs with slashes
        (e.g., 'medicationstatement-medication/1813433361850990')
        which violates FHIR R4B spec. IDs can only contain: A-Z, a-z, 0-9, -, .
        """
        ccda_doc = wrap_in_ccda_document(
            """<substanceAdministration classCode="SBADM" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
                <id root="1.2.3.4.5" extension="medication/1813433361850990"/>
                <statusCode code="completed"/>
                <effectiveTime xsi:type="IVL_TS">
                    <low value="20230101"/>
                </effectiveTime>
                <doseQuantity value="1"/>
                <consumable>
                    <manufacturedProduct>
                        <manufacturedMaterial>
                            <code code="197361" codeSystem="2.16.840.1.113883.6.88"
                                  displayName="Lisinopril 10 MG Oral Tablet"/>
                        </manufacturedMaterial>
                    </manufacturedProduct>
                </consumable>
            </substanceAdministration>""",
            TemplateIds.MEDICATIONS_SECTION
        )

        bundle = convert_document(ccda_doc)["bundle"]
        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")

        assert med_statement is not None
        # Slash character should be replaced with hyphen
        assert med_statement["id"] == "medicationstatement-medication-1813433361850990"
        # Verify it's the correct medication
        assert med_statement["medicationCodeableConcept"]["coding"][0]["code"] == "197361"

    def test_sanitizes_id_with_pipes(self) -> None:
        """Test that medication statement IDs with pipe characters are sanitized."""
        ccda_doc = wrap_in_ccda_document(
            """<substanceAdministration classCode="SBADM" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
                <id root="1.2.3.4.5" extension="med-15||rx-003"/>
                <statusCode code="active"/>
                <effectiveTime xsi:type="IVL_TS">
                    <low value="20230101"/>
                </effectiveTime>
                <doseQuantity value="2"/>
                <consumable>
                    <manufacturedProduct>
                        <manufacturedMaterial>
                            <code code="308136" codeSystem="2.16.840.1.113883.6.88"
                                  displayName="Metformin 500 MG Oral Tablet"/>
                        </manufacturedMaterial>
                    </manufacturedProduct>
                </consumable>
            </substanceAdministration>""",
            TemplateIds.MEDICATIONS_SECTION
        )

        bundle = convert_document(ccda_doc)["bundle"]
        med_statement = _find_resource_in_bundle(bundle, "MedicationStatement")

        assert med_statement is not None
        # Pipe characters should be replaced with hyphens
        assert med_statement["id"] == "medicationstatement-med-15--rx-003"
        # Verify it's the correct medication
        assert med_statement["medicationCodeableConcept"]["coding"][0]["code"] == "308136"
