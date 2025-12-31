# Device Mapping: C-CDA Device Elements ↔ FHIR Device

This document provides detailed mapping guidance between C-CDA device-related elements and FHIR `Device` resource.

## Overview

C-CDA represents devices in multiple contexts:

| C-CDA Element | Context | FHIR Resource |
|---------------|---------|---------------|
| Product Instance (`2.16.840.1.113883.10.20.22.4.37`) | Participant (typeCode="DEV") | Device |
| assignedAuthoringDevice | Author participation | Device |
| participant (typeCode="DEV") | Various clinical entries | Device |

## Mapping Strategy

### Device Type Classification

| C-CDA Context | Device Type | FHIR Profile | Patient Reference Required |
|---------------|-------------|--------------|----------------------------|
| Product Instance in Procedure (implanted) | Implantable device | US Core Implantable Device | Yes |
| Product Instance in Supply | Medical supply/equipment | Device (base) | Optional |
| assignedAuthoringDevice | Software/EHR system | Device (base) | No |
| Participant (typeCode="DEV") in observation | Measurement device | Device (base) | Optional |

## C-CDA to FHIR Mapping

### Product Instance to Device

#### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `participant/participantRole` (Product Instance) | `Device` | Create Device resource |
| `participantRole/id` | `Device.identifier` | [ID → Identifier](#identifier-mapping) |
| `participantRole/id[@root='2.16.840.1.113883.3.3719']` | `Device.udiCarrier` | [UDI Mapping](#udi-mapping) |
| `playingDevice/code` | `Device.type` | CodeableConcept |
| `playingDevice/manufacturerModelName` | `Device.deviceName` + `Device.modelNumber` | [Device Name Mapping](#device-name-mapping) |
| `scopingEntity/id` | `Device.owner` or manufacturer info | Reference(Organization) or text |
| `scopingEntity/desc` | `Device.manufacturer` | String |
| Context (procedure/supply) | `Device.patient` | Reference(Patient) if implanted |

### Identifier Mapping

Convert CDA `id` elements to FHIR `identifier`:

**C-CDA:**
```xml
<participantRole classCode="MANU">
  <!-- Always use FDA UDI OID for device identifiers -->
  <id root="2.16.840.1.113883.3.3719"
      extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
      assigningAuthorityName="FDA"/>
</participantRole>
```

**FHIR:**
```json
{
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.3.3719",
      "value": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    }
  ]
}
```

**Note:** Only use the FDA UDI OID for device identifiers. Do not create separate identifier entries with issuing agency OIDs.

**Well-Known Identifier Systems:**

| CDA OID | FHIR System | Description |
|---------|-------------|-------------|
| `2.16.840.1.113883.3.3719` | `urn:oid:2.16.840.1.113883.3.3719` | FDA UDI - Use for ALL UDI strings regardless of issuing agency |

**Note:** In C-CDA, always use the FDA UDI OID (`2.16.840.1.113883.3.3719`) for device identifiers, regardless of which agency (GS1, HIBCC, or ICCBBA) issued the UDI. The issuing agency is indicated by the UDI format itself, not by the OID. In FHIR, the issuer is specified in `Device.udiCarrier.issuer` using NamingSystem URIs.

### UDI Mapping

When `id/@root` is `2.16.840.1.113883.3.3719` (FDA UDI), parse the UDI string and populate `Device.udiCarrier`:

**C-CDA:**
```xml
<id root="2.16.840.1.113883.3.3719"
    extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    assigningAuthorityName="FDA"/>
```

**FHIR:**
```json
{
  "udiCarrier": [
    {
      "deviceIdentifier": "51022222233336",
      "issuer": "http://hl7.org/fhir/NamingSystem/gs1-di",
      "jurisdiction": "http://hl7.org/fhir/NamingSystem/fda-udi",
      "carrierHRF": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234",
      "entryType": "unknown"
    }
  ]
}
```

**UDI Parsing Rules:**

1. Extract `carrierHRF` from full `id/@extension` value
2. Parse Device Identifier (DI) from application identifier `(01)`
3. Extract production identifiers:
   - `(11)` → Manufacturing date
   - `(17)` → Expiration date
   - `(10)` → Lot number
   - `(21)` → Serial number

**Date Conversion:**
```
C-CDA: (11)141231 → FHIR: "2014-12-31" (manufactureDate)
C-CDA: (17)150707 → FHIR: "2015-07-07" (expirationDate)
```

**Complete UDI Example:**
```json
{
  "udiCarrier": [
    {
      "deviceIdentifier": "51022222233336",
      "issuer": "http://hl7.org/fhir/NamingSystem/gs1-di",
      "jurisdiction": "http://hl7.org/fhir/NamingSystem/fda-udi",
      "carrierHRF": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    }
  ],
  "manufactureDate": "2014-12-31",
  "expirationDate": "2015-07-07",
  "lotNumber": "A213B1",
  "serialNumber": "1234"
}
```

### Device Name Mapping

The `manufacturerModelName` maps to both `deviceName` and `modelNumber`:

**C-CDA:**
```xml
<playingDevice>
  <code code="14106009" codeSystem="2.16.840.1.113883.6.96"
        displayName="Cardiac pacemaker"/>
  <manufacturerModelName>Model XYZ Pacemaker</manufacturerModelName>
</playingDevice>
```

**FHIR:**
```json
{
  "deviceName": [
    {
      "name": "Model XYZ Pacemaker",
      "type": "model-name"
    },
    {
      "name": "Cardiac pacemaker",
      "type": "user-friendly-name"
    }
  ],
  "modelNumber": "Model XYZ Pacemaker",
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "14106009",
        "display": "Cardiac pacemaker"
      }
    ]
  }
}
```

**Device Name Type Mapping:**

| C-CDA Source | FHIR deviceName.type |
|--------------|---------------------|
| `manufacturerModelName` | `model-name` |
| `playingDevice/code/@displayName` | `user-friendly-name` |
| `playingDevice/code/originalText` | `user-friendly-name` |

### Device Type Mapping

**C-CDA:**
```xml
<playingDevice>
  <code code="90412006" codeSystem="2.16.840.1.113883.6.96"
        displayName="Colonoscope">
    <originalText>GI Endoscopy Device</originalText>
  </code>
</playingDevice>
```

**FHIR:**
```json
{
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "90412006",
        "display": "Colonoscope"
      }
    ],
    "text": "GI Endoscopy Device"
  }
}
```

**Code System Mapping:**

| CDA OID | FHIR System |
|---------|-------------|
| `2.16.840.1.113883.6.96` | `http://snomed.info/sct` |
| `2.16.840.1.113883.6.88` | `http://www.nlm.nih.gov/research/umls/rxnorm` |

### Manufacturer and Organization Mapping

**C-CDA:**
```xml
<scopingEntity>
  <id root="2.16.840.1.113883.19.321"/>
  <desc>Acme Devices, Inc</desc>
</scopingEntity>
```

**FHIR:**
```json
{
  "manufacturer": "Acme Devices, Inc"
}
```

**If Organization Details Available:**
Create a separate Organization resource and reference it:

```json
{
  "owner": {
    "reference": "Organization/org-acme-devices",
    "display": "Acme Devices, Inc"
  }
}
```

### Patient Reference for Implantable Devices

When the Product Instance appears in a Procedure or implantation context, include patient reference:

**Context from Procedure:**
```xml
<procedure>
  <subject>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="998991"/>
    </patientRole>
  </subject>
  <participant typeCode="DEV">
    <!-- Product Instance -->
  </participant>
</procedure>
```

**FHIR Device:**
```json
{
  "resourceType": "Device",
  "patient": {
    "reference": "Patient/patient-998991"
  }
}
```

### assignedAuthoringDevice to Device

#### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `assignedAuthor/id` | `Device.identifier` | ID → Identifier |
| `assignedAuthoringDevice/manufacturerModelName` | `Device.deviceName` (manufacturer-name type) | String |
| `assignedAuthoringDevice/softwareName` | `Device.deviceName` (model-name type) + `Device.version` | [Software Mapping](#software-mapping) |
| Inferred | `Device.type` | EHR/Software code |
| `representedOrganization` | `Device.owner` | Reference(Organization) |

### Software Mapping

**C-CDA:**
```xml
<assignedAuthoringDevice>
  <manufacturerModelName>Epic EHR</manufacturerModelName>
  <softwareName>Epic 2020.1.5</softwareName>
</assignedAuthoringDevice>
```

**FHIR:**
```json
{
  "deviceName": [
    {
      "name": "Epic EHR",
      "type": "manufacturer-name"
    },
    {
      "name": "Epic 2020.1.5",
      "type": "model-name"
    }
  ],
  "version": [
    {
      "value": "2020.1.5"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "706689003",
        "display": "Electronic health record"
      }
    ]
  }
}
```

**Version Extraction:**
If `softwareName` contains version pattern (e.g., "Epic 2020.1.5"), extract the version:
- Pattern: `{name} {version}` or `{name} v{version}`
- Extract version to `Device.version[].value`

## Complete Mapping Examples

### Example 1: Implanted Pacemaker

**C-CDA Input:**
```xml
<procedure classCode="PROC" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
  <code code="233174007" codeSystem="2.16.840.1.113883.6.96"
        displayName="Pacemaker insertion"/>
  <statusCode code="completed"/>
  <effectiveTime value="20141231"/>

  <participant typeCode="DEV">
    <participantRole classCode="MANU">
      <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
      <id root="2.16.840.1.113883.3.3719"
          extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
          assigningAuthorityName="FDA"/>
      <playingDevice>
        <code code="14106009" codeSystem="2.16.840.1.113883.6.96"
              displayName="Cardiac pacemaker"/>
        <manufacturerModelName>Model XYZ Pacemaker</manufacturerModelName>
      </playingDevice>
      <scopingEntity>
        <id root="2.16.840.1.113883.3.3719"/>
        <desc>Acme Devices, Inc</desc>
      </scopingEntity>
    </participantRole>
  </participant>
</procedure>
```

**FHIR Output:**
```json
{
  "resourceType": "Device",
  "id": "device-pacemaker-1234",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device"
    ]
  },
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.3.3719",
      "value": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    }
  ],
  "udiCarrier": [
    {
      "deviceIdentifier": "51022222233336",
      "issuer": "http://hl7.org/fhir/NamingSystem/gs1-di",
      "jurisdiction": "http://hl7.org/fhir/NamingSystem/fda-udi",
      "carrierHRF": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234",
      "entryType": "unknown"
    }
  ],
  "status": "active",
  "manufacturer": "Acme Devices, Inc",
  "manufactureDate": "2014-12-31",
  "expirationDate": "2015-07-07",
  "lotNumber": "A213B1",
  "serialNumber": "1234",
  "deviceName": [
    {
      "name": "Model XYZ Pacemaker",
      "type": "model-name"
    },
    {
      "name": "Cardiac pacemaker",
      "type": "user-friendly-name"
    }
  ],
  "modelNumber": "Model XYZ Pacemaker",
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "14106009",
        "display": "Cardiac pacemaker"
      }
    ]
  },
  "patient": {
    "reference": "Patient/patient-example"
  }
}
```

### Example 2: EHR Authoring Device

**C-CDA Input:**
```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200301102000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.19.5" extension="EHR-SYSTEM-01"/>
    <assignedAuthoringDevice>
      <manufacturerModelName>Epic EHR</manufacturerModelName>
      <softwareName>Epic 2020.1.5</softwareName>
    </assignedAuthoringDevice>
    <representedOrganization>
      <id root="2.16.840.1.113883.19.5.9999.1393"/>
      <name>Community Health and Hospitals</name>
    </representedOrganization>
  </assignedAuthor>
</author>
```

**FHIR Output:**
```json
{
  "resourceType": "Device",
  "id": "device-ehr-system-01",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5",
      "value": "EHR-SYSTEM-01"
    }
  ],
  "deviceName": [
    {
      "name": "Epic EHR",
      "type": "manufacturer-name"
    },
    {
      "name": "Epic 2020.1.5",
      "type": "model-name"
    }
  ],
  "version": [
    {
      "value": "2020.1.5"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "706689003",
        "display": "Electronic health record"
      }
    ]
  },
  "owner": {
    "reference": "Organization/org-community-health",
    "display": "Community Health and Hospitals"
  }
}
```

### Example 3: Medical Supply (Colonoscope)

**C-CDA Input:**
```xml
<participant typeCode="DEV">
  <participantRole classCode="MANU">
    <templateId root="2.16.840.1.113883.10.20.22.4.37"/>
    <id root="2.16.840.1.113883.3.3719"
        extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
        assigningAuthorityName="FDA"/>
    <playingDevice>
      <code code="90412006" codeSystem="2.16.840.1.113883.6.96"
            displayName="Colonoscope"/>
    </playingDevice>
    <scopingEntity>
      <id root="2.16.840.1.113883.3.3719"/>
    </scopingEntity>
  </participantRole>
</participant>
```

**FHIR Output:**
```json
{
  "resourceType": "Device",
  "id": "device-colonoscope",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.3.3719",
      "value": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    }
  ],
  "udiCarrier": [
    {
      "deviceIdentifier": "51022222233336",
      "issuer": "http://hl7.org/fhir/NamingSystem/gs1-di",
      "jurisdiction": "http://hl7.org/fhir/NamingSystem/fda-udi",
      "carrierHRF": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
    }
  ],
  "status": "active",
  "manufactureDate": "2014-12-31",
  "expirationDate": "2015-07-07",
  "lotNumber": "A213B1",
  "serialNumber": "1234",
  "deviceName": [
    {
      "name": "Colonoscope",
      "type": "user-friendly-name"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "90412006",
        "display": "Colonoscope"
      }
    ]
  }
}
```

### Example 4: Vital Signs Monitor

**C-CDA Input:**
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

**FHIR Output:**
```json
{
  "resourceType": "Device",
  "id": "device-vs-monitor-12",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.321",
      "value": "VS-MONITOR-12"
    }
  ],
  "deviceName": [
    {
      "name": "Welch Allyn Vital Signs Monitor 300 Series",
      "type": "manufacturer-name"
    },
    {
      "name": "Vital Signs v4.5",
      "type": "model-name"
    }
  ],
  "version": [
    {
      "value": "4.5"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "706767009",
        "display": "Patient vital signs monitoring system"
      }
    ]
  }
}
```

## FHIR to C-CDA Mapping

### Creating Product Instance from Device

| FHIR Path | C-CDA Path | Transform |
|-----------|------------|-----------|
| `Device.identifier` | `participantRole/id` | Identifier → ID |
| `Device.udiCarrier.carrierHRF` | `id[@root='2.16.840.1.113883.3.3719']/@extension` | Full UDI string |
| `Device.type` | `playingDevice/code` | CodeableConcept → CE |
| `Device.modelNumber` | `playingDevice/manufacturerModelName` | String |
| `Device.manufacturer` | `scopingEntity/desc` | String |
| `Device.owner` | `scopingEntity/id` | Reference → ID |

### Creating assignedAuthoringDevice from Device

| FHIR Path | C-CDA Path | Transform |
|-----------|------------|-----------|
| `Device.identifier` | `assignedAuthor/id` | Identifier → ID |
| `Device.deviceName[type='manufacturer-name']` | `assignedAuthoringDevice/manufacturerModelName` | String |
| `Device.deviceName[type='model-name']` or `Device.version` | `assignedAuthoringDevice/softwareName` | Combine name + version |
| `Device.owner` | `representedOrganization` | Reference → Organization |

## Device Status Mapping

C-CDA does not have an explicit status field for devices. Infer status from context:

| Context | FHIR Device.status |
|---------|-------------------|
| Product Instance in completed procedure | `active` |
| Product Instance in planned procedure | `inactive` |
| assignedAuthoringDevice | `active` |
| Device in current use | `active` |
| Historical/removed device | `inactive` |

## Referencing Devices in Other Resources

### In Procedure

**FHIR:**
```json
{
  "resourceType": "Procedure",
  "id": "procedure-pacemaker-insertion",
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "233174007",
        "display": "Pacemaker insertion"
      }
    ]
  },
  "focalDevice": [
    {
      "action": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "129337003",
            "display": "Implantation"
          }
        ]
      },
      "manipulated": {
        "reference": "Device/device-pacemaker-1234"
      }
    }
  ]
}
```

### In Observation (Author)

**FHIR Provenance:**
```json
{
  "resourceType": "Provenance",
  "id": "provenance-bp-observation",
  "target": [
    {
      "reference": "Observation/bp-observation"
    }
  ],
  "recorded": "2020-03-15T09:30:00-05:00",
  "agent": [
    {
      "type": {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
            "code": "author"
          }
        ]
      },
      "who": {
        "reference": "Device/device-vs-monitor-12"
      }
    }
  ]
}
```

### In Composition (Author)

**FHIR:**
```json
{
  "resourceType": "Composition",
  "id": "composition-ccd",
  "author": [
    {
      "reference": "Device/device-ehr-system-01",
      "display": "Epic EHR"
    }
  ]
}
```

## Resource Deduplication

When the same device appears multiple times in a document:

1. **Generate consistent IDs:** Use CDA identifier (root + extension) as basis for FHIR resource ID
2. **Reference existing resources:** Check if device already created before creating new one
3. **Merge information:** If same device has additional details in different contexts, merge them

**Example ID Generation:**
- UDI `(01)51022222233336...` → `Device/device-udi-51022222233336`
- OID `2.16.840.1.113883.19.5` extension `EHR-SYSTEM-01` → `Device/device-oid-2.16.840.1.113883.19.5-EHR-SYSTEM-01`

## Special Considerations

### Implantable Devices

For implantable devices:
1. **SHALL** include `patient` reference
2. **SHOULD** use US Core Implantable Device profile
3. **SHALL** include `type` (device code)
4. **SHOULD** include UDI information when available

### EHR/Software Devices

For authoring devices:
1. Include `owner` reference to organization
2. Use SNOMED CT code `706689003` (Electronic health record) for `type`
3. Extract version from `softwareName` to `Device.version`

### Historical Devices

When UDI unavailable:
1. Use organization-specific identifiers
2. Document manufacturer name in `Device.manufacturer`
3. Document model in `Device.modelNumber`
4. Include note explaining lack of UDI

## Common Device Type Codes

| SNOMED CT Code | Display | Context |
|----------------|---------|---------|
| 14106009 | Cardiac pacemaker | Implantable |
| 19257004 | Defibrillator | Implantable |
| 360203008 | Stent | Implantable |
| 257327003 | Orthopedic implant | Implantable |
| 43252007 | Cochlear prosthesis | Implantable |
| 90412006 | Colonoscope | Reusable instrument |
| 102303004 | Endoscope | Reusable instrument |
| 87405001 | Cane | Medical supply |
| 58938008 | Wheelchair | Medical equipment |
| 40388003 | Implant | Implantable (general) |
| 706689003 | Electronic health record | Authoring device (EHR systems) |
| 706767009 | Patient vital signs monitoring system | Measurement device |

## References

- [FHIR R4B Device Resource](https://hl7.org/fhir/R4B/device.html)
- [US Core Implantable Device Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device)
- [C-CDA Product Instance Template](http://hl7.org/cda/us/ccda/StructureDefinition/ProductInstance)
- [C-CDA Author Participation Template](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.119.html)
- [FDA UDI System](https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system)
- [AccessGUDID Database](https://accessgudid.nlm.nih.gov/)
