# C-CDA Care Team Representation

**Standard:** HL7 CDA® R2 Implementation Guide: Consolidated CDA Templates for Clinical Notes R2.1 Companion Guide

**Primary Templates:**
- **Care Teams Section**: `2.16.840.1.113883.10.20.22.2.500` (2019-07-01, 2022-06-01)
- **Care Team Organizer**: `2.16.840.1.113883.10.20.22.4.500` (2019-07-01, 2022-06-01)
- **Care Team Member Act**: `2.16.840.1.113883.10.20.22.4.500.1` (2019-07-01, 2022-06-01)
- **Care Team Type Observation**: `2.16.840.1.113883.10.20.22.4.500.2` (2019-07-01)

**Alternative Representation:**
- **documentationOf/serviceEvent/performer**: Care team members in document header

---

## Overview

C-CDA supports two distinct approaches for representing care team information:

1. **Structured Section-Based Approach** (C-CDA R2.1 Companion Guide)
   - Care Teams Section with Care Team Organizer entries
   - Discrete, computable representation
   - Supports multiple care teams per patient
   - Each team can have types, leads, and multiple members

2. **Header-Based Approach** (Traditional C-CDA)
   - documentationOf/serviceEvent/performer elements
   - Simpler representation for transition-of-care documents
   - Lists key care team members in the document header
   - Less structured but widely implemented

Both approaches are valid; the structured section-based approach provides richer, more computable data.

---

## Approach 1: Structured Care Teams Section

### Care Teams Section

**Template ID:** `2.16.840.1.113883.10.20.22.2.500`

**Extensions:** 2019-07-01, 2022-06-01

**LOINC Code:** `85847-2` - "Patient Care team information"

**Purpose:** Contains one or more Care Team Organizer entries representing distinct care teams for the patient.

**Note:** The section uses LOINC `85847-2`, while the Care Team Organizer entries within use LOINC `86744-0` ("Care team").

#### Section Structure

```xml
<section>
  <!-- Care Teams Section Template -->
  <templateId root="2.16.840.1.113883.10.20.22.2.500" extension="2022-06-01"/>
  <code code="85847-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Patient Care team information"/>
  <title>CARE TEAMS</title>
  <text>
    <table>
      <thead>
        <tr>
          <th>Care Team</th>
          <th>Member Name</th>
          <th>Role</th>
          <th>Contact</th>
        </tr>
      </thead>
      <tbody>
        <tr ID="careteam-1">
          <td>Primary Care Team</td>
          <td>Dr. John Smith</td>
          <td>Primary Care Physician</td>
          <td>555-0100</td>
        </tr>
        <!-- Additional members -->
      </tbody>
    </table>
  </text>
  <!-- Care Team Organizer entries -->
  <entry typeCode="DRIV">
    <!-- Care Team Organizer here -->
  </entry>
</section>
```

#### Cardinality and Conformance

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| `templateId` | 1..* | SHALL | Must include root and extension |
| `code` | 1..1 | SHALL | 86744-0 (LOINC) |
| `title` | 1..1 | SHALL | Section title |
| `text` | 1..1 | SHALL | Human-readable narrative |
| `entry` | 1..* | SHALL | At least one Care Team Organizer |

---

### Care Team Organizer

**Template ID:** `2.16.840.1.113883.10.20.22.4.500`

**Extensions:** 2019-07-01, 2022-06-01

**Purpose:** Organizes information about a single care team, including its type, status, time period, lead, location, and members.

#### Organizer Structure

```xml
<entry typeCode="DRIV">
  <organizer classCode="CLUSTER" moodCode="EVN">
    <!-- Care Team Organizer Template -->
    <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>

    <!-- Unique identifier for this care team -->
    <id root="2.16.840.1.113883.19.5.99999.1" extension="careteam-primary-123"/>

    <!-- Code: Care Team -->
    <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"
          displayName="Care team">
      <originalText>
        <reference value="#careteam-1"/>
      </originalText>
    </code>

    <!-- Status: active, completed, aborted, etc. -->
    <statusCode code="active"/>

    <!-- Effective time: when this care team is/was active -->
    <effectiveTime>
      <low value="20230115"/>
      <!-- high value optional: omit for ongoing teams -->
    </effectiveTime>

    <!-- OPTIONAL: Reference to narrative text -->
    <sdtcText>
      <reference value="#careteam-1"/>
    </sdtcText>

    <!-- OPTIONAL: Care Team Lead (PPRF = Primary Performer) -->
    <participant typeCode="PPRF">
      <participantRole>
        <!-- ID must match one of the Care Team Member performer IDs -->
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <!-- OPTIONAL: Function code for the lead's specific role -->
        <sdtcFunctionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                         displayName="Primary Care Physician"/>
      </participantRole>
    </participant>

    <!-- OPTIONAL: Care Team Location -->
    <participant typeCode="LOC">
      <participantRole>
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
        <addr>
          <streetAddressLine>1001 Village Avenue</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>
        <telecom use="WP" value="tel:+1(555)555-5000"/>
        <playingEntity classCode="PLC">
          <name>Community Health and Hospitals</name>
        </playingEntity>
      </participantRole>
    </participant>

    <!-- OPTIONAL: Care Team Type -->
    <component>
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
        <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"
              displayName="Care team"/>
        <!-- Type of care team -->
        <value xsi:type="CD" code="LA27976-2" codeSystem="2.16.840.1.113883.6.1"
               displayName="Longitudinal care-coordination focused care team"/>
      </observation>
    </component>

    <!-- REQUIRED: Care Team Members (at least one) -->
    <component>
      <!-- Care Team Member Act -->
      <act classCode="PCPR" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>

        <!-- Use same code as organizer -->
        <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"
              displayName="Care team"/>

        <statusCode code="active"/>

        <!-- Effective time for this member's participation -->
        <effectiveTime>
          <low value="20230115"/>
        </effectiveTime>

        <!-- Performer: the actual care team member -->
        <performer>
          <!-- Function code: member's role in the care team -->
          <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                       displayName="Primary Care Physician"/>
          <assignedEntity>
            <!-- Provider identifier (NPI, institutional ID, etc.) -->
            <id root="2.16.840.1.113883.4.6" extension="1234567890"/>

            <!-- OPTIONAL: Provider taxonomy code -->
            <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                  displayName="Family Medicine Physician"/>

            <!-- Provider work address -->
            <addr use="WP">
              <streetAddressLine>1001 Village Avenue</streetAddressLine>
              <city>Portland</city>
              <state>OR</state>
              <postalCode>99123</postalCode>
            </addr>

            <!-- Provider contact -->
            <telecom use="WP" value="tel:+1(555)555-5100"/>

            <!-- Provider name -->
            <assignedPerson>
              <name>
                <prefix>Dr.</prefix>
                <given>John</given>
                <given>D</given>
                <family>Smith</family>
                <suffix>MD</suffix>
              </name>
            </assignedPerson>

            <!-- Provider organization -->
            <representedOrganization>
              <id root="2.16.840.1.113883.19.5.99999.1"/>
              <name>Community Health and Hospitals</name>
              <telecom use="WP" value="tel:+1(555)555-5000"/>
              <addr>
                <streetAddressLine>1001 Village Avenue</streetAddressLine>
                <city>Portland</city>
                <state>OR</state>
                <postalCode>99123</postalCode>
              </addr>
            </representedOrganization>
          </assignedEntity>
        </performer>
      </act>
    </component>

    <!-- Additional Care Team Members -->
    <component>
      <act classCode="PCPR" moodCode="EVN">
        <!-- Repeat structure for each member -->
      </act>
    </component>

  </organizer>
</entry>
```

#### Cardinality and Conformance

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| `@classCode` | 1..1 | SHALL | Fixed: "CLUSTER" |
| `@moodCode` | 1..1 | SHALL | Fixed: "EVN" |
| `templateId` | 1..* | SHALL | Root + extension |
| `id` | 1..* | SHALL | Unique identifier for the care team |
| `code` | 1..1 | SHALL | 86744-0 (LOINC) |
| `code/@codeSystem` | 1..1 | SHALL | 2.16.840.1.113883.6.1 |
| `code/originalText/reference` | 1..1 | SHALL | Link to narrative |
| `statusCode` | 1..1 | SHALL | From ActStatus value set |
| `effectiveTime` | 1..1 | SHALL | Time period for the team |
| `effectiveTime/low` | 1..1 | SHALL | Start date required |
| `effectiveTime/high` | 0..1 | SHOULD | End date (omit for ongoing) |
| `sdtcText` | 0..1 | SHOULD | Narrative reference |
| `participant[@typeCode='PPRF']` | 0..1 | SHOULD | Care team lead |
| `participant[@typeCode='LOC']` | 0..* | MAY | Team location(s) |
| `component[type]` | 0..* | MAY | Care team type observation |
| `component[member]` | 1..* | SHALL | At least one member required |

---

### Care Team Member Act

**Template ID:** `2.16.840.1.113883.10.20.22.4.500.1`

**Extensions:** 2019-07-01, 2022-06-01

**Purpose:** Represents an individual member of a care team, including their role, contact information, and organization.

#### Member Act Structure

```xml
<component>
  <act classCode="PCPR" moodCode="EVN">
    <!-- Care Team Member Act Template -->
    <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>

    <!-- Code: Care Team -->
    <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"
          displayName="Care team"/>

    <!-- Member status -->
    <statusCode code="active"/>

    <!-- Time period for this member's participation -->
    <effectiveTime>
      <low value="20230115"/>
      <!-- high value optional -->
    </effectiveTime>

    <!-- The care team member -->
    <performer>
      <!-- Member's role/function in the care team -->
      <functionCode code="224535009" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Registered Nurse"/>

      <assignedEntity>
        <!-- Member identifier -->
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>

        <!-- OPTIONAL: Member's professional taxonomy -->
        <code code="163W00000X" codeSystem="2.16.840.1.113883.6.101"
              displayName="Registered Nurse"/>

        <!-- Work address -->
        <addr use="WP">
          <streetAddressLine>1001 Village Avenue</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>

        <!-- Contact information -->
        <telecom use="WP" value="tel:+1(555)555-5200"/>
        <telecom use="WP" value="mailto:nurse@communityhealthorg"/>

        <!-- Member name -->
        <assignedPerson>
          <name>
            <given>Sarah</given>
            <family>Johnson</family>
            <suffix>RN</suffix>
          </name>
        </assignedPerson>

        <!-- Member's organization -->
        <representedOrganization>
          <id root="2.16.840.1.113883.19.5.99999.1"/>
          <name>Community Health and Hospitals</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
  </act>
</component>
```

#### Cardinality and Conformance

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| `@classCode` | 1..1 | SHALL | Fixed: "PCPR" (care provision) |
| `@moodCode` | 1..1 | SHALL | Fixed: "EVN" (event) |
| `templateId` | 1..* | SHALL | Root + extension |
| `code` | 1..1 | SHALL | 86744-0 (LOINC) |
| `statusCode` | 1..1 | SHALL | Member status |
| `effectiveTime` | 0..1 | SHOULD | Member participation period |
| `performer` | 1..1 | SHALL | The care team member |
| `performer/functionCode` | 1..1 | SHALL | Member's role/function |
| `performer/assignedEntity` | 1..1 | SHALL | Member details |
| `performer/assignedEntity/id` | 1..* | SHALL | Member identifier |
| `performer/assignedEntity/code` | 0..1 | SHOULD | Professional taxonomy |
| `performer/assignedEntity/addr` | 0..* | SHOULD | Work address |
| `performer/assignedEntity/telecom` | 0..* | SHOULD | Contact info |
| `performer/assignedEntity/assignedPerson` | 0..1 | SHALL | Member name (if person) |
| `performer/assignedEntity/representedOrganization` | 0..1 | SHOULD | Member's organization |

---

### Care Team Type Observation

**Template ID:** `2.16.840.1.113883.10.20.22.4.500.2`

**Extension:** 2019-07-01

**Purpose:** Classifies the type of care team (e.g., longitudinal, condition-focused, encounter-focused).

```xml
<component>
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
    <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"
          displayName="Care team"/>
    <!-- Type of care team -->
    <value xsi:type="CD" code="LA28865-6" codeSystem="2.16.840.1.113883.6.1"
           displayName="Condition-focused care team"/>
  </observation>
</component>
```

#### LOINC Answer Codes for Care Team Types

| Code | Display Name |
|------|--------------|
| `LA27976-2` | Longitudinal care-coordination focused care team |
| `LA27977-0` | Episode of care focused care team |
| `LA28865-6` | Condition-focused care team |
| `LA28866-4` | Encounter-focused care team |
| `LA28867-2` | Event-focused care team |

---

## Approach 2: Header-Based Care Team Representation

### documentationOf/serviceEvent

**Purpose:** Simpler representation of care team members in document header, commonly used in transition-of-care documents.

**Context:** Used in CCD, Consultation Note, Discharge Summary, Transfer Summary, Referral Note

```xml
<ClinicalDocument>
  <!-- ... header elements ... -->

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20230115"/>
        <high value="20240115"/>
      </effectiveTime>

      <!-- Primary Care Physician -->
      <performer typeCode="PRF">
        <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                     displayName="Primary Care Physician"/>
        <time>
          <low value="20230115"/>
        </time>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                displayName="Family Medicine Physician"/>
          <addr use="WP">
            <streetAddressLine>1001 Village Avenue</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>99123</postalCode>
          </addr>
          <telecom use="WP" value="tel:+1(555)555-5100"/>
          <assignedPerson>
            <name>
              <prefix>Dr.</prefix>
              <given>John</given>
              <family>Smith</family>
              <suffix>MD</suffix>
            </name>
          </assignedPerson>
          <representedOrganization>
            <name>Community Health and Hospitals</name>
          </representedOrganization>
        </assignedEntity>
      </performer>

      <!-- Additional Care Team Members -->
      <performer typeCode="PRF">
        <functionCode code="ADMPHYS" codeSystem="2.16.840.1.113883.5.88"
                     displayName="Admitting Physician"/>
        <assignedEntity>
          <!-- Provider details -->
        </assignedEntity>
      </performer>

      <!-- Non-clinical team members -->
      <performer typeCode="PRF">
        <functionCode code="224930009" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Social worker"/>
        <assignedEntity>
          <!-- Provider details -->
        </assignedEntity>
      </performer>

    </serviceEvent>
  </documentationOf>

  <!-- ... rest of document ... -->
</ClinicalDocument>
```

#### Key Elements

| Element | Description |
|---------|-------------|
| `serviceEvent/@classCode` | "PCPR" (care provision) |
| `serviceEvent/effectiveTime` | Period of care being documented |
| `performer/@typeCode` | "PRF" (performer) |
| `performer/functionCode` | Role/function in care team |
| `performer/time` | Optional: when this performer joined |
| `performer/assignedEntity` | Provider demographics and contact |

#### Recommended Practice

Per HL7 C-CDA Examples guidance:
> "In Transition of Care documents, the patient's key healthcare care team members should be listed, particularly the patient's primary physician and any active consulting physicians, therapists, counselors"

---

## Value Sets and Code Systems

### Care Team Member Function

**OID:** `2.16.840.1.113762.1.4.1099.30`

**Source:** VSAC (Value Set Authority Center)

**Binding:** Preferred (for functionCode in both approaches)

Common codes include:

| System | Code | Display Name |
|--------|------|--------------|
| HL7 RoleCode (2.16.840.1.113883.5.88) | PCP | Primary Care Physician |
| HL7 RoleCode | ADMPHYS | Admitting Physician |
| HL7 RoleCode | ATTPHYS | Attending Physician |
| HL7 RoleCode | CONPHYS | Consulting Physician |
| SNOMED CT (2.16.840.1.113883.6.96) | 17561000 | General practitioner |
| SNOMED CT | 224535009 | Registered nurse |
| SNOMED CT | 224571005 | Nurse practitioner |
| SNOMED CT | 46255001 | Pharmacist |
| SNOMED CT | 224930009 | Social worker |
| SNOMED CT | 159141008 | Dietitian |
| SNOMED CT | 133932002 | Caregiver |

### NUCC Provider Taxonomy

**OID:** `2.16.840.1.113883.6.101`

Used in `assignedEntity/code` for professional credentials:
- `207Q00000X` - Family Medicine Physician
- `163W00000X` - Registered Nurse
- `367500000X` - Nurse Anesthetist
- `183500000X` - Pharmacist

### ActStatus Value Set

**OID:** `2.16.840.1.113883.1.11.15933`

Used for `statusCode`:
- `active` - Currently active
- `completed` - No longer active
- `aborted` - Terminated prematurely
- `suspended` - Temporarily inactive

---

## Examples

### Example 1: Primary Care Team (Structured)

Complete Care Teams Section with primary care team:

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.500" extension="2022-06-01"/>
  <code code="85847-2" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Care team information"/>
  <title>CARE TEAMS</title>
  <text>
    <table>
      <thead>
        <tr><th>Team</th><th>Member</th><th>Role</th><th>Contact</th></tr>
      </thead>
      <tbody>
        <tr ID="ct1"><td>Primary Care</td><td>Dr. John Smith</td><td>PCP</td><td>555-0100</td></tr>
        <tr ID="ct2"><td>Primary Care</td><td>Sarah Johnson, RN</td><td>Care Coordinator</td><td>555-0200</td></tr>
      </tbody>
    </table>
  </text>
  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>
      <id root="1.2.3.4.5.6" extension="primary-care-team"/>
      <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team">
        <originalText><reference value="#ct1"/></originalText>
      </code>
      <statusCode code="active"/>
      <effectiveTime><low value="20230115"/></effectiveTime>

      <!-- Team Lead -->
      <participant typeCode="PPRF">
        <participantRole>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </participantRole>
      </participant>

      <!-- Team Type -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
          <value xsi:type="CD" code="LA27976-2" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Longitudinal care-coordination focused care team"/>
        </observation>
      </component>

      <!-- Member 1: Physician -->
      <component>
        <act classCode="PCPR" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
          <statusCode code="active"/>
          <effectiveTime><low value="20230115"/></effectiveTime>
          <performer>
            <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88" displayName="Primary Care Physician"/>
            <assignedEntity>
              <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
              <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101" displayName="Family Medicine Physician"/>
              <addr use="WP">
                <streetAddressLine>1001 Village Avenue</streetAddressLine>
                <city>Portland</city>
                <state>OR</state>
                <postalCode>99123</postalCode>
              </addr>
              <telecom use="WP" value="tel:+1(555)555-0100"/>
              <assignedPerson>
                <name><prefix>Dr.</prefix><given>John</given><family>Smith</family><suffix>MD</suffix></name>
              </assignedPerson>
              <representedOrganization>
                <name>Community Health Clinic</name>
              </representedOrganization>
            </assignedEntity>
          </performer>
        </act>
      </component>

      <!-- Member 2: Nurse Care Coordinator -->
      <component>
        <act classCode="PCPR" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
          <statusCode code="active"/>
          <performer>
            <functionCode code="224535009" codeSystem="2.16.840.1.113883.6.96" displayName="Registered nurse"/>
            <assignedEntity>
              <id root="2.16.840.1.113883.19" extension="nurse-001"/>
              <telecom use="WP" value="tel:+1(555)555-0200"/>
              <assignedPerson>
                <name><given>Sarah</given><family>Johnson</family><suffix>RN</suffix></name>
              </assignedPerson>
            </assignedEntity>
          </performer>
        </act>
      </component>

    </organizer>
  </entry>
</section>
```

### Example 2: Multiple Care Teams

Patient with both primary care and diabetes specialty teams:

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.500" extension="2022-06-01"/>
  <code code="85847-2" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Care team information"/>
  <title>CARE TEAMS</title>
  <text>
    <!-- Narrative with both teams -->
  </text>

  <!-- Primary Care Team -->
  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>
      <id root="1.2.3.4" extension="primary-team"/>
      <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
      <statusCode code="active"/>
      <effectiveTime><low value="20230115"/></effectiveTime>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
          <value xsi:type="CD" code="LA27976-2" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Longitudinal care-coordination focused care team"/>
        </observation>
      </component>
      <!-- Primary care members -->
    </organizer>
  </entry>

  <!-- Diabetes Management Team -->
  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>
      <id root="1.2.3.4" extension="diabetes-team"/>
      <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
      <statusCode code="active"/>
      <effectiveTime><low value="20240301"/></effectiveTime>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
          <value xsi:type="CD" code="LA28865-6" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Condition-focused care team"/>
        </observation>
      </component>
      <!-- Diabetes team members: endocrinologist, dietitian, diabetes educator -->
    </organizer>
  </entry>

</section>
```

---

## Implementation Guidance

### When to Use Structured vs. Header Approach

**Use Structured Care Teams Section when:**
- Creating comprehensive care plans
- Documenting multiple distinct care teams
- Need to track team types, leads, and hierarchies
- Implementing USCDI v4 Care Team Members requirement
- Building systems for longitudinal care coordination

**Use Header documentationOf/serviceEvent when:**
- Creating transition-of-care documents (CCD, Referral, Discharge Summary)
- Simple listing of key providers sufficient
- Backward compatibility with legacy systems required
- Document focuses on single episode of care

**Use Both when:**
- Comprehensive care plan document
- Include structured section for detailed teams
- Include header performers for key contacts during transition

### Participant vs. Member Distinction

- **serviceEvent/performer** (header): Any clinician involved in the documented service
- **Care Team Member** (structured): Formal member of a coordinated care team
- Not all performers are care team members (e.g., ED physician for one-time visit)
- All care team members could be listed as performers in relevant documents

### Deduplication Strategies

When the same provider appears in multiple contexts:
1. **Consistent Identifiers**: Use same NPI across all representations
2. **Reference by ID**: In structured approach, care team lead references member by ID
3. **Document-Level**: Header performers can reference same individuals in structured section

### Non-Clinical Team Members

Both approaches support non-clinical members:
- Family caregivers (RelatedPerson)
- Social workers
- Transportation providers
- Community health workers
- Religious/spiritual advisors

Use appropriate functionCode values from the Care Team Member Function value set.

---

## References

- [HL7 C-CDA R2.1 Companion Guide](https://www.hl7.org/ccdasearch/)
- [HL7 C-CDA Examples - Care Team](https://github.com/HL7/C-CDA-Examples/tree/master/Care%20Team)
- [Care Team Organizer Template](https://cdasearch.hl7.org/examples/view/Guide%20Examples/Care%20Team%20Organizer%20(V2)_2.16.840.1.113883.10.20.22.4.500)
- [LOINC 86744-0 - Care team](https://loinc.org/86744-0)
- [Care Team Member Function Value Set](http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113762.1.4.1099.30)
