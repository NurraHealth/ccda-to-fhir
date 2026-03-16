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
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.ccda.models.observation import Observation
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

    def test_point_in_time_booked_drops_start(self, mock_reference_registry):
        """effectiveTime with value only + booked status → no start/end (app-1: both or neither)."""
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
        # app-1: booked status requires both start+end; point-in-time has no end
        assert "start" not in result
        assert "end" not in result

    def test_point_in_time_proposed_keeps_start(self, mock_reference_registry):
        """effectiveTime with value only + proposed status → start only (app-3 exception)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="new"),
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

    def test_apt_participant_status_accepted(self, basic_appointment, mock_reference_registry):
        """APT: all participants should have status=accepted."""
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_appointment)
        for participant in result["participant"]:
            assert participant["status"] == "accepted"

    def test_arq_patient_accepted_performer_needs_action(self, mock_reference_registry):
        """ARQ: patient=accepted, performers=needs-action (unconfirmed request)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="new"),
            performer=[
                Performer(
                    assigned_entity=AssignedEntity(
                        id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
                    ),
                )
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        # Patient participant should be accepted
        assert result["participant"][0]["status"] == "accepted"
        # Performer participant should be needs-action
        assert result["participant"][1]["status"] == "needs-action"

    def test_no_registry_raises(self):
        """Missing registry should raise ValueError."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            code=CD(code="185389009", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter()
        with pytest.raises(ValueError, match="reference_registry is required"):
            converter.convert(enc)


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


# ============================================================================
# Edge Case Tests — Status Mapping
# ============================================================================


class TestStatusMappingEdgeCases:
    """Edge cases for status code mapping."""

    def test_held_maps_to_waitlist(self, mock_reference_registry):
        """held → waitlist."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="held"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "waitlist"

    def test_suspended_maps_to_waitlist(self, mock_reference_registry):
        """suspended → waitlist."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="suspended"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "waitlist"

    def test_unknown_status_code_defaults_from_mood(self, mock_reference_registry):
        """Unrecognized status code → default from moodCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            status_code=CS(code="somethingweird"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "proposed"

    def test_status_code_no_code_no_null_flavor(self, mock_reference_registry):
        """CS with neither code nor nullFlavor → default from moodCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["status"] == "booked"


# ============================================================================
# Edge Case Tests — Timing
# ============================================================================


class TestTimingEdgeCases:
    """Edge cases for effectiveTime conversion."""

    def test_cancelled_with_start_only_keeps_start(self, mock_reference_registry):
        """cancelled status + start only → start allowed (app-3 exception)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="cancelled"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" in result
        assert "end" not in result

    def test_waitlist_with_start_only_keeps_start(self, mock_reference_registry):
        """waitlist status + start only → start allowed (app-3 exception)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="held"),
            effective_time=IVL_TS(low=TS(value="20240615")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" in result
        assert "end" not in result

    def test_ivl_ts_high_only(self, mock_reference_registry):
        """IVL_TS with high only and no low → no start/end (app-1)."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            effective_time=IVL_TS(high=TS(value="20240615110000")),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        # Only end, no start → app-1 drops both for booked status
        assert "start" not in result
        assert "end" not in result

    def test_empty_ivl_ts(self, mock_reference_registry):
        """IVL_TS with no value/low/high → no start/end."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            effective_time=IVL_TS(),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" not in result
        assert "end" not in result

    def test_str_effective_time(self, mock_reference_registry):
        """String effectiveTime → start only for proposed."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="ARQ",
            id=[II(root="test")],
            status_code=CS(code="new"),
            effective_time=IVL_TS(value="20240615100000"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "start" in result
        assert "end" not in result


# ============================================================================
# Edge Case Tests — Priority
# ============================================================================


class TestPriorityEdgeCases:
    """Edge cases for priority mapping."""

    def test_asap_priority(self, mock_reference_registry):
        """A → priority=3."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            priority_code=CE(code="A"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["priority"] == 3

    def test_elective_priority(self, mock_reference_registry):
        """EL → priority=7."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            priority_code=CE(code="EL"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["priority"] == 7

    def test_unknown_priority_code(self, mock_reference_registry):
        """Unknown priority code → no priority field."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            priority_code=CE(code="XYZ"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "priority" not in result

    def test_priority_code_case_insensitive(self, mock_reference_registry):
        """Lowercase priority code → still mapped."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            priority_code=CE(code="ur"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert result["priority"] == 2

    def test_priority_code_no_code_value(self, mock_reference_registry):
        """CE with no code → no priority."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            priority_code=CE(code=None),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "priority" not in result


# ============================================================================
# Edge Case Tests — Created Date
# ============================================================================


class TestCreatedDateEdgeCases:
    """Edge cases for author time extraction."""

    def test_multiple_authors_picks_earliest(self, mock_reference_registry):
        """Multiple authors → picks earliest timestamp for created."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            author=[
                Author(
                    time=TS(value="20240610"),
                    assigned_author=AssignedAuthor(id=[II(root="a1")]),
                ),
                Author(
                    time=TS(value="20240601"),
                    assigned_author=AssignedAuthor(id=[II(root="a2")]),
                ),
                Author(
                    time=TS(value="20240605"),
                    assigned_author=AssignedAuthor(id=[II(root="a3")]),
                ),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "created" in result
        assert "2024-06-01" in result["created"]

    def test_authors_without_time_no_created(self, mock_reference_registry):
        """Authors present but none have time → no created."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            author=[
                Author(
                    time=None,
                    assigned_author=AssignedAuthor(id=[II(root="a1")]),
                ),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "created" not in result


# ============================================================================
# Edge Case Tests — Reason Codes
# ============================================================================


class TestReasonCodes:
    """Test reasonCode extraction from entryRelationships."""

    def test_rson_observation_produces_reason_code(self, mock_reference_registry):
        """RSON entryRelationship with observation value → reasonCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            entry_relationship=[
                EntryRelationship(
                    type_code="RSON",
                    observation=Observation(
                        class_code="OBS",
                        mood_code="EVN",
                        value=CD(
                            code="29857009",
                            code_system="2.16.840.1.113883.6.96",
                            display_name="Chest pain",
                        ),
                    ),
                ),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "reasonCode" in result
        assert result["reasonCode"][0]["coding"][0]["code"] == "29857009"

    def test_non_rson_entry_relationship_skipped(self, mock_reference_registry):
        """Non-RSON entryRelationship → no reasonCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            entry_relationship=[
                EntryRelationship(
                    type_code="SUBJ",
                    observation=Observation(
                        class_code="OBS",
                        mood_code="EVN",
                        value=CD(code="29857009", code_system="2.16.840.1.113883.6.96"),
                    ),
                ),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "reasonCode" not in result

    def test_rson_without_observation_skipped(self, mock_reference_registry):
        """RSON entryRelationship without observation → no reasonCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            entry_relationship=[
                EntryRelationship(type_code="RSON", observation=None),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "reasonCode" not in result

    def test_rson_observation_without_value_skipped(self, mock_reference_registry):
        """RSON observation with no value → no reasonCode."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
            entry_relationship=[
                EntryRelationship(
                    type_code="RSON",
                    observation=Observation(class_code="OBS", mood_code="EVN", value=None),
                ),
            ],
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "reasonCode" not in result


# ============================================================================
# Edge Case Tests — ID / Identifiers
# ============================================================================


class TestIDEdgeCases:
    """Edge cases for ID and identifier generation."""

    def test_no_id_no_identifier(self, mock_reference_registry):
        """No C-CDA id → no id or identifier fields."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=None,
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "id" not in result
        assert "identifier" not in result

    def test_id_with_null_root_filtered(self, mock_reference_registry):
        """II elements with root=None filtered from identifiers list."""
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[
                II(root="valid-root", extension="ext-1"),
                II(root=None, extension="ext-2"),
            ],
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter(reference_registry=mock_reference_registry)
        result = converter.convert(enc)
        assert "identifier" in result
        # Only the valid root should be in identifiers
        assert len(result["identifier"]) == 1


# ============================================================================
# Edge Case Tests — Participant
# ============================================================================


class TestParticipantEdgeCases:
    """Edge cases for participant building."""

    def test_patient_ref_none_raises(self):
        """Patient reference returning None + no performers → ValueError."""
        registry = Mock(spec=ReferenceRegistry)
        registry.get_patient_reference = Mock(return_value=None)
        enc = CCDAEncounter(
            class_code="ENC",
            mood_code="APT",
            id=[II(root="test")],
            status_code=CS(code="active"),
        )
        converter = AppointmentConverter(reference_registry=registry)
        with pytest.raises(ValueError, match="at least one participant"):
            converter.convert(enc)
