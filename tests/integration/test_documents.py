"""Integration tests for C-CDA to FHIR document conversion.

Each test case is a simple input/output comparison:
- Input: Complete C-CDA XML document
- Output: Expected FHIR JSON Bundle

Tests are parameterized by document name. For each document "foo":
- fixtures/documents/foo.xml contains the input C-CDA
- fixtures/documents/foo.json contains the expected FHIR Bundle
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def get_document_test_cases() -> list[str]:
    """Find all document test cases (pairs of .xml and .json files)."""
    xml_files = sorted(DOCUMENTS_DIR.glob("*.xml"))
    return [f.stem for f in xml_files if (DOCUMENTS_DIR / f"{f.stem}.json").exists()]


@pytest.mark.parametrize("document_name", get_document_test_cases())
def test_document_conversion(document_name: str) -> None:
    """Test that a C-CDA document converts to the expected FHIR Bundle.

    Args:
        document_name: Base name of the test case (without extension).
            The test loads {document_name}.xml as input and compares
            the output to {document_name}.json.
    """
    # Load input XML
    xml_path = DOCUMENTS_DIR / f"{document_name}.xml"
    ccda_xml = xml_path.read_text()

    # Load expected output JSON
    json_path = DOCUMENTS_DIR / f"{document_name}.json"
    expected_bundle = json.loads(json_path.read_text())

    # Convert and compare
    actual_bundle = convert_document(ccda_xml)

    assert actual_bundle == expected_bundle, (
        f"Conversion output does not match expected for {document_name}.\n"
        f"Expected: {json.dumps(expected_bundle, indent=2)}\n"
        f"Actual: {json.dumps(actual_bundle, indent=2)}"
    )
