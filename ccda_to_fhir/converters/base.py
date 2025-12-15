"""Base converter class with common utilities."""

from __future__ import annotations

import hashlib
import re
from abc import ABC, abstractmethod
from typing import ClassVar, Generic, TypeVar

from ccda_to_fhir.constants import FHIRSystems
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .code_systems import CodeSystemMapper

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
    ):
        """Initialize the converter.

        Args:
            code_system_mapper: Optional code system mapper for OID to URI conversion
        """
        self.code_system_mapper = code_system_mapper or CodeSystemMapper()

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
            # It's an OID
            identifier["system"] = self.map_oid_to_uri(root)

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
    ) -> JSONObject:
        """Create a FHIR CodeableConcept from C-CDA code elements.

        Args:
            code: The code value
            code_system: The code system OID
            display_name: Display name for the code
            original_text: Original text from the document
            translations: List of translation codes

        Returns:
            FHIR CodeableConcept as a dict
        """
        if not code and not original_text:
            return {}

        codeable_concept: JSONObject = {}
        codings: list[JSONObject] = []

        # Primary coding
        if code and code_system:
            coding: JSONObject = {
                "system": self.map_oid_to_uri(code_system),
                "code": code,
            }
            if display_name:
                coding["display"] = display_name
            codings.append(coding)

        # Translation codings
        if translations:
            for trans in translations:
                if trans.get("code") and trans.get("code_system"):
                    trans_coding: JSONObject = {
                        "system": self.map_oid_to_uri(trans["code_system"]),
                        "code": trans["code"],
                    }
                    if trans.get("display_name"):
                        trans_coding["display"] = trans["display_name"]
                    codings.append(trans_coding)

        if codings:
            codeable_concept["coding"] = codings

        # Original text
        if original_text:
            codeable_concept["text"] = original_text

        return codeable_concept

    def create_quantity(
        self, value: float | int | None, unit: str | None = None
    ) -> JSONObject:
        """Create a FHIR Quantity from C-CDA PQ (Physical Quantity).

        Args:
            value: The numeric value
            unit: The UCUM unit

        Returns:
            FHIR Quantity as a dict
        """
        if value is None:
            return {}

        quantity: JSONObject = {"value": value}

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
        - YYYYMMDDHH → YYYY-MM-DDThh:00:00
        - YYYYMMDDHHmm → YYYY-MM-DDThh:mm:00
        - YYYYMMDDHHmmss → YYYY-MM-DDThh:mm:ss

        Args:
            ccda_date: C-CDA formatted date string

        Returns:
            FHIR formatted date string, or None if invalid

        Examples:
            >>> convert_date("20240115")
            '2024-01-15'
            >>> convert_date("202401150930")
            '2024-01-15T09:30:00'
            >>> convert_date("20240115093000-0500")
            '2024-01-15T09:30:00-05:00'
            >>> convert_date("202X0115")  # Invalid - returns None
            None
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

            # Format result using template
            result = fhir_template.format(
                year=f"{dt.year:04d}",
                month=f"{dt.month:02d}",
                day=f"{dt.day:02d}",
                hour=f"{dt.hour:02d}",
                minute=f"{dt.minute:02d}",
                second=f"{dt.second:02d}",
            )

            # Handle timezone if present
            if tz_part and len(tz_part) >= 5:
                tz_sign = tz_part[0]
                tz_hours = tz_part[1:3]
                tz_mins = tz_part[3:5]
                try:
                    tz_h = int(tz_hours)
                    tz_m = int(tz_mins)
                    if 0 <= tz_h <= 14 and 0 <= tz_m <= 59:
                        result += f"{tz_sign}{tz_hours}:{tz_mins}"
                except ValueError:
                    from ccda_to_fhir.logging_config import get_logger
                    logger = get_logger(__name__)
                    logger.warning(f"Invalid timezone format: {tz_part}")

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
                    for part, expected in zip(parts, [8, 4, 4, 4, 12])
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
