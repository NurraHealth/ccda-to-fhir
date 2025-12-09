# FHIR R4B: AllergyIntolerance Resource

## Overview

The AllergyIntolerance resource documents a clinical assessment of a propensity, or potential risk, for an individual to have an adverse reaction upon future exposure to a specified substance or class of substance. It represents the "risk of harmful or undesirable physiological response which is specific to an individual and associated with exposure to a substance."

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | AllergyIntolerance |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Patient Care |
| URL | https://hl7.org/fhir/R4B/allergyintolerance.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance |

## Scope and Usage

The resource documents a clinical assessment of an allergy or intolerance—a propensity, or a potential risk to an individual, to have an adverse reaction on future exposure to the specified substance, or class of substance. It supports:
- Direct clinical care and managed adverse reaction lists
- Information exchange between systems
- Adverse reaction reporting
- Computerized clinical decision support

**Substance Categories Include:**
- Therapeutic substances (medications)
- Food substances
- Materials from plants and animals
- Insect venoms

## Boundaries and Relationships

**This resource should NOT be used for:**
- Adverse events (use AdverseEvent resource)
- Clinical process failures or incorrect administration
- Recording alerts (use Flag or DetectedIssue)
- Reactions triggered by physical stimuli (light, heat, cold) - use Condition instead
- Failed therapy documentation

**Related Resources:**
- **RiskAssessment:** Describes general risks, not substance-specific propensity
- **Immunization.reaction:** May indicate allergy; requires separate AllergyIntolerance record
- **AdverseEvent, DiagnosticReport, FamilyMemberHistory, MedicationRequest, NutritionOrder:** Cross-referenced resources

## JSON Structure

```json
{
  "resourceType": "AllergyIntolerance",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/allergy",
      "value": "4adc1020-7b14-11db-9fe1-0800200c9a66"
    }
  ],
  "clinicalStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
        "code": "active",
        "display": "Active"
      }
    ]
  },
  "verificationStatus": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
        "code": "confirmed",
        "display": "Confirmed"
      }
    ]
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
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "onsetDateTime": "2010-03-01",
  "recordedDate": "2010-03-01",
  "recorder": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "asserter": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "lastOccurrence": "2010-03-01",
  "note": [
    {
      "text": "Patient reports severe reaction to penicillin family of antibiotics"
    }
  ],
  "reaction": [
    {
      "substance": {
        "coding": [
          {
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "70618",
            "display": "Penicillin V"
          }
        ]
      },
      "manifestation": [
        {
          "coding": [
            {
              "system": "http://snomed.info/sct",
              "code": "247472004",
              "display": "Hives"
            }
          ]
        }
      ],
      "description": "Hives developed within 30 minutes of taking medication",
      "onset": "2010-03-01",
      "severity": "moderate",
      "exposureRoute": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "26643006",
            "display": "Oral route"
          }
        ]
      },
      "note": [
        {
          "text": "Resolved after treatment with antihistamines"
        }
      ]
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this allergy intolerance record.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### clinicalStatus (0..1)

The clinical status of the allergy or intolerance. This is a **modifier element**.

| Type | Description |
|------|-------------|
| CodeableConcept | active \| inactive \| resolved |

**Value Set:** http://hl7.org/fhir/ValueSet/allergyintolerance-clinical (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| active | Active | The allergy is currently active |
| inactive | Inactive | The allergy is inactive but not resolved |
| resolved | Resolved | The allergy has been resolved |

**System:** `http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical`

**Summary Element:** Yes

### verificationStatus (0..1)

Assertion about certainty of the propensity. This is a **modifier element**.

| Type | Description |
|------|-------------|
| CodeableConcept | unconfirmed \| presumed \| confirmed \| refuted \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/allergyintolerance-verification (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| unconfirmed | Unconfirmed | Low level of certainty |
| presumed | Presumed | Assumed to be allergy based on evidence |
| confirmed | Confirmed | High level of certainty |
| refuted | Refuted | Determined to be not an allergy |
| entered-in-error | Entered in Error | Record was created in error |

**System:** `http://terminology.hl7.org/CodeSystem/allergyintolerance-verification`

**Summary Element:** Yes

**Implementation Note:** When uncertainty exists about causative substance, use verificationStatus. Multiple possible substances should each have separate AllergyIntolerance instances set to 'unconfirmed' for clinical decision support.

### type (0..1)

Identification of the underlying physiological mechanism for the reaction risk.

| Type | Values |
|------|--------|
| CodeableConcept | allergy \| intolerance |

**Value Set:** http://hl7.org/fhir/ValueSet/allergy-intolerance-type (Preferred binding)

| Code | Display | Definition |
|------|---------|------------|
| allergy | Allergy | Immune-mediated reaction (hypersensitivity reaction type I-IV) |
| intolerance | Intolerance | Non-immune-mediated reaction (pharmacologic, metabolic, or idiosyncratic) |

**Summary Element:** Yes

**Implementation Note:** Clinical practice may blur these distinctions; omit type element if determination is impossible.

### category (0..*)

Category of the identified substance.

| Type | Values |
|------|--------|
| code[] | food \| medication \| environment \| biologic |

| Code | Display | Definition |
|------|---------|------------|
| food | Food | Dietary substance |
| medication | Medication | Drug or medicament |
| environment | Environment | Environmental substances (dust, pollen, etc.) |
| biologic | Biologic | Biological substances (vaccines, blood products) |

### criticality (0..1)

Estimate of potential clinical harm, or seriousness, from future exposure.

| Type | Values |
|------|--------|
| code | low \| high \| unable-to-assess |

**Value Set:** http://hl7.org/fhir/ValueSet/allergy-intolerance-criticality (Required binding)

| Code | Display | Definition |
|------|---------|------------|
| low | Low Risk | Unlikely life-threatening or permanent serious organ damage |
| high | High Risk | Likely life-threatening or permanent serious organ damage |
| unable-to-assess | Unable to Assess | Unable to determine criticality with available information |

**Summary Element:** Yes

**Implementation Note:** Default to 'Low Risk' unless clinical assessment indicates higher risk (e.g., following life-threatening anaphylaxis).

### code (0..1)

Code for allergy or intolerance statement (positive or negated/excluded).

| Type | Description |
|------|-------------|
| CodeableConcept | Code for allergen or class |

**Value Set:** http://hl7.org/fhir/ValueSet/allergyintolerance-code (Example binding)

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| `http://snomed.info/sct` | SNOMED CT |
| `http://hl7.org/fhir/sid/ndc` | NDC |

**Summary Element:** Yes

**Implementation Note:** Can record either a class (e.g., penicillins) or specific substance (e.g., amoxicillin), with exact substance identified per exposure basis in reaction.substance.

### patient (1..1)

The patient who has the allergy or intolerance.

| Type | Description |
|------|-------------|
| Reference(Patient) | Required reference to patient |

### encounter (0..1)

The encounter when the allergy was recorded.

| Type | Description |
|------|-------------|
| Reference(Encounter) | Associated encounter |

### onset[x] (0..1)

When the allergy was identified.

| Element | Type | Description |
|---------|------|-------------|
| onsetDateTime | dateTime | Date/time of onset |
| onsetAge | Age | Age when allergy identified |
| onsetPeriod | Period | Period of onset |
| onsetRange | Range | Range of onset |
| onsetString | string | Textual onset description |

### recordedDate (0..1)

| Type | Description |
|------|-------------|
| dateTime | Date record was first recorded |

### recorder (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Patient \| RelatedPerson) | Who recorded the allergy |

### asserter (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| RelatedPerson \| Practitioner \| PractitionerRole) | Source of information |

### lastOccurrence (0..1)

| Type | Description |
|------|-------------|
| dateTime | Date of last known occurrence of reaction |

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional narrative about the allergy |

### reaction (0..*)

Details of each adverse reaction event.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| substance | CodeableConcept | 0..1 | Specific substance causing reaction |
| manifestation | CodeableConcept[] | 1..* | Clinical symptoms/signs (Required) |
| description | string | 0..1 | Description of the reaction |
| onset | dateTime | 0..1 | When reaction occurred |
| severity | code | 0..1 | mild \| moderate \| severe |
| exposureRoute | CodeableConcept | 0..1 | How substance was encountered |
| note | Annotation[] | 0..* | Additional notes |

### reaction.manifestation

The clinical symptoms or signs of the reaction.

**Common Manifestation Codes (SNOMED CT):**
| Code | Display |
|------|---------|
| 247472004 | Hives (urticaria) |
| 422587007 | Nausea |
| 422400008 | Vomiting |
| 271807003 | Skin rash |
| 267036007 | Dyspnea |
| 39579001 | Anaphylaxis |
| 25064002 | Headache |
| 62315008 | Diarrhea |
| 418290006 | Itching |
| 56018004 | Wheezing |

### reaction.severity

The clinical severity of the reaction.

| Code | Display | Definition |
|------|---------|------------|
| mild | Mild | Causes mild symptoms |
| moderate | Moderate | Causes moderate symptoms |
| severe | Severe | Causes severe symptoms |

## Special Cases

### No Known Allergies (NKDA)

When documenting that a patient has no known allergies:

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
  "patient": {
    "reference": "Patient/example"
  }
}
```

**No Known Allergy Codes (SNOMED):**
| Code | Display |
|------|---------|
| 716186003 | No known allergy |
| 409137002 | No known drug allergy |
| 429625007 | No known food allergy |
| 428607008 | No known environmental allergy |

## US Core Conformance Requirements

For US Core AllergyIntolerance profile compliance:

1. **SHALL** support `clinicalStatus`
2. **SHALL** support `verificationStatus`
3. **SHALL** support `code`
4. **SHALL** support `patient`
5. **SHOULD** support `reaction`
6. **SHOULD** support `reaction.manifestation`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| clinical-status | token | active \| inactive \| resolved |
| patient | reference | Who the allergy is for |
| code | token | Allergen code |
| date | date | Date record was recorded |
| criticality | token | low \| high \| unable-to-assess |
| type | token | allergy \| intolerance |
| category | token | food \| medication \| environment \| biologic |
| manifestation | token | Clinical symptoms/signs |
| severity | token | mild \| moderate \| severe |

## Modifier Elements

The following elements are modifier elements:
- **clinicalStatus** - Affects interpretation of the allergy status
- **verificationStatus** - Affects whether this record should be treated as valid

## Compartments

The AllergyIntolerance resource is part of the following compartments:
- Patient
- Practitioner
- RelatedPerson

## References

- FHIR R4B AllergyIntolerance: https://hl7.org/fhir/R4B/allergyintolerance.html
- US Core AllergyIntolerance: http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance
- SNOMED CT: http://snomed.info/sct
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
