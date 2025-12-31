"""Observation converter: C-CDA Observation to FHIR Observation resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, ED, INT, IVL_PQ, PQ, ST
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.constants import (
    BP_DIASTOLIC_CODE,
    BP_DIASTOLIC_DISPLAY,
    BP_PANEL_CODE,
    BP_PANEL_DISPLAY,
    BP_SYSTOLIC_CODE,
    BP_SYSTOLIC_DISPLAY,
    LOINC_TO_SDOH_CATEGORY,
    O2_CONCENTRATION_CODE,
    O2_CONCENTRATION_DISPLAY,
    O2_FLOW_RATE_CODE,
    O2_FLOW_RATE_DISPLAY,
    OBSERVATION_STATUS_TO_FHIR,
    PULSE_OX_ALT_CODE,
    PULSE_OX_PRIMARY_CODE,
    SDOH_CATEGORY_DISPLAY,
    VITAL_SIGNS_PANEL_CODE,
    VITAL_SIGNS_PANEL_DISPLAY,
    FHIRCodes,
    FHIRSystems,
    TemplateIds,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.utils.terminology import get_display_for_code

from .base import BaseConverter


class ObservationConverter(BaseConverter[Observation]):
    """Convert C-CDA Observation to FHIR Observation resource.

    This converter handles the mapping from C-CDA Observation to FHIR R4B
    Observation resource. It supports multiple observation types:
    - Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27)
    - Result Observation (2.16.840.1.113883.10.20.22.4.2)
    - Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78)
    - Social History Observation (2.16.840.1.113883.10.20.22.4.38)

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-observations.html
    """

    def __init__(self, *args, **kwargs):
        """Initialize the observation converter."""
        super().__init__(*args, **kwargs)

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Observation to a FHIR Observation.

        Args:
            observation: The C-CDA Observation
            section: The C-CDA Section containing this observation (for narrative)

        Returns:
            FHIR Observation resource as a dictionary

        Raises:
            ValueError: If the observation lacks required data
        """
        # FHIR R4 Requirement: Observation.code is required (1..1)
        # Validate that we can extract a valid code before creating the resource
        if not observation.code:
            raise ValueError("Observation must have a code element")

        code_cc = self._convert_code_to_codeable_concept(observation.code)
        if not code_cc:
            # Code has nullFlavor with no text - cannot create valid FHIR Observation
            # Try to extract text from narrative if available
            text_from_narrative = None
            if observation.text:
                text_from_narrative = self.extract_original_text(observation.text, section=section)

            if not text_from_narrative:
                raise ValueError(
                    "Observation code has nullFlavor with no extractable text. "
                    "Cannot create valid FHIR Observation without code."
                )

            # Create a text-only CodeableConcept from narrative
            code_cc = {"text": text_from_narrative}

        fhir_obs: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
        }

        # US Core profile will be determined after category is established
        # (different profiles for lab, vital signs, smoking status, etc.)

        # 1. Generate ID from observation identifier
        if observation.id and len(observation.id) > 0:
            for id_elem in observation.id:
                if id_elem.root and not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                    fhir_obs["id"] = self._generate_observation_id(
                        id_elem.root, id_elem.extension
                    )
                    break

        # If no valid ID from identifiers, try fallback strategies
        if "id" not in fhir_obs:
            # Fallback 1: Use code-based ID (e.g., "obs-8302-2" for body height)
            if observation.code and hasattr(observation.code, "code") and observation.code.code:
                code_value = observation.code.code.lower().replace(" ", "-")
                fhir_obs["id"] = f"obs-{self.sanitize_id(code_value)}"
            # Fallback 2: Use template ID if available
            elif hasattr(observation, "template_id") and observation.template_id:
                for template in observation.template_id:
                    if hasattr(template, "root") and template.root:
                        fhir_obs["id"] = f"obs-{self.sanitize_id(template.root)}"
                        break
            # Fallback 3: Generate synthetic UUID
            # This handles real-world C-CDA with all id elements having nullFlavor
            if "id" not in fhir_obs:
                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                fhir_obs["id"] = generate_id_from_identifiers("Observation", None, None)

        # 2. Identifiers
        if observation.id:
            identifiers = []
            for id_elem in observation.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                fhir_obs["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(observation)
        fhir_obs["status"] = status

        # 4. Category - determine based on template ID and observation code
        categories = self._determine_category(observation)
        if categories:
            fhir_obs["category"] = categories

        # 4b. Set US Core profile based on category
        profile = self._determine_us_core_profile(categories, observation)
        if profile:
            fhir_obs["meta"] = {"profile": [profile]}

        # 5. Code (required) - already validated and extracted above
        fhir_obs["code"] = code_cc

        # 6. Subject (patient reference)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Observation without patient reference."
            )
        fhir_obs["subject"] = self.reference_registry.get_patient_reference()

        # 7. Effective time (effectiveDateTime or effectivePeriod)
        effective_time = self._extract_effective_time(observation)
        if effective_time:
            # effective_time can be either a string (effectiveDateTime) or a dict (effectivePeriod)
            if isinstance(effective_time, dict):
                fhir_obs["effectivePeriod"] = effective_time
            else:
                fhir_obs["effectiveDateTime"] = effective_time

        # 8. Value - handle different value types
        value_element = self._convert_value(observation)
        if value_element:
            # Merge value element into observation (valueQuantity, valueCodeableConcept, etc.)
            fhir_obs.update(value_element)

        # 9. Interpretation
        if observation.interpretation_code and len(observation.interpretation_code) > 0:
            interpretations = []
            for interp_code in observation.interpretation_code:
                if isinstance(interp_code, (CD, CE)):
                    interp_cc = self._convert_code_to_codeable_concept(interp_code)
                    if interp_cc:
                        interpretations.append(interp_cc)
            if interpretations:
                fhir_obs["interpretation"] = interpretations

        # 10. Method code
        if observation.method_code and len(observation.method_code) > 0:
            # Per FHIR R4: method is 0..1 (single CodeableConcept)
            # Take the first method code if multiple are present
            first_method = observation.method_code[0]
            if isinstance(first_method, (CD, CE)):
                method_cc = self._convert_code_to_codeable_concept(first_method)
                if method_cc:
                    fhir_obs["method"] = method_cc

        # 11. Body site (target site code)
        if observation.target_site_code and len(observation.target_site_code) > 0:
            # Per FHIR R4: bodySite is 0..1 (single CodeableConcept)
            # Take the first target site code if multiple are present
            first_site = observation.target_site_code[0]
            if isinstance(first_site, (CD, CE)):
                # Use specialized method that handles laterality qualifiers
                body_site_cc = self._convert_body_site_with_qualifiers(first_site)
                if body_site_cc:
                    fhir_obs["bodySite"] = body_site_cc

        # 12. Reference ranges
        # Per C-CDA on FHIR IG: Only map reference ranges with interpretationCode="N" (normal)
        # FHIR expects reference ranges to be "normal" ranges
        if observation.reference_range:
            ref_ranges = []
            for ref_range in observation.reference_range:
                if ref_range.observation_range and ref_range.observation_range.value:
                    # Filter for normal ranges only (interpretationCode="N")
                    # If no interpretationCode is present, assume it's a normal range (common case)
                    obs_range = ref_range.observation_range
                    if obs_range.interpretation_code:
                        # Only include if interpretationCode is "N" (Normal)
                        if obs_range.interpretation_code.code and obs_range.interpretation_code.code.upper() == "N":
                            fhir_ref_range = self._convert_reference_range(obs_range)
                            if fhir_ref_range:
                                ref_ranges.append(fhir_ref_range)
                    else:
                        # No interpretationCode present - assume normal range
                        fhir_ref_range = self._convert_reference_range(obs_range)
                        if fhir_ref_range:
                            ref_ranges.append(fhir_ref_range)
            if ref_ranges:
                fhir_obs["referenceRange"] = ref_ranges

        # 13. Performers (who performed/observed the observation)
        # Per US Core: performer is Must-Support for many observation profiles
        # Maps from C-CDA performer element to FHIR Reference(Practitioner|Organization)
        if observation.performer:
            performers = []
            for performer in observation.performer:
                if performer.assigned_entity and performer.assigned_entity.id:
                    # Extract practitioner ID from assigned entity
                    for id_elem in performer.assigned_entity.id:
                        if id_elem.root:
                            practitioner_id = self._generate_practitioner_id(
                                id_elem.root, id_elem.extension
                            )
                            performers.append({
                                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{practitioner_id}"
                            })
                            break  # Use first valid ID
            if performers:
                fhir_obs["performer"] = performers

        # 14. Pregnancy observation special handling
        if observation.template_id:
            from ccda_to_fhir.constants import TemplateIds
            is_pregnancy = any(
                t.root == TemplateIds.PREGNANCY_OBSERVATION
                for t in observation.template_id
                if t.root
            )
            if is_pregnancy:
                self._handle_pregnancy_observation(observation, fhir_obs)

        # 15. Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=observation, section=section)
        if narrative:
            fhir_obs["text"] = narrative

        # US Core STU6.1 Constraint us-core-2:
        # "If there is no component or hasMember element then either a value[x] or
        # a data absent reason must be present"
        # Add dataAbsentReason as final step if no value/component/hasMember
        has_value = any(k.startswith("value") for k in fhir_obs.keys())
        has_data_absent = "dataAbsentReason" in fhir_obs
        has_component = "component" in fhir_obs
        has_has_member = "hasMember" in fhir_obs

        if not (has_value or has_data_absent or has_component or has_has_member):
            # Check for nullFlavor on value element
            has_null_flavor = (
                observation.value
                and hasattr(observation.value, 'null_flavor')
                and observation.value.null_flavor
            )

            if has_null_flavor:
                # Map C-CDA nullFlavor to FHIR DataAbsentReason
                fhir_obs["dataAbsentReason"] = {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                        "code": self._map_null_flavor_to_data_absent_reason(observation.value.null_flavor),
                    }]
                }
            else:
                # No value and no nullFlavor - use generic "unknown" reason
                fhir_obs["dataAbsentReason"] = {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                        "code": "unknown",
                        "display": "Unknown"
                    }],
                    "text": "Value not provided in source C-CDA document"
                }

        return fhir_obs

    def convert_vital_signs_organizer(self, organizer: Organizer, section=None) -> tuple[FHIRResourceDict, list[FHIRResourceDict]]:
        """Convert a C-CDA Vital Signs Organizer to FHIR Observation resources.

        The vital signs organizer becomes a panel Observation with individual
        vital sign observations as standalone resources (not contained).

        Args:
            organizer: The C-CDA Vital Signs Organizer
            section: The C-CDA Section containing this organizer (for narrative)

        Returns:
            Tuple of (panel_observation, list_of_individual_observations)
        """
        panel: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
        }

        # 1. Generate ID from organizer identifier
        panel_id = None
        if organizer.id and len(organizer.id) > 0:
            for id_elem in organizer.id:
                if id_elem.root and not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                    panel_id = self._generate_observation_id(id_elem.root, id_elem.extension)
                    panel["id"] = panel_id
                    break

        # If no valid ID from identifiers, try fallback strategies
        if panel_id is None:
            # Fallback 1: Use code-based ID (e.g., "obs-46680005" for vital signs)
            if organizer.code and hasattr(organizer.code, "code") and organizer.code.code:
                code_value = organizer.code.code.lower().replace(" ", "-")
                panel_id = f"obs-{self.sanitize_id(code_value)}"
                panel["id"] = panel_id
            # Fallback 2: Use template ID if available
            elif hasattr(organizer, "template_id") and organizer.template_id:
                for template in organizer.template_id:
                    if hasattr(template, "root") and template.root:
                        panel_id = f"obs-{self.sanitize_id(template.root)}"
                        panel["id"] = panel_id
                        break
            # Fallback 3: Generate synthetic UUID
            # This handles real-world C-CDA with all id elements having nullFlavor
            if panel_id is None:
                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                panel_id = generate_id_from_identifiers("Observation", None, None)
                panel["id"] = panel_id

        # 2. Identifiers
        if organizer.id:
            identifiers = []
            for id_elem in organizer.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                panel["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_organizer_status(organizer)
        panel["status"] = status

        # 4. Category - vital-signs
        panel["category"] = [
            {
                "coding": [
                    {
                        "system": FHIRSystems.OBSERVATION_CATEGORY,
                        "code": FHIRCodes.ObservationCategory.VITAL_SIGNS,
                        "display": "Vital Signs",
                    }
                ]
            }
        ]

        # 5. Code - use standard vital signs panel code
        panel["code"] = {
            "coding": [
                {
                    "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),  # LOINC
                    "code": VITAL_SIGNS_PANEL_CODE,
                    "display": VITAL_SIGNS_PANEL_DISPLAY,
                }
            ]
        }

        # 6. Subject (patient reference)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Observation panel without patient reference."
            )
        panel["subject"] = self.reference_registry.get_patient_reference()

        # 7. Effective time from organizer
        if organizer.effective_time:
            effective_time = self._extract_organizer_effective_time(organizer)
            if effective_time:
                panel["effectiveDateTime"] = effective_time

        # 8. Convert component observations to individual resources
        # First pass: convert all observations and detect BP and pulse oximetry components
        all_observations = []
        systolic_obs = None
        diastolic_obs = None
        pulse_ox_obs = None
        o2_flow_obs = None
        o2_concentration_obs = None

        if organizer.component:
            for component in organizer.component:
                if component.observation:
                    # Convert the component observation to a standalone resource
                    try:
                        individual = self.convert(component.observation, section=section)
                    except ValueError as e:
                        # Skip observations that can't be converted (e.g., nullFlavor codes without text)
                        # This handles real-world C-CDA documents with incomplete vital sign data
                        from ccda_to_fhir.logging_config import get_logger
                        logger = get_logger(__name__)
                        logger.warning(
                            f"Skipping vital sign component observation: {str(e)}"
                        )
                        continue

                    # Ensure it has an ID for referencing
                    if "id" not in individual:
                        # Generate ID if not present
                        if component.observation.id and len(component.observation.id) > 0:
                            obs_id = component.observation.id[0]
                            individual["id"] = self._generate_observation_id(
                                obs_id.root, obs_id.extension
                            )

                    # Check if this is a special vital sign requiring component handling
                    obs_code = self._get_observation_loinc_code(individual)

                    # Blood pressure components
                    if obs_code == BP_SYSTOLIC_CODE:
                        systolic_obs = individual
                    elif obs_code == BP_DIASTOLIC_CODE:
                        diastolic_obs = individual
                    # Pulse oximetry and O2 components
                    elif obs_code in (PULSE_OX_PRIMARY_CODE, PULSE_OX_ALT_CODE):
                        pulse_ox_obs = individual
                    elif obs_code == O2_FLOW_RATE_CODE:
                        o2_flow_obs = individual
                    elif obs_code == O2_CONCENTRATION_CODE:
                        o2_concentration_obs = individual
                    else:
                        # Not a special component, add to list
                        all_observations.append(individual)

        # 9. Combine BP observations if both systolic and diastolic found
        if systolic_obs and diastolic_obs:
            bp_combined = self._create_blood_pressure_observation(
                systolic_obs, diastolic_obs, status
            )
            all_observations.append(bp_combined)
        else:
            # Add individual BP observations if not both present
            if systolic_obs:
                all_observations.append(systolic_obs)
            if diastolic_obs:
                all_observations.append(diastolic_obs)

        # 10. Add O2 components to pulse oximetry if present
        if pulse_ox_obs:
            if o2_flow_obs or o2_concentration_obs:
                pulse_ox_with_components = self._add_pulse_ox_components(
                    pulse_ox_obs, o2_flow_obs, o2_concentration_obs
                )
                all_observations.append(pulse_ox_with_components)
            else:
                # Pulse ox without components
                all_observations.append(pulse_ox_obs)
        else:
            # Add O2 observations as standalone if no pulse ox found
            if o2_flow_obs:
                all_observations.append(o2_flow_obs)
            if o2_concentration_obs:
                all_observations.append(o2_concentration_obs)

        # 11. Build hasMember references
        has_member_refs = []
        for obs in all_observations:
            if "id" in obs:
                has_member_refs.append({
                    "reference": f"{FHIRCodes.ResourceTypes.OBSERVATION}/{obs['id']}"
                })

        if has_member_refs:
            panel["hasMember"] = has_member_refs

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=organizer, section=section)
        if narrative:
            panel["text"] = narrative

        # US Core STU6.1 Constraint us-core-2:
        # "If there is no component or hasMember element then either a value[x] or
        # a data absent reason must be present"
        # Panel observations with hasMember don't need value or dataAbsentReason
        # This check ensures compliance for any panel that somehow lacks hasMember
        has_value = any(k.startswith("value") for k in panel.keys())
        has_data_absent = "dataAbsentReason" in panel
        has_component = "component" in panel
        has_has_member = "hasMember" in panel

        if not (has_value or has_data_absent or has_component or has_has_member):
            # Panel should have hasMember but doesn't - add dataAbsentReason as fallback
            panel["dataAbsentReason"] = {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                    "code": "unknown",
                    "display": "Unknown"
                }],
                "text": "Value not provided in source C-CDA document"
            }

        return panel, all_observations

    def _generate_observation_id(
        self, root: str | None, extension: str | None
    ) -> str:
        """Generate a FHIR resource ID from C-CDA identifier.

        Uses standard ID generation with hashing for consistency across all converters.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A valid FHIR ID string
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="observation"
        )

    def _determine_status(self, observation: Observation) -> str:
        """Determine FHIR Observation status from C-CDA status code.

        Args:
            observation: The C-CDA Observation

        Returns:
            FHIR Observation status code
        """
        if not observation.status_code or not observation.status_code.code:
            return FHIRCodes.ObservationStatus.FINAL

        status_code = observation.status_code.code.lower()
        return OBSERVATION_STATUS_TO_FHIR.get(
            status_code, FHIRCodes.ObservationStatus.FINAL
        )

    def _determine_organizer_status(self, organizer: Organizer) -> str:
        """Determine FHIR Observation status from C-CDA organizer status code.

        Args:
            organizer: The C-CDA Organizer

        Returns:
            FHIR Observation status code
        """
        if not organizer.status_code or not organizer.status_code.code:
            return FHIRCodes.ObservationStatus.FINAL

        status_code = organizer.status_code.code.lower()
        return OBSERVATION_STATUS_TO_FHIR.get(
            status_code, FHIRCodes.ObservationStatus.FINAL
        )

    def _determine_category(self, observation: Observation) -> list[JSONObject] | None:
        """Determine observation categories based on template ID and observation code.

        For social history observations, this includes:
        1. Base category "social-history"
        2. Additional SDOH categories based on the observation's LOINC code

        Args:
            observation: The C-CDA Observation

        Returns:
            List of FHIR CodeableConcept for categories, or None
        """
        if not observation.template_id:
            return None

        categories: list[JSONObject] = []

        # Check template IDs to determine base category
        is_social_history = False
        for template in observation.template_id:
            if template.root == TemplateIds.VITAL_SIGN_OBSERVATION:
                categories.append({
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.VITAL_SIGNS,
                            "display": "Vital Signs",
                        }
                    ]
                })
                break
            elif template.root == TemplateIds.RESULT_OBSERVATION:
                categories.append({
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.LABORATORY,
                            "display": "Laboratory",
                        }
                    ]
                })
                break
            elif template.root in (
                TemplateIds.SMOKING_STATUS_OBSERVATION,
                TemplateIds.SOCIAL_HISTORY_OBSERVATION,
                TemplateIds.PREGNANCY_OBSERVATION,
            ):
                categories.append({
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.SOCIAL_HISTORY,
                            "display": "Social History",
                        }
                    ]
                })
                is_social_history = True
                break

        # For social history observations, add SDOH category based on LOINC code
        if is_social_history and observation.code:
            loinc_code = self._get_loinc_code_from_cd(observation.code)
            if loinc_code and loinc_code in LOINC_TO_SDOH_CATEGORY:
                sdoh_category_code = LOINC_TO_SDOH_CATEGORY[loinc_code]
                sdoh_display = SDOH_CATEGORY_DISPLAY.get(sdoh_category_code, sdoh_category_code)
                categories.append({
                    "coding": [
                        {
                            "system": FHIRSystems.SDOH_CATEGORY,
                            "code": sdoh_category_code,
                            "display": sdoh_display,
                        }
                    ]
                })

        return categories if categories else None

    def _determine_us_core_profile(
        self, categories: list[JSONObject] | None, observation: Observation
    ) -> str | None:
        """Determine appropriate US Core profile based on observation category and code.

        Args:
            categories: FHIR categories assigned to this observation
            observation: The C-CDA Observation

        Returns:
            US Core profile URL, or None
        """
        if not categories:
            # Default to clinical result if no category
            return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"

        # Check category codes to determine profile
        for category in categories:
            if "coding" in category:
                for coding in category["coding"]:
                    code = coding.get("code")

                    # Vital signs
                    if code == "vital-signs":
                        return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs"

                    # Laboratory
                    if code == "laboratory":
                        return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab"

                    # Social history - check for smoking status
                    if code == "social-history":
                        # Check if this is smoking status (LOINC 72166-2)
                        if observation.code:
                            loinc_code = self._get_loinc_code_from_cd(observation.code)
                            if loinc_code == "72166-2":
                                return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-smokingstatus"
                        # SDOH assessment
                        return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-sdoh-assessment"

        # Default to clinical result
        return "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-clinical-result"

    def _get_loinc_code_from_cd(self, code: CD | CE | None) -> str | None:
        """Extract LOINC code from a CD/CE element.

        Args:
            code: The C-CDA CD or CE code element

        Returns:
            LOINC code string, or None if not a LOINC code
        """
        if not code:
            return None

        # Check if this is a LOINC code (codeSystem = 2.16.840.1.113883.6.1)
        if code.code_system == "2.16.840.1.113883.6.1" and code.code:
            return code.code

        return None

    def _convert_code_to_codeable_concept(
        self, code: CD | CE | CS
    ) -> JSONObject | None:
        """Convert C-CDA CD/CE/CS to FHIR CodeableConcept.

        Args:
            code: The C-CDA code element

        Returns:
            FHIR CodeableConcept or None
        """
        if not code:
            return None

        codings = []

        # Primary coding
        if code.code and code.code_system:
            system_uri = self.map_oid_to_uri(code.code_system)
            coding: JSONObject = {
                "system": system_uri,
                "code": code.code,
            }
            if code.display_name:
                coding["display"] = code.display_name
            else:
                # Look up display from terminology maps
                looked_up_display = get_display_for_code(system_uri, code.code)
                if looked_up_display:
                    coding["display"] = looked_up_display
            codings.append(coding)

        # Translations
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if trans.code and trans.code_system:
                    trans_system_uri = self.map_oid_to_uri(trans.code_system)
                    trans_coding: JSONObject = {
                        "system": trans_system_uri,
                        "code": trans.code,
                    }
                    if trans.display_name:
                        trans_coding["display"] = trans.display_name
                    else:
                        # Look up display from terminology maps
                        looked_up_display = get_display_for_code(trans_system_uri, trans.code)
                        if looked_up_display:
                            trans_coding["display"] = looked_up_display
                    codings.append(trans_coding)

        if not codings:
            return None

        codeable_concept: JSONObject = {"coding": codings}

        # Original text
        if hasattr(code, "original_text") and code.original_text:
            # original_text is ED (Encapsulated Data)
            if hasattr(code.original_text, "text") and code.original_text.text:
                codeable_concept["text"] = code.original_text.text

        return codeable_concept

    def _convert_body_site_with_qualifiers(
        self, code: CD | CE
    ) -> JSONObject | None:
        """Convert C-CDA targetSiteCode with qualifiers to FHIR bodySite CodeableConcept.

        This method handles body site codes with laterality qualifiers. Per C-CDA standard,
        laterality (left/right) can be specified using qualifier elements within targetSiteCode.

        Example C-CDA:
            <targetSiteCode code="40983000" displayName="Upper arm structure"
                           codeSystem="2.16.840.1.113883.6.96">
              <qualifier>
                <name code="272741003" displayName="Laterality"
                      codeSystem="2.16.840.1.113883.6.96"/>
                <value code="7771000" displayName="Left"
                       codeSystem="2.16.840.1.113883.6.96"/>
              </qualifier>
            </targetSiteCode>

        Args:
            code: The C-CDA targetSiteCode element (CD or CE type)

        Returns:
            FHIR CodeableConcept with bodySite and laterality coding, or None
        """
        if not code:
            return None

        # Start with basic code conversion
        codeable_concept = self._convert_code_to_codeable_concept(code)
        if not codeable_concept:
            return None

        # Check for laterality qualifiers
        # Per C-CDA: laterality is specified using qualifier with name code 272741003 or 78615007
        laterality_qualifier_codes = ["272741003", "78615007"]  # "Laterality" and "with laterality"
        laterality_value = None

        if hasattr(code, "qualifier") and code.qualifier:
            for qualifier in code.qualifier:
                # Check if this is a laterality qualifier
                if qualifier.name and qualifier.name.code in laterality_qualifier_codes:
                    if qualifier.value and qualifier.value.code and qualifier.value.code_system:
                        laterality_value = qualifier.value
                        break

        # If we found a laterality qualifier, add it as additional coding
        if laterality_value:
            laterality_coding: JSONObject = {
                "system": self.map_oid_to_uri(laterality_value.code_system),
                "code": laterality_value.code,
            }
            if laterality_value.display_name:
                laterality_coding["display"] = laterality_value.display_name

            # Add laterality as additional coding
            if "coding" not in codeable_concept:
                codeable_concept["coding"] = []
            codeable_concept["coding"].append(laterality_coding)

            # Update text to include laterality for human readability
            # Format: "{laterality} {site}" (e.g., "Left Upper arm structure")
            if laterality_value.display_name and code.display_name:
                codeable_concept["text"] = f"{laterality_value.display_name} {code.display_name}"
            elif laterality_value.display_name and "text" in codeable_concept:
                codeable_concept["text"] = f"{laterality_value.display_name} {codeable_concept['text']}"

        return codeable_concept

    def _extract_effective_time(self, observation: Observation) -> str | JSONObject | None:
        """Extract and convert effective time to FHIR format.

        Per FHIR R4 and C-CDA on FHIR IG specifications:
        - If IVL_TS has both low AND high → effectivePeriod (Period with start and end)
        - If IVL_TS has only low → effectiveDateTime (single point in time)
        - If TS (single value) → effectiveDateTime (single point in time)

        Args:
            observation: The C-CDA Observation

        Returns:
            FHIR formatted datetime string (for effectiveDateTime),
            or dict with start/end (for effectivePeriod),
            or None
        """
        if not observation.effective_time:
            return None

        # Handle IVL_TS (interval)
        if hasattr(observation.effective_time, "low") or hasattr(observation.effective_time, "high"):
            has_low = hasattr(observation.effective_time, "low") and observation.effective_time.low
            has_high = hasattr(observation.effective_time, "high") and observation.effective_time.high

            # Case 1: Both low and high present → effectivePeriod
            if has_low and has_high:
                period: JSONObject = {}

                # Extract start from low
                if hasattr(observation.effective_time.low, "value"):
                    start_date = self.convert_date(observation.effective_time.low.value)
                    if start_date:
                        period["start"] = start_date

                # Extract end from high
                if hasattr(observation.effective_time.high, "value"):
                    end_date = self.convert_date(observation.effective_time.high.value)
                    if end_date:
                        period["end"] = end_date

                # Return period if at least one boundary is present
                if period:
                    return period

            # Case 2: Only low present → effectiveDateTime (use start date)
            elif has_low:
                if hasattr(observation.effective_time.low, "value"):
                    return self.convert_date(observation.effective_time.low.value)

        # Handle TS (single time point)
        if hasattr(observation.effective_time, "value") and observation.effective_time.value:
            return self.convert_date(observation.effective_time.value)

        return None

    def _extract_organizer_effective_time(self, organizer: Organizer) -> str | None:
        """Extract and convert organizer effective time to FHIR format.

        Args:
            organizer: The C-CDA Organizer

        Returns:
            FHIR formatted datetime string or None
        """
        if not organizer.effective_time:
            return None

        # Handle IVL_TS (interval) - use low if available
        if hasattr(organizer.effective_time, "low") and organizer.effective_time.low:
            if hasattr(organizer.effective_time.low, "value"):
                return self.convert_date(organizer.effective_time.low.value)

        # Handle TS (single time point)
        if hasattr(organizer.effective_time, "value") and organizer.effective_time.value:
            return self.convert_date(organizer.effective_time.value)

        return None

    def _map_null_flavor_to_data_absent_reason(self, null_flavor: str) -> str:
        """Map C-CDA nullFlavor to FHIR DataAbsentReason code.

        Args:
            null_flavor: C-CDA nullFlavor code (e.g., "UNK", "NA", "ASKU")

        Returns:
            FHIR DataAbsentReason code (e.g., "unknown", "not-applicable", "asked-unknown")
        """
        from ccda_to_fhir.constants import NULL_FLAVOR_TO_DATA_ABSENT_REASON

        # Case-insensitive lookup
        return NULL_FLAVOR_TO_DATA_ABSENT_REASON.get(
            null_flavor.upper() if null_flavor else None, "unknown"
        )

    def _convert_value(self, observation: Observation) -> JSONObject | None:
        """Convert observation value to appropriate FHIR value[x] element.

        Args:
            observation: The C-CDA Observation

        Returns:
            Dictionary with value element (e.g., {"valueQuantity": {...}}) or None
        """
        if not observation.value:
            return None

        # Handle PQ (Physical Quantity) → valueQuantity
        if isinstance(observation.value, PQ):
            return self._convert_pq_to_value_quantity(observation.value)

        # Handle IVL_PQ (Interval Physical Quantity) → valueRange
        if isinstance(observation.value, IVL_PQ):
            return self._convert_ivl_pq_to_value_range(observation.value)

        # Handle CD/CE (Coded values) → valueCodeableConcept
        if isinstance(observation.value, (CD, CE)):
            codeable_concept = self._convert_code_to_codeable_concept(observation.value)
            if codeable_concept:
                return {"valueCodeableConcept": codeable_concept}

        # Handle ST (String) → valueString
        if isinstance(observation.value, ST):
            if hasattr(observation.value, "text") and observation.value.text:
                return {"valueString": observation.value.text}
            elif hasattr(observation.value, "value") and observation.value.value:
                return {"valueString": observation.value.value}

        # Handle ED (Encapsulated Data) → extension with valueAttachment
        if isinstance(observation.value, ED):
            return self._convert_ed_to_value_attachment(observation.value)

        # Handle INT (Integer) → valueInteger
        if isinstance(observation.value, INT):
            if observation.value.value is not None:
                return {"valueInteger": observation.value.value}

        # Handle other types as needed (REAL, BL, etc.)
        # For now, return None for unsupported types
        return None

    def _convert_pq_to_value_quantity(self, pq: PQ) -> JSONObject:
        """Convert C-CDA PQ to FHIR valueQuantity.

        Args:
            pq: The C-CDA Physical Quantity

        Returns:
            Dictionary with valueQuantity element
        """
        quantity: JSONObject = {}

        # Handle value (may be string from parser)
        if pq.value is not None:
            if isinstance(pq.value, str):
                # Try to convert to numeric
                try:
                    if "." in pq.value:
                        quantity["value"] = float(pq.value)
                    else:
                        quantity["value"] = int(pq.value)
                except (ValueError, TypeError):
                    # If conversion fails, use as string
                    quantity["value"] = pq.value
            else:
                quantity["value"] = pq.value

        # Add unit
        if pq.unit:
            quantity["unit"] = pq.unit
            quantity["system"] = FHIRSystems.UCUM
            quantity["code"] = pq.unit

        return {"valueQuantity": quantity}

    def _convert_ivl_pq_to_value_range(self, ivl_pq: IVL_PQ) -> JSONObject:
        """Convert C-CDA IVL_PQ to FHIR valueRange or valueQuantity with comparator.

        When both low and high are present → valueRange
        When only one boundary is present → valueQuantity with comparator
        (Assumes inclusive=true by default per C-CDA spec)

        Args:
            ivl_pq: The C-CDA Interval Physical Quantity

        Returns:
            Dictionary with valueRange or valueQuantity element
        """
        has_low = ivl_pq.low is not None
        has_high = ivl_pq.high is not None

        # Case 1: Both boundaries → valueRange
        if has_low and has_high:
            range_val: JSONObject = {}
            if ivl_pq.low:
                low = self._pq_to_simple_quantity(ivl_pq.low)
                if low:
                    range_val["low"] = low
            if ivl_pq.high:
                high = self._pq_to_simple_quantity(ivl_pq.high)
                if high:
                    range_val["high"] = high
            return {"valueRange": range_val} if range_val else {}

        # Case 2: Only high → valueQuantity with comparator "<="
        if has_high and not has_low:
            quantity = self._pq_to_simple_quantity(ivl_pq.high)
            if quantity:
                quantity["comparator"] = "<="
                return {"valueQuantity": quantity}

        # Case 3: Only low → valueQuantity with comparator ">="
        if has_low and not has_high:
            quantity = self._pq_to_simple_quantity(ivl_pq.low)
            if quantity:
                quantity["comparator"] = ">="
                return {"valueQuantity": quantity}

        return {}

    def _convert_ed_to_value_attachment(self, ed: ED) -> JSONObject:
        """Convert C-CDA ED to FHIR valueAttachment extension.

        FHIR R4 does not support valueAttachment as a value[x] type. This was added in R5.
        To represent ED type observations in R4, we use the R5 backport extension.

        Per C-CDA on FHIR IG:
        - ED (Encapsulated Data) → extension with valueAttachment
        - Extension URL: http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value

        Args:
            ed: The C-CDA Encapsulated Data

        Returns:
            Dictionary with extension containing valueAttachment

        References:
            - https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html
            - https://build.fhir.org/ig/HL7/CDA-core-2.0/StructureDefinition-ED.html
        """
        import base64

        attachment: JSONObject = {}

        # Content type from mediaType attribute (required if data present)
        if hasattr(ed, "media_type") and ed.media_type:
            attachment["contentType"] = ed.media_type
        else:
            # Default to application/octet-stream for binary data
            attachment["contentType"] = "application/octet-stream"

        # Language
        if hasattr(ed, "language") and ed.language:
            attachment["language"] = ed.language

        # Data - base64 encoded content
        # In C-CDA, ED can have:
        # 1. Base64 encoded data (representation="B64")
        # 2. Plain text content
        # Note: ED model stores text in 'value' attribute
        has_data = False
        if hasattr(ed, "representation") and ed.representation == "B64":
            # Already base64 encoded
            if hasattr(ed, "value") and ed.value:
                # Remove whitespace from base64 data
                attachment["data"] = ed.value.replace("\n", "").replace(" ", "").strip()
                has_data = True
        elif hasattr(ed, "value") and ed.value:
            # Plain text or other content - need to base64 encode it
            text_bytes = ed.value.encode("utf-8")
            attachment["data"] = base64.b64encode(text_bytes).decode("ascii")
            has_data = True

        # Only create extension if we have data
        if not has_data:
            return {}

        # Create extension with R5 backport URL
        extension = {
            "extension": [
                {
                    "url": "http://hl7.org/fhir/5.0/StructureDefinition/extension-Observation.value",
                    "valueAttachment": attachment,
                }
            ]
        }

        return extension

    def _convert_reference_range(self, observation_range) -> JSONObject | None:
        """Convert C-CDA observation range to FHIR referenceRange.

        Args:
            observation_range: The C-CDA ObservationRange object

        Returns:
            FHIR referenceRange element or None
        """
        if not observation_range or not observation_range.value:
            return None

        ref_range: JSONObject = {}

        # Handle IVL_PQ (interval of physical quantities)
        value = observation_range.value
        if isinstance(value, IVL_PQ):
            if value.low:
                low_quantity = self._pq_to_simple_quantity(value.low)
                if low_quantity:
                    ref_range["low"] = low_quantity

            if value.high:
                high_quantity = self._pq_to_simple_quantity(value.high)
                if high_quantity:
                    ref_range["high"] = high_quantity

        # Add text if present
        if observation_range.text:
            # Extract text content from ED (encapsulated data) type
            # ED.value is aliased from _text in the XML
            if hasattr(observation_range.text, 'value') and observation_range.text.value:
                ref_range["text"] = observation_range.text.value

        if ref_range:
            return ref_range

        return None

    def _pq_to_simple_quantity(self, pq: PQ) -> JSONObject | None:
        """Convert PQ to a simple quantity (for reference ranges).

        Args:
            pq: The C-CDA Physical Quantity

        Returns:
            FHIR Quantity or None
        """
        if not pq or pq.value is None:
            return None

        quantity: JSONObject = {}

        # Convert value to numeric
        if isinstance(pq.value, str):
            try:
                if "." in pq.value:
                    quantity["value"] = float(pq.value)
                else:
                    quantity["value"] = int(pq.value)
            except (ValueError, TypeError):
                quantity["value"] = pq.value
        else:
            quantity["value"] = pq.value

        # Add unit and UCUM system
        # Per FHIR R4 qty-3: system SHALL be present if code is present
        # For unitless quantities, omit both system and code
        if pq.unit:
            quantity["unit"] = pq.unit
            quantity["system"] = FHIRSystems.UCUM
            quantity["code"] = pq.unit

        return quantity

    def _get_observation_loinc_code(self, observation: JSONObject) -> str | None:
        """Extract LOINC code from an observation resource.

        Args:
            observation: FHIR Observation resource

        Returns:
            LOINC code string or None
        """
        code = observation.get("code", {})
        for coding in code.get("coding", []):
            system = coding.get("system", "")
            if "loinc.org" in system:
                return coding.get("code")
        return None

    def _handle_pregnancy_observation(self, observation: Observation, fhir_obs: JSONObject) -> None:
        """Handle pregnancy observation-specific conversions.

        Per C-CDA on FHIR specification and C-CDA R2.1 Supplemental Templates:
        1. Transform code from ASSERTION (pre-C-CDA 4.0) to LOINC 82810-3 if needed
        2. Extract pregnancy-related observations from entryRelationship as components:
           - Estimated delivery date (11778-8)
           - Last menstrual period (8665-2)
           - Gestational age (11884-4, 11885-1, 18185-9, 49051-6, etc.)

        Args:
            observation: The C-CDA Observation (Pregnancy Observation template)
            fhir_obs: The FHIR Observation being built (modified in place)

        References:
            - https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-social.html
            - C-CDA R2.1 Supplemental Templates for Pregnancy
        """
        # 1. Fix code if pre-C-CDA 4.0 (ASSERTION → 82810-3)
        # Per spec: Prior to C-CDA 4.0, uses ASSERTION; version 4.0+ uses 82810-3
        if observation.code:
            if observation.code.code == "ASSERTION":
                fhir_obs["code"] = {
                    "coding": [{
                        "system": "http://loinc.org",
                        "code": "82810-3",
                        "display": "Pregnancy status"
                    }]
                }

        # 2. Extract pregnancy-related observations from entryRelationship
        # Maps to components following the pattern established for EDD
        if observation.entry_relationship:
            for rel in observation.entry_relationship:
                if rel.observation and rel.observation.code:
                    code = rel.observation.code.code

                    # Define pregnancy-related LOINC codes and their metadata
                    # Date-type observations
                    date_codes = {
                        "11778-8": "Delivery date Estimated",
                        "8665-2": "Last menstrual period start date"
                    }

                    # Quantity-type observations (gestational age)
                    quantity_codes = {
                        "11884-4": "Gestational age Estimated",
                        "11885-1": "Gestational age Estimated from last menstrual period",
                        "18185-9": "Gestational age",
                        "49051-6": "Gestational age in weeks",
                        "49052-4": "Gestational age in days",
                        "57714-8": "Obstetric estimation of gestational age",
                        "11887-7": "Gestational age Estimated from selected delivery date",
                        "11886-9": "Gestational age Estimated from ovulation date",
                        "53693-8": "Gestational age Estimated from conception date"
                    }

                    # Handle date-type observations (EDD, LMP)
                    if code in date_codes:
                        # Initialize component array if not exists
                        if "component" not in fhir_obs:
                            fhir_obs["component"] = []

                        # Create component
                        component: JSONObject = {
                            "code": {
                                "coding": [{
                                    "system": "http://loinc.org",
                                    "code": code,
                                    "display": date_codes[code]
                                }]
                            }
                        }

                        # Extract value (TS type in C-CDA)
                        if rel.observation.value and hasattr(rel.observation.value, 'value'):
                            date_str = rel.observation.value.value
                            # Handle ISO format dates (YYYY-MM-DD) which may appear in C-CDA
                            if date_str and '-' in date_str:
                                # Already in ISO format, use directly
                                component["valueDateTime"] = date_str
                            else:
                                # Convert from C-CDA format (YYYYMMDD or YYYYMMDDHHMMSS)
                                value_date = self.convert_date(date_str)
                                if value_date:
                                    component["valueDateTime"] = value_date

                        fhir_obs["component"].append(component)

                    # Handle quantity-type observations (gestational age)
                    elif code in quantity_codes:
                        # Initialize component array if not exists
                        if "component" not in fhir_obs:
                            fhir_obs["component"] = []

                        # Create component
                        component: JSONObject = {
                            "code": {
                                "coding": [{
                                    "system": "http://loinc.org",
                                    "code": code,
                                    "display": quantity_codes[code]
                                }]
                            }
                        }

                        # Extract value (PQ type in C-CDA)
                        if rel.observation.value:
                            if hasattr(rel.observation.value, 'value') and hasattr(rel.observation.value, 'unit'):
                                value_quantity: JSONObject = {
                                    "value": float(rel.observation.value.value)
                                }

                                # Add unit if present
                                if rel.observation.value.unit:
                                    value_quantity["unit"] = rel.observation.value.unit
                                    # Map common UCUM units
                                    if rel.observation.value.unit.lower() in ("wk", "weeks", "week"):
                                        value_quantity["system"] = "http://unitsofmeasure.org"
                                        value_quantity["code"] = "wk"
                                    elif rel.observation.value.unit.lower() in ("d", "days", "day"):
                                        value_quantity["system"] = "http://unitsofmeasure.org"
                                        value_quantity["code"] = "d"

                                component["valueQuantity"] = value_quantity
                            elif hasattr(rel.observation.value, 'value'):
                                # Value without unit (assume weeks for gestational age)
                                component["valueQuantity"] = {
                                    "value": float(rel.observation.value.value),
                                    "unit": "wk",
                                    "system": "http://unitsofmeasure.org",
                                    "code": "wk"
                                }

                        fhir_obs["component"].append(component)

    def _create_blood_pressure_observation(
        self,
        systolic_obs: JSONObject,
        diastolic_obs: JSONObject,
        status: str
    ) -> JSONObject:
        """Create a combined blood pressure observation with components.

        Args:
            systolic_obs: Systolic BP observation
            diastolic_obs: Diastolic BP observation
            status: Observation status

        Returns:
            Combined BP observation with components
        """
        # Generate ID from systolic observation (use first BP component's ID as base)
        if "id" not in systolic_obs:
            raise ValueError(
                "Cannot create blood pressure panel: systolic observation missing ID. "
                "This should not occur if observations are properly converted."
            )

        bp_id = systolic_obs["id"]
        if "-" in bp_id:
            # If ID has a suffix, use base part
            bp_id = bp_id.rsplit("-", 1)[0] + "-bp"
        else:
            bp_id = bp_id + "-bp"

        bp_obs: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
            "id": bp_id,
            "status": status,
        }

        # Identifier - use from systolic observation
        if "identifier" in systolic_obs:
            bp_obs["identifier"] = systolic_obs["identifier"]

        # Category - vital-signs
        bp_obs["category"] = [
            {
                "coding": [
                    {
                        "system": FHIRSystems.OBSERVATION_CATEGORY,
                        "code": FHIRCodes.ObservationCategory.VITAL_SIGNS,
                        "display": "Vital Signs",
                    }
                ]
            }
        ]

        # Code - BP panel
        bp_obs["code"] = {
            "coding": [
                {
                    "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),  # LOINC
                    "code": BP_PANEL_CODE,
                    "display": BP_PANEL_DISPLAY,
                }
            ]
        }

        # Subject
        if "subject" in systolic_obs:
            bp_obs["subject"] = systolic_obs["subject"]
        elif self.reference_registry:
            bp_obs["subject"] = self.reference_registry.get_patient_reference()
        else:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create blood pressure Observation without patient reference."
            )

        # Effective time (use from systolic or diastolic)
        effective_time = systolic_obs.get("effectiveDateTime") or diastolic_obs.get("effectiveDateTime")
        if effective_time:
            bp_obs["effectiveDateTime"] = effective_time

        # Body site (use from systolic, or diastolic if systolic doesn't have it)
        body_site = systolic_obs.get("bodySite") or diastolic_obs.get("bodySite")
        if body_site:
            bp_obs["bodySite"] = body_site

        # Interpretation (use from systolic, or diastolic if systolic doesn't have it)
        interpretation = systolic_obs.get("interpretation") or diastolic_obs.get("interpretation")
        if interpretation:
            bp_obs["interpretation"] = interpretation

        # Reference ranges (combine from systolic and diastolic if present)
        # Per FHIR spec: referenceRange describes normal range for the observation
        # For BP panel, we include both systolic and diastolic reference ranges
        reference_ranges = []
        if "referenceRange" in systolic_obs:
            for ref_range in systolic_obs["referenceRange"]:
                # Add context to indicate this is for systolic component
                ref_range_with_type = ref_range.copy()
                if "text" in ref_range_with_type:
                    ref_range_with_type["text"] = f"Systolic: {ref_range_with_type['text']}"
                else:
                    ref_range_with_type["text"] = "Systolic blood pressure"
                reference_ranges.append(ref_range_with_type)

        if "referenceRange" in diastolic_obs:
            for ref_range in diastolic_obs["referenceRange"]:
                # Add context to indicate this is for diastolic component
                ref_range_with_type = ref_range.copy()
                if "text" in ref_range_with_type:
                    ref_range_with_type["text"] = f"Diastolic: {ref_range_with_type['text']}"
                else:
                    ref_range_with_type["text"] = "Diastolic blood pressure"
                reference_ranges.append(ref_range_with_type)

        if reference_ranges:
            bp_obs["referenceRange"] = reference_ranges

        # Components
        components = []

        # Systolic component
        if "valueQuantity" in systolic_obs:
            systolic_component: JSONObject = {
                "code": {
                    "coding": [
                        {
                            "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),
                            "code": BP_SYSTOLIC_CODE,
                            "display": BP_SYSTOLIC_DISPLAY,
                        }
                    ]
                },
                "valueQuantity": systolic_obs["valueQuantity"]
            }
            # Preserve interpretation from original observation
            if "interpretation" in systolic_obs:
                systolic_component["interpretation"] = systolic_obs["interpretation"]
            components.append(systolic_component)

        # Diastolic component
        if "valueQuantity" in diastolic_obs:
            diastolic_component: JSONObject = {
                "code": {
                    "coding": [
                        {
                            "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),
                            "code": BP_DIASTOLIC_CODE,
                            "display": BP_DIASTOLIC_DISPLAY,
                        }
                    ]
                },
                "valueQuantity": diastolic_obs["valueQuantity"]
            }
            # Preserve interpretation from original observation
            if "interpretation" in diastolic_obs:
                diastolic_component["interpretation"] = diastolic_obs["interpretation"]
            components.append(diastolic_component)

        if components:
            bp_obs["component"] = components

        return bp_obs

    def _add_pulse_ox_components(
        self,
        pulse_ox_obs: JSONObject,
        o2_flow_obs: JSONObject | None,
        o2_concentration_obs: JSONObject | None
    ) -> JSONObject:
        """Add O2 flow rate and/or concentration as components to pulse oximetry observation.

        Args:
            pulse_ox_obs: Pulse oximetry observation
            o2_flow_obs: Optional O2 flow rate observation
            o2_concentration_obs: Optional O2 concentration observation

        Returns:
            Pulse oximetry observation with components added
        """
        components = []

        # O2 flow rate component
        if o2_flow_obs and "valueQuantity" in o2_flow_obs:
            components.append({
                "code": {
                    "coding": [
                        {
                            "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),
                            "code": O2_FLOW_RATE_CODE,
                            "display": O2_FLOW_RATE_DISPLAY,
                        }
                    ]
                },
                "valueQuantity": o2_flow_obs["valueQuantity"]
            })

        # O2 concentration component
        if o2_concentration_obs and "valueQuantity" in o2_concentration_obs:
            components.append({
                "code": {
                    "coding": [
                        {
                            "system": self.map_oid_to_uri("2.16.840.1.113883.6.1"),
                            "code": O2_CONCENTRATION_CODE,
                            "display": O2_CONCENTRATION_DISPLAY,
                        }
                    ]
                },
                "valueQuantity": o2_concentration_obs["valueQuantity"]
            })

        if components:
            pulse_ox_obs["component"] = components

        # Reference ranges (pulse ox observation already has its own, no need to merge from components)
        # The main pulse oximetry observation's reference range is preserved from the original convert()
        # O2 flow and concentration reference ranges are not typically included in FHIR pulse ox panels

        return pulse_ox_obs

    def _generate_practitioner_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Practitioner ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Practitioner", root, extension)
