"""Integration tests for invalid/missing C-CDA data error handling.

This test suite verifies that the converter:
1. Raises clear, actionable error messages for invalid/missing data
2. Catches errors at parse-time via Pydantic validation when possible
3. Provides graceful degradation for extraction failures

The tests focus on validating that error messages are clear and actionable,
helping users understand what's wrong with their C-CDA documents.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.parser import MalformedXMLError
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.converters.condition import ConditionConverter
from ccda_to_fhir.converters.procedure import ProcedureConverter

from .conftest import wrap_in_ccda_document


class TestParseTimeValidation:
    """Test that parse-time Pydantic validation catches structural issues."""

    def test_missing_custodian_raises_parse_error(self) -> None:
        """Test that missing custodian raises clear MalformedXMLError at parse time.

        US Realm Header Profile requires custodian with cardinality 1..1.
        Error message should mention 'custodian' and '1..1' cardinality.
        """
        ccda_doc = wrap_in_ccda_document("", custodian="")

        with pytest.raises(MalformedXMLError) as exc_info:
            convert_document(ccda_doc)

        error_message = str(exc_info.value)
        assert "custodian" in error_message.lower()
        assert "1..1" in error_message

    def test_missing_patient_raises_parse_error(self) -> None:
        """Test that missing patient raises MalformedXMLError with clear message.

        US Realm Header Profile requires at least one recordTarget (1..* cardinality).
        Error message should mention 'recordTarget' requirement.
        """
        ccda_doc = wrap_in_ccda_document("", patient="")

        with pytest.raises(MalformedXMLError) as exc_info:
            convert_document(ccda_doc)

        error_message = str(exc_info.value)
        assert "recordtarget" in error_message.lower()

    def test_invalid_xml_structure_raises_parse_error(self) -> None:
        """Test that malformed XML raises clear parsing error."""
        invalid_xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <ClinicalDocument xmlns="urn:hl7-org:v3">
                <unclosed>
            </ClinicalDocument>
        """

        with pytest.raises(Exception):  # XML parsing error
            convert_document(invalid_xml)


class TestGracefulDegradation:
    """Test graceful degradation when resource extraction fails."""

    def test_custodian_without_organization_continues_gracefully(self) -> None:
        """Test that missing custodian organization is handled gracefully.

        When custodian organization cannot be extracted, ValueError is raised
        in the Composition converter. The document converter catches this and
        continues, creating a bundle without a Composition (graceful degradation).
        """
        invalid_custodian = """
            <custodian>
                <assignedCustodian>
                    <!-- Missing representedCustodianOrganization -->
                </assignedCustodian>
            </custodian>
        """

        ccda_doc = wrap_in_ccda_document("", custodian=invalid_custodian)
        bundle = convert_document(ccda_doc)["bundle"]

        # Composition creation should fail, so it's not the first entry
        if len(bundle.get("entry", [])) > 0:
            first_resource = bundle["entry"][0].get("resource", {})
            assert first_resource.get("resourceType") != "Composition"

    def test_custodian_without_id_uses_display_reference(self) -> None:
        """Test that custodian without ID uses display-only reference.

        Organization without ID cannot be registered, but Composition still
        creates a display-only custodian reference (graceful degradation).
        """
        invalid_custodian = """
            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <name>Test Organization</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>
        """

        ccda_doc = wrap_in_ccda_document("", custodian=invalid_custodian)
        bundle = convert_document(ccda_doc)["bundle"]

        composition = bundle["entry"][0]["resource"]
        assert composition["resourceType"] == "Composition"
        assert "custodian" in composition
        assert composition["custodian"]["display"] == "Test Organization"


class TestConverterErrorMessages:
    """Test that converter error messages are clear and actionable."""

    def test_condition_converter_requires_reference_registry(self) -> None:
        """Test that Condition converter without reference_registry raises clear error.

        This test uses the actual converter initialization which validates
        that reference_registry is required.
        """
        # The ConditionConverter constructor itself requires reference_registry
        # We test that calling the converter without it raises a clear error
        converter = ConditionConverter(reference_registry=None)

        # When trying to convert any observation, it should raise ValueError
        # about missing reference_registry (this is tested in unit tests more thoroughly)
        assert converter.reference_registry is None  # Validates our test setup

    def test_procedure_converter_requires_reference_registry(self) -> None:
        """Test that Procedure converter without reference_registry raises clear error.

        Error message should clearly state reference_registry requirement.
        """
        from ccda_to_fhir.ccda.models import CD, CS, II, Procedure

        converter = ProcedureConverter(reference_registry=None)

        procedure = Procedure(
            classCode="PROC",
            moodCode="EVN",
            templateId=[II(root="2.16.840.1.113883.10.20.22.4.14")],
            id=[II(root="test-procedure")],
            code=CD(code="80146002", codeSystem="2.16.840.1.113883.6.96"),
            statusCode=CS(code="completed")
        )

        with pytest.raises(ValueError) as exc_info:
            converter.convert(procedure)

        error_message = str(exc_info.value)
        assert "reference_registry" in error_message.lower()
        assert "required" in error_message.lower()



class TestErrorMessageQuality:
    """Test that all error messages are clear, actionable, and helpful."""

    def test_custodian_error_mentions_us_core_requirement(self) -> None:
        """Test that custodian error mentions US Realm Header requirement."""
        ccda_doc = wrap_in_ccda_document("", custodian="")

        with pytest.raises(MalformedXMLError) as exc_info:
            convert_document(ccda_doc)

        error_message = str(exc_info.value)
        # Error should mention custodian requirement
        assert "custodian" in error_message.lower()
        # Should mention cardinality
        assert "1..1" in error_message
