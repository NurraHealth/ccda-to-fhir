# C-CDA to FHIR Converter - Error Report

**Generated:** 2025-12-26
**Total Failures:** 90/411 tested files
**Success Rate:** 78.1% (321/411)
**Target:** 100% (0 failures)

## Executive Summary

This document catalogs all remaining errors in the C-CDA to FHIR converter stress test.
All failures are in **complete ClinicalDocument files** (417 fragments already filtered out).

### Error Breakdown

- **Act Validation Errors**: 47 files
- **ClinicalDocument Validation Errors**: 3 files
- **Encounter Validation Errors**: 6 files
- **LanguageCommunication Validation Errors**: 13 files
- **Observation Validation Errors**: 11 files
- **Procedure Validation Errors**: 1 files
- **SubstanceAdministration Validation Errors**: 2 files
- **XML Syntax Errors**: 7 files

---

## Act Validation Errors

**Count:** 47 files

### Error Patterns

#### Pattern 1 (27 files)

```
Failed to parse Act from element act: 1 validation error for Act
  Value error, Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): effectiveTime SHALL contain high when statusCode is 'completed' or
...
```

**Affected files:**
- `C-CDA-Examples/Documents/Consultation Note/Consultation_Note.xml`
- `C-CDA-Examples/Documents/Progress Note/Progress_Note.xml`
- `C-CDA-Examples/Documents/Referral Note/Referral_Note.xml`
- `ccda-samples/Agastha/195352.xml`
- `ccda-samples/Agastha/TransitionOfCare_CCD_R21_Sample1_Susan_Turner.xml`
- ... and 22 more

#### Pattern 2 (20 files)

```
Failed to parse Act from element act: 1 validation error for Act
  Value error, Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): code SHALL be 'CONC', found '48765-2' [type=value_error, input_va
...
```

**Affected files:**
- `ccda-samples/Edaris Forerun/ccd20170710182523-MRNZ9986322.xml`
- `ccda-samples/Edaris Forerun/newman-rn.xml`
- `ccda-samples/Freedom Medical/BATES_JR_JEREMY_V_1550_08-01-1980.52232.xml`
- `ccda-samples/Freedom Medical/NEWMAN_ALICE_JONES_1000_05-01-1970.52306.xml`
- `ccda-samples/Henry Schein/CDA_Bates_g9.xml`
- ... and 15 more

---

## ClinicalDocument Validation Errors

**Count:** 3 files

### Error Patterns

#### Pattern 1 (2 files)

```
Failed to parse ClinicalDocument from element ClinicalDocument: 1 validation error for ClinicalDocument
  Value error, US Realm Header (2.16.840.1.113883.10.20.22.1.1): SHALL contain at least one [1..
...
```

**Affected files:**
- `C-CDA-Examples/Guide Examples/US Realm Header (V3)_2.16.840.1.113883.10.20.22.1.1/US Realm Header (V3) Example.xml`
- `C-CDA-Examples/Header/Direct Address/Patient and Provider Organization Direct Address(C-CDAR2.1).xml`

#### Pattern 2 (1 files)

```
Failed to parse ClinicalDocument from element ClinicalDocument: 1 validation error for ClinicalDocument
effective_time
  Input should be a valid dictionary or instance of TS [type=model_type, input_va
...
```

**Affected files:**
- `ccda-samples/EchoMan/JONEM00.xml`

---

## Encounter Validation Errors

**Count:** 6 files

### Error Patterns

#### Pattern 1 (6 files)

```
Failed to parse Encounter from element encounter: 1 validation error for Encounter
  Value error, Encounter Activity (2.16.840.1.113883.10.20.22.4.49): SHALL contain exactly one [1..1] code [type=valu
...
```

**Affected files:**
- `ccda-samples/OpenVista CareVue/B1 INP CCD SAMPLE 1.xml`
- `ccda-samples/OpenVista CareVue/B1 INP CCD SAMPLE 2.xml`
- `ccda-samples/OpenVista CareVue/B1 INP DS SAMPLE 1.xml`
- `ccda-samples/OpenVista CareVue/B1 INP DS SAMPLE 2.xml`
- `ccda-samples/OpenVista CareVue/B1 INP RN SAMPLE 1.xml`
- ... and 1 more

---

## LanguageCommunication Validation Errors

**Count:** 13 files

### Error Patterns

#### Pattern 1 (13 files)

```
Failed to parse LanguageCommunication from element languageCommunication: 1 validation error for LanguageCommunication
language_code
  Input should be a valid dictionary or instance of CE [type=model_
...
```

**Affected files:**
- `ccda-samples/NextTech/10_20170710104504_SummaryOfCare.xml`
- `ccda-samples/NextTech/11_20170710104505_SummaryOfCare.xml`
- `ccda-samples/NextTech/12_20170710104505_SummaryOfCare.xml`
- `ccda-samples/NextTech/13_20170710104505_SummaryOfCare.xml`
- `ccda-samples/NextTech/5 - Larson, Rebecca Jones_2017-07-10 10_38_39_000.xml`
- ... and 8 more

---

## Observation Validation Errors

**Count:** 11 files

### Error Patterns

#### Pattern 1 (5 files)

```
Failed to parse Observation from element observation: 1 validation error for Observation
  Value error, Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): value SHALL be PQ (Physical Quantity),
...
```

**Affected files:**
- `ccda-samples/MedConnect/CECILIA CUMMINGS_20170808143810.xml`
- `ccda-samples/MedConnect/MYRA JONES_20170808141701.xml`
- `ccda-samples/MedConnect/SUSAN TURNER_20170808143241.xml`
- `ccda-samples/Medical Office Technologies/5492_6_Sample_ReferralNote.xml`
- `ccda-samples/Medical Office Technologies/5597_12_ReferralNote.xml`

#### Pattern 2 (2 files)

```
Failed to parse Observation from element observation: 1 validation error for Observation
  Value error, Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): SHALL contain at least one [1..*] 
...
```

**Affected files:**
- `ccda-samples/Advanced Technologies Group/SLI_CCD_b6AliceNewman_ATG_ATGEHR_10162017.xml`
- `ccda-samples/Advanced Technologies Group/SLI_CCD_b6JeremyBates_ATG_ATGEHR_10162017.xml`

#### Pattern 3 (2 files)

```
Failed to parse Observation from element observation: 1 validation error for Observation
  Value error, Problem Observation (2.16.840.1.113883.10.20.22.4.4): statusCode SHALL be 'completed', found 'No
...
```

**Affected files:**
- `ccda-samples/EHealthPartners/201710-0010123.xml`
- `ccda-samples/eRAD/Bates.xml`

#### Pattern 4 (1 files)

```
Failed to parse Observation from element observation: 1 validation error for Observation
target_site_code.0
  Input should be a valid dictionary or instance of CE [type=model_type, input_value=CD(code
...
```

**Affected files:**
- `C-CDA-Examples/General/External Document Reference/PROBLEMS_in_Empty_C-CDA_2.1 (C-CDAR2.1).xml`

#### Pattern 5 (1 files)

```
Failed to parse Observation from element observation: 1 validation error for Observation
code
  Input should be a valid dictionary or instance of CE [type=model_type, input_value=CD(code='NI', code_sy
...
```

**Affected files:**
- `ccda-samples/eRAD/Newman.xml`

---

## Procedure Validation Errors

**Count:** 1 files

### Error Patterns

#### Pattern 1 (1 files)

```
Failed to parse Procedure from element procedure: 1 validation error for Procedure
target_site_code.0
  Input should be a valid dictionary or instance of CE [type=model_type, input_value=CD(code='8209
...
```

**Affected files:**
- `ccda-samples/Navigating Cancer/AliceNewman_DirectMessage_FullRecord.xml`

---

## SubstanceAdministration Validation Errors

**Count:** 2 files

### Error Patterns

#### Pattern 1 (2 files)

```
Failed to parse SubstanceAdministration from element substanceAdministration: 1 validation error for SubstanceAdministration
route_code
  Input should be a valid dictionary or instance of CE [type=mod
...
```

**Affected files:**
- `ccda-samples/EchoMan/CUMMC00.xml`
- `ccda-samples/EchoMan/TURNS00.xml`

---

## XML Syntax Errors

**Count:** 7 files

### Error Patterns

#### Pattern 1 (2 files)

```
Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 61, column 74 (<string>, line 61)
```

**Affected files:**
- `C-CDA-Examples/Health Concerns/Health Concerns Link to Problems Section with linkHTML/Health Concerns Link to Problems Section with linkHTML(C-CDA2.1).xml`
- `C-CDA-Examples/Health Concerns/Health Concerns Link to Problems Section/Health Concerns Link to Problems Section(C-CDA2.1).xml`

#### Pattern 2 (2 files)

```
Invalid XML syntax: xmlns:schemaLocation: 'urn:hl7-org:v3 CDA.xsd' is not a valid URI, line 13, column 48 (<string>, line 13)
```

**Affected files:**
- `ccda-samples/MDLogic/ContinuityOfCareDocument_MUBatJer_20170601-145724.xml`
- `ccda-samples/MDLogic/ContinuityOfCareDocument_MUNewAli_20170601-145612.xml`

#### Pattern 3 (1 files)

```
Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 39, column 45 (<string>, line 39)
```

**Affected files:**
- `C-CDA-Examples/Guide Examples/Entry Reference_2.16.840.1.113883.10.20.22.4.122/Entry Reference Example.xml`

#### Pattern 4 (1 files)

```
Invalid XML syntax: Namespace prefix xsi for type on time is not defined, line 4, column 28 (<string>, line 4)
```

**Affected files:**
- `C-CDA-Examples/Guide Examples/Transfer Summary (V2)_2.16.840.1.113883.10.20.22.1.13/Transfer Summary participant (Support) Example.xml`

#### Pattern 5 (1 files)

```
Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 136, column 168 (<string>, line 136)
```

**Affected files:**
- `C-CDA-Examples/Plan of Treatment/Planned Encounter - Referral/Planned Encounter - Reason for Referral(C-CDAR2.1).xml`

---

## Action Items

### Priority 1: C-CDA Parser Bugs (83 files)

These are **Pydantic validation errors** in the C-CDA parser models:

1. **Act validation (47 files)** - Most common issue
   - Fix Pydantic model constraints in `ccda_to_fhir.ccda.models.act`
   - Likely `effectiveTime` validation issues

2. **LanguageCommunication (13 files)**
   - Fix Pydantic model in `ccda_to_fhir.ccda.models.datatypes`
   - Likely `language_code` validation

3. **Observation validation (11 files)**
   - Fix `target_site_code` field validation

4. **Encounter validation (6 files)**
   - Fix Pydantic model constraints

5. **Other validations (6 files)**
   - ClinicalDocument, Procedure, SubstanceAdministration

### Priority 2: XML Syntax Errors (7 files)

These files have **invalid XML** and cannot be fixed programmatically:

- May need to be excluded from tests
- Or fixed manually if they're important test cases

## Next Steps

1. **Fix Act validation** (47 files) - biggest impact
2. **Fix LanguageCommunication** (13 files)
3. **Fix Observation targetSiteCode** (11 files)
4. **Fix remaining parser bugs** (12 files)
5. **Handle XML syntax errors** (7 files)

**Estimated Impact:** Fixing C-CDA parser bugs should bring success rate to ~98%
