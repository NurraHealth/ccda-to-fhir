"""Investigate missing Condition codes in detail.

Analyzes all 384 successful conversions to find Conditions without codes
and traces back to the C-CDA source to understand root cause.
"""

import json
from pathlib import Path
from collections import defaultdict
from lxml import etree

from ccda_to_fhir.convert import convert_document


def analyze_condition_codes():
    """Find all Conditions missing codes and analyze C-CDA source."""

    print("=" * 80)
    print("INVESTIGATING MISSING CONDITION CODES")
    print("=" * 80)

    # Load stress test results to get successful files
    results_file = Path(__file__).parent / "stress_test_results.json"

    if not results_file.exists():
        print(f"Error: {results_file} not found")
        return

    with open(results_file) as f:
        results = json.load(f)

    # Get list of correctly rejected files to exclude
    correctly_rejected_paths = {f["file"] for f in results.get("correctly_rejected_files", [])}

    # Find all XML files
    base_dir = Path(__file__).parent
    all_xml_files = []

    ccda_samples = base_dir / "ccda-samples"
    c_cda_examples = base_dir / "C-CDA-Examples"

    if ccda_samples.exists():
        all_xml_files.extend(ccda_samples.glob("**/*.xml"))
    if c_cda_examples.exists():
        all_xml_files.extend(c_cda_examples.glob("**/*.xml"))

    # Filter to successful conversions only
    successful_files = []
    for xml_file in all_xml_files:
        relative_path = str(xml_file.relative_to(base_dir))
        if relative_path not in correctly_rejected_paths:
            successful_files.append(xml_file)

    print(f"\nAnalyzing {len(successful_files)} successful conversions...")

    # Track all Conditions
    total_conditions = 0
    conditions_with_code = 0
    conditions_without_code = 0

    # Track files with missing codes
    files_with_missing_codes = []

    # Track root causes
    root_causes = defaultdict(int)

    # Analyze each file
    for i, xml_file in enumerate(successful_files, 1):
        if i % 50 == 0:
            print(f"  Processed {i}/{len(successful_files)}...")

        try:
            xml_string = xml_file.read_text()
            result = convert_document(xml_string)
            bundle_dict = result["bundle"]

            # Find Conditions in this bundle
            file_conditions = []
            for entry in bundle_dict.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Condition":
                    total_conditions += 1
                    code = resource.get("code")

                    if code and (code.get("coding") or code.get("text")):
                        conditions_with_code += 1
                    else:
                        conditions_without_code += 1
                        file_conditions.append({
                            "id": resource.get("id"),
                            "code": code,
                            "category": resource.get("category"),
                            "clinicalStatus": resource.get("clinicalStatus"),
                        })

            # If this file has Conditions without codes, analyze C-CDA source
            if file_conditions:
                files_with_missing_codes.append({
                    "file": str(xml_file.relative_to(base_dir)),
                    "conditions": file_conditions,
                    "xml": xml_string,
                })

        except Exception as e:
            # Skip files that fail to convert
            pass

    print(f"\n{'─' * 80}")
    print("SUMMARY")
    print(f"{'─' * 80}")
    print(f"Total Conditions: {total_conditions}")
    print(f"  With code:      {conditions_with_code} ({conditions_with_code/total_conditions*100:.1f}%)")
    print(f"  Without code:   {conditions_without_code} ({conditions_without_code/total_conditions*100:.1f}%)")
    print(f"\nFiles with missing Condition codes: {len(files_with_missing_codes)}")

    # Analyze C-CDA source for root causes
    print(f"\n{'─' * 80}")
    print("ROOT CAUSE ANALYSIS")
    print(f"{'─' * 80}")

    for file_info in files_with_missing_codes[:10]:  # Analyze first 10 files
        print(f"\n📄 {file_info['file']}")
        print(f"   Conditions without code: {len(file_info['conditions'])}")

        # Parse C-CDA XML
        try:
            root = etree.fromstring(file_info['xml'].encode('utf-8'))
            ns = {'cda': 'urn:hl7-org:v3'}

            # Find Problem Concern Acts (container for Problem Observations)
            concern_acts = root.xpath(
                "//cda:act[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.3']]",
                namespaces=ns
            )

            print(f"   Found {len(concern_acts)} Problem Concern Acts")

            # Analyze each Problem Observation
            for concern_act in concern_acts[:3]:  # First 3
                # Find Problem Observations within the Concern Act
                observations = concern_act.xpath(
                    ".//cda:observation[cda:templateId[@root='2.16.840.1.113883.10.20.22.4.4']]",
                    namespaces=ns
                )

                for obs in observations:
                    # Check if code element exists
                    code_elem = obs.find("cda:code", namespaces=ns)
                    value_elem = obs.find("cda:value", namespaces=ns)

                    if code_elem is not None:
                        # Code element exists - check if it has nullFlavor
                        null_flavor = code_elem.get("nullFlavor")
                        code_attr = code_elem.get("code")
                        display = code_elem.get("displayName")

                        if null_flavor:
                            print(f"   ⚠️  Problem Observation code has nullFlavor='{null_flavor}'")
                            root_causes["code_nullFlavor"] += 1
                        elif not code_attr:
                            print(f"   ⚠️  Problem Observation code element present but no @code attribute")
                            root_causes["code_no_attribute"] += 1
                        else:
                            print(f"   ✓  Problem Observation code: {code_attr} ({display})")

                    # Check value element (Problem Observation uses value for the problem code)
                    if value_elem is not None:
                        null_flavor = value_elem.get("nullFlavor")
                        code_attr = value_elem.get("code")
                        display = value_elem.get("displayName")
                        xsi_type = value_elem.get("{http://www.w3.org/2001/XMLSchema-instance}type")

                        if null_flavor:
                            print(f"   ⚠️  Problem Observation value has nullFlavor='{null_flavor}'")
                            root_causes["value_nullFlavor"] += 1
                        elif not code_attr:
                            print(f"   ⚠️  Problem Observation value element present but no @code attribute")
                            root_causes["value_no_attribute"] += 1
                        else:
                            print(f"   ✓  Problem Observation value: {code_attr} ({display}) [type={xsi_type}]")
                    else:
                        print(f"   ⚠️  Problem Observation missing value element")
                        root_causes["value_missing"] += 1

        except Exception as e:
            print(f"   ❌ Error analyzing C-CDA: {str(e)[:100]}")

    # Print root cause summary
    print(f"\n{'─' * 80}")
    print("ROOT CAUSE SUMMARY")
    print(f"{'─' * 80}")

    if root_causes:
        for cause, count in sorted(root_causes.items(), key=lambda x: -x[1]):
            print(f"  {cause:30s} {count:4d}")
    else:
        print("  No root causes identified in sample")

    # Save detailed results
    output_file = base_dir / "condition_codes_analysis.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": {
                "total_conditions": total_conditions,
                "with_code": conditions_with_code,
                "without_code": conditions_without_code,
                "files_with_missing_codes": len(files_with_missing_codes),
            },
            "root_causes": dict(root_causes),
            "files": [
                {
                    "file": f["file"],
                    "missing_count": len(f["conditions"]),
                }
                for f in files_with_missing_codes
            ],
        }, f, indent=2)

    print(f"\n✓ Detailed analysis saved to: {output_file.name}")
    print("=" * 80)


if __name__ == "__main__":
    analyze_condition_codes()
