# C-CDA: Clinical Document

## Overview

The C-CDA ClinicalDocument is the root element of all C-CDA documents and serves as a container for the entire document structure, including both document-level metadata and the clinical content organized in sections. When converting to FHIR, the ClinicalDocument maps to two complementary FHIR representations:

1. **Document Bundle (Bundle + Composition)** - For structured conversion where all C-CDA content is converted to FHIR resources and packaged in a Bundle with type="document"
2. **Document Index (DocumentReference)** - For indexing and referencing the original C-CDA document without full conversion

This document focuses on the document structure and metadata elements of ClinicalDocument. For the mapping to these FHIR resources, see:
- Bundle packaging: `docs/fhir/bundle.md` and `docs/mapping/20-bundle.md`
- Composition structure: `docs/fhir/composition.md` and `docs/mapping/19-composition.md`
- DocumentReference indexing: `docs/fhir/document-reference.md`

## Template Information

| Attribute | Value |
|-----------|-------|
| US Realm Header Template ID | `2.16.840.1.113883.10.20.22.1.1` |
| Template Version | 2015-08-01 (R2.1), 2024-05-01 (R5.0) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/USRealmHeader` |
| Root Element | ClinicalDocument |
| Namespace | urn:hl7-org:v3 |
| SDTC Namespace | urn:hl7-org:sdtc |

## Location in Document

```
ClinicalDocument
├── realmCode
├── typeId
├── templateId
├── id
├── code (document type)
├── title
├── effectiveTime
├── confidentialityCode
├── languageCode
├── setId
├── versionNumber
├── recordTarget (patient)
├── author (document author)
├── dataEnterer
├── informant
├── custodian
├── informationRecipient
├── legalAuthenticator
├── authenticator
├── participant
├── documentationOf
├── relatedDocument
└── component (document body)
```

## XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
                  xmlns:sdtc="urn:hl7-org:sdtc"
                  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

  <!-- Realm Code -->
  <realmCode code="US"/>

  <!-- Type ID (fixed) -->
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>

  <!-- Template IDs -->
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <!-- CCD -->
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>

  <!-- Document ID -->
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>

  <!-- Document Type Code (LOINC) -->
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Summarization of Episode Note">
    <translation code="CCD" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Continuity of Care Document"/>
  </code>

  <!-- Document Title -->
  <title>Continuity of Care Document</title>

  <!-- Document Creation Time -->
  <effectiveTime value="20200301102000-0500"/>

  <!-- Confidentiality Code -->
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"
                       displayName="Normal"/>

  <!-- Language Code -->
  <languageCode code="en-US"/>

  <!-- Set ID (for versioning) -->
  <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>

  <!-- Version Number -->
  <versionNumber value="1"/>

  <!-- Patient (recordTarget) -->
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
      <patient>
        <name>
          <given>Ellen</given>
          <family>Ross</family>
        </name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750501"/>
      </patient>
    </patientRole>
  </recordTarget>

  <!-- Document Author -->
  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
            displayName="Family Medicine"/>
      <addr>
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
      </addr>
      <telecom use="WP" value="tel:+1(555)555-1002"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
      <representedOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
      </representedOrganization>
    </assignedAuthor>
  </author>

  <!-- Data Enterer (optional) -->
  <dataEnterer>
    <time value="20200301"/>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
      <assignedPerson>
        <name>
          <given>Jane</given>
          <family>Smith</family>
        </name>
      </assignedPerson>
    </assignedEntity>
  </dataEnterer>

  <!-- Informant (optional) -->
  <informant>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
        </name>
      </assignedPerson>
    </assignedEntity>
  </informant>

  <!-- Custodian (required) -->
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
        <telecom use="WP" value="tel:+1(555)555-5000"/>
        <addr>
          <streetAddressLine>1001 Village Avenue</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <!-- Information Recipient (optional) -->
  <informationRecipient>
    <intendedRecipient>
      <informationRecipient>
        <name>
          <given>Henry</given>
          <family>Sevencare</family>
        </name>
      </informationRecipient>
      <receivedOrganization>
        <name>Good Health Clinic</name>
      </receivedOrganization>
    </intendedRecipient>
  </informationRecipient>

  <!-- Legal Authenticator (optional) -->
  <legalAuthenticator>
    <time value="20200301"/>
    <signatureCode code="S"/>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
        </name>
      </assignedPerson>
    </assignedEntity>
  </legalAuthenticator>

  <!-- Authenticator (optional) -->
  <authenticator>
    <time value="20200301"/>
    <signatureCode code="S"/>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
        </name>
      </assignedPerson>
    </assignedEntity>
  </authenticator>

  <!-- Participant (support, caregiver, etc.) -->
  <participant typeCode="IND">
    <associatedEntity classCode="NOK">
      <code code="MTH" codeSystem="2.16.840.1.113883.5.111" displayName="Mother"/>
      <addr>
        <streetAddressLine>1357 Amber Drive</streetAddressLine>
        <city>Beaverton</city>
        <state>OR</state>
        <postalCode>97867</postalCode>
      </addr>
      <telecom use="HP" value="tel:+1(555)555-2005"/>
      <associatedPerson>
        <name>
          <given>Martha</given>
          <family>Ross</family>
        </name>
      </associatedPerson>
    </associatedEntity>
  </participant>

  <!-- Documentation Of (service event) -->
  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20200101"/>
        <high value="20200301"/>
      </effectiveTime>
      <performer typeCode="PRF">
        <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                      displayName="Primary Care Provider"/>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name>
              <given>Adam</given>
              <family>Careful</family>
            </name>
          </assignedPerson>
        </assignedEntity>
      </performer>
    </serviceEvent>
  </documentationOf>

  <!-- Related Document (optional) -->
  <relatedDocument typeCode="RPLC">
    <parentDocument>
      <id root="2.16.840.1.113883.19.5.99999.1" extension="TT987"/>
      <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>
      <versionNumber value="1"/>
    </parentDocument>
  </relatedDocument>

  <!-- Document Body -->
  <component>
    <structuredBody>
      <!-- Sections go here -->
    </structuredBody>
  </component>

</ClinicalDocument>
```

## Element Details

### Document ID (id)

Unique identifier for this document instance.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID of the assigning authority | Yes |
| @extension | Unique identifier value | No (if root is UUID) |

### Document Type Code (code)

The type of clinical document.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | LOINC document type code | Yes |
| @codeSystem | `2.16.840.1.113883.6.1` (LOINC) | Yes |
| @displayName | Human-readable name | No |

**Common Document Type Codes (LOINC):**
| Code | Display |
|------|---------|
| 34133-9 | Summarization of Episode Note |
| 18842-5 | Discharge Summary |
| 11488-4 | Consultation Note |
| 11504-8 | Surgical Operation Note |
| 11506-3 | Progress Note |
| 28570-0 | Procedure Note |
| 34117-2 | History and Physical Note |
| 57133-1 | Referral Note |
| 34111-5 | Emergency Department Note |
| 57016-8 | Privacy Policy Acknowledgement Document |

### effectiveTime

The document creation date/time.

| Attribute | Description |
|-----------|-------------|
| @value | HL7 timestamp (YYYYMMDDHHMMSS±ZZZZ) |

### confidentialityCode

The confidentiality level of the document.

| Code | Display | Description |
|------|---------|-------------|
| N | Normal | Normal confidentiality |
| R | Restricted | Restricted access |
| V | Very Restricted | Very restricted access |
| L | Low | Low confidentiality |
| M | Moderate | Moderate confidentiality |
| U | Unrestricted | Publicly available |

**Code System:** `2.16.840.1.113883.5.25` (Confidentiality)

### languageCode

The language of the document.

| Attribute | Description |
|-----------|-------------|
| @code | Language code (RFC 5646/BCP 47) |

**Common Language Codes:**
| Code | Display |
|------|---------|
| en-US | English (United States) |
| es | Spanish |
| fr | French |
| de | German |
| zh | Chinese |

### setId and versionNumber

For document versioning.

| Element | Description |
|---------|-------------|
| setId | Identifier for the document set (all versions) |
| versionNumber | Version number within the set |

### author

Who created the document.

| Element | Description | Required |
|---------|-------------|----------|
| time | When authoring occurred | Yes |
| assignedAuthor/id | Author identifier (NPI) | Yes |
| assignedAuthor/code | Author specialty | No |
| assignedAuthor/assignedPerson/name | Author name | No |
| assignedAuthor/representedOrganization | Author's organization | No |

### custodian

Organization responsible for maintaining the document.

| Element | Description | Required |
|---------|-------------|----------|
| representedCustodianOrganization/id | Organization identifier | Yes |
| representedCustodianOrganization/name | Organization name | No |
| representedCustodianOrganization/addr | Organization address | No |
| representedCustodianOrganization/telecom | Organization contact | No |

### legalAuthenticator

Person who legally authenticates the document.

| Element | Description | Required |
|---------|-------------|----------|
| time | Authentication time | Yes |
| signatureCode | S (Signed) | Yes |
| assignedEntity/id | Authenticator identifier | Yes |
| assignedEntity/assignedPerson/name | Authenticator name | No |

### relatedDocument

Relationship to other documents.

| typeCode | Description |
|----------|-------------|
| RPLC | Replaces (new version of) |
| APND | Appends (addendum to) |
| XFRM | Transforms (different format of) |

## Document Templates

### Common C-CDA Document Types

| Template ID | Name |
|-------------|------|
| 2.16.840.1.113883.10.20.22.1.1 | US Realm Header |
| 2.16.840.1.113883.10.20.22.1.2 | Continuity of Care Document (CCD) |
| 2.16.840.1.113883.10.20.22.1.4 | Consultation Note |
| 2.16.840.1.113883.10.20.22.1.8 | Discharge Summary |
| 2.16.840.1.113883.10.20.22.1.9 | Progress Note |
| 2.16.840.1.113883.10.20.22.1.10 | Procedure Note |
| 2.16.840.1.113883.10.20.22.1.13 | Transfer Summary |
| 2.16.840.1.113883.10.20.22.1.14 | Referral Note |
| 2.16.840.1.113883.10.20.22.1.15 | Care Plan |

## Conformance Requirements

### US Realm Header
1. **SHALL** contain exactly one `realmCode` with code="US"
2. **SHALL** contain exactly one `typeId` with root="2.16.840.1.113883.1.3" and extension="POCD_HD000040"
3. **SHALL** contain at least one `templateId` with root="2.16.840.1.113883.10.20.22.1.1"
4. **SHALL** contain exactly one `id`
5. **SHALL** contain exactly one `code`
6. **SHALL** contain exactly one `effectiveTime`
7. **SHALL** contain exactly one `confidentialityCode`
8. **SHALL** contain at least one `recordTarget`
9. **SHALL** contain at least one `author`
10. **SHALL** contain exactly one `custodian`
11. **MAY** contain `legalAuthenticator`
12. **MAY** contain `authenticator`
13. **MAY** contain `documentationOf`
14. **MAY** contain `relatedDocument`

## USCDI Requirements

The following elements support USCDI data requirements:

| Element | USCDI Data Element |
|---------|-------------------|
| recordTarget/patientRole/patient/languageCommunication | Preferred Language |
| participant[@typeCode='IND'][@associatedEntity/@classCode='CAREGIVER'] | Care Team Member |
| participant[@typeCode='IND'][@associatedEntity/@classCode='PRS'] | Related Person |
| dataEnterer | Care Team Member |

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| confidentialityCode | Confidentiality Code (v3) | Required |
| languageCode | AllLanguages | Required |
| realmCode | USRealmCS | Required |

## FHIR Mapping Overview

The ClinicalDocument maps to FHIR in two ways:

### 1. Structured Document Conversion (Bundle + Composition)

When performing a full conversion to FHIR:

**Output:** A FHIR Bundle with `type="document"` containing:
1. **Composition** (first entry) - Document structure and metadata
   - Maps from: Document header elements (id, code, title, effectiveTime, author, custodian, etc.)
   - Contains: Sections with references to converted resources
2. **Patient** - Subject of the document
   - Maps from: `recordTarget/patientRole`
3. **Practitioners** - Authors, attesters
   - Maps from: `author`, `legalAuthenticator`, `authenticator`
4. **Organizations** - Custodian, author organizations
   - Maps from: `custodian`, `author/representedOrganization`
5. **Clinical Resources** - Section entries
   - Maps from: Each `section/entry` to appropriate FHIR resources (Condition, AllergyIntolerance, MedicationRequest, etc.)
6. **Supporting Resources** - Referenced resources
   - Maps from: Resources referenced by clinical resources

**Key Principles:**
- ClinicalDocument → Bundle (container) + Composition (first entry)
- Document header → Composition elements
- Document body (sections) → Composition.section[] with entry references
- All section entries → Individual FHIR resources in Bundle
- Bundle.identifier matches Composition.identifier
- Bundle is immutable and self-contained

**See:**
- `docs/fhir/bundle.md` - FHIR Bundle resource specification
- `docs/fhir/composition.md` - FHIR Composition resource specification
- `docs/mapping/20-bundle.md` - ClinicalDocument to Bundle mapping
- `docs/mapping/19-composition.md` - ClinicalDocument to Composition mapping

### 2. Document Indexing (DocumentReference)

When indexing the C-CDA document without full conversion:

**Output:** A FHIR DocumentReference that:
- Points to the original C-CDA XML document
- Contains document metadata (type, date, author, etc.)
- Provides searchable index for document discovery
- Does not include converted clinical content

**Key Principles:**
- ClinicalDocument header → DocumentReference metadata
- Original C-CDA XML → DocumentReference.content.attachment.data or .url
- Lightweight representation for document management

**See:**
- `docs/fhir/document-reference.md` - DocumentReference resource specification

### Choosing the Approach

| Scenario | Use Bundle + Composition | Use DocumentReference |
|----------|-------------------------|----------------------|
| Need structured FHIR resource access | ✓ | |
| Need to query specific clinical data | ✓ | |
| Building FHIR-native applications | ✓ | |
| C-CDA on FHIR compliance required | ✓ | |
| Document discovery/indexing | | ✓ |
| Preserving original C-CDA format | | ✓ |
| Lightweight document management | | ✓ |
| Both structured and original needed | ✓ | ✓ (complementary) |

## References

- C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- LOINC Document Types: https://loinc.org/
- HL7 V3 Data Types: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=264
- FHIR R4 Bundle: https://hl7.org/fhir/R4/bundle.html
- FHIR R4 Documents: https://hl7.org/fhir/R4/documents.html
- FHIR R4 Composition: https://hl7.org/fhir/R4/composition.html
- C-CDA on FHIR IG: http://hl7.org/fhir/us/ccda/
