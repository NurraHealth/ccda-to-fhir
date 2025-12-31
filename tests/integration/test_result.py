"""E2E tests for DiagnosticReport and Observation resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

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

    def test_converts_to_diagnostic_report(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that result organizer creates a DiagnosticReport."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["resourceType"] == "DiagnosticReport"

    def test_converts_panel_code(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that organizer code is converted to DiagnosticReport.code."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "code" in report
        loinc = next(
            (c for c in report["code"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "24357-6"

    def test_converts_status(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["status"] == "final"

    def test_converts_category(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that category is set to LAB."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert report["category"][0]["coding"][0]["code"] == "LAB"
        assert report["category"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/v2-0074"

    def test_converts_effective_date(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        assert "effectiveDateTime" in report
        assert report["effectiveDateTime"] == "2015-06-22"

    def test_converts_observations(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
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

    def test_converts_observation_code(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that observation code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        loinc = next(
            (c for c in obs["code"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
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

    def test_converts_reference_range(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
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

    def test_converts_observation_status(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that observation status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert obs["status"] == "final"

    def test_converts_observation_category(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
        """Test that observation category is set to laboratory."""
        ccda_doc = wrap_in_ccda_document(ccda_result, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        report = _find_resource_in_bundle(bundle, "DiagnosticReport")
        assert report is not None
        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = observations[0]
        assert obs["category"][0]["coding"][0]["code"] == "laboratory"

    def test_converts_identifier(
        self, ccda_result: str, fhir_result: JSONObject
    ) -> None:
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
            assert ref["reference"].startswith("Observation/")
