# Location Mapping: C-CDA Service Delivery Location ↔ FHIR Location

This document provides detailed mapping guidance between C-CDA Service Delivery Location and FHIR `Location` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Service Delivery Location (`2.16.840.1.113883.10.20.22.4.32`) | `Location` |
| Used in: Encounter Activity, Procedure Activity, Planned Encounter | Referenced by: `Encounter`, `Procedure`, `Immunization`, etc. |
| Document Header `encompassingEncounter/location/healthCareFacility` | `Location` |

## Source Locations

Locations can appear in multiple places in C-CDA:

1. **Encounter Activity:** `participant[@typeCode='LOC']/participantRole[@classCode='SDLOC']`
2. **Procedure Activity:** `participant[@typeCode='LOC']/participantRole[@classCode='SDLOC']`
3. **Planned Encounter:** `participant[@typeCode='LOC']/participantRole[@classCode='SDLOC']`
4. **Document Header:** `encompassingEncounter/location/healthCareFacility` (similar structure, no template ID)

**Deduplication:** The same location referenced in multiple places should consolidate into a single FHIR Location resource. Use facility identifier (e.g., NPI) and name matching to detect duplicates.

## Mapping Strategy

### Resource Creation

Unlike some C-CDA elements that embed location data within other resources (e.g., Encounter.location reference), this mapping creates **separate Location resources** that are then referenced.

**Output Bundle Structure:**
```json
{
  "resourceType": "Bundle",
  "entry": [
    {
      "resource": {
        "resourceType": "Location",
        "id": "location-1",
        ...
      }
    },
    {
      "resource": {
        "resourceType": "Encounter",
        "location": [{
          "location": {"reference": "Location/location-1"}
        }]
      }
    }
  ]
}
```

### Location ID Generation

Generate Location resource IDs using one of these strategies:

1. **From NPI:** If `id[@root='2.16.840.1.113883.4.6']` exists, use `"location-npi-{extension}"`
2. **From Name:** Hash the facility name to generate stable ID
3. **From OID:** Use the first `id/@root` + `@extension` combination
4. **UUID:** Generate new UUID for locations without identifiers

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform | Notes |
|------------|-----------|-----------|-------|
| `participantRole/templateId[@root='...4.32']` | `meta.tag` | Create coding tag | Document source template |
| `participantRole/id` | `identifier` | [ID → Identifier](#identifier-mapping) | Facility identifiers |
| `participantRole/code` | `type` | [Code → CodeableConcept](#type-mapping) | Facility type classification |
| `participantRole/addr` | `address` | [Address Mapping](#address-mapping) | Physical location address |
| `participantRole/telecom` | `telecom` | [Telecom Mapping](#telecom-mapping) | Contact information |
| `playingEntity/name` | `name` | String extraction | **Required** facility name |
| `playingEntity/@classCode='PLC'` | — | Validation only | Confirms this is a place |
| `participantRole/scopingEntity` | `managingOrganization` | Reference(Organization) | From location's scopingEntity when Organization registered |
| *Inferred from data* | `status` | Fixed: `"active"` | Default assumption |

### Identifier Mapping

**C-CDA:**
```xml
<participantRole classCode="SDLOC">
  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  <id root="2.16.840.1.113883.4.7" extension="11D0265516"/>
  <id root="2.16.840.1.113883.6.300" extension="98765"/>
</participantRole>
```

**FHIR:**
```json
{
  "identifier": [
    {
      "system": "http://hl7.org/fhir/sid/us-npi",
      "value": "1234567890"
    },
    {
      "system": "urn:oid:2.16.840.1.113883.4.7",
      "value": "11D0265516"
    },
    {
      "system": "urn:oid:2.16.840.1.113883.6.300",
      "value": "98765"
    }
  ]
}
```

**OID to System URI Mapping:**

| C-CDA Root OID | FHIR System URI | Identifier Type |
|----------------|-----------------|-----------------|
| `2.16.840.1.113883.4.6` | `http://hl7.org/fhir/sid/us-npi` | National Provider Identifier (NPI) |
| `2.16.840.1.113883.4.7` | `urn:oid:2.16.840.1.113883.4.7` | Clinical Laboratory Improvement Amendments (CLIA) |
| `2.16.840.1.113883.6.300` | `urn:oid:2.16.840.1.113883.6.300` | National Association of Insurance Commissioners (NAIC) |
| *(other)* | `urn:oid:{root}` | Generic OID-based identifier |

**Handling nullFlavor:**

If `id/@nullFlavor` is present (e.g., "NA", "NI"), the identifier may be omitted or represented as:

```json
{
  "identifier": [{
    "system": "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
    "value": "NA"
  }]
}
```

**Multiple Identifiers:**
A single location may have multiple identifiers. All should be included in the `identifier` array.

### Type Mapping

The facility type code maps to FHIR `Location.type` array.

**C-CDA:**
```xml
<code code="1061-3" codeSystem="2.16.840.1.113883.6.259"
      displayName="Hospital">
  <translation code="22232009" codeSystem="2.16.840.1.113883.6.96"
               displayName="Hospital"/>
  <translation code="21" codeSystem="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set"
               displayName="Inpatient Hospital"/>
</code>
```

**FHIR:**
```json
{
  "type": [
    {
      "coding": [
        {
          "system": "https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html",
          "code": "1061-3",
          "display": "Hospital"
        },
        {
          "system": "http://snomed.info/sct",
          "code": "22232009",
          "display": "Hospital"
        },
        {
          "system": "https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set",
          "code": "21",
          "display": "Inpatient Hospital"
        }
      ]
    }
  ]
}
```

**Code System OID to URI Mapping:**

| C-CDA Code System OID | FHIR System URI | Name |
|-----------------------|-----------------|------|
| `2.16.840.1.113883.6.259` | `https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html` | HealthcareServiceLocation (HSLOC) |
| `2.16.840.1.113883.6.96` | `http://snomed.info/sct` | SNOMED CT |
| `https://...place-of-service-codes/...` | *(use as-is)* | CMS Place of Service Codes |
| `2.16.840.1.113883.5.111` | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` | RoleCode (v3) |

**Translation Codes:**
- If the primary code is from one system and translation codes from others, include all as separate `coding` entries within a single `CodeableConcept`
- Do NOT create separate `type` array entries for each code system; combine them in one `type[0].coding` array

**Common HSLOC to SNOMED CT Mappings:**

| HSLOC Code | HSLOC Display | SNOMED CT Code | SNOMED CT Display |
|------------|---------------|----------------|-------------------|
| 1061-3 | Hospital | 22232009 | Hospital |
| 1118-1 | Emergency Department | 225728007 | Accident and Emergency department |
| 1021-7 | Critical Care Unit | 309904001 | Intensive care unit |
| 1108-2 | Operating Room | 309914001 | Operating theater |
| 1160-1 | Urgent Care Center | *(none)* | — |

### Address Mapping

**C-CDA:**
```xml
<addr use="WP">
  <streetAddressLine>1001 Village Avenue</streetAddressLine>
  <streetAddressLine>Building 1, South Wing</streetAddressLine>
  <city>Portland</city>
  <state>OR</state>
  <postalCode>99123</postalCode>
  <country>US</country>
</addr>
```

**FHIR:**
```json
{
  "address": {
    "use": "work",
    "line": [
      "1001 Village Avenue",
      "Building 1, South Wing"
    ],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123",
    "country": "US"
  }
}
```

**Address Use Mapping:**

| C-CDA @use | FHIR use |
|------------|----------|
| `HP` | `home` |
| `WP` | `work` |
| `TMP` | `temp` |
| `BAD` | `old` |
| `PHYS` | `work` |
| `PST` | `work` |
| *(none)* | *(omit)* |

**Address Type:**
FHIR `type` is typically `"physical"` for facility addresses. If the address explicitly represents a mailing address only, use `"postal"`.

**Multiple Street Lines:**
- Each `streetAddressLine` element becomes an entry in the `line` array
- Preserve order

**Missing Elements:**
If address elements are missing in C-CDA, omit them in FHIR (do not use null values).

### Telecom Mapping

**C-CDA:**
```xml
<telecom use="WP" value="tel:+1(555)555-5000"/>
<telecom use="WP" value="fax:+1(555)555-5001"/>
<telecom use="WP" value="mailto:contact@hospital.example.org"/>
<telecom use="WP" value="http://www.hospital.example.org"/>
```

**FHIR:**
```json
{
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-5000",
      "use": "work"
    },
    {
      "system": "fax",
      "value": "+1(555)555-5001",
      "use": "work"
    },
    {
      "system": "email",
      "value": "contact@hospital.example.org",
      "use": "work"
    },
    {
      "system": "url",
      "value": "http://www.hospital.example.org",
      "use": "work"
    }
  ]
}
```

**URI Scheme to System Mapping:**

| C-CDA URI Scheme | FHIR system |
|------------------|-------------|
| `tel:` | `phone` |
| `fax:` | `fax` |
| `mailto:` | `email` |
| `http:` or `https:` | `url` |
| `sms:` | `sms` |
| *(other)* | `other` |

**Value Extraction:**
- Remove the URI scheme prefix (`tel:`, `mailto:`, etc.) from the value
- Store only the actual contact value in FHIR `value` field

**Use Code Mapping:**

| C-CDA @use | FHIR use |
|------------|----------|
| `HP` | `home` |
| `WP` | `work` |
| `MC` | `mobile` |
| `TMP` | `temp` |
| `BAD` | `old` |
| *(none)* | *(omit)* |

### Name Mapping

**C-CDA:**
```xml
<playingEntity classCode="PLC">
  <name>Community Health and Hospitals</name>
</playingEntity>
```

**FHIR:**
```json
{
  "name": "Community Health and Hospitals"
}
```

**Required:** The `name` element is mandatory in both C-CDA Service Delivery Location and US Core Location profile.

**Text Extraction:**
- Extract text content from `playingEntity/name`
- If name contains child elements (rare), concatenate text content

### Status Mapping

**C-CDA:** No explicit status element in Service Delivery Location template.

**FHIR:**
```json
{
  "status": "active"
}
```

**Default:** Assume `"active"` unless context suggests otherwise.

**Inference Logic:**
- If location appears in a completed encounter → still assume `"active"` (the location exists and is operational)
- Only set to `"inactive"` if explicit information indicates the facility is closed
- Use `"suspended"` for temporarily closed facilities (not inferable from C-CDA)

**Status is Not Must Support:** While status has a cardinality of 0..1 in US Core, it is not a Must Support element, so omitting it is acceptable.

### Mode and Physical Type

**Mode:**
C-CDA Service Delivery Location represents specific instances of locations, not classes of locations.

```json
{
  "mode": "instance"
}
```

**Physical Type:**
Not directly represented in C-CDA. Can be inferred from the location type code.

**Inference from Type Code:**

| HSLOC Code | Physical Type Code | Physical Type Display |
|------------|-------------------|----------------------|
| 1061-3 (Hospital) | `bu` | Building |
| 1118-1 (Emergency Department) | `wa` | Ward |
| 1108-2 (Operating Room) | `ro` | Room |
| 1021-7 (ICU) | `wa` | Ward |
| 1160-1 (Urgent Care) | `bu` | Building |
| 1117-3 (Clinic) | `bu` | Building |

**Physical Type CodeSystem:** `http://terminology.hl7.org/CodeSystem/location-physical-type`

**Optional:** Including `physicalType` is optional and should only be added when there's high confidence in the inference.

### Managing Organization

**C-CDA:** Service Delivery Location `participantRole/scopingEntity` represents the organization that owns or manages the location.

**FHIR:**
```json
{
  "managingOrganization": {
    "reference": "Organization/org-hospital",
    "display": "Community Health and Hospitals"
  }
}
```

**Mapping Strategy:**
1. Extract organization from `participantRole/scopingEntity` identifiers
2. Generate Organization ID from scopingEntity identifiers
3. Create reference only if Organization resource exists in registry (avoids dangling references)
4. If no scopingEntity or Organization not registered, omit `managingOrganization`

**Note:** The implementation extracts managingOrganization directly from the location's scopingEntity element, not from encounter or procedure context. This ensures the reference accurately represents the organization specified in the C-CDA location structure itself.

## Special Cases

### Patient's Home

**C-CDA:**
```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
    <id nullFlavor="NA"/>
    <code code="PTRES" codeSystem="2.16.840.1.113883.5.111"
          displayName="Patient's Residence"/>
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

**FHIR:**
```json
{
  "resourceType": "Location",
  "id": "location-patient-home",
  "identifier": [],
  "status": "active",
  "name": "Patient's Home",
  "mode": "kind",
  "type": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "PTRES",
      "display": "Patient's Residence"
    }]
  }],
  "address": {
    "use": "home",
    "line": ["456 Oak Street"],
    "city": "Seattle",
    "state": "WA",
    "postalCode": "98101"
  },
  "physicalType": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
      "code": "ho",
      "display": "House"
    }]
  }
}
```

**Notes:**
- Use `mode = "kind"` (class of locations) for generic "Patient's Home"
- If specific patient address is included, could use `mode = "instance"`
- No identifier is expected (nullFlavor="NA")
- Consider whether to create one shared "Patient's Home" location or per-patient instances

### Ambulance / Mobile Location

**C-CDA:**
```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
    <id root="2.16.840.1.113883.4.6" extension="9988776655"/>
    <code code="AMB" codeSystem="2.16.840.1.113883.5.111"
          displayName="Ambulance"/>
    <addr use="WP">
      <streetAddressLine>Emergency Services Department</streetAddressLine>
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
    </addr>
    <playingEntity classCode="PLC">
      <name>Community Health Ambulance Unit 5</name>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR:**
```json
{
  "resourceType": "Location",
  "id": "location-ambulance-5",
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "9988776655"
  }],
  "status": "active",
  "name": "Community Health Ambulance Unit 5",
  "mode": "kind",
  "type": [{
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
      "code": "AMB",
      "display": "Ambulance"
    }]
  }],
  "physicalType": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
      "code": "ve",
      "display": "Vehicle"
    }]
  },
  "address": {
    "use": "work",
    "line": [
      "Emergency Services Department",
      "1001 Village Avenue"
    ],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  }
}
```

**Notes:**
- Address represents the base station, not current physical location
- Use `physicalType = "ve"` (vehicle)
- `mode = "kind"` for generic ambulance categories, or `instance` for specific numbered units

### encompassingEncounter/location

The document header `encompassingEncounter/location` uses a slightly different structure but represents the same concept.

**C-CDA:**
```xml
<componentOf>
  <encompassingEncounter>
    <location>
      <healthCareFacility>
        <id root="2.16.840.1.113883.19.5.9999.1"/>
        <code code="1160-1" codeSystem="2.16.840.1.113883.6.259"
              displayName="Urgent Care Center"/>
        <location>
          <name>Community Health and Hospitals</name>
          <addr>
            <streetAddressLine>1001 Village Avenue</streetAddressLine>
            <city>Portland</city>
            <state>OR</state>
            <postalCode>99123</postalCode>
          </addr>
        </location>
        <serviceProviderOrganization>
          <name>Community Health and Hospitals</name>
        </serviceProviderOrganization>
      </healthCareFacility>
    </location>
  </encompassingEncounter>
</componentOf>
```

**FHIR:**
```json
{
  "resourceType": "Location",
  "id": "location-encompassing",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5.9999",
    "value": "1"
  }],
  "status": "active",
  "name": "Community Health and Hospitals",
  "type": [{
    "coding": [{
      "system": "https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html",
      "code": "1160-1",
      "display": "Urgent Care Center"
    }]
  }],
  "address": {
    "use": "work",
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  },
  "managingOrganization": {
    "reference": "Organization/org-provider",
    "display": "Community Health and Hospitals"
  }
}
```

**Mapping Differences:**

| encompassingEncounter Element | Service Delivery Location Element | FHIR Location |
|-------------------------------|-----------------------------------|---------------|
| `healthCareFacility/id` | `participantRole/id` | `identifier` |
| `healthCareFacility/code` | `participantRole/code` | `type` |
| `healthCareFacility/location/name` | `playingEntity/name` | `name` |
| `healthCareFacility/location/addr` | `participantRole/addr` | `address` |
| `serviceProviderOrganization` | *(inferred from context)* | `managingOrganization` |

**Template ID:** Note that `healthCareFacility` does NOT have the Service Delivery Location template ID (`2.16.840.1.113883.10.20.22.4.32`), but the mapping is conceptually identical.

## Complete Example

### Input: C-CDA Service Delivery Location

```xml
<participant typeCode="LOC">
  <time>
    <low value="20200315103000-0500"/>
    <high value="20200315120000-0500"/>
  </time>
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>

    <!-- NPI -->
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>

    <!-- CLIA -->
    <id root="2.16.840.1.113883.4.7" extension="11D0265516"/>

    <!-- Facility Type: Hospital (HSLOC primary, SNOMED translation) -->
    <code code="1061-3" codeSystem="2.16.840.1.113883.6.259"
          displayName="Hospital">
      <translation code="22232009" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Hospital"/>
    </code>

    <!-- Address -->
    <addr use="WP">
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <streetAddressLine>Building 1, South Wing</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
      <country>US</country>
    </addr>

    <!-- Contact -->
    <telecom use="WP" value="tel:+1(555)555-5000"/>
    <telecom use="WP" value="mailto:info@hospital.example.org"/>

    <!-- Facility Name -->
    <playingEntity classCode="PLC">
      <name>Community Health and Hospitals</name>
    </playingEntity>
  </participantRole>
</participant>
```

### Output: FHIR Location Resource

```json
{
  "resourceType": "Location",
  "id": "location-npi-1234567890",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"
    ]
  },
  "identifier": [
    {
      "system": "http://hl7.org/fhir/sid/us-npi",
      "value": "1234567890"
    },
    {
      "system": "urn:oid:2.16.840.1.113883.4.7",
      "value": "11D0265516"
    }
  ],
  "status": "active",
  "name": "Community Health and Hospitals",
  "mode": "instance",
  "type": [
    {
      "coding": [
        {
          "system": "https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html",
          "code": "1061-3",
          "display": "Hospital"
        },
        {
          "system": "http://snomed.info/sct",
          "code": "22232009",
          "display": "Hospital"
        }
      ]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-5000",
      "use": "work"
    },
    {
      "system": "email",
      "value": "info@hospital.example.org",
      "use": "work"
    }
  ],
  "address": {
    "use": "work",
    "line": [
      "1001 Village Avenue",
      "Building 1, South Wing"
    ],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123",
    "country": "US"
  },
  "physicalType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
        "code": "bu",
        "display": "Building"
      }
    ]
  },
  "managingOrganization": {
    "reference": "Organization/org-hospital",
    "display": "Community Health and Hospitals"
  }
}
```

### Output: Referenced in Encounter

```json
{
  "resourceType": "Encounter",
  "id": "encounter-1",
  "identifier": [...],
  "status": "finished",
  "class": {...},
  "type": [...],
  "subject": {"reference": "Patient/patient-1"},
  "period": {
    "start": "2020-03-15T10:30:00-05:00",
    "end": "2020-03-15T12:00:00-05:00"
  },
  "location": [
    {
      "location": {
        "reference": "Location/location-npi-1234567890",
        "display": "Community Health and Hospitals"
      },
      "status": "completed",
      "period": {
        "start": "2020-03-15T10:30:00-05:00",
        "end": "2020-03-15T12:00:00-05:00"
      }
    }
  ],
  "serviceProvider": {
    "reference": "Organization/org-hospital"
  }
}
```

## FHIR to C-CDA Mapping

### Core Reverse Mappings

| FHIR Path | C-CDA Path | Transform | Notes |
|-----------|------------|-----------|-------|
| `identifier[system='http://hl7.org/fhir/sid/us-npi']` | `participantRole/id[@root='2.16.840.1.113883.4.6']` | Identifier → II | NPI |
| `identifier[system='urn:oid:...4.7']` | `participantRole/id[@root='2.16.840.1.113883.4.7']` | Identifier → II | CLIA |
| `identifier[system='urn:oid:...6.300']` | `participantRole/id[@root='2.16.840.1.113883.6.300']` | Identifier → II | NAIC |
| `type[0].coding` | `participantRole/code` + `translation` | CodeableConcept → CD | First coding is primary, rest are translations |
| `name` | `playingEntity/name` | String → EN | **Required** |
| `address` | `participantRole/addr` | [Address Reverse](#address-reverse) | Optional but SHOULD |
| `telecom` | `participantRole/telecom` | [Telecom Reverse](#telecom-reverse) | Optional but SHOULD |
| `status`, `managingOrganization` | *(context)* | Not directly mapped | Inferred from usage context |

### Address Reverse Mapping

**FHIR:**
```json
{
  "address": {
    "use": "work",
    "line": [
      "1001 Village Avenue",
      "Building 1, South Wing"
    ],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123",
    "country": "US"
  }
}
```

**C-CDA:**
```xml
<addr use="WP">
  <streetAddressLine>1001 Village Avenue</streetAddressLine>
  <streetAddressLine>Building 1, South Wing</streetAddressLine>
  <city>Portland</city>
  <state>OR</state>
  <postalCode>99123</postalCode>
  <country>US</country>
</addr>
```

**Use Reverse Mapping:**

| FHIR use | C-CDA @use |
|----------|------------|
| `home` | `HP` |
| `work` | `WP` |
| `temp` | `TMP` |
| `old` | `BAD` |
| *(none)* | *(omit)* |

### Telecom Reverse Mapping

**FHIR:**
```json
{
  "telecom": [
    {
      "system": "phone",
      "value": "+1(555)555-5000",
      "use": "work"
    },
    {
      "system": "email",
      "value": "info@hospital.example.org",
      "use": "work"
    }
  ]
}
```

**C-CDA:**
```xml
<telecom use="WP" value="tel:+1(555)555-5000"/>
<telecom use="WP" value="mailto:info@hospital.example.org"/>
```

**System to URI Scheme:**

| FHIR system | C-CDA URI prefix |
|-------------|------------------|
| `phone` | `tel:` |
| `fax` | `fax:` |
| `email` | `mailto:` |
| `url` | `http:` or `https:` |
| `sms` | `sms:` |
| `other` | *(use value as-is)* |

## Implementation Considerations

### Deduplication Strategy

**Problem:** The same location may appear multiple times in a C-CDA document (multiple encounters at same hospital).

**Solution:** Deduplicate locations by:

1. **NPI Match:** If two Service Delivery Locations have the same NPI identifier, they are the same location
2. **Name + Address Match:** If name and city/state match exactly, they are likely the same location
3. **ID Match:** If any identifier matches, they are the same location

**Approach:**
- Maintain a location registry during conversion
- Generate consistent IDs for duplicate locations
- Create only one Location resource per unique facility

### Identifier Priority

When multiple identifiers exist, use this priority for generating Location.id:

1. NPI (most stable and widely used)
2. CLIA (for laboratories)
3. NAIC (for insurance-related facilities)
4. First listed identifier
5. Name-based hash
6. Generated UUID

### Missing Required Elements

**C-CDA Requirement:** `playingEntity/name` is required (1..1)

**If Missing:**
- Use `code/@displayName` as fallback name
- Use "Unknown Location" as last resort
- Log a warning

**FHIR Requirement:** `name` is required (1..1) in US Core

**If Missing:**
- Attempt inference from context
- Use identifier value as name if nothing else available
- Conversion should fail with validation error if name cannot be determined

### Physical Type Inference

Physical type inference should be conservative:

- **Only infer** when there's high confidence (e.g., "Operating Room" → "room")
- **Do not infer** for ambiguous types (e.g., "Hospital" could be building, campus, organization)
- **Omit** `physicalType` when uncertain

### Organization Linking

The `managingOrganization` reference requires creating or referencing an Organization resource:

1. Extract organization from encounter `serviceProvider`
2. If not available, extract from document `custodian`
3. Create Organization resource if needed
4. Link Location to Organization using Reference

## US Core Conformance

### Required Elements

- `name` (1..1) - **Must be present**

### Must Support Elements

The following elements are Must Support and should be populated when data is available:

- `identifier` (0..*) - Include all facility identifiers
- `status` (0..1) - Default to `"active"`
- `type` (0..*) - Map from C-CDA facility type code
- `telecom` (0..*) - Include all contact information
- `address` (0..1) - Include facility address
- `address.line` (0..*) - All street address lines
- `address.city` (0..1) - City
- `address.state` (0..1) - State
- `address.postalCode` (0..1) - ZIP code
- `managingOrganization` (0..1) - Link to managing organization

### Profile Declaration

Always include the US Core profile in `meta.profile`:

```json
{
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"
    ]
  }
}
```

## Value Set Compliance

### Location Type

US Core specifies extensible binding to multiple value sets:

1. **ServiceDeliveryLocationRoleType** (v3-RoleCode)
2. **US Core Location Type** (HSLOC + SNOMED CT)
3. **CMS Place of Service Codes**

**Compliance Strategy:**
- Map HSLOC codes directly (most common in C-CDA)
- Include SNOMED CT translations when available
- Include CMS POS codes for billing interoperability
- Extensible binding allows other code systems

### Address State

Use USPS two-letter state abbreviations:
- Extensible binding
- Accept any state code from C-CDA
- Validate against USPS list when possible

## References

- C-CDA Service Delivery Location Template: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ServiceDeliveryLocation.html
- US Core Location Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-location
- C-CDA on FHIR Encounter Mapping (Location references): https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html
- FHIR Location Resource: https://hl7.org/fhir/R4B/location.html
- HSLOC Code System: https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html
- CMS Place of Service Codes: https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set
- Location Physical Type: http://terminology.hl7.org/CodeSystem/location-physical-type
