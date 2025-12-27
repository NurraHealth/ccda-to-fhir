# Error Summary - Quick Reference

**Date:** 2025-12-26
**Success Rate:** 78.1% (321/411)
**Failures:** 90 files
**Goal:** 100% success rate

---

## Error Categories

| Category | Count | Type | Priority |
|----------|-------|------|----------|
| Act validation | 47 | C-CDA Parser Bug | **HIGH** |
| LanguageCommunication | 13 | C-CDA Parser Bug | HIGH |
| Observation validation | 11 | C-CDA Parser Bug | MEDIUM |
| XML Syntax Errors | 7 | Invalid XML | LOW |
| Encounter validation | 6 | C-CDA Parser Bug | MEDIUM |
| ClinicalDocument validation | 3 | C-CDA Parser Bug | MEDIUM |
| SubstanceAdministration | 2 | C-CDA Parser Bug | LOW |
| Procedure validation | 1 | C-CDA Parser Bug | LOW |

---

## Top 3 Issues to Fix

### 1. Act Validation (47 files) - 52% of failures

**Problem:** Pydantic validation errors in `ccda_to_fhir.ccda.models.act`

**Two main patterns:**
- **Pattern A (27 files):** effectiveTime SHALL contain high when statusCode is 'completed'
- **Pattern B (20 files):** code SHALL be 'CONC', found incorrect code

**Files:**
- C-CDA-Examples/Documents/*.xml (Consultation, Progress, Referral Notes)
- ccda-samples from multiple vendors (Edaris, Freedom Medical, etc.)

**Fix:** Relax Pydantic validation constraints to match real-world C-CDA variance

---

### 2. LanguageCommunication Validation (13 files) - 14% of failures

**Problem:** language_code validation too strict

**Files:** ccda-samples from NextTech, NueMD, etc.

**Fix:** Update LanguageCommunication Pydantic model validation

---

### 3. Observation Validation (11 files) - 12% of failures

**Problem:** target_site_code field validation

**Files:** ccda-samples/CPSI, EchoMan, etc.

**Fix:** Fix target_site_code handling in Observation model

---

## Impact Projection

| Fix | Files Fixed | New Success Rate |
|-----|-------------|------------------|
| Act validation | +47 | 89.5% |
| + LanguageCommunication | +13 | 92.7% |
| + Observation | +11 | 95.4% |
| + Other parser bugs | +12 | 98.3% |
| + XML errors excluded | +7 | 100% |

---

## Quick Action Plan

1. **Week 1:** Fix Act validation (47 files → 89.5%)
2. **Week 2:** Fix LanguageCommunication + Observation (24 files → 95.4%)
3. **Week 3:** Fix remaining parser bugs (12 files → 98.3%)
4. **Week 4:** Decide on XML syntax errors (exclude or manual fix)

**Estimated time to 98%+:** 3 weeks of focused C-CDA parser fixes

---

## Files

- **Full details:** `ERROR_REPORT.md` (352 lines)
- **Test results:** `stress_test_results.json`
- **Run tests:** `python stress_test.py --skip-fragments`
