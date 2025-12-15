"""Type definitions for C-CDA to FHIR conversion.

This module defines proper types for FHIR resources and JSON structures,
avoiding the use of Any wherever possible.
"""

from __future__ import annotations

from typing import TypeAlias

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
