# Practitioner Mapping: C-CDA Participation ↔ FHIR Practitioner/PractitionerRole/Organization

This document provides detailed mapping guidance for C-CDA participation elements (author, performer, informant, participant) to FHIR `Practitioner`, `PractitionerRole`, and `Organization` resources.

## Overview

C-CDA participation elements appear throughout the document and entries:

| C-CDA Element | Context | FHIR Resources |
|---------------|---------|----------------|
| `author` | Document header, entries | `Practitioner`, `PractitionerRole`, `Organization` |
| `performer` | Entries | `Practitioner`, `PractitionerRole` |
| `informant` | Document header, entries | `Practitioner`, `RelatedPerson`, `Patient` |
| `participant` | Document header, entries | Various based on typeCode |
| `legalAuthenticator` | Document header | `Practitioner` |
| `authenticator` | Document header | `Practitioner` |
| `dataEnterer` | Document header | `Practitioner` |
| `custodian` | Document header | `Organization` |

## Author Mapping

### C-CDA Author Structure

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
          displayName="Family Medicine"/>
    <addr>
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
    </addr>
    <telecom use="WP" value="tel:+1(555)555-1002"/>
    <assignedPerson>
      <name>
        <given>Adam</given>
        <family>Careful</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
      <telecom use="WP" value="tel:+1(555)555-5000"/>
      <addr>
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
      </addr>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Mapping to FHIR Resources

An `assignedAuthor` typically generates three FHIR resources:

#### 1. Practitioner

| C-CDA Path | FHIR Path |
|------------|-----------|
| `assignedAuthor/id` | `Practitioner.identifier` |
| `assignedPerson/name` | `Practitioner.name` |
| `assignedAuthor/addr` | `Practitioner.address` |
| `assignedAuthor/telecom` | `Practitioner.telecom` |

```json
{
  "resourceType": "Practitioner",
  "id": "practitioner-careful",
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "1234567890"
  }],
  "name": [{
    "family": "Careful",
    "given": ["Adam"],
    "suffix": ["MD"]
  }],
  "address": [{
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  }],
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-1002",
    "use": "work"
  }]
}
```

#### 2. Organization

| C-CDA Path | FHIR Path |
|------------|-----------|
| `representedOrganization/id` | `Organization.identifier` |
| `representedOrganization/name` | `Organization.name` |
| `representedOrganization/addr` | `Organization.address` |
| `representedOrganization/telecom` | `Organization.telecom` |

```json
{
  "resourceType": "Organization",
  "id": "org-community-health",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5.9999.1393",
    "value": "2.16.840.1.113883.19.5.9999.1393"
  }],
  "name": "Community Health and Hospitals",
  "address": [{
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  }],
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-5000",
    "use": "work"
  }]
}
```

#### 3. PractitionerRole

| C-CDA Path | FHIR Path |
|------------|-----------|
| `assignedAuthor/code` | `PractitionerRole.specialty` |
| `assignedAuthor/id` (context) | `PractitionerRole.identifier` |
| — | `PractitionerRole.practitioner` |
| — | `PractitionerRole.organization` |

```json
{
  "resourceType": "PractitionerRole",
  "id": "practitionerrole-careful",
  "practitioner": {
    "reference": "Practitioner/practitioner-careful"
  },
  "organization": {
    "reference": "Organization/org-community-health"
  },
  "specialty": [{
    "coding": [{
      "system": "http://nucc.org/provider-taxonomy",
      "code": "207Q00000X",
      "display": "Family Medicine"
    }]
  }]
}
```

### Author Time

The `author/time` element maps to the resource's recorded date:

| Context | FHIR Target |
|---------|-------------|
| Document author | `Composition.date` |
| Condition author | `Condition.recordedDate` |
| AllergyIntolerance author | `AllergyIntolerance.recordedDate` |
| Procedure author | `Procedure.recorded` (extension) |
| MedicationRequest author | `MedicationRequest.authoredOn` |

### Multiple Authors

When multiple authors exist:
- **Latest author** → Resource's direct author/recorder reference
- **Earliest author/time** → Resource's recordedDate
- **All authors** → Provenance resource

## Performer Mapping

### C-CDA Performer Structure

```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <code code="59058001" codeSystem="2.16.840.1.113883.6.96"
          displayName="General physician"/>
    <assignedPerson>
      <name>
        <given>John</given>
        <family>Surgeon</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>
    <representedOrganization>
      <name>City Hospital</name>
    </representedOrganization>
  </assignedEntity>
</performer>
```

### Mapping to FHIR

| C-CDA Path | FHIR Path |
|------------|-----------|
| `performer/assignedEntity/id` | `Practitioner.identifier` |
| `performer/assignedEntity/code` | `PractitionerRole.specialty` |
| `performer/functionCode` | `Procedure.performer.function` or `Encounter.participant.type` |
| `assignedPerson/name` | `Practitioner.name` |
| `representedOrganization` | `Organization` |

### Function Codes

| C-CDA functionCode | FHIR participant.type |
|--------------------|----------------------|
| `PCP` | `PPRF` (primary performer) |
| `ATTPHYS` | `ATND` (attender) |
| `ADMPHYS` | `ADM` (admitter) |
| `DISPHYS` | `DIS` (discharger) |
| `ANEST` | `SPRF` (secondary performer) |
| `RNDPHYS` | `ATND` (attender) |
| `PRISURG` | `PPRF` (primary performer) |
| `FASST` | `SPRF` (secondary performer) |
| `ANRS` | `SPRF` (secondary performer) |
| `MDWF` | `PPRF` (primary performer) |
| `NASST` | `SPRF` (secondary performer) |
| `SNRS` | `SPRF` (secondary performer) |
| `SASST` | `SPRF` (secondary performer) |
| `TASST` | `SPRF` (secondary performer) |

## Informant Mapping

### Types of Informants

1. **assignedEntity** → Maps to `Practitioner`
2. **relatedEntity** → Maps to `RelatedPerson` or `Patient`

### Related Entity (Non-Practitioner)

**C-CDA:**
```xml
<informant>
  <relatedEntity classCode="PRS">
    <code code="MTH" codeSystem="2.16.840.1.113883.5.111"
          displayName="Mother"/>
    <relatedPerson>
      <name>
        <given>Martha</given>
        <family>Ross</family>
      </name>
    </relatedPerson>
  </relatedEntity>
</informant>
```

**FHIR RelatedPerson:**
```json
{
  "resourceType": "RelatedPerson",
  "id": "related-mother",
  "patient": {
    "reference": "Patient/patient-example"
  },
  "relationship": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "MTH",
      "display": "Mother"
    }]
  }],
  "name": [{
    "family": "Ross",
    "given": ["Martha"]
  }]
}
```

## Custodian Mapping

**C-CDA:**
```xml
<custodian>
  <assignedCustodian>
    <representedCustodianOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
      <telecom use="WP" value="tel:+1(555)555-5000"/>
      <addr>
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
      </addr>
    </representedCustodianOrganization>
  </assignedCustodian>
</custodian>
```

**FHIR Organization:**
```json
{
  "resourceType": "Organization",
  "id": "org-custodian",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5.9999.1393",
    "value": "2.16.840.1.113883.19.5.9999.1393"
  }],
  "name": "Community Health and Hospitals",
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-5000",
    "use": "work"
  }],
  "address": [{
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  }]
}
```

The custodian organization is referenced from `Composition.custodian`.

## Legal Authenticator Mapping

**C-CDA:**
```xml
<legalAuthenticator>
  <time value="20200301"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>Adam</given>
        <family>Careful</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</legalAuthenticator>
```

Maps to `Composition.attester` with mode="legal":

```json
{
  "attester": [{
    "mode": "legal",
    "time": "2020-03-01",
    "party": {
      "reference": "Practitioner/practitioner-careful"
    }
  }]
}
```

## Authenticator Mapping

Per C-CDA R2, the authenticator represents "a participant who has attested to the accuracy of the document, but who does not have privileges to legally authenticate the document." Example: a resident physician who sees a patient and dictates a note, then later signs it.

**C-CDA:**
```xml
<authenticator>
  <time value="20200302"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
    <assignedPerson>
      <name>
        <given>Jane</given>
        <family>Resident</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</authenticator>
```

Maps to `Composition.attester` with mode="professional":

```json
{
  "attester": [{
    "mode": "professional",
    "time": "2020-03-02",
    "party": {
      "reference": "Practitioner/practitioner-resident"
    }
  }]
}
```

### Multiple Attesters

A document can have both legal and professional attesters:

```json
{
  "attester": [
    {
      "mode": "legal",
      "time": "2020-03-01",
      "party": {
        "reference": "Practitioner/practitioner-careful"
      }
    },
    {
      "mode": "professional",
      "time": "2020-03-02",
      "party": {
        "reference": "Practitioner/practitioner-resident"
      }
    }
  ]
}
```

Per US Realm Header Profile:
- Legal attester (0..1 cardinality)
- Professional attester (0..* cardinality) - multiple authenticators supported
- Personal attester (0..* cardinality) - not commonly used in C-CDA documents

## Provenance Resource

For complete author tracking, create a Provenance resource:

**FHIR Provenance:**
```json
{
  "resourceType": "Provenance",
  "id": "provenance-condition",
  "target": [{
    "reference": "Condition/condition-example"
  }],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [
    {
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
          "code": "author"
        }]
      },
      "who": {
        "reference": "Practitioner/practitioner-careful"
      },
      "onBehalfOf": {
        "reference": "Organization/org-community-health"
      }
    }
  ]
}
```

### Provenance Agent Types

| CDA Role | Provenance agent.type |
|----------|----------------------|
| author | `author` |
| performer | `performer` |
| informant | `informant` |
| dataEnterer | `enterer` |
| legal authenticator | `attester` |
| custodian | `custodian` |

## Device as Author

When `assignedAuthoringDevice` is present instead of `assignedPerson`:

**C-CDA:**
```xml
<author>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Epic EHR</manufacturerModelName>
      <softwareName>Epic 2020</softwareName>
    </assignedAuthoringDevice>
  </assignedAuthor>
</author>
```

**FHIR Device:**
```json
{
  "resourceType": "Device",
  "id": "device-ehr",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5",
    "value": "DEVICE-001"
  }],
  "deviceName": [
    {
      "name": "Epic EHR",
      "type": "manufacturer-name"
    },
    {
      "name": "Epic 2020",
      "type": "model-name"
    }
  ]
}
```

## FHIR to C-CDA Mapping

### Creating Author from Practitioner

| FHIR Path | C-CDA Path |
|-----------|------------|
| `Practitioner.identifier` | `assignedAuthor/id` |
| `Practitioner.name` | `assignedPerson/name` |
| `Practitioner.address` | `assignedAuthor/addr` |
| `Practitioner.telecom` | `assignedAuthor/telecom` |
| `PractitionerRole.specialty` | `assignedAuthor/code` |
| `PractitionerRole.organization` | `representedOrganization` |
| `Organization.identifier` | `representedOrganization/id` |
| `Organization.name` | `representedOrganization/name` |

### Template IDs

When creating author participation:
- Author Participation: `2.16.840.1.113883.10.20.22.4.119`

## Resource Deduplication

When the same practitioner or organization appears multiple times in a document:

1. **Generate consistent IDs:** Use CDA identifier (root + extension) as basis for FHIR resource ID
2. **Reference existing resources:** Check if resource already created before creating new one
3. **Merge information:** If same entity has additional details in different contexts, merge them

**Example ID Generation:**
- NPI `1234567890` → `Practitioner/practitioner-npi-1234567890`
- OID `2.16.840.1.113883.19.5` extension `ORG-001` → `Organization/org-oid-2.16.840.1.113883.19.5-ORG-001`

## Complete Example

### C-CDA Input (Document Header)

```xml
<ClinicalDocument>
  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
            displayName="Family Medicine"/>
      <addr>
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
      </addr>
      <telecom use="WP" value="tel:+1(555)555-1002"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
      <representedOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
      </representedOrganization>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <legalAuthenticator>
    <time value="20200301"/>
    <signatureCode code="S"/>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name><given>Adam</given><family>Careful</family></name>
      </assignedPerson>
    </assignedEntity>
  </legalAuthenticator>
</ClinicalDocument>
```

### FHIR Output (Multiple Resources)

```json
[
  {
    "resourceType": "Practitioner",
    "id": "practitioner-careful",
    "identifier": [{
      "system": "http://hl7.org/fhir/sid/us-npi",
      "value": "1234567890"
    }],
    "name": [{
      "family": "Careful",
      "given": ["Adam"],
      "suffix": ["MD"]
    }],
    "address": [{
      "line": ["1001 Village Avenue"],
      "city": "Portland",
      "state": "OR",
      "postalCode": "99123"
    }],
    "telecom": [{
      "system": "phone",
      "value": "+1(555)555-1002",
      "use": "work"
    }]
  },
  {
    "resourceType": "Organization",
    "id": "org-community-health",
    "identifier": [{
      "system": "urn:oid:2.16.840.1.113883.19.5.9999.1393",
      "value": "2.16.840.1.113883.19.5.9999.1393"
    }],
    "name": "Community Health and Hospitals"
  },
  {
    "resourceType": "PractitionerRole",
    "id": "practitionerrole-careful",
    "practitioner": {
      "reference": "Practitioner/practitioner-careful"
    },
    "organization": {
      "reference": "Organization/org-community-health"
    },
    "specialty": [{
      "coding": [{
        "system": "http://nucc.org/provider-taxonomy",
        "code": "207Q00000X",
        "display": "Family Medicine"
      }]
    }]
  }
]
```

## References

- [C-CDA on FHIR Participation Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participation.html)
- [US Core Practitioner Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner)
- [US Core PractitionerRole Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitionerrole)
- [US Core Organization Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-organization)
- [C-CDA Author Participation](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.119.html)
