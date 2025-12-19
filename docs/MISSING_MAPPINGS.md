# Missing C-CDA to FHIR Mappings

**Purpose**: Track mappings documented in `docs/mapping/` that are not yet implemented in the converter code.

**Last Updated**: 2025-12-19

---

## Status Overview

This document tracks mappings that are:
1. ✅ Fully documented with standards-compliant specifications
2. ❌ Not yet implemented in converter code
3. 🎯 Required for certification or standards compliance

**Current Status**: 2 missing mappings

---

## High Priority: Certification Requirements

### 1. CarePlan ❌ **NOT IMPLEMENTED** - HIGH PRIORITY

**Deadline**: December 31, 2025 (certification requirement)

**Impact**: Care Plan documents cannot be converted to FHIR without CarePlan support. This is a foundational document type for care coordination.

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

### 2. Goal ❌ **NOT IMPLEMENTED** - HIGH PRIORITY

**Deadline**: December 31, 2025 (certification requirement)

**Impact**: Care Plan documents cannot be fully converted without Goal support

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
