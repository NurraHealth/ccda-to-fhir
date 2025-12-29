"""Integration tests for the main converter module."""

from ccda_to_fhir.convert import convert_document


def test_convert_returns_bundle() -> None:
    """Test that convert returns a FHIR Bundle structure."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <code code="34133-9" displayName="Summarization of Episode Note"/>
        <component>
            <structuredBody>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """
    result = convert_document(xml)["bundle"]

    assert result["resourceType"] == "Bundle"
    assert result["type"] == "document"
    assert "entry" in result
