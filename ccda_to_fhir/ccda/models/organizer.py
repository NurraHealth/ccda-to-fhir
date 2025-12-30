"""C-CDA Organizer models.

Organizers group related clinical entries together.
Used for Results Organizer, Vital Signs Organizer, and other groupings.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultOrganizer.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-VitalSignsOrganizer.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, model_validator

from .author import Author
from .datatypes import CD, CS, ED, II, IVL_TS, CDAModel
from .participant import Participant
from .performer import Performer
from .procedure import Specimen

if TYPE_CHECKING:
    from .act import Act, Reference
    from .clinical_document import Informant
    from .observation import Observation
    from .procedure import Procedure
    from .substance_administration import Precondition, SubstanceAdministration
    from .supply import Supply


class OrganizerComponent(CDAModel):
    """Component within an organizer.

    Contains the individual observations or other clinical statements
    that are grouped by the organizer.
    """

    type_code: str | None = Field(default="COMP", alias="typeCode")
    sequence_number: int | None = Field(default=None, alias="sequenceNumber")
    context_conduction_ind: bool | None = Field(default=None, alias="contextConductionInd")

    # The contained clinical statement
    observation: Observation | None = None
    procedure: Procedure | None = None
    act: Act | None = None
    substance_administration: SubstanceAdministration | None = Field(
        default=None, alias="substanceAdministration"
    )
    supply: Supply | None = None
    organizer: Organizer | None = None  # Nested organizers


class Organizer(CDAModel):
    """Clinical organizer.

    Groups related clinical entries together.
    Base model for:
    - Result Organizer (2.16.840.1.113883.10.20.22.4.1)
    - Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26)
    - Functional Status Organizer (2.16.840.1.113883.10.20.22.4.66)
    - Drug Monitoring Act (2.16.840.1.113883.10.20.22.4.123)
    - And others...

    Common class codes:
    - BATTERY: A set of observations produced by a battery (e.g., lab panel)
    - CLUSTER: A grouping of observations
    """

    # Class code (BATTERY for lab panels, CLUSTER for vital signs) - required
    class_code: str = Field(alias="classCode")

    # Mood code (typically EVN for event)
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Template IDs
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Organizer code (e.g., LOINC panel code)
    code: CD | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code (typically completed)
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Effective time (when the panel/group was performed)
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Specimens
    specimen: list[Specimen] | None = None

    # Authors
    author: list[Author] | None = None

    # Performers
    performer: list[Performer] | None = None

    # Participants
    participant: list[Participant] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Components (the grouped observations/entries)
    component: list[OrganizerComponent] | None = None

    # References
    reference: list[Reference] | None = None

    # Preconditions
    precondition: list[Precondition] | None = None

    def _has_template(self, template_id: str, extension: str | None = None) -> bool:
        """Check if this organizer has a specific template ID.

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
    def validate_vital_signs_organizer(self) -> Organizer:
        """Validate Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26).

        Reference: docs/ccda/organizer-vital-signs.md

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode with code="completed"
        4. SHALL contain exactly one [1..1] effectiveTime
        5. SHALL contain at least one [1..*] component

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.26"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                "SHALL contain exactly one [1..1] statusCode"
            )
        if self.status_code.code != "completed":
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.effective_time:
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.component or len(self.component) == 0:
            raise ValueError(
                "Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26): "
                "SHALL contain at least one [1..*] component"
            )

        return self

    @model_validator(mode='after')
    def validate_result_organizer(self) -> Organizer:
        """Validate Result Organizer (2.16.840.1.113883.10.20.22.4.1).

        Reference: docs/ccda/organizer-results.md

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode
        4. SHALL contain at least one [1..*] component

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.1"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Result Organizer (2.16.840.1.113883.10.20.22.4.1): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Result Organizer (2.16.840.1.113883.10.20.22.4.1): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Result Organizer (2.16.840.1.113883.10.20.22.4.1): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        if not self.component or len(self.component) == 0:
            raise ValueError(
                "Result Organizer (2.16.840.1.113883.10.20.22.4.1): "
                "SHALL contain at least one [1..*] component"
            )

        return self
