# C-CDA to FHIR Mapping Overview

This document provides general guidance for mapping between C-CDA (Consolidated Clinical Document Architecture) and FHIR R4 resources. The mappings in this directory are based on the [HL7 C-CDA on FHIR Implementation Guide](http://build.fhir.org/ig/HL7/ccda-on-fhir).

## Mapping Direction

This library currently supports unidirectional mapping:
- **C-CDA → FHIR**: Converting clinical documents to FHIR resources ✅ **Implemented**
- **FHIR → C-CDA**: Converting FHIR resources to clinical documents 🚧 **Planned**

## Documentation Structure

This directory contains comprehensive mapping documentation organized as follows:

### Clinical Domain Mappings

Detailed mappings for specific clinical areas (aligned with HL7 C-CDA on FHIR IG):

- **[01-patient.md](01-patient.md)**: Patient demographics and administrative data
- **[02-condition.md](02-condition.md)**: Problems and diagnoses
- **[03-allergy-intolerance.md](03-allergy-intolerance.md)**: Allergies and intolerances
- **[04-observation.md](04-observation.md)**: Laboratory results and observations
- **[05-procedure.md](05-procedure.md)**: Procedures and interventions
- **[06-immunization.md](06-immunization.md)**: Immunizations and vaccinations
- **[07-medication-request.md](07-medication-request.md)**: Medications and prescriptions
- **[08-encounter.md](08-encounter.md)**: Encounters and visits
- **[09-participations.md](09-participations.md)**: Document participants (author, performer, informant, etc.)
- **[10-notes.md](10-notes.md)**: Clinical notes and documentation
- **[11-social-history.md](11-social-history.md)**: Social history observations
- **[12-vital-signs.md](12-vital-signs.md)**: Vital signs measurements

### Supplementary Documentation

Supporting resources for implementation:

- **[terminology-maps.md](terminology-maps.md)**: Concept maps for value set translation between C-CDA and FHIR
- **[known-issues.md](known-issues.md)**: Known limitations, edge cases, and unresolved challenges
- **[change-log.md](change-log.md)**: Version history and mapping changes

### Planning Documentation

- **[../c-cda-fhir-compliance-plan.md](../c-cda-fhir-compliance-plan.md)**: Roadmap for achieving full HL7 C-CDA on FHIR IG compliance

## Core Data Type Mappings

### Identifier Mapping

#### C-CDA to FHIR

| C-CDA Element | FHIR Element | Notes |
|---------------|--------------|-------|
| `@root` (OID) | `identifier.system` | Translate OID to URI (see OID-URI mapping) |
| `@root` (UUID) | `identifier.system` | Prefix with `urn:uuid:` |
| `@extension` | `identifier.value` | Direct mapping |
| `@assigningAuthorityName` | `identifier.assigner.display` | If no Organization reference available |

**OID to URI Translation:**
- Known OIDs should be translated to their canonical URIs (e.g., `2.16.840.1.113883.6.1` → `http://loinc.org`)
- Unknown OIDs should be prefixed with `urn:oid:` (e.g., `urn:oid:2.16.840.1.113883.4.123456789`)

**Common OID-URI Mappings:**

| OID | URI | Description |
|-----|-----|-------------|
| `2.16.840.1.113883.6.1` | `http://loinc.org` | LOINC |
| `2.16.840.1.113883.6.96` | `http://snomed.info/sct` | SNOMED CT |
| `2.16.840.1.113883.6.88` | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| `2.16.840.1.113883.6.90` | `http://hl7.org/fhir/sid/icd-10-cm` | ICD-10-CM |
| `2.16.840.1.113883.6.103` | `http://hl7.org/fhir/sid/icd-9-cm` | ICD-9-CM |
| `2.16.840.1.113883.6.69` | `http://hl7.org/fhir/sid/ndc` | NDC |
| `2.16.840.1.113883.6.12` | `http://www.ama-assn.org/go/cpt` | CPT |
| `2.16.840.1.113883.4.1` | `http://hl7.org/fhir/sid/us-ssn` | US SSN |
| `2.16.840.1.113883.4.6` | `http://hl7.org/fhir/sid/us-npi` | US NPI |
| `2.16.840.1.113883.6.238` | `urn:oid:2.16.840.1.113883.6.238` | CDC Race/Ethnicity |
| `2.16.840.1.113883.5.1` | `http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender` | HL7 Gender |
| `2.16.840.1.113883.5.111` | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` | HL7 Role Code |
| `2.16.840.1.113883.12.292` | `http://hl7.org/fhir/sid/cvx` | CVX (Vaccines) |

#### FHIR to C-CDA

- Remove `urn:oid:` or `urn:uuid:` prefixes
- Translate known URIs back to OIDs
- For unmapped systems, use the URI specification OID (`2.16.840.1.113883.4.873`) as root and concatenate system+value

### Date/Time Mapping

#### C-CDA Format
```
YYYYMMDDHHmmss+ZZZZ
```

#### FHIR Format
```
YYYY-MM-DDThh:mm:ss+zz:zz
```

#### Conversion Rules

| C-CDA | FHIR | Notes |
|-------|------|-------|
| `20230515` | `2023-05-15` | Date only |
| `202305` | `2023-05` | Year-month only |
| `2023` | `2023` | Year only |
| `20230515143022-0500` | `2023-05-15T14:30:22-05:00` | Full timestamp with timezone |
| `20230515143022` | `2023-05-15` | Time without timezone → reduced to date per FHIR R4 |

**Precision Preservation:**
- Partial dates should maintain their precision (don't pad with zeros)
- Per FHIR R4: timezone offsets are **required** (SHALL) when precision includes hours/minutes
- When C-CDA timestamp has time but lacks timezone, precision is reduced to date-only per C-CDA on FHIR IG guidance (avoids manufacturing potentially incorrect timezone data)

**Structured Temporal Fields:**

| C-CDA | FHIR |
|-------|------|
| `effectiveTime/@value` | `effective` or `effectiveDateTime` |
| `effectiveTime/low/@value` | `period.start` or `effectivePeriod.start` |
| `effectiveTime/high/@value` | `period.end` or `effectivePeriod.end` |

### Coding and CodeableConcept Mapping

#### C-CDA to FHIR

| C-CDA Element | FHIR Element |
|---------------|--------------|
| `@code` | `coding.code` |
| `@codeSystem` | `coding.system` (OID→URI conversion) |
| `@displayName` | `coding.display` |
| `@codeSystemName` | Not mapped (can be derived from system) |
| `originalText` | `CodeableConcept.text` |
| `translation` | Additional `coding` entries |

**Example:**

C-CDA:
```xml
<code code="I10" codeSystem="2.16.840.1.113883.6.90" displayName="Essential hypertension">
  <originalText>
    <reference value="#problem1"/>
  </originalText>
  <translation code="59621000" codeSystem="2.16.840.1.113883.6.96"
               displayName="Essential hypertension"/>
</code>
```

FHIR:
```json
{
  "coding": [
    {
      "system": "http://hl7.org/fhir/sid/icd-10-cm",
      "code": "I10",
      "display": "Essential hypertension"
    },
    {
      "system": "http://snomed.info/sct",
      "code": "59621000",
      "display": "Essential hypertension"
    }
  ],
  "text": "Essential hypertension"
}
```

#### FHIR to C-CDA

- First coding becomes the primary `code` element
- Additional codings become `translation` elements
- If no coding matches the required value set, use `nullFlavor="OTH"` with translations
- `CodeableConcept.text` maps to `originalText`

### Quantity Mapping

| C-CDA | FHIR | Notes |
|-------|------|-------|
| `@value` | `value` | Numeric value |
| `@unit` | `code` | UCUM unit code |
| (implicit) | `system` | `http://unitsofmeasure.org` |
| `@unit` | `unit` | Human-readable unit (optional) |

**Range Handling:**

| C-CDA Pattern | FHIR Type |
|---------------|-----------|
| `IVL_PQ` with `low` and `high` | `Range` |
| High-only with `@inclusive="true"` | `Quantity` with `comparator: "<="` |
| High-only with `@inclusive="false"` | `Quantity` with `comparator: "<"` |
| Low-only with `@inclusive="true"` | `Quantity` with `comparator: ">="` |
| Low-only with `@inclusive="false"` | `Quantity` with `comparator: ">"` |

### Name Mapping

| C-CDA Element | FHIR Element |
|---------------|--------------|
| `@use` | `use` (via ConceptMap) |
| `prefix` | `prefix` |
| `given` | `given` (array) |
| `family` | `family` |
| `suffix` | `suffix` |
| `validTime/low/@value` | `period.start` |
| `validTime/high/@value` | `period.end` |

**Name Use ConceptMap:**

| C-CDA | FHIR |
|-------|------|
| `L` | `usual` |
| `OR` | `official` |
| `C` | `old` |
| `P` | `nickname` |
| `A` | `anonymous` |
| `ASGN` | `usual` |
| (maiden context) | `maiden` |

### Address Mapping

| C-CDA Element | FHIR Element |
|---------------|--------------|
| `@use` | `use` (via ConceptMap) |
| `streetAddressLine` | `line` (array) |
| `city` | `city` |
| `state` | `state` |
| `postalCode` | `postalCode` |
| `country` | `country` |
| `useablePeriod/low/@value` | `period.start` |
| `useablePeriod/high/@value` | `period.end` |

**Address Use ConceptMap:**

| C-CDA | FHIR |
|-------|------|
| `H` | `home` |
| `HP` | `home` |
| `HV` | `home` |
| `WP` | `work` |
| `DIR` | `work` |
| `PUB` | `work` |
| `TMP` | `temp` |
| `BAD` | `old` |

### Telecom Mapping

| C-CDA Element | FHIR Element |
|---------------|--------------|
| `@use` | `use` (via ConceptMap) |
| `@value` | `system` + `value` |

**Parsing `@value`:**
- `tel:+1(555)555-1234` → `system: "phone"`, `value: "+1(555)555-1234"`
- `mailto:name@email.com` → `system: "email"`, `value: "name@email.com"`
- `fax:+1(555)555-1234` → `system: "fax"`, `value: "+1(555)555-1234"`

**Telecom Use ConceptMap:**

| C-CDA | FHIR |
|-------|------|
| `HP` | `home` |
| `WP` | `work` |
| `MC` | `mobile` |
| `TMP` | `temp` |
| `BAD` | `old` |

## NullFlavor and Data Absent Reason

C-CDA uses `nullFlavor` attributes to indicate missing or unknown data. FHIR uses the `data-absent-reason` extension.

### NullFlavor to Data Absent Reason

| C-CDA NullFlavor | FHIR Data Absent Reason |
|------------------|-------------------------|
| `UNK` | `unknown` |
| `ASKU` | `asked-unknown` |
| `NAV` | `temp-unknown` |
| `NASK` | `not-asked` |
| `NI` | `unknown` |
| `NA` | `not-applicable` |
| `MSK` | `masked` |
| `OTH` | `other` |
| `NINF` | `negative-infinity` |
| `PINF` | `positive-infinity` |

## Narrative Text Handling

### C-CDA Section Text to FHIR

When CDA entries contain `<text><reference value="#id1">`, the FHIR resource should:
1. Extract the section narrative element matching the reference ID
2. Include the matched element and its children
3. For table elements (`<tr>`, `<td>`), include header context

### CDA to XHTML Conversion

| C-CDA Element | XHTML Element |
|---------------|---------------|
| `<content>` | `<span>` |
| `<paragraph>` | `<div>` or `<p>` |
| `<list>` | `<ul>` or `<ol>` (based on `@listType`) |
| `<renderMultiMedia>` | `<img>` |
| `@styleCode` | `@style` or `@class` |
| `@ID` | `@id` (lowercase) |

## Provenance Tracking

Author information in C-CDA should be mapped to FHIR resources and optionally to Provenance resources:

| C-CDA Element | FHIR Target | Notes |
|---------------|-------------|-------|
| Latest `author` | Resource `.recorder` | Last author in list |
| Earliest `author/time` | Resource `.recordedDate` | First timestamp |
| All `author` entries | `Provenance` resource | Complete audit trail |

## Negation Handling

### C-CDA Negation Indicator

When `@negationInd="true"` on an observation or activity:

| C-CDA Context | FHIR Handling |
|---------------|---------------|
| Allergy Observation | Use "No known allergy" code or `substanceExposureRisk` extension |
| Problem Observation | Set `verificationStatus: "refuted"` or use negated concept |
| Procedure | Set `status: "not-done"` |
| Medication | Set `doNotPerform: true` |
| Immunization | Set `status: "not-done"` |

## Resource Mapping Summary

| C-CDA Section/Entry | FHIR Resource |
|---------------------|---------------|
| `recordTarget/patientRole` | `Patient` |
| Allergy Concern Act / Allergy Observation | `AllergyIntolerance` |
| Problem Concern Act / Problem Observation | `Condition` |
| Medication Activity | `MedicationRequest` or `MedicationStatement` |
| Immunization Activity | `Immunization` |
| Procedure Activity | `Procedure` |
| Result Organizer / Result Observation | `DiagnosticReport` / `Observation` |
| Vital Signs Organizer / Observation | `Observation` (vital-signs category) |
| Encounter Activity | `Encounter` |
| Author | `Practitioner` / `PractitionerRole` |
| Performer | `Practitioner` / `PractitionerRole` |
| Custodian Organization | `Organization` |
| Clinical Document | `Composition` / `DocumentReference` |

## Implementation Considerations

### Status Code Ambiguity

C-CDA may list an activity as "completed" but contain dates in the future. Implementations should:
- Evaluate timestamps relative to the current date
- Consider "completed" with future dates as "active" in FHIR
- Document assumptions about status interpretation

### Multiple Authors

When multiple authors exist:
- Map the most recent/authoritative author to the FHIR resource's direct author field
- Create Provenance resources for complete author tracking
- Use the earliest `author/time` for `.recordedDate`

### Reference Resolution

FHIR references should be created when:
- Related resources are created from the same document
- External references can be resolved
- Consider using contained resources for tightly coupled data

### Validation

Implementations should validate:
- Required elements are present in both directions
- Code systems are correctly translated
- Dates are properly formatted
- References are resolvable

## References

- [HL7 C-CDA on FHIR Implementation Guide](http://build.fhir.org/ig/HL7/ccda-on-fhir)
- [HL7 FHIR R4](https://hl7.org/fhir/R4/)
- [HL7 C-CDA R2.1](http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492)
- [US Core Implementation Guide](http://hl7.org/fhir/us/core/)
- [HL7 Terminology](https://terminology.hl7.org/)
