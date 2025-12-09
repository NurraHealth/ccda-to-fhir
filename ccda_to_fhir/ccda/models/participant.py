"""C-CDA Participant models.

Participants represent entities involved in clinical activities.
Used for allergens (CSM), related persons, devices, and other participants.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/
"""

from __future__ import annotations

from pydantic import Field

from .datatypes import AD, CE, II, IVL_TS, ON, PN, TEL, CDAModel


class PlayingEntity(CDAModel):
    """Entity playing a role in the participation.

    Used for substances (allergens), materials, devices, etc.
    """

    # Class code (e.g., MMAT for manufactured material, ENT for entity)
    class_code: str | None = Field(default=None, alias="classCode")

    # Determiner code
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")

    # Entity code (e.g., RxNorm code for allergen)
    code: CE | None = None

    # Entity name
    name: list[ON | str] | None = None

    # Description
    desc: str | None = None

    # Quantity
    quantity: str | None = None


class PlayingDevice(CDAModel):
    """Device playing a role in the participation."""

    # Class code (DEV)
    class_code: str | None = Field(default="DEV", alias="classCode")

    # Determiner code
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")

    # Device code
    code: CE | None = None

    # Manufacturer model name
    manufacturer_model_name: str | None = Field(default=None, alias="manufacturerModelName")

    # Software name
    software_name: str | None = Field(default=None, alias="softwareName")


class ScopingEntity(CDAModel):
    """Entity that scopes a participant role."""

    # Class code
    class_code: str | None = Field(default="ENT", alias="classCode")

    # Determiner code
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")

    # Identifiers
    id: list[II] | None = None

    # Entity code
    code: CE | None = None

    # Description
    desc: str | None = None


class ParticipantRole(CDAModel):
    """Role of the participant.

    Contains the playing entity (e.g., substance, device) or
    scoping entity information.
    """

    # Class code (e.g., MANU for manufactured product)
    class_code: str | None = Field(default=None, alias="classCode")

    # Template ID
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Identifiers
    id: list[II] | None = None

    # Role code
    code: CE | None = None

    # Address
    addr: list[AD] | None = None

    # Telecom
    telecom: list[TEL] | None = None

    # The playing entity (substance, material)
    playing_entity: PlayingEntity | None = Field(default=None, alias="playingEntity")

    # The playing device
    playing_device: PlayingDevice | None = Field(default=None, alias="playingDevice")

    # The scoping entity
    scoping_entity: ScopingEntity | None = Field(default=None, alias="scopingEntity")


class AssociatedEntity(CDAModel):
    """Associated entity for participant.

    Used for related persons, organizations, etc.
    """

    # Class code (e.g., NOK for next of kin, CAREGIVER, PRS for personal relationship)
    class_code: str | None = Field(default=None, alias="classCode")

    # Identifiers
    id: list[II] | None = None

    # Relationship or role code
    code: CE | None = None

    # Address
    addr: list[AD] | None = None

    # Telecom
    telecom: list[TEL] | None = None

    # Associated person
    associated_person: AssociatedPerson | None = Field(default=None, alias="associatedPerson")

    # Scoping organization
    scoping_organization: ScopingOrganization | None = Field(
        default=None, alias="scopingOrganization"
    )


class AssociatedPerson(CDAModel):
    """Person associated with the participant."""

    name: list[PN] | None = None


class ScopingOrganization(CDAModel):
    """Organization that scopes an associated entity."""

    id: list[II] | None = None
    name: list[ON | str] | None = None
    telecom: list[TEL] | None = None
    addr: list[AD] | None = None


class Participant(CDAModel):
    """Participant in a clinical activity.

    Type codes:
    - CSM: Consumable (e.g., allergen substance)
    - DEV: Device
    - LOC: Location
    - PRD: Product
    - SBJ: Subject
    - IND: Indirect participant
    - VRF: Verifier
    - AUTHEN: Authenticator
    - LA: Legal authenticator
    """

    # Type code (CSM for consumable/allergen, DEV for device, etc.)
    type_code: str | None = Field(default=None, alias="typeCode")

    # Context control code
    context_control_code: str | None = Field(default=None, alias="contextControlCode")

    # Template ID
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Time of participation
    time: IVL_TS | None = None

    # Awareness code
    awareness_code: CE | None = Field(default=None, alias="awarenessCode")

    # The participant role (for consumables, devices)
    participant_role: ParticipantRole | None = Field(default=None, alias="participantRole")

    # The associated entity (for related persons)
    associated_entity: AssociatedEntity | None = Field(default=None, alias="associatedEntity")


# Rebuild models with forward references
AssociatedEntity.model_rebuild()
