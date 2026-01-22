"""Practitioner converter.

Converts C-CDA Author/Performer (AssignedAuthor/AssignedEntity) to FHIR Practitioner resource.

Practitioners represent healthcare providers who author, perform, or are otherwise
responsible for clinical activities.

Mapping:
- AssignedAuthor/AssignedEntity → Practitioner
- id (NPI, other identifiers) → Practitioner.identifier
- assignedPerson.name → Practitioner.name
- addr → Practitioner.address
- telecom → Practitioner.telecom

Note: AssignedAuthor/code (specialty) maps to PractitionerRole.specialty,
NOT Practitioner.qualification. See PractitionerRoleConverter.

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AuthorParticipation.html
- FHIR: https://hl7.org/fhir/R4B/practitioner.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition-us-core-practitioner.html
- Mapping: docs/mapping/09-practitioner.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import AssignedAuthor
    from ccda_to_fhir.ccda.models.datatypes import II
    from ccda_to_fhir.ccda.models.performer import AssignedEntity


class PractitionerConverter(BaseConverter["AssignedAuthor | AssignedEntity"]):
    """Convert C-CDA AssignedAuthor/AssignedEntity to FHIR Practitioner.

    Handles both Author.assignedAuthor and Performer.assignedEntity as they
    have the same structure for practitioner information.
    """

    def convert(self, assigned: AssignedAuthor | AssignedEntity) -> FHIRResourceDict:
        """Convert AssignedAuthor or AssignedEntity to Practitioner resource.

        Args:
            assigned: AssignedAuthor or AssignedEntity from C-CDA

        Returns:
            FHIR Practitioner resource as dictionary
        """
        practitioner: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.PRACTITIONER,
        }

        # Generate ID from identifiers
        if assigned.id:
            practitioner["id"] = self._generate_practitioner_id(assigned.id)

        # Map identifiers (NPI, organizational IDs, etc.)
        if assigned.id:
            identifiers = self.convert_identifiers(assigned.id)
            if identifiers:
                practitioner["identifier"] = identifiers

        # Map name
        if assigned.assigned_person and assigned.assigned_person.name:
            names = self.convert_human_names(assigned.assigned_person.name)
            if names:
                practitioner["name"] = names

        # Map telecom (phone, email)
        if assigned.telecom:
            telecom_list = self.convert_telecom(assigned.telecom)
            if telecom_list:
                practitioner["telecom"] = telecom_list

        # Map address
        if assigned.addr:
            addresses = self.convert_addresses(assigned.addr)
            if addresses:
                practitioner["address"] = addresses

        # NOTE: assignedAuthor/code (specialty) is NOT mapped here.
        # It belongs in PractitionerRole.specialty, not Practitioner.qualification.
        # Practitioner.qualification is for academic degrees (MD, PhD), not functional
        # specialties (Family Medicine, Internal Medicine).
        # See: PractitionerRoleConverter and docs/mapping/09-practitioner.md lines 133-160

        return practitioner

    def _generate_practitioner_id(self, identifiers: list[II]) -> str:
        """Generate FHIR ID using cached UUID v4 from C-CDA identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use first identifier for cache key
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("Practitioner", root, extension)

