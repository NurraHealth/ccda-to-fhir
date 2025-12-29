# Resource Inventory - Vendor Samples

**Date:** 2025-12-29
**Purpose:** Catalog what FHIR resources are actually present in each vendor sample

---

## Resource Counts by Vendor

### Athena Health CCD
```
AllergyIntolerance: 2
Composition: 1
Condition: 5
Device: 1
DocumentReference: 2
Encounter: 2
Location: 1
MedicationStatement: 12
Observation: 11
Organization: 20
Patient: 1
Practitioner: 2
Procedure: 4 ✅ NOT TESTED
Provenance: 9
```

**Total Resources:** 73
**Resource Types:** 14

### NIST Ambulatory CCD
```
AllergyIntolerance: 3
Composition: 1
Condition: 3
DiagnosticReport: 1 ✅ NOT TESTED
DocumentReference: 1
Encounter: 2 ✅ NOT TESTED
Immunization: 2 ✅ NOT TESTED
Location: 1
MedicationStatement: 1
Observation: 13
Organization: 1
Patient: 1
Practitioner: 6 ✅ NOT TESTED
RelatedPerson: 1
ServiceRequest: 1 ✅ NOT TESTED
```

**Total Resources:** 37
**Resource Types:** 15

### Cerner TOC
```
AllergyIntolerance: 2
Composition: 1
Condition: 7
Device: 1
DiagnosticReport: 2 ✅ NOT TESTED
DocumentReference: 1
Encounter: 1 ✅ NOT TESTED
Immunization: 1 ✅ NOT TESTED
Location: 1
MedicationRequest: 4 ✅ NOT TESTED
Observation: 9
Organization: 1
Patient: 1
Practitioner: 1 ✅ NOT TESTED
Procedure: 2 ✅ NOT TESTED
```

**Total Resources:** 35
**Resource Types:** 15

### Partners/Epic CCD
```
AllergyIntolerance: 3
CarePlan: 3 ✅ NOT TESTED
Composition: 1
Condition: 3
Device: 1
DiagnosticReport: 3 ✅ NOT TESTED
Encounter: 1 ✅ NOT TESTED
Goal: 6 ✅ NOT TESTED
Immunization: 1 ✅ NOT TESTED
Location: 1
MedicationRequest: 7 ✅ NOT TESTED
MedicationStatement: 6
Observation: 22
Organization: 1
Patient: 1
Practitioner: 3 ✅ NOT TESTED
Procedure: 2 ✅ NOT TESTED
RelatedPerson: 1
ServiceRequest: 4 ✅ NOT TESTED
```

**Total Resources:** 70
**Resource Types:** 19

---

## Available but Untested Resources

### 🔴 HIGH PRIORITY (Present in 3+ vendors)

1. **Procedure** - Present in Athena (4), Cerner (2), Epic (2)
   - **Recommendation:** Add validation tests across all 3 vendors
   - **Test cases:** CPT/SNOMED codes, status, performer, performed date

2. **Encounter** - Present in Athena (2), NIST (2), Cerner (1), Epic (1)
   - **Recommendation:** Add validation tests across all 4 vendors
   - **Test cases:** Type, class, period, location, participant

3. **Practitioner** - Present in Athena (2), NIST (6), Cerner (1), Epic (3)
   - **Recommendation:** Add validation tests across all 4 vendors
   - **Test cases:** NPI identifier, name, author role

4. **DiagnosticReport** - Present in NIST (1), Cerner (2), Epic (3)
   - **Recommendation:** Add validation tests across 3 vendors
   - **Test cases:** LOINC code, status, results references, issued date

5. **Immunization** - Present in NIST (2), Cerner (1), Epic (1)
   - **Recommendation:** Add validation tests across 3 vendors
   - **Test cases:** CVX code, occurrence date, status, route, site

### 🟠 MEDIUM PRIORITY (Present in 2+ vendors)

6. **MedicationRequest** - Present in Cerner (4), Epic (7)
   - **Recommendation:** Add validation tests for Cerner and Epic
   - **Test cases:** RxNorm code, intent, status, dosage instruction

7. **Location** - Present in all 4 vendors (1 each)
   - **Recommendation:** Add basic validation across all vendors
   - **Test cases:** Name, address (if available)

8. **DocumentReference** - Present in Athena (2), NIST (1), Cerner (1)
   - **Recommendation:** Add validation for 3 vendors
   - **Test cases:** Type, status, context

9. **Device** - Present in Athena (1), Cerner (1), Epic (1)
   - **Recommendation:** Add validation for 3 vendors
   - **Test cases:** Type, model, UDI (if available)

### 🟡 LOWER PRIORITY (Epic-specific or rare)

10. **Goal** - Present in Epic (6)
    - **Recommendation:** Add validation for Epic sample
    - **Test cases:** Description, status, target dates

11. **CarePlan** - Present in Epic (3)
    - **Recommendation:** Add validation for Epic sample
    - **Test cases:** Status, intent, activities, goals

12. **ServiceRequest** - Present in NIST (1), Epic (4)
    - **Recommendation:** Add validation for 2 vendors
    - **Test cases:** Code, status, intent, subject

13. **RelatedPerson** - Present in NIST (1), Epic (1)
    - **Recommendation:** Lower priority, may be sparse
    - **Test cases:** Relationship, name, patient reference

14. **Organization** - Present in all 4 vendors (20, 1, 1, 1)
    - **Recommendation:** Already implicitly tested via references
    - **Test cases:** Name, identifier (if adding explicit tests)

15. **Provenance** - Present in Athena (9)
    - **Recommendation:** Lower priority (generated resource)
    - **Test cases:** Target, agent, recorded

---

## Recommended E2E Test Additions - Data-Driven

Based on actual resource availability, here's the recommended phased approach:

### Phase 1: Universal Coverage (Present in all 4 vendors)
**Target:** Add to all 4 vendor E2E tests

1. ✅ **Encounter** (2 + 2 + 1 + 1 = 6 encounters across samples)
   - Athena: Validate 1 encounter with type, period
   - NIST: Validate 1 encounter with type, period
   - Cerner: Validate 1 encounter with type, period
   - Epic: Validate 1 encounter with type, period

2. ✅ **Practitioner** (2 + 6 + 1 + 3 = 12 practitioners)
   - All vendors: Validate document author has Practitioner with NPI and name

### Phase 2: High-Value Clinical Data (Present in 3+ vendors)
**Target:** Add where available

3. ✅ **Procedure** (4 + 2 + 2 = 8 procedures)
   - Athena: Validate 1 procedure with CPT/SNOMED code, status
   - Cerner: Validate 1 procedure with CPT/SNOMED code, status
   - Epic: Validate 1 procedure with CPT/SNOMED code, status

4. ✅ **DiagnosticReport** (1 + 2 + 3 = 6 reports)
   - NIST: Validate 1 diagnostic report with LOINC code, results
   - Cerner: Validate 1 diagnostic report with LOINC code, results
   - Epic: Validate 1 diagnostic report with LOINC code, results

5. ✅ **Immunization** (2 + 1 + 1 = 4 immunizations)
   - NIST: Validate 1 immunization with CVX code, date
   - Cerner: Validate 1 immunization with CVX code, date
   - Epic: Validate 1 immunization with CVX code, date

### Phase 3: Medication & Orders (Present in 2+ vendors)
**Target:** Add where available

6. ✅ **MedicationRequest** (4 + 7 = 11 requests)
   - Cerner: Validate 1 medication request with RxNorm code, intent
   - Epic: Validate 1 medication request with RxNorm code, intent

### Phase 4: Epic Advanced Features (Epic-specific)
**Target:** Leverage Epic's comprehensive data

7. ✅ **Goal** (6 in Epic)
   - Epic: Validate 1 goal with description, status, target date

8. ✅ **CarePlan** (3 in Epic)
   - Epic: Validate 1 care plan with status, intent, activities

---

## Expected Test Count Increases

### Current: 38 tests (10 Athena + 10 NIST + 8 Cerner + 10 Epic)

### After Phase 1:
- Athena: +2 tests (Encounter, Practitioner) = **12 tests**
- NIST: +2 tests (Encounter, Practitioner) = **12 tests**
- Cerner: +2 tests (Encounter, Practitioner) = **10 tests**
- Epic: +2 tests (Encounter, Practitioner) = **12 tests**
- **Total: 46 tests (+8, 21% increase)**

### After Phase 2:
- Athena: +1 test (Procedure) = **13 tests**
- NIST: +2 tests (DiagnosticReport, Immunization) = **14 tests**
- Cerner: +3 tests (Procedure, DiagnosticReport, Immunization) = **13 tests**
- Epic: +3 tests (Procedure, DiagnosticReport, Immunization) = **15 tests**
- **Total: 55 tests (+9, 20% increase)**

### After Phase 3:
- Cerner: +1 test (MedicationRequest) = **14 tests**
- Epic: +1 test (MedicationRequest) = **16 tests**
- **Total: 57 tests (+2, 4% increase)**

### After Phase 4:
- Epic: +2 tests (Goal, CarePlan) = **18 tests**
- **Total: 59 tests (+2, 4% increase)**

### Final Target: 59 tests (13 Athena + 14 NIST + 14 Cerner + 18 Epic)
**+21 tests from baseline (55% increase)**

---

## Coverage Improvement

### Current Coverage: 27% (7/26 documented mappings tested)

### After Phases 1-4:
- **Tested:** Patient, Condition, AllergyIntolerance, Observation, MedicationStatement, Composition, Bundle, **Encounter, Practitioner, Procedure, DiagnosticReport, Immunization, MedicationRequest, Goal, CarePlan**
- **Count:** 15/26 mappings
- **Coverage:** 58% (+31 percentage points)

---

## Next Steps

1. ✅ **COMPLETED:** Inventory resource types in vendor samples
2. **NEXT:** Implement Phase 1 tests (Encounter, Practitioner) across all 4 vendors
3. **NEXT:** Implement Phase 2 tests (Procedure, DiagnosticReport, Immunization)
4. **NEXT:** Implement Phase 3 tests (MedicationRequest)
5. **NEXT:** Implement Phase 4 tests (Goal, CarePlan in Epic)
6. **NEXT:** Update E2E_MAPPING_COVERAGE.md with final results
