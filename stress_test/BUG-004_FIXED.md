# BUG-004: RelatedPersonConverter missing _convert_oid_to_uri method - FIXED ✅

**Status:** ✅ RESOLVED
**Date Fixed:** 2025-12-23
**Impact:** Unknown number of files with informant/relatedEntity using non-standard code systems

## Problem

RelatedPersonConverter crashed when converting informant elements with relatedEntity that used non-standard code systems:

```
AttributeError: 'RelatedPersonConverter' object has no attribute '_convert_oid_to_uri'
```

Any C-CDA document with an informant/relatedEntity using a code system like SNOMED CT (OID: 2.16.840.1.113883.6.96) would fail during conversion.

## Root Cause

**File:** `ccda_to_fhir/converters/related_person.py` line 148

The converter tried to call a non-existent method `self._convert_oid_to_uri()`:

```python
if code.code_system == "2.16.840.1.113883.5.111":
    coding["system"] = FHIRSystems.V3_ROLE_CODE
else:
    coding["system"] = self._convert_oid_to_uri(code.code_system)  # ❌ Method doesn't exist
```

The correct method is `self.map_oid_to_uri()` which is inherited from `BaseConverter`. This method delegates to `CodeSystemMapper.oid_to_uri()` to convert OIDs like "2.16.840.1.113883.6.96" to FHIR canonical URIs like "http://snomed.info/sct".

## Fix Applied

**File:** `ccda_to_fhir/converters/related_person.py` line 148

**Before:**
```python
if code.code_system == "2.16.840.1.113883.5.111":
    coding["system"] = FHIRSystems.V3_ROLE_CODE
else:
    coding["system"] = self._convert_oid_to_uri(code.code_system)  # ❌ AttributeError
```

**After:**
```python
if code.code_system == "2.16.840.1.113883.5.111":
    coding["system"] = FHIRSystems.V3_ROLE_CODE
else:
    coding["system"] = self.map_oid_to_uri(code.code_system)  # ✅ Correct method
```

## Regression Test Added

**File:** `tests/integration/test_informant_mapping.py`

Added test method and fixture:

```python
def test_related_person_converts_non_standard_code_system(
    self, sample_ccda_with_snomed_relationship_code
):
    """Test that RelatedPerson properly converts non-standard code system OIDs.

    Regression test for BUG-004: RelatedPersonConverter called non-existent
    _convert_oid_to_uri() method. Should use map_oid_to_uri() from BaseConverter.
    """
    bundle = convert_document(sample_ccda_with_snomed_relationship_code)

    related_persons = [
        r for r in bundle["entry"]
        if r["resource"]["resourceType"] == "RelatedPerson"
    ]
    assert len(related_persons) == 1

    related_person = related_persons[0]["resource"]

    # Verify relationship exists with SNOMED code
    assert "relationship" in related_person
    relationship = related_person["relationship"][0]

    # Should have converted SNOMED CT OID to proper URI
    snomed_coding = next(
        (c for c in relationship["coding"] if c.get("code") == "444301002"),
        None
    )
    assert snomed_coding is not None
    # OID 2.16.840.1.113883.6.96 should map to http://snomed.info/sct
    assert snomed_coding["system"] == "http://snomed.info/sct"
    assert snomed_coding["display"] == "Caregiver"
```

Test fixture includes:
- Informant with relatedEntity
- Code element with SNOMED CT code system (OID: 2.16.840.1.113883.6.96)
- Code "444301002" (Caregiver concept)

All tests pass ✅

## Impact Measurement

### Stress Test Results (100 ONC samples)

**After Fix:**
- Success rate: **31%** (31/100 files)
- **4 RelatedPerson resources** successfully created
- **919 total FHIR resources** created across successful conversions

**Before Fix:**
Any C-CDA document with informant/relatedEntity using non-standard code systems would have crashed with AttributeError. The fix prevents these crashes and allows proper OID-to-URI conversion.

### How This Bug Was Found

1. Stress testing revealed AttributeError in some files
2. Error trace pointed to line 148 in `related_person.py`
3. Code inspection revealed call to non-existent `_convert_oid_to_uri()` method
4. Codebase search showed correct pattern is `self.map_oid_to_uri()`
5. Checked `base.py` and confirmed `map_oid_to_uri()` exists and delegates to `CodeSystemMapper`

### Technical Details

The converter architecture uses:
- `BaseConverter.map_oid_to_uri(oid)` - Public method all converters can use
- `CodeSystemMapper.oid_to_uri(oid)` - Core OID-to-URI mapping logic
- Maps OIDs to FHIR canonical URIs per FHIR R4B specifications

Example mappings:
- `2.16.840.1.113883.6.96` → `http://snomed.info/sct` (SNOMED CT)
- `2.16.840.1.113883.6.1` → `http://loinc.org` (LOINC)
- `2.16.840.1.113883.6.88` → `http://www.nlm.nih.gov/research/umls/rxnorm` (RxNorm)

## Verification

Run regression test:
```bash
uv run pytest tests/integration/test_informant_mapping.py::TestInformantMapping::test_related_person_converts_non_standard_code_system -v
```

Run stress test to verify no AttributeError crashes:
```bash
uv run python stress_test/stress_test.py --onc-only --limit 100
```

## Next Steps

This was a critical bug that prevented conversion of C-CDA documents with informant elements using non-standard code systems. The fix enables proper OID-to-URI conversion per FHIR R4B specifications.

Next highest priority bugs from stress test:
1. **BUG-002**: Missing timezone on datetime fields (33 files) - ValidationError
2. **BUG-003**: Missing required C-CDA fields causing ValueError (52 files)
3. **FEATURE-001**: Add CO (Coded Ordinal) data type support (7 files) - UnknownTypeError

---

**Resolution Confirmed:** ✅ Real production bug fixed, regression test added, stress test shows 4 RelatedPerson resources successfully created
