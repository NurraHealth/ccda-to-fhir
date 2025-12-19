# FHIR R4B: Provenance Resource

## Overview

The Provenance resource tracks information about entities and processes involved in producing and delivering or otherwise influencing a resource. It enables assessing authenticity, trust, and reproducibility within healthcare information systems. Provenance is particularly important for tracking authorship, data lineage, and changes to clinical information.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Provenance |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 3 (Trial Use) |
| Security Category | Not Classified |
| Responsible Work Group | Security |
| URL | https://hl7.org/fhir/R4B/provenance.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-provenance |

## Scope and Usage

The Provenance resource documents:
- Activities that created, revised, deleted, or signed resource versions
- Entities and agents involved in resource creation or modification
- Temporal information about when activities occurred
- Reasons and policies governing the activities
- Digital signatures on resources

**Key Use Cases:**
- Tracking authorship of clinical information (who created or documented)
- Recording data lineage and transformation (middleware converting formats)
- Documenting approvals, attestations, and signatures
- Supporting audit trails and compliance requirements
- Establishing trust in clinical data

**Provenance vs AuditEvent:**
- **Provenance**: Prepared by applications initiating create/update operations, records information about resource creation/modification
- **AuditEvent**: Captures events as they occur at the system level, typically used for security auditing

## JSON Structure

```json
{
  "resourceType": "Provenance",
  "id": "example-provenance",
  "target": [
    {
      "reference": "Condition/condition-example"
    }
  ],
  "recorded": "2020-03-01T10:30:00Z",
  "occurredDateTime": "2020-03-01T10:30:00Z",
  "policy": [
    "http://example.org/fhir/policy/disclosure"
  ],
  "location": {
    "reference": "Location/example-clinic"
  },
  "reason": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
          "code": "TREAT",
          "display": "treatment"
        }
      ]
    }
  ],
  "activity": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
        "code": "CREATE",
        "display": "create"
      }
    ]
  },
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "author",
            "display": "Author"
          }
        ]
      },
      "role": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-RoleClass",
              "code": "PROV",
              "display": "healthcare provider"
            }
          ]
        }
      ],
      "who": {
        "reference": "Practitioner/practitioner-careful"
      },
      "onBehalfOf": {
        "reference": "Organization/org-community-health"
      }
    },
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "enterer",
            "display": "Enterer"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/practitioner-resident"
      },
      "onBehalfOf": {
        "reference": "Organization/org-community-health"
      }
    }
  ],
  "entity": [
    {
      "role": "source",
      "what": {
        "reference": "DocumentReference/source-document"
      }
    }
  ],
  "signature": [
    {
      "type": [
        {
          "system": "urn:iso-astm:E1762-95:2013",
          "code": "1.2.840.10065.1.12.1.1",
          "display": "Author's Signature"
        }
      ],
      "when": "2020-03-01T10:30:00Z",
      "who": {
        "reference": "Practitioner/practitioner-careful"
      },
      "sigFormat": "application/signature+xml",
      "data": "dGhpcyBibG9iIGlzIHNuaXBwZWQ="
    }
  ]
}
```

## Element Definitions

### target (1..*)

**Required.** The resource(s) created, updated, or otherwise affected by the activity.

| Type | Description |
|------|-------------|
| Reference(Any) | Reference to the resource(s) |

**Notes:**
- On RESTful systems, target references should ideally be version-specific
- Multiple targets can be specified for a single provenance record
- References need not be resolvable but must provide unique identification

### recorded (1..1)

**Required.** When the activity was recorded by the system.

| Type | Description |
|------|-------------|
| instant | Timestamp when provenance was recorded |

**Notes:**
- This is when the provenance record was created, not necessarily when the activity occurred
- Must be in the format YYYY-MM-DDThh:mm:ss.sss+zz:zz
- Required element for all provenance records

### occurred[x] (0..1)

When the activity occurred.

| Element | Type | Description |
|---------|------|-------------|
| occurredPeriod | Period | Time period during which the activity occurred |
| occurredDateTime | dateTime | Specific date/time when the activity occurred |

**Notes:**
- Use when the occurrence time differs from the recorded time
- occurredPeriod is useful for activities spanning a time range

### policy (0..*)

Policy or plan that authorized the activity.

| Type | Description |
|------|-------------|
| uri | URI of policy/plan |

**Notes:**
- References organizational policies governing data handling
- Multiple policies can be referenced

### location (0..1)

Where the activity occurred.

| Type | Description |
|------|-------------|
| Reference(Location) | Location where activity occurred |

### reason (0..*)

Reason the activity occurred.

| Type | Description |
|------|-------------|
| CodeableConcept | Coded reason for the activity |

**Value Set:** http://terminology.hl7.org/ValueSet/v3-PurposeOfUse (Extensible)

**Common Codes:**
| Code | Display |
|------|---------|
| TREAT | treatment |
| HPAYMT | healthcare payment |
| HMARKT | healthcare marketing |
| DONAT | donation |
| FRAUD | fraud |
| DISC | disclosure |
| HRESCH | healthcare research |
| PUBHLTH | public health |

### activity (0..1)

Type of activity that occurred.

| Type | Description |
|------|-------------|
| CodeableConcept | Activity type |

**Value Set:** http://hl7.org/fhir/ValueSet/provenance-activity-type (Extensible)

**Common Codes from v3-DataOperation:**
| Code | Display |
|------|---------|
| CREATE | create |
| UPDATE | revise |
| DELETE | delete |
| APPEND | append |
| NULLIFY | nullify |

### agent (1..*)

**Required.** Who participated in the activity.

| Element | Cardinality | Type | Description |
|---------|------------|------|-------------|
| type | 0..1 | CodeableConcept | Type of participation |
| role | 0..* | CodeableConcept | Security/functional role |
| who | 1..1 | Reference | Individual, device, or organization |
| onBehalfOf | 0..1 | Reference(Organization) | Organization represented |

**agent.who References:**
- Practitioner
- PractitionerRole
- RelatedPerson
- Patient
- Device
- Organization

**agent.type Value Set:** http://hl7.org/fhir/ValueSet/provenance-agent-type (Extensible)

**Common Agent Types:**
| Code | Display | Description |
|------|---------|-------------|
| author | Author | Party that originates the resource |
| performer | Performer | Party who actually carries out the activity |
| enterer | Enterer | Person entering data into the system |
| informant | Informant | Party who reported information |
| verifier | Verifier | Person who verifies correctness |
| legal | Legal Authenticator | Person who legally authenticates content |
| attester | Attester | Person who attests to accuracy |
| custodian | Custodian | Entity maintaining true copy of original |
| assembler | Assembler | Device that assembles existing information |
| composer | Composer | Device used to record/aggregate information |

**agent.role Value Set:** http://hl7.org/fhir/ValueSet/security-role-type (Example)

### entity (0..*)

Resources used during the activity.

| Element | Cardinality | Type | Description |
|---------|------------|------|-------------|
| role | 1..1 | code | derivation \| revision \| quotation \| source \| removal |
| what | 1..1 | Reference(Any) | Identity of entity |
| agent | 0..* | Provenance.agent | Responsible agent for entity |

**entity.role (Required binding):**
| Code | Display | Description |
|------|---------|-------------|
| derivation | Derivation | Data derived from entity |
| revision | Revision | Revision of entity |
| quotation | Quotation | Quoted from entity |
| source | Source | Extracted from entity |
| removal | Removal | Entity removed from record |

**Notes:**
- Use `source` when extracting data from another resource (e.g., CDA document)
- Use `revision` when updating an existing resource
- Entities can have their own agent information

### signature (0..*)

Digital signature on the target resource(s).

| Element | Type | Description |
|---------|------|-------------|
| type | Coding[] | Signature type (1..*) |
| when | instant | When signature created (1..1) |
| who | Reference | Who signed (1..1) |
| onBehalfOf | Reference | Organization represented (0..1) |
| targetFormat | code | MIME type of signed target (0..1) |
| sigFormat | code | MIME type of signature (0..1) |
| data | base64Binary | Actual signature content (0..1) |

**Signature Type System:** urn:iso-astm:E1762-95:2013

**Common Signature Types:**
| Code | Display |
|------|---------|
| 1.2.840.10065.1.12.1.1 | Author's Signature |
| 1.2.840.10065.1.12.1.2 | Coauthor's Signature |
| 1.2.840.10065.1.12.1.5 | Verification Signature |
| 1.2.840.10065.1.12.1.7 | Consent Signature |
| 1.2.840.10065.1.12.1.8 | Signature Witness Signature |

## US Core Provenance Profile

### Conformance Requirements

1. **SHALL** support `target` (1..*)
2. **SHALL** support `recorded` (1..1)
3. **SHALL** support at least one `agent` (1..*)
4. **SHALL** support `agent.type` for ProvenanceAuthor slice (1..1)
5. **SHALL** support `agent.who` (1..1)
6. **SHALL** support `agent.onBehalfOf` when who is Practitioner or Device

### Agent Slices

**ProvenanceAuthor (1..1):**
- `agent.type` = "author" (fixed)
- `agent.who` = Reference to Organization, Practitioner, Patient, PractitionerRole, RelatedPerson, or Device
- `agent.onBehalfOf` = Organization (when applicable)

**ProvenanceTransmitter (0..*):**
- `agent.type` = "transmitter" (fixed)
- `agent.who` = Reference to Organization, Practitioner, Patient, PractitionerRole, RelatedPerson, or Device
- `agent.onBehalfOf` = Organization (required when who is Practitioner or Device)

### Constraint: provenance-1

**Error-level constraint:** "onBehalfOf SHALL be present when Provenance.agent.who is a Practitioner or Device"

**Rationale:** Ensures organizational accountability for individual provider and device actions.

### Supported Resource Types

US Core Provenance applies to these clinical resource types:
- AllergyIntolerance
- CarePlan
- CareTeam
- Condition
- Coverage
- Device
- DiagnosticReport
- DocumentReference
- Encounter
- Goal
- Immunization
- MedicationDispense
- MedicationRequest
- Observation
- Patient
- Procedure
- QuestionnaireResponse
- RelatedPerson
- ServiceRequest

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of resource |
| agent | reference | Who participated |
| agent-role | token | Agent's role |
| agent-type | token | Agent participation type |
| entity | reference | Entity identity |
| location | reference | Activity location |
| patient | reference | Patient-related provenance |
| recorded | date | Recording timestamp |
| target | reference | Target resource(s) |
| when | date | Activity occurrence |
| signature-type | token | Signature reason indication |

### Required Search Parameters (US Core)

**_revinclude:**
- Servers SHALL support `_revinclude=Provenance:target`
- Example: `GET [base]/Condition?patient=[id]&_revinclude=Provenance:target`

## Compartments

- Device
- Patient
- Practitioner
- RelatedPerson

## Implementation Guidance

### Creating Provenance Records

**When to create Provenance:**
1. Tracking authorship of clinical information
2. Recording data transformations (e.g., CDA to FHIR conversion)
3. Documenting approvals and attestations
4. Supporting regulatory/compliance requirements
5. When resource-specific properties (e.g., `AllergyIntolerance.recorder`) are insufficient

### Multiple Provenance Records

- Multiple provenance records can exist for a single resource or version
- Different provenance records can track different aspects:
  - Original authorship
  - Subsequent modifications
  - Approvals/attestations
  - Data transformations

### Target References

**Best Practices:**
- Use version-specific references on RESTful systems
- Submit resource + provenance in a single transaction for integrity
- Ensure references are unique and unambiguous

### Example: C-CDA to FHIR Conversion

When converting C-CDA to FHIR, create Provenance to track:

```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "Condition/condition-1"}],
  "recorded": "2020-03-01T10:30:00Z",
  "activity": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
      "code": "CREATE"
    }]
  },
  "agent": [
    {
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
          "code": "author"
        }]
      },
      "who": {"reference": "Practitioner/doc-1"},
      "onBehalfOf": {"reference": "Organization/hospital-1"}
    },
    {
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
          "code": "assembler"
        }]
      },
      "who": {"reference": "Device/converter"},
      "onBehalfOf": {"reference": "Organization/our-org"}
    }
  ],
  "entity": [
    {
      "role": "source",
      "what": {"reference": "DocumentReference/ccda-doc"}
    }
  ]
}
```

### W3C PROV Alignment

FHIR Provenance aligns with W3C PROV specifications:
- Provenance covers Entity "Generation" (creation/updating)
- AuditEvent covers "Usage" and other "Activity" types

## Common Patterns

### Pattern 1: Simple Authorship

```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "Observation/obs-1"}],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "author"
      }]
    },
    "who": {"reference": "Practitioner/pract-1"},
    "onBehalfOf": {"reference": "Organization/org-1"}
  }]
}
```

### Pattern 2: Data Entry with Author

```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "MedicationRequest/med-1"}],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [
    {
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
          "code": "author"
        }]
      },
      "who": {"reference": "Practitioner/physician-1"},
      "onBehalfOf": {"reference": "Organization/hospital-1"}
    },
    {
      "type": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
          "code": "enterer"
        }]
      },
      "who": {"reference": "Practitioner/nurse-1"},
      "onBehalfOf": {"reference": "Organization/hospital-1"}
    }
  ]
}
```

### Pattern 3: Document Conversion

```json
{
  "resourceType": "Provenance",
  "target": [
    {"reference": "Condition/cond-1"},
    {"reference": "AllergyIntolerance/allergy-1"}
  ],
  "recorded": "2020-03-15T14:00:00Z",
  "activity": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
      "code": "CREATE"
    }]
  },
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "assembler"
      }]
    },
    "who": {"reference": "Device/ccda-converter"},
    "onBehalfOf": {"reference": "Organization/converter-org"}
  }],
  "entity": [{
    "role": "source",
    "what": {"reference": "DocumentReference/ccda-1"}
  }]
}
```

## References

- FHIR R4B Provenance: https://hl7.org/fhir/R4B/provenance.html
- US Core Provenance Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-provenance
- W3C PROV: https://www.w3.org/TR/prov-overview/
- Provenance Participant Type Codes: http://terminology.hl7.org/CodeSystem/provenance-participant-type
- US Core Implementation Guide: http://hl7.org/fhir/us/core/
