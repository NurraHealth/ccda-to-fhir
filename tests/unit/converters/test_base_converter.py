"""Unit tests for BaseConverter shared utilities."""

import pytest

from ccda_to_fhir.ccda.models.datatypes import CS
from ccda_to_fhir.constants import (
    OBSERVATION_STATUS_TO_FHIR,
    PROCEDURE_STATUS_TO_FHIR,
    ENCOUNTER_STATUS_TO_FHIR,
    FHIRCodes,
)
from ccda_to_fhir.converters.base import BaseConverter


class ConcreteConverter(BaseConverter):
    """Concrete implementation of BaseConverter for testing."""

    def convert(self, ccda_model):
        """Dummy implementation."""
        return {}


class TestMapStatusCode:
    """Tests for the map_status_code shared utility method."""

    @pytest.fixture
    def converter(self):
        """Create a concrete converter instance for testing."""
        return ConcreteConverter()

    def test_map_status_code_with_valid_code(self, converter):
        """Test mapping a valid status code."""
        status_code = CS(code="completed")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_with_none_returns_default(self, converter):
        """Test that None status code returns the default."""
        result = converter.map_status_code(
            None,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_with_empty_code_returns_default(self, converter):
        """Test that status code with empty/None code returns the default."""
        status_code = CS(code=None)
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_case_insensitive(self, converter):
        """Test that status code mapping is case-insensitive."""
        # Test uppercase
        status_code = CS(code="COMPLETED")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.UNKNOWN,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

        # Test mixed case
        status_code = CS(code="Completed")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.UNKNOWN,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_unknown_code_returns_default(self, converter):
        """Test that unknown status code returns the default."""
        status_code = CS(code="unknown_code")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_with_string_input(self, converter):
        """Test that string input is handled correctly."""
        result = converter.map_status_code(
            "completed",
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.UNKNOWN,
        )
        assert result == FHIRCodes.ObservationStatus.FINAL

    def test_map_status_code_procedure_mapping(self, converter):
        """Test status mapping with procedure status codes."""
        test_cases = [
            ("completed", FHIRCodes.ProcedureStatus.COMPLETED),
            ("active", FHIRCodes.ProcedureStatus.IN_PROGRESS),
            ("aborted", FHIRCodes.ProcedureStatus.STOPPED),
            ("cancelled", FHIRCodes.ProcedureStatus.NOT_DONE),
            ("held", FHIRCodes.ProcedureStatus.ON_HOLD),
        ]
        for ccda_code, expected_fhir in test_cases:
            status_code = CS(code=ccda_code)
            result = converter.map_status_code(
                status_code,
                PROCEDURE_STATUS_TO_FHIR,
                FHIRCodes.ProcedureStatus.UNKNOWN,
            )
            assert result == expected_fhir, f"Failed for {ccda_code}"

    def test_map_status_code_encounter_mapping(self, converter):
        """Test status mapping with encounter status codes."""
        test_cases = [
            ("completed", FHIRCodes.EncounterStatus.FINISHED),
            ("active", FHIRCodes.EncounterStatus.IN_PROGRESS),
            ("aborted", FHIRCodes.EncounterStatus.CANCELLED),
        ]
        for ccda_code, expected_fhir in test_cases:
            status_code = CS(code=ccda_code)
            result = converter.map_status_code(
                status_code,
                ENCOUNTER_STATUS_TO_FHIR,
                FHIRCodes.EncounterStatus.UNKNOWN,
            )
            assert result == expected_fhir, f"Failed for {ccda_code}"

    def test_map_status_code_aborted_observation(self, converter):
        """Test that aborted maps to cancelled for observations."""
        status_code = CS(code="aborted")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.CANCELLED

    def test_map_status_code_active_observation(self, converter):
        """Test that active maps to registered for observations."""
        status_code = CS(code="active")
        result = converter.map_status_code(
            status_code,
            OBSERVATION_STATUS_TO_FHIR,
            FHIRCodes.ObservationStatus.FINAL,
        )
        assert result == FHIRCodes.ObservationStatus.REGISTERED
