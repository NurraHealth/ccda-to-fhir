#!/usr/bin/env python3
"""Filter out document fragments and namespace issues to see real conversion rate."""

import json
from pathlib import Path
from collections import defaultdict

def analyze_real_issues():
    """Analyze issues excluding fragments and namespace problems."""

    with open("stress_test_all_samples.json") as f:
        data = json.load(f)

    failed_files = data["failed_files"]

    # Filter out non-issues
    real_issues = []
    excluded = {
        "fragments": 0,
        "namespace": 0,
        "other_xml": 0
    }

    for failure in failed_files:
        error_msg = failure["error_message"].lower()

        # Exclude document fragments
        if "root element must be 'clinicaldocument'" in error_msg:
            excluded["fragments"] += 1
            continue

        # Exclude namespace issues
        if "namespace prefix xsi" in error_msg:
            excluded["namespace"] += 1
            continue

        # Exclude other XML syntax issues that aren't our problem
        if "invalid xml syntax" in error_msg and "namespace" not in error_msg:
            excluded["other_xml"] += 1
            continue

        real_issues.append(failure)

    # Categorize real issues
    categories = defaultdict(list)

    for issue in real_issues:
        error_type = issue["error_type"]
        error_msg = issue["error_message"]

        # Categorize by solvability
        if "no attribute" in error_msg.lower():
            categories["BUGS - Missing methods/attributes"].append(issue)
        elif "location name is required" in error_msg.lower():
            categories["DESIGN - Missing Location names"].append(issue)
        elif "cannot generate" in error_msg.lower() or "no valid identifiers" in error_msg.lower():
            categories["DESIGN - Missing identifiers"].append(issue)
        elif "is required" in error_msg.lower() and "field" in error_msg.lower():
            categories["DESIGN - Missing required fields"].append(issue)
        elif "vaccinecode" in error_msg.lower():
            categories["DESIGN - Missing vaccine codes"].append(issue)
        elif "unknown xsi:type" in error_msg.lower():
            categories["FEATURE - Unsupported data types"].append(issue)
        elif "code shall be" in error_msg.lower() or "value shall be" in error_msg.lower():
            categories["DATA - C-CDA conformance violations"].append(issue)
        elif "validation error" in error_msg.lower() and "bundle" in error_msg.lower():
            categories["BUGS - FHIR validation errors"].append(issue)
        elif error_type == "MalformedXMLError":
            categories["DATA - Malformed C-CDA"].append(issue)
        else:
            categories["OTHER - Need investigation"].append(issue)

    # Print analysis
    total_files = data["summary"]["total_files"]
    total_excluded = sum(excluded.values())
    real_issue_count = len(real_issues)

    print("\n" + "="*80)
    print("REAL ISSUES ANALYSIS (Excluding Fragments & Namespace Problems)")
    print("="*80)
    print(f"\nTotal files tested: {total_files}")
    print(f"Excluded (not real issues): {total_excluded}")
    print(f"  - Document fragments: {excluded['fragments']}")
    print(f"  - Namespace issues: {excluded['namespace']}")
    print(f"  - Other XML syntax: {excluded['other_xml']}")
    print(f"\nReal issues to analyze: {real_issue_count}")
    print(f"Potential success if fixed: {((total_files - real_issue_count) / total_files * 100):.1f}%")

    print("\n" + "="*80)
    print("ISSUE CATEGORIES BY SOLVABILITY")
    print("="*80)

    # Sort by count
    sorted_categories = sorted(categories.items(), key=lambda x: -len(x[1]))

    for category, issues in sorted_categories:
        print(f"\n{category}: {len(issues)} files")

        # Determine solvability
        if "BUGS" in category:
            print("  Solvability: ✅ HIGH - These are bugs that should be fixed")
        elif "FEATURE" in category:
            print("  Solvability: ✅ MEDIUM - Need to implement missing data types")
        elif "DESIGN" in category:
            print("  Solvability: ⚠️  DESIGN CHOICE - Fail loud vs graceful degradation")
        elif "DATA" in category:
            print("  Solvability: ⚠️  DATA QUALITY - Invalid/non-conformant C-CDA input")
        else:
            print("  Solvability: ❓ UNKNOWN - Needs investigation")

        # Show sample errors
        print("  Sample errors:")
        for issue in issues[:3]:
            filename = Path(issue["file"]).name
            error = issue["error_message"][:120]
            print(f"    - {filename}")
            print(f"      {error}")

    # Solvability summary
    print("\n" + "="*80)
    print("SOLVABILITY SUMMARY")
    print("="*80)

    bugs = sum(len(issues) for cat, issues in categories.items() if "BUGS" in cat)
    features = sum(len(issues) for cat, issues in categories.items() if "FEATURE" in cat)
    design = sum(len(issues) for cat, issues in categories.items() if "DESIGN" in cat)
    data = sum(len(issues) for cat, issues in categories.items() if "DATA" in cat)
    other = sum(len(issues) for cat, issues in categories.items() if "OTHER" in cat)

    print(f"\n✅ HIGH PRIORITY (Should Fix):")
    print(f"   - Bugs: {bugs} files")
    print(f"   - Missing features: {features} files")
    print(f"   Total: {bugs + features} files ({(bugs + features)/real_issue_count*100:.1f}% of real issues)")

    print(f"\n⚠️  DESIGN DECISIONS:")
    print(f"   - Missing required fields: {design} files")
    print(f"   ({(design)/real_issue_count*100:.1f}% of real issues)")
    print(f"   Question: Should converter gracefully handle missing optional fields?")

    print(f"\n⚠️  DATA QUALITY ISSUES:")
    print(f"   - Non-conformant C-CDA: {data} files")
    print(f"   ({(data)/real_issue_count*100:.1f}% of real issues)")
    print(f"   Note: These violate C-CDA spec - may be acceptable to reject")

    if other > 0:
        print(f"\n❓ NEEDS INVESTIGATION:")
        print(f"   - Other issues: {other} files")

    print("\n" + "="*80)

    # Calculate realistic success rate scenarios
    print("\nREALISTIC SUCCESS RATE PROJECTIONS")
    print("="*80)

    scenario1 = total_files - total_excluded - bugs - features
    scenario1_pct = scenario1 / total_files * 100
    print(f"\nScenario 1: Fix all bugs & add missing features")
    print(f"  Potential success: {scenario1}/{total_files} ({scenario1_pct:.1f}%)")

    scenario2 = total_files - total_excluded - bugs - features - design
    scenario2_pct = scenario2 / total_files * 100
    print(f"\nScenario 2: + Allow optional fields to be missing")
    print(f"  Potential success: {scenario2}/{total_files} ({scenario2_pct:.1f}%)")

    scenario3 = total_files - total_excluded
    scenario3_pct = scenario3 / total_files * 100
    print(f"\nScenario 3: + Accept non-conformant C-CDA (lenient mode)")
    print(f"  Potential success: {scenario3}/{total_files} ({scenario3_pct:.1f}%)")

    print("\n" + "="*80)

if __name__ == "__main__":
    analyze_real_issues()
