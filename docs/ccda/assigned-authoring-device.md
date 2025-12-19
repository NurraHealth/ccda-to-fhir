# C-CDA: assignedAuthoringDevice

## Overview

The `assignedAuthoringDevice` element represents a device (such as an EHR system, medical software, or automated device) that authored or created clinical content. This element appears within the `author` participation to indicate that a device, rather than a person, was responsible for documenting clinical information. It is commonly used to identify electronic health record systems, clinical decision support systems, automated measurement devices, or other software that generates clinical documentation.

## Template Information

| Attribute | Value |
|-----------|-------|
| Template | Part of Author Participation (`2.16.840.1.113883.10.20.22.4.119`) |
| Context | Within `assignedAuthor` element |
| Cardinality | 0..1 (mutually exclusive with `assignedPerson`) |

## Context of Use

The `assignedAuthoringDevice` appears in:
- **Document-level authors** - Identifying the system that created the clinical document
- **Entry-level authors** - Identifying automated systems that generated specific observations, measurements, or other clinical entries
- **Automated documentation** - Where devices or software create clinical content without direct human authoring

## Location in Document

```
ClinicalDocument
├── author [Document Author]
│   ├── templateId
│   ├── time
│   └── assignedAuthor
│       ├── id
│       └── assignedAuthoringDevice
│           ├── manufacturerModelName
│           └── softwareName
│
└── component/structuredBody/component/section
    └── entry
        └── [observation/procedure/...]
            └── author [Entry-Level Author]
                ├── time
                └── assignedAuthor
                    ├── id
                    └── assignedAuthoringDevice
                        ├── manufacturerModelName
                        └── softwareName
```

## XML Structure

### Basic Document-Level Authoring Device

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301102000-0500"/>
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

### EHR System with Version Information

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200722"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="EHR-SYSTEM-01"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Generic EHR Clinical System 2.0.0.0.0.0</manufacturerModelName>
      <softwareName>Generic EHR C-CDA Factory 2.0.0.0.0.0 - C-CDA Transform 2.0.0.0.0</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
      <telecom use="WP" value="tel:+1(555)555-5000"/>
      <addr>
        <streetAddressLine>1001 Village Avenue</streetAddressLine>
        <city>Portland</city>
        <state>OR</state>
        <postalCode>99123</postalCode>
      </addr>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Medical Device as Author

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200315093000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.321" extension="BP-MONITOR-01"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Omron Blood Pressure Monitor</manufacturerModelName>
      <softwareName>BP Monitor v3.2</softwareName>
    </assignedAuthoringDevice>
  </assignedAuthor>
</author>
```

### Advanced Directives Portal

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200110"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="PORTAL-001"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>MyDirectives.com</manufacturerModelName>
      <softwareName>MyDirectives.com v2.0</softwareName>
    </assignedAuthoringDevice>
  </assignedAuthor>
</author>
```

### Patient Portal System

```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200501120000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="PATIENT-PORTAL"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>PMEHR - Version 8.3</manufacturerModelName>
      <softwareName>PMEHR - Version 8.3</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Health System Patient Portal</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Entry-Level Device Author (Vital Signs Organizer)

```xml
<organizer classCode="CLUSTER" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
  <id root="c6f88321-67ad-11db-bd13-0800200c9a66"/>
  <code code="46680005" codeSystem="2.16.840.1.113883.6.96"
        displayName="Vital signs"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315093000-0500"/>

  <author>
    <time value="20200315093000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.19.321" extension="VITALS-DEVICE-01"/>
      <assignedAuthoringDevice>
        <manufacturerModelName>Welch Allyn Vital Signs Monitor 300 Series</manufacturerModelName>
        <softwareName>Vital Signs v4.5</softwareName>
      </assignedAuthoringDevice>
    </assignedAuthor>
  </author>

  <!-- vital sign observations -->
</organizer>
```

## Element Details

### assignedAuthoringDevice

Container element representing the authoring device.

| Element | Cardinality | Description |
|---------|-------------|-------------|
| manufacturerModelName | 0..1 | Device manufacturer and model designation |
| softwareName | 0..1 | Software name and version |

**Note:** Must contain at least one of `manufacturerModelName` or `softwareName`, though both are typically included.

### manufacturerModelName

| Type | Description |
|------|-------------|
| string | Manufacturer name and model designation of the device or system |

**Usage Guidance:**
- Should identify the manufacturer/vendor
- May include product line or system name
- May include version numbers
- Should be human-readable

**Examples:**
- `Epic EHR`
- `Cerner Millennium`
- `Generic EHR Clinical System 2.0.0.0.0.0`
- `Omron Blood Pressure Monitor Model BP785N`
- `Welch Allyn Vital Signs Monitor 300 Series`
- `PMEHR - Version 8.3`
- `MyDirectives.com`

### softwareName

| Type | Description |
|------|-------------|
| string | Software name, version, and build information |

**Usage Guidance:**
- Should identify specific software component
- Should include version number
- May include build or release information
- May identify transformation or generation components

**Examples:**
- `Epic 2020`
- `Epic 2020.1.5`
- `Generic EHR C-CDA Factory 2.0.0.0.0.0 - C-CDA Transform 2.0.0.0.0`
- `Cerner CCL Script v12.3`
- `BP Monitor v3.2`
- `MyDirectives.com v2.0`
- `PMEHR - Version 8.3`

## Conformance Requirements

Per C-CDA Author Participation template (`2.16.840.1.113883.10.20.22.4.119`):

1. `assignedAuthor` **SHALL** contain exactly one `assignedPerson` OR exactly one `assignedAuthoringDevice` (mutually exclusive)
2. If `assignedAuthoringDevice` is present, it **SHOULD** contain `manufacturerModelName` and/or `softwareName`
3. Authors **typically require** contact information (`addr`, `telecom`) and either `assignedPerson/name` or `assignedAuthoringDevice/manufacturerModelName`. For document-level authors, these details should be present on the author itself. For entry-level authors, these details may be inherited from document-level authors or referenced elsewhere in the document.

## assignedPerson vs. assignedAuthoringDevice

| Aspect | assignedPerson | assignedAuthoringDevice |
|--------|---------------|-------------------------|
| Represents | Human author | Device/software author |
| Contains | `name` element | `manufacturerModelName` and/or `softwareName` |
| Use case | Physician, nurse, other clinician documented the content | EHR system, medical device, or software generated the content |
| Cardinality | 0..1 | 0..1 |
| Mutual exclusivity | Cannot coexist with assignedAuthoringDevice | Cannot coexist with assignedPerson |

## Common Authoring Device Scenarios

### Scenario 1: EHR-Generated CCD

When an EHR system generates a Continuity of Care Document (CCD):

```xml
<author>
  <time value="20200301102000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="EHR-001"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Epic EHR</manufacturerModelName>
      <softwareName>Epic 2020.1</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Scenario 2: Automated Vital Signs

When a vital signs monitor automatically records measurements:

```xml
<author>
  <time value="20200315093000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.321" extension="VS-MONITOR-12"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Welch Allyn Vital Signs Monitor 300 Series</manufacturerModelName>
      <softwareName>Vital Signs v4.5</softwareName>
    </assignedAuthoringDevice>
  </assignedAuthor>
</author>
```

### Scenario 3: Patient Portal Entry

When a patient enters information through a portal (though the portal system is the "author"):

```xml
<author>
  <time value="20200501120000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="PATIENT-PORTAL"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Patient Portal System</manufacturerModelName>
      <softwareName>MyHealth Portal v3.0</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

### Scenario 4: Clinical Decision Support

When a CDS system generates a recommendation or alert:

```xml
<author>
  <time value="20200615141500-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="CDS-ENGINE-01"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Clinical Decision Support Engine</manufacturerModelName>
      <softwareName>CDS Rules Engine v2.5</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

## Author Time Considerations

The `author/time` element represents when the device performed the authoring action:
- For document generation, this is typically the document creation timestamp
- For automated measurements, this is when the device captured the data
- For transformations, this is when the transformation occurred

## Identification of Authoring Devices

### Device Identifiers

The `assignedAuthor/id` should uniquely identify the specific device instance or software installation:

```xml
<id root="2.16.840.1.113883.19.5" extension="EHR-INSTANCE-01"/>
```

**Best Practices:**
- Use organization-specific OID in `@root`
- Use unique device/instance identifier in `@extension`
- Consider using device serial number, installation ID, or system identifier
- Ensure consistency across documents from the same device

### Organization Context

The `representedOrganization` indicates the healthcare organization under whose authority the device operates:

```xml
<representedOrganization>
  <id root="2.16.840.1.113883.19.5.9999.1393"/>
  <name>Community Health and Hospitals</name>
  <telecom use="WP" value="tel:+1(555)555-5000"/>
  <addr>
    <streetAddressLine>1001 Village Avenue</streetAddressLine>
    <city>Portland</city>
    <state>OR</state>
    <postalCode>99123</postalCode>
  </addr>
</representedOrganization>
```

## Authoring Device vs. Product Instance

| Aspect | assignedAuthoringDevice | Product Instance |
|--------|------------------------|------------------|
| Context | Author participation | Device participation (typeCode="DEV") |
| Purpose | Identifies system that created documentation | Identifies device used in patient care |
| Template | Part of Author Participation (`2.16.840.1.113883.10.20.22.4.119`) | Product Instance (`2.16.840.1.113883.10.20.22.4.37`) |
| Location | Within `assignedAuthor` | Within `participant` |
| Elements | `manufacturerModelName`, `softwareName` | `playingDevice/code`, `manufacturerModelName`, `id` |
| UDI | Not typically used | Commonly used for implantable devices |
| Example | EHR system, patient portal | Pacemaker, colonoscope, cane |

## Complete Examples

### Example 1: Document Header with EHR Author

```xml
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Summarization of Episode Note"/>
  <title>Continuity of Care Document</title>
  <effectiveTime value="20200301102000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <!-- patient information -->
  </recordTarget>

  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20200301102000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.19.5" extension="EHR-SYSTEM-01"/>
      <assignedAuthoringDevice>
        <manufacturerModelName>MY EHR VENDOR</manufacturerModelName>
        <softwareName>MY EHR 9.7</softwareName>
      </assignedAuthoringDevice>
      <representedOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
        <telecom use="WP" value="tel:+1(555)555-5000"/>
        <addr>
          <streetAddressLine>1001 Village Avenue</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>
      </representedOrganization>
    </assignedAuthor>
  </author>

  <!-- remainder of document -->
</ClinicalDocument>
```

### Example 2: Observation with Device Author

```xml
<observation classCode="OBS" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
  <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
  <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
        displayName="Systolic blood pressure"/>
  <statusCode code="completed"/>
  <effectiveTime value="20200315093000-0500"/>
  <value xsi:type="PQ" value="132" unit="mm[Hg]"/>

  <author>
    <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
    <time value="20200315093000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.19.321" extension="BP-MONITOR-01"/>
      <assignedAuthoringDevice>
        <manufacturerModelName>Omron Blood Pressure Monitor Model BP785N</manufacturerModelName>
        <softwareName>BP Monitor v3.2</softwareName>
      </assignedAuthoringDevice>
    </assignedAuthor>
  </author>
</observation>
```

## References

- HL7 C-CDA Author Participation Template: http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.119.html
- C-CDA Implementation Guide: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492
- C-CDA R2.1 Companion Guide: https://www.hl7.org/implement/standards/product_brief.cfm?product_id=447
- C-CDA Examples Repository: https://github.com/HL7/C-CDA-Examples
