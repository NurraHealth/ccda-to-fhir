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

class TestObservationRange:
    def test_converts_ivl_pq_value_range(
        self, ccda_observation_ivl_pq: str
    ) -> None:
        """Test that IVL_PQ observation value is converted to valueRange.

        Result Observations must be within Result Organizers per C-CDA spec.
        This test verifies IVL_PQ conversion works within compliant structure.
        """
        ccda_doc = wrap_in_ccda_document(ccda_observation_ivl_pq, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be standalone in bundle (not contained)
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0
        observation = observations[0]
        assert observation["resourceType"] == "Observation"

        # Verify IVL_PQ → valueRange conversion
        assert "valueRange" in observation
        assert "valueQuantity" not in observation

        val_range = observation["valueRange"]
        assert val_range["low"]["value"] == 4.0
        assert val_range["low"]["unit"] == "10*9/L"
        assert val_range["high"]["value"] == 11.0
        assert val_range["high"]["unit"] == "10*9/L"

    def test_converts_ivl_pq_high_only_to_quantity_with_comparator(self) -> None:
        """Test that IVL_PQ with only high value converts to valueQuantity with <= comparator."""
        with open("tests/integration/fixtures/ccda/observation_ivl_pq_high_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be standalone in bundle (not contained)
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0
        observation = observations[0]
        assert observation["resourceType"] == "Observation"

        # Verify IVL_PQ (high-only) → valueQuantity with comparator
        assert "valueQuantity" in observation
        assert "valueRange" not in observation

        val_quantity = observation["valueQuantity"]
        assert val_quantity["value"] == 100
        assert val_quantity["unit"] == "mg/dL"
        assert val_quantity["comparator"] == "<="

    def test_converts_ivl_pq_low_only_to_quantity_with_comparator(self) -> None:
        """Test that IVL_PQ with only low value converts to valueQuantity with >= comparator."""
        with open("tests/integration/fixtures/ccda/observation_ivl_pq_low_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be standalone in bundle (not contained)
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0
        observation = observations[0]
        assert observation["resourceType"] == "Observation"

        # Verify IVL_PQ (low-only) → valueQuantity with comparator
        assert "valueQuantity" in observation
        assert "valueRange" not in observation

        val_quantity = observation["valueQuantity"]
        assert val_quantity["value"] == 200
        assert val_quantity["unit"] == "mg/dL"
        assert val_quantity["comparator"] == ">="

    def test_high_only_comparator_has_ucum_system(self) -> None:
        """Test that high-only IVL_PQ comparator quantity includes UCUM system."""
        with open("tests/integration/fixtures/ccda/observation_ivl_pq_high_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        observation = observations[0]

        val_quantity = observation["valueQuantity"]
        assert val_quantity["system"] == "http://unitsofmeasure.org"
        assert val_quantity["code"] == "mg/dL"

    def test_low_only_comparator_has_ucum_system(self) -> None:
        """Test that low-only IVL_PQ comparator quantity includes UCUM system."""
        with open("tests/integration/fixtures/ccda/observation_ivl_pq_low_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        observation = observations[0]

        val_quantity = observation["valueQuantity"]
        assert val_quantity["system"] == "http://unitsofmeasure.org"
        assert val_quantity["code"] == "mg/dL"

    def test_comparator_preserves_observation_metadata(self) -> None:
        """Test that using comparator preserves other observation metadata."""
        with open("tests/integration/fixtures/ccda/observation_ivl_pq_high_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        observation = observations[0]

        # Verify metadata is preserved
        assert observation["status"] == "final"
        assert "code" in observation
        assert observation["code"]["coding"][0]["code"] == "2339-0"
        assert "effectiveDateTime" in observation
        assert "2012-08-06" in observation["effectiveDateTime"]

    def test_converts_ivl_ts_to_effective_period(self) -> None:
        """Test that IVL_TS effectiveTime with both low and high converts to effectivePeriod."""
        with open("tests/integration/fixtures/ccda/observation_effective_period.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        # Result Organizer maps to DiagnosticReport
        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None, "Result Organizer should map to DiagnosticReport"

        # Observation should be standalone in bundle
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0
        observation = observations[0]
        assert observation["resourceType"] == "Observation"

        # Verify IVL_TS → effectivePeriod conversion
        assert "effectivePeriod" in observation
        assert "effectiveDateTime" not in observation

        period = observation["effectivePeriod"]
        assert "start" in period
        assert "end" in period
        # Timestamps without timezone are reduced to date-only per FHIR R4 requirement
        assert period["start"] == "2023-11-01"
        assert period["end"] == "2023-11-02"

    def test_effective_period_with_date_only(self) -> None:
        """Test that IVL_TS effectiveTime with date-only values converts to effectivePeriod."""
        with open("tests/integration/fixtures/ccda/observation_effective_period_date_only.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        observation = observations[0]

        # Verify IVL_TS → effectivePeriod conversion
        assert "effectivePeriod" in observation
        assert "effectiveDateTime" not in observation

        period = observation["effectivePeriod"]
        assert period["start"] == "2023-11-01"
        assert period["end"] == "2023-11-02"

    def test_effective_period_preserves_observation_metadata(self) -> None:
        """Test that using effectivePeriod preserves other observation metadata."""
        with open("tests/integration/fixtures/ccda/observation_effective_period.xml") as f:
            organizer_xml = f.read()

        ccda_doc = wrap_in_ccda_document(organizer_xml, TemplateIds.RESULTS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        observation = observations[0]

        # Verify metadata is preserved
        assert observation["status"] == "final"
        assert "code" in observation
        assert observation["code"]["coding"][0]["code"] == "5811-5"
        assert "valueQuantity" in observation
        assert observation["valueQuantity"]["value"] == 1.015


class TestObservationIDSanitization:
    """Tests for Observation resource ID sanitization."""

    def test_sanitizes_id_with_underscores(self) -> None:
        """Test that observation IDs with underscores are sanitized.

        Real-world C-CDA documents may have IDs with underscores (e.g., '16_Height')
        which violates FHIR R4B spec. IDs can only contain: A-Z, a-z, 0-9, -, .
        After standardization, IDs use sanitized extension (underscores → hyphens).
        """
        ccda_doc = wrap_in_ccda_document(
            """<organizer classCode="CLUSTER" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
                <id root="1.2.3.4.5" extension="vital-signs-panel"/>
                <code code="46680005" codeSystem="2.16.840.1.113883.6.96" displayName="Vital signs"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101120000"/>
                <component>
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                        <id root="1.2.3.4.5" extension="16_Height"/>
                        <code code="8302-2" codeSystem="2.16.840.1.113883.6.1" displayName="Height"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20230101120000"/>
                        <value xsi:type="PQ" value="177" unit="cm"/>
                    </observation>
                </component>
            </organizer>""",
            TemplateIds.VITAL_SIGNS_SECTION
        )

        bundle = convert_document(ccda_doc)["bundle"]
        observations = _find_all_resources_in_bundle(bundle, "Observation")

        # Find the Height observation with sanitized ID (lowercase)
        height_obs = next((obs for obs in observations if "16-height" in obs.get("id", "")), None)

        assert height_obs is not None, "Should find observation with sanitized ID"
        # After standardization: underscore replaced with hyphen, converted to lowercase
        assert height_obs["id"] == "observation-16-height"
        # Verify it's the correct observation
        assert height_obs["code"]["coding"][0]["code"] == "8302-2"

    def test_sanitizes_id_with_spaces(self) -> None:
        """Test that observation IDs with spaces are sanitized."""
        ccda_doc = wrap_in_ccda_document(
            """<organizer classCode="CLUSTER" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
                <id root="1.2.3.4.5" extension="vital-signs-panel"/>
                <code code="46680005" codeSystem="2.16.840.1.113883.6.96" displayName="Vital signs"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101120000"/>
                <component>
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                        <id root="1.2.3.4.5" extension="8_Body temperature"/>
                        <code code="8310-5" codeSystem="2.16.840.1.113883.6.1" displayName="Body temperature"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20230101120000"/>
                        <value xsi:type="PQ" value="37" unit="Cel"/>
                    </observation>
                </component>
            </organizer>""",
            TemplateIds.VITAL_SIGNS_SECTION
        )

        bundle = convert_document(ccda_doc)["bundle"]
        observations = _find_all_resources_in_bundle(bundle, "Observation")

        # Find the temperature observation (lowercase)
        temp_obs = next((obs for obs in observations if "body" in obs.get("id", "")), None)

        assert temp_obs is not None, "Should find observation with sanitized ID"
        # After standardization: underscore and space replaced with hyphens, converted to lowercase
        assert temp_obs["id"] == "observation-8-body-temperature"
        # Verify it's the correct observation
        assert temp_obs["code"]["coding"][0]["code"] == "8310-5"
