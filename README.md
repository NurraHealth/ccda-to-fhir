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
