"""Generic section traversal and resource extraction.

This module eliminates ~500 lines of duplicated section traversal code
by providing a generic, configurable section processor.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

from ccda_to_fhir.ccda.models.section import StructuredBody
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.template_registry import SupportedTemplates
from ccda_to_fhir.types import ConversionMetadata, FHIRResourceDict

logger = get_logger(__name__)

EntryType = Literal[
    "act",
    "observation",
    "organizer",
    "procedure",
    "encounter",
    "substance_administration",
]


@dataclass
class SectionConfig:
    """Configuration for processing a specific section type.

    Attributes:
        template_id: The C-CDA template ID to match
        entry_type: The type of entry element (act, observation, etc.)
        converter: Function to convert the entry to FHIR resource(s)
        error_message: Error message prefix for logging
        include_section_code: Whether to pass section_code to converter
    """

    template_id: str
    entry_type: EntryType
    converter: Callable
    error_message: str
    include_section_code: bool = False


class SectionProcessor:
    """Generic processor for extracting resources from C-CDA sections.

    This class eliminates duplication by providing a single implementation
    of the section traversal pattern used throughout DocumentConverter.

    Example:
        >>> config = SectionConfig(
        ...     template_id=TemplateIds.PROBLEM_CONCERN_ACT,
        ...     entry_type="act",
        ...     converter=convert_problem_concern_act,
        ...     error_message="problem concern act",
        ...     include_section_code=True
        ... )
        >>> processor = SectionProcessor(config)
        >>> conditions = processor.process(structured_body)
    """

    def __init__(self, config: SectionConfig):
        """Initialize the section processor.

        Args:
            config: Configuration for this processor
        """
        self.config = config

    def process(
        self,
        structured_body: StructuredBody,
        metadata: ConversionMetadata | None = None,
        **converter_kwargs,
    ) -> list[FHIRResourceDict]:
        """Process a structured body and extract resources.

        Recursively traverses sections, finds matching entries,
        and converts them to FHIR resources. Tracks metadata about
        processed, skipped, and failed templates.

        Args:
            structured_body: The C-CDA structuredBody element
            metadata: Optional metadata tracker for conversion statistics
            **converter_kwargs: Additional kwargs to pass to converter

        Returns:
            List of FHIR resources extracted from matching entries
        """
        resources = []

        if not structured_body.component:
            return resources

        for comp in structured_body.component:
            if not comp.section:
                continue

            section = comp.section
            section_code = section.code.code if section.code else None

            # Process entries in this section
            if section.entry:
                for entry in section.entry:
                    # Get the entry element based on type
                    entry_element = self._get_entry_element(entry)

                    if entry_element is None:
                        continue

                    # Check template IDs
                    if entry_element.template_id:
                        # Track all templates encountered
                        entry_templates = [t.root for t in entry_element.template_id if t.root]

                        # Check if this entry matches our configured template
                        matched = False
                        for template in entry_element.template_id:
                            if template.root == self.config.template_id:
                                matched = True
                                # Found a match - convert it
                                try:
                                    # Build converter arguments
                                    # Inspect converter signature to only pass supported parameters
                                    import inspect
                                    converter_sig = inspect.signature(self.config.converter)

                                    kwargs = {}

                                    # Pass section_code if needed and supported
                                    if self.config.include_section_code and "section_code" in converter_sig.parameters:
                                        kwargs["section_code"] = section_code

                                    # Pass section if supported
                                    if "section" in converter_sig.parameters:
                                        kwargs["section"] = section

                                    # Pass any additional kwargs from converter_kwargs if supported
                                    for key, value in converter_kwargs.items():
                                        if key in converter_sig.parameters:
                                            kwargs[key] = value

                                    # Call converter
                                    result = self.config.converter(
                                        entry_element, **kwargs
                                    )

                                    # Handle single resource or list
                                    if isinstance(result, list):
                                        resources.extend(result)
                                    elif result is not None:
                                        resources.append(result)

                                    # Track successful conversion
                                    if metadata is not None:
                                        self._track_processed(metadata, template.root)

                                except Exception as e:
                                    # Track error
                                    if metadata is not None:
                                        entry_id = None
                                        if hasattr(entry_element, "id") and entry_element.id:
                                            ids = entry_element.id if isinstance(entry_element.id, list) else [entry_element.id]
                                            if ids and ids[0]:
                                                entry_id = f"{ids[0].root}/{ids[0].extension or ''}"

                                        metadata["errors"].append({
                                            "template_id": template.root,
                                            "entry_id": entry_id,
                                            "error_type": type(e).__name__,
                                            "error_message": str(e),
                                        })

                                    logger.error(
                                        f"Error converting {self.config.error_message}",
                                        exc_info=True,
                                    )
                                break

                        # Track skipped templates (not matched by any processor)
                        if not matched and metadata is not None:
                            for template_id in entry_templates:
                                # Only track as skipped if it's not a supported template
                                # (might be processed by a different processor)
                                if not SupportedTemplates.is_supported(template_id):
                                    self._track_skipped(metadata, template_id)

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        # Create a temporary structured body for recursion
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_resources = self.process(temp_body, metadata, **converter_kwargs)
                        resources.extend(nested_resources)

        return resources

    def _get_entry_element(self, entry):
        """Get the appropriate entry element based on entry type.

        Args:
            entry: The section entry

        Returns:
            The entry element (act, observation, etc.) or None
        """
        return getattr(entry, self.config.entry_type, None)

    def _track_processed(self, metadata: ConversionMetadata, template_id: str) -> None:
        """Track a successfully processed template.

        Args:
            metadata: The conversion metadata to update
            template_id: The C-CDA template ID that was processed
        """
        if template_id not in metadata["processed_templates"]:
            metadata["processed_templates"][template_id] = {
                "template_id": template_id,
                "name": SupportedTemplates.get_template_name(template_id),
                "count": 0,
            }
        metadata["processed_templates"][template_id]["count"] += 1

    def _track_skipped(self, metadata: ConversionMetadata, template_id: str) -> None:
        """Track a skipped (unsupported) template.

        Args:
            metadata: The conversion metadata to update
            template_id: The C-CDA template ID that was skipped
        """
        if template_id not in metadata["skipped_templates"]:
            metadata["skipped_templates"][template_id] = {
                "template_id": template_id,
                "name": SupportedTemplates.get_template_name(template_id),
                "count": 0,
            }
        metadata["skipped_templates"][template_id]["count"] += 1
