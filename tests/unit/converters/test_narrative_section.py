"""Tests for narrative section → DocumentReference extraction."""

from __future__ import annotations

import base64

from ccda_to_fhir.ccda.models.section import SectionComponent, Section, StructuredBody
from ccda_to_fhir.ccda.models.struc_doc import Content, Paragraph, StrucDocText
from ccda_to_fhir.ccda.models.datatypes import CE
from ccda_to_fhir.converters.narrative_section import (
    NARRATIVE_SECTIONS,
    _is_empty_narrative,
    extract_narrative_sections,
)
from ccda_to_fhir.converters.references import ReferenceRegistry


def _make_registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


def _make_body(sections: list[Section]) -> StructuredBody:
    return StructuredBody(
        component=[SectionComponent(section=s) for s in sections]
    )


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
        body = _make_body([
            _make_section("10164-2", "HPI content."),
            _make_section("29545-1", "PE content."),
            _make_section("51848-0", "No assessment recorded."),  # should be skipped
        ])
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
                                content=[
                                    Content(text="well-appearing, no acute distress")
                                ],
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
