"""Unit tests for LocationConverter.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the behavior of the LocationConverter class.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.datatypes import AD, CE, II, ON, TEL
from ccda_to_fhir.ccda.models.participant import ParticipantRole, PlayingEntity
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.location import LocationConverter


@pytest.fixture
def location_converter() -> LocationConverter:
    """Create a LocationConverter instance for testing."""
    return LocationConverter()


@pytest.fixture
def sample_service_delivery_location() -> ParticipantRole:
    """Create a sample Service Delivery Location (hospital)."""
    return ParticipantRole(
        class_code="SDLOC",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
        id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
        code=CE(
            code="1061-3",
            code_system="2.16.840.1.113883.6.259",
            display_name="Hospital"
        ),
        addr=[
            AD(
                use="WP",
                street_address_line=["1001 Village Avenue"],
                city="Portland",
                state="OR",
                postal_code="99123",
                country="US"
            )
        ],
        telecom=[
            TEL(use="WP", value="tel:+1(555)555-5000")
        ],
        playing_entity=PlayingEntity(
            class_code="PLC",
            name=["Community Health and Hospitals"]
        )
    )


@pytest.fixture
def urgent_care_location() -> ParticipantRole:
    """Create an Urgent Care Center location."""
    return ParticipantRole(
        class_code="SDLOC",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
        id=[II(root="2.16.840.1.113883.4.6", extension="1122334455")],
        code=CE(
            code="1160-1",
            code_system="2.16.840.1.113883.6.259",
            display_name="Urgent Care Center"
        ),
        addr=[
            AD(
                use="WP",
                street_address_line=["123 Main Street"],
                city="Springfield",
                state="IL",
                postal_code="62701"
            )
        ],
        telecom=[TEL(use="WP", value="tel:+1(217)555-9999")],
        playing_entity=PlayingEntity(
            class_code="PLC",
            name=["Springfield Urgent Care"]
        )
    )


@pytest.fixture
def location_with_translations() -> ParticipantRole:
    """Create a location with code translations (multiple code systems)."""
    return ParticipantRole(
        class_code="SDLOC",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
        id=[
            II(root="2.16.840.1.113883.4.6", extension="1234567890"),
            II(root="2.16.840.1.113883.4.7", extension="11D0265516"),
            II(root="2.16.840.1.113883.6.300", extension="98765")
        ],
        code=CE(
            code="1061-3",
            code_system="2.16.840.1.113883.6.259",
            display_name="Hospital",
            translation=[
                CE(
                    code="22232009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Hospital"
                ),
                CE(
                    code="21",
                    code_system="https://www.cms.gov/Medicare/Coding/place-of-service-codes/Place_of_Service_Code_Set",
                    display_name="Inpatient Hospital"
                )
            ]
        ),
        addr=[
            AD(
                use="WP",
                street_address_line=["1001 Village Avenue", "Building 1, South Wing"],
                city="Portland",
                state="OR",
                postal_code="99123"
            )
        ],
        telecom=[
            TEL(use="WP", value="tel:+1(555)555-5000"),
            TEL(use="WP", value="fax:+1(555)555-5001"),
            TEL(use="WP", value="mailto:contact@hospital.example.org")
        ],
        playing_entity=PlayingEntity(
            class_code="PLC",
            name=["Community Health and Hospitals"]
        )
    )


@pytest.fixture
def patient_home_location() -> ParticipantRole:
    """Create a patient home location (no NPI identifier)."""
    return ParticipantRole(
        class_code="SDLOC",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
        id=[II(root=None, extension=None, null_flavor="NA")],
        code=CE(
            code="PTRES",
            code_system="2.16.840.1.113883.5.111",
            display_name="Patient's Residence"
        ),
        addr=[
            AD(
                use="HP",
                street_address_line=["456 Oak Street"],
                city="Seattle",
                state="WA",
                postal_code="98101"
            )
        ],
        playing_entity=PlayingEntity(
            class_code="PLC",
            name=["Patient's Home"]
        )
    )


class TestLocationConverter:
    """Unit tests for LocationConverter."""

    # ============================================================================
    # A. Basic Resource Creation (3 tests)
    # ============================================================================

    def test_creates_location_resource(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that converter creates a Location resource."""
        location = location_converter.convert(sample_service_delivery_location)

        assert location is not None
        assert location["resourceType"] == FHIRCodes.ResourceTypes.LOCATION

    def test_includes_us_core_profile(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that US Core Location profile is included in meta."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "meta" in location
        assert "profile" in location["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-location" in location["meta"]["profile"]

    def test_generates_id_from_npi(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that ID is generated from NPI identifier."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "id" in location
        assert location["id"] == "location-npi-1234567890"

    # ============================================================================
    # B. Identifier Mapping (5 tests)
    # ============================================================================

    def test_converts_npi_identifier(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that NPI identifier is converted to FHIR identifier with correct system."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "identifier" in location
        assert len(location["identifier"]) >= 1
        npi_identifiers = [i for i in location["identifier"] if i["system"] == "http://hl7.org/fhir/sid/us-npi"]
        assert len(npi_identifiers) == 1
        assert npi_identifiers[0]["value"] == "1234567890"

    def test_converts_multiple_identifiers(
        self, location_converter: LocationConverter, location_with_translations: ParticipantRole
    ) -> None:
        """Test that multiple identifiers are all converted."""
        location = location_converter.convert(location_with_translations)

        assert "identifier" in location
        assert len(location["identifier"]) == 3

        # Check NPI
        npi_ids = [i for i in location["identifier"] if i["system"] == "http://hl7.org/fhir/sid/us-npi"]
        assert len(npi_ids) == 1
        assert npi_ids[0]["value"] == "1234567890"

        # Check CLIA
        clia_ids = [i for i in location["identifier"] if i["system"] == "urn:oid:2.16.840.1.113883.4.7"]
        assert len(clia_ids) == 1
        assert clia_ids[0]["value"] == "11D0265516"

        # Check NAIC
        naic_ids = [i for i in location["identifier"] if i["system"] == "urn:oid:2.16.840.1.113883.6.300"]
        assert len(naic_ids) == 1
        assert naic_ids[0]["value"] == "98765"

    def test_identifier_oid_to_uri_mapping(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that OIDs are properly converted to URIs."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "identifier" in location
        # NPI should use standard FHIR system
        assert location["identifier"][0]["system"] == "http://hl7.org/fhir/sid/us-npi"

    def test_handles_nullflavor_identifier(
        self, location_converter: LocationConverter, patient_home_location: ParticipantRole
    ) -> None:
        """Test that nullFlavor identifiers are handled correctly."""
        location = location_converter.convert(patient_home_location)

        # Should either omit identifier or include nullFlavor representation
        # For patient home, identifier may be omitted or have nullFlavor system
        if "identifier" in location and len(location["identifier"]) > 0:
            # If included, should have nullFlavor system
            assert any(
                "terminology.hl7.org/CodeSystem/v3-NullFlavor" in i.get("system", "")
                for i in location["identifier"]
            )

    def test_id_generation_without_npi(
        self, location_converter: LocationConverter, patient_home_location: ParticipantRole
    ) -> None:
        """Test ID generation for locations without NPI (uses name-based hash)."""
        import uuid as uuid_module

        location = location_converter.convert(patient_home_location)

        assert "id" in location
        # Should be a UUID v4 when no NPI is available
        try:
            uuid_module.UUID(location["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {location['id']} is not a valid UUID v4")

    # ============================================================================
    # C. Name Mapping (3 tests)
    # ============================================================================

    def test_converts_name(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that playingEntity/name maps to Location.name (required)."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "name" in location
        assert location["name"] == "Community Health and Hospitals"

    def test_name_is_required(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that name is always present (US Core requirement)."""
        # Create location without name
        location_no_name = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC")  # No name
        )

        # Should either raise error or provide default name
        with pytest.raises(ValueError, match="name"):
            location_converter.convert(location_no_name)

    def test_handles_on_object_name(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that ON (OrganizationName) objects are properly extracted."""
        location_with_on = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(
                class_code="PLC",
                name=[ON(value="Test Hospital")]
            )
        )

        location = location_converter.convert(location_with_on)
        assert location["name"] == "Test Hospital"

    # ============================================================================
    # D. Type Mapping (5 tests)
    # ============================================================================

    def test_converts_hsloc_type(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that HSLOC codes map to Location.type with correct system URI."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "type" in location
        assert len(location["type"]) >= 1

        # Check primary coding
        primary_coding = location["type"][0]["coding"][0]
        assert primary_coding["system"] == "https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html"
        assert primary_coding["code"] == "1061-3"
        assert primary_coding["display"] == "Hospital"

    def test_converts_type_with_translations(
        self, location_converter: LocationConverter, location_with_translations: ParticipantRole
    ) -> None:
        """Test that code translations are included in type."""
        location = location_converter.convert(location_with_translations)

        assert "type" in location
        assert len(location["type"]) == 1

        # Should have 3 codings: HSLOC + 2 translations (SNOMED CT + CMS POS)
        codings = location["type"][0]["coding"]
        assert len(codings) == 3

        # Check HSLOC
        hsloc = [c for c in codings if "hsloc" in c["system"]]
        assert len(hsloc) == 1
        assert hsloc[0]["code"] == "1061-3"

        # Check SNOMED CT
        snomed = [c for c in codings if "snomed" in c["system"]]
        assert len(snomed) == 1
        assert snomed[0]["code"] == "22232009"

        # Check CMS POS
        cms = [c for c in codings if "cms.gov" in c["system"]]
        assert len(cms) == 1
        assert cms[0]["code"] == "21"

    def test_converts_snomed_ct_type(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that SNOMED CT codes use correct system URI."""
        snomed_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="22232009",
                code_system="2.16.840.1.113883.6.96",
                display_name="Hospital"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test Hospital"])
        )

        location = location_converter.convert(snomed_location)

        assert "type" in location
        assert location["type"][0]["coding"][0]["system"] == "http://snomed.info/sct"
        assert location["type"][0]["coding"][0]["code"] == "22232009"

    def test_converts_rolecode_type(
        self, location_converter: LocationConverter, patient_home_location: ParticipantRole
    ) -> None:
        """Test that RoleCode v3 codes use correct system URI."""
        location = location_converter.convert(patient_home_location)

        assert "type" in location
        assert location["type"][0]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
        assert location["type"][0]["coding"][0]["code"] == "PTRES"

    def test_type_is_required(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that type (code) is required and validated."""
        location_no_type = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            # Missing code
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        # Should either raise error or handle gracefully
        with pytest.raises(ValueError, match="code"):
            location_converter.convert(location_no_type)

    # ============================================================================
    # E. Address Mapping (4 tests)
    # ============================================================================

    def test_converts_address(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that C-CDA address maps to FHIR address."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "address" in location
        assert location["address"]["line"] == ["1001 Village Avenue"]
        assert location["address"]["city"] == "Portland"
        assert location["address"]["state"] == "OR"
        assert location["address"]["postalCode"] == "99123"

    def test_converts_address_use(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that address use codes are mapped (WP→work, HP→home)."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "address" in location
        assert location["address"]["use"] == "work"

    def test_handles_multiple_street_lines(
        self, location_converter: LocationConverter, location_with_translations: ParticipantRole
    ) -> None:
        """Test that multiple streetAddressLine elements are preserved."""
        location = location_converter.convert(location_with_translations)

        assert "address" in location
        assert len(location["address"]["line"]) == 2
        assert location["address"]["line"][0] == "1001 Village Avenue"
        assert location["address"]["line"][1] == "Building 1, South Wing"

    def test_address_is_optional(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that address is optional but should be present when available."""
        location_no_addr = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        location = location_converter.convert(location_no_addr)
        # Address should be omitted if not present in source
        assert "address" not in location

    # ============================================================================
    # F. Telecom Mapping (5 tests)
    # ============================================================================

    def test_converts_telecom(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that telecom values are converted."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "telecom" in location
        assert len(location["telecom"]) == 1
        assert location["telecom"][0]["system"] == "phone"
        assert location["telecom"][0]["value"] == "+1(555)555-5000"
        assert location["telecom"][0]["use"] == "work"

    def test_converts_multiple_telecom(
        self, location_converter: LocationConverter, location_with_translations: ParticipantRole
    ) -> None:
        """Test that multiple telecom entries are all converted."""
        location = location_converter.convert(location_with_translations)

        assert "telecom" in location
        assert len(location["telecom"]) == 3

        # Check phone
        phones = [t for t in location["telecom"] if t["system"] == "phone"]
        assert len(phones) == 1
        assert phones[0]["value"] == "+1(555)555-5000"

        # Check fax
        faxes = [t for t in location["telecom"] if t["system"] == "fax"]
        assert len(faxes) == 1
        assert faxes[0]["value"] == "+1(555)555-5001"

        # Check email
        emails = [t for t in location["telecom"] if t["system"] == "email"]
        assert len(emails) == 1
        assert emails[0]["value"] == "contact@hospital.example.org"

    def test_parses_telecom_uri_schemes(
        self, location_converter: LocationConverter, location_with_translations: ParticipantRole
    ) -> None:
        """Test that URI schemes (tel:, fax:, mailto:) are parsed correctly."""
        location = location_converter.convert(location_with_translations)

        # Should extract value without URI scheme prefix
        phones = [t for t in location["telecom"] if t["system"] == "phone"]
        # Value should not contain "tel:" prefix
        assert not phones[0]["value"].startswith("tel:")

    def test_converts_telecom_use(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that telecom use codes are mapped (WP→work)."""
        location = location_converter.convert(sample_service_delivery_location)

        assert location["telecom"][0]["use"] == "work"

    def test_telecom_is_optional(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that telecom is optional."""
        location_no_telecom = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        location = location_converter.convert(location_no_telecom)
        assert "telecom" not in location

    # ============================================================================
    # G. Status and Mode (3 tests)
    # ============================================================================

    def test_sets_status_to_active(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that status defaults to 'active'."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "status" in location
        assert location["status"] == "active"

    def test_sets_mode_to_instance(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that mode defaults to 'instance'."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "mode" in location
        assert location["mode"] == "instance"

    def test_mode_kind_for_jurisdiction(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that mode is 'kind' for jurisdiction/class types (not instances)."""
        # This is optional - only implement if we want to support jurisdiction types
        # For now, all locations are 'instance' (specific physical places)
        pass

    # ============================================================================
    # H. Template ID Validation (2 tests)
    # ============================================================================

    def test_validates_service_delivery_location_template(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that Service Delivery Location template is validated."""
        # Should convert successfully with correct template ID
        location = location_converter.convert(sample_service_delivery_location)
        assert location is not None

    def test_rejects_invalid_template_id(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that invalid template IDs are rejected."""
        invalid_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="9.9.9.9.9.9")],  # Invalid template
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        with pytest.raises(ValueError, match="template"):
            location_converter.convert(invalid_location)

    # ============================================================================
    # I. Class Code Validation (2 tests)
    # ============================================================================

    def test_validates_sdloc_class_code(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test that SDLOC classCode is validated."""
        location = location_converter.convert(sample_service_delivery_location)
        assert location is not None

    def test_rejects_invalid_class_code(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that invalid classCode values are rejected."""
        invalid_location = ParticipantRole(
            class_code="INVALID",  # Should be SDLOC
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        with pytest.raises(ValueError, match="classCode"):
            location_converter.convert(invalid_location)
