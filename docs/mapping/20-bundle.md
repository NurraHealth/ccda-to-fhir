# Mapping: C-CDA ClinicalDocument to FHIR Bundle (Document Packaging)

## Overview

This document specifies the mapping from a C-CDA ClinicalDocument to a FHIR document Bundle (type="document"). While the ClinicalDocument header maps to the Composition resource (covered in [19-composition.md](19-composition.md)), the overall document packaging maps to the Bundle resource. The Bundle serves as the container that packages the Composition along with all referenced resources into a single, immutable document unit.

## Context and Relationships

### Bundle vs Composition

When converting C-CDA to FHIR, the ClinicalDocument maps to two FHIR resources:

| Aspect | Bundle | Composition |
|--------|--------|-------------|
| **Purpose** | Container/packaging for entire document | Document structure and metadata |
| **Maps from** | ClinicalDocument (entire document) | ClinicalDocument header elements |
| **Location** | Wrapper around all resources | First entry in Bundle |
| **Type** | Infrastructure/transport resource | Clinical/administrative content |
| **Contains** | All document resources | Section structure with references |
| **Immutability** | Immutable once assembled | Immutable (part of document) |

**Key Principle:** `ClinicalDocument` → `Bundle` (container) + `Composition` (first entry)

### Document Bundle Structure

A FHIR document Bundle contains:

```
Bundle (type="document")
├── identifier (from ClinicalDocument/id)
├── timestamp (from ClinicalDocument/effectiveTime)
└── entry[]
    ├── [0] Composition (REQUIRED - first entry)
    ├── [1] Patient (subject of document)
    ├── [2..n] Practitioner/Organization resources (authors, custodian, etc.)
    └── [n+1..] Clinical resources (section entries: Condition, AllergyIntolerance, etc.)
```

## Standards References

| Standard | Reference |
|----------|-----------|
| **FHIR R4 Bundle** | https://hl7.org/fhir/R4/bundle.html |
| **FHIR R4 Documents** | https://hl7.org/fhir/R4/documents.html |
| **C-CDA R2.1** | US Realm Header + Document Type Templates |
| **C-CDA on FHIR IG** | http://hl7.org/fhir/us/ccda/ |

## Element-by-Element Mapping

### Bundle.resourceType

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (implicit) | `Bundle.resourceType` | 1..1 | Always "Bundle" |

**Example:**
```json
{
  "resourceType": "Bundle"
}
```

### Bundle.type

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (implicit) | `Bundle.type` | 1..1 | Always "document" for C-CDA conversions |

**Mapping Logic:**
- All C-CDA documents map to `type="document"`
- This indicates the Bundle is a clinical document
- Required field (1..1 cardinality)

**Example:**
```json
{
  "type": "document"
}
```

### Bundle.identifier

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/id/@root` | `Bundle.identifier.system` | 1..1 | Convert OID to URI |
| `ClinicalDocument/id/@extension` | `Bundle.identifier.value` | 1..1 | Required for document bundles (bdl-9); use root as value if no extension |

**OID to URI Conversion:**
- If `@root` is a UUID format: use `urn:uuid:{root}`
- If `@root` is an OID: use `urn:oid:{root}`
- No `@extension`: use `urn:ietf:rfc:3986` as system and full UUID/OID URN as value

**Required:** Document Bundles MUST have an identifier with both system and value (constraint bdl-9)

**Relationship to Composition.identifier:**
- `Bundle.identifier` SHOULD match `Composition.identifier`
- Both typically come from `ClinicalDocument/id`
- Represents the unique document instance identifier

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

### Bundle.timestamp

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| `ClinicalDocument/effectiveTime/@value` | `Bundle.timestamp` | 1..1 | Document assembly time |

**Timestamp Conversion:**
- C-CDA format: `YYYYMMDDHHmmss±ZZZZ`
- FHIR format: `YYYY-MM-DDThh:mm:ss±hh:mm`
- Preserve precision from C-CDA
- Timezone required if time component present

**Required:** Document Bundles MUST have a timestamp (constraint bdl-10)

**Relationship to Other Dates:**

| Timestamp | Purpose | Source |
|-----------|---------|--------|
| `Bundle.timestamp` | When Bundle was assembled | `ClinicalDocument/effectiveTime` |
| `Composition.date` | When composition was authored | `ClinicalDocument/effectiveTime` (same) |
| `Bundle.meta.lastUpdated` | When bundle resource was last updated/persisted to storage | System-assigned (optional) |

For C-CDA conversions, `Bundle.timestamp` and `Composition.date` typically have the same value.

**Example:**

C-CDA:
```xml
<ClinicalDocument>
  <effectiveTime value="20200301102000-0500"/>
</ClinicalDocument>
```

FHIR:
```json
{
  "timestamp": "2020-03-01T10:20:00-05:00"
}
```

### Bundle.entry[]

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (entire document) | `Bundle.entry[]` | 1..* | All document resources |

**Entry Order and Requirements:**

1. **First entry (REQUIRED):** Composition resource
   - Constraint bdl-11: Document Bundles must start with a Composition
   - See [19-composition.md](19-composition.md) for Composition mapping
2. **Subsequent entries:** All resources referenced by Composition
   - Patient (from `recordTarget`)
   - Practitioners (from `author`, `legalAuthenticator`, etc.)
   - Organizations (from `custodian`)
   - Clinical resources (from section entries)
   - Supporting resources (referenced by clinical resources)

**Entry Structure:**

Each entry contains:
- `fullUrl` (required) - Absolute URI for the resource
- `resource` (required) - The actual FHIR resource

**Example:**
```json
{
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-1",
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
    }
  ]
}
```

#### entry.fullUrl

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (generated) | `entry.fullUrl` | 1..1 | Absolute URI for resource |

**fullUrl Assignment Strategy:**

For C-CDA conversions, use **UUID-based URNs** (recommended):

| Resource | fullUrl Format | Example |
|----------|----------------|---------|
| Composition | `urn:uuid:{document-id}` | `urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f` |
| Patient | `urn:uuid:{generated-uuid}` | `urn:uuid:patient-998991` |
| Other resources | `urn:uuid:{generated-uuid}` | `urn:uuid:allergy-1` |

**Alternative: OID-based URNs** (when C-CDA uses OIDs):

```json
{
  "fullUrl": "urn:oid:2.16.840.1.113883.19.5.99999.2"
}
```

**Alternative: Absolute URLs** (when resources have canonical URLs):

```json
{
  "fullUrl": "https://hospital.example.org/fhir/Patient/patient-123"
}
```

**Rules:**
- MUST be present for all entries (required for document Bundles)
- MUST be an absolute URI
- MUST be unique within the Bundle (or have different meta.versionId)
- SHALL NOT disagree with `resource.id`
- Used for reference resolution within Bundle

**ID Consistency:**

The `resource.id` should match the identifier in `fullUrl`:

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

**Reference Resolution:**

When resources reference each other within the Bundle, references are resolved by matching the fullUrl:

```json
{
  "entry": [
    {
      "fullUrl": "urn:uuid:patient-123",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-123"
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

The reference "Patient/patient-123" resolves to the first entry because its fullUrl contains "patient-123".

#### entry.resource

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (varies) | `entry.resource` | 1..1 | The actual FHIR resource |

**Resource Mapping:**

| C-CDA Element | FHIR Resource | Mapping Document |
|---------------|---------------|------------------|
| ClinicalDocument header | Composition | [19-composition.md](19-composition.md) |
| recordTarget/patientRole | Patient | [01-patient.md](01-patient.md) |
| author/assignedAuthor | Practitioner/PractitionerRole | [09-participations.md](09-participations.md) |
| custodian | Organization | [09-participations.md](09-participations.md) |
| componentOf/encompassingEncounter | Encounter | [08-encounter.md](08-encounter.md) |
| section/entry (Allergy) | AllergyIntolerance | [03-allergy-intolerance.md](03-allergy-intolerance.md) |
| section/entry (Problem) | Condition | [02-condition.md](02-condition.md) |
| section/entry (Medication) | MedicationRequest | [07-medication-request.md](07-medication-request.md) |
| section/entry (Procedure) | Procedure | [05-procedure.md](05-procedure.md) |
| section/entry (Immunization) | Immunization | [06-immunization.md](06-immunization.md) |
| section/entry (Result) | Observation | [04-observation.md](04-observation.md) |
| section/entry (Goal) | Goal | [13-goal.md](13-goal.md) |
| section/entry (Care Plan) | CarePlan | [14-careplan.md](14-careplan.md) |
| section/entry (Care Team) | CareTeam | [17-careteam.md](17-careteam.md) |
| section/entry (Service Request) | ServiceRequest | [18-service-request.md](18-service-request.md) |
| documentationOf/serviceEvent/performer | Practitioner | [09-participations.md](09-participations.md) |
| author/representedOrganization | Organization | [09-participations.md](09-participations.md) |
| serviceDeliveryLocation | Location | [16-location.md](16-location.md) |

### Bundle.signature (optional)

| C-CDA Element | FHIR Element | Cardinality | Notes |
|---------------|--------------|-------------|-------|
| (generated) | `Bundle.signature` | 0..1 | Digital signature for document |

**Usage Notes:**
- Optional but recommended for clinical documents
- Provides document integrity and authenticity
- Should reference a listed attester in Composition
- C-CDA documents may have signatures at the ClinicalDocument level
- FHIR R4 signature is Trial Use maturity

**Signature Mapping:**

If C-CDA document has `legalAuthenticator/signatureCode/@code="S"`, consider creating a Bundle.signature:

C-CDA:
```xml
<legalAuthenticator>
  <time value="20200301"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  </assignedEntity>
</legalAuthenticator>
```

FHIR:
```json
{
  "signature": {
    "type": [
      {
        "system": "urn:iso-astm:E1762-95:2013",
        "code": "1.2.840.10065.1.12.1.5",
        "display": "Verification Signature"
      }
    ],
    "when": "2020-03-01T00:00:00-05:00",
    "who": {
      "reference": "Practitioner/practitioner-1234567890"
    }
  }
}
```

## Document Assembly Process

### Step-by-Step Assembly

When converting a C-CDA document to a FHIR document Bundle:

#### 1. Initialize Bundle

```json
{
  "resourceType": "Bundle",
  "type": "document"
}
```

#### 2. Set Bundle Metadata

From `ClinicalDocument`:

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:oid:{ClinicalDocument/id/@root}",
    "value": "{ClinicalDocument/id/@extension}"
  },
  "timestamp": "{ClinicalDocument/effectiveTime converted to ISO 8601}"
}
```

#### 3. Create Composition Resource

- Map ClinicalDocument header to Composition
- See [19-composition.md](19-composition.md) for detailed mapping
- Assign fullUrl (typically matches Bundle.identifier)
- Add as first entry

```json
{
  "entry": [
    {
      "fullUrl": "urn:uuid:{document-id}",
      "resource": {
        "resourceType": "Composition",
        ...
      }
    }
  ]
}
```

#### 4. Convert and Add Patient Resource

- Map `recordTarget/patientRole` to Patient
- See [01-patient.md](01-patient.md)
- Assign fullUrl
- Add to Bundle.entry[]
- Reference from Composition.subject

```json
{
  "entry": [
    ...,
    {
      "fullUrl": "urn:uuid:patient-{id}",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-{id}",
        ...
      }
    }
  ]
}
```

Update Composition:
```json
{
  "subject": {
    "reference": "Patient/patient-{id}"
  }
}
```

#### 5. Convert and Add Participant Resources

For each participant (authors, custodian, authenticators):

- Map to Practitioner, PractitionerRole, or Organization
- See [09-participations.md](09-participations.md)
- Assign fullUrl
- Add to Bundle.entry[]
- Reference from Composition (author, custodian, attester)

```json
{
  "entry": [
    ...,
    {
      "fullUrl": "urn:uuid:practitioner-{npi}",
      "resource": {
        "resourceType": "Practitioner",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:org-{id}",
      "resource": {
        "resourceType": "Organization",
        ...
      }
    }
  ]
}
```

#### 6. Convert Encounter (if present)

If `componentOf/encompassingEncounter` exists:

- Map to Encounter resource
- See [08-encounter.md](08-encounter.md)
- Assign fullUrl
- Add to Bundle.entry[]
- Reference from Composition.encounter

#### 7. Convert Section Entries

For each `section` in `component/structuredBody`:

For each `entry` in section:
- Determine FHIR resource type based on C-CDA template
- Convert C-CDA entry to FHIR resource
- Assign fullUrl
- Add to Bundle.entry[]
- Add reference to Composition.section[].entry[]

Example for Allergy section:
```json
{
  "entry": [
    ...,
    {
      "fullUrl": "urn:uuid:allergy-1",
      "resource": {
        "resourceType": "AllergyIntolerance",
        "id": "allergy-1",
        "patient": {
          "reference": "Patient/patient-{id}"
        },
        ...
      }
    }
  ]
}
```

Update Composition section:
```json
{
  "section": [
    {
      "title": "Allergies and Intolerances",
      "code": {...},
      "entry": [
        {
          "reference": "AllergyIntolerance/allergy-1"
        }
      ]
    }
  ]
}
```

#### 8. Recursively Include Referenced Resources

For each resource added to the Bundle:
- Check for references to other resources
- If referenced resource not yet in Bundle:
  - Convert referenced resource
  - Assign fullUrl
  - Add to Bundle.entry[]
- Continue until all references are resolved

Example: If Observation has a performer reference:
```json
{
  "resourceType": "Observation",
  "performer": [
    {
      "reference": "Practitioner/performer-123"
    }
  ]
}
```

Ensure Practitioner with id "performer-123" is in Bundle.

#### 9. Validate Bundle

- Ensure Composition is first entry
- Verify all entries have fullUrl
- Verify all entries have resource
- Check all references resolve within Bundle
- Verify no duplicate resources
- Ensure identifier and timestamp are present

#### 10. Optionally Sign Bundle

If document requires signing:
- Create Bundle.signature
- Include signature data
- Reference signing practitioner

### Resource Inclusion Algorithm

Pseudocode for determining which resources to include:

```
included = empty set
queue = [Composition]

while queue is not empty:
  resource = queue.pop()
  if resource in included:
    continue

  included.add(resource)

  for each reference in resource:
    referenced_resource = resolve(reference)
    if referenced_resource not in included:
      queue.add(referenced_resource)

return included
```

This ensures all directly and indirectly referenced resources are included.

## Complete Mapping Example

### C-CDA Input (Simplified)

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

  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
        </name>
      </assignedPerson>
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

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Allergies and Intolerances</title>
          <text>
            <table>
              <tr><td>Penicillin G - Hives</td></tr>
            </table>
          </text>
          <entry typeCode="DRIV">
            <!-- Allergy entry would be here -->
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

### FHIR Output (Complete Bundle)

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
      "fullUrl": "urn:uuid:3d70a971-eea6-4fe4-8d15-6f8f9c3c5e2f",
      "resource": {
        "resourceType": "Composition",
        "id": "composition-1",
        "meta": {
          "profile": [
            "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document"
          ]
        },
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
        "confidentiality": "N",
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
                  "code": "48765-2",
                  "display": "Allergies and adverse reactions Document"
                }
              ]
            },
            "text": {
              "status": "generated",
              "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><tr><td>Penicillin G - Hives</td></tr></table></div>"
            },
            "mode": "snapshot",
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
            "family": "Careful"
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
        "clinicalStatus": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
              "code": "active"
            }
          ]
        },
        "verificationStatus": {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
              "code": "confirmed"
            }
          ]
        },
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

## Implementation Considerations

### Bundle Size and Performance

Document Bundles can be large:

| Document Type | Typical Resource Count | Typical Size |
|---------------|----------------------|--------------|
| CCD | 50-200 resources | 100KB - 2MB |
| Discharge Summary | 30-100 resources | 50KB - 500KB |
| Progress Note | 10-50 resources | 20KB - 200KB |

**Considerations:**
- Use compression (gzip) for transmission
- Consider streaming for very large documents
- Monitor memory usage during conversion
- Implement pagination for display (though Bundle itself is not paginated)

### Identifier Management

**UUID Strategy (Recommended):**
- Generate UUIDs for resources without stable identifiers
- Use consistent UUID generation for reproducibility
- UUID v5 (name-based) can be derived from C-CDA identifiers

**OID Strategy:**
- Preserve C-CDA OIDs where meaningful
- Convert to `urn:oid:` format
- Combine with extension for composite identifiers

**Mixed Strategy:**
- Use OIDs for resources with C-CDA identifiers
- Use UUIDs for generated/supporting resources

### Reference Resolution Strategy

**Internal References (Preferred):**
```json
{
  "reference": "Patient/patient-123"
}
```

Resolves within Bundle by matching fullUrl.

**Absolute References (Avoid):**
```json
{
  "reference": "https://external-server.org/fhir/Patient/123"
}
```

Requires external resolution; not self-contained.

**Best Practice:** All references SHOULD resolve within the Bundle to maintain document integrity.

### Duplicate Resource Handling

If the same resource is referenced multiple times:
- Include it ONCE in Bundle
- All references point to the same entry
- Match by identifier or fullUrl

Example:
```json
{
  "entry": [
    {
      "fullUrl": "urn:uuid:practitioner-1",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-1"
      }
    },
    {
      "fullUrl": "urn:uuid:obs-1",
      "resource": {
        "resourceType": "Observation",
        "id": "obs-1",
        "performer": [
          {
            "reference": "Practitioner/practitioner-1"
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:obs-2",
      "resource": {
        "resourceType": "Observation",
        "id": "obs-2",
        "performer": [
          {
            "reference": "Practitioner/practitioner-1"
          }
        ]
      }
    }
  ]
}
```

Both observations reference the same Practitioner entry.

### Document Immutability

Once assembled, the Bundle is immutable:
- Content cannot change
- Bundle.identifier cannot be reused
- To create new version:
  - Create new Bundle with new identifier
  - Create new Composition with new identifier
  - Use Composition.relatesTo to link to prior version

### Error Handling

| Error Condition | Handling Strategy |
|-----------------|-------------------|
| Missing required C-CDA element | Log warning; create Bundle without optional elements |
| Circular references | Break cycle; log warning |
| External references in C-CDA | Attempt to convert; if impossible, use contained resources |
| Duplicate resource IDs | Generate unique IDs; ensure fullUrl uniqueness |
| Invalid references | Log error; omit broken reference or create stub resource |
| Resource conversion failure | Log error; skip resource; mark section with emptyReason if needed |

### Validation

**Bundle-Level Validation:**
- [ ] type = "document"
- [ ] identifier present
- [ ] timestamp present
- [ ] First entry is Composition
- [ ] All entries have fullUrl
- [ ] All entries have resource
- [ ] No broken references
- [ ] fullUrl values are unique

**Content Validation:**
- [ ] Composition conforms to C-CDA on FHIR profile
- [ ] Patient resource present
- [ ] All Composition references resolve
- [ ] Section entries match expected resource types
- [ ] Terminology codes valid

## Related Documentation

- **FHIR Bundle Resource**: [/docs/fhir/bundle.md](/docs/fhir/bundle.md)
- **FHIR Composition Resource**: [/docs/fhir/composition.md](/docs/fhir/composition.md)
- **C-CDA Clinical Document**: [/docs/ccda/clinical-document.md](/docs/ccda/clinical-document.md)
- **Composition Mapping**: [19-composition.md](19-composition.md)
- **Patient Mapping**: [01-patient.md](01-patient.md)
- **Section-Specific Mappings**: [02-condition.md](02-condition.md), [03-allergy-intolerance.md](03-allergy-intolerance.md), etc.

## References

- FHIR R4 Bundle: https://hl7.org/fhir/R4/bundle.html
- FHIR R4 Documents: https://hl7.org/fhir/R4/documents.html
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
- C-CDA R2.1: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- FHIR Document Bundles: https://hl7.org/fhir/R4/bundle.html#document
