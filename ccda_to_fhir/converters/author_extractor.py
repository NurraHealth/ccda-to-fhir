"""Extract author information from C-CDA elements.

This module provides functionality to extract author metadata from various C-CDA
element types and convert it into a standardized format for Provenance generation.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.author import Author
from ccda_to_fhir.converters.base_extractor import BaseParticipantExtractor


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
            # Prefer NPI (2.16.840.1.113883.4.6) over other identifiers for consistency
            # Only create practitioner ID if we have an explicit ID with root
            if assigned.assigned_person and assigned.id:
                npi_id = None
                first_id = None

                for id_elem in assigned.id:
                    if id_elem.root:
                        if not first_id:
                            first_id = id_elem
                        # Prefer NPI identifier
                        if id_elem.root == "2.16.840.1.113883.4.6":
                            npi_id = id_elem
                            break

                # Use NPI if available, otherwise use first identifier
                selected_id = npi_id if npi_id else first_id
                if selected_id:
                    self.practitioner_id = self._generate_practitioner_id(
                        selected_id.root, selected_id.extension
                    )

            # Extract device ID (from assignedAuthoringDevice)
            elif assigned.assigned_authoring_device and assigned.id:
                for id_elem in assigned.id:
                    if id_elem.root:
                        self.device_id = self._generate_device_id(
                            id_elem.root, id_elem.extension
                        )
                        break

            # Extract organization ID
            # Prefer NPI (2.16.840.1.113883.4.6) over other identifiers for consistency
            if assigned.represented_organization and assigned.represented_organization.id:
                npi_id = None
                first_id = None

                for id_elem in assigned.represented_organization.id:
                    if id_elem.root:
                        if not first_id:
                            first_id = id_elem
                        # Prefer NPI identifier
                        if id_elem.root == "2.16.840.1.113883.4.6":
                            npi_id = id_elem
                            break

                # Use NPI if available, otherwise use first identifier
                selected_id = npi_id if npi_id else first_id
                if selected_id:
                    self.organization_id = self._generate_organization_id(
                        selected_id.root, selected_id.extension
                    )

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


class AuthorExtractor(BaseParticipantExtractor[AuthorInfo]):
    """Extract author information from C-CDA elements.

    This class provides methods to extract author metadata from various
    C-CDA element types (Act, Observation, SubstanceAdministration, Procedure)
    and combine/deduplicate authors from multiple sources.

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
        """Return 'author' as the attribute to access on C-CDA elements."""
        return "author"

    def _create_info(self, element: Author, context: str) -> AuthorInfo:
        """Create an AuthorInfo from an Author element."""
        return AuthorInfo(element, context=context)

    def _get_info_id(self, info: AuthorInfo) -> tuple:
        """Get unique identifier for author deduplication.

        Uses (practitioner_id or device_id, organization_id) as the key.
        """
        return (
            info.practitioner_id or info.device_id,
            info.organization_id,
        )
