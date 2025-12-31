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
        """Test that ID is generated from NPI identifier using standard generation."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "id" in location
        # After standardization: uses extension value with resource type prefix
        assert location["id"] == "location-1234567890"

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
        """Test ID generation for locations without identifiers (uses fallback hash)."""
        location = location_converter.convert(patient_home_location)

        assert "id" in location
        # After standardization: nullFlavor extension results in hashed root
        # ID should start with "location-" prefix
        assert location["id"].startswith("location-")
        # Should be hashed since no valid extension
        assert len(location["id"]) > len("location-")

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

    def test_name_is_always_present(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that name is always present (US Core requirement) using fallback strategies."""
        # Create location without name but with ID
        location_no_name = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC")  # No name
        )

        # Should provide fallback name (from ID)
        location = location_converter.convert(location_no_name)
        assert "name" in location
        assert location["name"] == "Location 1234567890"

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

    def test_name_fallback_to_address(
        self, location_converter: LocationConverter
    ) -> None:
        """Test fallback to address when playingEntity/name is missing."""
        location_with_address = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC"),  # No name
            addr=[
                AD(
                    street_address_line=["123 Main Street"],
                    city="Portland",
                    state="OR"
                )
            ]
        )

        location = location_converter.convert(location_with_address)
        assert "name" in location
        assert location["name"] == "Location at 123 Main Street, Portland"

    def test_name_fallback_to_address_city_only(
        self, location_converter: LocationConverter
    ) -> None:
        """Test fallback to city when street is missing."""
        location_city_only = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC"),  # No name
            addr=[AD(city="Springfield", state="IL")]
        )

        location = location_converter.convert(location_city_only)
        assert "name" in location
        assert location["name"] == "Location at Springfield"

    def test_name_fallback_to_id_with_extension(
        self, location_converter: LocationConverter
    ) -> None:
        """Test fallback to ID extension when name and address are missing."""
        location_with_id = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="FAC-9876")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC")  # No name
            # No address
        )

        location = location_converter.convert(location_with_id)
        assert "name" in location
        assert location["name"] == "Location FAC-9876"

    def test_name_fallback_to_id_oid_segment(
        self, location_converter: LocationConverter
    ) -> None:
        """Test fallback to last OID segment when extension is missing."""
        location_oid_only = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.987654")],  # No extension
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC")  # No name
            # No address
        )

        location = location_converter.convert(location_oid_only)
        assert "name" in location
        assert location["name"] == "Location 987654"

    def test_name_fallback_to_unknown(
        self, location_converter: LocationConverter
    ) -> None:
        """Test final fallback to 'Unknown Location' when all else fails."""
        location_minimal = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[],  # No IDs
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC")  # No name
            # No address
        )

        location = location_converter.convert(location_minimal)
        assert "name" in location
        assert location["name"] == "Unknown Location"

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

    def test_type_is_optional(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that type (code) is optional per FHIR R4B specification.

        Per FHIR R4B, Location.type has cardinality 0..* (optional).
        Real-world C-CDA documents may omit participantRole/code.
        """
        location_no_type = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            # Missing code
            playing_entity=PlayingEntity(class_code="PLC", name=["Test"])
        )

        # Should succeed without error
        location = location_converter.convert(location_no_type)

        # Type field should be omitted when code is missing
        assert "type" not in location

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
        """Test that mode is 'instance' for specific locations."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "mode" in location
        assert location["mode"] == "instance"

    def test_mode_kind_for_patient_home(
        self, location_converter: LocationConverter, patient_home_location: ParticipantRole
    ) -> None:
        """Test mode='kind' for patient residence (represents any patient home, not specific address)."""
        location = location_converter.convert(patient_home_location)

        assert "mode" in location
        assert location["mode"] == "kind"

    def test_mode_kind_for_ambulance(
        self, location_converter: LocationConverter
    ) -> None:
        """Test mode='kind' for ambulance (represents vehicle type, not specific ambulance)."""
        ambulance_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="9988776655")],
            code=CE(
                code="AMB",
                code_system="2.16.840.1.113883.5.111",
                display_name="Ambulance"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Ambulance Unit 5"])
        )

        location = location_converter.convert(ambulance_location)

        assert "mode" in location
        assert location["mode"] == "kind"

    def test_mode_kind_for_work_site(
        self, location_converter: LocationConverter
    ) -> None:
        """Test mode='kind' for work site (represents any workplace)."""
        work_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="WORK",
                code_system="2.16.840.1.113883.5.111",
                display_name="Work Site"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Patient's Workplace"])
        )

        location = location_converter.convert(work_location)

        assert "mode" in location
        assert location["mode"] == "kind"

    def test_mode_kind_for_school(
        self, location_converter: LocationConverter
    ) -> None:
        """Test mode='kind' for school (represents any school)."""
        school_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="SCHOOL",
                code_system="2.16.840.1.113883.5.111",
                display_name="School"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Local School"])
        )

        location = location_converter.convert(school_location)

        assert "mode" in location
        assert location["mode"] == "kind"

    def test_mode_instance_for_urgent_care(
        self, location_converter: LocationConverter, urgent_care_location: ParticipantRole
    ) -> None:
        """Test mode='instance' for specific urgent care facility."""
        location = location_converter.convert(urgent_care_location)

        assert "mode" in location
        assert location["mode"] == "instance"

    def test_mode_instance_for_emergency_department(
        self, location_converter: LocationConverter
    ) -> None:
        """Test mode='instance' for specific emergency department."""
        ed_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
            code=CE(
                code="1118-1",
                code_system="2.16.840.1.113883.6.259",
                display_name="Emergency Department"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Boston General Emergency Department"])
        )

        location = location_converter.convert(ed_location)

        assert "mode" in location
        assert location["mode"] == "instance"

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

    def test_accepts_invalid_template_id(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that invalid template IDs are accepted (lenient for real-world data)."""
        location_with_invalid_template = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="9.9.9.9.9.9")],  # Non-standard template
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test Hospital"])
        )

        # Should convert successfully despite non-standard template ID
        location = location_converter.convert(location_with_invalid_template)
        assert location is not None
        assert location["name"] == "Test Hospital"

    def test_accepts_missing_template_id(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that missing template IDs are accepted (lenient for real-world data)."""
        location_without_template = ParticipantRole(
            class_code="SDLOC",
            template_id=None,  # No template ID
            id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Community Clinic"])
        )

        # Should convert successfully despite missing template ID
        location = location_converter.convert(location_without_template)
        assert location is not None
        assert location["name"] == "Community Clinic"

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

    def test_rejects_manufactured_product_participant(
        self, location_converter: LocationConverter
    ) -> None:
        """Test that MANU (Manufactured Product) participants are rejected.

        Real-world C-CDA documents may have participants with classCode="MANU"
        (manufactured products like medications) that should not be converted to Locations.
        Only SDLOC (Service Delivery Location) participants should be accepted.
        """
        manufactured_product = ParticipantRole(
            class_code="MANU",  # Manufactured Product, not a Service Delivery Location
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.23")],  # Medication Info template
            id=[II(root="2.a6f9b1a0-8000-11db-96d0-00221122aabb", extension="12345")],
            code=CE(code="2823-3", code_system="2.16.840.1.113883.6.88"),
            playing_entity=PlayingEntity(class_code="MMAT", name=["Aspirin 81mg"])
        )

        with pytest.raises(ValueError, match="classCode"):
            location_converter.convert(manufactured_product)

    # ============================================================================
    # J. Managing Organization (4 tests)
    # ============================================================================

    def test_managing_organization_from_scoping_entity(self) -> None:
        """Test managingOrganization mapped from scopingEntity when Organization registered."""
        from ccda_to_fhir.ccda.models.participant import ScopingEntity
        from ccda_to_fhir.converters.references import ReferenceRegistry
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Generate the organization ID using the same logic as the converter
        scoping_entity_id = II(root="2.16.840.1.113883.4.6", extension="org-123")
        org_id = generate_id_from_identifiers("Organization", scoping_entity_id.root, scoping_entity_id.extension)

        # Create a reference registry and register an organization
        registry = ReferenceRegistry()
        org_resource = {
            "resourceType": "Organization",
            "id": org_id,
            "name": "Community Health System"
        }
        registry.register_resource(org_resource)

        # Create location converter with registry
        converter = LocationConverter(reference_registry=registry)

        # Create location with scopingEntity
        location_with_org = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test Hospital"]),
            scoping_entity=ScopingEntity(
                class_code="ORG",
                id=[scoping_entity_id]
            )
        )

        location = converter.convert(location_with_org)

        # Should have managingOrganization reference
        assert "managingOrganization" in location
        assert "reference" in location["managingOrganization"]
        assert location["managingOrganization"]["reference"] == f"Organization/{org_id}"

    def test_managing_organization_omitted_when_not_registered(self) -> None:
        """Test managingOrganization omitted when scopingEntity exists but Organization not registered."""
        from ccda_to_fhir.ccda.models.participant import ScopingEntity
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create a reference registry WITHOUT registering the organization
        registry = ReferenceRegistry()

        # Create location converter with registry
        converter = LocationConverter(reference_registry=registry)

        # Create location with scopingEntity
        location_with_org = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test Hospital"]),
            scoping_entity=ScopingEntity(
                class_code="ORG",
                id=[II(root="2.16.840.1.113883.4.6", extension="org-456")]
            )
        )

        location = converter.convert(location_with_org)

        # Should NOT have managingOrganization (avoids dangling reference)
        assert "managingOrganization" not in location

    def test_managing_organization_omitted_without_scoping_entity(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test managingOrganization omitted when no scopingEntity present."""
        location = location_converter.convert(sample_service_delivery_location)

        # Should NOT have managingOrganization when no scoping entity
        assert "managingOrganization" not in location

    def test_managing_organization_omitted_when_scoping_entity_has_no_id(self) -> None:
        """Test managingOrganization omitted when scopingEntity has no identifiers."""
        from ccda_to_fhir.ccda.models.participant import ScopingEntity
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create a reference registry
        registry = ReferenceRegistry()

        # Create location converter with registry
        converter = LocationConverter(reference_registry=registry)

        # Create location with scopingEntity but no ID
        location_with_org = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="1061-3", code_system="2.16.840.1.113883.6.259"),
            playing_entity=PlayingEntity(class_code="PLC", name=["Test Hospital"]),
            scoping_entity=ScopingEntity(
                class_code="ORG",
                id=None  # No identifiers
            )
        )

        location = converter.convert(location_with_org)

        # Should NOT have managingOrganization when scoping entity has no ID
        assert "managingOrganization" not in location

    # ============================================================================
    # K. Physical Type Mapping (8 tests)
    # ============================================================================

    def test_physical_type_inferred_from_hsloc_hospital(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test physicalType inferred from HSLOC hospital code (→ Building)."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "physicalType" in location
        assert "coding" in location["physicalType"]
        assert len(location["physicalType"]["coding"]) == 1

        coding = location["physicalType"]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/location-physical-type"
        assert coding["code"] == "bu"
        assert coding["display"] == "Building"

    def test_physical_type_patient_home(
        self, location_converter: LocationConverter, patient_home_location: ParticipantRole
    ) -> None:
        """Test patient residence maps to House physical type."""
        location = location_converter.convert(patient_home_location)

        assert "physicalType" in location
        coding = location["physicalType"]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/location-physical-type"
        assert coding["code"] == "ho"
        assert coding["display"] == "House"

    def test_physical_type_ambulance(
        self, location_converter: LocationConverter
    ) -> None:
        """Test ambulance maps to Vehicle physical type."""
        ambulance_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="9988776655")],
            code=CE(
                code="AMB",
                code_system="2.16.840.1.113883.5.111",
                display_name="Ambulance"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Ambulance Unit 5"])
        )

        location = location_converter.convert(ambulance_location)

        assert "physicalType" in location
        coding = location["physicalType"]["coding"][0]
        assert coding["code"] == "ve"
        assert coding["display"] == "Vehicle"

    def test_physical_type_emergency_department(
        self, location_converter: LocationConverter
    ) -> None:
        """Test emergency department maps to Ward physical type."""
        ed_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
            code=CE(
                code="1118-1",
                code_system="2.16.840.1.113883.6.259",
                display_name="Emergency Department"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Boston General Emergency Department"])
        )

        location = location_converter.convert(ed_location)

        assert "physicalType" in location
        coding = location["physicalType"]["coding"][0]
        assert coding["code"] == "wa"
        assert coding["display"] == "Ward"

    def test_physical_type_operating_room(
        self, location_converter: LocationConverter
    ) -> None:
        """Test operating room maps to Room physical type."""
        or_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1111222233")],
            code=CE(
                code="1108-2",
                code_system="2.16.840.1.113883.6.259",
                display_name="Operating Room"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["OR 3"])
        )

        location = location_converter.convert(or_location)

        assert "physicalType" in location
        coding = location["physicalType"]["coding"][0]
        assert coding["code"] == "ro"
        assert coding["display"] == "Room"

    def test_physical_type_snomed_icu(
        self, location_converter: LocationConverter
    ) -> None:
        """Test SNOMED CT ICU code maps to Ward physical type."""
        icu_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="309904001",
                code_system="2.16.840.1.113883.6.96",
                display_name="Intensive care unit"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["ICU"])
        )

        location = location_converter.convert(icu_location)

        assert "physicalType" in location
        coding = location["physicalType"]["coding"][0]
        assert coding["code"] == "wa"
        assert coding["display"] == "Ward"

    def test_physical_type_omitted_when_cannot_infer(
        self, location_converter: LocationConverter
    ) -> None:
        """Test physicalType omitted when code not in mapping."""
        # Use a code that's not in our physical type mapping
        unmapped_location = ParticipantRole(
            class_code="SDLOC",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.32")],
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="99999",  # Unmapped code
                code_system="2.16.840.1.113883.6.259",
                display_name="Unknown Facility Type"
            ),
            playing_entity=PlayingEntity(class_code="PLC", name=["Unknown Facility"])
        )

        location = location_converter.convert(unmapped_location)

        # Should NOT have physicalType when cannot infer
        assert "physicalType" not in location

    def test_physical_type_uses_standard_fhir_system(
        self, location_converter: LocationConverter, sample_service_delivery_location: ParticipantRole
    ) -> None:
        """Test physicalType uses official FHIR CodeSystem URI."""
        location = location_converter.convert(sample_service_delivery_location)

        assert "physicalType" in location
        assert location["physicalType"]["coding"][0]["system"] == \
               "http://terminology.hl7.org/CodeSystem/location-physical-type"
