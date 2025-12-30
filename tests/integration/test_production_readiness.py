"""Production readiness tests using real C-CDA samples.

This test suite validates the C-CDA to FHIR converter against real EHR data
to ensure production readiness with comprehensive validation across 8 layers:

1. Basic Conversion & Bundle Structure
2. FHIR R4B Pydantic Validation
3. Reference Integrity
4. Clinical Data Quality
5. US Core Must Support
6. FHIR Invariants
7. Composition Sections
8. Comprehensive Reporting

Each real C-CDA sample is tested against all validation layers to ensure:
- Conversion accuracy
- FHIR R4B compliance
- US Core profile compliance
- C-CDA on FHIR IG mapping compliance
- Bundle and resource validity
- Reference integrity
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ccda_to_fhir.convert import RESOURCE_TYPE_MAPPING, convert_document
from tests.integration.validation_helpers import (
    assert_all_references_resolve,
    assert_all_required_fields_present,
    assert_chronological_dates,
    assert_composition_sections_valid,
    assert_fhir_invariants,
    assert_no_duplicate_section_references,
    assert_no_empty_codes,
    assert_no_placeholder_references,
    assert_references_point_to_correct_types,
    assert_us_core_must_support,
    assert_valid_code_systems,
    assert_valid_fhir_ids,
    get_resource_summary,
)

# Real C-CDA samples from certified EHR systems
REAL_SAMPLES = [
    "practice_fusion_alice_newman.xml",
    "practice_fusion_jeremy_bates.xml",
    "documents/athena_ccd.xml",
]


@pytest.fixture(params=REAL_SAMPLES, ids=lambda x: x.split("/")[-1])
def real_bundle(request):
    """Convert real C-CDA sample to FHIR Bundle.

    Args:
        request: Pytest request fixture with param containing sample file path

    Returns:
        FHIR Bundle dict with _test_metadata attached for reporting
    """
    sample_path = Path(__file__).parent / "fixtures" / request.param
    xml = sample_path.read_text()
    bundle = convert_document(xml)["bundle"]

    # Attach metadata for reporting
    bundle["_test_metadata"] = {
        "source_file": request.param,
        "source_size_kb": len(xml) / 1024,
    }

    return bundle


class TestLayer1_BasicStructure:
    """Layer 1: Document conversion and basic structure validation."""

    def test_real_sample_converts_successfully(self, real_bundle):
        """Verify real C-CDA converts to valid FHIR Bundle."""
        assert real_bundle["resourceType"] == "Bundle", "Must be a Bundle resource"
        assert real_bundle["type"] == "document", "Must be a document-type Bundle"
        assert len(real_bundle.get("entry", [])) > 0, "Bundle must have entries"

        # Composition must be first entry per FHIR document rules
        first_resource = real_bundle["entry"][0]["resource"]
        assert (
            first_resource["resourceType"] == "Composition"
        ), "First entry must be Composition"

        # Print resource summary for visibility
        summary = get_resource_summary(real_bundle)
        total_resources = len(real_bundle["entry"])

        print(f"\n  Resource Summary ({total_resources} total):")
        for resource_type in sorted(summary.keys()):
            print(f"    {resource_type}: {summary[resource_type]}")

    def test_bundle_has_identifier(self, real_bundle):
        """Verify Bundle has identifier."""
        assert "identifier" in real_bundle or "id" in real_bundle, (
            "Bundle should have identifier or id"
        )


class TestLayer2_PydanticValidation:
    """Layer 2: FHIR R4B Pydantic model validation."""

    def test_all_resources_validate_against_pydantic_models(self, real_bundle):
        """Validate all resources against fhir.resources R4B models.

        This test ensures every resource in the bundle conforms to the
        FHIR R4B specification by instantiating Pydantic models.
        """
        stats = {"total": 0, "passed": 0, "failed": 0, "errors": []}

        for entry in real_bundle["entry"]:
            resource = entry["resource"]
            resource_type = resource["resourceType"]
            resource_id = resource.get("id", "unknown")

            if resource_type not in RESOURCE_TYPE_MAPPING:
                stats["errors"].append({
                    "type": resource_type,
                    "id": resource_id,
                    "error": f"Unknown resource type: {resource_type}",
                })
                stats["failed"] += 1
                stats["total"] += 1
                continue

            resource_class = RESOURCE_TYPE_MAPPING[resource_type]

            try:
                # Attempt to instantiate Pydantic model
                validated = resource_class(**resource)
                stats["passed"] += 1
            except Exception as e:
                stats["failed"] += 1
                error_msg = str(e)
                # Truncate very long error messages
                if len(error_msg) > 500:
                    error_msg = error_msg[:497] + "..."

                stats["errors"].append({
                    "type": resource_type,
                    "id": resource_id,
                    "error": error_msg,
                })

            stats["total"] += 1

        # Print validation report
        print(f"\n  Pydantic Validation: {stats['passed']}/{stats['total']} passed")
        if stats["failed"] > 0:
            print(f"  Failures ({stats['failed']}):")
            for error in stats["errors"]:
                if isinstance(error, dict):
                    print(f"    - {error['type']}/{error['id']}: {error['error'][:200]}")
                else:
                    print(f"    - {str(error)[:200]}")

        assert stats["failed"] == 0, (
            f"Pydantic validation failures: {stats['failed']}/{stats['total']} failed\n"
            f"First error: {stats['errors'][0] if stats['errors'] else 'None'}"
        )


class TestLayer3_ReferenceIntegrity:
    """Layer 3: Reference integrity validation."""

    def test_no_placeholder_references(self, real_bundle):
        """Verify no placeholder references exist.

        Placeholder references like 'Patient/placeholder' indicate bugs
        in the reference registry or ID generation.
        """
        assert_no_placeholder_references(real_bundle)

    def test_all_references_resolve(self, real_bundle):
        """Verify all references point to resources in bundle.

        All references must resolve to actual resources in the bundle
        to maintain referential integrity.
        """
        assert_all_references_resolve(real_bundle)

    def test_valid_fhir_ids(self, real_bundle):
        """Verify all resource IDs comply with FHIR spec.

        Per FHIR R4: IDs must be max 64 chars and match [A-Za-z0-9\\-\\.]+
        """
        assert_valid_fhir_ids(real_bundle)

    def test_references_point_to_correct_types(self, real_bundle):
        """Verify references point to correct resource types.

        For example, Condition.subject must reference Patient or Group,
        not Practitioner.
        """
        assert_references_point_to_correct_types(real_bundle)


class TestLayer4_ClinicalDataQuality:
    """Layer 4: Clinical data quality validation."""

    def test_no_empty_codes(self, real_bundle):
        """Verify clinical resources have proper codes.

        Condition, AllergyIntolerance, Procedure, etc. must have codes
        with either coding arrays or text.
        """
        assert_no_empty_codes(real_bundle)

    def test_all_required_fields_present(self, real_bundle):
        """Verify critical FHIR fields are present.

        Check required fields like Patient.id, Condition.subject, etc.
        """
        assert_all_required_fields_present(real_bundle)

    def test_valid_code_systems(self, real_bundle):
        """Verify code systems are valid URIs, not unmapped OIDs.

        All code.system values should be canonical URIs like
        http://loinc.org, not OIDs like urn:oid:2.16.840...
        """
        assert_valid_code_systems(real_bundle)

    def test_chronological_dates(self, real_bundle):
        """Verify dates are chronologically consistent.

        Checks:
        - onset <= abatement (Condition)
        - whenPrepared <= whenHandedOver (MedicationDispense)
        - No future dates in completed status
        """
        assert_chronological_dates(real_bundle)


class TestLayer5_USCoreCompliance:
    """Layer 5: US Core Must Support validation."""

    def test_us_core_must_support_elements(self, real_bundle):
        """Verify US Core Must Support elements are populated.

        Per US Core: "Must be supported if the data is present in the
        sending system"

        Checks key Must Support elements for:
        - Patient
        - Condition
        - AllergyIntolerance
        - MedicationRequest
        - MedicationDispense
        - Observation
        - Procedure
        """
        assert_us_core_must_support(real_bundle)


class TestLayer6_FHIRInvariants:
    """Layer 6: FHIR invariant validation."""

    def test_fhir_invariants_satisfied(self, real_bundle):
        """Verify FHIR business rule invariants are satisfied.

        Checks key invariants:
        - obs-6: Observation must have value[x] OR dataAbsentReason OR component
        - obs-7: Observation.component must have value[x] OR dataAbsentReason
        - con-3: entered-in-error should not have clinicalStatus
        """
        assert_fhir_invariants(real_bundle)


class TestLayer7_CompositionSections:
    """Layer 7: Composition section validation."""

    def test_no_duplicate_section_references(self, real_bundle):
        """Verify Composition sections have no duplicate references.

        Each resource should appear once in section entries per FHIR spec.
        """
        assert_no_duplicate_section_references(real_bundle)

    def test_composition_sections_reference_correct_types(self, real_bundle):
        """Verify Composition sections reference correct resource types.

        Checks:
        - Problems section (11450-4) → Condition
        - Allergies section (48765-2) → AllergyIntolerance
        - Medications section (10160-0) → MedicationStatement/MedicationRequest
        - etc.
        """
        assert_composition_sections_valid(real_bundle)


class TestComprehensiveReport:
    """Generate comprehensive validation report for production readiness assessment."""

    def test_comprehensive_validation_report(self, real_bundle):
        """Run all validations and generate detailed report.

        This test runs all validation layers and generates a comprehensive
        report showing:
        - Source file information
        - Resource counts by type
        - Validation pass/fail status for each layer
        - Overall production readiness assessment
        """
        metadata = real_bundle.get("_test_metadata", {})
        source_file = metadata.get("source_file", "unknown")
        source_size_kb = metadata.get("source_size_kb", 0)

        report = {
            "source": source_file,
            "source_size_kb": source_size_kb,
            "total_resources": len(real_bundle.get("entry", [])),
            "resource_summary": get_resource_summary(real_bundle),
            "validations": {},
        }

        # Run all validation layers
        validations = [
            ("Layer 1: No placeholder references", lambda: assert_no_placeholder_references(real_bundle)),
            ("Layer 1: All references resolve", lambda: assert_all_references_resolve(real_bundle)),
            ("Layer 1: Valid FHIR IDs", lambda: assert_valid_fhir_ids(real_bundle)),
            ("Layer 1: References point to correct types", lambda: assert_references_point_to_correct_types(real_bundle)),
            ("Layer 2: No empty codes", lambda: assert_no_empty_codes(real_bundle)),
            ("Layer 2: Required fields present", lambda: assert_all_required_fields_present(real_bundle)),
            ("Layer 2: Valid code systems", lambda: assert_valid_code_systems(real_bundle)),
            ("Layer 2: Chronological dates", lambda: assert_chronological_dates(real_bundle)),
            ("Layer 3: US Core Must Support", lambda: assert_us_core_must_support(real_bundle)),
            ("Layer 4: FHIR invariants", lambda: assert_fhir_invariants(real_bundle)),
            ("Layer 5: No duplicate section refs", lambda: assert_no_duplicate_section_references(real_bundle)),
            ("Layer 5: Composition sections valid", lambda: assert_composition_sections_valid(real_bundle)),
        ]

        for check_name, check_func in validations:
            try:
                check_func()
                report["validations"][check_name] = "PASS"
            except AssertionError as e:
                error_msg = str(e)
                # Truncate very long error messages
                if len(error_msg) > 300:
                    error_msg = error_msg[:297] + "..."
                report["validations"][check_name] = f"FAIL: {error_msg}"

        # Pydantic validation (special handling for detailed stats)
        pydantic_passed = 0
        pydantic_total = 0
        pydantic_errors = []

        for entry in real_bundle["entry"]:
            resource = entry["resource"]
            resource_type = resource["resourceType"]

            if resource_type in RESOURCE_TYPE_MAPPING:
                resource_class = RESOURCE_TYPE_MAPPING[resource_type]
                try:
                    validated = resource_class(**resource)
                    pydantic_passed += 1
                except Exception:
                    pydantic_errors.append(f"{resource_type}/{resource.get('id', '?')}")

                pydantic_total += 1

        if pydantic_total > 0:
            pydantic_rate = (pydantic_passed / pydantic_total) * 100
            if pydantic_passed == pydantic_total:
                report["validations"]["Layer 0: Pydantic R4B validation"] = f"PASS ({pydantic_passed}/{pydantic_total})"
            else:
                report["validations"]["Layer 0: Pydantic R4B validation"] = (
                    f"FAIL ({pydantic_passed}/{pydantic_total} = {pydantic_rate:.1f}%) - "
                    f"Failed: {', '.join(pydantic_errors[:5])}"
                    + ("..." if len(pydantic_errors) > 5 else "")
                )

        # Print formatted report
        print(f"\n{'=' * 80}")
        print("PRODUCTION READINESS REPORT")
        print(f"{'=' * 80}")
        print(f"Source: {source_file}")
        print(f"Size: {source_size_kb:.1f} KB")
        print(f"Total Resources: {report['total_resources']}")
        print("\nResource Summary:")

        for resource_type in sorted(report["resource_summary"].keys()):
            count = report["resource_summary"][resource_type]
            print(f"  {resource_type:30s} {count:4d}")

        print("\nValidation Results:")

        passed_count = sum(1 for v in report["validations"].values() if v == "PASS" or v.startswith("PASS"))
        total_count = len(report["validations"])

        for check, result in sorted(report["validations"].items()):
            is_pass = result == "PASS" or result.startswith("PASS")
            status = "✓" if is_pass else "✗"
            print(f"  {status} {check:45s} {result}")

        print(f"\nOverall: {passed_count}/{total_count} validation layers passed")

        # Overall assessment
        if passed_count == total_count:
            print(f"\n{'✓' * 40}")
            print("PRODUCTION READY")
            print(f"{'✓' * 40}")
        else:
            print(f"\n{'✗' * 40}")
            print("NOT PRODUCTION READY - Issues found")
            print(f"{'✗' * 40}")

        print(f"{'=' * 80}\n")

        # All validations must pass for production readiness
        failures = [k for k, v in report["validations"].items() if not (v == "PASS" or v.startswith("PASS"))]
        assert not failures, (
            f"Production readiness validation failures ({len(failures)}/{total_count}):\n" +
            "\n".join(f"  - {f}: {report['validations'][f]}" for f in failures)
        )
