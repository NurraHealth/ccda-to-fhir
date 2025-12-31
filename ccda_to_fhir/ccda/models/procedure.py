"""C-CDA Procedure models.

Procedures represent clinical actions performed on or for the patient.
Can be represented as procedure, act, or observation depending on the type.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ProcedureActivityProcedure.html
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


class SpecimenPlayingEntity(CDAModel):
    """Playing entity for a specimen."""

    class_code: str | None = Field(default="ENT", alias="classCode")
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")
    code: CE | None = None
    name: str | None = None


class SpecimenRole(CDAModel):
    """Role for a specimen collected during a procedure."""

    class_code: str | None = Field(default="SPEC", alias="classCode")
    id: list[II] | None = None
    specimen_playing_entity: SpecimenPlayingEntity | None = Field(
        default=None, alias="specimenPlayingEntity"
    )


class Specimen(CDAModel):
    """Specimen collected during a procedure."""

    type_code: str | None = Field(default="SPC", alias="typeCode")
    specimen_role: SpecimenRole | None = Field(default=None, alias="specimenRole")


class Procedure(CDAModel):
    """Procedure Activity Procedure.

    Represents procedures whose immediate and primary outcome is the
    alteration of the physical condition of the patient.
    Examples: appendectomy, hip replacement, gastrostomy creation.

    Template ID: 2.16.840.1.113883.10.20.22.4.14
    """

    # Fixed structural attributes
    class_code: str | None = Field(default="PROC", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Negation indicator (true = procedure was NOT performed)
    negation_ind: bool | None = Field(default=None, alias="negationInd")

    # Template IDs
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Procedure code (SNOMED, CPT, ICD-10-PCS, etc.)
    code: CD | None = None

    # Narrative text reference
    text: ED | None = None

    # Status code (completed, active, aborted, cancelled)
    status_code: CS | None = Field(default=None, alias="statusCode")

    # When the procedure was performed
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Priority (routine, urgent, emergency, etc.)
    priority_code: CE | None = Field(default=None, alias="priorityCode")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Method used (laparoscopic, open, etc.)
    method_code: list[CE] | None = Field(default=None, alias="methodCode")

    # Approach site (how the target was accessed)
    approach_site_code: list[CE] | None = Field(default=None, alias="approachSiteCode")

    # Target site (body site where procedure was performed)
    # Per CDA spec, targetSiteCode uses CD (Concept Descriptor) datatype
    target_site_code: list[CD] | None = Field(default=None, alias="targetSiteCode")

    # Specimens collected
    specimen: list[Specimen] | None = None

    # Performers
    performer: list[Performer] | None = None

    # Authors
    author: list[Author] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Participants (location, device)
    participant: list[Participant] | None = None

    # Entry relationships (indication, instruction, medication, reaction)
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )

    # References
    reference: list[Reference] | None = None

    # Preconditions
    precondition: list[Precondition] | None = None

    # SDTC extension for category
    sdtc_category: list[CE] | None = Field(default=None, alias="sdtc:category")

    def _has_template(self, template_id: str, extension: str | None = None) -> bool:
        """Check if this procedure has a specific template ID.

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
    def validate_procedure_activity(self) -> Procedure:
        """Validate Procedure Activity Procedure template (2.16.840.1.113883.10.20.22.4.14).

        Reference: docs/ccda/activity-procedure.md

        Conformance requirements from C-CDA R2.1/R5.0:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        # Only validate if this is a Procedure Activity Procedure
        if not self._has_template("2.16.840.1.113883.10.20.22.4.14"):
            return self

        # 1. SHALL contain at least one id
        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14): "
                "SHALL contain at least one [1..*] id"
            )

        # 2. SHALL contain exactly one code
        if not self.code:
            raise ValueError(
                "Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14): "
                "SHALL contain exactly one [1..1] code"
            )

        # 3. SHALL contain exactly one statusCode
        if not self.status_code:
            raise ValueError(
                "Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        return self
