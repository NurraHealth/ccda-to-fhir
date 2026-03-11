"""Build FHIR author references from C-CDA Author elements.

Shared logic for converting C-CDA authors to FHIR Reference objects
(Practitioner, Device, or Organization) used by both document-level and
entry-level author reference builders.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.author import AssignedAuthor, Author
from ccda_to_fhir.id_generator import generate_id_from_identifiers
from ccda_to_fhir.types import JSONObject


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
        refs.append({"reference": f"urn:uuid:{device_id}"})
    # Organization uses its own identifier
    if assigned.represented_organization and assigned.represented_organization.id:
        org_first_id = assigned.represented_organization.id[0]
        org_id = generate_id_from_identifiers(
            "Organization",
            org_first_id.root or None,
            org_first_id.extension or None,
        )
        refs.append({"reference": f"urn:uuid:{org_id}"})
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
            refs.append({"reference": f"urn:uuid:{prac_id}"})
        else:
            refs.extend(_build_device_org_fallback_refs(assigned))
    return refs
