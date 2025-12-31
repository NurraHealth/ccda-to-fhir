# C-CDA: Result Observation (Laboratory)

## Overview

The Result Observation in C-CDA documents laboratory test results and other diagnostic findings. Result observations are typically grouped within a Result Organizer which represents a panel or battery of related tests.

## Template Information

| Attribute | Value |
|-----------|-------|
| Result Observation Template ID | `2.16.840.1.113883.10.20.22.4.2` |
| Result Observation Version | 2023-05-01 |
| Result Observation URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ResultObservation` |
| Result Organizer Template ID | `2.16.840.1.113883.10.20.22.4.1` |
| Result Organizer Version | 2023-05-01 |
| Result Organizer URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ResultOrganizer` |

## Section Information

| Attribute | Value |
|-----------|-------|
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.3.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.3` |
| LOINC Code | 30954-2 |
| LOINC Display | Relevant diagnostic tests/laboratory data Narrative |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Results Section]
                └── entry
                    └── organizer [Result Organizer]
                        └── component
                            └── observation [Result Observation]
                                ├── templateId [@root='2.16.840.1.113883.10.20.22.4.2']
                                ├── code (test type)
                                ├── value (result)
                                └── referenceRange (normal range)
```

## XML Structure

### Results Section

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.3.1" extension="2015-08-01"/>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Relevant diagnostic tests/laboratory data Narrative"/>
  <title>RESULTS</title>
  <text>
    <table>
      <thead>
        <tr><th>Test</th><th>Result</th><th>Units</th><th>Reference Range</th><th>Date</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="result1">Hemoglobin A1c</td>
          <td>7.0</td>
          <td>%</td>
          <td>4.0-6.0</td>
          <td>March 1, 2020</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <!-- Result Organizer -->
    <organizer classCode="BATTERY" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.1" extension="2015-08-01"/>
      <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
      <code code="4548-4" codeSystem="2.16.840.1.113883.6.1"
            displayName="Hemoglobin A1c/Hemoglobin.total in Blood"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200301"/>

      <!-- Author -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20200301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <component>
        <!-- Result Observation -->
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
          <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
          <code code="4548-4" codeSystem="2.16.840.1.113883.6.1"
                displayName="Hemoglobin A1c/Hemoglobin.total in Blood"/>
          <text>
            <reference value="#result1"/>
          </text>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="PQ" value="7.0" unit="%"/>
          <interpretationCode code="H" codeSystem="2.16.840.1.113883.5.83"
                              displayName="High"/>
          <referenceRange>
            <observationRange>
              <value xsi:type="IVL_PQ">
                <low value="4.0" unit="%"/>
                <high value="6.0" unit="%"/>
              </value>
              <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
            </observationRange>
          </referenceRange>
        </observation>
      </component>
    </organizer>
  </entry>
</section>
```

## Element Details

### Result Organizer

The container for grouping related laboratory test results (e.g., a panel).

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.1` | Yes |
| id | Unique identifier for the organizer | Yes |
| code | Panel/battery code (LOINC) | Yes |
| statusCode | completed \| active \| cancelled | Yes |
| effectiveTime | When tests were performed | No |
| author | Who ordered/reported the results | No |

### Result Observation

The individual laboratory test result.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.2` | Yes |
| id | Unique identifier for the observation | Yes |
| code | Test code (LOINC) | Yes |
| statusCode | completed | Yes |
| effectiveTime | When measurement was taken | Yes |
| value | Result value (various types) | Yes |
| interpretationCode | Clinical interpretation | No |
| referenceRange | Normal/reference range | No |

### observation/code

The type of laboratory test. **SHALL** be from LOINC.

**Common Laboratory Test Codes (LOINC):**
| Code | Display |
|------|---------|
| 4548-4 | Hemoglobin A1c/Hemoglobin.total in Blood |
| 2345-7 | Glucose [Mass/volume] in Serum or Plasma |
| 2160-0 | Creatinine [Mass/volume] in Serum or Plasma |
| 718-7 | Hemoglobin [Mass/volume] in Blood |
| 6690-2 | Leukocytes [#/volume] in Blood |
| 777-3 | Platelets [#/volume] in Blood |
| 2951-2 | Sodium [Moles/volume] in Serum or Plasma |
| 2823-3 | Potassium [Moles/volume] in Serum or Plasma |
| 1742-6 | Alanine aminotransferase [U/volume] in Serum or Plasma |
| 1920-8 | Aspartate aminotransferase [U/volume] in Serum or Plasma |

### observation/value

The result value. Type varies by test. This is a **USCDI requirement** (Values/Results).

**Value Type Guidance (based on LOINC Scale Part):**

| LOINC Scale | Permitted xsi:type Values |
|-------------|---------------------------|
| Quantitative (Qn) | INT, IVL_INT, MO, IVL_MO, REAL, IVL_REAL, PQ, IVL_PQ, RTO, TS, IVL_TS |
| Ordinal/Nominal | CD |
| Narrative | ED, ST |
| Quantitative or Ordinal | CD, INT, IVL_INT, MO, REAL, PQ, IVL_PQ, TS |

```xml
<!-- Physical Quantity -->
<value xsi:type="PQ" value="7.0" unit="%"/>

<!-- Coded Value -->
<value xsi:type="CD" code="260385009" codeSystem="2.16.840.1.113883.6.96"
       displayName="Negative"/>

<!-- String Value -->
<value xsi:type="ST">Positive</value>

<!-- Interval (Range) -->
<value xsi:type="IVL_PQ">
  <low value="4.0" unit="%"/>
  <high value="6.0" unit="%"/>
</value>

<!-- Ratio -->
<value xsi:type="RTO">
  <numerator xsi:type="PQ" value="1" unit="1"/>
  <denominator xsi:type="PQ" value="64" unit="1"/>
</value>
```

**Note:** Coded values SHOULD use SNOMED-CT or LOINC where appropriate.

### interpretationCode

Clinical interpretation of the result.

| Code | Display | Description |
|------|---------|-------------|
| H | High | Above normal |
| L | Low | Below normal |
| N | Normal | Within normal limits |
| A | Abnormal | Outside normal |
| HH | Critical high | Above critical level |
| LL | Critical low | Below critical level |
| POS | Positive | Detected/positive |
| NEG | Negative | Not detected/negative |
| IND | Indeterminate | Cannot be determined |

**Code System:** `2.16.840.1.113883.5.83` (ObservationInterpretation)

### referenceRange

Normal/reference range for the observation.

```xml
<referenceRange>
  <observationRange>
    <text>4.0-6.0 %</text>
    <value xsi:type="IVL_PQ">
      <low value="4.0" unit="%"/>
      <high value="6.0" unit="%"/>
    </value>
    <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
  </observationRange>
</referenceRange>
```

| Element | Description | Required |
|---------|-------------|----------|
| text | Human-readable range description | No |
| value | Structured range value | No |
| interpretationCode | What this range represents (N=Normal) | No |

### Author Participation

Identifies the clinician or organization responsible for the result.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` | Yes |
| time | Time of authorship | Yes |
| assignedAuthor/id | Author identifier | Yes |

## Conformance Requirements

### Result Organizer
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.1`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` from LOINC
4. **SHALL** contain exactly one `statusCode`
5. **MAY** contain exactly one `effectiveTime`
6. **SHALL** contain at least one `component` containing a Result Observation

### Result Observation
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.2`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` from LOINC
4. **SHALL** contain exactly one `statusCode` with code="completed"
5. **SHALL** contain exactly one `effectiveTime`
6. **SHALL** contain exactly one `value`
7. **MAY** contain `interpretationCode`
8. **MAY** contain `referenceRange`

## Terminology Bindings

### Result Observation

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| code | Common LOINC Lab Codes; Radiology Procedures (LOINC); Clinical Tests | Preferred |
| statusCode | Result Status (VSAC) | Required |
| interpretationCode | CDAObservationInterpretation | Required |
| value (PQ unit) | UnitsOfMeasureCaseSensitive | Preferred |
| sdtc:category | US Core Clinical Result Observation Category | Preferred |

### Result Organizer

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| code | Common LOINC Lab Codes; Radiology Procedures (LOINC); Clinical Tests | Preferred |
| statusCode | Result Status (VSAC `2.16.840.1.113883.11.20.9.39`) | Required |
| specimen.code | Specimen Type (VSAC `2.16.840.1.113762.1.4.1099.54`) | Preferred |
| sdtc:category | Diagnostic Service Section Codes | Preferred |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| shall-code-or-nullflavor | Error | Code must contain either @code or @nullFlavor (exclusive) |
| 4537-19212 | Warning | Code preferably from LOINC; local codes required if no LOINC available |
| 4537-32610 | Warning | Coded values should use SNOMED-CT or LOINC |
| value-starts-octothorpe | Error | Text references must begin with '#' |
| should-interpretationCode | Warning | Interpretation codes recommended |
| should-author | Warning | Author information recommended |
| should-referenceRange | Warning | Reference ranges recommended |

## Result Organizer Status Rule

**Critical Rule:** If any Result Observation within the organizer has a statusCode of "active", the Result Organizer must also have a statusCode of "active". Pending results are represented with active ActStatus.

## Specimen Support

A specimen linked at the organizer level applies to all contained Result Observations. This centralizes specimen details for clarity.

**USCDI Data Elements:**
- Specimen Type: specimenPlayingEntity.code
- Specimen Identifier: specimenRole.id
- Specimen Condition Acceptability: Represented in SpecimenCollectionProcedure component

## Usage Context

Result Observation is used within:
- Health Concern Act
- Result Organizer
- Risk Concern Act

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- LOINC: https://loinc.org/
