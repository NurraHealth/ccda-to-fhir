"""Unit tests for BaseConverter shared utility methods.

Tests the shared conversion utilities including:
- convert_human_names: C-CDA PN to FHIR HumanName
- convert_telecom: C-CDA TEL to FHIR ContactPoint
- convert_addresses: C-CDA AD to FHIR Address

These methods are shared across Patient, Practitioner, RelatedPerson,
Organization, Location, and other converters.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.datatypes import CS, ENXP, IVL_TS, PN, TS
from ccda_to_fhir.converters.patient import PatientConverter


@pytest.fixture
def converter():
    """Create a PatientConverter instance for testing base methods."""
    return PatientConverter()


class TestConvertHumanNames:
    """Test convert_human_names utility method."""

    def test_converts_basic_name(self, converter):
        """Test basic name with given and family."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["given"] == ["John"]
        assert result[0]["family"] == "Smith"

    def test_converts_multiple_given_names(self, converter):
        """Test name with multiple given names (first + middle)."""
        names = [
            PN(
                given=[ENXP(value="John"), ENXP(value="Jacob")],
                family=ENXP(value="Smith"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["given"] == ["John", "Jacob"]
        assert result[0]["family"] == "Smith"

    def test_converts_name_with_prefix(self, converter):
        """Test name with prefix (Dr., Mr., etc.)."""
        names = [
            PN(
                prefix=[ENXP(value="Dr.")],
                given=[ENXP(value="Jane")],
                family=ENXP(value="Doe"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["prefix"] == ["Dr."]
        assert result[0]["given"] == ["Jane"]
        assert result[0]["family"] == "Doe"

    def test_converts_name_with_suffix(self, converter):
        """Test name with suffix (MD, Jr., etc.)."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
                suffix=[ENXP(value="MD"), ENXP(value="PhD")],
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["given"] == ["John"]
        assert result[0]["family"] == "Smith"
        assert result[0]["suffix"] == ["MD", "PhD"]

    def test_converts_name_with_use_code(self, converter):
        """Test name with use code (L=Legal, P=Pseudonym)."""
        names = [
            PN(
                use="L",  # Legal
                given=[ENXP(value="Isabella")],
                family=ENXP(value="Garcia"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["use"] == "usual"  # L (Legal) -> usual per mapping
        assert result[0]["given"] == ["Isabella"]
        assert result[0]["family"] == "Garcia"

    def test_converts_name_with_period(self, converter):
        """Test name with valid_time (period)."""
        names = [
            PN(
                given=[ENXP(value="Mary")],
                family=ENXP(value="Johnson"),
                valid_time=IVL_TS(
                    low=TS(value="20100101"),
                    high=TS(value="20201231"),
                ),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["given"] == ["Mary"]
        assert result[0]["family"] == "Johnson"
        assert "period" in result[0]
        assert result[0]["period"]["start"] == "2010-01-01"
        assert result[0]["period"]["end"] == "2020-12-31"

    def test_converts_multiple_names(self, converter):
        """Test multiple names (legal + nickname)."""
        names = [
            PN(
                use="L",  # Legal
                given=[ENXP(value="Isabella"), ENXP(value="Maria")],
                family=ENXP(value="Garcia"),
            ),
            PN(
                use="P",  # Pseudonym/Nickname
                given=[ENXP(value="Bella")],
            ),
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 2
        assert result[0]["use"] == "usual"
        assert result[0]["given"] == ["Isabella", "Maria"]
        assert result[0]["family"] == "Garcia"
        assert result[1]["use"] == "nickname"
        assert result[1]["given"] == ["Bella"]

    def test_handles_none_input(self, converter):
        """Test handling of None input."""
        result = converter.convert_human_names(None)

        assert result == []

    def test_handles_empty_list(self, converter):
        """Test handling of empty list."""
        result = converter.convert_human_names([])

        assert result == []

    def test_handles_single_name_not_list(self, converter):
        """Test handling of single name (not in list)."""
        name = PN(
            given=[ENXP(value="John")],
            family=ENXP(value="Doe"),
        )

        result = converter.convert_human_names(name)

        assert len(result) == 1
        assert result[0]["given"] == ["John"]
        assert result[0]["family"] == "Doe"

    def test_skips_none_names_in_list(self, converter):
        """Test that None names in list are skipped."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
            ),
            None,
            PN(
                given=[ENXP(value="Jane")],
                family=ENXP(value="Doe"),
            ),
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 2
        assert result[0]["family"] == "Smith"
        assert result[1]["family"] == "Doe"

    def test_skips_empty_given_values(self, converter):
        """Test that empty given values are filtered out."""
        names = [
            PN(
                given=[ENXP(value="John"), ENXP(value=""), ENXP(value="Jacob")],
                family=ENXP(value="Smith"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        # Empty strings should be filtered out
        assert result[0]["given"] == ["John", "Jacob"]

    def test_extract_enxp_handles_string_input(self, converter):
        """Test that _extract_enxp_value_and_qualifier handles string input.

        The ENXP extraction method accepts strings for backward compatibility
        with edge cases where the parser produces plain strings.
        """
        # Direct string input to the extraction method
        value, qualifier = converter._extract_enxp_value_and_qualifier("Smith")

        assert value == "Smith"
        assert qualifier is None

    def test_complete_name_with_all_fields(self, converter):
        """Test complete name with all possible fields."""
        names = [
            PN(
                use="L",
                prefix=[ENXP(value="Dr."), ENXP(value="Professor")],
                given=[ENXP(value="John"), ENXP(value="Jacob")],
                family=ENXP(value="Smith"),
                suffix=[ENXP(value="MD"), ENXP(value="Jr.")],
                valid_time=IVL_TS(
                    low=TS(value="20150101"),
                    high=TS(value="20251231"),
                ),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        name = result[0]
        assert name["use"] == "usual"
        assert name["prefix"] == ["Dr.", "Professor"]
        assert name["given"] == ["John", "Jacob"]
        assert name["family"] == "Smith"
        assert name["suffix"] == ["MD", "Jr."]
        assert name["period"]["start"] == "2015-01-01"
        assert name["period"]["end"] == "2025-12-31"


class TestConvertHumanNamesENXPQualifier:
    """Test ENXP qualifier handling in convert_human_names."""

    def test_qualifier_cl_sets_nickname_use(self, converter):
        """Test that CL (callme) qualifier sets use to nickname."""
        names = [
            PN(
                given=[ENXP(value="Bobby", qualifier="CL")],  # Callme/nickname
                family=ENXP(value="Smith"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["given"] == ["Bobby"]
        assert result[0]["use"] == "nickname"

    def test_qualifier_br_sets_maiden_use(self, converter):
        """Test that BR (birth) qualifier sets use to maiden."""
        names = [
            PN(
                given=[ENXP(value="Mary")],
                family=ENXP(value="Johnson", qualifier="BR"),  # Birth name
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["family"] == "Johnson"
        assert result[0]["use"] == "maiden"

    def test_qualifier_sp_sets_maiden_use(self, converter):
        """Test that SP (spouse) qualifier sets use to maiden (previous married name)."""
        names = [
            PN(
                given=[ENXP(value="Jane")],
                family=ENXP(value="Williams", qualifier="SP"),  # Previous spouse name
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["family"] == "Williams"
        assert result[0]["use"] == "maiden"

    def test_explicit_use_overrides_qualifier(self, converter):
        """Test that explicit PN.use takes precedence over ENXP qualifier."""
        names = [
            PN(
                use="L",  # Explicit Legal use
                given=[ENXP(value="Bobby", qualifier="CL")],  # Would imply nickname
                family=ENXP(value="Smith"),
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        # Explicit use="L" should map to "usual", not "nickname"
        assert result[0]["use"] == "usual"

    def test_academic_qualifier_preserved_in_suffix(self, converter):
        """Test that academic suffix values are preserved."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
                suffix=[ENXP(value="PhD", qualifier="AC")],  # Academic qualifier
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["suffix"] == ["PhD"]


class TestConvertHumanNamesDelimiter:
    """Test delimiter handling in convert_human_names."""

    def test_builds_text_with_default_space_delimiter(self, converter):
        """Test that text is built with space delimiter by default."""
        names = [
            PN(
                prefix=[ENXP(value="Dr.")],
                given=[ENXP(value="John"), ENXP(value="Jacob")],
                family=ENXP(value="Smith"),
                suffix=[ENXP(value="MD")],
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["text"] == "Dr. John Jacob Smith MD"

    def test_builds_text_with_custom_delimiter(self, converter):
        """Test that text respects custom delimiter."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
                delimiter=[", "],  # Custom delimiter
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["text"] == "John, Smith"

    def test_builds_text_with_string_delimiter(self, converter):
        """Test that text handles string delimiter (single element list)."""
        names = [
            PN(
                given=[ENXP(value="John")],
                family=ENXP(value="Smith"),
                delimiter=["-"],  # Single element list delimiter
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["text"] == "John-Smith"


class TestConvertHumanNamesNullFlavor:
    """Test null_flavor handling in convert_human_names."""

    def test_null_flavor_unk_creates_data_absent_reason(self, converter):
        """Test that UNK null_flavor creates data-absent-reason extension."""
        names = [PN(null_flavor="UNK")]  # Unknown

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert "extension" in result[0]
        assert len(result[0]["extension"]) == 1
        ext = result[0]["extension"][0]
        assert ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert ext["valueCode"] == "unknown"

    def test_null_flavor_msk_creates_masked_reason(self, converter):
        """Test that MSK null_flavor maps to masked."""
        names = [PN(null_flavor="MSK")]  # Masked

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "masked"

    def test_null_flavor_asku_creates_asked_unknown_reason(self, converter):
        """Test that ASKU null_flavor maps to asked-unknown."""
        names = [PN(null_flavor="ASKU")]  # Asked but unknown

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "asked-unknown"

    def test_null_flavor_na_creates_not_applicable_reason(self, converter):
        """Test that NA null_flavor maps to not-applicable."""
        names = [PN(null_flavor="NA")]  # Not applicable

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "not-applicable"

    def test_null_flavor_skips_name_content_extraction(self, converter):
        """Test that null_flavor names don't have given/family extracted."""
        names = [
            PN(
                null_flavor="UNK",
                given=[ENXP(value="John")],  # Should be ignored
                family=ENXP(value="Smith"),  # Should be ignored
            )
        ]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        # Should only have extension, not given/family
        assert "extension" in result[0]
        assert "given" not in result[0]
        assert "family" not in result[0]


# =============================================================================
# Error Handling Helpers Tests
# =============================================================================


class TestRequireField:
    """Test require_field validation helper."""

    def test_require_field_passes_with_value(self, converter):
        """Test that require_field passes when value is present."""
        # Should not raise
        converter.require_field("some_value", "code", "Observation")

    def test_require_field_passes_with_non_empty_list(self, converter):
        """Test that require_field passes with non-empty list."""
        # Should not raise
        converter.require_field([1, 2, 3], "items", "Resource")

    def test_require_field_raises_on_none(self, converter):
        """Test that require_field raises MissingRequiredFieldError on None."""
        from ccda_to_fhir.exceptions import MissingRequiredFieldError

        with pytest.raises(MissingRequiredFieldError) as exc_info:
            converter.require_field(None, "code", "Observation")

        assert exc_info.value.field_name == "code"
        assert exc_info.value.resource_type == "Observation"

    def test_require_field_raises_on_empty_string(self, converter):
        """Test that require_field raises on empty string."""
        from ccda_to_fhir.exceptions import MissingRequiredFieldError

        with pytest.raises(MissingRequiredFieldError) as exc_info:
            converter.require_field("", "status", "Condition")

        assert exc_info.value.field_name == "status"

    def test_require_field_raises_on_empty_list(self, converter):
        """Test that require_field raises on empty list."""
        from ccda_to_fhir.exceptions import MissingRequiredFieldError

        with pytest.raises(MissingRequiredFieldError) as exc_info:
            converter.require_field([], "identifier", "Patient")

        assert exc_info.value.field_name == "identifier"

    def test_require_field_includes_details_in_message(self, converter):
        """Test that require_field includes details in error message."""
        from ccda_to_fhir.exceptions import MissingRequiredFieldError

        with pytest.raises(MissingRequiredFieldError) as exc_info:
            converter.require_field(
                None,
                "participant",
                "AllergyIntolerance",
                details="Allergen is required for allergy observation",
            )

        assert "Allergen is required" in str(exc_info.value)


class TestOptionalField:
    """Test optional_field conversion helper."""

    def test_optional_field_returns_default_on_none(self, converter):
        """Test that optional_field returns default when value is None."""
        result = converter.optional_field(
            None,
            lambda x: x.upper(),
            "name",
            default="unknown",
        )
        assert result == "unknown"

    def test_optional_field_converts_value(self, converter):
        """Test that optional_field converts value when present."""
        result = converter.optional_field(
            "hello",
            lambda x: x.upper(),
            "name",
            default="unknown",
        )
        assert result == "HELLO"

    def test_optional_field_returns_default_on_exception(self, converter):
        """Test that optional_field returns default when converter raises."""
        def bad_converter(x):
            raise ValueError("bad input")

        result = converter.optional_field(
            "some_value",
            bad_converter,
            "bad_field",
            default="fallback",
        )
        assert result == "fallback"

    def test_optional_field_returns_default_when_converter_returns_none(self, converter):
        """Test that optional_field returns default when converter returns None."""
        result = converter.optional_field(
            "value",
            lambda x: None,
            "field",
            default="default_value",
        )
        assert result == "default_value"


class TestMapStatusCode:
    """Test map_status_code utility method."""

    def test_map_status_code_with_valid_code(self, converter):
        """Test mapping a valid status code."""
        mapping = {"active": "active", "completed": "inactive"}
        status_code = CS(code="completed")

        result = converter.map_status_code(status_code, mapping, "unknown")
        assert result == "inactive"

    def test_map_status_code_case_insensitive(self, converter):
        """Test that status code mapping is case insensitive."""
        mapping = {"completed": "final"}
        status_code = CS(code="COMPLETED")

        result = converter.map_status_code(status_code, mapping, "unknown")
        assert result == "final"

    def test_map_status_code_returns_default_on_none(self, converter):
        """Test that None status code returns default."""
        mapping = {"active": "active"}
        result = converter.map_status_code(None, mapping, "unknown")
        assert result == "unknown"

    def test_map_status_code_returns_default_on_none_code(self, converter):
        """Test that None code attribute returns default."""
        mapping = {"active": "active"}
        status_code = CS(code=None)

        result = converter.map_status_code(status_code, mapping, "default")
        assert result == "default"

    def test_map_status_code_returns_default_on_unmapped(self, converter):
        """Test that unmapped code returns default."""
        mapping = {"active": "active"}
        status_code = CS(code="unmapped_status")

        result = converter.map_status_code(status_code, mapping, "fallback")
        assert result == "fallback"

    def test_map_status_code_with_string_input(self, converter):
        """Test that string input works directly."""
        mapping = {"active": "active", "completed": "final"}
        result = converter.map_status_code("active", mapping, "unknown")
        assert result == "active"


class TestHandleDuplicateId:
    """Test handle_duplicate_id helper for ID reuse detection."""

    def test_handle_duplicate_id_returns_none_for_new_id(self, converter):
        """Test that new ID returns None (no fallback needed)."""
        seen_ids = set()
        id_key = ("2.16.840.1.113883.19.5", "obs-001")

        result = converter.handle_duplicate_id(id_key, seen_ids, "Observation")

        assert result is None

    def test_handle_duplicate_id_returns_new_id_for_duplicate(self, converter):
        """Test that duplicate ID returns a new unique ID."""
        seen_ids = {("2.16.840.1.113883.19.5", "obs-001")}
        id_key = ("2.16.840.1.113883.19.5", "obs-001")

        result = converter.handle_duplicate_id(id_key, seen_ids, "Observation")

        assert result is not None
        # Should be a UUID format
        assert len(result) == 36
        assert result.count("-") == 4


# =============================================================================
# Exception Classes Tests
# =============================================================================


class TestConversionWarning:
    """Test ConversionWarning exception class."""

    def test_basic_message(self):
        """Test ConversionWarning with just a message."""
        from ccda_to_fhir.exceptions import ConversionWarning

        warning = ConversionWarning("Unexpected format")
        assert str(warning) == "Unexpected format"

    def test_with_field_name(self):
        """Test ConversionWarning with field name."""
        from ccda_to_fhir.exceptions import ConversionWarning

        warning = ConversionWarning("Unexpected format", field_name="telecom")
        assert str(warning) == "telecom: Unexpected format"
        assert warning.field_name == "telecom"

    def test_with_context(self):
        """Test ConversionWarning with context."""
        from ccda_to_fhir.exceptions import ConversionWarning

        warning = ConversionWarning(
            "Code not recognized",
            field_name="code",
            context="Observation conversion",
        )
        assert "code: Code not recognized" in str(warning)
        assert "(in Observation conversion)" in str(warning)
        assert warning.context == "Observation conversion"


class TestRecoverableConversionError:
    """Test RecoverableConversionError exception class."""

    def test_basic_message(self):
        """Test RecoverableConversionError with just a message."""
        from ccda_to_fhir.exceptions import RecoverableConversionError

        error = RecoverableConversionError("Invalid date format")
        assert str(error) == "Invalid date format"

    def test_with_field_name(self):
        """Test RecoverableConversionError with field name."""
        from ccda_to_fhir.exceptions import RecoverableConversionError

        error = RecoverableConversionError(
            "Invalid format",
            field_name="effectiveTime",
        )
        assert str(error) == "effectiveTime: Invalid format"
        assert error.field_name == "effectiveTime"

    def test_with_fallback_value(self):
        """Test RecoverableConversionError with fallback value."""
        from ccda_to_fhir.exceptions import RecoverableConversionError

        error = RecoverableConversionError(
            "Status code not mapped",
            field_name="status",
            fallback_value="unknown",
        )
        assert "status: Status code not mapped" in str(error)
        assert "(using fallback: unknown)" in str(error)
        assert error.fallback_value == "unknown"

    def test_with_all_fields(self):
        """Test RecoverableConversionError with all fields populated."""
        from ccda_to_fhir.exceptions import RecoverableConversionError

        error = RecoverableConversionError(
            "Code system not recognized",
            field_name="codeSystem",
            fallback_value="urn:oid:2.16.840.1.113883",
            context="CodeableConcept conversion",
        )
        assert error.field_name == "codeSystem"
        assert error.fallback_value == "urn:oid:2.16.840.1.113883"
        assert error.context == "CodeableConcept conversion"
        assert "codeSystem: Code system not recognized" in str(error)
        assert "(using fallback: urn:oid:2.16.840.1.113883)" in str(error)
        assert "(in CodeableConcept conversion)" in str(error)
