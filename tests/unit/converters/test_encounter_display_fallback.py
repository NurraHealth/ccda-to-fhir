"""Unit tests for encounter display fallback (#79).

Validates that _get_encompassing_encounter_context falls back to
encounterParticipant specialty when code element is absent.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.clinical_document import (
    ComponentOf,
    EncompassingEncounter,
    EncounterParticipant,
)
from ccda_to_fhir.ccda.models.datatypes import CE, II, IVL_TS
from ccda_to_fhir.ccda.models.performer import AssignedEntity
from ccda_to_fhir.convert import DocumentConverter
from ccda_to_fhir.id_generator import reset_id_cache


@pytest.fixture(autouse=True)
def _reset_ids():  # pyright: ignore[reportUnusedFunction]
    reset_id_cache()
    yield
    reset_id_cache()


def _make_converter() -> DocumentConverter:
    return DocumentConverter()


def _make_mock_ccda(enc: EncompassingEncounter):
    """Create a minimal ClinicalDocument-like object with encompassingEncounter."""

    class MockDoc:
        component_of = ComponentOf(encompassing_encounter=enc)

    return MockDoc()


class TestEncounterDisplayFallback:
    def test_display_from_code(self) -> None:
        """When code.displayName exists, use it directly."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            code=CE(
                code="99213",
                code_system="2.16.840.1.113883.6.12",
                display_name="Office visit",
            ),
            effective_time=IVL_TS(value="20240122"),
        )
        converter = _make_converter()
        ctx = converter._get_encompassing_encounter_context(_make_mock_ccda(enc))

        assert ctx.display == "Office visit"

    def test_display_fallback_to_participant_specialty(self) -> None:
        """When no code, fall back to encounterParticipant specialty."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            effective_time=IVL_TS(value="20240122"),
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(
                        id=[II(root="2.16.840.1.113883.4.6", extension="999")],
                        code=CE(
                            code="207Q00000X",
                            code_system="2.16.840.1.113883.6.101",
                            display_name="Family Medicine",
                        ),
                    ),
                ),
            ],
        )
        converter = _make_converter()
        ctx = converter._get_encompassing_encounter_context(_make_mock_ccda(enc))

        assert ctx.display == "Family Medicine"

    def test_no_display_when_no_code_or_participant(self) -> None:
        """When neither code nor participant specialty exists, display is None."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            effective_time=IVL_TS(value="20240122"),
        )
        converter = _make_converter()
        ctx = converter._get_encompassing_encounter_context(_make_mock_ccda(enc))

        assert ctx.display is None

    def test_code_takes_precedence_over_participant(self) -> None:
        """code.displayName takes precedence over participant specialty."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            code=CE(
                code="99213",
                code_system="2.16.840.1.113883.6.12",
                display_name="Office visit",
            ),
            effective_time=IVL_TS(value="20240122"),
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(
                        id=[II(root="2.16.840.1.113883.4.6", extension="999")],
                        code=CE(
                            code="207Q00000X",
                            code_system="2.16.840.1.113883.6.101",
                            display_name="Family Medicine",
                        ),
                    ),
                ),
            ],
        )
        converter = _make_converter()
        ctx = converter._get_encompassing_encounter_context(_make_mock_ccda(enc))

        assert ctx.display == "Office visit"
