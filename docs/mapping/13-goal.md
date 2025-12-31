# Goal Mapping: C-CDA Goal ↔ FHIR Goal

This document provides detailed mapping guidance between C-CDA Goal Observation and FHIR `Goal` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Goals Section (`2.16.840.1.113883.10.20.22.2.60`) | Container for goals |
| Goal Observation (`2.16.840.1.113883.10.20.22.4.121`) | `Goal` |
| Section: Goals (LOINC `61146-7`) | Resource type determined from template |

## Structural Mapping

Each **Goal Observation** within the Goals Section maps to a separate FHIR `Goal` resource.

```
Goals Section (section)
└── entry
    └── observation [Goal Observation]
        ├── @moodCode="GOL" → (identifies as Goal, not observation)
        ├── id → Goal.identifier
        ├── code → Goal.description
        ├── statusCode → Goal.lifecycleStatus
        ├── effectiveTime/low → Goal.startDate
        ├── effectiveTime/high → Goal.target.dueDate
        ├── author → Goal.expressedBy
        └── entryRelationship
            ├── Priority Preference → Goal.priority
            ├── Entry Reference (Health Concern) → Goal.addresses
            ├── Progress Toward Goal → Goal.achievementStatus
            └── Component Goal → Goal.target (measure + detail)
```

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| Goal Observation `id` | `identifier` | ID → Identifier |
| Goal Observation `code` | `description` | CodeableConcept |
| Goal Observation `statusCode` | `lifecycleStatus` | [Status ConceptMap](#lifecycle-status-mapping) |
| Goal Observation `effectiveTime/low` | `startDate` | Date conversion |
| Goal Observation `effectiveTime/high` | `target.dueDate` | Date conversion |
| Goal Observation `author` (first/only) | `expressedBy` | Reference(Patient \| Practitioner) |
| Priority Preference `value` | `priority` | [Priority ConceptMap](#priority-mapping) |
| Entry Reference `value` | `addresses` | Reference(Condition \| Observation) |
| Progress Toward Goal `value` | `achievementStatus` | [Achievement ConceptMap](#achievement-status-mapping) |
| Component Goal `code` | `target.measure` | CodeableConcept |
| Component Goal `value` | `target.detail[x]` | PQ → Quantity, IVL → Range, CD → CodeableConcept |

### Lifecycle Status Mapping

The C-CDA `statusCode` maps to FHIR `lifecycleStatus`:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <statusCode code="active"/>
</observation>
```

**Status ConceptMap:**

| C-CDA statusCode | FHIR lifecycleStatus | Notes |
|------------------|----------------------|-------|
| `active` | `active` | Goal is being actively pursued |
| `completed` | `completed` | Goal has been achieved |
| `cancelled` | `cancelled` | Goal was abandoned |
| `suspended` | `on-hold` | Goal temporarily suspended |
| `aborted` | `cancelled` | Goal was stopped without completion |

**FHIR:**
```json
{
  "lifecycleStatus": "active"
}
```

### Description Mapping

The Goal Observation `code` element maps to FHIR `description`:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <code code="289169006" codeSystem="2.16.840.1.113883.6.96"
        displayName="Weight loss">
    <originalText>
      <reference value="#goal1"/>
    </originalText>
  </code>
  <text>
    <reference value="#goal1"/>
  </text>
</observation>
```

**FHIR:**
```json
{
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "289169006",
        "display": "Weight loss"
      }
    ],
    "text": "Lose 20 pounds over the next 6 months"
  }
}
```

**Implementation Notes:**
- Extract human-readable text from narrative section using `text/reference` or `originalText/reference`
- If `code` has translations, include as additional `coding` elements
- Prefer specific goal codes from SNOMED CT or LOINC

### Start and Target Date Mapping

**C-CDA:**
```xml
<effectiveTime>
  <low value="20240115"/>
  <high value="20240715"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "startDate": "2024-01-15",
  "target": [
    {
      "dueDate": "2024-07-15"
    }
  ]
}
```

**Date Conversion Rules:**
- `effectiveTime/low` → `startDate` (YYYYMMDD → YYYY-MM-DD)
- `effectiveTime/high` → `target.dueDate` (YYYYMMDD → YYYY-MM-DD)
- If only high is present, omit startDate (US Core requires at least one of startDate or target.dueDate)
- Handle partial dates according to FHIR date format rules

**Null Flavor Handling:**
```xml
<effectiveTime>
  <low nullFlavor="UNK"/>
  <high value="20240715"/>
</effectiveTime>
```
Maps to:
```json
{
  "target": [
    {
      "dueDate": "2024-07-15"
    }
  ]
}
```

### Author Mapping (expressedBy)

The `author` element identifies who established the goal.

**C-CDA (Patient Goal):**
```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20240115"/>
  <assignedAuthor>
    <id root="patient-id-system" extension="patient-123"/>
  </assignedAuthor>
</author>
```

**FHIR:**
```json
{
  "expressedBy": {
    "reference": "Patient/patient-123"
  }
}
```

**C-CDA (Provider Goal):**
```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20240115"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>John</given>
        <family>Smith</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR:**
```json
{
  "expressedBy": {
    "reference": "Practitioner/1234567890",
    "display": "John Smith, MD"
  }
}
```

**Mapping Rules:**
- Use first author if multiple authors present
- Map to Patient reference if assignedAuthor references the patient
- Map to Practitioner reference if assignedAuthor includes NPI or provider details
- For negotiated goals (multiple authors), consider creating Provenance resource

### Priority Mapping

Priority is captured via the Priority Preference template nested within the Goal Observation.

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
    <code code="225773000" codeSystem="2.16.840.1.113883.6.96"
          displayName="Preference"/>
    <value xsi:type="CD" code="high-priority"
           codeSystem="http://terminology.hl7.org/CodeSystem/goal-priority"
           displayName="High Priority"/>
  </observation>
</entryRelationship>
```

**Priority ConceptMap:**

| C-CDA Priority Code | System | FHIR priority | Display |
|---------------------|--------|---------------|---------|
| `high-priority` | http://terminology.hl7.org/CodeSystem/goal-priority | `high-priority` | High Priority |
| `medium-priority` | http://terminology.hl7.org/CodeSystem/goal-priority | `medium-priority` | Medium Priority |
| `low-priority` | http://terminology.hl7.org/CodeSystem/goal-priority | `low-priority` | Low Priority |

**FHIR:**
```json
{
  "priority": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
        "code": "high-priority",
        "display": "High Priority"
      }
    ]
  }
}
```

### Achievement Status Mapping

Progress toward goal is captured via Progress Toward Goal Observation template.

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.110"/>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="in-progress"
           codeSystem="http://terminology.hl7.org/CodeSystem/goal-achievement"
           displayName="In Progress"/>
  </observation>
</entryRelationship>
```

**Achievement Status ConceptMap:**

| C-CDA Code | System | FHIR achievementStatus |
|------------|--------|------------------------|
| `in-progress` | http://terminology.hl7.org/CodeSystem/goal-achievement | `in-progress` |
| `improving` | http://terminology.hl7.org/CodeSystem/goal-achievement | `improving` |
| `worsening` | http://terminology.hl7.org/CodeSystem/goal-achievement | `worsening` |
| `no-change` | http://terminology.hl7.org/CodeSystem/goal-achievement | `no-change` |
| `achieved` | http://terminology.hl7.org/CodeSystem/goal-achievement | `achieved` |
| `sustaining` | http://terminology.hl7.org/CodeSystem/goal-achievement | `sustaining` |
| `not-achieved` | http://terminology.hl7.org/CodeSystem/goal-achievement | `not-achieved` |
| `no-progress` | http://terminology.hl7.org/CodeSystem/goal-achievement | `no-progress` |
| `not-attainable` | http://terminology.hl7.org/CodeSystem/goal-achievement | `not-attainable` |

**FHIR:**
```json
{
  "achievementStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
        "code": "in-progress",
        "display": "In Progress"
      }
    ]
  }
}
```

### Health Concern Reference (addresses)

Links goal to underlying health conditions via Entry Reference template.

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
    <id root="db734647-fc99-424c-a864-7e3cda82e704"/>
    <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
          displayName="Health Concern"/>
    <value xsi:type="CD" code="414915002" codeSystem="2.16.840.1.113883.6.96"
           displayName="Obesity"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "addresses": [
    {
      "reference": "Condition/db734647-fc99-424c-a864-7e3cda82e704",
      "display": "Obesity"
    }
  ]
}
```

**Mapping Rules:**
- Use Entry Reference `id` to locate corresponding Condition or Observation resource
- If resource not found, create contained resource with code from `value`
- typeCode "RSON" (has reason) indicates causal relationship

### Target Mapping (Component Goals)

Measurable targets are represented as component Goal Observations nested within the parent goal.

**C-CDA (Quantity Target):**
```xml
<entryRelationship typeCode="COMP">
  <observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <code code="29463-7" codeSystem="2.16.840.1.113883.6.1"
          displayName="Body weight"/>
    <value xsi:type="PQ" value="160" unit="[lb_av]"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "29463-7",
            "display": "Body weight"
          }
        ]
      },
      "detailQuantity": {
        "value": 160,
        "unit": "lb",
        "system": "http://unitsofmeasure.org",
        "code": "[lb_av]"
      }
    }
  ]
}
```

**C-CDA (Range Target):**
```xml
<entryRelationship typeCode="COMP">
  <observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
          displayName="Systolic blood pressure"/>
    <value xsi:type="IVL_PQ">
      <high value="140" unit="mm[Hg]"/>
    </value>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "detailRange": {
        "high": {
          "value": 140,
          "unit": "mm[Hg]",
          "system": "http://unitsofmeasure.org",
          "code": "mm[Hg]"
        }
      }
    }
  ]
}
```

**C-CDA (CodeableConcept Target):**
```xml
<entryRelationship typeCode="COMP">
  <observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
          displayName="Tobacco smoking status"/>
    <value xsi:type="CD" code="8517006" codeSystem="2.16.840.1.113883.6.96"
           displayName="Ex-smoker"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "72166-2",
            "display": "Tobacco smoking status"
          }
        ]
      },
      "detailCodeableConcept": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "8517006",
            "display": "Ex-smoker"
          }
        ]
      }
    }
  ]
}
```

**Data Type Mapping Rules:**

| C-CDA value xsi:type | FHIR target.detail[x] |
|----------------------|-----------------------|
| PQ (Physical Quantity) | detailQuantity |
| IVL_PQ (Interval) | detailRange |
| CD (Concept Descriptor) | detailCodeableConcept |
| ST (String) | detailString |
| BL (Boolean) | detailBoolean |
| INT (Integer) | detailInteger |
| RTO (Ratio) | detailRatio |

**Multiple Targets:**
Each component goal with typeCode="COMP" maps to a separate entry in the `target` array.

### Subject Mapping

The Goal subject is the patient referenced in the ClinicalDocument recordTarget.

**FHIR:**
```json
{
  "subject": {
    "reference": "Patient/patient-123"
  }
}
```

**Implementation Note:** Extract patient reference from document-level recordTarget/patientRole/id.

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `lifecycleStatus` | Goal Observation `statusCode` | Reverse status ConceptMap |
| `description` | Goal Observation `code` | CodeableConcept → CD |
| `subject` | ClinicalDocument `recordTarget` | Typically patient |
| `startDate` | `effectiveTime/low` | Date format conversion |
| `target.dueDate` | `effectiveTime/high` | Date format conversion |
| `target.measure` | Component Goal `code` | CodeableConcept → CD |
| `target.detail[x]` | Component Goal `value` | Type-specific conversion |
| `expressedBy` | `author` | Create Author Participation |
| `priority` | Priority Preference | Create nested observation |
| `achievementStatus` | Progress Toward Goal | Create nested observation |
| `addresses` | Entry Reference | Create nested observation with reference |

### FHIR lifecycleStatus to C-CDA statusCode

| FHIR lifecycleStatus | C-CDA statusCode | Notes |
|----------------------|------------------|-------|
| `proposed` | `active` | Not directly representable; use active |
| `planned` | `active` | Not directly representable; use active |
| `accepted` | `active` | Not directly representable; use active |
| `active` | `active` | Direct mapping |
| `on-hold` | `suspended` | Direct mapping |
| `completed` | `completed` | Direct mapping |
| `cancelled` | `cancelled` | Direct mapping |
| `entered-in-error` | Use `@negationInd="true"` | Special handling |
| `rejected` | `cancelled` | Map to cancelled |

### FHIR target.detail[x] to C-CDA value

| FHIR detail type | C-CDA value xsi:type | Conversion |
|------------------|----------------------|------------|
| detailQuantity | PQ | Map value, unit, system |
| detailRange | IVL_PQ | Map low/high bounds |
| detailCodeableConcept | CD | Map code, system, display |
| detailString | ST | Direct string value |
| detailBoolean | BL | Boolean value |
| detailInteger | INT | Integer value |
| detailRatio | RTO | Ratio numerator/denominator |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
  <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"
        displayName="Goals"/>
  <title>GOALS</title>
  <text>
    <table>
      <thead>
        <tr><th>Goal</th><th>Start</th><th>Target</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="goal1">Lose 20 pounds</td>
          <td>January 15, 2024</td>
          <td>July 15, 2024</td>
          <td>Active</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <observation classCode="OBS" moodCode="GOL">
      <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
      <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
      <code code="289169006" codeSystem="2.16.840.1.113883.6.96"
            displayName="Weight loss">
        <originalText>
          <reference value="#goal1"/>
        </originalText>
      </code>
      <text>
        <reference value="#goal1"/>
      </text>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240715"/>
      </effectiveTime>

      <!-- Patient as author -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20240115"/>
        <assignedAuthor>
          <id root="patient-system" extension="patient-123"/>
        </assignedAuthor>
      </author>

      <!-- Target: Body weight = 160 lbs -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
          <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
          <code code="29463-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Body weight"/>
          <value xsi:type="PQ" value="160" unit="[lb_av]"/>
        </observation>
      </entryRelationship>

      <!-- Priority: High -->
      <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
          <code code="225773000" codeSystem="2.16.840.1.113883.6.96"
                displayName="Preference"/>
          <value xsi:type="CD" code="high-priority"
                 codeSystem="http://terminology.hl7.org/CodeSystem/goal-priority"
                 displayName="High Priority"/>
        </observation>
      </entryRelationship>

      <!-- Addresses: Obesity -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
          <id root="condition-obesity-123"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                displayName="Health Concern"/>
          <value xsi:type="CD" code="414915002" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Obesity"/>
        </observation>
      </entryRelationship>

      <!-- Progress: In Progress -->
      <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.110"/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <value xsi:type="CD" code="in-progress"
                 codeSystem="http://terminology.hl7.org/CodeSystem/goal-achievement"
                 displayName="In Progress"/>
        </observation>
      </entryRelationship>
    </observation>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Goal",
  "id": "goal-weight-loss",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal"
    ]
  },
  "identifier": [
    {
      "system": "urn:ietf:rfc:3986",
      "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
    }
  ],
  "lifecycleStatus": "active",
  "achievementStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
        "code": "in-progress",
        "display": "In Progress"
      }
    ]
  },
  "priority": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
        "code": "high-priority",
        "display": "High Priority"
      }
    ]
  },
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "289169006",
        "display": "Weight loss"
      }
    ],
    "text": "Lose 20 pounds"
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "startDate": "2024-01-15",
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "29463-7",
            "display": "Body weight"
          }
        ]
      },
      "detailQuantity": {
        "value": 160,
        "unit": "lb",
        "system": "http://unitsofmeasure.org",
        "code": "[lb_av]"
      },
      "dueDate": "2024-07-15"
    }
  ],
  "expressedBy": {
    "reference": "Patient/patient-123"
  },
  "addresses": [
    {
      "reference": "Condition/condition-obesity-123",
      "display": "Obesity"
    }
  ]
}
```

## Special Cases

### Qualitative Goals Without Measurable Targets

Some goals are qualitative without specific numeric targets:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
  <id root="goal-quality-of-life"/>
  <code code="713458007" codeSystem="2.16.840.1.113883.6.96"
        displayName="Improving functional status"/>
  <text>Improve overall quality of life</text>
  <statusCode code="active"/>
  <effectiveTime>
    <low value="20240115"/>
  </effectiveTime>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Goal",
  "identifier": [
    {
      "value": "urn:uuid:goal-quality-of-life"
    }
  ],
  "lifecycleStatus": "active",
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "713458007",
        "display": "Improving functional status"
      }
    ],
    "text": "Improve overall quality of life"
  },
  "subject": {
    "reference": "Patient/example"
  },
  "startDate": "2024-01-15"
}
```

**Note:** No `target` array when goal lacks measurable targets. This is valid per US Core (target is optional).

### Social Determinants of Health (SDOH) Goals

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
  <id root="goal-housing"/>
  <code code="410518001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Establish living arrangements"/>
  <text>Secure stable housing within 3 months</text>
  <statusCode code="active"/>
  <effectiveTime>
    <low value="20240115"/>
    <high value="20240415"/>
  </effectiveTime>
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20240115"/>
    <assignedAuthor>
      <!-- Social worker details -->
    </assignedAuthor>
  </author>
  <entryRelationship typeCode="RSON">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
      <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
            displayName="Health Concern"/>
      <value xsi:type="CD" code="Z59.1" codeSystem="2.16.840.1.113883.6.90"
             displayName="Inadequate housing"/>
    </observation>
  </entryRelationship>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Goal",
  "identifier": [
    {
      "value": "urn:uuid:goal-housing"
    }
  ],
  "lifecycleStatus": "active",
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/sdoh-clinicalcare/CodeSystem/SDOHCC-CodeSystemTemporaryCodes",
          "code": "housing-instability",
          "display": "Housing Instability"
        }
      ]
    }
  ],
  "description": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "410518001",
        "display": "Establish living arrangements"
      }
    ],
    "text": "Secure stable housing within 3 months"
  },
  "subject": {
    "reference": "Patient/example"
  },
  "startDate": "2024-01-15",
  "target": [
    {
      "dueDate": "2024-04-15"
    }
  ],
  "expressedBy": {
    "reference": "Practitioner/social-worker"
  },
  "addresses": [
    {
      "reference": "Condition/homelessness"
    }
  ]
}
```

**Implementation Note:** Infer SDOH category from goal code or related health concern (ICD-10 Z-codes indicate SDOH).

### Multiple Component Targets

Goals may have multiple measurable targets (e.g., blood pressure with systolic and diastolic components):

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Blood pressure panel with all children optional"/>
  <!-- ... -->
  <entryRelationship typeCode="COMP">
    <observation classCode="OBS" moodCode="GOL">
      <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
            displayName="Systolic blood pressure"/>
      <value xsi:type="IVL_PQ">
        <high value="140" unit="mm[Hg]"/>
      </value>
    </observation>
  </entryRelationship>
  <entryRelationship typeCode="COMP">
    <observation classCode="OBS" moodCode="GOL">
      <code code="8462-4" codeSystem="2.16.840.1.113883.6.1"
            displayName="Diastolic blood pressure"/>
      <value xsi:type="IVL_PQ">
        <high value="90" unit="mm[Hg]"/>
      </value>
    </observation>
  </entryRelationship>
</observation>
```

**FHIR:**
```json
{
  "target": [
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "detailRange": {
        "high": {
          "value": 140,
          "unit": "mm[Hg]",
          "system": "http://unitsofmeasure.org",
          "code": "mm[Hg]"
        }
      }
    },
    {
      "measure": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8462-4",
            "display": "Diastolic blood pressure"
          }
        ]
      },
      "detailRange": {
        "high": {
          "value": 90,
          "unit": "mm[Hg]",
          "system": "http://unitsofmeasure.org",
          "code": "mm[Hg]"
        }
      }
    }
  ]
}
```

### Negotiated Goals (Multiple Authors)

When both patient and provider contribute to goal formulation:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="GOL">
  <!-- ... -->
  <author>
    <time value="20240115"/>
    <assignedAuthor>
      <!-- Patient -->
    </assignedAuthor>
  </author>
  <author>
    <time value="20240115"/>
    <assignedAuthor>
      <!-- Provider -->
    </assignedAuthor>
  </author>
</observation>
```

**FHIR:**
Map first author to `expressedBy`, document additional authors via Provenance:
```json
{
  "expressedBy": {
    "reference": "Patient/example"
  }
}
```

And create Provenance:
```json
{
  "resourceType": "Provenance",
  "target": [
    {
      "reference": "Goal/example"
    }
  ],
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
        "reference": "Patient/example"
      }
    },
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
        "reference": "Practitioner/provider"
      }
    }
  ]
}
```

## Implementation Notes

### US Core Compliance

To ensure US Core Goal profile compliance:

1. **SHALL** include `lifecycleStatus` (from C-CDA statusCode)
2. **SHALL** include `description` (from C-CDA code)
3. **SHALL** include `subject` (from document recordTarget)
4. **SHALL** include either `startDate` OR `target.dueDate` (from effectiveTime/low or /high)
5. **SHALL** include `expressedBy` (from author)

### Missing Data Handling

| C-CDA Missing | FHIR Handling | Notes |
|---------------|---------------|-------|
| No author | Omit `expressedBy` (not required by base FHIR) | US Core requires; use document author |
| No effectiveTime | Use document effectiveTime for startDate | US Core requires startDate or target.dueDate |
| No component goals | Omit `target` array | Valid - not all goals are measurable |
| No priority | Omit `priority` | Optional element |
| No progress | Omit `achievementStatus` | Optional element |

### Reference Resolution

Entry References require resolving to actual FHIR resources:

1. Extract `id` from Entry Reference observation
2. Search for corresponding Condition/Observation resource with matching identifier
3. If not found, create contained resource or use display-only reference
4. Prefer resolved references over contained resources for interoperability

### Category Inference

C-CDA doesn't explicitly categorize goals. Infer from context:

| Goal Code Pattern | Suggested Category |
|-------------------|-------------------|
| Dietary/nutrition codes | dietary |
| Activity/exercise codes | behavioral |
| Medical outcome codes | treatment |
| SDOH codes (housing, employment) | Appropriate SDOH category |

## References

- [C-CDA on FHIR IG](http://build.fhir.org/ig/HL7/ccda-on-fhir/) - Note: Goal mapping not yet published
- [US Core Goal Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal)
- [C-CDA Goals Section](https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.2.60.html)
- [C-CDA Goal Observation](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-GoalObservation.html)
- [FHIR R4B Goal Resource](https://hl7.org/fhir/R4B/goal.html)
