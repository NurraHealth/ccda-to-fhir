"""Device converter.

Converts C-CDA device elements to FHIR Device resource:
1. AssignedAuthoringDevice → Device (authoring systems/software)
2. Product Instance → Device (medical devices, implantable devices)

Device resources represent medical devices, software systems, or applications
that author clinical information or are used in patient care.

Mapping:
- AssignedAuthor.id → Device.identifier
- assignedAuthoringDevice.manufacturerModelName → Device.deviceName[type=manufacturer-name]
- assignedAuthoringDevice.softwareName → Device.deviceName[type=model-name]
- Product Instance participantRole → Device (with UDI, patient reference)

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AuthorParticipation.html
- C-CDA: http://hl7.org/cda/us/ccda/StructureDefinition/ProductInstance
- FHIR: https://hl7.org/fhir/R4B/device.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device
- Mapping: docs/mapping/22-device.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes, FHIRSystems
from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.utils.udi_parser import parse_udi

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import AssignedAuthor
    from ccda_to_fhir.ccda.models.datatypes import II
    from ccda_to_fhir.ccda.models.participant import ParticipantRole


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
        if not assigned.id:
            raise ValueError(
                "Cannot generate Device ID: no identifiers provided. "
                "C-CDA AssignedAuthor must have id element."
            )
        device["id"] = self._generate_device_id(assigned.id)

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

            # Add type for EHR systems (SNOMED CT 706689003)
            # Per task requirements, use SNOMED CT code 706689003 for "Electronic health record"
            # This identifies assignedAuthoringDevice elements as EHR software systems
            # Note: Device.type has "Example" binding strength per FHIR R4, allowing this usage
            device["type"] = {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "706689003",
                    "display": "Electronic health record"
                }],
                "text": "Electronic Health Record System"
            }

            # Extract and add version if available from softwareName
            version = self._extract_device_version(
                assigned.assigned_authoring_device.software_name
            )
            if version:
                device["version"] = version

        # Map owner organization from representedOrganization (if available)
        if hasattr(self, "reference_registry") and self.reference_registry:
            owner_ref = self._extract_ehr_device_owner(assigned)
            if owner_ref:
                device["owner"] = owner_ref

        return device

    def _generate_device_id(self, identifiers: list[II]) -> str:
        """Generate FHIR Device ID using cached UUID v4 from C-CDA identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use first identifier for cache key
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("Device", root, extension)

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

    def _extract_device_version(self, software_name: str | None) -> list[JSONObject] | None:
        """Extract version information from software name.

        Attempts to parse version number from software name string.
        Common patterns: "EHR System v2.1", "MyEHR 3.0.1", "System (version 1.5)"

        Per FHIR R4, Device.version is an array of BackboneElements with:
        - type (CodeableConcept, optional): The classification/category of the version
        - component (Identifier, optional): A specific component identifier
        - value (string, required): The actual version text/number

        Args:
            software_name: The software name string

        Returns:
            List of version dicts or None
        """
        if not software_name:
            return None

        import re

        # Pattern matches: v1.2, version 1.2, (1.2), 1.2.3, etc.
        version_patterns = [
            r'v\.?\s*(\d+(?:\.\d+)*)',  # v1.2 or v.1.2
            r'version\s+(\d+(?:\.\d+)*)',  # version 1.2
            r'\((\d+(?:\.\d+)*)\)',  # (1.2)
            r'\s(\d+\.\d+(?:\.\d+)?)\s*$',  # 1.2.3 at end
        ]

        for pattern in version_patterns:
            match = re.search(pattern, software_name, re.IGNORECASE)
            if match:
                version_number = match.group(1)
                return [{
                    "type": {
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/device-version-type",
                            "code": "software",
                            "display": "Software Version"
                        }],
                        "text": "software"
                    },
                    "value": version_number
                }]

        return None

    def convert_product_instance(
        self,
        participant_role: ParticipantRole,
        patient_reference: JSONObject | None = None,
        procedure_status: str | None = None
    ) -> FHIRResourceDict:
        """Convert C-CDA Product Instance to FHIR Device resource.

        Product Instance represents medical devices used in patient care,
        particularly implantable devices requiring UDI tracking.

        Args:
            participant_role: ParticipantRole containing Product Instance
            patient_reference: Optional patient reference for implantable devices
            procedure_status: Optional procedure status to infer device status

        Returns:
            FHIR Device resource as dictionary
        """
        device: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.DEVICE,
        }

        # Generate ID from identifiers
        if not participant_role.id:
            raise ValueError(
                "Cannot generate Device ID: no identifiers provided. "
                "C-CDA ParticipantRole (Product Instance) must have id element."
            )
        device["id"] = self._generate_device_id(participant_role.id)

        # Map identifiers
        if participant_role.id:
            identifiers = self.convert_identifiers(participant_role.id)
            if identifiers:
                device["identifier"] = identifiers

        # Parse UDI if present
        udi_info = self._extract_udi_info(participant_role.id)
        if udi_info:
            device["udiCarrier"] = [udi_info["udi_carrier"]]

            # Map UDI production identifiers to device fields
            if udi_info.get("manufacture_date"):
                device["manufactureDate"] = udi_info["manufacture_date"]
            if udi_info.get("expiration_date"):
                device["expirationDate"] = udi_info["expiration_date"]
            if udi_info.get("lot_number"):
                device["lotNumber"] = udi_info["lot_number"]
            if udi_info.get("serial_number"):
                device["serialNumber"] = udi_info["serial_number"]

        # Map device type code
        if participant_role.playing_device and participant_role.playing_device.code:
            code = participant_role.playing_device.code
            # Extract original text from ED object if present
            original_text = None
            if hasattr(code, "original_text") and code.original_text:
                original_text = self.extract_original_text(code.original_text)
            device["type"] = self.create_codeable_concept(
                code=code.code if hasattr(code, "code") else None,
                code_system=code.code_system if hasattr(code, "code_system") else None,
                display_name=code.display_name if hasattr(code, "display_name") else None,
                original_text=original_text
            )

        # Map device names
        if participant_role.playing_device:
            device_names = self._convert_product_instance_names(participant_role.playing_device)
            if device_names:
                device["deviceName"] = device_names

            # Map manufacturer model name to modelNumber
            if participant_role.playing_device.manufacturer_model_name:
                device["modelNumber"] = participant_role.playing_device.manufacturer_model_name

        # Map manufacturer
        if participant_role.scoping_entity and participant_role.scoping_entity.desc:
            device["manufacturer"] = participant_role.scoping_entity.desc

        # Add patient reference for implantable devices
        if patient_reference:
            device["patient"] = patient_reference
            # Apply US Core Implantable Device profile when patient reference present
            device["meta"] = {
                "profile": [
                    "http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device"
                ]
            }

        # Map status (infer from procedure status)
        device["status"] = self._infer_device_status(procedure_status)

        # Map owner organization from scopingEntity (if available)
        if hasattr(self, "reference_registry") and self.reference_registry:
            owner_ref = self._extract_device_owner(participant_role)
            if owner_ref:
                device["owner"] = owner_ref

        return device

    def _extract_udi_info(self, identifiers: list[II] | None) -> JSONObject | None:
        """Extract and parse UDI information from device identifiers.

        FDA UDI OID: 2.16.840.1.113883.3.3719

        Args:
            identifiers: List of device identifiers

        Returns:
            Dictionary with UDI carrier and parsed components, or None
        """
        if not identifiers:
            return None

        # Find UDI identifier (FDA OID)
        udi_oid = "2.16.840.1.113883.3.3719"
        udi_id = None

        for identifier in identifiers:
            if identifier.root == udi_oid and identifier.extension:
                udi_id = identifier
                break

        if not udi_id or not udi_id.extension:
            return None

        # Parse UDI string
        udi_string = udi_id.extension
        parsed = parse_udi(udi_string)

        if not parsed:
            return None

        # Build UDI carrier
        udi_carrier: JSONObject = {
            "carrierHRF": udi_string,
            "entryType": "unknown"  # Not specified in C-CDA
        }

        # Add device identifier if parsed
        if parsed.get("device_identifier"):
            udi_carrier["deviceIdentifier"] = parsed["device_identifier"]

        # Add issuer if detected
        if parsed.get("issuer"):
            udi_carrier["issuer"] = parsed["issuer"]

        # Set jurisdiction to FDA for US devices
        udi_carrier["jurisdiction"] = FHIRSystems.FDA_UDI

        result: JSONObject = {
            "udi_carrier": udi_carrier
        }

        # Add parsed production identifiers
        if parsed.get("manufacture_date"):
            result["manufacture_date"] = parsed["manufacture_date"]
        if parsed.get("expiration_date"):
            result["expiration_date"] = parsed["expiration_date"]
        if parsed.get("lot_number"):
            result["lot_number"] = parsed["lot_number"]
        if parsed.get("serial_number"):
            result["serial_number"] = parsed["serial_number"]

        return result

    def _convert_product_instance_names(self, playing_device) -> list[JSONObject]:
        """Convert Product Instance device names to FHIR Device.deviceName.

        Args:
            playing_device: PlayingDevice from ParticipantRole

        Returns:
            List of DeviceName objects
        """
        device_names: list[JSONObject] = []

        # Model name from manufacturerModelName
        if playing_device.manufacturer_model_name:
            device_names.append({
                "name": playing_device.manufacturer_model_name,
                "type": "model-name"
            })

        # User-friendly name from device code display
        if playing_device.code:
            display_name = None
            # Try original text first (extract from ED object if present)
            if hasattr(playing_device.code, "original_text") and playing_device.code.original_text:
                display_name = self.extract_original_text(playing_device.code.original_text)
            # Fall back to display name
            elif hasattr(playing_device.code, "display_name") and playing_device.code.display_name:
                display_name = playing_device.code.display_name

            if display_name:
                device_names.append({
                    "name": display_name,
                    "type": "user-friendly-name"
                })

        return device_names

    def _infer_device_status(self, procedure_status: str | None) -> str:
        """Infer FHIR Device status from procedure context.

        Args:
            procedure_status: C-CDA procedure status code

        Returns:
            FHIR Device status code
        """
        # Map C-CDA procedure status to device status
        # Per docs/mapping/22-device.md:
        # - completed procedure → active device
        # - planned/pending procedure → inactive device
        # - default → active

        if procedure_status == "completed":
            return "active"
        elif procedure_status in ("planned", "pending"):
            return "inactive"
        else:
            # Default to active for implanted/used devices
            return "active"

    def _extract_device_owner(self, participant_role: ParticipantRole) -> dict | None:
        """Extract device owner organization reference from Product Instance.

        Maps participantRole.scopingEntity to Device.owner.
        The scopingEntity represents the manufacturer or organization maintaining the device.

        Args:
            participant_role: C-CDA ParticipantRole containing scopingEntity

        Returns:
            Organization reference dict or None
        """
        if not hasattr(participant_role, "scoping_entity") or not participant_role.scoping_entity:
            return None

        scoping_entity = participant_role.scoping_entity

        # Extract organization ID from scopingEntity identifiers
        if not hasattr(scoping_entity, "id") or not scoping_entity.id:
            return None

        # Generate organization ID using same method as OrganizationConverter
        org_id = self._generate_organization_id(scoping_entity.id)

        # Check if Organization resource exists in registry
        if not self.reference_registry.has_resource("Organization", org_id):
            return None

        return {"reference": f"Organization/{org_id}"}

    def _extract_ehr_device_owner(self, assigned: AssignedAuthor) -> dict | None:
        """Extract device owner organization reference from EHR device.

        Maps assignedAuthor.representedOrganization to Device.owner.
        The representedOrganization represents the healthcare organization
        under whose authority the device operates.

        Args:
            assigned: C-CDA AssignedAuthor containing representedOrganization

        Returns:
            Organization reference dict or None
        """
        if not hasattr(assigned, "represented_organization") or not assigned.represented_organization:
            return None

        represented_org = assigned.represented_organization

        # Extract organization ID from representedOrganization identifiers
        if not hasattr(represented_org, "id") or not represented_org.id:
            return None

        # Generate organization ID using same method as OrganizationConverter
        org_id = self._generate_organization_id(represented_org.id)

        # Check if Organization resource exists in registry
        if not self.reference_registry.has_resource("Organization", org_id):
            return None

        return {"reference": f"Organization/{org_id}"}

    def _generate_organization_id(self, identifiers: list[II]) -> str:
        """Generate FHIR Organization ID using cached UUID v4 from C-CDA identifiers.

        Uses the same ID generation method as OrganizationConverter to ensure
        consistent IDs when referencing the same organization.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use first identifier for cache key
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("Organization", root, extension)
