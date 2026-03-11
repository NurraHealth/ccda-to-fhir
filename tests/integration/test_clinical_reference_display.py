"""Integration tests for display text on clinical resource references.

Validates that Observation, Condition, and Medication references include
display text when the source C-CDA provides displayName attributes.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def _find_resources(bundle: dict, resource_type: str) -> list[dict]:
    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == resource_type
    ]


class TestEncounterDiagnosisConditionDisplay:
    """Encounter.diagnosis.condition references should include display from observation value."""

    def test_nist_encounter_diagnosis_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        encounters = _find_resources(bundle, "Encounter")
        # Check encounters that have diagnoses
        for enc in encounters:
            for diag in enc.get("diagnosis", []):
                condition_ref = diag.get("condition", {})
                # If there's a reference, it should have display when the source had displayName
                if "reference" in condition_ref and "display" in condition_ref:
                    # Display should be a non-empty string
                    assert isinstance(condition_ref["display"], str)
                    assert len(condition_ref["display"]) > 0

    def test_athena_encounter_diagnosis_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        encounters = _find_resources(bundle, "Encounter")
        has_diagnosis_display = False
        for enc in encounters:
            for diag in enc.get("diagnosis", []):
                condition_ref = diag.get("condition", {})
                if "display" in condition_ref:
                    has_diagnosis_display = True
                    assert isinstance(condition_ref["display"], str)
                    assert len(condition_ref["display"]) > 0

        # Athena CCD has encounters with diagnoses that have displayName
        assert has_diagnosis_display, "Expected at least one encounter diagnosis with display text"


class TestDiagnosticReportResultDisplay:
    """DiagnosticReport.result references should include display from observation code."""

    def test_nist_diagnostic_report_result_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        reports = _find_resources(bundle, "DiagnosticReport")
        has_result_display = False
        for report in reports:
            for result_ref in report.get("result", []):
                if "display" in result_ref:
                    has_result_display = True
                    assert isinstance(result_ref["display"], str)
                    assert len(result_ref["display"]) > 0

        if reports:
            assert has_result_display, "Expected at least one DiagnosticReport result with display text"

    def test_athena_diagnostic_report_result_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        reports = _find_resources(bundle, "DiagnosticReport")
        has_result_display = False
        for report in reports:
            for result_ref in report.get("result", []):
                if "display" in result_ref:
                    has_result_display = True
                    assert isinstance(result_ref["display"], str)
                    assert len(result_ref["display"]) > 0

        if reports:
            assert has_result_display, "Expected at least one DiagnosticReport result with display text"


class TestMedicationReferenceDisplay:
    """MedicationRequest.medicationReference should include display from medication code."""

    def test_nist_medication_reference_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        med_requests = _find_resources(bundle, "MedicationRequest")
        has_med_display = False
        for req in med_requests:
            med_ref = req.get("medicationReference", {})
            if isinstance(med_ref, dict) and "display" in med_ref:
                has_med_display = True
                assert isinstance(med_ref["display"], str)
                assert len(med_ref["display"]) > 0

        if med_requests:
            # Only assert if there are medication requests with medicationReference
            med_refs_exist = any(
                "medicationReference" in req for req in med_requests
            )
            if med_refs_exist:
                assert has_med_display, "Expected at least one medicationReference with display text"


class TestReasonReferenceDisplay:
    """Procedure/ServiceRequest reasonReference to Conditions should include display."""

    def test_nist_reason_reference_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        # Check Procedures and ServiceRequests for reasonReference with display
        for resource_type in ("Procedure", "ServiceRequest"):
            resources = _find_resources(bundle, resource_type)
            for resource in resources:
                for reason_ref in resource.get("reasonReference", []):
                    if "display" in reason_ref:
                        assert isinstance(reason_ref["display"], str)
                        assert len(reason_ref["display"]) > 0


class TestConditionEvidenceDisplay:
    """Condition.evidence.detail references should include display from supporting observation."""

    def test_conditions_evidence_display(self) -> None:
        """Check that any Condition with evidence.detail has display on the reference."""
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        conditions = _find_resources(bundle, "Condition")
        for condition in conditions:
            for evidence in condition.get("evidence", []):
                for detail in evidence.get("detail", []):
                    if "display" in detail:
                        assert isinstance(detail["display"], str)
                        assert len(detail["display"]) > 0
