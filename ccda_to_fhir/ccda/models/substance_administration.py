"""C-CDA SubstanceAdministration models.

SubstanceAdministration represents medication and immunization activities.
Used for Medication Activity, Immunization Activity, and related templates.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationActivity.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ImmunizationActivity.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .author import Author
from .datatypes import (
    AD,
    BL,
    CD,
    CE,
    CS,
    ED,
    EIVL_TS,
    EN,
    II,
    INT,
    IVL_INT,
    IVL_PQ,
    IVL_TS,
    MO,
    ON,
    PIVL_TS,
    PN,
    PQ,
    REAL,
    RTO,
    ST,
    SXCM_TS,
    TEL,
    TN,
    TS,
    CDAModel,
)
from .participant import Participant
from .performer import Performer

if TYPE_CHECKING:
    from .act import Reference
    from .clinical_document import Informant
    from .observation import EntryRelationship


class ManufacturedMaterial(CDAModel):
    """Manufactured material (medication/vaccine product).

    Contains the product code (RxNorm, NDC, CVX) and name.
    """

    # Template ID (if applicable)
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Product code (RxNorm, NDC, CVX, etc.)
    code: CE | None = None

    # Lot number (for immunizations)
    lot_number_text: str | None = Field(default=None, alias="lotNumberText")

    # Product name
    name: str | None = None


class ManufacturerOrganization(CDAModel):
    """Organization that manufactured the product."""

    id: list[II] | None = None
    name: list[ON | str] | None = None


class ManufacturedProduct(CDAModel):
    """Manufactured product information.

    Contains the medication or vaccine product details.
    Template ID: 2.16.840.1.113883.10.20.22.4.23 (Medication Information)
    Template ID: 2.16.840.1.113883.10.20.22.4.54 (Immunization Medication Information)
    """

    # Class code
    class_code: str | None = Field(default="MANU", alias="classCode")

    # Template ID
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Product IDs
    id: list[II] | None = None

    # The manufactured material
    manufactured_material: ManufacturedMaterial | None = Field(
        default=None, alias="manufacturedMaterial"
    )

    # Manufacturer
    manufacturer_organization: ManufacturerOrganization | None = Field(
        default=None, alias="manufacturerOrganization"
    )


class Consumable(CDAModel):
    """Consumable containing the medication/vaccine product."""

    type_code: str | None = Field(default="CSM", alias="typeCode")
    manufactured_product: ManufacturedProduct | None = Field(
        default=None, alias="manufacturedProduct"
    )


class Precondition(CDAModel):
    """Precondition for medication administration.

    Defines conditions that must be met before administration.
    """

    type_code: str | None = Field(default="PRCN", alias="typeCode")
    criterion: Criterion | None = None


class Criterion(CDAModel):
    """Criterion within a precondition."""

    class_code: str | None = Field(default="OBS", alias="classCode")
    mood_code: str | None = Field(default="EVN.CRT", alias="moodCode")
    code: CE | None = None
    text: ED | None = None
    # Value can be various types per HL7 V3 spec
    value: (
        CD
        | CE
        | CS
        | ST
        | ED
        | BL
        | INT
        | REAL
        | PQ
        | MO
        | IVL_PQ
        | IVL_INT
        | IVL_TS
        | TS
        | PIVL_TS
        | EIVL_TS
        | RTO
        | II
        | TEL
        | AD
        | EN
        | PN
        | TN
        | ON
        | None
    ) = None


class SubstanceAdministration(CDAModel):
    """Substance administration (medication/immunization).

    Represents medication or immunization activities.
    Base model for:
    - Medication Activity (2.16.840.1.113883.10.20.22.4.16)
    - Immunization Activity (2.16.840.1.113883.10.20.22.4.52)
    - Admission Medication
    - Discharge Medication
    - And others...
    """

    # Fixed structural attributes
    class_code: str | None = Field(default="SBADM", alias="classCode")

    # Mood code: INT (intent/order) or EVN (event/administered)
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Negation indicator (true = "not given")
    negation_ind: bool | None = Field(default=None, alias="negationInd")

    # Template IDs identifying the activity type
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Code (for immunizations this may contain the vaccine type)
    code: CE | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code (active, completed, aborted, cancelled, suspended)
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Effective time - can be various types per C-CDA spec:
    # 1. IVL_TS for medication period (low/high)
    # 2. PIVL_TS for frequency (period)
    # 3. EIVL_TS for event-based timing (PRN)
    # 4. SXCM_TS for sequence of time stamps
    # 5. TS for single timestamp
    # Multiple effectiveTime elements allowed (one for period, one for frequency)
    effective_time: list[IVL_TS | PIVL_TS | EIVL_TS | SXCM_TS | TS] | None = Field(
        default=None, alias="effectiveTime"
    )

    # Priority code
    priority_code: CE | None = Field(default=None, alias="priorityCode")

    # Repeat number (number of doses/refills)
    repeat_number: IVL_PQ | None = Field(default=None, alias="repeatNumber")

    # Route of administration (oral, IV, etc.)
    route_code: CE | None = Field(default=None, alias="routeCode")

    # Approach site (body site)
    approach_site_code: list[CE] | None = Field(default=None, alias="approachSiteCode")

    # Dose quantity
    dose_quantity: PQ | IVL_PQ | None = Field(default=None, alias="doseQuantity")

    # Rate quantity (for IV)
    rate_quantity: PQ | IVL_PQ | None = Field(default=None, alias="rateQuantity")

    # Maximum dose quantity
    max_dose_quantity: PQ | None = Field(default=None, alias="maxDoseQuantity")

    # Administration unit code (tablet, capsule, etc.)
    administration_unit_code: CE | None = Field(default=None, alias="administrationUnitCode")

    # The consumable (medication/vaccine product)
    consumable: Consumable | None = None

    # Authors (prescriber)
    author: list[Author] | None = None

    # Performers (who administered)
    performer: list[Performer] | None = None

    # Participants (drug vehicle, etc.)
    participant: list[Participant] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Entry relationships (indications, instructions, supply, dispense, reactions)
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )

    # Preconditions
    precondition: list[Precondition] | None = None

    # References
    reference: list[Reference] | None = None
