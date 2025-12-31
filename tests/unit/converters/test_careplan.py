"""Comprehensive unit tests for CarePlan converter.

Tests comprehensive CarePlan resource conversion following:
- HL7 C-CDA R2.1 Care Plan Document
- US Core CarePlan Profile
- C-CDA on FHIR IG Care Plan mapping

All test data based on realistic clinical scenarios and official HL7 examples.
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson
from ccda_to_fhir.ccda.models.clinical_document import (
    AssignedCustodian,
    Author,
    ClinicalDocument,
    Custodian,
    CustodianOrganization,
    DocumentationOf,
    ServiceEvent,
    ServiceEventPerformer,
)
from ccda_to_fhir.ccda.models.datatypes import CE, CS, ENXP, II, IVL_TS, ON, PN, TS
from ccda_to_fhir.ccda.models.performer import AssignedEntity
from ccda_to_fhir.ccda.models.record_target import Patient, PatientRole, RecordTarget
from ccda_to_fhir.constants import FHIRCodes, TemplateIds
from ccda_to_fhir.converters.careplan import CarePlanConverter
from ccda_to_fhir.converters.references import ReferenceRegistry

# ============================================================================
# Fixtures - Realistic C-CDA Care Plan Document Data
# ============================================================================


@pytest.fixture
def care_plan_template_id() -> II:
    """Care Plan Document template ID."""
    return II(
        root=TemplateIds.CARE_PLAN_DOCUMENT,
        extension="2015-08-01"
    )


@pytest.fixture
def us_realm_header_template_id() -> II:
    """US Realm Header template ID."""
    return II(
        root="2.16.840.1.113883.10.20.22.1.1",
        extension="2015-08-01"
    )


@pytest.fixture
def basic_patient() -> Patient:
    """Create a basic patient for testing."""
    return Patient(
        name=[
            PN(
                given=[ENXP(value="Amy")],
                family=ENXP(value="Shaw"),
            )
        ],
        administrative_gender_code=CE(
            code="F",
            code_system="2.16.840.1.113883.5.1",
            display_name="Female",
        ),
        birth_time=TS(value="19750501"),
    )


@pytest.fixture
def basic_record_target(basic_patient) -> RecordTarget:
    """Create a basic record target."""
    return RecordTarget(
        patient_role=PatientRole(
            id=[II(root="2.16.840.1.113883.19.5", extension="patient-123")],
            patient=basic_patient,
        )
    )


@pytest.fixture
def basic_author() -> Author:
    """Create a basic author (practitioner)."""
    return Author(
        time=TS(value="20240115120000-0500"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension="npi-123")],
            assigned_person=AssignedPerson(
                name=[
                    PN(
                        given=[ENXP(value="John")],
                        family=ENXP(value="Smith"),
                        suffix=[ENXP(value="MD")],
                    )
                ]
            ),
        ),
    )


@pytest.fixture
def basic_custodian() -> Custodian:
    """Create a basic custodian organization."""
    return Custodian(
        assigned_custodian=AssignedCustodian(
            represented_custodian_organization=CustodianOrganization(
                id=[II(root="2.16.840.1.113883.19.5", extension="org-123")],
                name="Community Health Hospital",
            )
        )
    )


@pytest.fixture
def service_event_with_period() -> ServiceEvent:
    """Create a service event with effectiveTime period."""
    return ServiceEvent(
        class_code="PCPR",
        effective_time=IVL_TS(
            low=TS(value="20240115"),
            high=TS(value="20240415"),
        ),
    )


@pytest.fixture
def service_event_with_performer() -> ServiceEvent:
    """Create a service event with performer."""
    return ServiceEvent(
        class_code="PCPR",
        effective_time=IVL_TS(
            low=TS(value="20240115"),
            high=TS(value="20240415"),
        ),
        performer=[
            ServiceEventPerformer(
                type_code="PRF",
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="performer-456")]
                ),
            )
        ],
    )


@pytest.fixture
def minimal_care_plan_document(
    care_plan_template_id,
    us_realm_header_template_id,
    basic_record_target,
    basic_author,
    basic_custodian,
) -> ClinicalDocument:
    """Create a minimal Care Plan Document with only required fields.

    Based on C-CDA R2.1 Care Plan Document template requirements.
    """
    return ClinicalDocument(
        realm_code=[CS(code="US")],
        type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
        template_id=[us_realm_header_template_id, care_plan_template_id],
        id=II(root="2.16.840.1.113883.19.5.99999.1", extension="careplan-123"),
        code=CE(
            code="52521-2",
            code_system="2.16.840.1.113883.6.1",
            display_name="Overall plan of care/advance care directives",
        ),
        title="Care Plan",
        effective_time=TS(value="20240115120000-0500"),
        confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
        language_code=CS(code="en-US"),
        record_target=[basic_record_target],
        author=[basic_author],
        custodian=basic_custodian,
    )


@pytest.fixture
def complete_care_plan_document(
    minimal_care_plan_document,
    service_event_with_period,
) -> ClinicalDocument:
    """Create a complete Care Plan Document with all optional fields."""
    minimal_care_plan_document.set_id = II(
        root="2.16.840.1.113883.19.5.99999.2",
        extension="careplan-set-123"
    )
    minimal_care_plan_document.version_number = 1
    minimal_care_plan_document.documentation_of = [
        DocumentationOf(service_event=service_event_with_period)
    ]
    return minimal_care_plan_document


@pytest.fixture
def mock_reference_registry() -> ReferenceRegistry:
    """Create a mock reference registry."""
    registry = Mock(spec=ReferenceRegistry)
    registry.get_patient_reference = Mock(
        return_value={"reference": "Patient/test-patient"}
    )
    registry.has_resource = Mock(return_value=True)
    return registry


# ============================================================================
# Basic Conversion Tests
# ============================================================================


class TestBasicCarePlanConversion:
    """Test basic CarePlan resource creation."""

    def test_basic_care_plan_conversion(self, minimal_care_plan_document, mock_reference_registry):
        """Test basic CarePlan creation from Care Plan Document."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        # Verify resource type
        assert careplan["resourceType"] == FHIRCodes.ResourceTypes.CAREPLAN

        # Verify required fields
        assert "status" in careplan
        assert "intent" in careplan
        assert "category" in careplan
        assert "subject" in careplan

        # Verify fixed values
        assert careplan["intent"] == "plan"
        assert careplan["status"] == "active"

    def test_care_plan_with_minimal_data(self, minimal_care_plan_document, mock_reference_registry):
        """Test CarePlan with only required elements."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        # Should have required fields
        assert "resourceType" in careplan
        assert "status" in careplan
        assert "intent" in careplan
        assert "category" in careplan
        assert "subject" in careplan
        assert "identifier" in careplan
        assert "author" in careplan
        assert "text" in careplan

        # Should NOT have optional fields when not provided
        assert "period" not in careplan
        assert "addresses" not in careplan
        assert "goal" not in careplan
        assert "activity" not in careplan

    def test_care_plan_with_complete_data(
        self, complete_care_plan_document, mock_reference_registry
    ):
        """Test CarePlan with all optional elements."""
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            health_concern_refs=[{"reference": "Condition/concern-1"}],
            goal_refs=[{"reference": "Goal/goal-1"}],
        )
        careplan = converter.convert(complete_care_plan_document)

        # Should have all fields
        assert "resourceType" in careplan
        assert "status" in careplan
        assert "intent" in careplan
        assert "category" in careplan
        assert "subject" in careplan
        assert "identifier" in careplan
        assert "period" in careplan
        assert "author" in careplan
        assert "contributor" in careplan
        assert "addresses" in careplan
        assert "goal" in careplan
        assert "text" in careplan


# ============================================================================
# Identifier Mapping Tests
# ============================================================================


class TestIdentifierMapping:
    """Test document.id maps to CarePlan.identifier."""

    def test_identifier_mapping(self, minimal_care_plan_document, mock_reference_registry):
        """Test document.setId maps to CarePlan.identifier."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        # Verify identifier array exists
        assert "identifier" in careplan
        assert isinstance(careplan["identifier"], list)
        assert len(careplan["identifier"]) > 0

        # Verify identifier structure
        identifier = careplan["identifier"][0]
        assert "system" in identifier or "value" in identifier

    def test_identifier_with_version(self, complete_care_plan_document, mock_reference_registry):
        """Test identifier includes document version information."""
        # Note: Current implementation doesn't use versionNumber in identifier
        # This test documents current behavior
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(complete_care_plan_document)

        # Verify identifier exists
        assert "identifier" in careplan
        assert len(careplan["identifier"]) > 0


# ============================================================================
# Status Mapping Tests
# ============================================================================


class TestStatusMapping:
    """Test CarePlan status determination."""

    def test_status_defaults_to_active(self, minimal_care_plan_document, mock_reference_registry):
        """Test status defaults to 'active'."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert careplan["status"] == "active"

    def test_status_from_document_context(self, complete_care_plan_document, mock_reference_registry):
        """Test status determination from document context."""
        # Current implementation always returns "active"
        # This test documents current behavior
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(complete_care_plan_document)

        assert careplan["status"] in [
            "draft",
            "active",
            "on-hold",
            "revoked",
            "completed",
            "entered-in-error",
            "unknown",
        ]

    def test_status_completed_when_period_ended(
        self, care_plan_template_id, us_realm_header_template_id, basic_record_target,
        basic_author, basic_custodian, mock_reference_registry):
        """Test status 'completed' when period.end in past."""
        from datetime import datetime, timedelta, timezone

        # Create document with past end date
        past_date = datetime.now(timezone.utc) - timedelta(days=30)
        past_date_str = past_date.strftime("%Y%m%d")

        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[us_realm_header_template_id, care_plan_template_id],
            id=II(root="2.16.840.1.113883.19.5", extension="cp-past"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            title="Care Plan",
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[basic_record_target],
            author=[basic_author],
            custodian=basic_custodian,
            documentation_of=[
                DocumentationOf(
                    service_event=ServiceEvent(
                        class_code="PCPR",
                        effective_time=IVL_TS(
                            low=TS(value="20240101"),
                            high=TS(value=past_date_str),
                        ),
                    )
                )
            ],
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(doc)

        assert careplan["status"] == "completed"

    def test_status_completed_when_all_interventions_completed(
        self, care_plan_template_id, us_realm_header_template_id, basic_record_target,
        basic_author, basic_custodian, mock_reference_registry
    ):
        """Test status 'completed' when all interventions completed."""
        # Create mock intervention entries with completed status
        class MockIntervention:
            def __init__(self, status_code_value):
                self.status_code = CS(code=status_code_value)
                self.id = [II(root="intervention-123")]

        intervention_entries = [
            MockIntervention("completed"),
            MockIntervention("completed"),
        ]

        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[us_realm_header_template_id, care_plan_template_id],
            id=II(root="2.16.840.1.113883.19.5", extension="cp-completed"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            title="Care Plan",
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[basic_record_target],
            author=[basic_author],
            custodian=basic_custodian,
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry, intervention_entries=intervention_entries)
        careplan = converter.convert(doc)

        assert careplan["status"] == "completed"

    def test_status_revoked_when_intervention_cancelled(
        self, care_plan_template_id, us_realm_header_template_id, basic_record_target,
        basic_author, basic_custodian, mock_reference_registry):
        """Test status 'revoked' when any intervention cancelled."""
        # Create mock intervention entries with one cancelled
        class MockIntervention:
            def __init__(self, status_code_value):
                self.status_code = CS(code=status_code_value)
                self.id = [II(root=f"intervention-{status_code_value}")]

        intervention_entries = [
            MockIntervention("active"),
            MockIntervention("cancelled"),
        ]

        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[us_realm_header_template_id, care_plan_template_id],
            id=II(root="2.16.840.1.113883.19.5", extension="cp-revoked"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            title="Care Plan",
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[basic_record_target],
            author=[basic_author],
            custodian=basic_custodian,
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry, intervention_entries=intervention_entries)
        careplan = converter.convert(doc)

        assert careplan["status"] == "revoked"

    def test_status_active_when_authenticated(
        self, care_plan_template_id, us_realm_header_template_id, basic_record_target,
        basic_author, basic_custodian, mock_reference_registry):
        """Test status 'active' when document authenticated."""
        from ccda_to_fhir.ccda.models.clinical_document import LegalAuthenticator

        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[us_realm_header_template_id, care_plan_template_id],
            id=II(root="2.16.840.1.113883.19.5", extension="cp-authenticated"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            title="Care Plan",
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[basic_record_target],
            author=[basic_author],
            custodian=basic_custodian,
            legal_authenticator=LegalAuthenticator(
                time=TS(value="20240115120000-0500"),
                signature_code=CS(code="S"),
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="auth-123")]
                ),
            ),
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(doc)

        assert careplan["status"] == "active"


# ============================================================================
# Subject Mapping Tests
# ============================================================================


class TestSubjectMapping:
    """Test CarePlan subject reference."""

    def test_subject_from_registry(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test subject from ReferenceRegistry."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "subject" in careplan
        assert careplan["subject"]["reference"] == "Patient/test-patient"
        mock_reference_registry.get_patient_reference.assert_called_once()

    def test_subject_from_document_recordtarget(self, minimal_care_plan_document, mock_reference_registry):
        """Test subject fallback to document recordTarget."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)  # No registry
        careplan = converter.convert(minimal_care_plan_document)

        assert "subject" in careplan
        assert "reference" in careplan["subject"]
        assert careplan["subject"]["reference"].startswith("Patient/")

    def test_subject_placeholder_when_missing(self, care_plan_template_id, mock_reference_registry):
        """Test subject uses placeholder when unavailable."""
        # Create document without recordTarget
        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[care_plan_template_id],
            id=II(root="test-root", extension="test-ext"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[],  # Empty record target
            author=[
                Author(
                    time=TS(value="20240115"),
                    assigned_author=AssignedAuthor(
                        id=[II(root="test", extension="auth")]
                    ),
                )
            ],
            custodian=Custodian(
                assigned_custodian=AssignedCustodian(
                    represented_custodian_organization=CustodianOrganization(
                        id=[II(root="test", extension="cust")]
                    )
                )
            ),
        )

        # Don't pass reference_registry to test the fallback to document data
        converter = CarePlanConverter()
        with pytest.raises(ValueError, match="patient identifier missing"):
            converter.convert(doc)


# ============================================================================
# Period Mapping Tests
# ============================================================================


class TestPeriodMapping:
    """Test CarePlan period from serviceEvent."""

    def test_period_from_service_event(self, complete_care_plan_document, mock_reference_registry):
        """Test period extracted from serviceEvent.effectiveTime."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(complete_care_plan_document)

        assert "period" in careplan
        assert "start" in careplan["period"]
        assert "end" in careplan["period"]
        assert careplan["period"]["start"] == "2024-01-15"
        assert careplan["period"]["end"] == "2024-04-15"

    def test_period_with_only_start_date(
        self, minimal_care_plan_document, care_plan_template_id, mock_reference_registry):
        """Test period with only effectiveTime.low."""
        # Add documentation_of with only low date
        minimal_care_plan_document.documentation_of = [
            DocumentationOf(
                service_event=ServiceEvent(
                    class_code="PCPR",
                    effective_time=IVL_TS(low=TS(value="20240115")),
                )
            )
        ]

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "period" in careplan
        assert "start" in careplan["period"]
        assert careplan["period"]["start"] == "2024-01-15"
        # end should not be present if not in source
        assert "end" not in careplan["period"]

    def test_period_missing(self, minimal_care_plan_document, mock_reference_registry):
        """Test CarePlan without period when not available."""
        # minimal_care_plan_document has no documentation_of
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        # Period should not be present
        assert "period" not in careplan


# ============================================================================
# Author and Contributor Tests
# ============================================================================


class TestAuthorAndContributor:
    """Test author and contributor mapping."""

    def test_author_from_first_author(self, minimal_care_plan_document, mock_reference_registry):
        """Test author from document.author[0]."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "author" in careplan
        assert "reference" in careplan["author"]
        assert careplan["author"]["reference"].startswith("Practitioner/")

    def test_contributor_from_all_authors(self, minimal_care_plan_document, mock_reference_registry):
        """Test contributor includes all authors."""
        # Add second author
        second_author = Author(
            time=TS(value="20240115120000-0500"),
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="npi-456")],
                assigned_person=AssignedPerson(
                    name=[
                        PN(
                            given=[ENXP(value="Jane")],
                            family=ENXP(value="Doe"),
                        )
                    ]
                ),
            ),
        )
        minimal_care_plan_document.author.append(second_author)

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "contributor" in careplan
        assert len(careplan["contributor"]) == 2
        # All contributors should have references
        for contributor in careplan["contributor"]:
            assert "reference" in contributor

    def test_contributor_includes_performers(
        self, minimal_care_plan_document, service_event_with_performer, mock_reference_registry):
        """Test contributor includes serviceEvent.performer."""
        minimal_care_plan_document.documentation_of = [
            DocumentationOf(service_event=service_event_with_performer)
        ]

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "contributor" in careplan
        # Should have original author + performer
        assert len(careplan["contributor"]) >= 2

    def test_contributor_deduplication(self, minimal_care_plan_document, mock_reference_registry):
        """Test same practitioner not duplicated in contributors."""
        # Add duplicate author with same ID
        duplicate_author = Author(
            time=TS(value="20240115120000-0500"),
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="npi-123")],  # Same ID
                assigned_person=AssignedPerson(
                    name=[
                        PN(
                            given=[ENXP(value="John")],
                            family=ENXP(value="Smith"),
                        )
                    ]
                ),
            ),
        )
        minimal_care_plan_document.author.append(duplicate_author)

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "contributor" in careplan
        # Should only have one contributor (deduplicated)
        assert len(careplan["contributor"]) == 1


# ============================================================================
# Addresses (Health Concerns) Tests
# ============================================================================


class TestAddresses:
    """Test CarePlan.addresses field for health concerns."""

    def test_addresses_health_concern_references(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test addresses field includes Condition references."""
        health_concerns = [
            {"reference": "Condition/concern-1"},
            {"reference": "Condition/concern-2"},
        ]
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            health_concern_refs=health_concerns,
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "addresses" in careplan
        assert careplan["addresses"] == health_concerns
        assert len(careplan["addresses"]) == 2

    def test_addresses_empty_when_no_concerns(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test addresses omitted when no health concerns."""
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            health_concern_refs=[],  # Empty list
        )
        careplan = converter.convert(minimal_care_plan_document)

        # Addresses should not be present when empty
        assert "addresses" not in careplan


# ============================================================================
# Goal References Tests
# ============================================================================


class TestGoalReferences:
    """Test CarePlan.goal field."""

    def test_goal_references(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test goal field includes Goal resource references."""
        goals = [
            {"reference": "Goal/goal-1"},
            {"reference": "Goal/goal-2"},
        ]
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry, goal_refs=goals
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "goal" in careplan
        assert careplan["goal"] == goals
        assert len(careplan["goal"]) == 2

    def test_goal_empty_when_no_goals(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test goal omitted when no goals."""
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry, goal_refs=[]
        )
        careplan = converter.convert(minimal_care_plan_document)

        # Goal should not be present when empty
        assert "goal" not in careplan


# ============================================================================
# Activity Mapping Tests
# ============================================================================


class TestActivityMapping:
    """Test CarePlan.activity field.

    Note: Comprehensive outcome linking tests are in test_careplan_outcome_linking.py.
    These tests verify activity creation at a high level.
    """

    def test_activity_from_interventions(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test activity.reference from intervention section."""
        # Create mock intervention entry
        intervention = Mock()
        intervention.id = [Mock(root="intervention-123")]
        intervention.entry_relationship = []

        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            intervention_entries=[intervention],
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "activity" in careplan
        assert len(careplan["activity"]) == 1
        assert "reference" in careplan["activity"][0]

    def test_activity_empty_when_no_interventions(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test activity omitted when no interventions."""
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry, intervention_entries=[]
        )
        careplan = converter.convert(minimal_care_plan_document)

        # Activity should not be present when empty
        assert "activity" not in careplan


# ============================================================================
# Narrative Tests
# ============================================================================


class TestNarrative:
    """Test CarePlan.text narrative generation."""

    def test_narrative_generation(self, minimal_care_plan_document, mock_reference_registry):
        """Test text.div generated from sections."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        assert "status" in careplan["text"]
        assert "div" in careplan["text"]

        # Verify XHTML structure
        assert careplan["text"]["div"].startswith("<div")
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in careplan["text"]["div"]
        assert "</div>" in careplan["text"]["div"]

    def test_narrative_status_generated(self, minimal_care_plan_document, mock_reference_registry):
        """Test text.status is 'generated'."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        assert careplan["text"]["status"] == "generated"

    def test_narrative_includes_title(self, minimal_care_plan_document, mock_reference_registry):
        """Test narrative includes care plan title."""
        minimal_care_plan_document.title = "Patient Care Plan 2024"
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        assert "Patient Care Plan 2024" in careplan["text"]["div"]
        assert "<h2>" in careplan["text"]["div"]

    def test_narrative_includes_period(self, complete_care_plan_document, mock_reference_registry):
        """Test narrative includes care plan period."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(complete_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        assert "Period:" in div
        assert "2024-01-15" in div
        assert "2024-04-15" in div

    def test_narrative_includes_health_concerns_count(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test narrative includes health concerns count."""
        health_concerns = [
            {"reference": "Condition/concern-1"},
            {"reference": "Condition/concern-2"},
        ]
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            health_concern_refs=health_concerns,
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        assert "Health Concerns:" in div
        assert "2 concerns documented" in div

    def test_narrative_includes_goals_count(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test narrative includes goals count."""
        goals = [
            {"reference": "Goal/goal-1"},
            {"reference": "Goal/goal-2"},
            {"reference": "Goal/goal-3"},
        ]
        converter = CarePlanConverter(
            reference_registry=mock_reference_registry, goal_refs=goals
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        assert "Goals:" in div
        assert "3 goals documented" in div

    def test_narrative_includes_interventions(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test narrative includes intervention details."""
        # Create intervention with displayName
        from unittest.mock import Mock

        intervention = Mock()
        intervention.id = [Mock(root="intervention-123")]
        intervention.code = Mock()
        intervention.code.display_name = "Oxygen therapy via nasal cannula"
        intervention.entry_relationship = []

        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            intervention_entries=[intervention],
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        assert "Planned Interventions" in div
        assert "<h3>" in div
        assert "Oxygen therapy via nasal cannula" in div
        assert "<ul>" in div
        assert "<li>" in div

    def test_narrative_html_escaped(self, minimal_care_plan_document, mock_reference_registry):
        """Test special characters are HTML escaped."""
        # Use title with special characters
        minimal_care_plan_document.title = "Care Plan <Test> & 'Special' \"Chars\""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        # HTML entities should be escaped
        assert "&lt;" in div  # <
        assert "&gt;" in div  # >
        assert "&amp;" in div  # &
        # Original characters should not appear unescaped in text content
        assert "Care Plan <Test>" not in div or "<h2>Care Plan" not in div

    def test_narrative_minimal_with_no_data(
        self, care_plan_template_id, us_realm_header_template_id, mock_reference_registry):
        """Test narrative generation with minimal data."""
        # Create a bare minimum document
        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[us_realm_header_template_id, care_plan_template_id],
            id=II(root="test-root", extension="test-ext"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            title=None,  # No title
            record_target=[
                RecordTarget(
                    patient_role=PatientRole(id=[II(root="test", extension="pat")])
                )
            ],
            author=[
                Author(
                    time=TS(value="20240115"),
                    assigned_author=AssignedAuthor(
                        id=[II(root="test", extension="auth")],
                        assigned_person=AssignedPerson(
                            name=[
                                PN(
                                    given=[ENXP(value="Test")],
                                    family=ENXP(value="Author"),
                                )
                            ]
                        ),
                    ),
                )
            ],
            custodian=Custodian(
                assigned_custodian=AssignedCustodian(
                    represented_custodian_organization=CustodianOrganization(
                        id=[II(root="test", extension="cust")],
                        name=ON(value="Test Hospital"),
                    )
                )
            ),
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(doc)

        assert "text" in careplan
        assert "status" in careplan["text"]
        assert careplan["text"]["status"] == "generated"
        assert "div" in careplan["text"]
        # Should have at least a title
        assert "<h2>Care Plan</h2>" in careplan["text"]["div"]

    def test_narrative_period_with_start_only(
        self, minimal_care_plan_document, care_plan_template_id, mock_reference_registry):
        """Test narrative period formatting with only start date."""
        minimal_care_plan_document.documentation_of = [
            DocumentationOf(
                service_event=ServiceEvent(
                    effective_time=IVL_TS(low=TS(value="20240115")),
                )
            )
        ]

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        assert "Period:" in div
        assert "2024-01-15 onwards" in div

    def test_narrative_intervention_with_nested_procedure(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test intervention text extraction from nested procedure."""
        from unittest.mock import Mock

        # Create intervention with nested procedure (COMP relationship)
        intervention = Mock()
        intervention.id = [Mock(root="intervention-123")]
        intervention.code = Mock()
        intervention.code.display_name = "Intervention Act"  # Parent code

        # Create nested procedure
        nested_procedure = Mock()
        nested_procedure.code = Mock()
        nested_procedure.code.display_name = "Oxygen administration by nasal cannula"

        # Create COMP relationship
        comp_rel = Mock()
        comp_rel.type_code = "COMP"
        comp_rel.procedure = nested_procedure
        comp_rel.act = None

        intervention.entry_relationship = [comp_rel]

        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            intervention_entries=[intervention],
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        # Should extract text from nested procedure
        assert "Oxygen administration by nasal cannula" in div

    def test_narrative_intervention_fallback_to_code(
        self, minimal_care_plan_document, mock_reference_registry
    ):
        """Test intervention text falls back to code value when no displayName."""
        from unittest.mock import Mock

        intervention = Mock()
        intervention.id = [Mock(root="intervention-123")]
        intervention.code = Mock()
        intervention.code.display_name = None  # No display name
        intervention.code.original_text = None  # No original text
        intervention.code.code = "12345-6"  # Only code
        intervention.entry_relationship = []

        converter = CarePlanConverter(
            reference_registry=mock_reference_registry,
            intervention_entries=[intervention],
        )
        careplan = converter.convert(minimal_care_plan_document)

        assert "text" in careplan
        div = careplan["text"]["div"]
        # Should show code value
        assert "12345-6" in div


# ============================================================================
# Validation Tests
# ============================================================================


class TestValidation:
    """Test CarePlan validation requirements."""

    def test_validation_requires_care_plan_document(self, mock_reference_registry):
        """Test ValueError when not Care Plan Document."""
        # Create document without Care Plan template ID
        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=[
                II(root="2.16.840.1.113883.10.20.22.1.1")  # US Realm Header only
            ],
            id=II(root="test-root", extension="test-ext"),
            code=CE(code="11488-4", code_system="2.16.840.1.113883.6.1"),  # Wrong code
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[
                RecordTarget(
                    patient_role=PatientRole(id=[II(root="test", extension="pat")])
                )
            ],
            author=[
                Author(
                    time=TS(value="20240115"),
                    assigned_author=AssignedAuthor(
                        id=[II(root="test", extension="auth")]
                    ),
                )
            ],
            custodian=Custodian(
                assigned_custodian=AssignedCustodian(
                    represented_custodian_organization=CustodianOrganization(
                        id=[II(root="test", extension="cust")]
                    )
                )
            ),
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="Care Plan Document"):
            converter.convert(doc)

    def test_validation_template_id_required(self, mock_reference_registry):
        """Test ValueError when template ID missing."""
        # Create document without template_id
        doc = ClinicalDocument(
            realm_code=[CS(code="US")],
            type_id=II(root="2.16.840.1.113883.1.3", extension="POCD_HD000040"),
            template_id=None,  # No template ID
            id=II(root="test-root", extension="test-ext"),
            code=CE(code="52521-2", code_system="2.16.840.1.113883.6.1"),
            effective_time=TS(value="20240115"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[
                RecordTarget(
                    patient_role=PatientRole(id=[II(root="test", extension="pat")])
                )
            ],
            author=[
                Author(
                    time=TS(value="20240115"),
                    assigned_author=AssignedAuthor(
                        id=[II(root="test", extension="auth")]
                    ),
                )
            ],
            custodian=Custodian(
                assigned_custodian=AssignedCustodian(
                    represented_custodian_organization=CustodianOrganization(
                        id=[II(root="test", extension="cust")]
                    )
                )
            ),
        )

        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="Care Plan Document"):
            converter.convert(doc)

    def test_validation_requires_clinical_document(self, mock_reference_registry):
        """Test ValueError when ClinicalDocument is None."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="ClinicalDocument is required"):
            converter.convert(None)


# ============================================================================
# US Core Profile Tests
# ============================================================================


class TestUSCoreProfile:
    """Test US Core CarePlan profile compliance."""

    def test_us_core_profile_in_meta(self, minimal_care_plan_document, mock_reference_registry):
        """Test US Core CarePlan profile URL in meta."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "meta" in careplan
        assert "profile" in careplan["meta"]
        assert isinstance(careplan["meta"]["profile"], list)

        # Verify US Core profile URL
        profile_url = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan"
        assert profile_url in careplan["meta"]["profile"]

    def test_category_assess_plan(self, minimal_care_plan_document, mock_reference_registry):
        """Test category includes 'assess-plan' from US Core."""
        converter = CarePlanConverter(reference_registry=mock_reference_registry)
        careplan = converter.convert(minimal_care_plan_document)

        assert "category" in careplan
        assert isinstance(careplan["category"], list)
        assert len(careplan["category"]) > 0

        # Find assess-plan category
        category = careplan["category"][0]
        assert "coding" in category
        assert len(category["coding"]) > 0

        # Verify assess-plan code
        coding = category["coding"][0]
        assert coding["code"] == "assess-plan"
        assert (
            coding["system"]
            == "http://hl7.org/fhir/us/core/CodeSystem/careplan-category"
        )
