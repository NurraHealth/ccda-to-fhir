"""C-CDA Supply models.

Supply represents medication supply orders and dispenses.
Used within Medication Activity entries.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationSupplyOrder.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-MedicationDispense.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .author import Author
from .datatypes import CE, CS, ED, II, IVL_INT, IVL_TS, PQ, CDAModel
from .performer import Performer

if TYPE_CHECKING:
    from .observation import EntryRelationship
    from .substance_administration import ManufacturedProduct


class Supply(CDAModel):
    """Medication Supply.

    Represents medication supply orders or dispense events.
    Templates:
    - Medication Supply Order (2.16.840.1.113883.10.20.22.4.17)
    - Medication Dispense (2.16.840.1.113883.10.20.22.4.18)

    Mood codes:
    - INT: Supply order (intent)
    - EVN: Dispense event
    """

    # Fixed structural attribute
    class_code: str | None = Field(default="SPLY", alias="classCode")

    # Mood code (INT for order, EVN for dispense)
    mood_code: str | None = Field(default=None, alias="moodCode")

    # Template IDs
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Code (optional)
    code: CE | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Effective time (validity period for order, dispense time for dispense)
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Repeat number (number of refills)
    repeat_number: IVL_INT | None = Field(default=None, alias="repeatNumber")

    # Quantity (amount dispensed per fill)
    quantity: PQ | None = None

    # Expected use time
    expected_use_time: IVL_TS | None = Field(default=None, alias="expectedUseTime")

    # Product (if different from parent medication activity)
    product: ManufacturedProduct | None = None

    # Authors (prescriber)
    author: list[Author] | None = None

    # Performers (dispensing pharmacy)
    performer: list[Performer] | None = None

    # Entry relationships
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )
