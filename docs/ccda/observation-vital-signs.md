# C-CDA: Vital Signs Observation

## Overview

The Vital Signs Observation in C-CDA documents a patient's vital sign measurements such as blood pressure, heart rate, respiratory rate, temperature, height, weight, and BMI. Vital signs are typically grouped within a Vital Signs Organizer.

## Template Information

| Attribute | Value |
|-----------|-------|
| Vital Sign Observation Template ID | `2.16.840.1.113883.10.20.22.4.27` |
| Vital Sign Observation Version | 2014-06-09 |
| Vital Sign Observation URL | `http://hl7.org/cda/us/ccda/StructureDefinition/VitalSignObservation` |
| Vital Signs Organizer Template ID | `2.16.840.1.113883.10.20.22.4.26` |
| Vital Signs Organizer Version | 2015-08-01 |
| Vital Signs Organizer URL | `http://hl7.org/cda/us/ccda/StructureDefinition/VitalSignsOrganizer` |

## Section Information

| Attribute | Value |
|-----------|-------|
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.4.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.4` |
| LOINC Code | 8716-3 |
| LOINC Display | Vital signs |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Vital Signs Section]
                └── entry
                    └── organizer [Vital Signs Organizer]
                        └── component
                            └── observation [Vital Sign Observation]
                                ├── templateId [@root='2.16.840.1.113883.10.20.22.4.27']
                                ├── code (vital sign type)
                                └── value (measurement)
```

## XML Structure

### Vital Signs Section

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.4.1" extension="2015-08-01"/>
  <code code="8716-3" codeSystem="2.16.840.1.113883.6.1"
        displayName="Vital signs"/>
  <title>VITAL SIGNS</title>
  <text>
    <table>
      <thead>
        <tr><th>Date</th><th>BP Sys</th><th>BP Dia</th><th>Pulse</th><th>Temp</th><th>Height</th><th>Weight</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>March 1, 2020</td>
          <td ID="systolic1">120 mmHg</td>
          <td ID="diastolic1">80 mmHg</td>
          <td ID="pulse1">72 /min</td>
          <td ID="temp1">98.6 [degF]</td>
          <td ID="height1">170 cm</td>
          <td ID="weight1">75 kg</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <!-- Vital Signs Organizer -->
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.26" extension="2015-08-01"/>
      <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
      <code code="46680005" codeSystem="2.16.840.1.113883.6.96"
            displayName="Vital signs">
        <translation code="74728-7" codeSystem="2.16.840.1.113883.6.1"
                     displayName="Vital signs, weight, height, head circumference, oximetry, BMI, and BSA panel"/>
      </code>
      <statusCode code="completed"/>
      <effectiveTime value="20200301"/>

      <!-- Blood Pressure (composite) -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.27" extension="2014-06-09"/>
          <id root="..."/>
          <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"
                displayName="Blood pressure panel">
            <translation code="55284-4" codeSystem="2.16.840.1.113883.6.1"
                         displayName="Blood pressure systolic and diastolic"/>
          </code>
          <text>
            <reference value="#bp1"/>
          </text>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <!-- Interpretation -->
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"
                              displayName="Normal"/>
          <!-- Systolic -->
          <entryRelationship typeCode="COMP">
            <observation classCode="OBS" moodCode="EVN">
              <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Systolic blood pressure"/>
              <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
            </observation>
          </entryRelationship>
          <!-- Diastolic -->
          <entryRelationship typeCode="COMP">
            <observation classCode="OBS" moodCode="EVN">
              <code code="8462-4" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Diastolic blood pressure"/>
              <value xsi:type="PQ" value="80" unit="mm[Hg]"/>
            </observation>
          </entryRelationship>
        </observation>
      </component>

      <!-- Heart Rate -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.27" extension="2014-06-09"/>
          <id root="..."/>
          <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"
                displayName="Heart rate"/>
          <text>
            <reference value="#pulse1"/>
          </text>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="PQ" value="72" unit="/min"/>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
        </observation>
      </component>

      <!-- Body Temperature -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.27" extension="2014-06-09"/>
          <id root="..."/>
          <code code="8310-5" codeSystem="2.16.840.1.113883.6.1"
                displayName="Body temperature"/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="PQ" value="98.6" unit="[degF]"/>
        </observation>
      </component>

      <!-- Body Height -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.27" extension="2014-06-09"/>
          <id root="..."/>
          <code code="8302-2" codeSystem="2.16.840.1.113883.6.1"
                displayName="Body height"/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="PQ" value="170" unit="cm"/>
        </observation>
      </component>

      <!-- Body Weight -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.27" extension="2014-06-09"/>
          <id root="..."/>
          <code code="29463-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Body weight"/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
          <value xsi:type="PQ" value="75" unit="kg"/>
        </observation>
      </component>

    </organizer>
  </entry>
</section>
```

## Element Details

### Vital Signs Organizer

The container for grouping related vital sign measurements taken at the same time.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.26` | Yes |
| id | Unique identifier for the organizer | Yes |
| code | Vital signs code (SNOMED: 46680005) | Yes |
| statusCode | completed | Yes |
| effectiveTime | When vital signs were measured | Yes |

### Vital Sign Observation

The individual vital sign measurement.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.27` | Yes |
| id | Unique identifier for the observation | Yes |
| code | Vital sign type code (LOINC) | Yes |
| statusCode | completed | Yes |
| effectiveTime | When measurement was taken | Yes |
| value | Physical quantity with unit | Yes |
| interpretationCode | Clinical interpretation | No |

### Vital Sign Codes (LOINC)

| Code | Display | Description |
|------|---------|-------------|
| 8480-6 | Systolic blood pressure | Systolic BP |
| 8462-4 | Diastolic blood pressure | Diastolic BP |
| 8867-4 | Heart rate | Pulse/heart rate |
| 9279-1 | Respiratory rate | Breathing rate |
| 8310-5 | Body temperature | Temperature |
| 8302-2 | Body height | Height |
| 29463-7 | Body weight | Weight |
| 39156-5 | Body mass index | BMI |
| 59408-5 | Oxygen saturation | SpO2 |
| 8287-5 | Head circumference | Head circumference |

### Panel Codes (LOINC)

| Code | Display |
|------|---------|
| 85354-9 | Blood pressure panel |
| 55284-4 | Blood pressure systolic and diastolic |
| 74728-7 | Vital signs panel |

### observation/value

The vital sign measurement value. Always uses Physical Quantity (PQ) type.

```xml
<value xsi:type="PQ" value="120" unit="mm[Hg]"/>
```

### Recommended Units by Vital Sign Type

The template enforces unit-specific requirements:

| Vital Sign | Recommended Unit | Notes |
|-----------|-----------------|-------|
| Pulse Oximetry | % | |
| Height | cm | |
| Head Circumference | cm | |
| Weight | kg | |
| Temperature | Cel | Celsius recommended |
| Blood Pressure | mm[Hg] | |
| Pulse/Heart Rate | /min | |
| Respiratory Rate | /min | |
| BMI | kg/m2 | |
| Body Surface Area | m2 | |
| Inhaled O₂ Concentration | % | |

### Common Units (UCUM)

| Unit | Description |
|------|-------------|
| mm[Hg] | Millimeters of mercury |
| /min | Per minute |
| cm | Centimeters |
| [in_i] | Inches |
| kg | Kilograms |
| [lb_av] | Pounds |
| Cel | Celsius |
| [degF] | Fahrenheit |
| % | Percent |
| kg/m2 | Kilograms per meter squared |
| m2 | Square meters |

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

**Code System:** `2.16.840.1.113883.5.83` (ObservationInterpretation)

## Conformance Requirements

### Vital Signs Organizer
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.26`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` with code from SNOMED CT
4. **SHALL** contain exactly one `statusCode` with code="completed"
5. **SHALL** contain exactly one `effectiveTime`
6. **SHALL** contain at least one `component` containing a Vital Sign Observation

### Vital Sign Observation
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.27`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` from LOINC
4. **SHALL** contain exactly one `statusCode` with code="completed"
5. **SHALL** contain exactly one `effectiveTime`
6. **SHALL** contain exactly one `value` with xsi:type="PQ"
7. **MAY** contain `interpretationCode`

## Terminology Bindings

### Vital Sign Observation

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| code.code | Vital Sign Result Type (VSAC) | Preferred |
| value.unit | UnitsOfMeasureCaseSensitive (UCUM) | Required |

### Vital Signs Organizer

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| classCode | XActClassDocumentEntryOrganizer (v3) | Required |
| moodCode | CDAActMood | Required |
| statusCode | ActStatus | Required |
| code | LOINC 74728-7 (Vital signs panel) | Fixed |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| should-author | Warning | Author information recommended |
| should-sdtctext-ref-value | Warning | sdtcText.reference.value should reference narrative |
| value-starts-octothorpe | Error | Reference values must begin with '#' |

## Usage Context

Vital Sign Observation is used within:
- Health Concern Act
- Risk Concern Act
- Vital Signs Organizer

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- LOINC: https://loinc.org/
- UCUM: https://ucum.org/
