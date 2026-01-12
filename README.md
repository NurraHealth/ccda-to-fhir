# ccda-to-fhir

A Python library for converting C-CDA documents to FHIR R4B resources.

Built for **reliability**: the library fails loudly on unexpected data rather than silently dropping information, ensuring you always know when something needs attention.

## Installation

```bash
pip install ccda-to-fhir
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add ccda-to-fhir
```

## Quick Start

```python
from ccda_to_fhir import convert_document

with open("patient_record.xml") as f:
    result = convert_document(f.read())

bundle = result["bundle"]
print(f"Converted {len(bundle['entry'])} resources")
```

## What Gets Converted

The library converts clinical data from C-CDA sections into their FHIR equivalents:

| C-CDA Section | FHIR Resource |
|---------------|---------------|
| Patient (recordTarget) | Patient |
| Problems | Condition |
| Allergies | AllergyIntolerance |
| Medications | MedicationRequest, MedicationStatement |
| Immunizations | Immunization |
| Procedures | Procedure |
| Lab Results | DiagnosticReport, Observation |
| Vital Signs | Observation (vital-signs profile) |
| Social History | Observation |
| Encounters | Encounter |
| Notes | DocumentReference |
| Authors/Performers | Practitioner, PractitionerRole, Provenance |

Each conversion follows the [HL7 C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/) and produces US Core-compliant resources.

## Features

**Standards Compliance**
- FHIR R4B with US Core profile support
- HL7 C-CDA on FHIR IG v2.0.0 mapping specification
- C-CDA R2.1 conformance validation during parsing

**Clinical Data Handling**
- Complex structures: blood pressure components, pregnancy observations with EDD/gestational age
- Provenance tracking with multi-author support
- Negation patterns: no-known-allergies, refuted conditions, not-done procedures
- Body site qualifiers with laterality
- Reference ranges for vital signs and lab results

**Data Types**
- All C-CDA data types (CD, CE, PQ, IVL_TS, IVL_PQ, ED, etc.)
- NullFlavor to data-absent-reason mapping
- US Core extensions (race, ethnicity, birth sex, tribal affiliation)

## Error Handling

The library raises specific exceptions when it encounters data it cannot handle:

```python
from ccda_to_fhir import convert_document
from ccda_to_fhir.exceptions import UnknownCodeSystemError, UnmappedValueError

try:
    result = convert_document(xml_content)
except UnknownCodeSystemError as e:
    print(f"Unknown code system OID: {e.oid}")
except UnmappedValueError as e:
    print(f"Unmapped value '{e.value}' for {e.field}")
```

## Conversion Metadata

Track what was processed during conversion:

```python
result = convert_document(xml_content)
metadata = result["metadata"]

print(f"Processed: {len(metadata['processed_templates'])} templates")
print(f"Skipped: {len(metadata['skipped_templates'])} templates")
print(f"Errors: {len(metadata['errors'])}")
```

## Development

```bash
git clone https://github.com/nurra/ccda-to-fhir.git
cd ccda-to-fhir

uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src/
```

## Documentation

See [docs/mapping/](docs/mapping/) for detailed field-level mapping documentation covering each resource type.

## License

MIT
