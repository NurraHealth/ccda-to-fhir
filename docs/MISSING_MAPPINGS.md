# Missing C-CDA to FHIR Mappings

**Purpose**: Track mappings documented in `docs/mapping/` that are not yet implemented in the converter code.

**Last Updated**: 2025-12-19

---

## Status Overview

This document tracks mappings that are:
1. ✅ Fully documented with standards-compliant specifications
2. ❌ Not yet implemented in converter code
3. 🎯 Required for certification or standards compliance

**Current Status**: 4 missing mappings

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

### 3. MedicationDispense ❌ **NOT IMPLEMENTED** - MEDIUM PRIORITY

**Impact**: Cannot represent actual dispensing events (vs orders/statements). Medication fill history and pharmacy dispensing records cannot be converted to FHIR.

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

### 4. Location ❌ **NOT IMPLEMENTED** - MEDIUM PRIORITY

**Impact**: Location data is currently embedded within Encounter resources but not extracted as separate, reusable Location resources. This limits interoperability and violates US Core recommendations to create separate Location resources.

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
