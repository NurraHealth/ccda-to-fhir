# FHIR R4: Composition Resource

## Overview

The Composition resource defines the structure and narrative content of a document. It is a coherent set of information that is a statement of healthcare information, including clinical observations and services. A Composition defines the structure and narrative content necessary for a document and is the basis for a document. In the context of C-CDA conversion, Composition is the FHIR representation of a ClinicalDocument's structure and metadata.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Composition |
| FHIR Version | R4 (4.0.1) |
| Maturity Level | 2 (Trial Use) |
| Security Category | N/A |
| Responsible Work Group | Structured Documents |
| URL | https://hl7.org/fhir/R4/composition.html |
| C-CDA on FHIR Profiles | Document-level profiles (CCD, Care Plan, Discharge Summary, etc.) |

## Scope and Usage

The Composition resource is the foundation of FHIR documents. Key characteristics:

- **Documents**: A Composition is the basis for a FHIR document (Bundle with type="document")
- **First Entry**: In a document Bundle, the Composition must be the first entry
- **Sections**: Contains sections that organize and reference other resources
- **Immutability**: Once a document is assembled, it cannot be changed (new versions create new Compositions)
- **Clinical Documents**: Primary use case is clinical documents (C-CDA, clinical notes, discharge summaries)

### Key Differences from DocumentReference

| Aspect | Composition | DocumentReference |
|--------|-------------|-------------------|
| Purpose | Defines document structure and content | Indexes and references documents |
| Usage | Part of the document itself | Metadata about a document |
| Location | First entry in document Bundle | Separate resource pointing to document |
| Sections | Contains section structure | No section structure |
| References | References resources within document | References external document URL or data |

## JSON Structure

```json
{
  "resourceType": "Composition",
  "id": "example-ccd",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document"
    ]
  },
  "text": {
    "status": "generated",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h2>Continuity of Care Document</h2><p>Document for Ellen Ross, DOB 1975-05-01</p></div>"
  },
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f"
  },
  "status": "final",
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
          "system": "http://loinc.org",
          "code": "LP173421-1",
          "display": "Report"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "date": "2020-03-01T10:20:00-05:00",
  "author": [
    {
      "reference": "Practitioner/example",
      "display": "Dr. Adam Careful"
    }
  ],
  "title": "Continuity of Care Document",
  "confidentiality": "N",
  "attester": [
    {
      "mode": "legal",
      "time": "2020-03-01T10:20:00-05:00",
      "party": {
        "reference": "Practitioner/example",
        "display": "Dr. Adam Careful"
      }
    }
  ],
  "custodian": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "relatesTo": [
    {
      "code": "replaces",
      "targetIdentifier": {
        "system": "urn:ietf:rfc:3986",
        "value": "urn:uuid:c6c7b1e3-2b5a-4f9e-8d6c-1a2b3c4d5e6f"
      }
    }
  ],
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
          "reference": "Practitioner/example"
        }
      ]
    }
  ],
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
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td>Penicillin</td><td>Hives</td></tr></table></div>"
      },
      "mode": "snapshot",
      "orderedBy": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/list-order",
            "code": "event-date",
            "display": "Sorted by Event Date"
          }
        ]
      },
      "entry": [
        {
          "reference": "AllergyIntolerance/example"
        }
      ],
      "emptyReason": null
    },
    {
      "title": "Medications",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "10160-0",
            "display": "History of Medication use Narrative"
          }
        ]
      },
      "text": {
        "status": "generated",
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td>Lisinopril 10mg daily</td></tr></table></div>"
      },
      "mode": "snapshot",
      "entry": [
        {
          "reference": "MedicationRequest/example"
        }
      ]
    },
    {
      "title": "Problem List",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "11450-4",
            "display": "Problem list - Reported"
          }
        ]
      },
      "text": {
        "status": "generated",
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td>Essential hypertension</td></tr></table></div>"
      },
      "mode": "snapshot",
      "entry": [
        {
          "reference": "Condition/example"
        }
      ]
    }
  ]
}
```

## Element Definitions

### identifier (0..1)

Version-specific identifier for the composition.

| Type | Description |
|------|-------------|
| Identifier | Logical identifier for this version of the Composition |

**Usage Notes:**
- Maps from C-CDA `ClinicalDocument/id`
- Should be unique for each document version
- Use `urn:uuid:` URIs for UUIDs or `urn:oid:` for OID-based identifiers
- Different from `Composition.meta.versionId` which is assigned by the server

### status (1..1)

The workflow/clinical status of the composition. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | preliminary \| final \| amended \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/composition-status (Required binding)

**Status Definitions (FHIR R4):**

| Code | Display | Definition |
|------|---------|------------|
| preliminary | Preliminary | This is a preliminary composition or document (also known as initial or interim). Content may be incomplete or unverified. |
| final | Final | This version of the composition is complete and verified by an appropriate person and no further work is planned. Any subsequent updates would be on a new version of the composition. |
| amended | Amended | The composition content or the referenced resources have been modified (edited or added to) subsequent to being released as "final" and the composition is complete and verified by an authorized person. |
| entered-in-error | Entered in Error | The composition or document was originally created/issued in error, and this is an amendment that marks that the entire series should not have been created. |

**C-CDA Mapping:**
- Most C-CDA documents should map to `final` (completed clinical documentation)
- `amended` may be inferred from document relationships with typeCode='RPLC' (replaces)
- `preliminary` if document explicitly indicates draft or preliminary status
- `entered-in-error` only if explicitly marked as erroneous

**Note:** FHIR R4 does not support appended, corrected, cancelled, or other status values found in later FHIR versions. For C-CDA documents with addendum relationships (typeCode='APND'), use the `relatesTo` element with code='appends' rather than trying to represent this in status.

### type (1..1)

Specifies the particular kind of composition (e.g., Consultation Note, Discharge Summary).

| Type | Description |
|------|-------------|
| CodeableConcept | Kind of composition (LOINC Document Ontology) |

**Value Set:** http://hl7.org/fhir/ValueSet/doc-typecodes (Preferred binding)

**Common Document Type Codes (LOINC):**

| Code | Display | C-CDA Template |
|------|---------|----------------|
| 34133-9 | Summarization of Episode Note | Continuity of Care Document (CCD) |
| 18842-5 | Discharge Summary | Discharge Summary |
| 11488-4 | Consultation Note | Consultation Note |
| 18748-4 | Diagnostic imaging study | Diagnostic Imaging Report |
| 11504-8 | Surgical Operation Note | Operative Note |
| 11506-3 | Progress Note | Progress Note |
| 28570-0 | Procedure Note | Procedure Note |
| 34117-2 | History and Physical Note | History and Physical |
| 57133-1 | Referral Note | Referral Note |
| 34111-5 | Emergency Department Note | ED Note |
| 52521-2 | Overall plan of care/advance care directives | Care Plan |
| 57016-8 | Privacy Policy Acknowledgement Document | Privacy Policy |
| 57024-2 | Health Quality Measure Document | Quality Measure |

### category (0..*)

High-level categorization of the composition.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Categorization of Composition |

**Value Set:** http://hl7.org/fhir/ValueSet/referenced-item-category (Example binding)

**Common Categories:**
- Laboratory reports
- Radiology reports
- Clinical notes
- Administrative documents

### subject (1..1)

Who or what the composition is about.

| Type | Description |
|------|-------------|
| Reference(Any) | Who and/or what the composition is about |

**Typical References:**
- Patient (most common for clinical documents)
- Group (for population-level documents)
- Device
- Location

**US Core / C-CDA on FHIR:**
- SHALL reference a Patient resource
- Maps from C-CDA `recordTarget/patientRole`

### encounter (0..1)

Describes the clinical encounter that the composition is associated with.

| Type | Description |
|------|-------------|
| Reference(Encounter) | Context of the Composition |

**Usage Notes:**
- Not always present (e.g., longitudinal care summaries)
- Maps from C-CDA `componentOf/encompassingEncounter`
- Should reference an Encounter resource in the same Bundle

### date (1..1)

The composition editing time, when the composition was last logically changed by the author.

| Type | Description |
|------|-------------|
| dateTime | Composition editing time |

**Usage Notes:**
- Required element
- Maps from C-CDA `ClinicalDocument/effectiveTime`
- For C-CDA on FHIR: precision SHALL be to at least the day, SHOULD be to the second
- Use ISO 8601 format: `YYYY-MM-DDThh:mm:ss+zz:zz`

### author (1..*)

Identifies who is responsible for the information in the composition.

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Device \| Patient \| RelatedPerson \| Organization) | Who authored the composition |

**Cardinality:** 1..* (at least one author required)

**Usage Notes:**
- Maps from C-CDA `author`
- Multiple authors are allowed
- If C-CDA has multiple authors, include all in the array
- Author's timestamp maps to separate Provenance resource if detailed tracking needed

### title (1..1)

Official human-readable label for the composition.

| Type | Description |
|------|-------------|
| string | Human Readable name/title |

**Usage Notes:**
- Required element
- Maps from C-CDA `ClinicalDocument/title`
- Should match the document type (e.g., "Continuity of Care Document")
- Not necessarily unique

### confidentiality (0..1)

The code specifying the level of confidentiality of the Composition. This is a **modifier element**.

| Type | Description |
|------|-------------|
| code | As defined by affinity domain |

**Value Set:** http://terminology.hl7.org/ValueSet/v3-ConfidentialityClassification (Extensible binding)

**Common Codes (v3-ConfidentialityClassification):**

| Code | Display | Definition |
|------|---------|------------|
| U | unrestricted | Privacy metadata indicating that no level of protection is required |
| L | low | Privacy metadata indicating that a low level of protection is required |
| M | moderate | Privacy metadata indicating that a moderate level of protection is required |
| N | normal | Privacy metadata indicating that the information is typical |
| R | restricted | Privacy metadata indicating that the information is sensitive |
| V | very restricted | Privacy metadata indicating that the information is very sensitive |

**C-CDA Mapping:**
- Maps from C-CDA `confidentialityCode/@code`
- Code system: `2.16.840.1.113883.5.25` (v3-Confidentiality)

### attester (0..*)

A participant who has attested to the accuracy of the composition.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| mode | code | 1..1 | personal \| professional \| legal \| official |
| time | dateTime | 0..1 | When the composition was attested |
| party | Reference(Patient \| RelatedPerson \| Practitioner \| PractitionerRole \| Organization) | 0..1 | Who attested the composition |

**Attestation Modes:**

| Code | Display | Definition | C-CDA Mapping |
|------|---------|------------|---------------|
| personal | Personal | The person authenticated the content in their personal capacity | `authenticator` |
| professional | Professional | The person authenticated the content in their professional capacity | `authenticator` |
| legal | Legal | The person authenticated the content and accepted legal responsibility | `legalAuthenticator` |
| official | Official | The organization authenticated the content as consistent with their policies | `authenticator` (organization) |

**C-CDA Mapping:**
- `legalAuthenticator` → attester with mode="legal"
- `authenticator` → attester with mode="professional" or "personal"
- `legalAuthenticator/time` → attester.time
- `legalAuthenticator/assignedEntity` → attester.party

### custodian (0..1)

Identifies the organization responsible for ongoing maintenance of and access to the composition.

| Type | Description |
|------|-------------|
| Reference(Organization) | Organization which maintains the composition |

**Usage Notes:**
- Maps from C-CDA `custodian/assignedCustodian/representedCustodianOrganization`
- Usually the healthcare organization that created/maintains the document
- Should reference an Organization resource in the Bundle

### relatesTo (0..*)

Relationships to other compositions or documents.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| code | code | 1..1 | replaces \| transforms \| signs \| appends |
| target[x] | Identifier \| Reference(Composition) | 1..1 | Target of the relationship |

**Relationship Codes:**

| Code | Display | Definition | C-CDA Mapping |
|------|---------|------------|---------------|
| replaces | Replaces | This document logically replaces or supersedes the target | relatedDocument[@typeCode='RPLC'] |
| transforms | Transforms | This document was generated by transforming the target | relatedDocument[@typeCode='XFRM'] |
| signs | Signs | This document signs the target | N/A |
| appends | Appends | This document appends additional information to the target | relatedDocument[@typeCode='APND'] |

**C-CDA Mapping:**
- Maps from C-CDA `relatedDocument`
- `relatedDocument/parentDocument/id` → `relatesTo.targetIdentifier`
- `relatedDocument/@typeCode` → `relatesTo.code`

**Example:**
```json
{
  "relatesTo": [
    {
      "code": "replaces",
      "targetIdentifier": {
        "system": "urn:ietf:rfc:3986",
        "value": "urn:uuid:c6c7b1e3-2b5a-4f9e-8d6c-1a2b3c4d5e6f"
      }
    }
  ]
}
```

### event (0..*)

The clinical service(s) being documented.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| code | CodeableConcept[] | 0..* | Code(s) describing the type of event |
| period | Period | 0..1 | The period covered by the documentation |
| detail | Reference(Any)[] | 0..* | The event(s) being documented |

**Usage Notes:**
- Maps from C-CDA `documentationOf/serviceEvent`
- `serviceEvent/@classCode` → `event.code`
- `serviceEvent/effectiveTime` → `event.period`
- `serviceEvent/performer` → `event.detail` (reference to Practitioner/PractitionerRole)

**Common Event Codes (v3-ActClass):**

| Code | Display | Use Case |
|------|---------|----------|
| PCPR | care provision | General care provision |
| ENC | encounter | Specific encounter |
| IMP | inpatient encounter | Inpatient stay |
| ACUTE | inpatient acute | Acute inpatient |
| SS | short stay | Short stay |
| VR | virtual | Virtual visit |

**Example:**
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
          "reference": "Practitioner/example-pcp"
        }
      ]
    }
  ]
}
```

### section (0..*)

The root of the sections that make up the composition.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| title | string | 0..1 | Label for section (required in C-CDA on FHIR) |
| code | CodeableConcept | 0..1 | Classification of section (LOINC Document Ontology) |
| author | Reference(Practitioner \| PractitionerRole \| Device \| Patient \| RelatedPerson \| Organization)[] | 0..* | Who authored the section |
| focus | Reference(Any) | 0..1 | Who/what the section is about |
| text | Narrative | 0..1 | Human-readable section content |
| mode | code | 0..1 | working \| snapshot \| changes |
| orderedBy | CodeableConcept | 0..1 | Order of section entries |
| entry | Reference(Any)[] | 0..* | Resources referenced by this section |
| emptyReason | CodeableConcept | 0..1 | Why the section is empty |
| section | (recursive) | 0..* | Nested sub-sections |

#### section.title

Label for the section.

| Type | Required | Description |
|------|----------|-------------|
| string | C-CDA: YES | Human-readable label |

**Usage Notes:**
- Maps from C-CDA `section/title`
- Required by C-CDA on FHIR profiles
- Should be human-readable (e.g., "Allergies and Intolerances")

#### section.code

Classification code for the section.

| Type | Description |
|------|-------------|
| CodeableConcept | Section classification (LOINC) |

**Value Set:** http://hl7.org/fhir/ValueSet/doc-section-codes (Example binding)

**Common Section Codes (LOINC):**

| Code | Display | C-CDA Template |
|------|---------|----------------|
| 48765-2 | Allergies and adverse reactions Document | Allergies Section |
| 10160-0 | History of Medication use Narrative | Medications Section |
| 11450-4 | Problem list - Reported | Problem List Section |
| 29762-2 | Social history Narrative | Social History Section |
| 8716-3 | Vital signs | Vital Signs Section |
| 30954-2 | Relevant diagnostic tests/laboratory data Narrative | Results Section |
| 47519-4 | History of Procedures Document | Procedures Section |
| 11369-6 | History of Immunization Narrative | Immunizations Section |
| 46240-8 | Encounter list | Encounters Section |
| 42348-3 | Advance directives | Advance Directives Section |
| 42349-1 | Reason for referral | Reason for Referral |
| 10164-2 | History of Present illness Narrative | History of Present Illness |
| 10157-6 | History of family member diseases Narrative | Family History |
| 29545-1 | Physical examination Narrative | Physical Exam |
| 51847-2 | Assessment (evaluation) and plan Narrative | Assessment and Plan |
| 18776-5 | Plan of care note | Plan of Treatment |
| 61146-7 | Goals | Goals Section |
| 75310-3 | Health concerns Document | Health Concerns |
| 85847-2 | Patient Care team information | Care Teams |

**C-CDA Mapping:**
- Maps from C-CDA `section/code/@code`
- Code system: `2.16.840.1.113883.6.1` (LOINC)

#### section.text

Human-readable narrative content of the section.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| status | code | 1..1 | generated \| extensions \| additional \| empty |
| div | xhtml | 1..1 | Limited xhtml content |

**Narrative Status:**

| Code | Definition | Use Case |
|------|------------|----------|
| generated | Generated by system | System-generated from structured data |
| extensions | Extensions included | Contains extensions |
| additional | Additional narrative | Hand-authored narrative in addition to data |
| empty | Empty narrative | Section has no narrative |

**Usage Notes:**
- Maps from C-CDA `section/text`
- Must be valid XHTML (within div)
- C-CDA text uses different namespace and elements than FHIR XHTML
- Conversion required from C-CDA narrative elements to XHTML

**C-CDA to XHTML Mapping:**

| C-CDA Element | XHTML Element |
|---------------|---------------|
| `<content>` | `<span>` |
| `<paragraph>` | `<p>` |
| `<list>` | `<ul>` or `<ol>` |
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
| `@styleCode` | `@class` |

**Example:**
```json
{
  "text": {
    "status": "generated",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><thead><tr><th>Medication</th><th>Dose</th><th>Frequency</th></tr></thead><tbody><tr><td>Lisinopril</td><td>10mg</td><td>Daily</td></tr></tbody></table></div>"
  }
}
```

#### section.mode

How the entry list was created.

| Type | Values |
|------|--------|
| code | working \| snapshot \| changes |

**Mode Definitions:**

| Code | Display | Definition |
|------|---------|------------|
| working | Working | This list is the current working list |
| snapshot | Snapshot | This list is a point-in-time snapshot |
| changes | Changes | This list shows what has changed since a prior version |

**Usage Notes:**
- Most C-CDA sections should use `snapshot`
- `working` for sections that may be updated
- `changes` for addendum documents

#### section.orderedBy

Specifies the order applied to the section entries.

| Type | Description |
|------|-------------|
| CodeableConcept | Order of section entries |

**Value Set:** http://hl7.org/fhir/ValueSet/list-order (Preferred binding)

**Common Ordering:**

| Code | Display | Use Case |
|------|---------|----------|
| user | Sorted by User | User-defined order |
| system | Sorted by System | System-assigned order |
| event-date | Sorted by Event Date | Chronological by event date |
| entry-date | Sorted by Item Date | Chronological by entry date |
| priority | Sorted by Priority | By priority/importance |
| alphabetic | Sorted Alphabetically | Alphabetical order |

#### section.entry

References to resources that provide the data for the section.

| Type | Description |
|------|-------------|
| Reference(Any)[] | Resources included in the section |

**Usage Notes:**
- References resources in the same Bundle
- Each C-CDA entry maps to one or more FHIR resources
- All referenced resources should be included in the document Bundle
- Reference format: `"reference": "ResourceType/id"`

**Common Entry Types by Section:**

| Section | Common Entry Types |
|---------|-------------------|
| Allergies | AllergyIntolerance |
| Medications | MedicationRequest, MedicationStatement |
| Problems | Condition |
| Procedures | Procedure |
| Immunizations | Immunization |
| Results | Observation, DiagnosticReport |
| Vital Signs | Observation (vital-signs category) |
| Encounters | Encounter |
| Goals | Goal |
| Care Team | CareTeam |
| Social History | Observation (social-history category) |

#### section.emptyReason

Why the section is empty (if it is).

| Type | Description |
|------|-------------|
| CodeableConcept | Why the section is empty |

**Value Set:** http://hl7.org/fhir/ValueSet/list-empty-reason (Preferred binding)

**Common Empty Reasons:**

| Code | Display | C-CDA Equivalent |
|------|---------|------------------|
| nilknown | Nil Known | No known items |
| notasked | Not Asked | Information not requested |
| withheld | Information Withheld | Patient declined to provide |
| unavailable | Unavailable | Information unavailable |
| notstarted | Not Started | Section not yet populated |
| closed | Closed | Section closed |

**Usage Notes:**
- Use when section has no entries
- Maps from C-CDA `section/text` with nullFlavor or "No known..." text
- C-CDA often uses text like "No known allergies" which should map to `nilknown`

**Constraints:**
- `section.emptyReason` SHALL only be present if `section.entry` is empty
- If both `section.entry` and `section.emptyReason` are missing, the meaning is unknown

#### section.section (recursive)

Nested sub-sections.

| Type | Description |
|------|-------------|
| (Composition.section) | Nested sub-section |

**Usage Notes:**
- Same structure as parent section
- C-CDA allows nested sections (e.g., sub-sections within Results)
- Preserve nesting structure when mapping from C-CDA
- Maximum depth is not specified by FHIR but typically 2-3 levels

## Document Bundles

When creating a FHIR document from a C-CDA document, the result is a Bundle with:
1. `type` = "document"
2. `Composition` as the first entry
3. All resources referenced by the Composition

### Bundle Structure

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "timestamp": "2020-03-01T10:20:00-05:00",
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f"
  },
  "entry": [
    {
      "fullUrl": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f",
      "resource": {
        "resourceType": "Composition",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:patient-123",
      "resource": {
        "resourceType": "Patient",
        ...
      }
    },
    ...
  ]
}
```

### Document Bundle Rules

1. **Bundle.type** MUST be "document"
2. **First entry** MUST be a Composition resource
3. **Bundle.identifier** SHOULD match `Composition.identifier`
4. **Bundle.timestamp** SHOULD match `Composition.date`
5. **All referenced resources** MUST be included in the Bundle
6. **fullUrl** MUST be provided for each entry (use UUIDs if no stable URLs)
7. **No broken references** - all references must resolve within the Bundle

## C-CDA on FHIR Profiles

The C-CDA on FHIR Implementation Guide defines profiles for specific document types:

| C-CDA Document Type | FHIR Profile URL |
|---------------------|------------------|
| Continuity of Care Document (CCD) | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document |
| Consultation Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Consultation-Note |
| Discharge Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Discharge-Summary |
| Diagnostic Imaging Report | http://hl7.org/fhir/us/ccda/StructureDefinition/Diagnostic-Imaging-Report |
| History and Physical | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-History-and-Physical |
| Operative Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Operative-Note |
| Procedure Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Procedure-Note |
| Progress Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Progress-Note |
| Referral Note | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Referral-Note |
| Transfer Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Transfer-Summary |
| Care Plan | http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document |

### Profile Requirements

All C-CDA on FHIR Composition profiles require:
- **identifier**: 1..1 (required)
- **status**: 1..1 (required)
- **type**: 1..1 (required, bound to specific LOINC code)
- **subject**: 1..1 (required, must reference Patient)
- **date**: 1..1 (required)
- **author**: 1..* (at least one required)
- **title**: 1..1 (required)
- **custodian**: 1..1 (required)
- **section.title**: 1..1 (required for each section)
- **section.code**: 1..1 (required for each section)
- **section.text**: 0..1 (should be present if section has content)

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | registered \| partial \| preliminary \| final \| amended \| corrected \| appended \| cancelled \| entered-in-error \| deprecated \| unknown |
| identifier | token | Version-specific identifier |
| type | token | Kind of composition (LOINC Document Ontology) |
| category | token | Categorization of Composition |
| subject | reference | Who/what the composition is about |
| patient | reference | Who the composition is about (when subject is Patient) |
| encounter | reference | Context of the composition |
| date | date | Composition editing time |
| author | reference | Who authored the composition |
| title | string | Human-readable name/title |
| confidentiality | token | As defined by affinity domain |
| attester | reference | Who attested the composition |
| custodian | reference | Organization which maintains the composition |
| event | token | Code(s) for main clinical acts documented |
| period | date | The period covered by the documentation |
| section | token | Classification of section (LOINC) |
| section-code-text | composite | Search on section.code and section.text |
| entry | reference | Resources referenced by sections |
| related | reference | Related Composition |

## Constraints and Invariants

| Key | Severity | Description |
|-----|----------|-------------|
| dom-2 | error | If the resource is contained in another resource, it SHALL NOT contain nested Resources |
| dom-3 | error | If the resource is contained in another resource, it SHALL be referred to from elsewhere in the resource or SHALL refer to the containing resource |
| cmp-1 | error | A section must contain at least a text or entries or sub-sections |
| cmp-2 | error | A section can only have an emptyReason if it is empty |

## US Core Guidance

While US Core does not define a Composition profile, it provides guidance on clinical notes:
- Clinical notes SHOULD be represented using DocumentReference
- If representing as structured data, use Composition in a document Bundle
- DocumentReference and Composition are complementary, not mutually exclusive

## Implementation Considerations

### Version Management

- Each document version should have a unique `Composition.identifier`
- Use `relatesTo` to link to prior versions
- `Composition.status` tracks the lifecycle state
- Server-assigned `meta.versionId` is separate from logical document versioning

### Section Organization

- Sections should follow C-CDA template structure
- Required sections depend on the document type
- Use `section.emptyReason` for required empty sections
- Preserve nested sections from C-CDA

### Narrative Generation

- Each section SHOULD have narrative text
- Narrative can be generated from structured data or preserved from C-CDA
- Use `text.status = "generated"` for system-generated narrative
- Use `text.status = "additional"` for hand-authored content

### Reference Management

- All resources referenced by sections must be in the Bundle
- Use relative references within the Bundle ("ResourceType/id")
- Assign UUIDs to resources without stable identifiers
- Ensure no broken references

## Examples from Standards

### Example 1: Minimal Composition (from FHIR Specification)

```json
{
  "resourceType": "Composition",
  "id": "example-minimal",
  "status": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "11488-4",
        "display": "Consult note"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "date": "2018-10-30T16:56:04+11:00",
  "author": [
    {
      "reference": "Practitioner/example"
    }
  ],
  "title": "Consultation Note"
}
```

### Example 2: CCD Composition with Sections (from C-CDA on FHIR IG)

```json
{
  "resourceType": "Composition",
  "id": "CCDA-on-FHIR-CCD-Example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document"
    ]
  },
  "language": "en-US",
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:1c0ba2a1-4b15-4890-8d04-c187f8f6b1e7"
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
    "reference": "Patient/example",
    "display": "Amy V. Shaw"
  },
  "date": "2016-02-28T09:10:14Z",
  "author": [
    {
      "reference": "Practitioner/example",
      "display": "Ronald Bone, MD"
    }
  ],
  "title": "Continuity of Care Document (CCD)",
  "confidentiality": "N",
  "custodian": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "section": [
    {
      "title": "Allergies and Intolerances Section",
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
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td><b>Substance</b></td><td><b>Overall Severity</b></td><td><b>Reaction</b></td><td><b>Status</b></td></tr><tr><td>Penicillin G</td><td>Severe</td><td>Hives</td><td>Active</td></tr></table></div>"
      },
      "mode": "snapshot",
      "orderedBy": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/list-order",
            "code": "event-date",
            "display": "Sorted by Event Date"
          }
        ]
      },
      "entry": [
        {
          "reference": "AllergyIntolerance/example"
        }
      ]
    },
    {
      "title": "Medication Section",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "10160-0",
            "display": "History of Medication use Narrative"
          }
        ]
      },
      "text": {
        "status": "generated",
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td><b>Medication</b></td><td><b>Directions</b></td><td><b>Start Date</b></td><td><b>Status</b></td></tr><tr><td>Lisinopril 10mg</td><td>Take 1 tablet by mouth daily</td><td>2015-11-12</td><td>Active</td></tr></table></div>"
      },
      "mode": "snapshot",
      "orderedBy": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/list-order",
            "code": "event-date",
            "display": "Sorted by Event Date"
          }
        ]
      },
      "entry": [
        {
          "reference": "MedicationRequest/example"
        }
      ]
    }
  ]
}
```

## Modifier Elements

The following elements are modifier elements (affect interpretation):
- **status** - Changes interpretation of the composition's state
- **confidentiality** - Affects how the composition can be shared

## References

- FHIR R4 Composition: https://hl7.org/fhir/R4/composition.html
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- C-CDA on FHIR Composition Profiles: http://hl7.org/fhir/us/ccda/artifacts.html#structures-resource-profiles
- LOINC Document Ontology: https://loinc.org/document-ontology/
- HL7 CDA R2: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=7
- C-CDA R2.1 Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
