# C-CDA: Result Organizer

## Overview

The Result Organizer provides a mechanism for grouping related result observations. It contains information applicable to all of the contained result observations, such as panel/battery code, status, effective time, specimen, and authorship. Result organizers typically represent laboratory panels (e.g., CBC, metabolic panel), imaging studies, or other grouped diagnostic test results.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.1` |
| Extension | 2023-05-01 |
| Version | 5.0.0-ballot (STU5) |
| URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ResultOrganizer` |
| ClassCode | CLUSTER (fixed) |
| MoodCode | EVN (fixed) |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Results Section]
                └── entry
                    └── organizer [Result Organizer]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.1']
                        ├── id
                        ├── code (panel/battery code)
                        ├── statusCode
                        ├── effectiveTime
                        ├── author (optional)
                        ├── specimen (optional)
                        └── component
                            └── observation [Result Observation]
```

## XML Structure

### Complete Blood Count Panel Example

```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <!-- Template ID -->
  <templateId root="2.16.840.1.113883.10.20.22.4.1" extension="2023-05-01"/>

  <!-- Organizer ID -->
  <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>

  <!-- Panel/Battery Code -->
  <code code="58410-2"
        codeSystem="2.16.840.1.113883.6.1"
        displayName="CBC panel - Blood by Automated count">
    <originalText>
      <reference value="#panel1"/>
    </originalText>
  </code>

  <!-- Status -->
  <statusCode code="completed"/>

  <!-- Effective Time -->
  <effectiveTime value="20200301083000-0500"/>

  <!-- SDTC Category (optional) -->
  <sdtc:category xmlns:sdtc="urn:hl7-org:sdtc">
    <sdtc:code code="HM"
               codeSystem="2.16.840.1.113883.12.74"
               displayName="Hematology"/>
  </sdtc:category>

  <!-- SDTC Text Reference (optional) -->
  <sdtc:text>
    <reference value="#panel1"/>
  </sdtc:text>

  <!-- Author -->
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20200301153000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <addr>
        <streetAddressLine>123 Lab Street</streetAddressLine>
        <city>Boston</city>
        <state>MA</state>
        <postalCode>02134</postalCode>
      </addr>
      <telecom use="WP" value="tel:+1-617-555-1234"/>
      <assignedPerson>
        <name>
          <prefix>Dr.</prefix>
          <given>Sarah</given>
          <family>Pathologist</family>
        </name>
      </assignedPerson>
      <representedOrganization>
        <id root="2.16.840.1.113883.4.6" extension="9999999999"/>
        <name>Community Hospital Laboratory</name>
        <telecom use="WP" value="tel:+1-617-555-1000"/>
        <addr>
          <streetAddressLine>123 Lab Street</streetAddressLine>
          <city>Boston</city>
          <state>MA</state>
          <postalCode>02134</postalCode>
        </addr>
      </representedOrganization>
    </assignedAuthor>
  </author>

  <!-- Specimen -->
  <specimen typeCode="SPC">
    <specimenRole classCode="SPEC">
      <id root="c2ee9ee9-ae31-4628-a919-fec1cbb58683"/>
      <specimenPlayingEntity>
        <code code="122555007"
              codeSystem="2.16.840.1.113883.6.96"
              displayName="Venous blood specimen"/>
      </specimenPlayingEntity>
    </specimenRole>
  </specimen>

  <!-- Result Observations (components) -->
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
      <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
      <code code="718-7"
            codeSystem="2.16.840.1.113883.6.1"
            displayName="Hemoglobin [Mass/volume] in Blood"/>
      <text><reference value="#result1"/></text>
      <statusCode code="completed"/>
      <effectiveTime value="20200301083000-0500"/>
      <value xsi:type="PQ" value="13.2" unit="g/dL"/>
      <interpretationCode code="N"
                         codeSystem="2.16.840.1.113883.5.83"
                         displayName="Normal"/>
      <referenceRange>
        <observationRange>
          <value xsi:type="IVL_PQ">
            <low value="12.0" unit="g/dL"/>
            <high value="16.0" unit="g/dL"/>
          </value>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
        </observationRange>
      </referenceRange>
    </observation>
  </component>

  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
      <id root="8b3fa370-67a5-11db-bd13-0800200c9a66"/>
      <code code="26464-8"
            codeSystem="2.16.840.1.113883.6.1"
            displayName="Leukocytes [#/volume] in Blood"/>
      <text><reference value="#result2"/></text>
      <statusCode code="completed"/>
      <effectiveTime value="20200301083000-0500"/>
      <value xsi:type="PQ" value="6.7" unit="10*9/L"/>
      <interpretationCode code="N"
                         codeSystem="2.16.840.1.113883.5.83"
                         displayName="Normal"/>
      <referenceRange>
        <observationRange>
          <value xsi:type="IVL_PQ">
            <low value="4.3" unit="10*9/L"/>
            <high value="10.8" unit="10*9/L"/>
          </value>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
        </observationRange>
      </referenceRange>
    </observation>
  </component>

  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
      <id root="a40027e1-67a5-11db-bd13-0800200c9a66"/>
      <code code="777-3"
            codeSystem="2.16.840.1.113883.6.1"
            displayName="Platelets [#/volume] in Blood"/>
      <text><reference value="#result3"/></text>
      <statusCode code="completed"/>
      <effectiveTime value="20200301083000-0500"/>
      <value xsi:type="PQ" value="250" unit="10*9/L"/>
      <interpretationCode code="N"
                         codeSystem="2.16.840.1.113883.5.83"
                         displayName="Normal"/>
      <referenceRange>
        <observationRange>
          <value xsi:type="IVL_PQ">
            <low value="150" unit="10*9/L"/>
            <high value="400" unit="10*9/L"/>
          </value>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
        </observationRange>
      </referenceRange>
    </observation>
  </component>
</organizer>
```

### Metabolic Panel Example

```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.1" extension="2023-05-01"/>
  <id root="a2b33520-67a5-11db-bd13-0800200c9a66"/>

  <code code="24323-8"
        codeSystem="2.16.840.1.113883.6.1"
        displayName="Comprehensive metabolic 2000 panel - Serum or Plasma"/>

  <statusCode code="completed"/>
  <effectiveTime value="20200301090000-0500"/>

  <!-- Specimen -->
  <specimen typeCode="SPC">
    <specimenRole classCode="SPEC">
      <id root="d8aef2a0-5e3c-4e4f-b7c1-9876543210ab"/>
      <specimenPlayingEntity>
        <code code="119364003"
              codeSystem="2.16.840.1.113883.6.96"
              displayName="Serum specimen"/>
      </specimenPlayingEntity>
    </specimenRole>
  </specimen>

  <!-- Components: glucose, creatinine, sodium, potassium, etc. -->
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
      <id root="c1234567-89ab-cdef-0123-456789abcdef"/>
      <code code="2345-7"
            codeSystem="2.16.840.1.113883.6.1"
            displayName="Glucose [Mass/volume] in Serum or Plasma"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200301090000-0500"/>
      <value xsi:type="PQ" value="95" unit="mg/dL"/>
      <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
      <referenceRange>
        <observationRange>
          <value xsi:type="IVL_PQ">
            <low value="70" unit="mg/dL"/>
            <high value="100" unit="mg/dL"/>
          </value>
        </observationRange>
      </referenceRange>
    </observation>
  </component>
  <!-- Additional components omitted for brevity -->
</organizer>
```

## Element Details

### Root Element: organizer

| Attribute | Cardinality | Value | Description |
|-----------|------------|-------|-------------|
| classCode | 1..1 | CLUSTER | Fixed value indicating a cluster/battery |
| moodCode | 1..1 | EVN | Fixed value indicating an event (actual occurrence) |

**Note on classCode:** The C-CDA specification requires `classCode="CLUSTER"`. While `BATTERY` is sometimes seen in examples and is semantically similar, implementations should use `CLUSTER` for consistency and standards compliance.

### templateId

| Element | Cardinality | Description |
|---------|------------|-------------|
| root | 1..1 | SHALL be `2.16.840.1.113883.10.20.22.4.1` |
| extension | 0..1 | SHOULD be `2023-05-01` |

### id

| Element | Cardinality | Description |
|---------|------------|-------------|
| id | 1..* | Unique identifier(s) for the organizer. At least one required. |

**Implementation Note:** Use UUID or OID format. This identifier should be unique across all result organizers in the system.

### code

The code identifies the panel or battery of tests. **SHALL** be present.

| Element | Cardinality | Type | Description |
|---------|------------|------|-------------|
| code | 1..1 | CD | Panel/battery code |

**Conformance:**
- **SHOULD** be selected from LOINC (2.16.840.1.113883.6.1) OR SNOMED CT (2.16.840.1.113883.6.96)
- Use LOINC panel codes when available
- May include originalText with reference to narrative

**Common Laboratory Panel Codes (LOINC):**
| Code | Display |
|------|---------|
| 58410-2 | CBC panel - Blood by Automated count |
| 24323-8 | Comprehensive metabolic 2000 panel - Serum or Plasma |
| 24331-1 | Lipid panel - Serum or Plasma |
| 57021-8 | CBC W Auto Differential panel - Blood |
| 24356-8 | Urinalysis complete panel - Urine |
| 2345-7 | Glucose [Mass/volume] in Serum or Plasma |
| 51990-0 | Basic metabolic panel - Blood |

### statusCode

| Element | Cardinality | Description |
|---------|------------|-------------|
| statusCode | 1..1 | Status of the organizer. Required. |
| @code | 1..1 | Status code value |

**Value Set:** Result Status (2.16.840.1.113883.11.20.9.39) - Required binding

**Status Code Values:**
| Code | Display | Definition |
|------|---------|------------|
| completed | Completed | Panel is complete and final |
| active | Active | Panel has preliminary or pending results |
| aborted | Aborted | Panel was stopped before completion |
| cancelled | Cancelled | Panel was cancelled |

**Critical Rule:** If any Result Observation within the organizer has a statusCode of "active", the Result Organizer **must also** have a statusCode of "active". Pending results are represented with active ActStatus.

### effectiveTime

| Element | Cardinality | Description |
|---------|------------|-------------|
| effectiveTime | 0..1 | Time span of contained observations |

**Implementation Note:** Represents when the tests were performed or specimens collected. May be a single time point or a time range covering all contained observations.

```xml
<!-- Single time point -->
<effectiveTime value="20200301083000-0500"/>

<!-- Time range -->
<effectiveTime>
  <low value="20200301083000-0500"/>
  <high value="20200301100000-0500"/>
</effectiveTime>
```

### sdtc:category

| Element | Cardinality | Description |
|---------|------------|-------------|
| sdtc:category | 0..* | Diagnostic service section codes |

**USCDI Data Element:** This represents the USCDI Diagnostic Service Section concept.

**Value Set:** Diagnostic Service Section Codes (Preferred binding)

**Common Category Codes:**
| Code | System | Display |
|------|--------|---------|
| HM | 2.16.840.1.113883.12.74 (HL7 v2-0074) | Hematology |
| CH | 2.16.840.1.113883.12.74 | Chemistry |
| MB | 2.16.840.1.113883.12.74 | Microbiology |
| LAB | 2.16.840.1.113883.12.74 | Laboratory |
| RAD | 2.16.840.1.113883.12.74 | Radiology |

```xml
<sdtc:category xmlns:sdtc="urn:hl7-org:sdtc">
  <sdtc:code code="HM"
             codeSystem="2.16.840.1.113883.12.74"
             displayName="Hematology"/>
</sdtc:category>
```

### sdtc:text

| Element | Cardinality | Description |
|---------|------------|-------------|
| sdtc:text | 0..1 | Reference to narrative text |

**SHOULD** reference the portion of section narrative text corresponding to this organizer.

```xml
<sdtc:text xmlns:sdtc="urn:hl7-org:sdtc">
  <reference value="#panel1"/>
</sdtc:text>
```

If reference/@value is present, it **SHALL** begin with a '#' and point to narrative content.

### author

| Element | Cardinality | Description |
|---------|------------|-------------|
| author | 0..* | Author of the result organizer |

**SHOULD** contain author information identifying the responsible party for the results.

**Author Template ID:** `2.16.840.1.113883.10.20.22.4.119`

**USCDI Data Elements:**
- Author information represents result provider data

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301153000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>Sarah</given>
        <family>Pathologist</family>
      </name>
    </assignedPerson>
    <representedOrganization>
      <name>Community Hospital Laboratory</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### specimen

| Element | Cardinality | Description |
|---------|------------|-------------|
| specimen | 0..* | Specimen information |

A specimen linked to a Result Organizer applies to all Result Observations. Centralizing specimen details within the Organizer is advised for clarity and consistency.

**USCDI Data Elements:**
- Specimen Type: specimenPlayingEntity.code
- Specimen Identifier: specimenRole.id

```xml
<specimen typeCode="SPC">
  <specimenRole classCode="SPEC">
    <!-- Specimen Identifier -->
    <id root="c2ee9ee9-ae31-4628-a919-fec1cbb58683"/>

    <!-- Specimen Type -->
    <specimenPlayingEntity>
      <code code="122555007"
            codeSystem="2.16.840.1.113883.6.96"
            displayName="Venous blood specimen"/>
    </specimenPlayingEntity>
  </specimenRole>
</specimen>
```

**Common Specimen Types (SNOMED CT):**
| Code | Display |
|------|---------|
| 122555007 | Venous blood specimen |
| 119364003 | Serum specimen |
| 119361006 | Plasma specimen |
| 122575003 | Urine specimen |
| 258580003 | Whole blood specimen |
| 119297000 | Blood specimen |
| 258607008 | Bronchoalveolar lavage fluid sample |
| 258503004 | Sputum specimen |

### component (Result Observations)

| Element | Cardinality | Description |
|---------|------------|-------------|
| component | 1..* | Contains Result Observations. At least one required. |
| contextConductionInd | 1..1 | Fixed: true |

Each component **SHALL** contain a Result Observation (template ID: 2.16.840.1.113883.10.20.22.4.2).

### component (Specimen Collection Procedure)

| Element | Cardinality | Description |
|---------|------------|-------------|
| component | 0..1 | Optional Specimen Collection Procedure |

May contain a Specimen Collection Procedure to represent USCDI "Specimen Condition Acceptability".

## Conformance Requirements

### Mandatory Elements (SHALL)

1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.1`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` from LOINC or SNOMED CT
4. **SHALL** contain exactly one `statusCode` with required binding to Result Status
5. **SHALL** contain `classCode` = "CLUSTER"
6. **SHALL** contain `moodCode` = "EVN"
7. **SHALL** contain at least one `component` containing a Result Observation

### Recommended Elements (SHOULD)

1. **SHOULD** contain `sdtc:category` with diagnostic service section code
2. **SHOULD** contain `author` with result provider information
3. **SHOULD** contain `sdtc:text` reference to narrative
4. **SHOULD** select code from LOINC or SNOMED CT

### Optional Elements (MAY)

1. **MAY** contain `effectiveTime`
2. **MAY** contain `specimen`
3. **MAY** contain `component` with Specimen Collection Procedure

## Terminology Bindings

| Element | Value Set | Binding Strength | OID |
|---------|-----------|------------------|-----|
| code | Common LOINC Lab Codes | Preferred | - |
| code | Radiology Procedures (LOINC) | Preferred | - |
| code | Clinical Tests | Preferred | - |
| statusCode.code | Result Status | Required | 2.16.840.1.113883.11.20.9.39 |
| sdtc:category | Diagnostic Service Section Codes | Preferred | - |
| specimen.code | Specimen Type | Preferred | 2.16.840.1.113762.1.4.1099.54 |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| shall-code-or-nullflavor | Error | Code must contain either @code or @nullFlavor (exclusive) |
| 4537-19212 | Warning | Code preferably from LOINC; local codes required if no LOINC available |
| value-starts-octothorpe | Error | Text references must begin with '#' |
| should-author | Warning | Author information recommended |

## Status Rule

**Critical Rule:** If any Result Observation within the organizer has a statusCode of "active", the Result Organizer **must also** have a statusCode of "active". Pending results are represented with active ActStatus.

This ensures that the overall panel status accurately reflects the status of contained results.

## Specimen Centralization

A specimen linked at the organizer level applies to all contained Result Observations. This centralizes specimen details for clarity and avoids redundancy. When all observations in a panel use the same specimen, attach it once at the organizer level rather than repeating it for each observation.

## Usage Context

The Result Organizer is used within:
- Results Section (2.16.840.1.113883.10.20.22.2.3.1)
- Health Concern Act
- Risk Concern Act

## Implementation Notes

### Panel vs. Individual Test
- Use Result Organizer for panels and batteries (e.g., CBC, metabolic panel)
- Individual tests that are not part of a panel may still be wrapped in an organizer for consistency
- Organizer code represents the panel; observation codes represent individual tests

### Effective Time
- Represents when tests were performed or specimens collected
- May be a single time point or time range
- If omitted at organizer level, effective times must be present on individual observations

### Author Information
- Represents the laboratory or provider responsible for the results
- Should include identification, contact information, and organization
- Use NPI (National Provider Identifier) for practitioner identification when available

### Specimen Details
- Include specimen type and identifier when available
- Centralizing at organizer level reduces redundancy
- Specimen type should use SNOMED CT codes

### Component Organization
- Components must include at least one Result Observation
- May include optional Specimen Collection Procedure component
- Context conduction (contextConductionInd="true") propagates organizer context to observations

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultOrganizer.html
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- LOINC: https://loinc.org/
- SNOMED CT: https://www.snomed.org/
- USCDI v4: https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi
