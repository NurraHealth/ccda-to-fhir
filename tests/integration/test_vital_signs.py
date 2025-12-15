"""E2E tests for Vital Signs Observation resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

VITAL_SIGNS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.4.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


def _find_vital_signs_panel(bundle: JSONObject) -> JSONObject | None:
    """Find the vital signs panel Observation in the bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") == "85353-1":
                    return resource
    return None


class TestVitalSignsConversion:
    """E2E tests for C-CDA Vital Signs Organizer to FHIR Observation conversion."""

    def test_converts_to_observation_panel(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that vital signs organizer creates a panel Observation."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["resourceType"] == "Observation"
        assert "hasMember" in panel

    def test_converts_panel_code(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that panel uses vital signs panel code."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["code"]["coding"][0]["code"] == "85353-1"
        assert panel["code"]["coding"][0]["system"] == "http://loinc.org"

    def test_converts_category(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that category is set to vital-signs."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["category"][0]["coding"][0]["code"] == "vital-signs"
        assert panel["category"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

    def test_converts_effective_date(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert "effectiveDateTime" in panel
        assert "2014-05-20" in panel["effectiveDateTime"]

    def test_converts_status(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["status"] == "final"

    def test_converts_component_observations(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that component observations are created."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert "contained" in panel
        assert len(panel["contained"]) >= 3

    def test_converts_heart_rate(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that heart rate observation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        hr = next(
            (o for o in panel["contained"] if o["code"]["coding"][0]["code"] == "8867-4"),
            None
        )
        assert hr is not None
        assert hr["valueQuantity"]["value"] == 80
        assert hr["valueQuantity"]["unit"] == "/min"

    def test_converts_blood_pressure(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that blood pressure observations are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        systolic = next(
            (o for o in panel["contained"] if o["code"]["coding"][0]["code"] == "8480-6"),
            None
        )
        assert systolic is not None
        assert systolic["valueQuantity"]["value"] == 120

        diastolic = next(
            (o for o in panel["contained"] if o["code"]["coding"][0]["code"] == "8462-4"),
            None
        )
        assert diastolic is not None
        assert diastolic["valueQuantity"]["value"] == 80

    def test_converts_identifiers(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert "identifier" in panel
        assert panel["identifier"][0]["value"] == "21688133041015158234"

    def test_converts_component_identifiers(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that component observation identifiers are preserved."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        for obs in panel["contained"]:
            assert "identifier" in obs

    def test_has_member_references(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that hasMember references point to contained observations."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert len(panel["hasMember"]) == len(panel["contained"])
        for member in panel["hasMember"]:
            assert member["reference"].startswith("#")
