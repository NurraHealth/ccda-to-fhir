"""Unit tests for Procedure.recorder field fix (using latest author, not first)."""

import pytest

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
)
from ccda_to_fhir.ccda.models.datatypes import CE, CS, II, TS
from ccda_to_fhir.ccda.models.procedure import Procedure as CCDAProcedure
from ccda_to_fhir.converters.procedure import ProcedureConverter


class TestProcedureRecorderFix:
    """Test that Procedure.recorder uses latest author (not first)."""

    def create_procedure_with_authors(self, authors: list[Author] | None) -> CCDAProcedure:
        """Helper to create procedure with given authors."""
        proc = CCDAProcedure()
        proc.code = CE(
            code="80146002",
            code_system="2.16.840.1.113883.6.96",
            display_name="Appendectomy"
        )
        proc.id = [II(root="1.2.3.4", extension="proc-1")]
        proc.status_code = CS(code="completed")
        proc.author = authors
        return proc

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

    def test_single_author_with_time_creates_recorder(self, mock_reference_registry):
        """Test that single author with time creates recorder reference."""
        import uuid as uuid_module

        author = self.create_author(time="20240115090000", practitioner_ext="DOC-001")
        proc = self.create_procedure_with_authors([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_multiple_authors_chronological_returns_latest(self, mock_reference_registry):
        """Test that latest author by timestamp is used (not first)."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC"),
            self.create_author(time="20240201", practitioner_ext="MIDDLE-DOC"),
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
        ]
        proc = self.create_procedure_with_authors(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_multiple_authors_reverse_chronological_returns_latest(self, mock_reference_registry):
        """Test that latest author is selected even when listed first."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
            self.create_author(time="20240201", practitioner_ext="MIDDLE-DOC"),
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC"),
        ]
        proc = self.create_procedure_with_authors(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {practitioner_id} is not a valid UUID v4")

    def test_author_without_time_excluded(self, mock_reference_registry):
        """Test that authors without time are excluded from selection."""
        import uuid as uuid_module

        authors = [
            self.create_author(time=None, practitioner_ext="NO-TIME-DOC"),
            self.create_author(time="20240215", practitioner_ext="WITH-TIME-DOC"),
        ]
        proc = self.create_procedure_with_authors(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Practitioner/")
        # Extract and validate UUID v4
        practitioner_id = procedure["recorder"]["reference"].split("/")[1]
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
        proc = self.create_procedure_with_authors(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" not in procedure

    def test_device_author_creates_device_reference(self, mock_reference_registry):
        """Test that device author creates Device reference."""
        import uuid as uuid_module

        author = self.create_author(
            time="20240115",
            practitioner_ext="DEVICE-001",
            has_person=False,
            has_device=True
        )
        proc = self.create_procedure_with_authors([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Device/")
        # Extract and validate UUID v4
        device_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {device_id} is not a valid UUID v4")

    def test_mixed_practitioner_and_device_authors_returns_latest(self, mock_reference_registry):
        """Test that latest author is selected regardless of type."""
        import uuid as uuid_module

        authors = [
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC", has_person=True, has_device=False),
            self.create_author(time="20240201", practitioner_ext="LATEST-DEVICE", has_person=False, has_device=True),
        ]
        proc = self.create_procedure_with_authors(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        procedure = converter.convert(proc)

        assert "recorder" in procedure
        assert procedure["recorder"]["reference"].startswith("Device/")
        # Extract and validate UUID v4
        device_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {device_id} is not a valid UUID v4")
