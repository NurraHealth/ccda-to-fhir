"""CarePlan converter: C-CDA Care Plan Document to FHIR CarePlan resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.constants import FHIRCodes, TemplateIds
from ccda_to_fhir.logging_config import get_logger

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
        reference_registry: "ReferenceRegistry | None" = None,
        health_concern_refs: list[JSONObject] | None = None,
        goal_refs: list[JSONObject] | None = None,
        intervention_refs: list[JSONObject] | None = None,
        outcome_refs: list[JSONObject] | None = None,
        **kwargs,
    ):
        """Initialize the CarePlan converter.

        Args:
            reference_registry: Reference registry for resource references
            health_concern_refs: References to Condition resources (CarePlan.addresses)
            goal_refs: References to Goal resources (CarePlan.goal)
            intervention_refs: References to ServiceRequest/Procedure (CarePlan.activity)
            outcome_refs: References to Observation resources (CarePlan.activity.outcomeReference)
            **kwargs: Additional arguments passed to BaseConverter
        """
        super().__init__(**kwargs)
        self.reference_registry = reference_registry
        self.health_concern_refs = health_concern_refs or []
        self.goal_refs = goal_refs or []
        self.intervention_refs = intervention_refs or []
        self.outcome_refs = outcome_refs or []

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
                    careplan["subject"] = {"reference": "Patient/patient-unknown"}
            else:
                careplan["subject"] = {"reference": "Patient/patient-unknown"}

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

        # Activity - planned interventions and outcomes
        if self.intervention_refs:
            activities = []
            for intervention_ref in self.intervention_refs:
                activity: JSONObject = {
                    "reference": intervention_ref
                }
                # Add outcome references if they exist
                # Note: Linking outcomes to specific activities requires additional logic
                # For now, we'll add all outcomes to all activities
                # TODO: Implement proper outcome-to-activity linking based on entryRelationship
                if self.outcome_refs:
                    activity["outcomeReference"] = self.outcome_refs
                activities.append(activity)

            careplan["activity"] = activities

        # Text narrative - generate from sections
        # TODO: Implement narrative generation from Health Concerns, Goals, Interventions
        # For now, create a minimal narrative
        careplan["text"] = {
            "status": "additional",
            "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p>Care Plan</p></div>"
        }

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
        """Determine CarePlan status from document.

        Args:
            doc: ClinicalDocument

        Returns:
            CarePlan status code (active, completed, etc.)
        """
        # Note: ServiceEvent doesn't have statusCode in C-CDA
        # We default to "active" for Care Plan Documents
        # In the future, we could check other indicators like authentication status
        return "active"

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
                if self.reference_registry:
                    return self.reference_registry.get_patient_reference()
                else:
                    return {"reference": "Patient/patient-unknown"}

        return None
