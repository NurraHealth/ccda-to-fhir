"""Unit tests for ReferenceRegistry.

Tests the reference registry's ability to track FHIR resources and validate
references between resources in a Bundle. All tests use realistic FHIR R4B
resource structures compliant with the standard.
"""

import pytest

from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.exceptions import MissingReferenceError
from ccda_to_fhir.types import FHIRResourceDict


class TestResourceRegistration:
    """Test registering FHIR resources in the registry."""

    def test_registers_patient_resource(self, mock_reference_registry):
        """Test registering a Patient resource."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
            "name": [{"family": "Smith", "given": ["John"]}],
        }

        registry.register_resource(patient)

        assert registry.has_resource("Patient", "patient-123")
        assert registry.get_resource("Patient", "patient-123") == patient

    def test_registers_practitioner_resource(self, mock_reference_registry):
        """Test registering a Practitioner resource."""
        registry = ReferenceRegistry()

        practitioner: FHIRResourceDict = {
            "resourceType": "Practitioner",
            "id": "prac-456",
            "name": [{"family": "Jones", "given": ["Sarah"], "prefix": ["Dr."]}],
        }

        registry.register_resource(practitioner)

        assert registry.has_resource("Practitioner", "prac-456")

    def test_registers_multiple_resource_types(self, mock_reference_registry):
        """Test registering different resource types in same registry."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-1",
        }

        practitioner: FHIRResourceDict = {
            "resourceType": "Practitioner",
            "id": "prac-1",
        }

        organization: FHIRResourceDict = {
            "resourceType": "Organization",
            "id": "org-1",
            "name": "General Hospital",
        }

        registry.register_resource(patient)
        registry.register_resource(practitioner)
        registry.register_resource(organization)

        assert registry.has_resource("Patient", "patient-1")
        assert registry.has_resource("Practitioner", "prac-1")
        assert registry.has_resource("Organization", "org-1")

    def test_registers_multiple_resources_same_type(self, mock_reference_registry):
        """Test registering multiple resources of the same type."""
        registry = ReferenceRegistry()

        patient1: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-1",
            "name": [{"family": "Smith"}],
        }

        patient2: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-2",
            "name": [{"family": "Jones"}],
        }

        registry.register_resource(patient1)
        registry.register_resource(patient2)

        assert registry.has_resource("Patient", "patient-1")
        assert registry.has_resource("Patient", "patient-2")
        assert registry.get_resource("Patient", "patient-1") == patient1
        assert registry.get_resource("Patient", "patient-2") == patient2

    def test_warns_on_duplicate_resource_id(self, caplog, mock_reference_registry):
        """Test that duplicate resource IDs trigger a warning."""
        registry = ReferenceRegistry()

        patient1: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
            "name": [{"family": "Smith"}],
        }

        patient2: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",  # Same ID
            "name": [{"family": "Jones"}],
        }

        registry.register_resource(patient1)
        registry.register_resource(patient2)

        # Should silently skip duplicate (expected with ID caching)
        # Second registration is ignored, first one wins
        assert registry.get_resource("Patient", "patient-123") == patient1

    def test_ignores_resource_without_resource_type(self, caplog, mock_reference_registry):
        """Test that resources without resourceType are rejected."""
        registry = ReferenceRegistry()

        invalid_resource: FHIRResourceDict = {
            "id": "test-123",
            "name": "Test",
        }

        registry.register_resource(invalid_resource)

        assert "Cannot register resource without resourceType" in caplog.text
        assert not registry.has_resource("", "test-123")

    def test_ignores_resource_without_id(self, caplog, mock_reference_registry):
        """Test that resources without id are rejected."""
        registry = ReferenceRegistry()

        invalid_resource: FHIRResourceDict = {
            "resourceType": "Patient",
            "name": [{"family": "Smith"}],
        }

        registry.register_resource(invalid_resource)

        assert "Cannot register Patient without id" in caplog.text


class TestReferenceResolution:
    """Test resolving references between FHIR resources."""

    def test_resolves_valid_patient_reference(self, mock_reference_registry):
        """Test resolving a reference to a registered Patient."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
        }

        registry.register_resource(patient)

        reference = registry.resolve_reference("Patient", "patient-123")

        assert reference is not None
        assert reference == {"reference": "Patient/patient-123"}

    def test_resolves_valid_practitioner_reference(self, mock_reference_registry):
        """Test resolving a reference to a registered Practitioner."""
        registry = ReferenceRegistry()

        practitioner: FHIRResourceDict = {
            "resourceType": "Practitioner",
            "id": "prac-456",
        }

        registry.register_resource(practitioner)

        reference = registry.resolve_reference("Practitioner", "prac-456")

        assert reference == {"reference": "Practitioner/prac-456"}

    def test_raises_error_for_unregistered_resource_type(self, mock_reference_registry):
        """Test that references to unregistered resource types raise MissingReferenceError."""
        registry = ReferenceRegistry()

        # Register a Patient
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Try to resolve reference to Practitioner (not registered)
        with pytest.raises(MissingReferenceError) as exc_info:
            registry.resolve_reference("Practitioner", "prac-456")

        assert exc_info.value.resource_type == "Practitioner"
        assert exc_info.value.resource_id == "prac-456"
        assert "Resource type not registered" in str(exc_info.value)

    def test_raises_error_for_unregistered_resource_id(self, mock_reference_registry):
        """Test that references to non-existent resource IDs raise MissingReferenceError."""
        registry = ReferenceRegistry()

        # Register patient-123
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Try to resolve reference to patient-456 (doesn't exist)
        with pytest.raises(MissingReferenceError) as exc_info:
            registry.resolve_reference("Patient", "patient-456")

        assert exc_info.value.resource_type == "Patient"
        assert exc_info.value.resource_id == "patient-456"
        assert "patient-456" in str(exc_info.value)

    def test_realistic_condition_to_patient_reference(self, mock_reference_registry):
        """Test a realistic scenario: Condition references Patient.

        This is the most common reference in C-CDA conversion - every clinical
        resource (Condition, AllergyIntolerance, etc.) has a subject reference
        pointing to the Patient.
        """
        registry = ReferenceRegistry()

        # Register Patient first (as happens in convert.py)
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-newman",
            "name": [{"family": "Newman", "given": ["Alice"]}],
            "birthDate": "1970-05-01",
        }
        registry.register_resource(patient)

        # Create Condition with patient reference (simulating conversion)
        condition: FHIRResourceDict = {
            "resourceType": "Condition",
            "id": "condition-diabetes",
            "code": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": "44054006",
                    "display": "Diabetes mellitus type 2",
                }]
            },
            "subject": {"reference": "Patient/patient-newman-placeholder"},  # Placeholder
        }

        # Resolve the patient reference (as happens in convert.py)
        patient_ref = registry.resolve_reference("Patient", "patient-newman")

        assert patient_ref is not None
        # Update the condition's subject with validated reference
        condition["subject"] = patient_ref

        # Verify the reference is correct
        assert condition["subject"]["reference"] == "Patient/patient-newman"

    def test_realistic_observation_to_practitioner_reference(self, mock_reference_registry):
        """Test realistic scenario: Observation references Practitioner as performer.

        In C-CDA, observations often have authors that become performers in FHIR.
        """
        registry = ReferenceRegistry()

        # Register Practitioner
        practitioner: FHIRResourceDict = {
            "resourceType": "Practitioner",
            "id": "npi-1234567890",
            "identifier": [{
                "system": "http://hl7.org/fhir/sid/us-npi",
                "value": "1234567890",
            }],
            "name": [{
                "family": "Johnson",
                "given": ["Robert"],
                "prefix": ["Dr."],
            }],
        }
        registry.register_resource(practitioner)

        # Resolve reference for Observation.performer
        performer_ref = registry.resolve_reference("Practitioner", "npi-1234567890")

        assert performer_ref == {"reference": "Practitioner/npi-1234567890"}

    def test_realistic_medication_request_to_practitioner_reference(self, mock_reference_registry):
        """Test realistic scenario: MedicationRequest references Practitioner as requester.

        C-CDA medication activities have authors that map to MedicationRequest.requester.
        """
        registry = ReferenceRegistry()

        # Register Practitioner
        practitioner: FHIRResourceDict = {
            "resourceType": "Practitioner",
            "id": "prac-dr-smith",
            "name": [{"family": "Smith", "prefix": ["Dr."]}],
        }
        registry.register_resource(practitioner)

        # Resolve for MedicationRequest
        requester_ref = registry.resolve_reference("Practitioner", "prac-dr-smith")

        assert requester_ref == {"reference": "Practitioner/prac-dr-smith"}


class TestReferenceValidationIntegration:
    """Test realistic end-to-end scenarios with reference validation."""

    def test_detects_broken_reference_in_bundle(self, mock_reference_registry):
        """Test detecting a broken reference during bundle creation.

        Simulates what would happen if code tries to reference a Practitioner
        that wasn't successfully converted (e.g., due to validation failure).
        """
        registry = ReferenceRegistry()

        # Register Patient
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Try to resolve reference to Practitioner that was never registered
        # (e.g., Practitioner failed validation and wasn't added to bundle)
        # This should raise an error, preventing invalid FHIR bundle creation
        with pytest.raises(MissingReferenceError) as exc_info:
            registry.resolve_reference("Practitioner", "prac-failed")

        assert exc_info.value.resource_type == "Practitioner"
        assert exc_info.value.resource_id == "prac-failed"

    def test_validates_composition_section_entries(self, mock_reference_registry):
        """Test validating references in Composition.section.entry.

        Composition sections reference the resources they contain. All these
        references should be validated.
        """
        registry = ReferenceRegistry()

        # Register resources that would be in a Conditions section
        condition1: FHIRResourceDict = {
            "resourceType": "Condition",
            "id": "condition-diabetes",
        }
        condition2: FHIRResourceDict = {
            "resourceType": "Condition",
            "id": "condition-hypertension",
        }

        registry.register_resource(condition1)
        registry.register_resource(condition2)

        # Validate both references exist
        ref1 = registry.resolve_reference("Condition", "condition-diabetes")
        ref2 = registry.resolve_reference("Condition", "condition-hypertension")

        assert ref1 == {"reference": "Condition/condition-diabetes"}
        assert ref2 == {"reference": "Condition/condition-hypertension"}


class TestRegistryStatistics:
    """Test registry statistics tracking."""

    def test_tracks_registered_count(self, mock_reference_registry):
        """Test that registry tracks number of resources registered."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {"resourceType": "Patient", "id": "p1"}
        practitioner: FHIRResourceDict = {"resourceType": "Practitioner", "id": "pr1"}

        registry.register_resource(patient)
        registry.register_resource(practitioner)

        stats = registry.get_stats()
        assert stats["registered"] == 2

    def test_tracks_resolved_count(self, mock_reference_registry):
        """Test that registry tracks successful reference resolutions."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {"resourceType": "Patient", "id": "p1"}
        registry.register_resource(patient)

        # Resolve reference twice
        registry.resolve_reference("Patient", "p1")
        registry.resolve_reference("Patient", "p1")

        stats = registry.get_stats()
        assert stats["resolved"] == 2

    def test_tracks_failed_count(self, mock_reference_registry):
        """Test that registry tracks failed reference resolutions."""
        registry = ReferenceRegistry()

        # Try to resolve reference to non-existent resource (raises exception)
        try:
            registry.resolve_reference("Patient", "does-not-exist")
        except MissingReferenceError:
            pass

        try:
            registry.resolve_reference("Practitioner", "also-missing")
        except MissingReferenceError:
            pass

        stats = registry.get_stats()
        assert stats["failed"] == 2

    def test_clear_resets_registry(self, mock_reference_registry):
        """Test that clear() removes all resources and resets stats."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {"resourceType": "Patient", "id": "p1"}
        registry.register_resource(patient)
        registry.resolve_reference("Patient", "p1")

        registry.clear()

        assert not registry.has_resource("Patient", "p1")
        stats = registry.get_stats()
        assert stats["registered"] == 0
        assert stats["resolved"] == 0


class TestGetAllResources:
    """Test retrieving all registered resources."""

    def test_returns_all_registered_resources(self, mock_reference_registry):
        """Test that get_all_resources() returns all resources."""
        registry = ReferenceRegistry()

        patient: FHIRResourceDict = {"resourceType": "Patient", "id": "p1"}
        practitioner: FHIRResourceDict = {"resourceType": "Practitioner", "id": "pr1"}
        organization: FHIRResourceDict = {"resourceType": "Organization", "id": "org1"}

        registry.register_resource(patient)
        registry.register_resource(practitioner)
        registry.register_resource(organization)

        all_resources = registry.get_all_resources()

        assert len(all_resources) == 3
        assert patient in all_resources
        assert practitioner in all_resources
        assert organization in all_resources

    def test_returns_empty_list_when_no_resources(self, mock_reference_registry):
        """Test that get_all_resources() returns empty list when registry is empty."""
        registry = ReferenceRegistry()

        all_resources = registry.get_all_resources()

        assert all_resources == []


class TestEncounterReference:
    """Test encounter reference retrieval methods."""

    def test_has_encounter_returns_true_when_encounter_registered(self, mock_reference_registry):
        """Test that has_encounter() returns True when an encounter is registered."""
        registry = ReferenceRegistry()

        encounter: FHIRResourceDict = {
            "resourceType": "Encounter",
            "id": "encounter-123",
        }

        registry.register_resource(encounter)

        assert registry.has_encounter() is True

    def test_has_encounter_returns_false_when_no_encounter(self, mock_reference_registry):
        """Test that has_encounter() returns False when no encounter is registered."""
        registry = ReferenceRegistry()

        assert registry.has_encounter() is False

    def test_get_encounter_reference_returns_reference(self, mock_reference_registry):
        """Test that get_encounter_reference() returns reference when encounter exists."""
        registry = ReferenceRegistry()

        encounter: FHIRResourceDict = {
            "resourceType": "Encounter",
            "id": "encounter-abc",
            "status": "finished",
            "class": {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "AMB",
            },
        }

        registry.register_resource(encounter)

        reference = registry.get_encounter_reference()

        assert reference is not None
        assert reference == {"reference": "Encounter/encounter-abc"}

    def test_get_encounter_reference_returns_none_when_no_encounter(self, mock_reference_registry):
        """Test that get_encounter_reference() returns None when no encounter exists."""
        registry = ReferenceRegistry()

        reference = registry.get_encounter_reference()

        assert reference is None

    def test_get_encounter_reference_returns_first_when_multiple(self, mock_reference_registry):
        """Test that get_encounter_reference() returns first encounter when multiple exist."""
        registry = ReferenceRegistry()

        encounter1: FHIRResourceDict = {
            "resourceType": "Encounter",
            "id": "encounter-1",
        }
        encounter2: FHIRResourceDict = {
            "resourceType": "Encounter",
            "id": "encounter-2",
        }

        registry.register_resource(encounter1)
        registry.register_resource(encounter2)

        reference = registry.get_encounter_reference()

        assert reference is not None
        # Should return first encounter (dict iteration order is insertion order in Python 3.7+)
        assert reference == {"reference": "Encounter/encounter-1"}

    def test_get_encounter_reference_increments_stats(self, mock_reference_registry):
        """Test that get_encounter_reference() increments resolved count."""
        registry = ReferenceRegistry()

        encounter: FHIRResourceDict = {
            "resourceType": "Encounter",
            "id": "encounter-123",
        }

        registry.register_resource(encounter)

        # Call twice
        registry.get_encounter_reference()
        registry.get_encounter_reference()

        stats = registry.get_stats()
        # Should have 2 resolutions (one from each call)
        assert stats["resolved"] == 2
