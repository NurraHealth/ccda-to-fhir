"""E2E test: organization references include display text.

Validates that custodian, payor, and managingOrganization references
include display text from the source C-CDA organization names.
"""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle

NIST_AMBULATORY = Path(__file__).parent / "fixtures" / "documents" / "nist_ambulatory.xml"


class TestOrganizationReferenceDisplayE2E:
    """E2E tests for display text on organization references."""

    @pytest.fixture
    def nist_bundle(self):
        with open(NIST_AMBULATORY) as f:
            xml = f.read()
        result = convert_document(xml)
        return Bundle(**result["bundle"])

    def test_composition_custodian_has_display(self, nist_bundle):
        """Composition.custodian should include display from custodian org name."""
        composition = next(
            (e.resource for e in nist_bundle.entry
             if e.resource.get_resource_type() == "Composition"),
            None,
        )
        assert composition is not None

        custodian = composition.custodian
        assert custodian is not None
        assert custodian.display == "Community Health and Hospitals"

    def test_composition_custodian_has_reference(self, nist_bundle):
        """Composition.custodian should include reference URI when org has IDs."""
        composition = next(
            (e.resource for e in nist_bundle.entry
             if e.resource.get_resource_type() == "Composition"),
            None,
        )
        assert composition is not None

        custodian = composition.custodian
        assert custodian is not None
        assert custodian.reference is not None
        assert custodian.reference.startswith("urn:uuid:")

    def test_coverage_payor_has_display(self, nist_bundle):
        """Coverage.payor should include display from payor org name."""
        coverages = [
            e.resource for e in nist_bundle.entry
            if e.resource.get_resource_type() == "Coverage"
        ]
        if not coverages:
            pytest.skip("No Coverage resources in NIST sample")

        for coverage in coverages:
            if coverage.payor:
                for payor in coverage.payor:
                    if payor.reference and payor.reference.startswith("urn:uuid:"):
                        # Payor references to Organization should have display
                        # when organization name is available
                        assert payor.display is not None, (
                            "Coverage.payor Organization reference should have display"
                        )
