# FHIR R4B: Practitioner Resource

## Overview

The Practitioner resource represents a person who is directly or indirectly involved in the provisioning of healthcare or related services. This includes physicians, nurses, pharmacists, therapists, technicians, social workers, and other healthcare providers. It also includes service animals.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Practitioner |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Individual |
| Responsible Work Group | Patient Administration |
| URL | https://hl7.org/fhir/R4B/practitioner.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner |

## Scope and Usage

The resource encompasses diverse healthcare professionals including:
- Physicians, nurses, therapists, technicians
- Social workers, pharmacists
- Service animals

**Key Distinctions:**
- **Practitioner vs. RelatedPerson:** Practitioner operates on behalf of care organizations across multiple patients. RelatedPerson applies to those with personal relationships to individual patients.
- **Informal caregivers** without formal responsibilities should use the RelatedPerson resource instead.
- **PractitionerRole** provides detailed role authorizations and organizational affiliations.
- **CareTeam** independently groups practitioners for specific contexts.
- **Device** resource represents autonomous/AI systems.

## JSON Structure

```json
{
  "resourceType": "Practitioner",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"
    ]
  },
  "identifier": [
    {
      "system": "http://hl7.org/fhir/sid/us-npi",
      "value": "1234567890"
    },
    {
      "system": "http://hospital.example.org/practitioner",
      "value": "2981823"
    }
  ],
  "active": true,
  "name": [
    {
      "use": "official",
      "family": "Careful",
      "given": ["Adam"],
      "prefix": ["Dr."],
      "suffix": ["MD"]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-1002",
      "use": "work"
    },
    {
      "system": "email",
      "value": "dr.careful@hospital.org"
    }
  ],
  "address": [
    {
      "use": "work",
      "type": "physical",
      "line": ["1001 Village Avenue"],
      "city": "Portland",
      "state": "OR",
      "postalCode": "99123",
      "country": "US"
    }
  ],
  "gender": "male",
  "birthDate": "1971-11-07",
  "qualification": [
    {
      "identifier": [
        {
          "system": "http://example.org/license",
          "value": "MD12345"
        }
      ],
      "code": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0360",
            "code": "MD",
            "display": "Doctor of Medicine"
          }
        ],
        "text": "Medical Doctor"
      },
      "period": {
        "start": "1999-06-15"
      },
      "issuer": {
        "display": "State Medical Board"
      }
    },
    {
      "code": {
        "coding": [
          {
            "system": "http://nucc.org/provider-taxonomy",
            "code": "207Q00000X",
            "display": "Family Medicine Physician"
          }
        ]
      }
    }
  ],
  "communication": [
    {
      "coding": [
        {
          "system": "urn:ietf:bcp:47",
          "code": "en",
          "display": "English"
        }
      ]
    },
    {
      "coding": [
        {
          "system": "urn:ietf:bcp:47",
          "code": "es",
          "display": "Spanish"
        }
      ]
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

Business identifiers for the practitioner.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| secondary \| old |
| type | CodeableConcept | Type of identifier |
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| period | Period | Time period when identifier is/was valid |
| assigner | Reference(Organization) | Organization that assigned the identifier |

**Common Identifier Systems:**
| System URI | Description |
|------------|-------------|
| `http://hl7.org/fhir/sid/us-npi` | US National Provider Identifier |
| `urn:oid:2.16.840.1.113883.4.6` | NPI (OID form) |
| `http://hl7.org/fhir/sid/us-ssn` | US Social Security Number |

### active (0..1)

This is a **modifier element**.

| Type | Description |
|------|-------------|
| boolean | Whether the practitioner's record is in active use |

**Note:** Affects interpretation of other data when false.

### name (0..*)

The name(s) associated with the practitioner.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| nickname \| anonymous \| old \| maiden |
| text | string | Full text representation of name |
| family | string | Family name (surname) |
| given | string[] | Given names (not only first) |
| prefix | string[] | Parts before the name (Dr., Mr., etc.) |
| suffix | string[] | Parts after the name (MD, Jr., etc.) |
| period | Period | Time period when name was/is in use |

### telecom (0..*)

Contact details for the practitioner.

| Element | Type | Description |
|---------|------|-------------|
| system | code | phone \| fax \| email \| pager \| url \| sms \| other |
| value | string | The actual contact point details |
| use | code | home \| work \| temp \| old \| mobile |
| rank | positiveInt | Preferred order of use |
| period | Period | Time period when contact was/is in use |

### address (0..*)

Addresses for the practitioner.

| Element | Type | Description |
|---------|------|-------------|
| use | code | home \| work \| temp \| old \| billing |
| type | code | postal \| physical \| both |
| text | string | Full text representation |
| line | string[] | Street name, number, direction, etc. |
| city | string | City, town, village |
| district | string | District/county |
| state | string | Sub-unit of country |
| postalCode | string | Postal code |
| country | string | Country code |
| period | Period | Time period when address was/is in use |

### gender (0..1)

Administrative gender.

| Type | Values |
|------|--------|
| code | male \| female \| other \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/administrative-gender (Required binding)

### birthDate (0..1)

| Type | Format |
|------|--------|
| date | YYYY, YYYY-MM, or YYYY-MM-DD |

### deceased[x] (0..1)

Indicates if the practitioner is deceased. This is a **modifier element**.

| Element | Type | Description |
|---------|------|-------------|
| deceasedBoolean | boolean | Whether practitioner is deceased |
| deceasedDateTime | dateTime | Date and time of death |

**Note:** Affects understanding of practitioner availability.

### photo (0..*)

| Type | Description |
|------|-------------|
| Attachment | Image of the practitioner |

### qualification (0..*)

Qualifications, certifications, licenses, etc.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| identifier | Identifier[] | 0..* | Identifier for this qualification |
| code | CodeableConcept | 1..1 | Coded representation of qualification (Required) |
| status | CodeableConcept | 0..1 | Status of the qualification |
| period | Period | 0..1 | Period during which qualification is valid |
| issuer | Reference(Organization) | 0..1 | Organization that issued the qualification |

**code Value Set:** http://hl7.org/fhir/ValueSet/v2-2.7-0360 (Example binding)

**status Value Set:** http://hl7.org/fhir/ValueSet/qualification-status (Preferred binding)

**Common Qualification Code Systems:**
| System URI | Description |
|------------|-------------|
| `http://terminology.hl7.org/CodeSystem/v2-0360` | HL7 Degree/License/Certificate |
| `http://nucc.org/provider-taxonomy` | NUCC Healthcare Provider Taxonomy |

**Degree/License Codes (v2-0360):**
| Code | Display |
|------|---------|
| MD | Doctor of Medicine |
| DO | Doctor of Osteopathy |
| RN | Registered Nurse |
| NP | Nurse Practitioner |
| PA | Physician Assistant |
| PharmD | Doctor of Pharmacy |
| DDS | Doctor of Dental Surgery |
| DMD | Doctor of Dental Medicine |
| DPM | Doctor of Podiatric Medicine |
| PhD | Doctor of Philosophy |
| BS | Bachelor of Science |
| MS | Master of Science |
| RPh | Registered Pharmacist |

**Common NUCC Taxonomy Codes:**
| Code | Display |
|------|---------|
| 207Q00000X | Family Medicine Physician |
| 207R00000X | Internal Medicine Physician |
| 208D00000X | General Practice Physician |
| 207V00000X | Obstetrics & Gynecology Physician |
| 208600000X | Surgery Physician |
| 163W00000X | Registered Nurse |
| 363L00000X | Nurse Practitioner |
| 367500000X | Nurse Anesthetist |
| 1223G0001X | General Dentist |
| 152W00000X | Optometrist |
| 183500000X | Pharmacist |
| 261QM1300X | Multi-Specialty Clinic |

### communication (0..*)

Languages the practitioner can use in communication.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| language | CodeableConcept | 1..1 | Language code (BCP-47) - Required |
| preferred | boolean | 0..1 | Language preference indicator |

**language Value Set:** http://hl7.org/fhir/ValueSet/all-languages (Required binding)

**System:** `urn:ietf:bcp:47` (BCP 47 language tags)

**Common Language Codes:**
| Code | Display |
|------|---------|
| en | English |
| es | Spanish |
| fr | French |
| de | German |
| zh | Chinese |
| pt | Portuguese |
| ar | Arabic |
| ru | Russian |
| ja | Japanese |
| ko | Korean |

## Related Resources

### PractitionerRole

Links a Practitioner to an Organization with specific roles, specialties, and locations.

```json
{
  "resourceType": "PractitionerRole",
  "id": "example",
  "practitioner": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "organization": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "code": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/practitioner-role",
          "code": "doctor",
          "display": "Doctor"
        }
      ]
    }
  ],
  "specialty": [
    {
      "coding": [
        {
          "system": "http://nucc.org/provider-taxonomy",
          "code": "207Q00000X",
          "display": "Family Medicine Physician"
        }
      ]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-1002",
      "use": "work"
    }
  ],
  "availableTime": [
    {
      "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
      "availableStartTime": "08:00:00",
      "availableEndTime": "17:00:00"
    }
  ]
}
```

**PractitionerRole Code Values:**
| Code | Display |
|------|---------|
| doctor | Doctor |
| nurse | Nurse |
| pharmacist | Pharmacist |
| researcher | Researcher |
| teacher | Teacher/Educator |
| ict | ICT professional |

## US Core Conformance Requirements

For US Core Practitioner profile compliance:

1. **SHALL** support `identifier`
2. **SHALL** support `identifier.system`
3. **SHALL** support `identifier.value`
4. **SHALL** support `name`
5. **SHALL** support `name.family`

For NPI compliance:
- **SHALL** include NPI when available
- NPI system: `http://hl7.org/fhir/sid/us-npi`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| identifier | token | Practitioner identifier |
| name | string | Practitioner name (any part) |
| family | string | Family name |
| given | string | Given name |
| active | token | Whether the practitioner is active |
| address | string | Any address part |
| address-city | string | City |
| address-state | string | State |
| address-postalcode | string | Postal code |
| telecom | token | Contact point value |
| email | token | Email address |
| phone | token | Phone number |
| gender | token | Gender |
| communication | token | Language |

## Modifier Elements

The following elements are modifier elements:
- **active** - Affects interpretation of other data when false
- **deceased[x]** - Affects understanding of practitioner availability

## Compartments

The Practitioner resource is part of the following compartments:
- Practitioner

## References

- FHIR R4B Practitioner: https://hl7.org/fhir/R4B/practitioner.html
- FHIR R4B PractitionerRole: https://hl7.org/fhir/R4B/practitionerrole.html
- US Core Practitioner Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner
- NUCC Healthcare Provider Taxonomy: https://nucc.org/
- BCP 47 Language Tags: https://www.ietf.org/rfc/bcp/bcp47.txt
