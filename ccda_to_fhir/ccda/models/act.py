"""C-CDA Act models.

Acts represent clinical actions, concerns, and events.
Used for Problem Concern Act, Allergy Concern Act, and other acts.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ProblemConcernAct.html
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AllergyConcernAct.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, model_validator

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

    def _has_template(self, template_id: str, extension: str | None = None) -> bool:
        """Check if this act has a specific template ID.

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
    def validate_problem_concern_act(self) -> 'Act':
        """Validate Problem Concern Act (2.16.840.1.113883.10.20.22.4.3).

        Reference: docs/ccda/concern-act-problem.md

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code with code="CONC"
        3. SHALL contain exactly one [1..1] statusCode
        4. SHALL contain exactly one [1..1] effectiveTime
           - SHALL contain low
           - SHALL contain high if statusCode is "completed" or "aborted"
        5. SHALL contain at least one [1..*] entryRelationship

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.3"):
            return self

        # 1. SHALL contain at least one id
        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "SHALL contain at least one [1..*] id"
            )

        # 2. SHALL contain exactly one code with code="CONC"
        if not self.code:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "SHALL contain exactly one [1..1] code"
            )
        if self.code.code != "CONC":
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                f"code SHALL be 'CONC', found '{self.code.code}'"
            )

        # 3. SHALL contain exactly one statusCode
        if not self.status_code:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        # 4. SHALL contain exactly one effectiveTime
        if not self.effective_time:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        # 4a. effectiveTime SHALL contain low
        if not self.effective_time.low:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "effectiveTime SHALL contain low element"
            )

        # 4b. effectiveTime SHALL contain high if statusCode is completed/aborted
        if self.status_code.code in ["completed", "aborted"]:
            if not self.effective_time.high:
                raise ValueError(
                    "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                    "effectiveTime SHALL contain high when statusCode is 'completed' or 'aborted'"
                )

        # 5. SHALL contain at least one entryRelationship
        if not self.entry_relationship or len(self.entry_relationship) == 0:
            raise ValueError(
                "Problem Concern Act (2.16.840.1.113883.10.20.22.4.3): "
                "SHALL contain at least one [1..*] entryRelationship"
            )

        return self

    @model_validator(mode='after')
    def validate_allergy_concern_act(self) -> 'Act':
        """Validate Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30).

        Same requirements as Problem Concern Act.

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.30"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "SHALL contain exactly one [1..1] code"
            )
        if self.code.code != "CONC":
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                f"code SHALL be 'CONC', found '{self.code.code}'"
            )

        if not self.status_code:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        if not self.effective_time:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.effective_time.low:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "effectiveTime SHALL contain low"
            )

        if self.status_code.code in ["completed", "aborted"]:
            if not self.effective_time.high:
                raise ValueError(
                    "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                    "effectiveTime SHALL contain high when statusCode is 'completed' or 'aborted'"
                )

        if not self.entry_relationship or len(self.entry_relationship) == 0:
            raise ValueError(
                "Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30): "
                "SHALL contain at least one [1..*] entryRelationship"
            )

        return self


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
