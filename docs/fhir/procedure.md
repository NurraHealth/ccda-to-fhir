# FHIR R4B: Procedure Resource

## Overview

The Procedure resource documents an action that is or was performed on or for a patient, practitioner, device, organization, or location. This encompasses surgical interventions, diagnostic procedures, counseling, and inspections.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | Procedure |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Patient |
| Responsible Work Group | Patient Care |
| URL | https://hl7.org/fhir/R4B/procedure.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure |

## Scope and Usage

**Included:**
- Surgical procedures
- Diagnostics and endoscopy
- Biopsies
- Counseling and physiotherapy
- Home modifications
- Accreditation verification

**Excluded (use specific resources instead):**
- Immunization (use Immunization resource)
- Medication administration (use MedicationAdministration resource)
- Communication activities (use Communication resource)
- Nutrition intake (use NutritionIntake resource)

**Key Distinction:** Procedures involve intent to change mental/physical state; Communications are informational only.

**Implementation Notes:**
- Procedure provides summary-level information, not real-time snapshots
- Long-running procedures (psychotherapy) captured as aggregated progress
- Diagnostic procedures generate Observations/DiagnosticReports separately
- Task resources often parallel Procedure (workflow vs. clinical action distinction)

## JSON Structure

```json
{
  "resourceType": "Procedure",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/procedure",
      "value": "d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"
    }
  ],
  "instantiatesCanonical": [
    "http://example.org/fhir/PlanDefinition/appendectomy-protocol"
  ],
  "basedOn": [
    {
      "reference": "ServiceRequest/example"
    }
  ],
  "partOf": [
    {
      "reference": "Procedure/surgery-example"
    }
  ],
  "status": "completed",
  "statusReason": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "397943006",
        "display": "Planned"
      }
    ]
  },
  "category": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "387713003",
        "display": "Surgical procedure"
      }
    ]
  },
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "6025007",
        "display": "Laparoscopic appendectomy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "44970",
        "display": "Laparoscopic appendectomy"
      },
      {
        "system": "http://www.cms.gov/Medicare/Coding/ICD10",
        "code": "0DTJ4ZZ",
        "display": "Resection of Appendix, Percutaneous Endoscopic Approach"
      }
    ],
    "text": "Laparoscopic Appendectomy"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "performedDateTime": "2015-03-01",
  "recorder": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "asserter": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "performer": [
    {
      "function": {
        "coding": [
          {
            "system": "http://snomed.info/sct",
            "code": "304292004",
            "display": "Surgeon"
          }
        ]
      },
      "actor": {
        "reference": "Practitioner/example",
        "display": "Dr. Adam Careful"
      },
      "onBehalfOf": {
        "reference": "Organization/example",
        "display": "Community Health and Hospitals"
      }
    }
  ],
  "location": {
    "reference": "Location/example",
    "display": "Community Health and Hospitals"
  },
  "reasonCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "74400008",
          "display": "Appendicitis"
        }
      ]
    }
  ],
  "reasonReference": [
    {
      "reference": "Condition/appendicitis"
    }
  ],
  "bodySite": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "66754008",
          "display": "Appendix structure"
        }
      ]
    }
  ],
  "outcome": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "385669000",
        "display": "Successful"
      }
    ]
  },
  "report": [
    {
      "reference": "DiagnosticReport/operative-report"
    }
  ],
  "complication": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "131148009",
          "display": "Bleeding"
        }
      ]
    }
  ],
  "complicationDetail": [
    {
      "reference": "Condition/complication"
    }
  ],
  "followUp": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "30549001",
          "display": "Suture removal"
        }
      ]
    }
  ],
  "note": [
    {
      "text": "Procedure completed without complications. Patient tolerated well."
    }
  ],
  "focalDevice": [
    {
      "action": {
        "coding": [
          {
            "system": "http://hl7.org/fhir/device-action",
            "code": "implanted",
            "display": "Implanted"
          }
        ]
      },
      "manipulated": {
        "reference": "Device/mesh-implant"
      }
    }
  ],
  "usedReference": [
    {
      "reference": "Device/laparoscope"
    }
  ],
  "usedCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "86174004",
          "display": "Laparoscope"
        }
      ]
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

External identifiers for this procedure.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |

### instantiatesCanonical (0..*)

| Type | Description |
|------|-------------|
| canonical[] | FHIR protocol or definition followed |

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference(CarePlan \| ServiceRequest) | Request this procedure fulfills |

### partOf (0..*)

| Type | Description |
|------|-------------|
| Reference(Procedure \| Observation \| MedicationAdministration) | Part of referenced procedure |

### status (1..1)

The status of the procedure. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | preparation \| in-progress \| not-done \| on-hold \| stopped \| completed \| entered-in-error \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/event-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| preparation | Preparation | Procedure is being prepared |
| in-progress | In Progress | Procedure is underway |
| not-done | Not Done | Procedure was not performed |
| on-hold | On Hold | Procedure is suspended |
| stopped | Stopped | Procedure was ended early |
| completed | Completed | Procedure has been completed |
| entered-in-error | Entered in Error | Record was entered in error |
| unknown | Unknown | Status is unknown |

**Note:** Status modifier changes interpretation of other elements.

### statusReason (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Reason for current status |

### category (0..1)

Classification of the procedure.

| Type | Description |
|------|-------------|
| CodeableConcept | Procedure category code |

**Common Category Codes (SNOMED):**
| Code | Display |
|------|---------|
| 387713003 | Surgical procedure |
| 103693007 | Diagnostic procedure |
| 46947000 | Chiropractic manipulation |
| 410606002 | Social service procedure |
| 24642003 | Psychiatry procedure |

### code (0..1)

The specific procedure performed.

| Type | Description |
|------|-------------|
| CodeableConcept | Procedure code |

**Common Code Systems:**
| System URI | Name |
|------------|------|
| `http://snomed.info/sct` | SNOMED CT |
| `http://www.ama-assn.org/go/cpt` | CPT |
| `http://www.cms.gov/Medicare/Coding/ICD10` | ICD-10-PCS |
| `http://hl7.org/fhir/sid/icd-9-cm` | ICD-9-CM Vol 3 |
| `https://www.cms.gov/Medicare/Coding/HCPCSReleaseCodeSets` | HCPCS |

### subject (1..1)

This is a **modifier element**.

| Type | Description |
|------|-------------|
| Reference(Patient \| Group \| Device \| Practitioner \| Organization \| Location) | Required reference to subject |

### focus (0..1)

True target when differs from subject. This is a **modifier element**.

| Type | Description |
|------|-------------|
| Reference(Patient \| Group \| RelatedPerson \| Practitioner \| Organization \| CareTeam \| PractitionerRole \| Specimen) | Alternative target for the procedure |

**Note:** Focus redefines the actual procedure target.

### encounter (0..1)

| Type | Description |
|------|-------------|
| Reference(Encounter) | Encounter associated with procedure |

### performed[x] (0..1)

When the procedure was performed.

| Element | Type | Description |
|---------|------|-------------|
| performedDateTime | dateTime | Single point in time |
| performedPeriod | Period | Start and end time |
| performedString | string | Textual description |
| performedAge | Age | Patient age when performed |
| performedRange | Range | Age range |

### recorder (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| RelatedPerson \| Practitioner \| PractitionerRole) | Who recorded the procedure |

### asserter (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| RelatedPerson \| Practitioner \| PractitionerRole) | Person asserting procedure occurred |

### recorded (0..1)

| Type | Description |
|------|-------------|
| dateTime | Date procedure was first documented in record |

### performer (0..*)

Who performed the procedure.

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| function | CodeableConcept | 0..1 | Type of role performed |
| actor | Reference | 1..1 | Who performed procedure (Required) |
| onBehalfOf | Reference(Organization) | 0..1 | Organization they were acting for |
| period | Period | 0..1 | Time span of involvement |

**actor Types:** Practitioner, PractitionerRole, Organization, Patient, RelatedPerson, Device, CareTeam, HealthcareService

**Constraint:** onBehalfOf can only be populated when performer.actor isn't Practitioner/PractitionerRole.

**Performer Function Codes:**
| Code | Display | System |
|------|---------|--------|
| 304292004 | Surgeon | SNOMED |
| 309343006 | Primary surgeon | SNOMED |
| 62247001 | Assistant surgeon | SNOMED |
| 224561008 | Anesthesiologist | SNOMED |
| 106292003 | Nurse | SNOMED |

### location (0..1)

| Type | Description |
|------|-------------|
| Reference(Location) | Where procedure occurred |

### reason (0..*)

Justification for the procedure.

| Type | Description |
|------|-------------|
| CodeableReference[] | Reason as CodeableReference (Condition, Observation, Procedure, DiagnosticReport, DocumentReference) |

**Value Set:** http://hl7.org/fhir/ValueSet/procedure-reason (Example binding)

### bodySite (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Body site where procedure performed |

**Value Set:** http://hl7.org/fhir/ValueSet/body-site (Example binding)

**Constraint:** bodyStructure SHALL only be present if bodySite is not present.

**Common Body Site Codes (SNOMED):**
| Code | Display |
|------|---------|
| 66754008 | Appendix structure |
| 64033007 | Kidney structure |
| 80891009 | Heart structure |
| 39607008 | Lung structure |
| 71341001 | Bone structure |
| 76752008 | Breast structure |
| 302551006 | Entire joint |

### bodyStructure (0..1)

| Type | Description |
|------|-------------|
| Reference(BodyStructure) | Alternative to bodySite - a BodyStructure resource reference |

### supportingInfo (0..*)

| Type | Description |
|------|-------------|
| Reference(Any) | Relevant patient record resources supporting the procedure |

### outcome (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Procedure outcome |

**Outcome Codes (SNOMED):**
| Code | Display |
|------|---------|
| 385669000 | Successful |
| 385671000 | Unsuccessful |
| 385670004 | Partially successful |

### report (0..*)

| Type | Description |
|------|-------------|
| Reference(DiagnosticReport \| DocumentReference \| Composition) | Procedure reports |

### complication (0..*)

Post-procedure conditions.

| Type | Description |
|------|-------------|
| CodeableReference[] | Complications as CodeableReference (code or Condition reference) |

**Value Set:** http://hl7.org/fhir/ValueSet/condition-code (Example binding)

### followUp (0..*)

Required next steps.

| Type | Description |
|------|-------------|
| CodeableReference[] | Follow-up instructions as CodeableReference (ServiceRequest or PlanDefinition) |

**Value Set:** http://hl7.org/fhir/ValueSet/procedure-followup (Example binding)

### note (0..*)

| Type | Description |
|------|-------------|
| Annotation[] | Additional notes |

### focalDevice (0..*)

Device manipulated during procedure.

| Element | Type | Description |
|---------|------|-------------|
| action | CodeableConcept | Kind of device action |
| manipulated | Reference(Device) | Device that was manipulated |

**Device Action Codes:**
| Code | Display |
|------|---------|
| implanted | Implanted |
| explanted | Explanted |
| manipulated | Manipulated |

### used (0..*)

Devices, Medications, Substances used during procedure.

| Type | Description |
|------|-------------|
| CodeableReference[] | Items used as CodeableReference (Device, Medication, Substance, BiologicallyDerivedProduct) |

**Value Set:** http://hl7.org/fhir/ValueSet/device-type (Example binding)

## US Core Conformance Requirements

For US Core Procedure profile compliance:

1. **SHALL** support `status`
2. **SHALL** support `code`
3. **SHALL** support `subject`
4. **SHALL** support `performed[x]`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | preparation \| in-progress \| not-done \| on-hold \| stopped \| completed \| entered-in-error \| unknown |
| code | token | Procedure code |
| subject | reference | Who the procedure was performed on |
| patient | reference | Search by subject - Patient |
| encounter | reference | Encounter associated with procedure |
| date | date | When the procedure was performed |
| performer | reference | Who performed the procedure |
| location | reference | Where the procedure occurred |
| reason-code | token | Reason procedure performed |
| reason-reference | reference | Reason procedure performed |
| category | token | Classification of procedure |
| part-of | reference | Part of referenced procedure |
| based-on | reference | Request for this procedure |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| pro-1 | bodyStructure SHALL only be present if Procedure.bodySite is not present |
| pro-2 | onBehalfOf can only populate with non-Practitioner/PractitionerRole actors |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of other elements
- **subject** - Defines who/what the procedure is performed on
- **focus** - Redefines the actual procedure target when different from subject

## Compartments

The Procedure resource is part of the following compartments:
- Encounter
- Group
- Patient
- Practitioner
- RelatedPerson

## Related Resources

The Procedure resource is referenced by:
- Account, AdverseEvent, Appointment, CarePlan, Claim
- DetectedIssue, DiagnosticReport, Encounter, EpisodeOfCare
- Flag, Goal, ImagingStudy, MedicationAdministration
- MedicationRequest, NutritionIntake, Observation
- QuestionnaireResponse, ServiceRequest, Specimen

## References

- FHIR R4B Procedure: https://hl7.org/fhir/R4B/procedure.html
- US Core Procedure Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure
- SNOMED CT: http://snomed.info/sct
- CPT: https://www.ama-assn.org/practice-management/cpt
- ICD-10-PCS: https://www.cms.gov/Medicare/Coding/ICD10
