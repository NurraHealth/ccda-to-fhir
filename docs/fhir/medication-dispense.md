# FHIR R4B: MedicationDispense Resource

## Overview

The MedicationDispense resource represents a medication product that has been or is being dispensed for a named patient. This includes the supply provision and the instructions for administration to the patient. It is the result of a pharmacy system responding to a medication order.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | MedicationDispense |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 2 (Trial Use) |
| Security Category | Patient |
| Responsible Work Group | Pharmacy |
| URL | https://hl7.org/fhir/R4B/medicationdispense.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense |
| US Core Maturity | 3 (Trial Use) |

## Scope and Usage

**Covers:**
- Outpatient/community pharmacy dispensing and pickup
- Ward-level inpatient pharmacy distribution
- Single-dose ward stock issuance for patient consumption
- Partial fills and emergency fills
- Medication substitution information

**Excludes:**
- Prescription/ordering (use MedicationRequest)
- Actual patient consumption/administration (use MedicationAdministration)
- Patient-reported medication usage (use MedicationStatement)

**Key Distinctions:**
- **MedicationRequest:** The prescription/order
- **MedicationDispense:** The supply provision (this resource)
- **MedicationAdministration:** Actual patient consumption
- **MedicationStatement:** Patient-reported usage

**Workflow Notes:**
- MedicationDispense is the result of a pharmacy system responding to a MedicationRequest
- The resource captures the act of providing medication, not the act of consuming it
- Includes both the medication product and administration instructions
- Can represent completed dispenses or in-progress/planned dispenses

## JSON Structure

```json
{
  "resourceType": "MedicationDispense",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense"
    ]
  },
  "identifier": [
    {
      "system": "http://pharmacy.example.org/dispense",
      "value": "cb734647-fc99-424c-a864-7e3cda82e704"
    }
  ],
  "status": "completed",
  "category": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
        "code": "community",
        "display": "Community"
      }
    ]
  },
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
  "context": {
    "reference": "Encounter/example"
  },
  "performer": [
    {
      "function": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
            "code": "packager",
            "display": "Packager"
          }
        ]
      },
      "actor": {
        "reference": "Practitioner/pharmacist-1",
        "display": "Dr. Jane Smith, PharmD"
      }
    }
  ],
  "location": {
    "reference": "Location/pharmacy"
  },
  "authorizingPrescription": [
    {
      "reference": "MedicationRequest/med-request-1"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
        "code": "FF",
        "display": "First Fill"
      }
    ]
  },
  "quantity": {
    "value": 30,
    "unit": "tablet",
    "system": "http://unitsofmeasure.org",
    "code": "{tbl}"
  },
  "daysSupply": {
    "value": 30,
    "unit": "day",
    "system": "http://unitsofmeasure.org",
    "code": "d"
  },
  "whenPrepared": "2020-03-01T09:00:00-05:00",
  "whenHandedOver": "2020-03-01T14:30:00-05:00",
  "destination": {
    "reference": "Location/patient-home"
  },
  "receiver": [
    {
      "reference": "Patient/example"
    }
  ],
  "note": [
    {
      "text": "Patient counseled on medication use and side effects"
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
      "route": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "26643006",
            "display": "Oral route"
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
      ]
    }
  ],
  "substitution": {
    "wasSubstituted": true,
    "type": {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
          "code": "G",
          "display": "Generic composition"
        }
      ]
    },
    "reason": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
            "code": "FP",
            "display": "Formulary policy"
          }
        ]
      }
    ],
    "responsibleParty": [
      {
        "reference": "Practitioner/pharmacist-1"
      }
    ]
  },
  "detectedIssue": [
    {
      "reference": "DetectedIssue/example"
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

Business identifiers for this dispensing event.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### status (1..1)

The status of the dispense. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | preparation \| in-progress \| cancelled \| on-hold \| completed \| entered-in-error \| stopped \| declined \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/medicationdispense-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| preparation | Preparation | Preparing medication |
| in-progress | In Progress | Actions underway but not complete |
| cancelled | Cancelled | Actions halted, medication not supplied |
| on-hold | On Hold | Actions stopped temporarily |
| completed | Completed | All actions complete and product handed over |
| entered-in-error | Entered in Error | Record created in error |
| stopped | Stopped | Actions stopped without completing |
| declined | Declined | Patient declined medication |
| unknown | Unknown | Authoring system doesn't know status |

### category (0..1)

Type of medication dispense.

| Type | Description |
|------|-------------|
| CodeableConcept | Category of dispense |

**Category Codes:**
| Code | Display |
|------|---------|
| inpatient | Inpatient |
| outpatient | Outpatient |
| community | Community |
| discharge | Discharge |

**Value Set:** http://terminology.hl7.org/ValueSet/medicationdispense-category (Preferred binding)

### medication[x] (1..1)

The medication being dispensed.

| Type | Description |
|------|-------------|
| CodeableConcept \| Reference(Medication) | Medication code or reference |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-codes (Extensible binding - RxNorm preferred)

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| `http://hl7.org/fhir/sid/ndc` | NDC |
| `http://snomed.info/sct` | SNOMED CT |

**US Core Requirement:** Servers SHALL support at least one of CodeableConcept or Reference.

### subject (1..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Group) | Required reference to patient (US Core: Patient only) |

### context (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter \| EpisodeOfCare) | Associated encounter or episode |

**US Core:** Must Support element.

### supportingInformation (0..*)

| Type | Description |
|------|-------------|
| Reference(Any) | Additional documentation/information |

### performer (0..*)

Who or what performed the dispense event.

| Element | Type | Description |
|---------|------|-------------|
| function | CodeableConcept | Type of performance (packager, checker, etc.) |
| actor | Reference | Individual/organization who performed (Required) |

**Value Set (function):** http://terminology.hl7.org/ValueSet/medicationdispense-performer-function (Preferred binding)

**Performer Function Codes:**
| Code | Display |
|------|---------|
| dataenterer | Data Enterer |
| packager | Packager |
| checker | Checker |
| finalchecker | Final Checker |

**US Core:** Must Support element (performer.actor).

### location (0..1)

| Type | Description |
|------|-------------|
| Reference(Location) | Physical location where dispensed |

### authorizingPrescription (0..*)

| Type | Description |
|------|-------------|
| Reference(MedicationRequest) | Prescription that authorized dispense |

**US Core:** Must Support element.

### type (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Dispense type (first fill, partial fill, etc.) |

**Value Set:** http://terminology.hl7.org/ValueSet/v3-ActPharmacySupplyType (Extensible binding)

**Type Codes:**
| Code | Display | Definition |
|------|---------|------------|
| FF | First Fill | First fill of medication |
| DF | Daily Fill | Daily dose fill |
| EM | Emergency Supply | Emergency supply |
| FS | Floor Stock | Supply from floor stock |
| MS | Manufacturer Sample | Free manufacturer sample |
| RF | Refill | Refill of prescription |
| RFC | Refill - Complete | Final refill |
| RFCS | Refill - Complete (Partial Strength) | Final refill with strength change |
| RFF | Refill (First fill this facility) | Refill at new facility |
| RFFS | Refill (Part Fill, First fill this facility) | Partial refill at new facility |
| RFP | Refill - Part Fill | Partial refill |
| RFPS | Refill - Part Fill (Partial Strength) | Partial refill with strength change |
| SO | Script Owing | Script owed but not yet supplied |
| TF | Trial Fill | Trial quantity fill |
| UD | Unit Dose | Supply in unit dose form |

**US Core:** Must Support element.

### quantity (0..1)

| Type | Description |
|------|-------------|
| SimpleQuantity | Amount dispensed (includes unit) |

**US Core:** Must Support element.

### daysSupply (0..1)

| Type | Description |
|------|-------------|
| SimpleQuantity | Days supply of medication |

### whenPrepared (0..1)

| Type | Description |
|------|-------------|
| dateTime | When product was packaged/reviewed |

### whenHandedOver (0..1)

| Type | Description |
|------|-------------|
| dateTime | When product was given to patient |

**US Core:** Must Support element. **SHALL** be present if status is "completed".

**Constraint (mdd-1):** whenHandedOver cannot be before whenPrepared.

### destination (0..1)

| Type | Description |
|------|-------------|
| Reference(Location) | Where medication sent |

### receiver (0..*)

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| RelatedPerson) | Who collected the medication |

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

### dosageInstruction (0..*)

How the medication should be taken. Same structure as MedicationRequest.dosageInstruction.

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

**US Core:** Must Support elements:
- dosageInstruction.text
- dosageInstruction.timing
- dosageInstruction.route
- dosageInstruction.doseAndRate.dose[x]

### substitution (0..1)

Whether a substitution was made during the dispense.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| wasSubstituted | boolean | 1..1 | Whether substitution occurred (Required) |
| type | CodeableConcept | 0..1 | Type of substitution |
| reason | CodeableConcept[] | 0..* | Why substitution was made |
| responsibleParty | Reference[] | 0..* | Who decided on substitution |

**Value Set (type):** http://terminology.hl7.org/ValueSet/v3-ActSubstanceAdminSubstitutionCode (Example binding)

**Substitution Type Codes:**
| Code | Display | Definition |
|------|---------|------------|
| E | Equivalent | Equivalent therapeutic alternative |
| EC | Equivalent Composition | Same active ingredient(s), different inactive |
| BC | Brand Composition | Brand to brand, same composition |
| G | Generic Composition | Brand to generic or vice versa |
| TE | Therapeutic Alternative | Different ingredient, same therapeutic intent |
| TB | Therapeutic Brand | Different brand, same therapeutic class |
| TG | Therapeutic Generic | Different generic, same therapeutic class |
| F | Formulary | Formulary substitution |
| N | None | No substitution made |

**Value Set (reason):** http://terminology.hl7.org/ValueSet/v3-SubstanceAdminSubstitutionReason (Example binding)

**Substitution Reason Codes:**
| Code | Display |
|------|---------|
| FP | Formulary Policy |
| OS | Out of Stock |
| RR | Regulatory Requirement |
| CT | Continuing Therapy |

### detectedIssue (0..*)

| Type | Description |
|------|-------------|
| Reference(DetectedIssue)[] | Clinical issues detected |

### eventHistory (0..*)

| Type | Description |
|------|-------------|
| Reference(Provenance)[] | Event history |

## US Core Conformance Requirements

For US Core MedicationDispense profile compliance:

1. **SHALL** support `status`
2. **SHALL** support `medication[x]` (at least one of CodeableConcept or Reference)
3. **SHALL** support `subject` (Patient reference)
4. **SHALL** support `performer.actor`
5. **SHALL** support `whenHandedOver` (required when status='completed')
6. **SHOULD** support `context` (Encounter reference)
7. **SHOULD** support `authorizingPrescription`
8. **SHOULD** support `type`
9. **SHOULD** support `quantity`
10. **SHOULD** support `dosageInstruction.text`
11. **SHOULD** support `dosageInstruction.timing`
12. **SHOULD** support `dosageInstruction.route`
13. **SHOULD** support `dosageInstruction.doseAndRate.dose[x]`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | Status of dispense |
| patient | reference | Patient reference (US Core required) |
| subject | reference | Subject reference |
| context | reference | Associated encounter |
| medication | reference | Medication reference |
| code | token | Medication code |
| prescription | reference | Authorizing MedicationRequest |
| type | token | Dispense type |
| whenhandedover | date | Date product handed over |
| whenprepared | date | Date product prepared |
| performer | reference | Who performed dispense |

**US Core Required Search:**
- `patient` (with optional `_include=MedicationDispense:medication`)

**US Core Recommended Search Combinations:**
- `patient` + `status`
- `patient` + `status` + `type`

## Constraints

| Constraint | Severity | Description |
|------------|----------|-------------|
| mdd-1 | Error | whenHandedOver cannot be before whenPrepared |
| us-core-20 | Error | whenHandedOver SHALL be present if status is 'completed' |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the dispense record

## Compartments

The MedicationDispense resource is part of the following compartments:
- Patient
- Practitioner

## References

- FHIR R4B MedicationDispense: https://hl7.org/fhir/R4B/medicationdispense.html
- US Core MedicationDispense Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- SNOMED CT: http://snomed.info/sct
