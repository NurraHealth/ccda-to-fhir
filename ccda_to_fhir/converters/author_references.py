"""Build FHIR author references from C-CDA Author elements.

Shared logic for converting C-CDA authors to FHIR Reference objects
(Practitioner, Device, or Organization) used by both document-level and
entry-level author reference builders.
"""

from __future__ import annotations

import re
from typing import NamedTuple


from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    Author,
    RepresentedOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import ON, PN, AssignedPerson
from ccda_to_fhir.id_generator import generate_id_from_identifiers
from ccda_to_fhir.types import FHIRReference


def _extract_enxp_values(parts: list | None) -> list[str]:
    """Extract string values from a list of ENXP (or str) name parts."""
    if not parts:
        return []
    result: list[str] = []
    for part in parts:
        if isinstance(part, str):
            if part:
                result.append(part)
        elif part.value:
            result.append(part.value)
    return result


def format_person_display(person: AssignedPerson | None) -> str | None:
    """Format a person name for FHIR Reference.display.

    Extracts prefix + given + family + suffix from the first PN element.
    Deduplicates the family name when it already appears in the given name
    (e.g. Athena puts ``<given>John Doe, MD</given><family>Doe</family>``).

    Args:
        person: C-CDA AssignedPerson with name list.

    Returns:
        Formatted name string or None.
    """
    if not person or not person.name:
        return None

    name: PN = person.name[0]
    parts: list[str] = []

    parts.extend(_extract_enxp_values(name.prefix))

    given_values = _extract_enxp_values(name.given)
    parts.extend(given_values)

    family_value: str | None = None
    if name.family:
        if isinstance(name.family, str):
            family_value = name.family
        elif name.family.value:
            family_value = name.family.value

    if family_value and not _family_in_given(family_value, given_values):
        parts.append(family_value)

    parts.extend(_extract_enxp_values(name.suffix))

    return " ".join(parts) if parts else None


def _family_in_given(family: str, given_values: list[str]) -> bool:
    """Check if the family name already appears in the given name parts.

    Handles Athena-style names where ``<given>`` contains the full formatted
    name including the family name (e.g. ``"John Doe, MD"`` with family ``"Doe"``).
    Uses word-boundary matching (case-insensitive) to avoid false positives
    with short family names that are substrings of other words.
    """
    given_text = " ".join(given_values)
    return bool(re.search(r"\b" + re.escape(family) + r"\b", given_text, re.IGNORECASE))


def format_device_display(device: AssignedAuthoringDevice | None) -> str | None:
    """Format a device name for FHIR Reference.display.

    Creates "Manufacturer (Software)" or whichever part is available.

    Args:
        device: C-CDA AssignedAuthoringDevice element.

    Returns:
        Formatted device string or None.
    """
    if not device:
        return None

    manufacturer = device.manufacturer_model_name
    software = device.software_name

    if manufacturer and software:
        return f"{manufacturer} ({software})"
    return manufacturer or software or None


def format_organization_display(org: RepresentedOrganization | None) -> str | None:
    """Format an organization name for FHIR Reference.display.

    Extracts the first name from the organization's name list.

    Args:
        org: C-CDA RepresentedOrganization element.

    Returns:
        Organization name string or None.
    """
    if not org or not org.name:
        return None

    first_name = org.name[0]
    if isinstance(first_name, str):
        return first_name or None
    if isinstance(first_name, ON):
        return first_name.value or None
    return None


def _build_device_org_fallback_refs(assigned: AssignedAuthor) -> list[FHIRReference]:
    """Build Device and/or Organization refs when no assignedPerson exists.

    Args:
        assigned: The AssignedAuthor element (already confirmed to lack assignedPerson).

    Returns:
        List of FHIRReference objects for Device and/or Organization.
    """
    refs: list[FHIRReference] = []
    # Device uses the author-level assigned.id (not a device-specific ID)
    # because C-CDA assigns the identifier to the author role, not the device itself
    if assigned.assigned_authoring_device and assigned.id:
        first_id = assigned.id[0]
        device_id = generate_id_from_identifiers(
            "Device",
            first_id.root or None,
            first_id.extension or None,
        )
        display = format_device_display(assigned.assigned_authoring_device)
        refs.append(FHIRReference(reference=f"urn:uuid:{device_id}", display=display))
    # Organization uses its own identifier
    if assigned.represented_organization and assigned.represented_organization.id:
        org_first_id = assigned.represented_organization.id[0]
        org_id = generate_id_from_identifiers(
            "Organization",
            org_first_id.root or None,
            org_first_id.extension or None,
        )
        display = format_organization_display(assigned.represented_organization)
        refs.append(FHIRReference(reference=f"urn:uuid:{org_id}", display=display))
    return refs


def build_author_references(authors: list[Author]) -> list[FHIRReference]:
    """Convert C-CDA authors to FHIR references (Practitioner, Device, or Organization).

    When an author has an assignedPerson, a Practitioner reference is created.
    Otherwise, falls back to Device (from assignedAuthoringDevice) and/or
    Organization (from representedOrganization) per FHIR DocumentReference.author
    which accepts Practitioner | Device | Organization.
    """
    refs: list[FHIRReference] = []
    for author in authors:
        if not author.assigned_author:
            continue
        assigned = author.assigned_author
        if assigned.assigned_person and assigned.id:
            first_id = assigned.id[0]
            prac_id = generate_id_from_identifiers(
                "Practitioner",
                first_id.root or None,
                first_id.extension or None,
            )
            display = format_person_display(assigned.assigned_person)
            refs.append(FHIRReference(reference=f"urn:uuid:{prac_id}", display=display))
        else:
            refs.extend(_build_device_org_fallback_refs(assigned))
    return refs
