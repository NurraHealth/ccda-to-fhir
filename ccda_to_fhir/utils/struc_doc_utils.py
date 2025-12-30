"""StrucDocText utility functions.

Helper functions for working with C-CDA StrucDocText (narrative) elements.
These utilities support ID-based reference resolution and text extraction.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.struc_doc import (
        Caption,
        Footnote,
        List,
        StrucDocText,
        Table,
        TableBody,
        TableDataCell,
        TableHeaderCell,
        TableRow,
    )


def extract_text_by_id(narrative: StrucDocText | None, target_id: str) -> str | None:
    """Extract text content from element with matching ID.

    Recursively searches narrative structure for element with ID attribute
    matching target_id and returns its plain text content.

    This is used for resolving references from clinical statements to
    section narrative. For example, a Note Activity might have:
        <text><reference value="#note-content-1"/></text>

    This function would search the section narrative for an element with
    ID="note-content-1" and return its text content.

    Args:
        narrative: StrucDocText narrative object from Section.text
        target_id: ID to search for (without # prefix)

    Returns:
        Plain text content as string, or None if not found

    Example:
        >>> section_text = StrucDocText(
        ...     paragraph=[
        ...         Paragraph(text="First para", id_attr="p1"),
        ...         Paragraph(text="Second para", id_attr="p2")
        ...     ]
        ... )
        >>> extract_text_by_id(section_text, "p2")
        'Second para'
    """
    if not narrative:
        return None

    # Check root level ID
    if narrative.id_attr == target_id:
        return narrative_to_plain_text(narrative)

    # Search paragraphs
    if narrative.paragraph:
        for para in narrative.paragraph:
            if para.id_attr == target_id:
                return para.get_plain_text()
            # Also check content elements within paragraph
            if para.content:
                for content_elem in para.content:
                    if content_elem.id_attr == target_id:
                        return content_elem.get_plain_text()

    # Search tables
    if narrative.table:
        for table in narrative.table:
            result = _search_table_for_id(table, target_id)
            if result:
                return result

    # Search lists
    if narrative.list_elem:
        for list_elem in narrative.list_elem:
            result = _search_list_for_id(list_elem, target_id)
            if result:
                return result

    # Search root-level content elements
    if narrative.content:
        for content_elem in narrative.content:
            if content_elem.id_attr == target_id:
                return content_elem.get_plain_text()

    return None


def _search_table_for_id(table: Table, target_id: str) -> str | None:
    """Recursively search table for ID.

    Args:
        table: Table element to search
        target_id: ID to find

    Returns:
        Text content if found, None otherwise
    """
    # Check table itself
    if table.id_attr == target_id:
        return _extract_table_text(table)

    # Check thead rows
    if table.thead:
        result = _search_table_section_for_id(table.thead.tr, target_id)
        if result:
            return result

    # Check tbody rows
    if table.tbody:
        for tbody in table.tbody:
            if tbody.id_attr == target_id:
                return _extract_tbody_text(tbody)
            result = _search_table_section_for_id(tbody.tr, target_id)
            if result:
                return result

    # Check tfoot rows
    if table.tfoot:
        result = _search_table_section_for_id(table.tfoot.tr, target_id)
        if result:
            return result

    return None


def _search_table_section_for_id(
    rows: list[TableRow] | None, target_id: str
) -> str | None:
    """Search table rows for ID.

    Args:
        rows: List of TableRow elements
        target_id: ID to find

    Returns:
        Text content if found, None otherwise
    """
    if not rows:
        return None

    for row in rows:
        if row.id_attr == target_id:
            return _extract_row_text(row)

        # Check cells
        if row.td:
            for cell in row.td:
                if cell.id_attr == target_id:
                    return _extract_cell_text(cell)

        if row.th:
            for cell in row.th:
                if cell.id_attr == target_id:
                    return _extract_cell_text(cell)

    return None


def _search_list_for_id(list_elem: List, target_id: str) -> str | None:
    """Recursively search list for ID.

    Args:
        list_elem: List element to search
        target_id: ID to find

    Returns:
        Text content if found, None otherwise
    """
    # Check list itself
    if list_elem.id_attr == target_id:
        return _extract_list_text(list_elem)

    # Check items
    if list_elem.item:
        for item in list_elem.item:
            if item.id_attr == target_id:
                return _extract_list_item_text(item)
            # Check nested elements in item
            if item.paragraph:
                for para in item.paragraph:
                    if para.id_attr == target_id:
                        return para.get_plain_text()
            if item.list_elem:
                for nested_list in item.list_elem:
                    result = _search_list_for_id(nested_list, target_id)
                    if result:
                        return result

    return None


def _extract_table_text(table: Table) -> str:
    """Extract all text from a table.

    Args:
        table: Table element

    Returns:
        Plain text representation
    """
    parts = []

    if table.caption:
        caption_text = _extract_caption_text(table.caption)
        if caption_text:
            parts.append(caption_text)

    if table.thead and table.thead.tr:
        for row in table.thead.tr:
            parts.append(_extract_row_text(row))

    if table.tbody:
        for tbody in table.tbody:
            parts.append(_extract_tbody_text(tbody))

    if table.tfoot and table.tfoot.tr:
        for row in table.tfoot.tr:
            parts.append(_extract_row_text(row))

    return "\n".join(p for p in parts if p).strip()


def _extract_tbody_text(tbody: TableBody) -> str:
    """Extract text from table body.

    Args:
        tbody: TableBody element

    Returns:
        Plain text
    """
    if not tbody.tr:
        return ""
    return "\n".join(_extract_row_text(row) for row in tbody.tr if row)


def _extract_row_text(row: TableRow) -> str:
    """Extract text from table row.

    Args:
        row: TableRow element

    Returns:
        Plain text with cells separated by spaces
    """
    parts = []
    if row.th:
        for cell in row.th:
            text = _extract_cell_text(cell)
            if text:
                parts.append(text)
    if row.td:
        for cell in row.td:
            text = _extract_cell_text(cell)
            if text:
                parts.append(text)
    return " ".join(parts)


def _extract_cell_text(cell: TableDataCell | TableHeaderCell) -> str:
    """Extract text from table cell.

    Args:
        cell: TableDataCell or TableHeaderCell element

    Returns:
        Plain text
    """
    parts = []
    if cell.text:
        parts.append(cell.text)
    if cell.content:
        for content in cell.content:
            if content.text:
                parts.append(content.text)
    # TableDataCell can have paragraphs, TableHeaderCell cannot
    if hasattr(cell, "paragraph") and cell.paragraph:
        for para in cell.paragraph:
            parts.append(para.get_plain_text())
    # Both can have footnotes
    if hasattr(cell, "footnote") and cell.footnote:
        for footnote in cell.footnote:
            footnote_text = _extract_footnote_text(footnote)
            if footnote_text:
                parts.append(f"[{footnote_text}]")
    return " ".join(parts).strip()


def _extract_footnote_text(footnote: Footnote) -> str:
    """Extract text from footnote element.

    Footnotes can contain complex content including paragraphs, lists, and tables.

    Args:
        footnote: Footnote element

    Returns:
        Plain text
    """
    parts = []
    if footnote.text:
        parts.append(footnote.text)
    if footnote.content:
        for content in footnote.content:
            if content.text:
                parts.append(content.text)
    if footnote.paragraph:
        for para in footnote.paragraph:
            parts.append(para.get_plain_text())
    if footnote.list_elem:
        for list_elem in footnote.list_elem:
            parts.append(_extract_list_text(list_elem))
    if footnote.table:
        for table in footnote.table:
            parts.append(_extract_table_text(table))
    return " ".join(parts).strip()


def _extract_caption_text(caption: Caption) -> str:
    """Extract text from caption element.

    Args:
        caption: Caption element

    Returns:
        Plain text
    """
    parts = []
    if caption.text:
        parts.append(caption.text)
    if caption.footnote:
        for footnote in caption.footnote:
            footnote_text = _extract_footnote_text(footnote)
            if footnote_text:
                parts.append(f"[{footnote_text}]")
    return " ".join(parts).strip()


def _extract_list_text(list_elem: List) -> str:
    """Extract all text from a list.

    Args:
        list_elem: List element

    Returns:
        Plain text representation
    """
    parts = []

    if list_elem.caption:
        caption_text = _extract_caption_text(list_elem.caption)
        if caption_text:
            parts.append(caption_text)

    if list_elem.item:
        for item in list_elem.item:
            parts.append(_extract_list_item_text(item))

    return "\n".join(p for p in parts if p).strip()


def _extract_list_item_text(item) -> str:
    """Extract text from list item.

    Args:
        item: ListItem element

    Returns:
        Plain text
    """
    parts = []
    if item.caption:
        caption_text = _extract_caption_text(item.caption)
        if caption_text:
            parts.append(caption_text)
    if item.text:
        parts.append(item.text)
    if item.content:
        for content in item.content:
            if content.text:
                parts.append(content.text)
    if item.footnote:
        for footnote in item.footnote:
            footnote_text = _extract_footnote_text(footnote)
            if footnote_text:
                parts.append(f"[{footnote_text}]")
    if item.paragraph:
        for para in item.paragraph:
            parts.append(para.get_plain_text())
    return " ".join(parts).strip()


def narrative_to_plain_text(narrative: StrucDocText | None) -> str:
    """Convert StrucDocText to plain text (no formatting).

    Strips all markup and concatenates text content from all elements.

    Args:
        narrative: StrucDocText narrative object

    Returns:
        Plain text string

    Example:
        >>> narrative = StrucDocText(
        ...     paragraph=[
        ...         Paragraph(text="Para 1"),
        ...         Paragraph(text="Para 2")
        ...     ]
        ... )
        >>> narrative_to_plain_text(narrative)
        'Para 1 Para 2'
    """
    if not narrative:
        return ""

    parts = []

    if narrative.text:
        parts.append(narrative.text)

    if narrative.paragraph:
        for para in narrative.paragraph:
            text = para.get_plain_text()
            if text:
                parts.append(text)

    if narrative.list_elem:
        for list_elem in narrative.list_elem:
            text = _extract_list_text(list_elem)
            if text:
                parts.append(text)

    if narrative.table:
        for table in narrative.table:
            text = _extract_table_text(table)
            if text:
                parts.append(text)

    if narrative.content:
        for content in narrative.content:
            text = content.get_plain_text()
            if text:
                parts.append(text)

    return " ".join(parts).strip()


def has_complex_markup(narrative: StrucDocText | None) -> bool:
    """Check if narrative contains complex markup (tables or lists).

    Args:
        narrative: StrucDocText narrative object

    Returns:
        True if narrative has tables or lists, False otherwise
    """
    if not narrative:
        return False
    return bool(narrative.table or narrative.list_elem)


def narrative_to_html(narrative: StrucDocText | None) -> str:
    """Convert StrucDocText to XHTML fragment for FHIR Narrative.div.

    Converts CDA narrative markup to FHIR-compliant XHTML fragment suitable
    for use in FHIR Narrative.div elements. Follows FHIR Narrative requirements:
    - Uses only basic HTML formatting elements
    - No scripts, forms, external stylesheets, or event handlers
    - Applies styleCode attributes as CSS classes

    Reference: https://hl7.org/fhir/narrative.html

    Args:
        narrative: StrucDocText narrative object

    Returns:
        XHTML fragment string (without wrapping <div>)

    Example:
        >>> narrative = StrucDocText(
        ...     paragraph=[
        ...         Paragraph(text="Patient has ", content=[
        ...             Content(text="hypertension", style_code="Bold")
        ...         ])
        ...     ]
        ... )
        >>> narrative_to_html(narrative)
        '<p>Patient has <span class="Bold">hypertension</span></p>'
    """
    if not narrative:
        return ""

    parts = []

    # Convert paragraphs
    if narrative.paragraph:
        for para in narrative.paragraph:
            parts.append(_paragraph_to_html(para))

    # Convert tables
    if narrative.table:
        for table in narrative.table:
            parts.append(_table_to_html(table))

    # Convert lists
    if narrative.list_elem:
        for list_elem in narrative.list_elem:
            parts.append(_list_to_html(list_elem))

    # Convert root-level content elements (rare, but allowed)
    if narrative.content:
        for content in narrative.content:
            parts.append(_content_to_html(content))

    # Root-level text (if any)
    if narrative.text:
        parts.append(_escape_html(narrative.text))

    return "".join(parts)


# ============================================================================
# HTML Conversion Helpers
# ============================================================================


def _escape_html(text: str) -> str:
    """Escape HTML special characters.

    Args:
        text: Text to escape

    Returns:
        HTML-escaped text
    """
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _apply_style_class(style_code: str | None) -> str:
    """Convert styleCode to HTML class attribute.

    Args:
        style_code: CDA styleCode value (e.g., "Bold", "Italics", "Bold Italics")

    Returns:
        HTML class attribute string (e.g., ' class="Bold Italics"') or empty string
    """
    if not style_code:
        return ""
    return f' class="{_escape_html(style_code)}"'


def _paragraph_to_html(para) -> str:
    """Convert Paragraph to HTML <p> element.

    Args:
        para: Paragraph element

    Returns:
        HTML string
    """
    parts = []

    # Add caption if present
    if para.caption:
        parts.append(_caption_to_html(para.caption))

    # Add text content
    if para.text:
        parts.append(_escape_html(para.text))

    # Add inline elements
    if para.content:
        for content in para.content:
            parts.append(_content_to_html(content))

    if para.link_html:
        for link in para.link_html:
            parts.append(_link_to_html(link))

    if para.sub:
        for sub in para.sub:
            parts.append(f"<sub>{_escape_html(sub.text) if sub.text else ''}</sub>")

    if para.sup:
        for sup in para.sup:
            parts.append(f"<sup>{_escape_html(sup.text) if sup.text else ''}</sup>")

    if para.br:
        parts.extend(["<br/>" for _ in para.br])

    if para.footnote:
        for footnote in para.footnote:
            parts.append(_footnote_to_html(footnote))

    if para.render_multi_media:
        for rmm in para.render_multi_media:
            parts.append(_render_multimedia_to_html(rmm))

    content_html = "".join(parts)
    style_attr = _apply_style_class(para.style_code)
    id_attr = f' id="{_escape_html(para.id_attr)}"' if para.id_attr else ""

    return f"<p{id_attr}{style_attr}>{content_html}</p>"


def _content_to_html(content) -> str:
    """Convert Content to HTML <span> element.

    Args:
        content: Content element

    Returns:
        HTML string
    """
    parts = []

    if content.text:
        parts.append(_escape_html(content.text))

    # Recursively handle nested content
    if content.content:
        for nested in content.content:
            parts.append(_content_to_html(nested))

    if content.link_html:
        for link in content.link_html:
            parts.append(_link_to_html(link))

    if content.sub:
        for sub in content.sub:
            parts.append(f"<sub>{_escape_html(sub.text) if sub.text else ''}</sub>")

    if content.sup:
        for sup in content.sup:
            parts.append(f"<sup>{_escape_html(sup.text) if sup.text else ''}</sup>")

    if content.br:
        parts.extend(["<br/>" for _ in content.br])

    if content.footnote:
        for footnote in content.footnote:
            parts.append(_footnote_to_html(footnote))

    if content.render_multi_media:
        for rmm in content.render_multi_media:
            parts.append(_render_multimedia_to_html(rmm))

    content_html = "".join(parts)
    style_attr = _apply_style_class(content.style_code)
    id_attr = f' id="{_escape_html(content.id_attr)}"' if content.id_attr else ""

    # Build the element
    result = f"<span{id_attr}{style_attr}>{content_html}</span>"

    # Append tail text if present (preserves mixed content order)
    if hasattr(content, 'tail_text') and content.tail_text:
        result += _escape_html(content.tail_text)

    return result


def _link_to_html(link) -> str:
    """Convert LinkHtml to HTML <a> element.

    Args:
        link: LinkHtml element

    Returns:
        HTML string
    """
    text = _escape_html(link.text) if link.text else ""
    href_attr = f' href="{_escape_html(link.href)}"' if link.href else ""
    id_attr = f' id="{_escape_html(link.id_attr)}"' if link.id_attr else ""
    style_attr = _apply_style_class(link.style_code)

    return f"<a{id_attr}{href_attr}{style_attr}>{text}</a>"


def _caption_to_html(caption) -> str:
    """Convert Caption to HTML (typically as emphasized text).

    Args:
        caption: Caption element

    Returns:
        HTML string
    """
    parts = []

    if caption.text:
        parts.append(_escape_html(caption.text))

    if caption.footnote:
        for footnote in caption.footnote:
            parts.append(_footnote_to_html(footnote))

    content_html = "".join(parts)
    style_attr = _apply_style_class(caption.style_code)

    # Render caption as strong/bold text
    return f"<strong{style_attr}>{content_html}</strong>"


def _footnote_to_html(footnote) -> str:
    """Convert Footnote to HTML (as superscript reference or inline note).

    Args:
        footnote: Footnote element

    Returns:
        HTML string
    """
    parts = []

    if footnote.text:
        parts.append(_escape_html(footnote.text))

    if footnote.content:
        for content in footnote.content:
            parts.append(_content_to_html(content))

    if footnote.paragraph:
        for para in footnote.paragraph:
            parts.append(_paragraph_to_html(para))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(footnote.id_attr)}"' if footnote.id_attr else ""

    # Render as small text in brackets
    return f'<small{id_attr}>[{content_html}]</small>'


def _render_multimedia_to_html(rmm) -> str:
    """Convert RenderMultiMedia to HTML comment or placeholder.

    RenderMultiMedia references ObservationMedia/RegionOfInterest entries.
    Since we can't embed the actual media in plain XHTML, we create a placeholder.

    Args:
        rmm: RenderMultiMedia element

    Returns:
        HTML string
    """
    ref_obj = rmm.referenced_object or "unknown"
    return f'<em>[Media: {_escape_html(ref_obj)}]</em>'


def _table_to_html(table) -> str:
    """Convert Table to HTML <table> element.

    Args:
        table: Table element

    Returns:
        HTML string
    """
    parts = []

    if table.caption:
        caption_html = _caption_to_html(table.caption)
        parts.append(f"<caption>{caption_html}</caption>")

    if table.thead:
        parts.append("<thead>")
        if table.thead.tr:
            for row in table.thead.tr:
                parts.append(_table_row_to_html(row))
        parts.append("</thead>")

    if table.tbody:
        for tbody in table.tbody:
            parts.append("<tbody>")
            if tbody.tr:
                for row in tbody.tr:
                    parts.append(_table_row_to_html(row))
            parts.append("</tbody>")

    if table.tfoot:
        parts.append("<tfoot>")
        if table.tfoot.tr:
            for row in table.tfoot.tr:
                parts.append(_table_row_to_html(row))
        parts.append("</tfoot>")

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(table.id_attr)}"' if table.id_attr else ""
    style_attr = _apply_style_class(table.style_code)

    return f"<table{id_attr}{style_attr}>{content_html}</table>"


def _table_row_to_html(row) -> str:
    """Convert TableRow to HTML <tr> element.

    Args:
        row: TableRow element

    Returns:
        HTML string
    """
    parts = []

    if row.th:
        for cell in row.th:
            parts.append(_table_header_cell_to_html(cell))

    if row.td:
        for cell in row.td:
            parts.append(_table_data_cell_to_html(cell))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(row.id_attr)}"' if row.id_attr else ""
    style_attr = _apply_style_class(row.style_code)

    return f"<tr{id_attr}{style_attr}>{content_html}</tr>"


def _table_header_cell_to_html(cell) -> str:
    """Convert TableHeaderCell to HTML <th> element.

    Args:
        cell: TableHeaderCell element

    Returns:
        HTML string
    """
    parts = []

    if cell.text:
        parts.append(_escape_html(cell.text))

    if cell.content:
        for content in cell.content:
            parts.append(_content_to_html(content))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(cell.id_attr)}"' if cell.id_attr else ""
    style_attr = _apply_style_class(cell.style_code)

    return f"<th{id_attr}{style_attr}>{content_html}</th>"


def _table_data_cell_to_html(cell) -> str:
    """Convert TableDataCell to HTML <td> element.

    Args:
        cell: TableDataCell element

    Returns:
        HTML string
    """
    parts = []

    if cell.text:
        parts.append(_escape_html(cell.text))

    if cell.content:
        for content in cell.content:
            parts.append(_content_to_html(content))

    if cell.paragraph:
        for para in cell.paragraph:
            parts.append(_paragraph_to_html(para))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(cell.id_attr)}"' if cell.id_attr else ""
    style_attr = _apply_style_class(cell.style_code)

    return f"<td{id_attr}{style_attr}>{content_html}</td>"


def _list_to_html(list_elem) -> str:
    """Convert List to HTML <ul> or <ol> element.

    Args:
        list_elem: List element

    Returns:
        HTML string
    """
    parts = []

    if list_elem.caption:
        parts.append(_caption_to_html(list_elem.caption))

    if list_elem.item:
        for item in list_elem.item:
            parts.append(_list_item_to_html(item))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(list_elem.id_attr)}"' if list_elem.id_attr else ""
    style_attr = _apply_style_class(list_elem.style_code)

    # Use <ol> for ordered, <ul> for unordered
    tag = "ol" if list_elem.list_type == "ordered" else "ul"

    return f"<{tag}{id_attr}{style_attr}>{content_html}</{tag}>"


def _list_item_to_html(item) -> str:
    """Convert ListItem to HTML <li> element.

    Args:
        item: ListItem element

    Returns:
        HTML string
    """
    parts = []

    if item.caption:
        parts.append(_caption_to_html(item.caption))

    if item.text:
        parts.append(_escape_html(item.text))

    if item.content:
        for content in item.content:
            parts.append(_content_to_html(content))

    if item.paragraph:
        for para in item.paragraph:
            parts.append(_paragraph_to_html(para))

    if item.list_elem:
        for nested_list in item.list_elem:
            parts.append(_list_to_html(nested_list))

    content_html = "".join(parts)
    id_attr = f' id="{_escape_html(item.id_attr)}"' if item.id_attr else ""
    style_attr = _apply_style_class(item.style_code)

    return f"<li{id_attr}{style_attr}>{content_html}</li>"


# ============================================================================
# Reference-based Narrative Extraction (C-CDA on FHIR IG)
# ============================================================================


def find_element_by_id(narrative: StrucDocText, element_id: str):
    """Find an element by ID attribute in StrucDocText narrative.

    Per C-CDA on FHIR IG: When an entry has <text><reference value="#id"/></text>,
    we need to find the element with ID="id" in the section narrative.

    Args:
        narrative: StrucDocText object to search
        element_id: ID attribute value to find (without '#' prefix)

    Returns:
        The element (Paragraph, Content, Table, etc.) with matching ID, or None

    Reference:
        https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html
    """
    if not narrative or not element_id:
        return None

    # Search paragraphs
    if narrative.paragraph:
        for para in narrative.paragraph:
            if para.id_attr == element_id:
                return para
            # Search within paragraph's inline elements
            found = _find_in_inline_elements(para, element_id)
            if found:
                return found

    # Search tables
    if narrative.table:
        for table in narrative.table:
            if table.id_attr == element_id:
                return table
            # Search within table
            found = _find_in_table(table, element_id)
            if found:
                return found

    # Search lists
    if narrative.list_elem:
        for list_elem in narrative.list_elem:
            if list_elem.id_attr == element_id:
                return list_elem
            # Search within list
            found = _find_in_list(list_elem, element_id)
            if found:
                return found

    # Search root-level content
    if narrative.content:
        for content in narrative.content:
            if content.id_attr == element_id:
                return content
            found = _find_in_content(content, element_id)
            if found:
                return found

    return None


def _find_in_inline_elements(parent, element_id: str):
    """Search for ID in inline elements of a parent."""
    # Search content elements
    if hasattr(parent, 'content') and parent.content:
        for content in parent.content:
            if content.id_attr == element_id:
                return content
            found = _find_in_content(content, element_id)
            if found:
                return found

    # Search linkHtml elements
    if hasattr(parent, 'link_html') and parent.link_html:
        for link in parent.link_html:
            if link.id_attr == element_id:
                return link

    return None


def _find_in_content(content, element_id: str):
    """Recursively search Content elements."""
    if content.content:
        for nested in content.content:
            if nested.id_attr == element_id:
                return nested
            found = _find_in_content(nested, element_id)
            if found:
                return found
    return None


def _find_in_table(table, element_id: str):
    """Search for ID within table structure."""
    # Search table rows
    for section in [table.thead, table.tfoot] + (table.tbody or []):
        if not section or not section.tr:
            continue
        for row in section.tr:
            if row.id_attr == element_id:
                return row
            # Search cells
            for cell in (row.th or []) + (row.td or []):
                if cell.id_attr == element_id:
                    return cell
    return None


def _find_in_list(list_elem, element_id: str):
    """Search for ID within list structure."""
    if list_elem.item:
        for item in list_elem.item:
            if item.id_attr == element_id:
                return item
    return None


def element_to_html(element) -> str:
    """Convert a single StrucDocText element to HTML.

    Used for reference-based narrative extraction where only a specific
    element (identified by ID) should be included in the FHIR narrative.

    Args:
        element: StrucDocText element (Paragraph, Content, Table, etc.)

    Returns:
        HTML string for that element

    Reference:
        https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html
    """
    if not element:
        return ""

    # Import to avoid circular dependency
    from ccda_to_fhir.ccda.models.struc_doc import (
        Caption,
        Content,
        Footnote,
        LinkHtml,
        List,
        ListItem,
        Paragraph,
        RenderMultiMedia,
        Table,
        TableDataCell,
        TableHeaderCell,
        TableRow,
    )

    # Dispatch to appropriate converter
    if isinstance(element, Paragraph):
        return _paragraph_to_html(element)
    elif isinstance(element, Content):
        return _content_to_html(element)
    elif isinstance(element, Table):
        return _table_to_html(element)
    elif isinstance(element, List):
        return _list_to_html(element)
    elif isinstance(element, ListItem):
        return _list_item_to_html(element)
    elif isinstance(element, TableRow):
        return _table_row_to_html(element)
    elif isinstance(element, (TableHeaderCell, TableDataCell)):
        # For cells, we need context - include cell tags
        if isinstance(element, TableHeaderCell):
            return _table_header_cell_to_html(element)
        else:
            return _table_data_cell_to_html(element)
    elif isinstance(element, LinkHtml):
        return _link_to_html(element)
    elif isinstance(element, Footnote):
        return _footnote_to_html(element)
    elif isinstance(element, Caption):
        return _caption_to_html(element)
    elif isinstance(element, RenderMultiMedia):
        return _render_multimedia_to_html(element)
    else:
        # Unknown element type
        return ""
