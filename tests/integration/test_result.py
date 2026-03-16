"""E2E tests for DiagnosticReport and Observation resource conversion."""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"

RESULTS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.3.1"


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


class TestResultConversion:
    """E2E tests for C-CDA Result Organizer to FHIR DiagnosticReport/Observation conversion."""

    def test_converts_to_diagnostic_report(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that result organizer creates a DiagnosticReport."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["resourceType"] == "DiagnosticReport"

    def test_converts_panel_code(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that organizer code is converted to DiagnosticReport.code."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "code" in report
        loinc = next(
            (c for c in report["code"]["coding"] if c.get("system") == "http://loinc.org"), None
        )
        assert loinc is not None
        assert loinc["code"] == "24357-6"

    def test_converts_status(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["status"] == "final"

    def test_converts_category(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that category is set to LAB."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["category"][0]["coding"][0]["code"] == "LAB"
        assert (
            report["category"][0]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/v2-0074"
        )

    def test_converts_effective_date(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "effectiveDateTime" in report
        assert report["effectiveDateTime"] == "2015-06-22"

    def test_converts_observations(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that component observations are converted."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "result" in report
        assert len(report["result"]) >= 1
        # Observations should be standalone in bundle (not contained)
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) >= 1

    def test_converts_observation_code(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that observation code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        loinc = next(
            (c for c in obs["code"]["coding"] if c.get("system") == "http://loinc.org"), None
        )
        assert loinc is not None
        assert loinc["code"] == "5811-5"

    def test_converts_observation_value_quantity(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that PQ value is converted to valueQuantity."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" in obs
        assert obs["valueQuantity"]["value"] == 1.015

    def test_converts_reference_range(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that reference range is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "referenceRange" in obs
        ref_range = obs["referenceRange"][0]
        assert ref_range["low"]["value"] == 1.005
        assert ref_range["high"]["value"] == 1.030

    def test_converts_observation_status(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that observation status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert obs["status"] == "final"

    def test_converts_observation_category(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that observation category is set to laboratory."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert obs["category"][0]["coding"][0]["code"] == "laboratory"

    def test_converts_identifier(self, ccda_result: str, fhir_result: JSONObject) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "identifier" in report
        assert report["identifier"][0]["value"] == "R123"

    def test_result_references_point_to_standalone(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that result references point to standalone observations."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(report["result"]) == len(observations)
        for ref in report["result"]:
            assert ref["reference"].startswith("urn:uuid:")


class TestPQTranslationFallback:
    """Tests for PQ values with nullFlavor where the actual value is in a translation child.

    This is a pattern used by Athena when the unit is non-standard UCUM (e.g., x10e3/uL).
    The PQ element has nullFlavor="OTH" with no value/unit, and a <translation> child
    carries the actual numeric value and unit via originalText.
    """

    def test_pq_translation_produces_value_quantity(self, ccda_result_pq_translation: str) -> None:
        """PQ with nullFlavor and translation should produce a valueQuantity, not an empty one."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_translation, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        # Find the WBC observation (LOINC 6690-2) which uses PQ translation
        wbc = next(
            (
                o
                for o in observations
                if any(c.get("code") == "6690-2" for c in o.get("code", {}).get("coding", []))
            ),
            None,
        )
        assert wbc is not None, "WBC observation not found"
        assert "valueQuantity" in wbc, "valueQuantity missing — PQ translation fallback not working"
        assert wbc["valueQuantity"]["value"] == 11.5
        assert wbc["valueQuantity"]["unit"] == "x10e3/uL"

    def test_pq_translation_no_empty_value_quantity(self, ccda_result_pq_translation: str) -> None:
        """No observation should have an empty valueQuantity."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_translation, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        for obs in observations:
            if "valueQuantity" in obs:
                assert obs["valueQuantity"], f"Empty valueQuantity in {obs.get('code')}"
                assert "value" in obs["valueQuantity"], (
                    f"valueQuantity missing value in {obs.get('code')}"
                )

    def test_normal_pq_still_works(self, ccda_result_pq_translation: str) -> None:
        """Normal PQ with direct value/unit should still convert correctly."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_translation, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        # Find the HGB observation (LOINC 718-7) which uses normal PQ
        hgb = next(
            (
                o
                for o in observations
                if any(c.get("code") == "718-7" for c in o.get("code", {}).get("coding", []))
            ),
            None,
        )
        assert hgb is not None, "HGB observation not found"
        assert "valueQuantity" in hgb
        assert hgb["valueQuantity"]["value"] == 12.8
        assert hgb["valueQuantity"]["unit"] == "g/dL"

    def test_pq_nullflavor_no_translation_gets_data_absent_reason(
        self, ccda_result_pq_nullflavor_no_translation: str
    ) -> None:
        """PQ with nullFlavor but no translation should produce dataAbsentReason, not valueQuantity."""
        ccda_doc = wrap_in_ccda_document(
            ccda_result_pq_nullflavor_no_translation, RESULTS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" not in obs, (
            "Should not have valueQuantity when PQ has no value and no translation"
        )
        assert "dataAbsentReason" in obs, (
            "Should have dataAbsentReason for nullFlavor PQ without translation"
        )

    def test_translation_value_no_original_text(
        self, ccda_result_pq_translation_no_original_text: str
    ) -> None:
        """Translation with value but no originalText should produce valueQuantity with value, no unit."""
        ccda_doc = wrap_in_ccda_document(
            ccda_result_pq_translation_no_original_text, RESULTS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" in obs, "Should have valueQuantity from translation value"
        assert obs["valueQuantity"]["value"] == 11.5
        assert "unit" not in obs["valueQuantity"], (
            "Should not have unit when translation has no originalText or unit"
        )

    def test_multiple_translations_first_with_value_wins(
        self, ccda_result_pq_multiple_translations: str
    ) -> None:
        """When multiple translations exist, the first with a value should be used."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_multiple_translations, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" in obs
        assert obs["valueQuantity"]["value"] == 9.2, (
            "Should use first translation's value (9.2), not second (99.9)"
        )
        assert obs["valueQuantity"]["unit"] == "x10e3/uL", (
            "Should use first translation's originalText as unit"
        )

    def test_direct_value_takes_precedence_over_translation(
        self, ccda_result_pq_direct_value_with_translation: str
    ) -> None:
        """PQ with direct value AND translation should use the direct value."""
        ccda_doc = wrap_in_ccda_document(
            ccda_result_pq_direct_value_with_translation, RESULTS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" in obs
        assert obs["valueQuantity"]["value"] == 13.5, "Should use direct PQ value, not translation"
        assert obs["valueQuantity"]["unit"] == "g/dL", "Should use direct PQ unit, not translation"

    def test_empty_translation_gets_data_absent_reason(
        self, ccda_result_pq_empty_translation_list: str
    ) -> None:
        """PQ with nullFlavor and translation with no value should produce dataAbsentReason."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_empty_translation_list, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" not in obs, (
            "Should not have valueQuantity when translation has no value"
        )
        assert "dataAbsentReason" in obs, (
            "Should have dataAbsentReason when translation is valueless"
        )

    def test_translation_string_integer_value(
        self, ccda_result_pq_translation_string_int: str
    ) -> None:
        """Translation with integer-like value (e.g., '179') should produce a numeric valueQuantity."""
        ccda_doc = wrap_in_ccda_document(ccda_result_pq_translation_string_int, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert "valueQuantity" in obs
        # Value should be numeric (int or float), not a string
        assert isinstance(obs["valueQuantity"]["value"], (int, float))
        assert obs["valueQuantity"]["value"] in (179, 179.0)
        assert obs["valueQuantity"]["unit"] == "x10e3/uL"


class TestAthenaCCDFullDocument:
    """Full-document integration test for Athena CCD with PQ translation pattern.

    Validates that a real anonymized Athena CCD converts successfully and all
    observations with PQ translations produce valid valueQuantity (not empty).
    """

    def test_all_observations_have_valid_value_or_data_absent_reason(self) -> None:
        """Every Observation must have either a non-empty valueQuantity or dataAbsentReason."""
        xml = (DOCUMENTS_DIR / "athena_ccd_pq_translation.xml").read_text()
        bundle = convert_document(xml)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        assert len(observations) > 0, "Bundle should contain Observations"

        for obs in observations:
            has_value = any(k.startswith("value") and obs[k] for k in obs)
            has_data_absent = "dataAbsentReason" in obs
            has_component = "component" in obs
            has_member = "hasMember" in obs
            assert has_value or has_data_absent or has_component or has_member, (
                f"Observation {obs.get('code')} has neither a value, dataAbsentReason, component, nor hasMember"
            )

    def test_no_empty_value_quantity(self) -> None:
        """No observation should have an empty valueQuantity dict."""
        xml = (DOCUMENTS_DIR / "athena_ccd_pq_translation.xml").read_text()
        bundle = convert_document(xml)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        for obs in observations:
            if "valueQuantity" in obs:
                assert obs["valueQuantity"], f"Empty valueQuantity in {obs.get('code')}"
                assert "value" in obs["valueQuantity"], (
                    f"valueQuantity missing value in {obs.get('code')}"
                )
