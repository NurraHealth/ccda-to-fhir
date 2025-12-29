# Cerner TOC Test Coverage Analysis

## Overview
Converted Cerner TOC document contains **40 resources** across 13 resource types.

## Coverage Summary by Resource Type

| Resource Type | Count | Total Fields | Tested | Untested | Coverage % |
|--------------|-------|--------------|--------|----------|------------|
| Patient | 1 | 44 | 41 | 3 | 93.2% |
| Practitioner | 1 | 17 | 15 | 2 | 88.2% |
| Observation | 14 | 52 | 35 | 17 | 67.3% |
| Location | 1 | 18 | 12 | 6 | 66.7% |
| Immunization | 1 | 23 | 15 | 8 | 65.2% |
| MedicationRequest | 4 | 40 | 26 | 14 | 65.0% |
| DiagnosticReport | 2 | 19 | 12 | 7 | 63.2% |
| Procedure | 2 | 15 | 8 | 7 | 53.3% |
| Encounter | 1 | 32 | 17 | 15 | 53.1% |
| AllergyIntolerance | 2 | 34 | 18 | 16 | 52.9% |
| Condition | 7 | 27 | 8 | 19 | 29.6% |
| Composition | 1 | 38 | 7 | 31 | 18.4% |
| Organization | 1 | 18 | 0 | 18 | 0.0% |

**Overall**: 343 total fields, 214 tested (62.4%), 129 untested (37.6%)

## Top 10 Most Important Untested Fields

These fields are critical for interoperability, US Core compliance, and correct C-CDA mapping:

### 1. **Composition.section** (Priority: 10)
- **Why it matters**: Sections organize the document structure and reference all clinical resources
- **What's populated**: All major sections (Encounters, Problems, Allergies, Medications, Immunizations, Procedures, Results, Vital Signs)
- **Example value**: 
  ```json
  {
    "title": "Encounter",
    "code": {
      "coding": [{"system": "http://loinc.org", "code": "46240-8", "display": "History of hospitalizations"}]
    },
    "entry": [{"reference": "Encounter/encounter-162"}]
  }
  ```
- **What to test**: Verify all expected sections present, codes correct, entries reference appropriate resources

### 2. **AllergyIntolerance.identifier** (Priority: 10)
- **Why it matters**: Required for resource identity and tracking across systems
- **What's populated**: UUID-based identifiers from C-CDA
- **Example value**: `{"system": "urn:uuid:D37DDEEB-F330-406E-AB28-4AF5E98B2925", "value": "urn:uuid:..."}`
- **What to test**: Verify identifier system and value are populated from C-CDA ID elements

### 3. **AllergyIntolerance.clinicalStatus** (Priority: 9)
- **Why it matters**: US Core required field indicating active/inactive/resolved
- **What's populated**: "active" for both allergies in the document
- **Example value**: `{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]}`
- **What to test**: Verify correct mapping from C-CDA statusCode to FHIR clinicalStatus

### 4. **Condition.identifier** (Priority: 10)
- **Why it matters**: Required for resource identity and tracking
- **What's populated**: UUID-based identifiers from C-CDA
- **Example value**: `{"system": "urn:uuid:0D1159C0-FF39-483F-868A-F8A69595025B", "value": "urn:uuid:..."}`
- **What to test**: Verify identifier populated for all 7 conditions

### 5. **Encounter.diagnosis** (Priority: 8)
- **Why it matters**: Links encounter to the conditions being addressed
- **What's populated**: References to Condition resources with diagnosis role
- **Example value**: 
  ```json
  {
    "condition": {"reference": "Condition/5b054cbf-3932-46db-b83f-928004eb51e4"},
    "use": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/diagnosis-role", "code": "AD"}]}
  }
  ```
- **What to test**: Verify encounter links to appropriate conditions from problem list

### 6. **MedicationRequest.intent** (Priority: 8)
- **Why it matters**: US Core required field distinguishing order vs plan vs proposal
- **What's populated**: "plan" for all 4 medication requests
- **Example value**: `"plan"`
- **What to test**: Verify intent is set appropriately based on C-CDA context

### 7. **MedicationRequest.dispenseRequest** (Priority: 7)
- **Why it matters**: Contains supply/quantity instructions critical for pharmacy
- **What's populated**: Quantity with value, unit, and UCUM code
- **Example value**: `{"quantity": {"value": 10.0, "unit": "mL", "system": "http://unitsofmeasure.org", "code": "mL"}}`
- **What to test**: Verify dispense request quantity mapped from C-CDA supply element

### 8. **Observation.hasMember** (Priority: 8)
- **Why it matters**: Links panel observations to their component results
- **What's populated**: References from vital signs panel to individual observations
- **Example value**: `[{"reference": "Observation/observation-16ad85ad09ee"}]`
- **What to test**: Verify vital signs and lab panels reference their component observations

### 9. **Composition.author** (Priority: 9)
- **Why it matters**: US Core required field identifying document creator
- **What's populated**: Reference to Practitioner and Organization
- **Example value**: `[{"display": "Aaron Admit, MD"}]`
- **What to test**: Verify author references created from C-CDA author elements

### 10. **Organization** (entire resource) (Priority: 6-10)
- **Why it matters**: Referenced by Patient.managingOrganization and Composition.custodian
- **What's populated**: Complete organization with identifier, name, address, telecom
- **Example values**:
  - `identifier`: `{"system": "urn:oid:2.16.840.1.113883.1.13.99999", "value": "2.16.840.1.113883.1.13.99999"}`
  - `name`: "Local Community Hospital Organization"
  - `active`: true
- **What to test**: Verify organization resource created and properly referenced

## Additional High-Priority Untested Fields

### Identifiers (Priority: 10)
Almost all resource identifiers are untested:
- Condition.identifier
- DiagnosticReport.identifier
- Encounter.identifier
- Immunization.identifier
- MedicationRequest.identifier
- Observation.identifier
- Practitioner.identifier
- Procedure.identifier

**Impact**: Identifiers are critical for resource tracking and matching across systems.

### Status Fields (Priority: 8-9)
- AllergyIntolerance.verificationStatus
- Condition.clinicalStatus
- Observation.status

**Impact**: Required US Core fields affecting clinical interpretation.

### Subject/Patient References (Priority: 10)
Several resources don't test the subject/patient reference:
- Condition.subject
- DiagnosticReport.subject
- Encounter.subject
- Procedure.subject

**Impact**: While these are tested in aggregate (test_all_clinical_resources_reference_steve_williamson), testing them per-resource ensures proper reference creation.

### Category Fields (Priority: 8)
- AllergyIntolerance.category (e.g., "medication", "food", "environment")
- Condition.category (tested for one condition but not consistently)

**Impact**: US Core required/must-support fields for proper categorization.

## Recommendations for Test Additions

### High Priority (Should Add)
1. **Composition.section tests**: Verify all expected sections, codes, and entry references
2. **Resource identifiers**: Add assertions for identifier.system and identifier.value on all resources
3. **AllergyIntolerance.clinicalStatus and verificationStatus**: Verify proper status mapping
4. **Organization resource**: Add tests verifying organization creation and references
5. **Encounter.diagnosis**: Verify diagnosis links to conditions

### Medium Priority (Good to Have)
6. **MedicationRequest.intent and dispenseRequest**: Verify medication ordering metadata
7. **Observation.hasMember**: Verify panel/component relationships
8. **Composition.author**: Verify author references
9. **Category fields**: Verify proper categorization across resource types
10. **Resource-specific subject references**: Add per-resource subject verification

### Low Priority (Nice to Have)
- Individual resource IDs (mostly internal UUIDs)
- resourceType fields (always correct by construction)
- Meta/profile fields (informational)

## Test Methodology

For each recommended test addition:
1. **Locate specific resource(s)** in bundle by clinical characteristic (code, date, value)
2. **Assert field presence** and non-null value
3. **Validate field structure** (e.g., identifier has both system and value)
4. **Verify semantic correctness** (e.g., status codes from correct CodeSystem)
5. **Check reference integrity** (e.g., referenced resources exist in bundle)

## Example Test Template

```python
def test_condition_has_identifier(self, cerner_bundle):
    """Validate all Conditions have identifiers from C-CDA."""
    conditions = [
        e.resource for e in cerner_bundle.entry
        if e.resource.get_resource_type() == "Condition"
    ]
    
    assert len(conditions) == 7, "Expected 7 conditions"
    
    for condition in conditions:
        # EXACT check: identifier present
        assert condition.identifier is not None and len(condition.identifier) > 0, \
            f"Condition {condition.id} must have identifier"
        
        identifier = condition.identifier[0]
        assert identifier.system is not None, "Identifier must have system"
        assert identifier.value is not None, "Identifier must have value"
        assert identifier.system.startswith("urn:uuid:"), \
            "C-CDA identifiers should use UUID URN scheme"
```
