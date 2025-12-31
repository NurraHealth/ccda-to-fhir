# Encounter Mapping: C-CDA Encounter Activity ↔ FHIR Encounter

This document provides detailed mapping guidance between C-CDA Encounter Activity and FHIR `Encounter` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Encounter Activity (`2.16.840.1.113883.10.20.22.4.49`) | `Encounter` |
| Section: Encounters (LOINC `46240-8`) | — |
| Document Header `encompassingEncounter` | `Encounter` |

## Source Locations

Encounters can appear in two places in C-CDA:
1. **Document Body:** Encounter Activity entries in the Encounters section
2. **Document Header:** `encompassingEncounter` element

Duplicate encounters referenced in both header and body should consolidate into a single FHIR Encounter resource.

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `encounter/id` | `Encounter.identifier` | ID → Identifier |
| `encounter/code` (v3 ActCode) | `Encounter.class` | [Class Mapping](#class-mapping) |
| `encounter/code` (other) | `Encounter.type` | CodeableConcept |
| `encounter/statusCode` | `Encounter.status` | [Status Mapping](#status-mapping) |
| `encounter/effectiveTime/@value` or `/low/@value` | `Encounter.period.start` | Date conversion |
| `encounter/effectiveTime/high/@value` | `Encounter.period.end` | Date conversion |
| `encounter/code` + `priorityCode` (inferred) | `Encounter.hospitalization.admitSource` | [Admission Source Detection](#admission-source) |
| `encounter/dischargeDispositionCode` | `Encounter.hospitalization.dischargeDisposition` | CodeableConcept |
| `encounter/performer` or `encounterParticipant` | `Encounter.participant` | [Participant Mapping](#participant-mapping) |
| `encounter/performer/functionCode` | `Encounter.participant.type` | CodeableConcept |
| `participant[@typeCode='LOC']` or `/location` | `Encounter.location` | Reference(Location) |
| Indication | `Encounter.reasonCode` or `.reasonReference` | [Reason Mapping](#reason-mapping) |
| Encounter Diagnosis | `Encounter.diagnosis.condition` | Reference(Condition) |

### Class Mapping

The encounter `code` maps to FHIR `class` when it's from the V3 ActCode system:

**C-CDA:**
```xml
<code code="AMB" codeSystem="2.16.840.1.113883.5.4"
      displayName="Ambulatory"/>
```

**FHIR:**
```json
{
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB",
    "display": "ambulatory"
  }
}
```

**Common V3 ActCode Encounter Classes:**

| Code | Display | Description |
|------|---------|-------------|
| `AMB` | ambulatory | Outpatient encounter |
| `EMER` | emergency | Emergency room encounter |
| `FLD` | field | Home health or field visit |
| `HH` | home health | Home health encounter |
| `IMP` | inpatient encounter | Hospital inpatient |
| `ACUTE` | inpatient acute | Acute care hospitalization |
| `NONAC` | inpatient non-acute | Non-acute hospitalization |
| `OBSENC` | observation encounter | Observation status |
| `PRENC` | pre-admission | Pre-admission |
| `SS` | short stay | Short stay observation |
| `VR` | virtual | Telehealth/virtual |

**CPT to V3 ActCode Mapping:**

Some C-CDA documents use CPT codes for encounter type. Common mappings:

| CPT Code Range | V3 ActCode |
|----------------|------------|
| 99201-99215 | `AMB` (Outpatient) |
| 99221-99223 | `IMP` (Inpatient) |
| 99281-99285 | `EMER` (Emergency) |
| 99341-99350 | `HH` (Home Health) |

### Type Mapping

Non-V3 ActCode encounter codes map to `type`:

**C-CDA:**
```xml
<code code="99213" codeSystem="2.16.840.1.113883.6.12"
      displayName="Office or other outpatient visit">
  <translation code="AMB" codeSystem="2.16.840.1.113883.5.4"/>
</code>
```

**FHIR:**
```json
{
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB"
  },
  "type": [{
    "coding": [{
      "system": "http://www.ama-assn.org/go/cpt",
      "code": "99213",
      "display": "Office or other outpatient visit"
    }]
  }]
}
```

### Status Mapping

**C-CDA:**
```xml
<statusCode code="completed"/>
```

**Encounter Status ConceptMap:**

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `finished` |
| `active` | `in-progress` |
| `aborted` | `cancelled` |
| `cancelled` | `cancelled` |

**Status from Effective Time:**

If `statusCode` is missing or unclear, derive from `effectiveTime`:
- Single timestamp or `high` value present → `finished`
- `low` only without `high` → `in-progress` or `finished` (implementation choice)

**FHIR:**
```json
{
  "status": "finished"
}
```

### Period Mapping

**C-CDA (single timestamp):**
```xml
<effectiveTime value="20200315103000-0500"/>
```

**FHIR:**
```json
{
  "period": {
    "start": "2020-03-15T10:30:00-05:00"
  },
  "status": "finished"
}
```

**C-CDA (range):**
```xml
<effectiveTime>
  <low value="20200315103000-0500"/>
  <high value="20200315120000-0500"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "period": {
    "start": "2020-03-15T10:30:00-05:00",
    "end": "2020-03-15T12:00:00-05:00"
  }
}
```

### Participant Mapping

**C-CDA:**
```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <code code="59058001" codeSystem="2.16.840.1.113883.6.96"
          displayName="General physician"/>
    <assignedPerson>
      <name><given>Adam</given><family>Careful</family></name>
    </assignedPerson>
  </assignedEntity>
</performer>
```

**FHIR:**
```json
{
  "participant": [{
    "type": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
        "code": "PPRF",
        "display": "primary performer"
      }]
    }],
    "individual": {
      "reference": "Practitioner/practitioner-careful"
    }
  }]
}
```

**Performer Function Mapping:**

| C-CDA functionCode | FHIR participant.type |
|--------------------|----------------------|
| `PCP` | `PPRF` (primary performer) |
| `ATTPHYS` | `ATND` (attender) |
| `ADMPHYS` | `ADM` (admitter) |
| `DISPHYS` | `DIS` (discharger) |
| (none specified) | `PART` (participant) |

### Location Mapping

**C-CDA:**
```xml
<participant typeCode="LOC">
  <time>
    <low value="202003151030-0500"/>
    <high value="202003151200-0500"/>
  </time>
  <participantRole classCode="SDLOC">
    <id root="2.16.840.1.113883.19.5" extension="ROOM-101"/>
    <code code="1160-1" codeSystem="2.16.840.1.113883.6.259"
          displayName="Urgent Care Center"/>
    <playingEntity classCode="PLC">
      <name>City Urgent Care</name>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR:**
```json
{
  "location": [{
    "location": {
      "reference": "Location/location-urgent-care",
      "display": "City Urgent Care"
    },
    "period": {
      "start": "2020-03-15T10:30:00-05:00",
      "end": "2020-03-15T12:00:00-05:00"
    },
    "status": "completed"
  }]
}
```

#### Location Status Determination

The location `status` indicates the patient's presence at the location and is determined using intelligent mapping:

**Status Values:**
- `completed`: Patient was at location during the specified period (has end time)
- `active`: Patient is currently at location (no end time, or encounter in progress)
- `planned`: Patient is planned to be at location (planned encounter)
- `reserved`: Location held empty (rarely used)

**Determination Logic:**

1. **If participant.time is present:**
   - Both start and end times → `completed`
   - Only start time (no end) → `active`

2. **If no participant.time, derive from encounter status:**
   - Encounter `finished` → `completed`
   - Encounter `in-progress` → `active`
   - Encounter `planned` → `planned`
   - Encounter `cancelled` → `completed` (location was assigned)

**Examples:**

**Location with time period (completed):**
```xml
<participant typeCode="LOC">
  <time>
    <low value="202003151030-0500"/>
    <high value="202003151200-0500"/>
  </time>
  <participantRole>...</participantRole>
</participant>
```
→ `status`: `"completed"`, `period`: `{"start": "...", "end": "..."}`

**Location with only start time (active):**
```xml
<participant typeCode="LOC">
  <time>
    <low value="202003151030-0500"/>
  </time>
  <participantRole>...</participantRole>
</participant>
```
→ `status`: `"active"`, `period`: `{"start": "..."}`

**Location without time (derives from encounter):**
```xml
<encounter>
  <statusCode code="active"/>
  <participant typeCode="LOC">
    <participantRole>...</participantRole>
  </participant>
</encounter>
```
→ `status`: `"active"`, no period

Reference: [EncounterLocationStatus Value Set](http://hl7.org/fhir/R4/valueset-encounter-location-status.html)

### Reason Mapping

#### Reason Code (from Indication)

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <code code="75326-9" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="25064002" codeSystem="2.16.840.1.113883.6.96"
           displayName="Headache"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "25064002",
      "display": "Headache"
    }]
  }]
}
```

#### Reason Reference (to Condition)

If the indication references a problem that was converted to a Condition:

```json
{
  "reasonReference": [{
    "reference": "Condition/condition-headache"
  }]
}
```

### Diagnosis Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="SUBJ">
  <act classCode="ACT" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.80"/>
    <code code="29308-4" codeSystem="2.16.840.1.113883.6.1"
          displayName="Diagnosis"/>
    <entryRelationship typeCode="SUBJ">
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
        <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"
               displayName="Essential hypertension"/>
      </observation>
    </entryRelationship>
  </act>
</entryRelationship>
```

**FHIR Encounter:**
```json
{
  "diagnosis": [{
    "condition": {
      "reference": "Condition/condition-hypertension"
    },
    "use": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
        "code": "AD",
        "display": "Admission diagnosis"
      }]
    }
  }]
}
```

#### Diagnosis Role Detection

C-CDA Encounter Diagnosis Act does not explicitly encode diagnosis roles (admission, discharge, billing, etc.). The converter infers the appropriate `diagnosis.use` code from encounter context:

**Detection Logic:**

| Encounter Context | Diagnosis Role | Code | Rationale |
|-------------------|----------------|------|-----------|
| Has discharge disposition | Discharge diagnosis | `DD` | Discharge info indicates diagnosis documented at discharge |
| Inpatient class (IMP/ACUTE/NONAC) | Admission diagnosis | `AD` | Inpatient encounters document admission diagnoses |
| Emergency class (EMER) | Admission diagnosis | `AD` | Emergency diagnoses documented at presentation |
| All other encounters | Billing | `billing` | Default for outpatient/ambulatory encounters |

**Available Diagnosis Role Codes:**

| Code | Display | Use Case |
|------|---------|----------|
| `AD` | Admission diagnosis | Hospital/facility admission diagnosis |
| `DD` | Discharge diagnosis | Final diagnosis at discharge |
| `billing` | Billing | General documentation/billing diagnosis |
| `CC` | Chief complaint | Primary presenting complaint |
| `CM` | Comorbidity diagnosis | Comorbid condition |
| `pre-op` | Pre-op diagnosis | Pre-operative diagnosis |
| `post-op` | Post-op diagnosis | Post-operative diagnosis |

Reference: [DiagnosisRole CodeSystem](http://terminology.hl7.org/CodeSystem/diagnosis-role)

**FHIR Condition:**
The encounter diagnosis maps identically to problem conversion, with category set to `encounter-diagnosis`:

```json
{
  "resourceType": "Condition",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/condition-category",
      "code": "encounter-diagnosis"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "I10",
      "display": "Essential hypertension"
    }]
  }
}
```

### Discharge Disposition

**C-CDA:**
```xml
<sdtc:dischargeDispositionCode code="01" codeSystem="2.16.840.1.113883.12.112"
                                displayName="Discharged to home self care"/>
```

**FHIR:**
```json
{
  "hospitalization": {
    "dischargeDisposition": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
        "code": "home",
        "display": "Home"
      }]
    }
  }
}
```

**Common Discharge Disposition Mappings:**

| CDA Code | FHIR Code | Display |
|----------|-----------|---------|
| 01 | `home` | Home |
| 02 | `other-hcf` | Other Healthcare Facility |
| 03 | `snf` | Skilled Nursing Facility |
| 04 | `aama` | Against Medical Advice |
| 05 | `oth` | Other |
| 06 | `exp` | Expired |

### Admission Source

**Admission source** indicates where the patient came from before admission (e.g., emergency department, physician referral, transfer). C-CDA does not explicitly encode admission source, but it can be intelligently inferred from encounter characteristics:

**Detection Logic:**

| Encounter Characteristic | Admission Source | Code | Rationale |
|-------------------------|------------------|------|-----------|
| Emergency class (EMER) | From emergency department | `emd` | Emergency encounters originate from ED |
| priorityCode = "EM" (Emergency) | From emergency department | `emd` | Emergency priority indicates ED admission |
| Inpatient class without priority | Other | `other` | General inpatient admission |
| Ambulatory/Outpatient | — | — | No admission source for outpatient encounters |

**C-CDA (Emergency encounter):**
```xml
<encounter classCode="ENC" moodCode="EVN">
  <code code="EMER" codeSystem="2.16.840.1.113883.5.4" displayName="Emergency"/>
  <statusCode code="completed"/>
  <effectiveTime value="20230101"/>
</encounter>
```

**FHIR:**
```json
{
  "hospitalization": {
    "admitSource": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/admit-source",
        "code": "emd",
        "display": "From accident/emergency department"
      }]
    }
  }
}
```

**C-CDA (Emergency priority):**
```xml
<encounter classCode="ENC" moodCode="EVN">
  <code code="IMP" codeSystem="2.16.840.1.113883.5.4" displayName="Inpatient"/>
  <priorityCode code="EM" codeSystem="2.16.840.1.113883.5.7" displayName="Emergency"/>
  <statusCode code="completed"/>
  <effectiveTime value="20230101"/>
</encounter>
```

**FHIR:**
```json
{
  "hospitalization": {
    "admitSource": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/admit-source",
        "code": "emd",
        "display": "From accident/emergency department"
      }]
    }
  }
}
```

**Available Admission Source Codes:**

| Code | Display | Use Case |
|------|---------|----------|
| `emd` | From accident/emergency department | Patient transferred from hospital's ED |
| `hosp-trans` | Transferred from other hospital | Inter-hospital transfer |
| `outp` | From outpatient department | Outpatient to inpatient transition |
| `born` | Born in hospital | Newborn |
| `gp` | General Practitioner referral | GP referral |
| `mp` | Medical Practitioner/physician referral | Specialist referral |
| `nursing` | From nursing home | Nursing home transfer |
| `psych` | From psychiatric hospital | Psychiatric facility transfer |
| `rehab` | From rehabilitation facility | Rehab facility transfer |
| `other` | Other | Source not specified |

Reference: [AdmitSource CodeSystem](http://terminology.hl7.org/CodeSystem/admit-source)

**Note:** Admission source is only applicable for inpatient/hospital encounters. Outpatient encounters typically do not have an admission source.

## Document Header Encounter

The `encompassingEncounter` in the document header can also create an Encounter:

**C-CDA:**
```xml
<componentOf>
  <encompassingEncounter>
    <id root="2.16.840.1.113883.19.5" extension="ENC-12345"/>
    <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
    <effectiveTime>
      <low value="20200315103000-0500"/>
      <high value="20200315120000-0500"/>
    </effectiveTime>
    <responsibleParty>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      </assignedEntity>
    </responsibleParty>
    <location>
      <healthCareFacility>
        <id root="2.16.840.1.113883.19.5" extension="LOC-001"/>
        <location>
          <name>City Medical Center</name>
        </location>
      </healthCareFacility>
    </location>
  </encompassingEncounter>
</componentOf>
```

Maps similarly to Encounter Activity.

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Encounter.identifier` | `encounter/id` | Identifier → ID |
| `Encounter.status` | `encounter/statusCode` | Reverse status map |
| `Encounter.class` | `encounter/code` (if V3 ActCode) | Coding → CE |
| `Encounter.type` | `encounter/code` or translation | CodeableConcept → CE |
| `Encounter.period.start` | `encounter/effectiveTime/low` | Date format |
| `Encounter.period.end` | `encounter/effectiveTime/high` | Date format |
| `Encounter.participant` | `encounter/performer` | Create performer |
| `Encounter.participant.type` | `performer/functionCode` | CodeableConcept → CE |
| `Encounter.location` | `participant[@typeCode='LOC']` | Create participant |
| `Encounter.reasonCode` | Indication observation | Create entryRelationship |
| `Encounter.reasonReference` | Indication observation | Reference to problem |
| `Encounter.diagnosis` | Encounter Diagnosis Act | Create entryRelationship |
| `Encounter.hospitalization.admitSource` | `encounter/code` + `priorityCode` (inferred) | Intelligent inference |
| `Encounter.hospitalization.dischargeDisposition` | `sdtc:dischargeDispositionCode` | CodeableConcept → CE |

### FHIR Status to CDA

| FHIR status | CDA statusCode |
|-------------|----------------|
| `finished` | `completed` |
| `in-progress` | `active` |
| `cancelled` | `cancelled` |
| `entered-in-error` | — (do not convert) |
| `planned` | `new` |
| `arrived` | `active` |
| `triaged` | `active` |
| `onleave` | `active` |
| `unknown` | `completed` (with nullFlavor) |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
  <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
  <title>ENCOUNTERS</title>
  <entry typeCode="DRIV">
    <encounter classCode="ENC" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.49" extension="2015-08-01"/>
      <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
      <code code="99213" codeSystem="2.16.840.1.113883.6.12"
            displayName="Office or other outpatient visit">
        <translation code="AMB" codeSystem="2.16.840.1.113883.5.4"
                     displayName="Ambulatory"/>
      </code>
      <effectiveTime>
        <low value="20200315103000-0500"/>
        <high value="20200315120000-0500"/>
      </effectiveTime>
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name><given>Adam</given><family>Careful</family></name>
          </assignedPerson>
        </assignedEntity>
      </performer>
      <participant typeCode="LOC">
        <participantRole classCode="SDLOC">
          <playingEntity classCode="PLC">
            <name>Community Health Clinic</name>
          </playingEntity>
        </participantRole>
      </participant>
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
          <code code="75326-9" codeSystem="2.16.840.1.113883.6.1"/>
          <value xsi:type="CD" code="25064002" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Headache"/>
        </observation>
      </entryRelationship>
    </encounter>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Encounter",
  "id": "encounter-office-visit",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:2a620155-9d11-439e-92b3-5d9815ff4de8"
  }],
  "status": "finished",
  "class": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
    "code": "AMB",
    "display": "ambulatory"
  },
  "type": [{
    "coding": [{
      "system": "http://www.ama-assn.org/go/cpt",
      "code": "99213",
      "display": "Office or other outpatient visit"
    }]
  }],
  "subject": {
    "reference": "Patient/patient-example"
  },
  "participant": [{
    "individual": {
      "reference": "Practitioner/practitioner-careful",
      "display": "Adam Careful"
    }
  }],
  "period": {
    "start": "2020-03-15T10:30:00-05:00",
    "end": "2020-03-15T12:00:00-05:00"
  },
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "25064002",
      "display": "Headache"
    }]
  }],
  "location": [{
    "location": {
      "display": "Community Health Clinic"
    }
  }]
}
```

## References

- [C-CDA on FHIR Encounters Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html)
- [US Core Encounter Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-encounter)
- [C-CDA Encounter Activity](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.49.html)
