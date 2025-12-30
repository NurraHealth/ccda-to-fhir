"""MedicationStatement converter: C-CDA Medication Activity to FHIR MedicationStatement resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CD, CE, EIVL_TS, IVL_PQ, IVL_TS, PIVL_TS, PQ
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.constants import (
    EIVL_EVENT_TO_FHIR_WHEN,
    MEDICATION_STATUS_TO_FHIR_STATEMENT,
    UCUM_TO_FHIR_UNITS_OF_TIME,
    FHIRCodes,
    TemplateIds,
    TypeCodes,
)
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

logger = get_logger(__name__)


class MedicationStatementConverter(BaseConverter[SubstanceAdministration]):
    """Convert C-CDA Medication Activity to FHIR MedicationStatement resource.

    This converter handles the mapping from C-CDA SubstanceAdministration
    (Medication Activity template 2.16.840.1.113883.10.20.22.4.16) with
    moodCode="EVN" to a FHIR R4B MedicationStatement resource.

    MedicationStatement records medications that the patient has taken,
    is taking, or will take. It differs from MedicationRequest which
    represents prescribing intent.

    Reference: https://www.hl7.org/fhir/R4/medicationstatement.html
    """

    def __init__(self, *args, **kwargs):
        """Initialize the medication statement converter."""
        super().__init__(*args, **kwargs)

    def convert(self, substance_admin: SubstanceAdministration, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Medication Activity to a FHIR MedicationStatement.

        Args:
            substance_admin: The C-CDA SubstanceAdministration (Medication Activity)
            section: The C-CDA Section containing this medication (for narrative)

        Returns:
            FHIR MedicationStatement resource as a dictionary

        Raises:
            ValueError: If the substance administration lacks required data
        """
        # Validation
        if not substance_admin.consumable:
            raise ValueError("Medication Activity must have a consumable (medication)")

        med_statement: JSONObject = {
            "resourceType": "MedicationStatement",
        }

        # 1. Generate ID from substance administration identifier
        if substance_admin.id and len(substance_admin.id) > 0:
            first_id = substance_admin.id[0]
            med_statement["id"] = self._generate_medication_statement_id(
                first_id.root, first_id.extension
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
                med_statement["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(substance_admin)
        med_statement["status"] = status

        # 4. Medication (required) - use medicationCodeableConcept for simple cases
        medication = self._extract_medication(substance_admin)
        if medication:
            med_statement["medicationCodeableConcept"] = medication

        # 5. Subject (patient reference) - required
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create MedicationStatement without patient reference."
            )
        med_statement["subject"] = self.reference_registry.get_patient_reference()

        # 6. Effective[x] (from effectiveTime)
        effective = self._extract_effective_time(substance_admin)
        if effective:
            if "effectiveDateTime" in effective:
                med_statement["effectiveDateTime"] = effective["effectiveDateTime"]
            elif "effectivePeriod" in effective:
                med_statement["effectivePeriod"] = effective["effectivePeriod"]

        # 7. DateAsserted (from author time)
        date_asserted = self._extract_date_asserted(substance_admin)
        if date_asserted:
            med_statement["dateAsserted"] = date_asserted

        # 8. InformationSource (from latest author)
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
                    if hasattr(assigned, 'assigned_person') and assigned.assigned_person:
                        if hasattr(assigned, 'id') and assigned.id:
                            for id_elem in assigned.id:
                                if id_elem.root:
                                    pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                                    med_statement["informationSource"] = {
                                        "reference": f"Practitioner/{pract_id}"
                                    }
                                    break
                    # Check for device
                    elif hasattr(assigned, 'assigned_authoring_device') and assigned.assigned_authoring_device:
                        if hasattr(assigned, 'id') and assigned.id:
                            for id_elem in assigned.id:
                                if id_elem.root:
                                    device_id = self._generate_device_id(id_elem.root, id_elem.extension)
                                    med_statement["informationSource"] = {
                                        "reference": f"Device/{device_id}"
                                    }
                                    break

        # 9. ReasonCode (from indication entry relationship)
        reason_codes = self._extract_reason_codes(substance_admin)
        if reason_codes:
            med_statement["reasonCode"] = reason_codes

        # 10. Dosage (complex)
        dosage = self._extract_dosage(substance_admin)
        if dosage:
            med_statement["dosage"] = dosage

        # 11. Note (from notes)
        notes = self._extract_notes(substance_admin)
        if notes:
            med_statement["note"] = notes

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=substance_admin, section=section)
        if narrative:
            med_statement["text"] = narrative

        return med_statement

    def _generate_medication_statement_id(self, root: str | None, extension: str | None) -> str:
        """Generate a medication statement resource ID from C-CDA identifier.

        Uses standard ID generation with hashing for consistency across all converters.
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="medicationstatement"
        )

    def _determine_status(self, substance_admin: SubstanceAdministration) -> str:
        """Map C-CDA statusCode to FHIR MedicationStatement status.

        Per C-CDA on FHIR IG: C-CDA "completed" may mean "prescription writing completed"
        rather than "medication administration completed". When statusCode="completed"
        but effectiveTime contains future dates, map to FHIR "active" instead.

        Per FHIR R4 spec, MedicationStatement.status values:
        active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html
        """
        if not substance_admin.status_code:
            return FHIRCodes.MedicationStatementStatus.ACTIVE

        status_code = substance_admin.status_code.code

        # Special handling for "completed" status per C-CDA on FHIR IG guidance
        if status_code == "completed":
            # Check if medication has future dates in effectiveTime
            if self._has_future_dates(substance_admin):
                # Completed prescription with future dates → active medication
                return FHIRCodes.MedicationStatementStatus.ACTIVE

        # Use standard mapping for all other cases
        return MEDICATION_STATUS_TO_FHIR_STATEMENT.get(
            status_code, FHIRCodes.MedicationStatementStatus.ACTIVE
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

    def _extract_medication(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract medication code as medicationCodeableConcept."""
        if not substance_admin.consumable:
            return None

        consumable = substance_admin.consumable
        if not consumable.manufactured_product:
            return None

        manufactured_product = consumable.manufactured_product
        if not manufactured_product.manufactured_material:
            return None

        manufactured_material = manufactured_product.manufactured_material

        # Try to get medication information from code or name
        med_code = manufactured_material.code
        original_text = None

        # Extract original text from code's originalText if available
        if med_code and med_code.original_text:
            original_text = self.extract_original_text(med_code.original_text)

        # If code has nullFlavor or no original text, try to use the medication name
        if (not med_code or not med_code.code) and not original_text:
            if manufactured_material.name:
                original_text = manufactured_material.name

        # If we have neither code nor text, use fallback text to satisfy FHIR requirement
        # MedicationStatement requires medicationCodeableConcept or medicationReference
        if (not med_code or not med_code.code) and not original_text:
            original_text = "Medication information not available"
            logger.warning(
                "Medication Activity has no code or text. Using fallback text.",
                extra={"fallback_text": original_text}
            )

        # Extract translations - convert CD objects to dictionaries
        translations = None
        if med_code and hasattr(med_code, 'translation') and med_code.translation:
            translations = []
            for trans in med_code.translation:
                if trans.code and trans.code_system:
                    translations.append({
                        "code": trans.code,
                        "code_system": trans.code_system,
                        "display_name": trans.display_name,
                    })

        return self.create_codeable_concept(
            code=med_code.code if med_code else None,
            code_system=med_code.code_system if med_code else None,
            display_name=med_code.display_name if med_code else None,
            original_text=original_text,
            translations=translations,
        )

    def _extract_effective_time(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract effective time from effectiveTime elements.

        For MedicationStatement, effectiveTime represents when the medication was/is being taken.
        Can be effectiveDateTime (single point) or effectivePeriod (range).
        """
        if not substance_admin.effective_time:
            return None

        # Find IVL_TS for the medication period
        for eff_time in substance_admin.effective_time:
            if isinstance(eff_time, IVL_TS):
                # Check if it's a single value or a period
                if eff_time.value:
                    # Single datetime
                    date_val = self.convert_date(eff_time.value)
                    if date_val:
                        return {"effectiveDateTime": date_val}
                elif eff_time.low or eff_time.high:
                    # Period
                    period: JSONObject = {}
                    if eff_time.low and eff_time.low.value:
                        start = self.convert_date(eff_time.low.value)
                        if start:
                            period["start"] = start
                    if eff_time.high and eff_time.high.value:
                        end = self.convert_date(eff_time.high.value)
                        if end:
                            period["end"] = end
                    if period:
                        return {"effectivePeriod": period}

        return None

    def _extract_date_asserted(self, substance_admin: SubstanceAdministration) -> str | None:
        """Extract dateAsserted from author time.

        dateAsserted is when the statement was asserted/recorded.
        Use the earliest author time.
        """
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

    def _extract_dosage(
        self, substance_admin: SubstanceAdministration
    ) -> list[FHIRResourceDict]:
        """Extract dosage information from substance administration.

        Note: MedicationStatement.dosage is similar to MedicationRequest.dosageInstruction
        but represents what was/is taken rather than prescribing instructions.
        """
        dosage: JSONObject = {}

        # 1. Text (free text sig from substanceAdministration/text)
        if substance_admin.text and substance_admin.text.value:
            dosage["text"] = substance_admin.text.value

        # 2. Timing (from effectiveTime elements - frequency patterns)
        timing = self._extract_timing(substance_admin)
        if timing:
            dosage["timing"] = timing

        # 3. AsNeeded (from precondition)
        as_needed_concept = self._extract_as_needed(substance_admin)
        if as_needed_concept:
            dosage["asNeededCodeableConcept"] = as_needed_concept
        elif substance_admin.precondition:
            dosage["asNeededBoolean"] = True

        # 4. Route (from routeCode)
        if substance_admin.route_code:
            dosage["route"] = self.create_codeable_concept(
                code=substance_admin.route_code.code,
                code_system=substance_admin.route_code.code_system,
                display_name=substance_admin.route_code.display_name,
            )

        # 5. DoseAndRate (from doseQuantity)
        dose_and_rate = self._extract_dose_and_rate(substance_admin)
        if dose_and_rate:
            dosage["doseAndRate"] = dose_and_rate

        # 6. MaxDosePerPeriod (from maxDoseQuantity)
        max_dose = self._extract_max_dose_per_period(substance_admin)
        if max_dose:
            dosage["maxDosePerPeriod"] = max_dose

        return [dosage] if dosage else []

    def _extract_timing(self, substance_admin: SubstanceAdministration) -> JSONObject | None:
        """Extract timing from effectiveTime elements.

        C-CDA allows multiple effectiveTime elements:
        1. IVL_TS - medication period (used in effectivePeriod, not timing)
        2. PIVL_TS - periodic frequency (timing.repeat.frequency/period)
        3. EIVL_TS - event-based timing (timing.repeat.when)
        """
        if not substance_admin.effective_time:
            return None

        timing: JSONObject = {}
        repeat: JSONObject = {}

        # Find PIVL_TS for frequency and EIVL_TS for event-based timing
        pivl_ts = None
        eivl_ts = None

        for eff_time in substance_admin.effective_time:
            if isinstance(eff_time, PIVL_TS):
                pivl_ts = eff_time
            elif isinstance(eff_time, EIVL_TS):
                eivl_ts = eff_time

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
                period_value = self._extract_period_value(period.low)
                if period_value is not None:
                    repeat["period"] = period_value
                    repeat["periodUnit"] = self._map_ucum_to_fhir_unit(period.low.unit)
            if period.high:
                period_max = self._extract_period_value(period.high)
                if period_max is not None:
                    repeat["periodMax"] = period_max
        # Handle PQ (single value)
        elif isinstance(period, PQ):
            period_value = self._extract_period_value(period)
            if period_value is not None:
                repeat["period"] = period_value
                repeat["periodUnit"] = self._map_ucum_to_fhir_unit(period.unit)

        return repeat if repeat else None

    def _convert_eivl_to_repeat(self, eivl_ts: EIVL_TS) -> JSONObject | None:
        """Convert EIVL_TS (event-based timing) to FHIR Timing.repeat.

        EIVL_TS maps to timing.repeat.when for event-based dosing:
        - event.code → when (e.g., AC, ACM, PC, HS, WAKE)
        - offset → offset (duration after the event, converted to minutes)
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
        """Convert a PQ (physical quantity) with time unit to minutes."""
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

    def _extract_period_value(self, pq: PQ) -> int | float | None:
        """Extract numeric value from PQ with validation.

        Returns None if the value is unreasonably large (likely data error).
        """
        if pq.value is None:
            return 1
        try:
            value = float(pq.value)
            # Validate: reject absurdly large periods (> 10 years in any unit)
            # 10 years = 3650 days = 87600 hours = 5256000 minutes = 315360000 seconds
            # In months: 10 years = 120 months
            max_reasonable_value = 120 if (hasattr(pq, 'unit') and pq.unit in ['mo', 'm']) else 3650
            if value > max_reasonable_value:
                # Invalid period - return None to skip this timing info
                return None
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
        """Extract maxDosePerPeriod from maxDoseQuantity (RTO type)."""
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

    def _extract_notes(self, substance_admin: SubstanceAdministration) -> list[FHIRResourceDict]:
        """Extract notes from Comment Activity entry relationships."""
        notes = []

        if not substance_admin.entry_relationship:
            return notes

        for rel in substance_admin.entry_relationship:
            # Check for Comment Activity template
            if rel.act and rel.act.template_id:
                for template in rel.act.template_id:
                    if template.root == TemplateIds.COMMENT_ACTIVITY:
                        # Extract comment text
                        if rel.act.text and rel.act.text.value:
                            note: JSONObject = {
                                "text": rel.act.text.value
                            }
                            # Add author time if available
                            if rel.act.author and len(rel.act.author) > 0:
                                author = rel.act.author[0]
                                if author.time and author.time.value:
                                    time_str = self.convert_date(author.time.value)
                                    if time_str:
                                        note["time"] = time_str
                            notes.append(note)
                        break

        return notes

    def _generate_practitioner_id(self, root: str | None, extension: str | None) -> str:
        """Generate consistent Practitioner ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _generate_device_id(self, root: str | None, extension: str | None) -> str:
        """Generate consistent Device ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Device", root, extension)


def convert_medication_statement(
    substance_admin: SubstanceAdministration,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> FHIRResourceDict:
    """Convert a Medication Activity to a FHIR MedicationStatement resource.

    Also extracts nested MedicationDispense resources from entryRelationships.

    Args:
        substance_admin: The SubstanceAdministration (Medication Activity)
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing author metadata
        section: The C-CDA Section containing this medication (for narrative)

    Returns:
        FHIR MedicationStatement resource as a dictionary
    """
    converter = MedicationStatementConverter(
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )

    try:
        medication_statement = converter.convert(substance_admin, section=section)

        # Store author metadata if callback provided
        if metadata_callback and medication_statement.get("id"):
            metadata_callback(
                resource_type="MedicationStatement",
                resource_id=medication_statement["id"],
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

        return medication_statement
    except Exception:
        # Log error
        logger.error("Error converting medication activity to MedicationStatement", exc_info=True)
        raise
