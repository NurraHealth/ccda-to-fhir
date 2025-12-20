# Missing C-CDA to FHIR Mappings

**Purpose**: Track mappings documented in `docs/mapping/` that are not yet implemented in the converter code.

**Last Updated**: 2025-12-20

---

## Status Overview

This document tracks mappings that are:
1. ✅ Fully documented with standards-compliant specifications
2. ❌ Not yet implemented in converter code
3. 🎯 Required for certification or standards compliance

**Current Status**: 1 missing mapping (0 medium priority, 1 low priority)

**Recently Completed**: Composition, Bundle, Goal, CarePlan, MedicationDispense (2025-12-19), Location, Device, DocumentReference, and CareTeam (2025-12-20)

---

## High Priority: Certification Requirements

### 1. Composition (Document Structure) ✅ **IMPLEMENTED** (2025-12-19)

**Implementation**: Fully implemented with comprehensive test coverage (50 tests passing)

**Capabilities**: C-CDA documents are now converted to proper FHIR document Bundles with Composition as the first entry. All document metadata, sections, attestations, and participant extensions are supported per C-CDA on FHIR IG.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/composition.md`
- ✅ **C-CDA Documentation**: `docs/ccda/clinical-document.md` (covers both DocumentReference and Composition mappings)
- ✅ **Mapping Specification**: `docs/mapping/19-composition.md`

#### Standards References
- **FHIR R4 Resource**: [Composition](https://hl7.org/fhir/R4/composition.html)
- **FHIR Documents**: [FHIR Document Bundle Specification](https://hl7.org/fhir/R4/documents.html)
- **C-CDA on FHIR IG**: [Document Profiles](http://hl7.org/fhir/us/ccda/)
- **C-CDA Templates**:
  - US Realm Header: `2.16.840.1.113883.10.20.22.1.1`
  - CCD: `2.16.840.1.113883.10.20.22.1.2`
  - Consultation Note: `2.16.840.1.113883.10.20.22.1.4`
  - Diagnostic Imaging Report: `2.16.840.1.113883.10.20.22.1.5`
  - Discharge Summary: `2.16.840.1.113883.10.20.22.1.8`
  - Care Plan: `2.16.840.1.113883.10.20.22.1.15`
  - And all other C-CDA document types (11 total profiles)

#### Required Implementation

The Composition resource is the foundation of FHIR documents and must be the first entry in any FHIR document Bundle.

##### Input: C-CDA ClinicalDocument

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Summarization of Episode Note"/>
  <title>Continuity of Care Document</title>
  <effectiveTime value="20200301102000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
      <patient>
        <name><given>Ellen</given><family>Ross</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750501"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name><given>Adam</given><family>Careful</family></name>
      </assignedPerson>
      <representedOrganization>
        <name>Community Health and Hospitals</name>
      </representedOrganization>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"
                displayName="Allergies and adverse reactions Document"/>
          <title>Allergies and Intolerances</title>
          <text>...</text>
          <entry>...</entry>
        </section>
      </component>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.1.1"/>
          <code code="10160-0" codeSystem="2.16.840.1.113883.6.1"
                displayName="History of Medication use Narrative"/>
          <title>Medications</title>
          <text>...</text>
          <entry>...</entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

##### Output: FHIR Document Bundle with Composition

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  },
  "timestamp": "2020-03-01T10:20:00-05:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-tt988",
      "resource": {
        "resourceType": "Composition",
        "id": "composition-tt988",
        "meta": {
          "profile": [
            "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-Continuity-of-Care-Document"
          ]
        },
        "identifier": {
          "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
          "value": "TT988"
        },
        "status": "final",
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
        "subject": {
          "reference": "Patient/patient-998991",
          "display": "Ellen Ross"
        },
        "date": "2020-03-01T10:20:00-05:00",
        "author": [
          {
            "reference": "Practitioner/practitioner-1234567890",
            "display": "Adam Careful"
          }
        ],
        "title": "Continuity of Care Document",
        "confidentiality": "N",
        "custodian": {
          "reference": "Organization/org-1393",
          "display": "Community Health and Hospitals"
        },
        "section": [
          {
            "title": "Allergies and Intolerances",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "48765-2",
                  "display": "Allergies and adverse reactions Document"
                }
              ]
            },
            "text": {
              "status": "generated",
              "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">...</div>"
            },
            "mode": "snapshot",
            "entry": [
              {
                "reference": "AllergyIntolerance/allergy-1"
              }
            ]
          },
          {
            "title": "Medications",
            "code": {
              "coding": [
                {
                  "system": "http://loinc.org",
                  "code": "10160-0",
                  "display": "History of Medication use Narrative"
                }
              ]
            },
            "text": {
              "status": "generated",
              "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">...</div>"
            },
            "mode": "snapshot",
            "entry": [
              {
                "reference": "MedicationRequest/med-1"
              }
            ]
          }
        ]
      }
    },
    {
      "fullUrl": "urn:uuid:patient-998991",
      "resource": {
        "resourceType": "Patient",
        "id": "patient-998991",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-1234567890",
      "resource": {
        "resourceType": "Practitioner",
        "id": "practitioner-1234567890",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:org-1393",
      "resource": {
        "resourceType": "Organization",
        "id": "org-1393",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:allergy-1",
      "resource": {
        "resourceType": "AllergyIntolerance",
        "id": "allergy-1",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:med-1",
      "resource": {
        "resourceType": "MedicationRequest",
        "id": "med-1",
        ...
      }
    }
  ]
}
```

#### Implementation Checklist

##### Document-Level Converter (`ccda_to_fhir/converters/composition.py`)
- [ ] Create `CompositionConverter` class
- [ ] Implement Composition resource creation from ClinicalDocument
- [ ] Map ClinicalDocument `id` → Composition.identifier (OID to URI conversion)
- [ ] Map `code` (LOINC document type) → Composition.type
- [ ] Map `title` → Composition.title
- [ ] Map `effectiveTime` → Composition.date (timestamp conversion)
- [ ] Set `status` = "final" (or infer from document context)
- [ ] Map `confidentialityCode` → Composition.confidentiality
- [ ] Map `languageCode` → Composition.language
- [ ] Map `recordTarget` → Composition.subject (reference to Patient)
- [ ] Map `componentOf/encompassingEncounter` → Composition.encounter
- [ ] Map `author` → Composition.author[] (references to Practitioner/Organization)
- [ ] Map `custodian` → Composition.custodian (reference to Organization)
- [ ] Map `legalAuthenticator` → Composition.attester[] with mode="legal"
- [ ] Map `authenticator` → Composition.attester[] with mode="professional"
- [ ] Map `relatedDocument` → Composition.relatesTo[]
- [ ] Map `documentationOf/serviceEvent` → Composition.event[]

##### Section Processing
- [ ] Map ClinicalDocument sections → Composition.section[]
- [ ] Map `section/title` → section.title
- [ ] Map `section/code` → section.code (LOINC section codes)
- [ ] Convert C-CDA narrative (`section/text`) → FHIR XHTML (`section.text.div`)
- [ ] Set `section.mode` = "snapshot" (default for most C-CDA sections)
- [ ] Map `section/entry` → section.entry[] (references to resources)
- [ ] Handle empty sections → section.emptyReason
- [ ] Handle nested sections → section.section[] (recursive)
- [ ] Map `section/author` → section.author[] (section-specific authors)

##### Narrative Text Conversion
- [ ] Convert C-CDA HL7 narrative to FHIR XHTML
- [ ] Map C-CDA `<content>` → XHTML `<span>`
- [ ] Map C-CDA `<paragraph>` → XHTML `<p>`
- [ ] Map C-CDA `<list>` → XHTML `<ul>` or `<ol>`
- [ ] Map C-CDA `<table>` → XHTML `<table>` (preserve structure)
- [ ] Map C-CDA `@ID` → XHTML `@id`
- [ ] Map C-CDA `@styleCode` → XHTML `@class` or `@style`
- [ ] Handle `<linkHtml>` → `<a>`
- [ ] Handle `<renderMultiMedia>` → `<img>`
- [ ] Set `text.status` = "generated" or "additional"

##### Bundle Assembly
- [ ] Create Bundle with type="document"
- [ ] Set Bundle.identifier from ClinicalDocument/id
- [ ] Set Bundle.timestamp from ClinicalDocument/effectiveTime
- [ ] Insert Composition as first entry
- [ ] Add Patient resource (from recordTarget)
- [ ] Add all Practitioner resources (from authors, performers)
- [ ] Add Organization resources (from custodian, author orgs)
- [ ] Add section entry resources (AllergyIntolerance, Condition, MedicationRequest, etc.)
- [ ] Assign fullUrl for each entry (UUID-based)
- [ ] Ensure all Composition references resolve within Bundle

##### Profile Selection
- [ ] Detect C-CDA document type from templateId
- [ ] Map to appropriate C-CDA on FHIR Composition profile:
  - [ ] CCD (2.16.840.1.113883.10.20.22.1.2) → CCDA-on-FHIR-Continuity-of-Care-Document
  - [ ] Consultation Note (2.16.840.1.113883.10.20.22.1.4) → CCDA-on-FHIR-Consultation-Note
  - [ ] Discharge Summary (2.16.840.1.113883.10.20.22.1.8) → CCDA-on-FHIR-Discharge-Summary
  - [ ] Diagnostic Imaging Report (2.16.840.1.113883.10.20.22.1.5) → Diagnostic-Imaging-Report
  - [ ] History and Physical (2.16.840.1.113883.10.20.22.1.1) → CCDA-on-FHIR-History-and-Physical
  - [ ] Operative Note (2.16.840.1.113883.10.20.22.1.6) → CCDA-on-FHIR-Operative-Note
  - [ ] Progress Note (2.16.840.1.113883.10.20.22.1.9) → CCDA-on-FHIR-Progress-Note
  - [ ] Procedure Note (2.16.840.1.113883.10.20.22.1.7) → CCDA-on-FHIR-Procedure-Note
  - [ ] Referral Note (2.16.840.1.113883.10.20.22.1.14) → CCDA-on-FHIR-Referral-Note
  - [ ] Transfer Summary (2.16.840.1.113883.10.20.22.1.13) → CCDA-on-FHIR-Transfer-Summary
  - [ ] Care Plan (2.16.840.1.113883.10.20.22.1.15) → Care-Plan-Document
- [ ] Set Composition.meta.profile accordingly

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add document type validators for each C-CDA document template
- [ ] Add section validators for common section templates
- [ ] Validate required elements (id, code, title, effectiveTime, etc.)

##### Tests (`tests/converters/test_composition.py`)
- [ ] Test ClinicalDocument → Composition conversion
- [ ] Test document identifier mapping (OID/UUID to URI)
- [ ] Test document type mapping (LOINC codes)
- [ ] Test status determination (final, amended, appended)
- [ ] Test subject mapping (reference to Patient)
- [ ] Test author mapping (multiple authors)
- [ ] Test custodian mapping (Organization reference)
- [ ] Test attester mapping (legalAuthenticator, authenticator)
- [ ] Test relatedDocument mapping (replaces, appends, transforms)
- [ ] Test serviceEvent mapping (event.code, event.period, event.detail)
- [ ] Test section title and code mapping
- [ ] Test section narrative conversion (C-CDA to XHTML)
- [ ] Test section entry references
- [ ] Test empty section handling (emptyReason)
- [ ] Test nested sections
- [ ] Test Bundle assembly (type, identifier, timestamp, entry order)
- [ ] Test fullUrl assignment for each entry
- [ ] Test reference resolution within Bundle

##### Integration Tests (`tests/integration/test_composition_bundle.py`)
- [ ] Test complete CCD conversion (all sections)
- [ ] Test Discharge Summary conversion
- [ ] Test Consultation Note conversion
- [ ] Test Care Plan Document conversion
- [ ] Test document with multiple authors
- [ ] Test document with legalAuthenticator
- [ ] Test document with relatedDocument (version replacement)
- [ ] Test document with serviceEvent
- [ ] Test minimal document (only required sections)
- [ ] Test document with empty sections
- [ ] Test document with nested sections
- [ ] Test Bundle structure validation
- [ ] Test all references resolve within Bundle

##### C-CDA on FHIR Conformance
- [ ] Validate Composition.identifier present (1..1)
- [ ] Validate Composition.status present (1..1)
- [ ] Validate Composition.type present (1..1) with LOINC code
- [ ] Validate Composition.subject references Patient (1..1)
- [ ] Validate Composition.date present (1..1)
- [ ] Validate Composition.author[] not empty (1..*)
- [ ] Validate Composition.title present (1..1)
- [ ] Validate Composition.custodian present (1..1 for C-CDA on FHIR)
- [ ] Validate section.title present for each section (1..1)
- [ ] Validate section.code present for each section (1..1)
- [ ] Validate section.text present if section has content
- [ ] Include correct C-CDA on FHIR profile in meta.profile

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   ├── composition.py           # CompositionConverter class
│   └── narrative_converter.py   # C-CDA narrative to FHIR XHTML converter
├── bundle/
│   └── document_bundle.py       # Document Bundle assembly
tests/
├── converters/
│   ├── test_composition.py      # Unit tests
│   └── test_narrative_converter.py  # Narrative conversion tests
└── integration/
    └── test_composition_bundle.py   # Integration tests for full document conversion
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                    # Add document and section validators
├── converter.py                 # Register CompositionConverter and document bundle creation
└── converters/__init__.py       # Export CompositionConverter
```

#### Related Documentation
- See `docs/mapping/19-composition.md` for complete mapping specification
- See `docs/fhir/composition.md` for FHIR Composition element definitions
- See `docs/ccda/clinical-document.md` for C-CDA ClinicalDocument specifications
- See `docs/mapping/00-overview.md` for general mapping guidelines

#### Notes
- **Critical Priority**: This is the foundation for all C-CDA on FHIR document conversions
- **Document Bundle**: Output must be a FHIR Bundle with type="document" and Composition as first entry
- **Composition vs DocumentReference**: Composition is for structured document conversion; DocumentReference is for document indexing/referencing
- **Section Organization**: Preserve C-CDA section structure including nesting
- **Narrative Conversion**: Requires converting C-CDA HL7 narrative block to FHIR XHTML
- **Profile Selection**: Must detect C-CDA document type and apply correct C-CDA on FHIR profile
- **Reference Resolution**: All references in Composition must resolve to resources in the Bundle
- **C-CDA on FHIR IG Compliance**: Required for certification and interoperability
- **Entry References**: Composition sections reference resources created from C-CDA section entries
- **Empty Sections**: Use emptyReason for sections with no structured entries but required by document type

---

### 2. Bundle (Document Packaging) ✅ **IMPLEMENTED** (2025-12-19)

**Implementation**: Fully implemented with standards-compliant FHIR instant handling

**Capabilities**:
- C-CDA documents packaged as FHIR R4 document Bundles
- Bundle.identifier populated from ClinicalDocument/id (OID format)
- Bundle.timestamp populated from ClinicalDocument/effectiveTime when timezone present
- Proper FHIR instant type handling (timezone required)

**Implementation Notes**:
- Bundle.timestamp requires FHIR instant type (timezone mandatory)
- When C-CDA effectiveTime lacks timezone, Bundle.timestamp is omitted (per FHIR spec, timestamp is optional 0..1)
- This approach prevents manufacturing incorrect timezone data while maintaining FHIR compliance
- 54 tests including edge cases (all passing)

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/bundle.md`
- ✅ **C-CDA Documentation**: `docs/ccda/clinical-document.md` (includes Bundle packaging overview)
- ✅ **Mapping Specification**: `docs/mapping/20-bundle.md`

#### Standards References
- **FHIR R4 Resource**: [Bundle](https://hl7.org/fhir/R4/bundle.html)
- **FHIR Documents**: [FHIR Document Bundle Specification](https://hl7.org/fhir/R4/documents.html)
- **C-CDA on FHIR IG**: [Document Profiles](http://hl7.org/fhir/us/ccda/)

#### Required Implementation

The Bundle resource is the container for FHIR documents, packaging the Composition and all referenced resources.

##### Input: C-CDA ClinicalDocument (Entire Document)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Continuity of Care Document</title>
  <effectiveTime value="20200301102000-0500"/>
  <!-- Document header elements -->
  <!-- recordTarget, author, custodian -->
  <component>
    <structuredBody>
      <!-- Document sections with entries -->
    </structuredBody>
  </component>
</ClinicalDocument>
```

##### Output: FHIR Document Bundle

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "identifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  },
  "timestamp": "2020-03-01T10:20:00-05:00",
  "entry": [
    {
      "fullUrl": "urn:uuid:composition-1",
      "resource": {
        "resourceType": "Composition",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:patient-1",
      "resource": {
        "resourceType": "Patient",
        ...
      }
    },
    {
      "fullUrl": "urn:uuid:practitioner-1",
      "resource": {
        "resourceType": "Practitioner",
        ...
      }
    }
  ]
}
```

#### Implementation Checklist

##### Core Bundle Elements
- [ ] Create Bundle with type="document"
- [ ] Set Bundle.identifier from ClinicalDocument/id
- [ ] Set Bundle.timestamp from ClinicalDocument/effectiveTime

##### Entry Assembly
- [ ] Add Composition as first entry (required - constraint bdl-11)
- [ ] Add Patient resource
- [ ] Add Practitioner/Organization resources (authors, custodian)
- [ ] Add all section entry resources
- [ ] Recursively include all referenced resources

##### fullUrl Assignment
- [ ] Assign unique fullUrl to each entry
- [ ] Use UUID-based URNs (urn:uuid:...) or OID-based URNs
- [ ] Ensure fullUrl matches resource.id
- [ ] Ensure all fullUrl values are unique

##### Reference Resolution
- [ ] Ensure all references in Composition resolve within Bundle
- [ ] Ensure all references in resources resolve within Bundle
- [ ] Verify no broken references
- [ ] Verify no external references requiring resolution

##### Validation
- [ ] Validate Bundle.type = "document"
- [ ] Validate Bundle.identifier is present
- [ ] Validate Bundle.timestamp is present
- [ ] Validate Composition is first entry
- [ ] Validate all entries have fullUrl and resource
- [ ] Validate no duplicate resources

##### Optional Features
- [ ] Support Bundle.signature for signed documents
- [ ] Support Binary resource for stylesheets

#### Implementation Complexity: HIGH

**Estimated Effort**: 2-3 weeks (dependent on Composition implementation)

**Dependencies**:
- Composition resource conversion (see #1)
- All resource-specific converters (Patient, Practitioner, etc.)
- Reference tracking and resolution system
- UUID/identifier generation system

**Key Challenges**:
1. **Resource Assembly**: Tracking all resources that need to be included
2. **Reference Resolution**: Ensuring all references resolve within Bundle
3. **Duplicate Prevention**: Avoiding duplicate resources when multiple references exist
4. **fullUrl Strategy**: Choosing appropriate fullUrl format (UUID vs OID)
5. **Recursive Inclusion**: Following reference chains to include all needed resources
6. **Circular References**: Detecting and handling circular reference chains
7. **Large Documents**: Managing memory for large documents with 100+ resources

#### Testing Requirements

##### Unit Tests
- [ ] Test Bundle creation with correct type
- [ ] Test identifier mapping from ClinicalDocument/id
- [ ] Test timestamp conversion
- [ ] Test entry ordering (Composition first)
- [ ] Test fullUrl generation strategies (UUID, OID)
- [ ] Test duplicate resource detection
- [ ] Test reference resolution within Bundle

##### Integration Tests
- [ ] Test complete document conversion (CCD)
- [ ] Test with all document types (Discharge Summary, Progress Note, etc.)
- [ ] Test with documents containing 50+ resources
- [ ] Test with circular references
- [ ] Test with missing optional elements
- [ ] Test Bundle validation against FHIR schema
- [ ] Test Bundle signature generation (optional)

##### Validation Tests
- [ ] Validate Bundle structure meets FHIR specification
- [ ] Validate all required constraints (bdl-9, bdl-10, bdl-11)
- [ ] Validate no broken references
- [ ] Validate against C-CDA on FHIR profiles
- [ ] Test with FHIR validator tool

#### Key Implementation Notes

**Bundle Assembly Process**:
1. Initialize Bundle with type="document"
2. Set identifier and timestamp from ClinicalDocument
3. Convert and add Composition as first entry
4. Convert and add all participant resources (Patient, Practitioner, Organization)
5. For each section, convert and add entry resources
6. Recursively include all referenced resources
7. Assign fullUrl to all entries
8. Validate all references resolve
9. Optionally sign Bundle

**Reference Resolution Strategy**:
- Use internal Bundle references: `"reference": "Patient/patient-123"`
- Resolution: match against `entry.fullUrl` containing the reference
- All references SHOULD resolve within Bundle (self-contained document)

**Resource Inclusion Algorithm**:
```
included = empty set
queue = [Composition]

while queue not empty:
  resource = queue.pop()
  if resource in included: continue

  included.add(resource)

  for each reference in resource:
    referenced = resolve(reference)
    if referenced not in included:
      queue.add(referenced)
```

**fullUrl Strategy**:
- **Recommended**: UUID-based URNs (`urn:uuid:...`)
- Generate UUIDs for resources without stable identifiers
- Use UUID v5 (name-based) for reproducibility if needed
- Ensure uniqueness across all Bundle entries

**Immutability**:
- Once assembled, Bundle content cannot change
- Bundle.identifier never reused
- New version requires new Bundle with new identifier
- Use Composition.relatesTo to link versions

---

### 3. CarePlan ✅ **IMPLEMENTED** (2025-12-19)

**Implementation**: Basic CarePlan resource creation for Care Plan Documents is now functional. The converter creates CarePlan resources with US Core CarePlan profile compliance, including required fields (status, intent, category, subject) and support for goals references.

**Note**: Health Concerns, Interventions, and Outcomes sections are not yet fully implemented. Future enhancements needed for complete Care Plan Document support.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/careplan.md`
- ✅ **C-CDA Documentation**: `docs/ccda/care-plan-document.md`
- ✅ **Mapping Specification**: `docs/mapping/14-careplan.md`

#### Standards References
- **US Core Profile**: [US Core CarePlan Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan)
- **C-CDA on FHIR Profile**: [Care Plan Document v1.2.0](https://hl7.org/fhir/us/ccda/StructureDefinition-Care-Plan-Document.html)
- **C-CDA Template**:
  - Care Plan Document: `2.16.840.1.113883.10.20.22.1.15` (LOINC `52521-2`)
  - Health Concerns Section: `2.16.840.1.113883.10.20.22.2.58` (LOINC `75310-3`)
  - Goals Section: `2.16.840.1.113883.10.20.22.2.60` (LOINC `61146-7`)
  - Interventions Section: `2.16.840.1.113883.10.20.21.2.3` (LOINC `62387-6`)
  - Outcomes Section: `2.16.840.1.113883.10.20.22.2.61` (LOINC `11383-7`)

#### Required Implementation

The Care Plan Document requires **dual resource mapping**:
1. **Composition** resource (C-CDA on FHIR Care Plan Document profile)
2. **CarePlan** resource (US Core CarePlan profile)

##### Input: C-CDA Care Plan Document

```xml
<ClinicalDocument>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>

  <recordTarget><!-- Patient information --></recordTarget>
  <author><!-- Care plan author --></author>
  <custodian><!-- Organization --></custodian>

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <!-- REQUIRED: Health Concerns Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
          <!-- Contains Health Concern Act entries -->
        </section>
      </component>

      <!-- REQUIRED: Goals Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"/>
          <!-- Contains Goal Observation entries -->
        </section>
      </component>

      <!-- SHOULD: Interventions Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"/>
          <!-- Contains Intervention Act entries -->
        </section>
      </component>

      <!-- SHOULD: Outcomes Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
          <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"/>
          <!-- Contains Outcome Observation entries -->
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
```

##### Output: FHIR Bundle with Composition + CarePlan

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [
    {
      "resource": {
        "resourceType": "Composition",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document"]
        },
        "identifier": [{"value": "urn:uuid:careplan-12345"}],
        "status": "final",
        "type": {
          "coding": [{
            "system": "http://loinc.org",
            "code": "52521-2",
            "display": "Overall plan of care/advance care directives"
          }]
        },
        "subject": {"reference": "Patient/patient-123"},
        "date": "2024-01-15T12:00:00-05:00",
        "author": [{"reference": "Practitioner/provider-123"}],
        "title": "Care Plan",
        "custodian": {"reference": "Organization/hospital-123"},
        "event": [{
          "period": {"start": "2024-01-15", "end": "2024-04-15"},
          "detail": [{"reference": "CarePlan/careplan-1"}]
        }],
        "section": [
          {
            "title": "HEALTH CONCERNS",
            "code": {"coding": [{"system": "http://loinc.org", "code": "75310-3"}]},
            "entry": [{"reference": "Condition/concern-1"}]
          },
          {
            "title": "GOALS",
            "code": {"coding": [{"system": "http://loinc.org", "code": "61146-7"}]},
            "entry": [{"reference": "Goal/goal-1"}]
          },
          {
            "title": "INTERVENTIONS",
            "code": {"coding": [{"system": "http://loinc.org", "code": "62387-6"}]},
            "entry": [{"reference": "ServiceRequest/intervention-1"}]
          },
          {
            "title": "OUTCOMES",
            "code": {"coding": [{"system": "http://loinc.org", "code": "11383-7"}]},
            "entry": [{"reference": "Observation/outcome-1"}]
          }
        ]
      }
    },
    {
      "resource": {
        "resourceType": "CarePlan",
        "meta": {
          "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan"]
        },
        "text": {
          "status": "additional",
          "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><h3>Assessment</h3><p>Patient concerns and conditions.</p><h3>Plan</h3><p>Goals and planned interventions.</p></div>"
        },
        "identifier": [{"value": "urn:uuid:careplan-12345"}],
        "status": "active",
        "intent": "plan",
        "category": [{
          "coding": [{
            "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
            "code": "assess-plan"
          }]
        }],
        "subject": {"reference": "Patient/patient-123"},
        "period": {"start": "2024-01-15", "end": "2024-04-15"},
        "author": {"reference": "Practitioner/provider-123"},
        "contributor": [{"reference": "Practitioner/provider-123"}],
        "addresses": [{"reference": "Condition/concern-1"}],
        "goal": [{"reference": "Goal/goal-1"}],
        "activity": [{
          "reference": {"reference": "ServiceRequest/intervention-1"},
          "outcomeReference": [{"reference": "Observation/outcome-1"}]
        }]
      }
    }
  ]
}
```

#### Implementation Checklist

##### Document-Level Converter (`ccda_to_fhir/converters/care_plan_document.py`)
- [ ] Create `CarePlanDocumentConverter` class
- [ ] Implement dual resource creation (Composition + CarePlan)
- [ ] Map ClinicalDocument header → Composition metadata
- [ ] Map ClinicalDocument `id` → Composition.identifier + CarePlan.identifier
- [ ] Map `code` (52521-2) → Composition.type
- [ ] Map `title` → Composition.title
- [ ] Map `effectiveTime` → Composition.date
- [ ] Map `confidentialityCode` → Composition.confidentiality
- [ ] Map `languageCode` → Composition.language
- [ ] Map `setId` and `versionNumber` → Composition.identifier
- [ ] Map `recordTarget` → Composition.subject + CarePlan.subject
- [ ] Map `author` → Composition.author + CarePlan.author + CarePlan.contributor
- [ ] Map `custodian` → Composition.custodian
- [ ] Map serviceEvent `effectiveTime` → Composition.event.period + CarePlan.period
- [ ] Set CarePlan.intent = "plan" (fixed)
- [ ] Set CarePlan.category = "assess-plan" (fixed)
- [ ] Set CarePlan.status based on document and intervention status

##### Composition Section Processing
- [ ] Process Health Concerns Section → Composition.section + Condition resources
- [ ] Process Goals Section → Composition.section + Goal resources
- [ ] Process Interventions Section → Composition.section + ServiceRequest/Procedure
- [ ] Process Outcomes Section → Composition.section + Observation resources
- [ ] Link Composition sections to corresponding resources
- [ ] Generate section narratives from C-CDA text elements

##### CarePlan Content Mapping
- [ ] Map Health Concerns → CarePlan.addresses (Condition references)
- [ ] Map Goals → CarePlan.goal (Goal references)
- [ ] Map Interventions → CarePlan.activity.reference
- [ ] Map Intervention moodCode=INT → ServiceRequest (intent="plan")
- [ ] Map Intervention moodCode=EVN → Procedure (status="completed")
- [ ] Map Outcomes → CarePlan.activity.outcomeReference
- [ ] Link outcomes to goals via entryRelationship typeCode="GEVL"

##### Narrative Generation (`CarePlan.text`)
- [ ] Aggregate narratives from all sections
- [ ] Create Assessment section from Health Concerns
- [ ] Create Plan section from Goals + Interventions
- [ ] Format as XHTML div
- [ ] Set text.status = "additional"

##### Section Processors
- [ ] `HealthConcernsSectionProcessor` for Health Concerns Section
- [ ] `GoalsSectionProcessor` for Goals Section (reuse from Goal implementation)
- [ ] `InterventionsSectionProcessor` for Interventions Section
- [ ] `OutcomesSectionProcessor` for Outcomes Section

##### Bundle Assembly
- [ ] Create FHIR Document Bundle (type="document")
- [ ] Add Composition as first entry
- [ ] Add CarePlan resource
- [ ] Add all referenced resources (Patient, Practitioner, Organization, Condition, Goal, ServiceRequest, Procedure, Observation)
- [ ] Ensure all references are resolvable within bundle
- [ ] Assign fullUrl for each resource

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_care_plan_document()` validator for template `2.16.840.1.113883.10.20.22.1.15`
- [ ] Add `is_health_concerns_section()` validator for template `2.16.840.1.113883.10.20.22.2.58`
- [ ] Add `is_interventions_section()` validator for template `2.16.840.1.113883.10.20.21.2.3`
- [ ] Add `is_outcomes_section()` validator for template `2.16.840.1.113883.10.20.22.2.61`
- [ ] Validate required sections present

##### Tests (`tests/converters/test_care_plan_document.py`)
- [ ] Test Care Plan Document → Composition conversion
- [ ] Test Care Plan Document → CarePlan conversion
- [ ] Test dual resource creation in bundle
- [ ] Test Health Concerns Section mapping
- [ ] Test Goals Section mapping
- [ ] Test Interventions Section mapping (planned vs completed)
- [ ] Test Outcomes Section mapping
- [ ] Test Composition.event.detail links to CarePlan
- [ ] Test CarePlan.addresses links to Conditions
- [ ] Test CarePlan.goal links to Goals
- [ ] Test CarePlan.activity links to interventions
- [ ] Test CarePlan.activity.outcomeReference links to outcomes
- [ ] Test narrative generation from sections
- [ ] Test status mapping (active, completed, etc.)
- [ ] Test contributor mapping (multiple authors)
- [ ] Test empty sections with nullFlavor
- [ ] Test document versioning (setId, versionNumber)

##### Integration Tests (`tests/integration/test_care_plan_document.py`)
- [ ] Test complete Care Plan Document with all sections
- [ ] Test minimal Care Plan Document (only required sections)
- [ ] Test document with multiple authors
- [ ] Test document with patient as participant
- [ ] Test longitudinal care plan (multiple versions)
- [ ] Test bundle structure and reference resolution

##### US Core Conformance
- [ ] Validate Composition.type = 52521-2
- [ ] Validate required sections (Health Concerns, Goals)
- [ ] Validate section.entry references
- [ ] Validate CarePlan.status, intent, category, subject
- [ ] Validate CarePlan.text.status and text.div
- [ ] Validate CarePlan.contributor (USCDI requirement)
- [ ] Include US Core CarePlan profile in meta.profile
- [ ] Include C-CDA on FHIR Care Plan Document profile in meta.profile

##### C-CDA on FHIR Conformance
- [ ] Validate all required Composition elements
- [ ] Validate section codes (LOINC)
- [ ] Validate section.entry types match allowed resources
- [ ] Handle optional sections (Interventions, Outcomes)
- [ ] Prohibit Plan of Treatment Section in Care Plan

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── care_plan_document.py    # CarePlanDocumentConverter class
├── sections/
│   ├── health_concerns_section.py  # HealthConcernsSectionProcessor
│   ├── interventions_section.py    # InterventionsSectionProcessor
│   └── outcomes_section.py         # OutcomesSectionProcessor
tests/
├── converters/
│   └── test_care_plan_document.py  # Unit tests
└── integration/
    └── test_care_plan_document.py  # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                    # Add validators
├── converter.py                 # Register CarePlanDocumentConverter
└── sections/__init__.py         # Export section processors
```

#### Related Documentation
- See `docs/mapping/14-careplan.md` for complete mapping specification
- See `docs/fhir/careplan.md` for FHIR CarePlan element definitions
- See `docs/ccda/care-plan-document.md` for C-CDA template specifications
- See `docs/mapping/13-goal.md` for Goal mapping (required for Goals Section)
- See `docs/mapping/02-condition.md` for Condition mapping (required for Health Concerns)

#### Notes
- **Dual Resource Mapping**: Unlike other document types, Care Plan requires creating BOTH Composition and CarePlan resources
- **Document Bundle**: Output is a FHIR Document Bundle (type="document") with Composition as first entry
- **Section Processing**: Each section (Health Concerns, Goals, Interventions, Outcomes) creates corresponding FHIR resources
- **Reference Resolution**: Composition sections reference resources, CarePlan also references same resources for addresses, goal, activity
- **Narrative Aggregation**: CarePlan.text aggregates assessment/plan narrative from all sections
- **Status Logic**: CarePlan.status derived from intervention statuses and document context
- **Contributor vs Author**: Map all authors to contributor; first author maps to author
- **Intervention MoodCode**: INT (intent) → ServiceRequest, EVN (event) → Procedure
- **Certification**: ONC certification requires Interventions and Outcomes sections

---

### 4. Goal ✅ **IMPLEMENTED** (2025-12-19)

**Implementation**: Fully implemented with basic test coverage.

**Capabilities**: C-CDA Goal Observations are now converted to FHIR Goal resources per US Core Goal Profile. Supports goal description, lifecycle status, start dates, targets (quantity, range, coded values), expressedBy (patient/practitioner), priority, achievement status, and addresses (health concerns). Component goals with multiple targets are supported.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/goal.md`
- ✅ **C-CDA Documentation**: `docs/ccda/goals-section.md`
- ✅ **Mapping Specification**: `docs/mapping/13-goal.md`

#### Standards References
- **US Core Profile**: [US Core Goal Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal)
- **C-CDA Templates**:
  - Goals Section: `2.16.840.1.113883.10.20.22.2.60` (LOINC `61146-7`)
  - Goal Observation: `2.16.840.1.113883.10.20.22.4.121`
- **C-CDA on FHIR IG**: Not yet published (noted as absent from v2.0.0)

#### Required Implementation

##### Input: C-CDA Goal Observation
```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
  <code code="61146-7" codeSystem="2.16.840.1.113883.6.1" displayName="Goals"/>
  <entry typeCode="DRIV">
    <observation classCode="OBS" moodCode="GOL">
      <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
      <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
      <code code="289169006" codeSystem="2.16.840.1.113883.6.96"
            displayName="Weight loss"/>
      <statusCode code="active"/>
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240715"/>
      </effectiveTime>
      <author>
        <time value="20240115"/>
        <assignedAuthor>
          <id root="patient-system" extension="patient-123"/>
        </assignedAuthor>
      </author>
      <!-- Target value -->
      <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
          <code code="29463-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Body weight"/>
          <value xsi:type="PQ" value="160" unit="[lb_av]"/>
        </observation>
      </entryRelationship>
    </observation>
  </entry>
</section>
```

##### Output: FHIR Goal Resource
```json
{
  "resourceType": "Goal",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
  }],
  "lifecycleStatus": "active",
  "description": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "289169006",
      "display": "Weight loss"
    }]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "startDate": "2024-01-15",
  "target": [{
    "measure": {
      "coding": [{
        "system": "http://loinc.org",
        "code": "29463-7",
        "display": "Body weight"
      }]
    },
    "detailQuantity": {
      "value": 160,
      "unit": "lb",
      "system": "http://unitsofmeasure.org",
      "code": "[lb_av]"
    },
    "dueDate": "2024-07-15"
  }],
  "expressedBy": {
    "reference": "Patient/patient-123"
  }
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/goal.py`)
- [ ] Create `GoalConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Goal Observation
- [ ] Map `id` → `Goal.identifier`
- [ ] Map `code` → `Goal.description` (CodeableConcept)
- [ ] Map `statusCode` → `Goal.lifecycleStatus` per ConceptMap
- [ ] Map `effectiveTime/low` → `Goal.startDate` (date conversion)
- [ ] Map `effectiveTime/high` → `Goal.target.dueDate` (date conversion)
- [ ] Map `author` → `Goal.expressedBy` (Reference to Patient or Practitioner)
- [ ] Extract patient reference from document `recordTarget` → `Goal.subject`

##### Component Goals / Targets (`target` array)
- [ ] Parse component Goal Observations (entryRelationship typeCode="COMP")
- [ ] Map component `code` → `target.measure`
- [ ] Map component `value` by type:
  - [ ] PQ (Physical Quantity) → `detailQuantity`
  - [ ] IVL_PQ (Interval) → `detailRange`
  - [ ] CD (Concept Descriptor) → `detailCodeableConcept`
  - [ ] ST (String) → `detailString`
  - [ ] BL (Boolean) → `detailBoolean`
  - [ ] INT (Integer) → `detailInteger`
  - [ ] RTO (Ratio) → `detailRatio`

##### Optional Elements
- [ ] Parse Priority Preference (template `2.16.840.1.113883.10.20.22.4.143`) → `Goal.priority`
- [ ] Parse Progress Toward Goal (template `2.16.840.1.113883.10.20.22.4.110`) → `Goal.achievementStatus`
- [ ] Parse Entry Reference (template `2.16.840.1.113883.10.20.22.4.122`) → `Goal.addresses`

##### Section Processing (`ccda_to_fhir/sections/goal_section.py`)
- [ ] Create `GoalSectionProcessor` class
- [ ] Identify Goals Section by template ID `2.16.840.1.113883.10.20.22.2.60`
- [ ] Extract Goal Observation entries (moodCode="GOL")
- [ ] Call `GoalConverter` for each observation
- [ ] Store Goal resources in result bundle

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_goal_observation()` validator for template `2.16.840.1.113883.10.20.22.4.121`
- [ ] Validate required elements: id, code, statusCode, moodCode="GOL"

##### Value Set Mappings
- [ ] Implement lifecycle status ConceptMap:
  - `active` → `active`
  - `completed` → `completed`
  - `cancelled` → `cancelled`
  - `suspended` → `on-hold`
  - `aborted` → `cancelled`
- [ ] Implement achievement status mapping (FHIR CodeSystem direct use)
- [ ] Implement priority mapping (FHIR CodeSystem direct use)

##### Tests (`tests/converters/test_goal.py`)
- [ ] Test basic Goal Observation → Goal conversion
- [ ] Test `lifecycleStatus` mapping for all status codes
- [ ] Test `description` mapping with SNOMED/LOINC codes
- [ ] Test `startDate` from effectiveTime/low
- [ ] Test `target.dueDate` from effectiveTime/high
- [ ] Test `expressedBy` mapping (patient vs provider)
- [ ] Test component goal mapping (quantity, range, coded values)
- [ ] Test priority preference mapping
- [ ] Test achievement status mapping
- [ ] Test health concern reference (addresses)
- [ ] Test missing effectiveTime handling
- [ ] Test qualitative goals (no targets)
- [ ] Test SDOH goals
- [ ] Test multiple component targets (e.g., blood pressure)
- [ ] Test negotiated goals (multiple authors)

##### Integration Tests (`tests/integration/test_goal_section.py`)
- [ ] Test Goals Section extraction
- [ ] Test multiple goals in one section
- [ ] Test goal with all optional elements
- [ ] Test complete Care Plan document with goals

##### US Core Conformance
- [ ] Validate required elements: `lifecycleStatus`, `description`, `subject`
- [ ] Validate Must Support: at least one of `startDate` OR `target.dueDate`
- [ ] Validate Must Support: `expressedBy`
- [ ] Include US Core Goal profile in `meta.profile`

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── goal.py              # GoalConverter class
├── sections/
│   └── goal_section.py      # GoalSectionProcessor class
tests/
├── converters/
│   └── test_goal.py         # Unit tests
└── integration/
    └── test_goal_section.py # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                # Add is_goal_observation() validator
├── converter.py             # Register GoalSectionProcessor
└── sections/__init__.py     # Export GoalSectionProcessor
```

#### Related Documentation
- See `docs/mapping/13-goal.md` for complete element mappings
- See `docs/fhir/goal.md` for FHIR Goal element definitions
- See `docs/ccda/goals-section.md` for C-CDA template specifications

#### Notes
- **moodCode Validation**: CRITICAL - Only process observations with `moodCode="GOL"` (goal mood, not event mood)
- **Patient Reference**: Extract from document-level `recordTarget` since goals don't have inline subject
- **Multiple Authors**: For negotiated goals with multiple authors, map first to `expressedBy` and consider Provenance resource for others
- **Missing Target**: Valid to have goals without measurable targets (qualitative goals)
- **SDOH Categories**: Infer category from goal code when applicable (housing, employment, etc.)

---

### 5. MedicationDispense ✅ **IMPLEMENTED** (2025-12-19)

**Implementation**: Fully implemented with comprehensive test coverage (19 unit tests passing). Supports all required mappings including status, timing, type inference, performer, and quantity mappings per US Core MedicationDispense profile.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/medication-dispense.md`
- ✅ **C-CDA Documentation**: `docs/ccda/medication-dispense.md`
- ✅ **Mapping Specification**: `docs/mapping/15-medication-dispense.md`

#### Standards References
- **US Core Profile**: [US Core MedicationDispense Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense)
- **C-CDA Template**: Medication Dispense (`2.16.840.1.113883.10.20.22.4.18`)
- **C-CDA on FHIR IG**: Not yet published (noted as absent from v2.0.0)

#### Required Implementation

MedicationDispense captures the actual supply provision of medication to a patient, including when, where, and by whom it was dispensed.

##### Input: C-CDA Medication Dispense

```xml
<entryRelationship typeCode="REFR">
  <supply classCode="SPLY" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
    <id root="dispense-456"/>
    <statusCode code="completed"/>
    <effectiveTime value="20200301143000-0500"/>
    <repeatNumber value="1"/>
    <quantity value="30" unit="{tbl}"/>
    <product>
      <manufacturedProduct classCode="MANU">
        <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
        <manufacturedMaterial>
          <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                displayName="Lisinopril 10 MG Oral Tablet"/>
        </manufacturedMaterial>
      </manufacturedProduct>
    </product>
    <performer>
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
        <representedOrganization>
          <name>Community Pharmacy</name>
        </representedOrganization>
      </assignedEntity>
    </performer>
  </supply>
</entryRelationship>
```

##### Output: FHIR MedicationDispense Resource

```json
{
  "resourceType": "MedicationDispense",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:oid:dispense-456"
  }],
  "status": "completed",
  "category": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
      "code": "community",
      "display": "Community"
    }]
  },
  "medicationCodeableConcept": {
    "coding": [{
      "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
      "code": "314076",
      "display": "Lisinopril 10 MG Oral Tablet"
    }]
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "performer": [{
    "actor": {
      "reference": "Organization/pharmacy-1",
      "display": "Community Pharmacy"
    }
  }],
  "authorizingPrescription": [{
    "reference": "MedicationRequest/parent-medication-activity"
  }],
  "type": {
    "coding": [{
      "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
      "code": "FF",
      "display": "First Fill"
    }]
  },
  "quantity": {
    "value": 30,
    "unit": "tablet",
    "system": "http://unitsofmeasure.org",
    "code": "{tbl}"
  },
  "whenHandedOver": "2020-03-01T14:30:00-05:00"
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/medication_dispense.py`)
- [ ] Create `MedicationDispenseConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Medication Dispense supply element
- [ ] Map `id` → `MedicationDispense.identifier`
- [ ] Map `statusCode` → `MedicationDispense.status` per ConceptMap
- [ ] Map `effectiveTime` → `whenHandedOver` (single value) or `whenPrepared`/`whenHandedOver` (IVL_TS)
- [ ] Map `repeatNumber` → `type` (infer FF for value=1, RF for value>1)
- [ ] Map `quantity` → `MedicationDispense.quantity`
- [ ] Map `product/manufacturedMaterial/code` → `medicationCodeableConcept`
- [ ] Extract patient reference from document `recordTarget` → `subject`
- [ ] Map `performer` → `performer.actor` (Organization or Practitioner)
- [ ] Map `author` → Additional `performer` entry with function="packager"
- [ ] Link to parent Medication Activity → `authorizingPrescription`

##### Days Supply Processing
- [ ] Detect nested Days Supply template (`2.16.840.1.113883.10.20.37.3.10`)
- [ ] Map Days Supply `quantity` → `daysSupply`
- [ ] Calculate days supply if not present (quantity / daily dose)

##### Category Inference
- [ ] Infer category from performer organization type
- [ ] Default to "community" for retail pharmacy
- [ ] Use "inpatient" for hospital pharmacy
- [ ] Use "discharge" for discharge summaries

##### Substitution Detection
- [ ] Compare dispense product code with parent Medication Activity code
- [ ] If codes differ, set `substitution.wasSubstituted = true`
- [ ] Infer substitution type (brand vs generic, equivalent, etc.)

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_medication_dispense()` validator for template `2.16.840.1.113883.10.20.22.4.18`
- [ ] Validate `moodCode = "EVN"` (event, not intent)
- [ ] Validate required elements: id, statusCode, product

##### Resource Creation
- [ ] Create Practitioner resource for pharmacist (from author or performer)
- [ ] Create Organization resource for pharmacy (from performer)
- [ ] Create Location resource for pharmacy location (from performer address)
- [ ] Link MedicationDispense to parent MedicationRequest via authorizingPrescription

##### Tests (`tests/converters/test_medication_dispense.py`)
- [ ] Test basic Medication Dispense → MedicationDispense conversion
- [ ] Test status mapping for all status codes
- [ ] Test medication code mapping (RxNorm, NDC)
- [ ] Test timing mapping (single timestamp and IVL_TS period)
- [ ] Test repeatNumber → type inference (first fill vs refills)
- [ ] Test quantity mapping with various units
- [ ] Test days supply mapping (nested template)
- [ ] Test performer mapping (pharmacy organization)
- [ ] Test author mapping (pharmacist)
- [ ] Test substitution detection (different codes)
- [ ] Test missing effectiveTime handling
- [ ] Test category inference from context
- [ ] Test authorizingPrescription linking

##### Integration Tests (`tests/integration/test_medication_dispense.py`)
- [ ] Test complete Medication Activity with dispense events
- [ ] Test multiple dispenses (original + refills)
- [ ] Test dispense without parent activity
- [ ] Test dispense with days supply
- [ ] Test dispense with substitution

##### US Core Conformance
- [ ] Validate required elements: `status`, `medication[x]`, `subject`, `performer.actor`
- [ ] Validate conditional requirement: `whenHandedOver` present if status='completed'
- [ ] Validate Must Support: `context`, `authorizingPrescription`, `type`, `quantity`
- [ ] Include US Core MedicationDispense profile in `meta.profile`

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── medication_dispense.py    # MedicationDispenseConverter class
tests/
├── converters/
│   └── test_medication_dispense.py  # Unit tests
└── integration/
    └── test_medication_dispense.py  # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                    # Add is_medication_dispense() validator
├── converter.py                 # Register MedicationDispenseConverter
└── converters/__init__.py       # Export MedicationDispenseConverter
```

#### Related Documentation
- See `docs/mapping/15-medication-dispense.md` for complete mapping specification
- See `docs/fhir/medication-dispense.md` for FHIR MedicationDispense element definitions
- See `docs/ccda/medication-dispense.md` for C-CDA template specifications
- See `docs/mapping/07-medication-request.md` for MedicationRequest mapping (parent relationship)

#### Notes
- **Parent Relationship**: MedicationDispense is nested within Medication Activity (which maps to MedicationRequest)
- **moodCode Validation**: CRITICAL - Only process supply elements with `moodCode="EVN"` (event, not intent)
- **Medication Supply Order vs Dispense**: Template `2.16.840.1.113883.10.20.22.4.17` (moodCode=INT) is the order/prescription, while `2.16.840.1.113883.10.20.22.4.18` (moodCode=EVN) is the actual dispense
- **repeatNumber Semantics**: In dispense context, represents fill number (1=first, 2=first refill), NOT total fills allowed
- **Missing in C-CDA on FHIR IG**: The official IG notes "moodCode=EVN means dispense, which is not documented here" - this implementation fills that gap
- **Multiple Dispenses**: A single Medication Activity may have multiple dispense events (refills)
- **Substitution Detection**: Compare dispense product code with parent activity code to detect substitutions
- **Category Inference**: C-CDA lacks explicit category; infer from performer type and document context
- **Days Supply**: Optional nested template or calculate from quantity and dosage

---

### 6. Location ✅ **IMPLEMENTED** (2025-12-20)

**Implementation**: Fully implemented with comprehensive test coverage (32 unit tests passing)

**Capabilities**: Service Delivery Location participants from Encounters are now converted to separate FHIR Location resources with deduplication by NPI or name+city. Locations are registered in the reference registry and added to document bundles. Supports all identifier types (NPI, CLIA, NAIC), facility type codes (HSLOC, SNOMED CT, CMS POS), addresses, and telecom information per US Core Location profile.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/location.md`
- ✅ **C-CDA Documentation**: `docs/ccda/service-delivery-location.md`
- ✅ **Mapping Specification**: `docs/mapping/16-location.md`

#### Standards References
- **US Core Profile**: [US Core Location Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-location)
- **C-CDA Templates**:
  - Service Delivery Location: `2.16.840.1.113883.10.20.22.4.32`
  - Used in: Encounter Activity (participant[@typeCode='LOC'])
  - Also in: Procedure Activity, Planned Encounter
  - Header: encompassingEncounter/location/healthCareFacility
- **C-CDA on FHIR IG**: Mentioned in Encounter mappings but no dedicated Location mapping published

#### Required Implementation

Location represents physical places where services are provided. Unlike the current approach of embedding location details within Encounter, the standard approach is to create separate Location resources that are referenced by Encounter, Procedure, Immunization, and other resources.

##### Input: C-CDA Service Delivery Location

```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <templateId root="2.16.840.1.113883.10.20.22.4.32"/>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <code code="1061-3" codeSystem="2.16.840.1.113883.6.259"
          displayName="Hospital">
      <translation code="22232009" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Hospital"/>
    </code>
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

##### Output: FHIR Location Resource

```json
{
  "resourceType": "Location",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"]
  },
  "identifier": [{
    "system": "http://hl7.org/fhir/sid/us-npi",
    "value": "1234567890"
  }],
  "status": "active",
  "name": "Community Health and Hospitals",
  "mode": "instance",
  "type": [{
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
  }],
  "telecom": [{
    "system": "phone",
    "value": "+1(555)555-5000",
    "use": "work"
  }],
  "address": {
    "use": "work",
    "line": ["1001 Village Avenue"],
    "city": "Portland",
    "state": "OR",
    "postalCode": "99123"
  },
  "managingOrganization": {
    "reference": "Organization/org-hospital"
  }
}
```

##### Encounter Reference to Location

```json
{
  "resourceType": "Encounter",
  "location": [{
    "location": {
      "reference": "Location/location-npi-1234567890",
      "display": "Community Health and Hospitals"
    },
    "status": "completed"
  }]
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/location.py`)
- [ ] Create `LocationConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Service Delivery Location participantRole
- [ ] Map `id` → `Location.identifier` with OID to URI conversion
- [ ] Map NPI (`root='2.16.840.1.113883.4.6'`) → system `http://hl7.org/fhir/sid/us-npi`
- [ ] Map CLIA (`root='2.16.840.1.113883.4.7'`) → system `urn:oid:2.16.840.1.113883.4.7`
- [ ] Map NAIC (`root='2.16.840.1.113883.6.300'`) → system `urn:oid:2.16.840.1.113883.6.300`
- [ ] Map `code` → `Location.type` (CodeableConcept with all translations)
- [ ] Map HSLOC codes (`codeSystem='2.16.840.1.113883.6.259'`) to HSLOC system URI
- [ ] Map SNOMED CT codes (`codeSystem='2.16.840.1.113883.6.96'`) to SNOMED system URI
- [ ] Map RoleCode (`codeSystem='2.16.840.1.113883.5.111'`) to v3-RoleCode system URI
- [ ] Map `playingEntity/name` → `Location.name` (Required)
- [ ] Map `addr` → `Location.address` (USRealmAddress to FHIR Address)
- [ ] Map address `@use` codes (HP→home, WP→work, TMP→temp)
- [ ] Map `telecom` → `Location.telecom` array
- [ ] Parse telecom URI schemes (tel:, mailto:, fax:, http:) to FHIR system codes
- [ ] Set `status` = "active" (default)
- [ ] Set `mode` = "instance" (default for specific locations)
- [ ] Infer `physicalType` from location type code when confident

##### Location Deduplication
- [ ] Implement location registry to track created locations
- [ ] Deduplicate by NPI identifier match
- [ ] Deduplicate by name + city/state match
- [ ] Generate consistent Location IDs for duplicate facilities
- [ ] Use NPI-based ID when available: `"location-npi-{extension}"`
- [ ] Use name-based hash for locations without identifiers
- [ ] Return reference to existing Location resource for duplicates

##### encompassingEncounter/location Support
- [ ] Extract location from `componentOf/encompassingEncounter/location/healthCareFacility`
- [ ] Map `healthCareFacility/id` → `identifier`
- [ ] Map `healthCareFacility/code` → `type`
- [ ] Map `healthCareFacility/location/name` → `name`
- [ ] Map `healthCareFacility/location/addr` → `address`
- [ ] Map `serviceProviderOrganization` → `managingOrganization` reference
- [ ] Handle absence of template ID (healthCareFacility doesn't use template 4.32)

##### Organization Linking
- [ ] Extract managing organization from encounter `serviceProvider`
- [ ] Fallback to document `custodian` if no serviceProvider
- [ ] Create or reference Organization resource
- [ ] Set `Location.managingOrganization` reference

##### Section Processing
- [ ] Update `EncounterActivityConverter` to call `LocationConverter`
- [ ] Update `ProcedureActivityConverter` to call `LocationConverter`
- [ ] Extract location from `participant[@typeCode='LOC']/participantRole`
- [ ] Store Location resource in bundle
- [ ] Update Encounter.location to reference Location resource (not embed)

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_service_delivery_location()` validator for template `2.16.840.1.113883.10.20.22.4.32`
- [ ] Validate `participantRole/@classCode='SDLOC'`
- [ ] Validate `playingEntity/@classCode='PLC'`
- [ ] Validate required elements: code (1..1), playingEntity/name (1..1)

##### Tests (`tests/converters/test_location.py`)
- [ ] Test basic Service Delivery Location → Location conversion
- [ ] Test identifier mapping (NPI, CLIA, NAIC)
- [ ] Test OID to URI system conversion
- [ ] Test facility type mapping (HSLOC, SNOMED CT, RoleCode)
- [ ] Test translation codes (multiple code systems in one type)
- [ ] Test name mapping (required element)
- [ ] Test address mapping with multiple street lines
- [ ] Test address use code mapping (HP, WP, TMP, BAD)
- [ ] Test telecom mapping with various URI schemes
- [ ] Test telecom use code mapping
- [ ] Test location deduplication (NPI match, name+city match)
- [ ] Test Location ID generation strategies
- [ ] Test patient's home location (nullFlavor on id)
- [ ] Test ambulance/mobile location
- [ ] Test encompassingEncounter/location conversion
- [ ] Test managing organization linking
- [ ] Test physicalType inference
- [ ] Test missing optional elements handling

##### Integration Tests (`tests/integration/test_location.py`)
- [ ] Test complete encounter with location extraction
- [ ] Test multiple encounters sharing same location (deduplication)
- [ ] Test procedure with location
- [ ] Test document header encompassingEncounter location
- [ ] Test location without identifiers
- [ ] Test location with all optional elements
- [ ] Test Encounter.location reference to Location resource

##### US Core Conformance
- [ ] Validate required element: `name` (1..1)
- [ ] Validate Must Support: `identifier` (0..*)
- [ ] Validate Must Support: `status` (0..1)
- [ ] Validate Must Support: `type` (0..*)
- [ ] Validate Must Support: `telecom` (0..*)
- [ ] Validate Must Support: `address` (0..1)
- [ ] Validate Must Support: `address.line`, `address.city`, `address.state`, `address.postalCode`
- [ ] Validate Must Support: `managingOrganization` (0..1)
- [ ] Include US Core Location profile in `meta.profile`

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── location.py              # LocationConverter class
tests/
├── converters/
│   └── test_location.py         # Unit tests
└── integration/
    └── test_location.py         # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                    # Add is_service_delivery_location() validator
├── converters/
│   ├── encounter.py             # Update to create Location resources
│   ├── procedure.py             # Update to create Location resources
│   └── __init__.py              # Export LocationConverter
```

#### Related Documentation
- See `docs/mapping/16-location.md` for complete mapping specification
- See `docs/fhir/location.md` for FHIR Location element definitions
- See `docs/ccda/service-delivery-location.md` for C-CDA template specifications
- See `docs/mapping/08-encounter.md` for Encounter location reference mapping

#### Notes
- **Separate Resource Creation**: Unlike current implementation, Location should be extracted as separate resources, not embedded in Encounter
- **Deduplication Critical**: Same facility may appear in multiple encounters/procedures; must deduplicate to avoid resource proliferation
- **Multiple Source Locations**: Location data appears in both document body (Service Delivery Location template) and header (healthCareFacility); both should convert to same Location resource
- **Identifier Importance**: NPI is the most stable identifier for US facilities; use for deduplication when available
- **Managing Organization**: Required by US Core; infer from encounter serviceProvider or document custodian
- **Address Formatting**: Follow US Realm address conventions with separate street lines
- **Telecom URI Schemes**: Parse and convert C-CDA URI schemes (tel:, mailto:) to FHIR system codes
- **USCDI Compliance**: Facility Name, Type, Identifier, and Address are USCDI elements
- **Type Value Sets**: US Core allows HSLOC, SNOMED CT, or CMS POS codes; support all three
- **Physical Type**: Optional; only infer when highly confident (e.g., "Operating Room" → "room")
- **Status Default**: Always use "active" unless explicit information suggests otherwise
- **Not in C-CDA on FHIR IG**: Location mapping not officially published in C-CDA on FHIR IG v2.0.0; this implementation fills that gap

---

### 7. Device (Product Instance) ✅ **IMPLEMENTED** (2025-12-20)

**Implementation**: Fully implemented with comprehensive test coverage. Both assignedAuthoringDevice (authoring systems/software) and Product Instance (medical devices, implantable devices) are converted to FHIR Device resources with complete UDI parsing, US Core Implantable Device profile support, and integration with Procedure.focalDevice.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/device.md`
- ✅ **C-CDA Documentation**: `docs/ccda/product-instance.md`, `docs/ccda/assigned-authoring-device.md`
- ✅ **Mapping Specification**: `docs/mapping/22-device.md`

#### Standards References
- **FHIR R4B Resource**: [Device](https://hl7.org/fhir/R4B/device.html)
- **US Core Profile**: [US Core Implantable Device Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device)
- **C-CDA Templates**:
  - Product Instance: `2.16.840.1.113883.10.20.22.4.37`
  - Author Participation (assignedAuthoringDevice): `2.16.840.1.113883.10.20.22.4.119`
  - Device Identifier Observation: `2.16.840.1.113883.10.20.22.4.304`
- **USCDI Requirement**: Unique Device Identifier (UDI) for Implantable Devices (USCDI v1+)

#### Current Implementation Status

✅ **Implemented**: assignedAuthoringDevice to Device (authoring systems)
- Converts EHR systems, clinical software, and automated measurement devices
- Maps `manufacturerModelName` and `softwareName` to FHIR `Device.deviceName`
- Creates Device resources from document/entry authors
- Location: `ccda_to_fhir/converters/device.py`

✅ **Implemented**: Product Instance to Device (medical devices)
- Product Instance template (`2.16.840.1.113883.10.20.22.4.37`) fully converted
- Participant elements with typeCode="DEV" processed in Procedure converter
- Implantable devices (pacemakers, stents, prosthetics) converted with patient references
- Surgical instruments and medical equipment converted
- UDI parsing and mapping implemented (GS1 format with support for HIBCC/ICCBBA)
- Patient reference added for implantable devices
- US Core Implantable Device profile applied when patient reference present
- Integration with Procedure.focalDevice for device tracking
- Location: `ccda_to_fhir/converters/device.py`, `ccda_to_fhir/converters/procedure.py`
- UDI Parser: `ccda_to_fhir/utils/udi_parser.py`
- Tests: `tests/unit/converters/test_device.py` (33 tests, all passing)

#### Required Implementation

Product Instance represents specific medical devices used in patient care, particularly implantable devices requiring UDI tracking.

##### Input: C-CDA Product Instance

```xml
<procedure classCode="PROC" moodCode="EVN">
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

##### Output: FHIR US Core Implantable Device

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

#### Implementation Checklist

##### Product Instance Converter (`ccda_to_fhir/converters/device.py`)
- [ ] Add `convert_product_instance()` method to DeviceConverter
- [ ] Map `participantRole/id` → Device.identifier
- [ ] Parse UDI from `id[@root='2.16.840.1.113883.3.3719']` → Device.udiCarrier
- [ ] Extract Device Identifier (DI) from UDI application identifier `(01)`
- [ ] Extract production identifiers from UDI: `(11)` manufacturing date, `(17)` expiration date, `(10)` lot number, `(21)` serial number
- [ ] Map `playingDevice/code` → Device.type
- [ ] Map `playingDevice/manufacturerModelName` → Device.deviceName + Device.modelNumber
- [ ] Map `scopingEntity/desc` → Device.manufacturer
- [ ] Map `scopingEntity/id` → Device.owner (Organization reference)
- [ ] Add patient reference from procedure/observation subject for implantable devices
- [ ] Set Device.status based on context (procedure completed → active)
- [ ] Apply US Core Implantable Device profile for implanted devices

##### UDI Parsing Utility
- [ ] Create UDI parser utility function
- [ ] Support GS1 format (application identifiers: 01, 11, 17, 10, 21)
- [ ] Extract deviceIdentifier from `(01)` application identifier
- [ ] Parse manufacture date from `(11)` to FHIR date format (YYYYMMDD → YYYY-MM-DD)
- [ ] Parse expiration date from `(17)` to FHIR date format
- [ ] Extract lot number from `(10)`
- [ ] Extract serial number from `(21)`
- [ ] Determine issuer from OID (GS1, HIBCC, ICCBBA)
- [ ] Set jurisdiction to FDA for US devices

##### Procedure Converter Updates (`ccda_to_fhir/converters/procedure.py`)
- [ ] Detect participant elements with typeCode="DEV"
- [ ] Call DeviceConverter for Product Instance participants
- [ ] Add Device resources to conversion output
- [ ] Reference Device in Procedure.focalDevice
- [ ] Pass patient reference to DeviceConverter for implantable devices

##### Model Updates (`ccda_to_fhir/ccda/models/procedure.py`)
- [ ] Ensure Participant model includes typeCode
- [ ] Ensure ParticipantRole model includes playingDevice
- [ ] Ensure PlayingDevice model includes code and manufacturerModelName

##### Device Type Classification
- [ ] Identify implantable devices by procedure code (insertion, implantation)
- [ ] Identify implantable devices by device code (pacemaker, stent, prosthetic)
- [ ] Apply US Core Implantable Device profile when patient reference required
- [ ] Use base Device profile for non-implantable devices (instruments, equipment)

##### Deduplication
- [ ] Generate consistent Device IDs from UDI or identifier
- [ ] Check for existing Device before creating new one
- [ ] Deduplicate by UDI deviceIdentifier when available
- [ ] Deduplicate by organization identifier + serial number for non-UDI devices

##### Tests (`tests/converters/test_device.py`)
- [x] Test assignedAuthoringDevice → Device (already implemented)
- [ ] Test Product Instance → Device conversion
- [ ] Test UDI parsing and mapping (GS1 format)
- [ ] Test manufacturing/expiration date conversion
- [ ] Test lot number and serial number extraction
- [ ] Test device type code mapping (SNOMED CT)
- [ ] Test manufacturer name mapping
- [ ] Test patient reference for implantable devices
- [ ] Test US Core Implantable Device profile application
- [ ] Test device without UDI (organization identifier only)
- [ ] Test multiple devices in single procedure
- [ ] Test Device deduplication by UDI

##### Integration Tests (`tests/integration/test_procedure_with_device.py`)
- [ ] Test procedure with implanted pacemaker (complete UDI)
- [ ] Test procedure with orthopedic implant
- [ ] Test procedure with colonoscope (reusable device)
- [ ] Test procedure with multiple devices
- [ ] Test device reference in Procedure.focalDevice
- [ ] Test Device and Procedure in Bundle

#### File Locations

**Files to Modify:**
```
ccda_to_fhir/
├── converters/
│   ├── device.py                # Add convert_product_instance() method
│   └── procedure.py             # Add device participant processing
├── utils/
│   └── udi_parser.py            # New: UDI parsing utility
tests/
├── converters/
│   └── test_device.py           # Add Product Instance tests
└── integration/
    └── test_procedure_with_device.py  # New: Integration tests
```

#### Related Documentation
- See `docs/mapping/22-device.md` for complete mapping specification
- See `docs/fhir/device.md` for FHIR Device element definitions
- See `docs/ccda/product-instance.md` for C-CDA Product Instance specifications
- See `docs/ccda/assigned-authoring-device.md` for assignedAuthoringDevice specifications
- See `docs/mapping/05-procedure.md` for Procedure device participant mapping

#### Notes
- **Partial Implementation**: assignedAuthoringDevice already implemented; only Product Instance missing
- **UDI Critical**: UDI parsing is essential for FDA regulatory compliance and device tracking
- **US Core Profile**: Must apply US Core Implantable Device profile when patient reference present
- **Patient Reference**: Required for implantable devices; infer from procedure subject
- **Device Type Detection**: Use procedure code (insertion/implantation) and device code to identify implantable devices
- **Multiple Devices**: Procedures may have multiple device participants; create separate Device resource for each
- **Deduplication Important**: Same device may appear in multiple procedures; deduplicate by UDI or identifier
- **GS1 Format**: Most common UDI format in US; prioritize GS1 application identifier parsing
- **Historical Devices**: When UDI unavailable, use organization identifier and model name
- **Procedure Reference**: Link Device back to Procedure via Procedure.focalDevice[].manipulated
- **Status Mapping**: Infer Device.status from procedure status (completed → active)
- **USCDI Requirement**: UDI for implantable devices is USCDI v1 requirement
- **Non-Implantable Devices**: Support surgical instruments, diagnostic devices, and equipment
- **Software Devices**: assignedAuthoringDevice handles EHR/software; Product Instance handles physical devices

---

## Low Priority: USCDI Requirements

### 8. CareTeam ✅ **IMPLEMENTED** (2025-12-20)

**Implementation:** Fully implemented with support for structured Care Team Organizer conversion to US Core CareTeam profile. Converts Care Team Organizer entries with members, roles, team types, and team lead designation.

**Capabilities:** Care Team Organizer templates are now converted to FHIR CareTeam resources with full participant mapping, role codes, team categories, and referenced Practitioner/PractitionerRole/Organization resources.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/careteam.md`
- ✅ **C-CDA Documentation**: `docs/ccda/care-team.md`
- ✅ **Mapping Specification**: `docs/mapping/17-careteam.md`

#### Standards References
- **US Core Profile**: [US Core CareTeam Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam)
- **C-CDA Templates**:
  - Care Teams Section: `2.16.840.1.113883.10.20.22.2.500` (LOINC `85847-2` - "Patient Care team information")
  - Care Team Organizer: `2.16.840.1.113883.10.20.22.4.500` (LOINC `86744-0` - "Care team", extensions 2019-07-01, 2022-06-01)
  - Care Team Member Act: `2.16.840.1.113883.10.20.22.4.500.1` (extensions 2019-07-01, 2022-06-01)
  - Care Team Type Observation: `2.16.840.1.113883.10.20.22.4.500.2` (extension 2019-07-01)
  - Alternative: documentationOf/serviceEvent/performer (header-based representation)
- **USCDI Requirement**: Care Team Members (USCDI v4 data class)

#### Required Implementation

CareTeam represents the care team members associated with a patient for care coordination. C-CDA supports two approaches:

1. **Structured Care Teams Section** (Recommended)
   - Discrete, computable representation
   - Supports multiple teams with types, leads, and members
   - Newer approach (2019-2022 templates)

2. **Header serviceEvent/performer** (Legacy)
   - Simple list of care providers
   - Common in transition-of-care documents
   - Widely implemented but less structured

##### Input: C-CDA Care Team Organizer (Structured Approach)

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.500" extension="2022-06-01"/>
  <code code="85847-2" codeSystem="2.16.840.1.113883.6.1" displayName="Patient Care team information"/>
  <title>CARE TEAMS</title>

  <entry>
    <organizer classCode="CLUSTER" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.500" extension="2022-06-01"/>
      <id root="2.16.840.1.113883.19.5" extension="primary-team-001"/>
      <code code="86744-0" codeSystem="2.16.840.1.113883.6.1" displayName="Care team"/>
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

      <!-- Care Team Members -->
      <component>
        <act classCode="PCPR" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.500.1" extension="2022-06-01"/>
          <code code="86744-0" codeSystem="2.16.840.1.113883.6.1"/>
          <statusCode code="active"/>
          <performer>
            <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88"
                         displayName="Primary Care Physician"/>
            <assignedEntity>
              <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
              <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"/>
              <assignedPerson>
                <name><given>John</given><family>Smith</family></name>
              </assignedPerson>
              <representedOrganization>
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

##### Input: C-CDA Header serviceEvent/performer (Legacy Approach)

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
      <assignedEntity>
        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        <assignedPerson>
          <name><given>John</given><family>Smith</family></name>
        </assignedPerson>
      </assignedEntity>
    </performer>

    <!-- Additional performers -->
  </serviceEvent>
</documentationOf>
```

##### Output: FHIR CareTeam Resource

```json
{
  "resourceType": "CareTeam",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam"]
  },
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5",
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
    "reference": "Patient/patient-123"
  },
  "period": {
    "start": "2023-01-15"
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
      "reference": "PractitionerRole/practitionerrole-npi-1234567890",
      "display": "Dr. John Smith"
    }
  }],
  "managingOrganization": [{
    "reference": "Organization/org-clinic"
  }]
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/careteam.py`)
- [ ] Create `CareTeamConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Care Team Organizer
- [ ] Map `organizer/id` → `CareTeam.identifier` (OID to Identifier)
- [ ] Map `statusCode/@code` → `CareTeam.status` per ConceptMap (active, completed, suspended, etc.)
- [ ] Map `effectiveTime` → `CareTeam.period` (IVL_TS to Period)
- [ ] Extract patient reference from document `recordTarget` → `CareTeam.subject`
- [ ] Map `component/observation[type]` → `CareTeam.category` (team type)
- [ ] Generate `CareTeam.name` from team type and patient name
- [ ] Map managing organization from custodian or first member's organization → `CareTeam.managingOrganization`

##### Participant Processing
- [ ] Process Care Team Member Act components → `CareTeam.participant` array
- [ ] Map `performer/functionCode` → `participant.role` (CodeableConcept)
- [ ] Map function code system OIDs to FHIR system URIs (v3-RoleCode, SNOMED CT)
- [ ] Create Practitioner resource from `assignedEntity/assignedPerson`
- [ ] Create PractitionerRole resource from `assignedEntity` (includes location, contact, specialty)
- [ ] Create Organization resource from `representedOrganization`
- [ ] Map `participant.member` → Reference to PractitionerRole (preferred) or Practitioner
- [ ] Map `act/effectiveTime` → `participant.period` (member participation period)
- [ ] Handle non-clinical members (family caregivers) → RelatedPerson resources
- [ ] Deduplicate practitioners by NPI across multiple teams

##### Care Team Lead Handling
- [ ] Identify care team lead from `participant[@typeCode='PPRF']`
- [ ] Match lead ID to Care Team Member performer ID
- [ ] Order participants with lead first in array
- [ ] Add role coding for team lead if applicable

##### Header serviceEvent/performer Conversion
- [ ] Create `ServiceEventCareTeamConverter` for header-based approach
- [ ] Map `serviceEvent/effectiveTime` → `CareTeam.period`
- [ ] Map each `performer[@typeCode='PRF']` → `CareTeam.participant`
- [ ] Generate CareTeam identifier from document ID + "-careteam"
- [ ] Infer category from document type (encounter-focused, longitudinal, etc.)
- [ ] Generate name: "{DocumentType} Care Team for {PatientName}"

##### Section Processing (`ccda_to_fhir/sections/careteams_section.py`)
- [ ] Create `CareTeamsSectionProcessor` class
- [ ] Identify Care Teams Section by template ID `2.16.840.1.113883.10.20.22.2.500`
- [ ] Extract Care Team Organizer entries
- [ ] Call `CareTeamConverter` for each organizer
- [ ] Store CareTeam resources in result bundle

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_care_teams_section()` validator for template `2.16.840.1.113883.10.20.22.2.500`
- [ ] Add `is_care_team_organizer()` validator for template `2.16.840.1.113883.10.20.22.4.500`
- [ ] Add `is_care_team_member_act()` validator for template `2.16.840.1.113883.10.20.22.4.500.1`
- [ ] Add `is_care_team_type_observation()` validator for template `2.16.840.1.113883.10.20.22.4.500.2`
- [ ] Validate required elements: id, code, statusCode, effectiveTime, at least one member

##### Value Set Mappings
- [ ] Implement status ConceptMap: active→active, completed→inactive, suspended→suspended, etc.
- [ ] Map Care Team Type LOINC answer codes (LA27976-2, LA27977-0, LA28865-6, LA28866-4, LA28867-2)
- [ ] Map Care Team Member Function codes (v3-RoleCode, SNOMED CT)
- [ ] Convert NUCC Provider Taxonomy codes for professional credentials

##### Tests (`tests/converters/test_careteam.py`)
- [ ] Test Care Team Organizer → CareTeam conversion (structured approach)
- [ ] Test serviceEvent/performer → CareTeam conversion (header approach)
- [ ] Test status mapping for all status codes
- [ ] Test category mapping (team types)
- [ ] Test participant.role mapping (function codes from v3-RoleCode and SNOMED CT)
- [ ] Test participant.member reference creation (Practitioner, PractitionerRole, RelatedPerson)
- [ ] Test PractitionerRole creation with location and contact info
- [ ] Test care team lead identification and ordering
- [ ] Test multiple members in one team
- [ ] Test multiple care teams per patient
- [ ] Test non-clinical team members (family caregivers → RelatedPerson)
- [ ] Test organizational team members (Organization reference)
- [ ] Test practitioner deduplication by NPI
- [ ] Test combined approach (structured section + header performers)
- [ ] Test missing effectiveTime handling
- [ ] Test missing function codes
- [ ] Test narrative generation from section text

##### Integration Tests (`tests/integration/test_careteams_section.py`)
- [ ] Test complete Care Teams Section extraction
- [ ] Test document with both primary care and specialty teams
- [ ] Test transition-of-care document with header performers only
- [ ] Test combined structured section + header performers
- [ ] Test care team references from other resources (CarePlan, Observation)

##### US Core Conformance
- [ ] Validate required elements: `status` (1..1), `subject` (1..1), `participant` (1..*)
- [ ] Validate participant required elements: `role` (1..1), `member` (1..1)
- [ ] Validate Must Support: status, subject, participant, participant.role, participant.member
- [ ] Include US Core CareTeam profile in `meta.profile`
- [ ] Validate member references use PractitionerRole when available (recommended)
- [ ] Support patient+status search parameter combination

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── careteam.py                  # CareTeamConverter class
├── sections/
│   └── careteams_section.py         # CareTeamsSectionProcessor class
tests/
├── converters/
│   └── test_careteam.py             # Unit tests
└── integration/
    └── test_careteams_section.py    # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                        # Add validators
├── converter.py                     # Register CareTeamsSectionProcessor
├── converters/__init__.py           # Export CareTeamConverter
└── sections/__init__.py             # Export CareTeamsSectionProcessor
```

#### Related Documentation
- See `docs/mapping/17-careteam.md` for complete mapping specification
- See `docs/fhir/careteam.md` for FHIR CareTeam element definitions
- See `docs/ccda/care-team.md` for C-CDA template specifications
- See `docs/mapping/09-participations.md` for Practitioner/PractitionerRole/Organization mapping (dependency)

#### Notes
- **Two Approaches**: Supports both structured Care Team Organizer (newer, richer) and header serviceEvent/performer (legacy, simpler)
- **Low Priority Rationale**: Not widely adopted in legacy C-CDA documents; Care Team Organizer templates are relatively new (2019-2022)
- **USCDI v4**: Required for USCDI v4 compliance but not blocking for core conversion functionality
- **Practitioner Deduplication**: Same practitioner may appear in multiple teams; deduplicate by NPI
- **PractitionerRole Preferred**: Use PractitionerRole over Practitioner for member references (provides location/contact context)
- **Non-Clinical Members**: Support family caregivers, social services, transportation providers via RelatedPerson or Organization
- **Care Team Types**: LOINC answer codes classify teams as longitudinal, condition-focused, encounter-focused, episode-focused, or event-focused
- **Team Lead**: Identified by `participant[@typeCode='PPRF']` matching member performer ID; no direct FHIR element, use ordering
- **Combined Approach**: When both structured section and header performers exist, prefer structured section and optionally create encounter-specific team from header
- **Not in C-CDA on FHIR IG**: CareTeam mapping not officially published in C-CDA on FHIR IG v2.0.0; this implementation fills that gap based on US Core requirements

---

### 9. ServiceRequest ❌ **NOT IMPLEMENTED** - LOW PRIORITY

**Impact**: Planned procedures and ordered services are currently partially covered by Procedure resources with status=planned, but formal service requests/orders are not represented according to FHIR workflow patterns. This limits interoperability for order management and care planning workflows.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/service-request.md`
- ✅ **C-CDA Documentation**: `docs/ccda/planned-procedure.md`
- ✅ **Mapping Specification**: `docs/mapping/18-service-request.md`

#### Standards References
- **US Core Profile**: [US Core ServiceRequest Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest)
- **C-CDA Templates**:
  - Planned Procedure (V2): `2.16.840.1.113883.10.20.22.4.41` (extension 2022-06-01)
  - Planned Act (V2): `2.16.840.1.113883.10.20.22.4.39` (extension 2014-06-09)
  - Plan of Treatment Section: `2.16.840.1.113883.10.20.22.2.10` (LOINC `18776-5`)
- **C-CDA on FHIR IG**: ❌ **NOT COVERED** - ServiceRequest mapping not included in v2.0.0

#### Required Implementation

ServiceRequest represents orders, proposals, or plans for procedures, diagnostic tests, therapeutic services, and referrals. Distinguished from Procedure (completed activities) by intent and status.

##### Key Distinction: moodCode Validation

**CRITICAL**: C-CDA uses `moodCode` to distinguish planned vs completed activities:

| C-CDA moodCode | FHIR Resource | Action |
|----------------|---------------|--------|
| **INT** (Intent) | ServiceRequest | Convert to ServiceRequest |
| **RQO** (Request) | ServiceRequest | Convert to ServiceRequest |
| **PRP** (Proposal) | ServiceRequest | Convert to ServiceRequest |
| **EVN** (Event) | **Procedure** | Use Procedure converter instead |
| **GOL** (Goal) | **Goal** | Use Goal converter instead |

##### Input: C-CDA Planned Procedure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
  <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of care note"/>
  <title>PLAN OF TREATMENT</title>

  <entry typeCode="DRIV">
    <procedure classCode="PROC" moodCode="RQO">
      <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
      <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
      <statusCode code="active"/>
      <effectiveTime value="20240613"/>

      <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
            displayName="Colonoscopy">
        <originalText>Screening colonoscopy</originalText>
        <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
                     displayName="Colonoscopy, flexible"/>
      </code>

      <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Colon structure"/>

      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
          <assignedPerson>
            <name><given>John</given><family>Gastro</family></name>
          </assignedPerson>
        </assignedEntity>
      </performer>

      <author>
        <time value="20240115140000-0500"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name><given>Sarah</given><family>Smith</family></name>
          </assignedPerson>
        </assignedAuthor>
      </author>

      <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7" displayName="Routine"/>

      <!-- Indication -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19"/>
          <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
                displayName="Clinical finding"/>
          <value xsi:type="CD" code="428165003" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Screening for colon cancer"/>
        </observation>
      </entryRelationship>

      <!-- Patient Instructions -->
      <entryRelationship typeCode="SUBJ" inversionInd="true">
        <act classCode="ACT" moodCode="INT">
          <templateId root="2.16.840.1.113883.10.20.22.4.20"/>
          <code code="409073007" codeSystem="2.16.840.1.113883.6.96"
                displayName="Instruction"/>
          <text>Patient to follow bowel prep instructions 24 hours before procedure.</text>
        </act>
      </entryRelationship>

    </procedure>
  </entry>
</section>
```

##### Output: FHIR ServiceRequest Resource

```json
{
  "resourceType": "ServiceRequest",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:db734647-fc99-424c-a864-7e3cda82e703"
  }],
  "status": "active",
  "intent": "order",
  "category": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "387713003",
      "display": "Surgical procedure"
    }]
  }],
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "73761001",
        "display": "Colonoscopy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "45378",
        "display": "Colonoscopy, flexible"
      }
    ],
    "text": "Screening colonoscopy"
  },
  "subject": {
    "reference": "Patient/patient-123"
  },
  "occurrenceDateTime": "2024-06-13",
  "authoredOn": "2024-01-15T14:00:00-05:00",
  "requester": {
    "reference": "Practitioner/practitioner-npi-1234567890",
    "display": "Dr. Sarah Smith"
  },
  "performer": [{
    "reference": "Practitioner/practitioner-npi-9876543210",
    "display": "Dr. John Gastro"
  }],
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "428165003",
      "display": "Screening for colon cancer"
    }]
  }],
  "bodySite": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "71854001",
      "display": "Colon structure"
    }]
  }],
  "priority": "routine",
  "patientInstruction": "Patient to follow bowel prep instructions 24 hours before procedure."
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/service_request.py`)
- [ ] Create `ServiceRequestConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting Planned Procedure or Planned Act element
- [ ] **CRITICAL**: Validate moodCode ∈ {INT, RQO, PRP, ARQ, PRMS}
- [ ] Reject moodCode=EVN (use Procedure converter) or moodCode=GOL (use Goal converter)
- [ ] Map `id` → `ServiceRequest.identifier` (OID to Identifier conversion)
- [ ] Map `statusCode` → `ServiceRequest.status` per ConceptMap (active, completed, revoked, on-hold, etc.)
- [ ] Map `moodCode` → `ServiceRequest.intent` per ConceptMap (INT→plan, RQO→order, PRP→proposal)
- [ ] Map `code` → `ServiceRequest.code` (CodeableConcept with coding array and originalText)
- [ ] Infer `ServiceRequest.category` from code/@codeSystem (LOINC→lab, CPT radiology→imaging, etc.)
- [ ] Extract patient reference from document `recordTarget` → `ServiceRequest.subject`
- [ ] Extract encounter reference from document `encompassingEncounter` → `ServiceRequest.encounter`
- [ ] Map `effectiveTime` → `ServiceRequest.occurrence[x]` (single date→dateTime, range→Period)
- [ ] Map `author/time` → `ServiceRequest.authoredOn`
- [ ] Map `author/assignedAuthor` → `ServiceRequest.requester` (create Practitioner/PractitionerRole)
- [ ] Map `performer/assignedEntity` → `ServiceRequest.performer` array
- [ ] Map `performer/functionCode` → `ServiceRequest.performerType`
- [ ] Map `priorityCode` → `ServiceRequest.priority` per ConceptMap (R→routine, UR→urgent, EM→stat)
- [ ] Map Priority Preference observation (template 4.143) → `ServiceRequest.priority`
- [ ] Map `targetSiteCode` → `ServiceRequest.bodySite` array
- [ ] Map entryRelationship[typeCode='RSON']/observation (Indication) → `ServiceRequest.reasonCode`
- [ ] Map entryRelationship[typeCode='RSON'] (Problem Observation) → `ServiceRequest.reasonReference`
- [ ] Map entryRelationship[typeCode='SUBJ'] (Instruction) → `ServiceRequest.patientInstruction`
- [ ] Map `text` or narrative reference → `ServiceRequest.note`
- [ ] Map entryRelationship Goal Observations → `ServiceRequest.supportingInfo`
- [ ] Map entryRelationship Planned Coverage → `ServiceRequest.insurance`
- [ ] Set `meta.profile` to US Core ServiceRequest Profile URL

##### Section Processing (`ccda_to_fhir/sections/plan_of_treatment_section.py`)
- [ ] Create `PlanOfTreatmentSectionProcessor` class
- [ ] Identify Plan of Treatment Section by template ID `2.16.840.1.113883.10.20.22.2.10`
- [ ] Extract entry elements
- [ ] Filter for Planned Procedure (4.41) and Planned Act (4.39) templates
- [ ] Validate moodCode before calling converter
- [ ] Call `ServiceRequestConverter` for each planned entry
- [ ] Store ServiceRequest resources in result bundle

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_planned_procedure()` validator for template `2.16.840.1.113883.10.20.22.4.41`
- [ ] Add `is_planned_act()` validator for template `2.16.840.1.113883.10.20.22.4.39`
- [ ] Add `is_intervention_act()` validator for template `2.16.840.1.113883.10.20.22.4.131`
- [ ] Add `is_plan_of_treatment_section()` validator for template `2.16.840.1.113883.10.20.22.2.10`
- [ ] Validate moodCode attribute existence and value
- [ ] Validate required elements: id, code, statusCode

##### ConceptMaps
- [ ] Implement statusCode ConceptMap: active→active, completed→completed, cancelled→revoked, held→on-hold
- [ ] Implement moodCode ConceptMap: INT→plan, RQO→order, PRP→proposal, ARQ→order, PRMS→directive
- [ ] Implement priorityCode ConceptMap: R→routine, UR→urgent, EM→stat, A→asap, EL→routine

##### Tests (`tests/converters/test_service_request.py`)
- [ ] Test Planned Procedure → ServiceRequest conversion
- [ ] Test Planned Act → ServiceRequest conversion
- [ ] Test moodCode validation (INT/RQO/PRP accepted; EVN/GOL rejected)
- [ ] Test status mapping for all status codes
- [ ] Test intent mapping for all moodCodes
- [ ] Test category inference (LOINC→lab, CPT→imaging, SNOMED procedures→surgical)
- [ ] Test code mapping with multiple codings and originalText
- [ ] Test identifier mapping (OID to Identifier conversion)
- [ ] Test occurrence[x] mapping (single date, date range, missing)
- [ ] Test author mapping (requester and authoredOn)
- [ ] Test performer mapping (with and without organization)
- [ ] Test performerType from functionCode
- [ ] Test priority mapping (priorityCode and Priority Preference observation)
- [ ] Test bodySite mapping from targetSiteCode
- [ ] Test reasonCode from Indication observations
- [ ] Test reasonReference from Problem Observations
- [ ] Test patientInstruction from Instruction acts
- [ ] Test note from text/narrative
- [ ] Test supportingInfo from Goal Observations (if present)
- [ ] Test insurance from Planned Coverage
- [ ] Test missing optional elements
- [ ] Test minimal Planned Procedure (only required elements)

##### Integration Tests (`tests/integration/test_plan_of_treatment_section.py`)
- [ ] Test Plan of Treatment Section extraction
- [ ] Test multiple planned procedures in one section
- [ ] Test mixed Planned Procedure and Planned Act entries
- [ ] Test complete Care Plan document with planned procedures
- [ ] Test ServiceRequest references to other resources (Patient, Practitioner, Condition, Goal, Coverage)
- [ ] Test bundle structure with all dependent resources

##### US Core Conformance
- [ ] Validate required elements: status (1..1), intent (1..1), code (1..1), subject (1..1)
- [ ] Validate Must Support: category, code.text, encounter, occurrence[x], authoredOn, requester, reasonCode, reasonReference
- [ ] Include US Core ServiceRequest profile in meta.profile
- [ ] Support search parameters: patient, _id, patient+category, patient+code, patient+category+authored
- [ ] Validate code bindings (status/intent required, category/code extensible)

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── service_request.py          # ServiceRequestConverter class
├── sections/
│   └── plan_of_treatment_section.py # PlanOfTreatmentSectionProcessor class
tests/
├── converters/
│   └── test_service_request.py      # Unit tests
└── integration/
    └── test_plan_of_treatment_section.py # Integration tests
```

**Files to Modify:**
```
ccda_to_fhir/
├── models.py                        # Add validators
├── converter.py                     # Register PlanOfTreatmentSectionProcessor
├── converters/__init__.py           # Export ServiceRequestConverter
└── sections/__init__.py             # Export PlanOfTreatmentSectionProcessor
```

#### Related Documentation
- See `docs/mapping/18-service-request.md` for complete mapping specification
- See `docs/fhir/service-request.md` for FHIR ServiceRequest element definitions
- See `docs/ccda/planned-procedure.md` for C-CDA Planned Procedure and Planned Act template specifications
- See `docs/mapping/05-procedure.md` for Procedure mapping (completed procedures with moodCode=EVN)
- See `docs/mapping/13-goal.md` for Goal mapping (goal observations with moodCode=GOL)

#### Notes
- **Low Priority Rationale**: Current implementation partially handles this by creating Procedure resources with status=planned. ServiceRequest provides better FHIR workflow semantics but is not blocking for basic conversion.
- **moodCode Validation**: CRITICAL distinction between planned (ServiceRequest) and completed (Procedure) activities
- **Not in C-CDA on FHIR IG**: ServiceRequest mapping not officially published in C-CDA on FHIR IG v2.0.0; this implementation fills that gap
- **Category Inference**: C-CDA lacks explicit category; must infer from code system (LOINC→lab, CPT radiology codes→imaging, etc.)
- **Request-Response Pattern**: When planned procedure is performed, create Procedure with Procedure.basedOn referencing ServiceRequest
- **Care Plan Integration**: ServiceRequests are part of care plans; link via CarePlan.activity.reference
- **USCDI**: Service requests not explicitly required by USCDI, but supports care planning workflows
- **Multiple Authors**: If multiple authors exist, map first to requester, add others to note
- **Patient Instructions**: Map from Instruction template (typeCode='SUBJ', inversionInd='true') to patientInstruction

---

## Document Context

Goals appear in the following C-CDA document types:
- **Care Plan** (`2.16.840.1.113883.10.20.22.1.15`) - **REQUIRED**
- Continuity of Care Document (CCD) - OPTIONAL
- Consultation Note - OPTIONAL
- Discharge Summary - OPTIONAL

Goals may also appear in the **Plan of Treatment Section** (`2.16.840.1.113883.10.20.22.2.10`).

---

## Standards Compliance Notes

### C-CDA on FHIR IG v2.0.0 Status
The C-CDA on FHIR Implementation Guide v2.0.0 does **not** include Goal mappings. Per the official IG:
> "The following clinical domains are included: Allergies, Encounters, Immunizations, Medications, Notes, Participation, Patient, Problems, Procedures, Results, Social History, and Vital Signs. Goals are notably absent from this inventory."

Source: [C-CDA on FHIR IG CF-index](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-index.html)

### Why Implement Despite Absence from IG?

1. **US Core Requirement**: US Core v8.0.1 includes Goal as a key resource with Must Support elements
2. **USCDI Requirement**: Goals are part of USCDI data elements
3. **Certification Requirement**: ONC 2015 Edition certification requires Goal support by December 31, 2025
4. **Care Plan Completeness**: Care Plan documents (required template) cannot be fully converted without Goal support
5. **Clinical Value**: Goals are essential for patient-centered care planning and shared decision-making

### Implementation Approach

Since C-CDA on FHIR IG doesn't provide official mapping, this implementation:
1. Follows US Core Goal Profile v8.0.1 requirements
2. Uses C-CDA R2.1 Goal Observation template specifications
3. Applies mapping patterns consistent with other C-CDA → FHIR conversions in this library
4. Documents all design decisions in `docs/mapping/13-goal.md`

### 10. DocumentReference (Document Indexing) ✅ **IMPLEMENTED** (2025-12-20)

**Implementation**: Fully implemented with comprehensive test coverage (21 tests passing). C-CDA documents are now converted to DocumentReference resources with complete metadata, hash calculation, document relationships (relatesTo), and context including service events.

**Capabilities**: Provides lightweight document indexing with support for:
- Document metadata (identifier, masterIdentifier, type, category, status)
- Content attachment with SHA-1 hash for integrity verification
- Document relationships (replaces, appends, transforms)
- Clinical context including service events and encounter references
- Security labels and confidentiality
- US Core DocumentReference profile compliance

**Previous Impact**: Cannot index C-CDA documents for discovery and management without full conversion to FHIR resources. Document management systems, health information exchanges, and document repositories require DocumentReference for lightweight document indexing, search, and retrieval workflows.

#### Documentation
- ✅ **FHIR Documentation**: `docs/fhir/document-reference.md`
- ✅ **C-CDA Documentation**: Covered in `docs/ccda/clinical-document.md`
- ✅ **Mapping Specification**: `docs/mapping/26-document-reference.md`

#### Standards References
- **FHIR R4 Resource**: [DocumentReference](https://hl7.org/fhir/R4/documentreference.html)
- **US Core Profile**: [US Core DocumentReference Profile v8.0.1](http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference)
- **C-CDA Template**: US Realm Header (`2.16.840.1.113883.10.20.22.1.1`)
- **IHE Format Codes**: [IHE Format Code ValueSet](http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem)
- **USCDI Requirement**: Clinical Notes (v1+)

#### Required Implementation

DocumentReference provides metadata about a document to make it discoverable and manageable. Unlike Composition (which converts the entire document to FHIR resources), DocumentReference creates a lightweight index that points to the original C-CDA XML document.

**Key Distinction**:
- **Composition + Bundle**: Full structured conversion of C-CDA to FHIR resources
- **DocumentReference**: Lightweight indexing with reference to original C-CDA XML

Both approaches are complementary and can coexist.

##### Input: C-CDA ClinicalDocument

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>

  <id root="2.16.840.1.113883.19.5.99999.1" extension="TT988"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
        displayName="Summarization of Episode Note"/>
  <title>Continuity of Care Document</title>
  <effectiveTime value="20200301102000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <setId root="2.16.840.1.113883.19.5.99999.19" extension="sTT988"/>
  <versionNumber value="1"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5.99999.2" extension="998991"/>
      <patient>
        <name><given>Ellen</given><family>Ross</family></name>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20200301"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson>
        <name><given>Adam</given><family>Careful</family></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5.9999.1393"/>
        <name>Community Health and Hospitals</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <!-- Document body... -->
</ClinicalDocument>
```

##### Output: FHIR DocumentReference

```json
{
  "resourceType": "DocumentReference",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-documentreference"]
  },
  "identifier": [{
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.1",
    "value": "TT988"
  }],
  "masterIdentifier": {
    "system": "urn:oid:2.16.840.1.113883.19.5.99999.19",
    "value": "sTT988"
  },
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [{
      "system": "http://loinc.org",
      "code": "34133-9",
      "display": "Summarization of Episode Note"
    }]
  },
  "category": [{
    "coding": [{
      "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
      "code": "clinical-note",
      "display": "Clinical Note"
    }]
  }],
  "subject": {
    "reference": "Patient/patient-998991"
  },
  "date": "2020-03-01T10:20:00-05:00",
  "author": [{
    "reference": "Practitioner/practitioner-1234567890"
  }],
  "custodian": {
    "reference": "Organization/org-1393"
  },
  "content": [{
    "attachment": {
      "contentType": "application/xml",
      "language": "en-US",
      "url": "Binary/ccda-ccd-tt988",
      "title": "Continuity of Care Document",
      "creation": "2020-03-01T10:20:00-05:00"
    },
    "format": {
      "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
      "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
      "display": "C-CDA R2.1 Structured Body"
    }
  }]
}
```

#### Implementation Checklist

##### Core Converter (`ccda_to_fhir/converters/document_reference.py`)
- [ ] Create `DocumentReferenceConverter` class extending `BaseConverter`
- [ ] Implement `convert()` method accepting ClinicalDocument element
- [ ] Map `id` → `DocumentReference.identifier`
- [ ] Map `setId` → `DocumentReference.masterIdentifier`
- [ ] Map `code` → `DocumentReference.type` (LOINC document type)
- [ ] Set `category` = "clinical-note" for all clinical documents
- [ ] Set `status` = "current" (default), "superseded" (if replaced), or "entered-in-error"
- [ ] Set `docStatus` = "final" (default) or infer from context
- [ ] Map `effectiveTime` → `DocumentReference.date`
- [ ] Map `recordTarget` → `subject` (Patient reference)
- [ ] Map `author` → `author[]` (Practitioner references)
- [ ] Map `legalAuthenticator` → `authenticator`
- [ ] Map `custodian` → `custodian` (Organization reference)
- [ ] Map `confidentialityCode` → `securityLabel`
- [ ] Map `relatedDocument` → `relatesTo` (replaces, appends, transforms)

##### Content Attachment Processing
- [ ] Store C-CDA XML in Binary resource
- [ ] Set `content.attachment.contentType` = "application/xml"
- [ ] Set `content.attachment.url` = reference to Binary resource
- [ ] Calculate SHA-1 hash of C-CDA XML → `content.attachment.hash`
- [ ] Set `content.attachment.size` = byte size of C-CDA XML
- [ ] Map `languageCode` → `content.attachment.language`
- [ ] Map `title` → `content.attachment.title`
- [ ] Map `effectiveTime` → `content.attachment.creation`

##### Format Code Determination
- [ ] Detect C-CDA version from templateId extension
- [ ] templateId extension "2015-08-01" or later → "urn:hl7-org:sdwg:ccda-structuredBody:2.1"
- [ ] templateId extension "2014-06-09" or earlier → "urn:hl7-org:sdwg:ccda-structuredBody:1.1"
- [ ] Set `content.format` with appropriate IHE format code

##### Context Mapping
- [ ] Map `componentOf/encompassingEncounter` → `context.encounter`
- [ ] Map `documentationOf/serviceEvent/@classCode` → `context.event`
- [ ] Map `documentationOf/serviceEvent/effectiveTime` → `context.period`
- [ ] Infer `context.facilityType` from encounter location (if available)
- [ ] Infer `context.practiceSetting` from author specialty code

##### Document Versioning Support
- [ ] When document has relatedDocument[@typeCode='RPLC']:
  - Set new DocumentReference status = "current"
  - Add relatesTo.code = "replaces" with target identifier
  - Update prior DocumentReference status to "superseded"
- [ ] Track document versions via masterIdentifier (setId)

##### Resource Creation and Management
- [ ] Create Binary resource for C-CDA XML storage
- [ ] Create or reference Patient resource (from recordTarget)
- [ ] Create or reference Practitioner resources (from author, authenticator)
- [ ] Create or reference Organization resource (from custodian)
- [ ] Generate unique ID for DocumentReference
- [ ] Ensure all references are resolvable

##### Model Validation (`ccda_to_fhir/models.py`)
- [ ] Add `is_clinical_document()` validator for ClinicalDocument element
- [ ] Validate required elements: id, code, effectiveTime, recordTarget, author, custodian
- [ ] Validate templateId includes US Realm Header (2.16.840.1.113883.10.20.22.1.1)

##### Tests (`tests/converters/test_document_reference.py`)
- [ ] Test basic ClinicalDocument → DocumentReference conversion
- [ ] Test identifier mapping (id → identifier, setId → masterIdentifier)
- [ ] Test document type mapping (all common C-CDA document types)
- [ ] Test category assignment ("clinical-note")
- [ ] Test status mapping (current, superseded, entered-in-error)
- [ ] Test date/time conversion (effectiveTime → date)
- [ ] Test participant mapping (author, authenticator, custodian)
- [ ] Test confidentiality mapping (confidentialityCode → securityLabel)
- [ ] Test relatedDocument mapping (RPLC → replaces, APND → appends)
- [ ] Test Binary resource creation for C-CDA XML
- [ ] Test content.attachment.url referencing Binary
- [ ] Test format code determination (R2.1 vs R1.1)
- [ ] Test SHA-1 hash calculation
- [ ] Test context mapping (encounter, event, period)
- [ ] Test document versioning (masterIdentifier consistency)

##### Integration Tests (`tests/integration/test_document_reference.py`)
- [ ] Test complete CCD → DocumentReference + Binary conversion
- [ ] Test Discharge Summary → DocumentReference conversion
- [ ] Test document replacement workflow (version 1 → version 2)
- [ ] Test complementary use: DocumentReference + Composition/Bundle for same document
- [ ] Test document retrieval via DocumentReference.content.attachment.url
- [ ] Test $docref operation support (if implementing)

##### US Core Conformance
- [ ] Validate required elements: `status`, `type`, `category`, `subject`, `content`
- [ ] Validate `content.attachment.contentType` = "application/xml"
- [ ] Validate `content.attachment.url` OR `content.attachment.data` present
- [ ] Validate Must Support: `identifier`, `date`, `author`, `content.format`, `context.encounter`, `context.period`
- [ ] Include US Core DocumentReference profile in `meta.profile`

##### Search Parameter Support
- [ ] Implement search by patient
- [ ] Implement search by patient + category
- [ ] Implement search by patient + type
- [ ] Implement search by patient + date (with comparators)
- [ ] Implement search by identifier

#### File Locations

**New Files to Create:**
```
ccda_to_fhir/
├── converters/
│   └── document_reference.py    # DocumentReferenceConverter class
tests/
├── converters/
│   └── test_document_reference.py  # Unit tests
└── integration/
    └── test_document_reference.py  # Integration tests
```

**Existing Files to Update:**
```
ccda_to_fhir/
├── converters/
│   └── __init__.py              # Export DocumentReferenceConverter
└── models.py                    # Add ClinicalDocument validators
```

#### Related Documentation
- **Composition Mapping**: [19-composition.md](19-composition.md) - Alternative structured conversion approach
- **Bundle Mapping**: [20-bundle.md](20-bundle.md) - Document Bundle packaging
- **Patient Mapping**: [01-patient.md](01-patient.md) - Patient reference mapping
- **Participations**: [09-participations.md](09-participations.md) - Author, authenticator, custodian mapping

#### Notes
- **Composition vs DocumentReference**: Composition is for structured document conversion where all C-CDA content is converted to FHIR resources. DocumentReference is for document indexing/referencing where the original C-CDA is preserved and metadata is extracted for discovery.
- **Complementary Use**: Both approaches can coexist - a system can create both a DocumentReference (pointing to the C-CDA) and a Composition/Bundle (with structured FHIR resources) for the same document.
- **US Core Requirement**: US Core requires DocumentReference for clinical notes, making this essential for USCDI compliance and document-based interoperability.
- **Binary Storage**: The C-CDA XML should be stored in a Binary resource and referenced via DocumentReference.content.attachment.url for clean separation of metadata and content.
- **Hash Integrity**: Always calculate and include attachment.hash (SHA-1) for document integrity verification.
- **Document Versioning**: Use masterIdentifier (from setId) to track document series, and relatesTo to link versions.

---
## Future Mappings (Low Priority)

*Currently none identified. This section will track additional mappings as they are documented.*

---

## Completed Mappings

For reference, the following mappings are **documented and implemented**:

1. ✅ Patient (01-patient.md)
2. ✅ Condition (02-condition.md)
3. ✅ AllergyIntolerance (03-allergy-intolerance.md)
4. ✅ Observation/Results (04-observation.md)
5. ✅ Procedure (05-procedure.md)
6. ✅ Immunization (06-immunization.md)
7. ✅ MedicationRequest (07-medication-request.md)
8. ✅ Encounter (08-encounter.md)
9. ✅ Participations (09-participations.md)
10. ✅ Notes (10-notes.md)
11. ✅ Social History (11-social-history.md)
12. ✅ Vital Signs (12-vital-signs.md)
13. ✅ DiagnosticReport (21-diagnostic-report.md) - Groups lab results/observations together

See `docs/implementation-status.md` for detailed implementation status of all completed mappings.

---

## How to Use This Document

**For Developers**:
1. Pick a missing mapping from the High Priority section
2. Review the documentation files listed
3. Follow the implementation checklist
4. Create the required files
5. Write tests per the test checklist
6. Submit PR with implementation

**For Project Managers**:
- Track certification deadlines
- Prioritize missing mappings based on deadline and impact
- Monitor implementation progress

**For Documentation**:
- When a new mapping is documented, add it to this file
- When a mapping is implemented, move it to "Completed Mappings"
- Keep implementation checklists up to date with discovered edge cases
