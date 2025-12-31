# FHIR R4B: Condition Resource

## Overview

The Condition resource documents a clinical condition, problem, diagnosis, or other event, situation, issue, or clinical concept that has risen to a level of concern. It captures circumstances that affect patient health, including social determinants, risk factors, and post-procedural states.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Condition |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Patient Care |
| URL | https://hl7.org/fhir/R4B/condition.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition |

## Scope and Usage

The resource accommodates diverse use cases:
- Clinician-assessed diagnoses
- Patient-reported concerns
- Nursing problem lists
- Persistent symptoms
- Social determinants of health
- Risk factors
- Post-procedural states

The Condition resource captures "circumstances that rise to the level of importance" affecting patient health.

## JSON Structure

```json
{
  "resourceType": "Condition",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/condition",
      "value": "ab1791b0-5c71-11db-b0de-0800200c9a66"
    }
  ],
  "clinicalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
        "code": "active",
        "display": "Active"
      }
    ]
  },
  "verificationStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
        "code": "confirmed",
        "display": "Confirmed"
      }
    ]
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/condition-category",
          "code": "problem-list-item",
          "display": "Problem List Item"
        }
      ]
    }
  ],
  "severity": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "6736007",
        "display": "Moderate"
      }
    ]
  },
  "code": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "I10",
        "display": "Essential (primary) hypertension"
      },
      {
        "system": "http://snomed.info/sct",
        "code": "59621000",
        "display": "Essential hypertension"
      }
    ],
    "text": "Essential Hypertension"
  },
  "bodySite": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "80891009",
          "display": "Heart structure"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "onsetDateTime": "2010-03-01",
  "abatementDateTime": "2015-06-15",
  "recordedDate": "2010-03-01",
  "recorder": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "asserter": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "stage": [
    {
      "summary": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "786005",
            "display": "Clinical stage I"
          }
        ]
      },
      "type": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "260998006",
            "display": "Clinical staging"
          }
        ]
      }
    }
  ],
  "evidence": [
    {
      "code": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "271649006",
              "display": "Systolic blood pressure"
            }
          ]
        }
      ],
      "detail": [
        {
          "reference": "Observation/blood-pressure"
        }
      ]
    }
  ],
  "note": [
    {
      "text": "Patient has been managing hypertension with lifestyle changes"
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this condition.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### clinicalStatus (0..1)

The clinical status of the condition.

| Type | Description |
|------|-------------|
| CodeableConcept | active \| recurrence \| relapse \| inactive \| remission \| resolved |

**Value Set:** http://hl7.org/fhir/ValueSet/condition-clinical

| Code | Display | Definition |
|------|---------|------------|
| active | Active | The condition is active |
| recurrence | Recurrence | The condition has recurred after resolution |
| relapse | Relapse | The condition has relapsed after remission |
| inactive | Inactive | The condition is inactive but not resolved |
| remission | Remission | The condition is in remission |
| resolved | Resolved | The condition is resolved |

**System:** `http://terminology.hl7.org/CodeSystem/condition-clinical`

### verificationStatus (0..1)

The verification status to support the clinical status.

| Type | Description |
|------|-------------|
| CodeableConcept | unconfirmed \| provisional \| differential \| confirmed \| refuted \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/condition-ver-status

| Code | Display | Definition |
|------|---------|------------|
| unconfirmed | Unconfirmed | There is not sufficient evidence to confirm |
| provisional | Provisional | A tentative diagnosis |
| differential | Differential | One of a set of potential diagnoses |
| confirmed | Confirmed | Sufficient evidence to confirm diagnosis |
| refuted | Refuted | This condition has been ruled out |
| entered-in-error | Entered in Error | Record was entered in error |

**System:** `http://terminology.hl7.org/CodeSystem/condition-ver-status`

### category (0..*)

Category of the condition.

| Type | Description |
|------|-------------|
| CodeableConcept[] | problem-list-item \| encounter-diagnosis \| health-concern |

**Value Set:** http://hl7.org/fhir/ValueSet/condition-category

| Code | Display | Definition |
|------|---------|------------|
| problem-list-item | Problem List Item | Item on the patient's problem list |
| encounter-diagnosis | Encounter Diagnosis | Diagnosis made during an encounter |
| health-concern | Health Concern | A health concern or risk |

**System:** `http://terminology.hl7.org/CodeSystem/condition-category`

### severity (0..1)

Subjective severity of the condition.

| Type | Description |
|------|-------------|
| CodeableConcept | Severity level code |

**Common Severity Codes (SNOMED):**
| Code | Display |
|------|---------|
| 255604002 | Mild |
| 6736007 | Moderate |
| 24484000 | Severe |
| 399166001 | Fatal |

### code (0..1)

The condition, problem, or diagnosis code.

| Type | Description |
|------|-------------|
| CodeableConcept | Code for the condition |

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://hl7.org/fhir/sid/icd-10-cm` | ICD-10-CM |
| `http://snomed.info/sct` | SNOMED CT |
| `http://hl7.org/fhir/sid/icd-9-cm` | ICD-9-CM |

### bodySite (0..*)

Anatomical location of the condition.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Body site code (typically SNOMED) |

**Value Set:** http://hl7.org/fhir/ValueSet/body-site (Example binding)

### bodyStructure (0..1)

Structured anatomical location reference.

| Type | Description |
|------|-------------|
| Reference(BodyStructure) | Anatomical location as BodyStructure resource |

**Constraint:** bodyStructure SHALL only be present if bodySite is absent.

### subject (1..1)

The patient who has the condition.

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Required reference to subject |

### encounter (0..1)

The encounter during which the condition was recorded.

| Type | Description |
|------|-------------|
| Reference(Encounter) | Associated encounter |

### onset[x] (0..1)

When the condition began.

| Element | Type | Description |
|---------|------|-------------|
| onsetDateTime | dateTime | Date/time of onset |
| onsetAge | Age | Age when condition started |
| onsetPeriod | Period | Period of onset |
| onsetRange | Range | Range of onset |
| onsetString | string | Textual onset description |

### abatement[x] (0..1)

When the condition resolved or went into remission.

| Element | Type | Description |
|---------|------|-------------|
| abatementDateTime | dateTime | Date/time of resolution |
| abatementAge | Age | Age when resolved |
| abatementPeriod | Period | Period of resolution |
| abatementRange | Range | Range of resolution |
| abatementString | string | Textual resolution description |

### recordedDate (0..1)

| Type | Description |
|------|-------------|
| dateTime | Date record was first recorded |

### recorder (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Patient \| RelatedPerson) | Who recorded the condition |

### asserter (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Patient \| RelatedPerson) | Person who asserted the condition |

### stage (0..*)

Stage/grade assessment information.

| Element | Type | Description |
|---------|------|-------------|
| summary | CodeableConcept | Simple stage summary |
| assessment | Reference[] | Assessment basis |
| type | CodeableConcept | Kind of staging (clinical, pathological) |

**Constraint:** Stage SHALL include either summary or assessment element.

### evidence (0..*)

Supporting clinical findings for the diagnosis.

| Type | Description |
|------|-------------|
| CodeableReference[] | Supporting evidence as CodeableReference (Observation, DiagnosticReport, etc.) |

**Value Set:** http://hl7.org/fhir/ValueSet/clinical-findings (Example binding)

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional narrative about the condition |

## Special Considerations

### Condition vs AllergyIntolerance

Use Condition for:
- Diseases and disorders
- Diagnoses
- Problems
- Health concerns

Use AllergyIntolerance for:
- Allergies
- Drug intolerances
- Food intolerances
- Environmental sensitivities

### Problem List vs Encounter Diagnosis

| Category | Use Case |
|----------|----------|
| problem-list-item | Chronic/ongoing conditions on problem list |
| encounter-diagnosis | Conditions diagnosed during a specific encounter |
| health-concern | Risk factors, health maintenance items |

## US Core Conformance Requirements

For US Core Condition profile compliance:

1. **SHALL** support `clinicalStatus`
2. **SHALL** support `verificationStatus`
3. **SHALL** support `category`
4. **SHALL** support `code`
5. **SHALL** support `subject`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| clinical-status | token | active \| recurrence \| relapse \| inactive \| remission \| resolved |
| verification-status | token | unconfirmed \| provisional \| differential \| confirmed \| refuted \| entered-in-error |
| category | token | problem-list-item \| encounter-diagnosis |
| code | token | Condition code |
| subject | reference | Who has the condition |
| patient | reference | Who has the condition (Patient only) |
| encounter | reference | Encounter when recorded |
| onset-date | date | Date of onset |
| abatement-date | date | Date of resolution |
| recorded-date | date | Date record was recorded |
| severity | token | Severity of condition |
| body-site | token | Anatomical location |
| asserter | reference | Person who asserted the condition |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| con-1 | If condition has abatement, clinicalStatus must be inactive, resolved, or remission |
| con-2 | bodyStructure SHALL only be present if bodySite is absent |
| con-3 | Stage SHALL include either summary or assessment element |

## Compartments

The Condition resource is part of the following compartments:
- Encounter
- Group
- Patient
- Practitioner
- RelatedPerson

## References

- FHIR R4B Condition: https://hl7.org/fhir/R4B/condition.html
- US Core Condition Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition
- SNOMED CT: http://snomed.info/sct
- ICD-10-CM: https://www.cdc.gov/nchs/icd/icd10cm.htm
