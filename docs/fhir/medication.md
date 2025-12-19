# FHIR R4B: Medication Resource

## Overview

The Medication resource is used to identify and define a medication for the purposes of prescribing, dispensing, and administering. It represents the medication itself as a reference resource, containing details about the drug product including codes, ingredients, form, manufacturer, and packaging.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Medication |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Trial Use (Maturity Level 3) |
| Security Category | Drug |
| Responsible Work Group | Pharmacy |
| URL | https://hl7.org/fhir/R4B/medication.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication |

## Scope and Usage

**Primary Use Cases:**
- Identifying medications from established code systems (RxNorm, SNOMED CT, IDMP, local formularies)
- Documenting detailed composition of medications, especially compounded products
- Describing packaged medications with container and quantity information
- Specifying extemporaneous formulations with multiple ingredients

**Key Distinctions:**
- **Medication:** The drug product definition (reference resource)
- **MedicationRequest:** Order/prescription for the medication
- **MedicationDispense:** Fulfillment/dispensing event
- **MedicationAdministration:** Actual administration to patient
- **MedicationStatement:** Patient-reported or historical medication usage

**Workflow Notes:**
- Medication is typically referenced by other resources rather than used standalone
- Can represent both simple coded medications and complex compounded formulations
- Supports both active pharmaceutical ingredients and inactive components (vehicles)
- No direct clinical status; formulary status requires extensions

## JSON Structure

```json
{
  "resourceType": "Medication",
  "id": "medication-example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/medications",
      "value": "MED-123456"
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197361",
        "display": "Lisinopril 10 MG Oral Tablet"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "00591-3772-01",
        "display": "Lisinopril 10mg Tab"
      }
    ],
    "text": "Lisinopril 10 MG Oral Tablet"
  },
  "status": "active",
  "manufacturer": {
    "reference": "Organization/watson-pharma",
    "display": "Watson Pharmaceuticals Inc"
  },
  "form": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "385055001",
        "display": "Tablet"
      },
      {
        "system": "http://ncimeta.nci.nih.gov",
        "code": "C48542",
        "display": "Tablet"
      }
    ]
  },
  "amount": {
    "numerator": {
      "value": 30,
      "unit": "tablet",
      "system": "http://unitsofmeasure.org",
      "code": "{tbl}"
    },
    "denominator": {
      "value": 1,
      "unit": "bottle",
      "system": "http://unitsofmeasure.org",
      "code": "{bottle}"
    }
  },
  "ingredient": [
    {
      "itemCodeableConcept": {
        "coding": [
          {
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "29046",
            "display": "Lisinopril"
          }
        ]
      },
      "isActive": true,
      "strength": {
        "numerator": {
          "value": 10,
          "unit": "mg",
          "system": "http://unitsofmeasure.org",
          "code": "mg"
        },
        "denominator": {
          "value": 1,
          "unit": "tablet",
          "system": "http://unitsofmeasure.org",
          "code": "{tbl}"
        }
      }
    }
  ],
  "batch": {
    "lotNumber": "LOT-987654",
    "expirationDate": "2025-12-31"
  }
}
```

## Element Definitions

### identifier (0..*)

Business identifiers assigned to the medication.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for the identifier |
| value | string | The identifier value |

**Example:**
```json
{
  "identifier": [{
    "system": "http://hospital.example.org/medications",
    "value": "MED-123456"
  }]
}
```

### code (0..1)

Codes that identify this medication. This element is **MANDATORY (1..1)** in US Core.

| Type | Description |
|------|-------------|
| CodeableConcept | Medication code |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-codes (SNOMED CT, Example binding)
**US Core Binding:** Medication Clinical Drug (Extensible binding)

**Common Code Systems:**

| System URI | OID | Name |
|------------|-----|------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | 2.16.840.1.113883.6.88 | RxNorm |
| `http://hl7.org/fhir/sid/ndc` | 2.16.840.1.113883.6.69 | NDC (National Drug Code) |
| `http://snomed.info/sct` | 2.16.840.1.113883.6.96 | SNOMED CT |

**RxNorm Term Types (Preferred):**
- **SCD** (Semantic Clinical Drug): Generic drug with strength and form (e.g., "Lisinopril 10 MG Oral Tablet")
- **SBD** (Semantic Branded Drug): Brand drug with strength and form (e.g., "Prinivil 10 MG Oral Tablet")
- **GPCK** (Generic Pack): Package of generic drugs
- **BPCK** (Branded Pack): Package of branded drugs

**Example:**
```json
{
  "code": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "197361",
        "display": "Lisinopril 10 MG Oral Tablet"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "00591-3772-01",
        "display": "Lisinopril 10mg Tab"
      }
    ],
    "text": "Lisinopril 10 MG Oral Tablet"
  }
}
```

**US Core Note:** When codes are unavailable, text-only descriptions are acceptable. This is particularly important for compounded medications.

### status (0..1)

The status of the medication. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | active \| inactive \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-status (Required binding)

**Status Definitions:**

| Code | Display | Definition |
|------|---------|------------|
| active | Active | Medication is active for use |
| inactive | Inactive | Medication is not active for use |
| entered-in-error | Entered in Error | Record was entered in error |

**Note:** This status refers to the medication definition itself, not clinical usage. Clinical status is tracked in MedicationRequest, MedicationStatement, etc.

### manufacturer (0..1)

Organization that manufactures the medication.

| Type | Description |
|------|-------------|
| Reference(Organization) | Manufacturer organization |

**Example:**
```json
{
  "manufacturer": {
    "reference": "Organization/watson-pharma",
    "display": "Watson Pharmaceuticals Inc"
  }
}
```

### form (0..1)

Describes the form of the medication (tablet, capsule, liquid, etc.).

| Type | Description |
|------|-------------|
| CodeableConcept | Physical form of medication |

**Value Set:** http://hl7.org/fhir/ValueSet/medication-form-codes (Example binding)

**Common Form Codes (SNOMED CT):**

| Code | Display |
|------|---------|
| 385055001 | Tablet |
| 385049006 | Capsule |
| 385219001 | Solution for injection |
| 420699003 | Liquid |
| 385023001 | Oral solution |
| 385229008 | Cream |
| 385101003 | Ointment |
| 421026006 | Oral powder |
| 420692007 | Oral suspension |
| 385194003 | Chewable tablet |

**Common Form Codes (NCI Thesaurus):**

| Code | Display |
|------|---------|
| C48542 | Tablet |
| C48480 | Capsule |
| C42944 | Inhalant |
| C42953 | Solution |
| C42998 | Tablet, Extended Release |
| C48491 | Cream |
| C42966 | Ointment |
| C42986 | Syrup |
| C42905 | Spray |
| C42911 | Patch |

**Example:**
```json
{
  "form": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "385055001",
      "display": "Tablet"
    }]
  }
}
```

### amount (0..1)

Specific amount of medication in a package.

| Type | Description |
|------|-------------|
| Ratio | Numerator is medication quantity, denominator is package size |

**Example:**
```json
{
  "amount": {
    "numerator": {
      "value": 30,
      "unit": "tablet",
      "system": "http://unitsofmeasure.org",
      "code": "{tbl}"
    },
    "denominator": {
      "value": 1,
      "unit": "bottle",
      "system": "http://unitsofmeasure.org",
      "code": "{bottle}"
    }
  }
}
```

### ingredient (0..*)

Active or inactive ingredients in the medication.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| item[x] | CodeableConcept \| Reference(Substance \| Medication) | 1..1 | The ingredient substance |
| isActive | boolean | 0..1 | Whether ingredient has therapeutic effect |
| strength | Ratio | 0..1 | Quantity of ingredient per unit |

**Example (Active Ingredient):**
```json
{
  "ingredient": [{
    "itemCodeableConcept": {
      "coding": [{
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "29046",
        "display": "Lisinopril"
      }]
    },
    "isActive": true,
    "strength": {
      "numerator": {
        "value": 10,
        "unit": "mg",
        "system": "http://unitsofmeasure.org",
        "code": "mg"
      },
      "denominator": {
        "value": 1,
        "unit": "tablet",
        "system": "http://unitsofmeasure.org",
        "code": "{tbl}"
      }
    }
  }]
}
```

**Example (Inactive Ingredient - Drug Vehicle):**
```json
{
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

**Note:** Drug vehicles (diluents, solvents) should be marked with `isActive: false`.

### batch (0..1)

Information about a specific batch of medication.

| Element | Type | Description |
|---------|------|-------------|
| lotNumber | string | Identifier for the batch |
| expirationDate | dateTime | When batch expires |

**Example:**
```json
{
  "batch": {
    "lotNumber": "LOT-987654",
    "expirationDate": "2025-12-31"
  }
}
```

## US Core Conformance Requirements

For US Core Medication profile compliance:

1. **SHALL** support `code` (1..1 cardinality in US Core)
2. **Extensible Binding:** code SHALL be from Medication Clinical Drug value set if available
3. **Text Fallback:** When no code is available, text-only description is permitted
4. **NDC Codes:** Recommended as additional coding alongside RxNorm

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| code | token | Medication code |
| form | token | Physical form code |
| identifier | token | Business identifier |
| ingredient | reference | Ingredient reference |
| ingredient-code | token | Ingredient code |
| lot-number | token | Batch lot number |
| manufacturer | reference | Manufacturer organization |
| expiration-date | date | Batch expiration date |
| status | token | active \| inactive \| entered-in-error |

## Complete Example: Compounded Medication

```json
{
  "resourceType": "Medication",
  "id": "compound-ibuprofen-gel",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication"
    ]
  },
  "code": {
    "text": "Ibuprofen 10% Topical Gel (Compounded)"
  },
  "status": "active",
  "form": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "385099005",
      "display": "Gel"
    }]
  },
  "ingredient": [
    {
      "itemCodeableConcept": {
        "coding": [{
          "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
          "code": "5640",
          "display": "Ibuprofen"
        }]
      },
      "isActive": true,
      "strength": {
        "numerator": {
          "value": 10,
          "unit": "g",
          "system": "http://unitsofmeasure.org",
          "code": "g"
        },
        "denominator": {
          "value": 100,
          "unit": "g",
          "system": "http://unitsofmeasure.org",
          "code": "g"
        }
      }
    },
    {
      "itemCodeableConcept": {
        "coding": [{
          "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
          "code": "1298738",
          "display": "Carbomer 940"
        }]
      },
      "isActive": false
    }
  ]
}
```

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes whether the medication definition should be used

## Compartments

The Medication resource is not part of any defined compartments.

## Resource References

**Referenced By:**
- ActivityDefinition
- AdministrableProductDefinition
- ChargeItem
- ClinicalUseDefinition
- Immunization
- MedicationAdministration
- MedicationDispense
- MedicationKnowledge
- MedicationRequest
- MedicationStatement
- PackagedProductDefinition
- RequestOrchestration
- SupplyDelivery
- SupplyRequest

## References

- FHIR R4B Medication: https://hl7.org/fhir/R4B/medication.html
- US Core Medication Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- SNOMED CT: http://snomed.info/sct
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- Medication Clinical Drug Value Set: https://vsac.nlm.nih.gov/
