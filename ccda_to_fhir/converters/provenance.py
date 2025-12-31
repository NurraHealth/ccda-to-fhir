"""Provenance converter: C-CDA author information to FHIR Provenance resource."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from ccda_to_fhir.constants import (
    CCDA_ROLE_TO_PROVENANCE_AGENT,
    FHIRCodes,
    FHIRSystems,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from .author_extractor import AuthorInfo


class ProvenanceConverter(BaseConverter[None]):
    """Convert C-CDA author information to FHIR Provenance resource.

    A Provenance resource tracks who, what, when, where, and why information
    about activity that created, revised, or deleted a resource or resources.

    This converter creates Provenance resources from C-CDA author elements,
    typically found in Problem Observations, Allergy Observations, Medications,
    Procedures, etc.

    Reference: http://hl7.org/fhir/R4/provenance.html
    """

    def convert(
        self,
        target_resource: FHIRResourceDict,
        authors: list[AuthorInfo],
    ) -> FHIRResourceDict:
        """Create Provenance resource for target resource with all authors as agents.

        Args:
            target_resource: The FHIR resource this Provenance is about
            authors: List of AuthorInfo extracted from C-CDA author elements

        Returns:
            FHIR Provenance resource as a dictionary

        Raises:
            ValueError: If target_resource missing resourceType or id
        """
        if not target_resource.get("resourceType") or not target_resource.get("id"):
            raise ValueError("Target resource must have resourceType and id")

        provenance: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.PROVENANCE,
        }

        # Generate ID from target resource using centralized generator
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        resource_type = target_resource["resourceType"]
        resource_id = target_resource["id"]
        # Use target resource type and ID as cache key for consistency
        provenance["id"] = generate_id_from_identifiers(
            "Provenance",
            f"target-{resource_type}",
            resource_id
        )

        # Target - reference to the resource(s) this Provenance is about
        provenance["target"] = [{"reference": f"{resource_type}/{resource_id}"}]

        # Recorded - when the provenance was recorded (use earliest author time)
        recorded_date = self._get_earliest_author_time(authors)
        provenance["recorded"] = recorded_date

        # Agent - who participated in the activity
        agents = []
        for author_info in authors:
            agent = self._create_agent(author_info)
            if agent:
                agents.append(agent)

        # Always include agent array (may be empty)
        provenance["agent"] = agents

        return provenance

    def _get_earliest_author_time(self, authors: list[AuthorInfo]) -> str:
        """Get earliest author time or current timestamp as fallback.

        Args:
            authors: List of AuthorInfo objects

        Returns:
            ISO datetime string
        """
        # Find earliest time from authors
        times = [author.time for author in authors if author.time]

        if times:
            # Sort chronologically and take earliest
            times.sort()
            earliest = times[0]
            # Convert C-CDA datetime format (YYYYMMDDHHmmss) to ISO
            return self.convert_date(earliest) or datetime.now().isoformat()

        # Fallback to current time
        return datetime.now().isoformat()

    def _create_agent(self, author_info: AuthorInfo) -> JSONObject | None:
        """Create Provenance.agent from AuthorInfo.

        Args:
            author_info: AuthorInfo with extracted author data

        Returns:
            FHIR Provenance.agent object or None
        """
        if not author_info.practitioner_id and not author_info.device_id:
            return None

        agent: JSONObject = {}

        # Type - role the agent played
        agent_type = self._map_role_to_agent_type(author_info.role_code)
        agent["type"] = {
            "coding": [
                {
                    "system": FHIRSystems.PROVENANCE_PARTICIPANT_TYPE,
                    "code": agent_type,
                    "display": agent_type.capitalize(),
                }
            ]
        }

        # Who - reference to Practitioner or Device
        if author_info.practitioner_id:
            agent["who"] = {
                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{author_info.practitioner_id}"
            }
        elif author_info.device_id:
            agent["who"] = {
                "reference": f"{FHIRCodes.ResourceTypes.DEVICE}/{author_info.device_id}"
            }

        # OnBehalfOf - reference to Organization (optional)
        if author_info.organization_id:
            agent["onBehalfOf"] = {
                "reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{author_info.organization_id}"
            }

        return agent

    def _map_role_to_agent_type(self, role_code: str | None) -> str:
        """Map C-CDA role/function code to FHIR Provenance agent type.

        Args:
            role_code: C-CDA role code (e.g., "AUT", "PRF", "INF")

        Returns:
            FHIR Provenance agent type code (defaults to "author")
        """
        if not role_code:
            return FHIRCodes.ProvenanceAgent.AUTHOR

        # Try direct lookup
        agent_type = CCDA_ROLE_TO_PROVENANCE_AGENT.get(role_code)
        if agent_type:
            return agent_type

        # Default to author for unknown roles
        return FHIRCodes.ProvenanceAgent.AUTHOR
