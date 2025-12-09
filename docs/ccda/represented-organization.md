# C-CDA: Represented Organization

## Overview

The represented organization in C-CDA captures the organization associated with a practitioner (author or performer). It appears within `assignedAuthor/representedOrganization` and `assignedEntity/representedOrganization` elements.

## Template Information

| Attribute | Value |
|-----------|-------|
| Common Parent Template | US Realm Header (`2.16.840.1.113883.10.20.22.1.1`) |

## Location in Document

```
ClinicalDocument
├── author
│   └── assignedAuthor
│       └── representedOrganization
│           ├── id
│           ├── name
│           ├── telecom
│           └── addr
│
├── documentationOf/serviceEvent/performer
│   └── assignedEntity
│       └── representedOrganization
│           ├── id
│           ├── name
│           ├── telecom
│           └── addr
│
└── component/structuredBody/component/section/entry/[act|observation|procedure]
    └── performer
        └── assignedEntity
            └── representedOrganization
```

## XML Structure

### Full Represented Organization

```xml
<representedOrganization>
  <id root="2.16.840.1.113883.19.5.9999.1393"/>
  <id root="2.16.840.1.113883.4.6" extension="1234567893"/>
  <name>Community Health and Hospitals</name>
  <telecom use="WP" value="tel:+1(555)555-5000"/>
  <telecom value="mailto:info@communityhospital.org"/>
  <addr use="WP">
    <streetAddressLine>1001 Village Avenue</streetAddressLine>
    <city>Portland</city>
    <state>OR</state>
    <postalCode>99123</postalCode>
    <country>US</country>
  </addr>
</representedOrganization>
```

### Minimal Represented Organization

```xml
<representedOrganization>
  <id root="2.16.840.1.113883.19.5.9999.1393"/>
  <name>Community Health and Hospitals</name>
</representedOrganization>
```

## Element Details

### id (Identifier)

Organization identifiers such as NPI or organizational OIDs.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the organization or assigning authority | Yes |
| @extension | The identifier value | No (if root is UUID) |
| @assigningAuthorityName | Human-readable name of assigning authority | No |

**Common OIDs:**
| OID | Description |
|-----|-------------|
| 2.16.840.1.113883.4.6 | US National Provider Identifier (NPI) |
| 2.16.840.1.113883.4.2 | US Employer Identification Number (EIN) |

### name

The name of the organization as a simple text string.

| Element | Description | Required |
|---------|-------------|----------|
| name | Organization name | No |

### telecom (Contact Point)

| Attribute | Description | Required |
|-----------|-------------|----------|
| @use | Telecom use code | No |
| @value | Telecom value with scheme prefix | Yes |

**Telecom Use Codes (@use):**
| Code | Display |
|------|---------|
| WP | Work Place |
| DIR | Direct |
| PUB | Public |
| MC | Mobile Contact |

**Value Schemes:**
- `tel:` - Telephone number
- `mailto:` - Email address
- `fax:` - Fax number

### addr (Address)

| Element | Description | Required |
|---------|-------------|----------|
| @use | Address use code | No |
| streetAddressLine | Street address | No |
| city | City name | No |
| state | State/province code | No |
| postalCode | ZIP/postal code | No |
| country | Country code | No |

**Address Use Codes (@use):**
| Code | Display |
|------|---------|
| WP | Work Place |
| DIR | Direct |
| PUB | Public |

## Represented Organization vs Provider Organization

| Element | Context | Purpose |
|---------|---------|---------|
| representedOrganization | Within assignedAuthor/assignedEntity | Organization the practitioner represents |
| providerOrganization | Within patientRole | Organization providing care to the patient |

## Conformance Requirements

1. `representedOrganization` is **OPTIONAL** within `assignedAuthor` and `assignedEntity`
2. If present, `representedOrganization` **SHOULD** contain at least one `id`
3. If present, `representedOrganization` **SHOULD** contain a `name`

## References

- HL7 C-CDA R2.1 Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
- HL7 V3 Data Types: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=264
