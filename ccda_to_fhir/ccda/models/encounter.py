"""C-CDA Encounter models.

Encounters represent patient encounters/visits.
Used for Encounter Activity and related templates.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-EncounterActivity.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, model_validator

from .author import Author
from .datatypes import CD, CE, CS, ED, II, IVL_TS, CDAModel
from .participant import Participant
from .performer import Performer

if TYPE_CHECKING:
    from .act import Reference
    from .clinical_document import Informant
    from .observation import EntryRelationship
    from .substance_administration import Precondition


class Encounter(CDAModel):
    """Encounter Activity.

    Represents a patient encounter or visit.
    Template ID: 2.16.840.1.113883.10.20.22.4.49

    Mood codes:
    - EVN: Completed encounter
    - INT: Planned encounter
    """

    # Fixed structural attributes
    class_code: str | None = Field(default="ENC", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Template IDs
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Encounter type code (e.g., ambulatory, inpatient, emergency)
    code: CD | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Encounter time (start and end)
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Discharge disposition (for inpatient encounters)
    sdtc_discharge_disposition_code: CE | None = Field(
        default=None, alias="sdtc:dischargeDispositionCode"
    )

    # Priority code
    priority_code: CE | None = Field(default=None, alias="priorityCode")

    # Performers (care team for the encounter)
    performer: list[Performer] | None = None

    # Authors
    author: list[Author] | None = None

    # Participants (location, responsible party)
    participant: list[Participant] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Entry relationships (diagnoses, indications)
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )

    # References
    reference: list[Reference] | None = None

    # Preconditions
    precondition: list[Precondition] | None = None

    def _has_template(self, template_id: str, extension: str | None = None) -> bool:
        """Check if this encounter has a specific template ID.

        Args:
            template_id: The template ID root to check for
            extension: Optional template extension to match

        Returns:
            True if template ID is present, False otherwise
        """
        if not self.template_id:
            return False

        for tid in self.template_id:
            if tid.root == template_id:
                if extension is None or tid.extension == extension:
                    return True
        return False

    @model_validator(mode='after')
    def validate_encounter_activity(self) -> Encounter:
        """Validate Encounter Activity template (2.16.840.1.113883.10.20.22.4.49).

        Reference: docs/ccda/activity-encounter.md

        Conformance requirements from C-CDA R2.1/R5.0:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] effectiveTime

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        # Only validate if this is an Encounter Activity
        if not self._has_template("2.16.840.1.113883.10.20.22.4.49"):
            return self

        # 1. SHALL contain at least one id
        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Encounter Activity (2.16.840.1.113883.10.20.22.4.49): "
                "SHALL contain at least one [1..*] id"
            )

        # Note: C-CDA spec says code is SHALL (1..1), but real-world documents from
        # OpenVista CareVue and other EHR systems often omit the encounter code element.
        # Making this optional to handle real-world C-CDA documents.

        # 3. SHALL contain exactly one effectiveTime
        if not self.effective_time:
            raise ValueError(
                "Encounter Activity (2.16.840.1.113883.10.20.22.4.49): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        return self
