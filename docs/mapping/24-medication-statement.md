# MedicationStatement Mapping: C-CDA Medication Activity (EVN) ↔ FHIR MedicationStatement

This document provides detailed mapping guidance between C-CDA Medication Activity with moodCode="EVN" and FHIR `MedicationStatement` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Medication Activity (`2.16.840.1.113883.10.20.22.4.16`) | `MedicationStatement` |
| Section: Medications (LOINC `10160-0`) | — |
| moodCode: EVN (event/actual use) | `MedicationStatement` |
| moodCode: INT (intended/prescribed) | `MedicationRequest` (see 07-medication-request.md) |

**Important Note:** The official C-CDA on FHIR Implementation Guide states:

> "Medications shown below represent the moodCode='INT' in CDA. For mapping histories of medication use from CDA, no consensus was established."

This mapping document provides guidance based on logical inference from the FHIR MedicationStatement specification and C-CDA Medication Activity template for moodCode="EVN".

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform | Notes |
|------------|-----------|-----------|-------|
| `@negationInd="true"` | `MedicationStatement.status` | Set to `not-taken` | Positive assertion of non-use |
| `@moodCode="EVN"` | Implies MedicationStatement | — | EVN = actual use, not orders |
| `substanceAdministration/id` | `MedicationStatement.identifier` | ID → Identifier | Multiple IDs allowed |
| `statusCode` | `MedicationStatement.status` | [Status ConceptMap](#status-mapping) | See table below |
| Context-dependent | `category` | Infer from encounter/section context | See [Implementation Considerations](#category-assignment) |
| `effectiveTime[1]` (IVL_TS) | `MedicationStatement.effectivePeriod` | Period conversion | When medication was taken |
| `effectiveTime[1]/@value` | `MedicationStatement.effectiveDateTime` | DateTime | Single date/time |
| `effectiveTime[@operator='A']` (PIVL_TS) | `dosage.timing.repeat` | [Frequency Mapping](#frequency-mapping) | How often taken |
| `effectiveTime[@operator='A']` (EIVL_TS) | `dosage.timing.repeat.when` | [Event-Based Timing](#event-based-timing) | Meal-related timing |
| `routeCode` | `dosage.route` | CodeableConcept (NCI → SNOMED) | Administration route |
| `approachSiteCode` | `dosage.site` | CodeableConcept | Body site |
| `doseQuantity` | `dosage.doseAndRate.doseQuantity` | Quantity | Amount per dose |
| `rateQuantity` | `dosage.doseAndRate.rateQuantity` | Quantity | Rate (for IV) |
| `maxDoseQuantity` | `dosage.maxDosePerPeriod` | Ratio | Maximum dose |
| `consumable/manufacturedProduct/manufacturedMaterial/code` | `medicationCodeableConcept` | CodeableConcept | RxNorm preferred |
| `consumable/manufacturedProduct` (complex) | `medicationReference` | Reference(Medication) | When additional details needed |
| `author` | `informationSource` | Reference(Practitioner/Patient) | Who documented |
| `author/time` | `dateAsserted` | DateTime | When documented |
| Indication entryRelationship | `reasonCode` | CodeableConcept | Why medication taken |
| Indication reference | `reasonReference` | Reference(Condition) | Clinical justification |
| Instructions/text | `dosage.text` | String | Free text dosage |
| Precondition | `dosage.asNeeded[x]` | Boolean or CodeableConcept | PRN indicator |

### Status Mapping

**C-CDA:**
```xml
<statusCode code="active"/>
```

**Status ConceptMap:**

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| `active` | `active` | Currently taking |
| `completed` | `completed` | Medication course complete |
| `aborted` | `stopped` | Discontinued |
| `cancelled` | `entered-in-error` | May also use `stopped` depending on context |
| `suspended` | `on-hold` | Temporarily not taking |

**Special Case - Negation:**

| C-CDA Pattern | FHIR status | Notes |
|---------------|-------------|-------|
| `negationInd="true"` + any statusCode | `not-taken` | Positive assertion medication NOT taken |

**FHIR:**
```json
{
  "status": "active"
}
```

### Negation (Not Taken) Mapping

**C-CDA (Medication Refused):**
```xml
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
  <id root="b64f60b0-7cde-12db-9fe1-0800200c9a66"/>
  <statusCode code="completed"/>

  <effectiveTime xsi:type="IVL_TS">
    <low value="20240115"/>
  </effectiveTime>

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

**FHIR:**
```json
{
  "resourceType": "MedicationStatement",
  "id": "example-not-taken",
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:b64f60b0-7cde-12db-9fe1-0800200c9a66"
  }],
  "status": "not-taken",
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "308971",
      "display": "Warfarin Sodium 5 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectiveDateTime": "2024-01-15",
  "dateAsserted": "2024-01-15",
  "note": [{
    "text": "Patient refused medication"
  }]
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
      <code code="197380" codeSystem="2.16.840.1.113883.6.88"
            displayName="atenolol 25 MG Oral Tablet">
        <originalText>
          <reference value="#med1"/>
        </originalText>
        <translation code="00378-0025-01" codeSystem="2.16.840.1.113883.6.69"
                     displayName="Atenolol 25mg Tab"/>
      </code>
    </manufacturedMaterial>
  </manufacturedProduct>
</consumable>
```

**FHIR:**
```json
{
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197380",
        "display": "atenolol 25 MG Oral Tablet"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "00378-0025-01",
        "display": "Atenolol 25mg Tab"
      }
    ],
    "text": "atenolol 25 MG Oral Tablet"
  }
}
```

#### Complex (Reference to Medication)

When additional medication details (form, manufacturer, ingredients) require representation:

**FHIR MedicationStatement:**
```json
{
  "medicationReference": {
    "reference": "Medication/med-atenolol"
  }
}
```

**FHIR Medication:**
```json
{
  "resourceType": "Medication",
  "id": "med-atenolol",
  "code": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197380",
      "display": "atenolol 25 MG Oral Tablet"
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
    "display": "Mylan Pharmaceuticals Inc"
  }
}
```

### Timing Mapping

#### Effective Period (When Medication Was Taken)

**C-CDA (single datetime):**
```xml
<effectiveTime xsi:type="IVL_TS" value="20120318"/>
```

**FHIR:**
```json
{
  "effectiveDateTime": "2012-03-18"
}
```

**C-CDA (period):**
```xml
<effectiveTime xsi:type="IVL_TS">
  <low value="20120318"/>
  <high value="20130318"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "effectivePeriod": {
    "start": "2012-03-18",
    "end": "2013-03-18"
  }
}
```

**C-CDA (ongoing - no end date):**
```xml
<effectiveTime xsi:type="IVL_TS">
  <low value="20120318"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "effectivePeriod": {
    "start": "2012-03-18"
  }
}
```

#### Frequency Mapping (PIVL_TS)

**C-CDA:**
```xml
<effectiveTime xsi:type="PIVL_TS" operator="A" institutionSpecified="false">
  <period value="12" unit="h"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "dosage": [{
    "timing": {
      "repeat": {
        "frequency": 1,
        "period": 12,
        "periodUnit": "h"
      }
    }
  }]
}
```

**Common Frequency Patterns:**

| C-CDA Pattern | Description | FHIR Timing |
|---------------|-------------|-------------|
| `<period value="24" unit="h"/>` | Once daily (QD) | `frequency: 1, period: 1, periodUnit: "d"` |
| `<period value="12" unit="h"/>` | Twice daily (BID) | `frequency: 1, period: 12, periodUnit: "h"` OR `frequency: 2, period: 1, periodUnit: "d"` |
| `<period value="8" unit="h"/>` | Three times daily (TID) | `frequency: 1, period: 8, periodUnit: "h"` OR `frequency: 3, period: 1, periodUnit: "d"` |
| `<period value="6" unit="h"/>` | Four times daily (QID) | `frequency: 1, period: 6, periodUnit: "h"` OR `frequency: 4, period: 1, periodUnit: "d"` |
| `<period value="4" unit="h"/>` | Every 4 hours (Q4H) | `frequency: 1, period: 4, periodUnit: "h"` |
| `<period value="1" unit="wk"/>` | Once weekly | `frequency: 1, period: 1, periodUnit: "wk"` |

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
  "dosage": [{
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
  "dosage": [{
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

| Code | Display | Notes |
|------|---------|-------|
| `AC` | Before meal | General before meal |
| `ACM` | Before breakfast | Before morning meal |
| `ACD` | Before lunch | Before midday meal |
| `ACV` | Before dinner | Before evening meal |
| `PC` | After meal | General after meal |
| `PCM` | After breakfast | After morning meal |
| `PCD` | After lunch | After midday meal |
| `PCV` | After dinner | After evening meal |
| `HS` | At bedtime | Before sleep |
| `WAKE` | Upon waking | After waking |

**Offset Conversion:** C-CDA offset values must be converted to minutes for FHIR.

### Dosage Mapping

**C-CDA:**
```xml
<doseQuantity value="1"/>
<routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
           displayName="Oral"/>
<approachSiteCode code="181220002" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Mouth"/>
```

**FHIR:**
```json
{
  "dosage": [{
    "route": {
      "coding": [{
        "system": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        "code": "C38288",
        "display": "Oral"
      }]
    },
    "site": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "181220002",
        "display": "Mouth"
      }]
    },
    "doseAndRate": [{
      "doseQuantity": {
        "value": 1
      }
    }]
  }]
}
```

**With Units:**

**C-CDA:**
```xml
<doseQuantity value="10" unit="mg"/>
```

**FHIR:**
```json
{
  "dosage": [{
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
  "dosage": [{
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

### Indication (Reason) Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <id root="db734647-fc99-424c-a864-7e3cda82e705"/>
    <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Hypertensive disorder"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "38341003",
      "display": "Hypertensive disorder"
    }]
  }]
}
```

**With Reference:**

If the indication observation contains an entry reference to a Condition:

**FHIR:**
```json
{
  "reasonReference": [{
    "reference": "Condition/hypertension"
  }]
}
```

### Instructions Mapping

**C-CDA (free text):**
```xml
<text>
  <reference value="#sig1"/>
</text>
```

**FHIR:**
```json
{
  "dosage": [{
    "text": "Take 1 tablet by mouth every 12 hours"
  }]
}
```

**C-CDA (Instruction Activity):**
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
  "dosage": [{
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

### As Needed (Precondition) Mapping

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
  "dosage": [{
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
  "dosage": [{
    "asNeededBoolean": true
  }]
}
```

**Note:** `asNeededBoolean` and `asNeededCodeableConcept` are mutually exclusive (FHIR choice type `asNeeded[x]`).

### Author and Dating Mapping

**C-CDA:**
```xml
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
```

**FHIR:**
```json
{
  "dateAsserted": "2012-03-18",
  "informationSource": {
    "reference": "Practitioner/practitioner-1234567890",
    "display": "Dr. Adam Careful"
  }
}
```

**Note:** When the author is the patient (patient-reported), reference the Patient resource:

```json
{
  "informationSource": {
    "reference": "Patient/example"
  },
  "category": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
      "code": "patientspecified",
      "display": "Patient Specified"
    }]
  }
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `MedicationStatement.identifier` | `substanceAdministration/id` | Identifier → ID |
| `MedicationStatement.status` | `substanceAdministration/statusCode` + `@negationInd` | Reverse status map; "not-taken" → negationInd="true" |
| `MedicationStatement.medicationCodeableConcept` | `consumable/manufacturedMaterial/code` | CodeableConcept → CE |
| `MedicationStatement.medicationReference` | `consumable/manufacturedProduct` | Create product with details |
| `MedicationStatement.subject` | Referenced patient | Link to patient |
| `MedicationStatement.context` | Parent encounter | Create encounter reference |
| `MedicationStatement.effectivePeriod` | First `effectiveTime` (IVL_TS) | Period → IVL_TS |
| `MedicationStatement.effectiveDateTime` | First `effectiveTime/@value` | DateTime → TS |
| `dosage.timing.repeat.frequency/period` | Second `effectiveTime` (PIVL_TS) | Frequency mapping |
| `dosage.timing.repeat.when` | Second `effectiveTime` (EIVL_TS) | Event timing |
| `dosage.route` | `routeCode` | CodeableConcept → CE |
| `dosage.site` | `approachSiteCode` | CodeableConcept → CD |
| `dosage.doseAndRate.doseQuantity` | `doseQuantity` | Quantity → PQ |
| `dosage.maxDosePerPeriod` | `maxDoseQuantity` | Ratio → RTO |
| `dosage.text` | `text` or Instructions entryRelationship | String → text/sig |
| `dosage.asNeeded*` | `precondition` | Create precondition element |
| `MedicationStatement.informationSource` | `author` | Create author participation |
| `MedicationStatement.dateAsserted` | `author/time` | DateTime → TS |
| `MedicationStatement.reasonCode` | Indication observation | Create RSON entryRelationship |
| `MedicationStatement.reasonReference` | Indication with reference | Create RSON with reference to condition |

### Reverse Status Mapping

| FHIR status | C-CDA Mapping | Notes |
|-------------|---------------|-------|
| `active` | `statusCode="active"` | Currently taking |
| `completed` | `statusCode="completed"` | Medication course complete |
| `stopped` | `statusCode="aborted"` | Discontinued |
| `on-hold` | `statusCode="suspended"` | Temporarily suspended |
| `entered-in-error` | `statusCode="cancelled"` | Error correction |
| `not-taken` | `negationInd="true"` + `statusCode="completed"` | Positive assertion of non-use |
| `intended` | Use Planned Medication Activity template instead | Future medications |
| `unknown` | `statusCode nullFlavor="UNK"` | Status unknown |

### Additional EntryRelationship Mappings

The C-CDA Medication Activity template supports additional optional entryRelationships. Here's how they map to FHIR:

#### Medication Supply Order (Template 2.16.840.1.113883.10.20.22.4.17)

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.17"/>
    <!-- Supply order details -->
  </supply>
</entryRelationship>
```

**FHIR:**
```json
{
  "derivedFrom": [{
    "reference": "MedicationRequest/supply-order-id"
  }]
}
```

**Note:** The supply order becomes a separate MedicationRequest resource.

#### Medication Dispense (Template 2.16.840.1.113883.10.20.22.4.18)

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18"/>
    <!-- Dispense details -->
  </supply>
</entryRelationship>
```

**FHIR:**
```json
{
  "partOf": [{
    "reference": "MedicationDispense/dispense-id"
  }]
}
```

**Or:**
```json
{
  "derivedFrom": [{
    "reference": "MedicationDispense/dispense-id"
  }]
}
```

**Note:** The dispense becomes a separate MedicationDispense resource.

#### Reaction Observation (Template 2.16.840.1.113883.10.20.22.4.9)

**C-CDA:**
```xml
<entryRelationship typeCode="MFST" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="422587007" codeSystem="2.16.840.1.113883.6.96"
           displayName="Nausea"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "note": [{
    "text": "Adverse reaction: Nausea"
  }]
}
```

**Or create separate AllergyIntolerance:**
```json
{
  "resourceType": "AllergyIntolerance",
  "reaction": [{
    "substance": {
      "reference": "Medication/med-id"
    },
    "manifestation": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "422587007",
        "display": "Nausea"
      }]
    }]
  }]
}
```

#### Drug Monitoring Act (Template 2.16.840.1.113883.10.20.22.4.123)

**C-CDA:**
```xml
<entryRelationship typeCode="COMP">
  <act classCode="ACT" moodCode="INT">
    <templateId root="2.16.840.1.113883.10.20.22.4.123"/>
    <code code="395170001" codeSystem="2.16.840.1.113883.6.96"
          displayName="Medication monitoring"/>
  </act>
</entryRelationship>
```

**FHIR:**
```json
{
  "note": [{
    "text": "Drug monitoring required: Medication monitoring (SNOMED: 395170001)"
  }]
}
```

**Or use extension:**
```json
{
  "extension": [{
    "url": "http://example.org/fhir/StructureDefinition/drug-monitoring",
    "valueCodeableConcept": {
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "395170001",
        "display": "Medication monitoring"
      }]
    }
  }]
}
```

#### Medication Adherence

**C-CDA:**
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

**FHIR:**
```json
{
  "note": [{
    "text": "Medication compliance: Patient is adherent"
  }]
}
```

#### Drug Vehicle (Template 2.16.840.1.113883.10.20.22.4.24)

**C-CDA:**
```xml
<participant typeCode="CSM">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.24"/>
    <code code="412307009" codeSystem="2.16.840.1.113883.6.96"
          displayName="Drug vehicle"/>
    <playingEntity classCode="MMAT">
      <code code="324049" codeSystem="2.16.840.1.113883.6.88"
            displayName="Normal saline"/>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR:**

When using medicationReference, create a Medication resource with inactive ingredient:

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

### Route Code Translation Handling

When C-CDA includes both NCI Thesaurus and SNOMED translations:

**C-CDA:**
```xml
<routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
           displayName="Oral">
  <translation code="26643006" codeSystem="2.16.840.1.113883.6.96"
               displayName="Oral route"/>
</routeCode>
```

**FHIR:**

Include both codings:

```json
{
  "dosage": [{
    "route": {
      "coding": [
        {
          "system": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
          "code": "C38288",
          "display": "Oral"
        },
        {
          "system": "http://snomed.info/sct",
          "code": "26643006",
          "display": "Oral route"
        }
      ]
    }
  }]
}
```

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
  <code code="10160-0" codeSystem="2.16.840.1.113883.6.1"/>
  <title>MEDICATIONS</title>

  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
      <id root="cdbd5410-6cde-11db-9fe1-0800200c9a66"/>
      <statusCode code="active"/>

      <!-- Period: Started March 18, 2012, ongoing -->
      <effectiveTime xsi:type="IVL_TS">
        <low value="20120318"/>
      </effectiveTime>

      <!-- Frequency: Every 12 hours (BID) -->
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

      <author>
        <time value="20120318"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
          <code code="75321-0" codeSystem="2.16.840.1.113883.6.1"/>
          <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Hypertensive disorder"/>
        </observation>
      </entryRelationship>

    </substanceAdministration>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "MedicationStatement",
  "id": "medicationstatement-atenolol",
  "meta": {
    "profile": ["http://hl7.org/fhir/StructureDefinition/MedicationStatement"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:cdbd5410-6cde-11db-9fe1-0800200c9a66"
  }],
  "status": "active",
  "category": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
      "code": "community",
      "display": "Community"
    }]
  },
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197380",
      "display": "atenolol 25 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "effectivePeriod": {
    "start": "2012-03-18"
  },
  "dateAsserted": "2012-03-18",
  "informationSource": {
    "reference": "Practitioner/practitioner-1234567890"
  },
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "38341003",
      "display": "Hypertensive disorder"
    }]
  }],
  "dosage": [{
    "timing": {
      "repeat": {
        "frequency": 1,
        "period": 12,
        "periodUnit": "h"
      }
    },
    "route": {
      "coding": [{
        "system": "http://ncicb.nci.nih.gov/xml/owl/EVS/Thesaurus.owl",
        "code": "C38288",
        "display": "Oral"
      }]
    },
    "doseAndRate": [{
      "doseQuantity": {
        "value": 1
      }
    }]
  }]
}
```

## Implementation Considerations

### Category Assignment

C-CDA does not have an explicit category element for medication statements. The FHIR `category` should be inferred based on context:

- If from an inpatient encounter → `inpatient`
- If from an ambulatory encounter → `outpatient`
- If patient-reported (author is patient) → `patientspecified`
- Default → `community`

### Deduplication

When converting C-CDA to FHIR:
- Preserve C-CDA IDs in `MedicationStatement.identifier`
- Use these identifiers to support deduplication across MedicationStatement and MedicationRequest resources
- This helps identify when a statement is derived from or related to an order

### Handling Derived Information

When a medication statement is derived from other clinical records (e.g., from prescriptions or claims):

**FHIR:**
```json
{
  "derivedFrom": [{
    "reference": "MedicationRequest/prescription-123"
  }]
}
```

This is particularly useful when converting integrated C-CDA documents that contain both medication orders (INT) and statements (EVN).

### Timing Precision

C-CDA effectiveTime may have different levels of precision. Preserve the precision when mapping:

| C-CDA | FHIR |
|-------|------|
| `value="20120318"` | `"2012-03-18"` (date only) |
| `value="20120318120000"` | `"2012-03-18T12:00:00"` (full datetime) |
| `value="201203"` | `"2012-03"` (month precision) |

### Missing Information

When C-CDA elements are missing:
- If no effectiveTime: Omit `effective[x]` in FHIR
- If no author: Omit `informationSource` and `dateAsserted`
- If no frequency: Include only period in `dosage.timing` or omit timing entirely

## References

- [FHIR R4B MedicationStatement](https://hl7.org/fhir/R4B/medicationstatement.html)
- [C-CDA on FHIR Medications Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html)
- [US Core Implementation Guide STU7](https://hl7.org/fhir/us/core/STU7/) (Note: MedicationStatement profile deprecated)
- [US Core Medication List Guidance](https://hl7.org/fhir/us/core/medication-list.html)
- [C-CDA Medication Activity](http://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationActivity.html)
- [HL7 C-CDA Examples](https://github.com/HL7/C-CDA-Examples)
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/)
- [NCI Thesaurus Code System](https://build.fhir.org/ig/HL7/UTG/CodeSystem-v3-nciThesaurus.html)
