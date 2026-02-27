"""Base extractor class for extracting participant information from C-CDA elements.

This module provides a generic base class for extractors that follow the same pattern
of extracting information (authors, informants, etc.) from various C-CDA element types.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.act import Act
    from ccda_to_fhir.ccda.models.encounter import Encounter
    from ccda_to_fhir.ccda.models.observation import Observation
    from ccda_to_fhir.ccda.models.organizer import Organizer
    from ccda_to_fhir.ccda.models.procedure import Procedure
    from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration

# Type variable for the info container class (AuthorInfo, InformantInfo, etc.)
InfoType = TypeVar("InfoType")


class BaseParticipantExtractor(ABC, Generic[InfoType]):
    """Base class for extracting participant information from C-CDA elements.

    This class provides a generic pattern for extractors that need to pull
    participant information (authors, informants, performers, etc.) from
    various C-CDA element types using a consistent interface.

    Subclasses must implement:
    - _get_attribute_name(): Returns the attribute name to access on elements (e.g., "author")
    - _create_info(): Creates the info container from the raw element and context
    - _get_info_id(): Gets the unique identifier from an info object for deduplication
    """

    @abstractmethod
    def _get_attribute_name(self) -> str:
        """Return the attribute name to access on C-CDA elements.

        Returns:
            Attribute name string (e.g., "author", "informant")
        """
        pass

    @abstractmethod
    def _create_info(self, element, context: str) -> InfoType:
        """Create an info container from a participant element.

        Args:
            element: The raw participant element (Author, Informant, etc.)
            context: Context string describing the source

        Returns:
            Info container instance
        """
        pass

    @abstractmethod
    def _get_info_id(self, info: InfoType) -> tuple:
        """Get unique identifier tuple for deduplication.

        Args:
            info: The info container

        Returns:
            Tuple that uniquely identifies this participant for deduplication
        """
        pass

    def _extract_from_element(self, element, context: str) -> list[InfoType]:
        """Generic extraction from any C-CDA element with the configured attribute.

        Args:
            element: Any C-CDA element that may have the target attribute
            context: Context string for the extraction

        Returns:
            List of info containers
        """
        items: list[InfoType] = []
        attr_name = self._get_attribute_name()

        # Use getattr with default to avoid hasattr + getattr pattern
        attr_value = getattr(element, attr_name, None)
        if attr_value:
            for item in attr_value:
                items.append(self._create_info(item, context))

        return items

    def extract_from_concern_act(self, act: Act) -> list[InfoType]:
        """Extract from Concern Act (Problem, Allergy).

        Args:
            act: The C-CDA Act (concern act) element

        Returns:
            List of info objects
        """
        return self._extract_from_element(act, "concern_act")

    def extract_from_observation(self, observation: Observation) -> list[InfoType]:
        """Extract from Observation.

        Args:
            observation: The C-CDA Observation element

        Returns:
            List of info objects
        """
        return self._extract_from_element(observation, "observation")

    def extract_from_substance_administration(
        self, sa: SubstanceAdministration
    ) -> list[InfoType]:
        """Extract from SubstanceAdministration (Medication, Immunization).

        Args:
            sa: The C-CDA SubstanceAdministration element

        Returns:
            List of info objects
        """
        return self._extract_from_element(sa, "substance_administration")

    def extract_from_procedure(self, procedure: Procedure) -> list[InfoType]:
        """Extract from Procedure.

        Args:
            procedure: The C-CDA Procedure element

        Returns:
            List of info objects
        """
        return self._extract_from_element(procedure, "procedure")

    def extract_from_encounter(self, encounter: Encounter) -> list[InfoType]:
        """Extract from Encounter.

        Args:
            encounter: The C-CDA Encounter element

        Returns:
            List of info objects
        """
        return self._extract_from_element(encounter, "encounter")

    def extract_from_organizer(self, organizer: Organizer) -> list[InfoType]:
        """Extract from Organizer (Result Organizer, Vital Signs Organizer).

        Args:
            organizer: The C-CDA Organizer element

        Returns:
            List of info objects
        """
        return self._extract_from_element(organizer, "organizer")

    def extract_combined(
        self,
        concern_act: Act | None,
        entry_element: Observation | SubstanceAdministration | Procedure | Act,
    ) -> list[InfoType]:
        """Extract from both concern act and entry element, combining and deduplicating.

        Used for resources like Condition (from Problem Concern Act + Problem Observation)
        where participants may appear at multiple levels.

        Args:
            concern_act: The concern act (Act) element, or None
            entry_element: The entry element (Observation, etc.)

        Returns:
            List of unique info objects
        """
        all_items: list[InfoType] = []
        attr_name = self._get_attribute_name()

        # Extract from concern act
        if concern_act:
            attr_value = getattr(concern_act, attr_name, None)
            if attr_value:
                for item in attr_value:
                    all_items.append(self._create_info(item, "concern_act"))

        # Extract from entry element
        attr_value = getattr(entry_element, attr_name, None)
        if attr_value:
            for item in attr_value:
                all_items.append(self._create_info(item, "entry_element"))

        # Deduplicate by ID (skip if key is all None - handles both 1 and 2-element tuples)
        seen: set[tuple] = set()
        unique_items: list[InfoType] = []
        for info in all_items:
            key = self._get_info_id(info)
            if any(k is not None for k in key) and key not in seen:
                unique_items.append(info)
                seen.add(key)

        return unique_items
