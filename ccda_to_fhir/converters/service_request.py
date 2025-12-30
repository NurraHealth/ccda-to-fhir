"""ServiceRequest converter: C-CDA Planned Procedure/Act to FHIR ServiceRequest resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act as CCDAAct
from ccda_to_fhir.ccda.models.datatypes import CD, IVL_TS
from ccda_to_fhir.ccda.models.procedure import Procedure as CCDAProcedure
from ccda_to_fhir.constants import (
    SERVICE_REQUEST_MOOD_TO_INTENT,
    SERVICE_REQUEST_PRIORITY_TO_FHIR,
    SERVICE_REQUEST_STATUS_TO_FHIR,
    FHIRCodes,
    TemplateIds,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class ServiceRequestConverter(BaseConverter[CCDAProcedure | CCDAAct]):
    """Convert C-CDA Planned Procedure/Act to FHIR ServiceRequest resource.

    This converter handles the mapping from C-CDA Planned Procedure and Planned Act
    templates to FHIR R4B ServiceRequest resources.

    Supports:
    - Planned Procedure (V2): 2.16.840.1.113883.10.20.22.4.41
    - Planned Act (V2): 2.16.840.1.113883.10.20.22.4.39

    **CRITICAL**: Only converts procedures/acts with moodCode in {INT, RQO, PRP, ARQ, PRMS}.
    Procedures with moodCode=EVN (Event) or moodCode=GOL (Goal) must use
    Procedure or Goal converters instead.

    Reference: docs/mapping/18-service-request.md
    """

    def convert(
        self, procedure: CCDAProcedure | CCDAAct, section=None
    ) -> FHIRResourceDict:
        """Convert a C-CDA Planned Procedure/Act to a FHIR ServiceRequest resource.

        Args:
            procedure: The C-CDA Planned Procedure or Planned Act element
            section: The C-CDA Section containing this procedure (for narrative)

        Returns:
            FHIR ServiceRequest resource as a dictionary

        Raises:
            ValueError: If the procedure lacks required data or has invalid moodCode
        """
        # Validate moodCode - CRITICAL for distinguishing ServiceRequest from Procedure/Goal
        if not hasattr(procedure, "mood_code") or not procedure.mood_code:
            raise ValueError("Planned Procedure/Act must have a moodCode attribute")

        mood_code = procedure.mood_code.upper()
        valid_mood_codes = {"INT", "RQO", "PRP", "ARQ", "PRMS"}

        if mood_code not in valid_mood_codes:
            if mood_code == "EVN":
                raise ValueError(
                    "moodCode=EVN indicates completed procedure; use Procedure converter instead"
                )
            elif mood_code == "GOL":
                raise ValueError(
                    "moodCode=GOL indicates goal; use Goal converter instead"
                )
            else:
                raise ValueError(
                    f"Invalid moodCode '{mood_code}' for ServiceRequest; "
                    f"expected one of {valid_mood_codes}"
                )

        # Validate required code element
        if not procedure.code:
            raise ValueError("Planned Procedure/Act must have a code")

        has_valid_code = (
            hasattr(procedure.code, "code")
            and procedure.code.code
            and not (
                hasattr(procedure.code, "null_flavor") and procedure.code.null_flavor
            )
        )

        if not has_valid_code:
            raise ValueError("Planned Procedure/Act code must have a valid code value")

        # Build FHIR ServiceRequest resource
        fhir_service_request: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.SERVICE_REQUEST,
        }

        # Add US Core profile
        fhir_service_request["meta"] = {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"
            ]
        }

        # Generate ID from procedure identifier
        if procedure.id and len(procedure.id) > 0:
            first_id = procedure.id[0]
            fhir_service_request["id"] = self._generate_service_request_id(
                first_id.root, first_id.extension
            )

        # Identifiers
        if procedure.id:
            fhir_service_request["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in procedure.id
                if id_elem.root
            ]

        # Status (required) - map from statusCode
        status = self._map_status(procedure.status_code)
        fhir_service_request["status"] = status

        # Intent (required) - map from moodCode
        intent = self._map_intent(mood_code)
        fhir_service_request["intent"] = intent

        # Category (must support) - infer from code system
        category = self._infer_category(procedure.code)
        if category:
            fhir_service_request["category"] = [category]

        # Code (required)
        fhir_service_request["code"] = self._convert_code(procedure.code)

        # Subject (required) - patient reference
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create ServiceRequest without patient reference."
            )
        fhir_service_request["subject"] = self.reference_registry.get_patient_reference()

        # Encounter (must support)
        if self.reference_registry:
            encounter_ref = self.reference_registry.get_encounter_reference()
            if encounter_ref:
                fhir_service_request["encounter"] = encounter_ref

        # Occurrence[x] (must support) - from effectiveTime
        if procedure.effective_time:
            occurrence = self._convert_occurrence(procedure.effective_time)
            if occurrence:
                if isinstance(occurrence, dict) and (
                    "start" in occurrence or "end" in occurrence
                ):
                    fhir_service_request["occurrencePeriod"] = occurrence
                else:
                    fhir_service_request["occurrenceDateTime"] = occurrence

        # AuthoredOn (must support) - from author/time
        if procedure.author:
            authored_on = self._extract_authored_on(procedure.author)
            if authored_on:
                fhir_service_request["authoredOn"] = authored_on

        # Requester (must support) - from author/assignedAuthor
        if procedure.author:
            requester = self._extract_requester(procedure.author)
            if requester:
                fhir_service_request["requester"] = requester

        # Performer - from performer/assignedEntity
        if procedure.performer:
            performers = self._extract_performers(procedure.performer)
            if performers:
                fhir_service_request["performer"] = performers

        # PerformerType - from performer/functionCode
        if procedure.performer:
            performer_type = self._extract_performer_type(procedure.performer)
            if performer_type:
                fhir_service_request["performerType"] = performer_type

        # Priority - from priorityCode
        if hasattr(procedure, "priority_code") and procedure.priority_code:
            priority = self._map_priority(procedure.priority_code)
            if priority:
                fhir_service_request["priority"] = priority

        # Body site - from targetSiteCode
        if hasattr(procedure, "target_site_code") and procedure.target_site_code:
            body_sites = []
            for site_code in procedure.target_site_code:
                if site_code.code:
                    body_site = self._convert_code(site_code)
                    if body_site:
                        body_sites.append(body_site)
            if body_sites:
                fhir_service_request["bodySite"] = body_sites

        # Reason codes and references - from entryRelationship
        if procedure.entry_relationship:
            reasons = self._extract_reasons(procedure.entry_relationship)
            if reasons.get("codes"):
                fhir_service_request["reasonCode"] = reasons["codes"]
            if reasons.get("references"):
                fhir_service_request["reasonReference"] = reasons["references"]

        # Patient instruction - from entryRelationship with Instruction template
        if procedure.entry_relationship:
            patient_instruction = self._extract_patient_instruction(
                procedure.entry_relationship
            )
            if patient_instruction:
                fhir_service_request["patientInstruction"] = patient_instruction

        # Notes
        notes = self._extract_notes(procedure)
        if notes:
            fhir_service_request["note"] = notes

        # Narrative
        narrative = self._generate_narrative(entry=procedure, section=section)
        if narrative:
            fhir_service_request["text"] = narrative

        return fhir_service_request

    def _generate_service_request_id(
        self, root: str | None, extension: str | None
    ) -> str:
        """Generate a FHIR ServiceRequest ID from C-CDA identifiers.

        Uses centralized ID generation for consistent UUID caching and handling.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("ServiceRequest", root, extension)

    def _map_status(self, status_code) -> str:
        """Map C-CDA status code to FHIR ServiceRequest status.

        Handles nullFlavor per C-CDA on FHIR IG ConceptMap CF-NullFlavorDataAbsentReason.

        Args:
            status_code: The C-CDA status code

        Returns:
            FHIR ServiceRequest status code
        """
        if not status_code:
            return FHIRCodes.ServiceRequestStatus.ACTIVE

        # Check for nullFlavor - per C-CDA on FHIR IG
        if hasattr(status_code, 'null_flavor') and status_code.null_flavor:
            null_flavor_upper = status_code.null_flavor.upper()
            if null_flavor_upper == 'UNK':
                return FHIRCodes.ServiceRequestStatus.UNKNOWN
            # For planned procedures, other nullFlavors default to active
            return FHIRCodes.ServiceRequestStatus.ACTIVE

        if not status_code.code:
            return FHIRCodes.ServiceRequestStatus.ACTIVE

        ccda_status = status_code.code.lower()
        return SERVICE_REQUEST_STATUS_TO_FHIR.get(
            ccda_status, FHIRCodes.ServiceRequestStatus.ACTIVE
        )

    def _map_intent(self, mood_code: str) -> str:
        """Map C-CDA moodCode to FHIR ServiceRequest intent.

        Args:
            mood_code: The C-CDA moodCode (already validated)

        Returns:
            FHIR ServiceRequest intent code
        """
        return SERVICE_REQUEST_MOOD_TO_INTENT.get(
            mood_code, FHIRCodes.ServiceRequestIntent.PLAN
        )

    def _map_priority(self, priority_code) -> str | None:
        """Map C-CDA priorityCode to FHIR ServiceRequest priority.

        Args:
            priority_code: The C-CDA priorityCode

        Returns:
            FHIR ServiceRequest priority code or None
        """
        if not priority_code or not hasattr(priority_code, "code"):
            return None

        ccda_priority = priority_code.code.upper()
        return SERVICE_REQUEST_PRIORITY_TO_FHIR.get(ccda_priority)

    def _infer_category(self, code: CD) -> JSONObject | None:
        """Infer ServiceRequest category from procedure code.

        Args:
            code: The C-CDA procedure code

        Returns:
            FHIR CodeableConcept for category or None
        """
        if not code or not code.code_system:
            return None

        # Infer category based on code system and code ranges
        code_system = code.code_system
        code_value = code.code if hasattr(code, "code") else None

        # LOINC codes - typically lab procedures
        if code_system == "2.16.840.1.113883.6.1":
            return {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "108252007",
                        "display": "Laboratory procedure",
                    }
                ]
            }

        # CPT codes
        if code_system == "2.16.840.1.113883.6.12" and code_value:
            try:
                cpt_code = int(code_value)
                # Radiology range: 70000-79999
                if 70000 <= cpt_code <= 79999:
                    return {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "363679005",
                                "display": "Imaging",
                            }
                        ]
                    }
                # Surgery range: 10000-69999
                elif 10000 <= cpt_code <= 69999:
                    return {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "387713003",
                                "display": "Surgical procedure",
                            }
                        ]
                    }
            except ValueError:
                pass

        # SNOMED CT codes - check for specific procedure types
        if code_system == "2.16.840.1.113883.6.96" and code_value:
            # Counseling
            if code_value == "409063005":
                return {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "409063005",
                            "display": "Counselling",
                        }
                    ]
                }
            # Education
            if code_value == "409073007":
                return {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "409073007",
                            "display": "Education",
                        }
                    ]
                }

        # Default category: Diagnostic procedure
        return {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "103693007",
                    "display": "Diagnostic procedure",
                }
            ]
        }

    def _convert_code(self, code: CD) -> JSONObject:
        """Convert C-CDA code to FHIR CodeableConcept.

        Args:
            code: The C-CDA code

        Returns:
            FHIR CodeableConcept
        """
        # Extract translations if present
        translations = []
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if isinstance(trans, (CD, dict)):
                    trans_code = (
                        trans.code if hasattr(trans, "code") else trans.get("code")
                    )
                    trans_system = (
                        trans.code_system
                        if hasattr(trans, "code_system")
                        else trans.get("code_system")
                    )
                    trans_display = (
                        trans.display_name
                        if hasattr(trans, "display_name")
                        else trans.get("display_name")
                    )

                    if trans_code and trans_system:
                        translations.append(
                            {
                                "code": trans_code,
                                "code_system": trans_system,
                                "display_name": trans_display,
                            }
                        )

        # Get original text
        original_text = None
        if hasattr(code, "original_text") and code.original_text:
            original_text = self.extract_original_text(code.original_text, section=None)

        if not original_text and code.display_name:
            original_text = code.display_name

        return self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system,
            display_name=code.display_name,
            original_text=original_text,
            translations=translations,
        )

    def _convert_occurrence(self, effective_time: IVL_TS | str) -> JSONObject | str | None:
        """Convert C-CDA effectiveTime to FHIR occurrence[x].

        Args:
            effective_time: The C-CDA effectiveTime

        Returns:
            FHIR occurrenceDateTime (string) or occurrencePeriod (dict), or None
        """
        if isinstance(effective_time, str):
            return self.convert_date(effective_time)

        if hasattr(effective_time, "value") and effective_time.value:
            return self.convert_date(effective_time.value)

        # Handle period
        period: JSONObject = {}

        if hasattr(effective_time, "low") and effective_time.low:
            low_value = (
                effective_time.low.value
                if hasattr(effective_time.low, "value")
                else effective_time.low
            )
            if low_value:
                converted_low = self.convert_date(str(low_value))
                if converted_low:
                    period["start"] = converted_low

        if hasattr(effective_time, "high") and effective_time.high:
            high_value = (
                effective_time.high.value
                if hasattr(effective_time.high, "value")
                else effective_time.high
            )
            if high_value:
                converted_high = self.convert_date(str(high_value))
                if converted_high:
                    period["end"] = converted_high

        return period if period else None

    def _extract_authored_on(self, authors: list) -> str | None:
        """Extract authoredOn from C-CDA authors.

        Uses the latest author timestamp.

        Args:
            authors: List of C-CDA author elements

        Returns:
            FHIR dateTime string or None
        """
        if not authors or len(authors) == 0:
            return None

        # Get latest author by timestamp
        authors_with_time = [
            a for a in authors if hasattr(a, "time") and a.time and a.time.value
        ]

        if not authors_with_time:
            return None

        latest_author = max(authors_with_time, key=lambda a: a.time.value)
        return self.convert_date(latest_author.time.value)

    def _extract_requester(self, authors: list) -> JSONObject | None:
        """Extract requester reference from C-CDA authors.

        Uses the latest author.

        Args:
            authors: List of C-CDA author elements

        Returns:
            FHIR Reference or None
        """
        if not authors or len(authors) == 0:
            return None

        authors_with_time = [
            a for a in authors if hasattr(a, "time") and a.time and a.time.value
        ]

        if not authors_with_time:
            return None

        latest_author = max(authors_with_time, key=lambda a: a.time.value)

        if (
            hasattr(latest_author, "assigned_author")
            and latest_author.assigned_author
        ):
            assigned_author = latest_author.assigned_author

            if (
                hasattr(assigned_author, "assigned_person")
                and assigned_author.assigned_person
            ):
                if hasattr(assigned_author, "id") and assigned_author.id:
                    for id_elem in assigned_author.id:
                        if id_elem.root:
                            pract_id = self._generate_practitioner_id(
                                id_elem.root, id_elem.extension
                            )
                            return {
                                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                            }

        return None

    def _extract_performers(self, performers: list) -> list[JSONObject]:
        """Extract performer references from C-CDA performers.

        Args:
            performers: List of C-CDA performer elements

        Returns:
            List of FHIR References
        """
        fhir_performers = []

        for performer in performers:
            if not hasattr(performer, "assigned_entity") or not performer.assigned_entity:
                continue

            assigned_entity = performer.assigned_entity

            if hasattr(assigned_entity, "id") and assigned_entity.id:
                for id_elem in assigned_entity.id:
                    if id_elem.root:
                        pract_id = self._generate_practitioner_id(
                            id_elem.root, id_elem.extension
                        )
                        fhir_performers.append(
                            {
                                "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                            }
                        )
                        break

        return fhir_performers

    def _extract_performer_type(self, performers: list) -> JSONObject | None:
        """Extract performerType from C-CDA performer functionCode.

        Args:
            performers: List of C-CDA performer elements

        Returns:
            FHIR CodeableConcept or None
        """
        for performer in performers:
            if hasattr(performer, "function_code") and performer.function_code:
                return self._convert_code(performer.function_code)

        return None

    def _extract_reasons(self, entry_relationships: list) -> dict[str, list]:
        """Extract reason codes and references from entryRelationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            Dict with "codes" and "references" lists
        """
        reason_codes = []
        reason_refs = []

        for entry_rel in entry_relationships:
            if hasattr(entry_rel, "type_code") and entry_rel.type_code == "RSON":
                if hasattr(entry_rel, "observation") and entry_rel.observation:
                    obs = entry_rel.observation

                    # Check if this is a Problem Observation
                    is_problem_obs = False
                    if hasattr(obs, "template_id") and obs.template_id:
                        for template in obs.template_id:
                            if (
                                hasattr(template, "root")
                                and template.root == TemplateIds.PROBLEM_OBSERVATION
                            ):
                                is_problem_obs = True
                                break

                    if is_problem_obs:
                        # Check if Condition resource exists
                        condition_id = self._generate_condition_id_from_observation(obs)

                        # Skip if we couldn't generate a valid ID
                        if not condition_id:
                            continue

                        if self.reference_registry and self.reference_registry.has_resource(
                            FHIRCodes.ResourceTypes.CONDITION, condition_id
                        ):
                            reason_refs.append(
                                {
                                    "reference": f"{FHIRCodes.ResourceTypes.CONDITION}/{condition_id}"
                                }
                            )
                        else:
                            # Use reason code instead
                            if hasattr(obs, "value") and obs.value:
                                value = obs.value
                                if hasattr(value, "code") and value.code:
                                    reason_code = self.create_codeable_concept(
                                        code=value.code,
                                        code_system=(
                                            value.code_system
                                            if hasattr(value, "code_system")
                                            else None
                                        ),
                                        display_name=(
                                            value.display_name
                                            if hasattr(value, "display_name")
                                            else None
                                        ),
                                    )
                                    if reason_code:
                                        reason_codes.append(reason_code)
                    else:
                        # Extract reason code from observation value
                        if hasattr(obs, "value") and obs.value:
                            value = obs.value
                            if hasattr(value, "code") and value.code:
                                reason_code = self.create_codeable_concept(
                                    code=value.code,
                                    code_system=(
                                        value.code_system
                                        if hasattr(value, "code_system")
                                        else None
                                    ),
                                    display_name=(
                                        value.display_name
                                        if hasattr(value, "display_name")
                                        else None
                                    ),
                                )
                                if reason_code:
                                    reason_codes.append(reason_code)

        return {"codes": reason_codes, "references": reason_refs}

    def _generate_condition_id_from_observation(self, observation) -> str | None:
        """Generate Condition ID from Problem Observation.

        Args:
            observation: Problem Observation with ID

        Returns:
            Condition resource ID string, or None if no identifiers available
        """
        if hasattr(observation, "id") and observation.id:
            for id_elem in observation.id:
                if hasattr(id_elem, "root") and id_elem.root:
                    extension = (
                        id_elem.extension if hasattr(id_elem, "extension") else None
                    )
                    return self._generate_condition_id(id_elem.root, extension)

        logger.warning(
            "Cannot generate Condition ID from Problem Observation: no identifiers provided. "
            "Skipping reasonReference."
        )
        return None

    def _generate_condition_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Condition ID from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Condition", root, extension)

    def _extract_patient_instruction(self, entry_relationships: list) -> str | None:
        """Extract patient instruction from entryRelationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            Patient instruction text or None
        """
        for entry_rel in entry_relationships:
            # Look for Instruction acts with typeCode="SUBJ" and inversionInd="true"
            if (
                hasattr(entry_rel, "type_code")
                and entry_rel.type_code == "SUBJ"
                and hasattr(entry_rel, "inversion_ind")
                and entry_rel.inversion_ind
            ):
                if hasattr(entry_rel, "act") and entry_rel.act:
                    act = entry_rel.act

                    # Check if this is an Instruction template
                    is_instruction = False
                    if hasattr(act, "template_id") and act.template_id:
                        for template in act.template_id:
                            if (
                                hasattr(template, "root")
                                and template.root == TemplateIds.INSTRUCTION_ACT
                            ):
                                is_instruction = True
                                break

                    if is_instruction and hasattr(act, "text") and act.text:
                        if isinstance(act.text, str):
                            return act.text
                        elif hasattr(act.text, "value"):
                            return act.text.value

        return None

    def _extract_notes(self, procedure) -> list[JSONObject]:
        """Extract notes from procedure.

        Args:
            procedure: The C-CDA procedure element

        Returns:
            List of FHIR Annotation objects
        """
        notes = []

        if hasattr(procedure, "text") and procedure.text:
            text_content = None
            if isinstance(procedure.text, str):
                text_content = procedure.text
            elif hasattr(procedure.text, "value"):
                text_content = procedure.text.value

            if text_content:
                notes.append({"text": text_content})

        return notes

    def _generate_practitioner_id(
        self, root: str | None, extension: str | None
    ) -> str:
        """Generate FHIR Practitioner ID from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID string
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Practitioner", root, extension)
