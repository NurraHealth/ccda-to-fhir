# Terminology Maps: C-CDA ↔ FHIR Concept Maps

This document defines the concept maps used to translate coded values between C-CDA and FHIR. These mappings ensure consistent terminology transformation across the conversion process.

## Overview

C-CDA and FHIR use different value sets for many common fields (status codes, use codes, etc.). Concept maps provide the authoritative translation rules for these vocabularies.

**Reference**: [HL7 C-CDA on FHIR Concept Maps](https://build.fhir.org/ig/HL7/ccda-on-fhir/conceptMaps.html)

---

## General Data Type Maps

### Name Use

Maps C-CDA name/@use to FHIR HumanName.use

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `L` | `usual` | Legal name |
| `OR` | `official` | Official registry name |
| `C` | `old` | No longer in use |
| `P` | `nickname` | Nickname or pseudonym |
| `A` | `anonymous` | Anonymous |
| `ASGN` | `usual` | Assigned name |
| (maiden context) | `maiden` | Name before marriage |

**Source**: C-CDA EntityNameUse
**Target**: FHIR NameUse value set

---

### Address Use

Maps C-CDA addr/@use to FHIR Address.use

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `H` | `home` | Home address |
| `HP` | `home` | Primary home |
| `HV` | `home` | Vacation home |
| `WP` | `work` | Work address |
| `DIR` | `work` | Direct address |
| `PUB` | `work` | Public address |
| `TMP` | `temp` | Temporary address |
| `BAD` | `old` | Bad/incorrect address |

**Source**: C-CDA PostalAddressUse
**Target**: FHIR AddressUse value set

---

### Telecom Use

Maps C-CDA telecom/@use to FHIR ContactPoint.use

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `H` | `home` | Home contact |
| `HP` | `home` | Primary home |
| `WP` | `work` | Work contact |
| `MC` | `mobile` | Mobile contact |
| `TMP` | `temp` | Temporary contact |
| `BAD` | `old` | Bad/incorrect number |

**Source**: C-CDA TelecommunicationAddressUse
**Target**: FHIR ContactPointUse value set

---

### Telecom System

Derived from telecom/@value prefix

| C-CDA Prefix | FHIR System | Example |
|--------------|-------------|---------|
| `tel:` | `phone` | `tel:+1(555)555-1234` |
| `mailto:` | `email` | `mailto:user@example.com` |
| `fax:` | `fax` | `fax:+1(555)555-5678` |
| `http:` | `url` | `http://example.com` |
| `https:` | `url` | `https://example.com` |

**Source**: C-CDA telecom value scheme
**Target**: FHIR ContactPointSystem value set

---

### NullFlavor to Data Absent Reason

Maps C-CDA nullFlavor to FHIR data-absent-reason extension

| C-CDA NullFlavor | FHIR Code | Description |
|------------------|-----------|-------------|
| `UNK` | `unknown` | Unknown |
| `ASKU` | `asked-unknown` | Asked but unknown |
| `NAV` | `temp-unknown` | Temporarily unavailable |
| `NASK` | `not-asked` | Not asked |
| `NI` | `unknown` | No information |
| `NA` | `not-applicable` | Not applicable |
| `MSK` | `masked` | Masked |
| `OTH` | `unsupported` | Other |
| `NINF` | `negative-infinity` | Negative infinity |
| `PINF` | `positive-infinity` | Positive infinity |

**Source**: C-CDA NullFlavor vocabulary
**Target**: FHIR DataAbsentReason value set
**Extension**: `http://hl7.org/fhir/StructureDefinition/data-absent-reason`

---

### Administrative Gender

Maps C-CDA patient/administrativeGenderCode to FHIR Patient.gender

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `M` | `male` | Male |
| `F` | `female` | Female |
| `UN` | `other` | Undifferentiated |
| `UNK` | `unknown` | Unknown |

**Source**: C-CDA AdministrativeGender (OID 2.16.840.1.113883.5.1)
**Target**: FHIR AdministrativeGender value set

---

## Patient Maps

### Marital Status

Maps C-CDA patient/maritalStatusCode to FHIR Patient.maritalStatus

| C-CDA Code (HL7 v3) | FHIR Code (HL7 v3) | Description |
|---------------------|---------------------|-------------|
| `A` | `A` | Annulled |
| `D` | `D` | Divorced |
| `I` | `I` | Interlocutory |
| `L` | `L` | Legally separated |
| `M` | `M` | Married |
| `P` | `P` | Polygamous |
| `S` | `S` | Never married |
| `T` | `T` | Domestic partner |
| `W` | `W` | Widowed |
| `UNK` | `UNK` | Unknown |

**Source & Target**: HL7 v3 MaritalStatus (used by both standards)
**System**: `http://terminology.hl7.org/CodeSystem/v3-MaritalStatus`

---

## AllergyIntolerance Maps

### Allergy Type

Maps C-CDA Allergy Observation to FHIR AllergyIntolerance.type

| C-CDA Value | C-CDA Code System | FHIR Type |
|-------------|-------------------|-----------|
| Allergy | SNOMED CT 609328004 | `allergy` |
| Propensity to adverse reactions | SNOMED CT 420134006 | `allergy` |
| Drug intolerance | SNOMED CT 59037007 | `intolerance` |
| Drug allergy | SNOMED CT 416098002 | `allergy` |
| Food allergy | SNOMED CT 414285001 | `allergy` |
| Food intolerance | SNOMED CT 235719002 | `intolerance` |

**Source**: C-CDA Allergy Observation value
**Target**: FHIR AllergyIntolerance.type value set

---

### Allergy Category

Maps C-CDA substance codes to FHIR AllergyIntolerance.category

| C-CDA Code System | FHIR Category |
|-------------------|---------------|
| RxNorm (medication codes) | `medication` |
| UNII (substance codes) | `medication` |
| SNOMED CT food codes | `food` |
| Food allergen codes | `food` |
| Environmental substance codes | `environment` |

**Source**: C-CDA participant/participantRole/playingEntity/code
**Target**: FHIR AllergyIntolerance.category value set

**Note**: Category inference based on code system and semantic meaning

---

### Allergy Clinical Status

Maps C-CDA Allergy Status Observation to FHIR AllergyIntolerance.clinicalStatus

| C-CDA Code | C-CDA Display | FHIR Status | FHIR Code |
|------------|---------------|-------------|-----------|
| `55561003` | Active | Active | `active` |
| `73425007` | Inactive | Inactive | `inactive` |
| `413322009` | Resolved | Resolved | `resolved` |

**Source**: C-CDA Allergy Status Observation (SNOMED CT)
**Target**: FHIR allergyintolerance-clinical value set
**System**: `http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical`

---

### Allergy Verification Status

Maps C-CDA status to FHIR AllergyIntolerance.verificationStatus

| C-CDA Pattern | FHIR Status | FHIR Code |
|---------------|-------------|-----------|
| Active concern | Confirmed | `confirmed` |
| Negation indicator true | Refuted | `refuted` |
| Completed concern | Confirmed | `confirmed` |
| Suspended concern | Unconfirmed | `unconfirmed` |

**Target**: FHIR allergyintolerance-verification value set
**System**: `http://terminology.hl7.org/CodeSystem/allergyintolerance-verification`

---

### Criticality

Maps C-CDA Criticality Observation to FHIR AllergyIntolerance.criticality

| C-CDA Code | C-CDA Display | FHIR Criticality |
|------------|---------------|------------------|
| `399166001` | Fatal | `high` |
| `24484000` | Severe | `high` |
| `255604002` | Mild | `low` |
| `6736007` | Moderate | `low` |
| `371923003` | Mild to moderate | `low` |
| `371924009` | Moderate to severe | `high` |
| `442452003` | Life threatening | `high` |

**Source**: C-CDA Criticality Observation (SNOMED CT)
**Target**: FHIR AllergyIntolerance.criticality value set

---

### Reaction Severity

Maps C-CDA Severity Observation to FHIR AllergyIntolerance.reaction.severity

| C-CDA Code | C-CDA Display | FHIR Severity |
|------------|---------------|---------------|
| `255604002` | Mild | `mild` |
| `6736007` | Moderate | `moderate` |
| `24484000` | Severe | `severe` |
| `371923003` | Mild to moderate | `mild` |
| `371924009` | Moderate to severe | `severe` |

**Source**: C-CDA Severity Observation (SNOMED CT)
**Target**: FHIR reaction-event-severity value set

---

### No Known Allergies

Maps C-CDA negation patterns to FHIR negated allergy codes

| C-CDA Code | C-CDA System | FHIR Code | FHIR Display |
|------------|--------------|-----------|--------------|
| `716186003` | SNOMED CT | `716186003` | No known allergy |
| `409137002` | SNOMED CT | `409137002` | No known drug allergy |
| `428607008` | SNOMED CT | `428607008` | No known environmental allergy |
| `429625007` | SNOMED CT | `429625007` | No known food allergy |

**Source & Target**: SNOMED CT (used by both standards)
**Pattern**: C-CDA uses negationInd="true" with substance "No known allergies" vs. FHIR uses specific negated codes

---

## Condition (Problems) Maps

### Condition Clinical Status

Maps C-CDA Problem Status Observation to FHIR Condition.clinicalStatus

| C-CDA Code | C-CDA Display | FHIR Status | FHIR Code |
|------------|---------------|-------------|-----------|
| `55561003` | Active | Active | `active` |
| `73425007` | Inactive | Inactive | `inactive` |
| `413322009` | Resolved | Resolved | `resolved` |
| `277022003` | Remission | Remission | `remission` |

**Source**: C-CDA Problem Status Observation (SNOMED CT)
**Target**: FHIR condition-clinical value set
**System**: `http://terminology.hl7.org/CodeSystem/condition-clinical`

---

### Condition Verification Status

Maps C-CDA observation to FHIR Condition.verificationStatus

| C-CDA Pattern | FHIR Status | FHIR Code |
|---------------|-------------|-----------|
| Active concern | Confirmed | `confirmed` |
| Negation indicator true | Refuted | `refuted` |
| Preliminary/working diagnosis | Provisional | `provisional` |
| Differential diagnosis | Differential | `differential` |

**Target**: FHIR condition-ver-status value set
**System**: `http://terminology.hl7.org/CodeSystem/condition-ver-status`

---

### Problem Category

Maps C-CDA section codes to FHIR Condition.category

| C-CDA Section LOINC | Section Name | FHIR Category Code | FHIR Display |
|---------------------|--------------|-------------------|--------------|
| `11450-4` | Problem list | `problem-list-item` | Problem List Item |
| `75326-9` | Problem | `problem-list-item` | Problem List Item |
| `8648-8` | Hospital course | `encounter-diagnosis` | Encounter Diagnosis |

**Source**: C-CDA Section codes (LOINC)
**Target**: FHIR condition-category value set
**System**: `http://terminology.hl7.org/CodeSystem/condition-category`

---

## Observation (Results) Maps

### Result Status

Maps C-CDA Result Observation statusCode to FHIR Observation.status

Per ConceptMap CF-ResultStatus: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-ResultStatus.html

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `registered` |
| `held` | `registered` |
| `suspended` | `registered` |
| `aborted` | `cancelled` |
| `cancelled` | `cancelled` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR ObservationStatus value set

**Note**: Per official ConceptMap, C-CDA codes `active`, `held`, and `suspended` all map to FHIR `registered` status (with loose/cautious mapping relationship noted in the ConceptMap).

---

### DiagnosticReport Status

Maps C-CDA Result Organizer statusCode to FHIR DiagnosticReport.status

Per ConceptMap CF-ResultReportStatus: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-ResultReportStatus.html

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `registered` |
| `held` | `registered` |
| `suspended` | `registered` |
| `aborted` | `cancelled` |
| `cancelled` | `cancelled` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR DiagnosticReportStatus value set

**Note**: Per official ConceptMap, C-CDA codes `active`, `held`, and `suspended` all map to FHIR `registered` status (with loose/cautious mapping relationship noted in the ConceptMap).

---

### Result Interpretation

Maps C-CDA interpretationCode to FHIR Observation.interpretation

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `N` | `N` | Normal |
| `L` | `L` | Low |
| `H` | `H` | High |
| `LL` | `LL` | Critically low |
| `HH` | `HH` | Critically high |
| `A` | `A` | Abnormal |
| `AA` | `AA` | Critically abnormal |
| `<` | `<` | Off scale low |
| `>` | `>` | Off scale high |

**Source & Target**: HL7 v3 ObservationInterpretation (used by both standards)
**System**: `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation`

---

## Procedure Maps

### Procedure Status

Maps C-CDA Procedure Activity statusCode to FHIR Procedure.status

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `completed` | `completed` |
| `active` | `in-progress` |
| `aborted` | `stopped` |
| `cancelled` | `not-done` |
| `held` | `preparation` |
| `new` | `preparation` |
| `suspended` | `on-hold` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR EventStatus value set

---

### Procedure Negation

When C-CDA Procedure has @negationInd="true"

| C-CDA Pattern | FHIR Mapping |
|---------------|--------------|
| `negationInd="true"` | `status: "not-done"` |
| `negationInd="true"` | `statusReason` (if reason provided) |

**Target**: FHIR Procedure.status = `not-done`

---

## Immunization Maps

### Immunization Status

Maps C-CDA Immunization Activity statusCode and negation to FHIR Immunization.status

| C-CDA Pattern | FHIR Status |
|---------------|-------------|
| `completed` | `completed` |
| `active` | `completed` |
| `refused` | `not-done` |
| `negationInd="true"` | `not-done` |
| `cancelled` | `not-done` |
| `aborted` | `not-done` |

**Source**: C-CDA ActStatus + negationInd
**Target**: FHIR ImmunizationStatusCodes value set

---

### Immunization Refusal Reason

Maps C-CDA Immunization Refusal Reason to FHIR Immunization.statusReason

| C-CDA Code | C-CDA Display | FHIR Code | FHIR Display |
|------------|---------------|-----------|--------------|
| `IMMUNE` | Immunity | `IMMUNE` | Immunity |
| `MEDPREC` | Medical precaution | `MEDPREC` | Medical precaution |
| `OSTOCK` | Out of stock | `OSTOCK` | Product out of stock |
| `PATOBJ` | Patient objection | `PATOBJ` | Patient objection |
| `PHILISOP` | Philosophical objection | `PHILISOP` | Philosophical objection |
| `RELIG` | Religious objection | `RELIG` | Religious objection |
| `VACEFF` | Vaccine efficacy concerns | `VACEFF` | Vaccine efficacy concerns |
| `VACSAF` | Vaccine safety concerns | `VACSAF` | Vaccine safety concerns |

**Source & Target**: HL7 v3 ActReason (used by both standards)
**System**: `http://terminology.hl7.org/CodeSystem/v3-ActReason`

---

## Medication Maps

### Medication Status

Maps C-CDA Medication Activity statusCode to FHIR MedicationRequest.status

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `active` | `active` |
| `completed` | `completed` |
| `aborted` | `stopped` |
| `cancelled` | `cancelled` |
| `held` | `on-hold` |
| `suspended` | `on-hold` |
| `new` | `draft` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR medicationrequest-status value set

**Note**: Some implementers map all completed medications to `active` to indicate historical use.

---

### Medication Intent

Maps C-CDA Medication Activity @moodCode to FHIR MedicationRequest.intent

| C-CDA MoodCode | FHIR Intent |
|----------------|-------------|
| `EVN` (Event) | `order` |
| `INT` (Intent) | `order` |
| `PRMS` (Promise) | `proposal` |
| `PRP` (Proposal) | `proposal` |
| `RQO` (Request) | `order` |

**Source**: C-CDA ActMood vocabulary
**Target**: FHIR medicationrequest-intent value set

**Note**: C-CDA templates typically use EVN or INT for documented medications.

---

## Encounter Maps

### Encounter Status

Maps C-CDA Encounter Activity statusCode to FHIR Encounter.status

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `completed` | `finished` |
| `active` | `in-progress` |
| `cancelled` | `cancelled` |
| `aborted` | `cancelled` |
| `held` | `planned` |
| `new` | `planned` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR EncounterStatus value set

---

### Encounter Class

Maps C-CDA Encounter code to FHIR Encounter.class

| C-CDA Code | C-CDA System | FHIR Class Code | FHIR Display |
|------------|--------------|-----------------|--------------|
| `AMB` | Act Code | `AMB` | Ambulatory |
| `EMER` | Act Code | `EMER` | Emergency |
| `FLD` | Act Code | `FLD` | Field |
| `HH` | Act Code | `HH` | Home health |
| `IMP` | Act Code | `IMP` | Inpatient encounter |
| `ACUTE` | Act Code | `ACUTE` | Inpatient acute |
| `NONAC` | Act Code | `NONAC` | Inpatient non-acute |
| `OBSENC` | Act Code | `OBSENC` | Observation encounter |
| `PRENC` | Act Code | `PRENC` | Pre-admission |
| `SS` | Act Code | `SS` | Short stay |
| `VR` | Act Code | `VR` | Virtual |

**Source & Target**: HL7 v3 ActCode (used by both standards)
**System**: `http://terminology.hl7.org/CodeSystem/v3-ActCode`

---

## Document-Level Maps

### Composition Status

Maps C-CDA ClinicalDocument statusCode to FHIR Composition.status

| C-CDA StatusCode | FHIR Status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `preliminary` |

**Source**: C-CDA ActStatus vocabulary
**Target**: FHIR CompositionStatus value set

**Note**: C-CDA documents are almost always `completed` → `final`

---

### Confidentiality

Maps C-CDA confidentialityCode to FHIR Composition.confidentiality

| C-CDA Code | FHIR Code | Description |
|------------|-----------|-------------|
| `N` | `N` | Normal |
| `R` | `R` | Restricted |
| `V` | `V` | Very restricted |

**Source & Target**: HL7 v3 Confidentiality (used by both standards)
**System**: `http://terminology.hl7.org/CodeSystem/v3-Confidentiality`

---

## Implementation Notes

### Code System Translation

Many concept maps require translating C-CDA OIDs to FHIR URIs:

| C-CDA OID | FHIR URI | Code System |
|-----------|----------|-------------|
| `2.16.840.1.113883.6.1` | `http://loinc.org` | LOINC |
| `2.16.840.1.113883.6.96` | `http://snomed.info/sct` | SNOMED CT |
| `2.16.840.1.113883.6.88` | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |

**See**: [00-overview.md](00-overview.md#oid-to-uri-translation) for complete OID-URI mapping table

---

### Unmapped Values

When a C-CDA value has no equivalent in FHIR:

1. **Use extension**: Create a FHIR extension to preserve the original value
2. **Use text**: Map to `.text` field in CodeableConcept
3. **Use closest match**: Map to the nearest semantic equivalent with a note
4. **Log warning**: Document the unmapped value in conversion logs

---

### Bidirectional Considerations

Some mappings are **lossy in one direction**:

- **C-CDA → FHIR**: Generally preserves semantics well
- **FHIR → C-CDA**: May require defaulting or inference due to C-CDA's more rigid vocabulary constraints

**Example**: FHIR AllergyIntolerance.type allows `biologic` but C-CDA has no direct equivalent

---

## References

- [HL7 C-CDA on FHIR Concept Maps](https://build.fhir.org/ig/HL7/ccda-on-fhir/conceptMaps.html)
- [HL7 v3 Code Systems](https://terminology.hl7.org/codesystems-v3.html)
- [FHIR Value Sets](http://hl7.org/fhir/R4/terminologies-valuesets.html)
- [US Core Terminology](http://hl7.org/fhir/us/core/terminology.html)
