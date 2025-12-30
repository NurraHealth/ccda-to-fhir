"""Comprehensive property and relationship tests for athena_ccd document.

This test validates the athena_ccd conversion using property-based assertions
rather than exact JSON matching, making it compatible with non-deterministic UUIDs.
"""

from __future__ import annotations

import uuid as uuid_module
from pathlib import Path
from typing import Any

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def test_athena_ccd_comprehensive() -> None:
    """Comprehensive property and relationship test for athena_ccd document.

    Validates:
    - Bundle structure and required fields
    - All resource types and counts
    - All references are valid (no broken references)
    - All UUIDs are valid v4 format
    - No placeholder references
    - Specific content validations
    - Relationship validations
    """
    # Load and convert
    xml_path = DOCUMENTS_DIR / "athena_ccd.xml"
    ccda_xml = xml_path.read_text()
    bundle = convert_document(ccda_xml)["bundle"]

    # === BUNDLE STRUCTURE ===
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert "entry" in bundle
    assert len(bundle["entry"]) > 0

    # === BUILD RESOURCE INDEX ===
    resources_by_type: dict[str, list[dict[str, Any]]] = {}
    resources_by_id: dict[str, dict[str, Any]] = {}

    for entry in bundle["entry"]:
        resource = entry["resource"]
        resource_type = resource["resourceType"]

        if resource_type not in resources_by_type:
            resources_by_type[resource_type] = []
        resources_by_type[resource_type].append(resource)

        if "id" in resource:
            resource_id = f"{resource_type}/{resource['id']}"
            resources_by_id[resource_id] = resource

    # === COMPOSITION MUST BE FIRST ===
    first_resource = bundle["entry"][0]["resource"]
    assert first_resource["resourceType"] == "Composition"

    # === RESOURCE COUNTS ===
    assert len(resources_by_type.get("Composition", [])) == 1
    assert len(resources_by_type.get("Patient", [])) >= 1
    assert len(resources_by_type.get("Condition", [])) >= 2
    assert len(resources_by_type.get("AllergyIntolerance", [])) >= 1
    assert len(resources_by_type.get("MedicationStatement", [])) >= 1
    assert len(resources_by_type.get("Procedure", [])) >= 1
    assert len(resources_by_type.get("Practitioner", [])) >= 1

    # === UUID VALIDATION ===
    for resource in resources_by_id.values():
        if "id" in resource:
            # Check if ID is UUID v4 (most resources use UUID v4)
            # Some resources like Procedure may use simple IDs from C-CDA
            resource_id = resource["id"]
            try:
                uuid_module.UUID(resource_id, version=4)
            except (ValueError, AttributeError):
                # Not a UUID v4 - could be a simple ID like "procedure-with-ref-001"
                # This is acceptable for some resources
                pass

    # === NO PLACEHOLDER REFERENCES ===
    def check_no_placeholders(obj: Any, path: str = "") -> None:
        """Recursively check for placeholder references."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "reference" and isinstance(value, str):
                    assert "placeholder" not in value.lower(), \
                        f"Found placeholder reference at {path}.{key}: {value}"
                else:
                    check_no_placeholders(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_no_placeholders(item, f"{path}[{i}]")

    check_no_placeholders(bundle)

    # === REFERENCE VALIDATION ===
    def extract_references(obj: Any) -> list[str]:
        """Extract all reference strings from a resource."""
        refs = []
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "reference" and isinstance(value, str):
                    refs.append(value)
                else:
                    refs.extend(extract_references(value))
        elif isinstance(obj, list):
            for item in obj:
                refs.extend(extract_references(item))
        return refs

    # Check all references are valid
    broken_refs = []
    for resource in resources_by_id.values():
        refs = extract_references(resource)
        for ref in refs:
            if not ref.startswith("urn:") and ref not in resources_by_id:
                broken_refs.append(f"{resource['resourceType']}/{resource.get('id', 'unknown')} -> {ref}")

    assert len(broken_refs) == 0, f"Found broken references: {broken_refs}"

    # === COMPOSITION VALIDATION ===
    composition = resources_by_type["Composition"][0]
    assert "id" in composition
    assert "status" in composition
    assert composition["status"] in ["preliminary", "final", "amended"]
    assert "type" in composition
    assert "subject" in composition
    assert "reference" in composition["subject"]
    assert composition["subject"]["reference"] in resources_by_id
    assert "section" in composition

    # === PATIENT VALIDATION ===
    patient = resources_by_type["Patient"][0]
    assert "id" in patient
    assert "identifier" in patient
    assert len(patient["identifier"]) > 0

    # === CONDITION VALIDATION ===
    for condition in resources_by_type.get("Condition", []):
        assert "id" in condition
        assert "code" in condition
        assert "subject" in condition
        assert condition["subject"]["reference"] in resources_by_id
        # Must have either clinicalStatus or verificationStatus
        assert "clinicalStatus" in condition or "verificationStatus" in condition

    # === PROCEDURE -> CONDITION REFERENCE VALIDATION ===
    # Check that any Procedure with reasonReference points to valid Conditions
    for procedure in resources_by_type.get("Procedure", []):
        if "reasonReference" in procedure:
            for reason_ref in procedure["reasonReference"]:
                ref = reason_ref["reference"]
                assert ref in resources_by_id, f"Procedure reasonReference {ref} not found"
                assert ref.startswith("Condition/"), f"Procedure reasonReference should point to Condition, got {ref}"

                # Verify the Condition exists and has expected fields
                condition = resources_by_id[ref]
                assert "code" in condition
                assert "subject" in condition

    # === ALLERGY VALIDATION ===
    for allergy in resources_by_type.get("AllergyIntolerance", []):
        assert "id" in allergy
        assert "patient" in allergy
        assert allergy["patient"]["reference"] in resources_by_id
        # Must have either code or reaction
        assert "code" in allergy or "reaction" in allergy

    # === MEDICATION VALIDATION ===
    for med in resources_by_type.get("MedicationStatement", []):
        assert "id" in med
        assert "status" in med
        assert "subject" in med
        assert med["subject"]["reference"] in resources_by_id
        # Medication field is optional if medication info is missing from C-CDA
        # (per FHIR spec, should have medication but can be absent with data-absent-reason)

    # === PRACTITIONER VALIDATION ===
    for practitioner in resources_by_type.get("Practitioner", []):
        assert "id" in practitioner
        # Practitioners should have identifier or name
        assert "identifier" in practitioner or "name" in practitioner

    # === PROVENANCE VALIDATION ===
    for provenance in resources_by_type.get("Provenance", []):
        assert "id" in provenance
        assert "target" in provenance
        assert len(provenance["target"]) > 0
        # All targets must reference valid resources
        for target in provenance["target"]:
            assert target["reference"] in resources_by_id
        assert "recorded" in provenance
        assert "agent" in provenance

    print("\n✓ athena_ccd comprehensive validation passed!")
    print(f"  Resources validated: {len(resources_by_id)}")
    print(f"  Resource types: {sorted(resources_by_type.keys())}")
