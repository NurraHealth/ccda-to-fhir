"""Base converter class with common utilities."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, TypeVar

from ccda_to_fhir.constants import FHIRSystems
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .code_systems import CodeSystemMapper

if TYPE_CHECKING:
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
        """Generate a FHIR-compliant, collision-resistant resource ID.

        Priority:
        1. Use extension if available (cleaned)
        2. Use deterministic hash of root
        3. Use hash of fallback_context for deterministic fallback

        Args:
            root: OID or UUID root from C-CDA identifier
            extension: Extension from C-CDA identifier
            resource_type: FHIR resource type (lowercase, e.g., "condition")
            fallback_context: Additional context for fallback (e.g., timestamp + counter)

        Returns:
            FHIR-compliant ID (validated against [A-Za-z0-9\\-\\.]{1,64})

        Examples:
            >>> generate_resource_id(None, "ABC-123", "condition", "")
            'condition-abc-123'
            >>> generate_resource_id("2.16.840.1.113883", None, "allergy", "ctx")
            'allergy-a3f5e9c2d1b8'
        """
        prefix = resource_type.lower()

        # Priority 1: Use extension (cleaned and validated)
        if extension:
            # Remove invalid FHIR ID characters, keep alphanumeric, dash, dot
            clean_ext = re.sub(r'[^A-Za-z0-9\-\.]', '-', extension).lower()
            # Truncate to fit within 64 char limit (prefix + dash + ext)
            max_ext_len = 64 - len(prefix) - 1
            clean_ext = clean_ext[:max_ext_len]
            candidate_id = f"{prefix}-{clean_ext}"

            if self.FHIR_ID_PATTERN.match(candidate_id):
                return candidate_id

        # Priority 2: Use deterministic hash of root
        if root:
            # SHA256 hash -> first 12 hex chars (deterministic, low collision)
            root_hash = hashlib.sha256(root.encode('utf-8')).hexdigest()[:12]
            return f"{prefix}-{root_hash}"

        # Priority 3: Fallback with context hash (deterministic if context is same)
        if fallback_context:
            context_hash = hashlib.sha256(fallback_context.encode('utf-8')).hexdigest()[:12]
            return f"{prefix}-{context_hash}"

        # Priority 4: Last resort - log warning and use timestamp-based hash
        from ccda_to_fhir.logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(
            f"Generating fallback ID for {resource_type} with no identifiers",
            extra={"resource_type": resource_type}
        )
        # Use a random but deterministic hash of current timestamp
        import time
        fallback = hashlib.sha256(str(time.time()).encode()).hexdigest()[:12]
        return f"{prefix}-{fallback}"

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
        fhir_identifiers: list[JSONObject] = []

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
        codings: list[JSONObject] = []

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
