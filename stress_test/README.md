# C-CDA to FHIR Converter - Stress Test Suite

Comprehensive stress testing infrastructure for validating C-CDA to FHIR conversion quality, accuracy, and compliance.

## Quick Start

```bash
# Run stress test on real-world EHR data
uv run python stress_test.py --onc-only --output results.json

# Analyze results
uv run python analyze_results.py results.json --output REPORT.md

# View filtered real issues (excluding fragments)
uv run python filter_real_issues.py
```

## Test Results (Latest Run: 2025-12-23)

**Total C-CDA Files Tested:** 828 (382 ONC + 446 HL7)

### Current Status
- **Success Rate:** 0% (baseline before bug fixes)
- **Real Issues (excluding fragments/namespace):** 416 files
- **Projected Success Rate (after fixes):** 29-50%

### Error Breakdown
| Category | Count | % | Solvability |
|----------|-------|---|-------------|
| Document Fragments | 224 | 27.1% | N/A (not real issues) |
| XML Namespace Issues | 186 | 22.5% | N/A (malformed samples) |
| **Converter Bugs** | **137** | **32.9%** | ✅ **HIGH - Fix ASAP** |
| Missing Features (CO type) | 37 | 8.9% | ✅ Medium |
| Design Decisions | 85 | 20.4% | ⚠️ Decide |
| Data Quality Issues | 95 | 22.8% | ⚠️ Accept or Lenient |
| Needs Investigation | 62 | 14.9% | ❓ Research |

## Documentation

📋 **[BUGS_AND_ISSUES.md](BUGS_AND_ISSUES.md)** - Detailed bug tracker with test improvements for each issue
- All 416 real issues documented one-by-one
- Root cause analysis
- Test cases to add for each bug
- Suggested fixes with code examples
- Priority ordering by impact

📖 **[STRESS_TEST_GUIDE.md](STRESS_TEST_GUIDE.md)** - Complete user guide for running stress tests
- How to run tests (excluding fragments)
- Command-line options
- Interpreting results
- Best practices
- Troubleshooting

📊 **[STRESS_TEST_REPORT.md](STRESS_TEST_REPORT.md)** - Latest test run analysis
- Executive summary
- Error distribution
- Sample errors by category
- Priority fix recommendations

## Priority Fixes (Recommended Order)

### 1. BUG-001: Composition.resource_type AttributeError
**Impact:** 104 files (25% of real issues)
```python
# Test to add: tests/integration/test_composition_resource_type.py
# Fix: Ensure Composition properly sets resourceType field
```

### 2. BUG-004: RelatedPersonConverter missing method
**Impact:** Many files with informant/related persons
```python
# Test to add: tests/unit/converters/test_related_person.py
# Fix: Add _convert_oid_to_uri() method or use shared utility
```

### 3. BUG-002: Missing timezone on datetime fields
**Impact:** 33 files (FHIR validation errors)
```python
# Test to add: tests/unit/converters/test_datetime_timezone.py
# Fix: Reduce precision to date-only for timestamps without timezone
```

### 4. FEATURE-001: Add CO (Coded Ordinal) data type
**Impact:** 37 files (8.9%)
```python
# Test to add: tests/unit/ccda/test_co_datatype.py
# Fix: Add CO model and parser (extends CE)
```

### 5. DESIGN-001: Location name fallback strategies
**Impact:** 71 files (17.1%)
```python
# Test to add: tests/integration/test_location_without_name.py
# Fix: Add graceful fallbacks (address → ID → "Unknown Location")
```

## Tools

### stress_test.py
Main test runner - converts C-CDA files and validates FHIR output

**Usage:**
```bash
# Standard test (exclude fragments)
uv run python stress_test.py --onc-only

# Quick test (20 files)
uv run python stress_test.py --onc-only --limit 20

# Full test (all 828)
uv run python stress_test.py --output full_test.json
```

**Tests:**
- ✅ C-CDA to FHIR conversion
- ✅ FHIR Bundle validation
- ✅ US Core profile compliance
- ✅ CCDA on FHIR mapping compliance
- ✅ Performance metrics

### analyze_results.py
Results analyzer and report generator

**Usage:**
```bash
# Generate markdown report
uv run python analyze_results.py results.json --output REPORT.md

# Print to terminal
uv run python analyze_results.py results.json
```

**Output:**
- Executive summary
- Error categorization
- US Core compliance metrics
- CCDA on FHIR mapping metrics
- Priority fix recommendations

### filter_real_issues.py
Filters out document fragments and namespace issues to show real conversion issues

**Usage:**
```bash
cd stress_test
uv run python filter_real_issues.py
```

**Output:**
- Real issues count (excluding fragments/namespace)
- Solvability categorization
- Success rate projections
- Sample errors by category

## Test Data

### ONC Certification Samples (382 files)
**Source:** https://github.com/jddamore/ccda-samples
**Description:** Real-world C-CDA exports from 52 certified EHR systems
**Use Case:** Best indicator of production readiness
**Location:** `stress_test/ccda-samples/`

### HL7 Official Examples (446 files)
**Source:** https://github.com/HL7/C-CDA-Examples
**Description:** Official C-CDA examples from HL7
**Use Case:** Edge cases and specific template patterns
**Note:** ~50% are document fragments (expected to fail)
**Location:** `stress_test/C-CDA-Examples/`

## Success Rate Projections

| Scenario | Success Rate | Files Passing |
|----------|--------------|---------------|
| **Current (baseline)** | 0% | 0/828 |
| Fix all bugs | 29.2% | 242/828 |
| + Add CO type | 37.1% | 307/828 |
| + Graceful degradation | 47.3% | 392/828 |
| + Lenient mode | 56.3% | 466/828 |
| + After investigation | **100%*** | 416/828† |

*Of real issues only
†50.2% absolute success rate

## Key Metrics Tracked

### Conversion Metrics
- Success/failure count and rate
- Average conversion time
- Total FHIR resources created
- Error distribution by type

### FHIR Resource Distribution
- Count by resource type
- Patient, Composition, Condition, AllergyIntolerance, etc.

### US Core Compliance
- Patient completeness (name, identifier, gender, birthDate)
- Condition fields (code, category, subject)
- AllergyIntolerance fields (code, patient, clinicalStatus)
- Observation fields (code, status, category)

### CCDA on FHIR Mapping
- Composition creation rate
- Average sections per document
- Provenance tracking
- Narrative text preservation

## Example Workflow

### 1. Run Initial Test
```bash
uv run python stress_test.py --onc-only --output baseline.json
# Success rate: 0%
```

### 2. Review Issues
```bash
uv run python filter_real_issues.py
# Shows: 137 bugs (high priority), 37 missing features
```

### 3. Fix Top Bug
```python
# Fix BUG-001: Composition.resource_type
# Add test: tests/integration/test_composition_resource_type.py
# Update converter to properly set resourceType
```

### 4. Re-Test
```bash
uv run python stress_test.py --onc-only --output after_bug001.json
# Expected improvement: +104 files (to ~12.5% success rate)
```

### 5. Continue Fixing
```bash
# Repeat for BUG-004, BUG-002, FEATURE-001, etc.
# Track improvement after each fix
```

### 6. Generate Final Report
```bash
uv run python analyze_results.py after_all_fixes.json --output FINAL_REPORT.md
# Target: 60-80% success rate on ONC samples
```

## CI Integration

Add to GitHub Actions:

```yaml
# .github/workflows/stress-test.yml
- name: Run stress test
  run: |
    uv run python stress_test/stress_test.py \
      --onc-only \
      --limit 100 \
      --output ci_results.json

- name: Check success rate threshold
  run: |
    RATE=$(jq -r '.summary.success_rate' stress_test/ci_results.json | sed 's/%//')
    if (( $(echo "$RATE < 25" | bc -l) )); then
      echo "Error: Success rate below 25%"
      exit 1
    fi
```

## File Structure

```
stress_test/
├── README.md                    # This file
├── BUGS_AND_ISSUES.md           # Detailed bug tracker
├── STRESS_TEST_GUIDE.md         # User guide
├── STRESS_TEST_REPORT.md        # Latest analysis report
│
├── stress_test.py               # Main test runner
├── analyze_results.py           # Results analyzer
├── filter_real_issues.py        # Real issue filter
│
├── stress_test_results.json     # Test results (generated)
├── stress_test_all_samples.json # Full test results
│
├── ccda-samples/                # ONC samples (382 files)
│   ├── 360 Oncology/
│   ├── Allscripts/
│   ├── Amrita/
│   └── .../
│
└── C-CDA-Examples/              # HL7 examples (446 files)
    ├── Allergies/
    ├── Documents/
    └── .../
```

## Next Steps

1. **Review [BUGS_AND_ISSUES.md](BUGS_AND_ISSUES.md)** for detailed bug analysis
2. **Read [STRESS_TEST_GUIDE.md](STRESS_TEST_GUIDE.md)** for usage instructions
3. **Fix high-priority bugs** in recommended order
4. **Add tests** for each bug as specified
5. **Re-run stress tests** after each fix
6. **Track progress** toward target success rate

## Support

- Bug tracker: See BUGS_AND_ISSUES.md
- User guide: See STRESS_TEST_GUIDE.md
- Latest results: See STRESS_TEST_REPORT.md

---

**Last Updated:** 2025-12-23
**Test Data Version:** ONC Certification Samples + HL7 C-CDA Examples (828 files)
**Baseline Success Rate:** 0% (before fixes)
**Target Success Rate:** 60-80% (after high-priority fixes)
