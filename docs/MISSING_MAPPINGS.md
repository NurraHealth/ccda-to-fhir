# Missing C-CDA to FHIR Mappings

**Purpose**: Track mappings documented in `docs/mapping/` that are not yet implemented in the converter code.

**Last Updated**: 2025-12-19

---

## Status Overview

This document tracks mappings that are:
1. ✅ Fully documented with standards-compliant specifications
2. ❌ Not yet implemented in converter code
3. 🎯 Required for certification or standards compliance

**Current Status**: 1 missing mapping

---

## High Priority: Certification Requirements

### 1. Goal ❌ **NOT IMPLEMENTED** - HIGH PRIORITY

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
