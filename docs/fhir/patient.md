# FHIR R4B: Patient Resource

## Overview

The Patient resource covers demographics and other administrative information about an individual or animal that is the subject of potential, past, current, or future health-related care. The data includes demographics, administrative information, and contact details.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Patient |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Patient Administration |
| URL | https://hl7.org/fhir/R4B/patient.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient |

## Scope and Usage

The Patient resource encompasses:
- Curative and psychiatric care
- Social services and pregnancy care
- Nursing, dietary, and personal health tracking
- Financial services (insurance)
- Public and population health

The resource focuses on the "who" information—demographic data supporting administrative, financial, and logistic procedures. Organizations maintain Patient records for individuals receiving their care; patients at multiple organizations may have multiple records.

**Key Use Cases:**
- Can represent non-human recipients (animals; use Group for herds)
- Can represent financial roles (guarantor, subscriber, beneficiary)
- The Person resource can link disparate Patient records representing one individual

## JSON Structure

```json
{
  "resourceType": "Patient",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
    ]
  },
  "identifier": [
    {
      "use": "usual",
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
            "code": "MR",
            "display": "Medical Record Number"
          }
        ]
      },
      "system": "http://hospital.example.org/mrn",
      "value": "998991"
    },
    {
      "use": "official",
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
            "code": "SS",
            "display": "Social Security Number"
          }
        ]
      },
      "system": "http://hl7.org/fhir/sid/us-ssn",
      "value": "111-00-2330"
    }
  ],
  "active": true,
  "name": [
    {
      "use": "official",
      "family": "Ross",
      "given": ["Ellen"],
      "suffix": ["MD"]
    },
    {
      "use": "nickname",
      "given": ["Ellie"]
    },
    {
      "use": "maiden",
      "family": "Smith",
      "given": ["Ellen"]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-2003",
      "use": "home"
    },
    {
      "system": "phone",
      "value": "+1(555)555-2004",
      "use": "mobile"
    },
    {
      "system": "email",
      "value": "ellen@email.com"
    }
  ],
  "gender": "female",
  "birthDate": "1975-05-01",
  "deceasedBoolean": false,
  "address": [
    {
      "use": "home",
      "type": "physical",
      "line": ["1357 Amber Drive"],
      "city": "Beaverton",
      "state": "OR",
      "postalCode": "97867",
      "country": "US"
    }
  ],
  "maritalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
        "code": "M",
        "display": "Married"
      }
    ]
  },
  "multipleBirthBoolean": false,
  "contact": [
    {
      "relationship": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v2-0131",
              "code": "N",
              "display": "Next-of-Kin"
            }
          ]
        }
      ],
      "name": {
        "family": "Ross",
        "given": ["Boris"]
      },
      "telecom": [
        {
          "system": "phone",
          "value": "+1(555)555-2005",
          "use": "home"
        }
      ],
      "address": {
        "use": "home",
        "line": ["1357 Amber Drive"],
        "city": "Beaverton",
        "state": "OR",
        "postalCode": "97867"
      }
    }
  ],
  "communication": [
    {
      "language": {
        "coding": [
          {
            "system": "urn:ietf:bcp:47",
            "code": "en",
            "display": "English"
          }
        ]
      },
      "preferred": true
    },
    {
      "language": {
        "coding": [
          {
            "system": "urn:ietf:bcp:47",
            "code": "es",
            "display": "Spanish"
          }
        ]
      },
      "preferred": false
    }
  ],
  "generalPractitioner": [
    {
      "reference": "Practitioner/example",
      "display": "Dr. Adam Careful"
    }
  ],
  "managingOrganization": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "extension": [
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
      "extension": [
        {
          "url": "ombCategory",
          "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2106-3",
            "display": "White"
          }
        },
        {
          "url": "ombCategory",
          "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2076-8",
            "display": "Native Hawaiian or Other Pacific Islander"
          }
        },
        {
          "url": "text",
          "valueString": "White, Native Hawaiian or Other Pacific Islander"
        }
      ]
    },
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
      "extension": [
        {
          "url": "ombCategory",
          "valueCoding": {
            "system": "urn:oid:2.16.840.1.113883.6.238",
            "code": "2186-5",
            "display": "Not Hispanic or Latino"
          }
        },
        {
          "url": "text",
          "valueString": "Not Hispanic or Latino"
        }
      ]
    },
    {
      "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex",
      "valueCode": "F"
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

Business identifiers for the patient.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| secondary \| old |
| type | CodeableConcept | Type of identifier (MR, SS, etc.) |
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| period | Period | Time period when identifier is/was valid |
| assigner | Reference(Organization) | Organization that assigned the identifier |

**Common Identifier Systems:**
| System URI | Description |
|------------|-------------|
| `http://hl7.org/fhir/sid/us-ssn` | US Social Security Number |
| `http://hl7.org/fhir/sid/us-npi` | US National Provider Identifier |
| `urn:oid:2.16.840.1.113883.4.1` | SSN (OID form) |

### active (0..1)

| Type | Description |
|------|-------------|
| boolean | Whether the patient record is in active use |

### name (0..*)

A name associated with the patient.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| nickname \| anonymous \| old \| maiden |
| text | string | Full text representation of name |
| family | string | Family name (often called surname) |
| given | string[] | Given names (not only first). Includes middle names. |
| prefix | string[] | Parts that come before the name (Dr., Mr., etc.) |
| suffix | string[] | Parts that come after the name (Jr., MD, etc.) |
| period | Period | Time period when name was/is in use |

### telecom (0..*)

Contact details for the patient.

| Element | Type | Description |
|---------|------|-------------|
| system | code | phone \| fax \| email \| pager \| url \| sms \| other |
| value | string | The actual contact point details |
| use | code | home \| work \| temp \| old \| mobile |
| rank | positiveInt | Preferred order of use (1 = highest) |
| period | Period | Time period when contact was/is in use |

### gender (0..1)

Administrative gender.

| Type | Values |
|------|--------|
| code | male \| female \| other \| unknown |

**Note:** This is administrative gender, not clinical sex or gender identity. For clinical purposes, use the appropriate extensions.

### birthDate (0..1)

| Type | Format |
|------|--------|
| date | YYYY, YYYY-MM, or YYYY-MM-DD |

### deceased[x] (0..1)

Indicates if the patient is deceased.

| Element | Type | Description |
|---------|------|-------------|
| deceasedBoolean | boolean | Whether patient is deceased |
| deceasedDateTime | dateTime | Date and time of death |

### address (0..*)

Addresses for the patient.

| Element | Type | Description |
|---------|------|-------------|
| use | code | home \| work \| temp \| old \| billing |
| type | code | postal \| physical \| both |
| text | string | Full text representation |
| line | string[] | Street name, number, direction, P.O. Box, etc. |
| city | string | City, town, village, etc. |
| district | string | District/county |
| state | string | Sub-unit of country (state, province, etc.) |
| postalCode | string | Postal code |
| country | string | Country (ISO 3166 2 or 3 letter code) |
| period | Period | Time period when address was/is in use |

### maritalStatus (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Marital status of the patient |

**Value Set:** http://hl7.org/fhir/ValueSet/marital-status

| Code | Display |
|------|---------|
| A | Annulled |
| D | Divorced |
| I | Interlocutory |
| L | Legally Separated |
| M | Married |
| P | Polygamous |
| S | Never Married |
| T | Domestic Partner |
| U | Unmarried |
| W | Widowed |
| UNK | Unknown |

### multipleBirth[x] (0..1)

Whether patient is part of a multiple birth.

| Element | Type | Description |
|---------|------|-------------|
| multipleBirthBoolean | boolean | Whether patient is part of multiple birth |
| multipleBirthInteger | integer | Birth order in multiple birth |

### photo (0..*)

| Type | Description |
|------|-------------|
| Attachment | Image of the patient |

### contact (0..*)

Contact parties (guardian, partner, friend) for the patient.

| Element | Type | Description |
|---------|------|-------------|
| relationship | CodeableConcept[] | The kind of relationship |
| name | HumanName | Contact person's name |
| telecom | ContactPoint[] | Contact details |
| address | Address | Contact person's address |
| gender | code | male \| female \| other \| unknown |
| organization | Reference(Organization) | Organization that is the contact |
| period | Period | Period during which contact is valid |

**Constraint:** SHALL contain contact details or organization reference.

**Relationship Value Set:** http://hl7.org/fhir/ValueSet/patient-contactrelationship (Extensible)

### communication (0..*)

Languages spoken by the patient.

| Element | Type | Description |
|---------|------|-------------|
| language | CodeableConcept | Language code (BCP-47) |
| preferred | boolean | Is this the preferred language? |

**System:** `urn:ietf:bcp:47` (BCP 47 language tags)

### generalPractitioner (0..*)

| Type | Description |
|------|-------------|
| Reference(Organization \| Practitioner \| PractitionerRole) | Patient's nominated primary care provider |

### managingOrganization (0..1)

| Type | Description |
|------|-------------|
| Reference(Organization) | Organization that is custodian of the patient record |

### link (0..*)

Links to other patient resources that concern the same person. This is a **modifier element**.

| Element | Type | Description |
|---------|------|-------------|
| other | Reference(Patient \| RelatedPerson) | The other patient or related person (1..1) |
| type | code | replaced-by \| replaces \| refer \| seealso (1..1) |

**Link Type Value Set:** http://hl7.org/fhir/ValueSet/link-type (Required)

| Code | Display | Definition |
|------|---------|------------|
| replaced-by | Replaced-by | This patient resource is replaced by another patient resource |
| replaces | Replaces | This patient resource replaces another patient resource |
| refer | Refer | More information on another patient resource |
| seealso | See also | Patient resources may have duplicate records |

## Modifier Elements

The following elements are modifier elements that can change the meaning of the resource:

| Element | Impact |
|---------|--------|
| active | Affects interpretation - if false, this record should not be treated as valid |
| deceased[x] | Affects understanding of patient availability |
| link | May indicate this record should not be used (if replaced-by) |

## US Core Extensions

### us-core-race

Extension URL: `http://hl7.org/fhir/us/core/StructureDefinition/us-core-race`

| Extension | Type | Description |
|-----------|------|-------------|
| ombCategory | Coding | OMB race category (0..5) |
| detailed | Coding | Detailed race codes (0..*) |
| text | string | Race text description (1..1) |

### us-core-ethnicity

Extension URL: `http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity`

| Extension | Type | Description |
|-----------|------|-------------|
| ombCategory | Coding | OMB ethnicity category (0..1) |
| detailed | Coding | Detailed ethnicity codes (0..*) |
| text | string | Ethnicity text description (1..1) |

### us-core-birthsex

Extension URL: `http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex`

| Type | Values |
|------|--------|
| code | F \| M \| UNK |

## US Core Conformance Requirements

For US Core Patient profile compliance:

1. **SHALL** support `identifier`
2. **SHALL** support `identifier.system`
3. **SHALL** support `identifier.value`
4. **SHALL** support `name`
5. **SHALL** support `name.family`
6. **SHALL** support `name.given`
7. **SHALL** support `gender`
8. **SHOULD** support `birthDate`
9. **SHOULD** support `address`
10. **SHOULD** support `telecom`
11. **SHALL** support `us-core-race` extension
12. **SHALL** support `us-core-ethnicity` extension
13. **SHALL** support `us-core-birthsex` extension

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| identifier | token | Patient identifier |
| name | string | Patient name (any part) |
| family | string | Family name |
| given | string | Given name |
| birthdate | date | Patient's date of birth |
| gender | token | Gender of the patient |
| address | string | Any address part |
| address-city | string | City |
| address-state | string | State |
| address-postalcode | string | Postal code |
| telecom | token | Contact point value |
| email | token | Email address |
| phone | token | Phone number |

## Compartments

The Patient resource is part of the following compartments:
- Patient
- Practitioner
- RelatedPerson

## Related Resources

The Patient resource is referenced by over 70 other FHIR resources including:
- Account, AllergyIntolerance, Appointment, CarePlan, Claim
- Condition, Consent, Coverage, Encounter, ExplanationOfBenefit
- Immunization, MedicationRequest, Observation, Procedure
- And many others

## References

- FHIR R4B Patient: https://hl7.org/fhir/R4B/patient.html
- US Core Patient Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient
- US Core Implementation Guide: http://hl7.org/fhir/us/core/
- FHIR Data Types: https://hl7.org/fhir/R4B/datatypes.html
