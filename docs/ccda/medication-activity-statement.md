# C-CDA: Medication Activity (Event - Actual Use)

## Overview

The Medication Activity template with moodCode="EVN" (Event) documents actual medication use - medications that have been, are being, or were administered or consumed by the patient. This is distinct from medication orders or prescriptions (moodCode="INT"), representing what actually happened rather than what was intended.

## Template Information

| Attribute | Value |
|-----------|-------|
| Medication Activity Template ID | `2.16.840.1.113883.10.20.22.4.16` |
| Template Version | 2014-06-09 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/MedicationActivity` |
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.1.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.1` |
| LOINC Code | 10160-0 |
| LOINC Display | History of Medication use Narrative |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Medications Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.1.1']
                ├── code [@code='10160-0']
                └── entry
                    └── substanceAdministration [Medication Activity - EVN]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.16']
                        ├── @moodCode='EVN'
                        ├── consumable/manufacturedProduct/manufacturedMaterial
                        └── entryRelationship (indications, instructions, etc.)
```

## Critical Distinction: moodCode="EVN" vs moodCode="INT"

The Medication Activity template supports both EVN (Event) and INT (Intent) mood codes, with fundamentally different meanings:

### moodCode="EVN" (Event) - This Document

**Meaning:** Reflects **actual medication use** - what was actually administered or taken by the patient.

**Use Case:** Documents medications that:
- Have actually been administered (pills ingested, injections given)
- Are currently being taken by the patient
- Were taken in the past

**Example Scenario:**
> "A clinician may intend that a patient be administered Lisinopril 20 mg PO for blood pressure control. If what was actually administered was Lisinopril 10 mg, then the Medication Activity in the 'EVN' mood would reflect the actual 10 mg dose."

**RepeatNumber in EVN mood:**
- Represents the **number of occurrences**
- Example: repeatNumber of "3" means the current administration is the 3rd in a series

**Maps to:** FHIR `MedicationStatement` resource

### moodCode="INT" (Intent) - See activity-medication.md

**Meaning:** Reflects **what a clinician intends** a patient to be taking.

**Use Case:** Documents planned or prescribed medications (orders, prescriptions)

**RepeatNumber in INT mood:**
- Represents the **number of allowed administrations**
- Example: repeatNumber of "3" means the substance can be administered up to 3 times

**Maps to:** FHIR `MedicationRequest` resource

**Note:** It is recommended that the Planned Medication Activity (V2) template be used for moodCodes other than EVN if the document type contains a section that includes Planned Medication Activity.

## XML Structure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.1.1" extension="2014-06-09"/>
  <code code="10160-0" codeSystem="2.16.840.1.113883.6.1"
        displayName="History of Medication use Narrative"/>
  <title>MEDICATIONS</title>
  <text>
    <table>
      <thead>
        <tr><th>Medication</th><th>Directions</th><th>Start Date</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="med1">atenolol 25 MG Oral Tablet</td>
          <td ID="sig1">Take 1 tablet by mouth every 12 hours</td>
          <td>March 18, 2012</td>
          <td>Active</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
      <id root="cdbd5410-6cde-11db-9fe1-0800200c9a66"/>

      <text>
        <reference value="#med1"/>
      </text>

      <!-- Status -->
      <statusCode code="active"/>

      <!-- Medication Period: Started March 18, 2012, ongoing -->
      <effectiveTime xsi:type="IVL_TS">
        <low value="20120318"/>
      </effectiveTime>

      <!-- Frequency (timing): Every 12 hours -->
      <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
        <period value="12" unit="h"/>
      </effectiveTime>

      <!-- Route -->
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Oral"/>

      <!-- Dose -->
      <doseQuantity value="1"/>

      <!-- Administration Unit -->
      <administrationUnitCode code="C48542" codeSystem="2.16.840.1.113883.3.26.1.1"
                              displayName="Tablet"/>

      <!-- Medication Information -->
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
          <manufacturedMaterial>
            <code code="197380" codeSystem="2.16.840.1.113883.6.88"
                  displayName="atenolol 25 MG Oral Tablet">
              <originalText>
                <reference value="#med1"/>
              </originalText>
              <translation code="00378-0025-01" codeSystem="2.16.840.1.113883.6.69"
                           displayName="Atenolol 25mg Tab"/>
            </code>
          </manufacturedMaterial>
          <manufacturerOrganization>
            <name>Mylan Pharmaceuticals Inc</name>
          </manufacturerOrganization>
        </manufacturedProduct>
      </consumable>

      <!-- Author (who documented this) -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20120318"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name>
              <given>Adam</given>
              <family>Careful</family>
              <suffix>MD</suffix>
            </name>
          </assignedPerson>
        </assignedAuthor>
      </author>

      <!-- Indication (reason for medication) -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2014-06-09"/>
          <id root="db734647-fc99-424c-a864-7e3cda82e705"/>
          <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"
                displayName="Clinical finding"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Hypertensive disorder"/>
        </observation>
      </entryRelationship>

      <!-- Instructions -->
      <entryRelationship typeCode="SUBJ" inversionInd="true">
        <act classCode="ACT" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.20" extension="2014-06-09"/>
          <code code="422037009" codeSystem="2.16.840.1.113883.6.96"
                displayName="Provider medication administration instructions"/>
          <text>
            <reference value="#sig1"/>
          </text>
          <statusCode code="completed"/>
        </act>
      </entryRelationship>

    </substanceAdministration>
  </entry>
</section>
```

## Element Details

### substanceAdministration/@classCode

**Value:** SBADM (Substance Administration)

**Required:** SHALL contain exactly one `@classCode="SBADM"`

### substanceAdministration/@moodCode

**Value for Actual Use:** EVN (Event)

**Required:** SHALL contain exactly one `@moodCode` selected from ValueSet MoodCodeEvnInt

| Code | Display | Description |
|------|---------|-------------|
| EVN | Event | Medication was actually administered/taken |
| INT | Intent | Medication is intended/prescribed (see activity-medication.md) |

**Important:** This document describes EVN mood. For INT mood, see activity-medication.md.

### negationInd

**Attribute:** `@negationInd="true"`

**Meaning:** When set to "true", this is a **positive assertion that the medication is negated** - the medication is NOT being taken or was NOT administered.

**Use Case:** To document that a medication is NOT being taken (patient refused, discontinued, etc.)

**Important Note:**
> "A substance administration statement with negationInd is still a statement about the specific fact described by the SubstanceAdministration. For instance, a negated 'aspirin administration' means that the author positively denies that aspirin is being administered."

**Example:**
```xml
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
  <statusCode code="completed"/>
  <consumable>
    <manufacturedProduct>
      <manufacturedMaterial>
        <code code="308971" codeSystem="2.16.840.1.113883.6.88"
              displayName="Warfarin Sodium 5 MG Oral Tablet"/>
      </manufacturedMaterial>
    </manufacturedProduct>
  </consumable>
</substanceAdministration>
```

**Maps to FHIR:** `MedicationStatement.status = "not-taken"`

### statusCode

The status of the medication activity.

| Code | Display | Description |
|------|---------|-------------|
| active | Active | Medication is currently being taken |
| completed | Completed | Medication course is complete |
| aborted | Aborted | Medication was stopped/discontinued |
| cancelled | Cancelled | Medication was cancelled |
| suspended | Suspended | Medication is temporarily suspended |

**Required:** SHALL contain exactly one `statusCode` with required binding to Medication Status value set

### effectiveTime (Period)

The time period during which the medication was/is taken.

**Required:** SHALL contain exactly one `effectiveTime` indicating administration duration or single-administration timestamp

```xml
<!-- Start and end dates -->
<effectiveTime xsi:type="IVL_TS">
  <low value="20120318"/>
  <high value="20130318"/>
</effectiveTime>

<!-- Ongoing (no end date) -->
<effectiveTime xsi:type="IVL_TS">
  <low value="20120318"/>
</effectiveTime>

<!-- Single date -->
<effectiveTime xsi:type="IVL_TS" value="20120318"/>
```

**Constraint:** effectiveTime duration must contain either @value OR low/high, but not both

### effectiveTime (Frequency)

How often the medication was/is taken.

**Recommendation:** SHOULD contain frequency documentation via second effectiveTime

```xml
<!-- Every 12 hours (BID) -->
<effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
  <period value="12" unit="h"/>
</effectiveTime>

<!-- Once daily -->
<effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
  <period value="24" unit="h"/>
</effectiveTime>

<!-- Three times daily (TID) -->
<effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
  <period value="8" unit="h"/>
</effectiveTime>

<!-- Every 6 hours (Q6H) -->
<effectiveTime xsi:type="PIVL_TS" operator="A">
  <period value="6" unit="h"/>
</effectiveTime>

<!-- As needed (PRN) -->
<effectiveTime xsi:type="EIVL_TS" operator="A">
  <event code="PRN"/>
</effectiveTime>
```

### routeCode

How the medication was administered.

**Recommendation:** SHOULD contain `routeCode` when available

**Code System Requirements:**
- **Primary (Required):** NCI Thesaurus route codes (OID: `2.16.840.1.113883.3.26.1.1`)
- **Secondary (SHOULD include):** SNOMED CT translation

**Route Codes (NCI Thesaurus):**
| Code | Display |
|------|---------|
| C38288 | Oral |
| C38276 | Intravenous |
| C28161 | Intramuscular |
| C38299 | Subcutaneous |
| C38305 | Topical |
| C38284 | Nasal |
| C38287 | Intradermal |
| C38295 | Sublingual |
| C38246 | Rectal |
| C38192 | Ophthalmic |
| C38255 | Otic |
| C38291 | Transdermal |
| C38216 | Respiratory (Inhalation) |

**Translation Pattern:**

The C-CDA standard recommends including SNOMED CT translations of route codes:

```xml
<routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
           displayName="Oral">
  <translation code="26643006" codeSystem="2.16.840.1.113883.6.96"
               displayName="Oral route"/>
</routeCode>
```

**Common Route Translations:**
| NCI Code | NCI Display | SNOMED Code | SNOMED Display |
|----------|-------------|-------------|----------------|
| C38288 | Oral | 26643006 | Oral route |
| C38276 | Intravenous | 47625008 | Intravenous route |
| C28161 | Intramuscular | 78421000 | Intramuscular route |
| C38299 | Subcutaneous | 34206005 | Subcutaneous route |
| C38305 | Topical | 6064005 | Topical route |
| C38284 | Nasal | 46713006 | Nasal route |

### doseQuantity

Amount of medication per dose.

**Required:** SHALL contain exactly one `doseQuantity`

| Attribute | Description |
|-----------|-------------|
| @value | Numeric amount |
| @unit | Unit code (UCUM) |

**Dosing Rules:**
- **Pre-coordinated codes** (e.g., "metoprolol 25mg tablet"): doseQuantity is unitless count (e.g., "1 tablet")
- **Non-coordinated codes** (e.g., "metoprolol Oral Product"): doseQuantity requires physical units like mg

**Critical Constraint:** If doseQuantity/@unit is present, then administrationUnitCode SHALL NOT be present.

**Common Unit Codes:**
| Unit | Description |
|------|-------------|
| {tbl} | Tablet |
| {cap} | Capsule |
| mg | Milligram |
| mL | Milliliter |
| g | Gram |
| {puff} | Puff |
| {spray} | Spray |

### rateQuantity

Rate of administration (typically for IV medications).

```xml
<rateQuantity value="100" unit="mL/h"/>
```

### administrationUnitCode

The form of the medication dose.

**Administration Unit Codes (NCI):**
| Code | Display |
|------|---------|
| C48542 | Tablet |
| C48480 | Capsule |
| C42944 | Inhalant |
| C42953 | Solution |
| C42998 | Tablet, Extended Release |
| C48491 | Cream |
| C42966 | Ointment |
| C42986 | Syrup |
| C42905 | Spray |
| C42911 | Patch |

**Critical Constraint:** If doseQuantity/@unit exists, administrationUnitCode SHALL NOT be present.

### consumable/manufacturedProduct/manufacturedMaterial/code

The medication product code.

**Required:**
- consumable SHALL contain exactly one manufacturedProduct
- manufacturedProduct SHALL contain exactly one manufacturedMaterial
- manufacturedMaterial SHALL contain exactly one code

**Code Systems:**
| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.6.88 | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | NDC |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT |

### author

Who documented the medication use.

**Recommendation:** SHOULD contain `author` participation

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` |
| time | When this was documented |
| assignedAuthor | Person who documented |

**Note:** In EVN mood, the author is typically who documented the actual use, which may be the patient, a family member, or a clinician observing the medication use.

### Indication

The reason for taking the medication.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.19` |
| code | 75321-0 (Clinical finding) from LOINC |
| value | Condition code (ICD/SNOMED) |

```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Hypertensive disorder"/>
  </observation>
</entryRelationship>
```

### Instructions (Sig)

Patient instructions for taking the medication.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.20` |
| code | 422037009 (Provider medication administration instructions) |
| text/reference | Link to narrative text |

```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
    <code code="422037009" codeSystem="2.16.840.1.113883.6.96"/>
    <text>
      <reference value="#sig1"/>
    </text>
  </act>
</entryRelationship>
```

### repeatNumber

The number of occurrences for this medication administration event.

**Cardinality:** MAY contain zero or one [0..1] `repeatNumber`

| Attribute | Description |
|-----------|-------------|
| @value | Integer number of occurrences |

**Semantics in EVN mood:**
- Represents the **number of occurrences** (how many times the medication was/is administered in a series)
- Example: repeatNumber of "3" means this is the 3rd administration in a series

**Note:** This element is not commonly mapped to FHIR MedicationStatement as there is no direct equivalent element.

```xml
<repeatNumber value="3"/>
```

## Optional Entry Relationships

The Medication Activity template supports additional optional entryRelationships that provide supplementary information about the medication use.

### Medication Supply Order

Links to prescription/supply order information.

| Element | Description |
|---------|-------------|
| typeCode | REFR (refers to) |
| templateId | `2.16.840.1.113883.10.20.22.4.17` |
| Element | supply with moodCode="INT" |

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.17" extension="2014-06-09"/>
    <id root="..."/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
      <high value="20210301"/>
    </effectiveTime>
    <repeatNumber value="3"/>
    <quantity value="30" unit="{tbl}"/>
  </supply>
</entryRelationship>
```

### Medication Dispense

Information about actual dispensing events.

| Element | Description |
|---------|-------------|
| typeCode | REFR (refers to) |
| templateId | `2.16.840.1.113883.10.20.22.4.18` |
| Element | supply with moodCode="EVN" |

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
    <id root="..."/>
    <statusCode code="completed"/>
    <effectiveTime value="20200301"/>
    <quantity value="30" unit="{tbl}"/>
    <performer>
      <assignedEntity>
        <representedOrganization>
          <name>Community Pharmacy</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
  </supply>
</entryRelationship>
```

### Reaction Observation

Adverse reactions or side effects experienced from the medication.

| Element | Description |
|---------|-------------|
| typeCode | MFST (manifestation) |
| templateId | `2.16.840.1.113883.10.20.22.4.9` |
| Element | observation for reaction |

```xml
<entryRelationship typeCode="MFST" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.9" extension="2014-06-09"/>
    <id root="..."/>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <statusCode code="completed"/>
    <value xsi:type="CD" code="422587007" codeSystem="2.16.840.1.113883.6.96"
           displayName="Nausea"/>
  </observation>
</entryRelationship>
```

### Drug Monitoring Act

Drug level monitoring or therapeutic drug monitoring activities.

| Element | Description |
|---------|-------------|
| typeCode | COMP (has component) |
| templateId | `2.16.840.1.113883.10.20.22.4.123` |
| Element | act for drug monitoring |

```xml
<entryRelationship typeCode="COMP">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.123" extension="2014-06-09"/>
    <code code="395170001" codeSystem="2.16.840.1.113883.6.96"
          displayName="Medication monitoring"/>
  </act>
</entryRelationship>
```

### Substance Administered Act

Part of a series of administrations.

| Element | Description |
|---------|-------------|
| typeCode | COMP (has component) |
| templateId | `2.16.840.1.113883.10.20.22.4.118` |
| Element | act indicating series relationship |

### Medication Adherence

Adherence or compliance tracking information.

| Element | Description |
|---------|-------------|
| typeCode | COMP (has component) |
| templateId | `2.16.840.1.113883.10.20.37.4.3` (CMS) |
| Element | observation for adherence |

```xml
<entryRelationship typeCode="COMP">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.37.4.3"/>
    <code code="418633004" codeSystem="2.16.840.1.113883.6.96"
          displayName="Medication compliance"/>
    <value xsi:type="BL" value="true"/>
  </observation>
</entryRelationship>
```

### Medication Free Text Sig

Free-text signature/instructions when coded instructions are insufficient.

| Element | Description |
|---------|-------------|
| typeCode | COMP (has component) |
| templateId | `2.16.840.1.113883.10.20.22.4.147` |
| Element | substanceAdministration with free text |

### Drug Vehicle

Drug vehicle or carrier for IV medications or compounded preparations.

| Element | Description |
|---------|-------------|
| typeCode | CSM (consumable) |
| templateId | `2.16.840.1.113883.10.20.22.4.24` |
| Element | participantRole with drug vehicle |

```xml
<participant typeCode="CSM">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.24"/>
    <code code="412307009" codeSystem="2.16.840.1.113883.6.96"
          displayName="Drug vehicle"/>
    <playingEntity classCode="MMAT">
      <code code="324049" codeSystem="2.16.840.1.113883.6.88"
            displayName="Normal saline"/>
      <name>0.9% Sodium Chloride</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Precondition

Precondition or "as needed" (PRN) condition for medication use.

| Element | Description |
|---------|-------------|
| typeCode | PRCN (has precondition) |
| Element | criterion with assertion |

```xml
<precondition typeCode="PRCN">
  <criterion>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="25064002" codeSystem="2.16.840.1.113883.6.96"
           displayName="Headache"/>
  </criterion>
</precondition>
```

### Text Reference Constraint

**Important Conformance Rule:** If the medication activity contains a `text/reference/@value` element, it SHALL begin with '#' and SHALL point to the narrative section.

```xml
<text>
  <reference value="#med1"/>
</text>
```

**Constraint:** The reference value must:
- Begin with the '#' character
- Point to an element in the section's narrative `<text>` block with a matching `ID` attribute
- Example: `<reference value="#med1"/>` points to `<td ID="med1">...</td>` in the narrative

## Frequency Mapping Examples

| Description | C-CDA effectiveTime |
|-------------|---------------------|
| Once daily | `<period value="24" unit="h"/>` |
| BID (Twice daily) | `<period value="12" unit="h"/>` |
| TID (Three times daily) | `<period value="8" unit="h"/>` |
| QID (Four times daily) | `<period value="6" unit="h"/>` |
| Q4H (Every 4 hours) | `<period value="4" unit="h"/>` |
| Weekly | `<period value="1" unit="wk"/>` |
| Monthly | `<period value="1" unit="mo"/>` |

## Conformance Requirements

### Medication Activity (EVN mood)

1. **SHALL** contain exactly one `@classCode="SBADM"`
2. **SHALL** contain exactly one `@moodCode="EVN"` - Required binding to MoodCodeEvnInt
3. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.16`
4. **SHALL** contain at least one `id`
5. **SHALL** contain exactly one `statusCode` - Required binding to Medication Status value set
6. **SHALL** contain exactly one `effectiveTime` indicating administration duration or single-administration timestamp
7. **SHOULD** contain frequency documentation via second effectiveTime
8. **SHALL** contain exactly one `doseQuantity`
9. **SHALL** contain exactly one `consumable`
10. `consumable` **SHALL** contain exactly one `manufacturedProduct`
11. `manufacturedProduct` **SHALL** contain exactly one `manufacturedMaterial`
12. `manufacturedMaterial` **SHALL** contain exactly one `code`
13. **SHOULD** contain `routeCode` when available
14. **SHOULD** contain `author` participation

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| moodCode | MoodCodeEvnInt | Required |
| statusCode | Medication Status | Required |
| routeCode | SPL Drug Route | Required (primary), SNOMED translation (secondary) |
| doseQuantity unit | UCUM case-sensitive units | Preferred |
| approachSiteCode | Body Site Value Set | Preferred |
| administrationUnitCode | Pre-coordinated dose forms | Required |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| dose-unit-or-admin-unit | Error | If doseQuantity/@unit exists, administrationUnitCode cannot be present |
| 1098-32890 | Error | effectiveTime duration must contain either @value OR low/high, but not both |
| should-text-ref-value | Warning | Text references should begin with '#' and point to narrative |
| should-routeCode | Warning | Route should be documented when available |

## Examples

### Example 1: Currently Taking Medication

```xml
<entry typeCode="DRIV">
  <substanceAdministration classCode="SBADM" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
    <id root="cdbd5410-6cde-11db-9fe1-0800200c9a66"/>
    <statusCode code="active"/>

    <!-- Started March 18, 2012, ongoing -->
    <effectiveTime xsi:type="IVL_TS">
      <low value="20120318"/>
    </effectiveTime>

    <!-- Every 12 hours -->
    <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
      <period value="12" unit="h"/>
    </effectiveTime>

    <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
    <doseQuantity value="1"/>

    <consumable>
      <manufacturedProduct classCode="MANU">
        <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
        <manufacturedMaterial>
          <code code="197380" codeSystem="2.16.840.1.113883.6.88"
                displayName="atenolol 25 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </consumable>
  </substanceAdministration>
</entry>
```

### Example 2: Completed Medication Course

```xml
<entry typeCode="DRIV">
  <substanceAdministration classCode="SBADM" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
    <id root="a54f50a0-6cde-11db-9fe1-0800200c9a66"/>
    <statusCode code="completed"/>

    <!-- January 1 to December 31, 2023 -->
    <effectiveTime xsi:type="IVL_TS">
      <low value="20230101"/>
      <high value="20231231"/>
    </effectiveTime>

    <!-- Once daily -->
    <effectiveTime xsi:type="PIVL_TS" operator="A">
      <period value="1" unit="d"/>
    </effectiveTime>

    <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1" displayName="Oral"/>
    <doseQuantity value="10" unit="mg"/>

    <consumable>
      <manufacturedProduct>
        <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
        <manufacturedMaterial>
          <code code="197361" codeSystem="2.16.840.1.113883.6.88"
                displayName="Lisinopril 10 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </consumable>
  </substanceAdministration>
</entry>
```

### Example 3: Medication Refused (Negation)

```xml
<entry typeCode="DRIV">
  <substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
    <id root="b64f60b0-7cde-12db-9fe1-0800200c9a66"/>
    <statusCode code="completed"/>

    <effectiveTime xsi:type="IVL_TS">
      <low value="20240115"/>
    </effectiveTime>

    <consumable>
      <manufacturedProduct>
        <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
        <manufacturedMaterial>
          <code code="308971" codeSystem="2.16.840.1.113883.6.88"
                displayName="Warfarin Sodium 5 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </consumable>
  </substanceAdministration>
</entry>
```

## Relationship to Other Templates

### Related Templates
- **Medication Activity (INT mood)** - See activity-medication.md - Used for medication orders/prescriptions
- **Planned Medication Activity** - Template 2.16.840.1.113883.10.20.22.4.42 - Preferred for future planned medications
- **Medication Supply Order** - Template 2.16.840.1.113883.10.20.22.4.17 - Prescription/supply information
- **Medication Dispense** - Template 2.16.840.1.113883.10.20.22.4.18 - Dispensing events
- **Medication Information** - Template 2.16.840.1.113883.10.20.22.4.23 - Manufactured product details

## References

- C-CDA R2.1 Implementation Guide Section 3.47 (Medication Activity)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- C-CDA Medication Activity Structure Definition: http://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationActivity.html
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.16.html
- HL7 C-CDA Examples: https://github.com/HL7/C-CDA-Examples
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- NCI Thesaurus: https://ncit.nci.nih.gov/ncitbrowser/
