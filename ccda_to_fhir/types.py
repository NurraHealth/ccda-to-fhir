"""Type definitions for C-CDA to FHIR conversion.

This module defines proper types for FHIR resources and JSON structures,
avoiding the use of Any wherever possible.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias, TypedDict

from fhir.resources.R4B.reference import Reference
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    """FHIR Coding element (system + code + display).

    Per FHIR R4, ``system`` is required when ``code`` is present and vice-versa.
    A FHIRCoding with only ``display`` (no system/code) is permitted by the spec.
    """

    model_config = ConfigDict(extra="forbid")

    system: str | None = None
    code: str | None = None
    display: str | None = None

    @model_validator(mode="after")
    def _system_and_code_must_co_occur(self) -> FHIRCoding:
        has_system = self.system is not None
        has_code = self.code is not None
        if has_system != has_code:
            raise ValueError(
                "system and code must both be provided or both omitted; "
                f"got system={self.system!r}, code={self.code!r}"
            )
        return self

    def to_dict(self) -> JSONObject:
        return self.model_dump(exclude_none=True)


class FHIRCodeableConcept(BaseModel, frozen=True):
    """FHIR CodeableConcept element (coding list + text)."""

    model_config = ConfigDict(extra="forbid")

    coding: list[FHIRCoding] = Field(default_factory=list)
    text: str | None = None

    def to_dict(self) -> JSONObject:
        # Custom serialization: omit empty coding list (model_dump would
        # include it as []), unlike FHIRCoding which uses
        # model_dump(exclude_none=True) since they only need to drop None fields.
        d: JSONObject = {}
        if self.coding:
            d["coding"] = [c.to_dict() for c in self.coding]
        if self.text is not None:
            d["text"] = self.text
        return d


class ReasonResult(BaseModel, frozen=True):
    """Result of extracting reason codes and references from C-CDA entry relationships."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    codes: list[FHIRCodeableConcept] = Field(default_factory=list)
    """FHIR CodeableConcept elements for reason codes."""

    references: list[Reference] = Field(default_factory=list)
    """FHIR Reference elements for reason references."""

    def __bool__(self) -> bool:
        return bool(self.codes or self.references)


class DiagnosisRole(BaseModel, frozen=True):
    """Diagnosis role code/display for encounter diagnosis use element."""

    model_config = ConfigDict(extra="forbid")

    code: str
    display: str


class OperationStats(BaseModel, frozen=True):
    """Performance statistics for a single profiled operation.

    All fields default to zero.  A zero-valued instance (from an untracked
    operation) is falsy so callers can use ``if stats:`` to distinguish
    "tracked with data" from "not tracked".
    """

    model_config = ConfigDict(extra="forbid")

    count: int = 0
    total: float = 0.0
    avg: float = 0.0
    min_duration: float = 0.0
    max_duration: float = 0.0

    def __bool__(self) -> bool:
        return self.count > 0


class ValidationStats(BaseModel):
    """Validation statistics from FHIRValidator.

    Not frozen: mutated in-place by FHIRValidator during validation.
    Callers receive an immutable snapshot via ``model_copy()``.
    """

    model_config = ConfigDict(extra="forbid")

    validated: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0


class RegistryStats(BaseModel):
    """Statistics from ReferenceRegistry.

    Not frozen: mutated in-place by ReferenceRegistry during resolution.
    Callers receive an immutable snapshot via ``model_copy()``.
    """

    model_config = ConfigDict(extra="forbid")

    registered: int = 0
    resolved: int = 0
    failed: int = 0


class HumanName(TypedDict, total=False):
    """FHIR R4 HumanName element (all fields optional)."""

    use: str
    text: str
    family: str
    given: list[str]
    prefix: list[str]
    suffix: list[str]
    period: JSONObject
    extension: list[JSONObject]


def format_human_name_display(name: HumanName) -> str | None:
    """Build a display string from a FHIR HumanName.

    Per FHIR R4, HumanName.text is "the entire name as it should be displayed"
    and is preferred when present. Falls back to "prefix given family suffix".

    Returns None if no meaningful parts are present.
    """
    text = name.get("text")
    if text and text.strip():
        return text.strip()

    parts: list[str] = [
        *name.get("prefix", []),
        *name.get("given", []),
    ]
    family = name.get("family")
    if family:
        parts.append(family)
    parts.extend(name.get("suffix", []))

    return " ".join(p for p in parts if p) or None


class EncounterContext(BaseModel, frozen=True):
    """Encounter context from encompassingEncounter for DocumentReference creation."""

    reference: str | None = None
    """Encounter reference in urn:uuid format."""

    date: str | None = None
    """Encounter date as a FHIR instant string."""

    display: str | None = None
    """Human-readable label from encompassingEncounter code.displayName."""

    def to_fhir_reference(self) -> Reference | None:
        """Build a FHIR Reference, or None if no reference is set."""
        if not self.reference:
            return None
        return Reference(reference=self.reference, display=self.display)


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
