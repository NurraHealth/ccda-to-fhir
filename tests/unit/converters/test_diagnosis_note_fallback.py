"""Unit tests for diagnosis note fallback encounter/date (#81).

Validates that diagnosis notes fall back to encompassingEncounter
reference and date when body encounter mapping fails.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.converters.encounter_diagnosis_notes import (
    DiagnosisNote,
    create_diagnosis_note_doc_refs,
)
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.id_generator import reset_id_cache


@pytest.fixture(autouse=True)
def _reset_ids():  # pyright: ignore[reportUnusedFunction]
    reset_id_cache()
    yield
    reset_id_cache()


@pytest.fixture
def registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


class TestDiagnosisNoteFallback:
    def test_fallback_encounter_when_mapping_fails(self, registry: ReferenceRegistry) -> None:
        """When encounter_content_id doesn't map, use fallback reference."""
        notes = [
            DiagnosisNote(
                encounter_content_id="unmapped-id",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="BP above goal.",
            )
        ]

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},  # No mapping exists
            condition_snomed_map={},
            reference_registry=registry,
            fallback_encounter_reference="urn:uuid:fallback-enc-id",
            fallback_encounter_date="2024-01-22T00:00:00Z",
        )

        assert len(doc_refs) == 1
        dr = doc_refs[0]
        assert dr["date"] == "2024-01-22T00:00:00Z"
        context = dr["context"]
        assert context["encounter"] == [{"reference": "urn:uuid:fallback-enc-id"}]

    def test_fallback_encounter_when_no_content_id(self, registry: ReferenceRegistry) -> None:
        """When encounter_content_id is None, use fallback reference."""
        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="Diabetes",
                snomed_code=None,
                note_text="Monitor HbA1c.",
            )
        ]

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={},
            reference_registry=registry,
            fallback_encounter_reference="urn:uuid:fallback-enc-id",
            fallback_encounter_date="2024-01-22T00:00:00Z",
        )

        assert len(doc_refs) == 1
        dr = doc_refs[0]
        assert dr["date"] == "2024-01-22T00:00:00Z"
        context = dr["context"]
        assert context["encounter"] == [{"reference": "urn:uuid:fallback-enc-id"}]

    def test_body_encounter_takes_precedence(self, registry: ReferenceRegistry) -> None:
        """When body encounter mapping succeeds, use it instead of fallback."""
        notes = [
            DiagnosisNote(
                encounter_content_id="enc1",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="BP note.",
            )
        ]

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={"enc1": "body-enc-id"},
            condition_snomed_map={},
            reference_registry=registry,
            encounter_date_map={"body-enc-id": "2024-02-15T10:00:00Z"},
            fallback_encounter_reference="urn:uuid:fallback-enc-id",
            fallback_encounter_date="2024-01-22T00:00:00Z",
        )

        assert len(doc_refs) == 1
        dr = doc_refs[0]
        # Body encounter takes precedence
        assert dr["date"] == "2024-02-15T10:00:00Z"
        context = dr["context"]
        assert context["encounter"] == [{"reference": "urn:uuid:body-enc-id"}]

    def test_no_fallback_no_encounter(self, registry: ReferenceRegistry) -> None:
        """When no fallback and no mapping, context should have no encounter."""
        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="Diabetes",
                snomed_code=None,
                note_text="Monitor.",
            )
        ]

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={},
            reference_registry=registry,
        )

        assert len(doc_refs) == 1
        assert "context" not in doc_refs[0]

    def test_fallback_date_when_body_has_no_date(self, registry: ReferenceRegistry) -> None:
        """When body encounter has no date, fall back to encompassingEncounter date."""
        notes = [
            DiagnosisNote(
                encounter_content_id="enc1",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="BP note.",
            )
        ]

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={"enc1": "body-enc-id"},
            condition_snomed_map={},
            reference_registry=registry,
            encounter_date_map={},  # No date for body encounter
            fallback_encounter_date="2024-01-22T00:00:00Z",
        )

        assert len(doc_refs) == 1
        dr = doc_refs[0]
        # Body encounter reference used, but fallback date used
        context = dr["context"]
        assert context["encounter"] == [{"reference": "urn:uuid:body-enc-id"}]
        assert dr["date"] == "2024-01-22T00:00:00Z"
