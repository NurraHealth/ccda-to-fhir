# FHIR R4B: DocumentReference Resource

## Overview

The DocumentReference resource provides metadata about a document so that the document can be discovered and managed. It indexes documents of any kind, encompassing "any serialized object with a mime-type" including clinical documents, images, video, and audio files.

## Resource Information

| Attribute | Value |
|-----------|-------|
| Resource Type | DocumentReference |
| FHIR Version | R4B (4.3.0) |
| Maturity Level | Normative |
| Security Category | Not Classified |
| Responsible Work Group | Orders and Observations |
| URL | https://hl7.org/fhir/R4B/documentreference.html |
| US Core Profile | http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference |

## Scope and Usage

The DocumentReference resource indexes documents for discovery and management. Key uses include:
- Clinical notes and summaries
- Images and diagnostic reports
- Video and audio content
- Scanned documents
- External documents with URL references

## JSON Structure

```json
{
  "resourceType": "DocumentReference",
  "id": "example",
  "meta": {
    "profile": [
      "http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference"
    ]
  },
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  },
  "identifier": [
    {
      "system": "http://hospital.example.org/document",
      "value": "TT988"
    }
  ],
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "34133-9",
        "display": "Summarization of Episode Note"
      }
    ],
    "text": "Continuity of Care Document"
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/example",
    "display": "Ellen Ross"
  },
  "date": "2020-03-01T10:20:00-05:00",
  "author": [
    {
      "reference": "Practitioner/example",
      "display": "Dr. Adam Careful"
    },
    {
      "reference": "Organization/example",
      "display": "Community Health and Hospitals"
    }
  ],
  "authenticator": {
    "reference": "Practitioner/example",
    "display": "Dr. Adam Careful"
  },
  "custodian": {
    "reference": "Organization/example",
    "display": "Community Health and Hospitals"
  },
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "reference": "DocumentReference/previous"
      }
    }
  ],
  "description": "Continuity of Care Document for Ellen Ross",
  "securityLabel": [
    {
      "coding": [
        {
          "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
          "code": "N",
          "display": "normal"
        }
      ]
    }
  ],
  "content": [
    {
      "attachment": {
        "contentType": "application/xml",
        "language": "en-US",
        "url": "http://example.org/documents/TT988.xml",
        "size": 3654,
        "hash": "2jmj7l5rSw0yVb/vlWAYkK/YBwk=",
        "title": "Continuity of Care Document",
        "creation": "2020-03-01T10:20:00-05:00"
      },
      "format": {
        "system": "urn:oid:1.3.6.1.4.1.19376.1.2.3",
        "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
        "display": "C-CDA Structured Body 2.1"
      }
    },
    {
      "attachment": {
        "contentType": "application/pdf",
        "language": "en-US",
        "url": "http://example.org/documents/TT988.pdf",
        "title": "Continuity of Care Document (PDF)"
      },
      "format": {
        "system": "urn:oid:1.3.6.1.4.1.19376.1.2.3",
        "code": "urn:ihe:iti:xds-sd:pdf:2008",
        "display": "PDF"
      }
    }
  ],
  "context": {
    "encounter": [
      {
        "reference": "Encounter/example"
      }
    ],
    "event": [
      {
        "coding": [
          {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
            "code": "PCPR",
            "display": "care provision"
          }
        ]
      }
    ],
    "period": {
      "start": "2020-01-01",
      "end": "2020-03-01"
    },
    "facilityType": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "394802001",
          "display": "General medicine"
        }
      ]
    },
    "practiceSetting": {
      "coding": [
        {
          "system": "http://snomed.info/sct",
          "code": "408443003",
          "display": "General medical practice"
        }
      ]
    },
    "sourcePatientInfo": {
      "reference": "Patient/example"
    },
    "related": [
      {
        "reference": "Observation/example"
      }
    ]
  }
}
```

## Element Definitions

### masterIdentifier (0..1)

Master version-specific identifier for the document.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| secondary \| old |
| type | CodeableConcept | Description of identifier |
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| period | Period | Time period when id is/was valid |
| assigner | Reference(Organization) | Organization that issued id |

### identifier (0..*)

Other identifiers for the document.

| Element | Type | Description |
|---------|------|-------------|
| use | code | usual \| official \| temp \| secondary \| old |
| type | CodeableConcept | Description of identifier |
| system | uri | Namespace for identifier value |
| value | string | The identifier value |
| period | Period | Time period when id is/was valid |
| assigner | Reference(Organization) | Organization that issued id |

### version (0..1)

| Type | Description |
|------|-------------|
| string | Variation identifier for the content |

### basedOn (0..*)

| Type | Description |
|------|-------------|
| Reference(Appointment \| AppointmentResponse \| CarePlan \| Claim \| CommunicationRequest \| Contract \| CoverageEligibilityRequest \| DeviceRequest \| EnrollmentRequest \| ImmunizationRecommendation \| MedicationRequest \| NutritionOrder \| RequestOrchestration \| ServiceRequest \| SupplyRequest \| VisionPrescription) | Procedure fulfilled by document creation |

### status (1..1)

The status of this document reference. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | current \| superseded \| entered-in-error |

**Value Set:** http://hl7.org/fhir/ValueSet/document-reference-status (Required binding)

**Status Definitions:**
| Code | Display | Definition |
|------|---------|------------|
| current | Current | This is the current reference for this document |
| superseded | Superseded | This reference has been superseded by another |
| entered-in-error | Entered in Error | This reference was created in error |

### docStatus (0..1)

The status of the underlying document. This is a **modifier element**.

| Type | Values |
|------|--------|
| code | registered \| partial \| preliminary \| final \| amended \| corrected \| appended \| cancelled \| entered-in-error \| deprecated \| unknown |

### modality (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Imaging modality used (for images) |

### type (0..1)

The type of document.

| Type | Description |
|------|-------------|
| CodeableConcept | LOINC document type code |

**Common Document Type Codes (LOINC):**
| Code | Display |
|------|---------|
| 34133-9 | Summarization of Episode Note |
| 18842-5 | Discharge Summary |
| 11488-4 | Consultation Note |
| 11504-8 | Surgical Operation Note |
| 11506-3 | Progress Note |
| 28570-0 | Procedure Note |
| 34117-2 | History and Physical Note |
| 57133-1 | Referral Note |
| 34111-5 | Emergency Department Note |
| 57016-8 | Privacy Policy Acknowledgement Document |

### category (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Document category |

**US Core Category Codes:**
| Code | Display |
|------|---------|
| clinical-note | Clinical Note |

### subject (0..1)

| Type | Description |
|------|-------------|
| Reference(Patient \| Practitioner \| Group \| Device) | Who/what is the subject |

### date (0..1)

| Type | Description |
|------|-------------|
| instant | When document reference was created |

### author (0..*)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization \| Device \| Patient \| RelatedPerson) | Who authored the document |

### authenticator (0..1)

| Type | Description |
|------|-------------|
| Reference(Practitioner \| PractitionerRole \| Organization) | Who/what authenticated the document |

### custodian (0..1)

| Type | Description |
|------|-------------|
| Reference(Organization) | Organization which maintains the document |

### relatesTo (0..*)

Relationships to other documents.

| Element | Type | Description |
|---------|------|-------------|
| code | code | replaces \| transforms \| signs \| appends |
| target | Reference(DocumentReference) | Target of the relationship |

**Relationship Codes:**
| Code | Display | Definition |
|------|---------|------------|
| replaces | Replaces | This document replaces the target |
| transforms | Transforms | This document transforms the target |
| signs | Signs | This document signs the target |
| appends | Appends | This document appends to the target |

### description (0..1)

| Type | Description |
|------|-------------|
| markdown | Human-readable summary (supports markdown) |

### event (0..*)

| Type | Description |
|------|-------------|
| CodeableReference[] | Clinical acts documented |

### bodyStructure (0..*)

| Type | Description |
|------|-------------|
| CodeableReference(BodyStructure)[] | Anatomic structures included in document |

### facilityType (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Kind of facility where patient was seen |

**Constraint:** facilityType only present if context is not an encounter.

### practiceSetting (0..1)

| Type | Description |
|------|-------------|
| CodeableConcept | Clinical specialty context |

**Constraint:** practiceSetting only present if context absent.

### securityLabel (0..*)

| Type | Description |
|------|-------------|
| CodeableConcept[] | Security labels applied to document |

**Confidentiality Codes:**
| Code | Display | System |
|------|---------|--------|
| N | normal | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |
| R | restricted | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |
| V | very restricted | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |
| L | low | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |
| M | moderate | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |
| U | unrestricted | http://terminology.hl7.org/CodeSystem/v3-Confidentiality |

### content (1..*)

The document content. Required element (1..*).

| Element | Type | Cardinality | Description |
|---------|------|-------------|-------------|
| attachment | Attachment | 1..1 | Where to access the document (Required) |
| profile | BackboneElement[] | 0..* | Document constraints and encoding specifications |

### content.attachment

| Element | Type | Description |
|---------|------|-------------|
| contentType | code | MIME type |
| language | code | Human language |
| data | base64Binary | Data inline |
| url | url | URL to retrieve data |
| size | unsignedInt | Size in bytes |
| hash | base64Binary | Hash of data (SHA-1) |
| title | string | Label to display |
| creation | dateTime | Date attachment was created |
| height | positiveInt | Height of the image in pixels |
| width | positiveInt | Width of the image in pixels |
| frames | positiveInt | Number of frames if > 1 (photo) |
| duration | decimal | Length in seconds (audio/video) |
| pages | positiveInt | Number of printed pages |

**Common MIME Types:**
| MIME Type | Description |
|-----------|-------------|
| application/xml | XML document |
| application/pdf | PDF document |
| text/plain | Plain text |
| text/html | HTML |
| application/hl7-v3+xml | HL7 V3 XML |
| application/fhir+json | FHIR JSON |
| application/fhir+xml | FHIR XML |

### content.format

Format of the document.

**IHE Format Codes:**
| Code | Display |
|------|---------|
| urn:hl7-org:sdwg:ccda-structuredBody:2.1 | C-CDA Structured Body 2.1 |
| urn:hl7-org:sdwg:ccda-nonXMLBody:2.1 | C-CDA Non-XML Body 2.1 |
| urn:ihe:iti:xds-sd:pdf:2008 | PDF |
| urn:ihe:iti:xds-sd:text:2008 | Plain Text |
| urn:ihe:lab:xd-lab:2008 | Lab Report |
| urn:ihe:rad:TEXT | Radiology Report |
| urn:ihe:pcc:xphr:2007 | PHR Extract |

### context (0..1)

Clinical context of document.

| Element | Type | Description |
|---------|------|-------------|
| encounter | Reference(Encounter)[] | Context of the document |
| event | CodeableConcept[] | Main clinical acts documented |
| period | Period | Time of service documented |
| facilityType | CodeableConcept | Kind of facility |
| practiceSetting | CodeableConcept | Additional details |
| sourcePatientInfo | Reference(Patient) | Patient demographics from source |
| related | Reference(Any)[] | Related resources |

## US Core Conformance Requirements

For US Core DocumentReference profile compliance:

1. **SHALL** support `identifier`
2. **SHALL** support `status`
3. **SHALL** support `type`
4. **SHALL** support `category`
5. **SHALL** support `subject`
6. **SHALL** support `date`
7. **SHALL** support `author`
8. **SHALL** support `custodian`
9. **SHALL** support `content`
10. **SHALL** support `content.attachment`
11. **SHALL** support `content.attachment.contentType`
12. **SHALL** support `content.attachment.data` or `content.attachment.url`
13. **SHALL** support `content.format`
14. **SHALL** support `context`
15. **SHALL** support `context.encounter`
16. **SHALL** support `context.period`

## Search Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| _id | token | Logical id of the resource |
| status | token | current \| superseded \| entered-in-error |
| type | token | Document type (LOINC) |
| category | token | Categorization of document |
| subject | reference | Who/what is the subject |
| patient | reference | Who is the subject (Patient) |
| date | date | When this document reference was created |
| author | reference | Who authored |
| authenticator | reference | Who authenticated |
| custodian | reference | Organization which maintains |
| description | string | Human-readable description |
| identifier | token | Master Version Specific Identifier |
| period | date | Time of service documented |
| relatesto | reference | Target of relationship |
| relation | token | replaces \| transforms \| signs \| appends |
| relationship | composite | relatesto / relation |
| security-label | token | Document security-tags |
| setting | token | Additional details about where |
| facility | token | Kind of facility |
| event | token | Main clinical acts documented |
| contenttype | token | MIME type |
| language | token | Human language |
| location | uri | URL where document is found |
| format | token | Format/content rules |
| encounter | reference | Context of the document |
| related | reference | Related resources |

## Document Type Profiles

### US Core Clinical Note Types

| LOINC Code | Display | US Core Profile |
|------------|---------|-----------------|
| 18842-5 | Discharge Summary | us-core-documentreference |
| 11488-4 | Consultation Note | us-core-documentreference |
| 11506-3 | Progress Note | us-core-documentreference |
| 28570-0 | Procedure Note | us-core-documentreference |
| 34117-2 | History and Physical | us-core-documentreference |
| 11504-8 | Operative Note | us-core-documentreference |

## Constraints and Invariants

| Constraint | Description |
|------------|-------------|
| docref-1 | facilityType only present if context is not an encounter |
| docref-2 | practiceSetting only present if context absent |

## Modifier Elements

The following elements are modifier elements:
- **status** - Changes interpretation of the document reference
- **docStatus** - Changes interpretation of the underlying document

## Compartments

The DocumentReference resource is part of the following compartments:
- Device
- Encounter
- Group
- Patient
- Practitioner
- RelatedPerson

## References

- FHIR R4B DocumentReference: https://hl7.org/fhir/R4B/documentreference.html
- US Core DocumentReference Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference
- IHE IT Infrastructure Technical Framework: https://www.ihe.net/resources/technical_frameworks/#IT
- LOINC: https://loinc.org/
