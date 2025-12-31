# FHIR R4B: MedicationRequest Resource

## Overview

The MedicationRequest resource represents an order or request for both supply of the medication and instructions for administration to a patient. It generalizes across inpatient and outpatient settings, including prescriptions, medication orders, and medication-related requests.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | MedicationRequest |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Pharmacy |
| URL | https://hl7.org/fhir/R4B/medicationrequest.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest |

## Scope and Usage

**Covers:**
- Inpatient medication orders
- Community/outpatient prescriptions
- Over-the-counter medications
- Total parenteral nutrition
- Diet/vitamin supplements
- Medication-related devices (prefilled syringes, PCA devices)

**Excludes:**
- Heparin-coated stents and non-medication devices
- Eyeglasses and diet ordering
- Non-medication supplies

**Key Distinctions:**
- **MedicationRequest:** The order/prescription itself
- **MedicationDispense:** Fulfillment of the order
- **MedicationAdministration:** Actual consumption/administration
- **MedicationStatement:** Reported medication usage

**Workflow Notes:**
- Single medication per request; use multiple instances for compound orders
- Task resource handles fulfillment details
- Multiple MedicationRequests can group via identical groupIdentifier
- RequestOrchestration manages complex timing/sequencing dependencies
- When doNotPerform=true: no dispense/administration occurs; active conflicting orders should cancel

## JSON Structure

```json
{
  "resourceType": "MedicationRequest",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/medication",
      "value": "cdbd33f0-6cde-11db-9fe1-0800200c9a66"
    }
  ],
  "status": "active",
  "statusReason": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-status-reason",
        "code": "altchoice",
        "display": "Try another treatment first"
      }
    ]
  },
  "intent": "order",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category",
          "code": "outpatient",
          "display": "Outpatient"
        }
      ]
    }
  ],
  "priority": "routine",
  "doNotPerform": false,
  "reportedBoolean": false,
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "314076",
        "display": "Lisinopril 10 MG Oral Tablet"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "00591-3772-01",
        "display": "Lisinopril 10mg Tab"
      }
    ],
    "text": "Lisinopril 10 MG Oral Tablet"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "supportingInformation": [
    {
      "reference": "Observation/weight"
    }
  ],
  "authoredOn": "2020-03-01",
  "requester": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "performer": {
    "reference": "Practitioner/example"
  },
  "performerType": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "46255001",
        "display": "Pharmacist"
      }
    ]
  },
  "recorder": {
    "reference": "Practitioner/example"
  },
  "reasonCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "59621000",
          "display": "Essential hypertension"
        }
      ]
    }
  ],
  "reasonReference": [
    {
      "reference": "Condition/hypertension"
    }
  ],
  "instantiatesCanonical": [
    "http://example.org/fhir/ActivityDefinition/hypertension-treatment"
  ],
  "basedOn": [
    {
      "reference": "CarePlan/example"
    }
  ],
  "groupIdentifier": {
    "system": "http://hospital.example.org/prescription",
    "value": "RX123456"
  },
  "courseOfTherapyType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-course-of-therapy",
        "code": "continuous",
        "display": "Continuous long term therapy"
      }
    ]
  },
  "insurance": [
    {
      "reference": "Coverage/example"
    }
  ],
  "note": [
    {
      "text": "Patient should monitor blood pressure daily"
    }
  ],
  "dosageInstruction": [
    {
      "sequence": 1,
      "text": "Take 1 tablet by mouth once daily",
      "additionalInstruction": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "311504000",
              "display": "With or after food"
            }
          ]
        }
      ],
      "patientInstruction": "Take one tablet daily with or after food",
      "timing": {
        "repeat": {
          "frequency": 1,
          "period": 1,
          "periodUnit": "d"
        },
        "code": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation",
              "code": "QD",
              "display": "Every Day"
            }
          ]
        }
      },
      "asNeededBoolean": false,
      "site": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "181220002",
            "display": "Mouth"
          }
        ]
      },
      "route": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "26643006",
            "display": "Oral route"
          }
        ]
      },
      "method": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "421521009",
            "display": "Swallow"
          }
        ]
      },
      "doseAndRate": [
        {
          "type": {
            "coding": [
              {
                "system": "http://terminology.hl7.org/CodeSystem/dose-rate-type",
                "code": "ordered",
                "display": "Ordered"
              }
            ]
          },
          "doseQuantity": {
            "value": 1,
            "unit": "tablet",
            "system": "http://unitsofmeasure.org",
            "code": "{tbl}"
          }
        }
      ],
      "maxDosePerPeriod": {
        "numerator": {
          "value": 1,
          "unit": "tablet"
        },
        "denominator": {
          "value": 1,
          "unit": "day"
        }
      }
    }
  ],
  "dispenseRequest": {
    "initialFill": {
      "quantity": {
        "value": 30,
        "unit": "tablet",
        "system": "http://unitsofmeasure.org",
        "code": "{tbl}"
      },
      "duration": {
        "value": 30,
        "unit": "day",
        "system": "http://unitsofmeasure.org",
        "code": "d"
      }
    },
    "dispenseInterval": {
      "value": 30,
      "unit": "day",
      "system": "http://unitsofmeasure.org",
      "code": "d"
    },
    "validityPeriod": {
      "start": "2020-03-01",
      "end": "2021-03-01"
    },
    "numberOfRepeatsAllowed": 3,
    "quantity": {
      "value": 30,
      "unit": "tablet",
      "system": "http://unitsofmeasure.org",
      "code": "{tbl}"
    },
    "expectedSupplyDuration": {
      "value": 30,
      "unit": "day",
      "system": "http://unitsofmeasure.org",
      "code": "d"
    },
    "performer": {
      "reference": "Organization/pharmacy"
    }
  },
  "substitution": {
    "allowedBoolean": true,
    "reason": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
          "code": "CT",
          "display": "Continuing therapy"
        }
      ]
    }
  },
  "priorPrescription": {
    "reference": "MedicationRequest/previous"
  },
  "detectedIssue": [
    {
      "reference": "DetectedIssue/drug-interaction"
    }
  ],
  "eventHistory": [
    {
      "reference": "Provenance/example"
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this medication request.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### status (1..1)

The status of the prescription. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | active \| on-hold \| ended \| stopped \| completed \| cancelled \| entered-in-error \| draft \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/medicationrequest-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| active | Active | Prescription is currently active |
| on-hold | On Hold | Temporarily suspended |
| ended | Ended | Actions ended but not necessarily completed |
| stopped | Stopped | Discontinued |
| completed | Completed | All actions completed |
| cancelled | Cancelled | Cancelled before completion |
| entered-in-error | Entered in Error | Entered in error |
| draft | Draft | Not yet active |
| unknown | Unknown | Status unknown |

### statusChanged (0..1)

| Type | Description |
|------|-------------|
| dateTime | When the status was last modified |

### statusReason (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Reason for current status |

### intent (1..1)

The intent of the prescription. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | proposal \| plan \| order \| original-order \| reflex-order \| filler-order \| instance-order \| option |

**Value Set:** http://hl7.org/fhir/ValueSet/medicationrequest-intent (Required binding)

**Intent Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| proposal | Proposal | Suggestion or recommendation |
| plan | Plan | Intended but not yet ordered |
| order | Order | Authorized prescription |
| original-order | Original Order | First in a sequence |
| reflex-order | Reflex Order | Automatic follow-up |
| filler-order | Filler Order | Fulfillment request |
| instance-order | Instance Order | Single instance |
| option | Option | One of several alternatives |

### category (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Type of medication request |

**Category Codes:**
| Code | Display |
|------|---------|
| inpatient | Inpatient |
| outpatient | Outpatient |
| community | Community |
| discharge | Discharge |

### priority (0..1)

| Type | Values |
|------|--------|
| code | routine \| urgent \| asap \| stat |

### doNotPerform (0..1)

This is a **modifier element**.

| Type | Description |
|------|-------------|
| boolean | Indicates medication should NOT be taken |

**Note:** When true, no dispense/administration occurs; active conflicting orders should cancel.

### reportedBoolean / reportedReference (0..1)

| Type | Description |
|------|-------------|
| boolean \| Reference | Whether information is from secondary source |

### medication (1..1)

The medication being requested.

| Type | Description |
|------|-------------|
| CodeableReference(Medication) | Medication code or reference to Medication resource |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-codes (SNOMED CT, Example binding)

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| `http://hl7.org/fhir/sid/ndc` | NDC |
| `http://snomed.info/sct` | SNOMED CT |

### subject (1..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Required reference to patient |

### encounter (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter) | Associated encounter |

### authoredOn (0..1)

| Type | Description |
|------|-------------|
| dateTime | When request was authored |

### requester (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| Patient \| RelatedPerson \| Device) | Who ordered |

### performer (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| Patient \| Device \| RelatedPerson \| CareTeam) | Intended performer |

### recorder (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole) | Who entered the request |

### reason (0..*)

Justification for the medication request.

| Type | Description |
|------|-------------|
| CodeableReference[] | Reason as CodeableReference (Condition, Observation, DiagnosticReport, Procedure, AllergyIntolerance) |

### informationSource (0..*)

| Type | Description |
|------|-------------|
| Reference[] | Reporter if not the requester (Patient, Practitioner, PractitionerRole, RelatedPerson, Organization) |

### courseOfTherapyType (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Overall pattern of medication administration |

**Value Set:** http://hl7.org/fhir/ValueSet/medicationrequest-course-of-therapy (Extensible binding)

**Course of Therapy Codes:**
| Code | Display |
|------|---------|
| continuous | Continuous long term therapy |
| acute | Short course (acute) therapy |
| seasonal | Seasonal therapy |

### effectiveTiming[x] (0..1)

| Element | Type | Description |
|---------|------|-------------|
| effectiveDosePeriod | Period | Duration for medication use |
| effectiveDoseRange | Range | Duration range for medication use |

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

### dosageInstruction (0..*)

How the medication should be taken.

| Element | Type | Description |
|---------|------|-------------|
| sequence | integer | Order of dosage instructions |
| text | string | Free text dosage instructions |
| additionalInstruction | CodeableConcept[] | Supplemental instructions |
| patientInstruction | string | Patient-oriented instructions |
| timing | Timing | When medication should be administered |
| asNeeded[x] | boolean or CodeableConcept | PRN indicator |
| site | CodeableConcept | Body site for administration |
| route | CodeableConcept | How drug enters body |
| method | CodeableConcept | Technique for administering |
| doseAndRate | Element[] | Dose and rate information |
| maxDosePerPeriod | Ratio | Upper limit on dose |
| maxDosePerAdministration | SimpleQuantity | Max dose per administration |
| maxDosePerLifetime | SimpleQuantity | Max lifetime dose |

### dosageInstruction.timing

| Element | Type | Description |
|---------|------|-------------|
| event | dateTime[] | Specific times |
| repeat.frequency | integer | Times per period |
| repeat.period | decimal | Duration of one period |
| repeat.periodUnit | code | s \| min \| h \| d \| wk \| mo \| a |
| repeat.dayOfWeek | code[] | mon \| tue \| wed \| thu \| fri \| sat \| sun |
| repeat.timeOfDay | time[] | Time of day |
| repeat.when | code[] | Event timing (AC, PC, etc.) |
| code | CodeableConcept | Timing code (QD, BID, etc.) |

**Common Timing Codes:**
| Code | Display | System |
|------|---------|--------|
| QD | Every Day | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| BID | Twice a Day | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| TID | Three Times a Day | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| QID | Four Times a Day | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| Q4H | Every 4 Hours | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| Q6H | Every 6 Hours | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| QHS | Every Night at Bedtime | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |
| PRN | As Needed | http://terminology.hl7.org/CodeSystem/v3-GTSAbbreviation |

### dosageInstruction.route

**Common Route Codes (SNOMED):**
| Code | Display |
|------|---------|
| 26643006 | Oral route |
| 47625008 | Intravenous route |
| 78421000 | Intramuscular route |
| 34206005 | Subcutaneous route |
| 6064005 | Topical route |
| 46713006 | Nasal route |
| 37161004 | Rectal route |
| 418136008 | Sublingual route |
| 45890007 | Transdermal route |
| 127492001 | Inhalation route |

### dispenseRequest (0..1)

| Element | Type | Description |
|---------|------|-------------|
| initialFill | Element | First fill details |
| initialFill.quantity | SimpleQuantity | First dispense quantity |
| initialFill.duration | Duration | First dispense duration |
| dispenseInterval | Duration | Min period between dispenses |
| validityPeriod | Period | Time period prescription is valid |
| numberOfRepeatsAllowed | unsignedInt | Number of refills (excludes initial dispense) |
| quantity | SimpleQuantity | Amount to dispense per fill |
| expectedSupplyDuration | Duration | Days supply per dispense |
| dispenser | Reference(Organization) | Intended dispensing organization |
| dispenserInstruction | Annotation[] | Counseling/special instructions for dispenser |
| doseAdministrationAid | CodeableConcept | Adherence packaging type |
| destination | Reference(Location) | Delivery location |

### substitution (0..1)

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| allowed[x] | boolean or CodeableConcept | 1..1 | Whether substitution allowed (Required) |
| reason | CodeableConcept | 0..1 | Why should/should not substitute |

**allowed Value Set:** http://terminology.hl7.org/ValueSet/v3-ActSubstanceAdminSubstitutionCode (Preferred binding)

## US Core Conformance Requirements

For US Core MedicationRequest profile compliance:

1. **SHALL** support `status`
2. **SHALL** support `intent`
3. **SHALL** support `medication[x]`
4. **SHALL** support `subject`
5. **SHALL** support `authoredOn`
6. **SHALL** support `requester`
7. **SHOULD** support `dosageInstruction`
8. **SHOULD** support `dosageInstruction.text`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | active \| on-hold \| cancelled \| completed \| entered-in-error \| stopped \| draft \| unknown |
| intent | token | proposal \| plan \| order \| original-order \| reflex-order \| filler-order \| instance-order \| option |
| patient | reference | Patient reference |
| subject | reference | Subject reference |
| encounter | reference | Associated encounter |
| medication | reference | Medication reference |
| code | token | Medication code |
| authoredon | date | When request was authored |
| requester | reference | Who requested |
| category | token | Category of request |
| priority | token | routine \| urgent \| asap \| stat |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the request
- **intent** - Determines the level of authority
- **doNotPerform** - Reverses the meaning (medication should NOT be taken)

## Compartments

The MedicationRequest resource is part of the following compartments:
- Encounter
- Group
- Patient
- Practitioner

## References

- FHIR R4B MedicationRequest: https://hl7.org/fhir/R4B/medicationrequest.html
- US Core MedicationRequest Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- SNOMED CT: http://snomed.info/sct
