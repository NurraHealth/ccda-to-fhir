"""Integration tests for patient reference display text.

Validates that subject/patient references throughout converted resources
include a display field with the patient name, per FHIR R4 Reference.display.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"

# Resource types that use "subject" for the patient reference
SUBJECT_RESOURCE_TYPES = {
    "Condition", "Observation", "Procedure", "DiagnosticReport",
    "MedicationRequest", "MedicationStatement", "MedicationDispense",
    "CarePlan", "CareTeam", "Goal", "ServiceRequest", "Encounter",
    "DocumentReference",
}

# Resource types that use "patient" for the patient reference
PATIENT_RESOURCE_TYPES = {
    "AllergyIntolerance", "Immunization",
}


def _extract_resources(bundle: dict) -> list[dict]:
    """Extract all resources from bundle entries."""
    return [entry["resource"] for entry in bundle["entry"]]


def _get_patient_display(resources: list[dict]) -> str | None:
    """Get the expected display from the Patient resource name."""
    for r in resources:
        if r["resourceType"] == "Patient" and "name" in r:
            name = r["name"][0]
            parts: list[str] = []
            for p in name.get("prefix", []):
                if p:
                    parts.append(p)
            for g in name.get("given", []):
                if g:
                    parts.append(g)
            family = name.get("family")
            if family:
                parts.append(family)
            for s in name.get("suffix", []):
                if s:
                    parts.append(s)
            return " ".join(parts) if parts else None
    return None


class TestPatientReferenceDisplayEpic:
    """Epic CCD has patient name that should propagate to subject references."""

    def test_subject_references_have_display(self) -> None:
        xml = (DOCUMENTS_DIR / "partners_epic.xml").read_text()
        result = convert_document(xml)
        resources = _extract_resources(result["bundle"])

        patient_display = _get_patient_display(resources)
        assert patient_display is not None, "Patient should have a name"

        for r in resources:
            rt = r["resourceType"]
            if rt in SUBJECT_RESOURCE_TYPES and "subject" in r:
                ref = r["subject"]
                assert "display" in ref, (
                    f"{rt}/{r.get('id')}: subject reference missing display"
                )
                assert ref["display"] == patient_display

            if rt in PATIENT_RESOURCE_TYPES and "patient" in r:
                ref = r["patient"]
                assert "display" in ref, (
                    f"{rt}/{r.get('id')}: patient reference missing display"
                )
                assert ref["display"] == patient_display


class TestPatientReferenceDisplayCerner:
    """Cerner TOC has patient name that should propagate to subject references."""

    def test_subject_references_have_display(self) -> None:
        xml = (DOCUMENTS_DIR / "cerner_toc.xml").read_text()
        result = convert_document(xml)
        resources = _extract_resources(result["bundle"])

        patient_display = _get_patient_display(resources)
        assert patient_display is not None

        for r in resources:
            rt = r["resourceType"]
            if rt in SUBJECT_RESOURCE_TYPES and "subject" in r:
                assert "display" in r["subject"], (
                    f"{rt}/{r.get('id')}: subject reference missing display"
                )

            if rt in PATIENT_RESOURCE_TYPES and "patient" in r:
                assert "display" in r["patient"], (
                    f"{rt}/{r.get('id')}: patient reference missing display"
                )


class TestPatientReferenceDisplayNist:
    """NIST Ambulatory has patient name that should propagate to subject references."""

    def test_subject_references_have_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        resources = _extract_resources(result["bundle"])

        patient_display = _get_patient_display(resources)
        assert patient_display is not None

        for r in resources:
            rt = r["resourceType"]
            if rt in SUBJECT_RESOURCE_TYPES and "subject" in r:
                assert "display" in r["subject"], (
                    f"{rt}/{r.get('id')}: subject reference missing display"
                )


class TestPatientReferenceDisplayAthena:
    """Athena CCD has patient name that should propagate to subject references."""

    def test_subject_references_have_display(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        resources = _extract_resources(result["bundle"])

        patient_display = _get_patient_display(resources)
        assert patient_display is not None

        for r in resources:
            rt = r["resourceType"]
            if rt in SUBJECT_RESOURCE_TYPES and "subject" in r:
                assert "display" in r["subject"], (
                    f"{rt}/{r.get('id')}: subject reference missing display"
                )

            if rt in PATIENT_RESOURCE_TYPES and "patient" in r:
                assert "display" in r["patient"], (
                    f"{rt}/{r.get('id')}: patient reference missing display"
                )
