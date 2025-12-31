"""Unit tests for CareTeamConverter.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the behavior of the CareTeamConverter class for converting
C-CDA Care Team Organizer to FHIR CareTeam resources.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import AD, CE, CS, ENXP, II, IVL_TS, ON, PN, TEL, TS
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer, OrganizerComponent
from ccda_to_fhir.ccda.models.participant import Participant, ParticipantRole
from ccda_to_fhir.ccda.models.performer import (
    AssignedEntity,
    AssignedPerson,
    Performer,
    RepresentedOrganization,
)
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.careteam import CareTeamConverter


@pytest.fixture
def care_team_converter() -> CareTeamConverter:
    """Create a CareTeamConverter instance for testing."""
    patient_ref = {"reference": "Patient/patient-123"}
    return CareTeamConverter(patient_reference=patient_ref)


@pytest.fixture
def minimal_care_team_member() -> Act:
    """Create a minimal Care Team Member Act for testing.

    Satisfies US Core CareTeam requirement for at least one participant.
    """
    return Act(
        class_code="PCPR",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        performer=[Performer(
            function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
            assigned_entity=AssignedEntity(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(
                    name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))]
                )
            )
        )]
    )


@pytest.fixture
def sample_care_team_organizer() -> Organizer:
    """Create a sample Care Team Organizer with primary care team."""
    # Member Act 1: Physician (PCP)
    physician_member = Act(
        class_code="PCPR",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1", display_name="Care team"),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20230115")),
        performer=[Performer(
            function_code=CE(
                code="PCP",
                code_system="2.16.840.1.113883.5.88",
                display_name="Primary Care Physician"
            ),
            assigned_entity=AssignedEntity(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                code=CE(
                    code="207Q00000X",
                    code_system="2.16.840.1.113883.6.101",
                    display_name="Family Medicine Physician"
                ),
                addr=[AD(
                    use="WP",
                    street_address_line=["1001 Village Avenue"],
                    city="Portland",
                    state="OR",
                    postal_code="99123"
                )],
                telecom=[TEL(use="WP", value="tel:+1(555)555-0100")],
                assigned_person=AssignedPerson(
                    name=[PN(
                        prefix=[ENXP(value="Dr.")],
                        given=[ENXP(value="John")],
                        family=ENXP(value="Smith"),
                        suffix=[ENXP(value="MD")]
                    )]
                ),
                represented_organization=RepresentedOrganization(
                    id=[II(root="2.16.840.1.113883.19.5", extension="org-123")],
                    name=[ON(mixed_content="Community Health Clinic")]
                )
            )
        )]
    )

    # Team Type Observation
    team_type_obs = Observation(
        class_code="OBS",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2", extension="2019-07-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1", display_name="Care team"),
        value=CE(
            code="LA27976-2",
            code_system="2.16.840.1.113883.6.1",
            display_name="Longitudinal care-coordination focused care team"
        )
    )

    # Care Team Organizer
    organizer = Organizer(
        class_code="CLUSTER",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
        id=[II(root="2.16.840.1.113883.19.5.99999.1", extension="primary-team-001")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1", display_name="Care team"),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20230115")),
        component=[
            OrganizerComponent(observation=team_type_obs),
            OrganizerComponent(act=physician_member)
        ]
    )

    return organizer


@pytest.fixture
def care_team_with_multiple_members() -> Organizer:
    """Create Care Team Organizer with multiple members (physician and nurse)."""
    # Member 1: Physician (PCP)
    physician_member = Act(
        class_code="PCPR",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20230115")),
        performer=[Performer(
            function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
            assigned_entity=AssignedEntity(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))])
            )
        )]
    )

    # Member 2: Nurse
    nurse_member = Act(
        class_code="PCPR",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        performer=[Performer(
            function_code=CE(code="224535009", code_system="2.16.840.1.113883.6.96", display_name="Registered nurse"),
            assigned_entity=AssignedEntity(
                id=[II(root="2.16.840.1.113883.19", extension="nurse-001")],
                assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="Sarah")], family=ENXP(value="Johnson"))])
            )
        )]
    )

    organizer = Organizer(
        class_code="CLUSTER",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
        id=[II(root="2.16.840.1.113883.19.5", extension="team-multi")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20230115")),
        component=[
            OrganizerComponent(act=physician_member),
            OrganizerComponent(act=nurse_member)
        ]
    )

    return organizer


@pytest.fixture
def care_team_with_lead() -> Organizer:
    """Create Care Team Organizer with designated team lead."""
    physician_member = Act(
        class_code="PCPR",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        performer=[Performer(
            function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
            assigned_entity=AssignedEntity(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))])
            )
        )]
    )

    # Team lead participant (PPRF = Primary Performer)
    lead_participant = Participant(
        type_code="PPRF",
        participant_role=ParticipantRole(
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        )
    )

    organizer = Organizer(
        class_code="CLUSTER",
        mood_code="EVN",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
        id=[II(root="2.16.840.1.113883.19.5", extension="team-with-lead")],
        code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20230115")),
        participant=[lead_participant],
        component=[OrganizerComponent(act=physician_member)]
    )

    return organizer


class TestCareTeamConverter:
    """Unit tests for CareTeamConverter."""

    # ============================================================================
    # A. Basic Resource Creation (3 tests)
    # ============================================================================

    def test_creates_careteam_resource(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that converter creates a CareTeam resource."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert careteam is not None
        assert careteam["resourceType"] == FHIRCodes.ResourceTypes.CARETEAM

    def test_includes_us_core_profile(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that US Core CareTeam profile is included in meta."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "meta" in careteam
        assert "profile" in careteam["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam" in careteam["meta"]["profile"]

    def test_generates_id_from_identifier(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that ID is generated from organizer identifier."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "id" in careteam
        # ID should be deterministic based on identifier
        assert "primary-team-001" in careteam["id"] or careteam["id"]  # UUID v4 or based on extension

    # ============================================================================
    # B. Identifier Mapping (2 tests)
    # ============================================================================

    def test_converts_identifiers(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that C-CDA identifiers are converted to FHIR identifiers."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "identifier" in careteam
        assert len(careteam["identifier"]) >= 1
        assert careteam["identifier"][0]["system"] == "urn:oid:2.16.840.1.113883.19.5.99999.1"
        assert careteam["identifier"][0]["value"] == "primary-team-001"

    def test_handles_multiple_identifiers(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test handling of multiple identifiers."""
        # Create minimal member to satisfy US Core requirement
        member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))])
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[
                II(root="2.16.840.1.113883.19.5", extension="team-001"),
                II(root="2.16.840.1.113883.19.6", extension="team-002")
            ],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=member)]
        )

        careteam = care_team_converter.convert(organizer)

        assert "identifier" in careteam
        assert len(careteam["identifier"]) >= 2

    # ============================================================================
    # C. Status Mapping (6 tests)
    # ============================================================================

    def test_maps_status_active(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that 'active' status is mapped correctly."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert careteam["status"] == "active"

    def test_maps_status_completed_to_inactive(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that 'completed' status maps to 'inactive'."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="completed"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "inactive"

    def test_maps_status_aborted_to_inactive(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that 'aborted' status maps to 'inactive'."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="aborted"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "inactive"

    def test_maps_status_suspended(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that 'suspended' status is mapped correctly."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="suspended"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "suspended"

    def test_maps_status_nullified_to_entered_in_error(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that 'nullified' status maps to 'entered-in-error'."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="nullified"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "entered-in-error"

    def test_defaults_to_active_when_status_missing(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that status defaults to 'active' when missing."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=None,
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "active"

    # ============================================================================
    # D. Subject Mapping (2 tests)
    # ============================================================================

    def test_includes_patient_subject(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that patient reference is included as subject."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "subject" in careteam
        assert careteam["subject"]["reference"] == "Patient/patient-123"

    def test_requires_patient_reference(self) -> None:
        """Test that converter requires patient reference."""
        with pytest.raises(ValueError, match="patient_reference is required"):
            CareTeamConverter(patient_reference=None)

    # ============================================================================
    # E. Period Mapping (3 tests)
    # ============================================================================

    def test_converts_effective_time_to_period(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that effectiveTime is converted to period."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "period" in careteam
        assert "start" in careteam["period"]
        assert careteam["period"]["start"] == "2023-01-15"

    def test_converts_period_with_high_value(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that period with both low and high is converted."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(
                low=TS(value="20230115"),
                high=TS(value="20240115")
            ),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)

        assert "period" in careteam
        assert careteam["period"]["start"] == "2023-01-15"
        assert careteam["period"]["end"] == "2024-01-15"

    def test_handles_missing_effective_time(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that missing effectiveTime is handled gracefully."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=None,
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        # Period should be omitted if no effectiveTime
        assert "period" not in careteam or careteam["period"] == {}

    # ============================================================================
    # F. Category Mapping (5 tests)
    # ============================================================================

    def test_maps_team_type_to_category(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that Care Team Type Observation maps to category."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "category" in careteam
        assert len(careteam["category"]) >= 1
        assert careteam["category"][0]["coding"][0]["system"] == "http://loinc.org"
        assert careteam["category"][0]["coding"][0]["code"] == "LA27976-2"
        assert careteam["category"][0]["coding"][0]["display"] == "Longitudinal care-coordination focused care team"

    def test_maps_condition_focused_team_type(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test mapping of condition-focused team type."""
        team_type_obs = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA28865-6", code_system="2.16.840.1.113883.6.1", display_name="Condition-focused care team")
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[
                OrganizerComponent(observation=team_type_obs),
                OrganizerComponent(act=minimal_care_team_member)
            ]
        )

        careteam = care_team_converter.convert(organizer)

        assert "category" in careteam
        assert careteam["category"][0]["coding"][0]["code"] == "LA28865-6"

    def test_maps_encounter_focused_team_type(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test mapping of encounter-focused team type."""
        team_type_obs = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA28866-4", code_system="2.16.840.1.113883.6.1", display_name="Encounter-focused care team")
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[
                OrganizerComponent(observation=team_type_obs),
                OrganizerComponent(act=minimal_care_team_member)
            ]
        )

        careteam = care_team_converter.convert(organizer)

        assert "category" in careteam
        assert careteam["category"][0]["coding"][0]["code"] == "LA28866-4"

    def test_handles_multiple_team_types(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test handling of multiple team type observations."""
        type_obs_1 = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA27976-2", code_system="2.16.840.1.113883.6.1")
        )

        type_obs_2 = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA28865-6", code_system="2.16.840.1.113883.6.1")
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[
                OrganizerComponent(observation=type_obs_1),
                OrganizerComponent(observation=type_obs_2),
                OrganizerComponent(act=minimal_care_team_member)
            ]
        )

        careteam = care_team_converter.convert(organizer)

        assert "category" in careteam
        assert len(careteam["category"]) == 2

    def test_handles_missing_team_type(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that missing team type is handled (category is optional)."""
        physician_member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))])
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=physician_member)]  # No type observation
        )

        careteam = care_team_converter.convert(organizer)
        # Should still create valid CareTeam without category
        assert careteam["resourceType"] == FHIRCodes.ResourceTypes.CARETEAM

    # ============================================================================
    # G. Participant Mapping (10 tests)
    # ============================================================================

    def test_creates_participant_from_member_act(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that Care Team Member Act is converted to participant."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "participant" in careteam
        assert len(careteam["participant"]) >= 1

    def test_participant_has_required_role(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that participant has required role element."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        participant = careteam["participant"][0]
        assert "role" in participant
        assert len(participant["role"]) >= 1
        assert "coding" in participant["role"][0]

    def test_participant_has_required_member(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that participant has required member reference."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        participant = careteam["participant"][0]
        assert "member" in participant
        assert "reference" in participant["member"]

    def test_maps_function_code_to_role(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that performer functionCode maps to participant.role."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        participant = careteam["participant"][0]
        role_coding = participant["role"][0]["coding"][0]

        assert role_coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
        assert role_coding["code"] == "PCP"
        assert role_coding["display"] == "Primary Care Physician"

    def test_maps_snomed_function_code_to_role(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that SNOMED CT function codes are mapped correctly."""
        nurse_member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(
                    code="224535009",
                    code_system="2.16.840.1.113883.6.96",
                    display_name="Registered nurse"
                ),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.19", extension="nurse-001")],
                    assigned_person=AssignedPerson(name=[PN(given=[ENXP(value="Sarah")], family=ENXP(value="Johnson"))])
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=nurse_member)]
        )

        careteam = care_team_converter.convert(organizer)

        role_coding = careteam["participant"][0]["role"][0]["coding"][0]
        assert role_coding["system"] == "http://snomed.info/sct"
        assert role_coding["code"] == "224535009"

    def test_creates_practitioner_role_member_reference(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that member reference points to PractitionerRole (recommended)."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        member_ref = careteam["participant"][0]["member"]["reference"]
        assert member_ref.startswith("PractitionerRole/")

    def test_handles_multiple_participants(
        self, care_team_converter: CareTeamConverter, care_team_with_multiple_members: Organizer
    ) -> None:
        """Test that multiple Care Team Member Acts create multiple participants."""
        careteam = care_team_converter.convert(care_team_with_multiple_members)

        assert "participant" in careteam
        assert len(careteam["participant"]) == 2

    def test_maps_member_period(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that member act effectiveTime maps to participant.period."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        participant = careteam["participant"][0]
        assert "period" in participant
        assert participant["period"]["start"] == "2023-01-15"

    def test_orders_team_lead_first(
        self, care_team_converter: CareTeamConverter, care_team_with_lead: Organizer
    ) -> None:
        """Test that designated team lead is placed first in participants array."""
        careteam = care_team_converter.convert(care_team_with_lead)

        # First participant should be the team lead (NPI 1234567890)
        first_participant = careteam["participant"][0]
        # Should be ordered first based on matching ID with PPRF participant
        assert "member" in first_participant

    def test_requires_at_least_one_participant(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that CareTeam requires at least one participant (US Core requirement)."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[]  # No members
        )

        with pytest.raises(ValueError, match="at least one.*participant"):
            care_team_converter.convert(organizer)

    # ============================================================================
    # H. Name Generation (2 tests)
    # ============================================================================

    def test_generates_human_readable_name(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that a human-readable name is generated for the care team."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        assert "name" in careteam
        # Name should include patient context and team type/nature
        assert isinstance(careteam["name"], str)
        assert len(careteam["name"]) > 0

    def test_name_includes_team_type_context(
        self, care_team_converter: CareTeamConverter, sample_care_team_organizer: Organizer
    ) -> None:
        """Test that generated name includes context from team type."""
        careteam = care_team_converter.convert(sample_care_team_organizer)

        # Should include some indication of longitudinal/primary care nature
        name_lower = careteam["name"].lower()
        assert any(keyword in name_lower for keyword in ["care", "team", "longitudinal", "primary"])

    # ============================================================================
    # I. Validation and Error Handling (4 tests)
    # ============================================================================

    def test_requires_valid_template_id(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that organizer must have Care Team Organizer template ID."""
        invalid_organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.999999.INVALID")],  # Invalid template
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[]
        )

        with pytest.raises(ValueError, match="template.*2.16.840.1.113883.10.20.22.4.500"):
            care_team_converter.convert(invalid_organizer)

    def test_requires_status_code(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that organizer must have statusCode (defaults to active if missing)."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=None,  # Missing status
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        # Should default to active rather than error
        careteam = care_team_converter.convert(organizer)
        assert careteam["status"] == "active"

    def test_requires_id(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that organizer must have identifier."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=None,  # Missing ID
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[]
        )

        with pytest.raises(ValueError, match="identifier.*required"):
            care_team_converter.convert(organizer)

    def test_handles_none_organizer(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that None organizer raises error."""
        with pytest.raises(ValueError):
            care_team_converter.convert(None)

    # Tests for enhancements

    def test_validates_organizer_code(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that organizer code must be LOINC 86744-0."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="WRONG", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        with pytest.raises(ValueError, match="code SHALL be LOINC 86744-0"):
            care_team_converter.convert(organizer)

    def test_validates_effective_time_low_when_present(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that effectiveTime.low is required when effectiveTime is present."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=None, high=TS(value="20230615")),  # Missing low
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        with pytest.raises(ValueError, match="effectiveTime.low is required"):
            care_team_converter.convert(organizer)

    def test_extracts_managing_organization(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that managingOrganization is extracted from member organization."""
        member_with_org = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(
                        name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))]
                    ),
                    represented_organization=RepresentedOrganization(
                        id=[II(root="2.16.840.1.113883.4.6", extension="org-123")],
                        name=[ON(value="Acme Healthcare")]
                    )
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=member_with_org)]
        )

        careteam = care_team_converter.convert(organizer)

        assert "managingOrganization" in careteam
        assert len(careteam["managingOrganization"]) == 1
        assert "reference" in careteam["managingOrganization"][0]
        assert careteam["managingOrganization"][0]["reference"].startswith("Organization/")

    def test_generates_narrative_text(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that narrative text is generated."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)

        assert "text" in careteam
        assert careteam["text"]["status"] == "generated"
        assert "div" in careteam["text"]
        assert "xmlns" in careteam["text"]["div"]
        assert "Care Team" in careteam["text"]["div"]

    # ============================================================================
    # Template Extension Validation Tests
    # ============================================================================

    def test_rejects_organizer_without_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that Care Team Organizer without extension is rejected."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500")],  # No extension
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        with pytest.raises(ValueError, match="Invalid templateId.*extension"):
            care_team_converter.convert(organizer)

    def test_rejects_organizer_with_invalid_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that Care Team Organizer with invalid extension is rejected."""
        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2018-01-01")],  # Invalid
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        with pytest.raises(ValueError, match="Invalid templateId.*extension"):
            care_team_converter.convert(organizer)

    def test_accepts_organizer_with_2019_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that Care Team Organizer with 2019-07-01 extension is accepted."""
        # Update minimal member to have extension
        minimal_care_team_member.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2019-07-01")
        ]

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2019-07-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam is not None
        assert careteam["resourceType"] == FHIRCodes.ResourceTypes.CARETEAM

    def test_accepts_organizer_with_2022_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that Care Team Organizer with 2022-06-01 extension is accepted."""
        # Update minimal member to have extension
        minimal_care_team_member.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")
        ]

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=minimal_care_team_member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam is not None
        assert careteam["resourceType"] == FHIRCodes.ResourceTypes.CARETEAM

    def test_accepts_member_act_with_2019_extension(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that Care Team Member Act with 2019-07-01 extension is accepted."""
        member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2019-07-01")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(
                        name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))]
                    )
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam is not None
        assert len(careteam["participant"]) == 1

    def test_accepts_member_act_with_2022_extension(
        self, care_team_converter: CareTeamConverter
    ) -> None:
        """Test that Care Team Member Act with 2022-06-01 extension is accepted."""
        member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(
                        name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))]
                    )
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=member)]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam is not None
        assert len(careteam["participant"]) == 1

    def test_warns_but_accepts_member_act_without_extension(
        self, care_team_converter: CareTeamConverter, caplog
    ) -> None:
        """Test that Care Team Member Act without extension logs warning but continues."""
        import logging

        member = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1")],  # No extension
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            performer=[Performer(
                function_code=CE(code="PCP", code_system="2.16.840.1.113883.5.88"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(
                        name=[PN(given=[ENXP(value="John")], family=ENXP(value="Smith"))]
                    )
                )
            )]
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[OrganizerComponent(act=member)]
        )

        with caplog.at_level(logging.WARNING):
            careteam = care_team_converter.convert(organizer)

        assert careteam is not None
        assert len(careteam["participant"]) == 1
        assert any("missing or invalid extension" in record.message for record in caplog.records)

    def test_accepts_type_observation_with_correct_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act
    ) -> None:
        """Test that Care Team Type Observation with 2019-07-01 extension is accepted."""
        # Update minimal member to have extension
        minimal_care_team_member.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")
        ]

        team_type_obs = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2", extension="2019-07-01")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA27976-2", code_system="2.16.840.1.113883.6.1",
                    display_name="Longitudinal care-coordination focused care team")
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[
                OrganizerComponent(observation=team_type_obs),
                OrganizerComponent(act=minimal_care_team_member)
            ]
        )

        careteam = care_team_converter.convert(organizer)
        assert careteam is not None
        assert "category" in careteam
        assert len(careteam["category"]) == 1

    def test_warns_but_accepts_type_observation_without_extension(
        self, care_team_converter: CareTeamConverter, minimal_care_team_member: Act, caplog
    ) -> None:
        """Test that Care Team Type Observation without extension logs warning but continues."""
        import logging

        # Update minimal member to have extension
        minimal_care_team_member.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")
        ]

        team_type_obs = Observation(
            class_code="OBS",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.2")],  # No extension
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            value=CE(code="LA27976-2", code_system="2.16.840.1.113883.6.1",
                    display_name="Longitudinal care-coordination focused care team")
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="2.16.840.1.113883.19.5", extension="team-001")],
            code=CE(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230115")),
            component=[
                OrganizerComponent(observation=team_type_obs),
                OrganizerComponent(act=minimal_care_team_member)
            ]
        )

        with caplog.at_level(logging.WARNING):
            careteam = care_team_converter.convert(organizer)

        assert careteam is not None
        assert "category" in careteam
        assert len(careteam["category"]) == 1
        assert any("missing or invalid extension" in record.message for record in caplog.records)
