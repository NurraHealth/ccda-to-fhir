# FHIR R4B: Encounter Resource

## Overview

The Encounter resource represents an interaction between a patient and healthcare provider(s) for the purpose of providing healthcare service(s) or assessing the health status of a patient. It records actual activities that occurred, distinguishing it from the Appointment resource which captures planned activities. This includes ambulatory encounters (outpatient), inpatient stays, emergency room visits, home health visits, and virtual encounters.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Encounter |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Patient Administration |
| URL | https://hl7.org/fhir/R4B/encounter.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter |

## Scope and Usage

**Key Characteristics:**
- Characterized by setting (ambulatory, emergency, home health, inpatient, virtual)
- Encompasses pre-admission through discharge lifecycle
- Not all elements will be relevant in all settings
- Admission/discharge information stored in separate admission component
- Organizations vary on what business events trigger new Encounter instances
- Encounters can be aggregated under other Encounters via `partOf` element

**Status Management:**
- Status tracks overall encounter state
- `subjectStatus` specifically tracks patient status (arrived, triaged, receiving-care, discharged, departed, on-leave)
- EncounterHistory resource provides detailed status transition tracking

## JSON Structure

```json
{
  "resourceType": "Encounter",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/encounter",
      "value": "2a620155-9d11-439e-92b3-5d9815ff4de8"
    }
  ],
  "status": "finished",
  "statusHistory": [
    {
      "status": "arrived",
      "period": {
        "start": "2020-03-01T09:00:00-05:00",
        "end": "2020-03-01T09:05:00-05:00"
      }
    },
    {
      "status": "in-progress",
      "period": {
        "start": "2020-03-01T09:05:00-05:00",
        "end": "2020-03-01T10:00:00-05:00"
      }
    },
    {
      "status": "finished",
      "period": {
        "start": "2020-03-01T10:00:00-05:00"
      }
    }
  ],
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB",
    "display": "ambulatory"
  },
  "classHistory": [
    {
      "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory"
      },
      "period": {
        "start": "2020-03-01T09:00:00-05:00",
        "end": "2020-03-01T10:00:00-05:00"
      }
    }
  ],
  "type": [
    {
      "coding": [
        {
          "system": "http://www.ama-assn.org/go/cpt",
          "code": "99213",
          "display": "Office or other outpatient visit"
        }
      ],
      "text": "Office Visit"
    }
  ],
  "serviceType": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "394802001",
        "display": "General medicine"
      }
    ]
  },
  "priority": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
        "code": "R",
        "display": "routine"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "episodeOfCare": [
    {
      "reference": "EpisodeOfCare/example"
    }
  ],
  "basedOn": [
    {
      "reference": "ServiceRequest/example"
    }
  ],
  "participant": [
    {
      "type": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
              "code": "ATND",
              "display": "attender"
            }
          ]
        }
      ],
      "period": {
        "start": "2020-03-01T09:00:00-05:00",
        "end": "2020-03-01T10:00:00-05:00"
      },
      "individual": {
        "reference": "Practitioner/example",
        "display": "Dr. Adam Careful"
      }
    }
  ],
  "appointment": [
    {
      "reference": "Appointment/example"
    }
  ],
  "period": {
    "start": "2020-03-01T09:00:00-05:00",
    "end": "2020-03-01T10:00:00-05:00"
  },
  "length": {
    "value": 60,
    "unit": "minutes",
    "system": "http://unitsofmeasure.org",
    "code": "min"
  },
  "reasonCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "21522001",
          "display": "Abdominal pain"
        }
      ]
    }
  ],
  "reasonReference": [
    {
      "reference": "Condition/example"
    }
  ],
  "diagnosis": [
    {
      "condition": {
        "reference": "Condition/uri",
        "display": "Acute upper respiratory infection"
      },
      "use": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "code": "AD",
            "display": "Admission diagnosis"
          }
        ]
      },
      "rank": 1
    }
  ],
  "account": [
    {
      "reference": "Account/example"
    }
  ],
  "hospitalization": {
    "preAdmissionIdentifier": {
      "system": "http://hospital.example.org/preadmit",
      "value": "PRE12345"
    },
    "origin": {
      "reference": "Location/home"
    },
    "admitSource": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/admit-source",
          "code": "gp",
          "display": "General Practitioner referral"
        }
      ]
    },
    "reAdmission": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v2-0092",
          "code": "R",
          "display": "Readmission"
        }
      ]
    },
    "dietPreference": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/diet",
            "code": "vegetarian",
            "display": "Vegetarian"
          }
        ]
      }
    ],
    "specialCourtesy": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v3-EncounterSpecialCourtesy",
            "code": "VIP",
            "display": "very important person"
          }
        ]
      }
    ],
    "specialArrangement": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/encounter-special-arrangements",
            "code": "wheel",
            "display": "Wheelchair"
          }
        ]
      }
    ],
    "destination": {
      "reference": "Location/home"
    },
    "dischargeDisposition": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
          "code": "home",
          "display": "Home"
        }
      ]
    }
  },
  "location": [
    {
      "location": {
        "reference": "Location/example",
        "display": "Community Health and Hospitals"
      },
      "status": "completed",
      "physicalType": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
            "code": "wa",
            "display": "Ward"
          }
        ]
      },
      "period": {
        "start": "2020-03-01T09:00:00-05:00",
        "end": "2020-03-01T10:00:00-05:00"
      }
    }
  ],
  "serviceProvider": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "partOf": {
    "reference": "Encounter/parent"
  }
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this encounter.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### status (1..1)

The current status of the encounter. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | planned \| arrived \| triaged \| in-progress \| onleave \| finished \| cancelled \| entered-in-error \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/encounter-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| planned | Planned | Encounter has been planned |
| arrived | Arrived | Patient has arrived |
| triaged | Triaged | Patient has been triaged |
| in-progress | In Progress | Encounter is in progress |
| onleave | On Leave | Patient temporarily away |
| finished | Finished | Encounter has ended |
| cancelled | Cancelled | Encounter was cancelled |
| entered-in-error | Entered in Error | Entered in error |
| unknown | Unknown | Status unknown |

### subjectStatus (0..1)

Patient's status within the encounter.

| Type | Description |
|------|-------------|
| CodeableConcept | Subject/patient status (arrived, departed, triaged, receiving-care, on-leave, etc.) |

### statusHistory (0..*)

| Element | Type | Description |
|---------|------|-------------|
| status | code | Previous status |
| period | Period | When status was active |

### class (1..1)

The classification of the encounter.

| Type | Description |
|------|-------------|
| Coding | ActCode (AMB, EMER, IMP, etc.) |

**Encounter Class Codes:**
| Code | Display | Definition |
|------|---------|------------|
| AMB | ambulatory | Outpatient encounter |
| EMER | emergency | Emergency room encounter |
| FLD | field | Field encounter |
| HH | home health | Home health encounter |
| IMP | inpatient encounter | Inpatient stay |
| ACUTE | inpatient acute | Acute inpatient |
| NONAC | inpatient non-acute | Non-acute inpatient |
| OBSENC | observation encounter | Observation stay |
| PRENC | pre-admission | Pre-admission |
| SS | short stay | Short stay |
| VR | virtual | Virtual/telehealth encounter |

**System:** `http://terminology.hl7.org/CodeSystem/v3-ActCode`

### classHistory (0..*)

| Element | Type | Description |
|---------|------|-------------|
| class | Coding | Previous class |
| period | Period | When class was active |

### type (0..*)

The specific type of encounter.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Encounter type codes |

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://www.ama-assn.org/go/cpt` | CPT |
| `http://snomed.info/sct` | SNOMED CT |

### serviceType (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Type of service being provided |

### priority (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Indicates urgency of encounter |

**Priority Codes:**
| Code | Display |
|------|---------|
| A | ASAP |
| CR | Callback results |
| EL | Elective |
| EM | Emergency |
| P | Preop |
| PRN | As needed |
| R | Routine |
| RR | Rush reporting |
| S | Stat |
| T | Timing critical |
| UD | Use as directed |
| UR | Urgent |

### subject (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Who the encounter is for (may be absent for case meetings) |

### careTeam (0..*)

| Type | Description |
|------|-------------|
| Reference(CareTeam)[] | Allocated care team members |

### virtualService (0..*)

| Type | Description |
|------|-------------|
| VirtualServiceDetail[] | Conference call/virtual meeting details |

### plannedStartDate (0..1)

| Type | Description |
|------|-------------|
| dateTime | Planned admission date |

### plannedEndDate (0..1)

| Type | Description |
|------|-------------|
| dateTime | Planned discharge date |

### actualPeriod (0..1)

| Type | Description |
|------|-------------|
| Period | Actual start and end times of the encounter |

### episodeOfCare (0..*)

| Type | Description |
|------|-------------|
| Reference(EpisodeOfCare) | Episode of care |

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference(ServiceRequest) | Request that initiated the encounter |

### participant (0..*)

List of people responsible for providing service.

| Element | Type | Description |
|---------|------|-------------|
| type | CodeableConcept[] | Role of participant |
| period | Period | Time of involvement |
| actor | Reference | Who was involved (Practitioner, PractitionerRole, RelatedPerson, Device, HealthcareService, Patient, Group) |

**Constraints:**
- Type required when no explicit actor specified
- Type cannot be provided for patient/group participants

**Participant Type Codes:**
| Code | Display | System |
|------|---------|--------|
| ADM | admitter | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| ATND | attender | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| CON | consultant | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| DIS | discharger | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| REF | referrer | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| SPRF | secondary performer | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| PPRF | primary performer | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |
| PART | participation | http://terminology.hl7.org/CodeSystem/v3-ParticipationType |

### appointment (0..*)

| Type | Description |
|------|-------------|
| Reference(Appointment) | Appointment(s) that scheduled this |

### period (0..1)

| Type | Description |
|------|-------------|
| Period | Start and end time of encounter |

### length (0..1)

| Type | Description |
|------|-------------|
| Duration | Length of encounter |

### reason (0..*)

Medical reasons expected to be addressed.

| Element | Type | Description |
|---------|------|-------------|
| use | CodeableConcept[] | What the reason applies to |
| value | CodeableReference[] | Reason as CodeableReference (Condition, DiagnosticReport, Observation, ImmunizationRecommendation, Procedure) |

### dietPreference (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Patient-reported diet preferences |

### specialArrangement (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Equipment/accommodation requests |

### specialCourtesy (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | VIP/courtesy considerations |

### diagnosis (0..*)

| Element | Type | Description |
|---------|------|-------------|
| condition | Reference(Condition \| Procedure) | Condition/procedure |
| use | CodeableConcept | Role of diagnosis |
| rank | positiveInt | Ranking of diagnosis |

**Diagnosis Role Codes:**
| Code | Display |
|------|---------|
| AD | Admission diagnosis |
| DD | Discharge diagnosis |
| CC | Chief complaint |
| CM | Comorbidity diagnosis |
| pre-op | pre-op diagnosis |
| post-op | post-op diagnosis |
| billing | Billing |

### account (0..*)

| Type | Description |
|------|-------------|
| Reference(Account) | Billing account |

### admission (0..1)

Details about healthcare service stay (admission/discharge).

| Element | Type | Description |
|---------|------|-------------|
| preAdmissionIdentifier | Identifier | Pre-admission tracking ID |
| origin | Reference(Location \| Organization) | Where patient came from (referring location) |
| admitSource | CodeableConcept | From where patient admitted (referral, transfer) |
| reAdmission | CodeableConcept | Readmission indicator |
| destination | Reference(Location \| Organization) | Where patient goes after discharge |
| dischargeDisposition | CodeableConcept | Post-discharge placement category |

**Constraint:** Admission period should match encounter period.

**Discharge Disposition Codes:**
| Code | Display |
|------|---------|
| home | Home |
| alt-home | Alternative home |
| other-hcf | Other healthcare facility |
| hosp | Hospice |
| long | Long-term care |
| aadvice | Left against advice |
| exp | Expired |
| psy | Psychiatric hospital |
| rehab | Rehabilitation |
| snf | Skilled nursing facility |
| oth | Other |

### location (0..*)

Locations where patient has been.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| location | Reference(Location) | 1..1 | Location reference (Required) |
| status | code | 0..1 | planned \| active \| reserved \| completed |
| form | CodeableConcept | 0..1 | Physical form of location (bed, room, ward, virtual) |
| period | Period | 0..1 | Time during encounter at this location |

### serviceProvider (0..1)

| Type | Description |
|------|-------------|
| Reference(Organization) | Organization responsible for encounter |

### partOf (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter) | Parent encounter |

## US Core Conformance Requirements

For US Core Encounter profile compliance:

1. **SHALL** support `identifier`
2. **SHALL** support `status`
3. **SHALL** support `class`
4. **SHALL** support `type`
5. **SHALL** support `subject`
6. **SHALL** support `participant`
7. **SHALL** support `period`
8. **SHALL** support `reasonCode`
9. **SHALL** support `hospitalization.dischargeDisposition`
10. **SHALL** support `location`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | planned \| arrived \| triaged \| in-progress \| onleave \| finished \| cancelled \| entered-in-error \| unknown |
| class | token | Classification of encounter |
| type | token | Specific type of encounter |
| subject | reference | The patient or group present |
| patient | reference | The patient present |
| date | date | A date within the period |
| identifier | token | Identifier for the encounter |
| location | reference | Location(s) |
| participant | reference | Persons involved |
| participant-type | token | Role of participant |
| practitioner | reference | Practitioner involved |
| diagnosis | reference | Condition(s) diagnosed |
| reason-code | token | Coded reason |
| reason-reference | reference | Reason for encounter |
| service-provider | reference | Organization responsible |
| part-of | reference | Parent encounter |
| based-on | reference | Service request |
| appointment | reference | Appointment |
| length | quantity | Length of encounter |
| account | reference | Billing account |
| special-arrangement | token | Special arrangements |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| enc-1 | Type required when no explicit actor specified in participant |
| enc-2 | Type cannot be provided for patient/group participants |
| enc-3 | Admission period should match encounter period |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the encounter

## Compartments

The Encounter resource is part of the following compartments:
- Encounter
- Group
- Patient
- Practitioner
- RelatedPerson

## References

- FHIR R4B Encounter: https://hl7.org/fhir/R4B/encounter.html
- US Core Encounter Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter
- CPT: https://www.ama-assn.org/practice-management/cpt
- SNOMED CT: http://snomed.info/sct
