"""Generic section traversal and resource extraction.

This module eliminates ~500 lines of duplicated section traversal code
by providing a generic, configurable section processor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Literal

from ccda_to_fhir.ccda.models.section import StructuredBody
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict

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
        **converter_kwargs,
    ) -> list[FHIRResourceDict]:
        """Process a structured body and extract resources.

        Recursively traverses sections, finds matching entries,
        and converts them to FHIR resources.

        Args:
            structured_body: The C-CDA structuredBody element
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
                        for template in entry_element.template_id:
                            if template.root == self.config.template_id:
                                # Found a match - convert it
                                try:
                                    # Build converter arguments
                                    kwargs = converter_kwargs.copy()
                                    if self.config.include_section_code:
                                        kwargs["section_code"] = section_code

                                    # Pass section only for converters that accept it
                                    # Check if converter accepts 'section' parameter
                                    import inspect
                                    converter_sig = inspect.signature(self.config.converter)
                                    if "section" in converter_sig.parameters:
                                        kwargs["section"] = section

                                    # Call converter
                                    result = self.config.converter(
                                        entry_element, **kwargs
                                    )

                                    # Handle single resource or list
                                    if isinstance(result, list):
                                        resources.extend(result)
                                    elif result is not None:
                                        resources.append(result)

                                except Exception as e:
                                    logger.error(
                                        f"Error converting {self.config.error_message}",
                                        exc_info=True,
                                    )
                                break

            # Process nested sections recursively
            if section.component:
                for nested_comp in section.component:
                    if nested_comp.section:
                        # Create a temporary structured body for recursion
                        temp_body = type("obj", (object,), {"component": [nested_comp]})()
                        nested_resources = self.process(temp_body, **converter_kwargs)
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
