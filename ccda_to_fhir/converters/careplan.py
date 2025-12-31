"""CarePlan converter: C-CDA Care Plan Document to FHIR CarePlan resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.constants import FHIRCodes, TemplateIds
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from .references import ReferenceRegistry

logger = get_logger(__name__)


class CarePlanConverter(BaseConverter[ClinicalDocument]):
    """Convert C-CDA Care Plan Document to FHIR CarePlan resource.

    The CarePlan resource represents the Assessment and Plan portion of a Care Plan
    Document. It aggregates references to health concerns (addresses), goals, and
    planned interventions (activities).

    This converter works in conjunction with CompositionConverter to create complete
    Care Plan Documents per C-CDA on FHIR IG.

    Reference:
    - US Core CarePlan Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan
    - C-CDA on FHIR Care Plan: http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document
    - Mapping Specification: docs/mapping/14-careplan.md
    """

    def __init__(
        self,
        reference_registry: ReferenceRegistry | None = None,
        health_concern_refs: list[JSONObject] | None = None,
        goal_refs: list[JSONObject] | None = None,
        intervention_entries: list | None = None,
        outcome_entries: list | None = None,
        **kwargs,
    ):
        """Initialize the CarePlan converter.

        Args:
            reference_registry: Reference registry for resource references
            health_concern_refs: References to Condition resources (CarePlan.addresses)
            goal_refs: References to Goal resources (CarePlan.goal)
            intervention_entries: C-CDA intervention entry elements (CarePlan.activity)
            outcome_entries: C-CDA outcome observation entry elements (CarePlan.activity.outcomeReference)
            **kwargs: Additional arguments passed to BaseConverter
        """
        super().__init__(**kwargs)
        self.reference_registry = reference_registry
        self.health_concern_refs = health_concern_refs or []
        self.goal_refs = goal_refs or []
        self.intervention_entries = intervention_entries or []
        self.outcome_entries = outcome_entries or []

    def convert(self, clinical_document: ClinicalDocument) -> FHIRResourceDict:
        """Convert a C-CDA Care Plan Document to a FHIR CarePlan resource.

        Args:
            clinical_document: The C-CDA ClinicalDocument (Care Plan Document)

        Returns:
            FHIR CarePlan resource as a dictionary

        Raises:
            ValueError: If required fields are missing or document is not a Care Plan
        """
        if not clinical_document:
            raise ValueError("ClinicalDocument is required")

        # Verify this is a Care Plan Document
        if not self._is_care_plan_document(clinical_document):
            raise ValueError(
                "ClinicalDocument must be a Care Plan Document "
                f"(template ID {TemplateIds.CARE_PLAN_DOCUMENT})"
            )

        careplan: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.CAREPLAN,
        }

        # Add US Core CarePlan profile
        careplan["meta"] = {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careplan"
            ]
        }

        # Generate ID from document identifier
        if clinical_document.id:
            from ccda_to_fhir.id_generator import generate_id_from_identifiers
            careplan_id = generate_id_from_identifiers(
                "CarePlan",
                clinical_document.id.root,
                clinical_document.id.extension,
            )
            careplan["id"] = careplan_id

        # Identifier - same as document ID
        if clinical_document.id:
            identifier = self.create_identifier(
                clinical_document.id.root,
                clinical_document.id.extension
            )
            if identifier:
                careplan["identifier"] = [identifier]

        # Status (REQUIRED) - default to "active"
        # Map from serviceEvent statusCode if available
        status = self._determine_status(clinical_document)
        careplan["status"] = status

        # Intent (REQUIRED) - fixed value "plan" for Care Plan Documents
        careplan["intent"] = "plan"

        # Category (REQUIRED) - fixed value "assess-plan" for Care Plan Documents
        # US Core CarePlan requires category from http://hl7.org/fhir/us/core/CodeSystem/careplan-category
        careplan["category"] = [{
            "coding": [{
                "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                "code": "assess-plan",
                "display": "Assessment and Plan of Treatment"
            }]
        }]

        # Subject (REQUIRED) - reference to patient
        if self.reference_registry:
            careplan["subject"] = self.reference_registry.get_patient_reference()
        else:
            # Fallback for unit tests
            if clinical_document.record_target and len(clinical_document.record_target) > 0:
                record_target = clinical_document.record_target[0]
                if record_target.patient_role and record_target.patient_role.id:
                    from ccda_to_fhir.id_generator import generate_id_from_identifiers
                    patient_id = record_target.patient_role.id[0]
                    patient_ref_id = generate_id_from_identifiers(
                        "Patient",
                        patient_id.root,
                        patient_id.extension,
                    )
                    careplan["subject"] = {"reference": f"Patient/{patient_ref_id}"}
                else:
                    raise ValueError(
                        "Cannot create CarePlan: patient identifier has no root"
                    )
            else:
                raise ValueError(
                    "Cannot create CarePlan: patient identifier missing from recordTarget"
                )

        # Period - from documentationOf/serviceEvent effectiveTime
        if clinical_document.documentation_of:
            for doc_of in clinical_document.documentation_of:
                if doc_of.service_event and doc_of.service_event.effective_time:
                    period = self._convert_service_event_period(
                        doc_of.service_event.effective_time
                    )
                    if period:
                        careplan["period"] = period
                        break

        # Author - primary author of the care plan
        if clinical_document.author and len(clinical_document.author) > 0:
            first_author = clinical_document.author[0]
            author_ref = self._convert_author_to_reference(first_author)
            if author_ref:
                careplan["author"] = author_ref

        # Contributors - all authors and serviceEvent performers
        contributors = []

        # Add all authors as contributors
        if clinical_document.author:
            for author in clinical_document.author:
                contributor_ref = self._convert_author_to_reference(author)
                if contributor_ref and contributor_ref not in contributors:
                    contributors.append(contributor_ref)

        # Add serviceEvent performers as contributors (US Core Must Support)
        if clinical_document.documentation_of:
            for doc_of in clinical_document.documentation_of:
                if doc_of.service_event and doc_of.service_event.performer:
                    for performer in doc_of.service_event.performer:
                        if performer.assigned_entity and performer.assigned_entity.id:
                            from ccda_to_fhir.id_generator import generate_id_from_identifiers
                            performer_id = performer.assigned_entity.id[0]
                            practitioner_id = generate_id_from_identifiers(
                                "Practitioner",
                                performer_id.root,
                                performer_id.extension,
                            )
                            performer_ref = {"reference": f"Practitioner/{practitioner_id}"}
                            if performer_ref not in contributors:
                                contributors.append(performer_ref)

        if contributors:
            careplan["contributor"] = contributors

        # Addresses - references to health concerns (Condition resources)
        if self.health_concern_refs:
            careplan["addresses"] = self.health_concern_refs

        # Goal - references to Goal resources
        if self.goal_refs:
            careplan["goal"] = self.goal_refs

        # Activity - planned interventions with properly linked outcomes
        if self.intervention_entries:
            activities = self._link_outcomes_to_activities(
                self.intervention_entries,
                self.outcome_entries
            )
            if activities:
                careplan["activity"] = activities

        # Text narrative - generate from sections
        careplan["text"] = self._generate_narrative(
            clinical_document=clinical_document,
            period=careplan.get("period"),
            health_concern_count=len(self.health_concern_refs),
            goal_count=len(self.goal_refs),
            intervention_entries=self.intervention_entries,
        )

        return careplan

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

    def _determine_status(self, doc: ClinicalDocument) -> str:
        """Determine CarePlan status from document context.

        NOTE: This status hierarchy is implementation logic, not explicitly
        mandated by C-CDA on FHIR IG. It represents best-practice inference
        from available document context per C-CDA on FHIR mapping guidance
        (docs/mapping/14-careplan.md lines 567-582).

        Status hierarchy:
        1. If period.end in past → completed
        2. If all interventions completed → completed
        3. If any intervention cancelled → revoked
        4. If document authenticated → active
        5. Default → active

        Args:
            doc: ClinicalDocument

        Returns:
            CarePlan status code (active, completed, etc.)
        """
        from datetime import datetime, timezone

        # Extract period for date comparison
        period = None
        if doc.documentation_of:
            for doc_of in doc.documentation_of:
                if doc_of.service_event and doc_of.service_event.effective_time:
                    period = self._convert_service_event_period(
                        doc_of.service_event.effective_time
                    )
                    if period:
                        break

        # 1. Check if period has ended (past end date → completed)
        if period and period.get('end'):
            try:
                end_date_str = period['end']
                # Handle both date (YYYY-MM-DD) and datetime formats
                if 'T' in end_date_str:
                    end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
                else:
                    # Date only - add time component for comparison
                    end_date = datetime.fromisoformat(f"{end_date_str}T23:59:59+00:00")

                if end_date < datetime.now(timezone.utc):
                    return "completed"
            except (ValueError, AttributeError):
                # Invalid date format, skip this check
                pass

        # 2. Check intervention statuses
        if self.intervention_entries:
            intervention_statuses = [
                self._get_intervention_status(interv)
                for interv in self.intervention_entries
            ]
            # Filter out None values
            intervention_statuses = [s for s in intervention_statuses if s is not None]

            if intervention_statuses:
                # If all interventions completed → care plan completed
                if all(s == 'completed' for s in intervention_statuses):
                    return "completed"

                # If any intervention cancelled → care plan revoked
                if 'cancelled' in intervention_statuses:
                    return "revoked"

        # 3. Check if document is authenticated (finalized)
        if hasattr(doc, 'legal_authenticator') and doc.legal_authenticator:
            return "active"

        # 4. Default to active
        return "active"

    def _get_intervention_status(self, intervention_entry) -> str | None:
        """Extract status from intervention entry.

        Maps C-CDA statusCode values to CarePlan-relevant status indicators.

        Per C-CDA statusCode vocabulary:
        - completed → completed
        - active → active
        - cancelled → cancelled
        - aborted → cancelled
        - suspended → suspended
        - new, held → active (planned activities)

        Args:
            intervention_entry: C-CDA intervention entry element

        Returns:
            Status string (completed, active, cancelled, suspended) or None
        """
        if not hasattr(intervention_entry, 'status_code'):
            return None

        status_code = intervention_entry.status_code
        if not status_code or not hasattr(status_code, 'code'):
            return None

        code = status_code.code.lower() if status_code.code else None
        if not code:
            return None

        # Map common C-CDA status codes to CarePlan-relevant statuses
        status_map = {
            'completed': 'completed',
            'active': 'active',
            'cancelled': 'cancelled',
            'aborted': 'cancelled',  # Treat aborted as cancelled
            'suspended': 'suspended',
            'new': 'active',  # New planned activities are active
            'held': 'active',  # Held activities are still active (on hold)
        }

        return status_map.get(code)

    def _convert_service_event_period(self, effective_time) -> JSONObject | None:
        """Convert serviceEvent effectiveTime to FHIR Period.

        Args:
            effective_time: C-CDA effectiveTime element (IVL_TS)

        Returns:
            FHIR Period or None
        """
        period: JSONObject = {}

        if hasattr(effective_time, "low") and effective_time.low:
            start = self.convert_date(effective_time.low.value)
            if start:
                period["start"] = start

        if hasattr(effective_time, "high") and effective_time.high:
            end = self.convert_date(effective_time.high.value)
            if end:
                period["end"] = end

        return period if period else None

    def _convert_author_to_reference(self, author) -> JSONObject | None:
        """Convert C-CDA author to FHIR Reference.

        Args:
            author: C-CDA Author element

        Returns:
            FHIR Reference or None
        """
        if not author or not author.assigned_author:
            return None

        assigned_author = author.assigned_author

        # Create reference based on assignedAuthor ID
        if assigned_author.id and len(assigned_author.id) > 0:
            first_id = assigned_author.id[0]

            # If assignedPerson exists, reference Practitioner
            if assigned_author.assigned_person:
                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                practitioner_id = generate_id_from_identifiers(
                    "Practitioner",
                    first_id.root,
                    first_id.extension,
                )
                return {"reference": f"Practitioner/{practitioner_id}"}
            else:
                # Could be patient as author
                if not self.reference_registry:
                    raise ValueError(
                        "reference_registry is required. "
                        "Cannot extract activity performer without registry."
                    )
                return self.reference_registry.get_patient_reference()

        return None

    def _link_outcomes_to_activities(
        self,
        interventions: list,
        outcomes: list
    ) -> list[JSONObject]:
        """Link outcome observations to their parent intervention activities.

        Uses entryRelationship with typeCode='GEVL' (evaluates) to determine
        which outcomes belong to which activities. This prevents the incorrect
        behavior of adding all outcomes to all activities.

        Args:
            interventions: List of intervention entry elements from C-CDA
            outcomes: List of outcome observation entry elements from C-CDA

        Returns:
            List of activity detail dicts with proper outcomeReference arrays
        """
        activity_details = []

        for intervention in interventions:
            activity_ref = self._create_intervention_reference(intervention)
            if not activity_ref:
                continue

            # CarePlan.activity.reference is a Reference type, not a string
            activity_detail: JSONObject = {"reference": {"reference": activity_ref}}

            # Find outcomes linked to this intervention via entryRelationship
            linked_outcomes = []

            if hasattr(intervention, 'entry_relationship'):
                for rel in intervention.entry_relationship:
                    # typeCode='GEVL' means "evaluates" - outcome evaluates the intervention
                    if hasattr(rel, 'type_code') and rel.type_code == 'GEVL':
                        if hasattr(rel, 'observation'):
                            outcome_id = self._get_entry_id(rel.observation)
                            # Check if this outcome is in our outcomes list
                            for outcome_entry in outcomes:
                                if self._get_entry_id(outcome_entry) == outcome_id:
                                    outcome_ref = self._create_outcome_reference(outcome_entry)
                                    if outcome_ref:
                                        linked_outcomes.append(outcome_ref)

            # Only add outcomeReference if there are linked outcomes
            if linked_outcomes:
                activity_detail["outcomeReference"] = linked_outcomes

            activity_details.append(activity_detail)

        return activity_details

    def _get_entry_id(self, entry) -> str | None:
        """Extract identifier from C-CDA entry for matching.

        Args:
            entry: C-CDA entry element (observation, act, procedure, etc.)

        Returns:
            ID root or None if not found
        """
        if hasattr(entry, 'id') and entry.id:
            # Handle both single id and list of ids
            if isinstance(entry.id, list) and len(entry.id) > 0:
                if hasattr(entry.id[0], 'root'):
                    return entry.id[0].root
            elif hasattr(entry.id, 'root'):
                return entry.id.root
        return None

    def _generate_resource_id_from_entry(self, entry, resource_type: str) -> str | None:
        """Generate FHIR resource ID from C-CDA entry identifiers.

        Uses the same standardized ID generation logic as all resource converters.

        Args:
            entry: C-CDA entry element (observation, act, procedure, etc.)
            resource_type: FHIR resource type (lowercase, e.g., "procedure")

        Returns:
            Generated FHIR resource ID or None
        """
        if not hasattr(entry, 'id') or not entry.id:
            return None

        # Extract root and extension from first identifier
        root = None
        extension = None

        if isinstance(entry.id, list) and len(entry.id) > 0:
            if hasattr(entry.id[0], 'root'):
                root = entry.id[0].root
            if hasattr(entry.id[0], 'extension'):
                extension = entry.id[0].extension
        elif hasattr(entry.id, 'root'):
            root = entry.id.root
            if hasattr(entry.id, 'extension'):
                extension = entry.id.extension

        # Convert to strings if needed (handles Mock objects in tests)
        if root is not None and not isinstance(root, str):
            root = str(root) if root else None
        if extension is not None and not isinstance(extension, str):
            extension = str(extension) if extension else None

        # All converters now use standard generate_resource_id with hashing
        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type=resource_type
        )

    def _create_intervention_reference(self, intervention_entry) -> str | None:
        """Create reference to intervention resource (ServiceRequest/Procedure).

        For intervention acts (template 2.16.840.1.113883.10.20.22.4.131), the actual
        procedure/activity is in a nested entryRelationship with typeCode='COMP'.
        This method looks for the nested procedure first, then falls back to the
        intervention act itself.

        Args:
            intervention_entry: C-CDA intervention entry element (usually an intervention act)

        Returns:
            Reference string or None
        """
        if not intervention_entry or not self.reference_registry:
            return None

        # First, check if this intervention has nested procedures/acts (COMP entryRelationships)
        if hasattr(intervention_entry, 'entry_relationship') and intervention_entry.entry_relationship:
            for rel in intervention_entry.entry_relationship:
                if hasattr(rel, 'type_code') and rel.type_code == 'COMP':
                    # Look for nested procedure
                    if hasattr(rel, 'procedure') and rel.procedure:
                        resource_id = self._generate_resource_id_from_entry(rel.procedure, "procedure")
                        if resource_id:
                            # Try as Procedure
                            if self.reference_registry.has_resource("Procedure", resource_id):
                                return f"Procedure/{resource_id}"

                            # Try as ServiceRequest
                            if self.reference_registry.has_resource("ServiceRequest", resource_id):
                                return f"ServiceRequest/{resource_id}"

                    # Look for nested act
                    elif hasattr(rel, 'act') and rel.act:
                        resource_id = self._generate_resource_id_from_entry(rel.act, "procedure")
                        if resource_id:
                            # Try as Procedure
                            if self.reference_registry.has_resource("Procedure", resource_id):
                                return f"Procedure/{resource_id}"

        # Fallback: Try the intervention entry itself
        resource_id = self._generate_resource_id_from_entry(intervention_entry, "servicerequest")
        if resource_id:
            # Try ServiceRequest first (for planned interventions)
            if self.reference_registry.has_resource("ServiceRequest", resource_id):
                return f"ServiceRequest/{resource_id}"

            # Try Procedure (for completed interventions)
            if self.reference_registry.has_resource("Procedure", resource_id):
                return f"Procedure/{resource_id}"

        return None

    def _create_outcome_reference(self, outcome_entry) -> JSONObject | None:
        """Create reference to Observation outcome resource.

        Args:
            outcome_entry: C-CDA outcome observation entry element

        Returns:
            FHIR Reference dict or None
        """
        if not outcome_entry or not self.reference_registry:
            return None

        # Generate resource ID using same logic as Observation converter
        resource_id = self._generate_resource_id_from_entry(outcome_entry, "observation")
        if not resource_id:
            return None

        # Check if observation resource exists with generated ID
        if self.reference_registry.has_resource("Observation", resource_id):
            return {"reference": f"Observation/{resource_id}"}

        return None

    def _generate_narrative(
        self,
        clinical_document: ClinicalDocument,
        period: JSONObject | None,
        health_concern_count: int,
        goal_count: int,
        intervention_entries: list,
    ) -> JSONObject:
        """Generate FHIR narrative from Care Plan sections.

        Creates meaningful XHTML narrative summarizing the care plan per FHIR R4 and
        US Core requirements. The narrative uses "generated" status as it is created
        entirely from structured data.

        Args:
            clinical_document: The C-CDA ClinicalDocument
            period: Care plan period dict
            health_concern_count: Number of health concerns
            goal_count: Number of goals
            intervention_entries: List of intervention entry elements

        Returns:
            FHIR text dict with status and div (well-formed XHTML)
        """
        import html

        lines = ['<div xmlns="http://www.w3.org/1999/xhtml">']

        # Title
        if clinical_document.title:
            title = html.escape(clinical_document.title)
            lines.append(f'<h2>{title}</h2>')
        else:
            lines.append('<h2>Care Plan</h2>')

        # Period
        if period:
            period_text = self._format_period_text(period)
            lines.append(f'<p><strong>Period:</strong> {html.escape(period_text)}</p>')

        # Health Concerns summary
        if health_concern_count > 0:
            plural = "s" if health_concern_count > 1 else ""
            lines.append(f'<p><strong>Health Concerns:</strong> {health_concern_count} concern{plural} documented</p>')

        # Goals summary
        if goal_count > 0:
            plural = "s" if goal_count > 1 else ""
            lines.append(f'<p><strong>Goals:</strong> {goal_count} goal{plural} documented</p>')

        # Interventions section
        if intervention_entries:
            lines.append('<h3>Planned Interventions</h3>')
            lines.append('<ul>')
            for intervention in intervention_entries:
                intervention_text = self._extract_intervention_text(intervention)
                if intervention_text:
                    lines.append(f'<li>{html.escape(intervention_text)}</li>')
            lines.append('</ul>')

        # If no meaningful content was generated, add a minimal summary
        if len(lines) == 1:
            lines.append('<p>Care Plan with no detailed information available</p>')

        lines.append('</div>')

        return {
            "status": "generated",
            "div": '\n'.join(lines)
        }

    def _format_period_text(self, period: JSONObject) -> str:
        """Format period as readable text.

        Args:
            period: FHIR Period dict with start and/or end

        Returns:
            Human-readable period text
        """
        start = period.get('start', 'Unknown')
        end = period.get('end')

        if end:
            return f"{start} to {end}"
        else:
            return f"{start} onwards"

    def _extract_intervention_text(self, intervention_entry) -> str | None:
        """Extract displayable text from intervention entry.

        Attempts to extract meaningful display text from the intervention entry,
        preferring nested procedure/act details over the parent intervention code
        as they provide more specific information.

        Args:
            intervention_entry: C-CDA intervention entry element

        Returns:
            Displayable text or None
        """
        # First try to get text from nested procedure in entryRelationship
        # This is preferred as it provides more specific information
        if hasattr(intervention_entry, 'entry_relationship'):
            for rel in intervention_entry.entry_relationship:
                # Look for COMP (component) relationships with procedures
                if hasattr(rel, 'type_code') and rel.type_code == 'COMP':
                    # Check for procedure
                    if hasattr(rel, 'procedure') and rel.procedure:
                        text = self._extract_code_display_text(rel.procedure)
                        if text:
                            return text
                    # Check for act
                    elif hasattr(rel, 'act') and rel.act:
                        text = self._extract_code_display_text(rel.act)
                        if text:
                            return text

        # Fallback to parent intervention code element
        if hasattr(intervention_entry, 'code') and intervention_entry.code:
            code = intervention_entry.code

            # Prefer displayName
            if hasattr(code, 'display_name') and code.display_name:
                return code.display_name

            # Fallback to originalText
            if hasattr(code, 'original_text') and code.original_text:
                # originalText might be a string or an object
                if isinstance(code.original_text, str):
                    return code.original_text
                elif hasattr(code.original_text, 'value'):
                    return code.original_text.value

            # Fallback to code value
            if hasattr(code, 'code') and code.code:
                return f"Intervention (code: {code.code})"

        return None

    def _extract_code_display_text(self, entry) -> str | None:
        """Extract display text from an entry's code element.

        Args:
            entry: C-CDA entry element with a code attribute

        Returns:
            Display text or None
        """
        if not hasattr(entry, 'code') or not entry.code:
            return None

        code = entry.code

        # Prefer displayName
        if hasattr(code, 'display_name') and code.display_name:
            return code.display_name

        # Fallback to originalText
        if hasattr(code, 'original_text') and code.original_text:
            if isinstance(code.original_text, str):
                return code.original_text
            elif hasattr(code.original_text, 'value'):
                return code.original_text.value

        return None
