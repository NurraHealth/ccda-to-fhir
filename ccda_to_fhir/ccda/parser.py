"""C-CDA XML Parser.

Parses C-CDA XML documents into Pydantic models using lxml.

The parser handles:
- XML namespace resolution (urn:hl7-org:v3, urn:hl7-org:sdtc)
- xsi:type polymorphism for typed values
- Recursive nested structures
- Attribute and element parsing
- List aggregation for repeated elements
"""

from __future__ import annotations

from typing import Any, TypeVar

from lxml import etree
from pydantic import BaseModel

# Trigger model rebuilds for forward references
# This is necessary because models use TYPE_CHECKING for circular dependencies
# Import ALL models first so forward references resolve
from .models import (
    AD,
    BL,
    CD,
    CE,
    CO,
    CS,
    ED,
    EIVL_TS,
    EN,
    ENXP,
    II,
    INT,
    IVL_INT,
    IVL_PQ,
    IVL_TS,
    MO,
    ON,
    PIVL_TS,
    PN,
    PPD_PQ,
    PQ,
    REAL,
    RTO,
    ST,
    SXCM_TS,
    TEL,
    TN,
    TS,
    Act,
    ClinicalDocument,
    Encounter,
    Observation,
    Organizer,
    Procedure,
    SubstanceAdministration,
    Supply,
)
from .models.act import Reference
from .models.author import AssignedAuthoringDevice
from .models.clinical_document import HealthCareFacility, Informant, RelatedEntity
from .models.observation import EntryRelationship
from .models.organizer import OrganizerComponent
from .models.section import Entry, Section
from .models.substance_administration import ManufacturedProduct, Precondition
from .models.struc_doc import (
    Content,
    ListItem,
    Paragraph,
    StrucDocText,
    TableDataCell,
    TableHeaderCell,
)

# Trigger rebuilds in correct order (dependencies first)
# These models have forward references that are now available
EntryRelationship.model_rebuild()
Entry.model_rebuild()
OrganizerComponent.model_rebuild()
AssignedAuthoringDevice.model_rebuild()
HealthCareFacility.model_rebuild()

# Rebuild StrucDocText models (have circular references)
Paragraph.model_rebuild()
Content.model_rebuild()
ListItem.model_rebuild()
TableHeaderCell.model_rebuild()
TableDataCell.model_rebuild()
StrucDocText.model_rebuild()

# Rebuild Section (now references StrucDocText)
Section.model_rebuild()

# Rebuild clinical statement models that use EntryRelationship
Observation.model_rebuild()
Act.model_rebuild()
Organizer.model_rebuild()
Procedure.model_rebuild()
SubstanceAdministration.model_rebuild()
Encounter.model_rebuild()
Supply.model_rebuild()

# XML Namespaces used in C-CDA
NAMESPACES = {
    "hl7": "urn:hl7-org:v3",
    "sdtc": "urn:hl7-org:sdtc",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

T = TypeVar("T", bound=BaseModel)


class CDAParserError(Exception):
    """Base exception for C-CDA parsing errors."""

    pass


class UnknownTypeError(CDAParserError):
    """Raised when an unknown xsi:type is encountered."""

    def __init__(self, xsi_type: str, element_name: str):
        self.xsi_type = xsi_type
        self.element_name = element_name
        super().__init__(
            f"Unknown xsi:type '{xsi_type}' for element '{element_name}'. "
            f"This may indicate a new data type that needs to be added to the parser."
        )


class MalformedXMLError(CDAParserError):
    """Raised when XML structure is malformed."""

    pass


# Mapping from xsi:type values to Pydantic model classes
XSI_TYPE_MAP: dict[str, type[BaseModel]] = {
    # Simple types
    "ST": ST,
    "BL": BL,
    "INT": INT,
    "REAL": REAL,
    # Coded types
    "CD": CD,
    "CE": CE,
    "CO": CO,
    "CS": CS,
    # Identifiers
    "II": II,
    # Temporal types
    "TS": TS,
    "IVL_TS": IVL_TS,
    "PIVL_TS": PIVL_TS,
    "EIVL_TS": EIVL_TS,
    "SXCM_TS": SXCM_TS,
    # Quantity types
    "PQ": PQ,
    "PPD_PQ": PPD_PQ,
    "IVL_PQ": IVL_PQ,
    "IVL_INT": IVL_INT,
    "MO": MO,
    "RTO": RTO,
    # Encapsulated data
    "ED": ED,
    # Telecom and address
    "TEL": TEL,
    "AD": AD,
    # Names
    "EN": EN,
    "PN": PN,
    "ON": ON,
    "TN": TN,
}


def _get_qname(tag: str, namespace: str = "hl7") -> str:
    """Get qualified name for an XML tag."""
    return f"{{{NAMESPACES[namespace]}}}{tag}"


def _strip_namespace(tag: str) -> str:
    """Strip namespace from XML tag, returning just the local name."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _parse_attributes(element: etree._Element) -> dict[str, Any]:
    """Parse XML attributes into a dictionary with snake_case keys."""
    attrs = {}
    for key, value in element.attrib.items():
        # Strip namespace from attribute names
        local_key = _strip_namespace(key)

        # Convert to snake_case for Pydantic
        # e.g., classCode -> class_code
        snake_key = _to_snake_case(local_key)

        # Convert boolean strings
        if value.lower() in ("true", "false"):
            attrs[snake_key] = value.lower() == "true"
        else:
            attrs[snake_key] = value

    return attrs


def _to_snake_case(name: str) -> str:
    """Convert camelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            # Add underscore before uppercase letter
            result.append("_")
            result.append(char.lower())
        else:
            result.append(char.lower() if char.isupper() else char)
    return "".join(result)


def _to_camel_case(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split('_')
    # First part stays lowercase, rest get capitalized
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


def _parse_typed_value(element: etree._Element) -> Any:
    """Parse an element with xsi:type attribute.

    This handles polymorphic values like:
    <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
    <value xsi:type="CD" code="123" codeSystem="..."/>
    """
    xsi_type = element.get(f"{{{NAMESPACES['xsi']}}}type")
    if not xsi_type:
        return None

    # Get the model class for this type
    model_class = XSI_TYPE_MAP.get(xsi_type)
    if not model_class:
        raise UnknownTypeError(xsi_type, _strip_namespace(element.tag))

    # Parse as that specific type
    return _parse_element(element, model_class)


def _parse_element(element: etree._Element, model_class: type[T]) -> T:
    """Parse an XML element into a Pydantic model instance.

    This is the core recursive parsing function that:
    1. Extracts XML attributes
    2. Processes child elements
    3. Handles text content
    4. Aggregates repeated elements into lists
    5. Returns a Pydantic model instance
    """
    data: dict[str, Any] = {}

    # 1. Parse attributes
    data.update(_parse_attributes(element))

    # 2. Track child elements by name for aggregation
    # Also preserve the original order of all children for tail text processing
    child_elements: dict[str, list[etree._Element]] = {}
    all_children: list[etree._Element] = []

    for child in element:
        # Skip comments and processing instructions
        # Comments and PIs have a 'tag' attribute that's a function, not a string
        if not isinstance(child.tag, str):
            continue

        tag = _strip_namespace(child.tag)
        # Handle SDTC namespace elements
        # lxml expands namespaces, so <sdtc:deceasedInd> becomes {urn:hl7-org:sdtc}deceasedInd
        if child.tag.startswith('{urn:hl7-org:sdtc}'):
            tag = "sdtc_" + tag

        if tag not in child_elements:
            child_elements[tag] = []
        child_elements[tag].append(child)
        all_children.append(child)

    # 3. Parse child elements
    # We need to know which fields are lists vs single values
    # Pydantic model fields tell us this
    model_fields = model_class.model_fields

    for tag, elements in child_elements.items():
        # Convert tag to snake_case to match Pydantic field names
        field_name = _to_snake_case(tag)

        # Check if this field exists in the model
        if field_name not in model_fields:
            # Skip unknown elements (extra="ignore" in CDAModel config)
            continue

        field_info = model_fields[field_name]
        field_type = field_info.annotation

        # Determine if this is a list field
        is_list = _is_list_field(field_type)

        if is_list:
            # Parse all elements into a list
            parsed_items = []
            for elem in elements:
                parsed = _parse_child_element(elem, field_name, model_class)
                if parsed is not None:
                    parsed_items.append(parsed)
            if parsed_items:
                data[field_name] = parsed_items
        else:
            # Take the first element only
            if elements:
                parsed = _parse_child_element(elements[0], field_name, model_class)
                if parsed is not None:
                    data[field_name] = parsed

    # 4. Handle text content
    # Only capture text before first child element (not tail text)
    if element.text and element.text.strip():
        data["_text"] = element.text.strip()

    # 5. Create model instance
    try:
        instance = model_class.model_validate(data)

        # 6. Populate tail_text for child elements (AFTER model creation)
        # This preserves mixed content order by capturing text after each element
        for field_name in model_fields:
            if not hasattr(instance, field_name):
                continue

            field_value = getattr(instance, field_name)
            if field_value is None:
                continue

            # Handle list fields (multiple child elements)
            if isinstance(field_value, list):
                field_tag = _to_camel_case(field_name)
                if field_tag in child_elements:
                    xml_children = child_elements[field_tag]
                    # Match parsed models with their XML elements by index
                    for parsed_item, xml_child in zip(field_value, xml_children, strict=False):
                        if hasattr(parsed_item, 'tail_text') and hasattr(xml_child, 'tail') and xml_child.tail:
                            if xml_child.tail.strip():
                                parsed_item.tail_text = xml_child.tail.strip()

            # Handle single-value fields
            elif hasattr(field_value, '__dict__'):
                field_tag = _to_camel_case(field_name)
                if field_tag in child_elements and child_elements[field_tag]:
                    xml_child = child_elements[field_tag][0]
                    if hasattr(field_value, 'tail_text') and hasattr(xml_child, 'tail') and xml_child.tail:
                        if xml_child.tail.strip():
                            field_value.tail_text = xml_child.tail.strip()

        return instance
    except Exception as e:
        raise MalformedXMLError(
            f"Failed to parse {model_class.__name__} from element {_strip_namespace(element.tag)}: {e}"
        ) from e


def _is_list_field(field_type: Any) -> bool:
    """Check if a field type is a list."""
    import typing

    # Direct list type: list[X]
    origin = getattr(field_type, "__origin__", None)
    if origin is list:
        return True

    # Python 3.10+ Union syntax: list[X] | None
    # UnionType instances don't have __origin__, so use isinstance()
    if isinstance(field_type, types.UnionType):
        for arg in field_type.__args__:
            if getattr(arg, "__origin__", None) is list:
                return True

    # Old-style Union: Union[list[X], None]
    if origin is typing.Union:
        args = getattr(field_type, "__args__", ())
        for arg in args:
            if getattr(arg, "__origin__", None) is list:
                return True

    return False


def _parse_child_element(
    element: etree._Element, field_name: str, parent_model_class: type[BaseModel]
) -> Any:
    """Parse a child element, determining its type from the parent model."""
    # Get the expected type from the parent model
    field_info = parent_model_class.model_fields[field_name]
    field_type = field_info.annotation

    # Unwrap Optional/Union types and list types
    target_type = _unwrap_field_type(field_type)

    # Resolve ForwardRef if necessary
    from typing import ForwardRef, get_type_hints
    if isinstance(target_type, ForwardRef):
        # Get type hints from parent model to resolve forward references
        # This handles cases where a model references another model defined later in the file
        try:
            type_hints = get_type_hints(parent_model_class)
            if field_name in type_hints:
                resolved_type = type_hints[field_name]
                # Unwrap the resolved type (it might be Optional[X] or X | None)
                target_type = _unwrap_field_type(resolved_type)
        except Exception:
            # If resolution fails, continue with the ForwardRef
            # It will be handled as an unknown type and skipped
            pass

    # Check for xsi:type on the element
    xsi_type = element.get(f"{{{NAMESPACES['xsi']}}}type")
    if xsi_type:
        # This element has explicit type - use polymorphic parsing
        return _parse_typed_value(element)

    # Handle special cases
    tag = _strip_namespace(element.tag)

    # Handle name parts (given, family, etc.) - these need to be ENXP objects
    if tag in ("given", "family", "prefix", "suffix", "delimiter"):
        text = element.text.strip() if element.text else None
        if not text:
            return None
        attrs = _parse_attributes(element)
        attrs["value"] = text
        return ENXP.model_validate(attrs)

    # Handle address parts (city, state, etc.) - these are simple strings
    if tag in ("streetAddressLine", "city", "state", "postalCode", "country", "county"):
        return element.text.strip() if element.text else None

    # Simple string elements (title, text, etc.)
    if target_type is str:
        return element.text.strip() if element.text else None

    # Simple boolean elements (sdtc:deceasedInd, etc.)
    if target_type is bool:
        value_attr = element.get("value")
        if value_attr:
            return value_attr.lower() == "true"
        return None

    # If target_type is BaseModel subclass, recursively parse
    if isinstance(target_type, type) and issubclass(target_type, BaseModel):
        return _parse_element(element, target_type)

    # If we have a Union of multiple types, we need to detect which one
    # This handles cases like: value: CD | CE | CS | ST | PQ | ...
    if _is_union_type(target_type):
        return _parse_union_element(element, target_type)

    # Fallback: try to parse as the target type if it's a BaseModel
    if isinstance(target_type, type) and issubclass(target_type, BaseModel):
        return _parse_element(element, target_type)

    # Unknown type - skip
    return None


def _unwrap_field_type(field_type: Any) -> Any:
    """Unwrap Optional, Union, and list types to get the core type."""
    import typing
    from typing import ForwardRef

    # Resolve ForwardRef if present
    # ForwardRef is a placeholder for a type that hasn't been defined yet
    # We can't easily resolve it here without the module context
    # So we'll just return it as-is and handle it elsewhere
    if isinstance(field_type, ForwardRef):
        return field_type

    origin = getattr(field_type, "__origin__", None)

    # Unwrap list[X]
    if origin is list:
        args = getattr(field_type, "__args__", ())
        if args:
            return _unwrap_field_type(args[0])

    # Python 3.10+ Union syntax: X | None
    # UnionType instances don't have __origin__, so use isinstance()
    if isinstance(field_type, types.UnionType):
        args = field_type.__args__
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _unwrap_field_type(non_none_args[0])
        # Multiple non-None types - return as is (it's a true Union)
        return field_type

    # Old-style Union: Union[X, None]
    if origin is typing.Union:
        args = getattr(field_type, "__args__", ())
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return _unwrap_field_type(non_none_args[0])
        # Multiple non-None types - return as is (it's a true Union)
        return field_type

    return field_type


def _is_union_type(field_type: Any) -> bool:
    """Check if a field type is a Union (not just Optional)."""
    import typing

    # Python 3.10+ Union syntax: A | B | None
    # UnionType instances don't have __origin__, so use isinstance()
    if isinstance(field_type, types.UnionType):
        # It's a Union if there are multiple non-None types
        non_none_args = [arg for arg in field_type.__args__ if arg is not type(None)]
        return len(non_none_args) > 1

    # Old-style Union: Union[A, B, None]
    origin = getattr(field_type, "__origin__", None)
    if origin is typing.Union:
        args = getattr(field_type, "__args__", ())
        # It's a Union if there are multiple non-None types
        non_none_args = [arg for arg in args if arg is not type(None)]
        return len(non_none_args) > 1

    return False


def _parse_union_element(element: etree._Element, union_type: Any) -> Any:
    """Parse an element that could be one of multiple types."""
    args = getattr(union_type, "__args__", ())
    non_none_args = [arg for arg in args if arg is not type(None)]

    # Try each possible type in order
    for possible_type in non_none_args:
        # Unwrap list if needed
        unwrapped = _unwrap_field_type(possible_type)

        # Handle simple string type
        if unwrapped is str:
            return element.text.strip() if element.text else None

        if isinstance(unwrapped, type) and issubclass(unwrapped, BaseModel):
            try:
                return _parse_element(element, unwrapped)
            except Exception:
                continue  # Try next type

    # Couldn't parse as any type
    return None


# Need to import types for UnionType (Python 3.10+)
import re
import types


def preprocess_ccda_namespaces(xml_string: str) -> str:
    """Add missing namespace declarations to C-CDA XML.

    Automatically adds xmlns:xsi and xmlns:sdtc namespace declarations
    to the root element when these prefixes are used but not declared
    in the document.

    This preprocessing step fixes malformed XML from some C-CDA example
    documents while maintaining 100% W3C XML Namespaces compliance.

    Works with both complete ClinicalDocument files and document fragments
    (sections, entries, etc.) for testing purposes.

    Args:
        xml_string: C-CDA XML document or fragment as string

    Returns:
        XML string with namespace declarations added if needed

    Raises:
        None - safe to call on any XML string

    Standards Compliance:
        - W3C XML Namespaces 1.0: https://www.w3.org/TR/xml-names/
        - HL7 CDA Core v2.0.1-sd: https://hl7.org/cda/stds/core/2.0.1-sd/
        - SDTC Extensions: https://confluence.hl7.org/display/SD/CDA+Extensions

    Examples:
        >>> xml = '<ClinicalDocument><value xsi:type="CD"/></ClinicalDocument>'
        >>> preprocessed = preprocess_ccda_namespaces(xml)
        >>> 'xmlns:xsi=' in preprocessed
        True
    """
    # Check if xsi: prefix is used but not declared
    needs_xsi = (
        'xsi:' in xml_string and
        'xmlns:xsi=' not in xml_string
    )

    # Check if sdtc: prefix is used but not declared
    needs_sdtc = (
        'sdtc:' in xml_string and
        'xmlns:sdtc=' not in xml_string
    )

    # If no missing namespaces, return unchanged
    if not needs_xsi and not needs_sdtc:
        return xml_string

    # Find the root element opening tag (any tag)
    # Look for first opening tag: <tagname ... > or <tagname>
    # Pattern matches: <tagname followed by space or >
    pattern = r'<([a-zA-Z][a-zA-Z0-9:._-]*)(\s|>)'

    def add_namespaces(match):
        """Add namespace declarations to opening tag."""
        tag_name = match.group(1)  # tag name (e.g., 'ClinicalDocument', 'section')
        suffix = match.group(2)     # ' ' or '>'

        # Build namespace declarations
        namespaces = []
        if needs_xsi:
            namespaces.append('xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"')
        if needs_sdtc:
            namespaces.append('xmlns:sdtc="urn:hl7-org:sdtc"')

        # Insert namespaces
        # If suffix is '>', add space before it
        # If suffix is ' ', namespaces will naturally space-separate
        if suffix == '>':
            return f"<{tag_name} {' '.join(namespaces)}>"
        else:
            return f"<{tag_name} {' '.join(namespaces)}{suffix}"

    # Replace first occurrence only (root element)
    xml_string = re.sub(pattern, add_namespaces, xml_string, count=1)

    return xml_string


def parse_ccda(xml_string: str | bytes) -> ClinicalDocument:
    """Parse C-CDA XML document into a ClinicalDocument model.

    Args:
        xml_string: C-CDA XML as string or bytes

    Returns:
        Parsed ClinicalDocument instance

    Raises:
        CDAParserError: If parsing fails
        UnknownTypeError: If an unknown xsi:type is encountered
        MalformedXMLError: If XML structure is invalid

    Example:
        >>> xml = Path("patient.xml").read_text()
        >>> doc = parse_ccda(xml)
        >>> doc.record_target[0].patient_role.patient.name[0].family
        'Jones'
    """
    try:
        # Preprocess: Add missing namespace declarations
        if isinstance(xml_string, str):
            xml_string = preprocess_ccda_namespaces(xml_string)
            xml_bytes = xml_string.encode("utf-8")
        else:
            # For bytes input, decode, preprocess, then encode
            xml_str = xml_string.decode("utf-8")
            xml_str = preprocess_ccda_namespaces(xml_str)
            xml_bytes = xml_str.encode("utf-8")

        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        raise MalformedXMLError(f"Invalid XML syntax: {e}") from e

    # Verify this is a ClinicalDocument
    tag = _strip_namespace(root.tag)
    if tag != "ClinicalDocument":
        # Allow parsing of document fragments for testing
        # We'll wrap them in a minimal ClinicalDocument structure
        # This is handled by the test fixtures' wrap_in_ccda_document helper
        raise MalformedXMLError(
            f"Root element must be 'ClinicalDocument', got '{tag}'. "
            f"Use test fixtures' wrap_in_ccda_document() for fragments."
        )

    # Parse the document
    return _parse_element(root, ClinicalDocument)


def parse_ccda_fragment(xml_string: str | bytes, model_class: type[T]) -> T:
    """Parse a C-CDA XML fragment into a specific model type.

    This is useful for testing or parsing subsections of documents.

    Args:
        xml_string: C-CDA XML fragment as string or bytes
        model_class: The Pydantic model class to parse into

    Returns:
        Parsed model instance

    Example:
        >>> from ccda_to_fhir.ccda.models import RecordTarget
        >>> xml = '<recordTarget>...</recordTarget>'
        >>> record_target = parse_ccda_fragment(xml, RecordTarget)
    """
    try:
        # Preprocess: Add missing namespace declarations
        if isinstance(xml_string, str):
            xml_string = preprocess_ccda_namespaces(xml_string)
            xml_bytes = xml_string.encode("utf-8")
        else:
            # For bytes input, decode, preprocess, then encode
            xml_str = xml_string.decode("utf-8")
            xml_str = preprocess_ccda_namespaces(xml_str)
            xml_bytes = xml_str.encode("utf-8")

        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        raise MalformedXMLError(f"Invalid XML syntax: {e}") from e

    return _parse_element(root, model_class)
