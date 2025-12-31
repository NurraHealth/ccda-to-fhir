"""Root conftest.py for all tests.

This module provides fixtures and hooks that apply to all tests (unit and integration).
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def verify_fhir_r4b_compliance():
    """Auto-use fixture that verifies FHIR R4B compliance before any tests run.

    This fixture validates that all FHIR resources are using the R4B version (4.3.0)
    and not the R5 version (5.0.0). It runs once at the start of the test session.
    """
    # Import FHIR version from R4B
    from fhir.resources.R4B import __fhir_version__

    # Verify we're using R4B (4.3.0), not R5 (5.0.0)
    assert __fhir_version__ == "4.3.0", \
        f"Expected FHIR R4B version 4.3.0, got {__fhir_version__}. " \
        f"Check that all imports in ccda_to_fhir/fhir/models/__init__.py use R4B."

    # Import some representative resources to verify they're from R4B
    from ccda_to_fhir.fhir.models import (
        AllergyIntolerance,
        Condition,
        Device,
        MedicationRequest,
        Organization,
        Patient,
        Practitioner,
        Procedure,
        Provenance,
    )

    # Check that resources are from R4B module
    resources_to_verify = [
        (Condition, "Condition"),
        (AllergyIntolerance, "AllergyIntolerance"),
        (MedicationRequest, "MedicationRequest"),
        (Procedure, "Procedure"),
        (Patient, "Patient"),
        (Practitioner, "Practitioner"),
        (Organization, "Organization"),
        (Device, "Device"),
        (Provenance, "Provenance"),
    ]

    for resource_class, resource_name in resources_to_verify:
        module_path = resource_class.__module__
        assert "R4B" in module_path, \
            f"{resource_name} is not from R4B package. " \
            f"Module: {module_path}. Update imports in ccda_to_fhir/fhir/models/__init__.py"

    # Verify that recorder/requester fields exist in R4B (these are critical for our implementation)
    from fhir.resources.R4B.allergyintolerance import AllergyIntolerance as R4BAllergyIntolerance
    from fhir.resources.R4B.condition import Condition as R4BCondition
    from fhir.resources.R4B.medicationrequest import MedicationRequest as R4BMedicationRequest
    from fhir.resources.R4B.procedure import Procedure as R4BProcedure

    assert 'recorder' in R4BCondition.model_fields, \
        "Condition.recorder must exist in FHIR R4B"
    assert 'recorder' in R4BAllergyIntolerance.model_fields, \
        "AllergyIntolerance.recorder must exist in FHIR R4B"
    assert 'requester' in R4BMedicationRequest.model_fields, \
        "MedicationRequest.requester must exist in FHIR R4B"
    assert 'recorder' in R4BProcedure.model_fields, \
        "Procedure.recorder must exist in FHIR R4B"

    # Fixture doesn't need to return anything - just validates at session start
    yield
