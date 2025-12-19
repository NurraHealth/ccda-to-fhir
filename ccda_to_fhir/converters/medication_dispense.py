"""MedicationDispense converter: C-CDA Medication Dispense to FHIR MedicationDispense resource."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.ccda.models.datatypes import IVL_TS
from ccda_to_fhir.ccda.models.supply import Supply
from ccda_to_fhir.constants import (
    MEDICATION_DISPENSE_STATUS_TO_FHIR,
    FHIRCodes,
    TemplateIds,
)

from ccda_to_fhir.logging_config import get_logger

from .base import BaseConverter

logger = get_logger(__name__)


class MedicationDispenseConverter(BaseConverter[Supply]):
    """Convert C-CDA Medication Dispense to FHIR MedicationDispense resource.

    This converter handles the mapping from C-CDA Supply element
    (Medication Dispense template 2.16.840.1.113883.10.20.22.4.18) with
    moodCode="EVN" to a FHIR R4B MedicationDispense resource.

    MedicationDispense represents the actual dispensing/supply of medication
    to a patient, documenting when, where, and by whom it was dispensed.

    Note: dosageInstruction is a US Core Must Support element but is not
    currently implemented. In C-CDA, dosage instructions are stored in the
    parent Medication Activity (SubstanceAdministration), not in the Supply
    element. To populate dosageInstruction, the converter would need access
    to the parent Medication Activity context.

    Reference: http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense
    """

    def __init__(self, *args, **kwargs):
        """Initialize the medication dispense converter."""
        super().__init__(*args, **kwargs)

    def convert(self, supply: Supply, parent_medication_request_id: str | None = None) -> FHIRResourceDict:
        """Convert a C-CDA Medication Dispense to a FHIR MedicationDispense.

        Args:
            supply: The C-CDA Supply (Medication Dispense)
            parent_medication_request_id: Optional ID of parent MedicationRequest for authorizingPrescription

        Returns:
            FHIR MedicationDispense resource as a dictionary

        Raises:
            ValueError: If the supply lacks required data or has invalid moodCode
        """
        # Validation
        if not supply.product:
            raise ValueError("Medication Dispense must have a product (medication)")

        if supply.mood_code != "EVN":
            raise ValueError(
                f"Medication Dispense must have moodCode='EVN' (event), got '{supply.mood_code}'"
            )

        med_dispense: JSONObject = {
            "resourceType": "MedicationDispense",
        }

        # US Core profile
        med_dispense["meta"] = {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense"
            ]
        }

        # 1. Generate ID from supply identifier
        if supply.id and len(supply.id) > 0:
            first_id = supply.id[0]
            med_dispense["id"] = self.generate_resource_id(
                first_id.root,
                first_id.extension,
                "medicationdispense",
            )

        # 2. Identifiers
        if supply.id:
            identifiers = []
            for id_elem in supply.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                med_dispense["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(supply)
        med_dispense["status"] = status

        # 4. Category (default to community)
        med_dispense["category"] = {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                    "code": "community",
                    "display": "Community",
                }
            ]
        }

        # 5. Medication (required) - use medicationCodeableConcept for simple cases
        medication = self._extract_medication(supply)
        if medication:
            med_dispense["medicationCodeableConcept"] = medication

        # 6. Subject (patient reference) - required
        if self.reference_registry:
            med_dispense["subject"] = self.reference_registry.get_patient_reference()
        else:
            # Fallback for unit tests without registry
            med_dispense["subject"] = {"reference": "Patient/patient-unknown"}

        # 6b. Context (encounter reference) - US Core Must Support
        if self.reference_registry:
            encounter_ref = self.reference_registry.get_encounter_reference()
            if encounter_ref:
                med_dispense["context"] = encounter_ref

        # 7. Performer (pharmacy/pharmacist)
        performers = self._extract_performers(supply)
        if performers:
            med_dispense["performer"] = performers

        # 8. AuthorizingPrescription (reference to parent MedicationRequest)
        if parent_medication_request_id:
            med_dispense["authorizingPrescription"] = [
                {"reference": f"MedicationRequest/{parent_medication_request_id}"}
            ]

        # 9. Type (inferred from repeatNumber)
        dispense_type = self._infer_dispense_type(supply)
        if dispense_type:
            med_dispense["type"] = dispense_type

        # 10. Quantity
        if supply.quantity and supply.quantity.value:
            # Convert value to number if it's a string
            try:
                value = float(supply.quantity.value) if isinstance(supply.quantity.value, str) else supply.quantity.value
            except (ValueError, TypeError):
                value = None

            if value is not None:
                quantity = self.create_quantity(value, supply.quantity.unit)
                if quantity:
                    med_dispense["quantity"] = quantity

        # 11. DaysSupply (from nested Days Supply entry relationship)
        days_supply = self._extract_days_supply(supply)
        if days_supply:
            med_dispense["daysSupply"] = days_supply

        # 12. WhenPrepared and WhenHandedOver (from effectiveTime)
        timing = self._extract_timing(supply)
        if timing:
            if "whenPrepared" in timing:
                med_dispense["whenPrepared"] = timing["whenPrepared"]
            if "whenHandedOver" in timing:
                med_dispense["whenHandedOver"] = timing["whenHandedOver"]

        # US Core constraint: whenHandedOver SHALL be present if status='completed'
        # If status is completed but no whenHandedOver, adjust status to unknown
        if med_dispense["status"] == "completed" and "whenHandedOver" not in med_dispense:
            logger.warning(
                "MedicationDispense has status='completed' but no whenHandedOver timestamp. "
                "Setting status to 'unknown' per US Core constraint us-core-20."
            )
            med_dispense["status"] = "unknown"

        # 13. Substitution (detect if medication differs from parent)
        # Note: Cannot fully implement without parent medication reference
        # For now, default to no substitution
        med_dispense["substitution"] = {"wasSubstituted": False}

        return med_dispense

    def _determine_status(self, supply: Supply) -> str:
        """Map C-CDA statusCode to FHIR MedicationDispense status.

        Per mapping specification: docs/mapping/15-medication-dispense.md

        Args:
            supply: The C-CDA Supply element

        Returns:
            FHIR MedicationDispense status code
        """
        if not supply.status_code or not supply.status_code.code:
            return FHIRCodes.MedicationDispenseStatus.COMPLETED

        status_code = supply.status_code.code

        return MEDICATION_DISPENSE_STATUS_TO_FHIR.get(
            status_code, FHIRCodes.MedicationDispenseStatus.COMPLETED
        )

    def _extract_medication(self, supply: Supply) -> JSONObject | None:
        """Extract medication code as medicationCodeableConcept.

        Args:
            supply: The C-CDA Supply element

        Returns:
            FHIR CodeableConcept for medication
        """
        if not supply.product:
            return None

        manufactured_product = supply.product
        if not manufactured_product.manufactured_material:
            return None

        manufactured_material = manufactured_product.manufactured_material
        if not manufactured_material.code:
            return None

        med_code = manufactured_material.code

        # Extract translations
        translations = None
        if hasattr(med_code, "translation") and med_code.translation:
            translations = []
            for trans in med_code.translation:
                if trans.code and trans.code_system:
                    translations.append(
                        {
                            "code": trans.code,
                            "code_system": trans.code_system,
                            "display_name": trans.display_name,
                        }
                    )

        return self.create_codeable_concept(
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

    def _extract_performers(self, supply: Supply) -> list[JSONObject] | None:
        """Extract performers (pharmacy/pharmacist) from supply.

        Args:
            supply: The C-CDA Supply element

        Returns:
            List of FHIR performer objects
        """
        performers = []

        # From performer element (pharmacy/pharmacist)
        if supply.performer:
            for perf in supply.performer:
                if not perf.assigned_entity:
                    continue

                assigned = perf.assigned_entity
                performer_obj: JSONObject = {}

                # Determine if it's a practitioner or organization
                if hasattr(assigned, "assigned_person") and assigned.assigned_person:
                    # Practitioner
                    if hasattr(assigned, "id") and assigned.id:
                        for id_elem in assigned.id:
                            if id_elem.root:
                                pract_id = self.generate_resource_id(
                                    id_elem.root,
                                    id_elem.extension,
                                    "practitioner",
                                )
                                performer_obj["actor"] = {
                                    "reference": f"Practitioner/{pract_id}"
                                }
                                break

                    # Add function (default to finalchecker)
                    performer_obj["function"] = {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
                                "code": "finalchecker",
                                "display": "Final Checker",
                            }
                        ]
                    }

                    if performer_obj.get("actor"):
                        performers.append(performer_obj)

        # From author element (pharmacist who packaged)
        if supply.author:
            for author in supply.author:
                if not hasattr(author, "assigned_author") or not author.assigned_author:
                    continue

                assigned = author.assigned_author

                if hasattr(assigned, "assigned_person") and assigned.assigned_person:
                    if hasattr(assigned, "id") and assigned.id:
                        for id_elem in assigned.id:
                            if id_elem.root:
                                pract_id = self.generate_resource_id(
                                    id_elem.root,
                                    id_elem.extension,
                                    "practitioner",
                                )
                                performer_obj = {
                                    "function": {
                                        "coding": [
                                            {
                                                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
                                                "code": "packager",
                                                "display": "Packager",
                                            }
                                        ]
                                    },
                                    "actor": {"reference": f"Practitioner/{pract_id}"},
                                }
                                performers.append(performer_obj)
                                break

        return performers if performers else None

    def _infer_dispense_type(self, supply: Supply) -> JSONObject | None:
        """Infer dispense type from repeatNumber.

        Args:
            supply: The C-CDA Supply element

        Returns:
            FHIR CodeableConcept for dispense type
        """
        from ccda_to_fhir.ccda.models.datatypes import IVL_INT

        if not supply.repeat_number:
            return None

        # repeatNumber can be IVL_INT (with low/high) or just have attributes directly
        # In most cases, it's a single value stored in the low field
        repeat_value = None
        if isinstance(supply.repeat_number, IVL_INT):
            if supply.repeat_number.low and supply.repeat_number.low.value is not None:
                repeat_value = supply.repeat_number.low.value
        elif hasattr(supply.repeat_number, "value"):
            repeat_value = supply.repeat_number.value

        if repeat_value is None:
            return None

        try:
            repeat_num = int(repeat_value)
        except (ValueError, TypeError):
            return None

        if repeat_num == 1:
            # First fill
            return {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
                        "code": "FF",
                        "display": "First Fill",
                    }
                ]
            }
        elif repeat_num > 1:
            # Refill
            return {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
                        "code": "RF",
                        "display": "Refill",
                    }
                ]
            }

        return None

    def _extract_days_supply(self, supply: Supply) -> JSONObject | None:
        """Extract days supply from nested Days Supply template.

        Args:
            supply: The C-CDA Supply element

        Returns:
            FHIR SimpleQuantity for days supply
        """
        if not supply.entry_relationship:
            return None

        # Look for Days Supply template (2.16.840.1.113883.10.20.37.3.10)
        for entry_rel in supply.entry_relationship:
            if not hasattr(entry_rel, "supply") or not entry_rel.supply:
                continue

            nested_supply = entry_rel.supply

            # Check if it's a Days Supply template
            if hasattr(nested_supply, "template_id") and nested_supply.template_id:
                for template_id in nested_supply.template_id:
                    if template_id.root == "2.16.840.1.113883.10.20.37.3.10":
                        # This is a Days Supply
                        if nested_supply.quantity and nested_supply.quantity.value:
                            # Convert value to number if it's a string
                            try:
                                value = (
                                    float(nested_supply.quantity.value)
                                    if isinstance(nested_supply.quantity.value, str)
                                    else nested_supply.quantity.value
                                )
                            except (ValueError, TypeError):
                                value = None

                            if value is not None:
                                return self.create_quantity(
                                    value,
                                    nested_supply.quantity.unit,
                                )

        return None

    def _extract_timing(self, supply: Supply) -> JSONObject | None:
        """Extract whenPrepared and whenHandedOver from effectiveTime.

        Args:
            supply: The C-CDA Supply element

        Returns:
            Dictionary with whenPrepared and/or whenHandedOver
        """
        if not supply.effective_time:
            return None

        timing: JSONObject = {}
        eff_time = supply.effective_time

        # IVL_TS can have either a single value (point in time) or low/high (period)
        if isinstance(eff_time, IVL_TS):
            # Check for single value first (point in time)
            if eff_time.value:
                when_handed_over = self.convert_date(eff_time.value)
                if when_handed_over:
                    timing["whenHandedOver"] = when_handed_over
            # Check for period (low/high)
            else:
                if eff_time.low and eff_time.low.value:
                    when_prepared = self.convert_date(eff_time.low.value)
                    if when_prepared:
                        timing["whenPrepared"] = when_prepared

                if eff_time.high and eff_time.high.value:
                    when_handed_over = self.convert_date(eff_time.high.value)
                    if when_handed_over:
                        timing["whenHandedOver"] = when_handed_over

        return timing if timing else None
