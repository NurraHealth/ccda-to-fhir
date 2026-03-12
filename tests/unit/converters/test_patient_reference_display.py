"""Unit tests for patient reference display text.

Tests that get_patient_reference() includes display text extracted from the
registered Patient resource name, per FHIR R4 Reference.display (0..1).
"""

from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.types import format_human_name_display


class TestFormatHumanNameDisplay:
    """Test format_human_name_display helper."""

    def test_given_and_family(self):
        assert format_human_name_display({"family": "Smith", "given": ["John"]}) == "John Smith"

    def test_multiple_given_names(self):
        assert (
            format_human_name_display({"family": "Newman", "given": ["Alice", "Marie"]})
            == "Alice Marie Newman"
        )

    def test_prefix_given_family_suffix(self):
        name = {"prefix": ["Dr."], "given": ["Robert"], "family": "Jones", "suffix": ["III"]}
        assert format_human_name_display(name) == "Dr. Robert Jones III"

    def test_family_only(self):
        assert format_human_name_display({"family": "Doe"}) == "Doe"

    def test_returns_none_when_empty(self):
        assert format_human_name_display({}) is None

    def test_skips_empty_strings_in_given(self):
        assert format_human_name_display({"given": ["", "Jane"], "family": "Doe"}) == "Jane Doe"

    def test_prefers_text_over_parts(self):
        """Per FHIR R4, HumanName.text is preferred when present."""
        name = {"text": "Dr. John H. Smith III", "family": "Smith", "given": ["John"]}
        assert format_human_name_display(name) == "Dr. John H. Smith III"

    def test_falls_back_to_parts_when_text_empty(self):
        assert (
            format_human_name_display({"text": "  ", "family": "Doe", "given": ["Jane"]})
            == "Jane Doe"
        )


class TestGetPatientReferenceDisplay:
    """Test that get_patient_reference() includes display."""

    def _register_patient(
        self,
        registry: ReferenceRegistry,
        patient_id: str,
        display: str | None = None,
    ) -> None:
        """Register a patient and optionally set the display."""
        registry.register_resource({"resourceType": "Patient", "id": patient_id})
        if display is not None and registry.patient_display is None:
            registry.patient_display = display

    def test_includes_display_when_set(self):
        registry = ReferenceRegistry()
        self._register_patient(registry, "patient-123", "John Smith")

        ref = registry.get_patient_reference()

        assert ref["reference"] == "urn:uuid:patient-123"
        assert ref["display"] == "John Smith"

    def test_omits_display_when_not_set(self):
        registry = ReferenceRegistry()
        self._register_patient(registry, "patient-123")

        ref = registry.get_patient_reference()

        assert ref["reference"] == "urn:uuid:patient-123"
        assert "display" not in ref

    def test_display_survives_multiple_calls(self):
        """Display should be returned on every call."""
        registry = ReferenceRegistry()
        self._register_patient(registry, "patient-789", "Jane Doe")

        ref1 = registry.get_patient_reference()
        ref2 = registry.get_patient_reference()

        assert ref1["display"] == "Jane Doe"
        assert ref2["display"] == "Jane Doe"


class TestPatientDisplayProperty:
    """Test the patient_display property."""

    def test_returns_none_before_set(self):
        registry = ReferenceRegistry()
        assert registry.patient_display is None

    def test_set_and_get(self):
        registry = ReferenceRegistry()
        registry.patient_display = "John Smith"
        assert registry.patient_display == "John Smith"

    def test_cleared_after_clear(self):
        registry = ReferenceRegistry()
        registry.patient_display = "John Smith"
        registry.clear()
        assert registry.patient_display is None
