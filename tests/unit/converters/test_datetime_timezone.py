"""Tests for datetime and timezone handling in convert_date().

Regression tests for BUG-002A (invalid timezone) and BUG-002B (fractional seconds).
"""

import pytest

from ccda_to_fhir.converters.encounter import EncounterConverter


class TestInvalidTimezoneHandling:
    """Regression tests for BUG-002A: Invalid timezone handling.

    When C-CDA timestamp has invalid timezone (out of range or malformed),
    convert_date() should reduce precision to date-only per FHIR R4 requirement
    rather than returning datetime with time but no timezone.
    """

    @pytest.fixture
    def converter(self):
        """Create converter instance for testing."""
        return EncounterConverter()

    def test_invalid_timezone_out_of_range_reduces_to_date(self, converter):
        """Test that timezone out of valid range causes reduction to date-only.

        Regression test for BUG-002A: Timezone offset of -5000 (50 hours) is invalid.
        Should reduce to date-only format, not return datetime without timezone.
        """
        result = converter.convert_date("20150722230000-5000")

        # Should reduce to date-only, not return datetime without timezone
        assert result == "2015-07-22", \
            f"Expected date-only format for invalid timezone, got: {result}"

        # Should not have time component
        assert 'T' not in result, \
            "Result should not have time component when timezone is invalid"

    def test_invalid_timezone_extremely_out_of_range(self, converter):
        """Test that extremely invalid timezone (9999 hours) reduces to date."""
        result = converter.convert_date("20150722230000-9999")

        assert result == "2015-07-22"
        assert 'T' not in result

    def test_invalid_timezone_minutes_out_of_range(self, converter):
        """Test that timezone with invalid minutes (99) reduces to date."""
        result = converter.convert_date("20150722230000-0599")

        assert result == "2015-07-22"
        assert 'T' not in result

    def test_valid_timezone_preserved(self, converter):
        """Test that valid timezone is preserved correctly."""
        result = converter.convert_date("20150722230000-0500")

        assert result == "2015-07-22T23:00:00-05:00"
        assert 'T' in result
        assert '-05:00' in result

    def test_edge_case_timezone_max_valid(self, converter):
        """Test maximum valid timezone offset (+14:00)."""
        result = converter.convert_date("20150722230000+1400")

        assert result == "2015-07-22T23:00:00+14:00"
        assert '+14:00' in result

    def test_edge_case_timezone_just_over_max(self, converter):
        """Test timezone just over maximum (15 hours) reduces to date."""
        result = converter.convert_date("20150722230000+1500")

        assert result == "2015-07-22"
        assert 'T' not in result

    def test_edge_case_timezone_hour_14_with_nonzero_minutes(self, converter):
        """Test hour 14 with non-zero minutes is invalid (only +14:00 allowed).

        FHIR R4 spec: Hour 14 only valid with minutes 00 (UTC+14:00 is max offset).
        Regression test for timezone validation bug allowing +14:01 through +14:59.
        """
        # +14:01 is invalid (only +14:00 allowed)
        result = converter.convert_date("20150722230000+1401")
        assert result == "2015-07-22"
        assert 'T' not in result

        # +14:30 is invalid
        result = converter.convert_date("20150722230000+1430")
        assert result == "2015-07-22"
        assert 'T' not in result

        # +14:59 is invalid
        result = converter.convert_date("20150722230000+1459")
        assert result == "2015-07-22"
        assert 'T' not in result


class TestFractionalSecondsHandling:
    """Regression tests for BUG-002B: Fractional seconds support.

    C-CDA allows fractional seconds but FHIR dateTime doesn't support them.
    Timestamps with fractional seconds should have fractions stripped and
    timestamp preserved.
    """

    @pytest.fixture
    def converter(self):
        """Create converter instance for testing."""
        return EncounterConverter()

    def test_fractional_seconds_with_timezone_preserved(self, converter):
        """Test that fractional seconds are preserved with timezone.

        Regression test for BUG-002B: "20170821112858.251-0500" previously
        returned None due to non-numeric check. Should preserve fractional
        seconds and timezone per FHIR R4 spec.
        """
        result = converter.convert_date("20170821112858.251-0500")

        assert result == "2017-08-21T11:28:58.251-05:00", \
            f"Expected fractional seconds preserved with timezone, got: {result}"

        # Should have fractional seconds and timezone
        assert '.251' in result
        assert '-05:00' in result

    def test_fractional_seconds_without_timezone_reduces_to_date(self, converter):
        """Test that fractional seconds without timezone reduces to date-only.

        When timestamp has fractional seconds but no timezone, should reduce
        to date-only per FHIR R4 requirement (time component requires timezone).
        """
        result = converter.convert_date("20170821112858.251")

        assert result == "2017-08-21", \
            f"Expected reduced to date-only (no timezone available), got: {result}"

        # Should not have time component (no timezone available)
        assert 'T' not in result

    def test_fractional_seconds_multiple_digits(self, converter):
        """Test fractional seconds with various precision levels.

        FHIR R4 supports fractional seconds with no upper limit on precision.
        """
        # 1 digit fractional
        result = converter.convert_date("20170821112858.2-0500")
        assert result == "2017-08-21T11:28:58.2-05:00"
        assert '.2' in result

        # 3 digits fractional (milliseconds)
        result = converter.convert_date("20170821112858.999-0500")
        assert result == "2017-08-21T11:28:58.999-05:00"
        assert '.999' in result

        # 6 digits fractional (microseconds)
        result = converter.convert_date("20170821112858.123456-0500")
        assert result == "2017-08-21T11:28:58.123456-05:00"
        assert '.123456' in result

    def test_fractional_seconds_with_invalid_timezone(self, converter):
        """Test fractional seconds combined with invalid timezone.

        Should strip fractions AND reduce to date-only due to invalid timezone.
        """
        result = converter.convert_date("20170821112858.251-9999")

        assert result == "2017-08-21"
        assert 'T' not in result


class TestCombinedScenarios:
    """Tests for combined edge cases and real-world scenarios."""

    @pytest.fixture
    def converter(self):
        """Create converter instance for testing."""
        return EncounterConverter()

    def test_normal_timestamp_without_timezone_still_reduces(self, converter):
        """Ensure existing behavior (no timezone -> date-only) still works."""
        result = converter.convert_date("20150722230000")

        assert result == "2015-07-22"
        assert 'T' not in result

    def test_date_only_unchanged(self, converter):
        """Test that date-only timestamps remain unchanged."""
        result = converter.convert_date("20150722")

        assert result == "2015-07-22"
        assert 'T' not in result

    def test_year_month_only_unchanged(self, converter):
        """Test that year-month only timestamps work correctly."""
        result = converter.convert_date("201507")

        assert result == "2015-07"
        assert 'T' not in result

    def test_full_valid_timestamp_with_timezone(self, converter):
        """Test complete valid timestamp with timezone works end-to-end."""
        result = converter.convert_date("20240115093045-0500")

        assert result == "2024-01-15T09:30:45-05:00"
        assert 'T' in result
        assert '-05:00' in result


class TestRealWorldExamples:
    """Tests based on actual problematic timestamps from stress test."""

    @pytest.fixture
    def converter(self):
        """Create converter instance for testing."""
        return EncounterConverter()

    def test_jeremy_bates_timestamp(self, converter):
        """Test timestamp pattern from Jeremy_Bates_health_summary.xml.

        This file had ValidationError showing input_value='2015-07-22T23:00:00'
        which violated FHIR requirement for timezone when time is present.
        """
        # Assuming the C-CDA had invalid timezone like -5000
        result = converter.convert_date("20150722230000-5000")

        # Should now reduce to date-only instead of returning time without timezone
        assert result == "2015-07-22"
        assert 'T' not in result, \
            "Should not have time component when timezone is invalid"

    def test_atg_timestamp_with_fractional_seconds(self, converter):
        """Test timestamp pattern from ATG files with fractional seconds.

        Files like SLI_CCD_b2Cecilia_ATG_ATGEHR_10162017.xml had warnings:
        "Invalid date format (non-numeric): 20170821112858.251-0500"

        Now correctly preserves fractional seconds per FHIR R4 spec.
        """
        result = converter.convert_date("20170821112858.251-0500")

        # Should now work correctly with fractional seconds preserved
        assert result is not None, "Should not return None for fractional seconds"
        assert result == "2017-08-21T11:28:58.251-05:00"
        assert '.251' in result
