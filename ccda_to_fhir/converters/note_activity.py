"""NoteActivityConverter: C-CDA Note Activity Act to FHIR DocumentReference resource."""

from __future__ import annotations

import base64
from collections.abc import Callable

from fhir.resources.attachment import Attachment
from fhir.resources.documentreference import (
    DocumentReferenceContent,
    DocumentReferenceRelatesTo,
)
from fhir.resources.extension import Extension
from fhir.resources.period import Period

from ccda_to_fhir.ccda.models.act import Act, Reference
from ccda_to_fhir.ccda.models.author import Author
from ccda_to_fhir.ccda.models.datatypes import CD, ED, II, TEL
from ccda_to_fhir.ccda.models.section import Section
from ccda_to_fhir.constants import (
    CCDA_TYPECODE_TO_FHIR_RELATES_TO,
    DOCUMENT_REFERENCE_STATUS_TO_FHIR,
    FHIRCodes,
)
from ccda_to_fhir.id_generator import generate_id, generate_id_from_identifiers
from ccda_to_fhir.types import (
    EncounterContext,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRDocRefContext,
    FHIRReference,
    FHIRResourceDict,
    JSONObject,
)

from .author_references import build_author_references
from .base import BaseConverter
from .code_systems import CodeSystemMapper
from .references import ReferenceRegistry

# C-CDA statusCode → FHIR DocumentReference.docStatus
_DOC_STATUS_MAP: dict[str, str] = {
    "completed": "final",
    "active": "preliminary",
}

# Fixed US Core clinical-note category
_CLINICAL_NOTE_CATEGORY = FHIRCodeableConcept(
    coding=[
        FHIRCoding(
            system="http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
            code="clinical-note",
            display="Clinical Note",
        )
    ]
)

# US Core fallback type when no code is available
_FALLBACK_TYPE = FHIRCodeableConcept(
    coding=[
        FHIRCoding(
            system="http://loinc.org",
            code="34133-9",
            display="Summarization of Episode Note",
        )
    ],
    text="Clinical Note",
)

# FHIR R4B document-relationship-type system
_RELATES_TO_SYSTEM = "http://hl7.org/fhir/document-relationship-type"


class NoteActivityConverter(BaseConverter[Act]):
    """Convert C-CDA Note Activity Act to FHIR DocumentReference resource.

    Note Activity (2.16.840.1.113883.10.20.22.4.202) represents embedded clinical
    notes within a C-CDA document. These are converted to DocumentReference resources
    per US Core DocumentReference profile.

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-NoteActivity.html
    """

    def convert(
        self,
        ccda_model: Act,
        section: Section | None = None,
        fallback_encounter_context: EncounterContext | None = None,
    ) -> FHIRResourceDict:
        """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

        Args:
            ccda_model: The C-CDA Note Activity Act element
            section: Optional containing section (for text reference resolution)
            fallback_encounter_context: Optional encounter context from
                encompassingEncounter, used when the note has no explicit
                entryRelationship/encounter

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

        doc_ref: FHIRResourceDict = {
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
        doc_ref["type"] = _convert_type(note_act.code, self.code_system_mapper).to_dict()

        # Category - fixed to "clinical-note" for Note Activities
        doc_ref["category"] = [_CLINICAL_NOTE_CATEGORY.to_dict()]

        # Subject
        doc_ref["subject"] = self.reference_registry.get_patient_reference().to_dict()

        # Date and author references
        if note_act.author:
            date = _extract_author_date(note_act.author, self.convert_date)
            if date:
                doc_ref["date"] = date

            authors = build_author_references(note_act.author)
            if authors:
                doc_ref["author"] = [a.to_dict() for a in authors]

        # Content (required by US Core)
        if note_act.text:
            content_list = _create_content_list(note_act.text, section)
            if content_list:
                doc_ref["content"] = [
                    c.model_dump(exclude_none=True, mode="json") for c in content_list
                ]
            else:
                doc_ref["content"] = [
                    c.model_dump(exclude_none=True, mode="json")
                    for c in _create_missing_content("unknown")
                ]
        else:
            doc_ref["content"] = [
                c.model_dump(exclude_none=True, mode="json")
                for c in _create_missing_content("unknown")
            ]

        # Context - encounter and period
        context = _create_context(
            note_act,
            self.convert_date,
            fallback_encounter_context or EncounterContext(),
        )
        if context:
            doc_ref["context"] = context.to_dict()

        # RelatesTo - from reference to externalDocument
        if note_act.reference:
            relates_to = _convert_relates_to(note_act.reference)
            if relates_to:
                doc_ref["relatesTo"] = [
                    r.model_dump(exclude_none=True, mode="json") for r in relates_to
                ]

        # Narrative
        narrative = self._generate_narrative(entry=note_act, section=section)
        if narrative:
            doc_ref["text"] = narrative.model_dump(exclude_none=True)

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
    """Map C-CDA statusCode to FHIR docStatus (completed->final, active->preliminary)."""
    if note_act.status_code and note_act.status_code.code:
        return _DOC_STATUS_MAP.get(note_act.status_code.code.lower())
    return None


def _convert_type(code: CD | None, mapper: CodeSystemMapper) -> FHIRCodeableConcept:
    """Convert note type code to FHIR CodeableConcept, with US Core fallback."""
    if code and code.code:
        codings: list[FHIRCoding] = []

        primary = _make_coding(code.code, code.code_system, code.display_name, mapper)
        if primary:
            codings.append(primary)

        if code.translation:
            for trans in code.translation:
                coding = _make_coding(trans.code, trans.code_system, trans.display_name, mapper)
                if coding:
                    codings.append(coding)

        if codings:
            return FHIRCodeableConcept(
                coding=codings,
                text=code.display_name,
            )

    return _FALLBACK_TYPE


def _make_coding(
    code: str | None,
    system: str | None,
    display: str | None,
    mapper: CodeSystemMapper,
) -> FHIRCoding | None:
    """Create a FHIR Coding element, mapping OID to URI.

    Per FHIR R4: ``system`` SHALL be present when ``code`` is present.
    When no system is available, falls back to a display-only coding if
    display is present, otherwise returns None.
    """
    if not code:
        return None
    if system:
        mapped_system = mapper.oid_to_uri(system)
        return FHIRCoding(system=mapped_system, code=code, display=display)
    # No system → can't produce a valid system+code coding per FHIR spec.
    # Preserve display text if available.
    if display:
        return FHIRCoding(display=display)
    return None


def _extract_author_date(
    authors: list[Author],
    convert_date_fn: Callable[[str], str | None],
) -> str | None:
    """Extract date from first author's time element."""
    if not authors:
        return None
    first_author = authors[0]
    if first_author.time and first_author.time.value:
        return convert_date_fn(first_author.time.value)
    return None


def _create_content_list(
    text: ED,
    section: Section | None,
) -> list[DocumentReferenceContent]:
    """Create content elements from note text (inline and/or reference)."""
    content_list: list[DocumentReferenceContent] = []

    inline = _create_inline_content(text)
    if inline:
        content_list.append(inline)

    if text.reference and section:
        ref_content = _create_reference_content(text.reference, section)
        if ref_content:
            content_list.append(ref_content)

    return content_list


def _create_inline_content(text: ED) -> DocumentReferenceContent | None:
    """Create content element from inline text (base64 or plain)."""
    if text.representation == "B64" and text.value:
        data = text.value.replace("\n", "").replace(" ", "").strip()
        return DocumentReferenceContent(
            attachment=Attachment(
                contentType=text.media_type or "text/plain",
                data=data,
            )
        )

    if text.value:
        encoded = base64.b64encode(text.value.encode("utf-8")).decode("ascii")
        return DocumentReferenceContent(
            attachment=Attachment(
                contentType=text.media_type or "text/plain",
                data=encoded,
            )
        )

    return None


def _create_reference_content(reference: TEL, section: Section) -> DocumentReferenceContent | None:
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

    return DocumentReferenceContent(
        attachment=Attachment(
            contentType=content_type,
            data=encoded,
        )
    )


def _create_missing_content(reason_code: str) -> list[DocumentReferenceContent]:
    """Create content with data-absent-reason extension when text is missing.

    Args:
        reason_code: FHIR data-absent-reason code (e.g. "unknown", "asked-unknown").
    """
    from ccda_to_fhir.constants import FHIRSystems

    return [
        DocumentReferenceContent(
            attachment=Attachment(
                contentType="text/plain",
                _data={
                    "extension": [
                        Extension(
                            url=FHIRSystems.DATA_ABSENT_REASON,
                            valueCode=reason_code,
                        ).model_dump(exclude_none=True, mode="json")
                    ]
                },
            )
        )
    ]


def _create_context(
    note_act: Act,
    convert_date_fn: Callable[[str], str | None],
    fallback_encounter_context: EncounterContext,
) -> FHIRDocRefContext | None:
    """Create document context (period, encounter references) from note activity.

    Encounter references are extracted from entryRelationship/encounter elements.
    When none are found, falls back to ``fallback_encounter_context`` (typically
    derived from the document header's encompassingEncounter).
    """
    period: JSONObject | None = None
    encounter_refs: list[FHIRReference] = []

    if note_act.effective_time:
        effective = note_act.effective_time
        ts_value: str | None = None
        if effective.value:
            ts_value = effective.value
        elif effective.low and effective.low.value:
            ts_value = effective.low.value

        if ts_value:
            start = convert_date_fn(ts_value)
            if start:
                period = Period(start=start).model_dump(exclude_none=True, mode="json")

    if note_act.entry_relationship:
        for entry_rel in note_act.entry_relationship:
            if entry_rel.encounter and entry_rel.encounter.id:
                first_id = entry_rel.encounter.id[0]
                enc_id = generate_id_from_identifiers(
                    "encounter",
                    first_id.root or None,
                    first_id.extension or None,
                )
                encounter_refs.append(FHIRReference(reference=f"urn:uuid:{enc_id}"))

    # Fallback to encompassingEncounter when no explicit encounter refs
    if not encounter_refs:
        fallback_ref = fallback_encounter_context.to_fhir_reference()
        if fallback_ref:
            encounter_refs.append(fallback_ref)

    context = FHIRDocRefContext(period=period, encounter=encounter_refs)
    return context if context else None


def _convert_relates_to(references: list[Reference]) -> list[DocumentReferenceRelatesTo]:
    """Convert reference to externalDocument to FHIR relatesTo.

    Maps C-CDA typeCode to FHIR relatesTo.code (R4B CodeableConcept):
      RPLC -> replaces, APND -> appends, XFRM -> transforms.
    REFR and unmapped typeCodes are skipped (no FHIR relatesTo equivalent).
    """
    relates_to: list[DocumentReferenceRelatesTo] = []
    for ref in references:
        if not ref.external_document or not ref.external_document.id:
            continue
        fhir_code = CCDA_TYPECODE_TO_FHIR_RELATES_TO.get(ref.type_code or "")
        if not fhir_code:
            continue
        first_id = ref.external_document.id[0]
        doc_id = generate_id_from_identifiers(
            "DocumentReference",
            first_id.root or None,
            first_id.extension or None,
        )
        relates_to.append(
            DocumentReferenceRelatesTo(
                code={"coding": [{"system": _RELATES_TO_SYSTEM, "code": fhir_code}]},
                target={"reference": f"urn:uuid:{doc_id}"},
            )
        )
    return relates_to


# ---------------------------------------------------------------------------
# Public convenience function
# ---------------------------------------------------------------------------


def convert_note_activity(
    note_act: Act,
    code_system_mapper: CodeSystemMapper | None = None,
    section: Section | None = None,
    reference_registry: ReferenceRegistry | None = None,
    fallback_encounter_context: EncounterContext | None = None,
) -> FHIRResourceDict:
    """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

    Args:
        note_act: The C-CDA Note Activity Act
        code_system_mapper: Optional code system mapper
        section: Optional containing section (for text reference resolution)
        reference_registry: Optional reference registry for resource references
        fallback_encounter_context: Optional encounter context from
            encompassingEncounter, used when note has no explicit encounter ref

    Returns:
        FHIR DocumentReference resource
    """
    converter = NoteActivityConverter(
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )
    return converter.convert(
        note_act,
        section=section,
        fallback_encounter_context=fallback_encounter_context,
    )
