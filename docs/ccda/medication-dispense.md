# C-CDA: Medication Dispense

## Overview

The Medication Dispense template in C-CDA represents the act of dispensing medication to a patient. This template documents actual dispensing events (as opposed to prescriptions or supply orders). Medication Dispense appears as a nested entry relationship within Medication Activity templates, documenting when, where, and by whom medication was dispensed.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.18` |
| Template Version | 2014-06-09 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/MedicationDispense` |
| Parent Context | Medication Activity (`2.16.840.1.113883.10.20.22.4.16`) |
| Entry Relationship Type | REFR (refers to) |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Medications Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.1.1']
                ├── code [@code='10160-0']
                └── entry
                    └── substanceAdministration [Medication Activity]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.16']
                        └── entryRelationship [@typeCode='REFR']
                            └── supply [Medication Dispense]
                                └── templateId [@root='2.16.840.1.113883.10.20.22.4.18']
```

## XML Structure

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>

    <!-- Unique identifier -->
    <id root="1.2.3.4.56789.1" extension="cb734647-fc99-424c-a864-7e3cda82e704"/>

    <!-- Status -->
    <statusCode code="completed"/>

    <!-- When dispensed -->
    <effectiveTime value="20200301143000-0500"/>

    <!-- Refill number -->
    <repeatNumber value="1"/>

    <!-- Quantity dispensed -->
    <quantity value="30" unit="{tbl}"/>

    <!-- Medication product (references same product as parent Medication Activity) -->
    <product>
      <manufacturedProduct classCode="MANU">
        <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
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
        <manufacturerOrganization>
          <name>Watson Pharmaceuticals Inc</name>
        </manufacturerOrganization>
      </manufacturedProduct>
    </product>

    <!-- Dispensing pharmacy/pharmacist -->
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
        <representedOrganization>
          <name>Community Pharmacy</name>
          <telecom use="WP" value="tel:(555)555-1000"/>
          <addr>
            <streetAddressLine>123 Pharmacy Lane</streetAddressLine>
            <city>Boston</city>
            <state>MA</state>
            <postalCode>02101</postalCode>
          </addr>
        </representedOrganization>
      </assignedEntity>
    </performer>

    <!-- Author (pharmacist who dispensed) -->
    <author>
      <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
      <time value="20200301143000-0500"/>
      <assignedAuthor>
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
      </assignedAuthor>
    </author>

    <!-- Days supply (optional) -->
    <entryRelationship typeCode="COMP">
      <supply classCode="SPLY" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.37.3.10" extension="2017-08-01"/>
        <quantity value="30" unit="d"/>
      </supply>
    </entryRelationship>

  </supply>
</entryRelationship>
```

## Element Details

### supply/@classCode

The class code for medication dispense.

| Attribute | Value | Description |
|-----------|-------|-------------|
| @classCode | SPLY | Supply (required) |

### supply/@moodCode

The mood code indicating this is an actual event (not intent/order).

| Code | Display | Description |
|------|---------|-------------|
| EVN | Event | Actual dispense occurred |

**Critical:** Medication Dispense uses `moodCode="EVN"` (event) to distinguish from Medication Supply Order (`moodCode="INT"`, template `2.16.840.1.113883.10.20.22.4.17`), which represents the prescription/order.

### id

Unique identifier for the dispensing event.

| Attribute | Description |
|-----------|-------------|
| @root | OID or UUID |
| @extension | Additional identifier |

**Best Practice:** Use UUID or pharmacy-specific dispensing transaction ID.

### statusCode

The status of the dispense event.

| Code | Display | Description |
|------|---------|-------------|
| completed | Completed | Dispense completed |
| aborted | Aborted | Dispense was stopped |
| cancelled | Cancelled | Dispense was cancelled |

**Note:** Most dispense records use `completed` status. Other statuses are rare in historical documentation.

### effectiveTime

The date and time when the medication was dispensed/handed over to the patient.

```xml
<!-- Single timestamp -->
<effectiveTime value="20200301143000-0500"/>

<!-- With low/high (preparation to handover) -->
<effectiveTime xsi:type="IVL_TS">
  <low value="20200301090000-0500"/>
  <high value="20200301143000-0500"/>
</effectiveTime>
```

| Attribute | Description |
|-----------|-------------|
| @value | Single timestamp (when handed over) |
| low | When preparation started |
| high | When handed over to patient |

### repeatNumber

The fill/refill number.

```xml
<!-- First fill -->
<repeatNumber value="1"/>

<!-- First refill -->
<repeatNumber value="2"/>

<!-- Second refill -->
<repeatNumber value="3"/>
```

| Attribute | Description |
|-----------|-------------|
| @value | Fill number (1 = original fill, 2+ = refills) |

**Note:** This differs from Medication Supply Order where `repeatNumber` represents the total number of fills allowed (including the original).

### quantity

The amount of medication dispensed.

```xml
<quantity value="30" unit="{tbl}"/>
```

| Attribute | Description |
|-----------|-------------|
| @value | Numeric quantity |
| @unit | Unit code (UCUM) |

**Common Unit Codes:**
| Unit | Description |
|------|-------------|
| {tbl} | Tablet |
| {cap} | Capsule |
| mL | Milliliter |
| mg | Milligram |
| g | Gram |
| {puff} | Puff |
| {spray} | Spray |

### product

The medication product dispensed.

| Element | Description |
|---------|-------------|
| manufacturedProduct/templateId | `2.16.840.1.113883.10.20.22.4.23` |
| manufacturedMaterial/code | Medication code (RxNorm preferred) |

**Note:** The product element should reference the same medication as the parent Medication Activity. If a substitution occurred, the code may differ.

**Code Systems:**
| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.6.88 | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | NDC |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT |

### performer

The dispensing pharmacy or pharmacist.

| Element | Description |
|---------|-------------|
| assignedEntity/id | NPI or other identifier |
| assignedEntity/addr | Pharmacy address |
| assignedEntity/telecom | Pharmacy phone |
| representedOrganization | Pharmacy organization |

**Best Practice:** Include both individual pharmacist (if known) and pharmacy organization.

### author

The pharmacist who performed the dispense.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.119` (Author Participation) |
| time | When dispensed |
| assignedAuthor/id | Pharmacist NPI |
| assignedPerson/name | Pharmacist name |

### Days Supply (Optional Entry Relationship)

Optional nested template documenting the expected days supply.

```xml
<entryRelationship typeCode="COMP">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.37.3.10" extension="2017-08-01"/>
    <quantity value="30" unit="d"/>
  </supply>
</entryRelationship>
```

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.37.3.10` (Days Supply) |
| quantity/@value | Number of days |
| quantity/@unit | "d" (days) |

## Conformance Requirements

### Medication Dispense
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.18`
2. **SHALL** contain at least one `id`
3. **SHALL** contain exactly one `statusCode`
4. **SHALL** contain exactly one `moodCode` with value "EVN"
5. **SHOULD** contain exactly one `effectiveTime` (dispense date/time)
6. **MAY** contain exactly one `repeatNumber` (fill number)
7. **SHOULD** contain exactly one `quantity` (amount dispensed)
8. **SHALL** contain exactly one `product` with Medication Information template
9. **SHOULD** contain at least one `performer` (dispensing pharmacy)
10. **SHOULD** contain at least one `author` (pharmacist)
11. **MAY** contain Days Supply entry relationship

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| statusCode | ActStatus | Required |
| quantity/@unit | UCUM units | Preferred |
| product/manufacturedMaterial/code | RxNorm | Preferred |

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| mood-code-evn | Error | moodCode SHALL be "EVN" for dispense events |
| should-effectiveTime | Warning | effectiveTime SHOULD be present to document when dispensed |
| should-quantity | Warning | quantity SHOULD be present to document amount dispensed |

## Medication Dispense vs Medication Supply Order

| Aspect | Medication Dispense | Medication Supply Order |
|--------|---------------------|-------------------------|
| Template ID | `2.16.840.1.113883.10.20.22.4.18` | `2.16.840.1.113883.10.20.22.4.17` |
| moodCode | EVN (event) | INT (intent) |
| Represents | Actual dispensing event | Prescription/order |
| effectiveTime | When dispensed | Prescription validity period |
| repeatNumber | Fill number (1, 2, 3...) | Total fills allowed |
| quantity | Amount actually dispensed | Amount per fill |
| performer | Dispensing pharmacy | (not typically present) |

## Usage Context

Medication Dispense templates are typically found in:
- **Medications Section** - Historical dispensing records
- **Discharge Medications Section** - Medications dispensed at discharge
- **Hospital Discharge Medications Section** - Inpatient discharge medications

**Common Use Cases:**
- Documenting pharmacy dispensing history
- Reconciling medications at care transitions
- Verifying patient adherence (what was actually dispensed vs prescribed)
- Insurance/billing documentation

## Examples

### Example 1: Simple Dispense

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
    <id root="cb734647-fc99-424c-a864-7e3cda82e704"/>
    <statusCode code="completed"/>
    <effectiveTime value="20200301143000-0500"/>
    <repeatNumber value="1"/>
    <quantity value="30" unit="{tbl}"/>
    <product>
      <manufacturedProduct classCode="MANU">
        <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
        <manufacturedMaterial>
          <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                displayName="Lisinopril 10 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </product>
    <performer>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
        <representedOrganization>
          <name>Community Pharmacy</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
  </supply>
</entryRelationship>
```

### Example 2: Refill with Days Supply

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
    <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
    <statusCode code="completed"/>
    <effectiveTime value="20200401090000-0500"/>
    <repeatNumber value="2"/>
    <quantity value="30" unit="{tbl}"/>
    <product>
      <manufacturedProduct classCode="MANU">
        <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
        <manufacturedMaterial>
          <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                displayName="Lisinopril 10 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </product>
    <performer>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
        <representedOrganization>
          <name>Community Pharmacy</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
    <entryRelationship typeCode="COMP">
      <supply classCode="SPLY" moodCode="EVN">
        <templateId root="2.16.840.1.113883.10.20.37.3.10" extension="2017-08-01"/>
        <quantity value="30" unit="d"/>
      </supply>
    </entryRelationship>
  </supply>
</entryRelationship>
```

## Documentation Context

Medication Dispense is a nested template within Medication Activity. A complete medication record often includes:
1. **Medication Activity** (parent) - The prescription/medication order
2. **Medication Supply Order** (nested) - The original prescription details
3. **Medication Dispense** (nested) - One or more dispensing events

This hierarchy allows tracking from prescription → dispense → administration.

## References

- C-CDA R2.1 Implementation Guide Section 3.46 (Medication Dispense)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- C-CDA Examples: https://github.com/HL7/C-CDA-Examples
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
