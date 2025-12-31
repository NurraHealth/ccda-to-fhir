"""Type definitions for C-CDA to FHIR conversion.

This module defines proper types for FHIR resources and JSON structures,
avoiding the use of Any wherever possible.
"""

from __future__ import annotations

from typing import TypeAlias, TypedDict

# JSON primitive types
JSONPrimitive: TypeAlias = str | int | float | bool | None

# JSON value can be primitive, list, or object (recursive)
JSONValue: TypeAlias = JSONPrimitive | list["JSONValue"] | dict[str, "JSONValue"]

# FHIR resources are JSON objects with string keys
# This is more specific than dict[str, Any] and accurately represents FHIR structure
FHIRResourceDict: TypeAlias = dict[str, JSONValue]

# JSON object (for nested structures within FHIR resources)
JSONObject: TypeAlias = dict[str, JSONValue]

# JSON array (for lists within FHIR resources)
JSONArray: TypeAlias = list[JSONValue]


# =============================================================================
# Conversion Metadata Types
# =============================================================================


class TemplateOccurrence(TypedDict):
    """Information about a C-CDA template encountered during conversion."""

    template_id: str
    """The C-CDA template ID (OID)"""

    name: str | None
    """Human-readable template name, if known"""

    count: int
    """Number of times this template was encountered"""


class ConversionError(TypedDict):
    """Information about an error encountered during conversion."""

    template_id: str | None
    """The template ID of the entry that failed, if available"""

    entry_id: str | None
    """The C-CDA entry ID (root/extension), if available"""

    error_type: str
    """The type of error (class name)"""

    error_message: str
    """The error message"""


class ConversionMetadata(TypedDict):
    """Metadata about the conversion process.

    Tracks what templates were processed, skipped, and any errors encountered.
    This allows users to understand what C-CDA content was converted and what
    was skipped due to lack of FHIR mapping.
    """

    processed_templates: dict[str, TemplateOccurrence]
    """Templates that were successfully processed.

    Key: template_id (OID)
    Value: Occurrence information
    """

    skipped_templates: dict[str, TemplateOccurrence]
    """Templates encountered but not supported (no FHIR mapping).

    Key: template_id (OID)
    Value: Occurrence information
    """

    errors: list[ConversionError]
    """Errors encountered during conversion.

    These are templates that SHOULD be supported but failed during processing
    (e.g., missing required fields, validation errors).
    """


class ConversionResult(TypedDict):
    """Result of C-CDA to FHIR conversion.

    Contains both the converted FHIR Bundle and metadata about what was
    processed, skipped, and any errors encountered.
    """

    bundle: FHIRResourceDict
    """The FHIR Bundle containing all converted resources"""

    metadata: ConversionMetadata
    """Metadata about the conversion process"""
