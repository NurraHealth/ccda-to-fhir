"""Procedure converter: C-CDA Procedure Activity to FHIR Procedure resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act as CCDAAct
from ccda_to_fhir.ccda.models.datatypes import CD, IVL_TS
from ccda_to_fhir.ccda.models.observation import Observation as CCDAObservation
from ccda_to_fhir.ccda.models.procedure import Procedure as CCDAProcedure
from ccda_to_fhir.constants import (
    PROCEDURE_STATUS_TO_FHIR,
    FHIRCodes,
    FHIRSystems,
    TemplateIds,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class ProcedureConverter(BaseConverter[CCDAProcedure | CCDAObservation | CCDAAct]):
    """Convert C-CDA Procedure Activity to FHIR Procedure resource.

    This converter handles the mapping from C-CDA Procedure Activity templates
    to a FHIR R4B Procedure resource, including status, code, and performed date.

    Supports:
    - Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14)
    - Procedure Activity Observation (2.16.840.1.113883.10.20.22.4.13)
    - Procedure Activity Act (2.16.840.1.113883.10.20.22.4.12)

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ProcedureActivityProcedure.html
    """

    def convert(self, procedure: CCDAProcedure | CCDAObservation | CCDAAct, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Procedure Activity to a FHIR Procedure resource.

        Accepts Procedure Activity Procedure, Procedure Activity Observation,
        and Procedure Activity Act templates, as all map to FHIR Procedure resource.

        Args:
            procedure: The C-CDA Procedure Activity (Procedure, Observation, or Act element)
            section: The C-CDA Section containing this procedure (for narrative)

        Returns:
            FHIR Procedure resource as a dictionary

        Raises:
            ValueError: If the procedure lacks required data
        """
        if not procedure.code:
            raise ValueError("Procedure Activity must have a code")

        # Check if code has null flavor (no actual code value)
        # Per C-CDA spec, code is required but may have nullFlavor
        has_valid_code = (
            hasattr(procedure.code, "code") and procedure.code.code
            and not (hasattr(procedure.code, "null_flavor") and procedure.code.null_flavor)
        )

        fhir_procedure: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.PROCEDURE,
        }

        # Generate ID from procedure identifier
        # Find first valid identifier (skip nullFlavor)
        root = None
        extension = None
        if procedure.id and len(procedure.id) > 0:
            for id_elem in procedure.id:
                if not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                    if id_elem.root or id_elem.extension:
                        root = id_elem.root
                        extension = id_elem.extension
                        break

        # Generate fallback context if no valid identifiers
        fallback_context = ""
        if root is None and extension is None:
            # Create deterministic context from procedure properties
            context_parts = []
            if procedure.code and hasattr(procedure.code, "code") and procedure.code.code:
                context_parts.append(procedure.code.code)
            if procedure.effective_time:
                # Use low value if available for determinism
                if hasattr(procedure.effective_time, 'low') and procedure.effective_time.low:
                    context_parts.append(str(procedure.effective_time.low.value or ""))
                elif hasattr(procedure.effective_time, 'value') and procedure.effective_time.value:
                    context_parts.append(str(procedure.effective_time.value))
            if procedure.status_code and procedure.status_code.code:
                context_parts.append(procedure.status_code.code)
            fallback_context = "-".join(filter(None, context_parts))

        # Always generate an ID (with fallback if needed)
        fhir_procedure["id"] = self._generate_procedure_id(
            root=root,
            extension=extension,
            fallback_context=fallback_context,
        )

        # Identifiers
        if procedure.id:
            fhir_procedure["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in procedure.id
                if id_elem.root
            ]

        # Status (required)
        status = self._map_status(procedure.status_code)
        # Override status if negationInd is true
        if procedure.negation_ind:
            status = FHIRCodes.ProcedureStatus.NOT_DONE
        fhir_procedure["status"] = status

        # Code (required)
        # If code has nullFlavor, try to extract text from narrative
        if has_valid_code:
            fhir_procedure["code"] = self._convert_code(procedure.code)
        else:
            # Code has nullFlavor - extract text from narrative if available
            code_text = None
            if hasattr(procedure, "text") and procedure.text:
                # Try to resolve text reference to section narrative
                code_text = self.extract_original_text(procedure.text, section=section)

            if code_text:
                # Create CodeableConcept with only text
                fhir_procedure["code"] = {"text": code_text}
            else:
                # No text available - use data-absent-reason extension
                # Per C-CDA on FHIR IG ConceptMap CF-NullFlavorDataAbsentReason
                # Extension goes INSIDE CodeableConcept (complex type, not primitive)
                null_flavor = procedure.code.null_flavor if hasattr(procedure.code, "null_flavor") else None
                fhir_procedure["code"] = {
                    "extension": [
                        self.create_data_absent_reason_extension(null_flavor, default_reason="unknown")
                    ],
                    "text": "Procedure code not specified"
                }

        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Procedure without patient reference."
            )
        fhir_procedure["subject"] = self.reference_registry.get_patient_reference()

        # Performed date/time
        performed = None
        if procedure.effective_time:
            performed = self._convert_performed_time(procedure.effective_time)
            if performed:
                # Use performedDateTime if it's a single datetime, otherwise performedPeriod
                if "start" in performed or "end" in performed:
                    fhir_procedure["performedPeriod"] = performed
                else:
                    fhir_procedure["performedDateTime"] = performed

        # US Core Must Support: Procedure.performed[x] is required
        # If we couldn't extract a valid performed time, add data-absent-reason extension
        # per C-CDA on FHIR IG guidance (docs/mapping/05-procedure.md lines 160-174)
        if not performed:
            fhir_procedure["_performedDateTime"] = {
                "extension": [
                    self.create_data_absent_reason_extension(None, default_reason="unknown")
                ]
            }

        # Body site (only available in Procedure, not in Act or Observation)
        if hasattr(procedure, "target_site_code") and procedure.target_site_code:
            body_sites = []
            for site_code in procedure.target_site_code:
                if site_code.code:
                    # Use specialized method that handles laterality qualifiers
                    body_site = self._convert_body_site_with_qualifiers(site_code)
                    if body_site:
                        body_sites.append(body_site)
            if body_sites:
                fhir_procedure["bodySite"] = body_sites

        # Performers
        if procedure.performer:
            performers = self._extract_performers(procedure.performer)
            if performers:
                fhir_procedure["performer"] = performers

        # Location
        if procedure.participant:
            location = self._extract_location(procedure.participant)
            if location:
                fhir_procedure["location"] = location

            # Devices (Product Instance)
            devices_result = self._extract_devices(
                procedure.participant,
                procedure_status=procedure.status_code.code if procedure.status_code else None
            )
            if devices_result and devices_result.get("devices"):
                fhir_procedure["focalDevice"] = devices_result["focal_devices"]

        # Author/recorder
        if procedure.author:
            recorder = self._extract_recorder(procedure.author)
            if recorder:
                fhir_procedure["recorder"] = recorder

        # Reason codes and references
        if procedure.entry_relationship:
            reasons = self._extract_reasons(procedure.entry_relationship)
            if reasons.get("codes"):
                fhir_procedure["reasonCode"] = reasons["codes"]
            if reasons.get("references"):
                fhir_procedure["reasonReference"] = reasons["references"]

            # Outcomes
            outcomes = self._extract_outcomes(procedure.entry_relationship)
            if outcomes:
                fhir_procedure["outcome"] = outcomes

            # Complications
            complications = self._extract_complications(procedure.entry_relationship)
            if complications:
                fhir_procedure["complication"] = complications

            # Follow-up
            followups = self._extract_followups(procedure.entry_relationship)
            if followups:
                fhir_procedure["followUp"] = followups

        # Notes
        notes = self._extract_notes(procedure)
        if notes:
            fhir_procedure["note"] = notes

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=procedure, section=section)
        if narrative:
            fhir_procedure["text"] = narrative

        return fhir_procedure

    def _generate_procedure_id(
        self,
        root: str | None,
        extension: str | None,
        fallback_context: str = "",
    ) -> str:
        """Generate a FHIR Procedure ID from C-CDA identifiers.

        Uses base class generate_resource_id with fallback to synthetic ID.

        Args:
            root: The OID or UUID root
            extension: The extension value
            fallback_context: Additional context for synthetic ID generation

        Returns:
            A FHIR-compliant ID string
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="procedure",
            fallback_context=fallback_context,
        )

    def _map_status(self, status_code) -> str:
        """Map C-CDA status code to FHIR Procedure status.

        Args:
            status_code: The C-CDA status code

        Returns:
            FHIR Procedure status code
        """
        if not status_code or not status_code.code:
            return FHIRCodes.ProcedureStatus.UNKNOWN

        ccda_status = status_code.code.lower()
        return PROCEDURE_STATUS_TO_FHIR.get(ccda_status, FHIRCodes.ProcedureStatus.UNKNOWN)

    def _convert_code(self, code: CD) -> JSONObject:
        """Convert C-CDA procedure code to FHIR CodeableConcept.

        Args:
            code: The C-CDA procedure code

        Returns:
            FHIR CodeableConcept
        """
        # Extract translations if present
        translations = []
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if isinstance(trans, (CD, dict)):
                    trans_code = trans.code if hasattr(trans, "code") else trans.get("code")
                    trans_system = trans.code_system if hasattr(trans, "code_system") else trans.get("code_system")
                    trans_display = trans.display_name if hasattr(trans, "display_name") else trans.get("display_name")

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

    def _convert_performed_time(self, effective_time: IVL_TS | str) -> JSONObject | str | None:
        """Convert C-CDA effectiveTime to FHIR performed time.

        Args:
            effective_time: The C-CDA effectiveTime (can be IVL_TS or simple value)

        Returns:
            FHIR performedDateTime (string) or performedPeriod (dict), or None
        """
        if isinstance(effective_time, str):
            # Simple datetime value
            return self.convert_date(effective_time)

        # Handle IVL_TS (interval)
        if hasattr(effective_time, "value") and effective_time.value:
            # Single point in time
            return self.convert_date(effective_time.value)

        # Handle period (low/high)
        period: JSONObject = {}

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

    def _extract_performers(self, performers: list) -> list[JSONObject]:
        """Extract FHIR performers from C-CDA performers.

        Args:
            performers: List of C-CDA performer elements

        Returns:
            List of FHIR performer objects
        """
        from ccda_to_fhir.constants import PARTICIPATION_FUNCTION_CODE_MAP

        fhir_performers = []

        for performer in performers:
            if not hasattr(performer, "assigned_entity") or not performer.assigned_entity:
                continue

            assigned_entity = performer.assigned_entity
            performer_obj: JSONObject = {}

            # Extract function code from performer
            # Maps C-CDA ParticipationFunction to FHIR ParticipationType
            # Reference: docs/mapping/09-participations.md lines 211-232
            if hasattr(performer, "function_code") and performer.function_code:
                function_code = performer.function_code.code if hasattr(performer.function_code, "code") else None

                if function_code:
                    # Map known function codes or pass through if not in map
                    mapped_code = PARTICIPATION_FUNCTION_CODE_MAP.get(function_code, function_code)

                    # Only include codes that are valid for Procedure.performer.function
                    # The performer-function value set excludes encounter-specific codes like ADM, DIS
                    # Reference: https://build.fhir.org/valueset-performer-function.html
                    encounter_only_codes = {"ADM", "DIS", "REF"}
                    if mapped_code not in encounter_only_codes:
                        function_coding = {
                            "system": FHIRSystems.V3_PARTICIPATION_TYPE,
                            "code": mapped_code,
                        }
                        if hasattr(performer.function_code, "display_name") and performer.function_code.display_name:
                            function_coding["display"] = performer.function_code.display_name

                        performer_obj["function"] = {"coding": [function_coding]}

            # Extract practitioner reference from assigned entity
            if hasattr(assigned_entity, "id") and assigned_entity.id:
                for id_elem in assigned_entity.id:
                    if id_elem.root:
                        pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                        performer_obj["actor"] = {
                            "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                        }
                        break

            # Extract organization reference if present
            if hasattr(assigned_entity, "represented_organization") and assigned_entity.represented_organization:
                org = assigned_entity.represented_organization
                if hasattr(org, "id") and org.id:
                    for id_elem in org.id:
                        if id_elem.root:
                            org_id = self._generate_organization_id(id_elem.root, id_elem.extension)
                            performer_obj["onBehalfOf"] = {
                                "reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{org_id}"
                            }
                            break

            if performer_obj:
                fhir_performers.append(performer_obj)

        return fhir_performers

    def _extract_location(self, participants: list) -> JSONObject | None:
        """Extract FHIR location from C-CDA participants.

        Args:
            participants: List of C-CDA participant elements

        Returns:
            FHIR location reference or None
        """
        for participant in participants:
            # Look for location participants (typeCode="LOC")
            if hasattr(participant, "type_code") and participant.type_code == "LOC":
                if hasattr(participant, "participant_role") and participant.participant_role:
                    role = participant.participant_role

                    # Generate location ID from role ID - REQUIRED
                    location_id = None
                    if hasattr(role, "id") and role.id:
                        for id_elem in role.id:
                            if id_elem.root:
                                location_id = self._generate_location_id(id_elem.root, id_elem.extension)
                                break

                    if not location_id:
                        raise ValueError("Cannot create Location reference: missing location identifier")

                    # Extract location name from playingEntity
                    display = None
                    if hasattr(role, "playing_entity") and role.playing_entity:
                        entity = role.playing_entity
                        if hasattr(entity, "name"):
                            if isinstance(entity.name, str):
                                display = entity.name
                            elif hasattr(entity.name, "value"):
                                display = entity.name.value

                    # Create location reference (or would have raised error above)
                    location_ref: JSONObject = {
                        "reference": f"{FHIRCodes.ResourceTypes.LOCATION}/{location_id}"
                    }
                    if display:
                        location_ref["display"] = display

                    return location_ref

        return None

    def _extract_devices(
        self,
        participants: list,
        procedure_status: str | None = None
    ) -> JSONObject | None:
        """Extract FHIR devices from C-CDA participants.

        Looks for Product Instance participants (typeCode="DEV") and converts
        them to FHIR Device resources. Also creates focalDevice entries
        in the Procedure resource.

        Args:
            participants: List of C-CDA participant elements
            procedure_status: C-CDA procedure status code for device status inference

        Returns:
            Dictionary with 'devices' (list of Device resources) and
            'focal_devices' (list of focalDevice entries), or None
        """
        from ccda_to_fhir.converters.device import DeviceConverter

        # Product Instance template ID
        product_instance_template = "2.16.840.1.113883.10.20.22.4.37"

        device_converter = DeviceConverter()
        devices: list[FHIRResourceDict] = []
        focal_devices: list[JSONObject] = []

        for participant in participants:
            # Look for device participants (typeCode="DEV")
            if hasattr(participant, "type_code") and participant.type_code == "DEV":
                if hasattr(participant, "participant_role") and participant.participant_role:
                    role = participant.participant_role

                    # Check if this is a Product Instance (has template ID)
                    is_product_instance = False
                    if hasattr(role, "template_id") and role.template_id:
                        for template in role.template_id:
                            if template.root == product_instance_template:
                                is_product_instance = True
                                break

                    # Only process Product Instance devices
                    # (assignedAuthoringDevice is handled separately in author processing)
                    if is_product_instance:
                        # Get patient reference from registry
                        patient_ref = None
                        if self.reference_registry:
                            patient_ref = self.reference_registry.get_patient_reference()

                        # Convert Product Instance to Device
                        device = device_converter.convert_product_instance(
                            role,
                            patient_reference=patient_ref,
                            procedure_status=procedure_status
                        )

                        # Register device resource with reference registry
                        if self.reference_registry:
                            self.reference_registry.register_resource(device)

                        # Store device resource
                        devices.append(device)

                        # Create focalDevice entry for Procedure
                        focal_device: JSONObject = {
                            "manipulated": {
                                "reference": f"{FHIRCodes.ResourceTypes.DEVICE}/{device['id']}"
                            }
                        }

                        # Infer action from device type or procedure code
                        # For implantable devices, use "implantation"
                        if patient_ref:
                            focal_device["action"] = {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "129337003",
                                        "display": "Implantation"
                                    }
                                ]
                            }

                        focal_devices.append(focal_device)

        if not devices:
            return None

        return {
            "devices": devices,
            "focal_devices": focal_devices
        }

    def _extract_recorder(self, authors: list) -> JSONObject | None:
        """Extract FHIR recorder from C-CDA authors.

        Uses the latest author by timestamp as the recorder.

        Args:
            authors: List of C-CDA author elements

        Returns:
            FHIR recorder reference or None
        """
        if not authors or len(authors) == 0:
            return None

        # Filter authors with time
        authors_with_time = [
            a for a in authors
            if hasattr(a, 'time') and a.time and a.time.value
        ]

        if not authors_with_time:
            return None

        # Get latest author by timestamp
        latest_author = max(authors_with_time, key=lambda a: a.time.value)

        if hasattr(latest_author, "assigned_author") and latest_author.assigned_author:
            assigned_author = latest_author.assigned_author

            # Check for practitioner (assigned_person)
            if hasattr(assigned_author, "assigned_person") and assigned_author.assigned_person:
                if hasattr(assigned_author, "id") and assigned_author.id:
                    for id_elem in assigned_author.id:
                        if id_elem.root:
                            pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                            return {
                                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                            }

            # Check for device (assigned_authoring_device)
            elif hasattr(assigned_author, "assigned_authoring_device") and assigned_author.assigned_authoring_device:
                if hasattr(assigned_author, "id") and assigned_author.id:
                    for id_elem in assigned_author.id:
                        if id_elem.root:
                            device_id = self._generate_device_id(id_elem.root, id_elem.extension)
                            return {
                                "reference": f"{FHIRCodes.ResourceTypes.DEVICE}/{device_id}"
                            }

        return None

    def _extract_reasons(self, entry_relationships: list) -> dict[str, list]:
        """Extract FHIR reason codes and references from C-CDA entry relationships.

        Handles two patterns:
        1. RSON observation with inline code value → reasonCode
        2. RSON observation that IS a Problem Observation → reasonReference to Condition

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            Dict with "codes" and "references" lists
        """
        reason_codes = []
        reason_refs = []

        for entry_rel in entry_relationships:
            # Look for RSON (reason) relationships
            if hasattr(entry_rel, "type_code") and entry_rel.type_code == "RSON":
                if hasattr(entry_rel, "observation") and entry_rel.observation:
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

                        # Skip if we couldn't generate a valid ID
                        if not condition_id:
                            continue

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
                            if hasattr(obs, "value") and obs.value:
                                value = obs.value
                                if hasattr(value, "code") and value.code:
                                    reason_code = self.create_codeable_concept(
                                        code=value.code,
                                        code_system=value.code_system if hasattr(value, "code_system") else None,
                                        display_name=value.display_name if hasattr(value, "display_name") else None,
                                    )
                                    if reason_code:
                                        reason_codes.append(reason_code)
                    else:
                        # Extract reason code from observation value (existing logic)
                        if hasattr(obs, "value") and obs.value:
                            value = obs.value
                            if hasattr(value, "code") and value.code:
                                reason_code = self.create_codeable_concept(
                                    code=value.code,
                                    code_system=value.code_system if hasattr(value, "code_system") else None,
                                    display_name=value.display_name if hasattr(value, "display_name") else None,
                                )
                                if reason_code:
                                    reason_codes.append(reason_code)

        return {"codes": reason_codes, "references": reason_refs}

    def _generate_condition_id_from_observation(self, observation) -> str | None:
        """Generate a Condition resource ID from a Problem Observation.

        Uses the same ID generation logic as ConditionConverter to ensure
        consistent references to Condition resources.

        Args:
            observation: Problem Observation with ID

        Returns:
            Condition resource ID string, or None if no identifiers available
        """
        if hasattr(observation, "id") and observation.id:
            for id_elem in observation.id:
                if hasattr(id_elem, "root") and id_elem.root:
                    extension = id_elem.extension if hasattr(id_elem, "extension") else None
                    return self._generate_condition_id(id_elem.root, extension)

        logger.warning(
            "Cannot generate Condition ID from Problem Observation: no identifiers provided. "
            "Skipping reasonReference."
        )
        return None

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

    def _extract_outcomes(self, entry_relationships: list) -> JSONObject | None:
        """Extract FHIR outcome from C-CDA entry relationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            FHIR outcome CodeableConcept or None
        """
        # Look for outcome observations (typically typeCode="OUTC" or result observations)
        for entry_rel in entry_relationships:
            if hasattr(entry_rel, "type_code") and entry_rel.type_code in ["OUTC", "COMP"]:
                if hasattr(entry_rel, "observation") and entry_rel.observation:
                    obs = entry_rel.observation
                    if hasattr(obs, "value") and obs.value:
                        value = obs.value
                        if hasattr(value, "code") and value.code:
                            return self.create_codeable_concept(
                                code=value.code,
                                code_system=value.code_system if hasattr(value, "code_system") else None,
                                display_name=value.display_name if hasattr(value, "display_name") else None,
                            )

        return None

    def _extract_complications(self, entry_relationships: list) -> list[JSONObject]:
        """Extract FHIR complications from C-CDA entry relationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            List of FHIR complication CodeableConcepts
        """
        complications = []

        for entry_rel in entry_relationships:
            # Look for COMP (complication) relationships
            if hasattr(entry_rel, "type_code") and entry_rel.type_code == "COMP":
                if hasattr(entry_rel, "observation") and entry_rel.observation:
                    obs = entry_rel.observation
                    if hasattr(obs, "value") and obs.value:
                        value = obs.value
                        if hasattr(value, "code") and value.code:
                            complication = self.create_codeable_concept(
                                code=value.code,
                                code_system=value.code_system if hasattr(value, "code_system") else None,
                                display_name=value.display_name if hasattr(value, "display_name") else None,
                            )
                            if complication:
                                complications.append(complication)

        return complications

    def _extract_followups(self, entry_relationships: list) -> list[JSONObject]:
        """Extract FHIR follow-ups from C-CDA entry relationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            List of FHIR follow-up CodeableConcepts
        """
        followups = []

        for entry_rel in entry_relationships:
            # Look for SPRT (support) relationships which typically contain follow-up instructions
            if hasattr(entry_rel, "type_code") and entry_rel.type_code == "SPRT":
                if hasattr(entry_rel, "act") and entry_rel.act:
                    act = entry_rel.act
                    if hasattr(act, "code") and act.code:
                        followup = self.create_codeable_concept(
                            code=act.code.code if hasattr(act.code, "code") else None,
                            code_system=act.code.code_system if hasattr(act.code, "code_system") else None,
                            display_name=act.code.display_name if hasattr(act.code, "display_name") else None,
                        )
                        if followup:
                            followups.append(followup)

        return followups

    def _extract_notes(self, procedure) -> list[JSONObject]:
        """Extract FHIR notes from C-CDA procedure.

        Args:
            procedure: The C-CDA procedure element

        Returns:
            List of FHIR Annotation objects
        """
        notes = []

        # Extract from text element
        if hasattr(procedure, "text") and procedure.text:
            text_content = None
            if isinstance(procedure.text, str):
                text_content = procedure.text
            elif hasattr(procedure.text, "value"):
                text_content = procedure.text.value
            elif hasattr(procedure.text, "reference"):
                # Could resolve reference here if needed
                pass

            if text_content:
                notes.append({"text": text_content})

        # Extract from Comment Activity entries
        if hasattr(procedure, "entry_relationship") and procedure.entry_relationship:
            for entry_rel in procedure.entry_relationship:
                # Look for Comment Activity (template 2.16.840.1.113883.10.20.22.4.64)
                if hasattr(entry_rel, "act") and entry_rel.act:
                    act = entry_rel.act
                    # Check if it's a Comment Activity
                    if hasattr(act, "template_id") and act.template_id:
                        for template in act.template_id:
                            if template.root == "2.16.840.1.113883.10.20.22.4.64":
                                # This is a Comment Activity
                                if hasattr(act, "text") and act.text:
                                    comment_text = None
                                    if isinstance(act.text, str):
                                        comment_text = act.text
                                    elif hasattr(act.text, "value"):
                                        comment_text = act.text.value

                                    if comment_text:
                                        notes.append({"text": comment_text})
                                break

        return notes

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

    def _generate_organization_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Organization ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Organization", root, extension)

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

    def _generate_device_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Device ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Device", root, extension)

    def _convert_body_site_with_qualifiers(
        self, code: CD
    ) -> JSONObject | None:
        """Convert C-CDA targetSiteCode with qualifiers to FHIR bodySite CodeableConcept.

        This method handles body site codes with laterality qualifiers. Per C-CDA standard,
        laterality (left/right) can be specified using qualifier elements within targetSiteCode.

        Example C-CDA:
            <targetSiteCode code="71854001" displayName="Colon structure"
                           codeSystem="2.16.840.1.113883.6.96">
              <qualifier>
                <name code="272741003" displayName="Laterality"
                      codeSystem="2.16.840.1.113883.6.96"/>
                <value code="7771000" displayName="Left"
                       codeSystem="2.16.840.1.113883.6.96"/>
              </qualifier>
            </targetSiteCode>

        Args:
            code: The C-CDA targetSiteCode element (CD type)

        Returns:
            FHIR CodeableConcept with bodySite and laterality coding, or None
        """
        if not code:
            return None

        # Start with basic code conversion using existing method
        # Extract translations if present
        translations = []
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if isinstance(trans, (CD, dict)):
                    trans_code = trans.code if hasattr(trans, "code") else trans.get("code")
                    trans_system = trans.code_system if hasattr(trans, "code_system") else trans.get("code_system")
                    trans_display = trans.display_name if hasattr(trans, "display_name") else trans.get("display_name")

                    if trans_code and trans_system:
                        translations.append({
                            "code": trans_code,
                            "code_system": trans_system,
                            "display_name": trans_display,
                        })

        # Get original text if present
        original_text = None
        if hasattr(code, "original_text") and code.original_text:
            original_text = self.extract_original_text(code.original_text, section=None)

        # Use display_name as text if original_text not available
        if not original_text and code.display_name:
            original_text = code.display_name

        codeable_concept = self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system,
            display_name=code.display_name,
            original_text=original_text,
            translations=translations,
        )

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
            # Format: "{laterality} {site}" (e.g., "Left Colon structure")
            if laterality_value.display_name and code.display_name:
                codeable_concept["text"] = f"{laterality_value.display_name} {code.display_name}"
            elif laterality_value.display_name and "text" in codeable_concept:
                codeable_concept["text"] = f"{laterality_value.display_name} {codeable_concept['text']}"

        return codeable_concept
