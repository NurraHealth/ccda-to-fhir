"""Validation helpers for testing FHIR bundle conversion correctness.

Instead of exact JSON matching, these functions validate that the converted
FHIR bundles have the correct structure and content properties.
"""

from __future__ import annotations


def assert_no_placeholder_references(bundle: dict) -> None:
    """Verify no resources reference placeholder IDs.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any placeholder references are found
    """
    placeholders = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Check all reference fields
        refs = _extract_all_references(resource)
        for field_path, ref in refs:
            if "placeholder" in ref.lower():
                placeholders.append(
                    f"{resource_type}/{resource_id} -> {field_path}: {ref}"
                )

    assert not placeholders, (
        f"Found {len(placeholders)} placeholder reference(s):\n" +
        "\n".join(f"  - {p}" for p in placeholders)
    )


def assert_all_references_resolve(bundle: dict) -> None:
    """Verify all references point to resources in the bundle.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any references don't resolve
    """
    # Build set of available resource IDs
    resource_ids = set()
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if "resourceType" in resource and "id" in resource:
            ref = f"{resource['resourceType']}/{resource['id']}"
            resource_ids.add(ref)

    # Check all references resolve
    broken_refs = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        refs = _extract_all_references(resource)
        for field_path, ref in refs:
            # Skip urn: references (bundle-internal)
            if ref.startswith("urn:"):
                continue

            if ref not in resource_ids:
                broken_refs.append(
                    f"{resource_type}/{resource_id} -> {field_path}: {ref}"
                )

    assert not broken_refs, (
        f"Found {len(broken_refs)} broken reference(s):\n" +
        "\n".join(f"  - {r}" for r in broken_refs)
    )


def assert_all_required_fields_present(bundle: dict) -> None:
    """Verify all resources have critical FHIR fields.

    This validates the most critical required fields. Some FHIR fields
    have alternatives (e.g., MedicationStatement can have medicationCodeableConcept
    OR medicationReference), so we check for the most common required ones.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any critical fields are missing
    """
    # Define critical required fields per resource type
    # Note: Some fields have alternatives (checked separately)
    required_fields = {
        "Patient": ["id"],
        "Condition": ["id", "subject"],
        "AllergyIntolerance": ["id", "patient"],
        "MedicationStatement": ["id", "subject", "status"],  # medication* checked separately
        "Procedure": ["id", "subject", "status"],
        "Observation": ["id", "subject", "status"],  # code often missing in organizer obs
        "Composition": ["id", "status", "type", "subject", "date", "title"],
    }

    missing_fields = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        if resource_type in required_fields:
            for field in required_fields[resource_type]:
                if field not in resource:
                    missing_fields.append(
                        f"{resource_type}/{resource_id} missing '{field}'"
                    )

    assert not missing_fields, (
        f"Found {len(missing_fields)} missing required field(s):\n" +
        "\n".join(f"  - {m}" for m in missing_fields)
    )


def assert_no_empty_codes(bundle: dict) -> None:
    """Verify no resources have empty code elements.

    Some resources have alternatives (e.g., MedicationStatement can have
    medicationReference instead of medicationCodeableConcept). This validates
    that critical clinical resources have proper coding.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any empty codes are found
    """
    empty_codes = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Condition, AllergyIntolerance, Procedure always need codes
        if resource_type in ["Condition", "AllergyIntolerance", "Procedure"]:
            code = resource.get("code")

            if not code:
                empty_codes.append(f"{resource_type}/{resource_id} has no code")
            elif code == {}:
                empty_codes.append(f"{resource_type}/{resource_id} has empty code {{}}")
            elif isinstance(code, dict):
                # Check that code has at least 'coding' or 'text'
                if not code.get("coding") and not code.get("text"):
                    empty_codes.append(
                        f"{resource_type}/{resource_id} code has no coding or text"
                    )

        # MedicationStatement needs medication* (CodeableConcept OR Reference)
        elif resource_type == "MedicationStatement":
            has_medication = (
                resource.get("medicationCodeableConcept") or
                resource.get("medicationReference")
            )
            if not has_medication:
                empty_codes.append(
                    f"{resource_type}/{resource_id} has no medication* field"
                )

        # Observations: skip organizer observations (hasMember present)
        # Only validate leaf observations
        elif resource_type == "Observation":
            # Skip organizer observations
            if resource.get("hasMember"):
                continue

            code = resource.get("code")
            if not code or code == {}:
                empty_codes.append(f"{resource_type}/{resource_id} has no/empty code")
            elif isinstance(code, dict):
                if not code.get("coding") and not code.get("text"):
                    empty_codes.append(
                        f"{resource_type}/{resource_id} code has no coding or text"
                    )

    assert not empty_codes, (
        f"Found {len(empty_codes)} empty code(s):\n" +
        "\n".join(f"  - {c}" for c in empty_codes)
    )


def count_resources_by_type(bundle: dict, resource_type: str) -> int:
    """Count resources of a specific type in the bundle.

    Args:
        bundle: FHIR Bundle to count
        resource_type: Resource type to count (e.g., "Condition")

    Returns:
        Number of resources of that type
    """
    count = 0
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            count += 1
    return count


def get_resource_summary(bundle: dict) -> dict[str, int]:
    """Get a summary of resource counts by type.

    Args:
        bundle: FHIR Bundle to summarize

    Returns:
        Dictionary mapping resource type to count
    """
    summary = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type:
            summary[resource_type] = summary.get(resource_type, 0) + 1
    return summary


def _extract_all_references(obj: dict | list, path: str = "") -> list[tuple[str, str]]:
    """Recursively extract all reference values from a resource.

    Args:
        obj: Dictionary or list to search
        path: Current path (for error reporting)

    Returns:
        List of (field_path, reference_value) tuples
    """
    refs = []

    if isinstance(obj, dict):
        # Check if this dict is a Reference
        if "reference" in obj and isinstance(obj["reference"], str):
            refs.append((path, obj["reference"]))

        # Recurse into all values
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            refs.extend(_extract_all_references(value, new_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            refs.extend(_extract_all_references(item, new_path))

    return refs
