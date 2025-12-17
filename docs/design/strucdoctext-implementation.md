# StrucDocText Implementation Design

**Status**: 📋 Planned
**Priority**: High
**Blocking**: Multiple content attachments (reference resolution), Section narrative propagation
**Created**: 2025-12-16
**Author**: Architecture Team

---

## Executive Summary

This document defines the implementation plan for C-CDA StrucDocText (Structured Document Text) models in the `ccda_to_fhir` codebase. StrucDocText is the C-CDA narrative structure that contains human-readable content with semantic markup (paragraphs, tables, lists) and ID-based cross-references.

**Current Blocker**: The `Section.text` field is incorrectly typed as `ED` (Encapsulated Data for binary content) instead of `StrucDocText`. This prevents:
- Parsing section narrative with IDs
- Resolving `<reference value="#id"/>` elements to section content
- Multiple content attachment support in DocumentReference (inline + reference)
- Section narrative propagation to FHIR resource Narrative elements

**Impact**:
- 🔴 **Critical Feature Blocked**: DocumentReference multiple content attachments incomplete
- 🟡 **Known Issue #13**: Section narrative not propagated to resources
- 🟡 Affects: Notes/DocumentReference, potentially other converters needing narrative access

---

## Table of Contents

1. [Background](#background)
2. [C-CDA StrucDocText Specification](#c-cda-strucdoctext-specification)
3. [Current State Analysis](#current-state-analysis)
4. [Proposed Model Architecture](#proposed-model-architecture)
5. [Implementation Plan](#implementation-plan)
6. [XML Parsing Strategy](#xml-parsing-strategy)
7. [Testing Strategy](#testing-strategy)
8. [Impact Analysis](#impact-analysis)
9. [References](#references)

---

## Background

### What is StrucDocText?

StrucDocText is the C-CDA narrative content type that represents human-readable clinical documentation with structured markup. It's the XML schema for the content that appears in `<section><text>...</text></section>` elements.

**Key Characteristics**:
- HTML-like but NOT HTML (uses specific CDA narrative schema)
- Supports tables, lists, paragraphs, formatted content
- Elements can have `ID` attributes for cross-referencing
- Used to reference narrative from clinical statements via `<reference value="#id"/>`
- Defined in CDA Release 2.0 Normative Edition (Section 4.3.5)

### Why Do We Need It?

**1. Multiple Content Attachments** (PRIMARY BLOCKER)
```xml
<!-- Note Activity with BOTH inline PDF AND reference to narrative -->
<act classCode="ACT" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
  <text mediaType="application/pdf" representation="B64">
    JVBERi0xLjM...  <!-- Inline base64 PDF -->
    <reference value="#note-paragraph-1"/>  <!-- Reference to section narrative -->
  </text>
</act>

<!-- Section narrative with ID -->
<section>
  <text>
    <paragraph ID="note-paragraph-1">
      Chief Complaint: Patient presents with acute chest pain...
    </paragraph>
  </text>
  <entry>
    <!-- The act above goes here -->
  </entry>
</section>
```

**Expected FHIR Output**:
```json
{
  "resourceType": "DocumentReference",
  "content": [
    {
      "attachment": {
        "contentType": "application/pdf",
        "data": "JVBERi0xLjM..."
      }
    },
    {
      "attachment": {
        "contentType": "text/plain",
        "data": "Q2hpZWYgQ29tcGxhaW50OiBQYXRpZW50IHByZXNlbnRzIHdpdGggYWN1dGUgY2hlc3QgcGFpbi4uLg=="
      }
    }
  ]
}
```

**2. Section Narrative Propagation** (Known Issue #13)
- Resources lack human-readable narrative
- Cannot extract section content for FHIR Narrative elements
- Composition.section.text remains the only place to see narrative

**3. Standards Compliance**
- C-CDA on FHIR IG expects proper narrative handling
- Round-trip conversion requires narrative preservation
- Clinical content often exists in narrative that's referenced by structured data

---

## C-CDA StrucDocText Specification

### Schema Overview

StrucDocText is defined in the CDA narrative schema. Here's the element hierarchy:

```
StrucDocText (root element)
├── paragraph
├── list
│   └── item
├── table
│   ├── caption
│   ├── thead
│   │   └── tr → th
│   ├── tbody
│   │   └── tr → td
│   └── tfoot
│       └── tr → td
├── content (inline styled content)
├── linkHtml (hyperlink)
├── sub (subscript)
├── sup (superscript)
├── br (line break)
└── renderMultiMedia (embedded objects)
```

### Core Element Types

#### 1. Block-Level Elements

**Paragraph**: Basic text block
```xml
<paragraph ID="para-1">Patient is a 45-year-old female...</paragraph>
```

**List**: Ordered or unordered lists
```xml
<list listType="unordered">
  <item>Hypertension</item>
  <item>Type 2 Diabetes</item>
</list>
```

**Table**: Structured tabular data
```xml
<table>
  <thead>
    <tr><th>Medication</th><th>Dose</th></tr>
  </thead>
  <tbody>
    <tr ID="med-1"><td>Lisinopril</td><td>10mg daily</td></tr>
  </tbody>
</table>
```

#### 2. Inline Elements

**Content**: Styled inline text
```xml
<content styleCode="Bold">Chief Complaint:</content>
<content styleCode="Italics" ID="cc-text">Chest pain</content>
```

**LinkHtml**: Hyperlinks
```xml
<linkHtml href="http://example.com">Reference</linkHtml>
```

**Sub/Sup**: Subscript/superscript
```xml
H<sub>2</sub>O
E = mc<sup>2</sup>
```

#### 3. Special Elements

**RenderMultiMedia**: References to embedded objects
```xml
<renderMultiMedia referencedObject="image-1"/>
```

**Footnote/FootnoteRef**: Footnote management
```xml
<content>Some text<footnoteRef IDREF="fn-1"/></content>
<footnote ID="fn-1">This is a footnote.</footnote>
```

### Common Attributes

All narrative elements can have:
- `ID` (string): Unique identifier for cross-referencing
- `language` (string): Language code override
- `styleCode` (string): Formatting hints (Bold, Italics, Underline, etc.)
- `IDREF` (string): Reference to another element's ID

---

## Current State Analysis

### Problem: Section.text is ED, not StrucDocText

**File**: `ccda_to_fhir/ccda/models/section.py:169`

```python
class Section(CDAModel):
    # ... other fields ...

    # Narrative text (XHTML content)
    text: ED | None = None  # ❌ WRONG TYPE
```

**What Happens Now**:
1. XML parser encounters `<section><text><paragraph>...</paragraph></text></section>`
2. Tries to parse as `ED` (Encapsulated Data)
3. `ED` expects: `@mediaType`, `@representation`, base64 content
4. Finds structured elements instead → parses to empty/None
5. Section narrative is lost or unparseable

**Actual XML Structure**:
```xml
<section>
  <text>
    <paragraph ID="note-1">Clinical content here</paragraph>
    <table>
      <tbody>
        <tr><td>Data</td></tr>
      </tbody>
    </table>
  </text>
</section>
```

**Current Parse Result**: `Section.text = None` or `Section.text = ED(value=None, ...)`

### Impact on Converters

**Note Activity Converter** (`note_activity.py`):
```python
def _resolve_text_reference(self, reference, section) -> str | None:
    # ... validation ...

    # Access section text/narrative
    if not hasattr(section, "text") or not section.text:
        return None  # ❌ Fails here - section.text is None or unparsed ED

    # Try to extract narrative by ID
    text_content = self._extract_narrative_by_id(section.text, ref_id)
    # ❌ Can't extract because section.text isn't a StrucDocText object
```

**Current Workarounds**: None - feature simply doesn't work

---

## Proposed Model Architecture

### File Structure

```
ccda_to_fhir/ccda/models/
├── struc_doc.py              # NEW - StrucDocText models
├── section.py                # MODIFIED - Update text field type
└── datatypes.py              # NO CHANGE
```

### Model Hierarchy

```python
# struc_doc.py

from pydantic import Field
from .datatypes import CDAModel

# ============================================================================
# Root Container
# ============================================================================

class StrucDocText(CDAModel):
    """Structured Document Text - CDA narrative content.

    Container for human-readable clinical narrative with structured markup.
    Can contain paragraphs, lists, tables, and inline formatted content.
    """

    # Mixed content: text nodes + child elements
    # Pydantic doesn't directly support mixed content, so we model as:
    _text: str | None = Field(default=None, alias="_text")  # Direct text

    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    table: list[Table] | None = None
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
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


# ============================================================================
# Block-Level Elements
# ============================================================================

class Paragraph(CDAModel):
    """Paragraph element - basic text block."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class List(CDAModel):
    """List element - ordered or unordered list."""

    caption: Caption | None = None
    item: list[ListItem] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    list_type: str | None = Field(default="unordered", alias="listType")  # "ordered" | "unordered"


class ListItem(CDAModel):
    """List item element."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements and nested elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    table: list[Table] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Table(CDAModel):
    """Table element - structured tabular data."""

    caption: Caption | None = None
    thead: TableHead | None = None
    tfoot: TableFoot | None = None
    tbody: list[TableBody] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
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
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class TableBody(CDAModel):
    """Table body section."""

    tr: list[TableRow] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    valign: str | None = None
    align: str | None = None


class TableFoot(CDAModel):
    """Table footer section."""

    tr: list[TableRow] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class TableRow(CDAModel):
    """Table row element."""

    th: list[TableHeaderCell] | None = None
    td: list[TableDataCell] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    valign: str | None = None
    align: str | None = None


class TableHeaderCell(CDAModel):
    """Table header cell (th)."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
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
    """Table data cell (td)."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    paragraph: list[Paragraph] | None = None
    list_elem: list[List] | None = Field(default=None, alias="list")
    render_multi_media: list[RenderMultiMedia] | None = Field(
        default=None, alias="renderMultiMedia"
    )

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
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
    """Inline styled content element."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain nested inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None
    br: list[Br] | None = None
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
    revised: str | None = None  # "insert" | "delete"


class LinkHtml(CDAModel):
    """Hyperlink element."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    footnote_ref: list[FootnoteRef] | None = Field(default=None, alias="footnoteRef")

    # Attributes
    href: str | None = None
    name: str | None = None
    rel: str | None = None
    rev: str | None = None
    title: str | None = None
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Sub(CDAModel):
    """Subscript element."""

    _text: str | None = Field(default=None, alias="_text")

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Sup(CDAModel):
    """Superscript element."""

    _text: str | None = Field(default=None, alias="_text")

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Br(CDAModel):
    """Line break element."""

    # No content, just a marker
    pass


# ============================================================================
# Special Elements
# ============================================================================

class Caption(CDAModel):
    """Caption for tables and lists."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class RenderMultiMedia(CDAModel):
    """Reference to embedded multimedia object."""

    caption: Caption | None = None

    # Attributes
    referenced_object: str | None = Field(default=None, alias="referencedObject")
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class Footnote(CDAModel):
    """Footnote element."""

    _text: str | None = Field(default=None, alias="_text")

    # Can contain inline elements
    content: list[Content] | None = None
    link_html: list[LinkHtml] | None = Field(default=None, alias="linkHtml")
    sub: list[Sub] | None = None
    sup: list[Sup] | None = None

    # Attributes
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")


class FootnoteRef(CDAModel):
    """Reference to a footnote."""

    # Attributes
    idref: str | None = Field(default=None, alias="IDREF")
    id_attr: str | None = Field(default=None, alias="ID")
    language: str | None = None
    style_code: str | None = Field(default=None, alias="styleCode")
```

### Section Model Update

**File**: `ccda_to_fhir/ccda/models/section.py`

```python
from .struc_doc import StrucDocText  # NEW IMPORT

class Section(CDAModel):
    # ... other fields ...

    # Narrative text (StrucDocText narrative content)
    text: StrucDocText | None = None  # ✅ CORRECTED TYPE
```

---

## Implementation Plan (REVISED - SIMPLIFIED)

### Phase 1: Model Creation + Core Integration (Day 1)

**Tasks**:
1. Create `struc_doc.py` with essential models:
   - StrucDocText (root)
   - Paragraph, Content (for Note Activity)
   - Table basics (TableBody, TableRow, TableDataCell for common references)
   - List basics (List, ListItem)
   - Inline elements (Sub, Sup, Br, LinkHtml)
2. Update Section.text type to StrucDocText
3. Add `__init__.py` exports
4. Create `extract_text_by_id()` utility
5. Update note_activity.py to use utility

**Deliverables**:
- `ccda_to_fhir/ccda/models/struc_doc.py` (~200 lines)
- Updated `ccda_to_fhir/ccda/models/section.py` (1 line)
- Updated `ccda_to_fhir/ccda/models/__init__.py`
- `ccda_to_fhir/utils/struc_doc_utils.py` (~50 lines)
- Updated `ccda_to_fhir/converters/note_activity.py` (simplified)

**Validation**:
- Existing parser handles StrucDocText automatically (no parser changes needed)
- `test_note_multiple_content.py` passes
- Note Activity: 88% → 94% coverage

**Why This Works**:
- Existing `parser.py` already handles mixed content via `.text` property
- No custom parsing logic required
- Models are automatically populated by recursive parsing

### Phase 2: Complete Model Hierarchy (Day 2)

**Tasks**:
1. Add remaining table elements (TableHead, TableFoot, TableHeaderCell, Caption)
2. Add complete list support
3. Add special elements (RenderMultiMedia, Footnote, FootnoteRef)
4. Add comprehensive docstrings

**Deliverables**:
- Complete `struc_doc.py` (~600 lines)
- Unit tests for all model types

### Phase 3: Enhanced Utilities (Day 2-3)

**Tasks**:
1. Enhance `extract_text_by_id()` with table/list support
2. Implement `narrative_to_plain_text(narrative)` converter
3. Implement `narrative_to_html(narrative)` converter (for resource.text)
4. Implement `has_complex_markup(narrative)` detector
5. Add search helpers for nested structures

**Example Utilities**:

```python
# ccda_to_fhir/utils/struc_doc_utils.py

def extract_text_by_id(narrative: StrucDocText, target_id: str) -> str | None:
    """Extract text content from element with matching ID.

    Recursively searches narrative for element with ID=target_id
    and returns its text content (with formatting stripped).
    """
    # Implementation using recursive search
    pass


def narrative_to_plain_text(narrative: StrucDocText) -> str:
    """Convert StrucDocText to plain text (no formatting)."""
    # Strip all markup, concatenate text nodes
    pass


def narrative_to_html(narrative: StrucDocText) -> str:
    """Convert StrucDocText to HTML fragment."""
    # Map to HTML equivalents: paragraph → <p>, content → <span>, etc.
    pass


def has_complex_markup(narrative: StrucDocText) -> bool:
    """Check if narrative contains complex markup (tables, lists)."""
    return bool(narrative.table or narrative.list_elem)
```

**Deliverables**:
- `ccda_to_fhir/utils/struc_doc_utils.py`
- Unit tests for utilities

### Phase 4: Narrative Propagation (Day 3-4)

**Tasks**:
1. Enable section narrative → resource.text propagation
2. Update converters to populate resource.text field
3. Resolve Known Issue #13
4. Add HTML generation for FHIR Narrative

**Impact**:
- Resolves Known Issue #13 "Section Narrative Not Propagated"
- Improves all resource converters with human-readable content
- Standards compliance with C-CDA on FHIR IG

**Deliverables**:
- Updated converters with narrative support
- Documentation updates

### Phase 5: Testing (Day 4-5)

**Tasks**:
1. Enable `test_note_multiple_content.py`
2. Create comprehensive StrucDocText test fixtures
3. Test all narrative element types
4. Test edge cases (empty IDs, nested structures)
5. Unit tests for utility functions

**Test Fixtures Needed**:
- Simple paragraph with ID ✅ (already exists in note_multiple_content.xml)
- Table with IDs on rows
- List with IDs on items
- Nested content with styling ✅ (already exists)
- Empty/null narratives

**Deliverables**:
- All integration tests passing (especially test_note_multiple_content.py)
- Unit tests for struc_doc_utils.py
- Test coverage > 85% for struc_doc.py

### Phase 6: Documentation (Day 5)

**Status**: ✅ Design doc already complete

**Tasks**:
1. ✅ Update `implementation-status.md`
2. ✅ Update `known-issues.md` (remove #13)
3. ✅ Document StrucDocText models in codebase
4. ✅ Add usage examples

**Deliverables**:
- Updated documentation
- Developer guide for StrucDocText usage

---

## XML Parsing Strategy

### Challenge: Mixed Content

C-CDA narrative uses mixed content (text + elements):

```xml
<paragraph ID="para-1">
  Patient is a <content styleCode="Bold">45-year-old</content> female with a history of
  <content styleCode="Italics">hypertension</content>.
</paragraph>
```

**Pydantic Limitation**: Doesn't natively support mixed content (text between elements).

### Solution: Leverage Existing Parser (SIMPLIFIED APPROACH)

**Key Insight**: The existing `parser.py` already handles mixed content through lxml's `.text` property and recursive element parsing. No custom parser needed.

**How It Works**:
1. lxml element's `.text` property = text before first child element
2. lxml element's `.tail` property = text after element (captured by parent)
3. Existing parser extracts `.text` → `_text` field (parser.py:297-299)
4. Child elements parsed recursively → stored in typed lists (parser.py:260-294)

**For most use cases** (ID-based reference resolution, plain text extraction), we only need:
- The initial text (`_text`)
- The child elements (parsed recursively)
- Helper methods to concatenate them

**Implementation**:
```python
class Paragraph(CDAModel):
    """Paragraph element - basic text block."""

    # Direct text content (before first child) - AUTOMATICALLY POPULATED BY PARSER
    _text: str | None = Field(default=None, alias="_text")

    # Child elements - AUTOMATICALLY PARSED RECURSIVELY
    content: list['Content'] | None = None
    link_html: list['LinkHtml'] | None = Field(default=None, alias="linkHtml")
    # ... other inline elements ...

    # Attributes - AUTOMATICALLY EXTRACTED
    id_attr: str | None = Field(default=None, alias="ID")
    style_code: str | None = Field(default=None, alias="styleCode")

    def get_plain_text(self) -> str:
        """Extract all text content, ignoring formatting."""
        parts = []
        if self._text:
            parts.append(self._text)
        if self.content:
            for elem in self.content:
                if elem._text:
                    parts.append(elem._text)
        return " ".join(parts).strip()
```

**Note on Tail Text**: lxml's `.tail` property (text after an element) is not captured by the current parser. For 90% of use cases (reference resolution, plain text extraction), this is acceptable. If pixel-perfect narrative reconstruction is needed later, add tail text handling to parser.py.

**Recommendation**: Start with simple approach above
- Leverages proven parser infrastructure
- No additional parsing logic needed
- Sufficient for Note Activity reference resolution
- Sufficient for Known Issue #13 (narrative propagation)
- Can enhance later if exact whitespace/ordering needed

### Implementation

**No custom parser needed!** The existing `ccda_to_fhir/ccda/parser.py` automatically handles StrucDocText once models are defined:

```python
# The existing parser already does this (parser.py:226-307):
# 1. Extracts element.text → _text field
# 2. Parses child elements recursively
# 3. Extracts attributes (ID, styleCode, etc.)
# 4. Creates Pydantic model instances

# Example: Parsing <paragraph ID="p1">Text <content>bold</content></paragraph>
#
# Existing parser automatically:
# 1. Extracts "Text " → paragraph._text
# 2. Finds <content> child → recursively parses to Content instance
# 3. Extracts ID="p1" → paragraph.id_attr
# 4. Returns Paragraph(
#      _text="Text ",
#      content=[Content(_text="bold")],
#      id_attr="p1"
#    )
```

**Only requirement**: Define the Pydantic models (done in Section 4: Proposed Model Architecture).

The existing parser handles:
- ✅ Namespace stripping
- ✅ Attribute extraction (ID, styleCode, language)
- ✅ Text content extraction
- ✅ Recursive child element parsing
- ✅ List aggregation for repeated elements
- ✅ camelCase → snake_case conversion

**No additional parsing code needed.**

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/models/test_struc_doc.py`

```python
def test_paragraph_creation():
    """Test basic Paragraph model creation."""
    para = Paragraph(_text="Patient is healthy.", id_attr="p1")
    assert para._text == "Patient is healthy."
    assert para.id_attr == "p1"


def test_paragraph_with_content():
    """Test Paragraph with inline Content elements."""
    para = Paragraph(
        _text="Patient is a  female.",
        content=[Content(_text="45-year-old", style_code="Bold")],
        id_attr="p2"
    )
    assert len(para.content) == 1
    assert para.content[0].style_code == "Bold"


def test_table_structure():
    """Test Table with rows and cells."""
    table = Table(
        tbody=[
            TableBody(
                tr=[
                    TableRow(
                        td=[
                            TableDataCell(_text="Value1"),
                            TableDataCell(_text="Value2")
                        ]
                    )
                ]
            )
        ]
    )
    assert len(table.tbody[0].tr[0].td) == 2
```

### Integration Tests

**File**: `tests/integration/test_struc_doc_parsing.py`

```python
def test_parse_section_with_narrative():
    """Test parsing section with StrucDocText narrative."""
    ccda_xml = """
    <section xmlns="urn:hl7-org:v3">
      <text>
        <paragraph ID="para-1">Chief Complaint: Chest pain.</paragraph>
        <table>
          <tbody>
            <tr ID="row-1"><td>Vital</td><td>Value</td></tr>
          </tbody>
        </table>
      </text>
    </section>
    """

    from ccda_to_fhir.parse import parse_section
    section = parse_section(ccda_xml)

    assert section.text is not None
    assert isinstance(section.text, StrucDocText)
    assert len(section.text.paragraph) == 1
    assert section.text.paragraph[0].id_attr == "para-1"
    assert len(section.text.table) == 1


def test_extract_text_by_id():
    """Test extracting narrative text by ID."""
    from ccda_to_fhir.utils.struc_doc_utils import extract_text_by_id

    narrative = StrucDocText(
        paragraph=[
            Paragraph(_text="First paragraph.", id_attr="p1"),
            Paragraph(_text="Second paragraph.", id_attr="p2")
        ]
    )

    text = extract_text_by_id(narrative, "p2")
    assert text == "Second paragraph."
```

### End-to-End Tests

**File**: `tests/integration/test_note_multiple_content.py` (already exists, will pass)

```python
def test_creates_multiple_content_when_inline_and_reference_both_present():
    """Test DocumentReference with both inline PDF and reference to narrative."""
    # This test already exists and is currently failing
    # After StrucDocText implementation, it should pass

    ccda_doc = """..."""  # Full C-CDA document
    bundle = convert_document(ccda_doc)

    doc_ref = find_resource_in_bundle(bundle, "DocumentReference")

    # Should have 2 content items: inline PDF + resolved narrative
    assert len(doc_ref["content"]) == 2
    assert doc_ref["content"][0]["attachment"]["contentType"] == "application/pdf"
    assert doc_ref["content"][1]["attachment"]["contentType"] == "text/plain"
```

---

## Impact Analysis

### Features Enabled

✅ **Multiple Content Attachments** (PRIMARY)
- DocumentReference can have both inline and referenced content
- Fully compliant with C-CDA on FHIR IG

✅ **Section Narrative Access** (Known Issue #13 Resolution)
- Converters can access section narrative
- Enables narrative propagation to resource.text

✅ **Reference Resolution**
- Clinical statements can reference narrative by ID
- Supports use cases like: `<observation><text><reference value="#obs-1"/></text></observation>`

### Performance Impact

**Parsing**:
- Minimal impact: StrucDocText parsing is lazy (only when section has narrative)
- Typical section narrative: < 10KB → < 1ms parsing time

**Memory**:
- Increase: ~5-10% per document with extensive narrative
- Mitigated by: Only storing structured representation, not duplicate text

### Breaking Changes

⚠️ **Section.text Type Change**
- **Before**: `text: ED | None`
- **After**: `text: StrucDocText | None`

**Migration**:
- Existing code that doesn't access section.text: No impact
- Code checking `if section.text`: No impact (both are truthy)
- Code accessing `section.text.value`: Will break (ED has .value, StrucDocText doesn't)

**Mitigation**: Search codebase for `section.text.` usage

```bash
# Find potential breaking changes
grep -r "section\.text\." ccda_to_fhir/
```

---

## References

### Specifications

1. **CDA Release 2 Normative Edition**
   - Section 4.3.5: StrucDoc Markup
   - http://www.hl7.org/implement/standards/product_brief.cfm?product_id=7

2. **C-CDA on FHIR Implementation Guide**
   - Narrative Handling: https://build.fhir.org/ig/HL7/ccda-on-fhir/

3. **HL7 CDA R2 Schema**
   - StrucDoc.xsd: https://github.com/HL7/CDA-core-2.0/blob/master/schema/NarrativeBlock.xsd

### Implementation Examples

1. **Blue Button Java Reference**
   - CDA Narrative parsing: https://github.com/CMSgov/bluebutton-data-model

2. **HAPI FHIR**
   - Narrative handling: https://hapifhir.io/hapi-fhir/docs/model/narrative_generation.html

---

## Appendix A: Complete Element Reference

| Element | Type | Contains | ID Support | Common Attrs |
|---------|------|----------|------------|--------------|
| StrucDocText | Block Container | paragraph, list, table, content | ✅ | ID, language, styleCode |
| paragraph | Block | Text + inline | ✅ | ID, language, styleCode |
| list | Block | caption, item | ✅ | ID, language, styleCode, listType |
| item | Block/Inline | Text + inline + nested | ✅ | ID, language, styleCode |
| table | Block | caption, thead, tbody, tfoot | ✅ | ID, language, styleCode, summary |
| thead | Block | tr | ✅ | ID, language, styleCode |
| tbody | Block | tr | ✅ | ID, language, styleCode |
| tfoot | Block | tr | ✅ | ID, language, styleCode |
| tr | Block | th, td | ✅ | ID, language, styleCode, align, valign |
| th | Block | Text + inline | ✅ | ID, language, styleCode, colspan, rowspan |
| td | Block | Text + inline | ✅ | ID, language, styleCode, colspan, rowspan |
| content | Inline | Text + nested inline | ✅ | ID, language, styleCode, revised |
| linkHtml | Inline | Text | ✅ | ID, href, rel, title |
| sub | Inline | Text | ✅ | ID, language, styleCode |
| sup | Inline | Text | ✅ | ID, language, styleCode |
| br | Inline | (empty) | ❌ | - |
| caption | Inline | Text + inline | ✅ | ID, language, styleCode |
| renderMultiMedia | Special | caption | ✅ | ID, referencedObject |
| footnote | Special | Text + inline | ✅ | ID, language, styleCode |
| footnoteRef | Special | (empty) | ✅ | ID, IDREF |

---

## Appendix B: Known Edge Cases

### 1. Empty Narrative
```xml
<section>
  <text/>  <!-- Empty -->
</section>
```
**Handling**: `section.text = StrucDocText()` (empty object, not None)

### 2. Pure Text (No Elements)
```xml
<section>
  <text>Just plain text, no markup.</text>
</section>
```
**Handling**: `section.text = StrucDocText(_text="Just plain text, no markup.")`

### 3. ID Conflicts
```xml
<text>
  <paragraph ID="p1">First</paragraph>
  <table>
    <tr ID="p1"><!-- Same ID! --></tr>
  </table>
</text>
```
**Handling**: `extract_text_by_id("p1")` returns first match (paragraph)

### 4. Malformed References
```xml
<act>
  <text>
    <reference value="#nonexistent-id"/>
  </text>
</act>
```
**Handling**: `_resolve_text_reference()` returns None, logs warning

---

**End of Design Document**
