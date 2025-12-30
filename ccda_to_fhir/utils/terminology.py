"""Terminology display name mappings for FHIR CodeableConcept.

This module provides display text for coded values when C-CDA doesn't include
display names, ensuring FHIR output has human-readable text per FHIR R4 spec.

Standard Reference: https://hl7.org/fhir/R4/datatypes.html#CodeableConcept
"display is a label for the code for use when displaying code-concept to a user"
"""

from typing import Optional

from ccda_to_fhir.constants import FHIRSystems

# AllergyIntolerance Clinical Status
# System: http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical
ALLERGY_CLINICAL_STATUS: dict[str, str] = {
    "active": "Active",
    "inactive": "Inactive",
    "resolved": "Resolved",
}

# AllergyIntolerance Verification Status
# System: http://terminology.hl7.org/CodeSystem/allergyintolerance-verification
ALLERGY_VERIFICATION_STATUS: dict[str, str] = {
    "confirmed": "Confirmed",
    "unconfirmed": "Unconfirmed",
    "presumed": "Presumed",
    "refuted": "Refuted",
    "entered-in-error": "Entered in Error",
}

# AllergyIntolerance Type
ALLERGY_TYPE: dict[str, str] = {
    "allergy": "Allergy",
    "intolerance": "Intolerance",
}

# AllergyIntolerance Category
ALLERGY_CATEGORY: dict[str, str] = {
    "food": "Food",
    "medication": "Medication",
    "environment": "Environment",
    "biologic": "Biologic",
}

# AllergyIntolerance Criticality
ALLERGY_CRITICALITY: dict[str, str] = {
    "low": "Low Risk",
    "high": "High Risk",
    "unable-to-assess": "Unable to Assess Risk",
}

# AllergyIntolerance Reaction Severity
REACTION_SEVERITY: dict[str, str] = {
    "mild": "Mild",
    "moderate": "Moderate",
    "severe": "Severe",
}

# Condition Clinical Status
# System: http://terminology.hl7.org/CodeSystem/condition-clinical
CONDITION_CLINICAL_STATUS: dict[str, str] = {
    "active": "Active",
    "recurrence": "Recurrence",
    "relapse": "Relapse",
    "inactive": "Inactive",
    "remission": "Remission",
    "resolved": "Resolved",
    "unknown": "Unknown",
}

# Condition Verification Status
# System: http://terminology.hl7.org/CodeSystem/condition-ver-status
CONDITION_VERIFICATION_STATUS: dict[str, str] = {
    "unconfirmed": "Unconfirmed",
    "provisional": "Provisional",
    "differential": "Differential",
    "confirmed": "Confirmed",
    "refuted": "Refuted",
    "entered-in-error": "Entered in Error",
}

# Condition Category
# System: http://terminology.hl7.org/CodeSystem/condition-category
CONDITION_CATEGORY: dict[str, str] = {
    "problem-list-item": "Problem List Item",
    "encounter-diagnosis": "Encounter Diagnosis",
}

# Observation Category
# System: http://terminology.hl7.org/CodeSystem/observation-category
OBSERVATION_CATEGORY: dict[str, str] = {
    "social-history": "Social History",
    "vital-signs": "Vital Signs",
    "imaging": "Imaging",
    "laboratory": "Laboratory",
    "procedure": "Procedure",
    "survey": "Survey",
    "exam": "Exam",
    "therapy": "Therapy",
    "activity": "Activity",
}

# Observation Status
# System: http://hl7.org/fhir/observation-status
OBSERVATION_STATUS: dict[str, str] = {
    "registered": "Registered",
    "preliminary": "Preliminary",
    "final": "Final",
    "amended": "Amended",
    "corrected": "Corrected",
    "cancelled": "Cancelled",
    "entered-in-error": "Entered in Error",
    "unknown": "Unknown",
}

# Observation Interpretation
# System: http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation
OBSERVATION_INTERPRETATION: dict[str, str] = {
    "N": "Normal",
    "L": "Low",
    "H": "High",
    "LL": "Critical low",
    "HH": "Critical high",
    "A": "Abnormal",
    "AA": "Critical abnormal",
    "<": "Off scale low",
    ">": "Off scale high",
    "AC": "Anti-complementary substances present",
    "B": "Better",
    "D": "Significant change down",
    "DET": "Detected",
    "I": "Intermediate",
    "IND": "Indeterminate",
    "MS": "Moderately susceptible",
    "ND": "Not detected",
    "NEG": "Negative",
    "NR": "Non-reactive",
    "NS": "Non-susceptible",
    "POS": "Positive",
    "R": "Resistant",
    "RR": "Reactive",
    "S": "Susceptible",
    "U": "Significant change up",
    "VS": "Very susceptible",
    "W": "Worse",
    "WR": "Weakly reactive",
}

# Immunization Status
# System: http://hl7.org/fhir/event-status
IMMUNIZATION_STATUS: dict[str, str] = {
    "completed": "Completed",
    "entered-in-error": "Entered in Error",
    "not-done": "Not Done",
}

# Immunization Status Reason (for not-done)
# System: http://terminology.hl7.org/CodeSystem/v3-ActReason
IMMUNIZATION_STATUS_REASON: dict[str, str] = {
    "IMMUNE": "Immunity",
    "MEDPREC": "Medical Precaution",
    "OSTOCK": "Product Out Of Stock",
    "PATOBJ": "Patient Objection",
    "PHILISOP": "Philosophical Objection",
    "RELIG": "Religious Objection",
    "VACEFF": "Vaccine Efficacy Concerns",
    "VACSAF": "Vaccine Safety Concerns",
}

# MedicationStatement Status
# System: http://hl7.org/fhir/CodeSystem/medication-statement-status
MEDICATION_STATEMENT_STATUS: dict[str, str] = {
    "active": "Active",
    "completed": "Completed",
    "entered-in-error": "Entered in Error",
    "intended": "Intended",
    "stopped": "Stopped",
    "on-hold": "On Hold",
    "unknown": "Unknown",
    "not-taken": "Not Taken",
}

# MedicationRequest Intent
# System: http://hl7.org/fhir/CodeSystem/medicationrequest-intent
MEDICATION_REQUEST_INTENT: dict[str, str] = {
    "proposal": "Proposal",
    "plan": "Plan",
    "order": "Order",
    "original-order": "Original Order",
    "reflex-order": "Reflex Order",
    "filler-order": "Filler Order",
    "instance-order": "Instance Order",
    "option": "Option",
}

# Procedure Status
# System: http://hl7.org/fhir/event-status
PROCEDURE_STATUS: dict[str, str] = {
    "preparation": "Preparation",
    "in-progress": "In Progress",
    "not-done": "Not Done",
    "on-hold": "On Hold",
    "stopped": "Stopped",
    "completed": "Completed",
    "entered-in-error": "Entered in Error",
    "unknown": "Unknown",
}

# Goal Lifecycle Status
# System: http://hl7.org/fhir/goal-status
GOAL_LIFECYCLE_STATUS: dict[str, str] = {
    "proposed": "Proposed",
    "planned": "Planned",
    "accepted": "Accepted",
    "active": "Active",
    "on-hold": "On Hold",
    "completed": "Completed",
    "cancelled": "Cancelled",
    "entered-in-error": "Entered in Error",
    "rejected": "Rejected",
}

# DiagnosticReport Status
# System: http://hl7.org/fhir/diagnostic-report-status
DIAGNOSTIC_REPORT_STATUS: dict[str, str] = {
    "registered": "Registered",
    "partial": "Partial",
    "preliminary": "Preliminary",
    "final": "Final",
    "amended": "Amended",
    "corrected": "Corrected",
    "appended": "Appended",
    "cancelled": "Cancelled",
    "entered-in-error": "Entered in Error",
    "unknown": "Unknown",
}

# Device Status
# System: http://hl7.org/fhir/device-status
DEVICE_STATUS: dict[str, str] = {
    "active": "Active",
    "inactive": "Inactive",
    "entered-in-error": "Entered in Error",
    "unknown": "Unknown",
}


# Master lookup dictionary mapping system URIs to their display maps
DISPLAY_MAPS: dict[str, dict[str, str]] = {
    FHIRSystems.ALLERGY_CLINICAL: ALLERGY_CLINICAL_STATUS,
    FHIRSystems.ALLERGY_VERIFICATION: ALLERGY_VERIFICATION_STATUS,
    FHIRSystems.CONDITION_CLINICAL: CONDITION_CLINICAL_STATUS,
    FHIRSystems.CONDITION_VERIFICATION: CONDITION_VERIFICATION_STATUS,
    FHIRSystems.CONDITION_CATEGORY: CONDITION_CATEGORY,
    FHIRSystems.OBSERVATION_CATEGORY: OBSERVATION_CATEGORY,
    "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation": OBSERVATION_INTERPRETATION,
    "http://hl7.org/fhir/observation-status": OBSERVATION_STATUS,
    "http://hl7.org/fhir/event-status": IMMUNIZATION_STATUS,  # Also used for Procedure
    "http://terminology.hl7.org/CodeSystem/v3-ActReason": IMMUNIZATION_STATUS_REASON,
    "http://hl7.org/fhir/CodeSystem/medication-statement-status": MEDICATION_STATEMENT_STATUS,
    "http://hl7.org/fhir/CodeSystem/medicationrequest-intent": MEDICATION_REQUEST_INTENT,
    "http://hl7.org/fhir/goal-status": GOAL_LIFECYCLE_STATUS,
    "http://hl7.org/fhir/diagnostic-report-status": DIAGNOSTIC_REPORT_STATUS,
    "http://hl7.org/fhir/device-status": DEVICE_STATUS,
}


def get_display_for_code(system: str, code: str) -> Optional[str]:
    """Get display text for a code in a given system.

    Args:
        system: FHIR system URI (e.g., "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical")
        code: Code value (e.g., "active")

    Returns:
        Display text (e.g., "Active") or None if not found

    Example:
        >>> get_display_for_code(FHIRSystems.ALLERGY_CLINICAL, "active")
        "Active"
    """
    if system in DISPLAY_MAPS:
        return DISPLAY_MAPS[system].get(code)
    return None


def get_display_for_allergy_clinical_status(code: str) -> Optional[str]:
    """Get display for AllergyIntolerance.clinicalStatus code.

    Args:
        code: Clinical status code ("active", "inactive", "resolved")

    Returns:
        Display text or None
    """
    return ALLERGY_CLINICAL_STATUS.get(code)


def get_display_for_condition_clinical_status(code: str) -> Optional[str]:
    """Get display for Condition.clinicalStatus code.

    Args:
        code: Clinical status code

    Returns:
        Display text or None
    """
    return CONDITION_CLINICAL_STATUS.get(code)


def get_display_for_observation_interpretation(code: str) -> Optional[str]:
    """Get display for Observation.interpretation code.

    Args:
        code: Interpretation code ("N", "L", "H", "A", etc.)

    Returns:
        Display text or None
    """
    return OBSERVATION_INTERPRETATION.get(code)
