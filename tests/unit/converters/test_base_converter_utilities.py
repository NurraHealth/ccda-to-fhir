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

from ccda_to_fhir.ccda.models.datatypes import ENXP, IVL_TS, PN, TS
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

    def test_handles_string_family_name(self, converter):
        """Test handling of family as string instead of ENXP."""
        # Some C-CDA documents might have family as string
        class MockName:
            def __init__(self):
                self.given = [ENXP(value="John")]
                self.family = "Smith"  # String instead of ENXP
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None

        names = [MockName()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["family"] == "Smith"
        assert result[0]["given"] == ["John"]

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
        # Create a mock PN with delimiter
        class MockNameWithDelimiter:
            def __init__(self):
                self.given = [ENXP(value="John")]
                self.family = ENXP(value="Smith")
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.null_flavor = None
                self.delimiter = [", "]  # Custom delimiter

        names = [MockNameWithDelimiter()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["text"] == "John, Smith"

    def test_builds_text_with_string_delimiter(self, converter):
        """Test that text handles string delimiter (not list)."""
        class MockNameWithStringDelimiter:
            def __init__(self):
                self.given = [ENXP(value="John")]
                self.family = ENXP(value="Smith")
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.null_flavor = None
                self.delimiter = "-"  # String delimiter

        names = [MockNameWithStringDelimiter()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert result[0]["text"] == "John-Smith"


class TestConvertHumanNamesNullFlavor:
    """Test null_flavor handling in convert_human_names."""

    def test_null_flavor_unk_creates_data_absent_reason(self, converter):
        """Test that UNK null_flavor creates data-absent-reason extension."""
        class MockNameWithNullFlavor:
            def __init__(self):
                self.null_flavor = "UNK"  # Unknown
                self.given = None
                self.family = None
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.delimiter = None

        names = [MockNameWithNullFlavor()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        assert "extension" in result[0]
        assert len(result[0]["extension"]) == 1
        ext = result[0]["extension"][0]
        assert ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert ext["valueCode"] == "unknown"

    def test_null_flavor_msk_creates_masked_reason(self, converter):
        """Test that MSK null_flavor maps to masked."""
        class MockNameWithMaskedNullFlavor:
            def __init__(self):
                self.null_flavor = "MSK"  # Masked
                self.given = None
                self.family = None
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.delimiter = None

        names = [MockNameWithMaskedNullFlavor()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "masked"

    def test_null_flavor_asku_creates_asked_unknown_reason(self, converter):
        """Test that ASKU null_flavor maps to asked-unknown."""
        class MockNameWithAskuNullFlavor:
            def __init__(self):
                self.null_flavor = "ASKU"  # Asked but unknown
                self.given = None
                self.family = None
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.delimiter = None

        names = [MockNameWithAskuNullFlavor()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "asked-unknown"

    def test_null_flavor_na_creates_not_applicable_reason(self, converter):
        """Test that NA null_flavor maps to not-applicable."""
        class MockNameWithNaNullFlavor:
            def __init__(self):
                self.null_flavor = "NA"  # Not applicable
                self.given = None
                self.family = None
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.delimiter = None

        names = [MockNameWithNaNullFlavor()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        ext = result[0]["extension"][0]
        assert ext["valueCode"] == "not-applicable"

    def test_null_flavor_skips_name_content_extraction(self, converter):
        """Test that null_flavor names don't have given/family extracted."""
        class MockNameWithNullFlavorAndContent:
            def __init__(self):
                self.null_flavor = "UNK"
                self.given = [ENXP(value="John")]  # Should be ignored
                self.family = ENXP(value="Smith")  # Should be ignored
                self.prefix = None
                self.suffix = None
                self.use = None
                self.valid_time = None
                self.delimiter = None

        names = [MockNameWithNullFlavorAndContent()]

        result = converter.convert_human_names(names)

        assert len(result) == 1
        # Should only have extension, not given/family
        assert "extension" in result[0]
        assert "given" not in result[0]
        assert "family" not in result[0]
