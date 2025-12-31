"""PractitionerRole converter.

Converts C-CDA AssignedAuthor/AssignedEntity to FHIR PractitionerRole resource.

PractitionerRole links a Practitioner to an Organization and specifies the roles,
specialties, and locations where the practitioner performs services.

Key Mapping:
- AssignedAuthor/code → PractitionerRole.specialty (NOT Practitioner.qualification)
- Practitioner reference → Links to the Practitioner resource
- Organization reference → Links to the Organization resource

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AuthorParticipation.html
- FHIR: https://hl7.org/fhir/R4B/practitionerrole.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition-us-core-practitionerrole
- Mapping: docs/mapping/09-practitioner.md lines 133-160
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import AssignedAuthor
    from ccda_to_fhir.ccda.models.datatypes import CE
    from ccda_to_fhir.ccda.models.performer import AssignedEntity


class PractitionerRoleConverter(BaseConverter["AssignedAuthor | AssignedEntity"]):
    """Convert C-CDA AssignedAuthor/AssignedEntity to FHIR PractitionerRole.

    PractitionerRole links a Practitioner to an Organization with specific roles
    and specialties. This is essential for maintaining the organizational context
    of a provider's role.

    IMPORTANT: AssignedAuthor/code (specialty like "Family Medicine") maps to
    PractitionerRole.specialty, NOT Practitioner.qualification. Qualification is
    for academic degrees (MD, PhD), not functional specialties.
    """

    def convert(
        self,
        assigned: AssignedAuthor | AssignedEntity,
        practitioner_id: str,
        organization_id: str | None = None,
    ) -> FHIRResourceDict:
        """Convert AssignedAuthor or AssignedEntity to PractitionerRole resource.

        Args:
            assigned: AssignedAuthor or AssignedEntity from C-CDA
            practitioner_id: ID of the Practitioner resource to reference
            organization_id: ID of the Organization resource to reference (optional)

        Returns:
            FHIR PractitionerRole resource as dictionary

        Raises:
            ValueError: If practitioner_id is None
        """
        if not practitioner_id:
            raise ValueError("practitioner_id is required")

        practitioner_role: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.PRACTITIONER_ROLE,
        }

        # Generate ID combining practitioner and organization for uniqueness
        practitioner_role["id"] = self._generate_role_id(
            practitioner_id, organization_id
        )

        # Create reference to Practitioner
        practitioner_role["practitioner"] = self._create_practitioner_reference(
            practitioner_id
        )

        # Create reference to Organization (optional)
        if organization_id:
            practitioner_role["organization"] = self._create_organization_reference(
                organization_id
            )

        # Map specialty (assignedAuthor/code)
        if assigned.code:
            specialties = self._convert_specialty(assigned.code)
            if specialties:
                practitioner_role["specialty"] = specialties

        # Handle multiple specialties from SDTC extension (if supported)
        if hasattr(assigned, "sdtc_specialty") and assigned.sdtc_specialty:
            if "specialty" not in practitioner_role:
                practitioner_role["specialty"] = []
            for sdtc_specialty in assigned.sdtc_specialty:
                additional_specialties = self._convert_specialty(sdtc_specialty)
                if additional_specialties:
                    practitioner_role["specialty"].extend(additional_specialties)

        # Optional: Map identifiers (context-specific IDs)
        # PractitionerRole.identifier can contain identifiers specific to this role
        # This is different from Practitioner.identifier (person's identifiers)
        if assigned.id:
            identifiers = self._convert_identifiers(assigned.id)
            if identifiers:
                practitioner_role["identifier"] = identifiers

        return practitioner_role

    def _generate_role_id(self, practitioner_id: str, organization_id: str | None) -> str:
        """Generate a deterministic ID for the PractitionerRole.

        The ID combines both practitioner and organization IDs to ensure uniqueness
        and enable deduplication (same practitioner + same org = same role).
        If no organization is provided, uses only the practitioner ID.

        Args:
            practitioner_id: Practitioner resource ID
            organization_id: Organization resource ID (optional)

        Returns:
            Generated ID string
        """
        # Use a simple concatenation with separator for readability and uniqueness
        # This ensures same practitioner at different orgs gets different role IDs
        if organization_id:
            return f"role-{practitioner_id}-{organization_id}"
        else:
            return f"role-{practitioner_id}"

    def _create_practitioner_reference(self, practitioner_id: str) -> JSONObject:
        """Create a reference to the Practitioner resource.

        Args:
            practitioner_id: ID of the Practitioner resource

        Returns:
            FHIR Reference object
        """
        return {
            "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{practitioner_id}"
        }

    def _create_organization_reference(self, organization_id: str) -> JSONObject:
        """Create a reference to the Organization resource.

        Args:
            organization_id: ID of the Organization resource

        Returns:
            FHIR Reference object
        """
        return {
            "reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{organization_id}"
        }

    def _convert_specialty(self, code: CE) -> list[JSONObject]:
        """Convert specialty code to FHIR PractitionerRole.specialty.

        Maps C-CDA assignedAuthor/code (e.g., NUCC taxonomy specialty codes)
        to FHIR CodeableConcept for PractitionerRole.specialty.

        Args:
            code: C-CDA CE (coded element) for specialty

        Returns:
            List with single CodeableConcept (FHIR pattern is list)
        """
        if not code or not code.code:
            return []

        # Extract original text from ED if present
        original_text = None
        if hasattr(code, "original_text") and code.original_text:
            original_text = self.extract_original_text(code.original_text)

        # Create CodeableConcept using base converter utility
        codeable_concept = self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system,
            display_name=code.display_name,
            original_text=original_text,
        )

        if not codeable_concept:
            return []

        # PractitionerRole.specialty is an array of CodeableConcept
        return [codeable_concept]

    def _convert_identifiers(self, identifiers: list) -> list[JSONObject]:
        """Convert C-CDA identifiers to FHIR identifiers.

        Note: These are optional identifiers specific to this role/context,
        different from the Practitioner's own identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            List of FHIR Identifier objects
        """
        fhir_identifiers: list[JSONObject] = []

        for identifier in identifiers:
            if not identifier.root:
                continue

            fhir_identifier = self.create_identifier(
                root=identifier.root,
                extension=identifier.extension if hasattr(identifier, "extension") else None,
            )

            if fhir_identifier:
                fhir_identifiers.append(fhir_identifier)

        return fhir_identifiers
