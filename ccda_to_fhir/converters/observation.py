"""Observation converter: C-CDA Observation to FHIR Observation resource."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, IVL_PQ, PQ, ST
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.constants import (
    BP_DIASTOLIC_CODE,
    BP_DIASTOLIC_DISPLAY,
    BP_PANEL_CODE,
    BP_PANEL_DISPLAY,
    BP_SYSTOLIC_CODE,
    BP_SYSTOLIC_DISPLAY,
    FHIRCodes,
    FHIRSystems,
    O2_CONCENTRATION_CODE,
    O2_CONCENTRATION_DISPLAY,
    O2_FLOW_RATE_CODE,
    O2_FLOW_RATE_DISPLAY,
    OBSERVATION_STATUS_TO_FHIR,
    PULSE_OX_ALT_CODE,
    PULSE_OX_PRIMARY_CODE,
    TemplateIds,
    VITAL_SIGNS_PANEL_CODE,
    VITAL_SIGNS_PANEL_DISPLAY,
)

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
        fhir_obs: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
        }

        # 1. Generate ID from observation identifier
        if observation.id and len(observation.id) > 0:
            first_id = observation.id[0]
            fhir_obs["id"] = self._generate_observation_id(
                first_id.root, first_id.extension
            )

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

        # 4. Category - determine based on template ID
        category = self._determine_category(observation)
        if category:
            fhir_obs["category"] = [category]

        # 5. Code (required) - observation type code
        if observation.code:
            code_cc = self._convert_code_to_codeable_concept(observation.code)
            if code_cc:
                fhir_obs["code"] = code_cc

        # 6. Subject (patient reference)
        fhir_obs["subject"] = {
            "reference": f"{FHIRCodes.ResourceTypes.PATIENT}/patient-placeholder"
        }

        # 7. Effective time
        effective_time = self._extract_effective_time(observation)
        if effective_time:
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

        # 10. Reference ranges
        if observation.reference_range:
            ref_ranges = []
            for ref_range in observation.reference_range:
                if ref_range.observation_range and ref_range.observation_range.value:
                    fhir_ref_range = self._convert_reference_range(ref_range.observation_range.value)
                    if fhir_ref_range:
                        ref_ranges.append(fhir_ref_range)
            if ref_ranges:
                fhir_obs["referenceRange"] = ref_ranges

        # 11. Pregnancy observation special handling
        if observation.template_id:
            from ccda_to_fhir.constants import TemplateIds
            is_pregnancy = any(
                t.root == TemplateIds.PREGNANCY_OBSERVATION
                for t in observation.template_id
                if t.root
            )
            if is_pregnancy:
                self._handle_pregnancy_observation(observation, fhir_obs)

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=observation, section=section)
        if narrative:
            fhir_obs["text"] = narrative

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
            first_id = organizer.id[0]
            panel_id = self._generate_observation_id(first_id.root, first_id.extension)
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
        panel["subject"] = {
            "reference": f"{FHIRCodes.ResourceTypes.PATIENT}/patient-placeholder"
        }

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
                    individual = self.convert(component.observation, section=section)

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

        return panel, all_observations

    def _generate_observation_id(
        self, root: str | None, extension: str | None
    ) -> str:
        """Generate a FHIR resource ID from C-CDA identifier.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A valid FHIR ID string
        """
        if extension:
            # Use extension as ID (removing any invalid characters)
            return extension.replace(".", "-").replace(":", "-")
        elif root:
            # Use root as ID
            return root.replace(".", "-").replace(":", "-")
        else:
            return "observation-unknown"

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

    def _determine_category(self, observation: Observation) -> JSONObject | None:
        """Determine observation category based on template ID.

        Args:
            observation: The C-CDA Observation

        Returns:
            FHIR CodeableConcept for category, or None
        """
        if not observation.template_id:
            return None

        # Check template IDs to determine category
        for template in observation.template_id:
            if template.root == TemplateIds.VITAL_SIGN_OBSERVATION:
                return {
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.VITAL_SIGNS,
                            "display": "Vital Signs",
                        }
                    ]
                }
            elif template.root == TemplateIds.RESULT_OBSERVATION:
                return {
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.LABORATORY,
                            "display": "Laboratory",
                        }
                    ]
                }
            elif template.root in (
                TemplateIds.SMOKING_STATUS_OBSERVATION,
                TemplateIds.SOCIAL_HISTORY_OBSERVATION,
                TemplateIds.PREGNANCY_OBSERVATION,
            ):
                return {
                    "coding": [
                        {
                            "system": FHIRSystems.OBSERVATION_CATEGORY,
                            "code": FHIRCodes.ObservationCategory.SOCIAL_HISTORY,
                            "display": "Social History",
                        }
                    ]
                }

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
            coding: JSONObject = {
                "system": self.map_oid_to_uri(code.code_system),
                "code": code.code,
            }
            if code.display_name:
                coding["display"] = code.display_name
            codings.append(coding)

        # Translations
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if trans.code and trans.code_system:
                    trans_coding: JSONObject = {
                        "system": self.map_oid_to_uri(trans.code_system),
                        "code": trans.code,
                    }
                    if trans.display_name:
                        trans_coding["display"] = trans.display_name
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

    def _extract_effective_time(self, observation: Observation) -> str | None:
        """Extract and convert effective time to FHIR format.

        Args:
            observation: The C-CDA Observation

        Returns:
            FHIR formatted datetime string or None
        """
        if not observation.effective_time:
            return None

        # Handle IVL_TS (interval)
        if hasattr(observation.effective_time, "low") and observation.effective_time.low:
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

        # Handle other types as needed (INT, REAL, BL, etc.)
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

    def _convert_reference_range(self, value) -> JSONObject | None:
        """Convert C-CDA reference range value to FHIR referenceRange.

        Args:
            value: The C-CDA reference range value (typically IVL_PQ)

        Returns:
            FHIR referenceRange element or None
        """
        if not value:
            return None

        ref_range: JSONObject = {}

        # Handle IVL_PQ (interval of physical quantities)
        if isinstance(value, IVL_PQ):
            if value.low:
                low_quantity = self._pq_to_simple_quantity(value.low)
                if low_quantity:
                    ref_range["low"] = low_quantity

            if value.high:
                high_quantity = self._pq_to_simple_quantity(value.high)
                if high_quantity:
                    ref_range["high"] = high_quantity

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

        # Add unit
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

        Per C-CDA on FHIR specification:
        1. Transform code from ASSERTION (pre-C-CDA 4.0) to LOINC 82810-3 if needed
        2. Extract estimated delivery date from entryRelationship
        3. Add EDD as component with code 11778-8

        Args:
            observation: The C-CDA Observation (Pregnancy Observation template)
            fhir_obs: The FHIR Observation being built (modified in place)

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-social.html
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

        # 2. Extract estimated delivery date from entryRelationship
        # Maps to component with code 11778-8
        if observation.entry_relationship:
            for rel in observation.entry_relationship:
                if rel.observation and rel.observation.code:
                    # Check for Estimated Delivery Date (code 11778-8)
                    if rel.observation.code.code == "11778-8":
                        # Initialize component array if not exists
                        if "component" not in fhir_obs:
                            fhir_obs["component"] = []

                        # Create EDD component
                        component: JSONObject = {
                            "code": {
                                "coding": [{
                                    "system": "http://loinc.org",
                                    "code": "11778-8",
                                    "display": "Delivery date Estimated"
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
        bp_id = systolic_obs.get("id", "bp-unknown")
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
        bp_obs["subject"] = systolic_obs.get("subject", {
            "reference": f"{FHIRCodes.ResourceTypes.PATIENT}/patient-placeholder"
        })

        # Effective time (use from systolic or diastolic)
        effective_time = systolic_obs.get("effectiveDateTime") or diastolic_obs.get("effectiveDateTime")
        if effective_time:
            bp_obs["effectiveDateTime"] = effective_time

        # Components
        components = []

        # Systolic component
        if "valueQuantity" in systolic_obs:
            components.append({
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
            })

        # Diastolic component
        if "valueQuantity" in diastolic_obs:
            components.append({
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
            })

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

        return pulse_ox_obs
