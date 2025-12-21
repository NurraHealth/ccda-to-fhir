# CarePlan Mapping: C-CDA Care Plan Document ↔ FHIR Composition + CarePlan

This document provides detailed mapping guidance between C-CDA Care Plan Document and FHIR `Composition` + `CarePlan` resources.

## Overview

The C-CDA Care Plan Document maps to **two** FHIR resources:
1. **Composition** - Represents the Care Plan Document structure, sections, and metadata
2. **CarePlan** - Represents the care plan content referenced within the Composition

| C-CDA | FHIR |
|-------|------|
| Care Plan Document (`2.16.840.1.113883.10.20.22.1.15`) | `Composition` (C-CDA on FHIR Care Plan Document profile) + `CarePlan` (US Core CarePlan profile) |
| ClinicalDocument header | `Composition` metadata |
| structuredBody sections | `Composition.section` |
| Health Concerns, Goals, Interventions | Referenced resources in `Composition` + content in `CarePlan` |

## Architectural Pattern

The mapping follows the C-CDA on FHIR Implementation Guide pattern:

```
C-CDA Care Plan Document
├── ClinicalDocument header → Composition (metadata)
├── Health Concerns Section → Composition.section + Condition resources
├── Goals Section → Composition.section + Goal resources
├── Interventions Section → Composition.section + referenced in CarePlan.activity
└── Outcomes Section → Composition.section + Observation resources

FHIR Bundle contains:
├── Composition (Care Plan Document)
│   ├── section[healthConcerns] references → Condition resources
│   ├── section[goals] references → Goal resources
│   ├── section[interventions] references → ServiceRequest/Procedure
│   └── section[outcomes] references → Observation resources
├── CarePlan (Assessment and Plan)
│   ├── addresses → Condition resources (from Health Concerns)
│   ├── goal → Goal resources (from Goals Section)
│   └── activity → ServiceRequest/Procedure (from Interventions)
├── Goal resources
├── Condition resources
├── ServiceRequest/Procedure resources
└── Observation resources
```

## Structural Mapping

### Document to Composition

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| ClinicalDocument `id` | `Composition.identifier` | II → Identifier |
| ClinicalDocument `code` | `Composition.type` | Fixed: Care Plan Document type |
| ClinicalDocument `title` | `Composition.title` | String |
| (document state) | `Composition.status` | [Status ConceptMap](#composition-status-mapping) (default: "final") |
| ClinicalDocument `effectiveTime` | `Composition.date` | Timestamp conversion |
| ClinicalDocument `confidentialityCode` | `Composition.confidentiality` | [Confidentiality ConceptMap](#confidentiality-mapping) |
| ClinicalDocument `languageCode` | `Composition.language` | Language code |
| ClinicalDocument `setId` | `Composition.identifier` (additional) | II → Identifier |
| ClinicalDocument `versionNumber` | `Composition.identifier.version` | Integer |
| `recordTarget` | `Composition.subject` | Reference(Patient) |
| `author` (first/primary) | `Composition.author` | Reference(Practitioner \| Patient) |
| `author` (all) + `participant` + serviceEvent `performer` | `Composition.author` + `CarePlan.contributor` | References |
| `custodian` | `Composition.custodian` | Reference(Organization) |
| `documentationOf/serviceEvent` `effectiveTime` | `Composition.event.period` + `CarePlan.period` | Period mapping |
| `documentationOf/serviceEvent` `performer` | `CarePlan.contributor` | Reference (US Core Must Support) |

### Document to CarePlan

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| ClinicalDocument (implicit) | `CarePlan` resource | Create CarePlan from document content |
| ClinicalDocument `id` | `CarePlan.identifier` | II → Identifier |
| serviceEvent `statusCode` | `CarePlan.status` | Map to active/completed/etc. |
| (implicit: plan intent) | `CarePlan.intent` | Fixed: "plan" |
| (implicit: assess-plan) | `CarePlan.category` | Fixed: assess-plan |
| `recordTarget` | `CarePlan.subject` | Reference(Patient) |
| serviceEvent `effectiveTime` | `CarePlan.period` | Period |
| `author` | `CarePlan.author` | Reference(Practitioner \| Patient) |
| Health Concerns → Conditions | `CarePlan.addresses` | Reference(Condition)[] |
| Goals → Goal resources | `CarePlan.goal` | Reference(Goal)[] |
| Interventions → Activities | `CarePlan.activity` | Activity mapping |

## C-CDA to FHIR Mapping

### Composition Header Mappings

#### Document Identification

**C-CDA:**
```xml
<ClinicalDocument>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5" extension="careplan-12345"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>
  <setId root="2.16.840.1.113883.19.5" extension="careplan-set-123"/>
  <versionNumber value="2"/>
</ClinicalDocument>
```

**FHIR Composition:**
```json
{
  "resourceType": "Composition",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document"
    ]
  },
  "identifier": [
    {
      "system": "urn:ietf:rfc:3986",
      "value": "urn:oid:2.16.840.1.113883.19.5.careplan-12345"
    },
    {
      "system": "urn:ietf:rfc:3986",
      "value": "urn:oid:2.16.840.1.113883.19.5.careplan-set-123",
      "version": "2"
    }
  ],
  "status": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "52521-2",
        "display": "Overall plan of care/advance care directives"
      }
    ]
  },
  "title": "Care Plan",
  "date": "2024-01-15T12:00:00-05:00"
}
```

#### Subject and Author

**C-CDA:**
```xml
<recordTarget>
  <patientRole>
    <id root="2.16.840.1.113883.4.1" extension="123-45-6789"/>
    <patient>
      <name><given>Amy</given><family>Shaw</family></name>
    </patient>
  </patientRole>
</recordTarget>

<author>
  <time value="20240115120000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name><given>John</given><family>Smith</family><suffix>MD</suffix></name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR Composition:**
```json
{
  "subject": {
    "reference": "Patient/123-45-6789",
    "display": "Amy Shaw"
  },
  "author": [
    {
      "reference": "Practitioner/1234567890",
      "display": "John Smith, MD"
    }
  ]
}
```

**FHIR CarePlan:**
```json
{
  "subject": {
    "reference": "Patient/123-45-6789"
  },
  "author": {
    "reference": "Practitioner/1234567890"
  }
}
```

#### Service Event Period

**C-CDA:**
```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20240115"/>
      <high value="20240415"/>
    </effectiveTime>
    <performer typeCode="PRF">
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      </assignedEntity>
    </performer>
  </serviceEvent>
</documentationOf>
```

**FHIR Composition:**
```json
{
  "event": [
    {
      "period": {
        "start": "2024-01-15",
        "end": "2024-04-15"
      },
      "detail": [
        {
          "reference": "CarePlan/careplan-12345"
        }
      ]
    }
  ]
}
```

**FHIR CarePlan:**
```json
{
  "period": {
    "start": "2024-01-15",
    "end": "2024-04-15"
  },
  "contributor": [
    {
      "reference": "Practitioner/1234567890"
    }
  ]
}
```

**Mapping Notes:**
- serviceEvent `effectiveTime` → both Composition.event.period AND CarePlan.period
- serviceEvent `performer` → CarePlan.contributor (US Core Must Support element)
- serviceEvent performers also contribute to care team context (may create separate CareTeam resource)

### Composition Status Mapping

C-CDA documents don't have explicit status, but Composition.status is derived from document state:

| C-CDA Document State | FHIR Composition.status | Notes |
|---------------------|------------------------|-------|
| Authenticated/signed document | `final` | Most common for Care Plan documents |
| Draft/incomplete document | `preliminary` | Document in progress |
| Replaced by newer version | `amended` | When setId/versionNumber indicates update |
| Document created in error | `entered-in-error` | Rare; when document should not exist |

**Default Mapping:** Use `final` for authenticated Care Plan documents

### Confidentiality Mapping

| C-CDA confidentialityCode | FHIR Composition.confidentiality |
|---------------------------|----------------------------------|
| `N` (Normal) | `N` |
| `R` (Restricted) | `R` |
| `V` (Very restricted) | `V` |

### Section Mappings

#### Health Concerns Section → Composition.section + Conditions

**C-CDA:**
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
  <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
        displayName="Health concerns document"/>
  <title>HEALTH CONCERNS</title>
  <text>
    <table>
      <thead><tr><th>Concern</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td ID="concern1">Respiratory insufficiency</td><td>Active</td></tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.132" extension="2015-08-01"/>
      <id root="concern-act-123"/>
      <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
      <statusCode code="active"/>
      <effectiveTime><low value="20240115"/></effectiveTime>

      <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
          <id root="problem-obs-456"/>
          <value xsi:type="CD" code="409623005" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Respiratory insufficiency"/>
        </observation>
      </entryRelationship>
    </act>
  </entry>
</section>
```

**FHIR Composition.section:**
```json
{
  "section": [
    {
      "title": "HEALTH CONCERNS",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "75310-3",
            "display": "Health concerns document"
          }
        ]
      },
      "text": {
        "status": "generated",
        "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><thead><tr><th>Concern</th><th>Status</th></tr></thead><tbody><tr><td>Respiratory insufficiency</td><td>Active</td></tr></tbody></table></div>"
      },
      "entry": [
        {
          "reference": "Condition/problem-obs-456"
        }
      ]
    }
  ]
}
```

**FHIR CarePlan:**
```json
{
  "addresses": [
    {
      "reference": "Condition/problem-obs-456",
      "display": "Respiratory insufficiency"
    }
  ]
}
```

#### Goals Section → Composition.section + Goals

**C-CDA:**
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
  <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"
        displayName="Goals"/>
  <title>GOALS</title>
  <text><!-- narrative --></text>

  <entry typeCode="DRIV">
    <observation classCode="OBS" moodCode="GOL">
      <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
      <id root="goal-obs-123"/>
      <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
            displayName="Oxygen saturation"/>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
    </observation>
  </entry>
</section>
```

**FHIR Composition.section:**
```json
{
  "section": [
    {
      "title": "GOALS",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "61146-7",
            "display": "Goals"
          }
        ]
      },
      "entry": [
        {
          "reference": "Goal/goal-obs-123"
        }
      ]
    }
  ]
}
```

**FHIR CarePlan:**
```json
{
  "goal": [
    {
      "reference": "Goal/goal-obs-123"
    }
  ]
}
```

#### Interventions Section → Composition.section + Activities

**C-CDA:**
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
  <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"
        displayName="Interventions Provided"/>
  <title>INTERVENTIONS</title>
  <text><!-- narrative --></text>

  <entry typeCode="DRIV">
    <act classCode="ACT" moodCode="INT">
      <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
      <id root="intervention-act-123"/>
      <code code="362956003" codeSystem="2.16.840.1.113883.6.96"
            displayName="Procedure/intervention"/>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>

      <entryRelationship typeCode="COMP">
        <act classCode="ACT" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.12" extension="2014-06-09"/>
          <code code="371907003" codeSystem="2.16.840.1.113883.6.96"
                displayName="Oxygen administration by nasal cannula"/>
          <statusCode code="active"/>
        </act>
      </entryRelationship>
    </act>
  </entry>
</section>
```

**FHIR Composition.section:**
```json
{
  "section": [
    {
      "title": "INTERVENTIONS",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "62387-6",
            "display": "Interventions Provided"
          }
        ]
      },
      "entry": [
        {
          "reference": "ServiceRequest/intervention-act-123"
        }
      ]
    }
  ]
}
```

**FHIR CarePlan:**
```json
{
  "activity": [
    {
      "reference": {
        "reference": "ServiceRequest/intervention-act-123"
      }
    }
  ]
}
```

#### Intervention MoodCode Mapping

| C-CDA moodCode | FHIR Resource Type | CarePlan.activity Mapping |
|----------------|-------------------|---------------------------|
| INT (Intent - Planned) | ServiceRequest (intent="plan") | reference → ServiceRequest |
| EVN (Event - Completed) | Procedure (status="completed") | reference → Procedure |

#### Outcomes Section → Composition.section + Observations

**C-CDA:**
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
  <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"
        displayName="Patient problem outcome"/>
  <title>HEALTH STATUS EVALUATIONS AND OUTCOMES</title>
  <text><!-- narrative --></text>

  <entry typeCode="DRIV">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
      <id root="outcome-obs-123"/>
      <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
            displayName="Oxygen saturation"/>
      <statusCode code="completed"/>
      <effectiveTime value="20240120"/>
      <value xsi:type="PQ" value="95" unit="%"/>

      <entryRelationship typeCode="GEVL">
        <observation classCode="OBS" moodCode="GOL">
          <id root="goal-obs-123"/>
        </observation>
      </entryRelationship>
    </observation>
  </entry>
</section>
```

**FHIR Composition.section:**
```json
{
  "section": [
    {
      "title": "HEALTH STATUS EVALUATIONS AND OUTCOMES",
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "11383-7",
            "display": "Patient problem outcome"
          }
        ]
      },
      "entry": [
        {
          "reference": "Observation/outcome-obs-123"
        }
      ]
    }
  ]
}
```

**FHIR CarePlan (activity outcome):**
```json
{
  "activity": [
    {
      "outcomeReference": [
        {
          "reference": "Observation/outcome-obs-123"
        }
      ]
    }
  ]
}
```

### CarePlan Status Mapping

The CarePlan status is derived from document and intervention status:

| C-CDA Document Context | FHIR CarePlan.status |
|------------------------|----------------------|
| Recent document, active interventions | `active` |
| Document with all completed interventions | `completed` |
| Document marked as superseded | `revoked` |
| Document in error | `entered-in-error` |

**Mapping Logic:**
1. If document has active planned interventions → `active`
2. If all interventions completed and period.end passed → `completed`
3. If document is superseded (replacedBy relationship) → `revoked`
4. Default for current care plan documents → `active`

### CarePlan Category and Intent

**Fixed Mappings:**
```json
{
  "intent": "plan",
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
          "code": "assess-plan",
          "display": "Assessment and Plan of Treatment"
        }
      ]
    }
  ]
}
```

### Text/Narrative Mapping

The CarePlan narrative should summarize assessment and plan from all sections:

**C-CDA (from all section narratives):**
```xml
<!-- Health Concerns narrative -->
<text>Patient presents with respiratory insufficiency...</text>

<!-- Goals narrative -->
<text>Goals: Maintain oxygen saturation >92%...</text>

<!-- Interventions narrative -->
<text>Interventions: Oxygen therapy, elevation of head of bed...</text>
```

**FHIR CarePlan.text:**
```json
{
  "text": {
    "status": "generated",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h3>Assessment</h3><p>Patient presents with respiratory insufficiency and productive cough.</p><h3>Plan</h3><p>Goals: Maintain oxygen saturation >92% through supplemental oxygen. Interventions: Oxygen therapy at 2L/min, elevation of head of bed, pulmonary toilet.</p></div>"
  }
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings: Composition + CarePlan → Care Plan Document

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Composition.identifier` | ClinicalDocument `id` | Identifier → II |
| `Composition.type` | ClinicalDocument `code` | Fixed to 52521-2 |
| `Composition.title` | ClinicalDocument `title` | String |
| `Composition.date` | ClinicalDocument `effectiveTime` | Timestamp |
| `Composition.subject` | `recordTarget` | Create patient role |
| `Composition.author` | `author` | Create assigned author |
| `Composition.custodian` | `custodian` | Create custodian org |
| `CarePlan.period` | serviceEvent `effectiveTime` | Period → interval |
| `CarePlan.addresses` | Health Concerns Section entries | Create Health Concern Acts |
| `CarePlan.goal` | Goals Section entries | Reference Goal Observations |
| `CarePlan.activity` | Interventions Section entries | Create Intervention Acts |

### Status Mapping: FHIR to C-CDA

| FHIR CarePlan.status | C-CDA Intervention moodCode | C-CDA statusCode |
|----------------------|----------------------------|------------------|
| `draft` | INT (intent) | `new` |
| `active` | INT (intent) | `active` |
| `completed` | EVN (event) | `completed` |
| `revoked` | INT (intent) | `cancelled` |
| `entered-in-error` | Use @negationInd="true" | N/A |

## Complete Example

### C-CDA Input (Abbreviated)

```xml
<ClinicalDocument>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="careplan-12345"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>

  <recordTarget><!-- Patient: Amy Shaw --></recordTarget>
  <author><!-- Dr. Smith --></author>
  <custodian><!-- Hospital --></custodian>

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <component>
        <section><!-- Health Concerns: Respiratory insufficiency --></section>
      </component>
      <component>
        <section><!-- Goals: Oxygen saturation >92% --></section>
      </component>
      <component>
        <section><!-- Interventions: Oxygen therapy --></section>
      </component>
      <component>
        <section><!-- Outcomes: SpO2 95% --></section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

### FHIR Output Bundle

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-1",
      "resource": {
        "resourceType": "Composition",
        "meta": {
          "profile": [
            "http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document"
          ]
        },
        "identifier": [
          {
            "value": "urn:uuid:careplan-12345"
          }
        ],
        "status": "final",
        "type": {
          "coding": [
            {
              "system": "http://loinc.org",
              "code": "52521-2",
              "display": "Overall plan of care/advance care directives"
            }
          ]
        },
        "subject": {
          "reference": "Patient/patient-1"
        },
        "date": "2024-01-15T12:00:00-05:00",
        "author": [
          {
            "reference": "Practitioner/dr-smith"
          }
        ],
        "title": "Care Plan",
        "custodian": {
          "reference": "Organization/hospital"
        },
        "event": [
          {
            "period": {
              "start": "2024-01-15",
              "end": "2024-04-15"
            },
            "detail": [
              {
                "reference": "CarePlan/careplan-1"
              }
            ]
          }
        ],
        "section": [
          {
            "title": "HEALTH CONCERNS",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "75310-3"
                }
              ]
            },
            "entry": [
              {
                "reference": "Condition/respiratory-insufficiency"
              }
            ]
          },
          {
            "title": "GOALS",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "61146-7"
                }
              ]
            },
            "entry": [
              {
                "reference": "Goal/oxygen-saturation"
              }
            ]
          },
          {
            "title": "INTERVENTIONS",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "62387-6"
                }
              ]
            },
            "entry": [
              {
                "reference": "ServiceRequest/oxygen-therapy"
              }
            ]
          },
          {
            "title": "OUTCOMES",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "11383-7"
                }
              ]
            },
            "entry": [
              {
                "reference": "Observation/spo2-result"
              }
            ]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:careplan-1",
      "resource": {
        "resourceType": "CarePlan",
        "meta": {
          "profile": [
            "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan"
          ]
        },
        "text": {
          "status": "generated",
          "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h3>Assessment</h3><p>Patient presents with respiratory insufficiency.</p><h3>Plan</h3><p>Goals: Maintain oxygen saturation >92%. Interventions: Oxygen therapy at 2L/min via nasal cannula.</p></div>"
        },
        "identifier": [
          {
            "value": "urn:uuid:careplan-12345"
          }
        ],
        "status": "active",
        "intent": "plan",
        "category": [
          {
            "coding": [
              {
                "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                "code": "assess-plan"
              }
            ]
          }
        ],
        "subject": {
          "reference": "Patient/patient-1"
        },
        "period": {
          "start": "2024-01-15",
          "end": "2024-04-15"
        },
        "author": {
          "reference": "Practitioner/dr-smith"
        },
        "addresses": [
          {
            "reference": "Condition/respiratory-insufficiency"
          }
        ],
        "goal": [
          {
            "reference": "Goal/oxygen-saturation"
          }
        ],
        "activity": [
          {
            "reference": {
              "reference": "ServiceRequest/oxygen-therapy"
            },
            "outcomeReference": [
              {
                "reference": "Observation/spo2-result"
              }
            ]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:patient-1",
      "resource": {
        "resourceType": "Patient"
      }
    },
    {
      "fullUrl": "urn:uuid:respiratory-insufficiency",
      "resource": {
        "resourceType": "Condition"
      }
    },
    {
      "fullUrl": "urn:uuid:oxygen-saturation",
      "resource": {
        "resourceType": "Goal"
      }
    },
    {
      "fullUrl": "urn:uuid:oxygen-therapy",
      "resource": {
        "resourceType": "ServiceRequest"
      }
    },
    {
      "fullUrl": "urn:uuid:spo2-result",
      "resource": {
        "resourceType": "Observation"
      }
    }
  ]
}
```

## Implementation Notes

### US Core and C-CDA on FHIR Compliance

**Composition Requirements:**
1. **SHALL** support all C-CDA on FHIR Care Plan Document profile requirements
2. **SHALL** include all required sections (Health Concerns, Goals)
3. **SHOULD** include recommended sections (Interventions, Outcomes)
4. **SHALL** include narrative text for each section
5. **SHALL** reference appropriate FHIR resources in section entries

**CarePlan Requirements:**
1. **SHALL** support US Core CarePlan profile requirements
2. **SHALL** include status, intent, category (assess-plan), subject
3. **SHALL** support text.status and text.div
4. **SHALL** support contributor element (USCDI requirement)
5. **SHOULD** include addresses (Condition references)
6. **SHOULD** include goal (Goal references)

### Bundle Structure

The conversion produces a FHIR Document Bundle with:
1. **First entry:** Composition resource (required)
2. **Subsequent entries:** All referenced resources (Patient, Practitioner, Organization, CarePlan, Condition, Goal, ServiceRequest, Observation, etc.)

### Missing Data Handling

| C-CDA Missing | FHIR Handling | Notes |
|---------------|---------------|-------|
| No service event period | Use document effectiveTime for CarePlan.period | US Core CarePlan doesn't require period |
| No author | Use document author for CarePlan.author | Author is optional in base CarePlan |
| No interventions | Omit CarePlan.activity | Activity is optional |
| No goals | Omit CarePlan.goal | Goal is optional |
| Empty section (with nullFlavor) | Create section with emptyReason | Composition allows emptyReason |

### Contributor Mapping

Map multiple authors, participants, and service event performers to CarePlan.contributor:

**C-CDA:**
```xml
<author><!-- Dr. Smith --></author>
<author><!-- Nurse Jones --></author>
<participant typeCode="IND"><!-- Patient --></participant>
<documentationOf>
  <serviceEvent>
    <performer typeCode="PRF"><!-- Care coordinator --></performer>
  </serviceEvent>
</documentationOf>
```

**FHIR CarePlan:**
```json
{
  "author": {
    "reference": "Practitioner/dr-smith"
  },
  "contributor": [
    {
      "reference": "Practitioner/dr-smith"
    },
    {
      "reference": "Practitioner/nurse-jones"
    },
    {
      "reference": "Patient/patient-1"
    },
    {
      "reference": "Practitioner/care-coordinator"
    }
  ]
}
```

**Mapping Rules:**
1. Map **all** document authors → CarePlan.contributor
2. Map **first** author → CarePlan.author
3. Map **all** participants → CarePlan.contributor
4. Map **all** serviceEvent performers → CarePlan.contributor
5. US Core requires contributor as Must Support (USCDI requirement)

### CareTeam Resource Consideration

**When to Create a Separate CareTeam Resource:**

Create a separate CareTeam resource when:
- Multiple performers have **specific documented roles** (e.g., primary physician, care coordinator, social worker)
- The care team has a formal structure with lead practitioner designation
- Care team participation includes start/end dates for specific members
- Care team represents a persistent organizational unit

**When to Use Only CarePlan.contributor:**

Use only CarePlan.contributor when:
- Care team structure is simple (1-3 contributors)
- No specific roles or responsibilities are documented
- No temporal aspects to team membership
- Care plan is authored by a single provider or simple group

**Example with CareTeam:**

```json
{
  "resourceType": "CarePlan",
  "contributor": [
    {
      "reference": "Practitioner/dr-smith"
    },
    {
      "reference": "Practitioner/nurse-jones"
    },
    {
      "reference": "Practitioner/social-worker"
    }
  ],
  "careTeam": [
    {
      "reference": "CareTeam/respiratory-care-team"
    }
  ]
}
```

```json
{
  "resourceType": "CareTeam",
  "id": "respiratory-care-team",
  "subject": {
    "reference": "Patient/patient-1"
  },
  "participant": [
    {
      "role": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "446050000",
              "display": "Primary care physician"
            }
          ]
        }
      ],
      "member": {
        "reference": "Practitioner/dr-smith"
      }
    },
    {
      "role": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "224565004",
              "display": "Care coordinator"
            }
          ]
        }
      ],
      "member": {
        "reference": "Practitioner/nurse-jones"
      }
    }
  ]
}
```

### Activity Detail vs Reference

**Preferred:** Use `activity.reference` when discrete FHIR resources exist (ServiceRequest, Procedure, etc.)

**Alternative:** Use `activity.detail` for inline definition when resources aren't separately managed

**Mapping Logic:**
- Planned interventions (moodCode=INT) → ServiceRequest with `intent="plan"`
- Completed interventions (moodCode=EVN) → Procedure with `status="completed"`
- Map intervention code, status, effective time, and performers

## References

- [C-CDA on FHIR Care Plan Document](https://hl7.org/fhir/us/ccda/StructureDefinition-Care-Plan-Document.html)
- [US Core CarePlan Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan)
- [FHIR R4B CarePlan Resource](https://hl7.org/fhir/R4B/careplan.html)
- [FHIR R4B Composition Resource](https://hl7.org/fhir/R4B/composition.html)
- [C-CDA Care Plan Specification](https://hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.1.15.html)
- [C-CDA Example: Care Plan](https://github.com/HL7/C-CDA-Examples/blob/master/Documents/Care%20Plan/Care_Plan.xml)
- [C-CDA on FHIR IG v1.2.0](https://hl7.org/fhir/us/ccda/)
- [US Core IG v8.0.1](http://hl7.org/fhir/us/core/STU8/)
- [Care Plan Goals and Instructions Example](https://cdasearch.hl7.org/examples/view/Plan%20of%20Treatment/Care%20Plan%20Goals%20and%20Instructions)
