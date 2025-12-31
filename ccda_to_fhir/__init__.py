"""C-CDA to FHIR R4B conversion library."""

from __future__ import annotations

from .convert import DocumentConverter, convert_document

__version__ = "0.1.0"

__all__ = [
    "convert_document",
    "DocumentConverter",
]
