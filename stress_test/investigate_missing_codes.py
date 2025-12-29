"""Investigate why some Conditions and Allergies are missing codes."""

import json
from pathlib import Path

from ccda_to_fhir.convert import convert_document


def investigate_missing_codes():
    """Find examples of resources missing codes and analyze why."""

    print("=" * 80)
    print("INVESTIGATING MISSING CODES")
    print("=" * 80)

    # Analyze a few specific test files
    test_files = [
        "ccda-samples/Edaris Forerun/newman-rn.xml",
        "ccda-samples/Agastha/TransitionOfCare_CCD_R21_Sample1_Susan_Turner.xml",
        "ccda-samples/Equicare/Health Information Summary for Alice Newman [2016-09-07_10-58-56_154] (1).xml",
    ]

    base_dir = Path(__file__).parent

    for test_file_path in test_files:
        test_file = base_dir / test_file_path

        if not test_file.exists():
            continue

        print(f"\n{'─' * 80}")
        print(f"Analyzing: {test_file_path}")
        print(f"{'─' * 80}")

        xml_string = test_file.read_text()
        result = convert_document(xml_string)
        bundle_dict = result["bundle"]

        # Find Conditions without codes
        conditions_without_codes = []
        for entry in bundle_dict.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Condition":
                code = resource.get("code")
                if not code or (not code.get("coding") and not code.get("text")):
                    conditions_without_codes.append({
                        "id": resource.get("id"),
                        "code": code,
                        "clinicalStatus": resource.get("clinicalStatus"),
                        "verificationStatus": resource.get("verificationStatus"),
                        "category": resource.get("category"),
                    })

        # Find Allergies without codes
        allergies_without_codes = []
        for entry in bundle_dict.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "AllergyIntolerance":
                code = resource.get("code")
                if not code or (not code.get("coding") and not code.get("text")):
                    allergies_without_codes.append({
                        "id": resource.get("id"),
                        "code": code,
                        "clinicalStatus": resource.get("clinicalStatus"),
                        "verificationStatus": resource.get("verificationStatus"),
                        "type": resource.get("type"),
                    })

        if conditions_without_codes:
            print(f"\n  Conditions without codes: {len(conditions_without_codes)}")
            for i, cond in enumerate(conditions_without_codes[:3], 1):  # Show first 3
                print(f"\n    {i}. Condition ID: {cond['id']}")
                print(f"       code: {cond['code']}")
                print(f"       clinicalStatus: {cond['clinicalStatus']}")
                print(f"       category: {cond['category']}")

        if allergies_without_codes:
            print(f"\n  Allergies without codes: {len(allergies_without_codes)}")
            for i, allergy in enumerate(allergies_without_codes[:3], 1):
                print(f"\n    {i}. AllergyIntolerance ID: {allergy['id']}")
                print(f"       code: {allergy['code']}")
                print(f"       clinicalStatus: {allergy['clinicalStatus']}")
                print(f"       type: {allergy['type']}")

        # Check narrative coverage
        resources_by_type = {}
        narrative_by_type = {}

        for entry in bundle_dict.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")

            if resource_type in ["Condition", "AllergyIntolerance", "Observation",
                                "Procedure", "MedicationStatement", "MedicationRequest",
                                "DiagnosticReport", "Immunization"]:
                resources_by_type[resource_type] = resources_by_type.get(resource_type, 0) + 1

                text = resource.get("text")
                if text and text.get("div"):
                    narrative_by_type[resource_type] = narrative_by_type.get(resource_type, 0) + 1

        print(f"\n  Narrative Coverage:")
        for resource_type in sorted(resources_by_type.keys()):
            total = resources_by_type[resource_type]
            with_narrative = narrative_by_type.get(resource_type, 0)
            pct = (with_narrative / total * 100) if total > 0 else 0
            status = "✓" if pct > 0 else "✗"
            print(f"    {status} {resource_type:30s} {with_narrative:3d}/{total:3d} ({pct:5.1f}%)")


if __name__ == "__main__":
    investigate_missing_codes()
