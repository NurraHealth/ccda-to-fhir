"""Type definitions for C-CDA to FHIR conversion.

This module defines proper types for FHIR resources and JSON structures,
avoiding the use of Any wherever possible.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias, TypedDict

from pydantic import BaseModel

# JSON primitive types
JSONPrimitive: TypeAlias = str | int | float | bool | None

# JSON value can be primitive, sequence, or object (recursive)
# Uses Sequence (covariant) instead of list (invariant) so that
# list[str], list[JSONObject], etc. are assignable to JSONValue
JSONValue: TypeAlias = JSONPrimitive | Sequence["JSONValue"] | dict[str, "JSONValue"]

# FHIR resources are JSON objects with string keys
FHIRResourceDict: TypeAlias = dict[str, JSONValue]

# JSON object (for nested structures within FHIR resources)
JSONObject: TypeAlias = dict[str, JSONValue]

# JSON array (for lists within FHIR resources)
JSONArray: TypeAlias = list[JSONValue]


# ============================================================================
# FHIR element models
#
# Pydantic representations of common FHIR R4 data types.  These are used
# inside typed return values (e.g. ReasonResult) so the converters carry
# structured data instead of raw dicts.  Call `.to_dict()` when you need
# to embed the value in a FHIRResourceDict.
# ============================================================================


class FHIRCoding(BaseModel, frozen=True):
    """FHIR Coding element (system + code + display)."""

    system: str | None = None
    code: str | None = None
    display: str | None = None

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {}
        if self.system is not None:
            d["system"] = self.system
        if self.code is not None:
            d["code"] = self.code
        if self.display is not None:
            d["display"] = self.display
        return d


class FHIRCodeableConcept(BaseModel, frozen=True):
    """FHIR CodeableConcept element (coding list + text)."""

    coding: list[FHIRCoding] = []
    text: str | None = None

    def to_dict(self) -> dict[str, str | list[dict[str, str]]]:
        d: dict[str, str | list[dict[str, str]]] = {}
        if self.coding:
            d["coding"] = [c.to_dict() for c in self.coding]
        if self.text is not None:
            d["text"] = self.text
        return d


class FHIRReference(BaseModel, frozen=True):
    """FHIR Reference element (reference URI + optional display)."""

    reference: str
    display: str | None = None

    def to_dict(self) -> dict[str, str]:
        d: dict[str, str] = {"reference": self.reference}
        if self.display is not None:
            d["display"] = self.display
        return d


class ReasonResult(BaseModel, frozen=True):
    """Result of extracting reason codes and references from C-CDA entry relationships."""

    codes: list[FHIRCodeableConcept] = []
    """FHIR CodeableConcept elements for reason codes."""

    references: list[FHIRReference] = []
    """FHIR Reference elements for reason references."""


class DiagnosisRole(BaseModel, frozen=True):
    """Diagnosis role code/display for encounter diagnosis use element."""

    code: str
    display: str


class OperationStats(BaseModel, frozen=True):
    """Performance statistics for a single profiled operation."""

    count: float
    total: float
    avg: float
    min: float
    max: float


class ValidationStats(BaseModel, frozen=True):
    """Validation statistics from FHIRValidator."""

    validated: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0


class RegistryStats(BaseModel, frozen=True):
    """Statistics from ReferenceRegistry."""

    registered: int = 0
    resolved: int = 0
    failed: int = 0


class EncounterContext(BaseModel, frozen=True):
    """Encounter context from encompassingEncounter for DocumentReference creation."""

    reference: str | None = None
    """Encounter reference in urn:uuid format."""

    date: str | None = None
    """Encounter date as a FHIR instant string."""

    display: str | None = None
    """Human-readable label from encompassingEncounter code.displayName."""

    def to_fhir_reference(self) -> JSONObject | None:
        """Build a FHIR Reference object, or None if no reference is set."""
        if not self.reference:
            return None
        ref: JSONObject = {"reference": self.reference}
        if self.display:
            ref["display"] = self.display
        return ref


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
