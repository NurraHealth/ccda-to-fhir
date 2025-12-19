# FHIR R4B: Goal Resource

## Overview

The Goal resource documents intended health objectives for patients, groups, or organizations. It represents the "desired or target outcome for the person's health or well-being," which can include specific measurable targets, timeframes, and responsible parties. Goals are a core component of care planning and patient-centered care delivery.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Goal |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 3 (Trial Use) |
| Security Category | Patient |
| Responsible Work Group | Patient Care |
| URL | https://hl7.org/fhir/R4B/goal.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal |

## Scope and Usage

The Goal resource describes intended health outcomes and supports:
- Patient-centered care planning and shared decision-making
- Care coordination across providers and settings
- Progress tracking toward desired health states
- Goal-directed interventions and outcome measurement

**Common Goal Types:**
- Clinical outcomes (e.g., HbA1c < 7%, blood pressure < 140/90)
- Functional status (e.g., walk 30 minutes daily, return to work)
- Behavioral changes (e.g., smoking cessation, medication adherence)
- Social determinants of health (e.g., secure stable housing, obtain employment)
- Preventive health (e.g., complete cancer screening, achieve immunization targets)

## Boundaries and Relationships

**This resource should NOT be used for:**
- Service requests or orders (use ServiceRequest)
- Clinical tasks or to-dos (use Task)
- Organizational objectives unrelated to health (use Goal with organization subject cautiously)

**Related Resources:**
- **CarePlan:** Goals are typically referenced by care plans
- **Condition/Observation:** Referenced in `addresses` to show what the goal targets
- **ServiceRequest/MedicationRequest:** Interventions supporting goal achievement
- **QuestionnaireResponse:** May capture patient-reported goal preferences

## JSON Structure

```json
{
  "resourceType": "Goal",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/goal",
      "value": "goal-12345"
    }
  ],
  "lifecycleStatus": "active",
  "achievementStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
        "code": "in-progress",
        "display": "In Progress"
      }
    ]
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/goal-category",
          "code": "dietary",
          "display": "Dietary"
        }
      ]
    }
  ],
  "priority": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
        "code": "high-priority",
        "display": "High Priority"
      }
    ]
  },
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "289169006",
        "display": "Weight loss"
      }
    ],
    "text": "Lose 20 pounds over the next 6 months"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Amy Shaw"
  },
  "startDate": "2024-01-15",
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "29463-7",
            "display": "Body weight"
          }
        ]
      },
      "detailQuantity": {
        "value": 160,
        "unit": "lb",
        "system": "http://unitsofmeasure.org",
        "code": "[lb_av]"
      },
      "dueDate": "2024-07-15"
    }
  ],
  "statusDate": "2024-01-15",
  "expressedBy": {
    "reference": "Patient/example",
    "display": "Amy Shaw"
  },
  "addresses": [
    {
      "reference": "Condition/obesity",
      "display": "Obesity"
    }
  ],
  "note": [
    {
      "text": "Patient motivated to lose weight for upcoming wedding"
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this goal.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### lifecycleStatus (1..1)

The lifecycle state of the goal. This is a **required** and **modifier element**.

| Type | Description |
|------|-------------|
| code | Current state of the goal |

**Value Set:** http://hl7.org/fhir/ValueSet/goal-status (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| proposed | Proposed | Goal is proposed but not yet agreed |
| planned | Planned | Goal is planned but not yet actively pursued |
| accepted | Accepted | Goal has been accepted but not yet actively pursued |
| active | Active | Goal is being actively pursued |
| on-hold | On Hold | Goal was active but temporarily suspended |
| completed | Completed | Goal has been met |
| cancelled | Cancelled | Goal was abandoned without being met |
| entered-in-error | Entered in Error | Goal was created in error |
| rejected | Rejected | Proposed goal was rejected |

**System:** `http://hl7.org/fhir/goal-status`

**Summary Element:** Yes

**Note:** Changes to lifecycleStatus should be recorded in Goal.statusReason or documented via Provenance.

### achievementStatus (0..1)

Describes the progression toward the goal.

| Type | Description |
|------|-------------|
| CodeableConcept | Progress status |

**Value Set:** http://hl7.org/fhir/ValueSet/goal-achievement (Preferred binding)

| Code | Display | Definition |
|------|---------|------------|
| in-progress | In Progress | Goal is being pursued |
| improving | Improving | Goal is being met (e.g., 50% of target achieved) |
| worsening | Worsening | Goal is being pursued but moving away from target |
| no-change | No Change | Goal is being pursued but with no change |
| achieved | Achieved | Goal has been met |
| sustaining | Sustaining | Goal has been achieved and is being maintained |
| not-achieved | Not Achieved | Goal was not met |
| no-progress | No Progress | No progress toward goal |
| not-attainable | Not Attainable | Goal cannot be achieved |

**System:** `http://terminology.hl7.org/CodeSystem/goal-achievement`

**Summary Element:** Yes

### category (0..*)

Classification of the goal (e.g., treatment, dietary, behavioral).

| Type | Description |
|------|-------------|
| CodeableConcept[] | Goal category |

**Value Set:** http://hl7.org/fhir/ValueSet/goal-category (Example binding)

| Code | Display |
|------|---------|
| dietary | Dietary | Goals related to diet |
| safety | Safety | Goals related to safety |
| behavioral | Behavioral | Goals related to behavior modification |
| nursing | Nursing | Goals related to nursing care |
| physiotherapy | Physiotherapy | Goals related to physical therapy |

**System:** `http://terminology.hl7.org/CodeSystem/goal-category`

### priority (0..1)

Identifies the importance of the goal.

| Type | Description |
|------|-------------|
| CodeableConcept | Priority level |

**Value Set:** http://hl7.org/fhir/ValueSet/goal-priority (Preferred binding)

| Code | Display | Definition |
|------|---------|------------|
| high-priority | High Priority | Highest priority goal |
| medium-priority | Medium Priority | Medium priority goal |
| low-priority | Low Priority | Low priority goal |

**System:** `http://terminology.hl7.org/CodeSystem/goal-priority`

**Summary Element:** Yes

### description (1..1)

Code or text describing the goal being pursued. **Required element.**

| Type | Description |
|------|-------------|
| CodeableConcept | Goal description |

**Value Set:** http://hl7.org/fhir/ValueSet/clinical-findings (Example binding - SNOMED CT clinical findings)

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://snomed.info/sct` | SNOMED CT |
| `http://loinc.org` | LOINC |

**Summary Element:** Yes

**Implementation Note:** Description should be clear, measurable when possible, and patient-centered. May use coded concept from value set or free text in `.text` element.

### subject (1..1)

The patient, group, or organization for whom the goal is established. **Required element.**

| Type | Description |
|------|-------------|
| Reference(Patient \| Group \| Organization) | Who this goal is for |

**US Core:** Must reference US Core Patient Profile

**Summary Element:** Yes

### start[x] (0..1)

When the goal pursuit begins.

| Element | Type | Description |
|---------|------|-------------|
| startDate | date | Start date |
| startCodeableConcept | CodeableConcept | Event that triggers start |

**Summary Element:** Yes

**Implementation Note:** US Core requires startDate or target.dueDate be present.

### target (0..*)

Specific measurable targets for the goal.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| measure | CodeableConcept | 0..1 | Parameter being measured (e.g., blood pressure) |
| detail[x] | Multiple types | 0..1 | Target value (Quantity, Range, CodeableConcept, etc.) |
| dueDate | date | 0..1 | Target achievement date |
| dueDuration | Duration | 0..1 | Target achievement duration |

**Summary Element:** Yes

**Constraint:** If `target.detail[x]` is present, `target.measure` SHALL be present.

**detail[x] types:** Quantity, Range, CodeableConcept, String, Boolean, Integer, Ratio

### target.measure

The parameter whose value is being tracked (e.g., HbA1c, body weight, pain scale).

**Common Measure Codes (LOINC):**
| Code | Display |
|------|---------|
| 29463-7 | Body weight |
| 4548-4 | Hemoglobin A1c |
| 85354-9 | Blood pressure |
| 72166-2 | Tobacco smoking status |
| 9279-1 | Respiratory rate |

### target.detail[x]

The target value to achieve.

**Examples:**
```json
// Quantity target
"detailQuantity": {
  "value": 7.0,
  "unit": "%",
  "system": "http://unitsofmeasure.org",
  "code": "%"
}

// Range target
"detailRange": {
  "low": {
    "value": 120,
    "unit": "mmHg"
  },
  "high": {
    "value": 140,
    "unit": "mmHg"
  }
}

// CodeableConcept target
"detailCodeableConcept": {
  "coding": [{
    "system": "http://snomed.info/sct",
    "code": "8517006",
    "display": "Ex-smoker"
  }]
}
```

### statusDate (0..1)

When the goal status was last updated.

| Type | Description |
|------|-------------|
| date | Status date |

### statusReason (0..1)

Reason for current status.

| Type | Description |
|------|-------------|
| string | Explanation of status |

### expressedBy (0..1)

Who established the goal.

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| PractitionerRole \| RelatedPerson) | Goal author |

**Summary Element:** Yes

**Implementation Note:** US Core requires this as a Must Support element to capture USCDI provenance author data.

### addresses (0..*)

Health issues this goal addresses.

| Type | Description |
|------|-------------|
| Reference(Condition \| Observation \| MedicationStatement \| NutritionOrder \| ServiceRequest \| RiskAssessment) | Related health concerns |

**Summary Element:** Yes

### note (0..*)

Comments about the goal.

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

### outcomeCode (0..*)

What result was achieved.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Outcome codes |

**Value Set:** http://hl7.org/fhir/ValueSet/clinical-findings (Example binding)

### outcomeReference (0..*)

Observation that resulted from pursuing the goal.

| Type | Description |
|------|-------------|
| Reference(Observation)[] | Outcome observations |

## US Core Conformance Requirements

For US Core Goal profile compliance (v8.0.1):

### Required Elements
1. **SHALL** support `lifecycleStatus`
2. **SHALL** support `description`
3. **SHALL** support `subject` (Reference to US Core Patient)

### Must Support Elements
4. **SHALL** support `startDate` OR `target.dueDate` (at least one)
   - Server systems are not required to support both but SHALL support at least one
   - Client systems SHALL support both
5. **SHALL** support `expressedBy` (who set the goal)

### US Core-Specific Guidance
- Maturity Level: 3
- Standards Status: Trial-use
- Must Support Elements: 7 total
- Related SDOH guidance: Screening and Assessments guidance
- Related Provenance guidance: Basic Provenance guidance for individual-level author data

## Special Cases

### Social Determinants of Health (SDOH) Goals

SDOH goals use specific code sets from the SDOH Clinical Care IG:

```json
{
  "resourceType": "Goal",
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "410518001",
        "display": "Establish living arrangements"
      }
    ],
    "text": "Obtain stable housing within 3 months"
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/sdoh-clinicalcare/CodeSystem/SDOHCC-CodeSystemTemporaryCodes",
          "code": "housing-instability",
          "display": "Housing Instability"
        }
      ]
    }
  ],
  "addresses": [
    {
      "reference": "Condition/homelessness"
    }
  ]
}
```

### Patient vs Provider Goals

**Patient Goal:**
```json
{
  "expressedBy": {
    "reference": "Patient/example"
  }
}
```

**Provider Goal:**
```json
{
  "expressedBy": {
    "reference": "Practitioner/provider-example"
  }
}
```

**Negotiated Goal:** Both patient and provider contribute to goal formulation. Document via Provenance resource or note.

### Goal Without Specific Target

Goals may be qualitative without measurable targets:

```json
{
  "description": {
    "text": "Improve quality of life"
  },
  "target": []
}
```

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| patient | reference | Who this goal is for |
| lifecycle-status | token | proposed \| planned \| accepted \| active \| on-hold \| completed \| cancelled \| entered-in-error \| rejected |
| achievement-status | token | Progress status |
| category | token | Goal category |
| description | token | Goal description |
| target-date | date | Target achievement date |
| start-date | date | When goal pursuit began |

## Modifier Elements

The following elements are modifier elements:
- **lifecycleStatus** - Affects interpretation of whether the goal is active

## Compartments

The Goal resource is part of the following compartments:
- Patient

## References

- FHIR R4B Goal: https://hl7.org/fhir/R4B/goal.html
- US Core Goal Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal
- SNOMED CT: http://snomed.info/sct
- LOINC: http://loinc.org
- US Core IG v8.0.1: http://hl7.org/fhir/us/core/STU8/
