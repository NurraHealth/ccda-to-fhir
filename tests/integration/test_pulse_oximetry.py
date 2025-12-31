"""E2E tests for pulse oximetry with O2 flow rate and concentration components."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_observations_in_bundle(bundle: JSONObject) -> list[JSONObject]:
    """Find all Observation resources in a FHIR Bundle."""
    observations = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            observations.append(resource)
    return observations


def _get_observation_by_code(observations: list[JSONObject], loinc_code: str) -> JSONObject | None:
    """Find observation by LOINC code."""
    for obs in observations:
        if obs.get("code", {}).get("coding"):
            for coding in obs["code"]["coding"]:
                if coding.get("code") == loinc_code:
                    return obs
    return None


class TestPulseOximetryComponents:
    """E2E tests for pulse oximetry with O2 components."""

    def test_pulse_ox_with_flow_rate_creates_component(self) -> None:
        """Test that O2 flow rate is added as a component to pulse oximetry observation."""
        with open("tests/integration/fixtures/ccda/pulse_ox_with_flow_rate.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            organizer_xml,
            section_template_id="2.16.840.1.113883.10.20.22.2.4.1",
            section_code="8716-3"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_observations_in_bundle(bundle)

        # Should have pulse ox observation (not O2 flow as separate observation)
        pulse_ox = _get_observation_by_code(observations, "59408-5")
        assert pulse_ox is not None, "Pulse oximetry observation not found"

        # Should have component for O2 flow rate
        assert "component" in pulse_ox, "Pulse ox should have components"
        components = pulse_ox["component"]
        assert len(components) == 1, "Should have 1 component (O2 flow rate)"

        # Verify O2 flow rate component
        flow_component = components[0]
        assert flow_component["code"]["coding"][0]["code"] == "3151-8"
        assert flow_component["code"]["coding"][0]["display"] == "Inhaled oxygen flow rate"
        assert flow_component["valueQuantity"]["value"] == 2
        assert flow_component["valueQuantity"]["unit"] == "L/min"

        # Should NOT have separate O2 flow observation
        o2_flow = _get_observation_by_code(observations, "3151-8")
        assert o2_flow is None, "O2 flow rate should not be a separate observation"

    def test_pulse_ox_with_concentration_creates_component(self) -> None:
        """Test that O2 concentration is added as a component to pulse oximetry observation."""
        with open("tests/integration/fixtures/ccda/pulse_ox_with_concentration.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            organizer_xml,
            section_template_id="2.16.840.1.113883.10.20.22.2.4.1",
            section_code="8716-3"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_observations_in_bundle(bundle)

        # Should have pulse ox observation (using alt code 2708-6)
        pulse_ox = _get_observation_by_code(observations, "2708-6")
        assert pulse_ox is not None, "Pulse oximetry observation not found"

        # Should have component for O2 concentration
        assert "component" in pulse_ox, "Pulse ox should have components"
        components = pulse_ox["component"]
        assert len(components) == 1, "Should have 1 component (O2 concentration)"

        # Verify O2 concentration component
        conc_component = components[0]
        assert conc_component["code"]["coding"][0]["code"] == "3150-0"
        assert conc_component["code"]["coding"][0]["display"] == "Inhaled oxygen concentration"
        assert conc_component["valueQuantity"]["value"] == 40
        assert conc_component["valueQuantity"]["unit"] == "%"

        # Should NOT have separate O2 concentration observation
        o2_conc = _get_observation_by_code(observations, "3150-0")
        assert o2_conc is None, "O2 concentration should not be a separate observation"

    def test_pulse_ox_with_both_components(self) -> None:
        """Test that both O2 flow rate and concentration are added as components."""
        with open("tests/integration/fixtures/ccda/pulse_ox_with_both_components.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            organizer_xml,
            section_template_id="2.16.840.1.113883.10.20.22.2.4.1",
            section_code="8716-3"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_observations_in_bundle(bundle)

        # Should have pulse ox observation
        pulse_ox = _get_observation_by_code(observations, "59408-5")
        assert pulse_ox is not None, "Pulse oximetry observation not found"

        # Should have both components
        assert "component" in pulse_ox, "Pulse ox should have components"
        components = pulse_ox["component"]
        assert len(components) == 2, "Should have 2 components (O2 flow rate + concentration)"

        # Verify both components are present
        component_codes = {comp["code"]["coding"][0]["code"] for comp in components}
        assert "3151-8" in component_codes, "O2 flow rate component missing"
        assert "3150-0" in component_codes, "O2 concentration component missing"

        # Verify O2 flow rate component
        flow_comp = next(c for c in components if c["code"]["coding"][0]["code"] == "3151-8")
        assert flow_comp["valueQuantity"]["value"] == 3
        assert flow_comp["valueQuantity"]["unit"] == "L/min"

        # Verify O2 concentration component
        conc_comp = next(c for c in components if c["code"]["coding"][0]["code"] == "3150-0")
        assert conc_comp["valueQuantity"]["value"] == 50
        assert conc_comp["valueQuantity"]["unit"] == "%"

        # Should NOT have separate O2 observations
        o2_flow = _get_observation_by_code(observations, "3151-8")
        o2_conc = _get_observation_by_code(observations, "3150-0")
        assert o2_flow is None, "O2 flow rate should not be a separate observation"
        assert o2_conc is None, "O2 concentration should not be a separate observation"

    def test_pulse_ox_main_value_preserved(self) -> None:
        """Test that the main pulse oximetry value is preserved when adding components."""
        with open("tests/integration/fixtures/ccda/pulse_ox_with_flow_rate.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            organizer_xml,
            section_template_id="2.16.840.1.113883.10.20.22.2.4.1",
            section_code="8716-3"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_observations_in_bundle(bundle)
        pulse_ox = _get_observation_by_code(observations, "59408-5")
        assert pulse_ox is not None

        # Main value should still be present
        assert "valueQuantity" in pulse_ox, "Main pulse ox value should be preserved"
        assert pulse_ox["valueQuantity"]["value"] == 98
        assert pulse_ox["valueQuantity"]["unit"] == "%"

    def test_pulse_ox_metadata_preserved(self) -> None:
        """Test that pulse oximetry observation metadata is preserved."""
        with open("tests/integration/fixtures/ccda/pulse_ox_with_flow_rate.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(
            organizer_xml,
            section_template_id="2.16.840.1.113883.10.20.22.2.4.1",
            section_code="8716-3"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_observations_in_bundle(bundle)
        pulse_ox = _get_observation_by_code(observations, "59408-5")
        assert pulse_ox is not None

        # Check metadata
        assert pulse_ox["status"] == "final"
        assert "effectiveDateTime" in pulse_ox
        assert "2020-03-15" in pulse_ox["effectiveDateTime"]
        assert pulse_ox["category"][0]["coding"][0]["code"] == "vital-signs"
