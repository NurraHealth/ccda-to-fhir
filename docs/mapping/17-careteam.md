# C-CDA to FHIR Mapping: CareTeam

**FHIR Resource:** [CareTeam](http://hl7.org/fhir/R4/careteam.html)

**US Core Profile:** [US Core CareTeam Profile v8.0.1](http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-careteam.html)

**C-CDA Templates:**
- **Care Team Organizer**: `2.16.840.1.113883.10.20.22.4.500` (2019-07-01, 2022-06-01)
- **Care Team Member Act**: `2.16.840.1.113883.10.20.22.4.500.1` (2019-07-01, 2022-06-01)
- **Care Team Type Observation**: `2.16.840.1.113883.10.20.22.4.500.2` (2019-07-01)
- **documentationOf/serviceEvent/performer**: Care team members in document header (alternative)

**Section:** Care Teams Section (`2.16.840.1.113883.10.20.22.2.500`)

---

## Overview

C-CDA supports two distinct approaches for representing care team information, both of which can be mapped to FHIR CareTeam resources:

1. **Structured Care Team Organizer** (Recommended)
   - Discrete, computable representation
   - Supports multiple care teams with types, leads, and members
   - Appears in Care Teams Section
   - Maps to one CareTeam resource per organizer

2. **Header-based serviceEvent/performer** (Legacy)
   - Simple list of care providers
   - Appears in document header
   - Common in transition-of-care documents
   - May map to single CareTeam resource aggregating all performers

This specification covers both approaches.

---

## Mapping Approach 1: Structured Care Team Organizer

### Resource Cardinality

**Input:** One Care Team Organizer (1 organizer)

**Output:** One CareTeam resource (1:1 mapping)

### Element Mappings

#### Core Elements

| C-CDA Element | FHIR Element | Cardinality | Transformation Rules |
|---------------|--------------|-------------|---------------------|
| `organizer/id` | `CareTeam.identifier` | 0..* → 0..* | Convert OID-based II to Identifier. See [OID Conversion](#oid-to-identifier-conversion). |
| `organizer/statusCode/@code` | `CareTeam.status` | 1..1 → 1..1 | Map per [Status ConceptMap](#status-conceptmap). |
| `organizer/effectiveTime` | `CareTeam.period` | 1..1 → 0..1 | Convert IVL_TS to Period. See [Time Conversion](#effective-time-to-period). |
| `recordTarget/patientRole` | `CareTeam.subject` | 1..1 → 1..1 | Reference to Patient resource created from recordTarget. |
| `component/act` (Care Team Member) | `CareTeam.participant` | 1..* → 1..* | One participant per member act. See [Participant Mapping](#participant-mapping). |
| `participant[@typeCode='PPRF']` | Identifies team lead | 0..1 → (derived) | Match lead ID to participant; doesn't create separate element but informs ordering/roles. |
| `participant[@typeCode='LOC']` | Derived location info | 0..* → (reference) | May create Location resource; no direct CareTeam.location element in R4. |

#### Optional Elements

| C-CDA Element | FHIR Element | Cardinality | Transformation Rules |
|---------------|--------------|-------------|---------------------|
| `component[type]/observation/value` | `CareTeam.category` | 0..* → 0..* | Map care team type. See [Category Mapping](#category-mapping). |
| N/A (derive from context) | `CareTeam.name` | N/A → 0..1 | Generate human-readable name from team type and patient. Example: "{PatientName} Primary Care Team" |
| `component[encounter]` | `CareTeam.encounter` | 0..* → 0..1 | Reference to Encounter if encounter-focused team. |
| `component[note]` | `CareTeam.note` | 0..1 → 0..* | Convert Comment Activity to Annotation. |
| `code/originalText/reference` or `sdtcText/reference` | `CareTeam.text` (narrative) | 0..1 → 1..1 | Extract narrative from section text. |
| N/A (infer from context) | `CareTeam.managingOrganization` | N/A → 0..* | Reference organization from custodian or first member's representedOrganization. |
| N/A | `CareTeam.reasonReference` | N/A → 0..* | Not explicitly in C-CDA Care Team Organizer; may infer from document context (e.g., condition-focused team references Condition). |

---

### OID to Identifier Conversion

C-CDA `organizer/id` uses OID-based identifiers. Convert to FHIR Identifier:

**C-CDA:**
```xml
<id root="2.16.840.1.113883.19.5.99999.1" extension="careteam-primary-123"/>
```

**FHIR:**
```json
{
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "careteam-primary-123"
  }]
}
```

**Rules:**
- `root` → `identifier.system` (prefix with "urn:oid:")
- `extension` → `identifier.value`
- If no extension, use root as value with system "urn:ietf:rfc:3986"

---

### Status ConceptMap

Map C-CDA `statusCode/@code` to FHIR `CareTeam.status`:

| C-CDA statusCode | FHIR status | Notes |
|------------------|-------------|-------|
| `active` | `active` | Currently coordinating care |
| `completed` | `inactive` | No longer active |
| `aborted` | `inactive` | Terminated prematurely |
| `suspended` | `suspended` | Temporarily on hold |
| `nullified` | `entered-in-error` | Should not have existed |
| `obsolete` | `inactive` | Replaced by newer version |

**Default:** If statusCode missing or unrecognized, default to `active`.

---

### Effective Time to Period

Convert C-CDA `effectiveTime` (IVL_TS) to FHIR `period`:

**C-CDA:**
```xml
<effectiveTime>
  <low value="20230115"/>
  <high value="20240115"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "period": {
    "start": "2023-01-15",
    "end": "2024-01-15"
  }
}
```

**Rules:**
- `effectiveTime/low/@value` → `period.start` (convert TS to date or dateTime)
- `effectiveTime/high/@value` → `period.end` (omit if ongoing team)
- If only single `effectiveTime/@value`, map to `period.start`
- Use [C-CDA Timestamp Conversion](./00-overview.md#timestamp-conversion)

---

### Category Mapping

Map Care Team Type Observation to `CareTeam.category`:

**C-CDA:**
```xml
<component>
  <observation classCode="OBS" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
    <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
    <value xsi:type="CD" code="LA27976-2" codeSystem="2.16.840.1.113883.6.1"
           displayName="Longitudinal care-coordination focused care team"/>
  </observation>
</component>
```

**FHIR:**
```json
{
  "category": [{
    "coding": [{
      "system": "http://loinc.org",
      "code": "LA27976-2",
      "display": "Longitudinal care-coordination focused care team"
    }]
  }]
}
```

**Supported LOINC Answer Codes:**

| LOINC Code | Display Name |
|------------|--------------|
| `LA27976-2` | Longitudinal care-coordination focused care team |
| `LA27977-0` | Episode of care focused care team |
| `LA28865-6` | Condition-focused care team |
| `LA28866-4` | Encounter-focused care team |
| `LA28867-2` | Event-focused care team |

**Multiple Types:** If multiple type observations exist, create multiple category entries.

---

### Participant Mapping

Each Care Team Member Act maps to one `CareTeam.participant`:

**C-CDA:**
```xml
<component>
  <act classCode="PCPR" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
    <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
    <statusCode code="active"/>
    <effectiveTime>
      <low value="20230115"/>
      <high value="20240630"/>
    </effectiveTime>
    <performer>
      <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                   displayName="Primary Care Physician"/>
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
        <telecom use="WP" value="tel:+1(555)555-5100"/>
        <assignedPerson>
          <name>
            <prefix>Dr.</prefix>
            <given>John</given>
            <family>Smith</family>
            <suffix>MD</suffix>
          </name>
        </assignedPerson>
        <representedOrganization>
          <id root="2.16.840.1.113883.19.5" extension="org-123"/>
          <name>Community Health Clinic</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
  </act>
</component>
```

**FHIR:**
```json
{
  "participant": [{
    "role": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
        "code": "PCP",
        "display": "Primary Care Physician"
      }]
    }],
    "member": {
      "reference": "PractitionerRole/practitionerrole-npi-1234567890",
      "display": "Dr. John Smith"
    },
    "period": {
      "start": "2023-01-15",
      "end": "2024-06-30"
    }
  }]
}
```

#### Participant Element Mappings

| C-CDA Element | FHIR Element | Transformation |
|---------------|--------------|----------------|
| `performer/functionCode` | `participant.role` | Map to CodeableConcept. System depends on codeSystem. See [Function Code Mapping](#function-code-mapping). |
| `performer/assignedEntity` | `participant.member` | Create Practitioner + PractitionerRole resources. Reference PractitionerRole (preferred). See [Member Reference](#member-reference-creation). |
| `act/effectiveTime` | `participant.period` | Convert IVL_TS to Period (member's participation period). |
| N/A | `participant.onBehalfOf` | Reference to Organization created from representedOrganization. Only populate if member is Practitioner reference (not PractitionerRole). |

---

### Function Code Mapping

Map `performer/functionCode` to `participant.role`:

**Code System Mappings:**

| C-CDA codeSystem (OID) | FHIR system (URI) |
|------------------------|-------------------|
| `2.16.840.1.113883.5.88` | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` |
| `2.16.840.1.113883.6.96` | `http://snomed.info/sct` |
| `2.16.840.1.113762.1.4.1099.30` | (ValueSet, not a code system - see note below) |

**Important Note on Value Set vs. Code System:**
- `2.16.840.1.113762.1.4.1099.30` is a **value set** (Care Team Member Function), not a code system
- When encountering this OID in C-CDA `@codeSystem`, the actual code may come from v3-RoleCode or SNOMED CT
- Map based on the code itself rather than the value set OID:
  - If code matches v3-RoleCode pattern (e.g., PCP, ADMPHYS) → use v3-RoleCode system
  - If code is numeric (e.g., 17561000, 224535009) → use SNOMED CT system
  - Full value set expansion requires VSAC/UMLS access

**Common Role Codes:**

| Code | System | Display |
|------|--------|---------|
| `PCP` | v3-RoleCode | Primary care physician |
| `ADMPHYS` | v3-RoleCode | Admitting physician |
| `ATTPHYS` | v3-RoleCode | Attending physician |
| `17561000` | SNOMED CT | General practitioner |
| `224535009` | SNOMED CT | Registered nurse |
| `224930009` | SNOMED CT | Social worker |

**Multiple Roles:** If a member has multiple roles, create single participant with multiple role codings.

---

### Member Reference Creation

**Recommended Approach:** Create **PractitionerRole** resource (provides location, contact, specialty)

#### Step 1: Create Practitioner Resource

From `assignedEntity/assignedPerson`:

```json
{
  "resourceType": "Practitioner",
  "id": "practitioner-npi-1234567890",
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "1234567890"
  }],
  "name": [{
    "use": "official",
    "prefix": ["Dr."],
    "given": ["John"],
    "family": "Smith",
    "suffix": ["MD"]
  }]
}
```

#### Step 2: Create PractitionerRole Resource

From `assignedEntity`:

```json
{
  "resourceType": "PractitionerRole",
  "id": "practitionerrole-npi-1234567890",
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "1234567890"
  }],
  "practitioner": {
    "reference": "Practitioner/practitioner-npi-1234567890"
  },
  "organization": {
    "reference": "Organization/org-123"
  },
  "code": [{
    "coding": [{
      "system": "http://nucc.org/provider-taxonomy",
      "code": "207Q00000X",
      "display": "Family Medicine Physician"
    }]
  }],
  "location": [{
    "reference": "Location/location-org-123"
  }],
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-5100",
    "use": "work"
  }]
}
```

#### Step 3: Create Organization Resource

From `representedOrganization`:

```json
{
  "resourceType": "Organization",
  "id": "org-123",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5",
    "value": "org-123"
  }],
  "name": "Community Health Clinic"
}
```

#### Step 4: Create Location Resource (Optional)

From `assignedEntity/addr`:

```json
{
  "resourceType": "Location",
  "id": "location-org-123",
  "name": "Community Health Clinic",
  "address": {
    "use": "work",
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  },
  "managingOrganization": {
    "reference": "Organization/org-123"
  }
}
```

#### Step 5: Reference in CareTeam

```json
{
  "participant": [{
    "role": [{...}],
    "member": {
      "reference": "PractitionerRole/practitionerrole-npi-1234567890",
      "display": "Dr. John Smith"
    }
  }]
}
```

**Alternative:** Reference Practitioner directly if PractitionerRole not needed, but this loses location/contact context.

---

### Non-Clinical Members

For non-clinical team members (family, caregivers), handle differently:

**C-CDA:**
```xml
<performer>
  <functionCode code="133932002" codeSystem="2.16.840.1.113883.6.96"
               displayName="Caregiver"/>
  <assignedEntity>
    <id root="patient-system" extension="related-person-001"/>
    <assignedPerson>
      <name><given>Mary</given><family>Smith</family></name>
    </assignedPerson>
  </assignedEntity>
</performer>
```

**FHIR:** Create RelatedPerson resource

```json
{
  "resourceType": "RelatedPerson",
  "id": "relatedperson-001",
  "patient": {
    "reference": "Patient/patient-123"
  },
  "relationship": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "133932002",
      "display": "Caregiver"
    }]
  }],
  "name": [{
    "given": ["Mary"],
    "family": "Smith"
  }]
}
```

**CareTeam Participant:**
```json
{
  "participant": [{
    "role": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "133932002",
        "display": "Caregiver"
      }]
    }],
    "member": {
      "reference": "RelatedPerson/relatedperson-001",
      "display": "Mary Smith"
    }
  }]
}
```

**Detection Logic:**
- If `assignedEntity/assignedPerson` present but lacks professional codes → RelatedPerson
- If functionCode suggests non-clinical role (caregiver, family member) → RelatedPerson
- If `assignedEntity/id/@root` references patient system → RelatedPerson

---

### Care Team Lead Handling

The organizer's `participant[@typeCode='PPRF']` identifies the care team lead.

**C-CDA:**
```xml
<organizer>
  <!-- ... -->
  <participant typeCode="PPRF">
    <participantRole>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    </participantRole>
  </participant>

  <component>
    <act>
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <!-- This is the lead -->
        </assignedEntity>
      </performer>
    </act>
  </component>
</organizer>
```

**FHIR Handling:**
- Match lead's ID to Care Team Member Act performer ID
- This member should be listed **first** in `CareTeam.participant` array
- Optionally add role coding for "team lead" or "primary performer"

**No Direct FHIR Element:** FHIR R4 CareTeam lacks explicit "lead" element; use ordering and role codes to indicate.

**Note on Optionality:** The lead participant is **optional** in C-CDA (SHOULD, not SHALL). If absent, list members in document order without special designation.

---

### Location Participant Handling

C-CDA Care Team Organizer supports location participants (`participant[@typeCode='LOC']`), but FHIR R4 CareTeam **does not have a location element**.

**C-CDA:**
```xml
<participant typeCode="LOC">
  <participantRole>
    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
    <addr>
      <streetAddressLine>1001 Village Avenue</streetAddressLine>
      <city>Portland</city>
      <state>OR</state>
      <postalCode>99123</postalCode>
    </addr>
    <telecom use="WP" value="tel:+1(555)555-5000"/>
    <playingEntity classCode="PLC">
      <name>Community Health and Hospitals</name>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR Handling Options:**

1. **Recommended:** Create separate Location resource
   - Use for PractitionerRole.location references
   - Store in bundle for general use
   - No direct CareTeam reference (not supported in R4)

2. **Alternative:** Populate CareTeam.managingOrganization
   - If location represents the organization managing the team
   - Create Organization resource from location data

3. **Not Recommended:** Ignore location data
   - Loses valuable location context
   - Violates completeness principle

**Implementation Note:** Location information is preserved through PractitionerRole resources, which do support location references.

---

## Mapping Approach 2: Header serviceEvent/performer

### Resource Cardinality

**Input:** One serviceEvent with multiple performers (1 serviceEvent with N performers)

**Output:** One CareTeam resource aggregating all performers (N:1 mapping)

### Element Mappings

| C-CDA Element | FHIR Element | Transformation |
|---------------|--------------|----------------|
| `documentationOf/serviceEvent/effectiveTime` | `CareTeam.period` | Convert IVL_TS to Period (document coverage period). |
| `performer[@typeCode='PRF']` (each) | `CareTeam.participant` (each) | One participant per performer. See [Header Participant Mapping](#header-participant-mapping). |
| N/A (derive) | `CareTeam.identifier` | Generate identifier from document ID + "-careteam". |
| N/A (fixed) | `CareTeam.status` | Default to "active". |
| `recordTarget/patientRole` | `CareTeam.subject` | Reference to Patient. |
| N/A (derive) | `CareTeam.category` | Infer from document type (e.g., "encounter-focused" for Discharge Summary). |
| N/A (derive) | `CareTeam.name` | Generate: "{DocumentType} Care Team for {PatientName}". Example: "Discharge Summary Care Team for John Smith" |

---

### Header Participant Mapping

**C-CDA:**
```xml
<documentationOf>
  <serviceEvent classCode="PCPR">
    <effectiveTime>
      <low value="20240110"/>
      <high value="20240115"/>
    </effectiveTime>

    <performer typeCode="PRF">
      <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                   displayName="Primary Care Physician"/>
      <time><low value="20240110"/></time>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"/>
        <addr use="WP">
          <streetAddressLine>1001 Village Avenue</streetAddressLine>
          <city>Portland</city>
          <state>OR</state>
          <postalCode>99123</postalCode>
        </addr>
        <telecom use="WP" value="tel:+1(555)555-5100"/>
        <assignedPerson>
          <name><given>John</given><family>Smith</family></name>
        </assignedPerson>
        <representedOrganization>
          <name>Community Health Clinic</name>
        </representedOrganization>
      </assignedEntity>
    </performer>

    <!-- Additional performers -->
  </serviceEvent>
</documentationOf>
```

**FHIR:**
```json
{
  "resourceType": "CareTeam",
  "id": "careteam-document-12345",
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5",
    "value": "document-12345-careteam"
  }],
  "status": "active",
  "category": [{
    "coding": [{
      "system": "http://loinc.org",
      "code": "LA28866-4",
      "display": "Encounter-focused care team"
    }]
  }],
  "name": "Discharge Summary Care Team for John Doe",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "period": {
    "start": "2024-01-10",
    "end": "2024-01-15"
  },
  "participant": [{
    "role": [{
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
        "code": "PCP",
        "display": "Primary Care Physician"
      }]
    }],
    "member": {
      "reference": "PractitionerRole/practitionerrole-npi-1234567890"
    },
    "period": {
      "start": "2024-01-10"
    }
  }]
}
```

#### Participant Element Mappings

| C-CDA Element | FHIR Element | Transformation |
|---------------|--------------|----------------|
| `performer/functionCode` | `participant.role` | Map to CodeableConcept (same as structured approach). |
| `performer/assignedEntity` | `participant.member` | Create Practitioner + PractitionerRole (same as structured approach). |
| `performer/time` | `participant.period` | Convert to Period (when this performer joined). |

---

### Category Inference by Document Type

When mapping header performers, infer category from document type:

| C-CDA Document Type | Template ID | Inferred category |
|---------------------|-------------|-------------------|
| Discharge Summary | `2.16.840.1.113883.10.20.22.1.8` | Encounter-focused (`LA28866-4`) |
| Consultation Note | `2.16.840.1.113883.10.20.22.1.4` | Event-focused (`LA28867-2`) |
| Referral Note | `2.16.840.1.113883.10.20.22.1.14` | Episode of care (`LA27977-0`) |
| CCD | `2.16.840.1.113883.10.20.22.1.2` | Longitudinal (`LA27976-2`) |

**Default:** If unknown, use "Encounter-focused".

---

## Combined Approach: Structured + Header

When both structured Care Teams Section **and** header serviceEvent/performers exist:

1. **Prefer Structured Section**: Create CareTeam resources from Care Team Organizers
2. **Cross-Reference Header**: Use header performers to validate/enrich structured teams
3. **Deduplication**: Match performers by identifier (NPI); avoid creating duplicate Practitioner/PractitionerRole resources
4. **Encounter Attribution**: If header performers exist but aren't in structured section, consider creating separate "encounter-focused" team

**Example Scenario:**
- Document has Care Teams Section with "Primary Care Team" (longitudinal)
- Document header lists "Attending Physician" and "Consulting Specialist" for this encounter
- **Output**:
  - CareTeam "Primary Care Team" (from structured section)
  - Optionally: CareTeam "Encounter Team" (from header) OR add encounter participants to primary team if appropriate

**Decision Logic:**
- If structured section exists, prioritize it
- If header performers are subset of structured members → skip header mapping
- If header has unique performers not in structured teams → create encounter-specific team

---

## Resource Deduplication

### Practitioner Deduplication

Multiple care teams may reference the same practitioner. Use NPI for deduplication:

**C-CDA:**
```xml
<!-- Care Team 1 -->
<assignedEntity>
  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  <!-- ... -->
</assignedEntity>

<!-- Care Team 2 -->
<assignedEntity>
  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  <!-- ... -->
</assignedEntity>
```

**FHIR:** Create **one** Practitioner/PractitionerRole resource with ID `practitionerrole-npi-1234567890`, referenced by both CareTeam resources.

**Deduplication Strategy:**
1. Maintain registry of created Practitioner/PractitionerRole resources keyed by NPI
2. When processing new performer:
   - Extract NPI from `id[@root='2.16.840.1.113883.4.6']/@extension`
   - Check if Practitioner/PractitionerRole already exists for this NPI
   - If exists: reference existing resource
   - If new: create new resource and register

### Organization Deduplication

Similarly, deduplicate organizations by identifier or name+address.

---

## Narrative Generation

Generate `CareTeam.text` from C-CDA section narrative:

**C-CDA:**
```xml
<section>
  <text>
    <table>
      <thead>
        <tr><th>Member</th><th>Role</th><th>Contact</th></tr>
      </thead>
      <tbody>
        <tr ID="ct1">
          <td>Dr. John Smith</td>
          <td>Primary Care Physician</td>
          <td>555-0100</td>
        </tr>
      </tbody>
    </table>
  </text>
</section>
```

**FHIR:**
```json
{
  "text": {
    "status": "generated",
    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><thead><tr><th>Member</th><th>Role</th><th>Contact</th></tr></thead><tbody><tr><td>Dr. John Smith</td><td>Primary Care Physician</td><td>555-0100</td></tr></tbody></table></div>"
  }
}
```

**Rules:**
- Extract table or paragraph content from section `<text>` element
- Wrap in `<div xmlns="http://www.w3.org/1999/xhtml">`
- Set `text.status = "generated"`
- If no section narrative, generate summary: "Care team for {PatientName} including {N} members"

---

## Complete Mapping Example

### Input: C-CDA Care Team Organizer

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.500" extension="2022-06-01"/>
  <code code="85847-2" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Care team information"/>
  <title>CARE TEAMS</title>
  <text>
    <table>
      <thead>
        <tr><th>Team</th><th>Member</th><th>Role</th><th>Contact</th></tr>
      </thead>
      <tbody>
        <tr ID="ct1"><td>Primary Care</td><td>Dr. John Smith</td><td>PCP</td><td>555-0100</td></tr>
        <tr ID="ct2"><td>Primary Care</td><td>Sarah Johnson, RN</td><td>Care Coordinator</td><td>555-0200</td></tr>
      </tbody>
    </table>
  </text>

  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>
      <id root="2.16.840.1.113883.19.5.99999.1" extension="primary-team-001"/>
      <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team">
        <originalText><reference value="#ct1"/></originalText>
      </code>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20230115"/>
      </effectiveTime>

      <!-- Team Lead -->
      <participant typeCode="PPRF">
        <participantRole>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </participantRole>
      </participant>

      <!-- Team Type -->
      <component>
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.2" extension="2019-07-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
          <value xsi:type="CD" code="LA27976-2" codeSystem="2.16.840.1.113883.6.1"
                 displayName="Longitudinal care-coordination focused care team"/>
        </observation>
      </component>

      <!-- Member 1: Physician (Team Lead) -->
      <component>
        <act classCode="PCPR" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
          <statusCode code="active"/>
          <effectiveTime><low value="20230115"/></effectiveTime>
          <performer>
            <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88" displayName="Primary Care Physician"/>
            <assignedEntity>
              <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
              <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101" displayName="Family Medicine"/>
              <addr use="WP">
                <streetAddressLine>1001 Village Avenue</streetAddressLine>
                <city>Portland</city>
                <state>OR</state>
                <postalCode>99123</postalCode>
              </addr>
              <telecom use="WP" value="tel:+1(555)555-0100"/>
              <assignedPerson>
                <name>
                  <prefix>Dr.</prefix>
                  <given>John</given>
                  <family>Smith</family>
                  <suffix>MD</suffix>
                </name>
              </assignedPerson>
              <representedOrganization>
                <id root="2.16.840.1.113883.19.5" extension="org-123"/>
                <name>Community Health Clinic</name>
              </representedOrganization>
            </assignedEntity>
          </performer>
        </act>
      </component>

      <!-- Member 2: Nurse Care Coordinator -->
      <component>
        <act classCode="PCPR" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
          <statusCode code="active"/>
          <effectiveTime><low value="20230201"/></effectiveTime>
          <performer>
            <functionCode code="224535009" codeSystem="2.16.840.1.113883.6.96" displayName="Registered nurse"/>
            <assignedEntity>
              <id root="2.16.840.1.113883.19.5.99999.1" extension="nurse-001"/>
              <code code="163W00000X" codeSystem="2.16.840.1.113883.6.101" displayName="Registered Nurse"/>
              <telecom use="WP" value="tel:+1(555)555-0200"/>
              <telecom use="WP" value="mailto:sjohnson@clinic.example.org"/>
              <assignedPerson>
                <name>
                  <given>Sarah</given>
                  <family>Johnson</family>
                  <suffix>RN</suffix>
                </name>
              </assignedPerson>
              <representedOrganization>
                <id root="2.16.840.1.113883.19.5" extension="org-123"/>
                <name>Community Health Clinic</name>
              </representedOrganization>
            </assignedEntity>
          </performer>
        </act>
      </component>

    </organizer>
  </entry>
</section>
```

### Output: FHIR Bundle with CareTeam and Supporting Resources

```json
{
  "resourceType": "Bundle",
  "type": "transaction",
  "entry": [
    {
      "fullUrl": "urn:uuid:careteam-primary-001",
      "resource": {
        "resourceType": "CareTeam",
        "id": "careteam-primary-001",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam"]
        },
        "identifier": [{
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "primary-team-001"
        }],
        "status": "active",
        "category": [{
          "coding": [{
            "system": "http://loinc.org",
            "code": "LA27976-2",
            "display": "Longitudinal care-coordination focused care team"
          }]
        }],
        "name": "John Doe Primary Care Team",
        "subject": {
          "reference": "Patient/patient-123",
          "display": "John Doe"
        },
        "period": {
          "start": "2023-01-15"
        },
        "participant": [
          {
            "role": [{
              "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "PCP",
                "display": "Primary Care Physician"
              }]
            }],
            "member": {
              "reference": "PractitionerRole/practitionerrole-npi-1234567890",
              "display": "Dr. John Smith"
            },
            "period": {
              "start": "2023-01-15"
            }
          },
          {
            "role": [{
              "coding": [{
                "system": "http://snomed.info/sct",
                "code": "224535009",
                "display": "Registered nurse"
              }]
            }],
            "member": {
              "reference": "PractitionerRole/practitionerrole-nurse-001",
              "display": "Sarah Johnson, RN"
            },
            "period": {
              "start": "2023-02-01"
            }
          }
        ],
        "managingOrganization": [{
          "reference": "Organization/org-123",
          "display": "Community Health Clinic"
        }],
        "text": {
          "status": "generated",
          "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><table><thead><tr><th>Team</th><th>Member</th><th>Role</th><th>Contact</th></tr></thead><tbody><tr><td>Primary Care</td><td>Dr. John Smith</td><td>PCP</td><td>555-0100</td></tr><tr><td>Primary Care</td><td>Sarah Johnson, RN</td><td>Care Coordinator</td><td>555-0200</td></tr></tbody></table></div>"
        }
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-npi-1234567890",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-npi-1234567890",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"]
        },
        "identifier": [{
          "system": "http://hl7.org/fhir/sid/us-npi",
          "value": "1234567890"
        }],
        "name": [{
          "use": "official",
          "prefix": ["Dr."],
          "given": ["John"],
          "family": "Smith",
          "suffix": ["MD"]
        }]
      }
    },
    {
      "fullUrl": "urn:uuid:practitionerrole-npi-1234567890",
      "resource": {
        "resourceType": "PractitionerRole",
        "id": "practitionerrole-npi-1234567890",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitionerrole"]
        },
        "identifier": [{
          "system": "http://hl7.org/fhir/sid/us-npi",
          "value": "1234567890"
        }],
        "practitioner": {
          "reference": "Practitioner/practitioner-npi-1234567890"
        },
        "organization": {
          "reference": "Organization/org-123"
        },
        "code": [{
          "coding": [{
            "system": "http://nucc.org/provider-taxonomy",
            "code": "207Q00000X",
            "display": "Family Medicine"
          }]
        }],
        "location": [{
          "reference": "Location/location-org-123"
        }],
        "telecom": [{
          "system": "phone",
          "value": "+1(555)555-0100",
          "use": "work"
        }]
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-nurse-001",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-nurse-001",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"]
        },
        "identifier": [{
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "nurse-001"
        }],
        "name": [{
          "given": ["Sarah"],
          "family": "Johnson",
          "suffix": ["RN"]
        }]
      }
    },
    {
      "fullUrl": "urn:uuid:practitionerrole-nurse-001",
      "resource": {
        "resourceType": "PractitionerRole",
        "id": "practitionerrole-nurse-001",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitionerrole"]
        },
        "identifier": [{
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "nurse-001"
        }],
        "practitioner": {
          "reference": "Practitioner/practitioner-nurse-001"
        },
        "organization": {
          "reference": "Organization/org-123"
        },
        "code": [{
          "coding": [{
            "system": "http://nucc.org/provider-taxonomy",
            "code": "163W00000X",
            "display": "Registered Nurse"
          }]
        }],
        "telecom": [
          {
            "system": "phone",
            "value": "+1(555)555-0200",
            "use": "work"
          },
          {
            "system": "email",
            "value": "sjohnson@clinic.example.org",
            "use": "work"
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:org-123",
      "resource": {
        "resourceType": "Organization",
        "id": "org-123",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-organization"]
        },
        "identifier": [{
          "system": "urn:oid:2.16.840.1.113883.19.5",
          "value": "org-123"
        }],
        "name": "Community Health Clinic"
      }
    },
    {
      "fullUrl": "urn:uuid:location-org-123",
      "resource": {
        "resourceType": "Location",
        "id": "location-org-123",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"]
        },
        "name": "Community Health Clinic",
        "address": {
          "use": "work",
          "line": ["1001 Village Avenue"],
          "city": "Portland",
          "state": "OR",
          "postalCode": "99123"
        },
        "managingOrganization": {
          "reference": "Organization/org-123"
        }
      }
    }
  ]
}
```

---

## Edge Cases and Special Handling

### 1. Missing Effective Time

**Scenario:** Care Team Organizer lacks `effectiveTime/low`

**Handling:**
- Use document `effectiveTime` as fallback for `period.start`
- If still missing, use current date
- Log warning about missing data

### 2. Multiple Care Team Types

**Scenario:** Organizer has multiple type observations

**C-CDA:**
```xml
<component>
  <observation>
    <value code="LA27976-2" displayName="Longitudinal care-coordination focused care team"/>
  </observation>
</component>
<component>
  <observation>
    <value code="LA28865-6" displayName="Condition-focused care team"/>
  </observation>
</component>
```

**FHIR:**
```json
{
  "category": [
    {
      "coding": [{
        "system": "http://loinc.org",
        "code": "LA27976-2",
        "display": "Longitudinal care-coordination focused care team"
      }]
    },
    {
      "coding": [{
        "system": "http://loinc.org",
        "code": "LA28865-6",
        "display": "Condition-focused care team"
      }]
    }
  ]
}
```

### 3. Inactive Team Members

**Scenario:** Member with `statusCode="completed"` and `effectiveTime/high`

**Handling:**
- Still include in CareTeam.participant
- Set `participant.period.end` from `effectiveTime/high`
- Participant is historical but valid

### 4. Team Without Members

**Scenario:** Organizer has no member act components

**Handling:**
- C-CDA requires at least one member; this violates specification
- If encountered, create CareTeam with empty participant array OR skip creation
- Log error: "Invalid Care Team Organizer: no members"

### 5. Lead Not Matching Any Member

**Scenario:** Lead participant ID doesn't match any member performer ID

**Handling:**
- Ignore lead designation (can't validate)
- Create participants in document order
- Log warning: "Care team lead ID does not match any member"

### 6. Member Without Function Code

**Scenario:** Performer lacks `functionCode`

**Handling:**
- Create participant with empty `role` array OR
- Use generic role: "healthcare provider" (SNOMED 223366009)
- Log warning about missing function code

### 7. Organizational Team Members

**Scenario:** Team member is organization, not person

**C-CDA:**
```xml
<performer>
  <functionCode code="224930009" displayName="Social worker"/>
  <assignedEntity>
    <id root="org-social-services" extension="001"/>
    <!-- No assignedPerson, only representedOrganization -->
    <representedOrganization>
      <name>County Social Services</name>
    </representedOrganization>
  </assignedEntity>
</performer>
```

**FHIR:**
```json
{
  "participant": [{
    "role": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "224930009",
        "display": "Social worker"
      }]
    }],
    "member": {
      "reference": "Organization/org-social-services",
      "display": "County Social Services"
    }
  }]
}
```

**Detection:** If `assignedEntity` lacks `assignedPerson` but has `representedOrganization` → reference Organization

---

## Validation Rules

### US Core CareTeam Conformance

- [ ] `CareTeam.status` present and valid (required)
- [ ] `CareTeam.subject` references Patient (required, 1..1)
- [ ] `CareTeam.participant` has at least one entry (required, 1..*)
- [ ] Each `participant.role` is present (required, 1..1)
- [ ] Each `participant.member` references valid resource type (required, 1..1)
- [ ] `meta.profile` includes US Core CareTeam profile URL
- [ ] If server, support patient+status search
- [ ] Member references use PractitionerRole when available (recommended)

### C-CDA Template Conformance

- [ ] Validate Care Team Organizer has template ID `2.16.840.1.113883.10.20.22.4.500`
- [ ] Validate organizer `@classCode="CLUSTER"` and `@moodCode="EVN"`
- [ ] Validate organizer has required elements: id, code, statusCode, effectiveTime
- [ ] Validate Care Team Member Act has template ID `2.16.840.1.113883.10.20.22.4.500.1`
- [ ] Validate member act has required performer with functionCode
- [ ] Validate at least one member per organizer

---

## Implementation Notes

### Priority Level

**Priority:** LOW (Not part of core C-CDA to FHIR requirements, but supports USCDI v4)

### Rationale for Low Priority

1. **Not a traditional C-CDA element**: Care Team Organizer is relatively new (2019-2022 extensions)
2. **Limited adoption**: Not widely used in legacy C-CDA documents
3. **Alternative representation**: serviceEvent/performer provides simpler alternative
4. **Participation already mapped**: Practitioner/PractitionerRole mapping covered in other specs
5. **USCDI v4 requirement**: Important for future but not blocking current conversions

### When to Implement

- **Phase 1** (High Priority): Patient, Condition, Observation, Medication, Immunization, Procedure, Encounter
- **Phase 2** (Medium Priority): AllergyIntolerance, Goal, CarePlan, MedicationDispense, Location
- **Phase 3** (Low Priority): **CareTeam**, DiagnosticReport, DocumentReference

### Recommended Implementation Order

1. Implement Practitioner/PractitionerRole/Organization mapping (dependency)
2. Implement header serviceEvent/performer → CareTeam (simpler, covers more documents)
3. Implement structured Care Team Organizer → CareTeam (comprehensive but less common)

### Testing Strategy

**Test Cases:**
1. Structured Care Team Organizer with 2 members
2. Header serviceEvent with 3 performers
3. Combined: both structured and header
4. Edge cases: missing effectiveTime, no function codes, organizational members
5. Deduplication: same practitioner in multiple teams
6. Multiple teams: primary care + diabetes specialty teams
7. Non-clinical members: family caregiver

---

## References

- [FHIR CareTeam Resource](http://hl7.org/fhir/R4/careteam.html)
- [US Core CareTeam Profile v8.0.1](http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-careteam.html)
- [C-CDA Care Team Organizer](https://cdasearch.hl7.org/examples/view/Guide%20Examples/Care%20Team%20Organizer%20(V2)_2.16.840.1.113883.10.20.22.4.500)
- [HL7 C-CDA Examples - Care Team](https://github.com/HL7/C-CDA-Examples/tree/master/Care%20Team)
- [Care Team Member Function Value Set](http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113762.1.4.1099.30)
- [LOINC 86744-0 - Care team](https://loinc.org/86744-0)
- [USCDI v4 - Care Team Members](https://www.healthit.gov/isa/uscdi-data-class/care-team-members)
- [C-CDA on FHIR Mapping Guidance](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html)
