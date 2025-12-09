"""C-CDA Organizer models.

Organizers group related clinical entries together.
Used for Results Organizer, Vital Signs Organizer, and other groupings.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ResultOrganizer.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-VitalSignsOrganizer.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

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
