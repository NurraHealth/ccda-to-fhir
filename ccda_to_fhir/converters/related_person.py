"""RelatedPerson converter.

Converts C-CDA Informant (RelatedEntity) to FHIR RelatedPerson resource.

RelatedPersons represent non-provider informants such as family members,
caregivers, or the patient themselves who provide information for the document.

Mapping:
- Informant.relatedEntity → RelatedPerson
- relatedEntity.code → RelatedPerson.relationship
- relatedEntity.relatedPerson.name → RelatedPerson.name
- relatedEntity.addr → RelatedPerson.address
- relatedEntity.telecom → RelatedPerson.telecom

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/
- FHIR: https://hl7.org/fhir/R4/relatedperson.html
- Mapping: docs/mapping/09-participations.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes, FHIRSystems
from ccda_to_fhir.types import FHIRResourceDict

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.clinical_document import RelatedEntity
    from ccda_to_fhir.ccda.models.datatypes import AD, CE, PN, TEL


class RelatedPersonConverter(BaseConverter["RelatedEntity"]):
    """Convert C-CDA RelatedEntity to FHIR RelatedPerson.

    Handles Informant.relatedEntity which represents non-provider
    sources of information (family members, caregivers, patient).
    """

    def __init__(self, patient_id: str):
        """Initialize RelatedPersonConverter.

        Args:
            patient_id: The FHIR Patient ID to reference
        """
        super().__init__()
        self.patient_id = patient_id

    def convert(self, related_entity: RelatedEntity) -> FHIRResourceDict:
        """Convert RelatedEntity to RelatedPerson resource.

        Args:
            related_entity: RelatedEntity from C-CDA Informant

        Returns:
            FHIR RelatedPerson resource as dictionary
        """
        related_person: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.RELATED_PERSON,
        }

        # Generate ID from related person name or relationship
        related_person["id"] = self._generate_related_person_id(related_entity)

        # Patient reference (required)
        related_person["patient"] = {"reference": f"Patient/{self.patient_id}"}

        # Map relationship code
        if related_entity.code:
            relationship = self._convert_relationship(related_entity.code)
            if relationship:
                related_person["relationship"] = [relationship]

        # Map name
        if related_entity.related_person and related_entity.related_person.name:
            names = self._convert_names(related_entity.related_person.name)
            if names:
                related_person["name"] = names

        # Map telecom (phone, email)
        if related_entity.telecom:
            telecom_list = self._convert_telecom(related_entity.telecom)
            if telecom_list:
                related_person["telecom"] = telecom_list

        # Map address
        if related_entity.addr:
            addresses = self._convert_addresses(related_entity.addr)
            if addresses:
                related_person["address"] = addresses

        return related_person

    def _generate_related_person_id(self, related_entity: RelatedEntity) -> str:
        """Generate FHIR ID for RelatedPerson.

        Args:
            related_entity: The RelatedEntity element

        Returns:
            Generated ID string
        """
        # Try to use relationship code
        if related_entity.code and related_entity.code.code:
            code = related_entity.code.code.lower().replace(" ", "-")
            return f"relatedperson-{code}"

        # Try to use name
        if related_entity.related_person and related_entity.related_person.name:
            names = related_entity.related_person.name
            if names and len(names) > 0:
                name = names[0]
                if hasattr(name, "family") and name.family:
                    family = (
                        name.family.value
                        if hasattr(name.family, "value")
                        else str(name.family)
                    )
                    return f"relatedperson-{family.lower().replace(' ', '-')}"

        # Fallback: use classCode if available (e.g., PAT, NOK, PRS)
        if related_entity.class_code:
            return f"relatedperson-{related_entity.class_code.lower()}"

        # Last resort: generate synthetic UUID
        # This handles real-world C-CDA with all fields having nullFlavor
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        return generate_id_from_identifiers("RelatedPerson", None, None)

    def _convert_relationship(self, code: CE) -> dict[str, list[dict[str, str]]]:
        """Convert C-CDA relationship code to FHIR CodeableConcept.

        Args:
            code: C-CDA CE (coded element) for relationship

        Returns:
            FHIR CodeableConcept for relationship
        """
        concept: dict[str, list[dict[str, str]]] = {"coding": []}

        if code.code:
            coding: dict[str, str] = {}

            # Map system
            if code.code_system:
                # V3 RoleCode is the typical system for C-CDA relationship codes
                if code.code_system == "2.16.840.1.113883.5.111":
                    coding["system"] = FHIRSystems.V3_ROLE_CODE
                else:
                    coding["system"] = self.map_oid_to_uri(code.code_system)
            else:
                # Default to V3 RoleCode if not specified
                coding["system"] = FHIRSystems.V3_ROLE_CODE

            coding["code"] = code.code

            if code.display_name:
                coding["display"] = code.display_name

            concept["coding"].append(coding)

        if code.display_name:
            concept["text"] = code.display_name

        return concept

    def _convert_names(
        self, names: list[PN]
    ) -> list[dict[str, str | list[str]]]:
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
                if hasattr(name.family, "value"):
                    fhir_name["family"] = name.family.value
                else:
                    fhir_name["family"] = str(name.family)

            # Given names
            if name.given:
                fhir_name["given"] = [
                    g.value if hasattr(g, "value") else str(g) for g in name.given
                ]

            # Prefix (Mr., Mrs., etc.)
            if name.prefix:
                fhir_name["prefix"] = [
                    p.value if hasattr(p, "value") else str(p) for p in name.prefix
                ]

            # Suffix (Jr., Sr., etc.)
            if name.suffix:
                fhir_name["suffix"] = [
                    s.value if hasattr(s, "value") else str(s) for s in name.suffix
                ]

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
                contact_point["value"] = value[4:]
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]
            elif value.startswith("http:") or value.startswith("https:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                contact_point["value"] = value

            # Map use code (HP = Home, WP = Work, etc.)
            if telecom.use:
                fhir_use = TELECOM_USE_MAP.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            if contact_point:
                fhir_telecom.append(contact_point)

        return fhir_telecom

    def _convert_addresses(
        self, addresses: list[AD]
    ) -> list[dict[str, str | list[str]]]:
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
