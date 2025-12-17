"""Main conversion entry point for C-CDA to FHIR conversion."""

from __future__ import annotations

import hashlib
from typing import Type

from fhir_core.fhirabstractmodel import FHIRAbstractModel
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.composition import Composition
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.device import Device
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.documentreference import DocumentReference
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.procedure import Procedure
from fhir.resources.R4B.provenance import Provenance

from ccda_to_fhir.exceptions import CCDAConversionError
from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.validation import FHIRValidator

from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.ccda.models.section import StructuredBody
from ccda_to_fhir.ccda.parser import parse_ccda
from ccda_to_fhir.constants import TemplateIds, PARTICIPATION_FUNCTION_CODE_MAP
from ccda_to_fhir.logging_config import get_logger

from .converters.allergy_intolerance import convert_allergy_concern_act
from .converters.author_extractor import AuthorExtractor, AuthorInfo
from .converters.code_systems import CodeSystemMapper
from .converters.composition import CompositionConverter
from .converters.condition import convert_problem_concern_act
from .converters.device import DeviceConverter
from .converters.diagnostic_report import DiagnosticReportConverter
from .converters.document_reference import DocumentReferenceConverter
from .converters.encounter import EncounterConverter
from .converters.immunization import convert_immunization_activity
from .converters.medication_request import convert_medication_activity
from .converters.note_activity import convert_note_activity
from .converters.section_processor import SectionConfig, SectionProcessor
from .converters.observation import ObservationConverter
from .converters.organization import OrganizationConverter
from .converters.patient import PatientConverter
from .converters.practitioner import PractitionerConverter
from .converters.practitioner_role import PractitionerRoleConverter
from .converters.procedure import ProcedureConverter
from .converters.provenance import ProvenanceConverter
from .converters.references import ReferenceRegistry

logger = get_logger(__name__)

# Mapping of FHIR resource types to their fhir.resources classes for validation
RESOURCE_TYPE_MAPPING: dict[str, Type[FHIRAbstractModel]] = {
    "Patient": Patient,
    "Practitioner": Practitioner,
    "PractitionerRole": PractitionerRole,
    "Organization": Organization,
    "Device": Device,
    "DocumentReference": DocumentReference,
    "Condition": Condition,
    "AllergyIntolerance": AllergyIntolerance,
    "MedicationRequest": MedicationRequest,
    "Immunization": Immunization,
    "Observation": Observation,
    "DiagnosticReport": DiagnosticReport,
    "Procedure": Procedure,
    "Encounter": Encounter,
    "Composition": Composition,
    "Provenance": Provenance,
}


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

        # Initialize individual resource converters
        self.patient_converter = PatientConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.document_reference_converter = DocumentReferenceConverter(
            code_system_mapper=self.code_system_mapper,
            original_xml=original_xml,
        )
        self.observation_converter = ObservationConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.diagnostic_report_converter = DiagnosticReportConverter(
            code_system_mapper=self.code_system_mapper
        )
        self.procedure_converter = ProcedureConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
        )
        self.encounter_converter = EncounterConverter(
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
        self.medication_processor = SectionProcessor(
            SectionConfig(
                template_id=TemplateIds.MEDICATION_ACTIVITY,
                entry_type="substance_administration",
                converter=convert_medication_activity,
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

    def convert(self, ccda_doc: ClinicalDocument) -> FHIRResourceDict:
        """Convert a C-CDA document to a FHIR Bundle.

        Args:
            ccda_doc: Parsed C-CDA document (ClinicalDocument model)

        Returns:
            FHIR Bundle as a dict with Composition as first entry
        """
        resources = []
        # Section→resource mapping for Composition.section[].entry references
        section_resource_map: dict[str, list[FHIRResourceDict]] = {}

        # Convert Patient (from recordTarget)
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

        # Convert custodian organization if present
        if ccda_doc.custodian:
            custodian_org = self._extract_custodian_organization(ccda_doc.custodian)
            if custodian_org:
                resources.append(custodian_org)
                self.reference_registry.register_resource(custodian_org)

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
            conditions = self._extract_conditions(ccda_doc.component.structured_body)
            resources.extend(conditions)
            for condition in conditions:
                self.reference_registry.register_resource(condition)
            if conditions:
                section_resource_map[TemplateIds.PROBLEM_SECTION] = conditions

            # Allergies (from Allergy sections)
            allergies = self._extract_allergies(ccda_doc.component.structured_body)
            resources.extend(allergies)
            for allergy in allergies:
                self.reference_registry.register_resource(allergy)
            if allergies:
                section_resource_map[TemplateIds.ALLERGY_SECTION] = allergies

            # Medications (from Medications sections)
            medications = self._extract_medications(ccda_doc.component.structured_body)
            resources.extend(medications)
            for medication in medications:
                self.reference_registry.register_resource(medication)
            if medications:
                section_resource_map[TemplateIds.MEDICATIONS_SECTION] = medications

            # Immunizations (from Immunizations sections)
            immunizations = self._extract_immunizations(ccda_doc.component.structured_body)
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

            # Procedures (from Procedures sections)
            procedures = self._extract_procedures(ccda_doc.component.structured_body)
            resources.extend(procedures)
            for procedure in procedures:
                self.reference_registry.register_resource(procedure)
            if procedures:
                section_resource_map[TemplateIds.PROCEDURES_SECTION] = procedures

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

        # Create Composition resource (required first entry in document bundle)
        composition_converter = CompositionConverter(
            code_system_mapper=self.code_system_mapper,
            section_resource_map=section_resource_map,
            reference_registry=self.reference_registry,
        )
        try:
            composition = composition_converter.convert(ccda_doc)

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
        except Exception as e:
            logger.error(f"Error converting composition", exc_info=True)
            # If Composition fails, we can't create a valid document bundle
            # Fall back to collection bundle type
            logger.warning("Creating collection bundle instead of document bundle (Composition failed)")

        # Update patient references in all resources (after Composition is created)
        patient_id = None
        if resources and len(resources) > 1:
            # Patient is typically the second resource (after Composition)
            for resource in resources:
                if resource.get("resourceType") == "Patient":
                    patient_id = resource.get("id")
                    break

        if patient_id:
            # Validate that patient exists in registry and update references
            try:
                patient_ref = self.reference_registry.resolve_reference("Patient", patient_id)
                for resource in resources:
                    # Update subject references in all resources (including Composition)
                    if "subject" in resource:
                        resource["subject"] = patient_ref
            except CCDAConversionError as e:
                # Patient not in registry - this is a critical error
                # The bundle would have broken references
                logger.error(
                    f"Cannot create valid bundle: {e}",
                    exc_info=True,
                    extra={"patient_id": patient_id}
                )
                raise

        # Create document bundle
        # A document bundle MUST have a Composition as the first entry
        bundle: JSONObject = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [],
        }

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
                f"FHIR validation complete",
                validated=stats["validated"],
                passed=stats["passed"],
                failed=stats["failed"],
                warnings=stats["warnings"],
                pass_rate=f"{(stats['passed'] / stats['validated'] * 100):.1f}%" if stats["validated"] > 0 else "N/A"
            )

        return bundle

    def _extract_conditions(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Conditions from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Condition resources
        """
        return self.condition_processor.process(
            structured_body,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
        )

    def _extract_allergies(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Allergies from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR AllergyIntolerance resources
        """
        return self.allergy_processor.process(
            structured_body,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
        )

    def _extract_medications(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Medications from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR MedicationRequest resources
        """
        return self.medication_processor.process(
            structured_body,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
        )

    def _extract_immunizations(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Immunizations from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Immunization resources
        """
        return self.immunization_processor.process(
            structured_body,
            code_system_mapper=self.code_system_mapper,
            metadata_callback=self._store_author_metadata,
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
                                    except Exception as e:
                                        logger.error(f"Error converting vital signs organizer", exc_info=True)
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

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR DiagnosticReport resources
        """
        reports = self.results_processor.process(structured_body)

        # Store author metadata for Provenance generation
        self._store_diagnostic_report_metadata(structured_body, reports)

        return reports

    def _extract_patient_extensions_from_social_history(
        self, structured_body: StructuredBody
    ) -> list[JSONObject]:
        """Extract birth sex and gender identity extensions for Patient from social history.

        Birth sex and gender identity are special cases in social history - they should
        map to Patient extensions, NOT to separate Observation resources.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR extension dicts for Patient resource
        """
        from ccda_to_fhir.constants import CCDACodes, CodeSystemOIDs, FHIRSystems

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

                    # Check if it's a Birth Sex observation
                    if obs.template_id:
                        for template in obs.template_id:
                            if template.root == TemplateIds.BIRTH_SEX_OBSERVATION:
                                # Birth Sex Extension
                                if obs.value and hasattr(obs.value, "code") and obs.value.code:
                                    birth_sex_ext = {
                                        "url": FHIRSystems.US_CORE_BIRTHSEX,
                                        "valueCode": obs.value.code,  # F, M, or UNK
                                    }
                                    extensions.append(birth_sex_ext)
                                break

                    # Check if it's a Gender Identity observation (by LOINC code)
                    if obs.code:
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
                                    except Exception as e:
                                        logger.error(f"Error converting social history observation", exc_info=True)
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

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Procedure resources
        """
        # Process procedures using the section processor
        procedures = self.procedure_processor.process(structured_body)

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
                    if entry.procedure and entry.procedure.template_id:
                        for template in entry.procedure.template_id:
                            if template.root == TemplateIds.PROCEDURE_ACTIVITY_PROCEDURE:
                                # Generate the same ID the converter would use
                                if entry.procedure.id and len(entry.procedure.id) > 0:
                                    first_id = entry.procedure.id[0]
                                    procedure_id = self.procedure_converter._generate_procedure_id(
                                        first_id.root, first_id.extension
                                    )

                                    # If this procedure is in our list, store metadata
                                    if procedure_id in procedure_ids_needing_metadata:
                                        self._store_author_metadata(
                                            resource_type="Procedure",
                                            resource_id=procedure_id,
                                            ccda_element=entry.procedure,
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

    def _extract_encounters(self, structured_body: StructuredBody) -> list[FHIRResourceDict]:
        """Extract and convert Encounters from the structured body.

        Args:
            structured_body: The structuredBody element

        Returns:
            List of FHIR Encounter resources
        """
        # Process encounters using the section processor
        encounters = self.encounter_processor.process(structured_body)

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
                                # Generate the same ID the converter would use
                                if entry.encounter.id and len(entry.encounter.id) > 0:
                                    first_id = entry.encounter.id[0]
                                    encounter_id = self.encounter_converter._generate_encounter_id(
                                        first_id.root, first_id.extension
                                    )

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

        # Generate ID from encounter identifier
        if encompassing_encounter.id and len(encompassing_encounter.id) > 0:
            first_id = encompassing_encounter.id[0]
            # Generate encounter ID from extension or root (matching DocumentReferenceConverter logic)
            if first_id.extension:
                encounter_id = first_id.extension.replace(" ", "-").replace(".", "-").lower()
            elif first_id.root:
                encounter_id = first_id.root.replace(".", "-").replace(":", "-").lower()
            else:
                encounter_id = "encounter-header-unknown"

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
        # Check if code has a translation with V3 ActCode system
        if encompassing_encounter.code:
            class_code = None
            class_display = None

            # FIRST: Check translations for V3 ActCode (highest priority)
            # Per C-CDA on FHIR IG, explicit V3 ActCode translations should be preferred
            if encompassing_encounter.code.translation:
                for trans in encompassing_encounter.code.translation:
                    if trans.code_system == "2.16.840.1.113883.5.4":  # V3 ActCode
                        class_code = trans.code
                        class_display = trans.display_name if hasattr(trans, "display_name") and trans.display_name else None
                        break

            # SECOND: If no V3 ActCode translation, check if main code is CPT and map it
            # Only applies if no V3 ActCode translation was found above
            # Reference: docs/mapping/08-encounter.md lines 77-86
            if not class_code and encompassing_encounter.code.code_system == "2.16.840.1.113883.6.12":  # CPT
                from ccda_to_fhir.constants import map_cpt_to_actcode
                mapped_actcode = map_cpt_to_actcode(encompassing_encounter.code.code)
                if mapped_actcode:
                    class_code = mapped_actcode
                    # Map CPT code display names to V3 ActCode display names
                    display_map = {
                        "AMB": "ambulatory",
                        "IMP": "inpatient encounter",
                        "EMER": "emergency",
                        "HH": "home health",
                    }
                    class_display = display_map.get(mapped_actcode)

            if class_code:
                fhir_encounter["class"] = {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": class_code,
                }
                if class_display:
                    fhir_encounter["class"]["display"] = class_display
            else:
                # Default to ambulatory
                fhir_encounter["class"] = {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB",
                    "display": "ambulatory",
                }

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
                # Generate practitioner ID from extension or root
                if first_pract_id.extension:
                    practitioner_id = first_pract_id.extension.replace(" ", "-").replace(".", "-")
                elif first_pract_id.root:
                    practitioner_id = first_pract_id.root.replace(".", "-").replace(":", "-")
                else:
                    practitioner_id = None

                if practitioner_id:
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
                    # Generate practitioner ID from extension or root
                    if first_pract_id.extension:
                        practitioner_id = first_pract_id.extension.replace(" ", "-").replace(".", "-")
                    elif first_pract_id.root:
                        practitioner_id = first_pract_id.root.replace(".", "-").replace(":", "-")
                    else:
                        practitioner_id = None

                    if practitioner_id:
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

        # Subject: Patient reference (will be updated later with actual patient ID)
        fhir_encounter["subject"] = {"reference": "Patient/patient-placeholder"}

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

    def _generate_note_id_from_identifier(self, identifier) -> str | None:
        """Generate a note ID matching NoteActivityConverter logic.

        Args:
            identifier: Note II identifier

        Returns:
            Generated ID string or None
        """
        if not identifier:
            return None

        # Use extension if present
        if identifier.extension:
            clean_ext = identifier.extension.replace(" ", "-").replace(".", "-").lower()
            return f"note-{clean_ext}"
        elif identifier.root:
            # Use hash of root if no extension (matching NoteActivityConverter)
            hash_val = hashlib.sha256(identifier.root.encode()).hexdigest()[:16]
            return f"note-{hash_val}"

        return None

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
                except Exception as e:
                    logger.error(f"Error converting device", exc_info=True)

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
                except Exception as e:
                    logger.error(f"Error converting practitioner", exc_info=True)

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
                except Exception as e:
                    logger.error(f"Error converting organization", exc_info=True)

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
                except Exception as e:
                    logger.error(f"Error converting practitioner role", exc_info=True)

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
        except Exception as e:
            logger.error(f"Error converting custodian organization", exc_info=True)
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
        devices = []
        practitioners = []
        organizations = []

        for author_info in author_info_list:
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
                        except Exception as e:
                            logger.error("Error converting device from entry author", exc_info=True)

            # Create Practitioner resource if needed
            if author_info.practitioner_id and author_info.practitioner_id not in seen_practitioners:
                # Reconstruct AssignedAuthor from the original Author
                if author_info.author and author_info.author.assigned_author:
                    assigned = author_info.author.assigned_author
                    if assigned.assigned_person:
                        try:
                            practitioner = self.practitioner_converter.convert(assigned)
                            practitioner_id = practitioner.get("id")

                            if self._validate_resource(practitioner):
                                if practitioner_id and practitioner_id not in seen_practitioners:
                                    practitioners.append(practitioner)
                                    seen_practitioners.add(practitioner_id)
                            else:
                                logger.warning("Practitioner failed validation, skipping", practitioner_id=practitioner_id)
                        except Exception as e:
                            logger.error("Error converting practitioner from entry author", exc_info=True)

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
                        except Exception as e:
                            logger.error("Error converting organization from entry author", exc_info=True)

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
                except Exception as e:
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


def convert_document(ccda_input: str | ClinicalDocument) -> FHIRResourceDict:
    """Main conversion entry point.

    This is a convenience function that handles both XML strings and
    pre-parsed C-CDA documents.

    Args:
        ccda_input: Either an XML string or a parsed ClinicalDocument

    Returns:
        FHIR Bundle as a dict

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
