# C-CDA: Record Target / Patient Role - Provider Organization

## Overview

The provider organization in C-CDA is captured within the `patientRole/providerOrganization` element in the `recordTarget`. This represents the organization responsible for the patient's care or that maintains the patient's record.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.1.1` (US Realm Header) |
| Template Version | 2015-08-01 |
| LOINC Section Code | N/A (Header element) |

## Location in Document

```
ClinicalDocument
└── recordTarget
    └── patientRole
        └── providerOrganization
            ├── id
            ├── name
            ├── telecom
            └── addr
```

## XML Structure

```xml
<recordTarget>
  <patientRole>
    <!-- ... patient information ... -->

    <!-- Provider Organization -->
    <providerOrganization>
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
    </providerOrganization>
  </patientRole>
</recordTarget>
```

## Element Details

### providerOrganization/id (Identifier)

Organization identifiers such as NPI or organizational OIDs.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the organization or assigning authority | Yes |
| @extension | The identifier value | No (if root is UUID) |
| @assigningAuthorityName | Human-readable name of assigning authority | No |

**Common OIDs:**
- `2.16.840.1.113883.4.6` - US National Provider Identifier (NPI)

### providerOrganization/name

The name of the organization as a simple text string.

| Element | Description | Required |
|---------|-------------|----------|
| name | Organization name | No |

### providerOrganization/telecom (Contact Point)

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

**Value Schemes:**
- `tel:` - Telephone number
- `mailto:` - Email address
- `fax:` - Fax number

### providerOrganization/addr (Address)

| Attribute/Element | Description | Required |
|-------------------|-------------|----------|
| @use | Address use code | No |
| streetAddressLine | Street address | No |
| city | City name | No |
| state | State/province | No |
| postalCode | ZIP/postal code | No |
| country | Country code | No |

**Address Use Codes (@use):**
| Code | Display |
|------|---------|
| WP | Work Place |
| DIR | Direct |
| PUB | Public |

## Conformance Requirements

1. `providerOrganization` is **OPTIONAL** within `patientRole`
2. If present, `providerOrganization` **SHOULD** contain at least one `id`
3. If present, `providerOrganization` **SHOULD** contain a `name`

## References

- HL7 C-CDA R2.1 Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
- HL7 V3 Data Types: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=264
