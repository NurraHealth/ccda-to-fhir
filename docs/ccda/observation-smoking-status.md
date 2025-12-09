# C-CDA: Smoking Status Observation

## Overview

The Smoking Status Observation in C-CDA documents a patient's tobacco smoking status as part of their social history. This is a specific type of social history observation that captures whether the patient is a current smoker, former smoker, or never smoker.

## Template Information

| Attribute | Value |
|-----------|-------|
| Smoking Status Template ID | `2.16.840.1.113883.10.20.22.4.78` |
| Template Version | 2014-06-09 (R2.1), 2024-05-01 (R5.0) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/SmokingStatusMeaningfulUse` |
| Template Status | Retired as of 2025-12-04 (R5.0) |
| USCDI Designation | Smoking Status |

**Note:** This template represents "a snapshot in time observation" rather than historical smoking data or detailed habit information. It was required by Meaningful Use Stage 2 regulations.

## Section Information

| Attribute | Value |
|-----------|-------|
| Section Template ID | `2.16.840.1.113883.10.20.22.2.17` |
| Section Template Version | 2015-08-01 |
| LOINC Code | 29762-2 |
| LOINC Display | Social history Narrative |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Social History Section]
                └── entry
                    └── observation [Smoking Status Observation]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.78']
                        ├── code (smoking status type)
                        └── value (smoking status)
```

## XML Structure

### Social History Section

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.17" extension="2015-08-01"/>
  <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Social history Narrative"/>
  <title>SOCIAL HISTORY</title>
  <text>
    <table>
      <thead>
        <tr><th>Social History Element</th><th>Description</th><th>Date</th></tr>
      </thead>
      <tbody>
        <tr>
          <td>Smoking Status</td>
          <td ID="smoking1">Former smoker</td>
          <td>March 1, 2020</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <!-- Smoking Status Observation -->
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.78" extension="2014-06-09"/>
      <id root="45efb604-7049-4a36-b17f-d5a5e6af9a09"/>
      <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
            displayName="Tobacco smoking status"/>
      <text>
        <reference value="#smoking1"/>
      </text>
      <statusCode code="completed"/>
      <effectiveTime value="20200301"/>
      <value xsi:type="CD" code="8517006" codeSystem="2.16.840.1.113883.6.96"
             displayName="Former smoker"/>
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20200301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
    </observation>
  </entry>
</section>
```

## Element Details

### Smoking Status Observation

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.78` | Yes |
| id | Unique identifier for the observation | Yes |
| code | `72166-2` (Tobacco smoking status) from LOINC | Yes |
| statusCode | completed | Yes |
| effectiveTime | When status was observed/recorded | Yes |
| value | Smoking status code (SNOMED) | Yes |
| author | Who documented the status | No |

### observation/code

The code element **SHALL** be `72166-2` (Tobacco smoking status) from LOINC.

```xml
<code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
      displayName="Tobacco smoking status"/>
```

### observation/value (Smoking Status)

The patient's smoking status. **SHALL** be a coded value from SNOMED CT.

**Smoking Status Codes (SNOMED):**
| Code | Display | Description |
|------|---------|-------------|
| 449868002 | Current every day smoker | Smokes daily |
| 428041000124106 | Current some day smoker | Smokes occasionally |
| 8517006 | Former smoker | Previously smoked |
| 266919005 | Never smoker | Never smoked |
| 77176002 | Smoker, current status unknown | Smokes, status unknown |
| 266927001 | Unknown if ever smoked | Unknown smoking history |
| 428071000124103 | Current heavy tobacco smoker | Heavy smoker |
| 428061000124105 | Current light tobacco smoker | Light smoker |

```xml
<value xsi:type="CD" code="8517006" codeSystem="2.16.840.1.113883.6.96"
       displayName="Former smoker"/>
```

### effectiveTime

The date when the smoking status was observed or recorded. For current status observations, this typically represents when the observation was made.

**Critical Constraint:** The effectiveTime must be a single timestamp, NOT an interval. The specification states it "will approximately correspond with the author/time". Interval fields SHALL NOT be present.

```xml
<effectiveTime value="20200301"/>
```

### Author Participation

Identifies the clinician who documented the smoking status.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` | Yes |
| time | Time of documentation | Yes |
| assignedAuthor/id | Author identifier | Yes |

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  </assignedAuthor>
</author>
```

## Conformance Requirements

1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.78`
2. **SHALL** contain exactly one `id`
3. **SHALL** contain exactly one `code` with code="72166-2" from LOINC
4. **SHALL** contain exactly one `statusCode` - bound to "Completed or Nullified Act Status" value set (Required)
5. **SHALL** contain exactly one `effectiveTime` (single value only, no intervals)
6. **SHALL** contain exactly one `value` with xsi:type="CD" from SNOMED CT
7. **SHOULD** contain author participation
8. **SHOULD** reference corresponding section narrative text (text.reference/@value)

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| value.code | Smoking Status (`2.16.840.1.113883.11.20.9.38`) | Preferred |
| statusCode.code | Completed or Nullified Act Status | Required |

## Unknown Status Handling

If smoking status is unknown, use SNOMED CT code `266927001` ("Unknown if ever smoked").

## Related Templates

Other social history observations that may appear in the Social History Section:

| Template | Template ID | Description |
|----------|-------------|-------------|
| Tobacco Use | `2.16.840.1.113883.10.20.22.4.85` | Detailed tobacco use history |
| Social History Observation | `2.16.840.1.113883.10.20.22.4.38` | General social history observations |

## Usage Context

This template is used within the Health Concern Act profile structure for organizing clinical observations.

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- LOINC: https://loinc.org/
- SNOMED CT: http://snomed.info/sct
