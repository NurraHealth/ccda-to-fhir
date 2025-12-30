"""Goal converter: C-CDA Goal Observation to FHIR Goal resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import CD, CE, IVL_PQ, PQ
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.constants import FHIRCodes, TemplateIds
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

logger = get_logger(__name__)


# Lifecycle status mapping per C-CDA on FHIR IG ConceptMap
LIFECYCLE_STATUS_MAP = {
    "active": "active",
    "completed": "completed",
    "cancelled": "cancelled",
    "suspended": "on-hold",
    "aborted": "cancelled",
}


class GoalConverter(BaseConverter[Observation]):
    """Convert C-CDA Goal Observation to FHIR Goal resource.

    This converter handles the mapping from C-CDA Goal Observation to FHIR R4
    Goal resource per US Core Goal Profile and C-CDA on FHIR IG guidance.

    Reference:
    - US Core Goal Profile: http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal
    - C-CDA Goal Observation: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-GoalObservation.html
    - Mapping Specification: docs/mapping/13-goal.md
    """

    def __init__(self, *args, **kwargs):
        """Initialize the goal converter."""
        super().__init__(*args, **kwargs)

    def convert(self, observation: Observation, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Goal Observation to a FHIR Goal.

        Args:
            observation: The C-CDA Goal Observation (moodCode="GOL")
            section: The C-CDA Section containing this observation (for narrative)

        Returns:
            FHIR Goal resource as a dictionary

        Raises:
            ValueError: If the observation lacks required data or is not a Goal
        """
        # Validate this is a goal observation (moodCode="GOL")
        if observation.mood_code != "GOL":
            raise ValueError(
                f"Goal Observation must have moodCode='GOL', got '{observation.mood_code}'"
            )

        fhir_goal: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.GOAL,
        }

        # Add US Core Goal profile
        fhir_goal["meta"] = {
            "profile": [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal"
            ]
        }

        # 1. Generate ID from observation identifier
        if observation.id and len(observation.id) > 0:
            from ccda_to_fhir.id_generator import generate_id_from_identifiers
            first_id = observation.id[0]
            fhir_goal["id"] = generate_id_from_identifiers(
                "Goal", first_id.root, first_id.extension
            )

        # 2. Identifiers
        if observation.id:
            identifiers = []
            for id_elem in observation.id:
                if id_elem.root:
                    identifier = self.create_identifier(id_elem.root, id_elem.extension)
                    if identifier:
                        identifiers.append(identifier)
            if identifiers:
                fhir_goal["identifier"] = identifiers

        # 3. Lifecycle status (required) - map from statusCode
        if observation.status_code and observation.status_code.code:
            lifecycle_status = LIFECYCLE_STATUS_MAP.get(
                observation.status_code.code.lower(), "active"
            )
            fhir_goal["lifecycleStatus"] = lifecycle_status
        else:
            # Default to active if not specified
            fhir_goal["lifecycleStatus"] = "active"

        # 4. Description (required) - map from code or narrative text
        description = None

        # Try coded description first
        if observation.code:
            description = self._convert_code_to_codeable_concept(observation.code)

        # If no valid coded description, extract from narrative text
        if not description or not description.get("coding"):
            narrative_text = self.extract_original_text(observation.text, section)
            if narrative_text:
                description = {
                    "text": narrative_text
                }

        # Set description (required field) - fail if unavailable
        if not description:
            raise ValueError(
                "Goal.description cannot be determined. "
                "Goal Observation must have either a valid code or narrative text. "
                "Cannot create Goal resource without knowing the objective."
            )
        fhir_goal["description"] = description

        # 5. Subject (required) - reference to patient
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Goal without patient reference."
            )
        fhir_goal["subject"] = self.reference_registry.get_patient_reference()

        # 6. Start date and target due date from effectiveTime
        target_due_date = None  # Initialize outside if block to avoid UnboundLocalError
        if observation.effective_time:
            # effectiveTime/low → startDate
            if hasattr(observation.effective_time, "low") and observation.effective_time.low:
                start_date = self.convert_date(observation.effective_time.low.value)
                if start_date:
                    fhir_goal["startDate"] = start_date

            # effectiveTime/high → target.dueDate (will be added to targets below)
            if hasattr(observation.effective_time, "high") and observation.effective_time.high:
                target_due_date = self.convert_date(observation.effective_time.high.value)

        # 7. Targets from component goals (entryRelationship typeCode="COMP")
        targets = []
        if observation.entry_relationship:
            for entry_rel in observation.entry_relationship:
                if entry_rel.type_code == "COMP" and entry_rel.observation:
                    target = self._convert_component_goal_to_target(entry_rel.observation)
                    if target:
                        targets.append(target)

        # Add due date to first target if we have one
        if targets and target_due_date:
            if "dueDate" not in targets[0]:
                targets[0]["dueDate"] = target_due_date
        elif not targets and target_due_date:
            # Create a target with just the due date
            targets.append({"dueDate": target_due_date})

        if targets:
            fhir_goal["target"] = targets

        # 8. ExpressedBy from author (US Core Must Support)
        if observation.author and len(observation.author) > 0:
            # Use first author
            first_author = observation.author[0]
            expressed_by_ref = self._convert_author_to_reference(first_author)
            if expressed_by_ref:
                fhir_goal["expressedBy"] = expressed_by_ref

        # 9. Priority from Priority Preference entry relationship
        if observation.entry_relationship:
            for entry_rel in observation.entry_relationship:
                if entry_rel.type_code == "REFR" and entry_rel.observation:
                    if self._is_priority_preference(entry_rel.observation):
                        priority = self._extract_priority(entry_rel.observation)
                        if priority:
                            fhir_goal["priority"] = priority
                            break

        # 10. Achievement status from Progress Toward Goal entry relationship
        if observation.entry_relationship:
            for entry_rel in observation.entry_relationship:
                if entry_rel.type_code == "REFR" and entry_rel.observation:
                    if self._is_progress_toward_goal(entry_rel.observation):
                        achievement_status = self._extract_achievement_status(
                            entry_rel.observation
                        )
                        if achievement_status:
                            fhir_goal["achievementStatus"] = achievement_status
                            break

        # 11. Addresses (health concerns) from Entry Reference entry relationship
        if observation.entry_relationship:
            addresses = []
            for entry_rel in observation.entry_relationship:
                if entry_rel.type_code == "RSON" and entry_rel.observation:
                    if self._is_entry_reference(entry_rel.observation):
                        address_ref = self._extract_health_concern_reference(
                            entry_rel.observation
                        )
                        if address_ref:
                            addresses.append(address_ref)
            if addresses:
                fhir_goal["addresses"] = addresses

        # 12. Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=observation, section=section)
        if narrative:
            fhir_goal["text"] = narrative

        return fhir_goal

    def _convert_code_to_codeable_concept(
        self, code_element: CD | CE | None
    ) -> JSONObject:
        """Convert C-CDA code element to FHIR CodeableConcept.

        Args:
            code_element: C-CDA CD or CE element

        Returns:
            FHIR CodeableConcept
        """
        if not code_element:
            return {}

        # Extract original text if available
        original_text = None
        if hasattr(code_element, "original_text") and code_element.original_text:
            original_text = self.extract_original_text(code_element.original_text)

        # Handle translations
        translations = []
        if hasattr(code_element, "translation") and code_element.translation:
            for trans in code_element.translation:
                if trans.code and trans.code_system:
                    translations.append({
                        "code": trans.code,
                        "code_system": trans.code_system,
                        "display_name": trans.display_name if hasattr(trans, "display_name") else None,
                    })

        return self.create_codeable_concept(
            code=code_element.code,
            code_system=code_element.code_system,
            display_name=code_element.display_name if hasattr(code_element, "display_name") else None,
            original_text=original_text,
            translations=translations,
        )

    def _convert_component_goal_to_target(self, component_obs: Observation) -> JSONObject | None:
        """Convert a component Goal Observation to a FHIR target.

        Args:
            component_obs: Component observation with moodCode="GOL"

        Returns:
            FHIR target object or None
        """
        if component_obs.mood_code != "GOL":
            return None

        target: JSONObject = {}

        # Measure code
        if component_obs.code:
            measure = self._convert_code_to_codeable_concept(component_obs.code)
            if measure:
                target["measure"] = measure

        # Detail value (typed)
        if component_obs.value:
            # Handle PQ (Physical Quantity) → detailQuantity
            if isinstance(component_obs.value, PQ):
                if component_obs.value.value is not None:
                    detail_quantity = self.create_quantity(component_obs.value.value, component_obs.value.unit)
                    if detail_quantity:
                        target["detailQuantity"] = detail_quantity

            # Handle IVL_PQ (Interval) → detailRange
            elif isinstance(component_obs.value, IVL_PQ):
                detail_range: JSONObject = {}
                if component_obs.value.low and component_obs.value.low.value is not None:
                    low_quantity = self.create_quantity(component_obs.value.low.value, component_obs.value.low.unit)
                    if low_quantity:
                        detail_range["low"] = low_quantity
                if component_obs.value.high and component_obs.value.high.value is not None:
                    high_quantity = self.create_quantity(component_obs.value.high.value, component_obs.value.high.unit)
                    if high_quantity:
                        detail_range["high"] = high_quantity
                if detail_range:
                    target["detailRange"] = detail_range

            # Handle CD/CE (CodeableConcept) → detailCodeableConcept
            elif isinstance(component_obs.value, (CD, CE)):
                detail_cc = self._convert_code_to_codeable_concept(component_obs.value)
                if detail_cc:
                    target["detailCodeableConcept"] = detail_cc

            # Handle other types (ST, BL, INT, etc.) if needed
            # For now, we'll focus on the most common types

        # US Core gol-1 constraint: If target.detail is populated, target.measure is required
        # Validate defensive coding to prevent constraint violation
        has_detail = any(k in target for k in ["detailQuantity", "detailRange", "detailCodeableConcept"])
        if has_detail and "measure" not in target:
            logger.warning(
                "Skipping target with detail but no measure (violates US Core gol-1 constraint). "
                "This should not occur with valid C-CDA (code is 1..1)."
            )
            return None

        return target if target else None

    def _convert_author_to_reference(self, author) -> JSONObject | None:
        """Convert C-CDA author to FHIR Reference.

        Args:
            author: C-CDA Author element

        Returns:
            FHIR Reference object or None
        """
        if not author or not author.assigned_author:
            return None

        assigned_author = author.assigned_author

        # Check if author is the patient (by checking if assignedAuthor/id matches recordTarget)
        # For now, we'll create a reference based on the ID
        if assigned_author.id and len(assigned_author.id) > 0:
            first_id = assigned_author.id[0]

            # Check if this is a patient ID (this is a simplification; in production
            # we'd need to compare with the recordTarget/patientRole/id)
            # For now, if it has an assignedPerson, assume it's a Practitioner
            if assigned_author.assigned_person:
                # Create Practitioner reference
                from ccda_to_fhir.id_generator import generate_id_from_identifiers
                practitioner_id = generate_id_from_identifiers(
                    "Practitioner", first_id.root, first_id.extension
                )
                return {"reference": f"Practitioner/{practitioner_id}"}
            else:
                # Assume it's the patient
                if not self.reference_registry:
                    raise ValueError(
                        "reference_registry is required. "
                        "Cannot extract expressedBy reference without registry."
                    )
                return self.reference_registry.get_patient_reference()

        return None

    def _is_priority_preference(self, obs: Observation) -> bool:
        """Check if observation is a Priority Preference template.

        Template ID: 2.16.840.1.113883.10.20.22.4.143
        """
        if not obs.template_id:
            return False
        return any(
            t.root == TemplateIds.PRIORITY_PREFERENCE for t in obs.template_id if t.root
        )

    def _is_progress_toward_goal(self, obs: Observation) -> bool:
        """Check if observation is a Progress Toward Goal template.

        Template ID: 2.16.840.1.113883.10.20.22.4.110
        """
        if not obs.template_id:
            return False
        return any(
            t.root == TemplateIds.PROGRESS_TOWARD_GOAL for t in obs.template_id if t.root
        )

    def _is_entry_reference(self, obs: Observation) -> bool:
        """Check if observation is an Entry Reference template.

        Template ID: 2.16.840.1.113883.10.20.22.4.122
        """
        if not obs.template_id:
            return False
        return any(
            t.root == TemplateIds.ENTRY_REFERENCE for t in obs.template_id if t.root
        )

    def _extract_priority(self, priority_obs: Observation) -> JSONObject | None:
        """Extract priority from Priority Preference observation.

        Args:
            priority_obs: Priority Preference observation

        Returns:
            FHIR CodeableConcept for priority
        """
        if not priority_obs.value:
            return None

        if isinstance(priority_obs.value, (CD, CE)):
            return self._convert_code_to_codeable_concept(priority_obs.value)

        return None

    def _extract_achievement_status(self, progress_obs: Observation) -> JSONObject | None:
        """Extract achievement status from Progress Toward Goal observation.

        Args:
            progress_obs: Progress Toward Goal observation

        Returns:
            FHIR CodeableConcept for achievement status
        """
        if not progress_obs.value:
            return None

        if isinstance(progress_obs.value, (CD, CE)):
            return self._convert_code_to_codeable_concept(progress_obs.value)

        return None

    def _extract_health_concern_reference(self, entry_ref_obs: Observation) -> JSONObject | None:
        """Extract health concern reference from Entry Reference observation.

        Args:
            entry_ref_obs: Entry Reference observation

        Returns:
            FHIR Reference object or None
        """
        # Look for the referenced observation's ID
        if entry_ref_obs.id and len(entry_ref_obs.id) > 0:
            from ccda_to_fhir.id_generator import generate_id_from_identifiers
            first_id = entry_ref_obs.id[0]
            # Create a reference to a Condition resource
            condition_id = generate_id_from_identifiers(
                "Condition", first_id.root, first_id.extension
            )

            reference: JSONObject = {"reference": f"Condition/{condition_id}"}

            # Add display if we have the value
            if entry_ref_obs.value:
                if isinstance(entry_ref_obs.value, (CD, CE)) and hasattr(entry_ref_obs.value, "display_name") and entry_ref_obs.value.display_name:
                    reference["display"] = entry_ref_obs.value.display_name

            return reference

        return None
