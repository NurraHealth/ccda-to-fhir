"""Unit tests for encounter display fallback in _get_encompassing_encounter_context.

When encompassingEncounter has no code element, the display should fall back
to the first encounterParticipant's assignedEntity/code/@displayName.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.clinical_document import (
    ClinicalDocument,
    ComponentOf,
    EncompassingEncounter,
    EncounterParticipant,
)
from ccda_to_fhir.ccda.models.datatypes import CE, II, IVL_TS
from ccda_to_fhir.ccda.models.performer import AssignedEntity
from ccda_to_fhir.convert import DocumentConverter


@pytest.fixture
def converter() -> DocumentConverter:
    return DocumentConverter()


def _make_doc(enc: EncompassingEncounter) -> ClinicalDocument:
    """Build a minimal ClinicalDocument with the given encompassingEncounter."""
    return ClinicalDocument(
        component_of=ComponentOf(encompassing_encounter=enc),
    )


class TestEncounterDisplayFromCode:
    """Display comes from encompassingEncounter/code/@displayName."""

    def test_code_display_name_used(self, converter: DocumentConverter) -> None:
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            code=CE(
                code="99213",
                code_system="2.16.840.1.113883.6.12",
                display_name="Office visit",
            ),
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display == "Office visit"

    def test_code_display_takes_precedence_over_participant(
        self, converter: DocumentConverter
    ) -> None:
        """When both code and participant specialty exist, code wins."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            code=CE(
                code="99213",
                code_system="2.16.840.1.113883.6.12",
                display_name="Office visit",
            ),
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(
                        code=CE(
                            code="207Q00000X",
                            code_system="2.16.840.1.113883.6.101",
                            display_name="Family Medicine",
                        ),
                    ),
                ),
            ],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display == "Office visit"


class TestEncounterDisplayFromParticipantSpecialty:
    """Fallback: display from encounterParticipant/assignedEntity/code/@displayName."""

    def test_participant_specialty_fallback(self, converter: DocumentConverter) -> None:
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            effective_time=IVL_TS(value="20240122"),
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(
                        code=CE(
                            code="207Q00000X",
                            code_system="2.16.840.1.113883.6.101",
                            display_name="Family Medicine",
                        ),
                    ),
                ),
            ],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display == "Family Medicine"

    def test_first_participant_with_specialty_used(
        self, converter: DocumentConverter
    ) -> None:
        """When multiple participants exist, first with a specialty code wins."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(),
                ),
                EncounterParticipant(
                    type_code="CON",
                    assigned_entity=AssignedEntity(
                        code=CE(
                            code="208D00000X",
                            code_system="2.16.840.1.113883.6.101",
                            display_name="General Practice",
                        ),
                    ),
                ),
            ],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display == "General Practice"

    def test_participant_without_code_skipped(
        self, converter: DocumentConverter
    ) -> None:
        """Participant without assignedEntity.code produces no display."""
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(),
                ),
            ],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display is None

    def test_participant_with_code_but_no_display_name_skipped(
        self, converter: DocumentConverter
    ) -> None:
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            encounter_participant=[
                EncounterParticipant(
                    type_code="ATND",
                    assigned_entity=AssignedEntity(
                        code=CE(
                            code="207Q00000X",
                            code_system="2.16.840.1.113883.6.101",
                        ),
                    ),
                ),
            ],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display is None


class TestEncounterDisplayNone:
    """No display when neither code nor participant specialty available."""

    def test_no_code_no_participants(self, converter: DocumentConverter) -> None:
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            effective_time=IVL_TS(value="20240122"),
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display is None

    def test_no_component_of(self, converter: DocumentConverter) -> None:
        doc = ClinicalDocument()
        ctx = converter._get_encompassing_encounter_context(doc)
        assert ctx.display is None
        assert ctx.reference is None

    def test_empty_participant_list(self, converter: DocumentConverter) -> None:
        enc = EncompassingEncounter(
            id=[II(root="2.16.840.1.113883.19", extension="enc-1")],
            encounter_participant=[],
        )
        ctx = converter._get_encompassing_encounter_context(_make_doc(enc))
        assert ctx.display is None
