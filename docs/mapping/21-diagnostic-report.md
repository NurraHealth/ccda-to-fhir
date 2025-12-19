# DiagnosticReport Mapping: C-CDA Result Organizer ↔ FHIR DiagnosticReport

This document provides detailed mapping guidance for C-CDA Result Organizers to FHIR `DiagnosticReport` resources. Result Organizers group related laboratory tests, imaging studies, or other diagnostic findings into panels or batteries.

## Overview

The C-CDA Results Section uses Result Organizers to group related Result Observations. Each Result Organizer maps to a FHIR DiagnosticReport, while the contained Result Observations map to FHIR Observation resources referenced by the DiagnosticReport.

| C-CDA Template | FHIR Resource | Notes |
|----------------|---------------|-------|
| Results Section (2.16.840.1.113883.10.20.22.2.3.1) | Section context | Contains Result Organizers |
| Result Organizer (2.16.840.1.113883.10.20.22.4.1) | DiagnosticReport | Panel/battery grouping |
| Result Observation (2.16.840.1.113883.10.20.22.4.2) | Observation | Individual test results (see `04-observation.md`) |

## Structural Mapping

```
Results Section
└── Result Organizer
    ├── id → DiagnosticReport.identifier
    ├── code → DiagnosticReport.code & .category
    ├── statusCode → DiagnosticReport.status
    ├── effectiveTime → DiagnosticReport.effective[x]
    ├── author → Provenance resource
    ├── specimen → DiagnosticReport.specimen & Observation.specimen
    └── component/observation (Result Observation)
        ├── → DiagnosticReport.result[Reference(Observation)]
        └── → Observation resource (see observation mapping)
```

## Core Element Mappings

### C-CDA to FHIR

| C-CDA Path | FHIR Path | Transform | Notes |
|------------|-----------|-----------|-------|
| `organizer/id` | `DiagnosticReport.identifier` | ID → Identifier | Business identifier |
| `organizer/code` | `DiagnosticReport.code` | CD → CodeableConcept | Panel/battery code |
| `organizer/code` | `DiagnosticReport.category` | Derive from LOINC CLASSTYPE | Use $lookup operation |
| `organizer/statusCode` | `DiagnosticReport.status` | [Status ConceptMap](#status-mapping) | See mapping table |
| `organizer/effectiveTime` | `DiagnosticReport.effectiveDateTime` or `.effectivePeriod` | TS → dateTime or Period | Clinically relevant time |
| `organizer/effectiveTime` (absent) | `DiagnosticReport.effectiveDateTime` | Use earliest observation time | Fallback strategy |
| `organizer/author` | Provenance resource | Create separate resource | Not direct DiagnosticReport element |
| `organizer/specimen` | `DiagnosticReport.specimen` | Reference(Specimen) | Also add to child Observations |
| `organizer/sdtc:category` | `DiagnosticReport.category` | CE → CodeableConcept | Diagnostic service section |
| `component/observation` | `DiagnosticReport.result` | Reference(Observation) | Link to Observation resources |
| `component/observation` | Observation resource | See observation mapping | Individual results |

### FHIR to C-CDA

| FHIR Path | C-CDA Path | Transform | Notes |
|-----------|------------|-----------|-------|
| `DiagnosticReport.identifier` | `organizer/id` | Identifier → ID | Business identifier |
| `DiagnosticReport.code` | `organizer/code` | CodeableConcept → CD | Panel/battery code |
| `DiagnosticReport.category` | `organizer/sdtc:category` | CodeableConcept → CE | Diagnostic service section |
| `DiagnosticReport.status` | `organizer/statusCode` | [Status ConceptMap](#status-mapping) | Reverse mapping |
| `DiagnosticReport.effectiveDateTime` | `organizer/effectiveTime` | dateTime → TS | Single time point |
| `DiagnosticReport.effectivePeriod` | `organizer/effectiveTime` | Period → IVL_TS | Time range with low/high |
| `DiagnosticReport.issued` | Not directly mapped | - | No equivalent in organizer |
| `DiagnosticReport.performer` | `organizer/author` | Create author participation | Lab/provider info |
| `DiagnosticReport.resultsInterpreter` | `organizer/author` | Create author participation | May be same as performer |
| `DiagnosticReport.specimen` | `organizer/specimen` | Create specimen participation | Include type and ID |
| `DiagnosticReport.result` | `component/observation` | Create Result Observations | One per result |

## Status Mapping

### C-CDA to FHIR

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| `completed` | `final` | Complete and verified results |
| `active` | `preliminary` | Preliminary or pending results |
| `cancelled` | `cancelled` | Test cancelled |
| `aborted` | `cancelled` | Test stopped before completion |
| `new` | `registered` | Order placed but not yet processed |
| `held` | `registered` | On hold |

### FHIR to C-CDA

| FHIR status | C-CDA statusCode | Notes |
|-------------|------------------|-------|
| `final` | `completed` | Final results |
| `preliminary` | `active` | Preliminary results |
| `registered` | `new` | Registered but not yet available |
| `partial` | `active` | Partial results available |
| `amended` | `completed` | Final with amendments (use replacement relationship) |
| `corrected` | `completed` | Final with corrections (use replacement relationship) |
| `appended` | `completed` | Final with additions (use appends relationship) |
| `cancelled` | `cancelled` | Cancelled |
| `entered-in-error` | `nullFlavor="NI"` | Entered in error |

**Important:** If any Result Observation has `statusCode="active"`, the Result Organizer MUST also have `statusCode="active"`.

**Standards Reference:** This mapping aligns with ConceptMap-CF-ResultReportStatus from the C-CDA on FHIR Implementation Guide, which provides the official status code mappings between C-CDA Result Organizer and FHIR DiagnosticReport.

## Category Derivation

The FHIR DiagnosticReport.category can be derived from multiple sources:

### Method 1: From C-CDA sdtc:category

```xml
<!-- C-CDA -->
<sdtc:category xmlns:sdtc="urn:hl7-org:sdtc">
  <sdtc:code code="HM"
             codeSystem="2.16.840.1.113883.12.74"
             displayName="Hematology"/>
</sdtc:category>
```

```json
// FHIR
{
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
      "code": "HM",
      "display": "Hematology"
    }]
  }]
}
```

### Method 2: From LOINC Code CLASSTYPE

Query LOINC using the `$lookup` operation to get CLASSTYPE property:

| LOINC CLASSTYPE | FHIR category.code | FHIR category.system |
|-----------------|-------------------|---------------------|
| 1 | `laboratory` | http://terminology.hl7.org/CodeSystem/v2-0074 → LAB |
| 2 | `procedure` | http://terminology.hl7.org/CodeSystem/observation-category |
| 3 | `survey` | http://terminology.hl7.org/CodeSystem/observation-category |
| 4 | `exam` | http://terminology.hl7.org/CodeSystem/observation-category |

**Recommended Approach:** Use sdtc:category if present; otherwise query LOINC for CLASSTYPE.

## Identifier Mapping

### C-CDA to FHIR

```xml
<!-- C-CDA -->
<organizer>
  <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
  <id root="2.16.840.1.113883.19.5.99999" extension="LAB-2020-001"/>
</organizer>
```

```json
// FHIR
{
  "identifier": [
    {
      "system": "urn:ietf:rfc:3986",
      "value": "urn:uuid:7d5a02b0-67a4-11db-bd13-0800200c9a66"
    },
    {
      "system": "urn:oid:2.16.840.1.113883.19.5.99999",
      "value": "LAB-2020-001"
    }
  ]
}
```

**Transform Rules:**
- If C-CDA id has only root (UUID): Create identifier with system=`urn:ietf:rfc:3986` and value=`urn:uuid:{root}`
- If C-CDA id has root (OID) and extension: Create identifier with system=`urn:oid:{root}` and value=`{extension}`

## Effective Time Mapping

### Single Time Point

```xml
<!-- C-CDA -->
<effectiveTime value="20200301083000-0500"/>
```

```json
// FHIR
{
  "effectiveDateTime": "2020-03-01T08:30:00-05:00"
}
```

### Time Range

```xml
<!-- C-CDA -->
<effectiveTime>
  <low value="20200301083000-0500"/>
  <high value="20200301100000-0500"/>
</effectiveTime>
```

```json
// FHIR
{
  "effectivePeriod": {
    "start": "2020-03-01T08:30:00-05:00",
    "end": "2020-03-01T10:00:00-05:00"
  }
}
```

### Missing Effective Time (C-CDA → FHIR)

If the Result Organizer lacks effectiveTime:
1. Find the earliest effectiveTime among all contained Result Observations
2. Use that as DiagnosticReport.effectiveDateTime
3. If observations also lack effective time, use document effectiveTime as fallback

```javascript
// Pseudocode
if (organizer.effectiveTime exists) {
  diagnosticReport.effectiveDateTime = organizer.effectiveTime
} else {
  let earliestTime = min(observation.effectiveTime for all observations)
  diagnosticReport.effectiveDateTime = earliestTime || document.effectiveTime
}
```

## Code Mapping

### C-CDA to FHIR

```xml
<!-- C-CDA -->
<code code="58410-2"
      codeSystem="2.16.840.1.113883.6.1"
      displayName="CBC panel - Blood by Automated count">
  <originalText>
    <reference value="#panel1"/>
  </originalText>
  <translation code="CBC"
               codeSystem="2.16.840.1.113883.19.5.99999"
               displayName="CBC"/>
</code>
```

```json
// FHIR
{
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "58410-2",
        "display": "CBC panel - Blood by Automated count"
      },
      {
        "system": "urn:oid:2.16.840.1.113883.19.5.99999",
        "code": "CBC",
        "display": "CBC"
      }
    ],
    "text": "CBC panel - Blood by Automated count"
  }
}
```

**Transform Rules:**
- Primary code → first coding element
- Translation codes → additional coding elements
- originalText or displayName → text element
- Map code system OIDs to FHIR URIs (see [Code System Mapping](#code-system-mapping))

## Specimen Mapping

Specimen information can be attached at the Result Organizer level, applying to all contained observations.

### C-CDA to FHIR

```xml
<!-- C-CDA -->
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
```

First, create a FHIR Specimen resource:

```json
{
  "resourceType": "Specimen",
  "id": "specimen-blood",
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:c2ee9ee9-ae31-4628-a919-fec1cbb58683"
  }],
  "type": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "122555007",
      "display": "Venous blood specimen"
    }]
  }
}
```

Then reference in DiagnosticReport and Observations:

```json
{
  "resourceType": "DiagnosticReport",
  "specimen": [{
    "reference": "Specimen/specimen-blood"
  }],
  "result": [
    {"reference": "Observation/obs1"},
    {"reference": "Observation/obs2"}
  ]
}
```

```json
{
  "resourceType": "Observation",
  "id": "obs1",
  "specimen": {
    "reference": "Specimen/specimen-blood"
  }
}
```

**Important:** When a specimen is attached at the organizer level, add the specimen reference to:
1. The DiagnosticReport.specimen
2. Each child Observation.specimen

## Author Mapping

C-CDA author information should be converted to a FHIR Provenance resource rather than being directly mapped to DiagnosticReport elements.

### C-CDA to FHIR

```xml
<!-- C-CDA -->
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

Create Practitioner and Organization resources:

```json
{
  "resourceType": "Practitioner",
  "id": "practitioner-pathologist",
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "1234567890"
  }],
  "name": [{
    "family": "Pathologist",
    "given": ["Sarah"]
  }]
}
```

```json
{
  "resourceType": "Organization",
  "id": "org-lab",
  "name": "Community Hospital Laboratory"
}
```

Create Provenance resource:

```json
{
  "resourceType": "Provenance",
  "target": [{
    "reference": "DiagnosticReport/cbc"
  }],
  "recorded": "2020-03-01T15:30:00-05:00",
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "author",
        "display": "Author"
      }]
    },
    "who": {
      "reference": "Practitioner/practitioner-pathologist"
    },
    "onBehalfOf": {
      "reference": "Organization/org-lab"
    }
  }]
}
```

**Alternative (US Core):** Use DiagnosticReport.performer and resultsInterpreter:

```json
{
  "resourceType": "DiagnosticReport",
  "performer": [{
    "reference": "Organization/org-lab",
    "display": "Community Hospital Laboratory"
  }],
  "resultsInterpreter": [{
    "reference": "Practitioner/practitioner-pathologist",
    "display": "Dr. Sarah Pathologist"
  }]
}
```

**Recommended Approach:** Use both performer/resultsInterpreter AND Provenance for complete representation.

## Result References

Each Result Observation in the organizer becomes a referenced Observation resource.

### C-CDA to FHIR

```xml
<!-- C-CDA -->
<organizer>
  <component>
    <observation>
      <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
      <code code="718-7" codeSystem="2.16.840.1.113883.6.1"/>
      <value xsi:type="PQ" value="13.2" unit="g/dL"/>
    </observation>
  </component>
  <component>
    <observation>
      <id root="8b3fa370-67a5-11db-bd13-0800200c9a66"/>
      <code code="26464-8" codeSystem="2.16.840.1.113883.6.1"/>
      <value xsi:type="PQ" value="6.7" unit="10*9/L"/>
    </observation>
  </component>
</organizer>
```

```json
// FHIR DiagnosticReport
{
  "result": [
    {"reference": "Observation/hemoglobin"},
    {"reference": "Observation/wbc"}
  ]
}

// FHIR Observations
{
  "resourceType": "Observation",
  "id": "hemoglobin",
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:107c2dc0-67a5-11db-bd13-0800200c9a66"
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "718-7"
    }]
  },
  "valueQuantity": {
    "value": 13.2,
    "unit": "g/dL",
    "system": "http://unitsofmeasure.org",
    "code": "g/dL"
  }
}
```

**Processing Steps:**
1. Convert each component/observation to a FHIR Observation (see `04-observation.md`)
2. Add category="laboratory" to each Observation based on DiagnosticReport.category
3. Add specimen reference if organizer has specimen
4. Reference each Observation in DiagnosticReport.result

## Subject and Encounter References

### C-CDA Context to FHIR

The Result Organizer inherits context from the document:

```xml
<!-- C-CDA Document Level -->
<recordTarget>
  <patientRole>
    <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
  </patientRole>
</recordTarget>

<componentOf>
  <encompassingEncounter>
    <id root="2.16.840.1.113883.19.5.99999.20" extension="ENC-2020-001"/>
  </encompassingEncounter>
</componentOf>
```

```json
// FHIR
{
  "resourceType": "DiagnosticReport",
  "subject": {
    "reference": "Patient/patient-example"
  },
  "encounter": {
    "reference": "Encounter/enc-2020-001"
  }
}
```

**Transform Rules:**
- Extract patient reference from recordTarget/patientRole/id
- Extract encounter reference from componentOf/encompassingEncounter/id
- Add same references to all child Observation resources

## Complete Example

### C-CDA Result Organizer

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.3.1" extension="2015-08-01"/>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>RESULTS</title>
  <text>
    <table>
      <thead>
        <tr><th>Test</th><th>Result</th><th>Units</th><th>Date</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="result1">Hemoglobin</td>
          <td>13.2</td>
          <td>g/dL</td>
          <td>March 1, 2020</td>
        </tr>
        <tr>
          <td ID="result2">WBC</td>
          <td>6.7</td>
          <td>10*9/L</td>
          <td>March 1, 2020</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.1" extension="2023-05-01"/>
      <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>

      <code code="58410-2"
            codeSystem="2.16.840.1.113883.6.1"
            displayName="CBC panel - Blood by Automated count"/>

      <statusCode code="completed"/>
      <effectiveTime value="20200301083000-0500"/>

      <author>
        <time value="20200301153000-0500"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name><given>Sarah</given><family>Pathologist</family></name>
          </assignedPerson>
          <representedOrganization>
            <name>Community Hospital Laboratory</name>
          </representedOrganization>
        </assignedAuthor>
      </author>

      <specimen>
        <specimenRole>
          <id root="c2ee9ee9-ae31-4628-a919-fec1cbb58683"/>
          <specimenPlayingEntity>
            <code code="122555007" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Venous blood specimen"/>
          </specimenPlayingEntity>
        </specimenRole>
      </specimen>

      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
          <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
          <code code="718-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Hemoglobin [Mass/volume] in Blood"/>
          <text><reference value="#result1"/></text>
          <statusCode code="completed"/>
          <effectiveTime value="20200301083000-0500"/>
          <value xsi:type="PQ" value="13.2" unit="g/dL"/>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
          <referenceRange>
            <observationRange>
              <value xsi:type="IVL_PQ">
                <low value="12.0" unit="g/dL"/>
                <high value="16.0" unit="g/dL"/>
              </value>
            </observationRange>
          </referenceRange>
        </observation>
      </component>

      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.2" extension="2015-08-01"/>
          <id root="8b3fa370-67a5-11db-bd13-0800200c9a66"/>
          <code code="26464-8" codeSystem="2.16.840.1.113883.6.1"
                displayName="Leukocytes [#/volume] in Blood"/>
          <text><reference value="#result2"/></text>
          <statusCode code="completed"/>
          <effectiveTime value="20200301083000-0500"/>
          <value xsi:type="PQ" value="6.7" unit="10*9/L"/>
          <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
          <referenceRange>
            <observationRange>
              <value xsi:type="IVL_PQ">
                <low value="4.3" unit="10*9/L"/>
                <high value="10.8" unit="10*9/L"/>
              </value>
            </observationRange>
          </referenceRange>
        </observation>
      </component>
    </organizer>
  </entry>
</section>
```

### FHIR DiagnosticReport Output

```json
{
  "resourceType": "DiagnosticReport",
  "id": "cbc-report",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-lab"
    ]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:7d5a02b0-67a4-11db-bd13-0800200c9a66"
  }],
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
      "code": "LAB",
      "display": "Laboratory"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "58410-2",
      "display": "CBC panel - Blood by Automated count"
    }],
    "text": "CBC panel - Blood by Automated count"
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "encounter": {
    "reference": "Encounter/encounter-example"
  },
  "effectiveDateTime": "2020-03-01T08:30:00-05:00",
  "issued": "2020-03-01T15:30:00-05:00",
  "performer": [{
    "reference": "Organization/org-lab",
    "display": "Community Hospital Laboratory"
  }],
  "resultsInterpreter": [{
    "reference": "Practitioner/practitioner-pathologist",
    "display": "Dr. Sarah Pathologist"
  }],
  "specimen": [{
    "reference": "Specimen/specimen-blood"
  }],
  "result": [
    {
      "reference": "Observation/hemoglobin"
    },
    {
      "reference": "Observation/wbc"
    }
  ]
}
```

### FHIR Specimen Resource

```json
{
  "resourceType": "Specimen",
  "id": "specimen-blood",
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:c2ee9ee9-ae31-4628-a919-fec1cbb58683"
  }],
  "type": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "122555007",
      "display": "Venous blood specimen"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  }
}
```

### FHIR Observation Resources

```json
{
  "resourceType": "Observation",
  "id": "hemoglobin",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"
    ]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:107c2dc0-67a5-11db-bd13-0800200c9a66"
  }],
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "laboratory",
      "display": "Laboratory"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "718-7",
      "display": "Hemoglobin [Mass/volume] in Blood"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "encounter": {
    "reference": "Encounter/encounter-example"
  },
  "effectiveDateTime": "2020-03-01T08:30:00-05:00",
  "specimen": {
    "reference": "Specimen/specimen-blood"
  },
  "valueQuantity": {
    "value": 13.2,
    "unit": "g/dL",
    "system": "http://unitsofmeasure.org",
    "code": "g/dL"
  },
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "N",
      "display": "Normal"
    }]
  }],
  "referenceRange": [{
    "low": {
      "value": 12.0,
      "unit": "g/dL",
      "system": "http://unitsofmeasure.org",
      "code": "g/dL"
    },
    "high": {
      "value": 16.0,
      "unit": "g/dL",
      "system": "http://unitsofmeasure.org",
      "code": "g/dL"
    }
  }]
}
```

```json
{
  "resourceType": "Observation",
  "id": "wbc",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"
    ]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:8b3fa370-67a5-11db-bd13-0800200c9a66"
  }],
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "laboratory",
      "display": "Laboratory"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "26464-8",
      "display": "Leukocytes [#/volume] in Blood"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "encounter": {
    "reference": "Encounter/encounter-example"
  },
  "effectiveDateTime": "2020-03-01T08:30:00-05:00",
  "specimen": {
    "reference": "Specimen/specimen-blood"
  },
  "valueQuantity": {
    "value": 6.7,
    "unit": "10*9/L",
    "system": "http://unitsofmeasure.org",
    "code": "10*9/L"
  },
  "interpretation": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
      "code": "N",
      "display": "Normal"
    }]
  }],
  "referenceRange": [{
    "low": {
      "value": 4.3,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    },
    "high": {
      "value": 10.8,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    }
  }]
}
```

### FHIR Provenance Resource

```json
{
  "resourceType": "Provenance",
  "id": "cbc-provenance",
  "target": [{
    "reference": "DiagnosticReport/cbc-report"
  }],
  "recorded": "2020-03-01T15:30:00-05:00",
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "author",
        "display": "Author"
      }]
    },
    "who": {
      "reference": "Practitioner/practitioner-pathologist"
    },
    "onBehalfOf": {
      "reference": "Organization/org-lab"
    }
  }]
}
```

## Code System Mapping

Common C-CDA OIDs to FHIR URIs:

| C-CDA Code System | OID | FHIR URI |
|-------------------|-----|----------|
| LOINC | 2.16.840.1.113883.6.1 | http://loinc.org |
| SNOMED CT | 2.16.840.1.113883.6.96 | http://snomed.info/sct |
| RxNorm | 2.16.840.1.113883.6.88 | http://www.nlm.nih.gov/research/umls/rxnorm |
| CPT | 2.16.840.1.113883.6.12 | http://www.ama-assn.org/go/cpt |
| ICD-10-CM | 2.16.840.1.113883.6.90 | http://hl7.org/fhir/sid/icd-10-cm |
| HL7 v2-0074 | 2.16.840.1.113883.12.74 | http://terminology.hl7.org/CodeSystem/v2-0074 |
| ObservationInterpretation | 2.16.840.1.113883.5.83 | http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation |
| NPI | 2.16.840.1.113883.4.6 | http://hl7.org/fhir/sid/us-npi |

## Implementation Notes

### Resource Creation Order

When converting C-CDA to FHIR:
1. Create Patient resource (from recordTarget)
2. Create Practitioner/Organization resources (from authors)
3. Create Specimen resource (if present)
4. Create Observation resources (from component/observation)
5. Create DiagnosticReport resource (linking to above resources)
6. Create Provenance resource (if needed)

### Bundle Creation

For document conversion, create a Bundle with type="document":

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [
    {"resource": {"resourceType": "Composition", ...}},
    {"resource": {"resourceType": "Patient", ...}},
    {"resource": {"resourceType": "DiagnosticReport", ...}},
    {"resource": {"resourceType": "Observation", ...}},
    {"resource": {"resourceType": "Specimen", ...}},
    {"resource": {"resourceType": "Practitioner", ...}},
    {"resource": {"resourceType": "Organization", ...}},
    {"resource": {"resourceType": "Provenance", ...}}
  ]
}
```

### Issued Time Derivation

DiagnosticReport.issued represents when the report was made available. If the C-CDA organizer lacks author/time, use the following fallback logic:

**Fallback Order:**
1. Use `organizer/author/time` if present (primary source)
2. Use `document/effectiveTime` (document creation time)
3. Use `DiagnosticReport.effectiveDateTime` (observation time)
4. Use current system time as last resort

**Implementation:**
```javascript
// Pseudocode
if (organizer.author.time exists) {
  diagnosticReport.issued = organizer.author.time
} else if (document.effectiveTime exists) {
  diagnosticReport.issued = document.effectiveTime
} else if (diagnosticReport.effectiveDateTime exists) {
  diagnosticReport.issued = diagnosticReport.effectiveDateTime
} else {
  diagnosticReport.issued = currentSystemTime()
}
```

**US Core Requirement:** When status is partial, preliminary, final, amended, corrected, or appended, issued is MANDATORY (us-core-9).

### Category Inference

When sdtc:category is absent:
1. Query LOINC terminology server using code.$lookup
2. Extract CLASSTYPE property
3. Map CLASSTYPE to appropriate category code
4. If LOINC lookup fails, default to "LAB" for laboratory codes

### Observation Category Propagation

Set the same category on child Observation resources as on the DiagnosticReport. This ensures consistent categorization.

### Specimen Attachment

When specimen is at organizer level:
- Create one Specimen resource
- Reference from DiagnosticReport.specimen
- Reference from each Observation.specimen

When specimen is at observation level:
- Create Specimen resource per observation
- Reference only from that specific Observation

### Status Propagation Rule

If converting to C-CDA and any Observation has status="preliminary":
- Set organizer statusCode="active"

If all Observations have status="final":
- Set organizer statusCode="completed"

### Unmapped C-CDA Elements

The following C-CDA Result Organizer elements do NOT have direct FHIR DiagnosticReport equivalents:

| C-CDA Element | FHIR Equivalent | Notes |
|---------------|----------------|-------|
| `sdtc:text` | None | Narrative reference has no direct FHIR mapping. The narrative content is preserved in the section/text element but not referenced from individual resources. |
| `organizer/code/@originalText` | Mapped to `code.text` | While the value is mapped, the reference pointer (e.g., `<reference value="#panel1"/>`) is not preserved in FHIR. |

**Implementation Note:** While these elements don't map directly to DiagnosticReport, their information may be preserved in:
- The section narrative (for sdtc:text references)
- The code.text field (for originalText content)
- Extensions (if custom extensions are needed for full fidelity)

## US Core Conformance

When creating DiagnosticReport resources, ensure US Core conformance:

### Required Elements
1. status
2. category (with LAB code)
3. code (from LOINC)
4. subject (Patient reference)
5. effectiveDateTime or effectivePeriod (**us-core-8**: SHALL be present when status is partial, preliminary, final, amended, corrected, or appended)
6. issued (**us-core-9**: SHALL be present when status is partial, preliminary, final, amended, corrected, or appended)

### Constraints
- **us-core-8**: effective[x] SHALL be present if status is partial | preliminary | final | amended | corrected | appended
- **us-core-9**: issued SHALL be present if status is partial | preliminary | final | amended | corrected | appended

### Must Support Elements
1. encounter
2. performer
3. resultsInterpreter
4. result (Observation references)

### Search Parameters Support
Implement these search parameters:
- `patient`
- `patient` + `category`
- `patient` + `code`
- `patient` + `category` + `date`
- `patient` + `status`

## References

- [C-CDA on FHIR Results Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html)
- [FHIR R4B DiagnosticReport](https://hl7.org/fhir/R4B/diagnosticreport.html)
- [US Core DiagnosticReport Lab Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-lab)
- [C-CDA Result Organizer](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultOrganizer.html)
- [C-CDA Results Section](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultsSection.html)
- [C-CDA Result Observation](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultObservation.html)
- [Observation Mapping (04-observation.md)](./04-observation.md)
