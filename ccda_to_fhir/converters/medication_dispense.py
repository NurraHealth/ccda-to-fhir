"""MedicationDispense converter: C-CDA Medication Dispense to FHIR MedicationDispense resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.datatypes import AD, TEL
    from ccda_to_fhir.ccda.models.performer import RepresentedOrganization

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
            from ccda_to_fhir.id_generator import generate_id_from_identifiers
            first_id = supply.id[0]
            med_dispense["id"] = generate_id_from_identifiers(
                "MedicationDispense",
                first_id.root,
                first_id.extension,
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

        # 7. Performer (pharmacy/pharmacist) and Location (pharmacy)
        performers, location_ref = self._extract_performers_and_location(supply)
        if performers:
            med_dispense["performer"] = performers

        # 7b. Location (pharmacy location)
        if location_ref:
            med_dispense["location"] = {"reference": location_ref}

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

    def _extract_performers_and_location(self, supply: Supply) -> tuple[list[JSONObject] | None, str | None]:
        """Extract performers (pharmacy/pharmacist) and location (pharmacy) from supply.

        Also creates Location resource for pharmacy when representedOrganization is present.

        Args:
            supply: The C-CDA Supply element

        Returns:
            Tuple of (performer list, location reference string)
            - performer list: List of FHIR performer objects or None
            - location reference: Location reference (e.g., "Location/pharmacy-123") or None
        """
        performers = []
        location_ref = None

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
                                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                                pract_id = generate_id_from_identifiers(
                                    "Practitioner",
                                    id_elem.root,
                                    id_elem.extension,
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

                # Create Location resource from representedOrganization
                if hasattr(assigned, "represented_organization") and assigned.represented_organization:
                    location_ref = self._create_pharmacy_location(assigned.represented_organization)

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
                                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                                pract_id = generate_id_from_identifiers(
                                    "Practitioner",
                                    id_elem.root,
                                    id_elem.extension,
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

        return (performers if performers else None, location_ref)

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

    def _create_pharmacy_location(
        self,
        organization: "RepresentedOrganization"
    ) -> str | None:
        """Create Location resource for pharmacy organization.

        Maps C-CDA performer/representedOrganization to FHIR Location resource
        per mapping guidance: docs/mapping/15-medication-dispense.md (line 297-309).

        Args:
            organization: The representedOrganization element from performer

        Returns:
            Location reference (e.g., "Location/pharmacy-123") or None if creation fails

        Examples:
            >>> org = RepresentedOrganization(name=["Community Pharmacy"])
            >>> ref = self._create_pharmacy_location(org)
            >>> # Returns: "Location/pharmacy-..."
        """
        if not organization:
            return None

        if not self.reference_registry:
            # Cannot create Location without registry
            return None

        # Generate Location ID from organization identifiers or name
        location_id = self._generate_location_id(organization)

        # Check if already created
        if self.reference_registry.has_resource("Location", location_id):
            return f"Location/{location_id}"

        # Create Location resource
        location: JSONObject = {
            "resourceType": "Location",
            "id": location_id,
            "status": "active",
            "mode": "instance",
        }

        # Add name from organization (required by US Core)
        name = self._extract_organization_name(organization)
        if not name:
            # Name is required by US Core - cannot create Location without it
            return None

        location["name"] = name

        # Add type (pharmacy location)
        # Per FHIR standards, use RoleCode "PHARM" for pharmacy locations
        location["type"] = [{
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "PHARM",
                "display": "Pharmacy"
            }]
        }]

        # Add address if available
        if hasattr(organization, "addr") and organization.addr:
            address = self._convert_address(organization.addr)
            if address:
                location["address"] = address

        # Add telecom if available
        if hasattr(organization, "telecom") and organization.telecom:
            telecom_list = self._convert_telecom(organization.telecom)
            if telecom_list:
                location["telecom"] = telecom_list

        # Register Location resource
        self.reference_registry.register_resource(location)

        return f"Location/{location_id}"

    def _generate_location_id(self, organization: "RepresentedOrganization") -> str:
        """Generate FHIR Location ID from pharmacy organization.

        Uses organization identifiers if available, otherwise generates
        from organization name using cached ID generator.

        Args:
            organization: RepresentedOrganization element

        Returns:
            Generated Location ID

        Examples:
            >>> org = RepresentedOrganization(
            ...     id=[II(root="1.2.3.4", extension="PHARM-001")],
            ...     name=["Community Pharmacy"]
            ... )
            >>> location_id = self._generate_location_id(org)
            >>> # Returns: "location-pharm-001" or similar
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Try to use organization identifiers
        if hasattr(organization, "id") and organization.id:
            for id_elem in organization.id:
                if id_elem.root:
                    return generate_id_from_identifiers(
                        "Location",
                        id_elem.root,
                        id_elem.extension
                    )

        # Fallback: Generate from organization name
        name = self._extract_organization_name(organization)
        if name:
            # Use name as fallback context for deterministic ID generation
            return generate_id_from_identifiers(
                "Location",
                None,
                name
            )

        # Ultimate fallback: Generate random ID
        return generate_id_from_identifiers("Location", None, None)

    def _extract_organization_name(self, organization: "RepresentedOrganization") -> str | None:
        """Extract organization name from representedOrganization.

        Args:
            organization: RepresentedOrganization element

        Returns:
            Organization name string or None

        Examples:
            >>> org = RepresentedOrganization(name=["Community Pharmacy"])
            >>> name = self._extract_organization_name(org)
            >>> # Returns: "Community Pharmacy"
        """
        if not hasattr(organization, "name") or not organization.name:
            return None

        names = organization.name

        # Handle single name (string)
        if isinstance(names, str):
            return names

        # Handle list of names
        if isinstance(names, list) and len(names) > 0:
            first_name = names[0]

            # Handle string in list
            if isinstance(first_name, str):
                return first_name

            # Handle ON (OrganizationName) object
            if hasattr(first_name, "value") and first_name.value:
                return first_name.value

            # Fallback to string representation
            return str(first_name) if first_name else None

        return None

    def _convert_address(self, addresses: list["AD"] | "AD") -> JSONObject:
        """Convert C-CDA address to FHIR Address.

        Note: Location.address is 0..1 (single address), not array.
        If multiple addresses provided, uses the first one.

        Args:
            addresses: List of C-CDA AD or single AD

        Returns:
            FHIR Address object (or empty dict if no valid address)

        Examples:
            >>> addr = AD(
            ...     street_address_line=["123 Main St"],
            ...     city="Boston",
            ...     state="MA",
            ...     postal_code="02101"
            ... )
            >>> fhir_addr = self._convert_address(addr)
            >>> # Returns: {"line": ["123 Main St"], "city": "Boston", ...}
        """
        from ccda_to_fhir.constants import ADDRESS_USE_MAP

        # Normalize to list
        addr_list = addresses if isinstance(addresses, list) else [addresses]

        if not addr_list:
            return {}

        # Use first address
        addr = addr_list[0]
        fhir_address: JSONObject = {}

        # Use code (HP = home, WP = work, etc.)
        if hasattr(addr, "use") and addr.use:
            fhir_use = ADDRESS_USE_MAP.get(addr.use)
            if fhir_use:
                fhir_address["use"] = fhir_use

        # Street address lines
        if hasattr(addr, "street_address_line") and addr.street_address_line:
            fhir_address["line"] = addr.street_address_line

        # City
        if hasattr(addr, "city") and addr.city:
            fhir_address["city"] = addr.city if isinstance(addr.city, str) else addr.city[0]

        # State
        if hasattr(addr, "state") and addr.state:
            fhir_address["state"] = addr.state if isinstance(addr.state, str) else addr.state[0]

        # Postal code
        if hasattr(addr, "postal_code") and addr.postal_code:
            fhir_address["postalCode"] = (
                addr.postal_code if isinstance(addr.postal_code, str) else addr.postal_code[0]
            )

        # Country
        if hasattr(addr, "country") and addr.country:
            fhir_address["country"] = addr.country if isinstance(addr.country, str) else addr.country[0]

        return fhir_address if fhir_address else {}

    def _convert_telecom(self, telecoms: list["TEL"] | "TEL") -> list[JSONObject]:
        """Convert C-CDA telecom to FHIR ContactPoint.

        Parses URI schemes (tel:, fax:, mailto:, http:) and maps to FHIR system codes.

        Args:
            telecoms: List of C-CDA TEL or single TEL

        Returns:
            List of FHIR ContactPoint objects

        Examples:
            >>> tel = TEL(value="tel:+1-555-1234", use="WP")
            >>> contact_points = self._convert_telecom(tel)
            >>> # Returns: [{"system": "phone", "value": "+1-555-1234", "use": "work"}]
        """
        fhir_telecom: list[JSONObject] = []

        # Normalize to list
        telecom_list = telecoms if isinstance(telecoms, list) else [telecoms]

        for telecom in telecom_list:
            if not hasattr(telecom, "value") or not telecom.value:
                continue

            contact_point: JSONObject = {}

            # Parse value (tel:+1..., mailto:..., fax:..., http://...)
            value = telecom.value
            if value.startswith("tel:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value[4:]  # Remove "tel:" prefix
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]  # Remove "mailto:" prefix
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]  # Remove "fax:" prefix
            elif value.startswith("http:") or value.startswith("https:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                # Unknown format, store as-is (assume phone if no prefix)
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value

            # Map use code (HP = home, WP = work, etc.)
            if hasattr(telecom, "use") and telecom.use:
                # Simple mapping for common use codes
                use_map = {
                    "HP": "home",
                    "WP": "work",
                    "MC": "mobile",
                    "PG": "mobile"
                }
                fhir_use = use_map.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            if contact_point:
                fhir_telecom.append(contact_point)

        return fhir_telecom
