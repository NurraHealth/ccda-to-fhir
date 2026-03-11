"""Utility functions for C-CDA to FHIR conversion."""

from __future__ import annotations

from datetime import datetime, timezone


def fhir_date_to_instant(fhir_date: str | None) -> str | None:
    """Convert a FHIR date or dateTime to a FHIR instant.

    ``DocumentReference.date`` is type ``instant`` which requires at minimum
    ``YYYY-MM-DDThh:mm:ssZ``.  The encounter converter's ``convert_date``
    may return date-only values (``YYYY-MM-DD``) when the C-CDA timestamp
    lacks a timezone.  This helper pads those to a valid instant.

    Returns ``None`` when *fhir_date* is ``None`` or empty.
    """
    if not fhir_date:
        return None

    # Pad partial dates (YYYY, YYYY-MM) to full YYYY-MM-DD so fromisoformat works
    if len(fhir_date) == 4:
        fhir_date = f"{fhir_date}-01-01"
    elif len(fhir_date) == 7:
        fhir_date = f"{fhir_date}-01"

    try:
        dt = datetime.fromisoformat(fhir_date)
    except ValueError:
        return fhir_date

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.isoformat().replace("+00:00", "Z")
