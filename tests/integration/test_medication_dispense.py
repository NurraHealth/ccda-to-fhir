"""E2E tests for MedicationDispense resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

MEDICATIONS_SECTION_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.1.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestMedicationDispenseConversion:
    """E2E tests for C-CDA Supply to FHIR MedicationDispense conversion."""

    def test_medication_required_when_no_product_code(
        self, ccda_medication_dispense_no_product_code: str
    ) -> None:
        """Test that MedicationDispense without medication code is not created.

        Per FHIR R4B spec and user code review, medication[x] is required (1..1 cardinality).
        When C-CDA Supply has nullFlavor product code, the MedicationDispense should not be created
        rather than using data-absent-reason (which violates FHIR spec).

        This ensures strict validation and FHIR compliance.
        """
        ccda_doc = wrap_in_ccda_document(
            ccda_medication_dispense_no_product_code, MEDICATIONS_SECTION_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # MedicationDispense should NOT be created when medication code is missing
        med_dispense = _find_resource_in_bundle(bundle, "MedicationDispense")
        assert med_dispense is None, (
            "MedicationDispense should not be created when medication code is missing. "
            "medication[x] is required (1..1 cardinality) per FHIR R4B spec."
        )
