"""Organization converter.

Converts C-CDA RepresentedOrganization to FHIR Organization resource.

Organizations represent healthcare facilities, practices, hospitals, departments,
and other entities that provide or are involved in providing healthcare services.

Mapping:
- RepresentedOrganization → Organization
- id → Organization.identifier
- name → Organization.name
- telecom → Organization.telecom
- addr → Organization.address
- standardIndustryClassCode → Organization.type

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/
- FHIR: https://hl7.org/fhir/R4B/organization.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition-us-core-organization.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import RepresentedOrganization as AuthorOrganization
    from ccda_to_fhir.ccda.models.datatypes import CE, II, ON
    from ccda_to_fhir.ccda.models.performer import RepresentedOrganization as PerformerOrganization
    from ccda_to_fhir.ccda.models.record_target import Organization as ProviderOrganization


class OrganizationConverter(BaseConverter["AuthorOrganization | PerformerOrganization | ProviderOrganization"]):
    """Convert C-CDA RepresentedOrganization to FHIR Organization.

    Handles RepresentedOrganization from Author, Performer, and Patient contexts.
    """

    def convert(
        self, ccda_model: AuthorOrganization | PerformerOrganization | ProviderOrganization
    ) -> FHIRResourceDict:
        """Convert RepresentedOrganization to Organization resource.

        Args:
            ccda_model: RepresentedOrganization from C-CDA

        Returns:
            FHIR Organization resource as dictionary
        """
        organization = ccda_model  # Alias for readability
        org: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.ORGANIZATION,
        }

        # Generate ID from identifiers
        if organization.id:
            org["id"] = self._generate_organization_id(organization.id)

        # Map identifiers (NPI, organizational IDs, etc.)
        if organization.id:
            identifiers = self.convert_identifiers(organization.id)
            if identifiers:
                org["identifier"] = identifiers

        # Map name
        if organization.name:
            name = self._extract_name(organization.name)
            if name:
                org["name"] = name

        # Map telecom (phone, fax, email, url)
        if organization.telecom:
            telecom_list = self.convert_telecom(organization.telecom)
            if telecom_list:
                org["telecom"] = telecom_list

        # Map address
        if organization.addr:
            addresses = self.convert_addresses(organization.addr)
            if addresses:
                org["address"] = addresses

        # Map type (organization classification)
        # Note: standard_industry_class_code only exists on Author/Performer organizations, not Custodian
        if hasattr(organization, "standard_industry_class_code") and organization.standard_industry_class_code:
            org_type = self._convert_type(organization.standard_industry_class_code)
            if org_type:
                org["type"] = [org_type]

        # Default to active unless we have information otherwise
        org["active"] = True

        return org

    def _generate_organization_id(self, identifiers: list[II]) -> str:
        """Generate FHIR ID using cached UUID v4 from C-CDA identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use first identifier for cache key
        root = None
        extension = None
        if identifiers and len(identifiers) > 0:
            root = identifiers[0].root if identifiers[0].root else None
            extension = identifiers[0].extension if identifiers[0].extension else None

        return generate_id_from_identifiers("Organization", root, extension)

    def _extract_name(self, names: list[ON | str] | ON | str) -> str | None:
        """Extract organization name from C-CDA name list or single name.

        Args:
            names: List of organization names (ON objects or strings), or a single ON/str

        Returns:
            Organization name string or None
        """
        if not names:
            return None

        # Handle single name (not a list) - e.g. from CustodianOrganization
        if isinstance(names, str):
            return names

        if not isinstance(names, list):
            # It's a single ON object
            if hasattr(names, "value") and names.value:
                return names.value
            else:
                return str(names) if names else None

        # Handle list of names - get first name
        first_name = names[0]

        # Handle string names
        if isinstance(first_name, str):
            return first_name

        # Handle ON (OrganizationName) objects
        # ON has a .value field that contains the text content
        if hasattr(first_name, "value") and first_name.value:
            return first_name.value
        else:
            # Fallback to string representation
            return str(first_name) if first_name else None

    def _convert_type(self, code: CE) -> dict[str, str | list[dict[str, str]]]:
        """Convert industry classification code to FHIR Organization.type.

        Args:
            code: C-CDA CE (coded element) for organization type/classification

        Returns:
            FHIR CodeableConcept for organization type
        """
        if not code or not code.code:
            return {}

        # Map code system OID to FHIR URL
        system = None
        if code.code_system:
            system = self.map_oid_to_uri(code.code_system)

        # Create coding
        coding: dict[str, str] = {}
        if system:
            coding["system"] = system
        if code.code:
            coding["code"] = code.code
        if code.display_name:
            coding["display"] = code.display_name

        if not coding:
            return {}

        # Build CodeableConcept structure
        codeable_concept: dict[str, str | list[dict[str, str]]] = {"coding": [coding]}

        # Add original text if present
        if code.original_text:
            codeable_concept["text"] = code.original_text

        return codeable_concept
