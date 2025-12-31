"""Registry of supported C-CDA templates.

This module defines all C-CDA templates that have official FHIR mappings
documented in docs/mapping/. Templates not in this registry should be
gracefully skipped during conversion.
"""

from __future__ import annotations

from ccda_to_fhir.constants import TemplateIds

# =============================================================================
# Supported C-CDA Templates
# =============================================================================
# Templates documented in docs/mapping/ that have official C-CDA → FHIR mappings


class SupportedTemplates:
    """Registry of C-CDA templates with official FHIR mappings.

    Each template listed here is documented in docs/mapping/ and has
    a defined conversion path to FHIR resources.
    """

    # Entry-level templates (primary conversion targets)
    ENTRY_TEMPLATES = {
        # Problems (02-condition.md)
        TemplateIds.PROBLEM_CONCERN_ACT: "Problem Concern Act",
        TemplateIds.PROBLEM_OBSERVATION: "Problem Observation",
        TemplateIds.PROBLEM_STATUS_OBSERVATION: "Problem Status Observation",
        "2.16.840.1.113883.10.20.22.4.502": "Date of Diagnosis Act",

        # Allergies (03-allergy-intolerance.md)
        TemplateIds.ALLERGY_CONCERN_ACT: "Allergy Concern Act",
        TemplateIds.ALLERGY_INTOLERANCE_OBSERVATION: "Allergy Intolerance Observation",
        TemplateIds.ALLERGY_STATUS_OBSERVATION: "Allergy Status Observation",
        TemplateIds.SEVERITY_OBSERVATION: "Severity Observation",
        TemplateIds.REACTION_OBSERVATION: "Reaction Observation",
        TemplateIds.CRITICALITY_OBSERVATION: "Criticality Observation",

        # Observations (04-observation.md, 11-social-history.md, 12-vital-signs.md)
        TemplateIds.RESULT_ORGANIZER: "Result Organizer",
        TemplateIds.RESULT_OBSERVATION: "Result Observation",
        TemplateIds.VITAL_SIGNS_ORGANIZER: "Vital Signs Organizer",
        TemplateIds.VITAL_SIGN_OBSERVATION: "Vital Sign Observation",
        TemplateIds.SMOKING_STATUS_OBSERVATION: "Smoking Status Observation",
        TemplateIds.SOCIAL_HISTORY_OBSERVATION: "Social History Observation",
        TemplateIds.PREGNANCY_OBSERVATION: "Pregnancy Observation",
        TemplateIds.ESTIMATED_DELIVERY_DATE_OBSERVATION: "Estimated Delivery Date Observation",
        TemplateIds.BIRTH_SEX_OBSERVATION: "Birth Sex Observation",
        TemplateIds.TRIBAL_AFFILIATION_OBSERVATION: "Tribal Affiliation Observation",
        TemplateIds.SEX_PARAMETER_FOR_CLINICAL_USE_OBSERVATION: "Sex Parameter for Clinical Use",

        # Procedures (05-procedure.md, 18-service-request.md)
        TemplateIds.PROCEDURE_ACTIVITY_PROCEDURE: "Procedure Activity Procedure",
        TemplateIds.PROCEDURE_ACTIVITY_ACT: "Procedure Activity Act",
        TemplateIds.PROCEDURE_ACTIVITY_OBSERVATION: "Procedure Activity Observation",
        TemplateIds.PLANNED_PROCEDURE: "Planned Procedure",
        TemplateIds.PLANNED_ACT: "Planned Act",

        # Immunizations (06-immunization.md)
        TemplateIds.IMMUNIZATION_ACTIVITY: "Immunization Activity",
        TemplateIds.IMMUNIZATION_MEDICATION_INFORMATION: "Immunization Medication Information",
        TemplateIds.IMMUNIZATION_REFUSAL_REASON: "Immunization Refusal Reason",

        # Medications (07-medication-request.md, 15-medication-dispense.md, 23-medication.md, 24-medication-statement.md)
        TemplateIds.MEDICATION_ACTIVITY: "Medication Activity",
        TemplateIds.MEDICATION_INFORMATION: "Medication Information",
        TemplateIds.INDICATION_OBSERVATION: "Indication Observation",
        TemplateIds.INSTRUCTION_ACT: "Instruction Act",
        TemplateIds.MEDICATION_SUPPLY_ORDER: "Medication Supply Order",
        TemplateIds.MEDICATION_DISPENSE: "Medication Dispense",

        # Encounters (08-encounter.md)
        TemplateIds.ENCOUNTER_ACTIVITY: "Encounter Activity",
        TemplateIds.ENCOUNTER_DIAGNOSIS: "Encounter Diagnosis",

        # Notes (10-notes.md, 26-document-reference.md)
        TemplateIds.NOTE_ACTIVITY: "Note Activity",

        # Goals (13-goal.md)
        TemplateIds.GOAL_OBSERVATION: "Goal Observation",
        TemplateIds.PRIORITY_PREFERENCE: "Priority Preference",
        TemplateIds.PROGRESS_TOWARD_GOAL: "Progress Toward Goal Observation",
        TemplateIds.ENTRY_REFERENCE: "Entry Reference",

        # Care Plans (14-careplan.md)
        TemplateIds.HEALTH_CONCERN_ACT: "Health Concern Act",
        TemplateIds.INTERVENTION_ACT: "Intervention Act",
        "2.16.840.1.113883.10.20.22.4.146": "Planned Intervention Act",

        # Care Teams (17-careteam.md)
        TemplateIds.CARE_TEAM_ORGANIZER: "Care Team Organizer",
        "2.16.840.1.113883.10.20.22.4.500.1": "Care Team Member Act",
        "2.16.840.1.113883.10.20.22.4.500.2": "Care Team Member Schedule Observation",

        # Devices (22-device.md)
        "2.16.840.1.113883.10.20.22.4.37": "Product Instance",

        # Supporting templates
        TemplateIds.AGE_OBSERVATION: "Age Observation",
        TemplateIds.COMMENT_ACTIVITY: "Comment Activity",
        TemplateIds.ASSESSMENT_SCALE_OBSERVATION: "Assessment Scale Observation",
        TemplateIds.AUTHOR_PARTICIPATION: "Author Participation",
    }

    # Section-level templates (organizational structure)
    SECTION_TEMPLATES = {
        TemplateIds.PROBLEM_SECTION: "Problems Section",
        TemplateIds.ALLERGY_SECTION: "Allergies Section",
        TemplateIds.MEDICATIONS_SECTION: "Medications Section",
        TemplateIds.IMMUNIZATIONS_SECTION: "Immunizations Section",
        TemplateIds.VITAL_SIGNS_SECTION: "Vital Signs Section",
        TemplateIds.RESULTS_SECTION: "Results Section",
        TemplateIds.SOCIAL_HISTORY_SECTION: "Social History Section",
        TemplateIds.PROCEDURES_SECTION: "Procedures Section",
        TemplateIds.PLAN_OF_TREATMENT_SECTION: "Plan of Treatment Section",
        TemplateIds.ENCOUNTERS_SECTION: "Encounters Section",
        TemplateIds.NOTES_SECTION: "Notes Section",
        TemplateIds.GOALS_SECTION: "Goals Section",
        TemplateIds.HEALTH_CONCERNS_SECTION: "Health Concerns Section",
        "2.16.840.1.113883.10.20.21.2.3": "Interventions Section",
        "2.16.840.1.113883.10.20.22.2.61": "Outcomes Section",
        TemplateIds.CARE_TEAMS_SECTION: "Care Teams Section",
    }

    # Document-level templates
    DOCUMENT_TEMPLATES = {
        "2.16.840.1.113883.10.20.22.1.1": "US Realm Header",
        "2.16.840.1.113883.10.20.22.1.2": "CCD",
        TemplateIds.CARE_PLAN_DOCUMENT: "Care Plan Document",
        "2.16.840.1.113883.10.20.22.1.4": "History and Physical",
        "2.16.840.1.113883.10.20.22.1.5": "Operative Note",
        "2.16.840.1.113883.10.20.22.1.6": "Consultation Note",
        "2.16.840.1.113883.10.20.22.1.7": "Discharge Summary",
        "2.16.840.1.113883.10.20.22.1.8": "Progress Note",
        "2.16.840.1.113883.10.20.22.1.9": "Procedure Note",
        "2.16.840.1.113883.10.20.22.1.10": "Diagnostic Imaging Report",
        "2.16.840.1.113883.10.20.22.1.13": "Transfer Summary",
        "2.16.840.1.113883.10.20.22.1.14": "Referral Note",
    }

    @classmethod
    def is_supported(cls, template_id: str) -> bool:
        """Check if a template ID is supported.

        Args:
            template_id: The C-CDA template ID (OID)

        Returns:
            True if the template has a documented FHIR mapping
        """
        return (
            template_id in cls.ENTRY_TEMPLATES
            or template_id in cls.SECTION_TEMPLATES
            or template_id in cls.DOCUMENT_TEMPLATES
        )

    @classmethod
    def get_template_name(cls, template_id: str) -> str | None:
        """Get the human-readable name for a template ID.

        Args:
            template_id: The C-CDA template ID (OID)

        Returns:
            The template name, or None if not found
        """
        for registry in [cls.ENTRY_TEMPLATES, cls.SECTION_TEMPLATES, cls.DOCUMENT_TEMPLATES]:
            if template_id in registry:
                return registry[template_id]
        return None

    @classmethod
    def get_all_supported_templates(cls) -> set[str]:
        """Get all supported template IDs.

        Returns:
            Set of all supported C-CDA template IDs
        """
        return (
            set(cls.ENTRY_TEMPLATES.keys())
            | set(cls.SECTION_TEMPLATES.keys())
            | set(cls.DOCUMENT_TEMPLATES.keys())
        )
