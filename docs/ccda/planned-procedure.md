# C-CDA Planned Procedures and Acts (ServiceRequest Mapping)

## Overview

C-CDA represents planned, proposed, or ordered clinical activities using "planned" templates with specific moodCode values. These templates are used in the **Plan of Treatment Section** to document prospective, unfulfilled, or incomplete orders and requests.

**⚠️ IMPORTANT**: This document covers templates that map to FHIR **ServiceRequest** resources (future-oriented requests/orders). For completed interventions that map to FHIR **Procedure** resources, see separate documentation.

## Key Templates for Planned Activities

### 1. Planned Procedure (V2)

**Template ID**: `2.16.840.1.113883.10.20.22.4.41`

**Extension**: `2014-06-09` (C-CDA R2.1) or `2022-06-01` (C-CDA R3)

**OID**: http://hl7.org/cda/us/ccda/StructureDefinition/PlannedProcedure

**Purpose**: Represents "planned alterations of the patient's physical condition" such as surgical procedures, diagnostic procedures, or therapeutic interventions that are scheduled or proposed.

**FHIR Mapping**: ServiceRequest

### 2. Planned Act (V2)

**Template ID**: `2.16.840.1.113883.10.20.22.4.39`

**Extension**: `2014-06-09`

**Purpose**: Represents planned non-procedural clinical activities such as patient education, counseling, or administrative acts.

**FHIR Mapping**: ServiceRequest

## Plan of Treatment Section

**Template ID**: `2.16.840.1.113883.10.20.22.2.10`

**Extension**: `2014-06-09`

**LOINC Code**: `18776-5` ("Plan of care note")

### Section Purpose

Documents "pending orders, interventions, encounters, services, and procedures" for the patient. Limited to **prospective, unfulfilled, or incomplete** clinical activities indicated by specific moodCode values.

### Allowed Entry Types

The Plan of Treatment Section supports the following 11 entry types (per C-CDA specification):

1. **Planned Observation** (`2.16.840.1.113883.10.20.22.4.44`)
2. **Planned Encounter** (`2.16.840.1.113883.10.20.22.4.40`)
3. **Planned Act** (`2.16.840.1.113883.10.20.22.4.39`) - **Maps to ServiceRequest**
4. **Planned Procedure** (`2.16.840.1.113883.10.20.22.4.41`) - **Maps to ServiceRequest**
5. **Planned Medication Activity** (`2.16.840.1.113883.10.20.22.4.42`)
6. **Planned Supply** (`2.16.840.1.113883.10.20.22.4.43`)
7. **Planned Immunization Activity** (`2.16.840.1.113883.10.20.22.4.120`)
8. **Instruction** (`2.16.840.1.113883.10.20.22.4.20`)
9. **Handoff Communication Participants** (`2.16.840.1.113883.10.20.22.4.141`)
10. **Nutrition Recommendation** (`2.16.840.1.113883.10.20.22.4.130`)
11. **Goal Observation** (`2.16.840.1.113883.10.20.22.4.121`)

**Note**: Intervention Act (`2.16.840.1.113883.10.20.22.4.131`) is **NOT** an allowed entry type in Plan of Treatment Section. Intervention Act appears in the Interventions Section and always has moodCode=EVN (completed), mapping to Procedure, not ServiceRequest.

## Planned Procedure Template Specification

### Context

- **Parent**: Entry within Plan of Treatment Section
- **classCode**: `PROC` (Procedure, fixed)
- **moodCode**: Bound to "Planned moodCode (Act/Encounter/Procedure)" value set (required)

### Allowed moodCode Values

| moodCode | Name | Meaning | FHIR Mapping |
|----------|------|---------|--------------|
| **INT** | Intent | Planned intervention | ServiceRequest (intent=plan) |
| **RQO** | Request | Ordered procedure | ServiceRequest (intent=order) |
| **PRP** | Proposal | Proposed procedure | ServiceRequest (intent=proposal) |
| **ARQ** | Appointment Request | Appointment request | ServiceRequest (intent=order) |
| **PRMS** | Promise | Commitment to perform | ServiceRequest (intent=directive) |

**Note**: moodCode **EVN** (Event) indicates a completed procedure and should map to FHIR Procedure resource, NOT ServiceRequest.

### Mandatory Elements

#### templateId (1..*)

```xml
<templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
```

**Versions**:
- Extension `2014-06-09` (C-CDA R2.1)
- Extension `2022-06-01` (C-CDA R3)

#### id (1..*)

Unique identifier for the planned procedure.

```xml
<id root="db734647-fc99-424c-a864-7e3cda82e703"/>
```

**FHIR Mapping**: ServiceRequest.identifier

#### code (1..1)

Procedure being planned. Preferred binding to:
- **LOINC** (Logical Observation Identifiers Names and Codes)
- **SNOMED CT** (Systematized Nomenclature of Medicine Clinical Terms)
- **CPT** (Current Procedural Terminology)
- **ICD-10-PCS** (International Classification of Diseases, 10th Revision, Procedure Coding System)
- **HCPCS** (Healthcare Common Procedure Coding System)
- **CDT-2** (Code on Dental Procedures and Nomenclature)

```xml
<code code="73761001" codeSystem="2.16.840.1.113883.6.96"
      displayName="Colonoscopy"/>
```

**FHIR Mapping**: ServiceRequest.code

#### statusCode (1..1)

Fixed to **"active"** for planned procedures.

```xml
<statusCode code="active"/>
```

**FHIR Mapping**: ServiceRequest.status

### Recommended Elements (SHOULD)

#### text/reference (0..1)

Link to narrative text describing the planned procedure. Should begin with '#'.

```xml
<text>
  <reference value="#plan-proc-1"/>
</text>
```

#### effectiveTime (0..1)

When the procedure should occur or be performed.

```xml
<!-- Single date/time -->
<effectiveTime value="20240613"/>

<!-- Date range -->
<effectiveTime>
  <low value="20240601"/>
  <high value="20240630"/>
</effectiveTime>
```

**FHIR Mapping**: ServiceRequest.occurrence[x]

#### author (0..1)

Clinician who requested or planned the procedure.

```xml
<author>
  <time value="20240115140000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>Sarah</given>
        <family>Smith</family>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR Mapping**: ServiceRequest.authoredOn (from time), ServiceRequest.requester (from assignedAuthor)

### Optional Elements

#### methodCode (0..*)

Suggested method for performing the procedure.

```xml
<methodCode code="129304002" codeSystem="2.16.840.1.113883.6.96"
            displayName="Excision - action"/>
```

#### targetSiteCode (0..*)

Anatomical location where procedure should be performed. Binding to **Body Site Value Set**.

```xml
<targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                displayName="Colon structure"/>
```

**FHIR Mapping**: ServiceRequest.bodySite

#### performer (0..*)

Expected performer of the procedure.

```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <addr>
      <streetAddressLine>123 Main St</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>97214</postalCode>
    </addr>
    <telecom use="WP" value="tel:+1(555)555-1234"/>
    <assignedPerson>
      <name>
        <prefix>Dr.</prefix>
        <given>John</given>
        <family>Gastro</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</performer>
```

**FHIR Mapping**: ServiceRequest.performer

#### priorityCode (0..1)

Patient or provider priority indication.

```xml
<priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
              displayName="Routine"/>
```

**FHIR Mapping**: ServiceRequest.priority

### Contained Templates (EntryRelationships)

#### Priority Preference (0..*)

**typeCode**: `REFR` (Refers to)

**Template**: `2.16.840.1.113883.10.20.22.4.143`

Indicates patient or provider priority for this procedure.

```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
    <code code="225773000" codeSystem="2.16.840.1.113883.6.96"
          displayName="Preference"/>
    <value xsi:type="CD" code="LA6270-8" codeSystem="2.16.840.1.113883.6.1"
           displayName="High priority"/>
  </observation>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.priority

#### Indication (0..*)

**typeCode**: `RSON` (Reason)

**Template**: `2.16.840.1.113883.10.20.22.4.19` (Indication observation)

Clinical reason or justification for the planned procedure.

```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <id root="indication-123"/>
    <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
          displayName="Clinical finding"/>
    <statusCode code="completed"/>
    <value xsi:type="CD" code="428165003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Screening for colon cancer"/>
  </observation>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.reasonCode or ServiceRequest.reasonReference

#### Instructions (0..*)

**typeCode**: `SUBJ` (Subject, inversionInd="true")

**Template**: `2.16.840.1.113883.10.20.22.4.20` (Instruction)

Instructions for the patient regarding the procedure.

```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
    <code code="409073007" codeSystem="2.16.840.1.113883.6.96"
          displayName="Instruction"/>
    <text>Patient to follow bowel prep instructions 24 hours before procedure</text>
    <statusCode code="completed"/>
  </act>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.patientInstruction or ServiceRequest.note

#### Planned Coverage (0..*)

**typeCode**: `COMP` (Component)

**Template**: `2.16.840.1.113883.10.20.22.4.129` (Planned Coverage)

Insurance coverage information for the planned procedure.

```xml
<entryRelationship typeCode="COMP">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.129"/>
    <code code="48768-6" codeSystem="2.16.840.1.113883.6.1"
          displayName="Payment sources"/>
    <statusCode code="active"/>
    <entryRelationship typeCode="COMP">
      <act classCode="ACT" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.60"/>
        <!-- Coverage Activity template -->
      </act>
    </entryRelationship>
  </act>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.insurance

#### Assessment Scale Observations (0..*)

**typeCode**: `RSON` (Reason)

For SDOH (Social Determinants of Health) assessments supporting the planned procedure.

```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.69"/>
    <!-- Assessment Scale Observation -->
  </observation>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.supportingInfo

#### Entry References (0..*)

**typeCode**: `RSON` (Reason)

**Template**: `2.16.840.1.113883.10.20.22.4.122` (Entry Reference)

References to other clinical entries supporting the planned procedure.

```xml
<entryRelationship typeCode="RSON">
  <act classCode="ACT" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
    <id root="referenced-entry-id"/>
    <code nullFlavor="NP"/>
    <statusCode code="completed"/>
  </act>
</entryRelationship>
```

**FHIR Mapping**: ServiceRequest.reasonReference or ServiceRequest.supportingInfo

## Planned Act Template Specification

### Context

**Template ID**: `2.16.840.1.113883.10.20.22.4.39`

**Extension**: `2014-06-09`

- **classCode**: `ACT` (Act)
- **moodCode**: INT, RQO, PRP, ARQ, PRMS

### Use Cases

Planned Act is used for non-procedural clinical activities such as:
- Patient education sessions
- Counseling
- Administrative activities
- Care coordination tasks

### Key Differences from Planned Procedure

| Aspect | Planned Procedure | Planned Act |
|--------|-------------------|-------------|
| **classCode** | PROC | ACT |
| **Use** | Physical interventions | Non-procedural activities |
| **Examples** | Surgery, diagnostic tests | Education, counseling |

### Structure

The structure is similar to Planned Procedure with the same mandatory and optional elements:
- id, code, statusCode, text, effectiveTime, author
- entryRelationships for indications, instructions, coverage, etc.

## Complete Example: Planned Procedure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
  <code code="18776-5" codeSystem="2.16.840.1.113883.6.1"
        displayName="Plan of care note"/>
  <title>PLAN OF TREATMENT</title>
  <text>
    <table border="1" width="100%">
      <thead>
        <tr>
          <th>Planned Activity</th>
          <th>Planned Date</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        <tr ID="plan-proc-1">
          <td>Colonoscopy</td>
          <td>June 13, 2024</td>
          <td>Scheduled</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <procedure classCode="PROC" moodCode="RQO">
      <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
      <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
      <text>
        <reference value="#plan-proc-1"/>
      </text>
      <statusCode code="active"/>
      <effectiveTime value="20240613"/>

      <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
            displayName="Colonoscopy">
        <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
                     displayName="Colonoscopy, flexible, proximal to splenic flexure"/>
      </code>

      <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Colon structure"/>

      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
          <addr use="WP">
            <streetAddressLine>123 Gastro Lane</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>97214</postalCode>
          </addr>
          <telecom use="WP" value="tel:+1(555)555-5678"/>
          <assignedPerson>
            <name>
              <prefix>Dr.</prefix>
              <given>John</given>
              <family>Gastro</family>
            </name>
          </assignedPerson>
        </assignedEntity>
      </performer>

      <author>
        <time value="20240115140000-0500"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name>
              <given>Sarah</given>
              <family>Smith</family>
            </name>
          </assignedPerson>
        </assignedAuthor>
      </author>

      <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                    displayName="Routine"/>

      <!-- Indication -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
          <id root="indication-456"/>
          <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
                displayName="Clinical finding"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="428165003" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Screening for colon cancer"/>
        </observation>
      </entryRelationship>

      <!-- Patient Instructions -->
      <entryRelationship typeCode="SUBJ" inversionInd="true">
        <act classCode="ACT" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
          <code code="409073007" codeSystem="2.16.840.1.113883.6.96"
                displayName="Instruction"/>
          <text>Patient to follow bowel prep instructions 24 hours before procedure.
                NPO after midnight on day of procedure.</text>
          <statusCode code="completed"/>
        </act>
      </entryRelationship>

      <!-- Priority Preference -->
      <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
          <code code="225773000" codeSystem="2.16.840.1.113883.6.96"
                displayName="Preference"/>
          <value xsi:type="CD" code="LA6270-8" codeSystem="2.16.840.1.113883.6.1"
                 displayName="High priority"/>
        </observation>
      </entryRelationship>

    </procedure>
  </entry>
</section>
```

## Implementation Notes

### Common Practice

The specification notes that "common practice" uses Planned Procedure broadly for:
- Interventions and care activities
- Assessments (e.g., "Home Environment Evaluation")
- Evaluations (e.g., "Assessment of nutritional status")

This is regardless of whether the activity directly "alters physical condition."

### moodCode Validation

**CRITICAL**: When converting to FHIR, validate the moodCode:
- **moodCode=EVN** → Maps to **Procedure** resource (completed activity)
- **moodCode=INT/RQO/PRP** → Maps to **ServiceRequest** resource (planned activity)

### Missing Elements

C-CDA Planned Procedure may not include:
- **performer**: If not specified, ServiceRequest.performer should be omitted
- **effectiveTime**: If not specified, ServiceRequest.occurrence[x] should be omitted
- **priorityCode**: Default to "routine" in FHIR if not specified

### Relationship to Goals

When Planned Procedures or Planned Acts reference Goal Observations via entryRelationship[typeCode='RSON']:
- Create separate Goal resources
- Reference from ServiceRequest.supportingInfo
- This pattern is common in Care Plan documents

## Value Sets and Code Systems

### Body Site Value Set

OID: `2.16.840.1.113883.3.88.12.3221.8.9`

Binding: Preferred

Code System: SNOMED CT (`2.16.840.1.113883.6.96`)

### Priority Codes

OID: `2.16.840.1.113883.5.7` (ActPriority)

| Code | Display | FHIR Mapping |
|------|---------|--------------|
| R | Routine | routine |
| UR | Urgent | urgent |
| EM | Emergency | stat |
| EL | Elective | routine |
| A | ASAP | asap |

## References

- [C-CDA Planned Procedure Template](https://hl7.org/cda/us/ccda/2024Jan/StructureDefinition-PlannedProcedure.html)
- [C-CDA Planned Act Template](https://build.fhir.org/ig/HL7/CDA-ccda-2.2/StructureDefinition-2.16.840.1.113883.10.20.22.4.39.html)
- [C-CDA Plan of Treatment Section](https://build.fhir.org/ig/HL7/CDA-ccda-2.2/StructureDefinition-2.16.840.1.113883.10.20.22.2.10.html)
- [C-CDA Examples - Planned Procedure](https://github.com/HL7/C-CDA-Examples/tree/master/Guide%20Examples/Planned%20Procedure%20(V2)_2.16.840.1.113883.10.20.22.4.41)
- [C-CDA Online Documentation](https://www.hl7.org/ccdasearch/)

---

**Next Steps**: See [ServiceRequest Mapping Specification](../mapping/18-service-request.md) for conversion to FHIR.
