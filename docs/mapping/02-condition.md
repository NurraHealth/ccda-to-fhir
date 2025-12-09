# Condition Mapping: C-CDA Problem ↔ FHIR Condition

This document provides detailed mapping guidance between C-CDA Problem Concern Act / Problem Observation and FHIR `Condition` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Problem Concern Act (`2.16.840.1.113883.10.20.22.4.3`) | Container for tracking |
| Problem Observation (`2.16.840.1.113883.10.20.22.4.4`) | `Condition` |
| Section: Problem List (LOINC `11450-4`) | Category: `problem-list-item` |
| Section: Encounter Diagnosis | Category: `encounter-diagnosis` |

## Structural Mapping

Each **Problem Observation** within a Problem Concern Act maps to a separate FHIR `Condition` resource. The Problem Concern Act provides context (concern status, author) but does not create its own resource.

```
Problem Concern Act (act)
├── statusCode → Condition.clinicalStatus (fallback)
├── effectiveTime → (informational)
├── author → Condition.recorder + Provenance
└── entryRelationship/observation (Problem Observation)
    ├── id → Condition.identifier
    ├── code → Condition.category (problem type)
    ├── effectiveTime/low → Condition.onsetDateTime
    ├── effectiveTime/high → Condition.abatementDateTime
    ├── value → Condition.code
    └── entryRelationship (nested observations)
        ├── Problem Status → Condition.clinicalStatus
        ├── Age Observation → Condition.onsetAge
        └── Assessment Scale → Condition.evidence.detail
```

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| Section `code/@code` | `Condition.category` | [Section → Category](#category-mapping) |
| Problem Concern Act `statusCode` | `Condition.clinicalStatus` | Only if no Problem Status Observation |
| Problem Observation `negationInd="true"` | `Condition.verificationStatus` | Set to `refuted` |
| Problem Observation `id` | `Condition.identifier` | ID → Identifier |
| Problem Observation `code` | `Condition.category` | [Problem Type](#problem-type-mapping) |
| Problem Observation `effectiveTime/low` | `Condition.onsetDateTime` | Date conversion |
| Problem Observation `effectiveTime/high` | `Condition.abatementDateTime` | Date conversion |
| Problem Observation `value` | `Condition.code` | CodeableConcept |
| Problem Observation `targetSiteCode` | `Condition.bodySite` | CodeableConcept |
| Problem Observation `author` | `Condition.recorder` + Provenance | Use latest author |
| Problem Observation `author/time` | `Condition.recordedDate` | Use earliest time |
| Problem Status Observation `value` | `Condition.clinicalStatus` | [Status ConceptMap](#clinical-status-mapping) |
| Date of Diagnosis Act | `Condition.extension:assertedDate` | Date conversion |
| Age Observation `value` | `Condition.onsetAge` | Only if no onsetDateTime |
| Comment Activity `text` | `Condition.note` | Annotation |
| Supporting Observations | `Condition.evidence.detail` | Reference(Observation) |

### Category Mapping

The FHIR Condition category is determined by the C-CDA section:

| C-CDA Section LOINC | Section Name | FHIR Category |
|---------------------|--------------|---------------|
| `11450-4` | Problem List | `problem-list-item` |
| `10160-0` | History of Medication Use | `problem-list-item` |
| `11348-0` | History of Past Illness | `encounter-diagnosis` |
| `29545-1` | Physical Findings | `encounter-diagnosis` |
| `46240-8` | History of Hospitalizations | `encounter-diagnosis` |

**FHIR:**
```json
{
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-category",
      "code": "problem-list-item",
      "display": "Problem List Item"
    }]
  }]
}
```

### Problem Type Mapping

The Problem Observation `code` indicates the type of problem and maps to an additional category:

| C-CDA Code | Display | FHIR Category |
|------------|---------|---------------|
| `55607006` | Problem | problem-list-item |
| `404684003` | Finding | problem-list-item |
| `282291009` | Diagnosis | encounter-diagnosis |
| `64572001` | Condition | problem-list-item |
| `248536006` | Symptom | problem-list-item |
| `418799008` | Complaint | problem-list-item |

### Clinical Status Mapping

#### From Problem Status Observation

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.6"/>
    <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Active"/>
  </observation>
</entryRelationship>
```

**Problem Status ConceptMap:**

| C-CDA SNOMED Code | Display | FHIR clinicalStatus |
|-------------------|---------|---------------------|
| `55561003` | Active | `active` |
| `73425007` | Inactive | `inactive` |
| `413322009` | Resolved | `resolved` |
| `277022003` | Remission | `remission` |
| `255227004` | Recurrence | `recurrence` |

**FHIR:**
```json
{
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active",
      "display": "Active"
    }]
  }
}
```

#### From Problem Concern Act Status (Fallback)

If no Problem Status Observation is present, derive from the Problem Concern Act `statusCode`:

| CDA statusCode | FHIR clinicalStatus |
|----------------|---------------------|
| `active` | `active` |
| `completed` | `resolved` (if effectiveTime/high present) or `inactive` |
| `suspended` | `inactive` |
| `aborted` | `inactive` |

### Effective Time and Abatement

**C-CDA:**
```xml
<effectiveTime>
  <low value="20100301"/>
  <high value="20150615"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "onsetDateTime": "2010-03-01",
  "abatementDateTime": "2015-06-15"
}
```

**Clinical Status Constraint:**
If `effectiveTime/high` is present (or has `nullFlavor="UNK"`), the `clinicalStatus` must be one of: `inactive`, `remission`, or `resolved`.

**Unknown Resolution Date:**
```xml
<effectiveTime>
  <low value="20100301"/>
  <high nullFlavor="UNK"/>
</effectiveTime>
```

```json
{
  "onsetDateTime": "2010-03-01",
  "_abatementDateTime": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
      "valueCode": "unknown"
    }]
  },
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "resolved"
    }]
  }
}
```

### Diagnosis Code Mapping

**C-CDA:**
```xml
<value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"
       displayName="Essential (primary) hypertension">
  <originalText>
    <reference value="#problem1"/>
  </originalText>
  <translation code="59621000" codeSystem="2.16.840.1.113883.6.96"
               displayName="Essential hypertension"/>
</value>
```

**FHIR:**
```json
{
  "code": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "I10",
        "display": "Essential (primary) hypertension"
      },
      {
        "system": "http://snomed.info/sct",
        "code": "59621000",
        "display": "Essential hypertension"
      }
    ],
    "text": "Essential hypertension"
  }
}
```

### Negation Handling

When `negationInd="true"` on the Problem Observation:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
  <code code="64572001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Disease (disorder)"/>
  <value xsi:type="CD" code="64572001" codeSystem="2.16.840.1.113883.6.96"
         displayName="Disease (disorder)"/>
</observation>
```

**FHIR Options:**

1. **Set verificationStatus to refuted:**
```json
{
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "refuted"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "64572001",
      "display": "Disease (disorder)"
    }]
  }
}
```

2. **Use negated concept code:**
```json
{
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "160245001",
      "display": "No current problems or disability"
    }]
  }
}
```

### Age at Onset

**C-CDA:**
```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.31"/>
    <code code="445518008" codeSystem="2.16.840.1.113883.6.96"
          displayName="Age at onset"/>
    <value xsi:type="PQ" value="35" unit="a"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "onsetAge": {
    "value": 35,
    "unit": "years",
    "system": "http://unitsofmeasure.org",
    "code": "a"
  }
}
```

**Constraint:** Only one of `onsetAge` or `onsetDateTime` is permitted. If both are available, prefer `onsetDateTime`.

### Author and Provenance

**C-CDA:**
```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20100301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name><given>Adam</given><family>Careful</family></name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR Condition:**
```json
{
  "recorder": {
    "reference": "Practitioner/practitioner-example"
  },
  "recordedDate": "2010-03-01"
}
```

**FHIR Provenance (optional):**
```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "Condition/condition-example"}],
  "recorded": "2010-03-01T00:00:00Z",
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "author"
      }]
    },
    "who": {"reference": "Practitioner/practitioner-example"}
  }]
}
```

### Supporting Observations

Assessment scales and SDOH screening observations map to `evidence.detail`:

**C-CDA:**
```xml
<entryRelationship typeCode="COMP">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.69"/>
    <!-- Assessment Scale Observation -->
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "evidence": [{
    "detail": [{"reference": "Observation/assessment-observation"}]
  }]
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Condition.category` | Section placement + `code` | Determine section |
| `Condition.clinicalStatus` | Problem Status Observation | Create nested observation |
| `Condition.verificationStatus: refuted` | `negationInd="true"` | Set negation indicator |
| `Condition.code` | Problem Observation `value` | CodeableConcept → CD |
| `Condition.bodySite` | `targetSiteCode` | CodeableConcept → CD |
| `Condition.onsetDateTime` | `effectiveTime/low` | Date format conversion |
| `Condition.abatementDateTime` | `effectiveTime/high` | Date format conversion |
| `Condition.onsetAge` | Age Observation | Create nested observation |
| `Condition.recorder` | `author` | Create author participation |
| `Condition.recordedDate` | `author/time` | Date format conversion |
| `Condition.note` | Comment Activity | Create nested act |

### Clinical Status to Problem Status

| FHIR clinicalStatus | SNOMED Code | Display |
|---------------------|-------------|---------|
| `active` | `55561003` | Active |
| `inactive` | `73425007` | Inactive |
| `resolved` | `413322009` | Resolved |
| `remission` | `277022003` | Remission |
| `recurrence` | `255227004` | Recurrence |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
  <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
  <title>PROBLEM LIST</title>
  <entry typeCode="DRIV">
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
      <id root="ec8a6ff8-ed4b-4f7e-82c3-e98e58b45de7"/>
      <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20100301"/>
      </effectiveTime>
      <author>
        <time value="20100301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
          <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
          <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
                displayName="Problem">
            <translation code="75326-9" codeSystem="2.16.840.1.113883.6.1"/>
          </code>
          <statusCode code="completed"/>
          <effectiveTime>
            <low value="20100301"/>
          </effectiveTime>
          <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"
                 displayName="Essential (primary) hypertension">
            <translation code="59621000" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Essential hypertension"/>
          </value>
          <entryRelationship typeCode="REFR">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.6"/>
              <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"/>
              <statusCode code="completed"/>
              <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Active"/>
            </observation>
          </entryRelationship>
        </observation>
      </entryRelationship>
    </act>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Condition",
  "id": "condition-hypertension",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:ab1791b0-5c71-11db-b0de-0800200c9a66"
  }],
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
      "code": "active",
      "display": "Active"
    }]
  },
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
      "code": "confirmed"
    }]
  },
  "category": [
    {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/condition-category",
        "code": "problem-list-item",
        "display": "Problem List Item"
      }]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/icd-10-cm",
        "code": "I10",
        "display": "Essential (primary) hypertension"
      },
      {
        "system": "http://snomed.info/sct",
        "code": "59621000",
        "display": "Essential hypertension"
      }
    ],
    "text": "Essential hypertension"
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "onsetDateTime": "2010-03-01",
  "recordedDate": "2010-03-01",
  "recorder": {
    "reference": "Practitioner/practitioner-example"
  }
}
```

## References

- [C-CDA on FHIR Problems Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-problems.html)
- [US Core Condition Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition)
- [C-CDA Problem Concern Act](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.3.html)
- [C-CDA Problem Observation](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.4.html)
