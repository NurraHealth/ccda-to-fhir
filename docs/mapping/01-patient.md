# Patient Mapping: C-CDA recordTarget ↔ FHIR Patient

This document provides detailed mapping guidance between C-CDA `recordTarget/patientRole` and FHIR `Patient` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| `recordTarget/patientRole` | `Patient` |
| Location: Document header | Resource type: Patient |

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `patientRole/id` | `Patient.identifier` | [ID → Identifier](#identifier-mapping) |
| `patientRole/addr` | `Patient.address` | [Addr → Address](#address-mapping) |
| `patientRole/telecom` | `Patient.telecom` | [Telecom → ContactPoint](#telecom-mapping) |
| `patientRole/patient/name` | `Patient.name` | [Name → HumanName](#name-mapping) |
| `patientRole/patient/administrativeGenderCode` | `Patient.gender` | [Gender ConceptMap](#gender-mapping) |
| `patientRole/patient/birthTime` | `Patient.birthDate` | Date conversion |
| `patientRole/patient/sdtc:deceasedInd` | `Patient.deceasedBoolean` | Direct mapping |
| `patientRole/patient/sdtc:deceasedTime` | `Patient.deceasedDateTime` | Date conversion |
| `patientRole/patient/maritalStatusCode` | `Patient.maritalStatus` | CodeableConcept |
| `patientRole/patient/raceCode` | `Patient.extension:us-core-race` | [Race Extension](#race-extension) |
| `patientRole/patient/sdtc:raceCode` | `Patient.extension:us-core-race` | [Race Extension](#race-extension) |
| `patientRole/patient/ethnicGroupCode` | `Patient.extension:us-core-ethnicity` | [Ethnicity Extension](#ethnicity-extension) |
| `patientRole/patient/sdtc:ethnicGroupCode` | `Patient.extension:us-core-ethnicity` | [Ethnicity Extension](#ethnicity-extension) |
| `patientRole/patient/religiousAffiliationCode` | `Patient.extension:patient-religion` | ValueCodeableConcept |
| `patientRole/patient/birthplace/place/addr` | `Patient.extension:patient-birthPlace` | ValueAddress |
| `patientRole/patient/guardian` | `Patient.contact` | [Guardian → Contact](#guardian-mapping) |
| `patientRole/patient/languageCommunication` | `Patient.communication` | [Language Communication](#language-mapping) |
| `patientRole/providerOrganization` | `Patient.managingOrganization` | Reference(Organization) |

### Identifier Mapping

Convert CDA `id` elements to FHIR `identifier`:

**C-CDA:**
```xml
<patientRole>
  <id root="2.16.840.1.113883.19.5" extension="998991"/>
  <id root="2.16.840.1.113883.4.1" extension="111-00-2330"/>
</patientRole>
```

**FHIR:**
```json
{
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5",
      "value": "998991"
    },
    {
      "system": "http://hl7.org/fhir/sid/us-ssn",
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
          "code": "SS"
        }]
      },
      "value": "111-00-2330"
    }
  ]
}
```

**Well-Known Identifier Systems:**

| CDA OID | FHIR System | Type Code |
|---------|-------------|-----------|
| `2.16.840.1.113883.4.1` | `http://hl7.org/fhir/sid/us-ssn` | `SS` |
| `2.16.840.1.113883.4.6` | `http://hl7.org/fhir/sid/us-npi` | `NPI` |
| Hospital-specific OID | `urn:oid:{OID}` | `MR` |

### Name Mapping

**C-CDA:**
```xml
<patient>
  <name use="L">
    <given>Ellen</given>
    <given>Marie</given>
    <family>Ross</family>
    <suffix>MD</suffix>
  </name>
  <name use="P">
    <given>Ellie</given>
  </name>
</patient>
```

**FHIR:**
```json
{
  "name": [
    {
      "use": "usual",
      "family": "Ross",
      "given": ["Ellen", "Marie"],
      "suffix": ["MD"]
    },
    {
      "use": "nickname",
      "given": ["Ellie"]
    }
  ]
}
```

**Name Use Mapping:**

| CDA @use | FHIR use |
|----------|----------|
| `L` (Legal) | `usual` |
| `OR` (Official Record) | `official` |
| `C` (License) | `old` |
| `P` (Pseudonym) | `nickname` |
| `A` (Artist) | `anonymous` |
| `ASGN` (Assigned) | `usual` |
| (maiden context) | `maiden` |

### Gender Mapping

**C-CDA:**
```xml
<administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"
                          displayName="Female"/>
```

**FHIR:**
```json
{
  "gender": "female"
}
```

**Gender ConceptMap:**

| CDA Code | FHIR Code |
|----------|-----------|
| `F` | `female` |
| `M` | `male` |
| `UN` | `other` |
| `UNK` | `unknown` |

### Address Mapping

**C-CDA:**
```xml
<addr use="HP">
  <streetAddressLine>1357 Amber Drive</streetAddressLine>
  <city>Beaverton</city>
  <state>OR</state>
  <postalCode>97867</postalCode>
  <country>US</country>
</addr>
```

**FHIR:**
```json
{
  "address": [{
    "use": "home",
    "type": "physical",
    "line": ["1357 Amber Drive"],
    "city": "Beaverton",
    "state": "OR",
    "postalCode": "97867",
    "country": "US"
  }]
}
```

**Address Use Mapping:**

| CDA @use | FHIR use |
|----------|----------|
| `H` | `home` |
| `HP` (primary home) | `home` |
| `HV` (vacation home) | `home` |
| `WP` (work) | `work` |
| `DIR` (direct) | `work` |
| `PUB` (public) | `work` |
| `TMP` | `temp` |
| `BAD` | `old` |

### Telecom Mapping

**C-CDA:**
```xml
<telecom use="HP" value="tel:+1(555)555-2003"/>
<telecom use="MC" value="tel:+1(555)555-2004"/>
<telecom value="mailto:ellen@email.com"/>
```

**FHIR:**
```json
{
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
  ]
}
```

**Telecom Parsing:**
1. Extract system from value prefix: `tel:` → `phone`, `mailto:` → `email`, `fax:` → `fax`
2. Remove prefix from value
3. Map `@use` to FHIR use code

**Telecom Use Mapping:**

| CDA @use | FHIR use |
|----------|----------|
| `HP` (home phone) | `home` |
| `WP` (work phone) | `work` |
| `MC` (mobile) | `mobile` |
| `TMP` | `temp` |
| `BAD` | `old` |

### BirthDate and BirthTime

**C-CDA:**
```xml
<birthTime value="19750501"/>
```

**FHIR:**
```json
{
  "birthDate": "1975-05-01"
}
```

**Precision Notes:**
- If CDA `birthTime` includes time component (e.g., `19750501103022`), use the `patient-birthTime` extension for full precision:

```json
{
  "birthDate": "1975-05-01",
  "_birthDate": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
      "valueDateTime": "1975-05-01T10:30:22"
    }]
  }
}
```

### Deceased Mapping

**C-CDA (using SDTC extension):**
```xml
<patient>
  <sdtc:deceasedInd value="true"/>
  <sdtc:deceasedTime value="20200315"/>
</patient>
```

**FHIR:**
```json
{
  "deceasedDateTime": "2020-03-15"
}
```

**Rules:**
- Only one `deceased[x]` element allowed in FHIR
- If both `deceasedInd` and `deceasedTime` present, use `deceasedDateTime`
- If only `deceasedInd="true"`, use `deceasedBoolean: true`

### Race Extension

US Core requires the `us-core-race` extension for race data.

**C-CDA:**
```xml
<patient>
  <raceCode code="2106-3" codeSystem="2.16.840.1.113883.6.238"
            displayName="White"/>
  <sdtc:raceCode code="2076-8" codeSystem="2.16.840.1.113883.6.238"
                 displayName="Native Hawaiian or Other Pacific Islander"/>
</patient>
```

**FHIR:**
```json
{
  "extension": [{
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
  }]
}
```

**Categorization Rules:**
- OMB-defined categories (5 main race categories) → `ombCategory` sub-extension
- Detailed race codes → `detailed` sub-extension
- Consolidate all `originalText` values with comma delimiter → `text` sub-extension (required)

**OMB Race Categories:**

| Code | Display |
|------|---------|
| `1002-5` | American Indian or Alaska Native |
| `2028-9` | Asian |
| `2054-5` | Black or African American |
| `2076-8` | Native Hawaiian or Other Pacific Islander |
| `2106-3` | White |

### Ethnicity Extension

**C-CDA:**
```xml
<patient>
  <ethnicGroupCode code="2186-5" codeSystem="2.16.840.1.113883.6.238"
                   displayName="Not Hispanic or Latino"/>
</patient>
```

**FHIR:**
```json
{
  "extension": [{
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
  }]
}
```

**OMB Ethnicity Categories:**

| Code | Display |
|------|---------|
| `2135-2` | Hispanic or Latino |
| `2186-5` | Not Hispanic or Latino |

### Guardian Mapping

**C-CDA:**
```xml
<guardian>
  <code code="GUARD" codeSystem="2.16.840.1.113883.5.111"
        displayName="Guardian"/>
  <addr>
    <streetAddressLine>1357 Amber Drive</streetAddressLine>
    <city>Beaverton</city>
    <state>OR</state>
  </addr>
  <telecom use="HP" value="tel:+1(555)555-2005"/>
  <guardianPerson>
    <name>
      <given>Martha</given>
      <family>Ross</family>
    </name>
  </guardianPerson>
</guardian>
```

**FHIR:**
```json
{
  "contact": [{
    "relationship": [
      {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
          "code": "GUARD",
          "display": "Guardian"
        }]
      }
    ],
    "name": {
      "family": "Ross",
      "given": ["Martha"]
    },
    "telecom": [{
      "system": "phone",
      "value": "+1(555)555-2005",
      "use": "home"
    }],
    "address": {
      "line": ["1357 Amber Drive"],
      "city": "Beaverton",
      "state": "OR"
    }
  }]
}
```

**Rules:**
- Always include `GUARD` code from v3-RoleCode in relationship
- Prepend guardian code if a more specific code is present in CDA

### Language Communication Mapping

**C-CDA:**
```xml
<languageCommunication>
  <languageCode code="en"/>
  <modeCode code="ESP" codeSystem="2.16.840.1.113883.5.60"
            displayName="Expressed spoken"/>
  <proficiencyLevelCode code="G" codeSystem="2.16.840.1.113883.5.61"
                        displayName="Good"/>
  <preferenceInd value="true"/>
</languageCommunication>
```

**FHIR:**
```json
{
  "communication": [{
    "language": {
      "coding": [{
        "system": "urn:ietf:bcp:47",
        "code": "en",
        "display": "English"
      }]
    },
    "preferred": true,
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/patient-proficiency",
      "extension": [
        {
          "url": "type",
          "valueCoding": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityMode",
            "code": "ESP",
            "display": "Expressed spoken"
          }
        },
        {
          "url": "level",
          "valueCoding": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityProficiency",
            "code": "G",
            "display": "Good"
          }
        }
      ]
    }]
  }]
}
```

**Notes:**
- `modeCode` and `proficiencyLevelCode` combine into single `patient-proficiency` extension
- Language code should conform to BCP-47

## FHIR to C-CDA Mapping

Reverse the mappings above with these considerations:

### Key Differences

| FHIR Element | C-CDA Element | Notes |
|--------------|---------------|-------|
| `Patient.gender` | `administrativeGenderCode` | Reverse ConceptMap |
| `Patient.birthDate` | `birthTime` | Convert format |
| `Patient.deceasedDateTime` | `sdtc:deceasedTime` + `sdtc:deceasedInd` | Set both |
| `Patient.deceasedBoolean` | `sdtc:deceasedInd` | Boolean only |
| US Core extensions | SDTC elements | Race/ethnicity |

### FHIR Gender to CDA

| FHIR Code | CDA Code |
|-----------|----------|
| `female` | `F` |
| `male` | `M` |
| `other` | `UN` |
| `unknown` | `UNK` |

## Complete Example

### C-CDA Input

```xml
<recordTarget>
  <patientRole>
    <id root="2.16.840.1.113883.19.5" extension="998991"/>
    <addr use="HP">
      <streetAddressLine>1357 Amber Drive</streetAddressLine>
      <city>Beaverton</city>
      <state>OR</state>
      <postalCode>97867</postalCode>
      <country>US</country>
    </addr>
    <telecom use="HP" value="tel:+1(555)555-2003"/>
    <patient>
      <name use="L">
        <given>Ellen</given>
        <family>Ross</family>
      </name>
      <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
      <birthTime value="19750501"/>
      <maritalStatusCode code="M" codeSystem="2.16.840.1.113883.5.2"
                         displayName="Married"/>
      <raceCode code="2106-3" codeSystem="2.16.840.1.113883.6.238"
                displayName="White"/>
      <ethnicGroupCode code="2186-5" codeSystem="2.16.840.1.113883.6.238"
                       displayName="Not Hispanic or Latino"/>
      <languageCommunication>
        <languageCode code="en"/>
        <preferenceInd value="true"/>
      </languageCommunication>
    </patient>
    <providerOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
    </providerOrganization>
  </patientRole>
</recordTarget>
```

### FHIR Output

```json
{
  "resourceType": "Patient",
  "id": "patient-example",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
  },
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5",
    "value": "998991"
  }],
  "name": [{
    "use": "usual",
    "family": "Ross",
    "given": ["Ellen"]
  }],
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-2003",
    "use": "home"
  }],
  "gender": "female",
  "birthDate": "1975-05-01",
  "address": [{
    "use": "home",
    "line": ["1357 Amber Drive"],
    "city": "Beaverton",
    "state": "OR",
    "postalCode": "97867",
    "country": "US"
  }],
  "maritalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
      "code": "M",
      "display": "Married"
    }]
  },
  "communication": [{
    "language": {
      "coding": [{
        "system": "urn:ietf:bcp:47",
        "code": "en"
      }]
    },
    "preferred": true
  }],
  "managingOrganization": {
    "reference": "Organization/org-example",
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
          "url": "text",
          "valueString": "White"
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
    }
  ]
}
```

## References

- [C-CDA on FHIR Patient Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-patient.html)
- [US Core Patient Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient)
- [C-CDA US Realm Header](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.1.1.html)
