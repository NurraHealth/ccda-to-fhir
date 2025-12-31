"""Encounter converter: C-CDA Encounter Activity to FHIR Encounter resource."""

from __future__ import annotations

import logging

from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.ccda.models.observation import EntryRelationship
from ccda_to_fhir.constants import (
    CPT_CODE_SYSTEM,
    DISCHARGE_DISPOSITION_TO_FHIR,
    ENCOUNTER_STATUS_TO_FHIR,
    PARTICIPATION_FUNCTION_CODE_MAP,
    V3_ACT_CODE_SYSTEM,
    V3_ACTCODE_DISPLAY_NAMES,
    FHIRCodes,
    FHIRSystems,
    TemplateIds,
    TypeCodes,
    map_cpt_to_actcode,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

logger = logging.getLogger(__name__)


class EncounterConverter(BaseConverter[CCDAEncounter]):
    """Convert C-CDA Encounter Activity to FHIR Encounter resource.

    This converter handles the mapping from C-CDA Encounter Activity
    to a FHIR R4B Encounter resource, including status, class, type, and period.

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-EncounterActivity.html
    """

    def convert(self, encounter: CCDAEncounter, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Encounter Activity to a FHIR Encounter resource.

        Args:
            encounter: The C-CDA Encounter Activity
            section: The C-CDA Section containing this encounter (for narrative)

        Returns:
            FHIR Encounter resource as a dictionary

        Raises:
            ValueError: If the encounter lacks required data
        """
        fhir_encounter: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.ENCOUNTER,
        }

        # Generate ID from encounter identifier (skip nullFlavor entries)
        # Find first valid identifier
        root = None
        extension = None
        if encounter.id:
            for id_elem in encounter.id:
                if not id_elem.null_flavor and (id_elem.root or id_elem.extension):
                    root = id_elem.root
                    extension = id_elem.extension
                    break

        # Generate fallback context if no valid identifiers
        fallback_context = ""
        if root is None and extension is None:
            # Create deterministic context from encounter properties
            context_parts = []
            if encounter.code and encounter.code.code:
                context_parts.append(encounter.code.code)
            if encounter.effective_time:
                # Use low value if available for determinism
                if hasattr(encounter.effective_time, 'low') and encounter.effective_time.low:
                    context_parts.append(str(encounter.effective_time.low.value or ""))
                elif hasattr(encounter.effective_time, 'value') and encounter.effective_time.value:
                    context_parts.append(str(encounter.effective_time.value))
            if encounter.status_code and encounter.status_code.code:
                context_parts.append(encounter.status_code.code)
            fallback_context = "-".join(filter(None, context_parts))

        # Always generate an ID (with fallback if needed)
        fhir_encounter["id"] = self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="encounter",
            fallback_context=fallback_context,
        )

        # Identifiers (skip nullFlavor entries)
        if encounter.id:
            fhir_encounter["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in encounter.id
                if not id_elem.null_flavor and id_elem.root
            ]

        # Status - Map from statusCode, with moodCode as fallback
        fhir_encounter["status"] = self._extract_status(encounter)

        # Class - Map from code if V3 ActCode, otherwise default to ambulatory
        fhir_encounter["class"] = self._extract_class(encounter)

        # Subject (patient reference)
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Encounter without patient reference."
            )
        fhir_encounter["subject"] = self.reference_registry.get_patient_reference()

        # Type - Convert encounter code to type (if not used for class)
        encounter_type = self._extract_type(encounter)
        if encounter_type:
            fhir_encounter["type"] = [encounter_type]

        # Participant - Extract performers and their roles
        participants = self._extract_participants(encounter)
        if participants:
            fhir_encounter["participant"] = participants

        # Period - Convert effective time to period
        if encounter.effective_time:
            period = self._convert_period(encounter.effective_time)
            if period:
                fhir_encounter["period"] = period

        # Reason codes and references - Extract from indication entry relationships
        reasons = self._extract_reasons(encounter.entry_relationship)
        if reasons["codes"]:
            fhir_encounter["reasonCode"] = reasons["codes"]
        if reasons["references"]:
            fhir_encounter["reasonReference"] = reasons["references"]

        # Diagnosis - Extract from encounter diagnosis entry relationships
        diagnoses = self._extract_diagnoses(encounter.entry_relationship)
        if diagnoses:
            # Apply intelligent diagnosis role detection based on encounter context
            self._apply_diagnosis_roles(diagnoses, encounter)
            fhir_encounter["diagnosis"] = diagnoses

        # Location - Extract from location participants
        locations = self._extract_locations(encounter)
        if locations:
            fhir_encounter["location"] = locations

        # Hospitalization (discharge disposition)
        hospitalization = self._extract_hospitalization(encounter)
        if hospitalization:
            fhir_encounter["hospitalization"] = hospitalization

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=encounter, section=section)
        if narrative:
            fhir_encounter["text"] = narrative

        return fhir_encounter

    def _generate_encounter_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Encounter ID from C-CDA identifiers.

        Uses base class generate_resource_id with fallback to synthetic ID.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A FHIR-compliant ID string
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="encounter",
            fallback_context="",
        )

    def _extract_status(self, encounter: CCDAEncounter) -> str:
        """Extract FHIR status from C-CDA encounter.

        Maps from statusCode first, then falls back to moodCode.

        Args:
            encounter: The C-CDA encounter

        Returns:
            FHIR encounter status code
        """
        # First try statusCode
        if encounter.status_code and encounter.status_code.code:
            status_code = encounter.status_code.code.lower()
            if status_code in ENCOUNTER_STATUS_TO_FHIR:
                return ENCOUNTER_STATUS_TO_FHIR[status_code]

        # Fallback to moodCode
        if encounter.mood_code:
            mood_code = encounter.mood_code.upper()
            if mood_code == "INT":
                return FHIRCodes.EncounterStatus.PLANNED
            elif mood_code == "EVN":
                return FHIRCodes.EncounterStatus.FINISHED

        # Default to finished for documented encounters
        return FHIRCodes.EncounterStatus.FINISHED

    def _extract_class(self, encounter: CCDAEncounter) -> JSONObject:
        """Extract FHIR class from C-CDA encounter code.

        If the encounter code is from V3 ActCode system, use it for class.
        If translations contain V3 ActCode, prefer that over CPT mapping.
        If the encounter code is a CPT code with no V3 translation, map to V3 ActCode per C-CDA on FHIR IG.
        Otherwise, default to ambulatory.

        Args:
            encounter: The C-CDA encounter

        Returns:
            FHIR Coding object for encounter class
        """
        if encounter.code and encounter.code.code:
            # Check if code is from V3 ActCode system
            if encounter.code.code_system == V3_ACT_CODE_SYSTEM:
                # Use standard display name from mapping if available, otherwise fall back to C-CDA display
                standard_display = V3_ACTCODE_DISPLAY_NAMES.get(encounter.code.code)
                display = standard_display if standard_display else encounter.code.display_name

                return {
                    "system": FHIRSystems.V3_ACT_CODE,
                    "code": encounter.code.code,
                    "display": display,
                }

            # Check translations for V3 ActCode FIRST (before CPT mapping)
            # Per C-CDA on FHIR IG, explicit V3 ActCode translations should be preferred
            if hasattr(encounter.code, "translation") and encounter.code.translation:
                for trans in encounter.code.translation:
                    trans_system = None
                    trans_code = None
                    trans_display = None

                    if isinstance(trans, dict):
                        trans_system = trans.get("code_system")
                        trans_code = trans.get("code")
                        trans_display = trans.get("display_name")
                    elif hasattr(trans, "code_system"):
                        trans_system = trans.code_system
                        trans_code = trans.code if hasattr(trans, "code") else None
                        trans_display = trans.display_name if hasattr(trans, "display_name") else None

                    if trans_system == V3_ACT_CODE_SYSTEM and trans_code:
                        # Use standard display name from mapping if available
                        standard_display = V3_ACTCODE_DISPLAY_NAMES.get(trans_code)
                        display = standard_display if standard_display else trans_display

                        return {
                            "system": FHIRSystems.V3_ACT_CODE,
                            "code": trans_code,
                            "display": display,
                        }

            # Check if code is CPT and map to V3 ActCode
            # Only applies if no V3 ActCode translation was found above
            # Reference: docs/mapping/08-encounter.md lines 77-86
            if encounter.code.code_system == CPT_CODE_SYSTEM:
                mapped_actcode = map_cpt_to_actcode(encounter.code.code)
                if mapped_actcode:
                    # Use standard display name from mapping
                    display = V3_ACTCODE_DISPLAY_NAMES.get(mapped_actcode)
                    return {
                        "system": FHIRSystems.V3_ACT_CODE,
                        "code": mapped_actcode,
                        "display": display,
                    }

        # Default to ambulatory
        return {
            "system": FHIRSystems.V3_ACT_CODE,
            "code": FHIRCodes.EncounterClass.AMBULATORY,
        }

    def _extract_type(self, encounter: CCDAEncounter) -> JSONObject | None:
        """Extract FHIR type from C-CDA encounter code.

        If the encounter code is NOT from V3 ActCode (since that's used for class),
        convert it to type.

        Args:
            encounter: The C-CDA encounter

        Returns:
            FHIR CodeableConcept for encounter type, or None
        """
        if not encounter.code or not encounter.code.code:
            return None

        # If code is from V3 ActCode, don't use it for type (it's used for class)
        if encounter.code.code_system == V3_ACT_CODE_SYSTEM:
            return None

        return self._convert_code(encounter.code)

    def _convert_code(self, code) -> JSONObject | None:
        """Convert C-CDA encounter code to FHIR CodeableConcept.

        Args:
            code: The C-CDA encounter code

        Returns:
            FHIR CodeableConcept or None
        """
        if not code or not code.code:
            return None

        # Extract translations if present
        translations = []
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if isinstance(trans, dict):
                    trans_code = trans.get("code")
                    trans_system = trans.get("code_system")
                    trans_display = trans.get("display_name")
                elif hasattr(trans, "code"):
                    trans_code = trans.code
                    trans_system = trans.code_system if hasattr(trans, "code_system") else None
                    trans_display = trans.display_name if hasattr(trans, "display_name") else None
                else:
                    continue

                if trans_code and trans_system:
                    translations.append({
                        "code": trans_code,
                        "code_system": trans_system,
                        "display_name": trans_display,
                    })

        # Get original text if present (with reference resolution)
        original_text = None
        if hasattr(code, "original_text") and code.original_text:
            # original_text is an ED (Encapsulated Data) object
            original_text = self.extract_original_text(code.original_text, section=None)

        # Use display_name as text if original_text not available
        if not original_text and code.display_name:
            original_text = code.display_name

        return self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system,
            display_name=code.display_name,
            original_text=original_text,
            translations=translations,
        )

    def _convert_period(self, effective_time) -> JSONObject | None:
        """Convert C-CDA effectiveTime to FHIR Period.

        Args:
            effective_time: The C-CDA effectiveTime (can be IVL_TS or simple value)

        Returns:
            FHIR Period or None
        """
        if isinstance(effective_time, str):
            # Simple datetime value - use as start
            converted = self.convert_date(effective_time)
            if converted:
                return {"start": converted}

        period: JSONObject = {}

        # Handle single value
        if hasattr(effective_time, "value") and effective_time.value:
            converted = self.convert_date(effective_time.value)
            if converted:
                period["start"] = converted

        # Handle period (low/high)
        if hasattr(effective_time, "low") and effective_time.low:
            low_value = effective_time.low.value if hasattr(effective_time.low, "value") else effective_time.low
            if low_value:
                converted_low = self.convert_date(str(low_value))
                if converted_low:
                    period["start"] = converted_low

        if hasattr(effective_time, "high") and effective_time.high:
            high_value = effective_time.high.value if hasattr(effective_time.high, "value") else effective_time.high
            if high_value:
                converted_high = self.convert_date(str(high_value))
                if converted_high:
                    period["end"] = converted_high

        return period if period else None

    def _extract_participants(self, encounter: CCDAEncounter) -> list[JSONObject]:
        """Extract FHIR participants from C-CDA performers.

        Args:
            encounter: The C-CDA encounter

        Returns:
            List of FHIR participant objects
        """
        participants = []

        if not encounter.performer:
            return participants

        for performer in encounter.performer:
            participant: JSONObject = {}

            # Extract participant type from functionCode
            # Map C-CDA ParticipationFunction codes to FHIR ParticipationType codes
            # Reference: docs/mapping/08-encounter.md lines 217-223
            # Reference: docs/mapping/09-participations.md lines 217-232
            if hasattr(performer, "function_code") and performer.function_code:
                function_code = performer.function_code.code if hasattr(performer.function_code, "code") else None

                # Map known function codes (PCP→PPRF, ATTPHYS→ATND, ANEST→SPRF, etc.)
                mapped_code = PARTICIPATION_FUNCTION_CODE_MAP.get(
                    function_code,
                    function_code  # Pass through if not in map
                ) if function_code else "PART"  # Default to PART if no code

                type_coding = {
                    "system": FHIRSystems.V3_PARTICIPATION_TYPE,
                    "code": mapped_code,
                    "display": performer.function_code.display_name if hasattr(performer.function_code, "display_name") else None,
                }
                participant["type"] = [{"coding": [type_coding]}]
            else:
                # Default to PART (participant) if no function code specified
                participant["type"] = [{
                    "coding": [{
                        "system": FHIRSystems.V3_PARTICIPATION_TYPE,
                        "code": "PART",
                        "display": "participant",
                    }]
                }]

            # Extract individual reference from assignedEntity
            if hasattr(performer, "assigned_entity") and performer.assigned_entity:
                assigned_entity = performer.assigned_entity

                # Generate practitioner ID from NPI or other identifiers
                if hasattr(assigned_entity, "id") and assigned_entity.id:
                    for id_elem in assigned_entity.id:
                        if id_elem.root:
                            practitioner_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                            participant["individual"] = {
                                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{practitioner_id}"
                            }
                            break

            if participant:
                participants.append(participant)

        return participants

    def _extract_locations(self, encounter: CCDAEncounter) -> list[JSONObject]:
        """Extract FHIR locations from C-CDA location participants.

        Args:
            encounter: The C-CDA encounter

        Returns:
            List of FHIR location objects
        """
        locations = []

        if not encounter.participant:
            return locations

        for participant in encounter.participant:
            # Look for location participants (typeCode="LOC")
            if hasattr(participant, "type_code") and participant.type_code == "LOC":
                location: JSONObject = {}

                # Extract location reference and display
                if hasattr(participant, "participant_role") and participant.participant_role:
                    role = participant.participant_role

                    # Extract location name from playingEntity (needed for synthetic ID)
                    display = None
                    if hasattr(role, "playing_entity") and role.playing_entity:
                        entity = role.playing_entity
                        if hasattr(entity, "name") and entity.name:
                            if isinstance(entity.name, str):
                                display = entity.name
                            elif isinstance(entity.name, list) and len(entity.name) > 0:
                                # Handle list of ON objects
                                first_name = entity.name[0]
                                if hasattr(first_name, "value") and first_name.value:
                                    display = first_name.value
                            elif hasattr(entity.name, "value"):
                                display = entity.name.value

                    # Extract address data (needed for synthetic ID)
                    address_for_id = None
                    if hasattr(role, "addr") and role.addr:
                        addr_raw = role.addr[0] if isinstance(role.addr, list) else role.addr
                        # Build simple address dict for ID generation
                        address_for_id = {}
                        if hasattr(addr_raw, "city") and addr_raw.city:
                            address_for_id["city"] = addr_raw.city
                        if hasattr(addr_raw, "state") and addr_raw.state:
                            address_for_id["state"] = addr_raw.state
                        if hasattr(addr_raw, "street_address_line") and addr_raw.street_address_line:
                            # street_address_line is a list, use first element
                            address_for_id["line"] = [addr_raw.street_address_line[0]] if addr_raw.street_address_line else []

                    # Generate location ID from role ID, or create synthetic ID if missing
                    location_id = None
                    if hasattr(role, "id") and role.id:
                        for id_elem in role.id:
                            if id_elem.root:
                                location_id = self._generate_location_id(id_elem.root, id_elem.extension)
                                break

                    # Generate synthetic ID if no explicit ID
                    if not location_id and display:
                        location_id = self._generate_synthetic_location_id(display, address_for_id)

                    # Create location reference if we have a valid ID
                    if location_id:
                        location["location"] = {
                            "reference": f"Location/{location_id}"
                        }
                        if display:
                            location["location"]["display"] = display

                        # Extract period from participant time
                        period = None
                        if hasattr(participant, "time") and participant.time:
                            period = self._convert_period(participant.time)
                            if period:
                                location["period"] = period

                        # Determine status based on participant time and encounter status
                        location["status"] = self._determine_location_status(participant, period, encounter)

                        if location:
                            locations.append(location)

        return locations

    def _determine_location_status(
        self,
        participant,
        period: JSONObject | None,
        encounter: CCDAEncounter
    ) -> str:
        """Determine FHIR location status from C-CDA participant time and encounter context.

        The location status indicates the patient's presence at the location:
        - completed: Patient was at location during the period (has end time)
        - active: Patient is/was at location (no end time, or ongoing)
        - planned: Patient is planned to be at location
        - reserved: Location is held empty (rarely used in C-CDA)

        Determination logic:
        1. If participant.time has both start and end → "completed"
        2. If participant.time has only start (no end) → "active"
        3. If no participant.time, derive from encounter status:
           - encounter "finished" → "completed"
           - encounter "in-progress" → "active"
           - encounter "planned" → "planned"
           - encounter "cancelled" → "completed" (was assigned)

        Reference: http://hl7.org/fhir/R4/valueset-encounter-location-status.html

        Args:
            participant: The C-CDA participant with typeCode="LOC"
            period: The converted FHIR period from participant.time (if any)
            encounter: The C-CDA encounter providing context

        Returns:
            FHIR EncounterLocationStatus code
        """
        # If participant has time information, use it to determine status
        if period:
            # If period has both start and end, location assignment is completed
            if "end" in period:
                return "completed"
            # If period has only start (no end), location is active
            elif "start" in period:
                return "active"

        # Fall back to encounter status
        encounter_status = self._extract_status(encounter)

        # Map encounter status to location status
        if encounter_status == FHIRCodes.EncounterStatus.FINISHED:
            return "completed"
        elif encounter_status == FHIRCodes.EncounterStatus.IN_PROGRESS:
            return "active"
        elif encounter_status == FHIRCodes.EncounterStatus.PLANNED:
            return "planned"
        elif encounter_status == FHIRCodes.EncounterStatus.CANCELLED:
            # Location was assigned but encounter cancelled
            return "completed"
        else:
            # Default to completed for documented encounters
            return "completed"

    def _determine_admit_source(self, encounter: CCDAEncounter) -> JSONObject | None:
        """Determine FHIR admission source from C-CDA encounter characteristics.

        C-CDA does not explicitly encode admission source, but it can be intelligently
        inferred from encounter characteristics:

        1. Emergency encounter class (EMER) → "emd" (from emergency department)
           Rationale: Emergency encounters originate from the hospital's ED

        2. priorityCode = "EM" (Emergency) → "emd" (from emergency department)
           Rationale: Emergency priority indicates admission via ED

        3. Inpatient encounters (IMP, ACUTE, NONAC) → "other"
           Rationale: General hospital admission without specific source

        4. Outpatient/Ambulatory encounters → No admission source
           Rationale: Admission source only applies to inpatient admissions

        Reference: http://terminology.hl7.org/CodeSystem/admit-source

        Args:
            encounter: The C-CDA encounter

        Returns:
            FHIR CodeableConcept for admission source, or None
        """
        # Extract encounter class from code or translation
        encounter_class = None
        if encounter.code and encounter.code.code:
            if encounter.code.code_system == V3_ACT_CODE_SYSTEM:
                encounter_class = encounter.code.code
            elif hasattr(encounter.code, "translation") and encounter.code.translation:
                for trans in encounter.code.translation:
                    trans_system = None
                    trans_code = None

                    if isinstance(trans, dict):
                        trans_system = trans.get("code_system")
                        trans_code = trans.get("code")
                    elif hasattr(trans, "code_system"):
                        trans_system = trans.code_system
                        trans_code = trans.code if hasattr(trans, "code") else None

                    if trans_system == V3_ACT_CODE_SYSTEM and trans_code:
                        encounter_class = trans_code
                        break

        # 1. Emergency encounter class → from emergency department
        if encounter_class == "EMER":
            return {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/admit-source",
                    "code": "emd",
                    "display": "From accident/emergency department"
                }]
            }

        # 2. Emergency priority code → from emergency department
        if encounter.priority_code and encounter.priority_code.code == "EM":
            return {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/admit-source",
                    "code": "emd",
                    "display": "From accident/emergency department"
                }]
            }

        # 3. Inpatient encounters → other (general admission)
        # Only assign "other" for inpatient encounters, not outpatient
        if encounter_class in ["IMP", "ACUTE", "NONAC"]:
            return {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/admit-source",
                    "code": "other",
                    "display": "Other"
                }]
            }

        # 4. Outpatient/Ambulatory → No admission source
        # Don't assign admission source for non-inpatient encounters
        return None

    def _extract_hospitalization(self, encounter: CCDAEncounter) -> JSONObject | None:
        """Extract FHIR hospitalization from C-CDA encounter.

        Extracts:
        - admitSource: Intelligently inferred from encounter characteristics
        - dischargeDisposition: Mapped from sdtc:dischargeDispositionCode

        Args:
            encounter: The C-CDA encounter

        Returns:
            FHIR hospitalization object or None
        """
        hospitalization: JSONObject = {}

        # Extract admission source (intelligently inferred)
        admit_source = self._determine_admit_source(encounter)
        if admit_source:
            hospitalization["admitSource"] = admit_source

        # Extract discharge disposition
        if encounter.sdtc_discharge_disposition_code:
            disposition = encounter.sdtc_discharge_disposition_code
            if disposition.code:
                # Map discharge disposition code to FHIR
                fhir_code = DISCHARGE_DISPOSITION_TO_FHIR.get(disposition.code)
                if not fhir_code:
                    # Use original code if not in mapping
                    fhir_code = disposition.code

                hospitalization["dischargeDisposition"] = {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
                        "code": fhir_code,
                        "display": disposition.display_name if hasattr(disposition, "display_name") and disposition.display_name else None,
                    }]
                }

        return hospitalization if hospitalization else None

    def _extract_diagnoses(self, entry_relationships: list[EntryRelationship] | None) -> list[JSONObject]:
        """Extract FHIR diagnoses from encounter diagnosis entry relationships.

        Creates condition references with intelligent diagnosis role detection.

        Args:
            entry_relationships: List of entry relationships

        Returns:
            List of FHIR diagnosis objects with condition references and use codes
        """
        diagnoses = []

        if not entry_relationships:
            return diagnoses

        for entry_rel in entry_relationships:
            # Look for Encounter Diagnosis act (template 2.16.840.1.113883.10.20.22.4.80)
            if entry_rel.act and entry_rel.act.template_id:
                for template in entry_rel.act.template_id:
                    if template.root == TemplateIds.ENCOUNTER_DIAGNOSIS:
                        # Extract diagnosis from nested observation
                        if entry_rel.act.entry_relationship:
                            for nested_entry in entry_rel.act.entry_relationship:
                                if nested_entry.observation:
                                    obs = nested_entry.observation

                                    # Generate condition ID from observation ID
                                    # Must match ID generation in ConditionConverter
                                    if obs.id and len(obs.id) > 0:
                                        first_id = obs.id[0]
                                        condition_id = self._generate_condition_id(first_id.root, first_id.extension)
                                    else:
                                        # Fallback: Generate deterministic ID from observation content
                                        # Must use same method as ConditionConverter for consistency
                                        from ccda_to_fhir.converters.condition import (
                                            generate_id_from_observation_content,
                                        )
                                        condition_id = generate_id_from_observation_content(obs)

                                    diagnosis: JSONObject = {
                                        "condition": {
                                            "reference": f"{FHIRCodes.ResourceTypes.CONDITION}/{condition_id}"
                                        }
                                    }

                                    # Add diagnosis use/role - will be set by _determine_diagnosis_role
                                    # when the encounter context is available
                                    diagnosis["use"] = {
                                        "coding": [{
                                            "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
                                            "code": "billing",
                                            "display": "Billing"
                                        }]
                                    }

                                    diagnoses.append(diagnosis)
                        break

        return diagnoses

    def _apply_diagnosis_roles(self, diagnoses: list[JSONObject], encounter: CCDAEncounter) -> None:
        """Apply intelligent diagnosis role detection to diagnoses based on encounter context.

        Updates diagnosis.use codes in place based on encounter characteristics:
        - Encounters with discharge disposition → DD (discharge diagnosis)
        - Inpatient encounters (IMP/ACUTE) without discharge → AD (admission diagnosis)
        - Emergency encounters (EMER) → AD (admission diagnosis)
        - All other encounters → billing (general documentation/billing)

        Args:
            diagnoses: List of diagnosis objects to update (modified in place)
            encounter: The C-CDA encounter providing context
        """
        if not diagnoses:
            return

        # Determine the appropriate diagnosis role based on encounter context
        diagnosis_role = self._determine_diagnosis_role(encounter)

        # Apply the determined role to all diagnoses in this encounter
        for diagnosis in diagnoses:
            if "use" in diagnosis and "coding" in diagnosis["use"]:
                diagnosis["use"]["coding"][0]["code"] = diagnosis_role["code"]
                diagnosis["use"]["coding"][0]["display"] = diagnosis_role["display"]

    def _determine_diagnosis_role(self, encounter: CCDAEncounter) -> dict[str, str]:
        """Determine the appropriate diagnosis role based on encounter context.

        C-CDA Encounter Diagnosis Act does not explicitly encode diagnosis roles
        (admission, discharge, billing, etc.). This method infers the role from
        encounter characteristics:

        1. Discharge disposition present → Discharge diagnosis (DD)
           Rationale: If discharge info exists, diagnosis is documented at discharge

        2. Inpatient encounter (IMP/ACUTE) → Admission diagnosis (AD)
           Rationale: Inpatient encounters typically document admission diagnoses

        3. Emergency encounter (EMER) → Admission diagnosis (AD)
           Rationale: Emergency diagnoses are documented at presentation/admission

        4. All other cases → Billing diagnosis (billing)
           Rationale: Most encounters document diagnoses for billing/general purposes

        Reference: http://terminology.hl7.org/CodeSystem/diagnosis-role

        Args:
            encounter: The C-CDA encounter

        Returns:
            Dict with 'code' and 'display' keys for the diagnosis role
        """
        # Check for discharge disposition - indicates discharge diagnosis
        if encounter.sdtc_discharge_disposition_code and encounter.sdtc_discharge_disposition_code.code:
            return {
                "code": "DD",
                "display": "Discharge diagnosis"
            }

        # Check encounter class for inpatient or emergency
        if encounter.code and encounter.code.code:
            encounter_class = None

            # Extract class from code or translation
            if encounter.code.code_system == V3_ACT_CODE_SYSTEM:
                encounter_class = encounter.code.code
            elif hasattr(encounter.code, "translation") and encounter.code.translation:
                for trans in encounter.code.translation:
                    trans_system = None
                    trans_code = None

                    if isinstance(trans, dict):
                        trans_system = trans.get("code_system")
                        trans_code = trans.get("code")
                    elif hasattr(trans, "code_system"):
                        trans_system = trans.code_system
                        trans_code = trans.code if hasattr(trans, "code") else None

                    if trans_system == V3_ACT_CODE_SYSTEM and trans_code:
                        encounter_class = trans_code
                        break

            # Inpatient encounters → admission diagnosis
            if encounter_class in ["IMP", "ACUTE", "NONAC"]:
                return {
                    "code": "AD",
                    "display": "Admission diagnosis"
                }

            # Emergency encounters → admission diagnosis
            if encounter_class == "EMER":
                return {
                    "code": "AD",
                    "display": "Admission diagnosis"
                }

        # Default to billing diagnosis for all other encounters
        # This is the most general-purpose role for outpatient, ambulatory, etc.
        return {
            "code": "billing",
            "display": "Billing"
        }

    def _extract_reasons(self, entry_relationships: list[EntryRelationship] | None) -> dict[str, list]:
        """Extract FHIR reason codes and references from C-CDA entry relationships.

        Handles two patterns:
        1. RSON observation with inline code value → reasonCode
        2. RSON observation that IS a Problem Observation → reasonReference to Condition

        Args:
            entry_relationships: List of entry relationships

        Returns:
            Dict with "codes" and "references" lists
        """
        reason_codes = []
        reason_refs = []

        if not entry_relationships:
            return {"codes": reason_codes, "references": reason_refs}

        for entry_rel in entry_relationships:
            # Look for indication observations (RSON typeCode)
            if entry_rel.type_code == TypeCodes.REASON and entry_rel.observation:
                obs = entry_rel.observation

                # Check if this observation IS a Problem Observation
                is_problem_obs = False
                if hasattr(obs, "template_id") and obs.template_id:
                    for template in obs.template_id:
                        if hasattr(template, "root") and template.root == TemplateIds.PROBLEM_OBSERVATION:
                            is_problem_obs = True
                            break

                if is_problem_obs:
                    # This is a Problem Observation - check if Condition exists
                    condition_id = self._generate_condition_id_from_observation(obs)

                    # Per C-CDA on FHIR spec: only create reasonReference if the Problem
                    # Observation was converted to a Condition resource elsewhere in the document
                    if self.reference_registry and self.reference_registry.has_resource(
                        FHIRCodes.ResourceTypes.CONDITION, condition_id
                    ):
                        # Condition exists - use reasonReference
                        reason_refs.append({
                            "reference": f"{FHIRCodes.ResourceTypes.CONDITION}/{condition_id}"
                        })
                    else:
                        # Inline Problem Observation not converted - use reasonCode
                        if obs.value:
                            if isinstance(obs.value, list):
                                for value in obs.value:
                                    if hasattr(value, "code") and value.code:
                                        codeable = self._convert_diagnosis_code(value)
                                        if codeable:
                                            reason_codes.append(codeable)
                            elif hasattr(obs.value, "code"):
                                codeable = self._convert_diagnosis_code(obs.value)
                                if codeable:
                                    reason_codes.append(codeable)
                else:
                    # Extract reason code from observation.value
                    if obs.value:
                        if isinstance(obs.value, list):
                            for value in obs.value:
                                if hasattr(value, "code") and value.code:
                                    codeable = self._convert_diagnosis_code(value)
                                    if codeable:
                                        reason_codes.append(codeable)
                        elif hasattr(obs.value, "code"):
                            codeable = self._convert_diagnosis_code(obs.value)
                            if codeable:
                                reason_codes.append(codeable)

        return {"codes": reason_codes, "references": reason_refs}

    def _convert_diagnosis_code(self, code) -> JSONObject | None:
        """Convert diagnosis code to FHIR CodeableConcept.

        Args:
            code: The diagnosis code

        Returns:
            FHIR CodeableConcept or None
        """
        if not code or not hasattr(code, "code") or not code.code:
            return None

        return self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system if hasattr(code, "code_system") else None,
            display_name=code.display_name if hasattr(code, "display_name") else None,
        )

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

    def _generate_location_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Location ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Location", root, extension)

    def _generate_synthetic_location_id(self, name: str, address: JSONObject | None) -> str:
        """Generate synthetic FHIR Location ID from name and address.

        Used when C-CDA location participant has no explicit ID element.
        Creates a deterministic ID based on location characteristics.

        Args:
            name: Location name
            address: FHIR address object (if available)

        Returns:
            Generated synthetic Location ID
        """
        import hashlib

        # Build a unique string from available identifying information
        id_parts = [name]

        if address:
            if "city" in address:
                id_parts.append(address["city"])
            if "state" in address:
                id_parts.append(address["state"])
            if "line" in address and address["line"]:
                # Use first line
                id_parts.append(address["line"][0])

        # Create deterministic hash
        combined = "|".join(id_parts)
        hash_value = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return f"location-{hash_value}"

    def _generate_condition_id_from_observation(self, observation) -> str:
        """Generate a Condition resource ID from a Problem Observation.

        Uses the same ID generation logic as ConditionConverter to ensure
        consistent references to Condition resources.

        Args:
            observation: Problem Observation with ID

        Returns:
            Condition resource ID string
        """
        if hasattr(observation, "id") and observation.id:
            for id_elem in observation.id:
                if hasattr(id_elem, "root") and id_elem.root:
                    extension = id_elem.extension if hasattr(id_elem, "extension") else None
                    return self._generate_condition_id(id_elem.root, extension)
        # Fallback: Generate deterministic ID from observation content
        # Must use same method as ConditionConverter for consistency
        from ccda_to_fhir.converters.condition import generate_id_from_observation_content
        return generate_id_from_observation_content(observation)

    def _generate_condition_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Condition ID using cached UUID v4 from C-CDA identifiers.

        Matches the ID generation logic in ConditionConverter for consistency.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Condition", root, extension)

    def extract_diagnosis_observations(self, encounter: CCDAEncounter) -> list:
        """Extract diagnosis observations from Encounter Diagnosis Acts.

        These observations should be converted to Condition resources with
        category="encounter-diagnosis" to match the Encounter.diagnosis references.

        Args:
            encounter: The C-CDA Encounter Activity

        Returns:
            List of diagnosis observations to convert to Condition resources
        """
        observations = []

        if not encounter.entry_relationship:
            return observations

        for entry_rel in encounter.entry_relationship:
            # Look for Encounter Diagnosis act (template 2.16.840.1.113883.10.20.22.4.80)
            if entry_rel.act and entry_rel.act.template_id:
                for template in entry_rel.act.template_id:
                    if template.root == TemplateIds.ENCOUNTER_DIAGNOSIS:
                        # Extract diagnosis from nested observation
                        if entry_rel.act.entry_relationship:
                            for nested_entry in entry_rel.act.entry_relationship:
                                if nested_entry.observation:
                                    observations.append(nested_entry.observation)
                        break

        return observations
