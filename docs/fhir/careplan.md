# FHIR R4B: CarePlan Resource

## Overview

The CarePlan resource describes the intention of how one or more practitioners intend to deliver care for a particular patient, group, or community over a period of time. It represents a consensus-driven dynamic plan that integrates multiple interventions proposed by multiple providers and disciplines for multiple conditions, serving as a blueprint shared by all Care Team Members to guide patient care.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | CarePlan |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 2 (Trial Use) |
| Security Category | Patient |
| Responsible Work Group | Patient Care |
| URL | https://hl7.org/fhir/R4B/careplan.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan |

## Scope and Usage

The CarePlan resource supports care coordination across providers and settings by documenting:
- Patient-centered care plans addressing prioritized concerns and goals
- Planned interventions and activities
- Integration of multiple Plans of Care from different providers/disciplines
- Progress tracking and outcome monitoring
- Shared decision-making and goal setting

**Key Use Cases:**
- Comprehensive care plans for chronic disease management
- Care coordination across care transitions
- Assessment and plan documentation
- Integration of multiple specialist treatment plans
- Care team communication and collaboration

## Boundaries and Relationships

**This resource should NOT be used for:**
- Generic clinical protocols (use PlanDefinition)
- Immunization-specific recommendations (use ImmunizationRecommendation)
- Individual goals without context (use Goal)
- Individual orders or requests (use ServiceRequest, MedicationRequest, etc.)

**Related Resources:**
- **Goal:** Referenced to show desired outcomes the plan aims to achieve
- **Condition:** Referenced in `addresses` to show conditions being managed
- **CareTeam:** Team members responsible for executing the plan
- **ServiceRequest/MedicationRequest/Procedure:** Activities planned or completed
- **Composition:** C-CDA Care Plan Document maps to Composition + CarePlan

## JSON Structure

```json
{
  "resourceType": "CarePlan",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan"
    ]
  },
  "text": {
    "status": "additional",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h3>Assessment</h3><p>Patient presents with respiratory insufficiency and productive cough. Current tobacco use noted as health concern.</p><h3>Plan</h3><p>Goals: Maintain oxygen saturation >92% through supplemental oxygen and pulmonary hygiene. Interventions: Oxygen therapy, elevation of head of bed, pulmonary toilet. Monitor progress with pulse oximetry.</p></div>"
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/careplan",
      "value": "careplan-12345"
    }
  ],
  "instantiatesCanonical": [
    "http://example.org/fhir/PlanDefinition/copd-pathway"
  ],
  "basedOn": [
    {
      "reference": "CarePlan/previous-plan"
    }
  ],
  "replaces": [
    {
      "reference": "CarePlan/old-plan"
    }
  ],
  "partOf": [
    {
      "reference": "CarePlan/master-plan"
    }
  ],
  "status": "active",
  "intent": "plan",
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
          "code": "assess-plan",
          "display": "Assessment and Plan of Treatment"
        }
      ]
    }
  ],
  "title": "Respiratory Care Plan",
  "description": "Care plan for management of respiratory insufficiency with COPD exacerbation",
  "subject": {
    "reference": "Patient/example",
    "display": "Amy Shaw"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "period": {
    "start": "2024-01-15",
    "end": "2024-04-15"
  },
  "created": "2024-01-15",
  "author": {
    "reference": "Practitioner/dr-smith",
    "display": "Dr. John Smith"
  },
  "contributor": [
    {
      "reference": "Practitioner/dr-smith"
    },
    {
      "reference": "Practitioner/nurse-jones"
    },
    {
      "reference": "Patient/example"
    }
  ],
  "careTeam": [
    {
      "reference": "CareTeam/respiratory-team"
    }
  ],
  "addresses": [
    {
      "reference": "Condition/copd",
      "display": "COPD"
    },
    {
      "reference": "Condition/respiratory-insufficiency",
      "display": "Respiratory insufficiency"
    }
  ],
  "supportingInfo": [
    {
      "reference": "Observation/smoking-status"
    }
  ],
  "goal": [
    {
      "reference": "Goal/oxygen-saturation"
    }
  ],
  "activity": [
    {
      "outcomeCodeableConcept": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "268910001",
              "display": "Patient's condition improved"
            }
          ]
        }
      ],
      "outcomeReference": [
        {
          "reference": "Observation/pulse-oximetry-result"
        }
      ],
      "detail": {
        "kind": "ServiceRequest",
        "instantiatesCanonical": [
          "http://example.org/fhir/ActivityDefinition/oxygen-therapy"
        ],
        "code": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "371907003",
              "display": "Oxygen administration by nasal cannula"
            }
          ]
        },
        "reasonCode": [
          {
            "coding": [
              {
                "system": "http://snomed.info/sct",
                "code": "409623005",
                "display": "Respiratory insufficiency"
              }
            ]
          }
        ],
        "reasonReference": [
          {
            "reference": "Condition/respiratory-insufficiency"
          }
        ],
        "goal": [
          {
            "reference": "Goal/oxygen-saturation"
          }
        ],
        "status": "in-progress",
        "statusReason": {
          "text": "Patient tolerating oxygen well"
        },
        "doNotPerform": false,
        "scheduledPeriod": {
          "start": "2024-01-15",
          "end": "2024-04-15"
        },
        "location": {
          "reference": "Location/patient-home"
        },
        "performer": [
          {
            "reference": "Practitioner/respiratory-therapist"
          }
        ],
        "productCodeableConcept": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "57613001",
              "display": "Oxygen"
            }
          ]
        },
        "dailyAmount": {
          "value": 2,
          "unit": "L/min",
          "system": "http://unitsofmeasure.org",
          "code": "L/min"
        },
        "quantity": {
          "value": 90,
          "unit": "days",
          "system": "http://unitsofmeasure.org",
          "code": "d"
        },
        "description": "Administer oxygen at 2L/min via nasal cannula continuously to maintain oxygen saturation >92%"
      }
    },
    {
      "reference": {
        "reference": "ServiceRequest/pulmonary-toilet"
      }
    }
  ],
  "note": [
    {
      "text": "Patient is motivated to improve respiratory status. Family support available for home oxygen management."
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External business identifiers for this care plan.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### instantiatesCanonical (0..*)

Canonical references to PlanDefinition or other canonical resources that this plan instantiates.

| Type | Description |
|------|-------------|
| canonical[] | Link to protocol or guideline |

**Reference Types:** PlanDefinition, Questionnaire, Measure, ActivityDefinition, OperationDefinition

### basedOn (0..*)

Care plans that this plan fulfills in whole or in part.

| Type | Description |
|------|-------------|
| Reference(CarePlan)[] | Fulfills care plan |

### replaces (0..*)

Care plans superseded by this plan.

| Type | Description |
|------|-------------|
| Reference(CarePlan)[] | Replaces care plan |

### partOf (0..*)

Larger care plan of which this is a component.

| Type | Description |
|------|-------------|
| Reference(CarePlan)[] | Part of care plan |

### status (1..1)

The current state of the care plan. This is a **required** and **modifier element**.

| Type | Description |
|------|-------------|
| code | Workflow status |

**Value Set:** http://hl7.org/fhir/ValueSet/request-status (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| draft | Draft | Plan is being developed |
| active | Active | Plan is ready to be acted upon |
| on-hold | On Hold | Plan temporarily suspended |
| revoked | Revoked | Plan no longer in use |
| completed | Completed | Plan achieved all goals or period ended |
| entered-in-error | Entered in Error | Plan created in error |
| unknown | Unknown | Status cannot be determined |

**System:** `http://hl7.org/fhir/request-status`

**Summary Element:** Yes

**Note:** status is a modifier element because it affects the interpretation of whether the plan is actionable.

### intent (1..1)

Indicates the level of authority/intentionality. This is a **required** and **modifier element**.

| Type | Description |
|------|-------------|
| code | Intent level |

**Value Set:** http://hl7.org/fhir/ValueSet/care-plan-intent (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| proposal | Proposal | Plan is a suggestion |
| plan | Plan | Plan is a commitment |
| order | Order | Plan is a request/demand for action |
| option | Option | Plan represents alternative or option |

**System:** `http://hl7.org/fhir/request-intent`

**Summary Element:** Yes

### category (0..*)

Classification of the type of care plan.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Care plan category |

**Value Set:** http://hl7.org/fhir/ValueSet/care-plan-category (Example binding)

**Common Categories:**
| Code | System | Display |
|------|--------|---------|
| assess-plan | http://hl7.org/fhir/us/core/CodeSystem/careplan-category | Assessment and Plan of Treatment |
| careteam | http://hl7.org/fhir/us/core/CodeSystem/careplan-category | Care Team |

**US Core:** Must support category with required slice for `assess-plan`

**Summary Element:** Yes

### title (0..1)

Human-friendly name for the care plan.

| Type | Description |
|------|-------------|
| string | Care plan title |

**Summary Element:** Yes

### description (0..1)

Summary of nature of plan.

| Type | Description |
|------|-------------|
| string | Care plan description |

**Summary Element:** Yes

### subject (1..1)

Who the care plan is for. **Required element.**

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Plan subject |

**US Core:** Must reference US Core Patient Profile

**Summary Element:** Yes

### encounter (0..1)

Encounter created as part of documenting the plan.

| Type | Description |
|------|-------------|
| Reference(Encounter) | Encounter context |

**Summary Element:** Yes

### period (0..1)

Time period plan covers.

| Element | Type | Description |
|---------|------|-------------|
| start | dateTime | Start date |
| end | dateTime | End date |

**Summary Element:** Yes

### created (0..1)

When the care plan was created.

| Type | Description |
|------|-------------|
| dateTime | Creation timestamp |

**Summary Element:** Yes

### author (0..1)

Who is the designated responsible party.

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| PractitionerRole \| Device \| RelatedPerson \| Organization \| CareTeam) | Plan author |

**Summary Element:** Yes

### contributor (0..*)

Who provided content for the care plan.

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| PractitionerRole \| Device \| RelatedPerson \| Organization \| CareTeam)[] | Plan contributors |

**US Core:** Must Support element for USCDI requirement

**Summary Element:** Yes

**Implementation Note:** Multiple contributors reflect collaborative care planning. May include patients, caregivers, and multidisciplinary team members.

### careTeam (0..*)

Care teams involved in the plan.

| Type | Description |
|------|-------------|
| Reference(CareTeam)[] | Care team members |

### addresses (0..*)

Health issues this plan addresses.

| Type | Description |
|------|-------------|
| Reference(Condition)[] | Conditions addressed |

**Summary Element:** Yes

**Implementation Note:** US Core recommends including references to US Core Condition resources.

### supportingInfo (0..*)

Information considered as part of plan formulation.

| Type | Description |
|------|-------------|
| Reference(Any)[] | Supporting information |

### goal (0..*)

Desired outcomes of the plan.

| Type | Description |
|------|-------------|
| Reference(Goal)[] | Plan goals |

**Implementation Note:** US Core recommends including references to US Core Goal resources.

### activity (0..*)

Actions to occur as part of the plan.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| outcomeCodeableConcept | CodeableConcept | 0..* | Activity results in coded form |
| outcomeReference | Reference(Any) | 0..* | Activity outcome observations |
| progress | Annotation | 0..* | Comments about activity status |
| reference | Reference | 0..1 | Link to activity details |
| detail | BackboneElement | 0..1 | Inline activity definition |

**Constraint (cpl-3):** Provide either `reference` OR `detail`, not both.

### activity.reference

Reference to ServiceRequest, MedicationRequest, Task, Appointment, CommunicationRequest, DeviceRequest, NutritionOrder, RequestGroup, VisionPrescription, or ImmunizationRecommendation.

| Type | Description |
|------|-------------|
| Reference | Activity request |

### activity.detail

Inline definition of a planned activity.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| kind | code | 0..1 | Activity type (Required binding) |
| instantiatesCanonical | canonical | 0..* | Protocol being followed |
| instantiatesUri | uri | 0..* | External protocol URI |
| code | CodeableConcept | 0..1 | Activity to perform |
| reasonCode | CodeableConcept | 0..* | Why activity should occur |
| reasonReference | Reference | 0..* | References to conditions/observations |
| goal | Reference(Goal) | 0..* | Goals activity works toward |
| status | code | 1..1 | Activity status (Required binding) |
| statusReason | CodeableConcept | 0..1 | Reason for status |
| doNotPerform | boolean | 0..1 | Activity should not occur |
| scheduled[x] | Timing \| Period \| string | 0..1 | When activity occurs |
| location | Reference(Location) | 0..1 | Where activity occurs |
| performer | Reference | 0..* | Who performs activity |
| product[x] | CodeableConcept \| Reference(Medication \| Substance) | 0..1 | What is administered/supplied |
| dailyAmount | Quantity | 0..1 | Daily quantity |
| quantity | Quantity | 0..1 | Total quantity |
| description | string | 0..1 | Activity description |

**activity.detail.kind Value Set:**

| Code | Display |
|------|---------|
| Appointment | Appointment |
| CommunicationRequest | CommunicationRequest |
| DeviceRequest | DeviceRequest |
| MedicationRequest | MedicationRequest |
| NutritionOrder | NutritionOrder |
| Task | Task |
| ServiceRequest | ServiceRequest |
| VisionPrescription | VisionPrescription |

**activity.detail.status Value Set:**

| Code | Display |
|------|---------|
| not-started | Not Started |
| scheduled | Scheduled |
| in-progress | In Progress |
| on-hold | On Hold |
| completed | Completed |
| cancelled | Cancelled |
| stopped | Stopped |
| unknown | Unknown |
| entered-in-error | Entered in Error |

**activity.detail.doNotPerform** is a **modifier element** indicating the activity should NOT occur.

### note (0..*)

Comments about the plan.

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

## US Core Conformance Requirements

For US Core CarePlan profile compliance (v8.0.1):

### Required Elements
1. **SHALL** support `status`
2. **SHALL** support `intent`
3. **SHALL** support `category` with at least one coding from assess-plan category
4. **SHALL** support `subject` (Reference to US Core Patient)

### Must Support Elements
5. **SHALL** support `text` (Narrative)
6. **SHALL** support `text.status`
7. **SHALL** support `text.div` (XHTML content)
8. **SHALL** support `contributor` (USCDI requirement)

### US Core-Specific Guidance
- **Maturity Level:** 3
- **Standards Status:** Trial-use
- **Category:** Must include assess-plan slice with fixed code from US Core careplan-category CodeSystem
- **Narrative Relaxation:** Sophisticated systems may discretely encode plans without requiring all data in narrative
- **Related Resources:** Recommend including Goal and Condition references
- **Search:** Must support patient + category searches

## Special Cases

### Assessment and Plan CarePlan

The most common US Core use case documents assessment and plan of treatment:

```json
{
  "resourceType": "CarePlan",
  "text": {
    "status": "additional",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h3>Assessment</h3><p>Type 2 diabetes poorly controlled. HbA1c 8.5%.</p><h3>Plan</h3><p>Increase metformin to 1000mg BID. Diabetes education referral. Follow-up in 3 months for repeat HbA1c.</p></div>"
  },
  "status": "active",
  "intent": "plan",
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
          "code": "assess-plan"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/example"
  },
  "contributor": [
    {
      "reference": "Practitioner/endocrinologist"
    }
  ]
}
```

### Activity with Reference vs Detail

**Using Reference (preferred for discrete activities):**
```json
{
  "activity": [
    {
      "reference": {
        "reference": "MedicationRequest/metformin"
      }
    }
  ]
}
```

**Using Detail (for inline definition):**
```json
{
  "activity": [
    {
      "detail": {
        "kind": "MedicationRequest",
        "code": {
          "coding": [
            {
              "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
              "code": "860975",
              "display": "metformin 1000 MG Oral Tablet"
            }
          ]
        },
        "status": "in-progress",
        "doNotPerform": false
      }
    }
  ]
}
```

### Prohibited Activities

Use `doNotPerform` to document activities that should NOT occur:

```json
{
  "activity": [
    {
      "detail": {
        "kind": "MedicationRequest",
        "code": {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "372584003",
              "display": "Metformin"
            }
          ]
        },
        "status": "cancelled",
        "doNotPerform": true,
        "statusReason": {
          "text": "Patient developed acute kidney injury"
        }
      }
    }
  ]
}
```

### Care Plan Relationships

**Based On (fulfills another plan):**
```json
{
  "basedOn": [
    {
      "reference": "CarePlan/diabetes-protocol"
    }
  ]
}
```

**Replaces (supersedes old plan):**
```json
{
  "replaces": [
    {
      "reference": "CarePlan/previous-diabetes-plan"
    }
  ]
}
```

**Part Of (component of larger plan):**
```json
{
  "partOf": [
    {
      "reference": "CarePlan/comprehensive-chronic-disease-plan"
    }
  ]
}
```

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| patient | reference | Who the care plan is for |
| category | token | Type of plan |
| status | token | Plan status |
| date | date | Time period plan covers (period.start or period.end) |
| care-team | reference | Care team involved |
| condition | reference | Conditions addressed |
| encounter | reference | Encounter context |
| goal | reference | Goals addressed |
| instantiates-canonical | reference | Instantiates protocol |
| intent | token | Proposal, plan, order, option |
| part-of | reference | Part of larger plan |
| performer | reference | Matches performer |
| replaces | reference | Supersedes plan |
| subject | reference | Who plan is for |
| based-on | reference | Fulfills plan |
| activity-code | token | Activity code |
| activity-date | date | Activity scheduled date |
| activity-reference | reference | Activity reference |

## Modifier Elements

The following elements are modifier elements:
- **status** - Affects interpretation of whether the plan is actionable
- **intent** - Affects authority level
- **activity.detail.doNotPerform** - Indicates activity should NOT occur

## Compartments

The CarePlan resource is part of the following compartments:
- Patient
- Encounter

## References

- FHIR R4B CarePlan: https://hl7.org/fhir/R4B/careplan.html
- US Core CarePlan Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan
- C-CDA on FHIR Care Plan Document: https://hl7.org/fhir/us/ccda/StructureDefinition-Care-Plan-Document.html
- US Core IG v8.0.1: http://hl7.org/fhir/us/core/STU8/
