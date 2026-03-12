"""Tests for narrative section → DocumentReference extraction."""

from __future__ import annotations

import base64

from ccda_to_fhir.ccda.models.datatypes import CE
from ccda_to_fhir.ccda.models.section import Section, SectionComponent, StructuredBody
from ccda_to_fhir.ccda.models.struc_doc import Content, Paragraph, StrucDocText
from ccda_to_fhir.converters.narrative_section import (
    _is_empty_narrative,
    extract_narrative_sections,
)
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.types import EncounterContext, FHIRReference


def _make_registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


def _make_body(sections: list[Section]) -> StructuredBody:
    return StructuredBody(component=[SectionComponent(section=s) for s in sections])


def _make_section(loinc_code: str, text: str) -> Section:
    return Section(
        code=CE(code=loinc_code, code_system="2.16.840.1.113883.6.1"),
        text=StrucDocText(paragraph=[Paragraph(text=text)]),
    )


class TestIsEmptyNarrative:
    def test_blank(self) -> None:
        assert _is_empty_narrative("") is True
        assert _is_empty_narrative("   ") is True

    def test_placeholder(self) -> None:
        assert _is_empty_narrative("No assessment recorded.") is True
        assert _is_empty_narrative("NO DATA RECORDED") is True
        assert _is_empty_narrative("N/A") is True
        assert _is_empty_narrative("none") is True

    def test_real_content(self) -> None:
        assert _is_empty_narrative("Patient is 82 years old.") is False


class TestExtractNarrativeSections:
    def test_extracts_hpi(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient presents with chest pain.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1
        assert results[0]["resourceType"] == "DocumentReference"
        assert results[0]["type"]["coding"][0]["code"] == "10164-2"
        assert results[0]["type"]["text"] == "History of Present Illness"

    def test_extracts_physical_exam(self) -> None:
        body = _make_body([_make_section("29545-1", "Constitutional: well-appearing.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1
        assert results[0]["type"]["coding"][0]["code"] == "29545-1"

    def test_extracts_ros(self) -> None:
        body = _make_body([_make_section("10187-3", "Constitutional: no fever.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1
        assert results[0]["type"]["coding"][0]["code"] == "10187-3"

    def test_extracts_reason_for_visit(self) -> None:
        body = _make_body([_make_section("29299-5", "Follow-up hypertension.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1
        assert results[0]["type"]["coding"][0]["code"] == "29299-5"

    def test_skips_empty_assessment(self) -> None:
        body = _make_body([_make_section("51848-0", "No assessment recorded.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 0

    def test_extracts_real_assessment(self) -> None:
        body = _make_body([_make_section("51848-0", "Uncontrolled hypertension.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1

    def test_skips_unknown_section(self) -> None:
        body = _make_body([_make_section("99999-9", "Unknown section.")])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 0

    def test_skips_section_without_text(self) -> None:
        section = Section(
            code=CE(code="10164-2", code_system="2.16.840.1.113883.6.1"),
            text=None,
        )
        body = _make_body([section])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 0

    def test_multiple_sections(self) -> None:
        body = _make_body(
            [
                _make_section("10164-2", "HPI content."),
                _make_section("29545-1", "PE content."),
                _make_section("51848-0", "No assessment recorded."),  # should be skipped
            ]
        )
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 2
        codes = {r["type"]["coding"][0]["code"] for r in results}
        assert codes == {"10164-2", "29545-1"}

    def test_document_reference_structure(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        results = extract_narrative_sections(body, _make_registry())
        dr = results[0]

        assert dr["resourceType"] == "DocumentReference"
        assert dr["status"] == "current"
        assert "id" in dr

        # Type
        assert dr["type"]["coding"][0]["system"] == "http://loinc.org"
        assert dr["type"]["coding"][0]["code"] == "10164-2"

        # Category
        cat = dr["category"][0]["coding"][0]
        assert cat["code"] == "clinical-note"

        # Subject
        assert "reference" in dr["subject"]

        # Content - plain text
        assert len(dr["content"]) >= 1
        plain_att = dr["content"][0]["attachment"]
        assert plain_att["contentType"] == "text/plain"
        decoded = base64.b64decode(plain_att["data"]).decode("utf-8")
        assert "chest pain" in decoded

    def test_includes_html_content(self) -> None:
        body = _make_body([_make_section("10164-2", "Some text.")])
        results = extract_narrative_sections(body, _make_registry())
        dr = results[0]

        # Should have both plain text and HTML
        assert len(dr["content"]) == 2
        assert dr["content"][0]["attachment"]["contentType"] == "text/plain"
        assert dr["content"][1]["attachment"]["contentType"] == "text/html"

    def test_nested_content_extracted(self) -> None:
        """Verify deeply nested content elements (like PE body systems) are extracted."""
        section = Section(
            code=CE(code="29545-1", code_system="2.16.840.1.113883.6.1"),
            text=StrucDocText(
                paragraph=[
                    Paragraph(
                        content=[
                            Content(
                                text="Constitutional:",
                                content=[Content(text="well-appearing, no acute distress")],
                            )
                        ]
                    )
                ]
            ),
        )
        body = _make_body([section])
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 1
        plain = base64.b64decode(results[0]["content"][0]["attachment"]["data"]).decode()
        assert "Constitutional:" in plain
        assert "well-appearing" in plain

    def test_empty_body(self) -> None:
        body = StructuredBody(component=None)
        results = extract_narrative_sections(body, _make_registry())
        assert len(results) == 0


class TestEncounterContext:
    """Tests for encounter reference and date from encompassingEncounter."""

    def test_encounter_reference_set(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(reference="urn:uuid:enc-123")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert len(results) == 1
        assert results[0]["context"]["encounter"][0]["reference"] == "urn:uuid:enc-123"

    def test_encounter_date_set(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(date="2026-01-20")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert len(results) == 1
        assert results[0]["date"] == "2026-01-20"

    def test_both_encounter_reference_and_date(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(reference="urn:uuid:enc-123", date="2026-01-20")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        dr = results[0]
        assert dr["date"] == "2026-01-20"
        assert dr["context"]["encounter"][0]["reference"] == "urn:uuid:enc-123"

    def test_all_narrative_sections_share_encounter(self) -> None:
        body = _make_body(
            [
                _make_section("10164-2", "HPI content."),
                _make_section("29545-1", "PE content."),
                _make_section("10187-3", "ROS content."),
            ]
        )
        ctx = EncounterContext(reference="urn:uuid:enc-shared", date="2026-01-20")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert len(results) == 3
        enc_refs = {r["context"]["encounter"][0]["reference"] for r in results}
        assert enc_refs == {"urn:uuid:enc-shared"}
        dates = {r["date"] for r in results}
        assert dates == {"2026-01-20"}

    def test_no_encounter_reference_omits_context(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        results = extract_narrative_sections(body, _make_registry())
        assert "context" not in results[0]

    def test_no_encounter_date_omits_date(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        results = extract_narrative_sections(body, _make_registry())
        assert "date" not in results[0]

    def test_none_encounter_reference_omits_context(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext()
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert "context" not in results[0]
        assert "date" not in results[0]


class TestAuthorReferences:
    """Tests for author references from document header."""

    def test_author_references_set(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        author_refs = [FHIRReference(reference="urn:uuid:prac-1")]
        results = extract_narrative_sections(
            body, _make_registry(), author_references=author_refs
        )
        assert len(results) == 1
        assert results[0]["author"] == [{"reference": "urn:uuid:prac-1"}]

    def test_multiple_author_references(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        author_refs = [
            FHIRReference(reference="urn:uuid:prac-1"),
            FHIRReference(reference="urn:uuid:prac-2"),
        ]
        results = extract_narrative_sections(body, _make_registry(), author_references=author_refs)
        assert len(results[0]["author"]) == 2

    def test_no_author_references_omits_field(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        results = extract_narrative_sections(body, _make_registry())
        assert "author" not in results[0]

    def test_empty_author_references_omits_field(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        results = extract_narrative_sections(body, _make_registry(), author_references=[])
        assert "author" not in results[0]

    def test_all_sections_share_authors(self) -> None:
        body = _make_body([
            _make_section("10164-2", "HPI content."),
            _make_section("29545-1", "PE content."),
        ])
        author_refs = [FHIRReference(reference="urn:uuid:prac-1")]
        results = extract_narrative_sections(
            body, _make_registry(), author_references=author_refs
        )
        author_refs = [{"reference": "urn:uuid:prac-1"}]
        results = extract_narrative_sections(body, _make_registry(), author_references=author_refs)
        assert len(results) == 2
        for dr in results:
            assert dr["author"] == [{"reference": "urn:uuid:prac-1"}]


class TestEncounterDisplay:
    """Tests for encounter display text on context.encounter references."""

    def test_encounter_display_set(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(reference="urn:uuid:enc-123", display="Pneumonia")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        enc_ref = results[0]["context"]["encounter"][0]
        assert enc_ref["reference"] == "urn:uuid:enc-123"
        assert enc_ref["display"] == "Pneumonia"

    def test_no_display_when_none(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(reference="urn:uuid:enc-123")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        enc_ref = results[0]["context"]["encounter"][0]
        assert enc_ref == {"reference": "urn:uuid:enc-123"}
        assert "display" not in enc_ref

    def test_display_omitted_without_encounter_reference(self) -> None:
        body = _make_body([_make_section("10164-2", "Patient has chest pain.")])
        ctx = EncounterContext(display="Pneumonia")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert "context" not in results[0]

    def test_all_sections_share_encounter_display(self) -> None:
        body = _make_body(
            [
                _make_section("10164-2", "HPI content."),
                _make_section("29545-1", "PE content."),
                _make_section("10187-3", "ROS content."),
            ]
        )
        ctx = EncounterContext(reference="urn:uuid:enc-shared", display="Office visit")
        results = extract_narrative_sections(body, _make_registry(), encounter_context=ctx)
        assert len(results) == 3
        for dr in results:
            enc_ref = dr["context"]["encounter"][0]
            assert enc_ref["display"] == "Office visit"
