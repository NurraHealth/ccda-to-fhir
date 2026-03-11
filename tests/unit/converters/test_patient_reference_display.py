"""Unit tests for patient reference display text.

Tests that get_patient_reference() includes display text extracted from the
registered Patient resource name, per FHIR R4 Reference.display (0..1).
"""

from ccda_to_fhir.converters.references import ReferenceRegistry, _extract_patient_display
from ccda_to_fhir.types import FHIRResourceDict


class TestExtractPatientDisplay:
    """Test _extract_patient_display helper."""

    def test_extracts_given_and_family(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"family": "Smith", "given": ["John"]}],
        }
        assert _extract_patient_display(patient) == "John Smith"

    def test_extracts_multiple_given_names(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"family": "Newman", "given": ["Alice", "Marie"]}],
        }
        assert _extract_patient_display(patient) == "Alice Marie Newman"

    def test_extracts_prefix_given_family_suffix(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{
                "prefix": ["Dr."],
                "given": ["Robert"],
                "family": "Jones",
                "suffix": ["III"],
            }],
        }
        assert _extract_patient_display(patient) == "Dr. Robert Jones III"

    def test_extracts_family_only(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"family": "Doe"}],
        }
        assert _extract_patient_display(patient) == "Doe"

    def test_returns_none_when_no_name(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
        }
        assert _extract_patient_display(patient) is None

    def test_returns_none_when_name_list_empty(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [],
        }
        assert _extract_patient_display(patient) is None

    def test_returns_none_when_name_has_no_parts(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{}],
        }
        assert _extract_patient_display(patient) is None

    def test_skips_empty_strings_in_given(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"given": ["", "Jane"], "family": "Doe"}],
        }
        assert _extract_patient_display(patient) == "Jane Doe"

    def test_uses_first_name_entry(self):
        """Uses the first HumanName even when multiple are present."""
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [
                {"family": "Smith", "given": ["John"], "use": "official"},
                {"family": "Johnny", "given": ["J"], "use": "nickname"},
            ],
        }
        assert _extract_patient_display(patient) == "John Smith"

    def test_prefers_text_over_parts(self):
        """Per FHIR R4, HumanName.text is preferred when present."""
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"text": "Dr. John H. Smith III", "family": "Smith", "given": ["John"]}],
        }
        assert _extract_patient_display(patient) == "Dr. John H. Smith III"

    def test_falls_back_to_parts_when_text_empty(self):
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"text": "  ", "family": "Doe", "given": ["Jane"]}],
        }
        assert _extract_patient_display(patient) == "Jane Doe"


class TestGetPatientReferenceDisplay:
    """Test that get_patient_reference() includes display."""

    def test_includes_display_when_name_present(self):
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
            "name": [{"family": "Smith", "given": ["John"]}],
        }
        registry.register_resource(patient)

        ref = registry.get_patient_reference()

        assert ref["reference"] == "urn:uuid:patient-123"
        assert ref["display"] == "John Smith"

    def test_omits_display_when_no_name(self):
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        ref = registry.get_patient_reference()

        assert ref["reference"] == "urn:uuid:patient-123"
        assert "display" not in ref

    def test_display_with_prefix_and_suffix(self):
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-456",
            "name": [{
                "prefix": ["Mrs."],
                "given": ["Alice"],
                "family": "Newman",
                "suffix": ["PhD"],
            }],
        }
        registry.register_resource(patient)

        ref = registry.get_patient_reference()

        assert ref["display"] == "Mrs. Alice Newman PhD"

    def test_display_uses_first_patient_when_multiple_registered(self):
        """When multiple patients are registered, display matches the first."""
        registry = ReferenceRegistry()
        patient1: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-1",
            "name": [{"family": "Smith", "given": ["John"]}],
        }
        patient2: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-2",
            "name": [{"family": "Jones", "given": ["Alice"]}],
        }
        registry.register_resource(patient1)
        registry.register_resource(patient2)

        ref = registry.get_patient_reference()

        # get_patient_reference returns the first patient's ID
        assert ref["reference"] == "urn:uuid:patient-1"
        # display must match the first patient, not the second
        assert ref["display"] == "John Smith"

    def test_display_survives_multiple_calls(self):
        """Display should be returned on every call."""
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "patient-789",
            "name": [{"family": "Doe", "given": ["Jane"]}],
        }
        registry.register_resource(patient)

        ref1 = registry.get_patient_reference()
        ref2 = registry.get_patient_reference()

        assert ref1["display"] == "Jane Doe"
        assert ref2["display"] == "Jane Doe"


class TestPatientDisplayProperty:
    """Test the patient_display public property."""

    def test_returns_none_before_registration(self):
        registry = ReferenceRegistry()
        assert registry.patient_display is None

    def test_returns_display_after_registration(self):
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"family": "Smith", "given": ["John"]}],
        }
        registry.register_resource(patient)
        assert registry.patient_display == "John Smith"

    def test_cleared_after_clear(self):
        registry = ReferenceRegistry()
        patient: FHIRResourceDict = {
            "resourceType": "Patient",
            "id": "p1",
            "name": [{"family": "Smith", "given": ["John"]}],
        }
        registry.register_resource(patient)
        registry.clear()
        assert registry.patient_display is None
