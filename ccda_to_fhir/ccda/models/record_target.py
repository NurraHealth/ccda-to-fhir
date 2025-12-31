"""C-CDA RecordTarget and Patient models.

The recordTarget represents the patient who is the subject of the clinical document.
Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-USRealmHeader.html
"""

from __future__ import annotations

from pydantic import Field

from .datatypes import AD, CE, CS, II, ON, PN, TEL, TS, CDAModel


class LanguageCommunication(CDAModel):
    """Patient's language communication abilities.

    Documents languages the patient can use for communication,
    along with proficiency and preference information.
    """

    # Per CDA spec, languageCode uses CS (Coded Simple) datatype
    language_code: CS | None = Field(default=None, alias="languageCode")
    mode_code: CE | None = Field(default=None, alias="modeCode")
    proficiency_level_code: CE | None = Field(default=None, alias="proficiencyLevelCode")
    preference_ind: bool | None = Field(default=None, alias="preferenceInd")


class GuardianPerson(CDAModel):
    """Person who is a guardian.

    Contains the name of the guardian person.
    """

    name: list[PN] | None = None


class Guardian(CDAModel):
    """Patient's guardian information.

    A guardian is a person or organization with legal responsibility
    for the patient.
    """

    id: list[II] | None = None
    code: CE | None = None  # Relationship to patient (e.g., FTH, MTH, GUARD)
    addr: list[AD] | None = None
    telecom: list[TEL] | None = None
    guardian_person: GuardianPerson | None = Field(default=None, alias="guardianPerson")
    guardian_organization: Organization | None = Field(default=None, alias="guardianOrganization")


class Place(CDAModel):
    """A physical place.

    Used for birthplace and other location references.
    """

    name: str | None = None
    addr: AD | None = None


class Birthplace(CDAModel):
    """Patient's birthplace.

    Contains the location where the patient was born.
    """

    place: Place | None = None


class Patient(CDAModel):
    """Patient demographics.

    Contains the demographic information about the patient including
    name, gender, birth date, and other identifying information.
    """

    # Names (multiple allowed for legal, maiden, etc.)
    name: list[PN] | None = None

    # Administrative gender
    administrative_gender_code: CE | None = Field(default=None, alias="administrativeGenderCode")

    # Birth information
    birth_time: TS | None = Field(default=None, alias="birthTime")
    birthplace: Birthplace | None = None

    # Marital and religious status
    marital_status_code: CE | None = Field(default=None, alias="maritalStatusCode")
    religious_affiliation_code: CE | None = Field(default=None, alias="religiousAffiliationCode")

    # Race and ethnicity (OMB categories)
    race_code: CE | None = Field(default=None, alias="raceCode")
    ethnic_group_code: CE | None = Field(default=None, alias="ethnicGroupCode")

    # SDTC extensions for additional race/ethnicity codes
    # These are in the sdtc namespace (urn:hl7-org:sdtc)
    sdtc_race_code: list[CE] | None = Field(default=None, alias="sdtc:raceCode")
    sdtc_ethnic_group_code: list[CE] | None = Field(default=None, alias="sdtc:ethnicGroupCode")

    # SDTC deceased indicator and time
    sdtc_deceased_ind: bool | None = Field(default=None, alias="sdtc:deceasedInd")
    sdtc_deceased_time: TS | None = Field(default=None, alias="sdtc:deceasedTime")

    # SDTC multiple birth indicator
    sdtc_multiple_birth_ind: bool | None = Field(default=None, alias="sdtc:multipleBirthInd")
    sdtc_multiple_birth_order_number: int | None = Field(
        default=None, alias="sdtc:multipleBirthOrderNumber"
    )

    # Guardian(s)
    guardian: list[Guardian] | None = None

    # Language communication abilities
    language_communication: list[LanguageCommunication] | None = Field(
        default=None, alias="languageCommunication"
    )


class Organization(CDAModel):
    """An organization.

    Used for provider organizations and other organizational entities.
    """

    id: list[II] | None = None
    name: list[ON | str] | None = None
    telecom: list[TEL] | None = None
    addr: list[AD] | None = None
    standardIndustryClassCode: CE | None = None


class PatientRole(CDAModel):
    """Patient role containing patient demographics and identifiers.

    The patientRole is the main container for patient information,
    including identifiers (MRN, SSN), contact information, and
    the patient demographics.
    """

    # Patient identifiers (MRN, SSN, etc.)
    id: list[II] | None = None

    # Contact information at the patient role level
    addr: list[AD] | None = None
    telecom: list[TEL] | None = None

    # The patient demographics
    patient: Patient | None = None

    # Provider organization
    provider_organization: Organization | None = Field(default=None, alias="providerOrganization")


class RecordTarget(CDAModel):
    """The patient who is the subject of the clinical document.

    The recordTarget is a required element in all C-CDA documents
    and contains the patientRole which holds all patient information.
    """

    # Context control code (default: OP - overriding propagating)
    context_control_code: str | None = Field(default=None, alias="contextControlCode")

    # Type code (default: RCT - record target)
    type_code: str | None = Field(default=None, alias="typeCode")

    # The patient role containing all patient information
    patient_role: PatientRole | None = Field(default=None, alias="patientRole")


# Update forward references for Guardian which references Organization
Guardian.model_rebuild()
