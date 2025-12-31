"""C-CDA Performer and AssignedEntity models.

Performers represent who performed a clinical action.
They appear at service event level and entry level.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/
"""

from __future__ import annotations

from pydantic import Field

from .datatypes import AD, CE, II, IVL_TS, ON, PN, TEL, CDAModel


class AssignedPerson(CDAModel):
    """Person assigned as performer.

    Contains the name of the person who performed the action.
    """

    name: list[PN] | None = None


class RepresentedOrganization(CDAModel):
    """Organization represented by the performer."""

    id: list[II] | None = None
    name: list[ON | str] | None = None
    telecom: list[TEL] | None = None
    addr: list[AD] | None = None
    standard_industry_class_code: CE | None = Field(default=None, alias="standardIndustryClassCode")


class AssignedEntity(CDAModel):
    """Assigned entity containing practitioner details.

    Contains identifiers, specialty, contact information,
    and optionally an assigned person.
    """

    # Class code (default: ASSIGNED)
    class_code: str | None = Field(default="ASSIGNED", alias="classCode")

    # Identifiers (NPI, organizational IDs)
    id: list[II] | None = None

    # Provider specialty/type (e.g., NUCC Healthcare Provider Taxonomy)
    code: CE | None = None

    # Contact information
    addr: list[AD] | None = None
    telecom: list[TEL] | None = None

    # The person
    assigned_person: AssignedPerson | None = Field(default=None, alias="assignedPerson")

    # Represented organization
    represented_organization: RepresentedOrganization | None = Field(
        default=None, alias="representedOrganization"
    )

    # SDTC specialty extension (additional specialties)
    sdtc_specialty: list[CE] | None = Field(default=None, alias="sdtc:specialty")


class Performer(CDAModel):
    """Performer participation.

    Represents who performed a clinical action.
    Can appear at service event level or entry level.

    Type codes:
    - PRF: Performer (general)
    - SPRF: Secondary Performer
    - PPRF: Primary Performer
    """

    # Type code
    type_code: str | None = Field(default="PRF", alias="typeCode")

    # Template ID (if applicable)
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Function code (role of the performer, e.g., PCP, ADMPHYS)
    function_code: CE | None = Field(default=None, alias="functionCode")

    # Time period of involvement
    time: IVL_TS | None = None

    # Mode code (how they participated)
    mode_code: CE | None = Field(default=None, alias="modeCode")

    # The assigned entity details
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")
