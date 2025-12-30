"""DocumentReference converter: C-CDA ClinicalDocument to FHIR DocumentReference resource."""

from __future__ import annotations

import base64
import hashlib

from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.ccda.models.datatypes import CE, II
from ccda_to_fhir.constants import FHIRCodes, FHIRSystems
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class DocumentReferenceConverter(BaseConverter[ClinicalDocument]):
    """Convert C-CDA ClinicalDocument to FHIR DocumentReference resource.

    A DocumentReference resource provides metadata about a document to make it
    discoverable and manageable. This converter extracts document-level metadata
    from the C-CDA clinical document header.

    Reference: http://hl7.org/fhir/R4/documentreference.html
    """

    def __init__(self, original_xml: str | bytes | None = None, **kwargs):
        """Initialize the converter.

        Args:
            original_xml: Optional original C-CDA XML for content.attachment.data
            **kwargs: Additional arguments passed to BaseConverter
        """
        super().__init__(**kwargs)
        self.original_xml = original_xml

    def convert(self, clinical_document: ClinicalDocument) -> FHIRResourceDict:
        """Convert a C-CDA ClinicalDocument to a FHIR DocumentReference resource.

        Args:
            clinical_document: The C-CDA ClinicalDocument element

        Returns:
            FHIR DocumentReference resource as a dictionary

        Raises:
            ConversionError: If conversion fails
        """
        if not clinical_document:
            raise ValueError("ClinicalDocument is required")

        document_ref: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.DOCUMENT_REFERENCE,
            "status": FHIRCodes.DocumentReferenceStatus.CURRENT,
        }

        # Generate ID from document identifier
        document_ref["id"] = self._generate_document_reference_id(
            clinical_document.id if clinical_document.id else None
        )

        # Master identifier (document's unique identifier)
        if clinical_document.id:
            master_identifier = self._convert_master_identifier(clinical_document.id)
            if master_identifier:
                document_ref["masterIdentifier"] = master_identifier

        # Additional identifiers (set_id for versioning)
        identifiers = self._convert_identifiers(clinical_document)
        if identifiers:
            document_ref["identifier"] = identifiers

        # Document status (preliminary, final, amended, etc.)
        # Inferred from authenticator presence per C-CDA semantics
        doc_status = self._infer_doc_status(clinical_document)
        if doc_status:
            document_ref["docStatus"] = doc_status

        # Type (document kind - LOINC code) - REQUIRED by US Core
        if clinical_document.code:
            doc_type = self._convert_type(clinical_document.code)
            if doc_type:
                document_ref["type"] = doc_type

        # US Core requires DocumentReference.type (1..1)
        # Use default if not set from clinical_document.code
        if "type" not in document_ref:
            document_ref["type"] = {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": "34133-9",
                    "display": "Summarization of Episode Note"
                }],
                "text": "Clinical Document"
            }

        # Category (high-level categorization)
        # We can derive this from the document type code
        if clinical_document.code:
            categories = self._derive_categories(clinical_document.code)
            if categories:
                document_ref["category"] = categories

        # Subject (patient reference)
        if clinical_document.record_target and len(clinical_document.record_target) > 0:
            subject_ref = self._create_subject_reference(clinical_document.record_target[0])
            if subject_ref:
                document_ref["subject"] = subject_ref

        # Date (when this reference was created - use document effectiveTime)
        if clinical_document.effective_time:
            date = self.convert_date(clinical_document.effective_time.value)
            if date:
                document_ref["date"] = date

        # Author references (document authors)
        if clinical_document.author:
            authors = self._convert_author_references(clinical_document.author)
            if authors:
                document_ref["author"] = authors

        # Authenticator (who validated the document)
        if clinical_document.legal_authenticator:
            authenticator = self._convert_authenticator_reference(
                clinical_document.legal_authenticator
            )
            if authenticator:
                document_ref["authenticator"] = authenticator

        # Custodian (organization maintaining the document)
        if clinical_document.custodian:
            custodian = self._convert_custodian_reference(clinical_document.custodian)
            if custodian:
                document_ref["custodian"] = custodian

        # Description (human-readable summary)
        if clinical_document.title:
            document_ref["description"] = clinical_document.title

        # Security label (confidentiality)
        if clinical_document.confidentiality_code:
            security_labels = self._convert_security_labels(clinical_document.confidentiality_code)
            if security_labels:
                document_ref["securityLabel"] = security_labels

        # Context (clinical context)
        context = self._create_context(clinical_document)
        if context:
            document_ref["context"] = context

        # RelatesTo (document relationships - replaces, appends, transforms)
        if clinical_document.related_document:
            relates_to = self._convert_related_documents(clinical_document.related_document)
            if relates_to:
                document_ref["relatesTo"] = relates_to

        # Content (required - at least one)
        content = self._create_content(clinical_document)
        document_ref["content"] = [content]

        return document_ref

    def _generate_document_reference_id(self, document_id: II) -> str:
        """Generate a FHIR resource ID from the document identifier.

        Args:
            document_id: Document II identifier

        Returns:
            Generated ID string (never None - generates UUID fallback if needed)
        """
        if not document_id:
            # No document ID - generate UUID fallback
            from ccda_to_fhir.id_generator import generate_id
            return generate_id()

        # Use document root and extension to create ID via cached UUID generator
        from ccda_to_fhir.id_generator import generate_id_from_identifiers
        root = document_id.root if hasattr(document_id, 'root') and document_id.root else None
        extension = document_id.extension if hasattr(document_id, 'extension') and document_id.extension else None

        return generate_id_from_identifiers("DocumentReference", root, extension)

    def _convert_master_identifier(self, document_id: II) -> JSONObject | None:
        """Convert document ID to masterIdentifier.

        Args:
            document_id: Document II identifier

        Returns:
            FHIR Identifier or None
        """
        if not document_id:
            return None

        return self.create_identifier(root=document_id.root, extension=document_id.extension)

    def _convert_identifiers(self, clinical_document: ClinicalDocument) -> list[JSONObject]:
        """Convert document identifiers (including set_id for versioning).

        Args:
            clinical_document: The ClinicalDocument

        Returns:
            List of FHIR Identifiers
        """
        identifiers = []

        # Add set_id as an identifier if present (for document versioning)
        if clinical_document.set_id:
            set_identifier = self.create_identifier(
                root=clinical_document.set_id.root,
                extension=clinical_document.set_id.extension,
            )
            if set_identifier:
                # Add a type to indicate this is a set identifier
                set_identifier["type"] = {
                    "coding": [
                        {
                            "system": FHIRSystems.V2_IDENTIFIER_TYPE,
                            "code": "VN",
                            "display": "Version Number",
                        }
                    ],
                    "text": "Document Set ID",
                }
                identifiers.append(set_identifier)

        return identifiers

    def _convert_type(self, code: CE) -> JSONObject | None:
        """Convert document type code to FHIR CodeableConcept.

        Args:
            code: Document type code (usually LOINC)

        Returns:
            FHIR CodeableConcept or None
        """
        if not code:
            return None

        return self.create_codeable_concept(
            code=code.code,
            code_system=code.code_system,
            display_name=code.display_name,
            original_text=self._extract_original_text(code),
        )

    def _derive_categories(self, code: CE) -> list[JSONObject]:
        """Derive document categories from document type code.

        Categories provide high-level classification for indexing/grouping.

        Args:
            code: Document type code

        Returns:
            List of FHIR CodeableConcepts for categories
        """
        if not code or not code.code:
            return []

        categories = []

        # Map common C-CDA LOINC document type codes to US Core DocumentReference categories
        # Reference: http://hl7.org/fhir/us/core/ValueSet/us-core-documentreference-category
        # US Core v9.0.0: Systems SHALL support these 10 Common Clinical Notes

        # Clinical notes category (US Core 10 Common Clinical Notes + common C-CDA types)
        clinical_note_codes = {
            # US Core 10 Common Clinical Notes (SHALL support)
            "11488-4",  # Consultation Note
            "18842-5",  # Discharge Summary
            "34117-2",  # History & Physical Note
            "28570-0",  # Procedures Note
            "11506-3",  # Progress Note
            "18748-4",  # Imaging Narrative
            "11502-2",  # Laboratory Report Narrative
            "11526-1",  # Pathology Report Narrative
            "11504-8",  # Surgical Operation Note
            "34111-5",  # Emergency Department Note
            # Additional common C-CDA document types
            "34133-9",  # Summarization of Episode Note
            # Encouraged by US Core
            "57133-1",  # Referral Note
            "34746-8",  # Nurse Note
        }

        if code.code in clinical_note_codes:
            categories.append(
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                            "code": "clinical-note",
                            "display": "Clinical Note",
                        }
                    ]
                }
            )

        return categories

    def _create_subject_reference(self, record_target) -> JSONObject:
        """Create reference to the patient (subject).

        Args:
            record_target: RecordTarget element

        Returns:
            FHIR Reference
        """
        # Patient reference (from recordTarget in document header)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create DocumentReference without patient reference."
            )
        return self.reference_registry.get_patient_reference()

    def _convert_author_references(self, authors: list) -> list[JSONObject]:
        """Convert document authors to FHIR references.

        Args:
            authors: List of Author elements

        Returns:
            List of FHIR References to Practitioner/Organization resources
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

            # Create reference to organization if present
            elif assigned_author.represented_organization:
                if assigned_author.represented_organization.id and len(
                    assigned_author.represented_organization.id
                ) > 0:
                    first_id = assigned_author.represented_organization.id[0]
                    org_id = self._generate_organization_id(first_id)
                    author_refs.append(
                        {"reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{org_id}"}
                    )

        return author_refs

    def _generate_practitioner_id(self, identifier: II) -> str:
        """Generate practitioner ID using cached UUID v4.

        Args:
            identifier: Practitioner identifier

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        root = identifier.root if identifier.root else None
        extension = identifier.extension if identifier.extension else None

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _generate_organization_id(self, identifier: II) -> str:
        """Generate organization ID using cached UUID v4.

        Args:
            identifier: Organization identifier

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        root = identifier.root if identifier.root else None
        extension = identifier.extension if identifier.extension else None

        return generate_id_from_identifiers("Organization", root, extension)

    def _convert_authenticator_reference(self, legal_authenticator) -> JSONObject | None:
        """Convert legal authenticator to FHIR reference.

        Args:
            legal_authenticator: LegalAuthenticator element

        Returns:
            FHIR Reference or None
        """
        if not legal_authenticator.assigned_entity:
            return None

        assigned_entity = legal_authenticator.assigned_entity

        # Generate practitioner reference
        if assigned_entity.id and len(assigned_entity.id) > 0:
            first_id = assigned_entity.id[0]
            prac_id = self._generate_practitioner_id(first_id)
            return {"reference": f"{FHIRCodes.ResourceTypes.PRACTITIONER}/{prac_id}"}

        return None

    def _convert_custodian_reference(self, custodian) -> JSONObject | None:
        """Convert custodian to organization reference.

        Args:
            custodian: Custodian element

        Returns:
            FHIR Reference or None
        """
        if not custodian.assigned_custodian:
            return None

        if not custodian.assigned_custodian.represented_custodian_organization:
            return None

        custodian_org = custodian.assigned_custodian.represented_custodian_organization

        # Generate organization reference
        if custodian_org.id and len(custodian_org.id) > 0:
            first_id = custodian_org.id[0]
            org_id = self._generate_organization_id(first_id)
            return {"reference": f"{FHIRCodes.ResourceTypes.ORGANIZATION}/{org_id}"}

        return None

    def _convert_security_labels(self, confidentiality_code: CE) -> list[JSONObject]:
        """Convert confidentiality code to security labels.

        Args:
            confidentiality_code: Confidentiality code

        Returns:
            List of FHIR CodeableConcepts
        """
        if not confidentiality_code or not confidentiality_code.code:
            return []

        security_label = self.create_codeable_concept(
            code=confidentiality_code.code,
            code_system=confidentiality_code.code_system,
            display_name=confidentiality_code.display_name,
        )

        if security_label:
            return [security_label]

        return []

    def _convert_related_documents(self, related_documents: list) -> list[JSONObject]:
        """Convert related documents to relatesTo elements.

        Args:
            related_documents: List of RelatedDocument elements

        Returns:
            List of FHIR relatesTo elements
        """
        relates_to_list = []

        for related_doc in related_documents:
            if not related_doc.type_code:
                continue

            # Map C-CDA type codes to FHIR codes
            # RPLC = replaces, APND = appends, XFRM = transforms
            type_code_map = {
                "RPLC": "replaces",
                "APND": "appends",
                "XFRM": "transforms",
            }

            code = type_code_map.get(related_doc.type_code.upper())
            if not code:
                continue

            relates_to: JSONObject = {"code": code}

            # Create target reference from parent document
            if related_doc.parent_document:
                parent_doc = related_doc.parent_document
                if parent_doc.id and len(parent_doc.id) > 0:
                    first_id = parent_doc.id[0]
                    # Generate DocumentReference ID from parent document identifier
                    parent_doc_id = self._generate_document_reference_id(first_id)
                    relates_to["target"] = {
                        "reference": f"{FHIRCodes.ResourceTypes.DOCUMENT_REFERENCE}/{parent_doc_id}"
                    }

            if "target" in relates_to:
                relates_to_list.append(relates_to)

        return relates_to_list

    def _create_event_code(self, class_code: str) -> JSONObject | None:
        """Create event code from service event classCode.

        Args:
            class_code: Service event class code (PCPR, ENC, etc.)

        Returns:
            FHIR CodeableConcept or None
        """
        if not class_code:
            return None

        # Map common event class codes to display names
        # Per https://terminology.hl7.org/6.0.2/CodeSystem-v3-ActClass.html
        display_map = {
            "PCPR": "care provision",
            "ENC": "encounter",
        }

        display = display_map.get(class_code.upper(), class_code)

        return {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
                    "code": class_code,
                    "display": display,
                }
            ]
        }

    def _create_context(self, clinical_document: ClinicalDocument) -> JSONObject | None:
        """Create document context (clinical context).

        Args:
            clinical_document: The ClinicalDocument

        Returns:
            FHIR context object or None
        """
        context: JSONObject = {}

        # Encounter reference (from componentOf/encompassingEncounter)
        if clinical_document.component_of:
            if clinical_document.component_of.encompassing_encounter:
                encounter = clinical_document.component_of.encompassing_encounter
                if encounter.id and len(encounter.id) > 0:
                    first_id = encounter.id[0]
                    encounter_id = self._generate_encounter_id(first_id)
                    context["encounter"] = [
                        {"reference": f"{FHIRCodes.ResourceTypes.ENCOUNTER}/{encounter_id}"}
                    ]

                # Period (encounter time)
                if encounter.effective_time:
                    period = self._convert_period(encounter.effective_time)
                    if period:
                        context["period"] = period

        # Service event period and event code (from documentationOf)
        if clinical_document.documentation_of:
            for doc_of in clinical_document.documentation_of:
                if doc_of.service_event:
                    # Period
                    if doc_of.service_event.effective_time:
                        period = self._convert_period(doc_of.service_event.effective_time)
                        if period:
                            # Use service event period if no encounter period
                            if "period" not in context:
                                context["period"] = period

                    # Event code (classCode)
                    if doc_of.service_event.class_code:
                        event_code = self._create_event_code(doc_of.service_event.class_code)
                        if event_code:
                            if "event" not in context:
                                context["event"] = []
                            context["event"].append(event_code)

        # Facility type (from encompassing encounter location)
        if clinical_document.component_of:
            if clinical_document.component_of.encompassing_encounter:
                encounter = clinical_document.component_of.encompassing_encounter
                if encounter.location:
                    if encounter.location.health_care_facility:
                        facility = encounter.location.health_care_facility
                        if facility.code:
                            facility_type = self.create_codeable_concept(
                                code=facility.code.code,
                                code_system=facility.code.code_system,
                                display_name=facility.code.display_name,
                            )
                            if facility_type:
                                context["facilityType"] = facility_type

        # Practice setting (type of service)
        if clinical_document.documentation_of:
            for doc_of in clinical_document.documentation_of:
                if doc_of.service_event and doc_of.service_event.code:
                    practice_setting = self.create_codeable_concept(
                        code=doc_of.service_event.code.code,
                        code_system=doc_of.service_event.code.code_system,
                        display_name=doc_of.service_event.code.display_name,
                    )
                    if practice_setting:
                        context["practiceSetting"] = practice_setting
                        break

        return context if context else None

    def _generate_encounter_id(self, identifier: II) -> str:
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

    def _convert_period(self, ivl_ts) -> JSONObject | None:
        """Convert IVL_TS to FHIR Period.

        Args:
            ivl_ts: Interval of timestamps

        Returns:
            FHIR Period or None
        """
        if not ivl_ts:
            return None

        period: JSONObject = {}

        if ivl_ts.low:
            start = self.convert_date(ivl_ts.low.value)
            if start:
                period["start"] = start

        if ivl_ts.high:
            end = self.convert_date(ivl_ts.high.value)
            if end:
                period["end"] = end

        return period if period else None

    def _create_content(self, clinical_document: ClinicalDocument) -> JSONObject:
        """Create content element with attachment.

        This is required - must have at least one content element.

        Args:
            clinical_document: The ClinicalDocument

        Returns:
            FHIR content object
        """
        content: JSONObject = {"attachment": {}}
        attachment = content["attachment"]

        # Content type
        attachment["contentType"] = "text/xml"

        # Language
        if clinical_document.language_code:
            attachment["language"] = clinical_document.language_code.code

        # Title (from code display or title)
        if clinical_document.code and clinical_document.code.display_name:
            attachment["title"] = clinical_document.code.display_name
        elif clinical_document.title:
            attachment["title"] = clinical_document.title

        # Data (base64 encoded original XML)
        if self.original_xml:
            if isinstance(self.original_xml, str):
                xml_bytes = self.original_xml.encode("utf-8")
            else:
                xml_bytes = self.original_xml

            attachment["data"] = base64.b64encode(xml_bytes).decode("ascii")

            # Hash (SHA-1 hash of the content for integrity verification)
            sha1_hash = hashlib.sha1(xml_bytes).digest()
            attachment["hash"] = base64.b64encode(sha1_hash).decode("ascii")

        # URL (if the document is stored elsewhere)
        # Could be populated if we have an external document repository

        # Size (in bytes)
        if self.original_xml:
            attachment["size"] = len(xml_bytes)

        # Creation date (document effectiveTime)
        if clinical_document.effective_time:
            creation_date = self.convert_date(clinical_document.effective_time.value)
            if creation_date:
                attachment["creation"] = creation_date

        # Format (C-CDA format coding)
        # Uses HL7 CodeSystem as authoritative source for C-CDA format codes
        content["format"] = {
            "system": "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes",
            "code": "urn:hl7-org:sdwg:ccda-structuredBody:2.1",
            "display": "For documents following C-CDA 2.1 constraints using a structured body.",
        }

        return content

    def _infer_doc_status(self, clinical_document: ClinicalDocument) -> str | None:
        """Infer document status from authenticator presence.

        Per C-CDA semantics:
        - legalAuthenticator present → document is finalized and legally authenticated
        - authenticator present (not legal) → document is authenticated but not finalized
        - Neither present → status unknown (omit field)

        Args:
            clinical_document: The C-CDA clinical document

        Returns:
            docStatus code ('final', 'preliminary') or None
        """
        # Check for legal authenticator (document is finalized)
        legal_auth = getattr(clinical_document, 'legal_authenticator', None)
        if legal_auth is not None:
            return "final"

        # Check for regular authenticator (document is authenticated but not finalized)
        authenticator = getattr(clinical_document, 'authenticator', None)
        if authenticator is not None:
            # authenticator can be a list or single element
            if isinstance(authenticator, list):
                if len(authenticator) > 0:
                    return "preliminary"
            else:
                return "preliminary"

        # No authentication → don't specify status
        return None

    def _extract_original_text(self, code: CE) -> str | None:
        """Extract original text from CE code element.

        Args:
            code: CE code element

        Returns:
            Original text string or None
        """
        if not code:
            return None

        if code.original_text:
            # ED type - extract text
            if hasattr(code.original_text, "text"):
                return code.original_text.text
            # String type
            elif isinstance(code.original_text, str):
                return code.original_text

        return None
