"""Analyze FHIR conversion quality for 384 successful conversions.

This script analyzes the quality of FHIR resources generated from C-CDA documents
to identify systematic issues and missing required fields.
"""

import json
from pathlib import Path
from collections import defaultdict

from ccda_to_fhir.convert import convert_document


def analyze_resource_quality(bundle_dict):
    """Analyze quality metrics for a single bundle.

    Returns:
        dict: Quality metrics for this bundle
    """
    metrics = {
        "total_resources": len(bundle_dict.get("entry", [])),
        "conditions": {
            "total": 0,
            "with_code": 0,
            "with_code_text": 0,
            "missing_code": [],
        },
        "allergies": {
            "total": 0,
            "with_code": 0,
            "with_code_text": 0,
            "missing_code": [],
        },
        "observations": {
            "total": 0,
            "with_category": 0,
            "missing_category": [],
        },
        "narrative": {
            "total_clinical_resources": 0,
            "with_text": 0,
            "resource_types_with_text": set(),
            "resource_types_without_text": set(),
        },
    }

    for entry in bundle_dict.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Check Condition quality
        if resource_type == "Condition":
            metrics["conditions"]["total"] += 1
            code = resource.get("code")

            if code:
                # Has code element
                if code.get("coding") or code.get("text"):
                    metrics["conditions"]["with_code"] += 1
                    if code.get("text"):
                        metrics["conditions"]["with_code_text"] += 1
                else:
                    # Empty code element
                    metrics["conditions"]["missing_code"].append(resource_id)
            else:
                # No code element at all
                metrics["conditions"]["missing_code"].append(resource_id)

        # Check AllergyIntolerance quality
        elif resource_type == "AllergyIntolerance":
            metrics["allergies"]["total"] += 1
            code = resource.get("code")

            if code:
                if code.get("coding") or code.get("text"):
                    metrics["allergies"]["with_code"] += 1
                    if code.get("text"):
                        metrics["allergies"]["with_code_text"] += 1
                else:
                    metrics["allergies"]["missing_code"].append(resource_id)
            else:
                metrics["allergies"]["missing_code"].append(resource_id)

        # Check Observation quality
        elif resource_type == "Observation":
            metrics["observations"]["total"] += 1
            category = resource.get("category")

            if category and len(category) > 0:
                metrics["observations"]["with_category"] += 1
            else:
                metrics["observations"]["missing_category"].append(resource_id)

        # Check narrative text presence
        if resource_type in ["Condition", "AllergyIntolerance", "Observation",
                            "Procedure", "MedicationStatement", "MedicationRequest",
                            "DiagnosticReport", "Immunization"]:
            metrics["narrative"]["total_clinical_resources"] += 1
            text = resource.get("text")

            if text and text.get("div"):
                metrics["narrative"]["with_text"] += 1
                metrics["narrative"]["resource_types_with_text"].add(resource_type)
            else:
                metrics["narrative"]["resource_types_without_text"].add(resource_type)

    return metrics


def aggregate_metrics(all_metrics):
    """Aggregate metrics across all bundles."""
    aggregated = {
        "total_bundles": len(all_metrics),
        "total_resources": sum(m["total_resources"] for m in all_metrics),
        "conditions": {
            "total": sum(m["conditions"]["total"] for m in all_metrics),
            "with_code": sum(m["conditions"]["with_code"] for m in all_metrics),
            "with_code_text": sum(m["conditions"]["with_code_text"] for m in all_metrics),
            "missing_code_count": sum(len(m["conditions"]["missing_code"]) for m in all_metrics),
        },
        "allergies": {
            "total": sum(m["allergies"]["total"] for m in all_metrics),
            "with_code": sum(m["allergies"]["with_code"] for m in all_metrics),
            "with_code_text": sum(m["allergies"]["with_code_text"] for m in all_metrics),
            "missing_code_count": sum(len(m["allergies"]["missing_code"]) for m in all_metrics),
        },
        "observations": {
            "total": sum(m["observations"]["total"] for m in all_metrics),
            "with_category": sum(m["observations"]["with_category"] for m in all_metrics),
            "missing_category_count": sum(len(m["observations"]["missing_category"]) for m in all_metrics),
        },
        "narrative": {
            "total_clinical_resources": sum(m["narrative"]["total_clinical_resources"] for m in all_metrics),
            "with_text": sum(m["narrative"]["with_text"] for m in all_metrics),
            "resource_types_with_text": set(),
            "resource_types_without_text": set(),
        },
    }

    # Merge resource type sets
    for m in all_metrics:
        aggregated["narrative"]["resource_types_with_text"].update(m["narrative"]["resource_types_with_text"])
        aggregated["narrative"]["resource_types_without_text"].update(m["narrative"]["resource_types_without_text"])

    return aggregated


def print_quality_report(aggregated):
    """Print formatted quality report."""
    print("\n" + "=" * 80)
    print("FHIR CONVERSION QUALITY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal Bundles Analyzed: {aggregated['total_bundles']}")
    print(f"Total Resources: {aggregated['total_resources']}")

    # Condition quality
    print(f"\n{'─' * 80}")
    print("CONDITION QUALITY")
    print(f"{'─' * 80}")
    cond = aggregated["conditions"]
    print(f"Total Conditions: {cond['total']}")
    if cond['total'] > 0:
        code_pct = (cond['with_code'] / cond['total']) * 100
        text_pct = (cond['with_code_text'] / cond['total']) * 100
        print(f"  With code:      {cond['with_code']:5d} ({code_pct:5.1f}%)")
        print(f"  With code.text: {cond['with_code_text']:5d} ({text_pct:5.1f}%)")
        print(f"  Missing code:   {cond['missing_code_count']:5d} ({100-code_pct:5.1f}%)")

    # Allergy quality
    print(f"\n{'─' * 80}")
    print("ALLERGY INTOLERANCE QUALITY")
    print(f"{'─' * 80}")
    allg = aggregated["allergies"]
    print(f"Total Allergies: {allg['total']}")
    if allg['total'] > 0:
        code_pct = (allg['with_code'] / allg['total']) * 100
        text_pct = (allg['with_code_text'] / allg['total']) * 100
        print(f"  With code:      {allg['with_code']:5d} ({code_pct:5.1f}%)")
        print(f"  With code.text: {allg['with_code_text']:5d} ({text_pct:5.1f}%)")
        print(f"  Missing code:   {allg['missing_code_count']:5d} ({100-code_pct:5.1f}%)")

    # Observation quality
    print(f"\n{'─' * 80}")
    print("OBSERVATION QUALITY")
    print(f"{'─' * 80}")
    obs = aggregated["observations"]
    print(f"Total Observations: {obs['total']}")
    if obs['total'] > 0:
        cat_pct = (obs['with_category'] / obs['total']) * 100
        print(f"  With category:  {obs['with_category']:5d} ({cat_pct:5.1f}%)")
        print(f"  Missing category: {obs['missing_category_count']:5d} ({100-cat_pct:5.1f}%)")

    # Narrative text quality
    print(f"\n{'─' * 80}")
    print("NARRATIVE TEXT QUALITY")
    print(f"{'─' * 80}")
    narr = aggregated["narrative"]
    print(f"Total Clinical Resources: {narr['total_clinical_resources']}")
    if narr['total_clinical_resources'] > 0:
        text_pct = (narr['with_text'] / narr['total_clinical_resources']) * 100
        print(f"  With text.div:  {narr['with_text']:5d} ({text_pct:5.1f}%)")
        print(f"  Missing text:   {narr['total_clinical_resources'] - narr['with_text']:5d} ({100-text_pct:5.1f}%)")

    print(f"\nResource types with narrative:")
    for rt in sorted(narr['resource_types_with_text']):
        print(f"  ✓ {rt}")

    print(f"\nResource types without narrative:")
    for rt in sorted(narr['resource_types_without_text'] - narr['resource_types_with_text']):
        print(f"  ✗ {rt}")

    print(f"\n{'=' * 80}\n")


def main():
    """Run quality analysis on all successful conversions."""
    # Load stress test results
    results_file = Path(__file__).parent / "stress_test_results.json"

    if not results_file.exists():
        print(f"Error: {results_file} not found")
        return

    with open(results_file) as f:
        results = json.load(f)

    # Get list of successful files
    successful_files = []
    base_dir = Path(__file__).parent

    # Load from results - files that are NOT in correctly_rejected or failed
    correctly_rejected_paths = {f["file"] for f in results.get("correctly_rejected_files", [])}

    # Find all XML files and filter to successful only
    ccda_samples = base_dir / "ccda-samples"
    c_cda_examples = base_dir / "C-CDA-Examples"

    all_xml_files = []
    if ccda_samples.exists():
        all_xml_files.extend(ccda_samples.glob("**/*.xml"))
    if c_cda_examples.exists():
        all_xml_files.extend(c_cda_examples.glob("**/*.xml"))

    # Filter to successful conversions
    for xml_file in all_xml_files:
        relative_path = str(xml_file.relative_to(base_dir))
        if relative_path not in correctly_rejected_paths:
            successful_files.append(xml_file)

    print(f"Analyzing {len(successful_files)} successful conversions...")

    # Analyze each successful conversion
    all_metrics = []
    errors = []

    for i, xml_file in enumerate(successful_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(successful_files)}...")

        try:
            xml_string = xml_file.read_text()
            result = convert_document(xml_string)
            bundle_dict = result["bundle"]

            metrics = analyze_resource_quality(bundle_dict)
            all_metrics.append(metrics)

        except Exception as e:
            errors.append({
                "file": str(xml_file.relative_to(base_dir)),
                "error": str(e)[:200]
            })

    # Aggregate and print results
    if all_metrics:
        aggregated = aggregate_metrics(all_metrics)
        print_quality_report(aggregated)

    # Print errors if any
    if errors:
        print(f"\n{'─' * 80}")
        print(f"ERRORS ({len(errors)} files)")
        print(f"{'─' * 80}")
        for error in errors[:10]:  # Limit to first 10
            print(f"  {error['file']}: {error['error']}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more errors")


if __name__ == "__main__":
    main()
