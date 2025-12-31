"""Unit tests for AuthorExtractor.

Test-Driven Development (TDD) - Tests written before implementation.
These tests define the behavior of the AuthorExtractor class and AuthorInfo container.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
    RepresentedOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import CE, II, TS
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.procedure import Procedure
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.converters.author_extractor import AuthorExtractor, AuthorInfo

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def author_extractor() -> AuthorExtractor:
    """Create an AuthorExtractor instance for testing."""
    return AuthorExtractor()


@pytest.fixture
def sample_practitioner_author() -> Author:
    """Create a sample Author with practitioner."""
    return Author(
        time=TS(value="20240115090000"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(code="207Q00000X", display_name="Family Medicine"),
            assigned_person=AssignedPerson(name=[]),
            represented_organization=RepresentedOrganization(
                id=[II(root="2.16.840.1.113883.19.5", extension="ORG-001")]
            ),
        ),
    )


@pytest.fixture
def sample_device_author() -> Author:
    """Create a sample Author with device."""
    return Author(
        time=TS(value="20240115143000"),
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.19.5", extension="DEVICE-001")],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="Epic EHR", software_name="Epic 2020"
            ),
        ),
    )


@pytest.fixture
def sample_observation_with_author(sample_practitioner_author: Author) -> Observation:
    """Create an Observation with an author."""
    observation = Observation()
    observation.author = [sample_practitioner_author]
    return observation


@pytest.fixture
def sample_concern_act_with_author(sample_practitioner_author: Author) -> Act:
    """Create an Act (concern act) with an author."""
    act = Act()
    act.author = [sample_practitioner_author]
    return act


# ============================================================================
# A. Extract from Observation (3 tests)
# ============================================================================


class TestExtractFromObservation:
    """Test extracting authors from Observation elements."""

    def test_extract_from_observation_single_author(
        self,
        author_extractor: AuthorExtractor,
        sample_observation_with_author: Observation,
    ) -> None:
        """Test extracting a single author from an observation."""
        authors = author_extractor.extract_from_observation(
            sample_observation_with_author
        )

        assert authors is not None
        assert len(authors) == 1
        assert isinstance(authors[0], AuthorInfo)
        assert authors[0].time == "20240115090000"
        assert authors[0].practitioner_id is not None
        assert authors[0].organization_id is not None

    def test_extract_from_observation_multiple_authors(
        self,
        author_extractor: AuthorExtractor,
        sample_practitioner_author: Author,
        sample_device_author: Author,
    ) -> None:
        """Test extracting multiple authors from an observation."""
        observation = Observation()
        observation.author = [sample_practitioner_author, sample_device_author]

        authors = author_extractor.extract_from_observation(observation)

        assert len(authors) == 2
        assert authors[0].practitioner_id is not None
        assert authors[1].device_id is not None

    def test_extract_from_observation_no_author(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test extracting from observation with no author."""
        observation = Observation()
        observation.author = None

        authors = author_extractor.extract_from_observation(observation)

        assert authors == []


# ============================================================================
# B. Extract from Concern Act (3 tests)
# ============================================================================


class TestExtractFromConcernAct:
    """Test extracting authors from Concern Act (Act) elements."""

    def test_extract_from_concern_act_with_practitioner(
        self,
        author_extractor: AuthorExtractor,
        sample_concern_act_with_author: Act,
    ) -> None:
        """Test extracting practitioner author from concern act."""
        import uuid as uuid_module

        authors = author_extractor.extract_from_concern_act(sample_concern_act_with_author)

        assert len(authors) == 1
        assert authors[0].practitioner_id is not None
        # Validate UUID v4 format
        try:
            uuid_module.UUID(authors[0].practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {authors[0].practitioner_id} is not a valid UUID v4")

    def test_extract_from_concern_act_with_device(
        self, author_extractor: AuthorExtractor, sample_device_author: Author
    ) -> None:
        """Test extracting device author from concern act."""
        import uuid as uuid_module

        act = Act()
        act.author = [sample_device_author]

        authors = author_extractor.extract_from_concern_act(act)

        assert len(authors) == 1
        assert authors[0].device_id is not None
        # Validate UUID v4 format
        try:
            uuid_module.UUID(authors[0].device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {authors[0].device_id} is not a valid UUID v4")
        assert authors[0].practitioner_id is None

    def test_extract_from_concern_act_no_author(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test extracting from concern act with no author."""
        act = Act()
        act.author = None

        authors = author_extractor.extract_from_concern_act(act)

        assert authors == []


# ============================================================================
# C. Extract Combined (with deduplication) (2 tests)
# ============================================================================


class TestExtractCombined:
    """Test extracting and deduplicating authors from both concern act and entry element."""

    def test_extract_combined_deduplicates_by_practitioner_and_org(
        self,
        author_extractor: AuthorExtractor,
        sample_practitioner_author: Author,
    ) -> None:
        """Test that duplicate authors (same practitioner and org) are deduplicated."""
        # Create concern act and observation with same author
        concern_act = Act()
        concern_act.author = [sample_practitioner_author]

        observation = Observation()
        observation.author = [sample_practitioner_author]

        authors = author_extractor.extract_combined(concern_act, observation)

        # Should only return one author (deduplicated)
        assert len(authors) == 1
        assert authors[0].practitioner_id is not None

    def test_extract_combined_preserves_different_authors(
        self,
        author_extractor: AuthorExtractor,
        sample_practitioner_author: Author,
        sample_device_author: Author,
    ) -> None:
        """Test that different authors are preserved."""
        concern_act = Act()
        concern_act.author = [sample_practitioner_author]

        observation = Observation()
        observation.author = [sample_device_author]

        authors = author_extractor.extract_combined(concern_act, observation)

        # Should return both authors (not duplicates)
        assert len(authors) == 2


# ============================================================================
# D. ID Generation (3 tests)
# ============================================================================


class TestIDGeneration:
    """Test FHIR ID generation from C-CDA identifiers."""

    def test_extract_practitioner_id_generation(
        self, author_extractor: AuthorExtractor, sample_practitioner_author: Author
    ) -> None:
        """Test that practitioner IDs are generated from assignedAuthor.id as UUID v4."""
        import uuid as uuid_module

        observation = Observation()
        observation.author = [sample_practitioner_author]

        authors = author_extractor.extract_from_observation(observation)

        assert authors[0].practitioner_id is not None
        # Validate UUID v4 format
        try:
            uuid_module.UUID(authors[0].practitioner_id, version=4)
        except ValueError:
            pytest.fail(f"ID {authors[0].practitioner_id} is not a valid UUID v4")

    def test_extract_device_id_generation(
        self, author_extractor: AuthorExtractor, sample_device_author: Author
    ) -> None:
        """Test that device IDs are generated from assignedAuthor.id as UUID v4."""
        import uuid as uuid_module

        observation = Observation()
        observation.author = [sample_device_author]

        authors = author_extractor.extract_from_observation(observation)

        assert authors[0].device_id is not None
        # Validate UUID v4 format
        try:
            uuid_module.UUID(authors[0].device_id, version=4)
        except ValueError:
            pytest.fail(f"ID {authors[0].device_id} is not a valid UUID v4")

    def test_extract_organization_id_from_represented_org(
        self, author_extractor: AuthorExtractor, sample_practitioner_author: Author
    ) -> None:
        """Test that organization IDs are extracted from representedOrganization as UUID v4."""
        import uuid as uuid_module

        observation = Observation()
        observation.author = [sample_practitioner_author]

        authors = author_extractor.extract_from_observation(observation)

        assert authors[0].organization_id is not None
        # Validate UUID v4 format
        try:
            uuid_module.UUID(authors[0].organization_id, version=4)
        except ValueError:
            pytest.fail(f"ID {authors[0].organization_id} is not a valid UUID v4")


# ============================================================================
# E. Role Code Extraction (2 tests)
# ============================================================================


class TestRoleCodeExtraction:
    """Test extracting role/function codes from authors."""

    def test_extract_role_code_from_function_code(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test extracting role code from author.functionCode."""
        author = Author(
            time=TS(value="20240115090000"),
            function_code=CE(code="PRF", display_name="Performer"),
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        observation = Observation()
        observation.author = [author]

        authors = author_extractor.extract_from_observation(observation)

        assert authors[0].role_code == "PRF"

    def test_function_code_precedence_over_assigned_code(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test that functionCode takes precedence over assignedAuthor.code."""
        author = Author(
            time=TS(value="20240115090000"),
            function_code=CE(code="PRF", display_name="Performer"),
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                code=CE(code="207Q00000X", display_name="Family Medicine"),
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        observation = Observation()
        observation.author = [author]

        authors = author_extractor.extract_from_observation(observation)

        # Should use functionCode (PRF), not assignedAuthor.code
        assert authors[0].role_code == "PRF"


# ============================================================================
# F. Extract from Other Element Types (2 tests)
# ============================================================================


class TestExtractFromOtherTypes:
    """Test extracting authors from SubstanceAdministration and Procedure."""

    def test_extract_from_substance_administration(
        self, author_extractor: AuthorExtractor, sample_practitioner_author: Author
    ) -> None:
        """Test extracting authors from SubstanceAdministration."""
        sa = SubstanceAdministration()
        sa.author = [sample_practitioner_author]

        authors = author_extractor.extract_from_substance_administration(sa)

        assert len(authors) == 1
        assert authors[0].practitioner_id is not None

    def test_extract_from_procedure(
        self, author_extractor: AuthorExtractor, sample_practitioner_author: Author
    ) -> None:
        """Test extracting authors from Procedure."""
        procedure = Procedure()
        procedure.author = [sample_practitioner_author]

        authors = author_extractor.extract_from_procedure(procedure)

        assert len(authors) == 1
        assert authors[0].practitioner_id is not None


# ============================================================================
# G. Edge Cases (2 tests)
# ============================================================================


class TestEdgeCases:
    """Test edge cases in author extraction."""

    def test_handles_missing_author_gracefully(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test handling of None author list."""
        observation = Observation()
        observation.author = None

        # Should not raise exception
        authors = author_extractor.extract_from_observation(observation)

        assert authors == []

    def test_author_without_time_uses_none(
        self, author_extractor: AuthorExtractor
    ) -> None:
        """Test that author without time has None as time value."""
        author = Author(
            time=None,  # No time
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(name=[]),
            ),
        )

        observation = Observation()
        observation.author = [author]

        authors = author_extractor.extract_from_observation(observation)

        assert authors[0].time is None
