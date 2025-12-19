# FHIR R4B: Device Resource

## Overview

The Device resource represents a manufactured item used in healthcare provision without being substantially changed during that activity. Unlike medications that are consumed, devices remain active continuously throughout their use. This resource tracks individual device instances and their locations within healthcare systems.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Device |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 2 |
| Standards Status | Trial Use (STU) |
| Security Category | Business |
| Responsible Work Group | Orders and Observations |
| URL | https://hl7.org/fhir/R4B/device.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device |

## Scope and Usage

The Device resource serves multiple critical functions:
- Recording which devices performed clinical actions (procedures, observations)
- Prescribing and dispensing devices for patient use
- Managing supply ordering and inventory
- Transmitting Unique Device Identifier (UDI) information, particularly for implanted devices
- Tracking device location and ownership within healthcare systems
- Documenting authoring systems (EHR software) that created clinical documents

**Key Distinctions:**
- **Device vs. Medication:** Devices remain active continuously rather than being consumed during use.
- **Device vs. DeviceDefinition:** Device represents a specific instance, while DeviceDefinition describes the device "kind" or catalog entry.
- **Device vs. DeviceMetric:** DeviceMetric represents measurement, calculation, or setting capability.
- **Implantable vs. Non-implantable:** Implantable devices require patient reference and should conform to US Core Implantable Device profile.

## JSON Structure

```json
{
  "resourceType": "Device",
  "id": "example-pacemaker",
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
      "entryType": "barcode"
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
      "name": "Cardiac Pacemaker",
      "type": "user-friendly-name"
    },
    {
      "name": "Model XYZ Pacemaker",
      "type": "model-name"
    }
  ],
  "modelNumber": "XYZ-2014",
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
    "reference": "Patient/example"
  }
}
```

## Element Definitions

### identifier (0..*)

Business identifiers assigned to this device by manufacturers, organizations, or other entities.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| secondary \| old |
| type | CodeableConcept | Type of identifier |
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| period | Period | Time period when identifier is/was valid |
| assigner | Reference(Organization) | Organization that assigned the identifier |

**Common Identifier Systems:**
| System URI | Description |
|------------|-------------|
| `urn:oid:2.16.840.1.113883.3.3719` | FDA UDI (complete UDI string) - Use for all UDI identifiers |

**Note:** For UDI identifiers in FHIR Device resources, use the FDA UDI OID (`urn:oid:2.16.840.1.113883.3.3719`) in the identifier system, regardless of which agency issued the UDI. The issuing agency is specified separately in `Device.udiCarrier.issuer` using NamingSystem URIs (see UDI Issuing Organizations table below).

### definition (0..1)

Reference to DeviceDefinition resource describing the device type.

| Type | Description |
|------|-------------|
| Reference(DeviceDefinition) | The catalog entry or definition for this device type |

**Note:** DeviceDefinition is a FHIR-only concept representing catalog-level device information (the "kind" of device). C-CDA does not have an equivalent template; device catalog information in C-CDA is typically represented inline within Product Instance.

### udiCarrier (0..*)

Unique Device Identifier (UDI) information as required by regulatory authorities.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| deviceIdentifier | string | 0..1 | Mandatory DI component identifying labeler and version |
| issuer | uri | 0..1 | URI identifying UDI issuing organization |
| jurisdiction | uri | 0..1 | Authoritative UDI source URI by jurisdiction |
| carrierAIDC | base64Binary | 0..1 | Base64-encoded machine-readable barcode/RFID data |
| carrierHRF | string | 0..1 | Human-readable form of UDI carrier |
| entryType | code | 0..1 | How the UDI was entered |

**UDI Issuing Organizations:**
| URI | Organization | Primary Use |
|-----|--------------|-------------|
| `http://hl7.org/fhir/NamingSystem/gs1-di` | GS1 (GTIN) | Most common in US; uses application identifiers (01), (11), (17), (10), (21) |
| `http://hl7.org/fhir/NamingSystem/hibcc-di` | HIBCC | Health Industry Business Communications Council; uses different format with + delimiters |
| `http://hl7.org/fhir/NamingSystem/iccbba-di` | ICCBBA | International Council for Commonality in Blood Banking Automation; primarily blood/tissue products |

**UDI Jurisdictions:**
| URI | Description |
|-----|-------------|
| `http://hl7.org/fhir/NamingSystem/fda-udi` | US FDA |
| `http://hl7.org/fhir/NamingSystem/eu-ec-udi` | European Commission |

**Entry Type Codes:**
| Code | Display |
|------|---------|
| barcode | Barcode |
| rfid | RFID |
| manual | Manual entry |
| card | Card |
| self-reported | Self Reported |
| unknown | Unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/udi-entry-type (Required binding)

### status (0..1)

This is a **modifier element**.

| Type | Values |
|------|--------|
| code | active \| inactive \| entered-in-error \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/device-status (Required binding)

**Note:** Affects interpretation of the resource.

### statusReason (0..*)

Reason for current operational status.

| Type | Description |
|------|-------------|
| CodeableConcept | Status reason codes |

**Value Set:** http://hl7.org/fhir/ValueSet/device-status-reason (Extensible binding)

**Common Status Reasons:**
| Code | Display |
|------|---------|
| online | Online |
| paused | Paused |
| standby | Standby |
| offline | Offline |
| not-ready | Not Ready |
| transduc-discon | Transducer Disconnected |
| hw-discon | Hardware Disconnected |

### distinctIdentifier (0..1)

Regulatory-required distinct identification for cellular and tissue-based products.

| Type | Description |
|------|-------------|
| string | The distinct identifier string |

### manufacturer (0..1)

| Type | Description |
|------|-------------|
| string | Name of device manufacturer |

### manufactureDate (0..1)

| Type | Format |
|------|--------|
| dateTime | Manufacturing timestamp |

### expirationDate (0..1)

| Type | Format |
|------|--------|
| dateTime | Expiration timestamp (when applicable) |

### lotNumber (0..1)

| Type | Description |
|------|-------------|
| string | Manufacturer's lot assignment |

### serialNumber (0..1)

| Type | Description |
|------|-------------|
| string | Organization-assigned serial identifier |

### deviceName (0..*)

Name(s) by which the device is known.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| name | string | 1..1 | The name of the device (Required) |
| type | code | 1..1 | Type of device name (Required) |

**Device Name Type Codes:**
| Code | Display |
|------|---------|
| udi-label-name | UDI Label name |
| user-friendly-name | User Friendly name |
| patient-reported-name | Patient Reported name |
| manufacturer-name | Manufacturer name |
| model-name | Model name |
| other | Other |

**Value Set:** http://hl7.org/fhir/ValueSet/device-nametype (Required binding)

### modelNumber (0..1)

| Type | Description |
|------|-------------|
| string | Manufacturer's model designation |

### partNumber (0..1)

| Type | Description |
|------|-------------|
| string | Catalog or part identifier |

### type (0..1)

Device category or type.

| Type | Description |
|------|-------------|
| CodeableConcept | Device type code |

**Value Set:** http://hl7.org/fhir/ValueSet/device-type (Example binding)

**Common Code Systems:**
| System URI | Description |
|------------|-------------|
| `http://snomed.info/sct` | SNOMED CT device codes |
| `http://www.nlm.nih.gov/research/umls/rxnorm` | RxNorm (for medication delivery devices) |

**Common SNOMED CT Device Codes:**
| Code | Display |
|------|---------|
| 14106009 | Cardiac pacemaker |
| 19257004 | Defibrillator |
| 102303004 | Colonoscope |
| 257327003 | Orthopedic implant |
| 360203008 | Stent |
| 87405001 | Cane |
| 40388003 | Implant |
| 43252007 | Cochlear prosthesis |
| 58938008 | Wheelchair |
| 706689003 | Electronic health record (for authoring devices) |
| 706767009 | Patient vital signs monitoring system |

### specialization (0..*)

Device capabilities, certifications, or communication standards.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| systemType | CodeableConcept | 1..1 | Standard or capability (Required) |
| version | string | 0..1 | Standard version |

### version (0..*)

Design and software versions.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| type | CodeableConcept | 0..1 | Version type identifier |
| component | Identifier | 0..1 | Single component version |
| value | string | 1..1 | Version text (Required) |

### property (0..*)

Static or persistent device configuration settings.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| type | CodeableConcept | 1..1 | Property type (Required) |
| valueQuantity | Quantity | 0..* | Property value as quantity |
| valueCode | CodeableConcept | 0..* | Property value as code |

### patient (0..1)

Reference to Patient if device is affixed to person.

| Type | Description |
|------|-------------|
| Reference(Patient) | Patient to whom device is affixed |

**Note:** Required for implantable devices per US Core profile.

### owner (0..1)

Organization responsible for device provision and maintenance.

| Type | Description |
|------|-------------|
| Reference(Organization) | Owning organization |

### contact (0..*)

Contact details for device support.

| Type | Description |
|------|-------------|
| ContactPoint | Device contact information |

### location (0..1)

Current physical location of the device.

| Type | Description |
|------|-------------|
| Reference(Location) | Where the device is found |

### url (0..1)

Network address for directly contacting the device.

| Type | Description |
|------|-------------|
| uri | Network URL to device |

### note (0..*)

Additional descriptive or usage information.

| Type | Description |
|------|-------------|
| Annotation | Device notes or text |

### safety (0..*)

Safety characteristics such as latex presence or MRI safety.

| Type | Description |
|------|-------------|
| CodeableConcept | Safety characteristic codes |

### parent (0..1)

Reference to parent Device if this device is attached as a component.

| Type | Description |
|------|-------------|
| Reference(Device) | Parent device |

## US Core Implantable Device Conformance Requirements

For US Core Implantable Device profile compliance:

1. **SHALL** support `type` (device category code)
2. **SHALL** support `patient` (reference to patient)
3. **SHALL** support `udiCarrier.deviceIdentifier` (UDI-DI) when UDI information is available
4. **SHOULD** support `udiCarrier.carrierHRF` (UDI human-readable barcode)
5. **SHOULD** support `manufactureDate`
6. **SHOULD** support `expirationDate`
7. **SHOULD** support `lotNumber`
8. **SHOULD** support `serialNumber`
9. **SHOULD** support `distinctIdentifier`

**UDI Guidance:**
- When UDI available: deviceIdentifier is mandatory (1..1 cardinality)
- Only the Human Readable Form (HRF) must be supported for the carrier representation
- When UDI data unavailable (older implants, patient-reported devices): document manufacturer and model information instead

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| identifier | token | Instance identifier |
| device-name | string | Device name (any type) |
| type | token | Device type |
| manufacturer | string | Manufacturer name |
| model | string | Model number |
| status | token | Device status |
| patient | reference | Patient to whom device is affixed |
| organization | reference | Organization responsible for device |
| location | reference | Current device location |
| udi-carrier | string | UDI carrier string |
| udi-di | string | UDI device identifier |
| serial-number | string | Serial number |
| lot-number | string | Lot number |
| url | uri | Network address |

## Examples

### Example 1: Implantable Pacemaker with UDI

```json
{
  "resourceType": "Device",
  "id": "pacemaker-example",
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
      "entryType": "barcode"
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
      "name": "Cardiac Pacemaker",
      "type": "user-friendly-name"
    }
  ],
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
    "reference": "Patient/example"
  }
}
```

### Example 2: Authoring Device (EHR System)

```json
{
  "resourceType": "Device",
  "id": "ehr-system",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.19.5",
      "value": "DEVICE-001"
    }
  ],
  "deviceName": [
    {
      "name": "Epic EHR",
      "type": "manufacturer-name"
    },
    {
      "name": "Epic 2020",
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

### Example 3: Colonoscope with Product Instance

```json
{
  "resourceType": "Device",
  "id": "colonoscope-example",
  "identifier": [
    {
      "system": "urn:oid:2.16.840.1.113883.3.3719",
      "value": "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234",
      "assigner": {
        "display": "FDA"
      }
    }
  ],
  "status": "active",
  "manufacturer": "Olympus Medical Systems",
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

## Related Resources

### DeviceDefinition

Catalog-level information about device types (the "kind" of device).

```json
{
  "resourceType": "DeviceDefinition",
  "id": "example",
  "identifier": [
    {
      "value": "XYZ-2014"
    }
  ],
  "manufacturerString": "Acme Devices, Inc",
  "deviceName": [
    {
      "name": "Model XYZ Pacemaker",
      "type": "model-name"
    }
  ],
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

### DeviceMetric

Measurement, calculation, or setting capability of a device.

```json
{
  "resourceType": "DeviceMetric",
  "id": "example",
  "identifier": [
    {
      "value": "METRIC-001"
    }
  ],
  "type": {
    "coding": [
      {
        "system": "urn:iso:std:iso:11073:10101",
        "code": "150456",
        "display": "MDC_PULS_OXIM_SAT_O2"
      }
    ]
  },
  "source": {
    "reference": "Device/example"
  },
  "parent": {
    "reference": "DeviceDefinition/example"
  },
  "operationalStatus": "on",
  "category": "measurement"
}
```

## Modifier Elements

The following elements are modifier elements:
- **status** - Affects interpretation of the resource

## Compartments

The Device resource is part of the following compartments:
- Device

## References

- FHIR R4B Device: https://hl7.org/fhir/R4B/device.html
- US Core Implantable Device Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device
- FDA Unique Device Identifier (UDI) System: https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system
- AccessGUDID Database: https://accessgudid.nlm.nih.gov/
- GS1 Standards: https://www.gs1.org/
- HIBCC Standards: https://www.hibcc.org/
- ICCBBA Standards: https://www.iccbba.org/
