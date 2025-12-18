# MedicationRequest Mapping: C-CDA Medication Activity ↔ FHIR MedicationRequest

This document provides detailed mapping guidance between C-CDA Medication Activity and FHIR `MedicationRequest` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Medication Activity (`2.16.840.1.113883.10.20.22.4.16`) | `MedicationRequest` |
| Section: Medications (LOINC `10160-0`) | — |
| moodCode: INT (intended) | `MedicationRequest` with intent |
| moodCode: EVN (historical) | `MedicationStatement` (not covered here) |

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `@negationInd="true"` | `MedicationRequest.doNotPerform` | Set to `true` |
| `@moodCode` | `MedicationRequest.intent` | [Intent ConceptMap](#intent-mapping) |
| `substanceAdministration/id` | `MedicationRequest.identifier` | ID → Identifier |
| `substanceAdministration/statusCode` | `MedicationRequest.status` | [Status ConceptMap](#status-mapping) |
| `effectiveTime[1]/@value` | `dosageInstruction.timing.event` | DateTime |
| `effectiveTime[1]/low` | `dosageInstruction.timing.repeat.boundsPeriod.start` | Date conversion |
| `effectiveTime[1]/high` | `dosageInstruction.timing.repeat.boundsPeriod.end` | Date conversion |
| `effectiveTime[@operator='A']` (PIVL_TS) | `dosageInstruction.timing.repeat` | [Frequency Mapping](#frequency-mapping) |
| `effectiveTime[@operator='A']` (EIVL_TS) | `dosageInstruction.timing.repeat.when` | [Event-Based Timing](#event-based-timing) |
| `routeCode` | `dosageInstruction.route` | CodeableConcept |
| `approachSiteCode` | `dosageInstruction.site` | CodeableConcept |
| `doseQuantity` | `dosageInstruction.doseAndRate.doseQuantity` | Quantity |
| `rateQuantity` | `dosageInstruction.doseAndRate.rateQuantity` | Quantity |
| `maxDoseQuantity` | `dosageInstruction.maxDosePerPeriod` | Ratio |
| `consumable/manufacturedProduct/manufacturedMaterial/code` | `medicationCodeableConcept` | CodeableConcept |
| `consumable/manufacturedProduct` (complex) | `medicationReference` | Reference(Medication) |
| `author` | `requester` + Provenance | Reference(Practitioner) |
| `author/time` | `authoredOn` | DateTime |
| Indication | `reasonCode` | CodeableConcept |
| Instructions | `dosageInstruction.text` / `.patientInstruction` | String |
| Precondition | `dosageInstruction.asNeededBoolean` | Boolean |
| Supply/repeatNumber | `dispenseRequest.numberOfRepeatsAllowed` | Integer (minus 1) |
| Supply/quantity | `dispenseRequest.quantity` | Quantity |
| Supply/effectiveTime/high | `dispenseRequest.validityPeriod.end` | DateTime |

### Intent Mapping

**C-CDA:**
```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
```

**Medication Intent ConceptMap:**

| C-CDA moodCode | FHIR intent |
|----------------|-------------|
| `INT` | `plan` |
| `RQO` | `order` |
| `PRMS` | `plan` |
| `PRP` | `proposal` |
| `EVN` | Use MedicationStatement instead |

**FHIR:**
```json
{
  "intent": "order"
}
```

### Status Mapping

**C-CDA:**
```xml
<statusCode code="active"/>
```

**Medication Status ConceptMap:**

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| `active` | `active` | — |
| `completed` | `completed` | Check effectiveTime - may be `active` if future dates |
| `aborted` | `stopped` | — |
| `cancelled` | `cancelled` | — |
| `held` | `on-hold` | — |
| `new` | `draft` | — |
| `suspended` | `on-hold` | — |
| `nullified` | `entered-in-error` | — |

**Status Ambiguity Note:**
C-CDA may list a medication as "completed" but containing dates in the future. Evaluate timestamps relative to current date:
- "completed" with future dates → FHIR `active`
- "completed" with past dates → FHIR `completed`

**FHIR:**
```json
{
  "status": "active"
}
```

### Medication Code Mapping

#### Simple (CodeableConcept)

**C-CDA:**
```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
    <manufacturedMaterial>
      <code code="197361" codeSystem="2.16.840.1.113883.6.88"
            displayName="Lisinopril 10 MG Oral Tablet">
        <originalText>
          <reference value="#med1"/>
        </originalText>
      </code>
    </manufacturedMaterial>
  </manufacturedProduct>
</consumable>
```

**FHIR:**
```json
{
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }],
    "text": "Lisinopril 10 MG Oral Tablet"
  }
}
```

#### Complex (Reference to Medication)

When additional medication details (form, manufacturer, ingredients) require representation:

**FHIR MedicationRequest:**
```json
{
  "medicationReference": {
    "reference": "Medication/med-lisinopril"
  }
}
```

**FHIR Medication:**
```json
{
  "resourceType": "Medication",
  "id": "med-lisinopril",
  "code": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  },
  "form": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "385055001",
      "display": "Tablet"
    }]
  },
  "manufacturer": {
    "display": "Generic Manufacturer"
  }
}
```

### Timing and Frequency Mapping

#### Scheduling (First effectiveTime)

**C-CDA (single datetime):**
```xml
<effectiveTime xsi:type="IVL_TS" value="20200301"/>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "timing": {
      "event": ["2020-03-01"]
    }
  }]
}
```

**C-CDA (period):**
```xml
<effectiveTime xsi:type="IVL_TS">
  <low value="20200301"/>
  <high value="20200401"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "timing": {
      "repeat": {
        "boundsPeriod": {
          "start": "2020-03-01",
          "end": "2020-04-01"
        }
      }
    }
  }]
}
```

#### Frequency Mapping (PIVL_TS)

**C-CDA:**
```xml
<effectiveTime xsi:type="PIVL_TS" operator="A" institutionSpecified="false">
  <period value="8" unit="h"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "timing": {
      "repeat": {
        "frequency": 1,
        "period": 8,
        "periodUnit": "h"
      }
    }
  }]
}
```

**Range in Period:**

**C-CDA:**
```xml
<effectiveTime xsi:type="PIVL_TS" operator="A">
  <period>
    <low value="4" unit="h"/>
    <high value="6" unit="h"/>
  </period>
</effectiveTime>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "timing": {
      "repeat": {
        "frequency": 1,
        "period": 4,
        "periodMax": 6,
        "periodUnit": "h"
      }
    }
  }]
}
```

**Common Frequency Patterns:**

| CDA Pattern | FHIR Timing |
|-------------|-------------|
| Every 8 hours | `frequency: 1, period: 8, periodUnit: "h"` |
| Twice daily (BID) | `frequency: 2, period: 1, periodUnit: "d"` |
| Three times daily (TID) | `frequency: 3, period: 1, periodUnit: "d"` |
| Once daily | `frequency: 1, period: 1, periodUnit: "d"` |
| Every 12 hours | `frequency: 1, period: 12, periodUnit: "h"` |
| Once weekly | `frequency: 1, period: 1, periodUnit: "wk"` |

#### Event-Based Timing (EIVL_TS)

**C-CDA:**
```xml
<effectiveTime xsi:type="EIVL_TS" operator="A">
  <event code="ACM"/>
  <offset>
    <width value="30" unit="min"/>
  </offset>
</effectiveTime>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "timing": {
      "repeat": {
        "when": ["ACM"],
        "offset": 30
      }
    }
  }]
}
```

**Event Codes (when):**

| Code | Display |
|------|---------|
| `AC` | Before meal |
| `ACM` | Before breakfast |
| `ACD` | Before lunch |
| `ACV` | Before dinner |
| `PC` | After meal |
| `PCM` | After breakfast |
| `PCD` | After lunch |
| `PCV` | After dinner |
| `HS` | At bedtime |
| `WAKE` | Upon waking |

**Offset Conversion:** CDA offset values must be converted to minutes for FHIR.

### Dosage Mapping

**C-CDA:**
```xml
<doseQuantity value="10" unit="mg"/>
<routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
           displayName="Oral"/>
<approachSiteCode code="181216001" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Mouth"/>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "route": {
      "coding": [{
        "system": "http://ncimeta.nci.nih.gov",
        "code": "C38288",
        "display": "Oral"
      }]
    },
    "site": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "181216001",
        "display": "Mouth"
      }]
    },
    "doseAndRate": [{
      "doseQuantity": {
        "value": 10,
        "unit": "mg",
        "system": "http://unitsofmeasure.org",
        "code": "mg"
      }
    }]
  }]
}
```

### Max Dose Mapping

**C-CDA:**
```xml
<maxDoseQuantity>
  <numerator value="4000" unit="mg"/>
  <denominator value="1" unit="d"/>
</maxDoseQuantity>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "maxDosePerPeriod": {
      "numerator": {
        "value": 4000,
        "unit": "mg",
        "system": "http://unitsofmeasure.org",
        "code": "mg"
      },
      "denominator": {
        "value": 1,
        "unit": "day",
        "system": "http://unitsofmeasure.org",
        "code": "d"
      }
    }
  }]
}
```

### Indication (Reason)

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <code code="75326-9" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="59621000" codeSystem="2.16.840.1.113883.6.96"
           displayName="Essential hypertension"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "59621000",
      "display": "Essential hypertension"
    }]
  }]
}
```

### Instructions

**C-CDA (free text sig):**
```xml
<text>Take one tablet by mouth daily</text>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "text": "Take one tablet by mouth daily"
  }]
}
```

**C-CDA (Instruction Activity - coded):**
```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
    <code code="422037009" codeSystem="2.16.840.1.113883.6.96"
          displayName="Provider medication administration instructions"/>
    <text>Take with food</text>
  </act>
</entryRelationship>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "additionalInstruction": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "311504000",
        "display": "With or after food"
      }]
    }],
    "patientInstruction": "Take with food"
  }]
}
```

### As Needed (Precondition)

#### With Coded Reason

**C-CDA:**
```xml
<precondition typeCode="PRCN">
  <criterion>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="25064002" codeSystem="2.16.840.1.113883.6.96"
           displayName="Headache"/>
  </criterion>
</precondition>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "asNeededCodeableConcept": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "25064002",
        "display": "Headache"
      }]
    }
  }]
}
```

**Note:** When a coded reason is present, use `asNeededCodeableConcept`. Boolean is implied `true` per FHIR specification.

#### Without Coded Reason

**C-CDA:**
```xml
<precondition typeCode="PRCN">
  <criterion>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <!-- No value element - simple PRN -->
  </criterion>
</precondition>
```

**FHIR:**
```json
{
  "dosageInstruction": [{
    "asNeededBoolean": true
  }]
}
```

**Note:** `asNeededBoolean` and `asNeededCodeableConcept` are mutually exclusive (FHIR choice type `asNeeded[x]`). Use one or the other, never both.

### Supply/Dispense Information

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.17"/>
    <repeatNumber value="3"/>
    <quantity value="30"/>
    <effectiveTime>
      <high value="20210301"/>
    </effectiveTime>
  </supply>
</entryRelationship>
```

**FHIR:**
```json
{
  "dispenseRequest": {
    "numberOfRepeatsAllowed": 2,
    "quantity": {
      "value": 30
    },
    "validityPeriod": {
      "end": "2021-03-01"
    }
  }
}
```

**Repeat Number Conversion:**
- CDA `repeatNumber` represents total number of dispenses allowed
- FHIR `numberOfRepeatsAllowed` represents refills (excludes original fill)
- Formula: `numberOfRepeatsAllowed = repeatNumber - 1`

### Drug Vehicle

**C-CDA:**
```xml
<participant typeCode="CSM">
  <participantRole classCode="MANU">
    <playingEntity classCode="MMAT">
      <code code="324049" codeSystem="2.16.840.1.113883.6.88"
            displayName="Normal saline"/>
    </playingEntity>
  </participantRole>
</participant>
```

This maps to the `Medication` resource's `ingredient` with `isActive = false`:

**FHIR Medication:**
```json
{
  "resourceType": "Medication",
  "ingredient": [{
    "itemCodeableConcept": {
      "coding": [{
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "324049",
        "display": "Normal saline"
      }]
    },
    "isActive": false
  }]
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `MedicationRequest.identifier` | `substanceAdministration/id` | Identifier → ID |
| `MedicationRequest.status` | `substanceAdministration/statusCode` | Reverse status map |
| `MedicationRequest.intent` | `@moodCode` | Reverse intent map |
| `MedicationRequest.doNotPerform: true` | `@negationInd="true"` | Set negation |
| `MedicationRequest.medicationCodeableConcept` | `consumable/manufacturedMaterial/code` | CodeableConcept → CE |
| `MedicationRequest.medicationReference` | `consumable/manufacturedProduct` | Create product |
| `dosageInstruction.timing.repeat.boundsPeriod` | First `effectiveTime` | Period |
| `dosageInstruction.timing.repeat.frequency/period` | Second `effectiveTime` (PIVL_TS) | Frequency |
| `dosageInstruction.timing.repeat.when` | Second `effectiveTime` (EIVL_TS) | Event timing |
| `dosageInstruction.route` | `routeCode` | CodeableConcept → CE |
| `dosageInstruction.site` | `approachSiteCode` | CodeableConcept → CD |
| `dosageInstruction.doseAndRate.doseQuantity` | `doseQuantity` | Quantity → PQ |
| `dosageInstruction.maxDosePerPeriod` | `maxDoseQuantity` | Ratio → RTO |
| `dosageInstruction.text` | `text` (sig) | Direct mapping |
| `dosageInstruction.asNeeded*` | `precondition` | Create precondition |
| `MedicationRequest.requester` | `author` | Create author |
| `MedicationRequest.authoredOn` | `author/time` | Date format |
| `MedicationRequest.reasonCode` | Indication observation | Create entryRelationship |
| `dispenseRequest.numberOfRepeatsAllowed` | `supply/repeatNumber` | Add 1 |
| `dispenseRequest.quantity` | `supply/quantity` | Quantity → PQ |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
  <code code="10160-0" codeSystem="2.16.840.1.113883.6.1"/>
  <title>MEDICATIONS</title>
  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="INT">
      <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
      <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
      <statusCode code="active"/>
      <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
        <high value="20210301"/>
      </effectiveTime>
      <effectiveTime xsi:type="PIVL_TS" operator="A" institutionSpecified="false">
        <period value="1" unit="d"/>
      </effectiveTime>
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Oral"/>
      <doseQuantity value="10" unit="mg"/>
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
          <manufacturedMaterial>
            <code code="197361" codeSystem="2.16.840.1.113883.6.88"
                  displayName="Lisinopril 10 MG Oral Tablet"/>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>
      <author>
        <time value="20200301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
          <code code="75326-9" codeSystem="2.16.840.1.113883.6.1"/>
          <value xsi:type="CD" code="59621000" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Essential hypertension"/>
        </observation>
      </entryRelationship>
      <entryRelationship typeCode="REFR">
        <supply classCode="SPLY" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.17"/>
          <repeatNumber value="3"/>
          <quantity value="30"/>
        </supply>
      </entryRelationship>
    </substanceAdministration>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "MedicationRequest",
  "id": "medicationrequest-lisinopril",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:cdbd33f0-6cde-11db-9fe1-0800200c9a66"
  }],
  "status": "active",
  "intent": "plan",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "authoredOn": "2020-03-01",
  "requester": {
    "reference": "Practitioner/practitioner-example"
  },
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "59621000",
      "display": "Essential hypertension"
    }]
  }],
  "dosageInstruction": [{
    "timing": {
      "repeat": {
        "boundsPeriod": {
          "start": "2020-03-01",
          "end": "2021-03-01"
        },
        "frequency": 1,
        "period": 1,
        "periodUnit": "d"
      }
    },
    "route": {
      "coding": [{
        "system": "http://ncimeta.nci.nih.gov",
        "code": "C38288",
        "display": "Oral"
      }]
    },
    "doseAndRate": [{
      "doseQuantity": {
        "value": 10,
        "unit": "mg",
        "system": "http://unitsofmeasure.org",
        "code": "mg"
      }
    }]
  }],
  "dispenseRequest": {
    "numberOfRepeatsAllowed": 2,
    "quantity": {
      "value": 30
    }
  }
}
```

## References

- [C-CDA on FHIR Medications Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html)
- [US Core MedicationRequest Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest)
- [C-CDA Medication Activity](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.16.html)
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/)
