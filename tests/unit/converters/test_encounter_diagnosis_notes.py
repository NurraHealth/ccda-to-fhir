"""Unit tests for encounter diagnosis notes extraction.

Tests extraction of per-diagnosis notes from encounter narrative tables
and creation of DocumentReference resources.
"""

from __future__ import annotations

import base64

import pytest

from ccda_to_fhir.ccda.models.datatypes import CE
from ccda_to_fhir.ccda.models.section import Section, SectionComponent, StructuredBody
from ccda_to_fhir.ccda.models.struc_doc import (
    StrucDocText,
    Table,
    TableBody,
    TableDataCell,
    TableHead,
    TableHeaderCell,
    TableRow,
)
from ccda_to_fhir.converters.encounter_diagnosis_notes import (
    DiagnosisNote,
    build_condition_snomed_map,
    create_diagnosis_note_doc_refs,
    extract_diagnosis_notes_from_section,
    extract_encounter_diagnosis_notes,
)
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.id_generator import reset_id_cache


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def _reset_ids():
    reset_id_cache()
    yield
    reset_id_cache()


@pytest.fixture
def registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


def _make_header_row(*headers: str) -> TableRow:
    return TableRow(th=[TableHeaderCell.model_validate({"_text": h}) for h in headers])


def _make_data_cells(*cells_data: str | tuple[str, str | None]) -> list[TableDataCell]:
    """Create data cells. Each cell is either text or (text, content_id)."""
    cells: list[TableDataCell] = []
    for cell_input in cells_data:
        if isinstance(cell_input, tuple):
            text_val, content_id = cell_input
            if content_id:
                cells.append(TableDataCell.model_validate(
                    {"_text": None, "content": [{"_text": text_val, "i_d": content_id}]}
                ))
            else:
                cells.append(TableDataCell.model_validate({"_text": text_val}))
        else:
            cells.append(TableDataCell.model_validate({"_text": cell_input}))
    return cells


def _make_encounter_table(
    headers: list[str],
    rows: list[list[str | tuple[str, str | None]]],
) -> Table:
    header_row = _make_header_row(*headers)
    data_rows = []
    for row_data in rows:
        tds = _make_data_cells(*row_data)
        data_rows.append(TableRow(td=tds))
    return Table(
        thead=TableHead(tr=[header_row]),
        tbody=[TableBody(tr=data_rows)],
    )


def _make_encounters_section(
    table: Table,
    entries: list | None = None,
) -> Section:
    return Section(
        code=CE(code="46240-8", code_system="2.16.840.1.113883.6.1"),
        text=StrucDocText(table=[table]),
        entry=entries,
    )


# ============================================================================
# extract_diagnosis_notes_from_section
# ============================================================================


class TestExtractDiagnosisNotes:
    def test_extracts_notes_from_table(self) -> None:
        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [
                    ("1234", "encounter1234"),
                    "Essential hypertension",
                    "59621000",
                    "Blood pressure not within goal. Referred to cardiology.",
                ],
            ],
        )
        section = _make_encounters_section(table)
        notes = extract_diagnosis_notes_from_section(section)

        assert len(notes) == 1
        assert notes[0].encounter_content_id == "encounter1234"
        assert notes[0].diagnosis_display == "Essential hypertension"
        assert notes[0].snomed_code == "59621000"
        assert "Blood pressure" in notes[0].note_text

    def test_skips_empty_notes(self) -> None:
        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [("1234", "encounter1234"), "Hypertension", "59621000", ""],
                [("1234", "encounter1234"), "Diabetes", "44054006", "Monitor HbA1c."],
            ],
        )
        section = _make_encounters_section(table)
        notes = extract_diagnosis_notes_from_section(section)

        assert len(notes) == 1
        assert notes[0].diagnosis_display == "Diabetes"

    def test_no_diagnosis_note_column(self) -> None:
        table = _make_encounter_table(
            headers=["Encounter ID", "Diagnosis/Indication"],
            rows=[
                [("1234", "enc1"), "Hypertension"],
            ],
        )
        section = _make_encounters_section(table)
        notes = extract_diagnosis_notes_from_section(section)
        assert notes == []

    def test_no_table(self) -> None:
        section = Section(
            code=CE(code="46240-8", code_system="2.16.840.1.113883.6.1"),
            text=StrucDocText(text="No table here"),
        )
        notes = extract_diagnosis_notes_from_section(section)
        assert notes == []

    def test_no_text(self) -> None:
        section = Section(
            code=CE(code="46240-8", code_system="2.16.840.1.113883.6.1"),
        )
        notes = extract_diagnosis_notes_from_section(section)
        assert notes == []

    def test_multiple_diagnoses_same_encounter(self) -> None:
        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [
                    ("4068", "encounter4068"),
                    "Hypertension",
                    "59621000",
                    "BP above goal.",
                ],
                # Continuation row (empty encounter ID)
                ["", "Dyslipidemia", "370992007", "LDL within goal."],
            ],
        )
        section = _make_encounters_section(table)
        notes = extract_diagnosis_notes_from_section(section)

        assert len(notes) == 2
        # First row has encounter ID
        assert notes[0].encounter_content_id == "encounter4068"
        # Second row inherits encounter ID
        assert notes[1].encounter_content_id == "encounter4068"
        assert notes[1].diagnosis_display == "Dyslipidemia"

    def test_missing_diagnosis_display_uses_fallback(self) -> None:
        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [("1234", "enc1"), "", "", "Some clinical note."],
            ],
        )
        section = _make_encounters_section(table)
        notes = extract_diagnosis_notes_from_section(section)

        assert len(notes) == 1
        assert notes[0].diagnosis_display == "Unknown diagnosis"


# ============================================================================
# build_condition_snomed_map
# ============================================================================


class TestBuildConditionSnomedMap:
    def test_maps_snomed_codes(self) -> None:
        conditions = [
            {
                "resourceType": "Condition",
                "id": "cond-1",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "59621000"},
                    ]
                },
            },
            {
                "resourceType": "Condition",
                "id": "cond-2",
                "code": {
                    "coding": [
                        {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "I10"},
                        {"system": "http://snomed.info/sct", "code": "44054006"},
                    ]
                },
            },
        ]
        result = build_condition_snomed_map(conditions)
        assert result == {"59621000": ["cond-1"], "44054006": ["cond-2"]}

    def test_duplicate_snomed_codes(self) -> None:
        conditions = [
            {
                "resourceType": "Condition",
                "id": "cond-1",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "59621000"},
                    ]
                },
            },
            {
                "resourceType": "Condition",
                "id": "cond-2",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "59621000"},
                    ]
                },
            },
        ]
        result = build_condition_snomed_map(conditions)
        assert result == {"59621000": ["cond-1", "cond-2"]}

    def test_empty_conditions(self) -> None:
        assert build_condition_snomed_map([]) == {}

    def test_no_snomed_coding(self) -> None:
        conditions = [
            {
                "resourceType": "Condition",
                "id": "cond-1",
                "code": {
                    "coding": [
                        {"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": "I10"},
                    ]
                },
            },
        ]
        assert build_condition_snomed_map(conditions) == {}

    def test_missing_code(self) -> None:
        conditions = [{"resourceType": "Condition", "id": "cond-1"}]
        assert build_condition_snomed_map(conditions) == {}


# ============================================================================
# create_diagnosis_note_doc_refs
# ============================================================================


class TestCreateDiagnosisNoteDocRefs:
    def test_creates_doc_ref(self, registry: ReferenceRegistry) -> None:
        notes = [
            DiagnosisNote(
                encounter_content_id="enc1",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="Blood pressure above goal.",
            ),
        ]
        encounter_map = {"enc1": "encounter-uuid-1"}
        condition_map: dict[str, list[str]] = {"59621000": ["condition-uuid-1"]}

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map=encounter_map,
            condition_snomed_map=condition_map,
            reference_registry=registry,
            encounter_date_map={"encounter-uuid-1": "2024-01-22T12:02:39-05:00"},
        )

        assert len(doc_refs) == 1
        dr = doc_refs[0]
        assert dr["resourceType"] == "DocumentReference"
        assert dr["status"] == "current"
        assert dr["date"] == "2024-01-22T12:02:39-05:00"

        # Subject
        assert dr["subject"] == {"reference": "urn:uuid:test-patient"}

        # Content
        content = dr["content"][0]["attachment"]
        assert content["contentType"] == "text/plain"
        decoded = base64.b64decode(content["data"]).decode("utf-8")
        assert decoded == "Blood pressure above goal."

        # Context
        context = dr["context"]
        assert context["encounter"] == [{"reference": "urn:uuid:encounter-uuid-1"}]
        assert context["related"] == [{"reference": "urn:uuid:condition-uuid-1"}]

        # Type and description
        assert dr["type"]["text"] == "Diagnosis Note - Hypertension"
        assert dr["description"] == "Diagnosis Note - Hypertension"

        # Category
        assert dr["category"][0]["coding"][0]["code"] == "clinical-note"

    def test_multiple_conditions_same_snomed(self, registry: ReferenceRegistry) -> None:
        notes = [
            DiagnosisNote(
                encounter_content_id="enc1",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="BP note.",
            ),
        ]
        condition_map: dict[str, list[str]] = {"59621000": ["cond-1", "cond-2"]}

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map=condition_map,
            reference_registry=registry,
        )

        assert len(doc_refs) == 1
        related = doc_refs[0]["context"]["related"]
        assert related == [
            {"reference": "urn:uuid:cond-1"},
            {"reference": "urn:uuid:cond-2"},
        ]

    def test_no_encounter_link(self, registry: ReferenceRegistry) -> None:
        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="Hypertension",
                snomed_code=None,
                note_text="Some note.",
            ),
        ]
        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={},
            reference_registry=registry,
        )

        assert len(doc_refs) == 1
        # No context since no encounter or condition links
        assert "context" not in doc_refs[0]

    def test_condition_link_without_encounter(self, registry: ReferenceRegistry) -> None:
        notes = [
            DiagnosisNote(
                encounter_content_id=None,
                diagnosis_display="Diabetes",
                snomed_code="44054006",
                note_text="Monitor HbA1c.",
            ),
        ]
        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={"44054006": ["cond-1"]},
            reference_registry=registry,
        )

        assert len(doc_refs) == 1
        context = doc_refs[0]["context"]
        assert "encounter" not in context
        assert context["related"] == [{"reference": "urn:uuid:cond-1"}]

    def test_deterministic_ids(self, registry: ReferenceRegistry) -> None:
        notes = [
            DiagnosisNote(
                encounter_content_id="enc1",
                diagnosis_display="Hypertension",
                snomed_code="59621000",
                note_text="Note text.",
            ),
        ]
        doc_refs_1 = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={},
            reference_registry=registry,
        )
        doc_refs_2 = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map={},
            condition_snomed_map={},
            reference_registry=registry,
        )
        assert doc_refs_1[0]["id"] == doc_refs_2[0]["id"]


# ============================================================================
# extract_encounter_diagnosis_notes (integration)
# ============================================================================


class TestExtractEncounterDiagnosisNotesIntegration:
    def test_no_encounters_section(self, registry: ReferenceRegistry) -> None:
        body = StructuredBody(component=[])
        result = extract_encounter_diagnosis_notes(body, [], [], registry)
        assert result == []

    def test_non_encounters_section_skipped(self, registry: ReferenceRegistry) -> None:
        section = Section(
            code=CE(code="11450-4", code_system="2.16.840.1.113883.6.1"),
            text=StrucDocText(
                table=[
                    _make_encounter_table(
                        headers=["Diagnosis Note"],
                        rows=[["Should not be extracted"]],
                    )
                ]
            ),
        )
        body = StructuredBody(component=[SectionComponent(section=section)])
        result = extract_encounter_diagnosis_notes(body, [], [], registry)
        assert result == []

    def test_full_pipeline(self, registry: ReferenceRegistry) -> None:
        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [
                    ("4068", "encounter4068"),
                    "Hypertension",
                    "59621000",
                    "BP above goal. Referred to cardiology.",
                ],
            ],
        )
        section = _make_encounters_section(table)
        body = StructuredBody(component=[SectionComponent(section=section)])

        encounters = [
            {
                "resourceType": "Encounter",
                "id": "enc-fhir-1",
                "period": {"start": "2024-01-22T12:02:39-05:00"},
            }
        ]
        conditions = [
            {
                "resourceType": "Condition",
                "id": "cond-fhir-1",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "59621000"},
                    ]
                },
            }
        ]

        result = extract_encounter_diagnosis_notes(
            body, encounters, conditions, registry
        )

        assert len(result) == 1
        dr = result[0]
        assert dr["resourceType"] == "DocumentReference"
        assert dr["status"] == "current"
        assert dr["description"] == "Diagnosis Note - Hypertension"

        # Content is base64-encoded note text
        decoded = base64.b64decode(dr["content"][0]["attachment"]["data"]).decode()
        assert "BP above goal" in decoded

        # Condition link via SNOMED matching
        context = dr["context"]
        assert context["related"] == [{"reference": "urn:uuid:cond-fhir-1"}]

    def test_full_pipeline_with_encounter_linking(self, registry: ReferenceRegistry) -> None:
        """Test encounter linking via section entries with text references."""
        from ccda_to_fhir.ccda.models.datatypes import ED, II, TEL
        from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
        from ccda_to_fhir.ccda.models.section import Entry
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        enc_root = "2.16.840.1.113883.19.5"
        enc_ext = "4068"
        fhir_enc_id = generate_id_from_identifiers("Encounter", enc_root, enc_ext)

        table = _make_encounter_table(
            headers=[
                "Encounter ID",
                "Diagnosis/Indication",
                "Diagnosis SNOMED-CT Code",
                "Diagnosis Note",
            ],
            rows=[
                [
                    ("4068", "encounter4068"),
                    "Hypertension",
                    "59621000",
                    "BP above goal.",
                ],
            ],
        )

        cda_encounter = CDAEncounter(
            id=[II(root=enc_root, extension=enc_ext)],
            text=ED(reference=TEL(value="#encounter4068")),
        )
        entry = Entry(encounter=cda_encounter)
        section = _make_encounters_section(table, entries=[entry])
        body = StructuredBody(component=[SectionComponent(section=section)])

        encounters = [
            {
                "resourceType": "Encounter",
                "id": fhir_enc_id,
                "period": {"start": "2024-01-22T12:02:39-05:00"},
            }
        ]
        conditions: list[dict] = []

        result = extract_encounter_diagnosis_notes(
            body, encounters, conditions, registry
        )

        assert len(result) == 1
        dr = result[0]
        context = dr["context"]
        assert context["encounter"] == [{"reference": f"urn:uuid:{fhir_enc_id}"}]
        assert dr["date"] == "2024-01-22T12:02:39-05:00"


# ============================================================================
# Author references
# ============================================================================


class TestAuthorReferences:
    """Tests for author references on diagnosis note DocumentReferences."""

    def test_author_references_set_on_doc_ref(self, registry: ReferenceRegistry) -> None:
        notes = [DiagnosisNote(
            encounter_content_id=None,
            diagnosis_display="Pneumonia",
            snomed_code="233604007",
            note_text="Improving on antibiotics.",
        )]
        author_refs = [{"reference": "urn:uuid:prac-1"}]
        result = create_diagnosis_note_doc_refs(
            notes, {}, {}, registry, author_references=author_refs
        )
        assert len(result) == 1
        assert result[0]["author"] == [{"reference": "urn:uuid:prac-1"}]

    def test_multiple_authors(self, registry: ReferenceRegistry) -> None:
        notes = [DiagnosisNote(
            encounter_content_id=None,
            diagnosis_display="HTN",
            snomed_code=None,
            note_text="Blood pressure controlled.",
        )]
        author_refs = [
            {"reference": "urn:uuid:prac-1"},
            {"reference": "urn:uuid:prac-2"},
        ]
        result = create_diagnosis_note_doc_refs(
            notes, {}, {}, registry, author_references=author_refs
        )
        assert len(result[0]["author"]) == 2

    def test_no_author_references_omits_field(self, registry: ReferenceRegistry) -> None:
        notes = [DiagnosisNote(
            encounter_content_id=None,
            diagnosis_display="Pneumonia",
            snomed_code=None,
            note_text="Improving.",
        )]
        result = create_diagnosis_note_doc_refs(notes, {}, {}, registry)
        assert "author" not in result[0]

    def test_empty_author_references_omits_field(self, registry: ReferenceRegistry) -> None:
        notes = [DiagnosisNote(
            encounter_content_id=None,
            diagnosis_display="Pneumonia",
            snomed_code=None,
            note_text="Improving.",
        )]
        result = create_diagnosis_note_doc_refs(
            notes, {}, {}, registry, author_references=[]
        )
        assert "author" not in result[0]
