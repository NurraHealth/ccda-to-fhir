"""Unit tests for Encounter.participant.individual display text (#80).

Validates that Encounter participant individual references include display.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.datatypes import CE, ENXP, II, PN, AssignedPerson
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.ccda.models.encounter import Performer
from ccda_to_fhir.ccda.models.performer import AssignedEntity
from ccda_to_fhir.converters.encounter import EncounterConverter
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.id_generator import reset_id_cache


@pytest.fixture(autouse=True)
def _reset_ids():  # pyright: ignore[reportUnusedFunction]
    reset_id_cache()
    yield
    reset_id_cache()


class TestEncounterParticipantDisplay:
    def test_participant_has_person_display(self) -> None:
        """Encounter.participant.individual should include display."""
        registry = ReferenceRegistry()

        encounter = CCDAEncounter(
            performer=[
                Performer(
                    assigned_entity=AssignedEntity(
                        id=[II(root="2.16.840.1.113883.4.6", extension="9999999999")],
                        assigned_person=AssignedPerson(
                            name=[
                                PN(
                                    given=[ENXP(value="Henry")],
                                    family=ENXP(value="Doe"),
                                )
                            ]
                        ),
                    ),
                    function_code=CE(code="PCP", display_name="Primary Care Provider"),
                ),
            ],
        )

        converter = EncounterConverter(reference_registry=registry)
        participants = converter._extract_participants(encounter)

        assert len(participants) >= 1
        individual = participants[0]["individual"]
        assert individual["display"] == "Henry Doe"
        assert individual["reference"].startswith("urn:uuid:")

    def test_participant_no_name_omits_display(self) -> None:
        """When person has no name, display should be absent."""
        registry = ReferenceRegistry()

        encounter = CCDAEncounter(
            performer=[
                Performer(
                    assigned_entity=AssignedEntity(
                        id=[II(root="2.16.840.1.113883.4.6", extension="9999999999")],
                        assigned_person=AssignedPerson(name=[]),
                    ),
                ),
            ],
        )

        converter = EncounterConverter(reference_registry=registry)
        participants = converter._extract_participants(encounter)

        assert len(participants) >= 1
        individual = participants[0]["individual"]
        assert isinstance(individual, dict)
        assert "display" not in individual
