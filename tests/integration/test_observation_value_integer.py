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


def _find_all_resources_in_bundle(bundle: JSONObject, resource_type: str) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


class TestObservationValueInteger:
    def test_converts_int_value_to_value_integer(
        self
    ) -> None:
        """Test that INT observation value is converted to valueInteger.

        Tests rare but valid C-CDA INT type conversion to FHIR valueInteger.
        INT values are uncommon in real C-CDA documents but must be supported.
        """
        # Create a simple observation with INT value
        observation_xml = """
        <organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test-organizer"/>
            <code code="test-panel" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="test-obs"/>
                    <code code="test-code" codeSystem="2.16.840.1.113883.6.1"
                          displayName="Test Integer Observation"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20240101120000"/>
                    <value value="42" xsi:type="INT" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>
                </observation>
            </component>
        </organizer>
        """

        ccda_doc = wrap_in_ccda_document(observation_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be in bundle
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0, "Must have at least one Observation"

        observation = observations[0]
        assert observation["resourceType"] == "Observation"

        # Verify INT → valueInteger conversion
        assert "valueInteger" in observation, "Observation must have valueInteger for INT type"
        assert observation["valueInteger"] == 42, "valueInteger must match C-CDA INT value"

        # Ensure no other value types are present
        assert "valueQuantity" not in observation, "Should not have valueQuantity for INT type"
        assert "valueString" not in observation, "Should not have valueString for INT type"
        assert "valueCodeableConcept" not in observation, "Should not have valueCodeableConcept for INT type"

    def test_converts_int_value_zero(
        self
    ) -> None:
        """Test that INT value of 0 is correctly converted."""
        observation_xml = """
        <organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="test-organizer"/>
            <code code="test-panel" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="test-obs-zero"/>
                    <code code="test-code" codeSystem="2.16.840.1.113883.6.1"
                          displayName="Test Zero Value"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20240101120000"/>
                    <value value="0" xsi:type="INT" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>
                </observation>
            </component>
        </organizer>
        """

        ccda_doc = wrap_in_ccda_document(observation_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0

        observation = observations[0]

        # Verify zero is correctly handled (not None, not omitted)
        assert "valueInteger" in observation, "Must have valueInteger even for value 0"
        assert observation["valueInteger"] == 0, "valueInteger must be 0"
        assert isinstance(observation["valueInteger"], int), "valueInteger must be int type"
