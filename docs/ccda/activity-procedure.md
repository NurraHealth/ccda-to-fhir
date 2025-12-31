# C-CDA: Procedure Activity

## Overview

Procedures in C-CDA are documented using Procedure Activity templates that can be represented as procedures, acts, or observations depending on the type of procedure. The Procedures Section describes all historical or current interventional, surgical, diagnostic, or therapeutic procedures or treatments pertinent to the patient at the time the document is generated.

**Scope:** This includes surgical interventions, diagnostic activities, endoscopic work, biopsies, counseling, rehabilitation services, and other comparable clinical actions performed by healthcare professionals or patients themselves. Procedures may be executed by healthcare professionals or patients themselves. Notable procedures are required; all procedures may be included for the summarized timeframe.

### RIM Classification

The common notion of "procedure" is broader than that specified by the HL7 Version 3 Reference Information Model (RIM). Therefore procedure templates can be represented with various RIM classes:

| RIM Class | Use Case | Example |
|-----------|----------|---------|
| procedure | Procedures whose immediate and primary outcome is the alteration of the physical condition of the patient | Appendectomy, hip replacement, gastrostomy creation |
| act | Procedures that cannot be classified as observations or procedures per HL7 RIM | Dressing change, patient teaching, feeding, comfort measures, consent |
| observation | Procedures that generate new information about the patient without physical alteration | Diagnostic imaging, EEG, EKG |

This template can be used with a contained Product Instance template to represent a device in or on a patient. Devices applied during a procedure (e.g., cardiac pacemaker, gastrostomy tube, port catheter), whether permanent or temporary, are represented within the Procedure Activity Procedure template.

## Template Information

| Attribute | Value |
|-----------|-------|
| Procedure Activity Procedure Template ID | `2.16.840.1.113883.10.20.22.4.14` |
| Procedure Activity Act Template ID | `2.16.840.1.113883.10.20.22.4.12` |
| Procedure Activity Observation Template ID | `2.16.840.1.113883.10.20.22.4.13` |
| Template Version (Extension) - R2.1 | 2014-06-09 |
| Template Version (Extension) - R5.0 | 2024-05-01 (Procedure Activity Procedure only) |
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.7.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.7` |
| LOINC Code | 47519-4 |
| LOINC Display | History of Procedures Document |
| LOINC Code System OID | 2.16.840.1.113883.6.1 |

### Template URLs (FHIR IG)
| Template | URL |
|----------|-----|
| Procedure Activity Procedure | `http://hl7.org/cda/us/ccda/StructureDefinition/ProcedureActivityProcedure` |
| Procedure Activity Act | `http://hl7.org/cda/us/ccda/StructureDefinition/ProcedureActivityAct` |
| Procedure Activity Observation | `http://hl7.org/cda/us/ccda/StructureDefinition/ProcedureActivityObservation` |
| Procedures Section | `http://hl7.org/cda/us/ccda/StructureDefinition/ProceduresSection` |

### Section Types

| Section Type | Template ID | Entry Requirement |
|--------------|-------------|-------------------|
| Procedures Section (entries required) | `2.16.840.1.113883.10.20.22.2.7.1` | SHALL contain at least one Procedure Activity Procedure entry (or nullFlavor) |
| Procedures Section (entries optional) | `2.16.840.1.113883.10.20.22.2.7` | MAY contain entries |

The "entries required" section is used in Continuity of Care Documents (CCD) and Transfer Summaries where procedure documentation is mandatory.

**Section Constraint:** If section/@nullFlavor is not present, SHALL contain at least one entry conformant to Procedure Activity Procedure.

### Section Subsections

Subsections MAY be used to partition entries into different categories:
| LOINC Code | Display | Use Case |
|------------|---------|----------|
| 18748-4 | Diagnostic Imaging | Radiological and imaging procedures |
| 11502-2 | Clinical Laboratory | Laboratory procedures |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Procedures Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.7.1']
                ├── code [@code='47519-4']
                └── entry
                    ├── procedure [Procedure Activity Procedure]
                    ├── act [Procedure Activity Act]
                    └── observation [Procedure Activity Observation]
```

## XML Structure

### Procedure Activity Procedure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.7.1" extension="2014-06-09"/>
  <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"
        displayName="History of Procedures Document"/>
  <title>PROCEDURES</title>
  <text>
    <table>
      <thead>
        <tr><th>Procedure</th><th>Date</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="procedure1">Laparoscopic Appendectomy</td>
          <td>March 1, 2015</td>
          <td>Completed</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <procedure classCode="PROC" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.14" extension="2014-06-09"/>
      <!-- For C-CDA R5.0, use extension="2024-05-01" -->
      <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>

      <!-- Procedure Code (USCDI requirement) -->
      <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
            displayName="Laparoscopic appendectomy">
        <originalText>
          <reference value="#procedure1"/>
        </originalText>
        <translation code="44970" codeSystem="2.16.840.1.113883.6.12"
                     displayName="Laparoscopic appendectomy"/>
        <translation code="0DTJ4ZZ" codeSystem="2.16.840.1.113883.6.4"
                     displayName="Resection of Appendix, Percutaneous Endoscopic"/>
      </code>

      <text>
        <reference value="#procedure1"/>
      </text>

      <!-- Negation Indicator (optional) - indicates procedure was NOT performed -->
      <!-- <negationInd value="true"/> -->

      <!-- Status -->
      <statusCode code="completed"/>

      <!-- Procedure Date/Time -->
      <effectiveTime value="20150301"/>

      <!-- Priority -->
      <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                    displayName="Routine"/>

      <!-- Method -->
      <methodCode code="51316009" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Laparoscopic procedure"/>

      <!-- Approach Site (optional) - anatomical approach to target site -->
      <!-- <approachSiteCode code="255580003" codeSystem="2.16.840.1.113883.6.96"
                            displayName="Percutaneous approach"/> -->

      <!-- Target Site (Body Site) - location where procedure was performed -->
      <!-- For implanted devices, records location on/in patient's body -->
      <targetSiteCode code="66754008" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Appendix structure"/>

      <!-- Performer -->
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <!-- Performer Specialty (sdtc extension) -->
          <sdtc:specialty code="208600000X" codeSystem="2.16.840.1.113883.6.101"
                          displayName="Surgery"/>
          <addr nullFlavor="UNK"/>
          <telecom nullFlavor="UNK"/>
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

      <!-- Informant (optional) - source of information -->
      <!-- <informant>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedEntity>
      </informant> -->

      <!-- Author -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20150301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <!-- Service Delivery Location -->
      <participant typeCode="LOC">
        <participantRole classCode="SDLOC">
          <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
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

      <!-- Indication (Reason for Procedure) -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2014-06-09"/>
          <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
          <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"
                displayName="Clinical finding"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="74400008" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Appendicitis"/>
        </observation>
      </entryRelationship>

      <!-- Specimen (if obtained) -->
      <specimen>
        <specimenRole>
          <id root="c2ee9ee9-ae31-4628-a919-fec1cbb58683"/>
          <specimenPlayingEntity>
            <code code="119376003" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Tissue specimen"/>
          </specimenPlayingEntity>
        </specimenRole>
      </specimen>

      <!-- Product/Device Participant -->
      <participant typeCode="DEV">
        <participantRole classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
          <id root="eb936010-7b17-11db-9fe1-0800200c9a68"/>
          <playingDevice>
            <code code="40388003" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Implant"/>
          </playingDevice>
          <scopingEntity>
            <id root="2.16.840.1.113883.3.3719"/>
          </scopingEntity>
        </participantRole>
      </participant>

      <!-- Instruction (Patient Instructions) -->
      <entryRelationship typeCode="SUBJ" inversionInd="true">
        <act classCode="ACT" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.20" extension="2014-06-09"/>
          <code code="311401005" codeSystem="2.16.840.1.113883.6.96"
                displayName="Patient education"/>
          <text>
            <reference value="#instruction1"/>
          </text>
          <statusCode code="completed"/>
        </act>
      </entryRelationship>

      <!-- Medication Activity (medication used during procedure) -->
      <entryRelationship typeCode="COMP">
        <substanceAdministration classCode="SBADM" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
          <!-- medication details -->
        </substanceAdministration>
      </entryRelationship>

      <!-- Reaction Observation (adverse reaction during procedure) -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.9" extension="2014-06-09"/>
          <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="422587007" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Nausea"/>
        </observation>
      </entryRelationship>

      <!-- Encounter Reference (links to encounter in another section) -->
      <entryRelationship typeCode="COMP" inversionInd="true">
        <encounter classCode="ENC" moodCode="EVN">
          <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
        </encounter>
      </entryRelationship>

      <!-- UDI Organizer (for medical devices) - C-CDA R5.0+ -->
      <!-- <entryRelationship typeCode="COMP" inversionInd="true">
        <organizer>
          <templateId root="2.16.840.1.113883.10.20.22.4.312"/>
          ...UDI Organizer details...
        </organizer>
      </entryRelationship> -->

      <!-- Assessment Scale Observation (for SDOH interventions) - C-CDA R5.0+ -->
      <!-- MAY contain LOINC Q&A pairs from SDOH screening instruments -->
      <!-- <entryRelationship typeCode="RSON">
        <observation>
          <templateId root="2.16.840.1.113883.10.20.22.4.69"/>
          ...Assessment Scale Observation details...
        </observation>
      </entryRelationship> -->

      <!-- Entry Reference (for SDOH procedures) - C-CDA R5.0+ -->
      <!-- MAY refer to Assessment Scale Observations -->
      <!-- <entryRelationship typeCode="RSON">
        <act>
          <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
          ...Entry Reference details...
        </act>
      </entryRelationship> -->

    </procedure>
  </entry>
</section>
```

### Procedure Activity Act

Used for procedures that cannot be classified as observations or procedures per HL7 RIM standards (dressing changes, patient teaching, feeding, comfort measures, consent, counseling):

```xml
<entry typeCode="DRIV">
  <act classCode="ACT" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.12" extension="2014-06-09"/>
    <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85e"/>

    <!-- Procedure Code -->
    <code code="171207006" codeSystem="2.16.840.1.113883.6.96"
          displayName="Depression screening">
      <originalText>
        <reference value="#act1"/>
      </originalText>
    </code>

    <text>
      <reference value="#act1"/>
    </text>

    <!-- Status (REQUIRED) -->
    <statusCode code="completed"/>

    <!-- Effective Time (REQUIRED for Act) -->
    <effectiveTime value="20150301"/>

    <!-- Priority -->
    <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                  displayName="Routine"/>

    <!-- Performer -->
    <performer>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <addr nullFlavor="UNK"/>
        <telecom nullFlavor="UNK"/>
        <assignedPerson>
          <name>
            <given>Adam</given>
            <family>Careful</family>
          </name>
        </assignedPerson>
        <representedOrganization>
          <id root="2.16.840.1.113883.19.5.9999.1393"/>
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

    <!-- Author -->
    <author>
      <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
      <time value="20150301"/>
      <assignedAuthor>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      </assignedAuthor>
    </author>

    <!-- Service Delivery Location -->
    <participant typeCode="LOC">
      <participantRole classCode="SDLOC">
        <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
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

    <!-- Indication (Reason) -->
    <entryRelationship typeCode="RSON">
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2014-06-09"/>
        <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
        <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"
              displayName="Clinical finding"/>
        <statusCode code="completed"/>
        <value xsi:type="CD" code="35489007" codeSystem="2.16.840.1.113883.6.96"
               displayName="Depressive disorder"/>
      </observation>
    </entryRelationship>

    <!-- Instruction -->
    <entryRelationship typeCode="SUBJ" inversionInd="true">
      <act classCode="ACT" moodCode="INT">
        <templateId root="2.16.840.1.113883.10.20.22.4.20" extension="2014-06-09"/>
        <code code="311401005" codeSystem="2.16.840.1.113883.6.96"
              displayName="Patient education"/>
        <statusCode code="completed"/>
      </act>
    </entryRelationship>

    <!-- Encounter Reference -->
    <entryRelationship typeCode="COMP" inversionInd="true">
      <encounter classCode="ENC" moodCode="EVN">
        <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
      </encounter>
    </entryRelationship>

  </act>
</entry>
```

### Procedure Activity Observation

Used for procedures that generate new information about the patient without physical alteration (diagnostic imaging, EEG, EKG):

```xml
<entry typeCode="DRIV">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.13" extension="2014-06-09"/>
    <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85f"/>

    <!-- Procedure Code -->
    <code code="24627-2" codeSystem="2.16.840.1.113883.6.1"
          displayName="Chest X-ray PA and lateral">
      <originalText>
        <reference value="#obs1"/>
      </originalText>
    </code>

    <text>
      <reference value="#obs1"/>
    </text>

    <!-- Status (REQUIRED) -->
    <statusCode code="completed"/>

    <!-- Effective Time -->
    <effectiveTime value="20150301"/>

    <!-- Priority -->
    <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7"
                  displayName="Routine"/>

    <!-- Value (REQUIRED) - multiple data types allowed -->
    <value xsi:type="CD" code="260385009" codeSystem="2.16.840.1.113883.6.96"
           displayName="Negative"/>

    <!-- Method (SHALL NOT conflict with code) -->
    <methodCode code="363680008" codeSystem="2.16.840.1.113883.6.96"
                displayName="Radiographic imaging procedure"/>

    <!-- Target Site(s) -->
    <targetSiteCode code="51185008" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Thoracic structure"/>

    <!-- Performer -->
    <performer>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567891"/>
        <addr nullFlavor="UNK"/>
        <telecom nullFlavor="UNK"/>
        <assignedPerson>
          <name>
            <given>Paula</given>
            <family>Periwinkle</family>
          </name>
        </assignedPerson>
        <representedOrganization>
          <id root="2.16.840.1.113883.19.5.9999.1394"/>
          <name>Good Health Radiology</name>
          <telecom use="WP" value="tel:+1(555)555-6000"/>
          <addr>
            <streetAddressLine>2000 Medical Drive</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>99123</postalCode>
          </addr>
        </representedOrganization>
      </assignedEntity>
    </performer>

    <!-- Author -->
    <author>
      <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
      <time value="20150301"/>
      <assignedAuthor>
        <id root="2.16.840.1.113883.4.6" extension="1234567891"/>
      </assignedAuthor>
    </author>

    <!-- Service Delivery Location -->
    <participant typeCode="LOC">
      <participantRole classCode="SDLOC">
        <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
        <code code="1179-1" codeSystem="2.16.840.1.113883.6.259"
              displayName="Radiology unit"/>
        <addr>
          <streetAddressLine>2000 Medical Drive</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>
        <playingEntity classCode="PLC">
          <name>Good Health Radiology</name>
        </playingEntity>
      </participantRole>
    </participant>

    <!-- Indication (Reason) -->
    <entryRelationship typeCode="RSON">
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2014-06-09"/>
        <id root="db734647-fc99-424c-a864-7e3cda82e704"/>
        <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"
              displayName="Clinical finding"/>
        <statusCode code="completed"/>
        <value xsi:type="CD" code="49727002" codeSystem="2.16.840.1.113883.6.96"
               displayName="Cough"/>
      </observation>
    </entryRelationship>

    <!-- Instruction -->
    <entryRelationship typeCode="SUBJ" inversionInd="true">
      <act classCode="ACT" moodCode="INT">
        <templateId root="2.16.840.1.113883.10.20.22.4.20" extension="2014-06-09"/>
        <code code="311401005" codeSystem="2.16.840.1.113883.6.96"
              displayName="Patient education"/>
        <statusCode code="completed"/>
      </act>
    </entryRelationship>

    <!-- Medication Activity -->
    <entryRelationship typeCode="COMP">
      <substanceAdministration classCode="SBADM" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
        <!-- contrast agent details -->
      </substanceAdministration>
    </entryRelationship>

    <!-- Reaction Observation -->
    <entryRelationship typeCode="COMP">
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.9" extension="2014-06-09"/>
        <id root="4adc1020-7b14-11db-9fe1-0800200c9a67"/>
        <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
        <statusCode code="completed"/>
        <value xsi:type="CD" nullFlavor="NA"/>
      </observation>
    </entryRelationship>

    <!-- Encounter Reference -->
    <entryRelationship typeCode="COMP" inversionInd="true">
      <encounter classCode="ENC" moodCode="EVN">
        <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
      </encounter>
    </entryRelationship>

  </observation>
</entry>
```

## Element Details

### procedure/code

The procedure code identifying what was performed. This is a USCDI requirement.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Procedure code | Yes |
| @codeSystem | Code system OID | Yes |
| @displayName | Human-readable display | No |
| originalText/reference | Link to narrative (SHALL begin with '#') | SHOULD |
| translation | Additional code mappings | No |

**Common Code Systems:**
| OID | URI | Name | Use |
|-----|-----|------|-----|
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT | Primary (SHOULD use) |
| 2.16.840.1.113883.6.1 | `http://loinc.org` | LOINC | Primary (SHOULD use) |
| 2.16.840.1.113883.6.12 | `http://www.ama-assn.org/go/cpt` | CPT-4 | Billing (MAY use) |
| 2.16.840.1.113883.6.4 | `http://www.cms.gov/Medicare/Coding/ICD10` | ICD-10-PCS | Inpatient (MAY use) |
| 2.16.840.1.113883.6.13 | `http://www.ada.org/cdt` | CDT-2 | Dental (MAY use) |
| 2.16.840.1.113883.6.14 | `http://www.ama-assn.org/go/hcpcs` | HCPCS | Supplies/Services |
| 2.16.840.1.113883.6.104 | N/A | ICD-9-CM Vol 3 | Legacy |

**Code Selection Guidance (CONF:1098-19207):**
- Code **SHOULD** be selected from LOINC (2.16.840.1.113883.6.1) or SNOMED CT (2.16.840.1.113883.6.96)
- Code **MAY** be selected from CPT-4 (2.16.840.1.113883.6.12), ICD-10-PCS (2.16.840.1.113883.6.4), or CDT-2 (2.16.840.1.113883.6.13)
- For SDOH procedures, use codes from Social Determinants of Health Procedures value set

**Value Set Bindings (C-CDA R5.0+):**
| Value Set | OID | Binding |
|-----------|-----|---------|
| US Core Procedure Codes | N/A | Preferred |
| Social Determinants of Health Procedures | N/A | Preferred (for SDOH) |

### negationInd

Optional boolean attribute indicating whether the procedure was NOT performed. When `true`, indicates the procedure was explicitly not done.

```xml
<!-- Procedure was NOT performed -->
<procedure classCode="PROC" moodCode="EVN" negationInd="true">
  ...
</procedure>
```

### statusCode

The status of the procedure. Bound to `ProcedureAct statusCode` value set (OID: `2.16.840.1.113883.11.20.9.22`) with required conformance.

| Code | Display | Description |
|------|---------|-------------|
| completed | Completed | Procedure has been completed |
| active | Active | Procedure is in progress |
| aborted | Aborted | Procedure was terminated |
| cancelled | Cancelled | Procedure was cancelled before starting |

Code System: `ActStatus` (`2.16.840.1.113883.5.14`)

### effectiveTime

When the procedure was performed. This is a USCDI Performance Time requirement for Procedure Activity Procedure.

| Format | Description |
|--------|-------------|
| value="YYYYMMDD" | Single point in time (may be date or year only) |
| low/high | Time range for procedure duration |
| center | Center time point |
| width | Duration width |

```xml
<!-- Single time -->
<effectiveTime value="20150301"/>

<!-- Time range -->
<effectiveTime>
  <low value="20150301103000"/>
  <high value="20150301120000"/>
</effectiveTime>
```

**Constraints:**
- `ts-value-before-document` (ERROR): Time value SHALL be ≤ ClinicalDocument/effectiveTime
- `active-high-ts-after-document` (ERROR): If statusCode='active' and effectiveTime/high exists, high SHALL be after ClinicalDocument/effectiveTime
- For Procedure Activity Act: effectiveTime is REQUIRED (1..1)
- For Procedure Activity Procedure/Observation: effectiveTime is SHOULD (0..1)

### priorityCode

The urgency of the procedure. Bound to `ActPriority` value set (OID: `2.16.840.1.113883.1.11.16866`) with required conformance.

| Code | Display | Description |
|------|---------|-------------|
| R | Routine | Regular scheduling |
| A | ASAP | As soon as possible |
| UR | Urgent | Requires urgent attention |
| EM | Emergency | Emergency procedure |
| S | Stat | Immediate |
| CR | Callback results | For results callback |
| CS | Callback for scheduling | For scheduling callback |

Code System: `ActPriority` (`2.16.840.1.113883.5.7`)

### methodCode

The method or technique used.

**Constraint (CONF:1098-7890):** methodCode **SHALL NOT** conflict with the method inherent in Procedure/code.

**Common Method Codes (SNOMED CT - 2.16.840.1.113883.6.96):**
| Code | Display |
|------|---------|
| 51316009 | Laparoscopic procedure |
| 129304002 | Excision - action |
| 129303009 | Repair - action |
| 257867005 | Insertion - action |
| 281615006 | Biopsy of site |
| 118673008 | Procedure on head |
| 363680008 | Radiographic imaging procedure |
| 277132007 | Therapeutic procedure |

### targetSiteCode

The body site where the procedure was performed. Bound to `Body Site Value Set` (OID: `2.16.840.1.113883.3.88.12.3221.8.9`) with required conformance.

For Procedure Activity Procedure, this element is also used to record the location of an implanted medical device.

**Common Body Site Codes (SNOMED CT - 2.16.840.1.113883.6.96):**
| Code | Display |
|------|---------|
| 66754008 | Appendix structure |
| 64033007 | Kidney structure |
| 80891009 | Heart structure |
| 39607008 | Lung structure |
| 71341001 | Bone structure |
| 76752008 | Breast structure |
| 51185008 | Thoracic structure |
| 302509004 | Entire heart |
| 368208006 | Left upper arm |

### approachSiteCode

The anatomical approach used to access the target site. Optional element for Procedure Activity Procedure.

```xml
<approachSiteCode code="255580003" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Percutaneous approach"/>
```

**Common Approach Site Codes (SNOMED CT):**
| Code | Display |
|------|---------|
| 255580003 | Percutaneous approach |
| 103388001 | Transabdominal approach |
| 6921000 | Transcervical approach |
| 420185003 | Endoscopic approach |

### languageCode

Optional element specifying the language used during the procedure or for documentation. Bound to `AllLanguages` value set with required conformance.

```xml
<languageCode code="en-US"/>
```

### sdtcCategory (Extension)

Optional extension element for categorizing procedures. Allows multiple categories.

```xml
<sdtc:category code="387713003" codeSystem="2.16.840.1.113883.6.96"
               displayName="Surgical procedure"/>
```

### performer

Who performed the procedure. SHOULD be present.

| Element | Description | Required |
|---------|-------------|----------|
| assignedEntity/id | Performer identifier (NPI) | Yes (1..*) |
| assignedEntity/sdtc:specialty | Performer specialty (extension) | No |
| assignedEntity/addr | Address | Yes (1..*) |
| assignedEntity/telecom | Contact information | Yes (1..*) |
| assignedEntity/assignedPerson/name | Performer name | SHOULD |
| assignedEntity/representedOrganization | Organization | SHOULD |
| assignedEntity/representedOrganization/id | Organization identifier | SHOULD |
| assignedEntity/representedOrganization/telecom | Organization contact | Yes (1..*) |
| assignedEntity/representedOrganization/addr | Organization address | Yes (1..*) |

**Performer Specialty Binding:**
- Value Set: Practice Setting Code Value Set
- Binding: Preferred

### participant[@typeCode='LOC']

The location where the procedure was performed.

| Element | Description |
|---------|-------------|
| participantRole/@classCode | SDLOC (Service Delivery Location) |
| participantRole/code | Facility type code |
| participantRole/addr | Location address |
| playingEntity/name | Location name |

**Facility Type Codes (HealthcareServiceLocation):**
| Code | Display |
|------|---------|
| 1160-1 | Urgent Care Center |
| 1061-3 | Hospital |
| 1118-1 | Emergency Department |
| 1116-5 | Ambulatory Surgical Center |
| 1021-7 | Critical Care Unit |

### entryRelationship[@typeCode='RSON'] (Indication)

The reason/indication for the procedure.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.19` |
| code | 75321-0 (Clinical finding) from LOINC |
| value | Condition code (ICD/SNOMED) |

## Procedure Types Mapping

| C-CDA Element | classCode | moodCode | Use Case | Example |
|---------------|-----------|----------|----------|---------|
| procedure | PROC | EVN | Surgical/therapeutic procedures that alter physical condition | Appendectomy, hip replacement, gastrostomy |
| act | ACT | EVN | Administrative procedures not classifiable as observations or procedures | Dressing change, patient teaching, feeding, comfort measures, consent |
| observation | OBS | EVN | Diagnostic procedures that generate new information | X-ray, EEG, EKG, lab test |

### Choosing the Right Template

1. **Use Procedure Activity Procedure** when the procedure's primary outcome is alteration of the physical condition of the patient. Also use when representing devices applied during procedures.

2. **Use Procedure Activity Act** for actions that are neither physical procedures nor diagnostic observations. These include administrative activities, counseling, and routine care activities.

3. **Use Procedure Activity Observation** when the procedure generates diagnostic information about the patient without physically altering them.

## Conformance Requirements

### Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14)

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| @classCode | 1..1 | SHALL | Fixed: PROC |
| @moodCode | 1..1 | SHALL | Fixed: EVN |
| @negationInd | 0..1 | MAY | Indicates procedure was NOT performed |
| templateId | 1..1 | SHALL | root=2.16.840.1.113883.10.20.22.4.14, extension=2014-06-09 (or 2024-05-01 for R5.0) |
| id | 1..* | SHALL | At least one identifier |
| code | 1..1 | SHALL | From LOINC/SNOMED (SHOULD) or CPT/ICD-10-PCS/CDT (MAY); USCDI requirement |
| code/originalText/reference | 0..1 | SHOULD | **SHALL** begin with '#' and point to narrative (CONF:1098-19206) |
| text/reference | 0..1 | SHOULD | **SHALL** begin with '#' |
| statusCode | 1..1 | SHALL | From ProcedureAct statusCode value set; nullFlavor prohibited |
| effectiveTime | 1..1 | SHALL (R5.0) / SHOULD (R2.1) | USCDI Performance Time |
| effectiveTime/@value | 0..1 | SHOULD | Point-in-time (may be date or year only) |
| effectiveTime/low | 0..1 | MAY | Procedure start |
| effectiveTime/high | 0..1 | MAY | Procedure end (constraint: active-high-ts-after-document) |
| priorityCode | 0..1 | MAY | From ActPriority value set |
| languageCode | 0..1 | MAY | From AllLanguages value set |
| methodCode | 0..1 | MAY | **SHALL NOT** conflict with inherent method (CONF:4515-7890) |
| approachSiteCode | 0..* | MAY | Anatomical approach |
| targetSiteCode | 0..* | SHOULD | From Body Site Value Set; for device location |
| sdtc:category | 0..* | MAY | Procedure categorization (extension) |
| specimen | 0..* | MAY | Specimens obtained from procedure (CONF:1098-16842) |
| specimen/specimenRole/id | 0..* | SHOULD | CONF:4515-29744 |
| performer | 0..* | SHOULD | Who performed the procedure |
| performer/assignedEntity/sdtc:specialty | 0..* | MAY | Performer specialty (extension) |
| author | 0..* | SHOULD | AuthorParticipation template |
| informant | 0..* | MAY | Information source |
| participant[@typeCode='DEV'] | 0..* | MAY | Product Instance (device) |
| participant[@typeCode='LOC'] | 0..* | MAY | Service Delivery Location |
| entryRelationship[@typeCode='COMP'] (encounter) | 0..* | MAY | Encounter reference (CONF:4515-16843) |
| entryRelationship[@typeCode='SUBJ'] (instruction) | 0..1 | MAY | Instruction Observation template |
| entryRelationship[@typeCode='RSON'] (indication) | 0..* | MAY | Indication template |
| entryRelationship[@typeCode='COMP'] (medication) | 0..* | MAY | Medication Activity template |
| entryRelationship[@typeCode='COMP'] (reaction) | 0..* | MAY | Reaction Observation template |
| entryRelationship[@typeCode='COMP'] (udiOrganizer) | 0..* | MAY | UDI Organizer (R5.0+) |
| entryRelationship[@typeCode='RSON'] (assessmentScale) | 0..* | MAY | Assessment Scale Observation (R5.0+, for SDOH) |
| entryRelationship[@typeCode='RSON'] (entryReference) | 0..* | MAY | Entry Reference (R5.0+, for SDOH) |

**Key Constraints:**
| ID | Level | Description |
|----|-------|-------------|
| CONF:4515-7890 | ERROR | methodCode SHALL NOT conflict with method inherent in code |
| CONF:4515-16842 | - | For specimens obtained from procedure |
| CONF:4515-29744 | SHOULD | Procedure/specimen/specimenRole/id SHOULD equal Organizer/specimen/specimenRole/id if same specimen |
| CONF:4515-16843 | - | Encounter ID should match encounter in other sections |
| should-text-ref-value | WARNING | SHOULD contain text/reference/@value |
| should-otext-ref-value | WARNING | SHOULD contain originalText/reference/@value |
| should-targetSiteCode | WARNING | SHOULD contain targetSiteCode |
| should-performer | WARNING | SHOULD contain performer |
| should-author | WARNING | SHOULD contain author |
| ts-value-before-document | ERROR | Time value ≤ ClinicalDocument/effectiveTime |
| active-high-ts-after-document | ERROR | If active with high time, must be after document effectiveTime |
| value-starts-octothorpe | ERROR | Reference values SHALL begin with '#' |

### Procedure Activity Act (2.16.840.1.113883.10.20.22.4.12)

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| @classCode | 1..1 | SHALL | Fixed: ACT |
| @moodCode | 1..1 | SHALL | Fixed: EVN |
| @negationInd | 0..1 | MAY | Indicates act was NOT performed |
| templateId | 1..1 | SHALL | root=2.16.840.1.113883.10.20.22.4.12, extension=2014-06-09 |
| id | 1..* | SHALL | At least one identifier |
| code | 1..1 | SHALL | From LOINC/SNOMED (SHOULD) or CPT/ICD-10-PCS/CDT (MAY) (CONF:1098-19190) |
| code/originalText/reference | 0..1 | SHOULD | **SHALL** begin with '#' (CONF:1098-19189) |
| text/reference | 0..1 | SHOULD | **SHALL** begin with '#' |
| statusCode | 1..1 | SHALL | From ProcedureAct statusCode value set (OID: 2.16.840.1.113883.11.20.9.22) |
| effectiveTime | 1..1 | SHALL | When act was performed (REQUIRED for Act) |
| priorityCode | 0..1 | MAY | From ActPriority value set (OID: 2.16.840.1.113883.1.11.16866) |
| languageCode | 0..1 | MAY | From HumanLanguage value set |
| performer | 0..* | SHOULD | Who performed the act |
| performer/assignedEntity/id | 1..* | SHALL | At least one identifier |
| performer/assignedEntity/addr | 1..* | SHALL | At least one address |
| performer/assignedEntity/telecom | 1..* | SHALL | At least one contact |
| performer/assignedEntity/representedOrganization | 0..1 | SHOULD | Organization |
| author | 0..* | SHOULD | AuthorParticipation template |
| informant | 0..* | MAY | Information source |
| participant[@typeCode='LOC'] | 0..* | MAY | Service Delivery Location |
| entryRelationship[@typeCode='COMP'] (encounter) | 0..* | MAY | Encounter reference (CONF:1098-16849) |
| entryRelationship[@typeCode='SUBJ'] (instruction) | 0..1 | MAY | Instruction template |
| entryRelationship[@typeCode='RSON'] (indication) | 0..* | MAY | Indication template |
| entryRelationship[@typeCode='COMP'] (medication) | 0..* | MAY | Medication Activity template |

**Medication Activity Constraint:** If Medication Activity is included, it SHOULD contain doseQuantity OR rateQuantity.

### Procedure Activity Observation (2.16.840.1.113883.10.20.22.4.13)

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| @classCode | 1..1 | SHALL | Fixed: OBS (CONF:1098-8282) |
| @moodCode | 1..1 | SHALL | Fixed: EVN (CONF:1098-8237) |
| @negationInd | 0..1 | MAY | Indicates observation was NOT performed |
| templateId | 1..1 | SHALL | root=2.16.840.1.113883.10.20.22.4.13, extension=2014-06-09 |
| id | 1..* | SHALL | At least one identifier (CONF:1098-8239) |
| code | 1..1 | SHALL | From LOINC/SNOMED (SHOULD) or CPT/ICD-10-PCS/CDT (MAY) (CONF:1098-19197, CONF:1098-19202) |
| code/originalText | 0..1 | SHOULD | CONF:1098-19198 |
| code/originalText/reference | 0..1 | SHOULD | **SHALL** begin with '#' (CONF:1098-19201) |
| text/reference | 0..1 | SHOULD | **SHALL** begin with '#' |
| statusCode | 1..1 | SHALL | From ProcedureAct statusCode value set (CONF:1098-8245) |
| effectiveTime | 0..1 | SHOULD | When observation was performed (CONF:1098-8246) |
| priorityCode | 0..1 | MAY | From ActPriority value set (CONF:1098-8247) |
| value | 1..1 | SHALL | Result value - multiple data types allowed (CONF:1098-16846) |
| methodCode | 0..1 | MAY | **SHALL NOT** conflict with code (CONF:1098-8248, CONF:1098-8249) |
| targetSiteCode | 0..* | SHOULD | From Body Site Value Set (CONF:1098-8250) |
| performer | 0..* | SHOULD | Who performed the observation (CONF:1098-8251) |
| performer/assignedEntity/id | 1..* | SHALL | At least one identifier |
| performer/assignedEntity/addr | 1..* | SHALL | At least one address |
| performer/assignedEntity/telecom | 1..* | SHALL | At least one contact |
| author | 0..* | MAY | AuthorParticipation template |
| participant[@typeCode='LOC'] | 0..* | MAY | Service Delivery Location |
| entryRelationship[@typeCode='COMP'] (encounter) | 0..* | MAY | Encounter reference (CONF:1098-16847) |
| entryRelationship[@typeCode='SUBJ'] (instruction) | 0..1 | MAY | Instruction template |
| entryRelationship[@typeCode='RSON'] (indication) | 0..* | MAY | Indication template |
| entryRelationship[@typeCode='COMP'] (medication) | 0..* | MAY | Medication Activity template |
| entryRelationship[@typeCode='MFST'] (reaction) | 0..* | MAY | Reaction Observation template |

**Value Data Types:** The value element for Procedure Activity Observation supports multiple data types: BL, ED, ST, CD, CV, CE, SC, II, TEL, AD, EN, INT, REAL, PQ, MO, TS, IVL_PQ, IVL_TS, PIVL_TS, EIVL_TS, SXPR_TS, RTO_PQ_PQ. If no appropriate value exists, use nullFlavor.

**Code System Bindings:**
| Element | Value Set | Code System OID |
|---------|-----------|-----------------|
| code | ObservationType | V3 standard |
| statusCode | ProcedureAct statusCode | 2.16.840.1.113883.11.20.9.22 |
| targetSiteCode | Body Site Value Set | 2.16.840.1.113883.3.88.12.3221.8.9 |
| priorityCode | ActPriority | 2.16.840.1.113883.1.11.16866 |
| methodCode | ObservationMethod | V3 standard |

### Procedures Section (entries required) (2.16.840.1.113883.10.20.22.2.7.1)

| Element | Cardinality | Conformance | Notes |
|---------|-------------|-------------|-------|
| @classCode | 1..1 | SHALL | Fixed: DOCSECT |
| @moodCode | 1..1 | SHALL | Fixed: EVN |
| @nullFlavor | 0..1 | MAY | May be "NI" if section contains no data |
| templateId (primary) | 1..1 | SHALL | root=2.16.840.1.113883.10.20.22.2.7 |
| templateId (secondary) | 1..1 | SHALL | root=2.16.840.1.113883.10.20.22.2.7.1, extension=2014-06-09 |
| code | 1..1 | SHALL | LOINC 47519-4 |
| title | 1..1 | SHALL | Section heading |
| text | 1..1 | SHALL | Human-readable narrative (xhtml) |
| confidentialityCode | 0..1 | MAY | Confidentiality level |
| languageCode | 0..1 | MAY | From AllLanguages value set |
| subject | 0..1 | MAY | Subject of section |
| author | 0..* | MAY | Section author(s) |
| informant | 0..* | MAY | Information source(s) |
| entry | 1..* | SHALL | At least one entry required |
| component | 0..* | MAY | Subsections for categorization |

**Entry Constraint (shall-procedure-act-procedure):** If section/@nullFlavor is not present, SHALL contain at least one entry conformant to Procedure Activity Procedure.

**Document Types Using This Section:**
- Consultation Note
- Continuity of Care Document (CCD)
- Discharge Summary
- History and Physical
- Procedure Note
- Referral Note
- Transfer Summary

## Related Templates

| Template | OID | Description |
|----------|-----|-------------|
| Author Participation | `2.16.840.1.113883.10.20.22.4.119` | Records author information |
| Service Delivery Location | `2.16.840.1.113883.10.20.22.4.32` | Location where procedure was performed |
| Product Instance | `2.16.840.1.113883.10.20.22.4.37` | Device used/implanted during procedure |
| Indication | `2.16.840.1.113883.10.20.22.4.19` | Reason for the procedure |
| Instruction | `2.16.840.1.113883.10.20.22.4.20` | Patient instructions (legacy) |
| Instruction Observation | `2.16.840.1.113883.10.20.22.4.20` | Patient instructions (R5.0+) |
| Medication Activity | `2.16.840.1.113883.10.20.22.4.16` | Medications used during procedure |
| Reaction Observation | `2.16.840.1.113883.10.20.22.4.9` | Adverse reactions during procedure |
| UDI Organizer | `2.16.840.1.113883.10.20.22.4.312` | Unique Device Identifier (R5.0+) |
| Assessment Scale Observation | `2.16.840.1.113883.10.20.22.4.69` | For SDOH screening instruments (R5.0+) |
| Entry Reference | `2.16.840.1.113883.10.20.22.4.122` | Reference to other entries (R5.0+) |

### Templates Using Procedure Activity

Procedure Activity Procedure is used by:
- Anesthesia Section
- Intervention Act
- Medical Equipment Organizer
- Medical Equipment Section
- Procedures Section
- Reaction Observation

## Value Sets

| Value Set Name | OID | Binding | Usage |
|----------------|-----|---------|-------|
| ProcedureAct statusCode | `2.16.840.1.113883.11.20.9.22` | Required | statusCode element |
| ActPriority | `2.16.840.1.113883.1.11.16866` | Required | priorityCode element |
| Body Site Value Set | `2.16.840.1.113883.3.88.12.3221.8.9` | Required | targetSiteCode element |
| US Core Procedure Codes | N/A | Preferred | code element (R5.0+) |
| Social Determinants of Health Procedures | N/A | Preferred | SDOH procedure codes (R5.0+) |
| AllLanguages | N/A | Required | languageCode element |
| CDANullFlavor | N/A | Required | nullFlavor attribute |
| Problem Type | SNOMED CT subset | - | Indication/code element |
| Problem | SNOMED CT subset | - | Indication/value element |
| HealthcareServiceLocation | `2.16.840.1.113883.6.259` | - | Service delivery location code |
| Practice Setting Code Value Set | N/A | Preferred | Performer specialty (sdtc:specialty) |
| ObservationType | V3 standard | - | Observation code element |
| ObservationMethod | V3 standard | - | methodCode element |

## References

### C-CDA Implementation Guides
- C-CDA R2.1 Implementation Guide Section 3.76 (Procedure Activity Procedure)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- C-CDA R2.2 StructureDefinitions: https://build.fhir.org/ig/HL7/CDA-ccda-2.2/

### Template Documentation
- HL7 C-CDA Templates Search: http://www.hl7.org/ccdasearch/
- HL7 C-CDA Examples Repository: https://github.com/HL7/C-CDA-Examples
- Procedure Activity Procedure Examples: https://cdasearch.hl7.org/examples/view/Guide%20Examples/Procedure%20Activity%20Procedure%20(V2)_2.16.840.1.113883.10.20.22.4.14
- Procedure Activity Act Examples: https://cdasearch.hl7.org/examples/view/Guide%20Examples/Procedure%20Activity%20Act%20(V2)_2.16.840.1.113883.10.20.22.4.12
- Procedure Activity Observation Examples: https://cdasearch.hl7.org/examples/view/Guide%20Examples/Procedure%20Activity%20Observation%20(V2)_2.16.840.1.113883.10.20.22.4.13

### Code Systems
- SNOMED CT: http://snomed.info/sct (OID: 2.16.840.1.113883.6.96)
- LOINC: http://loinc.org (OID: 2.16.840.1.113883.6.1)
- CPT-4: https://www.ama-assn.org/practice-management/cpt (OID: 2.16.840.1.113883.6.12)
- ICD-10-PCS: https://www.cms.gov/Medicare/Coding/ICD10 (OID: 2.16.840.1.113883.6.4)
- CDT-2: https://www.ada.org/cdt (OID: 2.16.840.1.113883.6.13)
- HCPCS: https://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets (OID: 2.16.840.1.113883.6.14)
