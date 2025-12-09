"""C-CDA Act models.

Acts represent clinical actions, concerns, and events.
Used for Problem Concern Act, Allergy Concern Act, and other acts.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ProblemConcernAct.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AllergyConcernAct.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .author import Author
from .datatypes import CD, CE, CS, ED, II, IVL_TS, CDAModel
from .participant import Participant
from .performer import Performer

if TYPE_CHECKING:
    from .clinical_document import Informant
    from .observation import EntryRelationship
    from .substance_administration import Precondition


class Act(CDAModel):
    """Clinical act.

    Represents a clinical action, concern, or event.
    Base model for:
    - Problem Concern Act (2.16.840.1.113883.10.20.22.4.3)
    - Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30)
    - Note Activity (2.16.840.1.113883.10.20.22.4.202)
    - Planned Act (2.16.840.1.113883.10.20.22.4.39)
    - And others...

    Concern Acts are containers that track the overall concern status
    for one or more observations. They represent whether the provider
    is still concerned about tracking the issue.
    """

    # Fixed structural attributes
    class_code: str | None = Field(default="ACT", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Negation indicator
    negation_ind: bool | None = Field(default=None, alias="negationInd")

    # Template IDs identifying the act type
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Act code (e.g., CONC for Concern)
    code: CD | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code (active, completed, aborted, suspended)
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Effective time (timeframe of the concern)
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Priority code
    priority_code: CE | None = Field(default=None, alias="priorityCode")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Authors
    author: list[Author] | None = None

    # Performers
    performer: list[Performer] | None = None

    # Participants
    participant: list[Participant] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Entry relationships (to contained observations)
    # For Concern Acts, typeCode="SUBJ" links to the Problem/Allergy Observation
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )

    # Reference to other entries
    reference: list[Reference] | None = None

    # Preconditions
    precondition: list[Precondition] | None = None


class Reference(CDAModel):
    """Reference to another entry or external document."""

    type_code: str | None = Field(default=None, alias="typeCode")
    external_document: ExternalDocument | None = Field(default=None, alias="externalDocument")
    external_act: ExternalAct | None = Field(default=None, alias="externalAct")
    external_observation: ExternalObservation | None = Field(
        default=None, alias="externalObservation"
    )
    external_procedure: ExternalProcedure | None = Field(default=None, alias="externalProcedure")


class ExternalDocument(CDAModel):
    """Reference to an external document."""

    class_code: str | None = Field(default="DOC", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CD | None = None
    text: ED | None = None
    set_id: II | None = Field(default=None, alias="setId")
    version_number: int | None = Field(default=None, alias="versionNumber")


class ExternalAct(CDAModel):
    """Reference to an external act."""

    class_code: str | None = Field(default="ACT", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CD | None = None
    text: ED | None = None


class ExternalObservation(CDAModel):
    """Reference to an external observation."""

    class_code: str | None = Field(default="OBS", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CD | None = None
    text: ED | None = None


class ExternalProcedure(CDAModel):
    """Reference to an external procedure."""

    class_code: str | None = Field(default="PROC", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CD | None = None
    text: ED | None = None
