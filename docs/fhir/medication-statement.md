# FHIR R4B: MedicationStatement Resource

## Overview

The MedicationStatement resource records that a medication is being consumed by a patient. A MedicationStatement may indicate that the patient is taking the medication now, has taken the medication in the past, or will be taking the medication in the future. The source of this information can be the patient, significant other (such as a family member or spouse), or a clinician.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | MedicationStatement |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 3 |
| Standards Status | Trial Use |
| Security Category | Patient |
| Responsible Work Group | Pharmacy |
| URL | https://hl7.org/fhir/R4B/medicationstatement.html |
| US Core Profile | **Not included in US Core STU7+** (deprecated since 2019) |

## Scope and Usage

**Purpose:**
A record of a medication that is being consumed by a patient. This is a broader assertion covering a wider timespan and is independent of specific medication events.

**Key Distinctions:**
- **MedicationRequest:** The order/prescription itself
- **MedicationDispense:** Fulfillment of the order
- **MedicationAdministration:** Actual consumption/administration (specific event documentation)
- **MedicationStatement:** Reported medication usage (broader assertion, not requiring specific event documentation)

**Important:** MedicationStatement is fundamentally different from MedicationAdministration. The medication administration has complete administration information based on actual administration by the person who administered the medication. A medication statement is often, if not always, less specific. It is not a part of the prescribe→dispense→administer sequence but is a report that such a sequence (or at least a part of it) did take place.

**Covers:**
- Current medications being taken
- Historical medication use
- Future intended medication use
- Patient-reported medications (including OTC)
- Family member/caregiver-reported medications
- Medications derived from other clinical records

**Use Cases:**
- Medication reconciliation
- Patient medication history
- Home medication lists
- Self-reported medication tracking
- Negative assertions (medication NOT being taken)

## JSON Structure

```json
{
  "resourceType": "MedicationStatement",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/StructureDefinition/MedicationStatement"
    ]
  },
  "identifier": [
    {
      "use": "official",
      "system": "http://hospital.example.org/medication-statements",
      "value": "12345689"
    }
  ],
  "basedOn": [
    {
      "reference": "MedicationRequest/example"
    }
  ],
  "partOf": [
    {
      "reference": "MedicationAdministration/example"
    }
  ],
  "status": "active",
  "statusReason": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "182862001",
          "display": "Drug not taken - patient choice"
        }
      ]
    }
  ],
  "category": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
        "code": "inpatient",
        "display": "Inpatient"
      }
    ]
  },
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197361",
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
  "context": {
    "reference": "Encounter/example"
  },
  "effectivePeriod": {
    "start": "2020-03-01",
    "end": "2020-04-01"
  },
  "dateAsserted": "2020-04-15",
  "informationSource": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "derivedFrom": [
    {
      "reference": "MedicationRequest/example"
    }
  ],
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
  "note": [
    {
      "text": "Patient indicates they miss the occasional dose"
    }
  ],
  "dosage": [
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
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this medication statement.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

**Note:** Source EHR identifiers SHOULD be included to support deduplication across MedicationStatement and MedicationRequest resources.

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference[] | Plan, proposal or order fulfilled by this statement (MedicationRequest, CarePlan, ServiceRequest) |

### partOf (0..*)

| Type | Description |
|------|-------------|
| Reference[] | Larger event this statement is part of (MedicationAdministration, MedicationDispense, MedicationStatement, Procedure, Observation) |

### status (1..1)

The status of the medication usage. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | active \| completed \| entered-in-error \| intended \| stopped \| on-hold \| unknown \| not-taken |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-statement-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| active | Active | Medication is currently active |
| completed | Completed | Medication course is complete |
| entered-in-error | Entered in Error | Statement was recorded in error |
| intended | Intended | Medication may be taken in the future |
| stopped | Stopped | Medication was discontinued |
| on-hold | On Hold | Temporarily suspended |
| unknown | Unknown | Status is unknown |
| not-taken | Not Taken | **Patient is asserting they are NOT taking this medication** |

**Important:** The "not-taken" status is particularly useful for negative assertions when a patient explicitly states they are not taking a particular medication.

### statusReason (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Reason for current status |

**Value Set:** http://hl7.org/fhir/ValueSet/reason-medication-status-codes (Example binding)

**Common Status Reason Codes (SNOMED):**
| Code | Display |
|------|---------|
| 182862001 | Drug not taken - patient choice |
| 182863006 | Drug not taken - patient forgot |
| 182864000 | Drug not taken - side effects |
| 266711001 | Drug not taken - cost |

### category (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Type of medication statement |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-statement-category (Preferred binding)

**Category Codes:**
| Code | Display | Definition |
|------|---------|------------|
| inpatient | Inpatient | Medications administered/consumed in inpatient or acute care setting |
| outpatient | Outpatient | Medications administered/consumed in outpatient setting |
| community | Community | Medications consumed by patient in home (long term care, nursing homes, hospices) |
| patientspecified | Patient Specified | Medication use statements provided by patient, agent or another provider (including OTC) |

### medication[x] (1..1)

The medication being taken.

| Type | Description |
|------|-------------|
| CodeableConcept \| Reference(Medication) | Medication code or reference to Medication resource |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-codes (SNOMED CT, Example binding)

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm (preferred) |
| `http://hl7.org/fhir/sid/ndc` | NDC |
| `http://snomed.info/sct` | SNOMED CT |

**Terminology Binding:** Example binding to SNOMED CT Medication Codes value set. RxNorm is the preferred code system in US implementations.

### subject (1..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Required reference to patient |

### context (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter \| EpisodeOfCare) | Associated encounter or episode |

**Note:** This element is renamed to "encounter" in FHIR R5.

### effective[x] (0..1)

**The time period when the medication was/is/will be taken by the patient.**

| Element | Type | Description |
|---------|------|-------------|
| effectiveDateTime | dateTime | Specific date/time |
| effectivePeriod | Period | Time interval |

**Important Distinction:**
- **effective[x]:** When the medication was actually taken (the timeframe of medication use)
- **dateAsserted:** When the statement was recorded or claimed

**Example:** A patient may have taken medication from January 1-15, 2024 (effectivePeriod), but this was documented on February 1, 2024 (dateAsserted).

### dateAsserted (0..1)

| Type | Description |
|------|-------------|
| dateTime | When the usage was asserted |

**Purpose:** The date when the medication statement was recorded or claimed, which may be different from when the medication was actually taken.

### informationSource (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| PractitionerRole \| RelatedPerson \| Organization) | Person or organization who provided the information |

**Important Distinction:**
- **informationSource:** Person/organization that reported the medication use (e.g., patient, family member, clinician)
- **derivedFrom:** Other FHIR resources from which the statement was derived

### derivedFrom (0..*)

| Type | Description |
|------|-------------|
| Reference[] | Supporting FHIR resources (MedicationRequest, MedicationDispense, MedicationAdministration, Claim, or any Resource) |

**Use Case:** When a MedicationStatement is created from other clinical records (e.g., derived from a prescription or claim).

### reasonCode (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Reason for why medication is being taken |

**Value Set:** http://hl7.org/fhir/ValueSet/condition-code (Example binding)

### reasonReference (0..*)

| Type | Description |
|------|-------------|
| Reference[] | Clinical justification (Condition, Observation, DiagnosticReport) |

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes about medication use |

### dosage (0..*)

How the medication is/was/will be taken.

| Element | Type | Description |
|---------|------|-------------|
| sequence | integer | Order of dosage instructions |
| text | string | Free text dosage instructions |
| additionalInstruction | CodeableConcept[] | Supplemental instructions |
| patientInstruction | string | Patient-oriented instructions |
| timing | Timing | When medication should be taken |
| asNeeded[x] | boolean or CodeableConcept | PRN indicator |
| site | CodeableConcept | Body site for administration |
| route | CodeableConcept | How drug enters body |
| method | CodeableConcept | Technique for administering |
| doseAndRate | Element[] | Dose and rate information |
| maxDosePerPeriod | Ratio[] | Upper limit on dose |
| maxDosePerAdministration | SimpleQuantity | Max dose per administration |
| maxDosePerLifetime | SimpleQuantity | Max lifetime dose |

### dosage.timing

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

### dosage.route

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

### dosage.doseAndRate

| Element | Type | Description |
|---------|------|-------------|
| type | CodeableConcept | Calculated or ordered |
| dose[x] | Range or Quantity | Amount of medication per dose |
| rate[x] | Ratio, Range, or Quantity | Rate of administration |

## FHIR R4B Conformance Requirements

For FHIR R4B MedicationStatement conformance:

### Mandatory Elements (Cardinality 1..1)

1. **status** - Required code indicating the medication statement status
2. **medication[x]** - Required identification of the medication (CodeableConcept or Reference)
3. **subject** - Required reference to the patient

### Must Support Elements (Recommended when available)

1. **effective[x]** - When the medication was/is being taken (strongly recommended)
2. **dateAsserted** - When the statement was asserted (strongly recommended)
3. **informationSource** - Who provided the information (strongly recommended for patient-reported medications)
4. **derivedFrom** - Underlying resources from which statement was derived

### US Core Note

**Important:** US Core Implementation Guide (STU7 and later) does not include a MedicationStatement profile. US Core recommends using MedicationRequest for active medication lists. The last US Core version with MedicationStatement support was STU3.1.1 (2019).

## Search Parameters

Standard FHIR R4B search parameters for MedicationStatement:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| patient | reference | **SHOULD** | Patient reference (with optional `_include`) |
| patient+status | composite | **SHOULD** | Patient and status combination |
| patient+effective | composite | **SHOULD** | Patient and effective date/period |
| _id | token | MAY | Logical id of the resource |
| status | token | MAY | active \| completed \| entered-in-error \| intended \| stopped \| on-hold \| unknown \| not-taken |
| subject | reference | MAY | Subject reference |
| context | reference | MAY | Associated encounter/episode |
| medication | reference | MAY | Medication reference |
| code | token | MAY | Medication code |
| effective | date | MAY | When medication was/is being taken |
| category | token | MAY | Category of statement |
| identifier | token | MAY | Business identifier |
| source | reference | MAY | Information source (informationSource) |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the statement (e.g., "not-taken" reverses the meaning)

## Compartments

The MedicationStatement resource is part of the following compartments:
- Patient
- Practitioner
- RelatedPerson

## Implementation Notes

### Deduplication

Source EHR identifiers SHOULD be included in the `identifier` element to support deduplication across MedicationStatement and MedicationRequest resources. Exposing the EHR identifiers helps client applications identify duplicates.

### Medication Representation

When using medicationReference:
- The resource may be contained or an external reference
- If external reference is used, the server SHALL support the `_include` parameter
- The client application SHALL support all methods

### Negative Assertions

Use `status = "not-taken"` for positive assertions that a medication is NOT being taken. This is important for medication reconciliation and documenting patient-reported non-adherence or discontinuation.

## Examples

### Example 1: Active Medication (Patient-Reported)

```json
{
  "resourceType": "MedicationStatement",
  "id": "example-patient-reported",
  "status": "active",
  "category": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
      "code": "patientspecified",
      "display": "Patient Specified"
    }]
  },
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectivePeriod": {
    "start": "2020-03-01"
  },
  "dateAsserted": "2024-01-15",
  "informationSource": {
    "reference": "Patient/example"
  },
  "dosage": [{
    "text": "Take 1 tablet by mouth once daily"
  }]
}
```

### Example 2: Medication Not Taken

```json
{
  "resourceType": "MedicationStatement",
  "id": "example-not-taken",
  "status": "not-taken",
  "statusReason": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "182862001",
      "display": "Drug not taken - patient choice"
    }]
  }],
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "308971",
      "display": "Warfarin Sodium 5 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectiveDateTime": "2024-01-15",
  "dateAsserted": "2024-01-15",
  "note": [{
    "text": "Patient refused medication due to concerns about side effects"
  }]
}
```

### Example 3: Completed Historical Medication

```json
{
  "resourceType": "MedicationStatement",
  "id": "example-completed",
  "status": "completed",
  "category": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
      "code": "community",
      "display": "Community"
    }]
  },
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197380",
      "display": "atenolol 25 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectivePeriod": {
    "start": "2023-01-01",
    "end": "2023-12-31"
  },
  "dateAsserted": "2024-01-15",
  "informationSource": {
    "reference": "Practitioner/example"
  },
  "derivedFrom": [{
    "reference": "MedicationRequest/example"
  }],
  "dosage": [{
    "timing": {
      "repeat": {
        "frequency": 2,
        "period": 1,
        "periodUnit": "d"
      }
    },
    "route": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "26643006",
        "display": "Oral route"
      }]
    },
    "doseAndRate": [{
      "doseQuantity": {
        "value": 1,
        "unit": "tablet",
        "system": "http://unitsofmeasure.org",
        "code": "{tbl}"
      }
    }]
  }]
}
```

## References

- FHIR R4B MedicationStatement: https://hl7.org/fhir/R4B/medicationstatement.html
- US Core Implementation Guide (STU7): https://hl7.org/fhir/us/core/STU7/ (Note: MedicationStatement profile deprecated)
- US Core Medication List Guidance: https://hl7.org/fhir/us/core/medication-list.html
- FHIR Medication Statement Category Value Set: https://hl7.org/fhir/r4/valueset-medication-statement-category.html
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- SNOMED CT: http://snomed.info/sct
