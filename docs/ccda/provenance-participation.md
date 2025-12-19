# C-CDA: Provenance and Participation Elements

## Overview

C-CDA uses participation elements throughout clinical documents to track provenance—who created, performed, verified, or was otherwise involved in clinical information. These participation elements appear at both document and entry levels, providing a comprehensive audit trail of clinical data creation and modification.

## Key Concepts

### Provenance in C-CDA

Provenance in C-CDA is represented through several participation templates and elements:

1. **Provenance - Author Participation**: Records who or what organization created or asserted a clinical statement or section
2. **Provenance - Assembler Participation**: Captures the entity that compiled or assembled the document or section from multiple sources

### Context Conduction

**Critical Concept:** C-CDA uses context conduction where participation information at higher levels (document, section) automatically applies to contained elements unless explicitly overridden.

**Example:**
```
ClinicalDocument/author → applies to all sections and entries
Section/author → overrides document author for this section and its entries
Entry/author → overrides section and document author for this specific entry
```

This differs fundamentally from FHIR, where each resource must have explicit provenance.

## Participation Types

C-CDA defines four primary participation types for tracking provenance:

| Participation | Description | Context |
|---------------|-------------|---------|
| **author** | Humans and/or machines that authored the document/section/entry | Documentation of clinical information |
| **performer** | Person who actually and principally carries out an action | Clinical procedures, observations, acts |
| **informant** | Provides relevant information, such as the parent of a comatose patient | When information source differs from author |
| **participant** | Other participants not explicitly mentioned by other classes | Associated persons, caregivers |

## Provenance - Author Participation

### Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.119` |
| Template Version | 2014-06-09 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/AuthorParticipation` |
| Parent Template | US Realm Header (`2.16.840.1.113883.10.20.22.1.1`) |

### XML Structure

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301103000-0500"/>
  <assignedAuthor>
    <!-- NPI -->
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <!-- Internal ID -->
    <id root="2.16.840.1.113883.19.5.9999.456" extension="2981823"/>

    <!-- Provider Specialty/Type -->
    <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
          displayName="Family Medicine Physician">
      <originalText>Family Medicine</originalText>
    </code>

    <addr use="WP">
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
      <country>US</country>
    </addr>

    <telecom use="WP" value="tel:+1(555)555-1002"/>
    <telecom value="mailto:dr.careful@hospital.org"/>

    <assignedPerson>
      <name>
        <prefix>Dr.</prefix>
        <given>Adam</given>
        <family>Careful</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>

    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
      <telecom use="WP" value="tel:+1(555)555-5000"/>
      <addr use="WP">
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
        <country>US</country>
      </addr>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Element Details

#### author/time

The time when authoring occurred.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @value | Date/time in HL7 format (YYYYMMDD or YYYYMMDDHHMM±ZZZZ) | Yes |

**Note:** The author time may differ from when the document was assembled or transmitted.

#### assignedAuthor

The person, device, or organization responsible for authoring.

| Element | Cardinality | Description |
|---------|------------|-------------|
| id | 1..* | Practitioner/device identifiers |
| code | 0..1 | Provider specialty or type |
| addr | 0..* | Address(es) |
| telecom | 0..* | Contact point(s) |
| assignedPerson | 0..1 | Person who authored (mutually exclusive with assignedAuthoringDevice) |
| assignedAuthoringDevice | 0..1 | Device that authored |
| representedOrganization | 0..1 | Organization on whose behalf |

**Constraint:** MUST contain either `assignedPerson` OR `assignedAuthoringDevice`.

#### assignedAuthor/id

Practitioner or device identifiers.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the assigning authority | Yes |
| @extension | The identifier value | No (if root is UUID) |
| @assigningAuthorityName | Human-readable authority name | No |

**Common OIDs:**
| OID | Description |
|-----|-------------|
| 2.16.840.1.113883.4.6 | US National Provider Identifier (NPI) |
| 2.16.840.1.113883.4.4 | IRS/EIN |

#### assignedAuthor/code

Provider specialty or type code.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Specialty code | Yes |
| @codeSystem | Code system OID | Yes |
| @displayName | Human-readable display | No |

**Code System:** 2.16.840.1.113883.6.101 (Healthcare Provider Taxonomy - NUCC)

**Common NUCC Taxonomy Codes:**
| Code | Display |
|------|---------|
| 207Q00000X | Family Medicine Physician |
| 207R00000X | Internal Medicine Physician |
| 208D00000X | General Practice Physician |
| 207V00000X | Obstetrics & Gynecology Physician |
| 208600000X | Surgery Physician |
| 163W00000X | Registered Nurse |
| 363L00000X | Nurse Practitioner |
| 367500000X | Nurse Anesthetist |

## Provenance - Performer Participation

### Location in Document

Performers appear in two contexts:

1. **Service Event Performer** (documentationOf/serviceEvent/performer): Represents care team members
2. **Entry-Level Performer**: Who performed specific clinical actions

### XML Structure - Service Event Performer

```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20150622"/>
      <high value="20150722"/>
    </effectiveTime>
    <performer typeCode="PRF">
      <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                    displayName="Primary Care Provider">
        <originalText>Primary Care Provider</originalText>
      </functionCode>
      <time>
        <low value="20150622"/>
      </time>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
              displayName="Family Medicine Physician"/>
        <addr use="WP">
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
      </assignedEntity>
    </performer>
  </serviceEvent>
</documentationOf>
```

### Element Details

#### performer/@typeCode

| Code | Display | Use |
|------|---------|-----|
| PRF | Performer | Primary performer |
| SPRF | Secondary Performer | Assisting performer |
| PPRF | Primary Performer | Main performer |

#### performer/functionCode

The function or role of the performer.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Function code | Yes |
| @codeSystem | `2.16.840.1.113883.5.88` (ParticipationFunction) | Yes |
| @displayName | Human-readable display | No |

**Function Codes (ParticipationFunction v3):**
| Code | Display | Description |
|------|---------|-------------|
| PCP | Primary Care Provider | Primary care physician |
| ADMPHYS | Admitting Physician | Physician who admits patient |
| ATTPHYS | Attending Physician | Physician with primary responsibility |
| DISPHYS | Discharging Physician | Physician who discharges patient |
| ANEST | Anesthesist | Provider of anesthesia |
| FASST | First Assistant Surgeon | First surgical assistant |
| MDWF | Midwife | Midwife provider |
| NASST | Nurse Assistant | Nursing assistant |
| RNDPHYS | Rounding Physician | Physician who makes rounds |
| SASST | Second Assistant Surgeon | Second surgical assistant |
| SNRS | Scrub Nurse | Scrub nurse in surgery |
| TASST | Third Assistant | Third assistant in surgery |

#### performer/time

The time period during which the performer was involved.

| Element | Description | Required |
|---------|-------------|----------|
| low/@value | Start date/time | No |
| high/@value | End date/time | No |

## Informant Participation

### Types of Informants

1. **assignedEntity**: Healthcare provider or professional informant
2. **relatedEntity**: Family member, guardian, or non-professional informant

### XML Structure - Related Entity Informant

```xml
<informant>
  <relatedEntity classCode="PRS">
    <code code="MTH" codeSystem="2.16.840.1.113883.5.111"
          displayName="Mother"/>
    <relatedPerson>
      <name>
        <given>Martha</given>
        <family>Ross</family>
      </name>
    </relatedPerson>
  </relatedEntity>
</informant>
```

### Element Details

#### relatedEntity/@classCode

| Code | Display | Use |
|------|---------|-----|
| PRS | Personal Relationship | Family member, friend |
| CAREGIVER | Caregiver | Non-professional caregiver |
| NOK | Next of Kin | Next of kin |
| ECON | Emergency Contact | Emergency contact person |
| GUARD | Guardian | Legal guardian |

#### relatedEntity/code

Relationship to the patient.

**Code System:** 2.16.840.1.113883.5.111 (RoleCode v3)

**Common Relationship Codes:**
| Code | Display |
|------|---------|
| MTH | Mother |
| FTH | Father |
| SPS | Spouse |
| CHILD | Child |
| GUARD | Guardian |
| FRND | Unrelated Friend |
| NBOR | Neighbor |

## Device as Author

When a device (such as an EHR system) is the author:

### XML Structure

```xml
<author>
  <time value="20200301"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Epic EHR</manufacturerModelName>
      <softwareName>Epic 2020</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Element Details

#### assignedAuthoringDevice

| Element | Description | Required |
|---------|-------------|----------|
| manufacturerModelName | Manufacturer and model | Should |
| softwareName | Software name and version | Should |

## Document-Level Participations

### Legal Authenticator

The person who legally authenticates the document.

```xml
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
```

**signatureCode Values:**
| Code | Display |
|------|---------|
| S | Signed |

**Cardinality:** 0..1 (optional, at most one legal authenticator)

### Authenticator

A participant who has attested to the accuracy of the document but does not have privileges to legally authenticate.

```xml
<authenticator>
  <time value="20200302"/>
  <signatureCode code="S"/>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
    <assignedPerson>
      <name>
        <given>Jane</given>
        <family>Resident</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</authenticator>
```

**Cardinality:** 0..* (multiple authenticators allowed)

**Example:** A resident physician who dictates a note and later signs it.

### Data Enterer

The person who entered the data into the system.

```xml
<dataEnterer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="9999999999"/>
    <assignedPerson>
      <name>
        <given>Sarah</given>
        <family>Clerk</family>
      </name>
    </assignedPerson>
  </assignedEntity>
</dataEnterer>
```

**Cardinality:** 0..1 (optional, at most one data enterer per document)

### Custodian

The organization that is in charge of maintaining the document.

```xml
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
```

**Cardinality:** 1..1 (required, exactly one custodian)

**Note:** Per US Realm Header Profile, custodian is mandatory.

## Participation Summary Table

| Participation | Level | Cardinality | Primary Use |
|---------------|-------|-------------|-------------|
| author | Document, Section, Entry | 1..* | Who created/documented |
| performer | Service Event, Entry | 0..* | Who performed action |
| informant | Document, Entry | 0..* | Information source |
| participant | Document, Entry | 0..* | Other involved parties |
| legalAuthenticator | Document | 0..1 | Legal signature |
| authenticator | Document | 0..* | Professional attestation |
| dataEnterer | Document | 0..1 | Data entry person |
| custodian | Document | 1..1 | Document custodian org |

## Author vs Performer vs Informant

| Role | Description | Example |
|------|-------------|---------|
| **Author** | Who created/documented the information | Dr. Smith documents patient's blood pressure reading |
| **Performer** | Who performed the clinical action | Nurse Jones takes the blood pressure |
| **Informant** | Who provided the information | Patient reports their home blood pressure readings |

**Common Scenario:**
- **Performer**: Nurse takes blood pressure
- **Author**: Physician documents the observation in patient record
- **Informant**: Patient reports home readings to nurse

## Conformance Requirements

### Author Participation

1. **SHALL** contain exactly one `time`
2. **SHALL** contain exactly one `assignedAuthor`
3. `assignedAuthor` **SHALL** contain at least one `id`
4. `assignedAuthor` **SHALL** contain exactly one `assignedPerson` OR `assignedAuthoringDevice`
5. Authors **require** `addr`, `telecom`, and either `assignedPerson/name` or `assignedAuthoringDevice/manufacturerModelName`

### Performer Participation

1. **SHALL** contain exactly one `assignedEntity`
2. `assignedEntity` **SHALL** contain at least one `id`
3. `assignedEntity` **SHOULD** contain `assignedPerson`

## Templates Using These Participations

These participation templates are used by 39+ C-CDA templates including:
- Allergy Concern Act
- Care Plan Act
- Problem Observation
- Medication Activity
- Vital Signs Organizer
- Encounter Activity
- Procedure Activity
- Immunization Activity
- Result Observation

## SDTC Extensions

| Extension | Description | Element |
|-----------|-------------|---------|
| sdtc:specialty | Additional provider specialty codes (0..*) | assignedEntity |

**Namespace:** `xmlns:sdtc="urn:hl7-org:sdtc"`

## References

- HL7 C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5): https://build.fhir.org/ig/HL7/CDA-ccda/
- NUCC Healthcare Provider Taxonomy: https://nucc.org/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
- Author Participation Template: http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.119.html
- HL7 v3 RoleCode: http://terminology.hl7.org/CodeSystem/v3-RoleCode
- HL7 v3 ParticipationFunction: http://terminology.hl7.org/CodeSystem/v3-ParticipationFunction
