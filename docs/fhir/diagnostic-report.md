# FHIR R4B: DiagnosticReport Resource

## Overview

The DiagnosticReport resource represents findings and interpretation of diagnostic tests performed on patients, groups of patients, devices, and locations. It serves as the central document when diagnostic investigations conclude, integrating clinical context with atomic results, images, textual interpretations, and formatted reports. This resource functions as an event resource within FHIR's workflow framework.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | DiagnosticReport |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | 3 (Trial Use) |
| Security Category | Patient |
| Responsible Work Group | Orders and Observations |
| URL | https://hl7.org/fhir/R4B/diagnosticreport.html |
| US Core Laboratory Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-lab |

## Scope and Usage

DiagnosticReport serves as the central document when diagnostic investigations conclude. It encompasses:

- Laboratory results (chemistry, hematology, microbiology)
- Pathology and histopathology findings
- Imaging investigations (x-ray, CT, MRI)
- Specialized diagnostics (cardiology, gastroenterology)
- Product quality testing

The resource supports flexible presentation: atomic structured data, narrative text, or formatted documents (PDF). It explicitly does NOT support cumulative result presentations or detailed sequencing reports (use specialized Genomics Reporting IG instead).

### Key Applications

- Laboratory data reporting with structured results
- Imaging reports with references to DICOM studies
- Pathology reports with narrative and coded diagnoses
- Cardiology diagnostic findings
- Genomic testing results

## Boundaries and Relationships

### Distinction from Observation

While Observation provides atomic data points, DiagnosticReport adds clinical context, workflow support, and mixed content types. DiagnosticReport groups related observations and provides interpretation and conclusions.

### Distinction from Composition

Composition serves narrative-driven reports with minimal workflow requirements (histology, mortuary reports). Use DiagnosticReport when the focus is on diagnostic test results with workflow status tracking.

### Related Resources

**Referenced By:** CarePlan, ChargeItem, ClinicalImpression, Communication, Condition, Contract, DeviceRequest, FamilyMemberHistory, GuidanceResponse, ImagingStudy, Immunization, MedicationAdministration, Procedure, RequestGroup, RiskAssessment, ServiceRequest, SupplyRequest.

## JSON Structure

### Laboratory Report Example

```json
{
  "resourceType": "DiagnosticReport",
  "id": "cbc",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-lab"
    ]
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/lab",
      "value": "2021-123456"
    }
  ],
  "basedOn": [
    {
      "reference": "ServiceRequest/lab-order-123"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
          "code": "LAB",
          "display": "Laboratory"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "58410-2",
        "display": "Complete blood count (hemogram) panel - Blood by Automated count"
      }
    ],
    "text": "Complete Blood Count"
  },
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "encounter": {
    "reference": "Encounter/example"
  },
  "effectiveDateTime": "2020-03-01T08:30:00-05:00",
  "issued": "2020-03-01T15:30:00-05:00",
  "performer": [
    {
      "reference": "Organization/lab",
      "display": "Community Hospital Laboratory"
    }
  ],
  "resultsInterpreter": [
    {
      "reference": "Practitioner/pathologist",
      "display": "Dr. Sarah Pathologist"
    }
  ],
  "specimen": [
    {
      "reference": "Specimen/blood-sample"
    }
  ],
  "result": [
    {
      "reference": "Observation/hemoglobin"
    },
    {
      "reference": "Observation/wbc-count"
    },
    {
      "reference": "Observation/platelet-count"
    }
  ],
  "conclusion": "All values within normal limits.",
  "conclusionCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "17621005",
          "display": "Normal"
        }
      ]
    }
  ]
}
```

### Imaging Report Example

```json
{
  "resourceType": "DiagnosticReport",
  "id": "chest-xray",
  "identifier": [
    {
      "system": "http://hospital.example.org/radiology",
      "value": "XR-2020-0301-123"
    }
  ],
  "status": "final",
  "category": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
          "code": "RAD",
          "display": "Radiology"
        }
      ]
    }
  ],
  "code": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "30746-2",
        "display": "Chest X-ray"
      }
    ]
  },
  "subject": {
    "reference": "Patient/example"
  },
  "effectiveDateTime": "2020-03-01",
  "issued": "2020-03-01T16:45:00-05:00",
  "performer": [
    {
      "reference": "Practitioner/radiologist",
      "display": "Dr. John Radiologist"
    }
  ],
  "imagingStudy": [
    {
      "reference": "ImagingStudy/chest-study"
    }
  ],
  "media": [
    {
      "comment": "Key image showing normal cardiac silhouette",
      "link": {
        "reference": "Media/chest-key-image"
      }
    }
  ],
  "conclusion": "Normal chest x-ray. No acute cardiopulmonary process.",
  "conclusionCode": [
    {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "17621005",
          "display": "Normal"
        }
      ]
    }
  ],
  "presentedForm": [
    {
      "contentType": "application/pdf",
      "language": "en-US",
      "data": "JVBERi0xLjQKJeLjz9MK...",
      "title": "Chest X-Ray Report",
      "creation": "2020-03-01T16:45:00-05:00"
    }
  ]
}
```

## Element Definitions

### identifier (0..*)

Business identifiers assigned by the performer or other systems.

| Element | Type | Description |
|---------|------|-------------|
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| type | CodeableConcept | Identifier type (PLAC for placer, FILL for filler) |

**Implementation Note:** Use Identifier.type to distinguish "Placer" (code: PLAC) and "Filler" identifiers from requesters and performers respectively.

### basedOn (0..*)

Details of the request for this diagnostic investigation.

| Type | Description |
|------|-------------|
| Reference(CarePlan \| ImmunizationRecommendation \| MedicationRequest \| NutritionOrder \| ServiceRequest) | Request fulfilled by this report |

### status (1..1)

The status of the diagnostic report. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | registered \| partial \| preliminary \| final \| amended \| corrected \| appended \| cancelled \| entered-in-error \| unknown |

**Value Set:** http://hl7.org/fhir/ValueSet/diagnostic-report-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| registered | Registered | Existence of report is registered but not yet available |
| partial | Partial | Some results available |
| preliminary | Preliminary | Initial or interim findings |
| final | Final | Report is complete and verified |
| amended | Amended | Subsequent to final with amendments |
| corrected | Corrected | Subsequent to final with corrections |
| appended | Appended | Subsequent to final with additional information |
| cancelled | Cancelled | Report is cancelled |
| entered-in-error | Entered in Error | Report was entered in error |
| unknown | Unknown | Status is not known |

**Critical Rules:**
- Reports must not reach "final" until all constituent data items are final or appended
- Withdrawn reports must be marked "entered-in-error" with narrative like "This report has been withdrawn"
- Consumers must handle updated/revised reports appropriately

### category (0..*)

Classification of the type of diagnostic report.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Service category |

**Value Set:** http://terminology.hl7.org/ValueSet/diagnostic-service-sections (Example binding, v2-0074)

**Common Category Codes:**
| Code | Display | System |
|------|---------|--------|
| LAB | Laboratory | http://terminology.hl7.org/CodeSystem/v2-0074 |
| RAD | Radiology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| PATH | Pathology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| AU | Audiology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| CG | Cytogenetics | http://terminology.hl7.org/CodeSystem/v2-0074 |
| CH | Chemistry | http://terminology.hl7.org/CodeSystem/v2-0074 |
| CP | Cytopathology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| CT | CAT Scan | http://terminology.hl7.org/CodeSystem/v2-0074 |
| CTH | Cardiac Catheterization | http://terminology.hl7.org/CodeSystem/v2-0074 |
| HM | Hematology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| ICU | Bedside ICU Monitoring | http://terminology.hl7.org/CodeSystem/v2-0074 |
| MB | Microbiology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| NMR | Nuclear Magnetic Resonance | http://terminology.hl7.org/CodeSystem/v2-0074 |
| SP | Surgical Pathology | http://terminology.hl7.org/CodeSystem/v2-0074 |
| URN | Urinalysis | http://terminology.hl7.org/CodeSystem/v2-0074 |
| XRC | Cineradiograph | http://terminology.hl7.org/CodeSystem/v2-0074 |

### code (1..1)

Name/code for this diagnostic report. Required element.

| Type | Description |
|------|-------------|
| CodeableConcept | LOINC or other diagnostic report code |

**Value Set:** http://hl7.org/fhir/ValueSet/report-codes (Preferred binding, LOINC Diagnostic Report Codes)

**Implementation Note:** DiagnosticReport.code names the report itself. This is distinct from the result observations which have their own codes.

**Common Laboratory Panel Codes (LOINC):**
| Code | Display |
|------|---------|
| 58410-2 | Complete blood count (hemogram) panel - Blood by Automated count |
| 24331-1 | Lipid panel - Serum or Plasma |
| 24323-8 | Comprehensive metabolic 2000 panel - Serum or Plasma |
| 24356-8 | Urinalysis complete panel - Urine |
| 57698-3 | Lipid panel with direct LDL - Serum or Plasma |
| 57021-8 | CBC W Auto Differential panel - Blood |

**Common Imaging Codes (LOINC):**
| Code | Display |
|------|---------|
| 30746-2 | Chest X-ray |
| 36643-5 | CT Head |
| 24727-0 | MRI Brain |
| 30954-2 | Diagnostic imaging study |

### subject (0..1)

The subject of the report.

| Type | Description |
|------|-------------|
| Reference(Patient \| Group \| Device \| Location \| Organization \| Procedure \| Practitioner \| Medication \| Substance) | Who/what the report is about |

**Implementation Note:** Usually a Patient reference. In R4B, expanded to include additional target types.

### encounter (0..1)

The healthcare event during which this diagnostic report was created.

| Type | Description |
|------|-------------|
| Reference(Encounter) | Healthcare event when report was created |

### effective[x] (0..1)

The clinically relevant time/time-period for the report.

| Element | Type | Description |
|---------|------|-------------|
| effectiveDateTime | dateTime | Single point in time |
| effectivePeriod | Period | Time period |

**Implementation Note:** This is mandatory for reports even when specimen information is unavailable. It represents procedure time or specimen collection time depending on context. This is the time that is relevant to the reported results.

### issued (0..1)

The date and time that this version of the report was made available to providers.

| Type | Description |
|------|-------------|
| instant | Date/time report was released |

**Implementation Note:** May be different from the last update time of the resource itself, as the report may be edited during review without being released.

### performer (0..*)

The diagnostic service that is responsible for issuing the report.

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| CareTeam) | Responsible diagnostic service |

**Implementation Note:** This is not necessarily the source of the observations, but who is taking responsibility for the clinical report.

### resultsInterpreter (0..*)

The practitioner or organization that is responsible for the report's conclusions and interpretations.

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| CareTeam) | Primary result interpreter |

**Implementation Note:** May be different from performer. For example, a radiologist may interpret an imaging study performed by a technologist.

### specimen (0..*)

Details about the specimen on which this diagnostic report is based.

| Type | Description |
|------|-------------|
| Reference(Specimen) | Specimens this report is based on |

**Implementation Note:** If the specimen information is recorded separately, the specimen references can be used to link the report to the specimen. Multiple specimens may be used for a single report.

### result (0..*)

Observations that are part of this diagnostic report.

| Type | Description |
|------|-------------|
| Reference(Observation) | Observations comprising the report |

**Implementation Note:** Observations may form hierarchical panels/groups using Observation.hasMember. DiagnosticReport.result contains top-level Observation references. Two nesting levels rarely exceed clinical needs.

### imagingStudy (0..*)

One or more links to full details of any imaging performed during the diagnostic investigation.

| Type | Description |
|------|-------------|
| Reference(ImagingStudy) | Reference to DICOM imaging studies |

**Implementation Note:** Typically, this is imaging performed as part of the diagnostic investigation, such as a chest x-ray for a respiratory diagnosis. PACS viewers can use these references.

### media (0..*)

Key images associated with this report. The images are generally created during the diagnostic process and may be directly of the patient or of specimens.

| Element | Type | Description |
|---------|------|-------------|
| comment | string | Comment about the image |
| link | Reference(Media) | Reference to the image (Required) |

**Implementation Note:** ImagingStudy and media elements may overlap. Both, either, or neither may be provided depending on use case—imaging study references enable PACS viewer integration; media elements highlight key diagnostic images.

### conclusion (0..1)

Concise and clinically contextualized summary conclusion (interpretation/impression) of the diagnostic report.

| Type | Description |
|------|-------------|
| string | Clinical conclusion/interpretation |

### conclusionCode (0..*)

One or more codes that represent the summary conclusion (interpretation/impression) of the diagnostic report.

| Type | Description |
|------|-------------|
| CodeableConcept[] | Codes for conclusion |

**Value Set:** http://hl7.org/fhir/ValueSet/clinical-findings (Example binding, SNOMED CT Clinical Findings)

### presentedForm (0..*)

Rich text representation of the entire result as issued by the diagnostic service.

| Element | Type | Description |
|---------|------|-------------|
| contentType | code | Mime type (e.g., application/pdf) |
| language | code | Language (e.g., en-US) |
| data | base64Binary | Encoded document data |
| title | string | Label for the document |
| creation | dateTime | When document was created |

**Implementation Note:** Multiple formats are allowed but they should all be semantically equivalent.

## Report Content Patterns

Three primary presentation models exist:

### 1. Atomic Data Only (High-Volume Labs)
Hierarchical Observations with tabular narrative. Best for labs with many structured numeric results.

### 2. Structured + Document (Histopathology)
Presented form document with key images and coded diagnoses. Combines narrative with discrete data elements.

### 3. Narrative + Document (Imaging)
Document report with imaging study references. Primary content is in presentedForm with imaging references.

## Observation Nesting

DiagnosticReport.code names the report itself; DiagnosticReport.result contains Observation references that may form hierarchical panels/groups using Observation.hasMember.

"Profiles" typically consist of multiple panels; two nesting levels rarely exceed clinical needs:
- Level 1: Panel observation (e.g., CBC panel)
- Level 2: Individual result observations (e.g., WBC, RBC, platelets)

## US Core Conformance Requirements

### US Core DiagnosticReport Laboratory Profile

1. **SHALL** support `status`
2. **SHALL** support `category` with value 'LAB'
3. **SHALL** support `code` (extensible binding to US Core Laboratory Test Codes)
4. **SHALL** support `subject` (reference to Patient)
5. **SHALL** support `effectiveDateTime` or `effectivePeriod` (when status is partial, preliminary, final, amended, corrected, or appended)
6. **SHALL** support `issued` (when status is partial, preliminary, final, amended, corrected, or appended)
7. **SHOULD** support `encounter`
8. **SHOULD** support `performer`
9. **SHOULD** support `resultsInterpreter`
10. **SHOULD** support `result` (references to US Core Laboratory Result Observation)

### US Core Search Parameters

**Mandatory (SHALL support):**
- `patient` - Retrieve all reports for a specific patient
- `patient` + `category` - Filter by LAB category
- `patient` + `code` - Search by test code (supports multiple codes)
- `patient` + `category` + `date` - Include date range filters (gt, lt, ge, le)

**Optional (SHOULD support):**
- `patient` + `status` - Filter by report status
- `patient` + `category` + `_lastUpdated` - Track resource changes
- `patient` + `code` + `date` - Combined code and date searches

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| based-on | reference | Reference to the service request |
| category | token | Service category |
| code | token | Report code (LOINC) |
| conclusion | token | Coded conclusion |
| date | date | When report was performed |
| encounter | reference | Associated encounter |
| identifier | token | Business identifier |
| issued | date | When report was issued |
| media | reference | Reference to media |
| patient | reference | Patient reference |
| performer | reference | Responsible practitioner/organization |
| result | reference | Link to atomic results |
| results-interpreter | reference | Result interpreter |
| specimen | reference | Specimen used |
| status | token | Report status |
| subject | reference | Subject of report |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| dom-2 | If the resource is contained in another resource, it SHALL NOT contain nested Resources |
| dom-3 | If the resource is contained in another resource, it SHALL be referred to from elsewhere in the resource |
| dom-4 | If a resource is contained in another resource, it SHALL NOT have a meta.versionId or a meta.lastUpdated |
| dom-5 | If a resource is contained in another resource, it SHALL NOT have a security label |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the report

## Compartments

The DiagnosticReport resource is part of the following compartments:
- Device
- Encounter
- Patient
- Practitioner

## Implementation Notes

### CLIA Compliance
The US Core profile references a CLIA/USCDI/HL7 crossmapping table for regulatory alignment.

### Code Flexibility
Systems may include local codes alongside standard LOINC codes. Use code.text for display purposes.

### Provenance
The performer and resultsInterpreter elements communicate author-level provenance data. For more detailed provenance, use a separate Provenance resource.

### Last Updated
The meta.lastUpdated element should reflect new reports and status changes, including amendments.

### Status Lifecycle
Follow the status lifecycle carefully:
1. registered → preliminary → final (normal flow)
2. final → amended/corrected/appended (updates)
3. Any status → cancelled (cancellation)
4. Any status → entered-in-error (error correction)

## References

- FHIR R4B DiagnosticReport: https://hl7.org/fhir/R4B/diagnosticreport.html
- US Core DiagnosticReport Lab Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-diagnosticreport-lab
- C-CDA on FHIR Results Mapping: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html
- LOINC: https://loinc.org/
- Diagnostic Service Section Codes: http://terminology.hl7.org/CodeSystem/v2-0074
- SNOMED CT: https://www.snomed.org/
