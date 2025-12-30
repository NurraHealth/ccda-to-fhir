from __future__ import annotations

from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None

class TestMedicationNegation:
    def test_converts_negated_medication(
        self, ccda_medication_negated: str
    ) -> None:
        """Test that negationInd=true is converted to doNotPerform=True."""
        ccda_doc = wrap_in_ccda_document(ccda_medication_negated, TemplateIds.MEDICATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        med_request = _find_resource_in_bundle(bundle, "MedicationRequest")
        assert med_request is not None
        assert med_request.get("doNotPerform") is True
