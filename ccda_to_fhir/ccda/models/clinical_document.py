"""C-CDA Clinical Document model.

The ClinicalDocument is the root element of a C-CDA document.
It contains the header information and body content.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-USRealmHeader.html
"""

from __future__ import annotations

from pydantic import Field, model_validator

from .author import Author
from .datatypes import AD, CE, CS, ED, II, IVL_TS, ON, PN, SXCM_TS, TEL, TS, CDAModel
from .participant import AssociatedEntity
from .performer import AssignedEntity
from .record_target import Organization, RecordTarget
from .section import Component


class InformationRecipient(CDAModel):
    """Intended recipient of the document."""

    type_code: str | None = Field(default="PRCP", alias="typeCode")
    intended_recipient: IntendedRecipient | None = Field(default=None, alias="intendedRecipient")


class IntendedRecipient(CDAModel):
    """Details about an intended recipient."""

    class_code: str | None = Field(default="ASSIGNED", alias="classCode")
    id: list[II] | None = None
    information_recipient: InformationRecipientPerson | None = Field(
        default=None, alias="informationRecipient"
    )
    received_organization: Organization | None = Field(default=None, alias="receivedOrganization")


class InformationRecipientPerson(CDAModel):
    """Person who is an information recipient."""

    name: list[PN] | None = None


class LegalAuthenticator(CDAModel):
    """Legal authenticator of the document."""

    time: TS | None = None
    signature_code: CS | None = Field(default=None, alias="signatureCode")
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class Authenticator(CDAModel):
    """Authenticator of the document."""

    time: TS | None = None
    signature_code: CS | None = Field(default=None, alias="signatureCode")
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class Custodian(CDAModel):
    """Organization responsible for maintaining the document."""

    type_code: str | None = Field(default="CST", alias="typeCode")
    assigned_custodian: AssignedCustodian | None = Field(default=None, alias="assignedCustodian")


class AssignedCustodian(CDAModel):
    """Assigned custodian details."""

    class_code: str | None = Field(default="ASSIGNED", alias="classCode")
    represented_custodian_organization: CustodianOrganization | None = Field(
        default=None, alias="representedCustodianOrganization"
    )


class CustodianOrganization(CDAModel):
    """Custodian organization details."""

    class_code: str | None = Field(default="ORG", alias="classCode")
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")
    id: list[II] | None = None
    name: ON | str | None = None
    telecom: TEL | None = None
    addr: AD | None = None


class DataEnterer(CDAModel):
    """Person who entered the data into the system."""

    type_code: str | None = Field(default="ENT", alias="typeCode")
    time: TS | None = None
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class RelatedPerson(CDAModel):
    """Person related to the patient who is an informant."""

    name: list[PN] | None = None


class RelatedEntity(CDAModel):
    """Related entity for informant (non-provider).

    Used when the informant is not a healthcare provider but a related
    person such as a family member, caregiver, or the patient themselves.
    """

    # Class code (e.g., PRS for personal relationship, NOK for next of kin)
    class_code: str | None = Field(default=None, alias="classCode")

    # Relationship code to the patient
    code: CE | None = None

    # Contact information
    addr: list[AD] | None = None
    telecom: list[TEL] | None = None

    # Effective time of the relationship
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # The related person
    related_person: RelatedPerson | None = Field(default=None, alias="relatedPerson")


class Informant(CDAModel):
    """Source of information in the document.

    Can be either a healthcare provider (assignedEntity) or a related
    person such as a family member (relatedEntity).
    """

    type_code: str | None = Field(default="INF", alias="typeCode")
    context_control_code: str | None = Field(default="OP", alias="contextControlCode")
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")
    related_entity: RelatedEntity | None = Field(default=None, alias="relatedEntity")


class DocumentationOf(CDAModel):
    """Documentation of a service event."""

    type_code: str | None = Field(default="DOC", alias="typeCode")
    service_event: ServiceEvent | None = Field(default=None, alias="serviceEvent")


class ServiceEventPerformer(CDAModel):
    """Performer within a service event.

    Represents a healthcare provider who participated in the service event.
    Uses different type codes than entry-level performers.

    Type codes:
    - PRF: Performer
    - PPRF: Primary Performer
    - SPRF: Secondary Performer
    """

    type_code: str | None = Field(default="PRF", alias="typeCode")
    function_code: CE | None = Field(default=None, alias="functionCode")
    time: IVL_TS | None = None
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class ServiceEvent(CDAModel):
    """Service event being documented."""

    class_code: str | None = Field(default="PCPR", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CE | None = None
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")
    performer: list[ServiceEventPerformer] | None = None


class ComponentOf(CDAModel):
    """Parent encounter of this document."""

    type_code: str | None = Field(default="COMP", alias="typeCode")
    encompassing_encounter: EncompassingEncounter | None = Field(
        default=None, alias="encompassingEncounter"
    )


class ResponsibleParty(CDAModel):
    """Responsible party for the encompassing encounter."""

    type_code: str | None = Field(default="RESP", alias="typeCode")
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class EncounterParticipant(CDAModel):
    """Participant in the encompassing encounter.

    Type codes:
    - ADM: Admitter
    - ATND: Attender
    - CON: Consultant
    - DIS: Discharger
    - REF: Referrer
    """

    type_code: str | None = Field(default=None, alias="typeCode")
    time: IVL_TS | None = None
    assigned_entity: AssignedEntity | None = Field(default=None, alias="assignedEntity")


class HealthCareFacility(CDAModel):
    """Healthcare facility where the encounter took place."""

    class_code: str | None = Field(default="SDLOC", alias="classCode")
    id: list[II] | None = None
    code: CE | None = None
    location: Place | None = None
    service_provider_organization: Organization | None = Field(
        default=None, alias="serviceProviderOrganization"
    )


class Place(CDAModel):
    """Physical place for the healthcare facility."""

    class_code: str | None = Field(default="PLC", alias="classCode")
    determiner_code: str | None = Field(default="INSTANCE", alias="determinerCode")
    name: str | None = None
    addr: AD | None = None


class Location(CDAModel):
    """Location of the encompassing encounter."""

    type_code: str | None = Field(default="LOC", alias="typeCode")
    health_care_facility: HealthCareFacility | None = Field(
        default=None, alias="healthCareFacility"
    )


class EncompassingEncounter(CDAModel):
    """The encounter that encompasses this document."""

    class_code: str | None = Field(default="ENC", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CE | None = None
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")
    discharge_disposition_code: CE | None = Field(default=None, alias="dischargeDispositionCode")
    responsible_party: ResponsibleParty | None = Field(default=None, alias="responsibleParty")
    encounter_participant: list[EncounterParticipant] | None = Field(
        default=None, alias="encounterParticipant"
    )
    location: Location | None = None


class RelatedDocument(CDAModel):
    """Relationship to another document."""

    type_code: str | None = Field(default=None, alias="typeCode")  # RPLC, XFRM, APND
    parent_document: ParentDocument | None = Field(default=None, alias="parentDocument")


class ParentDocument(CDAModel):
    """Parent document reference."""

    class_code: str | None = Field(default="DOCCLIN", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CE | None = None
    text: ED | None = None
    set_id: II | None = Field(default=None, alias="setId")
    version_number: int | None = Field(default=None, alias="versionNumber")


class Authorization(CDAModel):
    """Authorization for the document."""

    type_code: str | None = Field(default="AUTH", alias="typeCode")
    consent: Consent | None = None


class Order(CDAModel):
    """Order being fulfilled by the document."""

    class_code: str | None = Field(default="ACT", alias="classCode")
    mood_code: str | None = Field(default="RQO", alias="moodCode")
    id: list[II] | None = None
    code: CE | None = None
    priority_code: CE | None = Field(default=None, alias="priorityCode")


class InFulfillmentOf(CDAModel):
    """Reference to orders that this document fulfills."""

    type_code: str | None = Field(default="FLFS", alias="typeCode")
    order: Order | None = None


class DocumentParticipant(CDAModel):
    """Participant at the document level.

    Used for support persons, insurance providers, and other participants.

    Type codes:
    - IND: Indirect participant
    - HLD: Holder (insurance)
    - NOT: Urgent notification contact
    - CALLBCK: Callback contact
    """

    type_code: str | None = Field(default=None, alias="typeCode")
    context_control_code: str | None = Field(default="OP", alias="contextControlCode")
    function_code: CE | None = Field(default=None, alias="functionCode")
    time: IVL_TS | None = None
    associated_entity: AssociatedEntity | None = Field(default=None, alias="associatedEntity")


class Consent(CDAModel):
    """Patient consent."""

    class_code: str | None = Field(default="CONS", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")
    id: list[II] | None = None
    code: CE | None = None
    status_code: CS | None = Field(default=None, alias="statusCode")


class ClinicalDocument(CDAModel):
    """Clinical Document Architecture (CDA) root element.

    The ClinicalDocument represents a complete C-CDA document including
    the header (metadata) and body (clinical content).

    US Realm Header Template ID: 2.16.840.1.113883.10.20.22.1.1
    """

    # Class code (fixed: DOCCLIN)
    class_code: str | None = Field(default="DOCCLIN", alias="classCode")

    # Mood code (fixed: EVN)
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Realm code (US)
    realm_code: list[CS] | None = Field(default=None, alias="realmCode")

    # Type ID (CDA R2)
    type_id: II | None = Field(default=None, alias="typeId")

    # Template IDs (document type, e.g., CCD, Discharge Summary)
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Document ID (unique identifier for this document)
    id: II | None = None

    # Document type code (LOINC)
    code: CE | None = None

    # Document title
    title: str | None = None

    # Document creation time
    # CDA spec says TS, but real-world documents (EchoMan EHR) use SXCM_TS
    effective_time: TS | SXCM_TS | None = Field(default=None, alias="effectiveTime")

    # Confidentiality code
    confidentiality_code: CE | None = Field(default=None, alias="confidentialityCode")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Set ID (for document versioning)
    set_id: II | None = Field(default=None, alias="setId")

    # Version number
    version_number: int | None = Field(default=None, alias="versionNumber")

    # Copy time
    copy_time: TS | None = Field(default=None, alias="copyTime")

    # Record targets (patients)
    record_target: list[RecordTarget] | None = Field(default=None, alias="recordTarget")

    # Authors
    author: list[Author] | None = None

    # Data enterer
    data_enterer: DataEnterer | None = Field(default=None, alias="dataEnterer")

    # Informants
    informant: list[Informant] | None = None

    # Custodian (required)
    custodian: Custodian | None = None

    # Information recipients
    information_recipient: list[InformationRecipient] | None = Field(
        default=None, alias="informationRecipient"
    )

    # Legal authenticator
    legal_authenticator: LegalAuthenticator | None = Field(default=None, alias="legalAuthenticator")

    # Authenticators
    authenticator: list[Authenticator] | None = None

    # Participant (support persons, etc.)
    participant: list[DocumentParticipant] | None = None

    # In fulfillment of (orders)
    in_fulfillment_of: list[InFulfillmentOf] | None = Field(default=None, alias="inFulfillmentOf")

    # Documentation of (service events)
    documentation_of: list[DocumentationOf] | None = Field(default=None, alias="documentationOf")

    # Related documents
    related_document: list[RelatedDocument] | None = Field(default=None, alias="relatedDocument")

    # Authorization
    authorization: list[Authorization] | None = None

    # Component of (encompassing encounter)
    component_of: ComponentOf | None = Field(default=None, alias="componentOf")

    # Document body (structured or non-XML)
    component: Component | None = None

    @model_validator(mode='after')
    def validate_us_realm_header(self) -> ClinicalDocument:
        """Validate US Realm Header (2.16.840.1.113883.10.20.22.1.1).

        Reference: docs/ccda/clinical-document.md

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain exactly one [1..1] realmCode with code="US"
        2. SHALL contain exactly one [1..1] typeId
           - root SHALL be "2.16.840.1.113883.1.3"
           - extension SHALL be "POCD_HD000040"
        3. SHALL contain at least one [1..*] templateId
        4. SHALL contain exactly one [1..1] id
        5. SHALL contain exactly one [1..1] code
        6. SHALL contain exactly one [1..1] effectiveTime
        7. SHALL contain exactly one [1..1] confidentialityCode
        8. SHALL contain at least one [1..*] recordTarget
        9. SHALL contain at least one [1..*] author
        10. SHALL contain exactly one [1..1] custodian

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        # Only validate if this document claims to be a US Realm document
        # Check for US Realm Header template ID
        has_us_realm = False
        if self.template_id:
            for tid in self.template_id:
                if tid.root == "2.16.840.1.113883.10.20.22.1.1":
                    has_us_realm = True
                    break

        if not has_us_realm:
            return self

        # 1. SHALL contain exactly one realmCode with code="US"
        if not self.realm_code or len(self.realm_code) == 0:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] realmCode"
            )
        if len(self.realm_code) > 1:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                f"SHALL contain exactly one [1..1] realmCode, found {len(self.realm_code)}"
            )
        if self.realm_code[0].code != "US":
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                f"realmCode SHALL be 'US', found '{self.realm_code[0].code}'"
            )

        # 2. SHALL contain exactly one typeId
        if not self.type_id:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] typeId"
            )

        # 2a. typeId root SHALL be "2.16.840.1.113883.1.3"
        if self.type_id.root != "2.16.840.1.113883.1.3":
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                f"typeId root SHALL be '2.16.840.1.113883.1.3', found '{self.type_id.root}'"
            )

        # 2b. typeId extension SHALL be "POCD_HD000040"
        if self.type_id.extension != "POCD_HD000040":
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                f"typeId extension SHALL be 'POCD_HD000040', found '{self.type_id.extension}'"
            )

        # 3. SHALL contain at least one templateId
        if not self.template_id or len(self.template_id) == 0:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain at least one [1..*] templateId"
            )

        # 4. SHALL contain exactly one id
        if not self.id:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] id"
            )

        # 5. SHALL contain exactly one code
        if not self.code:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] code"
            )

        # 6. SHALL contain exactly one effectiveTime
        if not self.effective_time:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        # 7. SHALL contain exactly one confidentialityCode
        if not self.confidentiality_code:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] confidentialityCode"
            )

        # 8. SHALL contain at least one recordTarget
        if not self.record_target or len(self.record_target) == 0:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain at least one [1..*] recordTarget"
            )

        # 9. SHALL contain at least one author
        if not self.author or len(self.author) == 0:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain at least one [1..*] author"
            )

        # 10. SHALL contain exactly one custodian
        if not self.custodian:
            raise ValueError(
                "US Realm Header (2.16.840.1.113883.10.20.22.1.1): "
                "SHALL contain exactly one [1..1] custodian"
            )

        return self


# Rebuild models with forward references
HealthCareFacility.model_rebuild()
Custodian.model_rebuild()
AssignedCustodian.model_rebuild()
CustodianOrganization.model_rebuild()
