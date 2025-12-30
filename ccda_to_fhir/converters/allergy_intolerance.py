"""AllergyIntolerance converter: C-CDA Allergy Observation to FHIR AllergyIntolerance resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import CD, CE
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.constants import (
    ALLERGY_TYPE_CATEGORY_MAP,
    CRITICALITY_CODE_TO_FHIR,
    SNOMED_ALLERGY_STATUS_TO_FHIR,
    SNOMED_SEVERITY_TO_FHIR,
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
from ccda_to_fhir.utils.terminology import get_display_for_allergy_clinical_status

from .author_extractor import AuthorExtractor
from .base import BaseConverter

logger = get_logger(__name__)


class AllergyIntoleranceConverter(BaseConverter[Observation]):
    """Convert C-CDA Allergy Intolerance Observation to FHIR AllergyIntolerance resource.

    This converter handles the mapping from C-CDA Allergy Intolerance Observation within
    an Allergy Concern Act to a FHIR R4B AllergyIntolerance resource.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-allergies.html
    """

    def __init__(self, *args, concern_act: Act | None = None, section=None, **kwargs):
        """Initialize the allergy intolerance converter.

        Args:
            concern_act: The Allergy Concern Act containing this observation
            section: The C-CDA Section containing this allergy (for narrative)
        """
        super().__init__(*args, **kwargs)
        self.concern_act = concern_act
        self.section = section

    def convert(self, observation: Observation) -> FHIRResourceDict:
        """Convert a C-CDA Allergy Intolerance Observation to a FHIR AllergyIntolerance resource.

        Args:
            observation: The C-CDA Allergy Intolerance Observation

        Returns:
            FHIR AllergyIntolerance resource as a dictionary

        Raises:
            MissingRequiredFieldError: If the observation lacks required data
        """
        # Check if this is a "no known allergy" case
        is_no_known_allergy = self._is_no_known_allergy(observation)

        # Require participant unless it's a no known allergy case
        if not is_no_known_allergy and not observation.participant:
            raise MissingRequiredFieldError(
                field_name="participant",
                resource_type="Allergy Observation (AllergyIntolerance)",
                details="Allergen (participant) is required for Allergy Observation"
            )

        allergy: JSONObject = {
            "resourceType": "AllergyIntolerance",
            "meta": {
                "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-allergyintolerance"]
            },
        }

        # Generate ID from observation identifier
        if observation.id and len(observation.id) > 0:
            first_id = observation.id[0]
            allergy["id"] = self._generate_allergy_id(first_id.root, first_id.extension)

        # Identifiers
        if observation.id:
            allergy["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in observation.id
                if id_elem.root and not id_elem.null_flavor
            ]

        # Clinical status
        clinical_status = self._determine_clinical_status(observation)
        if clinical_status:
            # ENHANCEMENT: Include display text from terminology map
            display = get_display_for_allergy_clinical_status(clinical_status)
            coding = {
                "system": FHIRSystems.ALLERGY_CLINICAL,
                "code": clinical_status,
            }
            if display:
                coding["display"] = display
            allergy["clinicalStatus"] = {
                "coding": [coding]
            }

        # Verification status
        # For no known allergies, use "confirmed" (they are confirmed absences)
        # For other negated observations, use "refuted"
        if is_no_known_allergy:
            allergy["verificationStatus"] = {
                "coding": [
                    {
                        "system": FHIRSystems.ALLERGY_VERIFICATION,
                        "code": FHIRCodes.AllergyVerification.CONFIRMED,
                    }
                ]
            }
        elif observation.negation_ind:
            allergy["verificationStatus"] = {
                "coding": [
                    {
                        "system": FHIRSystems.ALLERGY_VERIFICATION,
                        "code": FHIRCodes.AllergyVerification.REFUTED,
                    }
                ]
            }
        else:
            # Default to confirmed for non-negated allergies
            allergy["verificationStatus"] = {
                "coding": [
                    {
                        "system": FHIRSystems.ALLERGY_VERIFICATION,
                        "code": FHIRCodes.AllergyVerification.CONFIRMED,
                    }
                ]
            }

        # Type and category (from observation value)
        if observation.value and isinstance(observation.value, (CD, CE)):
            allergy_type, category = self._determine_type_and_category(observation.value.code)
            if allergy_type:
                allergy["type"] = allergy_type
            if category:
                allergy["category"] = [category]

        # Criticality
        criticality = self._extract_criticality(observation)
        if criticality:
            allergy["criticality"] = criticality

        # Code (allergen, negated concept, or substanceExposureRisk extension)
        # Per FHIR spec: substanceExposureRisk extension is used when documenting
        # "no known allergy" to a SPECIFIC substance without a pre-coordinated negated code
        if is_no_known_allergy and self._should_use_substance_exposure_risk(observation):
            # Use substanceExposureRisk extension for specific substance
            # Per FHIR constraint: code SHALL be omitted when using this extension
            substance_code = self._extract_allergen_code(observation)
            allergy.setdefault("extension", []).append({
                "url": "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk",
                "extension": [
                    {
                        "url": "substance",
                        "valueCodeableConcept": substance_code,
                    },
                    {
                        "url": "exposureRisk",
                        "valueCodeableConcept": {
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/allerg-intol-substance-exp-risk",
                                "code": "no-known-reaction-risk",
                                "display": "No Known Reaction Risk",
                            }]
                        },
                    },
                ]
            })
        elif is_no_known_allergy:
            # Use negated concept code based on allergy type
            allergy["code"] = self._get_no_known_allergy_code(observation)
        else:
            # Extract allergen from participant
            allergy["code"] = self._extract_allergen_code(observation)

        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create AllergyIntolerance without patient reference."
            )
        allergy["patient"] = self.reference_registry.get_patient_reference()

        # Onset date
        if observation.effective_time and observation.effective_time.low:
            if observation.effective_time.low.value:
                onset_date = self.convert_date(observation.effective_time.low.value)
                if onset_date:
                    allergy["onsetDateTime"] = onset_date

        # Abatement (as extension if high value exists)
        if observation.effective_time and observation.effective_time.high:
            if observation.effective_time.high.value:
                abatement_date = self.convert_date(observation.effective_time.high.value)
                if abatement_date:
                    allergy.setdefault("extension", []).append({
                        "url": FHIRSystems.ALLERGY_ABATEMENT_EXTENSION,
                        "valueDateTime": abatement_date,
                    })

        # Recorded date (from earliest author time)
        if self.concern_act and self.concern_act.author:
            earliest_time = None
            for author in self.concern_act.author:
                if author.time and author.time.value:
                    if earliest_time is None or author.time.value < earliest_time:
                        earliest_time = author.time.value
            if earliest_time:
                recorded_date = self.convert_date(earliest_time)
                if recorded_date:
                    allergy["recordedDate"] = recorded_date
        elif observation.author:
            earliest_time = None
            for author in observation.author:
                if author.time and author.time.value:
                    if earliest_time is None or author.time.value < earliest_time:
                        earliest_time = author.time.value
            if earliest_time:
                recorded_date = self.convert_date(earliest_time)
                if recorded_date:
                    allergy["recordedDate"] = recorded_date

        # Recorder (from latest author - both concern act and observation)
        extractor = AuthorExtractor()
        all_authors_info = extractor.extract_combined(self.concern_act, observation)

        # Find latest author by time
        authors_with_time = [a for a in all_authors_info if a.time]
        if authors_with_time:
            latest_author = max(authors_with_time, key=lambda a: a.time)
            if latest_author.practitioner_id:
                allergy["recorder"] = {
                    "reference": f"Practitioner/{latest_author.practitioner_id}"
                }
            elif latest_author.device_id:
                allergy["recorder"] = {
                    "reference": f"Device/{latest_author.device_id}"
                }

        # Extract allergy-level severity (if present)
        allergy_level_severity = self._extract_allergy_level_severity(observation)

        # Reactions
        reactions = self._extract_reactions(observation, allergy_level_severity)
        if reactions:
            allergy["reaction"] = reactions

        # Notes (from text or comment activities)
        notes = self._extract_notes(observation)
        if notes:
            allergy["note"] = notes

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=observation, section=self.section)
        if narrative:
            allergy["text"] = narrative

        return allergy

    def _generate_allergy_id(self, root: str | None, extension: str | None) -> str:
        """Generate an allergy resource ID.

        Uses standard ID generation with hashing for consistency across all converters.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A resource ID string
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="allergyintolerance"
        )

    def _is_no_known_allergy(self, observation: Observation) -> bool:
        """Check if this is a "no known allergy" observation.

        A no known allergy has negationInd = true and either:
        - Pattern A: participant with nullFlavor (typically "NA") - general "no known"
        - Pattern B: participant with specific substance code - specific "no known X"

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            True if this is a no known allergy, False otherwise
        """
        if not observation.negation_ind:
            return False

        # If we have a participant, it's a "no known" case
        # (either with nullFlavor or specific substance)
        return bool(observation.participant)

    def _should_use_substance_exposure_risk(self, observation: Observation) -> bool:
        """Check if substanceExposureRisk extension should be used.

        Per FHIR spec and C-CDA on FHIR IG, use substanceExposureRisk extension when:
        - negationInd = true (documenting "no known allergy")
        - participant has a SPECIFIC substance code (not nullFlavor)
        - no pre-coordinated negated concept code exists for that substance

        This enables documenting "no known allergy to penicillin" where no
        SNOMED code like "no known penicillin allergy" exists.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            True if substanceExposureRisk extension should be used
        """
        if not observation.negation_ind or not observation.participant:
            return False

        # Check if participant has a specific substance code (not nullFlavor)
        for participant in observation.participant:
            if participant.type_code == TypeCodes.CONSUMABLE and participant.participant_role:
                playing_entity = participant.participant_role.playing_entity
                if playing_entity and playing_entity.code:
                    # If code has a nullFlavor, this is Pattern A (use negated concept)
                    if playing_entity.code.null_flavor:
                        return False
                    # If code has an actual value, this is Pattern B (use extension)
                    if playing_entity.code.code:
                        return True
        return False

    def _get_no_known_allergy_code(self, observation: Observation) -> FHIRResourceDict:
        """Get the appropriate "no known allergy" negated concept code.

        Maps the observation value code (allergy type) to the corresponding
        "no known" SNOMED code.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            FHIR CodeableConcept for the negated concept
        """
        # Default to general "no known allergy"
        negated_code = SnomedCodes.NO_KNOWN_ALLERGY
        negated_display = "No known allergy"

        # Map based on observation value (allergy type)
        if observation.value and isinstance(observation.value, (CD, CE)):
            value_code = observation.value.code
            if value_code == SnomedCodes.DRUG_ALLERGY:
                negated_code = SnomedCodes.NO_KNOWN_DRUG_ALLERGY
                negated_display = "No known drug allergy"
            elif value_code == SnomedCodes.FOOD_ALLERGY:
                negated_code = SnomedCodes.NO_KNOWN_FOOD_ALLERGY
                negated_display = "No known food allergy"
            elif value_code == SnomedCodes.ENVIRONMENTAL_ALLERGY:
                negated_code = SnomedCodes.NO_KNOWN_ENVIRONMENTAL_ALLERGY
                negated_display = "No known environmental allergy"

        return {
            "coding": [
                {
                    "system": self.map_oid_to_uri("2.16.840.1.113883.6.96"),  # SNOMED CT
                    "code": negated_code,
                    "display": negated_display,
                }
            ]
        }

    def _determine_clinical_status(self, observation: Observation) -> str | None:
        """Determine the clinical status from observation or concern act.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            FHIR clinical status code (active, inactive, resolved)
        """
        # First, check for Allergy Status Observation in entry relationships
        if observation.entry_relationship:
            for rel in observation.entry_relationship:
                if rel.observation and rel.type_code == TypeCodes.REFERENCE:
                    # Check if it's an Allergy Status Observation
                    if rel.observation.code and rel.observation.code.code == CCDACodes.STATUS:
                        # This is an Allergy Status Observation
                        if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                            status_code = rel.observation.value.code
                            return self._map_allergy_status_to_clinical_status(status_code)

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
        return FHIRCodes.AllergyClinical.ACTIVE

    def _map_allergy_status_to_clinical_status(self, snomed_code: str | None) -> str:
        """Map SNOMED allergy status code to FHIR clinical status.

        Args:
            snomed_code: SNOMED CT code for allergy status

        Returns:
            FHIR clinical status code
        """
        return SNOMED_ALLERGY_STATUS_TO_FHIR.get(
            snomed_code, FHIRCodes.AllergyClinical.ACTIVE
        )

    def _map_concern_status_to_clinical_status(
        self, concern_status: str | None, has_abatement: bool = False
    ) -> str:
        """Map concern act status to FHIR clinical status.

        Args:
            concern_status: The concern act statusCode
            has_abatement: Whether the allergy has an abatement date

        Returns:
            FHIR clinical status code
        """
        if concern_status == "active":
            return FHIRCodes.AllergyClinical.ACTIVE
        elif concern_status == "completed":
            return (
                FHIRCodes.AllergyClinical.RESOLVED
                if has_abatement
                else FHIRCodes.AllergyClinical.INACTIVE
            )
        elif concern_status in ("suspended", "aborted"):
            return FHIRCodes.AllergyClinical.INACTIVE
        else:
            return FHIRCodes.AllergyClinical.ACTIVE

    def _determine_type_and_category(
        self, value_code: str | None
    ) -> tuple[str | None, str | None]:
        """Determine FHIR type and category from C-CDA observation value code.

        Args:
            value_code: SNOMED code from observation value

        Returns:
            Tuple of (type, category)
        """
        return ALLERGY_TYPE_CATEGORY_MAP.get(
            value_code, (FHIRCodes.AllergyType.ALLERGY, None)
        )

    def _extract_criticality(self, observation: Observation) -> str | None:
        """Extract criticality from Criticality Observation.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            FHIR criticality code (low, high, unable-to-assess)
        """
        if not observation.entry_relationship:
            return None

        for rel in observation.entry_relationship:
            if rel.observation and rel.type_code == TypeCodes.SUBJECT:
                # Check if it's a Criticality Observation
                if rel.observation.code and rel.observation.code.code == CCDACodes.CRITICALITY:
                    if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                        criticality_code = rel.observation.value.code
                        return CRITICALITY_CODE_TO_FHIR.get(criticality_code)
        return None

    def _extract_allergen_code(self, observation: Observation) -> FHIRResourceDict:
        """Extract allergen code from participant.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            FHIR CodeableConcept for the allergen
        """
        # Find the CSM (Consumable) participant
        for participant in observation.participant:
            if participant.type_code == TypeCodes.CONSUMABLE and participant.participant_role:
                playing_entity = participant.participant_role.playing_entity
                if playing_entity and playing_entity.code:
                    code = playing_entity.code

                    # Get translations if any
                    translations = []
                    if code.translation:
                        for trans in code.translation:
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
                    if playing_entity.name:
                        # Extract string value from name (can be list[ON | str] or single ON | str)
                        names = playing_entity.name if isinstance(playing_entity.name, list) else [playing_entity.name]
                        for name in names:
                            if isinstance(name, str):
                                original_text = name
                                break
                            elif hasattr(name, 'value') and name.value:
                                original_text = name.value
                                break
                    elif code.original_text:
                        original_text = self.extract_original_text(code.original_text, section=None)

                    return self.create_codeable_concept(
                        code=code.code,
                        code_system=code.code_system,
                        display_name=code.display_name,
                        original_text=original_text,
                        translations=translations,
                    )

        # Fallback if no participant found
        return {"text": "Unknown allergen"}

    def _extract_allergy_level_severity(self, observation: Observation) -> str | None:
        """Extract severity from Severity Observation at allergy level.

        Per C-CDA on FHIR IG, severity can be specified at the allergy level (not recommended)
        or at the reaction level. This extracts allergy-level severity if present.

        Args:
            observation: The Allergy Intolerance Observation

        Returns:
            FHIR severity code (mild, moderate, severe) or None
        """
        if not observation.entry_relationship:
            return None

        for rel in observation.entry_relationship:
            if rel.observation and rel.type_code == TypeCodes.SUBJECT:
                # Check if it's a Severity Observation (not nested in a reaction)
                if rel.observation.code and rel.observation.code.code == CCDACodes.SEVERITY:
                    if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                        severity_code = rel.observation.value.code
                        return SNOMED_SEVERITY_TO_FHIR.get(severity_code)
        return None

    def _extract_reactions(
        self, observation: Observation, allergy_level_severity: str | None = None
    ) -> list[FHIRResourceDict]:
        """Extract reactions from Reaction Observations.

        Implements severity inheritance per C-CDA on FHIR IG:
        - Scenario A: Severity only at allergy level → apply to all reactions
        - Scenario B: Severity at both levels → reaction level takes precedence
        - Scenario C: Severity only at reaction level → use reaction severity

        Extracts multiple reaction details per FHIR R4 spec:
        - manifestation (required)
        - onset, severity (standard fields)
        - description (from Reaction Observation text)
        - note (from Comment Activity entries within reaction)

        Args:
            observation: The Allergy Intolerance Observation
            allergy_level_severity: Optional severity from allergy level

        Returns:
            List of FHIR reaction elements
        """
        reactions = []

        if not observation.entry_relationship:
            return reactions

        for rel in observation.entry_relationship:
            if rel.observation and rel.type_code == TypeCodes.MANIFESTATION:
                # This is a Reaction Observation
                reaction: JSONObject = {}

                # Manifestation
                if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                    value = rel.observation.value

                    # Get original text if available (with reference resolution)
                    original_text = None
                    if value.original_text:
                        original_text = self.extract_original_text(value.original_text, section=None)

                    manifestation = self.create_codeable_concept(
                        code=value.code,
                        code_system=value.code_system,
                        display_name=value.display_name,
                        original_text=original_text,
                    )
                    reaction["manifestation"] = [manifestation]

                # Description (from Reaction Observation text element)
                if rel.observation.text:
                    description_text = None
                    if isinstance(rel.observation.text, str):
                        description_text = rel.observation.text
                    elif hasattr(rel.observation.text, "value") and rel.observation.text.value:
                        description_text = rel.observation.text.value
                    elif hasattr(rel.observation.text, "reference"):
                        # Resolve text reference to section narrative
                        description_text = self.extract_original_text(
                            rel.observation.text, section=self.section
                        )

                    if description_text:
                        reaction["description"] = description_text

                # Onset date
                if rel.observation.effective_time:
                    if rel.observation.effective_time.low and rel.observation.effective_time.low.value:
                        onset_date = self.convert_date(rel.observation.effective_time.low.value)
                        if onset_date:
                            reaction["onset"] = onset_date
                    elif hasattr(rel.observation.effective_time, "value") and rel.observation.effective_time.value:
                        onset_date = self.convert_date(rel.observation.effective_time.value)
                        if onset_date:
                            reaction["onset"] = onset_date

                # Severity (with inheritance)
                # Scenario B: Reaction-level severity takes precedence
                reaction_severity = self._extract_reaction_severity(rel.observation)
                if reaction_severity:
                    reaction["severity"] = reaction_severity
                # Scenario A: Fall back to allergy-level severity
                elif allergy_level_severity:
                    reaction["severity"] = allergy_level_severity

                # Notes (from Comment Activity entries within reaction)
                reaction_notes = self._extract_reaction_notes(rel.observation)
                if reaction_notes:
                    reaction["note"] = reaction_notes

                if reaction:
                    reactions.append(reaction)

        return reactions

    def _extract_reaction_severity(self, reaction_observation: Observation) -> str | None:
        """Extract severity from Severity Observation nested in Reaction Observation.

        Args:
            reaction_observation: The Reaction Observation

        Returns:
            FHIR severity code (mild, moderate, severe)
        """
        if not reaction_observation.entry_relationship:
            return None

        for rel in reaction_observation.entry_relationship:
            if rel.observation and rel.type_code == TypeCodes.SUBJECT:
                # Check if it's a Severity Observation
                if rel.observation.code and rel.observation.code.code == CCDACodes.SEVERITY:
                    if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                        severity_code = rel.observation.value.code
                        return SNOMED_SEVERITY_TO_FHIR.get(severity_code)
        return None

    def _extract_reaction_notes(self, reaction_observation: Observation) -> list[JSONObject]:
        """Extract FHIR notes from Reaction Observation.

        Extracts notes from Comment Activity entries (template 2.16.840.1.113883.10.20.22.4.64)
        within the Reaction Observation.

        Args:
            reaction_observation: The Reaction Observation

        Returns:
            List of FHIR Annotation objects (as dicts with 'text' field)
        """
        notes = []

        # Extract from Comment Activity entries
        if reaction_observation.entry_relationship:
            for entry_rel in reaction_observation.entry_relationship:
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

    def _extract_notes(self, observation: Observation) -> list[JSONObject]:
        """Extract FHIR notes from C-CDA observation.

        Extracts notes from:
        1. observation.text element
        2. Comment Activity entries (template 2.16.840.1.113883.10.20.22.4.64)

        Args:
            observation: The Allergy Intolerance Observation

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


def convert_allergy_concern_act(
    act: Act, code_system_mapper=None, metadata_callback=None, section=None, reference_registry=None
) -> list[FHIRResourceDict]:
    """Convert an Allergy Concern Act to a list of FHIR AllergyIntolerance resources.

    Args:
        act: The Allergy Concern Act
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing author metadata
        section: Optional C-CDA Section containing this allergy (for narrative)

    Returns:
        List of FHIR AllergyIntolerance resources (one per Allergy Intolerance Observation)
    """
    allergies = []

    if not act.entry_relationship:
        return allergies

    converter = AllergyIntoleranceConverter(
        code_system_mapper=code_system_mapper,
        concern_act=act,
        section=section,
        reference_registry=reference_registry,
    )

    for rel in act.entry_relationship:
        if rel.observation and rel.type_code == TypeCodes.SUBJECT:
            # This is an Allergy Intolerance Observation
            try:
                allergy = converter.convert(rel.observation)
                allergies.append(allergy)

                # Store author metadata if callback provided
                if metadata_callback and allergy.get("id"):
                    metadata_callback(
                        resource_type="AllergyIntolerance",
                        resource_id=allergy["id"],
                        ccda_element=rel.observation,
                        concern_act=act,
                    )
            except Exception:
                # Log error but continue
                logger.error("Error converting allergy observation", exc_info=True)

    return allergies
