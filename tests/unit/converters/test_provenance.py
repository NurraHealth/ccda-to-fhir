"""Unit tests for ProvenanceConverter.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the behavior of the ProvenanceConverter class.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from ccda_to_fhir.converters.author_extractor import AuthorInfo
from ccda_to_fhir.converters.provenance import ProvenanceConverter
from ccda_to_fhir.types import FHIRResourceDict

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def provenance_converter() -> ProvenanceConverter:
    """Create a ProvenanceConverter instance for testing."""
    return ProvenanceConverter()


@pytest.fixture
def sample_target_condition() -> FHIRResourceDict:
    """Create a sample target Condition resource."""
    return {
        "resourceType": "Condition",
        "id": "condition-123",
        "code": {
            "coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]
        },
    }


@pytest.fixture
def sample_practitioner_author_info() -> AuthorInfo:
    """Create a sample AuthorInfo for a practitioner."""
    from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
    from ccda_to_fhir.ccda.models.datatypes import CE, II, TS

    author = Author(
        time=TS(value="20240115090000"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="207Q00000X"),
            assigned_person=AssignedPerson(name=[]),
        ),
    )
    return AuthorInfo(author)


@pytest.fixture
def sample_device_author_info() -> AuthorInfo:
    """Create a sample AuthorInfo for a device."""
    from ccda_to_fhir.ccda.models.author import (
        AssignedAuthor,
        AssignedAuthoringDevice,
        Author,
    )
    from ccda_to_fhir.ccda.models.datatypes import II, TS

    author = Author(
        time=TS(value="20240115143000"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="Epic EHR"
            ),
        ),
    )
    return AuthorInfo(author)


@pytest.fixture
def sample_author_with_org() -> AuthorInfo:
    """Create a sample AuthorInfo with organization."""
    from ccda_to_fhir.ccda.models.author import (
        AssignedAuthor,
        AssignedPerson,
        Author,
        RepresentedOrganization,
    )
    from ccda_to_fhir.ccda.models.datatypes import II, TS

    author = Author(
        time=TS(value="20240115090000"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            assigned_person=AssignedPerson(name=[]),
            represented_organization=RepresentedOrganization(
                id=[II(root="2.16.840.1.113883.19.5", extension="ORG-001")]
            ),
        ),
    )
    return AuthorInfo(author)


# ============================================================================
# A. Basic Resource Creation (3 tests)
# ============================================================================


class TestBasicResourceCreation:
    """Test basic Provenance resource creation."""

    def test_convert_creates_provenance_resource(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that converter creates a Provenance resource."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert provenance is not None
        assert provenance["resourceType"] == "Provenance"

    def test_provenance_resource_type_is_provenance(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that resourceType is exactly 'Provenance'."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert provenance["resourceType"] == "Provenance"

    def test_provenance_id_format(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that Provenance ID is generated using centralized id_generator."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert "id" in provenance
        # ID should be a valid UUID (36 chars with hyphens) generated by id_generator
        provenance_id = provenance["id"]
        assert len(provenance_id) == 36, f"Expected UUID format, got: {provenance_id}"
        assert provenance_id.count("-") == 4, f"Expected UUID format, got: {provenance_id}"
        # Should be <= 64 chars (FHIR requirement)
        assert len(provenance_id) <= 64, f"ID exceeds 64-char limit: {provenance_id}"


# ============================================================================
# B. Target Reference (2 tests)
# ============================================================================


class TestTargetReference:
    """Test Provenance target reference creation."""

    def test_provenance_has_target_reference(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that Provenance has a target array with reference."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert "target" in provenance
        assert isinstance(provenance["target"], list)
        assert len(provenance["target"]) == 1
        assert "reference" in provenance["target"][0]

    def test_target_reference_format_resource_type_slash_id(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that target reference follows format: ResourceType/id."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert provenance["target"][0]["reference"] == "Condition/condition-123"


# ============================================================================
# C. Recorded Date (3 tests)
# ============================================================================


class TestRecordedDate:
    """Test Provenance recorded date extraction."""

    def test_provenance_has_recorded_date_from_earliest_author(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that recorded date comes from earliest author time."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import II, TS

        # Create two authors with different times
        author1 = Author(
            time=TS(value="20240115143000"),  # Later
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="111")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )
        author2 = Author(
            time=TS(value="20240115090000"),  # Earlier
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="222")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        authors = [AuthorInfo(author1), AuthorInfo(author2)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        assert "recorded" in provenance
        # Should use earliest time (author2), reduced to date-only per FHIR R4 requirement (no timezone in source)
        assert provenance["recorded"] == "2024-01-15"

    def test_handles_author_without_time(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test handling of author without time."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import II

        author = Author(
            time=None,  # No time
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        authors = [AuthorInfo(author)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        # Should still have a recorded date (current timestamp fallback)
        assert "recorded" in provenance

    def test_recorded_date_fallback_to_current_timestamp(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that recorded date falls back to current timestamp when no author times."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import II

        author = Author(
            time=None,
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        authors = [AuthorInfo(author)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        # Should have current date
        recorded = provenance["recorded"]
        current_year = datetime.now().year
        assert str(current_year) in recorded


# ============================================================================
# D. Agent Creation (5 tests)
# ============================================================================


class TestAgentCreation:
    """Test Provenance agent creation from authors."""

    def test_provenance_has_agents_array(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that Provenance has an agent array."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        assert "agent" in provenance
        assert isinstance(provenance["agent"], list)
        assert len(provenance["agent"]) == 1

    def test_agent_has_practitioner_who_reference(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that agent has 'who' reference to Practitioner."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        agent = provenance["agent"][0]
        assert "who" in agent
        assert "reference" in agent["who"]
        assert agent["who"]["reference"].startswith("Practitioner/")

    def test_device_author_references_device_not_practitioner(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_device_author_info: AuthorInfo,
    ) -> None:
        """Test that device author creates Device reference, not Practitioner."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_device_author_info],
        )

        agent = provenance["agent"][0]
        assert agent["who"]["reference"].startswith("Device/")

    def test_agent_has_organization_on_behalf_of(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_author_with_org: AuthorInfo,
    ) -> None:
        """Test that agent has 'onBehalfOf' reference to Organization."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_author_with_org],
        )

        agent = provenance["agent"][0]
        assert "onBehalfOf" in agent
        assert "reference" in agent["onBehalfOf"]
        assert agent["onBehalfOf"]["reference"].startswith("Organization/")

    def test_multiple_authors_create_multiple_agents(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
        sample_device_author_info: AuthorInfo,
    ) -> None:
        """Test that multiple authors create multiple agents."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info, sample_device_author_info],
        )

        assert len(provenance["agent"]) == 2


# ============================================================================
# E. Agent Type Mapping (3 tests)
# ============================================================================


class TestAgentTypeMapping:
    """Test mapping of C-CDA roles to Provenance agent types."""

    def test_agent_type_author_for_default(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that default agent type is 'author'."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        agent = provenance["agent"][0]
        assert "type" in agent
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_agent_type_performer_for_performer_role(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that PRF role maps to 'performer' agent type."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import CE, II, TS

        author = Author(
            time=TS(value="20240115090000"),
            function_code=CE(code="PRF"),  # Performer
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        authors = [AuthorInfo(author)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        agent = provenance["agent"][0]
        assert agent["type"]["coding"][0]["code"] == "performer"

    def test_agent_type_mapping_all_roles(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that all C-CDA roles map to correct Provenance agent types."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import CE, II, TS

        role_mappings = {
            "AUT": "author",
            "PRF": "performer",
            "INF": "informant",
            "ENT": "enterer",
            "LA": "attester",
            "CST": "custodian",
        }

        for ccda_code, expected_agent_type in role_mappings.items():
            author = Author(
                time=TS(value="20240115090000"),
                function_code=CE(code=ccda_code),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                    assigned_person=AssignedPerson(name=[]),
                ),
            )

            authors = [AuthorInfo(author)]
            provenance = provenance_converter.convert(
                target_resource=sample_target_condition, authors=authors
            )

            agent = provenance["agent"][0]
            assert agent["type"]["coding"][0]["code"] == expected_agent_type


# ============================================================================
# F. Edge Cases (4 tests)
# ============================================================================


class TestEdgeCases:
    """Test edge cases in Provenance conversion."""

    def test_handles_author_without_organization(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
        sample_practitioner_author_info: AuthorInfo,
    ) -> None:
        """Test that agent without organization doesn't have onBehalfOf field."""
        # sample_practitioner_author_info has no organization
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition,
            authors=[sample_practitioner_author_info],
        )

        agent = provenance["agent"][0]
        # Should not have onBehalfOf (optional field)
        assert "onBehalfOf" not in agent or agent.get("onBehalfOf") is None

    def test_agent_without_organization_omits_on_behalf_of(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that onBehalfOf is omitted when no organization."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import II, TS

        author = Author(
            time=TS(value="20240115090000"),
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                assigned_person=AssignedPerson(name=[]),
                represented_organization=None,  # No org
            ),
        )

        authors = [AuthorInfo(author)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        agent = provenance["agent"][0]
        assert "onBehalfOf" not in agent

    def test_empty_authors_list_creates_no_agents(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that empty authors list creates Provenance with empty agent array."""
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=[]
        )

        assert "agent" in provenance
        assert provenance["agent"] == []

    def test_agent_type_defaults_to_author_for_unknown_role(
        self,
        provenance_converter: ProvenanceConverter,
        sample_target_condition: FHIRResourceDict,
    ) -> None:
        """Test that unknown role codes default to 'author' agent type."""
        from ccda_to_fhir.ccda.models.author import AssignedAuthor, AssignedPerson, Author
        from ccda_to_fhir.ccda.models.datatypes import CE, II, TS

        author = Author(
            time=TS(value="20240115090000"),
            function_code=CE(code="UNKNOWN_ROLE"),  # Unknown role
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="123")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        authors = [AuthorInfo(author)]
        provenance = provenance_converter.convert(
            target_resource=sample_target_condition, authors=authors
        )

        agent = provenance["agent"][0]
        # Should default to 'author'
        assert agent["type"]["coding"][0]["code"] == "author"
