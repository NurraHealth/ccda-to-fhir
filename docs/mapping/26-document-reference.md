# Mapping: C-CDA ClinicalDocument to FHIR DocumentReference

## Overview

This document specifies the mapping between the C-CDA ClinicalDocument header and the FHIR DocumentReference resource. Unlike the Composition-based approach (covered in [19-composition.md](19-composition.md) and [20-bundle.md](20-bundle.md)) where the entire C-CDA document is converted to FHIR resources, the DocumentReference approach creates a lightweight index/reference to the original C-CDA document.

## Context and Relationships

### Two Approaches for C-CDA Documents in FHIR

When working with C-CDA documents in FHIR systems, there are two complementary approaches:

| Approach | FHIR Resource | Use Case | Output |
|----------|---------------|----------|--------|
| **Structured Conversion** | Composition + Bundle | Full conversion to FHIR resources | Document Bundle with all clinical data as FHIR resources |
| **Document Indexing** | DocumentReference | Index/reference to original document | DocumentReference pointing to C-CDA XML |

### When to Use DocumentReference

**Use DocumentReference when:**
- Need to index C-CDA documents for discovery and search
- Original C-CDA format must be preserved
- Full conversion to FHIR resources is not needed or not feasible
- Building a document management or health information exchange system
- Need lightweight metadata without full conversion overhead
- Supporting document upload/download workflows

**Complementary Use:**
Both approaches can coexist - a DocumentReference can point to the C-CDA, while a Composition/Bundle provides structured FHIR access to the same content.

## Standards References

| Standard | Reference |
|----------|-----------|
| **FHIR R4 DocumentReference** | https://hl7.org/fhir/R4/documentreference.html |
| **US Core DocumentReference** | http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference |
| **C-CDA R2.1** | US Realm Header Template (`2.16.840.1.113883.10.20.22.1.1`) |
| **C-CDA on FHIR IG** | http://hl7.org/fhir/us/ccda/ |
| **HL7 Document Format Codes** | http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes |

## Element-by-Element Mapping

### Document Identifiers

#### identifier (Document Instance ID)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/id/@root` | `DocumentReference.identifier[].system` | 1..1 | Convert OID to URI |
| `ClinicalDocument/id/@extension` | `DocumentReference.identifier[].value` | 1..1 | Use root as value if no extension |

**OID to URI Conversion:**
- If `@root` is a UUID: use `urn:uuid:{root}`
- If `@root` is an OID: use `urn:oid:{root}`
- No `@extension`: use `urn:ietf:rfc:3986` as system and full UUID/OID URN as value

**US Core Requirement:** At least one identifier is required.

**Example:**

C-CDA:
```xml
<ClinicalDocument>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
</ClinicalDocument>
```

FHIR:
```json
{
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
      "value": "TT988"
    }
  ]
}
```

#### masterIdentifier (Document Series ID)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/setId/@root` | `DocumentReference.masterIdentifier.system` | 0..1 | Version-independent ID |
| `ClinicalDocument/setId/@extension` | `DocumentReference.masterIdentifier.value` | 0..1 | Same ID across versions |

**Purpose:** The `setId` identifies the document series - all versions of a document share the same `setId` but have different instance `id` values.

**Example:**

C-CDA:
```xml
<ClinicalDocument>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>
  <versionNumber value="2"/>
</ClinicalDocument>
```

FHIR:
```json
{
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
      "value": "TT988"
    }
  ],
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988"
  }
}
```

### Document Status

#### status (Reference Status)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (infer from context) | `DocumentReference.status` | 1..1 | Current, superseded, or entered-in-error |

**Status Mapping Logic:**

| C-CDA Context | FHIR status | Rationale |
|---------------|-------------|-----------|
| Normal document | `current` | Default for active documents |
| Has `relatedDocument[@typeCode='RPLC']` pointing TO this doc | `superseded` | This document has been replaced |
| Error indicator | `entered-in-error` | Document was created in error |

**Important:** The `status` represents the status of the **reference**, not the document content itself.

**Example:**
```json
{
  "status": "current"
}
```

#### docStatus (Document Content Status)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (infer from context) | `DocumentReference.docStatus` | 0..1 | Status of underlying document |

**Status Mapping:**

| C-CDA Context | FHIR docStatus |
|---------------|----------------|
| Authenticated document (legalAuthenticator present with signatureCode="S") | `final` |
| Preliminary/draft indicator | `preliminary` |
| Document with amendments | `amended` |
| Erroneous document | `entered-in-error` |

**Conservative Approach:** Only populate docStatus when it can be reliably inferred from C-CDA elements (e.g., legalAuthenticator signatureCode). Omit docStatus when status is uncertain rather than defaulting to "final".

**Example:**
```json
{
  "docStatus": "final"
}
```

### Document Type and Classification

#### type (Document Type)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/code/@code` | `DocumentReference.type.coding[].code` | 1..1 | LOINC document type |
| `ClinicalDocument/code/@codeSystem` | `DocumentReference.type.coding[].system` | 1..1 | Always `http://loinc.org` |
| `ClinicalDocument/code/@displayName` | `DocumentReference.type.coding[].display` | 0..1 | Human-readable name |
| `ClinicalDocument/code/translation` | `DocumentReference.type.coding[]` | 0..* | Additional codings |
| `ClinicalDocument/code/originalText` | `DocumentReference.type.text` | 0..1 | Original text |

**US Core Requirement:** SHALL use LOINC codes where SCALE="Doc"

**Common Document Type Mappings:**

| C-CDA Template ID | LOINC Code | Display |
|-------------------|------------|---------|
| 2.16.840.1.113883.10.20.22.1.2 | 34133-9 | Summarization of Episode Note (CCD) |
| 2.16.840.1.113883.10.20.22.1.4 | 11488-4 | Consultation Note |
| 2.16.840.1.113883.10.20.22.1.8 | 18842-5 | Discharge Summary |
| 2.16.840.1.113883.10.20.22.1.1 | 34117-2 | History and Physical Note |
| 2.16.840.1.113883.10.20.22.1.6 | 11504-8 | Surgical Operation Note |
| 2.16.840.1.113883.10.20.22.1.9 | 11506-3 | Progress Note |
| 2.16.840.1.113883.10.20.22.1.7 | 28570-0 | Procedure Note |
| 2.16.840.1.113883.10.20.22.1.14 | 57133-1 | Referral Note |
| 2.16.840.1.113883.10.20.22.1.15 | 52521-2 | Overall plan of care/advance care directives |
| 2.16.840.1.113883.10.20.22.1.10 | 34111-5 | Emergency Department Note |

**Example:**

C-CDA:
```xml
<code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
      displayName="Summarization of Episode Note">
  <originalText>Continuity of Care Document</originalText>
</code>
```

FHIR:
```json
{
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "34133-9",
        "display": "Summarization of Episode Note"
      }
    ],
    "text": "Continuity of Care Document"
  }
}
```

#### category (Document Category)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (infer from type) | `DocumentReference.category[]` | 1..* | Document classification |

**US Core Requirement:** SHALL include at least one category. For clinical documents, use "clinical-note".

**Category Inference:**
All C-CDA clinical documents should be categorized as "clinical-note":

```json
{
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ]
}
```

### Patient/Subject

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/recordTarget/patientRole` | `DocumentReference.subject` | 1..1 | Reference to Patient resource |

**Mapping Process:**
1. Convert `recordTarget/patientRole` to Patient resource (see [01-patient.md](01-patient.md))
2. Create Patient resource or resolve existing patient
3. Reference from DocumentReference: `"reference": "Patient/{id}"`

**US Core Requirement:** SHALL reference a Patient resource.

**Example:**

C-CDA:
```xml
<recordTarget>
  <patientRole>
    <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
    <patient>
      <name>
        <given>Ellen</given>
        <family>Ross</family>
      </name>
      <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
      <birthTime value="19750501"/>
    </patient>
  </patientRole>
</recordTarget>
```

FHIR:
```json
{
  "subject": {
    "reference": "Patient/patient-998991",
    "display": "Ellen Ross"
  }
}
```

### Document Date/Time

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/effectiveTime/@value` | `DocumentReference.date` | 0..1 | Document creation time |

**Timestamp Conversion:**
- C-CDA format: `YYYYMMDDHHmmss±ZZZZ`
- FHIR format: `YYYY-MM-DDThh:mm:ss±hh:mm` (instant)
- Preserve precision from C-CDA
- Timezone required if time component present

**US Core:** Must Support element

**Example:**

C-CDA:
```xml
<effectiveTime value="20200301102000-0500"/>
```

FHIR:
```json
{
  "date": "2020-03-01T10:20:00-05:00"
}
```

### Authors

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/author/assignedAuthor` | `DocumentReference.author[]` | 0..* | Document authors |

**Mapping Process:**
1. Convert each `author/assignedAuthor` to Practitioner or PractitionerRole resource (see [09-participations.md](09-participations.md))
2. Create or resolve practitioner resources
3. Reference from DocumentReference: `"reference": "Practitioner/{id}"`

**US Core:** Must Support element

**Author Timestamp:**
- `author/time` is authorship time, not document creation time
- Use earliest `author/time` if different from `effectiveTime`

**Example:**

C-CDA:
```xml
<author>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
          displayName="Family Medicine"/>
    <assignedPerson>
      <name>
        <given>Adam</given>
        <family>Careful</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

FHIR:
```json
{
  "author": [
    {
      "reference": "Practitioner/practitioner-1234567890",
      "display": "Dr. Adam Careful"
    }
  ]
}
```

### Legal Authenticator

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/legalAuthenticator/assignedEntity` | `DocumentReference.authenticator` | 0..1 | Legal authenticator |

**Mapping Process:**
1. Convert `legalAuthenticator/assignedEntity` to Practitioner resource
2. Reference from DocumentReference: `"reference": "Practitioner/{id}"`

**Note:** FHIR DocumentReference has a single `authenticator`, while C-CDA allows multiple `authenticator` elements. Map the `legalAuthenticator` to DocumentReference.authenticator.

**Example:**

C-CDA:
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

FHIR:
```json
{
  "authenticator": {
    "reference": "Practitioner/practitioner-1234567890",
    "display": "Dr. Adam Careful"
  }
}
```

### Custodian

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/custodian/assignedCustodian/representedCustodianOrganization` | `DocumentReference.custodian` | 0..1 | Organization maintaining document |

**Mapping Process:**
1. Convert `representedCustodianOrganization` to Organization resource
2. Reference from DocumentReference: `"reference": "Organization/{id}"`

**Example:**

C-CDA:
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

FHIR:
```json
{
  "custodian": {
    "reference": "Organization/org-1393",
    "display": "Community Health and Hospitals"
  }
}
```

### Related Documents

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/relatedDocument` | `DocumentReference.relatesTo[]` | 0..* | Document relationships |

**Relationship Type Mapping:**

| C-CDA typeCode | FHIR code | Description |
|----------------|-----------|-------------|
| RPLC | replaces | This document replaces the target |
| APND | appends | This document appends to the target |
| XFRM | transforms | This document transforms the target |

**Target Mapping:**
- `relatedDocument/parentDocument/id` → `relatesTo.target`
- Use `target.identifier` for external documents (preferred)
- Use `target.reference` if target DocumentReference exists in system

**Example:**

C-CDA:
```xml
<relatedDocument typeCode="RPLC">
  <parentDocument>
    <id root="2.16.840.1.113883.19.5.99999.1" extension="TT987"/>
    <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>
    <versionNumber value="1"/>
  </parentDocument>
</relatedDocument>
```

FHIR:
```json
{
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "identifier": {
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "TT987"
        }
      }
    }
  ]
}
```

### Document Description

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/title` | `DocumentReference.description` | 0..1 | Human-readable description |

**Alternative:** Construct description from document type and patient name if title is not descriptive enough.

**Example:**

C-CDA:
```xml
<title>Continuity of Care Document</title>
```

FHIR:
```json
{
  "description": "Continuity of Care Document for Ellen Ross, created 2020-03-01"
}
```

### Confidentiality/Security Label

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/confidentialityCode/@code` | `DocumentReference.securityLabel[]` | 0..* | Document confidentiality |

**Confidentiality Code Mapping:**

| C-CDA Code | FHIR Code | Display |
|------------|-----------|---------|
| N | N | normal |
| R | R | restricted |
| V | V | very restricted |
| L | L | low |
| M | M | moderate |
| U | U | unrestricted |

**Code System:** `http://terminology.hl7.org/CodeSystem/v3-Confidentiality`

**Example:**

C-CDA:
```xml
<confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"
                     displayName="Normal"/>
```

FHIR:
```json
{
  "securityLabel": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
          "code": "N",
          "display": "normal"
        }
      ]
    }
  ]
}
```

### Document Content

#### content.attachment (The C-CDA Document)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (entire ClinicalDocument XML) | `DocumentReference.content[].attachment` | 1..1 | The actual C-CDA document |
| `ClinicalDocument/languageCode/@code` | `DocumentReference.content[].attachment.language` | 0..1 | Document language |
| `ClinicalDocument/title` | `DocumentReference.content[].attachment.title` | 0..1 | Document title |
| `ClinicalDocument/effectiveTime/@value` | `DocumentReference.content[].attachment.creation` | 0..1 | Creation timestamp |

**Required Elements:**
- `attachment.contentType` (1..1) - MIME type
- `attachment.url` OR `attachment.data` (1..1) - US Core requires at least one

**MIME Type for C-CDA:**
```json
{
  "contentType": "application/xml"
}
```

**Storage Options:**

**Option 1: URL Reference (Recommended)**
```json
{
  "attachment": {
    "contentType": "application/xml",
    "language": "en-US",
    "url": "Binary/ccda-ccd-tt988",
    "size": 125678,
    "hash": "ZGE5NWQwNzVmZGUyYjA3ZGYzYjA4YzU5ZjFkYmYxNmU=",
    "title": "Continuity of Care Document",
    "creation": "2020-03-01T10:20:00-05:00"
  }
}
```

**Option 2: Embedded Data**
```json
{
  "attachment": {
    "contentType": "application/xml",
    "language": "en-US",
    "data": "PENsaW5pY2FsRG9jdW1lbnQgeG1sbnM9InVybjpobDctb3JnOnYzIj4uLi48L0NsaW5pY2FsRG9jdW1lbnQ+",
    "size": 125678,
    "hash": "ZGE5NWQwNzVmZGUyYjA3ZGYzYjA4YzU5ZjFkYmYxNmU=",
    "title": "Continuity of Care Document",
    "creation": "2020-03-01T10:20:00-05:00"
  }
}
```

**Hash Calculation:**
The `attachment.hash` should be the SHA-1 hash of the C-CDA XML document (base64-encoded).

**Size:**
Document size in bytes (original XML, not base64-encoded size if using data).

#### content.format (Document Format Code)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (infer from templateId) | `DocumentReference.content[].format` | 0..1 | C-CDA format specification |

**US Core:** Must Support element

**C-CDA Format Codes:**

| Template Version | Format Code | Display |
|------------------|-------------|---------|
| C-CDA R1.1 | urn:hl7-org:sdwg:ccda-structuredBody:1.1 | C-CDA R1.1 Structured Body |
| C-CDA R2.1 | urn:hl7-org:sdwg:ccda-structuredBody:2.1 | C-CDA R2.1 Structured Body |
| C-CDA R3.0 | urn:hl7-org:sdwg:ccda-structuredBody:3.0 | C-CDA R3.0 Structured Body |
| C-CDA R4.0 | urn:hl7-org:sdwg:ccda-structuredBody:4.0 | C-CDA R4.0 Structured Body |
| C-CDA R1.1 (nonXMLBody) | urn:hl7-org:sdwg:ccda-nonXMLBody:1.1 | C-CDA R1.1 Non-XML Body |
| C-CDA R2.1 (nonXMLBody) | urn:hl7-org:sdwg:ccda-nonXMLBody:2.1 | C-CDA R2.1 Non-XML Body |
| C-CDA R3.0 (nonXMLBody) | urn:hl7-org:sdwg:ccda-nonXMLBody:3.0 | C-CDA R3.0 Non-XML Body |
| C-CDA R4.0 (nonXMLBody) | urn:hl7-org:sdwg:ccda-nonXMLBody:4.0 | C-CDA R4.0 Non-XML Body |

**System:** `http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes`

**Determining Format Code:**
Check `ClinicalDocument/templateId` for version:
- If templateId has extension="2015-08-01" or later → Use C-CDA R2.1
- If templateId has extension="2014-06-09" or earlier → Use C-CDA R1.1

**Example:**

C-CDA:
```xml
<ClinicalDocument>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>
  ...
</ClinicalDocument>
```

FHIR:
```json
{
  "format": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
    "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
    "display": "C-CDA R2.1 Structured Body"
  }
}
```

### Document Context

#### context.encounter

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/componentOf/encompassingEncounter` | `DocumentReference.context.encounter[]` | 0..* | Related encounter(s) |

**US Core:** Must Support element

**Mapping Process:**
1. Convert `encompassingEncounter` to Encounter resource (see [08-encounter.md](08-encounter.md))
2. Reference from DocumentReference: `"reference": "Encounter/{id}"`

**Note:** Not all C-CDA documents have an encounter context (e.g., longitudinal care summaries).

**Example:**

C-CDA:
```xml
<componentOf>
  <encompassingEncounter>
    <id root="2.16.840.1.113883.19.5" extension="9937012"/>
    <code code="99213" codeSystem="2.16.840.1.113883.6.12"
          displayName="Office Visit"/>
    <effectiveTime>
      <low value="20200301"/>
      <high value="20200301"/>
    </effectiveTime>
  </encompassingEncounter>
</componentOf>
```

FHIR:
```json
{
  "context": {
    "encounter": [
      {
        "reference": "Encounter/encounter-9937012"
      }
    ]
  }
}
```

#### context.event

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/documentationOf/serviceEvent/@classCode` | `DocumentReference.context.event[]` | 0..* | Event codes |

**Event Code Mapping:**

| C-CDA classCode | FHIR Code | Display |
|-----------------|-----------|---------|
| PCPR | PCPR | care provision |
| ENC | ENC | encounter |
| IMP | IMP | inpatient encounter |
| ACUTE | ACUTE | inpatient acute |

**Code System:** `http://terminology.hl7.org/CodeSystem/v3-ActClass`

**Example:**

C-CDA:
```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20200101"/>
      <high value="20200301"/>
    </effectiveTime>
  </serviceEvent>
</documentationOf>
```

FHIR:
```json
{
  "context": {
    "event": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
            "code": "PCPR",
            "display": "care provision"
          }
        ]
      }
    ]
  }
}
```

#### context.period

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/documentationOf/serviceEvent/effectiveTime` | `DocumentReference.context.period` | 0..1 | Service time period |

**US Core:** Must Support element

**Mapping:**
- `effectiveTime/low/@value` → `period.start`
- `effectiveTime/high/@value` → `period.end`

**Example:**

C-CDA:
```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20200101"/>
      <high value="20200301"/>
    </effectiveTime>
  </serviceEvent>
</documentationOf>
```

FHIR:
```json
{
  "context": {
    "period": {
      "start": "2020-01-01",
      "end": "2020-03-01"
    }
  }
}
```

#### context.facilityType and context.practiceSetting

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/componentOf/encompassingEncounter/location/healthCareFacility/code` | `DocumentReference.context.facilityType` | 0..1 | Facility type |
| `ClinicalDocument/author/assignedAuthor/code` | `DocumentReference.context.practiceSetting` | 0..1 | Practice specialty |

**Facility Type:**
May be inferred from encounter location if available.

**Practice Setting:**
Infer from author's specialty code.

**Example:**

C-CDA:
```xml
<author>
  <assignedAuthor>
    <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
          displayName="Family Medicine"/>
  </assignedAuthor>
</author>
```

FHIR:
```json
{
  "context": {
    "practiceSetting": {
      "coding": [
        {
          "system": "http://nucc.org/provider-taxonomy",
          "code": "207Q00000X",
          "display": "Family Medicine"
        }
      ]
    }
  }
}
```

## Complete Mapping Example

### C-CDA Input (Header Only)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>

  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Summarization of Episode Note"/>
  <title>Continuity of Care Document</title>
  <effectiveTime value="20200301102000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>
  <versionNumber value="1"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
      <patient>
        <name><given>Ellen</given><family>Ross</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750501"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
            displayName="Family Medicine"/>
      <assignedPerson>
        <name><given>Adam</given><family>Careful</family><suffix>MD</suffix></name>
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

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20200101"/>
        <high value="20200301"/>
      </effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <!-- Sections... -->
    </structuredBody>
  </component>
</ClinicalDocument>
```

### FHIR Output (DocumentReference)

```json
{
  "resourceType": "DocumentReference",
  "id": "ccda-ccd-tt988",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference"
    ]
  },
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
      "value": "TT988"
    }
  ],
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988"
  },
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "34133-9",
        "display": "Summarization of Episode Note"
      }
    ],
    "text": "Continuity of Care Document"
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/patient-998991",
    "display": "Ellen Ross"
  },
  "date": "2020-03-01T10:20:00-05:00",
  "author": [
    {
      "reference": "Practitioner/practitioner-1234567890",
      "display": "Dr. Adam Careful, MD"
    }
  ],
  "authenticator": {
    "reference": "Practitioner/practitioner-1234567890",
    "display": "Dr. Adam Careful"
  },
  "custodian": {
    "reference": "Organization/org-1393",
    "display": "Community Health and Hospitals"
  },
  "description": "Continuity of Care Document for Ellen Ross, created 2020-03-01",
  "securityLabel": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
          "code": "N",
          "display": "normal"
        }
      ]
    }
  ],
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "language": "en-US",
        "url": "Binary/ccda-ccd-tt988",
        "size": 125678,
        "hash": "ZGE5NWQwNzVmZGUyYjA3ZGYzYjA4YzU5ZjFkYmYxNmU=",
        "title": "Continuity of Care Document",
        "creation": "2020-03-01T10:20:00-05:00"
      },
      "format": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
        "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
        "display": "C-CDA R2.1 Structured Body"
      }
    }
  ],
  "context": {
    "event": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
            "code": "PCPR",
            "display": "care provision"
          }
        ]
      }
    ],
    "period": {
      "start": "2020-01-01",
      "end": "2020-03-01"
    },
    "practiceSetting": {
      "coding": [
        {
          "system": "http://nucc.org/provider-taxonomy",
          "code": "207Q00000X",
          "display": "Family Medicine"
        }
      ]
    }
  }
}
```

## Implementation Considerations

### Document Storage Strategy

**Option 1: Binary Resource**
Store the C-CDA XML in a FHIR Binary resource:

```json
{
  "resourceType": "Binary",
  "id": "ccda-ccd-tt988",
  "contentType": "application/xml",
  "data": "PENsaW5pY2FsRG9jdW1lbnQ+Li4uPC9DbGluaWNhbERvY3VtZW50Pg=="
}
```

Then reference from DocumentReference:
```json
{
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "url": "Binary/ccda-ccd-tt988"
      }
    }
  ]
}
```

**Option 2: External Storage**
Store C-CDA in external document repository and provide URL:

```json
{
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "url": "https://docs.example.org/ccda/TT988.xml"
      }
    }
  ]
}
```

**Option 3: Embedded Data**
Embed base64-encoded C-CDA directly in DocumentReference:

```json
{
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "data": "PENsaW5pY2FsRG9jdW1lbnQ+Li4uPC9DbGluaWNhbERvY3VtZW50Pg=="
      }
    }
  ]
}
```

**Recommendation:**
- Use Binary resources for FHIR-native storage
- Use external URLs for existing document management systems
- Avoid embedded data for large documents (size limits)

### Document Versioning

When a C-CDA document is revised:

1. **Create new DocumentReference:**
   - New `identifier` from new `ClinicalDocument/id`
   - Same `masterIdentifier` from `ClinicalDocument/setId`
   - `status` = "current"
   - `relatesTo.code` = "replaces" pointing to prior version

2. **Update old DocumentReference:**
   - Change `status` to "superseded"

**Example:**

New version:
```json
{
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
      "value": "TT989"
    }
  ],
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988"
  },
  "status": "current",
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "reference": "DocumentReference/ccda-ccd-tt988"
      }
    }
  ]
}
```

### Complementary Use with Composition

A system can create both:
- **DocumentReference** - For document discovery and access to original C-CDA
- **Bundle + Composition** - For structured FHIR resource access

**Example Workflow:**
1. Receive C-CDA document
2. Create DocumentReference pointing to C-CDA XML
3. Optionally, also convert to Composition + Bundle for structured access
4. Link both representations via identifiers

### Missing or Unmapped Elements

C-CDA elements not directly mapped to DocumentReference:

| C-CDA Element | Handling |
|---------------|----------|
| dataEnterer | No equivalent; omit or use Provenance resource |
| informant | No equivalent; omit or use Provenance resource |
| informationRecipient | No equivalent; not part of document metadata |
| participant (support contacts) | No equivalent; include in Patient.contact instead |
| authenticator (non-legal) | Only legalAuthenticator maps; others omitted |

### Validation Checklist

**Required Elements:**
- [ ] `status` present (current, superseded, or entered-in-error)
- [ ] `type` present with LOINC code
- [ ] `category` includes "clinical-note"
- [ ] `subject` references Patient resource
- [ ] `content[0].attachment.contentType` = "application/xml"
- [ ] `content[0].attachment.url` OR `content[0].attachment.data` present

**Must Support Elements (US Core):**
- [ ] `identifier` present
- [ ] `date` present
- [ ] `author` present (if available in C-CDA)
- [ ] `content.format` includes C-CDA format code
- [ ] `context.encounter` present (if applicable)
- [ ] `context.period` present (if serviceEvent has effectiveTime)

**US Core Profile Conformance:**
- [ ] Conforms to http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference

## Error Handling

| Error Condition | Handling Strategy |
|-----------------|-------------------|
| Missing required C-CDA element | Log warning; omit optional FHIR element |
| Invalid C-CDA date format | Attempt to parse; use reduced precision if needed |
| Unknown document type code | Use provided code; log warning if not LOINC |
| Missing patient identifier | Cannot create DocumentReference; fail conversion |
| C-CDA file not accessible | Cannot create content.attachment; fail conversion |
| Multiple legalAuthenticators | Use first one for authenticator; log others |

## Related Documentation

- **FHIR DocumentReference Resource**: [/docs/fhir/document-reference.md](/docs/fhir/document-reference.md)
- **C-CDA Clinical Document**: [/docs/ccda/clinical-document.md](/docs/ccda/clinical-document.md)
- **Composition Mapping**: [19-composition.md](19-composition.md)
- **Bundle Mapping**: [20-bundle.md](20-bundle.md)
- **Patient Mapping**: [01-patient.md](01-patient.md)
- **Participations Mapping**: [09-participations.md](09-participations.md)

## References

- FHIR R4 DocumentReference: https://hl7.org/fhir/R4/documentreference.html
- US Core DocumentReference Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- C-CDA R2.1 Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- HL7 Document Format Codes: http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes
- LOINC Document Codes: https://loinc.org/document-ontology/
