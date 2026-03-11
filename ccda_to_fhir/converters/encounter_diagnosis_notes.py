"""Extract per-diagnosis notes from encounter narrative tables.

Encounter sections (LOINC 46240-8) in some EHR systems (e.g. Athena) embed
per-diagnosis clinical notes in the narrative table's "Diagnosis Note" column.
These are A&P notes specific to each condition seen during the encounter.

This module parses those narrative tables and creates FHIR DocumentReference
resources for each non-empty diagnosis note, linked to the Encounter and
(when matchable) the Condition.
"""

from __future__ import annotations

import base64
import logging

from ccda_to_fhir.utils import fhir_date_to_instant
from dataclasses import dataclass

from ccda_to_fhir.ccda.models.section import Section, StructuredBody
from ccda_to_fhir.ccda.models.struc_doc import (
    StrucDocText,
    Table,
    TableDataCell,
    TableHeaderCell,
    TableRow,
)
from ccda_to_fhir.id_generator import generate_id_from_identifiers
from ccda_to_fhir.types import FHIRResourceDict, JSONObject
from ccda_to_fhir.utils.struc_doc_utils import extract_cell_text

from .references import ReferenceRegistry

logger = logging.getLogger(__name__)

# LOINC code for the Encounters section
_ENCOUNTERS_SECTION_CODE = "46240-8"

# Header names we look for (case-insensitive)
_DIAGNOSIS_NOTE_HEADER = "diagnosis note"
_DIAGNOSIS_HEADER = "diagnosis/indication"
_SNOMED_HEADER = "diagnosis snomed-ct code"
_ENCOUNTER_ID_HEADER = "encounter id"


@dataclass(frozen=True)
class DiagnosisNote:
    """A single diagnosis note extracted from the encounter narrative table."""

    encounter_content_id: str | None
    diagnosis_display: str
    snomed_code: str | None
    note_text: str


def extract_diagnosis_notes_from_section(
    section: Section,
) -> list[DiagnosisNote]:
    """Extract diagnosis notes from an encounters section narrative table.

    Looks for a table with a "Diagnosis Note" column header. For each row with
    a non-empty note cell, extracts the diagnosis name, SNOMED code, and note.

    Args:
        section: The encounters Section (LOINC 46240-8)

    Returns:
        List of DiagnosisNote objects for rows with non-empty notes
    """
    if not section.text:
        return []

    narrative: StrucDocText = section.text
    if not narrative.table:
        return []

    results: list[DiagnosisNote] = []
    for table in narrative.table:
        results.extend(_extract_from_table(table))
    return results


def _extract_from_table(table: Table) -> list[DiagnosisNote]:
    """Extract diagnosis notes from a single narrative table."""
    if not table.thead or not table.thead.tr:
        return []

    # Find column indices from header row
    header_row = table.thead.tr[0]
    col_map = _build_column_map(header_row)

    note_col = col_map.get(_DIAGNOSIS_NOTE_HEADER)
    if note_col is None:
        return []  # No "Diagnosis Note" column

    diag_col = col_map.get(_DIAGNOSIS_HEADER)
    snomed_col = col_map.get(_SNOMED_HEADER)
    enc_id_col = col_map.get(_ENCOUNTER_ID_HEADER)

    if not table.tbody:
        return []

    results: list[DiagnosisNote] = []
    # Athena-specific: the first row for each encounter has a content ID in the
    # encounter ID cell; subsequent diagnosis rows for the same encounter leave
    # this cell empty ("continuation rows"). We track the most recent encounter
    # content ID so continuation rows inherit it.
    current_encounter_id: str | None = None

    for tbody in table.tbody:
        if not tbody.tr:
            continue
        for row in tbody.tr:
            cells = row.td or []

            # Track the most recent encounter content ID
            if enc_id_col is not None and enc_id_col < len(cells):
                enc_cell = cells[enc_id_col]
                enc_id = _extract_content_id(enc_cell)
                if enc_id:
                    current_encounter_id = enc_id

            # Get note text
            note_text = _get_cell_text(cells, note_col)
            if not note_text:
                continue

            # Get diagnosis display
            diagnosis_display = _get_cell_text(cells, diag_col) if diag_col is not None else ""
            if not diagnosis_display:
                diagnosis_display = "Unknown diagnosis"

            # Get SNOMED code
            snomed_code = _get_cell_text(cells, snomed_col) if snomed_col is not None else None

            results.append(
                DiagnosisNote(
                    encounter_content_id=current_encounter_id,
                    diagnosis_display=diagnosis_display,
                    snomed_code=snomed_code,
                    note_text=note_text,
                )
            )

    return results


def _build_column_map(header_row: TableRow) -> dict[str, int]:
    """Map lowercase header text to column index."""
    col_map: dict[str, int] = {}
    cells: list[TableHeaderCell] = header_row.th or []
    for i, cell in enumerate(cells):
        text = ""
        if cell.text:
            text = cell.text.strip()
        if text:
            col_map[text.lower()] = i
    return col_map


def _extract_content_id(cell: TableDataCell) -> str | None:
    """Extract the ID attribute from a content element inside a cell.

    The encounter ID cell typically looks like:
        <td><content ID="encounter123">123</content></td>
    """
    if cell.content:
        for content in cell.content:
            if content.id_attr:
                return content.id_attr
    return None


def _get_cell_text(cells: list[TableDataCell], col_idx: int) -> str:
    """Get trimmed text from a cell at the given index."""
    if col_idx >= len(cells):
        return ""
    return extract_cell_text(cells[col_idx]).strip()


def create_diagnosis_note_doc_refs(
    notes: list[DiagnosisNote],
    encounter_map: dict[str, str],
    condition_snomed_map: dict[str, list[str]],
    reference_registry: ReferenceRegistry,
    encounter_date_map: dict[str, str] | None = None,
    author_references: list[JSONObject] | None = None,
    fallback_encounter_reference: str | None = None,
    fallback_encounter_date: str | None = None,
) -> list[FHIRResourceDict]:
    """Create DocumentReference resources for extracted diagnosis notes.

    Args:
        notes: Diagnosis notes extracted from the narrative table
        encounter_map: Maps encounter content ID -> FHIR Encounter resource ID
        condition_snomed_map: Maps SNOMED code -> list of FHIR Condition resource IDs
        reference_registry: Reference registry (for patient reference)
        encounter_date_map: Maps FHIR Encounter resource ID -> date string
        author_references: Optional author references from document header
        fallback_encounter_reference: urn:uuid reference from encompassingEncounter,
            used when body encounter mapping fails
        fallback_encounter_date: Date from encompassingEncounter, used when body
            encounter mapping fails

    Returns:
        List of DocumentReference resources
    """
    date_map = encounter_date_map or {}
    doc_refs: list[FHIRResourceDict] = []

    for note in notes:
        encounter_id = encounter_map.get(note.encounter_content_id or "") if note.encounter_content_id else None
        encounter_date = date_map.get(encounter_id) if encounter_id else None

        # Fall back to encompassingEncounter when body encounter mapping fails
        encounter_ref: str | None = f"urn:uuid:{encounter_id}" if encounter_id else None
        if encounter_ref is None:
            encounter_ref = fallback_encounter_reference
        if encounter_date is None:
            encounter_date = fallback_encounter_date

        doc_ref = _build_doc_ref(
            note=note,
            encounter_reference=encounter_ref,
            condition_snomed_map=condition_snomed_map,
            reference_registry=reference_registry,
            encounter_date=encounter_date,
            author_references=author_references,
        )
        doc_refs.append(doc_ref)

    return doc_refs


def _build_doc_ref(
    note: DiagnosisNote,
    encounter_reference: str | None,
    condition_snomed_map: dict[str, list[str]],
    reference_registry: ReferenceRegistry,
    encounter_date: str | None,
    author_references: list[JSONObject] | None = None,
) -> FHIRResourceDict:
    """Build a single DocumentReference for a diagnosis note."""
    # Generate deterministic ID from encounter + diagnosis
    id_context = f"diagnosis-note-{note.encounter_content_id or 'unknown'}-{note.snomed_code or note.diagnosis_display}"
    doc_ref_id = generate_id_from_identifiers("DocumentReference", id_context)

    encoded = base64.b64encode(note.note_text.encode("utf-8")).decode("ascii")

    doc_ref: FHIRResourceDict = {
        "resourceType": "DocumentReference",
        "id": doc_ref_id,
        "status": "current",
        "description": f"Diagnosis Note - {note.diagnosis_display}",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "51855-5",
                    "display": "Patient Note",
                }
            ],
            "text": f"Diagnosis Note - {note.diagnosis_display}",
        },
        "category": [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                        "code": "clinical-note",
                        "display": "Clinical Note",
                    }
                ]
            }
        ],
        "subject": reference_registry.get_patient_reference(),
        "content": [
            {
                "attachment": {
                    "contentType": "text/plain",
                    "data": encoded,
                }
            }
        ],
    }

    if encounter_date:
        doc_ref["date"] = fhir_date_to_instant(encounter_date)

    if author_references:
        doc_ref["author"] = author_references

    # Context: link to Encounter and optionally Condition(s)
    context: dict = {}

    if encounter_reference:
        context["encounter"] = [{"reference": encounter_reference}]

    if note.snomed_code and note.snomed_code in condition_snomed_map:
        condition_ids = condition_snomed_map[note.snomed_code]
        related_refs: list[JSONObject] = []
        for cid in condition_ids:
            ref: JSONObject = {"reference": f"urn:uuid:{cid}"}
            # Add display from diagnosis note display text
            if note.diagnosis_display:
                ref["display"] = note.diagnosis_display
            related_refs.append(ref)
        context["related"] = related_refs

    if context:
        doc_ref["context"] = context

    return doc_ref


def extract_encounter_content_id_map(
    section: Section,
    encounters: list[FHIRResourceDict],
) -> dict[str, str]:
    """Build a map from narrative content IDs to FHIR Encounter resource IDs.

    The encounter entry has <text><reference value="#encounter123"/> which points
    to the content ID in the narrative table. We match these to link diagnosis
    notes to the correct Encounter resource.

    Args:
        section: The encounters Section
        encounters: List of Encounter FHIR resources

    Returns:
        Dict mapping content ID (e.g. "encounter123") to Encounter resource ID
    """
    content_id_map: dict[str, str] = {}

    if not section.entry:
        return content_id_map

    encounter_ids: set[str] = set()
    for enc in encounters:
        eid = enc.get("id")
        if isinstance(eid, str):
            encounter_ids.add(eid)

    for entry in section.entry:
        enc = entry.encounter
        if not enc:
            continue

        # Get the text reference (e.g. "#encounter123")
        content_id: str | None = None
        if enc.text and enc.text.reference:
            ref_val = enc.text.reference.value
            if ref_val and ref_val.startswith("#"):
                content_id = ref_val[1:]

        if not content_id:
            continue

        # Find the FHIR Encounter with matching identifier
        # The encounter converter generates IDs from C-CDA encounter IDs
        if enc.id:
            for id_elem in enc.id:
                if not id_elem.null_flavor and (id_elem.root or id_elem.extension):
                    fhir_enc_id = generate_id_from_identifiers(
                        "Encounter", id_elem.root, id_elem.extension
                    )
                    if fhir_enc_id in encounter_ids:
                        content_id_map[content_id] = fhir_enc_id
                    break

    return content_id_map


def build_condition_snomed_map(
    conditions: list[FHIRResourceDict],
) -> dict[str, list[str]]:
    """Build a map from SNOMED codes to Condition resource IDs.

    Multiple Conditions may share the same SNOMED code (e.g. recurring diagnoses
    across encounters), so each code maps to a list of Condition IDs.

    Args:
        conditions: List of Condition FHIR resources

    Returns:
        Dict mapping SNOMED code to list of Condition resource IDs
    """
    snomed_map: dict[str, list[str]] = {}

    for condition in conditions:
        condition_id = condition.get("id")
        if not isinstance(condition_id, str):
            continue

        code = condition.get("code")
        if not isinstance(code, dict):
            continue

        codings = code.get("coding")
        if not isinstance(codings, list):
            continue

        for coding in codings:
            if not isinstance(coding, dict):
                continue
            system = coding.get("system", "")
            code_val = coding.get("code", "")
            if isinstance(code_val, str) and isinstance(system, str) and code_val and system in (
                "http://snomed.info/sct",
                "http://snomed.info/sct/731000124108",
            ):
                snomed_map.setdefault(code_val, []).append(condition_id)
                break

    return snomed_map


def extract_encounter_diagnosis_notes(
    structured_body: StructuredBody,
    encounters: list[FHIRResourceDict],
    conditions: list[FHIRResourceDict],
    reference_registry: ReferenceRegistry,
    author_references: list[JSONObject] | None = None,
    fallback_encounter_reference: str | None = None,
    fallback_encounter_date: str | None = None,
) -> list[FHIRResourceDict]:
    """Top-level function: extract diagnosis notes from encounter narrative tables.

    Iterates over all Encounters sections in the structured body, extracts
    diagnosis notes from narrative tables, and creates DocumentReference resources.

    Args:
        structured_body: The C-CDA structured body
        encounters: Already-converted Encounter resources
        conditions: Already-converted Condition resources (for SNOMED matching)
        reference_registry: Reference registry for patient reference
        author_references: Optional author references from document header
        fallback_encounter_reference: urn:uuid reference from encompassingEncounter,
            used when body encounter mapping fails
        fallback_encounter_date: Date from encompassingEncounter, used when body
            encounter mapping fails

    Returns:
        List of DocumentReference resources for diagnosis notes
    """
    if not structured_body.component:
        return []

    condition_snomed_map = build_condition_snomed_map(conditions)
    all_doc_refs: list[FHIRResourceDict] = []

    for comp in structured_body.component:
        if not comp.section:
            continue

        section = comp.section
        if not _is_encounters_section(section):
            continue

        # Extract notes from narrative
        notes = extract_diagnosis_notes_from_section(section)
        if not notes:
            continue

        # Build encounter content ID -> FHIR ID map
        enc_only = [e for e in encounters if e.get("resourceType") == "Encounter"]
        encounter_map = extract_encounter_content_id_map(section, enc_only)

        # Build encounter ID -> date map
        encounter_date_map = _build_encounter_date_map(enc_only)

        doc_refs = create_diagnosis_note_doc_refs(
            notes=notes,
            encounter_map=encounter_map,
            condition_snomed_map=condition_snomed_map,
            reference_registry=reference_registry,
            encounter_date_map=encounter_date_map,
            author_references=author_references,
            fallback_encounter_reference=fallback_encounter_reference,
            fallback_encounter_date=fallback_encounter_date,
        )
        all_doc_refs.extend(doc_refs)

    return all_doc_refs


def _build_encounter_date_map(encounters: list[FHIRResourceDict]) -> dict[str, str]:
    """Build a map from Encounter resource ID to period start date."""
    date_map: dict[str, str] = {}
    for enc in encounters:
        enc_id = enc.get("id")
        if not isinstance(enc_id, str):
            continue
        period = enc.get("period")
        if isinstance(period, dict):
            start = period.get("start")
            if isinstance(start, str):
                date_map[enc_id] = start
    return date_map


def _is_encounters_section(section: Section) -> bool:
    """Check if section is an Encounters section (LOINC 46240-8)."""
    return bool(section.code and section.code.code == _ENCOUNTERS_SECTION_CODE)
