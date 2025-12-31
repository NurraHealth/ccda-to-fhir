"""Central ID generation for FHIR resources.

This module provides a single source of truth for generating FHIR resource IDs.
All converters should use these functions instead of implementing their own ID generation.

IMPORTANT: Within a single document conversion, the same C-CDA identifiers should
always generate the same UUID to ensure references resolve correctly.
"""

import uuid
from typing import Optional

# Cache for ID generation within a document conversion
# Key: (resource_type, root, extension) tuple
# Value: generated UUID
_id_cache: dict[tuple[str, Optional[str], Optional[str]], str] = {}


def reset_id_cache() -> None:
    """Reset the ID cache.

    This should be called at the start of each document conversion to ensure
    IDs are unique across documents but consistent within a document.
    """
    global _id_cache
    _id_cache = {}


def generate_id_from_identifiers(
    resource_type: str,
    root: Optional[str] = None,
    extension: Optional[str] = None
) -> str:
    """Generate a consistent UUID v4 for a resource based on C-CDA identifiers.

    Within a single document, the same (resource_type, root, extension) combination
    will always return the same UUID. Across documents, different UUIDs are generated.

    Args:
        resource_type: The FHIR resource type (e.g., "Practitioner", "Patient")
        root: The C-CDA identifier root (OID or UUID)
        extension: The C-CDA identifier extension

    Returns:
        A UUID v4 string (cached for consistency within document)

    Examples:
        >>> reset_id_cache()
        >>> id1 = generate_id_from_identifiers("Practitioner", "2.16.840.1.113883.4.6", "123")
        >>> id2 = generate_id_from_identifiers("Practitioner", "2.16.840.1.113883.4.6", "123")
        >>> id1 == id2  # Same within document
        True
    """
    # Normalize None to empty string for cache key
    cache_key = (resource_type, root or "", extension or "")

    # Check cache first
    if cache_key in _id_cache:
        return _id_cache[cache_key]

    # Generate new UUID and cache it
    new_id = str(uuid.uuid4())
    _id_cache[cache_key] = new_id
    return new_id


def generate_id() -> str:
    """Generate a unique FHIR resource ID using UUID v4.

    WARNING: This generates a new UUID every time. For resources that may be
    referenced multiple times, use generate_id_from_identifiers() instead.

    Returns:
        A unique ID string (UUID v4 format)
    """
    return str(uuid.uuid4())
