"""Reusable validators for temporal fields (date, dateTime, instant).

These validators ensure exact compliance with FHIR R4 temporal format
requirements per specification.
"""

import re
from typing import Optional


def assert_date_format(date_str: str, field_name: str = "date"):
    """Validate FHIR date format: YYYY, YYYY-MM, or YYYY-MM-DD.

    Per FHIR R4 spec, dates may have reduced precision.

    Args:
        date_str: Date string to validate
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#date
    """
    assert date_str is not None, f"{field_name} must not be None"

    # Pattern for FHIR date: YYYY, YYYY-MM, or YYYY-MM-DD
    date_pattern = r"^\d{4}(-\d{2}(-\d{2})?)?$"

    assert re.match(date_pattern, date_str), \
        f"{field_name} must be valid FHIR date format (YYYY, YYYY-MM, or YYYY-MM-DD), got '{date_str}'"


def assert_datetime_format(datetime_str: str, field_name: str = "dateTime"):
    """Validate FHIR dateTime format with timezone requirement.

    Per FHIR R4 spec: "If hours and minutes are specified, a time zone SHALL be populated"

    Valid formats:
    - YYYY
    - YYYY-MM
    - YYYY-MM-DD
    - YYYY-MM-DDThh:mm:ss+zz:zz (with timezone)
    - YYYY-MM-DDThh:mm:ss.sss+zz:zz (with milliseconds and timezone)

    Args:
        datetime_str: DateTime string to validate
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#dateTime
    """
    assert datetime_str is not None, f"{field_name} must not be None"

    # Pattern for FHIR dateTime with partial date support
    date_pattern = r"^\d{4}(-\d{2}(-\d{2})?)?$"
    # Pattern for dateTime with timezone (REQUIRED per spec if time present)
    datetime_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?[+-]\d{2}:\d{2}$"

    is_date = re.match(date_pattern, datetime_str)
    is_datetime = re.match(datetime_pattern, datetime_str)

    assert is_date or is_datetime, \
        f"{field_name} must be valid FHIR dateTime format, got '{datetime_str}'"

    # If it contains time, it MUST have timezone
    if "T" in datetime_str and not is_datetime:
        raise AssertionError(
            f"{field_name} has time component but missing timezone. "
            f"Per FHIR R4: 'If hours and minutes are specified, a time zone SHALL be populated'. "
            f"Got: '{datetime_str}'"
        )


def assert_instant_format(instant_str: str, field_name: str = "instant"):
    """Validate FHIR instant format (always requires timezone).

    instant is a precise point in time with mandatory timezone.

    Format: YYYY-MM-DDThh:mm:ss.sss+zz:zz

    Args:
        instant_str: Instant string to validate
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#instant
    """
    assert instant_str is not None, f"{field_name} must not be None"

    # Pattern for FHIR instant (always requires full precision + timezone)
    instant_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,3})?[+-]\d{2}:\d{2}$"

    assert re.match(instant_pattern, instant_str), \
        f"{field_name} must be valid FHIR instant format (YYYY-MM-DDThh:mm:ss.sss+zz:zz), got '{instant_str}'"


def assert_time_format(time_str: str, field_name: str = "time"):
    """Validate FHIR time format: hh:mm:ss.

    Args:
        time_str: Time string to validate
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#time
    """
    assert time_str is not None, f"{field_name} must not be None"

    # Pattern for FHIR time: hh:mm:ss
    time_pattern = r"^\d{2}:\d{2}:\d{2}(\.\d{1,3})?$"

    assert re.match(time_pattern, time_str), \
        f"{field_name} must be valid FHIR time format (hh:mm:ss), got '{time_str}'"


def assert_period_format(period, field_name: str = "Period"):
    """Validate FHIR Period structure with start/end dates.

    Args:
        period: FHIR Period object
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#Period
    """
    assert period is not None, f"{field_name} must not be None"

    # Validate start if present
    if period.start:
        assert_datetime_format(period.start, field_name=f"{field_name}.start")

    # Validate end if present
    if period.end:
        assert_datetime_format(period.end, field_name=f"{field_name}.end")

    # If both present, start should be before end
    if period.start and period.end:
        # Note: We don't enforce chronological order here since partial dates
        # make string comparison unreliable. Leave to FHIR validator.
        pass


def assert_timing_repeat_exact(
    repeat,
    expected_frequency: Optional[int] = None,
    expected_period: Optional[float] = None,
    expected_period_unit: Optional[str] = None,
    field_name: str = "Timing.repeat"
):
    """Validate Timing.repeat has exact frequency/period/periodUnit.

    Args:
        repeat: Timing.repeat object
        expected_frequency: Expected frequency value (optional)
        expected_period: Expected period value (optional)
        expected_period_unit: Expected periodUnit (optional, e.g., "d", "h", "wk")
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#Timing
    """
    assert repeat is not None, f"{field_name} must not be None"

    # Frequency validation
    if expected_frequency is not None:
        assert repeat.frequency == expected_frequency, \
            f"{field_name}.frequency must be {expected_frequency}, got {repeat.frequency}"
        assert isinstance(repeat.frequency, int), \
            f"{field_name}.frequency must be integer"

    # Period validation
    if expected_period is not None:
        assert repeat.period == expected_period, \
            f"{field_name}.period must be {expected_period}, got {repeat.period}"
        assert isinstance(repeat.period, (int, float)), \
            f"{field_name}.period must be numeric"

    # PeriodUnit validation
    if expected_period_unit is not None:
        assert repeat.periodUnit == expected_period_unit, \
            f"{field_name}.periodUnit must be '{expected_period_unit}', got '{repeat.periodUnit}'"

    # Validate periodUnit is valid UCUM temporal unit
    if repeat.periodUnit:
        valid_units = ["s", "min", "h", "d", "wk", "mo", "a"]
        assert repeat.periodUnit in valid_units, \
            f"{field_name}.periodUnit must be valid UCUM temporal unit, got '{repeat.periodUnit}'"


def assert_timing_event_format(timing, field_name: str = "Timing"):
    """Validate Timing.event has valid dateTime format.

    Args:
        timing: Timing object
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#Timing
    """
    assert timing is not None, f"{field_name} must not be None"

    if timing.event:
        for i, event in enumerate(timing.event):
            assert_datetime_format(event, field_name=f"{field_name}.event[{i}]")
