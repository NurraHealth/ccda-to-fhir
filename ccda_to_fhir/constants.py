"""Constants for C-CDA to FHIR conversion.

This module contains all magic strings used throughout the conversion process,
organized by category for maintainability and clarity.
"""

from __future__ import annotations

# =============================================================================
# C-CDA Template IDs
# =============================================================================

class TemplateIds:
    """C-CDA Template Identifiers."""

    # Problem templates
    PROBLEM_CONCERN_ACT = "2.16.840.1.113883.10.20.22.4.3"
    PROBLEM_OBSERVATION = "2.16.840.1.113883.10.20.22.4.4"
    PROBLEM_STATUS_OBSERVATION = "2.16.840.1.113883.10.20.22.4.6"
    DATE_OF_DIAGNOSIS_ACT = "2.16.840.1.113883.10.20.22.4.502"

    # Allergy templates
    ALLERGY_CONCERN_ACT = "2.16.840.1.113883.10.20.22.4.30"
    ALLERGY_INTOLERANCE_OBSERVATION = "2.16.840.1.113883.10.20.22.4.7"
    ALLERGY_STATUS_OBSERVATION = "2.16.840.1.113883.10.20.22.4.28"

    # Common observation templates
    SEVERITY_OBSERVATION = "2.16.840.1.113883.10.20.22.4.8"
    REACTION_OBSERVATION = "2.16.840.1.113883.10.20.22.4.9"
    AGE_OBSERVATION = "2.16.840.1.113883.10.20.22.4.31"
    CRITICALITY_OBSERVATION = "2.16.840.1.113883.10.20.22.4.145"
    COMMENT_ACTIVITY = "2.16.840.1.113883.10.20.22.4.64"
    ASSESSMENT_SCALE_OBSERVATION = "2.16.840.1.113883.10.20.22.4.69"

    # Author template
    AUTHOR_PARTICIPATION = "2.16.840.1.113883.10.20.22.4.119"

    # Medication templates
    MEDICATION_ACTIVITY = "2.16.840.1.113883.10.20.22.4.16"
    MEDICATION_INFORMATION = "2.16.840.1.113883.10.20.22.4.23"
    INDICATION_OBSERVATION = "2.16.840.1.113883.10.20.22.4.19"
    INSTRUCTION_ACT = "2.16.840.1.113883.10.20.22.4.20"
    MEDICATION_SUPPLY_ORDER = "2.16.840.1.113883.10.20.22.4.17"
    MEDICATION_DISPENSE = "2.16.840.1.113883.10.20.22.4.18"

    # Immunization templates
    IMMUNIZATION_ACTIVITY = "2.16.840.1.113883.10.20.22.4.52"
    IMMUNIZATION_MEDICATION_INFORMATION = "2.16.840.1.113883.10.20.22.4.54"
    IMMUNIZATION_REFUSAL_REASON = "2.16.840.1.113883.10.20.22.4.53"

    # Observation templates
    VITAL_SIGNS_ORGANIZER = "2.16.840.1.113883.10.20.22.4.26"
    VITAL_SIGN_OBSERVATION = "2.16.840.1.113883.10.20.22.4.27"
    RESULT_ORGANIZER = "2.16.840.1.113883.10.20.22.4.1"
    RESULT_OBSERVATION = "2.16.840.1.113883.10.20.22.4.2"
    SMOKING_STATUS_OBSERVATION = "2.16.840.1.113883.10.20.22.4.78"
    SOCIAL_HISTORY_OBSERVATION = "2.16.840.1.113883.10.20.22.4.38"
    PREGNANCY_OBSERVATION = "2.16.840.1.113883.10.20.15.3.8"
    ESTIMATED_DELIVERY_DATE_OBSERVATION = "2.16.840.1.113883.10.20.15.3.1"
    BIRTH_SEX_OBSERVATION = "2.16.840.1.113883.10.20.22.4.200"
    TRIBAL_AFFILIATION_OBSERVATION = "2.16.840.1.113883.10.20.22.4.506"
    SEX_PARAMETER_FOR_CLINICAL_USE_OBSERVATION = "2.16.840.1.113883.10.20.22.4.513"
    # Gender Identity Observation doesn't have a standardized template ID in C-CDA
    # It's typically identified by LOINC code 76691-5

    # Procedure templates
    PROCEDURE_ACTIVITY_PROCEDURE = "2.16.840.1.113883.10.20.22.4.14"
    PROCEDURE_ACTIVITY_ACT = "2.16.840.1.113883.10.20.22.4.12"
    PROCEDURE_ACTIVITY_OBSERVATION = "2.16.840.1.113883.10.20.22.4.13"
    PLANNED_PROCEDURE = "2.16.840.1.113883.10.20.22.4.41"
    PLANNED_ACT = "2.16.840.1.113883.10.20.22.4.39"

    # Encounter templates
    ENCOUNTER_ACTIVITY = "2.16.840.1.113883.10.20.22.4.49"
    ENCOUNTER_DIAGNOSIS = "2.16.840.1.113883.10.20.22.4.80"

    # Note templates
    NOTE_ACTIVITY = "2.16.840.1.113883.10.20.22.4.202"

    # Goal templates
    GOAL_OBSERVATION = "2.16.840.1.113883.10.20.22.4.121"
    PRIORITY_PREFERENCE = "2.16.840.1.113883.10.20.22.4.143"
    PROGRESS_TOWARD_GOAL = "2.16.840.1.113883.10.20.22.4.110"
    ENTRY_REFERENCE = "2.16.840.1.113883.10.20.22.4.122"

    # Care Plan templates
    HEALTH_CONCERN_ACT = "2.16.840.1.113883.10.20.22.4.132"
    INTERVENTION_ACT = "2.16.840.1.113883.10.20.22.4.131"
    PLANNED_INTERVENTION_ACT = "2.16.840.1.113883.10.20.22.4.146"

    # Care Team templates
    CARE_TEAM_ORGANIZER = "2.16.840.1.113883.10.20.22.4.500"
    CARE_TEAM_MEMBER_ACT = "2.16.840.1.113883.10.20.22.4.500.1"

    # Document templates
    CARE_PLAN_DOCUMENT = "2.16.840.1.113883.10.20.22.1.15"

    # Section templates
    PROBLEM_SECTION = "2.16.840.1.113883.10.20.22.2.5.1"
    ALLERGY_SECTION = "2.16.840.1.113883.10.20.22.2.6.1"
    MEDICATIONS_SECTION = "2.16.840.1.113883.10.20.22.2.1.1"
    IMMUNIZATIONS_SECTION = "2.16.840.1.113883.10.20.22.2.2.2.1"
    VITAL_SIGNS_SECTION = "2.16.840.1.113883.10.20.22.2.4.1"
    RESULTS_SECTION = "2.16.840.1.113883.10.20.22.2.3.1"
    SOCIAL_HISTORY_SECTION = "2.16.840.1.113883.10.20.22.2.17"
    PROCEDURES_SECTION = "2.16.840.1.113883.10.20.22.2.7.1"
    PLAN_OF_TREATMENT_SECTION = "2.16.840.1.113883.10.20.22.2.10"
    ENCOUNTERS_SECTION = "2.16.840.1.113883.10.20.22.2.22.1"
    NOTES_SECTION = "2.16.840.1.113883.10.20.22.2.65"
    GOALS_SECTION = "2.16.840.1.113883.10.20.22.2.60"
    HEALTH_CONCERNS_SECTION = "2.16.840.1.113883.10.20.22.2.58"
    INTERVENTIONS_SECTION = "2.16.840.1.113883.10.20.21.2.3"
    OUTCOMES_SECTION = "2.16.840.1.113883.10.20.22.2.61"
    CARE_TEAMS_SECTION = "2.16.840.1.113883.10.20.22.2.500"


# =============================================================================
# C-CDA OIDs
# =============================================================================

class CodeSystemOIDs:
    """C-CDA OID identifiers for code systems and identifiers."""

    # Identifier systems
    SSN = "2.16.840.1.113883.4.1"  # US Social Security Number
    NPI = "2.16.840.1.113883.4.6"  # US National Provider Identifier

    # Race and Ethnicity
    CDC_RACE_ETHNICITY = "2.16.840.1.113883.6.238"

    # Tribal affiliation
    TRIBAL_ENTITY_US = "2.16.840.1.113883.5.140"  # TribalEntityUS code system

    # Provider specialty/taxonomy
    NUCC_PROVIDER_TAXONOMY = "2.16.840.1.113883.6.101"  # NUCC Healthcare Provider Taxonomy


# =============================================================================
# C-CDA Codes
# =============================================================================

class CCDACodes:
    """C-CDA code values."""

    # Act codes
    CONCERN = "CONC"
    ASSERTION = "ASSERTION"

    # Observation codes (LOINC)
    STATUS = "33999-4"  # Status code
    CRITICALITY = "82606-5"  # Allergy or intolerance criticality
    AGE_AT_ONSET = "445518008"  # SNOMED code for age at onset
    BIRTH_SEX = "76689-9"  # Sex assigned at birth
    GENDER_IDENTITY = "76691-5"  # Gender identity
    SEX = "46098-0"  # Sex (documented clinical sex)
    SEX_PARAMETER_FOR_CLINICAL_USE = "99501-9"  # Sex parameter for clinical use
    TRIBAL_AFFILIATION = "95370-3"  # Tribal affiliation

    # Severity code
    SEVERITY = "SEV"

    # Section codes (LOINC)
    PROBLEM_LIST = "11450-4"
    ALLERGIES_SECTION = "48765-2"
    MEDICATIONS_SECTION_CODE = "10160-0"  # History of medication use


# =============================================================================
# C-CDA Type Codes
# =============================================================================

class TypeCodes:
    """C-CDA typeCode values for relationships."""

    SUBJECT = "SUBJ"  # Subject of the act
    REFERENCE = "REFR"  # Refers to
    MANIFESTATION = "MFST"  # Manifestation of
    CONSUMABLE = "CSM"  # Consumable (for allergen participant)
    REASON = "RSON"  # Reason for (indication)
    SUPPORT = "SPRT"  # Supporting observation (evidence)
    COMPONENT = "COMP"  # Component observation (assessment scale, etc.)
    RSON = "RSON"  # Alternative name for REASON
    MFST = "MFST"  # Alternative name for MANIFESTATION
    SPRT = "SPRT"  # Alternative name for SUPPORT
    COMP = "COMP"  # Alternative name for COMPONENT


# =============================================================================
# HL7 V2 and V3 Codes
# =============================================================================

class V2IdentifierTypes:
    """HL7 V2 Table 0203 - Identifier Type codes."""

    SOCIAL_SECURITY = "SS"
    MEDICAL_RECORD = "MR"
    NATIONAL_PROVIDER_ID = "NPI"


class V2ParticipationFunctionCodes:
    """HL7 V2 Table 0443 - Provider Role codes."""

    ADMITTING_PROVIDER = "AD"
    ADMINISTERING_PROVIDER = "AP"
    ATTENDING_PROVIDER = "AT"
    CONSULTING_PROVIDER = "CP"
    PRIMARY_CARE_PROVIDER = "PP"
    REFERRING_PROVIDER = "RP"
    TREATING_PROVIDER = "RT"


class V3RoleCodes:
    """HL7 V3 RoleCode values."""

    GUARDIAN = "GUARD"


class V3NameUseCodes:
    """HL7 V3 EntityNameUse codes."""

    LEGAL = "L"
    OFFICIAL_RECORD = "OR"
    LICENSE = "C"
    PSEUDONYM = "P"
    ANONYMOUS = "A"
    ASSIGNED = "ASGN"


class V3TelecomUseCodes:
    """HL7 V3 TelecomAddressUse codes."""

    PRIMARY_HOME = "HP"
    HOME = "H"
    WORK = "WP"
    MOBILE = "MC"
    TEMP = "TMP"
    BAD = "BAD"


class V3AddressUseCodes:
    """HL7 V3 PostalAddressUse codes."""

    HOME = "H"
    PRIMARY_HOME = "HP"
    VACATION_HOME = "HV"
    WORK = "WP"
    DIRECT = "DIR"
    PUBLIC = "PUB"
    TEMP = "TMP"
    BAD = "BAD"


class V3AdministrativeGenderCodes:
    """HL7 V3 AdministrativeGender codes."""

    MALE = "M"
    FEMALE = "F"
    UNDIFFERENTIATED = "UN"
    UNKNOWN = "UNK"


# =============================================================================
# CDC Race and Ethnicity Codes
# =============================================================================

class CDCRaceCodes:
    """CDC Race codes (OMB categories)."""

    # OMB Categories (main 5 categories)
    AMERICAN_INDIAN_OR_ALASKA_NATIVE = "1002-5"
    ASIAN = "2028-9"
    BLACK_OR_AFRICAN_AMERICAN = "2054-5"
    NATIVE_HAWAIIAN_OR_OTHER_PACIFIC_ISLANDER = "2076-8"
    WHITE = "2106-3"


class CDCEthnicityCodes:
    """CDC Ethnicity codes (OMB categories)."""

    # OMB Categories (2 main categories)
    HISPANIC_OR_LATINO = "2135-2"
    NOT_HISPANIC_OR_LATINO = "2186-5"


# =============================================================================
# SNOMED CT Codes
# =============================================================================

class SnomedCodes:
    """SNOMED CT codes for clinical concepts."""

    # Clinical status codes
    ACTIVE = "55561003"
    INACTIVE = "73425007"
    RESOLVED = "413322009"
    REMISSION = "277022003"
    RECURRENCE_255227004 = "255227004"
    RECURRENCE_246455001 = "246455001"  # Alternate recurrence code

    # Severity codes
    MILD = "255604002"
    MODERATE = "6736007"
    SEVERE = "24484000"

    # Allergy type codes
    ALLERGY_TO_SUBSTANCE = "419199007"
    DRUG_ALLERGY = "416098002"
    FOOD_ALLERGY = "414285001"
    ENVIRONMENTAL_ALLERGY = "426232007"
    PROPENSITY_TO_DRUG_REACTIONS = "419511003"
    DRUG_INTOLERANCE = "59037007"
    FOOD_INTOLERANCE = "235719002"
    PROPENSITY_TO_ADVERSE_REACTIONS = "420134006"
    PROPENSITY_TO_FOOD_REACTIONS = "418471000"

    # No known allergy codes (negated concept codes)
    NO_KNOWN_ALLERGY = "716186003"
    NO_KNOWN_DRUG_ALLERGY = "409137002"
    NO_KNOWN_FOOD_ALLERGY = "429625007"
    NO_KNOWN_ENVIRONMENTAL_ALLERGY = "428607008"

    # Problem-related codes
    PROBLEM = "55607006"  # Generic problem code
    FINDING = "404684003"  # Generic finding code
    CONDITION = "64572001"  # Generic condition/disease code

    # Negated problem codes
    NO_CURRENT_PROBLEMS = "160245001"  # No current problems or disability


# =============================================================================
# HL7 V3 Criticality Codes
# =============================================================================

class CriticalityCodes:
    """HL7 V3 Criticality observation codes."""

    LOW = "CRITL"
    HIGH = "CRITH"
    UNABLE_TO_ASSESS = "CRITU"


# =============================================================================
# FHIR Systems (URLs)
# =============================================================================

class FHIRSystems:
    """FHIR terminology system URLs."""

    # Condition
    CONDITION_CLINICAL = "http://terminology.hl7.org/CodeSystem/condition-clinical"
    CONDITION_VERIFICATION = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
    CONDITION_CATEGORY = "http://terminology.hl7.org/CodeSystem/condition-category"

    # AllergyIntolerance
    ALLERGY_CLINICAL = "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
    ALLERGY_VERIFICATION = "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"

    # Observation
    OBSERVATION_CATEGORY = "http://terminology.hl7.org/CodeSystem/observation-category"
    SDOH_CATEGORY = "http://hl7.org/fhir/us/sdoh-clinicalcare/CodeSystem/SDOHCC-CodeSystemTemporaryCodes"

    # DiagnosticReport
    V2_0074 = "http://terminology.hl7.org/CodeSystem/v2-0074"  # Diagnostic service section ID

    # HL7 V2 and V3 systems
    V2_IDENTIFIER_TYPE = "http://terminology.hl7.org/CodeSystem/v2-0203"
    V2_PARTICIPATION_FUNCTION = "http://terminology.hl7.org/CodeSystem/v2-0443"
    V3_ACT_CODE = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
    V3_ROLE_CODE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
    V3_PARTICIPATION_TYPE = "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
    V3_LANGUAGE_ABILITY_MODE = "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityMode"
    V3_LANGUAGE_ABILITY_PROFICIENCY = "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityProficiency"

    # Sex and Gender
    SEX_PARAMETER_FOR_CLINICAL_USE = "http://terminology.hl7.org/CodeSystem/sex-parameter-for-clinical-use"

    # Language
    BCP_47 = "urn:ietf:bcp:47"

    # CDC Race and Ethnicity
    CDC_RACE_ETHNICITY = "urn:oid:2.16.840.1.113883.6.238"

    # FHIR extensions
    ALLERGY_ABATEMENT_EXTENSION = "http://hl7.org/fhir/StructureDefinition/allergyintolerance-abatement"
    CONDITION_ASSERTED_DATE = "http://hl7.org/fhir/StructureDefinition/condition-assertedDate"
    DATA_ABSENT_REASON = "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
    PATIENT_RELIGION = "http://hl7.org/fhir/StructureDefinition/patient-religion"
    PATIENT_PROFICIENCY = "http://hl7.org/fhir/StructureDefinition/patient-proficiency"
    PATIENT_BIRTHPLACE = "http://hl7.org/fhir/StructureDefinition/patient-birthPlace"
    PATIENT_BIRTH_TIME = "http://hl7.org/fhir/StructureDefinition/patient-birthTime"

    # US Core extensions
    US_CORE_RACE = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"
    US_CORE_ETHNICITY = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"
    US_CORE_BIRTHSEX = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"
    US_CORE_GENDER_IDENTITY = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"
    US_CORE_SEX = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-sex"
    US_CORE_TRIBAL_AFFILIATION = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation"

    # FHIR Core extensions
    PATIENT_SEX_PARAMETER_FOR_CLINICAL_USE = "http://hl7.org/fhir/StructureDefinition/patient-sexParameterForClinicalUse"

    # Units
    UCUM = "http://unitsofmeasure.org"

    # Medications
    RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
    NDC = "http://hl7.org/fhir/sid/ndc"
    NCI_THESAURUS = "http://ncithesaurus-stage.nci.nih.gov"

    # Identifiers
    US_NPI = "http://hl7.org/fhir/sid/us-npi"  # US National Provider Identifier
    US_SSN = "http://hl7.org/fhir/sid/us-ssn"  # US Social Security Number

    # Device identifiers
    FDA_UDI = "http://hl7.org/fhir/NamingSystem/fda-udi"  # FDA Unique Device Identification

    # Provider taxonomy
    NUCC_PROVIDER_TAXONOMY = "http://nucc.org/provider-taxonomy"  # NUCC Healthcare Provider Taxonomy
    NUCC_TAXONOMY = NUCC_PROVIDER_TAXONOMY  # Alias for convenience

    # Provenance
    PROVENANCE_PARTICIPANT_TYPE = "http://terminology.hl7.org/CodeSystem/provenance-participant-type"
    PROVENANCE_ACTIVITY_TYPE = "http://terminology.hl7.org/CodeSystem/v3-DataOperation"


# =============================================================================
# FHIR Codes
# =============================================================================

class FHIRCodes:
    """FHIR code values."""

    # Condition clinical status
    class ConditionClinical:
        ACTIVE = "active"
        INACTIVE = "inactive"
        RESOLVED = "resolved"
        REMISSION = "remission"
        RECURRENCE = "recurrence"

    # Condition verification status
    class ConditionVerification:
        CONFIRMED = "confirmed"
        REFUTED = "refuted"

    # Condition category
    class ConditionCategory:
        PROBLEM_LIST_ITEM = "problem-list-item"
        ENCOUNTER_DIAGNOSIS = "encounter-diagnosis"

    # AllergyIntolerance clinical status
    class AllergyClinical:
        ACTIVE = "active"
        INACTIVE = "inactive"
        RESOLVED = "resolved"

    # AllergyIntolerance verification status
    class AllergyVerification:
        CONFIRMED = "confirmed"
        REFUTED = "refuted"

    # AllergyIntolerance type
    class AllergyType:
        ALLERGY = "allergy"
        INTOLERANCE = "intolerance"

    # AllergyIntolerance category
    class AllergyCategory:
        MEDICATION = "medication"
        FOOD = "food"
        ENVIRONMENT = "environment"

    # AllergyIntolerance criticality
    class AllergyCriticality:
        LOW = "low"
        HIGH = "high"
        UNABLE_TO_ASSESS = "unable-to-assess"

    # Reaction severity
    class ReactionSeverity:
        MILD = "mild"
        MODERATE = "moderate"
        SEVERE = "severe"

    # MedicationRequest status
    class MedicationRequestStatus:
        ACTIVE = "active"
        ON_HOLD = "on-hold"
        CANCELLED = "cancelled"
        COMPLETED = "completed"
        STOPPED = "stopped"
        DRAFT = "draft"
        UNKNOWN = "unknown"
        ENTERED_IN_ERROR = "entered-in-error"

    # MedicationRequest intent
    class MedicationRequestIntent:
        PROPOSAL = "proposal"
        PLAN = "plan"
        ORDER = "order"
        ORIGINAL_ORDER = "original-order"
        REFLEX_ORDER = "reflex-order"
        FILLER_ORDER = "filler-order"
        INSTANCE_ORDER = "instance-order"
        OPTION = "option"

    # MedicationStatement status
    class MedicationStatementStatus:
        ACTIVE = "active"
        COMPLETED = "completed"
        ENTERED_IN_ERROR = "entered-in-error"
        INTENDED = "intended"
        STOPPED = "stopped"
        ON_HOLD = "on-hold"
        UNKNOWN = "unknown"
        NOT_TAKEN = "not-taken"

    # MedicationDispense status
    class MedicationDispenseStatus:
        PREPARATION = "preparation"
        IN_PROGRESS = "in-progress"
        CANCELLED = "cancelled"
        ON_HOLD = "on-hold"
        COMPLETED = "completed"
        ENTERED_IN_ERROR = "entered-in-error"
        STOPPED = "stopped"
        DECLINED = "declined"
        UNKNOWN = "unknown"

    # Immunization status
    class Immunization:
        STATUS_COMPLETED = "completed"
        STATUS_NOT_DONE = "not-done"
        STATUS_ENTERED_IN_ERROR = "entered-in-error"

    # Observation status
    class ObservationStatus:
        REGISTERED = "registered"
        PRELIMINARY = "preliminary"
        FINAL = "final"
        AMENDED = "amended"
        CORRECTED = "corrected"
        CANCELLED = "cancelled"
        ENTERED_IN_ERROR = "entered-in-error"
        UNKNOWN = "unknown"

    # Procedure status
    class ProcedureStatus:
        PREPARATION = "preparation"
        IN_PROGRESS = "in-progress"
        NOT_DONE = "not-done"
        ON_HOLD = "on-hold"
        STOPPED = "stopped"
        COMPLETED = "completed"
        ENTERED_IN_ERROR = "entered-in-error"
        UNKNOWN = "unknown"

    # ServiceRequest status
    class ServiceRequestStatus:
        DRAFT = "draft"
        ACTIVE = "active"
        ON_HOLD = "on-hold"
        REVOKED = "revoked"
        COMPLETED = "completed"
        ENTERED_IN_ERROR = "entered-in-error"
        UNKNOWN = "unknown"

    # ServiceRequest intent
    class ServiceRequestIntent:
        PROPOSAL = "proposal"
        PLAN = "plan"
        ORDER = "order"
        DIRECTIVE = "directive"
        ORIGINAL_ORDER = "original-order"
        REFLEX_ORDER = "reflex-order"
        FILLER_ORDER = "filler-order"
        INSTANCE_ORDER = "instance-order"
        OPTION = "option"

    # ServiceRequest priority
    class ServiceRequestPriority:
        ROUTINE = "routine"
        URGENT = "urgent"
        ASAP = "asap"
        STAT = "stat"

    # Encounter status
    class EncounterStatus:
        PLANNED = "planned"
        ARRIVED = "arrived"
        TRIAGED = "triaged"
        IN_PROGRESS = "in-progress"
        ONLEAVE = "onleave"
        FINISHED = "finished"
        CANCELLED = "cancelled"
        ENTERED_IN_ERROR = "entered-in-error"
        UNKNOWN = "unknown"

    # Encounter class (v3 ActCode)
    class EncounterClass:
        AMBULATORY = "AMB"  # Ambulatory
        EMERGENCY = "EMER"  # Emergency
        FIELD = "FLD"  # Field
        HOME_HEALTH = "HH"  # Home health
        INPATIENT = "IMP"  # Inpatient encounter
        INPATIENT_ACUTE = "ACUTE"  # Inpatient acute
        INPATIENT_NON_ACUTE = "NONAC"  # Inpatient non-acute
        OBSERVATION = "OBSENC"  # Observation encounter
        PREOPERATIVE = "PRENC"  # Pre-admission
        SHORT_STAY = "SS"  # Short stay
        VIRTUAL = "VR"  # Virtual

    # DocumentReference status
    class DocumentReferenceStatus:
        CURRENT = "current"
        SUPERSEDED = "superseded"
        ENTERED_IN_ERROR = "entered-in-error"

    # Composition status
    class CompositionStatus:
        PRELIMINARY = "preliminary"
        FINAL = "final"
        AMENDED = "amended"
        ENTERED_IN_ERROR = "entered-in-error"

    # Observation category
    class ObservationCategory:
        VITAL_SIGNS = "vital-signs"
        LABORATORY = "laboratory"
        SOCIAL_HISTORY = "social-history"
        EXAM = "exam"
        IMAGING = "imaging"
        PROCEDURE = "procedure"
        SURVEY = "survey"
        THERAPY = "therapy"
        ACTIVITY = "activity"

    # SDOH categories (from SDOHCC ValueSet)
    class SDOHCategory:
        FOOD_INSECURITY = "food-insecurity"
        HOUSING_INSTABILITY = "housing-instability"
        HOMELESSNESS = "homelessness"
        INADEQUATE_HOUSING = "inadequate-housing"
        TRANSPORTATION_INSECURITY = "transportation-insecurity"
        FINANCIAL_INSECURITY = "financial-insecurity"
        MATERIAL_HARDSHIP = "material-hardship"
        EDUCATIONAL_ATTAINMENT = "educational-attainment"
        EMPLOYMENT_STATUS = "employment-status"
        VETERAN_STATUS = "veteran-status"
        STRESS = "stress"
        SOCIAL_CONNECTION = "social-connection"
        INTIMATE_PARTNER_VIOLENCE = "intimate-partner-violence"
        ELDER_ABUSE = "elder-abuse"
        PERSONAL_HEALTH_LITERACY = "personal-health-literacy"
        HEALTH_INSURANCE_COVERAGE_STATUS = "health-insurance-coverage-status"
        MEDICAL_COST_BURDEN = "medical-cost-burden"
        DIGITAL_LITERACY = "digital-literacy"
        DIGITAL_ACCESS = "digital-access"
        UTILITY_INSECURITY = "utility-insecurity"
        INCARCERATION_STATUS = "incarceration-status"
        LANGUAGE_ACCESS = "language-access"
        SDOH_CATEGORY_UNSPECIFIED = "sdoh-category-unspecified"

    # DiagnosticReport status
    class DiagnosticReportStatus:
        REGISTERED = "registered"
        PARTIAL = "partial"
        PRELIMINARY = "preliminary"
        FINAL = "final"
        AMENDED = "amended"
        CORRECTED = "corrected"
        APPENDED = "appended"
        CANCELLED = "cancelled"
        ENTERED_IN_ERROR = "entered-in-error"
        UNKNOWN = "unknown"

    # DiagnosticReport category (v2-0074)
    class DiagnosticReportCategory:
        LAB = "LAB"  # Laboratory
        RAD = "RAD"  # Radiology
        PATH = "PATH"  # Pathology
        CARD = "CARD"  # Cardiology
        GEN = "GEN"  # Genetics

    # Resource types (for consistent resource type strings)
    class ResourceTypes:
        IMMUNIZATION = "Immunization"
        PATIENT = "Patient"
        CONDITION = "Condition"
        ALLERGY_INTOLERANCE = "AllergyIntolerance"
        MEDICATION_REQUEST = "MedicationRequest"
        OBSERVATION = "Observation"
        DIAGNOSTIC_REPORT = "DiagnosticReport"
        DEVICE = "Device"
        PROCEDURE = "Procedure"
        ENCOUNTER = "Encounter"
        PRACTITIONER = "Practitioner"
        PRACTITIONER_ROLE = "PractitionerRole"
        ORGANIZATION = "Organization"
        RELATED_PERSON = "RelatedPerson"
        DOCUMENT_REFERENCE = "DocumentReference"
        COMPOSITION = "Composition"
        LOCATION = "Location"
        PROVENANCE = "Provenance"
        GOAL = "Goal"
        CAREPLAN = "CarePlan"
        CARETEAM = "CareTeam"
        SERVICE_REQUEST = "ServiceRequest"

    # Patient gender
    class PatientGender:
        MALE = "male"
        FEMALE = "female"
        OTHER = "other"
        UNKNOWN = "unknown"

    # HumanName use
    class NameUse:
        USUAL = "usual"
        OFFICIAL = "official"
        OLD = "old"
        NICKNAME = "nickname"
        ANONYMOUS = "anonymous"

    # ContactPoint use
    class ContactPointUse:
        HOME = "home"
        WORK = "work"
        MOBILE = "mobile"
        TEMP = "temp"
        OLD = "old"

    # ContactPoint system
    class ContactPointSystem:
        PHONE = "phone"
        EMAIL = "email"
        FAX = "fax"
        URL = "url"

    # Address use
    class AddressUse:
        HOME = "home"
        WORK = "work"
        TEMP = "temp"
        OLD = "old"

    # Address type
    class AddressType:
        PHYSICAL = "physical"
        POSTAL = "postal"

    # Provenance agent type
    class ProvenanceAgent:
        AUTHOR = "author"
        PERFORMER = "performer"
        INFORMANT = "informant"
        ENTERER = "enterer"
        ATTESTER = "attester"
        CUSTODIAN = "custodian"

    # Provenance activity type
    class ProvenanceActivity:
        CREATE = "CREATE"
        UPDATE = "UPDATE"

    # Data absent reason
    UNKNOWN = "unknown"


# =============================================================================
# NoImmunizationReason ValueSet (2.16.840.1.113883.1.11.19717)
# =============================================================================
# Codes from v3-ActReason code system that represent reasons for not administering an immunization
# These should map to Immunization.statusReason when negationInd="true"
# Reference: http://terminology.hl7.org/CodeSystem/v3-ActReason
# This value set contains exactly the codes from the _ActNoImmunizationReason hierarchy
NO_IMMUNIZATION_REASON_CODES = frozenset({
    "IMMUNE",      # Immunity - patient already immune
    "MEDPREC",     # Medical precaution - medical condition or precaution
    "OSTOCK",      # Out of stock - vaccine not available
    "PATOBJ",      # Patient objection - patient refused
    "PHILISOP",    # Philosophical objection - personal beliefs
    "RELIG",       # Religious objection - religious beliefs
    "VACEFF",      # Vaccine efficacy concerns - doubts about effectiveness
    "VACSAF",      # Vaccine safety concerns - safety worries
})


# =============================================================================
# Age Units
# =============================================================================

class AgeUnits:
    """Age unit codes for C-CDA and FHIR."""

    # C-CDA units
    YEARS_CCDA = "a"
    MONTHS_CCDA = "mo"
    DAYS_CCDA = "d"

    # FHIR units
    YEAR = "year"
    MONTH = "month"
    DAY = "day"


# =============================================================================
# Status Code Mappings
# =============================================================================

# Map C-CDA concern act statusCode to FHIR clinicalStatus
CONCERN_STATUS_TO_CLINICAL_STATUS = {
    "active": FHIRCodes.ConditionClinical.ACTIVE,
    "completed": FHIRCodes.ConditionClinical.RESOLVED,  # or inactive if no abatement
    "suspended": FHIRCodes.ConditionClinical.INACTIVE,
    "aborted": FHIRCodes.ConditionClinical.INACTIVE,
}

# Map SNOMED problem status to FHIR clinicalStatus
SNOMED_PROBLEM_STATUS_TO_FHIR = {
    SnomedCodes.ACTIVE: FHIRCodes.ConditionClinical.ACTIVE,
    SnomedCodes.INACTIVE: FHIRCodes.ConditionClinical.INACTIVE,
    SnomedCodes.RESOLVED: FHIRCodes.ConditionClinical.RESOLVED,
    SnomedCodes.REMISSION: FHIRCodes.ConditionClinical.REMISSION,
    SnomedCodes.RECURRENCE_255227004: FHIRCodes.ConditionClinical.RECURRENCE,
    SnomedCodes.RECURRENCE_246455001: FHIRCodes.ConditionClinical.RECURRENCE,
}

# Map SNOMED allergy status to FHIR clinicalStatus
SNOMED_ALLERGY_STATUS_TO_FHIR = {
    SnomedCodes.ACTIVE: FHIRCodes.AllergyClinical.ACTIVE,
    SnomedCodes.INACTIVE: FHIRCodes.AllergyClinical.INACTIVE,
    SnomedCodes.RESOLVED: FHIRCodes.AllergyClinical.RESOLVED,
}

# Map SNOMED severity codes to FHIR severity
SNOMED_SEVERITY_TO_FHIR = {
    SnomedCodes.MILD: FHIRCodes.ReactionSeverity.MILD,
    SnomedCodes.MODERATE: FHIRCodes.ReactionSeverity.MODERATE,
    SnomedCodes.SEVERE: FHIRCodes.ReactionSeverity.SEVERE,
}

# Map HL7 criticality codes to FHIR criticality
CRITICALITY_CODE_TO_FHIR = {
    CriticalityCodes.LOW: FHIRCodes.AllergyCriticality.LOW,
    CriticalityCodes.HIGH: FHIRCodes.AllergyCriticality.HIGH,
    CriticalityCodes.UNABLE_TO_ASSESS: FHIRCodes.AllergyCriticality.UNABLE_TO_ASSESS,
}

# Map C-CDA age units to FHIR
AGE_UNIT_MAP = {
    AgeUnits.YEARS_CCDA: (AgeUnits.YEAR, AgeUnits.YEARS_CCDA),
    AgeUnits.MONTHS_CCDA: (AgeUnits.MONTH, AgeUnits.MONTHS_CCDA),
    AgeUnits.DAYS_CCDA: (AgeUnits.DAY, AgeUnits.DAYS_CCDA),
}

# Map SNOMED allergy type codes to FHIR type and category
ALLERGY_TYPE_CATEGORY_MAP = {
    # (type, category)
    SnomedCodes.ALLERGY_TO_SUBSTANCE: (FHIRCodes.AllergyType.ALLERGY, None),
    SnomedCodes.DRUG_ALLERGY: (FHIRCodes.AllergyType.ALLERGY, FHIRCodes.AllergyCategory.MEDICATION),
    SnomedCodes.FOOD_ALLERGY: (FHIRCodes.AllergyType.ALLERGY, FHIRCodes.AllergyCategory.FOOD),
    SnomedCodes.ENVIRONMENTAL_ALLERGY: (FHIRCodes.AllergyType.ALLERGY, FHIRCodes.AllergyCategory.ENVIRONMENT),
    SnomedCodes.PROPENSITY_TO_DRUG_REACTIONS: (FHIRCodes.AllergyType.ALLERGY, FHIRCodes.AllergyCategory.MEDICATION),
    SnomedCodes.DRUG_INTOLERANCE: (FHIRCodes.AllergyType.INTOLERANCE, FHIRCodes.AllergyCategory.MEDICATION),
    SnomedCodes.FOOD_INTOLERANCE: (FHIRCodes.AllergyType.INTOLERANCE, FHIRCodes.AllergyCategory.FOOD),
    SnomedCodes.PROPENSITY_TO_ADVERSE_REACTIONS: (None, None),
    SnomedCodes.PROPENSITY_TO_FOOD_REACTIONS: (FHIRCodes.AllergyType.ALLERGY, FHIRCodes.AllergyCategory.FOOD),
}

# Map section LOINC codes to FHIR Condition category
SECTION_CODE_TO_CONDITION_CATEGORY = {
    CCDACodes.PROBLEM_LIST: FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,
    "10160-0": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # History of medication use
    "11348-0": FHIRCodes.ConditionCategory.ENCOUNTER_DIAGNOSIS,  # History of past illness
    "29545-1": FHIRCodes.ConditionCategory.ENCOUNTER_DIAGNOSIS,  # Physical findings
    "46240-8": FHIRCodes.ConditionCategory.ENCOUNTER_DIAGNOSIS,  # History of Hospitalizations
}

# Map problem type SNOMED codes to FHIR Condition category
PROBLEM_TYPE_TO_CONDITION_CATEGORY = {
    "55607006": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # Problem
    "404684003": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # Finding
    "282291009": FHIRCodes.ConditionCategory.ENCOUNTER_DIAGNOSIS,  # Diagnosis
    "64572001": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # Condition
    "248536006": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # Symptom
    "418799008": FHIRCodes.ConditionCategory.PROBLEM_LIST_ITEM,  # Complaint
}

# =============================================================================
# Patient Mappings
# =============================================================================

# Map C-CDA name use codes to FHIR
NAME_USE_MAP = {
    V3NameUseCodes.LEGAL: FHIRCodes.NameUse.USUAL,
    V3NameUseCodes.OFFICIAL_RECORD: FHIRCodes.NameUse.OFFICIAL,
    V3NameUseCodes.LICENSE: FHIRCodes.NameUse.OLD,
    V3NameUseCodes.PSEUDONYM: FHIRCodes.NameUse.NICKNAME,
    V3NameUseCodes.ANONYMOUS: FHIRCodes.NameUse.ANONYMOUS,
    V3NameUseCodes.ASSIGNED: FHIRCodes.NameUse.USUAL,
}

# Map C-CDA telecom use codes to FHIR
TELECOM_USE_MAP = {
    V3TelecomUseCodes.PRIMARY_HOME: FHIRCodes.ContactPointUse.HOME,
    V3TelecomUseCodes.HOME: FHIRCodes.ContactPointUse.HOME,
    V3TelecomUseCodes.WORK: FHIRCodes.ContactPointUse.WORK,
    V3TelecomUseCodes.MOBILE: FHIRCodes.ContactPointUse.MOBILE,
    V3TelecomUseCodes.TEMP: FHIRCodes.ContactPointUse.TEMP,
    V3TelecomUseCodes.BAD: FHIRCodes.ContactPointUse.OLD,
}

# Map C-CDA address use codes to FHIR
ADDRESS_USE_MAP = {
    V3AddressUseCodes.HOME: FHIRCodes.AddressUse.HOME,
    V3AddressUseCodes.PRIMARY_HOME: FHIRCodes.AddressUse.HOME,
    V3AddressUseCodes.VACATION_HOME: FHIRCodes.AddressUse.HOME,
    V3AddressUseCodes.WORK: FHIRCodes.AddressUse.WORK,
    V3AddressUseCodes.DIRECT: FHIRCodes.AddressUse.WORK,
    V3AddressUseCodes.PUBLIC: FHIRCodes.AddressUse.WORK,
    V3AddressUseCodes.TEMP: FHIRCodes.AddressUse.TEMP,
    V3AddressUseCodes.BAD: FHIRCodes.AddressUse.OLD,
}

# Map C-CDA administrative gender to FHIR
ADMINISTRATIVE_GENDER_MAP = {
    V3AdministrativeGenderCodes.MALE: FHIRCodes.PatientGender.MALE,
    V3AdministrativeGenderCodes.FEMALE: FHIRCodes.PatientGender.FEMALE,
    V3AdministrativeGenderCodes.UNDIFFERENTIATED: FHIRCodes.PatientGender.OTHER,
    V3AdministrativeGenderCodes.UNKNOWN: FHIRCodes.PatientGender.UNKNOWN,
}

# OMB race category codes (for US Core race extension)
OMB_RACE_CATEGORIES = {
    CDCRaceCodes.AMERICAN_INDIAN_OR_ALASKA_NATIVE,
    CDCRaceCodes.ASIAN,
    CDCRaceCodes.BLACK_OR_AFRICAN_AMERICAN,
    CDCRaceCodes.NATIVE_HAWAIIAN_OR_OTHER_PACIFIC_ISLANDER,
    CDCRaceCodes.WHITE,
}

# OMB ethnicity category codes (for US Core ethnicity extension)
OMB_ETHNICITY_CATEGORIES = {
    CDCEthnicityCodes.HISPANIC_OR_LATINO,
    CDCEthnicityCodes.NOT_HISPANIC_OR_LATINO,
}

# =============================================================================
# Medication Mappings
# =============================================================================

# Map C-CDA medication statusCode to FHIR MedicationRequest status
# Per ConceptMap: http://hl7.org/fhir/us/ccda/ConceptMap/CF-MedicationStatus
MEDICATION_STATUS_TO_FHIR = {
    "active": FHIRCodes.MedicationRequestStatus.ACTIVE,
    "completed": FHIRCodes.MedicationRequestStatus.COMPLETED,
    "aborted": FHIRCodes.MedicationRequestStatus.STOPPED,
    "cancelled": FHIRCodes.MedicationRequestStatus.CANCELLED,
    "suspended": FHIRCodes.MedicationRequestStatus.ON_HOLD,
    "held": FHIRCodes.MedicationRequestStatus.ON_HOLD,
    "new": FHIRCodes.MedicationRequestStatus.DRAFT,
    "nullified": FHIRCodes.MedicationRequestStatus.ENTERED_IN_ERROR,
}

# Map C-CDA medication statusCode to FHIR MedicationStatement status
MEDICATION_STATUS_TO_FHIR_STATEMENT = {
    "active": FHIRCodes.MedicationStatementStatus.ACTIVE,
    "completed": FHIRCodes.MedicationStatementStatus.COMPLETED,
    "aborted": FHIRCodes.MedicationStatementStatus.STOPPED,
    "cancelled": FHIRCodes.MedicationStatementStatus.STOPPED,
    "suspended": FHIRCodes.MedicationStatementStatus.ON_HOLD,
    "held": FHIRCodes.MedicationStatementStatus.ON_HOLD,
    "new": FHIRCodes.MedicationStatementStatus.INTENDED,
    "nullified": FHIRCodes.MedicationStatementStatus.ENTERED_IN_ERROR,
}

# Map C-CDA medication dispense statusCode to FHIR MedicationDispense status
# Per mapping specification: docs/mapping/15-medication-dispense.md
MEDICATION_DISPENSE_STATUS_TO_FHIR = {
    "completed": FHIRCodes.MedicationDispenseStatus.COMPLETED,
    "active": FHIRCodes.MedicationDispenseStatus.IN_PROGRESS,
    "aborted": FHIRCodes.MedicationDispenseStatus.STOPPED,
    "cancelled": FHIRCodes.MedicationDispenseStatus.CANCELLED,
    "held": FHIRCodes.MedicationDispenseStatus.ON_HOLD,
    "new": FHIRCodes.MedicationDispenseStatus.PREPARATION,
    "nullified": FHIRCodes.MedicationDispenseStatus.ENTERED_IN_ERROR,
}

# Map C-CDA medication moodCode to FHIR MedicationRequest intent
# Note: EVN (event/historical) maps to MedicationStatement, not MedicationRequest
MEDICATION_MOOD_TO_INTENT = {
    "INT": FHIRCodes.MedicationRequestIntent.PLAN,  # Intent
    "RQO": FHIRCodes.MedicationRequestIntent.ORDER,  # Request
    "PRMS": FHIRCodes.MedicationRequestIntent.PROPOSAL,  # Promise
    "PRP": FHIRCodes.MedicationRequestIntent.PROPOSAL,  # Proposal
}

# Map UCUM time units to FHIR UnitsOfTime
# FHIR UnitsOfTime: s | min | h | d | wk | mo | a
UCUM_TO_FHIR_UNITS_OF_TIME = {
    "s": "s",
    "sec": "s",
    "second": "s",
    "seconds": "s",
    "min": "min",
    "minute": "min",
    "minutes": "min",
    "h": "h",
    "hour": "h",
    "hours": "h",
    "d": "d",
    "day": "d",
    "days": "d",
    "wk": "wk",
    "week": "wk",
    "weeks": "wk",
    "mo": "mo",
    "month": "mo",
    "months": "mo",
    "a": "a",
    "year": "a",
    "years": "a",
}

# Map EIVL_TS event codes to FHIR Timing.repeat.when
# Reference: http://hl7.org/fhir/valueset-event-timing.html
EIVL_EVENT_TO_FHIR_WHEN = {
    # Meal-related
    "AC": "AC",      # before meal (from lat. ante cibus)
    "ACM": "ACM",    # before breakfast (from lat. ante cibus matutinus)
    "ACD": "ACD",    # before lunch (from lat. ante cibus diurnus)
    "ACV": "ACV",    # before dinner (from lat. ante cibus vespertinus)
    "PC": "PC",      # after meal (from lat. post cibus)
    "PCM": "PCM",    # after breakfast (from lat. post cibus matutinus)
    "PCD": "PCD",    # after lunch (from lat. post cibus diurnus)
    "PCV": "PCV",    # after dinner (from lat. post cibus vespertinus)
    # Sleep-related
    "HS": "HS",      # before sleep (from lat. hora somni)
    "WAKE": "WAKE",  # upon waking
    # Daily events
    "CM": "CM",      # in the morning
    "CD": "CD",      # in the afternoon
    "CV": "CV",      # in the evening
    "C": "C",        # at a meal (from lat. cum)
}

# =============================================================================
# Observation Mappings
# =============================================================================

# Map C-CDA observation statusCode to FHIR Observation status
# Per ConceptMap CF-ResultStatus: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-ResultStatus.html
OBSERVATION_STATUS_TO_FHIR = {
    "completed": FHIRCodes.ObservationStatus.FINAL,
    "active": FHIRCodes.ObservationStatus.REGISTERED,
    "held": FHIRCodes.ObservationStatus.REGISTERED,
    "suspended": FHIRCodes.ObservationStatus.REGISTERED,
    "aborted": FHIRCodes.ObservationStatus.CANCELLED,
    "cancelled": FHIRCodes.ObservationStatus.CANCELLED,
}

# Map C-CDA observation statusCode to FHIR DiagnosticReport status
# Per ConceptMap CF-ResultReportStatus: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-ResultReportStatus.html
DIAGNOSTIC_REPORT_STATUS_TO_FHIR = {
    "completed": FHIRCodes.DiagnosticReportStatus.FINAL,
    "active": FHIRCodes.DiagnosticReportStatus.REGISTERED,
    "held": FHIRCodes.DiagnosticReportStatus.REGISTERED,
    "suspended": FHIRCodes.DiagnosticReportStatus.REGISTERED,
    "aborted": FHIRCodes.DiagnosticReportStatus.CANCELLED,
    "cancelled": FHIRCodes.DiagnosticReportStatus.CANCELLED,
}

# =============================================================================
# Procedure Mappings
# =============================================================================

# Map C-CDA procedure statusCode to FHIR Procedure status
PROCEDURE_STATUS_TO_FHIR = {
    "completed": FHIRCodes.ProcedureStatus.COMPLETED,
    "active": FHIRCodes.ProcedureStatus.IN_PROGRESS,
    "aborted": FHIRCodes.ProcedureStatus.STOPPED,
    "cancelled": FHIRCodes.ProcedureStatus.NOT_DONE,
    "new": FHIRCodes.ProcedureStatus.PREPARATION,
    "held": FHIRCodes.ProcedureStatus.ON_HOLD,
    "suspended": FHIRCodes.ProcedureStatus.ON_HOLD,
}

# =============================================================================
# ServiceRequest Mappings
# =============================================================================

# Map C-CDA statusCode to FHIR ServiceRequest status
SERVICE_REQUEST_STATUS_TO_FHIR = {
    "active": FHIRCodes.ServiceRequestStatus.ACTIVE,
    "completed": FHIRCodes.ServiceRequestStatus.COMPLETED,
    "aborted": FHIRCodes.ServiceRequestStatus.REVOKED,
    "cancelled": FHIRCodes.ServiceRequestStatus.REVOKED,
    "held": FHIRCodes.ServiceRequestStatus.ON_HOLD,
    "suspended": FHIRCodes.ServiceRequestStatus.ON_HOLD,
    "new": FHIRCodes.ServiceRequestStatus.DRAFT,
}

# Map C-CDA moodCode to FHIR ServiceRequest intent
SERVICE_REQUEST_MOOD_TO_INTENT = {
    "INT": FHIRCodes.ServiceRequestIntent.PLAN,  # Intent
    "RQO": FHIRCodes.ServiceRequestIntent.ORDER,  # Request
    "PRP": FHIRCodes.ServiceRequestIntent.PROPOSAL,  # Proposal
    "ARQ": FHIRCodes.ServiceRequestIntent.ORDER,  # Appointment request
    "PRMS": FHIRCodes.ServiceRequestIntent.DIRECTIVE,  # Promise
}

# Map C-CDA priorityCode to FHIR ServiceRequest priority
SERVICE_REQUEST_PRIORITY_TO_FHIR = {
    "R": FHIRCodes.ServiceRequestPriority.ROUTINE,  # Routine
    "UR": FHIRCodes.ServiceRequestPriority.URGENT,  # Urgent
    "EM": FHIRCodes.ServiceRequestPriority.STAT,  # Emergency/Stat
    "A": FHIRCodes.ServiceRequestPriority.ASAP,  # ASAP
    "EL": FHIRCodes.ServiceRequestPriority.ROUTINE,  # Elective
}

# =============================================================================
# Encounter Mappings
# =============================================================================

# Map C-CDA encounter statusCode to FHIR Encounter status
ENCOUNTER_STATUS_TO_FHIR = {
    "completed": FHIRCodes.EncounterStatus.FINISHED,
    "active": FHIRCodes.EncounterStatus.IN_PROGRESS,
    "aborted": FHIRCodes.EncounterStatus.CANCELLED,
    "cancelled": FHIRCodes.EncounterStatus.CANCELLED,
}

# Map C-CDA V3 ActCode encounter class codes
V3_ACT_CODE_SYSTEM = "2.16.840.1.113883.5.4"

# V3 ActEncounterCode standard display names (all lowercase per FHIR R4 specification)
# Reference: https://terminology.hl7.org/ValueSet-v3-ActEncounterCode.html
# Reference: https://www.hl7.org/fhir/R4/v3/ActCode/vs.html
V3_ACTCODE_DISPLAY_NAMES = {
    "AMB": "ambulatory",
    "EMER": "emergency",
    "FLD": "field",
    "HH": "home health",
    "IMP": "inpatient encounter",
    "ACUTE": "inpatient acute",
    "NONAC": "inpatient non-acute",
    "OBSENC": "observation encounter",
    "PRENC": "pre-admission",
    "SS": "short stay",
    "VR": "virtual",
}

# CPT code system OID
CPT_CODE_SYSTEM = "2.16.840.1.113883.6.12"

# Map discharge disposition codes (HL7 Table 0112) to FHIR
DISCHARGE_DISPOSITION_TO_FHIR = {
    "01": "home",
    "02": "other-hcf",
    "03": "snf",
    "04": "aama",
    "05": "oth",
    "06": "exp",
    "07": "hosp",
}

# Map C-CDA ParticipationFunction codes (OID 2.16.840.1.113883.5.88) to FHIR ParticipationType codes
# Reference: docs/mapping/09-participations.md lines 217-232
# Reference: https://phinvads.cdc.gov/vads/ViewCodeSystem.action?id=2.16.840.1.113883.5.88
# Reference: http://hl7.org/fhir/R4/v3/ParticipationType/cs.html
#
# Note: Some codes are context-specific:
# - For Encounter.participant.type: Can use ADM, DIS, REF (broader value set)
# - For Procedure.performer.function: Limited to performer-function value set (PPRF, SPRF, ATND, etc.)
PARTICIPATION_FUNCTION_CODE_MAP = {
    # C-CDA Code: FHIR Code - Description
    "ADMPHYS": "ADM",       # Admitting Physician → admitter (Encounter only)
    "ANRS": "SPRF",         # Anesthesia Nurse → secondary performer
    "ANEST": "SPRF",        # Anesthesist → secondary performer (ANEST not in FHIR v3-ParticipationType)
    "ATTPHYS": "ATND",      # Attending Physician → attender
    "DISPHYS": "DIS",       # Discharging Physician → discharger (Encounter only)
    "FASST": "SPRF",        # First Assistant Surgeon → secondary performer
    "MDWF": "PPRF",         # Midwife → primary performer
    "NASST": "SPRF",        # Nurse Assistant → secondary performer
    "PCP": "PPRF",          # Primary Care Physician → primary performer
    "PRISURG": "PPRF",      # Primary Surgeon → primary performer
    "RNDPHYS": "ATND",      # Rounding Physician → attender
    "SNRS": "SPRF",         # Scrub Nurse → secondary performer
    "SASST": "SPRF",        # Second Assistant Surgeon → secondary performer
    "TASST": "SPRF",        # Third Assistant Surgeon → secondary performer
}

# Backward compatibility alias for encounter-specific usage
ENCOUNTER_PARTICIPANT_FUNCTION_CODE_MAP = PARTICIPATION_FUNCTION_CODE_MAP


def map_cpt_to_actcode(cpt_code: str) -> str | None:
    """Map CPT encounter code to V3 ActCode.

    Per C-CDA on FHIR IG specification (docs/mapping/08-encounter.md lines 77-86):
    - 99201-99215: Outpatient visits → AMB (ambulatory)
    - 99221-99223: Initial hospital care → IMP (inpatient encounter)
    - 99281-99285: Emergency department visits → EMER (emergency)
    - 99341-99350: Home visits → HH (home health)

    Args:
        cpt_code: The CPT code as a string (e.g., "99213")

    Returns:
        The corresponding V3 ActCode or None if no mapping exists

    Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html
    """
    if not cpt_code:
        return None

    try:
        code_int = int(cpt_code)
    except (ValueError, TypeError):
        return None

    # Outpatient visits (99201-99215)
    if 99201 <= code_int <= 99215:
        return "AMB"

    # Initial hospital care (99221-99223)
    elif 99221 <= code_int <= 99223:
        return "IMP"

    # Emergency department visits (99281-99285)
    elif 99281 <= code_int <= 99285:
        return "EMER"

    # Home visits (99341-99350)
    elif 99341 <= code_int <= 99350:
        return "HH"

    # No mapping found
    return None


# Map C-CDA Note Activity statusCode to FHIR DocumentReference status
DOCUMENT_REFERENCE_STATUS_TO_FHIR = {
    "completed": FHIRCodes.DocumentReferenceStatus.CURRENT,
    "active": FHIRCodes.DocumentReferenceStatus.CURRENT,
    "aborted": FHIRCodes.DocumentReferenceStatus.ENTERED_IN_ERROR,
    "cancelled": FHIRCodes.DocumentReferenceStatus.ENTERED_IN_ERROR,
}

# LOINC code for Vital signs panel
VITAL_SIGNS_PANEL_CODE = "85353-1"
VITAL_SIGNS_PANEL_DISPLAY = "Vital signs, weight, height, head circumference, oxygen saturation and BMI panel"

# LOINC codes for Blood Pressure
BP_PANEL_CODE = "85354-9"
BP_PANEL_DISPLAY = "Blood pressure panel with all children optional"
BP_SYSTOLIC_CODE = "8480-6"
BP_SYSTOLIC_DISPLAY = "Systolic blood pressure"
BP_DIASTOLIC_CODE = "8462-4"
BP_DIASTOLIC_DISPLAY = "Diastolic blood pressure"

# LOINC codes for Pulse Oximetry
PULSE_OX_PRIMARY_CODE = "59408-5"
PULSE_OX_PRIMARY_DISPLAY = "Oxygen saturation in Arterial blood by Pulse oximetry"
PULSE_OX_ALT_CODE = "2708-6"
PULSE_OX_ALT_DISPLAY = "Oxygen saturation in Arterial blood"
O2_FLOW_RATE_CODE = "3151-8"
O2_FLOW_RATE_DISPLAY = "Inhaled oxygen flow rate"
O2_CONCENTRATION_CODE = "3150-0"
O2_CONCENTRATION_DISPLAY = "Inhaled oxygen concentration"

# =============================================================================
# Section Empty Reason Mappings
# =============================================================================

# Map C-CDA section nullFlavor to FHIR Composition.section.emptyReason
# Reference: http://terminology.hl7.org/CodeSystem/list-empty-reason
# C-CDA nullFlavor values per: http://terminology.hl7.org/CodeSystem/v3-NullFlavor
#
# IMPORTANT: This is a custom mapping as no official HL7 guidance exists for
# mapping section-level nullFlavor to emptyReason. The official C-CDA on FHIR
# ConceptMap (CF-NullFlavorDataAbsentReason) maps nullFlavor to data-absent-reason
# for element values, not section-level empty reasons.
#
# Semantic mapping choices:
# - Conservative approach: Most unmappable values → "unavailable"
# - Only map when semantics clearly align between the two value sets
NULL_FLAVOR_TO_EMPTY_REASON = {
    "NASK": "notasked",  # Not asked → Not Asked (exact semantic match)
    "NAV": "unavailable",  # Temporarily unavailable → Unavailable (exact semantic match)
    "UNK": "unavailable",  # Unknown → Unavailable (conservative: we don't know if items exist)
    "MSK": "withheld",  # Masked → Information Withheld (exact semantic match for privacy)
    "NA": "unavailable",  # Not applicable → Unavailable (conservative: concept doesn't apply)
    "NI": "unavailable",  # No information → Unavailable (most common section nullFlavor)
    "OTH": "unavailable",  # Other → Unavailable (conservative fallback)
    "ASKU": "unavailable",  # Asked but unknown → Unavailable (patient was asked but didn't know)
    "NP": "unavailable",  # Not present → Unavailable (conservative)
    "TRC": "unavailable",  # Trace amount → Unavailable (not semantically applicable for sections)
}

# =============================================================================
# Element-Level Data Absent Reason Mappings
# =============================================================================

# Map C-CDA element nullFlavor to FHIR data-absent-reason extension
# Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-NullFlavorDataAbsentReason.html
# Reference: http://hl7.org/fhir/R4/extension-data-absent-reason.html
# Reference: http://terminology.hl7.org/CodeSystem/v3-NullFlavor
# Reference: http://terminology.hl7.org/CodeSystem/data-absent-reason
#
# Official C-CDA on FHIR IG ConceptMap for element-level nullFlavor mapping.
# Per US Core guidance: when an element is not required, omit the element rather
# than include data-absent-reason. This mapping applies when the element IS required
# and has a nullFlavor in C-CDA.
#
# Mapping relationship types from ConceptMap:
# - "equivalent": Direct 1:1 mapping
# - "wider": C-CDA concept maps to a broader FHIR concept
# - "relatedto": Loose semantic relationship
NULL_FLAVOR_TO_DATA_ABSENT_REASON = {
    "UNK": "unknown",  # Unknown (maps to wider concept)
    "ASKU": "asked-unknown",  # Asked but unknown (equivalent)
    "NAV": "temp-unknown",  # Temporarily unavailable (equivalent)
    "NASK": "not-asked",  # Not asked (equivalent)
    "NI": "unknown",  # No information → unknown (when required per US Core; loose mapping)
    "NA": "not-applicable",  # Not applicable (equivalent)
    "MSK": "masked",  # Masked (equivalent)
    "OTH": "unsupported",  # Other (maps to wider concept)
    "NINF": "negative-infinity",  # Negative infinity (equivalent)
    "PINF": "positive-infinity",  # Positive infinity (equivalent)
    "TRC": "unsupported",  # Trace → unsupported (maps to wider concept)
    "NP": "unknown",  # Not present → unknown (maps to wider concept)
}

# =============================================================================
# Provenance Mappings
# =============================================================================

# Map C-CDA role/function codes to FHIR Provenance agent type
CCDA_ROLE_TO_PROVENANCE_AGENT = {
    "AUT": FHIRCodes.ProvenanceAgent.AUTHOR,
    "PRF": FHIRCodes.ProvenanceAgent.PERFORMER,
    "INF": FHIRCodes.ProvenanceAgent.INFORMANT,
    "ENT": FHIRCodes.ProvenanceAgent.ENTERER,
    "LA": FHIRCodes.ProvenanceAgent.ATTESTER,
    "CST": FHIRCodes.ProvenanceAgent.CUSTODIAN,
}

# =============================================================================
# SDOH Category Mappings
# =============================================================================

# Map LOINC codes to SDOH categories
# Based on US Core Common SDOH Assessments and SDOHCC ValueSet
# Reference: https://www.hl7.org/fhir/us/core/ValueSet-us-core-common-sdoh-assessments.html
LOINC_TO_SDOH_CATEGORY = {
    # Food Insecurity
    "88121-9": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Hunger Vital Sign [HVS]
    "88124-3": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Food insecurity risk [HVS]
    "88123-5": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Food didn't last
    "88122-7": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Worried food would run out
    "103982-5": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Do you have food insecurity
    "99122-7": FHIRCodes.SDOHCategory.FOOD_INSECURITY,  # Food insecurity - worried food will run out

    # Housing Instability
    "93033-9": FHIRCodes.SDOHCategory.HOUSING_INSTABILITY,  # Worried about losing housing [PRAPARE]
    "71802-3": FHIRCodes.SDOHCategory.HOUSING_INSTABILITY,  # Housing status
    "103983-3": FHIRCodes.SDOHCategory.HOUSING_INSTABILITY,  # Do you have housing insecurity

    # Inadequate Housing
    "93026-3": FHIRCodes.SDOHCategory.INADEQUATE_HOUSING,  # Feel physically/emotionally safe at home

    # Utility Insecurity
    "96779-4": FHIRCodes.SDOHCategory.UTILITY_INSECURITY,  # Utility company threatened shut off

    # Employment Status
    "67875-5": FHIRCodes.SDOHCategory.EMPLOYMENT_STATUS,  # Employment status - current
    "96780-2": FHIRCodes.SDOHCategory.EMPLOYMENT_STATUS,  # Wants help finding/keeping job
    "93035-4": FHIRCodes.SDOHCategory.EMPLOYMENT_STATUS,  # Season/migrant farm work

    # Transportation Insecurity
    "93030-5": FHIRCodes.SDOHCategory.TRANSPORTATION_INSECURITY,  # Lack of transportation kept from appointments

    # Financial Insecurity
    "76513-1": FHIRCodes.SDOHCategory.FINANCIAL_INSECURITY,  # How hard to pay for basics
    "63586-2": FHIRCodes.SDOHCategory.FINANCIAL_INSECURITY,  # Total family income estimate

    # Incarceration Status
    "93028-9": FHIRCodes.SDOHCategory.INCARCERATION_STATUS,  # Spent >2 nights in jail/prison

    # Legal
    "93677-3": FHIRCodes.SDOHCategory.SDOH_CATEGORY_UNSPECIFIED,  # Need help with legal issues (no specific legal category)

    # Social Connection
    "93029-7": FHIRCodes.SDOHCategory.SOCIAL_CONNECTION,  # How often see/talk to people you care about
    "93159-2": FHIRCodes.SDOHCategory.SOCIAL_CONNECTION,  # Feel lonely or isolated

    # Stress
    "93038-8": FHIRCodes.SDOHCategory.STRESS,  # Stress level
    "44250-9": FHIRCodes.SDOHCategory.STRESS,  # Little interest or pleasure
    "44255-8": FHIRCodes.SDOHCategory.STRESS,  # Feeling down/depressed/hopeless

    # Educational Attainment
    "82589-3": FHIRCodes.SDOHCategory.EDUCATIONAL_ATTAINMENT,  # Highest level of education
    "96782-8": FHIRCodes.SDOHCategory.EDUCATIONAL_ATTAINMENT,  # Wants help with school/training

    # Material Hardship
    "93031-3": FHIRCodes.SDOHCategory.MATERIAL_HARDSHIP,  # Unable to get necessities
    "96781-0": FHIRCodes.SDOHCategory.MATERIAL_HARDSHIP,  # Able to get help with daily activities
    "69861-3": FHIRCodes.SDOHCategory.MATERIAL_HARDSHIP,  # Difficulty with daily activities (physical/mental)
    "69858-9": FHIRCodes.SDOHCategory.MATERIAL_HARDSHIP,  # Serious difficulty (physical/mental)

    # Language Access
    "54899-0": FHIRCodes.SDOHCategory.LANGUAGE_ACCESS,  # Preferred language
    "97027-7": FHIRCodes.SDOHCategory.LANGUAGE_ACCESS,  # Speaks language other than English at home

    # Health Insurance Coverage Status
    "76437-3": FHIRCodes.SDOHCategory.HEALTH_INSURANCE_COVERAGE_STATUS,  # Primary insurance

    # Veteran Status
    "93034-7": FHIRCodes.SDOHCategory.VETERAN_STATUS,  # Discharged from armed forces

    # Intimate Partner Violence
    "76501-6": FHIRCodes.SDOHCategory.INTIMATE_PARTNER_VIOLENCE,  # Afraid of partner/ex-partner
    "95618-5": FHIRCodes.SDOHCategory.INTIMATE_PARTNER_VIOLENCE,  # Physically hurt you [HITS]
}

# Display names for SDOH categories
SDOH_CATEGORY_DISPLAY = {
    FHIRCodes.SDOHCategory.FOOD_INSECURITY: "Food Insecurity",
    FHIRCodes.SDOHCategory.HOUSING_INSTABILITY: "Housing Instability",
    FHIRCodes.SDOHCategory.HOMELESSNESS: "Homelessness",
    FHIRCodes.SDOHCategory.INADEQUATE_HOUSING: "Inadequate Housing",
    FHIRCodes.SDOHCategory.TRANSPORTATION_INSECURITY: "Transportation Insecurity",
    FHIRCodes.SDOHCategory.FINANCIAL_INSECURITY: "Financial Insecurity",
    FHIRCodes.SDOHCategory.MATERIAL_HARDSHIP: "Material Hardship",
    FHIRCodes.SDOHCategory.EDUCATIONAL_ATTAINMENT: "Educational Attainment",
    FHIRCodes.SDOHCategory.EMPLOYMENT_STATUS: "Employment Status",
    FHIRCodes.SDOHCategory.VETERAN_STATUS: "Veteran Status",
    FHIRCodes.SDOHCategory.STRESS: "Stress",
    FHIRCodes.SDOHCategory.SOCIAL_CONNECTION: "Social Connection",
    FHIRCodes.SDOHCategory.INTIMATE_PARTNER_VIOLENCE: "Intimate Partner Violence",
    FHIRCodes.SDOHCategory.ELDER_ABUSE: "Elder Abuse",
    FHIRCodes.SDOHCategory.PERSONAL_HEALTH_LITERACY: "Personal Health Literacy",
    FHIRCodes.SDOHCategory.HEALTH_INSURANCE_COVERAGE_STATUS: "Health Insurance Coverage Status",
    FHIRCodes.SDOHCategory.MEDICAL_COST_BURDEN: "Medical Cost Burden",
    FHIRCodes.SDOHCategory.DIGITAL_LITERACY: "Digital Literacy",
    FHIRCodes.SDOHCategory.DIGITAL_ACCESS: "Digital Access",
    FHIRCodes.SDOHCategory.UTILITY_INSECURITY: "Utility Insecurity",
    FHIRCodes.SDOHCategory.INCARCERATION_STATUS: "Incarceration Status",
    FHIRCodes.SDOHCategory.LANGUAGE_ACCESS: "Language Status",
    FHIRCodes.SDOHCategory.SDOH_CATEGORY_UNSPECIFIED: "SDOH Category Unspecified",
}


