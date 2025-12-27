# C-CDA to FHIR Stress Test - User Guide

Comprehensive guide for running stress tests on the C-CDA to FHIR converter.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Test Suite](#understanding-the-test-suite)
3. [Running Tests](#running-tests)
4. [Analyzing Results](#analyzing-results)
5. [Advanced Usage](#advanced-usage)
6. [Interpreting Metrics](#interpreting-metrics)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Run stress test on ONC samples (real-world EHR data, excluding fragments):

```bash
cd /path/to/c-cda-to-fhir
uv run python stress_test/stress_test.py --onc-only --output results.json
```

### Analyze results:

```bash
uv run python stress_test/analyze_results.py stress_test/results.json
```

---

## Understanding the Test Suite

### Test Components

The stress test suite consists of:

1. **stress_test.py** - Main test runner
2. **analyze_results.py** - Results analyzer and report generator
3. **filter_real_issues.py** - Filters out document fragments and namespace issues
4. **Sample data directories:**
   - `ccda-samples/` - 382 ONC certification samples (real-world EHR data)
   - `C-CDA-Examples/` - 446 HL7 official examples (many are fragments)

### What Gets Tested

For each C-CDA file, the stress test:

1. ✅ **Converts** C-CDA XML to FHIR Bundle
2. ✅ **Validates** FHIR Bundle against Pydantic models
3. ✅ **Checks** US Core profile compliance:
   - Patient completeness (name, identifier, gender, birthDate)
   - Condition required fields (code, category, subject)
   - AllergyIntolerance required fields (code, patient, clinicalStatus)
   - Observation required fields (code, status, category)
4. ✅ **Checks** CCDA on FHIR mapping compliance:
   - Composition resources created
   - Section preservation
   - Provenance tracking
   - Narrative text preservation
5. ✅ **Measures** conversion time and resource counts

### Success Criteria

A file passes if:
- Converts without exceptions
- Produces valid FHIR Bundle
- All resources pass Pydantic validation
- References are resolvable

---

## Running Tests

### Basic Usage

```bash
# Run on all samples (828 files, ~5 minutes)
uv run python stress_test/stress_test.py

# Run on ONC samples only (382 files, excludes HL7 fragments)
uv run python stress_test/stress_test.py --onc-only

# Run on limited sample (for quick testing)
uv run python stress_test/stress_test.py --limit 50

# Specify output file
uv run python stress_test/stress_test.py --output my_results.json
```

### Recommended Test Scenarios

#### 1. Real-World EHR Data (Recommended for Production Readiness)

```bash
# ONC certification samples - real-world EHR output
uv run python stress_test/stress_test.py \
    --onc-only \
    --output stress_test_onc.json
```

**Why:** These are actual exports from certified EHR systems. Best indicator of production readiness.

#### 2. Quick Smoke Test

```bash
# Test first 20 ONC samples
uv run python stress_test/stress_test.py \
    --onc-only \
    --limit 20 \
    --output quick_test.json
```

**Why:** Fast feedback during development (completes in ~10 seconds).

#### 3. Full Comprehensive Test

```bash
# All 828 samples (ONC + HL7)
uv run python stress_test/stress_test.py \
    --output full_test.json
```

**Why:** Tests edge cases and unusual patterns. Note: ~60% will fail due to document fragments.

#### 4. After Bug Fixes

```bash
# Re-run to measure improvement
uv run python stress_test/stress_test.py \
    --onc-only \
    --output after_fix.json

# Compare with baseline
diff <(jq '.summary' stress_test_onc.json) \
     <(jq '.summary' after_fix.json)
```

### Command-Line Options

```
usage: stress_test.py [-h] [--limit LIMIT] [--output OUTPUT] [--onc-only]

options:
  -h, --help       Show help message
  --limit LIMIT    Limit number of files to process (default: all)
  --output OUTPUT  Output JSON file (default: stress_test_results.json)
  --onc-only       Only test ONC certification samples, skip HL7 examples
                   (recommended to exclude document fragments)
```

---

## Analyzing Results

### Generate Analysis Report

```bash
# Generate markdown report
uv run python stress_test/analyze_results.py \
    stress_test/results.json \
    --output REPORT.md

# View in terminal
uv run python stress_test/analyze_results.py stress_test/results.json
```

### Filter Real Issues

```bash
# Exclude document fragments and namespace issues
cd stress_test
uv run python filter_real_issues.py
```

This shows:
- Real issues (excluding fragments/namespace)
- Solvability categorization
- Projected success rates after fixes

### Key Metrics in JSON Output

```json
{
  "summary": {
    "total_files": 828,
    "successful": 0,
    "failed": 828,
    "success_rate": "0.0%",
    "total_resources_created": 0,
    "avg_conversion_time_ms": "4.5"
  },
  "resource_distribution": {
    "Patient": 123,
    "Condition": 456,
    ...
  },
  "error_distribution": {
    "MalformedXMLError": 507,
    "ValueError": 140,
    ...
  },
  "us_core_compliance": {
    "patient_completeness": { ... },
    "condition_compliance": { ... },
    ...
  },
  "ccda_fhir_mapping": { ... },
  "failed_files": [
    {
      "file": "path/to/file.xml",
      "error_type": "ValueError",
      "error_message": "..."
    },
    ...
  ]
}
```

---

## Advanced Usage

### Running Tests Programmatically

```python
from pathlib import Path
from stress_test import StressTestRunner

# Create runner
base_dir = Path("stress_test")
runner = StressTestRunner(base_dir)

# Run with options
report = runner.run(limit=100, onc_only=True)

# Access results
print(f"Success rate: {report['summary']['success_rate']}")
print(f"Total resources: {report['summary']['total_resources_created']}")

# Iterate through failures
for failure in report['failed_files']:
    print(f"{failure['file']}: {failure['error_type']}")
```

### Custom Test Sets

```python
# Test specific files
runner = StressTestRunner(base_dir)
runner.results = []  # Clear results

specific_files = [
    Path("ccda-samples/vendor1/sample1.xml"),
    Path("ccda-samples/vendor2/sample2.xml"),
]

for file_path in specific_files:
    result = runner.convert_file(file_path)
    runner.results.append(result)

report = runner.generate_report()
```

### Adding Custom Validations

```python
# In stress_test.py, add to validate_bundle() method

def validate_bundle(self, bundle: Bundle) -> Dict[str, Any]:
    validation = { ... }  # existing validations

    # Add custom validation
    for entry in bundle.entry:
        resource = entry.resource

        # Custom check: All Observations must have effective[x]
        if resource.resource_type == "Observation":
            if not (resource.effective_date_time or
                    resource.effective_period or
                    resource.effective_instant):
                validation["observations_missing_effective"] += 1

    return validation
```

---

## Interpreting Metrics

### Success Rate

**Formula:** `(successful conversions / total files) × 100`

**What it means:**
- **0-20%:** Significant compatibility issues
- **20-50%:** Moderate compatibility, some edge cases
- **50-80%:** Good compatibility, minor issues
- **80-95%:** Excellent compatibility
- **95-100%:** Production ready

**Context matters:**
- ONC samples: Lower rate expected (real-world data has edge cases)
- Clean test fixtures: Should be 90%+ success rate

### Error Distribution

Shows categories of failures:

```
MalformedXMLError: 507 files  → XML parsing issues
ValueError: 140 files         → Missing required C-CDA fields
AttributeError: 104 files     → Converter bugs
ValidationError: 40 files     → FHIR validation failures
```

**Action items:**
1. Focus on highest count errors first
2. Check if errors are converter bugs vs. bad input data
3. See BUGS_AND_ISSUES.md for detailed analysis

### US Core Compliance

Measures FHIR resource quality:

```python
{
  "patient_completeness": {
    "has_patient": 150,      # 150 bundles have Patient resource
    "has_name": 148,         # 148 of those have name (98.7%)
    "has_identifier": 150,   # All have identifier (100%)
    "has_gender": 145,       # 145 have gender (96.7%)
    "has_birthdate": 147     # 147 have birthDate (98.0%)
  }
}
```

**Good targets:**
- Essential fields (identifier, name): 95%+
- Important fields (gender, birthDate): 90%+
- Optional fields: 70%+

### CCDA on FHIR Mapping

Measures conversion completeness:

```python
{
  "has_composition": 150,           # All successful conversions
  "avg_sections_per_doc": 8.3,     # Average sections preserved
  "total_provenance": 245,          # Provenance resources created
  "has_narrative": 142              # 142 have narrative text (94.7%)
}
```

**Good targets:**
- Composition created: 100%
- Avg sections: 5-15 (depends on document type)
- Narrative preservation: 80%+
- Provenance tracking: 50%+ (if authored info present)

### Resource Distribution

Shows FHIR resources created:

```
Patient: 150
Composition: 150
Condition: 234
AllergyIntolerance: 187
MedicationRequest: 312
Procedure: 89
Observation: 567
```

**Sanity checks:**
- Patient count ≈ successful conversions
- Composition count = Patient count
- Clinical resources > 0 for non-empty documents

---

## Interpreting Results by File Type

### Document Fragments (HL7 Examples)

**Expected:** ~50% are fragments, will fail with:
```
Root element must be 'ClinicalDocument', got 'section'
```

**Action:** Exclude with `--onc-only` flag

### Namespace Issues

**Expected:** ~24% of HL7 examples have namespace issues:
```
Namespace prefix xsi for type on value is not defined
```

**Action:** These are malformed sample files, not converter issues

### ONC Certification Samples

**Expected:**
- Real-world EHR data
- May have missing optional fields
- May have vendor-specific quirks
- Success rate: 20-40% initially, 60-80% after fixes

**Action:** Focus optimization efforts here

---

## Troubleshooting

### Issue: All tests fail immediately

**Symptom:**
```
ImportError: cannot import name 'convert_document'
```

**Solution:**
```bash
# Ensure you're in the project root
cd /path/to/c-cda-to-fhir

# Run with uv
uv run python stress_test/stress_test.py
```

### Issue: Out of memory

**Symptom:** Python crashes during large test runs

**Solution:**
```bash
# Run in batches
for i in {1..8}; do
  uv run python stress_test/stress_test.py \
    --limit 100 \
    --output batch_$i.json
done

# Merge results (manual or script)
```

### Issue: Tests run very slowly

**Symptom:** Takes >10 minutes for 100 files

**Causes:**
- Debug logging enabled
- Running on slow storage
- Large/complex documents

**Solution:**
```bash
# Disable verbose logging
export CCDA_LOG_LEVEL=ERROR

# Run on SSD if possible
# Exclude complex documents initially
```

### Issue: Can't find sample files

**Symptom:**
```
Total files to process: 0
```

**Solution:**
```bash
# Download sample files (if not already done)
cd stress_test
git clone --depth 1 https://github.com/jddamore/ccda-samples.git
git clone --depth 1 https://github.com/HL7/C-CDA-Examples.git
```

### Issue: Results show 0% success rate

**Expected for initial run.** See success rate projections:

1. Many samples are fragments or malformed → Exclude with `--onc-only`
2. Real bugs exist → See BUGS_AND_ISSUES.md for fixes
3. Design decisions needed → Review DESIGN-001, DESIGN-002, etc.

**Action:**
```bash
# Run filtered analysis
cd stress_test
uv run python filter_real_issues.py
```

---

## Continuous Integration

### Adding to CI Pipeline

```yaml
# .github/workflows/stress-test.yml
name: Stress Test

on: [push, pull_request]

jobs:
  stress-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Download test samples
        run: |
          cd stress_test
          git clone --depth 1 https://github.com/jddamore/ccda-samples.git

      - name: Run stress test
        run: |
          uv sync
          uv run python stress_test/stress_test.py \
            --onc-only \
            --limit 100 \
            --output stress_test_ci.json

      - name: Check success rate
        run: |
          SUCCESS_RATE=$(jq -r '.summary.success_rate' stress_test/stress_test_ci.json)
          echo "Success rate: $SUCCESS_RATE"

          # Fail if success rate drops below threshold
          RATE_NUM=$(echo $SUCCESS_RATE | sed 's/%//')
          if (( $(echo "$RATE_NUM < 25" | bc -l) )); then
            echo "Error: Success rate below 25%"
            exit 1
          fi

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: stress-test-results
          path: stress_test/stress_test_ci.json
```

---

## Best Practices

### 1. Establish Baseline

Before making changes:
```bash
# Run full test and save baseline
uv run python stress_test/stress_test.py \
    --onc-only \
    --output baseline.json

# Note success rate and key metrics
```

### 2. Test After Each Fix

After fixing a bug:
```bash
# Run same test
uv run python stress_test/stress_test.py \
    --onc-only \
    --output after_fix_123.json

# Compare
python -c "
import json
baseline = json.load(open('baseline.json'))
current = json.load(open('after_fix_123.json'))
print(f\"Baseline: {baseline['summary']['successful']} successful\")
print(f\"Current:  {current['summary']['successful']} successful\")
print(f\"Improvement: {current['summary']['successful'] - baseline['summary']['successful']} files\")
"
```

### 3. Focus on High-Impact Issues

Prioritize fixes by impact:
```bash
# Run filtered analysis to see impact
cd stress_test
uv run python filter_real_issues.py > impact_analysis.txt

# Fix bugs in this order:
# 1. Highest count issues
# 2. Blocking bugs (prevent other conversions)
# 3. FHIR compliance issues
# 4. Missing features
```

### 4. Test Edge Cases

Add failing samples to integration tests:
```bash
# Copy failing file to test fixtures
cp stress_test/ccda-samples/vendor/problematic.xml \
   tests/integration/fixtures/ccda/

# Create test
# tests/integration/test_vendor_edge_cases.py
```

### 5. Monitor Trends

Track success rate over time:
```bash
# After each sprint/milestone
echo "$(date),$(jq -r '.summary.success_rate' stress_test_latest.json)" \
  >> stress_test_history.csv

# Plot trends (requires gnuplot or python)
python plot_trends.py stress_test_history.csv
```

---

## Quick Reference

### Common Commands

```bash
# Standard test run
uv run python stress_test/stress_test.py --onc-only

# Quick test (20 files)
uv run python stress_test/stress_test.py --onc-only --limit 20

# Generate report
uv run python stress_test/analyze_results.py stress_test_results.json

# Filter real issues
cd stress_test && uv run python filter_real_issues.py

# View specific error types
jq '.failed_files[] | select(.error_type=="ValueError")' \
  stress_test_results.json | less

# Count errors by type
jq '.error_distribution' stress_test_results.json

# List all failed files
jq -r '.failed_files[].file' stress_test_results.json > failed_files.txt
```

### Success Rate Targets

| Milestone | Target | Description |
|-----------|--------|-------------|
| Initial | 0-10% | Expected with real-world data |
| Bug fixes | 25-35% | After fixing critical bugs |
| Features added | 40-50% | After adding missing types |
| Production ready | 60-80% | With graceful degradation |
| Excellent | 80-95% | With lenient mode |

Remember: 100% success rate unrealistic with wild real-world data. Focus on:
- High success rate on clean, conformant C-CDA
- Graceful handling of edge cases
- Clear error messages for invalid input

---

## Getting Help

1. **Check BUGS_AND_ISSUES.md** for known issues and fixes
2. **Run filter_real_issues.py** to understand what's failing
3. **Review failed file directly:**
   ```bash
   # Find a specific failed file
   FILE=$(jq -r '.failed_files[0].file' stress_test_results.json)

   # Try to convert it directly
   python -c "
   from ccda_to_fhir import convert_document
   with open('stress_test/$FILE') as f:
       print(convert_document(f.read()))
   "
   ```

4. **Enable debug logging:**
   ```bash
   export CCDA_LOG_LEVEL=DEBUG
   uv run python stress_test/stress_test.py --limit 1
   ```

---

## Appendix: File Structure

```
stress_test/
├── stress_test.py           # Main test runner
├── analyze_results.py       # Results analyzer
├── filter_real_issues.py    # Real issue filter
├── BUGS_AND_ISSUES.md       # Detailed bug tracker (this file)
├── STRESS_TEST_GUIDE.md     # This guide
├── STRESS_TEST_REPORT.md    # Generated analysis report
├── stress_test_results.json # Test results (generated)
├── ccda-samples/            # ONC certification samples (382 files)
│   ├── 360 Oncology/
│   ├── Allscripts/
│   ├── Amrita/
│   └── .../
└── C-CDA-Examples/          # HL7 official examples (446 files)
    ├── Allergies/
    ├── Documents/
    ├── Problems/
    └── .../
```

---

**Last Updated:** 2025-12-23
**Version:** 1.0
**Tested With:** Python 3.12, uv 0.5+
