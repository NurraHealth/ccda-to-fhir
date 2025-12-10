# ccda-to-fhir

A Python library to convert C-CDA (Consolidated Clinical Document Architecture) documents to FHIR R4B resources.

## Design Principles

### Fail Loud and Clear

This library is designed to **fail loudly** when it encounters unexpected data. Rather than silently dropping data or making assumptions, it will raise clear exceptions when:

- An unknown code system OID is encountered
- An unmapped status code is found
- A required element is missing or malformed
- An unexpected XML structure is detected

This ensures data integrity and makes it immediately obvious when the converter needs to be extended to handle new cases.

```python
from ccda_to_fhir import convert
from ccda_to_fhir.exceptions import UnknownCodeSystemError, UnmappedValueError

try:
    bundle = convert(xml_content)
except UnknownCodeSystemError as e:
    print(f"Unknown code system: {e.oid}")
except UnmappedValueError as e:
    print(f"Unmapped value '{e.value}' for {e.field}")
```

## 🚧 C-CDA Validation (Work in Progress)

> **Note**: This library includes C-CDA conformance validation based on the C-CDA R2.1 specification. The validation system is currently **under active development** and not all features are complete.

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

### What's Not Yet Complete

- 🚧 **C-CDA to FHIR Conversion**: The conversion pipeline from C-CDA models to FHIR resources is not yet implemented
- 🚧 **Section-level validation**: Some nested section structures may not parse correctly (known issue with forward references)
- 🚧 **Complete template coverage**: Additional C-CDA templates beyond the 16 listed above are not yet validated
- 🚧 **Warning/soft validation mode**: All validation errors are currently hard failures

### Current Status

**C-CDA Parsing & Validation:**
- ✅ 143 unit tests passing (validation + parser)
- ✅ 7 integration tests passing (validation with real C-CDA documents)
- ✅ 16/16 planned validators complete (100%)

**FHIR Models:**
- ✅ FHIR R4B models available via [`fhir.resources`](https://github.com/nazrulworld/fhir.resources) library
- ✅ Complete Pydantic models for all FHIR resources and datatypes
- ✅ Wrapper module at `ccda_to_fhir.fhir.models` for easy imports

**For More Details:** See [VALIDATION_IMPLEMENTATION_PLAN.md](VALIDATION_IMPLEMENTATION_PLAN.md)

## Installation

```bash
pip install ccda-to-fhir
```

Or with uv:

```bash
uv add ccda-to-fhir
```

## Usage

```python
from ccda_to_fhir import convert, convert_file

# From string/bytes
with open("patient_record.xml") as f:
    bundle = convert(f.read())

# From file path
bundle = convert_file("patient_record.xml")
```

## Supported Resources

Based on the [HL7 C-CDA on FHIR](https://build.fhir.org/ig/HL7/ccda-on-fhir/) mapping specification:

| C-CDA Section | FHIR Resource |
|---------------|---------------|
| Patient (recordTarget) | Patient |
| Allergies | AllergyIntolerance |
| Problems | Condition |
| Medications | MedicationRequest |
| Immunizations | Immunization |
| Procedures | Procedure |
| Results | DiagnosticReport, Observation |
| Vital Signs | Observation |
| Social History | Observation |
| Encounters | Encounter |
| Notes | DocumentReference |
| Author/Performer | Practitioner, PractitionerRole |

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
