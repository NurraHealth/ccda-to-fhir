#!/usr/bin/env python3
"""Analyze stress test results and generate detailed report."""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List


def load_results(json_path: Path) -> Dict[str, Any]:
    """Load stress test results from JSON file."""
    with open(json_path) as f:
        return json.load(f)


def analyze_failed_files(report: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze patterns in failed files."""
    failed_files = report.get("failed_files", [])

    # Group by error type
    error_types = defaultdict(list)
    for failure in failed_files:
        error_type = failure.get("error_type", "Unknown")
        error_types[error_type].append(failure)

    # Analyze error messages for common patterns
    error_patterns = defaultdict(int)
    for failure in failed_files:
        error_msg = failure.get("error_message", "")

        # Common patterns
        if "no attribute" in error_msg:
            error_patterns["Missing attribute/method"] += 1
        elif "missing required field" in error_msg.lower() or "is required" in error_msg.lower():
            error_patterns["Missing required C-CDA field"] += 1
        elif "namespace" in error_msg.lower():
            error_patterns["XML namespace issue"] += 1
        elif "root element" in error_msg.lower():
            error_patterns["Document fragment (not full ClinicalDocument)"] += 1
        elif "validation error" in error_msg.lower():
            error_patterns["FHIR validation error"] += 1
        elif "code shall be" in error_msg.lower():
            error_patterns["C-CDA conformance validation"] += 1
        elif "cannot generate" in error_msg.lower() or "no valid identifiers" in error_msg.lower():
            error_patterns["Missing identifiers"] += 1
        elif "vaccineCode" in error_msg:
            error_patterns["Missing vaccine code"] += 1
        else:
            error_patterns["Other"] += 1

    return {
        "by_type": {k: len(v) for k, v in error_types.items()},
        "by_pattern": dict(error_patterns),
        "sample_errors": {
            error_type: [
                {
                    "file": f["file"],
                    "message": f["error_message"][:200]
                }
                for f in failures[:3]
            ]
            for error_type, failures in sorted(error_types.items(), key=lambda x: -len(x[1]))[:5]
        }
    }


def calculate_success_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate detailed success metrics."""
    summary = report["summary"]
    total = summary["total_files"]
    successful = summary["successful"]

    success_rate = (successful / total * 100) if total > 0 else 0

    return {
        "total_files_tested": total,
        "successful_conversions": successful,
        "failed_conversions": summary["failed"],
        "success_rate_pct": f"{success_rate:.2f}%",
        "avg_conversion_time_ms": summary["avg_conversion_time_ms"],
        "total_fhir_resources_created": summary["total_resources_created"],
    }


def generate_us_core_report(report: Dict[str, Any]) -> str:
    """Generate US Core compliance report."""
    us_core = report.get("us_core_compliance", {})
    patient = us_core.get("patient_completeness", {})
    condition = us_core.get("condition_compliance", {})
    allergy = us_core.get("allergy_compliance", {})
    observation = us_core.get("observation_compliance", {})

    total_successful = report["summary"]["successful"]

    report_lines = []
    report_lines.append("\n## US Core Profile Compliance\n")

    if total_successful == 0:
        report_lines.append("No successful conversions to analyze.\n")
        return "\n".join(report_lines)

    # Patient completeness
    report_lines.append("### Patient Resource (US Core Patient)")
    report_lines.append(f"- Documents with Patient: {patient.get('has_patient', 0)}/{total_successful}")
    if patient.get('has_patient', 0) > 0:
        report_lines.append(f"  - with name: {patient.get('has_name', 0)}/{patient.get('has_patient', 0)} ({patient.get('has_name', 0)/patient.get('has_patient', 1)*100:.1f}%)")
        report_lines.append(f"  - with identifier: {patient.get('has_identifier', 0)}/{patient.get('has_patient', 0)} ({patient.get('has_identifier', 0)/patient.get('has_patient', 1)*100:.1f}%)")
        report_lines.append(f"  - with gender: {patient.get('has_gender', 0)}/{patient.get('has_patient', 0)} ({patient.get('has_gender', 0)/patient.get('has_patient', 1)*100:.1f}%)")
        report_lines.append(f"  - with birthDate: {patient.get('has_birthdate', 0)}/{patient.get('has_patient', 0)} ({patient.get('has_birthdate', 0)/patient.get('has_patient', 1)*100:.1f}%)")

    # Condition compliance
    report_lines.append("\n### Condition Resources (US Core Condition)")
    report_lines.append(f"- with code: {condition.get('with_code', 0)}")
    report_lines.append(f"- with category: {condition.get('with_category', 0)}")
    report_lines.append(f"- with subject: {condition.get('with_subject', 0)}")

    # AllergyIntolerance compliance
    report_lines.append("\n### AllergyIntolerance Resources (US Core AllergyIntolerance)")
    report_lines.append(f"- with code: {allergy.get('with_code', 0)}")
    report_lines.append(f"- with patient: {allergy.get('with_patient', 0)}")
    report_lines.append(f"- with clinicalStatus: {allergy.get('with_clinical_status', 0)}")

    # Observation compliance
    report_lines.append("\n### Observation Resources (US Core Observation)")
    report_lines.append(f"- with code: {observation.get('with_code', 0)}")
    report_lines.append(f"- with status: {observation.get('with_status', 0)}")
    report_lines.append(f"- with category: {observation.get('with_category', 0)}")

    return "\n".join(report_lines)


def generate_ccda_fhir_report(report: Dict[str, Any]) -> str:
    """Generate CCDA on FHIR mapping report."""
    ccda_fhir = report.get("ccda_fhir_mapping", {})
    total_successful = report["summary"]["successful"]

    report_lines = []
    report_lines.append("\n## CCDA on FHIR Mapping Compliance\n")

    if total_successful == 0:
        report_lines.append("No successful conversions to analyze.\n")
        return "\n".join(report_lines)

    report_lines.append(f"- Composition resources created: {ccda_fhir.get('has_composition', 0)}/{total_successful}")
    report_lines.append(f"- Average sections per document: {ccda_fhir.get('avg_sections_per_doc', 0):.1f}")
    report_lines.append(f"- Provenance resources created: {ccda_fhir.get('total_provenance', 0)}")
    report_lines.append(f"- Documents with narrative text: {ccda_fhir.get('has_narrative', 0)}/{total_successful}")

    return "\n".join(report_lines)


def generate_markdown_report(report: Dict[str, Any], analysis: Dict[str, Any]) -> str:
    """Generate comprehensive markdown report."""
    lines = []

    lines.append("# C-CDA to FHIR Converter - Comprehensive Stress Test Report\n")
    lines.append(f"**Generated:** {Path.cwd()}\n")

    # Executive Summary
    lines.append("## Executive Summary\n")
    metrics = analysis["success_metrics"]
    lines.append(f"- **Total C-CDA Files Tested:** {metrics['total_files_tested']}")
    lines.append(f"- **Successful Conversions:** {metrics['successful_conversions']}")
    lines.append(f"- **Failed Conversions:** {metrics['failed_conversions']}")
    lines.append(f"- **Success Rate:** {metrics['success_rate_pct']}")
    lines.append(f"- **Total FHIR Resources Created:** {metrics['total_fhir_resources_created']}")
    lines.append(f"- **Average Conversion Time:** {metrics['avg_conversion_time_ms']}ms\n")

    # Resource Distribution
    if report["resource_distribution"]:
        lines.append("## FHIR Resource Distribution\n")
        resource_dist = sorted(report["resource_distribution"].items(), key=lambda x: -x[1])
        lines.append("| Resource Type | Count |")
        lines.append("|---------------|-------|")
        for resource_type, count in resource_dist:
            lines.append(f"| {resource_type} | {count} |")
        lines.append("")

    # Error Analysis
    lines.append("## Error Analysis\n")
    error_analysis = analysis["error_analysis"]

    lines.append("### Errors by Type\n")
    for error_type, count in sorted(error_analysis["by_type"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{error_type}**: {count} files")
    lines.append("")

    lines.append("### Errors by Pattern\n")
    for pattern, count in sorted(error_analysis["by_pattern"].items(), key=lambda x: -x[1]):
        lines.append(f"- **{pattern}**: {count} files")
    lines.append("")

    lines.append("### Sample Errors by Type\n")
    for error_type, samples in error_analysis["sample_errors"].items():
        lines.append(f"\n#### {error_type}\n")
        for sample in samples:
            lines.append(f"**File:** `{sample['file']}`")
            lines.append(f"**Error:** {sample['message']}\n")

    # US Core Compliance
    lines.append(generate_us_core_report(report))

    # CCDA on FHIR Mapping
    lines.append(generate_ccda_fhir_report(report))

    # Recommendations
    lines.append("\n## Recommendations\n")
    failed_count = metrics['failed_conversions']
    if failed_count > 0:
        lines.append(f"### Priority Fixes\n")
        top_errors = sorted(error_analysis["by_pattern"].items(), key=lambda x: -x[1])[:5]
        for i, (pattern, count) in enumerate(top_errors, 1):
            pct = (count / failed_count * 100)
            lines.append(f"{i}. **{pattern}** ({count} files, {pct:.1f}% of failures)")

    return "\n".join(lines)


def main():
    """Run analysis and generate report."""
    import argparse

    parser = argparse.ArgumentParser(description="Analyze stress test results")
    parser.add_argument("json_file", help="Path to stress test results JSON file")
    parser.add_argument("--output", "-o", help="Output markdown file (default: stdout)")
    args = parser.parse_args()

    # Load results
    json_path = Path(args.json_file)
    if not json_path.exists():
        print(f"Error: File not found: {json_path}", file=sys.stderr)
        return 1

    report = load_results(json_path)

    # Analyze
    analysis = {
        "success_metrics": calculate_success_metrics(report),
        "error_analysis": analyze_failed_files(report),
    }

    # Generate report
    markdown_report = generate_markdown_report(report, analysis)

    # Output
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(markdown_report)
        print(f"Report saved to: {output_path}")
    else:
        print(markdown_report)

    return 0


if __name__ == "__main__":
    sys.exit(main())
