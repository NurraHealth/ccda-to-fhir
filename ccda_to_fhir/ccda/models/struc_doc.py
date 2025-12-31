"""C-CDA StrucDocText (Structured Document Text) models.

StrucDocText is the CDA narrative content type used in Section.text elements.
It represents human-readable clinical documentation with structured markup.

This is NOT the same as ED (Encapsulated Data). ED is for binary content in
nonXMLBody; StrucDocText is for structured narrative in section bodies.

Reference: https://build.fhir.org/ig/HL7/CDA-core-sd/narrative.html
Schema: NarrativeBlock.xsd (MIME type: text/x-hl7-text+xml)
"""

from __future__ import annotations

from pydantic import Field

from .datatypes import CDAModel

# ============================================================================
# Root Container
# ============================================================================


class StrucDocText(CDAModel):
    """Structured Document Text - CDA narrative content.

    Container for human-readable clinical narrative with structured markup.
    Can contain paragraphs, lists, tables, and inline formatted content.

    Used in Section.text elements to store narrative that is rendered for
    human readers. Elements can have ID attributes for cross-referencing
    from clinical statements.
    """

    # Direct text (if section contains only plain text, no elements)
    # Use 'text' as field name with '_text' alias to match XML text content
    text: str | None = Field(default=None, alias="_text")

    # Block-level elements
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    table: list[Table] | None = None

    # Inline elements (can appear at root level in some cases)
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )
    footnote: list[Footnote] | None = None

    # Common attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


# ============================================================================
# Block-Level Elements
# ============================================================================


class Paragraph(CDAModel):
    """Paragraph element - basic text block.

    Logically groups narrative content. Can contain text and inline elements.
    Commonly used with ID attributes for cross-referencing.

    Per CDA schema, paragraphs can optionally start with a caption, followed by
    inline elements including styled content, footnotes, and multimedia references.

    Example:
        <paragraph ID="para-1">
            <content styleCode="Bold">Chief Complaint:</content> Chest pain.
        </paragraph>
    """

    # Direct text content (before first child element)
    # Note: Parser automatically extracts element.text into this field
    text: str | None = Field(default=None, alias="_text")

    # Optional caption (must be first child per schema)
    caption: Caption | None = None

    # Inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")

    def get_plain_text(self) -> str:
        """Extract all text content, ignoring formatting.

        Concatenates text from this paragraph and all inline elements.
        Useful for reference resolution and plain text extraction.

        Returns:
            Plain text string with formatting removed
        """
        parts = []
        if self.text:
            parts.append(self.text)
        if self.content:
            for elem in self.content:
                text_content = elem.get_plain_text()
                if text_content:
                    parts.append(text_content)
        if self.sub:
            for elem in self.sub:
                if elem.text:
                    parts.append(elem.text)
        if self.sup:
            for elem in self.sup:
                if elem.text:
                    parts.append(elem.text)
        return " ".join(parts).strip()


class List(CDAModel):
    """List element - ordered or unordered list.

    Can contain multiple items. List type is specified via listType attribute.

    Example:
        <list listType="unordered">
            <item>Hypertension</item>
            <item>Type 2 Diabetes</item>
        </list>
    """

    caption: Caption | None = None
    item: list[ListItem] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    list_type: str | None = Field(default="unordered", alias="listType")


class ListItem(CDAModel):
    """List item element.

    Can contain text, inline elements, and nested block elements.
    Per CDA schema, list items can start with an optional caption, followed by
    inline elements and nested block structures.
    """

    text: str | None = Field(default=None, alias="_text")

    # Optional caption (must be first child per schema)
    caption: Caption | None = None

    # Inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Can also contain nested block elements
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    table: list[Table] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Table(CDAModel):
    """Table element - structured tabular data.

    Presentation-only tables with modified XHTML structure.
    Commonly used with ID attributes on rows or cells for cross-referencing.

    Example:
        <table>
            <tbody>
                <tr ID="row-1"><td>Vital</td><td>Value</td></tr>
            </tbody>
        </table>
    """

    caption: Caption | None = None
    thead: TableHead | None = None
    tfoot: TableFoot | None = None
    tbody: list[TableBody] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    summary: str | None = None
    width: str | None = None
    border: str | None = None
    frame: str | None = None
    rules: str | None = None
    cellspacing: str | None = None
    cellpadding: str | None = None


class TableHead(CDAModel):
    """Table header section."""

    tr: list[TableRow] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class TableBody(CDAModel):
    """Table body section."""

    tr: list[TableRow] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    valign: str | None = None
    align: str | None = None


class TableFoot(CDAModel):
    """Table footer section."""

    tr: list[TableRow] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class TableRow(CDAModel):
    """Table row element.

    Can contain header cells (th) or data cells (td).
    Commonly has ID attribute for cross-referencing.
    """

    th: list[TableHeaderCell] | None = None
    td: list[TableDataCell] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    valign: str | None = None
    align: str | None = None


class TableHeaderCell(CDAModel):
    """Table header cell (th).

    Per CDA schema, table header cells can only contain inline elements,
    not block-level elements like paragraphs or lists.
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements only (per schema)
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    abbr: str | None = None
    axis: str | None = None
    headers: str | None = None
    scope: str | None = None
    rowspan: str | None = None
    colspan: str | None = None
    align: str | None = None
    valign: str | None = None


class TableDataCell(CDAModel):
    """Table data cell (td).

    Can contain text, inline elements, and nested block elements.
    Per CDA schema, data cells support both inline and block-level content,
    including footnotes and multimedia references.
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Can also contain block elements
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    abbr: str | None = None
    axis: str | None = None
    headers: str | None = None
    scope: str | None = None
    rowspan: str | None = None
    colspan: str | None = None
    align: str | None = None
    valign: str | None = None


# ============================================================================
# Inline Elements
# ============================================================================


class Content(CDAModel):
    """Inline styled content element.

    Wraps text for explicit referencing or rendering suggestions.
    Supports recursive nesting and optional ID attributes.

    Per CDA schema, content elements can contain other inline elements including
    footnotes and multimedia references, enabling rich inline formatting.

    Example:
        <content styleCode="Bold">Important</content>
        <content ID="cc-1" styleCode="Italics">Chest pain</content>
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain nested inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")

    # Tail text - text that appears after this element (from lxml tail attribute)
    # Not part of XML schema, but needed to preserve mixed content order
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    revised: str | None = None  # "insert" | "delete"

    def get_plain_text(self) -> str:
        """Get text content with nested elements flattened."""
        parts = []
        if self.text:
            parts.append(self.text)

        if self.content:
            for elem in self.content:
                text = elem.get_plain_text()
                if text:
                    parts.append(text)

        if self.sub:
            for elem in self.sub:
                if elem.text:
                    parts.append(elem.text)

        if self.sup:
            for elem in self.sup:
                if elem.text:
                    parts.append(elem.text)

        return "".join(parts)


class LinkHtml(CDAModel):
    """Hyperlink element.

    Generic referencing mechanism for internal or external targets.
    Per CDA schema, links can contain footnotes and footnote references.
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements (per schema: footnote, footnoteRef)
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")

    # Attributes
    href: str | None = None
    name: str | None = None
    rel: str | None = None
    rev: str | None = None
    title: str | None = None
    id_attr: str | None = Field(default=None, alias="i_d")
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Sub(CDAModel):
    """Subscript element.

    Example: H<sub>2</sub>O
    """

    text: str | None = Field(default=None, alias="_text")

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Sup(CDAModel):
    """Superscript element.

    Example: E = mc<sup>2</sup>
    """

    text: str | None = Field(default=None, alias="_text")
    tail_text: str | None = Field(default=None, exclude=True)

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Br(CDAModel):
    """Line break element.

    Represents a hard line break in narrative text.
    """

    tail_text: str | None = Field(default=None, exclude=True)


# ============================================================================
# Special Elements
# ============================================================================


class Caption(CDAModel):
    """Caption for tables and lists.

    Labels structural elements with descriptive text.
    Per CDA schema, captions can contain limited inline elements and footnote references.
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements (per schema: linkHtml, sub, sup, footnote, footnoteRef)
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    footnote: list[Footnote] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class RenderMultiMedia(CDAModel):
    """Reference to embedded multimedia object.

    References integral multimedia via ObservationMedia or RegionOfInterest entries.
    """

    caption: Caption | None = None

    # Attributes
    referenced_object: str | None = Field(default=None, alias="referencedObject")
    id_attr: str | None = Field(default=None, alias="i_d")
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Footnote(CDAModel):
    """Footnote element.

    Provides supplementary information referenced from narrative.
    Can contain complex narrative structures including paragraphs, lists, and tables.

    Per CDA schema, footnotes support mixed content with both inline elements
    and block-level elements, allowing rich formatting in footnote content.
    """

    text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Can also contain block-level elements
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    table: list[Table] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="i_d")
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class FootnoteRef(CDAModel):
    """Reference to a footnote.

    Points to a footnote element via IDREF attribute.
    """

    # Attributes
    idref: str | None = Field(default=None, alias="IDREF")
    id_attr: str | None = Field(default=None, alias="i_d")
    tail_text: str | None = Field(default=None, exclude=True)
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


# Rebuild models for forward references
# These models have circular/forward references and need explicit rebuilding
Caption.model_rebuild()
Footnote.model_rebuild()
Paragraph.model_rebuild()
Content.model_rebuild()
LinkHtml.model_rebuild()
ListItem.model_rebuild()
List.model_rebuild()
TableHeaderCell.model_rebuild()
TableDataCell.model_rebuild()
TableRow.model_rebuild()
TableHead.model_rebuild()
TableBody.model_rebuild()
TableFoot.model_rebuild()
Table.model_rebuild()
StrucDocText.model_rebuild()
