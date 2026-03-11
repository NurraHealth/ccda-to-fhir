"""Build FHIR author references from C-CDA Author elements.

Shared logic for converting C-CDA authors to FHIR Reference objects
(Practitioner, Device, or Organization) used by both document-level and
entry-level author reference builders.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
    RepresentedOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import ON, PN
from ccda_to_fhir.id_generator import generate_id_from_identifiers
from ccda_to_fhir.types import JSONObject


def format_person_display(person: AssignedPerson | None) -> str | None:
    """Format a person name for FHIR Reference.display.

    Extracts given + family name parts from the first PN element.

    Args:
        person: C-CDA AssignedPerson with name list.

    Returns:
        Formatted "Given Family" string or None.
    """
    if not person or not person.name:
        return None

    name: PN = person.name[0]
    parts: list[str] = []

    if name.given:
        for given in name.given:
            if isinstance(given, str):
                parts.append(given)
            elif given.value:
                parts.append(given.value)

    if name.family:
        if isinstance(name.family, str):
            parts.append(name.family)
        elif name.family.value:
            parts.append(name.family.value)

    return " ".join(parts) if parts else None


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


def _make_ref(reference: str, display: str | None) -> JSONObject:
    """Build a FHIR Reference dict, including display when available."""
    ref: JSONObject = {"reference": reference}
    if display:
        ref["display"] = display
    return ref


def _build_device_org_fallback_refs(assigned: AssignedAuthor) -> list[JSONObject]:
    """Build Device and/or Organization refs when no assignedPerson exists.

    Args:
        assigned: The AssignedAuthor element (already confirmed to lack assignedPerson).

    Returns:
        List of FHIR Reference objects for Device and/or Organization.
    """
    refs: list[JSONObject] = []
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
        refs.append(_make_ref(f"urn:uuid:{device_id}", display))
    # Organization uses its own identifier
    if assigned.represented_organization and assigned.represented_organization.id:
        org_first_id = assigned.represented_organization.id[0]
        org_id = generate_id_from_identifiers(
            "Organization",
            org_first_id.root or None,
            org_first_id.extension or None,
        )
        display = format_organization_display(assigned.represented_organization)
        refs.append(_make_ref(f"urn:uuid:{org_id}", display))
    return refs


def build_author_references(authors: list[Author]) -> list[JSONObject]:
    """Convert C-CDA authors to FHIR references (Practitioner, Device, or Organization).

    When an author has an assignedPerson, a Practitioner reference is created.
    Otherwise, falls back to Device (from assignedAuthoringDevice) and/or
    Organization (from representedOrganization) per FHIR DocumentReference.author
    which accepts Practitioner | Device | Organization.
    """
    refs: list[JSONObject] = []
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
            refs.append(_make_ref(f"urn:uuid:{prac_id}", display))
        else:
            refs.extend(_build_device_org_fallback_refs(assigned))
    return refs
