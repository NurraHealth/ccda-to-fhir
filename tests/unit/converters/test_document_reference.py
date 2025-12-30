"""Comprehensive unit tests for DocumentReference converter.

Tests DocumentReference resource conversion following:
- FHIR R4 DocumentReference resource specification
- C-CDA on FHIR IG DocumentReference mapping
- Document status inference from authenticators

All test data based on realistic clinical scenarios and official HL7 examples.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.clinical_document import (
    Authenticator,
    ClinicalDocument,
    LegalAuthenticator,
    RecordTarget,
)
from ccda_to_fhir.ccda.models.datatypes import CE, CS, II, TS
from ccda_to_fhir.ccda.models.performer import AssignedEntity, AssignedPerson
from ccda_to_fhir.ccda.models.record_target import Patient, PatientRole
from ccda_to_fhir.converters.document_reference import DocumentReferenceConverter
from ccda_to_fhir.converters.references import ReferenceRegistry

# ============================================================================
# Fixtures - Realistic C-CDA Clinical Document Data
# ============================================================================


@pytest.fixture
def basic_patient() -> Patient:
    """Create a basic patient for testing."""
    from ccda_to_fhir.ccda.models.datatypes import ENXP, PN

    return Patient(
        name=[
            PN(
                given=[ENXP(value="Test")],
                family=ENXP(value="Patient"),
            )
        ],
        administrative_gender_code=CE(
            code="F",
            code_system="2.16.840.1.113883.5.1",
            display_name="Female",
        ),
        birth_time=TS(value="19800101"),
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
def basic_clinical_document(basic_record_target) -> ClinicalDocument:
    """Create a basic clinical document."""
    return ClinicalDocument(
        id=II(root="2.16.840.1.113883.19.5.99999.1", extension="doc-123"),
        code=CE(
            code="34133-9",
            code_system="2.16.840.1.113883.6.1",
            display_name="Summarization of Episode Note",
        ),
        title="Test Document",
        effective_time=TS(value="20231215120000-0500"),
        confidentiality_code=CE(
            code="N",
            code_system="2.16.840.1.113883.5.25",
            display_name="Normal",
        ),
        language_code=CS(code="en-US"),
        record_target=[basic_record_target],
    )


@pytest.fixture
def legal_authenticator() -> LegalAuthenticator:
    """Create a legal authenticator."""
    from ccda_to_fhir.ccda.models.datatypes import ENXP, PN

    return LegalAuthenticator(
        time=TS(value="20231215120000-0500"),
        signature_code=CS(code="S"),
        assigned_entity=AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="legal-auth-123")],
            assigned_person=AssignedPerson(
                name=[
                    PN(
                        given=[ENXP(value="Legal")],
                        family=ENXP(value="Authenticator"),
                    )
                ]
            ),
        ),
    )


@pytest.fixture
def regular_authenticator() -> Authenticator:
    """Create a regular authenticator."""
    from ccda_to_fhir.ccda.models.datatypes import ENXP, PN

    return Authenticator(
        time=TS(value="20231215120000-0500"),
        signature_code=CS(code="S"),
        assigned_entity=AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="auth-123")],
            assigned_person=AssignedPerson(
                name=[
                    PN(
                        given=[ENXP(value="Regular")],
                        family=ENXP(value="Authenticator"),
                    )
                ]
            ),
        ),
    )


@pytest.fixture
def reference_registry() -> ReferenceRegistry:
    """Create a reference registry with a patient."""
    registry = ReferenceRegistry()
    # Register a patient resource
    registry.register_resource({
        "resourceType": "Patient",
        "id": "patient-123"
    })
    return registry


@pytest.fixture
def converter(reference_registry) -> DocumentReferenceConverter:
    """Create a DocumentReference converter."""
    return DocumentReferenceConverter(
        reference_registry=reference_registry,
        original_xml="<ClinicalDocument>test</ClinicalDocument>"
    )


# ============================================================================
# Tests - Document Status Inference
# ============================================================================


class TestDocStatusInference:
    """Test docStatus inference from authenticators."""

    def test_doc_status_final_with_legal_authenticator(
        self,
        basic_clinical_document,
        legal_authenticator,
        converter
    ) -> None:
        """Test docStatus='final' when legalAuthenticator present."""
        # Add legal authenticator to document
        basic_clinical_document.legal_authenticator = legal_authenticator

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is 'final'
        assert "docStatus" in doc_ref
        assert doc_ref["docStatus"] == "final"

    def test_doc_status_preliminary_with_authenticator(
        self,
        basic_clinical_document,
        regular_authenticator,
        converter
    ) -> None:
        """Test docStatus='preliminary' when authenticator present."""
        # Add regular authenticator as list (no legal authenticator)
        basic_clinical_document.authenticator = [regular_authenticator]

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is 'preliminary'
        assert "docStatus" in doc_ref
        assert doc_ref["docStatus"] == "preliminary"

    def test_doc_status_preliminary_with_authenticator_list(
        self,
        basic_clinical_document,
        regular_authenticator,
        converter
    ) -> None:
        """Test docStatus='preliminary' when authenticator is a list."""
        # Add authenticator as list
        basic_clinical_document.authenticator = [regular_authenticator]

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is 'preliminary'
        assert "docStatus" in doc_ref
        assert doc_ref["docStatus"] == "preliminary"

    def test_doc_status_omitted_without_authenticators(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test docStatus omitted when no authenticators."""
        # Ensure no authenticators
        basic_clinical_document.legal_authenticator = None
        basic_clinical_document.authenticator = None

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is not present
        assert "docStatus" not in doc_ref

    def test_doc_status_final_takes_precedence_over_authenticator(
        self,
        basic_clinical_document,
        legal_authenticator,
        regular_authenticator,
        converter
    ) -> None:
        """Test legalAuthenticator takes precedence when both present."""
        # Add both legal and regular authenticators
        basic_clinical_document.legal_authenticator = legal_authenticator
        basic_clinical_document.authenticator = [regular_authenticator]

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is 'final' (legal takes precedence)
        assert "docStatus" in doc_ref
        assert doc_ref["docStatus"] == "final"

    def test_doc_status_omitted_with_empty_authenticator_list(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test docStatus omitted when authenticator list is empty."""
        # Set authenticator to empty list
        basic_clinical_document.authenticator = []

        # Convert
        doc_ref = converter.convert(basic_clinical_document)

        # Verify docStatus is not present
        assert "docStatus" not in doc_ref


# ============================================================================
# Tests - Basic Conversion Validation
# ============================================================================


class TestBasicConversion:
    """Test basic DocumentReference conversion."""

    def test_converts_basic_document(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test basic DocumentReference creation."""
        doc_ref = converter.convert(basic_clinical_document)

        # Verify basic structure
        assert doc_ref["resourceType"] == "DocumentReference"
        assert doc_ref["status"] == "current"
        assert "id" in doc_ref
        assert "masterIdentifier" in doc_ref
        assert "type" in doc_ref
        assert "subject" in doc_ref
        assert "date" in doc_ref
        assert "content" in doc_ref

    def test_converts_with_all_authenticators(
        self,
        basic_clinical_document,
        legal_authenticator,
        regular_authenticator,
        converter
    ) -> None:
        """Test conversion with both types of authenticators."""
        basic_clinical_document.legal_authenticator = legal_authenticator
        basic_clinical_document.authenticator = [regular_authenticator]

        doc_ref = converter.convert(basic_clinical_document)

        # Verify conversion succeeded
        assert doc_ref["resourceType"] == "DocumentReference"
        # Verify legal authenticator referenced
        assert "authenticator" in doc_ref
        # Verify docStatus is final
        assert doc_ref["docStatus"] == "final"

    def test_resource_type_is_document_reference(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test resourceType is DocumentReference."""
        doc_ref = converter.convert(basic_clinical_document)
        assert doc_ref["resourceType"] == "DocumentReference"


# ============================================================================
# Tests - Edge Cases
# ============================================================================


class TestEdgeCases:
    """Test edge cases for docStatus inference."""

    def test_handles_none_legal_authenticator(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test handles None legalAuthenticator gracefully."""
        basic_clinical_document.legal_authenticator = None
        basic_clinical_document.authenticator = None

        doc_ref = converter.convert(basic_clinical_document)

        # Should not have docStatus
        assert "docStatus" not in doc_ref

    def test_handles_missing_authenticator_attribute(
        self,
        basic_clinical_document,
        converter
    ) -> None:
        """Test handles missing authenticator attribute."""
        # Ensure authenticator attributes are None (default for optional Pydantic fields)
        basic_clinical_document.authenticator = None
        basic_clinical_document.legal_authenticator = None

        doc_ref = converter.convert(basic_clinical_document)

        # Should not have docStatus
        assert "docStatus" not in doc_ref

    def test_converts_document_without_optional_fields(
        self,
        reference_registry
    ) -> None:
        """Test converts minimal document without optional authenticators."""
        # Create minimal document
        minimal_doc = ClinicalDocument(
            id=II(root="2.16.840.1.113883.19.5.99999.1"),
            code=CE(
                code="34133-9",
                code_system="2.16.840.1.113883.6.1",
                display_name="Test",
            ),
            effective_time=TS(value="20231215120000-0500"),
            confidentiality_code=CE(code="N", code_system="2.16.840.1.113883.5.25"),
            language_code=CS(code="en-US"),
            record_target=[],
        )

        converter = DocumentReferenceConverter(
            reference_registry=reference_registry,
            original_xml="<ClinicalDocument/>"
        )

        doc_ref = converter.convert(minimal_doc)

        # Verify conversion succeeded
        assert doc_ref["resourceType"] == "DocumentReference"
        # Should not have docStatus
        assert "docStatus" not in doc_ref
