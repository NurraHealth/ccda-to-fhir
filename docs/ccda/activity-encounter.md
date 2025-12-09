# C-CDA: Encounter Activity

## Overview

Encounters in C-CDA are documented using the Encounter Activity template within the Encounters Section. This template records information about a healthcare encounter, including the type, time period, location, and participants. It describes interactions between patients and clinicians, including in-person encounters, telephone conversations, and email exchanges.

**Important:** The Encounter Activity template (moodCode=EVN) can only represent encounters that have occurred. For future/planned encounters, use the Planned Encounter template instead.

## Template Information

| Attribute | Value |
|-----------|-------|
| Encounter Activity Template ID | `2.16.840.1.113883.10.20.22.4.49` |
| Template Version (Extension) | 2015-08-01 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/EncounterActivity` |
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.22.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.22` |
| Section Version (Extension) | 2015-08-01 |
| LOINC Code | 46240-8 |
| LOINC Display | History of Hospitalizations+Outpatient visits Narrative |

## USCDI Data Elements

The following elements are designated as USCDI (United States Core Data for Interoperability) elements:

| USCDI Element | C-CDA Element |
|---------------|---------------|
| Identifier | encounter/id |
| Type | encounter/code |
| Time | encounter/effectiveTime |
| Disposition | encounter/sdtc:dischargeDispositionCode |
| Location | participant[@typeCode='LOC'] |
| Diagnosis | entryRelationship[@typeCode='SUBJ'] with Encounter Diagnosis |
| Interpreter Needed | entryRelationship with Interpreter Needed Observation |

## Location in Document

```
ClinicalDocument
├── componentOf
│   └── encompassingEncounter [Document-level encounter]
│
└── component
    └── structuredBody
        └── component
            └── section [Encounters Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.22.1']
                ├── code [@code='46240-8']
                └── entry
                    └── encounter [Encounter Activity]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.49']
                        ├── participant (locations)
                        └── entryRelationship (diagnoses, indications, interpreter needed)
```

## XML Structure

### Document-Level Encounter (encompassingEncounter)

The encompassingEncounter is an optional CDA header element representing the setting of the clinical encounter during which the documented acts occurred. It SHALL be sent if there is information on either the admission or the attender participation.

```xml
<componentOf>
  <encompassingEncounter>
    <!-- Class and Mood (fixed values) -->
    <!-- classCode="ENC" moodCode="EVN" -->

    <id root="2.16.840.1.113883.19.5.99999.1" extension="12345"/>

    <code code="AMB" codeSystem="2.16.840.1.113883.5.4"
          displayName="Ambulatory"/>

    <!-- Required: effectiveTime -->
    <effectiveTime>
      <low value="20200301090000-0500"/>
      <high value="20200301100000-0500"/>
    </effectiveTime>

    <!-- Optional: Admission/Referral Source (SDTC extension) -->
    <sdtc:admissionReferralSourceCode code="1"
        codeSystem="2.16.840.1.113883.6.301.4"
        displayName="Physician Referral"/>

    <dischargeDispositionCode code="01" codeSystem="2.16.840.1.113883.6.301.5"
                               displayName="Discharged to home care or self care"/>

    <!-- Responsible Party (0..1) -->
    <responsibleParty>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <assignedPerson>
          <name>
            <given>Adam</given>
            <family>Careful</family>
          </name>
        </assignedPerson>
      </assignedEntity>
    </responsibleParty>

    <!-- Encounter Participants (0..*) -->
    <encounterParticipant typeCode="ATND">
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <assignedPerson>
          <name>
            <given>Adam</given>
            <family>Careful</family>
          </name>
        </assignedPerson>
      </assignedEntity>
    </encounterParticipant>

    <!-- Location (0..1) -->
    <location>
      <healthCareFacility>
        <id root="2.16.840.1.113883.19.5.9999.1"/>
        <code code="1160-1" codeSystem="2.16.840.1.113883.6.259"
              displayName="Urgent Care Center"/>
        <location>
          <name>Community Health and Hospitals</name>
          <addr>
            <streetAddressLine>1001 Village Avenue</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>99123</postalCode>
          </addr>
        </location>
        <serviceProviderOrganization>
          <name>Community Health and Hospitals</name>
        </serviceProviderOrganization>
      </healthCareFacility>
    </location>
  </encompassingEncounter>
</componentOf>
```

### Section-Level Encounter (Encounter Activity)

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.22.1" extension="2015-08-01"/>
  <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"
        displayName="History of Hospitalizations+Outpatient visits Narrative"/>
  <title>ENCOUNTERS</title>
  <text>
    <table>
      <thead>
        <tr><th>Encounter</th><th>Performer</th><th>Location</th><th>Date</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="enc1">Office Visit</td>
          <td>Dr. Adam Careful</td>
          <td>Community Health and Hospitals</td>
          <td>March 1, 2020</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <encounter classCode="ENC" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.49" extension="2015-08-01"/>

      <!-- Identifier(s) - USCDI: Identifier -->
      <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>

      <!-- Encounter Type Code - USCDI: Type -->
      <code code="99213" codeSystem="2.16.840.1.113883.6.12"
            displayName="Office or other outpatient visit">
        <originalText>
          <reference value="#enc1"/>
        </originalText>
        <translation code="AMB" codeSystem="2.16.840.1.113883.5.4"
                     displayName="Ambulatory"/>
      </code>

      <!-- Text reference to narrative -->
      <text>
        <reference value="#enc1"/>
      </text>

      <!-- Status Code (optional) -->
      <statusCode code="completed"/>

      <!-- Priority Code (optional) -->
      <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                    displayName="Routine"/>

      <!-- Encounter Time - USCDI: Time -->
      <effectiveTime>
        <low value="20200301090000-0500"/>
        <high value="20200301100000-0500"/>
      </effectiveTime>

      <!-- Discharge Disposition - USCDI: Disposition -->
      <sdtc:dischargeDispositionCode code="01"
          codeSystem="2.16.840.1.113883.6.301.5"
          displayName="Discharged to home care or self care"/>

      <!-- Encounter Performer(s) (0..*) -->
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                displayName="Family Medicine"/>
          <!-- Provider Specialty (SDTC extension) -->
          <sdtc:specialty code="207Q00000X"
                          codeSystem="2.16.840.1.113883.6.101"
                          displayName="Family Medicine"/>
          <addr>
            <streetAddressLine>1001 Village Avenue</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>99123</postalCode>
          </addr>
          <telecom use="WP" value="tel:+1(555)555-1002"/>
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
        </assignedEntity>
      </performer>

      <!-- Author (0..*) -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20200301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <!-- Service Delivery Location - USCDI: Location -->
      <participant typeCode="LOC">
        <participantRole classCode="SDLOC">
          <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
          <!-- Facility Identifiers (optional) -->
          <!-- NPI -->
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <!-- CLIA -->
          <id root="2.16.840.1.113883.4.7" extension="11D0265516"/>
          <code code="1160-1" codeSystem="2.16.840.1.113883.6.259"
                displayName="Urgent Care Center"/>
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

      <!-- Encounter Diagnosis - USCDI: Diagnosis -->
      <entryRelationship typeCode="SUBJ">
        <act classCode="ACT" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.80" extension="2015-08-01"/>
          <code code="29308-4" codeSystem="2.16.840.1.113883.6.1"
                displayName="Diagnosis"/>
          <statusCode code="completed"/>
          <effectiveTime>
            <low value="20200301"/>
          </effectiveTime>
          <entryRelationship typeCode="SUBJ">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
              <id root="..."/>
              <code code="282291009" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Diagnosis">
                <translation code="29308-4" codeSystem="2.16.840.1.113883.6.1"
                             displayName="Diagnosis"/>
              </code>
              <statusCode code="completed"/>
              <effectiveTime>
                <low value="20200301"/>
              </effectiveTime>
              <value xsi:type="CD" code="J06.9" codeSystem="2.16.840.1.113883.6.90"
                     displayName="Acute upper respiratory infection, unspecified">
                <translation code="54150009" codeSystem="2.16.840.1.113883.6.96"
                             displayName="Upper respiratory infection"/>
              </value>
            </observation>
          </entryRelationship>
        </act>
      </entryRelationship>

      <!-- Indication (reason for visit) -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2023-05-01"/>
          <id root="db734647-fc99-424c-a864-7e3cda82e706"/>
          <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"
                displayName="Clinical finding"/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="CD" code="21522001" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Abdominal pain"/>
        </observation>
      </entryRelationship>

      <!-- Interpreter Needed Observation - USCDI -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.515" extension="2025-05-01"/>
          <code code="54588-9" codeSystem="2.16.840.1.113883.6.1"
                displayName="Interpreter needed"/>
          <statusCode code="completed"/>
          <effectiveTime>
            <low value="20200301"/>
            <high value="20200301"/>
          </effectiveTime>
          <value xsi:type="CD" code="Y" codeSystem="2.16.840.1.113883.5.1008"
                 displayName="Yes"/>
        </observation>
      </entryRelationship>

    </encounter>
  </entry>
</section>
```

## Element Details

### encounter (Root Element)

| Attribute | Value | Required |
|-----------|-------|----------|
| @classCode | ENC | Yes (fixed) |
| @moodCode | EVN | Yes (fixed) |

### encounter/id (Identifier)

Unique identifier(s) for the encounter. USCDI element.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID or UUID | Yes |
| @extension | Identifier value | No |

**Cardinality:** 1..*

### encounter/code (Encounter Type)

The type of encounter. USCDI element.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Encounter type code | Yes |
| @codeSystem | Code system OID | Yes |
| @displayName | Human-readable display | No |
| originalText/reference | Link to narrative | SHOULD |
| translation | Additional codes (ActCode, etc.) | No |

**Value Set:** Encounter Type (VSAC) - Preferred binding

**Terminology Bindings for Encounter Activity:**
| Element | Value Set | Binding |
|---------|-----------|---------|
| code | Encounter Type (VSAC) | Preferred |
| sdtc:dischargeDispositionCode | USEncounterDischargeDisposition | Preferred |
| performer.assignedEntity.code | Healthcare Provider Taxonomy | Preferred |
| performer.assignedEntity.sdtc:specialty | Practice Setting Code Value Set | Preferred |

**Common Code Systems:**
| OID | URI | Name | Use |
|-----|-----|------|-----|
| 2.16.840.1.113883.6.12 | `http://www.ama-assn.org/go/cpt` | CPT | E&M codes |
| 2.16.840.1.113883.5.4 | `http://terminology.hl7.org/CodeSystem/v3-ActCode` | ActCode | Encounter class |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT | Clinical terms |

**CPT E&M Codes:**
| Code | Display |
|------|---------|
| 99201-99205 | Office/Outpatient Visit, New Patient |
| 99211-99215 | Office/Outpatient Visit, Established |
| 99221-99223 | Initial Hospital Care |
| 99231-99233 | Subsequent Hospital Care |
| 99281-99285 | Emergency Department Visit |
| 99241-99245 | Office Consultation |

**ActCode Encounter Class:**
| Code | Display |
|------|---------|
| AMB | Ambulatory |
| EMER | Emergency |
| IMP | Inpatient encounter |
| ACUTE | Inpatient acute |
| NONAC | Inpatient non-acute |
| SS | Short stay |
| OBSENC | Observation encounter |
| HH | Home health |
| VR | Virtual |
| FLD | Field |
| PRENC | Pre-admission |

### encounter/text

Reference to the narrative text describing this encounter.

| Element | Description |
|---------|-------------|
| reference/@value | Must start with '#' pointing to narrative |

**Conformance:** SHOULD contain text/reference/@value

### encounter/statusCode

The status of the encounter.

| Attribute | Description |
|-----------|-------------|
| @code | Status code from ActStatus |

**Value Set:** ActStatus
| Code | Display |
|------|---------|
| active | Active |
| completed | Completed |
| cancelled | Cancelled |
| held | Held |
| new | New |
| suspended | Suspended |
| nullified | Nullified |
| obsolete | Obsolete |

**Cardinality:** 0..1

### encounter/priorityCode

The priority of the encounter.

| Attribute | Description |
|-----------|-------------|
| @code | Priority code |
| @codeSystem | 2.16.840.1.113883.5.7 (ActPriority) |

**Value Set:** ActPriority
| Code | Display |
|------|---------|
| A | ASAP |
| CR | Callback results |
| CS | Callback for scheduling |
| CSP | Callback placer for scheduling |
| CSR | Contact recipient for scheduling |
| EL | Elective |
| EM | Emergency |
| P | Preoperative |
| PRN | As needed |
| R | Routine |
| RR | Rush reporting |
| S | Stat |
| T | Timing critical |
| UD | Use as directed |
| UR | Urgent |

**Cardinality:** 0..1

### effectiveTime

When the encounter occurred. USCDI element.

```xml
<!-- Single point in time -->
<effectiveTime value="20200301"/>

<!-- Time range -->
<effectiveTime>
  <low value="20200301090000-0500"/>
  <high value="20200301100000-0500"/>
</effectiveTime>
```

**Cardinality:** 1..1 (Required)

### sdtc:dischargeDispositionCode

The disposition at the end of the encounter. USCDI element.

| Attribute | Description |
|-----------|-------------|
| @code | Disposition code |
| @codeSystem | Code system OID |
| @displayName | Human-readable display |

**Value Set:** US Encounter Discharge Disposition (Preferred binding)

**Common Discharge Disposition Codes (NUBC UB-04 FL17):**
| Code | Display |
|------|---------|
| 01 | Discharged to home care or self care (routine discharge) |
| 02 | Discharged/transferred to short term general hospital |
| 03 | Discharged/transferred to skilled nursing facility (SNF) |
| 04 | Discharged/transferred to intermediate care facility (ICF) |
| 05 | Discharged/transferred to another type of institution |
| 06 | Discharged/transferred to home under care of organized home health |
| 07 | Left against medical advice (AMA) |
| 09 | Admitted as an inpatient to this hospital |
| 20 | Expired |
| 21 | Expired at home |
| 30 | Still patient |
| 40 | Expired at home (hospice) |
| 41 | Expired in medical facility (hospice) |
| 42 | Expired - place unknown (hospice) |
| 43 | Discharged/transferred to federal health care facility |
| 50 | Hospice - home |
| 51 | Hospice - medical facility |
| 61 | Discharged/transferred to hospital-based swing bed |
| 62 | Discharged/transferred to inpatient rehabilitation facility (IRF) |
| 63 | Discharged/transferred to long term care hospital (LTCH) |
| 64 | Discharged/transferred to nursing facility certified under Medicaid |
| 65 | Discharged/transferred to psychiatric hospital or psychiatric unit |
| 66 | Discharged/transferred to critical access hospital (CAH) |
| 69 | Discharged/transferred to designated disaster alternative care site |
| 70 | Discharged/transferred to another type of health care institution not defined |
| 81 | Discharged to home or self care with planned readmission |
| 82 | Discharged/transferred to short term general hospital with planned readmission |
| 83 | Discharged/transferred to SNF with planned readmission |
| 84 | Discharged/transferred to ICF with planned readmission |
| 85 | Discharged/transferred to designated cancer center or children's hospital |
| 86 | Discharged/transferred to home under care of home health with planned readmission |
| 87 | Discharged/transferred to court/law enforcement |
| 88 | Discharged/transferred to federal facility with planned readmission |
| 89 | Discharged/transferred to designated disaster alternative care site with planned readmission |
| 90 | Discharged/transferred to another institution with planned readmission |
| 91 | Discharged/transferred to psychiatric hospital or unit with planned readmission |
| 94 | Discharged/transferred to critical access hospital with planned readmission |
| 95 | Discharged/transferred to another type of health care institution not defined with planned readmission |

**Code System:** `2.16.840.1.113883.6.301.5` (NUBC UB-04 FL17)

**Cardinality:** 0..1

### performer

Who performed the encounter.

| Element | Description |
|---------|-------------|
| assignedEntity/id | Provider identifier (NPI: 2.16.840.1.113883.4.6) |
| assignedEntity/code | Provider role/specialty |
| assignedEntity/sdtc:specialty | Provider clinical specialty (0..*) |
| assignedEntity/addr | Provider address |
| assignedEntity/telecom | Provider contact info |
| assignedEntity/assignedPerson/name | Provider name |
| assignedEntity/representedOrganization | Organization |

**Healthcare Provider Taxonomy Value Set:** 2.16.840.1.114222.4.11.1066 (Preferred binding)

**Cardinality:** 0..*

### author

Author of the encounter documentation.

| Element | Description |
|---------|-------------|
| templateId | 2.16.840.1.113883.10.20.22.4.119 (Author Participation) |
| time | When authored |
| assignedAuthor/id | Author identifier |
| assignedAuthor/code | Author role |
| assignedAuthor/assignedPerson | Person details |
| assignedAuthor/assignedAuthoringDevice | Device details (alternative) |

**Cardinality:** 0..*

### participant[@typeCode='LOC'] (Service Delivery Location)

The location of the encounter. USCDI element.

**Template ID:** 2.16.840.1.113883.10.20.22.4.32

| Element | Description |
|---------|-------------|
| participantRole/@classCode | SDLOC (Service Delivery Location) - fixed |
| participantRole/id | Facility identifiers (USCDI: Facility Identifier) |
| participantRole/code | Facility type code |
| participantRole/addr | Location address (USCDI: Facility Address) |
| participantRole/telecom | Location contact |
| playingEntity/@classCode | PLC (Place) - fixed |
| playingEntity/name | Location name (USCDI: Facility Name) |

**Facility Identifier Types:**
| Type | Root OID |
|------|----------|
| NPI | 2.16.840.1.113883.4.6 |
| CLIA | 2.16.840.1.113883.4.7 |
| NAIC | 2.16.840.1.113883.6.300 |

**Healthcare Facility Type Codes:**

Must use codes from one of the following value sets:
- NHSN Healthcare Facility Patient Care Location (HSLOC)
- SNOMED CT location types
- CMS Place of Service (POS) codes (optional, for billing)

| Code | Display | Code System |
|------|---------|-------------|
| 1160-1 | Urgent Care Center | HealthcareServiceLocation |
| 1061-3 | Hospital | HealthcareServiceLocation |
| 1118-1 | Emergency Department | HealthcareServiceLocation |
| 1116-5 | Ambulatory Surgical Center | HealthcareServiceLocation |
| 1021-7 | Critical Care Unit | HealthcareServiceLocation |
| 1108-2 | Operating Room | HealthcareServiceLocation |
| 1023-3 | Inpatient Medical Ward | HealthcareServiceLocation |
| 1117-3 | Ambulatory Primary Care Clinic | HealthcareServiceLocation |
| 1242-9 | Outpatient Clinic | HealthcareServiceLocation |
| 1024-1 | Inpatient Surgical Ward | HealthcareServiceLocation |
| 1025-8 | Inpatient Pediatric Ward | HealthcareServiceLocation |
| 1026-6 | Inpatient Obstetric Ward | HealthcareServiceLocation |
| 1027-4 | Inpatient Psychiatric Ward | HealthcareServiceLocation |
| 1028-2 | Rehabilitation Unit | HealthcareServiceLocation |
| 1029-0 | Labor and Delivery | HealthcareServiceLocation |
| 1033-2 | Pediatric Critical Care | HealthcareServiceLocation |
| 1034-0 | Neonatal Critical Care | HealthcareServiceLocation |
| 1035-7 | Burn Unit | HealthcareServiceLocation |
| 1200-7 | Long Term Care | HealthcareServiceLocation |

**Code System:** `2.16.840.1.113883.6.259` (HealthcareServiceLocation)

**Cardinality:** 0..*

### entryRelationship[@typeCode='SUBJ'] (Encounter Diagnosis)

Diagnoses made during the encounter. USCDI element.

**Template IDs:**
- Encounter Diagnosis Act: `2.16.840.1.113883.10.20.22.4.80` (extension: 2015-08-01)
- Problem Observation: `2.16.840.1.113883.10.20.22.4.4` (extension: 2015-08-01)

| Element | Description |
|---------|-------------|
| act/templateId | 2.16.840.1.113883.10.20.22.4.80 (Encounter Diagnosis Act) |
| act/code | 29308-4 (Diagnosis) from LOINC |
| act/statusCode | completed (fixed) |
| observation/templateId | 2.16.840.1.113883.10.20.22.4.4 (Problem Observation) |
| observation/value | Diagnosis code (ICD-10-CM, SNOMED CT) |

**Encounter Diagnosis Act Requirements:**
- **SHALL** contain at least one Problem Observation (entryRelationship[@typeCode='SUBJ'])
- **SHALL** have statusCode = "completed"
- **SHALL** have code = 29308-4 (Diagnosis)

**Cardinality:** 0..*

### entryRelationship[@typeCode='RSON'] (Indication/Reason for Visit)

The reason for the encounter.

**Template ID:** 2.16.840.1.113883.10.20.22.4.19 (extension: 2023-05-01)

| Element | Description |
|---------|-------------|
| templateId | 2.16.840.1.113883.10.20.22.4.19 |
| id | May reference problem documented elsewhere |
| code | Problem Type value set |
| statusCode | completed (fixed) |
| effectiveTime | When indication applies (SHOULD) |
| value | Reason code - US Core Condition Codes (Preferred) |

**Problem Type Value Set:** VSAC OID 2.16.840.1.113762.1.4.1267.1

**Constraint:** If the id element does not reference a problem recorded elsewhere in the document, then observation/value MUST be populated with a coded entry.

**Cardinality:** 0..*

### entryRelationship (Interpreter Needed Observation)

Indicates whether a patient needs language interpretation services. USCDI element.

**Template ID:** 2.16.840.1.113883.10.20.22.4.515 (extension: 2025-05-01)

| Element | Description | Cardinality |
|---------|-------------|-------------|
| code | 54588-9 (Interpreter needed) from LOINC | 1..1 |
| statusCode | Act status | 0..1 |
| effectiveTime | When observation applies | 1..1 |
| effectiveTime/low | Start time | 1..1 |
| effectiveTime/high | End time | SHOULD |
| value | Yes/No/Unknown | 1..1 |

**Value Binding:** Answer Set with Yes No and Unknowns (VSAC OID: 2.16.840.1.113762.1.4.1267.16)

**Cardinality:** 0..*

## Encounter Participants

### encompassingEncounter Participants

| typeCode | Role |
|----------|------|
| ATND | Attending Physician |
| ADM | Admitting Physician |
| DIS | Discharging Physician |
| CON | Consultant |
| REF | Referrer |

### encounterParticipant/@typeCode

| Code | Display |
|------|---------|
| ATND | Attending |
| ADM | Admitter |
| DIS | Discharger |
| REF | Referrer |
| CON | Consultant |
| SPRF | Secondary Performer |

## Conformance Requirements

### Encounters Section (entries required)
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.2.22.1` and extension `2015-08-01`
2. **SHALL** contain exactly one `code` with code `46240-8` from LOINC
3. **SHALL** contain exactly one `title`
4. **SHALL** contain exactly one `text` (narrative)
5. **SHALL** contain at least one `Encounter Activity` if section/@nullFlavor is not present
6. **MAY** set @nullFlavor to NI if section contains no information

### Encounter Activity
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.49` and extension `2015-08-01`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code`
4. **SHALL** contain exactly one `effectiveTime`
5. **SHOULD** contain `text/reference/@value`
6. **SHOULD** contain `code/originalText/reference/@value`
7. **MAY** contain zero or one `statusCode`
8. **MAY** contain zero or one `priorityCode`
9. **MAY** contain zero or one `sdtc:dischargeDispositionCode`
10. **MAY** contain zero or more `performer`
11. **MAY** contain zero or more `author`
12. **MAY** contain zero or more `participant` with typeCode="LOC"
13. **MAY** contain zero or more `entryRelationship` with typeCode="SUBJ" (diagnoses)
14. **MAY** contain zero or more `entryRelationship` with typeCode="RSON" (indication)
15. **MAY** contain zero or more `entryRelationship` for Interpreter Needed Observation

### Constraint Identifiers

| Constraint ID | Level | Description |
|---------------|-------|-------------|
| should-text-ref-value | Warning | SHOULD contain text/reference/@value |
| should-otext-ref-value | Warning | Code SHOULD contain originalText/reference/@value |
| value-starts-octothorpe | Error | Reference values must begin with '#' pointing to narrative |
| shall-encounter-activity | Error | Section SHALL contain at least one Encounter Activity (if no nullFlavor) |

## Related Templates

| Template | OID | Purpose |
|----------|-----|---------|
| Encounters Section (entries required) | 2.16.840.1.113883.10.20.22.2.22.1 | Section container |
| Encounters Section (entries optional) | 2.16.840.1.113883.10.20.22.2.22 | Section container (optional entries) |
| Encounter Activity | 2.16.840.1.113883.10.20.22.4.49 | Individual encounter |
| Service Delivery Location | 2.16.840.1.113883.10.20.22.4.32 | Location details |
| Encounter Diagnosis | 2.16.840.1.113883.10.20.22.4.80 | Diagnosis wrapper |
| Problem Observation | 2.16.840.1.113883.10.20.22.4.4 | Diagnosis details |
| Indication | 2.16.840.1.113883.10.20.22.4.19 | Reason for encounter |
| Author Participation | 2.16.840.1.113883.10.20.22.4.119 | Author details |
| Interpreter Needed Observation | 2.16.840.1.113883.10.20.22.4.515 | Interpreter needs |
| Planned Encounter | 2.16.840.1.113883.10.20.22.4.40 | Future encounters |

## References

- HL7 C-CDA R2.1 Implementation Guide
- HL7 C-CDA v5.0.0-ballot Specification: https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- HL7 C-CDA Examples: https://github.com/HL7/C-CDA-Examples
- CPT: https://www.ama-assn.org/practice-management/cpt
- NUBC Discharge Status: https://www.nubc.org/
- SNOMED CT: http://snomed.info/sct
- VSAC (Value Set Authority Center): https://vsac.nlm.nih.gov/
