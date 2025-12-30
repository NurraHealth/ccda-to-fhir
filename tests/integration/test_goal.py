"""E2E tests for Goal resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

GOALS_SECTION_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.60"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestGoalConversion:
    """E2E tests for C-CDA Goal Observation to FHIR Goal conversion."""

    def test_converts_goal_description(self, ccda_goal_weight_loss: str) -> None:
        """Test that the goal description is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "description" in goal

        # Check for SNOMED code
        snomed = next(
            (c for c in goal["description"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "289169006"
        assert snomed["display"] == "Weight loss"

    def test_converts_lifecycle_status(self, ccda_goal_weight_loss: str) -> None:
        """Test that lifecycle status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "lifecycleStatus" in goal
        assert goal["lifecycleStatus"] == "active"

    def test_converts_start_date(self, ccda_goal_weight_loss: str) -> None:
        """Test that start date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "startDate" in goal
        assert goal["startDate"] == "2024-01-15"

    def test_converts_target_with_due_date(self, ccda_goal_weight_loss: str) -> None:
        """Test that target with quantity and due date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "target" in goal
        assert len(goal["target"]) == 1

        target = goal["target"][0]

        # Check measure code
        assert "measure" in target
        loinc = next(
            (c for c in target["measure"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "29463-7"
        assert loinc["display"] == "Body weight"

        # Check detail quantity (value can be string or number in FHIR)
        assert "detailQuantity" in target
        assert target["detailQuantity"]["value"] in [160, "160"]
        assert target["detailQuantity"]["unit"] == "[lb_av]"  # UCUM unit
        assert target["detailQuantity"]["system"] == "http://unitsofmeasure.org"
        assert target["detailQuantity"]["code"] == "[lb_av]"

        # Check due date
        assert "dueDate" in target
        assert target["dueDate"] == "2024-07-15"

    def test_converts_expressed_by_patient(self, ccda_goal_weight_loss: str) -> None:
        """Test that expressedBy is correctly mapped to patient."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "expressedBy" in goal
        assert "reference" in goal["expressedBy"]
        assert goal["expressedBy"]["reference"].startswith("Patient/")

    def test_converts_priority(self, ccda_goal_with_priority: str) -> None:
        """Test that priority preference is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_with_priority, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "priority" in goal
        # Per FHIR R4B: CodeSystem canonical URI, not OID format
        assert goal["priority"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/goal-priority"
        assert goal["priority"]["coding"][0]["code"] == "high-priority"

    def test_converts_achievement_status(self, ccda_goal_with_progress: str) -> None:
        """Test that progress toward goal is correctly converted to achievement status."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_with_progress, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "achievementStatus" in goal
        # Per FHIR R4B: CodeSystem canonical URI, not OID format
        assert goal["achievementStatus"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/goal-achievement"
        assert goal["achievementStatus"]["coding"][0]["code"] == "in-progress"

    def test_converts_addresses_health_concern(self, ccda_goal_with_health_concern: str) -> None:
        """Test that health concern reference is correctly mapped to addresses."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_with_health_concern, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "addresses" in goal
        assert len(goal["addresses"]) >= 1
        # The reference should point to a Condition resource
        assert "reference" in goal["addresses"][0]
        assert goal["addresses"][0]["reference"].startswith("Condition/")

    def test_converts_target_range(self, ccda_goal_blood_pressure: str) -> None:
        """Test that target with range is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_blood_pressure, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "target" in goal

        # Find systolic BP target
        systolic_target = next(
            (t for t in goal["target"]
             if any(c.get("code") == "8480-6" for c in t.get("measure", {}).get("coding", []))),
            None
        )
        assert systolic_target is not None
        assert "detailRange" in systolic_target
        assert "high" in systolic_target["detailRange"]
        # Value can be string or number in FHIR
        assert systolic_target["detailRange"]["high"]["value"] in [140, "140"]

    def test_converts_qualitative_goal_without_target(self, ccda_goal_qualitative: str) -> None:
        """Test that qualitative goal without measurable target is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_qualitative, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "description" in goal
        assert "lifecycleStatus" in goal
        # Target should be omitted or empty for qualitative goals
        assert "target" not in goal or len(goal.get("target", [])) == 0

    def test_includes_us_core_profile(self, ccda_goal_weight_loss: str) -> None:
        """Test that US Core Goal profile is included in meta.profile."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "meta" in goal
        assert "profile" in goal["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-goal" in goal["meta"]["profile"]

    def test_has_subject_reference(self, ccda_goal_weight_loss: str) -> None:
        """Test that subject reference to patient is correctly set."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "subject" in goal
        assert "reference" in goal["subject"]
        assert goal["subject"]["reference"].startswith("Patient/")

    def test_has_identifier(self, ccda_goal_weight_loss: str) -> None:
        """Test that goal identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_goal_weight_loss, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is not None
        assert "identifier" in goal
        assert len(goal["identifier"]) >= 1
        assert "system" in goal["identifier"][0]
        assert "value" in goal["identifier"][0]

    def test_description_fallback_when_no_code(self, ccda_goal_narrative_only: str) -> None:
        """Test that Goal conversion fails when description cannot be determined.

        Verifies strict validation (consistent with Observation.code pattern):
        1. Try coded description first
        2. Fall back to narrative text extraction
        3. If neither available: FAIL conversion (no placeholder text)

        This ensures Goal resources are semantically meaningful - a goal without
        a description (what the objective is) is clinically useless.
        """
        ccda_doc = wrap_in_ccda_document(ccda_goal_narrative_only, GOALS_SECTION_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Goal should not be created when description is unavailable
        goal = _find_resource_in_bundle(bundle, "Goal")
        assert goal is None, "Goal should not be created without valid description"
