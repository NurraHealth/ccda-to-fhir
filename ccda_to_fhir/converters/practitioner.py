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
    from ccda_to_fhir.ccda.models.datatypes import AD, II, PN, TEL
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
            names = self._convert_names(assigned.assigned_person.name)
            if names:
                practitioner["name"] = names

        # Map telecom (phone, email)
        if assigned.telecom:
            telecom_list = self._convert_telecom(assigned.telecom)
            if telecom_list:
                practitioner["telecom"] = telecom_list

        # Map address
        if assigned.addr:
            addresses = self._convert_addresses(assigned.addr)
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

    def _convert_names(self, names: list[PN]) -> list[dict[str, str | list[str]]]:
        """Convert C-CDA person names to FHIR HumanName.

        Args:
            names: List of C-CDA PN (person names)

        Returns:
            List of FHIR HumanName objects
        """
        fhir_names: list[dict[str, str | list[str]]] = []

        for name in names:
            fhir_name: dict[str, str | list[str]] = {}

            # Family name
            if name.family:
                # PN.family is ENXP (single object)
                if hasattr(name.family, "value"):
                    fhir_name["family"] = name.family.value
                else:
                    fhir_name["family"] = str(name.family)

            # Given names
            if name.given:
                # PN.given is list[ENXP]
                fhir_name["given"] = [
                    g.value if hasattr(g, "value") else str(g) for g in name.given
                ]

            # Prefix (Dr., Prof., etc.)
            if name.prefix:
                # PN.prefix is list[ENXP]
                fhir_name["prefix"] = [
                    p.value if hasattr(p, "value") else str(p) for p in name.prefix
                ]

            # Suffix (MD, PhD, etc.)
            if name.suffix:
                # PN.suffix is list[ENXP]
                fhir_name["suffix"] = [
                    s.value if hasattr(s, "value") else str(s) for s in name.suffix
                ]

            # Use code (L = Legal, P = Pseudonym, etc.)
            # C-CDA uses EntityNameUse vocabulary, FHIR uses NameUse
            # Common mappings: L → official, P → nickname, ASGN → usual
            # For simplicity, we'll omit use unless it's clearly mapped
            # (Most C-CDA names don't specify use, so this is rarely populated)

            if fhir_name:
                fhir_names.append(fhir_name)

        return fhir_names

    def _convert_telecom(self, telecoms: list[TEL]) -> list[dict[str, str]]:
        """Convert C-CDA telecom to FHIR ContactPoint.

        Args:
            telecoms: List of C-CDA TEL (telecom)

        Returns:
            List of FHIR ContactPoint objects
        """
        from ccda_to_fhir.constants import TELECOM_USE_MAP

        fhir_telecom: list[dict[str, str]] = []

        for telecom in telecoms:
            if not telecom.value:
                continue

            contact_point: dict[str, str] = {}

            # Parse value (tel:555-1234, mailto:foo@bar.com, etc.)
            value = telecom.value
            if value.startswith("tel:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value[4:]  # Remove "tel:" prefix
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]  # Remove "mailto:" prefix
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]  # Remove "fax:" prefix
            elif value.startswith("http:") or value.startswith("https:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                # Unknown format, store as-is
                contact_point["value"] = value

            # Map use code (HP = Home, WP = Work, etc.)
            if telecom.use:
                fhir_use = TELECOM_USE_MAP.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            if contact_point:
                fhir_telecom.append(contact_point)

        return fhir_telecom

    def _convert_addresses(self, addresses: list[AD]) -> list[dict[str, str | list[str]]]:
        """Convert C-CDA addresses to FHIR Address.

        Args:
            addresses: List of C-CDA AD (addresses)

        Returns:
            List of FHIR Address objects
        """
        from ccda_to_fhir.constants import ADDRESS_USE_MAP

        fhir_addresses: list[dict[str, str | list[str]]] = []

        for addr in addresses:
            fhir_address: dict[str, str | list[str]] = {}

            # Street address lines
            if addr.street_address_line:
                fhir_address["line"] = addr.street_address_line

            # City
            if addr.city:
                if isinstance(addr.city, list):
                    fhir_address["city"] = addr.city[0]
                else:
                    fhir_address["city"] = addr.city

            # State
            if addr.state:
                if isinstance(addr.state, list):
                    fhir_address["state"] = addr.state[0]
                else:
                    fhir_address["state"] = addr.state

            # Postal code
            if addr.postal_code:
                if isinstance(addr.postal_code, list):
                    fhir_address["postalCode"] = addr.postal_code[0]
                else:
                    fhir_address["postalCode"] = addr.postal_code

            # Country
            if addr.country:
                if isinstance(addr.country, list):
                    fhir_address["country"] = addr.country[0]
                else:
                    fhir_address["country"] = addr.country

            # Map use code (H = Home, WP = Work, etc.)
            if addr.use:
                fhir_use = ADDRESS_USE_MAP.get(addr.use)
                if fhir_use:
                    fhir_address["use"] = fhir_use

            if fhir_address:
                fhir_addresses.append(fhir_address)

        return fhir_addresses
