# E2E Test Mapping Coverage Analysis

**Date:** 2025-12-29
**Purpose:** Analyze which documented C-CDA→FHIR mappings are validated by E2E tests

---

## Executive Summary

The converter has **26 documented resource mappings** in `docs/mapping/`. Current E2E tests validate **7 of 26 mappings (27%)** across 4 vendor samples.

**E2E Test Coverage:** 38 tests across 4 vendors (Athena, NIST, Cerner, Epic)

**Coverage Status:**
- ✅ **Well-tested:** Patient, Condition, AllergyIntolerance, Composition, Bundle
- ⚠️ **Partially tested:** Observation (Epic only), MedicationStatement (Athena only)
- ❌ **Not E2E tested:** 19 resource types (73%)

---

## Documented Mappings vs E2E Test Coverage

| # | Mapping Document | FHIR Resource | E2E Coverage | Vendors Testing | Notes |
|---|------------------|---------------|--------------|-----------------|-------|
| 01 | patient.md | Patient | ✅ **FULL** | Athena, NIST, Cerner, Epic | Demographics, name, DOB, gender, race, ethnicity |
| 02 | condition.md | Condition | ✅ **FULL** | Athena, NIST, Cerner, Epic | SNOMED codes, ICD-10, code.text, clinical status |
| 03 | allergy-intolerance.md | AllergyIntolerance | ✅ **FULL** | Athena, NIST, Cerner, Epic | RxNorm codes, code.text, reactions, severity, negation |
| 04 | observation.md | Observation | ⚠️ **PARTIAL** | Epic only | Lab results validated, but not vital signs, social history |
| 05 | procedure.md | Procedure | ❌ **NONE** | - | Not validated by E2E tests |
| 06 | immunization.md | Immunization | ❌ **NONE** | - | Not validated by E2E tests |
| 07 | medication-request.md | MedicationRequest | ❌ **NONE** | - | Not validated by E2E tests |
| 08 | encounter.md | Encounter | ❌ **NONE** | - | Not validated by E2E tests |
| 09 | participations.md | Practitioner, PractitionerRole | ❌ **NONE** | - | Author/performer not validated |
| 10 | notes.md | DocumentReference | ❌ **NONE** | - | Not validated by E2E tests |
| 11 | social-history.md | Observation (social-history) | ❌ **NONE** | - | Not validated by E2E tests |
| 12 | vital-signs.md | Observation (vital-signs) | ❌ **NONE** | - | Not validated by E2E tests |
| 13 | goal.md | Goal | ❌ **NONE** | - | Not validated by E2E tests |
| 14 | careplan.md | CarePlan | ❌ **NONE** | - | Not validated by E2E tests |
| 15 | medication-dispense.md | MedicationDispense | ❌ **NONE** | - | Not validated by E2E tests |
| 16 | location.md | Location | ❌ **NONE** | - | Not validated by E2E tests |
| 17 | careteam.md | CareTeam | ❌ **NONE** | - | Not validated by E2E tests |
| 18 | service-request.md | ServiceRequest | ❌ **NONE** | - | Not validated by E2E tests |
| 19 | composition.md | Composition | ✅ **FULL** | Athena, NIST, Cerner, Epic | Title, type, status, date, resource type |
| 20 | bundle.md | Bundle | ✅ **FULL** | Athena, NIST, Cerner, Epic | Structure, reference integrity, sections |
| 21 | diagnostic-report.md | DiagnosticReport | ❌ **NONE** | - | Not validated by E2E tests |
| 22 | device.md | Device | ❌ **NONE** | - | Not validated by E2E tests |
| 23 | medication.md | Medication | ❌ **NONE** | - | Not validated by E2E tests |
| 24 | medication-statement.md | MedicationStatement | ⚠️ **PARTIAL** | Athena only | RxNorm codes, status, dosage (needs broader testing) |
| 25 | provenance.md | Provenance | ❌ **NONE** | - | Not validated by E2E tests |
| 26 | document-reference.md | DocumentReference | ❌ **NONE** | - | Not validated by E2E tests |

---

## Current E2E Test Coverage Breakdown

### Athena Health CCD (10 tests)
1. ✅ Patient demographics (name, DOB, gender, race, ethnicity)
2. ✅ Condition: Acute low back pain (SNOMED 278862001 + ICD-10)
3. ✅ Condition: Moderate dementia (SNOMED 428351000124105)
4. ✅ AllergyIntolerance: Strawberry (RxNorm 892484)
5. ✅ AllergyIntolerance: No known drug allergies (negated)
6. ✅ MedicationStatement: Donepezil (active)
7. ✅ MedicationStatement: Cephalexin (aborted)
8. ✅ Composition metadata
9. ✅ Bundle reference integrity
10. ✅ Bundle expected sections

**Coverage:** Patient, Condition, AllergyIntolerance, MedicationStatement, Composition, Bundle

---

### NIST Ambulatory CCD (10 tests)
1. ✅ Patient demographics (name, DOB, gender, race, ethnicity)
2. ✅ Condition: Pneumonia (SNOMED 233604007, resolved)
3. ✅ Condition: Asthma (SNOMED 195967001, active)
4. ✅ AllergyIntolerance: Penicillin with hives (RxNorm 7982)
5. ✅ AllergyIntolerance: Codeine with shortness of breath (RxNorm 2670, moderate severity)
6. ✅ AllergyIntolerance: Aspirin with hives (RxNorm 1191)
7. ✅ MedicationStatement: Albuterol inhalant (RxNorm 573621, completed)
8. ✅ Composition metadata
9. ✅ Bundle reference integrity
10. ✅ Bundle expected sections

**Coverage:** Patient, Condition, AllergyIntolerance, MedicationStatement, Composition, Bundle

---

### Cerner TOC (8 tests)
1. ✅ Patient demographics (name, DOB, gender, race)
2. ✅ Condition: Angina (SNOMED 194828000, active)
3. ✅ Condition: Diabetes Type 2 (SNOMED 44054006, active)
4. ✅ Condition: Hypercholesterolemia (SNOMED 13644009)
5. ✅ AllergyIntolerance: Codeine with Nausea (RxNorm 2670)
6. ✅ AllergyIntolerance: Penicillin with Weal/Hives (RxNorm 7980)
7. ✅ Composition metadata
8. ✅ Bundle reference integrity

**Coverage:** Patient, Condition, AllergyIntolerance, Composition, Bundle

---

### Partners/Epic CCD (10 tests)
1. ✅ Patient demographics (name, DOB, gender)
2. ✅ Condition: Community acquired pneumonia (SNOMED 385093006)
3. ✅ Condition: Asthma (SNOMED 195967001)
4. ✅ Condition: Multiple problems validated
5. ✅ AllergyIntolerance: Penicillins (RxNorm 000476)
6. ✅ AllergyIntolerance: Codeine (RxNorm 2670)
7. ✅ AllergyIntolerance: Aspirin (RxNorm 1191)
8. ✅ Composition metadata
9. ✅ Bundle reference integrity
10. ✅ Observation: Lab results (22+ observations)

**Coverage:** Patient, Condition, AllergyIntolerance, Observation, Composition, Bundle

---

## Coverage Gaps - Critical Missing Tests

### High Priority (Common in EHR samples)

1. **Procedure** 🔴 **HIGH PRIORITY**
   - **Why important:** Procedures are core clinical data (surgeries, interventions)
   - **What to test:** CPT codes, SNOMED codes, status, performer, date
   - **Likely in samples:** Athena, NIST, Cerner, Epic all typically include procedures

2. **Immunization** 🔴 **HIGH PRIORITY**
   - **Why important:** Vaccines are critical for public health tracking
   - **What to test:** CVX codes, lot numbers, route, site, status, negation
   - **Likely in samples:** NIST, possibly Athena/Cerner

3. **Encounter** 🔴 **HIGH PRIORITY**
   - **Why important:** Context for all clinical activities
   - **What to test:** Encounter class, type, period, location, participant
   - **Likely in samples:** All vendors include encounter context

4. **Vital Signs** 🟠 **MEDIUM PRIORITY**
   - **Why important:** Blood pressure, temperature, height, weight are fundamental
   - **What to test:** LOINC codes, value+unit, interpretation, category=vital-signs
   - **Likely in samples:** All vendors include vital signs

5. **DiagnosticReport** 🟠 **MEDIUM PRIORITY**
   - **Why important:** Lab panels and imaging reports
   - **What to test:** LOINC codes, status, results references, issued date
   - **Likely in samples:** Epic has extensive lab results

6. **Practitioner/PractitionerRole** 🟠 **MEDIUM PRIORITY**
   - **Why important:** Author and performer tracking
   - **What to test:** NPI, name, specialty, organization
   - **Likely in samples:** All vendors include authoring clinician

### Medium Priority (Less common but important)

7. **Goal** 🟡 **MEDIUM PRIORITY**
   - **Why important:** Care planning and patient goals
   - **What to test:** Description, status, target dates, achievement status
   - **Likely in samples:** May be sparse in samples

8. **CarePlan** 🟡 **MEDIUM PRIORITY**
   - **Why important:** Treatment plans and care coordination
   - **What to test:** Status, intent, activities, goals
   - **Likely in samples:** May be sparse in samples

9. **CareTeam** 🟡 **LOW PRIORITY**
   - **Why important:** Care coordination
   - **What to test:** Members, roles, period
   - **Likely in samples:** Cerner TOC may include

10. **ServiceRequest** 🟡 **LOW PRIORITY**
    - **Why important:** Orders and referrals
    - **What to test:** Code, status, intent, subject
    - **Likely in samples:** May be sparse

### Lower Priority (Specialized or less common)

11. **Social History** 🔵 **LOW PRIORITY**
    - Smoking status, alcohol use, etc.
    - Likely in NIST sample

12. **MedicationRequest** 🔵 **LOW PRIORITY**
    - Prescriptions vs MedicationStatement
    - May overlap with MedicationStatement testing

13. **MedicationDispense** 🔵 **LOW PRIORITY**
    - Pharmacy dispenses
    - Rarely in C-CDA samples

14. **Device** 🔵 **LOW PRIORITY**
    - Implants, medical equipment
    - Rarely in C-CDA samples

15. **Location** 🔵 **LOW PRIORITY**
    - Healthcare facilities
    - May be in Encounter references

16. **Provenance** 🔵 **LOW PRIORITY**
    - Audit trail
    - Generated resource, not direct mapping

17. **DocumentReference** 🔵 **LOW PRIORITY**
    - Clinical notes
    - May overlap with Composition

---

## Recommended E2E Test Additions

### Phase 1: Critical Core Clinical Data (High Priority)

Add to **all 4 vendor tests** where data exists:

1. **Procedure validation**
   - At least 1 procedure with CPT/SNOMED code
   - Status (completed, in-progress)
   - Performer reference
   - Performed date/period

2. **Encounter validation**
   - Encounter type (office visit, inpatient, emergency)
   - Period (start/end)
   - Location reference
   - Participant (attending physician)

3. **Immunization validation**
   - At least 1 immunization with CVX code
   - Occurrence date
   - Status (completed, not-done)
   - Route and site

4. **Vital Signs validation**
   - Blood pressure (systolic/diastolic)
   - Temperature, height, weight
   - LOINC codes
   - category = "vital-signs"

5. **Practitioner/PractitionerRole validation**
   - Document author has Practitioner resource
   - NPI identifier present
   - Name matches C-CDA author

### Phase 2: Extended Clinical Content (Medium Priority)

Add where data is available:

6. **DiagnosticReport validation** (Epic has extensive labs)
   - Lab panel with LOINC code
   - Status (final, preliminary)
   - Results references to Observations
   - Issued date

7. **Goal validation** (if present in samples)
   - Goal description
   - Status (active, achieved)
   - Target dates

8. **CarePlan validation** (if present)
   - Status (active, completed)
   - Activities and goals

### Phase 3: Specialized Content (Lower Priority)

9. **Social History** (NIST likely has)
   - Smoking status
   - Alcohol use

10. **MedicationRequest** (if distinct from MedicationStatement in samples)
    - Prescription intent vs administration

---

## Implementation Strategy

### Step 1: Inventory Existing Sample Data
For each vendor sample, analyze what resources are actually present:
```bash
# Convert sample and inspect bundle
uv run python -c "
from ccda_to_fhir.convert import convert_document
from pathlib import Path
from collections import Counter

sample = Path('tests/integration/fixtures/documents/athena_ccd.xml')
xml = sample.read_text()
result = convert_document(xml)
bundle = result['bundle']

# Count resource types
resource_types = Counter(entry['resource']['resourceType'] for entry in bundle['entry'])
for rtype, count in sorted(resource_types.items()):
    print(f'{rtype}: {count}')
"
```

### Step 2: Prioritize by Data Availability
- Add tests only for resources that exist in samples
- Start with high-priority resources (Procedure, Encounter, Immunization)
- Validate exact codes/values from C-CDA XML

### Step 3: Implement Tests Incrementally
- Add 3-5 tests per vendor per phase
- Validate EXACT values from source XML (like current tests)
- Ensure tests are resilient (not brittle)

### Step 4: Document Coverage
- Update this document after each phase
- Track coverage percentage improvement
- Identify remaining gaps

---

## Coverage Metrics

### Current Coverage: 27% (7/26 mappings)

**Target Goals:**
- **Phase 1 Complete:** 50% coverage (13/26 mappings) - Add 6 high-priority resources
- **Phase 2 Complete:** 65% coverage (17/26 mappings) - Add 4 medium-priority resources
- **Phase 3 Complete:** 77% coverage (20/26 mappings) - Add 3 specialized resources

**Realistic Goal:** 75-80% coverage
- Some mappings (Provenance, DocumentReference, Device) may have sparse data in samples
- Focus on core clinical content that's consistently present

---

## Next Steps

1. ✅ **COMPLETED:** Create mapping coverage analysis document
2. **NEXT:** Run resource inventory on all 4 vendor samples to identify available data
3. **NEXT:** Add Procedure validation tests (Phase 1)
4. **NEXT:** Add Encounter validation tests (Phase 1)
5. **NEXT:** Add Immunization validation tests (Phase 1)
6. **NEXT:** Add Vital Signs validation tests (Phase 1)
7. **NEXT:** Add Practitioner validation tests (Phase 1)
8. **NEXT:** Update coverage metrics after Phase 1

---

## References

- Mapping Documentation: `docs/mapping/00-overview.md`
- E2E Test Files:
  - `tests/integration/test_athena_e2e_detailed.py`
  - `tests/integration/test_nist_e2e_detailed.py`
  - `tests/integration/test_cerner_e2e_detailed.py`
  - `tests/integration/test_epic_e2e_detailed.py`
- E2E Findings: `stress_test/E2E_TEST_FINDINGS.md`
