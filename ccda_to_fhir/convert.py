"""Main conversion entry point for C-CDA to FHIR conversion."""

from __future__ import annotations

from fhir_core.fhirabstractmodel import FHIRAbstractModel

from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.ccda.models.datatypes import II
from ccda_to_fhir.ccda.models.section import StructuredBody
from ccda_to_fhir.ccda.parser import parse_ccda
from ccda_to_fhir.constants import PARTICIPATION_FUNCTION_CODE_MAP, TemplateIds
from ccda_to_fhir.exceptions import CCDAConversionError
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import (
    ConversionMetadata,
    ConversionResult,
    FHIRResourceDict,
    JSONObject,
)
from ccda_to_fhir.validation import FHIRValidator
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.careplan import CarePlan
from fhir.resources.R4B.careteam import CareTeam
from fhir.resources.R4B.composition import Composition
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.device import Device
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.documentreference import DocumentReference
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.goal import Goal
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.location import Location
from fhir.resources.R4B.medication import Medication
from fhir.resources.R4B.medicationdispense import MedicationDispense
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.medicationstatement import MedicationStatement
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.procedure import Procedure
from fhir.resources.R4B.provenance import Provenance
from fhir.resources.R4B.relatedperson import RelatedPerson
from fhir.resources.R4B.servicerequest import ServiceRequest

from .converters.allergy_intolerance import convert_allergy_concern_act
from .converters.author_extractor import AuthorExtractor, AuthorInfo
from .converters.careplan import CarePlanConverter
from .converters.careteam import CareTeamConverter
from .converters.code_systems import CodeSystemMapper
from .converters.composition import CompositionConverter
from .converters.condition import ConditionConverter, convert_problem_concern_act
from .converters.device import DeviceConverter
from .converters.diagnostic_report import DiagnosticReportConverter
from .converters.document_reference import DocumentReferenceConverter
from .converters.encounter import EncounterConverter
from .converters.goal import GoalConverter
from .converters.immunization import convert_immunization_activity
from .converters.medication_dispense import (
    clear_medication_dispense_registry,
    get_medication_dispense_resources,
)
from .converters.medication_request import (
    clear_medication_registry,
    convert_medication_activity,
    get_medication_resources,
)
from .converters.medication_statement import convert_medication_statement
from .converters.note_activity import convert_note_activity
from .converters.observation import ObservationConverter
from .converters.organization import OrganizationConverter
from .converters.patient import PatientConverter
from .converters.practitioner import PractitionerConverter
from .converters.practitioner_role import PractitionerRoleConverter
from .converters.procedure import ProcedureConverter
from .converters.provenance import ProvenanceConverter
from .converters.references import ReferenceRegistry
from .converters.section_processor import SectionConfig, SectionProcessor
from .converters.service_request import ServiceRequestConverter

logger = get_logger(__name__)

# Mapping of FHIR resource types to their fhir.resources classes for validation
RESOURCE_TYPE_MAPPING: dict[str, type[FHIRAbstractModel]] = {
    "Patient": Patient,
    "Practitioner": Practitioner,
    "PractitionerRole": PractitionerRole,
    "Organization": Organization,
    "RelatedPerson": RelatedPerson,
    "Device": Device,
    "DocumentReference": DocumentReference,
    "Condition": Condition,
    "AllergyIntolerance": AllergyIntolerance,
    "Medication": Medication,
    "MedicationDispense": MedicationDispense,
    "MedicationRequest": MedicationRequest,
    "MedicationStatement": MedicationStatement,
    "Immunization": Immunization,
    "Location": Location,
    "Observation": Observation,
    "DiagnosticReport": DiagnosticReport,
    "Procedure": Procedure,
    "ServiceRequest": ServiceRequest,
    "Encounter": Encounter,
    "Composition": Composition,
    "Provenance": Provenance,
    "Goal": Goal,
    "CarePlan": CarePlan,
    "CareTeam": CareTeam,
}


def convert_careteam_organizer(
    organizer,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> list[FHIRResourceDict]:
    """Convert a Care Team Organizer to FHIR CareTeam and related resources.

    Args:
        organizer: The Care Team Organizer
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing metadata
        section: The C-CDA Section containing this care team (for narrative)
        reference_registry: Reference registry for patient reference

    Returns:
        List of FHIR resources: CareTeam, Practitioner, PractitionerRole, Organization
    """
    # Get patient reference from registry
    if not reference_registry:
        raise ValueError("Reference registry required for CareTeam conversion")

    patient_reference = reference_registry.get_patient_reference()

    converter = CareTeamConverter(
        patient_reference=patient_reference,
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )

    try:
        careteam = converter.convert(organizer)

        # Store metadata if callback provided
        if metadata_callback and careteam.get("id"):
            metadata_callback(
                resource_type="CareTeam",
                resource_id=careteam["id"],
                ccda_element=organizer,
                concern_act=None,
            )

        # Collect all resources (CareTeam + related resources)
        resources = [careteam]
        resources.extend(converter.get_related_resources())

        return resources
    except Exception:
        logger.error("Error converting care team organizer", exc_info=True)
        raise


def convert_medication(
    substance_admin,
    code_system_mapper=None,
    metadata_callback=None,
    section=None,
    reference_registry=None,
) -> FHIRResourceDict:
    """Route medication activity to appropriate converter based on moodCode.

    Per FHIR/C-CDA standards:
    - moodCode="EVN" (event/historical) → MedicationStatement
    - moodCode="INT", "RQO", "PRMS", "PRP" → MedicationRequest
    - negationInd="true" → Always MedicationRequest (with doNotPerform)

    Args:
        substance_admin: The SubstanceAdministration (Medication Activity)
        code_system_mapper: Optional code system mapper
        metadata_callback: Optional callback for storing author metadata
        section: The C-CDA Section containing this medication (for narrative)

    Returns:
        FHIR MedicationRequest or MedicationStatement resource
    """
    mood_code = substance_admin.mood_code if hasattr(substance_admin, 'mood_code') else None
    negation_ind = substance_admin.negation_ind if hasattr(substance_admin, 'negation_ind') else False

    # Negated medications always use MedicationRequest with doNotPerform
    if negation_ind:
        return convert_medication_activity(
            substance_admin,
            code_system_mapper=code_system_mapper,
            metadata_callback=metadata_callback,
            section=section,
            reference_registry=reference_registry,
        )

    # Route based on moodCode
    if mood_code == "EVN":
        # Historical/actual medication use → MedicationStatement
        return convert_medication_statement(
            substance_admin,
            code_system_mapper=code_system_mapper,
            metadata_callback=metadata_callback,
            section=section,
            reference_registry=reference_registry,
        )
    else:
        # Intent/order/proposal → MedicationRequest
        return convert_medication_activity(
            substance_admin,
            code_system_mapper=code_system_mapper,
            metadata_callback=metadata_callback,
            section=section,
            reference_registry=reference_registry,
        )


class DocumentConverter:
    """Converts a C-CDA document to a FHIR Bundle.

    This is the main converter class that orchestrates the conversion of
    a complete C-CDA document to a FHIR Bundle with all resources.
    """

    def __init__(
        self,
        code_system_mapper: CodeSystemMapper | None = None,
                original_xml: str | bytes | None = None,
        enable_validation: bool = False,
        strict_validation: bool = False,
    ):
        """Initialize the document converter.

        Args:
            code_system_mapper: Optional code system mapper
            original_xml: Optional original C-CDA XML for DocumentReference content
            enable_validation: If True, validate FHIR resources during conversion
            strict_validation: If True, raise exceptions on validation failures
        """
        self.code_system_mapper = code_system_mapper or CodeSystemMapper()
        self.original_xml = original_xml

        # Reference registry for tracking and validating resource references
        self.reference_registry = ReferenceRegistry()

        # FHIR validation settings
        self.enable_validation = enable_validation
        self.validator = FHIRValidator(strict=strict_validation) if enable_validation else None

        # Author metadata storage for Provenance generation
        self._author_metadata: dict[str, list[AuthorInfo]] = {}
        self.author_extractor = AuthorExtractor()
        self.provenance_converter = ProvenanceConverter(
            code_system_mapper=self.code_system_mapper
        )

        # Informant metadata storage for RelatedPerson/Practitioner generation
        self._informant_metadata: dict[str, list] = {}
        from .converters.informant_extractor import InformantExtractor
        self.informant_extractor = InformantExtractor()

        # Initialize individual resource converters
        self.patient_converter = PatientConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.document_reference_converter = DocumentReferenceConverter(
            code_system_mapper=self.code_system_mapper,
            original_xml=original_xml,
            reference_registry=self.reference_registry,
        )
        self.observation_converter = ObservationConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.diagnostic_report_converter = DiagnosticReportConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.procedure_converter = ProcedureConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.service_request_converter = ServiceRequestConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.encounter_converter = EncounterConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.goal_converter = GoalConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.practitioner_converter = PractitionerConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.practitioner_role_converter = PractitionerRoleConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.device_converter = DeviceConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.organization_converter = OrganizationConverter(
            code_system_mapper=self.code_system_mapper
        )

        # Initialize section processors for generic extraction
        self._init_section_processors()

    def _init_section_processors(self) -> None:
        """Initialize section processors for extracting resources from sections."""
        # Conditions (Problem Concern Acts)
        self.condition_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PROBLEM_CONCERN_ACT,
                entry_type="act",
                converter=convert_problem_concern_act,
                error_message="problem concern act",
                include_section_code=True,
            )
        )

        # Allergies (Allergy Concern Acts)
        self.allergy_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.ALLERGY_CONCERN_ACT,
                entry_type="act",
                converter=convert_allergy_concern_act,
                error_message="allergy concern act",
                include_section_code=False,
            )
        )

        # Medications (Medication Activities)
        # Routes to MedicationRequest or MedicationStatement based on moodCode
        self.medication_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.MEDICATION_ACTIVITY,
                entry_type="substance_administration",
                converter=convert_medication,
                error_message="medication activity",
                include_section_code=False,
            )
        )

        # Immunizations (Immunization Activities)
        self.immunization_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.IMMUNIZATION_ACTIVITY,
                entry_type="substance_administration",
                converter=convert_immunization_activity,
                error_message="immunization activity",
                include_section_code=False,
            )
        )

        # Procedures (Procedure Activity Procedures)
        self.procedure_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PROCEDURE_ACTIVITY_PROCEDURE,
                entry_type="procedure",
                converter=self.procedure_converter.convert,
                error_message="procedure",
                include_section_code=False,
            )
        )

        # Procedure Activity Observations (also map to FHIR Procedure)
        self.procedure_observation_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PROCEDURE_ACTIVITY_OBSERVATION,
                entry_type="observation",
                converter=self.procedure_converter.convert,
                error_message="procedure observation",
                include_section_code=False,
            )
        )

        # Procedure Activity Acts (also map to FHIR Procedure)
        self.procedure_act_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PROCEDURE_ACTIVITY_ACT,
                entry_type="act",
                converter=self.procedure_converter.convert,
                error_message="procedure act",
                include_section_code=False,
            )
        )

        # Encounters (Encounter Activities)
        self.encounter_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.ENCOUNTER_ACTIVITY,
                entry_type="encounter",
                converter=self.encounter_converter.convert,
                error_message="encounter",
                include_section_code=False,
            )
        )

        # Notes (Note Activities)
        self.note_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.NOTE_ACTIVITY,
                entry_type="act",
                converter=convert_note_activity,
                error_message="note activity",
                include_section_code=False,
            )
        )

        # Vital Signs (Vital Signs Organizers)
        self.vital_signs_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.VITAL_SIGNS_ORGANIZER,
                entry_type="organizer",
                converter=self.observation_converter.convert_vital_signs_organizer,
                error_message="vital signs organizer",
                include_section_code=False,
            )
        )

        # Results (Result Organizers)
        self.results_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.RESULT_ORGANIZER,
                entry_type="organizer",
                converter=self.diagnostic_report_converter.convert,
                error_message="result organizer",
                include_section_code=False,
            )
        )

        # Smoking Status Observations
        self.smoking_status_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.SMOKING_STATUS_OBSERVATION,
                entry_type="observation",
                converter=self.observation_converter.convert,
                error_message="smoking status observation",
                include_section_code=False,
            )
        )

        # Social History Observations (general)
        self.social_history_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.SOCIAL_HISTORY_OBSERVATION,
                entry_type="observation",
                converter=self.observation_converter.convert,
                error_message="social history observation",
                include_section_code=False,
            )
        )

        # Goals (Goal Observations)
        self.goal_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.GOAL_OBSERVATION,
                entry_type="observation",
                converter=self.goal_converter.convert,
                error_message="goal observation",
                include_section_code=False,
            )
        )

        # Service Requests (Planned Procedures)
        self.planned_procedure_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PLANNED_PROCEDURE,
                entry_type="procedure",
                converter=self.service_request_converter.convert,
                error_message="planned procedure",
                include_section_code=False,
            )
        )

        # Service Requests (Planned Acts)
        self.planned_act_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.PLANNED_ACT,
                entry_type="act",
                converter=self.service_request_converter.convert,
                error_message="planned act",
                include_section_code=False,
            )
        )

        # Care Teams (Care Team Organizers)
        self.careteam_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.CARE_TEAM_ORGANIZER,
                entry_type="organizer",
                converter=convert_careteam_organizer,
                error_message="care team organizer",
                include_section_code=False,
            )
        )

    def _create_bundle_identifier(self, doc_id: II) -> JSONObject:
        """Create Bundle identifier from ClinicalDocument ID.

        Args:
            doc_id: Document identifier (II element)

        Returns:
            FHIR Identifier
        """
        identifier: JSONObject = {
            "system": f"urn:oid:{doc_id.root}",
        }

        if doc_id.extension:
            identifier["value"] = doc_id.extension

        return identifier

    def _convert_bundle_timestamp(self, ccda_datetime: str | None) -> str | None:
        """Convert C-CDA datetime to FHIR instant (timestamp).

        FHIR instant type requires full timestamp with timezone.
        Per FHIR spec: instant = YYYY-MM-DDThh:mm:ss.sss+zz:zz (timezone REQUIRED)

        If C-CDA effectiveTime lacks timezone, Bundle.timestamp is omitted
        (it's optional 0..1 per FHIR spec) rather than manufacturing potentially
        incorrect timezone data.

        Args:
            ccda_datetime: C-CDA datetime string (YYYYMMDDHHmmss±ZZZZ)

        Returns:
            FHIR instant (ISO 8601 with timezone) or None if timezone missing

        Examples:
            >>> _convert_bundle_timestamp("20231215120000-0500")
            '2023-12-15T12:00:00-05:00'
            >>> _convert_bundle_timestamp("20231215120000")  # No timezone
            None
            >>> _convert_bundle_timestamp("20231215")  # Date only
            None
        """
        from datetime import datetime

        if not ccda_datetime:
            return None

        try:
            ccda_datetime = ccda_datetime.strip()

            # Extract timezone
            tz_start = -1
            for i, char in enumerate(ccda_datetime):
                if char in ('+', '-') and i > 8:
                    tz_start = i
                    break

            # instant type REQUIRES timezone - return None if missing
            if tz_start <= 0:
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.info(
                    f"Bundle.timestamp omitted: C-CDA effectiveTime '{ccda_datetime}' lacks timezone. "
                    f"FHIR instant type requires timezone."
                )
                return None

            numeric_part = ccda_datetime[:tz_start]
            tz_part = ccda_datetime[tz_start:]

            # Validate timezone format
            if len(tz_part) < 5:
                return None

            # Only support full datetime (14 digits)
            if not numeric_part.isdigit() or len(numeric_part) != 14:
                return None

            # Parse datetime
            dt = datetime.strptime(numeric_part, "%Y%m%d%H%M%S")

            # Validate year range
            if not 1800 <= dt.year <= 2200:
                return None

            # Format timezone
            tz_sign = tz_part[0]
            tz_hours = tz_part[1:3]
            tz_mins = tz_part[3:5]

            tz_h = int(tz_hours)
            tz_m = int(tz_mins)

            if not (0 <= tz_h <= 14 and 0 <= tz_m <= 59):
                return None

            # Format as FHIR instant
            return (
                f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}T"
                f"{dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"
                f"{tz_sign}{tz_hours}:{tz_mins}"
            )

        except (ValueError, IndexError):
            from ccda_to_fhir.logging_config import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Failed to convert C-CDA datetime to FHIR instant: {ccda_datetime}")
            return None

    def _validate_resource(self, resource: FHIRResourceDict) -> bool:
        """Validate a FHIR resource if validation is enabled.

        Args:
            resource: FHIR resource dictionary to validate

        Returns:
            True if validation passed or is disabled, False if validation failed
        """
        if not self.enable_validation or not self.validator:
            return True

        resource_type = resource.get("resourceType")
        if not resource_type:
            logger.warning("Resource missing resourceType field, skipping validation")
            return False

        # Get the corresponding FHIR resource class
        resource_class = RESOURCE_TYPE_MAPPING.get(resource_type)
        if not resource_class:
            logger.debug(
                f"No validation mapping for {resource_type}, skipping validation"
            )
            return True

        # Validate the resource
        validated = self.validator.validate_resource(resource, resource_class)
        return validated is not None

    def get_validation_stats(self) -> dict[str, int]:
        """Get validation statistics.

        Returns:
            Dictionary with validation stats (validated, passed, failed, warnings)
        """
        if self.validator:
            return self.validator.get_stats()
        return {"validated": 0, "passed": 0, "failed": 0, "warnings": 0}

    def convert(self, ccda_doc: ClinicalDocument) -> ConversionResult:
        """Convert a C-CDA document to a FHIR Bundle with metadata.

        Args:
            ccda_doc: Parsed C-CDA document (ClinicalDocument model)

        Returns:
            ConversionResult with bundle and metadata about processing
        """
        # Clear medication registries at start of conversion
        clear_medication_registry()
        clear_medication_dispense_registry()

        # Reset ID cache for this document to ensure consistency within document
        from ccda_to_fhir.id_generator import reset_id_cache
        reset_id_cache()

        # Initialize conversion metadata
        metadata: ConversionMetadata = {
            "processed_templates": {},
            "skipped_templates": {},
            "errors": [],
        }

        resources = []
        # Section→resource mapping for Composition.section[].entry references
        section_resource_map: dict[str, list[FHIRResourceDict]] = {}

        # Convert Patient (from recordTarget)
        # Patient is extracted first so we can replace placeholders in clinical resources
        if ccda_doc.record_target:
            for record_target in ccda_doc.record_target:
                try:
                    patient = self.patient_converter.convert(record_target)

                    # Extract birth sex and gender identity extensions from social history
                    if ccda_doc.component and ccda_doc.component.structured_body:
                        social_history_extensions = (
                            self._extract_patient_extensions_from_social_history(
                                ccda_doc.component.structured_body
                            )
                        )
                        if social_history_extensions:
                            if "extension" not in patient:
                                patient["extension"] = []
                            patient["extension"].extend(social_history_extensions)

                    # Validate the patient resource
                    if self._validate_resource(patient):
                        resources.append(patient)
                        self.reference_registry.register_resource(patient)
                        # Store patient ID for RelatedPerson references
                        if "id" in patient:
                            self._patient_id = patient["id"]

                        # Convert providerOrganization to Organization resource
                        if (record_target.patient_role and
                            record_target.patient_role.provider_organization):
                            try:
                                provider_org = record_target.patient_role.provider_organization
                                organization = self.organization_converter.convert(provider_org)

                                # Validate and add Organization to bundle
                                if self._validate_resource(organization):
                                    resources.append(organization)
                                    self.reference_registry.register_resource(organization)

                                    # Update Patient.managingOrganization with proper reference
                                    if "id" in organization:
                                        # Preserve display from PatientConverter if it exists
                                        org_display = None
                                        if "managingOrganization" in patient:
                                            org_display = patient["managingOrganization"].get("display")

                                        # Create reference with display
                                        patient["managingOrganization"] = {
                                            "reference": f"Organization/{organization['id']}"
                                        }
                                        if org_display:
                                            patient["managingOrganization"]["display"] = org_display
                                else:
                                    logger.warning(
                                        "Provider organization resource failed validation, skipping",
                                        resource_id=organization.get("id")
                                    )
                            except Exception as e:
                                logger.warning(
                                    f"Error converting provider organization: {e}",
                                    exc_info=True,
                                    extra={"error_type": type(e).__name__}
                                )
                    else:
                        logger.warning(
                            "Patient resource failed validation, skipping",
                            resource_id=patient.get("id")
                        )
                except CCDAConversionError as e:
                    # Expected conversion errors - log and continue
                    logger.error(
                        f"Error converting patient: {e}",
                        exc_info=True,
                        extra={"error_type": type(e).__name__}
                    )
                except (AttributeError, KeyError, TypeError) as e:
                    # Unexpected structural errors - log with warning
                    logger.warning(
                        f"Unexpected error in patient conversion - possible C-CDA structure issue: {e}",
                        exc_info=True,
                        extra={"error_type": type(e).__name__}
                    )

        # Convert Practitioners and Organizations (from document-level authors)
        if ccda_doc.author:
            practitioners_and_orgs = self._extract_practitioners_and_organizations(ccda_doc.author)
            resources.extend(practitioners_and_orgs)
            for resource in practitioners_and_orgs:
                self.reference_registry.register_resource(resource)

        # Process document-level informants
        if ccda_doc.informant:
            from .converters.informant_extractor import InformantInfo
            for informant in ccda_doc.informant:
                informant_info = InformantInfo(informant, context="document")
                # Store in a temporary list to process later with _generate_informant_resources
                # For now, manually handle document-level informants
                if informant_info.is_practitioner and informant_info.informant.assigned_entity:
                    try:
                        practitioner = self.practitioner_converter.convert(
                            informant_info.informant.assigned_entity
                        )
                        # Check if practitioner already exists (deduplication)
                        if not self.reference_registry.has_resource("Practitioner", practitioner['id']):
                            resources.append(practitioner)
                            self.reference_registry.register_resource(practitioner)
                    except Exception as e:
                        logger.error(f"Error converting document informant practitioner: {e}", exc_info=True)

                elif informant_info.is_related_person and informant_info.informant.related_entity:
                    try:
                        if not hasattr(self, "_patient_id"):
                            raise ValueError(
                                "Cannot create RelatedPerson: patient_id is required. "
                                "Patient must be processed before informants."
                            )
                        patient_id = self._patient_id
                        from .converters.related_person import RelatedPersonConverter
                        related_person_converter = RelatedPersonConverter(patient_id=patient_id)
                        related_person = related_person_converter.convert(
                            informant_info.informant.related_entity
                        )
                        resources.append(related_person)
                        self.reference_registry.register_resource(related_person)
                    except Exception as e:
                        logger.error(f"Error converting document informant related person: {e}", exc_info=True)

        # Convert Practitioner from legalAuthenticator
        if ccda_doc.legal_authenticator and ccda_doc.legal_authenticator.assigned_entity:
            try:
                practitioner = self.practitioner_converter.convert(
                    ccda_doc.legal_authenticator.assigned_entity
                )
                if self._validate_resource(practitioner):
                    resources.append(practitioner)
                    self.reference_registry.register_resource(practitioner)
            except Exception as e:
                logger.warning(
                    f"Error converting legal authenticator practitioner: {e}",
                    exc_info=True,
                    extra={"error_type": type(e).__name__}
                )

        # Convert Practitioner from dataEnterer
        if ccda_doc.data_enterer and ccda_doc.data_enterer.assigned_entity:
            try:
                practitioner = self.practitioner_converter.convert(
                    ccda_doc.data_enterer.assigned_entity
                )
                if self._validate_resource(practitioner):
                    resources.append(practitioner)
                    self.reference_registry.register_resource(practitioner)
            except Exception as e:
                logger.warning(
                    f"Error converting data enterer practitioner: {e}",
                    exc_info=True,
                    extra={"error_type": type(e).__name__}
                )

        # Convert custodian organization if present
        if ccda_doc.custodian:
            custodian_org = self._extract_custodian_organization(ccda_doc.custodian)
            if custodian_org:
                resources.append(custodian_org)
                self.reference_registry.register_resource(custodian_org)

        # Convert Practitioners from documentationOf/serviceEvent/performer
        # These represent clinicians who actually carried out clinical services
        # and are referenced in Composition.extension (PerformerExtension)
        if ccda_doc.documentation_of:
            for doc_of in ccda_doc.documentation_of:
                if doc_of.service_event and doc_of.service_event.performer:
                    for performer in doc_of.service_event.performer:
                        if performer.assigned_entity:
                            try:
                                practitioner = self.practitioner_converter.convert(
                                    performer.assigned_entity
                                )
                                # Check if practitioner already exists (deduplication)
                                practitioner_id = practitioner.get('id')
                                if practitioner_id and not self.reference_registry.has_resource("Practitioner", practitioner_id):
                                    if self._validate_resource(practitioner):
                                        resources.append(practitioner)
                                        self.reference_registry.register_resource(practitioner)
                            except Exception as e:
                                logger.error(
                                    f"Error converting documentationOf performer practitioner: {e}",
                                    exc_info=True
                                )

        # Convert DocumentReference (document metadata)
        try:
            doc_reference = self.document_reference_converter.convert(ccda_doc)

            # Validate DocumentReference
            if self._validate_resource(doc_reference):
                resources.append(doc_reference)
                self.reference_registry.register_resource(doc_reference)
            else:
                logger.warning(
                    "DocumentReference failed validation, skipping",
                    resource_id=doc_reference.get("id")
                )
        except CCDAConversionError as e:
            # Expected conversion errors - log and continue
            logger.error(
                f"Error converting document reference: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__}
            )
        except (AttributeError, KeyError, TypeError) as e:
            # Unexpected structural errors
            logger.warning(
                f"Unexpected error in document reference conversion: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__}
            )

        # Convert section-based resources and build section→resource mapping
        if ccda_doc.component and ccda_doc.component.structured_body:
            # Conditions (from Problem sections)
            conditions = self._extract_conditions(ccda_doc.component.structured_body, metadata)
            resources.extend(conditions)
            for condition in conditions:
                self.reference_registry.register_resource(condition)
            if conditions:
                section_resource_map[TemplateIds.PROBLEM_SECTION] = conditions

            # Allergies (from Allergy sections)
            allergies = self._extract_allergies(ccda_doc.component.structured_body, metadata)
            resources.extend(allergies)
            for allergy in allergies:
                self.reference_registry.register_resource(allergy)
            if allergies:
                section_resource_map[TemplateIds.ALLERGY_SECTION] = allergies

            # Medications (from Medications sections)
            medications = self._extract_medications(ccda_doc.component.structured_body, metadata)
            resources.extend(medications)
            for medication in medications:
                self.reference_registry.register_resource(medication)
            if medications:
                section_resource_map[TemplateIds.MEDICATIONS_SECTION] = medications

            # Immunizations (from Immunizations sections)
            immunizations = self._extract_immunizations(ccda_doc.component.structured_body, metadata)
            resources.extend(immunizations)
            for immunization in immunizations:
                self.reference_registry.register_resource(immunization)
            if immunizations:
                section_resource_map[TemplateIds.IMMUNIZATIONS_SECTION] = immunizations

            # Vital Signs (from Vital Signs sections)
            vital_signs = self._extract_vital_signs(ccda_doc.component.structured_body)
            resources.extend(vital_signs)
            for vital_sign in vital_signs:
                self.reference_registry.register_resource(vital_sign)
            if vital_signs:
                section_resource_map[TemplateIds.VITAL_SIGNS_SECTION] = vital_signs

            # Results (from Results sections)
            results = self._extract_results(ccda_doc.component.structured_body)
            resources.extend(results)
            for result in results:
                self.reference_registry.register_resource(result)
            if results:
                section_resource_map[TemplateIds.RESULTS_SECTION] = results

            # Social History (from Social History sections)
            social_history = self._extract_social_history(ccda_doc.component.structured_body)
            resources.extend(social_history)
            for history_item in social_history:
                self.reference_registry.register_resource(history_item)
            if social_history:
                section_resource_map[TemplateIds.SOCIAL_HISTORY_SECTION] = social_history

            # Goals (from Goals sections)
            goals = self._extract_goals(ccda_doc.component.structured_body, metadata)
            resources.extend(goals)
            for goal in goals:
                self.reference_registry.register_resource(goal)
            if goals:
                section_resource_map[TemplateIds.GOALS_SECTION] = goals

            # Care Teams (from Care Teams section)
            # Note: _extract_careteams returns CareTeam resources plus related
            # Practitioner, PractitionerRole, and Organization resources
            careteam_resources = self._extract_careteams(ccda_doc.component.structured_body, metadata)
            resources.extend(careteam_resources)

            # Register all resources and collect just CareTeams for section map
            careteams = []
            for resource in careteam_resources:
                self.reference_registry.register_resource(resource)
                if resource.get("resourceType") == "CareTeam":
                    careteams.append(resource)

            if careteams:
                section_resource_map[TemplateIds.CARE_TEAMS_SECTION] = careteams

            # Procedures (from Procedures sections)
            procedures = self._extract_procedures(ccda_doc.component.structured_body)
            resources.extend(procedures)
            for procedure in procedures:
                self.reference_registry.register_resource(procedure)
            if procedures:
                section_resource_map[TemplateIds.PROCEDURES_SECTION] = procedures

            # Process Interventions Section (for Care Plan documents)
            # These are converted to Procedure resources and registered so CarePlan can reference them
            intervention_procedures = self._process_interventions_section(
                ccda_doc.component.structured_body
            )
            resources.extend(intervention_procedures)
            for procedure in intervention_procedures:
                self.reference_registry.register_resource(procedure)

            # Process Outcomes Section (for Care Plan documents)
            # These are converted to Observation resources and registered so CarePlan can reference them
            outcome_observations = self._process_outcomes_section(
                ccda_doc.component.structured_body
            )
            resources.extend(outcome_observations)
            for observation in outcome_observations:
                self.reference_registry.register_resource(observation)

            # Service Requests (from Plan of Treatment sections)
            service_requests = self._extract_service_requests(
                ccda_doc.component.structured_body
            )
            resources.extend(service_requests)
            for service_request in service_requests:
                self.reference_registry.register_resource(service_request)
            if service_requests:
                section_resource_map[TemplateIds.PLAN_OF_TREATMENT_SECTION] = service_requests

            # Encounters (from Encounters sections)
            encounters = self._extract_encounters(ccda_doc.component.structured_body)

            # Also extract header encounter if present (componentOf.encompassingEncounter)
            # Deduplication: Only add if not already in body encounters
            header_encounter = self._extract_header_encounter(ccda_doc)
            if header_encounter:
                # Check if this encounter already exists in body encounters (by ID)
                header_id = header_encounter.get("id")
                duplicate_found = False

                if header_id:
                    for existing_enc in encounters:
                        # Case-insensitive comparison (body converter doesn't lowercase, but header does)
                        existing_id = existing_enc.get("id", "")
                        if existing_id.lower() == header_id.lower():
                            duplicate_found = True
                            logger.debug(
                                f"Header encounter {header_id} already exists in body - using body version"
                            )
                            break

                # Only add header encounter if it's not a duplicate
                if not duplicate_found:
                    encounters.append(header_encounter)
                    logger.debug(f"Added header encounter {header_id} to bundle")

                    # Store author metadata for header encounter
                    # Header encounters use document-level authors from the encompassingEncounter
                    if header_id and ccda_doc.component_of and ccda_doc.component_of.encompassing_encounter:
                        self._store_author_metadata(
                            resource_type="Encounter",
                            resource_id=header_id,
                            ccda_element=ccda_doc.component_of.encompassing_encounter,
                            concern_act=None,
                        )

            resources.extend(encounters)
            for encounter in encounters:
                self.reference_registry.register_resource(encounter)
            if encounters:
                section_resource_map[TemplateIds.ENCOUNTERS_SECTION] = encounters

            # Extract and convert Encounter Diagnosis observations to Condition resources
            encounter_diagnoses = self._extract_encounter_diagnosis_conditions(
                ccda_doc.component.structured_body
            )
            resources.extend(encounter_diagnoses)
            for diagnosis in encounter_diagnoses:
                self.reference_registry.register_resource(diagnosis)

            # Extract and convert Location resources from encounter participants
            locations = self._extract_locations(ccda_doc.component.structured_body)
            resources.extend(locations)
            for location in locations:
                self.reference_registry.register_resource(location)

            # Notes (from Notes sections)
            notes = self._extract_notes(ccda_doc.component.structured_body)
            resources.extend(notes)
            for note in notes:
                self.reference_registry.register_resource(note)
            if notes:
                section_resource_map[TemplateIds.NOTES_SECTION] = notes

        # Generate Provenance resources and create missing author resources
        # (after all clinical resources, before Composition)
        provenances, devices, practitioners, organizations = self._generate_provenance_resources(resources)

        # Add entry-level author resources first (Device, Practitioner, Organization)
        resources.extend(devices)
        for device in devices:
            self.reference_registry.register_resource(device)

        resources.extend(practitioners)
        for practitioner in practitioners:
            self.reference_registry.register_resource(practitioner)

        resources.extend(organizations)
        for org in organizations:
            self.reference_registry.register_resource(org)

        # Then add Provenance resources
        resources.extend(provenances)
        for provenance in provenances:
            self.reference_registry.register_resource(provenance)

        # Add Medication resources (created during MedicationRequest conversion)
        medications = get_medication_resources()
        for medication in medications:
            # Validate medication
            if self._validate_resource(medication):
                resources.append(medication)
                self.reference_registry.register_resource(medication)
            else:
                logger.warning(
                    "Medication resource failed validation, skipping",
                    resource_id=medication.get("id")
                )

        # Add MedicationDispense resources (extracted from medication activities)
        dispenses = get_medication_dispense_resources()
        for dispense in dispenses:
            # Validate dispense
            if self._validate_resource(dispense):
                resources.append(dispense)
                self.reference_registry.register_resource(dispense)
            else:
                logger.warning(
                    "MedicationDispense resource failed validation, skipping",
                    resource_id=dispense.get("id")
                )

        # Generate Practitioner and RelatedPerson resources from informants
        informant_practitioners, related_persons = self._generate_informant_resources()

        # Add informant-generated Practitioner resources (deduplicated with author practitioners)
        resources.extend(informant_practitioners)
        for practitioner in informant_practitioners:
            self.reference_registry.register_resource(practitioner)

        # Add RelatedPerson resources
        resources.extend(related_persons)
        for related_person in related_persons:
            self.reference_registry.register_resource(related_person)

        # Create Composition resource (required first entry in document bundle)
        composition_converter = CompositionConverter(
            code_system_mapper=self.code_system_mapper,
            section_resource_map=section_resource_map,
            reference_registry=self.reference_registry,
        )
        try:
            # Track resources before composition creation
            resources_before = set((r["resourceType"], r["id"]) for r in resources if "resourceType" in r and "id" in r)

            composition = composition_converter.convert(ccda_doc)

            # Check if composition converter registered any additional resources (e.g., placeholder custodian)
            all_registered = self.reference_registry.get_all_resources()
            for resource in all_registered:
                resource_key = (resource.get("resourceType"), resource.get("id"))
                if resource_key[0] and resource_key[1] and resource_key not in resources_before:
                    # New resource registered during composition creation
                    if resource not in resources:
                        resources.append(resource)

            # Validate Composition
            if self._validate_resource(composition):
                # Composition must be first entry in a document bundle
                # Insert at beginning of resources list
                resources.insert(0, composition)
                self.reference_registry.register_resource(composition)
            else:
                logger.error(
                    "Composition failed validation - cannot create valid document bundle",
                    resource_id=composition.get("id")
                )
        except Exception:
            logger.error("Error converting composition", exc_info=True)
            # If Composition fails, we can't create a valid document bundle
            # Fall back to collection bundle type
            logger.warning("Creating collection bundle instead of document bundle (Composition failed)")

        # Create CarePlan resource if this is a Care Plan Document
        if self._is_care_plan_document(ccda_doc):
            try:
                # Collect references for CarePlan
                goal_refs = []
                if TemplateIds.GOALS_SECTION in section_resource_map:
                    for goal in section_resource_map[TemplateIds.GOALS_SECTION]:
                        if goal.get("id"):
                            goal_refs.append({"reference": f"Goal/{goal['id']}"})

                health_concern_refs = []
                if TemplateIds.HEALTH_CONCERNS_SECTION in section_resource_map:
                    for condition in section_resource_map[TemplateIds.HEALTH_CONCERNS_SECTION]:
                        if condition.get("id"):
                            health_concern_refs.append({"reference": f"Condition/{condition['id']}"})

                # Extract intervention and outcome entries from sections for CarePlan linking
                # NOTE: Intervention/outcome resources have already been processed and registered
                # (see lines 828-844). Now we extract the raw C-CDA entries to enable proper
                # GEVL-based linking in the CarePlan converter.
                intervention_entries = []
                outcome_entries = []
                if ccda_doc.component and ccda_doc.component.structured_body:
                    structured_body = ccda_doc.component.structured_body
                    if structured_body.component:
                        for comp in structured_body.component:
                            if not comp.section:
                                continue

                            section = comp.section

                            # Check if this is the Interventions Section
                            if section.template_id:
                                for template in section.template_id:
                                    if template.root == TemplateIds.INTERVENTIONS_SECTION:
                                        # Extract intervention act entries for GEVL linking
                                        if section.entry:
                                            for entry in section.entry:
                                                if hasattr(entry, 'act') and entry.act:
                                                    intervention_entries.append(entry.act)
                                        break
                                    elif template.root == TemplateIds.OUTCOMES_SECTION:
                                        # Extract outcome observation entries for GEVL linking
                                        if section.entry:
                                            for entry in section.entry:
                                                if hasattr(entry, 'observation') and entry.observation:
                                                    outcome_entries.append(entry.observation)
                                        break

                # Create CarePlan converter and convert
                careplan_converter = CarePlanConverter(
                    code_system_mapper=self.code_system_mapper,
                    reference_registry=self.reference_registry,
                    health_concern_refs=health_concern_refs,
                    goal_refs=goal_refs,
                    intervention_entries=intervention_entries,
                    outcome_entries=outcome_entries,
                )
                careplan = careplan_converter.convert(ccda_doc)

                # Validate and add CarePlan
                if self._validate_resource(careplan):
                    resources.append(careplan)
                    self.reference_registry.register_resource(careplan)
                else:
                    logger.warning(
                        "CarePlan failed validation, skipping",
                        resource_id=careplan.get("id")
                    )
            except Exception as e:
                logger.error(f"Error converting care plan: {e}", exc_info=True)

        # Create document bundle
        # A document bundle MUST have a Composition as the first entry
        bundle: JSONObject = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [],
        }

        # Add Bundle.identifier from ClinicalDocument.id (per FHIR document spec)
        if ccda_doc.id:
            bundle["identifier"] = self._create_bundle_identifier(ccda_doc.id)

        # Add Bundle.timestamp from ClinicalDocument.effectiveTime (per FHIR document spec)
        if ccda_doc.effective_time:
            timestamp = self._convert_bundle_timestamp(ccda_doc.effective_time.value)
            if timestamp:
                bundle["timestamp"] = timestamp

        # Add resources as bundle entries (Composition first, then all others)
        for resource in resources:
            entry: JSONObject = {
                "resource": resource,
            }
            if resource.get("resourceType") and resource.get("id"):
                resource_type = resource["resourceType"]
                resource_id = resource["id"]
                entry["fullUrl"] = f"urn:uuid:{resource_id}"
            bundle["entry"].append(entry)

        # Log validation statistics
        if self.enable_validation:
            stats = self.get_validation_stats()
            logger.info(
                "FHIR validation complete",
                validated=stats["validated"],
                passed=stats["passed"],
                failed=stats["failed"],
                warnings=stats["warnings"],
                pass_rate=f"{(stats['passed'] / stats['validated'] * 100):.1f}%" if stats["validated"] > 0 else "N/A"
            )

        return {
            "bundle": bundle,
            "metadata": metadata,
        }

    def _is_care_plan_document(self, doc: ClinicalDocument) -> bool:
        """Check if document is a Care Plan Document.

        Args:
            doc: ClinicalDocument to check

        Returns:
            True if document has Care Plan Document template ID
        """
        if not doc.template_id:
            return False

        return any(
            t.root == TemplateIds.CARE_PLAN_DOCUMENT
            for t in doc.template_id
            if t.root
        )

    def _extract_conditions(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert Conditions from the structured body.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR Condition resources
        """
        return self.condition_processor.process(
            structured_body,
            metadata=metadata,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
            reference_registry=self.reference_registry,
        )

    def _extract_allergies(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert Allergies from the structured body.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR AllergyIntolerance resources
        """
        return self.allergy_processor.process(
            structured_body,
            metadata=metadata,
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
            metadata_callback=self._store_author_metadata,
        )

    def _extract_medications(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert Medications from the structured body.

        Routes to MedicationRequest (moodCode=INT/RQO/PRMS/PRP) or
        MedicationStatement (moodCode=EVN) based on mood code.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR MedicationRequest and/or MedicationStatement resources
        """
        return self.medication_processor.process(
            structured_body,
            metadata=metadata,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
            reference_registry=self.reference_registry,
        )

    def _extract_immunizations(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert Immunizations from the structured body.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR Immunization resources
        """
        return self.immunization_processor.process(
            structured_body,
            metadata=metadata,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
            reference_registry=self.reference_registry,
        )

    def _extract_goals(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert Goals from the structured body.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR Goal resources
        """
        return self.goal_processor.process(
            structured_body,
            metadata=metadata,
            reference_registry=self.reference_registry,
        )

    def _extract_careteams(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
    ) -> list[FHIRResourceDict]:
        """Extract and convert CareTeams from the structured body.

        Args:
            structured_body: The structuredBody element
            metadata: Optional conversion metadata tracker

        Returns:
            List of FHIR CareTeam resources
        """
        return self.careteam_processor.process(
            structured_body,
            metadata=metadata,
            reference_registry=self.reference_registry,
            code_system_mapper=self.code_system_mapper,
        )

    def _extract_vital_signs(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Vital Signs from the structured body.

        Note: Kept manual due to special author metadata handling.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Observation resources (panels with contained vital signs)
        """
        vital_signs = []

        if not structured_body.component:
            return vital_signs

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            if section.entry:
                for entry in section.entry:
                    if entry.organizer:
                        if entry.organizer.template_id:
                            for template in entry.organizer.template_id:
                                if template.root == TemplateIds.VITAL_SIGNS_ORGANIZER:
                                    try:
                                        panel, individuals = self.observation_converter.convert_vital_signs_organizer(
                                            entry.organizer, section=section
                                        )

                                        # Add the panel observation
                                        vital_signs.append(panel)

                                        # Add individual vital sign observations
                                        vital_signs.extend(individuals)

                                        # Store author metadata for panel observation
                                        if panel.get("id"):
                                            self._store_author_metadata(
                                                resource_type="Observation",
                                                resource_id=panel["id"],
                                                ccda_element=entry.organizer,
                                                concern_act=None,
                                            )

                                        # Store author metadata for individual observations
                                        for individual in individuals:
                                            if individual.get("id"):
                                                self._store_author_metadata(
                                                    resource_type="Observation",
                                                    resource_id=individual["id"],
                                                    ccda_element=entry.organizer,
                                                    concern_act=None,
                                                )
                                    except Exception:
                                        logger.error("Error converting vital signs organizer", exc_info=True)
                                    break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_vital_signs = self._extract_vital_signs(temp_body)
                        vital_signs.extend(nested_vital_signs)

        return vital_signs

    def _store_diagnostic_report_metadata(
        self, structured_body: StructuredBody, reports: list[FHIRResourceDict]
    ):
        """Store author metadata for DiagnosticReport resources.

        Args:
            structured_body: The structuredBody element
            reports: List of converted DiagnosticReport resources
        """
        if not structured_body.component:
            return

        # Create a map of report IDs to track which ones need metadata
        report_ids_needing_metadata = {r.get("id") for r in reports if r.get("id")}

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    if entry.organizer and entry.organizer.template_id:
                        for template in entry.organizer.template_id:
                            if template.root == TemplateIds.RESULT_ORGANIZER:
                                # Generate the same ID the converter would use
                                if entry.organizer.id and len(entry.organizer.id) > 0:
                                    first_id = entry.organizer.id[0]
                                    report_id = self._generate_report_id_from_identifier(
                                        first_id.root, first_id.extension
                                    )

                                    # If this report is in our list, store metadata
                                    if report_id and report_id in report_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="DiagnosticReport",
                                            resource_id=report_id,
                                            ccda_element=entry.organizer,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        report_ids_needing_metadata.discard(report_id)
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        self._store_diagnostic_report_metadata(temp_body, reports)

    def _generate_report_id_from_identifier(
        self, root: str | None, extension: str | None
    ) -> str | None:
        """Generate a report ID matching DiagnosticReportConverter logic.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated ID string or None
        """
        if extension:
            # Use extension as ID (removing any invalid characters)
            return extension.replace(".", "-").replace(":", "-")
        elif root:
            # Use root as ID
            return root.replace(".", "-").replace(":", "-")
        return None

    def _extract_results(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Lab Results from the structured body.

        Per FHIR best practices, result observations are created as standalone
        resources (not contained) since they have proper identifiers and independent
        existence.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR resources (DiagnosticReport and Observation resources)
        """
        resources = []

        if not structured_body.component:
            return resources

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            if section.entry:
                for entry in section.entry:
                    if entry.organizer:
                        if entry.organizer.template_id:
                            for template in entry.organizer.template_id:
                                if template.root == TemplateIds.RESULT_ORGANIZER:
                                    try:
                                        report, observations = self.diagnostic_report_converter.convert(
                                            entry.organizer, section=section
                                        )

                                        # Add the DiagnosticReport
                                        resources.append(report)

                                        # Add standalone result observations
                                        resources.extend(observations)

                                        # Store author metadata for DiagnosticReport
                                        if report.get("id"):
                                            self._store_author_metadata(
                                                resource_type="DiagnosticReport",
                                                resource_id=report["id"],
                                                ccda_element=entry.organizer,
                                                concern_act=None,
                                            )

                                        # Store author metadata for observations
                                        for observation in observations:
                                            if observation.get("id"):
                                                self._store_author_metadata(
                                                    resource_type="Observation",
                                                    resource_id=observation["id"],
                                                    ccda_element=entry.organizer,
                                                    concern_act=None,
                                                )
                                    except Exception:
                                        logger.error("Error converting result organizer", exc_info=True)
                                    break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_results = self._extract_results(temp_body)
                        resources.extend(nested_results)

        return resources

    def _extract_patient_extensions_from_social_history(
        self, structured_body: StructuredBody
    ) -> list[JSONObject]:
        """Extract patient extensions from social history observations.

        Birth sex, gender identity, sex, and tribal affiliation are special cases in
        social history - they should map to Patient extensions, NOT to separate
        Observation resources.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR extension dicts for Patient resource
        """
        from ccda_to_fhir.constants import CCDACodes, FHIRSystems

        extensions = []

        if not structured_body.component:
            return extensions

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Only process social history sections
            # Check both template ID and section code (LOINC 29762-2)
            is_social_history = False

            if section.template_id:
                is_social_history = any(
                    t.root == TemplateIds.SOCIAL_HISTORY_SECTION
                    for t in section.template_id
                    if t.root
                )

            # Also check section code for social history (LOINC 29762-2)
            if not is_social_history and section.code:
                is_social_history = (
                    section.code.code == "29762-2"
                    and section.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                )

            if not is_social_history:
                continue

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    if not entry.observation:
                        continue

                    obs = entry.observation

                    # Track if we already processed this observation (to avoid duplicates)
                    processed = False

                    # Check if it's a Birth Sex observation
                    if not processed and obs.template_id:
                        for template in obs.template_id:
                            if template.root == TemplateIds.BIRTH_SEX_OBSERVATION:
                                # Birth Sex Extension
                                if obs.value and hasattr(obs.value, "code") and obs.value.code:
                                    birth_sex_ext = {
                                        "url": FHIRSystems.US_CORE_BIRTHSEX,
                                        "valueCode": obs.value.code,  # F, M, or UNK
                                    }
                                    extensions.append(birth_sex_ext)
                                processed = True
                                break

                    # Check if it's a Gender Identity observation (by LOINC code)
                    if not processed and obs.code:
                        # Gender Identity identified by LOINC 76691-5
                        if (
                            obs.code.code == CCDACodes.GENDER_IDENTITY
                            and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                        ):
                            # Gender Identity Extension
                            if obs.value:
                                gender_identity_ext = {
                                    "url": FHIRSystems.US_CORE_GENDER_IDENTITY,
                                    "valueCodeableConcept": self.observation_converter.create_codeable_concept(
                                        code=getattr(obs.value, "code", None),
                                        code_system=getattr(obs.value, "code_system", None),
                                        display_name=getattr(obs.value, "display_name", None),
                                    ),
                                }
                                extensions.append(gender_identity_ext)
                            processed = True

                        # Sex observation identified by LOINC 46098-0
                        if (
                            obs.code.code == CCDACodes.SEX
                            and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                        ):
                            # Sex Extension (US Core)
                            if obs.value and hasattr(obs.value, "code") and obs.value.code:
                                sex_ext = {
                                    "url": FHIRSystems.US_CORE_SEX,
                                    "valueCode": obs.value.code,
                                }
                                extensions.append(sex_ext)
                            processed = True

                        # Sex Parameter for Clinical Use observation identified by LOINC 99501-9
                        if (
                            obs.code.code == CCDACodes.SEX_PARAMETER_FOR_CLINICAL_USE
                            and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                        ):
                            # Sex Parameter for Clinical Use Extension (FHIR Core)
                            if obs.value:
                                spcu_ext = {
                                    "url": FHIRSystems.PATIENT_SEX_PARAMETER_FOR_CLINICAL_USE,
                                    "extension": []
                                }

                                # value sub-extension (required)
                                value_concept = self.observation_converter.create_codeable_concept(
                                    code=getattr(obs.value, "code", None),
                                    code_system=getattr(obs.value, "code_system", None),
                                    display_name=getattr(obs.value, "display_name", None),
                                )
                                spcu_ext["extension"].append({
                                    "url": "value",
                                    "valueCodeableConcept": value_concept
                                })

                                # period sub-extension (optional)
                                # C-CDA effectiveTime is a snapshot, map to period.start
                                if obs.effective_time:
                                    effective_time = self.observation_converter._extract_effective_time(obs)
                                    if effective_time:
                                        # If it's a dict (period), use the start; otherwise use the datetime directly
                                        if isinstance(effective_time, dict):
                                            start_date = effective_time.get("start")
                                        else:
                                            start_date = effective_time

                                        if start_date:
                                            spcu_ext["extension"].append({
                                                "url": "period",
                                                "valuePeriod": {
                                                    "start": start_date
                                                }
                                            })

                                # comment sub-extension (optional)
                                # Extract from text/reference to narrative
                                if hasattr(obs, 'text') and obs.text:
                                    comment_text = None

                                    # Try to resolve reference first
                                    if hasattr(obs.text, 'reference') and obs.text.reference:
                                        ref_value = obs.text.reference.value if hasattr(
                                            obs.text.reference, 'value'
                                        ) else obs.text.reference

                                        if ref_value and isinstance(ref_value, str) and ref_value.startswith('#'):
                                            content_id = ref_value[1:]
                                            if section and hasattr(section, 'text') and section.text:
                                                comment_text = self.observation_converter._resolve_narrative_reference(
                                                    section.text, content_id
                                                )

                                    # Fall back to direct text value if reference didn't work
                                    if not comment_text and hasattr(obs.text, 'value') and obs.text.value:
                                        comment_text = obs.text.value

                                    if comment_text:
                                        spcu_ext["extension"].append({
                                            "url": "comment",
                                            "valueString": comment_text
                                        })

                                # supportingInfo sub-extension (optional)
                                # Extract from entryRelationship with typeCode="SPRT"
                                if hasattr(obs, 'entry_relationship') and obs.entry_relationship:
                                    for entry_rel in obs.entry_relationship:
                                        if hasattr(entry_rel, 'type_code') and entry_rel.type_code == "SPRT":
                                            # Get the supporting observation/act
                                            supporting_entry = None
                                            if hasattr(entry_rel, 'observation') and entry_rel.observation:
                                                supporting_entry = entry_rel.observation
                                            elif hasattr(entry_rel, 'act') and entry_rel.act:
                                                supporting_entry = entry_rel.act

                                            # Extract ID for reference
                                            if supporting_entry and hasattr(supporting_entry, 'id') and supporting_entry.id:
                                                # Use first ID
                                                supporting_id = supporting_entry.id[0] if isinstance(
                                                    supporting_entry.id, list
                                                ) else supporting_entry.id

                                                if hasattr(supporting_id, 'extension') and supporting_id.extension:
                                                    ref_id = supporting_id.extension
                                                    spcu_ext["extension"].append({
                                                        "url": "supportingInfo",
                                                        "valueReference": {
                                                            "reference": f"Observation/{ref_id}"
                                                        }
                                                    })

                                extensions.append(spcu_ext)
                            processed = True

                        # Tribal Affiliation identified by LOINC 95370-3
                        if (
                            obs.code.code == CCDACodes.TRIBAL_AFFILIATION
                            and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                        ):
                            # Tribal Affiliation Extension (US Core)
                            # Per FHIR: Extension has two sub-extensions:
                            # - tribalAffiliation (1..1, CodeableConcept, Must-Support)
                            # - isEnrolled (0..1, boolean, optional - not available in C-CDA)
                            if obs.value:
                                tribal_affiliation_ext = {
                                    "url": FHIRSystems.US_CORE_TRIBAL_AFFILIATION,
                                    "extension": [
                                        {
                                            "url": "tribalAffiliation",
                                            "valueCodeableConcept": self.observation_converter.create_codeable_concept(
                                                code=getattr(obs.value, "code", None),
                                                code_system=getattr(obs.value, "code_system", None),
                                                display_name=getattr(obs.value, "display_name", None),
                                            ),
                                        }
                                    ]
                                }
                                extensions.append(tribal_affiliation_ext)
                            processed = True

                    # Check template ID for special observations
                    if not processed and obs.template_id:
                        for template in obs.template_id:
                            # Tribal Affiliation observation
                            if template.root == TemplateIds.TRIBAL_AFFILIATION_OBSERVATION:
                                # Tribal Affiliation Extension (US Core)
                                if obs.value:
                                    tribal_affiliation_ext = {
                                        "url": FHIRSystems.US_CORE_TRIBAL_AFFILIATION,
                                        "extension": [
                                            {
                                                "url": "tribalAffiliation",
                                                "valueCodeableConcept": self.observation_converter.create_codeable_concept(
                                                    code=getattr(obs.value, "code", None),
                                                    code_system=getattr(obs.value, "code_system", None),
                                                    display_name=getattr(obs.value, "display_name", None),
                                                ),
                                            }
                                        ]
                                    }
                                    extensions.append(tribal_affiliation_ext)
                                processed = True
                                break

                            # Sex Parameter for Clinical Use observation
                            if template.root == TemplateIds.SEX_PARAMETER_FOR_CLINICAL_USE_OBSERVATION:
                                # Sex Parameter for Clinical Use Extension (FHIR Core)
                                if obs.value:
                                    spcu_ext = {
                                        "url": FHIRSystems.PATIENT_SEX_PARAMETER_FOR_CLINICAL_USE,
                                        "extension": []
                                    }

                                    # value sub-extension (required)
                                    value_concept = self.observation_converter.create_codeable_concept(
                                        code=getattr(obs.value, "code", None),
                                        code_system=getattr(obs.value, "code_system", None),
                                        display_name=getattr(obs.value, "display_name", None),
                                    )
                                    spcu_ext["extension"].append({
                                        "url": "value",
                                        "valueCodeableConcept": value_concept
                                    })

                                    # period sub-extension (optional)
                                    if obs.effective_time:
                                        effective_time = self.observation_converter._extract_effective_time(obs)
                                        if effective_time:
                                            # If it's a dict (period), use the start; otherwise use the datetime directly
                                            if isinstance(effective_time, dict):
                                                start_date = effective_time.get("start")
                                            else:
                                                start_date = effective_time

                                            if start_date:
                                                spcu_ext["extension"].append({
                                                    "url": "period",
                                                    "valuePeriod": {
                                                        "start": start_date
                                                    }
                                                })

                                    # comment sub-extension (optional)
                                    if hasattr(obs, 'text') and obs.text:
                                        comment_text = None

                                        # Try to resolve reference first
                                        if hasattr(obs.text, 'reference') and obs.text.reference:
                                            ref_value = obs.text.reference.value if hasattr(
                                                obs.text.reference, 'value'
                                            ) else obs.text.reference

                                            if ref_value and isinstance(ref_value, str) and ref_value.startswith('#'):
                                                content_id = ref_value[1:]
                                                if section and hasattr(section, 'text') and section.text:
                                                    comment_text = self.observation_converter._resolve_narrative_reference(
                                                        section.text, content_id
                                                    )

                                        # Fall back to direct text value
                                        if not comment_text and hasattr(obs.text, 'value') and obs.text.value:
                                            comment_text = obs.text.value

                                        if comment_text:
                                            spcu_ext["extension"].append({
                                                "url": "comment",
                                                "valueString": comment_text
                                            })

                                    # supportingInfo sub-extension (optional)
                                    if hasattr(obs, 'entry_relationship') and obs.entry_relationship:
                                        for entry_rel in obs.entry_relationship:
                                            if hasattr(entry_rel, 'type_code') and entry_rel.type_code == "SPRT":
                                                supporting_entry = None
                                                if hasattr(entry_rel, 'observation') and entry_rel.observation:
                                                    supporting_entry = entry_rel.observation
                                                elif hasattr(entry_rel, 'act') and entry_rel.act:
                                                    supporting_entry = entry_rel.act

                                                if supporting_entry and hasattr(supporting_entry, 'id') and supporting_entry.id:
                                                    supporting_id = supporting_entry.id[0] if isinstance(
                                                        supporting_entry.id, list
                                                    ) else supporting_entry.id

                                                    if hasattr(supporting_id, 'extension') and supporting_id.extension:
                                                        ref_id = supporting_id.extension
                                                        spcu_ext["extension"].append({
                                                            "url": "supportingInfo",
                                                            "valueReference": {
                                                                "reference": f"Observation/{ref_id}"
                                                            }
                                                        })

                                    extensions.append(spcu_ext)
                                processed = True
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        # Create a temporary structured body for recursion
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_extensions = self._extract_patient_extensions_from_social_history(
                            temp_body
                        )
                        extensions.extend(nested_extensions)

        return extensions

    def _extract_social_history(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Social History Observations from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Observation resources
        """
        observations = []

        if not structured_body.component:
            return observations

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    # Check for Observation (smoking status, social history)
                    if entry.observation:
                        obs = entry.observation

                        # Skip birth sex observations - they map to Patient.extension
                        if obs.template_id:
                            is_birth_sex = any(
                                t.root == TemplateIds.BIRTH_SEX_OBSERVATION
                                for t in obs.template_id
                                if t.root
                            )
                            if is_birth_sex:
                                continue

                        # Skip gender identity observations - they map to Patient.extension
                        if obs.code:
                            from ccda_to_fhir.constants import CCDACodes

                            is_gender_identity = (
                                obs.code.code == CCDACodes.GENDER_IDENTITY
                                and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                            )
                            if is_gender_identity:
                                continue

                        # Skip sex observations - they map to Patient.extension
                        if obs.code:
                            is_sex = (
                                obs.code.code == CCDACodes.SEX
                                and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                            )
                            if is_sex:
                                continue

                        # Skip tribal affiliation observations - they map to Patient.extension
                        if obs.code:
                            is_tribal_affiliation = (
                                obs.code.code == CCDACodes.TRIBAL_AFFILIATION
                                and obs.code.code_system == "2.16.840.1.113883.6.1"  # LOINC
                            )
                            if is_tribal_affiliation:
                                continue

                        # Skip tribal affiliation observations by template ID - they map to Patient.extension
                        if obs.template_id:
                            is_tribal_affiliation_template = any(
                                t.root == TemplateIds.TRIBAL_AFFILIATION_OBSERVATION
                                for t in obs.template_id
                                if t.root
                            )
                            if is_tribal_affiliation_template:
                                continue

                        # Check if it's a Smoking Status, Pregnancy, or Social History Observation
                        if obs.template_id:
                            for template in obs.template_id:
                                if template.root in (
                                    TemplateIds.SMOKING_STATUS_OBSERVATION,
                                    TemplateIds.SOCIAL_HISTORY_OBSERVATION,
                                    TemplateIds.PREGNANCY_OBSERVATION,
                                ):
                                    # This is a Social History Observation
                                    try:
                                        observation = self.observation_converter.convert(obs, section=section)
                                        observations.append(observation)

                                        # Store author metadata
                                        if observation.get("id"):
                                            self._store_author_metadata(
                                                resource_type="Observation",
                                                resource_id=observation["id"],
                                                ccda_element=entry.observation,
                                                concern_act=None,
                                            )
                                    except Exception:
                                        logger.error("Error converting social history observation", exc_info=True)
                                    break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        # Create a temporary structured body for recursion
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_observations = self._extract_social_history(temp_body)
                        observations.extend(nested_observations)

        return observations

    def _extract_procedures(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Procedures from the structured body.

        Processes Procedure Activity Procedure, Procedure Activity Observation,
        and Procedure Activity Act templates, as all map to FHIR Procedure resource.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Procedure resources
        """
        # Process Procedure Activity Procedures
        procedures = self.procedure_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )

        # Process Procedure Activity Observations (also map to Procedure)
        procedure_observations = self.procedure_observation_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )
        procedures.extend(procedure_observations)

        # Process Procedure Activity Acts (also map to Procedure)
        procedure_acts = self.procedure_act_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )
        procedures.extend(procedure_acts)

        # Store author metadata for each procedure
        # Note: We need to re-traverse to get the C-CDA elements for metadata
        # This is a limitation of the class-based converter approach
        self._store_procedure_metadata(structured_body, procedures)

        return procedures

    def _store_procedure_metadata(
        self, structured_body: StructuredBody, procedures: list[FHIRResourceDict]
    ):
        """Store author metadata for procedure resources.

        Args:
            structured_body: The structuredBody element
            procedures: List of converted Procedure resources
        """
        if not structured_body.component:
            return

        # Create a map of procedure IDs to track which ones need metadata
        procedure_ids_needing_metadata = {p.get("id") for p in procedures if p.get("id")}

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    # Check for Procedure Activity Procedure
                    if entry.procedure and entry.procedure.template_id:
                        for template in entry.procedure.template_id:
                            if template.root == TemplateIds.PROCEDURE_ACTIVITY_PROCEDURE:
                                # Generate the same ID the converter would use
                                procedure_id = None
                                if entry.procedure.id and len(entry.procedure.id) > 0:
                                    for id_elem in entry.procedure.id:
                                        if id_elem.root and not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                                            procedure_id = self.procedure_converter._generate_procedure_id(
                                                id_elem.root, id_elem.extension
                                            )
                                            break

                                    # If this procedure is in our list, store metadata
                                    if procedure_id and procedure_id in procedure_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="Procedure",
                                            resource_id=procedure_id,
                                            ccda_element=entry.procedure,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        procedure_ids_needing_metadata.discard(procedure_id)
                                break

                    # Check for Procedure Activity Observation
                    if entry.observation and entry.observation.template_id:
                        for template in entry.observation.template_id:
                            if template.root == TemplateIds.PROCEDURE_ACTIVITY_OBSERVATION:
                                # Generate the same ID the converter would use
                                procedure_id = None
                                if entry.observation.id and len(entry.observation.id) > 0:
                                    for id_elem in entry.observation.id:
                                        if id_elem.root and not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                                            procedure_id = self.procedure_converter._generate_procedure_id(
                                                id_elem.root, id_elem.extension
                                            )
                                            break

                                    # If this procedure is in our list, store metadata
                                    if procedure_id and procedure_id in procedure_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="Procedure",
                                            resource_id=procedure_id,
                                            ccda_element=entry.observation,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        procedure_ids_needing_metadata.discard(procedure_id)
                                break

                    # Check for Procedure Activity Act
                    if entry.act and entry.act.template_id:
                        for template in entry.act.template_id:
                            if template.root == TemplateIds.PROCEDURE_ACTIVITY_ACT:
                                # Generate the same ID the converter would use
                                procedure_id = None
                                if entry.act.id and len(entry.act.id) > 0:
                                    for id_elem in entry.act.id:
                                        if id_elem.root and not (hasattr(id_elem, "null_flavor") and id_elem.null_flavor):
                                            procedure_id = self.procedure_converter._generate_procedure_id(
                                                id_elem.root, id_elem.extension
                                            )
                                            break

                                    # If this procedure is in our list, store metadata
                                    if procedure_id and procedure_id in procedure_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="Procedure",
                                            resource_id=procedure_id,
                                            ccda_element=entry.act,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        procedure_ids_needing_metadata.discard(procedure_id)
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        self._store_procedure_metadata(temp_body, procedures)

    def _process_interventions_section(
        self, structured_body: StructuredBody
    ) -> list[FHIRResourceDict]:
        """Process intervention acts from Interventions Section.

        Intervention acts (template 2.16.840.1.113883.10.20.22.4.131) contain nested
        procedures/acts that represent the actual interventions. This method extracts
        and converts those nested entries to FHIR Procedure or ServiceRequest resources.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Procedure/ServiceRequest resources
        """
        resources = []

        if not structured_body.component:
            return resources

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Check if this is the Interventions Section
            if section.template_id:
                for template in section.template_id:
                    if template.root == TemplateIds.INTERVENTIONS_SECTION:
                        # Process entries in this section
                        if section.entry:
                            for entry in section.entry:
                                if not entry.act:
                                    continue

                                intervention_act = entry.act

                                # Check if this is an Intervention Act
                                is_intervention_act = False
                                if intervention_act.template_id:
                                    for act_template in intervention_act.template_id:
                                        if act_template.root == "2.16.840.1.113883.10.20.22.4.131":
                                            is_intervention_act = True
                                            break

                                if not is_intervention_act:
                                    continue

                                # Extract nested procedures/acts from entryRelationships
                                if hasattr(intervention_act, 'entry_relationship') and intervention_act.entry_relationship:
                                    for rel in intervention_act.entry_relationship:
                                        # Look for COMP (component) relationships
                                        if hasattr(rel, 'type_code') and rel.type_code == 'COMP':
                                            # Convert nested procedure
                                            if hasattr(rel, 'procedure') and rel.procedure:
                                                try:
                                                    procedure = self.procedure_converter.convert(rel.procedure)
                                                    if procedure:
                                                        resources.append(procedure)
                                                except Exception as e:
                                                    logger.warning(f"Failed to convert intervention procedure: {e}")

                                            # Convert nested act to procedure
                                            elif hasattr(rel, 'act') and rel.act:
                                                try:
                                                    procedure = self.procedure_converter.convert(rel.act)
                                                    if procedure:
                                                        resources.append(procedure)
                                                except Exception as e:
                                                    logger.warning(f"Failed to convert intervention act: {e}")

                                            # Convert nested substance administration
                                            elif hasattr(rel, 'substanceAdministration') and rel.substanceAdministration:
                                                # Medication activities - skip for now, they're handled elsewhere
                                                pass
                        break

        return resources

    def _process_outcomes_section(
        self, structured_body: StructuredBody
    ) -> list[FHIRResourceDict]:
        """Process outcome observations from Outcomes Section.

        Outcome observations (template 2.16.840.1.113883.10.20.22.4.144) represent
        measured outcomes of interventions. This method converts them to FHIR
        Observation resources.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Observation resources
        """
        resources = []

        if not structured_body.component:
            return resources

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Check if this is the Outcomes Section
            if section.template_id:
                for template in section.template_id:
                    if template.root == TemplateIds.OUTCOMES_SECTION:
                        # Process entries in this section
                        if section.entry:
                            for entry in section.entry:
                                if not entry.observation:
                                    continue

                                outcome_obs = entry.observation

                                # Check if this is an Outcome Observation
                                is_outcome_obs = False
                                if outcome_obs.template_id:
                                    for obs_template in outcome_obs.template_id:
                                        if obs_template.root == "2.16.840.1.113883.10.20.22.4.144":
                                            is_outcome_obs = True
                                            break

                                if not is_outcome_obs:
                                    continue

                                # Convert to FHIR Observation
                                try:
                                    observation = self.observation_converter.convert(outcome_obs, section=section)
                                    if observation:
                                        resources.append(observation)
                                except Exception as e:
                                    logger.warning(f"Failed to convert outcome observation: {e}")
                        break

        return resources

    def _extract_service_requests(
        self, structured_body: StructuredBody
    ) -> list[FHIRResourceDict]:
        """Extract and convert ServiceRequests from the structured body.

        Processes Planned Procedure and Planned Act templates from Plan of Treatment sections.
        CRITICAL: Only converts procedures/acts with moodCode in {INT, RQO, PRP, ARQ, PRMS}.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR ServiceRequest resources
        """
        # Process Planned Procedures
        service_requests = self.planned_procedure_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )

        # Process Planned Acts
        planned_acts = self.planned_act_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )
        service_requests.extend(planned_acts)

        return service_requests

    def _extract_encounters(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Encounters from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Encounter resources
        """
        # Process encounters using the section processor
        encounters = self.encounter_processor.process(
            structured_body,
            reference_registry=self.reference_registry,
        )

        # Store author metadata for each encounter
        # Note: We need to re-traverse to get the C-CDA elements for metadata
        # This is a limitation of the class-based converter approach
        self._store_encounter_metadata(structured_body, encounters)

        return encounters

    def _store_encounter_metadata(
        self, structured_body: StructuredBody, encounters: list[FHIRResourceDict]
    ):
        """Store author metadata for encounter resources.

        Args:
            structured_body: The structuredBody element
            encounters: List of converted Encounter resources
        """
        if not structured_body.component:
            return

        # Create a map of encounter IDs to track which ones need metadata
        encounter_ids_needing_metadata = {e.get("id") for e in encounters if e.get("id")}

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    if entry.encounter and entry.encounter.template_id:
                        for template in entry.encounter.template_id:
                            if template.root == TemplateIds.ENCOUNTER_ACTIVITY:
                                # Generate the same ID the converter would use (skip nullFlavor)
                                encounter_id = None
                                if entry.encounter.id:
                                    # Find first valid identifier (skip nullFlavor)
                                    for id_elem in entry.encounter.id:
                                        if not id_elem.null_flavor and (id_elem.root or id_elem.extension):
                                            encounter_id = self.encounter_converter._generate_encounter_id(
                                                id_elem.root, id_elem.extension
                                            )
                                            break

                                if encounter_id:

                                    # If this encounter is in our list, store metadata
                                    if encounter_id in encounter_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="Encounter",
                                            resource_id=encounter_id,
                                            ccda_element=entry.encounter,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        encounter_ids_needing_metadata.discard(encounter_id)
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        self._store_encounter_metadata(temp_body, encounters)

    def _extract_encounter_diagnosis_conditions(
        self, structured_body: StructuredBody
    ) -> list[FHIRResourceDict]:
        """Extract Encounter Diagnosis observations and convert to Condition resources.

        Per the mapping docs, Encounter Diagnosis observations should be converted to
        Condition resources with category="encounter-diagnosis".

        Args:
            structured_body: The C-CDA structured body

        Returns:
            List of Condition resources from encounter diagnoses
        """
        conditions = []

        if not structured_body.component:
            return conditions

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process encounters section
            if section.entry:
                for entry in section.entry:
                    if hasattr(entry, "encounter") and entry.encounter:
                        # Extract diagnosis observations from this encounter
                        diagnosis_observations = self.encounter_converter.extract_diagnosis_observations(
                            entry.encounter
                        )

                        # Convert each observation to a Condition with category="encounter-diagnosis"
                        for obs in diagnosis_observations:
                            try:
                                # Use a special section code to trigger encounter-diagnosis category
                                # The ConditionConverter maps section code "46240-8" to encounter-diagnosis
                                condition_converter = ConditionConverter(
                                    section_code="46240-8",  # Encounters section LOINC code
                                    concern_act=None,
                                    section=None,
                                    code_system_mapper=self.code_system_mapper,
                                    reference_registry=self.reference_registry,
                                )
                                condition = condition_converter.convert(obs)
                                conditions.append(condition)
                            except Exception as e:
                                logger.error(
                                    f"Error converting encounter diagnosis observation: {e}",
                                    exc_info=True
                                )

            # Process nested sections
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_conditions = self._extract_encounter_diagnosis_conditions(temp_body)
                        conditions.extend(nested_conditions)

        return conditions

    def _extract_locations(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Location resources from encounter participants.

        Extracts Service Delivery Location participants from encounters and procedures,
        converts them to FHIR Location resources, and deduplicates by identifier.

        Args:
            structured_body: The C-CDA structured body

        Returns:
            List of deduplicated FHIR Location resources
        """
        from ccda_to_fhir.converters.location import LocationConverter

        locations = []
        location_registry = {}  # Deduplication registry: key -> Location resource

        location_converter = LocationConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )

        if not structured_body.component:
            return locations

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process encounters and procedures sections
            if section.entry:
                for entry in section.entry:
                    # Extract from encounters
                    if hasattr(entry, "encounter") and entry.encounter:
                        # Extract location participants from encounter
                        if entry.encounter.participant:
                            for participant in entry.encounter.participant:
                                # Look for location participants (typeCode="LOC")
                                if hasattr(participant, "type_code") and participant.type_code == "LOC":
                                    if participant.participant_role:
                                        # Only convert if classCode is SDLOC (Service Delivery Location)
                                        # Skip other classCodes like MANU (Manufactured Product)
                                        if hasattr(participant.participant_role, "class_code") and \
                                           participant.participant_role.class_code == "SDLOC":
                                            # Convert to Location resource
                                            location = location_converter.convert(participant.participant_role)

                                            # Deduplicate by NPI or name+city
                                            dedup_key = self._get_location_dedup_key(location)

                                            if dedup_key not in location_registry:
                                                location_registry[dedup_key] = location
                                                logger.debug(
                                                    f"Created Location resource: {location.get('name')} (ID: {location.get('id')})"
                                                )

                    # Extract from procedures
                    elif hasattr(entry, "procedure") and entry.procedure:
                        # Extract location participants from procedure
                        if entry.procedure.participant:
                            for participant in entry.procedure.participant:
                                # Look for location participants (typeCode="LOC")
                                if hasattr(participant, "type_code") and participant.type_code == "LOC":
                                    if participant.participant_role:
                                        # Only convert if classCode is SDLOC (Service Delivery Location)
                                        # Skip other classCodes like MANU (Manufactured Product)
                                        if hasattr(participant.participant_role, "class_code") and \
                                           participant.participant_role.class_code == "SDLOC":
                                            # Convert to Location resource
                                            location = location_converter.convert(participant.participant_role)

                                            # Deduplicate by NPI or name+city
                                            dedup_key = self._get_location_dedup_key(location)

                                            if dedup_key not in location_registry:
                                                location_registry[dedup_key] = location
                                                logger.debug(
                                                    f"Created Location resource from Procedure: {location.get('name')} (ID: {location.get('id')})"
                                                )

            # Process nested sections
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_locations = self._extract_locations(temp_body)
                        for location in nested_locations:
                            dedup_key = self._get_location_dedup_key(location)
                            if dedup_key not in location_registry:
                                location_registry[dedup_key] = location

        # Convert registry to list
        locations = list(location_registry.values())

        return locations

    def _get_location_dedup_key(self, location: FHIRResourceDict) -> str:
        """Generate deduplication key for a Location resource.

        Uses NPI identifier if available, otherwise name+city combination.

        Args:
            location: FHIR Location resource

        Returns:
            Deduplication key string
        """
        # Priority 1: Use NPI identifier
        if "identifier" in location:
            for identifier in location["identifier"]:
                if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
                    return f"npi:{identifier.get('value')}"

        # Priority 2: Use name + city combination
        name = location.get("name", "")
        city = ""
        if "address" in location:
            city = location["address"].get("city", "")

        if name and city:
            # Normalize to lowercase for case-insensitive deduplication
            return f"name-city:{name.lower()}:{city.lower()}"

        # Priority 3: Use Location ID as fallback
        return f"id:{location.get('id', 'unknown')}"

    def _extract_header_encounter(self, ccda_doc: ClinicalDocument) -> FHIRResourceDict | None:
        """Extract and convert encompassingEncounter from document header.

        The encompassingEncounter in the header provides context for the entire document.
        This is mapped to a FHIR Encounter resource.

        Args:
            ccda_doc: The C-CDA Clinical Document

        Returns:
            FHIR Encounter resource if header encounter exists, None otherwise
        """
        if not ccda_doc.component_of:
            return None

        encompassing_encounter = ccda_doc.component_of.encompassing_encounter
        if not encompassing_encounter:
            return None

        # Build FHIR Encounter resource from header encounter
        fhir_encounter: FHIRResourceDict = {
            "resourceType": "Encounter",
        }

        # Generate ID from encounter identifier (using same logic as body encounters)
        if encompassing_encounter.id and len(encompassing_encounter.id) > 0:
            first_id = encompassing_encounter.id[0]
            # Use encounter converter's ID generation for consistency
            encounter_id = self.encounter_converter._generate_encounter_id(
                root=first_id.root,
                extension=first_id.extension,
            )
            fhir_encounter["id"] = encounter_id

            # Also add as identifier
            identifier = {"value": f"urn:uuid:{first_id.root}"}
            if first_id.extension:
                identifier["value"] = f"{first_id.root}:{first_id.extension}"
            fhir_encounter["identifier"] = [identifier]

        # Status: Default to "finished" for documented encounters
        # Header encounters in C-CDA documents are typically completed
        fhir_encounter["status"] = "finished"

        # Class: Map from code translations or CPT mapping, or default to ambulatory
        # Default to ambulatory first (required field)
        fhir_encounter["class"] = {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": "ambulatory",
        }

        # Override with specific class if code exists
        if encompassing_encounter.code:
            class_code = None
            class_display = None

            # FIRST: Check translations for V3 ActCode (highest priority)
            # Per C-CDA on FHIR IG, explicit V3 ActCode translations should be preferred
            if encompassing_encounter.code.translation:
                from ccda_to_fhir.constants import V3_ACTCODE_DISPLAY_NAMES
                for trans in encompassing_encounter.code.translation:
                    if trans.code_system == "2.16.840.1.113883.5.4":  # V3 ActCode
                        class_code = trans.code
                        # Use standard display name from mapping if available
                        standard_display = V3_ACTCODE_DISPLAY_NAMES.get(trans.code)
                        class_display = standard_display if standard_display else (trans.display_name if hasattr(trans, "display_name") else None)
                        break

            # SECOND: If no V3 ActCode translation, check if main code is CPT and map it
            # Only applies if no V3 ActCode translation was found above
            # Reference: docs/mapping/08-encounter.md lines 77-86
            if not class_code and encompassing_encounter.code.code_system == "2.16.840.1.113883.6.12":  # CPT
                from ccda_to_fhir.constants import V3_ACTCODE_DISPLAY_NAMES, map_cpt_to_actcode
                mapped_actcode = map_cpt_to_actcode(encompassing_encounter.code.code)
                if mapped_actcode:
                    class_code = mapped_actcode
                    # Use standard display name from mapping
                    class_display = V3_ACTCODE_DISPLAY_NAMES.get(mapped_actcode)

            if class_code:
                # Override default with specific class code
                fhir_encounter["class"] = {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": class_code,
                }
                if class_display:
                    fhir_encounter["class"]["display"] = class_display

            # Type: Main code goes to type
            if encompassing_encounter.code.code:
                type_coding = {
                    "code": encompassing_encounter.code.code,
                }
                if encompassing_encounter.code.code_system:
                    # Map OID to FHIR URI
                    type_coding["system"] = self.code_system_mapper.oid_to_uri(
                        encompassing_encounter.code.code_system
                    )
                if encompassing_encounter.code.display_name:
                    type_coding["display"] = encompassing_encounter.code.display_name

                fhir_encounter["type"] = [{
                    "coding": [type_coding],
                }]
                if encompassing_encounter.code.display_name:
                    fhir_encounter["type"][0]["text"] = encompassing_encounter.code.display_name

        # Period: Map from effectiveTime
        if encompassing_encounter.effective_time:
            period = {}
            if encompassing_encounter.effective_time.low:
                low_value = encompassing_encounter.effective_time.low.value if hasattr(encompassing_encounter.effective_time.low, "value") else str(encompassing_encounter.effective_time.low)
                if low_value:
                    converted = self.encounter_converter.convert_date(str(low_value))
                    if converted:
                        period["start"] = converted

            if encompassing_encounter.effective_time.high:
                high_value = encompassing_encounter.effective_time.high.value if hasattr(encompassing_encounter.effective_time.high, "value") else str(encompassing_encounter.effective_time.high)
                if high_value:
                    converted = self.encounter_converter.convert_date(str(high_value))
                    if converted:
                        period["end"] = converted

            if period:
                fhir_encounter["period"] = period

        # Discharge disposition
        if encompassing_encounter.discharge_disposition_code:
            if encompassing_encounter.discharge_disposition_code.code:
                discharge_coding = {
                    "code": encompassing_encounter.discharge_disposition_code.code,
                }
                if encompassing_encounter.discharge_disposition_code.code_system:
                    discharge_coding["system"] = self.code_system_mapper.oid_to_uri(
                        encompassing_encounter.discharge_disposition_code.code_system
                    )
                if encompassing_encounter.discharge_disposition_code.display_name:
                    discharge_coding["display"] = encompassing_encounter.discharge_disposition_code.display_name

                # Map discharge code to FHIR standard if possible
                # Code "01" = home
                if encompassing_encounter.discharge_disposition_code.code == "01":
                    discharge_coding = {
                        "system": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
                        "code": "home",
                        "display": "Home",
                    }

                fhir_encounter["hospitalization"] = {
                    "dischargeDisposition": {
                        "coding": [discharge_coding]
                    }
                }

        # Participants: responsibleParty and encounterParticipant
        participants = []

        # Responsible party -> participant with type PPRF (primary performer)
        if encompassing_encounter.responsible_party and encompassing_encounter.responsible_party.assigned_entity:
            assigned_entity = encompassing_encounter.responsible_party.assigned_entity
            if assigned_entity.id and len(assigned_entity.id) > 0:
                first_pract_id = assigned_entity.id[0]
                # Generate practitioner ID using cached UUID v4
                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                practitioner_id = generate_id_from_identifiers(
                    "Practitioner",
                    first_pract_id.root,
                    first_pract_id.extension
                )

                participants.append({
                    "type": [{
                        "coding": [{
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "PPRF",
                            "display": "primary performer",
                        }]
                    }],
                    "individual": {
                        "reference": f"Practitioner/{practitioner_id}"
                    }
                })

        # Encounter participants
        if encompassing_encounter.encounter_participant:
            for participant in encompassing_encounter.encounter_participant:
                if participant.assigned_entity and participant.assigned_entity.id:
                    first_pract_id = participant.assigned_entity.id[0]
                    # Generate practitioner ID using cached UUID v4
                    from ccda_to_fhir.id_generator import generate_id_from_identifiers
                    practitioner_id = generate_id_from_identifiers(
                        "Practitioner",
                        first_pract_id.root,
                        first_pract_id.extension
                    )

                    part_dict = {
                        "individual": {
                            "reference": f"Practitioner/{practitioner_id}"
                        }
                    }
                    # Add type code - map C-CDA ParticipationFunction codes to FHIR ParticipationType codes
                    # Reference: docs/mapping/08-encounter.md lines 217-223
                    # Reference: docs/mapping/09-participations.md lines 217-232
                    if participant.type_code:
                        # Map known function codes (PCP→PPRF, ATTPHYS→ATND, ANEST→SPRF, etc.)
                        mapped_code = PARTICIPATION_FUNCTION_CODE_MAP.get(
                            participant.type_code,
                            participant.type_code  # Pass through if not in map
                        )
                        part_dict["type"] = [{
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": mapped_code,
                            }]
                        }]
                    else:
                        # Default to PART (participant) if no type code specified
                        part_dict["type"] = [{
                            "coding": [{
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                "code": "PART",
                                "display": "participant",
                            }]
                        }]
                    participants.append(part_dict)

        if participants:
            fhir_encounter["participant"] = participants

        # Location: healthCareFacility -> location
        if encompassing_encounter.location and encompassing_encounter.location.health_care_facility:
            facility = encompassing_encounter.location.health_care_facility
            location_display = None

            if facility.location and facility.location.name:
                location_display = facility.location.name

            if location_display or (facility.id and len(facility.id) > 0):
                location_dict = {}
                if facility.id and len(facility.id) > 0:
                    first_loc_id = facility.id[0]
                    # Generate location ID from extension or root
                    if first_loc_id.extension:
                        location_id = first_loc_id.extension.replace(" ", "-").replace(".", "-")
                    elif first_loc_id.root:
                        location_id = first_loc_id.root.replace(".", "-").replace(":", "-")
                    else:
                        location_id = None

                    if location_id:
                        location_dict["reference"] = f"Location/{location_id}"

                if location_display:
                    location_dict["display"] = location_display

                if location_dict:
                    fhir_encounter["location"] = [{
                        "location": location_dict,
                        "status": "completed"  # Header encounters are completed
                    }]

        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create header Encounter without patient reference."
            )
        fhir_encounter["subject"] = self.reference_registry.get_patient_reference()

        return fhir_encounter

    def _store_note_metadata(
        self, structured_body: StructuredBody, notes: list[FHIRResourceDict]
    ):
        """Store author metadata for note (DocumentReference) resources.

        Args:
            structured_body: The structuredBody element
            notes: List of converted DocumentReference resources
        """
        if not structured_body.component:
            return

        # Create a map of note IDs to track which ones need metadata
        note_ids_needing_metadata = {n.get("id") for n in notes if n.get("id")}

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    if entry.act and entry.act.template_id:
                        for template in entry.act.template_id:
                            if template.root == TemplateIds.NOTE_ACTIVITY:
                                # Generate the same ID the converter would use
                                if entry.act.id and len(entry.act.id) > 0:
                                    first_id = entry.act.id[0]
                                    note_id = self._generate_note_id_from_identifier(first_id)

                                    # If this note is in our list, store metadata
                                    if note_id and note_id in note_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="DocumentReference",
                                            resource_id=note_id,
                                            ccda_element=entry.act,
                                            concern_act=None,
                                        )
                                        # Remove from tracking set
                                        note_ids_needing_metadata.discard(note_id)
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        self._store_note_metadata(temp_body, notes)

    def _generate_note_id_from_identifier(self, identifier) -> str:
        """Generate a note ID matching NoteActivityConverter logic.

        Args:
            identifier: Note II identifier

        Returns:
            Generated ID string (matches NoteActivityConverter._generate_note_id)
        """
        # Must match the exact logic in NoteActivityConverter._generate_note_id
        from ccda_to_fhir.id_generator import generate_id, generate_id_from_identifiers

        if not identifier:
            return generate_id()

        root = identifier.root if hasattr(identifier, 'root') and identifier.root else None
        extension = identifier.extension if hasattr(identifier, 'extension') and identifier.extension else None

        return generate_id_from_identifiers("DocumentReference", root, extension)

    def _extract_notes(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Note Activities from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR DocumentReference resources
        """
        notes = self.note_processor.process(
            structured_body,
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )

        # Store author metadata for Provenance generation
        self._store_note_metadata(structured_body, notes)

        return notes

    def _extract_practitioners_and_organizations(
        self, authors: list
    ) -> list[FHIRResourceDict]:
        """Extract and convert Practitioners, Devices, Organizations, and PractitionerRoles from authors.

        Creates four types of resources:
        1. Practitioner - person information (from assignedPerson)
        2. Device - device/software information (from assignedAuthoringDevice)
        3. Organization - organization information (from representedOrganization)
        4. PractitionerRole - links Practitioner to Organization with specialty

        Note: C-CDA requires either assignedPerson OR assignedAuthoringDevice (mutually exclusive).

        Args:
            authors: List of Author elements from C-CDA document

        Returns:
            List of FHIR Practitioner, Device, Organization, and PractitionerRole resources
        """
        resources = []
        seen_practitioners = set()
        seen_organizations = set()
        seen_roles = set()
        seen_devices = set()

        for author in authors:
            if not author.assigned_author:
                continue

            assigned_author = author.assigned_author
            practitioner_id = None
            org_id = None

            # Convert Device (from assigned_authoring_device)
            # C-CDA requires either assignedPerson OR assignedAuthoringDevice (mutually exclusive)
            if assigned_author.assigned_authoring_device:
                try:
                    device = self.device_converter.convert(assigned_author)

                    # Validate and deduplicate based on ID
                    device_id = device.get("id")
                    if self._validate_resource(device):
                        if device_id and device_id not in seen_devices:
                            resources.append(device)
                            self.reference_registry.register_resource(device)
                            seen_devices.add(device_id)
                    else:
                        logger.warning("Device failed validation, skipping", device_id=device_id)
                except Exception:
                    logger.error("Error converting device", exc_info=True)

            # Convert Practitioner (from assigned_person)
            elif assigned_author.assigned_person:
                try:
                    practitioner = self.practitioner_converter.convert(assigned_author)

                    # Validate and deduplicate based on ID
                    practitioner_id = practitioner.get("id")
                    if self._validate_resource(practitioner):
                        if practitioner_id and practitioner_id not in seen_practitioners:
                            resources.append(practitioner)
                            self.reference_registry.register_resource(practitioner)
                            seen_practitioners.add(practitioner_id)
                    else:
                        logger.warning("Practitioner failed validation, skipping", practitioner_id=practitioner_id)
                        practitioner_id = None  # Don't use for PractitionerRole
                except Exception:
                    logger.error("Error converting practitioner", exc_info=True)

            # Convert Organization (from represented_organization)
            if assigned_author.represented_organization:
                try:
                    organization = self.organization_converter.convert(
                        assigned_author.represented_organization
                    )

                    # Validate and deduplicate based on ID
                    org_id = organization.get("id")
                    if self._validate_resource(organization):
                        if org_id and org_id not in seen_organizations:
                            resources.append(organization)
                            self.reference_registry.register_resource(organization)
                            seen_organizations.add(org_id)
                    else:
                        logger.warning("Organization failed validation, skipping", org_id=org_id)
                        org_id = None  # Don't use for PractitionerRole
                except Exception:
                    logger.error("Error converting organization", exc_info=True)

            # Convert PractitionerRole (links Practitioner + Organization + specialty)
            # Only create if we have both practitioner and organization
            if practitioner_id and org_id:
                try:
                    practitioner_role = self.practitioner_role_converter.convert(
                        assigned_author,
                        practitioner_id=practitioner_id,
                        organization_id=org_id,
                    )

                    # Validate and deduplicate based on ID (combination of practitioner + org)
                    role_id = practitioner_role.get("id")
                    if self._validate_resource(practitioner_role):
                        if role_id and role_id not in seen_roles:
                            resources.append(practitioner_role)
                            self.reference_registry.register_resource(practitioner_role)
                            seen_roles.add(role_id)
                    else:
                        logger.warning("PractitionerRole failed validation, skipping", role_id=role_id)
                except Exception:
                    logger.error("Error converting practitioner role", exc_info=True)

        return resources

    def _extract_custodian_organization(self, custodian) -> FHIRResourceDict | None:
        """Extract custodian organization from document custodian.

        Args:
            custodian: Custodian element from clinical document

        Returns:
            Organization resource or None
        """
        if not custodian.assigned_custodian:
            return None

        if not custodian.assigned_custodian.represented_custodian_organization:
            return None

        custodian_org = custodian.assigned_custodian.represented_custodian_organization

        try:
            organization = self.organization_converter.convert(custodian_org)

            # Validate organization
            if self._validate_resource(organization):                return organization
            else:
                logger.warning(
                    "Custodian organization failed validation, skipping",
                    org_id=organization.get("id")
                )
                return None
        except Exception:
            logger.error("Error converting custodian organization", exc_info=True)
            return None

    def _create_resources_from_author_info(
        self,
        author_info_list: list[AuthorInfo],
        seen_devices: set[str],
        seen_practitioners: set[str],
        seen_organizations: set[str],
    ) -> tuple[list[FHIRResourceDict], list[FHIRResourceDict], list[FHIRResourceDict]]:
        """Create Device, Practitioner, and Organization resources from AuthorInfo.

        This method creates the actual FHIR resources that Provenance agents reference.
        It's used for entry-level authors (procedures, observations, etc.) where the
        Device/Practitioner resources aren't created during document-level processing.

        Args:
            author_info_list: List of AuthorInfo objects with extracted author data
            seen_devices: Set of device IDs already created (for deduplication)
            seen_practitioners: Set of practitioner IDs already created (for deduplication)
            seen_organizations: Set of organization IDs already created (for deduplication)

        Returns:
            Tuple of (devices, practitioners, organizations) lists
        """
        logger.info(f"_create_resources_from_author_info called with {len(author_info_list)} authors")
        logger.info(f"Already seen: {len(seen_practitioners)} practitioners, {len(seen_organizations)} organizations")

        devices = []
        practitioners = []
        organizations = []

        for author_info in author_info_list:
            logger.debug(f"Processing author: pract_id={author_info.practitioner_id}, org_id={author_info.organization_id}, device_id={author_info.device_id}")

            # Create Device resource if needed
            if author_info.device_id and author_info.device_id not in seen_devices:
                # Reconstruct AssignedAuthor from the original Author
                if author_info.author and author_info.author.assigned_author:
                    assigned = author_info.author.assigned_author
                    if assigned.assigned_authoring_device:
                        try:
                            device = self.device_converter.convert(assigned)
                            device_id = device.get("id")

                            if self._validate_resource(device):
                                if device_id and device_id not in seen_devices:
                                    devices.append(device)
                                    seen_devices.add(device_id)
                            else:
                                logger.warning("Device failed validation, skipping", device_id=device_id)
                        except Exception:
                            logger.error("Error converting device from entry author", exc_info=True)

            # Create Practitioner resource if needed
            if author_info.practitioner_id and author_info.practitioner_id not in seen_practitioners:
                # Reconstruct AssignedAuthor from the original Author
                if author_info.author and author_info.author.assigned_author:
                    assigned = author_info.author.assigned_author
                    if assigned.assigned_person:
                        try:
                            practitioner = self.practitioner_converter.convert(assigned)
                            # Use the practitioner_id from author_info (already generated deterministically)
                            # instead of relying on PractitionerConverter, which may not have valid IIs
                            practitioner["id"] = author_info.practitioner_id

                            if self._validate_resource(practitioner):
                                if author_info.practitioner_id not in seen_practitioners:
                                    practitioners.append(practitioner)
                                    seen_practitioners.add(author_info.practitioner_id)
                            else:
                                logger.warning("Practitioner failed validation, skipping", practitioner_id=author_info.practitioner_id)
                        except Exception:
                            logger.error("Error converting practitioner from entry author", exc_info=True)
                    else:
                        logger.debug(f"Skipping practitioner {author_info.practitioner_id} - no assigned_person in C-CDA")
                else:
                    logger.debug(f"Skipping practitioner {author_info.practitioner_id} - no author.assigned_author in metadata")

            # Create Organization resource if needed
            if author_info.organization_id and author_info.organization_id not in seen_organizations:
                # Reconstruct from the original Author
                if author_info.author and author_info.author.assigned_author:
                    assigned = author_info.author.assigned_author
                    if assigned.represented_organization:
                        try:
                            organization = self.organization_converter.convert(
                                assigned.represented_organization
                            )
                            org_id = organization.get("id")

                            if self._validate_resource(organization):
                                if org_id and org_id not in seen_organizations:
                                    organizations.append(organization)
                                    seen_organizations.add(org_id)
                            else:
                                logger.warning("Organization failed validation, skipping", org_id=org_id)
                        except Exception:
                            logger.error("Error converting organization from entry author", exc_info=True)
                    else:
                        logger.debug(f"Skipping organization {author_info.organization_id} - no represented_organization in C-CDA")
                else:
                    logger.debug(f"Skipping organization {author_info.organization_id} - no author.assigned_author in metadata")

        return (devices, practitioners, organizations)

    def _generate_provenance_resources(
        self, resources: list[FHIRResourceDict]
    ) -> tuple[list[FHIRResourceDict], list[FHIRResourceDict], list[FHIRResourceDict], list[FHIRResourceDict]]:
        """Generate Provenance resources and create missing author resources.

        This method generates Provenance resources for all resources with stored author
        metadata. It also creates any Device, Practitioner, or Organization resources
        that are referenced by Provenance agents but don't exist yet (from entry-level authors).

        Args:
            resources: List of FHIR resources that have been converted

        Returns:
            Tuple of (provenances, devices, practitioners, organizations) lists
        """
        provenances = []
        devices = []
        practitioners = []
        organizations = []

        seen_provenances = set()
        seen_devices = set()
        seen_practitioners = set()
        seen_organizations = set()

        # First, track what resources already exist in the bundle
        for resource in resources:
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            if resource_type == "Device" and resource_id:
                seen_devices.add(resource_id)
            elif resource_type == "Practitioner" and resource_id:
                seen_practitioners.add(resource_id)
            elif resource_type == "Organization" and resource_id:
                seen_organizations.add(resource_id)

        # Process each resource and create Provenance + missing author resources
        for resource in resources:
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")

            if not resource_type or not resource_id:
                continue

            key = f"{resource_type}/{resource_id}"

            # Get stored author metadata
            author_info = self._author_metadata.get(key)
            if not author_info:
                continue

            # Create missing Device/Practitioner/Organization resources from entry-level authors
            entry_devices, entry_practitioners, entry_orgs = self._create_resources_from_author_info(
                author_info, seen_devices, seen_practitioners, seen_organizations
            )
            devices.extend(entry_devices)
            practitioners.extend(entry_practitioners)
            organizations.extend(entry_orgs)

            # Create Provenance only if there are valid agents
            # (authors with practitioner/device IDs)
            has_valid_agents = any(
                a.practitioner_id or a.device_id for a in author_info
            )
            if not has_valid_agents:
                continue

            # Create Provenance
            provenance_id = f"provenance-{resource_type.lower()}-{resource_id}"
            if provenance_id not in seen_provenances:
                try:
                    provenance = self.provenance_converter.convert(
                        target_resource=resource,
                        authors=author_info,
                    )

                    # Validate provenance
                    if self._validate_resource(provenance):
                        provenances.append(provenance)
                        seen_provenances.add(provenance_id)
                    else:
                        logger.warning(
                            f"Provenance for {resource_type}/{resource_id} failed validation, skipping"
                        )
                except Exception:
                    logger.error(
                        f"Error creating Provenance for {resource_type}/{resource_id}",
                        exc_info=True,
                    )

        return (provenances, devices, practitioners, organizations)

    def _store_author_metadata(
        self,
        resource_type: str,
        resource_id: str,
        ccda_element,
        concern_act=None,
    ):
        """Store author metadata for later Provenance generation.

        Args:
            resource_type: FHIR resource type (e.g., "Condition", "AllergyIntolerance")
            resource_id: FHIR resource ID
            ccda_element: The C-CDA element containing author information
            concern_act: Optional concern act (for combined author extraction)
        """
        from ccda_to_fhir.ccda.models.act import Act
        from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
        from ccda_to_fhir.ccda.models.observation import Observation
        from ccda_to_fhir.ccda.models.organizer import Organizer
        from ccda_to_fhir.ccda.models.procedure import Procedure
        from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration

        authors = []

        if concern_act:
            # Extract from both concern act and entry element
            authors = self.author_extractor.extract_combined(concern_act, ccda_element)
        else:
            # Extract based on element type
            if isinstance(ccda_element, Observation):
                authors = self.author_extractor.extract_from_observation(ccda_element)
            elif isinstance(ccda_element, SubstanceAdministration):
                authors = self.author_extractor.extract_from_substance_administration(
                    ccda_element
                )
            elif isinstance(ccda_element, Procedure):
                authors = self.author_extractor.extract_from_procedure(ccda_element)
            elif isinstance(ccda_element, CCDAEncounter):
                authors = self.author_extractor.extract_from_encounter(ccda_element)
            elif isinstance(ccda_element, Organizer):
                authors = self.author_extractor.extract_from_organizer(ccda_element)
            elif isinstance(ccda_element, Act):
                authors = self.author_extractor.extract_from_concern_act(ccda_element)

        if authors:
            key = f"{resource_type}/{resource_id}"
            self._author_metadata[key] = authors

    def _store_informant_metadata(
        self,
        resource_type: str,
        resource_id: str,
        ccda_element,
        concern_act=None,
    ):
        """Store informant metadata for later resource generation.

        Args:
            resource_type: FHIR resource type (e.g., "Condition", "AllergyIntolerance")
            resource_id: FHIR resource ID
            ccda_element: The C-CDA element containing informant information
            concern_act: Optional concern act (for combined informant extraction)
        """
        from ccda_to_fhir.ccda.models.act import Act
        from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
        from ccda_to_fhir.ccda.models.observation import Observation
        from ccda_to_fhir.ccda.models.organizer import Organizer
        from ccda_to_fhir.ccda.models.procedure import Procedure
        from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration

        informants = []

        if concern_act:
            # Extract from both concern act and entry element
            informants = self.informant_extractor.extract_combined(concern_act, ccda_element)
        else:
            # Extract based on element type
            if isinstance(ccda_element, Observation):
                informants = self.informant_extractor.extract_from_observation(ccda_element)
            elif isinstance(ccda_element, SubstanceAdministration):
                informants = self.informant_extractor.extract_from_substance_administration(
                    ccda_element
                )
            elif isinstance(ccda_element, Procedure):
                informants = self.informant_extractor.extract_from_procedure(ccda_element)
            elif isinstance(ccda_element, CCDAEncounter):
                informants = self.informant_extractor.extract_from_encounter(ccda_element)
            elif isinstance(ccda_element, Organizer):
                informants = self.informant_extractor.extract_from_organizer(ccda_element)
            elif isinstance(ccda_element, Act):
                informants = self.informant_extractor.extract_from_concern_act(ccda_element)

        if informants:
            key = f"{resource_type}/{resource_id}"
            self._informant_metadata[key] = informants

    def _generate_informant_resources(
        self
    ) -> tuple[list[FHIRResourceDict], list[FHIRResourceDict]]:
        """Generate Practitioner and RelatedPerson resources from informant metadata.

        Returns:
            Tuple of (practitioners, related_persons)
        """
        practitioners: list[FHIRResourceDict] = []
        related_persons: list[FHIRResourceDict] = []
        seen_practitioners: set[str] = set()
        seen_related_persons: set[str] = set()

        for key, informant_list in self._informant_metadata.items():
            for informant_info in informant_list:
                try:
                    # Create Practitioner for assignedEntity informants
                    if informant_info.is_practitioner and informant_info.informant.assigned_entity:
                        practitioner_id = informant_info.practitioner_id
                        if practitioner_id and practitioner_id not in seen_practitioners:
                            practitioner = self.practitioner_converter.convert(
                                informant_info.informant.assigned_entity
                            )
                            practitioners.append(practitioner)
                            seen_practitioners.add(practitioner_id)

                    # Create RelatedPerson for relatedEntity informants
                    elif informant_info.is_related_person and informant_info.informant.related_entity:
                        related_person_id = informant_info.related_person_id
                        if related_person_id and related_person_id not in seen_related_persons:
                            # Get patient_id from the first patient resource in the bundle
                            # (All informants will reference the same patient)
                            if not hasattr(self, "_patient_id"):
                                raise ValueError(
                                    "Cannot create RelatedPerson: patient_id is required. "
                                    "Patient must be processed before informants."
                                )
                            patient_id = self._patient_id

                            from .converters.related_person import RelatedPersonConverter
                            related_person_converter = RelatedPersonConverter(patient_id=patient_id)
                            related_person = related_person_converter.convert(
                                informant_info.informant.related_entity
                            )
                            related_persons.append(related_person)
                            seen_related_persons.add(related_person_id)

                except Exception as e:
                    logger.error(
                        f"Error creating informant resource: {e}",
                        exc_info=True,
                    )

        return (practitioners, related_persons)


def convert_document(ccda_input: str | ClinicalDocument) -> ConversionResult:
    """Main conversion entry point.

    This is a convenience function that handles both XML strings and
    pre-parsed C-CDA documents.

    Args:
        ccda_input: Either an XML string or a parsed ClinicalDocument

    Returns:
        ConversionResult with bundle and metadata about processing

    Raises:
        Exception: If parsing or conversion fails
    """
    # Parse if needed and keep original XML for DocumentReference
    original_xml = None
    if isinstance(ccda_input, str):
        original_xml = ccda_input
        ccda_doc = parse_ccda(ccda_input)
    else:
        ccda_doc = ccda_input

    # Convert using DocumentConverter
    converter = DocumentConverter(original_xml=original_xml)
    return converter.convert(ccda_doc)
