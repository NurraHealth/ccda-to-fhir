# C-CDA: Allergy Intolerance Observation

## Overview

The Allergy Intolerance Observation in C-CDA documents a patient's allergy or adverse reaction to a substance. It is contained within an Allergy Concern Act which tracks the overall concern status.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.7` |
| Template Name | Allergy Intolerance Observation |
| Template Version | 2014-06-09 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/AllergyIntoleranceObservation` |
| Parent Template | SubstanceOrDeviceAllergyIntoleranceObservation |
| Container Template | Allergy Concern Act (`2.16.840.1.113883.10.20.22.4.30`) |

## Section Information

| Attribute | Value |
|-----------|-------|
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.6.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.6` |
| LOINC Code | 48765-2 |
| LOINC Display | Allergies and adverse reactions Document |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Allergies Section]
                └── entry
                    └── act [Allergy Concern Act]
                        └── entryRelationship [@typeCode='SUBJ']
                            └── observation [Allergy Intolerance Observation]
                                ├── participant [@typeCode='CSM'] (allergen)
                                └── entryRelationship [@typeCode='MFST'] (reaction)
                                    └── observation [Reaction Observation]
                                        └── entryRelationship [@typeCode='SUBJ']
                                            └── observation [Severity Observation]
```

## XML Structure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.6.1" extension="2015-08-01"/>
  <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Allergies and adverse reactions Document"/>
  <title>ALLERGIES AND ADVERSE REACTIONS</title>
  <text>
    <table>
      <thead><tr><th>Substance</th><th>Reaction</th><th>Severity</th><th>Status</th></tr></thead>
      <tbody>
        <tr>
          <td ID="allergen1">Penicillin</td>
          <td ID="reaction1">Hives</td>
          <td>Moderate</td>
          <td>Active</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <!-- Allergy Concern Act -->
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.30" extension="2015-08-01"/>
      <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
      <code code="CONC" codeSystem="2.16.840.1.113883.5.6" displayName="Concern"/>
      <!-- Concern Status: active, completed, aborted, suspended -->
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20100301"/>
      </effectiveTime>
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20100301"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <entryRelationship typeCode="SUBJ">
        <!-- Allergy Intolerance Observation -->
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.7" extension="2014-06-09"/>
          <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <statusCode code="completed"/>
          <effectiveTime>
            <low value="20100301"/>
          </effectiveTime>

          <!-- Allergy Type (value) -->
          <value xsi:type="CD" code="419199007" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Allergy to substance (disorder)">
            <originalText>
              <reference value="#allergyType1"/>
            </originalText>
          </value>

          <!-- Allergen (participant) -->
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

          <!-- Reaction (entryRelationship) -->
          <entryRelationship typeCode="MFST" inversionInd="true">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.9" extension="2014-06-09"/>
              <id root="4adc1020-7b14-11db-9fe1-0800200c9a67"/>
              <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
              <text>
                <reference value="#reaction1"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime>
                <low value="20100301"/>
              </effectiveTime>
              <value xsi:type="CD" code="247472004" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Hives">
                <originalText>
                  <reference value="#reaction1"/>
                </originalText>
              </value>

              <!-- Severity Observation -->
              <entryRelationship typeCode="SUBJ" inversionInd="true">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.8" extension="2014-06-09"/>
                  <code code="SEV" codeSystem="2.16.840.1.113883.5.4"
                        displayName="Severity Observation"/>
                  <statusCode code="completed"/>
                  <value xsi:type="CD" code="6736007" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Moderate"/>
                </observation>
              </entryRelationship>
            </observation>
          </entryRelationship>

          <!-- Allergy Status Observation (optional) -->
          <entryRelationship typeCode="REFR">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.28" extension="2019-06-20"/>
              <code code="33999-4" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Status"/>
              <statusCode code="completed"/>
              <value xsi:type="CD" code="55561003" codeSystem="2.16.840.1.113883.6.96"
                     displayName="Active"/>
            </observation>
          </entryRelationship>

          <!-- Criticality Observation (optional) -->
          <entryRelationship typeCode="SUBJ" inversionInd="true">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.145"/>
              <code code="82606-5" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Allergy or intolerance criticality"/>
              <statusCode code="completed"/>
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

## Element Details

### Allergy Concern Act (act)

The container for the allergy information, tracking the overall concern status.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.30` | Yes |
| id | Unique identifier for the concern | Yes |
| code | CONC (Concern) from ActCode | Yes |
| statusCode | active \| completed \| aborted \| suspended | Yes |
| effectiveTime/low | When concern was first noted | Yes |
| effectiveTime/high | When concern was resolved (if applicable) | No |

### Allergy Intolerance Observation (observation)

The actual allergy or intolerance information.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.7` | Yes |
| id | Unique identifier for the observation | Yes |
| code | ASSERTION from ActCode | Yes |
| statusCode | completed | Yes |
| effectiveTime/low | Onset date | No |
| value | Allergy type code (SNOMED) | Yes |

### Value (Allergy Type)

The type of allergy or intolerance reaction.

**Common SNOMED Codes:**
| Code | Display | Category |
|------|---------|----------|
| 419199007 | Allergy to substance | allergy |
| 416098002 | Drug allergy | allergy/medication |
| 414285001 | Food allergy | allergy/food |
| 426232007 | Environmental allergy | allergy/environment |
| 59037007 | Drug intolerance | intolerance |
| 235719002 | Food intolerance | intolerance |
| 420134006 | Propensity to adverse reactions | general |

### Participant (Allergen)

The substance that causes the allergic reaction. This is a **USCDI requirement** - the substance must be documented.

| Element | Path | Description |
|---------|------|-------------|
| @typeCode | participant | CSM (consumable) |
| participantRole/@classCode | participantRole | MANU (manufactured product) |
| playingEntity/@classCode | playingEntity | MMAT (manufactured material - though covers non-manufactured agents like foods) |
| playingEntity/code | playingEntity/code | Allergen code |
| playingEntity/name | playingEntity/name | Allergen name (optional) |

**Value Set Binding:** Common substances for allergy and intolerance documentation (`2.16.840.1.113762.1.4.1186.8`) - Preferred binding

**Common Allergen Code Systems:**
| OID | Name | Use |
|-----|------|-----|
| 2.16.840.1.113883.6.88 | RxNorm | Drug allergens |
| 2.16.840.1.113883.6.96 | SNOMED CT | Any allergen type |
| 2.16.840.1.113883.6.69 | NDC | Drug allergens |

### Reaction Observation

Documents the manifestation of the allergic reaction.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.9` | Yes |
| @typeCode | MFST (manifestation) | Yes |
| @inversionInd | true | Yes |
| value | Reaction manifestation (SNOMED) | Yes |

**Common Reaction Codes (SNOMED):**
| Code | Display |
|------|---------|
| 247472004 | Hives (urticaria) |
| 422587007 | Nausea |
| 422400008 | Vomiting |
| 271807003 | Skin rash |
| 267036007 | Dyspnea (breathing difficulty) |
| 39579001 | Anaphylaxis |
| 25064002 | Headache |
| 62315008 | Diarrhea |

### Severity Observation

Documents the severity of the reaction.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.8` | No |
| code | SEV from ObservationValue | Yes |
| value | Severity code (SNOMED) | Yes |

**Severity Codes (SNOMED):**
| Code | Display |
|------|---------|
| 255604002 | Mild |
| 6736007 | Moderate |
| 24484000 | Severe |
| 399166001 | Fatal |

### Allergy Status Observation

Documents whether the allergy is currently active.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.28` | No |
| code | 33999-4 (Status) from LOINC | Yes |
| value | Status code (SNOMED) | Yes |

**Status Codes (SNOMED):**
| Code | Display |
|------|---------|
| 55561003 | Active |
| 73425007 | Inactive |
| 413322009 | Resolved |

### Criticality Observation

Documents the potential clinical harm of future reactions.

| Element | Description | Required |
|---------|-------------|----------|
| templateId | `2.16.840.1.113883.10.20.22.4.145` | No |
| code | 82606-5 from LOINC | Yes |
| value | Criticality code | Yes |

**Criticality Codes:**
| Code | System | Display |
|------|--------|---------|
| CRITL | 2.16.840.1.113883.5.1063 | Low Criticality |
| CRITH | 2.16.840.1.113883.5.1063 | High Criticality |
| CRITU | 2.16.840.1.113883.5.1063 | Unable to Assess |

## Conformance Requirements

### Allergy Concern Act
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.30`
2. **SHALL** contain exactly one `id`
3. **SHALL** contain exactly one `code` with code="CONC"
4. **SHALL** contain exactly one `statusCode`
5. **SHALL** contain exactly one `effectiveTime`
6. **SHALL** contain at least one `entryRelationship` with typeCode="SUBJ"

### Allergy Intolerance Observation
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.7`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `code` with code="ASSERTION"
4. **SHALL** contain exactly one `statusCode` with code="completed"
5. **SHALL** contain exactly one `value` with xsi:type="CD"
6. **SHOULD** contain zero or one `participant` with typeCode="CSM"
7. **MAY** contain zero or more `entryRelationship` with typeCode="MFST"

## No Known Allergies

When documenting that a patient has no known allergies:

```xml
<observation classCode="OBS" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.7" extension="2014-06-09"/>
  <id root="..."/>
  <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
  <statusCode code="completed"/>
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

## Allergy Concern Act Information

The Allergy Concern Act wraps the Allergy Intolerance Observation and represents an ongoing concern on behalf of the provider. Key details:

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.30` |
| Template Version | 2015-08-01 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/AllergyConcernAct` |
| Fixed Values | classCode=ACT, moodCode=EVN, code=CONC |

**Status Constraints:**
- If statusCode = "active": effectiveTime/low is required
- If statusCode = "completed": effectiveTime/high is required

**Terminology Bindings:**
| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| statusCode | ProblemAct statusCode (VSAC) | Required |
| languageCode | All Languages | Required |
| priorityCode | ActPriority (v3) | Example |

## effectiveTime Semantics

The effectiveTime element indicates "the time at which the observation holds for the patient." For resolved allergies with unknown resolution dates, the high element must be present with `nullFlavor="UNK"`.

## Negation Indicator

The optional `@negationInd` attribute can be set to "true" to indicate the allergy was not observed (i.e., to explicitly state that a patient does NOT have an allergy to a substance).

## References

- C-CDA R2.1 Implementation Guide Section 3.5
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- SNOMED CT: http://snomed.info/sct
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
