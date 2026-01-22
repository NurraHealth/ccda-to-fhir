"""Base converter class with common utilities."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from ccda_to_fhir.constants import FHIRSystems
from ccda_to_fhir.exceptions import CCDAConversionError, MissingRequiredFieldError
from ccda_to_fhir.id_generator import generate_id
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict, JSONObject, JSONValue

from .code_systems import CodeSystemMapper

logger = get_logger(__name__)

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.datatypes import CS

    from .references import ReferenceRegistry

# Type variable for input C-CDA model
CCDAModel = TypeVar("CCDAModel")


class BaseConverter(ABC, Generic[CCDAModel]):
    """Base class for all C-CDA to FHIR converters.

    This class provides common utilities and patterns for converting
    C-CDA Pydantic models to FHIR resources.
    """

    # FHIR ID regex: [A-Za-z0-9\-\.]{1,64}
    FHIR_ID_PATTERN: ClassVar[re.Pattern] = re.compile(r'^[A-Za-z0-9\-\.]{1,64}$')

    def __init__(
        self,
        code_system_mapper: CodeSystemMapper | None = None,
        reference_registry: ReferenceRegistry | None = None,
    ):
        """Initialize the converter.

        Args:
            code_system_mapper: Optional code system mapper for OID to URI conversion
            reference_registry: Optional reference registry for tracking converted resources
        """
        self.code_system_mapper = code_system_mapper or CodeSystemMapper()
        self.reference_registry = reference_registry

    @abstractmethod
    def convert(self, ccda_model: CCDAModel) -> FHIRResourceDict:
        """Convert a C-CDA model to a FHIR resource.

        Args:
            ccda_model: Validated C-CDA Pydantic model

        Returns:
            FHIR resource as a dictionary

        Raises:
            CCDAConversionError: If conversion fails
        """
        pass

    @staticmethod
    def sanitize_id(value: str) -> str:
        """Sanitize a string to be FHIR-compliant resource ID.

        Per FHIR R4B spec, IDs can only contain:
        - A-Z, a-z (letters)
        - 0-9 (numerals)
        - - (hyphen)
        - . (period)

        Max length: 64 characters

        Args:
            value: String to sanitize

        Returns:
            FHIR-compliant ID with invalid characters replaced by hyphens

        Examples:
            >>> BaseConverter.sanitize_id("16_Height")
            '16-Height'
            >>> BaseConverter.sanitize_id("8_Body temperature")
            '8-Body-temperature'
        """
        # Replace any character that's not alphanumeric, dash, or period with hyphen
        sanitized = re.sub(r'[^A-Za-z0-9\-\.]', '-', value)
        # Truncate to 64 characters max
        return sanitized[:64]

    def generate_resource_id(
        self,
        root: str | None,
        extension: str | None,
        resource_type: str,
        fallback_context: str = "",
    ) -> str:
        """Generate a FHIR-compliant UUID v4 resource ID.

        Delegates to central id_generator module for consistency.
        Within a document, same identifiers → same UUID.

        Args:
            root: OID or UUID root from C-CDA identifier
            extension: Extension from C-CDA identifier
            resource_type: FHIR resource type (e.g., "Encounter", "condition")
            fallback_context: Additional context for fallback (unused but kept for API compatibility)

        Returns:
            UUID v4 string (cached for consistency within document)

        Examples:
            >>> generate_resource_id(None, "ABC-123", "condition", "")
            'f47ac10b-58cc-4372-a567-0e02b2c3d479'
            >>> generate_resource_id("2.16.840.1.113883", None, "allergy", "ctx")
            'a1b2c3d4-e5f6-4789-a012-3456789abcde'
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers(resource_type, root, extension)

    def map_oid_to_uri(self, oid: str | None) -> str:
        """Map a C-CDA OID to a FHIR canonical URI.

        Args:
            oid: The OID to convert

        Returns:
            The FHIR canonical URI
        """
        if not oid:
            return ""
        return self.code_system_mapper.oid_to_uri(oid)

    def map_oid_to_identifier_system(self, oid: str | None) -> str | None:
        """Map a C-CDA OID to a system URI for use in Identifier.system.

        Unlike map_oid_to_uri(), this returns urn:oid: format for unmapped OIDs
        because Identifier.system allows urn:oid: format.

        Args:
            oid: The OID to convert

        Returns:
            The FHIR canonical URI if known, otherwise urn:oid:{oid}
        """
        if not oid:
            return None
        return self.code_system_mapper.oid_to_identifier_system(oid)

    def convert_identifiers(self, identifiers: list) -> list[JSONObject]:
        """Convert C-CDA identifiers (list of II) to FHIR identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            List of FHIR identifier objects
        """
        fhir_identifiers: list[JSONValue] = []

        for identifier in identifiers:
            if not identifier.root:
                continue

            fhir_identifier = self.create_identifier(
                root=identifier.root, extension=identifier.extension
            )

            if fhir_identifier:
                fhir_identifiers.append(fhir_identifier)

        return fhir_identifiers

    def create_identifier(
        self, root: str | None, extension: str | None = None
    ) -> JSONObject:
        """Convert C-CDA II (Instance Identifier) to FHIR Identifier.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            FHIR Identifier as a dict
        """
        if not root:
            return {}

        identifier: JSONObject = {}

        # Determine system
        if root.startswith("urn:"):
            identifier["system"] = root
        elif self._is_uuid(root):
            identifier["system"] = f"urn:uuid:{root}"
        else:
            # It's an OID - use identifier-specific mapping that allows urn:oid:
            identifier["system"] = self.map_oid_to_identifier_system(root)

        # Add value if extension provided
        if extension:
            identifier["value"] = extension
        elif self._is_uuid(root):
            # For UUIDs without extension, use urn:uuid:... as value
            identifier["value"] = f"urn:uuid:{root}"
        elif not root.startswith("urn:"):
            # If no extension, and it's an OID, use the root as value
            identifier["value"] = root

        return identifier

    def create_codeable_concept(
        self,
        code: str | None,
        code_system: str | None,
        display_name: str | None = None,
        original_text: str | None = None,
        translations: list[JSONObject] | None = None,
    ) -> JSONObject | None:
        """Create a FHIR CodeableConcept from C-CDA code elements.

        Args:
            code: The code value
            code_system: The code system OID
            display_name: Display name for the code
            original_text: Original text from the document
            translations: List of translation codes

        Returns:
            FHIR CodeableConcept as a dict, or None if no content available
        """
        if not code and not original_text:
            return None  # Return None instead of empty dict for proper truthiness checks

        codeable_concept: JSONObject = {}
        codings: list[JSONValue] = []

        # Primary coding
        if code and code_system:
            system_uri = self.map_oid_to_uri(code_system)
            coding: JSONObject = {
                "system": system_uri,
                "code": code.strip(),  # Sanitize: remove leading/trailing whitespace
            }
            # ENHANCEMENT: Add display from terminology map if not provided from C-CDA
            if display_name:
                coding["display"] = display_name.strip()  # Sanitize display name too
            else:
                # Look up display from terminology maps for known systems
                from ccda_to_fhir.utils.terminology import get_display_for_code
                looked_up_display = get_display_for_code(system_uri, code.strip())
                if looked_up_display:
                    coding["display"] = looked_up_display
            codings.append(coding)

        # Translation codings
        if translations:
            for trans in translations:
                if trans.get("code") and trans.get("code_system"):
                    trans_system_uri = self.map_oid_to_uri(trans["code_system"])
                    trans_coding: JSONObject = {
                        "system": trans_system_uri,
                        "code": trans["code"].strip(),  # Sanitize: remove leading/trailing whitespace
                    }
                    # ENHANCEMENT: Add display from terminology map if not provided
                    if trans.get("display_name"):
                        trans_coding["display"] = trans["display_name"].strip()  # Sanitize display name too
                    else:
                        # Look up display from terminology maps for known systems
                        from ccda_to_fhir.utils.terminology import get_display_for_code
                        looked_up_display = get_display_for_code(trans_system_uri, trans["code"].strip())
                        if looked_up_display:
                            trans_coding["display"] = looked_up_display
                    codings.append(trans_coding)

        if codings:
            codeable_concept["coding"] = codings

        # Original text (preferred)
        if original_text:
            codeable_concept["text"] = original_text
        # Fallback: Use display_name from primary coding if available
        elif display_name:
            codeable_concept["text"] = display_name.strip()
        # Fallback: Use first coding's display if available
        elif codings and codings[0].get("display"):
            codeable_concept["text"] = codings[0]["display"]

        # If codeable_concept is empty (no coding and no text), return None
        # This can happen when code exists but code_system is missing/None
        if not codeable_concept:
            return None

        return codeable_concept

    def create_quantity(
        self, value: float | int | None, unit: str | None = None
    ) -> JSONObject:
        """Create a FHIR Quantity from C-CDA PQ (Physical Quantity).

        Per FHIR R4 spec, Quantity.system SHALL be present if a code is present.
        For clinical data, system should always be UCUM.

        Args:
            value: The numeric value
            unit: The UCUM unit

        Returns:
            FHIR Quantity as a dict

        Standard Reference:
            https://hl7.org/fhir/R4/datatypes.html#Quantity
        """
        if value is None:
            return {}

        quantity: JSONObject = {"value": value}

        # Include UCUM system and code only when unit is present
        # Per FHIR R4 qty-3: system only required if code is present
        # Omitting both is valid when no unit exists
        if unit:
            quantity["unit"] = unit
            quantity["system"] = FHIRSystems.UCUM
            quantity["code"] = unit

        return quantity

    def convert_date(self, ccda_date: str | None) -> str | None:
        """Convert C-CDA date format to FHIR date format with validation.

        Uses datetime.strptime() for robust date parsing and validation.

        C-CDA format: YYYYMMDDHHmmss+ZZZZ
        FHIR format: YYYY-MM-DDThh:mm:ss+zz:zz

        Handles partial precision:
        - YYYY → YYYY
        - YYYYMM → YYYY-MM
        - YYYYMMDD → YYYY-MM-DD
        - YYYYMMDDHH → YYYY-MM-DD (reduced to date per FHIR requirement)
        - YYYYMMDDHHmm → YYYY-MM-DD (reduced to date per FHIR requirement)
        - YYYYMMDDHHmmss → YYYY-MM-DD (reduced to date per FHIR requirement)
        - YYYYMMDDHHmmss+ZZZZ → YYYY-MM-DDThh:mm:ss+zz:zz (full conversion with timezone)

        Per FHIR R4 specification, if hours and minutes are specified, a time zone
        SHALL be populated. When C-CDA timestamp includes time but lacks timezone,
        this implementation reduces precision to date-only per C-CDA on FHIR IG
        guidance to avoid violating FHIR requirements or manufacturing potentially
        incorrect timezone data.

        Args:
            ccda_date: C-CDA formatted date string

        Returns:
            FHIR formatted date string, or None if invalid

        Examples:
            >>> convert_date("20240115")
            '2024-01-15'
            >>> convert_date("202401150930")
            '2024-01-15'  # Reduced to date - no timezone available
            >>> convert_date("20240115093000-0500")
            '2024-01-15T09:30:00-05:00'
            >>> convert_date("202X0115")  # Invalid - returns None
            None

        References:
            - FHIR R4 dateTime: https://hl7.org/fhir/R4/datatypes.html#dateTime
            - C-CDA on FHIR IG: https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html
        """
        from datetime import datetime

        if not ccda_date:
            return None

        try:
            ccda_date = ccda_date.strip()
            if not ccda_date:
                return None

            # Extract numeric portion (before +/- timezone)
            tz_start = -1
            for i, char in enumerate(ccda_date):
                if char in ('+', '-') and i > 8:  # Timezone starts after date
                    tz_start = i
                    break

            if tz_start > 0:
                numeric_part = ccda_date[:tz_start]
                tz_part = ccda_date[tz_start:]
            else:
                numeric_part = ccda_date
                tz_part = ""

            # Handle fractional seconds (e.g., "20170821112858.251")
            # Both C-CDA and FHIR R4 support fractional seconds
            # Extract and preserve them in the output
            fractional_seconds = ""
            if '.' in numeric_part:
                parts = numeric_part.split('.')
                numeric_part = parts[0]
                fractional_seconds = '.' + parts[1]

            # Validate numeric portion contains only digits
            if not numeric_part.isdigit():
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Invalid date format (non-numeric): {ccda_date}")
                return None

            length = len(numeric_part)

            # Format mapping: length -> (strptime_format, fhir_format_template)
            format_map = {
                4: ("%Y", "{year}"),
                6: ("%Y%m", "{year}-{month}"),
                8: ("%Y%m%d", "{year}-{month}-{day}"),
                10: ("%Y%m%d%H", "{year}-{month}-{day}T{hour}:00:00"),
                12: ("%Y%m%d%H%M", "{year}-{month}-{day}T{hour}:{minute}:00"),
                14: ("%Y%m%d%H%M%S", "{year}-{month}-{day}T{hour}:{minute}:{second}"),
            }

            if length not in format_map:
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Unknown date format (length {length}): {ccda_date}")
                return None

            strptime_format, fhir_template = format_map[length]

            # Use datetime.strptime() to parse and validate
            dt = datetime.strptime(numeric_part, strptime_format)

            # Sanity check year range (1800-2200)
            if not 1800 <= dt.year <= 2200:
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.warning(f"Year out of valid range: {dt.year}")
                return None

            # Check if timestamp includes time components (length > 8)
            # Per FHIR R4: "If hours and minutes are specified, a time zone SHALL be populated"
            has_time_component = length > 8
            has_timezone = tz_part and len(tz_part) >= 5

            if has_time_component and not has_timezone:
                # Per C-CDA on FHIR IG guidance: When timezone is missing, reduce precision to date-only
                # This avoids FHIR validation errors and prevents manufacturing potentially incorrect timezone data
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.info(
                    f"C-CDA timestamp '{ccda_date}' has time component but no timezone. "
                    f"Reducing precision to date-only per FHIR R4 requirement and C-CDA on FHIR IG guidance."
                )
                # Return date-only format (YYYY-MM-DD)
                return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"

            # Format result using template
            result = fhir_template.format(
                year=f"{dt.year:04d}",
                month=f"{dt.month:02d}",
                day=f"{dt.day:02d}",
                hour=f"{dt.hour:02d}",
                minute=f"{dt.minute:02d}",
                second=f"{dt.second:02d}",
            )

            # Add fractional seconds if present (FHIR R4 supports fractional seconds)
            if fractional_seconds and has_time_component:
                result += fractional_seconds

            # Handle timezone if present
            timezone_added = False
            if has_timezone:
                tz_sign = tz_part[0]
                tz_hours = tz_part[1:3]
                tz_mins = tz_part[3:5]
                try:
                    tz_h = int(tz_hours)
                    tz_m = int(tz_mins)
                    # FHIR R4: Hour 14 only valid with minutes 00 (UTC+14:00 max)
                    if (0 <= tz_h <= 13 and 0 <= tz_m <= 59) or (tz_h == 14 and tz_m == 0):
                        result += f"{tz_sign}{tz_hours}:{tz_mins}"
                        timezone_added = True
                    else:
                        from ccda_to_fhir.logging_config import get_logger
                        logger = get_logger(__name__)
                        logger.warning(
                            f"Timezone offset out of valid range: {tz_part}. "
                            f"Reducing to date-only per FHIR R4 requirement."
                        )
                except ValueError:
                    from ccda_to_fhir.logging_config import get_logger
                    logger = get_logger(__name__)
                    logger.warning(
                        f"Invalid timezone format: {tz_part}. "
                        f"Reducing to date-only per FHIR R4 requirement."
                    )

            # Per FHIR R4: if time component present, timezone is required
            # If we have time but no valid timezone, reduce to date-only
            if has_time_component and not timezone_added:
                return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d}"

            return result

        except ValueError as e:
            from ccda_to_fhir.logging_config import get_logger
            logger = get_logger(__name__)
            logger.warning(f"Invalid date '{ccda_date}': {e}")
            return None
        except (IndexError, AttributeError) as e:
            from ccda_to_fhir.logging_config import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to convert date '{ccda_date}': {e}", exc_info=True)
            return None

    def _is_uuid(self, value: str) -> bool:
        """Check if a string is a UUID.

        Args:
            value: String to check

        Returns:
            True if the string is a UUID format
        """
        # Simple UUID format check (8-4-4-4-12 hex digits)
        if len(value) == 36 and value.count("-") == 4:
            parts = value.split("-")
            if len(parts) == 5:
                return all(
                    len(part) == expected
                    for part, expected in zip(parts, [8, 4, 4, 4, 12], strict=False)
                )
        # Also check for UUID without dashes
        if len(value) == 32:
            try:
                int(value, 16)
                return True
            except ValueError:
                return False
        return False

    def extract_original_text(
        self,
        original_text_element,
        section=None
    ) -> str | None:
        """Extract original text, resolving references if needed.

        C-CDA allows originalText to contain either:
        1. Direct text value: <originalText>Hypertension</originalText>
        2. Reference to narrative: <originalText><reference value="#id"/></originalText>

        This method handles both cases, with reference resolution for case 2.

        Args:
            original_text_element: ED (Encapsulated Data) element
            section: Optional Section containing narrative block for reference resolution

        Returns:
            Resolved text string or None

        Reference:
            https://github.com/HL7/C-CDA-Examples - Narrative Reference examples
        """
        if not original_text_element:
            return None

        # Case 1: Direct value
        if hasattr(original_text_element, 'value') and original_text_element.value:
            return original_text_element.value

        # Case 2: Reference to narrative
        if hasattr(original_text_element, 'reference') and original_text_element.reference:
            ref_value = original_text_element.reference.value if hasattr(
                original_text_element.reference, 'value'
            ) else original_text_element.reference

            if ref_value and isinstance(ref_value, str) and ref_value.startswith('#'):
                content_id = ref_value[1:]  # Remove '#' prefix

                # If section provided, search narrative
                if section and hasattr(section, 'text'):
                    resolved = self._resolve_narrative_reference(section.text, content_id)
                    if resolved:
                        return resolved

                # Reference couldn't be resolved
                # Log warning but don't fail
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.debug(f"Could not resolve narrative reference: {ref_value}")

        return None

    def _resolve_narrative_reference(self, narrative_text, content_id: str) -> str | None:
        """Resolve a reference ID to text within narrative block.

        Searches the narrative block (which is XML/HTML) for an element
        with ID matching content_id and extracts its text content.

        Args:
            narrative_text: Narrative text block (may be string or object)
            content_id: ID to search for (without '#' prefix)

        Returns:
            Text content of referenced element or None
        """
        if not narrative_text:
            return None

        # Convert narrative to string if needed
        narrative_str = str(narrative_text) if hasattr(narrative_text, '__str__') else narrative_text

        # Simple regex-based resolution
        # Look for: <content ID="content_id">text</content>
        # or: <td ID="content_id">text</td>
        # or any element with matching ID
        import re

        # Pattern: any tag with ID="content_id">captured_text</tag>
        pattern = rf'<[^>]+\s+ID="{re.escape(content_id)}"[^>]*>(.*?)</[^>]+>'
        match = re.search(pattern, narrative_str, re.IGNORECASE | re.DOTALL)

        if match:
            # Extract text, remove any inner tags
            text = match.group(1)
            # Strip HTML tags from extracted text
            text = re.sub(r'<[^>]+>', '', text)
            return text.strip()

        return None

    def _extract_text_reference(self, entry) -> str | None:
        """Extract reference ID from entry's text element.

        Per C-CDA standard, entries can have:
        <text><reference value="#some-id"/></text>

        Args:
            entry: C-CDA entry (Observation, Act, Procedure, etc.)

        Returns:
            Reference ID without '#' prefix, or None if no reference found
        """
        if not hasattr(entry, 'text') or not entry.text:
            return None

        # Check if text has a reference element
        if hasattr(entry.text, 'reference') and entry.text.reference:
            ref_value = entry.text.reference.value
            if ref_value and ref_value.startswith('#'):
                # Remove '#' prefix to get the ID
                return ref_value[1:]

        return None

    def _generate_narrative(self, entry=None, section=None) -> JSONObject | None:
        """Generate FHIR Narrative from C-CDA entry text element.

        Per C-CDA on FHIR IG, supports three scenarios:
        1. Entry with text/reference: Extract referenced narrative from section
        2. Entry with mixed content + reference: Combine both in separate divs
        3. Entry with text value only: Use the text directly as narrative

        Creates a FHIR Narrative element suitable for resource.text field.

        Resolves Known Issue #13: "Section Narrative Not Propagated"

        Args:
            entry: C-CDA entry (Observation, Act, Procedure, etc.) with optional text element
            section: C-CDA Section object containing text/narrative (optional for Scenario 3)

        Returns:
            FHIR Narrative dict with status and div, or None if no text found

        Example:
            >>> # Scenario 1: Entry with reference to specific narrative portion
            >>> narrative = converter._generate_narrative(observation, section)
            >>> # Result: {"status": "generated", "div": "<div xmlns=...><p id='ref1'>...</p></div>"}
            >>>
            >>> # Scenario 3: Entry with direct text content
            >>> narrative = converter._generate_narrative(observation)
            >>> # Result: {"status": "generated", "div": "<div xmlns=...><p>Direct text</p></div>"}

        Reference:
            - C-CDA on FHIR Mapping: https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html
            - FHIR Narrative: https://hl7.org/fhir/narrative.html
        """
        # Must have entry
        if not entry:
            return None

        # Check if entry has text element
        if not hasattr(entry, 'text') or not entry.text:
            return None

        import html

        # Extract reference ID if present
        reference_id = self._extract_text_reference(entry)

        # Extract direct text value if present
        direct_text = None
        if hasattr(entry.text, 'value') and entry.text.value:
            direct_text = entry.text.value.strip()

        # Scenario 1 & 2: Entry has text/reference (with or without mixed content)
        if reference_id:
            # Need section to resolve reference
            if not section or not hasattr(section, 'text') or not section.text:
                # Can't resolve reference, fall back to direct text if available
                if direct_text:
                    # Scenario 3 fallback
                    escaped_text = html.escape(direct_text)
                    xhtml_div = f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escaped_text}</p></div>'
                    return {"status": "generated", "div": xhtml_div}
                return None

            from ccda_to_fhir.utils.struc_doc_utils import element_to_html, find_element_by_id

            # Find the referenced element in section narrative
            referenced_element = find_element_by_id(section.text, reference_id)
            if not referenced_element:
                # Reference not found, fall back to direct text if available
                if direct_text:
                    escaped_text = html.escape(direct_text)
                    xhtml_div = f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escaped_text}</p></div>'
                    return {"status": "generated", "div": xhtml_div}
                return None

            # Convert referenced element to HTML
            referenced_html = element_to_html(referenced_element)
            if not referenced_html or referenced_html.strip() == "":
                # Empty reference, fall back to direct text if available
                if direct_text:
                    escaped_text = html.escape(direct_text)
                    xhtml_div = f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escaped_text}</p></div>'
                    return {"status": "generated", "div": xhtml_div}
                return None

            # Check if there's also mixed content (Scenario 2)
            if direct_text:
                # Scenario 2: Mixed content + reference
                # Per IG: wrap each part in separate divs for clarity
                escaped_text = html.escape(direct_text)
                xhtml_div = (
                    f'<div xmlns="http://www.w3.org/1999/xhtml">'
                    f'<div><p>{escaped_text}</p></div>'
                    f'<div>{referenced_html}</div>'
                    f'</div>'
                )
            else:
                # Scenario 1: Reference only
                xhtml_div = f'<div xmlns="http://www.w3.org/1999/xhtml">{referenced_html}</div>'

            return {"status": "generated", "div": xhtml_div}

        # Scenario 3: Entry has text value only (no reference)
        elif direct_text:
            escaped_text = html.escape(direct_text)
            xhtml_div = f'<div xmlns="http://www.w3.org/1999/xhtml"><p>{escaped_text}</p></div>'
            return {"status": "generated", "div": xhtml_div}

        # No text content at all
        return None

    def create_data_absent_reason_extension(
        self, null_flavor: str | None, default_reason: str = "unknown"
    ) -> JSONObject:
        """Create a FHIR data-absent-reason extension from C-CDA nullFlavor.

        Per C-CDA on FHIR IG ConceptMap CF-NullFlavorDataAbsentReason, maps C-CDA nullFlavor
        codes to FHIR data-absent-reason extension values. This should be used when a required
        FHIR element has a nullFlavor in C-CDA.

        Per US Core guidance: when an element is not required, omit the element entirely rather
        than including data-absent-reason. This method is for required elements only.

        Args:
            null_flavor: C-CDA nullFlavor code (e.g., "UNK", "NA", "ASKU")
            default_reason: Fallback data-absent-reason code if nullFlavor is None or unmapped
                          (default: "unknown")

        Returns:
            FHIR extension dict with data-absent-reason

        Examples:
            >>> # Unknown abatement date
            >>> ext = converter.create_data_absent_reason_extension("UNK")
            >>> # Result: {"url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
            >>>          "valueCode": "unknown"}
            >>>
            >>> # Asked but unknown
            >>> ext = converter.create_data_absent_reason_extension("ASKU")
            >>> # Result: {"url": "...", "valueCode": "asked-unknown"}

        Reference:
            - Official ConceptMap: https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-NullFlavorDataAbsentReason.html
            - FHIR Extension: http://hl7.org/fhir/R4/extension-data-absent-reason.html
            - C-CDA NullFlavor: http://terminology.hl7.org/CodeSystem/v3-NullFlavor
            - FHIR DataAbsentReason: http://terminology.hl7.org/CodeSystem/data-absent-reason
        """
        from ccda_to_fhir.constants import NULL_FLAVOR_TO_DATA_ABSENT_REASON, FHIRSystems

        # Map nullFlavor to data-absent-reason code
        if null_flavor:
            # Case-insensitive lookup
            null_flavor_upper = null_flavor.upper()
            reason_code = NULL_FLAVOR_TO_DATA_ABSENT_REASON.get(null_flavor_upper, default_reason)
        else:
            reason_code = default_reason

        return {
            "url": FHIRSystems.DATA_ABSENT_REASON,
            "valueCode": reason_code,
        }

    def map_null_flavor_to_data_absent_reason(
        self, null_flavor: str | None, default: str = "unknown"
    ) -> str:
        """Map C-CDA nullFlavor to FHIR data-absent-reason code.

        Convenience method for getting just the code value without the full extension structure.

        Args:
            null_flavor: C-CDA nullFlavor code (e.g., "UNK", "NA", "ASKU")
            default: Fallback data-absent-reason code if nullFlavor is None or unmapped

        Returns:
            FHIR data-absent-reason code

        Example:
            >>> code = converter.map_null_flavor_to_data_absent_reason("UNK")
            >>> # Result: "unknown"
        """
        from ccda_to_fhir.constants import NULL_FLAVOR_TO_DATA_ABSENT_REASON

        if null_flavor:
            null_flavor_upper = null_flavor.upper()
            return NULL_FLAVOR_TO_DATA_ABSENT_REASON.get(null_flavor_upper, default)
        return default

    def extract_notes_from_element(
        self,
        element,
        include_text: bool = True,
        include_comments: bool = True,
        include_author_time: bool = False,
    ) -> list[JSONObject]:
        """Extract FHIR Annotation notes from a C-CDA element.

        This method extracts notes from two sources:
        1. The element's text field (if include_text=True)
        2. Comment Activity entries in entry_relationship (if include_comments=True)

        Args:
            element: C-CDA element (Observation, Procedure, SubstanceAdministration, etc.)
            include_text: Whether to extract from element.text (default True)
            include_comments: Whether to extract from Comment Activity entries (default True)
            include_author_time: Whether to include author time in comment notes (default False)

        Returns:
            List of FHIR Annotation objects (dicts with 'text' field, optionally 'time')

        Example:
            >>> notes = converter.extract_notes_from_element(observation)
            >>> # Result: [{"text": "Patient reported..."}]
        """
        from ccda_to_fhir.constants import TemplateIds

        notes: list[JSONValue] = []

        # Extract from text element
        if include_text and hasattr(element, "text") and element.text:
            text_content = None
            if isinstance(element.text, str):
                text_content = element.text
            elif hasattr(element.text, "value") and element.text.value:
                text_content = element.text.value
            elif hasattr(element.text, "reference"):
                # Reference to narrative - skip (could resolve if needed)
                pass

            if text_content:
                notes.append({"text": text_content})

        # Extract from Comment Activity entries
        if include_comments and hasattr(element, "entry_relationship") and element.entry_relationship:
            for entry_rel in element.entry_relationship:
                if not hasattr(entry_rel, "act") or not entry_rel.act:
                    continue

                act = entry_rel.act

                # Check if it's a Comment Activity
                if not hasattr(act, "template_id") or not act.template_id:
                    continue

                for template in act.template_id:
                    if template.root == TemplateIds.COMMENT_ACTIVITY:
                        # This is a Comment Activity - extract text
                        if hasattr(act, "text") and act.text:
                            comment_text = None
                            if isinstance(act.text, str):
                                comment_text = act.text
                            elif hasattr(act.text, "value") and act.text.value:
                                comment_text = act.text.value

                            if comment_text:
                                note: JSONObject = {"text": comment_text}

                                # Optionally add author time
                                if include_author_time:
                                    if hasattr(act, "author") and act.author and len(act.author) > 0:
                                        author = act.author[0]
                                        if hasattr(author, "time") and author.time:
                                            if hasattr(author.time, "value") and author.time.value:
                                                time_str = self.convert_date(author.time.value)
                                                if time_str:
                                                    note["time"] = time_str

                                notes.append(note)
                        break

        return notes

    def _generate_practitioner_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Practitioner ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _generate_organization_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Organization ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Organization", root, extension)

    def _generate_device_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Device ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Device", root, extension)

    def _generate_location_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Location ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Location", root, extension)

    def convert_addresses(self, addresses, include_type: bool = False) -> list[JSONObject]:
        """Convert C-CDA AD elements to FHIR Address objects.

        Handles both single AD and list of AD inputs. Converts all address
        components including use, line, city, state, postalCode,
        country, and period.

        Args:
            addresses: C-CDA AD element(s) - single or list
            include_type: If True, adds type="physical" to each address.
                         Default False to match original converter behavior.
                         Only PatientConverter historically added type.

        Returns:
            List of FHIR Address objects
        """
        from ccda_to_fhir.constants import ADDRESS_USE_MAP, FHIRCodes

        if addresses is None:
            return []

        fhir_addresses: list[JSONValue] = []

        # Normalize to list
        addr_list = addresses if isinstance(addresses, list) else [addresses]

        for addr in addr_list:
            if addr is None:
                continue

            fhir_address: JSONObject = {}

            # Use
            if hasattr(addr, "use") and addr.use:
                fhir_use = ADDRESS_USE_MAP.get(addr.use)
                if fhir_use:
                    fhir_address["use"] = fhir_use

            # Type - only add if explicitly requested (matches original PatientConverter behavior)
            if include_type:
                fhir_address["type"] = FHIRCodes.AddressType.PHYSICAL

            # Street address lines
            if hasattr(addr, "street_address_line") and addr.street_address_line:
                fhir_address["line"] = addr.street_address_line

            # City - handle potential list type
            if hasattr(addr, "city") and addr.city:
                if isinstance(addr.city, list):
                    fhir_address["city"] = addr.city[0]
                else:
                    fhir_address["city"] = addr.city

            # State - handle potential list type
            if hasattr(addr, "state") and addr.state:
                if isinstance(addr.state, list):
                    fhir_address["state"] = addr.state[0]
                else:
                    fhir_address["state"] = addr.state

            # Postal code - handle potential list type
            if hasattr(addr, "postal_code") and addr.postal_code:
                if isinstance(addr.postal_code, list):
                    fhir_address["postalCode"] = addr.postal_code[0]
                else:
                    fhir_address["postalCode"] = addr.postal_code

            # Country - handle potential list type
            if hasattr(addr, "country") and addr.country:
                if isinstance(addr.country, list):
                    fhir_address["country"] = addr.country[0]
                else:
                    fhir_address["country"] = addr.country

            # Period from useable_period
            if hasattr(addr, "useable_period") and addr.useable_period:
                period: JSONObject = {}
                if hasattr(addr.useable_period, "low") and addr.useable_period.low:
                    start = self.convert_date(addr.useable_period.low.value)
                    if start:
                        period["start"] = start
                if hasattr(addr.useable_period, "high") and addr.useable_period.high:
                    end = self.convert_date(addr.useable_period.high.value)
                    if end:
                        period["end"] = end
                if period:
                    fhir_address["period"] = period

            # Only add if we have meaningful content
            if fhir_address:
                fhir_addresses.append(fhir_address)

        return fhir_addresses

    def convert_address_single(self, addresses) -> JSONObject:
        """Convert C-CDA AD element(s) to a single FHIR Address.

        For resources like Location where address is 0..1, not an array.
        Returns the first address if multiple provided.

        Args:
            addresses: C-CDA AD element(s) - single or list

        Returns:
            Single FHIR Address object or empty dict
        """
        result = self.convert_addresses(addresses)
        return result[0] if result else {}

    def _generate_condition_id(self, root: str | None, extension: str | None) -> str:
        """Generate FHIR Condition ID using cached UUID v4 from C-CDA identifiers.

        Args:
            root: The OID or UUID root
            extension: The extension value

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Condition", root, extension)

    def _generate_condition_id_from_observation(self, observation) -> str | None:
        """Generate a Condition resource ID from a Problem Observation.

        Uses the same ID generation logic as ConditionConverter to ensure
        consistent references to Condition resources.

        Args:
            observation: Problem Observation with ID

        Returns:
            Condition resource ID string, or None if no identifiers available
        """
        if hasattr(observation, "id") and observation.id:
            for id_elem in observation.id:
                if hasattr(id_elem, "root") and id_elem.root:
                    extension = id_elem.extension if hasattr(id_elem, "extension") else None
                    return self._generate_condition_id(id_elem.root, extension)

        from ccda_to_fhir.logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(
            "Cannot generate Condition ID from Problem Observation: no identifiers provided. "
            "Skipping reasonReference."
        )
        return None

    def extract_reasons_from_entry_relationships(
        self,
        entry_relationships: list,
        problem_template_id: str = "2.16.840.1.113883.10.20.22.4.4",
    ) -> dict[str, list]:
        """Extract reason codes and references from C-CDA entry relationships.

        Looks for RSON (reason) type relationships and extracts:
        - Problem Observations → Condition references (if Condition exists in registry)
        - Other observations → CodeableConcepts from observation.value

        This is a common pattern used across multiple converters including:
        - ProcedureConverter
        - ServiceRequestConverter
        - EncounterConverter

        Args:
            entry_relationships: List of C-CDA EntryRelationship elements
            problem_template_id: Template ID for Problem Observation
                (default: standard C-CDA template 2.16.840.1.113883.10.20.22.4.4)

        Returns:
            Dict with "codes" (list of CodeableConcept) and "references" (list of Reference)
        """
        from ccda_to_fhir.constants import FHIRCodes

        reason_codes: list[JSONValue] = []
        reason_refs: list[JSONValue] = []

        if not entry_relationships:
            return {"codes": reason_codes, "references": reason_refs}

        for entry_rel in entry_relationships:
            # Look for RSON (reason) relationships
            type_code = None
            if hasattr(entry_rel, "type_code"):
                type_code = entry_rel.type_code
                # Handle TypeCodes enum if present
                if hasattr(type_code, "value"):
                    type_code = type_code.value

            if type_code != "RSON":
                continue

            if not hasattr(entry_rel, "observation") or not entry_rel.observation:
                continue

            obs = entry_rel.observation

            # Check if this observation IS a Problem Observation
            is_problem_obs = False
            if hasattr(obs, "template_id") and obs.template_id:
                for template in obs.template_id:
                    if hasattr(template, "root") and template.root == problem_template_id:
                        is_problem_obs = True
                        break

            if is_problem_obs:
                # This is a Problem Observation - check if Condition exists
                condition_id = self._generate_condition_id_from_observation(obs)

                # Skip if we couldn't generate a valid ID
                if not condition_id:
                    continue

                # Per C-CDA on FHIR spec: only create reasonReference if the Problem
                # Observation was converted to a Condition resource elsewhere in the document
                if self.reference_registry and self.reference_registry.has_resource(
                    FHIRCodes.ResourceTypes.CONDITION, condition_id
                ):
                    # Condition exists - use reasonReference
                    reason_refs.append({
                        "reference": f"urn:uuid:{condition_id}"
                    })
                else:
                    # Inline Problem Observation not converted - use reasonCode
                    codes = self._extract_codes_from_observation_value(obs)
                    reason_codes.extend(codes)
            else:
                # Extract reason code from observation.value (non-Problem observation)
                codes = self._extract_codes_from_observation_value(obs)
                reason_codes.extend(codes)

        return {"codes": reason_codes, "references": reason_refs}

    def _extract_codes_from_observation_value(self, obs) -> list[JSONObject]:
        """Extract CodeableConcepts from an observation's value field.

        Handles both single value objects and lists of values, as C-CDA allows both.

        Args:
            obs: C-CDA Observation element

        Returns:
            List of FHIR CodeableConcept dicts
        """
        codes: list[JSONValue] = []

        if not hasattr(obs, "value") or not obs.value:
            return codes

        # Handle both single value and list of values
        values = obs.value if isinstance(obs.value, list) else [obs.value]

        for value in values:
            if hasattr(value, "code") and value.code:
                codeable = self.create_codeable_concept(
                    code=value.code,
                    code_system=value.code_system if hasattr(value, "code_system") else None,
                    display_name=value.display_name if hasattr(value, "display_name") else None,
                )
                if codeable:
                    codes.append(codeable)

        return codes

    def convert_telecom(self, telecoms) -> list[JSONObject]:
        """Convert C-CDA TEL elements to FHIR ContactPoint objects.

        Handles both single TEL and list of TEL inputs. Parses URI schemes
        (tel:, mailto:, fax:, http:) and maps to FHIR system codes.

        Args:
            telecoms: C-CDA TEL element(s) - single or list

        Returns:
            List of FHIR ContactPoint objects
        """
        from ccda_to_fhir.constants import TELECOM_USE_MAP, FHIRCodes

        if telecoms is None:
            return []

        contact_points: list[JSONValue] = []

        # Normalize to list
        telecom_list = telecoms if isinstance(telecoms, list) else [telecoms]

        for telecom in telecom_list:
            if telecom is None:
                continue

            if not hasattr(telecom, "value") or not telecom.value:
                continue

            contact_point: JSONObject = {}
            value = telecom.value

            # Parse system and value from URI scheme prefix
            if value.startswith("tel:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value[4:]  # Remove "tel:" prefix
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]  # Remove "mailto:" prefix
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]  # Remove "fax:" prefix
            elif value.startswith("http://") or value.startswith("https://"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                # Unknown format - assume phone if no recognized prefix
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value

            # Use
            if hasattr(telecom, "use") and telecom.use:
                fhir_use = TELECOM_USE_MAP.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            # Period from use_period
            if hasattr(telecom, "use_period") and telecom.use_period:
                period: JSONObject = {}
                if hasattr(telecom.use_period, "low") and telecom.use_period.low:
                    start = self.convert_date(telecom.use_period.low.value)
                    if start:
                        period["start"] = start
                if hasattr(telecom.use_period, "high") and telecom.use_period.high:
                    end = self.convert_date(telecom.use_period.high.value)
                    if end:
                        period["end"] = end
                if period:
                    contact_point["period"] = period

            if contact_point:
                contact_points.append(contact_point)

        return contact_points

    # ENXP qualifier to FHIR name use mapping
    # HL7 v3 EntityNamePartQualifier codes that affect FHIR HumanName.use
    _ENXP_QUALIFIER_TO_USE = {
        "CL": "nickname",   # Callme - name used informally
        "BR": "maiden",     # Birth name
        "SP": "maiden",     # Spouse name (previous married name when remarried)
    }

    def convert_human_names(self, names) -> list[JSONObject]:
        """Convert C-CDA PN elements to FHIR HumanName objects.

        Handles person names from Patient, Practitioner, RelatedPerson contexts.
        Fully supports HL7 v3 name model including:
        - Name use codes (L, OR, P, etc.) mapped to FHIR use
        - ENXP qualifiers (CL, BR, IN, AC, etc.)
        - Prefix, given, family, suffix components
        - Delimiters for text representation
        - Valid time periods
        - Null flavors

        Args:
            names: C-CDA PN element(s) - single or list

        Returns:
            List of FHIR HumanName objects
        """
        from ccda_to_fhir.constants import NAME_USE_MAP, FHIRCodes

        if names is None:
            return []

        fhir_names: list[JSONValue] = []

        # Normalize to list
        name_list = names if isinstance(names, list) else [names]

        for name in name_list:
            if name is None:
                continue

            fhir_name: JSONObject = {}

            # Handle null_flavor - name is explicitly unknown/masked
            if hasattr(name, "null_flavor") and name.null_flavor:
                fhir_name["extension"] = [{
                    "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                    "valueCode": self._map_null_flavor_to_data_absent_reason(name.null_flavor)
                }]
                fhir_names.append(fhir_name)
                continue

            # Track if any ENXP qualifier should override the name use
            qualifier_use = None

            # Name use mapping from PN.use attribute
            if hasattr(name, "use") and name.use:
                fhir_name["use"] = NAME_USE_MAP.get(name.use, FHIRCodes.NameUse.USUAL)

            # Family name - handle ENXP type with qualifier
            if hasattr(name, "family") and name.family:
                family_value, family_qualifier = self._extract_enxp_value_and_qualifier(name.family)
                if family_value:
                    fhir_name["family"] = family_value
                if family_qualifier and family_qualifier in self._ENXP_QUALIFIER_TO_USE:
                    qualifier_use = self._ENXP_QUALIFIER_TO_USE[family_qualifier]

            # Given names - handle list of ENXP with qualifiers
            if hasattr(name, "given") and name.given:
                given_names = []
                for given in name.given:
                    value, qualifier = self._extract_enxp_value_and_qualifier(given)
                    if value:
                        given_names.append(value)
                    # CL qualifier on given name indicates nickname
                    if qualifier and qualifier in self._ENXP_QUALIFIER_TO_USE:
                        qualifier_use = self._ENXP_QUALIFIER_TO_USE[qualifier]
                if given_names:
                    fhir_name["given"] = given_names

            # Prefix - handle list of ENXP
            if hasattr(name, "prefix") and name.prefix:
                prefixes = []
                for prefix in name.prefix:
                    value, _ = self._extract_enxp_value_and_qualifier(prefix)
                    if value:
                        prefixes.append(value)
                if prefixes:
                    fhir_name["prefix"] = prefixes

            # Suffix - handle list of ENXP (including academic qualifiers)
            if hasattr(name, "suffix") and name.suffix:
                suffixes = []
                for suffix in name.suffix:
                    value, _ = self._extract_enxp_value_and_qualifier(suffix)
                    if value:
                        suffixes.append(value)
                if suffixes:
                    fhir_name["suffix"] = suffixes

            # If ENXP qualifier indicates a specific use, and no explicit use was set, apply it
            if qualifier_use and "use" not in fhir_name:
                fhir_name["use"] = qualifier_use

            # Build text representation using delimiters if present
            text_parts = []
            if "prefix" in fhir_name:
                text_parts.extend(fhir_name["prefix"])
            if "given" in fhir_name:
                text_parts.extend(fhir_name["given"])
            if "family" in fhir_name:
                text_parts.append(fhir_name["family"])
            if "suffix" in fhir_name:
                text_parts.extend(fhir_name["suffix"])

            if text_parts:
                # Use delimiter if provided, otherwise space
                delimiter = " "
                if hasattr(name, "delimiter") and name.delimiter:
                    # delimiter is list[str], use first one
                    if isinstance(name.delimiter, list) and len(name.delimiter) > 0:
                        delimiter = name.delimiter[0]
                    elif isinstance(name.delimiter, str):
                        delimiter = name.delimiter
                fhir_name["text"] = delimiter.join(text_parts)

            # Period from valid_time
            if hasattr(name, "valid_time") and name.valid_time:
                period: JSONObject = {}
                if hasattr(name.valid_time, "low") and name.valid_time.low:
                    start = self.convert_date(name.valid_time.low.value)
                    if start:
                        period["start"] = start
                if hasattr(name.valid_time, "high") and name.valid_time.high:
                    end = self.convert_date(name.valid_time.high.value)
                    if end:
                        period["end"] = end
                if period:
                    fhir_name["period"] = period

            # Only add if we have meaningful content
            if fhir_name:
                fhir_names.append(fhir_name)

        return fhir_names

    def _extract_enxp_value_and_qualifier(self, enxp) -> tuple[str | None, str | None]:
        """Extract value and qualifier from an ENXP element.

        Args:
            enxp: ENXP element or string

        Returns:
            Tuple of (value, qualifier)
        """
        if enxp is None:
            return (None, None)

        if isinstance(enxp, str):
            return (enxp, None)

        value = None
        qualifier = None

        if hasattr(enxp, "value"):
            value = enxp.value
        else:
            value = str(enxp) if enxp else None

        if hasattr(enxp, "qualifier"):
            qualifier = enxp.qualifier

        return (value, qualifier)

    def _map_null_flavor_to_data_absent_reason(self, null_flavor: str) -> str:
        """Map HL7 v3 NullFlavor to FHIR data-absent-reason.

        Args:
            null_flavor: HL7 v3 NullFlavor code

        Returns:
            FHIR data-absent-reason code
        """
        mapping = {
            "NI": "unknown",        # No Information
            "UNK": "unknown",       # Unknown
            "ASKU": "asked-unknown",  # Asked but unknown
            "NAV": "temp-unknown",  # Temporarily unavailable
            "NASK": "not-asked",    # Not asked
            "MSK": "masked",        # Masked
            "NA": "not-applicable", # Not applicable
            "OTH": "unknown",       # Other
            "NINF": "negative-infinity",
            "PINF": "positive-infinity",
        }
        return mapping.get(null_flavor, "unknown")

    # -------------------------------------------------------------------------
    # Performer Extraction Helpers
    # -------------------------------------------------------------------------
    # These helpers support common patterns for extracting practitioner and
    # organization references from C-CDA performer and author elements.

    NPI_OID = "2.16.840.1.113883.4.6"  # National Provider Identifier

    def select_preferred_identifier(
        self,
        identifiers: list,
        prefer_npi: bool = True,
    ) -> tuple[str | None, str | None]:
        """Select the preferred identifier from a list of C-CDA identifiers.

        By default prefers NPI (National Provider Identifier) when available,
        otherwise returns the first valid identifier.

        Args:
            identifiers: List of C-CDA II (Instance Identifier) elements
            prefer_npi: If True, prefer NPI identifier over others (default True)

        Returns:
            Tuple of (root, extension) for the selected identifier, or (None, None)
        """
        if not identifiers:
            return (None, None)

        npi_id = None
        first_id = None

        for id_elem in identifiers:
            root = getattr(id_elem, "root", None)
            if not root:
                continue

            if first_id is None:
                first_id = id_elem

            # Check for NPI
            if prefer_npi and root == self.NPI_OID:
                npi_id = id_elem
                break

        # Use NPI if available and preferred, otherwise use first
        selected = npi_id if npi_id else first_id
        if selected:
            return (selected.root, getattr(selected, "extension", None))

        return (None, None)

    def create_practitioner_reference_from_entity(
        self,
        assigned_entity,
        create_resource: bool = False,
        pending_resources: list | None = None,
    ) -> JSONObject | None:
        """Create a Practitioner reference from a C-CDA AssignedEntity.

        Optionally creates the Practitioner resource if it doesn't already exist
        in the reference registry.

        Args:
            assigned_entity: C-CDA AssignedEntity element
            create_resource: If True, creates Practitioner resource if not in registry
            pending_resources: List to append created Practitioner resources to

        Returns:
            FHIR Reference dict or None if no valid identifier found
        """
        if not assigned_entity:
            return None

        # Check for assigned_person (indicates this is a practitioner)
        if not (hasattr(assigned_entity, "assigned_person") and assigned_entity.assigned_person):
            return None

        # Get identifiers
        ids = getattr(assigned_entity, "id", None)
        if not ids:
            return None

        root, extension = self.select_preferred_identifier(ids)
        if not root:
            return None

        pract_id = self._generate_practitioner_id(root, extension)

        # Create resource if requested and not already in registry
        if create_resource and self.reference_registry:
            if not self.reference_registry.has_resource("Practitioner", pract_id):
                from ccda_to_fhir.converters.practitioner import PractitionerConverter

                pract_converter = PractitionerConverter(
                    code_system_mapper=self.code_system_mapper
                )
                practitioner = pract_converter.convert(assigned_entity)
                practitioner["id"] = pract_id

                # Add to pending resources list
                if pending_resources is not None:
                    pending_resources.append(practitioner)

                # Register with reference registry
                self.reference_registry.register_resource(practitioner)

        return {"reference": f"urn:uuid:{pract_id}"}

    def create_organization_reference_from_entity(
        self,
        represented_organization,
        create_resource: bool = False,
        pending_resources: list | None = None,
    ) -> JSONObject | None:
        """Create an Organization reference from a C-CDA RepresentedOrganization.

        Optionally creates the Organization resource if it doesn't already exist
        in the reference registry.

        Args:
            represented_organization: C-CDA Organization element
            create_resource: If True, creates Organization resource if not in registry
            pending_resources: List to append created Organization resources to

        Returns:
            FHIR Reference dict or None if no valid identifier found
        """
        if not represented_organization:
            return None

        # Get identifiers
        ids = getattr(represented_organization, "id", None)
        if not ids:
            return None

        root, extension = self.select_preferred_identifier(ids)
        if not root:
            return None

        org_id = self._generate_organization_id(root, extension)

        # Create resource if requested and not already in registry
        if create_resource and self.reference_registry:
            if not self.reference_registry.has_resource("Organization", org_id):
                from ccda_to_fhir.converters.organization import OrganizationConverter

                org_converter = OrganizationConverter(
                    code_system_mapper=self.code_system_mapper
                )
                organization = org_converter.convert(represented_organization)
                organization["id"] = org_id

                # Add to pending resources list
                if pending_resources is not None:
                    pending_resources.append(organization)

                # Register with reference registry
                self.reference_registry.register_resource(organization)

        return {"reference": f"urn:uuid:{org_id}"}

    def extract_performer_function(
        self,
        function_code,
        exclude_codes: set[str] | None = None,
    ) -> JSONObject | None:
        """Extract performer function as FHIR CodeableConcept from C-CDA functionCode.

        Maps C-CDA ParticipationFunction codes to FHIR ParticipationType codes
        using the PARTICIPATION_FUNCTION_CODE_MAP.

        Args:
            function_code: C-CDA functionCode element
            exclude_codes: Set of codes to exclude (e.g., encounter-only codes)

        Returns:
            FHIR CodeableConcept for function, or None
        """
        from ccda_to_fhir.constants import PARTICIPATION_FUNCTION_CODE_MAP, FHIRSystems

        if not function_code:
            return None

        code = function_code.code if hasattr(function_code, "code") else None
        if not code:
            return None

        # Map known function codes or pass through if not in map
        mapped_code = PARTICIPATION_FUNCTION_CODE_MAP.get(code, code)

        # Check exclusion list
        if exclude_codes and mapped_code in exclude_codes:
            return None

        function_coding: JSONObject = {
            "system": FHIRSystems.V3_PARTICIPATION_TYPE,
            "code": mapped_code,
        }
        if hasattr(function_code, "display_name") and function_code.display_name:
            function_coding["display"] = function_code.display_name

        return {"coding": [function_coding]}

    def extract_code_translations(self, code) -> list[JSONObject]:
        """Extract translation codes from a C-CDA coded element.

        C-CDA codes often include translations to other code systems (e.g., SNOMED
        to ICD-10). This method extracts all translations into a normalized format.

        Args:
            code: C-CDA coded element (CD, CE, etc.) with optional translation attribute

        Returns:
            List of translation dicts with keys: code, code_system, display_name
        """
        translations: list[JSONValue] = []

        if not hasattr(code, "translation") or not code.translation:
            return translations

        for trans in code.translation:
            # Handle both object and dict representations
            if hasattr(trans, "code"):
                trans_code = trans.code
                trans_system = getattr(trans, "code_system", None)
                trans_display = getattr(trans, "display_name", None)
            elif isinstance(trans, dict):
                trans_code = trans.get("code")
                trans_system = trans.get("code_system")
                trans_display = trans.get("display_name")
            else:
                continue

            if trans_code and trans_system:
                translations.append({
                    "code": trans_code,
                    "code_system": trans_system,
                    "display_name": trans_display,
                })

        return translations

    def extract_performer_references(
        self,
        performers: list,
        prefer_npi: bool = False,
    ) -> list[JSONObject]:
        """Extract FHIR performer references from C-CDA performer elements.

        This is a shared utility for extracting Practitioner references from C-CDA
        performer elements. It handles the common pattern of iterating through
        performers, extracting assigned_entity identifiers, and creating FHIR
        Reference objects.

        For more complex scenarios (creating Practitioner resources, extracting
        organization references, or handling performer function codes), use the
        individual helper methods like create_practitioner_reference_from_entity().

        Args:
            performers: List of C-CDA Performer elements
            prefer_npi: If True, prefer NPI identifier over others (default False)

        Returns:
            List of FHIR Reference dicts (e.g., [{"reference": "urn:uuid:..."}])
        """
        if not performers:
            return []

        references: list[JSONValue] = []

        for performer in performers:
            if not performer:
                continue

            assigned_entity = getattr(performer, "assigned_entity", None)
            if not assigned_entity:
                continue

            ids = getattr(assigned_entity, "id", None)
            if not ids:
                continue

            # Select preferred identifier
            root, extension = self.select_preferred_identifier(ids, prefer_npi=prefer_npi)
            if root:
                practitioner_id = self._generate_practitioner_id(root, extension)
                references.append({"reference": f"urn:uuid:{practitioner_id}"})

        return references

    def map_status_code(
        self,
        status_code: CS | str | None,
        mapping: dict[str, str],
        default: str,
    ) -> str:
        """Map C-CDA status code to FHIR status using provided mapping.

        Generic utility for status code mapping used by all converters.
        Handles null/missing status codes gracefully.

        Args:
            status_code: C-CDA CS status code element (may be None)
            mapping: Dictionary mapping C-CDA codes (lowercase) to FHIR codes
            default: Default FHIR status if code is missing or unmapped

        Returns:
            FHIR status code string

        Example:
            >>> status = self.map_status_code(
            ...     observation.status_code,
            ...     OBSERVATION_STATUS_TO_FHIR,
            ...     FHIRCodes.ObservationStatus.FINAL
            ... )
        """
        if not status_code:
            return default

        code = None
        if hasattr(status_code, "code"):
            code = status_code.code
        elif isinstance(status_code, str):
            code = status_code

        if not code:
            return default

        # Case-insensitive lookup
        return mapping.get(code.lower(), default)

    def convert_code_to_codeable_concept(
        self,
        code,
        section=None,
        include_original_text: bool = True,
    ) -> JSONObject | None:
        """Convert a C-CDA coded element to FHIR CodeableConcept with translations.

        This is a higher-level method that combines translation extraction with
        CodeableConcept creation. It handles:
        - Primary code extraction
        - Translation extraction
        - Original text extraction (with optional narrative reference resolution)

        Args:
            code: C-CDA coded element (CD, CE, etc.)
            section: Optional section element for resolving narrative references
            include_original_text: Whether to include original_text in the result

        Returns:
            FHIR CodeableConcept dict or None if code is invalid
        """
        if not code or not hasattr(code, "code") or not code.code:
            return None

        # Extract translations
        translations = self.extract_code_translations(code)

        # Get original text if present
        original_text = None
        if include_original_text:
            if hasattr(code, "original_text") and code.original_text:
                original_text = self.extract_original_text(code.original_text, section=section)
            # Fallback to display_name if no original_text
            if not original_text and hasattr(code, "display_name") and code.display_name:
                original_text = code.display_name

        return self.create_codeable_concept(
            code=code.code,
            code_system=getattr(code, "code_system", None),
            display_name=getattr(code, "display_name", None),
            original_text=original_text,
            translations=translations,
        )

    # -------------------------------------------------------------------------
    # Error Handling Helpers
    # -------------------------------------------------------------------------
    # These methods provide consistent error handling across all converters.

    def require_field(
        self,
        value,
        field_name: str,
        resource_type: str,
        details: str = "",
    ) -> None:
        """Validate that a required field is present.

        Use this for FHIR required fields (1..1 or 1..*) where the conversion
        cannot proceed without the value.

        Args:
            value: The field value to check
            field_name: Name of the field for error message
            resource_type: FHIR resource type for error message
            details: Additional context about the requirement

        Raises:
            MissingRequiredFieldError: If value is None, empty string, or empty list

        Example:
            >>> self.require_field(observation.code, "code", "Observation")
            >>> # Raises MissingRequiredFieldError if code is missing
        """
        is_empty = (
            value is None
            or value == ""
            or (isinstance(value, list) and len(value) == 0)
        )

        if is_empty:
            raise MissingRequiredFieldError(
                field_name=field_name,
                resource_type=resource_type,
                details=details,
            )

    def optional_field(
        self,
        value,
        converter,
        field_name: str,
        default=None,
    ):
        """Convert an optional field, returning default if missing or on error.

        Use for optional FHIR fields (0..1 or 0..*) where conversion should
        continue even if the value is missing or malformed.

        Args:
            value: The field value (may be None)
            converter: Function to convert the value
            field_name: Name used in warning logs if conversion fails
            default: Value to return if field is missing or conversion fails

        Returns:
            Converted value, or default if missing/failed

        Example:
            >>> telecom = self.optional_field(
            ...     patient_role.telecom,
            ...     self.convert_telecom,
            ...     "telecom",
            ...     default=[]
            ... )
        """
        if value is None:
            return default

        try:
            result = converter(value)
            return result if result is not None else default
        except (CCDAConversionError, ValueError, TypeError, AttributeError) as e:
            logger.warning(
                f"Failed to convert optional field {field_name} "
                f"({type(e).__name__}): {e}",
                exc_info=True,
            )
            return default

    def map_status_code(
        self,
        status_code,
        mapping: dict[str, str],
        default: str,
    ) -> str:
        """Map C-CDA status code to FHIR status using provided mapping.

        Generic utility for status code mapping used by all converters.
        Handles null/missing status codes gracefully with case-insensitive lookup.

        Args:
            status_code: C-CDA CS status code element (may be None)
            mapping: Dictionary mapping C-CDA codes to FHIR codes
            default: Default FHIR status if code is missing or unmapped

        Returns:
            FHIR status code string

        Example:
            >>> status = self.map_status_code(
            ...     observation.status_code,
            ...     OBSERVATION_STATUS_TO_FHIR,
            ...     "final"
            ... )
        """
        if not status_code:
            return default

        code = None
        if hasattr(status_code, "code"):
            code = status_code.code
        elif isinstance(status_code, str):
            code = status_code

        if not code:
            return default

        # Case-insensitive lookup
        return mapping.get(code.lower(), default)

    def handle_duplicate_id(
        self,
        id_key: tuple[str | None, str | None],
        seen_ids: set[tuple[str | None, str | None]],
        resource_type: str,
    ) -> str | None:
        """Handle duplicate ID detection and generate fallback if needed.

        Many converters need to detect when C-CDA documents incorrectly reuse
        the same ID for multiple entries. This method centralizes that logic.

        Args:
            id_key: Tuple of (root, extension) from C-CDA identifier
            seen_ids: Set tracking previously seen IDs
            resource_type: Resource type for logging

        Returns:
            New unique ID if duplicate detected, None if ID is new

        Example:
            >>> id_key = (id_elem.root, id_elem.extension)
            >>> fallback = self.handle_duplicate_id(id_key, self.seen_ids, "Observation")
            >>> if fallback:
            ...     resource["id"] = fallback
            ... else:
            ...     resource["id"] = self.generate_resource_id(...)
            ...     self.seen_ids.add(id_key)
        """
        if id_key in seen_ids:
            root, extension = id_key
            logger.warning(
                f"{resource_type} ID {root} (extension={extension}) is reused in C-CDA document. "
                f"Generating unique ID to avoid duplicate {resource_type} resources."
            )
            return generate_id()

        return None
