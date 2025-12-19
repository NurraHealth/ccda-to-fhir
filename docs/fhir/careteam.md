# FHIR CareTeam Resource

**Profile:** [US Core CareTeam Profile v8.0.1](http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-careteam.html)

**Resource Type:** CareTeam

**Maturity Level:** 3 (Trial Use)

---

## Overview

The CareTeam resource represents the care team members associated with a patient to promote care coordination and interoperability. Unlike individual practitioner or organization references, CareTeam provides a structured way to group multiple care participants with their specific roles and responsibilities.

The US Core CareTeam Profile sets minimum expectations for identifying care team members, their roles, and the patient they serve.

---

## Purpose and Scope

CareTeam is used to:
- Identify the patient's primary care team members
- Document specialist consultants involved in care
- Track multidisciplinary team members (clinical and non-clinical)
- Support care coordination across organizations
- Represent care teams for specific conditions, episodes, or encounters

---

## Resource Structure

### Mandatory Elements (SHALL)

These elements must always be present:

| Element | Cardinality | Type | Description |
|---------|-------------|------|-------------|
| `subject` | 1..1 | Reference(US Core Patient) | The patient this care team serves |
| `participant` | 1..* | BackboneElement | Care team members (at least one required) |
| `participant.role` | 1..1 | CodeableConcept | Member's function within the care team |
| `participant.member` | 1..1 | Reference | The person or organization participating |

### Must Support Elements (SHOULD)

These elements must be supported if data is present:

| Element | Cardinality | Type | Description |
|---------|-------------|------|-------------|
| `status` | 0..1 | code | proposed \| active \| suspended \| inactive \| entered-in-error |
| `subject` | 1..1 | Reference(US Core Patient) | Patient reference |
| `participant` | 1..* | BackboneElement | Team members |
| `participant.role` | 1..1 | CodeableConcept | Member's role/function |
| `participant.member` | 1..1 | Reference | Practitioner, PractitionerRole, RelatedPerson, Organization, Patient, or CareTeam |

### Optional Elements (MAY)

| Element | Cardinality | Type | Description |
|---------|-------------|------|-------------|
| `identifier` | 0..* | Identifier | External identifiers for this care team |
| `category` | 0..* | CodeableConcept | Type of team (e.g., encounter, episode, condition-specific) |
| `name` | 0..1 | string | Human-readable name for the care team |
| `encounter` | 0..1 | Reference(Encounter) | Encounter creating the care team |
| `period` | 0..1 | Period | When the team is active |
| `participant.onBehalfOf` | 0..1 | Reference(Organization) | Organization the practitioner represents |
| `participant.period` | 0..1 | Period | When the member is active in this team |
| `reasonCode` | 0..* | CodeableConcept | Why the team exists |
| `reasonReference` | 0..* | Reference(Condition) | Condition(s) the team addresses |
| `managingOrganization` | 0..* | Reference(Organization) | Organization responsible for the team |
| `telecom` | 0..* | ContactPoint | Contact details for the team |
| `note` | 0..* | Annotation | Comments about the team |

---

## Participant Member References

The `participant.member` element can reference multiple profile types. US Core specifies different requirements for servers vs. clients:

### Server Requirements (SHALL support at least one)

Servers **must support** at least one of the following for practitioner references:
- **US Core Practitioner Profile** - Basic practitioner demographics
- **US Core PractitionerRole Profile** - Practitioner + location + contact info (RECOMMENDED)

### Client Requirements (SHALL support all)

Clients **must support** all three core participant types:
- **US Core Practitioner Profile**
- **US Core PractitionerRole Profile**
- **US Core RelatedPerson Profile**

### Additional Allowed References

The member element may also reference:
- **US Core Organization Profile** - For organizational team members
- **US Core Patient Profile** - When the patient is a care team participant
- **US Core CareTeam Profile** - For nested care teams

### Implementation Recommendation

The US Core IG recommends using **PractitionerRole** instead of Practitioner when possible because:
- Provides location information (where the practitioner practices)
- Includes contact information (phone, email)
- Links to the organization the practitioner represents
- Supplies specialty and role information in context

---

## Value Sets and Terminology

### CareTeam.status (Required Binding)

**ValueSet:** [CareTeamStatus](http://hl7.org/fhir/ValueSet/care-team-status) (FHIR Standard v4.0.1)

| Code | Display | Definition |
|------|---------|------------|
| `proposed` | Proposed | The care team has been drafted and proposed but not yet participating in coordination and delivery of care |
| `active` | Active | The care team is currently participating in coordination and delivery of care |
| `suspended` | Suspended | The care team is temporarily on hold or suspended |
| `inactive` | Inactive | The care team was, but is no longer, participating in coordination and delivery of care |
| `entered-in-error` | Entered in Error | The care team should have never existed |

### CareTeam.participant.role (Extensible Binding)

**ValueSet:** [Care Team Member Function](http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113762.1.4.1099.30) (VSAC v0.24, version 20240605)

**OID:** 2.16.840.1.113762.1.4.1099.30

**Binding Strength:** Extensible (codes SHOULD come from this value set but others are allowed if necessary)

This value set includes roles such as:
- Primary care physician (PCP)
- Consulting physician
- Care coordinator
- Case manager
- Caregiver
- Emergency contact
- Team coordinator
- Social worker
- Physical therapist
- Occupational therapist
- Nurse
- Pharmacist
- Family member
- Transportation provider
- Clergy/spiritual advisor

**Note:** This is the same value set used in C-CDA for care team member functions, promoting alignment between standards.

---

## Formal Invariants (Constraints)

### ctm-1 (Error Level)

**Rule:** "Participant onBehalfOf can only be populated when member is a Practitioner"

**Expression:** `onBehalfOf.exists() implies (member.resolve().iif(empty(), true, ofType(Practitioner).exists()))`

**Human:** The `participant.onBehalfOf` element should only be present when `participant.member` references a Practitioner resource.

### Standard FHIR Constraints

- **dom-2:** Resources cannot contain nested contained resources
- **dom-3:** Contained resources must be referenced from elsewhere in the resource
- **dom-4:** Contained resources cannot have versionId or lastUpdated metadata
- **dom-5:** Contained resources cannot have security labels
- **dom-6:** Resources SHOULD have narrative text for human readability
- **ele-1:** All elements must have either a value or children
- **ext-1:** Extensions cannot have both a value[x] and nested extensions

---

## Search Parameters

### Mandatory Search Combinations

#### Patient + Status
Servers **SHALL** support searching by patient and status:

```http
GET [base]/CareTeam?patient=[id]&status=active
```

**Parameters:**
- `patient` - Reference to patient (type: reference)
- `status` - Care team status (type: token)

**Example:**
```http
GET [base]/CareTeam?patient=1137192&status=active
```

### Recommended Search Combinations (SHOULD)

#### Patient + Role
Servers **SHOULD** support searching by patient and participant role:

```http
GET [base]/CareTeam?patient=[id]&role=[code]
```

**Example (Primary Care Physician):**
```http
GET [base]/CareTeam?patient=1137192&role=http://snomed.info/sct|17561000
```

### Include Parameters (Optional)

Servers **MAY** support including referenced resources:

```http
GET [base]/CareTeam?patient=1137192&status=active
  &_include=CareTeam:participant:PractitionerRole
  &_include=CareTeam:participant:Practitioner
  &_include=CareTeam:participant:RelatedPerson
  &_include=CareTeam:participant:Patient
```

---

## SMART on FHIR Scopes

Servers providing CareTeam data **SHALL** support:

```
patient/CareTeam.rs
user/CareTeam.rs
system/CareTeam.rs
```

Where `.rs` indicates resource-level scope for read and search operations.

---

## Usage Patterns

### Pattern 1: Primary Care Team

A patient's ongoing primary care team with stable membership:

```json
{
  "resourceType": "CareTeam",
  "id": "example-primary-care",
  "status": "active",
  "category": [{
    "coding": [{
      "system": "http://loinc.org",
      "code": "LA27976-2",
      "display": "Longitudinal care-coordination focused care team"
    }]
  }],
  "name": "John Smith Primary Care Team",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "period": {
    "start": "2023-01-15"
  },
  "participant": [
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "17561000",
          "display": "General practitioner"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/dr-jones-pcp"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "224571005",
          "display": "Nurse practitioner"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/np-smith"
      }
    }
  ],
  "managingOrganization": [{
    "reference": "Organization/primary-care-clinic"
  }]
}
```

### Pattern 2: Condition-Specific Care Team

A multidisciplinary team for diabetes management:

```json
{
  "resourceType": "CareTeam",
  "id": "example-diabetes-team",
  "status": "active",
  "category": [{
    "coding": [{
      "system": "http://loinc.org",
      "code": "LA28865-6",
      "display": "Condition-focused care team"
    }]
  }],
  "name": "Diabetes Management Team",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "period": {
    "start": "2024-03-01"
  },
  "reasonReference": [{
    "reference": "Condition/diabetes-type2"
  }],
  "participant": [
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "17561000",
          "display": "General practitioner"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/dr-jones-pcp"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "159141008",
          "display": "Dietitian"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/dietitian-brown"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "46255001",
          "display": "Pharmacist"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/pharmacist-wilson"
      }
    }
  ]
}
```

### Pattern 3: Encounter-Specific Team

A surgical care team for a specific procedure:

```json
{
  "resourceType": "CareTeam",
  "id": "example-surgical-team",
  "status": "inactive",
  "category": [{
    "coding": [{
      "system": "http://loinc.org",
      "code": "LA28866-4",
      "display": "Encounter-focused care team"
    }]
  }],
  "name": "Appendectomy Surgical Team",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "encounter": {
    "reference": "Encounter/surgery-2024-01-15"
  },
  "period": {
    "start": "2024-01-15T08:00:00-05:00",
    "end": "2024-01-15T12:00:00-05:00"
  },
  "participant": [
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "304292004",
          "display": "Surgeon"
        }]
      }],
      "member": {
        "reference": "Practitioner/surgeon-davis"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "88189002",
          "display": "Anesthesiologist"
        }]
      }],
      "member": {
        "reference": "Practitioner/anesthesiologist-lee"
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
        "reference": "Practitioner/nurse-garcia"
      }
    }
  ]
}
```

### Pattern 4: Care Team with Non-Clinical Members

Including family caregivers and support services:

```json
{
  "resourceType": "CareTeam",
  "id": "example-comprehensive-team",
  "status": "active",
  "name": "Comprehensive Care Support Team",
  "subject": {
    "reference": "Patient/patient-123"
  },
  "participant": [
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "17561000",
          "display": "General practitioner"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/dr-jones-pcp"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "133932002",
          "display": "Caregiver"
        }]
      }],
      "member": {
        "reference": "RelatedPerson/spouse-mary-smith"
      }
    },
    {
      "role": [{
        "coding": [{
          "system": "http://snomed.info/sct",
          "code": "224930009",
          "display": "Social worker"
        }]
      }],
      "member": {
        "reference": "PractitionerRole/social-worker-johnson"
      }
    },
    {
      "role": [{
        "text": "Transportation provider"
      }],
      "member": {
        "reference": "Organization/medical-transport-services"
      }
    }
  ]
}
```

---

## Implementation Considerations

### Multiple Care Teams per Patient

A single patient may have multiple active care teams simultaneously:
- **Longitudinal primary care team** - Ongoing general health management
- **Condition-specific teams** - Diabetes team, cardiac rehab team, etc.
- **Episode-specific teams** - Hospital admission team, surgical team
- **Social support team** - Case manager, social worker, home health

Each team should have distinct identifiers and appropriate `category` codes.

### Care Team Lifecycle

1. **Proposed** - Team has been suggested but not yet active
2. **Active** - Currently coordinating care
3. **Suspended** - Temporarily on hold (e.g., patient travel)
4. **Inactive** - No longer active but historically accurate
5. **Entered-in-error** - Should never have existed

### Accessing Practitioner Details

When using **PractitionerRole** references:

```http
GET [base]/CareTeam?patient=123&_include=CareTeam:participant:PractitionerRole
```

Then follow `PractitionerRole.practitioner` references to get names/identifiers:

```http
GET [base]/Practitioner/[id]
```

When using **Practitioner** references directly, location/contact info must be obtained through other means (Organization references, endpoints, etc.).

### Care Team vs. Individual Practitioners

Use CareTeam when:
- Multiple people coordinate care for the patient
- Roles and responsibilities need explicit documentation
- Care coordination across organizations is required
- A formal team structure exists

Use individual Practitioner/PractitionerRole references when:
- Documenting a single provider relationship
- The concept of a coordinated "team" is not applicable
- Simple attribution is sufficient

### Participant Period

Use `participant.period` to track when individual members joined/left the team:

```json
{
  "participant": [{
    "role": [{
      "coding": [{
        "system": "http://snomed.info/sct",
        "code": "17561000",
        "display": "General practitioner"
      }]
    }],
    "member": {
      "reference": "PractitionerRole/dr-jones"
    },
    "period": {
      "start": "2023-01-15",
      "end": "2024-06-30"
    }
  }]
}
```

This allows historical tracking of team composition changes.

---

## Conformance Requirements Summary

### US Core v8.0.1 Conformance

| Requirement | Details |
|-------------|---------|
| **Profile URL** | http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam |
| **FHIR Version** | 4.0.1 |
| **Maturity** | FMM 3 (Trial Use) |
| **Mandatory Elements** | 4 (status, subject, participant, participant.role, participant.member) |
| **Must Support Elements** | 5 |
| **Required Searches** | patient+status |
| **Recommended Searches** | patient+role |
| **SMART Scopes** | patient/CareTeam.rs, user/CareTeam.rs, system/CareTeam.rs |

### USCDI Requirement

Care Team Members are part of **USCDI v4** as a required data class for interoperability.

---

## References

- [US Core CareTeam Profile v8.0.1](http://hl7.org/fhir/us/core/STU8.0.1/StructureDefinition-us-core-careteam.html)
- [FHIR CareTeam Resource](http://hl7.org/fhir/R4/careteam.html)
- [Care Team Member Function Value Set](http://cts.nlm.nih.gov/fhir/ValueSet/2.16.840.1.113762.1.4.1099.30)
- [USCDI v4 - Care Team Members](https://www.healthit.gov/isa/uscdi-data-class/care-team-members)
