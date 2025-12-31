# C-CDA: Medication Activity

## Overview

Medications in C-CDA are documented using Medication Activity templates within the Medications Section. This template describes medications the patient is currently taking, has taken in the past, or is intended to take. Medications can be prescribed, dispensed, or administered.

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
                    └── substanceAdministration [Medication Activity]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.16']
                        ├── consumable/manufacturedProduct/manufacturedMaterial
                        └── entryRelationship (instructions, supply, etc.)
```

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
          <td ID="med1">Lisinopril 10 MG Oral Tablet</td>
          <td ID="sig1">Take 1 tablet by mouth once daily</td>
          <td>March 1, 2020</td>
          <td>Active</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="INT">
      <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
      <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>

      <text>
        <reference value="#med1"/>
      </text>

      <!-- Status -->
      <statusCode code="active"/>

      <!-- Medication Period -->
      <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
        <high nullFlavor="UNK"/>
      </effectiveTime>

      <!-- Frequency (timing) -->
      <effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
        <period value="24" unit="h"/>
      </effectiveTime>

      <!-- Route -->
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Oral"/>

      <!-- Dose -->
      <doseQuantity value="1" unit="{tbl}"/>

      <!-- Rate (for IV medications) -->
      <!-- <rateQuantity value="100" unit="mL/h"/> -->

      <!-- Administration Unit Code -->
      <administrationUnitCode code="C48542" codeSystem="2.16.840.1.113883.3.26.1.1"
                              displayName="Tablet"/>

      <!-- Medication Information -->
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
          <manufacturedMaterial>
            <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                  displayName="Lisinopril 10 MG Oral Tablet">
              <originalText>
                <reference value="#med1"/>
              </originalText>
              <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
                           displayName="Lisinopril 10mg Tab"/>
            </code>
          </manufacturedMaterial>
          <manufacturerOrganization>
            <name>Watson Pharmaceuticals Inc</name>
          </manufacturerOrganization>
        </manufacturedProduct>
      </consumable>

      <!-- Prescriber/Author -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20200301"/>
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
          <value xsi:type="CD" code="59621000" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Essential hypertension"/>
        </observation>
      </entryRelationship>

      <!-- Instructions (Sig) -->
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

      <!-- Medication Supply Order -->
      <entryRelationship typeCode="REFR">
        <supply classCode="SPLY" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.17" extension="2014-06-09"/>
          <id root="..."/>
          <statusCode code="completed"/>
          <effectiveTime xsi:type="IVL_TS">
            <low value="20200301"/>
            <high value="20210301"/>
          </effectiveTime>
          <repeatNumber value="3"/>
          <quantity value="30" unit="{tbl}"/>
          <author>
            <time value="20200301"/>
            <assignedAuthor>
              <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
            </assignedAuthor>
          </author>
        </supply>
      </entryRelationship>

      <!-- Medication Dispense -->
      <entryRelationship typeCode="REFR">
        <supply classCode="SPLY" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
          <id root="..."/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <quantity value="30" unit="{tbl}"/>
          <performer>
            <assignedEntity>
              <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
              <addr>
                <streetAddressLine>1001 Village Avenue</streetAddressLine>
                <city>Portland</city>
                <state>OR</state>
                <postalCode>99123</postalCode>
              </addr>
            </assignedEntity>
          </performer>
        </supply>
      </entryRelationship>

      <!-- Drug Vehicle (for IV medications) -->
      <participant typeCode="CSM">
        <participantRole classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.24"/>
          <code code="412307009" codeSystem="2.16.840.1.113883.6.96"
                displayName="Drug vehicle"/>
          <playingEntity classCode="MMAT">
            <code code="5% dextrose" codeSystem="2.16.840.1.113883.6.88"/>
            <name>5% Dextrose in Water</name>
          </playingEntity>
        </participantRole>
      </participant>

      <!-- Precondition -->
      <precondition typeCode="PRCN">
        <criterion>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <value xsi:type="CD" code="59621000" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Essential hypertension"/>
        </criterion>
      </precondition>

    </substanceAdministration>
  </entry>
</section>
```

## Element Details

### substanceAdministration/@moodCode

The intent of the medication activity. INT (intent) or EVN (event) are allowed, though INT is recommended only when the document lacks dedicated Planned Medication Activity sections.

| Code | Display | Description |
|------|---------|-------------|
| INT | Intent | Medication is intended/prescribed |
| EVN | Event | Medication was actually administered |

### statusCode

The status of the medication activity.

| Code | Display | Description |
|------|---------|-------------|
| active | Active | Medication is currently active |
| completed | Completed | Medication course is complete |
| aborted | Aborted | Medication was stopped |
| cancelled | Cancelled | Medication was cancelled |
| suspended | Suspended | Medication is temporarily suspended |

### effectiveTime (Period)

The time period during which the medication is taken.

```xml
<!-- Start and end dates -->
<effectiveTime xsi:type="IVL_TS">
  <low value="20200301"/>
  <high value="20210301"/>
</effectiveTime>

<!-- Ongoing (no end date) -->
<effectiveTime xsi:type="IVL_TS">
  <low value="20200301"/>
  <high nullFlavor="UNK"/>
</effectiveTime>
```

### effectiveTime (Frequency)

How often the medication is taken.

```xml
<!-- Once daily -->
<effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
  <period value="24" unit="h"/>
</effectiveTime>

<!-- Twice daily (BID) -->
<effectiveTime xsi:type="PIVL_TS" institutionSpecified="true" operator="A">
  <period value="12" unit="h"/>
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

How the medication is administered.

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

**Code System:** `2.16.840.1.113883.3.26.1.1` (NCI Thesaurus)

### doseQuantity

Amount of medication per dose. This is a **required** element.

| Attribute | Description |
|-----------|-------------|
| @value | Numeric amount |
| @unit | Unit code (UCUM) |

**Dosing Rules:**
- **Pre-coordinated codes** (e.g., "metoprolol 25mg tablet"): doseQuantity is unitless count (e.g., "1 tablet")
- **Non-coordinated codes** (e.g., "metoprolol Oral Product"): doseQuantity requires physical units like mg

**Critical Constraint:** If doseQuantity/@unit is present, then administrationUnitCode SHALL NOT be present (dose-unit-or-admin-unit constraint).

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

Rate of administration (for IV medications).

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

### consumable/manufacturedProduct/manufacturedMaterial/code

The medication product code.

**Code Systems:**
| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.6.88 | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | NDC |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT |

### Medication Supply Order

Information about the prescription/order.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.17` |
| effectiveTime | Validity period of prescription |
| repeatNumber | Number of refills |
| quantity | Amount dispensed per fill |

### Medication Dispense

Information about the dispensing event.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.18` |
| effectiveTime | Dispense date |
| quantity | Amount dispensed |
| performer | Dispensing pharmacy |

### Instructions (Sig)

Patient instructions for taking the medication.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.20` |
| code | 422037009 (Provider medication administration instructions) |
| text/reference | Link to narrative text |

### Indication

The reason for taking the medication.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.19` |
| code | 75321-0 (Clinical finding) from LOINC |
| value | Condition code (ICD/SNOMED) |

## Frequency Mapping Examples

| FHIR Timing | C-CDA effectiveTime |
|-------------|---------------------|
| Once daily | `<period value="24" unit="h"/>` |
| BID | `<period value="12" unit="h"/>` |
| TID | `<period value="8" unit="h"/>` |
| QID | `<period value="6" unit="h"/>` |
| Q4H | `<period value="4" unit="h"/>` |
| Weekly | `<period value="1" unit="wk"/>` |
| Monthly | `<period value="1" unit="mo"/>` |

## Conformance Requirements

### Medication Activity
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.16`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `moodCode` (EVN or INT) - Required binding to MoodCodeEvnInt
4. **SHALL** contain exactly one `statusCode` - Required binding to Medication Status value set
5. **SHALL** contain exactly one `effectiveTime` indicating administration duration or single-administration timestamp
6. **SHOULD** contain frequency documentation (e.g., "every 8 hours") via second effectiveTime
7. **SHALL** contain exactly one `doseQuantity`
8. **SHALL** contain exactly one `consumable`
9. `consumable` **SHALL** contain exactly one `manufacturedProduct`
10. `manufacturedProduct` **SHALL** contain exactly one `manufacturedMaterial`
11. `manufacturedMaterial` **SHALL** contain exactly one `code`
12. **SHOULD** contain `routeCode` when available
13. **SHOULD** contain `author` participation

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

## Optional Entry Relationships

The template supports nested entries for:
- Indications (reason for medication)
- Instructions and adherence monitoring
- Supply orders and dispensing records
- Adverse reactions
- Drug monitoring activities

## Documentation Context

This template appears in multiple sections including medications lists, admission/discharge medications, and anesthesia records across various CDA document types.

## References

- C-CDA R2.1 Implementation Guide Section 3.47 (Medication Activity)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- NCI Thesaurus: https://ncit.nci.nih.gov/ncitbrowser/
