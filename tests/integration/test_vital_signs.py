"""E2E tests for Vital Signs Observation resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

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
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["resourceType"] == "Observation"
        assert "hasMember" in panel

    def test_converts_panel_code(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that panel uses vital signs panel code."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["code"]["coding"][0]["code"] == "85353-1"
        assert panel["code"]["coding"][0]["system"] == "http://loinc.org"

    def test_converts_category(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that category is set to vital-signs."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["category"][0]["coding"][0]["code"] == "vital-signs"
        assert panel["category"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

    def test_converts_effective_date(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert "effectiveDateTime" in panel
        assert "2014-05-20" in panel["effectiveDateTime"]

    def test_converts_status(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert panel["status"] == "final"

    def test_converts_component_observations(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that individual observations are created in the bundle."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all individual vital sign observations in the bundle
        individual_obs = _find_all_vital_sign_observations(bundle)
        # HR (1) + BP combined (1) = 2 observations (BP combines systolic + diastolic)
        assert len(individual_obs) == 2

    def test_converts_heart_rate(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that heart rate observation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        panel = _find_vital_signs_panel(bundle)
        assert panel is not None
        assert "identifier" in panel
        assert panel["identifier"][0]["value"] == "21688133041015158234"

    def test_converts_component_identifiers(
        self, ccda_vital_signs: str, fhir_vital_signs: JSONObject
    ) -> None:
        """Test that individual observation identifiers are preserved."""
        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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

    def test_converts_method_code_oral_temperature(self) -> None:
        """Test that methodCode is converted to Observation.method for oral temperature."""
        # Load fixture with oral temperature method
        with open("tests/integration/fixtures/ccda/vital_signs_temp_oral_method.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find body temperature observation
        temp_obs = _find_observation_by_code(bundle, "8310-5")
        assert temp_obs is not None, "Body temperature observation should be found"

        # Verify method field exists
        assert "method" in temp_obs, "Observation should have method field"
        method = temp_obs["method"]

        # Verify method is a CodeableConcept with coding
        assert "coding" in method, "Method should have coding array"
        assert len(method["coding"]) > 0, "Method should have at least one coding"

        # Verify SNOMED CT system and code
        coding = method["coding"][0]
        assert coding["system"] == "http://snomed.info/sct", "Method system should be SNOMED CT"
        assert coding["code"] == "89003005", "Method code should be 89003005 (Oral temperature taking)"
        assert coding["display"] == "Oral temperature taking", "Method display should be preserved"

    def test_converts_method_code_axillary_temperature(self) -> None:
        """Test that methodCode is converted to Observation.method for axillary temperature."""
        # Load fixture with axillary temperature method
        with open("tests/integration/fixtures/ccda/vital_signs_temp_axillary_method.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find body temperature observation
        temp_obs = _find_observation_by_code(bundle, "8310-5")
        assert temp_obs is not None, "Body temperature observation should be found"

        # Verify method field exists
        assert "method" in temp_obs, "Observation should have method field"
        method = temp_obs["method"]

        # Verify method is a CodeableConcept with coding
        assert "coding" in method, "Method should have coding array"
        assert len(method["coding"]) > 0, "Method should have at least one coding"

        # Verify SNOMED CT system and code
        coding = method["coding"][0]
        assert coding["system"] == "http://snomed.info/sct", "Method system should be SNOMED CT"
        assert coding["code"] == "415945006", "Method code should be 415945006 (Axillary temperature taking)"
        assert coding["display"] == "Axillary temperature taking", "Method display should be preserved"

    def test_method_code_not_present_when_absent(self) -> None:
        """Test that method field is not present when methodCode is absent in C-CDA."""
        # Use existing fixture without methodCode
        with open("tests/integration/fixtures/ccda/vital_signs.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (no method code in this fixture)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify method field is not present
        assert "method" not in hr_obs, "Observation should not have method field when methodCode is absent"

    def test_converts_body_site_blood_pressure(self) -> None:
        """Test that targetSiteCode is converted to Observation.bodySite for blood pressure."""
        # Load fixture with blood pressure with body site (right arm)
        with open("tests/integration/fixtures/ccda/vital_signs_bp_with_body_site.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find combined blood pressure observation (should combine systolic/diastolic)
        bp_obs = _find_observation_by_code(bundle, "85354-9")
        assert bp_obs is not None, "Blood pressure observation should be found"

        # Verify bodySite field exists
        assert "bodySite" in bp_obs, "Observation should have bodySite field"
        body_site = bp_obs["bodySite"]

        # Verify bodySite is a CodeableConcept with coding
        assert "coding" in body_site, "bodySite should have coding array"
        assert len(body_site["coding"]) > 0, "bodySite should have at least one coding"

        # Verify SNOMED CT system and code
        coding = body_site["coding"][0]
        assert coding["system"] == "http://snomed.info/sct", "bodySite system should be SNOMED CT"
        assert coding["code"] == "368209003", "bodySite code should be 368209003 (Right arm)"
        assert coding["display"] == "Right arm", "bodySite display should be preserved"

    def test_converts_body_site_heart_rate(self) -> None:
        """Test that targetSiteCode is converted to Observation.bodySite for heart rate."""
        # Load fixture with heart rate with body site (left arm)
        with open("tests/integration/fixtures/ccda/vital_signs_hr_with_body_site.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify bodySite field exists
        assert "bodySite" in hr_obs, "Observation should have bodySite field"
        body_site = hr_obs["bodySite"]

        # Verify bodySite is a CodeableConcept with coding
        assert "coding" in body_site, "bodySite should have coding array"
        assert len(body_site["coding"]) > 0, "bodySite should have at least one coding"

        # Verify SNOMED CT system and code
        coding = body_site["coding"][0]
        assert coding["system"] == "http://snomed.info/sct", "bodySite system should be SNOMED CT"
        assert coding["code"] == "368208008", "bodySite code should be 368208008 (Left arm)"
        assert coding["display"] == "Left arm", "bodySite display should be preserved"

    def test_body_site_not_present_when_absent(self) -> None:
        """Test that bodySite field is not present when targetSiteCode is absent in C-CDA."""
        # Use existing fixture without targetSiteCode
        with open("tests/integration/fixtures/ccda/vital_signs.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (no body site in this fixture)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify bodySite field is not present
        assert "bodySite" not in hr_obs, "Observation should not have bodySite field when targetSiteCode is absent"

    def test_converts_body_site_with_laterality_qualifier_blood_pressure(self) -> None:
        """Test that targetSiteCode with laterality qualifier is converted to bodySite with laterality coding."""
        # Load fixture with blood pressure with laterality qualifier
        with open("tests/integration/fixtures/ccda/vital_signs_bp_with_laterality.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find combined blood pressure observation
        bp_obs = _find_observation_by_code(bundle, "85354-9")
        assert bp_obs is not None, "Blood pressure observation should be found"

        # Verify bodySite field is present
        assert "bodySite" in bp_obs, "Blood pressure observation should have bodySite"
        body_site = bp_obs["bodySite"]

        # Verify coding array exists with at least 2 codings (site + laterality)
        assert "coding" in body_site, "bodySite should have coding array"
        assert len(body_site["coding"]) >= 2, "bodySite should have at least 2 codings (site + laterality)"

        # Verify main body site coding (Upper arm structure)
        site_coding = body_site["coding"][0]
        assert site_coding["system"] == "http://snomed.info/sct", "Body site system should be SNOMED CT"
        assert site_coding["code"] == "40983000", "Body site code should be 40983000 (Upper arm structure)"
        assert site_coding["display"] == "Upper arm structure", "Body site display should be preserved"

        # Verify laterality coding (Left)
        laterality_coding = body_site["coding"][1]
        assert laterality_coding["system"] == "http://snomed.info/sct", "Laterality system should be SNOMED CT"
        assert laterality_coding["code"] == "7771000", "Laterality code should be 7771000 (Left)"
        assert laterality_coding["display"] == "Left", "Laterality display should be preserved"

        # Verify text field includes both site and laterality
        assert "text" in body_site, "bodySite should have text field"
        assert "Left" in body_site["text"], "bodySite text should include laterality"
        assert "Upper arm structure" in body_site["text"], "bodySite text should include site"

    def test_converts_body_site_with_laterality_qualifier_heart_rate(self) -> None:
        """Test that targetSiteCode with laterality qualifier is converted for individual vital sign."""
        # Load fixture with heart rate with laterality qualifier
        with open("tests/integration/fixtures/ccda/vital_signs_hr_with_laterality.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify bodySite field is present
        assert "bodySite" in hr_obs, "Heart rate observation should have bodySite"
        body_site = hr_obs["bodySite"]

        # Verify coding array exists with at least 2 codings (site + laterality)
        assert "coding" in body_site, "bodySite should have coding array"
        assert len(body_site["coding"]) >= 2, "bodySite should have at least 2 codings (site + laterality)"

        # Verify main body site coding (Structure of radial artery)
        site_coding = body_site["coding"][0]
        assert site_coding["system"] == "http://snomed.info/sct", "Body site system should be SNOMED CT"
        assert site_coding["code"] == "45631007", "Body site code should be 45631007 (Structure of radial artery)"
        assert site_coding["display"] == "Structure of radial artery", "Body site display should be preserved"

        # Verify laterality coding (Right)
        laterality_coding = body_site["coding"][1]
        assert laterality_coding["system"] == "http://snomed.info/sct", "Laterality system should be SNOMED CT"
        assert laterality_coding["code"] == "24028007", "Laterality code should be 24028007 (Right)"
        assert laterality_coding["display"] == "Right", "Laterality display should be preserved"

        # Verify text field includes both site and laterality
        assert "text" in body_site, "bodySite should have text field"
        assert "Right" in body_site["text"], "bodySite text should include laterality"
        assert "Structure of radial artery" in body_site["text"], "bodySite text should include site"

    def test_converts_interpretation_code_normal(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for normal values."""
        # Load fixture with interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_with_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (Normal interpretation)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify interpretation field exists
        assert "interpretation" in hr_obs, "Observation should have interpretation field"
        interpretation = hr_obs["interpretation"]

        # Verify interpretation is an array of CodeableConcepts
        assert isinstance(interpretation, list), "interpretation should be an array"
        assert len(interpretation) > 0, "interpretation should have at least one element"

        # Verify interpretation CodeableConcept has coding
        assert "coding" in interpretation[0], "interpretation should have coding array"
        assert len(interpretation[0]["coding"]) > 0, "interpretation should have at least one coding"

        # Verify v3-ObservationInterpretation system and code
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", \
            "interpretation system should be v3-ObservationInterpretation"
        assert coding["code"] == "N", "interpretation code should be N (Normal)"
        assert coding["display"] == "Normal", "interpretation display should be preserved"

    def test_converts_interpretation_code_high(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for high values."""
        # Load fixture with interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_with_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find combined BP observation
        bp_obs = _find_observation_by_code(bundle, "85354-9")
        assert bp_obs is not None, "Blood pressure observation should be found"

        # Note: Systolic has H, diastolic has N - converter preserves first (systolic)
        # Verify interpretation field exists
        assert "interpretation" in bp_obs, "Observation should have interpretation field"
        interpretation = bp_obs["interpretation"]

        # Verify interpretation array
        assert isinstance(interpretation, list), "interpretation should be an array"
        assert len(interpretation) > 0, "interpretation should have at least one element"

        # Verify v3-ObservationInterpretation code H (High)
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert coding["code"] == "H", "interpretation code should be H (High)"
        assert coding["display"] == "High", "interpretation display should be preserved"

    def test_converts_interpretation_code_low(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for low values."""
        # Load fixture with interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_with_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find body temperature observation (Low interpretation)
        temp_obs = _find_observation_by_code(bundle, "8310-5")
        assert temp_obs is not None, "Body temperature observation should be found"

        # Verify interpretation field exists
        assert "interpretation" in temp_obs, "Observation should have interpretation field"
        interpretation = temp_obs["interpretation"]

        # Verify v3-ObservationInterpretation code L (Low)
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert coding["code"] == "L", "interpretation code should be L (Low)"
        assert coding["display"] == "Low", "interpretation display should be preserved"

    def test_converts_interpretation_code_abnormal(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for abnormal values."""
        # Load fixture with interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_with_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find respiratory rate observation (Abnormal interpretation)
        rr_obs = _find_observation_by_code(bundle, "9279-1")
        assert rr_obs is not None, "Respiratory rate observation should be found"

        # Verify interpretation field exists
        assert "interpretation" in rr_obs, "Observation should have interpretation field"
        interpretation = rr_obs["interpretation"]

        # Verify v3-ObservationInterpretation code A (Abnormal)
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert coding["code"] == "A", "interpretation code should be A (Abnormal)"
        assert coding["display"] == "Abnormal", "interpretation display should be preserved"

    def test_converts_interpretation_code_critical_high(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for critical high values."""
        # Load fixture with critical interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_critical_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (Critical high interpretation)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify interpretation field exists
        assert "interpretation" in hr_obs, "Observation should have interpretation field"
        interpretation = hr_obs["interpretation"]

        # Verify v3-ObservationInterpretation code HH (Critical high)
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert coding["code"] == "HH", "interpretation code should be HH (Critical high)"
        assert coding["display"] == "Critical high", "interpretation display should be preserved"

    def test_converts_interpretation_code_critical_low(self) -> None:
        """Test that interpretationCode is converted to Observation.interpretation for critical low values."""
        # Load fixture with critical interpretation codes
        with open("tests/integration/fixtures/ccda/vital_signs_critical_interpretation.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find body temperature observation (Critical low interpretation)
        temp_obs = _find_observation_by_code(bundle, "8310-5")
        assert temp_obs is not None, "Body temperature observation should be found"

        # Verify interpretation field exists
        assert "interpretation" in temp_obs, "Observation should have interpretation field"
        interpretation = temp_obs["interpretation"]

        # Verify v3-ObservationInterpretation code LL (Critical low)
        coding = interpretation[0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"
        assert coding["code"] == "LL", "interpretation code should be LL (Critical low)"
        assert coding["display"] == "Critical low", "interpretation display should be preserved"

    def test_interpretation_code_not_present_when_absent(self) -> None:
        """Test that interpretation field is not present when interpretationCode is absent in C-CDA."""
        # Use existing fixture without interpretationCode
        with open("tests/integration/fixtures/ccda/vital_signs.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (no interpretation code in this fixture)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify interpretation field is not present
        assert "interpretation" not in hr_obs, "Observation should not have interpretation field when interpretationCode is absent"

    def test_converts_reference_range_individual_vital_sign(self) -> None:
        """Test that referenceRange is converted for individual vital sign observations."""
        # Load fixture with heart rate with reference range
        with open("tests/integration/fixtures/ccda/vital_signs_hr_with_reference_range.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify referenceRange field exists
        assert "referenceRange" in hr_obs, "Observation should have referenceRange field"
        ref_ranges = hr_obs["referenceRange"]

        # Verify referenceRange is an array
        assert isinstance(ref_ranges, list), "referenceRange should be an array"
        assert len(ref_ranges) > 0, "referenceRange should have at least one element"

        # Verify first reference range has low and high values
        ref_range = ref_ranges[0]
        assert "low" in ref_range, "referenceRange should have low value"
        assert "high" in ref_range, "referenceRange should have high value"

        # Verify low value
        assert ref_range["low"]["value"] == 60, "Reference range low value should be 60"
        assert ref_range["low"]["unit"] == "/min", "Reference range low unit should be /min"
        assert ref_range["low"]["system"] == "http://unitsofmeasure.org", "Reference range should use UCUM system"

        # Verify high value
        assert ref_range["high"]["value"] == 100, "Reference range high value should be 100"
        assert ref_range["high"]["unit"] == "/min", "Reference range high unit should be /min"

        # Verify text if present
        assert "text" in ref_range, "referenceRange should have text field"
        assert "Normal heart rate range" in ref_range["text"], "referenceRange text should be preserved"

    def test_converts_reference_range_blood_pressure_panel(self) -> None:
        """Test that referenceRange is converted and combined for blood pressure panel observations."""
        # Load fixture with blood pressure with reference ranges
        with open("tests/integration/fixtures/ccda/vital_signs_bp_with_reference_ranges.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find combined blood pressure observation (should combine systolic/diastolic)
        bp_obs = _find_observation_by_code(bundle, "85354-9")
        assert bp_obs is not None, "Blood pressure observation should be found"

        # Verify referenceRange field exists
        assert "referenceRange" in bp_obs, "Blood pressure observation should have referenceRange field"
        ref_ranges = bp_obs["referenceRange"]

        # Verify referenceRange is an array with two elements (systolic and diastolic)
        assert isinstance(ref_ranges, list), "referenceRange should be an array"
        assert len(ref_ranges) == 2, "referenceRange should have two elements (systolic and diastolic)"

        # Verify systolic reference range (first element)
        systolic_ref = ref_ranges[0]
        assert "low" in systolic_ref, "Systolic referenceRange should have low value"
        assert "high" in systolic_ref, "Systolic referenceRange should have high value"
        assert systolic_ref["low"]["value"] == 90, "Systolic reference range low should be 90"
        assert systolic_ref["high"]["value"] == 120, "Systolic reference range high should be 120"
        assert "text" in systolic_ref, "Systolic referenceRange should have text field"
        assert "Systolic" in systolic_ref["text"], "Systolic referenceRange text should indicate systolic"

        # Verify diastolic reference range (second element)
        diastolic_ref = ref_ranges[1]
        assert "low" in diastolic_ref, "Diastolic referenceRange should have low value"
        assert "high" in diastolic_ref, "Diastolic referenceRange should have high value"
        assert diastolic_ref["low"]["value"] == 60, "Diastolic reference range low should be 60"
        assert diastolic_ref["high"]["value"] == 80, "Diastolic reference range high should be 80"
        assert "text" in diastolic_ref, "Diastolic referenceRange should have text field"
        assert "Diastolic" in diastolic_ref["text"], "Diastolic referenceRange text should indicate diastolic"

    def test_reference_range_not_present_when_absent(self) -> None:
        """Test that referenceRange field is not present when reference range is absent in C-CDA."""
        # Use existing fixture without reference ranges
        with open("tests/integration/fixtures/ccda/vital_signs.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation (no reference range in this fixture)
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify referenceRange field is not present
        assert "referenceRange" not in hr_obs, "Observation should not have referenceRange field when absent in C-CDA"

        # Find blood pressure observation (no reference range in this fixture)
        bp_obs = _find_observation_by_code(bundle, "85354-9")
        assert bp_obs is not None, "Blood pressure observation should be found"

        # Verify referenceRange field is not present in combined BP observation
        assert "referenceRange" not in bp_obs, "Blood pressure observation should not have referenceRange field when absent in C-CDA"

    def test_reference_range_filters_for_normal_interpretation_code_only(self) -> None:
        """Test that only reference ranges with interpretationCode='N' are included per C-CDA on FHIR IG."""
        # Load fixture with multiple reference ranges (Normal, High, Low)
        with open("tests/integration/fixtures/ccda/vital_signs_hr_with_multiple_reference_ranges.xml", encoding="utf-8") as f:
            ccda_vital_signs = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_vital_signs, VITAL_SIGNS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Find heart rate observation
        hr_obs = _find_observation_by_code(bundle, "8867-4")
        assert hr_obs is not None, "Heart rate observation should be found"

        # Verify referenceRange field exists
        assert "referenceRange" in hr_obs, "Observation should have referenceRange field"
        ref_ranges = hr_obs["referenceRange"]

        # Per C-CDA on FHIR IG: Only normal ranges (interpretationCode="N") should be included
        # The fixture has 3 ranges (N, H, L) but only the Normal one should be mapped
        assert len(ref_ranges) == 1, "Should only include one reference range (Normal interpretation code)"

        # Verify it's the normal range (60-100)
        ref_range = ref_ranges[0]
        assert ref_range["low"]["value"] == 60, "Should be the normal range with low=60"
        assert ref_range["high"]["value"] == 100, "Should be the normal range with high=100"
        assert "Normal heart rate range" in ref_range["text"], "Should be the normal range text"

        # Verify the high and low ranges were excluded
        # (If they were included, we'd have 3 ranges instead of 1)
