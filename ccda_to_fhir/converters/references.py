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
            # Resource already registered - this is expected with ID caching where
            # the same C-CDA identifiers generate the same UUID across multiple uses.
            # Silently skip re-registration since the resource is already tracked.
            logger.debug(
                f"Resource already registered, skipping: {resource_type}/{resource_id}",
                extra={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                }
            )
            return

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

    def has_patient(self) -> bool:
        """Check if a patient has been registered.

        Per C-CDA specification, recordTarget is required (SHALL, cardinality 1..*).
        For full C-CDA documents, patient should be extracted from recordTarget in
        the document header before clinical resources are processed.

        Returns:
            True if at least one patient is registered, False otherwise
        """
        return "Patient" in self._resources and bool(self._resources["Patient"])

    def get_patient_reference(self) -> JSONObject:
        """Get reference to the document's patient.

        Per C-CDA specification, recordTarget is required (SHALL, cardinality 1..*).
        For full C-CDA documents, patient is extracted from recordTarget in the
        document header before clinical resources are processed.

        This method returns a reference to the first registered patient. For the
        rare cases of multiple recordTargets (group encounters, conjoined twins),
        this returns the first patient.

        Returns:
            Reference object {"reference": "Patient/id"}

        Raises:
            MissingReferenceError: If no patient is registered (architectural violation)

        Example:
            >>> registry = ReferenceRegistry()
            >>> patient = {"resourceType": "Patient", "id": "patient-123"}
            >>> registry.register_resource(patient)
            >>> ref = registry.get_patient_reference()
            >>> # Returns: {"reference": "Patient/patient-123"}
        """
        if not self.has_patient():
            raise MissingReferenceError(
                resource_type="Patient",
                resource_id="(any)",
                context="Patient must be extracted from recordTarget before clinical resources. "
                        "This indicates a C-CDA document structure violation or extraction order error."
            )

        # Get first patient (for most C-CDA documents, there's only one)
        patient_id = next(iter(self._resources["Patient"].keys()))
        self._stats["resolved"] += 1
        return {"reference": f"Patient/{patient_id}"}

    def has_encounter(self) -> bool:
        """Check if an encounter has been registered.

        Returns:
            True if at least one encounter is registered, False otherwise
        """
        return "Encounter" in self._resources and bool(self._resources["Encounter"])

    def get_encounter_reference(self) -> JSONObject | None:
        """Get reference to the document's encounter if one exists.

        C-CDA documents may contain an encounter in componentOf/encompassingEncounter.
        This is optional in C-CDA, so this method returns None if no encounter
        has been registered.

        This method returns a reference to the first registered encounter.

        Returns:
            Reference object {"reference": "Encounter/id"} or None if no encounter registered

        Example:
            >>> registry = ReferenceRegistry()
            >>> encounter = {"resourceType": "Encounter", "id": "encounter-123"}
            >>> registry.register_resource(encounter)
            >>> ref = registry.get_encounter_reference()
            >>> # Returns: {"reference": "Encounter/encounter-123"}
        """
        if not self.has_encounter():
            return None

        # Get first encounter
        encounter_id = next(iter(self._resources["Encounter"].keys()))
        self._stats["resolved"] += 1
        return {"reference": f"Encounter/{encounter_id}"}

    def clear(self) -> None:
        """Clear all registered resources and reset stats."""
        self._resources.clear()
        self._stats = {
            "registered": 0,
            "resolved": 0,
            "failed": 0,
        }
