"""Unit tests for Procedure.recorder display text."""

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
)
from ccda_to_fhir.ccda.models.datatypes import CE, CS, ENXP, II, PN, TS
from ccda_to_fhir.ccda.models.procedure import Procedure as CCDAProcedure
from ccda_to_fhir.converters.procedure import ProcedureConverter


def _make_procedure(authors: list[Author]) -> CCDAProcedure:
    proc = CCDAProcedure()
    proc.code = CE(
        code="80146002",
        code_system="2.16.840.1.113883.6.96",
        display_name="Appendectomy",
    )
    proc.id = [II(root="1.2.3.4", extension="proc-1")]
    proc.status_code = CS(code="completed")
    proc.author = authors
    return proc


def _make_author_with_name(
    time: str,
    ext: str,
    given: str,
    family: str,
    suffix: str | None = None,
) -> Author:
    name = PN(
        given=[ENXP(value=given)],
        family=ENXP(value=family),
        suffix=[ENXP(value=suffix)] if suffix else None,
    )
    assigned = AssignedAuthor()
    assigned.id = [II(root="2.16.840.1.113883.4.6", extension=ext)]
    assigned.assigned_person = AssignedPerson(name=[name])
    author = Author()
    author.time = TS(value=time)
    author.assigned_author = assigned
    return author


class TestProcedureRecorderDisplay:
    """Procedure.recorder reference should include display text from author name."""

    def test_recorder_has_display_from_person_name(self, mock_reference_registry):
        author = _make_author_with_name("20240115", "DOC-001", "Sarah", "Documenter", "MD")
        proc = _make_procedure([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        result = converter.convert(proc)

        assert "recorder" in result
        assert result["recorder"]["display"] == "Sarah Documenter MD"
        assert result["recorder"]["reference"].startswith("urn:uuid:")

    def test_recorder_display_without_suffix(self, mock_reference_registry):
        author = _make_author_with_name("20240115", "DOC-002", "John", "Smith")
        proc = _make_procedure([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        result = converter.convert(proc)

        assert result["recorder"]["display"] == "John Smith"

    def test_recorder_display_from_latest_author(self, mock_reference_registry):
        authors = [
            _make_author_with_name("20240101", "EARLY", "Early", "Author"),
            _make_author_with_name("20240301", "LATEST", "Latest", "Author"),
        ]
        proc = _make_procedure(authors)

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        result = converter.convert(proc)

        assert result["recorder"]["display"] == "Latest Author"

    def test_recorder_device_has_display(self, mock_reference_registry):
        assigned = AssignedAuthor()
        assigned.id = [II(root="2.16.840.1.113883.4.6", extension="DEV-001")]
        assigned.assigned_authoring_device = AssignedAuthoringDevice(
            manufacturer_model_name="Acme EHR",
            software_name="v3.0",
        )
        author = Author()
        author.time = TS(value="20240115")
        author.assigned_author = assigned
        proc = _make_procedure([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        result = converter.convert(proc)

        assert "recorder" in result
        assert result["recorder"]["display"] == "Acme EHR (v3.0)"

    def test_recorder_no_display_when_no_name(self, mock_reference_registry):
        """Recorder without name still gets reference, just no display."""
        assigned = AssignedAuthor()
        assigned.id = [II(root="2.16.840.1.113883.4.6", extension="NO-NAME")]
        assigned.assigned_person = AssignedPerson(name=[])
        author = Author()
        author.time = TS(value="20240115")
        author.assigned_author = assigned
        proc = _make_procedure([author])

        converter = ProcedureConverter(code_system_mapper=None, reference_registry=mock_reference_registry)
        result = converter.convert(proc)

        assert "recorder" in result
        assert result["recorder"]["reference"].startswith("urn:uuid:")
        assert "display" not in result["recorder"]
