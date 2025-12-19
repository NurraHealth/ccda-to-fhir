# FHIR ServiceRequest Resource

## Overview

**Profile**: [US Core ServiceRequest Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest)

**Base Resource**: ServiceRequest (FHIR R4)

**Maturity Level**: 3 (Trial-use, STU8)

**Purpose**: Establishes baseline expectations for documenting service requests within US healthcare systems. ServiceRequest represents orders, proposals, or plans for procedures, diagnostic tests, therapeutic services, and referrals.

## Resource Type

ServiceRequest is a **request** resource in the FHIR workflow framework, representing "a record of a request for a procedure or diagnostic or other service to be planned, proposed, or performed."

## Key Characteristics

- Represents **future-oriented** clinical activities (proposals, plans, orders)
- Distinguished from Procedure resource (which represents completed or in-progress activities)
- Supports both orders (initiated by clinician) and proposals (suggestions or recommendations)
- Used for procedures, diagnostic tests, imaging studies, lab orders, referrals, and therapeutic services

## Mandatory Elements (Cardinality 1..1)

These elements MUST always be present:

| Element | Type | Description |
|---------|------|-------------|
| **status** | code | Request lifecycle state (draft, active, on-hold, revoked, completed, entered-in-error, unknown) |
| **intent** | code | Proposal, plan, directive, order, original-order, reflex-order, filler-order, instance-order, option |
| **code** | CodeableConcept | Service or procedure being requested |
| **subject** | Reference(Patient) | Individual or entity receiving the service |

## Must Support Elements (Cardinality 0..1 or 0..*)

Systems SHALL be capable of populating and receiving these elements when data exists:

| Element | Cardinality | Type | Description |
|---------|-------------|------|-------------|
| **category** | 0..* | CodeableConcept | Classification of service (lab, imaging, procedure, etc.) |
| **code.text** | 0..1 | string | Plain-language service description (Additional USCDI) |
| **encounter** | 0..1 | Reference(Encounter) | Associated clinical visit |
| **occurrence[x]** | 0..1 | dateTime \| Period \| Timing | Scheduled timing for service |
| **authoredOn** | 0..1 | dateTime | When request was created |
| **requester** | 0..1 | Reference | Individual/organization initiating request |
| **reasonCode** | 0..* | CodeableConcept | Clinical justification (Additional USCDI) |
| **reasonReference** | 0..* | Reference | Supporting clinical evidence (Additional USCDI) |

### Additional USCDI Requirements

The profile specifies that **reasonCode** and **reasonReference** are marked as Additional USCDI Requirements:
- Servers need only support **one** of these elements
- Clients SHALL support **both** elements

## Element Definitions

### status (Required)

Request lifecycle state from RequestStatus value set (required binding):

| Code | Display | Definition |
|------|---------|------------|
| draft | Draft | Request has been created but not yet complete |
| active | Active | Request is ready to be acted upon |
| on-hold | On Hold | Request is temporarily suspended |
| revoked | Revoked | Request has been terminated prior to completion |
| completed | Completed | Activity described by request has been completed |
| entered-in-error | Entered in Error | Request was created in error and should be ignored |
| unknown | Unknown | Authoring system does not know status |

### intent (Required)

Indicates the level of authority/intentionality from RequestIntent value set (required binding):

| Code | Display | Use Case |
|------|---------|----------|
| proposal | Proposal | Suggestion made by someone/something |
| plan | Plan | Intention to ensure something occurs without authorization |
| directive | Directive | Request represents instruction from authority |
| order | Order | Request represents demand for action |
| original-order | Original Order | Initial request authorizing action |
| reflex-order | Reflex Order | Automatically generated supplemental order |
| filler-order | Filler Order | Order created during fulfillment process |
| instance-order | Instance Order | Instantiation of protocol or definition |
| option | Option | Request represents component/option for consideration |

**C-CDA Mapping Context**:
- C-CDA Planned Procedure (moodCode=RQO, INT, PRP) typically maps to intent=order or intent=plan
- C-CDA Intervention Act with moodCode=INT maps to intent=plan

### code (Required)

Procedure or service being requested. Extensible binding to **US Core Procedure Codes** value set.

**Value Set Components**:
- **LOINC** - Laboratory and diagnostic test codes (preferred for lab orders)
- **SNOMED CT** - Clinical procedures and interventions
- **CPT** - Current Procedural Terminology (billing/procedure codes)
- **HCPCS** - Healthcare Common Procedure Coding System
- **ICD-10-PCS** - Procedural codes

**code.text** (Additional USCDI): Plain-language description of the service

### category (Must Support)

Classification of the service type. Required binding to **US Core ServiceRequest Category Codes**.

**Common Categories**:

| Code | System | Display | Use |
|------|--------|---------|-----|
| 108252007 | SNOMED CT | Laboratory procedure | Lab test orders |
| 363679005 | SNOMED CT | Imaging | Radiology/imaging orders |
| 409063005 | SNOMED CT | Counselling | Counseling services |
| 409073007 | SNOMED CT | Education | Patient education |
| 387713003 | SNOMED CT | Surgical procedure | Surgical orders |
| 103693007 | SNOMED CT | Diagnostic procedure | Diagnostic services |

**SDOH Categories**: For social determinants of health screening and referrals, use codes from the SDOH Category value set.

### subject (Required)

Reference to the patient or group for whom the service is being requested.

**US Core Profile**: SHALL reference **US Core Patient Profile**

### encounter (Must Support)

Reference to the clinical encounter during which the request was created.

**US Core Profile**: SHALL reference **US Core Encounter Profile**

### occurrence[x] (Must Support)

When the service should occur. Choice of three datatypes:

| Type | Use | Example |
|------|-----|---------|
| **occurrenceDateTime** | Single point in time | "2024-03-15T14:30:00Z" |
| **occurrencePeriod** | Time range | {"start": "2024-03-15", "end": "2024-03-22"} |
| **occurrenceTiming** | Recurring schedule | {"repeat": {"frequency": 1, "period": 1, "periodUnit": "wk"}} |

**C-CDA Mapping**: Maps from Planned Procedure `effectiveTime`

### authoredOn (Must Support)

Date and time when the request was created/authored.

**C-CDA Mapping**: Maps from `author/time`

### requester (Must Support)

Individual, organization, or device that initiated the request.

**Allowed Reference Types**:
- **Practitioner** (US Core Practitioner Profile)
- **PractitionerRole** (US Core PractitionerRole Profile)
- **Organization** (US Core Organization Profile)
- **Patient** (US Core Patient Profile) - for patient-initiated requests
- **RelatedPerson** - for family/caregiver requests
- **Device** - for automated order generation

**C-CDA Mapping**: Maps from `author/assignedAuthor`

### reasonCode (Must Support, Additional USCDI)

Clinical indication or justification for the service. Extensible binding to **US Core Condition Codes**.

**Value Set**: SNOMED CT clinical findings and diagnoses

**C-CDA Mapping**: Maps from entryRelationship[@typeCode='RSON']/observation (Indication)

### reasonReference (Must Support, Additional USCDI)

Supporting clinical evidence for the request.

**Allowed Reference Types**:
- **Condition** (US Core Condition Profile)
- **Observation** (US Core Observation Profiles)
- **DiagnosticReport** (US Core DiagnosticReport Profiles)
- **DocumentReference** (US Core DocumentReference Profile)

**C-CDA Mapping**: Maps from entryRelationship[@typeCode='RSON'] referencing observations or conditions

### performer (Optional)

Expected performer of the requested service.

**Allowed Reference Types**: Practitioner, PractitionerRole, Organization, Patient, Device, RelatedPerson, HealthcareService, CareTeam

**C-CDA Mapping**: Maps from `performer/assignedEntity`

### performerType (Optional)

Desired type of performer (role) for the service.

**Value Set**: Participant Role (extensible)

### priority (Optional)

Indicates urgency of the request.

**Codes**: routine | urgent | asap | stat

### orderDetail (Optional)

Additional details about how the service should be performed.

**Constraint**: Can only appear if `code` is present

### bodySite (Optional)

Anatomical location where service should be performed.

**Value Set**: Body Site (example binding)

**C-CDA Mapping**: Maps from `targetSiteCode`

### note (Optional)

Comments or additional information about the request.

**C-CDA Mapping**: Maps from entryRelationship[typeCode='SUBJ']/act (Instructions)

### patientInstruction (Optional)

Instructions for the patient regarding the service.

### supportingInfo (Optional)

Additional clinical information supporting the request.

### specimen (Optional)

Specimen to be tested (for lab orders).

### insurance (Optional)

Insurance plans covering the requested service.

**C-CDA Mapping**: Maps from entryRelationship[typeCode='COMP']/act[templateId='Planned Coverage']

## Search Parameters

US Core ServiceRequest Profile requires support for the following search parameters:

### Required Searches

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| **patient** | reference | Search by subject | `GET [base]/ServiceRequest?patient=123` |
| **_id** | token | Search by resource ID | `GET [base]/ServiceRequest?_id=sr-456` |

### Required Combination Searches

| Combination | Description | Example |
|-------------|-------------|---------|
| **patient + category** | Filter by service type | `GET [base]/ServiceRequest?patient=123&category=363679005` |
| **patient + code** | Filter by procedure code | `GET [base]/ServiceRequest?patient=123&code=24627-2` |
| **patient + category + authored** | Date range filtering | `GET [base]/ServiceRequest?patient=123&category=108252007&authored=ge2024-01-01&authored=le2024-12-31` |

### Optional Searches

| Parameter | Type | Description |
|-----------|------|-------------|
| **patient + status** | reference + token | Filter by request state |
| **patient + code + authored** | reference + token + date | Combined code and date search |

**Search Modifiers**:
- **code** supports `:text` modifier for text searching
- **authored** supports comparators: `gt`, `lt`, `ge`, `le`, `eq`

## Constraints

### Profile Constraints

| ID | Severity | Description |
|----|----------|-------------|
| prr-1 | error | orderDetail can only appear if code is present |
| dom-2 | error | No nested contained resources within contained resources |
| dom-6 | error | Resources must have narrative or structured content |

### Invariants

**us-core-1**: ServiceRequest.code or ServiceRequest.code.coding or ServiceRequest.code.text SHALL be present

## Related Resources

### Request-Response Pattern

ServiceRequest participates in the request-response workflow:

- **ServiceRequest** (request) → **Procedure** (event/response)
- **Procedure.basedOn** references the originating ServiceRequest

### Related Profiles

| Profile | Relationship |
|---------|--------------|
| **US Core Procedure** | Records completion of ServiceRequest |
| **US Core DiagnosticReport** | Results from diagnostic ServiceRequest |
| **US Core Observation** | Results from lab/test ServiceRequest |
| **US Core Patient** | Subject of request |
| **US Core Encounter** | Context of request creation |
| **US Core Practitioner** | Requester or performer |
| **US Core Condition** | Clinical justification (reasonReference) |

## Examples from US Core

### Laboratory Order Example

```json
{
  "resourceType": "ServiceRequest",
  "id": "cbc",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "108252007",
      "display": "Laboratory procedure"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "24360-0",
      "display": "Hemoglobin and Hematocrit panel - Blood"
    }],
    "text": "Complete blood count (hemogram) panel - Blood"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Amy V. Baxter"
  },
  "encounter": {
    "reference": "Encounter/example-1"
  },
  "occurrenceDateTime": "2024-01-15",
  "authoredOn": "2024-01-15T09:15:00Z",
  "requester": {
    "reference": "Practitioner/practitioner-1",
    "display": "Dr. Sarah Smith"
  }
}
```

### Imaging Order Example

```json
{
  "resourceType": "ServiceRequest",
  "id": "chest-xray",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "363679005",
      "display": "Imaging"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "36643-5",
      "display": "XR Chest 2 Views"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "49727002",
      "display": "Cough"
    }]
  }],
  "authoredOn": "2024-01-15T10:30:00Z"
}
```

### Referral Example

```json
{
  "resourceType": "ServiceRequest",
  "id": "foodpantry-referral",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-category",
      "code": "sdoh",
      "display": "SDOH"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "467771000124109",
      "display": "Assistance with application for food program"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "authoredOn": "2024-02-01T11:00:00Z",
  "requester": {
    "reference": "Practitioner/practitioner-1"
  }
}
```

### Planned Procedure Example

```json
{
  "resourceType": "ServiceRequest",
  "id": "colonoscopy-planned",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "status": "active",
  "intent": "plan",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "387713003",
      "display": "Surgical procedure"
    }]
  }],
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73761001",
      "display": "Colonoscopy"
    }]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "occurrenceDateTime": "2024-06-13",
  "authoredOn": "2024-01-15T14:00:00Z",
  "requester": {
    "reference": "Practitioner/practitioner-1"
  },
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "428165003",
      "display": "Screening for colon cancer"
    }]
  }],
  "note": [{
    "text": "Patient to follow bowel prep instructions 24 hours before procedure"
  }]
}
```

## Implementation Considerations

### Distinguishing ServiceRequest from Procedure

| Aspect | ServiceRequest | Procedure |
|--------|----------------|-----------|
| **Timing** | Future-oriented | Completed or in-progress |
| **Status** | draft, active, on-hold, etc. | preparation, in-progress, completed, etc. |
| **Intent** | proposal, plan, order | N/A (event resource) |
| **Use Case** | "Should be done" | "Was done" or "Is being done" |

### C-CDA moodCode Mapping

C-CDA uses `moodCode` to distinguish planned vs completed activities:

| C-CDA moodCode | FHIR Resource | Notes |
|----------------|---------------|-------|
| **INT** (Intent) | ServiceRequest (intent=plan) | Planned intervention |
| **RQO** (Request) | ServiceRequest (intent=order) | Ordered procedure |
| **PRP** (Proposal) | ServiceRequest (intent=proposal) | Proposed procedure |
| **EVN** (Event) | Procedure | Completed procedure |
| **GOL** (Goal) | Goal | Patient goal, not a service request |

### SDOH Screening and Referrals

For Social Determinants of Health (SDOH) screening and assessment services:
- Use **category** = SDOH
- Consult [Screening and Assessments Guidance](http://hl7.org/fhir/us/core/screening-and-assessments.html)
- Reference SDOH-specific value sets for codes

### Linking to Goals

ServiceRequest MAY reference Goal resources to indicate the service is part of achieving a patient goal:
- Use **supportingInfo** to reference related Goal resources
- This pattern is common in Care Plan contexts

### Insurance and Coverage

Planned Coverage information from C-CDA maps to ServiceRequest.insurance:
- Extract entryRelationship[typeCode='COMP'] with Planned Coverage template
- Create Coverage resource
- Reference from ServiceRequest.insurance

## SMART on FHIR Scopes

### Resource-Level Scopes

- `patient/ServiceRequest.rs` - Read and search ServiceRequests for a single patient
- `user/ServiceRequest.rs` - Read and search ServiceRequests for all patients user has access to
- `system/ServiceRequest.rs` - Read and search all ServiceRequests (backend services)

### Granular Scopes

For SDOH-specific access:
```
patient/ServiceRequest.rs?category=http://hl7.org/fhir/us/core/CodeSystem/us-core-category|sdoh
```

## References

- [US Core ServiceRequest Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest)
- [FHIR R4 ServiceRequest Resource](http://hl7.org/fhir/R4/servicerequest.html)
- [US Core Implementation Guide v8.0.1](http://hl7.org/fhir/us/core/STU8/)
- [USCDI v4](https://www.healthit.gov/isa/united-states-core-data-interoperability-uscdi)

---

**Next Steps**: See [Planned Procedure Mapping](../mapping/18-service-request.md) for C-CDA to FHIR conversion specifications.
