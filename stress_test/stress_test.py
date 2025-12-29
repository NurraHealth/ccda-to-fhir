#!/usr/bin/env python3
"""
Comprehensive stress test for C-CDA to FHIR converter.
Tests conversion accuracy against US Core and CCDA on FHIR requirements.
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import traceback

# Add parent directory to path to import ccda_to_fhir
sys.path.insert(0, str(Path(__file__).parent.parent))

from ccda_to_fhir import convert_document
from ccda_to_fhir.exceptions import (
    InvalidCodeSystemError,
    InvalidValueError,
    CCDAConversionError,
)
from fhir.resources.bundle import Bundle
from fhir.resources.composition import Composition
from fhir.resources.patient import Patient
from fhir.resources.condition import Condition
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.immunization import Immunization
from fhir.resources.procedure import Procedure
from fhir.resources.observation import Observation
from fhir.resources.encounter import Encounter


@dataclass
class ConversionResult:
    """Result of converting a single C-CDA file."""
    file_path: str
    success: bool
    duration_ms: float
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    # Expected failure tracking
    expected_failure: bool = False
    expected_failure_reason: Optional[str] = None

    # FHIR Bundle metrics
    total_resources: int = 0
    resource_counts: Dict[str, int] = None

    # Validation metrics
    has_patient: bool = False
    has_composition: bool = False
    patient_has_name: bool = False
    patient_has_identifier: bool = False
    patient_has_gender: bool = False
    patient_has_birthdate: bool = False

    # US Core compliance checks
    conditions_have_code: int = 0
    conditions_have_category: int = 0
    conditions_have_subject: int = 0
    allergies_have_code: int = 0
    allergies_have_patient: int = 0
    allergies_have_clinical_status: int = 0
    observations_have_code: int = 0
    observations_have_status: int = 0
    observations_have_category: int = 0

    # CCDA on FHIR mapping checks
    composition_has_sections: int = 0
    provenance_resources: int = 0
    has_narrative_text: bool = False

    def __post_init__(self):
        if self.resource_counts is None:
            self.resource_counts = {}


class StressTestRunner:
    """Runs comprehensive stress tests on C-CDA to FHIR conversion."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.results: List[ConversionResult] = []
        self.skipped_fragments: List[Path] = []
        self.expected_failures = self._load_expected_failures()

    def _load_expected_failures(self) -> Dict[str, Any]:
        """Load expected failures configuration."""
        config_path = self.base_dir / "expected_failures.json"
        if not config_path.exists():
            return {"categories": {}}

        with open(config_path, 'r') as f:
            return json.load(f)

    def _is_expected_failure(self, file_path: Path, error_message: str) -> tuple[bool, Optional[str]]:
        """Check if a file is expected to fail with the given error.

        Returns:
            (is_expected, reason): Tuple of whether this is an expected failure and the reason
        """
        import re

        relative_path = str(file_path.relative_to(self.base_dir))

        # Check all categories
        for category_name, category in self.expected_failures.get("categories", {}).items():
            for expected in category.get("files", []):
                if expected["path"] == relative_path:
                    # Check if error message matches expected pattern (if provided)
                    if "expected_error_pattern" in expected:
                        pattern = expected["expected_error_pattern"]
                        if re.search(pattern, error_message, re.IGNORECASE):
                            return True, expected.get("reason", f"Expected failure: {category_name}")
                    else:
                        # No pattern specified, any error is expected
                        return True, expected.get("reason", f"Expected failure: {category_name}")

        return False, None

    def is_document_fragment(self, file_path: Path) -> bool:
        """Check if a file is a document fragment (not a full ClinicalDocument)."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Read entire file for small files, or just check beginning for large ones
                content = f.read()

            # First, do a simple text check for ClinicalDocument
            # This catches fragments even if they have namespace errors
            if '<ClinicalDocument' not in content:
                return True  # No ClinicalDocument tag = fragment

            # If it has ClinicalDocument tag, try to verify it's the root element
            import xml.etree.ElementTree as ET

            # Parse to get the root element
            try:
                root = ET.fromstring(content)
                # Check if root element is ClinicalDocument
                local_name = root.tag.split('}')[-1] if '}' in root.tag else root.tag
                return local_name != 'ClinicalDocument'
            except ET.ParseError:
                # Can't parse, but we saw <ClinicalDocument in content
                # Assume it's a complete document with XML errors
                return False

        except Exception:
            # If we can't determine, assume it's not a fragment
            return False

    def find_ccda_files(self, onc_only: bool = False, skip_fragments: bool = False) -> List[Path]:
        """Find all C-CDA XML files in the stress test directories."""
        ccda_files = []

        # Find files in ccda-samples (ONC certification)
        ccda_samples_dir = self.base_dir / "ccda-samples"
        if ccda_samples_dir.exists():
            ccda_files.extend(ccda_samples_dir.glob("**/*.xml"))

        # Find files in C-CDA-Examples (HL7 official) - many are fragments
        if not onc_only:
            hl7_examples_dir = self.base_dir / "C-CDA-Examples"
            if hl7_examples_dir.exists():
                ccda_files.extend(hl7_examples_dir.glob("**/*.xml"))

        # Filter out document fragments if requested
        if skip_fragments:
            filtered_files = []
            for file_path in ccda_files:
                if self.is_document_fragment(file_path):
                    self.skipped_fragments.append(file_path)
                else:
                    filtered_files.append(file_path)
            return sorted(filtered_files)

        return sorted(ccda_files)

    def validate_bundle(self, bundle: Bundle) -> Dict[str, Any]:
        """Validate FHIR Bundle against US Core and CCDA on FHIR requirements."""
        validation = {
            "has_patient": False,
            "has_composition": False,
            "patient_has_name": False,
            "patient_has_identifier": False,
            "patient_has_gender": False,
            "patient_has_birthdate": False,
            "conditions_have_code": 0,
            "conditions_have_category": 0,
            "conditions_have_subject": 0,
            "total_conditions": 0,
            "allergies_have_code": 0,
            "allergies_have_patient": 0,
            "allergies_have_clinical_status": 0,
            "total_allergies": 0,
            "observations_have_code": 0,
            "observations_have_status": 0,
            "observations_have_category": 0,
            "total_observations": 0,
            "composition_has_sections": 0,
            "provenance_resources": 0,
            "has_narrative_text": False,
        }

        if not bundle or not bundle.entry:
            return validation

        for entry in bundle.entry:
            resource = entry.resource
            resource_type = resource.get_resource_type()

            # Patient validation (US Core Patient profile)
            if resource_type == "Patient":
                validation["has_patient"] = True
                patient = resource
                if patient.name:
                    validation["patient_has_name"] = True
                if patient.identifier:
                    validation["patient_has_identifier"] = True
                if patient.gender:
                    validation["patient_has_gender"] = True
                if patient.birthDate:
                    validation["patient_has_birthdate"] = True

            # Composition validation (CCDA on FHIR)
            elif resource_type == "Composition":
                validation["has_composition"] = True
                composition = resource
                if composition.section:
                    validation["composition_has_sections"] = len(composition.section)
                if composition.text and composition.text.div:
                    validation["has_narrative_text"] = True

            # Condition validation (US Core Condition profile)
            elif resource_type == "Condition":
                validation["total_conditions"] += 1
                condition = resource
                if condition.code:
                    validation["conditions_have_code"] += 1
                if condition.category:
                    validation["conditions_have_category"] += 1
                if condition.subject:
                    validation["conditions_have_subject"] += 1

            # AllergyIntolerance validation (US Core AllergyIntolerance profile)
            elif resource_type == "AllergyIntolerance":
                validation["total_allergies"] += 1
                allergy = resource
                if allergy.code:
                    validation["allergies_have_code"] += 1
                if allergy.patient:
                    validation["allergies_have_patient"] += 1
                if allergy.clinicalStatus:
                    validation["allergies_have_clinical_status"] += 1

            # Observation validation (US Core Observation profiles)
            elif resource_type == "Observation":
                validation["total_observations"] += 1
                observation = resource
                if observation.code:
                    validation["observations_have_code"] += 1
                if observation.status:
                    validation["observations_have_status"] += 1
                if observation.category:
                    validation["observations_have_category"] += 1

            # Provenance tracking
            elif resource_type == "Provenance":
                validation["provenance_resources"] += 1

        return validation

    def convert_file(self, file_path: Path) -> ConversionResult:
        """Convert a single C-CDA file and validate the output."""
        start_time = time.time()

        try:
            # Read file and convert C-CDA to FHIR
            with open(file_path, 'r', encoding='utf-8') as f:
                ccda_xml = f.read()

            result_dict = convert_document(ccda_xml)
            duration_ms = (time.time() - start_time) * 1000

            # Extract bundle from ConversionResult
            bundle_dict = result_dict["bundle"]

            # Count resources by type
            resource_counts = defaultdict(int)
            total_resources = 0

            if bundle_dict and bundle_dict.get("entry"):
                for entry in bundle_dict["entry"]:
                    resource = entry["resource"]
                    resource_type = resource["resourceType"]
                    resource_counts[resource_type] += 1
                    total_resources += 1

            # Validate bundle - convert to Bundle object for validation
            bundle = Bundle(**bundle_dict)
            validation = self.validate_bundle(bundle)

            result = ConversionResult(
                file_path=str(file_path.relative_to(self.base_dir)),
                success=True,
                duration_ms=duration_ms,
                total_resources=total_resources,
                resource_counts=dict(resource_counts),
                has_patient=validation["has_patient"],
                has_composition=validation["has_composition"],
                patient_has_name=validation["patient_has_name"],
                patient_has_identifier=validation["patient_has_identifier"],
                patient_has_gender=validation["patient_has_gender"],
                patient_has_birthdate=validation["patient_has_birthdate"],
                conditions_have_code=validation["conditions_have_code"],
                conditions_have_category=validation["conditions_have_category"],
                conditions_have_subject=validation["conditions_have_subject"],
                allergies_have_code=validation["allergies_have_code"],
                allergies_have_patient=validation["allergies_have_patient"],
                allergies_have_clinical_status=validation["allergies_have_clinical_status"],
                observations_have_code=validation["observations_have_code"],
                observations_have_status=validation["observations_have_status"],
                observations_have_category=validation["observations_have_category"],
                composition_has_sections=validation["composition_has_sections"],
                provenance_resources=validation["provenance_resources"],
                has_narrative_text=validation["has_narrative_text"],
            )

            return result

        except InvalidCodeSystemError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"OID: {e.oid}"
            is_expected, reason = self._is_expected_failure(file_path, error_msg)
            return ConversionResult(
                file_path=str(file_path.relative_to(self.base_dir)),
                success=False,
                duration_ms=duration_ms,
                error_type="InvalidCodeSystem",
                error_message=error_msg,
                expected_failure=is_expected,
                expected_failure_reason=reason,
            )

        except InvalidValueError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = f"{e.field_name}: {e.value}"
            is_expected, reason = self._is_expected_failure(file_path, error_msg)
            return ConversionResult(
                file_path=str(file_path.relative_to(self.base_dir)),
                success=False,
                duration_ms=duration_ms,
                error_type="InvalidValue",
                error_message=error_msg,
                expected_failure=is_expected,
                expected_failure_reason=reason,
            )

        except CCDAConversionError as e:
            duration_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            is_expected, reason = self._is_expected_failure(file_path, error_msg)
            return ConversionResult(
                file_path=str(file_path.relative_to(self.base_dir)),
                success=False,
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=error_msg,
                expected_failure=is_expected,
                expected_failure_reason=reason,
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_trace = traceback.format_exc()
            error_msg = str(e)
            is_expected, reason = self._is_expected_failure(file_path, error_msg)
            return ConversionResult(
                file_path=str(file_path.relative_to(self.base_dir)),
                success=False,
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=error_msg,
                expected_failure=is_expected,
                expected_failure_reason=reason,
            )

    def run(self, limit: Optional[int] = None, onc_only: bool = False, skip_fragments: bool = False) -> Dict[str, Any]:
        """Run stress test on all C-CDA files."""
        ccda_files = self.find_ccda_files(onc_only=onc_only, skip_fragments=skip_fragments)

        if limit:
            ccda_files = ccda_files[:limit]

        print(f"\n{'='*80}")
        print(f"C-CDA to FHIR Converter - Comprehensive Stress Test")
        print(f"{'='*80}")
        print(f"Total files to process: {len(ccda_files)}")
        if skip_fragments and self.skipped_fragments:
            print(f"Skipped {len(self.skipped_fragments)} document fragments")
        print(f"{'='*80}\n")

        for i, file_path in enumerate(ccda_files, 1):
            print(f"[{i}/{len(ccda_files)}] Processing: {file_path.name}...", end=" ")
            result = self.convert_file(file_path)
            self.results.append(result)

            if result.success:
                print(f"✓ {result.duration_ms:.1f}ms - {result.total_resources} resources")
            elif result.expected_failure:
                print(f"✓ Correctly rejected: {result.expected_failure_reason}")
            else:
                print(f"✗ {result.error_type}: {result.error_message}")

        return self.generate_report()

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        expected_failures = sum(1 for r in self.results if not r.success and r.expected_failure)
        correctly_rejected = expected_failures  # Expected failures are correct rejections
        actual_failures = sum(1 for r in self.results if not r.success and not r.expected_failure)
        # Total success includes both successful conversions and correct rejections
        total_success = successful + correctly_rejected
        failed = actual_failures

        # Aggregate metrics
        total_resources = sum(r.total_resources for r in self.results if r.success)
        avg_duration = sum(r.duration_ms for r in self.results) / total if total > 0 else 0

        # Resource type distribution
        all_resource_counts = defaultdict(int)
        for result in self.results:
            if result.success and result.resource_counts:
                for resource_type, count in result.resource_counts.items():
                    all_resource_counts[resource_type] += count

        # Error type distribution
        error_distribution = defaultdict(int)
        for result in self.results:
            if not result.success and result.error_type:
                error_distribution[result.error_type] += 1

        # US Core compliance metrics
        successful_results = [r for r in self.results if r.success]
        us_core_compliance = {
            "patient_completeness": {
                "has_patient": sum(1 for r in successful_results if r.has_patient),
                "has_name": sum(1 for r in successful_results if r.patient_has_name),
                "has_identifier": sum(1 for r in successful_results if r.patient_has_identifier),
                "has_gender": sum(1 for r in successful_results if r.patient_has_gender),
                "has_birthdate": sum(1 for r in successful_results if r.patient_has_birthdate),
            },
            "condition_compliance": {
                "with_code": sum(r.conditions_have_code for r in successful_results),
                "with_category": sum(r.conditions_have_category for r in successful_results),
                "with_subject": sum(r.conditions_have_subject for r in successful_results),
            },
            "allergy_compliance": {
                "with_code": sum(r.allergies_have_code for r in successful_results),
                "with_patient": sum(r.allergies_have_patient for r in successful_results),
                "with_clinical_status": sum(r.allergies_have_clinical_status for r in successful_results),
            },
            "observation_compliance": {
                "with_code": sum(r.observations_have_code for r in successful_results),
                "with_status": sum(r.observations_have_status for r in successful_results),
                "with_category": sum(r.observations_have_category for r in successful_results),
            },
        }

        # CCDA on FHIR mapping metrics
        ccda_fhir_mapping = {
            "has_composition": sum(1 for r in successful_results if r.has_composition),
            "avg_sections_per_doc": sum(r.composition_has_sections for r in successful_results) / successful if successful > 0 else 0,
            "total_provenance": sum(r.provenance_resources for r in successful_results),
            "has_narrative": sum(1 for r in successful_results if r.has_narrative_text),
        }

        report = {
            "summary": {
                "total_files": total,
                "successful": successful,
                "correctly_rejected": correctly_rejected,
                "total_success": total_success,
                "failed": failed,
                "success_rate": f"{(total_success/total*100):.1f}%" if total > 0 else "0%",
                "conversion_rate": f"{(successful/total*100):.1f}%" if total > 0 else "0%",
                "total_resources_created": total_resources,
                "avg_conversion_time_ms": f"{avg_duration:.1f}",
            },
            "resource_distribution": dict(all_resource_counts),
            "error_distribution": dict(error_distribution),
            "us_core_compliance": us_core_compliance,
            "ccda_fhir_mapping": ccda_fhir_mapping,
            "correctly_rejected_files": [
                {
                    "file": r.file_path,
                    "reason": r.expected_failure_reason,
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                }
                for r in self.results if r.expected_failure
            ],
            "failed_files": [
                {
                    "file": r.file_path,
                    "error_type": r.error_type,
                    "error_message": r.error_message,
                }
                for r in self.results if not r.success and not r.expected_failure
            ],
        }

        return report


def main():
    """Run the stress test."""
    import argparse

    parser = argparse.ArgumentParser(description="Stress test C-CDA to FHIR converter")
    parser.add_argument("--limit", type=int, help="Limit number of files to process")
    parser.add_argument("--output", type=str, default="stress_test_results.json", help="Output JSON file")
    parser.add_argument("--onc-only", action="store_true", help="Only test ONC certification samples (skip HL7 fragments)")
    parser.add_argument("--skip-fragments", action="store_true", help="Skip document fragments (only process full ClinicalDocuments)")
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    runner = StressTestRunner(base_dir)

    report = runner.run(limit=args.limit, onc_only=args.onc_only, skip_fragments=args.skip_fragments)

    # Print summary
    print(f"\n{'='*80}")
    print("STRESS TEST RESULTS")
    print(f"{'='*80}")
    print(f"Total Files:          {report['summary']['total_files']}")
    print(f"Successful:           {report['summary']['successful']}")
    print(f"Correctly Rejected:   {report['summary']['correctly_rejected']} (spec violations)")
    print(f"Total Success:        {report['summary']['total_success']}")
    print(f"Failed:               {report['summary']['failed']}")
    print(f"Success Rate:         {report['summary']['success_rate']} (includes correct rejections)")
    print(f"Conversion Rate:      {report['summary']['conversion_rate']} (successful conversions only)")
    print(f"Total Resources:      {report['summary']['total_resources_created']}")
    print(f"Avg Conversion Time:  {report['summary']['avg_conversion_time_ms']}ms")
    print(f"\nResource Distribution:")
    for resource_type, count in sorted(report['resource_distribution'].items(), key=lambda x: -x[1]):
        print(f"  {resource_type:30s} {count:5d}")

    if report['error_distribution']:
        print(f"\nError Distribution:")
        for error_type, count in sorted(report['error_distribution'].items(), key=lambda x: -x[1]):
            print(f"  {error_type:30s} {count:5d}")

    print(f"\nUS Core Compliance:")
    print(f"  Patient Resources: {report['us_core_compliance']['patient_completeness']['has_patient']}")
    print(f"    - with name:       {report['us_core_compliance']['patient_completeness']['has_name']}")
    print(f"    - with identifier: {report['us_core_compliance']['patient_completeness']['has_identifier']}")
    print(f"    - with gender:     {report['us_core_compliance']['patient_completeness']['has_gender']}")
    print(f"    - with birthdate:  {report['us_core_compliance']['patient_completeness']['has_birthdate']}")

    print(f"\nCCDA on FHIR Mapping:")
    print(f"  Composition Resources: {report['ccda_fhir_mapping']['has_composition']}")
    print(f"  Avg Sections per Doc:  {report['ccda_fhir_mapping']['avg_sections_per_doc']:.1f}")
    print(f"  Provenance Resources:  {report['ccda_fhir_mapping']['total_provenance']}")
    print(f"  With Narrative Text:   {report['ccda_fhir_mapping']['has_narrative']}")

    print(f"\n{'='*80}")

    # Save detailed results to JSON
    output_path = base_dir / args.output
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Detailed results saved to: {output_path}")

    return 0 if report['summary']['failed'] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
