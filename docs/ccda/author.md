# C-CDA: Author

## Overview

Authors in C-CDA represent who documented or created clinical information. Authors appear at both the document level (who authored the document) and entry level (who documented specific clinical entries like observations or procedures).

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.119` |
| Template Version | 2014-06-09 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/AuthorParticipation` |
| Parent Template | US Realm Header (`2.16.840.1.113883.10.20.22.1.1`) |

## Authorship Propagation

Authorship propagates to contained sections and entries, unless explicitly overridden. This means that if an author is specified at the document level, all entries within that document are considered to have that author unless a specific entry overrides it with its own author element.

## Location in Document

```
ClinicalDocument
├── author [Document Author]
│   ├── templateId
│   ├── time
│   └── assignedAuthor
│       ├── id
│       ├── code (specialty)
│       ├── addr
│       ├── telecom
│       ├── assignedPerson
│       │   └── name
│       └── representedOrganization
│
└── component/structuredBody/component/section
    └── entry
        └── [act/observation/procedure]
            └── author [Entry-Level Author]
                ├── templateId
                ├── time
                └── assignedAuthor
```

## XML Structure

### Document Author

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20150722"/>
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

### Entry-Level Author

```xml
<observation classCode="OBS" moodCode="EVN">
  <!-- ... observation content ... -->
  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20150722103000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name>
          <given>Adam</given>
          <family>Careful</family>
        </name>
      </assignedPerson>
    </assignedAuthor>
  </author>
</observation>
```

## Element Details

### author/time

The time when authoring occurred.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @value | Date/time in HL7 format (YYYYMMDD or YYYYMMDDHHMM±ZZZZ) | Yes |

### assignedAuthor/id

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

### assignedAuthor/code

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

## Author vs Performer

| Role | Description | Context |
|------|-------------|---------|
| Author | Who created/documented the information | Documentation of clinical information |
| Performer | Who performed the clinical action | Procedures, observations, acts |

## Conformance Requirements

1. **SHALL** contain exactly one `time`
2. **SHALL** contain exactly one `assignedAuthor`
3. `assignedAuthor` **SHALL** contain at least one `id`
4. `assignedAuthor` **SHALL** contain exactly one `assignedPerson` or `assignedAuthoringDevice`
5. Authors **require** `addr`, `telecom`, and either `assignedPerson/name` or `assignedAuthoringDevice/manufacturerModelName`. These details may exist on the author itself or reference another author instance elsewhere in the document.

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| assignedAuthor/code | Healthcare Provider Taxonomy | Preferred |
| assignedAuthor/sdtc:specialty | Practice Setting Code Value Set | Preferred |

## Templates Using Author Participation

This template is used by 39+ templates including:
- Allergy Concern Act
- Care Plan Act
- Problem Observation
- Medication Activity
- Vital Signs Organizer
- Encounter Activity
- Procedure Activity
- Immunization Activity
- Result Observation

## References

- HL7 C-CDA R2.1 Implementation Guide
- NUCC Healthcare Provider Taxonomy: https://nucc.org/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
