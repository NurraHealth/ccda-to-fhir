"""C-CDA EntryRelationship model.

EntryRelationship links clinical statements together (observations, acts, procedures, etc.).
This module is separate to avoid circular imports - it references all clinical statement
types via forward references that are resolved by model_rebuild() in __init__.py.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .datatypes import CDAModel

if TYPE_CHECKING:
    from .act import Act
    from .encounter import Encounter
    from .observation import Observation
    from .organizer import Organizer
    from .procedure import Procedure
    from .substance_administration import SubstanceAdministration
    from .supply import Supply


class EntryRelationship(CDAModel):
    """Relationship between clinical entries.

    Links observations to related observations, acts, or other entries.
    Common type codes:
    - SUBJ: Subject of (e.g., problem observation subject of concern act)
    - MFST: Manifestation of (e.g., reaction manifestation of allergy)
    - REFR: Refers to (e.g., status observation)
    - COMP: Component of (e.g., vital sign component of organizer)
    - RSON: Reason for (e.g., reason for procedure)
    - CAUS: Cause of
    """

    type_code: str | None = Field(default=None, alias="typeCode")
    inversion_ind: bool | None = Field(default=None, alias="inversionInd")
    context_conduction_ind: bool | None = Field(default=None, alias="contextConductionInd")
    negation_ind: bool | None = Field(default=None, alias="negationInd")
    sequence_number: int | None = Field(default=None, alias="sequenceNumber")

    # The related clinical statement (one of these will be present)
    # These are forward references resolved by model_rebuild() in __init__.py
    observation: Observation | None = None
    act: Act | None = None
    procedure: Procedure | None = None
    substance_administration: SubstanceAdministration | None = Field(
        default=None, alias="substanceAdministration"
    )
    supply: Supply | None = None
    encounter: Encounter | None = None
    organizer: Organizer | None = None
