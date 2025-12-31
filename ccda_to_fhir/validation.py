"""FHIR resource validation utilities.

This module provides validation for FHIR resources using the fhir.resources library
to ensure generated resources conform to FHIR R4/R4B specifications.
"""

from __future__ import annotations

from fhir_core.fhirabstractmodel import FHIRAbstractModel

from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict

logger = get_logger(__name__)


class ValidationError(Exception):
    """Exception raised when FHIR resource validation fails."""

    def __init__(self, resource_type: str, errors: list[str]):
        """Initialize validation error.

        Args:
            resource_type: Type of FHIR resource that failed validation
            errors: List of validation error messages
        """
        self.resource_type = resource_type
        self.errors = errors
        error_msg = f"Validation failed for {resource_type}: {'; '.join(errors)}"
        super().__init__(error_msg)


class ValidationWarning:
    """Warning for non-critical validation issues."""

    def __init__(self, resource_type: str, warnings: list[str]):
        """Initialize validation warning.

        Args:
            resource_type: Type of FHIR resource
            warnings: List of warning messages
        """
        self.resource_type = resource_type
        self.warnings = warnings


class FHIRValidator:
    """Validates FHIR resources against FHIR specifications."""

    def __init__(self, strict: bool = False):
        """Initialize the FHIR validator.

        Args:
            strict: If True, raise exceptions on validation errors.
                   If False, log errors and continue.
        """
        self.strict = strict
        self._validation_stats = {
            "validated": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

    def validate_resource(
        self, resource_dict: FHIRResourceDict, resource_class: type[FHIRAbstractModel]
    ) -> FHIRAbstractModel | None:
        """Validate a FHIR resource dictionary against its schema.

        Args:
            resource_dict: Dictionary representation of FHIR resource
            resource_class: The fhir.resources class to validate against
                          (e.g., Patient, Observation, Condition)

        Returns:
            Validated FHIR resource model if successful, None if validation fails
            and strict mode is disabled

        Raises:
            ValidationError: If validation fails and strict mode is enabled
        """
        self._validation_stats["validated"] += 1
        resource_type = resource_dict.get("resourceType", "Unknown")

        try:
            # Attempt to construct the FHIR resource model
            # This will raise pydantic ValidationError if the resource is invalid
            validated_resource = resource_class(**resource_dict)

            self._validation_stats["passed"] += 1
            logger.debug(
                f"Validation passed for {resource_type}",
                resource_id=resource_dict.get("id"),
            )
            return validated_resource

        except Exception as e:
            self._validation_stats["failed"] += 1
            errors = self._extract_validation_errors(e)

            logger.error(
                f"Validation failed for {resource_type}: {'; '.join(errors)}",
                resource_id=resource_dict.get("id"),
                errors=errors,
            )

            if self.strict:
                raise ValidationError(resource_type, errors) from e

            return None

    def validate_bundle(self, bundle_dict: FHIRResourceDict) -> FHIRResourceDict:
        """Validate a Bundle and all its entries.

        Args:
            bundle_dict: Bundle dictionary to validate

        Returns:
            The bundle dictionary (potentially with invalid entries removed in non-strict mode)

        Raises:
            ValidationError: If bundle validation fails and strict mode is enabled
        """
        # Import here to avoid circular imports
        from fhir.resources.R4B.bundle import Bundle

        self._validation_stats["validated"] += 1

        try:
            # Validate the bundle structure
            validated_bundle = Bundle(**bundle_dict)
            self._validation_stats["passed"] += 1

            logger.info(
                "Bundle validation passed",
                entry_count=len(bundle_dict.get("entry", [])),
            )
            return bundle_dict

        except Exception as e:
            self._validation_stats["failed"] += 1
            errors = self._extract_validation_errors(e)

            logger.error(
                f"Bundle validation failed: {'; '.join(errors)}",
                errors=errors,
            )

            if self.strict:
                raise ValidationError("Bundle", errors) from e

            # In non-strict mode, return the bundle as-is
            # Individual entry validation happens in converters
            return bundle_dict

    def _extract_validation_errors(self, exception: Exception) -> list[str]:
        """Extract error messages from validation exception.

        Args:
            exception: The validation exception

        Returns:
            List of error message strings
        """
        errors = []

        # Handle pydantic ValidationError
        if hasattr(exception, "errors"):
            for error in exception.errors():
                loc = " -> ".join(str(x) for x in error.get("loc", []))
                msg = error.get("msg", "Unknown error")
                errors.append(f"{loc}: {msg}")
        else:
            errors.append(str(exception))

        return errors

    def get_stats(self) -> dict[str, int]:
        """Get validation statistics.

        Returns:
            Dictionary with validation stats (validated, passed, failed, warnings)
        """
        return self._validation_stats.copy()

    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            "validated": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }


# Global validator instance (can be configured)
_default_validator: FHIRValidator | None = None


def get_validator(strict: bool = False) -> FHIRValidator:
    """Get the global FHIR validator instance.

    Args:
        strict: If True, validator will raise exceptions on errors

    Returns:
        FHIRValidator instance
    """
    global _default_validator
    if _default_validator is None or _default_validator.strict != strict:
        _default_validator = FHIRValidator(strict=strict)
    return _default_validator


def validate_resource(
    resource_dict: FHIRResourceDict,
    resource_class: type[FHIRAbstractModel],
    strict: bool = False,
) -> FHIRAbstractModel | None:
    """Convenience function to validate a single resource.

    Args:
        resource_dict: Dictionary representation of FHIR resource
        resource_class: The fhir.resources class to validate against
        strict: If True, raise exception on validation failure

    Returns:
        Validated FHIR resource model if successful, None otherwise

    Raises:
        ValidationError: If validation fails and strict=True
    """
    validator = get_validator(strict=strict)
    return validator.validate_resource(resource_dict, resource_class)
