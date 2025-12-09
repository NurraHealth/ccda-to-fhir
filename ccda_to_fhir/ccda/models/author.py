"""C-CDA Author and AssignedAuthor models.

Authors represent who documented or created clinical information.
They appear at both document level and entry level.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-AuthorParticipation.html
Template ID: 2.16.840.1.113883.10.20.22.4.119
"""

from __future__ import annotations

from pydantic import Field

from .datatypes import AD, CE, II, ON, PN, TEL, TS, CDAModel


class AssignedPerson(CDAModel):
    """Person assigned as author.

    Contains the name of the person who authored the content.
    """

    name: list[PN] | None = None


class AssignedAuthoringDevice(CDAModel):
    """Device that authored content.

    Used when content is authored by a device rather than a person.
    """

    manufacturer_model_name: str | None = Field(default=None, alias="manufacturerModelName")
    software_name: str | None = Field(default=None, alias="softwareName")
    as_maintained_entity: MaintainedEntity | None = Field(default=None, alias="asMaintainedEntity")


class MaintainedEntity(CDAModel):
    """Entity that maintains the authoring device."""

    maintaining_person: AssignedPerson | None = Field(default=None, alias="maintainingPerson")


class RepresentedOrganization(CDAModel):
    """Organization represented by the author.

    The organization that the author is acting on behalf of.
    """

    id: list[II] | None = None
    name: list[ON | str] | None = None
    telecom: list[TEL] | None = None
    addr: list[AD] | None = None
    standard_industry_class_code: CE | None = Field(default=None, alias="standardIndustryClassCode")


class AssignedAuthor(CDAModel):
    """Assigned author containing practitioner details.

    Contains identifiers, specialty, contact information,
    and either an assigned person or authoring device.
    """

    # Identifiers (NPI, organizational IDs)
    id: list[II] | None = None

    # Provider specialty/type (e.g., NUCC Healthcare Provider Taxonomy)
    code: CE | None = None

    # Contact information
    addr: list[AD] | None = None
    telecom: list[TEL] | None = None

    # Either person or device (one must be present)
    assigned_person: AssignedPerson | None = Field(default=None, alias="assignedPerson")
    assigned_authoring_device: AssignedAuthoringDevice | None = Field(
        default=None, alias="assignedAuthoringDevice"
    )

    # Represented organization
    represented_organization: RepresentedOrganization | None = Field(
        default=None, alias="representedOrganization"
    )


class Author(CDAModel):
    """Author participation.

    Represents who authored/documented clinical information.
    Can appear at document level or entry level.

    Template ID: 2.16.840.1.113883.10.20.22.4.119
    """

    # Template ID for Author Participation
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Time of authorship
    time: TS | None = None

    # The assigned author details
    assigned_author: AssignedAuthor | None = Field(default=None, alias="assignedAuthor")

    # Type code (default: AUT)
    type_code: str | None = Field(default=None, alias="typeCode")

    # Function code (role of the author)
    function_code: CE | None = Field(default=None, alias="functionCode")

    # Context control code
    context_control_code: str | None = Field(default=None, alias="contextControlCode")


# Rebuild model to resolve forward reference
AssignedAuthoringDevice.model_rebuild()
