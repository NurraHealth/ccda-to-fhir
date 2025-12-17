# AllergyIntolerance Mapping: C-CDA Allergy ↔ FHIR AllergyIntolerance

This document provides detailed mapping guidance between C-CDA Allergy Concern Act / Allergy Intolerance Observation and FHIR `AllergyIntolerance` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Allergy Concern Act (`2.16.840.1.113883.10.20.22.4.30`) | Container for tracking |
| Allergy Intolerance Observation (`2.16.840.1.113883.10.20.22.4.7`) | `AllergyIntolerance` |
| Section: Allergies (LOINC `48765-2`) | Category determined from observation value |

## Structural Mapping

Each **Allergy Intolerance Observation** within an Allergy Concern Act maps to a separate FHIR `AllergyIntolerance` resource.

```
Allergy Concern Act (act)
├── statusCode → AllergyIntolerance.clinicalStatus (fallback)
├── author → AllergyIntolerance.recorder + Provenance
└── entryRelationship/observation (Allergy Intolerance Observation)
    ├── id → AllergyIntolerance.identifier
    ├── effectiveTime/low → AllergyIntolerance.onsetDateTime
    ├── effectiveTime/high → extension:allergyintolerance-abatement
    ├── value → AllergyIntolerance.type + .category
    ├── participant/playingEntity/code → AllergyIntolerance.code
    └── entryRelationship (nested observations)
        ├── Allergy Status → AllergyIntolerance.clinicalStatus
        ├── Criticality → AllergyIntolerance.criticality
        ├── Reaction Observation → AllergyIntolerance.reaction
        │   ├── value → reaction.manifestation
        │   └── Severity Observation → reaction.severity
        └── Comment Activity → AllergyIntolerance.note
```

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| Allergy Concern Act `statusCode` | `clinicalStatus` | Only if no Allergy Status Observation |
| Allergy Observation `id` | `identifier` | ID → Identifier |
| Allergy Observation `effectiveTime/low` | `onsetDateTime` | Date conversion |
| Allergy Observation `effectiveTime/high` | `extension:allergyintolerance-abatement` | Extension |
| Allergy Observation `value` | `type` + `category` | [Type/Category ConceptMap](#type-and-category-mapping) |
| `participant[@typeCode='CSM']/playingEntity/code` | `code` | [Allergen Code](#allergen-code-mapping) |
| Allergy Status Observation `value` | `clinicalStatus` | [Status ConceptMap](#clinical-status-mapping) |
| Criticality Observation `value` | `criticality` | [Criticality ConceptMap](#criticality-mapping) |
| Reaction Observation `value` | `reaction.manifestation` | CodeableConcept |
| Reaction Observation `effectiveTime` | `reaction.onset` | DateTime |
| Severity Observation `value` | `reaction.severity` | [Severity ConceptMap](#severity-mapping) |
| Comment Activity `text` | `note` | Annotation |
| Author (latest) | `recorder` | Reference(Practitioner) |
| Author/time (earliest) | `recordedDate` | DateTime |

### Type and Category Mapping

The Allergy Observation `value` element determines both `type` and `category`:

**C-CDA:**
```xml
<value xsi:type="CD" code="416098002" codeSystem="2.16.840.1.113883.6.96"
       displayName="Drug allergy"/>
```

**Allergy Type ConceptMap:**

| C-CDA SNOMED Code | Display | FHIR type |
|-------------------|---------|-----------|
| `419199007` | Allergy to substance | `allergy` |
| `416098002` | Drug allergy | `allergy` |
| `414285001` | Food allergy | `allergy` |
| `426232007` | Environmental allergy | `allergy` |
| `419511003` | Propensity to adverse reactions to drug | `allergy` |
| `59037007` | Drug intolerance | `intolerance` |
| `235719002` | Food intolerance | `intolerance` |
| `420134006` | Propensity to adverse reactions | (omit type) |

**Category ConceptMap:**

| C-CDA SNOMED Code | Display | FHIR category |
|-------------------|---------|---------------|
| `416098002` | Drug allergy | `medication` |
| `59037007` | Drug intolerance | `medication` |
| `419511003` | Propensity to adverse reactions to drug | `medication` |
| `414285001` | Food allergy | `food` |
| `235719002` | Food intolerance | `food` |
| `418471000` | Propensity to adverse reactions to food | `food` |
| `426232007` | Environmental allergy | `environment` |
| `419199007` | Allergy to substance | (may need inference) |
| `420134006` | Propensity to adverse reactions | (may need inference) |

**FHIR:**
```json
{
  "type": "allergy",
  "category": ["medication"]
}
```

### Allergen Code Mapping

**C-CDA:**
```xml
<participant typeCode="CSM">
  <participantRole classCode="MANU">
    <playingEntity classCode="MMAT">
      <code code="70618" codeSystem="2.16.840.1.113883.6.88"
            displayName="Penicillin V">
        <originalText>
          <reference value="#allergen1"/>
        </originalText>
        <translation code="7980" codeSystem="2.16.840.1.113883.6.88"
                     displayName="Penicillin"/>
      </code>
      <name>Penicillin</name>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR:**
```json
{
  "code": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "70618",
        "display": "Penicillin V"
      },
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "7980",
        "display": "Penicillin"
      }
    ],
    "text": "Penicillin"
  }
}
```

### Clinical Status Mapping

#### From Allergy Status Observation

**C-CDA:**
```xml
<entryRelationship typeCode="REFR">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.28"/>
    <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
           displayName="Active"/>
  </observation>
</entryRelationship>
```

**Allergy Status ConceptMap:**

| C-CDA SNOMED Code | Display | FHIR clinicalStatus |
|-------------------|---------|---------------------|
| `55561003` | Active | `active` |
| `73425007` | Inactive | `inactive` |
| `413322009` | Resolved | `resolved` |

**FHIR:**
```json
{
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
      "code": "active",
      "display": "Active"
    }]
  }
}
```

#### From Allergy Concern Act Status (Fallback)

If no Allergy Status Observation is present:

| CDA statusCode | FHIR clinicalStatus |
|----------------|---------------------|
| `active` | `active` |
| `completed` | `resolved` |
| `suspended` | `inactive` |
| `aborted` | `inactive` |

### Criticality Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="SUBJ" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.145"/>
    <code code="82606-5" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="CRITH" codeSystem="2.16.840.1.113883.5.1063"
           displayName="High Criticality"/>
  </observation>
</entryRelationship>
```

**Criticality ConceptMap:**

| C-CDA Code | System | Display | FHIR criticality |
|------------|--------|---------|------------------|
| `CRITL` | `2.16.840.1.113883.5.1063` | Low Criticality | `low` |
| `CRITH` | `2.16.840.1.113883.5.1063` | High Criticality | `high` |
| `CRITU` | `2.16.840.1.113883.5.1063` | Unable to Assess | `unable-to-assess` |

**FHIR:**
```json
{
  "criticality": "high"
}
```

### Reaction Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="MFST" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <statusCode code="completed"/>
    <effectiveTime>
      <low value="20100301"/>
    </effectiveTime>
    <value xsi:type="CD" code="247472004" codeSystem="2.16.840.1.113883.6.96"
           displayName="Hives"/>
    <!-- Severity Observation -->
    <entryRelationship typeCode="SUBJ" inversionInd="true">
      <observation classCode="OBS" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.22.4.8"/>
        <code code="SEV" codeSystem="2.16.840.1.113883.5.4"/>
        <value xsi:type="CD" code="6736007" codeSystem="2.16.840.1.113883.6.96"
               displayName="Moderate"/>
      </observation>
    </entryRelationship>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reaction": [{
    "manifestation": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "247472004",
        "display": "Hives"
      }]
    }],
    "onset": "2010-03-01",
    "severity": "moderate"
  }]
}
```

### Severity Mapping

**Severity ConceptMap:**

| C-CDA SNOMED Code | Display | FHIR severity |
|-------------------|---------|---------------|
| `255604002` | Mild | `mild` |
| `6736007` | Moderate | `moderate` |
| `24484000` | Severe | `severe` |

**Severity Inheritance Rules:**
1. If severity exists on reaction observation → use for that reaction
2. If severity exists only at allergy observation level → apply to all reactions
3. Reaction-level severity takes precedence

### Abatement Extension

When the allergy has resolved, `effectiveTime/high` maps to an extension:

**C-CDA:**
```xml
<effectiveTime>
  <low value="20100301"/>
  <high value="20150615"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "onsetDateTime": "2010-03-01",
  "extension": [{
    "url": "http://hl7.org/fhir/StructureDefinition/allergyintolerance-abatement",
    "valueDateTime": "2015-06-15"
  }],
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
      "code": "resolved"
    }]
  }
}
```

**Note:** Do NOT map `effectiveTime/high` to onset period. It represents abatement, not onset end.

### No Known Allergies

**C-CDA (negated):**
```xml
<observation classCode="OBS" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
  <value xsi:type="CD" code="419199007" codeSystem="2.16.840.1.113883.6.96"
         displayName="Allergy to substance"/>
  <participant typeCode="CSM">
    <participantRole classCode="MANU">
      <playingEntity classCode="MMAT">
        <code nullFlavor="NA"/>
      </playingEntity>
    </participantRole>
  </participant>
</observation>
```

**FHIR Options:**

1. **Use negated concept code:**
```json
{
  "resourceType": "AllergyIntolerance",
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
      "code": "active"
    }]
  },
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
      "code": "confirmed"
    }]
  },
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "716186003",
      "display": "No known allergy"
    }]
  },
  "patient": {"reference": "Patient/example"}
}
```

2. **Use substanceExposureRisk extension:**
```json
{
  "extension": [{
    "url": "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk",
    "extension": [
      {
        "url": "substance",
        "valueCodeableConcept": {
          "coding": [{
            "system": "http://snomed.info/sct",
            "code": "419199007",
            "display": "Allergy to substance"
          }]
        }
      },
      {
        "url": "exposureRisk",
        "valueCodeableConcept": {
          "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/allerg-intol-substance-exp-risk",
            "code": "no-known-reaction-risk",
            "display": "No Known Reaction Risk"
          }]
        }
      }
    ]
  }]
}
```

**No Known Allergy Codes (SNOMED):**

| Code | Display |
|------|---------|
| `716186003` | No known allergy |
| `409137002` | No known drug allergy |
| `429625007` | No known food allergy |
| `428607008` | No known environmental allergy |

### Author and Provenance

**Rules:**
- Latest CDA author → `AllergyIntolerance.recorder`
- Earliest `author/time` → `AllergyIntolerance.recordedDate`
- All authors → Provenance resource

**FHIR:**
```json
{
  "recorder": {
    "reference": "Practitioner/practitioner-example"
  },
  "recordedDate": "2010-03-01"
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `clinicalStatus` | Allergy Status Observation | Create nested observation |
| `type` | Allergy Observation `value` | Reverse type ConceptMap |
| `category` | Allergy Observation `value` | Combined with type |
| `criticality` | Criticality Observation | Create nested observation |
| `code` | `participant/playingEntity/code` | CodeableConcept → CD |
| `onsetDateTime` | `effectiveTime/low` | Date format conversion |
| `extension:abatement` | `effectiveTime/high` | Date format conversion |
| `reaction.manifestation` | Reaction Observation `value` | Create nested observation |
| `reaction.severity` | Severity Observation `value` | Create nested observation |
| `recorder` | `author` | Create author participation |
| `recordedDate` | `author/time` | Date format conversion |
| `note` | Comment Activity | Create nested act |

### FHIR Category to CDA Value

| FHIR type | FHIR category | C-CDA SNOMED Code |
|-----------|---------------|-------------------|
| `allergy` | `medication` | `416098002` (Drug allergy) |
| `intolerance` | `medication` | `59037007` (Drug intolerance) |
| `allergy` | `food` | `414285001` (Food allergy) |
| `intolerance` | `food` | `235719002` (Food intolerance) |
| `allergy` | `environment` | `426232007` (Environmental allergy) |
| `allergy` | (other) | `419199007` (Allergy to substance) |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
  <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>ALLERGIES AND ADVERSE REACTIONS</title>
  <entry typeCode="DRIV">
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
      <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
      <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
      <statusCode code="active"/>
      <effectiveTime><low value="20100301"/></effectiveTime>
      <author>
        <time value="20100301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
      <entryRelationship typeCode="SUBJ">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
          <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <statusCode code="completed"/>
          <effectiveTime><low value="20100301"/></effectiveTime>
          <value xsi:type="CD" code="416098002" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Drug allergy"/>
          <participant typeCode="CSM">
            <participantRole classCode="MANU">
              <playingEntity classCode="MMAT">
                <code code="70618" codeSystem="2.16.840.1.113883.6.88"
                      displayName="Penicillin V">
                  <translation code="7980" codeSystem="2.16.840.1.113883.6.88"
                               displayName="Penicillin"/>
                </code>
              </playingEntity>
            </participantRole>
          </participant>
          <entryRelationship typeCode="MFST" inversionInd="true">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
              <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
              <statusCode code="completed"/>
              <value xsi:type="CD" code="247472004" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Hives"/>
              <entryRelationship typeCode="SUBJ" inversionInd="true">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.8"/>
                  <code code="SEV" codeSystem="2.16.840.1.113883.5.4"/>
                  <value xsi:type="CD" code="6736007" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Moderate"/>
                </observation>
              </entryRelationship>
            </observation>
          </entryRelationship>
          <entryRelationship typeCode="REFR">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.28"/>
              <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"/>
              <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Active"/>
            </observation>
          </entryRelationship>
          <entryRelationship typeCode="SUBJ" inversionInd="true">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.145"/>
              <code code="82606-5" codeSystem="2.16.840.1.113883.6.1"/>
              <value xsi:type="CD" code="CRITH" codeSystem="2.16.840.1.113883.5.1063"
                     displayName="High Criticality"/>
            </observation>
          </entryRelationship>
        </observation>
      </entryRelationship>
    </act>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "AllergyIntolerance",
  "id": "allergy-penicillin",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:4adc1020-7b14-11db-9fe1-0800200c9a66"
  }],
  "clinicalStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
      "code": "active",
      "display": "Active"
    }]
  },
  "verificationStatus": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
      "code": "confirmed"
    }]
  },
  "type": "allergy",
  "category": ["medication"],
  "criticality": "high",
  "code": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "70618",
        "display": "Penicillin V"
      },
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "7980",
        "display": "Penicillin"
      }
    ],
    "text": "Penicillin"
  },
  "patient": {
    "reference": "Patient/patient-example"
  },
  "onsetDateTime": "2010-03-01",
  "recordedDate": "2010-03-01",
  "recorder": {
    "reference": "Practitioner/practitioner-example"
  },
  "reaction": [{
    "manifestation": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "247472004",
        "display": "Hives"
      }]
    }],
    "severity": "moderate"
  }]
}
```

## References

- [C-CDA on FHIR Allergies Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-allergies.html)
- [US Core AllergyIntolerance Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance)
- [C-CDA Allergy Concern Act](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.30.html)
- [C-CDA Allergy Intolerance Observation](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.7.html)
