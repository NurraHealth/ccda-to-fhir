"""Unit tests for Encounter.participant.individual display text."""

from ccda_to_fhir.ccda.models.datatypes import CE, CS, ENXP, II, IVL_TS, PN, AssignedPerson
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer
from ccda_to_fhir.converters.encounter import EncounterConverter


def _make_encounter_with_performer(
    given: str,
    family: str,
    suffix: str | None = None,
    npi: str = "9876543210",
) -> CCDAEncounter:
    name = PN(
        given=[ENXP(value=given)],
        family=ENXP(value=family),
        suffix=[ENXP(value=suffix)] if suffix else None,
    )
    entity = AssignedEntity()
    entity.id = [II(root="2.16.840.1.113883.4.6", extension=npi)]
    entity.assigned_person = AssignedPerson(name=[name])

    performer = Performer()
    performer.assigned_entity = entity

    enc = CCDAEncounter()
    enc.id = [II(root="2a620155-9d11-439e-92b3-5d9815ff4de8")]
    enc.code = CE(
        code="99213",
        code_system="2.16.840.1.113883.6.12",
        display_name="Office visit",
    )
    enc.status_code = CS(code="completed")
    enc.effective_time = IVL_TS(value="202003151030-0500")
    enc.performer = [performer]
    return enc


class TestEncounterParticipantDisplay:
    """Encounter.participant.individual should have display from performer name."""

    def test_participant_individual_has_display(self, mock_reference_registry):
        mock_reference_registry.has_resource.return_value = False
        enc = _make_encounter_with_performer("Adam", "Careful")

        converter = EncounterConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(enc)

        participants = result.get("participant", [])
        assert len(participants) >= 1
        individual = participants[0]["individual"]
        assert individual["display"] == "Adam Careful"
        assert individual["reference"].startswith("urn:uuid:")

    def test_participant_display_with_suffix(self, mock_reference_registry):
        mock_reference_registry.has_resource.return_value = False
        enc = _make_encounter_with_performer("Jane", "Doe", suffix="MD")

        converter = EncounterConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(enc)

        individual = result["participant"][0]["individual"]
        assert individual["display"] == "Jane Doe MD"

    def test_participant_no_display_when_no_name(self, mock_reference_registry):
        """Participant without name parts still gets reference, no display."""
        mock_reference_registry.has_resource.return_value = False

        entity = AssignedEntity()
        entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        entity.assigned_person = AssignedPerson(name=[])

        performer = Performer()
        performer.assigned_entity = entity

        enc = CCDAEncounter()
        enc.id = [II(root="test-enc-id")]
        enc.code = CE(code="99213", code_system="2.16.840.1.113883.6.12", display_name="Office visit")
        enc.status_code = CS(code="completed")
        enc.effective_time = IVL_TS(value="202003151030")
        enc.performer = [performer]

        converter = EncounterConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(enc)

        individual = result["participant"][0]["individual"]
        assert individual["reference"].startswith("urn:uuid:")
        assert "display" not in individual

    def test_multiple_participants_each_have_display(self, mock_reference_registry):
        mock_reference_registry.has_resource.return_value = False

        performers = []
        for given, family, npi in [("Adam", "Careful", "1111111111"), ("Beth", "Healer", "2222222222")]:
            name = PN(given=[ENXP(value=given)], family=ENXP(value=family))
            entity = AssignedEntity()
            entity.id = [II(root="2.16.840.1.113883.4.6", extension=npi)]
            entity.assigned_person = AssignedPerson(name=[name])
            p = Performer()
            p.assigned_entity = entity
            performers.append(p)

        enc = CCDAEncounter()
        enc.id = [II(root="test-enc-multi")]
        enc.code = CE(code="99213", code_system="2.16.840.1.113883.6.12", display_name="Office visit")
        enc.status_code = CS(code="completed")
        enc.effective_time = IVL_TS(value="202003151030")
        enc.performer = performers

        converter = EncounterConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(enc)

        displays = [p["individual"]["display"] for p in result["participant"]]
        assert "Adam Careful" in displays
        assert "Beth Healer" in displays
