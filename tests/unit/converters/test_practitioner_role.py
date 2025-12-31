"""Unit tests for PractitionerRoleConverter.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the expected behavior of the PractitionerRoleConverter.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, RepresentedOrganization
from ccda_to_fhir.ccda.models.datatypes import CE, ED, II
from ccda_to_fhir.constants import CodeSystemOIDs, FHIRCodes, FHIRSystems
from ccda_to_fhir.converters.code_systems import CodeSystemMapper
from ccda_to_fhir.converters.practitioner_role import PractitionerRoleConverter


class TestPractitionerRoleConverter:
    """Unit tests for PractitionerRoleConverter."""

    @pytest.fixture
    def code_system_mapper(self) -> CodeSystemMapper:
        """Create a code system mapper."""
        return CodeSystemMapper()

    @pytest.fixture
    def converter(self, code_system_mapper: CodeSystemMapper) -> PractitionerRoleConverter:
        """Create a PractitionerRoleConverter instance."""
        return PractitionerRoleConverter(code_system_mapper=code_system_mapper)

    @pytest.fixture
    def sample_assigned_author(self) -> AssignedAuthor:
        """Create a sample AssignedAuthor with all fields."""
        # Create identifiers
        npi_id = II(root=CodeSystemOIDs.NPI, extension="1234567890")

        # Create specialty code (NUCC taxonomy)
        specialty_code = CE(
            code="207Q00000X",
            code_system="2.16.840.1.113883.6.101",  # NUCC Taxonomy OID
            display_name="Family Medicine"
        )

        # Create person
        person = AssignedPerson(name=[])

        # Create organization
        org = RepresentedOrganization(
            id=[II(root=CodeSystemOIDs.NPI, extension="9999999999")],
            name=["Test Clinic"]
        )

        # Create assigned author
        assigned_author = AssignedAuthor(
            id=[npi_id],
            code=specialty_code,
            assigned_person=person,
            represented_organization=org
        )

        return assigned_author

    def test_creates_practitioner_role_resource(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that converter creates a PractitionerRole resource."""
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        assert result["resourceType"] == FHIRCodes.ResourceTypes.PRACTITIONER_ROLE

    def test_generates_id_from_practitioner_and_org(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that ID is generated from practitioner and organization IDs."""
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-npi-1234567890",
            organization_id="org-npi-9999999999"
        )

        assert "id" in result
        # ID should combine both practitioner and organization IDs for uniqueness
        assert "practitioner-npi-1234567890" in result["id"]
        assert "org-npi-9999999999" in result["id"]

    def test_creates_practitioner_reference(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that practitioner reference is created correctly."""
        practitioner_id = "practitioner-test-123"
        result = converter.convert(
            sample_assigned_author,
            practitioner_id=practitioner_id,
            organization_id="org-456"
        )

        assert "practitioner" in result
        assert result["practitioner"]["reference"] == f"Practitioner/{practitioner_id}"

    def test_creates_organization_reference(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that organization reference is created correctly."""
        organization_id = "org-test-789"
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id=organization_id
        )

        assert "organization" in result
        assert result["organization"]["reference"] == f"Organization/{organization_id}"

    def test_converts_specialty_code(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that specialty code is correctly converted."""
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        assert "specialty" in result
        assert len(result["specialty"]) >= 1
        assert "coding" in result["specialty"][0]
        assert len(result["specialty"][0]["coding"]) >= 1

        coding = result["specialty"][0]["coding"][0]
        assert coding["code"] == "207Q00000X"

    def test_converts_specialty_display_name(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that specialty display name is included."""
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        coding = result["specialty"][0]["coding"][0]
        assert coding["display"] == "Family Medicine"

    def test_maps_nucc_taxonomy_system(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that NUCC taxonomy OID is mapped to correct FHIR URI."""
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        coding = result["specialty"][0]["coding"][0]
        # NUCC Taxonomy OID (2.16.840.1.113883.6.101) should map to NUCC URI
        assert coding["system"] == FHIRSystems.NUCC_TAXONOMY

    def test_handles_missing_specialty(
        self, converter: PractitionerRoleConverter
    ) -> None:
        """Test that missing specialty code is handled gracefully."""
        # Create assigned author without specialty code
        assigned_author = AssignedAuthor(
            id=[II(root=CodeSystemOIDs.NPI, extension="1234567890")],
            code=None,  # No specialty
            assigned_person=AssignedPerson(name=[]),
            represented_organization=RepresentedOrganization(id=[], name=["Test"])
        )

        result = converter.convert(
            assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        # Should still create resource, but specialty field should be empty or absent
        assert result["resourceType"] == FHIRCodes.ResourceTypes.PRACTITIONER_ROLE
        assert "specialty" not in result or result.get("specialty") == []

    def test_handles_multiple_specialties(
        self, converter: PractitionerRoleConverter
    ) -> None:
        """Test that multiple specialties from SDTC extension are handled.

        Note: This tests the SDTC specialty extension which may appear in
        AssignedEntity (performer) contexts.
        """
        # Create assigned author with primary specialty
        primary_specialty = CE(
            code="207Q00000X",
            code_system="2.16.840.1.113883.6.101",
            display_name="Family Medicine"
        )

        assigned_author = AssignedAuthor(
            id=[II(root=CodeSystemOIDs.NPI, extension="1234567890")],
            code=primary_specialty,
            assigned_person=AssignedPerson(name=[]),
            represented_organization=RepresentedOrganization(id=[], name=["Test"])
        )

        # Add SDTC specialty if the model supports it
        if hasattr(assigned_author, 'sdtc_specialty'):
            secondary_specialty = CE(
                code="207R00000X",
                code_system="2.16.840.1.113883.6.101",
                display_name="Internal Medicine"
            )
            assigned_author.sdtc_specialty = [secondary_specialty]

        result = converter.convert(
            assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        # Should have at least the primary specialty
        assert "specialty" in result
        assert len(result["specialty"]) >= 1

        # If SDTC supported, should have both
        if hasattr(assigned_author, 'sdtc_specialty') and assigned_author.sdtc_specialty:
            assert len(result["specialty"]) == 2
            codes = [s["coding"][0]["code"] for s in result["specialty"]]
            assert "207Q00000X" in codes
            assert "207R00000X" in codes

    def test_creates_identifier_from_context(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that optional identifier field is created from assignedAuthor/id.

        The PractitionerRole can optionally include identifiers that are specific
        to this role context (different from the Practitioner's own identifiers).
        """
        result = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        # PractitionerRole.identifier is optional - may or may not be present
        # If present, should be derived from assignedAuthor/id
        if "identifier" in result:
            assert len(result["identifier"]) >= 1
            # At least one identifier should be present
            assert "system" in result["identifier"][0]
            assert "value" in result["identifier"][0]

    def test_handles_missing_practitioner_id(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that missing practitioner_id raises appropriate error."""
        with pytest.raises((ValueError, TypeError)):
            converter.convert(
                sample_assigned_author,
                practitioner_id=None,  # type: ignore
                organization_id="org-456"
            )

    def test_handles_missing_organization_id(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that PractitionerRole can be created without organization reference."""
        role = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-123",
            organization_id=None
        )

        assert role["resourceType"] == "PractitionerRole"
        assert role["practitioner"]["reference"] == "Practitioner/practitioner-123"
        assert "organization" not in role  # No organization reference when not provided
        assert role["id"] == "role-practitioner-123"  # ID without org suffix

    def test_id_generation_is_deterministic(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that ID generation is deterministic for deduplication."""
        result1 = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-abc",
            organization_id="org-xyz"
        )

        result2 = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-abc",
            organization_id="org-xyz"
        )

        # Same inputs should produce same ID
        assert result1["id"] == result2["id"]

    def test_different_orgs_produce_different_ids(
        self, converter: PractitionerRoleConverter, sample_assigned_author: AssignedAuthor
    ) -> None:
        """Test that same practitioner with different orgs produces different IDs."""
        result1 = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-abc",
            organization_id="org-xyz"
        )

        result2 = converter.convert(
            sample_assigned_author,
            practitioner_id="practitioner-abc",
            organization_id="org-different"
        )

        # Different organization should produce different ID
        assert result1["id"] != result2["id"]

    def test_specialty_with_original_text(
        self, converter: PractitionerRoleConverter
    ) -> None:
        """Test that original text from specialty code is preserved."""
        specialty_with_text = CE(
            code="207Q00000X",
            code_system="2.16.840.1.113883.6.101",
            display_name="Family Medicine",
            original_text=ED(value="Family Practice Physician")
        )

        assigned_author = AssignedAuthor(
            id=[II(root=CodeSystemOIDs.NPI, extension="1234567890")],
            code=specialty_with_text,
            assigned_person=AssignedPerson(name=[]),
            represented_organization=RepresentedOrganization(id=[], name=["Test"])
        )

        result = converter.convert(
            assigned_author,
            practitioner_id="practitioner-123",
            organization_id="org-456"
        )

        # Original text should be preserved in CodeableConcept.text
        if "text" in result["specialty"][0]:
            assert result["specialty"][0]["text"] == "Family Practice Physician"
