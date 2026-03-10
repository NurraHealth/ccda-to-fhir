"""Unit tests for NoteActivityConverter.

Tests type-safe conversion of C-CDA Note Activity Act (2.16.840.1.113883.10.20.22.4.202)
to FHIR DocumentReference resources per US Core DocumentReference profile.
"""

from __future__ import annotations

import base64

import pytest

from ccda_to_fhir.ccda.models.act import Act, ExternalDocument, Reference
from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
from ccda_to_fhir.ccda.models.datatypes import CD, CS, ED, ENXP, II, IVL_TS, PN, TS
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.note_activity import NoteActivityConverter
from ccda_to_fhir.converters.references import ReferenceRegistry


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


@pytest.fixture
def converter(registry: ReferenceRegistry) -> NoteActivityConverter:
    return NoteActivityConverter(reference_registry=registry)


def _make_note_act(
    *,
    code: CD | None = None,
    status: str = "completed",
    text: ED | None = None,
    effective_time: IVL_TS | None = None,
    authors: list[Author] | None = None,
    note_id: str = "note-1",
) -> Act:
    """Create a Note Activity Act with realistic defaults."""
    return Act(
        class_code="ACT",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.202", extension="2016-11-01")],
        id=[II(root=note_id)],
        code=code or CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
        ),
        text=text,
        status_code=CS(code=status),
        effective_time=effective_time or IVL_TS(value="20260120160000-0500"),
        author=authors,
    )


def _make_author(npi: str = "1234567890") -> Author:
    return Author(
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.119")],
        time=TS(value="20260120160000-0500"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension=npi)],
            assigned_person=AssignedPerson(
                name=[PN(given=[ENXP(value="Dr")], family=ENXP(value="Smith"))],
            ),
        ),
    )


# ============================================================================
# Resource structure
# ============================================================================


class TestResourceStructure:
    def test_resource_type(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert result["resourceType"] == "DocumentReference"

    def test_id_generated(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert result["id"]
        assert isinstance(result["id"], str)

    def test_id_deterministic(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(note_id="abc-123")
        r1 = converter.convert(act)
        r2 = converter.convert(act)
        assert r1["id"] == r2["id"]

    def test_id_fallback_when_no_identifier(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.id = None
        result = converter.convert(act)
        assert result["id"]  # still generates a UUID

    def test_requires_reference_registry(self) -> None:
        converter = NoteActivityConverter(reference_registry=None)
        act = _make_note_act()
        with pytest.raises(ValueError, match="reference_registry is required"):
            converter.convert(act)


# ============================================================================
# Status mapping
# ============================================================================


class TestStatus:
    def test_completed_maps_to_current(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="completed")
        result = converter.convert(act)
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT

    def test_active_maps_to_current(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="active")
        result = converter.convert(act)
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT

    def test_aborted_maps_to_entered_in_error(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="aborted")
        result = converter.convert(act)
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.ENTERED_IN_ERROR

    def test_no_status_defaults_to_current(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.status_code = None
        result = converter.convert(act)
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT


class TestDocStatus:
    def test_completed_maps_to_final(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="completed")
        result = converter.convert(act)
        assert result["docStatus"] == "final"

    def test_active_maps_to_preliminary(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="active")
        result = converter.convert(act)
        assert result["docStatus"] == "preliminary"

    def test_aborted_omits_doc_status(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(status="aborted")
        result = converter.convert(act)
        assert "docStatus" not in result

    def test_no_status_omits_doc_status(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.status_code = None
        result = converter.convert(act)
        assert "docStatus" not in result


# ============================================================================
# Type (code) mapping
# ============================================================================


class TestType:
    def test_primary_code_mapped(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(code=CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
        ))
        result = converter.convert(act)
        doc_type = result["type"]
        coding = doc_type["coding"]
        assert coding[0]["code"] == "34109-9"
        assert coding[0]["system"] == "http://loinc.org"
        assert coding[0]["display"] == "Note"

    def test_translation_codes_included(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(code=CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
            translation=[CD(
                code="34117-2",
                code_system="2.16.840.1.113883.6.1",
                display_name="History and physical note",
            )],
        ))
        result = converter.convert(act)
        codings = result["type"]["coding"]
        assert len(codings) == 2
        assert codings[1]["code"] == "34117-2"
        assert codings[1]["display"] == "History and physical note"

    def test_display_text_set(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(code=CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
        ))
        result = converter.convert(act)
        assert result["type"]["text"] == "Note"

    def test_fallback_when_no_code(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.code = None
        result = converter.convert(act)
        doc_type = result["type"]
        assert doc_type["coding"][0]["code"] == "34133-9"
        assert doc_type["text"] == "Clinical Note"

    def test_code_without_code_system(self, converter: NoteActivityConverter) -> None:
        """Athena-style note code without codeSystem attribute."""
        act = _make_note_act(code=CD(code="34109-9", display_name="Note"))
        result = converter.convert(act)
        coding = result["type"]["coding"][0]
        assert coding["code"] == "34109-9"
        assert "system" not in coding


# ============================================================================
# Category
# ============================================================================


class TestCategory:
    def test_category_is_clinical_note(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        category = result["category"]
        assert len(category) == 1
        coding = category[0]["coding"][0]
        assert coding["code"] == "clinical-note"
        assert "us-core-documentreference-category" in coding["system"]


# ============================================================================
# Subject
# ============================================================================


class TestSubject:
    def test_subject_references_patient(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert result["subject"]["reference"] == "urn:uuid:test-patient"


# ============================================================================
# Date and author
# ============================================================================


class TestDateAndAuthor:
    def test_date_from_first_author_time(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(authors=[_make_author()])
        result = converter.convert(act)
        assert result["date"] == "2026-01-20T16:00:00-05:00"

    def test_no_date_without_author(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert "date" not in result

    def test_no_date_when_author_has_no_time(self, converter: NoteActivityConverter) -> None:
        author = _make_author()
        author.time = None
        act = _make_note_act(authors=[author])
        result = converter.convert(act)
        assert "date" not in result

    def test_author_reference_created(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(authors=[_make_author()])
        result = converter.convert(act)
        assert len(result["author"]) == 1
        assert result["author"][0]["reference"].startswith("urn:uuid:")

    def test_author_without_person_skipped(self, converter: NoteActivityConverter) -> None:
        author = _make_author()
        author.assigned_author.assigned_person = None
        act = _make_note_act(authors=[author])
        result = converter.convert(act)
        assert "author" not in result


# ============================================================================
# Content
# ============================================================================


class TestContent:
    def test_base64_content_passthrough(self, converter: NoteActivityConverter) -> None:
        b64_data = base64.b64encode(b"Hello RTF").decode("ascii")
        act = _make_note_act(text=ED(
            media_type="text/rtf",
            representation="B64",
            value=b64_data,
        ))
        result = converter.convert(act)
        content = result["content"]
        assert len(content) == 1
        attachment = content[0]["attachment"]
        assert attachment["contentType"] == "text/rtf"
        assert attachment["data"] == b64_data

    def test_plain_text_encoded(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(text=ED(value="Some clinical note text"))
        result = converter.convert(act)
        attachment = result["content"][0]["attachment"]
        assert attachment["contentType"] == "text/plain"
        decoded = base64.b64decode(attachment["data"]).decode("utf-8")
        assert decoded == "Some clinical note text"

    def test_base64_whitespace_stripped(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(text=ED(
            representation="B64",
            value="AAAA\n BBBB\n CCCC",
        ))
        result = converter.convert(act)
        assert result["content"][0]["attachment"]["data"] == "AAAABBBBCCCC"

    def test_missing_text_uses_data_absent_reason(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        content = result["content"]
        assert len(content) == 1
        attachment = content[0]["attachment"]
        assert attachment["contentType"] == "text/plain"
        assert "_data" in attachment
        ext = attachment["_data"]["extension"][0]
        assert ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"

    def test_empty_text_uses_data_absent_reason(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(text=ED())
        result = converter.convert(act)
        assert "_data" in result["content"][0]["attachment"]

    def test_default_content_type_is_text_plain(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(text=ED(value="note text"))
        result = converter.convert(act)
        assert result["content"][0]["attachment"]["contentType"] == "text/plain"

    def test_custom_media_type_preserved(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(text=ED(
            media_type="application/pdf",
            representation="B64",
            value="JVBER",
        ))
        result = converter.convert(act)
        assert result["content"][0]["attachment"]["contentType"] == "application/pdf"


# ============================================================================
# Context
# ============================================================================


class TestContext:
    def test_period_from_effective_time_value(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        result = converter.convert(act)
        assert result["context"]["period"]["start"] == "2026-01-15"

    def test_period_from_effective_time_low(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(effective_time=IVL_TS(low=TS(value="20260110")))
        result = converter.convert(act)
        assert result["context"]["period"]["start"] == "2026-01-10"

    def test_no_context_without_effective_time(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.effective_time = None
        result = converter.convert(act)
        assert "context" not in result

    def test_encounter_reference_from_entry_relationship(
        self, converter: NoteActivityConverter
    ) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(
                    id=[II(root="enc-root", extension="enc-1")],
                ),
            )
        ]
        result = converter.convert(act)
        enc_refs = result["context"]["encounter"]
        assert len(enc_refs) == 1
        assert enc_refs[0]["reference"].startswith("urn:uuid:")


# ============================================================================
# RelatesTo
# ============================================================================


class TestRelatesTo:
    def test_relates_to_from_external_document(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.reference = [
            Reference(
                type_code="REFR",
                external_document=ExternalDocument(
                    id=[II(root="ext-doc-123")],
                ),
            )
        ]
        result = converter.convert(act)
        relates = result["relatesTo"]
        assert len(relates) == 1
        assert relates[0]["code"] == "appends"
        assert relates[0]["target"]["reference"] == "urn:uuid:ext-doc-123"

    def test_no_relates_to_without_references(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert "relatesTo" not in result


# ============================================================================
# Convenience function
# ============================================================================


class TestConvertNoteActivity:
    def test_convenience_function(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.note_activity import convert_note_activity

        act = _make_note_act()
        result = convert_note_activity(act, reference_registry=registry)
        assert result["resourceType"] == "DocumentReference"
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT
