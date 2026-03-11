"""E2E test: custodian reference includes display text and reference URI."""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle

NIST_AMBULATORY = Path(__file__).parent / "fixtures" / "documents" / "nist_ambulatory.xml"


@pytest.fixture
def nist_bundle():
    with open(NIST_AMBULATORY) as f:
        xml = f.read()
    result = convert_document(xml)
    return Bundle(**result["bundle"])


def test_custodian_has_display_and_reference(nist_bundle):
    composition = next(
        e.resource for e in nist_bundle.entry
        if e.resource.get_resource_type() == "Composition"
    )
    custodian = composition.custodian
    assert custodian.display == "Community Health and Hospitals"
    assert custodian.reference.startswith("urn:uuid:")
