from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.constants import TemplateIds
from .conftest import wrap_in_ccda_document

def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None

class TestImmunizationNegation:
    def test_converts_negated_immunization_reason(
        self, ccda_immunization_negated: str
    ) -> None:
        """Test that negated immunization converts indication to statusReason."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_negated, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        
        # Verify reason is mapped to statusReason, not reasonCode
        assert "statusReason" in immunization
        assert "reasonCode" not in immunization
        
        # Verify the reason content
        reason = immunization["statusReason"]
        coding = reason["coding"][0]
        assert coding["code"] == "PATOBJ"
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActReason"