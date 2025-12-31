"""E2E tests for Smoking Status Observation resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

SOCIAL_HISTORY_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.17"


def _find_smoking_status_observation(bundle: JSONObject) -> JSONObject | None:
    """Find the smoking status Observation in the bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") == "72166-2":
                    return resource
    return None


class TestSmokingStatusConversion:
    """E2E tests for C-CDA Smoking Status Observation to FHIR Observation conversion."""

    def test_resource_type_is_observation(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that the resource type is Observation."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["resourceType"] == "Observation"

    def test_converts_status(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that status is correctly mapped to final."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["status"] == "final"

    def test_converts_category(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that category is set to social-history."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert observation["category"][0]["coding"][0]["code"] == "social-history"
        assert observation["category"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

    def test_converts_code(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that observation code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "code" in observation
        loinc = next(
            (c for c in observation["code"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "72166-2"
        assert loinc["display"] == "Tobacco smoking status NHIS"

    def test_converts_effective_datetime(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "effectiveDateTime" in observation
        assert "2014-06-06" in observation["effectiveDateTime"]

    def test_converts_value_codeable_concept(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that CD value is converted to valueCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "valueCodeableConcept" in observation
        snomed = next(
            (c for c in observation["valueCodeableConcept"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "449868002"
        assert snomed["display"] == "Current every day smoker"

    def test_converts_identifier(
        self, ccda_smoking_status: str, fhir_smoking_status: JSONObject
    ) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None
        assert "identifier" in observation
        assert observation["identifier"][0]["value"] == "123456789"

    def test_provenance_has_recorded_date(
        self, ccda_smoking_status_with_author: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status_with_author, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        obs_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                observation["id"] in t.get("reference", "") for t in prov["target"]
            ):
                obs_provenance = prov
                break

        assert obs_provenance is not None
        assert "recorded" in obs_provenance
        # Should have a valid ISO datetime
        assert len(obs_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_smoking_status_with_author: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status_with_author, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        obs_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                observation["id"] in t.get("reference", "") for t in prov["target"]
            ):
                obs_provenance = prov
                break

        assert obs_provenance is not None
        assert "agent" in obs_provenance
        assert len(obs_provenance["agent"]) > 0

        # Check agent type
        agent = obs_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_smoking_status_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_smoking_status_multiple_authors, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_smoking_status_observation(bundle)
        assert observation is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        obs_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                observation["id"] in t.get("reference", "") for t in prov["target"]
            ):
                obs_provenance = prov
                break

        assert obs_provenance is not None
        assert "agent" in obs_provenance
        # Should have multiple agents for multiple authors
        assert len(obs_provenance["agent"]) >= 2

        # Verify all agents reference practitioners
        for agent in obs_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_narrative_propagates_from_text_reference(self) -> None:
        """Test that Observation.text narrative is generated from text/reference."""
        # Create complete document with section text and entry with text/reference
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                    <code code="29762-2" codeSystem="2.16.840.1.113883.6.1" displayName="Social History"/>
                    <text>
                        <paragraph ID="smoking-narrative-1">
                            <content styleCode="Bold">Smoking Status:</content>
                            Current every day smoker, started at age 16.
                        </paragraph>
                    </text>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
                            <id root="smoking-obs-123"/>
                            <code code="72166-2" displayName="Tobacco smoking status NHIS"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <text>
                                <reference value="#smoking-narrative-1"/>
                            </text>
                            <statusCode code="completed"/>
                            <effectiveTime value="20231201"/>
                            <value xsi:type="CD" code="449868002" displayName="Current every day smoker"
                                   codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)["bundle"]

        smoking_obs = _find_smoking_status_observation(bundle)
        assert smoking_obs is not None

        # Verify Observation has text.div with resolved narrative
        assert "text" in smoking_obs, "Observation should have .text field"
        assert "status" in smoking_obs["text"]
        assert smoking_obs["text"]["status"] == "generated"
        assert "div" in smoking_obs["text"], "Observation should have .text.div"

        div_content = smoking_obs["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify referenced content was resolved
        assert "Current every day smoker" in div_content
        assert "started at age 16" in div_content

        # Verify structured markup preserved
        assert "<p" in div_content  # Paragraph converted to <p>
        assert 'id="smoking-narrative-1"' in div_content  # ID preserved
        assert 'class="Bold"' in div_content or "Bold" in div_content  # Style preserved
