"""DiagnosticReport converter: C-CDA Result Organizer to FHIR DiagnosticReport resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.constants import (
    DIAGNOSTIC_REPORT_STATUS_TO_FHIR,
    FHIRCodes,
    FHIRSystems,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter
from .observation import ObservationConverter


class DiagnosticReportConverter(BaseConverter[Organizer]):
    """Convert C-CDA Result Organizer to FHIR DiagnosticReport resource.

    This converter handles the mapping from C-CDA Result Organizer
    (template 2.16.840.1.113883.10.20.22.4.1) to a FHIR R4B DiagnosticReport
    resource, including panel code, status, category, and standalone result observations.

    Per FHIR best practices, result observations are created as standalone resources
    (not contained) since they have proper identifiers and independent existence.

    Reference: http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html
    """

    def __init__(self, *args, seen_observation_ids: set | None = None, seen_diagnostic_report_ids: set | None = None, **kwargs):
        """Initialize the diagnostic report converter.

        Args:
            seen_observation_ids: Set to track observation IDs and detect duplicates within a document
            seen_diagnostic_report_ids: Set to track diagnostic report IDs and detect duplicates within a document
        """
        super().__init__(*args, **kwargs)
        self.observation_converter = ObservationConverter(
            code_system_mapper=self.code_system_mapper,
            reference_registry=self.reference_registry,
            seen_observation_ids=seen_observation_ids,
        )
        # Track seen diagnostic report IDs to detect invalid C-CDA documents that reuse IDs
        self.seen_diagnostic_report_ids = seen_diagnostic_report_ids if seen_diagnostic_report_ids is not None else set()

    def convert(self, organizer: Organizer, section=None) -> tuple[FHIRResourceDict, list[FHIRResourceDict]]:
        """Convert a C-CDA Result Organizer to a FHIR DiagnosticReport and Observations.

        Args:
            organizer: The C-CDA Result Organizer
            section: The C-CDA Section containing this organizer (for narrative)

        Returns:
            Tuple of (DiagnosticReport resource, list of Observation resources)

        Raises:
            ValueError: If the organizer lacks required data
        """
        report: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.DIAGNOSTIC_REPORT,
        }

        # 1. Generate ID from organizer identifier
        # NOTE: Some C-CDA documents reuse the same ID for different DiagnosticReports
        # We detect this and use a fallback ID generation to avoid duplicates
        if organizer.id and len(organizer.id) > 0:
            first_id = organizer.id[0]
            dr_id_key = (first_id.root, first_id.extension)

            # Check if we've seen this diagnostic report ID before (duplicate)
            if dr_id_key in self.seen_diagnostic_report_ids:
                # ID reuse detected - fall back to generating a unique ID
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.warning(
                    f"DiagnosticReport ID {first_id.root} (extension={first_id.extension}) is reused in C-CDA document. "
                    f"Generating unique ID to avoid duplicate DiagnosticReport resources."
                )
                from ccda_to_fhir.id_generator import generate_id
                report["id"] = generate_id()
            else:
                # First time seeing this diagnostic report ID - use it
                report["id"] = self._generate_report_id(first_id.root, first_id.extension)
                self.seen_diagnostic_report_ids.add(dr_id_key)

        # 2. Identifiers
        if organizer.id:
            identifiers = []
            for id_elem in organizer.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                report["identifier"] = identifiers

        # 3. Status (required)
        status = self._determine_status(organizer)
        report["status"] = status

        # 4. Category - LAB
        report["category"] = [
            {
                "coding": [
                    {
                        "system": FHIRSystems.V2_0074,
                        "code": FHIRCodes.DiagnosticReportCategory.LAB,
                        "display": "Laboratory",
                    }
                ]
            }
        ]

        # 5. Code (required) - panel code from organizer
        # FHIR R4B requires DiagnosticReport.code (1..1)
        code_cc = None
        if organizer.code:
            code_cc = self._convert_code_to_codeable_concept(organizer.code)

        if not code_cc:
            # Fallback for C-CDA Result Organizers with nullFlavor codes
            # Real-world C-CDA documents may have valid organizers without usable codes
            # Per FHIR requirement, use a generic fallback code
            code_cc = {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "11502-2",
                    "display": "Laboratory report"
                }],
                "text": "Laboratory report"
            }

        report["code"] = code_cc

        # 6. Subject (patient reference)
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create DiagnosticReport without patient reference."
            )
        report["subject"] = self.reference_registry.get_patient_reference()

        # 7. Effective time
        effective_time = self._extract_effective_time(organizer)
        if effective_time:
            report["effectiveDateTime"] = effective_time

        # 8. Results interpreter (who interpreted the results)
        # Per US Core: resultsInterpreter is Must-Support
        # Maps from C-CDA organizer.performer to FHIR Reference(Practitioner|Organization)
        if organizer.performer:
            interpreters = []
            for performer in organizer.performer:
                if performer.assigned_entity and performer.assigned_entity.id:
                    # Extract practitioner ID from assigned entity
                    for id_elem in performer.assigned_entity.id:
                        if id_elem.root:
                            practitioner_id = self._generate_practitioner_id(
                                id_elem.root, id_elem.extension
                            )
                            interpreters.append({
                                "reference": f"urn:uuid:{practitioner_id}"
                            })
                            break  # Use first valid ID
            if interpreters:
                report["resultsInterpreter"] = interpreters

        # 9. Convert component observations to standalone resources
        # Per FHIR best practices: use standalone resources (not contained) since
        # these observations have proper identifiers and independent existence.
        # Reference: https://www.hl7.org/fhir/R4/references.html#contained
        observations = []
        result_refs = []

        if organizer.component:
            for component in organizer.component:
                if component.observation:
                    # Convert the component observation to standalone resource
                    observation = self.observation_converter.convert(
                        component.observation, section=section
                    )
                    observations.append(observation)

                    # Add reference to this observation
                    if "id" in observation:
                        result_refs.append({
                            "reference": f"urn:uuid:{observation['id']}"
                        })

        if result_refs:
            report["result"] = result_refs

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=organizer, section=section)
        if narrative:
            report["text"] = narrative

        return report, observations

    def _generate_report_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR resource ID from C-CDA identifier.

        Uses standard ID generation with hashing for consistency across all converters.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            A valid FHIR ID string
        """
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="diagnosticreport"
        )

    def _determine_status(self, organizer: Organizer) -> str:
        """Determine FHIR DiagnosticReport status from C-CDA status code.

        Args:
            organizer: The C-CDA Organizer

        Returns:
            FHIR DiagnosticReport status code
        """
        if not organizer.status_code or not organizer.status_code.code:
            return FHIRCodes.DiagnosticReportStatus.FINAL

        status_code = organizer.status_code.code.lower()
        return DIAGNOSTIC_REPORT_STATUS_TO_FHIR.get(
            status_code, FHIRCodes.DiagnosticReportStatus.FINAL
        )

    def _convert_code_to_codeable_concept(self, code) -> JSONObject | None:
        """Convert C-CDA CD to FHIR CodeableConcept.

        Args:
            code: The C-CDA code element

        Returns:
            FHIR CodeableConcept or None
        """
        if not code:
            return None

        codings = []

        # Primary coding
        if code.code and code.code_system:
            coding: JSONObject = {
                "system": self.map_oid_to_uri(code.code_system),
                "code": code.code,
            }
            if code.display_name:
                coding["display"] = code.display_name
            codings.append(coding)

        # Translations
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                if trans.code and trans.code_system:
                    trans_coding: JSONObject = {
                        "system": self.map_oid_to_uri(trans.code_system),
                        "code": trans.code,
                    }
                    if trans.display_name:
                        trans_coding["display"] = trans.display_name
                    codings.append(trans_coding)

        if not codings:
            return None

        codeable_concept: JSONObject = {"coding": codings}

        # Original text
        if hasattr(code, "original_text") and code.original_text:
            # original_text is ED (Encapsulated Data)
            if hasattr(code.original_text, "reference"):
                # Skip reference-only original text
                pass
            elif hasattr(code.original_text, "text") and code.original_text.text:
                codeable_concept["text"] = code.original_text.text

        return codeable_concept

    def _extract_effective_time(self, organizer: Organizer) -> str | None:
        """Extract and convert effective time to FHIR format.

        Args:
            organizer: The C-CDA Organizer

        Returns:
            FHIR formatted datetime string or None
        """
        if not organizer.effective_time:
            return None

        # Handle IVL_TS (interval) - use low if available, otherwise high
        if hasattr(organizer.effective_time, "low") and organizer.effective_time.low:
            if hasattr(organizer.effective_time.low, "value"):
                return self.convert_date(organizer.effective_time.low.value)

        if hasattr(organizer.effective_time, "high") and organizer.effective_time.high:
            if hasattr(organizer.effective_time.high, "value"):
                return self.convert_date(organizer.effective_time.high.value)

        # Handle TS (single time point)
        if hasattr(organizer.effective_time, "value") and organizer.effective_time.value:
            return self.convert_date(organizer.effective_time.value)

        return None

    # Note: _generate_practitioner_id is inherited from BaseConverter
