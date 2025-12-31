# Medication Mapping: C-CDA Medication Information ↔ FHIR Medication

This document provides detailed mapping guidance between C-CDA Medication Information (Manufactured Product) and FHIR `Medication` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Medication Information (`2.16.840.1.113883.10.20.22.4.23`) | `Medication` |
| Located in: `consumable/manufacturedProduct` | Referenced by: MedicationRequest, MedicationDispense, etc. |
| Parent: Medication Activity, Medication Dispense, Medication Supply Order | US Core Profile: us-core-medication |

## When to Create a Medication Resource

The FHIR Medication resource should be created when any of the following conditions apply:

1. **Manufacturer Information Present:** C-CDA includes `manufacturerOrganization`
2. **Batch Information Present:** C-CDA includes `lotNumberText` or `expirationTime`
3. **Drug Vehicle Present:** Parent `substanceAdministration` has `participant[@typeCode="CSM"]` (drug vehicle/diluent)
4. **Form Information Present:** Parent `substanceAdministration` has `administrationUnitCode`
5. **Multiple Codes Present:** C-CDA includes translations (RxNorm + NDC, etc.)

**Otherwise:** Use `medicationCodeableConcept` inline in MedicationRequest/MedicationDispense for simple cases with just a medication code.

**Important:** Only one of `medicationCodeableConcept` or `medicationReference` may be populated in FHIR.

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `manufacturedProduct/id` | `Medication.identifier` | ID → Identifier |
| `manufacturedMaterial/code` | `Medication.code` | CodeableConcept |
| `manufacturedMaterial/code/@code` | `Medication.code.coding[0].code` | String |
| `manufacturedMaterial/code/@codeSystem` | `Medication.code.coding[0].system` | [OID to URI](#code-system-mapping) |
| `manufacturedMaterial/code/@displayName` | `Medication.code.coding[0].display` | String |
| `manufacturedMaterial/code/originalText` | `Medication.code.text` | Extract text |
| `manufacturedMaterial/code/translation` | `Medication.code.coding[1..*]` | Additional codings |
| `manufacturedMaterial/name` | `Medication.code.text` (if no originalText) | String |
| `manufacturedMaterial/lotNumberText` | `Medication.batch.lotNumber` | String |
| `manufacturedMaterial/sdtc:expirationTime` | `Medication.batch.expirationDate` | DateTime (SDTC extension, STU5+ only) |
| `manufacturerOrganization/name` | `Medication.manufacturer.display` | String |
| `manufacturerOrganization` (full) | `Medication.manufacturer` | Reference(Organization) |
| `substanceAdministration/administrationUnitCode` | `Medication.form` | CodeableConcept |
| `substanceAdministration/participant[@typeCode="CSM"]` | `Medication.ingredient` | [Drug Vehicle Mapping](#drug-vehicle-mapping) |

### Code System Mapping

C-CDA uses OIDs for code systems, while FHIR uses URIs. The following table shows the conversion:

| C-CDA Code System OID | FHIR System URI | Name |
|----------------------|-----------------|------|
| 2.16.840.1.113883.6.88 | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | NDC |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT |
| 2.16.840.1.113883.3.26.1.1 | `http://ncimeta.nci.nih.gov` | NCI Thesaurus |

### Medication Code Mapping

#### Simple Code (RxNorm)

**C-CDA:**
```xml
<manufacturedProduct classCode="MANU">
  <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
  <manufacturedMaterial>
    <code code="197361" codeSystem="2.16.840.1.113883.6.88"
          codeSystemName="RxNorm"
          displayName="Lisinopril 10 MG Oral Tablet">
      <originalText>
        <reference value="#med1"/>
      </originalText>
    </code>
  </manufacturedMaterial>
</manufacturedProduct>
```

**FHIR:**
```json
{
  "resourceType": "Medication",
  "id": "medication-197361",
  "code": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "197361",
      "display": "Lisinopril 10 MG Oral Tablet"
    }],
    "text": "Lisinopril 10 MG Oral Tablet"
  }
}
```

#### Multiple Codes (RxNorm + NDC)

**C-CDA:**
```xml
<manufacturedMaterial>
  <code code="197361" codeSystem="2.16.840.1.113883.6.88"
        codeSystemName="RxNorm"
        displayName="Lisinopril 10 MG Oral Tablet">
    <originalText>
      <reference value="#med1"/>
    </originalText>
    <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
                 codeSystemName="NDC" displayName="Lisinopril 10mg Tab"/>
  </code>
</manufacturedMaterial>
```

**FHIR:**
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

#### Text-Only (Compounded Medications)

**C-CDA:**
```xml
<manufacturedMaterial>
  <code nullFlavor="OTH">
    <originalText>Ibuprofen 10% Topical Gel (Compounded)</originalText>
  </code>
  <name>Ibuprofen 10% Topical Gel</name>
</manufacturedMaterial>
```

**FHIR:**
```json
{
  "code": {
    "text": "Ibuprofen 10% Topical Gel (Compounded)"
  }
}
```

**Note:** US Core allows text-only codes when coded values are unavailable, which is particularly important for compounded medications.

### Manufacturer Mapping

#### Manufacturer Name Only

**C-CDA:**
```xml
<manufacturerOrganization>
  <name>Watson Pharmaceuticals Inc</name>
</manufacturerOrganization>
```

**FHIR:**
```json
{
  "manufacturer": {
    "display": "Watson Pharmaceuticals Inc"
  }
}
```

#### Full Manufacturer with Organization Reference

**C-CDA:**
```xml
<manufacturerOrganization>
  <id root="2.16.840.1.113883.4.6" extension="123456789"/>
  <name>Watson Pharmaceuticals Inc</name>
  <telecom value="tel:+1-800-272-5525"/>
  <addr>
    <streetAddressLine>311 Bonnie Circle</streetAddressLine>
    <city>Corona</city>
    <state>CA</state>
    <postalCode>92880</postalCode>
  </addr>
</manufacturerOrganization>
```

**FHIR (Medication):**
```json
{
  "manufacturer": {
    "reference": "Organization/watson-pharma",
    "display": "Watson Pharmaceuticals Inc"
  }
}
```

**FHIR (Organization):**
```json
{
  "resourceType": "Organization",
  "id": "watson-pharma",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.4.6",
    "value": "123456789"
  }],
  "name": "Watson Pharmaceuticals Inc",
  "telecom": [{
    "system": "phone",
    "value": "+1-800-272-5525"
  }],
  "address": [{
    "line": ["311 Bonnie Circle"],
    "city": "Corona",
    "state": "CA",
    "postalCode": "92880"
  }]
}
```

### Form Mapping

The medication form comes from the parent `substanceAdministration/administrationUnitCode`, not from the manufacturedProduct itself.

**C-CDA:**
```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
  <administrationUnitCode code="C48542" codeSystem="2.16.840.1.113883.3.26.1.1"
                          displayName="Tablet"/>
  <consumable>
    <manufacturedProduct>
      <!-- ... -->
    </manufacturedProduct>
  </consumable>
</substanceAdministration>
```

**FHIR:**
```json
{
  "form": {
    "coding": [{
      "system": "http://ncimeta.nci.nih.gov",
      "code": "C48542",
      "display": "Tablet"
    }]
  }
}
```

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

### Batch Information Mapping

**C-CDA (with SDTC extension - STU5+):**
```xml
<manufacturedMaterial>
  <code code="197361" codeSystem="2.16.840.1.113883.6.88"
        displayName="Lisinopril 10 MG Oral Tablet"/>
  <lotNumberText>LOT-987654</lotNumberText>
  <sdtc:expirationTime value="20251231" xmlns:sdtc="urn:hl7-org:sdtc"/>
</manufacturedMaterial>
```

**C-CDA R2.1 (lot number only):**
```xml
<manufacturedMaterial>
  <code code="197361" codeSystem="2.16.840.1.113883.6.88"
        displayName="Lisinopril 10 MG Oral Tablet"/>
  <lotNumberText>LOT-987654</lotNumberText>
</manufacturedMaterial>
```

**FHIR (from STU5+ with expiration):**
```json
{
  "batch": {
    "lotNumber": "LOT-987654",
    "expirationDate": "2025-12-31"
  }
}
```

**FHIR (from R2.1 without expiration):**
```json
{
  "batch": {
    "lotNumber": "LOT-987654"
  }
}
```

**Note:** The `sdtc:expirationTime` element is an SDTC extension only available in C-CDA STU5 and later. C-CDA R2.1 documents should only use `lotNumberText`.

### Drug Vehicle Mapping

Drug vehicles (diluents, solvents) in C-CDA are represented as `participant` elements with `@typeCode="CSM"` (consumable). These map to inactive ingredients in FHIR.

**C-CDA:**
```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
  <!-- ... medication details ... -->

  <consumable>
    <manufacturedProduct>
      <!-- Primary medication -->
    </manufacturedProduct>
  </consumable>

  <!-- Drug Vehicle -->
  <participant typeCode="CSM">
    <participantRole classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.24"/>
      <code code="412307009" codeSystem="2.16.840.1.113883.6.96"
            displayName="Drug vehicle"/>
      <playingEntity classCode="MMAT">
        <code code="324049" codeSystem="2.16.840.1.113883.6.88"
              displayName="Normal saline"/>
        <name>0.9% Sodium Chloride</name>
      </playingEntity>
    </participantRole>
  </participant>
</substanceAdministration>
```

**FHIR:**
```json
{
  "ingredient": [{
    "itemCodeableConcept": {
      "coding": [{
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "324049",
        "display": "Normal saline"
      }],
      "text": "0.9% Sodium Chloride"
    },
    "isActive": false
  }]
}
```

**Note:** Drug vehicles are marked with `isActive: false` to distinguish them from active pharmaceutical ingredients.

### Identifier Mapping

**C-CDA:**
```xml
<manufacturedProduct classCode="MANU">
  <id root="2.16.840.1.113883.3.3489.1.1" extension="MED-12345"/>
  <manufacturedMaterial>
    <!-- ... -->
  </manufacturedMaterial>
</manufacturedProduct>
```

**FHIR:**
```json
{
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.3.3489.1.1",
    "value": "MED-12345"
  }]
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Medication.identifier` | `manufacturedProduct/id` | Identifier → II |
| `Medication.code` | `manufacturedMaterial/code` | CodeableConcept → CE |
| `Medication.code.coding[0]` | Primary code | First coding is primary |
| `Medication.code.coding[1..*]` | `code/translation` | Additional codings |
| `Medication.code.text` | `code/originalText` or `name` | Text representation |
| `Medication.manufacturer.display` | `manufacturerOrganization/name` | String |
| `Medication.form` | `administrationUnitCode` (in parent) | Goes in substanceAdministration |
| `Medication.batch.lotNumber` | `manufacturedMaterial/lotNumberText` | String |
| `Medication.batch.expirationDate` | `manufacturedMaterial/sdtc:expirationTime` | DateTime → TS (SDTC extension, STU5+ only) |
| `Medication.ingredient[isActive=false]` | `participant[@typeCode="CSM"]` | Drug vehicle |

### Code System Reverse Mapping

| FHIR System URI | C-CDA Code System OID |
|----------------|----------------------|
| `http://www.nlm.nih.gov/research/umls/rxnorm` | 2.16.840.1.113883.6.88 |
| `http://hl7.org/fhir/sid/ndc` | 2.16.840.1.113883.6.69 |
| `http://snomed.info/sct` | 2.16.840.1.113883.6.96 |
| `http://ncimeta.nci.nih.gov` | 2.16.840.1.113883.3.26.1.1 |

## Complete Example: Standard Medication

### C-CDA Input

```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
  <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
  <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
  <statusCode code="active"/>

  <!-- Dosing details... -->
  <administrationUnitCode code="C48542" codeSystem="2.16.840.1.113883.3.26.1.1"
                          displayName="Tablet"/>

  <consumable>
    <manufacturedProduct classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
      <id root="2.16.840.1.113883.3.3489.1.1" extension="MED-197361"/>
      <manufacturedMaterial>
        <code code="197361" codeSystem="2.16.840.1.113883.6.88"
              codeSystemName="RxNorm"
              displayName="Lisinopril 10 MG Oral Tablet">
          <originalText>
            <reference value="#med1"/>
          </originalText>
          <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
                       codeSystemName="NDC" displayName="Lisinopril 10mg Tab"/>
        </code>
        <name>Lisinopril 10mg Tablets</name>
        <lotNumberText>LOT-987654</lotNumberText>
        <sdtc:expirationTime value="20251231" xmlns:sdtc="urn:hl7-org:sdtc"/>
      </manufacturedMaterial>
      <manufacturerOrganization>
        <name>Watson Pharmaceuticals Inc</name>
      </manufacturerOrganization>
    </manufacturedProduct>
  </consumable>
</substanceAdministration>
```

### FHIR Output

```json
{
  "resourceType": "Medication",
  "id": "medication-197361",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication"
    ]
  },
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.3.3489.1.1",
    "value": "MED-197361"
  }],
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
  "manufacturer": {
    "display": "Watson Pharmaceuticals Inc"
  },
  "form": {
    "coding": [{
      "system": "http://ncimeta.nci.nih.gov",
      "code": "C48542",
      "display": "Tablet"
    }]
  },
  "batch": {
    "lotNumber": "LOT-987654",
    "expirationDate": "2025-12-31"
  }
}
```

**MedicationRequest Reference:**
```json
{
  "resourceType": "MedicationRequest",
  "medicationReference": {
    "reference": "Medication/medication-197361",
    "display": "Lisinopril 10 MG Oral Tablet"
  }
}
```

## Complete Example: IV Medication with Drug Vehicle

### C-CDA Input

```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
  <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
  <statusCode code="active"/>
  <routeCode code="C38276" codeSystem="2.16.840.1.113883.3.26.1.1"
             displayName="Intravenous"/>
  <doseQuantity value="100" unit="mg"/>

  <consumable>
    <manufacturedProduct classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
      <manufacturedMaterial>
        <code code="1049502" codeSystem="2.16.840.1.113883.6.88"
              codeSystemName="RxNorm"
              displayName="Vancomycin 100 MG/ML Injectable Solution"/>
      </manufacturedMaterial>
    </manufacturedProduct>
  </consumable>

  <!-- Drug Vehicle (Diluent) -->
  <participant typeCode="CSM">
    <participantRole classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.24"/>
      <code code="412307009" codeSystem="2.16.840.1.113883.6.96"
            displayName="Drug vehicle"/>
      <playingEntity classCode="MMAT">
        <code code="313002" codeSystem="2.16.840.1.113883.6.88"
              displayName="Sodium Chloride 0.9% injectable solution"/>
        <name>Normal Saline 0.9%</name>
      </playingEntity>
    </participantRole>
  </participant>
</substanceAdministration>
```

### FHIR Output

```json
{
  "resourceType": "Medication",
  "id": "medication-vancomycin-iv",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication"
    ]
  },
  "code": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "1049502",
      "display": "Vancomycin 100 MG/ML Injectable Solution"
    }],
    "text": "Vancomycin 100 MG/ML Injectable Solution"
  },
  "ingredient": [{
    "itemCodeableConcept": {
      "coding": [{
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "313002",
        "display": "Sodium Chloride 0.9% injectable solution"
      }],
      "text": "Normal Saline 0.9%"
    },
    "isActive": false
  }]
}
```

## Decision Tree: When to Create Medication Resource

```
Does the C-CDA manufacturedProduct contain:
├─ manufacturerOrganization? ──────────────────────► Create Medication resource
├─ lotNumberText or expirationTime? ───────────────► Create Medication resource
├─ Parent has participant[@typeCode="CSM"]? ───────► Create Medication resource
├─ Parent has administrationUnitCode? ─────────────► Create Medication resource
├─ Multiple code/translation elements? ────────────► Create Medication resource
└─ Only manufacturedMaterial/code (single)? ───────► Use medicationCodeableConcept inline
```

## Implementation Notes

### C-CDA Version Compatibility

**SDTC Extensions:**
- `sdtc:expirationTime` is **only available in C-CDA STU5 and later versions**
- **NOT available in C-CDA R2.1**
- When processing C-CDA R2.1 documents, only `lotNumberText` is available for batch tracking
- When processing C-CDA STU5+ documents, both `lotNumberText` and `sdtc:expirationTime` may be present
- SDTC namespace must be declared: `xmlns:sdtc="urn:hl7-org:sdtc"`

**Recommendation:** Converters should gracefully handle both versions:
```python
# Check for both forms
lot_number = manufactured_material.lot_number_text
expiration = getattr(manufactured_material, 'sdtc_expiration_time', None)

if lot_number or expiration:
    medication["batch"] = {}
    if lot_number:
        medication["batch"]["lotNumber"] = lot_number
    if expiration:
        medication["batch"]["expirationDate"] = convert_date(expiration)
```

### US Core Compliance

1. **code is mandatory** (1..1) in US Core Medication profile
2. **Extensible binding** to Medication Clinical Drug value set
3. **Text-only codes allowed** when coded values unavailable
4. **NDC codes recommended** as supplementary coding to RxNorm

### RxNorm Best Practices

1. **Prefer pre-coordinated codes:** Use SCD, SBD, GPCK, or BPCK term types
2. **SCD format:** "Ingredient Strength DoseForm" (e.g., "Lisinopril 10 MG Oral Tablet")
3. **Include NDC as translation** when available for precise product identification
4. **Use current RxNorm release** for 2025

### Compounded Medications

1. **Use text-only code** when no standard code exists
2. **Set code/@nullFlavor="OTH"** in C-CDA
3. **Include originalText** with full medication description
4. **Consider ingredient breakdown** if recipe is available

### Drug Vehicles

1. **Map to Medication.ingredient** with isActive=false
2. **Common for IV medications** mixed with saline, D5W, etc.
3. **Participant typeCode="CSM"** indicates consumable (vehicle)
4. **Template ID** 2.16.840.1.113883.10.20.22.4.24 identifies drug vehicle

## Common Mapping Scenarios

### Scenario 1: Simple Oral Medication (Inline Code)

**Use:** `medicationCodeableConcept` in MedicationRequest (no Medication resource needed)

**When:**
- Only medication code present
- No manufacturer, batch, or form information
- No drug vehicle

### Scenario 2: Medication with Manufacturer

**Use:** Medication resource with `manufacturer` element

**When:**
- manufacturerOrganization present in C-CDA

### Scenario 3: IV Medication with Diluent

**Use:** Medication resource with `ingredient` array

**When:**
- participant[@typeCode="CSM"] present (drug vehicle)

### Scenario 4: Compounded Medication

**Use:** Medication resource with text-only code

**When:**
- No standard code available
- Custom pharmacy preparation

## References

- [C-CDA on FHIR Medications Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html)
- [US Core Medication Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication)
- [FHIR R4B Medication Resource](https://hl7.org/fhir/R4B/medication.html)
- [C-CDA Medication Information Template](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.23.html)
- [C-CDA R5.0 Medication Information](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationInformation.html)
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/)
- [RxNorm Term Types](https://www.nlm.nih.gov/research/umls/rxnorm/docs/appendix5.html)
- [Medication Clinical Drug Value Set](https://vsac.nlm.nih.gov/valueset/2.16.840.1.113762.1.4.1010.4/expansion)
- [C-CDA Examples - Medications](https://github.com/HL7/C-CDA-Examples/tree/master/Medications)
