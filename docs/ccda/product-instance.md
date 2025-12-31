# C-CDA: Product Instance

## Overview

The Product Instance template represents a specific device used in patient care, such as devices implanted in patients or used as part of procedures or other acts. This template enables tracking of unique device identifiers, particularly supporting the FDA Unique Device Identification (UDI) System. It allows documentation of not just *that* a device was used or implanted, but *which specific* device with its unique serial number.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.4.37` |
| Template Version | Multiple versions (see C-CDA releases) |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ProductInstance` |
| Parent Template | N/A (Used within other templates) |
| Status | Active |

## Context of Use

The Product Instance template is used within:
- **Procedure Activity Procedure** - Devices used during procedures
- **Non-Medicinal Supply Activity** - Devices provided to patients
- **Planned Supply** - Devices planned for future use
- **Participant elements** - Devices participating in clinical acts

## Location in Document

```
ClinicalDocument
└── component/structuredBody/component/section
    └── entry
        └── [procedure/supply/...]
            └── participant (typeCode="DEV")
                └── participantRole (Product Instance)
                    ├── templateId
                    ├── id (device identifier)
                    ├── playingDevice
                    │   └── code
                    └── scopingEntity
                        └── id (manufacturer)
```

## XML Structure

### Basic Product Instance

```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
    <id root="2.16.840.1.113883.3.3719"
        extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
        assigningAuthorityName="FDA"/>
    <playingDevice>
      <code code="14106009" codeSystem="2.16.840.1.113883.6.96"
            displayName="Cardiac pacemaker">
        <originalText>Pacemaker Model XYZ</originalText>
      </code>
    </playingDevice>
    <scopingEntity>
      <id root="2.16.840.1.113883.3.3719"/>
    </scopingEntity>
  </participantRole>
</participant>
```

### Product Instance with UDI Components

```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>

    <!-- Full UDI -->
    <id root="2.16.840.1.113883.3.3719"
        extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
        assigningAuthorityName="FDA"/>

    <!-- Device Identifier (DI) only -->
    <id root="2.16.840.1.113883.3.3719"
        extension="51022222233336"/>

    <playingDevice>
      <code code="90412006" codeSystem="2.16.840.1.113883.6.96"
            displayName="Colonoscope"/>
    </playingDevice>

    <scopingEntity>
      <id root="2.16.840.1.113883.3.3719"/>
      <desc>Olympus Medical Systems</desc>
    </scopingEntity>
  </participantRole>
</participant>
```

### Product Instance in Procedure

```xml
<procedure classCode="PROC" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
  <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
  <code code="80146002" codeSystem="2.16.840.1.113883.6.96"
        displayName="Appendectomy"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315"/>

  <!-- Device participant -->
  <participant typeCode="DEV">
    <participantRole classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
      <id root="2.16.840.1.113883.3.3719"
          extension="(01)00643169001763(17)180322(10)M320(21)AC221"/>
      <playingDevice>
        <code code="257327003" codeSystem="2.16.840.1.113883.6.96"
              displayName="Orthopedic implant"/>
      </playingDevice>
      <scopingEntity>
        <id root="2.16.840.1.113883.3.3719"/>
      </scopingEntity>
    </participantRole>
  </participant>
</procedure>
```

### Product Instance with Model Name

```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
    <id root="2.16.840.1.113883.19.321" extension="SN-12345"/>
    <playingDevice>
      <code code="87405001" codeSystem="2.16.840.1.113883.6.96"
            displayName="Cane"/>
      <manufacturerModelName>Standard Walker Model 2020</manufacturerModelName>
    </playingDevice>
    <scopingEntity>
      <id root="2.16.840.1.113883.19.321"/>
      <desc>Mobility Aids Inc</desc>
    </scopingEntity>
  </participantRole>
</participant>
```

## Element Details

### participant

The wrapper element indicating device participation.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @typeCode | Type of participation, typically "DEV" (device) | Yes |

**Common typeCode Values:**
| Code | Display |
|------|---------|
| DEV | Device |
| BBY | Baby (for medical devices used on newborns) |

### participantRole

The role played by the device in the clinical context.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @classCode | Role class, fixed to "MANU" (manufactured product) | Yes |

### templateId

Template identifier for Product Instance.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | Template OID: `2.16.840.1.113883.10.20.22.4.37` | Yes |

### id (1..*)

Device identifiers, including UDI information.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the assigning authority | Yes |
| @extension | The identifier value | No |
| @assigningAuthorityName | Human-readable authority name | No |

**Device Identifier OID:**
| OID | Description |
|-----|-------------|
| 2.16.840.1.113883.3.3719 | FDA UDI - Use for ALL UDI strings regardless of issuing agency (GS1, HIBCC, ICCBBA) |

**UDI Format:**
When communicating UDI information in C-CDA, **always use the FDA UDI OID** (`2.16.840.1.113883.3.3719`) regardless of which agency issued the UDI (GS1, HIBCC, or ICCBBA). The issuing agency is indicated by the UDI format itself, not by the OID.

**Complete UDI (Device Identifier + Production Identifiers):**
- Use FDA OID: `2.16.840.1.113883.3.3719`
- Include full UDI string in `@extension` attribute
- Example: `(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234`

**Device Identifier Only:**
- Use FDA OID: `2.16.840.1.113883.3.3719`
- Include only the DI portion in `@extension`
- Example: `51022222233336`

### playingDevice

The device being represented.

| Element | Cardinality | Description |
|---------|-------------|-------------|
| code | 0..1 (SHOULD) | Device type code |
| manufacturerModelName | 0..1 | Device model designation |
| softwareName | 0..1 | Associated software identifier |

### playingDevice/code

Device type or category code.

| Attribute | Description | Required |
|-----------|-------------|----------|
| @code | Device type code | Yes (if element present) |
| @codeSystem | Code system OID | Yes (if element present) |
| @displayName | Human-readable display | No |
| @codeSystemName | Code system name | No |

**Code Systems:**
| OID | Name | Use |
|-----|------|-----|
| 2.16.840.1.113883.6.96 | SNOMED CT | Primary device type codes |
| 2.16.840.1.113883.6.88 | RxNorm | Medication delivery devices |

**Common SNOMED CT Device Codes:**
| Code | Display |
|------|---------|
| 14106009 | Cardiac pacemaker |
| 19257004 | Defibrillator |
| 360203008 | Stent |
| 257327003 | Orthopedic implant |
| 90412006 | Colonoscope |
| 102303004 | Endoscope |
| 87405001 | Cane |
| 58938008 | Wheelchair |
| 40388003 | Implant |
| 706689003 | Electronic health record |

### playingDevice/code/originalText

| Element | Description | Required |
|---------|-------------|----------|
| originalText | Free text description of the device | No |
| reference | Reference to narrative text using #id | No |

### playingDevice/manufacturerModelName

| Type | Description |
|------|-------------|
| string | Manufacturer's model designation or name |

### playingDevice/softwareName

| Type | Description |
|------|-------------|
| string | Software name and version (for software-based devices or EHR systems) |

### scopingEntity

The manufacturer or scoping organization for the device.

| Element | Cardinality | Description |
|---------|-------------|-------------|
| id | 1..* | Manufacturer identifier(s) |
| desc | 0..1 | Manufacturer name/description |

### scopingEntity/id

| Attribute | Description | Required |
|-----------|-------------|----------|
| @root | OID identifying the manufacturer | Yes |
| @extension | Manufacturer-specific identifier | No |

### scopingEntity/desc

| Type | Description |
|------|-------------|
| string | Human-readable manufacturer name or description |

## Conformance Requirements

Per C-CDA specification:

1. **SHALL** contain exactly one `@classCode="MANU"`
2. **SHALL** contain at least one `templateId` with `@root="2.16.840.1.113883.10.20.22.4.37"`
3. **SHALL** contain at least one `id`
4. **SHALL** contain exactly one `playingDevice` or `playingEntity` (mutually exclusive)
5. **SHALL** contain exactly one `scopingEntity`
6. `scopingEntity` **SHALL** contain at least one `id`
7. `playingDevice` **SHOULD** contain a `code` element
8. If `id` is present, it **SHALL** have either `@root` or `@nullFlavor`

## UDI Implementation Guidance

### Recommended Approach

For complete UDI communication (Device Identifier + Production Identifiers):
1. Include the full UDI string in one `id` element using FDA OID
2. Optionally include a separate `id` for just the Device Identifier using the appropriate issuing agency OID

### UDI Component Breakdown

A complete UDI includes:
- **Device Identifier (DI):** Identifies the labeler and specific version/model
- **Production Identifiers (PI):** Lot number, serial number, manufacturing date, expiration date

**Example UDI String:**
```
(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234
```

Breakdown:
- `(01)` - Application Identifier for DI
- `51022222233336` - Device Identifier
- `(11)141231` - Manufacturing date (December 31, 2014)
- `(17)150707` - Expiration date (July 7, 2015)
- `(10)A213B1` - Lot number
- `(21)1234` - Serial number

### Historical Devices

When UDI data is unavailable (older implants, patient-reported devices):
- Use organization-specific identifier in `id/@root` and `id/@extension`
- Document manufacturer in `scopingEntity/desc`
- Document model in `playingDevice/manufacturerModelName`

## Templates Using Product Instance

This template is used by:
- Procedure Activity Procedure (`2.16.840.1.113883.10.20.22.4.14`)
- Non-Medicinal Supply Activity (`2.16.840.1.113883.10.20.22.4.50`)
- Planned Supply (`2.16.840.1.113883.10.20.22.4.43`)
- Device Identifier Observation (`2.16.840.1.113883.10.20.22.4.304`)

## Device vs. Non-Device Participants

| Element | Device (typeCode="DEV") | Non-Device (other codes) |
|---------|------------------------|--------------------------|
| Template | Product Instance (`2.16.840.1.113883.10.20.22.4.37`) | Various |
| participantRole/@classCode | MANU | Varies (PRS, SDLOC, etc.) |
| playingDevice | Present | Absent |
| playingEntity | Absent | May be present |

## Examples from C-CDA Implementation Guide

### Example 1: Implanted Pacemaker

```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
    <id root="2.16.840.1.113883.3.3719"
        extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"/>
    <playingDevice>
      <code code="14106009" codeSystem="2.16.840.1.113883.6.96"
            displayName="Cardiac pacemaker"/>
    </playingDevice>
    <scopingEntity>
      <id root="2.16.840.1.113883.3.3719"/>
      <desc>Acme Devices, Inc</desc>
    </scopingEntity>
  </participantRole>
</participant>
```

### Example 2: Surgical Implant with Multiple IDs

```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>

    <!-- Full UDI - Always use FDA UDI OID regardless of issuing agency -->
    <id root="2.16.840.1.113883.3.3719"
        extension="(01)00643169001763(17)180322(10)M320(21)AC221"
        assigningAuthorityName="FDA"/>

    <playingDevice>
      <code code="257327003" codeSystem="2.16.840.1.113883.6.96"
            displayName="Orthopedic implant"/>
      <manufacturerModelName>Hip Replacement Model HR-2000</manufacturerModelName>
    </playingDevice>

    <scopingEntity>
      <id root="2.16.840.1.113883.3.3719"/>
      <desc>Orthopedic Implants Corp</desc>
    </scopingEntity>
  </participantRole>
</participant>
```

### Example 3: Medical Supply (Cane)

```xml
<supply classCode="SPLY" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.50"/>
  <id root="9a6d1bac-17d3-4195-89a4-1121bc809b4d"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200301"/>

  <participant typeCode="PRD">
    <participantRole classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
      <id root="2.16.840.1.113883.19.321" extension="SN-12345"/>
      <playingDevice>
        <code code="87405001" codeSystem="2.16.840.1.113883.6.96"
              displayName="Cane"/>
        <manufacturerModelName>Standard Walker Model 2020</manufacturerModelName>
      </playingDevice>
      <scopingEntity>
        <id root="2.16.840.1.113883.19.321"/>
        <desc>Mobility Aids Inc</desc>
      </scopingEntity>
    </participantRole>
  </participant>
</supply>
```

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| playingDevice/code | Device Types (SNOMED CT) | Preferred |

## References

- HL7 C-CDA Product Instance Template: http://hl7.org/cda/us/ccda/StructureDefinition/ProductInstance
- C-CDA Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- FDA UDI System: https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system
- C-CDA Examples Repository: https://github.com/HL7/C-CDA-Examples
- SNOMED CT Browser: https://browser.ihtsdotools.org/
