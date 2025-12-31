"""Medication converter: C-CDA Manufactured Product to FHIR Medication resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.substance_administration import (
    ManufacturedProduct,
    SubstanceAdministration,
)
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

logger = get_logger(__name__)


class MedicationConverter(BaseConverter[ManufacturedProduct]):
    """Convert C-CDA Manufactured Product to FHIR Medication resource.

    This converter handles the mapping from C-CDA ManufacturedProduct
    (Medication Information template 2.16.840.1.113883.10.20.22.4.23) to a
    FHIR R4B Medication resource, including manufacturer details, form,
    and drug vehicle ingredients.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html
    """

    def __init__(self, *args, **kwargs):
        """Initialize the medication converter."""
        super().__init__(*args, **kwargs)

    def convert(
        self,
        manufactured_product: ManufacturedProduct,
        substance_admin: SubstanceAdministration | None = None,
    ) -> FHIRResourceDict:
        """Convert a C-CDA Manufactured Product to a FHIR Medication.

        Args:
            manufactured_product: The C-CDA ManufacturedProduct
            substance_admin: Optional SubstanceAdministration for additional context

        Returns:
            FHIR Medication resource as a dictionary

        Raises:
            ValueError: If the manufactured product lacks required data
        """
        # Validation
        if not manufactured_product.manufactured_material:
            raise ValueError("ManufacturedProduct must have a manufacturedMaterial")

        medication: JSONObject = {
            "resourceType": "Medication",
            "meta": {
                "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication"]
            },
        }

        # 1. Generate ID from product identifier or material code
        med_id = self._generate_medication_id(manufactured_product)
        medication["id"] = med_id

        # 2. Code (from manufacturedMaterial.code) - required
        if manufactured_product.manufactured_material.code:
            code_elem = manufactured_product.manufactured_material.code
            # Extract translations - convert CD objects to dictionaries
            translations = None
            if hasattr(code_elem, "translation") and code_elem.translation:
                translations = []
                for trans in code_elem.translation:
                    if trans.code and trans.code_system:
                        translations.append({
                            "code": trans.code,
                            "code_system": trans.code_system,
                            "display_name": trans.display_name,
                        })

            medication["code"] = self.create_codeable_concept(
                code=code_elem.code,
                code_system=code_elem.code_system,
                display_name=code_elem.display_name,
                original_text=(
                    self.extract_original_text(code_elem.original_text)
                    if code_elem.original_text
                    else None
                ),
                translations=translations,
            )

        # 3. Manufacturer (from manufacturerOrganization)
        if manufactured_product.manufacturer_organization:
            manufacturer_org = manufactured_product.manufacturer_organization
            if manufacturer_org.name:
                # Use first name - extract value from ON (Organization Name) object
                org_name = None
                if manufacturer_org.name and len(manufacturer_org.name) > 0:
                    first_name = manufacturer_org.name[0]
                    # Handle both ON objects and plain strings
                    if isinstance(first_name, str):
                        org_name = first_name
                    elif hasattr(first_name, "value") and first_name.value:
                        org_name = first_name.value
                    else:
                        org_name = str(first_name)

                if org_name:
                    # For now, just use display name. Could create Organization resource.
                    medication["manufacturer"] = {"display": org_name}

        # 4. Form (from administrationUnitCode in SubstanceAdministration)
        if substance_admin and substance_admin.administration_unit_code:
            form_code = substance_admin.administration_unit_code
            medication["form"] = self.create_codeable_concept(
                code=form_code.code,
                code_system=form_code.code_system,
                display_name=form_code.display_name,
            )

        # 5. Ingredients (from participant with typeCode="CSM" - drug vehicle)
        if substance_admin and substance_admin.participant:
            ingredients = self._extract_ingredients(substance_admin)
            if ingredients:
                medication["ingredient"] = ingredients

        # 6. Batch (lot number from manufacturedMaterial.lot_number_text)
        if manufactured_product.manufactured_material.lot_number_text:
            medication["batch"] = {
                "lotNumber": manufactured_product.manufactured_material.lot_number_text
            }

        return medication

    def _generate_medication_id(self, manufactured_product: ManufacturedProduct) -> str:
        """Generate a medication resource ID from C-CDA manufactured product.

        Uses standard ID generation with hashing for consistency across all converters.
        Falls back to material code if no ID present.

        Args:
            manufactured_product: The manufactured product

        Returns:
            A medication resource ID string
        """
        # Try to use product ID first
        if manufactured_product.id and len(manufactured_product.id) > 0:
            first_id = manufactured_product.id[0]
            return self.generate_resource_id(
                root=first_id.root,
                extension=first_id.extension,
                resource_type="medication"
            )

        # Fall back to material code
        if (
            manufactured_product.manufactured_material
            and manufactured_product.manufactured_material.code
            and manufactured_product.manufactured_material.code.code
        ):
            code = manufactured_product.manufactured_material.code.code
            return self.generate_resource_id(
                root=None,
                extension=None,
                resource_type="medication",
                fallback_context=code
            )

        raise ValueError(
            "Cannot generate Medication ID: no identifiers or material code provided. "
            "C-CDA ManufacturedProduct must have id element or manufacturedMaterial/code."
        )

    def _extract_ingredients(
        self, substance_admin: SubstanceAdministration
    ) -> list[FHIRResourceDict]:
        """Extract drug vehicle ingredients from participant elements.

        Drug vehicle participants (typeCode="CSM") map to Medication.ingredient
        with isActive=false.

        Args:
            substance_admin: The substance administration

        Returns:
            List of FHIR ingredient objects
        """
        ingredients = []

        for participant in substance_admin.participant:
            # Check for drug vehicle (CSM = consumable)
            if participant.type_code and participant.type_code.upper() == "CSM":
                if (
                    participant.participant_role
                    and participant.participant_role.playing_entity
                ):
                    playing_entity = participant.participant_role.playing_entity

                    # Extract code from playing entity
                    if playing_entity.code:
                        ingredient: JSONObject = {}

                        # Create itemCodeableConcept
                        item_code = self.create_codeable_concept(
                            code=playing_entity.code.code,
                            code_system=playing_entity.code.code_system,
                            display_name=playing_entity.code.display_name,
                        )
                        if item_code:
                            ingredient["itemCodeableConcept"] = item_code

                        # Drug vehicle is inactive ingredient
                        ingredient["isActive"] = False

                        if ingredient:
                            ingredients.append(ingredient)

        return ingredients


def convert_manufactured_product(
    manufactured_product: ManufacturedProduct,
    substance_admin: SubstanceAdministration | None = None,
    code_system_mapper=None,
) -> FHIRResourceDict:
    """Convert a Manufactured Product to a FHIR Medication resource.

    Args:
        manufactured_product: The ManufacturedProduct
        substance_admin: Optional SubstanceAdministration for additional context
        code_system_mapper: Optional code system mapper

    Returns:
        FHIR Medication resource as a dictionary
    """
    converter = MedicationConverter(code_system_mapper=code_system_mapper)

    try:
        medication = converter.convert(manufactured_product, substance_admin)
        return medication
    except Exception:
        # Log error
        logger.error("Error converting manufactured product to Medication", exc_info=True)
        raise
