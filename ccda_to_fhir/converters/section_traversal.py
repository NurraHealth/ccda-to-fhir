"""Typed section traversal helpers.

Concrete iterator functions for each C-CDA entry type. Each returns
the correctly typed element, eliminating dynamic dispatch.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import TYPE_CHECKING

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.ccda.models.procedure import Procedure
from ccda_to_fhir.ccda.models.section import Entry, Section, StructuredBody
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.template_registry import SupportedTemplates
from ccda_to_fhir.types import ConversionMetadata, FHIRResourceDict

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.datatypes import II

logger = get_logger(__name__)

# Union type for template-bearing entry elements
ClinicalStatement = (
    Act | Observation | Organizer | Procedure | CDAEncounter | SubstanceAdministration
)


def _iter_sections(body: StructuredBody) -> Iterator[tuple[Section, str | None]]:
    """Yield (section, section_code) including nested sections."""
    if not body.component:
        return
    for comp in body.component:
        if not comp.section:
            continue
        yield from _iter_section_tree(comp.section)


def _iter_section_tree(section: Section) -> Iterator[tuple[Section, str | None]]:
    """Yield (section, section_code) for a section and all its nested children."""
    section_code = section.code.code if section.code else None
    yield section, section_code
    if section.component:
        for nested_comp in section.component:
            if nested_comp.section:
                yield from _iter_section_tree(nested_comp.section)


def _iter_entries(body: StructuredBody) -> Iterator[tuple[Entry, Section, str | None]]:
    """Yield (entry, section, section_code) for all entries in all sections."""
    for section, section_code in _iter_sections(body):
        if not section.entry:
            continue
        for entry in section.entry:
            yield entry, section, section_code


def _has_template(element: ClinicalStatement, template_id: str) -> bool:
    """Check if a clinical statement element has a matching template ID."""
    if not element.template_id:
        return False
    return any(t.root == template_id for t in element.template_id)


# --- Typed iterator functions ---
# Each narrows the entry element to its concrete type.


def iter_matching_acts(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[Act, Section, str | None]]:
    """Yield (act, section, section_code) for acts matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        if entry.act is not None and _has_template(entry.act, template_id):
            yield entry.act, section, section_code


def iter_matching_observations(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[Observation, Section, str | None]]:
    """Yield (observation, section, section_code) for observations matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        if entry.observation is not None and _has_template(entry.observation, template_id):
            yield entry.observation, section, section_code


def iter_matching_organizers(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[Organizer, Section, str | None]]:
    """Yield (organizer, section, section_code) for organizers matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        if entry.organizer is not None and _has_template(entry.organizer, template_id):
            yield entry.organizer, section, section_code


def iter_matching_procedures(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[Procedure, Section, str | None]]:
    """Yield (procedure, section, section_code) for procedures matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        if entry.procedure is not None and _has_template(entry.procedure, template_id):
            yield entry.procedure, section, section_code


def iter_matching_encounters(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[CDAEncounter, Section, str | None]]:
    """Yield (encounter, section, section_code) for encounters matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        if entry.encounter is not None and _has_template(entry.encounter, template_id):
            yield entry.encounter, section, section_code


def iter_matching_substance_administrations(
    body: StructuredBody, template_id: str
) -> Iterator[tuple[SubstanceAdministration, Section, str | None]]:
    """Yield (substance_administration, section, section_code) for SAs matching template_id."""
    for entry, section, section_code in _iter_entries(body):
        sa = entry.substance_administration
        if sa is not None and _has_template(sa, template_id):
            yield sa, section, section_code


def scan_skipped_templates(body: StructuredBody, metadata: ConversionMetadata) -> None:
    """Scan all entries and track unsupported templates as skipped."""
    for entry, _section, _section_code in _iter_entries(body):
        for element in (
            entry.act,
            entry.observation,
            entry.organizer,
            entry.procedure,
            entry.encounter,
            entry.substance_administration,
        ):
            if element is None or not element.template_id:
                continue
            for t in element.template_id:
                if (
                    t.root
                    and not SupportedTemplates.is_supported(t.root)
                    and t.root not in metadata["processed_templates"]
                ):
                    track_skipped(metadata, t.root)


# --- Result collection helpers ---


def collect_results(
    resources: list[FHIRResourceDict],
    result: FHIRResourceDict
    | list[FHIRResourceDict]
    | tuple[FHIRResourceDict, list[FHIRResourceDict]]
    | None,
) -> None:
    """Append converter result(s) to the resources list."""
    if isinstance(result, tuple):
        resource, pending = result
        resources.append(resource)
        resources.extend(pending)
    elif isinstance(result, list):
        resources.extend(result)
    elif result is not None:
        resources.append(result)


# --- Error handling ---


@contextmanager
def converting(
    metadata: ConversionMetadata | None,
    template_id: str,
    element_ids: list[II] | None,
    error_message: str,
) -> Iterator[None]:
    """Context manager for converter error handling and metadata tracking.

    Wraps a converter call to handle exceptions and track processed/errored
    templates in conversion metadata.

    Usage:
        with converting(metadata, TemplateIds.XXX, element.id, "xxx"):
            result = converter(element, ...)
            collect_results(resources, result)
    """
    try:
        yield
        if metadata is not None:
            track_processed(metadata, template_id)
    except Exception as e:
        if metadata is not None:
            track_error(metadata, template_id, element_ids, e)
        logger.error(f"Error converting {error_message}", exc_info=True)


# --- Metadata tracking helpers ---


def track_processed(metadata: ConversionMetadata, template_id: str) -> None:
    """Track a successfully processed template."""
    if template_id not in metadata["processed_templates"]:
        metadata["processed_templates"][template_id] = {
            "template_id": template_id,
            "name": SupportedTemplates.get_template_name(template_id),
            "count": 0,
        }
    metadata["processed_templates"][template_id]["count"] += 1


def track_skipped(metadata: ConversionMetadata, template_id: str) -> None:
    """Track a skipped (unsupported) template."""
    if template_id not in metadata["skipped_templates"]:
        metadata["skipped_templates"][template_id] = {
            "template_id": template_id,
            "name": SupportedTemplates.get_template_name(template_id),
            "count": 0,
        }
    metadata["skipped_templates"][template_id]["count"] += 1


def track_error(
    metadata: ConversionMetadata,
    template_id: str,
    element_ids: list[II] | None,
    error: Exception,
) -> None:
    """Track a conversion error."""
    entry_id = None
    if element_ids:
        first = element_ids[0]
        if first:
            entry_id = f"{first.root}/{first.extension or ''}"
    metadata["errors"].append(
        {
            "template_id": template_id,
            "entry_id": entry_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }
    )
