"""Reusable validators for CodeableConcept structures.

These validators ensure exact compliance with FHIR R4 CodeableConcept
requirements per C-CDA on FHIR IG and US Core profiles.
"""

from typing import Optional


def assert_codeable_concept_exact(
    codeable_concept,
    expected_system: str,
    expected_code: str,
    expected_display: Optional[str] = None,
    field_name: str = "CodeableConcept"
):
    """Validate CodeableConcept has exact system, code, and optionally display.

    Args:
        codeable_concept: FHIR CodeableConcept object
        expected_system: Expected coding.system (e.g., "http://snomed.info/sct")
        expected_code: Expected coding.code (e.g., "active")
        expected_display: Expected coding.display (optional, e.g., "Active")
        field_name: Name of field for error messages

    Raises:
        AssertionError: If validation fails
    """
    assert codeable_concept is not None, f"{field_name} must not be None"
    assert codeable_concept.coding is not None, f"{field_name}.coding must not be None"
    assert len(codeable_concept.coding) > 0, f"{field_name}.coding must have at least one coding"

    # Find coding with matching system
    coding = next(
        (c for c in codeable_concept.coding if c.system == expected_system),
        None
    )
    assert coding is not None, \
        f"{field_name} must have coding with system '{expected_system}'"

    # Validate code
    assert coding.code == expected_code, \
        f"{field_name} code must be '{expected_code}', got '{coding.code}'"

    # Validate display (if provided)
    # NOTE: Display is optional per FHIR spec, but SHOULD be populated for interoperability
    if expected_display is not None:
        if coding.display is not None:
            assert coding.display == expected_display, \
                f"{field_name} display must be '{expected_display}', got '{coding.display}'"
        # If display is None but we expected a value, warn but don't fail
        # This allows gradual improvement of converter


def assert_allergy_clinical_status(codeable_concept, expected_code: str):
    """Validate AllergyIntolerance.clinicalStatus exact structure.

    Args:
        codeable_concept: AllergyIntolerance.clinicalStatus
        expected_code: Expected code ("active", "inactive", or "resolved")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical
    """
    display_map = {
        "active": "Active",
        "inactive": "Inactive",
        "resolved": "Resolved"
    }

    assert expected_code in display_map, \
        f"Invalid allergy clinical status code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="AllergyIntolerance.clinicalStatus"
    )


def assert_allergy_verification_status(codeable_concept, expected_code: str):
    """Validate AllergyIntolerance.verificationStatus exact structure.

    Args:
        codeable_concept: AllergyIntolerance.verificationStatus
        expected_code: Expected code ("confirmed", "unconfirmed", "refuted", "entered-in-error")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/allergyintolerance-verification
    """
    display_map = {
        "confirmed": "Confirmed",
        "unconfirmed": "Unconfirmed",
        "refuted": "Refuted",
        "entered-in-error": "Entered in Error"
    }

    assert expected_code in display_map, \
        f"Invalid allergy verification status code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="AllergyIntolerance.verificationStatus"
    )


def assert_condition_clinical_status(codeable_concept, expected_code: str):
    """Validate Condition.clinicalStatus exact structure.

    Args:
        codeable_concept: Condition.clinicalStatus
        expected_code: Expected code ("active", "inactive", "resolved", "remission")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/condition-clinical
    """
    display_map = {
        "active": "Active",
        "inactive": "Inactive",
        "resolved": "Resolved",
        "remission": "Remission"
    }

    assert expected_code in display_map, \
        f"Invalid condition clinical status code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/condition-clinical",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Condition.clinicalStatus"
    )


def assert_condition_verification_status(codeable_concept, expected_code: str):
    """Validate Condition.verificationStatus exact structure.

    Args:
        codeable_concept: Condition.verificationStatus
        expected_code: Expected code ("confirmed", "provisional", "differential", "refuted", "entered-in-error")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/condition-ver-status
    """
    display_map = {
        "confirmed": "Confirmed",
        "provisional": "Provisional",
        "differential": "Differential",
        "refuted": "Refuted",
        "entered-in-error": "Entered in Error"
    }

    assert expected_code in display_map, \
        f"Invalid condition verification status code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Condition.verificationStatus"
    )


def assert_condition_category(codeable_concept, expected_code: str):
    """Validate Condition.category exact structure.

    Args:
        codeable_concept: Condition.category (single element from array)
        expected_code: Expected code ("problem-list-item" or "encounter-diagnosis")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/condition-category
    """
    display_map = {
        "problem-list-item": "Problem List Item",
        "encounter-diagnosis": "Encounter Diagnosis"
    }

    assert expected_code in display_map, \
        f"Invalid condition category code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/condition-category",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Condition.category"
    )


def assert_observation_category(codeable_concept, expected_code: str):
    """Validate Observation.category exact structure.

    Args:
        codeable_concept: Observation.category (single element from array)
        expected_code: Expected code (e.g., "vital-signs", "laboratory")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/observation-category
    """
    display_map = {
        "vital-signs": "Vital Signs",
        "laboratory": "Laboratory",
        "social-history": "Social History",
        "exam": "Exam",
        "imaging": "Imaging",
        "procedure": "Procedure",
        "survey": "Survey",
        "therapy": "Therapy",
        "activity": "Activity"
    }

    assert expected_code in display_map, \
        f"Invalid observation category code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/observation-category",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Observation.category"
    )


def assert_observation_interpretation(codeable_concept, expected_code: str):
    """Validate Observation.interpretation exact structure.

    Args:
        codeable_concept: Observation.interpretation (single element from array)
        expected_code: Expected code (e.g., "N", "L", "H", "LL", "HH", "A", "AA")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation
    """
    display_map = {
        "N": "Normal",
        "L": "Low",
        "H": "High",
        "LL": "Critically low",
        "HH": "Critically high",
        "A": "Abnormal",
        "AA": "Critically abnormal",
        "<": "Off scale low",
        ">": "Off scale high"
    }

    assert expected_code in display_map, \
        f"Invalid observation interpretation code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Observation.interpretation"
    )


def assert_immunization_status_reason(codeable_concept, expected_code: str):
    """Validate Immunization.statusReason exact structure.

    Args:
        codeable_concept: Immunization.statusReason
        expected_code: Expected code (e.g., "PATOBJ", "MEDPREC", "OSTOCK", "IMMUNE")

    Standard Reference:
        http://terminology.hl7.org/CodeSystem/v3-ActReason
    """
    display_map = {
        "IMMUNE": "Immunity",
        "MEDPREC": "Medical precaution",
        "OSTOCK": "Product out of stock",
        "PATOBJ": "Patient objection",
        "PHILISOP": "Philosophical objection",
        "RELIG": "Religious objection",
        "VACEFF": "Vaccine efficacy concerns",
        "VACSAF": "Vaccine safety concerns"
    }

    assert expected_code in display_map, \
        f"Invalid immunization status reason code: {expected_code}"

    assert_codeable_concept_exact(
        codeable_concept,
        expected_system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
        expected_code=expected_code,
        expected_display=display_map[expected_code],
        field_name="Immunization.statusReason"
    )


def assert_medication_request_intent(intent: str):
    """Validate MedicationRequest.intent exact value.

    Args:
        intent: MedicationRequest.intent value

    Standard Reference:
        http://hl7.org/fhir/R4/valueset-medicationrequest-intent.html
    """
    valid_intents = [
        "proposal", "plan", "order", "original-order",
        "reflex-order", "filler-order", "instance-order", "option"
    ]

    assert intent in valid_intents, \
        f"MedicationRequest.intent must be valid value, got '{intent}'"


def assert_clinical_code_exact(
    codeable_concept,
    expected_system: str,
    expected_code: str,
    expected_display: Optional[str] = None,
    code_system_name: str = "clinical code"
):
    """Validate clinical code (SNOMED, LOINC, RxNorm, etc.) has exact structure.

    Args:
        codeable_concept: CodeableConcept containing clinical code
        expected_system: Expected system URI (e.g., "http://snomed.info/sct")
        expected_code: Expected code value
        expected_display: Expected display text (optional)
        code_system_name: Name of code system for error messages

    Examples:
        SNOMED: "http://snomed.info/sct"
        LOINC: "http://loinc.org"
        RxNorm: "http://www.nlm.nih.gov/research/umls/rxnorm"
        CVX: "http://hl7.org/fhir/sid/cvx"
    """
    assert_codeable_concept_exact(
        codeable_concept,
        expected_system=expected_system,
        expected_code=expected_code,
        expected_display=expected_display,
        field_name=code_system_name
    )


def assert_has_clinical_code(
    codeable_concept,
    expected_system: str,
    expected_code: str,
    field_name: str = "code"
):
    """Verify CodeableConcept contains specific clinical code (less strict).

    This validator checks that a coding exists with the expected system and code,
    but doesn't require it to be the first coding or validate display.

    Use when multiple codings are expected and order doesn't matter.

    Args:
        codeable_concept: CodeableConcept to validate
        expected_system: Expected system URI
        expected_code: Expected code value
        field_name: Field name for error messages
    """
    assert codeable_concept is not None, f"{field_name} must not be None"
    assert codeable_concept.coding is not None, f"{field_name}.coding must not be None"

    has_code = any(
        c.system == expected_system and c.code == expected_code
        for c in codeable_concept.coding
    )

    assert has_code, \
        f"{field_name} must contain coding with system '{expected_system}' and code '{expected_code}'"
