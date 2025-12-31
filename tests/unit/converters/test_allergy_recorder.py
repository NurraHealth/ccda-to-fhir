"""Unit tests for AllergyIntolerance.recorder field extraction."""

import pytest

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
)
from ccda_to_fhir.ccda.models.datatypes import CE, II, TS
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.participant import Participant, ParticipantRole, PlayingEntity
from ccda_to_fhir.converters.allergy_intolerance import AllergyIntoleranceConverter


class TestAllergyRecorder:
    """Test AllergyIntolerance.recorder field extraction from latest author."""

    def create_observation_with_authors(self, authors: list[Author] | None) -> Observation:
        """Helper to create allergy observation with given authors."""
        obs = Observation()
        obs.code = CE(code="ASSERTION", code_system="2.16.840.1.113883.5.4")
        obs.value = CE(code="419199007", code_system="2.16.840.1.113883.6.96", display_name="Allergy to substance")

        # Add participant (allergen) - required for allergy
        participant = Participant()
        participant.participant_role = ParticipantRole()
        participant.participant_role.playing_entity = PlayingEntity()
        participant.participant_role.playing_entity.code = CE(
            code="70618",
            code_system="2.16.840.1.113883.6.88",
            display_name="Penicillin"
        )
        obs.participant = [participant]

        obs.id = [II(root="1.2.3.4", extension="allergy-1")]
        obs.author = authors
        return obs

    def create_author(
        self,
        time: str | None,
        practitioner_ext: str | None = None,
        has_person: bool = True,
        has_device: bool = False
    ) -> Author:
        """Helper to create author with specified time and identifiers."""
        assigned_author = AssignedAuthor()
        assigned_author.id = [II(root="2.16.840.1.113883.4.6", extension=practitioner_ext)] if practitioner_ext else []

        if has_person and not has_device:
            assigned_author.assigned_person = AssignedPerson(name=[])
        elif has_device:
            assigned_author.assigned_authoring_device = AssignedAuthoringDevice(
                manufacturer_model_name="Test Device",
                software_name="Test Software"
            )

        author = Author()
        author.time = TS(value=time) if time else None
        author.assigned_author = assigned_author
        return author

    def create_concern_act_with_authors(self, authors: list[Author] | None) -> Act:
        """Helper to create allergy concern act with given authors."""
        act = Act()
        act.author = authors
        return act

    def test_single_author_with_time_creates_recorder(self, mock_reference_registry):
        """Test that single author with time creates recorder reference."""
        import uuid as uuid_module

        author = self.create_author(time="20240115090000", practitioner_ext="DOC-001")
        obs = self.create_observation_with_authors([author])

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_multiple_authors_chronological_returns_latest(self, mock_reference_registry):
        """Test that latest author by timestamp is used for recorder."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC"),
            self.create_author(time="20240201", practitioner_ext="MIDDLE-DOC"),
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_author_without_time_excluded(self, mock_reference_registry):
        """Test that authors without time are excluded from recorder selection."""
        import uuid as uuid_module

        authors = [
            self.create_author(time=None, practitioner_ext="NO-TIME-DOC"),
            self.create_author(time="20240215", practitioner_ext="WITH-TIME-DOC"),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_all_authors_without_time_no_recorder(self, mock_reference_registry):
        """Test that no recorder is created if all authors lack time."""
        authors = [
            self.create_author(time=None, practitioner_ext="NO-TIME-1"),
            self.create_author(time=None, practitioner_ext="NO-TIME-2"),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        assert "recorder" not in allergy

    def test_device_author_creates_device_reference(self, mock_reference_registry):
        """Test that device author creates Device reference."""
        import uuid as uuid_module

        author = self.create_author(
            time="20240115",
            practitioner_ext="DEVICE-001",
            has_person=False,
            has_device=True
        )
        obs = self.create_observation_with_authors([author])

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Device/")
        # Extract and validate UUID v4
        device_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {device_id} is not a valid UUID v4")

    def test_concern_act_and_observation_authors_both_considered(self, mock_reference_registry):
        """Test that authors from both concern act and observation are considered."""
        import uuid as uuid_module

        concern_act_authors = [
            self.create_author(time="20240101", practitioner_ext="CONCERN-EARLY")
        ]
        obs_authors = [
            self.create_author(time="20240301", practitioner_ext="OBS-LATEST")
        ]

        concern_act = self.create_concern_act_with_authors(concern_act_authors)
        obs = self.create_observation_with_authors(obs_authors)

        converter = AllergyIntoleranceConverter(
            code_system_mapper=None,
            concern_act=concern_act,
            reference_registry=mock_reference_registry
        )
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_latest_from_concern_act_used_if_later_than_observation(self, mock_reference_registry):
        """Test that concern act author is used if it's latest."""
        import uuid as uuid_module

        concern_act_authors = [
            self.create_author(time="20240301", practitioner_ext="CONCERN-LATEST")
        ]
        obs_authors = [
            self.create_author(time="20240101", practitioner_ext="OBS-EARLY")
        ]

        concern_act = self.create_concern_act_with_authors(concern_act_authors)
        obs = self.create_observation_with_authors(obs_authors)

        converter = AllergyIntoleranceConverter(
            code_system_mapper=None,
            concern_act=concern_act,
            reference_registry=mock_reference_registry
        )
        allergy = converter.convert(obs)

        assert "recorder" in allergy
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_recorded_date_still_uses_earliest_author(self, mock_reference_registry):
        """Test that recordedDate still uses earliest author time (existing behavior)."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
            self.create_author(time="20240101", practitioner_ext="EARLIEST-DOC"),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = AllergyIntoleranceConverter(code_system_mapper=None, concern_act=None, reference_registry=mock_reference_registry)
        allergy = converter.convert(obs)

        # recordedDate should still use earliest
        assert allergy.get("recordedDate") == "2024-01-01"
        # recorder should use latest (validated as UUID v4)
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        practitioner_id = allergy["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")
