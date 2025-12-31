from __future__ import annotations

from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

SOCIAL_HISTORY_TEMPLATE_ID = TemplateIds.SOCIAL_HISTORY_SECTION


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestPregnancyIntentionObservation:
    def test_converts_pregnancy_intention_code(
        self, ccda_pregnancy_intention: str
    ) -> None:
        """Test that pregnancy intention code (86645-9) is converted correctly."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_intention, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "code" in observation

        code_coding = observation["code"]["coding"][0]
        assert code_coding["system"] == "http://loinc.org"
        assert code_coding["code"] == "86645-9"
        assert "Pregnancy intention" in code_coding["display"]

    def test_converts_pregnancy_intention_value(
        self, ccda_pregnancy_intention: str
    ) -> None:
        """Test that pregnancy intention value is converted to valueCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_intention, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "valueCodeableConcept" in observation

        value_coding = observation["valueCodeableConcept"]["coding"][0]
        assert value_coding["system"] == "http://snomed.info/sct"
        assert value_coding["code"] == "454381000124105"
        assert "Wants to become pregnant" in value_coding["display"]

    def test_category_is_social_history(
        self, ccda_pregnancy_intention: str
    ) -> None:
        """Test that pregnancy intention has social-history category."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_intention, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "category" in observation
        assert len(observation["category"]) > 0

        category_coding = observation["category"][0]["coding"][0]
        assert category_coding["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"
        assert category_coding["code"] == "social-history"

    def test_converts_status(
        self, ccda_pregnancy_intention: str
    ) -> None:
        """Test that pregnancy intention status is converted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_intention, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert observation["status"] == "final"

    def test_converts_effective_date(
        self, ccda_pregnancy_intention: str
    ) -> None:
        """Test that pregnancy intention effectiveTime is converted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_intention, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "effectiveDateTime" in observation
        assert "2024-01-15" in observation["effectiveDateTime"]
