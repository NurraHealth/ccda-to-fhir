# C-CDA to FHIR Mapping: ServiceRequest

## Overview

This document specifies how to map C-CDA planned procedures and planned acts to FHIR **ServiceRequest** resources.

## Scope

**C-CDA Source Templates**:
1. **Planned Procedure (V2)** - `2.16.840.1.113883.10.20.22.4.41`
2. **Planned Act (V2)** - `2.16.840.1.113883.10.20.22.4.39`

**FHIR Target Profile**: [US Core ServiceRequest Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest)

**Source Section**: Plan of Treatment Section (`2.16.840.1.113883.10.20.22.2.10`)

## Standards References

- **US Core**: ServiceRequest Profile v8.0.1
- **C-CDA**: Consolidated CDA R2.1 / R3 (Planned Procedure, Planned Act templates)
- **C-CDA on FHIR IG**: ❌ **NOT COVERED** - ServiceRequest mapping not included in v2.0.0

**Note**: This mapping specification fills the gap left by the C-CDA on FHIR Implementation Guide, which does not include ServiceRequest mappings.

## Critical Distinction: moodCode Validation

**CRITICAL**: C-CDA uses `moodCode` to distinguish planned vs completed activities:

| C-CDA moodCode | FHIR Resource | Conversion Action |
|----------------|---------------|-------------------|
| **INT** (Intent) | ServiceRequest | Convert to ServiceRequest |
| **RQO** (Request) | ServiceRequest | Convert to ServiceRequest |
| **PRP** (Proposal) | ServiceRequest | Convert to ServiceRequest |
| **ARQ** (Appointment Request) | ServiceRequest | Convert to ServiceRequest |
| **PRMS** (Promise) | ServiceRequest | Convert to ServiceRequest |
| **EVN** (Event) | **Procedure** | DO NOT convert to ServiceRequest; use Procedure converter |
| **GOL** (Goal) | **Goal** | DO NOT convert to ServiceRequest; use Goal converter |

**Validation Rule**: ONLY convert procedures/acts with moodCode ∈ {INT, RQO, PRP, ARQ, PRMS} to ServiceRequest.

## Element Mapping Table

### Required Elements

| FHIR ServiceRequest | Cardinality | C-CDA Source | XPath | Notes |
|---------------------|-------------|--------------|-------|-------|
| **meta.profile** | 0..* | Fixed | N/A | Set to `["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]` |
| **status** | 1..1 | statusCode/@code | `procedure/statusCode/@code` or `act/statusCode/@code` | Map per ConceptMap below |
| **intent** | 1..1 | moodCode | `procedure/@moodCode` or `act/@moodCode` | Map per ConceptMap below |
| **code** | 1..1 | code | `procedure/code` or `act/code` | CodeableConcept with coding array |
| **subject** | 1..1 | Document recordTarget | `/ClinicalDocument/recordTarget/patientRole` | Reference to Patient resource |

### Must Support Elements

| FHIR ServiceRequest | Cardinality | C-CDA Source | XPath | Notes |
|---------------------|-------------|--------------|-------|-------|
| **category** | 0..* | Inferred from code | `procedure/code/@codeSystem` | Infer category from procedure code system |
| **code.text** | 0..1 | code/originalText | `procedure/code/originalText` or `procedure/text` | Plain-language description |
| **encounter** | 0..1 | Document encompassingEncounter | `/ClinicalDocument/componentOf/encompassingEncounter` | Reference to Encounter resource |
| **occurrence[x]** | 0..1 | effectiveTime | `procedure/effectiveTime` | Map to occurrenceDateTime, occurrencePeriod, or occurrenceTiming |
| **authoredOn** | 0..1 | author/time | `procedure/author/time` | DateTime when request was created |
| **requester** | 0..1 | author/assignedAuthor | `procedure/author/assignedAuthor` | Reference to Practitioner/PractitionerRole |
| **reasonCode** | 0..* | entryRelationship[typeCode='RSON']/observation | `procedure/entryRelationship[@typeCode='RSON']/observation[templateId/@root='2.16.840.1.113883.10.20.22.4.19']` | Indication observation |
| **reasonReference** | 0..* | entryRelationship[typeCode='RSON'] | `procedure/entryRelationship[@typeCode='RSON']` | Reference to Condition or Observation |

### Optional Elements

| FHIR ServiceRequest | Cardinality | C-CDA Source | XPath | Notes |
|---------------------|-------------|--------------|-------|-------|
| **identifier** | 0..* | id | `procedure/id` | OID to Identifier conversion |
| **bodySite** | 0..* | targetSiteCode | `procedure/targetSiteCode` | Anatomical location |
| **performer** | 0..* | performer/assignedEntity | `procedure/performer/assignedEntity` | Expected performer |
| **performerType** | 0..1 | performer/functionCode | `procedure/performer/functionCode` | Performer role |
| **priority** | 0..1 | priorityCode or entryRelationship[Priority Preference] | `procedure/priorityCode` | Urgency indicator |
| **note** | 0..* | text or entryRelationship[Instruction] | `procedure/text` or entryRelationship with Instruction template | Comments |
| **patientInstruction** | 0..1 | entryRelationship[typeCode='SUBJ'][Instruction] | `procedure/entryRelationship[@typeCode='SUBJ'][@inversionInd='true']/act[templateId/@root='2.16.840.1.113883.10.20.22.4.20']` | Patient instructions |
| **supportingInfo** | 0..* | entryRelationship[typeCode='RSON'] | `procedure/entryRelationship[@typeCode='RSON']` | Supporting clinical information |
| **insurance** | 0..* | entryRelationship[typeCode='COMP'][Planned Coverage] | `procedure/entryRelationship[@typeCode='COMP']/act[templateId/@root='2.16.840.1.113883.10.20.22.4.129']` | Coverage information |

## Detailed Element Mappings

### 1. meta.profile

**FHIR**: `ServiceRequest.meta.profile`

**Cardinality**: 0..*

**Mapping**: Fixed value

**Value**:
```json
{
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  }
}
```

**Implementation**: Always set this profile URL to indicate US Core conformance.

---

### 2. identifier

**FHIR**: `ServiceRequest.identifier`

**Cardinality**: 0..*

**C-CDA**: `procedure/id` or `act/id`

**Type**: Identifier array

**Mapping Logic**:

```typescript
function mapIdentifier(ccdaId: Element): Identifier {
  const root = ccdaId.getAttribute('root');
  const extension = ccdaId.getAttribute('extension');

  if (extension) {
    return {
      system: convertOidToUri(root),
      value: extension
    };
  } else {
    return {
      system: 'urn:ietf:rfc:3986',
      value: `urn:oid:${root}`
    };
  }
}
```

**Example**:

C-CDA:
```xml
<id root="db734647-fc99-424c-a864-7e3cda82e703"/>
```

FHIR:
```json
{
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
  }]
}
```

---

### 3. status (Required)

**FHIR**: `ServiceRequest.status`

**Cardinality**: 1..1 (Required)

**C-CDA**: `procedure/statusCode/@code` or `act/statusCode/@code`

**Binding**: Required to RequestStatus value set

**ConceptMap**:

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| active | active | Procedure is planned and active |
| completed | completed | Planning process complete (rare for planned procedure) |
| aborted | revoked | Procedure was cancelled |
| cancelled | revoked | Procedure order was cancelled |
| held | on-hold | Procedure temporarily suspended |
| suspended | on-hold | Procedure temporarily suspended |
| nullFlavor="UNK" | unknown | Status unknown |
| (any other) | draft | Default for unknown status codes |

**Default**: If statusCode is missing or unrecognized, default to **"active"** (planned procedures are typically active).

**Example**:

C-CDA:
```xml
<statusCode code="active"/>
```

FHIR:
```json
{
  "status": "active"
}
```

---

### 4. intent (Required)

**FHIR**: `ServiceRequest.intent`

**Cardinality**: 1..1 (Required)

**C-CDA**: `procedure/@moodCode` or `act/@moodCode`

**Binding**: Required to RequestIntent value set

**ConceptMap**:

| C-CDA moodCode | FHIR intent | Definition |
|----------------|-------------|------------|
| **INT** | plan | Planned intervention/procedure |
| **RQO** | order | Ordered procedure (formal order) |
| **PRP** | proposal | Proposed procedure (suggestion) |
| **ARQ** | order | Appointment request (treated as order) |
| **PRMS** | directive | Promise/commitment to perform |

**Validation**: Reject or skip procedures with moodCode=EVN (Event) or moodCode=GOL (Goal).

**Example**:

C-CDA:
```xml
<procedure classCode="PROC" moodCode="RQO">
```

FHIR:
```json
{
  "intent": "order"
}
```

---

### 5. category (Must Support)

**FHIR**: `ServiceRequest.category`

**Cardinality**: 0..*

**C-CDA**: Inferred from `code/@codeSystem` or `code/@code`

**Binding**: Required to US Core ServiceRequest Category Codes (extensible)

**Inference Rules**:

| Condition | FHIR category |
|-----------|---------------|
| code/@codeSystem = "2.16.840.1.113883.6.1" (LOINC) AND code starts with lab-related terms | 108252007 (Laboratory procedure) |
| code/@codeSystem = "2.16.840.1.113883.6.12" (CPT) AND code in radiology range (70000-79999) | 363679005 (Imaging) |
| code/@code = "409063005" (Counseling) | 409063005 (Counselling) |
| code/@code = "409073007" (Education) | 409073007 (Education) |
| code in surgical CPT codes (10000-69999) | 387713003 (Surgical procedure) |
| Unable to infer | 103693007 (Diagnostic procedure) - default |

**Example**:

C-CDA:
```xml
<code code="73761001" codeSystem="2.16.840.1.113883.6.96"
      displayName="Colonoscopy"/>
```

FHIR:
```json
{
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "387713003",
      "display": "Surgical procedure"
    }]
  }]
}
```

---

### 6. code (Required)

**FHIR**: `ServiceRequest.code`

**Cardinality**: 1..1 (Required)

**C-CDA**: `procedure/code` or `act/code`

**Binding**: Extensible to US Core Procedure Codes

**Mapping Logic**:

1. Extract primary code from `code/@code`, `code/@codeSystem`, `code/@displayName`
2. Extract translation codes from `code/translation` elements
3. Extract original text from `code/originalText` or linked narrative text
4. Construct CodeableConcept with coding array and text

**Code System OID to URI Mapping**:

| C-CDA codeSystem OID | FHIR system URI |
|----------------------|-----------------|
| 2.16.840.1.113883.6.1 | http://loinc.org |
| 2.16.840.1.113883.6.96 | http://snomed.info/sct |
| 2.16.840.1.113883.6.12 | http://www.ama-assn.org/go/cpt |
| 2.16.840.1.113883.6.4 | http://www.cms.gov/Medicare/Coding/ICD10 |
| 2.16.840.1.113883.6.13 | http://www.cms.gov/Medicare/Coding/MedHCPCSGenInfo/index.html |
| 2.16.840.1.113883.6.104 | http://www.ada.org/cdt |

**Example**:

C-CDA:
```xml
<code code="73761001" codeSystem="2.16.840.1.113883.6.96"
      displayName="Colonoscopy">
  <originalText>Screening colonoscopy</originalText>
  <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
               displayName="Colonoscopy, flexible"/>
</code>
```

FHIR:
```json
{
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "73761001",
        "display": "Colonoscopy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "45378",
        "display": "Colonoscopy, flexible"
      }
    ],
    "text": "Screening colonoscopy"
  }
}
```

---

### 7. code.text (Must Support, Additional USCDI)

**FHIR**: `ServiceRequest.code.text`

**Cardinality**: 0..1

**C-CDA**: `code/originalText` or `text/reference` (linked narrative)

**Mapping Priority**:

1. First, try `code/originalText` text content
2. If not present, try resolving `text/reference/@value` to narrative section
3. If neither present, use `code/@displayName`

**Example**:

C-CDA:
```xml
<code code="73761001" codeSystem="2.16.840.1.113883.6.96">
  <originalText>Screening colonoscopy for colon cancer prevention</originalText>
</code>
```

FHIR:
```json
{
  "code": {
    "coding": [...],
    "text": "Screening colonoscopy for colon cancer prevention"
  }
}
```

---

### 8. subject (Required)

**FHIR**: `ServiceRequest.subject`

**Cardinality**: 1..1 (Required)

**C-CDA**: Document-level `recordTarget/patientRole`

**Type**: Reference(US Core Patient)

**Mapping Logic**:

Extract patient reference from document header, not from procedure element itself (C-CDA procedures don't have inline subject).

**Example**:

C-CDA (document header):
```xml
<recordTarget>
  <patientRole>
    <id extension="12345" root="2.16.840.1.113883.4.1"/>
    <patient>...</patient>
  </patientRole>
</recordTarget>
```

FHIR:
```json
{
  "subject": {
    "reference": "Patient/patient-12345"
  }
}
```

---

### 9. encounter (Must Support)

**FHIR**: `ServiceRequest.encounter`

**Cardinality**: 0..1

**C-CDA**: Document-level `componentOf/encompassingEncounter`

**Type**: Reference(US Core Encounter)

**Mapping Logic**:

If the document has an encompassingEncounter, create an Encounter resource and reference it. Not all documents have encounters (e.g., standalone care plans).

**Example**:

C-CDA (document header):
```xml
<componentOf>
  <encompassingEncounter>
    <id root="encounter-123"/>
    <effectiveTime>
      <low value="20240115"/>
    </effectiveTime>
  </encompassingEncounter>
</componentOf>
```

FHIR:
```json
{
  "encounter": {
    "reference": "Encounter/encounter-123"
  }
}
```

---

### 10. occurrence[x] (Must Support)

**FHIR**: `ServiceRequest.occurrence[x]`

**Cardinality**: 0..1

**C-CDA**: `effectiveTime`

**Choice Types**: occurrenceDateTime | occurrencePeriod | occurrenceTiming

**Mapping Logic**:

| C-CDA effectiveTime Pattern | FHIR occurrence[x] Type | Mapping |
|-----------------------------|-------------------------|---------|
| `<effectiveTime value="..."/>` | occurrenceDateTime | Single timestamp → dateTime |
| `<effectiveTime><low/><high/></effectiveTime>` | occurrencePeriod | Period with start and end |
| `<effectiveTime><low/></effectiveTime>` (no high) | occurrencePeriod | Period with only start |
| Missing effectiveTime | (omit) | Leave occurrence[x] absent |

**DateTime Conversion**: Convert C-CDA timestamp (yyyyMMddHHmmss±ZZZZ) to FHIR dateTime (yyyy-MM-ddTHH:mm:ss±ZZ:ZZ).

**Example 1**: Single date

C-CDA:
```xml
<effectiveTime value="20240613"/>
```

FHIR:
```json
{
  "occurrenceDateTime": "2024-06-13"
}
```

**Example 2**: Date range

C-CDA:
```xml
<effectiveTime>
  <low value="20240601"/>
  <high value="20240630"/>
</effectiveTime>
```

FHIR:
```json
{
  "occurrencePeriod": {
    "start": "2024-06-01",
    "end": "2024-06-30"
  }
}
```

---

### 11. authoredOn (Must Support)

**FHIR**: `ServiceRequest.authoredOn`

**Cardinality**: 0..1

**C-CDA**: `author/time/@value`

**Type**: dateTime

**Mapping Logic**:

Extract timestamp from first author/time element. Convert C-CDA timestamp to FHIR dateTime format.

**Example**:

C-CDA:
```xml
<author>
  <time value="20240115140000-0500"/>
  <assignedAuthor>...</assignedAuthor>
</author>
```

FHIR:
```json
{
  "authoredOn": "2024-01-15T14:00:00-05:00"
}
```

---

### 12. requester (Must Support)

**FHIR**: `ServiceRequest.requester`

**Cardinality**: 0..1

**C-CDA**: `author/assignedAuthor`

**Type**: Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device)

**Mapping Logic**:

1. Create Practitioner resource from `assignedAuthor/assignedPerson`
2. If `assignedAuthor` includes `representedOrganization`, create PractitionerRole resource
3. Reference PractitionerRole (preferred) or Practitioner

**Example**:

C-CDA:
```xml
<author>
  <time value="20240115140000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>Sarah</given>
        <family>Smith</family>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

FHIR:
```json
{
  "requester": {
    "reference": "Practitioner/practitioner-npi-1234567890",
    "display": "Dr. Sarah Smith"
  }
}
```

---

### 13. performer (Optional)

**FHIR**: `ServiceRequest.performer`

**Cardinality**: 0..*

**C-CDA**: `performer/assignedEntity`

**Type**: Reference array

**Mapping Logic**:

1. Create Practitioner resource from `assignedEntity/assignedPerson`
2. If `assignedEntity` includes location/organization, create PractitionerRole
3. Add to performer array

**Example**:

C-CDA:
```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <assignedPerson>
      <name>
        <prefix>Dr.</prefix>
        <given>John</given>
        <family>Gastro</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</performer>
```

FHIR:
```json
{
  "performer": [{
    "reference": "Practitioner/practitioner-npi-9876543210",
    "display": "Dr. John Gastro"
  }]
}
```

---

### 14. performerType (Optional)

**FHIR**: `ServiceRequest.performerType`

**Cardinality**: 0..1

**C-CDA**: `performer/functionCode`

**Type**: CodeableConcept

**Mapping Logic**:

Map performer functionCode to FHIR performerType using Participant Role value set.

**Example**:

C-CDA:
```xml
<performer>
  <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                displayName="Primary Care Physician"/>
  <assignedEntity>...</assignedEntity>
</performer>
```

FHIR:
```json
{
  "performerType": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "PCP",
      "display": "Primary Care Physician"
    }]
  }
}
```

---

### 15. reasonCode (Must Support, Additional USCDI)

**FHIR**: `ServiceRequest.reasonCode`

**Cardinality**: 0..*

**C-CDA**: `entryRelationship[@typeCode='RSON']/observation` (Indication template `2.16.840.1.113883.10.20.22.4.19`)

**Type**: CodeableConcept array

**Binding**: Extensible to US Core Condition Codes

**Mapping Logic**:

1. Find entryRelationship elements with typeCode='RSON'
2. Extract observations with Indication template ID
3. Map observation/value (CD type) to CodeableConcept
4. Add to reasonCode array

**Example**:

C-CDA:
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
          displayName="Clinical finding"/>
    <statusCode code="completed"/>
    <value xsi:type="CD" code="428165003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Screening for colon cancer"/>
  </observation>
</entryRelationship>
```

FHIR:
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "428165003",
      "display": "Screening for colon cancer"
    }]
  }]
}
```

---

### 16. reasonReference (Must Support, Additional USCDI)

**FHIR**: `ServiceRequest.reasonReference`

**Cardinality**: 0..*

**C-CDA**: `entryRelationship[@typeCode='RSON']` referencing Problem Observation, other observations, or Entry References

**Type**: Reference(Condition | Observation | DiagnosticReport | DocumentReference) array

**Mapping Logic**:

1. Find entryRelationship elements with typeCode='RSON'
2. If the observation is a Problem Observation (`2.16.840.1.113883.10.20.22.4.4`), create Condition resource
3. If the observation is another clinical observation, create Observation resource
4. If entryRelationship contains Entry Reference template (`2.16.840.1.113883.10.20.22.4.122`), resolve reference to existing resource
5. Add Reference to reasonReference array

**Note**: US Core allows servers to support either reasonCode OR reasonReference. If both are present, include both.

**Example**:

C-CDA:
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
    <id root="problem-789"/>
    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
          displayName="Problem"/>
    <value xsi:type="CD" code="235919008" codeSystem="2.16.840.1.113883.6.96"
           displayName="Family history of colon cancer"/>
  </observation>
</entryRelationship>
```

FHIR:
```json
{
  "reasonReference": [{
    "reference": "Condition/condition-problem-789",
    "display": "Family history of colon cancer"
  }]
}
```

---

### 17. bodySite (Optional)

**FHIR**: `ServiceRequest.bodySite`

**Cardinality**: 0..*

**C-CDA**: `targetSiteCode`

**Type**: CodeableConcept array

**Binding**: Example to Body Site value set

**Mapping Logic**:

Extract all `targetSiteCode` elements and map to CodeableConcept array.

**Example**:

C-CDA:
```xml
<targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                displayName="Colon structure"/>
```

FHIR:
```json
{
  "bodySite": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "71854001",
      "display": "Colon structure"
    }]
  }]
}
```

---

### 18. priority (Optional)

**FHIR**: `ServiceRequest.priority`

**Cardinality**: 0..1

**C-CDA**: `priorityCode` or `entryRelationship` with Priority Preference template (`2.16.840.1.113883.10.20.22.4.143`)

**Type**: code

**Binding**: Required to RequestPriority value set

**ConceptMap**:

| C-CDA priorityCode | FHIR priority | Notes |
|--------------------|---------------|-------|
| R (Routine) | routine | Normal priority |
| UR (Urgent) | urgent | Urgent but not emergency |
| EM (Emergency) | stat | Emergency/STAT |
| A (ASAP) | asap | As soon as possible |
| EL (Elective) | routine | Elective procedure |

**Priority Preference Mapping**:

| C-CDA Priority Preference value | FHIR priority |
|---------------------------------|---------------|
| LA6270-8 (High priority) | urgent |
| LA6271-6 (Medium priority) | routine |
| LA6272-4 (Low priority) | routine |

**Default**: If not specified, omit (do not default to "routine").

**Example 1**: priorityCode

C-CDA:
```xml
<priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
              displayName="Routine"/>
```

FHIR:
```json
{
  "priority": "routine"
}
```

**Example 2**: Priority Preference observation

C-CDA:
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
    <code code="225773000" codeSystem="2.16.840.1.113883.6.96"
          displayName="Preference"/>
    <value xsi:type="CD" code="LA6270-8" codeSystem="2.16.840.1.113883.6.1"
           displayName="High priority"/>
  </observation>
</entryRelationship>
```

FHIR:
```json
{
  "priority": "urgent"
}
```

---

### 19. note (Optional)

**FHIR**: `ServiceRequest.note`

**Cardinality**: 0..*

**C-CDA**: `text` element or narrative section reference

**Type**: Annotation array

**Mapping Logic**:

1. If `text/reference/@value` exists, resolve to narrative text
2. If `text` has inline content, extract text
3. Create Annotation with text content

**Example**:

C-CDA:
```xml
<text>
  <reference value="#plan-proc-1"/>
</text>
```

Resolved narrative:
```
Colonoscopy scheduled for June 13, 2024. Patient to follow bowel prep instructions.
```

FHIR:
```json
{
  "note": [{
    "text": "Colonoscopy scheduled for June 13, 2024. Patient to follow bowel prep instructions."
  }]
}
```

---

### 20. patientInstruction (Optional)

**FHIR**: `ServiceRequest.patientInstruction`

**Cardinality**: 0..1

**C-CDA**: `entryRelationship[@typeCode='SUBJ'][@inversionInd='true']/act` with Instruction template (`2.16.840.1.113883.10.20.22.4.20`)

**Type**: string

**Mapping Logic**:

1. Find entryRelationship with typeCode='SUBJ' and inversionInd='true'
2. Extract Instruction act with template ID `2.16.840.1.113883.10.20.22.4.20`
3. Extract text content from `act/text`
4. Concatenate multiple instructions with newlines

**Example**:

C-CDA:
```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
    <code code="409073007" codeSystem="2.16.840.1.113883.6.96"
          displayName="Instruction"/>
    <text>Patient to follow bowel prep instructions 24 hours before procedure.
          NPO after midnight on day of procedure.</text>
    <statusCode code="completed"/>
  </act>
</entryRelationship>
```

FHIR:
```json
{
  "patientInstruction": "Patient to follow bowel prep instructions 24 hours before procedure. NPO after midnight on day of procedure."
}
```

---

### 21. supportingInfo (Optional)

**FHIR**: `ServiceRequest.supportingInfo`

**Cardinality**: 0..*

**C-CDA**: `entryRelationship` with Assessment Scale Observations, Entry References, or related Goal Observations

**Type**: Reference(Any) array

**Mapping Logic**:

1. Extract entryRelationship elements with typeCode='RSON' (not already mapped to reasonCode/reasonReference)
2. Extract entryRelationship elements referencing Goal Observations
3. Create corresponding FHIR resources (Observation, Goal, etc.)
4. Add References to supportingInfo array

**Example** (Goal Reference):

C-CDA:
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121"/>
    <id root="goal-123"/>
    <code code="289169006" codeSystem="2.16.840.1.113883.6.96"
          displayName="Weight loss"/>
  </observation>
</entryRelationship>
```

FHIR:
```json
{
  "supportingInfo": [{
    "reference": "Goal/goal-123",
    "display": "Weight loss"
  }]
}
```

---

### 22. insurance (Optional)

**FHIR**: `ServiceRequest.insurance`

**Cardinality**: 0..*

**C-CDA**: `entryRelationship[@typeCode='COMP']/act` with Planned Coverage template (`2.16.840.1.113883.10.20.22.4.129`)

**Type**: Reference(Coverage) array

**Mapping Logic**:

1. Find entryRelationship with typeCode='COMP'
2. Extract Planned Coverage act (template `2.16.840.1.113883.10.20.22.4.129`)
3. Within Planned Coverage, extract nested Coverage Activity (template `2.16.840.1.113883.10.20.22.4.60`)
4. Create Coverage resource
5. Add Reference to insurance array

**Example**:

C-CDA:
```xml
<entryRelationship typeCode="COMP">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.129"/>
    <id root="planned-coverage-456"/>
    <code code="48768-6" codeSystem="2.16.840.1.113883.6.1"
          displayName="Payment sources"/>
    <statusCode code="active"/>
    <entryRelationship typeCode="COMP">
      <act classCode="ACT" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.60"/>
        <!-- Coverage Activity details -->
      </act>
    </entryRelationship>
  </act>
</entryRelationship>
```

FHIR:
```json
{
  "insurance": [{
    "reference": "Coverage/coverage-456"
  }]
}
```

---

## Complete Mapping Examples

### Example 1: Simple Planned Procedure

**C-CDA Input**:

```xml
<procedure classCode="PROC" moodCode="RQO">
  <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
  <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
  <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Colonoscopy"/>
  <statusCode code="active"/>
  <effectiveTime value="20240613"/>
  <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"/>
</procedure>
```

**FHIR Output**:

```json
{
  "resourceType": "ServiceRequest",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
  }],
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "387713003",
      "display": "Surgical procedure"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73761001",
      "display": "Colonoscopy"
    }]
  },
  "subject": {
    "reference": "Patient/patient-12345"
  },
  "occurrenceDateTime": "2024-06-13",
  "priority": "routine"
}
```

---

### Example 2: Planned Procedure with Full Details

**C-CDA Input**:

```xml
<procedure classCode="PROC" moodCode="RQO">
  <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
  <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
  <text>
    <reference value="#plan-proc-1"/>
  </text>
  <statusCode code="active"/>
  <effectiveTime value="20240613"/>

  <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Colonoscopy">
    <originalText>Screening colonoscopy</originalText>
    <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
                 displayName="Colonoscopy, flexible"/>
  </code>

  <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Colon structure"/>

  <performer>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
      <assignedPerson>
        <name>
          <prefix>Dr.</prefix>
          <given>John</given>
          <family>Gastro</family>
        </name>
      </assignedPerson>
    </assignedEntity>
  </performer>

  <author>
    <time value="20240115140000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Sarah</given>
          <family>Smith</family>
        </name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                displayName="Routine"/>

  <!-- Indication -->
  <entryRelationship typeCode="RSON">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
      <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
            displayName="Clinical finding"/>
      <statusCode code="completed"/>
      <value xsi:type="CD" code="428165003" codeSystem="2.16.840.1.113883.6.96"
             displayName="Screening for colon cancer"/>
    </observation>
  </entryRelationship>

  <!-- Patient Instructions -->
  <entryRelationship typeCode="SUBJ" inversionInd="true">
    <act classCode="ACT" moodCode="INT">
      <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
      <code code="409073007" codeSystem="2.16.840.1.113883.6.96"
            displayName="Instruction"/>
      <text>Patient to follow bowel prep instructions 24 hours before procedure.
            NPO after midnight on day of procedure.</text>
      <statusCode code="completed"/>
    </act>
  </entryRelationship>

</procedure>
```

**FHIR Output**:

```json
{
  "resourceType": "ServiceRequest",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
  }],
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "387713003",
      "display": "Surgical procedure"
    }]
  }],
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "73761001",
        "display": "Colonoscopy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "45378",
        "display": "Colonoscopy, flexible"
      }
    ],
    "text": "Screening colonoscopy"
  },
  "subject": {
    "reference": "Patient/patient-12345"
  },
  "occurrenceDateTime": "2024-06-13",
  "authoredOn": "2024-01-15T14:00:00-05:00",
  "requester": {
    "reference": "Practitioner/practitioner-npi-1234567890",
    "display": "Dr. Sarah Smith"
  },
  "performer": [{
    "reference": "Practitioner/practitioner-npi-9876543210",
    "display": "Dr. John Gastro"
  }],
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "428165003",
      "display": "Screening for colon cancer"
    }]
  }],
  "bodySite": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "71854001",
      "display": "Colon structure"
    }]
  }],
  "priority": "routine",
  "patientInstruction": "Patient to follow bowel prep instructions 24 hours before procedure. NPO after midnight on day of procedure."
}
```

---

## Implementation Guidance

### 1. Section Processing

**Plan of Treatment Section**:
- Template ID: `2.16.840.1.113883.10.20.22.2.10`
- Extract entry elements
- Filter for Planned Procedure (4.41) and Planned Act (4.39) templates
- Validate moodCode ∈ {INT, RQO, PRP, ARQ, PRMS}
- Convert each to ServiceRequest

### 2. Resource Creation Dependencies

When creating ServiceRequest, ensure dependent resources are created first or concurrently:

1. **Patient** (from document recordTarget)
2. **Encounter** (from encompassingEncounter, if present)
3. **Practitioner** (from author, performer)
4. **PractitionerRole** (if author/performer includes organization)
5. **Condition** (from reasonReference Problem Observations)
6. **Observation** (from reasonReference clinical observations)
7. **Goal** (from supportingInfo Goal Observations if present)
8. **Coverage** (from insurance Planned Coverage)

Then create **ServiceRequest** with references to above resources.

### 3. Validation Rules

Before creating ServiceRequest:

1. **moodCode Validation**: MUST be INT, RQO, PRP, ARQ, or PRMS
2. **Required Elements**: Ensure statusCode, code, and document has recordTarget
3. **US Core Conformance**: Include profile URL in meta.profile
4. **Cardinality**: status (1..1), intent (1..1), code (1..1), subject (1..1)

### 4. Edge Cases

#### Missing effectiveTime

If Planned Procedure lacks effectiveTime:
- **Action**: Omit occurrence[x] from ServiceRequest
- **Rationale**: Better to omit than to fabricate timing

#### Missing author

If Planned Procedure lacks author:
- **Action**: Omit requester and authoredOn
- **Alternative**: Use document author as fallback if clinically appropriate

#### Multiple authors

If Planned Procedure has multiple authors:
- **Action**: Map first author to requester, add others to note as "Additional authors: ..."

#### Patient as author

If author is the patient (self-referral or patient-initiated request):
- **Action**: Set requester to Reference(Patient)

#### Missing statusCode

If statusCode is missing:
- **Default**: Use "active" (planned procedures are typically active)

### 5. Deduplication

If the same planned procedure appears in multiple documents (e.g., updated care plans):
- Compare by identifier (procedure/id)
- If identifiers match, update existing ServiceRequest rather than creating duplicate
- Track version history using meta.versionId

### 6. Linking ServiceRequest to Procedure

When a planned procedure is later performed:
- Create Procedure resource for the completed activity
- Set Procedure.basedOn to reference the originating ServiceRequest
- Update ServiceRequest.status to "completed"

This establishes the request-response workflow pattern.

### 7. Care Plan Context

In Care Plan documents:
- ServiceRequests are part of the care plan
- Link to CarePlan resource via CarePlan.activity.reference
- Link to goals via ServiceRequest.supportingInfo

---

## ConceptMaps

### C-CDA statusCode → FHIR ServiceRequest.status

**Source**: C-CDA statusCode

**Target**: FHIR RequestStatus value set

| Source Code | Target Code | Equivalence | Comment |
|-------------|-------------|-------------|---------|
| active | active | equivalent | Procedure is planned and active |
| completed | completed | equivalent | Planning complete (rare) |
| aborted | revoked | equivalent | Procedure cancelled |
| cancelled | revoked | equivalent | Order cancelled |
| held | on-hold | equivalent | Temporarily suspended |
| suspended | on-hold | equivalent | Temporarily suspended |
| nullFlavor="UNK" | unknown | equivalent | Status unknown |
| (other) | draft | wider | Default for unknown codes |

### C-CDA moodCode → FHIR ServiceRequest.intent

**Source**: C-CDA moodCode

**Target**: FHIR RequestIntent value set

| Source Code | Target Code | Equivalence | Comment |
|-------------|-------------|-------------|---------|
| INT | plan | equivalent | Planned intervention |
| RQO | order | equivalent | Formal order |
| PRP | proposal | equivalent | Proposal/suggestion |
| ARQ | order | narrower | Appointment request |
| PRMS | directive | equivalent | Promise/commitment |

### C-CDA priorityCode → FHIR ServiceRequest.priority

**Source**: C-CDA ActPriority

**Target**: FHIR RequestPriority value set

| Source Code | Target Code | Equivalence | Comment |
|-------------|-------------|-------------|---------|
| R | routine | equivalent | Routine priority |
| UR | urgent | equivalent | Urgent |
| EM | stat | equivalent | Emergency/STAT |
| A | asap | equivalent | As soon as possible |
| EL | routine | equivalent | Elective |

---

## Known Limitations

### Not Covered by C-CDA on FHIR IG

ServiceRequest mapping is **NOT included** in the C-CDA on FHIR Implementation Guide v2.0.0. This specification fills that gap based on:
- US Core ServiceRequest Profile requirements
- C-CDA Planned Procedure/Act template specifications
- Mapping patterns from other implemented resources

### C-CDA Gaps

C-CDA Planned Procedure does not include:
1. **Explicit category**: Must infer from code system or code values
2. **Detailed timing specifications**: effectiveTime is limited compared to FHIR Timing
3. **Formal ordering organization**: Organization context is limited
4. **Rejection/denial tracking**: No standard way to represent rejected requests

### FHIR Elements Without C-CDA Source

The following ServiceRequest elements have no direct C-CDA mapping:
- **orderDetail**: Additional performance details not captured in C-CDA
- **quantityQuantity/quantityRatio/quantityRange**: Service quantity (use case unclear in planned procedures)
- **doNotPerform**: C-CDA has no equivalent for "do not perform" orders
- **asNeeded[x]**: PRN (as needed) indicator not standardized in C-CDA Planned Procedure
- **locationReference**: Service delivery location (could infer from performer/assignedEntity/addr)
- **specimen**: Specimen for lab orders (not in Planned Procedure template)
- **basedOn**: Reference to other requests (no equivalent in C-CDA)
- **replaces**: Request replacement tracking (no equivalent in C-CDA)
- **requisition**: Group identifier (no equivalent in C-CDA)

---

## Testing Recommendations

### Unit Tests

1. **moodCode validation**: Verify only INT/RQO/PRP/ARQ/PRMS convert to ServiceRequest
2. **Required elements**: Test missing statusCode, code, subject handling
3. **effectiveTime variants**: Test single date, date range, missing effectiveTime
4. **Code system conversions**: Test LOINC, SNOMED, CPT code mappings
5. **Priority mappings**: Test all priority codes and Priority Preference observations
6. **Indication extraction**: Test reasonCode and reasonReference from RSON relationships
7. **Instruction extraction**: Test patientInstruction from SUBJ relationships
8. **Author mapping**: Test requester and authoredOn extraction
9. **Performer mapping**: Test performer extraction with and without organization
10. **Category inference**: Test category assignment based on code system

### Integration Tests

1. **Complete Plan of Treatment Section**: Convert section with multiple planned procedures
2. **Care Plan document**: Test ServiceRequest creation within Care Plan context
3. **Missing optional elements**: Test minimal Planned Procedure (only required elements)
4. **Full example**: Test Planned Procedure with all optional elements
5. **Deduplication**: Test handling of duplicate planned procedures across documents
6. **Reference resolution**: Verify all references (Patient, Practitioner, Condition, etc.) resolve correctly

### US Core Conformance Tests

1. **Profile validation**: Validate against US Core ServiceRequest Profile
2. **Required elements**: Verify status, intent, code, subject present
3. **Must Support**: Verify category, encounter, occurrence[x], authoredOn, requester when data available
4. **Search parameters**: Test patient, patient+category, patient+code, patient+category+authored searches
5. **Cardinality**: Verify all elements meet cardinality constraints
6. **Code bindings**: Verify status, intent use required bindings; category, code use extensible bindings

---

## Implementation Checklist

### Core Converter (`ccda_to_fhir/converters/service_request.py`)

- [ ] Create `ServiceRequestConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Planned Procedure or Planned Act element
- [ ] Validate moodCode ∈ {INT, RQO, PRP, ARQ, PRMS}
- [ ] Reject moodCode=EVN (use Procedure converter instead)
- [ ] Reject moodCode=GOL (use Goal converter instead)
- [ ] Map `id` → `identifier` (OID to Identifier conversion)
- [ ] Map `statusCode` → `status` per ConceptMap
- [ ] Map `moodCode` → `intent` per ConceptMap
- [ ] Map `code` → `code` (CodeableConcept with coding array and text)
- [ ] Infer `category` from code system or code value
- [ ] Extract patient reference from document `recordTarget` → `subject`
- [ ] Extract encounter reference from document `encompassingEncounter` → `encounter`
- [ ] Map `effectiveTime` → `occurrence[x]` (handle single date, date range, missing)
- [ ] Map `author/time` → `authoredOn`
- [ ] Map `author/assignedAuthor` → `requester` (create Practitioner/PractitionerRole)
- [ ] Map `performer/assignedEntity` → `performer` array
- [ ] Map `performer/functionCode` → `performerType`
- [ ] Map `priorityCode` → `priority` per ConceptMap
- [ ] Map Priority Preference observation → `priority`
- [ ] Map `targetSiteCode` → `bodySite` array
- [ ] Map entryRelationship[typeCode='RSON'] Indication → `reasonCode` array
- [ ] Map entryRelationship[typeCode='RSON'] Problem Observation → `reasonReference` array
- [ ] Map entryRelationship[typeCode='SUBJ'] Instruction → `patientInstruction`
- [ ] Map `text` or narrative reference → `note` array
- [ ] Map entryRelationship Goal Observations → `supportingInfo` array
- [ ] Map entryRelationship Planned Coverage → `insurance` array
- [ ] Set `meta.profile` to US Core ServiceRequest Profile URL

### Section Processing (`ccda_to_fhir/sections/plan_of_treatment_section.py`)

- [ ] Create `PlanOfTreatmentSectionProcessor` class
- [ ] Identify Plan of Treatment Section by template ID `2.16.840.1.113883.10.20.22.2.10`
- [ ] Extract entry elements
- [ ] Filter for Planned Procedure (4.41) and Planned Act (4.39) templates
- [ ] Validate moodCode before calling converter
- [ ] Call `ServiceRequestConverter` for each planned entry
- [ ] Store ServiceRequest resources in result bundle

### Model Validation (`ccda_to_fhir/models.py`)

- [ ] Add `is_planned_procedure()` validator for template `2.16.840.1.113883.10.20.22.4.41`
- [ ] Add `is_planned_act()` validator for template `2.16.840.1.113883.10.20.22.4.39`
- [ ] Add `is_plan_of_treatment_section()` validator for template `2.16.840.1.113883.10.20.22.2.10`
- [ ] Validate moodCode attribute existence and value
- [ ] Validate required elements: id, code, statusCode

### Tests (`tests/converters/test_service_request.py`)

- [ ] Test Planned Procedure → ServiceRequest conversion
- [ ] Test Planned Act → ServiceRequest conversion
- [ ] Test moodCode validation (INT/RQO/PRP accepted; EVN/GOL rejected)
- [ ] Test status mapping for all status codes
- [ ] Test intent mapping for all moodCodes
- [ ] Test category inference from code systems
- [ ] Test code mapping with multiple codings and originalText
- [ ] Test identifier mapping (OID conversion)
- [ ] Test occurrence[x] mapping (single date, date range, missing)
- [ ] Test author mapping (requester and authoredOn)
- [ ] Test performer mapping (with and without organization)
- [ ] Test performerType mapping
- [ ] Test priority mapping (priorityCode and Priority Preference)
- [ ] Test bodySite mapping
- [ ] Test reasonCode extraction from Indication observations
- [ ] Test reasonReference extraction from Problem Observations
- [ ] Test patientInstruction extraction from Instruction acts
- [ ] Test note extraction from text/narrative
- [ ] Test supportingInfo extraction from Goal Observations (if present)
- [ ] Test insurance extraction (Planned Coverage)
- [ ] Test missing optional elements
- [ ] Test minimal Planned Procedure (only required elements)

### Integration Tests (`tests/integration/test_plan_of_treatment_section.py`)

- [ ] Test Plan of Treatment Section extraction
- [ ] Test multiple planned procedures in one section
- [ ] Test mixed Planned Procedure and Planned Act entries
- [ ] Test complete Care Plan document with planned procedures
- [ ] Test ServiceRequest references to other resources (Patient, Practitioner, Condition, Goal, Coverage)
- [ ] Test bundle structure with all dependent resources

### US Core Conformance

- [ ] Validate required elements: status, intent, code, subject
- [ ] Validate Must Support: category, code.text, encounter, occurrence[x], authoredOn, requester, reasonCode, reasonReference
- [ ] Include US Core ServiceRequest profile in meta.profile
- [ ] Support search parameters: patient, _id, patient+category, patient+code, patient+category+authored

---

## Related Documentation

- [FHIR ServiceRequest Resource](../fhir/service-request.md)
- [C-CDA Planned Procedure Templates](../ccda/planned-procedure.md)
- [Procedure Mapping](05-procedure.md) - For completed procedures (moodCode=EVN)
- [Goal Mapping](13-goal.md) - For goal observations (moodCode=GOL)
- [Participations Mapping](09-participations.md) - For Practitioner/PractitionerRole creation
- [Condition Mapping](02-condition.md) - For reasonReference Problem Observations

---

## References

- [US Core ServiceRequest Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest)
- [FHIR R4 ServiceRequest Resource](http://hl7.org/fhir/R4/servicerequest.html)
- [C-CDA Planned Procedure Template](https://hl7.org/cda/us/ccda/2024Jan/StructureDefinition-PlannedProcedure.html)
- [C-CDA Planned Act Template](https://build.fhir.org/ig/HL7/CDA-ccda-2.2/StructureDefinition-2.16.840.1.113883.10.20.22.4.39.html)
- [C-CDA Plan of Treatment Section](https://build.fhir.org/ig/HL7/CDA-ccda-2.2/StructureDefinition-2.16.840.1.113883.10.20.22.2.10.html)
- [C-CDA on FHIR IG v2.0.0](https://build.fhir.org/ig/HL7/ccda-on-fhir/) - Note: ServiceRequest NOT included
- [C-CDA Examples - GitHub](https://github.com/HL7/C-CDA-Examples/)

---

**Status**: DOCUMENTED, NOT YET IMPLEMENTED

**Priority**: LOW - Partially covered by Procedure resource with status=planned

**Next Steps**: Implement `ServiceRequestConverter` and `PlanOfTreatmentSectionProcessor` classes
