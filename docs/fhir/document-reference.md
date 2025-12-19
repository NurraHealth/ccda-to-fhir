# FHIR R4: DocumentReference Resource

## Overview

The DocumentReference resource provides metadata about a document to make it discoverable and manageable within a healthcare system. Unlike the Composition resource which represents the structure and content of a document, DocumentReference is an index entry that points to a document. It's used for document management and discovery across health information exchanges.

In the context of C-CDA conversion, DocumentReference serves to index the entire C-CDA document, making it searchable and accessible without requiring full conversion to FHIR resources.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | DocumentReference |
| FHIR Version | R4 (4.0.1) |
| Maturity Level | 3 (Trial Use) |
| Security Category | Patient |
| Responsible Work Group | Structured Documents |
| URL | https://hl7.org/fhir/R4/documentreference.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference |

## Scope and Usage

The DocumentReference resource is used for indexing and managing documents:

- **Document Discovery**: Enables searching for documents by type, date, patient, etc.
- **Document Access**: Provides URLs or binary data for retrieving documents
- **Metadata Index**: Captures document metadata without requiring full content transformation
- **Clinical Notes**: Primary use case in US Core for clinical notes and C-CDA documents
- **Document Management**: Tracks document status, relationships, and provenance

### DocumentReference vs Composition

| Aspect | DocumentReference | Composition |
|--------|-------------------|-------------|
| Purpose | Index/metadata for documents | Structure and content of documents |
| Usage | Points to a document | Is part of the document |
| Location | Separate resource | First entry in document Bundle |
| Content | URL or binary data of document | Section structure with references |
| Conversion | Minimal - metadata only | Full - all C-CDA content to FHIR |
| Size | Small (~1-5KB) | Large (100KB-2MB for full document Bundle) |

**Use DocumentReference when:**
- You need to index C-CDA documents for discovery
- Original C-CDA format must be preserved
- Full conversion to FHIR resources is not needed
- Building a document management system

**Use Composition when:**
- You need structured FHIR resource access
- Applications require querying specific clinical data
- C-CDA on FHIR compliance is required

## JSON Structure

```json
{
  "resourceType": "DocumentReference",
  "id": "example-ccda",
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
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "date": "2020-03-01T10:20:00-05:00",
  "author": [
    {
      "reference": "Practitioner/example",
      "display": "Dr. Adam Careful"
    }
  ],
  "authenticator": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "custodian": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "reference": "DocumentReference/prior-version"
      }
    }
  ],
  "description": "Continuity of Care Document for Ellen Ross",
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
        "url": "https://example.org/fhir/Binary/ccda-example",
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
    "encounter": [
      {
        "reference": "Encounter/example"
      }
    ],
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
    "facilityType": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "225732001",
          "display": "Primary care clinic"
        }
      ]
    },
    "practiceSetting": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "394802001",
          "display": "General medicine"
        }
      ]
    }
  }
}
```

## Element Definitions

### masterIdentifier (0..1)

Version-independent identifier for the document.

| Type | Description |
|------|-------------|
| Identifier | Document series identifier (setId in C-CDA) |

**Usage Notes:**
- Maps from C-CDA `ClinicalDocument/setId` (document series ID)
- Remains constant across document versions
- Different from `identifier` which is version-specific

**Example:**
```json
{
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988"
  }
}
```

### identifier (0..*)

Version-specific identifier(s) for the document.

| Type | Description |
|------|-------------|
| Identifier | Document instance identifier |

**Usage Notes:**
- Maps from C-CDA `ClinicalDocument/id` (document instance ID)
- Unique to this specific version
- US Core requires at least one identifier

**Example:**
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

### status (1..1)

The status of the DocumentReference. **Modifier element**.

| Type | Values |
|------|--------|
| code | current \| superseded \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/document-reference-status (Required binding)

**Status Definitions:**

| Code | Display | Definition |
|------|---------|------------|
| current | Current | This is the current reference for this document. |
| superseded | Superseded | This reference has been superseded by another reference. |
| entered-in-error | Entered in Error | This reference was created in error. |

**C-CDA Mapping:**
- Most C-CDA documents → `current`
- Replaced by another document (relatedDocument typeCode='RPLC') → `superseded`
- Erroneous document → `entered-in-error`

### docStatus (0..1)

The status of the underlying document.

| Type | Values |
|------|--------|
| code | preliminary \| final \| amended \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/composition-status (Required binding)

**Usage Notes:**
- Represents the clinical status of the document content
- Different from `status` which is about the reference
- Maps from C-CDA document status indicators

### type (1..1)

The kind of document (e.g., Discharge Summary, Progress Note).

| Type | Description |
|------|-------------|
| CodeableConcept | Document type (LOINC) |

**Value Set:** http://hl7.org/fhir/us/core/ValueSet/us-core-documentreference-type (Required binding for US Core)

**US Core Requirement:**
- SHALL use LOINC codes where SCALE="Doc"
- Common codes: 34133-9 (CCD), 18842-5 (Discharge Summary), etc.

**C-CDA Mapping:**
- Maps directly from `ClinicalDocument/code`

**Example:**
```json
{
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "34133-9",
        "display": "Summarization of Episode Note"
      }
    ]
  }
}
```

### category (0..*)

Categorization of the document.

| Type | Description |
|------|-------------|
| CodeableConcept | Document category |

**Value Set:** http://hl7.org/fhir/us/core/ValueSet/us-core-documentreference-category (Required binding for US Core - USCDI)

**US Core Requirement:**
- SHALL include at least one category
- Currently limited to `clinical-note` for clinical documents

**Example:**
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

### subject (0..1)

Who/what is the subject of the document.

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| Group \| Device) | Subject of document |

**US Core Requirement:**
- SHALL reference a Patient resource
- Required for patient-centric documents (all C-CDA documents)

**C-CDA Mapping:**
- Maps from `ClinicalDocument/recordTarget/patientRole`
- Create or reference Patient resource

### date (0..1)

When the document reference was created.

| Type | Description |
|------|-------------|
| instant | Creation timestamp |

**US Core:** Must Support element

**C-CDA Mapping:**
- Maps from `ClinicalDocument/effectiveTime`
- Represents when the document was authored/created

**Example:**
```json
{
  "date": "2020-03-01T10:20:00-05:00"
}
```

### author (0..*)

Who authored the document.

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| Device \| Patient \| RelatedPerson) | Document author |

**US Core:** Must Support element

**C-CDA Mapping:**
- Maps from `ClinicalDocument/author/assignedAuthor`
- May reference Practitioner, PractitionerRole, or Organization

**Example:**
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

### authenticator (0..1)

Who/what authenticated the document.

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization) | Authenticator |

**C-CDA Mapping:**
- Maps from `ClinicalDocument/legalAuthenticator`
- Person who legally authenticated the document

### custodian (0..1)

Organization maintaining the document.

| Type | Description |
|------|-------------|
| Reference(Organization) | Custodian organization |

**C-CDA Mapping:**
- Maps from `ClinicalDocument/custodian/representedCustodianOrganization`

### relatesTo (0..*)

Relationships to other documents.

| Type | Description |
|------|-------------|
| BackboneElement | Relationship to another document |

**Elements:**
- `code` (1..1): replaces \| transforms \| signs \| appends
- `target` (1..1): Reference(DocumentReference) or Identifier

**C-CDA Mapping:**
- Maps from `ClinicalDocument/relatedDocument`

| C-CDA typeCode | FHIR code | Description |
|----------------|-----------|-------------|
| RPLC | replaces | This document replaces the target |
| APND | appends | This document appends to the target |
| XFRM | transforms | This document transforms the target |

**Example:**
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

### description (0..1)

Human-readable description of the document.

| Type | Description |
|------|-------------|
| string | Document description |

**C-CDA Mapping:**
- May use `ClinicalDocument/title`
- Or construct from type and patient name

### securityLabel (0..*)

Document security classification.

| Type | Description |
|------|-------------|
| CodeableConcept | Security label |

**Value Set:** http://hl7.org/fhir/ValueSet/security-labels (Extensible binding)

**C-CDA Mapping:**
- Maps from `ClinicalDocument/confidentialityCode`

**Example:**
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

### content (1..*)

Document content. **This is the actual document.**

| Type | Description |
|------|-------------|
| BackboneElement | Document content |

**Elements:**
- `attachment` (1..1): The actual document
- `format` (0..1): Format code beyond MIME type

#### content.attachment (1..1)

The document data or URL.

| Element | Type | Description |
|---------|------|-------------|
| contentType | code | MIME type (required) |
| language | code | Human language (e.g., en-US) |
| data | base64Binary | Base64-encoded document |
| url | url | URL to retrieve document |
| size | unsignedInt | Size in bytes |
| hash | base64Binary | SHA-1 hash of data |
| title | string | Document title |
| creation | dateTime | When document was created |

**US Core Requirement:**
- `attachment.url` OR `attachment.data` (or both) SHALL be present
- `contentType` is required

**C-CDA Document Options:**

**Option 1: URL Reference**
```json
{
  "attachment": {
    "contentType": "application/xml",
    "language": "en-US",
    "url": "https://example.org/fhir/Binary/ccda-example",
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

**MIME Types for C-CDA:**
- `application/xml` - Standard XML
- `text/xml` - Also acceptable
- `application/cda+xml` - CDA-specific (less common)

#### content.format (0..1)

Format code providing more detail than MIME type.

| Type | Description |
|------|-------------|
| Coding | Format code |

**Value Set:** http://hl7.org/fhir/ValueSet/formatcodes (Extensible binding)

**US Core:** Must Support element

**C-CDA Format Codes:**

| Code | Display | Use |
|------|---------|-----|
| urn:hl7-org:sdwg:ccda-structuredBody:1.1 | C-CDA R1.1 Structured Body | C-CDA R1.1 documents |
| urn:hl7-org:sdwg:ccda-structuredBody:2.1 | C-CDA R2.1 Structured Body | C-CDA R2.1 documents |
| urn:hl7-org:sdwg:ccda-structuredBody:3.0 | C-CDA R3.0 Structured Body | C-CDA R3.0 documents |
| urn:hl7-org:sdwg:ccda-structuredBody:4.0 | C-CDA R4.0 Structured Body | C-CDA R4.0 documents |
| urn:hl7-org:sdwg:ccda-nonXMLBody:1.1 | C-CDA R1.1 Non-XML Body | C-CDA R1.1 unstructured |
| urn:hl7-org:sdwg:ccda-nonXMLBody:2.1 | C-CDA R2.1 Non-XML Body | C-CDA R2.1 unstructured |
| urn:hl7-org:sdwg:ccda-nonXMLBody:3.0 | C-CDA R3.0 Non-XML Body | C-CDA R3.0 unstructured |
| urn:hl7-org:sdwg:ccda-nonXMLBody:4.0 | C-CDA R4.0 Non-XML Body | C-CDA R4.0 unstructured |

**System:** `http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes`

**Example:**
```json
{
  "format": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
    "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
    "display": "C-CDA R2.1 Structured Body"
  }
}
```

### context (0..1)

Clinical context of document.

| Type | Description |
|------|-------------|
| BackboneElement | Context metadata |

**Elements:**
- `encounter` (0..*): Related encounter
- `event` (0..*): Event codes
- `period` (0..1): Time period covered
- `facilityType` (0..1): Kind of facility
- `practiceSetting` (0..1): Practice specialty
- `sourcePatientInfo` (0..1): Patient demographics snapshot
- `related` (0..*): Related resources

#### context.encounter (0..*)

Encounter(s) during which the document was created.

| Type | Description |
|------|-------------|
| Reference(Encounter \| EpisodeOfCare) | Related encounter |

**US Core:** Must Support element

**C-CDA Mapping:**
- Maps from `ClinicalDocument/componentOf/encompassingEncounter`

#### context.event (0..*)

Event codes describing the main activity being documented.

| Type | Description |
|------|-------------|
| CodeableConcept | Event code |

**C-CDA Mapping:**
- Maps from `ClinicalDocument/documentationOf/serviceEvent/@classCode`

**Example:**
```json
{
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
```

#### context.period (0..1)

Time period covered by the documentation.

| Type | Description |
|------|-------------|
| Period | Service time range |

**US Core:** Must Support element

**C-CDA Mapping:**
- Maps from `ClinicalDocument/documentationOf/serviceEvent/effectiveTime`

**Example:**
```json
{
  "period": {
    "start": "2020-01-01",
    "end": "2020-03-01"
  }
}
```

#### context.facilityType (0..1)

Kind of facility where the document was created.

| Type | Description |
|------|-------------|
| CodeableConcept | Facility type |

**Value Set:** http://hl7.org/fhir/ValueSet/c80-facilitycodes (Example binding)

**Example:**
```json
{
  "facilityType": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "225732001",
        "display": "Primary care clinic"
      }
    ]
  }
}
```

#### context.practiceSetting (0..1)

Practice specialty associated with the document.

| Type | Description |
|------|-------------|
| CodeableConcept | Practice setting |

**Value Set:** http://hl7.org/fhir/ValueSet/c80-practice-codes (Example binding)

**C-CDA Mapping:**
- May infer from `ClinicalDocument/author/assignedAuthor/code` (provider specialty)

**Example:**
```json
{
  "practiceSetting": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "394802001",
        "display": "General medicine"
      }
    ]
  }
}
```

## US Core DocumentReference Profile Requirements

### Mandatory Elements (Must Always Be Present)

1. **status** - current | superseded | entered-in-error
2. **type** - LOINC document type code
3. **category** - Document category (clinical-note for clinical documents)
4. **subject** - Reference to Patient
5. **content** - The document
6. **content.attachment.contentType** - MIME type
7. **content.attachment.url OR data** - How to access the document

### Must Support Elements (If Present, Must Be Supported)

- identifier
- date
- author
- content.format
- context.encounter
- context.period

### Required Search Parameters

Systems **SHALL** support:

1. `_id` - Fetch DocumentReference by logical ID
2. `patient` - All documents for a patient
3. `patient` + `category` - Filter by category
4. `patient` + `category` + `date` - With date comparators (gt, lt, ge, le)
5. `patient` + `type` - Filter by document type

### Optional Search Parameters (SHOULD Support)

- `patient` + `status`
- `patient` + `type` + `period`

### Write Capability (OPTIONAL)

**Important:** US Core does **NOT** require POST/create operations for DocumentReference. Per the US Core Clinical Notes guidance:

> "Note that this guide focuses on exposing existing information, not how systems allow users to capture data."

Systems **MAY** support writing new clinical notes via `POST [base]/DocumentReference`, but this is not a US Core requirement. US Core focuses exclusively on reading and querying existing documents.

### $docref Operation (REQUIRED)

**US Core Requirement:** Systems **SHALL** support the `$docref` operation for generating document references based on specified parameters.

**Syntax:**
- GET: `GET [base]/DocumentReference/$docref?patient=[id]&type=[type]&start=[date]&end=[date]`
- POST: `POST [base]/DocumentReference/$docref` with Parameters resource

**Required parameters:**
- Patient identification (required)

**Optional parameters:**
- Type (document type code)
- Start/end dates (date range)
- On-demand parameter (generate document on demand vs return existing references)

This operation enables document generation/retrieval based on query parameters rather than requiring pre-existing DocumentReference resources.

## Examples

### Example 1: C-CDA Document Reference with URL

```json
{
  "resourceType": "DocumentReference",
  "id": "ccda-ccd-example",
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
      "display": "Dr. Adam Careful"
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
    "encounter": [
      {
        "reference": "Encounter/encounter-9937012"
      }
    ],
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
    "facilityType": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "225732001",
          "display": "Primary care clinic"
        }
      ]
    },
    "practiceSetting": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "394802001",
          "display": "General medicine"
        }
      ]
    }
  }
}
```

### Example 2: Embedded C-CDA Document

```json
{
  "resourceType": "DocumentReference",
  "id": "ccda-discharge-summary",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference"
    ]
  },
  "identifier": [
    {
      "system": "urn:oid:1.2.840.114350.1.13.12345.1.7.2.123456",
      "value": "DOC001"
    }
  ],
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "18842-5",
        "display": "Discharge Summary"
      }
    ]
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
    "reference": "Patient/patient-123"
  },
  "date": "2020-03-15T14:30:00-05:00",
  "author": [
    {
      "reference": "Practitioner/practitioner-1"
    }
  ],
  "custodian": {
    "reference": "Organization/org-1"
  },
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "language": "en-US",
        "data": "PENsaW5pY2FsRG9jdW1lbnQgeG1sbnM9InVybjpobDctb3JnOnYzIj4uLi48L0NsaW5pY2FsRG9jdW1lbnQ+",
        "title": "Discharge Summary",
        "creation": "2020-03-15T14:30:00-05:00"
      },
      "format": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
        "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
        "display": "C-CDA R2.1 Structured Body"
      }
    }
  ]
}
```

## Implementation Considerations

### Document Storage Options

**Option 1: Binary Resource**
Store C-CDA XML in a Binary resource and reference via URL:
```json
{
  "attachment": {
    "contentType": "application/xml",
    "url": "Binary/ccda-document-123"
  }
}
```

**Option 2: External URL**
Store C-CDA externally and provide HTTPS URL:
```json
{
  "attachment": {
    "contentType": "application/xml",
    "url": "https://docs.example.org/ccda/document-123.xml"
  }
}
```

**Option 3: Embedded Data**
Embed base64-encoded C-CDA in attachment.data:
```json
{
  "attachment": {
    "contentType": "application/xml",
    "data": "PENsaW5pY2FsRG9jdW1lbnQ+Li4uPC9DbGluaWNhbERvY3VtZW50Pg=="
  }
}
```

**Recommendation:** Use Binary resources for FHIR-native storage, external URLs for existing document repositories.

### Hash Calculation

The `attachment.hash` should be a SHA-1 hash of the document data:

```python
import hashlib
import base64

# Calculate SHA-1 hash
sha1_hash = hashlib.sha1(document_bytes).digest()

# Base64 encode
hash_base64 = base64.b64encode(sha1_hash).decode('utf-8')
```

### Document Relationships

Use `relatesTo` to track document versions and relationships:

**Replacement:**
```json
{
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "reference": "DocumentReference/prior-version"
      }
    }
  ]
}
```

When a document is replaced:
1. Create new DocumentReference with status="current"
2. Add relatesTo.code="replaces" pointing to old document
3. Update old DocumentReference status to "superseded"

### Security and Privacy

**Confidentiality:**
Always map C-CDA `confidentialityCode` to `securityLabel`:
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

**Access Control:**
- Enforce patient consent rules
- Respect document confidentiality
- Audit document access

## Related Documentation

- **FHIR Composition Resource**: [composition.md](composition.md)
- **FHIR Bundle Resource**: [bundle.md](bundle.md)
- **C-CDA Clinical Document**: [/docs/ccda/clinical-document.md](/docs/ccda/clinical-document.md)
- **DocumentReference Mapping**: [/docs/mapping/26-document-reference.md](/docs/mapping/26-document-reference.md)

## References

- FHIR R4 DocumentReference: https://hl7.org/fhir/R4/documentreference.html
- US Core DocumentReference Profile: https://www.hl7.org/fhir/us/core/StructureDefinition-us-core-documentreference.html
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- HL7 Document Format Codes: http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes
- LOINC Document Ontology: https://loinc.org/document-ontology/
