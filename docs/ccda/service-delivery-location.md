# C-CDA: Service Delivery Location

## Overview

The Service Delivery Location template represents the physical place of available services or resources. It is the location of a service event where an act, observation, or procedure took or can take place. This template is used within various clinical statements (such as Encounter Activity, Procedure Activity, and Planned Encounter) to specify where healthcare services were or will be delivered.

Service Delivery Location captures the facility name, facility identifiers (such as NPI, CLIA), facility type/classification, and physical address. It represents both permanent facilities (hospitals, clinics) and temporary/mobile locations (ambulances, patient homes).

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID (OID) | `2.16.840.1.113883.10.20.22.4.32` |
| Template Extension | No extension attribute (template has no version-specific extension) |
| Specification Version | v5.0.0-ballot (STU5 Ballot 1) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ServiceDeliveryLocation` |
| Parent Template | CDA ParticipantRole |
| Status | Draft as of 2025-12-12 (marked as "New Content" in v5.0.0-ballot) |
| Computable Name | ServiceDeliveryLocation |

## USCDI Data Elements

The following elements are designated as USCDI (United States Core Data for Interoperability) elements:

| USCDI Element | C-CDA Element |
|---------------|---------------|
| Facility Name | participantRole/playingEntity/name |
| Facility Type | participantRole/code |
| Facility Identifier | participantRole/id |
| Facility Address | participantRole/addr |

**USCDI Requirement:** To conform with USCDI requirements, certifying systems shall support either HSLOC codes or SNOMED CT codes for facility type. Inclusion of CMS POS codes is optional and may be used to meet billing or administrative needs.

## Context and Usage

Service Delivery Location appears in the following contexts:

1. **Encounter Activity** (`participant[@typeCode='LOC']`) - Where the encounter occurred
2. **Procedure Activity** (`participant[@typeCode='LOC']`) - Where the procedure was performed
3. **Planned Encounter** (`participant[@typeCode='LOC']`) - Where the planned encounter will occur
4. **encompassingEncounter** (header) - Document-level encounter location (uses healthCareFacility structure, not this template)

**Note:** The encompassingEncounter/location uses a similar but distinct structure (healthCareFacility) and does not use this template ID.

## XML Structure

### Basic Structure

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <!-- Facility Identifiers (0..*) - USCDI: Facility Identifier -->
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <id root="2.16.840.1.113883.4.7" extension="11D0265516"/>

    <!-- Facility Type (1..1) - USCDI: Facility Type -->
    <code code="1061-3" codeSystem="2.16.840.1.113883.6.259"
          displayName="Hospital"/>

    <!-- Facility Address (0..1) - USCDI: Facility Address -->
    <addr use="WP">
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
      <country>US</country>
    </addr>

    <!-- Contact Information (0..*) -->
    <telecom use="WP" value="tel:+1(555)555-5000"/>
    <telecom use="WP" value="mailto:info@hospital.example.org"/>

    <!-- Playing Entity (1..1) -->
    <playingEntity classCode="PLC">
      <!-- Facility Name (1..1) - USCDI: Facility Name -->
      <name>Community Health and Hospitals</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 1: Hospital Location with Multiple Identifiers

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <!-- NPI Identifier -->
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>

    <!-- CLIA Identifier -->
    <id root="2.16.840.1.113883.4.7" extension="11D0265516"/>

    <!-- NAIC Identifier -->
    <id root="2.16.840.1.113883.6.300" extension="98765"/>

    <!-- HSLOC Code for Hospital -->
    <code code="1061-3" codeSystem="2.16.840.1.113883.6.259"
          displayName="Hospital">
      <!-- Optional translation to SNOMED CT -->
      <translation code="22232009" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Hospital"/>
      <!-- Optional translation to CMS Place of Service -->
      <translation code="21" codeSystem="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set"
                   displayName="Inpatient Hospital"/>
    </code>

    <addr use="WP">
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <streetAddressLine>Building 1, South Wing</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
      <country>US</country>
    </addr>

    <telecom use="WP" value="tel:+1(555)555-5000"/>
    <telecom use="WP" value="fax:+1(555)555-5001"/>
    <telecom use="WP" value="mailto:contact@hospital.example.org"/>

    <playingEntity classCode="PLC">
      <name>Community Health and Hospitals</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 2: Emergency Department

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>

    <code code="1118-1" codeSystem="2.16.840.1.113883.6.259"
          displayName="Emergency Department"/>

    <addr use="WP">
      <streetAddressLine>500 University Avenue</streetAddressLine>
      <city>Boston</city>
      <state>MA</state>
      <postalCode>02101</postalCode>
    </addr>

    <telecom use="WP" value="tel:+1(617)555-1234"/>

    <playingEntity classCode="PLC">
      <name>Boston General Emergency Department</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 3: Urgent Care Center

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <id root="2.16.840.1.113883.4.6" extension="1122334455"/>

    <code code="1160-1" codeSystem="2.16.840.1.113883.6.259"
          displayName="Urgent Care Center">
      <!-- CMS Place of Service for billing -->
      <translation code="20" codeSystem="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set"
                   displayName="Urgent Care Facility"/>
    </code>

    <addr use="WP">
      <streetAddressLine>123 Main Street</streetAddressLine>
      <city>Springfield</city>
      <state>IL</state>
      <postalCode>62701</postalCode>
    </addr>

    <telecom use="WP" value="tel:+1(217)555-9999"/>

    <playingEntity classCode="PLC">
      <name>Springfield Urgent Care</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 4: Ambulatory Clinic

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <id root="2.16.840.1.113883.4.6" extension="5566778899"/>

    <code code="1117-3" codeSystem="2.16.840.1.113883.6.259"
          displayName="Ambulatory Primary Care Clinic">
      <translation code="394802001" codeSystem="2.16.840.1.113883.6.96"
                   displayName="General medicine"/>
    </code>

    <addr use="WP">
      <streetAddressLine>789 Health Plaza</streetAddressLine>
      <streetAddressLine>Suite 200</streetAddressLine>
      <city>Denver</city>
      <state>CO</state>
      <postalCode>80202</postalCode>
    </addr>

    <telecom use="WP" value="tel:+1(303)555-7777"/>

    <playingEntity classCode="PLC">
      <name>Denver Family Medicine Clinic</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 5: Patient's Home (Home Health Visit)

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <!-- Patient's home may not have facility identifier -->
    <id nullFlavor="NA"/>

    <code code="PTRES" codeSystem="2.16.840.1.113883.5.111"
          displayName="Patient's Residence">
      <translation code="12" codeSystem="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set"
                   displayName="Home"/>
    </code>

    <!-- Patient's home address -->
    <addr use="HP">
      <streetAddressLine>456 Oak Street</streetAddressLine>
      <city>Seattle</city>
      <state>WA</state>
      <postalCode>98101</postalCode>
    </addr>

    <playingEntity classCode="PLC">
      <name>Patient's Home</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Example 6: Mobile Clinic/Ambulance

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <id root="2.16.840.1.113883.4.6" extension="9988776655"/>

    <code code="AMB" codeSystem="2.16.840.1.113883.5.111"
          displayName="Ambulance">
      <translation code="41" codeSystem="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set"
                   displayName="Ambulance - Land"/>
    </code>

    <!-- Mobile unit may have organization address, not current physical location -->
    <addr use="WP">
      <streetAddressLine>Emergency Services Department</streetAddressLine>
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
    </addr>

    <telecom use="WP" value="tel:+1(555)555-9111"/>

    <playingEntity classCode="PLC">
      <name>Community Health Ambulance Unit 5</name>
    </playingEntity>
  </participantRole>
</participant>
```

## Element Details

### participant (Container)

| Attribute | Value | Required |
|-----------|-------|----------|
| @typeCode | LOC | Yes (fixed) |

**Conformance:** This template is contained within a `participant` element with `typeCode="LOC"` (location).

### participantRole (Root Element)

| Attribute | Value | Required |
|-----------|-------|----------|
| @classCode | SDLOC | Yes (fixed) |

**Cardinality:** 1..1

**SDLOC** = Service Delivery Location

### participantRole/templateId

| Attribute | Value | Required |
|-----------|-------|----------|
| @root | 2.16.840.1.113883.10.20.22.4.32 | Yes |

**Cardinality:** 1..1

### participantRole/id (Facility Identifier)

Unique identifier(s) for the healthcare facility. USCDI element.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID for identifier system | Yes |
| @extension | Identifier value | No |
| @nullFlavor | Reason for absence (NA, NI, UNK) | No |

**Cardinality:** 0..*

**SHOULD be present:** Address SHOULD be provided when available.

**Identifier Type Slices:**

Three specific identifier types are defined:

1. **NPI (National Provider Identifier)**
   - Root: `2.16.840.1.113883.4.6`
   - Used for facilities with NPI registration
   - Cardinality: 0..*

2. **CLIA (Clinical Laboratory Improvement Amendments)**
   - Root: `2.16.840.1.113883.4.7`
   - Used for laboratories
   - Cardinality: 0..*

3. **NAIC (National Association of Insurance Commissioners)**
   - Root: `2.16.840.1.113883.6.300`
   - Used for insurance-related facility identification
   - Cardinality: 0..*

**Note:** A location may have multiple identifiers from different systems.

### participantRole/code (Facility Type)

The type/classification of the healthcare facility. USCDI element.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Facility type code | Yes |
| @codeSystem | Code system OID | Yes |
| @displayName | Human-readable display | No |
| translation | Additional codes from other systems | No |

**Cardinality:** 1..1 (Required)

**Value Set:** Healthcare Service Location Type Combined (VSAC OID: 2.16.840.1.113762.1.4.1267.31)

**Binding Strength:** Preferred

**USCDI Conformance Constraint:** Code must belong to one of three value sets:
1. NHSN Healthcare Facility Patient Care Location (HSLOC) - USCDI-compliant
2. SNOMED CT location types - USCDI-compliant
3. CMS Place of Service (POS) codes - Optional for billing

**SHALL use one binding:** Systems SHALL use codes from at least one of the approved value sets.

#### Primary Code System: HSLOC (HealthcareServiceLocation)

**Code System OID:** `2.16.840.1.113883.6.259`

**Common HSLOC Codes:**

| Code | Display | Description |
|------|---------|-------------|
| 1061-3 | Hospital | General hospital facility |
| 1118-1 | Emergency Department | Emergency room/department |
| 1160-1 | Urgent Care Center | Urgent care facility |
| 1116-5 | Ambulatory Surgical Center | Outpatient surgery center |
| 1117-3 | Ambulatory Primary Care Clinic | Primary care clinic |
| 1242-9 | Outpatient Clinic | General outpatient clinic |
| 1021-7 | Critical Care Unit | ICU/CCU |
| 1108-2 | Operating Room | Surgical operating room |
| 1023-3 | Inpatient Medical Ward | Medical ward |
| 1024-1 | Inpatient Surgical Ward | Surgical ward |
| 1025-8 | Inpatient Pediatric Ward | Pediatric ward |
| 1026-6 | Inpatient Obstetric Ward | Obstetric/maternity ward |
| 1027-4 | Inpatient Psychiatric Ward | Psychiatric ward |
| 1028-2 | Rehabilitation Unit | Rehab unit |
| 1029-0 | Labor and Delivery | Labor and delivery unit |
| 1033-2 | Pediatric Critical Care | Pediatric ICU |
| 1034-0 | Neonatal Critical Care | NICU |
| 1035-7 | Burn Unit | Burn treatment unit |
| 1200-7 | Long Term Care | Nursing home/LTC facility |
| 1250-2 | Pharmacy | Hospital or retail pharmacy |
| 1251-0 | Radiology | Radiology/imaging department |
| 1252-8 | Laboratory | Clinical laboratory |

#### Alternative Code System: SNOMED CT

**Code System OID:** `2.16.840.1.113883.6.96`

**Common SNOMED CT Location Codes:**

| Code | Display |
|------|---------|
| 22232009 | Hospital |
| 225728007 | Accident and Emergency department |
| 309904001 | Intensive care unit |
| 309914001 | Operating theater |
| 225746001 | Patient room |
| 702871004 | Infusion clinic |
| 309939001 | Palliative care unit |
| 394802001 | General medicine |
| 309905002 | Coronary care unit |

#### Optional Code System: CMS Place of Service

**Code System URI:** `https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set`

**Common CMS POS Codes:**

| Code | Display | Description |
|------|---------|-------------|
| 11 | Office | Physician office |
| 12 | Home | Patient's home |
| 21 | Inpatient Hospital | Inpatient acute care |
| 22 | On Campus-Outpatient Hospital | Hospital outpatient |
| 23 | Emergency Room – Hospital | Hospital ER |
| 24 | Ambulatory Surgical Center | ASC |
| 31 | Skilled Nursing Facility | SNF |
| 32 | Nursing Facility | NF |
| 20 | Urgent Care Facility | Urgent care |
| 41 | Ambulance - Land | Land ambulance |
| 49 | Independent Clinic | Freestanding clinic |
| 50 | Federally Qualified Health Center | FQHC |
| 71 | Public Health Clinic | Public health |

#### Alternative Code System: RoleCode (v3)

**Code System OID:** `2.16.840.1.113883.5.111`

**Common RoleCode Values:**

| Code | Display | Description |
|------|---------|-------------|
| PTRES | Patient's Residence | Patient's home |
| AMB | Ambulance | Mobile emergency vehicle |
| PHARM | Pharmacy | Pharmacy |
| HOSP | Hospital | Hospital facility |

### participantRole/addr (Facility Address)

The physical address of the facility. USCDI element.

| Element | Cardinality | Description |
|---------|-------------|-------------|
| @use | 0..1 | Address use (HP, WP, TMP, etc.) |
| streetAddressLine | 0..* | Street address components |
| city | 0..1 | City name |
| state | 0..1 | State abbreviation |
| postalCode | 0..1 | ZIP code |
| country | 0..1 | Country code or name |

**Cardinality:** 0..1

**SHOULD be present:** Address SHOULD be provided when available.

**Data Type:** USRealmAddress (US-specific address formatting)

**Address Use Codes:**
| Code | Display |
|------|---------|
| HP | Primary Home |
| WP | Work Place |
| TMP | Temporary Address |
| BAD | Bad Address |
| PHYS | Physical Visit Address |
| PST | Postal Address |

### participantRole/telecom (Contact Information)

Contact information for the facility.

| Attribute | Description | Values |
|-----------|-------------|--------|
| @use | Telecom use | HP, WP, MC, etc. |
| @value | Contact value | URI (tel:, mailto:, fax:, http:) |

**Cardinality:** 0..*

**SHOULD be present:** Telecom SHOULD be provided when available.

**Telecom URI Schemes:**
- `tel:` - Telephone number
- `fax:` - Fax number
- `mailto:` - Email address
- `http:` or `https:` - Website URL

**Examples:**
- `tel:+1(555)555-5000`
- `fax:+1(555)555-5001`
- `mailto:info@hospital.example.org`
- `http://www.hospital.example.org`

### playingEntity (Facility Details)

Container for the facility name and additional entity details.

| Attribute | Value | Required |
|-----------|-------|----------|
| @classCode | PLC | Yes (fixed) |

**Cardinality:** 1..1 (Required)

**PLC** = Place

### playingEntity/name (Facility Name)

The name of the facility as it is commonly known. USCDI element.

| Type | Description |
|------|-------------|
| PN (Person Name) or EN (Entity Name) | Facility name |

**Cardinality:** 1..1 (Required)

**Examples:**
- "Community Health and Hospitals"
- "Springfield Urgent Care"
- "Boston General Emergency Department"
- "Patient's Home"

### SDTC Extensions (Optional)

The template supports optional SDTC (Structured Data Capture) extensions:

#### sdtcIdentifiedBy

Additional identifier metadata using the IdentifiedBy extension.

**Cardinality:** 0..*

#### sdtc:specialty

Clinical specialty codes for the facility.

| Element | Description |
|---------|-------------|
| @code | Specialty code |
| @codeSystem | Code system OID |
| @displayName | Specialty name |

**Cardinality:** 0..*

**Value Set:** Healthcare Provider Taxonomy (NUCC) or Practice Setting Code Value Set

## Conformance Requirements

### Service Delivery Location Template

1. **SHALL** contain exactly one `templateId` with `@root="2.16.840.1.113883.10.20.22.4.32"`
2. **SHALL** have `participantRole/@classCode="SDLOC"`
3. **SHALL** contain exactly one `code` (facility type)
4. **SHALL** contain exactly one `playingEntity` with `@classCode="PLC"`
5. **SHALL** contain exactly one `playingEntity/name` (facility name)
6. **SHOULD** contain at least one `id` (facility identifier)
7. **SHOULD** contain `addr` (facility address)
8. **SHOULD** contain at least one `telecom` (contact information)
9. **MAY** contain `sdtc:identifiedBy` extensions
10. **MAY** contain `sdtc:specialty` extensions

### Constraint Identifiers

| Constraint ID | Level | Description |
|---------------|-------|-------------|
| should-addr | Warning | Address SHOULD be present |
| should-telecom | Warning | Telecom SHOULD be present |
| shall-use-one-binding | Error | Code must belong to one of three value sets (HSLOC, SNOMED CT, or CMS POS) |
| role-choice | Error | playingDevice and playingEntity are mutually exclusive |
| II-1 | Error | Identifier instances must have either root or nullFlavor |

## Relationship to encompassingEncounter/location

**Important Distinction:** The encompassingEncounter/location element in the CDA header uses a different structure (healthCareFacility) and does NOT use this template ID. However, the semantic meaning and data elements are similar.

### encompassingEncounter/location Structure

```xml
<componentOf>
  <encompassingEncounter>
    <location>
      <healthCareFacility>
        <!-- Similar elements but different structure -->
        <id root="..."/>
        <code code="..." codeSystem="..."/>
        <location>
          <name>Facility Name</name>
          <addr>...</addr>
        </location>
        <serviceProviderOrganization>
          <name>Organization Name</name>
        </serviceProviderOrganization>
      </healthCareFacility>
    </location>
  </encompassingEncounter>
</componentOf>
```

### Service Delivery Location in Encounter Activity

```xml
<encounter>
  <participant typeCode="LOC">
    <participantRole classCode="SDLOC">
      <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
      <!-- Uses this template -->
    </participantRole>
  </participant>
</encounter>
```

Both structures represent the same semantic concept (facility location) but use different CDA constructs.

## Related Templates

| Template | OID | Purpose |
|----------|-----|---------|
| Encounter Activity | 2.16.840.1.113883.10.20.22.4.49 | Contains Service Delivery Location |
| Procedure Activity Procedure | 2.16.840.1.113883.10.20.22.4.14 | Contains Service Delivery Location |
| Planned Encounter | 2.16.840.1.113883.10.20.22.4.40 | Contains Service Delivery Location |

## Implementation Notes

1. **Multiple Locations:** An Encounter or Procedure may have multiple location participants if the patient moved during the event (e.g., ER → Operating Room → Recovery Room).

2. **Identifier Availability:** Not all locations have formal identifiers (e.g., patient's home). Use `@nullFlavor="NA"` when identifier is not applicable.

3. **Code Selection:** Systems should select the most specific applicable code from the preferred value sets. HSLOC codes are preferred for USCDI compliance.

4. **Address Formatting:** Follow US Realm address formatting with separate streetAddressLine elements for each line.

5. **Telecom Formatting:** Use proper URI schemes (tel:, mailto:, fax:) and include country codes for phone numbers.

6. **Translation Codes:** It is acceptable and encouraged to include multiple code systems using translation elements to support interoperability with different systems (HSLOC for USCDI, CMS POS for billing).

7. **SDTC Extensions:** While SDTC extensions are supported, they are optional and should only be used when the standard CDA elements are insufficient.

## References

- HL7 C-CDA R2.1 Implementation Guide
- HL7 C-CDA v5.0.0-ballot Specification: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ServiceDeliveryLocation.html
- VSAC (Value Set Authority Center): https://vsac.nlm.nih.gov/
- NHSN Healthcare Facility Patient Care Location (HSLOC): https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html
- CMS Place of Service Codes: https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set
- SNOMED CT: http://snomed.info/sct
