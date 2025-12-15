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

class TestObservationRange:
    def test_converts_ivl_pq_value_range(
        self, ccda_observation_ivl_pq: str
    ) -> None:
        """Test that IVL_PQ observation value is converted to valueRange.

        Result Observations must be within Result Organizers per C-CDA spec.
        This test verifies IVL_PQ conversion works within compliant structure.
        """
        ccda_doc = wrap_in_ccda_document(ccda_observation_ivl_pq, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be in contained array
        assert "contained" in report
        assert len(report["contained"]) > 0
        observation = report["contained"][0]
        assert observation["resourceType"] == "Observation"

        # Verify IVL_PQ → valueRange conversion
        assert "valueRange" in observation
        assert "valueQuantity" not in observation

        val_range = observation["valueRange"]
        assert val_range["low"]["value"] == 4.0
        assert val_range["low"]["unit"] == "10*9/L"
        assert val_range["high"]["value"] == 11.0
        assert val_range["high"]["unit"] == "10*9/L"