"""NoteActivityConverter: C-CDA Note Activity Act to FHIR DocumentReference resource."""

from __future__ import annotations

import hashlib

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import CD
from ccda_to_fhir.constants import (
    DOCUMENT_REFERENCE_STATUS_TO_FHIR,
    FHIRCodes,
    FHIRSystems,
)

from .base import BaseConverter


class NoteActivityConverter(BaseConverter[Act]):
    """Convert C-CDA Note Activity Act to FHIR DocumentReference resource.

    Note Activity (2.16.840.1.113883.10.20.22.4.202) represents embedded clinical
    notes within a C-CDA document. These are converted to DocumentReference resources
    to represent the metadata and content of each note.

    Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-NoteActivity.html
    """

    def convert(self, note_act: Act) -> FHIRResourceDict:
        """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

        Args:
            note_act: The C-CDA Note Activity Act element

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
        if note_act.id and len(note_act.id) > 0:
            note_id = self._generate_note_id(note_act.id[0])
            if note_id:
                doc_ref["id"] = note_id

        # Status (required) - map from statusCode
        status = self._extract_status(note_act)
        doc_ref["status"] = status

        # Type (required) - note type from code
        if note_act.code:
            doc_type = self._convert_type(note_act.code)
            if doc_type:
                doc_ref["type"] = doc_type

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
        doc_ref["subject"] = {"reference": f"{FHIRCodes.ResourceTypes.PATIENT}/patient-placeholder"}

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
        if note_act.text:
            content = self._create_content(note_act.text)
            if content:
                doc_ref["content"] = [content]
        else:
            # Content is required - provide empty attachment if no text
            doc_ref["content"] = [{"attachment": {}}]

        # Context - encounter and period
        context = self._create_context(note_act)
        if context:
            doc_ref["context"] = context

        # RelatesTo - from reference to externalDocument
        if note_act.reference:
            relates_to = self._convert_relates_to(note_act.reference)
            if relates_to:
                doc_ref["relatesTo"] = relates_to

        return doc_ref

    def _generate_note_id(self, identifier) -> str | None:
        """Generate a FHIR resource ID from the note identifier.

        Args:
            identifier: Note II identifier

        Returns:
            Generated ID string or None
        """
        if not identifier:
            return None

        # Use extension if present
        if identifier.extension:
            clean_ext = identifier.extension.replace(" ", "-").replace(".", "-").lower()
            return f"note-{clean_ext}"
        elif identifier.root:
            # Use hash of root if no extension
            hash_val = hashlib.sha256(identifier.root.encode()).hexdigest()[:16]
            return f"note-{hash_val}"

        return None

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
        """Generate practitioner ID from identifier.

        Args:
            identifier: Practitioner identifier

        Returns:
            Generated ID string
        """
        from ccda_to_fhir.constants import CodeSystemOIDs

        # Check for NPI
        if identifier.root == CodeSystemOIDs.NPI and identifier.extension:
            return f"npi-{identifier.extension}"

        # Use extension if present
        if identifier.extension:
            return identifier.extension.replace(" ", "-").replace(".", "-").lower()

        # Use last 16 chars of root
        if identifier.root:
            return identifier.root.replace(".", "")[-16:]

        return "practitioner-unknown"

    def _create_content(self, text) -> JSONObject | None:
        """Create content element with attachment from note text.

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
        if hasattr(text, "representation") and text.representation == "B64":
            # Already base64 encoded
            if hasattr(text, "value") and text.value:
                # Remove whitespace from base64 data
                attachment["data"] = text.value.replace("\n", "").replace(" ", "").strip()
        elif hasattr(text, "value") and text.value:
            # Plain text - need to base64 encode it
            import base64
            text_bytes = text.value.encode("utf-8")
            attachment["data"] = base64.b64encode(text_bytes).decode("ascii")

        # Always return content, even if no data (content is required in FHIR)
        return content

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

        Args:
            identifier: Encounter identifier

        Returns:
            Generated ID string
        """
        if identifier.extension:
            return identifier.extension.replace(" ", "-").replace(".", "-").lower()

        if identifier.root:
            # For UUIDs, use the UUID as-is
            if self._is_uuid(identifier.root):
                return identifier.root

            # For OIDs, use last 16 chars
            return identifier.root.replace(".", "")[-16:]

        return "encounter-unknown"

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
) -> FHIRResourceDict:
    """Convert a C-CDA Note Activity Act to a FHIR DocumentReference resource.

    Convenience function for converting a single note activity.

    Args:
        note_act: The C-CDA Note Activity Act
        code_system_mapper: Optional code system mapper

    Returns:
        FHIR DocumentReference resource
    """
    converter = NoteActivityConverter(code_system_mapper=code_system_mapper)
    return converter.convert(note_act)
