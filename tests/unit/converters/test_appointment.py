"""Unit tests for Appointment converter.

Tests C-CDA Planned Encounter (V2) to FHIR Appointment resource conversion
following:
- HL7 C-CDA R2.1 Planned Encounter template (2.16.840.1.113883.10.20.22.4.40)
- FHIR R4B Appointment resource spec
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor, Author
from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, II, IVL_TS, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.appointment import AppointmentConverter
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.types import FHIRReference

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_reference_registry() -> ReferenceRegistry:
    """Create a mock reference registry."""
    registry = Mock(spec=ReferenceRegistry)
    registry.get_patient_reference = Mock(
        return_value=FHIRReference(reference="urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
    registry.get_encounter_reference = Mock(return_value=None)
    registry.has_resource = Mock(return_value=True)
    return registry


@pytest.fixture
def basic_appointment() -> CCDAEncounter:
    """Basic planned encounter with APT moodCode."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="APT",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="appt-001")],
        code=CD(
            code="185389009",
            code_system="2.16.840.1.113883.6.96",
            display_name="Follow-up visit",
        ),
        status_code=CS(code="active"),
        effective_time=IVL_TS(
            low=TS(value="20240615100000"),
            high=TS(value="20240615110000"),
        ),
    )


@pytest.fixture
def appointment_request() -> CCDAEncounter:
    """Planned encounter with ARQ (appointment request) moodCode."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="ARQ",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="appt-002")],
        code=CD(
            code="11429006",
            code_system="2.16.840.1.113883.6.96",
            display_name="Consultation",
        ),
        status_code=CS(code="new"),
    )


@pytest.fixture
def appointment_with_priority() -> CCDAEncounter:
    """Planned encounter with priority code."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="APT",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="appt-003")],
        code=CD(
            code="185389009",
            code_system="2.16.840.1.113883.6.96",
            display_name="Follow-up visit",
        ),
        status_code=CS(code="active"),
        priority_code=CE(
            code="UR",
            code_system="2.16.840.1.113883.5.7",
            display_name="Urgent",
        ),
    )


@pytest.fixture
def appointment_with_author() -> CCDAEncounter:
    """Planned encounter with author (order/submit date)."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="APT",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="appt-004")],
        code=CD(
            code="185389009",
            code_system="2.16.840.1.113883.6.96",
            display_name="Follow-up visit",
        ),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20240615")),
        author=[
            Author(
                time=TS(value="20240601140000-0500"),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                ),
            )
        ],
    )


@pytest.fixture
def appointment_with_performer() -> CCDAEncounter:
    """Planned encounter with performer (provider)."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="APT",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="appt-005")],
        code=CD(
            code="185389009",
            code_system="2.16.840.1.113883.6.96",
            display_name="Follow-up visit",
        ),
        status_code=CS(code="active"),
        performer=[
            Performer(
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
                ),
            )
        ],
    )


# ============================================================================
# MoodCode Validation Tests
# ============================================================================


class TestMoodCodeValidation:
    """Test moodCode validation for appointment conversion."""

    def test_apt_mood_code_accepted(self, basic_appointment, mock_reference_registry):
        """APT moodCode should produce an Appointment resource."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert result["resourceType"] == FHIRCodes.ResourceTypes.APPOINTMENT

    def test_arq_mood_code_accepted(self, appointment_request, mock_reference_registry):
        """ARQ moodCode should produce an Appointment resource."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(appointment_request)
        assert result["resourceType"] == FHIRCodes.ResourceTypes.APPOINTMENT

    def test_int_mood_code_rejected(self, mock_reference_registry):
        """INT moodCode should be rejected (not an appointment)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="INT",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
            id=[II(root="test-root", extension="test-ext")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="not an appointment moodCode"):
            converter.convert(enc)

    def test_evn_mood_code_rejected(self, mock_reference_registry):
        """EVN moodCode should be rejected."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
            id=[II(root="test-root", extension="test-ext")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="not an appointment moodCode"):
            converter.convert(enc)

    def test_missing_mood_code_raises(self, mock_reference_registry):
        """Missing moodCode should raise ValueError."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code=None,
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
            id=[II(root="test-root", extension="test-ext")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="must have a moodCode"):
            converter.convert(enc)


# ============================================================================
# Status Mapping Tests
# ============================================================================


class TestStatusMapping:
    """Test status code to FHIR Appointment status mapping."""

    def test_apt_active_maps_to_booked(self, mock_reference_registry):
        """APT + active → booked."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "booked"

    def test_arq_new_maps_to_proposed(self, mock_reference_registry):
        """ARQ + new → proposed."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="new"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "proposed"

    def test_completed_maps_to_fulfilled(self, mock_reference_registry):
        """completed → fulfilled."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="completed"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "fulfilled"

    def test_cancelled_maps_to_cancelled(self, mock_reference_registry):
        """cancelled → cancelled."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="cancelled"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "cancelled"

    def test_aborted_maps_to_cancelled(self, mock_reference_registry):
        """aborted → cancelled."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="aborted"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "cancelled"

    def test_no_status_code_defaults_from_mood(self, mock_reference_registry):
        """Missing statusCode → default from moodCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=None,
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "proposed"

    def test_null_flavor_status_defaults_from_mood(self, mock_reference_registry):
        """nullFlavor statusCode → default from moodCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(null_flavor="UNK"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "booked"


# ============================================================================
# Timing Tests
# ============================================================================


class TestTiming:
    """Test effectiveTime to start/end mapping."""

    def test_period_with_low_high(self, basic_appointment, mock_reference_registry):
        """effectiveTime with low+high → start+end."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "start" in result
        assert "end" in result

    def test_point_in_time(self, mock_reference_registry):
        """effectiveTime with just value → start only."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(value="20240615100000"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" in result
        assert "end" not in result

    def test_no_effective_time(self, mock_reference_registry):
        """No effectiveTime → no start/end."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" not in result
        assert "end" not in result


# ============================================================================
# Service Type Tests
# ============================================================================


class TestServiceType:
    """Test encounter code to serviceType mapping."""

    def test_service_type_from_code(self, basic_appointment, mock_reference_registry):
        """Encounter code maps to serviceType."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "serviceType" in result
        assert result["serviceType"][0]["coding"][0]["code"] == "185389009"

    def test_no_code_no_service_type(self, mock_reference_registry):
        """Missing code → no serviceType."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "serviceType" not in result


# ============================================================================
# Priority Tests
# ============================================================================


class TestPriority:
    """Test priorityCode to FHIR Appointment priority mapping."""

    def test_urgent_priority(self, appointment_with_priority, mock_reference_registry):
        """UR → priority=2 (high)."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(appointment_with_priority)
        assert result["priority"] == 2

    def test_routine_priority(self, mock_reference_registry):
        """R → priority=5 (normal)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            priority_code=CE(code="R", code_system="2.16.840.1.113883.5.7"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["priority"] == 5

    def test_emergency_priority(self, mock_reference_registry):
        """EM → priority=1 (high/emergency)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            priority_code=CE(code="EM", code_system="2.16.840.1.113883.5.7"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["priority"] == 1

    def test_no_priority(self, basic_appointment, mock_reference_registry):
        """No priorityCode → no priority field."""
        basic_appointment.priority_code = None
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "priority" not in result


# ============================================================================
# Created Date Tests
# ============================================================================


class TestCreatedDate:
    """Test author time to Appointment.created mapping."""

    def test_created_from_author(self, appointment_with_author, mock_reference_registry):
        """Author time → created date."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(appointment_with_author)
        assert "created" in result

    def test_no_author_no_created(self, basic_appointment, mock_reference_registry):
        """No author → no created field."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "created" not in result


# ============================================================================
# Participant Tests
# ============================================================================


class TestParticipants:
    """Test participant building."""

    def test_patient_participant(self, basic_appointment, mock_reference_registry):
        """Patient should always be a participant."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "participant" in result
        patient_parts = [
            p
            for p in result["participant"]
            if "Patient" in str(p.get("actor", {}).get("reference", ""))
            or p.get("actor", {}).get("reference", "").startswith("urn:uuid:")
        ]
        assert len(patient_parts) >= 1

    def test_performer_participant(self, appointment_with_performer, mock_reference_registry):
        """Performer → additional participant."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(appointment_with_performer)
        assert len(result["participant"]) >= 2  # patient + performer

    def test_participant_status_accepted(self, basic_appointment, mock_reference_registry):
        """All participants should have status=accepted."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        for participant in result["participant"]:
            assert participant["status"] == "accepted"


# ============================================================================
# ID Generation Tests
# ============================================================================


class TestIDGeneration:
    """Test Appointment ID generation."""

    def test_id_generated_from_identifier(self, basic_appointment, mock_reference_registry):
        """ID should be generated from C-CDA identifier."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "id" in result
        assert isinstance(result["id"], str)

    def test_identifiers_preserved(self, basic_appointment, mock_reference_registry):
        """C-CDA identifiers should be preserved."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "identifier" in result
        assert len(result["identifier"]) > 0


# ============================================================================
# Resource Type Tests
# ============================================================================


class TestResourceType:
    """Test that the output is a proper Appointment resource."""

    def test_resource_type(self, basic_appointment, mock_reference_registry):
        """resourceType should be Appointment."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert result["resourceType"] == "Appointment"

    def test_no_meta_profile(self, basic_appointment, mock_reference_registry):
        """Appointment has no US Core profile (not defined in US Core)."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        assert "meta" not in result
