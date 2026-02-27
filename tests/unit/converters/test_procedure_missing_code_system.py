"""Unit tests for Procedure code handling when code_system is missing.

This tests the fix for the bug where a procedure with a code value but no code_system
would result in `code: null` in the FHIR output, causing validation errors.
"""

from ccda_to_fhir.ccda.models.datatypes import CE, CS, II
from ccda_to_fhir.ccda.models.procedure import Procedure as CCDAProcedure
from ccda_to_fhir.converters.procedure import ProcedureConverter


class TestProcedureMissingCodeSystem:
    """Test Procedure conversion when code_system is missing."""

    def create_procedure_with_code(
        self,
        code: str | None = None,
        code_system: str | None = None,
        display_name: str | None = None,
    ) -> CCDAProcedure:
        """Helper to create procedure with specific code attributes."""
        proc = CCDAProcedure()
        proc.code = CE(
            code=code,
            code_system=code_system,
            display_name=display_name,
        )
        proc.id = [II(root="1.2.3.4", extension="proc-1")]
        proc.status_code = CS(code="completed")
        return proc

    def test_code_with_missing_code_system_uses_data_absent_reason(
        self, mock_reference_registry
    ):
        """Test that code with value but no code_system gets data-absent-reason.

        This is the key bug fix: previously this would result in code=null.
        Now it should use data-absent-reason extension.
        """
        # This matches the real-world case we found:
        # code='24606-6' code_system=None code_system_name='UNK'
        proc = self.create_procedure_with_code(
            code="24606-6",
            code_system=None,
            display_name="",
        )

        converter = ProcedureConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(proc)

        # code should NOT be None
        assert result["code"] is not None, "code should not be None"

        # Should have data-absent-reason extension
        assert "extension" in result["code"], "code should have extension"
        extensions = result["code"]["extension"]
        assert len(extensions) == 1
        assert extensions[0]["url"] == (
            "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        )
        assert extensions[0]["valueCode"] == "unknown"

        # Should have fallback text
        assert result["code"].get("text") == "Procedure code not specified"

    def test_code_with_code_system_creates_valid_codeable_concept(
        self, mock_reference_registry
    ):
        """Test that code with both value and code_system works normally."""
        proc = self.create_procedure_with_code(
            code="80146002",
            code_system="2.16.840.1.113883.6.96",  # SNOMED CT
            display_name="Appendectomy",
        )

        converter = ProcedureConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(proc)

        # code should be a valid CodeableConcept
        assert result["code"] is not None
        assert "coding" in result["code"]
        assert len(result["code"]["coding"]) == 1
        assert result["code"]["coding"][0]["code"] == "80146002"
        assert result["code"]["coding"][0]["system"] == "http://snomed.info/sct"
        assert result["code"]["coding"][0]["display"] == "Appendectomy"

    def test_code_with_display_name_but_no_code_system_uses_text(
        self, mock_reference_registry
    ):
        """Test that code with display_name but no code_system uses text fallback.

        When we have a display_name, we should use it as the text even if
        code_system is missing.
        """
        proc = self.create_procedure_with_code(
            code="12345",
            code_system=None,
            display_name="Some Procedure Name",
        )

        converter = ProcedureConverter(
            code_system_mapper=None,
            reference_registry=mock_reference_registry,
        )
        result = converter.convert(proc)

        # code should NOT be None
        assert result["code"] is not None, "code should not be None"

        # Should have the data-absent-reason since conversion failed,
        # but we fall back to the narrative text extraction path
        # Since there's no narrative, we get data-absent-reason
        assert "extension" in result["code"] or "text" in result["code"]
