"""Unit tests for display text in clinical resource references.

Tests that Observation, Condition, and Medication references include
display text when source data provides it (FHIR Reference.display).
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, II, IVL_TS, TS
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.converters.references import ReferenceRegistry


# ============================================================================
# Fixtures
# ============================================================================


def _make_registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


@pytest.fixture
def registry() -> ReferenceRegistry:
    return _make_registry()


def _register(registry: ReferenceRegistry, resource_type: str, resource_id: str) -> None:
    """Helper to register a minimal resource in the registry."""
    registry.register_resource({"resourceType": resource_type, "id": resource_id})


# ============================================================================
# base.py: extract_reasons_from_entry_relationships
# ============================================================================


class TestReasonReferenceDisplay:
    """Tests for display text on Condition reasonReference from base converter."""

    def _make_converter(self, registry: ReferenceRegistry):
        from ccda_to_fhir.converters.procedure import ProcedureConverter

        return ProcedureConverter(reference_registry=registry)

    def _make_problem_observation(
        self,
        *,
        obs_root: str = "1.2.3.4.5",
        obs_ext: str | None = "obs-1",
        value_code: str = "233604007",
        value_system: str = "2.16.840.1.113883.6.96",
        value_display: str | None = "Pneumonia",
    ) -> Observation:
        obs = Observation(
            id=[II(root=obs_root, extension=obs_ext)],
            template_id=[II(root=TemplateIds.PROBLEM_OBSERVATION)],
            code=CE(code="ASSERTION", code_system="2.16.840.1.113883.5.4"),
            status_code=CS(code="completed"),
            effective_time=IVL_TS(low=TS(value="20240101")),
            value=CD(
                code=value_code,
                code_system=value_system,
                display_name=value_display,
            ),
        )
        return obs

    def test_reason_reference_includes_display(self, registry: ReferenceRegistry) -> None:
        obs = self._make_problem_observation()
        converter = self._make_converter(registry)

        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        condition_id = generate_id_from_identifiers("Condition", "1.2.3.4.5", "obs-1")
        _register(registry, "Condition", condition_id)

        entry_rels = [EntryRelationship(type_code="RSON", observation=obs)]
        result = converter.extract_reasons_from_entry_relationships(entry_rels)

        refs = result["references"]
        assert len(refs) == 1
        assert refs[0]["reference"] == f"urn:uuid:{condition_id}"
        assert refs[0]["display"] == "Pneumonia"

    def test_reason_reference_no_display_when_none(self, registry: ReferenceRegistry) -> None:
        obs = self._make_problem_observation(value_display=None)
        converter = self._make_converter(registry)

        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        condition_id = generate_id_from_identifiers("Condition", "1.2.3.4.5", "obs-1")
        _register(registry, "Condition", condition_id)

        entry_rels = [EntryRelationship(type_code="RSON", observation=obs)]
        result = converter.extract_reasons_from_entry_relationships(entry_rels)

        refs = result["references"]
        assert len(refs) == 1
        assert "display" not in refs[0]


# ============================================================================
# condition.py: _extract_evidence
# ============================================================================


class TestConditionEvidenceDisplay:
    """Tests for display text on Observation evidence detail references."""

    def _make_converter(self, registry: ReferenceRegistry):
        from ccda_to_fhir.converters.condition import ConditionConverter

        return ConditionConverter(reference_registry=registry)

    def test_evidence_detail_includes_display(self, registry: ReferenceRegistry) -> None:
        converter = self._make_converter(registry)

        supporting_obs = Observation()
        supporting_obs.id = [II(root="2.2.2.2", extension="support-1")]
        supporting_obs.code = CE(
            code="404684003",
            code_system="2.16.840.1.113883.6.96",
            display_name="Clinical finding",
        )

        parent_obs = Observation()
        parent_obs.entry_relationship = [
            EntryRelationship(type_code="SPRT", observation=supporting_obs)
        ]

        result = converter._extract_evidence(parent_obs)
        assert result is not None
        assert len(result) == 1
        detail_ref = result[0]["detail"][0]
        assert detail_ref["display"] == "Clinical finding"

    def test_evidence_detail_no_display_when_code_missing(self, registry: ReferenceRegistry) -> None:
        converter = self._make_converter(registry)

        supporting_obs = Observation()
        supporting_obs.id = [II(root="2.2.2.2", extension="support-1")]

        parent_obs = Observation()
        parent_obs.entry_relationship = [
            EntryRelationship(type_code="SPRT", observation=supporting_obs)
        ]

        result = converter._extract_evidence(parent_obs)
        assert result is not None
        assert len(result) == 1
        detail_ref = result[0]["detail"][0]
        assert "display" not in detail_ref

    def test_evidence_detail_no_display_when_display_name_none(self, registry: ReferenceRegistry) -> None:
        converter = self._make_converter(registry)

        supporting_obs = Observation()
        supporting_obs.id = [II(root="2.2.2.2", extension="support-1")]
        supporting_obs.code = CE(
            code="404684003",
            code_system="2.16.840.1.113883.6.96",
            display_name=None,
        )

        parent_obs = Observation()
        parent_obs.entry_relationship = [
            EntryRelationship(type_code="SPRT", observation=supporting_obs)
        ]

        result = converter._extract_evidence(parent_obs)
        assert result is not None
        detail_ref = result[0]["detail"][0]
        assert "display" not in detail_ref


# ============================================================================
# diagnostic_report.py: convert() result references
# ============================================================================


class TestDiagnosticReportResultDisplay:
    """Tests for display text on Observation result references in DiagnosticReport."""

    def test_result_reference_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.datatypes import CS
        from ccda_to_fhir.ccda.models.organizer import OrganizerComponent, Organizer
        from ccda_to_fhir.converters.diagnostic_report import DiagnosticReportConverter

        obs = Observation(
            id=[II(root="3.3.3.3", extension="result-obs-1")],
            code=CE(
                code="2339-0",
                code_system="2.16.840.1.113883.6.1",
                display_name="Glucose [Mass/volume] in Blood",
            ),
            status_code=CS(code="completed"),
        )

        organizer = Organizer(
            classCode="BATTERY",
            id=[II(root="4.4.4.4", extension="report-1")],
            code=CE(
                code="24323-8",
                code_system="2.16.840.1.113883.6.1",
                display_name="Comprehensive metabolic 2000 panel",
            ),
            status_code=CS(code="completed"),
            component=[OrganizerComponent(observation=obs)],
        )

        converter = DiagnosticReportConverter(reference_registry=registry)
        report, observations = converter.convert(organizer)

        result_refs = report.get("result", [])
        assert len(result_refs) == 1
        assert result_refs[0]["display"] == "Glucose [Mass/volume] in Blood"

    def test_result_reference_no_display_when_display_name_missing(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.datatypes import CS
        from ccda_to_fhir.ccda.models.organizer import OrganizerComponent, Organizer
        from ccda_to_fhir.converters.diagnostic_report import DiagnosticReportConverter

        obs = Observation(
            id=[II(root="3.3.3.3", extension="result-obs-2")],
            code=CE(code="2339-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="completed"),
        )

        organizer = Organizer(
            classCode="BATTERY",
            id=[II(root="4.4.4.4", extension="report-2")],
            code=CE(
                code="24323-8",
                code_system="2.16.840.1.113883.6.1",
            ),
            status_code=CS(code="completed"),
            component=[OrganizerComponent(observation=obs)],
        )

        converter = DiagnosticReportConverter(reference_registry=registry)
        report, _ = converter.convert(organizer)

        result_refs = report.get("result", [])
        assert len(result_refs) == 1
        assert "display" not in result_refs[0]


# ============================================================================
# careplan.py: _create_outcome_reference
# ============================================================================


class TestCarePlanOutcomeDisplay:
    """Tests for display text on Observation outcome references in CarePlan."""

    def test_outcome_reference_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.careplan import CarePlanConverter

        converter = CarePlanConverter(reference_registry=registry)

        outcome_entry = Mock()
        outcome_entry.id = [Mock(root="5.5.5.5", extension="outcome-1")]
        outcome_entry.code = CE(
            code="55607006",
            code_system="2.16.840.1.113883.6.96",
            display_name="Problem",
        )

        resource_id = converter._generate_resource_id_from_entry(outcome_entry, "observation")
        if resource_id:
            _register(registry, "Observation", resource_id)

        result = converter._create_outcome_reference(outcome_entry)
        assert result is not None
        assert result["display"] == "Problem"

    def test_outcome_reference_no_display_when_code_missing(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.careplan import CarePlanConverter

        converter = CarePlanConverter(reference_registry=registry)

        outcome_entry = Mock()
        outcome_entry.id = [Mock(root="5.5.5.5", extension="outcome-2")]
        outcome_entry.code = None

        resource_id = converter._generate_resource_id_from_entry(outcome_entry, "observation")
        if resource_id:
            _register(registry, "Observation", resource_id)

        result = converter._create_outcome_reference(outcome_entry)
        if result:
            assert "display" not in result


# ============================================================================
# encounter.py: _extract_diagnoses
# ============================================================================


class TestEncounterDiagnosisDisplay:
    """Tests for display text on Condition diagnosis references in Encounter."""

    def _make_converter(self, registry: ReferenceRegistry):
        from ccda_to_fhir.converters.encounter import EncounterConverter

        return EncounterConverter(reference_registry=registry)

    def test_diagnosis_condition_ref_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.act import Act

        converter = self._make_converter(registry)

        obs = Observation()
        obs.id = [II(root="6.6.6.6", extension="diag-obs-1")]
        obs.value = CD(
            code="59621000",
            code_system="2.16.840.1.113883.6.96",
            display_name="Essential hypertension",
        )

        diag_act = Act()
        diag_act.template_id = [II(root=TemplateIds.ENCOUNTER_DIAGNOSIS)]
        diag_act.entry_relationship = [
            EntryRelationship(type_code="SUBJ", observation=obs)
        ]

        entry_rel = EntryRelationship(type_code="COMP", act=diag_act)

        diagnoses = converter._extract_diagnoses([entry_rel])
        assert len(diagnoses) == 1
        condition_ref = diagnoses[0]["condition"]
        assert condition_ref["display"] == "Essential hypertension"

    def test_diagnosis_condition_ref_no_display_when_value_missing(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.act import Act

        converter = self._make_converter(registry)

        obs = Observation()
        obs.id = [II(root="6.6.6.6", extension="diag-obs-2")]

        diag_act = Act()
        diag_act.template_id = [II(root=TemplateIds.ENCOUNTER_DIAGNOSIS)]
        diag_act.entry_relationship = [
            EntryRelationship(type_code="SUBJ", observation=obs)
        ]

        entry_rel = EntryRelationship(type_code="COMP", act=diag_act)

        diagnoses = converter._extract_diagnoses([entry_rel])
        assert len(diagnoses) == 1
        condition_ref = diagnoses[0]["condition"]
        assert "display" not in condition_ref

    def test_diagnosis_condition_ref_no_display_when_display_name_none(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.act import Act

        converter = self._make_converter(registry)

        obs = Observation()
        obs.id = [II(root="6.6.6.6", extension="diag-obs-3")]
        obs.value = CD(
            code="59621000",
            code_system="2.16.840.1.113883.6.96",
            display_name=None,
        )

        diag_act = Act()
        diag_act.template_id = [II(root=TemplateIds.ENCOUNTER_DIAGNOSIS)]
        diag_act.entry_relationship = [
            EntryRelationship(type_code="SUBJ", observation=obs)
        ]

        entry_rel = EntryRelationship(type_code="COMP", act=diag_act)

        diagnoses = converter._extract_diagnoses([entry_rel])
        assert len(diagnoses) == 1
        condition_ref = diagnoses[0]["condition"]
        assert "display" not in condition_ref


# ============================================================================
# encounter_diagnosis_notes.py: _build_doc_ref related references
# ============================================================================


class TestEncounterDiagnosisNotesDisplay:
    """Tests for display text on Condition related references in diagnosis note DocumentReferences."""

    def test_related_condition_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.encounter_diagnosis_notes import (
            DiagnosisNote,
            create_diagnosis_note_doc_refs,
        )

        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="Type 2 Diabetes Mellitus",
                snomed_code="44054006",
                note_text="Monitor HbA1c levels.",
            ),
        ]
        condition_map: dict[str, list[str]] = {"44054006": ["cond-abc"]}

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map=condition_map,
            reference_registry=registry,
        )

        assert len(doc_refs) == 1
        related = doc_refs[0]["context"]["related"]
        assert len(related) == 1
        assert related[0]["display"] == "Type 2 Diabetes Mellitus"

    def test_related_condition_no_display_when_diagnosis_display_empty(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.encounter_diagnosis_notes import (
            DiagnosisNote,
            create_diagnosis_note_doc_refs,
        )

        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="",
                snomed_code="44054006",
                note_text="Some note.",
            ),
        ]
        condition_map: dict[str, list[str]] = {"44054006": ["cond-xyz"]}

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map=condition_map,
            reference_registry=registry,
        )

        related = doc_refs[0]["context"]["related"]
        assert "display" not in related[0]


# ============================================================================
# medication_request.py: _extract_medication medicationReference
# ============================================================================


class TestMedicationReferenceDisplay:
    """Tests for display text on Medication references in MedicationRequest."""

    def test_medication_reference_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.datatypes import CS
        from ccda_to_fhir.ccda.models.substance_administration import (
            Consumable,
            ManufacturedMaterial,
            ManufacturedProduct,
            SubstanceAdministration,
        )
        from ccda_to_fhir.converters.medication_request import MedicationRequestConverter

        material = ManufacturedMaterial()
        material.code = CE(
            code="197361",
            code_system="2.16.840.1.113883.6.88",
            display_name="Lisinopril 10 MG Oral Tablet",
        )
        material.lot_number_text = "LOT123"

        product = ManufacturedProduct()
        product.manufactured_material = material

        consumable = Consumable()
        consumable.manufactured_product = product

        sa = SubstanceAdministration()
        sa.id = [II(root="7.7.7.7", extension="med-1")]
        sa.consumable = consumable
        sa.status_code = CS(code="active")

        converter = MedicationRequestConverter(reference_registry=registry)
        result = converter._extract_medication(sa)

        assert result is not None
        assert "medicationReference" in result
        med_ref = result["medicationReference"]
        assert med_ref["display"] == "Lisinopril 10 MG Oral Tablet"

    def test_medication_reference_no_display_when_display_name_none(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.ccda.models.datatypes import CS
        from ccda_to_fhir.ccda.models.substance_administration import (
            Consumable,
            ManufacturedMaterial,
            ManufacturedProduct,
            SubstanceAdministration,
        )
        from ccda_to_fhir.converters.medication_request import MedicationRequestConverter

        material = ManufacturedMaterial()
        material.code = CE(
            code="197361",
            code_system="2.16.840.1.113883.6.88",
            display_name=None,
        )
        material.lot_number_text = "LOT456"

        product = ManufacturedProduct()
        product.manufactured_material = material

        consumable = Consumable()
        consumable.manufactured_product = product

        sa = SubstanceAdministration()
        sa.id = [II(root="7.7.7.7", extension="med-2")]
        sa.consumable = consumable
        sa.status_code = CS(code="active")

        converter = MedicationRequestConverter(reference_registry=registry)
        result = converter._extract_medication(sa)

        assert result is not None
        if "medicationReference" in result:
            assert "display" not in result["medicationReference"]
