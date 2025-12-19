# C-CDA: Medication Information

## Overview

The Medication Information template represents the details of a medication product in C-CDA documents. It is used within the `consumable` element of Medication Activity, Medication Dispense, Medication Supply Order, and Planned Medication Activity templates to specify the actual medication being prescribed, dispensed, or administered.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.23` |
| Template Version | 2014-06-09 |
| Official URL | `http://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationInformation.html` |
| Parent Template | ManufacturedProduct (CDA R2) |
| Class Code | MANU (manufactured product) |
| Contained In | Medication Activity, Medication Dispense, Medication Supply Order, Planned Medication Activity |

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Medications Section]
                └── entry
                    └── substanceAdministration [Medication Activity]
                        └── consumable
                            └── manufacturedProduct [Medication Information]
                                ├── templateId [@root='2.16.840.1.113883.10.20.22.4.23']
                                ├── id
                                ├── manufacturedMaterial
                                │   ├── code (RxNorm/NDC/SNOMED)
                                │   ├── name
                                │   ├── lotNumberText
                                │   └── expirationTime
                                └── manufacturerOrganization
```

## XML Structure

```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <!-- Medication Information Template -->
    <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
    <templateId root="2.16.840.1.113883.10.20.22.4.23"/>

    <!-- Optional: Product Identifier -->
    <id root="2.16.840.1.113883.3.3489.1.1" extension="MED-12345"/>

    <!-- Required: Manufactured Material -->
    <manufacturedMaterial>
      <!-- Required: Medication Code -->
      <code code="197361" codeSystem="2.16.840.1.113883.6.88"
            codeSystemName="RxNorm"
            displayName="Lisinopril 10 MG Oral Tablet">
        <originalText>
          <reference value="#med1"/>
        </originalText>
        <!-- Optional: Additional codes (NDC, etc.) -->
        <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
                     codeSystemName="NDC" displayName="Lisinopril 10mg Tab"/>
      </code>

      <!-- Optional: Medication Name -->
      <name>Lisinopril 10mg Tablets</name>

      <!-- Optional: Lot Number -->
      <lotNumberText>LOT-987654</lotNumberText>

      <!-- Optional: Expiration Date (SDTC Extension - STU5+) -->
      <sdtc:expirationTime value="20251231" xmlns:sdtc="urn:hl7-org:sdtc"/>
    </manufacturedMaterial>

    <!-- Optional: Manufacturer Organization -->
    <manufacturerOrganization>
      <name>Watson Pharmaceuticals Inc</name>
    </manufacturerOrganization>
  </manufacturedProduct>
</consumable>
```

## Element Details

### manufacturedProduct/@classCode

Fixed value indicating manufactured product role.

| Attribute | Value | Required |
|-----------|-------|----------|
| classCode | MANU | Yes |

### manufacturedProduct/id (0..*)

Business identifiers for the medication product.

| Element | Description |
|---------|-------------|
| @root | OID or UUID identifying the namespace |
| @extension | The actual identifier value |

**Example:**
```xml
<id root="2.16.840.1.113883.3.3489.1.1" extension="MED-12345"/>
```

### manufacturedMaterial (1..1)

**Required element** containing the medication details. SHALL contain exactly one manufacturedMaterial.

#### manufacturedMaterial/code (1..1)

The medication code. **Required element**. SHALL be selected from the Medication Clinical Drug value set.

**Value Set:** Medication Clinical Drug (version 20240606)
**Binding Strength:** Required

**Code Systems:**

| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.6.88 | `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm |
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | NDC (National Drug Code) |
| 2.16.840.1.113883.6.96 | `http://snomed.info/sct` | SNOMED CT |

**RxNorm Term Types (Preferred):**

Medications SHOULD be recorded as **pre-coordinated** codes combining ingredient + strength + dose form:

| Term Type | Description | Example |
|-----------|-------------|---------|
| SCD | Semantic Clinical Drug | "Lisinopril 10 MG Oral Tablet" |
| SBD | Semantic Branded Drug | "Prinivil 10 MG Oral Tablet" |
| GPCK | Generic Pack | "Lisinopril 10 MG Oral Tablet [30 Tablets]" |
| BPCK | Branded Pack | "Prinivil 10 MG Oral Tablet [30 Tablets]" |

**Preferred:** SCD (Semantic Clinical Drug) codes from RxNorm

**Example (RxNorm with NDC translation):**
```xml
<code code="197361" codeSystem="2.16.840.1.113883.6.88"
      codeSystemName="RxNorm"
      displayName="Lisinopril 10 MG Oral Tablet">
  <originalText>
    <reference value="#med1"/>
  </originalText>
  <translation code="00591-3772-01" codeSystem="2.16.840.1.113883.6.69"
               codeSystemName="NDC" displayName="Lisinopril 10mg Tab"/>
</code>
```

**Example (RxNorm SCD):**
```xml
<code code="197806" codeSystem="2.16.840.1.113883.6.88"
      codeSystemName="RxNorm"
      displayName="ibuprofen 600 MG Oral Tablet">
  <translation code="00603402221" codeSystem="2.16.840.1.113883.6.69"
               codeSystemName="NDC"/>
</code>
```

**Example (Text-only for compounded medications):**
```xml
<code nullFlavor="OTH">
  <originalText>Ibuprofen 10% Topical Gel (Compounded)</originalText>
</code>
```

#### manufacturedMaterial/name (0..1)

The name of the medication product as a string.

**Example:**
```xml
<name>Lisinopril 10mg Tablets</name>
```

#### manufacturedMaterial/lotNumberText (0..1)

Lot number or batch identifier for the medication.

**Type:** String

**Example:**
```xml
<lotNumberText>LOT-987654</lotNumberText>
```

#### manufacturedMaterial/sdtc:expirationTime (0..1)

Expiration date for the medication batch. This is an **SDTC (Structured Document Template Content) extension** element.

**Type:** TS (Timestamp)
**Namespace:** `xmlns:sdtc="urn:hl7-org:sdtc"`
**Availability:** C-CDA STU5+ (not available in C-CDA R2.1)

**Example:**
```xml
<sdtc:expirationTime value="20251231" xmlns:sdtc="urn:hl7-org:sdtc"/>
```

**Note:** For C-CDA R2.1 compliance, use only `lotNumberText` for batch tracking. The `sdtc:expirationTime` extension is only available in later versions.

### manufacturerOrganization (0..1)

The organization that manufactures the medication product.

| Element | Type | Description |
|---------|------|-------------|
| name | ON | Manufacturer name |
| telecom | TEL | Contact information |
| addr | AD | Address |

**Example:**
```xml
<manufacturerOrganization>
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

## Conformance Requirements

### Medication Information Template
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.23`
2. **SHALL** contain exactly one `@classCode="MANU"`
3. **MAY** contain zero or more `id` elements
4. **SHALL** contain exactly one `manufacturedMaterial`
5. `manufacturedMaterial` **SHALL** contain exactly one `code`
6. `code` **SHALL** be selected from ValueSet Medication Clinical Drug
7. **MAY** contain zero or one `manufacturerOrganization`
8. If `manufacturedMaterial/code/@nullFlavor` is present, SHALL include `originalText` with medication description

## Key Constraints

| Constraint ID | Severity | Description |
|---------------|----------|-------------|
| product-choice | Error | SHALL contain either manufacturedLabeledDrug OR manufacturedMaterial (mutually exclusive) |
| II-1 | Error | Identifier SHALL contain either @root or @nullFlavor |
| 1098-7411 | Error | SHALL contain exactly [1..1] manufacturedMaterial |
| 1098-16078 | Error | manufacturedMaterial SHALL contain exactly [1..1] code |
| 1098-16079 | Warning | manufacturedMaterial/code SHOULD be from Medication Clinical Drug value set |

## SDTC Extensions

**Note on Version Compatibility:** The `sdtc:expirationTime` element is an SDTC (Structured Document Template Content) extension that is only available in **C-CDA STU5 and later versions**. It is **NOT available in C-CDA R2.1**.

**For C-CDA R2.1 implementations:**
- Use only `manufacturedMaterial/lotNumberText` for batch tracking
- Do not include `sdtc:expirationTime` in your documents

**For C-CDA STU5+ implementations:**
- May optionally use `sdtc:expirationTime` alongside `lotNumberText`
- Must include the SDTC namespace declaration: `xmlns:sdtc="urn:hl7-org:sdtc"`
- Maps to `Medication.batch.expirationDate` in FHIR

**SDTC Namespace Declaration:**
```xml
<ClinicalDocument xmlns:sdtc="urn:hl7-org:sdtc">
  <!-- Document content -->
</ClinicalDocument>
```

## Pre-Coordinated vs Non-Coordinated Codes

**Pre-coordinated (Preferred):**
A single code that includes ingredient + strength + dose form.

```xml
<!-- Pre-coordinated: "Lisinopril 10 MG Oral Tablet" -->
<code code="197361" codeSystem="2.16.840.1.113883.6.88"
      displayName="Lisinopril 10 MG Oral Tablet"/>
```

In this case, the `doseQuantity` in the parent `substanceAdministration` would be a unitless count (e.g., "1 tablet").

**Non-coordinated:**
A code for the ingredient only, without strength or form.

```xml
<!-- Non-coordinated: just "Lisinopril" -->
<code code="29046" codeSystem="2.16.840.1.113883.6.88"
      displayName="Lisinopril"/>
```

In this case, the `doseQuantity` would need physical units (e.g., "10 mg").

**Best Practice:** Use pre-coordinated codes (SCD, SBD, GPCK, BPCK) whenever possible for clarity and interoperability.

## Complete Examples

### Example 1: Standard RxNorm Medication

```xml
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
```

### Example 2: Branded Medication (SBD)

```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
    <manufacturedMaterial>
      <code code="206765" codeSystem="2.16.840.1.113883.6.88"
            codeSystemName="RxNorm"
            displayName="Prinivil 10 MG Oral Tablet">
        <originalText>
          <reference value="#med2"/>
        </originalText>
      </code>
      <name>Prinivil 10mg</name>
    </manufacturedMaterial>
    <manufacturerOrganization>
      <name>Merck Sharp &amp; Dohme Corp</name>
    </manufacturerOrganization>
  </manufacturedProduct>
</consumable>
```

### Example 3: Compounded Medication (Text-Only)

```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
    <manufacturedMaterial>
      <code nullFlavor="OTH">
        <originalText>Ibuprofen 10% Topical Gel (Compounded by pharmacy)</originalText>
      </code>
      <name>Ibuprofen 10% Topical Gel</name>
    </manufacturedMaterial>
  </manufacturedProduct>
</consumable>
```

### Example 4: With NDC as Primary Code

```xml
<consumable>
  <manufacturedProduct classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
    <manufacturedMaterial>
      <code code="00603402221" codeSystem="2.16.840.1.113883.6.69"
            codeSystemName="NDC" displayName="Ibuprofen 600mg Tab">
        <translation code="197806" codeSystem="2.16.840.1.113883.6.88"
                     codeSystemName="RxNorm"
                     displayName="ibuprofen 600 MG Oral Tablet"/>
      </code>
    </manufacturedMaterial>
  </manufacturedProduct>
</consumable>
```

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| manufacturedMaterial/code | Medication Clinical Drug (version 20240606) | Required |
| code/translation | Clinical Substance (optional) | Preferred |

## Usage Context

This template is used within:
- **Medication Activity** (`2.16.840.1.113883.10.20.22.4.16`)
- **Medication Dispense** (`2.16.840.1.113883.10.20.22.4.18`)
- **Medication Supply Order** (`2.16.840.1.113883.10.20.22.4.17`)
- **Planned Medication Activity** (`2.16.840.1.113883.10.20.22.4.42`)

## Documentation Context

Medication Information appears in medication-related sections across various C-CDA document types including Continuity of Care Documents (CCD), Discharge Summaries, Consultation Notes, and Care Plans.

## References

- C-CDA R2.1 Implementation Guide: Medication Information (2.16.840.1.113883.10.20.22.4.23)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationInformation.html
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.23.html
- RxNorm: https://www.nlm.nih.gov/research/umls/rxnorm/
- RxNorm Term Types: https://www.nlm.nih.gov/research/umls/rxnorm/docs/appendix5.html
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
- Medication Clinical Drug Value Set (VSAC): https://vsac.nlm.nih.gov/valueset/2.16.840.1.113762.1.4.1010.4/expansion
- C-CDA Examples: https://github.com/HL7/C-CDA-Examples
