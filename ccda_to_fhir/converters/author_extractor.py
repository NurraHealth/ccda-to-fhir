"""Extract author information from C-CDA elements.

This module provides functionality to extract author metadata from various C-CDA
element types and convert it into a standardized format for Provenance generation.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.author import Author
from ccda_to_fhir.ccda.models.encounter import Encounter
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.ccda.models.procedure import Procedure
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration


class AuthorInfo:
    """Container for extracted C-CDA author information.

    This class stores author metadata extracted from C-CDA Author elements,
    including identifiers for the practitioner/device, organization, timestamps,
    and role codes.
    """

    def __init__(self, author: Author, context: str = ""):
        """Initialize AuthorInfo from a C-CDA Author element.

        Args:
            author: The C-CDA Author element
            context: Context string (e.g., "concern_act", "observation")
        """
        self.author = author
        self.context = context
        self.time: str | None = None
        self.practitioner_id: str | None = None
        self.device_id: str | None = None
        self.organization_id: str | None = None
        self.role_code: str | None = None

        self._extract_from_author()

    def _extract_from_author(self):
        """Extract fields from C-CDA Author element."""
        if not self.author:
            return

        # Extract time
        if self.author.time and self.author.time.value:
            self.time = self.author.time.value

        # Extract IDs from assignedAuthor
        if self.author.assigned_author:
            assigned = self.author.assigned_author

            # Extract practitioner ID (from assignedPerson)
            # Only create practitioner ID if we have an explicit ID with root
            if assigned.assigned_person and assigned.id:
                for id_elem in assigned.id:
                    if id_elem.root:
                        self.practitioner_id = self._generate_practitioner_id(
                            id_elem.root, id_elem.extension
                        )
                        break

            # Extract device ID (from assignedAuthoringDevice)
            elif assigned.assigned_authoring_device and assigned.id:
                for id_elem in assigned.id:
                    if id_elem.root:
                        self.device_id = self._generate_device_id(
                            id_elem.root, id_elem.extension
                        )
                        break

            # Extract organization ID
            if assigned.represented_organization and assigned.represented_organization.id:
                for id_elem in assigned.represented_organization.id:
                    if id_elem.root:
                        self.organization_id = self._generate_organization_id(
                            id_elem.root, id_elem.extension
                        )
                        break

            # Extract role code from assignedAuthor.code
            if assigned.code:
                self.role_code = assigned.code.code

        # Extract function code (takes precedence over assigned code)
        if self.author.function_code:
            self.role_code = self.author.function_code.code

    def _generate_practitioner_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Practitioner ID using cached UUID v4.

        The same (root, extension) combination will always generate the same UUID
        within a document conversion, ensuring references resolve correctly.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A cached UUID v4 string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        return generate_id_from_identifiers("Practitioner", root, extension)

    def _generate_device_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Device ID using cached UUID v4.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A cached UUID v4 string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        return generate_id_from_identifiers("Device", root, extension)

    def _generate_organization_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Organization ID using cached UUID v4.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A cached UUID v4 string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        return generate_id_from_identifiers("Organization", root, extension)


class AuthorExtractor:
    """Extract author information from C-CDA elements.

    This class provides methods to extract author metadata from various
    C-CDA element types (Act, Observation, SubstanceAdministration, Procedure)
    and combine/deduplicate authors from multiple sources.
    """

    def extract_from_concern_act(self, act: Act) -> list[AuthorInfo]:
        """Extract authors from Concern Act (Problem, Allergy).

        Args:
            act: The C-CDA Act (concern act) element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if act.author:
            for author in act.author:
                authors.append(AuthorInfo(author, context="concern_act"))
        return authors

    def extract_from_observation(self, observation: Observation) -> list[AuthorInfo]:
        """Extract authors from Observation.

        Args:
            observation: The C-CDA Observation element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if observation.author:
            for author in observation.author:
                authors.append(AuthorInfo(author, context="observation"))
        return authors

    def extract_from_substance_administration(
        self, sa: SubstanceAdministration
    ) -> list[AuthorInfo]:
        """Extract authors from SubstanceAdministration (Medication, Immunization).

        Args:
            sa: The C-CDA SubstanceAdministration element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if sa.author:
            for author in sa.author:
                authors.append(AuthorInfo(author, context="substance_administration"))
        return authors

    def extract_from_procedure(self, procedure: Procedure) -> list[AuthorInfo]:
        """Extract authors from Procedure.

        Args:
            procedure: The C-CDA Procedure element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if procedure.author:
            for author in procedure.author:
                authors.append(AuthorInfo(author, context="procedure"))
        return authors

    def extract_from_encounter(self, encounter: Encounter) -> list[AuthorInfo]:
        """Extract authors from Encounter.

        Args:
            encounter: The C-CDA Encounter element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if encounter.author:
            for author in encounter.author:
                authors.append(AuthorInfo(author, context="encounter"))
        return authors

    def extract_from_organizer(self, organizer: Organizer) -> list[AuthorInfo]:
        """Extract authors from Organizer (Result Organizer, Vital Signs Organizer).

        Args:
            organizer: The C-CDA Organizer element

        Returns:
            List of AuthorInfo objects
        """
        authors = []
        if organizer.author:
            for author in organizer.author:
                authors.append(AuthorInfo(author, context="organizer"))
        return authors

    def extract_combined(
        self,
        concern_act: Act | None,
        entry_element: Observation | SubstanceAdministration | Procedure | Act,
    ) -> list[AuthorInfo]:
        """Extract authors from both concern act and entry element, combining and deduplicating.

        Used for resources like Condition (from Problem Concern Act + Problem Observation)
        where authors may appear at multiple levels.

        Args:
            concern_act: The concern act (Act) element, or None
            entry_element: The entry element (Observation, etc.)

        Returns:
            List of unique AuthorInfo objects
        """
        all_authors = []

        # Extract from concern act
        if concern_act and concern_act.author:
            for author in concern_act.author:
                all_authors.append(AuthorInfo(author, context="concern_act"))

        # Extract from entry element
        if hasattr(entry_element, "author") and entry_element.author:
            for author in entry_element.author:
                all_authors.append(AuthorInfo(author, context="entry_element"))

        # Deduplicate by (practitioner_id or device_id, organization_id)
        seen = set()
        unique_authors = []
        for author_info in all_authors:
            key = (
                author_info.practitioner_id or author_info.device_id,
                author_info.organization_id,
            )
            if key not in seen:
                unique_authors.append(author_info)
                seen.add(key)

        return unique_authors
