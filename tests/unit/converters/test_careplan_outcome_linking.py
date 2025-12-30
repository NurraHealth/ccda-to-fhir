"""Unit tests for CarePlan outcome linking functionality.

Tests the proper linking of outcome observations to intervention activities
based on entryRelationship with typeCode='GEVL'.
"""

from unittest.mock import Mock

import pytest

from ccda_to_fhir.converters.careplan import CarePlanConverter
from ccda_to_fhir.converters.references import ReferenceRegistry


class MockEntry:
    """Mock C-CDA entry element."""
    def __init__(self, entry_id, entry_relationships=None):
        self.id = [Mock(root=entry_id)]
        self.entry_relationship = entry_relationships or []


class MockEntryRelationship:
    """Mock C-CDA entryRelationship element."""
    def __init__(self, type_code, observation_id):
        self.type_code = type_code
        self.observation = MockEntry(observation_id)


class TestCarePlanOutcomeLinking:
    """Test CarePlan outcome-to-activity linking functionality."""

    @pytest.fixture
    def mock_reference_registry(self):
        """Create a mock reference registry."""
        registry = Mock(spec=ReferenceRegistry)
        registry.has_resource = Mock(return_value=True)
        registry.get_patient_reference = Mock(return_value={"reference": "Patient/test-patient"})
        return registry

    @pytest.fixture
    def converter(self, mock_reference_registry):
        """Create CarePlanConverter instance with mock registry."""
        return CarePlanConverter(reference_registry=mock_reference_registry)

    def test_activity_with_single_outcome_gevl_relationship(self, converter, mock_reference_registry):
        """Test activity with single outcome linked via GEVL relationship."""
        # Create intervention with GEVL entryRelationship to outcome
        intervention = MockEntry(
            "intervention-123",
            entry_relationships=[
                MockEntryRelationship("GEVL", "outcome-456")
            ]
        )

        # Create outcome observation
        outcome = MockEntry("outcome-456")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [outcome])

        # Verify activity has outcomeReference
        assert len(activities) == 1
        assert "reference" in activities[0]
        assert "outcomeReference" in activities[0]
        assert len(activities[0]["outcomeReference"]) == 1
        assert activities[0]["outcomeReference"][0]["reference"].startswith("Observation/")

    def test_activity_with_multiple_outcomes(self, converter, mock_reference_registry):
        """Test activity with multiple outcomes linked via GEVL relationships."""
        # Create intervention with multiple GEVL entryRelationships
        intervention = MockEntry(
            "intervention-123",
            entry_relationships=[
                MockEntryRelationship("GEVL", "outcome-456"),
                MockEntryRelationship("GEVL", "outcome-789")
            ]
        )

        # Create outcome observations
        outcome1 = MockEntry("outcome-456")
        outcome2 = MockEntry("outcome-789")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities(
            [intervention],
            [outcome1, outcome2]
        )

        # Verify activity has multiple outcomeReferences
        assert len(activities) == 1
        assert "outcomeReference" in activities[0]
        assert len(activities[0]["outcomeReference"]) == 2
        # Verify both references start with Observation/
        outcome_refs = [ref["reference"] for ref in activities[0]["outcomeReference"]]
        assert all(ref.startswith("Observation/") for ref in outcome_refs)

    def test_activity_with_no_outcomes(self, converter, mock_reference_registry):
        """Test activity with no GEVL relationships (no outcomes)."""
        # Create intervention without entryRelationships
        intervention = MockEntry("intervention-123")

        # Create outcome observation (not linked)
        outcome = MockEntry("outcome-456")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [outcome])

        # Verify activity has no outcomeReference field
        assert len(activities) == 1
        assert "reference" in activities[0]
        assert "outcomeReference" not in activities[0]

    def test_multiple_activities_with_different_outcomes(self, converter, mock_reference_registry):
        """Test multiple activities each with their own outcomes."""
        # Create two interventions with different outcomes
        intervention1 = MockEntry(
            "intervention-123",
            entry_relationships=[MockEntryRelationship("GEVL", "outcome-456")]
        )
        intervention2 = MockEntry(
            "intervention-789",
            entry_relationships=[MockEntryRelationship("GEVL", "outcome-999")]
        )

        # Create outcome observations
        outcome1 = MockEntry("outcome-456")
        outcome2 = MockEntry("outcome-999")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities(
            [intervention1, intervention2],
            [outcome1, outcome2]
        )

        # Verify each activity has its own outcome
        assert len(activities) == 2

        # First activity should have an outcome
        assert "outcomeReference" in activities[0]
        assert len(activities[0]["outcomeReference"]) == 1
        assert activities[0]["outcomeReference"][0]["reference"].startswith("Observation/")

        # Second activity should have a different outcome
        assert "outcomeReference" in activities[1]
        assert len(activities[1]["outcomeReference"]) == 1
        assert activities[1]["outcomeReference"][0]["reference"].startswith("Observation/")

        # Verify the outcomes are different
        assert activities[0]["outcomeReference"][0]["reference"] != activities[1]["outcomeReference"][0]["reference"]

    def test_outcomes_without_gevl_relationship_not_linked(self, converter, mock_reference_registry):
        """Test outcomes without GEVL relationship are not linked to activities."""
        # Create intervention with RSON relationship (not GEVL)
        intervention = MockEntry(
            "intervention-123",
            entry_relationships=[MockEntryRelationship("RSON", "outcome-456")]
        )

        # Create outcome observation
        outcome = MockEntry("outcome-456")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [outcome])

        # Verify activity has no outcomeReference (RSON is not GEVL)
        assert len(activities) == 1
        assert "outcomeReference" not in activities[0]

    def test_outcome_not_in_outcomes_list_not_linked(self, converter, mock_reference_registry):
        """Test outcome referenced in GEVL but not in outcomes list is not linked."""
        # Create intervention with GEVL to outcome-456
        intervention = MockEntry(
            "intervention-123",
            entry_relationships=[MockEntryRelationship("GEVL", "outcome-456")]
        )

        # Create different outcome (not the one referenced)
        outcome = MockEntry("outcome-789")

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [outcome])

        # Verify activity has no outcomeReference (outcome-456 not in list)
        assert len(activities) == 1
        assert "outcomeReference" not in activities[0]

    def test_intervention_without_id_skipped(self, converter, mock_reference_registry):
        """Test intervention without ID is skipped."""
        # Create intervention without id
        intervention = Mock()
        intervention.id = None
        intervention.entry_relationship = []

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [])

        # Verify no activities created
        assert len(activities) == 0

    def test_outcome_without_id_not_linked(self, converter, mock_reference_registry):
        """Test outcome without ID cannot be linked."""
        # Create intervention with GEVL
        intervention = MockEntry(
            "intervention-123",
            entry_relationships=[MockEntryRelationship("GEVL", "outcome-456")]
        )

        # Create outcome without id
        outcome = Mock()
        outcome.id = None

        # Link outcomes to activities
        activities = converter._link_outcomes_to_activities([intervention], [outcome])

        # Verify activity has no outcomeReference (outcome has no ID)
        assert len(activities) == 1
        assert "outcomeReference" not in activities[0]

    def test_get_entry_id_with_list_of_ids(self, converter, mock_reference_registry):
        """Test _get_entry_id handles list of IDs."""
        entry = MockEntry("test-id-123")
        entry_id = converter._get_entry_id(entry)
        assert entry_id == "test-id-123"

    def test_get_entry_id_with_single_id(self, converter, mock_reference_registry):
        """Test _get_entry_id handles single ID object."""
        entry = Mock()
        entry.id = Mock(root="test-id-456")
        entry_id = converter._get_entry_id(entry)
        assert entry_id == "test-id-456"

    def test_get_entry_id_with_no_id(self, converter, mock_reference_registry):
        """Test _get_entry_id returns None when no ID."""
        entry = Mock()
        entry.id = None
        entry_id = converter._get_entry_id(entry)
        assert entry_id is None

    def test_create_intervention_reference_as_service_request(self, converter, mock_reference_registry):
        """Test intervention reference created as ServiceRequest when in registry."""
        intervention = MockEntry("intervention-123")

        # Mock registry to have ServiceRequest
        converter.reference_registry.has_resource = Mock(
            side_effect=lambda resource_type, resource_id: resource_type == "ServiceRequest"
        )

        ref = converter._create_intervention_reference(intervention)
        assert ref.startswith("ServiceRequest/")

    def test_create_intervention_reference_as_procedure(self, converter, mock_reference_registry):
        """Test intervention reference created as Procedure when ServiceRequest not in registry."""
        intervention = MockEntry("intervention-123")

        # Mock registry to have Procedure but not ServiceRequest
        def has_resource_mock(resource_type, resource_id):
            return resource_type == "Procedure"

        converter.reference_registry.has_resource = Mock(side_effect=has_resource_mock)

        ref = converter._create_intervention_reference(intervention)
        assert ref.startswith("Procedure/")

    def test_create_intervention_reference_not_found(self, converter, mock_reference_registry):
        """Test intervention reference returns None when not in registry."""
        intervention = MockEntry("intervention-123")

        # Mock registry to not have resource
        converter.reference_registry.has_resource = Mock(return_value=False)

        ref = converter._create_intervention_reference(intervention)
        assert ref is None

    def test_create_outcome_reference_found_in_registry(self, converter, mock_reference_registry):
        """Test outcome reference created when Observation in registry."""
        outcome = MockEntry("outcome-456")

        ref = converter._create_outcome_reference(outcome)
        assert isinstance(ref, dict)
        assert "reference" in ref
        assert ref["reference"].startswith("Observation/")

    def test_create_outcome_reference_not_found(self, converter, mock_reference_registry):
        """Test outcome reference returns None when not in registry."""
        outcome = MockEntry("outcome-456")

        # Mock registry to not have resource
        converter.reference_registry.has_resource = Mock(return_value=False)

        ref = converter._create_outcome_reference(outcome)
        assert ref is None

    def test_create_outcome_reference_without_registry(self, mock_reference_registry):
        """Test outcome reference returns None when no registry."""
        converter = CarePlanConverter()  # No registry
        outcome = MockEntry("outcome-456")

        ref = converter._create_outcome_reference(outcome)
        assert ref is None

    def test_empty_interventions_list(self, converter, mock_reference_registry):
        """Test empty interventions list returns empty activities."""
        activities = converter._link_outcomes_to_activities([], [])
        assert activities == []

    def test_empty_outcomes_list_with_interventions(self, converter, mock_reference_registry):
        """Test interventions without outcomes still create activities."""
        intervention = MockEntry("intervention-123")

        activities = converter._link_outcomes_to_activities([intervention], [])

        # Verify activity created without outcomeReference
        assert len(activities) == 1
        assert "reference" in activities[0]
        assert "outcomeReference" not in activities[0]
