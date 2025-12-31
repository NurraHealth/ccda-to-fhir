# FHIR R4B: Immunization Resource

## Overview

The Immunization resource describes the event of a patient being administered a vaccine or a record of an immunization as reported by a patient, a clinician, or another party. It covers recording of current and historical administration of vaccines to patients across all healthcare disciplines.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Immunization |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Public Health |
| URL | https://hl7.org/fhir/R4B/immunization.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-immunization |

## Scope and Usage

The resource applies to both human and animal immunizations, excluding non-vaccine agents despite immunological claims.

**Key Boundaries:**
- Immunization handles vaccines only
- MedicationAdministration covers non-vaccine medications
- Systems may reference both resources for immunization data
- Immunization.reaction may indicate an allergy or intolerance, requiring separate AllergyIntolerance resources
- Educational materials should use Communication resources

## JSON Structure

```json
{
  "resourceType": "Immunization",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-immunization"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/immunization",
      "value": "e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"
    }
  ],
  "status": "completed",
  "statusReason": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "code": "IMMUNE",
        "display": "Immunity"
      }
    ]
  },
  "vaccineCode": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/cvx",
        "code": "140",
        "display": "Influenza, seasonal, injectable, preservative free"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "49281-0703-55",
        "display": "Fluzone Quadrivalent"
      }
    ],
    "text": "Influenza, seasonal, injectable, preservative free"
  },
  "patient": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "occurrenceDateTime": "2020-11-01",
  "recorded": "2020-11-01",
  "primarySource": true,
  "reportOrigin": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/immunization-origin",
        "code": "provider",
        "display": "Provider"
      }
    ]
  },
  "location": {
    "reference": "Location/example",
    "display": "Community Health and Hospitals"
  },
  "manufacturer": {
    "reference": "Organization/sanofi",
    "display": "Sanofi Pasteur Inc"
  },
  "lotNumber": "AAJN11K",
  "expirationDate": "2021-05-01",
  "site": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "368208006",
        "display": "Left upper arm structure"
      }
    ]
  },
  "route": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
        "code": "IM",
        "display": "Injection, intramuscular"
      }
    ]
  },
  "doseQuantity": {
    "value": 0.5,
    "unit": "mL",
    "system": "http://unitsofmeasure.org",
    "code": "mL"
  },
  "performer": [
    {
      "function": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
            "code": "AP",
            "display": "Administering Provider"
          }
        ]
      },
      "actor": {
        "reference": "Practitioner/example",
        "display": "Dr. Adam Careful"
      }
    },
    {
      "function": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
            "code": "OP",
            "display": "Ordering Provider"
          }
        ]
      },
      "actor": {
        "reference": "Practitioner/example2",
        "display": "Dr. Jane Smith"
      }
    }
  ],
  "note": [
    {
      "text": "Patient tolerated vaccine well. No immediate adverse reactions."
    }
  ],
  "reasonCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "195967001",
          "display": "Routine immunization"
        }
      ]
    }
  ],
  "reasonReference": [
    {
      "reference": "Condition/example"
    }
  ],
  "isSubpotent": false,
  "education": [
    {
      "documentType": "VIS",
      "reference": "http://example.org/vis/influenza",
      "publicationDate": "2020-08-15",
      "presentationDate": "2020-11-01"
    }
  ],
  "programEligibility": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/immunization-program-eligibility",
          "code": "ineligible",
          "display": "Not Eligible"
        }
      ]
    }
  ],
  "fundingSource": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/immunization-funding-source",
        "code": "private",
        "display": "Private"
      }
    ]
  },
  "reaction": [
    {
      "date": "2020-11-01",
      "detail": {
        "reference": "Observation/reaction"
      },
      "reported": true
    }
  ],
  "protocolApplied": [
    {
      "series": "Influenza 2020-2021",
      "authority": {
        "reference": "Organization/cdc"
      },
      "targetDisease": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "6142004",
              "display": "Influenza"
            }
          ]
        }
      ],
      "doseNumberPositiveInt": 1,
      "seriesDosesPositiveInt": 1
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

Business identifiers assigned to this Immunization.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference(CarePlan \| MedicationRequest \| ServiceRequest \| ImmunizationRecommendation) | Plan/order/recommendation fulfilled by this immunization |

### status (1..1)

The status of the immunization event.

| Type | Values |
|------|--------|
| code | completed \| entered-in-error \| not-done |

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| completed | Completed | Immunization was performed |
| entered-in-error | Entered in Error | Record was entered in error |
| not-done | Not Done | Immunization was not performed |

### statusReason (0..1)

Reason for current status (particularly for not-done).

| Type | Description |
|------|-------------|
| CodeableConcept | Reason immunization was not given |

**Status Reason Codes:**
| Code | Display | System |
|------|---------|--------|
| IMMUNE | Immunity | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| MEDPREC | Medical precaution | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| OSTOCK | Product out of stock | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| PATOBJ | Patient objection | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| PHILISOP | Philosophical objection | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| RELIG | Religious objection | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| VACEFF | Vaccine efficacy concerns | http://terminology.hl7.org/CodeSystem/v3-ActReason |
| VACSAF | Vaccine safety concerns | http://terminology.hl7.org/CodeSystem/v3-ActReason |

### vaccineCode (1..1)

Vaccine product administered.

| Type | Description |
|------|-------------|
| CodeableConcept | Vaccine code (CVX, NDC) |

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://hl7.org/fhir/sid/cvx` | CVX (Vaccine Administered) |
| `http://hl7.org/fhir/sid/ndc` | National Drug Code |

**Common CVX Codes:**
| Code | Display |
|------|---------|
| 140 | Influenza, seasonal, injectable, preservative free |
| 141 | Influenza, seasonal, injectable |
| 08 | Hepatitis B vaccine |
| 10 | IPV (Polio) |
| 20 | DTaP |
| 21 | Varicella |
| 03 | MMR |
| 33 | Pneumococcal polysaccharide |
| 115 | Tdap |
| 207 | COVID-19, mRNA, LNP-S |
| 208 | COVID-19, mRNA, LNP-S (Pfizer-BioNTech) |
| 212 | COVID-19, vector-nr, rS-Ad26 (Janssen) |
| 213 | SARS-COV-2 COVID-19 NOS |

### patient (1..1)

| Type | Description |
|------|-------------|
| Reference(Patient) | Required reference to patient |

### encounter (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter) | Encounter during which immunization occurred |

### occurrence[x] (1..1)

When the immunization was administered.

| Element | Type | Description |
|---------|------|-------------|
| occurrenceDateTime | dateTime | Date/time of administration |
| occurrenceString | string | Textual date (e.g., "childhood") |

### recorded (0..1)

| Type | Description |
|------|-------------|
| dateTime | Date record was entered |

### primarySource (0..1)

| Type | Description |
|------|-------------|
| boolean | Information source is authoritative |

### reportOrigin (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Source of secondary reported record |

**Report Origin Codes:**
| Code | Display |
|------|---------|
| provider | Other Provider |
| record | Written Record |
| recall | Parent/Guardian/Patient Recall |
| school | School Record |

### location (0..1)

| Type | Description |
|------|-------------|
| Reference(Location) | Where immunization occurred |

### administeredProduct (0..1)

| Type | Description |
|------|-------------|
| CodeableReference(Medication) | Specific product administered (more detailed than vaccineCode) |

### manufacturer (0..1)

| Type | Description |
|------|-------------|
| CodeableReference(Organization) | Vaccine manufacturer |

### lotNumber (0..1)

| Type | Description |
|------|-------------|
| string | Vaccine lot number |

### expirationDate (0..1)

| Type | Description |
|------|-------------|
| date | Vaccine expiration date |

### site (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Body site vaccine was administered |

**Common Site Codes (SNOMED):**
| Code | Display |
|------|---------|
| 368208006 | Left upper arm structure |
| 368209003 | Right upper arm structure |
| 61396006 | Left thigh |
| 11207009 | Right thigh |
| 46862004 | Buttock structure |

### route (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | How vaccine entered body |

**Route Codes:**
| Code | Display | System |
|------|---------|--------|
| IM | Injection, intramuscular | http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration |
| SC | Injection, subcutaneous | http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration |
| PO | Swallow, oral | http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration |
| NASINHLC | Inhalation, nasal | http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration |
| IDINJ | Injection, intradermal | http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration |

### doseQuantity (0..1)

| Type | Description |
|------|-------------|
| SimpleQuantity | Amount of vaccine administered |

### performer (0..*)

Who performed the immunization.

| Element | Type | Description |
|---------|------|-------------|
| function | CodeableConcept | Role type |
| actor | Reference(Practitioner \| PractitionerRole \| Organization) | Who performed |

**Performer Function Codes:**
| Code | Display | System |
|------|---------|--------|
| AP | Administering Provider | http://terminology.hl7.org/CodeSystem/v2-0443 |
| OP | Ordering Provider | http://terminology.hl7.org/CodeSystem/v2-0443 |

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

### reasonCode (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Coded reason for immunization |

### reasonReference (0..*)

| Type | Description |
|------|-------------|
| Reference(Condition \| Observation \| DiagnosticReport) | Detailed reason |

### reason (0..*)

| Type | Description |
|------|-------------|
| CodeableReference[] | Why immunization occurred (Condition, Observation, DiagnosticReport) |

### isSubpotent (0..1)

This is a **modifier element**.

| Type | Description |
|------|-------------|
| boolean | Dose potency was reduced |

**Note:** Indicates that the content of the resource is not to be used for clinical decision support.

### subpotentReason (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Reason for subpotent dose |

### supportingInformation (0..*)

| Type | Description |
|------|-------------|
| Reference(Any) | Contextual information (e.g., pregnancy status) |

### informationSource (0..1)

| Type | Description |
|------|-------------|
| CodeableReference | Source for non-primary records (Patient, Practitioner, Organization, etc.) |

### education (0..*)

Educational material presented to patient.

| Element | Type | Description |
|---------|------|-------------|
| documentType | string | Type of educational material |
| reference | uri | Link to material |
| publicationDate | dateTime | Publication date |
| presentationDate | dateTime | When presented to patient |

### programEligibility (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Patient's eligibility for funding program |

### fundingSource (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Funding source (private, public) |

### reaction (0..*)

Details of reaction that occurred.

| Element | Type | Description |
|---------|------|-------------|
| date | dateTime | When reaction occurred |
| detail | Reference(Observation) | Details of reaction |
| reported | boolean | Was reaction self-reported |

### protocolApplied (0..*)

Protocol followed during immunization.

| Element | Type | Description |
|---------|------|-------------|
| series | string | Name of vaccine series |
| authority | Reference(Organization) | Authority defining protocol |
| targetDisease | CodeableConcept[] | Disease being prevented |
| doseNumber[x] | positiveInt or string | Dose number in series |
| seriesDoses[x] | positiveInt or string | Total doses in series |

## US Core Conformance Requirements

For US Core Immunization profile compliance:

1. **SHALL** support `status`
2. **SHALL** support `statusReason`
3. **SHALL** support `vaccineCode`
4. **SHALL** support `patient`
5. **SHALL** support `occurrence[x]`
6. **SHALL** support `primarySource`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | completed \| entered-in-error \| not-done |
| vaccine-code | token | Vaccine product administered |
| patient | reference | The patient for the vaccination |
| date | date | When the vaccination occurred |
| location | reference | Where vaccination occurred |
| lot-number | string | Vaccine lot number |
| manufacturer | reference | Vaccine manufacturer |
| performer | reference | Who performed |
| reaction | reference | Additional reaction details |
| reason-code | token | Reason for immunization |
| series | string | Vaccine series |
| target-disease | token | Disease targeted |
| status-reason | token | Reason for current status |

## Modifier Elements

The following elements are modifier elements:
- **isSubpotent** - Indicates content should not be used for clinical decision support

## Compartments

The Immunization resource is part of the following compartments:
- Patient
- Practitioner

## References

- FHIR R4B Immunization: https://hl7.org/fhir/R4B/immunization.html
- US Core Immunization Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-immunization
- CVX Code Set: https://www2a.cdc.gov/vaccines/iis/iisstandards/vaccines.asp?rpt=cvx
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
