# C-CDA: AssignedEntity / AssignedAuthor

## Overview

AssignedEntity is the core structure in C-CDA that contains practitioner details. It appears within both `author/assignedAuthor` and `performer/assignedEntity` elements, representing the person (and optionally their organization) associated with clinical documentation or actions.

## Template Information

| Attribute | Value |
|-----------|-------|
| Common Parent Template | US Realm Header (`2.16.840.1.113883.10.20.22.1.1`) |

## Location in Document

```
ClinicalDocument
├── author
│   └── assignedAuthor [AssignedAuthor]
│       ├── id
│       ├── code (specialty)
│       ├── addr
│       ├── telecom
│       ├── assignedPerson
│       │   └── name
│       └── representedOrganization
│
├── documentationOf/serviceEvent/performer
│   └── assignedEntity [AssignedEntity]
│       ├── id
│       ├── code
│       ├── addr
│       ├── telecom
│       ├── assignedPerson
│       │   └── name
│       └── representedOrganization
│
└── component/structuredBody/component/section/entry/[act|observation|procedure]
    └── performer
        └── assignedEntity [AssignedEntity]
```

## XML Structure

### Full AssignedAuthor Structure

```xml
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
```

### Full AssignedEntity Structure

```xml
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
```

### Minimal AssignedEntity (Entry-Level)

```xml
<assignedEntity>
  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  <addr nullFlavor="UNK"/>
  <telecom nullFlavor="UNK"/>
  <assignedPerson>
    <name>
      <given>Adam</given>
      <family>Careful</family>
    </name>
  </assignedPerson>
</assignedEntity>
```

## Element Details

### id (Identifier)

Practitioner identifiers, typically NPI or organizational IDs.

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

### code (Specialty/Type)

Provider specialty or type code.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Specialty code | Yes |
| @codeSystem | Code system OID | Yes |
| @displayName | Human-readable display | No |
| @codeSystemName | Code system name | No |

**Code Systems:**
| OID | Name | Use |
|-----|------|-----|
| 2.16.840.1.113883.6.101 | Healthcare Provider Taxonomy (NUCC) | Provider specialties |
| 2.16.840.1.113883.6.96 | SNOMED CT | General codes |

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
| 1223G0001X | General Dentist |
| 152W00000X | Optometrist |

### assignedPerson/name

| Element | Description | Required |
|---------|-------------|----------|
| prefix | Name prefix (Dr., Mr., etc.) | No |
| given | Given name(s) | No |
| family | Family name | No |
| suffix | Name suffix (MD, Jr., etc.) | No |

**Qualifier Codes:**
| Code | Display |
|------|---------|
| AC | Academic (MD, PhD) |
| NB | Nobility |
| PR | Professional |
| HON | Honorific |

### addr (Address)

| Element | Description | Required |
|---------|-------------|----------|
| @use | Address use code | No |
| streetAddressLine | Street address | No |
| city | City name | No |
| state | State/province code | No |
| postalCode | ZIP/postal code | No |
| country | Country code | No |

**Address Use Codes:**
| Code | Display |
|------|---------|
| WP | Work Place |
| HP | Primary Home |
| DIR | Direct (office address) |
| PUB | Public |
| TMP | Temporary |

### telecom (Contact Point)

| Attribute | Description | Required |
|-----------|-------------|----------|
| @use | Telecom use code | No |
| @value | Value with scheme prefix | Yes |

**Telecom Use Codes:**
| Code | Display |
|------|---------|
| WP | Work Place |
| DIR | Direct |
| MC | Mobile Contact |
| EC | Emergency Contact |

**Value Schemes:**
- `tel:` - Telephone number
- `mailto:` - Email address
- `fax:` - Fax number

### representedOrganization

The organization the practitioner is associated with.

| Element | Description | Required |
|---------|-------------|----------|
| id | Organization identifier | No |
| name | Organization name | No |
| telecom | Organization contact | No |
| addr | Organization address | No |

## AssignedAuthor vs AssignedEntity

| Element | Context | Child Element |
|---------|---------|---------------|
| assignedAuthor | Within `author` element | `assignedPerson` or `assignedAuthoringDevice` |
| assignedEntity | Within `performer`, `informant`, etc. | `assignedPerson` |

Both structures share the same core elements (id, code, addr, telecom, assignedPerson, representedOrganization).

## Conformance Requirements

### For assignedAuthor
1. **SHALL** contain at least one `id`
2. **SHALL** contain exactly one `assignedPerson` or `assignedAuthoringDevice`

### For assignedEntity
1. **SHALL** contain at least one `id`
2. **SHOULD** contain `assignedPerson`

## SDTC Extensions

| Extension | Description |
|-----------|-------------|
| sdtc:specialty | Additional provider specialty codes (0..*) |

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| code | Healthcare Provider Taxonomy | Preferred |
| sdtc:specialty | Practice Setting Code Value Set | Preferred |

## References

- HL7 C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- NUCC Healthcare Provider Taxonomy: https://nucc.org/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
