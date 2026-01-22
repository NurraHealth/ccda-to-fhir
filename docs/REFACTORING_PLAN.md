# C-CDA to FHIR Codebase Refactoring Plan

**Date**: 2026-01-22
**Status**: Proposed
**Goal**: Simplify and clean up codebase while maintaining 100% standard compliance

---

## Executive Summary

This document outlines a comprehensive refactoring plan to reduce code duplication, improve maintainability, and simplify the C-CDA to FHIR conversion library. All changes preserve existing functionality and standard compliance.

### Current State

| Metric | Value |
|--------|-------|
| Source Files | ~65 Python files |
| Total LOC | ~43k+ |
| Test Coverage | 1,928 passing tests |
| Largest Files | `convert.py` (4,055), `observation.py` (1,652), `encounter.py` (1,207) |

### Expected Outcomes

- ~700+ lines of duplicated code eliminated
- Better separation of concerns
- Easier maintenance and extension
- No changes to FHIR output or standard compliance

---

## Table of Contents

1. [Issue 1: Duplicated Utility Methods](#issue-1-duplicated-utility-methods)
2. [Issue 2: Monolithic convert.py](#issue-2-monolithic-convertpy)
3. [Issue 3: Large Observation Converter](#issue-3-large-observation-converter)
4. [Issue 4: Repeated Status Mapping Pattern](#issue-4-repeated-status-mapping-pattern)
5. [Issue 5: Inconsistent Error Handling](#issue-5-inconsistent-error-handling)
6. [Issue 6: Dead Code](#issue-6-dead-code)
7. [Issue 7: Missing Utility Reuse](#issue-7-missing-utility-reuse)
8. [Implementation Plan](#implementation-plan)
9. [Standard Compliance](#standard-compliance)

---

## Issue 1: Duplicated Utility Methods

**Priority**: High
**Impact**: High
**Effort**: Low

### Problem

The same utility methods are reimplemented across multiple converters with nearly identical logic:

| Method | Duplicated In | Approx Lines |
|--------|---------------|--------------|
| `_convert_telecom` | patient.py, practitioner.py, organization.py, location.py, related_person.py, medication_dispense.py | ~300 |
| `_convert_addresses` | patient.py, practitioner.py, organization.py, related_person.py | ~200 |
| `_convert_names` | patient.py, practitioner.py, related_person.py | ~150 |

### Current State

**patient.py:397-452** - Telecom conversion:
```python
def _convert_telecom(self, telecoms: list[TEL]) -> list[FHIRResourceDict]:
    """Convert C-CDA telecom to FHIR ContactPoint."""
    contact_points = []
    for telecom in telecoms:
        if not telecom.value:
            continue
        contact_point: JSONObject = {}
        if telecom.value.startswith("tel:"):
            contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
            contact_point["value"] = telecom.value[4:]
        elif telecom.value.startswith("mailto:"):
            contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
            contact_point["value"] = telecom.value[7:]
        # ... 40 more lines of identical logic
```

**practitioner.py:167-213** - Nearly identical:
```python
def _convert_telecom(self, telecoms: list[TEL]) -> list[dict[str, str]]:
    """Convert C-CDA telecom to FHIR ContactPoint."""
    fhir_telecom: list[dict[str, str]] = []
    for telecom in telecoms:
        if not telecom.value:
            continue
        contact_point: dict[str, str] = {}
        value = telecom.value
        if value.startswith("tel:"):
            contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
            contact_point["value"] = value[4:]
        # ... same logic repeated
```

### Proposed Solution

Move shared utilities to `BaseConverter` in `base.py`:

```python
# ccda_to_fhir/converters/base.py

class BaseConverter(ABC, Generic[CCDAModel]):
    # ... existing methods ...

    def convert_telecom(self, telecoms: list) -> list[JSONObject]:
        """Convert C-CDA TEL elements to FHIR ContactPoint.

        Shared utility used by Patient, Practitioner, Organization,
        Location, RelatedPerson, and other converters.

        Args:
            telecoms: List of C-CDA TEL elements

        Returns:
            List of FHIR ContactPoint dictionaries
        """
        from ccda_to_fhir.constants import TELECOM_USE_MAP, FHIRCodes

        contact_points: list[JSONObject] = []

        for telecom in telecoms:
            if not telecom or not telecom.value:
                continue

            contact_point: JSONObject = {}
            value = telecom.value

            # Parse system and value from URI prefix
            if value.startswith("tel:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value[4:]
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]
            elif value.startswith("http://") or value.startswith("https://"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value

            # Map use code
            if telecom.use:
                fhir_use = TELECOM_USE_MAP.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            # Handle period if present
            if hasattr(telecom, 'use_period') and telecom.use_period:
                period = self._convert_period(telecom.use_period)
                if period:
                    contact_point["period"] = period

            contact_points.append(contact_point)

        return contact_points

    def convert_addresses(self, addresses: list) -> list[JSONObject]:
        """Convert C-CDA AD elements to FHIR Address.

        Shared utility used by Patient, Practitioner, Organization,
        Location, and RelatedPerson converters.

        Args:
            addresses: List of C-CDA AD elements

        Returns:
            List of FHIR Address dictionaries
        """
        from ccda_to_fhir.constants import ADDRESS_USE_MAP, FHIRCodes

        fhir_addresses: list[JSONObject] = []

        for addr in addresses:
            if not addr:
                continue

            fhir_addr: JSONObject = {}

            # Use
            if addr.use:
                fhir_addr["use"] = ADDRESS_USE_MAP.get(
                    addr.use, FHIRCodes.AddressUse.HOME
                )

            # Type
            fhir_addr["type"] = FHIRCodes.AddressType.PHYSICAL

            # Street lines
            if addr.street_address_line:
                fhir_addr["line"] = addr.street_address_line

            # City (handle both single value and list)
            if addr.city:
                fhir_addr["city"] = (
                    addr.city[0] if isinstance(addr.city, list) else addr.city
                )

            # State
            if addr.state:
                fhir_addr["state"] = (
                    addr.state[0] if isinstance(addr.state, list) else addr.state
                )

            # Postal code
            if addr.postal_code:
                fhir_addr["postalCode"] = (
                    addr.postal_code[0] if isinstance(addr.postal_code, list)
                    else addr.postal_code
                )

            # Country
            if addr.country:
                fhir_addr["country"] = (
                    addr.country[0] if isinstance(addr.country, list)
                    else addr.country
                )

            # Period
            if hasattr(addr, 'useable_period') and addr.useable_period:
                period = self._convert_period(addr.useable_period)
                if period:
                    fhir_addr["period"] = period

            if fhir_addr:
                fhir_addresses.append(fhir_addr)

        return fhir_addresses

    def convert_human_names(self, names: list) -> list[JSONObject]:
        """Convert C-CDA PN elements to FHIR HumanName.

        Shared utility used by Patient, Practitioner, and RelatedPerson.

        Args:
            names: List of C-CDA PN (Person Name) elements

        Returns:
            List of FHIR HumanName dictionaries
        """
        from ccda_to_fhir.constants import NAME_USE_MAP, FHIRCodes

        fhir_names: list[JSONObject] = []

        for name in names:
            if not name:
                continue

            fhir_name: JSONObject = {}

            # Use
            if name.use:
                fhir_name["use"] = NAME_USE_MAP.get(name.use, FHIRCodes.NameUse.USUAL)

            # Family
            if name.family:
                fhir_name["family"] = (
                    name.family.value if hasattr(name.family, 'value')
                    else str(name.family)
                )

            # Given (list)
            if name.given:
                fhir_name["given"] = [
                    g.value if hasattr(g, 'value') else str(g)
                    for g in name.given
                    if g and (hasattr(g, 'value') and g.value or str(g))
                ]

            # Prefix (list)
            if name.prefix:
                fhir_name["prefix"] = [
                    p.value if hasattr(p, 'value') else str(p)
                    for p in name.prefix
                    if p and (hasattr(p, 'value') and p.value or str(p))
                ]

            # Suffix (list)
            if name.suffix:
                fhir_name["suffix"] = [
                    s.value if hasattr(s, 'value') else str(s)
                    for s in name.suffix
                    if s and (hasattr(s, 'value') and s.value or str(s))
                ]

            # Period
            if hasattr(name, 'valid_time') and name.valid_time:
                period = self._convert_period(name.valid_time)
                if period:
                    fhir_name["period"] = period

            if fhir_name:
                fhir_names.append(fhir_name)

        return fhir_names

    def _convert_period(self, time_interval) -> JSONObject | None:
        """Convert C-CDA IVL_TS to FHIR Period.

        Args:
            time_interval: C-CDA interval with low/high

        Returns:
            FHIR Period dict or None
        """
        period: JSONObject = {}

        if hasattr(time_interval, 'low') and time_interval.low:
            if hasattr(time_interval.low, 'value'):
                start = self.convert_date(time_interval.low.value)
                if start:
                    period["start"] = start

        if hasattr(time_interval, 'high') and time_interval.high:
            if hasattr(time_interval.high, 'value'):
                end = self.convert_date(time_interval.high.value)
                if end:
                    period["end"] = end

        return period if period else None
```

### Migration Steps

1. Add shared methods to `BaseConverter`
2. Update each converter to use inherited methods:
   ```python
   # patient.py - Before
   patient["telecom"] = self._convert_telecom(patient_role.telecom)

   # patient.py - After
   patient["telecom"] = self.convert_telecom(patient_role.telecom)
   ```
3. Delete duplicate `_convert_telecom`, `_convert_addresses`, `_convert_names` methods
4. Run tests to verify no behavioral changes

### Files to Modify

- `ccda_to_fhir/converters/base.py` - Add shared methods
- `ccda_to_fhir/converters/patient.py` - Remove duplicates
- `ccda_to_fhir/converters/practitioner.py` - Remove duplicates
- `ccda_to_fhir/converters/organization.py` - Remove duplicates
- `ccda_to_fhir/converters/location.py` - Remove duplicates
- `ccda_to_fhir/converters/related_person.py` - Remove duplicates
- `ccda_to_fhir/converters/medication_dispense.py` - Remove duplicates

### Estimated Impact

- **Lines removed**: ~500
- **Risk**: Low (pure refactoring, same logic)

---

## Issue 2: Monolithic convert.py

**Priority**: High
**Impact**: High
**Effort**: Medium

### Problem

`convert.py` at 4,055 lines is doing too much:
- Document parsing orchestration
- 19+ instance variables for state tracking
- 12+ converter instances
- 20+ section processor configurations
- Author/informant extraction coordination
- Metadata tracking
- Validation coordination
- Bundle assembly

### Current State

**convert.py:227-330** - Constructor with too many responsibilities:
```python
class DocumentConverter:
    def __init__(self, ...):
        self.code_system_mapper = code_system_mapper or CodeSystemMapper()
        self.original_xml = original_xml
        self.reference_registry = ReferenceRegistry()
        self.enable_validation = enable_validation
        self.validator = FHIRValidator(...) if enable_validation else None

        # 6 different "seen" sets for deduplication
        self._seen_observation_ids: set[tuple[str, str | None]] = set()
        self._seen_medication_ids: set[tuple[str, str | None]] = set()
        self._seen_allergy_ids: set[tuple[str, str | None]] = set()
        self._seen_goal_ids: set[tuple[str, str | None]] = set()
        self._seen_immunization_ids: set[tuple[str, str | None]] = set()
        self._seen_diagnostic_report_ids: set[tuple[str, str | None]] = set()

        # Author/informant tracking
        self._author_metadata: dict[str, list[AuthorInfo]] = {}
        self.author_extractor = AuthorExtractor()
        self.provenance_converter = ProvenanceConverter(...)
        self._informant_metadata: dict[str, list] = {}
        self.informant_extractor = InformantExtractor()

        # 12 individual converters
        self.patient_converter = PatientConverter(...)
        self.document_reference_converter = DocumentReferenceConverter(...)
        self.observation_converter = ObservationConverter(...)
        self.diagnostic_report_converter = DiagnosticReportConverter(...)
        self.procedure_converter = ProcedureConverter(...)
        self.service_request_converter = ServiceRequestConverter(...)
        self.encounter_converter = EncounterConverter(...)
        self.goal_converter = GoalConverter(...)
        self.practitioner_converter = PractitionerConverter(...)
        self.practitioner_role_converter = PractitionerRoleConverter(...)
        self.device_converter = DeviceConverter(...)
        self.organization_converter = OrganizationConverter(...)

        # Initialize section processors (another 200 lines)
        self._init_section_processors()
```

### Proposed Solution

Split into focused modules:

```
ccda_to_fhir/
├── convert.py                      # Slim public API (~200 lines)
├── orchestration/
│   ├── __init__.py
│   ├── document_orchestrator.py    # Main orchestrator (~400 lines)
│   ├── section_orchestrator.py     # Section processing config (~300 lines)
│   ├── participant_orchestrator.py # Authors, informants, provenance (~300 lines)
│   └── deduplication.py            # Seen ID tracking (~100 lines)
```

### Proposed Structure

**convert.py** - Public API only:
```python
"""Public API for C-CDA to FHIR conversion."""

from ccda_to_fhir.orchestration.document_orchestrator import DocumentOrchestrator

def convert_document(
    ccda_xml: str | bytes,
    enable_validation: bool = False,
    strict_validation: bool = False,
) -> ConversionResult:
    """Convert a C-CDA document to FHIR Bundle.

    This is the main entry point for C-CDA to FHIR conversion.

    Args:
        ccda_xml: C-CDA XML string or bytes
        enable_validation: Enable FHIR resource validation
        strict_validation: Raise on validation errors

    Returns:
        ConversionResult with bundle and metadata
    """
    orchestrator = DocumentOrchestrator(
        enable_validation=enable_validation,
        strict_validation=strict_validation,
    )
    return orchestrator.convert(ccda_xml)


# Re-export for backwards compatibility
DocumentConverter = DocumentOrchestrator
```

**orchestration/document_orchestrator.py** - Core orchestration:
```python
"""Main document conversion orchestrator."""

class DocumentOrchestrator:
    """Orchestrates C-CDA to FHIR document conversion."""

    def __init__(self, ...):
        self.code_system_mapper = CodeSystemMapper()
        self.reference_registry = ReferenceRegistry()

        # Delegate to specialized orchestrators
        self.section_orchestrator = SectionOrchestrator(self)
        self.participant_orchestrator = ParticipantOrchestrator(self)
        self.deduplication = DeduplicationTracker()

    def convert(self, ccda_xml: str | bytes) -> ConversionResult:
        """Convert complete C-CDA document."""
        document = parse_ccda(ccda_xml)

        # 1. Extract patient
        patient = self._convert_patient(document)

        # 2. Extract participants (authors, informants)
        participants = self.participant_orchestrator.extract(document)

        # 3. Process clinical sections
        clinical_resources = self.section_orchestrator.process(document)

        # 4. Generate provenance
        provenance = self.participant_orchestrator.create_provenance()

        # 5. Build bundle
        return self._build_bundle(patient, participants, clinical_resources, provenance)
```

**orchestration/section_orchestrator.py** - Section processing:
```python
"""Section processing configuration and orchestration."""

class SectionOrchestrator:
    """Configures and runs section processors."""

    def __init__(self, parent: DocumentOrchestrator):
        self.parent = parent
        self._init_processors()

    def _init_processors(self):
        """Initialize all section processors."""
        self.processors = {
            "conditions": SectionProcessor(SectionConfig(
                template_id=TemplateIds.PROBLEM_CONCERN_ACT,
                entry_type="act",
                converter=convert_problem_concern_act,
                error_message="problem concern act",
            )),
            "allergies": SectionProcessor(SectionConfig(...)),
            "medications": SectionProcessor(SectionConfig(...)),
            # ... etc
        }

    def process(self, document: ClinicalDocument) -> list[FHIRResourceDict]:
        """Process all sections and return resources."""
        resources = []
        for name, processor in self.processors.items():
            section_resources = processor.process(
                document.component.structured_body,
                **self._get_processor_kwargs()
            )
            resources.extend(section_resources)
        return resources
```

**orchestration/deduplication.py** - ID tracking:
```python
"""Deduplication tracking for resource IDs."""

class DeduplicationTracker:
    """Tracks seen IDs to prevent duplicates."""

    def __init__(self):
        self._seen: dict[str, set[tuple[str, str | None]]] = {
            "observation": set(),
            "medication": set(),
            "allergy": set(),
            "goal": set(),
            "immunization": set(),
            "diagnostic_report": set(),
        }

    def is_seen(self, resource_type: str, root: str, extension: str | None) -> bool:
        """Check if ID has been seen."""
        key = (root, extension)
        return key in self._seen.get(resource_type, set())

    def mark_seen(self, resource_type: str, root: str, extension: str | None) -> None:
        """Mark ID as seen."""
        if resource_type in self._seen:
            self._seen[resource_type].add((root, extension))

    def reset(self) -> None:
        """Reset all tracking (for new document)."""
        for key in self._seen:
            self._seen[key] = set()
```

### Migration Steps

1. Create `orchestration/` package
2. Extract `DeduplicationTracker` (low risk, no dependencies)
3. Extract `SectionOrchestrator` (section processor config)
4. Extract `ParticipantOrchestrator` (author/informant handling)
5. Refactor `DocumentConverter` to use orchestrators
6. Update imports and tests

### Estimated Impact

- **Lines in convert.py**: 4,055 → ~500
- **Overall LOC**: Same (reorganized)
- **Maintainability**: Significantly improved
- **Risk**: Medium (need careful testing)

---

## Issue 3: Large Observation Converter

**Priority**: Medium
**Impact**: Medium
**Effort**: Medium

### Problem

`observation.py` at 1,652 lines handles too many observation types:
- Vital signs with blood pressure panel logic
- Laboratory results
- Social history observations
- Smoking status
- Pregnancy observations (with EDD, LMP, gestational age)
- Pulse oximetry with O2 flow/concentration components

### Current State

**observation.py:36-47** - Single class handles everything:
```python
class ObservationConverter(BaseConverter[Observation]):
    """Convert C-CDA Observation to FHIR Observation resource.

    This converter handles the mapping from C-CDA Observation to FHIR R4B
    Observation resource. It supports multiple observation types:
    - Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27)
    - Result Observation (2.16.840.1.113883.10.20.22.4.2)
    - Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78)
    - Social History Observation (2.16.840.1.113883.10.20.22.4.38)
    """
```

### Proposed Solution

Split into specialized converters:

```
ccda_to_fhir/converters/
├── observation/
│   ├── __init__.py           # Re-exports for compatibility
│   ├── base.py               # ObservationConverterBase (~300 lines)
│   ├── vital_signs.py        # VitalSignsConverter (~500 lines)
│   ├── laboratory.py         # LaboratoryConverter (~300 lines)
│   └── social_history.py     # SocialHistoryConverter (~300 lines)
```

### Proposed Structure

**observation/base.py** - Shared observation logic:
```python
"""Base observation converter with shared logic."""

class ObservationConverterBase(BaseConverter[Observation]):
    """Base class for observation converters.

    Provides shared logic for:
    - ID generation
    - Status determination
    - Value conversion (PQ, CD, ST, etc.)
    - Reference range handling
    - Narrative generation
    """

    def __init__(self, *args, seen_observation_ids: set | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.seen_observation_ids = seen_observation_ids or set()

    def _generate_observation_id(self, root: str | None, ext: str | None) -> str:
        """Generate FHIR resource ID from C-CDA identifier."""
        return self.generate_resource_id(root, ext, "observation")

    def _determine_status(self, observation: Observation) -> str:
        """Determine FHIR status from C-CDA status code."""
        # Shared logic

    def _convert_value(self, observation: Observation) -> JSONObject | None:
        """Convert observation value to FHIR value[x]."""
        # Handles PQ, CD, ST, ED, INT, IVL_PQ

    def _convert_reference_range(self, obs_range) -> JSONObject | None:
        """Convert C-CDA reference range to FHIR."""
        # Shared logic
```

**observation/vital_signs.py** - Vital signs specialist:
```python
"""Vital signs observation converter."""

class VitalSignsConverter(ObservationConverterBase):
    """Convert vital sign observations including panels.

    Handles:
    - Individual vital signs
    - Vital signs organizer → panel with hasMember
    - Blood pressure → combined observation with systolic/diastolic components
    - Pulse oximetry → observation with O2 flow/concentration components
    """

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Convert vital sign observation."""
        # Sets category to vital-signs
        # Applies US Core vital signs profile

    def convert_vital_signs_organizer(self, organizer, section=None):
        """Convert vital signs organizer to panel + individual observations."""
        # Blood pressure detection and combination
        # Pulse oximetry component handling

    def _create_blood_pressure_observation(self, systolic, diastolic, status):
        """Create combined BP observation with components."""

    def _add_pulse_ox_components(self, pulse_ox, o2_flow, o2_concentration):
        """Add O2 components to pulse oximetry observation."""
```

**observation/laboratory.py** - Lab results specialist:
```python
"""Laboratory observation converter."""

class LaboratoryObservationConverter(ObservationConverterBase):
    """Convert laboratory/result observations.

    Handles:
    - Result observations
    - Reference ranges (normal ranges only)
    - US Core laboratory profile
    """

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Convert lab result observation."""
        # Sets category to laboratory
        # Applies US Core lab profile
```

**observation/social_history.py** - Social history specialist:
```python
"""Social history observation converter."""

class SocialHistoryConverter(ObservationConverterBase):
    """Convert social history observations.

    Handles:
    - Social history observations
    - Smoking status (LOINC 72166-2)
    - Pregnancy observations with components (EDD, LMP, gestational age)
    - SDOH category assignment
    """

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Convert social history observation."""
        # Sets category to social-history
        # Adds SDOH category if applicable
        # Special handling for pregnancy observations

    def _handle_pregnancy_observation(self, observation, fhir_obs):
        """Handle pregnancy-specific conversions."""
        # Transform ASSERTION code to LOINC 82810-3
        # Extract EDD, LMP, gestational age as components
```

**observation/__init__.py** - Compatibility exports:
```python
"""Observation converters package.

Provides backwards-compatible ObservationConverter that delegates
to specialized converters based on template ID.
"""

from .vital_signs import VitalSignsConverter
from .laboratory import LaboratoryObservationConverter
from .social_history import SocialHistoryConverter

class ObservationConverter:
    """Facade that delegates to specialized observation converters.

    Maintains backwards compatibility while using specialized converters.
    """

    def __init__(self, *args, **kwargs):
        self.vital_signs = VitalSignsConverter(*args, **kwargs)
        self.laboratory = LaboratoryObservationConverter(*args, **kwargs)
        self.social_history = SocialHistoryConverter(*args, **kwargs)

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Route to appropriate converter based on template ID."""
        converter = self._get_converter(observation)
        return converter.convert(observation, section)

    def convert_vital_signs_organizer(self, organizer, section=None):
        """Delegate to vital signs converter."""
        return self.vital_signs.convert_vital_signs_organizer(organizer, section)

    def _get_converter(self, observation):
        """Determine converter based on template ID."""
        if self._is_vital_sign(observation):
            return self.vital_signs
        elif self._is_lab_result(observation):
            return self.laboratory
        else:
            return self.social_history
```

### Migration Steps

1. Create `observation/` package with `__init__.py`
2. Extract shared logic to `base.py`
3. Create `vital_signs.py` with BP/pulse ox handling
4. Create `laboratory.py` for lab results
5. Create `social_history.py` for social/smoking/pregnancy
6. Create facade `ObservationConverter` for backwards compatibility
7. Update imports in `convert.py`

### Estimated Impact

- **observation.py**: 1,652 → split into 4 files (~300-500 each)
- **Maintainability**: Much easier to understand and modify
- **Risk**: Medium (need careful testing of each observation type)

---

## Issue 4: Repeated Status Mapping Pattern

**Priority**: Medium
**Impact**: Medium
**Effort**: Low

### Problem

Every converter implements similar status extraction logic:

**condition.py**:
```python
def _determine_clinical_status(self, observation):
    if not observation.status_code or not observation.status_code.code:
        return "active"
    status = observation.status_code.code.lower()
    return CONDITION_STATUS_TO_FHIR.get(status, "active")
```

**observation.py**:
```python
def _determine_status(self, observation):
    if not observation.status_code or not observation.status_code.code:
        return FHIRCodes.ObservationStatus.FINAL
    status_code = observation.status_code.code.lower()
    return OBSERVATION_STATUS_TO_FHIR.get(status_code, FHIRCodes.ObservationStatus.FINAL)
```

**allergy_intolerance.py**:
```python
def _extract_clinical_status(self, ...):
    if not status_code:
        return "active"
    return ALLERGY_STATUS_TO_FHIR.get(status_code.lower(), "active")
```

### Proposed Solution

Add generic status mapper to `BaseConverter`:

```python
# ccda_to_fhir/converters/base.py

class BaseConverter(ABC, Generic[CCDAModel]):
    # ... existing methods ...

    def map_status_code(
        self,
        status_code,  # CS type from C-CDA
        mapping: dict[str, str],
        default: str,
    ) -> str:
        """Map C-CDA status code to FHIR status using provided mapping.

        Generic utility for status code mapping used by all converters.
        Handles null/missing status codes gracefully.

        Args:
            status_code: C-CDA CS status code element (may be None)
            mapping: Dictionary mapping C-CDA codes to FHIR codes
            default: Default FHIR status if code is missing or unmapped

        Returns:
            FHIR status code string

        Example:
            >>> status = self.map_status_code(
            ...     observation.status_code,
            ...     OBSERVATION_STATUS_TO_FHIR,
            ...     "final"
            ... )
        """
        if not status_code:
            return default

        code = None
        if hasattr(status_code, 'code'):
            code = status_code.code
        elif isinstance(status_code, str):
            code = status_code

        if not code:
            return default

        # Case-insensitive lookup
        return mapping.get(code.lower(), default)
```

### Usage After Refactoring

```python
# condition.py - Before
def _determine_clinical_status(self, observation):
    if not observation.status_code or not observation.status_code.code:
        return "active"
    status = observation.status_code.code.lower()
    return CONDITION_STATUS_TO_FHIR.get(status, "active")

# condition.py - After
def _determine_clinical_status(self, observation):
    return self.map_status_code(
        observation.status_code,
        CONDITION_STATUS_TO_FHIR,
        "active"
    )
```

### Files to Modify

- `ccda_to_fhir/converters/base.py` - Add method
- `ccda_to_fhir/converters/condition.py`
- `ccda_to_fhir/converters/observation.py`
- `ccda_to_fhir/converters/allergy_intolerance.py`
- `ccda_to_fhir/converters/medication_request.py`
- `ccda_to_fhir/converters/medication_statement.py`
- `ccda_to_fhir/converters/immunization.py`
- `ccda_to_fhir/converters/procedure.py`

### Estimated Impact

- **Lines removed**: ~100
- **Consistency**: All status mapping uses same pattern
- **Risk**: Low

---

## Issue 5: Inconsistent Error Handling

**Priority**: Medium
**Impact**: Medium
**Effort**: Medium

### Problem

Error handling varies across converters:

**Strict (raises exception)**:
```python
# observation.py:74
if not observation.code:
    raise ValueError("Observation must have a code element")
```

**Lenient (logs and continues)**:
```python
# allergy_intolerance.py (hypothetical)
if not reaction.reaction_observation:
    logger.warning("No reaction observation found")
    continue  # Silently skips
```

**Mixed (sometimes raises, sometimes logs)**:
```python
# Various converters have inconsistent patterns
```

### Proposed Solution

Establish clear error handling strategy:

```python
# ccda_to_fhir/exceptions.py - Add new exception types

class ConversionWarning(CCDAConversionError):
    """Warning-level issue that doesn't prevent conversion."""
    pass

class RecoverableConversionError(CCDAConversionError):
    """Error that can be recovered from with fallback behavior."""
    pass
```

**Strategy**:

| Scenario | Action | Example |
|----------|--------|---------|
| Required FHIR field missing, no fallback | Raise `MissingRequiredFieldError` | Observation without code |
| Required FHIR field missing, fallback available | Log warning, use fallback | Status missing → "unknown" |
| Optional field missing | Log debug, omit field | No telecom |
| Invalid data, recoverable | Log warning, skip item | Invalid date format |
| Invalid data, not recoverable | Raise `InvalidDataError` | Malformed XML |

**Implementation**:

```python
# ccda_to_fhir/converters/base.py

class BaseConverter(ABC, Generic[CCDAModel]):

    def require_field(
        self,
        value,
        field_name: str,
        resource_type: str,
    ):
        """Validate required field is present.

        Args:
            value: The field value to check
            field_name: Name of the field for error message
            resource_type: FHIR resource type for error message

        Raises:
            MissingRequiredFieldError: If value is None/empty
        """
        if value is None or value == "" or value == []:
            raise MissingRequiredFieldError(
                f"{resource_type} requires {field_name}"
            )

    def optional_field(
        self,
        value,
        converter: Callable,
        field_name: str,
    ):
        """Convert optional field, returning None if missing.

        Args:
            value: The field value (may be None)
            converter: Function to convert the value
            field_name: Name for debug logging

        Returns:
            Converted value or None
        """
        if value is None:
            logger.debug(f"Optional field {field_name} not present")
            return None
        try:
            return converter(value)
        except Exception as e:
            logger.warning(f"Failed to convert {field_name}: {e}")
            return None
```

### Migration Steps

1. Define clear error handling strategy in documentation
2. Add helper methods to `BaseConverter`
3. Audit each converter for consistency
4. Update converters to use consistent patterns
5. Add tests for error scenarios

### Estimated Impact

- **Consistency**: Predictable error behavior
- **Debugging**: Clearer error messages
- **Risk**: Medium (behavior changes for edge cases)

---

## Issue 6: Dead Code

**Priority**: Low
**Impact**: Low
**Effort**: Trivial

### Problem

Unused methods and code remain in the codebase:

**patient.py:203-223** - Unused OLD method:
```python
def _generate_patient_id_OLD(self, identifier: II) -> str:
    """Generate a patient resource ID from an identifier.

    Args:
        identifier: The C-CDA identifier

    Returns:
        A resource ID string
    """
    if identifier.extension:
        # Use extension as basis for ID
        return f"patient-{identifier.extension.lower().replace(' ', '-')}"
    elif identifier.root:
        # Use last 16 chars of root
        root_suffix = identifier.root.replace(".", "").replace("-", "")[-16:]
        return f"patient-{root_suffix}"
    else:
        raise ValueError(
            "Cannot generate Patient ID: no identifiers provided. "
            "C-CDA recordTarget/patientRole must have id element."
        )
```

### Proposed Solution

Delete unused code:

```python
# patient.py - Remove _generate_patient_id_OLD method entirely
```

### Files to Audit

Run dead code detection:
```bash
# Find unused functions
vulture ccda_to_fhir/

# Or use coverage to find untested code
uv run pytest --cov=ccda_to_fhir --cov-report=html
```

### Estimated Impact

- **Lines removed**: ~20+
- **Risk**: Very low

---

## Issue 7: Missing Utility Reuse

**Priority**: Low
**Impact**: Low
**Effort**: Low

### Problem

`AuthorExtractor` exists but isn't consistently used:

**convert.py** - Uses it:
```python
self.author_extractor = AuthorExtractor()
authors = self.author_extractor.extract_from_document(document)
```

**observation.py** - Reimplements author extraction:
```python
def _extract_performers(self, observation):
    performers = []
    for performer in observation.performer:
        if performer.assigned_entity and performer.assigned_entity.id:
            for id_elem in performer.assigned_entity.id:
                if id_elem.root:
                    practitioner_id = self._generate_practitioner_id(
                        id_elem.root, id_elem.extension
                    )
                    performers.append({
                        "reference": f"urn:uuid:{practitioner_id}"
                    })
                    break
    return performers
```

### Proposed Solution

Use `AuthorExtractor` consistently:

```python
# observation.py - Before
if observation.performer:
    performers = []
    for performer in observation.performer:
        # Manual extraction logic
    fhir_obs["performer"] = performers

# observation.py - After
if observation.performer:
    fhir_obs["performer"] = self.author_extractor.extract_performer_references(
        observation.performer
    )
```

This may require extending `AuthorExtractor` to handle performer extraction.

### Estimated Impact

- **Consistency**: Single source of truth for author/performer extraction
- **Lines removed**: ~50
- **Risk**: Low

---

## Implementation Plan

### Phase 1: Quick Wins (1-2 days)

**Low risk, immediate value**

1. **Delete dead code**
   - Remove `_generate_patient_id_OLD` from patient.py
   - Run vulture to find other dead code

2. **Add generic status mapper**
   - Add `map_status_code` to BaseConverter
   - Update 8 converters to use it

### Phase 2: Extract Shared Utilities (3-5 days)

**Low-medium risk, high value**

1. **Add shared methods to BaseConverter**
   - `convert_telecom`
   - `convert_addresses`
   - `convert_human_names`
   - `_convert_period`

2. **Update converters to use shared methods**
   - patient.py
   - practitioner.py
   - organization.py
   - location.py
   - related_person.py
   - medication_dispense.py

3. **Delete duplicate methods from converters**

### Phase 3: Split Observation Converter (1-2 weeks)

**Medium risk, medium value**

1. Create `observation/` package
2. Extract `ObservationConverterBase`
3. Create specialized converters
4. Create facade for compatibility
5. Update tests

### Phase 4: Modularize DocumentConverter (2-3 weeks)

**Higher risk, high value**

1. Create `orchestration/` package
2. Extract `DeduplicationTracker`
3. Extract `SectionOrchestrator`
4. Extract `ParticipantOrchestrator`
5. Refactor `DocumentConverter`
6. Update all imports and tests

### Phase 5: Standardize Error Handling (1 week)

**Medium risk**

1. Define error handling strategy
2. Add helper methods to BaseConverter
3. Audit and update all converters

---

## Standard Compliance

All recommended changes maintain 100% standard compliance:

| Aspect | Status |
|--------|--------|
| FHIR R4B output | Unchanged |
| US Core profiles | Unchanged |
| C-CDA on FHIR IG mappings | Unchanged |
| Template ID handling | Unchanged |
| Code system mappings | Unchanged |

**Why compliance is preserved**:

1. **Pure refactoring** - No changes to conversion logic
2. **Same output** - Tests verify FHIR output remains identical
3. **No mapping changes** - Same C-CDA → FHIR transformations
4. **Profile URLs preserved** - US Core profile assignments unchanged

---

## Testing Strategy

### For Each Change

1. **Run existing tests**: `uv run pytest`
2. **Compare output**: Generate FHIR bundles before/after, diff
3. **Validate FHIR**: Run FHIR validator on sample outputs
4. **Check coverage**: Ensure no regression in test coverage

### Sample Comparison Script

```python
# scripts/compare_output.py
import json
from ccda_to_fhir import convert_document

# Load test documents
test_docs = [
    "tests/fixtures/sample1.xml",
    "tests/fixtures/sample2.xml",
]

for doc_path in test_docs:
    with open(doc_path) as f:
        xml = f.read()

    result = convert_document(xml)
    bundle = result["bundle"]

    # Save for comparison
    output_path = doc_path.replace(".xml", "_output.json")
    with open(output_path, "w") as f:
        json.dump(bundle, f, indent=2)

    print(f"Generated: {output_path}")
```

---

## Summary

| Issue | Priority | Impact | Effort | Lines Saved |
|-------|----------|--------|--------|-------------|
| 1. Duplicated utilities | High | High | Low | ~500 |
| 2. Monolithic convert.py | High | High | Medium | Reorganized |
| 3. Large observation.py | Medium | Medium | Medium | Split ~1,600 |
| 4. Status mapping | Medium | Medium | Low | ~100 |
| 5. Error handling | Medium | Medium | Medium | Consistency |
| 6. Dead code | Low | Low | Trivial | ~20 |
| 7. Missing utility reuse | Low | Low | Low | ~50 |

**Total estimated impact**: ~700+ lines of duplicated code eliminated, significantly improved maintainability, no changes to standard compliance.
