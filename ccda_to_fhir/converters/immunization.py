"""Immunization converter: C-CDA Immunization Activity to FHIR Immunization resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CD, CE, IVL_PQ, IVL_TS, PQ, TS
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.constants import (
    NO_IMMUNIZATION_REASON_CODES,
    FHIRCodes,
    FHIRSystems,
    TemplateIds,
    TypeCodes,
    V2ParticipationFunctionCodes,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter
from .medication_request import MedicationRequestConverter


class ImmunizationConverter(BaseConverter[SubstanceAdministration]):
    """Convert C-CDA Immunization Activity to FHIR Immunization resource.

    This converter handles the mapping from C-CDA SubstanceAdministration
    (Immunization Activity template 2.16.840.1.113883.10.20.22.4.52) to a
    FHIR R4B Immunization resource, including vaccine code, administration date,
    dose quantity, lot number, manufacturer, route, site, and reactions.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-immunizations.html
    """

    def __init__(self, *args, **kwargs):
        """Initialize the immunization converter."""
        super().__init__(*args, **kwargs)

    def convert(self, substance_admin: SubstanceAdministration, section=None) -> tuple[FHIRResourceDict, list[FHIRResourceDict]]:
        """Convert a C-CDA Immunization Activity to FHIR resources.

        Args:
            substance_admin: The C-CDA SubstanceAdministration (Immunization Activity)
            section: The C-CDA Section containing this immunization (for narrative)

        Returns:
            Tuple of (immunization, reaction_observations):
            - immunization: FHIR Immunization resource
            - reaction_observations: List of FHIR Observation resources for reactions

        Raises:
            ValueError: If the substance administration lacks required data
        """
        # Validation
        if not substance_admin.consumable:
            raise ValueError("Immunization Activity must have a consumable (vaccine)")

        immunization: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.IMMUNIZATION,
        }

        # 1. Generate ID from substance administration identifier
        immunization_id = None
        if substance_admin.id and len(substance_admin.id) > 0:
            first_id = substance_admin.id[0]
            immunization_id = self._generate_immunization_id(
                first_id.root, first_id.extension
            )
            immunization["id"] = immunization_id

        # Default ID if not available
        if not immunization_id:
            from ccda_to_fhir.id_generator import generate_id
            immunization_id = generate_id()
            immunization["id"] = immunization_id

        # 2. Identifiers
        if substance_admin.id:
            identifiers = []
            for id_elem in substance_admin.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                immunization["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(substance_admin)
        immunization["status"] = status

        # 4. VaccineCode (required) - from consumable
        # Always present (method returns data-absent-reason if no code available)
        immunization["vaccineCode"] = self._extract_vaccine_code(substance_admin)

        # 5. Patient (subject reference)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Immunization without patient reference."
            )
        immunization["patient"] = self.reference_registry.get_patient_reference()

        # 6. OccurrenceDateTime - from effectiveTime (required field)
        occurrence_date = self._extract_occurrence_date(substance_admin)
        if occurrence_date:
            immunization["occurrenceDateTime"] = occurrence_date
        else:
            # Fallback: Use occurrenceString when date is unavailable
            # This handles cases with nullFlavor on effectiveTime
            immunization["occurrenceString"] = "unknown"

        # 7. DoseQuantity - from doseQuantity
        dose_quantity = self._extract_dose_quantity(substance_admin)
        if dose_quantity:
            immunization["doseQuantity"] = dose_quantity

        # 8. Lot number - from manufacturedMaterial.lotNumberText
        lot_number = self._extract_lot_number(substance_admin)
        if lot_number:
            immunization["lotNumber"] = lot_number

        # 9. Manufacturer - from manufacturerOrganization
        manufacturer = self._extract_manufacturer(substance_admin)
        if manufacturer:
            immunization["manufacturer"] = manufacturer

        # 10. Route - from routeCode
        route = self._extract_route(substance_admin)
        if route:
            immunization["route"] = route

        # 11. Site - from approachSiteCode
        site = self._extract_site(substance_admin)
        if site:
            immunization["site"] = site

        # 12. ReasonCode / StatusReason - from indication (RSON) entryRelationship
        # Complex not-given reason mapping: distinguish refusal reasons from clinical indications
        status_reasons, reason_codes = self._extract_reason_codes(substance_admin)

        # If negated (not-done), use statusReason for refusal reasons
        if status == FHIRCodes.Immunization.STATUS_NOT_DONE and status_reasons:
            # statusReason is single CodeableConcept, use first refusal reason
            immunization["statusReason"] = status_reasons[0]

        # Clinical indications go to reasonCode (only if NOT negated)
        if status != FHIRCodes.Immunization.STATUS_NOT_DONE and reason_codes:
            immunization["reasonCode"] = reason_codes

        # 13. ProtocolApplied - from repeatNumber
        protocol_applied = self._extract_protocol_applied(substance_admin)
        if protocol_applied:
            immunization["protocolApplied"] = protocol_applied

        # 14. Reactions - from reaction (MFST) entryRelationship
        # Returns both reaction objects (with references) and Observation resources
        reactions, reaction_observations = self._extract_reactions(substance_admin, immunization_id)
        if reactions:
            immunization["reaction"] = reactions

        # 15. Supporting observations - from SPRT entryRelationship
        # Returns Observation resources for evidence/supporting observations
        supporting_observations = self._extract_supporting_observations(substance_admin, immunization_id)

        # 16. Component observations - from COMP entryRelationship
        # Returns Observation resources for complications/adverse events
        component_observations = self._extract_component_observations(substance_admin, immunization_id)

        # 17. Performer - from performer
        performers = self._extract_performers(substance_admin)
        if performers:
            immunization["performer"] = performers

        # 18. Notes - from Comment Activity entryRelationship
        notes = self._extract_notes(substance_admin)
        if notes:
            immunization["note"] = notes

        # primarySource is optional in US Core STU6+ (0..1, Must Support)
        # C-CDA has no equivalent concept for indicating if data came from primary source
        # Per Must Support: include if known, omit if unknown
        # Omit the field rather than making false claims about provenance

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=substance_admin, section=section)
        if narrative:
            immunization["text"] = narrative

        # Collect all additional observations (reactions, supporting, and component observations)
        all_observations = reaction_observations + supporting_observations + component_observations

        return immunization, all_observations

    def _generate_immunization_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Immunization ID from C-CDA identifier.

        Uses centralized id_generator to ensure consistency across document.

        Args:
            root: The identifier root (OID or UUID)
            extension: The identifier extension

        Returns:
            Generated UUID string (cached for consistency within document)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Immunization", root, extension)

    def _determine_status(self, substance_admin: SubstanceAdministration) -> str:
        """Determine FHIR Immunization status from C-CDA statusCode.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR status code
        """
        # Default to completed
        status = FHIRCodes.Immunization.STATUS_COMPLETED

        if substance_admin.status_code and substance_admin.status_code.code:
            ccda_status = substance_admin.status_code.code.lower()

            # Map C-CDA status to FHIR status
            status_map = {
                "completed": FHIRCodes.Immunization.STATUS_COMPLETED,
                "active": FHIRCodes.Immunization.STATUS_COMPLETED,
                "aborted": FHIRCodes.Immunization.STATUS_NOT_DONE,
                "cancelled": FHIRCodes.Immunization.STATUS_NOT_DONE,
            }
            status = status_map.get(ccda_status, FHIRCodes.Immunization.STATUS_COMPLETED)

        # Check negationInd
        if substance_admin.negation_ind:
            status = FHIRCodes.Immunization.STATUS_NOT_DONE

        return status

    def _extract_vaccine_code(self, substance_admin: SubstanceAdministration) -> JSONObject:
        """Extract vaccine code from consumable.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR CodeableConcept for vaccine code (required field, always returns a value)
        """
        # Try to extract code from consumable
        vaccine_code = None
        if substance_admin.consumable:
            manufactured_product = substance_admin.consumable.manufactured_product
            if manufactured_product:
                manufactured_material = manufactured_product.manufactured_material
                if manufactured_material and manufactured_material.code:
                    code = manufactured_material.code
                    vaccine_code = self._convert_code_to_codeable_concept(code)

        # vaccineCode is required (1..1 cardinality)
        if not vaccine_code or not vaccine_code.get("coding"):
            raise ValueError(
                "Cannot create Immunization: vaccineCode is required. "
                "C-CDA Immunization Activity must have consumable/manufacturedProduct/manufacturedMaterial/code."
            )

        return vaccine_code

    def _extract_occurrence_date(self, substance_admin: SubstanceAdministration) -> str | None:
        """Extract occurrence date from effectiveTime.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            ISO date string or None
        """
        if not substance_admin.effective_time or len(substance_admin.effective_time) == 0:
            return None

        # Use the first effectiveTime (typically a timestamp or interval)
        effective_time = substance_admin.effective_time[0]

        # Extract value based on type
        if isinstance(effective_time, TS):
            if effective_time.value:
                return self.convert_date(effective_time.value)
        elif isinstance(effective_time, IVL_TS):
            # For intervals, use low (administration date) over high
            if effective_time.low and hasattr(effective_time.low, 'value') and effective_time.low.value:
                return self.convert_date(effective_time.low.value)
            elif effective_time.high and hasattr(effective_time.high, 'value') and effective_time.high.value:
                return self.convert_date(effective_time.high.value)

        return None

    def _extract_dose_quantity(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract dose quantity.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR Quantity or None
        """
        if not substance_admin.dose_quantity:
            return None

        dose = substance_admin.dose_quantity

        # Handle both PQ and IVL_PQ
        if isinstance(dose, PQ):
            quantity: JSONObject = {}
            if dose.value is not None:
                # Ensure value is a number (float or int)
                try:
                    value = float(dose.value) if isinstance(dose.value, str) else dose.value
                    # Convert to int if it's a whole number
                    if value == int(value):
                        quantity["value"] = int(value)
                    else:
                        quantity["value"] = value
                except (ValueError, TypeError):
                    quantity["value"] = dose.value
            if dose.unit:
                quantity["unit"] = dose.unit
            return quantity if quantity else None
        elif isinstance(dose, IVL_PQ):
            # For intervals, use the low value if available
            if dose.low:
                quantity = {}
                if dose.low.value is not None:
                    quantity["value"] = dose.low.value
                if dose.low.unit:
                    quantity["unit"] = dose.low.unit
                return quantity if quantity else None

        return None

    def _extract_lot_number(self, substance_admin: SubstanceAdministration) -> str | None:
        """Extract lot number from manufacturedMaterial.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            Lot number string or None
        """
        if not substance_admin.consumable:
            return None

        manufactured_product = substance_admin.consumable.manufactured_product
        if not manufactured_product:
            return None

        manufactured_material = manufactured_product.manufactured_material
        if not manufactured_material:
            return None

        return manufactured_material.lot_number_text

    def _extract_manufacturer(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract manufacturer organization.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR Reference to Organization or None
        """
        if not substance_admin.consumable:
            return None

        manufactured_product = substance_admin.consumable.manufactured_product
        if not manufactured_product:
            return None

        manufacturer_org = manufactured_product.manufacturer_organization
        if not manufacturer_org:
            return None

        # Extract organization name
        if manufacturer_org.name and len(manufacturer_org.name) > 0:
            org_name = manufacturer_org.name[0]
            # Extract value from ON object or use string directly
            if isinstance(org_name, str):
                name_str = org_name
            elif hasattr(org_name, "value") and org_name.value:
                name_str = org_name.value
            else:
                name_str = None

            if name_str:
                # For now, return a display-only reference
                # Full Organization resource conversion would be in Phase 6
                return {"display": name_str}

        return None

    def _extract_route(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract route of administration.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR CodeableConcept for route or None
        """
        if not substance_admin.route_code:
            return None

        return self._convert_code_to_codeable_concept(substance_admin.route_code)

    def _extract_site(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract approach site (body site).

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            FHIR CodeableConcept for site or None
        """
        if not substance_admin.approach_site_code or len(substance_admin.approach_site_code) == 0:
            return None

        # Use the first approach site
        return self._convert_code_to_codeable_concept(substance_admin.approach_site_code[0])

    def _extract_reason_codes(self, substance_admin: SubstanceAdministration) -> tuple[list[JSONObject], list[JSONObject]]:
        """Extract reason codes from RSON (reason) entry relationships.

        Implements complex not-given reason mapping per C-CDA on FHIR IG:
        - Distinguishes between refusal reasons (NoImmunizationReason ValueSet → statusReason)
          and clinical indications (Problem Type ValueSet → reasonCode)
        - Both use typeCode="RSON", so differentiation is by ValueSet membership
        - Checks both observation.code and observation.value for refusal reasons
        - Handles multiple reasons and complex nested structures

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            Tuple of (status_reasons, reason_codes):
            - status_reasons: List of refusal reason CodeableConcepts for statusReason
            - reason_codes: List of clinical indication CodeableConcepts for reasonCode
        """
        status_reasons = []  # NoImmunizationReason codes (refusal reasons)
        reason_codes = []    # Clinical indications

        if not substance_admin.entry_relationship:
            return status_reasons, reason_codes

        # Process all RSON (reason) entry relationships
        for entry_rel in substance_admin.entry_relationship:
            if entry_rel.type_code == TypeCodes.RSON and entry_rel.observation:
                observation = entry_rel.observation

                # Check if this observation has the Immunization Refusal Reason template
                has_refusal_template = False
                if observation.template_id:
                    for tid in observation.template_id:
                        if tid.root == TemplateIds.IMMUNIZATION_REFUSAL_REASON:
                            has_refusal_template = True
                            break

                # Try to extract a refusal reason from observation.code first
                # This is the primary location per C-CDA IG for Immunization Refusal Reason template
                refusal_found = False
                if observation.code and observation.code.code:
                    # Check if this code is from the NoImmunizationReason ValueSet
                    if self._is_no_immunization_reason_code(observation.code.code):
                        reason_code = self._convert_code_to_codeable_concept(observation.code)
                        if reason_code:
                            status_reasons.append(reason_code)
                            refusal_found = True

                # If no refusal reason found in observation.code, check observation.value
                # Some C-CDA documents may place the refusal reason in value instead
                if not refusal_found and observation.value and isinstance(observation.value, (CD, CE)):
                    value_cd = observation.value
                    if value_cd.code and self._is_no_immunization_reason_code(value_cd.code):
                        reason_code = self._convert_code_to_codeable_concept(value_cd)
                        if reason_code:
                            status_reasons.append(reason_code)
                            refusal_found = True

                # If this is not a refusal reason, treat as clinical indication
                # Clinical indications use Indication template (2.16.840.1.113883.10.20.22.4.19)
                # and have the indication in observation.value
                if not refusal_found and not has_refusal_template:
                    if observation.value and isinstance(observation.value, (CD, CE)):
                        # This is likely a clinical indication (e.g., Asthma as reason for flu vaccine)
                        reason_code = self._convert_code_to_codeable_concept(observation.value)
                        if reason_code:
                            reason_codes.append(reason_code)

        return status_reasons, reason_codes

    def _is_no_immunization_reason_code(self, code: str) -> bool:
        """Check if a code is from the NoImmunizationReason ValueSet.

        Args:
            code: The code to check

        Returns:
            True if the code is from the NoImmunizationReason ValueSet
        """
        return code in NO_IMMUNIZATION_REASON_CODES

    def _extract_protocol_applied(self, substance_admin: SubstanceAdministration) -> list[JSONObject]:
        """Extract protocol applied from repeatNumber.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            List containing protocol applied information
        """
        if not substance_admin.repeat_number:
            return []

        repeat_number = substance_admin.repeat_number

        # Extract dose number from repeat_number
        # IVL_PQ can have value or low.value
        dose_number = None
        if hasattr(repeat_number, 'value') and repeat_number.value is not None:
            dose_number = int(repeat_number.value)
        elif hasattr(repeat_number, 'low') and repeat_number.low and repeat_number.low.value is not None:
            dose_number = int(repeat_number.low.value)

        if dose_number is not None:
            protocol: JSONObject = {
                "doseNumberPositiveInt": dose_number
            }
            return [protocol]

        return []

    def _extract_reactions(self, substance_admin: SubstanceAdministration, immunization_id: str) -> tuple[list[JSONObject], list[JSONObject]]:
        """Extract reaction observations from entry relationships.

        Creates separate Observation resources for reactions and references them
        from the Immunization resource per FHIR R4 spec and C-CDA on FHIR IG.

        Args:
            substance_admin: The C-CDA SubstanceAdministration
            immunization_id: The ID of the parent Immunization resource

        Returns:
            Tuple of (reactions, observation_resources):
            - reactions: List of reaction objects with detail references
            - observation_resources: List of created Observation resources
        """
        reactions = []
        observation_resources = []

        if not substance_admin.entry_relationship:
            return reactions, observation_resources

        # Find reaction (MFST) observations
        for idx, entry_rel in enumerate(substance_admin.entry_relationship):
            if entry_rel.type_code == TypeCodes.MFST and entry_rel.observation:
                observation = entry_rel.observation

                # Create Observation resource for this reaction
                observation_resource = self._create_reaction_observation(
                    observation, immunization_id, idx
                )

                if observation_resource:
                    observation_resources.append(observation_resource)

                    # Create reaction object with reference to the Observation
                    reaction: JSONObject = {
                        "detail": {
                            "reference": f"Observation/{observation_resource['id']}"
                        }
                    }

                    # Extract date from observation.effectiveTime
                    if observation.effective_time:
                        date = self._extract_reaction_date(observation.effective_time)
                        if date:
                            reaction["date"] = date

                    reactions.append(reaction)

        return reactions, observation_resources

    def _create_reaction_observation(
        self, observation, immunization_id: str, idx: int
    ) -> JSONObject | None:
        """Create an Observation resource for a reaction.

        Args:
            observation: The C-CDA Reaction Observation
            immunization_id: The ID of the parent Immunization resource
            idx: Index of this reaction (for unique ID generation)

        Returns:
            FHIR Observation resource or None
        """
        # Extract code from observation.value (this is the reaction manifestation)
        if not observation.value or not isinstance(observation.value, (CD, CE)):
            return None

        code = self._convert_code_to_codeable_concept(observation.value)
        if not code:
            return None

        # Generate unique ID for the reaction observation
        observation_id = f"{immunization_id}-reaction-{idx}"

        observation_resource: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
            "id": observation_id,
            "status": "final",
            "code": code,
        }

        # Add patient reference
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Observation without patient reference."
            )
        observation_resource["subject"] = self.reference_registry.get_patient_reference()

        # Extract effectiveDateTime if available
        if observation.effective_time:
            date = self._extract_reaction_date(observation.effective_time)
            if date:
                observation_resource["effectiveDateTime"] = date

        # Add value - use same code as value for reaction observations
        observation_resource["valueCodeableConcept"] = code

        return observation_resource

    def _extract_reaction_date(self, effective_time) -> str | None:
        """Extract date from reaction observation effectiveTime.

        Args:
            effective_time: The effectiveTime element (can be IVL_TS, TS, etc.)

        Returns:
            ISO date string or None
        """
        # Try to extract low value from IVL_TS
        if hasattr(effective_time, 'low') and effective_time.low:
            if hasattr(effective_time.low, 'value') and effective_time.low.value:
                return self.convert_date(effective_time.low.value)
        # Try direct value from TS
        elif hasattr(effective_time, 'value') and effective_time.value:
            return self.convert_date(effective_time.value)

        return None

    def _extract_supporting_observations(
        self, substance_admin: SubstanceAdministration, immunization_id: str
    ) -> list[JSONObject]:
        """Extract supporting observations from SPRT entry relationships.

        Creates separate Observation resources for supporting observations (evidence)
        such as antibody titers, immunity tests, etc.

        Args:
            substance_admin: The C-CDA SubstanceAdministration
            immunization_id: The ID of the parent Immunization resource

        Returns:
            List of FHIR Observation resources
        """
        observations = []

        if not substance_admin.entry_relationship:
            return observations

        # Find SPRT (supporting) observations
        for idx, entry_rel in enumerate(substance_admin.entry_relationship):
            if entry_rel.type_code == TypeCodes.SPRT and entry_rel.observation:
                observation = entry_rel.observation

                # Create Observation resource for this supporting observation
                observation_resource = self._create_supporting_observation(
                    observation, immunization_id, idx
                )

                if observation_resource:
                    observations.append(observation_resource)

        return observations

    def _create_supporting_observation(
        self, observation, immunization_id: str, idx: int
    ) -> JSONObject | None:
        """Create an Observation resource for a supporting observation.

        Args:
            observation: The C-CDA Observation
            immunization_id: The ID of the parent Immunization resource
            idx: Index of this observation (for unique ID generation)

        Returns:
            FHIR Observation resource or None
        """
        # Extract code from observation.code
        if not observation.code:
            return None

        code = self._convert_code_to_codeable_concept(observation.code)
        if not code:
            return None

        # Generate unique ID for the supporting observation
        observation_id = f"{immunization_id}-supporting-{idx}"

        observation_resource: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
            "id": observation_id,
            "status": "final",
            "code": code,
        }

        # Add patient reference
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Observation without patient reference."
            )
        observation_resource["subject"] = self.reference_registry.get_patient_reference()

        # Extract effectiveDateTime if available
        if observation.effective_time:
            # Try to get the value from effective_time
            if hasattr(observation.effective_time, 'value') and observation.effective_time.value:
                date = self.convert_date(observation.effective_time.value)
                if date:
                    observation_resource["effectiveDateTime"] = date
            # Try low value for IVL_TS
            elif hasattr(observation.effective_time, 'low') and observation.effective_time.low:
                if hasattr(observation.effective_time.low, 'value') and observation.effective_time.low.value:
                    date = self.convert_date(observation.effective_time.low.value)
                    if date:
                        observation_resource["effectiveDateTime"] = date

        # Extract value based on type
        if observation.value:
            # Check for PQ (physical quantity)
            if hasattr(observation.value, 'value') and hasattr(observation.value, 'unit'):
                quantity: JSONObject = {}
                if observation.value.value is not None:
                    # Ensure value is a number (float or int)
                    try:
                        value = float(observation.value.value) if isinstance(observation.value.value, str) else observation.value.value
                        # Convert to int if it's a whole number
                        if value == int(value):
                            quantity["value"] = int(value)
                        else:
                            quantity["value"] = value
                    except (ValueError, TypeError):
                        quantity["value"] = observation.value.value
                if observation.value.unit:
                    quantity["unit"] = observation.value.unit
                    # Map common UCUM units
                    if observation.value.unit == ":{titer}":
                        quantity["system"] = "http://unitsofmeasure.org"
                        quantity["code"] = "{titer}"
                if quantity:
                    observation_resource["valueQuantity"] = quantity
            # Check for CD/CE (coded value)
            elif isinstance(observation.value, (CD, CE)):
                value_code = self._convert_code_to_codeable_concept(observation.value)
                if value_code:
                    observation_resource["valueCodeableConcept"] = value_code

        # Extract interpretation code if available
        if observation.interpretation_code and len(observation.interpretation_code) > 0:
            interpretations = []
            for interp_code in observation.interpretation_code:
                interpretation = self._convert_code_to_codeable_concept(interp_code)
                if interpretation:
                    interpretations.append(interpretation)
            if interpretations:
                observation_resource["interpretation"] = interpretations

        return observation_resource

    def _extract_component_observations(
        self, substance_admin: SubstanceAdministration, immunization_id: str
    ) -> list[JSONObject]:
        """Extract component observations from COMP entry relationships.

        Creates separate Observation resources for component observations (complications)
        such as injection site infections, adverse events, etc.

        Args:
            substance_admin: The C-CDA SubstanceAdministration
            immunization_id: The ID of the parent Immunization resource

        Returns:
            List of FHIR Observation resources
        """
        observations = []

        if not substance_admin.entry_relationship:
            return observations

        # Find COMP (component) observations
        for idx, entry_rel in enumerate(substance_admin.entry_relationship):
            if entry_rel.type_code == TypeCodes.COMP and entry_rel.observation:
                observation = entry_rel.observation

                # Create Observation resource for this component observation
                observation_resource = self._create_component_observation(
                    observation, immunization_id, idx
                )

                if observation_resource:
                    observations.append(observation_resource)

        return observations

    def _create_component_observation(
        self, observation, immunization_id: str, idx: int
    ) -> JSONObject | None:
        """Create an Observation resource for a component observation (complication).

        Args:
            observation: The C-CDA Observation
            immunization_id: The ID of the parent Immunization resource
            idx: Index of this observation (for unique ID generation)

        Returns:
            FHIR Observation resource or None
        """
        # Extract code from observation.code (usually "Problem" or similar)
        if not observation.code:
            return None

        code = self._convert_code_to_codeable_concept(observation.code)
        if not code:
            return None

        # Extract value from observation.value (this is the actual complication/problem)
        if not observation.value or not isinstance(observation.value, (CD, CE)):
            return None

        value_code = self._convert_code_to_codeable_concept(observation.value)
        if not value_code:
            return None

        # Generate unique ID for the component observation
        observation_id = f"{immunization_id}-complication-{idx}"

        observation_resource: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.OBSERVATION,
            "id": observation_id,
            "status": "final",
            "code": code,
            "valueCodeableConcept": value_code,
        }

        # Add patient reference
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Observation without patient reference."
            )
        observation_resource["subject"] = self.reference_registry.get_patient_reference()

        # Extract effectiveDateTime if available (usually has low value for when complication started)
        if observation.effective_time:
            # Try low value for IVL_TS (when the complication started)
            if hasattr(observation.effective_time, 'low') and observation.effective_time.low:
                if hasattr(observation.effective_time.low, 'value') and observation.effective_time.low.value:
                    date = self.convert_date(observation.effective_time.low.value)
                    if date:
                        observation_resource["effectiveDateTime"] = date
            # Try direct value from TS
            elif hasattr(observation.effective_time, 'value') and observation.effective_time.value:
                date = self.convert_date(observation.effective_time.value)
                if date:
                    observation_resource["effectiveDateTime"] = date

        return observation_resource

    def _extract_performers(self, substance_admin: SubstanceAdministration) -> list[JSONObject]:
        """Extract performer information.

        Per FHIR R4B, Immunization.performer.actor is a required Reference to
        Practitioner, PractitionerRole, or Organization.

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            List of performer objects
        """
        performers = []

        if not substance_admin.performer:
            return performers

        for performer in substance_admin.performer:
            if not performer.assigned_entity:
                continue

            assigned_entity = performer.assigned_entity
            performer_obj: JSONObject = {}

            # Extract practitioner reference from assigned entity ID
            # Per C-CDA on FHIR IG, use assignedEntity.id to create Practitioner reference
            if assigned_entity.id:
                for id_elem in assigned_entity.id:
                    # Skip nullFlavor IDs if there are other valid IDs
                    if id_elem.root and not id_elem.null_flavor:
                        pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                        performer_obj["actor"] = {
                            "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                        }
                        break

                # If all IDs have nullFlavor, use the first one anyway to create a reference
                if "actor" not in performer_obj and assigned_entity.id:
                    id_elem = assigned_entity.id[0]
                    if id_elem.root:
                        pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                        performer_obj["actor"] = {
                            "reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{pract_id}"
                        }

            # If no ID found, try to use represented organization
            if "actor" not in performer_obj:
                if assigned_entity.represented_organization and assigned_entity.represented_organization.id:
                    org = assigned_entity.represented_organization
                    for id_elem in org.id:
                        if id_elem.root:
                            org_id = self._generate_organization_id(id_elem.root, id_elem.extension)
                            performer_obj["actor"] = {
                                "reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{org_id}"
                            }
                            break

            # Set function (who administered the vaccine)
            performer_obj["function"] = {
                "coding": [{
                    "system": FHIRSystems.V2_PARTICIPATION_FUNCTION,
                    "code": V2ParticipationFunctionCodes.ADMINISTERING_PROVIDER,
                    "display": "Administering Provider"
                }]
            }

            # Only add performer if we successfully created an actor reference
            # FHIR requires performer.actor to be present
            if "actor" in performer_obj:
                performers.append(performer_obj)

        return performers

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

    def _extract_notes(self, substance_admin: SubstanceAdministration) -> list[JSONObject]:
        """Extract FHIR notes from C-CDA substance administration.

        Extracts notes from Comment Activity entries (template 2.16.840.1.113883.10.20.22.4.64).

        Args:
            substance_admin: The C-CDA SubstanceAdministration

        Returns:
            List of FHIR Annotation objects (as dicts with 'text' field)
        """
        notes = []

        # Extract from Comment Activity entries
        if substance_admin.entry_relationship:
            for entry_rel in substance_admin.entry_relationship:
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

    def _format_name_for_display(self, name) -> str | None:
        """Format a name for display.

        Args:
            name: The name element (PN)

        Returns:
            Formatted name string or None
        """
        parts = []

        # Extract given names
        if hasattr(name, 'given') and name.given:
            for given in name.given:
                parts.append(str(given))

        # Extract family name
        if hasattr(name, 'family') and name.family:
            if isinstance(name.family, list):
                parts.extend(str(f) for f in name.family)
            else:
                parts.append(str(name.family))

        return " ".join(parts) if parts else None

    def _convert_code_to_codeable_concept(self, code_elem: CD | CE) -> JSONObject | None:
        """Convert a C-CDA CD/CE code element to a FHIR CodeableConcept.

        Args:
            code_elem: The C-CDA CD or CE code element

        Returns:
            FHIR CodeableConcept or None
        """
        if not code_elem:
            return None

        # Check if main code has nullFlavor - if so, use first translation as primary
        primary_code = code_elem.code
        primary_system = code_elem.code_system
        primary_display = code_elem.display_name

        # Extract translations
        translations = None
        if code_elem.translation:
            translations = []
            for trans in code_elem.translation:
                if trans.code and trans.code_system:
                    translations.append({
                        "code": trans.code,
                        "code_system": trans.code_system,
                        "display_name": trans.display_name,
                    })

        # If primary code is missing (nullFlavor), promote first translation to primary
        if (not primary_code or hasattr(code_elem, 'null_flavor') and code_elem.null_flavor) and translations:
            first_trans = translations[0]
            primary_code = first_trans["code"]
            primary_system = first_trans["code_system"]
            primary_display = first_trans["display_name"]
            # Remove from translations to avoid duplication
            translations = translations[1:] if len(translations) > 1 else None

        # Get original text if available (with reference resolution)
        original_text = None
        if hasattr(code_elem, 'original_text') and code_elem.original_text:
            original_text = self.extract_original_text(code_elem.original_text, section=None)

        return self.create_codeable_concept(
            code=primary_code,
            code_system=primary_system,
            display_name=primary_display,
            original_text=original_text,
            translations=translations,
        )


def convert_immunization_activity(
    substance_admin: SubstanceAdministration,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> list[FHIRResourceDict]:
    """Convert a C-CDA Immunization Activity to FHIR resources.

    This is a convenience function that creates a converter and performs the conversion.

    For historical immunizations (moodCode="EVN"), creates FHIR Immunization resources.
    For planned immunizations (moodCode="INT"), creates FHIR MedicationRequest resources.

    Args:
        substance_admin: The C-CDA SubstanceAdministration (Immunization Activity)
        code_system_mapper: Optional CodeSystemMapper instance
        metadata_callback: Optional callback for storing author metadata
        section: The C-CDA Section containing this immunization (for narrative)

    Returns:
        List of FHIR resources:
        - For moodCode="EVN": [Immunization, Observation, ...]
          - First element is the Immunization resource
          - Subsequent elements are Observation resources for reactions (if any)
        - For moodCode="INT": [MedicationRequest]
          - Single MedicationRequest resource for planned immunization
    """
    # Check moodCode to determine resource type
    # Per C-CDA on FHIR IG: INT (planned) → MedicationRequest, EVN (historical) → Immunization
    mood_code = substance_admin.mood_code or "EVN"

    if mood_code.upper() == "INT":
        # Planned immunization - convert to MedicationRequest
        converter = MedicationRequestConverter(
            code_system_mapper=code_system_mapper,
            reference_registry=reference_registry,
        )
        medication_request = converter.convert(substance_admin, section=section)

        # Store author metadata if callback provided
        if metadata_callback and medication_request.get("id"):
            metadata_callback(
                resource_type="MedicationRequest",
                resource_id=medication_request["id"],
                ccda_element=substance_admin,
                concern_act=None,
            )

        return [medication_request]
    else:
        # Historical immunization - convert to Immunization resource
        converter = ImmunizationConverter(
            code_system_mapper=code_system_mapper,
            reference_registry=reference_registry,
        )
        immunization, reaction_observations = converter.convert(substance_admin, section=section)

        # Store author metadata if callback provided
        if metadata_callback and immunization.get("id"):
            metadata_callback(
                resource_type="Immunization",
                resource_id=immunization["id"],
                ccda_element=substance_admin,
                concern_act=None,
            )

        # Return all resources as a list
        return [immunization] + reaction_observations
