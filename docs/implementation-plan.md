# Implementation Plan: C-CDA to FHIR Conversion Pipeline

## Overview

The goal is to convert C-CDA XML documents to FHIR R4B JSON Bundles using a three-stage pipeline:

```
┌─────────────┐      ┌─────────────────┐      ┌─────────────────┐      ┌─────────────┐
│  C-CDA XML  │  →   │  C-CDA Pydantic │  →   │  FHIR Pydantic  │  →   │  FHIR JSON  │
│   (string)  │      │     Models      │      │     Models      │      │   Bundle    │
└─────────────┘      └─────────────────┘      └─────────────────┘      └─────────────┘
                           Stage 1                 Stage 2                 Stage 3
                          (Parser)               (Mapper)              (Serializer)
```

## Architecture

### Stage 1: C-CDA XML → C-CDA Pydantic Models

**Purpose:** Parse XML into a typed object graph that represents the C-CDA document structure.

**Location:** `src/ccda_to_fhir/ccda/`

**Key Components:**
- `models/` - Pydantic models for C-CDA data types and clinical structures
- `parser.py` - XML parsing logic that instantiates the models

**C-CDA Models to Implement:**

1. **Data Types** (`models/datatypes.py`)
   - `II` - Instance Identifier (id elements)
   - `CD` / `CE` / `CV` - Coded values with translations
   - `AD` - Address
   - `PN` / `EN` - Person/Entity names
   - `TEL` - Telecom
   - `TS` - Timestamp
   - `IVL_TS` - Interval of time
   - `PQ` - Physical quantity
   - `ST` - String
   - `ED` - Encapsulated data (for text content)

2. **Clinical Document Structure** (`models/document.py`)
   - `ClinicalDocument` - Root element
   - `RecordTarget` / `PatientRole` / `Patient`
   - `Author` / `AssignedAuthor`
   - `Custodian`
   - `Component` / `StructuredBody` / `Section`

3. **Clinical Entries** (`models/entries.py`)
   - `Act` - Allergy Concern Act, Problem Concern Act
   - `Observation` - Allergy, Problem, Vital Sign, Result, Social History
   - `SubstanceAdministration` - Medication, Immunization
   - `Procedure` - Procedure Activity
   - `Encounter` - Encounter Activity
   - `Organizer` - Results Organizer, Vital Signs Organizer

4. **Participants** (`models/participants.py`)
   - `Participant` / `ParticipantRole`
   - `Performer` / `AssignedEntity`
   - `Author` (entry-level)

### Stage 2: C-CDA Pydantic → FHIR Pydantic Models

**Purpose:** Map C-CDA clinical concepts to FHIR resources.

**Location:** `src/ccda_to_fhir/fhir/`

**Key Components:**
- `models/` - Pydantic models for FHIR R4B resources
- `mappers/` - Mapping functions from C-CDA to FHIR models

**FHIR Models to Implement:**

1. **Data Types** (`models/datatypes.py`)
   - `Identifier`
   - `CodeableConcept` / `Coding`
   - `Address`
   - `HumanName`
   - `ContactPoint`
   - `Quantity`
   - `Period`
   - `Reference`
   - `Annotation`
   - `Extension`

2. **Resources** (`models/resources/`)
   - `Patient`
   - `AllergyIntolerance`
   - `Condition`
   - `MedicationRequest`
   - `Procedure`
   - `Observation` (vital signs, labs, social history)
   - `DiagnosticReport`
   - `Immunization`
   - `Encounter`
   - `DocumentReference`
   - `Practitioner`
   - `Organization`
   - `Bundle`

**Mappers to Implement** (`mappers/`):

Each mapper converts one or more C-CDA models to FHIR models:

| Mapper | Input (C-CDA) | Output (FHIR) |
|--------|---------------|---------------|
| `patient.py` | `RecordTarget` | `Patient` |
| `allergy.py` | `Act` (Allergy Concern) | `AllergyIntolerance` |
| `condition.py` | `Act` (Problem Concern) | `Condition` |
| `medication.py` | `SubstanceAdministration` | `MedicationRequest` |
| `procedure.py` | `Procedure` | `Procedure` |
| `immunization.py` | `SubstanceAdministration` | `Immunization` |
| `observation.py` | `Observation` / `Organizer` | `Observation`, `DiagnosticReport` |
| `encounter.py` | `Encounter` | `Encounter` |
| `practitioner.py` | `Author` / `Performer` | `Practitioner`, `Organization` |
| `document_reference.py` | `Act` (Note Activity) | `DocumentReference` |

### Stage 3: FHIR Pydantic → JSON Bundle

**Purpose:** Serialize FHIR models to a valid JSON Bundle.

**Location:** `src/ccda_to_fhir/fhir/serializer.py`

**Key Components:**
- Bundle assembly (collect all resources, assign UUIDs)
- Reference resolution (link resources within the bundle)
- JSON serialization via Pydantic's `.model_dump()`

## Entry Point

**Location:** `src/ccda_to_fhir/convert.py`

```python
def convert_document(ccda_xml: str) -> dict[str, Any]:
    # Stage 1: Parse XML to C-CDA models
    ccda_doc = parse_ccda(ccda_xml)

    # Stage 2: Map C-CDA models to FHIR models
    fhir_resources = map_to_fhir(ccda_doc)

    # Stage 3: Assemble and serialize Bundle
    bundle = create_bundle(fhir_resources)
    return bundle.model_dump(exclude_none=True)
```

## File Structure

```
src/ccda_to_fhir/
├── convert.py                 # Main entry point
├── ccda/                      # C-CDA parsing (Stage 1)
│   ├── __init__.py
│   ├── parser.py              # XML → C-CDA models
│   └── models/
│       ├── __init__.py
│       ├── datatypes.py       # II, CD, AD, PN, TEL, TS, PQ, etc.
│       ├── document.py        # ClinicalDocument, Section, etc.
│       ├── entries.py         # Act, Observation, Procedure, etc.
│       └── participants.py    # Author, Performer, Participant
├── fhir/                      # FHIR mapping & serialization (Stages 2-3)
│   ├── __init__.py
│   ├── serializer.py          # Bundle assembly and JSON output
│   ├── models/
│   │   ├── __init__.py
│   │   ├── datatypes.py       # Identifier, CodeableConcept, etc.
│   │   └── resources/
│   │       ├── __init__.py
│   │       ├── patient.py
│   │       ├── allergy_intolerance.py
│   │       ├── condition.py
│   │       ├── medication_request.py
│   │       ├── procedure.py
│   │       ├── immunization.py
│   │       ├── observation.py
│   │       ├── diagnostic_report.py
│   │       ├── encounter.py
│   │       ├── document_reference.py
│   │       ├── practitioner.py
│   │       ├── organization.py
│   │       └── bundle.py
│   └── mappers/
│       ├── __init__.py
│       ├── patient.py
│       ├── allergy.py
│       ├── condition.py
│       ├── medication.py
│       ├── procedure.py
│       ├── immunization.py
│       ├── observation.py
│       ├── encounter.py
│       ├── practitioner.py
│       └── document_reference.py
├── utils/                     # Existing utilities (keep)
│   ├── codes.py
│   ├── datatypes.py           # May be refactored into ccda/fhir
│   ├── datetime.py
│   └── oid.py
└── exceptions.py              # Existing exceptions (keep)
```

## Implementation Order

### Phase 1: Foundation
1. **FHIR Data Types** - `fhir/models/datatypes.py`
2. **C-CDA Data Types** - `ccda/models/datatypes.py`
3. **Bundle model** - `fhir/models/resources/bundle.py`

### Phase 2: Patient (simplest resource)
1. **C-CDA Patient models** - `ccda/models/document.py` (RecordTarget, PatientRole, Patient)
2. **C-CDA Parser** - Basic XML parsing for recordTarget
3. **FHIR Patient model** - `fhir/models/resources/patient.py`
4. **Patient mapper** - `fhir/mappers/patient.py`
5. **Wire up convert.py** - Get first test passing

### Phase 3: Clinical Entries (one at a time)
For each resource type:
1. Add C-CDA entry models
2. Extend parser to handle the section/entry
3. Add FHIR resource model
4. Implement mapper
5. Run integration tests

Order:
1. AllergyIntolerance
2. Condition
3. MedicationRequest
4. Procedure
5. Immunization
6. Observation (vital signs, labs, smoking status)
7. DiagnosticReport
8. Encounter
9. DocumentReference
10. Practitioner / Organization

### Phase 4: Polish
1. Reference resolution between resources
2. Provenance tracking
3. Error handling refinement
4. Remove old converter code

## Design Decisions

### Why Pydantic for C-CDA?
- Type safety catches XML parsing errors early
- Self-documenting structure
- Validation at parse time
- Easy to test mappers with in-memory objects

### Why Pydantic for FHIR?
- Ensures output conforms to FHIR schema
- Built-in JSON serialization with `exclude_none=True`
- Can add FHIR-specific validators
- Future: Could use official fhir.resources library

### Handling Optional Fields
- C-CDA: Use `Optional[T]` with `None` default
- FHIR: Use `Optional[T]`, serialize with `exclude_none=True`
- Empty lists: Use `list[T] = Field(default_factory=list)`

### Handling Code Systems
- Reuse existing `utils/oid.py` for OID → URI mapping
- Reuse existing `utils/codes.py` for value mappings

### Error Strategy
- Keep "fail loud" philosophy from existing code
- Raise specific exceptions for unknown codes/structures
- Allow lenient mode via configuration (future)

## Testing Strategy

### Unit Tests
- Test each C-CDA model can be instantiated
- Test each FHIR model can be instantiated and serialized
- Test each mapper in isolation with mock C-CDA objects

### Integration Tests
- Located in `tests/integration/`
- Currently skipped, will be enabled as implementation progresses
- Test full pipeline: XML string → JSON Bundle

## Existing Code to Preserve

The following utilities are well-designed and should be reused:

- `utils/oid.py` - OID to URI mapping (65+ mappings)
- `utils/codes.py` - Value set mappings (gender, status, etc.)
- `utils/datetime.py` - HL7 datetime parsing
- `exceptions.py` - Custom exception hierarchy

The existing `converters/` and `parsers/` can be referenced for logic but will be replaced by the new architecture.

## Success Criteria

1. All 126 integration tests pass
2. Type-safe throughout (mypy strict passes)
3. No regression in supported C-CDA sections
4. Clear separation between parsing, mapping, serialization
