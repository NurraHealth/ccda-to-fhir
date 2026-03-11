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
from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.constants import CCDA_TYPECODE_TO_FHIR_RELATES_TO, FHIRCodes
from ccda_to_fhir.converters.note_activity import (
    NoteActivityConverter,
    _convert_author_references,
    _convert_relates_to,
    _convert_type,
    _create_context,
    _create_content_list,
    _create_inline_content,
    _create_missing_content,
    _extract_author_date,
    _extract_doc_status,
    _generate_note_id,
    _make_coding,
    convert_note_activity,
)
from ccda_to_fhir.converters.code_systems import CodeSystemMapper
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


@pytest.fixture
def mapper() -> CodeSystemMapper:
    return CodeSystemMapper()


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
        effective_time=effective_time,
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
# _generate_note_id
# ============================================================================


class TestGenerateNoteId:
    def test_with_identifier(self) -> None:
        identifier = II(root="1.2.3", extension="ext-1")
        result = _generate_note_id(identifier)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_deterministic(self) -> None:
        identifier = II(root="1.2.3", extension="ext-1")
        assert _generate_note_id(identifier) == _generate_note_id(identifier)

    def test_none_generates_uuid(self) -> None:
        result = _generate_note_id(None)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_root_only(self) -> None:
        identifier = II(root="1.2.3")
        result = _generate_note_id(identifier)
        assert isinstance(result, str)

    def test_extension_only(self) -> None:
        identifier = II(extension="ext-1")
        result = _generate_note_id(identifier)
        assert isinstance(result, str)


# ============================================================================
# _extract_doc_status
# ============================================================================


class TestExtractDocStatus:
    def test_completed_maps_to_final(self) -> None:
        act = _make_note_act(status="completed")
        assert _extract_doc_status(act) == "final"

    def test_active_maps_to_preliminary(self) -> None:
        act = _make_note_act(status="active")
        assert _extract_doc_status(act) == "preliminary"

    def test_aborted_returns_none(self) -> None:
        act = _make_note_act(status="aborted")
        assert _extract_doc_status(act) is None

    def test_no_status_returns_none(self) -> None:
        act = _make_note_act()
        act.status_code = None
        assert _extract_doc_status(act) is None

    def test_case_insensitive(self) -> None:
        act = _make_note_act(status="COMPLETED")
        assert _extract_doc_status(act) == "final"


# ============================================================================
# _convert_type
# ============================================================================


class TestConvertType:
    def test_primary_code_mapped(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1", display_name="Note")
        result = _convert_type(code, mapper)
        assert result["coding"][0]["code"] == "34109-9"
        assert result["coding"][0]["system"] == "http://loinc.org"
        assert result["coding"][0]["display"] == "Note"

    def test_translation_codes_included(self, mapper: CodeSystemMapper) -> None:
        code = CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
            translation=[CD(
                code="34117-2",
                code_system="2.16.840.1.113883.6.1",
                display_name="History and physical note",
            )],
        )
        result = _convert_type(code, mapper)
        assert len(result["coding"]) == 2
        assert result["coding"][1]["code"] == "34117-2"

    def test_display_text_set(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1", display_name="Note")
        result = _convert_type(code, mapper)
        assert result["text"] == "Note"

    def test_no_display_omits_text(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1")
        result = _convert_type(code, mapper)
        assert "text" not in result

    def test_fallback_when_no_code(self, mapper: CodeSystemMapper) -> None:
        result = _convert_type(None, mapper)
        assert result["coding"][0]["code"] == "34133-9"
        assert result["text"] == "Clinical Note"

    def test_fallback_when_code_has_no_value(self, mapper: CodeSystemMapper) -> None:
        code = CD(display_name="Note")
        result = _convert_type(code, mapper)
        assert result["coding"][0]["code"] == "34133-9"

    def test_code_without_code_system(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", display_name="Note")
        result = _convert_type(code, mapper)
        coding = result["coding"][0]
        assert coding["code"] == "34109-9"
        assert "system" not in coding


# ============================================================================
# _make_coding
# ============================================================================


class TestMakeCoding:
    def test_full_coding(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", "2.16.840.1.113883.6.1", "Test", mapper)
        assert result == {"code": "12345", "system": "http://loinc.org", "display": "Test"}

    def test_no_code_returns_none(self, mapper: CodeSystemMapper) -> None:
        assert _make_coding(None, "2.16.840.1.113883.6.1", "Test", mapper) is None

    def test_no_system(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", None, "Test", mapper)
        assert result == {"code": "12345", "display": "Test"}

    def test_no_display(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", None, None, mapper)
        assert result == {"code": "12345"}

    def test_unknown_system_uses_oid_urn(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", "9.9.9.9.9", None, mapper)
        assert result is not None
        assert result["system"] == "urn:oid:9.9.9.9.9"


# ============================================================================
# _extract_author_date
# ============================================================================


class TestExtractAuthorDate:
    def test_extracts_date(self) -> None:
        authors = [_make_author()]
        result = _extract_author_date(authors, lambda v: f"converted-{v}")
        assert result == "converted-20260120160000-0500"

    def test_empty_list_returns_none(self) -> None:
        assert _extract_author_date([], lambda v: v) is None

    def test_no_time_returns_none(self) -> None:
        author = _make_author()
        author.time = None
        assert _extract_author_date([author], lambda v: v) is None

    def test_no_time_value_returns_none(self) -> None:
        author = _make_author()
        author.time = TS()
        assert _extract_author_date([author], lambda v: v) is None

    def test_uses_first_author_only(self) -> None:
        a1 = _make_author()
        a1.time = TS(value="20260101")
        a2 = _make_author()
        a2.time = TS(value="20260202")
        result = _extract_author_date([a1, a2], lambda v: v)
        assert result == "20260101"

    def test_converter_returns_none(self) -> None:
        authors = [_make_author()]
        assert _extract_author_date(authors, lambda v: None) is None


# ============================================================================
# _convert_author_references
# ============================================================================


class TestConvertAuthorReferences:
    def test_single_author(self) -> None:
        refs = _convert_author_references([_make_author()])
        assert len(refs) == 1
        assert refs[0]["reference"].startswith("urn:uuid:")

    def test_multiple_authors(self) -> None:
        refs = _convert_author_references([_make_author("111"), _make_author("222")])
        assert len(refs) == 2

    def test_skip_without_assigned_author(self) -> None:
        author = Author(time=TS(value="20260101"))
        assert _convert_author_references([author]) == []

    def test_skip_without_assigned_person(self) -> None:
        author = _make_author()
        author.assigned_author.assigned_person = None
        assert _convert_author_references([author]) == []

    def test_skip_without_id(self) -> None:
        author = _make_author()
        author.assigned_author.id = None
        assert _convert_author_references([author]) == []

    def test_empty_list(self) -> None:
        assert _convert_author_references([]) == []

    def test_deterministic_ids(self) -> None:
        refs1 = _convert_author_references([_make_author()])
        refs2 = _convert_author_references([_make_author()])
        assert refs1[0]["reference"] == refs2[0]["reference"]


# ============================================================================
# _create_inline_content
# ============================================================================


class TestCreateInlineContent:
    def test_base64_passthrough(self) -> None:
        b64_data = base64.b64encode(b"Hello RTF").decode("ascii")
        text = ED(media_type="text/rtf", representation="B64", value=b64_data)
        result = _create_inline_content(text)
        assert result is not None
        assert result["attachment"]["contentType"] == "text/rtf"
        assert result["attachment"]["data"] == b64_data

    def test_base64_whitespace_stripped(self) -> None:
        text = ED(representation="B64", value="AAAA\n BBBB\n CCCC")
        result = _create_inline_content(text)
        assert result is not None
        assert result["attachment"]["data"] == "AAAABBBBCCCC"

    def test_plain_text_encoded(self) -> None:
        text = ED(value="Some clinical note text")
        result = _create_inline_content(text)
        assert result is not None
        assert result["attachment"]["contentType"] == "text/plain"
        decoded = base64.b64decode(result["attachment"]["data"]).decode("utf-8")
        assert decoded == "Some clinical note text"

    def test_default_content_type(self) -> None:
        text = ED(value="note")
        result = _create_inline_content(text)
        assert result is not None
        assert result["attachment"]["contentType"] == "text/plain"

    def test_custom_media_type(self) -> None:
        text = ED(media_type="application/pdf", representation="B64", value="JVBER")
        result = _create_inline_content(text)
        assert result is not None
        assert result["attachment"]["contentType"] == "application/pdf"

    def test_empty_value_returns_none(self) -> None:
        assert _create_inline_content(ED()) is None

    def test_b64_no_value_returns_none(self) -> None:
        assert _create_inline_content(ED(representation="B64")) is None


# ============================================================================
# _create_content_list
# ============================================================================


class TestCreateContentList:
    def test_inline_only(self) -> None:
        text = ED(value="Some text")
        result = _create_content_list(text, section=None)
        assert len(result) == 1
        assert "data" in result[0]["attachment"]

    def test_empty_text_returns_empty(self) -> None:
        text = ED()
        assert _create_content_list(text, section=None) == []

    def test_b64_inline(self) -> None:
        text = ED(representation="B64", value="AQID", media_type="application/pdf")
        result = _create_content_list(text, section=None)
        assert len(result) == 1
        assert result[0]["attachment"]["contentType"] == "application/pdf"

    def test_no_reference_content_without_section(self) -> None:
        from ccda_to_fhir.ccda.models.datatypes import TEL

        text = ED(value="inline", reference=TEL(value="#note-1"))
        result = _create_content_list(text, section=None)
        # reference content skipped when section is None
        assert len(result) == 1


# ============================================================================
# _create_missing_content
# ============================================================================


class TestCreateMissingContent:
    def test_structure(self) -> None:
        fn = lambda nf: {"url": "http://test", "valueCode": "unknown"}
        result = _create_missing_content(fn)
        assert len(result) == 1
        assert result[0]["attachment"]["contentType"] == "text/plain"

    def test_calls_absent_reason_fn(self) -> None:
        calls: list[str | None] = []

        def fake_fn(nf: str | None) -> dict[str, str]:
            calls.append(nf)
            return {"url": "http://test", "valueCode": "unknown"}

        _create_missing_content(fake_fn)
        assert calls == [None]

    def test_extension_in_data(self) -> None:
        ext = {"url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason", "valueCode": "unknown"}
        result = _create_missing_content(lambda nf: ext)
        assert result[0]["attachment"]["_data"]["extension"] == [ext]


# ============================================================================
# _create_context
# ============================================================================


class TestCreateContext:
    def test_period_from_ivl_ts_value(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        result = _create_context(act, lambda v: f"converted-{v}")
        assert result is not None
        assert result["period"]["start"] == "converted-20260115"

    def test_period_from_ivl_ts_low(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(low=TS(value="20260110")))
        result = _create_context(act, lambda v: f"converted-{v}")
        assert result is not None
        assert result["period"]["start"] == "converted-20260110"

    def test_ivl_ts_value_preferred_over_low(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260101", low=TS(value="20260110")))
        result = _create_context(act, lambda v: f"converted-{v}")
        assert result is not None
        assert result["period"]["start"] == "converted-20260101"

    def test_no_effective_time_returns_none(self) -> None:
        act = _make_note_act()
        assert _create_context(act, lambda v: v) is None

    def test_converter_returns_none(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        assert _create_context(act, lambda v: None) is None

    def test_encounter_reference(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-root", extension="enc-1")]),
            )
        ]
        result = _create_context(act, lambda v: v)
        assert result is not None
        assert len(result["encounter"]) == 1
        assert result["encounter"][0]["reference"].startswith("urn:uuid:")

    def test_multiple_encounters(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-1")]),
            ),
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-2")]),
            ),
        ]
        result = _create_context(act, lambda v: v)
        assert result is not None
        assert len(result["encounter"]) == 2

    def test_encounter_without_id_skipped(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(type_code="COMP", encounter=CDAEncounter()),
        ]
        assert _create_context(act, lambda v: v) is None

    def test_both_period_and_encounter(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-1")]),
            ),
        ]
        result = _create_context(act, lambda v: v)
        assert result is not None
        assert "period" in result
        assert "encounter" in result


# ============================================================================
# _convert_relates_to
# ============================================================================


class TestConvertRelatesTo:
    def test_rplc_maps_to_replaces(self) -> None:
        refs = [Reference(
            type_code="RPLC",
            external_document=ExternalDocument(id=[II(root="doc-1", extension="v2")]),
        )]
        result = _convert_relates_to(refs)
        assert len(result) == 1
        assert result[0]["code"] == "replaces"

    def test_apnd_maps_to_appends(self) -> None:
        refs = [Reference(
            type_code="APND",
            external_document=ExternalDocument(id=[II(root="doc-1")]),
        )]
        result = _convert_relates_to(refs)
        assert result[0]["code"] == "appends"

    def test_xfrm_maps_to_transforms(self) -> None:
        refs = [Reference(
            type_code="XFRM",
            external_document=ExternalDocument(id=[II(root="doc-1")]),
        )]
        result = _convert_relates_to(refs)
        assert result[0]["code"] == "transforms"

    def test_refr_skipped(self) -> None:
        refs = [Reference(
            type_code="REFR",
            external_document=ExternalDocument(id=[II(root="doc-1")]),
        )]
        assert _convert_relates_to(refs) == []

    def test_unknown_type_code_skipped(self) -> None:
        refs = [Reference(
            type_code="BOGUS",
            external_document=ExternalDocument(id=[II(root="doc-1")]),
        )]
        assert _convert_relates_to(refs) == []

    def test_none_type_code_skipped(self) -> None:
        refs = [Reference(
            external_document=ExternalDocument(id=[II(root="doc-1")]),
        )]
        assert _convert_relates_to(refs) == []

    def test_no_external_document_skipped(self) -> None:
        refs = [Reference(type_code="RPLC")]
        assert _convert_relates_to(refs) == []

    def test_no_id_skipped(self) -> None:
        refs = [Reference(
            type_code="RPLC",
            external_document=ExternalDocument(),
        )]
        assert _convert_relates_to(refs) == []

    def test_target_uses_generate_id(self) -> None:
        refs = [Reference(
            type_code="RPLC",
            external_document=ExternalDocument(id=[II(root="doc-root", extension="doc-ext")]),
        )]
        result = _convert_relates_to(refs)
        target_ref = result[0]["target"]["reference"]
        assert target_ref.startswith("urn:uuid:")
        # raw OID should NOT appear directly
        assert target_ref != "urn:uuid:doc-root"

    def test_deterministic_ids(self) -> None:
        refs = [Reference(
            type_code="RPLC",
            external_document=ExternalDocument(id=[II(root="doc-1", extension="v1")]),
        )]
        r1 = _convert_relates_to(refs)
        r2 = _convert_relates_to(refs)
        assert r1[0]["target"]["reference"] == r2[0]["target"]["reference"]

    def test_multiple_references(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            ),
            Reference(
                type_code="APND",
                external_document=ExternalDocument(id=[II(root="doc-2")]),
            ),
        ]
        result = _convert_relates_to(refs)
        assert len(result) == 2
        assert result[0]["code"] == "replaces"
        assert result[1]["code"] == "appends"

    def test_mixed_valid_and_invalid(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            ),
            Reference(type_code="REFR", external_document=ExternalDocument(id=[II(root="doc-2")])),
            Reference(type_code="APND"),  # no external_document
        ]
        result = _convert_relates_to(refs)
        assert len(result) == 1
        assert result[0]["code"] == "replaces"

    def test_empty_list(self) -> None:
        assert _convert_relates_to([]) == []


# ============================================================================
# CCDA_TYPECODE_TO_FHIR_RELATES_TO constant
# ============================================================================


class TestRelatesToConstant:
    def test_all_mappings_present(self) -> None:
        assert CCDA_TYPECODE_TO_FHIR_RELATES_TO["RPLC"] == "replaces"
        assert CCDA_TYPECODE_TO_FHIR_RELATES_TO["APND"] == "appends"
        assert CCDA_TYPECODE_TO_FHIR_RELATES_TO["XFRM"] == "transforms"

    def test_refr_not_in_map(self) -> None:
        assert "REFR" not in CCDA_TYPECODE_TO_FHIR_RELATES_TO

    def test_exactly_three_entries(self) -> None:
        assert len(CCDA_TYPECODE_TO_FHIR_RELATES_TO) == 3


# ============================================================================
# Resource structure (integration-level via converter.convert)
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
# Date and author (integration)
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

    def test_multiple_authors(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(authors=[_make_author("111"), _make_author("222")])
        result = converter.convert(act)
        assert len(result["author"]) == 2


# ============================================================================
# Content (integration)
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
# Context (integration)
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
# RelatesTo (integration)
# ============================================================================


class TestRelatesToIntegration:
    def test_rplc_reference(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.reference = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="ext-doc-123", extension="v1")]),
            )
        ]
        result = converter.convert(act)
        relates = result["relatesTo"]
        assert len(relates) == 1
        assert relates[0]["code"] == "replaces"
        assert relates[0]["target"]["reference"].startswith("urn:uuid:")

    def test_refr_not_in_relates_to(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.reference = [
            Reference(
                type_code="REFR",
                external_document=ExternalDocument(id=[II(root="ext-doc-123")]),
            )
        ]
        result = converter.convert(act)
        assert "relatesTo" not in result

    def test_no_relates_to_without_references(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert "relatesTo" not in result


# ============================================================================
# Convenience function
# ============================================================================


class TestFallbackEncounterReference:
    """Tests for encompassingEncounter fallback in _create_context."""

    def test_fallback_used_when_no_explicit_encounter(self) -> None:
        act = _make_note_act()
        result = _create_context(act, lambda v: v, fallback_encounter_reference="urn:uuid:enc-fallback")
        assert result is not None
        assert result["encounter"][0]["reference"] == "urn:uuid:enc-fallback"

    def test_explicit_encounter_takes_precedence(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-explicit")]),
            )
        ]
        result = _create_context(act, lambda v: v, fallback_encounter_reference="urn:uuid:enc-fallback")
        assert result is not None
        # Should use explicit encounter, not fallback
        assert len(result["encounter"]) == 1
        ref = result["encounter"][0]["reference"]
        assert ref != "urn:uuid:enc-fallback"
        assert ref.startswith("urn:uuid:")

    def test_no_fallback_no_encounter_returns_none(self) -> None:
        act = _make_note_act()
        result = _create_context(act, lambda v: v)
        assert result is None

    def test_fallback_combined_with_period(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        result = _create_context(act, lambda v: f"converted-{v}", fallback_encounter_reference="urn:uuid:enc-fb")
        assert result is not None
        assert result["period"]["start"] == "converted-20260115"
        assert result["encounter"][0]["reference"] == "urn:uuid:enc-fb"

    def test_none_fallback_ignored(self) -> None:
        act = _make_note_act()
        result = _create_context(act, lambda v: v, fallback_encounter_reference=None)
        assert result is None


class TestFallbackEncounterIntegration:
    """Integration tests for fallback encounter via converter.convert()."""

    def test_fallback_encounter_on_convert(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act, fallback_encounter_reference="urn:uuid:enc-123")
        assert result["context"]["encounter"][0]["reference"] == "urn:uuid:enc-123"

    def test_explicit_encounter_not_overridden_on_convert(
        self, converter: NoteActivityConverter
    ) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-explicit")]),
            )
        ]
        result = converter.convert(act, fallback_encounter_reference="urn:uuid:enc-fallback")
        enc_ref = result["context"]["encounter"][0]["reference"]
        assert enc_ref != "urn:uuid:enc-fallback"
        assert enc_ref.startswith("urn:uuid:")

    def test_no_fallback_no_context(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert "context" not in result

    def test_convenience_fn_passes_fallback(self, registry: ReferenceRegistry) -> None:
        act = _make_note_act()
        result = convert_note_activity(
            act,
            reference_registry=registry,
            fallback_encounter_reference="urn:uuid:enc-conv",
        )
        assert result["context"]["encounter"][0]["reference"] == "urn:uuid:enc-conv"


class TestConvertNoteActivity:
    def test_convenience_function(self, registry: ReferenceRegistry) -> None:
        act = _make_note_act()
        result = convert_note_activity(act, reference_registry=registry)
        assert result["resourceType"] == "DocumentReference"
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT
