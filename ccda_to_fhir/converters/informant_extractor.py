"""Extract informant information from C-CDA elements.

This module provides functionality to extract informant metadata from various C-CDA
element types. Informants can be either healthcare providers (assignedEntity) or
related persons (relatedEntity).
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.clinical_document import Informant
from ccda_to_fhir.ccda.models.encounter import Encounter
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.ccda.models.procedure import Procedure
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration


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
        """Generate a FHIR RelatedPerson ID from C-CDA RelatedEntity.

        Args:
            related_entity: The RelatedEntity element

        Returns:
            A related person resource ID string
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
        if hasattr(related_entity, "class_code") and related_entity.class_code:
            return f"relatedperson-{related_entity.class_code.lower()}"

        # Last resort: generate synthetic UUID
        # This handles real-world C-CDA with all fields having nullFlavor
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        return generate_id_from_identifiers("RelatedPerson", None, None)


class InformantExtractor:
    """Extract informant information from C-CDA elements.

    This class provides methods to extract informant metadata from various
    C-CDA element types (Act, Observation, SubstanceAdministration, Procedure, etc.)
    """

    def extract_from_concern_act(self, act: Act) -> list[InformantInfo]:
        """Extract informants from Concern Act (Problem, Allergy).

        Args:
            act: The C-CDA Act (concern act) element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if act.informant:
            for informant in act.informant:
                informants.append(InformantInfo(informant, context="concern_act"))
        return informants

    def extract_from_observation(self, observation: Observation) -> list[InformantInfo]:
        """Extract informants from Observation.

        Args:
            observation: The C-CDA Observation element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if observation.informant:
            for informant in observation.informant:
                informants.append(InformantInfo(informant, context="observation"))
        return informants

    def extract_from_substance_administration(
        self, sa: SubstanceAdministration
    ) -> list[InformantInfo]:
        """Extract informants from SubstanceAdministration (Medication, Immunization).

        Args:
            sa: The C-CDA SubstanceAdministration element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if sa.informant:
            for informant in sa.informant:
                informants.append(InformantInfo(informant, context="substance_administration"))
        return informants

    def extract_from_procedure(self, procedure: Procedure) -> list[InformantInfo]:
        """Extract informants from Procedure.

        Args:
            procedure: The C-CDA Procedure element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if procedure.informant:
            for informant in procedure.informant:
                informants.append(InformantInfo(informant, context="procedure"))
        return informants

    def extract_from_encounter(self, encounter: Encounter) -> list[InformantInfo]:
        """Extract informants from Encounter.

        Args:
            encounter: The C-CDA Encounter element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if encounter.informant:
            for informant in encounter.informant:
                informants.append(InformantInfo(informant, context="encounter"))
        return informants

    def extract_from_organizer(self, organizer: Organizer) -> list[InformantInfo]:
        """Extract informants from Organizer (Result Organizer, Vital Signs Organizer).

        Args:
            organizer: The C-CDA Organizer element

        Returns:
            List of InformantInfo objects
        """
        informants = []
        if organizer.informant:
            for informant in organizer.informant:
                informants.append(InformantInfo(informant, context="organizer"))
        return informants

    def extract_combined(
        self,
        concern_act: Act | None,
        entry_element: Observation | SubstanceAdministration | Procedure | Act,
    ) -> list[InformantInfo]:
        """Extract informants from both concern act and entry element, combining and deduplicating.

        Used for resources like Condition (from Problem Concern Act + Problem Observation)
        where informants may appear at multiple levels.

        Args:
            concern_act: The concern act (Act) element, or None
            entry_element: The entry element (Observation, etc.)

        Returns:
            List of unique InformantInfo objects
        """
        all_informants = []

        # Extract from concern act
        if concern_act and concern_act.informant:
            for informant in concern_act.informant:
                all_informants.append(InformantInfo(informant, context="concern_act"))

        # Extract from entry element
        if hasattr(entry_element, "informant") and entry_element.informant:
            for informant in entry_element.informant:
                all_informants.append(InformantInfo(informant, context="entry_element"))

        # Deduplicate by ID
        seen = set()
        unique_informants = []
        for informant_info in all_informants:
            key = informant_info.practitioner_id or informant_info.related_person_id
            if key and key not in seen:
                unique_informants.append(informant_info)
                seen.add(key)

        return unique_informants
