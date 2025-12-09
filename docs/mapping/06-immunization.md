# Immunization Mapping: C-CDA Immunization Activity ↔ FHIR Immunization

This document provides detailed mapping guidance between C-CDA Immunization Activity and FHIR `Immunization` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Immunization Activity (`2.16.840.1.113883.10.20.22.4.52`) | `Immunization` |
| Section: Immunizations (LOINC `11369-6`) | — |
| moodCode: EVN (historical) | `Immunization` |
| moodCode: INT (planned) | `MedicationRequest` |

**Scope:** This mapping applies only to **historical immunizations** (`@moodCode="EVN"`). Planned/future immunizations (`INT`) should use MedicationRequest resource.

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `@negationInd="true"` | `Immunization.status` | Set to `not-done` |
| `substanceAdministration/id` | `Immunization.identifier` | ID → Identifier |
| `substanceAdministration/statusCode` | `Immunization.status` | [Status ConceptMap](#status-mapping) |
| `substanceAdministration/effectiveTime/@value` | `Immunization.occurrenceDateTime` | Date conversion |
| `substanceAdministration/effectiveTime/low/@value` | `Immunization.occurrenceDateTime` | Use low if no @value |
| `substanceAdministration/repeatNumber/@value` | `Immunization.protocolApplied.doseNumberPositiveInt` | Direct mapping |
| `substanceAdministration/routeCode` | `Immunization.route` | CodeableConcept |
| `substanceAdministration/approachSiteCode` | `Immunization.site` | CodeableConcept |
| `substanceAdministration/doseQuantity` | `Immunization.doseQuantity` | Quantity |
| `consumable/manufacturedProduct/manufacturedMaterial/code` | `Immunization.vaccineCode` | CodeableConcept |
| `consumable/manufacturedMaterial/lotNumberText` | `Immunization.lotNumber` | String |
| `consumable/manufacturedMaterial/manufacturerOrganization` | `Immunization.manufacturer` | Reference(Organization) |
| `performer` | `Immunization.performer` | [Performer Mapping](#performer-mapping) |
| `author` | Provenance | Create Provenance resource |
| Immunization Not Given Reason | `Immunization.statusReason` | [Not Given Reason](#not-given-reason) |
| Indication | `Immunization.reasonCode` | CodeableConcept |
| Reaction | `Immunization.reaction.detail` | Reference(Observation) |
| Comment Activity | `Immunization.note` | Annotation |

### Status Mapping

**C-CDA:**
```xml
<statusCode code="completed"/>
```

**Immunization Status ConceptMap:**

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `completed` |
| `active` | `completed` |
| `aborted` | `not-done` |
| `cancelled` | `not-done` |

**With negationInd:**

| C-CDA | FHIR status |
|-------|-------------|
| `@negationInd="true"` | `not-done` |

**FHIR:**
```json
{
  "status": "completed"
}
```

### Vaccine Code Mapping

**C-CDA:**
```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
    <manufacturedMaterial>
      <code code="140" codeSystem="2.16.840.1.113883.12.292"
            displayName="Influenza, seasonal, injectable, preservative free">
        <originalText>
          <reference value="#imm1"/>
        </originalText>
        <translation code="49281-0400-10" codeSystem="2.16.840.1.113883.6.69"
                     displayName="Fluzone Quadrivalent"/>
      </code>
      <lotNumberText>L12345</lotNumberText>
    </manufacturedMaterial>
    <manufacturerOrganization>
      <name>Sanofi Pasteur</name>
    </manufacturerOrganization>
  </manufacturedProduct>
</consumable>
```

**FHIR:**
```json
{
  "vaccineCode": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/cvx",
        "code": "140",
        "display": "Influenza, seasonal, injectable, preservative free"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "49281-0400-10",
        "display": "Fluzone Quadrivalent"
      }
    ],
    "text": "Influenza vaccine"
  },
  "lotNumber": "L12345",
  "manufacturer": {
    "display": "Sanofi Pasteur"
  }
}
```

### Occurrence DateTime

**C-CDA (single value):**
```xml
<effectiveTime value="20200915"/>
```

**C-CDA (with low/high):**
```xml
<effectiveTime>
  <low value="20200915"/>
  <high value="20200915"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "occurrenceDateTime": "2020-09-15"
}
```

**Note:** EVN immunizations typically only contain a single value. If `effectiveTime` contains `low`/`high`, use `low` for `occurrenceDateTime`.

### Dose Quantity

**C-CDA:**
```xml
<doseQuantity value="0.5" unit="mL"/>
```

**FHIR:**
```json
{
  "doseQuantity": {
    "value": 0.5,
    "unit": "mL",
    "system": "http://unitsofmeasure.org",
    "code": "mL"
  }
}
```

### Route and Site

**C-CDA:**
```xml
<routeCode code="C28161" codeSystem="2.16.840.1.113883.3.26.1.1"
           displayName="Intramuscular injection"/>
<approachSiteCode code="61396006" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Left thigh"/>
```

**FHIR:**
```json
{
  "route": {
    "coding": [{
      "system": "http://ncimeta.nci.nih.gov",
      "code": "C28161",
      "display": "Intramuscular injection"
    }]
  },
  "site": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "61396006",
      "display": "Left thigh"
    }]
  }
}
```

### Performer Mapping

**C-CDA:**
```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name><given>Jane</given><family>Nurse</family></name>
    </assignedPerson>
    <representedOrganization>
      <name>City Clinic</name>
    </representedOrganization>
  </assignedEntity>
</performer>
```

**FHIR:**
```json
{
  "performer": [{
    "function": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
        "code": "AP",
        "display": "Administering Provider"
      }]
    },
    "actor": {
      "reference": "Practitioner/practitioner-nurse"
    }
  }]
}
```

**Note:** Set `performer.function` to `AP` (Administering Provider) for immunization performers.

### Primary Source

**C-CDA** does not have a direct equivalent for `primarySource`. When mapping to a FHIR profile that requires this element (e.g., US Core prior to Release 6), include a data-absent-reason extension:

```json
{
  "_primarySource": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
      "valueCode": "unsupported"
    }]
  }
}
```

For US Core 6+, use `informationSourceCodeableConcept` or `informationSourceReference` instead.

### Not Given Reason

When `@negationInd="true"`, the reason for not giving the immunization:

**C-CDA:**
```xml
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
  <!-- ... -->
  <entryRelationship typeCode="RSON">
    <observation classCode="OBS" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
      <code code="PATOBJ" codeSystem="2.16.840.1.113883.5.8"
            displayName="Patient Objection"/>
    </observation>
  </entryRelationship>
</substanceAdministration>
```

**FHIR:**
```json
{
  "status": "not-done",
  "statusReason": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
      "code": "PATOBJ",
      "display": "Patient Objection"
    }]
  }
}
```

### Indication (Reason)

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
    <code code="59037007" codeSystem="2.16.840.1.113883.6.96"
          displayName="Indication"/>
    <value xsi:type="CD" code="195967001" codeSystem="2.16.840.1.113883.6.96"
           displayName="Asthma"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "195967001",
      "display": "Asthma"
    }]
  }]
}
```

**Note:** Differentiate from "Not Given Reason" by checking if it's from the Problem Type ValueSet (indication) vs. Act Reason codes (not given reason).

### Reaction

**C-CDA:**
```xml
<entryRelationship typeCode="MFST" inversionInd="true">
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.9"/>
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="39579001" codeSystem="2.16.840.1.113883.6.96"
           displayName="Anaphylaxis"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reaction": [{
    "detail": {
      "reference": "Observation/reaction-anaphylaxis"
    }
  }]
}
```

**FHIR Observation for Reaction:**
```json
{
  "resourceType": "Observation",
  "id": "reaction-anaphylaxis",
  "status": "final",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "39579001",
      "display": "Anaphylaxis"
    }]
  }
}
```

### Dose Number (Protocol Applied)

**C-CDA:**
```xml
<repeatNumber value="2"/>
```

**FHIR:**
```json
{
  "protocolApplied": [{
    "doseNumberPositiveInt": 2
  }]
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Immunization.identifier` | `substanceAdministration/id` | Identifier → ID |
| `Immunization.status: not-done` | `@negationInd="true"` | Set negation indicator |
| `Immunization.status` | `substanceAdministration/statusCode` | Reverse status map |
| `Immunization.vaccineCode` | `consumable/manufacturedMaterial/code` | CodeableConcept → CE |
| `Immunization.occurrenceDateTime` | `effectiveTime/@value` | Date format |
| `Immunization.lotNumber` | `manufacturedMaterial/lotNumberText` | Direct mapping |
| `Immunization.manufacturer` | `manufacturerOrganization` | Create organization |
| `Immunization.doseQuantity` | `doseQuantity` | Quantity → PQ |
| `Immunization.route` | `routeCode` | CodeableConcept → CE |
| `Immunization.site` | `approachSiteCode` | CodeableConcept → CD |
| `Immunization.performer` | `performer` | Create performer |
| `Immunization.statusReason` | Not Given Reason Observation | Create entryRelationship |
| `Immunization.reasonCode` | Indication Observation | Create entryRelationship |
| `Immunization.reaction.detail` | Reaction Observation | Create entryRelationship |
| `Immunization.note` | Comment Activity | Create nested act |
| `Immunization.protocolApplied.doseNumberPositiveInt` | `repeatNumber/@value` | Direct mapping |

### FHIR Status to CDA

| FHIR status | CDA statusCode | Additional |
|-------------|----------------|------------|
| `completed` | `completed` | — |
| `not-done` | `cancelled` | or `negationInd="true"` |
| `entered-in-error` | — | Do not convert |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.2.1"/>
  <code code="11369-6" codeSystem="2.16.840.1.113883.6.1"/>
  <title>IMMUNIZATIONS</title>
  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.52" extension="2015-08-01"/>
      <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
      <statusCode code="completed"/>
      <effectiveTime value="20200915"/>
      <repeatNumber value="1"/>
      <routeCode code="C28161" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Intramuscular injection"/>
      <approachSiteCode code="61396006" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Left thigh"/>
      <doseQuantity value="0.5" unit="mL"/>
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
          <manufacturedMaterial>
            <code code="140" codeSystem="2.16.840.1.113883.12.292"
                  displayName="Influenza, seasonal, injectable, preservative free">
              <translation code="49281-0400-10" codeSystem="2.16.840.1.113883.6.69"/>
            </code>
            <lotNumberText>L12345</lotNumberText>
          </manufacturedMaterial>
          <manufacturerOrganization>
            <name>Sanofi Pasteur</name>
          </manufacturerOrganization>
        </manufacturedProduct>
      </consumable>
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name><given>Jane</given><family>Nurse</family></name>
          </assignedPerson>
        </assignedEntity>
      </performer>
      <author>
        <time value="20200915"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
    </substanceAdministration>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Immunization",
  "id": "immunization-flu",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-immunization"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"
  }],
  "status": "completed",
  "vaccineCode": {
    "coding": [
      {
        "system": "http://hl7.org/fhir/sid/cvx",
        "code": "140",
        "display": "Influenza, seasonal, injectable, preservative free"
      },
      {
        "system": "http://hl7.org/fhir/sid/ndc",
        "code": "49281-0400-10"
      }
    ]
  },
  "patient": {
    "reference": "Patient/patient-example"
  },
  "occurrenceDateTime": "2020-09-15",
  "lotNumber": "L12345",
  "manufacturer": {
    "display": "Sanofi Pasteur"
  },
  "route": {
    "coding": [{
      "system": "http://ncimeta.nci.nih.gov",
      "code": "C28161",
      "display": "Intramuscular injection"
    }]
  },
  "site": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "61396006",
      "display": "Left thigh"
    }]
  },
  "doseQuantity": {
    "value": 0.5,
    "unit": "mL",
    "system": "http://unitsofmeasure.org",
    "code": "mL"
  },
  "performer": [{
    "function": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
        "code": "AP",
        "display": "Administering Provider"
      }]
    },
    "actor": {
      "reference": "Practitioner/practitioner-nurse"
    }
  }],
  "protocolApplied": [{
    "doseNumberPositiveInt": 1
  }]
}
```

## References

- [C-CDA on FHIR Immunizations Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-immunizations.html)
- [US Core Immunization Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-immunization)
- [C-CDA Immunization Activity](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.52.html)
- [CVX Vaccine Codes](https://www2.cdc.gov/vaccines/iis/iisstandards/vaccines.asp?rpt=cvx)
