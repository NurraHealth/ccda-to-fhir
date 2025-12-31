"""MedicationRequest converter: C-CDA Medication Activity to FHIR MedicationRequest resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CD, CE, EIVL_TS, IVL_PQ, IVL_TS, PIVL_TS, PQ
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.constants import (
    EIVL_EVENT_TO_FHIR_WHEN,
    MEDICATION_MOOD_TO_INTENT,
    MEDICATION_STATUS_TO_FHIR,
    UCUM_TO_FHIR_UNITS_OF_TIME,
    FHIRCodes,
    TemplateIds,
    TypeCodes,
)
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter
from .medication import MedicationConverter

logger = get_logger(__name__)

# Global registry for storing created Medication resources
# This will be populated during conversion and extracted by the DocumentConverter
_medication_registry: dict[str, FHIRResourceDict] = {}


class MedicationRequestConverter(BaseConverter[SubstanceAdministration]):
    """Convert C-CDA Medication Activity to FHIR MedicationRequest resource.

    This converter handles the mapping from C-CDA SubstanceAdministration
    (Medication Activity template 2.16.840.1.113883.10.20.22.4.16) to a
    FHIR R4B MedicationRequest resource, including dosage instructions,
    timing, route, and dispense requests.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html
    """

    def __init__(self, *args, **kwargs):
        """Initialize the medication request converter."""
        super().__init__(*args, **kwargs)

    def convert(self, substance_admin: SubstanceAdministration, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Medication Activity to a FHIR MedicationRequest.

        Args:
            substance_admin: The C-CDA SubstanceAdministration (Medication Activity)
            section: The C-CDA Section containing this medication (for narrative)

        Returns:
            FHIR MedicationRequest resource as a dictionary

        Raises:
            ValueError: If the substance administration lacks required data
        """
        # Validation
        if not substance_admin.consumable:
            raise ValueError("Medication Activity must have a consumable (medication)")

        med_request: JSONObject = {
            "resourceType": "MedicationRequest",
        }

        # 1. Generate ID from substance administration identifier
        # Find first valid identifier (skip nullFlavor)
        root = None
        extension = None
        if substance_admin.id:
            for id_elem in substance_admin.id:
                if not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                    if id_elem.root or id_elem.extension:
                        root = id_elem.root
                        extension = id_elem.extension
                        break

        # Generate fallback context if no valid identifiers
        fallback_context = ""
        if root is None and extension is None:
            # Create deterministic context from medication properties
            context_parts = []
            if substance_admin.consumable and substance_admin.consumable.manufactured_product:
                material = substance_admin.consumable.manufactured_product.manufactured_material
                if material and material.code and material.code.code:
                    context_parts.append(material.code.code)
            if substance_admin.effective_time:
                # Use low value if available for determinism
                if hasattr(substance_admin.effective_time, 'low') and substance_admin.effective_time.low:
                    context_parts.append(str(substance_admin.effective_time.low.value or ""))
                elif hasattr(substance_admin.effective_time, 'value') and substance_admin.effective_time.value:
                    context_parts.append(str(substance_admin.effective_time.value))
            if substance_admin.status_code and substance_admin.status_code.code:
                context_parts.append(substance_admin.status_code.code)
            fallback_context = "-".join(filter(None, context_parts))

        # Always generate an ID (with fallback if needed)
        med_request["id"] = self._generate_medication_request_id(
            root=root,
            extension=extension,
            fallback_context=fallback_context,
        )

        # 2. Identifiers
        if substance_admin.id:
            identifiers = []
            for id_elem in substance_admin.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                med_request["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(substance_admin)
        med_request["status"] = status

        # 4. Intent (required) - from moodCode
        intent = self._determine_intent(substance_admin)
        med_request["intent"] = intent

        # 5. DoNotPerform - from negationInd
        if substance_admin.negation_ind:
            med_request["doNotPerform"] = True

        # 6. Medication (required) - use medicationReference for complex cases, medicationCodeableConcept for simple
        medication_data = self._extract_medication(substance_admin)
        if medication_data:
            if "medicationReference" in medication_data:
                med_request["medicationReference"] = medication_data["medicationReference"]
            elif "medicationCodeableConcept" in medication_data:
                med_request["medicationCodeableConcept"] = medication_data["medicationCodeableConcept"]
        else:
            # US Core Must Support: medication[x] is required
            # If we couldn't extract medication data, create a text-only CodeableConcept
            # with data-absent-reason extension embedded inside (complex type, not primitive)
            med_request["medicationCodeableConcept"] = {
                "extension": [
                    self.create_data_absent_reason_extension(None, default_reason="unknown")
                ],
                "text": "Medication information not provided"
            }

        # 6. Subject (patient reference)
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create MedicationRequest without patient reference."
            )
        med_request["subject"] = self.reference_registry.get_patient_reference()

        # 7. AuthoredOn (from author time)
        authored_on = self._extract_authored_on(substance_admin)
        if authored_on:
            med_request["authoredOn"] = authored_on

        # 7b. Requester (from latest author)
        if substance_admin.author:
            # Filter authors with time
            authors_with_time = [
                a for a in substance_admin.author
                if hasattr(a, 'time') and a.time and a.time.value
            ]

            if authors_with_time:
                # Sort by time and get latest
                latest_author = max(authors_with_time, key=lambda a: a.time.value)

                if hasattr(latest_author, 'assigned_author') and latest_author.assigned_author:
                    assigned = latest_author.assigned_author

                    # Check for practitioner
                    # Only create reference if we have an explicit ID with root
                    if hasattr(assigned, 'assigned_person') and assigned.assigned_person:
                        if hasattr(assigned, 'id') and assigned.id:
                            for id_elem in assigned.id:
                                if id_elem.root:
                                    pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                                    med_request["requester"] = {
                                        "reference": f"Practitioner/{pract_id}"
                                    }
                                    break
                    # Check for device
                    elif hasattr(assigned, 'assigned_authoring_device') and assigned.assigned_authoring_device:
                        if hasattr(assigned, 'id') and assigned.id:
                            for id_elem in assigned.id:
                                if id_elem.root:
                                    device_id = self._generate_device_id(id_elem.root, id_elem.extension)
                                    med_request["requester"] = {
                                        "reference": f"Device/{device_id}"
                                    }
                                    break

        # 8. ReasonCode (from indication entry relationship)
        reason_codes = self._extract_reason_codes(substance_admin)
        if reason_codes:
            med_request["reasonCode"] = reason_codes

        # 9. DosageInstruction (complex)
        dosage_instructions = self._extract_dosage_instructions(substance_admin)
        if dosage_instructions:
            med_request["dosageInstruction"] = dosage_instructions

        # 10. DispenseRequest (from supply order entry relationships or repeatNumber)
        dispense_request = self._extract_dispense_request(substance_admin)
        if dispense_request:
            med_request["dispenseRequest"] = dispense_request

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=substance_admin, section=section)
        if narrative:
            med_request["text"] = narrative

        return med_request

    def _generate_medication_request_id(
        self,
        root: str | None,
        extension: str | None,
        fallback_context: str = "",
    ) -> str:
        """Generate a medication request resource ID from C-CDA identifier.

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
            resource_type="medicationrequest",
            fallback_context=fallback_context,
        )

    def _determine_status(self, substance_admin: SubstanceAdministration) -> str:
        """Map C-CDA statusCode to FHIR MedicationRequest status.

        Per C-CDA on FHIR IG: C-CDA "completed" may mean "prescription writing completed"
        rather than "medication administration completed". When statusCode="completed"
        but effectiveTime contains future dates, map to FHIR "active" instead.

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html
        """
        if not substance_admin.status_code:
            return FHIRCodes.MedicationRequestStatus.ACTIVE

        status_code = substance_admin.status_code.code

        # Special handling for "completed" status per C-CDA on FHIR IG guidance
        if status_code == "completed":
            # Check if medication has future dates in effectiveTime
            if self._has_future_dates(substance_admin):
                # Completed prescription with future dates → active medication
                return FHIRCodes.MedicationRequestStatus.ACTIVE

        # Use standard mapping for all other cases
        return MEDICATION_STATUS_TO_FHIR.get(
            status_code, FHIRCodes.MedicationRequestStatus.ACTIVE
        )

    def _has_future_dates(self, substance_admin: SubstanceAdministration) -> bool:
        """Check if medication has future dates in effectiveTime.

        Examines IVL_TS effectiveTime elements to determine if the medication
        period extends into the future.

        Args:
            substance_admin: The substance administration to check

        Returns:
            True if any effectiveTime.high is in the future or unbounded,
            False otherwise
        """
        from datetime import datetime

        if not substance_admin.effective_time:
            return False

        # Get current date for comparison (system local time)
        # Note: C-CDA dates without explicit timezone (YYYYMMDD format) are typically
        # in the document author's local timezone. Comparing against system local time
        # is appropriate for these dates. If timezone-aware comparison is needed,
        # the C-CDA date parser should extract and preserve timezone information.
        now = datetime.now().strftime("%Y%m%d")

        for eff_time in substance_admin.effective_time:
            # Only check IVL_TS (interval) for medication period
            if isinstance(eff_time, IVL_TS):
                # If high is absent, medication is ongoing (unbounded) → future
                if not eff_time.high or not eff_time.high.value:
                    # Unbounded medication (no end date) is considered active/future
                    return True

                # If high date is in the future → future
                if eff_time.high.value:
                    # Extract date portion (first 8 chars: YYYYMMDD)
                    high_date = str(eff_time.high.value)[:8]
                    if high_date > now:
                        return True

        return False

    def _determine_intent(self, substance_admin: SubstanceAdministration) -> str:
        """Map C-CDA moodCode to FHIR MedicationRequest intent."""
        mood_code = substance_admin.mood_code or "INT"
        return MEDICATION_MOOD_TO_INTENT.get(
            mood_code, FHIRCodes.MedicationRequestIntent.PLAN
        )

    def _extract_medication(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract medication as medicationReference or medicationCodeableConcept.

        Per C-CDA on FHIR IG: When additional medication details need to be conveyed
        (manufacturer, drug vehicle, form, lot number), a Medication resource should
        be created and referenced. Otherwise, use medicationCodeableConcept.

        Returns:
            Dict with either "medicationReference" or "medicationCodeableConcept" key
        """
        if not substance_admin.consumable:
            return None

        consumable = substance_admin.consumable
        if not consumable.manufactured_product:
            return None

        manufactured_product = consumable.manufactured_product
        if not manufactured_product.manufactured_material:
            return None

        manufactured_material = manufactured_product.manufactured_material
        if not manufactured_material.code:
            return None

        # Check if we need to create a Medication resource (complex medication info)
        has_complex_info = self._has_complex_medication_info(substance_admin, manufactured_product)

        if has_complex_info:
            # Create Medication resource and return reference
            medication_converter = MedicationConverter(code_system_mapper=self.code_system_mapper)
            medication = medication_converter.convert(manufactured_product, substance_admin)

            # Store in registry for later extraction by DocumentConverter
            medication_id = medication["id"]
            _medication_registry[medication_id] = medication

            return {"medicationReference": {"reference": f"Medication/{medication_id}"}}
        else:
            # Simple case - use medicationCodeableConcept
            med_code = manufactured_material.code

            # Extract translations - convert CD objects to dictionaries
            translations = None
            if hasattr(med_code, 'translation') and med_code.translation:
                translations = []
                for trans in med_code.translation:
                    if trans.code and trans.code_system:
                        translations.append({
                            "code": trans.code,
                            "code_system": trans.code_system,
                            "display_name": trans.display_name,
                        })

            codeable_concept = self.create_codeable_concept(
                code=med_code.code,
                code_system=med_code.code_system,
                display_name=med_code.display_name,
                original_text=(
                    self.extract_original_text(med_code.original_text)
                    if med_code.original_text
                    else None
                ),
                translations=translations,
            )

            # Check if codeable_concept is empty (no codings, no text)
            # This can happen when all codings are skipped due to unmapped OIDs
            if not codeable_concept or (not codeable_concept.get("coding") and not codeable_concept.get("text")):
                return None

            return {"medicationCodeableConcept": codeable_concept}

    def _has_complex_medication_info(
        self, substance_admin: SubstanceAdministration, manufactured_product
    ) -> bool:
        """Check if medication has complex information requiring a Medication resource.

        Complex information includes:
        - Manufacturer organization
        - Drug vehicle participant (ingredient)
        - Administration unit code (form)
        - Lot number (batch)

        Args:
            substance_admin: The substance administration
            manufactured_product: The manufactured product

        Returns:
            True if complex information exists, False otherwise
        """
        # Check for manufacturer
        if manufactured_product.manufacturer_organization:
            if manufactured_product.manufacturer_organization.name:
                return True

        # Check for drug vehicle (participant with typeCode="CSM")
        if substance_admin.participant:
            for participant in substance_admin.participant:
                if participant.type_code and participant.type_code.upper() == "CSM":
                    return True

        # Check for administration unit code (form)
        if substance_admin.administration_unit_code:
            return True

        # Check for lot number (batch)
        if manufactured_product.manufactured_material.lot_number_text:
            return True

        return False

    def _extract_authored_on(self, substance_admin: SubstanceAdministration) -> str | None:
        """Extract authoredOn date from author time."""
        if not substance_admin.author:
            return None

        # Use earliest author time
        earliest_time = None
        for author in substance_admin.author:
            if author.time and author.time.value:
                if earliest_time is None or author.time.value < earliest_time:
                    earliest_time = author.time.value

        if earliest_time:
            return self.convert_date(earliest_time)

        return None

    def _extract_reason_codes(self, substance_admin: SubstanceAdministration) -> list[FHIRResourceDict]:
        """Extract indication as reasonCode from RSON entry relationships."""
        reason_codes = []

        if not substance_admin.entry_relationship:
            return reason_codes

        for rel in substance_admin.entry_relationship:
            if rel.type_code == TypeCodes.REASON and rel.observation:
                # This is an Indication observation
                if rel.observation.value and isinstance(rel.observation.value, (CD, CE)):
                    value = rel.observation.value
                    reason_code = self.create_codeable_concept(
                        code=value.code,
                        code_system=value.code_system,
                        display_name=value.display_name,
                    )
                    if reason_code:
                        reason_codes.append(reason_code)

        return reason_codes

    def _extract_dosage_instructions(
        self, substance_admin: SubstanceAdministration
    ) -> list[FHIRResourceDict]:
        """Extract dosage instruction from substance administration."""
        dosage: JSONObject = {}

        # 1. Text (free text sig from substanceAdministration/text)
        # Per C-CDA on FHIR IG: substanceAdministration/text → dosageInstruction.text
        # Per FHIR R4: Dosage.text = "Free text dosage instructions e.g. SIG"
        if substance_admin.text and substance_admin.text.value:
            dosage["text"] = substance_admin.text.value

        # 2. PatientInstruction (from Instruction Act with typeCode=SUBJ)
        patient_instruction = self._extract_patient_instruction(substance_admin)
        if patient_instruction:
            dosage["patientInstruction"] = patient_instruction

        # 3. AdditionalInstruction (from Instruction Act code)
        additional_instructions = self._extract_additional_instructions(substance_admin)
        if additional_instructions:
            dosage["additionalInstruction"] = additional_instructions

        # 4. Timing (from effectiveTime elements)
        timing = self._extract_timing(substance_admin)
        if timing:
            dosage["timing"] = timing

        # 5. AsNeeded (from precondition)
        # Per C-CDA on FHIR IG: "The presence of a precondition element indicates
        # asNeededBoolean should be true. More complex maps may be possible with
        # .asNeededCodeableConcept."
        # Per FHIR R4: asNeededBoolean and asNeededCodeableConcept are mutually exclusive.
        # When asNeededCodeableConcept is used, Boolean is implied to be true.
        as_needed_concept = self._extract_as_needed(substance_admin)
        if as_needed_concept:
            # Precondition with coded value → use asNeededCodeableConcept
            # (Boolean is implied true per FHIR spec)
            dosage["asNeededCodeableConcept"] = as_needed_concept
        elif substance_admin.precondition:
            # Precondition exists but no coded value → use asNeededBoolean
            dosage["asNeededBoolean"] = True

        # 6. Route (from routeCode)
        # routeCode can be CE (with code_system) or CS (without code_system)
        if substance_admin.route_code:
            code_system = getattr(substance_admin.route_code, 'code_system', None)
            dosage["route"] = self.create_codeable_concept(
                code=substance_admin.route_code.code,
                code_system=code_system,
                display_name=substance_admin.route_code.display_name,
            )

        # 7. DoseAndRate (from doseQuantity)
        dose_and_rate = self._extract_dose_and_rate(substance_admin)
        if dose_and_rate:
            dosage["doseAndRate"] = dose_and_rate

        # 8. MaxDosePerPeriod (from maxDoseQuantity)
        max_dose = self._extract_max_dose_per_period(substance_admin)
        if max_dose:
            dosage["maxDosePerPeriod"] = max_dose

        return [dosage] if dosage else []

    def _extract_patient_instruction(self, substance_admin: SubstanceAdministration) -> str | None:
        """Extract patient instruction text from Instruction Act."""
        if not substance_admin.entry_relationship:
            return None

        for rel in substance_admin.entry_relationship:
            if (rel.type_code == TypeCodes.SUBJECT and
                rel.inversion_ind and
                rel.act):
                # Check if it's an Instruction Act
                if rel.act.template_id:
                    for template in rel.act.template_id:
                        if template.root == TemplateIds.INSTRUCTION_ACT:
                            if rel.act.text and rel.act.text.value:
                                return rel.act.text.value

        return None

    def _extract_additional_instructions(
        self, substance_admin: SubstanceAdministration
    ) -> list[FHIRResourceDict]:
        """Extract coded additional instructions from Instruction Act."""
        instructions = []

        if not substance_admin.entry_relationship:
            return instructions

        for rel in substance_admin.entry_relationship:
            if (rel.type_code == TypeCodes.SUBJECT and
                rel.inversion_ind and
                rel.act):
                if rel.act.template_id:
                    for template in rel.act.template_id:
                        if template.root == TemplateIds.INSTRUCTION_ACT:
                            if rel.act.code and rel.act.code.code:
                                instruction = self.create_codeable_concept(
                                    code=rel.act.code.code,
                                    code_system=rel.act.code.code_system,
                                    display_name=rel.act.code.display_name,
                                )
                                if instruction:
                                    instructions.append(instruction)

        return instructions

    def _extract_timing(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract timing from effectiveTime elements.

        C-CDA allows multiple effectiveTime elements:
        1. IVL_TS - medication period (boundsPeriod)
        2. PIVL_TS - periodic frequency (timing.repeat.frequency/period)
        3. EIVL_TS - event-based timing (timing.repeat.when)
        """
        if not substance_admin.effective_time:
            return None

        timing: JSONObject = {}
        repeat: JSONObject = {}

        # Find IVL_TS for boundsPeriod, PIVL_TS for frequency, and EIVL_TS for event-based timing
        ivl_ts = None
        pivl_ts = None
        eivl_ts = None

        for eff_time in substance_admin.effective_time:
            if isinstance(eff_time, IVL_TS):
                ivl_ts = eff_time
            elif isinstance(eff_time, PIVL_TS):
                pivl_ts = eff_time
            elif isinstance(eff_time, EIVL_TS):
                eivl_ts = eff_time

        # Convert IVL_TS to timing.repeat.boundsPeriod
        if ivl_ts:
            bounds_period = self._convert_ivl_ts_to_bounds_period(ivl_ts)
            if bounds_period:
                repeat["boundsPeriod"] = bounds_period

        # Convert PIVL_TS to timing.repeat (frequency/period)
        if pivl_ts:
            pivl_repeat = self._convert_pivl_to_repeat(pivl_ts)
            if pivl_repeat:
                repeat.update(pivl_repeat)

        # Convert EIVL_TS to timing.repeat (when/offset)
        if eivl_ts:
            eivl_repeat = self._convert_eivl_to_repeat(eivl_ts)
            if eivl_repeat:
                repeat.update(eivl_repeat)

        if repeat:
            timing["repeat"] = repeat

        return timing if timing else None

    def _convert_ivl_ts_to_bounds_period(self, ivl_ts: IVL_TS) -> JSONObject | None:
        """Convert IVL_TS (interval) to FHIR Period (boundsPeriod).

        IVL_TS represents the time period during which the medication should be taken.
        - low → boundsPeriod.start
        - high → boundsPeriod.end

        Args:
            ivl_ts: C-CDA IVL_TS (interval of time)

        Returns:
            FHIR Period dict with start and/or end dates
        """
        period: JSONObject = {}

        if ivl_ts.low and ivl_ts.low.value:
            start = self.convert_date(ivl_ts.low.value)
            if start:
                period["start"] = start

        if ivl_ts.high and ivl_ts.high.value:
            end = self.convert_date(ivl_ts.high.value)
            if end:
                period["end"] = end

        return period if period else None

    def _convert_pivl_to_repeat(self, pivl_ts: PIVL_TS) -> JSONObject | None:
        """Convert PIVL_TS (periodic interval) to FHIR Timing.repeat.

        PIVL_TS.period can be:
        - PQ: single period value (e.g., 6h)
        - IVL_PQ: range of periods (e.g., 4-6h) → use period and periodMax
        """
        if not pivl_ts.period:
            return None

        repeat: JSONObject = {}

        period = pivl_ts.period

        # Handle IVL_PQ (range)
        if isinstance(period, IVL_PQ):
            if period.low:
                repeat["period"] = self._extract_period_value(period.low)
                repeat["periodUnit"] = self._map_ucum_to_fhir_unit(period.low.unit)
            if period.high:
                repeat["periodMax"] = self._extract_period_value(period.high)
                # periodUnit comes from low, high should have same unit
        # Handle PQ (single value)
        elif isinstance(period, PQ):
            repeat["period"] = self._extract_period_value(period)
            repeat["periodUnit"] = self._map_ucum_to_fhir_unit(period.unit)

        return repeat if repeat else None

    def _convert_eivl_to_repeat(self, eivl_ts: EIVL_TS) -> JSONObject | None:
        """Convert EIVL_TS (event-based timing) to FHIR Timing.repeat.

        EIVL_TS maps to timing.repeat.when for event-based dosing:
        - event.code → when (e.g., AC, ACM, PC, HS, WAKE)
        - offset → offset (duration after the event, converted to minutes)

        Args:
            eivl_ts: C-CDA EIVL_TS (event-based timing)

        Returns:
            FHIR Timing.repeat dict with when and optionally offset
        """
        if not eivl_ts.event:
            return None

        repeat: JSONObject = {}

        # Extract event code
        event_code = None
        if hasattr(eivl_ts.event, "code") and eivl_ts.event.code:
            event_code = eivl_ts.event.code

        if event_code:
            # Map to FHIR when code
            when_code = EIVL_EVENT_TO_FHIR_WHEN.get(event_code)
            if when_code:
                repeat["when"] = [when_code]

        # Extract offset (if present)
        if hasattr(eivl_ts, "offset") and eivl_ts.offset:
            offset_pq = eivl_ts.offset
            if isinstance(offset_pq, PQ) and offset_pq.value is not None:
                # Convert offset to minutes (FHIR offset is in minutes)
                offset_minutes = self._convert_to_minutes(offset_pq)
                if offset_minutes is not None:
                    repeat["offset"] = offset_minutes

        return repeat if repeat else None

    def _convert_to_minutes(self, pq: PQ) -> int | None:
        """Convert a PQ (physical quantity) with time unit to minutes.

        Args:
            pq: Physical quantity with value and unit

        Returns:
            Value converted to minutes, or None if conversion fails
        """
        try:
            value = float(pq.value)
            unit = pq.unit.lower() if pq.unit else "min"

            # Convert to minutes
            if unit in ("min", "minute", "minutes"):
                return int(value)
            elif unit in ("h", "hour", "hours"):
                return int(value * 60)
            elif unit in ("s", "sec", "second", "seconds"):
                return int(value / 60)
            elif unit in ("d", "day", "days"):
                return int(value * 24 * 60)
            else:
                # Default to minutes if unknown unit
                return int(value)
        except (ValueError, TypeError, AttributeError):
            return None

    def _extract_period_value(self, pq: PQ) -> int | float:
        """Extract numeric value from PQ."""
        if pq.value is None:
            return 1
        try:
            value = float(pq.value)
            return int(value) if value.is_integer() else value
        except (ValueError, TypeError, AttributeError):
            return 1

    def _map_ucum_to_fhir_unit(self, ucum_unit: str | None) -> str:
        """Map UCUM unit code to FHIR UnitsOfTime."""
        if not ucum_unit:
            return "d"  # default to days

        return UCUM_TO_FHIR_UNITS_OF_TIME.get(
            ucum_unit, ucum_unit
        )

    def _extract_as_needed(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract PRN/as-needed indication from precondition."""
        if not substance_admin.precondition:
            return None

        for precondition in substance_admin.precondition:
            if precondition.criterion and precondition.criterion.value:
                criterion_value = precondition.criterion.value
                if isinstance(criterion_value, (CD, CE)):
                    return self.create_codeable_concept(
                        code=criterion_value.code,
                        code_system=criterion_value.code_system,
                        display_name=criterion_value.display_name,
                    )

        return None

    def _extract_dose_and_rate(self, substance_admin: SubstanceAdministration) -> list[FHIRResourceDict]:
        """Extract dose and rate from doseQuantity and rateQuantity."""
        dose_and_rate_list = []
        dose_and_rate: JSONObject = {}

        # DoseQuantity
        if substance_admin.dose_quantity:
            dose_qty = substance_admin.dose_quantity
            if isinstance(dose_qty, PQ):
                quantity = self.create_quantity(
                    value=self._extract_period_value(dose_qty),
                    unit=dose_qty.unit
                )
                if quantity:
                    dose_and_rate["doseQuantity"] = quantity
            elif isinstance(dose_qty, IVL_PQ):
                # If range, use low
                if dose_qty.low:
                    quantity = self.create_quantity(
                        value=self._extract_period_value(dose_qty.low),
                        unit=dose_qty.low.unit
                    )
                    if quantity:
                        dose_and_rate["doseQuantity"] = quantity

        # RateQuantity
        if substance_admin.rate_quantity:
            rate_qty = substance_admin.rate_quantity
            if isinstance(rate_qty, PQ):
                quantity = self.create_quantity(
                    value=self._extract_period_value(rate_qty),
                    unit=rate_qty.unit
                )
                if quantity:
                    dose_and_rate["rateQuantity"] = quantity

        if dose_and_rate:
            dose_and_rate_list.append(dose_and_rate)

        return dose_and_rate_list

    def _extract_max_dose_per_period(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract maxDosePerPeriod from maxDoseQuantity (RTO type).

        C-CDA maxDoseQuantity is RTO with numerator and denominator.
        FHIR maxDosePerPeriod is a Ratio with numerator and denominator Quantity.
        """
        if not substance_admin.max_dose_quantity:
            return None

        max_dose = substance_admin.max_dose_quantity

        ratio: JSONObject = {}

        if max_dose.numerator:
            numerator = self.create_quantity(
                value=self._extract_period_value(max_dose.numerator),
                unit=max_dose.numerator.unit
            )
            if numerator:
                ratio["numerator"] = numerator

        if max_dose.denominator:
            denominator = self.create_quantity(
                value=self._extract_period_value(max_dose.denominator),
                unit=max_dose.denominator.unit
            )
            if denominator:
                ratio["denominator"] = denominator

        return ratio if ratio else None

    def _extract_dispense_request(
        self, substance_admin: SubstanceAdministration
    ) -> JSONObject | None:
        """Extract dispenseRequest from Supply order entry relationships.

        C-CDA repeatNumber on SubstanceAdministration OR on Supply Order
        represents the number of refills.
        FHIR numberOfRepeatsAllowed = C-CDA repeatNumber - 1
        """
        dispense_request: JSONObject = {}

        # Check repeatNumber on SubstanceAdministration
        if substance_admin.repeat_number:
            repeat_num = substance_admin.repeat_number
            if hasattr(repeat_num, 'value') and repeat_num.value is not None:
                try:
                    ccda_repeat = int(repeat_num.value)
                    # C-CDA repeatNumber = FHIR numberOfRepeatsAllowed + 1
                    fhir_repeats = max(0, ccda_repeat - 1)
                    dispense_request["numberOfRepeatsAllowed"] = fhir_repeats
                except (ValueError, TypeError):
                    pass

        # Check for Supply Order in entry relationships
        if substance_admin.entry_relationship:
            for rel in substance_admin.entry_relationship:
                if rel.type_code == TypeCodes.REFERENCE and rel.supply:
                    supply = rel.supply

                    # Quantity from Supply
                    if supply.quantity:
                        quantity = self.create_quantity(
                            value=self._extract_period_value(supply.quantity),
                            unit=supply.quantity.unit
                        )
                        if quantity:
                            dispense_request["quantity"] = quantity

                    # Validity period from Supply.effectiveTime
                    if supply.effective_time:
                        eff_time = supply.effective_time
                        validity_period = {}
                        if eff_time.low and eff_time.low.value:
                            start = self.convert_date(eff_time.low.value)
                            if start:
                                validity_period["start"] = start
                        if eff_time.high and eff_time.high.value:
                            end = self.convert_date(eff_time.high.value)
                            if end:
                                validity_period["end"] = end
                        if validity_period:
                            dispense_request["validityPeriod"] = validity_period

                    # RepeatNumber from Supply overrides SubstanceAdministration
                    if supply.repeat_number:
                        if hasattr(supply.repeat_number, 'high') and supply.repeat_number.high:
                            try:
                                ccda_repeat = int(supply.repeat_number.high.value)
                                fhir_repeats = max(0, ccda_repeat - 1)
                                dispense_request["numberOfRepeatsAllowed"] = fhir_repeats
                            except (ValueError, TypeError, AttributeError):
                                pass

        return dispense_request if dispense_request else None

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


def convert_medication_activity(
    substance_admin: SubstanceAdministration,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> FHIRResourceDict:
    """Convert a Medication Activity to a FHIR MedicationRequest resource.

    Also extracts nested MedicationDispense resources from entryRelationships.

    Args:
        substance_admin: The SubstanceAdministration (Medication Activity)
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing author metadata
        section: The C-CDA Section containing this medication (for narrative)

    Returns:
        FHIR MedicationRequest resource as a dictionary
    """
    converter = MedicationRequestConverter(
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )

    try:
        medication_request = converter.convert(substance_admin, section=section)

        # Store author metadata if callback provided
        if metadata_callback and medication_request.get("id"):
            metadata_callback(
                resource_type="MedicationRequest",
                resource_id=medication_request["id"],
                ccda_element=substance_admin,
                concern_act=None,
            )

        # Extract nested medication dispenses
        from ccda_to_fhir.converters.medication_dispense import extract_medication_dispenses
        extract_medication_dispenses(
            substance_admin,
            code_system_mapper=code_system_mapper,
            reference_registry=reference_registry,
        )

        return medication_request
    except Exception:
        # Log error
        logger.error("Error converting medication activity", exc_info=True)
        raise


def get_medication_resources() -> list[FHIRResourceDict]:
    """Get all Medication resources created during conversion.

    Returns:
        List of FHIR Medication resources
    """
    return list(_medication_registry.values())


def clear_medication_registry() -> None:
    """Clear the medication registry.

    Should be called at the start of each document conversion.
    """
    _medication_registry.clear()
