"""Unit tests for PatientConverter.

Tests comprehensive patient demographics conversion following:
- HL7 C-CDA R2.1 Implementation Guide
- US Core Patient Profile
- ONC USCDI v1/v2 requirements

All test data based on realistic clinical scenarios and official HL7 examples.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.datatypes import AD, CE, CS, ENXP, II, PN, TEL, TS
from ccda_to_fhir.ccda.models.record_target import (
    Birthplace,
    Guardian,
    GuardianPerson,
    LanguageCommunication,
    Patient,
    PatientRole,
    Place,
    RecordTarget,
)
from ccda_to_fhir.converters.patient import PatientConverter

# ============================================================================
# Fixtures - Realistic C-CDA Patient Data
# ============================================================================


@pytest.fixture
def basic_patient() -> Patient:
    """Create a basic patient with minimal required fields.

    Based on HL7 C-CDA Example: CCD.xml (Patient Demographics).
    """
    return Patient(
        name=[
            PN(
                given=[ENXP(value="John"), ENXP(value="Jacob")],
                family=ENXP(value="Smith"),
            )
        ],
        administrative_gender_code=CE(
            code="M",
            code_system="2.16.840.1.113883.5.1",  # AdministrativeGender
            display_name="Male",
        ),
        birth_time=TS(value="19630407"),
    )


@pytest.fixture
def complete_patient() -> Patient:
    """Create a patient with all demographic fields populated.

    Realistic scenario: Adult patient with complete demographics for
    primary care enrollment. Includes all US Core required elements.
    """
    return Patient(
        # Names with different use codes (legal, nickname)
        name=[
            PN(
                use="L",  # Legal
                given=[ENXP(value="Isabella"), ENXP(value="Maria")],
                family=ENXP(value="Garcia"),
            ),
            PN(
                use="P",  # Pseudonym/Nickname
                given=[ENXP(value="Bella")],
            ),
        ],
        # Gender
        administrative_gender_code=CE(
            code="F",
            code_system="2.16.840.1.113883.5.1",
            display_name="Female",
        ),
        # Birth date
        birth_time=TS(value="19850223"),
        # Marital status
        marital_status_code=CE(
            code="M",
            code_system="2.16.840.1.113883.5.2",  # MaritalStatus
            display_name="Married",
        ),
        # Language - Spanish (preferred)
        # Note: languageCode uses CS (Coded Simple) per CDA spec
        language_communication=[
            LanguageCommunication(
                language_code=CS(
                    code="es",
                    display_name="Spanish",
                ),
                preference_ind=True,
            ),
            LanguageCommunication(
                language_code=CS(
                    code="en",
                    display_name="English",
                ),
                preference_ind=False,
            ),
        ],
        # Race - Hispanic/Latino (OMB standard)
        race_code=CE(
            code="2106-3",  # White (OMB Race Category)
            code_system="2.16.840.1.113883.6.238",  # Race & Ethnicity - CDC
            display_name="White",
        ),
        # Ethnicity - Central American
        ethnic_group_code=CE(
            code="2155-0",  # Central American
            code_system="2.16.840.1.113883.6.238",
            display_name="Central American",
        ),
        # Religious affiliation
        religious_affiliation_code=CE(
            code="1013",  # Roman Catholic
            code_system="2.16.840.1.113883.5.1076",  # ReligiousAffiliation
            display_name="Roman Catholic Church",
        ),
    )


@pytest.fixture
def patient_role_with_identifiers() -> PatientRole:
    """Create patient role with realistic identifiers.

    Includes:
    - MRN (Medical Record Number) from Epic EHR
    - SSN (Social Security Number)
    - State Driver's License
    """
    return PatientRole(
        id=[
            # MRN - Most common patient identifier
            II(
                root="1.2.840.114350.1.13.297.3.7.2.686980",  # Epic OID pattern
                extension="E12345",
                assigning_authority_name="Community Health Hospital",
            ),
            # SSN - National ID
            II(
                root="2.16.840.1.113883.4.1",  # SSN OID
                extension="123-45-6789",
            ),
            # Driver's License - State ID
            II(
                root="2.16.840.1.113883.4.3.25",  # Massachusetts DL OID
                extension="S12345678",
            ),
        ],
        patient=None,  # Will be set by test
    )


@pytest.fixture
def patient_role_with_contacts() -> PatientRole:
    """Create patient role with realistic contact information.

    Includes:
    - Home address (complete with county and country)
    - Mobile phone (primary contact)
    - Home phone
    - Work email
    """
    return PatientRole(
        addr=[
            AD(
                use="HP",  # Primary Home
                street_address_line=["123 Main Street", "Apt 4B"],
                city="Boston",
                state="MA",
                postal_code="02101",
                country="USA",
            ),
            AD(
                use="WP",  # Work Place
                street_address_line=["456 Corporate Blvd", "Suite 200"],
                city="Cambridge",
                state="MA",
                postal_code="02139",
                country="USA",
            ),
        ],
        telecom=[
            TEL(
                use="MC",  # Mobile Contact
                value="tel:+1(617)555-1234",
            ),
            TEL(
                use="HP",  # Home Phone
                value="tel:+1(617)555-5678",
            ),
            TEL(
                use="WP",  # Work Email
                value="mailto:patient@example.com",
            ),
        ],
        patient=None,
    )


@pytest.fixture
def patient_with_guardian() -> tuple[Patient, Guardian]:
    """Create pediatric patient with guardian (parent).

    Realistic scenario: 8-year-old child with mother as legal guardian.
    Used for pediatric records and consent management.
    """
    child = Patient(
        name=[
            PN(
                given=[ENXP(value="Emma")],
                family=ENXP(value="Johnson"),
            )
        ],
        administrative_gender_code=CE(
            code="F",
            code_system="2.16.840.1.113883.5.1",
            display_name="Female",
        ),
        birth_time=TS(value="20160512"),  # 8 years old
    )

    guardian = Guardian(
        code=CE(
            code="MTH",  # Mother
            code_system="2.16.840.1.113883.5.111",  # RoleCode
            display_name="Mother",
        ),
        guardian_person=GuardianPerson(
            name=[
                PN(
                    given=[ENXP(value="Sarah")],
                    family=ENXP(value="Johnson"),
                )
            ],
        ),
        telecom=[
            TEL(
                use="MC",
                value="tel:+1(617)555-9999",
            )
        ],
    )

    return child, guardian


@pytest.fixture
def deceased_patient() -> Patient:
    """Create deceased patient with death date.

    Realistic scenario: Patient death recorded in system for
    mortality tracking and record closure.
    """
    return Patient(
        name=[
            PN(
                given=[ENXP(value="Robert")],
                family=ENXP(value="Williams"),
            )
        ],
        administrative_gender_code=CE(
            code="M",
            code_system="2.16.840.1.113883.5.1",
            display_name="Male",
        ),
        birth_time=TS(value="19450315"),
        sdtc_deceased_ind=True,
        sdtc_deceased_time=TS(value="20231107"),  # Died Nov 7, 2023
    )


@pytest.fixture
def patient_with_birthplace() -> tuple[Patient, Birthplace]:
    """Create patient with birthplace (international).

    Realistic scenario: Patient born in Mexico, relevant for
    public health reporting and cultural considerations.
    """
    patient = Patient(
        name=[
            PN(
                given=[ENXP(value="Carlos")],
                family=ENXP(value="Rodriguez"),
            )
        ],
        administrative_gender_code=CE(
            code="M",
            code_system="2.16.840.1.113883.5.1",
            display_name="Male",
        ),
        birth_time=TS(value="19800610"),
    )

    birthplace = Birthplace(
        place=Place(
            addr=AD(
                city="Mexico City",
                state="CDMX",
                country="Mexico",
            ),
        ),
    )

    return patient, birthplace


# ============================================================================
# Test Class: Basic Demographics
# ============================================================================


class TestBasicDemographics:
    """Test conversion of basic patient demographics.

    US Core Patient Profile required elements:
    - identifier
    - name
    - gender
    - birthDate (if known)
    """

    def test_converts_basic_patient_minimal_fields(self, basic_patient, mock_reference_registry):
        """Test patient with only required fields.

        Validates minimal compliant patient record.
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="12345")],
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Resource type
        assert result["resourceType"] == "Patient"

        # Name
        assert len(result["name"]) == 1
        assert result["name"][0]["given"] == ["John", "Jacob"]
        assert result["name"][0]["family"] == "Smith"

        # Gender
        assert result["gender"] == "male"

        # Birth date
        assert result["birthDate"] == "1963-04-07"

        # Identifier
        assert len(result["identifier"]) == 1
        assert result["identifier"][0]["value"] == "12345"

    def test_converts_complete_demographics(self, complete_patient, mock_reference_registry):
        """Test patient with all demographic fields.

        Validates comprehensive demographic capture per USCDI v2.
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="67890")],
                patient=complete_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Multiple names
        assert len(result["name"]) == 2
        assert result["name"][0]["use"] == "usual"  # L (Legal) -> usual per V3 EntityNameUse standard
        assert result["name"][0]["given"] == ["Isabella", "Maria"]
        assert result["name"][0]["family"] == "Garcia"
        assert result["name"][1]["use"] == "nickname"  # P -> nickname
        assert result["name"][1]["given"] == ["Bella"]

        # Gender
        assert result["gender"] == "female"

        # Birth date
        assert result["birthDate"] == "1985-02-23"

        # Marital status
        assert result["maritalStatus"]["coding"][0]["code"] == "M"
        assert "Married" in result["maritalStatus"]["coding"][0]["display"]

    def test_converts_multiple_languages(self, complete_patient, mock_reference_registry):
        """Test language communication preferences.

        Important for:
        - LEP (Limited English Proficiency) patients
        - Interpreter services
        - Patient materials translation
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="99999")],
                patient=complete_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Communication
        assert len(result["communication"]) == 2

        # Spanish (preferred)
        spanish = result["communication"][0]
        assert spanish["language"]["coding"][0]["code"] == "es"
        # Display is optional in FHIR Coding
        assert spanish["preferred"] is True

        # English (non-preferred)
        english = result["communication"][1]
        assert english["language"]["coding"][0]["code"] == "en"
        assert english["preferred"] is False


# ============================================================================
# Test Class: Identifiers
# ============================================================================


class TestPatientIdentifiers:
    """Test patient identifier conversion.

    Identifiers are critical for:
    - Patient matching across systems
    - Record linkage
    - Identity verification
    """

    def test_converts_mrn_identifier(self, patient_role_with_identifiers, basic_patient, mock_reference_registry):
        """Test Medical Record Number conversion.

        MRN is the primary patient identifier in most EHR systems.
        """
        patient_role_with_identifiers.patient = basic_patient

        record_target = RecordTarget(patient_role=patient_role_with_identifiers)

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Should have 3 identifiers
        assert len(result["identifier"]) == 3

        # MRN identifier
        mrn = result["identifier"][0]
        assert mrn["value"] == "E12345"
        assert "1.2.840.114350" in mrn["system"]  # Epic OID

    def test_converts_ssn_identifier(self, patient_role_with_identifiers, basic_patient, mock_reference_registry):
        """Test SSN conversion with proper type coding.

        SSN requires special handling per:
        - HIPAA privacy rules
        - V2 identifier type codes
        - Conversion to canonical FHIR URI
        """
        patient_role_with_identifiers.patient = basic_patient

        record_target = RecordTarget(patient_role=patient_role_with_identifiers)

        converter = PatientConverter()
        result = converter.convert(record_target)

        # SSN identifier - OID is converted to canonical FHIR URI
        ssn = next(i for i in result["identifier"] if "us-ssn" in i["system"])
        assert ssn["value"] == "123-45-6789"
        assert ssn["system"] == "http://hl7.org/fhir/sid/us-ssn"  # Canonical URI (not raw OID)

    def test_handles_missing_identifiers_gracefully(self, basic_patient, mock_reference_registry):
        """Test patient with no identifiers.

        Edge case: Some systems may not provide identifiers
        (e.g., unidentified patients in ED).
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[],  # No identifiers
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Should not crash, identifier field may be empty or omitted
        assert "identifier" not in result or result["identifier"] == []


# ============================================================================
# Test Class: Contact Information
# ============================================================================


class TestContactInformation:
    """Test address and telecom conversion.

    Per USCDI v2:
    - Address (required if known)
    - Phone number (required if known)
    """

    def test_converts_home_address(self, patient_role_with_contacts, basic_patient, mock_reference_registry):
        """Test home address conversion with all components.

        Address validation important for:
        - Geographic health analysis
        - Patient outreach
        - Emergency contact
        """
        patient_role_with_contacts.patient = basic_patient

        record_target = RecordTarget(patient_role=patient_role_with_contacts)

        converter = PatientConverter()
        result = converter.convert(record_target)

        assert len(result["address"]) == 2

        # Home address
        home = result["address"][0]
        assert home["use"] == "home"
        assert home["line"] == ["123 Main Street", "Apt 4B"]
        assert home["city"] == "Boston"
        assert home["state"] == "MA"
        assert home["postalCode"] == "02101"
        assert home["country"] == "USA"

    def test_converts_multiple_addresses(self, patient_role_with_contacts, basic_patient, mock_reference_registry):
        """Test multiple addresses (home + work).

        Realistic for working patients with separate contact points.
        """
        patient_role_with_contacts.patient = basic_patient

        record_target = RecordTarget(patient_role=patient_role_with_contacts)

        converter = PatientConverter()
        result = converter.convert(record_target)

        assert len(result["address"]) == 2
        assert result["address"][0]["use"] == "home"
        assert result["address"][1]["use"] == "work"

    def test_converts_telecom_with_use_codes(self, patient_role_with_contacts, basic_patient, mock_reference_registry):
        """Test phone/email conversion with proper use codes.

        Use codes critical for:
        - Knowing which number to call
        - Respecting communication preferences
        - Emergency vs routine contact
        """
        patient_role_with_contacts.patient = basic_patient

        record_target = RecordTarget(patient_role=patient_role_with_contacts)

        converter = PatientConverter()
        result = converter.convert(record_target)

        assert len(result["telecom"]) == 3

        # Mobile (primary)
        mobile = result["telecom"][0]
        assert mobile["system"] == "phone"
        assert mobile["value"] == "+1(617)555-1234"
        assert mobile["use"] == "mobile"

        # Email
        email = result["telecom"][2]
        assert email["system"] == "email"
        assert "patient@example.com" in email["value"]


# ============================================================================
# Test Class: US Core Extensions
# ============================================================================


class TestUSCoreExtensions:
    """Test US Core Patient extensions.

    US Core requires:
    - Race (OMB categories)
    - Ethnicity (OMB categories)
    - Birth sex (optional)
    """

    def test_converts_race_extension_omb_compliant(self, complete_patient, mock_reference_registry):
        """Test race extension per OMB standard.

        OMB (Office of Management and Budget) categories:
        - American Indian or Alaska Native
        - Asian
        - Black or African American
        - Native Hawaiian or Other Pacific Islander
        - White
        - Hispanic or Latino (often in ethnicity, but CDC includes here)
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="race-test")],
                patient=complete_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Find race extension
        race_ext = next(
            (e for e in result.get("extension", [])
             if "us-core-race" in e["url"]),
            None
        )

        assert race_ext is not None, "Race extension missing"

        # Should have ombCategory sub-extension
        omb_category = next(
            (e for e in race_ext["extension"] if e["url"] == "ombCategory"),
            None
        )

        assert omb_category is not None
        assert omb_category["valueCoding"]["code"] == "2106-3"
        assert "White" in omb_category["valueCoding"]["display"]

    def test_converts_ethnicity_extension_omb_compliant(self, complete_patient, mock_reference_registry):
        """Test ethnicity extension per OMB standard.

        OMB categories:
        - Hispanic or Latino
        - Not Hispanic or Latino

        Plus detailed ethnicity codes.
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="eth-test")],
                patient=complete_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Find ethnicity extension
        eth_ext = next(
            (e for e in result.get("extension", [])
             if "us-core-ethnicity" in e["url"]),
            None
        )

        assert eth_ext is not None, "Ethnicity extension missing"

        # Central American (2155-0) is a detailed ethnicity code, not an OMB category
        # OMB categories are: 2135-2 (Hispanic or Latino) or 2186-5 (Not Hispanic or Latino)
        detailed = next(
            (e for e in eth_ext["extension"] if e["url"] == "detailed"),
            None
        )

        assert detailed is not None
        assert detailed["valueCoding"]["code"] == "2155-0"
        assert "Central American" in detailed["valueCoding"]["display"]


# ============================================================================
# Test Class: Special Cases
# ============================================================================


class TestSpecialCases:
    """Test edge cases and special patient scenarios."""

    def test_converts_pediatric_patient_with_guardian(self, patient_with_guardian, mock_reference_registry):
        """Test child patient with guardian/parent.

        Pediatric records require:
        - Guardian information for consent
        - Guardian contact for communications
        - Relationship to patient
        """
        child, guardian = patient_with_guardian

        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="child-001")],
                patient=child,
            )
        )

        # Add guardian to patient role
        record_target.patient_role.patient.guardian = [guardian]

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Child demographics
        assert result["name"][0]["given"] == ["Emma"]
        assert result["birthDate"] == "2016-05-12"
        assert result["gender"] == "female"

        # Guardian as contact
        assert len(result.get("contact", [])) >= 1
        contact = result["contact"][0]

        # Relationship
        assert len(contact["relationship"]) >= 1
        assert contact["relationship"][0]["coding"][0]["code"] == "MTH"
        assert "Mother" in contact["relationship"][0]["coding"][0]["display"]

        # Guardian name
        assert contact["name"]["given"] == ["Sarah"]
        assert contact["name"]["family"] == "Johnson"

        # Guardian phone
        assert len(contact["telecom"]) >= 1

    def test_converts_deceased_patient(self, deceased_patient, mock_reference_registry):
        """Test deceased patient with death date.

        Important for:
        - Mortality statistics
        - Record closure
        - Family notifications
        """
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="deceased-001")],
                patient=deceased_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Deceased indicator
        assert "deceasedDateTime" in result or "deceasedBoolean" in result

        if "deceasedDateTime" in result:
            assert result["deceasedDateTime"] == "2023-11-07"
        elif "deceasedBoolean" in result:
            assert result["deceasedBoolean"] is True

    def test_converts_birthplace_international(self, patient_with_birthplace, mock_reference_registry):
        """Test patient born outside USA.

        Birthplace extension important for:
        - Immigration/refugee health programs
        - Cultural competence
        - Public health tracking
        """
        patient, birthplace = patient_with_birthplace

        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="bp-001")],
                patient=patient,
            )
        )

        # Add birthplace
        record_target.patient_role.patient.birthplace = birthplace

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Find birthplace extension
        bp_ext = next(
            (e for e in result.get("extension", [])
             if "patient-birthPlace" in e["url"]),
            None
        )

        assert bp_ext is not None, "Birthplace extension missing"
        assert "valueAddress" in bp_ext
        assert bp_ext["valueAddress"]["city"] == "Mexico City"
        assert bp_ext["valueAddress"]["country"] == "Mexico"


# ============================================================================
# Test Class: Error Handling
# ============================================================================


class TestErrorHandling:
    """Test converter error handling and edge cases."""

    def test_handles_missing_patient_gracefully(self, mock_reference_registry):
        """Test RecordTarget with no patient (malformed C-CDA)."""
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="error-001")],
                patient=None,  # Missing patient!
            )
        )

        converter = PatientConverter()

        with pytest.raises((ValueError, AttributeError)):
            converter.convert(record_target)

    def test_handles_invalid_gender_code(self, basic_patient, mock_reference_registry):
        """Test invalid administrative gender code.

        Per HL7, only M/F/UN are valid. Invalid codes should map to 'unknown'.
        """
        basic_patient.administrative_gender_code = CE(
            code="INVALID",
            code_system="2.16.840.1.113883.5.1",
            display_name="Invalid Gender",
        )

        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="inv-gender")],
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Should default to unknown
        assert result["gender"] == "unknown"

    def test_handles_malformed_dates(self, basic_patient, mock_reference_registry):
        """Test malformed birth date."""
        basic_patient.birth_time = TS(value="20XX0101")  # Invalid year

        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(root="2.16.840.1.113883.19.5", extension="bad-date")],
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # Should handle gracefully - either omit birthDate or return None
        assert "birthDate" not in result or result["birthDate"] is None


# ============================================================================
# Test Class: ID Generation
# ============================================================================


class TestPatientIDGeneration:
    """Test patient resource ID generation with new method."""

    def test_generates_id_from_mrn(self, basic_patient, mock_reference_registry):
        """Test ID generation from MRN extension."""
        import uuid

        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(
                    root="1.2.840.114350.1.13.297.3.7.2.686980",
                    extension="MRN12345",
                )],
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result = converter.convert(record_target)

        # ID should be a valid UUID v4
        assert "id" in result
        assert result["id"]
        # Validate UUID format
        try:
            uuid.UUID(result["id"], version=4)
        except ValueError:
            pytest.fail(f"ID {result['id']} is not a valid UUID v4")

    def test_generates_deterministic_id(self, basic_patient, mock_reference_registry):
        """Test that same input produces same ID."""
        record_target = RecordTarget(
            patient_role=PatientRole(
                id=[II(
                    root="2.16.840.1.113883.19.5",
                    extension="STABLE-ID",
                )],
                patient=basic_patient,
            )
        )

        converter = PatientConverter()
        result1 = converter.convert(record_target)
        result2 = converter.convert(record_target)

        # Same input -> same ID
        assert result1["id"] == result2["id"]
