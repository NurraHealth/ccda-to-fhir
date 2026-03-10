"""Convert narrative-only C-CDA sections to FHIR DocumentReference resources.

Many C-CDA sections (HPI, Physical Exam, ROS, Assessment, Reason for Visit)
contain clinically valuable text but have no structured entries. The C-CDA on
FHIR IG does not yet formally map these to standalone FHIR resources (its scope
is PAMI+), but dropping them loses important clinical context.

This module creates a DocumentReference per narrative section, following the
same pattern as NoteActivity → DocumentReference but for section-level text.
"""

from __future__ import annotations

import base64

from ccda_to_fhir.ccda.models.section import Section, StructuredBody
from ccda_to_fhir.id_generator import generate_id
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict
from ccda_to_fhir.utils.struc_doc_utils import narrative_to_html, narrative_to_plain_text

from .references import ReferenceRegistry

logger = get_logger(__name__)


# Sections to extract, keyed by LOINC code.
# display is used as DocumentReference.type.text and for logging.
NARRATIVE_SECTIONS: dict[str, str] = {
    "10164-2": "History of Present Illness",
    "29545-1": "Physical Examination",
    "10187-3": "Review of Systems",
    "51848-0": "Assessment",
    "29299-5": "Reason for Visit",
}

# Placeholder-like text that should be treated as empty.
_EMPTY_PATTERNS = frozenset({
    "no assessment recorded",
    "no assessment recorded.",
    "no data recorded",
    "no data recorded.",
    "no information",
    "no information.",
    "none",
    "none.",
    "n/a",
})


def _is_empty_narrative(plain_text: str) -> bool:
    """Return True if the narrative is blank or a placeholder."""
    stripped = plain_text.strip()
    if not stripped:
        return True
    return stripped.lower() in _EMPTY_PATTERNS


def extract_narrative_sections(
    structured_body: StructuredBody,
    reference_registry: ReferenceRegistry,
) -> list[FHIRResourceDict]:
    """Walk sections and create DocumentReferences for narrative-only clinical sections.

    Only creates a resource when:
    - The section's LOINC code is in NARRATIVE_SECTIONS
    - The section has narrative text (section.text)
    - The narrative is not empty or a placeholder

    Args:
        structured_body: Parsed C-CDA structured body
        reference_registry: Registry for patient reference resolution

    Returns:
        List of FHIR DocumentReference dicts
    """
    results: list[FHIRResourceDict] = []

    if not structured_body.component:
        return results

    for comp in structured_body.component:
        section = comp.section
        if not section or not section.code:
            continue

        loinc_code = section.code.code
        if loinc_code not in NARRATIVE_SECTIONS:
            continue

        display = NARRATIVE_SECTIONS[loinc_code]

        # Skip if no narrative
        if not section.text:
            logger.debug("Skipping narrative section with no text", section=display)
            continue

        plain_text = narrative_to_plain_text(section.text)
        if _is_empty_narrative(plain_text):
            logger.debug("Skipping empty narrative section", section=display)
            continue

        doc_ref = _build_document_reference(
            section=section,
            loinc_code=loinc_code,
            display=display,
            plain_text=plain_text,
            reference_registry=reference_registry,
        )
        results.append(doc_ref)
        logger.info(
            "Extracted narrative section as DocumentReference",
            section=display,
            loinc_code=loinc_code,
            text_length=len(plain_text),
        )

    return results


def _build_document_reference(
    *,
    section: Section,
    loinc_code: str,
    display: str,
    plain_text: str,
    reference_registry: ReferenceRegistry,
) -> FHIRResourceDict:
    """Build a FHIR DocumentReference for a narrative section."""
    doc_ref: FHIRResourceDict = {
        "resourceType": "DocumentReference",
        "id": generate_id(),
        "status": "current",
        "type": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": loinc_code,
                    "display": display,
                }
            ],
            "text": display,
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
        "content": [],
    }

    # Plain text attachment
    plain_b64 = base64.b64encode(plain_text.encode("utf-8")).decode("ascii")
    doc_ref["content"].append(
        {
            "attachment": {
                "contentType": "text/plain",
                "data": plain_b64,
            }
        }
    )

    # HTML attachment (preserves formatting like bold system headers in PE)
    html_text = narrative_to_html(section.text)
    if html_text:
        html_b64 = base64.b64encode(html_text.encode("utf-8")).decode("ascii")
        doc_ref["content"].append(
            {
                "attachment": {
                    "contentType": "text/html",
                    "data": html_b64,
                }
            }
        )

    return doc_ref
