# C-CDA: Performer

## Overview

Performers in C-CDA represent who performed a clinical action. Performers appear at the service event level (care team members) and entry level (who performed specific procedures, observations, or acts).

## Template Information

| Attribute | Value |
|-----------|-------|
| Common Parent Template | US Realm Header (`2.16.840.1.113883.10.20.22.1.1`) |
| Service Event Template | Various (context-dependent) |

## Location in Document

```
ClinicalDocument
├── documentationOf
│   └── serviceEvent
│       └── performer [@typeCode='PRF'] [Service Event Performer]
│           ├── functionCode
│           ├── time
│           └── assignedEntity
│               ├── id
│               ├── code
│               ├── addr
│               ├── telecom
│               ├── assignedPerson
│               │   └── name
│               └── representedOrganization
│
└── component/structuredBody/component/section
    └── entry
        └── [act/observation/procedure]
            └── performer [@typeCode='PRF'] [Entry-Level Performer]
                └── assignedEntity
```

## XML Structure

### Service Event Performer (Care Team)

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

### Entry-Level Performer

```xml
<performer typeCode="PRF">
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
</performer>
```

## Element Details

### performer/@typeCode

| Code | Display | Use |
|------|---------|-----|
| PRF | Performer | Primary performer |
| SPRF | Secondary Performer | Assisting performer |
| PPRF | Primary Performer | Main performer |

### performer/functionCode

The function or role of the performer.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Function code | Yes |
| @codeSystem | `2.16.840.1.113883.5.88` | Yes |
| @displayName | Human-readable display | No |

**Function Codes (ParticipationFunction):**
| Code | Display |
|------|---------|
| PCP | Primary Care Provider |
| ADMPHYS | Admitting Physician |
| ATTPHYS | Attending Physician |
| DISPHYS | Discharging Physician |
| FASST | First Assistant Surgeon |
| MDWF | Midwife |
| NASST | Nurse Assistant |
| RNDPHYS | Rounding Physician |
| SASST | Second Assistant Surgeon |
| SNRS | Scrub Nurse |

### performer/time

The time period during which the performer was involved.

| Element | Description | Required |
|---------|-------------|----------|
| low/@value | Start date/time | No |
| high/@value | End date/time | No |

### assignedEntity/id

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

### assignedEntity/code

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
| Informant | Source of information | When information comes from someone other than author |
| Participant | Other involved parties | Various contexts |

## Conformance Requirements

1. **SHALL** contain exactly one `assignedEntity`
2. `assignedEntity` **SHALL** contain at least one `id`
3. `assignedEntity` **SHOULD** contain `assignedPerson`

## SDTC Extensions

| Extension | Description |
|-----------|-------------|
| sdtc:specialty | Additional provider specialty codes (0..*) - available on assignedEntity |

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| functionCode | ParticipationFunction (v3) | Required |
| assignedEntity/code | Healthcare Provider Taxonomy | Preferred |
| assignedEntity/sdtc:specialty | Practice Setting Code Value Set | Preferred |

## References

- HL7 C-CDA R2.1 Implementation Guide
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- NUCC Healthcare Provider Taxonomy: https://nucc.org/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
