# Required Fixes and Enhancements

**Last Updated:** 2025-12-21
**Status:** Action Items from Comprehensive Code Review
**Total Items:** 15 (1 Critical ✅, 1 Critical Complete, 4 High, 6 Medium, 3 Low)

---

## 🔴 CRITICAL - Must Fix Before Production (1 item)

### ~~1. Location: Add managingOrganization Reference~~ ✅ COMPLETED

**Priority:** 🔴 CRITICAL
**File:** `ccda_to_fhir/converters/location.py`
**Status:** ✅ COMPLETED (2025-12-21)
**Issue:** Missing US Core Must Support element - US Core validation will fail
**Estimated Effort:** 1-2 hours

**Implementation Summary:**
- Added `_get_managing_organization_reference()` method to extract managing organization from location's scopingEntity
- Added `_generate_organization_id()` helper method to ensure consistent ID generation with OrganizationConverter
- managingOrganization field is now populated when:
  - Location has a scopingEntity with identifiers
  - Corresponding Organization resource exists in the reference registry
- Field is correctly omitted when no managing organization available (avoiding dangling references)
- Added 4 comprehensive unit tests covering all scenarios
- All existing tests still passing (36 location tests, 267 total converter tests)

**Current Behavior:**
`managingOrganization` field is now properly populated from scopingEntity when Organization resource is registered.

**Original Required Change:**

Add method to infer managing organization from context:

```python
def _get_managing_organization_reference(
    self,
    service_delivery_location,
    encounter_ref: str | None = None,
    document_context: dict | None = None
) -> dict | None:
    """Infer managing organization from available context.

    Priority:
    1. From encounter.serviceProvider if encounter_ref available
    2. From document custodian
    3. From location's participant/representedOrganization
    4. None if no organization found

    Args:
        service_delivery_location: C-CDA location element
        encounter_ref: Reference to encounter if available
        document_context: Document-level context with custodian

    Returns:
        Organization reference dict or None
    """
    # 1. Try to get from encounter's serviceProvider
    if encounter_ref and self.reference_registry:
        org_ref = self.reference_registry.get_organization_for_encounter(encounter_ref)
        if org_ref:
            return {"reference": org_ref}

    # 2. Try document custodian
    if document_context and document_context.get("custodian_org_id"):
        return {"reference": f"Organization/{document_context['custodian_org_id']}"}

    # 3. Try location participant's organization
    if hasattr(service_delivery_location, 'participant'):
        for participant in service_delivery_location.participant:
            if hasattr(participant, 'participantRole'):
                role = participant.participantRole
                if hasattr(role, 'scopingEntity') and role.scopingEntity:
                    org_id = self._extract_organization_id(role.scopingEntity)
                    if org_id:
                        return {"reference": f"Organization/{org_id}"}

    return None
```

Add to `convert()` method around line 175:

```python
# managingOrganization (US Core Must Support)
managing_org = self._get_managing_organization_reference(
    service_delivery_location,
    encounter_ref=self.context.get("encounter_ref"),
    document_context=self.context.get("document")
)
if managing_org:
    fhir_location["managingOrganization"] = managing_org
```

**Test Coverage Required:**
- Test with encounter context (serviceProvider)
- Test with document custodian
- Test with location participant organization
- Test with no managing organization (should omit field)

**Acceptance Criteria:**
- US Core Location profile validation passes
- managingOrganization populated when organization data available
- Field omitted (not null) when no organization found

---

### 2. CarePlan: Fix activity.outcomeReference Associations

**Priority:** 🔴 CRITICAL
**File:** `ccda_to_fhir/converters/careplan.py`
**Issue:** All outcomes incorrectly linked to all activities - violates semantic correctness
**Estimated Effort:** 3-4 hours

**Current Behavior (Lines 218-221):**
```python
# TODO: Implement proper outcome-to-activity linking based on entryRelationship
if outcome_refs:
    for activity_detail in activity_details:
        activity_detail["outcomeReference"] = outcome_refs
```

This adds ALL outcomes to ALL activities, which is semantically incorrect.

**Required Change:**

Replace with proper entryRelationship-based linking:

```python
def _link_outcomes_to_activities(
    self,
    interventions: list,
    outcomes: list,
    section
) -> list[dict]:
    """Link outcome observations to their parent intervention activities.

    Uses entryRelationship with typeCode='GEVL' (evaluates) to determine
    which outcomes belong to which activities.

    Args:
        interventions: List of intervention entry elements
        outcomes: List of outcome observation entry elements
        section: The section containing the entries

    Returns:
        List of activity detail dicts with proper outcomeReference arrays
    """
    activity_details = []

    for intervention in interventions:
        activity_ref = self._create_intervention_reference(intervention)
        if not activity_ref:
            continue

        activity_detail = {"reference": activity_ref}

        # Find outcomes linked to this intervention via entryRelationship
        linked_outcomes = []

        if hasattr(intervention, 'entry_relationship'):
            for rel in intervention.entry_relationship:
                # typeCode='GEVL' means "evaluates" - outcome evaluates the intervention
                if hasattr(rel, 'type_code') and rel.type_code == 'GEVL':
                    if hasattr(rel, 'observation'):
                        outcome_id = self._get_observation_id(rel.observation)
                        # Check if this outcome is in our outcomes list
                        for outcome_entry in outcomes:
                            if self._get_observation_id(outcome_entry) == outcome_id:
                                outcome_ref = self._create_outcome_reference(outcome_entry)
                                if outcome_ref:
                                    linked_outcomes.append(outcome_ref)

        # Only add outcomeReference if there are linked outcomes
        if linked_outcomes:
            activity_detail["outcomeReference"] = linked_outcomes

        activity_details.append(activity_detail)

    return activity_details
```

**Helper Methods Needed:**

```python
def _get_observation_id(self, observation) -> str | None:
    """Extract identifier from observation for matching."""
    if hasattr(observation, 'id') and observation.id:
        if hasattr(observation.id, 'root'):
            return observation.id.root
    return None

def _create_outcome_reference(self, outcome_entry) -> dict | None:
    """Create reference to Observation outcome resource."""
    # Check if Observation resource exists in registry
    outcome_id = self._generate_observation_id(outcome_entry)
    if self.reference_registry.has_resource("Observation", outcome_id):
        return {"reference": f"Observation/{outcome_id}"}
    return None
```

**Test Coverage Required:**
- Test activity with single outcome (GEVL relationship)
- Test activity with multiple outcomes
- Test activity with no outcomes
- Test multiple activities with different outcomes
- Test outcomes without GEVL relationship (should not link)

**Acceptance Criteria:**
- Outcomes only linked to activities with GEVL entryRelationship
- Activities without outcomes have no outcomeReference field
- No outcome appears in multiple activities unless properly linked
- All existing tests still pass

---

## 🟠 HIGH PRIORITY - Should Fix Soon (4 items)

### 3. CarePlan: Add Comprehensive Unit Tests

**Priority:** 🟠 HIGH
**File:** `tests/unit/converters/test_careplan.py` (NEW FILE)
**Issue:** Only 1 integration test - critical gap in test coverage
**Estimated Effort:** 4-6 hours

**Current State:**
- 1 integration test in `tests/integration/test_careplan_simple.py`
- No unit tests for CarePlanConverter class
- High risk of regressions

**Required Tests (Minimum 25 tests):**

```python
"""Unit tests for CarePlan converter."""

class TestCarePlanConverter:
    """Test CarePlan resource conversion."""

    # Basic conversion (3 tests)
    def test_basic_care_plan_conversion(self):
        """Test basic CarePlan creation from Care Plan Document."""

    def test_care_plan_with_minimal_data(self):
        """Test CarePlan with only required elements."""

    def test_care_plan_with_complete_data(self):
        """Test CarePlan with all optional elements."""

    # Identifier mapping (2 tests)
    def test_identifier_mapping(self):
        """Test document.setId maps to CarePlan.identifier."""

    def test_identifier_with_version(self):
        """Test identifier includes versionNumber."""

    # Status mapping (4 tests)
    def test_status_defaults_to_active(self):
        """Test status defaults to 'active'."""

    def test_status_from_document_context(self):
        """Test status inferred from document authentication."""

    def test_status_from_intervention_status(self):
        """Test status inferred from intervention activities."""

    def test_status_completed_when_period_ended(self):
        """Test status 'completed' when period.end in past."""

    # Subject mapping (3 tests)
    def test_subject_from_registry(self):
        """Test subject from ReferenceRegistry."""

    def test_subject_from_document_recordtarget(self):
        """Test subject fallback to document recordTarget."""

    def test_subject_placeholder_when_missing(self):
        """Test subject uses placeholder when unavailable."""

    # Period mapping (3 tests)
    def test_period_from_service_event(self):
        """Test period extracted from serviceEvent.effectiveTime."""

    def test_period_with_only_start_date(self):
        """Test period with only effectiveTime.low."""

    def test_period_missing(self):
        """Test CarePlan without period when not available."""

    # Author and contributor (4 tests)
    def test_author_from_first_author(self):
        """Test author from document.author[0]."""

    def test_contributor_from_all_authors(self):
        """Test contributor includes all authors."""

    def test_contributor_includes_performers(self):
        """Test contributor includes serviceEvent.performer."""

    def test_contributor_deduplication(self):
        """Test same practitioner not duplicated in contributors."""

    # Addresses (health concerns) (2 tests)
    def test_addresses_health_concern_references(self):
        """Test addresses field includes Condition references."""

    def test_addresses_empty_when_no_concerns(self):
        """Test addresses omitted when no health concerns."""

    # Goal references (2 tests)
    def test_goal_references(self):
        """Test goal field includes Goal resource references."""

    def test_goal_empty_when_no_goals(self):
        """Test goal omitted when no goals."""

    # Activity mapping (5 tests)
    def test_activity_from_interventions(self):
        """Test activity.reference from intervention section."""

    def test_activity_outcome_linking(self):
        """Test activity.outcomeReference linked via GEVL relationship."""

    def test_activity_multiple_outcomes(self):
        """Test activity with multiple outcome references."""

    def test_activity_no_outcomes(self):
        """Test activity without outcomeReference when no GEVL."""

    def test_multiple_activities_different_outcomes(self):
        """Test multiple activities each with correct outcomes."""

    # Narrative (2 tests)
    def test_narrative_generation(self):
        """Test text.div generated from sections."""

    def test_narrative_status_generated(self):
        """Test text.status is 'generated'."""

    # Validation (3 tests)
    def test_validation_requires_care_plan_document(self):
        """Test ValueError when not Care Plan Document."""

    def test_validation_template_id_required(self):
        """Test ValueError when template ID missing."""

    def test_validation_service_event_required(self):
        """Test ValueError when serviceEvent missing."""

    # US Core profile (2 tests)
    def test_us_core_profile_in_meta(self):
        """Test US Core CarePlan profile URL in meta."""

    def test_category_assess_plan(self):
        """Test category includes 'assess-plan' from US Core."""
```

**Acceptance Criteria:**
- Minimum 25 unit tests added
- All tests passing
- Code coverage >90% for careplan.py
- Edge cases covered (missing data, nullFlavor, etc.)

---

### 4. ServiceRequest: Add nullFlavor Check for statusCode

**Priority:** 🟠 HIGH
**File:** `ccda_to_fhir/converters/service_request.py`
**Issue:** statusCode with nullFlavor="UNK" should map to status "unknown"
**Estimated Effort:** 30 minutes

**Current Code (Lines 256-258):**
```python
if not status_code or not status_code.code:
    # Default to active for planned procedures
    return FHIRCodes.ServiceRequestStatus.ACTIVE
```

**Required Change:**

```python
def _map_status(self, status_code) -> str:
    """Map C-CDA status code to FHIR ServiceRequest status.

    Handles nullFlavor per C-CDA on FHIR IG ConceptMap CF-NullFlavorDataAbsentReason.

    Args:
        status_code: The C-CDA status code

    Returns:
        FHIR ServiceRequest status code
    """
    if not status_code:
        return FHIRCodes.ServiceRequestStatus.ACTIVE

    # Check for nullFlavor - per C-CDA on FHIR IG
    if hasattr(status_code, 'null_flavor') and status_code.null_flavor:
        null_flavor_upper = status_code.null_flavor.upper()
        if null_flavor_upper == 'UNK':
            return FHIRCodes.ServiceRequestStatus.UNKNOWN
        # For planned procedures, other nullFlavors default to active
        return FHIRCodes.ServiceRequestStatus.ACTIVE

    if not status_code.code:
        return FHIRCodes.ServiceRequestStatus.ACTIVE

    ccda_status = status_code.code.lower()
    return SERVICE_REQUEST_STATUS_TO_FHIR.get(
        ccda_status, FHIRCodes.ServiceRequestStatus.ACTIVE
    )
```

**Test Coverage Required:**

Add to `tests/unit/converters/test_service_request.py` (NEW FILE):

```python
def test_status_null_flavor_unk():
    """Test statusCode with nullFlavor='UNK' maps to unknown."""
    procedure = create_planned_procedure(
        status_code={'nullFlavor': 'UNK'}
    )
    service_request = converter.convert(procedure)
    assert service_request['status'] == 'unknown'

def test_status_null_flavor_other():
    """Test other nullFlavors default to active."""
    procedure = create_planned_procedure(
        status_code={'nullFlavor': 'NI'}
    )
    service_request = converter.convert(procedure)
    assert service_request['status'] == 'active'
```

**Acceptance Criteria:**
- nullFlavor="UNK" → status "unknown"
- Other nullFlavors → status "active" (default for planned procedures)
- Missing statusCode → status "active"
- Tests added and passing

---

### 5. ServiceRequest: Add Integration Tests

**Priority:** 🟠 HIGH
**File:** `tests/integration/test_service_request.py` (NEW FILE)
**Issue:** No dedicated tests for ServiceRequest converter
**Estimated Effort:** 2-3 hours

**Required Tests:**

```python
"""Integration tests for ServiceRequest converter."""

def test_planned_procedure_to_service_request():
    """Test PlannedProcedure template converts to ServiceRequest."""
    # Use sample C-CDA with PlannedProcedure

def test_procedure_activity_act_to_service_request():
    """Test ProcedureActivityAct template converts to ServiceRequest."""

def test_service_request_with_performer():
    """Test ServiceRequest.performer from C-CDA performer."""

def test_service_request_with_priority():
    """Test ServiceRequest.priority from priorityCode."""

def test_service_request_with_reason():
    """Test ServiceRequest.reasonCode and reasonReference."""

def test_service_request_with_body_site():
    """Test ServiceRequest.bodySite from targetSiteCode."""

def test_service_request_category_inference():
    """Test category inferred from code system."""

def test_service_request_rejects_event_mood():
    """Test ValueError when moodCode='EVN' (should be Procedure)."""

def test_service_request_rejects_goal_mood():
    """Test ValueError when moodCode='GOL' (should be Goal)."""
```

**Acceptance Criteria:**
- Minimum 9 integration tests added
- Tests use realistic C-CDA XML samples
- All conversion paths tested
- Validation errors tested

---

### 6. Device: Add version and type Fields for EHR Systems

**Priority:** 🟠 HIGH
**File:** `ccda_to_fhir/converters/device.py`
**Issue:** Missing version and type mapping for assignedAuthoringDevice
**Estimated Effort:** 2 hours

**Current Behavior:**
- `softwareName` only maps to `deviceName`
- EHR devices missing `type` code (SNOMED 706689003)
- `version` array not populated

**Required Changes:**

1. **Extract version from softwareName** (around line 200):

```python
def _extract_device_version(self, software_name: str | None) -> list[dict] | None:
    """Extract version information from software name.

    Attempts to parse version number from software name string.
    Common patterns: "EHR System v2.1", "MyEHR 3.0.1", "System (version 1.5)"

    Args:
        software_name: The software name string

    Returns:
        List of version dicts or None
    """
    if not software_name:
        return None

    import re

    # Pattern matches: v1.2, version 1.2, (1.2), 1.2.3, etc.
    version_patterns = [
        r'v\.?\s*(\d+(?:\.\d+)*)',  # v1.2 or v.1.2
        r'version\s+(\d+(?:\.\d+)*)',  # version 1.2
        r'\((\d+(?:\.\d+)*)\)',  # (1.2)
        r'\s(\d+\.\d+(?:\.\d+)?)\s*$',  # 1.2.3 at end
    ]

    for pattern in version_patterns:
        match = re.search(pattern, software_name, re.IGNORECASE)
        if match:
            version_number = match.group(1)
            return [{
                "type": {"text": "software"},
                "value": version_number
            }]

    return None
```

2. **Add inferred type for EHR systems** (in `_create_ehr_device` method):

```python
# Add after deviceName mapping
device["type"] = {
    "coding": [{
        "system": "http://snomed.info/sct",
        "code": "706689003",
        "display": "Electronic health record"
    }],
    "text": "Electronic Health Record System"
}

# Add version if extractable
version = self._extract_device_version(software_name)
if version:
    device["version"] = version
```

**Test Coverage Required:**

```python
def test_ehr_device_version_extraction():
    """Test version extracted from softwareName."""

def test_ehr_device_type_code():
    """Test EHR device has SNOMED type code 706689003."""

def test_ehr_device_version_patterns():
    """Test various version string patterns."""
```

**Acceptance Criteria:**
- Version extracted from softwareName when pattern matches
- EHR devices have type.coding with SNOMED 706689003
- Version format follows FHIR Device.version structure
- Tests passing

---

## 🟡 MEDIUM PRIORITY - Enhance When Possible (6 items)

### 7. CarePlan: Implement Narrative Generation

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/careplan.py`
**Issue:** Minimal placeholder narrative - US Core requires meaningful text
**Estimated Effort:** 3-4 hours

**Current Code (Lines 227-232):**
```python
# TODO: Implement narrative generation from Health Concerns, Goals, Interventions
fhir_careplan["text"] = {
    "status": "generated",
    "div": '<div xmlns="http://www.w3.org/1999/xhtml"><p>Care Plan</p></div>'
}
```

**Required Implementation:**

```python
def _generate_narrative(
    self,
    care_plan_title: str | None,
    period: dict | None,
    health_concerns: list,
    goals: list,
    interventions: list
) -> dict:
    """Generate FHIR narrative from Care Plan sections.

    Creates meaningful XHTML narrative summarizing the care plan.

    Args:
        care_plan_title: Document title
        period: Care plan period
        health_concerns: List of health concern entries
        goals: List of goal entries
        interventions: List of intervention entries

    Returns:
        FHIR text dict with status and div
    """
    lines = ['<div xmlns="http://www.w3.org/1999/xhtml">']

    # Title
    if care_plan_title:
        lines.append(f'<h2>{self._escape_html(care_plan_title)}</h2>')

    # Period
    if period:
        period_text = self._format_period_text(period)
        lines.append(f'<p><strong>Period:</strong> {period_text}</p>')

    # Health Concerns section
    if health_concerns:
        lines.append('<h3>Health Concerns</h3>')
        lines.append('<ul>')
        for concern in health_concerns:
            concern_text = self._extract_concern_text(concern)
            if concern_text:
                lines.append(f'<li>{self._escape_html(concern_text)}</li>')
        lines.append('</ul>')

    # Goals section
    if goals:
        lines.append('<h3>Goals</h3>')
        lines.append('<ul>')
        for goal in goals:
            goal_text = self._extract_goal_text(goal)
            if goal_text:
                lines.append(f'<li>{self._escape_html(goal_text)}</li>')
        lines.append('</ul>')

    # Interventions section
    if interventions:
        lines.append('<h3>Planned Interventions</h3>')
        lines.append('<ul>')
        for intervention in interventions:
            intervention_text = self._extract_intervention_text(intervention)
            if intervention_text:
                lines.append(f'<li>{self._escape_html(intervention_text)}</li>')
        lines.append('</ul>')

    lines.append('</div>')

    return {
        "status": "generated",
        "div": '\n'.join(lines)
    }
```

**Helper Methods:**

```python
def _escape_html(self, text: str) -> str:
    """Escape HTML special characters."""
    import html
    return html.escape(text)

def _format_period_text(self, period: dict) -> str:
    """Format period as readable text."""
    start = period.get('start', 'Unknown')
    end = period.get('end', 'Ongoing')
    return f"{start} to {end}"

def _extract_concern_text(self, concern_entry) -> str | None:
    """Extract displayable text from health concern."""
    # Extract from code.displayName or originalText

def _extract_goal_text(self, goal_entry) -> str | None:
    """Extract displayable text from goal."""
    # Extract from code.displayName or text

def _extract_intervention_text(self, intervention_entry) -> str | None:
    """Extract displayable text from intervention."""
    # Extract from code.displayName or originalText
```

**Test Coverage:**

```python
def test_narrative_includes_health_concerns():
    """Test narrative includes health concerns section."""

def test_narrative_includes_goals():
    """Test narrative includes goals section."""

def test_narrative_includes_interventions():
    """Test narrative includes interventions section."""

def test_narrative_html_escaped():
    """Test special characters are HTML escaped."""
```

**Acceptance Criteria:**
- Narrative includes meaningful content from sections
- XHTML is well-formed and valid
- HTML special characters properly escaped
- Status is "generated"
- US Core validators accept the narrative

---

### 8. CarePlan: Enhance Status Determination

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/careplan.py`
**Issue:** Status always defaults to "active"
**Estimated Effort:** 2 hours

**Current Code (Lines 254-266):**
```python
# ServiceEvent doesn't have statusCode in C-CDA, infer from context
return "active"
```

**Required Implementation:**

```python
def _determine_status(
    self,
    service_event,
    period: dict | None,
    interventions: list,
    document
) -> str:
    """Determine CarePlan status from available context.

    Status hierarchy:
    1. If period.end in past → completed
    2. If all interventions completed → completed
    3. If document authenticated → active
    4. If any intervention cancelled → revoked
    5. Default → active

    Args:
        service_event: The serviceEvent element
        period: Care plan period
        interventions: List of intervention entries
        document: Clinical document

    Returns:
        FHIR CarePlan status code
    """
    from datetime import datetime, timezone

    # Check if period has ended
    if period and period.get('end'):
        try:
            end_date = datetime.fromisoformat(period['end'].replace('Z', '+00:00'))
            if end_date < datetime.now(timezone.utc):
                return "completed"
        except (ValueError, AttributeError):
            pass

    # Check intervention statuses
    if interventions:
        intervention_statuses = [
            self._get_intervention_status(interv) for interv in interventions
        ]

        # If all completed → care plan completed
        if intervention_statuses and all(s == 'completed' for s in intervention_statuses):
            return "completed"

        # If any cancelled → care plan revoked
        if 'cancelled' in intervention_statuses:
            return "revoked"

    # Check if document is authenticated (finalized)
    if hasattr(document, 'legal_authenticator') and document.legal_authenticator:
        return "active"

    # Default
    return "active"

def _get_intervention_status(self, intervention_entry) -> str | None:
    """Extract status from intervention entry."""
    if hasattr(intervention_entry, 'statusCode'):
        code = intervention_entry.statusCode.code
        # Map common C-CDA status codes
        status_map = {
            'completed': 'completed',
            'active': 'active',
            'cancelled': 'cancelled',
            'suspended': 'suspended'
        }
        return status_map.get(code.lower())
    return None
```

**Test Coverage:**

```python
def test_status_completed_when_period_ended():
    """Test status 'completed' when period.end in past."""

def test_status_completed_when_all_interventions_completed():
    """Test status 'completed' when all interventions completed."""

def test_status_revoked_when_intervention_cancelled():
    """Test status 'revoked' when any intervention cancelled."""

def test_status_active_when_authenticated():
    """Test status 'active' when document authenticated."""
```

**Acceptance Criteria:**
- Status accurately reflects care plan state
- Past period.end → "completed"
- All interventions completed → "completed"
- Cancelled interventions → "revoked"
- Tests passing

---

### 9. DocumentReference: Fix format.system URI

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/document_reference.py`
**Issue:** Using non-standard IHE URI instead of HL7 standard
**Estimated Effort:** 15 minutes

**Current Code (Line 708):**
```python
"system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem"
```

**Required Change:**
```python
"system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes"
```

**Full Context (Lines 707-711):**
```python
"format": {
    "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
    "code": format_code,
    "display": format_display
}
```

**Test Coverage:**
Update existing test to verify system URI:

```python
def test_format_uses_hl7_system():
    """Test format.system uses HL7 standard URI."""
    doc_ref = converter.convert(clinical_document)
    format_coding = doc_ref["content"][0]["format"]
    assert format_coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes"
```

**Acceptance Criteria:**
- System URI uses HL7 standard
- Existing tests updated
- FHIR validation passes

---

### 10. Device: Add owner Reference

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/device.py`
**Issue:** Not mapping representedOrganization to Device.owner
**Estimated Effort:** 1 hour

**Current State:**
Lines 84-86 note that `asMaintainedEntity` is ignored.

**Required Implementation:**

```python
def _extract_device_owner(
    self,
    participant_role,
    reference_registry
) -> dict | None:
    """Extract device owner organization reference.

    Maps from participantRole.scopingEntity (organization maintaining device).

    Args:
        participant_role: C-CDA participant role
        reference_registry: Reference registry for Organization lookup

    Returns:
        Organization reference dict or None
    """
    if not hasattr(participant_role, 'scopingEntity'):
        return None

    scoping_entity = participant_role.scopingEntity
    if not scoping_entity:
        return None

    # Extract organization ID
    org_id = None
    if hasattr(scoping_entity, 'id') and scoping_entity.id:
        org_id = self._generate_organization_id(scoping_entity.id)

    # Check if Organization resource exists
    if org_id and reference_registry.has_resource("Organization", org_id):
        return {"reference": f"Organization/{org_id}"}

    return None
```

Add to convert method:

```python
# owner (organization maintaining device)
owner = self._extract_device_owner(participant_role, reference_registry)
if owner:
    device["owner"] = owner
```

**Test Coverage:**

```python
def test_device_owner_from_scoping_entity():
    """Test Device.owner from scopingEntity."""

def test_device_owner_missing_when_no_entity():
    """Test owner omitted when scopingEntity missing."""
```

**Acceptance Criteria:**
- owner mapped when scopingEntity present
- Organization reference validated via registry
- Field omitted when no scoping entity

---

### 11. Location: Add physicalType Mapping

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/location.py`
**Issue:** physicalType not populated
**Estimated Effort:** 1-2 hours

**Required Implementation:**

```python
def _infer_physical_type(self, location_code) -> dict | None:
    """Infer physical type from location type code.

    Maps common location codes to physical type codes.
    Uses http://terminology.hl7.org/CodeSystem/location-physical-type

    Args:
        location_code: The location type code

    Returns:
        Physical type CodeableConcept or None
    """
    if not location_code or not hasattr(location_code, 'code'):
        return None

    # Mapping from common location codes to physical types
    physical_type_map = {
        # HSLOC codes
        '1160-1': 'bu',  # Burn Unit → Building
        '1025-6': 'ro',  # Cardiac Catheterization Lab → Room
        '1026-4': 'ro',  # Coronary Care Unit → Room
        '1029-8': 'ro',  # Emergency Room → Room
        '1073-6': 'ro',  # ICU → Room
        # RoleCode
        'HOSP': 'bu',   # Hospital → Building
        'COMM': 'bu',   # Community Location → Building
        'SCHOOL': 'bu', # School → Building
        'PTRES': 'ho',  # Patient's Residence → House
        'WORK': 'bu',   # Work Site → Building
        'AMB': 've',    # Ambulance → Vehicle
    }

    code_value = location_code.code
    physical_type_code = physical_type_map.get(code_value)

    if not physical_type_code:
        return None

    # Physical type display names
    display_map = {
        'bu': 'Building',
        'ro': 'Room',
        'ho': 'House',
        've': 'Vehicle',
        'wa': 'Ward',
        'co': 'Corridor',
        'bd': 'Bed',
        'area': 'Area'
    }

    return {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
            "code": physical_type_code,
            "display": display_map.get(physical_type_code)
        }]
    }
```

**Test Coverage:**

```python
def test_physical_type_inferred_from_code():
    """Test physicalType inferred from location type."""

def test_physical_type_hospital_building():
    """Test hospital location → building physical type."""

def test_physical_type_patient_home():
    """Test patient residence → house physical type."""
```

**Acceptance Criteria:**
- Common location codes map to appropriate physical types
- Uses standard FHIR location-physical-type system
- Field omitted when cannot infer

---

### 12. Location: Enhance mode Detection

**Priority:** 🟡 MEDIUM
**File:** `ccda_to_fhir/converters/location.py`
**Issue:** Mode always "instance", should detect "kind" for patient homes
**Estimated Effort:** 1 hour

**Current Code (Line 86):**
```python
fhir_location["mode"] = "instance"
```

**Required Implementation:**

```python
def _determine_mode(self, location_code) -> str:
    """Determine location mode (instance vs kind).

    - instance: Specific location (Room 123, specific hospital)
    - kind: Type of location (patient's home, ambulance)

    Args:
        location_code: The location type code

    Returns:
        "instance" or "kind"
    """
    if not location_code or not hasattr(location_code, 'code'):
        return "instance"

    # Codes that represent types rather than specific instances
    kind_codes = {
        'PTRES',  # Patient's Residence (any patient home)
        'AMB',    # Ambulance (any ambulance)
        'WORK',   # Work Site (any workplace)
        'SCHOOL', # School (any school)
    }

    if location_code.code in kind_codes:
        return "kind"

    return "instance"
```

**Test Coverage:**

```python
def test_mode_kind_for_patient_home():
    """Test mode='kind' for patient residence."""

def test_mode_kind_for_ambulance():
    """Test mode='kind' for ambulance."""

def test_mode_instance_for_specific_location():
    """Test mode='instance' for specific hospital/room."""
```

**Acceptance Criteria:**
- Patient homes, ambulances → mode "kind"
- Specific locations → mode "instance"
- Default to "instance" when uncertain

---

## 🟢 LOW PRIORITY - Nice to Have (3 items)

### 13. DocumentReference: Implement docStatus Inference

**Priority:** 🟢 LOW
**File:** `ccda_to_fhir/converters/document_reference.py`
**Issue:** docStatus not populated, could infer from authenticators
**Estimated Effort:** 1 hour

**Current Code (Lines 73-76):**
```python
# docStatus: Could be inferred from authenticator presence
# - If legalAuthenticator present: "final"
# - If authenticator present but not legal: "preliminary"
# Not critical for current implementation
```

**Required Implementation:**

```python
def _infer_doc_status(self, clinical_document) -> str | None:
    """Infer document status from authenticator presence.

    Logic:
    - legalAuthenticator present → "final"
    - authenticator present (not legal) → "preliminary"
    - Neither present → None (omit field)

    Args:
        clinical_document: The C-CDA clinical document

    Returns:
        docStatus code or None
    """
    # Check for legal authenticator (document is finalized)
    if hasattr(clinical_document, 'legal_authenticator') and clinical_document.legal_authenticator:
        return "final"

    # Check for regular authenticator (document is authenticated but not finalized)
    if hasattr(clinical_document, 'authenticator') and clinical_document.authenticator:
        return "preliminary"

    # No authentication → don't specify status
    return None
```

Add to convert method (around line 130):

```python
# docStatus (inferred from authentication)
doc_status = self._infer_doc_status(clinical_document)
if doc_status:
    fhir_doc_ref["docStatus"] = doc_status
```

**Test Coverage:**

```python
def test_doc_status_final_with_legal_authenticator():
    """Test docStatus='final' when legalAuthenticator present."""

def test_doc_status_preliminary_with_authenticator():
    """Test docStatus='preliminary' when authenticator present."""

def test_doc_status_omitted_without_authenticators():
    """Test docStatus omitted when no authenticators."""
```

**Acceptance Criteria:**
- Legal authenticator → docStatus "final"
- Regular authenticator → docStatus "preliminary"
- No authenticator → field omitted
- Tests passing

---

### 14. ServiceRequest: Add Integration with Full C-CDA Document

**Priority:** 🟢 LOW
**File:** `tests/integration/test_service_request_full_document.py` (NEW)
**Issue:** Current tests use isolated elements, need full document test
**Estimated Effort:** 2 hours

**Required Test:**

Use a complete C-CDA document with Plan of Care section containing planned procedures.

```python
"""Integration test for ServiceRequest with full C-CDA document."""

def test_full_ccd_with_planned_procedures():
    """Test ServiceRequest conversion from complete CCD with Plan of Care."""
    # Load sample CCD with Plan of Care section
    # Verify ServiceRequest resources created
    # Verify references to patient, encounter, practitioners
    # Verify category inference works in context
    # Verify all sections processed correctly
```

**Acceptance Criteria:**
- Test uses realistic complete C-CDA document
- All ServiceRequest resources found in bundle
- References properly resolve
- No placeholder references

---

### 15. MedicationDispense: Add Location Resource for Pharmacy

**Priority:** 🟢 LOW
**File:** `ccda_to_fhir/converters/medication_dispense.py`
**Issue:** Pharmacy organization not converted to Location resource
**Estimated Effort:** 2-3 hours

**Enhancement:**

When performer has `representedOrganization`, create a Location resource for the pharmacy.

**Implementation:**

```python
def _create_pharmacy_location(
    self,
    organization,
    reference_registry
) -> str | None:
    """Create Location resource for pharmacy organization.

    Args:
        organization: The representedOrganization element
        reference_registry: Reference registry

    Returns:
        Location reference or None
    """
    if not organization:
        return None

    location_id = self._generate_location_id(organization)

    # Check if already created
    if reference_registry.has_resource("Location", location_id):
        return f"Location/{location_id}"

    # Create Location resource
    location = {
        "resourceType": "Location",
        "id": location_id,
        "status": "active",
        "mode": "instance",
        "type": [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "PHARM",
                "display": "Pharmacy"
            }]
        }]
    }

    # Add name from organization
    if hasattr(organization, 'name') and organization.name:
        location["name"] = organization.name

    # Add address
    if hasattr(organization, 'addr') and organization.addr:
        location["address"] = self._convert_address(organization.addr)

    # Add telecom
    if hasattr(organization, 'telecom') and organization.telecom:
        location["telecom"] = self._convert_telecom_list(organization.telecom)

    # Register Location resource
    reference_registry.register_resource(location)

    return f"Location/{location_id}"
```

**Acceptance Criteria:**
- Location created for pharmacy organizations
- Location properly typed as PHARM
- Location registered and referenced
- Tests added

---

## 📈 Summary Statistics

| Priority | Count | Est. Total Hours |
|----------|-------|------------------|
| 🔴 Critical | 2 | 5-6 hours |
| 🟠 High | 4 | 9-13 hours |
| 🟡 Medium | 6 | 10-14 hours |
| 🟢 Low | 3 | 5-6 hours |
| **Total** | **15** | **29-39 hours** |

---

## 🎯 Recommended Implementation Order

### Sprint 1 (Critical + High Priority)
1. Location: Add managingOrganization (1-2 hrs)
2. ServiceRequest: Add nullFlavor check (30 min)
3. CarePlan: Fix outcome associations (3-4 hrs)
4. CarePlan: Add unit tests (4-6 hrs)
5. ServiceRequest: Add integration tests (2-3 hrs)
6. Device: Add version/type fields (2 hrs)

**Total:** ~13-18 hours

### Sprint 2 (Medium Priority)
7. CarePlan: Implement narrative generation (3-4 hrs)
8. CarePlan: Enhance status determination (2 hrs)
9. DocumentReference: Fix format URI (15 min)
10. Device: Add owner reference (1 hr)
11. Location: Add physicalType (1-2 hrs)
12. Location: Enhance mode detection (1 hr)

**Total:** ~8-10 hours

### Sprint 3 (Low Priority - Optional)
13. DocumentReference: Implement docStatus (1 hr)
14. ServiceRequest: Full document test (2 hrs)
15. MedicationDispense: Pharmacy Location (2-3 hrs)

**Total:** ~5-6 hours

---

## ✅ Acceptance Criteria (Overall)

Before marking this document as complete:

- [ ] All 2 Critical items resolved
- [ ] At least 3 of 4 High priority items resolved
- [ ] All new code has test coverage >90%
- [ ] All 1074+ existing tests still passing
- [ ] US Core validation passes for all converters
- [ ] FHIR R4 validation passes for all resources
- [ ] No regressions introduced
- [ ] Code review completed for all changes
- [ ] Documentation updated where needed

---

**Document Version:** 1.0
**Next Review:** After Sprint 1 completion
