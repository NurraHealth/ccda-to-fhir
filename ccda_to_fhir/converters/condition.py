"""Condition converter: C-CDA Problem Observation to FHIR Condition resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import CD, CE, PQ
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.constants import (
    AGE_UNIT_MAP,
    PROBLEM_TYPE_TO_CONDITION_CATEGORY,
    SECTION_CODE_TO_CONDITION_CATEGORY,
    SNOMED_PROBLEM_STATUS_TO_FHIR,
    SNOMED_SEVERITY_TO_FHIR,
    AgeUnits,
    CCDACodes,
    FHIRCodes,
    FHIRSystems,
    SnomedCodes,
    TemplateIds,
    TypeCodes,
)
from ccda_to_fhir.exceptions import MissingRequiredFieldError
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.utils.terminology import (
    get_display_for_code,
    get_display_for_condition_clinical_status,
)

from .author_extractor import AuthorExtractor
from .base import BaseConverter

logger = get_logger(__name__)


def generate_id_from_observation_content(observation: Observation) -> str:
    """Generate deterministic ID from observation content when no ID exists.

    Creates a reproducible UUID v5 based on observation's code, value, and time.
    This ensures the same observation generates the same ID in both
    ConditionConverter and EncounterConverter.

    Args:
        observation: The observation to generate ID from

    Returns:
        UUID v5 string generated from observation content
    """
    import uuid

    # Build a stable string from observation attributes
    parts = []

    # Add code (observation type)
    if observation.code:
        if hasattr(observation.code, 'code') and observation.code.code:
            parts.append(f"code:{observation.code.code}")
        if hasattr(observation.code, 'code_system') and observation.code.code_system:
            parts.append(f"sys:{observation.code.code_system}")

    # Add value (diagnosis code)
    if observation.value:
        if hasattr(observation.value, 'code') and observation.value.code:
            parts.append(f"value:{observation.value.code}")
        if hasattr(observation.value, 'code_system') and observation.value.code_system:
            parts.append(f"valuesys:{observation.value.code_system}")
        # For string values
        elif isinstance(observation.value, str):
            parts.append(f"value:{observation.value}")

    # Add effective time if present
    if observation.effective_time:
        if hasattr(observation.effective_time, 'value') and observation.effective_time.value:
            parts.append(f"time:{observation.effective_time.value}")
        elif hasattr(observation.effective_time, 'low') and observation.effective_time.low:
            if hasattr(observation.effective_time.low, 'value'):
                parts.append(f"time:{observation.effective_time.low.value}")

    # Fallback: if no parts were found, use random UUID
    if not parts:
        return str(uuid.uuid4())

    # Create deterministic UUID v5 from concatenated parts
    content_string = "|".join(parts)
    # Use a namespace UUID specific to this use case
    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace UUID
    return str(uuid.uuid5(namespace, content_string))


class ConditionConverter(BaseConverter[Observation]):
    """Convert C-CDA Problem Observation to FHIR Condition resource.

    This converter handles the mapping from C-CDA Problem Observation within
    a Problem Concern Act to a FHIR R4B Condition resource, including clinical
    status, verification status, and US Core requirements.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-problems.html
    """

    def __init__(self, *args, section_code: str | None = None, concern_act: Act | None = None, section=None, **kwargs):
        """Initialize the condition converter.

        Args:
            section_code: The LOINC code of the section containing this problem
            concern_act: The Problem Concern Act containing this observation
            section: The C-CDA Section containing this condition (for narrative)
        """
        super().__init__(*args, **kwargs)
        self.section_code = section_code
        self.concern_act = concern_act
        self.section = section

    def convert(self, observation: Observation) -> FHIRResourceDict:
        """Convert a C-CDA Problem Observation to a FHIR Condition resource.

        Args:
            observation: The C-CDA Problem Observation

        Returns:
            FHIR Condition resource as a dictionary

        Raises:
            MissingRequiredFieldError: If the observation lacks required data
        """
        if not observation.value:
            raise MissingRequiredFieldError(
                field_name="value",
                resource_type="Problem Observation (Condition)",
                details="Diagnosis code is required for Problem Observation"
            )

        condition: JSONObject = {
            "resourceType": "Condition",
        }

        # Generate ID from observation identifier
        if observation.id and len(observation.id) > 0:
            first_id = observation.id[0]
            condition["id"] = self._generate_condition_id(first_id.root, first_id.extension)
        else:
            # Fallback: Generate deterministic ID from observation content
            # This ensures the same observation gets the same ID in both
            # ConditionConverter and EncounterConverter (for diagnosis references)
            condition["id"] = self._generate_id_from_observation_content(observation)

        # Identifiers
        if observation.id:
            condition["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in observation.id
                if id_elem.root
            ]

        # Clinical status
        clinical_status = self._determine_clinical_status(observation)
        if clinical_status:
            # ENHANCEMENT: Include display text from terminology map
            display = get_display_for_condition_clinical_status(clinical_status)
            coding = {
                "system": FHIRSystems.CONDITION_CLINICAL,
                "code": clinical_status,
            }
            if display:
                coding["display"] = display
            condition["clinicalStatus"] = {
                "coding": [coding]
            }

        # Handle negation: Check if this is a generic "no known problems" scenario
        # or a specific condition being refuted
        uses_negated_concept_code = False
        if observation.negation_ind and observation.value:
            # Check if the value is a generic problem code
            if isinstance(observation.value, (CD, CE)) and observation.value.code in (
                SnomedCodes.PROBLEM,  # 55607006
                SnomedCodes.FINDING,  # 404684003
                SnomedCodes.CONDITION,  # 64572001
            ):
                # Use negated concept code for generic problems
                uses_negated_concept_code = True
                condition["code"] = self.create_codeable_concept(
                    code=SnomedCodes.NO_CURRENT_PROBLEMS,
                    code_system="2.16.840.1.113883.6.96",  # SNOMED CT
                    display_name="No current problems or disability",
                )
            else:
                # For specific conditions, set verification status to refuted
                # ENHANCEMENT: Include display text from terminology map
                display = get_display_for_code(
                    FHIRSystems.CONDITION_VERIFICATION,
                    FHIRCodes.ConditionVerification.REFUTED
                )
                coding = {
                    "system": FHIRSystems.CONDITION_VERIFICATION,
                    "code": FHIRCodes.ConditionVerification.REFUTED,
                }
                if display:
                    coding["display"] = display
                condition["verificationStatus"] = {
                    "coding": [coding]
                }

        # Category (from section code)
        categories = self._determine_categories(observation)
        if categories:
            condition["category"] = categories

        # Code (diagnosis/problem) - only if not already set by negated concept code logic
        if "code" not in condition:
            condition["code"] = self._convert_diagnosis_code(observation.value)

        # Severity (from Severity Observation)
        severity = self._extract_severity(observation)
        if severity:
            condition["severity"] = severity

        # Body site
        if observation.target_site_code:
            body_sites = []
            for site_code in observation.target_site_code:
                if site_code.code:
                    body_site = self.create_codeable_concept(
                        code=site_code.code,
                        code_system=site_code.code_system,
                        display_name=site_code.display_name,
                    )
                    if body_site:
                        body_sites.append(body_site)
            if body_sites:
                condition["bodySite"] = body_sites

        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Condition without patient reference."
            )
        condition["subject"] = self.reference_registry.get_patient_reference()

        # Onset and abatement
        onset, abatement = self._convert_effective_time(observation)
        if onset:
            condition.update(onset)
        if abatement:
            condition.update(abatement)

        # Recorded date (from earliest author time)
        if observation.author:
            earliest_time = None
            for author in observation.author:
                if author.time and author.time.value:
                    if earliest_time is None or author.time.value < earliest_time:
                        earliest_time = author.time.value
            if earliest_time:
                recorded_date = self.convert_date(earliest_time)
                if recorded_date:
                    condition["recordedDate"] = recorded_date

        # assertedDate extension (from Date of Diagnosis Act)
        asserted_date = self._extract_asserted_date(observation)
        if asserted_date:
            if "extension" not in condition:
                condition["extension"] = []
            condition["extension"].append({
                "url": FHIRSystems.CONDITION_ASSERTED_DATE,
                "valueDateTime": asserted_date
            })

        # Recorder (from latest author - both concern act and observation)
        extractor = AuthorExtractor()
        all_authors_info = extractor.extract_combined(self.concern_act, observation)

        # Find latest author by time
        authors_with_time = [a for a in all_authors_info if a.time]
        if authors_with_time:
            latest_author = max(authors_with_time, key=lambda a: a.time)
            if latest_author.practitioner_id:
                condition["recorder"] = {
                    "reference": f"Practitioner/{latest_author.practitioner_id}"
                }
            elif latest_author.device_id:
                condition["recorder"] = {
                    "reference": f"Device/{latest_author.device_id}"
                }

        # Evidence (from related observations)
        if observation.entry_relationship:
            evidence = self._extract_evidence(observation)
            if evidence:
                condition["evidence"] = evidence

        # Notes (from text or comment activities)
        notes = self._extract_notes(observation)
        if notes:
            condition["note"] = notes

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=observation, section=self.section)
        if narrative:
            condition["text"] = narrative

        return condition

    def _extract_asserted_date(self, observation: Observation) -> str | None:
        """Extract assertedDate from Date of Diagnosis Act.

        The assertedDate represents when the condition was first asserted or
        acknowledged by a clinician, which may differ from when it was recorded
        in the system or when the patient first experienced symptoms.

        C-CDA Source: Date of Diagnosis Act (template 2.16.840.1.113883.10.20.22.4.502)
        in Problem Observation entry relationships.

        Args:
            observation: Problem Observation containing entry relationships

        Returns:
            ISO 8601 datetime string or None if not found

        Reference:
            http://hl7.org/fhir/R4/extension-condition-asserteddate.html
        """
        if not observation.entry_relationship:
            return None

        for entry_rel in observation.entry_relationship:
            # Look for acts with Date of Diagnosis template
            if entry_rel.act and entry_rel.act.template_id:
                for template in entry_rel.act.template_id:
                    if template.root == TemplateIds.DATE_OF_DIAGNOSIS_ACT:
                        # Found Date of Diagnosis Act
                        if entry_rel.act.effective_time:
                            eff_time = entry_rel.act.effective_time
                            # Handle both IVL_TS (with .low) and simple TS
                            if hasattr(eff_time, 'low') and eff_time.low:
                                return self.convert_date(eff_time.low.value)
                            elif hasattr(eff_time, 'value') and eff_time.value:
                                return self.convert_date(eff_time.value)

        return None

    def _generate_condition_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Condition ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Condition", root, extension)

    def _generate_id_from_observation_content(self, observation: Observation) -> str:
        """Generate deterministic ID from observation content when no ID exists.

        Delegates to the module-level function for consistency.

        Args:
            observation: The observation to generate ID from

        Returns:
            UUID v5 string generated from observation content
        """
        return generate_id_from_observation_content(observation)

    def _determine_clinical_status(self, observation: Observation) -> str | None:
        """Determine the clinical status from observation and concern act.

        Args:
            observation: The Problem Observation

        Returns:
            FHIR clinical status code (active, inactive, resolved, etc.)
        """
        # First, check for Problem Status Observation in entry relationships
        if observation.entry_relationship:
            for rel in observation.entry_relationship:
                if rel.observation and rel.type_code == TypeCodes.REFERENCE:
                    # Check if it's a Problem Status Observation
                    if rel.observation.code and rel.observation.code.code == CCDACodes.STATUS:
                        # This is a Problem Status Observation
                        if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                            status_code = rel.observation.value.code
                            return self._map_problem_status_to_clinical_status(status_code)

        # Fallback to concern act status if available
        if self.concern_act and self.concern_act.status_code:
            return self._map_concern_status_to_clinical_status(
                self.concern_act.status_code.code,
                has_abatement=bool(
                    observation.effective_time
                    and observation.effective_time.high
                    and observation.effective_time.high.value
                ),
            )

        # Default to active if no status info
        return FHIRCodes.ConditionClinical.ACTIVE

    def _map_problem_status_to_clinical_status(self, snomed_code: str | None) -> str:
        """Map SNOMED problem status code to FHIR clinical status.

        Args:
            snomed_code: SNOMED CT code for problem status

        Returns:
            FHIR clinical status code
        """
        return SNOMED_PROBLEM_STATUS_TO_FHIR.get(
            snomed_code, FHIRCodes.ConditionClinical.ACTIVE
        )

    def _map_concern_status_to_clinical_status(
        self, concern_status: str | None, has_abatement: bool = False
    ) -> str:
        """Map concern act status to FHIR clinical status.

        Args:
            concern_status: The concern act statusCode
            has_abatement: Whether the problem has an abatement date

        Returns:
            FHIR clinical status code
        """
        if concern_status == "active":
            return FHIRCodes.ConditionClinical.ACTIVE
        elif concern_status == "completed":
            return (
                FHIRCodes.ConditionClinical.RESOLVED
                if has_abatement
                else FHIRCodes.ConditionClinical.INACTIVE
            )
        elif concern_status in ("suspended", "aborted"):
            return FHIRCodes.ConditionClinical.INACTIVE
        else:
            return FHIRCodes.ConditionClinical.ACTIVE

    def _determine_categories(self, observation: Observation) -> list[FHIRResourceDict]:
        """Determine FHIR condition categories.

        Args:
            observation: The Problem Observation

        Returns:
            List of category CodeableConcepts
        """
        categories = []

        # Category from section code
        section_category = self._section_code_to_category(self.section_code)
        if section_category:
            categories.append(
                {
                    "coding": [
                        {
                            "system": FHIRSystems.CONDITION_CATEGORY,
                            "code": section_category,
                        }
                    ]
                }
            )

        # Additional category from problem type code
        if observation.code and observation.code.code:
            problem_type_category = self._problem_type_to_category(observation.code.code)
            # Only add if different from section category
            if problem_type_category and problem_type_category != section_category:
                categories.append(
                    {
                        "coding": [
                            {
                                "system": FHIRSystems.CONDITION_CATEGORY,
                                "code": problem_type_category,
                            }
                        ]
                    }
                )

        # Default to problem-list-item if no categories determined
        if not categories:
            categories.append(
                {
                    "coding": [
                        {
                            "system": FHIRSystems.CONDITION_CATEGORY,
                            "code": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,
                        }
                    ]
                }
            )

        return categories

    def _section_code_to_category(self, section_code: str | None) -> str | None:
        """Map section LOINC code to condition category.

        Args:
            section_code: The LOINC code of the section

        Returns:
            FHIR condition category code
        """
        return SECTION_CODE_TO_CONDITION_CATEGORY.get(section_code) if section_code else None

    def _problem_type_to_category(self, problem_type_code: str | None) -> str | None:
        """Map problem type SNOMED code to condition category.

        Args:
            problem_type_code: SNOMED code for problem type

        Returns:
            FHIR condition category code
        """
        return PROBLEM_TYPE_TO_CONDITION_CATEGORY.get(problem_type_code) if problem_type_code else None

    def _convert_diagnosis_code(self, value: CD | CE) -> FHIRResourceDict:
        """Convert observation value to FHIR diagnosis code.

        Args:
            value: The observation value (should be CD/CE with diagnosis code)

        Returns:
            FHIR CodeableConcept
        """
        if isinstance(value, (CD, CE)):
            # Get translations if any
            translations = []
            if value.translation:
                for trans in value.translation:
                    if trans.code and trans.code_system:
                        translations.append(
                            {
                                "code": trans.code,
                                "code_system": trans.code_system,
                                "display_name": trans.display_name,
                            }
                        )

            # Get original text if available (with reference resolution)
            original_text = None
            if value.original_text:
                # Try to resolve reference to narrative (section context may not be available here)
                original_text = self.extract_original_text(value.original_text, section=None)

            return self.create_codeable_concept(
                code=value.code,
                code_system=value.code_system,
                display_name=value.display_name,
                original_text=original_text,
                translations=translations,
            )
        else:
            # Fallback for unexpected types
            return {"text": str(value)}

    def _convert_effective_time(
        self, observation: Observation
    ) -> tuple[JSONObject | None, JSONObject | None]:
        """Convert effective time to onset and abatement.

        FHIR R4B Compliance: onset[x] is a choice type - only ONE variant can be populated.
        Per https://hl7.org/fhir/R4B/condition.html, the choice types are:
        onsetDateTime | onsetAge | onsetPeriod | onsetRange | onsetString

        Priority for choosing onset variant:
        1. onsetAge (if Age at Onset observation exists) - most specific
        2. onsetPeriod (if both low and high dates exist) - date range
        3. onsetDateTime (if only low date exists) - specific date

        Args:
            observation: The Problem Observation

        Returns:
            Tuple of (onset_dict, abatement_dict)
        """
        onset = None
        abatement = None

        if not observation.effective_time:
            return onset, abatement

        eff_time = observation.effective_time

        # Priority 1: Check for Age at Onset observation (most specific)
        onset_age_data = None
        if observation.entry_relationship:
            for rel in observation.entry_relationship:
                if (
                    rel.observation
                    and rel.observation.code
                    and rel.observation.code.code == CCDACodes.AGE_AT_ONSET
                ):
                    if rel.observation.value and isinstance(rel.observation.value, PQ):
                        age = rel.observation.value.value
                        unit = rel.observation.value.unit or AgeUnits.YEARS_CCDA
                        if age is not None:
                            onset_age_data = (age, unit)
                    break

        # If Age at Onset exists, use onsetAge (FHIR choice type - only one variant allowed)
        if onset_age_data:
            age, unit = onset_age_data
            # Convert age to numeric type
            try:
                age_numeric = int(age) if float(age).is_integer() else float(age)
            except (ValueError, TypeError):
                age_numeric = age  # Keep as string if conversion fails

            # Map age units
            if unit in AGE_UNIT_MAP:
                fhir_unit, fhir_code = AGE_UNIT_MAP[unit]
            else:
                fhir_unit = unit
                fhir_code = unit

            onset = {
                "onsetAge": {
                    "value": age_numeric,
                    "unit": fhir_unit,
                    "system": FHIRSystems.UCUM,
                    "code": fhir_code,
                }
            }
        # Priority 2: Check for period (both low and high dates)
        elif eff_time.low and eff_time.low.value and eff_time.high and eff_time.high.value:
            onset_date = self.convert_date(eff_time.low.value)
            end_date = self.convert_date(eff_time.high.value)
            if onset_date and end_date:
                # Use onsetPeriod for date range
                onset = {
                    "onsetPeriod": {
                        "start": onset_date,
                        "end": end_date
                    }
                }
                # Don't set abatement if we used high date in onsetPeriod
                # The high date represents end of onset period, not abatement
            elif onset_date:
                # If end_date conversion failed, fall back to onsetDateTime
                onset = {"onsetDateTime": onset_date}
        # Priority 3: Check for single onset date (low value only)
        elif eff_time.low and eff_time.low.value:
            onset_date = self.convert_date(eff_time.low.value)
            if onset_date:
                onset = {"onsetDateTime": onset_date}

        # Check for abatement (high value) - only if not used in onsetPeriod
        # Abatement represents when the condition resolved, not the end of onset period
        if eff_time.high and "onsetPeriod" not in (onset or {}):
            if eff_time.high.value:
                abatement_date = self.convert_date(eff_time.high.value)
                if abatement_date:
                    abatement = {"abatementDateTime": abatement_date}
            elif eff_time.high.null_flavor:
                # Unknown abatement date - use data-absent-reason extension
                # Per C-CDA on FHIR IG ConceptMap CF-NullFlavorDataAbsentReason
                abatement = {
                    "_abatementDateTime": {
                        "extension": [
                            self.create_data_absent_reason_extension(eff_time.high.null_flavor)
                        ]
                    }
                }

        return onset, abatement

    def _extract_severity(self, observation: Observation) -> JSONObject | None:
        """Extract severity from Severity Observation.

        Args:
            observation: The Problem Observation

        Returns:
            FHIR CodeableConcept for severity or None
        """
        if not observation.entry_relationship:
            return None

        for rel in observation.entry_relationship:
            if rel.observation and rel.type_code == TypeCodes.REFERENCE:
                # Check if it's a Severity Observation
                if rel.observation.code and rel.observation.code.code == CCDACodes.SEVERITY:
                    if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                        severity_code = rel.observation.value.code
                        # Check if this is a valid SNOMED severity code
                        if severity_code in SNOMED_SEVERITY_TO_FHIR:
                            return self.create_codeable_concept(
                                code=severity_code,
                                code_system=rel.observation.value.code_system,
                                display_name=rel.observation.value.display_name,
                            )
        return None

    def _extract_notes(self, observation: Observation) -> list[JSONObject]:
        """Extract FHIR notes from C-CDA observation.

        Extracts notes from:
        1. observation.text element
        2. Comment Activity entries (template 2.16.840.1.113883.10.20.22.4.64)

        Args:
            observation: The Problem Observation

        Returns:
            List of FHIR Annotation objects (as dicts with 'text' field)
        """
        notes = []

        # Extract from text element
        if observation.text:
            text_content = None
            if isinstance(observation.text, str):
                text_content = observation.text
            elif hasattr(observation.text, "value") and observation.text.value:
                text_content = observation.text.value

            if text_content:
                notes.append({"text": text_content})

        # Extract from Comment Activity entries
        if observation.entry_relationship:
            for entry_rel in observation.entry_relationship:
                if hasattr(entry_rel, "act") and entry_rel.act:
                    act = entry_rel.act
                    # Check if it's a Comment Activity
                    if hasattr(act, "template_id") and act.template_id:
                        for template in act.template_id:
                            if template.root == TemplateIds.COMMENT_ACTIVITY:
                                # This is a Comment Activity
                                if hasattr(act, "text") and act.text:
                                    comment_text = None
                                    if isinstance(act.text, str):
                                        comment_text = act.text
                                    elif hasattr(act.text, "value") and act.text.value:
                                        comment_text = act.text.value

                                    if comment_text:
                                        notes.append({"text": comment_text})
                                break

        return notes

    def _generate_observation_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Observation ID from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A resource ID string
        """
        if extension:
            clean_ext = extension.lower().replace(" ", "-").replace(".", "-")
            return f"observation-{clean_ext}"
        elif root:
            root_suffix = root.replace(".", "").replace("-", "")[-16:]
            return f"observation-{root_suffix}"
        else:
            raise ValueError(
                "Cannot generate Observation ID: no identifiers provided. "
                "C-CDA Observation must have id element."
            )

    def _extract_evidence(self, observation: Observation) -> list[JSONObject] | None:
        """Extract evidence from related observations.

        Supporting observations (e.g., lab results) and assessment scale observations
        that support the diagnosis are converted to references and linked as evidence.detail.

        Args:
            observation: The Problem Observation

        Returns:
            List of evidence dicts with detail references, or None
        """
        if not observation.entry_relationship:
            return None

        evidence_list = []

        for entry_rel in observation.entry_relationship:
            # Look for supporting observations (typeCode="SPRT") and component observations (typeCode="COMP")
            if hasattr(entry_rel, "type_code") and entry_rel.type_code in (TypeCodes.SUPPORT, TypeCodes.COMPONENT):
                if hasattr(entry_rel, "observation") and entry_rel.observation:
                    supporting_obs = entry_rel.observation

                    # Generate observation ID from the supporting observation's identifiers
                    obs_id = None
                    if hasattr(supporting_obs, "id") and supporting_obs.id:
                        for id_elem in supporting_obs.id:
                            if id_elem.root:
                                obs_id = self._generate_observation_id(id_elem.root, id_elem.extension)
                                break

                    # Skip evidence entry if we cannot generate a valid ID
                    if not obs_id:
                        logger.warning(
                            "Skipping evidence observation without identifiers. "
                            "C-CDA supporting observation must have id element."
                        )
                        continue

                    # Add evidence detail reference
                    evidence_list.append({
                        "detail": [{
                            "reference": f"Observation/{obs_id}"
                        }]
                    })

        return evidence_list if evidence_list else None


def convert_problem_concern_act(
    act: Act,
    section_code: str | None = None,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> list[FHIRResourceDict]:
    """Convert a Problem Concern Act to a list of FHIR Condition resources.

    Args:
        act: The Problem Concern Act
        section_code: The LOINC code of the section
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing author metadata
        section: Optional C-CDA Section containing this problem (for narrative)

    Returns:
        List of FHIR Condition resources (one per Problem Observation)
    """
    conditions = []

    if not act.entry_relationship:
        return conditions

    converter = ConditionConverter(
        code_system_mapper=code_system_mapper,
        section_code=section_code,
        concern_act=act,
        section=section,
        reference_registry=reference_registry,
    )

    for rel in act.entry_relationship:
        if rel.observation and rel.type_code == TypeCodes.SUBJECT:
            # This is a Problem Observation
            try:
                condition = converter.convert(rel.observation)
                conditions.append(condition)

                # Store author metadata if callback provided
                if metadata_callback and condition.get("id"):
                    metadata_callback(
                        resource_type="Condition",
                        resource_id=condition["id"],
                        ccda_element=rel.observation,
                        concern_act=act,
                    )
            except Exception:
                # Log error but continue
                logger.error("Error converting problem observation", exc_info=True)

    return conditions
