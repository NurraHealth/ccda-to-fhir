"""Unit tests for DeviceConverter.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the behavior of the DeviceConverter class.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedAuthoringDevice
from ccda_to_fhir.ccda.models.datatypes import II
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.device import DeviceConverter


@pytest.fixture
def device_converter(mock_reference_registry) -> DeviceConverter:
    """Create a DeviceConverter instance for testing."""
    return DeviceConverter(reference_registry=mock_reference_registry)


@pytest.fixture
def sample_device() -> AssignedAuthoringDevice:
    """Create a sample AssignedAuthoringDevice."""
    return AssignedAuthoringDevice(
        manufacturer_model_name="Epic EHR",
        software_name="Epic 2020"
    )


@pytest.fixture
def sample_assigned_author_with_device(sample_device: AssignedAuthoringDevice) -> AssignedAuthor:
    """Create AssignedAuthor with device and identifier."""
    return AssignedAuthor(
        id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
        assigned_authoring_device=sample_device
    )


class TestDeviceConverter:
    """Unit tests for DeviceConverter."""

    # ============================================================================
    # A. Basic Resource Creation (3 tests)
    # ============================================================================

    def test_creates_device_resource(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that converter creates a Device resource."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert device is not None
        assert device["resourceType"] == FHIRCodes.ResourceTypes.DEVICE

    def test_generates_id_from_identifier(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that ID is generated from identifier as UUID v4."""
        import uuid as uuid_module

        device = device_converter.convert(sample_assigned_author_with_device)

        assert "id" in device
        # Validate UUID format
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {device['id']} is not a valid UUID v4")

    def test_generates_id_from_root_when_no_extension(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test ID generation from root OID when no extension (UUID v4)."""
        import uuid as uuid_module

        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension=None)],
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        assert "id" in device
        # Validate UUID format
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {device['id']} is not a valid UUID v4")

    # ============================================================================
    # B. Identifier Mapping (3 tests)
    # ============================================================================

    def test_converts_identifiers(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that C-CDA identifiers are converted to FHIR identifiers."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "identifier" in device
        assert len(device["identifier"]) == 1
        assert device["identifier"][0]["system"] == "urn:oid:2.16.840.1.113883.19.5"
        assert device["identifier"][0]["value"] == "DEVICE-001"

    def test_handles_multiple_identifiers(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test handling of multiple identifiers."""
        assigned_author = AssignedAuthor(
            id=[
                II(root="2.16.840.1.113883.19.5", extension="DEVICE-001"),
                II(root="2.16.840.1.113883.19.6", extension="DEVICE-002")
            ],
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        assert "identifier" in device
        assert len(device["identifier"]) == 2
        assert device["identifier"][0]["value"] == "DEVICE-001"
        assert device["identifier"][1]["value"] == "DEVICE-002"

    def test_identifier_oid_to_uri_mapping(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that OIDs are properly converted to URIs."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "identifier" in device
        # OID should be converted to urn:oid: format
        assert device["identifier"][0]["system"].startswith("urn:oid:")

    # ============================================================================
    # C. Device Name Mapping (4 tests)
    # ============================================================================

    def test_converts_manufacturer_model_name(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that manufacturerModelName maps to deviceName with type=manufacturer-name."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "deviceName" in device
        manufacturer_names = [
            dn for dn in device["deviceName"]
            if dn.get("type") == "manufacturer-name"
        ]
        assert len(manufacturer_names) == 1
        assert manufacturer_names[0]["name"] == "Epic EHR"

    def test_converts_software_name(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that softwareName maps to deviceName with type=model-name."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "deviceName" in device
        model_names = [
            dn for dn in device["deviceName"]
            if dn.get("type") == "model-name"
        ]
        assert len(model_names) == 1
        assert model_names[0]["name"] == "Epic 2020"

    def test_includes_both_device_names(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test that both manufacturer and software names are included."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "deviceName" in device
        assert len(device["deviceName"]) == 2

        types = {dn["type"] for dn in device["deviceName"]}
        assert "manufacturer-name" in types
        assert "model-name" in types

    def test_handles_missing_device_names(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test that missing names result in empty deviceName array."""
        device_no_names = AssignedAuthoringDevice(
            manufacturer_model_name=None,
            software_name=None
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_no_names
        )

        device = device_converter.convert(assigned_author)

        assert "deviceName" in device
        assert len(device["deviceName"]) == 0

    # ============================================================================
    # D. Edge Cases (5 tests)
    # ============================================================================

    def test_device_without_identifiers(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test device without identifiers raises ValueError.

        Per FHIR R4B spec and strict validation requirements,
        Device resources require identifiers. Without identifiers,
        the converter should raise an error rather than using a placeholder.
        """
        assigned_author = AssignedAuthor(
            id=None,
            assigned_authoring_device=sample_device
        )

        with pytest.raises(ValueError, match="Cannot generate Device ID"):
            device_converter.convert(assigned_author)

    def test_device_with_only_manufacturer_name(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device with only manufacturer name (software is optional)."""
        device_only_manufacturer = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name=None
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_only_manufacturer
        )

        device = device_converter.convert(assigned_author)

        assert "deviceName" in device
        assert len(device["deviceName"]) == 1
        assert device["deviceName"][0]["name"] == "Epic EHR"
        assert device["deviceName"][0]["type"] == "manufacturer-name"

    def test_device_with_only_software_name(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device with only software name (manufacturer is optional)."""
        device_only_software = AssignedAuthoringDevice(
            manufacturer_model_name=None,
            software_name="Epic 2020"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_only_software
        )

        device = device_converter.convert(assigned_author)

        assert "deviceName" in device
        assert len(device["deviceName"]) == 1
        assert device["deviceName"][0]["name"] == "Epic 2020"
        assert device["deviceName"][0]["type"] == "model-name"

    def test_device_with_empty_assigned_authoring_device(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device with all fields None/empty."""
        import uuid as uuid_module

        device_empty = AssignedAuthoringDevice(
            manufacturer_model_name=None,
            software_name=None,
            as_maintained_entity=None
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_empty
        )

        device = device_converter.convert(assigned_author)

        # Should still create valid Device resource
        assert device["resourceType"] == FHIRCodes.ResourceTypes.DEVICE
        # Validate UUID format
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {device['id']} is not a valid UUID v4")
        assert len(device["deviceName"]) == 0

    def test_owner_from_represented_organization(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test Device.owner from representedOrganization."""
        from ccda_to_fhir.ccda.models.author import RepresentedOrganization
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Setup reference registry with organization
        registry = ReferenceRegistry()
        org_id = device_converter._generate_organization_id(
            [II(root="2.16.840.1.113883.19.5.9999.1393", extension="ORG-001")]
        )
        registry.register_resource({
            "resourceType": "Organization",
            "id": org_id,
            "name": "Community Health and Hospitals"
        })
        device_converter.reference_registry = registry

        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=sample_device,
            represented_organization=RepresentedOrganization(
                id=[II(root="2.16.840.1.113883.19.5.9999.1393", extension="ORG-001")],
                name=["Community Health and Hospitals"]
            )
        )

        device = device_converter.convert(assigned_author)

        assert "owner" in device
        assert device["owner"]["reference"] == f"Organization/{org_id}"

    def test_owner_omitted_when_no_represented_organization(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test owner omitted when representedOrganization missing."""
        from ccda_to_fhir.converters.references import ReferenceRegistry

        device_converter.reference_registry = ReferenceRegistry()

        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        assert "owner" not in device

    def test_owner_omitted_when_organization_not_registered(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test owner omitted when Organization not in registry."""
        from ccda_to_fhir.ccda.models.author import RepresentedOrganization
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Registry with no organizations
        device_converter.reference_registry = ReferenceRegistry()

        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=sample_device,
            represented_organization=RepresentedOrganization(
                id=[II(root="2.16.840.1.113883.19.5.9999.1393", extension="ORG-001")],
                name=["Community Health and Hospitals"]
            )
        )

        device = device_converter.convert(assigned_author)

        # Owner should be omitted since Organization not registered
        assert "owner" not in device

    def test_as_maintained_entity_still_ignored(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test that asMaintainedEntity is still ignored (out of scope)."""
        from ccda_to_fhir.ccda.models.author import MaintainedEntity

        # Create device with asMaintainedEntity
        # Note: We don't need to fully populate MaintainedEntity - just verify it's ignored
        device_with_maintained_entity = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name="Epic 2020",
            as_maintained_entity=MaintainedEntity()
        )

        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_with_maintained_entity
        )

        device = device_converter.convert(assigned_author)

        # Device should be created successfully
        assert device["resourceType"] == FHIRCodes.ResourceTypes.DEVICE
        # asMaintainedEntity should not be mapped (owner would be the logical mapping)
        assert "owner" not in device

    # ============================================================================
    # E. EHR Device Type and Version (8 tests)
    # ============================================================================

    def test_ehr_device_has_snomed_type_code(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test EHR device has SNOMED type code 706689003."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "type" in device
        assert "coding" in device["type"]
        assert len(device["type"]["coding"]) == 1
        assert device["type"]["coding"][0]["system"] == "http://snomed.info/sct"
        assert device["type"]["coding"][0]["code"] == "706689003"
        assert device["type"]["coding"][0]["display"] == "Electronic health record"

    def test_ehr_device_type_includes_text(
        self, device_converter: DeviceConverter, sample_assigned_author_with_device: AssignedAuthor
    ) -> None:
        """Test EHR device type includes text field."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "type" in device
        assert device["type"]["text"] == "Electronic Health Record System"

    def test_version_extraction_v_pattern(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version extracted from 'v1.2' pattern."""
        device_with_version = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name="Epic v2.1"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_with_version
        )

        device = device_converter.convert(assigned_author)

        assert "version" in device
        assert len(device["version"]) == 1
        assert device["version"][0]["value"] == "2.1"
        # Verify full CodeableConcept structure
        assert "type" in device["version"][0]
        assert "coding" in device["version"][0]["type"]
        assert len(device["version"][0]["type"]["coding"]) == 1
        assert device["version"][0]["type"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/device-version-type"
        assert device["version"][0]["type"]["coding"][0]["code"] == "software"
        assert device["version"][0]["type"]["coding"][0]["display"] == "Software Version"
        assert device["version"][0]["type"]["text"] == "software"

    def test_version_extraction_version_keyword(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version extracted from 'version 1.2' pattern."""
        device_with_version = AssignedAuthoringDevice(
            manufacturer_model_name="MyEHR",
            software_name="MyEHR version 3.0.1"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_with_version
        )

        device = device_converter.convert(assigned_author)

        assert "version" in device
        assert device["version"][0]["value"] == "3.0.1"

    def test_version_extraction_parentheses(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version extracted from '(1.5)' pattern."""
        device_with_version = AssignedAuthoringDevice(
            manufacturer_model_name="System",
            software_name="System (1.5)"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_with_version
        )

        device = device_converter.convert(assigned_author)

        assert "version" in device
        assert device["version"][0]["value"] == "1.5"

    def test_version_extraction_end_of_string(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version extracted from '1.2.3' at end of string."""
        device_with_version = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name="Epic 2020.1.5"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_with_version
        )

        device = device_converter.convert(assigned_author)

        assert "version" in device
        assert device["version"][0]["value"] == "2020.1.5"

    def test_version_not_extracted_when_no_pattern_match(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version not extracted when no recognizable pattern."""
        device_no_version = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name="Epic System"
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_no_version
        )

        device = device_converter.convert(assigned_author)

        assert "version" not in device

    def test_version_not_extracted_when_no_software_name(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test version not extracted when softwareName is None."""
        device_no_software = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name=None
        )
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=device_no_software
        )

        device = device_converter.convert(assigned_author)

        assert "version" not in device


# =============================================================================
# Product Instance Conversion Tests
# =============================================================================


class TestProductInstanceConverter:
    """Unit tests for Product Instance to Device conversion."""

    # ============================================================================
    # A. Basic Product Instance Conversion (5 tests)
    # ============================================================================

    def test_creates_device_from_product_instance(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test basic Product Instance to Device conversion."""
        from ccda_to_fhir.ccda.models.datatypes import CE, II
        from ccda_to_fhir.ccda.models.participant import (
            ParticipantRole,
            PlayingDevice,
            ScopingEntity,
        )

        # Create Product Instance
        participant_role = ParticipantRole(
            class_code="MANU",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.37")],
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            playing_device=PlayingDevice(
                code=CE(
                    code="14106009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Cardiac pacemaker"
                )
            ),
            scoping_entity=ScopingEntity(
                id=[II(root="2.16.840.1.113883.3.3719")],
                desc="Acme Devices, Inc"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert device is not None
        assert device["resourceType"] == FHIRCodes.ResourceTypes.DEVICE

    def test_generates_id_from_product_instance_identifier(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test ID generation from Product Instance identifier."""
        import uuid as uuid_module

        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "id" in device
        # Validate UUID format
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {device['id']} is not a valid UUID v4")

    def test_maps_device_identifiers(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test identifier mapping from Product Instance."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "identifier" in device
        assert len(device["identifier"]) == 1
        assert device["identifier"][0]["system"] == "urn:oid:2.16.840.1.113883.19.321"
        assert device["identifier"][0]["value"] == "DEVICE-12345"

    def test_maps_device_type_code(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device type code mapping."""
        from ccda_to_fhir.ccda.models.datatypes import CE, II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole, PlayingDevice

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            playing_device=PlayingDevice(
                code=CE(
                    code="14106009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Cardiac pacemaker"
                )
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "type" in device
        assert "coding" in device["type"]
        assert len(device["type"]["coding"]) == 1
        assert device["type"]["coding"][0]["code"] == "14106009"
        assert device["type"]["coding"][0]["display"] == "Cardiac pacemaker"

    def test_maps_manufacturer(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test manufacturer mapping from scoping entity."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import (
            ParticipantRole,
            ScopingEntity,
        )

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            scoping_entity=ScopingEntity(
                id=[II(root="2.16.840.1.113883.3.3719")],
                desc="Acme Devices, Inc"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "manufacturer" in device
        assert device["manufacturer"] == "Acme Devices, Inc"

    # ============================================================================
    # B. UDI Parsing and Mapping (6 tests)
    # ============================================================================

    def test_parses_udi_with_gs1_format(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test UDI parsing with GS1 format (complete UDI string)."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "udiCarrier" in device
        assert len(device["udiCarrier"]) == 1

        udi_carrier = device["udiCarrier"][0]
        assert udi_carrier["deviceIdentifier"] == "51022222233336"
        assert udi_carrier["carrierHRF"] == "(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
        assert udi_carrier["issuer"] == "http://hl7.org/fhir/NamingSystem/gs1-di"
        assert udi_carrier["jurisdiction"] == "http://hl7.org/fhir/NamingSystem/fda-udi"

    def test_extracts_manufacture_date_from_udi(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test manufacture date extraction from UDI."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(11)141231"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "manufactureDate" in device
        assert device["manufactureDate"] == "2014-12-31"

    def test_extracts_expiration_date_from_udi(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test expiration date extraction from UDI."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(17)150707"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "expirationDate" in device
        assert device["expirationDate"] == "2015-07-07"

    def test_extracts_lot_number_from_udi(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test lot number extraction from UDI."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(10)A213B1"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "lotNumber" in device
        assert device["lotNumber"] == "A213B1"

    def test_extracts_serial_number_from_udi(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test serial number extraction from UDI."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(21)1234"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "serialNumber" in device
        assert device["serialNumber"] == "1234"

    def test_udi_with_all_components(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test complete UDI with all production identifiers."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[
                II(
                    root="2.16.840.1.113883.3.3719",
                    extension="(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234"
                )
            ]
        )

        device = device_converter.convert_product_instance(participant_role)

        # Verify all UDI components are extracted
        assert device["manufactureDate"] == "2014-12-31"
        assert device["expirationDate"] == "2015-07-07"
        assert device["lotNumber"] == "A213B1"
        assert device["serialNumber"] == "1234"

    # ============================================================================
    # C. Device Name Mapping (3 tests)
    # ============================================================================

    def test_maps_manufacturer_model_name(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test manufacturerModelName mapping to deviceName and modelNumber."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole, PlayingDevice

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            playing_device=PlayingDevice(
                manufacturer_model_name="Model XYZ Pacemaker"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "deviceName" in device
        model_names = [dn for dn in device["deviceName"] if dn.get("type") == "model-name"]
        assert len(model_names) == 1
        assert model_names[0]["name"] == "Model XYZ Pacemaker"

        assert "modelNumber" in device
        assert device["modelNumber"] == "Model XYZ Pacemaker"

    def test_maps_device_code_display_to_user_friendly_name(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device code displayName mapping to user-friendly deviceName."""
        from ccda_to_fhir.ccda.models.datatypes import CE, II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole, PlayingDevice

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            playing_device=PlayingDevice(
                code=CE(
                    code="14106009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Cardiac pacemaker"
                )
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "deviceName" in device
        user_friendly_names = [
            dn for dn in device["deviceName"]
            if dn.get("type") == "user-friendly-name"
        ]
        assert len(user_friendly_names) == 1
        assert user_friendly_names[0]["name"] == "Cardiac pacemaker"

    def test_includes_both_model_and_user_friendly_names(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test that both model name and user-friendly name are included."""
        from ccda_to_fhir.ccda.models.datatypes import CE, II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole, PlayingDevice

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            playing_device=PlayingDevice(
                code=CE(
                    code="14106009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Cardiac pacemaker"
                ),
                manufacturer_model_name="Model XYZ Pacemaker"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "deviceName" in device
        assert len(device["deviceName"]) == 2

        types = {dn["type"] for dn in device["deviceName"]}
        assert "model-name" in types
        assert "user-friendly-name" in types

    # ============================================================================
    # D. Patient Reference and US Core Profile (4 tests)
    # ============================================================================

    def test_adds_patient_reference_when_provided(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test patient reference is added for implantable devices."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        patient_ref = {"reference": "Patient/patient-123"}
        device = device_converter.convert_product_instance(
            participant_role,
            patient_reference=patient_ref
        )

        assert "patient" in device
        assert device["patient"]["reference"] == "Patient/patient-123"

    def test_applies_us_core_profile_with_patient_reference(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test US Core Implantable Device profile is applied when patient reference present."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        patient_ref = {"reference": "Patient/patient-123"}
        device = device_converter.convert_product_instance(
            participant_role,
            patient_reference=patient_ref
        )

        assert "meta" in device
        assert "profile" in device["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-implantable-device" in device["meta"]["profile"]

    def test_no_profile_when_patient_reference_absent(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test no US Core profile when patient reference not provided."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "patient" not in device
        assert "meta" not in device

    def test_device_status_from_procedure_context(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test device status inference from procedure status."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        # Completed procedure → active device
        device = device_converter.convert_product_instance(
            participant_role,
            procedure_status="completed"
        )
        assert device["status"] == "active"

        # Planned procedure → inactive device
        device = device_converter.convert_product_instance(
            participant_role,
            procedure_status="planned"
        )
        assert device["status"] == "inactive"

    # ============================================================================
    # E. Device Owner Mapping (3 tests)
    # ============================================================================

    def test_device_owner_from_scoping_entity(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test Device.owner from scopingEntity."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import (
            ParticipantRole,
            ScopingEntity,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Setup reference registry with organization
        registry = ReferenceRegistry()
        org_id = device_converter._generate_organization_id(
            [II(root="2.16.840.1.113883.3.3719", extension="ORG-123")]
        )
        registry.register_resource({
            "resourceType": "Organization",
            "id": org_id,
            "name": "Acme Devices, Inc"
        })
        device_converter.reference_registry = registry

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            scoping_entity=ScopingEntity(
                id=[II(root="2.16.840.1.113883.3.3719", extension="ORG-123")],
                desc="Acme Devices, Inc"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "owner" in device
        assert device["owner"]["reference"] == f"Organization/{org_id}"

    def test_device_owner_omitted_when_no_scoping_entity(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test owner omitted when scopingEntity missing."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import ParticipantRole
        from ccda_to_fhir.converters.references import ReferenceRegistry

        device_converter.reference_registry = ReferenceRegistry()

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")]
        )

        device = device_converter.convert_product_instance(participant_role)

        assert "owner" not in device

    def test_device_owner_omitted_when_organization_not_registered(
        self, device_converter: DeviceConverter
    ) -> None:
        """Test owner omitted when Organization not in registry."""
        from ccda_to_fhir.ccda.models.datatypes import II
        from ccda_to_fhir.ccda.models.participant import (
            ParticipantRole,
            ScopingEntity,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Registry with no organizations
        device_converter.reference_registry = ReferenceRegistry()

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.19.321", extension="DEVICE-12345")],
            scoping_entity=ScopingEntity(
                id=[II(root="2.16.840.1.113883.3.3719", extension="ORG-123")],
                desc="Acme Devices, Inc"
            )
        )

        device = device_converter.convert_product_instance(participant_role)

        # Owner should be omitted since Organization not registered
        assert "owner" not in device
