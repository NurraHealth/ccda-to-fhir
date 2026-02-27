"""Extract informant information from C-CDA elements.

This module provides functionality to extract informant metadata from various C-CDA
element types. Informants can be either healthcare providers (assignedEntity) or
related persons (relatedEntity).
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.clinical_document import Informant
from ccda_to_fhir.converters.base_extractor import BaseParticipantExtractor


class InformantInfo:
    """Container for extracted C-CDA informant information.

    This class stores informant metadata extracted from C-CDA Informant elements,
    distinguishing between practitioner informants (assignedEntity) and
    related person informants (relatedEntity).
    """

    def __init__(self, informant: Informant, context: str = ""):
        """Initialize InformantInfo from a C-CDA Informant element.

        Args:
            informant: The C-CDA Informant element
            context: Context string (e.g., "concern_act", "observation")
        """
        self.informant = informant
        self.context = context
        self.is_practitioner: bool = False
        self.is_related_person: bool = False
        self.practitioner_id: str | None = None
        self.related_person_id: str | None = None

        self._extract_from_informant()

    def _extract_from_informant(self):
        """Extract fields from C-CDA Informant element."""
        if not self.informant:
            return

        # Check if this is a practitioner (assignedEntity)
        if self.informant.assigned_entity:
            self.is_practitioner = True
            assigned = self.informant.assigned_entity

            # Extract practitioner ID
            if assigned.id:
                for id_elem in assigned.id:
                    if id_elem.root:
                        self.practitioner_id = self._generate_practitioner_id(
                            id_elem.root, id_elem.extension
                        )
                        break

        # Check if this is a related person (relatedEntity)
        elif self.informant.related_entity:
            self.is_related_person = True
            related = self.informant.related_entity

            # Generate ID from related person info
            self.related_person_id = self._generate_related_person_id(related)

    def _generate_practitioner_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Practitioner ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _generate_related_person_id(self, related_entity) -> str:
        """Generate a FHIR RelatedPerson ID using UUID v4.

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
                if name.family:
                    family = name.family.value if name.family.value else str(name.family)
                    cache_key_parts.append(f"family:{family}")

        # Add classCode if available
        if related_entity.class_code:
            cache_key_parts.append(f"class:{related_entity.class_code}")

        # Build final cache key (or None for fully synthetic)
        cache_key = "|".join(cache_key_parts) if cache_key_parts else None

        return generate_id_from_identifiers("RelatedPerson", cache_key, None)


class InformantExtractor(BaseParticipantExtractor[InformantInfo]):
    """Extract informant information from C-CDA elements.

    This class provides methods to extract informant metadata from various
    C-CDA element types (Act, Observation, SubstanceAdministration, Procedure, etc.)

    Inherits extraction methods from BaseParticipantExtractor:
    - extract_from_concern_act
    - extract_from_observation
    - extract_from_substance_administration
    - extract_from_procedure
    - extract_from_encounter
    - extract_from_organizer
    - extract_combined
    """

    def _get_attribute_name(self) -> str:
        """Return 'informant' as the attribute to access on C-CDA elements."""
        return "informant"

    def _create_info(self, element: Informant, context: str) -> InformantInfo:
        """Create an InformantInfo from an Informant element."""
        return InformantInfo(element, context=context)

    def _get_info_id(self, info: InformantInfo) -> tuple:
        """Get unique identifier for informant deduplication.

        Uses practitioner_id or related_person_id as the key.
        """
        return (info.practitioner_id or info.related_person_id,)
