"""Reference registry for tracking and validating FHIR resource references.

The ReferenceRegistry tracks all generated FHIR resources during conversion,
enabling validation that references point to actual resources in the Bundle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.exceptions import MissingReferenceError
from ccda_to_fhir.logging_config import get_logger

if TYPE_CHECKING:
    from ccda_to_fhir.types import FHIRResourceDict, JSONObject

logger = get_logger(__name__)


class ReferenceRegistry:
    """Registry for tracking and resolving FHIR resource references.

    This registry maintains a mapping of resource type + ID to the actual
    resource, allowing validation that references point to real resources.

    Example:
        >>> registry = ReferenceRegistry()
        >>> patient = {"resourceType": "Patient", "id": "patient-123"}
        >>> registry.register_resource(patient)
        >>>
        >>> # Later, validate a reference
        >>> ref = registry.resolve_reference("Patient", "patient-123")
        >>> # Returns: {"reference": "Patient/patient-123"}
        >>>
        >>> # Invalid reference
        >>> ref = registry.resolve_reference("Patient", "does-not-exist")
        >>> # Returns: None (and logs warning)
    """

    def __init__(self):
        """Initialize empty registry."""
        self._resources: dict[str, dict[str, FHIRResourceDict]] = {}
        self._stats = {
            "registered": 0,
            "resolved": 0,
            "failed": 0,
        }

    def register_resource(self, resource: FHIRResourceDict) -> None:
        """Register a resource in the registry.

        Args:
            resource: FHIR resource dictionary with resourceType and id
        """
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")

        if not resource_type:
            logger.warning("Cannot register resource without resourceType")
            return

        if not resource_id:
            logger.warning(
                f"Cannot register {resource_type} without id",
                extra={"resource_type": resource_type}
            )
            return

        # Initialize type bucket if needed
        if resource_type not in self._resources:
            self._resources[resource_type] = {}

        # Check for duplicates
        if resource_id in self._resources[resource_type]:
            logger.warning(
                f"Duplicate resource ID: {resource_type}/{resource_id}",
                extra={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                }
            )

        # Register the resource
        self._resources[resource_type][resource_id] = resource
        self._stats["registered"] += 1

        logger.debug(
            f"Registered {resource_type}/{resource_id}",
            extra={
                "resource_type": resource_type,
                "resource_id": resource_id,
            }
        )

    def resolve_reference(
        self,
        resource_type: str,
        resource_id: str,
    ) -> JSONObject:
        """Resolve a reference to a resource, validating it exists.

        Args:
            resource_type: The FHIR resource type (e.g., "Patient")
            resource_id: The resource ID

        Returns:
            Reference object {"reference": "ResourceType/id"}

        Raises:
            MissingReferenceError: If the referenced resource doesn't exist
        """
        # Check if resource type exists
        if resource_type not in self._resources:
            self._stats["failed"] += 1
            raise MissingReferenceError(
                resource_type=resource_type,
                resource_id=resource_id,
                context="Resource type not registered in bundle"
            )

        # Check if resource ID exists
        if resource_id not in self._resources[resource_type]:
            self._stats["failed"] += 1
            available_ids = list(self._resources[resource_type].keys())[:5]
            raise MissingReferenceError(
                resource_type=resource_type,
                resource_id=resource_id,
                context=f"Resource ID not found. Available IDs: {available_ids}"
            )

        # Resource exists - return reference
        self._stats["resolved"] += 1
        return {"reference": f"{resource_type}/{resource_id}"}

    def has_resource(self, resource_type: str, resource_id: str) -> bool:
        """Check if a resource exists in the registry.

        Args:
            resource_type: The FHIR resource type
            resource_id: The resource ID

        Returns:
            True if resource exists, False otherwise
        """
        return (
            resource_type in self._resources
            and resource_id in self._resources[resource_type]
        )

    def get_resource(
        self,
        resource_type: str,
        resource_id: str,
    ) -> FHIRResourceDict | None:
        """Get a resource from the registry.

        Args:
            resource_type: The FHIR resource type
            resource_id: The resource ID

        Returns:
            The resource dictionary if found, None otherwise
        """
        if not self.has_resource(resource_type, resource_id):
            return None

        return self._resources[resource_type][resource_id]

    def get_all_resources(self) -> list[FHIRResourceDict]:
        """Get all registered resources.

        Returns:
            List of all resources in registration order
        """
        all_resources = []
        for resource_type_dict in self._resources.values():
            all_resources.extend(resource_type_dict.values())
        return all_resources

    def get_stats(self) -> dict[str, int]:
        """Get registry statistics.

        Returns:
            Dictionary with stats: registered, resolved, failed
        """
        return self._stats.copy()

    def clear(self) -> None:
        """Clear all registered resources and reset stats."""
        self._resources.clear()
        self._stats = {
            "registered": 0,
            "resolved": 0,
            "failed": 0,
        }
