"""NoteActivityConverter: C-CDA Note Activity Act to FHIR DocumentReference resource."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import CD
from ccda_to_fhir.constants import (
    DOCUMENT_REFERENCE_STATUS_TO_FHIR,
    FHIRCodes,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class NoteActivityConverter(BaseConverter[Act]):
    """Convert C-CDA Note Activity Act to FHIR DocumentReference resource.

    Note Activity (2.16.840.1.113883.10.20.22.4.202) represents embedded clinical
    notes within a C-CDA document. These are converted to DocumentReference resources
    to represent the metadata and content of each note.

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-NoteActivity.html
    """

    def convert(self, note_act: Act, section=None) -> FHIRResourceDict:
        """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

        Args:
            note_act: The C-CDA Note Activity Act element
            section: Optional containing section (for text reference resolution)

        Returns:
            FHIR DocumentReference resource as a dictionary

        Raises:
            ValueError: If conversion fails due to missing required fields
        """
        if not note_act:
            raise ValueError("Note Activity Act is required")

        doc_ref: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.DOCUMENT_REFERENCE,
        }

        # Generate ID from note activity identifiers
        doc_ref["id"] = self._generate_note_id(
            note_act.id[0] if (note_act.id and len(note_act.id) > 0) else None
        )

        # Status (required) - map from statusCode
        status = self._extract_status(note_act)
        doc_ref["status"] = status

        # DocStatus - document completion status from statusCode
        doc_status = self._extract_doc_status(note_act)
        if doc_status:
            doc_ref["docStatus"] = doc_status

        # Type (required) - note type from code - REQUIRED by US Core
        if note_act.code:
            doc_type = self._convert_type(note_act.code)
            if doc_type:
                doc_ref["type"] = doc_type

        # US Core requires DocumentReference.type (1..1)
        # Use default if not set from note_act.code
        if "type" not in doc_ref:
            doc_ref["type"] = {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34133-9",
                    "display": "Summarization of Episode Note"
                }],
                "text": "Clinical Note"
            }

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

        # Subject (patient reference) - placeholder that will be resolved later
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create DocumentReference without patient reference."
            )
        doc_ref["subject"] = self.reference_registry.get_patient_reference()

        # Date - from author/time (first author's time)
        if note_act.author and len(note_act.author) > 0:
            first_author = note_act.author[0]
            if first_author.time:
                date = self.convert_date(first_author.time.value)
                if date:
                    doc_ref["date"] = date

        # Author references
        if note_act.author:
            authors = self._convert_author_references(note_act.author)
            if authors:
                doc_ref["author"] = authors

        # Content (required) - from text element
        # Note: Can have multiple content items (inline + reference)
        if note_act.text:
            content_list = self._create_content_list(note_act.text, section)
            if content_list:
                doc_ref["content"] = content_list
            else:
                # Content is required but text has no extractable data
                # Use data-absent-reason extension per FHIR R4 spec
                doc_ref["content"] = self._create_missing_content()
        else:
            # Content is required but no text element present
            # Use data-absent-reason extension per FHIR R4 spec
            doc_ref["content"] = self._create_missing_content()

        # Context - encounter and period
        context = self._create_context(note_act)
        if context:
            doc_ref["context"] = context

        # RelatesTo - from reference to externalDocument
        if note_act.reference:
            relates_to = self._convert_relates_to(note_act.reference)
            if relates_to:
                doc_ref["relatesTo"] = relates_to

        # Narrative (from entry text reference, per C-CDA on FHIR IG)
        narrative = self._generate_narrative(entry=note_act, section=section)
        if narrative:
            doc_ref["text"] = narrative

        return doc_ref

    def _generate_note_id(self, identifier) -> str:
        """Generate a FHIR resource ID from the note identifier.

        Args:
            identifier: Note II identifier

        Returns:
            Generated ID string (never None - generates UUID fallback if needed)
        """
        if not identifier:
            # No identifier - generate UUID fallback
            from ccda_to_fhir.id_generator import generate_id
            return generate_id()

        # Use ID generator with caching for consistency
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        root = identifier.root if hasattr(identifier, 'root') and identifier.root else None
        extension = identifier.extension if hasattr(identifier, 'extension') and identifier.extension else None

        return generate_id_from_identifiers("DocumentReference", root, extension)

    def _extract_status(self, note_act: Act) -> str:
        """Extract FHIR status from C-CDA note activity statusCode.

        Args:
            note_act: The Note Activity Act

        Returns:
            FHIR DocumentReference status code
        """
        if note_act.status_code and note_act.status_code.code:
            status_code = note_act.status_code.code.lower()
            if status_code in DOCUMENT_REFERENCE_STATUS_TO_FHIR:
                return DOCUMENT_REFERENCE_STATUS_TO_FHIR[status_code]

        # Default to current
        return FHIRCodes.DocumentReferenceStatus.CURRENT

    def _extract_doc_status(self, note_act: Act) -> str | None:
        """Extract FHIR docStatus from C-CDA note activity statusCode.

        Maps C-CDA status to FHIR document completion status:
        - completed → final
        - active → preliminary
        - Others → None (omit docStatus)

        Args:
            note_act: The Note Activity Act

        Returns:
            FHIR DocumentReference docStatus code or None
        """
        if note_act.status_code and note_act.status_code.code:
            status_code = note_act.status_code.code.lower()
            if status_code == "completed":
                return "final"
            elif status_code == "active":
                return "preliminary"

        return None

    def _convert_type(self, code: CD) -> JSONObject | None:
        """Convert note type code to FHIR CodeableConcept.

        Includes the primary code and all translation codes.

        Args:
            code: Note type code (usually LOINC)

        Returns:
            FHIR CodeableConcept or None
        """
        if not code:
            return None

        type_concept: JSONObject = {
            "coding": [],
        }

        # Add primary code
        if code.code:
            primary_coding = self._create_coding(
                code=code.code,
                system=code.code_system,
                display=code.display_name,
            )
            if primary_coding:
                type_concept["coding"].append(primary_coding)

        # Add translation codes
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                trans_coding = self._create_coding(
                    code=trans.code,
                    system=trans.code_system,
                    display=trans.display_name,
                )
                if trans_coding:
                    type_concept["coding"].append(trans_coding)

        # Add text from display name
        if code.display_name:
            type_concept["text"] = code.display_name

        return type_concept if type_concept["coding"] else None

    def _create_coding(self, code: str | None, system: str | None, display: str | None) -> JSONObject | None:
        """Create a FHIR Coding element.

        Args:
            code: Code value
            system: Code system OID or URI
            display: Display name

        Returns:
            FHIR Coding or None
        """
        if not code:
            return None

        coding: JSONObject = {"code": code}

        # Convert OID to URI if needed
        if system:
            system_uri = self.code_system_mapper.oid_to_uri(system)
            if system_uri:
                coding["system"] = system_uri

        if display:
            coding["display"] = display

        return coding

    def _convert_author_references(self, authors: list) -> list[JSONObject]:
        """Convert note authors to FHIR references.

        Args:
            authors: List of Author elements

        Returns:
            List of FHIR References to Practitioner resources
        """
        author_refs = []

        for author in authors:
            if not author.assigned_author:
                continue

            assigned_author = author.assigned_author

            # Create reference to practitioner if person present
            if assigned_author.assigned_person:
                # Generate practitioner ID from identifiers
                if assigned_author.id and len(assigned_author.id) > 0:
                    first_id = assigned_author.id[0]
                    prac_id = self._generate_practitioner_id(first_id)
                    author_refs.append(
                        {"reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{prac_id}"}
                    )

        return author_refs

    def _generate_practitioner_id(self, identifier) -> str:
        """Generate FHIR Practitioner ID using cached UUID v4 from C-CDA identifier.

        Args:
            identifier: Practitioner identifier (C-CDA II type)

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        root = identifier.root if identifier.root else None
        extension = identifier.extension if identifier.extension else None

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _create_content_list(self, text, section=None) -> list[JSONObject]:
        """Create list of content elements with attachments from note text.

        C-CDA Note Activity text can contain multiple representations:
        1. Inline content (base64 encoded or plain text)
        2. Reference to section narrative

        When both are present, create separate content items for each.

        Args:
            text: ED (Encapsulated Data) element containing note content
            section: Optional containing section (for reference resolution)

        Returns:
            List of FHIR content objects (may be empty)
        """
        if not text:
            return []

        content_list: list[JSONObject] = []

        # Check for inline content (base64 or plain text)
        inline_content = self._create_inline_content(text)
        if inline_content:
            content_list.append(inline_content)

        # Check for reference to section narrative
        if hasattr(text, "reference") and text.reference and section:
            reference_content = self._create_reference_content(text.reference, section)
            if reference_content:
                content_list.append(reference_content)

        return content_list

    def _create_missing_content(self) -> list[JSONObject]:
        """Create content element for missing attachment data with data-absent-reason.

        When a Note Activity has no text content, US Core DocumentReference requires
        at least one content element. Use data-absent-reason extension to indicate
        the attachment data is missing.

        Reference: http://hl7.org/fhir/R4/extension-data-absent-reason.html

        Returns:
            List with single content object containing data-absent-reason extension
        """
        return [
            {
                "attachment": {
                    "contentType": "text/plain",
                    "_data": {
                        "extension": [
                            self.create_data_absent_reason_extension(None, default_reason="unknown")
                        ]
                    },
                }
            }
        ]

    def _create_inline_content(self, text) -> JSONObject | None:
        """Create content element from inline text content.

        Args:
            text: ED (Encapsulated Data) element containing note content

        Returns:
            FHIR content object or None
        """
        if not text:
            return None

        content: JSONObject = {"attachment": {}}
        attachment = content["attachment"]

        # Content type from mediaType attribute
        if hasattr(text, "media_type") and text.media_type:
            attachment["contentType"] = text.media_type
        else:
            # Default to text/plain if not specified
            attachment["contentType"] = "text/plain"

        # Data - base64 encoded content
        # In C-CDA, text content can be:
        # 1. Direct text content
        # 2. Base64 encoded (representation="B64")
        # Note: ED model stores text in 'value' attribute
        has_data = False
        if hasattr(text, "representation") and text.representation == "B64":
            # Already base64 encoded
            if hasattr(text, "value") and text.value:
                # Remove whitespace from base64 data
                attachment["data"] = text.value.replace("\n", "").replace(" ", "").strip()
                has_data = True
        elif hasattr(text, "value") and text.value:
            # Plain text - need to base64 encode it
            import base64
            text_bytes = text.value.encode("utf-8")
            attachment["data"] = base64.b64encode(text_bytes).decode("ascii")
            has_data = True

        # Only return content if we have data
        return content if has_data else None

    def _create_reference_content(self, reference, section) -> JSONObject | None:
        """Create content element from reference to section narrative.

        Args:
            reference: Reference element with value attribute (e.g., value="#note-1")
            section: Section containing the narrative text

        Returns:
            FHIR content object or None
        """
        if not reference or not section:
            return None

        # Resolve the reference to get the actual text
        resolved_text = self._resolve_text_reference(reference, section)
        if not resolved_text:
            return None

        content: JSONObject = {"attachment": {}}
        attachment = content["attachment"]

        # Determine content type based on markup presence
        if "<" in resolved_text and ">" in resolved_text:
            attachment["contentType"] = "text/html"
        else:
            attachment["contentType"] = "text/plain"

        # Base64 encode the resolved text
        import base64
        text_bytes = resolved_text.encode("utf-8")
        attachment["data"] = base64.b64encode(text_bytes).decode("ascii")

        return content

    def _resolve_text_reference(self, reference, section) -> str | None:
        """Resolve a text reference to section narrative content.

        Args:
            reference: Reference element with value attribute (e.g., value="#note-1")
            section: Section containing the narrative text

        Returns:
            Resolved text content as string or None
        """
        if not reference or not section:
            return None

        # Get reference value
        ref_value = None
        if hasattr(reference, "value") and reference.value:
            ref_value = reference.value
        elif isinstance(reference, str):
            ref_value = reference

        if not ref_value:
            return None

        # Parse reference ID (remove # prefix if present)
        ref_id = ref_value.lstrip("#")

        # Access section text/narrative
        if not hasattr(section, "text") or not section.text:
            return None

        # Use utility to extract text by ID from StrucDocText narrative
        from ccda_to_fhir.utils.struc_doc_utils import extract_text_by_id

        return extract_text_by_id(section.text, ref_id)

    def _extract_narrative_by_id(self, narrative, target_id: str) -> str | None:
        """Extract text content from CDA narrative by ID.

        Args:
            narrative: StrucDocText narrative object
            target_id: ID to search for

        Returns:
            Text content as string or None
        """
        # Try to convert narrative to XML and search
        try:
            # If narrative has an XML representation, search it
            if hasattr(narrative, "__dict__"):
                # Search through narrative elements
                for attr_name, attr_value in vars(narrative).items():
                    if isinstance(attr_value, list):
                        for item in attr_value:
                            text = self._search_element_for_id(item, target_id)
                            if text:
                                return text
            return None
        except Exception:
            return None

    def _search_element_for_id(self, element, target_id: str) -> str | None:
        """Recursively search an element for matching ID.

        Args:
            element: Element to search
            target_id: ID to find

        Returns:
            Text content if found, None otherwise
        """
        if not hasattr(element, "__dict__"):
            return None

        # Check if this element has the target ID
        if hasattr(element, "ID") and target_id == element.ID:
            # Extract text content from this element
            return self._extract_text_from_element(element)

        # Recursively search child elements
        for attr_value in vars(element).values():
            if isinstance(attr_value, list):
                for item in attr_value:
                    text = self._search_element_for_id(item, target_id)
                    if text:
                        return text
            elif hasattr(attr_value, "__dict__"):
                text = self._search_element_for_id(attr_value, target_id)
                if text:
                    return text

        return None

    def _extract_text_from_element(self, element) -> str:
        """Extract all text content from an element.

        Args:
            element: Element to extract text from

        Returns:
            Concatenated text content
        """
        texts = []

        if hasattr(element, "content") and element.content:
            if isinstance(element.content, str):
                texts.append(element.content)
            elif isinstance(element.content, list):
                for item in element.content:
                    if isinstance(item, str):
                        texts.append(item)
                    elif hasattr(item, "__dict__"):
                        texts.append(self._extract_text_from_element(item))

        # Check for direct text content
        for attr_name in ["text", "value", "_value"]:
            if hasattr(element, attr_name):
                attr_value = getattr(element, attr_name)
                if isinstance(attr_value, str):
                    texts.append(attr_value)

        # Recursively extract from children
        for attr_value in vars(element).values():
            if isinstance(attr_value, list):
                for item in attr_value:
                    if hasattr(item, "__dict__") and not isinstance(item, str):
                        child_text = self._extract_text_from_element(item)
                        if child_text:
                            texts.append(child_text)

        return " ".join(texts).strip()

    def _create_context(self, note_act: Act) -> JSONObject | None:
        """Create document context from note activity.

        Args:
            note_act: The Note Activity Act

        Returns:
            FHIR context object or None
        """
        context: JSONObject = {}

        # Period from effectiveTime
        if note_act.effective_time:
            # Note Activity uses IVL_TS for effectiveTime
            # But it's often just a single timestamp, treat as start
            if hasattr(note_act.effective_time, "low") and note_act.effective_time.low:
                if note_act.effective_time.low.value:
                    start = self.convert_date(note_act.effective_time.low.value)
                    if start:
                        context["period"] = {"start": start}
            elif hasattr(note_act.effective_time, "value") and note_act.effective_time.value:
                # Single timestamp
                start = self.convert_date(note_act.effective_time.value)
                if start:
                    context["period"] = {"start": start}

        # Encounter reference from entryRelationship
        if note_act.entry_relationship:
            for entry_rel in note_act.entry_relationship:
                # Look for encounter in entryRelationship (typeCode="COMP")
                if hasattr(entry_rel, "encounter") and entry_rel.encounter:
                    encounter = entry_rel.encounter
                    if encounter.id and len(encounter.id) > 0:
                        first_id = encounter.id[0]
                        encounter_id = self._generate_encounter_id(first_id)
                        if "encounter" not in context:
                            context["encounter"] = []
                        context["encounter"].append(
                            {"reference": f"{FHIRCodes.ResourceTypes.ENCOUNTER}/{encounter_id}"}
                        )

        return context if context else None

    def _generate_encounter_id(self, identifier) -> str:
        """Generate encounter ID from identifier.

        Uses base class generate_resource_id for consistency with EncounterConverter.

        Args:
            identifier: Encounter identifier

        Returns:
            Generated ID string
        """
        return self.generate_resource_id(
            root=identifier.root,
            extension=identifier.extension,
            resource_type="encounter",
            fallback_context="",
        )

    def _convert_relates_to(self, references: list) -> list[JSONObject]:
        """Convert reference to externalDocument to relatesTo.

        Args:
            references: List of Reference elements

        Returns:
            List of FHIR relatesTo elements
        """
        relates_to = []

        for ref in references:
            if hasattr(ref, "external_document") and ref.external_document:
                ext_doc = ref.external_document
                if ext_doc.id and len(ext_doc.id) > 0:
                    first_id = ext_doc.id[0]
                    relates_to.append(
                        {
                            "code": "appends",  # This note appends to the referenced document
                            "target": {
                                "reference": f"DocumentReference/{first_id.root}"
                            },
                        }
                    )

        return relates_to


def convert_note_activity(
    note_act: Act,
    code_system_mapper=None,
    section=None,
    reference_registry=None,
) -> FHIRResourceDict:
    """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

    Convenience function for converting a single note activity.

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
