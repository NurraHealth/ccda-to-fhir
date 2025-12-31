# FHIR R4B: Location Resource

## Overview

The Location resource represents details and position information for a place where services are provided and resources and participants can be found. A Location can be a physical place (such as a building, room, or vehicle), a virtual place (such as a telehealth consultation space), or a jurisdiction (such as a city or state). Locations can range from large structures like entire buildings or wings to specific rooms, beds, or virtual meeting spaces.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Location |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 3 (Trial Use) |
| Security Category | Business |
| Responsible Work Group | Patient Administration |
| URL | https://hl7.org/fhir/R4B/location.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-location |

## Scope and Usage

**Key Characteristics:**
- Locations include both incidental locations (a place which is used for healthcare without prior designation or authorization) and dedicated, formally appointed locations
- Can represent physical places, mobile units (ambulances, mobile clinics), or virtual spaces (telehealth)
- Locations may have a physical location hierarchy (e.g., wing -> floor -> room -> bed)
- Can have geographical attributes for resource discovery and routing
- Locations can be hierarchical using the `partOf` element
- Not all locations where care is provided are represented as Location resources - some may be represented using Organization or HealthcareService

**Common Use Cases:**
- Hospital buildings, wings, floors, rooms, and beds
- Ambulances and mobile clinics
- Patient homes (for home health services)
- Telehealth virtual rooms
- Jurisdictions (cities, counties, states)
- Pharmacies, laboratories, and imaging centers
- Community service locations

## JSON Structure

```json
{
  "resourceType": "Location",
  "id": "example-hospital-room",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/location",
      "value": "B1-S.F2-R.001"
    },
    {
      "system": "http://hl7.org/fhir/sid/us-npi",
      "value": "1234567890"
    }
  ],
  "status": "active",
  "name": "South Wing, 2nd Floor, Room 001",
  "alias": [
    "Room 201",
    "Patient Room 201"
  ],
  "description": "Private patient room with bathroom",
  "mode": "instance",
  "type": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
          "code": "HOSP",
          "display": "Hospital"
        }
      ]
    },
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "225746001",
          "display": "Patient room"
        }
      ]
    }
  ],
  "telecom": [
    {
      "system": "phone",
      "value": "555-1234",
      "use": "work"
    }
  ],
  "address": {
    "use": "work",
    "line": [
      "123 Main Street",
      "Building 1, South Wing"
    ],
    "city": "Boston",
    "state": "MA",
    "postalCode": "02101",
    "country": "USA"
  },
  "physicalType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
        "code": "ro",
        "display": "Room"
      }
    ]
  },
  "position": {
    "longitude": -71.0589,
    "latitude": 42.3601,
    "altitude": 0
  },
  "managingOrganization": {
    "reference": "Organization/example-hospital",
    "display": "Example Hospital"
  },
  "partOf": {
    "reference": "Location/south-wing-floor-2",
    "display": "South Wing, 2nd Floor"
  },
  "hoursOfOperation": [
    {
      "daysOfWeek": [
        "mon",
        "tue",
        "wed",
        "thu",
        "fri"
      ],
      "allDay": true
    }
  ],
  "availabilityExceptions": "Visiting hours end at 8pm"
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this location. **Must Support**

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

**Common Identifier Systems:**
- **NPI (National Provider Identifier)**: `http://hl7.org/fhir/sid/us-npi` (for healthcare facilities with NPI)
- **CLIA**: `urn:oid:2.16.840.1.113883.4.7` (Clinical Laboratory Improvement Amendments)
- **NAIC**: `urn:oid:2.16.840.1.113883.6.300` (National Association of Insurance Commissioners)

### status (0..1)

Indicates whether the location is in use. **Must Support**

| Type | Values |
|------|--------|
| code | active \| suspended \| inactive |

**Value Set:** http://hl7.org/fhir/ValueSet/location-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| active | Active | The location is operational |
| suspended | Suspended | The location is temporarily closed |
| inactive | Inactive | The location is no longer in use |

### name (1..1)

Name of the location as used by humans. Does not need to be unique. **Required** and **Must Support**

| Type | Description |
|------|-------------|
| string | Human-readable name for the location |

**Guidance:**
- Required by US Core
- Should be the name by which the location is commonly known
- Examples: "South Wing, 2nd Floor, Room 001", "Emergency Department", "Radiology - MRI Suite 1"

### alias (0..*)

A list of alternate names that the location is known as, or was known as, in the past.

| Type | Description |
|------|-------------|
| string[] | Alternate names for the location |

### description (0..1)

Additional details about the location that could be displayed as further information to identify the location beyond its name.

| Type | Description |
|------|-------------|
| string | Description of the location |

### mode (0..1)

Indicates whether a resource instance represents a specific location or a class of locations.

| Type | Values |
|------|--------|
| code | instance \| kind |

**Value Set:** http://hl7.org/fhir/ValueSet/location-mode (Required binding)

**Mode Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| instance | Instance | The Location resource represents a specific instance of a location |
| kind | Kind | The Location resource represents a class of locations |

**Usage:**
- Use `instance` for specific physical locations (e.g., "Room 201")
- Use `kind` for types of locations (e.g., "Isolation Room" as a category)

### type (0..*)

Indicates the type of function performed at the location. **Must Support**

| Type | Description |
|------|-------------|
| CodeableConcept[] | Type of location |

**Value Sets (Extensible binding):**

1. **ServiceDeliveryLocationRoleType** (v3.0.0)
   - System: `http://terminology.hl7.org/CodeSystem/v3-RoleCode`
   - Preferred in FHIR R5/R6

2. **Healthcare Service Location Type Combined** (USCDI-compliant)
   - ValueSet: `http://hl7.org/fhir/us/core/ValueSet/us-core-location-type`
   - Includes HSLOC (NHSN Healthcare Facility Patient Care Location) and SNOMED CT codes

3. **CMS Place of Service Codes**
   - System: `https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set`
   - Required for HIPAA billing

**Common Location Type Codes (RoleCode):**
| Code | Display | System |
|------|---------|--------|
| HOSP | Hospital | http://terminology.hl7.org/CodeSystem/v3-RoleCode |
| ER | Emergency room | http://terminology.hl7.org/CodeSystem/v3-RoleCode |
| ICU | Intensive care unit | http://terminology.hl7.org/CodeSystem/v3-RoleCode |
| PHU | Psychiatric hospital unit | http://terminology.hl7.org/CodeSystem/v3-RoleCode |
| PHARM | Pharmacy | http://terminology.hl7.org/CodeSystem/v3-RoleCode |
| MBL | medical laboratory | http://terminology.hl7.org/CodeSystem/v3-RoleCode |

**USCDI Guidance:**
Systems SHALL support either HSLOC codes or SNOMED CT codes for facility type. Inclusion of CMS POS codes is optional and may be used to meet billing or administrative needs.

### telecom (0..*)

Contact details for the location. **Must Support**

| Element | Type | Description |
|---------|------|-------------|
| system | code | phone \| fax \| email \| pager \| url \| sms \| other |
| value | string | The actual contact point |
| use | code | home \| work \| temp \| old \| mobile |
| rank | positiveInt | Specify preferred order of use (1 = highest) |
| period | Period | Time period when contact point was/is in use |

### address (0..1)

Physical location address. **Must Support**

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| use | code | 0..1 | home \| work \| temp \| old \| billing |
| type | code | 0..1 | postal \| physical \| both |
| text | string | 0..1 | Full text representation |
| line | string | 0..* | Street address components |
| city | string | 0..1 | Municipality name |
| state | string | 0..1 | US state abbreviation |
| postalCode | string | 0..1 | ZIP code |
| country | string | 0..1 | Country name or code |
| period | Period | 0..1 | When address was in use |

**Must Support Sub-elements:**
- `line` (0..*)
- `city` (0..1)
- `state` (0..1) - **Value Set:** USPS Two Letter Alphabetic Codes (Extensible)
- `postalCode` (0..1)

**Guidance:**
Per US Core, address formatting should align with "Project US@ Technical Specification for Patient Addresses Final Version 1.0."

### physicalType (0..1)

Physical form of the location (e.g., building, room, vehicle, bed).

| Type | Description |
|------|-------------|
| CodeableConcept | Physical form |

**Value Set:** http://hl7.org/fhir/ValueSet/location-physical-type (Example binding)

**Common Physical Types:**
| Code | Display |
|------|---------|
| si | Site |
| bu | Building |
| wi | Wing |
| wa | Ward |
| lvl | Level |
| co | Corridor |
| ro | Room |
| bd | Bed |
| ve | Vehicle |
| ho | House |
| ca | Cabinet |
| rd | Road |
| area | Area |
| jdn | Jurisdiction |
| vi | Virtual |

### position (0..1)

The absolute geographic location of the Location, expressed using the WGS84 datum.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| longitude | decimal | 1..1 | Longitude with WGS84 datum |
| latitude | decimal | 1..1 | Latitude with WGS84 datum |
| altitude | decimal | 0..1 | Altitude with WGS84 datum |

**Constraints:**
- Longitude: -180.0 to +180.0 (0° is Greenwich meridian)
- Latitude: -90.0 to +90.0 (0° is equator)

### managingOrganization (0..1)

The organization responsible for the provisioning and upkeep of the location. **Must Support**

| Type | Description |
|------|-------------|
| Reference(Organization) | Organization managing this location |

**Reference to:** US Core Organization Profile

### partOf (0..1)

Another Location of which this Location is physically a part of.

| Type | Description |
|------|-------------|
| Reference(Location) | Parent location |

**Usage:**
- Used to create location hierarchies (e.g., Building -> Floor -> Room -> Bed)
- Examples:
  - Room is part of Floor
  - Floor is part of Building
  - Bed is part of Room

### hoursOfOperation (0..*)

Hours of operation for the location.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| daysOfWeek | code | 0..* | mon \| tue \| wed \| thu \| fri \| sat \| sun |
| allDay | boolean | 0..1 | Always open (24/7) |
| openingTime | time | 0..1 | Opening time |
| closingTime | time | 0..1 | Closing time |

**Constraints:**
- If `allDay` is true, `openingTime` and `closingTime` should not be provided

### availabilityExceptions (0..1)

Description of when the location is not available.

| Type | Description |
|------|-------------|
| string | Description of availability exceptions |

**Examples:**
- "Visiting hours end at 8pm"
- "Closed on federal holidays"
- "Emergency entrance only after hours"

### endpoint (0..*)

Technical endpoints providing access to services operated for the location.

| Type | Description |
|------|-------------|
| Reference(Endpoint)[] | Technical endpoints |

## US Core Conformance Requirements

For US Core Location profile compliance:

1. **SHALL** support `name` (1..1) - Required
2. **SHALL** support `identifier` (0..*)
3. **SHALL** support `status` (0..1)
4. **SHALL** support `type` (0..*)
5. **SHALL** support `telecom` (0..*)
6. **SHALL** support `address` (0..1)
   - **SHALL** support `address.line` (0..*)
   - **SHALL** support `address.city` (0..1)
   - **SHALL** support `address.state` (0..1)
   - **SHALL** support `address.postalCode` (0..1)
7. **SHALL** support `managingOrganization` (0..1)

## Search Parameters (Mandatory for US Core)

Servers SHALL support:

1. **name** - Search by location name
   - Type: string
   - Expression: `Location.name | Location.alias`
   - Example: `GET [base]/Location?name=Emergency`

2. **address** - Search by physical location
   - Type: string
   - Expression: `Location.address`
   - Example: `GET [base]/Location?address=Boston`

**Optional (SHOULD support):**
- **address-city** - `Location.address.city`
- **address-state** - `Location.address.state`
- **address-postalcode** - `Location.address.postalCode`

**Other Search Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id |
| identifier | token | Identifier |
| status | token | active \| suspended \| inactive |
| type | token | Type of location |
| organization | reference | Managing organization |
| partof | reference | Parent location |
| near | special | Geographic proximity search |
| operational-status | token | Current operational status |
| endpoint | reference | Technical endpoint |

## Referenced Profiles

Location resources reference:
- **US Core Organization Profile** (managingOrganization)

## Resources That Reference Location

Location is referenced by:
- **US Core Encounter Profile** (Encounter.location.location)
- **US Core Immunization Profile** (Immunization.location)
- MedicationDispense (location)
- Observation (Event Location Extension)
- Procedure (location)
- DiagnosticReport (Event Location Extension)
- ServiceRequest (locationReference)

## SMART Scopes

Resource-level scopes for Location data access:
- `patient/Location.rs` - Read and search Location resources in patient context
- `user/Location.rs` - Read and search Location resources in user context
- `system/Location.rs` - Read and search Location resources in system context

## Usage Patterns

### Direct References

Location is directly referenced in:
- `Encounter.location.location` (SHALL support in US Core Encounter)
- `Immunization.location`

### Indirect References via Encounter

The following US Core profiles access location information indirectly through Encounter:
- DiagnosticReport for Laboratory Results
- MedicationDispense
- Observation (Clinical Result and Screening Assessment)
- Procedure
- ServiceRequest

**Guidance from US Core:**
Systems **SHOULD** reference the location element for all resources where available. Systems **MAY** use the standard Event Location Extension for DiagnosticReport and Observation profiles.

### Location Hierarchies

Locations can be organized hierarchically using the `partOf` element:

```
Hospital (Organization)
  └─ Building 1 (Location: partOf=null)
      └─ South Wing (Location: partOf=Building 1)
          └─ Floor 2 (Location: partOf=South Wing)
              └─ Room 201 (Location: partOf=Floor 2)
                  └─ Bed A (Location: partOf=Room 201)
```

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| dom-2 | If the resource is contained, it SHALL NOT contain nested Resources |
| dom-3 | If the resource is contained, it SHALL be referred to from elsewhere in the resource or SHALL refer to the containing resource |
| dom-4 | If a resource is contained, it SHALL NOT have a meta.versionId or a meta.lastUpdated |
| dom-5 | If a resource is contained, it SHALL NOT have a security label |
| dom-6 | A resource should have narrative for robust management |

## Modifier Elements

None. The Location resource does not contain modifier elements.

## Compartments

The Location resource is not part of any compartments.

## Examples from Standards

### Example 1: Hospital Room (from FHIR Core Specification)

```json
{
  "resourceType": "Location",
  "id": "1",
  "name": "South Wing, second floor",
  "description": "Second floor of the Old South Wing, formerly in use by Psychiatry",
  "mode": "instance",
  "telecom": [
    {
      "system": "phone",
      "value": "2328",
      "use": "work"
    },
    {
      "system": "fax",
      "value": "2329",
      "use": "work"
    },
    {
      "system": "email",
      "value": "second wing admissions"
    },
    {
      "system": "url",
      "value": "http://sampleorg.com/southwing",
      "use": "work"
    }
  ],
  "address": {
    "use": "work",
    "line": ["Galapagosweg 91, Building A"],
    "city": "Den Burg",
    "postalCode": "9105 PZ",
    "country": "NLD"
  },
  "physicalType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
        "code": "wi",
        "display": "Wing"
      }
    ]
  },
  "managingOrganization": {
    "reference": "Organization/f001"
  }
}
```

### Example 2: Patient's Home (for Home Health)

```json
{
  "resourceType": "Location",
  "id": "ph",
  "status": "active",
  "name": "Patient's Home",
  "description": "Patient's Home",
  "mode": "kind",
  "type": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
          "code": "PTRES",
          "display": "Patient's Residence"
        }
      ]
    }
  ],
  "physicalType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
        "code": "ho",
        "display": "House"
      }
    ]
  }
}
```

### Example 3: Ambulance (Mobile Location)

```json
{
  "resourceType": "Location",
  "id": "amb",
  "status": "active",
  "name": "BUMC Ambulance",
  "description": "Ambulance provided by Burgers University Medical Center",
  "mode": "kind",
  "type": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
          "code": "AMB",
          "display": "Ambulance"
        }
      ]
    }
  ],
  "physicalType": {
    "coding": [
      {
        "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
        "code": "ve",
        "display": "Vehicle"
      }
    ]
  },
  "managingOrganization": {
    "reference": "Organization/f001"
  }
}
```

## Changes in Recent Versions

### R4 to R4B
- Added `form` element to Encounter.location for physical form/layout
- Enhanced support for virtual locations

### US Core 7.0.0 to 8.0.1
- Mandatory and must-support data elements list revised
- Updated guidance on address formatting
- Added multiple value set bindings for type element

## References

- FHIR R4B Location: https://hl7.org/fhir/R4B/location.html
- US Core Location Profile v8.0.1: http://hl7.org/fhir/us/core/StructureDefinition/us-core-location
- US Core Location Type ValueSet: http://hl7.org/fhir/us/core/ValueSet/us-core-location-type
- RoleCode CodeSystem: http://terminology.hl7.org/CodeSystem/v3-RoleCode
- Location Physical Type: http://terminology.hl7.org/CodeSystem/location-physical-type
- CMS Place of Service Codes: https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set
