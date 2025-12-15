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
def device_converter() -> DeviceConverter:
    """Create a DeviceConverter instance for testing."""
    return DeviceConverter()


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
        """Test that ID is generated from identifier extension."""
        device = device_converter.convert(sample_assigned_author_with_device)

        assert "id" in device
        assert device["id"] == "device-DEVICE-001"

    def test_generates_id_from_root_when_no_extension(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test ID generation fallback to root OID when no extension."""
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension=None)],
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        assert "id" in device
        # Should use last 16 chars of root OID (removing dots)
        assert device["id"].startswith("device-")
        assert len(device["id"]) > 7  # device- + some hash

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
        """Test device without identifiers uses fallback ID."""
        assigned_author = AssignedAuthor(
            id=None,
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        assert "id" in device
        assert device["id"] == "device-unknown"

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
        assert device["id"] == "device-DEVICE-001"
        assert len(device["deviceName"]) == 0

    def test_ignores_as_maintained_entity(
        self, device_converter: DeviceConverter, sample_device: AssignedAuthoringDevice
    ) -> None:
        """Test that asMaintainedEntity is ignored (out of scope for MVP)."""
        # Note: We're not even setting asMaintainedEntity because it's out of scope
        # This test just verifies converter works without errors when device has basic fields
        assigned_author = AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=sample_device
        )

        device = device_converter.convert(assigned_author)

        # Device should be created successfully
        assert device["resourceType"] == FHIRCodes.ResourceTypes.DEVICE
        # asMaintainedEntity should not be mapped to any FHIR field
        assert "owner" not in device  # owner would be the logical FHIR mapping
