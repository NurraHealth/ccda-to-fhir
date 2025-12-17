"""C-CDA Section, StructuredBody, and Component models.

Sections organize clinical content within a CDA document.
Each section contains narrative text and optionally clinical entries.

Reference: https://build.fhir.org/ig/HL7/CDA-core-sd/StructureDefinition-Section.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field

from .author import Author
from .datatypes import AD, CE, CS, ED, II, PN, TEL, TS, CDAModel
from .performer import AssignedEntity
from .struc_doc import StrucDocText

if TYPE_CHECKING:
    from .act import Act
    from .clinical_document import RelatedEntity
    from .encounter import Encounter
    from .observation import Observation
    from .organizer import Organizer
    from .procedure import Procedure
    from .substance_administration import SubstanceAdministration
    from .supply import Supply


class SubjectPerson(CDAModel):
    """Person who is the subject.

    Contains demographic information about the related subject.
    """

    # Name
    name: list[PN] | None = None

    # Administrative gender code
    administrative_gender_code: CE | None = Field(default=None, alias="administrativeGenderCode")

    # Birth time
    birth_time: TS | None = Field(default=None, alias="birthTime")

    # SDTC extensions for deceased information
    sdtc_deceased_ind: bool | None = Field(default=None, alias="sdtc:deceasedInd")
    sdtc_deceased_time: TS | None = Field(default=None, alias="sdtc:deceasedTime")


class RelatedSubject(CDAModel):
    """Related subject (e.g., family member in family history section).

    Used in sections like Family History to document information about
    a person related to the patient.
    """

    # Class code (typically PRS for person)
    class_code: str | None = Field(default="PRS", alias="classCode")

    # Relationship code (e.g., FTH=father, MTH=mother, SIB=sibling)
    code: CE | None = None

    # Address (optional)
    addr: list[AD] | None = None

    # Telecom (optional)
    telecom: list[TEL] | None = None

    # The subject person
    subject: SubjectPerson | None = None


class Subject(CDAModel):
    """Subject of the section.

    Allows a section to specify its own subject, overriding the
    document-level subject. Most commonly used in Family History sections.
    """

    # Type code (default: SBJ for subject)
    type_code: str | None = Field(default="SBJ", alias="typeCode")

    # Context control code
    context_control_code: str | None = Field(default="OP", alias="contextControlCode")

    # Awareness code
    awareness_code: CE | None = Field(default=None, alias="awarenessCode")

    # Related subject
    related_subject: RelatedSubject | None = Field(default=None, alias="relatedSubject")


class Informant(CDAModel):
    """Source of information for this section.

    Identifies who provided the information in this specific section.
    Can be either a healthcare provider (assignedEntity) or a related
    person (relatedEntity).
    """

    # Type code (default: INF for informant)
    type_code: str | None = Field(default="INF", alias="typeCode")

    # Context control code
    context_control_code: str | None = Field(default="OP", alias="contextControlCode")

    # Either assigned entity or related entity
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")
    related_entity: RelatedEntity | None = Field(default=None, alias="relatedEntity")


class Entry(CDAModel):
    """Entry containing a clinical statement.

    Entries are the structured clinical data within a section.
    Each entry contains one clinical statement (act, observation,
    procedure, etc.).
    """

    # Type code (default: DRIV for driven, COMP for component)
    type_code: str | None = Field(default=None, alias="typeCode")

    # Context conduction indicator
    context_conduction_ind: bool | None = Field(default=None, alias="contextConductionInd")

    # Clinical statement - one of these will be present
    act: Act | None = None
    observation: Observation | None = None
    procedure: Procedure | None = None
    substance_administration: SubstanceAdministration | None = Field(
        default=None, alias="substanceAdministration"
    )
    encounter: Encounter | None = None
    organizer: Organizer | None = None
    supply: Supply | None = None


class Section(CDAModel):
    """Document section containing narrative and clinical entries.

    Sections organize clinical content and can nest within each other.
    Each section typically has:
    - A template ID identifying the section type
    - A LOINC code identifying the section content
    - Human-readable narrative text
    - Structured clinical entries
    """

    # Fixed values
    class_code: str | None = Field(default="DOCSECT", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # XML ID for linking
    id_attr: str | None = Field(default=None, alias="ID")

    # Template IDs identifying the section type
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Section identifier
    id: II | None = None

    # Section code (typically LOINC)
    code: CE | None = None

    # Section title (human-readable heading)
    title: str | None = None

    # Narrative text (StrucDocText narrative content)
    # Note: This is StrucDocText, not ED. ED is for binary content in nonXMLBody.
    # StrucDocText is the structured narrative type for section bodies.
    text: StrucDocText | None = None

    # Confidentiality code
    confidentiality_code: CE | None = Field(default=None, alias="confidentialityCode")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Section authors (override document-level authors)
    author: list[Author] | None = None

    # Section informants (source of information for this section)
    informant: list[Informant] | None = None

    # Section subject (override document-level subject)
    subject: Subject | None = None

    # Clinical entries
    entry: list[Entry] | None = None

    # Nested subsections
    component: list[SectionComponent] | None = None

    # Null flavor
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class SectionComponent(CDAModel):
    """Component containing a nested section."""

    type_code: str | None = Field(default="COMP", alias="typeCode")
    context_conduction_ind: bool | None = Field(default=True, alias="contextConductionInd")
    section: Section | None = None


class StructuredBody(CDAModel):
    """Structured body containing document sections.

    The structuredBody is the main content container for C-CDA documents,
    containing one or more section components.
    """

    class_code: str | None = Field(default="DOCBODY", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Confidentiality code
    confidentiality_code: CE | None = Field(default=None, alias="confidentialityCode")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Section components
    component: list[SectionComponent] | None = None


class NonXMLBody(CDAModel):
    """Non-XML body for unstructured content.

    Used when the document body is not structured XML (e.g., PDF, images).
    """

    class_code: str | None = Field(default="DOCBODY", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # The embedded content
    text: ED | None = None


class Component(CDAModel):
    """Document body component.

    Contains either a structured body (with sections) or
    a non-XML body (unstructured content).
    """

    type_code: str | None = Field(default="COMP", alias="typeCode")
    context_conduction_ind: bool | None = Field(default=True, alias="contextConductionInd")

    # Either structured or non-XML body
    structured_body: StructuredBody | None = Field(default=None, alias="structuredBody")
    non_xml_body: NonXMLBody | None = Field(default=None, alias="nonXMLBody")
