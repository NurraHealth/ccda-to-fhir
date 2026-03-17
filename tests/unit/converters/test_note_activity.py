"""Unit tests for NoteActivityConverter.

Tests type-safe conversion of C-CDA Note Activity Act (2.16.840.1.113883.10.20.22.4.202)
to FHIR DocumentReference resources per US Core DocumentReference profile.
"""

from __future__ import annotations

import base64

import pytest
from fhir.resources.R4B.attachment import Attachment
from fhir.resources.R4B.documentreference import (
    DocumentReferenceContent,
    DocumentReferenceRelatesTo,
)
from fhir.resources.R4B.period import Period
from pydantic import ValidationError

from ccda_to_fhir.ccda.models.act import Act, ExternalDocument, Reference
from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedPerson,
    Author,
)
from ccda_to_fhir.ccda.models.datatypes import CD, CS, ED, ENXP, II, IVL_TS, PN, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.constants import CCDA_TYPECODE_TO_FHIR_RELATES_TO, FHIRCodes
from ccda_to_fhir.converters.author_references import build_author_references
from ccda_to_fhir.converters.code_systems import CodeSystemMapper
from ccda_to_fhir.converters.note_activity import (
    NoteActivityConverter,
    _convert_relates_to,
    _convert_type,
    _create_content_list,
    _create_context,
    _create_inline_content,
    _create_missing_content,
    _extract_author_date,
    _extract_doc_status,
    _generate_note_id,
    _make_coding,
    convert_note_activity,
)
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.types import (
    EncounterContext,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRDocRefContext,
    FHIRReference,
)

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
        code=code
        or CD(
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
# _convert_type — returns FHIRCodeableConcept
# ============================================================================


class TestConvertType:
    def test_primary_code_mapped(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1", display_name="Note")
        result = _convert_type(code, mapper)
        assert isinstance(result, FHIRCodeableConcept)
        assert result.coding[0].code == "34109-9"
        assert result.coding[0].system == "http://loinc.org"
        assert result.coding[0].display == "Note"

    def test_translation_codes_included(self, mapper: CodeSystemMapper) -> None:
        code = CD(
            code="34109-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Note",
            translation=[
                CD(
                    code="34117-2",
                    code_system="2.16.840.1.113883.6.1",
                    display_name="History and physical note",
                )
            ],
        )
        result = _convert_type(code, mapper)
        assert len(result.coding) == 2
        assert result.coding[1].code == "34117-2"

    def test_display_text_set(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1", display_name="Note")
        result = _convert_type(code, mapper)
        assert result.text == "Note"

    def test_no_display_omits_text(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1")
        result = _convert_type(code, mapper)
        assert result.text is None

    def test_fallback_when_no_code(self, mapper: CodeSystemMapper) -> None:
        result = _convert_type(None, mapper)
        assert result.coding[0].code == "34133-9"
        assert result.text == "Clinical Note"

    def test_fallback_when_code_has_no_value(self, mapper: CodeSystemMapper) -> None:
        code = CD(display_name="Note")
        result = _convert_type(code, mapper)
        assert result.coding[0].code == "34133-9"

    def test_code_without_code_system_preserves_display(self, mapper: CodeSystemMapper) -> None:
        """Per FHIR R4: system SHALL be present when code is present.
        When code_system is missing, code is dropped but display is preserved."""
        code = CD(code="34109-9", display_name="Note")
        result = _convert_type(code, mapper)
        assert result.coding[0].display == "Note"
        assert result.coding[0].system is None
        assert result.coding[0].code is None

    def test_type_to_dict_with_primary_code(self, mapper: CodeSystemMapper) -> None:
        code = CD(code="34109-9", code_system="2.16.840.1.113883.6.1", display_name="Note")
        result = _convert_type(code, mapper)
        d = result.to_dict()
        assert d["coding"][0]["code"] == "34109-9"
        assert d["text"] == "Note"

    def test_type_to_dict_with_fallback(self, mapper: CodeSystemMapper) -> None:
        result = _convert_type(None, mapper)
        d = result.to_dict()
        assert d["coding"][0]["system"] == "http://loinc.org"
        assert d["coding"][0]["code"] == "34133-9"
        assert d["text"] == "Clinical Note"


# ============================================================================
# _make_coding — returns FHIRCoding | None
# ============================================================================


class TestMakeCoding:
    def test_full_coding(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", "2.16.840.1.113883.6.1", "Test", mapper)
        assert result is not None
        assert isinstance(result, FHIRCoding)
        assert result.code == "12345"
        assert result.system == "http://loinc.org"
        assert result.display == "Test"

    def test_no_code_returns_none(self, mapper: CodeSystemMapper) -> None:
        assert _make_coding(None, "2.16.840.1.113883.6.1", "Test", mapper) is None

    def test_no_system_preserves_display(self, mapper: CodeSystemMapper) -> None:
        """Per FHIR R4: system SHALL co-occur with code. Falls back to display-only."""
        result = _make_coding("12345", None, "Test", mapper)
        assert result is not None
        assert result.code is None
        assert result.system is None
        assert result.display == "Test"

    def test_no_system_no_display_returns_none(self, mapper: CodeSystemMapper) -> None:
        """Code without system or display cannot produce a valid coding."""
        result = _make_coding("12345", None, None, mapper)
        assert result is None

    def test_unknown_system_uses_oid_urn(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", "9.9.9.9.9", None, mapper)
        assert result is not None
        assert result.system == "urn:oid:9.9.9.9.9"

    def test_coding_to_dict_with_system(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", "2.16.840.1.113883.6.1", "Test", mapper)
        assert result is not None
        d = result.to_dict()
        assert d == {"code": "12345", "system": "http://loinc.org", "display": "Test"}

    def test_coding_to_dict_display_only(self, mapper: CodeSystemMapper) -> None:
        result = _make_coding("12345", None, "Test", mapper)
        assert result is not None
        d = result.to_dict()
        assert d == {"display": "Test"}


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
# build_author_references
# ============================================================================


class TestConvertAuthorReferences:
    def test_single_author(self) -> None:
        refs = build_author_references([_make_author()])
        assert len(refs) == 1
        assert refs[0].reference.startswith("urn:uuid:")

    def test_multiple_authors(self) -> None:
        refs = build_author_references([_make_author("111"), _make_author("222")])
        assert len(refs) == 2

    def test_skip_without_assigned_author(self) -> None:
        author = Author(time=TS(value="20260101"))
        assert build_author_references([author]) == []

    def test_skip_without_assigned_person(self) -> None:
        author = _make_author()
        author.assigned_author.assigned_person = None
        assert build_author_references([author]) == []

    def test_skip_without_id(self) -> None:
        author = _make_author()
        author.assigned_author.id = None
        assert build_author_references([author]) == []

    def test_empty_list(self) -> None:
        assert build_author_references([]) == []

    def test_deterministic_ids(self) -> None:
        refs1 = build_author_references([_make_author()])
        refs2 = build_author_references([_make_author()])
        assert refs1[0].reference == refs2[0].reference


# ============================================================================
# _create_inline_content — returns DocumentReferenceContent | None
# ============================================================================


class TestCreateInlineContent:
    def test_base64_passthrough(self) -> None:
        b64_data = base64.b64encode(b"Hello RTF").decode("ascii")
        text = ED(media_type="text/rtf", representation="B64", value=b64_data)
        result = _create_inline_content(text)
        assert result is not None
        assert isinstance(result, DocumentReferenceContent)
        assert result.attachment.contentType == "text/rtf"
        assert result.attachment.data == b"Hello RTF"

    def test_base64_whitespace_stripped(self) -> None:
        text = ED(representation="B64", value="AAAA\n BBBB\n CCCC")
        result = _create_inline_content(text)
        assert result is not None
        d = result.model_dump(exclude_none=True, mode="json")
        assert d["attachment"]["data"] == "AAAABBBBCCCC"

    def test_plain_text_encoded(self) -> None:
        text = ED(value="Some clinical note text")
        result = _create_inline_content(text)
        assert result is not None
        assert result.attachment.contentType == "text/plain"
        assert result.attachment.data == b"Some clinical note text"

    def test_default_content_type(self) -> None:
        text = ED(value="note")
        result = _create_inline_content(text)
        assert result is not None
        assert result.attachment.contentType == "text/plain"

    def test_custom_media_type(self) -> None:
        text = ED(media_type="application/pdf", representation="B64", value="JVBER0==")
        result = _create_inline_content(text)
        assert result is not None
        assert result.attachment.contentType == "application/pdf"

    def test_empty_value_returns_none(self) -> None:
        assert _create_inline_content(ED()) is None

    def test_b64_no_value_returns_none(self) -> None:
        assert _create_inline_content(ED(representation="B64")) is None

    def test_inline_content_to_dict(self) -> None:
        text = ED(value="note text", media_type="text/plain")
        result = _create_inline_content(text)
        assert result is not None
        d = result.model_dump(exclude_none=True, mode="json")
        assert "attachment" in d
        assert d["attachment"]["contentType"] == "text/plain"
        assert isinstance(d["attachment"]["data"], str)


# ============================================================================
# _create_content_list — returns list[DocumentReferenceContent]
# ============================================================================


class TestCreateContentList:
    def test_inline_only(self) -> None:
        text = ED(value="Some text")
        result = _create_content_list(text, section=None)
        assert len(result) == 1
        assert isinstance(result[0], DocumentReferenceContent)
        assert result[0].attachment.data is not None

    def test_empty_text_returns_empty(self) -> None:
        text = ED()
        assert _create_content_list(text, section=None) == []

    def test_b64_inline(self) -> None:
        text = ED(representation="B64", value="AQID", media_type="application/pdf")
        result = _create_content_list(text, section=None)
        assert len(result) == 1
        assert result[0].attachment.contentType == "application/pdf"

    def test_no_reference_content_without_section(self) -> None:
        from ccda_to_fhir.ccda.models.datatypes import TEL

        text = ED(value="inline", reference=TEL(value="#note-1"))
        result = _create_content_list(text, section=None)
        # reference content skipped when section is None
        assert len(result) == 1


# ============================================================================
# _create_missing_content — returns list[JSONObject] (pre-serialized)
# ============================================================================


class TestCreateMissingContent:
    def test_returns_single_element(self) -> None:
        result = _create_missing_content()
        assert len(result) == 1
        assert isinstance(result[0], dict)
        assert result[0]["attachment"]["contentType"] == "text/plain"

    def test_data_absent_reason_extension(self) -> None:
        result = _create_missing_content()
        ext_list = result[0]["attachment"]["_data"]["extension"]
        assert len(ext_list) == 1
        assert ext_list[0]["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert ext_list[0]["valueCode"] == "unknown"


# ============================================================================
# _create_context — returns FHIRDocRefContext | None
# ============================================================================


class TestCreateContext:
    _NO_ENC = EncounterContext()

    def test_period_from_ivl_ts_value(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        result = _create_context(act, lambda v: "2026-01-15", self._NO_ENC)
        assert result is not None
        assert isinstance(result, FHIRDocRefContext)
        assert result.period is not None
        assert result.period.start == "2026-01-15"

    def test_period_from_ivl_ts_low(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(low=TS(value="20260110")))
        result = _create_context(act, lambda v: "2026-01-10", self._NO_ENC)
        assert result is not None
        assert result.period is not None
        assert result.period.start == "2026-01-10"

    def test_ivl_ts_value_preferred_over_low(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260101", low=TS(value="20260110")))
        result = _create_context(act, lambda v: "2026-01-01", self._NO_ENC)
        assert result is not None
        assert result.period is not None
        assert result.period.start == "2026-01-01"

    def test_no_effective_time_returns_none(self) -> None:
        act = _make_note_act()
        assert _create_context(act, lambda v: v, self._NO_ENC) is None

    def test_converter_returns_none(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        assert _create_context(act, lambda v: None, self._NO_ENC) is None

    def test_encounter_reference(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-root", extension="enc-1")]),
            )
        ]
        result = _create_context(act, lambda v: v, self._NO_ENC)
        assert result is not None
        assert len(result.encounter) == 1
        assert result.encounter[0].reference.startswith("urn:uuid:")

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
        result = _create_context(act, lambda v: v, self._NO_ENC)
        assert result is not None
        assert len(result.encounter) == 2

    def test_encounter_without_id_skipped(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(type_code="COMP", encounter=CDAEncounter()),
        ]
        assert _create_context(act, lambda v: v, self._NO_ENC) is None

    def test_both_period_and_encounter(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-1")]),
            ),
        ]
        result = _create_context(act, lambda v: "2026-01-15", self._NO_ENC)
        assert result is not None
        assert result.period is not None
        assert len(result.encounter) == 1

    def test_context_to_dict_with_period_and_encounter(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-1")]),
            ),
        ]
        result = _create_context(act, lambda v: "2026-01-15", self._NO_ENC)
        assert result is not None
        d = result.to_dict()
        assert d["period"]["start"] == "2026-01-15"
        assert d["encounter"][0]["reference"].startswith("urn:uuid:")


# ============================================================================
# _convert_relates_to — returns list[DocumentReferenceRelatesTo]
# ============================================================================


class TestConvertRelatesTo:
    def test_rplc_maps_to_replaces(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-1", extension="v2")]),
            )
        ]
        result = _convert_relates_to(refs)
        assert len(result) == 1
        assert isinstance(result[0], DocumentReferenceRelatesTo)
        assert result[0].code == "replaces"

    def test_apnd_maps_to_appends(self) -> None:
        refs = [
            Reference(
                type_code="APND",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            )
        ]
        result = _convert_relates_to(refs)
        assert result[0].code == "appends"

    def test_xfrm_maps_to_transforms(self) -> None:
        refs = [
            Reference(
                type_code="XFRM",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            )
        ]
        result = _convert_relates_to(refs)
        assert result[0].code == "transforms"

    def test_refr_skipped(self) -> None:
        refs = [
            Reference(
                type_code="REFR",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            )
        ]
        assert _convert_relates_to(refs) == []

    def test_unknown_type_code_skipped(self) -> None:
        refs = [
            Reference(
                type_code="BOGUS",
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            )
        ]
        assert _convert_relates_to(refs) == []

    def test_none_type_code_skipped(self) -> None:
        refs = [
            Reference(
                external_document=ExternalDocument(id=[II(root="doc-1")]),
            )
        ]
        assert _convert_relates_to(refs) == []

    def test_no_external_document_skipped(self) -> None:
        refs = [Reference(type_code="RPLC")]
        assert _convert_relates_to(refs) == []

    def test_no_id_skipped(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(),
            )
        ]
        assert _convert_relates_to(refs) == []

    def test_target_uses_generate_id(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-root", extension="doc-ext")]),
            )
        ]
        result = _convert_relates_to(refs)
        target_ref = result[0].target.reference
        assert target_ref.startswith("urn:uuid:")
        # raw OID should NOT appear directly
        assert target_ref != "urn:uuid:doc-root"

    def test_deterministic_ids(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-1", extension="v1")]),
            )
        ]
        r1 = _convert_relates_to(refs)
        r2 = _convert_relates_to(refs)
        assert r1[0].target.reference == r2[0].target.reference

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
        assert result[0].code == "replaces"
        assert result[1].code == "appends"

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
        assert result[0].code == "replaces"

    def test_empty_list(self) -> None:
        assert _convert_relates_to([]) == []

    def test_relates_to_serializes_to_fhir_dict(self) -> None:
        refs = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="doc-1", extension="v1")]),
            )
        ]
        result = _convert_relates_to(refs)
        d = result[0].model_dump(exclude_none=True, mode="json")
        assert d["code"] == "replaces"
        assert d["target"]["reference"].startswith("urn:uuid:")


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
        act = _make_note_act(
            code=CD(
                code="34109-9",
                code_system="2.16.840.1.113883.6.1",
                display_name="Note",
            )
        )
        result = converter.convert(act)
        doc_type = result["type"]
        coding = doc_type["coding"]
        assert coding[0]["code"] == "34109-9"
        assert coding[0]["system"] == "http://loinc.org"
        assert coding[0]["display"] == "Note"

    def test_translation_codes_included(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(
            code=CD(
                code="34109-9",
                code_system="2.16.840.1.113883.6.1",
                display_name="Note",
                translation=[
                    CD(
                        code="34117-2",
                        code_system="2.16.840.1.113883.6.1",
                        display_name="History and physical note",
                    )
                ],
            )
        )
        result = converter.convert(act)
        codings = result["type"]["coding"]
        assert len(codings) == 2
        assert codings[1]["code"] == "34117-2"
        assert codings[1]["display"] == "History and physical note"

    def test_display_text_set(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act(
            code=CD(
                code="34109-9",
                code_system="2.16.840.1.113883.6.1",
                display_name="Note",
            )
        )
        result = converter.convert(act)
        assert result["type"]["text"] == "Note"

    def test_fallback_when_no_code(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        act.code = None
        result = converter.convert(act)
        doc_type = result["type"]
        assert doc_type["coding"][0]["code"] == "34133-9"
        assert doc_type["text"] == "Clinical Note"

    def test_code_without_code_system_preserves_display(
        self, converter: NoteActivityConverter
    ) -> None:
        """Per FHIR R4: system SHALL co-occur with code. Display preserved."""
        act = _make_note_act(code=CD(code="34109-9", display_name="Note"))
        result = converter.convert(act)
        coding = result["type"]["coding"][0]
        assert coding["display"] == "Note"
        assert "code" not in coding
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
        act = _make_note_act(
            text=ED(
                media_type="text/rtf",
                representation="B64",
                value=b64_data,
            )
        )
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
        act = _make_note_act(
            text=ED(
                representation="B64",
                value="AAAA\n BBBB\n CCCC",
            )
        )
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
        act = _make_note_act(
            text=ED(
                media_type="application/pdf",
                representation="B64",
                value="JVBER0==",
            )
        )
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
        ctx = EncounterContext(reference="urn:uuid:enc-fallback")
        result = _create_context(act, lambda v: v, ctx)
        assert result is not None
        assert result.encounter[0].reference == "urn:uuid:enc-fallback"

    def test_explicit_encounter_takes_precedence(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-explicit")]),
            )
        ]
        ctx = EncounterContext(reference="urn:uuid:enc-fallback")
        result = _create_context(act, lambda v: v, ctx)
        assert result is not None
        # Should use explicit encounter, not fallback
        assert len(result.encounter) == 1
        ref = result.encounter[0].reference
        assert ref != "urn:uuid:enc-fallback"
        assert ref.startswith("urn:uuid:")

    def test_no_fallback_no_encounter_returns_none(self) -> None:
        act = _make_note_act()
        result = _create_context(act, lambda v: v, EncounterContext())
        assert result is None

    def test_fallback_combined_with_period(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        ctx = EncounterContext(reference="urn:uuid:enc-fb")
        result = _create_context(act, lambda v: "2026-01-15", ctx)
        assert result is not None
        assert result.period is not None
        assert result.period.start == "2026-01-15"
        assert result.encounter[0].reference == "urn:uuid:enc-fb"

    def test_empty_context_no_encounter(self) -> None:
        act = _make_note_act()
        result = _create_context(act, lambda v: v, EncounterContext())
        assert result is None


class TestFallbackEncounterDisplay:
    """Tests for encounter display text on fallback encounter references."""

    def test_display_set_on_fallback(self) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-fb", display="Pneumonia")
        result = _create_context(act, lambda v: v, ctx)
        assert result is not None
        enc_ref = result.encounter[0]
        assert enc_ref.reference == "urn:uuid:enc-fb"
        assert enc_ref.display == "Pneumonia"

    def test_no_display_when_none(self) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-fb")
        result = _create_context(act, lambda v: v, ctx)
        assert result is not None
        enc_ref = result.encounter[0]
        assert enc_ref.reference == "urn:uuid:enc-fb"
        assert enc_ref.display is None

    def test_display_not_applied_to_explicit_encounter(self) -> None:
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-explicit")]),
            )
        ]
        ctx = EncounterContext(reference="urn:uuid:enc-fb", display="Office visit")
        result = _create_context(act, lambda v: v, ctx)
        assert result is not None
        enc_ref = result.encounter[0]
        assert enc_ref.display is None

    def test_display_combined_with_period(self) -> None:
        act = _make_note_act(effective_time=IVL_TS(value="20260115"))
        ctx = EncounterContext(reference="urn:uuid:enc-fb", display="Checkup")
        result = _create_context(act, lambda v: "2026-01-15", ctx)
        assert result is not None
        assert result.period is not None
        assert result.period.start == "2026-01-15"
        assert result.encounter[0].display == "Checkup"


class TestFallbackEncounterIntegration:
    """Integration tests for fallback encounter via converter.convert()."""

    def test_fallback_encounter_on_convert(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-123")
        result = converter.convert(act, fallback_encounter_context=ctx)
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
        ctx = EncounterContext(reference="urn:uuid:enc-fallback")
        result = converter.convert(act, fallback_encounter_context=ctx)
        enc_ref = result["context"]["encounter"][0]["reference"]
        assert enc_ref != "urn:uuid:enc-fallback"
        assert enc_ref.startswith("urn:uuid:")

    def test_no_fallback_no_context(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        result = converter.convert(act)
        assert "context" not in result

    def test_convenience_fn_passes_fallback(self, registry: ReferenceRegistry) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-conv")
        result = convert_note_activity(
            act, reference_registry=registry, fallback_encounter_context=ctx
        )
        assert result["context"]["encounter"][0]["reference"] == "urn:uuid:enc-conv"

    def test_display_on_convert(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-123", display="Pneumonia")
        result = converter.convert(act, fallback_encounter_context=ctx)
        enc_ref = result["context"]["encounter"][0]
        assert enc_ref["reference"] == "urn:uuid:enc-123"
        assert enc_ref["display"] == "Pneumonia"

    def test_no_display_on_convert_when_none(self, converter: NoteActivityConverter) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-123")
        result = converter.convert(act, fallback_encounter_context=ctx)
        enc_ref = result["context"]["encounter"][0]
        assert enc_ref == {"reference": "urn:uuid:enc-123"}

    def test_convenience_fn_passes_display(self, registry: ReferenceRegistry) -> None:
        act = _make_note_act()
        ctx = EncounterContext(reference="urn:uuid:enc-conv", display="Office visit")
        result = convert_note_activity(
            act, reference_registry=registry, fallback_encounter_context=ctx
        )
        enc_ref = result["context"]["encounter"][0]
        assert enc_ref["display"] == "Office visit"


class TestConvertNoteActivity:
    def test_convenience_function(self, registry: ReferenceRegistry) -> None:
        act = _make_note_act()
        result = convert_note_activity(act, reference_registry=registry)
        assert result["resourceType"] == "DocumentReference"
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT


# ============================================================================
# Pydantic model type safety
# ============================================================================


class TestPydanticModelTypeSafety:
    """Tests verifying that Pydantic models enforce type constraints."""

    def test_fhir_coding_system_code_co_occurrence(self) -> None:
        with pytest.raises(ValueError, match="system and code must both be provided"):
            FHIRCoding(system="http://loinc.org")

    def test_fhir_coding_code_without_system_rejected(self) -> None:
        with pytest.raises(ValueError, match="system and code must both be provided"):
            FHIRCoding(code="12345")

    def test_fhir_coding_display_only_allowed(self) -> None:
        coding = FHIRCoding(display="Some display")
        assert coding.display == "Some display"
        assert coding.system is None
        assert coding.code is None

    def test_attachment_frozen(self) -> None:
        att = Attachment(contentType="text/plain", data="aGVsbG8=")
        with pytest.raises(ValidationError):
            att.data = b"world"

    def test_fhir_doc_ref_context_falsy_when_empty(self) -> None:
        ctx = FHIRDocRefContext()
        assert not ctx

    def test_fhir_doc_ref_context_truthy_with_period(self) -> None:
        ctx = FHIRDocRefContext(period=Period(start="2026-01-01"))
        assert ctx

    def test_fhir_doc_ref_context_truthy_with_encounter(self) -> None:
        ctx = FHIRDocRefContext(encounter=[FHIRReference(reference="urn:uuid:enc-1")])
        assert ctx

    def test_relates_to_construction(self) -> None:
        from fhir.resources.R4B.reference import Reference as LibRef

        rt = DocumentReferenceRelatesTo(
            code="replaces",
            target=LibRef(reference="urn:uuid:doc-1"),
        )
        assert rt.code == "replaces"
        assert rt.target.reference == "urn:uuid:doc-1"

    def test_period_model_dump_omits_none(self) -> None:
        p = Period(start="2026-01-01")
        d = p.model_dump(exclude_none=True, mode="json")
        assert d == {"start": "2026-01-01"}

    def test_period_model_dump_both(self) -> None:
        p = Period(start="2026-01-01", end="2026-02-01")
        d = p.model_dump(exclude_none=True, mode="json")
        assert d == {"start": "2026-01-01", "end": "2026-02-01"}

    def test_attachment_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            Attachment(contentType="text/plain", bogus="field")

    def test_doc_ref_content_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            DocumentReferenceContent(
                attachment=Attachment(contentType="text/plain"),
                bogus="field",
            )


# ============================================================================
# Edge cases
# ============================================================================


class TestEdgeCases:
    """Edge case tests for robustness and spec compliance."""

    def test_ivl_ts_without_value_or_low(self) -> None:
        """IVL_TS with only high and no value/low should not produce a period."""
        act = _make_note_act(effective_time=IVL_TS(high=TS(value="20260201")))
        result = _create_context(act, lambda v: v, EncounterContext())
        assert result is None

    def test_entry_relationship_without_encounter(self) -> None:
        """EntryRelationship with no encounter should be skipped."""
        act = _make_note_act()
        act.entry_relationship = [EntryRelationship(type_code="COMP")]
        result = _create_context(act, lambda v: v, EncounterContext())
        assert result is None

    def test_convert_type_with_translation_but_no_primary(self, mapper: CodeSystemMapper) -> None:
        """Translation codes present but primary code is None."""
        code = CD(
            display_name="Note",
            translation=[
                CD(
                    code="34117-2",
                    code_system="2.16.840.1.113883.6.1",
                    display_name="H&P",
                )
            ],
        )
        # No primary code → falls back
        result = _convert_type(code, mapper)
        assert result.coding[0].code == "34133-9"

    def test_make_coding_empty_string_code(self, mapper: CodeSystemMapper) -> None:
        """Empty string code is falsy, so _make_coding returns None."""
        result = _make_coding("", None, None, mapper)
        assert result is None

    def test_inline_content_unicode(self) -> None:
        """Unicode text should be properly base64 encoded."""
        text = ED(value="Diagnose: Diabetes mellitus Typ 2 (E11.9)")
        result = _create_inline_content(text)
        assert result is not None
        decoded = result.attachment.data.decode("utf-8")
        assert "Diagnose" in decoded
        assert "Typ 2" in decoded

    def test_multiple_encounters_all_included(self) -> None:
        """All valid encounters should be included in context."""
        act = _make_note_act()
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root=f"enc-{i}")]),
            )
            for i in range(5)
        ]
        result = _create_context(act, lambda v: v, EncounterContext())
        assert result is not None
        assert len(result.encounter) == 5

    def test_relates_to_all_valid_type_codes(self) -> None:
        """All three valid type codes should be mapped."""
        refs = [
            Reference(
                type_code=tc,
                external_document=ExternalDocument(id=[II(root=f"doc-{tc}")]),
            )
            for tc in ("RPLC", "APND", "XFRM")
        ]
        result = _convert_relates_to(refs)
        assert len(result) == 3
        codes = {r.code for r in result}
        assert codes == {"replaces", "appends", "transforms"}

    def test_full_document_reference_structure(self, converter: NoteActivityConverter) -> None:
        """Full integration: all fields populated produce a valid structure."""
        act = _make_note_act(
            code=CD(
                code="34109-9",
                code_system="2.16.840.1.113883.6.1",
                display_name="Note",
            ),
            text=ED(value="Clinical findings..."),
            effective_time=IVL_TS(value="20260115"),
            authors=[_make_author()],
        )
        act.reference = [
            Reference(
                type_code="RPLC",
                external_document=ExternalDocument(id=[II(root="prev-doc")]),
            )
        ]
        act.entry_relationship = [
            EntryRelationship(
                type_code="COMP",
                encounter=CDAEncounter(id=[II(root="enc-1")]),
            )
        ]
        result = converter.convert(act)

        assert result["resourceType"] == "DocumentReference"
        assert isinstance(result["id"], str)
        assert result["status"] == FHIRCodes.DocumentReferenceStatus.CURRENT
        assert result["docStatus"] == "final"
        assert result["type"]["coding"][0]["code"] == "34109-9"
        assert len(result["category"]) == 1
        assert result["subject"]["reference"] == "urn:uuid:test-patient"
        assert result["date"] == "2026-01-20T16:00:00-05:00"
        assert len(result["author"]) == 1
        assert len(result["content"]) == 1
        assert result["context"]["period"]["start"] == "2026-01-15"
        assert len(result["context"]["encounter"]) == 1
        assert len(result["relatesTo"]) == 1
        assert result["relatesTo"][0]["code"] == "replaces"
