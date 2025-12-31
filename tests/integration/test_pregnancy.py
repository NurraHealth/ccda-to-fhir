"""E2E tests for Pregnancy Observation resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

SOCIAL_HISTORY_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.17"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestPregnancyObservation:
    """E2E tests for C-CDA Pregnancy Observation to FHIR Observation conversion."""

    def test_converts_pregnancy_status_code(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that ASSERTION code is transformed to LOINC 82810-3."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "code" in observation

        # Verify code transformation from ASSERTION to 82810-3
        code_coding = observation["code"]["coding"][0]
        assert code_coding["system"] == "http://loinc.org"
        assert code_coding["code"] == "82810-3"
        assert code_coding["display"] == "Pregnancy status"

    def test_converts_pregnancy_value(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that pregnancy status value is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "valueCodeableConcept" in observation

        # Verify SNOMED CT pregnancy status value
        value_coding = observation["valueCodeableConcept"]["coding"][0]
        assert value_coding["system"] == "http://snomed.info/sct"
        assert value_coding["code"] == "77386006"
        assert "pregnant" in value_coding["display"].lower()

    def test_category_is_social_history(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that pregnancy observation has social-history category."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "category" in observation
        assert len(observation["category"]) > 0

        category_coding = observation["category"][0]["coding"][0]
        assert category_coding["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"
        assert category_coding["code"] == "social-history"
        assert category_coding["display"] == "Social History"

    def test_converts_estimated_delivery_date(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that estimated delivery date is mapped to component."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "component" in observation
        assert len(observation["component"]) == 1

        component = observation["component"][0]

        # Verify component code
        assert "code" in component
        comp_coding = component["code"]["coding"][0]
        assert comp_coding["system"] == "http://loinc.org"
        assert comp_coding["code"] == "11778-8"
        assert "Delivery date" in comp_coding["display"] or "Estimated date" in comp_coding["display"]

        # Verify component value
        assert "valueDateTime" in component
        assert component["valueDateTime"] == "2023-02-14"

    def test_converts_effective_datetime(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that effective time is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "effectiveDateTime" in observation
        # The fixture has effectiveTime/low value="20220824103952+0000"
        assert "2022-08-24" in observation["effectiveDateTime"]

    def test_converts_status(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "status" in observation
        # C-CDA statusCode="completed" → FHIR status="final"
        assert observation["status"] == "final"

    def test_converts_identifier(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "identifier" in observation
        assert len(observation["identifier"]) > 0

        identifier = observation["identifier"][0]
        assert identifier["system"] == "urn:oid:2.16.840.1.113883.19"
        assert identifier["value"] == "123456789"

    def test_resource_type_is_observation(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that the resource type is Observation."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert observation["resourceType"] == "Observation"

    def test_has_subject_reference(
        self, ccda_pregnancy: str
    ) -> None:
        """Test that observation has a subject reference to Patient."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "subject" in observation
        assert "reference" in observation["subject"]
        assert observation["subject"]["reference"].startswith("Patient/")


class TestPregnancyWithoutEDD:
    """Tests for pregnancy observations without estimated delivery date."""

    def test_pregnancy_without_edd_component(
        self, ccda_pregnancy_no_edd: str
    ) -> None:
        """Test pregnancy observation without EDD still creates valid observation."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_no_edd, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None

        # Should have all base fields
        assert observation["status"] == "final"
        assert observation["code"]["coding"][0]["code"] == "82810-3"
        assert observation["valueCodeableConcept"]["coding"][0]["code"] == "60001007"

        # Should NOT have component
        assert "component" not in observation or len(observation.get("component", [])) == 0


class TestPregnancyCodeVariants:
    """Tests for pregnancy observations with different code variants."""

    def test_pregnancy_with_loinc_code(
        self, ccda_pregnancy_loinc: str
    ) -> None:
        """Test pregnancy observation with LOINC 82810-3 code (C-CDA 4.0+)."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_loinc, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None

        # Code should remain 82810-3 (not transformed)
        code_coding = observation["code"]["coding"][0]
        assert code_coding["system"] == "http://loinc.org"
        assert code_coding["code"] == "82810-3"


class TestPregnancyGestationalAge:
    """Tests for pregnancy observations with gestational age component."""

    def test_pregnancy_with_gestational_age_component(
        self, ccda_pregnancy_with_gestational_age: str
    ) -> None:
        """Test pregnancy observation with gestational age component."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_with_gestational_age, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "component" in observation
        assert len(observation["component"]) == 2  # EDD + Gestational Age

        # Find gestational age component
        ga_component = None
        edd_component = None
        for comp in observation["component"]:
            code = comp["code"]["coding"][0]["code"]
            if code == "49051-6":
                ga_component = comp
            elif code == "11778-8":
                edd_component = comp

        assert ga_component is not None, "Gestational age component not found"
        assert edd_component is not None, "EDD component not found"

        # Verify gestational age component structure
        ga_code = ga_component["code"]["coding"][0]
        assert ga_code["system"] == "http://loinc.org"
        assert ga_code["code"] == "49051-6"
        assert "Gestational age" in ga_code["display"]

        # Verify gestational age value
        assert "valueQuantity" in ga_component
        ga_value = ga_component["valueQuantity"]
        assert ga_value["value"] == 24
        assert ga_value["unit"] == "wk"
        assert ga_value["system"] == "http://unitsofmeasure.org"
        assert ga_value["code"] == "wk"

    def test_gestational_age_different_loinc_codes(
        self, ccda_pregnancy_with_gestational_age: str
    ) -> None:
        """Test that different gestational age LOINC codes are supported."""
        # Modify the fixture to use different LOINC code
        modified_ccda = ccda_pregnancy_with_gestational_age.replace(
            'code code="49051-6"',
            'code code="11885-1"'
        ).replace(
            'displayName="Gestational age in weeks"',
            'displayName="Gestational age Estimated from last menstrual period"'
        )

        ccda_doc = wrap_in_ccda_document(modified_ccda, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "component" in observation

        # Find gestational age component
        ga_component = None
        for comp in observation["component"]:
            code = comp["code"]["coding"][0]["code"]
            if code == "11885-1":
                ga_component = comp
                break

        assert ga_component is not None
        assert ga_component["code"]["coding"][0]["code"] == "11885-1"
        assert "valueQuantity" in ga_component


class TestPregnancyLastMenstrualPeriod:
    """Tests for pregnancy observations with last menstrual period component."""

    def test_pregnancy_with_lmp_component(
        self, ccda_pregnancy_with_lmp: str
    ) -> None:
        """Test pregnancy observation with last menstrual period component."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_with_lmp, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "component" in observation
        assert len(observation["component"]) == 1  # Only LMP (no EDD in this fixture)

        # Verify LMP component
        lmp_component = observation["component"][0]
        lmp_code = lmp_component["code"]["coding"][0]
        assert lmp_code["system"] == "http://loinc.org"
        assert lmp_code["code"] == "8665-2"
        assert "Last menstrual period" in lmp_code["display"]

        # Verify LMP value
        assert "valueDateTime" in lmp_component
        assert lmp_component["valueDateTime"] == "2022-06-01"

    def test_lmp_date_conversion(
        self, ccda_pregnancy_with_lmp: str
    ) -> None:
        """Test that LMP date is correctly converted from C-CDA format."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_with_lmp, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None

        lmp_component = observation["component"][0]
        assert lmp_component["valueDateTime"] == "2022-06-01"


class TestPregnancyComprehensive:
    """Tests for pregnancy observations with all components."""

    def test_pregnancy_with_all_components(
        self, ccda_pregnancy_comprehensive: str
    ) -> None:
        """Test pregnancy observation with EDD, LMP, and gestational age."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_comprehensive, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None
        assert "component" in observation
        assert len(observation["component"]) == 3  # EDD + LMP + Gestational Age

        # Collect all component codes
        component_codes = {
            comp["code"]["coding"][0]["code"]
            for comp in observation["component"]
        }

        # Verify all three components are present
        assert "11778-8" in component_codes, "EDD component missing"
        assert "8665-2" in component_codes, "LMP component missing"
        assert "11885-1" in component_codes, "Gestational age component missing"

    def test_comprehensive_component_values(
        self, ccda_pregnancy_comprehensive: str
    ) -> None:
        """Test that all component values are correctly extracted."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_comprehensive, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None

        # Build a dictionary of components by code
        components = {
            comp["code"]["coding"][0]["code"]: comp
            for comp in observation["component"]
        }

        # Verify EDD
        edd = components["11778-8"]
        assert edd["valueDateTime"] == "2023-02-14"

        # Verify LMP
        lmp = components["8665-2"]
        assert lmp["valueDateTime"] == "2022-05-10"

        # Verify Gestational Age
        ga = components["11885-1"]
        assert ga["valueQuantity"]["value"] == 24
        assert ga["valueQuantity"]["unit"] == "wk"

    def test_pregnancy_base_observation_with_components(
        self, ccda_pregnancy_comprehensive: str
    ) -> None:
        """Test that base pregnancy observation is correct with components."""
        ccda_doc = wrap_in_ccda_document(ccda_pregnancy_comprehensive, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_resource_in_bundle(bundle, "Observation")
        assert observation is not None

        # Verify base observation fields
        assert observation["status"] == "final"
        assert observation["code"]["coding"][0]["code"] == "82810-3"
        assert observation["valueCodeableConcept"]["coding"][0]["code"] == "77386006"

        # Verify category
        assert len(observation["category"]) > 0
        assert observation["category"][0]["coding"][0]["code"] == "social-history"
