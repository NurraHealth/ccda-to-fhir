# FHIR R4: Bundle Resource

## Overview

The Bundle resource is a container for a collection of resources. In the context of C-CDA conversion, a Bundle with `type="document"` serves as the packaging mechanism that contains a Composition resource (representing the document structure and metadata) along with all resources referenced by that Composition. A FHIR document Bundle is the complete representation of a clinical document, equivalent to a C-CDA ClinicalDocument.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Bundle |
| FHIR Version | R4 (4.0.1) |
| Maturity Level | Normative (since 4.0.0) |
| Security Category | N/A |
| Responsible Work Group | FHIR Infrastructure |
| URL | https://hl7.org/fhir/R4/bundle.html |
| Document Specification | https://hl7.org/fhir/R4/documents.html |

## Scope and Usage

Bundles are used for multiple purposes in FHIR:

- **Documents**: Packaging clinical documents with Composition + all referenced resources
- **Messages**: Message-based exchanges
- **Search Results**: Returning sets of resources from a search
- **History**: Returning resource version history
- **Transactions/Batches**: Executing operations atomically or in batches
- **Collections**: Grouping resources for transport or persistence

### Document Bundles

For C-CDA conversion, we focus on **document Bundles** (`type="document"`), which:

- Package a complete clinical document as a single unit
- Have a Composition resource as the first entry
- Include all resources referenced (directly or indirectly) from the Composition
- Are immutable once assembled
- Can be digitally signed
- Can be managed and exchanged as a single unit

## JSON Structure

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f"
  },
  "timestamp": "2020-03-01T10:20:00-05:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f",
      "resource": {
        "resourceType": "Composition",
        "id": "composition-1",
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
        "identifier": [
          {
            "system": "urn:oid:2.16.840.1.113883.19.5.99999.2",
            "value": "998991"
          }
        ],
        "name": [
          {
            "given": ["Ellen"],
            "family": "Ross"
          }
        ],
        "gender": "female",
        "birthDate": "1975-05-01"
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-1234567890",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-1234567890",
        "identifier": [
          {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "1234567890"
          }
        ],
        "name": [
          {
            "given": ["Adam"],
            "family": "Careful",
            "suffix": ["MD"]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:org-1393",
      "resource": {
        "resourceType": "Organization",
        "id": "org-1393",
        "identifier": [
          {
            "system": "urn:oid:2.16.840.1.113883.19.5.9999.1393",
            "value": "1393"
          }
        ],
        "name": "Community Health and Hospitals"
      }
    },
    {
      "fullUrl": "urn:uuid:allergy-1",
      "resource": {
        "resourceType": "AllergyIntolerance",
        "id": "allergy-1",
        "patient": {
          "reference": "Patient/patient-998991"
        },
        "code": {
          "coding": [
            {
              "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
              "code": "7980",
              "display": "Penicillin G"
            }
          ]
        },
        "reaction": [
          {
            "manifestation": [
              {
                "coding": [
                  {
                    "system": "http://snomed.info/sct",
                    "code": "247472004",
                    "display": "Hives"
                  }
                ]
              }
            ]
          }
        ]
      }
    }
  ]
}
```

## Element Definitions

### type (1..1)

Indicates the purpose of the Bundle.

| Type | Description |
|------|-------------|
| code | Bundle type code |

**Value Set:** http://hl7.org/fhir/ValueSet/bundle-type (Required binding)

**Bundle Types:**

| Code | Display | Definition | Use in C-CDA Conversion |
|------|---------|------------|------------------------|
| document | Document | A document Bundle | **Primary use case** |
| message | Message | A message Bundle | Not used |
| transaction | Transaction | A transaction Bundle | Not used |
| transaction-response | Transaction Response | Response to transaction | Not used |
| batch | Batch | A batch Bundle | Not used |
| batch-response | Batch Response | Response to batch | Not used |
| history | History | A version history Bundle | Not used |
| searchset | Search Results | Search result set | Not used |
| collection | Collection | Generic collection | Not used |

**C-CDA Mapping:**
- All C-CDA documents map to `type="document"`
- This is a required field (1..1 cardinality)

### identifier (0..1)

Persistent identifier for the Bundle.

| Type | Description |
|------|-------------|
| Identifier | Unique Bundle identifier |

**Usage Notes:**
- **Required for document Bundles with both system and value** (constraint bdl-9)
- Maps from C-CDA `ClinicalDocument/id`
- Should be globally unique and never reused
- Typically matches `Composition.identifier`
- Use `urn:uuid:` format for UUIDs or `urn:oid:` for OID-based identifiers

**Document Identifier vs Composition Identifier:**

| Identifier | Location | Purpose | Persistence |
|------------|----------|---------|-------------|
| Document Identifier | `Bundle.identifier` | Identifies this specific document instance | Never changes, never reused |
| Composition Identifier | `Composition.identifier` | Identifies the composition content | May be consistent across derived documents |

**Example:**
```json
{
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f"
  }
}
```

### timestamp (0..1)

Date/time when the Bundle was assembled.

| Type | Description |
|------|-------------|
| instant | Bundle assembly timestamp |

**Usage Notes:**
- **Required for document Bundles** (constraint bdl-10)
- Maps from C-CDA `ClinicalDocument/effectiveTime`
- Represents when the document was assembled, not when it was authored
- Use ISO 8601 format: `YYYY-MM-DDThh:mm:ss+zz:zz`
- Typically matches `Composition.date` for C-CDA documents

**Timestamp vs Composition Date:**

| Timestamp | Purpose |
|-----------|---------|
| `Bundle.timestamp` | When the document Bundle was assembled |
| `Composition.date` | When the composition was authored/last modified |
| `Bundle.meta.lastUpdated` | When the bundle resource was last updated/persisted to storage |

For C-CDA conversions, these typically have the same value from `ClinicalDocument/effectiveTime`.

**Example:**
```json
{
  "timestamp": "2020-03-01T10:20:00-05:00"
}
```

### total (0..1)

Total number of matching resources (for search results).

| Type | Description |
|------|-------------|
| unsignedInt | Total matches |

**Usage Notes:**
- **NOT used for document Bundles**
- Only valid for `searchset` and `history` Bundle types
- Constraint bdl-1: "total only when a search or history"

### link (0..*)

Links related to this Bundle.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| relation | string | 1..1 | Link relation (self, first, next, last, etc.) |
| url | uri | 1..1 | Reference URL |

**Usage Notes:**
- Used for pagination in search results
- **Rarely used for document Bundles**
- C-CDA documents typically don't need link elements

### entry (0..*)

Resources contained in the Bundle.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| link | (Bundle.link) | 0..* | Links for this entry |
| fullUrl | uri | 0..1 | URI for resource (required for documents) |
| resource | Resource | 0..1 | The actual resource |
| search | BackboneElement | 0..1 | Search context (not for documents) |
| request | BackboneElement | 0..1 | Request details (transactions/batches) |
| response | BackboneElement | 0..1 | Response details (transaction/batch responses) |

**Document Bundle Entry Requirements:**

For document Bundles:
1. **First entry MUST be a Composition** (constraint bdl-11)
2. All subsequent entries are resources referenced by the Composition
3. Each entry MUST have a `fullUrl`
4. Each entry MUST have a `resource`
5. No `search`, `request`, or `response` elements (these are for other Bundle types)

#### entry.fullUrl

URI for the resource within the Bundle context.

| Type | Description |
|------|-------------|
| uri | Absolute URI or UUID |

**fullUrl Formats:**

| Format | Example | Use Case |
|--------|---------|----------|
| UUID URN | `urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f` | **Recommended for documents** |
| OID URN | `urn:oid:2.16.840.1.113883.19.5.99999.1` | When source has OID identifier |
| Absolute URL | `https://hospital.example.org/fhir/Patient/123` | When resource has canonical URL |

**Rules:**
- MUST be present for all entries in document Bundles
- MUST be an absolute URI (not relative)
- Cannot contain version-specific paths (no `/_history/`)
- SHALL NOT disagree with `resource.id`
- Used for reference resolution within the Bundle

**Reference Resolution:**

When a resource in the Bundle references another resource (e.g., `"reference": "Patient/patient-123"`), the reference is resolved by:

1. Looking for a Bundle entry where `fullUrl` ends with the reference value
2. If not found, attempting external resolution
3. For document Bundles, all references SHOULD resolve within the Bundle

**Example:**
```json
{
  "entry": [
    {
      "fullUrl": "urn:uuid:patient-123",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-123",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:condition-456",
      "resource": {
        "resourceType": "Condition",
        "id": "condition-456",
        "subject": {
          "reference": "Patient/patient-123"
        }
      }
    }
  ]
}
```

In this example, the Condition's reference to "Patient/patient-123" resolves to the first entry because the fullUrl contains "patient-123" as the id.

#### entry.resource

The actual FHIR resource.

| Type | Description |
|------|-------------|
| Resource | Any FHIR resource type |

**Document Bundle Resource Types:**

| Resource Type | Purpose | Location |
|---------------|---------|----------|
| Composition | Document structure and metadata | **First entry** |
| Patient | Subject of the document | Referenced by Composition.subject |
| Practitioner | Authors, attesters | Referenced by Composition.author, attester |
| Organization | Custodian, author organization | Referenced by Composition.custodian |
| Encounter | Clinical context | Referenced by Composition.encounter |
| AllergyIntolerance | Allergies section | Referenced by section.entry |
| Condition | Problems section | Referenced by section.entry |
| MedicationRequest | Medications section | Referenced by section.entry |
| Observation | Results, vitals, social history | Referenced by section.entry |
| Procedure | Procedures section | Referenced by section.entry |
| Immunization | Immunizations section | Referenced by section.entry |
| DiagnosticReport | Results section | Referenced by section.entry |
| Goal | Goals section | Referenced by section.entry |
| CarePlan | Plan of Treatment section | Referenced by section.entry |
| CareTeam | Care Team section | Referenced by section.entry |
| ServiceRequest | Planned procedures | Referenced by section.entry |
| Location | Service delivery locations | Referenced by Encounter.location |
| Binary | Stylesheet (optional) | Not referenced by Composition |
| Provenance | Audit trail (optional) | References Composition or other resources |

### signature (0..1)

Digital signature for the Bundle.

| Type | Description |
|------|-------------|
| Signature | Digital signature |

**Usage Notes:**
- Optional but recommended for clinical documents
- Provides integrity and authenticity
- SHOULD be provided by a listed attester in the Composition
- Maturity level: Trial Use (not Normative)

**Signature Structure:**

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| type | Coding[] | 1..* | Signature type/reason |
| when | instant | 1..1 | When signature was created |
| who | Reference(Practitioner\|Organization\|Patient\|Device) | 1..1 | Who signed |
| onBehalfOf | Reference(Practitioner\|Organization\|Patient\|Device) | 0..1 | Organization represented |
| targetFormat | code | 0..1 | Format of signed data |
| sigFormat | code | 0..1 | Format of signature |
| data | base64Binary | 0..1 | The actual signature |

**Example:**
```json
{
  "signature": {
    "type": [
      {
        "system": "urn:iso-astm:E1762-95:2013",
        "code": "1.2.840.10065.1.12.1.1",
        "display": "Author's Signature"
      }
    ],
    "when": "2020-03-01T10:20:00-05:00",
    "who": {
      "reference": "Practitioner/practitioner-1234567890"
    },
    "data": "dGhpcyBpcyBub3QgYSByZWFsIHNpZ25hdHVyZQ=="
  }
}
```

## Document Bundle Rules

### Mandatory Rules (FHIR Specification)

1. **Bundle.type** MUST be "document" (1..1)
2. **Bundle.identifier** MUST be present (constraint bdl-9)
3. **Bundle.timestamp** MUST be present (constraint bdl-10)
4. **First entry** MUST be a Composition resource (constraint bdl-11)
5. **All entries** MUST have `fullUrl`
6. **All entries** MUST have `resource`
7. **All referenced resources** MUST be included in the Bundle
8. **No broken references** - all references must resolve within the Bundle
9. **Document is immutable** - once assembled, content cannot change
10. **Document identifier never reused** - each document has unique identifier

### Resource Inclusion Rules

The Bundle SHALL include:

- The Composition resource (first entry)
- All resources directly referenced by Composition:
  - `subject` (typically Patient)
  - `encounter` (if present)
  - `author[]` (Practitioner/PractitionerRole/Organization)
  - `attester[].party` (if present)
  - `custodian` (Organization)
  - `relatesTo[].targetReference` (if using references instead of identifiers)
  - `event[].detail[]` (if present)
  - `section[].author[]` (if present)
  - `section[].focus` (if present)
  - `section[].entry[]` (all section entries)
- All resources indirectly referenced (e.g., referenced by section entries)
- Recursively, all resources referenced by included resources

The Bundle MAY include:

- Binary resource containing a stylesheet
- Provenance resources targeting the Composition or other included resources

The Bundle SHOULD NOT include:

- Resources not referenced by the Composition or included resources
- Duplicate resources (same resource should appear only once)

### Reference Resolution

References within the document Bundle:

- Use relative references: `"reference": "Patient/patient-123"`
- Resolution process:
  1. Look for entry with matching fullUrl (e.g., `"fullUrl": "urn:uuid:patient-123"`)
  2. If not found, look for entry where resource.id matches
  3. Should not need external resolution for document Bundles

**Best Practice:** Use consistent ID assignment:
```json
{
  "fullUrl": "urn:uuid:patient-123",
  "resource": {
    "resourceType": "Patient",
    "id": "patient-123",
    ...
  }
}
```

## Document Assembly Process

When converting a C-CDA document to a FHIR document Bundle:

1. **Create Bundle** with `type="document"`
2. **Set Bundle.identifier** from `ClinicalDocument/id`
3. **Set Bundle.timestamp** from `ClinicalDocument/effectiveTime`
4. **Create Composition** resource (first entry)
   - Map document header elements to Composition
   - Assign fullUrl (UUID or OID-based)
5. **Convert Patient** from `recordTarget/patientRole`
   - Create Patient resource
   - Assign fullUrl
   - Add to Bundle.entry[]
   - Reference from Composition.subject
6. **Convert document participants**:
   - Authors → Practitioner/PractitionerRole resources
   - Custodian → Organization resource
   - Authenticators → Practitioner resources
   - Add all to Bundle.entry[]
7. **Convert each section** in document body:
   - For each C-CDA entry in section:
     - Convert to appropriate FHIR resource
     - Assign fullUrl
     - Add to Bundle.entry[]
     - Add reference to Composition.section[].entry[]
8. **Recursively include referenced resources**:
   - If a section entry references other resources (e.g., Observation.performer), include those
   - Continue until all references are resolved
9. **Validate Bundle**:
   - Ensure all references resolve within Bundle
   - Verify Composition is first entry
   - Check for duplicate resources
   - Validate identifier and timestamp are present

## C-CDA on FHIR Document Bundles

### Profile Conformance

When creating document Bundles from C-CDA documents, the Composition should conform to the appropriate C-CDA on FHIR profile:

| C-CDA Document Type | C-CDA on FHIR Composition Profile |
|---------------------|----------------------------------|
| Continuity of Care Document (CCD) | http://hl7.org/fhir/us/ccda/StructureDefinition/Continuity-of-Care-Document |
| Consultation Note | http://hl7.org/fhir/us/ccda/StructureDefinition/Consultation-Note |
| Discharge Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/Discharge-Summary |
| Diagnostic Imaging Report | http://hl7.org/fhir/us/ccda/StructureDefinition/Diagnostic-Imaging-Report |
| History and Physical | http://hl7.org/fhir/us/ccda/StructureDefinition/History-and-Physical |
| Operative Note | http://hl7.org/fhir/us/ccda/StructureDefinition/Operative-Note |
| Procedure Note | http://hl7.org/fhir/us/ccda/StructureDefinition/Procedure-Note |
| Progress Note | http://hl7.org/fhir/us/ccda/StructureDefinition/Progress-Note |
| Referral Note | http://hl7.org/fhir/us/ccda/StructureDefinition/Referral-Note |
| Transfer Summary | http://hl7.org/fhir/us/ccda/StructureDefinition/Transfer-Summary |
| Care Plan | http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document |

### Bundle vs DocumentReference

When working with C-CDA documents, there are two FHIR approaches:

| Approach | Resource | Use Case | Result |
|----------|----------|----------|--------|
| **Structured Conversion** | Bundle (type="document") | Full conversion to FHIR resources | Bundle with Composition + all converted resources |
| **Document Indexing** | DocumentReference | Index/reference to source document | DocumentReference pointing to original C-CDA XML |

These approaches are complementary, not mutually exclusive. A system may:
1. Convert C-CDA to FHIR document Bundle for structured access
2. Create DocumentReference pointing to original C-CDA for reference
3. Maintain both representations

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| identifier | token | Persistent identifier for the bundle |
| composition | reference | The first resource in the bundle (for type=document) |
| message | reference | The first resource in the bundle (for type=message) |
| timestamp | date | When the bundle was assembled |
| type | token | document \| message \| transaction \| transaction-response \| batch \| batch-response \| history \| searchset \| collection |

## Constraints and Invariants

| Key | Severity | Expression | Description |
|-----|----------|------------|-------------|
| bdl-1 | error | total.empty() or (type = 'searchset') or (type = 'history') | total only when a search or history |
| bdl-2 | error | entry.search.empty() or (type = 'searchset') | entry.search only when a search |
| bdl-3 | error | entry.all(request.empty() or ((type = 'batch') or (type = 'transaction') or (type = 'history'))) | entry.request only for some types of bundles |
| bdl-4 | error | entry.all(response.empty() or ((type = 'batch-response') or (type = 'transaction-response'))) | entry.response only for some types of bundles |
| bdl-7 | error | entry.all(resource.empty() or request.empty() or request.method = 'POST' or request.method = 'PUT' or request.url.exists()) | FullUrl must be unique in a bundle, or else entries with the same fullUrl must have different meta.versionId (except for history) |
| bdl-9 | error | type = 'document' implies (identifier.system.exists() and identifier.value.exists()) | Document Bundles must have an identifier with both system and value |
| bdl-10 | error | type = 'document' implies (timestamp.exists()) | Document Bundles must have a timestamp |
| bdl-11 | error | type = 'document' implies (entry.first().resource.is(Composition)) | Document Bundles must start with a Composition |
| bdl-12 | error | type = 'message' implies (entry.first().resource.is(MessageHeader)) | Message Bundles must start with a MessageHeader |

## Implementation Considerations

### Immutability

Once a document Bundle is assembled:
- The Bundle content cannot be changed
- The Bundle.identifier can never be reused
- To create a new version, create a new Bundle with a new identifier
- Use Composition.relatesTo to link to prior versions

### Persistence and Exchange

Document Bundles can be:
- Stored as JSON files
- Stored as XML files
- Exchanged via RESTful APIs
- Signed using Bundle.signature
- Validated for conformance

### Performance Considerations

Document Bundles can be large:
- A typical CCD may contain 50-200 resources
- Bundle size can range from 100KB to several MB
- Consider compression for transmission
- Consider pagination or filtering for display

### Stylesheet Support

FHIR documents may include a Binary resource containing an XSLT stylesheet:
- Referenced from Composition via extension or link
- Used for rendering the document
- Must not alter clinical meaning of content
- Optional; narrative content should be sufficient without stylesheet

## Examples from Standards

### Example 1: Minimal Document Bundle (from FHIR Specification)

```json
{
  "resourceType": "Bundle",
  "id": "example-document",
  "type": "document",
  "identifier": {
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:a1b2c3d4-e5f6-7890-1234-567890abcdef"
  },
  "timestamp": "2018-10-30T16:56:04+11:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-1",
      "resource": {
        "resourceType": "Composition",
        "id": "composition-1",
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
          "reference": "Patient/patient-1"
        },
        "date": "2018-10-30T16:56:04+11:00",
        "author": [
          {
            "reference": "Practitioner/practitioner-1"
          }
        ],
        "title": "Consultation Note"
      }
    },
    {
      "fullUrl": "urn:uuid:patient-1",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-1",
        "name": [
          {
            "family": "Example"
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-1",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-1",
        "name": [
          {
            "family": "Doctor"
          }
        ]
      }
    }
  ]
}
```

### Example 2: CCD Document Bundle (from C-CDA on FHIR)

See the complete example in the JSON structure section above, which includes:
- Bundle with type="document"
- Composition as first entry with CCD profile
- Patient resource (subject)
- Practitioner resource (author)
- Organization resource (custodian)
- AllergyIntolerance resource (section entry)

## Relationship to Other Resources

### Bundle vs Composition

| Aspect | Bundle | Composition |
|--------|--------|-------------|
| Purpose | Container/packaging | Document structure/metadata |
| Location | Wrapper around all resources | First entry in Bundle |
| Type | Infrastructure resource | Clinical/administrative content |
| Required | For document exchange | For document structure |

### Bundle vs DocumentReference

| Aspect | Bundle | DocumentReference |
|--------|--------|------------------|
| Purpose | Contains the actual document | Indexes/references a document |
| Content | Full FHIR resources | Pointer to document + metadata |
| Size | Can be large (MB) | Small metadata resource |
| Access | Direct resource access | Requires document retrieval |

### Bundle vs List

| Aspect | Bundle | List |
|--------|--------|------|
| Purpose | Transport/persistence container | Dynamic enumeration |
| Membership | Fixed at assembly time | Can change over time |
| Immutability | Immutable (documents) | Mutable |
| References | All resources included | References external resources |

## Validation Checklist

When validating a document Bundle:

- [ ] `type` = "document"
- [ ] `identifier` is present with system and value
- [ ] `timestamp` is present
- [ ] First entry is a Composition resource
- [ ] All entries have `fullUrl`
- [ ] All entries have `resource`
- [ ] No entries have `search`, `request`, or `response` elements
- [ ] All resources referenced by Composition are present in Bundle
- [ ] All resources referenced by other resources are present in Bundle
- [ ] No broken references (all resolve within Bundle)
- [ ] No duplicate resources (same resource.id)
- [ ] Patient resource is present (referenced by Composition.subject)
- [ ] fullUrl values are unique (or have different meta.versionId)
- [ ] fullUrl values are absolute URIs
- [ ] resource.id matches the id in fullUrl (if fullUrl uses id-based format)

## References

- FHIR R4 Bundle: https://hl7.org/fhir/R4/bundle.html
- FHIR R4 Documents: https://hl7.org/fhir/R4/documents.html
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- FHIR Document Bundles: https://hl7.org/fhir/R4/bundle.html#document
- Bundle Profiles: https://hl7.org/fhir/R4/bundle-profiles.html
- Digital Signatures: https://hl7.org/fhir/R4/signatures.html
