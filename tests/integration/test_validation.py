"""Validation-based integration tests for C-CDA to FHIR conversion.

Instead of exact JSON matching, these tests validate that converted FHIR bundles
have correct properties and structure. This approach is more robust to implementation
changes and makes tests easier to understand.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document
from tests.integration.validation_helpers import (
    assert_all_references_resolve,
    assert_all_required_fields_present,
    assert_no_duplicate_section_references,
    assert_no_empty_codes,
    assert_no_placeholder_references,
    assert_valid_fhir_ids,
    count_resources_by_type,
    get_resource_summary,
)

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def test_athena_ccd_validation():
    """Validate athena CCD converts correctly using property-based assertions.

    This test validates behavior rather than exact output:
    - No broken references
    - Required fields present
    - No empty codes
    - Expected resource counts

    This approach is more maintainable than exact JSON matching.
    """
    # Load and convert
    xml_path = DOCUMENTS_DIR / "athena_ccd.xml"
    ccda_xml = xml_path.read_text()
    bundle = convert_document(ccda_xml)["bundle"]

    # Validate bundle structure
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert len(bundle["entry"]) > 0, "Bundle should contain resources"

    # Validate no placeholder references (bug #1)
    assert_no_placeholder_references(bundle)

    # Validate all references resolve
    assert_all_references_resolve(bundle)

    # Validate required fields present
    assert_all_required_fields_present(bundle)

    # Validate no empty codes
    assert_no_empty_codes(bundle)

    # Validate no duplicate section references
    assert_no_duplicate_section_references(bundle)

    # Validate FHIR ID compliance (max 64 chars, valid characters)
    assert_valid_fhir_ids(bundle)

    # Get resource summary for reporting
    summary = get_resource_summary(bundle)
    print(f"\nResource summary: {summary}")

    # Validate expected resource types exist
    assert summary.get("Composition") == 1, "Should have exactly one Composition"
    assert summary.get("Patient") >= 1, "Should have at least one Patient"

    # Validate we have clinical data (not just metadata)
    clinical_count = (
        summary.get("Condition", 0) +
        summary.get("AllergyIntolerance", 0) +
        summary.get("MedicationStatement", 0) +
        summary.get("Procedure", 0)
    )
    assert clinical_count > 0, "Should have clinical data"


def test_athena_ccd_critical_bugs_fixed():
    """Specifically test that the critical bugs from FIXES_NEEDED.md are fixed.

    This test explicitly checks for the three critical bugs:
    1. Patient placeholder references
    2. Missing procedure codes
    3. Invalid medication timing
    """
    # Load and convert
    xml_path = DOCUMENTS_DIR / "athena_ccd.xml"
    ccda_xml = xml_path.read_text()
    bundle = convert_document(ccda_xml)["bundle"]

    # Bug #1: Patient placeholder references
    placeholder_count = 0
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        # Check subject references
        if "subject" in resource:
            ref = resource["subject"].get("reference", "")
            if "placeholder" in ref.lower():
                placeholder_count += 1
        # Check patient references (AllergyIntolerance)
        if "patient" in resource:
            ref = resource["patient"].get("reference", "")
            if "placeholder" in ref.lower():
                placeholder_count += 1

    assert placeholder_count == 0, (
        f"Bug #1 NOT FIXED: Found {placeholder_count} placeholder reference(s)"
    )

    # Bug #2: Missing procedure codes
    empty_procedure_codes = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Procedure":
            code = resource.get("code")
            # Code must exist and not be empty
            if not code or code == {}:
                empty_procedure_codes.append(resource.get("id", "unknown"))
            # Code must have either coding or text
            elif not code.get("coding") and not code.get("text"):
                empty_procedure_codes.append(resource.get("id", "unknown"))

    assert len(empty_procedure_codes) == 0, (
        f"Bug #2 NOT FIXED: {len(empty_procedure_codes)} Procedure(s) with empty codes: "
        f"{empty_procedure_codes}"
    )

    # Bug #3: Invalid medication timing (absurdly large periods)
    invalid_timing = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "MedicationStatement":
            if "dosage" in resource:
                for dosage in resource["dosage"]:
                    timing = dosage.get("timing", {}).get("repeat", {})
                    period = timing.get("period")
                    period_unit = timing.get("periodUnit")

                    # Check for absurdly large periods
                    if period:
                        # More than 10 years in any unit is suspicious
                        if period_unit == "m" and period > 120:  # 10 years in months
                            invalid_timing.append(
                                f"{resource.get('id')}: {period} {period_unit}"
                            )
                        elif period_unit == "d" and period > 3650:  # 10 years in days
                            invalid_timing.append(
                                f"{resource.get('id')}: {period} {period_unit}"
                            )

    assert len(invalid_timing) == 0, (
        f"Bug #3 NOT FIXED: {len(invalid_timing)} medication(s) with invalid timing: "
        f"{invalid_timing}"
    )

    print("\n✓ All critical bugs verified as fixed!")


def test_athena_ccd_resource_counts():
    """Validate expected resource counts for athena CCD.

    This gives us confidence that we're extracting the major sections.
    Counts don't need to be exact (implementation may improve over time),
    but should be in the right ballpark.
    """
    xml_path = DOCUMENTS_DIR / "athena_ccd.xml"
    ccda_xml = xml_path.read_text()
    bundle = convert_document(ccda_xml)["bundle"]

    # Must have
    assert count_resources_by_type(bundle, "Composition") == 1
    assert count_resources_by_type(bundle, "Patient") >= 1

    # Should have (clinical data from athena CCD)
    assert count_resources_by_type(bundle, "Condition") >= 2, "Should have problems"
    assert count_resources_by_type(bundle, "AllergyIntolerance") >= 1, "Should have allergies"
    assert count_resources_by_type(bundle, "MedicationStatement") >= 1, "Should have medications"

    # May have (depends on what's in the document)
    procedures = count_resources_by_type(bundle, "Procedure")
    observations = count_resources_by_type(bundle, "Observation")

    print("\nResource counts:")
    print(f"  Conditions: {count_resources_by_type(bundle, 'Condition')}")
    print(f"  Allergies: {count_resources_by_type(bundle, 'AllergyIntolerance')}")
    print(f"  Medications: {count_resources_by_type(bundle, 'MedicationStatement')}")
    print(f"  Procedures: {procedures}")
    print(f"  Observations: {observations}")
