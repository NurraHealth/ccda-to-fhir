# C-CDA Parser: Quick Start Guide

**For developers picking up parser implementation**

---

## TL;DR

✅ Parser is **58% complete** (18/31 tests passing)
✅ **Basic structures work** - ready to use for simple cases
⚠️ **13 tests failing** - needs 10-15 hours to reach 100%
📝 **Comprehensive docs** available

---

## Getting Started in 5 Minutes

### 1. Install Dependencies

```bash
cd c-cda-to-fhir
uv sync --dev
```

### 2. Run Tests

```bash
# Run all parser tests
uv run pytest tests/unit/test_parser.py -v

# Run a specific test
uv run pytest tests/unit/test_parser.py::TestBasicParsing::test_parse_simple_identifier -v

# Run with coverage
uv run pytest tests/unit/test_parser.py --cov=ccda_to_fhir.ccda.parser --cov-report=html
```

### 3. Try the Parser

```python
from ccda_to_fhir.ccda.parser import parse_ccda_fragment
from ccda_to_fhir.ccda.models import II

xml = '<id root="1.2.3.4" extension="abc" xmlns="urn:hl7-org:v3"/>'
identifier = parse_ccda_fragment(xml, II)

print(identifier.root)       # "1.2.3.4"
print(identifier.extension)  # "abc"
```

---

## What Works Right Now

### ✅ Fully Working

```python
from ccda_to_fhir.ccda.parser import parse_ccda_fragment
from ccda_to_fhir.ccda.models import II, CE, TS, BL, CS

# Identifiers
xml = '<id root="2.16.840.1.113883.19.5" extension="12345" xmlns="urn:hl7-org:v3"/>'
ii = parse_ccda_fragment(xml, II)  # ✅ Works perfectly

# Coded elements
xml = '<code code="F" codeSystem="2.16.840.1.113883.5.1" xmlns="urn:hl7-org:v3"/>'
ce = parse_ccda_fragment(xml, CE)  # ✅ Works perfectly

# Timestamps
xml = '<birthTime value="19470501" xmlns="urn:hl7-org:v3"/>'
ts = parse_ccda_fragment(xml, TS)  # ✅ Works perfectly

# Booleans
xml = '<value value="true" xmlns="urn:hl7-org:v3"/>'
bl = parse_ccda_fragment(xml, BL)  # ✅ Works perfectly
```

### ⚠️ Partially Working

```python
# Person names - works but has issues with ENXP wrapping
xml = '''<name use="L" xmlns="urn:hl7-org:v3">
    <given>John</given>
    <family>Doe</family>
</name>'''
pn = parse_ccda_fragment(xml, PN)  # ⚠️ Parses but field types wrong

# Nested observations - basic works, complex fails
xml = '''<act classCode="ACT" moodCode="EVN" xmlns="urn:hl7-org:v3">
    <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
    <statusCode code="active"/>
</act>'''
act = parse_ccda_fragment(xml, Act)  # ⚠️ Works for simple, fails with nested entryRelationship
```

### ❌ Not Working Yet

```python
# SDTC namespace elements
xml = '''<patient xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
    <sdtc:deceasedInd value="false"/>
</patient>'''
patient = parse_ccda_fragment(xml, Patient)
# ❌ patient.sdtc_deceased_ind returns None (should be False)

# Complex nested structures (3+ levels)
# ❌ Needs debugging

# Real C-CDA fixtures
# ❌ Fail due to above issues
```

---

## Priority Tasks (In Order)

### Task 1: Fix SDTC Namespace Parsing (1-2 hours) 🔴

**Problem**: `sdtc:deceasedInd` not being parsed into `sdtc_deceased_ind` field

**File**: `ccda_to_fhir/ccda/parser.py`, lines 219-231

**Test**: `tests/unit/test_parser.py::TestNamespaceHandling::test_parse_with_sdtc_namespace`

**Debug Steps**:
```python
# Add this around line 220
for child in element:
    tag = _strip_namespace(child.tag)
    print(f"[DEBUG] Child tag: {child.tag}")
    print(f"[DEBUG] Stripped tag: {tag}")
    print(f"[DEBUG] Has sdtc: {'sdtc' in str(child.tag)}")
```

**Expected Fix**: Ensure SDTC elements like `{urn:hl7-org:sdtc}deceasedInd` become `sdtc_deceased_ind`

---

### Task 2: Fix PN/AD Parsing (2-3 hours) 🔴

**Problem**: Name parts should be wrapped in ENXP objects and lists

**File**: `ccda_to_fhir/ccda/parser.py`, lines 342-357

**Test**: `tests/unit/test_parser.py::TestNestedStructures::test_parse_person_name`

**Current Code**:
```python
# Handle name parts (given, family, etc.) - these need to be ENXP objects
if tag in ("given", "family", "prefix", "suffix", "delimiter"):
    text = element.text.strip() if element.text else None
    if not text:
        return None
    attrs = _parse_attributes(element)
    attrs["value"] = text
    return ENXP.model_validate(attrs)  # ⚠️ Always returns single ENXP
```

**Issue**: Need to check if field is `list[ENXP]` (given) or `ENXP` (family)

**Expected Fix**:
```python
if tag in ("given", "family", "prefix", "suffix", "delimiter"):
    text = element.text.strip() if element.text else None
    if not text:
        return None
    attrs = _parse_attributes(element)
    attrs["value"] = text
    enxp = ENXP.model_validate(attrs)

    # Check if parent expects a list
    # (Need to check parent_model_class field annotation)
    return enxp  # Caller will handle list wrapping
```

---

### Task 3: Fix List Aggregation (1-2 hours) 🟠

**Problem**: Multiple IDs, template IDs not being collected into lists

**File**: `ccda_to_fhir/ccda/parser.py`, lines 233-267

**Test**: `tests/unit/test_parser.py::TestListAggregation::test_parse_multiple_identifiers`

**Debug Steps**:
```python
# Add around line 245
field_info = model_fields[field_name]
field_type = field_info.annotation
is_list = _is_list_field(field_type)

print(f"[DEBUG] Field: {field_name}")
print(f"[DEBUG] Type: {field_type}")
print(f"[DEBUG] Is list: {is_list}")
print(f"[DEBUG] Elements count: {len(elements)}")
```

**Expected Fix**: Ensure list detection and aggregation works for all repeated elements

---

### Task 4: Fix Nested Structures (3-4 hours) 🔴

**Problem**: EntryRelationships with nested observations not parsing

**File**: `ccda_to_fhir/ccda/parser.py`, lines 300-370

**Test**: `tests/unit/test_parser.py::TestNestedStructures::test_parse_nested_observations_in_act`

**This is the hardest one** - requires deep understanding of Union type handling

---

## File Roadmap

```
ccda_to_fhir/ccda/parser.py (500+ lines)
├── Lines 1-88:     Setup and model rebuilds
├── Lines 89-176:   Helper functions and type handling
├── Lines 177-285:  ⭐ Core parser (_parse_element) - MOST IMPORTANT
├── Lines 286-370:  ⭐ Child parsing (_parse_child_element) - NEEDS MOST WORK
├── Lines 371-430:  Type utilities
└── Lines 431-490:  Public API

Focus on lines 177-370 for most fixes!
```

---

## Running Individual Tests

```bash
# SDTC namespace test
uv run pytest tests/unit/test_parser.py::TestNamespaceHandling::test_parse_with_sdtc_namespace -vv

# Person name test
uv run pytest tests/unit/test_parser.py::TestNestedStructures::test_parse_person_name -vv

# List aggregation test
uv run pytest tests/unit/test_parser.py::TestListAggregation::test_parse_multiple_identifiers -vv

# All failing tests
uv run pytest tests/unit/test_parser.py -v | grep FAILED
```

---

## Debugging Checklist

When a test fails:

- [ ] Run the test in isolation with `-vv` flag
- [ ] Read the test code to understand expectations
- [ ] Add print statements in parser at key decision points
- [ ] Check what the Pydantic model expects:
      ```python
      from ccda_to_fhir.ccda.models import ModelName
      print(ModelName.model_fields)
      ```
- [ ] Inspect the XML structure:
      ```python
      from lxml import etree
      root = etree.fromstring(xml)
      print(etree.tostring(root, pretty_print=True).decode())
      ```
- [ ] Trace through `_parse_element()` and `_parse_child_element()`
- [ ] Check namespace handling
- [ ] Verify type detection (`_is_list_field`, `_unwrap_field_type`)
- [ ] Test fix incrementally
- [ ] Re-run all tests to ensure no regressions

---

## Common Patterns

### Pattern 1: Adding Debug Output

```python
def _parse_element(element: etree._Element, model_class: type[T]) -> T:
    data: dict[str, Any] = {}

    # ADD THIS
    print(f"\n[PARSE] Parsing {_strip_namespace(element.tag)} as {model_class.__name__}")

    data.update(_parse_attributes(element))

    # ADD THIS
    print(f"[ATTRS] {data}")
```

### Pattern 2: Checking Model Fields

```python
# In a test or debug session
from ccda_to_fhir.ccda.models import PN

print("PN fields:")
for name, field in PN.model_fields.items():
    print(f"  {name}: {field.annotation}")

# Output shows:
#   given: list[ENXP] | None
#   family: ENXP | None
```

### Pattern 3: Testing XML Fragments

```python
# Create minimal test case
from ccda_to_fhir.ccda.parser import parse_ccda_fragment
from ccda_to_fhir.ccda.models import Patient

xml = '''
<patient xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
    <sdtc:deceasedInd value="false"/>
</patient>
'''

patient = parse_ccda_fragment(xml, Patient)
print(f"deceased_ind: {patient.sdtc_deceased_ind}")
# Should be False, currently None
```

---

## Success Criteria

### For Each Task
- [ ] Test passes
- [ ] No new test failures
- [ ] Code is readable
- [ ] Debug prints removed or commented
- [ ] Git commit with clear message

### For Overall Completion
- [ ] 80%+ tests passing (25/31) - GOOD ENOUGH
- [ ] 95%+ tests passing (30/31) - PRODUCTION READY
- [ ] 100% tests passing (31/31) - EXCELLENT

---

## Documentation

📄 **[parser-remaining-work.md](./parser-remaining-work.md)** - Detailed task breakdown with technical analysis

📄 **[parser-implementation-summary.md](./parser-implementation-summary.md)** - Comprehensive overview of what's built

📄 **This file** - Quick start for getting productive fast

---

## Getting Help

1. **Check the test** - What does it expect?
2. **Check the model** - What does Pydantic expect?
3. **Check the XML** - What structure are we parsing?
4. **Add prints** - Trace the execution
5. **Compare with working tests** - What's different?

---

## Time Estimates

| Task | Difficulty | Time | Tests Fixed |
|------|------------|------|-------------|
| SDTC namespace | Medium | 1-2h | 1-2 tests |
| PN/AD parsing | Medium | 2-3h | 2-3 tests |
| List aggregation | Easy | 1-2h | 3 tests |
| Nested structures | Hard | 3-4h | 3-4 tests |
| **Total** | - | **7-11h** | **9-12 tests** |

**Result**: 27-30 tests passing (87-97%) after 1-2 days of focused work

---

## Quick Commands Reference

```bash
# Run all parser tests
uv run pytest tests/unit/test_parser.py -v

# Run one test
uv run pytest tests/unit/test_parser.py::TestClass::test_name -vv

# Run with debugger on failure
uv run pytest tests/unit/test_parser.py --pdb

# Run with coverage
uv run pytest tests/unit/test_parser.py --cov=ccda_to_fhir.ccda.parser

# Show failing tests only
uv run pytest tests/unit/test_parser.py --tb=no | grep FAILED

# Run fast (no coverage, no verbose)
uv run pytest tests/unit/test_parser.py -q
```

---

## Final Notes

- ✅ **Parser works** - don't be intimidated by failing tests
- ✅ **Good foundation** - code is well-structured
- ✅ **Clear path forward** - issues are well-defined
- ✅ **Comprehensive tests** - know exactly what needs fixing

**You can do this!** Start with Task 1 (SDTC namespace), get that one test passing, then move to Task 2. Small wins build momentum.

---

**Good luck!** 🚀
