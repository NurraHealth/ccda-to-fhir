# Vital Signs Mapping: C-CDA Vital Signs ↔ FHIR Observation

This document provides detailed mapping guidance between C-CDA Vital Signs observations and FHIR `Observation` resources using Vital Signs profiles.

## Overview

| C-CDA | FHIR |
|-------|------|
| Vital Signs Organizer (`2.16.840.1.113883.10.20.22.4.26`) | `Observation` (Vital Signs Panel) |
| Vital Sign Observation (`2.16.840.1.113883.10.20.22.4.27`) | `Observation` (individual vital sign) |
| Section: Vital Signs (LOINC `8716-3`) | Category: `vital-signs` |

**Reference:** [C-CDA on FHIR Vital Signs Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-vitals.html)

**Key Principle:** Vital Signs Organizer becomes a panel Observation with individual vital signs as `hasMember` references. Blood pressure and pulse oximetry use component structure for multi-part measurements.

---

## 1. Vital Signs Organizer (Panel)

### Template

- Vital Signs Organizer (`2.16.840.1.113883.10.20.22.4.26`)

### Mapping to FHIR

**Target:** `Observation` resource (Vital Signs Panel)

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `organizer/id` | `Observation.identifier` | ID → Identifier |
| `organizer/code` | `Observation.code` | Fixed: LOINC `85353-1` (Vital signs panel) |
| `organizer/statusCode` | `Observation.status` | [Status ConceptMap](#status-mapping) |
| `organizer/effectiveTime` | `Observation.effectiveDateTime` | Date conversion |
| `organizer/component/observation` | `Observation.hasMember` | Reference to each vital sign Observation |

### Example

**C-CDA:**
```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
  <id root="1.2.3.4" extension="vs-panel-123"/>
  <code code="46680005" displayName="Vital signs"
        codeSystem="2.16.840.1.113883.6.96">
    <translation code="74728-7" displayName="Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"
                 codeSystem="2.16.840.1.113883.6.1"/>
  </code>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>
  <component>
    <!-- Individual vital sign observations -->
  </component>
</organizer>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "vs-panel-123",
  "identifier": [
    {
      "system": "urn:oid:1.2.3.4",
      "value": "vs-panel-123"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs",
          "display": "Vital Signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85353-1",
        "display": "Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "hasMember": [
    {"reference": "Observation/bp-123"},
    {"reference": "Observation/hr-123"},
    {"reference": "Observation/temp-123"},
    {"reference": "Observation/resp-123"},
    {"reference": "Observation/spo2-123"}
  ]
}
```

---

## 2. Individual Vital Sign Observations

### Template

- Vital Sign Observation (`2.16.840.1.113883.10.20.22.4.27`)

### Core Mapping

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `observation/id` | `Observation.identifier` | ID → Identifier |
| `observation/code` | `Observation.code` | LOINC code for specific vital sign |
| `observation/statusCode` | `Observation.status` | Status mapping |
| `observation/effectiveTime` | `Observation.effectiveDateTime` | Date conversion |
| `observation/value[@xsi:type="PQ"]` | `Observation.valueQuantity` | Quantity with unit |
| `observation/interpretationCode` | `Observation.interpretation` | CodeableConcept |
| `observation/methodCode` | `Observation.method` | CodeableConcept |
| `observation/targetSiteCode` | `Observation.bodySite` | CodeableConcept |

---

## 3. Common Vital Signs

### Heart Rate

**LOINC Code:** `8867-4` (Heart rate)

**C-CDA:**
```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <id root="1.2.3.4" extension="hr-123"/>
  <code code="8867-4" displayName="Heart rate"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>
  <value xsi:type="PQ" value="72" unit="/min"/>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "hr-123",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "8867-4",
        "display": "Heart rate"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "valueQuantity": {
    "value": 72,
    "unit": "/min",
    "system": "http://unitsofmeasure.org",
    "code": "/min"
  }
}
```

### Body Temperature

**LOINC Code:** `8310-5` (Body temperature)

**Units:** `Cel` (Celsius) or `[degF]` (Fahrenheit)

### Respiratory Rate

**LOINC Code:** `9279-1` (Respiratory rate)

**Units:** `/min`

### Body Weight

**LOINC Code:** `29463-7` (Body weight) or `3141-9` (Body weight Measured)

**Units:** `kg`, `g`, `[lb_av]` (pounds)

### Body Height

**LOINC Code:** `8302-2` (Body height) or `8306-3` (Body height --lying)

**Units:** `cm`, `m`, `[in_i]` (inches)

### Body Mass Index (BMI)

**LOINC Code:** `39156-5` (Body mass index)

**Units:** `kg/m2`

---

## 4. Blood Pressure (Special Handling)

**⚠️ IMPORTANT:** Blood pressure uses component structure, NOT separate observations for systolic/diastolic.

### Template

- Vital Sign Observation (`2.16.840.1.113883.10.20.22.4.27`) with special handling

### Mapping

**C-CDA:** Two separate observations (systolic and diastolic)

**FHIR:** Single Observation with two components

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| Systolic BP observation | `Observation.component[0]` | Component with code `8480-6` |
| Diastolic BP observation | `Observation.component[1]` | Component with code `8462-4` |
| Panel code | `Observation.code` | Fixed: `85354-9` (Blood pressure panel) |

### Example

**C-CDA:**
```xml
<!-- Systolic BP -->
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <code code="8480-6" displayName="Systolic blood pressure"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>
  <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
</observation>

<!-- Diastolic BP -->
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <code code="8462-4" displayName="Diastolic blood pressure"
        codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>
  <value xsi:type="PQ" value="80" unit="mm[Hg]"/>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "bp-123",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85354-9",
        "display": "Blood pressure panel with all children optional"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8480-6",
            "display": "Systolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 120,
        "unit": "mm[Hg]",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    },
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "8462-4",
            "display": "Diastolic blood pressure"
          }
        ]
      },
      "valueQuantity": {
        "value": 80,
        "unit": "mm[Hg]",
        "system": "http://unitsofmeasure.org",
        "code": "mm[Hg]"
      }
    }
  ]
}
```

**Blood Pressure LOINC Codes:**
- Panel: `85354-9` (Blood pressure panel with all children optional)
- Systolic: `8480-6` (Systolic blood pressure)
- Diastolic: `8462-4` (Diastolic blood pressure)

---

## 5. Pulse Oximetry (Special Handling)

**⚠️ IMPORTANT:** Pulse oximetry may include oxygen flow rate as a component.

### Template

- Vital Sign Observation (`2.16.840.1.113883.10.20.22.4.27`)

### Mapping

**Primary Measurement:** Oxygen saturation

**Optional Component:** Oxygen flow rate or inhaled oxygen concentration

| C-CDA Code | FHIR Mapping |
|------------|--------------|
| `2708-6` or `59408-5` | Main observation code (dual coding) |
| `3150-0` (Inhaled O2 concentration) | Component |
| `3151-8` (Inhaled O2 flow rate) | Component |

### Example

**C-CDA:**
```xml
<!-- Oxygen saturation -->
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <code code="2708-6" displayName="Oxygen saturation in Arterial blood"
        codeSystem="2.16.840.1.113883.6.1">
    <translation code="59408-5" displayName="Oxygen saturation in Arterial blood by Pulse oximetry"
                 codeSystem="2.16.840.1.113883.6.1"/>
  </code>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>
  <value xsi:type="PQ" value="98" unit="%"/>
</observation>

<!-- Oxygen flow rate (if applicable) -->
<observation classCode="OBS" moodCode="EVN">
  <code code="3151-8" displayName="Inhaled oxygen flow rate"
        codeSystem="2.16.840.1.113883.6.1"/>
  <value xsi:type="PQ" value="2" unit="L/min"/>
</observation>
```

**FHIR:**
```json
{
  "resourceType": "Observation",
  "id": "spo2-123",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
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
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "valueQuantity": {
    "value": 98,
    "unit": "%",
    "system": "http://unitsofmeasure.org",
    "code": "%"
  },
  "component": [
    {
      "code": {
        "coding": [
          {
            "system": "http://loinc.org",
            "code": "3151-8",
            "display": "Inhaled oxygen flow rate"
          }
        ]
      },
      "valueQuantity": {
        "value": 2,
        "unit": "L/min",
        "system": "http://unitsofmeasure.org",
        "code": "L/min"
      }
    }
  ]
}
```

**Pulse Oximetry LOINC Codes:**
- Primary: `59408-5` (Oxygen saturation in Arterial blood by Pulse oximetry)
- Alternative: `2708-6` (Oxygen saturation in Arterial blood)
- Oxygen flow: `3151-8` (Inhaled oxygen flow rate)
- Oxygen concentration: `3150-0` (Inhaled oxygen concentration)

---

## 6. Status Mapping

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `final` |
| `active` | `preliminary` |
| `aborted` | `cancelled` |

---

## 7. Interpretation Codes

**C-CDA:**
```xml
<interpretationCode code="N" displayName="Normal"
                    codeSystem="2.16.840.1.113883.5.83"/>
```

**FHIR:**
```json
{
  "interpretation": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
          "code": "N",
          "display": "Normal"
        }
      ]
    }
  ]
}
```

**Common Interpretation Codes:**
- `N` - Normal
- `L` - Low
- `H` - High
- `LL` - Critical low
- `HH` - Critical high
- `A` - Abnormal

---

## 8. Method and Body Site

### Method

**C-CDA:**
```xml
<methodCode code="82810-3" displayName="Oral temperature"
            codeSystem="2.16.840.1.113883.6.1"/>
```

**FHIR:**
```json
{
  "method": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "82810-3",
        "display": "Oral temperature"
      }
    ]
  }
}
```

### Body Site

**C-CDA:**
```xml
<targetSiteCode code="368209003" displayName="Right arm"
                codeSystem="2.16.840.1.113883.6.96"/>
```

**FHIR:**
```json
{
  "bodySite": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "368209003",
        "display": "Right arm"
      }
    ]
  }
}
```

---

## 9. Complete Example: Vital Signs Panel

### C-CDA

```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
  <id root="1.2.3.4" extension="vitals-202003151200"/>
  <code code="46680005" displayName="Vital signs"
        codeSystem="2.16.840.1.113883.6.96">
    <translation code="74728-7" codeSystem="2.16.840.1.113883.6.1"/>
  </code>
  <statusCode code="completed"/>
  <effectiveTime value="20200315120000-0500"/>

  <!-- Blood Pressure -->
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
      <id root="1.2.3.4" extension="bp-sys-1"/>
      <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200315120000-0500"/>
      <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
    </observation>
  </component>
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
      <id root="1.2.3.4" extension="bp-dia-1"/>
      <code code="8462-4" codeSystem="2.16.840.1.113883.6.1"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200315120000-0500"/>
      <value xsi:type="PQ" value="80" unit="mm[Hg]"/>
    </observation>
  </component>

  <!-- Heart Rate -->
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
      <id root="1.2.3.4" extension="hr-1"/>
      <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200315120000-0500"/>
      <value xsi:type="PQ" value="72" unit="/min"/>
    </observation>
  </component>

  <!-- Temperature -->
  <component>
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
      <id root="1.2.3.4" extension="temp-1"/>
      <code code="8310-5" codeSystem="2.16.840.1.113883.6.1"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200315120000-0500"/>
      <value xsi:type="PQ" value="37.2" unit="Cel"/>
    </observation>
  </component>
</organizer>
```

### FHIR

**Panel Observation:**
```json
{
  "resourceType": "Observation",
  "id": "vitals-202003151200",
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/observation-category",
          "code": "vital-signs"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85353-1",
        "display": "Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"
      }
    ]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "hasMember": [
    {"reference": "Observation/bp-1"},
    {"reference": "Observation/hr-1"},
    {"reference": "Observation/temp-1"}
  ]
}
```

**Blood Pressure Observation (combined):**
```json
{
  "resourceType": "Observation",
  "id": "bp-1",
  "status": "final",
  "category": [{"coding": [{"code": "vital-signs"}]}],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "85354-9",
        "display": "Blood pressure panel"
      }
    ]
  },
  "subject": {"reference": "Patient/patient-123"},
  "effectiveDateTime": "2020-03-15T12:00:00-05:00",
  "component": [
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]},
      "valueQuantity": {"value": 120, "unit": "mm[Hg]"}
    },
    {
      "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4"}]},
      "valueQuantity": {"value": 80, "unit": "mm[Hg]"}
    }
  ]
}
```

---

## Quick Reference: Common Vital Sign LOINC Codes

| Vital Sign | LOINC Code | UCUM Unit |
|------------|------------|-----------|
| Heart rate | `8867-4` | `/min` |
| Respiratory rate | `9279-1` | `/min` |
| Body temperature | `8310-5` | `Cel`, `[degF]` |
| Body weight | `29463-7` | `kg`, `[lb_av]` |
| Body height | `8302-2` | `cm`, `[in_i]` |
| BMI | `39156-5` | `kg/m2` |
| Blood pressure panel | `85354-9` | — |
| Systolic BP | `8480-6` | `mm[Hg]` |
| Diastolic BP | `8462-4` | `mm[Hg]` |
| Oxygen saturation | `59408-5` | `%` |
| Oxygen flow rate | `3151-8` | `L/min` |

---

## Implementation Notes

### Blood Pressure Detection

When converting C-CDA to FHIR:
1. Detect systolic (`8480-6`) and diastolic (`8462-4`) observations
2. Combine into single Observation with `code: 85354-9`
3. Use component structure for systolic/diastolic values
4. Ensure both have same effectiveTime

### Panel vs Individual

**Create Panel when:**
- C-CDA has Vital Signs Organizer template
- Multiple vital signs taken at same time

**Skip Panel when:**
- Single vital sign measurement
- Vital signs from different times

### US Core Vital Signs Profiles

Use appropriate US Core profiles:
- [US Core Vital Signs Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-vital-signs.html)
- [US Core Blood Pressure Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-blood-pressure.html)
- [US Core BMI Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-bmi.html)
- [US Core Body Height Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-body-height.html)
- [US Core Body Weight Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-body-weight.html)
- [US Core Body Temperature Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-body-temperature.html)
- [US Core Heart Rate Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-heart-rate.html)
- [US Core Respiratory Rate Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-respiratory-rate.html)
- [US Core Pulse Oximetry Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-pulse-oximetry.html)

---

## References

- [C-CDA on FHIR Vital Signs Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-vitals.html)
- [FHIR Vital Signs Profile](http://hl7.org/fhir/R4/observation-vitalsigns.html)
- [US Core Vital Signs Profiles](http://hl7.org/fhir/us/core/profiles-and-extensions.html#observation)
- [C-CDA Vital Signs Organizer](https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.26.html)
- [C-CDA Vital Sign Observation](https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.27.html)

## Related Mappings

- See [04-observation.md](04-observation.md) for general observation mapping details
