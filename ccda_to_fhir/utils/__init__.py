"""Utility functions for C-CDA to FHIR conversion."""

from __future__ import annotations

import re


def fhir_date_to_instant(fhir_date: str | None) -> str | None:
    """Convert a FHIR date or dateTime to a FHIR instant.

    ``DocumentReference.date`` is type ``instant`` which requires at minimum
    ``YYYY-MM-DDThh:mm:ssZ``.  The encounter converter's ``convert_date``
    may return date-only values (``YYYY-MM-DD``) when the C-CDA timestamp
    lacks a timezone.  This helper pads those to a valid instant.

    Already-valid instants (containing ``T``) are returned unchanged.

    Returns ``None`` when *fhir_date* is ``None`` or empty.
    """
    if not fhir_date:
        return None

    # Already has a time component — assume it's a valid dateTime/instant
    if "T" in fhir_date:
        return fhir_date

    # Date-only: YYYY-MM-DD, YYYY-MM, or YYYY
    # Pad to midnight UTC to satisfy the instant type
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", fhir_date):
        return f"{fhir_date}T00:00:00Z"
    if re.fullmatch(r"\d{4}-\d{2}", fhir_date):
        return f"{fhir_date}-01T00:00:00Z"
    if re.fullmatch(r"\d{4}", fhir_date):
        return f"{fhir_date}-01-01T00:00:00Z"

    # Unrecognised format — return as-is rather than corrupt
    return fhir_date
