# FHIR R4B: Observation Resource

## Overview

The Observation resource is used to capture measurements and simple assertions made about a patient, device, or other subject. It functions as an event resource within FHIR's workflow framework, supporting diagnosis, monitoring, and baseline determination. This includes vital signs, laboratory results, imaging results, clinical findings, device measurements, and social history data.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Observation |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Orders and Observations |
| URL | https://hl7.org/fhir/R4B/observation.html |
| US Core Vital Signs Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs |
| US Core Laboratory Result Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab |
| US Core Smoking Status Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-smokingstatus |

## Scope and Usage

Observations serve as central healthcare elements supporting diagnosis, monitoring, and baseline determination. Key applications include:

- Vital signs (weight, blood pressure, temperature)
- Laboratory data (glucose levels, estimated GFR)
- Imaging results (bone density, fetal measurements)
- Clinical findings and assessments
- Device measurements and settings
- Clinical assessment tools (APGAR, Glasgow Coma Score)
- Personal characteristics and social history
- Product quality testing

## Boundaries and Relationships

The resource explicitly avoids overlap with specialized resources. It should NOT capture:
- Clinical diagnoses (use Condition resource instead)
- Allergies (use AllergyIntolerance)
- Medications (use MedicationStatement)
- Family history (use FamilyMemberHistory)
- Procedures (use Procedure resource)
- Questionnaire responses (use QuestionnaireResponse)

When observations instantiate an ObservationDefinition, elements inherit corresponding definitional content from that resource.

## JSON Structure

### Vital Signs Observation

```json
{
  "resourceType": "Observation",
  "id": "blood-pressure",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/StructureDefinition/vitalsigns",
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-blood-pressure"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/observation",
      "value": "c6f88320-67ad-11db-bd13-0800200c9a66"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs",
          "display": "Vital Signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85354-9",
        "display": "Blood pressure panel with all children optional"
      }
    ],
    "text": "Blood Pressure"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "effectiveDateTime": "2020-03-01",
  "issued": "2020-03-01T10:30:00-05:00",
  "performer": [
    {
      "reference": "Practitioner/example",
      "display": "Dr. Adam Careful"
    }
  ],
  "interpretation": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
          "code": "N",
          "display": "Normal"
        }
      ]
    }
  ],
  "bodySite": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "368209003",
        "display": "Right upper arm structure"
      }
    ]
  },
  "method": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "37931006",
        "display": "Auscultation"
      }
    ]
  },
  "device": {
    "reference": "Device/bp-cuff"
  },
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 120,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      },
      "interpretation": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
              "code": "N",
              "display": "Normal"
            }
          ]
        }
      ]
    },
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8462-4",
            "display": "Diastolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 80,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}
```

### Laboratory Result Observation

```json
{
  "resourceType": "Observation",
  "id": "hba1c",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/lab",
      "value": "107c2dc0-67a5-11db-bd13-0800200c9a66"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "laboratory",
          "display": "Laboratory"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "4548-4",
        "display": "Hemoglobin A1c/Hemoglobin.total in Blood"
      }
    ],
    "text": "Hemoglobin A1c"
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectiveDateTime": "2020-03-01",
  "issued": "2020-03-01T15:30:00-05:00",
  "performer": [
    {
      "reference": "Organization/lab"
    }
  ],
  "valueQuantity": {
    "value": 7.0,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  },
  "interpretation": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
          "code": "H",
          "display": "High"
        }
      ]
    }
  ],
  "referenceRange": [
    {
      "low": {
        "value": 4.0,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%"
      },
      "high": {
        "value": 6.0,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%"
      },
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
            "code": "normal",
            "display": "Normal Range"
          }
        ]
      }
    }
  ]
}
```

### Smoking Status Observation

```json
{
  "resourceType": "Observation",
  "id": "smoking-status",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-smokingstatus"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/observation",
      "value": "45efb604-7049-4a36-b17f-d5a5e6af9a09"
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
    "reference": "Patient/example"
  },
  "effectiveDateTime": "2020-03-01",
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

## Element Definitions

### identifier (0..*)

External identifiers for this observation.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference(CarePlan \| DeviceRequest \| ImmunizationRecommendation \| MedicationRequest \| NutritionOrder \| ServiceRequest) | Request fulfilled by this observation |

### partOf (0..*)

| Type | Description |
|------|-------------|
| Reference(MedicationAdministration \| MedicationDispense \| MedicationStatement \| Procedure \| Immunization \| ImagingStudy) | Part of referenced event |

### status (1..1)

The status of the observation. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | registered \| specimen-in-process \| preliminary \| final \| amended \| corrected \| appended \| cancelled \| entered-in-error \| unknown \| cannot-be-obtained |

**Value Set:** http://hl7.org/fhir/ValueSet/observation-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| registered | Registered | Observation recorded but not validated |
| specimen-in-process | Specimen In Process | Specimen is being processed |
| preliminary | Preliminary | This is a preliminary result |
| final | Final | Observation is complete |
| amended | Amended | Subsequent to final with changes |
| corrected | Corrected | Subsequent to final with corrections |
| appended | Appended | Subsequent to final with additions |
| cancelled | Cancelled | Observation is cancelled |
| entered-in-error | Entered in Error | Observation was entered in error |
| unknown | Unknown | Status is not available |
| cannot-be-obtained | Cannot Be Obtained | Result cannot be obtained |

### category (0..*)

Classification of the observation.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Category codes |

**Common Category Codes:**
| Code | Display | System |
|------|---------|--------|
| vital-signs | Vital Signs | http://terminology.hl7.org/CodeSystem/observation-category |
| laboratory | Laboratory | http://terminology.hl7.org/CodeSystem/observation-category |
| imaging | Imaging | http://terminology.hl7.org/CodeSystem/observation-category |
| procedure | Procedure | http://terminology.hl7.org/CodeSystem/observation-category |
| survey | Survey | http://terminology.hl7.org/CodeSystem/observation-category |
| exam | Exam | http://terminology.hl7.org/CodeSystem/observation-category |
| therapy | Therapy | http://terminology.hl7.org/CodeSystem/observation-category |
| activity | Activity | http://terminology.hl7.org/CodeSystem/observation-category |
| social-history | Social History | http://terminology.hl7.org/CodeSystem/observation-category |

### code (1..1)

What was observed. Required element.

| Type | Description |
|------|-------------|
| CodeableConcept | LOINC or other observation code |

**Value Set:** http://hl7.org/fhir/ValueSet/observation-codes (Example binding, LOINC)

**Common Vital Signs Codes (LOINC):**
| Code | Display |
|------|---------|
| 8480-6 | Systolic blood pressure |
| 8462-4 | Diastolic blood pressure |
| 85354-9 | Blood pressure panel |
| 8867-4 | Heart rate |
| 9279-1 | Respiratory rate |
| 8310-5 | Body temperature |
| 8302-2 | Body height |
| 29463-7 | Body weight |
| 39156-5 | Body mass index |
| 59408-5 | Oxygen saturation |
| 8287-5 | Head circumference |

**Smoking Status Code:**
| Code | Display |
|------|---------|
| 72166-2 | Tobacco smoking status |

### subject (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Group \| Device \| Location) | Who/what the observation is about |

### focus (0..*)

| Type | Description |
|------|-------------|
| Reference(Any) | What the observation is about (other than subject) |

### encounter (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter) | Healthcare event during which observation made |

### effective[x] (0..1)

When the observation was made.

| Element | Type | Description |
|---------|------|-------------|
| effectiveDateTime | dateTime | Clinically relevant time |
| effectivePeriod | Period | Time period |
| effectiveTiming | Timing | Timing schedule |
| effectiveInstant | instant | Precise time |

### issued (0..1)

| Type | Description |
|------|-------------|
| instant | Date/time observation was made available |

### performer (0..*)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| CareTeam \| Patient \| RelatedPerson) | Who is responsible |

### triggeredBy (0..*)

Identifies triggering observations (reflex/repeat testing).

| Element | Type | Description |
|---------|------|-------------|
| observation | Reference(Observation) | Triggering observation (Required) |
| type | code | reflex \| repeat \| re-run (Required) |
| reason | string | Explanation for trigger |

### value[x] (0..1)

The observation value. Supports 13 different types.

| Element | Type | Description |
|---------|------|-------------|
| valueQuantity | Quantity | Numeric value with units |
| valueCodeableConcept | CodeableConcept | Coded value |
| valueString | string | Text value |
| valueBoolean | boolean | True/false value |
| valueInteger | integer | Integer value |
| valueRange | Range | Range of values |
| valueRatio | Ratio | Ratio value |
| valueSampledData | SampledData | Series of measurements |
| valueTime | time | Time value |
| valueDateTime | dateTime | Date/time value |
| valuePeriod | Period | Period value |
| valueAttachment | Attachment | Attachment value |
| valueReference | Reference | Reference value |

**Constraint:** dataAbsentReason cannot coexist with populated value[x] elements.

### dataAbsentReason (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Why the result is missing |

**Data Absent Reason Codes:**
| Code | Display |
|------|---------|
| unknown | Unknown |
| asked-unknown | Asked But Unknown |
| temp-unknown | Temporarily Unknown |
| not-asked | Not Asked |
| asked-declined | Asked But Declined |
| masked | Masked |
| not-applicable | Not Applicable |
| unsupported | Unsupported |
| as-text | As Text |
| error | Error |
| not-a-number | Not a Number |
| negative-infinity | Negative Infinity |
| positive-infinity | Positive Infinity |
| not-performed | Not Performed |
| not-permitted | Not Permitted |

### interpretation (0..*)

High, low, normal, etc.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Interpretation codes |

**Interpretation Codes:**
| Code | Display | Definition |
|------|---------|------------|
| H | High | Above normal range |
| L | Low | Below normal range |
| N | Normal | Within normal range |
| HH | Critical high | Above critical threshold |
| LL | Critical low | Below critical threshold |
| A | Abnormal | Outside normal |
| AA | Critical abnormal | Critical abnormal |
| POS | Positive | Positive/detected |
| NEG | Negative | Negative/not detected |
| IND | Indeterminate | Cannot be determined |

**System:** `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation`

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Comments about the observation |

### bodySite (0..1)

**Deprecated:** Use bodyStructure instead.

| Type | Description |
|------|-------------|
| CodeableConcept | Body site of observation |

### bodyStructure (0..1)

| Type | Description |
|------|-------------|
| CodeableReference(BodyStructure) | Anatomical location (preferred over bodySite) |

### method (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | How the observation was made |

### specimen (0..1)

| Type | Description |
|------|-------------|
| Reference(Specimen) | Specimen used for observation |

### device (0..1)

| Type | Description |
|------|-------------|
| Reference(Device \| DeviceMetric) | Measurement device |

### referenceRange (0..*)

| Element | Type | Description |
|---------|------|-------------|
| low | SimpleQuantity | Low range boundary |
| high | SimpleQuantity | High range boundary |
| type | CodeableConcept | Reference range qualifier |
| appliesTo | CodeableConcept[] | Population for range |
| age | Range | Applicable age range |
| text | string | Text description of range |

### hasMember (0..*)

| Type | Description |
|------|-------------|
| Reference(Observation \| QuestionnaireResponse \| MolecularSequence) | Related observations |

### derivedFrom (0..*)

| Type | Description |
|------|-------------|
| Reference(DocumentReference \| ImagingStudy \| Media \| QuestionnaireResponse \| Observation \| MolecularSequence) | Source of observation |

### component (0..*)

Component observations (e.g., systolic/diastolic).

| Element | Type | Description |
|---------|------|-------------|
| code | CodeableConcept | Type of component |
| value[x] | Various | Component value |
| dataAbsentReason | CodeableConcept | Why component is missing |
| interpretation | CodeableConcept[] | Component interpretation |
| referenceRange | Element[] | Component reference range |

## Smoking Status Value Codes

| SNOMED Code | Display | FHIR Preferred Display |
|-------------|---------|------------------------|
| 449868002 | Current every day smoker | Current every day smoker |
| 428041000124106 | Current some day smoker | Current some day smoker |
| 8517006 | Former smoker | Former smoker |
| 266919005 | Never smoker | Never smoker |
| 77176002 | Smoker, current status unknown | Smoker, current status unknown |
| 266927001 | Unknown if ever smoked | Unknown if ever smoked |

## US Core Conformance Requirements

### US Core Vital Signs
1. **SHALL** support `status`
2. **SHALL** support `category` (vital-signs)
3. **SHALL** support `code`
4. **SHALL** support `subject`
5. **SHALL** support `effective[x]`
6. **SHALL** support `value[x]`

### US Core Laboratory Result
1. **SHALL** support `status`
2. **SHALL** support `category` (laboratory)
3. **SHALL** support `code`
4. **SHALL** support `subject`
5. **SHALL** support `effective[x]`
6. **SHALL** support `value[x]`

### US Core Smoking Status
1. **SHALL** support `status`
2. **SHALL** support `category` (social-history)
3. **SHALL** support `code` (72166-2)
4. **SHALL** support `subject`
5. **SHALL** support `effectiveDateTime`
6. **SHALL** support `valueCodeableConcept`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | registered \| preliminary \| final \| amended \| corrected \| cancelled \| entered-in-error \| unknown |
| category | token | Category of observation |
| code | token | Observation code (LOINC) |
| subject | reference | Subject of observation |
| patient | reference | Patient reference |
| encounter | reference | Associated encounter |
| date | date | Observation date |
| value-quantity | quantity | Numeric value |
| value-concept | token | Coded value |
| value-string | string | String value |
| combo-code | token | Code and component code |
| combo-value-quantity | quantity | Value and component value |
| component-code | token | Component code |
| component-value-quantity | quantity | Component value |
| performer | reference | Who performed observation |
| based-on | reference | Request this fulfills |
| derived-from | reference | Source observation |
| has-member | reference | Related observations |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| obs-1 | dataAbsentReason cannot coexist with populated value[x] elements |
| obs-2 | When component codes match parent code, parent value must be absent |
| obs-3 | If referenceRange contains comparators, they must align with range bounds |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the observation

## Compartments

The Observation resource is part of the following compartments:
- Device
- Encounter
- Group
- Patient
- Practitioner
- RelatedPerson

## Related Resources

Observation interconnects with 20+ resource types including:
- AdverseEvent, Condition, DiagnosticReport
- MedicationRequest, Procedure, RiskAssessment
- And many others

## Implementation Notes

- All observations should ideally include performer information
- When Observation instantiates ObservationDefinition, elements inherit definitional content
- Provenance resource provides detailed source documentation when needed
- ArtifactAssessment captures evaluation/commentary on the Observation record itself

## References

- FHIR R4B Observation: https://hl7.org/fhir/R4B/observation.html
- US Core Vital Signs Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs
- US Core Laboratory Result Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab
- US Core Smoking Status Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-smokingstatus
- LOINC: https://loinc.org/
- UCUM: https://ucum.org/
