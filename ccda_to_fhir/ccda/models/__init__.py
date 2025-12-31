"""C-CDA Pydantic models.

This package contains Pydantic models representing C-CDA/HL7 V3 structures.
Models are organized idiomatically matching C-CDA's RIM-based structure.
"""

from __future__ import annotations

from .act import (
    Act,
    ExternalAct,
    ExternalDocument,
    ExternalObservation,
    ExternalProcedure,
    Reference,
)

# Author
from .author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
    MaintainedEntity,
    RepresentedOrganization,
)

# Clinical document (root element)
from .clinical_document import (
    AssignedCustodian,
    Authenticator,
    Authorization,
    ClinicalDocument,
    ComponentOf,
    Consent,
    Custodian,
    CustodianOrganization,
    DataEnterer,
    DocumentationOf,
    DocumentParticipant,
    EncompassingEncounter,
    EncounterParticipant,
    HealthCareFacility,
    Informant,
    InformationRecipient,
    InformationRecipientPerson,
    InFulfillmentOf,
    IntendedRecipient,
    LegalAuthenticator,
    Location,
    Order,
    ParentDocument,
    Place,
    RelatedDocument,
    RelatedEntity,
    RelatedPerson,
    ResponsibleParty,
    ServiceEvent,
    ServiceEventPerformer,
)

# Data types (HL7 V3 building blocks)
from .datatypes import (
    AD,
    BL,
    CD,
    CE,
    CO,
    CR,
    CS,
    CV,
    ED,
    EIVL_TS,
    EN,
    ENXP,
    GTS,
    II,
    INT,
    IVL_INT,
    IVL_PQ,
    IVL_TS,
    MO,
    ON,
    PIVL_TS,
    PN,
    PPD_PQ,
    PQ,
    REAL,
    RTO,
    ST,
    SXCM_TS,
    TEL,
    TN,
    TS,
    CDAModel,
    TELReference,
)
from .encounter import Encounter

# Clinical statements
from .observation import (
    EntryRelationship,
    Observation,
    ObservationRange,
    ReferenceRange,
)
from .organizer import (
    Organizer,
    OrganizerComponent,
)

# Participant
from .participant import (
    AssociatedEntity,
    AssociatedPerson,
    Participant,
    ParticipantRole,
    PlayingDevice,
    PlayingEntity,
    ScopingEntity,
    ScopingOrganization,
)

# Performer
from .performer import (
    AssignedEntity,
    Performer,
)
from .procedure import (
    Procedure,
    Specimen,
    SpecimenPlayingEntity,
    SpecimenRole,
)

# Record target (Patient)
from .record_target import (
    Birthplace,
    Guardian,
    GuardianPerson,
    LanguageCommunication,
    Organization,
    Patient,
    PatientRole,
    Place,
    RecordTarget,
)

# Section and document structure
from .section import (
    Component,
    Entry,
    NonXMLBody,
    Section,
    SectionComponent,
    StructuredBody,
)

# StrucDocText (narrative content)
from .struc_doc import (
    Br,
    Caption,
    Content,
    Footnote,
    FootnoteRef,
    LinkHtml,
    List,
    ListItem,
    Paragraph,
    RenderMultiMedia,
    StrucDocText,
    Sub,
    Sup,
    Table,
    TableBody,
    TableDataCell,
    TableFoot,
    TableHead,
    TableHeaderCell,
    TableRow,
)
from .substance_administration import (
    Consumable,
    Criterion,
    ManufacturedMaterial,
    ManufacturedProduct,
    ManufacturerOrganization,
    Precondition,
    SubstanceAdministration,
)
from .supply import Supply

__all__ = [
    # Base model
    "CDAModel",
    # Simple types
    "BL",
    "INT",
    "REAL",
    "ST",
    # Identifiers
    "II",
    # Coded types
    "CD",
    "CE",
    "CO",
    "CR",
    "CS",
    "CV",
    # Encapsulated data
    "ED",
    "TELReference",
    # Quantities
    "IVL_PQ",
    "MO",
    "PPD_PQ",
    "PQ",
    "RTO",
    # Time types
    "EIVL_TS",
    "GTS",
    "IVL_INT",
    "IVL_TS",
    "PIVL_TS",
    "SXCM_TS",
    "TS",
    # Telecom and address
    "AD",
    "TEL",
    # Name types
    "EN",
    "ENXP",
    "ON",
    "PN",
    "TN",
    # Record target / Patient
    "Birthplace",
    "Guardian",
    "GuardianPerson",
    "LanguageCommunication",
    "Organization",
    "Patient",
    "PatientRole",
    "Place",
    "RecordTarget",
    # Author
    "AssignedAuthor",
    "AssignedAuthoringDevice",
    "AssignedPerson",
    "Author",
    "MaintainedEntity",
    "RepresentedOrganization",
    # Performer
    "AssignedEntity",
    "Performer",
    # Participant
    "AssociatedEntity",
    "AssociatedPerson",
    "Participant",
    "ParticipantRole",
    "PlayingDevice",
    "PlayingEntity",
    "ScopingEntity",
    "ScopingOrganization",
    # Section and structure
    "Component",
    "Entry",
    "NonXMLBody",
    "Section",
    "SectionComponent",
    "StructuredBody",
    # StrucDocText (narrative)
    "Br",
    "Caption",
    "Content",
    "Footnote",
    "FootnoteRef",
    "LinkHtml",
    "List",
    "ListItem",
    "Paragraph",
    "RenderMultiMedia",
    "StrucDocText",
    "Sub",
    "Sup",
    "Table",
    "TableBody",
    "TableDataCell",
    "TableFoot",
    "TableHead",
    "TableHeaderCell",
    "TableRow",
    # Clinical document
    "AssignedCustodian",
    "Authenticator",
    "Authorization",
    "ClinicalDocument",
    "ComponentOf",
    "Consent",
    "Custodian",
    "CustodianOrganization",
    "DataEnterer",
    "DocumentationOf",
    "DocumentParticipant",
    "EncompassingEncounter",
    "EncounterParticipant",
    "HealthCareFacility",
    "Informant",
    "InformationRecipient",
    "InformationRecipientPerson",
    "InFulfillmentOf",
    "IntendedRecipient",
    "LegalAuthenticator",
    "Location",
    "Order",
    "ParentDocument",
    "Place",
    "RelatedDocument",
    "RelatedEntity",
    "RelatedPerson",
    "ResponsibleParty",
    "ServiceEvent",
    "ServiceEventPerformer",
    # Observation
    "EntryRelationship",
    "Observation",
    "ObservationRange",
    "ReferenceRange",
    # Act
    "Act",
    "ExternalAct",
    "ExternalDocument",
    "ExternalObservation",
    "ExternalProcedure",
    "Reference",
    # Procedure
    "Procedure",
    "Specimen",
    "SpecimenPlayingEntity",
    "SpecimenRole",
    # Substance Administration
    "Consumable",
    "Criterion",
    "ManufacturedMaterial",
    "ManufacturedProduct",
    "ManufacturerOrganization",
    "Precondition",
    "SubstanceAdministration",
    # Organizer
    "Organizer",
    "OrganizerComponent",
    # Encounter
    "Encounter",
    # Supply
    "Supply",
]

# Rebuild models with forward references after all imports are complete
# This resolves circular dependencies between clinical statement types
EntryRelationship.model_rebuild()
Entry.model_rebuild()
OrganizerComponent.model_rebuild()
ClinicalDocument.model_rebuild()
StructuredBody.model_rebuild()
Informant.model_rebuild()
Section.model_rebuild()
SectionComponent.model_rebuild()
