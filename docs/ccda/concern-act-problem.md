# C-CDA: Problem Concern Act

## Overview

The **Problem Concern Act** is a container that tracks the overall concern status for one or more problems/conditions. It represents whether the provider is still concerned about tracking the issue, not necessarily the clinical status of the condition itself. A single Problem Concern Act can contain multiple Problem Observations to represent the evolution of a condition over time.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.3` |
| Template Version | 2015-08-01 (R2.1), 2024-05-01 (R5.0) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ProblemConcernAct` |
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.5.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.5` |
| LOINC Code | 11450-4 |
| LOINC Display | Problem list - Reported |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Problem Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.5.1']
                ├── code [@code='11450-4']
                └── entry
                    └── act [Problem Concern Act]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.3']
                        └── entryRelationship [@typeCode='SUBJ']
                            └── observation [Problem Observation]
```

## XML Structure

```xml
<entry typeCode="DRIV">
  <!-- Problem Concern Act -->
  <act classCode="ACT" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.3" extension="2015-08-01"/>
    <id root="ec8a6ff8-ed4b-4f7e-82c3-e98e58b45de7"/>
    <code code="CONC" codeSystem="2.16.840.1.113883.5.6" displayName="Concern"/>
    <!-- Concern Status: active | suspended | aborted | completed -->
    <statusCode code="active"/>
    <effectiveTime>
      <low value="20100301"/>
      <!-- high value present if statusCode is completed/aborted -->
    </effectiveTime>
    <author>
      <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
      <time value="20100301"/>
      <assignedAuthor>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      </assignedAuthor>
    </author>

    <entryRelationship typeCode="SUBJ">
      <!-- Problem Observation (see problem-observation.ccda.md) -->
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
        <!-- ... -->
      </observation>
    </entryRelationship>
  </act>
</entry>
```

## Element Details

*   **Class Code**: `ACT`
*   **Mood Code**: `EVN`

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.3` | 1..* | SHALL |
| id | Unique identifier for the concern | 1..* | SHALL |
| code | `CONC` (Concern) from ActCode (`2.16.840.1.113883.5.6`) | 1..1 | SHALL |
| statusCode | State of the concern (`active`, `suspended`, `aborted`, `completed`) | 1..1 | SHALL |
| effectiveTime | Timeframe of the concern | 1..1 | SHALL |
| effectiveTime/low | When concern was first noted | 1..1 | SHALL |
| effectiveTime/high | When concern was resolved (Required if status is completed/aborted) | 0..1 | SHALL |
| author | Clinician who authored the concern | 0..* | SHOULD |
| entryRelationship | Contains Problem Observation (`typeCode="SUBJ"`) | 1..* | SHALL |

### Concern Status Codes

| Code | Display | Description |
|------|---------|-------------|
| active | Active | Concern is currently being tracked |
| completed | Completed | Concern has been resolved |
| aborted | Aborted | Concern was stopped before completion |
| suspended | Suspended | Concern is temporarily inactive |

### Author Participation (optional)

Identifies the clinician who authored the concern.

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` | 1..1 | SHALL |
| time | Time of authorship | 1..1 | SHALL |
| assignedAuthor | Author details | 1..1 | SHALL |
| assignedAuthor/id | Author identifier | 1..* | SHALL |

## Constraints & Business Rules

1.  **Concern vs. Problem Status**:
    *   The `statusCode` of the **Problem Concern Act** reflects the status of the *provider's concern* (e.g., "active" means the provider is still tracking it), not necessarily the clinical status of the condition.
    *   A `completed` Problem Concern Act means the provider is no longer concerned/tracking the issue, even if the patient still historically has it.

2.  **Entry Relationship**:
    *   The Problem Concern Act **SHALL** contain at least one Problem Observation (`typeCode="SUBJ"`).
    *   It **MAY** contain multiple Problem Observations to track the evolution of the condition (e.g., severity changes).

3.  **Effective Time Constraints**:
    *   `effectiveTime/low` **SHALL** be present.
    *   `effectiveTime/high` **SHALL** be present if `statusCode` is `completed` or `aborted`.

## No Known Problems

When documenting that a patient has no known problems, the Problem Concern Act wraps a negated Problem Observation.

```xml
<entry typeCode="DRIV">
  <act classCode="ACT" moodCode="EVN">
    <!-- Concern Act Wrapper -->
    <templateId root="2.16.840.1.113883.10.20.22.4.3" extension="2015-08-01"/>
    <id root="..."/>
    <code code="CONC" codeSystem="2.16.840.1.113883.5.6" displayName="Concern"/>
    <statusCode code="active"/>
    <effectiveTime><low value="20230101"/></effectiveTime>

    <entryRelationship typeCode="SUBJ">
      <!-- Negated Observation (see problem-observation.ccda.md) -->
      <observation classCode="OBS" moodCode="EVN" negationInd="true">
        <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
        <!-- ... -->
      </observation>
    </entryRelationship>
  </act>
</entry>
```

## Conformance Requirements

1. **SHALL** contain exactly one [1..1] `templateId` with root `2.16.840.1.113883.10.20.22.4.3`.
2. **SHALL** contain at least one [1..*] `id`.
3. **SHALL** contain exactly one [1..1] `code` with `code="CONC"`.
4. **SHALL** contain exactly one [1..1] `statusCode` (`active`, `suspended`, `aborted`, `completed`).
5. **SHALL** contain exactly one [1..1] `effectiveTime`.
    *   **SHALL** contain `low`.
    *   **SHALL** contain `high` if `statusCode` is `completed` or `aborted`.
6. **SHALL** contain at least one [1..*] `entryRelationship` with `typeCode="SUBJ"` containing a **Problem Observation**.
7. **MAY** contain `author` participation.

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| statusCode | ProblemAct statusCode (VSAC) | Required |
| languageCode | All Languages | Required |
| priorityCode | ActPriority (v3) | Example |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| 1198-7504 | Error | Active status requires effectiveTime/low boundary |
| 1198-10085 | Error | Completed status requires effectiveTime/high boundary |
| should-author | Warning | Author participation recommended |
| should-text-ref-value | Warning | Text reference to narrative section recommended |
| value-starts-octothorpe | Error | Text references must start with '#' |

## Entry Relationships

| Relationship | Template | Cardinality | Type Code |
|--------------|----------|-------------|-----------|
| Problem Observation | `2.16.840.1.113883.10.20.22.4.4` | 1..* | SUBJ (required) |
| Priority Preference | `2.16.840.1.113883.10.20.22.4.143` | 0..* | REFR (optional) |

## Related Templates

- [Problem Observation](problem-observation.ccda.md) - The observation contained within this act

## References

- C-CDA R2.1 Implementation Guide Section 3.78 (Problem Concern Act)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
