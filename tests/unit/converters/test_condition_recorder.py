"""Unit tests for Condition.recorder field extraction."""

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
from ccda_to_fhir.converters.condition import ConditionConverter


class TestConditionRecorder:
    """Test Condition.recorder field extraction from latest author."""

    def create_observation_with_authors(self, authors: list[Author] | None) -> Observation:
        """Helper to create observation with given authors."""
        obs = Observation()
        obs.code = CE(code="55607006", code_system="2.16.840.1.113883.6.96")
        obs.value = CE(code="233604007", code_system="2.16.840.1.113883.6.96", display_name="Pneumonia")
        obs.id = [II(root="1.2.3.4", extension="obs-1")]
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
        """Helper to create concern act with given authors."""
        act = Act()
        act.author = authors
        return act

    def test_single_author_with_time_creates_recorder(self, mock_reference_registry):
        """Test that single author with time creates recorder reference."""
        import uuid as uuid_module

        author = self.create_author(time="20240115090000", practitioner_ext="DOC-001")
        obs = self.create_observation_with_authors([author])

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
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

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_multiple_authors_reverse_chronological_returns_latest(self, mock_reference_registry):
        """Test that latest author is found even if not last in list."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
            self.create_author(time="20240201", practitioner_ext="MIDDLE-DOC"),
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC"),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
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

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
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

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" not in condition

    def test_author_without_id_no_recorder(self, mock_reference_registry):
        """Test that author without ID cannot create recorder reference."""
        author = self.create_author(time="20240115", practitioner_ext=None)
        obs = self.create_observation_with_authors([author])

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" not in condition

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

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Device/")
        # Extract and validate UUID v4
        device_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {device_id} is not a valid UUID v4")

    def test_practitioner_and_device_authors_returns_latest_by_time(self, mock_reference_registry):
        """Test that latest author is selected regardless of type."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240101", practitioner_ext="EARLY-PRAC", has_person=True),
            self.create_author(time="20240301", practitioner_ext="LATE-DEVICE", has_person=False, has_device=True),
            self.create_author(time="20240201", practitioner_ext="MID-PRAC", has_person=True),
        ]
        obs = self.create_observation_with_authors(authors)

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Device/")
        # Extract and validate UUID v4
        device_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {device_id} is not a valid UUID v4")

    def test_empty_authors_list_no_recorder(self, mock_reference_registry):
        """Test that empty authors list does not create recorder."""
        obs = self.create_observation_with_authors([])

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" not in condition

    def test_none_authors_no_recorder(self, mock_reference_registry):
        """Test that None authors does not create recorder."""
        obs = self.create_observation_with_authors(None)

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        assert "recorder" not in condition

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

        converter = ConditionConverter(
            code_system_mapper=None,
            section_code="11450-4",
            concern_act=concern_act,
            reference_registry=mock_reference_registry
        )
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
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

        converter = ConditionConverter(
            code_system_mapper=None,
            section_code="11450-4",
            concern_act=concern_act,
            reference_registry=mock_reference_registry
        )
        condition = converter.convert(obs)

        assert "recorder" in condition
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
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

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)
        condition = converter.convert(obs)

        # recordedDate should still use earliest
        assert condition.get("recordedDate") == "2024-01-01"
        # recorder should use latest (validated as UUID v4)
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")


class TestConditionIDGeneration:
    """Test Condition ID generation, especially for observations without IDs."""

    def test_condition_without_observation_id_gets_unique_id(self, mock_reference_registry):
        """Verify Condition ID generation when C-CDA observation lacks ID.

        Bug #9 Fix: Ensures Conditions always get IDs even when observation.id is missing,
        and that multiple ID-less observations get UNIQUE UUIDs.
        """
        import uuid as uuid_module

        # Create observation WITHOUT id field
        obs1 = Observation()
        obs1.code = CE(code="55607006", code_system="2.16.840.1.113883.6.96")
        obs1.value = CE(code="233604007", code_system="2.16.840.1.113883.6.96", display_name="Pneumonia")
        # Intentionally no id field set

        obs2 = Observation()
        obs2.code = CE(code="44054006", code_system="2.16.840.1.113883.6.96")
        obs2.value = CE(code="73211009", code_system="2.16.840.1.113883.6.96", display_name="Diabetes")
        # Intentionally no id field set

        converter = ConditionConverter(code_system_mapper=None, section_code="11450-4", concern_act=None, reference_registry=mock_reference_registry)

        condition1 = converter.convert(obs1)
        condition2 = converter.convert(obs2)

        # Both conditions should have IDs
        assert "id" in condition1, "Condition without observation.id should still have ID"
        assert "id" in condition2, "Condition without observation.id should still have ID"

        # IDs should be valid UUIDs
        assert condition1["id"], "Condition ID should not be empty"
        assert condition2["id"], "Condition ID should not be empty"

        try:
            uuid_module.UUID(condition1["id"], version=4)
            uuid_module.UUID(condition2["id"], version=4)
        except ValueError:
            pytest.fail("Generated IDs should be valid UUID v4")

        # IDs should be UNIQUE
        assert condition1["id"] != condition2["id"], "Different observations should generate unique IDs"
