# MedicationDispense Mapping: C-CDA Medication Dispense ↔ FHIR MedicationDispense

This document provides detailed mapping guidance between C-CDA Medication Dispense and FHIR `MedicationDispense` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Medication Dispense (`2.16.840.1.113883.10.20.22.4.18`) | `MedicationDispense` |
| Parent: Medication Activity | Related: `MedicationRequest` (via authorizingPrescription) |
| moodCode: EVN (event) | status indicates completion state |
| entryRelationship typeCode: REFR | Nested within Medication Activity |

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `supply/id` | `MedicationDispense.identifier` | ID → Identifier |
| `supply/statusCode` | `MedicationDispense.status` | [Status ConceptMap](#status-mapping) |
| `supply/@moodCode` | — | Validate = "EVN" |
| `supply/effectiveTime/@value` | `MedicationDispense.whenHandedOver` | DateTime |
| `supply/effectiveTime/low` | `MedicationDispense.whenPrepared` | DateTime |
| `supply/effectiveTime/high` | `MedicationDispense.whenHandedOver` | DateTime |
| `supply/repeatNumber` | `MedicationDispense.type` | [Type Mapping](#dispense-type-mapping) |
| `supply/quantity` | `MedicationDispense.quantity` | Quantity |
| `product/manufacturedMaterial/code` | `MedicationDispense.medicationCodeableConcept` | CodeableConcept |
| `product/manufacturedProduct` (complex) | `MedicationDispense.medicationReference` | Reference(Medication) |
| `performer` | `MedicationDispense.performer.actor` + `location` | Reference(Organization/Practitioner) |
| `author` | `MedicationDispense.performer` | Reference(Practitioner) + function="packager" |
| `author/time` | `MedicationDispense.whenHandedOver` | DateTime (if not present) |
| Days Supply entry | `MedicationDispense.daysSupply` | Quantity |
| Parent Medication Activity | `MedicationDispense.authorizingPrescription` | Reference(MedicationRequest) |
| Document recordTarget | `MedicationDispense.subject` | Reference(Patient) |
| Document encounter | `MedicationDispense.context` | Reference(Encounter) |

### Status Mapping

**C-CDA:**
```xml
<statusCode code="completed"/>
```

**Status ConceptMap:**

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| `completed` | `completed` | Dispense completed and handed over |
| `active` | `in-progress` | Dispense in progress |
| `aborted` | `stopped` | Dispense was stopped |
| `cancelled` | `cancelled` | Dispense was cancelled |
| `held` | `on-hold` | Dispense temporarily suspended |
| `new` | `preparation` | Preparing to dispense |
| `nullified` | `entered-in-error` | Entered in error |

**FHIR:**
```json
{
  "status": "completed"
}
```

**Note:** Most C-CDA Medication Dispense records have `statusCode="completed"` since they document historical dispensing events.

### Dispense Type Mapping

**C-CDA:**
```xml
<repeatNumber value="1"/>
```

**Type Inference from repeatNumber:**

| C-CDA repeatNumber | FHIR type | Notes |
|--------------------|-----------|-------|
| `1` | `FF` (First Fill) | Original fill |
| `2` | `RF` (Refill) | First refill |
| `3+` | `RF` (Refill) | Subsequent refills |
| Not present | Not set | Type cannot be determined |

**FHIR:**
```json
{
  "type": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
      "code": "FF",
      "display": "First Fill"
    }]
  }
}
```

**Note:** C-CDA does not have a direct equivalent to FHIR's dispense type. The type must be inferred from `repeatNumber` or left unspecified.

### Medication Code Mapping

#### Simple (CodeableConcept)

**C-CDA:**
```xml
<product>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
    <manufacturedMaterial>
      <code code="314076" codeSystem="2.16.840.1.113883.6.88"
            displayName="Lisinopril 10 MG Oral Tablet">
        <originalText>
          <reference value="#med1"/>
        </originalText>
        <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
                     displayName="Lisinopril 10mg Tab"/>
      </code>
    </manufacturedMaterial>
  </manufacturedProduct>
</product>
```

**FHIR:**
```json
{
  "medicationCodeableConcept": {
    "coding": [
      {
        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
        "code": "314076",
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

#### Complex (Reference to Medication)

When additional medication details (form, manufacturer, ingredients) require representation:

**FHIR MedicationDispense:**
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
      "code": "314076",
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
    "display": "Watson Pharmaceuticals Inc"
  }
}
```

### Quantity Mapping

**C-CDA:**
```xml
<quantity value="30" unit="{tbl}"/>
```

**FHIR:**
```json
{
  "quantity": {
    "value": 30,
    "unit": "tablet",
    "system": "http://unitsofmeasure.org",
    "code": "{tbl}"
  }
}
```

**Unit Code Conversion:**

| C-CDA Unit | FHIR code | FHIR unit (display) |
|------------|-----------|---------------------|
| `{tbl}` | `{tbl}` | tablet |
| `{cap}` | `{cap}` | capsule |
| `mL` | `mL` | milliliter |
| `mg` | `mg` | milligram |
| `g` | `g` | gram |
| `{puff}` | `{puff}` | puff |
| `{spray}` | `{spray}` | spray |

### Days Supply Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="COMP">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.37.3.10" extension="2017-08-01"/>
    <quantity value="30" unit="d"/>
  </supply>
</entryRelationship>
```

**FHIR:**
```json
{
  "daysSupply": {
    "value": 30,
    "unit": "day",
    "system": "http://unitsofmeasure.org",
    "code": "d"
  }
}
```

### Performer Mapping

**C-CDA:**
```xml
<!-- Pharmacist/pharmacy as performer -->
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <addr>
      <streetAddressLine>123 Pharmacy Lane</streetAddressLine>
      <city>Boston</city>
      <state>MA</state>
      <postalCode>02101</postalCode>
    </addr>
    <telecom use="WP" value="tel:(555)555-1000"/>
    <assignedPerson>
      <name>
        <given>Jane</given>
        <family>Smith</family>
        <suffix>PharmD</suffix>
      </name>
    </assignedPerson>
    <representedOrganization>
      <name>Community Pharmacy</name>
    </representedOrganization>
  </assignedEntity>
</performer>

<!-- Author (pharmacist) -->
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301143000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <assignedPerson>
      <name>
        <given>Jane</given>
        <family>Smith</family>
        <suffix>PharmD</suffix>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR:**
```json
{
  "performer": [
    {
      "function": {
        "coding": [{
          "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
          "code": "packager",
          "display": "Packager"
        }]
      },
      "actor": {
        "reference": "Practitioner/pharmacist-1",
        "display": "Jane Smith, PharmD"
      }
    }
  ],
  "location": {
    "reference": "Location/pharmacy-1",
    "display": "Community Pharmacy"
  }
}
```

**Mapping Strategy:**
1. Map `performer/assignedEntity` → Create Practitioner or Organization resource
2. If `assignedPerson` present → Practitioner, otherwise → Organization
3. Map `performer/assignedEntity/representedOrganization` → Location resource (pharmacy)
4. Map `author` → Additional performer entry (often same person)
5. Set `performer.function` to "packager" or "finalchecker"

### Timing Mapping

**C-CDA (single timestamp):**
```xml
<effectiveTime value="20200301143000-0500"/>
```

**FHIR:**
```json
{
  "whenHandedOver": "2020-03-01T14:30:00-05:00"
}
```

**C-CDA (period - preparation to handover):**
```xml
<effectiveTime xsi:type="IVL_TS">
  <low value="20200301090000-0500"/>
  <high value="20200301143000-0500"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "whenPrepared": "2020-03-01T09:00:00-05:00",
  "whenHandedOver": "2020-03-01T14:30:00-05:00"
}
```

### Substitution Mapping

**C-CDA does not have a standard template for medication substitution in Medication Dispense.**

If the dispensed medication differs from the prescribed medication (different code in dispense vs parent Medication Activity), infer substitution occurred:

**FHIR:**
```json
{
  "substitution": {
    "wasSubstituted": true,
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v3-substanceAdminSubstitution",
        "code": "G",
        "display": "Generic composition"
      }]
    }
  }
}
```

**Substitution Detection Logic:**
1. Compare `Medication Dispense/product/code` with parent `Medication Activity/consumable/code`
2. If codes differ → Set `wasSubstituted = true`
3. Infer substitution type:
   - Brand to generic or vice versa → "G" (Generic composition)
   - Unknown → "E" (Equivalent)
   - Same → `wasSubstituted = false`

### Authorizing Prescription Mapping

Link to the parent Medication Activity (which maps to MedicationRequest):

**C-CDA:** (implicit parent relationship)
```xml
<substanceAdministration classCode="SBADM" moodCode="INT">
  <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
  <id root="parent-medication-activity-id"/>
  <!-- ... -->
  <entryRelationship typeCode="REFR">
    <supply classCode="SPLY" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.18"/>
      <!-- This dispense -->
    </supply>
  </entryRelationship>
</substanceAdministration>
```

**FHIR:**
```json
{
  "authorizingPrescription": [
    {
      "reference": "MedicationRequest/parent-medication-activity-id"
    }
  ]
}
```

**Mapping Strategy:**
- The parent Medication Activity maps to a MedicationRequest
- Create a reference from MedicationDispense.authorizingPrescription to that MedicationRequest
- Use the parent Medication Activity's `id` to establish the relationship

### Subject and Context Mapping

**C-CDA:** (from document level)
```xml
<ClinicalDocument>
  <!-- ... -->
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.4.1" extension="111-00-1234"/>
      <!-- Patient information -->
    </patientRole>
  </recordTarget>
  <componentOf>
    <encompassingEncounter>
      <id root="encounter-123"/>
      <!-- Encounter information -->
    </encompassingEncounter>
  </componentOf>
  <!-- ... -->
</ClinicalDocument>
```

**FHIR:**
```json
{
  "subject": {
    "reference": "Patient/patient-111-00-1234"
  },
  "context": {
    "reference": "Encounter/encounter-123"
  }
}
```

**Mapping Strategy:**
- Extract patient from document `recordTarget` → `subject`
- Extract encounter from document `componentOf/encompassingEncounter` → `context`

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `MedicationDispense.identifier` | `supply/id` | Identifier → ID |
| `MedicationDispense.status` | `supply/statusCode` | Reverse status map |
| `MedicationDispense.medicationCodeableConcept` | `product/manufacturedMaterial/code` | CodeableConcept → CE |
| `MedicationDispense.medicationReference` | `product/manufacturedProduct` | Create product |
| `MedicationDispense.subject` | Document `recordTarget` | Patient reference |
| `MedicationDispense.context` | Document `componentOf` | Encounter reference |
| `MedicationDispense.performer.actor` | `performer/assignedEntity` | Create performer |
| `MedicationDispense.location` | `performer/representedOrganization` | Pharmacy location |
| `MedicationDispense.type` | `repeatNumber` | Infer from type code |
| `MedicationDispense.quantity` | `quantity` | Quantity → PQ |
| `MedicationDispense.daysSupply` | Days Supply entry | Create nested supply |
| `MedicationDispense.whenPrepared` | `effectiveTime/low` | DateTime format |
| `MedicationDispense.whenHandedOver` | `effectiveTime/@value` or `/high` | DateTime format |
| `MedicationDispense.authorizingPrescription` | Parent Medication Activity | Create entryRelationship |
| `MedicationDispense.substitution` | Compare codes | Document if different |

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
      <id root="medication-activity-123"/>
      <statusCode code="active"/>

      <!-- Medication details -->
      <effectiveTime xsi:type="IVL_TS">
        <low value="20200301"/>
      </effectiveTime>
      <effectiveTime xsi:type="PIVL_TS" operator="A">
        <period value="1" unit="d"/>
      </effectiveTime>
      <routeCode code="C38288" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Oral"/>
      <doseQuantity value="1"/>

      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.23"/>
          <manufacturedMaterial>
            <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                  displayName="Lisinopril 10 MG Oral Tablet"/>
          </manufacturedMaterial>
        </manufacturedProduct>
      </consumable>

      <!-- DISPENSE EVENT -->
      <entryRelationship typeCode="REFR">
        <supply classCode="SPLY" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
          <id root="dispense-456"/>
          <statusCode code="completed"/>
          <effectiveTime xsi:type="IVL_TS">
            <low value="20200301090000-0500"/>
            <high value="20200301143000-0500"/>
          </effectiveTime>
          <repeatNumber value="1"/>
          <quantity value="30" unit="{tbl}"/>

          <product>
            <manufacturedProduct classCode="MANU">
              <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
              <manufacturedMaterial>
                <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                      displayName="Lisinopril 10 MG Oral Tablet"/>
              </manufacturedMaterial>
              <manufacturerOrganization>
                <name>Watson Pharmaceuticals Inc</name>
              </manufacturerOrganization>
            </manufacturedProduct>
          </product>

          <performer>
            <assignedEntity>
              <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
              <addr>
                <streetAddressLine>123 Pharmacy Lane</streetAddressLine>
                <city>Boston</city>
                <state>MA</state>
                <postalCode>02101</postalCode>
              </addr>
              <assignedPerson>
                <name>
                  <given>Jane</given>
                  <family>Smith</family>
                  <suffix>PharmD</suffix>
                </name>
              </assignedPerson>
              <representedOrganization>
                <name>Community Pharmacy</name>
              </representedOrganization>
            </assignedEntity>
          </performer>

          <author>
            <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
            <time value="20200301143000-0500"/>
            <assignedAuthor>
              <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
              <assignedPerson>
                <name>
                  <given>Jane</given>
                  <family>Smith</family>
                  <suffix>PharmD</suffix>
                </name>
              </assignedPerson>
            </assignedAuthor>
          </author>

          <entryRelationship typeCode="COMP">
            <supply classCode="SPLY" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.37.3.10" extension="2017-08-01"/>
              <quantity value="30" unit="d"/>
            </supply>
          </entryRelationship>

        </supply>
      </entryRelationship>

    </substanceAdministration>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "resource": {
        "resourceType": "MedicationRequest",
        "id": "medication-activity-123",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest"]
        },
        "identifier": [{
          "system": "urn:ietf:rfc:3986",
          "value": "urn:oid:medication-activity-123"
        }],
        "status": "active",
        "intent": "order",
        "medicationCodeableConcept": {
          "coding": [{
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "314076",
            "display": "Lisinopril 10 MG Oral Tablet"
          }]
        },
        "subject": {
          "reference": "Patient/patient-example"
        },
        "dosageInstruction": [{
          "timing": {
            "repeat": {
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
              "value": 1
            }
          }]
        }]
      }
    },
    {
      "resource": {
        "resourceType": "MedicationDispense",
        "id": "dispense-456",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense"]
        },
        "identifier": [{
          "system": "urn:ietf:rfc:3986",
          "value": "urn:oid:dispense-456"
        }],
        "status": "completed",
        "category": {
          "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
            "code": "community",
            "display": "Community"
          }]
        },
        "medicationCodeableConcept": {
          "coding": [{
            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
            "code": "314076",
            "display": "Lisinopril 10 MG Oral Tablet"
          }]
        },
        "subject": {
          "reference": "Patient/patient-example"
        },
        "performer": [{
          "function": {
            "coding": [{
              "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
              "code": "packager",
              "display": "Packager"
            }]
          },
          "actor": {
            "reference": "Practitioner/pharmacist-9876543210",
            "display": "Jane Smith, PharmD"
          }
        }],
        "location": {
          "reference": "Location/pharmacy-community",
          "display": "Community Pharmacy"
        },
        "authorizingPrescription": [{
          "reference": "MedicationRequest/medication-activity-123"
        }],
        "type": {
          "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
            "code": "FF",
            "display": "First Fill"
          }]
        },
        "quantity": {
          "value": 30,
          "unit": "tablet",
          "system": "http://unitsofmeasure.org",
          "code": "{tbl}"
        },
        "daysSupply": {
          "value": 30,
          "unit": "day",
          "system": "http://unitsofmeasure.org",
          "code": "d"
        },
        "whenPrepared": "2020-03-01T09:00:00-05:00",
        "whenHandedOver": "2020-03-01T14:30:00-05:00",
        "substitution": {
          "wasSubstituted": false
        }
      }
    },
    {
      "resource": {
        "resourceType": "Practitioner",
        "id": "pharmacist-9876543210",
        "identifier": [{
          "system": "http://hl7.org/fhir/sid/us-npi",
          "value": "9876543210"
        }],
        "name": [{
          "family": "Smith",
          "given": ["Jane"],
          "suffix": ["PharmD"]
        }]
      }
    },
    {
      "resource": {
        "resourceType": "Location",
        "id": "pharmacy-community",
        "name": "Community Pharmacy",
        "address": {
          "line": ["123 Pharmacy Lane"],
          "city": "Boston",
          "state": "MA",
          "postalCode": "02101"
        }
      }
    }
  ]
}
```

## Mapping Notes and Edge Cases

### Multiple Dispense Events

A single Medication Activity may have multiple Medication Dispense entries (original fill + refills):

**C-CDA:**
```xml
<substanceAdministration>
  <!-- Medication Activity -->
  <entryRelationship typeCode="REFR">
    <supply><!-- First dispense --></supply>
  </entryRelationship>
  <entryRelationship typeCode="REFR">
    <supply><!-- Second dispense (refill) --></supply>
  </entryRelationship>
</substanceAdministration>
```

**FHIR:** Create separate MedicationDispense resources, all referencing the same MedicationRequest:
```json
[
  {
    "resourceType": "MedicationDispense",
    "id": "dispense-1",
    "authorizingPrescription": [{"reference": "MedicationRequest/med-req-1"}],
    "type": {"coding": [{"code": "FF"}]}
  },
  {
    "resourceType": "MedicationDispense",
    "id": "dispense-2",
    "authorizingPrescription": [{"reference": "MedicationRequest/med-req-1"}],
    "type": {"coding": [{"code": "RF"}]}
  }
]
```

### Missing effectiveTime

If C-CDA Medication Dispense lacks `effectiveTime`:
- Check parent Medication Activity's `effectiveTime`
- Use parent's `low` value as approximate dispense date
- Set FHIR `status` to "unknown" if unable to determine completion

### Category Inference

C-CDA does not specify dispense category. Infer from context:
- If document is discharge summary → "discharge"
- If performer is retail pharmacy → "community"
- If performer is hospital pharmacy → "inpatient"
- Default → "outpatient"

### Medication Substitution Detection

**Algorithm:**
1. Compare dispense product code with parent Medication Activity product code
2. If codes differ:
   - Set `wasSubstituted = true`
   - Look up both codes in RxNorm
   - If same ingredient, different strength/form → "EC" (Equivalent composition)
   - If brand vs generic → "G" (Generic composition)
   - Otherwise → "E" (Equivalent)
3. If codes same → Set `wasSubstituted = false`

### Days Supply Calculation

If Days Supply nested template is absent but quantity and dosage are known:
- Calculate: `daysSupply = quantity / (dose × frequency)`
- Example: 30 tablets, 1 tablet daily → 30 days

**Note:** Only calculate if dosage is unambiguous (single instruction with simple frequency).

## Standards Compliance

### US Core Requirements Met

| US Core Element | C-CDA Source | Mapping |
|-----------------|--------------|---------|
| status (SHALL) | statusCode | Direct map |
| medication[x] (SHALL) | product/code | CodeableConcept preferred |
| subject (SHALL) | recordTarget | Patient reference |
| performer.actor (SHALL) | performer | Practitioner/Organization |
| whenHandedOver (conditional) | effectiveTime | DateTime (required if status=completed) |
| context (SHOULD) | encompassingEncounter | Encounter reference |
| authorizingPrescription (SHOULD) | Parent relationship | MedicationRequest reference |
| type (SHOULD) | Inferred from repeatNumber | Type code |
| quantity (SHOULD) | quantity | SimpleQuantity |

### C-CDA on FHIR IG Status

**Note:** The C-CDA on FHIR IG v2.0.0 does **not** include MedicationDispense mapping guidance. The IG states:

> "moodCode=INT means supply, moodCode=EVN means dispense, which is not documented here."

This mapping specification fills that gap by providing comprehensive guidance for converting C-CDA Medication Dispense (moodCode=EVN) to FHIR MedicationDispense.

### Implementation Recommendations

1. **Always create MedicationRequest first** - The dispense references it
2. **Link dispense to request** - Use authorizingPrescription
3. **Preserve original codes** - Include both RxNorm and NDC when present
4. **Create supporting resources** - Practitioner, Location for complete data
5. **Calculate missing data carefully** - Days supply, type inference
6. **Document assumptions** - When inferring data, note in resource text or extension

## References

- [FHIR R4B MedicationDispense](https://hl7.org/fhir/R4B/medicationdispense.html)
- [US Core MedicationDispense Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense)
- [C-CDA Medication Dispense Template](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.18.html)
- [C-CDA on FHIR IG](http://build.fhir.org/ig/HL7/ccda-on-fhir/)
- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/)
