# C-CDA: Record Target / Patient Role - Patient

## Overview

The patient information in C-CDA is captured in the `recordTarget` element within the ClinicalDocument header. This contains the `patientRole` element which holds all patient demographic information.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.1.1` (US Realm Header) |
| Template Version | 2015-08-01 (R2.1), 2024-05-01 (R5.0) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/USRealmHeader` |
| LOINC Section Code | N/A (Header element) |

## Location in Document

```
ClinicalDocument
└── recordTarget
    └── patientRole
        ├── id
        ├── addr
        ├── telecom
        └── patient
            ├── name
            ├── administrativeGenderCode
            ├── birthTime
            ├── maritalStatusCode
            ├── religiousAffiliationCode
            ├── raceCode
            ├── sdtc:raceCode (additional races)
            ├── ethnicGroupCode
            ├── sdtc:ethnicGroupCode (additional ethnicities)
            ├── guardian
            ├── birthplace
            └── languageCommunication
```

## XML Structure

```xml
<recordTarget>
  <patientRole>
    <!-- Patient Identifiers (MRN, SSN, etc.) -->
    <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
    <id root="2.16.840.1.113883.4.1" extension="111-00-2330"/>

    <!-- Address(es) -->
    <addr use="HP">
      <streetAddressLine>1357 Amber Drive</streetAddressLine>
      <city>Beaverton</city>
      <state>OR</state>
      <postalCode>97867</postalCode>
      <country>US</country>
    </addr>

    <!-- Telecom (Phone, Email, etc.) -->
    <telecom use="HP" value="tel:+1(555)555-2003"/>
    <telecom use="MC" value="tel:+1(555)555-2004"/>
    <telecom value="mailto:ellen@email.com"/>

    <patient>
      <!-- Patient Name(s) -->
      <name use="L">
        <given>Ellen</given>
        <given qualifier="CL">Ellie</given>
        <family>Ross</family>
        <suffix qualifier="AC">MD</suffix>
      </name>
      <name use="P">
        <given>Ellen</given>
        <family>Smith</family>
      </name>

      <!-- Administrative Gender -->
      <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"
                                 displayName="Female"/>

      <!-- Birth Time -->
      <birthTime value="19750501"/>

      <!-- Marital Status -->
      <maritalStatusCode code="M" codeSystem="2.16.840.1.113883.5.2"
                         displayName="Married"/>

      <!-- Religious Affiliation -->
      <religiousAffiliationCode code="1013" codeSystem="2.16.840.1.113883.5.1076"
                                 displayName="Christian"/>

      <!-- Race (OMB Categories) -->
      <raceCode code="2106-3" codeSystem="2.16.840.1.113883.6.238"
                displayName="White"/>
      <!-- Additional Race Codes (SDTC Extension) -->
      <sdtc:raceCode code="2076-8" codeSystem="2.16.840.1.113883.6.238"
                     displayName="Native Hawaiian or Other Pacific Islander"/>

      <!-- Ethnicity -->
      <ethnicGroupCode code="2186-5" codeSystem="2.16.840.1.113883.6.238"
                       displayName="Not Hispanic or Latino"/>

      <!-- Guardian -->
      <guardian>
        <code code="POWATT" codeSystem="2.16.840.1.113883.5.111"
              displayName="Power of Attorney"/>
        <addr use="HP">
          <streetAddressLine>1357 Amber Drive</streetAddressLine>
          <city>Beaverton</city>
          <state>OR</state>
          <postalCode>97867</postalCode>
        </addr>
        <telecom use="HP" value="tel:+1(555)555-2005"/>
        <guardianPerson>
          <name>
            <given>Boris</given>
            <family>Ross</family>
          </name>
        </guardianPerson>
      </guardian>

      <!-- Birthplace -->
      <birthplace>
        <place>
          <addr>
            <city>Beaverton</city>
            <state>OR</state>
            <postalCode>97867</postalCode>
            <country>US</country>
          </addr>
        </place>
      </birthplace>

      <!-- Language Communication -->
      <languageCommunication>
        <languageCode code="en"/>
        <modeCode code="ESP" codeSystem="2.16.840.1.113883.5.60"
                  displayName="Expressed spoken"/>
        <proficiencyLevelCode code="G" codeSystem="2.16.840.1.113883.5.61"
                              displayName="Good"/>
        <preferenceInd value="true"/>
      </languageCommunication>
      <languageCommunication>
        <languageCode code="es"/>
        <preferenceInd value="false"/>
      </languageCommunication>
    </patient>
  </patientRole>
</recordTarget>
```

## Element Details

### patientRole/id (Identifier)

Patient identifiers such as Medical Record Number (MRN), Social Security Number, or other organizational identifiers.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the assigning authority | Yes |
| @extension | The identifier value | No (if root is UUID) |
| @assigningAuthorityName | Human-readable name of assigning authority | No |

**Common OIDs:**
- `2.16.840.1.113883.4.1` - US Social Security Number
- `2.16.840.1.113883.4.6` - US National Provider Identifier (NPI)

### patientRole/addr (Address)

| Attribute/Element | Description | Required |
|-------------------|-------------|----------|
| @use | Address use code (HP, WP, TMP, etc.) | No |
| streetAddressLine | Street address | No |
| city | City name | No |
| state | State/province | No |
| postalCode | ZIP/postal code | No |
| country | Country code | No |

**Address Use Codes (@use):**
| Code | Display |
|------|---------|
| HP | Primary Home |
| H | Home |
| WP | Work Place |
| TMP | Temporary |
| BAD | Bad Address |

### patientRole/telecom (Contact Point)

| Attribute | Description | Required |
|-----------|-------------|----------|
| @use | Telecom use code | No |
| @value | Telecom value with scheme prefix | Yes |

**Telecom Use Codes (@use):**
| Code | Display |
|------|---------|
| HP | Primary Home |
| WP | Work Place |
| MC | Mobile Contact |
| EC | Emergency Contact |

**Value Schemes:**
- `tel:` - Telephone number
- `mailto:` - Email address
- `fax:` - Fax number

### patient/name (Human Name)

| Attribute/Element | Description | Required |
|-------------------|-------------|----------|
| @use | Name use code | No |
| prefix | Name prefix (Mr., Dr., etc.) | No |
| given | Given name(s) | No |
| family | Family name | No |
| suffix | Name suffix (Jr., MD, etc.) | No |

**Name Use Codes (@use):**
| Code | Display |
|------|---------|
| L | Legal |
| OR | Official Record |
| P | Pseudonym/Alias |
| A | Artist/Stage |
| C | License |
| ASGN | Assigned |

**Qualifier Codes (@qualifier on given/suffix):**
| Code | Display |
|------|---------|
| CL | Callme (nickname) |
| AC | Academic |
| NB | Nobility |
| PR | Professional |

### patient/administrativeGenderCode

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Gender code | Yes |
| @codeSystem | `2.16.840.1.113883.5.1` | Yes |
| @displayName | Human-readable display | No |

**Gender Codes:**
| Code | Display |
|------|---------|
| M | Male |
| F | Female |
| UN | Undifferentiated |

### patient/birthTime

| Attribute | Description | Required |
|-----------|-------------|----------|
| @value | Birth date in HL7 format (YYYYMMDD or YYYYMMDDHHMM±ZZZZ) | Yes |

### patient/maritalStatusCode

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Marital status code | Yes |
| @codeSystem | `2.16.840.1.113883.5.2` | Yes |
| @displayName | Human-readable display | No |

**Marital Status Codes:**
| Code | Display |
|------|---------|
| A | Annulled |
| D | Divorced |
| I | Interlocutory |
| L | Legally Separated |
| M | Married |
| P | Polygamous |
| S | Never Married |
| T | Domestic Partner |
| U | Unmarried |
| W | Widowed |

### patient/raceCode and sdtc:raceCode

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Race code from CDC Race & Ethnicity | Yes |
| @codeSystem | `2.16.840.1.113883.6.238` | Yes |
| @displayName | Human-readable display | No |

**OMB Race Categories:**
| Code | Display |
|------|---------|
| 1002-5 | American Indian or Alaska Native |
| 2028-9 | Asian |
| 2054-5 | Black or African American |
| 2076-8 | Native Hawaiian or Other Pacific Islander |
| 2106-3 | White |
| 2131-1 | Other Race |

### patient/ethnicGroupCode

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Ethnicity code | Yes |
| @codeSystem | `2.16.840.1.113883.6.238` | Yes |
| @displayName | Human-readable display | No |

**OMB Ethnicity Categories:**
| Code | Display |
|------|---------|
| 2135-2 | Hispanic or Latino |
| 2186-5 | Not Hispanic or Latino |

### patient/languageCommunication

| Element | Description | Required |
|---------|-------------|----------|
| languageCode/@code | Language code (ISO 639) | Yes |
| modeCode | Communication mode (spoken, written, etc.) | No |
| proficiencyLevelCode | Proficiency level | No |
| preferenceInd/@value | Is this the preferred language? | No |

### patient/guardian

| Element | Description | Required |
|---------|-------------|----------|
| code | Relationship code (e.g., POWATT for Power of Attorney) | No |
| addr | Guardian's address | No |
| telecom | Guardian's contact information | No |
| guardianPerson/name | Guardian's name | No |

**Common Guardian Relationship Codes (codeSystem 2.16.840.1.113883.5.111):**
| Code | Display |
|------|---------|
| GUARD | Guardian |
| POWATT | Power of Attorney |
| DPOWATT | Durable Power of Attorney |

### patient/birthplace

| Element | Description | Required |
|---------|-------------|----------|
| place/addr | Address of birthplace | No |

## Conformance Requirements

1. **SHALL** contain exactly one `recordTarget`
2. **SHALL** contain exactly one `patientRole`
3. `patientRole` **SHALL** contain at least one `id`
4. `patientRole` **SHALL** contain exactly one `patient`
5. `patient` **SHALL** contain at least one `name`
6. `patient` **SHALL** contain exactly one `administrativeGenderCode`
7. `patient` **SHALL** contain exactly one `birthTime`
8. `patient` **SHOULD** contain `raceCode` (US Realm)
9. `patient` **SHOULD** contain `ethnicGroupCode` (US Realm)

## USCDI Data Elements

| C-CDA Element | USCDI Data Class/Element |
|---------------|-------------------------|
| patientRole/patient/administrativeGenderCode | Sex (assigned at birth) |
| patientRole/patient/sdtc:sexForClinicalUse | Sex for Clinical Use (R5.0+) |
| patientRole/patient/birthTime | Date of Birth |
| patientRole/patient/raceCode | Race |
| patientRole/patient/sdtc:raceCode | Detailed Race |
| patientRole/patient/ethnicGroupCode | Ethnicity |
| patientRole/patient/sdtc:ethnicGroupCode | Detailed Ethnicity |
| patientRole/patient/languageCommunication | Preferred Language |
| patientRole/addr | Current Address, Previous Address |
| patientRole/telecom | Phone Number, Email Address |
| patientRole/patient/name | First Name, Last Name, Previous Name, Suffix |

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| administrativeGenderCode | Administrative Gender (v3) | Required |
| raceCode | Race Category (CDC) | Required |
| sdtc:raceCode | Race (CDC Race & Ethnicity) | Required |
| ethnicGroupCode | Ethnicity Group (CDC) | Required |
| languageCommunication/languageCode | AllLanguages | Required |
| maritalStatusCode | Marital Status (v3) | Required |
| religiousAffiliationCode | Religious Affiliation (HL7) | Example |

## SDTC Extensions

The following SDTC (Structured Documents Technical Committee) extensions may be used:

| Extension | Description |
|-----------|-------------|
| sdtc:raceCode | Additional race codes beyond the primary race |
| sdtc:ethnicGroupCode | Additional ethnicity codes beyond the primary ethnicity |
| sdtc:sexForClinicalUse | Sex for clinical purposes (R5.0+) |
| sdtc:deceasedInd | Deceased indicator |
| sdtc:deceasedTime | Deceased date/time |
| sdtc:multipleBirthInd | Multiple birth indicator |
| sdtc:multipleBirthOrderNumber | Birth order for multiples |

## References

- HL7 C-CDA R2.1 Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- C-CDA Companion Guide R3: https://www.hl7.org/ccdasearch/
- HL7 V3 Data Types: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=264
