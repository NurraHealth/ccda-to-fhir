"""NoteActivityConverter: C-CDA Note Activity Act to FHIR DocumentReference resource."""

from __future__ import annotations

import base64
from collections.abc import Callable

from ccda_to_fhir.ccda.models.act import Act, Reference
from ccda_to_fhir.ccda.models.author import Author
from ccda_to_fhir.ccda.models.datatypes import CD, ED, II, IVL_TS, TEL, TS
from ccda_to_fhir.ccda.models.section import Section
from ccda_to_fhir.constants import (
    DOCUMENT_REFERENCE_STATUS_TO_FHIR,
    FHIRCodes,
)
from ccda_to_fhir.id_generator import generate_id, generate_id_from_identifiers
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter
from .code_systems import CodeSystemMapper
from .references import ReferenceRegistry


# C-CDA statusCode → FHIR DocumentReference.docStatus
_DOC_STATUS_MAP: dict[str, str] = {
    "completed": "final",
    "active": "preliminary",
}


class NoteActivityConverter(BaseConverter[Act]):
    """Convert C-CDA Note Activity Act to FHIR DocumentReference resource.

    Note Activity (2.16.840.1.113883.10.20.22.4.202) represents embedded clinical
    notes within a C-CDA document. These are converted to DocumentReference resources
    per US Core DocumentReference profile.

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-NoteActivity.html
    """

    def convert(self, ccda_model: Act, section: Section | None = None) -> FHIRResourceDict:
        """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

        Args:
            ccda_model: The C-CDA Note Activity Act element
            section: Optional containing section (for text reference resolution)

        Returns:
            FHIR DocumentReference resource as a dictionary

        Raises:
            ValueError: If reference_registry is not set
        """
        note_act = ccda_model

        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create DocumentReference without patient reference."
            )

        doc_ref: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.DOCUMENT_REFERENCE,
        }

        # ID
        first_id = note_act.id[0] if note_act.id else None
        doc_ref["id"] = _generate_note_id(first_id)

        # Status (required)
        doc_ref["status"] = self.map_status_code(
            note_act.status_code,
            DOCUMENT_REFERENCE_STATUS_TO_FHIR,
            FHIRCodes.DocumentReferenceStatus.CURRENT,
        )

        # DocStatus
        doc_status = _extract_doc_status(note_act)
        if doc_status:
            doc_ref["docStatus"] = doc_status

        # Type (required by US Core)
        doc_ref["type"] = _convert_type(note_act.code, self.code_system_mapper)

        # Category - fixed to "clinical-note" for Note Activities
        doc_ref["category"] = [
            {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                        "code": "clinical-note",
                        "display": "Clinical Note",
                    }
                ]
            }
        ]

        # Subject
        doc_ref["subject"] = self.reference_registry.get_patient_reference()

        # Date - from first author's time
        if note_act.author:
            date = _extract_author_date(note_act.author, self.convert_date)
            if date:
                doc_ref["date"] = date

        # Author references
        if note_act.author:
            authors = _convert_author_references(note_act.author)
            if authors:
                doc_ref["author"] = authors

        # Content (required by US Core)
        if note_act.text:
            content_list = _create_content_list(note_act.text, section)
            if content_list:
                doc_ref["content"] = content_list
            else:
                doc_ref["content"] = _create_missing_content(self)
        else:
            doc_ref["content"] = _create_missing_content(self)

        # Context - encounter and period
        context = _create_context(note_act, self.convert_date)
        if context:
            doc_ref["context"] = context

        # RelatesTo - from reference to externalDocument
        if note_act.reference:
            relates_to = _convert_relates_to(note_act.reference)
            if relates_to:
                doc_ref["relatesTo"] = relates_to

        # Narrative
        narrative = self._generate_narrative(entry=note_act, section=section)
        if narrative:
            doc_ref["text"] = narrative

        return doc_ref


# ---------------------------------------------------------------------------
# Pure helper functions (no self, fully typed)
# ---------------------------------------------------------------------------


def _generate_note_id(identifier: II | None) -> str:
    """Generate a FHIR resource ID from the note identifier."""
    if not identifier:
        return generate_id()
    return generate_id_from_identifiers(
        "DocumentReference",
        identifier.root or None,
        identifier.extension or None,
    )


def _extract_doc_status(note_act: Act) -> str | None:
    """Map C-CDA statusCode to FHIR docStatus (completed→final, active→preliminary)."""
    if note_act.status_code and note_act.status_code.code:
        return _DOC_STATUS_MAP.get(note_act.status_code.code.lower())
    return None


def _convert_type(code: CD | None, mapper: CodeSystemMapper) -> JSONObject:
    """Convert note type code to FHIR CodeableConcept, with US Core fallback."""
    if code and code.code:
        codings: list[JSONObject] = []

        primary = _make_coding(code.code, code.code_system, code.display_name, mapper)
        if primary:
            codings.append(primary)

        if code.translation:
            for trans in code.translation:
                coding = _make_coding(trans.code, trans.code_system, trans.display_name, mapper)
                if coding:
                    codings.append(coding)

        if codings:
            result: JSONObject = {"coding": codings}
            if code.display_name:
                result["text"] = code.display_name
            return result

    # US Core fallback
    return {
        "coding": [{
            "system": "http://loinc.org",
            "code": "34133-9",
            "display": "Summarization of Episode Note",
        }],
        "text": "Clinical Note",
    }


def _make_coding(
    code: str | None,
    system: str | None,
    display: str | None,
    mapper: CodeSystemMapper,
) -> JSONObject | None:
    """Create a FHIR Coding element, mapping OID to URI."""
    if not code:
        return None
    coding: JSONObject = {"code": code}
    if system:
        uri = mapper.oid_to_uri(system)
        if uri:
            coding["system"] = uri
    if display:
        coding["display"] = display
    return coding


def _extract_author_date(
    authors: list[Author],
    convert_date_fn: Callable[[str], str | None],
) -> str | None:
    """Extract date from first author's time element."""
    first_author = authors[0]
    if first_author.time and first_author.time.value:
        return convert_date_fn(first_author.time.value)
    return None


def _convert_author_references(authors: list[Author]) -> list[JSONObject]:
    """Convert note authors to FHIR Practitioner references."""
    refs: list[JSONObject] = []
    for author in authors:
        if not author.assigned_author:
            continue
        assigned = author.assigned_author
        if assigned.assigned_person and assigned.id:
            first_id = assigned.id[0]
            prac_id = generate_id_from_identifiers(
                "Practitioner",
                first_id.root or None,
                first_id.extension or None,
            )
            refs.append({"reference": f"urn:uuid:{prac_id}"})
    return refs


def _create_content_list(
    text: ED,
    section: Section | None,
) -> list[JSONObject]:
    """Create content elements from note text (inline and/or reference)."""
    content_list: list[JSONObject] = []

    inline = _create_inline_content(text)
    if inline:
        content_list.append(inline)

    if text.reference and section:
        ref_content = _create_reference_content(text.reference, section)
        if ref_content:
            content_list.append(ref_content)

    return content_list


def _create_inline_content(text: ED) -> JSONObject | None:
    """Create content element from inline text (base64 or plain)."""
    if text.representation == "B64" and text.value:
        data = text.value.replace("\n", "").replace(" ", "").strip()
        return {
            "attachment": {
                "contentType": text.media_type or "text/plain",
                "data": data,
            }
        }

    if text.value:
        encoded = base64.b64encode(text.value.encode("utf-8")).decode("ascii")
        return {
            "attachment": {
                "contentType": text.media_type or "text/plain",
                "data": encoded,
            }
        }

    return None


def _create_reference_content(reference: TEL, section: Section) -> JSONObject | None:
    """Create content element from reference to section narrative."""
    ref_value = reference.value
    if not ref_value or not section.text:
        return None

    from ccda_to_fhir.utils.struc_doc_utils import extract_text_by_id

    ref_id = ref_value.lstrip("#")
    resolved_text = extract_text_by_id(section.text, ref_id)
    if not resolved_text:
        return None

    is_html = "<" in resolved_text and ">" in resolved_text
    content_type = "text/html" if is_html else "text/plain"
    encoded = base64.b64encode(resolved_text.encode("utf-8")).decode("ascii")

    return {
        "attachment": {
            "contentType": content_type,
            "data": encoded,
        }
    }


def _create_missing_content(converter: NoteActivityConverter) -> list[JSONObject]:
    """Create content with data-absent-reason extension when text is missing."""
    return [
        {
            "attachment": {
                "contentType": "text/plain",
                "_data": {
                    "extension": [
                        converter.create_data_absent_reason_extension(None, default_reason="unknown")
                    ]
                },
            }
        }
    ]


def _create_context(
    note_act: Act,
    convert_date_fn: Callable[[str], str | None],
) -> JSONObject | None:
    """Create document context (period, encounter references) from note activity."""
    context: JSONObject = {}

    if note_act.effective_time:
        effective = note_act.effective_time
        ts_value: str | None = None
        if isinstance(effective, IVL_TS):
            if effective.value:
                ts_value = effective.value
            elif effective.low and effective.low.value:
                ts_value = str(effective.low.value)
        elif isinstance(effective, TS) and effective.value:
            ts_value = effective.value

        if ts_value:
            start = convert_date_fn(ts_value)
            if start:
                context["period"] = {"start": start}

    if note_act.entry_relationship:
        encounter_refs: list[JSONObject] = []
        for entry_rel in note_act.entry_relationship:
            if entry_rel.encounter and entry_rel.encounter.id:
                first_id = entry_rel.encounter.id[0]
                enc_id = generate_id_from_identifiers(
                    "encounter",
                    first_id.root or None,
                    first_id.extension or None,
                )
                encounter_refs.append({"reference": f"urn:uuid:{enc_id}"})
        if encounter_refs:
            context["encounter"] = encounter_refs

    return context if context else None


def _convert_relates_to(references: list[Reference]) -> list[JSONObject]:
    """Convert reference to externalDocument to relatesTo."""
    relates_to: list[JSONObject] = []
    for ref in references:
        if ref.external_document and ref.external_document.id:
            first_id = ref.external_document.id[0]
            relates_to.append({
                "code": "appends",
                "target": {"reference": f"urn:uuid:{first_id.root}"},
            })
    return relates_to


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------


def convert_note_activity(
    note_act: Act,
    code_system_mapper: CodeSystemMapper | None = None,
    section: Section | None = None,
    reference_registry: ReferenceRegistry | None = None,
) -> FHIRResourceDict:
    """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

    Args:
        note_act: The C-CDA Note Activity Act
        code_system_mapper: Optional code system mapper
        section: Optional containing section (for text reference resolution)
        reference_registry: Optional reference registry for resource references

    Returns:
        FHIR DocumentReference resource
    """
    converter = NoteActivityConverter(
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )
    return converter.convert(note_act, section=section)
