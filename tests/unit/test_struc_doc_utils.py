"""Tests for struc_doc_utils — narrative text extraction and HTML conversion.

Covers the runtime bug where TableDataCell was only imported under TYPE_CHECKING,
causing _extract_cell_text to fail with NameError at runtime.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.struc_doc import (
    Content,
    Paragraph,
    StrucDocText,
    Table,
    TableBody,
    TableDataCell,
    TableHeaderCell,
    TableRow,
)
from ccda_to_fhir.utils.struc_doc_utils import (
    _extract_cell_text,
    _extract_row_text,
    _extract_table_text,
    _extract_tbody_text,
    _search_table_for_id,
    _search_table_section_for_id,
    extract_text_by_id,
    narrative_to_html,
    narrative_to_plain_text,
)


# ---------------------------------------------------------------------------
# _extract_cell_text — the function that was broken by the missing import
# ---------------------------------------------------------------------------


class TestExtractCellText:
    """Tests for _extract_cell_text with both TableDataCell and TableHeaderCell."""

    def test_table_data_cell_with_text(self) -> None:
        cell = TableDataCell(text="simple text")
        assert _extract_cell_text(cell) == "simple text"

    def test_table_header_cell_with_text(self) -> None:
        cell = TableHeaderCell(text="header text")
        assert _extract_cell_text(cell) == "header text"

    def test_table_data_cell_with_content(self) -> None:
        cell = TableDataCell(
            content=[Content(text="first"), Content(text="second")]
        )
        assert _extract_cell_text(cell) == "first second"

    def test_table_data_cell_with_paragraphs(self) -> None:
        """This is the case that triggered the NameError — paragraphs only exist on TableDataCell."""
        cell = TableDataCell(
            paragraph=[Paragraph(text="para 1"), Paragraph(text="para 2")]
        )
        result = _extract_cell_text(cell)
        assert "para 1" in result
        assert "para 2" in result

    def test_table_data_cell_with_text_content_and_paragraphs(self) -> None:
        cell = TableDataCell(
            text="prefix",
            content=[Content(text="inline")],
            paragraph=[Paragraph(text="block")],
        )
        result = _extract_cell_text(cell)
        assert "prefix" in result
        assert "inline" in result
        assert "block" in result

    def test_table_header_cell_ignores_paragraph_attr(self) -> None:
        """TableHeaderCell does not have paragraphs — isinstance check prevents access."""
        cell = TableHeaderCell(text="header only")
        assert _extract_cell_text(cell) == "header only"

    def test_empty_cell(self) -> None:
        cell = TableDataCell()
        assert _extract_cell_text(cell) == ""


# ---------------------------------------------------------------------------
# extract_text_by_id — ID-based reference resolution
# ---------------------------------------------------------------------------


class TestExtractTextById:
    def test_finds_paragraph_by_id(self) -> None:
        narrative = StrucDocText(
            paragraph=[
                Paragraph(text="wrong", id_attr="p1"),
                Paragraph(text="correct", id_attr="p2"),
            ]
        )
        assert extract_text_by_id(narrative, "p2") == "correct"

    def test_finds_content_in_paragraph_by_id(self) -> None:
        narrative = StrucDocText(
            paragraph=[
                Paragraph(
                    content=[Content(text="nested", id_attr="c1")]
                )
            ]
        )
        assert extract_text_by_id(narrative, "c1") == "nested"

    def test_finds_table_cell_by_id(self) -> None:
        """Simulates the Athena Notes section pattern: ID on a <td> element."""
        narrative = StrucDocText(
            table=[
                Table(
                    tbody=[
                        TableBody(
                            tr=[
                                TableRow(
                                    td=[
                                        TableDataCell(
                                            text="note text",
                                            id_attr="clinicalnotes1",
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        result = extract_text_by_id(narrative, "clinicalnotes1")
        assert result is not None
        assert "note text" in result

    def test_finds_table_cell_with_content_by_id(self) -> None:
        """The real Athena pattern: <td> with nested <content> elements."""
        narrative = StrucDocText(
            table=[
                Table(
                    tbody=[
                        TableBody(
                            tr=[
                                TableRow(
                                    td=[
                                        TableDataCell(
                                            id_attr="clinicalnotes1",
                                            content=[
                                                Content(text="Patient is 82 years old."),
                                                Content(text="Follow-up visit."),
                                            ],
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        result = extract_text_by_id(narrative, "clinicalnotes1")
        assert result is not None
        assert "Patient is 82 years old." in result
        assert "Follow-up visit." in result

    def test_finds_root_content_by_id(self) -> None:
        narrative = StrucDocText(
            content=[Content(text="root content", id_attr="rc1")]
        )
        assert extract_text_by_id(narrative, "rc1") == "root content"

    def test_returns_none_for_missing_id(self) -> None:
        narrative = StrucDocText(paragraph=[Paragraph(text="text", id_attr="p1")])
        assert extract_text_by_id(narrative, "nonexistent") is None

    def test_returns_none_for_none_narrative(self) -> None:
        assert extract_text_by_id(None, "id") is None


# ---------------------------------------------------------------------------
# Table text extraction helpers
# ---------------------------------------------------------------------------


class TestTableTextExtraction:
    def test_extract_row_text(self) -> None:
        row = TableRow(
            td=[TableDataCell(text="cell1"), TableDataCell(text="cell2")]
        )
        assert _extract_row_text(row) == "cell1 cell2"

    def test_extract_row_with_headers_and_data(self) -> None:
        row = TableRow(
            th=[TableHeaderCell(text="header")],
            td=[TableDataCell(text="data")],
        )
        result = _extract_row_text(row)
        assert "header" in result
        assert "data" in result

    def test_extract_tbody_text(self) -> None:
        tbody = TableBody(
            tr=[
                TableRow(td=[TableDataCell(text="row1")]),
                TableRow(td=[TableDataCell(text="row2")]),
            ]
        )
        result = _extract_tbody_text(tbody)
        assert "row1" in result
        assert "row2" in result

    def test_extract_table_text(self) -> None:
        table = Table(
            tbody=[
                TableBody(
                    tr=[TableRow(td=[TableDataCell(text="data")])]
                )
            ]
        )
        assert "data" in _extract_table_text(table)

    def test_search_table_for_id_on_table(self) -> None:
        table = Table(
            id_attr="t1",
            tbody=[TableBody(tr=[TableRow(td=[TableDataCell(text="inside")])])],
        )
        result = _search_table_for_id(table, "t1")
        assert result is not None
        assert "inside" in result

    def test_search_table_for_id_on_tbody(self) -> None:
        table = Table(
            tbody=[
                TableBody(
                    id_attr="tb1",
                    tr=[TableRow(td=[TableDataCell(text="body text")])],
                )
            ]
        )
        result = _search_table_for_id(table, "tb1")
        assert result is not None
        assert "body text" in result

    def test_search_table_section_for_id_on_row(self) -> None:
        rows = [TableRow(id_attr="r1", td=[TableDataCell(text="row data")])]
        result = _search_table_section_for_id(rows, "r1")
        assert result is not None
        assert "row data" in result

    def test_search_table_section_returns_none(self) -> None:
        rows = [TableRow(td=[TableDataCell(text="x")])]
        assert _search_table_section_for_id(rows, "nope") is None

    def test_search_table_section_none_rows(self) -> None:
        assert _search_table_section_for_id(None, "id") is None


# ---------------------------------------------------------------------------
# narrative_to_plain_text
# ---------------------------------------------------------------------------


class TestNarrativeToPlainText:
    def test_paragraphs(self) -> None:
        narrative = StrucDocText(
            paragraph=[Paragraph(text="Hello"), Paragraph(text="World")]
        )
        result = narrative_to_plain_text(narrative)
        assert "Hello" in result
        assert "World" in result

    def test_table(self) -> None:
        narrative = StrucDocText(
            table=[
                Table(
                    tbody=[
                        TableBody(
                            tr=[TableRow(td=[TableDataCell(text="cell")])]
                        )
                    ]
                )
            ]
        )
        assert "cell" in narrative_to_plain_text(narrative)

    def test_none_narrative(self) -> None:
        assert narrative_to_plain_text(None) == ""

    def test_root_text(self) -> None:
        narrative = StrucDocText(text="root")
        assert narrative_to_plain_text(narrative) == "root"

    def test_content_elements(self) -> None:
        narrative = StrucDocText(
            content=[Content(text="inline1"), Content(text="inline2")]
        )
        result = narrative_to_plain_text(narrative)
        assert "inline1" in result
        assert "inline2" in result


# ---------------------------------------------------------------------------
# narrative_to_html
# ---------------------------------------------------------------------------


class TestNarrativeToHtml:
    def test_paragraph_to_html(self) -> None:
        narrative = StrucDocText(paragraph=[Paragraph(text="test")])
        html = narrative_to_html(narrative)
        assert "<p>" in html
        assert "test" in html

    def test_table_to_html(self) -> None:
        narrative = StrucDocText(
            table=[
                Table(
                    tbody=[
                        TableBody(
                            tr=[
                                TableRow(
                                    td=[TableDataCell(text="val", id_attr="td1")]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        html = narrative_to_html(narrative)
        assert "<table>" in html
        assert '<td id="td1">' in html
        assert "val" in html

    def test_none_narrative(self) -> None:
        assert narrative_to_html(None) == ""

    def test_data_cell_with_paragraph_to_html(self) -> None:
        """Ensure TableDataCell paragraphs render in HTML output."""
        narrative = StrucDocText(
            table=[
                Table(
                    tbody=[
                        TableBody(
                            tr=[
                                TableRow(
                                    td=[
                                        TableDataCell(
                                            paragraph=[Paragraph(text="note paragraph")]
                                        )
                                    ]
                                )
                            ]
                        )
                    ]
                )
            ]
        )
        html = narrative_to_html(narrative)
        assert "note paragraph" in html
        assert "<p>" in html
