# Observation Mapping: C-CDA Results/Vitals/Social History ↔ FHIR Observation

This document provides detailed mapping guidance for various C-CDA observation types to FHIR `Observation` resources.

## Overview

Multiple C-CDA observation types map to FHIR Observation:

| C-CDA Section | C-CDA Template | FHIR Category |
|---------------|----------------|---------------|
| Results (LOINC `30954-2`) | Result Observation | `laboratory` |
| Vital Signs (LOINC `8716-3`) | Vital Sign Observation | `vital-signs` |
| Social History (LOINC `29762-2`) | Smoking Status, Pregnancy | `social-history` |

## Result Observations

### Structural Mapping

```
Results Section
└── Result Organizer
    ├── id → DiagnosticReport.identifier
    ├── code → DiagnosticReport.code
    ├── statusCode → DiagnosticReport.status
    └── component/observation (Result Observation)
        ├── id → Observation.identifier
        ├── code → Observation.code
        ├── statusCode → Observation.status
        ├── effectiveTime → Observation.effective[x]
        ├── value → Observation.value[x]
        ├── interpretationCode → Observation.interpretation
        └── referenceRange → Observation.referenceRange
```

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/id` | `Observation.identifier` | ID → Identifier |
| `observation/code` | `Observation.code` | CodeableConcept |
| `observation/statusCode` | `Observation.status` | [Status ConceptMap](#result-status-mapping) |
| `observation/effectiveTime` | `Observation.effectiveDateTime` or `.effectivePeriod` | Date conversion |
| `observation/value[@xsi:type='PQ']` | `Observation.valueQuantity` | [Quantity](#value-type-mappings) |
| `observation/value[@xsi:type='CD']` | `Observation.valueCodeableConcept` | CodeableConcept |
| `observation/value[@xsi:type='ST']` | `Observation.valueString` | String |
| `observation/value[@xsi:type='INT']` | `Observation.valueInteger` | Integer |
| `observation/value[@xsi:type='REAL']` | `Observation.valueQuantity` | Empty unit |
| `observation/value[@xsi:type='IVL_PQ']` | `Observation.valueRange` | [Range](#range-values) |
| `observation/value[@xsi:type='ED']` | `Observation.extension:valueAttachment` | Attachment |
| `observation/interpretationCode` | `Observation.interpretation` | CodeableConcept |
| `observation/methodCode` | `Observation.method` | CodeableConcept |
| `observation/targetSiteCode` | `Observation.bodySite` | CodeableConcept |
| `observation/specimen` | `Observation.specimen` | Reference(Specimen) |
| `observation/author` | Provenance | Create Provenance resource |
| `observation/referenceRange` | `Observation.referenceRange` | [Reference Range](#reference-range-mapping) |

### Result Status Mapping

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `preliminary` |
| `cancelled` | `cancelled` |
| `aborted` | `cancelled` |
| `held` | `registered` |
| `new` | `registered` |

### Value Type Mappings

#### Physical Quantity (PQ)

**C-CDA:**
```xml
<value xsi:type="PQ" value="6.3" unit="10*9/L"/>
```

**FHIR:**
```json
{
  "valueQuantity": {
    "value": 6.3,
    "unit": "10*9/L",
    "system": "http://unitsofmeasure.org",
    "code": "10*9/L"
  }
}
```

#### Coded Value (CD/CE/CV)

**C-CDA:**
```xml
<value xsi:type="CD" code="260385009" codeSystem="2.16.840.1.113883.6.96"
       displayName="Negative"/>
```

**FHIR:**
```json
{
  "valueCodeableConcept": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "260385009",
      "display": "Negative"
    }]
  }
}
```

#### Range Values

**C-CDA (IVL_PQ):**
```xml
<value xsi:type="IVL_PQ">
  <low value="4.0" unit="10*9/L"/>
  <high value="11.0" unit="10*9/L"/>
</value>
```

**FHIR (Range):**
```json
{
  "valueRange": {
    "low": {
      "value": 4.0,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    },
    "high": {
      "value": 11.0,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    }
  }
}
```

**C-CDA (High-only with comparator):**
```xml
<value xsi:type="IVL_PQ">
  <high value="100" unit="mg/dL" inclusive="true"/>
</value>
```

**FHIR (Quantity with comparator):**
```json
{
  "valueQuantity": {
    "value": 100,
    "comparator": "<=",
    "unit": "mg/dL",
    "system": "http://unitsofmeasure.org",
    "code": "mg/dL"
  }
}
```

### Reference Range Mapping

**C-CDA:**
```xml
<referenceRange>
  <observationRange>
    <value xsi:type="IVL_PQ">
      <low value="4.0" unit="10*9/L"/>
      <high value="11.0" unit="10*9/L"/>
    </value>
    <interpretationCode code="N" codeSystem="2.16.840.1.113883.5.83"/>
    <text>Normal range</text>
  </observationRange>
</referenceRange>
```

**FHIR:**
```json
{
  "referenceRange": [{
    "low": {
      "value": 4.0,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    },
    "high": {
      "value": 11.0,
      "unit": "10*9/L",
      "system": "http://unitsofmeasure.org",
      "code": "10*9/L"
    },
    "text": "Normal range"
  }]
}
```

**Note:** FHIR expects reference ranges to be "normal" ranges. If C-CDA includes multiple reference ranges, only map the one with `interpretationCode = "N"`.

### Category from LOINC

For LOINC-coded observations, the category can be derived from the LOINC code's CLASSTYPE property:

| LOINC CLASSTYPE | FHIR Category |
|-----------------|---------------|
| 1 | `laboratory` |
| 2 | `clinical` |
| 3 | `claims-attachment` |
| 4 | `survey` |

## Vital Signs Observations

### Vital Signs Organizer

**C-CDA:**
```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
  <id root="..."/>
  <code code="46680005" codeSystem="2.16.840.1.113883.6.96"
        displayName="Vital signs">
    <translation code="74728-7" codeSystem="2.16.840.1.113883.6.1"/>
  </code>
  <statusCode code="completed"/>
  <effectiveTime value="20200301"/>
  <component>
    <!-- Individual vital sign observations -->
  </component>
</organizer>
```

**FHIR Panel Observation:**
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "85353-1",
      "display": "Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"
    }]
  },
  "effectiveDateTime": "2020-03-01",
  "hasMember": [
    {"reference": "Observation/bp-observation"},
    {"reference": "Observation/hr-observation"},
    {"reference": "Observation/temp-observation"}
  ]
}
```

### Individual Vital Sign Mappings

| C-CDA LOINC | Vital Sign | FHIR LOINC |
|-------------|------------|------------|
| `8310-5` | Body Temperature | `8310-5` |
| `8867-4` | Heart Rate | `8867-4` |
| `9279-1` | Respiratory Rate | `9279-1` |
| `85354-9` | Blood Pressure Panel | `85354-9` |
| `8480-6` | Systolic Blood Pressure | `8480-6` |
| `8462-4` | Diastolic Blood Pressure | `8462-4` |
| `8302-2` | Body Height | `8302-2` |
| `29463-7` | Body Weight | `29463-7` |
| `39156-5` | BMI | `39156-5` |
| `59408-5` | Pulse Oximetry | `59408-5` |
| `8287-5` | Head Circumference | `8287-5` |

### Blood Pressure Special Handling

Blood pressure requires a panel structure:

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200301"/>
  <!-- Systolic -->
  <entryRelationship typeCode="COMP">
    <observation classCode="OBS" moodCode="EVN">
      <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
      <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
    </observation>
  </entryRelationship>
  <!-- Diastolic -->
  <entryRelationship typeCode="COMP">
    <observation classCode="OBS" moodCode="EVN">
      <code code="8462-4" codeSystem="2.16.840.1.113883.6.1"/>
      <value xsi:type="PQ" value="80" unit="mm[Hg]"/>
    </observation>
  </entryRelationship>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "vital-signs"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "85354-9",
      "display": "Blood pressure panel"
    }]
  },
  "effectiveDateTime": "2020-03-01",
  "component": [
    {
      "code": {
        "coding": [{
          "system": "http://loinc.org",
          "code": "8480-6",
          "display": "Systolic blood pressure"
        }]
      },
      "valueQuantity": {
        "value": 120,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    },
    {
      "code": {
        "coding": [{
          "system": "http://loinc.org",
          "code": "8462-4",
          "display": "Diastolic blood pressure"
        }]
      },
      "valueQuantity": {
        "value": 80,
        "unit": "mmHg",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}
```

**Note:** Blood pressure panel should NOT have `Observation.valueQuantity` at the root level; values go in components.

### Pulse Oximetry Special Handling

**FHIR:**
```json
{
  "resourceType": "Observation",
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "59408-5",
        "display": "Oxygen saturation in Arterial blood by Pulse oximetry"
      },
      {
        "system": "http://loinc.org",
        "code": "2708-6",
        "display": "Oxygen saturation in Arterial blood"
      }
    ]
  },
  "valueQuantity": {
    "value": 98,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  },
  "component": [
    {
      "code": {
        "coding": [{
          "system": "http://loinc.org",
          "code": "3150-0",
          "display": "Inhaled oxygen concentration"
        }]
      },
      "valueQuantity": {
        "value": 21,
        "unit": "%",
        "system": "http://unitsofmeasure.org",
        "code": "%"
      }
    }
  ]
}
```

## Smoking Status

### Mapping

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
  <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Tobacco smoking status"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200301"/>
  <value xsi:type="CD" code="428041000124106" codeSystem="2.16.840.1.113883.6.96"
         displayName="Current some day smoker"/>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "status": "final",
  "category": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/observation-category",
      "code": "social-history"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "72166-2",
      "display": "Tobacco smoking status"
    }]
  },
  "effectiveDateTime": "2020-03-01",
  "valueCodeableConcept": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "428041000124106",
      "display": "Current some day smoker"
    }]
  }
}
```

### Smoking Status Codes (SNOMED)

| Code | Display |
|------|---------|
| `266919005` | Never smoked tobacco |
| `8517006` | Ex-smoker |
| `428041000124106` | Current some day smoker |
| `449868002` | Current every day smoker |
| `77176002` | Smoker |
| `266927001` | Tobacco smoking consumption unknown |

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Observation.identifier` | `observation/id` | Identifier → ID |
| `Observation.status` | `observation/statusCode` | Reverse status map |
| `Observation.category` | Section placement | Determines section |
| `Observation.code` | `observation/code` | CodeableConcept → CD |
| `Observation.effectiveDateTime` | `observation/effectiveTime/@value` | Date format |
| `Observation.effectivePeriod` | `observation/effectiveTime/low,high` | Period format |
| `Observation.valueQuantity` | `observation/value[@xsi:type='PQ']` | Quantity → PQ |
| `Observation.valueCodeableConcept` | `observation/value[@xsi:type='CD']` | CodeableConcept → CD |
| `Observation.valueString` | `observation/value[@xsi:type='ST']` | Direct mapping |
| `Observation.valueInteger` | `observation/value[@xsi:type='INT']` | Direct mapping |
| `Observation.interpretation` | `observation/interpretationCode` | CodeableConcept → CE |
| `Observation.method` | `observation/methodCode` | CodeableConcept → CE |
| `Observation.bodySite` | `observation/targetSiteCode` | CodeableConcept → CD |
| `Observation.referenceRange` | `observation/referenceRange` | See mapping above |
| `Observation.component` | Component observations | Nested or entryRelationship |

### FHIR Status to CDA

| FHIR status | CDA statusCode |
|-------------|----------------|
| `final` | `completed` |
| `preliminary` | `active` |
| `cancelled` | `cancelled` |
| `registered` | `new` |
| `amended` | `completed` |
| `corrected` | `completed` |

## Complete Example: Lab Result

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
  <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>RESULTS</title>
  <entry>
    <organizer classCode="BATTERY" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
      <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
      <code code="26464-8" codeSystem="2.16.840.1.113883.6.1"
            displayName="Leukocytes [#/volume] in Blood"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200301"/>
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
          <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
          <code code="26464-8" codeSystem="2.16.840.1.113883.6.1"
                displayName="Leukocytes [#/volume] in Blood"/>
          <statusCode code="completed"/>
          <effectiveTime value="20200301"/>
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

### FHIR Output

```json
{
  "resourceType": "Observation",
  "id": "lab-wbc",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"]
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
      "code": "26464-8",
      "display": "Leukocytes [#/volume] in Blood"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "effectiveDateTime": "2020-03-01",
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

## References

- [C-CDA on FHIR Results Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html)
- [C-CDA on FHIR Vital Signs Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-vitals.html)
- [US Core Observation Lab Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab)
- [US Core Vital Signs Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs)
- [C-CDA Result Observation](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.2.html)
- [C-CDA Vital Sign Observation](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.27.html)
