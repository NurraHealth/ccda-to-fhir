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


def _find_observation_by_code(bundle: JSONObject, loinc_code: str) -> JSONObject | None:
    """Find an Observation resource by its LOINC code."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") == loinc_code:
                    return resource
    return None


def _find_all_vital_sign_observations(bundle: JSONObject) -> list[JSONObject]:
    """Find all vital sign Observation resources (excluding panel)."""
    observations = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            # Exclude the panel observation
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") != "85353-1":  # Not the panel code
                    # Check if it has vital-signs category
                    category = resource.get("category", [])
                    for cat in category:
                        for cat_coding in cat.get("coding", []):
                            if cat_coding.get("code") == "vital-signs":
                                observations.append(resource)
                                break
                        break
                    break
    return observations


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
        """Test that individual observations are created in the bundle."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        # Find all individual vital sign observations in the bundle
        individual_obs = _find_all_vital_sign_observations(bundle)
        # HR (1) + BP combined (1) = 2 observations (BP combines systolic + diastolic)
        assert len(individual_obs) == 2

    def test_converts_heart_rate(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that heart rate observation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        # Find heart rate observation in bundle
        hr = _find_observation_by_code(bundle, "8867-4")
        assert hr is not None
        assert hr["valueQuantity"]["value"] == 80
        assert hr["valueQuantity"]["unit"] == "/min"

    def test_converts_blood_pressure(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that blood pressure observations are combined with components."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        # Find combined BP observation in bundle
        bp = _find_observation_by_code(bundle, "85354-9")  # BP panel code
        assert bp is not None
        assert "component" in bp
        assert len(bp["component"]) == 2

        # Verify systolic component
        systolic = next((c for c in bp["component"] if c["code"]["coding"][0]["code"] == "8480-6"), None)
        assert systolic is not None
        assert systolic["valueQuantity"]["value"] == 120

        # Verify diastolic component
        diastolic = next((c for c in bp["component"] if c["code"]["coding"][0]["code"] == "8462-4"), None)
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
        """Test that individual observation identifiers are preserved."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        # Find all individual vital sign observations
        individual_obs = _find_all_vital_sign_observations(bundle)
        assert len(individual_obs) > 0
        for obs in individual_obs:
            assert "identifier" in obs

    def test_has_member_references(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that hasMember references point to individual observations."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None

        # Find all individual vital sign observations
        individual_obs = _find_all_vital_sign_observations(bundle)
        assert len(panel["hasMember"]) == len(individual_obs)

        # Verify hasMember references point to Observation resources (not contained)
        for member in panel["hasMember"]:
            assert member["reference"].startswith("Observation/")
            # Verify the referenced observation exists in the bundle
            obs_id = member["reference"].split("/")[1]
            assert any(obs.get("id") == obs_id for obs in individual_obs)

    def test_component_narrative_propagates_from_text_reference(self) -> None:
        """Test that component Observation.text narrative is generated from text/reference."""
        # Test vital signs organizer with component observation that has text/reference
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="test-doc-id"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999"/>
            <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="test-org"/>
                <name>Test Org</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.4.1"/>
                    <code code="8716-3" codeSystem="2.16.840.1.113883.6.1" displayName="Vital Signs"/>
                    <text>
                        <paragraph ID="vitals-hr-1">
                            <content styleCode="Bold">Heart Rate:</content>
                            72 beats/min, regular rhythm, measured at rest.
                        </paragraph>
                    </text>
                    <entry>
                        <organizer classCode="CLUSTER" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
                            <id root="vitals-organizer-123"/>
                            <code code="46680005" codeSystem="2.16.840.1.113883.6.96" displayName="Vital signs"/>
                            <statusCode code="completed"/>
                            <effectiveTime value="20231201"/>
                            <component>
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                                    <id root="hr-obs-456"/>
                                    <code code="8867-4" displayName="Heart rate"
                                          codeSystem="2.16.840.1.113883.6.1"/>
                                    <text>
                                        <reference value="#vitals-hr-1"/>
                                    </text>
                                    <statusCode code="completed"/>
                                    <effectiveTime value="20231201"/>
                                    <value xsi:type="PQ" value="72" unit="/min"/>
                                </observation>
                            </component>
                        </organizer>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)

        # Find the heart rate observation (component observation, not the panel)
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        hr_obs = next(
            (obs for obs in observations if obs.get("code", {}).get("coding", [{}])[0].get("code") == "8867-4"),
            None
        )
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify Observation has text.div with resolved narrative
        assert "text" in hr_obs, "Observation should have .text field"
        assert "status" in hr_obs["text"]
        assert hr_obs["text"]["status"] == "generated"
        assert "div" in hr_obs["text"], "Observation should have .text.div"

        div_content = hr_obs["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify referenced content was resolved
        assert "Heart Rate" in div_content or "Heart rate" in div_content
        assert "72" in div_content
        assert "regular rhythm" in div_content

        # Verify structured markup preserved
        assert "<p" in div_content  # Paragraph converted to <p>
        assert 'id="vitals-hr-1"' in div_content  # ID preserved
        assert 'class="Bold"' in div_content or "Bold" in div_content  # Style preserved
