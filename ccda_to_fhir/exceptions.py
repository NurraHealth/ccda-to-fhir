"""Custom exceptions for C-CDA to FHIR conversion.

This module defines a hierarchy of specific exceptions to replace generic
Exception catching and provide better error context for debugging and logging.
"""

from __future__ import annotations


class CCDAConversionError(Exception):
    """Base exception for all C-CDA to FHIR conversion errors.

    All converter-specific exceptions inherit from this base class,
    allowing callers to catch all conversion errors with a single except clause.
    """

    pass


class MissingRequiredFieldError(CCDAConversionError):
    """Raised when a required C-CDA field is missing or None.

    Examples:
        - AllergyIntolerance without participant (allergen)
        - Observation without code
        - Patient without name
    """

    def __init__(self, field_name: str, resource_type: str, details: str = ""):
        """Initialize with field and resource context.

        Args:
            field_name: Name of the missing required field
            resource_type: Type of C-CDA/FHIR resource being converted
            details: Additional context about the error
        """
        self.field_name = field_name
        self.resource_type = resource_type
        self.details = details

        message = f"{resource_type} is missing required field: {field_name}"
        if details:
            message += f" ({details})"

        super().__init__(message)


class InvalidCodeSystemError(CCDAConversionError):
    """Raised when a code system OID cannot be mapped to FHIR URI.

    Examples:
        - Unknown OID that's not in the mapping table
        - Malformed OID (not matching pattern)
    """

    def __init__(self, oid: str, context: str = ""):
        """Initialize with OID and context.

        Args:
            oid: The invalid or unmapped OID
            context: Where this OID was encountered
        """
        self.oid = oid
        self.context = context

        message = f"Cannot map OID to FHIR code system: {oid}"
        if context:
            message += f" (in {context})"

        super().__init__(message)


class InvalidDateFormatError(CCDAConversionError):
    """Raised when a C-CDA date string cannot be parsed or validated.

    Examples:
        - Non-numeric characters in date: "202X0101"
        - Invalid month: "20240013"
        - Invalid day: "20240132"
    """

    def __init__(self, date_string: str, reason: str = ""):
        """Initialize with date string and reason.

        Args:
            date_string: The invalid date string
            reason: Why the date is invalid
        """
        self.date_string = date_string
        self.reason = reason

        message = f"Invalid date format: {date_string}"
        if reason:
            message += f" - {reason}"

        super().__init__(message)


class InvalidTemplateError(CCDAConversionError):
    """Raised when a C-CDA template ID is not recognized or supported.

    Examples:
        - Template ID doesn't match expected pattern
        - Template version not supported
    """

    def __init__(self, template_id: str, expected: str = ""):
        """Initialize with template ID and expected value.

        Args:
            template_id: The invalid or unrecognized template ID
            expected: What template ID was expected (optional)
        """
        self.template_id = template_id
        self.expected = expected

        message = f"Invalid or unsupported template ID: {template_id}"
        if expected:
            message += f" (expected: {expected})"

        super().__init__(message)


class ResourceValidationError(CCDAConversionError):
    """Raised when a generated FHIR resource fails validation.

    Examples:
        - Missing required FHIR field
        - Invalid value for FHIR element
        - Constraint violation
    """

    def __init__(self, resource_type: str, resource_id: str, errors: list[str]):
        """Initialize with resource info and validation errors.

        Args:
            resource_type: Type of FHIR resource (e.g., "Patient")
            resource_id: ID of the resource that failed validation
            errors: List of validation error messages
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.errors = errors

        error_list = "\n  - ".join(errors)
        message = (
            f"FHIR {resource_type} validation failed (id: {resource_id}):\n  - {error_list}"
        )

        super().__init__(message)


class MissingReferenceError(CCDAConversionError):
    """Raised when a FHIR reference points to a non-existent resource.

    This error is raised during reference validation when attempting to create
    a reference to a resource that doesn't exist in the bundle.

    Examples:
        - Condition.subject references Patient that wasn't converted
        - Observation.performer references Practitioner that failed validation
        - MedicationRequest.requester references missing Practitioner
    """

    def __init__(self, resource_type: str, resource_id: str, context: str = ""):
        """Initialize with reference details.

        Args:
            resource_type: Type of resource being referenced (e.g., "Patient")
            resource_id: ID of the non-existent resource
            context: Where this reference was created (optional)
        """
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.context = context

        message = f"Reference to non-existent resource: {resource_type}/{resource_id}"
        if context:
            message += f" (in {context})"

        super().__init__(message)


class InvalidValueError(CCDAConversionError):
    """Raised when a C-CDA value is invalid or out of range.

    Examples:
        - Negative value where positive required
        - Value outside reference range
        - Invalid unit code
    """

    def __init__(self, field_name: str, value: str, reason: str = ""):
        """Initialize with field, value, and reason.

        Args:
            field_name: Name of the field with invalid value
            value: The invalid value
            reason: Why the value is invalid
        """
        self.field_name = field_name
        self.value = value
        self.reason = reason

        message = f"Invalid value for {field_name}: {value}"
        if reason:
            message += f" - {reason}"

        super().__init__(message)


class UnsupportedFeatureError(CCDAConversionError):
    """Raised when encountering a C-CDA feature not yet supported.

    Examples:
        - Complex nested structures
        - Rare template combinations
        - Extensions not in scope
    """

    def __init__(self, feature: str, context: str = ""):
        """Initialize with feature description and context.

        Args:
            feature: Description of the unsupported feature
            context: Where this feature was encountered
        """
        self.feature = feature
        self.context = context

        message = f"Unsupported C-CDA feature: {feature}"
        if context:
            message += f" (in {context})"

        super().__init__(message)
