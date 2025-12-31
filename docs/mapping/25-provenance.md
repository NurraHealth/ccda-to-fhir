# Provenance Mapping: C-CDA Participations ↔ FHIR Provenance

This document provides detailed mapping guidance for C-CDA participation elements (author, performer, informant, participant) to FHIR `Provenance` resources.

## Overview

Provenance tracks information about entities and processes involved in producing and delivering clinical resources. While many FHIR resources have built-in properties for authorship (e.g., `Condition.recorder`, `MedicationRequest.requester`), the Provenance resource provides comprehensive tracking when additional information is required or explicit provenance records are desired.

### Key Differences: C-CDA vs FHIR

| Aspect | C-CDA | FHIR |
|--------|-------|------|
| **Context Conduction** | Participations propagate from document → section → entry | No context conduction; each resource needs explicit provenance |
| **Recording Time** | Author time at each level | Provenance.recorded for when provenance was captured |
| **Multiple Authors** | Multiple authors tracked via multiple author elements | Multiple authors via Provenance.agent[] array |
| **Device Authors** | assignedAuthoringDevice | Provenance.agent.who references Device resource |
| **Organizational Context** | representedOrganization | Provenance.agent.onBehalfOf |

## Mapping Strategy

### When to Create Provenance Resources

Create FHIR Provenance resources when:

1. **Multiple authors exist** for a clinical resource
2. **Complete audit trail** is required
3. **Device or system authorship** needs tracking
4. **Entry-level authors** differ from document-level authors
5. **Provenance information** exceeds what resource-specific elements can capture

### When to Use Resource-Specific Elements

Use resource properties when sufficient:

| FHIR Resource | Built-in Property | Use When |
|---------------|------------------|----------|
| Condition | `recorder` | Single author, basic tracking |
| AllergyIntolerance | `recorder` | Single author, basic tracking |
| Procedure | `recorder` | Single author (via extension) |
| MedicationRequest | `requester`, `authoredOn` | Single prescriber |
| Observation | `performer` | Single performer |
| Encounter | `participant` | Care team tracking |
| Composition | `author`, `attester` | Document-level authorship |

**Note:** Provenance provides richer tracking even when resource properties exist.

## C-CDA Author to FHIR Provenance

### Basic Author Mapping

#### C-CDA Input

```xml
<observation>
  <id root="2.16.840.1.113883.19.5" extension="OBS-123"/>
  <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
        displayName="Systolic Blood Pressure"/>
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20200301103000-0500"/>
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
</observation>
```

#### FHIR Output

```json
{
  "resourceType": "Provenance",
  "id": "provenance-obs-123",
  "target": [
    {
      "reference": "Observation/obs-123"
    }
  ],
  "recorded": "2020-03-01T10:30:00-05:00",
  "occurredDateTime": "2020-03-01T10:30:00-05:00",
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
      "who": {
        "reference": "Practitioner/practitioner-1234567890"
      },
      "onBehalfOf": {
        "reference": "Organization/org-1393"
      }
    }
  ]
}
```

### Mapping Table: Author to Provenance

| C-CDA Path | FHIR Path | Notes |
|------------|-----------|-------|
| `author/time/@value` | `Provenance.recorded` | When provenance recorded |
| `author/time/@value` | `Provenance.occurredDateTime` | When authoring occurred |
| `assignedAuthor/id` | `Practitioner.identifier` | Creates/references Practitioner |
| `assignedPerson/name` | `Practitioner.name` | Practitioner name |
| `assignedAuthor/code` | `PractitionerRole.specialty` | Creates PractitionerRole |
| `representedOrganization` | `Organization` | Creates/references Organization |
| — | `Provenance.agent.type` = "author" | Fixed code |
| `assignedAuthor` → Practitioner | `Provenance.agent.who` | Reference to Practitioner |
| `representedOrganization` → Organization | `Provenance.agent.onBehalfOf` | Reference to Organization |

## Multiple Authors Mapping

When multiple authors exist at entry level:

#### C-CDA Input

```xml
<observation>
  <!-- First author: original documenter -->
  <author>
    <time value="20200301103000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
      <assignedPerson>
        <name><given>John</given><family>Original</family></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <!-- Second author: updated by -->
  <author>
    <time value="20200315143000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="2222222222"/>
      <assignedPerson>
        <name><given>Jane</given><family>Updater</family></name>
      </assignedPerson>
    </assignedAuthor>
  </author>
</observation>
```

#### FHIR Output

```json
{
  "resourceType": "Provenance",
  "id": "provenance-obs-123",
  "target": [
    {
      "reference": "Observation/obs-123"
    }
  ],
  "recorded": "2020-03-01T10:30:00-05:00",
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
      "who": {
        "reference": "Practitioner/practitioner-1111111111"
      }
    },
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
      "who": {
        "reference": "Practitioner/practitioner-2222222222"
      }
    }
  ]
}
```

**Mapping Rules for Multiple Authors:**
1. **Provenance.recorded** = earliest author time
2. **Provenance.agent[]** = array containing all authors
3. Each author becomes a separate agent element
4. Agent order preserved from C-CDA

## C-CDA Performer to FHIR Provenance

### Performer Mapping

| C-CDA Path | FHIR Path | Notes |
|------------|-----------|-------|
| `performer/@typeCode` | Determines agent.type | PRF→performer, SPRF→performer |
| `performer/functionCode` | `Provenance.agent.role` | Maps to RoleClass or ParticipationFunction |
| `performer/time` | `Provenance.occurredPeriod` | When performer was involved |
| `assignedEntity/id` | `Practitioner.identifier` | Creates/references Practitioner |
| `assignedEntity/code` | `PractitionerRole.specialty` | Specialty of performer |
| `assignedPerson/name` | `Practitioner.name` | Performer name |
| — | `Provenance.agent.type` = "performer" | Fixed code |

### Example: Procedure Performer

#### C-CDA Input

```xml
<procedure>
  <performer>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
      <code code="208600000X" codeSystem="2.16.840.1.113883.6.101"
            displayName="Surgery"/>
      <assignedPerson>
        <name>
          <given>John</given>
          <family>Surgeon</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
    </assignedEntity>
  </performer>
</procedure>
```

#### FHIR Output

```json
{
  "resourceType": "Provenance",
  "id": "provenance-proc-123",
  "target": [
    {
      "reference": "Procedure/proc-123"
    }
  ],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "performer",
            "display": "Performer"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/practitioner-9876543210"
      }
    }
  ]
}
```

### Service Event Performer (Care Team)

Service event performers typically map to CareTeam rather than Provenance, but can also create Provenance for document-level tracking.

#### C-CDA Input

```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <performer typeCode="PRF">
      <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                    displayName="Primary Care Provider"/>
      <time>
        <low value="20150622"/>
      </time>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <assignedPerson>
          <name><given>Adam</given><family>Careful</family></name>
        </assignedPerson>
      </assignedEntity>
    </performer>
  </serviceEvent>
</documentationOf>
```

#### FHIR Output - CareTeam (Primary)

```json
{
  "resourceType": "CareTeam",
  "id": "careteam-1",
  "status": "active",
  "subject": {
    "reference": "Patient/patient-1"
  },
  "period": {
    "start": "2015-06-22"
  },
  "participant": [
    {
      "role": [
        {
          "coding": [
            {
              "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationFunction",
              "code": "PCP",
              "display": "Primary Care Provider"
            }
          ]
        }
      ],
      "member": {
        "reference": "Practitioner/practitioner-1234567890"
      },
      "period": {
        "start": "2015-06-22"
      }
    }
  ]
}
```

## C-CDA Informant to FHIR Provenance

### Informant Mapping

| C-CDA Path | FHIR Path | Notes |
|------------|-----------|-------|
| `informant/assignedEntity` | Creates Practitioner | Professional informant |
| `informant/relatedEntity` | Creates RelatedPerson | Family member informant |
| `relatedEntity/code` | `RelatedPerson.relationship` | Relationship to patient |
| `relatedPerson/name` | `RelatedPerson.name` | Informant name |
| — | `Provenance.agent.type` = "informant" | Fixed code |
| Informant → Person/RelatedPerson | `Provenance.agent.who` | Reference to informant |

### Example: Family Member Informant

#### C-CDA Input

```xml
<observation>
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
</observation>
```

#### FHIR Output

**RelatedPerson:**
```json
{
  "resourceType": "RelatedPerson",
  "id": "related-mother-1",
  "patient": {
    "reference": "Patient/patient-1"
  },
  "relationship": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
          "code": "MTH",
          "display": "Mother"
        }
      ]
    }
  ],
  "name": [
    {
      "family": "Ross",
      "given": ["Martha"]
    }
  ]
}
```

**Provenance:**
```json
{
  "resourceType": "Provenance",
  "id": "provenance-obs-123",
  "target": [
    {
      "reference": "Observation/obs-123"
    }
  ],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "informant",
            "display": "Informant"
          }
        ]
      },
      "who": {
        "reference": "RelatedPerson/related-mother-1"
      }
    }
  ]
}
```

## Device as Author

When a device authored the content:

### Mapping Table

| C-CDA Path | FHIR Path | Notes |
|------------|-----------|-------|
| `assignedAuthoringDevice/manufacturerModelName` | `Device.deviceName` (type=manufacturer-name) | Manufacturer and model |
| `assignedAuthoringDevice/softwareName` | `Device.deviceName` (type=model-name) | Software name |
| `assignedAuthor/id` | `Device.identifier` | Device identifier |
| `representedOrganization` | `Organization` | Organization owning device |
| — | `Provenance.agent.type` = "author" or "assembler" | Based on context |
| Device | `Provenance.agent.who` | Reference to Device |
| Organization | `Provenance.agent.onBehalfOf` | Required per US Core |

### Example: Device Author

#### C-CDA Input

```xml
<author>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Epic EHR</manufacturerModelName>
      <softwareName>Epic 2020</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

#### FHIR Output

**Device:**
```json
{
  "resourceType": "Device",
  "id": "device-ehr-001",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5",
      "value": "DEVICE-001"
    }
  ],
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

**Provenance:**
```json
{
  "resourceType": "Provenance",
  "id": "provenance-1",
  "target": [
    {
      "reference": "Condition/cond-1"
    }
  ],
  "recorded": "2020-03-01T00:00:00Z",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "assembler",
            "display": "Assembler"
          }
        ]
      },
      "who": {
        "reference": "Device/device-ehr-001"
      },
      "onBehalfOf": {
        "reference": "Organization/org-1393"
      }
    }
  ]
}
```

## Document-Level Participations

### Legal Authenticator and Authenticator

These map to `Composition.attester` rather than Provenance, but can also create Provenance for complete tracking.

#### C-CDA Input

```xml
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

<authenticator>
  <time value="20200302"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
    <assignedPerson>
      <name><given>Jane</given><family>Resident</family></name>
    </assignedPerson>
  </assignedEntity>
</authenticator>
```

#### FHIR Output - Composition.attester (Primary)

```json
{
  "resourceType": "Composition",
  "attester": [
    {
      "mode": "legal",
      "time": "2020-03-01",
      "party": {
        "reference": "Practitioner/practitioner-1234567890"
      }
    },
    {
      "mode": "professional",
      "time": "2020-03-02",
      "party": {
        "reference": "Practitioner/practitioner-5555555555"
      }
    }
  ]
}
```

#### FHIR Output - Provenance (Optional, for complete tracking)

```json
{
  "resourceType": "Provenance",
  "id": "provenance-composition-1",
  "target": [
    {
      "reference": "Composition/composition-1"
    }
  ],
  "recorded": "2020-03-01T00:00:00Z",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "legal",
            "display": "Legal Authenticator"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/practitioner-1234567890"
      }
    },
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "attester",
            "display": "Attester"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/practitioner-5555555555"
      }
    }
  ]
}
```

### Data Enterer

Maps to Composition extension and optionally to Provenance.

| C-CDA Element | FHIR Path |
|---------------|-----------|
| `dataEnterer` | `Composition.extension` (DataEntererExtension) |
| `dataEnterer` | `Provenance.agent` with type="enterer" (optional) |

### Custodian

Maps to Composition.custodian, not typically to Provenance.

| C-CDA Element | FHIR Path |
|---------------|-----------|
| `custodian/assignedCustodian/representedCustodianOrganization` | `Composition.custodian` |
| `custodian` | `Provenance.agent` with type="custodian" (optional) |

## Provenance Agent Type Mapping

### Complete Mapping Table

| C-CDA Participation | C-CDA Context | FHIR Provenance.agent.type |
|---------------------|---------------|---------------------------|
| author | Entry-level | `author` |
| author (device) | Entry-level | `author` or `assembler` |
| performer | Entry-level | `performer` |
| informant | Entry-level | `informant` |
| participant | Entry-level | Based on typeCode |
| dataEnterer | Document-level | `enterer` |
| legalAuthenticator | Document-level | `legal` |
| authenticator | Document-level | `attester` |
| custodian | Document-level | `custodian` |

### C-CDA typeCode to Provenance agent.type

When participant has typeCode:

| C-CDA typeCode | FHIR agent.type |
|----------------|----------------|
| AUT | author |
| PRF | performer |
| INF | informant |
| ENT | enterer |
| VRF | verifier |
| LA | legal |
| AUTHEN | attester |
| CST | custodian |

## Context Conduction Handling

### Challenge

C-CDA context conduction means entry-level elements inherit document/section-level participations unless overridden. FHIR has no context conduction.

### Strategy

1. **Explicit Provenance:** Create Provenance only for explicitly stated participations at entry level
2. **Document Context:** If entry has no explicit author, optionally create Provenance referencing document author
3. **Precedence:** Entry-level participation > Section-level > Document-level

### Example: Entry with No Explicit Author

#### C-CDA Input

```xml
<ClinicalDocument>
  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
      <assignedPerson>
        <name><given>Document</given><family>Author</family></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <component>
    <section>
      <entry>
        <observation>
          <!-- No explicit author - inherits from document -->
        </observation>
      </entry>
    </section>
  </component>
</ClinicalDocument>
```

#### FHIR Output Option 1: No Provenance (Minimal)

```json
{
  "resourceType": "Observation",
  "id": "obs-1",
  "status": "final",
  "code": {...}
}
```

#### FHIR Output Option 2: Create Provenance (Complete Tracking)

```json
{
  "resourceType": "Provenance",
  "id": "provenance-obs-1",
  "target": [
    {
      "reference": "Observation/obs-1"
    }
  ],
  "recorded": "2020-03-01T00:00:00Z",
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
      "who": {
        "reference": "Practitioner/practitioner-1111111111"
      }
    }
  ]
}
```

**Recommendation:** Use Option 2 when complete audit trail required; use Option 1 for minimal compliant conversion.

## C-CDA on FHIR IG Guidance

### Provenance Patterns

Per C-CDA on FHIR IG, provenance patterns vary by document type:

#### Provider-Generated Documents

```json
{
  "agent": [
    {
      "type": {"coding": [{"code": "author"}]},
      "who": {"reference": "Practitioner/pract-1"},
      "onBehalfOf": {"reference": "Organization/org-1"}
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

#### Patient-Generated Documents

```json
{
  "agent": [
    {
      "type": {"coding": [{"code": "author"}]},
      "who": {"reference": "Patient/patient-1"}
    },
    {
      "type": {"coding": [{"code": "assembler"}]},
      "who": {"reference": "Device/patient-app"},
      "onBehalfOf": {"reference": "Organization/app-vendor"}
    }
  ]
}
```

#### Device/Assembler-Generated Documents

```json
{
  "agent": [
    {
      "type": {"coding": [{"code": "assembler"}]},
      "who": {"reference": "Device/ehr-system"},
      "onBehalfOf": {"reference": "Organization/hospital"}
    }
  ]
}
```

## Provenance.entity Usage

### Tracking Source Document

When converting from C-CDA, include entity to reference source:

```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "Condition/cond-1"}],
  "agent": [...],
  "entity": [
    {
      "role": "source",
      "what": {
        "reference": "DocumentReference/ccda-source"
      }
    }
  ]
}
```

### Entity Roles

| entity.role | Use Case |
|-------------|----------|
| derivation | Data derived from entity |
| revision | Updated version of entity |
| quotation | Quoted from entity |
| source | Extracted from entity (C-CDA conversion) |
| removal | Entity removed from record |

## US Core Provenance Compliance

### Required Elements

1. **target** (1..*): Reference to clinical resource(s)
2. **recorded** (1..1): When provenance recorded
3. **agent** (1..*): At least one agent
4. **agent.type** (1..1 for ProvenanceAuthor slice): Fixed to "author"
5. **agent.who** (1..1): Reference to participant
6. **agent.onBehalfOf** (0..1): Required when who is Practitioner or Device

### Constraint: provenance-1

**"onBehalfOf SHALL be present when Provenance.agent.who is a Practitioner or Device"**

This ensures organizational accountability.

### Example: US Core Compliant

```json
{
  "resourceType": "Provenance",
  "id": "provenance-1",
  "target": [{"reference": "Condition/cond-1"}],
  "recorded": "2020-03-01T10:30:00Z",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "author"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/pract-1"
      },
      "onBehalfOf": {
        "reference": "Organization/org-1"
      }
    }
  ]
}
```

## Implementation Notes

### Resource Deduplication

When the same practitioner or organization appears multiple times:

1. **Generate consistent IDs** from CDA identifiers (root + extension)
2. **Reference existing resources** before creating new ones
3. **Use ReferenceRegistry** pattern for tracking

**Example ID Generation:**
- NPI `1234567890` → `Practitioner/practitioner-npi-1234567890`
- OID `2.16.840.1.113883.19.5` + extension `ORG-001` → `Organization/org-2.16.840.1.113883.19.5-ORG-001`

### Provenance.recorded vs occurredDateTime

| Element | Use |
|---------|-----|
| `recorded` | When provenance record was created (required) |
| `occurredDateTime` | When the activity actually occurred (optional) |

**Mapping:**
- Use earliest author/performer time for `recorded`
- Use same time for `occurredDateTime` when activity time is known
- For document conversion, `recorded` = conversion time, `occurred` = original author time

### Activity Codes

When creating Provenance during C-CDA conversion:

```json
{
  "activity": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/v3-DataOperation",
        "code": "CREATE",
        "display": "create"
      }
    ]
  }
}
```

**Common Activity Codes:**
| Code | Use |
|------|-----|
| CREATE | Creating new FHIR resource from C-CDA |
| UPDATE | Updating existing resource |
| APPEND | Adding to existing resource |

## Complete Example: Multi-Author Clinical Entry

### C-CDA Input

```xml
<observation>
  <id root="2.16.840.1.113883.19.5" extension="OBS-456"/>
  <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>

  <!-- Original author -->
  <author>
    <time value="20200301103000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
      <assignedPerson>
        <name><given>Alice</given><family>Original</family></name>
      </assignedPerson>
      <representedOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1"/>
        <name>Primary Clinic</name>
      </representedOrganization>
    </assignedAuthor>
  </author>

  <!-- Performer -->
  <performer>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="2222222222"/>
      <assignedPerson>
        <name><given>Bob</given><family>Performer</family></name>
      </assignedPerson>
    </assignedEntity>
  </performer>

  <!-- Informant -->
  <informant>
    <relatedEntity classCode="PRS">
      <code code="SPS" codeSystem="2.16.840.1.113883.5.111"
            displayName="Spouse"/>
      <relatedPerson>
        <name><given>Carol</given><family>Spouse</family></name>
      </relatedPerson>
    </relatedEntity>
  </informant>
</observation>
```

### FHIR Output

**Observation:**
```json
{
  "resourceType": "Observation",
  "id": "obs-456",
  "status": "final",
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8480-6"
      }
    ]
  },
  "performer": [
    {
      "reference": "Practitioner/practitioner-2222222222"
    }
  ]
}
```

**Provenance:**
```json
{
  "resourceType": "Provenance",
  "id": "provenance-obs-456",
  "target": [
    {
      "reference": "Observation/obs-456"
    }
  ],
  "recorded": "2020-03-01T10:30:00-05:00",
  "occurredDateTime": "2020-03-01T10:30:00-05:00",
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
      "who": {
        "reference": "Practitioner/practitioner-1111111111"
      },
      "onBehalfOf": {
        "reference": "Organization/org-1"
      }
    },
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "performer",
            "display": "Performer"
          }
        ]
      },
      "who": {
        "reference": "Practitioner/practitioner-2222222222"
      }
    },
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "informant",
            "display": "Informant"
          }
        ]
      },
      "who": {
        "reference": "RelatedPerson/related-spouse-1"
      }
    }
  ]
}
```

**Supporting Resources:**
- `Practitioner/practitioner-1111111111` (Alice Original)
- `Practitioner/practitioner-2222222222` (Bob Performer)
- `Organization/org-1` (Primary Clinic)
- `RelatedPerson/related-spouse-1` (Carol Spouse)

## Summary of Mapping Rules

1. **Create Provenance** when entry-level participations exist or complete tracking required
2. **Provenance.target** references the clinical resource created from C-CDA entry
3. **Provenance.recorded** = earliest participation time (typically first author time)
4. **Provenance.agent[]** contains all participations as separate agent elements
5. **agent.type** maps from C-CDA participation type (author→author, performer→performer, etc.)
6. **agent.who** references Practitioner, Device, Patient, or RelatedPerson
7. **agent.onBehalfOf** references Organization (required for Practitioner/Device per US Core)
8. **Provenance.entity** with role="source" references source DocumentReference when converting from C-CDA
9. **Handle context conduction** by creating explicit Provenance for entry-level participations
10. **Deduplicate resources** using consistent ID generation from C-CDA identifiers

## References

- [FHIR R4B Provenance](https://hl7.org/fhir/R4B/provenance.html)
- [US Core Provenance Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-provenance)
- [C-CDA on FHIR Mapping Guidance](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html)
- [C-CDA Provenance Implementation](https://build.fhir.org/ig/HL7/CDA-ccda/provenance.html)
- [C-CDA Author Participation Template](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.119.html)
- [Provenance Participant Type Codes](http://terminology.hl7.org/CodeSystem/provenance-participant-type)
- [C-CDA on FHIR Participations](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participations.html)
