# C-CDA: Problem Observation

## Overview

The **Problem Observation** contains the actual problem/diagnosis information including the specific diagnosis or condition details (e.g., the clinical reality). Problem Observations are always contained within a Problem Concern Act. A single Problem Concern Act can contain multiple Problem Observations to represent the evolution of a condition over time.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.4` |
| Template Version | 2015-08-01 (R2.1), 2024-05-01 (R5.0) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ProblemObservation` |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Problem Section]
                └── entry
                    └── act [Problem Concern Act]
                        └── entryRelationship [@typeCode='SUBJ']
                            └── observation [Problem Observation]
                                ├── templateId [@root='2.16.840.1.113883.10.20.22.4.4']
                                └── value (diagnosis code)
```

## XML Structure

```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
  <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
  <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
        displayName="Problem">
    <translation code="75326-9" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Problem"/>
  </code>
  <text>
    <reference value="#problem1"/>
  </text>
  <statusCode code="completed"/>
  <effectiveTime>
    <low value="20100301"/>
  </effectiveTime>

  <!-- Problem Code (ICD-10, SNOMED, etc.) -->
  <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"
         displayName="Essential (primary) hypertension">
    <originalText>
      <reference value="#problem1"/>
    </originalText>
    <translation code="59621000" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Essential hypertension"/>
  </value>

  <!-- Target Site (optional) -->
  <targetSiteCode code="368209003" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Right arm"/>

  <!-- Problem Status Observation (optional) -->
  <entryRelationship typeCode="REFR">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.6" extension="2019-06-20"/>
      <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"
            displayName="Status"/>
      <statusCode code="completed"/>
      <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
             displayName="Active"/>
    </observation>
  </entryRelationship>

  <!-- Severity Observation (optional) -->
  <entryRelationship typeCode="REFR">
     <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.8" extension="2014-06-09"/>
        <code code="SEV" codeSystem="2.16.840.1.113883.5.4" displayName="Severity observation"/>
        <text><reference value="#severity1"/></text>
        <statusCode code="completed"/>
        <value xsi:type="CD" code="255604002" codeSystem="2.16.840.1.113883.6.96" displayName="Mild"/>
     </observation>
  </entryRelationship>

  <!-- Age at Onset (optional) -->
  <entryRelationship typeCode="SUBJ" inversionInd="true">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.31"/>
      <code code="445518008" codeSystem="2.16.840.1.113883.6.96"
            displayName="Age at onset"/>
      <statusCode code="completed"/>
      <value xsi:type="PQ" value="35" unit="a"/>
    </observation>
  </entryRelationship>

  <!-- Health Status Observation (optional) -->
  <entryRelationship typeCode="REFR">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.5" extension="2014-06-09"/>
      <code code="11323-3" codeSystem="2.16.840.1.113883.6.1"
            displayName="Health status"/>
      <statusCode code="completed"/>
      <value xsi:type="CD" code="81323004" codeSystem="2.16.840.1.113883.6.96"
             displayName="Alive and well"/>
    </observation>
  </entryRelationship>

  <!-- Prognosis Observation (optional) -->
  <entryRelationship typeCode="REFR">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.113"/>
      <code code="75328-5" codeSystem="2.16.840.1.113883.6.1"
            displayName="Prognosis"/>
      <statusCode code="completed"/>
      <value xsi:type="CD" code="170968001" codeSystem="2.16.840.1.113883.6.96"
             displayName="Prognosis good"/>
    </observation>
  </entryRelationship>

</observation>
```

## Element Details

*   **Class Code**: `OBS`
*   **Mood Code**: `EVN`

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.4` | 1..* | SHALL |
| id | Unique identifier for the observation | 1..* | SHALL |
| code | Problem type code (e.g., Problem, Symptom) | 1..1 | SHALL |
| statusCode | Status of the observation, must be `completed` | 1..1 | SHALL |
| effectiveTime | Biologically relevant time of the condition | 1..1 | SHALL |
| effectiveTime/low | Onset date | 1..1 | SHALL |
| effectiveTime/high | Resolution/abatement date (Use `nullFlavor="UNK"` if resolved but unknown date) | 0..1 | MAY |
| value | Diagnosis code (ICD/SNOMED) | 1..1 | SHALL |
| targetSiteCode | Anatomical location | 0..1 | SHOULD |
| author | Clinician who observed/documented | 0..* | SHOULD |
| performer | Clinician who performed the observation | 0..* | MAY |
| entryRelationship | Relationships to other observations (Status, Severity, etc.) | 0..* | MAY |

### observation/code (Problem Type)

The type of problem being documented.

**Problem Type Codes - Preferred Binding (VSAC `2.16.840.1.113762.1.4.1267.1`):**
| Code | Display | Description |
|------|---------|-------------|
| 55607006 | Problem | General problem |
| 404684003 | Finding | Clinical finding |
| 282291009 | Diagnosis | Clinical diagnosis |
| 64572001 | Condition | Disease or condition |
| 248536006 | Symptom | Symptom |
| 418799008 | Complaint | Chief complaint |
| 373930000 | Cognitive function finding | Cognitive issues |

**LOINC Translations (ValueSet `2.16.840.1.113762.1.4.1099.28`):**
| Code | Display |
|------|---------|
| 75326-9 | Problem |
| 75325-1 | Symptom |
| 75324-4 | Functional status |
| 75323-6 | Cognitive function |

### observation/value (Diagnosis Code)

The specific diagnosis or condition code.

**Value Set Binding:** US Core Condition Codes (Preferred)

**Common Code Systems:**
| OID | URI | Name | Use |
|-----|-----|------|-----|
| 2.16.840.1.113883.6.90 | `http://hl7.org/fhir/sid/icd-10-cm` | ICD-10-CM | Diagnoses (US) |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT | Clinical terms |
| 2.16.840.1.113883.6.103 | `http://hl7.org/fhir/sid/icd-9-cm` | ICD-9-CM | Legacy diagnoses |
| 2.16.840.1.113883.6.4 | `http://www.icd10data.com/icd10pcs` | ICD-10-PCS | Procedures |

**Post-Coordination:**
The `value` element **MAY** contain zero or more `qualifier` elements to refine the meaning of the primary code (e.g., severity, laterality) if a pre-coordinated code is not available.

**Social Determinants of Health (SDOH):**
If the problem is a Social Determinant of Health Observation, the `value` **SHOULD** be selected from the ValueSet *Social Determinants of Health Conditions* (2.16.840.1.113762.1.4.1196.788). This is a USCDI requirement for SDOH Problems/Health Concerns categorization.

### Problem Status Observation

Documents whether the problem is currently active from a clinical perspective.

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.6` | 1..1 | SHALL |
| code | `33999-4` (Status) from LOINC | 1..1 | SHALL |
| value | Status code (SNOMED) | 1..1 | SHALL |

**Status Codes (SNOMED):**
| Code | Display | FHIR clinicalStatus |
|------|---------|---------------------|
| 55561003 | Active | active |
| 73425007 | Inactive | inactive |
| 413322009 | Resolved | resolved |
| 277022003 | Remission | remission |
| 255227004 | Recurrence | recurrence |

### Severity Observation (optional)

Documents the severity of the problem.

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.8` | 1..1 | SHALL |
| code | `SEV` (Severity observation) from ActCode | 1..1 | SHALL |
| value | Severity code (SNOMED) | 1..1 | SHALL |

**Severity Codes (SNOMED):**
| Code | Display |
|------|---------|
| 255604002 | Mild |
| 6736007 | Moderate |
| 24484000 | Severe |

### Health Status Observation (optional)

Documents the patient's overall health status related to this condition.

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.5` | 1..1 | SHALL |
| code | `11323-3` (Health status) from LOINC | 1..1 | SHALL |
| value | Health status code (SNOMED) | 1..1 | SHALL |

**Health Status Codes (SNOMED):**
| Code | Display |
|------|---------|
| 81323004 | Alive and well |
| 313386006 | In remission |
| 162467007 | Symptom free |
| 161901003 | Chronically ill |
| 271593001 | Severely ill |
| 21134002 | Disability |
| 135818000 | Dependent |

### Prognosis Observation (optional)

Documents the anticipated health outcome related to the problem.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.113` |
| code | `75328-5` (Prognosis) from LOINC |
| value | Prognosis code (SNOMED) |

### Age at Onset Observation (optional)

Documents the patient's age when the problem began.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.31` |
| code | `445518008` (Age at onset) from SNOMED |
| value | Physical quantity with unit |

### Target Site Code (optional)

Documents the anatomical location of the problem.

| Element | Description |
|---------|-------------|
| code | Anatomical location code (SNOMED) |

### Priority Preference (optional)

Documents the priority of the problem.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.143` |
| code | `225773000` (Preference) from SNOMED |
| value | Priority level (SNOMED) |

### Author Participation (optional)

Identifies the clinician who authored the observation.

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` | 1..1 | SHALL |
| time | Time of authorship | 1..1 | SHALL |
| assignedAuthor | Author details | 1..1 | SHALL |
| assignedAuthor/id | Author identifier | 1..* | SHALL |

### Performer Participation (optional)

Identifies the clinician who performed the observation (e.g., the person who asserted the diagnosis). This is distinct from the author, who may have just recorded it.

*   **Type Code**: `PRF` (Performer)

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| assignedEntity | Performer details | 1..1 | SHALL |
| assignedEntity/id | Performer identifier | 1..* | SHALL |
| assignedEntity/code | Type of performer | 0..1 | MAY |

### Informant Participation (optional)

Identifies the source of information for the observation (e.g., patient, relative, caregiver), especially when the information is reported rather than directly observed.

*   **Type Code**: `INF` (Informant)

| Element | Description | Card | Conf |
|---------|-------------|------|------|
| relatedEntity | Informant details (if person) | 0..1 | MAY |
| relatedEntity/code | Relationship to patient | 0..1 | MAY |

## Constraints & Business Rules

1.  **Clinical Status**:
    *   The clinical status (e.g., active, resolved, in remission) is carried in the Problem Observation via `effectiveTime` or a specific Status Observation.
    *   This is distinct from the Problem Concern Act's `statusCode` which reflects the provider's concern status.

2.  **Problem Type Translation**:
    *   If the `observation/code` is selected from the ValueSet *Problem Type (SNOMEDCT)* (`2.16.840.1.113883.3.88.12.3221.7.2`), it **SHALL** have at least one `translation` element.
    *   The `translation` **SHOULD** be selected from the ValueSet *Problem Type (LOINC)* (`2.16.840.1.113762.1.4.1099.28`).

3.  **Effective Time Constraints**:
    *   `effectiveTime/low` **SHALL** be present.
    *   `effectiveTime/high` **SHALL** be present if the condition is resolved.
    *   If resolution date is unknown, `effectiveTime/high` **SHOULD** be present with `nullFlavor="UNK"`.

## No Known Problems

When documenting that a patient has no known problems, use `negationInd="true"` on the Problem Observation.

```xml
<observation classCode="OBS" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
  <id root="..."/>
  <!-- Code can be 55607006 (Problem) or 64572001 (Disease) -->
  <code code="64572001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Disease (disorder)"/>
  <statusCode code="completed"/>
  <effectiveTime>
    <low nullFlavor="NA"/>
  </effectiveTime>
  <!-- Value matches code -->
  <value xsi:type="CD" code="64572001" codeSystem="2.16.840.1.113883.6.96"
         displayName="Disease (disorder)"/>
</observation>
```

**Note:** The `code` and `value` should generally match. Common patterns include asserting "No known problems" or "No known diseases".

## Category Mapping

Problem observations can be categorized based on the section they appear in:

| Section LOINC | Section Name | FHIR Category |
|---------------|--------------|---------------|
| 11450-4 | Problem list | problem-list-item |
| 10160-0 | History of medication use | problem-list-item |
| 11348-0 | History of past illness | encounter-diagnosis |
| 29545-1 | Physical findings | encounter-diagnosis |

## Conformance Requirements

1. **SHALL** contain exactly one [1..1] `templateId` with root `2.16.840.1.113883.10.20.22.4.4`.
2. **SHALL** contain at least one [1..*] `id`.
3. **SHALL** contain exactly one [1..1] `code`.
4. **SHALL** contain exactly one [1..1] `statusCode` with `code="completed"`.
5. **SHALL** contain exactly one [1..1] `effectiveTime`.
    *   **SHALL** contain `low`.
    *   **SHALL** contain `high` if the problem is resolved.
6. **SHALL** contain exactly one [1..1] `value` with `xsi:type="CD"`.
7. **SHOULD** contain zero or one [0..1] `targetSiteCode`.
8. **SHOULD** contain zero or more [0..*] `author`.
9. **MAY** contain `performer`.
10. **MAY** contain `entryRelationship` for Priority, Status, Severity, Health Status.

## USCDI Requirements

| Element | USCDI Data Element |
|---------|-------------------|
| effectiveTime/low | Date of Onset (problem initiation) |
| effectiveTime/high | Date of Resolution (condition closure) |
| value | SDOH Problems/Health Concerns categorization |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| should-author | Warning | Author participation recommended |
| should-text-ref-value | Warning | Text reference to narrative section recommended |
| value-starts-octothorpe | Error | Text references must start with '#' |

## Optional Entry Relationships

| Relationship | Template | Type Code | Description |
|--------------|----------|-----------|-------------|
| Age Observation | `2.16.840.1.113883.10.20.22.4.31` | SUBJ | Age at onset |
| Prognosis Observation | `2.16.840.1.113883.10.20.22.4.113` | REFR | Anticipated outcome |
| Priority Preference | `2.16.840.1.113883.10.20.22.4.143` | REFR | Priority level |
| Problem Status | `2.16.840.1.113883.10.20.22.4.6` | REFR | Clinical status |
| Date of Diagnosis Act | N/A | COMP | Diagnosis timing |
| Assessment Scale Observation | `2.16.840.1.113883.10.20.22.4.69` | COMP | Supporting assessment |
| Entry Reference | `2.16.840.1.113883.10.20.22.4.122` | REFR | Supporting documentation |

## Clinical Context Notes

The template acknowledges real-world implementation variability: onset dates, diagnosis dates, and recorded dates represent distinct concepts but EHR systems rarely distinguish them. Implementations should anticipate inconsistency in timestamp precision and availability across these three temporal markers.

## Related Templates

- [Problem Concern Act](problem-concern-act.ccda.md) - The container act that holds this observation

## References

- C-CDA R2.1 Implementation Guide Section 3.79 (Problem Observation)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- SNOMED CT: http://snomed.info/sct
- ICD-10-CM: https://www.cdc.gov/nchs/icd/icd10cm.htm
