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

class TestProcedureNegation:
    def test_converts_negated_procedure(
        self, ccda_procedure_negated: str
    ) -> None:
        """Test that negationInd=true is converted to status=not-done."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_negated, TemplateIds.PROCEDURES_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "not-done"
