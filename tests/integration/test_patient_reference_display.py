"""Integration tests for patient reference display text.

Validates that subject/patient references throughout converted resources
include a display field with the patient name, per FHIR R4 Reference.display.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.converters.references import _extract_patient_display

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
        if r["resourceType"] == "Patient":
            return _extract_patient_display(r)
    return None


@pytest.mark.parametrize(
    "fixture",
    [
        "partners_epic.xml",
        "cerner_toc.xml",
        "nist_ambulatory.xml",
        "athena_ccd.xml",
    ],
)
def test_subject_references_have_display(fixture: str) -> None:
    xml = (DOCUMENTS_DIR / fixture).read_text()
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
