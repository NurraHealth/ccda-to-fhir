"""Reusable validators for Quantity and Range structures.

These validators ensure exact compliance with FHIR R4 Quantity
requirements per C-CDA on FHIR IG.
"""

from typing import Optional


def assert_quantity_exact(
    quantity,
    expected_value: Optional[float] = None,
    expected_unit: Optional[str] = None,
    expected_system: str = "http://unitsofmeasure.org",
    expected_code: Optional[str] = None,
    field_name: str = "Quantity"
):
    """Validate Quantity has exact structure with UCUM units.

    Args:
        quantity: FHIR Quantity object
        expected_value: Expected numeric value (optional)
        expected_unit: Expected human-readable unit (optional, e.g., "mg")
        expected_system: Expected system (default: UCUM)
        expected_code: Expected UCUM code (optional, e.g., "mg")
        field_name: Name of field for error messages

    Standard Reference:
        http://unitsofmeasure.org (UCUM)
        https://hl7.org/fhir/R4/datatypes.html#Quantity
    """
    assert quantity is not None, f"{field_name} must not be None"

    # Value validation
    assert quantity.value is not None, f"{field_name}.value must not be None"
    if expected_value is not None:
        assert quantity.value == expected_value, \
            f"{field_name}.value must be {expected_value}, got {quantity.value}"

    # Unit validation
    if expected_unit is not None:
        assert quantity.unit == expected_unit, \
            f"{field_name}.unit must be '{expected_unit}', got '{quantity.unit}'"

    # System validation (should always be UCUM for FHIR)
    assert quantity.system == expected_system, \
        f"{field_name}.system must be '{expected_system}', got '{quantity.system}'"

    # Code validation (UCUM code)
    if expected_code is not None:
        assert quantity.code == expected_code, \
            f"{field_name}.code must be '{expected_code}', got '{quantity.code}'"


def assert_quantity_has_ucum(quantity, field_name: str = "Quantity", strict_system: bool = True):
    """Validate Quantity uses UCUM system when unit is present.

    Per FHIR R4 qty-3 constraint: system only required if code is present.
    Unitless quantities (no unit) may omit both system and code.

    Args:
        quantity: FHIR Quantity object
        field_name: Name of field for error messages
        strict_system: If True, require UCUM system when unit present. If False, only warn if missing.
    """
    assert quantity is not None, f"{field_name} must not be None"
    assert quantity.value is not None, f"{field_name}.value must not be None"

    # Check if quantity has a unit - if not, system and code can be omitted per FHIR spec
    has_unit = hasattr(quantity, 'unit') and quantity.unit is not None

    if strict_system:
        if has_unit:
            # If unit is present, require UCUM system and code
            assert quantity.system == "http://unitsofmeasure.org", \
                f"{field_name}.system must be UCUM when unit present, got '{quantity.system}'"
            assert quantity.code is not None, f"{field_name}.code must not be None when unit present"
        else:
            # No unit - system and code are optional per FHIR qty-3
            # If system is present without unit, it should still be UCUM
            if hasattr(quantity, 'system') and quantity.system is not None:
                assert quantity.system == "http://unitsofmeasure.org", \
                    f"{field_name}.system should be UCUM when present, got '{quantity.system}'"
    else:
        # Lenient mode: just check if system exists and is UCUM when present
        if hasattr(quantity, 'system') and quantity.system:
            assert quantity.system == "http://unitsofmeasure.org", \
                f"{field_name}.system should be UCUM when present, got '{quantity.system}'"


def assert_range_exact(
    range_obj,
    expected_low_value: Optional[float] = None,
    expected_high_value: Optional[float] = None,
    expected_unit: Optional[str] = None,
    field_name: str = "Range"
):
    """Validate Range has exact low/high Quantity structure.

    Args:
        range_obj: FHIR Range object
        expected_low_value: Expected low.value (optional)
        expected_high_value: Expected high.value (optional)
        expected_unit: Expected unit for both low and high (optional)
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#Range
    """
    assert range_obj is not None, f"{field_name} must not be None"

    # Low validation
    if range_obj.low:
        assert_quantity_has_ucum(range_obj.low, field_name=f"{field_name}.low")
        if expected_low_value is not None:
            assert range_obj.low.value == expected_low_value, \
                f"{field_name}.low.value must be {expected_low_value}"
        if expected_unit is not None:
            assert range_obj.low.unit == expected_unit, \
                f"{field_name}.low.unit must be '{expected_unit}'"

    # High validation
    if range_obj.high:
        assert_quantity_has_ucum(range_obj.high, field_name=f"{field_name}.high")
        if expected_high_value is not None:
            assert range_obj.high.value == expected_high_value, \
                f"{field_name}.high.value must be {expected_high_value}"
        if expected_unit is not None:
            assert range_obj.high.unit == expected_unit, \
                f"{field_name}.high.unit must be '{expected_unit}'"


def assert_reference_range_exact(
    reference_range,
    expected_low_value: Optional[float] = None,
    expected_high_value: Optional[float] = None,
    expected_unit: Optional[str] = None,
    field_name: str = "referenceRange"
):
    """Validate Observation.referenceRange has exact Quantity structure.

    Args:
        reference_range: Observation.referenceRange element
        expected_low_value: Expected low.value (optional)
        expected_high_value: Expected high.value (optional)
        expected_unit: Expected unit (optional)
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/observation-definitions.html#Observation.referenceRange
    """
    assert reference_range is not None, f"{field_name} must not be None"

    # Low validation
    if reference_range.low:
        assert_quantity_has_ucum(reference_range.low, field_name=f"{field_name}.low")
        if expected_low_value is not None:
            assert reference_range.low.value == expected_low_value
        if expected_unit is not None:
            assert reference_range.low.unit == expected_unit

    # High validation
    if reference_range.high:
        assert_quantity_has_ucum(reference_range.high, field_name=f"{field_name}.high")
        if expected_high_value is not None:
            assert reference_range.high.value == expected_high_value
        if expected_unit is not None:
            assert reference_range.high.unit == expected_unit

    # Type validation (should be "normal" per Known Issues doc)
    if reference_range.type:
        type_coding = reference_range.type.coding[0]
        assert type_coding.system == "http://terminology.hl7.org/CodeSystem/referencerange-meaning"
        assert type_coding.code == "normal", \
            f"Reference range type should be 'normal', got '{type_coding.code}'"


def assert_ratio_exact(
    ratio,
    expected_numerator_value: Optional[float] = None,
    expected_numerator_unit: Optional[str] = None,
    expected_denominator_value: Optional[float] = None,
    expected_denominator_unit: Optional[str] = None,
    field_name: str = "Ratio"
):
    """Validate Ratio has exact numerator/denominator Quantity structure.

    Used for maxDosePerPeriod validation.

    Args:
        ratio: FHIR Ratio object
        expected_numerator_value: Expected numerator.value (optional)
        expected_numerator_unit: Expected numerator.unit (optional)
        expected_denominator_value: Expected denominator.value (optional)
        expected_denominator_unit: Expected denominator.unit (optional)
        field_name: Name of field for error messages

    Standard Reference:
        https://hl7.org/fhir/R4/datatypes.html#Ratio
    """
    assert ratio is not None, f"{field_name} must not be None"

    # Numerator validation
    if ratio.numerator:
        assert_quantity_has_ucum(ratio.numerator, field_name=f"{field_name}.numerator")
        if expected_numerator_value is not None:
            assert ratio.numerator.value == expected_numerator_value
        if expected_numerator_unit is not None:
            assert ratio.numerator.unit == expected_numerator_unit

    # Denominator validation
    if ratio.denominator:
        assert_quantity_has_ucum(ratio.denominator, field_name=f"{field_name}.denominator")
        if expected_denominator_value is not None:
            assert ratio.denominator.value == expected_denominator_value
        if expected_denominator_unit is not None:
            assert ratio.denominator.unit == expected_denominator_unit
