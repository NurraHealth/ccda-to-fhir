"""Device converter.

Converts C-CDA AssignedAuthoringDevice to FHIR Device resource.

Device resources represent medical devices, software systems, or applications
that author or generate clinical information.

Mapping:
- AssignedAuthor.id → Device.identifier
- assignedAuthoringDevice.manufacturerModelName → Device.deviceName[type=manufacturer-name]
- assignedAuthoringDevice.softwareName → Device.deviceName[type=model-name]

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AuthorParticipation.html
- FHIR: https://hl7.org/fhir/R4B/device.html
- Mapping: docs/mapping/09-practitioner.md lines 396-434
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import AssignedAuthor
    from ccda_to_fhir.ccda.models.datatypes import II


class DeviceConverter(BaseConverter["AssignedAuthor"]):
    """Convert C-CDA AssignedAuthoringDevice to FHIR Device.

    Devices represent software systems or medical devices that author clinical content.
    Examples: "Epic EHR", "Cerner Millennium", automated monitoring devices.

    NOTE: This converter accepts AssignedAuthor (not just AssignedAuthoringDevice)
    to access the identifiers in AssignedAuthor.id, following the same pattern
    as PractitionerConverter.
    """

    def convert(self, assigned: AssignedAuthor) -> FHIRResourceDict:
        """Convert AssignedAuthor with assignedAuthoringDevice to Device resource.

        Args:
            assigned: AssignedAuthor from C-CDA containing assignedAuthoringDevice

        Returns:
            FHIR Device resource as dictionary
        """
        device: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.DEVICE,
        }

        # Generate ID from identifiers
        if assigned.id:
            device["id"] = self._generate_device_id(assigned.id)
        else:
            device["id"] = "device-unknown"

        # Map identifiers
        if assigned.id:
            identifiers = self.convert_identifiers(assigned.id)
            if identifiers:
                device["identifier"] = identifiers

        # Map device names (manufacturer and software)
        if assigned.assigned_authoring_device:
            device_names = self._convert_device_names(
                assigned.assigned_authoring_device.manufacturer_model_name,
                assigned.assigned_authoring_device.software_name
            )
            device["deviceName"] = device_names

        # NOTE: assignedAuthoringDevice.asMaintainedEntity is NOT mapped.
        # This field (maintaining person/org) is out of scope for MVP.
        # Future enhancement: Could map to Device.owner if needed.

        return device

    def _generate_device_id(self, identifiers: list[II]) -> str:
        """Generate FHIR ID from C-CDA identifiers.

        Strategy:
        1. Use first identifier extension if available
        2. Fall back to hash of root OID
        3. Ultimate fallback: "device-unknown"

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated ID string
        """
        if not identifiers:
            return "device-unknown"

        # Prefer first identifier with extension
        for identifier in identifiers:
            if identifier.extension:
                # Sanitize extension for use in ID
                sanitized = identifier.extension.replace(" ", "-").replace(".", "-")
                return f"device-{sanitized}"

        # Fallback: Use last 16 chars of root OID (without dots)
        if identifiers and identifiers[0].root:
            root_hash = identifiers[0].root.replace(".", "")[-16:]
            return f"device-{root_hash}"

        return "device-unknown"

    def _convert_device_names(
        self,
        manufacturer_model_name: str | None,
        software_name: str | None
    ) -> list[JSONObject]:
        """Convert device names to FHIR Device.deviceName.

        FHIR Device.deviceName is an array where each entry has:
        - name: The actual name
        - type: The type of name (manufacturer-name, model-name, etc.)

        Args:
            manufacturer_model_name: C-CDA manufacturerModelName
            software_name: C-CDA softwareName

        Returns:
            List of DeviceName objects
        """
        device_names: list[JSONObject] = []

        if manufacturer_model_name:
            device_names.append({
                "name": manufacturer_model_name,
                "type": "manufacturer-name"
            })

        if software_name:
            device_names.append({
                "name": software_name,
                "type": "model-name"
            })

        return device_names
