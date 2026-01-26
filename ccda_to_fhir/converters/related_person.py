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
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.clinical_document import RelatedEntity
    from ccda_to_fhir.ccda.models.datatypes import CE


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

    def convert(self, ccda_model: RelatedEntity) -> FHIRResourceDict:
        """Convert RelatedEntity to RelatedPerson resource.

        Args:
            ccda_model: RelatedEntity from C-CDA Informant

        Returns:
            FHIR RelatedPerson resource as dictionary
        """
        related_entity = ccda_model  # Alias for readability
        related_person: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.RELATED_PERSON,
        }

        # Generate ID from related person name or relationship
        related_person["id"] = self._generate_related_person_id(related_entity)

        # Patient reference (required)
        related_person["patient"] = {"reference": f"urn:uuid:{self.patient_id}"}

        # Map relationship code
        if related_entity.code:
            relationship = self._convert_relationship(related_entity.code)
            if relationship:
                related_person["relationship"] = [relationship]

        # Map name
        if related_entity.related_person and related_entity.related_person.name:
            names = self.convert_human_names(related_entity.related_person.name)
            if names:
                related_person["name"] = names

        # Map telecom (phone, email)
        if related_entity.telecom:
            telecom_list = self.convert_telecom(related_entity.telecom)
            if telecom_list:
                related_person["telecom"] = telecom_list

        # Map address
        if related_entity.addr:
            addresses = self.convert_addresses(related_entity.addr)
            if addresses:
                related_person["address"] = addresses

        return related_person

    def _generate_related_person_id(self, related_entity: RelatedEntity) -> str:
        """Generate FHIR ID for RelatedPerson using UUID v4.

        Builds a cache key from available identifiers to ensure same
        RelatedEntity generates same UUID within a document.

        Args:
            related_entity: The RelatedEntity element

        Returns:
            UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Build cache key from available identifiers
        cache_key_parts = []

        # Add relationship code
        if related_entity.code and related_entity.code.code:
            cache_key_parts.append(f"code:{related_entity.code.code}")

        # Add name if available
        if related_entity.related_person and related_entity.related_person.name:
            names = related_entity.related_person.name
            if names and len(names) > 0:
                name = names[0]
                # PN has family attribute of type ENXP | None
                if name.family:
                    # ENXP has value attribute, fall back to str() if None
                    family = name.family.value if name.family.value else str(name.family)
                    cache_key_parts.append(f"family:{family}")

        # Add classCode if available
        if related_entity.class_code:
            cache_key_parts.append(f"class:{related_entity.class_code}")

        # Build final cache key (or None for fully synthetic)
        cache_key = "|".join(cache_key_parts) if cache_key_parts else None

        return generate_id_from_identifiers("RelatedPerson", cache_key, None)

    def _convert_relationship(self, code: CE) -> JSONObject:
        """Convert C-CDA relationship code to FHIR CodeableConcept.

        Args:
            code: C-CDA CE (coded element) for relationship

        Returns:
            FHIR CodeableConcept for relationship
        """
        concept: JSONObject = {"coding": []}

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

