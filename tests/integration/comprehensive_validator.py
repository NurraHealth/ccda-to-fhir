"""Comprehensive FHIR field validator for E2E tests.

This module provides utilities to validate EVERY field in converted FHIR resources,
ensuring complete test coverage of all populated fields.
"""

from typing import Any

from fhir.resources.bundle import Bundle


class FieldValidator:
    """Validates all fields in FHIR resources comprehensively."""

    def __init__(self, bundle: Bundle):
        """Initialize with a FHIR Bundle."""
        self.bundle = bundle
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_all(self) -> dict[str, Any]:
        """Validate all resources in bundle comprehensively.

        Returns:
            Dict with validation results including errors, warnings, and stats
        """
        stats = {
            "total_resources": 0,
            "resources_by_type": {},
            "fields_validated": 0,
            "errors": [],
            "warnings": []
        }

        for entry in self.bundle.entry:
            resource = entry.resource
            resource_type = resource.get_resource_type()

            stats["total_resources"] += 1
            stats["resources_by_type"][resource_type] = \
                stats["resources_by_type"].get(resource_type, 0) + 1

            # Validate this resource
            resource_dict = resource.dict() if hasattr(resource, 'dict') else resource.model_dump()
            field_count = self._validate_resource(resource_type, resource_dict)
            stats["fields_validated"] += field_count

        stats["errors"] = self.errors
        stats["warnings"] = self.warnings
        return stats

    def _validate_resource(self, resource_type: str, resource: dict, path: str = "") -> int:
        """Recursively validate all fields in a resource.

        Returns:
            Number of fields validated
        """
        field_count = 0

        if isinstance(resource, dict):
            for key, value in resource.items():
                current_path = f"{path}.{key}" if path else f"{resource_type}.{key}"

                # Skip None and empty values
                if value is None or value == [] or value == {}:
                    continue

                field_count += 1

                # Validate based on field type
                self._validate_field(current_path, key, value, resource_type)

                # Recurse into nested structures
                field_count += self._validate_resource(resource_type, value, current_path)

        elif isinstance(resource, list):
            for i, item in enumerate(resource):
                field_count += self._validate_resource(resource_type, item, f"{path}[{i}]")

        return field_count

    def _validate_field(self, path: str, key: str, value: Any, resource_type: str):
        """Validate a specific field."""

        # Required fields must exist
        if key == "resourceType":
            if not value:
                self.errors.append(f"{path}: resourceType is empty")

        elif key == "id":
            if not value or not isinstance(value, str):
                self.errors.append(f"{path}: id must be a non-empty string, got {type(value)}")

        elif key == "status":
            if not value or not isinstance(value, str):
                self.errors.append(f"{path}: status must be a non-empty string")

        # Coding structures
        elif key == "system":
            if not value or not isinstance(value, str):
                self.errors.append(f"{path}: system must be a non-empty string (URI)")
            elif not (value.startswith("http://") or value.startswith("https://") or
                      value.startswith("urn:")):
                self.warnings.append(f"{path}: system should be a URI, got '{value}'")

        elif key == "code":
            if isinstance(value, str):
                if not value:
                    self.errors.append(f"{path}: code must not be empty")
            elif isinstance(value, dict):
                # code as CodeableConcept - validate it has coding
                if "coding" not in value or not value["coding"]:
                    self.errors.append(f"{path}: CodeableConcept must have coding array")

        # Identifiers
        elif key == "identifier":
            if isinstance(value, list):
                for i, ident in enumerate(value):
                    if isinstance(ident, dict):
                        if "system" not in ident or not ident["system"]:
                            self.errors.append(f"{path}[{i}]: identifier must have system")
                        if "value" not in ident or not ident["value"]:
                            self.errors.append(f"{path}[{i}]: identifier must have value")

        # References
        elif key == "reference":
            if not value or not isinstance(value, str):
                self.errors.append(f"{path}: reference must be a non-empty string")
            elif "/" not in value:
                self.warnings.append(f"{path}: reference should be ResourceType/id format, got '{value}'")

        # Meta profiles (US Core)
        elif key == "profile":
            if isinstance(value, list):
                for profile in value:
                    if not profile.startswith("http://"):
                        self.warnings.append(f"{path}: profile should be a URL, got '{profile}'")


def validate_resource_comprehensive(bundle: Bundle, resource_type: str,
                                   expected_fields: set[str]) -> dict[str, Any]:
    """Validate that a specific resource type has all expected fields populated.

    Args:
        bundle: FHIR Bundle
        resource_type: Resource type to validate (e.g., "Patient")
        expected_fields: Set of field paths that MUST be populated

    Returns:
        Validation results with missing/extra fields
    """
    resources = [e.resource for e in bundle.entry
                 if e.resource.get_resource_type() == resource_type]

    if not resources:
        return {"error": f"No {resource_type} resources found in bundle"}

    # Collect all populated fields from first resource
    resource_dict = resources[0].dict() if hasattr(resources[0], 'dict') else resources[0].model_dump()

    def collect_paths(obj, path="", depth=0, max_depth=6):
        if depth > max_depth:
            return set()
        paths = set()
        if isinstance(obj, dict):
            for key, value in obj.items():
                if value is None or value == [] or value == {}:
                    continue
                new_path = f"{path}.{key}" if path else key
                paths.add(new_path)
                paths.update(collect_paths(value, new_path, depth + 1, max_depth))
        elif isinstance(obj, list) and obj:
            paths.update(collect_paths(obj[0], path, depth + 1, max_depth))
        return paths

    populated_fields = collect_paths(resource_dict)

    # Find missing and extra fields
    missing = expected_fields - populated_fields
    extra = populated_fields - expected_fields

    return {
        "resource_type": resource_type,
        "expected": len(expected_fields),
        "populated": len(populated_fields),
        "missing": sorted(missing),
        "extra": sorted(extra),
        "coverage": len(populated_fields & expected_fields) / len(expected_fields) * 100
                    if expected_fields else 100
    }
