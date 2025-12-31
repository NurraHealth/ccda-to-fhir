"""Integration tests for Observation with ED (Encapsulated Data) value type."""

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


def _find_observation_by_code(
    observations: list[JSONObject], loinc_code: str
) -> JSONObject | None:
    """Find an observation with a specific LOINC code."""
    for obs in observations:
        if "code" in obs:
            for coding in obs["code"].get("coding", []):
                if (
                    coding.get("system") == "http://loinc.org"
                    and coding.get("code") == loinc_code
                ):
                    return obs
    return None


class TestObservationEDValue:
    """Tests for Observation value with ED (Encapsulated Data) type."""

    def test_ed_plain_text_creates_extension_with_attachment(self) -> None:
        """Test that ED plain text value creates extension with valueAttachment."""
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-1"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-1"/>
            <code code="5778-6" codeSystem="2.16.840.1.113883.6.1" displayName="Color of Urine"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" mediaType="text/plain">Yellow</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "5778-6")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        assert value_ext["valueAttachment"]["contentType"] == "text/plain"
        assert "data" in value_ext["valueAttachment"]

        # Verify base64 decoding
        import base64
        decoded = base64.b64decode(value_ext["valueAttachment"]["data"]).decode("utf-8")
        assert decoded == "Yellow"

    def test_ed_base64_encoded_preserves_encoding(self) -> None:
        """Test that ED with representation='B64' preserves the base64 encoding."""
        # "Hello World" in base64
        base64_content = "SGVsbG8gV29ybGQ="

        ccda = f"""
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-2"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-2"/>
            <code code="18748-4" codeSystem="2.16.840.1.113883.6.1" displayName="Diagnostic imaging study"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" representation="B64" mediaType="text/plain">{base64_content}</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "18748-4")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        assert value_ext["valueAttachment"]["contentType"] == "text/plain"
        assert value_ext["valueAttachment"]["data"] == base64_content

        # Verify decoding
        import base64
        decoded = base64.b64decode(value_ext["valueAttachment"]["data"]).decode("utf-8")
        assert decoded == "Hello World"

    def test_ed_custom_media_type(self) -> None:
        """Test that ED mediaType is correctly mapped to contentType."""
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-3"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-3"/>
            <code code="11502-2" codeSystem="2.16.840.1.113883.6.1" displayName="Laboratory report"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" mediaType="application/pdf">PDF content here</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "11502-2")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        assert value_ext["valueAttachment"]["contentType"] == "application/pdf"

    def test_ed_with_language(self) -> None:
        """Test that ED language attribute is mapped to attachment.language."""
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-4"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-4"/>
            <code code="11502-2" codeSystem="2.16.840.1.113883.6.1" displayName="Laboratory report"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" mediaType="text/plain" language="es-MX">Resultados en español</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "11502-2")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        assert value_ext["valueAttachment"]["language"] == "es-MX"

    def test_ed_no_value_does_not_create_extension(self) -> None:
        """Test that ED without value content does not create an extension."""
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-5"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-5"/>
            <code code="5778-6" codeSystem="2.16.840.1.113883.6.1" displayName="Color of Urine"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" mediaType="text/plain"></value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "5778-6")
        assert obs is not None

        # Should not have valueAttachment extension
        if "extension" in obs:
            value_exts = [
                ext for ext in obs["extension"]
                if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value"
            ]
            assert len(value_exts) == 0

    def test_ed_default_content_type(self) -> None:
        """Test that ED without mediaType uses default contentType."""
        ccda = """
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-6"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-6"/>
            <code code="5778-6" codeSystem="2.16.840.1.113883.6.1" displayName="Color of Urine"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED">Dark yellow</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "5778-6")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        # Default should be application/octet-stream
        assert value_ext["valueAttachment"]["contentType"] == "application/octet-stream"

    def test_ed_base64_with_whitespace_removed(self) -> None:
        """Test that base64 data with whitespace is properly cleaned."""
        # Base64 with newlines and spaces
        base64_content = """SGVs
        bG8g
        V29y
        bGQ="""

        ccda = f"""
<organizer classCode="BATTERY" moodCode="EVN" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
    <id root="result-org-7"/>
    <code code="24357-6" codeSystem="2.16.840.1.113883.6.1" displayName="Urinalysis macro panel"/>
    <statusCode code="completed"/>
    <effectiveTime value="20150622"/>
    <component>
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="obs-ed-7"/>
            <code code="18748-4" codeSystem="2.16.840.1.113883.6.1" displayName="Diagnostic imaging study"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150622"/>
            <value xsi:type="ED" representation="B64" mediaType="text/plain">{base64_content}</value>
        </observation>
    </component>
</organizer>
        """
        ccda_doc = wrap_in_ccda_document(ccda, RESULTS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observations = _find_all_resources_in_bundle(bundle, "Observation")
        obs = _find_observation_by_code(observations, "18748-4")
        assert obs is not None
        assert "extension" in obs

        # Find the valueAttachment extension
        value_ext = None
        for ext in obs["extension"]:
            if ext["url"] == "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value":
                value_ext = ext
                break

        assert value_ext is not None
        assert "valueAttachment" in value_ext
        # Should be cleaned (no whitespace)
        assert value_ext["valueAttachment"]["data"] == "SGVsbG8gV29ybGQ="

        # Verify decoding still works
        import base64
        decoded = base64.b64decode(value_ext["valueAttachment"]["data"]).decode("utf-8")
        assert decoded == "Hello World"
