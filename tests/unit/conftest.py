"""Shared fixtures for unit tests."""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_reference_registry():
    """Create a mock reference registry for unit tests.

    Provides basic patient reference functionality that most converters need.
    Tests can customize the mock if they need specific behavior.
    """
    registry = MagicMock()

    # Default patient reference
    registry.get_patient_reference.return_value = {
        "reference": "urn:uuid:12345678-1234-5678-1234-567812345678"
    }

    # Default encounter reference
    registry.get_encounter_reference.return_value = {
        "reference": "urn:uuid:87654321-4321-8765-4321-876543218765"
    }

    # Make register_resource a no-op
    registry.register_resource.return_value = None

    return registry
