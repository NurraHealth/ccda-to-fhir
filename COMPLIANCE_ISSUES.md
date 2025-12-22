# Standards Compliance Issues

**Review Date:** 2025-12-22
**Review Scope:** CareTeam, MedicationDispense converters
**Test Status:** ✅ All 1257 tests passing - no regressions

## Overview

This document tracks standards compliance gaps found during comprehensive review against C-CDA, FHIR R4, and US Core specifications.

**Overall Assessment:** Implementations are functional with excellent test coverage. The main issue is MedicationDispense not extracting the `supply.code` element which contains the actual dispense status per C-CDA spec. Other issues involve intentional leniency for real-world data compatibility.

**Design Philosophy:** The implementation favors robustness (accepting imperfect data) over strict validation (rejecting non-compliant data). This is a valid engineering choice but deviates from strict spec compliance.

---

## Critical Priority Issues

### ~~CRITICAL-1: MedicationDispense - Not Extracting supply.code Element~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** Critical
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:200-264`

**Issue:**
The converter was mapping `supply.statusCode` to `MedicationDispense.status`, but per C-CDA spec:
- **statusCode** is FIXED to "completed" (always the same value)
- **code** element (1..1 required) contains the actual dispense status from MedicationDispenseStatusCodes value set
- The code element was **NOT extracted at all** in the implementation

**Fix Applied:**
Updated `_determine_status()` method to:
1. Extract status from `supply.code` instead of `supply.statusCode`
2. Support both FHIR codes (direct mapping) and legacy ActStatus codes (backwards compatibility)
3. Validate that `statusCode` is "completed" if present (with warning if not)
4. Warn if `code` element is missing
5. Updated all tests to use `supply.code` element

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py:200-264`
- Updated: `tests/unit/converters/test_medication_dispense.py` (all test fixtures)
- Test Status: ✅ All 1234 tests passing - no regressions

**References:**
- [C-CDA Medication Dispense Spec](https://build.fhir.org/ig/HL7/CDA-ccda-2.1-sd/StructureDefinition-MedicationDispense.html)
- [C-CDA Example](https://github.com/HL7/C-CDA-Examples/blob/master/Guide%20Examples/Medication%20Dispense%20(V2)_2.16.840.1.113883.10.20.22.4.18/Medication%20Dispense%20(V2)%20Example.xml)

---

### ~~CRITICAL-2: MedicationDispense - Location.identifier Not Populated~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** High
**Component:** MedicationDispense Converter - Location creation
**Location:** `ccda_to_fhir/converters/medication_dispense.py:616-626`

**Issue:**
When creating Location resources for pharmacies, `identifier` field was not populated even when the source organization had identifiers.

**US Core Must Support Rule:**
> "Must be supported if the data is present in the sending system"

**Fix Applied:**
Added identifier population from organization identifiers to Location resource creation:
```python
# Add identifiers from organization (US Core Must Support)
# Per US Core: "Must be supported if the data is present in the sending system"
if hasattr(organization, "id") and organization.id:
    identifiers = []
    for id_elem in organization.id:
        if id_elem.root:
            identifier = self.create_identifier(id_elem.root, id_elem.extension)
            if identifier:
                identifiers.append(identifier)
    if identifiers:
        location["identifier"] = identifiers
```

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py:616-626`
- Added test: `test_location_includes_identifiers_from_organization()`
- Test Status: ✅ All 1235 tests passing - no regressions

**References:**
- [US Core Location Profile](http://hl7.org/fhir/us/core/STU7/StructureDefinition-us-core-location.html)

---

## High Priority Issues

### ~~HIGH-1: MedicationDispense - Organization Performer Not Handled~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** High
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:370-386`

**Issue:**
When `performer/assignedEntity` represents an Organization (no assignedPerson), no performer entry was created. Only Practitioner cases were handled.

**C-CDA Spec:**
Per C-CDA Medication Dispense specification, the performer element can contain:
- `assignedPerson` - Individual pharmacist/practitioner
- `representedOrganization` - Pharmacy organization (or both)

When only `representedOrganization` is present (no `assignedPerson`), this represents an organization performer.

**FHIR Spec:**
Per FHIR R4B MedicationDispense, `performer.actor` supports Reference to:
- Practitioner | PractitionerRole | **Organization** | Patient | Device | RelatedPerson

**Fix Applied:**
Updated `_extract_performers_and_location()` method to handle organization-only performers:

1. Added `elif` branch to handle organization performers when no assignedPerson is present
2. Created new `_create_pharmacy_organization()` method to:
   - Generate Organization resource from representedOrganization
   - Use OrganizationConverter for consistent resource creation
   - Register Organization resource in reference registry
   - Return Organization ID for performer.actor reference
3. Set performer function to "finalchecker" (consistent with practitioner performers)

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py:370-386`
- Added: `_create_pharmacy_organization()` method at line 651-721
- Added tests:
  - `test_performer_with_only_organization_creates_organization_performer()`
  - `test_performer_with_both_person_and_organization()`
- Test Status: ✅ All 1237 tests passing - no regressions

**Behavior:**
- Practitioner only → Practitioner performer + Location
- Organization only → **Organization performer + Location** (newly fixed)
- Both → Practitioner performer + Location (practitioner takes precedence)

**References:**
- [C-CDA Medication Dispense Spec](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationDispense.html)
- [FHIR MedicationDispense](https://hl7.org/fhir/R4B/medicationdispense.html)
- [US Core MedicationDispense](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense)

---

### ~~HIGH-2: CareTeam - Template Extension Not Validated~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** High
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:370-386`

**Issue:**
When `performer/assignedEntity` represents an Organization (no assignedPerson), no performer entry was created. Only Practitioner cases were handled.

**C-CDA Spec:**
Per C-CDA Medication Dispense specification, the performer element can contain:
- `assignedPerson` - Individual pharmacist/practitioner
- `representedOrganization` - Pharmacy organization (or both)

When only `representedOrganization` is present (no `assignedPerson`), this represents an organization performer.

**FHIR Spec:**
Per FHIR R4B MedicationDispense, `performer.actor` supports Reference to:
- Practitioner | PractitionerRole | **Organization** | Patient | Device | RelatedPerson

**Fix Applied:**
Updated `_extract_performers_and_location()` method to handle organization-only performers:

1. Added `elif` branch to handle organization performers when no assignedPerson is present
2. Created new `_create_pharmacy_organization()` method to:
   - Generate Organization resource from representedOrganization
   - Use OrganizationConverter for consistent resource creation
   - Register Organization resource in reference registry
   - Return Organization ID for performer.actor reference
3. Set performer function to "finalchecker" (consistent with practitioner performers)

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py:370-386`
- Added: `_create_pharmacy_organization()` method at line 651-721
- Added tests:
  - `test_performer_with_only_organization_creates_organization_performer()`
  - `test_performer_with_both_person_and_organization()`
- Test Status: ✅ All 1237 tests passing - no regressions

**Behavior:**
- Practitioner only → Practitioner performer + Location
- Organization only → **Organization performer + Location** (newly fixed)
- Both → Practitioner performer + Location (practitioner takes precedence)

**References:**
- [C-CDA Medication Dispense Spec](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationDispense.html)
- [FHIR MedicationDispense](https://hl7.org/fhir/R4B/medicationdispense.html)
- [US Core MedicationDispense](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense)

---

### ~~HIGH-2: CareTeam - Template Extension Not Validated~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** High
**Component:** CareTeam Converter
**Location:** `ccda_to_fhir/converters/careteam.py:210-251, 335-401, 425-522`

**Issue:**
Template validation only checked root OID, not extension date. Applies to all three templates:
- Care Team Organizer (2.16.840.1.113883.10.20.22.4.500)
- Care Team Member Act (2.16.840.1.113883.10.20.22.4.500.1)
- Care Team Type Observation (2.16.840.1.113883.10.20.22.4.500.2)

**C-CDA Requirements:**
Per C-CDA specification, valid extensions are:
- Care Team Organizer: 2019-07-01 or 2022-06-01 (both valid)
- Care Team Member Act: 2019-07-01 or 2022-06-01 (both valid)
- Care Team Type Observation: 2019-07-01 (only version)

**Fix Applied:**
Updated template validation in three locations:

1. **Care Team Organizer (`_validate_template`)** - Strict validation:
   - Added `CARE_TEAM_ORGANIZER_EXTENSIONS = ["2019-07-01", "2022-06-01"]`
   - Validates both root and extension
   - Rejects templates without valid extension
   - Provides helpful error messages showing found vs expected

2. **Care Team Type Observation (`_extract_categories`)** - Lenient validation:
   - Added `CARE_TEAM_TYPE_OBSERVATION_EXTENSION = "2019-07-01"`
   - Validates both root and extension
   - Logs warning but continues if extension missing/invalid (real-world compatibility)
   - Still extracts category data from non-compliant observations

3. **Care Team Member Act (`_extract_participants`)** - Lenient validation:
   - Added `CARE_TEAM_MEMBER_ACT_EXTENSIONS = ["2019-07-01", "2022-06-01"]`
   - Validates both root and extension
   - Logs warning but continues if extension missing/invalid (real-world compatibility)
   - Still extracts participant data from non-compliant acts

**Implementation:**
- Modified: `ccda_to_fhir/converters/careteam.py`
  - Lines 43-56: Added extension constants
  - Lines 216-251: Updated `_validate_template()` with strict extension checking
  - Lines 335-401: Updated `_extract_categories()` with lenient extension checking
  - Lines 425-445, 495-521: Updated participant extraction with lenient extension checking
- Added comprehensive tests:
  - `test_rejects_organizer_without_extension()`
  - `test_rejects_organizer_with_invalid_extension()`
  - `test_accepts_organizer_with_2019_extension()`
  - `test_accepts_organizer_with_2022_extension()`
  - `test_accepts_member_act_with_2019_extension()`
  - `test_accepts_member_act_with_2022_extension()`
  - `test_warns_but_accepts_member_act_without_extension()`
  - `test_accepts_type_observation_with_correct_extension()`
  - `test_warns_but_accepts_type_observation_without_extension()`
- Updated all existing test fixtures to include proper extensions
- Test Status: ✅ All 1246 tests passing - no regressions

**Design Philosophy:**
- **Strict for Organizer**: Entry point validation rejects non-compliant documents
- **Lenient for Children**: Child elements warn but don't block processing (real-world compatibility)
- Accepts both valid C-CDA extension versions (2019-07-01 and 2022-06-01) where applicable

**References:**
- [C-CDA Care Team Organizer](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamOrganizer.html)
- [C-CDA Care Team Member Act](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamMemberAct.html)
- [C-CDA Care Team Type Observation](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamTypeObservation.html)

---

### ~~HIGH-3: MedicationDispense - Performer Function Assignment~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** Medium-High
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:936-1051`

**Issue:**
Performer from `supply/performer` always gets function="finalchecker", but this may not be accurate. The C-CDA performer represents the dispensing pharmacist/pharmacy, which could have different roles based on the C-CDA functionCode element.

**Fix Applied:**
Implemented intelligent performer function determination:

1. **Added `_map_participation_function_to_fhir()` method** (lines 936-980):
   - Maps C-CDA ParticipationFunction codes to FHIR MedicationDispense performer function codes
   - Supports standard codes: PCP, ADMPHYS, ATTPHYS → "finalchecker"
   - Supports pharmacy local extensions: PHARM, DISPPHARM → "finalchecker", PACKPHARM → "packager"
   - Logs debug message for unmapped codes and returns None to use default

2. **Added `_determine_performer_function()` method** (lines 982-1051):
   - Checks for C-CDA functionCode element in performer
   - Maps functionCode to FHIR codes if present
   - Falls back to context-based defaults:
     - supply.performer → "finalchecker" (dispensing pharmacist/pharmacy)
     - supply.author → "packager" (pharmacist who packaged)
   - Returns proper FHIR CodeableConcept with system, code, and display

3. **Updated performer creation** (lines 357, 369, 395):
   - Replaced hardcoded function assignments with `_determine_performer_function()` calls
   - Works for practitioner performers, organization performers, and author performers
   - Maintains backward compatibility (same defaults when functionCode absent)

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py`
  - Lines 936-1051: New methods for function determination and mapping
  - Line 357: Updated practitioner performer function
  - Line 369: Updated organization performer function
  - Line 395: Updated author performer function
- Added comprehensive tests: `tests/unit/converters/test_medication_dispense.py`
  - `test_performer_with_function_code_pcp_maps_to_finalchecker()`
  - `test_performer_with_function_code_packpharm_maps_to_packager()`
  - `test_performer_without_function_code_defaults_to_finalchecker()`
  - `test_author_without_function_code_defaults_to_packager()`
  - `test_author_with_function_code_uses_mapped_function()`
  - `test_performer_with_unknown_function_code_uses_default()`
  - `test_organization_performer_without_function_code_defaults_to_finalchecker()`
  - `test_organization_performer_with_function_code_uses_mapped_function()`
- Test Status: ✅ All 1254 tests passing (+8 new tests) - no regressions

**Behavior:**
- **With functionCode:** Maps C-CDA ParticipationFunction code to FHIR performer function
- **Without functionCode:**
  - supply.performer → "finalchecker" (default for dispensing pharmacist/pharmacy)
  - supply.author → "packager" (default for pharmacist who prepared medication)
- **Unknown functionCode:** Logs debug message and uses context-based default

**Standards Compliance:**
- Implements C-CDA performer functionCode → FHIR performer.function mapping per RIM mapping guidance
- Supports both standard ParticipationFunction codes and local pharmacy extensions
- Maintains backward compatibility with existing behavior when functionCode absent
- Provides accurate semantic mapping based on context (performer vs author)

**References:**
- [C-CDA ParticipationFunction](https://terminology.hl7.org/7.0.1/CodeSystem-v3-ParticipationFunction.html)
- [FHIR MedicationDispense Performer Function](http://hl7.org/fhir/R4B/valueset-medicationdispense-performer-function.html)
- [US Core MedicationDispense Mappings](https://build.fhir.org/ig/HL7/US-Core/StructureDefinition-us-core-medicationdispense-mappings.html)

---

## Medium Priority Issues (Intentional Leniency)

**Note:** These are C-CDA SHALL requirements that the implementation treats as optional to handle imperfect real-world data. This is an intentional design choice favoring robustness over strict compliance.

### MEDIUM-1: CareTeam - effectiveTime Not Enforced

**Severity:** Medium
**Component:** CareTeam Converter
**Location:** `ccda_to_fhir/converters/careteam.py:128-133`

**Issue:**
effectiveTime validation is incomplete. C-CDA requires effectiveTime (1..1 SHALL) but implementation treats it as optional.

**C-CDA Requirement:**
```
SHALL contain exactly one [1..1] effectiveTime
effectiveTime SHALL contain exactly one [1..1] low
```

**Current Code:**
```python
# Validate effectiveTime.low when effectiveTime is present
if organizer.effective_time:
    if hasattr(organizer.effective_time, "low"):
        if not organizer.effective_time.low:
            raise ValueError("Care Team Organizer effectiveTime.low is required when effectiveTime is present")
    elif not hasattr(organizer.effective_time, "value"):
        raise ValueError("Care Team Organizer effectiveTime must have low or value")
```

**Problem:**
This only validates when effectiveTime exists, but doesn't require effectiveTime to exist.

**Options:**

**Option 1 (Strict - breaks leniency):**
```python
if not organizer.effective_time:
    raise ValueError("Care Team Organizer effectiveTime is required (C-CDA SHALL)")
```

**Option 2 (Lenient - current approach):**
Keep as-is but document that this intentionally deviates from spec for real-world compatibility.

**Recommendation:** Document the intentional deviation rather than changing behavior.

---

### MEDIUM-2: CareTeam - statusCode Not Enforced

**Severity:** Medium
**Component:** CareTeam Converter
**Location:** `ccda_to_fhir/converters/careteam.py:278-291`

**Issue:**
C-CDA requires statusCode (1..1 SHALL) but implementation defaults to "active" when missing.

**C-CDA Requirement:**
```
SHALL contain exactly one [1..1] statusCode
```

**Current Behavior:**
```python
def _map_status(self, status_code) -> str:
    if not status_code or not status_code.code:
        return "active"  # Accepts missing statusCode
```

**Options:**

**Option 1 (Strict):**
```python
if not status_code or not status_code.code:
    raise ValueError("statusCode is required (C-CDA SHALL)")
```

**Option 2 (Lenient - current):**
Keep as-is but document the deviation.

**Recommendation:** Document the intentional deviation.

---

### MEDIUM-3: CareTeam - Care Team Type Observation Not Enforced

**Severity:** Medium
**Component:** CareTeam Converter
**Location:** `ccda_to_fhir/converters/careteam.py:316-360`

**Issue:**
C-CDA requires at least one Care Team Type Observation (1..1 SHALL) but implementation treats as optional.

**C-CDA Requirement:**
```
SHALL contain exactly one [1..1] Care Team Type Observation component
```

**Current Behavior:**
Test `test_handles_missing_team_type` confirms category is optional in implementation.

**Options:**

**Option 1 (Strict):**
```python
categories = self._extract_categories(organizer)
if not categories:
    raise ValueError("At least one Care Team Type Observation required (C-CDA SHALL)")
```

**Option 2 (Lenient - current):**
Keep as-is but document the deviation.

**Recommendation:** Document the intentional deviation.

---

### ~~MEDIUM-4: MedicationDispense - Location.managingOrganization Not Populated~~ ✅ FIXED

**Status:** ✅ Fixed on 2025-12-22
**Severity:** Medium
**Component:** MedicationDispense Converter - Location creation
**Location:** `ccda_to_fhir/converters/medication_dispense.py:622-627`

**Issue:**
US Core Must Support element `managingOrganization` not populated when creating Location resources for pharmacy organizations.

**US Core Must Support Rule:**
> "Must be supported if the data is present in the sending system"

Since the Location is created from C-CDA `representedOrganization`, the managing organization data is present and should be populated per US Core requirements.

**Fix Applied:**
Added `managingOrganization` reference to Location resources:

```python
# Add managingOrganization (US Core Must Support)
# Create Organization resource from the same representedOrganization and reference it
# Per US Core: "Must be supported if the data is present in the sending system"
org_id = self._create_pharmacy_organization(organization)
if org_id:
    location["managingOrganization"] = {"reference": f"Organization/{org_id}"}
```

**Implementation:**
- Modified: `ccda_to_fhir/converters/medication_dispense.py`
  - Lines 622-627: Added managingOrganization reference in `_create_pharmacy_location()` method
  - Reuses existing Organization creation logic to ensure consistency
  - Organization is created/retrieved before Location registration
- Added comprehensive tests: `tests/unit/converters/test_medication_dispense.py`
  - `test_location_includes_managing_organization_reference()` - Basic functionality
  - `test_location_managing_organization_with_organization_performer()` - Same org for performer and location
  - `test_location_managing_organization_reuses_existing_organization()` - No duplication when org referenced multiple times
- Test Status: ✅ All 1257 tests passing (+3 new tests) - no regressions

**Behavior:**
- When Location is created from `representedOrganization`, also creates Organization resource
- Location.managingOrganization references the Organization
- Organization is reused if already created (no duplication)
- Both performer.actor and location.managingOrganization can reference the same Organization

**Standards Compliance:**
- Implements US Core Must Support requirement for Location.managingOrganization
- Populates field when source data is available per US Core guidance
- Maintains referential integrity between Location and Organization resources

**References:**
- [US Core Location Profile](http://hl7.org/fhir/us/core/STU7/StructureDefinition-us-core-location.html)

---

### MEDIUM-5: MedicationDispense - us-core-20 Status Fallback

**Severity:** Medium
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:186-191`

**Issue:**
When status is "completed" but whenHandedOver is missing, status is changed to "unknown". This may not be appropriate in all cases.

**US Core Constraint us-core-20:**
```
whenHandedOver SHALL be present if the status is 'completed'
```

**Current Code:**
```python
if med_dispense["status"] == "completed" and "whenHandedOver" not in med_dispense:
    logger.warning(
        "MedicationDispense has status='completed' but no whenHandedOver timestamp. "
        "Setting status to 'unknown' per US Core constraint us-core-20."
    )
    med_dispense["status"] = "unknown"
```

**Current Approach:**
Changes status to "unknown" when timing missing.

**Concern:**
"unknown" may not be semantically correct - "in-progress" might be better.

**Alternative:**
```python
med_dispense["status"] = "in-progress"  # Instead of "unknown"
```

**Recommendation:** Current approach is acceptable, alternative is slightly more semantically accurate.

---

## Low Priority Issues

### LOW-1: CareTeam - Template Extensions Not Validated

**Severity:** Low
**Component:** CareTeam Converter
**Location:** `ccda_to_fhir/converters/careteam.py:224-232, 454-457, 341-343`

**Issue:**
Template validation checks root OID but not extension dates for all three templates.

**Current:**
```python
has_valid_template = any(
    tid.root == self.CARE_TEAM_ORGANIZER_TEMPLATE
    for tid in organizer.template_id
)
```

**Enhancement:**
```python
has_valid_template = any(
    tid.root == self.CARE_TEAM_ORGANIZER_TEMPLATE and
    tid.extension == "2022-06-01"
    for tid in organizer.template_id
)
```

**Impact:** Low - mainly for strict version checking.

---

### LOW-2: MedicationDispense - FHIR Invariant mdd-1 Not Validated

**Severity:** Low
**Component:** MedicationDispense Converter
**Location:** `ccda_to_fhir/converters/medication_dispense.py:462-496`

**Issue:**
No explicit validation that whenHandedOver >= whenPrepared.

**Current:**
Timing extraction naturally satisfies this, but not explicitly checked.

**Enhancement:**
```python
if "whenPrepared" in med_dispense and "whenHandedOver" in med_dispense:
    if med_dispense["whenHandedOver"] < med_dispense["whenPrepared"]:
        logger.warning("whenHandedOver before whenPrepared - FHIR invariant mdd-1 violation")
```

**Impact:** Low - timing extraction already handles this correctly in practice.

---

---

## Summary

### By Severity
- **Critical:** ~~2~~ 0 remaining (2 fixed)
- **High:** ~~3~~ ~~2~~ ~~1~~ 0 remaining (3 fixed)
- **Medium:** ~~5~~ 4 remaining (1 fixed, 3 intentional leniency, 1 enhancement)
- **Low:** 2 (nice-to-have validations)

### By Component
- **MedicationDispense:** ~~7~~ ~~6~~ ~~5~~ ~~4~~ ~~3~~ 2 issues remaining (5 fixed)
- **CareTeam:** ~~5~~ 4 issues remaining (1 fixed)

### Key Takeaways

**Fixed:**
1. ✅ MedicationDispense: Extract supply.code element (contains actual status) - FIXED 2025-12-22
2. ✅ MedicationDispense: Populate Location.identifier from organization - FIXED 2025-12-22
3. ✅ MedicationDispense: Handle Organization performers - FIXED 2025-12-22
4. ✅ CareTeam: Validate template extensions for all three templates - FIXED 2025-12-22
5. ✅ MedicationDispense: Performer function assignment with functionCode mapping - FIXED 2025-12-22
6. ✅ MedicationDispense: Populate Location.managingOrganization reference - FIXED 2025-12-22

**Intentional Design Choices:**
- CareTeam accepts missing required elements (statusCode, effectiveTime, type observation)
- Favors robustness over strict validation
- These should be **documented** not changed

**Nice to Have:**
- Template extension validation
- FHIR invariant checks

---

## References

### C-CDA Specifications
- [C-CDA Medication Dispense v2.1](https://build.fhir.org/ig/HL7/CDA-ccda-2.1-sd/StructureDefinition-MedicationDispense.html)
- [C-CDA Care Team Organizer](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamOrganizer.html)
- [C-CDA Examples (GitHub)](https://github.com/HL7/C-CDA-Examples)

### US Core Profiles
- [US Core MedicationDispense](http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense)
- [US Core CareTeam](http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam)
- [US Core Location](http://hl7.org/fhir/us/core/STU7/StructureDefinition-us-core-location.html)

### FHIR R4 Resources
- [MedicationDispense](https://hl7.org/fhir/R4/medicationdispense.html)
- [CareTeam](https://hl7.org/fhir/R4/careteam.html)
- [Location](https://hl7.org/fhir/R4/location.html)
