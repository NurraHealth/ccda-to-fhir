# C-CDA: Goals Section and Goal Observation

## Overview

The Goals Section in C-CDA documents patient health goals established by providers, patients, or both collaboratively. Goals represent desired health outcomes and target states that guide care planning and patient-centered interventions. The section contains Goal Observation entries that capture specific measurable or qualitative objectives.

## Template Information

### Goals Section

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.2.60` |
| Template Name | Goals Section |
| Template Version | 2015-08-01 |
| LOINC Code | 61146-7 |
| LOINC Display | Goals |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/GoalsSection` |
| Parent Template | Section |

### Goal Observation

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.121` |
| Template Name | Goal Observation |
| Template Version | 2022-06-01 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/GoalObservation` |
| Context | Entry within Goals Section or Plan of Treatment Section |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Goals Section]
                ├── code (61146-7 "Goals")
                ├── title
                ├── text (narrative)
                └── entry [@typeCode='DRIV']
                    └── observation [Goal Observation]
                        ├── id
                        ├── code
                        ├── value (goal description)
                        ├── author (who set the goal)
                        ├── effectiveTime (start/target dates)
                        ├── entryRelationship [Priority Preference]
                        ├── entryRelationship [Entry Reference to Health Concern]
                        └── entryRelationship [Progress Toward Goal]
```

## XML Structure

```xml
<section>
  <!-- Goals Section Template -->
  <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
  <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"
        codeSystemName="LOINC" displayName="Goals"/>
  <title>GOALS</title>
  <text>
    <table border="1" width="100%">
      <thead>
        <tr>
          <th>Goal</th>
          <th>Start Date</th>
          <th>Target Date</th>
          <th>Status</th>
          <th>Author</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td ID="goal1">Lose 20 pounds</td>
          <td>January 15, 2024</td>
          <td>July 15, 2024</td>
          <td>Active</td>
          <td>Patient</td>
        </tr>
        <tr>
          <td ID="goal2">Lower blood pressure to less than 140/90 mmHg</td>
          <td>January 15, 2024</td>
          <td>April 15, 2024</td>
          <td>In Progress</td>
          <td>Dr. Smith</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <!-- Goal Observation: Weight Loss -->
    <observation classCode="OBS" moodCode="GOL">
      <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
      <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
      <code code="289169006" codeSystem="2.16.840.1.113883.6.96"
            codeSystemName="SNOMED CT" displayName="Weight loss">
        <originalText>
          <reference value="#goal1"/>
        </originalText>
      </code>
      <text>
        <reference value="#goal1"/>
      </text>
      <statusCode code="active"/>
      <effectiveTime>
        <!-- Start date -->
        <low value="20240115"/>
        <!-- Target achievement date -->
        <high value="20240715"/>
      </effectiveTime>
      <!-- Goal author: Patient -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20240115"/>
        <assignedAuthor>
          <!-- Reference to patient as author -->
          <id root="2.16.840.1.113883.4.6" extension="patient-123"
              assigningAuthorityName="Patient ID"/>
        </assignedAuthor>
      </author>
      <!-- Target value using entryRelationship -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
          <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
          <code code="29463-7" codeSystem="2.16.840.1.113883.6.1"
                codeSystemName="LOINC" displayName="Body weight"/>
          <value xsi:type="PQ" value="160" unit="[lb_av]"/>
        </observation>
      </entryRelationship>
      <!-- Priority Preference -->
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
      <!-- Reference to related health concern -->
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
    </observation>
  </entry>

  <entry typeCode="DRIV">
    <!-- Goal Observation: Blood Pressure Control -->
    <observation classCode="OBS" moodCode="GOL">
      <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
      <id root="ab734647-fc99-424c-a864-7e3cda82e709"/>
      <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"
            codeSystemName="LOINC" displayName="Blood pressure panel with all children optional">
        <translation code="75367002" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Blood pressure"/>
      </code>
      <text>
        <reference value="#goal2"/>
      </text>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
      <!-- Goal author: Provider -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20240115"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="npi-1234567890"/>
          <addr>
            <streetAddressLine>123 Medical Dr</streetAddressLine>
            <city>Springfield</city>
            <state>IL</state>
            <postalCode>62701</postalCode>
          </addr>
          <telecom use="WP" value="tel:+1-217-555-1234"/>
          <assignedPerson>
            <name>
              <given>John</given>
              <family>Smith</family>
              <suffix>MD</suffix>
            </name>
          </assignedPerson>
        </assignedAuthor>
      </author>
      <!-- Target value: Systolic BP -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
          <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
          <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
                displayName="Systolic blood pressure"/>
          <!-- Range target -->
          <value xsi:type="IVL_PQ">
            <high value="140" unit="mm[Hg]"/>
          </value>
        </observation>
      </entryRelationship>
      <!-- Target value: Diastolic BP -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
          <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
          <code code="8462-4" codeSystem="2.16.840.1.113883.6.1"
                displayName="Diastolic blood pressure"/>
          <value xsi:type="IVL_PQ">
            <high value="90" unit="mm[Hg]"/>
          </value>
        </observation>
      </entryRelationship>
      <!-- Progress Toward Goal -->
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

## Element Details

### Goals Section (section)

The container section for all goal entries in the document.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.2.60` extension `2015-08-01` | Yes |
| code | LOINC `61146-7` "Goals" | Yes |
| title | Section title (typically "GOALS" or "Goals") | Yes |
| text | Human-readable narrative content | Yes |
| entry | Contains Goal Observation(s) | Should (at least one) |

### Goal Observation (observation)

Represents a specific health goal for the patient.

| Element | Description | Required |
|---------|-------------|----------|
| @classCode | OBS (Observation) | Yes |
| @moodCode | GOL (Goal) | Yes |
| templateId | `2.16.840.1.113883.10.20.22.4.121` extension `2022-06-01` | Yes |
| id | Unique identifier for the goal | Yes (at least one) |
| code | Goal code or category | Yes |
| text | Reference to narrative text | Should |
| statusCode | Goal status (active, completed, cancelled) | Yes |
| effectiveTime | Start and target dates | Should |

### @moodCode="GOL"

The moodCode of "GOL" (Goal) distinguishes this observation as representing an intended future state rather than a current observation. This is critical for proper interpretation.

### code

The code element identifies the type or category of goal.

**Common Goal Codes:**
| Code | System | Display |
|------|--------|---------|
| 289169006 | SNOMED CT | Weight loss |
| 160303001 | SNOMED CT | Weight gain |
| 85354-9 | LOINC | Blood pressure panel with all children optional |
| 410518001 | SNOMED CT | Establish living arrangements |
| 361231003 | SNOMED CT | Prescribed activity/exercise |
| 225773000 | SNOMED CT | Preference (for priority) |

**Value Set Binding:** US Core Goal Codes (preferred)

### text

Should contain a reference to the human-readable goal description in the narrative section.

```xml
<text>
  <reference value="#goal1"/>
</text>
```

### statusCode

Represents the lifecycle status of the goal.

| Code | Meaning |
|------|---------|
| active | Goal is currently being pursued |
| completed | Goal has been achieved |
| cancelled | Goal was abandoned |
| suspended | Goal pursuit is temporarily on hold |

**Note:** This differs from achievement status (progress toward goal).

### effectiveTime

Indicates when the goal was established and when achievement is targeted.

| Element | Description |
|---------|-------------|
| low | Goal start date (when goal was established or pursuit began) |
| high | Target achievement date ("achieve by" date) |

**Examples:**
```xml
<!-- Goal with start and target date -->
<effectiveTime>
  <low value="20240115"/>
  <high value="20240715"/>
</effectiveTime>

<!-- Goal with start date only -->
<effectiveTime>
  <low value="20240115"/>
</effectiveTime>

<!-- Goal with unknown start date -->
<effectiveTime>
  <low nullFlavor="UNK"/>
  <high value="20240715"/>
</effectiveTime>
```

### author

Identifies who established the goal (patient, provider, or both).

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` (Author Participation) |
| time | When the goal was authored |
| assignedAuthor | Author details |

**Author Types:**
- **Patient Goal:** assignedAuthor references the patient
- **Provider Goal:** assignedAuthor references the practitioner
- **Negotiated Goal:** Multiple author elements for both patient and provider

### value

For component goals (targets), the value element specifies the desired measurement or state.

**Value Types:**
- **PQ (Physical Quantity):** Numeric goals with units
  ```xml
  <value xsi:type="PQ" value="160" unit="[lb_av]"/>
  ```
- **IVL_PQ (Interval of Physical Quantity):** Range goals
  ```xml
  <value xsi:type="IVL_PQ">
    <high value="140" unit="mm[Hg]"/>
  </value>
  ```
- **CD (Concept Descriptor):** Coded target states
  ```xml
  <value xsi:type="CD" code="8517006" codeSystem="2.16.840.1.113883.6.96"
         displayName="Ex-smoker"/>
  ```

### entryRelationship (Component Goals)

Goals may have component sub-goals using `entryRelationship` with `@typeCode="COMP"`.

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

### entryRelationship (Priority Preference)

Optional priority indicator using Priority Preference template (`2.16.840.1.113883.10.20.22.4.143`).

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

**Priority Codes:**
| Code | System | Display |
|------|--------|---------|
| high-priority | http://terminology.hl7.org/CodeSystem/goal-priority | High Priority |
| medium-priority | http://terminology.hl7.org/CodeSystem/goal-priority | Medium Priority |
| low-priority | http://terminology.hl7.org/CodeSystem/goal-priority | Low Priority |

### entryRelationship (Health Concern Reference)

Links the goal to an underlying health concern using Entry Reference template (`2.16.840.1.113883.10.20.22.4.122`).

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

### entryRelationship (Progress Toward Goal)

Tracks achievement status using Progress Toward Goal Observation template (`2.16.840.1.113883.10.20.22.4.110`).

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

**Achievement Status Codes:**
| Code | System | Display |
|------|--------|---------|
| in-progress | http://terminology.hl7.org/CodeSystem/goal-achievement | In Progress |
| improving | http://terminology.hl7.org/CodeSystem/goal-achievement | Improving |
| worsening | http://terminology.hl7.org/CodeSystem/goal-achievement | Worsening |
| achieved | http://terminology.hl7.org/CodeSystem/goal-achievement | Achieved |
| not-achieved | http://terminology.hl7.org/CodeSystem/goal-achievement | Not Achieved |

## Conformance Requirements

### Goals Section
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.2.60`
2. **SHALL** contain exactly one `code` with code=`61146-7` from LOINC
3. **SHALL** contain exactly one `title`
4. **SHALL** contain exactly one `text` element
5. **SHOULD** contain at least one `entry` with Goal Observation

### Goal Observation
1. **SHALL** contain exactly one `@classCode="OBS"`
2. **SHALL** contain exactly one `@moodCode="GOL"`
3. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.121`
4. **SHALL** contain at least one `id`
5. **SHALL** contain exactly one `code`
6. **SHALL** contain exactly one `statusCode`
7. **SHOULD** contain exactly one `text`
8. **SHOULD** contain exactly one `effectiveTime`
9. **MAY** contain one or more `author` (Author Participation)
10. **MAY** contain one or more `entryRelationship` with Priority Preference
11. **MAY** contain one or more `entryRelationship` with Entry Reference (health concern)
12. **MAY** contain one or more `entryRelationship` with Progress Toward Goal Observation

## Special Cases

### Social Determinants of Health (SDOH) Goals

SDOH goals address non-medical factors affecting health:

```xml
<observation classCode="OBS" moodCode="GOL">
  <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
  <id root="c4734647-fc99-424c-a864-7e3cda82e705"/>
  <code code="410518001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Establish living arrangements"/>
  <text>
    <reference value="#goal-housing"/>
  </text>
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

**Common SDOH Goal Codes:**
| Code | System | Display |
|------|--------|---------|
| 410518001 | SNOMED CT | Establish living arrangements |
| 713458007 | SNOMED CT | Improving functional status |
| 160903007 | SNOMED CT | Full-time employment |

### Qualitative Goals Without Measurable Targets

Not all goals have specific numeric targets:

```xml
<observation classCode="OBS" moodCode="GOL">
  <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
  <id root="d5734647-fc99-424c-a864-7e3cda82e706"/>
  <code code="713458007" codeSystem="2.16.840.1.113883.6.96"
        displayName="Improving functional status"/>
  <text>Improve quality of life</text>
  <statusCode code="active"/>
  <effectiveTime>
    <low value="20240115"/>
  </effectiveTime>
</observation>
```

### Multiple Authors (Negotiated Goals)

When both patient and provider contribute:

```xml
<observation classCode="OBS" moodCode="GOL">
  <!-- ... -->
  <!-- Patient authored -->
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20240115"/>
    <assignedAuthor>
      <id root="patient-id-system" extension="patient-123"/>
    </assignedAuthor>
  </author>
  <!-- Provider authored -->
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20240115"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="npi-1234567890"/>
      <assignedPerson>
        <name>
          <given>John</given>
          <family>Smith</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
    </assignedAuthor>
  </author>
</observation>
```

## Document Context

Goals Section appears in the following C-CDA document types:
- **Care Plan** (2.16.840.1.113883.10.20.22.1.15) - **REQUIRED**
- Continuity of Care Document (CCD) - OPTIONAL
- Consultation Note - OPTIONAL
- Discharge Summary - OPTIONAL

Goals may also appear in the **Plan of Treatment Section** (2.16.840.1.113883.10.20.22.2.10) across various document types.

## Related Templates

| Template ID | Template Name | Usage |
|-------------|---------------|-------|
| 2.16.840.1.113883.10.20.22.4.119 | Author Participation | Identifies goal author |
| 2.16.840.1.113883.10.20.22.4.143 | Priority Preference | Goal priority |
| 2.16.840.1.113883.10.20.22.4.122 | Entry Reference | Links to health concerns |
| 2.16.840.1.113883.10.20.22.4.110 | Progress Toward Goal Observation | Achievement status |
| 2.16.840.1.113883.10.20.22.2.10 | Plan of Treatment Section | Alternative location for goals |

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.2.60.html
- HL7 Goal Observation Template: https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.121.html
- SNOMED CT: http://snomed.info/sct
- LOINC: http://loinc.org
- HL7 C-CDA Examples: https://github.com/HL7/C-CDA-Examples/tree/master/Goals
