# Mapping: C-CDA ClinicalDocument to FHIR Composition

## Overview

This document specifies the mapping between C-CDA ClinicalDocument (the root element of all C-CDA documents) and the FHIR Composition resource. The Composition resource represents the structure and metadata of a clinical document and serves as the first entry in a FHIR document Bundle.

## Context and Relationships

### Composition vs DocumentReference

When converting C-CDA documents to FHIR, there are two complementary approaches:

| Approach | Resource | Use Case | Output |
|----------|----------|----------|--------|
| **Structured Document** | Composition | Full conversion to FHIR resources | Bundle of type "document" with Composition + resources |
| **Document Index** | DocumentReference | Index/reference to source document | DocumentReference pointing to original C-CDA |

**This mapping focuses on the Composition approach** (structured document conversion).

### Document Bundle Structure

The result of mapping a C-CDA document to FHIR Composition is a **FHIR document Bundle** with:

1. `Bundle.type` = "document"
2. `Composition` as the first entry (this mapping)
3. `Patient` resource (from recordTarget)
4. Section-specific resources (Condition, AllergyIntolerance, MedicationRequest, etc.)
5. Supporting resources (Practitioner, Organization, etc.)

## Standards References

| Standard | Reference |
|----------|-----------|
| **C-CDA R2.1** | US Realm Header Template (`2.16.840.1.113883.10.20.22.1.1`) |
| **FHIR R4** | Composition resource (https://hl7.org/fhir/R4/composition.html) |
| **C-CDA on FHIR IG** | http://hl7.org/fhir/us/ccda/ |
| **CDA R2** | HL7 Clinical Document Architecture Release 2.0 |

## Element-by-Element Mapping

### Document Identifier

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/id/@root` | `Composition.identifier.system` | 1..1 | Convert OID to URI (see below) |
| `ClinicalDocument/id/@extension` | `Composition.identifier.value` | 0..1 | If present |

**OID to URI Conversion:**
- If `@root` is a UUID (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`): use `urn:uuid:{root}`
- If `@root` is an OID: use `urn:oid:{root}`
- No `@extension`: use full UUID/OID as both system and value

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
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  }
}
```

### Document Status

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (implicit) | `Composition.status` | 1..1 | Default: "final" |

**Status Mapping Logic (FHIR R4):**

FHIR R4 defines only 4 status codes: preliminary, final, amended, entered-in-error

| C-CDA Context | FHIR status | Rationale |
|---------------|-------------|-----------|
| Normal document | `final` | Most C-CDA documents are completed |
| Document with `relatedDocument[@typeCode='RPLC']` | `amended` | Replaces prior version (use relatesTo for details) |
| Preliminary report indicator | `preliminary` | If document explicitly indicates draft/preliminary status |
| Error indicator | `entered-in-error` | If document explicitly marked as erroneous |

**Important Notes:**
- **Default:** Use `final` for most C-CDA documents, as they represent completed clinical documentation
- **Addendum Documents:** For C-CDA documents with `relatedDocument[@typeCode='APND']`, still use status='final' but include the relationship in `Composition.relatesTo` with code='appends'. FHIR R4 does not have an 'appended' status value.
- **Corrections:** FHIR R4 does not distinguish between amended and corrected. Use status='amended' and provide details in relatesTo or extension if needed.
- **FHIR R5 Note:** Later FHIR versions add more status codes (registered, partial, corrected, appended, cancelled, deprecated, unknown), but these are not available in R4.

### Document Type

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/code/@code` | `Composition.type.coding.code` | 1..1 | LOINC code |
| `ClinicalDocument/code/@codeSystem` | `Composition.type.coding.system` | 1..1 | Always `http://loinc.org` |
| `ClinicalDocument/code/@displayName` | `Composition.type.coding.display` | 0..1 | Human-readable display |
| `ClinicalDocument/code/translation` | `Composition.type.coding[]` | 0..* | Additional codings |
| `ClinicalDocument/code/originalText` | `Composition.type.text` | 0..1 | Original text |

**Document Type Mapping (LOINC):**

| C-CDA Template ID | LOINC Code | Display | FHIR Profile |
|-------------------|------------|---------|--------------|
| 2.16.840.1.113883.10.20.22.1.2 | 34133-9 | Summarization of Episode Note | CCDA-on-FHIR-Continuity-of-Care-Document |
| 2.16.840.1.113883.10.20.22.1.4 | 11488-4 | Consultation Note | CCDA-on-FHIR-Consultation-Note |
| 2.16.840.1.113883.10.20.22.1.8 | 18842-5 | Discharge Summary | CCDA-on-FHIR-Discharge-Summary |
| 2.16.840.1.113883.10.20.22.1.5 | 18748-4 | Diagnostic imaging study | Diagnostic-Imaging-Report |
| 2.16.840.1.113883.10.20.22.1.1 | 34117-2 | History and Physical Note | CCDA-on-FHIR-History-and-Physical |
| 2.16.840.1.113883.10.20.22.1.6 | 11504-8 | Surgical Operation Note | CCDA-on-FHIR-Operative-Note |
| 2.16.840.1.113883.10.20.22.1.9 | 11506-3 | Progress Note | CCDA-on-FHIR-Progress-Note |
| 2.16.840.1.113883.10.20.22.1.7 | 28570-0 | Procedure Note | CCDA-on-FHIR-Procedure-Note |
| 2.16.840.1.113883.10.20.22.1.14 | 57133-1 | Referral Note | CCDA-on-FHIR-Referral-Note |
| 2.16.840.1.113883.10.20.22.1.13 | 18761-7 | Transfer Summary | CCDA-on-FHIR-Transfer-Summary |
| 2.16.840.1.113883.10.20.22.1.15 | 52521-2 | Overall plan of care/advance care directives | Care-Plan-Document |
| 2.16.840.1.113883.10.20.22.1.10 | 34111-5 | Emergency Department Note | (not profiled) |

**Example:**

C-CDA:
```xml
<code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
      displayName="Summarization of Episode Note">
  <originalText>Continuity of Care Document</originalText>
  <translation code="CCD" codeSystem="2.16.840.1.113883.6.1"
               displayName="Continuity of Care Document"/>
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
      },
      {
        "system": "http://loinc.org",
        "code": "CCD",
        "display": "Continuity of Care Document"
      }
    ],
    "text": "Continuity of Care Document"
  }
}
```

### Document Category

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (infer from type) | `Composition.category` | 0..* | Infer from document type |

**Category Inference:**

| Document Type | Category Code | System |
|---------------|---------------|--------|
| Clinical notes | LP173421-1 "Report" | http://loinc.org |
| Discharge summaries | LP173421-1 "Report" | http://loinc.org |
| History and Physical | LP173421-1 "Report" | http://loinc.org |

**Note:** Category is not explicitly present in C-CDA; infer from document type code.

### Patient/Subject

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/recordTarget/patientRole` | `Composition.subject` | 1..1 | Reference to Patient resource |

**Mapping Process:**
1. Convert `recordTarget/patientRole` to Patient resource (see [01-patient.md](01-patient.md))
2. Include Patient resource in document Bundle
3. Reference from Composition: `"reference": "Patient/{id}"`

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

### Encounter Context

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/componentOf/encompassingEncounter` | `Composition.encounter` | 0..1 | Reference to Encounter resource |

**Mapping Process:**
1. Convert `encompassingEncounter` to Encounter resource (see [08-encounter.md](08-encounter.md))
2. Include Encounter resource in document Bundle
3. Reference from Composition: `"reference": "Encounter/{id}"`

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
  "encounter": {
    "reference": "Encounter/encounter-9937012",
    "display": "Office Visit"
  }
}
```

### Document Date/Time

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/effectiveTime/@value` | `Composition.date` | 1..1 | Document creation time |

**Timestamp Conversion:**
- C-CDA format: `YYYYMMDDHHmmss±ZZZZ`
- FHIR format: `YYYY-MM-DDThh:mm:ss±hh:mm`
- Preserve precision from C-CDA
- **Timezone required** by C-CDA on FHIR if time component present

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
| `ClinicalDocument/author/assignedAuthor` | `Composition.author[]` | 1..* | Reference to Practitioner/PractitionerRole/Organization |

**Mapping Process:**
1. Convert each `author/assignedAuthor` to Practitioner/PractitionerRole resource (see [09-participations.md](09-participations.md))
2. Include all author resources in document Bundle
3. Reference from Composition: `"reference": "Practitioner/{id}"`

**Author Timestamp:**
- `author/time` is authorship time, not document date
- Use earliest `author/time` for provenance tracking
- Consider creating Provenance resource for complete author audit trail

**Multiple Authors:**
- C-CDA allows multiple authors
- Map all to `Composition.author[]` array
- Order should be preserved from C-CDA

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
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

FHIR:
```json
{
  "author": [
    {
      "reference": "Practitioner/practitioner-1234567890",
      "display": "Adam Careful, MD"
    }
  ]
}
```

### Document Title

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/title` | `Composition.title` | 1..1 | Human-readable document title |

**Example:**

C-CDA:
```xml
<title>Continuity of Care Document</title>
```

FHIR:
```json
{
  "title": "Continuity of Care Document"
}
```

### Confidentiality

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/confidentialityCode/@code` | `Composition.confidentiality` | 0..1 | Confidentiality level |

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
  "confidentiality": "N"
}
```

### Language

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/languageCode/@code` | `Composition.language` | 0..1 | Document language |

**Language Code Format:**
- C-CDA: RFC 5646 (e.g., "en-US")
- FHIR: RFC 5646 (same format)
- Direct mapping

**Example:**

C-CDA:
```xml
<languageCode code="en-US"/>
```

FHIR:
```json
{
  "language": "en-US"
}
```

**Note:** FHIR also supports `Composition.language` at the resource level (different from individual section languages).

### Legal Authenticator

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/legalAuthenticator` | `Composition.attester[]` | 0..* | Attestation with mode="legal" |

**Mapping Process:**
1. Create attester entry with `mode` = "legal"
2. Map `legalAuthenticator/time` → `attester.time`
3. Convert `legalAuthenticator/assignedEntity` to Practitioner resource
4. Reference from `attester.party`

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
  "attester": [
    {
      "mode": "legal",
      "time": "2020-03-01",
      "party": {
        "reference": "Practitioner/practitioner-1234567890",
        "display": "Adam Careful"
      }
    }
  ]
}
```

### Authenticators

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/authenticator` | `Composition.attester[]` | 0..* | Attestation with mode="professional" |

**Mapping Process:**
1. Create attester entry with `mode` = "professional" or "personal"
2. Map `authenticator/time` → `attester.time`
3. Convert `authenticator/assignedEntity` to Practitioner resource
4. Reference from `attester.party`

**Mode Selection:**
- Use "professional" for organizational/professional authentication
- Use "personal" for individual capacity authentication

**Example:**

C-CDA:
```xml
<authenticator>
  <time value="20200301"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <assignedPerson>
      <name>
        <given>Jane</given>
        <family>Authenticator</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</authenticator>
```

FHIR:
```json
{
  "attester": [
    {
      "mode": "professional",
      "time": "2020-03-01",
      "party": {
        "reference": "Practitioner/practitioner-9876543210",
        "display": "Jane Authenticator"
      }
    }
  ]
}
```

### Custodian

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/custodian/assignedCustodian/representedCustodianOrganization` | `Composition.custodian` | 0..1 | Organization maintaining document |

**Mapping Process:**
1. Convert `representedCustodianOrganization` to Organization resource
2. Include Organization resource in document Bundle
3. Reference from Composition: `"reference": "Organization/{id}"`

**C-CDA on FHIR Requirement:**
- Required (1..1) for C-CDA on FHIR profiles
- Optional (0..1) in base FHIR Composition

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
| `ClinicalDocument/relatedDocument` | `Composition.relatesTo[]` | 0..* | Document relationships |

**Relationship Type Mapping:**

| C-CDA typeCode | FHIR code | Description |
|----------------|-----------|-------------|
| RPLC | replaces | This document replaces the target |
| APND | appends | This document appends to the target |
| XFRM | transforms | This document transforms the target |

**Target Mapping:**
- `relatedDocument/parentDocument/id` → `relatesTo.targetIdentifier`
- Use `targetIdentifier` (not `targetReference`) for external documents
- Convert OID to URI format

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
      "targetIdentifier": {
        "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
        "value": "TT987"
      }
    }
  ]
}
```

### Service Event (documentationOf)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/documentationOf/serviceEvent` | `Composition.event[]` | 0..* | Clinical service documented |

**Event Elements:**

| C-CDA Element | FHIR Element | Notes |
|---------------|--------------|-------|
| `serviceEvent/@classCode` | `event.code` | Event type (v3-ActClass) |
| `serviceEvent/effectiveTime` | `event.period` | Time period of service |
| `serviceEvent/performer` | `event.detail[]` | Performers/participants |

**Class Code Mapping:**

| C-CDA classCode | FHIR Code | Display |
|-----------------|-----------|---------|
| PCPR | PCPR | care provision |
| ENC | ENC | encounter |
| IMP | IMP | inpatient encounter |
| ACUTE | ACUTE | inpatient acute |

**Example:**

C-CDA:
```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20200101"/>
      <high value="20200301"/>
    </effectiveTime>
    <performer typeCode="PRF">
      <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                    displayName="Primary Care Provider"/>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <assignedPerson>
          <name>
            <given>Adam</given>
            <family>Careful</family>
          </name>
        </assignedPerson>
      </assignedEntity>
    </performer>
  </serviceEvent>
</documentationOf>
```

FHIR:
```json
{
  "event": [
    {
      "code": [
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
      "detail": [
        {
          "reference": "Practitioner/practitioner-1234567890",
          "display": "Adam Careful (Primary Care Provider)"
        }
      ]
    }
  ]
}
```

### Document Sections

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/component/structuredBody/component/section` | `Composition.section[]` | 0..* | Document sections |

**Section Mapping (Detailed):**

#### Section Title

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/title` | `section.title` | 0..1 (C-CDA: 1..1) | Section title |

**C-CDA on FHIR:** Required (1..1) by all C-CDA on FHIR profiles.

#### Section Code

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/code/@code` | `section.code.coding.code` | 0..1 (C-CDA: 1..1) | LOINC section code |
| `section/code/@codeSystem` | `section.code.coding.system` | 0..1 | Always `http://loinc.org` |
| `section/code/@displayName` | `section.code.coding.display` | 0..1 | Display text |
| `section/code/translation` | `section.code.coding[]` | 0..* | Additional codings |

**C-CDA on FHIR:** Required (1..1) by all C-CDA on FHIR profiles.

**Common Section Codes:**

| C-CDA Template | LOINC Code | Display | Entry Resource Types |
|----------------|------------|---------|----------------------|
| 2.16.840.1.113883.10.20.22.2.6.1 | 48765-2 | Allergies and adverse reactions Document | AllergyIntolerance |
| 2.16.840.1.113883.10.20.22.2.1.1 | 10160-0 | History of Medication use Narrative | MedicationRequest, MedicationStatement |
| 2.16.840.1.113883.10.20.22.2.5.1 | 11450-4 | Problem list - Reported | Condition |
| 2.16.840.1.113883.10.20.22.2.7.1 | 47519-4 | History of Procedures Document | Procedure |
| 2.16.840.1.113883.10.20.22.2.2.1 | 11369-6 | History of Immunization Narrative | Immunization |
| 2.16.840.1.113883.10.20.22.2.3.1 | 30954-2 | Relevant diagnostic tests/laboratory data Narrative | Observation, DiagnosticReport |
| 2.16.840.1.113883.10.20.22.2.4.1 | 8716-3 | Vital signs | Observation (vital-signs) |
| 2.16.840.1.113883.10.20.22.2.22.1 | 46240-8 | Encounter list | Encounter |
| 2.16.840.1.113883.10.20.22.2.17 | 29762-2 | Social history Narrative | Observation (social-history) |
| 2.16.840.1.113883.10.20.22.2.15 | 10157-6 | History of family member diseases Narrative | FamilyMemberHistory |
| 2.16.840.1.113883.10.20.22.2.10 | 18776-5 | Plan of care note | CarePlan, Goal, ServiceRequest |
| 2.16.840.1.113883.10.20.22.2.60 | 61146-7 | Goals | Goal |
| 2.16.840.1.113883.10.20.22.2.58 | 75310-3 | Health concerns Document | Condition |
| 2.16.840.1.113883.10.20.22.2.500 | 85847-2 | Patient Care team information | CareTeam |

#### Section Author

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/author/assignedAuthor` | `section.author[]` | 0..* | Section-specific authors |

**Note:** Section authors override document-level authors for that section.

#### Section Text/Narrative

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/text` | `section.text` | 0..1 | Human-readable narrative |

**Narrative Conversion:**

C-CDA uses HL7 narrative block format; FHIR uses XHTML. Conversion required:

| C-CDA Element | XHTML Element |
|---------------|---------------|
| `<content>` | `<span>` |
| `<paragraph>` | `<p>` |
| `<list listType="ordered">` | `<ol>` |
| `<list listType="unordered">` | `<ul>` |
| `<item>` | `<li>` |
| `<table>` | `<table>` |
| `<thead>` | `<thead>` |
| `<tbody>` | `<tbody>` |
| `<tr>` | `<tr>` |
| `<th>` | `<th>` |
| `<td>` | `<td>` |
| `<linkHtml>` | `<a>` |
| `<renderMultiMedia>` | `<img>` |
| `@ID` | `@id` |
| `@styleCode` | `@class` or `@style` |

**text.status:**
- Use "generated" if narrative generated from structured data
- Use "additional" if preserving C-CDA hand-authored text

**Example:**

C-CDA:
```xml
<text>
  <table border="1" width="100%">
    <thead>
      <tr>
        <th>Medication</th>
        <th>Directions</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      <tr ID="med1">
        <td>Lisinopril 10mg</td>
        <td>Take 1 tablet by mouth daily</td>
        <td>Active</td>
      </tr>
    </tbody>
  </table>
</text>
```

FHIR:
```json
{
  "text": {
    "status": "generated",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table border=\"1\" width=\"100%\"><thead><tr><th>Medication</th><th>Directions</th><th>Status</th></tr></thead><tbody><tr id=\"med1\"><td>Lisinopril 10mg</td><td>Take 1 tablet by mouth daily</td><td>Active</td></tr></tbody></table></div>"
  }
}
```

#### Section Mode

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (implicit) | `section.mode` | 0..1 | Default: "snapshot" |

**Mode Selection:**
- `snapshot`: Most C-CDA sections (point-in-time view)
- `changes`: For addendum documents
- `working`: For draft/working documents

#### Section Entries

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/entry` | `section.entry[]` | 0..* | References to resources |

**Entry Mapping Process:**
1. Convert each C-CDA entry to appropriate FHIR resource (see section-specific mappings)
2. Include resource in document Bundle
3. Add reference to `section.entry[]`: `"reference": "ResourceType/id"`

**Entry Ordering:**
- Preserve C-CDA entry order if meaningful
- Use `section.orderedBy` to specify ordering

**Example:**

C-CDA:
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.6.1" extension="2015-08-01"/>
  <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Allergies and adverse reactions Document"/>
  <title>Allergies and Intolerances</title>
  <text>...</text>
  <entry typeCode="DRIV">
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
      <!-- Allergy Concern Act -->
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
          <!-- Allergy Observation -->
          ...
        </observation>
      </entryRelationship>
    </act>
  </entry>
</section>
```

FHIR:
```json
{
  "section": [
    {
      "title": "Allergies and Intolerances",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "48765-2",
            "display": "Allergies and adverse reactions Document"
          }
        ]
      },
      "text": {...},
      "mode": "snapshot",
      "entry": [
        {
          "reference": "AllergyIntolerance/allergy-1"
        }
      ]
    }
  ]
}
```

#### Empty Sections

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/text` with "No known..." | `section.emptyReason` | 0..1 | Why section is empty |

**Empty Reason Mapping:**

| C-CDA Text Pattern | FHIR emptyReason | Code |
|--------------------|------------------|------|
| "No known allergies" | Nil Known | nilknown |
| "No known problems" | Nil Known | nilknown |
| "No current medications" | Nil Known | nilknown |
| "Information not available" | Unavailable | unavailable |
| "Patient declined to provide" | Information Withheld | withheld |
| (nullFlavor="NA") | Not Applicable | notapplicable |
| (nullFlavor="UNK") | Unknown | unknown |

**Example:**

C-CDA:
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.6.1" extension="2015-08-01"/>
  <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Allergies and Intolerances</title>
  <text>No known allergies</text>
</section>
```

FHIR:
```json
{
  "section": [
    {
      "title": "Allergies and Intolerances",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "48765-2",
            "display": "Allergies and adverse reactions Document"
          }
        ]
      },
      "text": {
        "status": "generated",
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">No known allergies</div>"
      },
      "emptyReason": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
            "code": "nilknown",
            "display": "Nil Known"
          }
        ]
      }
    }
  ]
}
```

#### Nested Sections

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `section/component/section` | `section.section[]` | 0..* | Nested sub-sections |

**Note:** Preserve nesting structure from C-CDA.

**Example:**

C-CDA:
```xml
<section>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Results</title>
  <component>
    <section>
      <code code="26436-6" codeSystem="2.16.840.1.113883.6.1"/>
      <title>Laboratory Results</title>
      ...
    </section>
  </component>
</section>
```

FHIR:
```json
{
  "section": [
    {
      "title": "Results",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "30954-2"
          }
        ]
      },
      "section": [
        {
          "title": "Laboratory Results",
          "code": {
            "coding": [
              {
                "system": "http://loinc.org",
                "code": "26436-6"
              }
            ]
          }
        }
      ]
    }
  ]
}
```

## Document Bundle Assembly

### Bundle Creation Process

1. **Create Bundle** with `type` = "document"
2. **Set Bundle.identifier** from `ClinicalDocument/id`
3. **Set Bundle.timestamp** from `ClinicalDocument/effectiveTime`
4. **Create Composition** as first entry
5. **Convert Patient** from `recordTarget` and add to Bundle
6. **Convert all sections** and their entries:
   - For each section, convert C-CDA entries to FHIR resources
   - Add resources to Bundle
   - Reference from Composition section entries
7. **Convert document participants**:
   - Authors → Practitioner/PractitionerRole
   - Custodian → Organization
   - Authenticators → Practitioner
8. **Assign fullUrl** to each Bundle entry (use UUIDs or stable IDs)
9. **Validate references** - ensure all references resolve within Bundle

### Bundle Entry fullUrl Assignment

**UUID-based (recommended for documents without stable IDs):**
```json
{
  "fullUrl": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f",
  "resource": {...}
}
```

**Identifier-based (when resource has stable identifier):**
```json
{
  "fullUrl": "urn:oid:2.16.840.1.113883.19.5.99999.1",
  "resource": {...}
}
```

**URL-based (if resources have canonical URLs):**
```json
{
  "fullUrl": "https://hospital.example.org/fhir/Patient/patient-123",
  "resource": {...}
}
```

### Complete Bundle Example

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  },
  "timestamp": "2020-03-01T10:20:00-05:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:doc-composition-1",
      "resource": {
        "resourceType": "Composition",
        "id": "doc-composition-1",
        "identifier": {
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "TT988"
        },
        "status": "final",
        "type": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "34133-9",
              "display": "Summarization of Episode Note"
            }
          ]
        },
        "subject": {
          "reference": "Patient/patient-998991"
        },
        "date": "2020-03-01T10:20:00-05:00",
        "author": [
          {
            "reference": "Practitioner/practitioner-1234567890"
          }
        ],
        "title": "Continuity of Care Document",
        "custodian": {
          "reference": "Organization/org-1393"
        },
        "section": [
          {
            "title": "Allergies and Intolerances",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "48765-2"
                }
              ]
            },
            "entry": [
              {
                "reference": "AllergyIntolerance/allergy-1"
              }
            ]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:patient-998991",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-998991",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-1234567890",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-1234567890",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:org-1393",
      "resource": {
        "resourceType": "Organization",
        "id": "org-1393",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:allergy-1",
      "resource": {
        "resourceType": "AllergyIntolerance",
        "id": "allergy-1",
        ...
      }
    }
  ]
}
```

## C-CDA on FHIR Profile Selection

Based on the C-CDA document template ID, select the appropriate FHIR profile for `Composition.meta.profile`:

| C-CDA Template ID | C-CDA Document Type | FHIR Profile |
|-------------------|---------------------|--------------|
| 2.16.840.1.113883.10.20.22.1.2 | Continuity of Care Document (CCD) | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document |
| 2.16.840.1.113883.10.20.22.1.4 | Consultation Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Consultation-Note |
| 2.16.840.1.113883.10.20.22.1.8 | Discharge Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Discharge-Summary |
| 2.16.840.1.113883.10.20.22.1.5 | Diagnostic Imaging Report | http://hl7.org/fhir/us/ccda/StructureDefinition/Diagnostic-Imaging-Report |
| 2.16.840.1.113883.10.20.22.1.1 | History and Physical | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-History-and-Physical |
| 2.16.840.1.113883.10.20.22.1.6 | Operative Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Operative-Note |
| 2.16.840.1.113883.10.20.22.1.9 | Progress Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Progress-Note |
| 2.16.840.1.113883.10.20.22.1.7 | Procedure Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Procedure-Note |
| 2.16.840.1.113883.10.20.22.1.14 | Referral Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Referral-Note |
| 2.16.840.1.113883.10.20.22.1.13 | Transfer Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Transfer-Summary |
| 2.16.840.1.113883.10.20.22.1.15 | Care Plan | http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document |

## Implementation Considerations

### Document Versioning

C-CDA supports explicit versioning through `setId` and `versionNumber`:

| C-CDA Element | FHIR Element | Notes |
|---------------|--------------|-------|
| `setId` | (part of identifier) | Document set identifier |
| `versionNumber` | (part of identifier or extension) | Version within set |

**Approach 1: Include in identifier**
```json
{
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988-v2"
  }
}
```

**Approach 2: Use extension**
```json
{
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  },
  "extension": [
    {
      "url": "http://hl7.org/fhir/StructureDefinition/composition-clinicaldocument-versionNumber",
      "valueString": "2"
    }
  ]
}
```

### Data Enterer, Informant, Information Recipient

C-CDA includes additional participants not directly mapped to Composition:

| C-CDA Element | FHIR Approach |
|---------------|---------------|
| `dataEnterer` | Create Provenance resource with `agent.type` = "enterer" |
| `informant` | Create Provenance resource with `agent.type` = "informant" |
| `informationRecipient` | Not mapped (document routing, not content) |
| `participant` (emergency contact, next of kin) | Convert to RelatedPerson, reference from Patient |

### Participant Type Codes

| C-CDA participant typeCode | Mapping |
|----------------------------|---------|
| IND (indirect target) | RelatedPerson (family, caregiver) |
| DEV (device) | Device resource |
| SBJ (subject) | Usually maps to subject (unusual) |

### Missing or Unknown Data

When C-CDA elements have `nullFlavor`:

| C-CDA nullFlavor | FHIR Approach |
|------------------|---------------|
| UNK, ASKU, NAV | Omit element or use data-absent-reason extension |
| NI (no information) | Omit element |
| NA (not applicable) | Use emptyReason for sections |
| OTH (other) | Map as text if originalText present |

### Narrative-Only Sections

Some C-CDA sections may have narrative but no structured entries:
- Include `section.text` in FHIR
- Omit `section.entry`
- Do not use `emptyReason` (section has content, just not structured)

### Multi-Part Names and Addresses

C-CDA allows multiple instances; FHIR uses arrays:
- Multiple `<given>` → `name.given[]` array
- Multiple `<streetAddressLine>` → `address.line[]` array
- Multiple `<telecom>` → `telecom[]` array

## Validation Checklist

### Required Elements

- [ ] `Composition.identifier` present (from `ClinicalDocument/id`)
- [ ] `Composition.status` = "final" (or appropriate status)
- [ ] `Composition.type` present (from `ClinicalDocument/code`)
- [ ] `Composition.subject` references Patient resource
- [ ] `Composition.date` present (from `ClinicalDocument/effectiveTime`)
- [ ] `Composition.author[]` has at least one author
- [ ] `Composition.title` present (from `ClinicalDocument/title`)
- [ ] `Composition.custodian` present (C-CDA on FHIR requirement)

### Bundle Validation

- [ ] `Bundle.type` = "document"
- [ ] First entry is Composition
- [ ] All resources referenced by Composition are in Bundle
- [ ] All Bundle entries have `fullUrl`
- [ ] No broken references (all resolve within Bundle)
- [ ] Patient resource exists and is referenced by Composition

### Section Validation

For each section:
- [ ] `section.title` present (C-CDA on FHIR requirement)
- [ ] `section.code` present (C-CDA on FHIR requirement)
- [ ] `section.text` present if section has content
- [ ] `section.entry[]` references exist in Bundle
- [ ] `section.emptyReason` only if `section.entry` is empty

### Profile Conformance

- [ ] Correct C-CDA on FHIR profile in `Composition.meta.profile`
- [ ] Required sections present per document type
- [ ] Section codes match expected LOINC codes
- [ ] Narrative format is valid XHTML

## Error Handling

| Error Condition | Handling Strategy |
|-----------------|-------------------|
| Missing required C-CDA element | Omit FHIR element and log warning |
| Invalid C-CDA date format | Attempt to parse; use reduced precision if needed |
| Unknown section template | Include section but mark as general section |
| Broken internal reference | Log error; omit reference or use stub resource |
| Invalid code system OID | Use `urn:oid:` format as fallback |
| Missing section text | Generate from structured entries if possible |
| No entries in required section | Use `emptyReason` if appropriate |

## Examples from Standards

### Example 1: Minimal CCD (from C-CDA on FHIR IG)

See complete example in `/docs/fhir/composition.md` "Example 2: CCD Composition with Sections".

### Example 2: Discharge Summary with Multiple Sections

C-CDA:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.8" extension="2015-08-01"/>
  <id root="1.2.840.114350.1.13.12345.1.7.2.123456" extension="DOC001"/>
  <code code="18842-5" codeSystem="2.16.840.1.113883.6.1"
        displayName="Discharge Summary"/>
  <title>Discharge Summary</title>
  <effectiveTime value="20200315143000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <!-- recordTarget, author, custodian, etc. -->
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"
                displayName="Encounter list"/>
          <title>Encounters</title>
          <text>...</text>
          <entry>...</entry>
        </section>
      </component>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Allergies and Intolerances</title>
          <text>...</text>
          <entry>...</entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

FHIR:
```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:oid:1.2.840.114350.1.13.12345.1.7.2.123456",
    "value": "DOC001"
  },
  "timestamp": "2020-03-15T14:30:00-05:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-1",
      "resource": {
        "resourceType": "Composition",
        "id": "composition-1",
        "meta": {
          "profile": [
            "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Discharge-Summary"
          ]
        },
        "identifier": {
          "system": "urn:oid:1.2.840.114350.1.13.12345.1.7.2.123456",
          "value": "DOC001"
        },
        "status": "final",
        "type": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "18842-5",
              "display": "Discharge Summary"
            }
          ]
        },
        "subject": {
          "reference": "Patient/patient-123"
        },
        "date": "2020-03-15T14:30:00-05:00",
        "author": [
          {
            "reference": "Practitioner/practitioner-1"
          }
        ],
        "title": "Discharge Summary",
        "confidentiality": "N",
        "custodian": {
          "reference": "Organization/org-1"
        },
        "section": [
          {
            "title": "Encounters",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "46240-8",
                  "display": "Encounter list"
                }
              ]
            },
            "text": {...},
            "entry": [
              {
                "reference": "Encounter/encounter-1"
              }
            ]
          },
          {
            "title": "Allergies and Intolerances",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "48765-2"
                }
              ]
            },
            "text": {...},
            "entry": [
              {
                "reference": "AllergyIntolerance/allergy-1"
              }
            ]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:patient-123",
      "resource": {
        "resourceType": "Patient",
        ...
      }
    }
  ]
}
```

## Related Documentation

- **FHIR Composition Resource**: [/docs/fhir/composition.md](/docs/fhir/composition.md)
- **C-CDA Clinical Document**: [/docs/ccda/clinical-document.md](/docs/ccda/clinical-document.md)
- **Patient Mapping**: [01-patient.md](01-patient.md)
- **Encounter Mapping**: [08-encounter.md](08-encounter.md)
- **Participations Mapping**: [09-participations.md](09-participations.md)
- **Section-Specific Mappings**: [02-condition.md](02-condition.md), [03-allergy-intolerance.md](03-allergy-intolerance.md), etc.

## References

- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- FHIR R4 Composition: https://hl7.org/fhir/R4/composition.html
- FHIR R4 Bundle: https://hl7.org/fhir/R4/bundle.html
- FHIR Documents: https://hl7.org/fhir/R4/documents.html
- C-CDA R2.1: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- HL7 CDA R2: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=7
- LOINC Document Ontology: https://loinc.org/document-ontology/
