"""Pytest configuration and shared fixtures for integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

# NOTE: Conversion tests are skipped until converter is implemented
# from ccda_to_fhir.convert import convert_document

# Skip conversion integration tests until the new converter is implemented
# Validation integration tests can run independently
SKIP_REASON = "Integration tests skipped until C-CDA Pydantic -> FHIR Pydantic pipeline is implemented"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip conversion tests (but allow validation tests)."""
    for item in items:
        # Only skip conversion tests, not validation tests
        if "/integration/" in str(item.fspath) and "conversion" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason=SKIP_REASON))

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CCDA_FIXTURES_DIR = FIXTURES_DIR / "ccda"
FHIR_FIXTURES_DIR = FIXTURES_DIR / "fhir"


def wrap_in_ccda_document(
    section_content: str,
    section_template_id: str | None = None,
    section_code: str | None = None,
) -> str:
    """Wrap a C-CDA fragment in a minimal valid C-CDA document structure.

    This allows testing with XML fragments while still going through
    the full document conversion pipeline.
    """
    section_template = ""
    if section_template_id:
        section_template = f'<templateId root="{section_template_id}"/>'

    section_code_elem = ""
    if section_code:
        section_code_elem = f'<code code="{section_code}" codeSystem="2.16.840.1.113883.6.1"/>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    {section_content}
    <component>
        <structuredBody>
            <component>
                <section>
                    {section_template}
                    {section_code_elem}
                    {section_content}
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""


# @pytest.fixture
# def converter() -> type:
#     """Provide the convert_document function for integration tests."""
#     return convert_document


@pytest.fixture
def ccda_patient() -> str:
    """Load C-CDA patient fixture."""
    return (CCDA_FIXTURES_DIR / "patient.xml").read_text()


@pytest.fixture
def fhir_patient() -> dict[str, Any]:
    """Load expected FHIR patient fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "patient.json").read_text())


@pytest.fixture
def ccda_allergy() -> str:
    """Load C-CDA allergy fixture."""
    return (CCDA_FIXTURES_DIR / "allergy.xml").read_text()


@pytest.fixture
def fhir_allergy() -> dict[str, Any]:
    """Load expected FHIR allergy fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "allergy.json").read_text())


@pytest.fixture
def ccda_problem() -> str:
    """Load C-CDA problem fixture."""
    return (CCDA_FIXTURES_DIR / "problem.xml").read_text()


@pytest.fixture
def fhir_problem() -> dict[str, Any]:
    """Load expected FHIR problem/condition fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "problem.json").read_text())


@pytest.fixture
def ccda_immunization() -> str:
    """Load C-CDA immunization fixture."""
    return (CCDA_FIXTURES_DIR / "immunization.xml").read_text()


@pytest.fixture
def fhir_immunization() -> dict[str, Any]:
    """Load expected FHIR immunization fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "immunization.json").read_text())


@pytest.fixture
def ccda_medication() -> str:
    """Load C-CDA medication fixture."""
    return (CCDA_FIXTURES_DIR / "medication.xml").read_text()


@pytest.fixture
def fhir_medication() -> dict[str, Any]:
    """Load expected FHIR medication request fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "medication.json").read_text())


@pytest.fixture
def ccda_procedure() -> str:
    """Load C-CDA procedure fixture."""
    return (CCDA_FIXTURES_DIR / "procedure.xml").read_text()


@pytest.fixture
def fhir_procedure() -> dict[str, Any]:
    """Load expected FHIR procedure fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "procedure.json").read_text())


@pytest.fixture
def ccda_result() -> str:
    """Load C-CDA result/lab fixture."""
    return (CCDA_FIXTURES_DIR / "result.xml").read_text()


@pytest.fixture
def fhir_result() -> dict[str, Any]:
    """Load expected FHIR diagnostic report fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "result.json").read_text())


@pytest.fixture
def ccda_encounter() -> str:
    """Load C-CDA encounter fixture."""
    return (CCDA_FIXTURES_DIR / "encounter.xml").read_text()


@pytest.fixture
def fhir_encounter() -> dict[str, Any]:
    """Load expected FHIR encounter fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "encounter.json").read_text())


@pytest.fixture
def ccda_note() -> str:
    """Load C-CDA note fixture."""
    return (CCDA_FIXTURES_DIR / "note.xml").read_text()


@pytest.fixture
def fhir_note() -> dict[str, Any]:
    """Load expected FHIR document reference fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "note.json").read_text())


@pytest.fixture
def ccda_vital_signs() -> str:
    """Load C-CDA vital signs fixture."""
    return (CCDA_FIXTURES_DIR / "vital_signs.xml").read_text()


@pytest.fixture
def fhir_vital_signs() -> dict[str, Any]:
    """Load expected FHIR vital signs observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "vital_signs.json").read_text())


@pytest.fixture
def ccda_smoking_status() -> str:
    """Load C-CDA smoking status fixture."""
    return (CCDA_FIXTURES_DIR / "smoking_status.xml").read_text()


@pytest.fixture
def fhir_smoking_status() -> dict[str, Any]:
    """Load expected FHIR smoking status observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "smoking_status.json").read_text())


@pytest.fixture
def ccda_pregnancy() -> str:
    """Load C-CDA pregnancy observation fixture."""
    return (CCDA_FIXTURES_DIR / "pregnancy.xml").read_text()


@pytest.fixture
def fhir_pregnancy() -> dict[str, Any]:
    """Load expected FHIR pregnancy observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "pregnancy.json").read_text())


@pytest.fixture
def ccda_author() -> str:
    """Load C-CDA author fixture."""
    return (CCDA_FIXTURES_DIR / "author.xml").read_text()


@pytest.fixture
def fhir_practitioner() -> dict[str, Any]:
    """Load expected FHIR practitioner fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "practitioner.json").read_text())
