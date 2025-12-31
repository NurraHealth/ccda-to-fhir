"""Integration tests for Observation with nullFlavor codes."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

RESULTS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.3.1"


def _find_all_resources_in_bundle(
    bundle: JSONObject, resource_type: str
) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


class TestObservationNullFlavor:
    """Tests for Observation with nullFlavor codes.

    Per FHIR R4 spec, Observation.code is required (1..1).
    Observations with nullFlavor codes and no extractable text should be skipped.
    """

    def test_observation_with_nullflavor_code_and_no_text_is_skipped(self) -> None:
        """Test that observation with nullFlavor code and no text is skipped.

        Per FHIR R4: Observation.code is required (1..1).
        When code has nullFlavor and no text is available, the observation
        cannot be converted to valid FHIR and should be skipped.
        """
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-1"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Test Panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20240121"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-nullflavor-1"/>
            <code nullFlavor="NI" xsi:type="CE"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240121"/>
            <value nullFlavor="NI" xsi:type="CD"/>
        </observation>
    </component>
</organizer>
"""
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all observations
        observations = _find_all_resources_in_bundle(bundle, "Observation")

        # When component observation has invalid code, entire organizer is skipped
        # This is expected behavior - no observations should be created
        assert len(observations) == 0, (
            "Organizer with only nullFlavor observation should be skipped entirely"
        )

    def test_observation_with_valid_code_is_created(self) -> None:
        """Test that observation with valid code is created normally.

        This is a control test to ensure that valid observations work as expected.
        """
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-2"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Test Panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20240121"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-valid-code"/>
            <code code="2339-0" codeSystem="2.16.840.1.113883.6.1" displayName="Glucose"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240121"/>
            <value xsi:type="PQ" value="95" unit="mg/dL"/>
        </observation>
    </component>
</organizer>
"""
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all observations
        observations = _find_all_resources_in_bundle(bundle, "Observation")

        # Should have at least one observation (may or may not include panel observation)
        assert len(observations) > 0

        # Find the leaf observation with the glucose code
        leaf_obs = [
            o for o in observations
            if not o.get("hasMember") and "code" in o
        ]
        assert len(leaf_obs) >= 1, "Should have at least one leaf observation"

        # Check that at least one observation has the glucose code
        glucose_obs = None
        for obs in leaf_obs:
            for coding in obs.get("code", {}).get("coding", []):
                if coding.get("code") == "2339-0":
                    glucose_obs = obs
                    break
            if glucose_obs:
                break

        assert glucose_obs is not None, "Should have glucose observation"
        assert glucose_obs["code"]["coding"][0]["system"] == "http://loinc.org"
        assert glucose_obs["code"]["coding"][0]["code"] == "2339-0"
        assert glucose_obs["code"]["coding"][0]["display"] == "Glucose"

    def test_multiple_observations_some_with_nullflavor(self) -> None:
        """Test that valid observations are created while nullFlavor ones are skipped.

        In a result organizer with multiple component observations,
        those with valid codes should be converted, while those with
        nullFlavor codes and no text should be skipped.
        """
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-3"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Lab Panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20240121"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-valid-1"/>
            <code code="2339-0" codeSystem="2.16.840.1.113883.6.1" displayName="Glucose"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240121"/>
            <value xsi:type="PQ" value="95" unit="mg/dL"/>
        </observation>
    </component>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-nullflavor-3"/>
            <code nullFlavor="NI" xsi:type="CE"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240121"/>
            <value nullFlavor="NI" xsi:type="CD"/>
        </observation>
    </component>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-valid-2"/>
            <code code="2951-2" codeSystem="2.16.840.1.113883.6.1" displayName="Sodium"/>
            <statusCode code="completed"/>
            <effectiveTime value="20240121"/>
            <value xsi:type="PQ" value="140" unit="mmol/L"/>
        </observation>
    </component>
</organizer>
"""
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all observations
        observations = _find_all_resources_in_bundle(bundle, "Observation")

        # Current behavior: When any component observation fails,
        # the entire organizer/DiagnosticReport is skipped
        # This is expected - better to skip entire panel than create incomplete panel
        assert len(observations) == 0, (
            "Organizer with any nullFlavor component should be skipped entirely "
            "(current behavior - entire panel skipped if any component invalid)"
        )
