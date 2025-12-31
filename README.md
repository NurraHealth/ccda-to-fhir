# ccda-to-fhir

A Python library to convert C-CDA (Consolidated Clinical Document Architecture) documents to FHIR R4B resources.

## Quick Start

```python
from ccda_to_fhir import convert_document

# Convert C-CDA document
with open('patient_record.xml') as f:
    result = convert_document(f.read())

# Access the FHIR Bundle
bundle = result["bundle"]
print(f"Converted {len(bundle['entry'])} resources")

# Access conversion metadata
metadata = result["metadata"]
print(f"Processed templates: {len(metadata['processed_templates'])}")
print(f"Skipped templates: {len(metadata['skipped_templates'])}")
print(f"Errors: {len(metadata['errors'])}")
```

## Design Principles

### Fail Loud and Clear

This library is designed to **fail loudly** when it encounters unexpected data. Rather than silently dropping data or making assumptions, it will raise clear exceptions when:

- An unknown code system OID is encountered
- An unmapped status code is found
- A required element is missing or malformed
- An unexpected XML structure is detected

This ensures data integrity and makes it immediately obvious when the converter needs to be extended to handle new cases.

```python
from ccda_to_fhir import convert_document
from ccda_to_fhir.exceptions import UnknownCodeSystemError, UnmappedValueError

try:
    result = convert_document(xml_content)
    bundle = result["bundle"]
except UnknownCodeSystemError as e:
    print(f"Unknown code system: {e.oid}")
except UnmappedValueError as e:
    print(f"Unmapped value '{e.value}' for {e.field}")
```

## C-CDA Validation

This library includes C-CDA conformance validation based on the C-CDA R2.1 specification. Validation happens automatically during parsing to ensure documents meet C-CDA requirements.

### What's Working

The library validates C-CDA documents during parsing and will raise errors if documents violate C-CDA conformance requirements. Currently implemented validators (16 templates):

**Document Level:**
- ✅ US Realm Header (2.16.840.1.113883.10.20.22.1.1)

**Clinical Statements:**
- ✅ Problem Observation (2.16.840.1.113883.10.20.22.4.4)
- ✅ Problem Concern Act (2.16.840.1.113883.10.20.22.4.3)
- ✅ Allergy Observation (2.16.840.1.113883.10.20.22.4.7)
- ✅ Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30)
- ✅ Medication Activity (2.16.840.1.113883.10.20.22.4.16)
- ✅ Immunization Activity (2.16.840.1.113883.10.20.22.4.52)
- ✅ Procedure Activity (2.16.840.1.113883.10.20.22.4.14)
- ✅ Encounter Activity (2.16.840.1.113883.10.20.22.4.49)
- ✅ Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27)
- ✅ Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26)
- ✅ Result Observation (2.16.840.1.113883.10.20.22.4.2)
- ✅ Result Organizer (2.16.840.1.113883.10.20.22.4.1)
- ✅ Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78)
- ✅ Social History Observation (2.16.840.1.113883.10.20.22.4.38)
- ✅ Family History Observation (2.16.840.1.113883.10.20.22.4.46)

### How Validation Works

Validation happens automatically during parsing. If a C-CDA document violates conformance requirements, a `MalformedXMLError` will be raised with a detailed message:

```python
from ccda_to_fhir.ccda.parser import parse_ccda, MalformedXMLError

xml = """<?xml version="1.0"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="UK"/>  <!-- Invalid: Must be "US" for US Realm Header -->
    <!-- ... -->
</ClinicalDocument>
"""

try:
    doc = parse_ccda(xml)
except MalformedXMLError as e:
    print(f"Validation error: {e}")
    # Output: US Realm Header (2.16.840.1.113883.10.20.22.1.1):
    #         realmCode SHALL be 'US', found 'UK'
```

### Implementation Status

**Overall:** 🟡 **ALPHA** - Comprehensive feature set with ongoing testing and refinement

**Test Coverage:**
- ✅ **1928 tests passing** (validation, parsing, conversion, and E2E tests)
- ✅ 16 C-CDA template validators implemented
- ✅ 25+ resource types with conversion support
- ✅ 100% specification compliance for implemented features

**C-CDA → FHIR Conversion:**
- ✅ **Patient**: 100% complete (21/21 features - zero gaps!) 🎉
- ✅ **Condition**: 100% complete (16/16 features - zero gaps!)
- ✅ **AllergyIntolerance**: 100% complete (15/15 features - zero gaps!)
- ✅ **Observation/Results**: 100% complete (17/17 features - zero gaps!)
- ✅ **Procedure**: 100% complete (14/14 features - zero gaps!)
- ✅ **Immunization**: 100% complete (15/15 features - zero gaps!)
- ✅ **MedicationRequest**: 100% complete (17/17 features - zero gaps!)
- ✅ **Encounter**: 100% complete (15/15 features - zero gaps!)
- ✅ **Vital Signs**: 100% complete (17/17 features - zero gaps!)
- ✅ **Social History**: 100% complete (13/13 features - zero gaps!)
- ✅ **Notes/DocumentReference**: 100% complete (14/14 features - zero gaps!)
- ✅ **Participations (Provenance)**: 100% complete (19/19 features - zero gaps!)

**FHIR Models:**
- ✅ FHIR R4B models available via [`fhir.resources`](https://github.com/nazrulworld/fhir.resources) library
- ✅ Complete Pydantic models for all FHIR resources and datatypes
- ✅ Wrapper module at `ccda_to_fhir.fhir.models` for easy imports

**For More Details:** See [docs/mapping/](docs/mapping/) for comprehensive field-level mapping documentation

## Installation

```bash
pip install ccda-to-fhir
```

Or with uv:

```bash
uv add ccda-to-fhir
```

## Supported C-CDA Templates

Based on the [HL7 C-CDA on FHIR](https://build.fhir.org/ig/HL7/ccda-on-fhir/) mapping specification:

### Document Level
- ✅ US Realm Header (2.16.840.1.113883.10.20.22.1.1)

### Clinical Statements
- ✅ Problem Concern Act (2.16.840.1.113883.10.20.22.4.3) → Condition
- ✅ Problem Observation (2.16.840.1.113883.10.20.22.4.4) → Condition
- ✅ Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30) → AllergyIntolerance
- ✅ Allergy Observation (2.16.840.1.113883.10.20.22.4.7) → AllergyIntolerance
- ✅ Medication Activity (2.16.840.1.113883.10.20.22.4.16) → MedicationRequest
- ✅ Immunization Activity (2.16.840.1.113883.10.20.22.4.52) → Immunization
- ✅ Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14) → Procedure
- ✅ Procedure Activity Act (2.16.840.1.113883.10.20.22.4.12) → Procedure
- ✅ Encounter Activity (2.16.840.1.113883.10.20.22.4.49) → Encounter
- ✅ Result Organizer (2.16.840.1.113883.10.20.22.4.1) → DiagnosticReport
- ✅ Result Observation (2.16.840.1.113883.10.20.22.4.2) → Observation
- ✅ Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26) → Observation (vital-signs)
- ✅ Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27) → Observation (vital-signs)
- ✅ Social History Observation (2.16.840.1.113883.10.20.22.4.38) → Observation
- ✅ Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78) → Observation
- ✅ Pregnancy Observation (2.16.840.1.113883.10.20.15.3.8) → Observation
- ✅ Note Activity (2.16.840.1.113883.10.20.22.4.202) → DocumentReference

### Supporting Templates
- ✅ Author Participation (2.16.840.1.113883.10.20.22.4.119) → Practitioner, PractitionerRole, Provenance
- ✅ Comment Activity (2.16.840.1.113883.10.20.22.4.64) → Annotation (notes)
- ✅ Assessment Scale Observation (2.16.840.1.113883.10.20.22.4.69) → Evidence
- ✅ Date of Diagnosis Act (2.16.840.1.113883.10.20.22.4.502) → Extension

## Resource Mapping Summary

| C-CDA Section/Entry | FHIR Resource | Implementation |
|---------------------|---------------|----------------|
| Patient (recordTarget) | Patient | ✅ 100% (21/21 features) |
| Problems | Condition | ✅ 100% (16/16 features) |
| Allergies | AllergyIntolerance | ✅ 100% (15/15 features) |
| Medications | MedicationRequest, MedicationStatement | ✅ 100% (17/17 features) |
| Immunizations | Immunization | ✅ 100% (15/15 features) |
| Procedures | Procedure | ✅ 100% (14/14 features) |
| Results | DiagnosticReport, Observation | ✅ 100% (17/17 features) |
| Vital Signs | Observation (vital-signs) | ✅ 100% (17/17 features) |
| Social History | Observation | ✅ 100% (13/13 features) |
| Encounters | Encounter | ✅ 100% (15/15 features) |
| Notes | DocumentReference | ✅ 100% (14/14 features) |
| Authors/Performers | Practitioner, PractitionerRole, Provenance | ✅ 100% (19/19 features) |

**For detailed feature mapping:** See [docs/mapping/](docs/mapping/) for comprehensive field-level documentation

## Key Features

### Standards Compliance
- ✅ **100% HL7 C-CDA on FHIR IG v2.0.0 compliant** for implemented features
- ✅ **US Core profiles** (Patient, AllergyIntolerance, Condition, Observation, etc.)
- ✅ **FHIR R4 specification** with R4B compatibility

### Advanced Mapping Support
- ✅ **Complex nested structures**: Blood pressure components, pregnancy observations with EDD/gestational age/LMP
- ✅ **Complete provenance tracking**: Multi-author support with Provenance resources
- ✅ **Narrative preservation**: Section text/reference resolution to FHIR Narrative
- ✅ **Extension support**: US Core extensions (race, ethnicity, birthsex, tribal affiliation, sex parameter)
- ✅ **Body site qualifiers**: Laterality support for procedures and vital signs
- ✅ **SDOH categorization**: 44+ LOINC codes mapped to 15 SDOH domains
- ✅ **DiagnosticReport generation**: Result organizers with standalone observations
- ✅ **Reference ranges**: Complex vital signs reference range mapping
- ✅ **Negation handling**: No-known-allergy, refuted conditions, not-done procedures

### Data Type Coverage
- ✅ All standard C-CDA data types (CD, CE, PQ, IVL_TS, IVL_PQ, ED, etc.)
- ✅ Period-based effective times (effectivePeriod for time ranges)
- ✅ Encapsulated data (ED type → valueAttachment via R5 backport extension)
- ✅ NullFlavor → data-absent-reason mappings
- ✅ Qualifier support (body site laterality, etc.)

## Performance

- **Parsing speed**: ~50-100ms for typical C-CDA documents (1-10 sections)
- **Memory usage**: Proportional to document size; ~10-20MB for standard documents
- **Scalability**: Tested with documents up to 1000+ clinical statements
- **Bundle size**: Average 10-50 FHIR resources per C-CDA document

**Note**: Performance may vary based on document complexity, section count, and clinical statement density.

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
# Clone the repository
git clone https://github.com/nurra/ccda-to-fhir.git
cd ccda-to-fhir

# Install dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .
uv run mypy src/
```

## License

MIT
