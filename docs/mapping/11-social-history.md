# Social History Mapping: C-CDA Social History Observations ↔ FHIR Observation / Patient Extensions

This document provides detailed mapping guidance between C-CDA Social History observations and FHIR `Observation` resources and `Patient` extensions.

## Overview

| C-CDA | FHIR |
|-------|------|
| Social History Section (LOINC `29762-2`) | Multiple FHIR resources |
| Social History Observation (`2.16.840.1.113883.10.20.22.4.38`) | `Observation` (Simple Observation) |
| Smoking Status (`2.16.840.1.113883.10.20.22.4.78`) | `Observation` (Smoking Status) |
| Pregnancy Observation (`2.16.840.1.113883.10.20.15.3.8`) | `Observation` (Pregnancy Status) |
| Birth Sex Observation | `Patient.extension` (US Core Birth Sex) |
| Gender Identity Observation | `Patient.extension` (US Core Gender Identity) |

**Reference:** [C-CDA on FHIR Social History Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-social.html)

**Key Principle:** Some C-CDA social history observations map to FHIR Observations, while others map to Patient extensions rather than creating separate Observation resources.

---

## 1. Smoking Status / Tobacco Use

### Templates

- Smoking Status - Meaningful Use (`2.16.840.1.113883.10.20.22.4.78`)
- Tobacco Use (`2.16.840.1.113883.10.20.22.4.85`)
- Smoking Status - C-CDA 3.0 (`2.16.840.1.113883.10.20.22.4.511`)

### Mapping to FHIR

**Target:** `Observation` resource with Smoking Status profile

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/id` | `Observation.identifier` | ID → Identifier |
| `observation/code` | `Observation.code` | Fixed: LOINC `72166-2` (Tobacco smoking status) |
| `observation/statusCode` | `Observation.status` | [Status ConceptMap](#status-mapping) |
| `observation/effectiveTime/@value` | `Observation.effectiveDateTime` | Date conversion |
| `observation/value[@xsi:type="CD"]` | `Observation.valueCodeableConcept` | [Smoking Status Values](#smoking-status-values) |

### Smoking Status Values

**C-CDA SNOMED CT Codes:**

| Code | Display | FHIR Mapping |
|------|---------|--------------|
| `449868002` | Current every day smoker | Direct mapping |
| `428041000124106` | Current some day smoker | Direct mapping |
| `8517006` | Former smoker | Direct mapping |
| `266919005` | Never smoker | Direct mapping |
| `77176002` | Smoker, current status unknown | Direct mapping |
| `266927001` | Unknown if ever smoked | Direct mapping |
| `428071000124103` | Current Heavy tobacco smoker | Direct mapping |
| `428061000124105` | Current Light tobacco smoker | Direct mapping |

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
  <id root="1.2.3.4" extension="smoking-123"/>
  <code code="72166-2" displayName="Tobacco smoking status"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315"/>
  <value xsi:type="CD" code="8517006" displayName="Former smoker"
         codeSystem="2.16.840.1.113883.6.96"/>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "smoking-123",
  "identifier": [
    {
      "system": "urn:oid:1.2.3.4",
      "value": "smoking-123"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "social-history",
          "display": "Social History"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "72166-2",
        "display": "Tobacco smoking status"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15",
  "valueCodeableConcept": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "8517006",
        "display": "Former smoker"
      }
    ]
  }
}
```

---

## 2. Pregnancy Observation

### Template

- Pregnancy Observation (`2.16.840.1.113883.10.20.15.3.8`)

### Mapping to FHIR

**Target:** `Observation` resource with Pregnancy Status profile (US Core v6.1+)

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/id` | `Observation.identifier` | ID → Identifier |
| `observation/code` | `Observation.code` | Fixed: LOINC `82810-3` (Pregnancy status) |
| `observation/statusCode` | `Observation.status` | Status conversion |
| `observation/effectiveTime` | `Observation.effectiveDateTime` | Date conversion |
| `observation/value[@xsi:type="CD"]` | `Observation.valueCodeableConcept` | [Pregnancy Status Values](#pregnancy-status-values) |
| Estimated Delivery Date observation | `Observation.component` | [EDD Component](#estimated-delivery-date) |

### Pregnancy Status Values

| Code | System | Display |
|------|--------|---------|
| `77386006` | SNOMED CT | Pregnant |
| `60001007` | SNOMED CT | Not pregnant |
| `261665006` | SNOMED CT | Unknown |

### Estimated Delivery Date

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <code code="11778-8" displayName="Estimated date of delivery"
          codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="TS" value="20201215"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "11778-8",
            "display": "Estimated date of delivery"
          }
        ]
      },
      "valueDateTime": "2020-12-15"
    }
  ]
}
```

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.15.3.8"/>
  <id root="1.2.3.4" extension="preg-456"/>
  <code code="82810-3" displayName="Pregnancy status"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315"/>
  <value xsi:type="CD" code="77386006" displayName="Pregnant"
         codeSystem="2.16.840.1.113883.6.96"/>
  <entryRelationship typeCode="REFR">
    <observation classCode="OBS" moodCode="EVN">
      <code code="11778-8" displayName="Estimated date of delivery"
            codeSystem="2.16.840.1.113883.6.1"/>
      <value xsi:type="TS" value="20201215"/>
    </observation>
  </entryRelationship>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "preg-456",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "social-history"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "82810-3",
        "display": "Pregnancy status"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15",
  "valueCodeableConcept": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "77386006",
        "display": "Pregnant"
      }
    ]
  },
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "11778-8",
            "display": "Estimated date of delivery"
          }
        ]
      },
      "valueDateTime": "2020-12-15"
    }
  ]
}
```

---

## 3. Pregnancy Intention

### Template

- Pregnancy Intention in Next Year

### Mapping to FHIR

**Target:** `Observation` resource (Pregnancy Intent - US Core v6+)

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/code` | `Observation.code` | LOINC `86645-9` (Pregnancy intention) |
| `observation/value` | `Observation.valueCodeableConcept` | Intent values |

**Pregnancy Intent Values:**

| Code | Display |
|------|---------|
| `454381000124105` | Wants to become pregnant |
| `454391000124108` | Does not want to become pregnant |
| `261665006` | Unknown |

---

## 4. Birth Sex → Patient Extension

**⚠️ Maps to Extension, NOT Observation**

### Template

- Birth Sex Observation (`2.16.840.1.113883.10.20.22.4.200`)

### Mapping to Patient Extension

**Target:** `Patient.extension` (US Core Birth Sex Extension)

**Extension URL:** `http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex`

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/value/@code` | `Patient.extension:birthsex.valueCode` | Direct code mapping |

### Birth Sex Values

| C-CDA Code | FHIR Code | Display |
|------------|-----------|---------|
| `F` | `F` | Female |
| `M` | `M` | Male |
| `UNK` | `UNK` | Unknown |

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
  <code code="76689-9" displayName="Sex assigned at birth"
        codeSystem="2.16.840.1.113883.6.1"/>
  <value xsi:type="CD" code="F" displayName="Female"
         codeSystem="2.16.840.1.113883.5.1"/>
</observation>
```

**FHIR (on Patient resource):**
```json
{
  "resourceType": "Patient",
  "extension": [
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex",
      "valueCode": "F"
    }
  ]
}
```

**❌ Do NOT create:**
```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{"code": "76689-9"}]
  }
}
```

---

## 5. Gender Identity → Patient Extension

**⚠️ Maps to Extension, NOT Observation**

### Template

- Gender Identity Observation

### Mapping to Patient Extension

**Target:** `Patient.extension` (US Core Gender Identity Extension)

**Extension URL:** `http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity`

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/value` | `Patient.extension:genderIdentity.valueCodeableConcept` | CodeableConcept |

### Gender Identity Values

Uses LOINC Answer List LL6130-5:

| Code | Display |
|------|---------|
| `446151000124109` | Identifies as male |
| `446141000124107` | Identifies as female |
| `407377005` | Female-to-male transsexual |
| `407376001` | Male-to-female transsexual |
| `446131000124102` | Identifies as non-conforming |
| `OTH` | Other |
| `UNK` | Unknown |

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <code code="76691-5" displayName="Gender identity"
        codeSystem="2.16.840.1.113883.6.1"/>
  <value xsi:type="CD" code="446151000124109"
         displayName="Identifies as male"
         codeSystem="2.16.840.1.113883.6.96"/>
</observation>
```

**FHIR (on Patient resource):**
```json
{
  "resourceType": "Patient",
  "extension": [
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity",
      "valueCodeableConcept": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "446151000124109",
            "display": "Identifies as male"
          }
        ]
      }
    }
  ]
}
```

---

## 6. Sex Parameter for Clinical Use → Patient Extension

**⚠️ Maps to Extension, NOT Observation**

### Template

- Sex Parameter for Clinical Use Observation (`2.16.840.1.113883.10.20.22.4.513`)

### Mapping to Patient Extension

**Target:** `Patient.extension` (FHIR Patient Sex Parameter for Clinical Use Extension)

**Extension URL:** `http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse`

**Note:** This is a complex extension with multiple sub-extensions for value, period, comment, and supportingInfo.

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/value` | `Patient.extension:sexParameterForClinicalUse.extension:value.valueCodeableConcept` | [SPCU Values](#sex-parameter-for-clinical-use-values) |
| `observation/effectiveTime` | `Patient.extension:sexParameterForClinicalUse.extension:period.valuePeriod.start` | Date conversion (snapshot→period start) |
| `observation/text/reference` | `Patient.extension:sexParameterForClinicalUse.extension:comment.valueString` | Narrative text extraction |
| `observation/entryRelationship[@typeCode='SPRT']` | `Patient.extension:sexParameterForClinicalUse.extension:supportingInfo.valueReference` | Reference to supporting Observation |

### Sex Parameter for Clinical Use Values

Uses FHIR CodeSystem `2.16.840.1.113883.4.642.4.2038` (from ValueSet `2.16.840.1.113883.4.642.3.3181`):

| Code | System | OID | Display |
|------|--------|-----|---------|
| `female-typical` | http://terminology.hl7.org/CodeSystem/sex-parameter-for-clinical-use | 2.16.840.1.113883.4.642.4.2038 | Apply female-typical setting or reference range |
| `male-typical` | http://terminology.hl7.org/CodeSystem/sex-parameter-for-clinical-use | 2.16.840.1.113883.4.642.4.2038 | Apply male-typical setting or reference range |
| `specified` | http://terminology.hl7.org/CodeSystem/sex-parameter-for-clinical-use | 2.16.840.1.113883.4.642.4.2038 | Apply specified setting or reference range |
| `unknown` | http://terminology.hl7.org/CodeSystem/data-absent-reason | 2.16.840.1.113883.4.642.4.1048 | Unknown |

**Important:**
- **CodeSystem OID** `2.16.840.1.113883.4.642.4.2038` is used in C-CDA `codeSystem` attribute ✅
- **ValueSet OID** `2.16.840.1.113883.4.642.3.3181` is for binding/validation only (not used in C-CDA XML)
- The `unknown` code comes from the data-absent-reason code system (OID: 2.16.840.1.113883.4.642.4.1048)

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.513" extension="2025-05-01"/>
  <id root="1.2.3.4" extension="spcu-123"/>
  <code code="99501-9" displayName="Sex parameter for clinical use"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20240101"/>
  <value xsi:type="CD" code="female-typical"
         displayName="Apply female-typical setting or reference range"
         codeSystem="2.16.840.1.113883.4.642.4.2038"/>
  <text>
    <reference value="#spcu-note"/>
  </text>
  <entryRelationship typeCode="SPRT">
    <observation classCode="OBS" moodCode="EVN">
      <id root="supporting-obs-id"/>
      <!-- Supporting clinical observation -->
    </observation>
  </entryRelationship>
</observation>
```

**FHIR (on Patient resource):**
```json
{
  "resourceType": "Patient",
  "extension": [
    {
      "url": "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse",
      "extension": [
        {
          "url": "value",
          "valueCodeableConcept": {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/sex-parameter-for-clinical-use",
                "code": "female-typical",
                "display": "Apply female-typical setting or reference range"
              }
            ]
          }
        },
        {
          "url": "period",
          "valuePeriod": {
            "start": "2024-01-01"
          }
        },
        {
          "url": "comment",
          "valueString": "Based on current clinical presentation and recent lab results"
        },
        {
          "url": "supportingInfo",
          "valueReference": {
            "reference": "Observation/supporting-obs-id"
          }
        }
      ]
    }
  ]
}
```

**❌ Do NOT create:**
```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [{"code": "99501-9"}]
  }
}
```

### Key Differences from Simple Sex Extension

**Simple Sex (LOINC 46098-0):**
- Maps to `us-core-sex` extension (deprecated) or `us-core-individual-sex` extension
- Simple extension with just `valueCode` or `valueCoding`
- No context information (period, supporting info)
- Already implemented ✅

**Sex Parameter for Clinical Use (LOINC 99501-9):**
- Maps to `patient-sexParameterForClinicalUse` extension
- Complex extension with multiple sub-extensions
- Includes period, comment, and supportingInfo
- Provides clinical context for decision-making
- Uses official FHIR ValueSet codes (female-typical, male-typical, specified, unknown)
- Implemented ✅

---

## 7. Tribal Affiliation → Patient Extension

**⚠️ Maps to Extension, NOT Observation**

### Mapping to Patient Extension

**Target:** `Patient.extension` (US Core Tribal Affiliation Extension)

**Extension URL:** `http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation`

---

## 8. General Social History Observation

### Template

- Social History Observation (`2.16.840.1.113883.10.20.22.4.38`)

### Mapping to FHIR

**Target:** `Observation` resource (Simple Observation - US Core v6)

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/id` | `Observation.identifier` | ID → Identifier |
| `observation/code` | `Observation.code` | CodeableConcept |
| `observation/statusCode` | `Observation.status` | Status mapping |
| `observation/effectiveTime` | `Observation.effectiveDateTime` | Date conversion |
| `observation/value` | `Observation.value[x]` | Type-specific mapping |

**Common Social History Codes:**

| LOINC Code | Display |
|------------|---------|
| `11367-0` | History of Tobacco use |
| `11368-8` | History of Alcohol use |
| `11369-6` | History of Immunization |
| `8653-8` | Hospital course |
| `8648-8` | Hospital consultations |

### Example

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
  <code code="11367-0" displayName="History of Tobacco use"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315"/>
  <value xsi:type="ST">Patient reports 20 pack-year history, quit 5 years ago</value>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "social-history"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "11367-0",
        "display": "History of Tobacco use"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15",
  "valueString": "Patient reports 20 pack-year history, quit 5 years ago"
}
```

---

## Status Mapping

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `preliminary` |
| `aborted` | `cancelled` |

---

## Category

All social history observations should include:

```json
{
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "social-history",
          "display": "Social History"
        }
      ]
    }
  ]
}
```

---

## Implementation Decision Tree

```
Is this a Social History observation?
│
├─ Birth Sex (code 76689-9)?
│  └─ → Patient.extension:us-core-birthsex ✅
│
├─ Gender Identity (code 76691-5)?
│  └─ → Patient.extension:us-core-genderIdentity ✅
│
├─ Sex for Clinical Use?
│  └─ → Patient.extension:us-core-sex ✅
│
├─ Tribal Affiliation?
│  └─ → Patient.extension:us-core-tribal-affiliation ✅
│
├─ Smoking Status (template 2.16.840.1.113883.10.20.22.4.78)?
│  └─ → Observation (Smoking Status profile) ✅
│
├─ Pregnancy (template 2.16.840.1.113883.10.20.15.3.8)?
│  └─ → Observation (Pregnancy Status profile) ✅
│
└─ Other Social History (template 2.16.840.1.113883.10.20.22.4.38)?
   └─ → Observation (Simple Observation) ✅
```

---

## Common Mistakes

### ❌ Creating Observations for Birth Sex

**Wrong:**
```json
{
  "resourceType": "Observation",
  "code": {"coding": [{"code": "76689-9"}]},
  "valueCodeableConcept": {"coding": [{"code": "F"}]}
}
```

**Correct:**
```json
{
  "resourceType": "Patient",
  "extension": [
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex",
      "valueCode": "F"
    }
  ]
}
```

### ❌ Wrong Category

**Wrong:**
```json
{
  "category": [{"coding": [{"code": "vital-signs"}]}]
}
```

**Correct:**
```json
{
  "category": [{"coding": [{"code": "social-history"}]}]
}
```

---

## References

- [C-CDA on FHIR Social History Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-social.html)
- [US Core Smoking Status Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-smokingstatus.html)
- [US Core Birth Sex Extension](http://hl7.org/fhir/us/core/StructureDefinition-us-core-birthsex.html)
- [US Core Gender Identity Extension](http://hl7.org/fhir/us/core/StructureDefinition-us-core-genderIdentity.html)
- [FHIR Observation Resource](http://hl7.org/fhir/R4/observation.html)

## Related Mappings

- See [01-patient.md](01-patient.md) for Patient extension details
- See [04-observation.md](04-observation.md) for general observation mapping
