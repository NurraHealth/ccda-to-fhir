"""Composition converter: C-CDA ClinicalDocument to FHIR Composition resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.ccda.models.clinical_document import ClinicalDocument
from ccda_to_fhir.ccda.models.datatypes import II
from ccda_to_fhir.ccda.models.section import Section, StructuredBody
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from .references import ReferenceRegistry


class CompositionConverter(BaseConverter[ClinicalDocument]):
    """Convert C-CDA ClinicalDocument to FHIR Composition resource.

    A Composition defines the structure and narrative content necessary for a document.
    The Composition resource organizes sections and references to clinical resources.

    In FHIR, a document Bundle MUST have a Composition as the first entry, with all
    referenced resources included as subsequent entries.

    Reference: http://hl7.org/fhir/R4/composition.html
    """

    def __init__(
        self,
        section_resource_map: dict[str, list[FHIRResourceDict]] | None = None,
        reference_registry: ReferenceRegistry | None = None,
        **kwargs,
    ):
        """Initialize the converter.

        Args:
            section_resource_map: Mapping of section template IDs to extracted resources
            reference_registry: Reference registry for validating resource references
            **kwargs: Additional arguments passed to BaseConverter
        """
        super().__init__(**kwargs)
        self.section_resource_map = section_resource_map or {}
        self.reference_registry = reference_registry

    def convert(self, clinical_document: ClinicalDocument) -> FHIRResourceDict:
        """Convert a C-CDA ClinicalDocument to a FHIR Composition resource.

        Args:
            clinical_document: The C-CDA ClinicalDocument element

        Returns:
            FHIR Composition resource as a dictionary

        Raises:
            ValueError: If required fields are missing
        """
        if not clinical_document:
            raise ValueError("ClinicalDocument is required")

        composition: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.COMPOSITION,
        }

        # Generate ID from document identifier
        if clinical_document.id:
            comp_id = self._generate_composition_id(clinical_document.id)
            if comp_id:
                composition["id"] = comp_id

        # Identifier - version-independent identifier for the composition
        if clinical_document.id:
            identifier = self._convert_identifier(clinical_document.id)
            if identifier:
                composition["identifier"] = identifier

        # Status - REQUIRED (preliminary | final | amended | entered-in-error)
        # Default to "final" for completed documents
        # NOTE: C-CDA legalAuthenticator maps to Composition.attester (not status) per
        # C-CDA on FHIR spec. There is no official guidance for inferring status from
        # authentication state. Using "final" as default is the safest approach.
        # See: https://build.fhir.org/ig/HL7/ccda-on-fhir/
        composition["status"] = FHIRCodes.CompositionStatus.FINAL

        # Attesters from legalAuthenticator and authenticator
        attesters = []

        # Legal attester from legalAuthenticator (if present)
        if clinical_document.legal_authenticator:
            legal_attester = self._extract_legal_attester(clinical_document.legal_authenticator)
            if legal_attester:
                attesters.append(legal_attester)

        # Professional attesters from authenticator elements (if present)
        if clinical_document.authenticator:
            for authenticator in clinical_document.authenticator:
                professional_attester = self._extract_professional_attester(authenticator)
                if professional_attester:
                    attesters.append(professional_attester)

        # Add attesters to composition if any exist
        if attesters:
            composition["attester"] = attesters

        # Extensions array for C-CDA on FHIR participant extensions
        extensions = []

        # Data Enterer extension
        if clinical_document.data_enterer:
            data_enterer_ext = self._extract_data_enterer_extension(clinical_document.data_enterer)
            if data_enterer_ext:
                extensions.append(data_enterer_ext)

        # Informant extensions
        if clinical_document.informant:
            for informant in clinical_document.informant:
                informant_ext = self._extract_informant_extension(informant)
                if informant_ext:
                    extensions.append(informant_ext)

        # Information Recipient extensions
        if clinical_document.information_recipient:
            for recipient in clinical_document.information_recipient:
                recipient_ext = self._extract_information_recipient_extension(recipient)
                if recipient_ext:
                    extensions.append(recipient_ext)

        # Participant extensions
        if clinical_document.participant:
            for participant in clinical_document.participant:
                participant_ext = self._extract_participant_extension(participant)
                if participant_ext:
                    extensions.append(participant_ext)

        # Performer extensions (from documentationOf/serviceEvent)
        if clinical_document.documentation_of:
            for doc_of in clinical_document.documentation_of:
                if doc_of.service_event and doc_of.service_event.performer:
                    for performer in doc_of.service_event.performer:
                        performer_ext = self._extract_performer_extension(performer)
                        if performer_ext:
                            extensions.append(performer_ext)

        # Authorization extensions
        if clinical_document.authorization:
            for auth in clinical_document.authorization:
                auth_ext = self._extract_authorization_extension(auth)
                if auth_ext:
                    extensions.append(auth_ext)

        # Order extensions (inFulfillmentOf)
        if clinical_document.in_fulfillment_of:
            for fulfillment in clinical_document.in_fulfillment_of:
                order_ext = self._extract_order_extension(fulfillment)
                if order_ext:
                    extensions.append(order_ext)

        # Add all extensions to composition if any exist
        if extensions:
            composition["extension"] = extensions

        # Type - REQUIRED (document type code)
        if clinical_document.code:
            doc_type = self.create_codeable_concept(
                code=clinical_document.code.code,
                code_system=clinical_document.code.code_system,
                display_name=clinical_document.code.display_name,
            )
            if doc_type:
                composition["type"] = doc_type
        else:
            # Provide a default if no code is present (shouldn't happen in valid C-CDA)
            composition["type"] = {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "34133-9",
                        "display": "Summarization of Episode Note",
                    }
                ],
                "text": "Clinical Document",
            }

        # Subject - patient reference - OPTIONAL (0..1 per US Realm Header Profile)
        # Per US Realm Header Profile, Composition.subject has cardinality 0..1 (optional).
        # Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html
        #
        # While subject is optional per profile, most C-CDA documents include a recordTarget.
        # Always attempts to use first recordTarget when present. Clinical documents typically have
        # one recordTarget representing the patient. Multiple recordTargets are rare and not yet
        # supported in this implementation.
        if clinical_document.record_target and len(clinical_document.record_target) > 0:
            subject_ref = self._create_subject_reference(clinical_document.record_target[0])
            if subject_ref:
                composition["subject"] = subject_ref
            # If extraction fails, subject remains absent (allowed per 0..1 cardinality)
        # else: subject remains absent (allowed per 0..1 cardinality)

        # Date - REQUIRED (composition editing time)
        # Maps ClinicalDocument.effectiveTime per C-CDA on FHIR IG
        # Fallback: UTC current time when effectiveTime missing/invalid
        # Ensures FHIR validation succeeds while avoiding manufactured timezones
        date = None
        if clinical_document.effective_time:
            date = self.convert_date(clinical_document.effective_time.value)

        # Use fallback if effectiveTime missing or conversion failed
        if not date:
            import datetime
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "effectiveTime missing or invalid - using current UTC time as fallback for Composition.date"
            )
            # Use current time with timezone as fallback
            composition["date"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        else:
            composition["date"] = date

        # Author - REQUIRED (1..*)
        # Map document authors to Practitioner/Organization references
        if clinical_document.author:
            authors = self._convert_author_references(clinical_document.author)
            # FHIR requires at least one author
            if authors:
                composition["author"] = authors
            else:
                # Fallback if author extraction failed
                composition["author"] = [{"display": "Unknown Author"}]
        else:
            # FHIR requires at least one author - use a placeholder if none present
            composition["author"] = [{"display": "Unknown Author"}]

        # Title - REQUIRED
        if clinical_document.title:
            composition["title"] = clinical_document.title
        elif clinical_document.code and clinical_document.code.display_name:
            composition["title"] = clinical_document.code.display_name
        else:
            composition["title"] = "Clinical Document"

        # Confidentiality (optional)
        if clinical_document.confidentiality_code:
            confidentiality = self._convert_confidentiality(clinical_document.confidentiality_code)
            if confidentiality:
                composition["confidentiality"] = confidentiality

        # Custodian - REQUIRED (1..1 per US Realm Header Profile)
        # Organization maintaining the composition
        #
        # Note: US Realm Header documents (template 2.16.840.1.113883.10.20.22.1.1) are
        # validated at parse time and WILL FAIL if custodian is missing. Custodian conversion
        # should always succeed when custodian is present.
        if clinical_document.custodian:
            custodian_ref = self._create_custodian_reference(clinical_document.custodian)
            if custodian_ref:
                composition["custodian"] = custodian_ref
            else:
                # Custodian element present but couldn't extract reference - this is an error
                raise ValueError(
                    "Failed to create Composition.custodian reference. "
                    "US Realm Header Profile requires custodian with cardinality 1..1. "
                    "Custodian organization could not be extracted from C-CDA."
                )
        else:
            # No custodian - validation should have caught this for US Realm Header docs
            raise ValueError(
                "Cannot create Composition without custodian. "
                "US Realm Header Profile requires custodian with cardinality 1..1."
            )

        # Encounter - optional reference to the encompassing encounter
        # Maps from ClinicalDocument.componentOf.encompassingEncounter
        if self.reference_registry:
            encounter_ref = self.reference_registry.get_encounter_reference()
            if encounter_ref:
                composition["encounter"] = encounter_ref

        # Sections - convert structured body to Composition sections
        if clinical_document.component and clinical_document.component.structured_body:
            sections = self._convert_sections(clinical_document.component.structured_body)
            if sections:
                composition["section"] = sections

        return composition

    def _generate_composition_id(self, doc_id: II) -> str | None:
        """Generate a FHIR Composition ID from C-CDA document ID.

        Uses centralized id_generator to ensure consistency across document.

        Args:
            doc_id: C-CDA II element (document identifier)

        Returns:
            Generated UUID string or None (cached for consistency within document)
        """
        if not doc_id:
            return None

        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Composition", doc_id.root, doc_id.extension)

    def _convert_identifier(self, doc_id: II) -> JSONObject | None:
        """Convert document ID to Composition identifier.

        Args:
            doc_id: C-CDA II element

        Returns:
            FHIR Identifier or None
        """
        if not doc_id or not doc_id.root:
            return None

        identifier: JSONObject = {
            "system": f"urn:oid:{doc_id.root}",
        }

        if doc_id.extension:
            identifier["value"] = doc_id.extension

        return identifier

    def _create_subject_reference(self, record_target) -> JSONObject | None:
        """Create a reference to the patient (subject).

        Args:
            record_target: RecordTarget element from clinical document

        Returns:
            FHIR Reference or None if patient not available
        """
        if not record_target or not record_target.patient_role:
            return None

        # Patient reference (from recordTarget in document header)
        if self.reference_registry:
            try:
                return self.reference_registry.get_patient_reference()
            except Exception:
                # Patient not registered (conversion failed) - return None to trigger fail-fast
                return None
        else:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Composition without patient reference."
            )

    def _convert_author_references(self, authors: list) -> list[JSONObject]:
        """Convert C-CDA authors to FHIR Practitioner or Device references.

        Handles both human authors (assignedPerson) and device authors (assignedAuthoringDevice).

        Args:
            authors: List of Author elements

        Returns:
            List of FHIR References (never empty if authors list provided)
        """
        author_refs = []

        for author in authors:
            if not author.assigned_author:
                # If no assigned author, still add a generic entry
                author_refs.append({"display": "Unknown Author"})
                continue

            assigned_author = author.assigned_author

            # Create a display-only reference from the author
            # C-CDA requires either assignedPerson OR assignedAuthoringDevice
            if assigned_author.assigned_person and assigned_author.assigned_person.name:
                # Human author
                name = assigned_author.assigned_person.name[0]
                display = self._format_name_for_display(name)
                if display:
                    author_refs.append({"display": display})
                else:
                    # Name extraction failed
                    author_refs.append({"display": "Unknown Author"})
            elif assigned_author.assigned_authoring_device:
                # Device author
                device = assigned_author.assigned_authoring_device
                display = self._format_device_for_display(device)
                if display:
                    author_refs.append({"display": display})
                else:
                    # Device name extraction failed
                    author_refs.append({"display": "Unknown Device"})
            else:
                # No person or device available
                author_refs.append({"display": "Unknown Author"})

        return author_refs

    def _format_name_for_display(self, name) -> str | None:
        """Format a PN (person name) for display.

        Args:
            name: PN element

        Returns:
            Formatted name string or None
        """
        if not name:
            return None

        parts = []

        # Extract given names (handle ENXP objects)
        if name.given:
            for given in name.given:
                if isinstance(given, str):
                    parts.append(given)
                elif hasattr(given, "value") and given.value:
                    parts.append(given.value)

        # Extract family name (handle ENXP object)
        if name.family:
            if isinstance(name.family, str):
                parts.append(name.family)
            elif hasattr(name.family, "value") and name.family.value:
                parts.append(name.family.value)

        return " ".join(parts) if parts else None

    def _format_device_for_display(self, device) -> str | None:
        """Format a device for display in Composition.author.

        Creates display format: "Manufacturer (Software)" or just manufacturer/software if only one present.

        Args:
            device: AssignedAuthoringDevice element

        Returns:
            Formatted device string or None
        """
        if not device:
            return None

        manufacturer = device.manufacturer_model_name
        software = device.software_name

        if manufacturer and software:
            return f"{manufacturer} ({software})"
        elif manufacturer:
            return manufacturer
        elif software:
            return software
        else:
            return None

    def _extract_legal_attester(self, legal_authenticator) -> JSONObject | None:
        """Extract legal attester from legalAuthenticator.

        Maps C-CDA legal authentication to FHIR Composition.attester
        with mode="legal".

        Per C-CDA R2: legalAuthenticator represents a participant who has
        legally authenticated the document and accepts legal responsibility.

        Per US Realm Header Profile: legal_attester slice with mode fixed to "legal"
        and party referencing US Core Practitioner or PractitionerRole (1..1 cardinality).

        IMPORTANT: Per US Realm Header Profile, party is REQUIRED (1..1). This function
        returns None if party cannot be created, ensuring strict profile compliance.

        Args:
            legal_authenticator: C-CDA legalAuthenticator element

        Returns:
            FHIR attester object or None if party reference cannot be created

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html
        """
        if not legal_authenticator:
            return None

        # Try to create party reference first (REQUIRED per US Realm Header Profile)
        party_ref = None
        if legal_authenticator.assigned_entity:
            assigned = legal_authenticator.assigned_entity

            # Generate practitioner ID from identifiers
            if assigned.id:
                practitioner_id = self._generate_practitioner_id(assigned.id)
                if practitioner_id:
                    party_ref = {
                        "reference": f"Practitioner/{practitioner_id}"
                    }

        # If we can't create party, don't create attester (US Realm Header requires party 1..1)
        if not party_ref:
            return None

        attester: JSONObject = {
            "mode": "legal",  # Legal attestation
            "party": party_ref  # Required per US Realm Header Profile
        }

        # Extract time (optional)
        if legal_authenticator.time and legal_authenticator.time.value:
            time_str = self.convert_date(legal_authenticator.time.value)
            if time_str:
                attester["time"] = time_str

        return attester

    def _extract_professional_attester(self, authenticator) -> JSONObject | None:
        """Extract professional attester from authenticator.

        Maps C-CDA authenticator to FHIR Composition.attester with mode="professional".

        Per C-CDA R2: authenticator represents a participant who has attested to the
        accuracy of the document, but who does not have privileges to legally authenticate
        the document. Example: a resident physician who sees a patient and dictates a note,
        then later signs it.

        Per US Realm Header Profile: professional_attester slice with mode fixed to "professional"
        and party referencing US Core Practitioner or PractitionerRole (1..1 cardinality).

        IMPORTANT: Per US Realm Header Profile, party is REQUIRED (1..1). This function
        returns None if party cannot be created, ensuring strict profile compliance.

        Args:
            authenticator: C-CDA Authenticator element

        Returns:
            FHIR attester object or None if party reference cannot be created

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html
        Reference: https://build.fhir.org/ig/HL7/CDA-core-2.0/StructureDefinition-Authenticator.html
        """
        if not authenticator:
            return None

        # Try to create party reference first (REQUIRED per US Realm Header Profile)
        party_ref = None
        if authenticator.assigned_entity:
            assigned = authenticator.assigned_entity

            # Generate practitioner ID from identifiers
            if assigned.id:
                practitioner_id = self._generate_practitioner_id(assigned.id)
                if practitioner_id:
                    party_ref = {
                        "reference": f"Practitioner/{practitioner_id}"
                    }

        # If we can't create party, don't create attester (US Realm Header requires party 1..1)
        if not party_ref:
            return None

        attester: JSONObject = {
            "mode": "professional",  # Professional attestation
            "party": party_ref  # Required per US Realm Header Profile
        }

        # Extract time (optional)
        if authenticator.time and authenticator.time.value:
            time_str = self.convert_date(authenticator.time.value)
            if time_str:
                attester["time"] = time_str

        return attester

    def _extract_data_enterer_extension(self, data_enterer) -> JSONObject | None:
        """Extract Data Enterer extension from C-CDA dataEnterer.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension

        Per C-CDA on FHIR IG v2.0.0, this is a simple extension with valueReference only.
        Note: C-CDA dataEnterer/time is not captured in the extension per official spec.

        Args:
            data_enterer: C-CDA DataEnterer element

        Returns:
            FHIR extension object or None
        """
        if not data_enterer:
            return None

        # Create Practitioner reference from assignedEntity
        if data_enterer.assigned_entity and data_enterer.assigned_entity.id:
            practitioner_id = self._generate_practitioner_id(data_enterer.assigned_entity.id)
            if practitioner_id:
                # Simple extension with valueReference (per official C-CDA on FHIR IG)
                extension: JSONObject = {
                    "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension",
                    "valueReference": {
                        "reference": f"Practitioner/{practitioner_id}"
                    }
                }
                return extension

        return None

    def _extract_informant_extension(self, informant) -> JSONObject | None:
        """Extract Informant extension from C-CDA informant.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/InformantExtension

        Informant can be either:
        - assignedEntity (healthcare provider) -> Practitioner/PractitionerRole
        - relatedEntity (family member, etc.) -> RelatedPerson or Patient

        Args:
            informant: C-CDA Informant element

        Returns:
            FHIR extension object or None
        """
        if not informant:
            return None

        extension: JSONObject = {
            "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/InformantExtension"
        }

        # Check for assignedEntity (healthcare provider)
        if informant.assigned_entity and informant.assigned_entity.id:
            practitioner_id = self._generate_practitioner_id(informant.assigned_entity.id)
            if practitioner_id:
                extension["valueReference"] = {
                    "reference": f"Practitioner/{practitioner_id}"
                }
                return extension

        # Check for relatedEntity (family member, caregiver, etc.)
        if informant.related_entity:
            # For now, create a display-only reference since we don't convert RelatedPerson resources yet
            display = self._format_related_entity_display(informant.related_entity)
            if display:
                extension["valueReference"] = {
                    "display": display
                }
                return extension

        return None

    def _extract_information_recipient_extension(self, recipient) -> JSONObject | None:
        """Extract InformationRecipient extension from C-CDA informationRecipient.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/InformationRecipientExtension

        Args:
            recipient: C-CDA InformationRecipient element

        Returns:
            FHIR extension object or None
        """
        if not recipient or not recipient.intended_recipient:
            return None

        extension: JSONObject = {
            "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/InformationRecipientExtension"
        }

        intended = recipient.intended_recipient

        # Check for information recipient person
        if intended.information_recipient and intended.information_recipient.name and len(intended.information_recipient.name) > 0:
            # Create display-only reference
            name = intended.information_recipient.name[0]
            display = self._format_name_for_display(name)
            if display:
                extension["valueReference"] = {
                    "display": display
                }
                return extension

        # Fallback to ID-based reference if available
        if intended.id:
            practitioner_id = self._generate_practitioner_id(intended.id)
            if practitioner_id:
                extension["valueReference"] = {
                    "reference": f"Practitioner/{practitioner_id}"
                }
                return extension

        return None

    def _extract_participant_extension(self, participant) -> JSONObject | None:
        """Extract Participant extension from C-CDA participant.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/ParticipantExtension

        Represents supporting entities like parents, relatives, caregivers, etc.

        Args:
            participant: C-CDA DocumentParticipant element

        Returns:
            FHIR extension object or None
        """
        if not participant or not participant.associated_entity:
            return None

        extension: JSONObject = {
            "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/ParticipantExtension"
        }

        associated = participant.associated_entity

        # Check for associated person
        if associated.associated_person and associated.associated_person.name and len(associated.associated_person.name) > 0:
            # Create display-only reference for now
            name = associated.associated_person.name[0]
            display = self._format_name_for_display(name)
            if display:
                extension["valueReference"] = {
                    "display": display
                }
                return extension

        # Fallback to ID-based reference if available
        if associated.id:
            practitioner_id = self._generate_practitioner_id(associated.id)
            if practitioner_id:
                extension["valueReference"] = {
                    "reference": f"Practitioner/{practitioner_id}"
                }
                return extension

        return None

    def _extract_performer_extension(self, performer) -> JSONObject | None:
        """Extract Performer extension from C-CDA documentationOf/serviceEvent/performer.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/PerformerExtension

        Represents clinicians who actually carried out clinical services.

        Args:
            performer: C-CDA ServiceEventPerformer element

        Returns:
            FHIR extension object or None
        """
        if not performer or not performer.assigned_entity:
            return None

        if not performer.assigned_entity.id:
            return None

        practitioner_id = self._generate_practitioner_id(performer.assigned_entity.id)
        if practitioner_id:
            extension: JSONObject = {
                "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/PerformerExtension",
                "valueReference": {
                    "reference": f"Practitioner/{practitioner_id}"
                }
            }
            return extension

        return None

    def _extract_authorization_extension(self, authorization) -> JSONObject | None:
        """Extract Authorization extension from C-CDA authorization.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/AuthorizationExtension

        Contains consent information as a reference to a Consent resource.

        Args:
            authorization: C-CDA Authorization element

        Returns:
            FHIR extension object or None
        """
        if not authorization or not authorization.consent:
            return None

        consent = authorization.consent

        # Generate Consent resource ID from consent identifier
        if consent.id:
            from ccda_to_fhir.id_generator import generate_id_from_identifiers

            root = consent.id[0].root if consent.id[0].root else None
            extension_val = consent.id[0].extension if consent.id[0].extension else None
            consent_id = generate_id_from_identifiers("Consent", root, extension_val)

            extension: JSONObject = {
                "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/AuthorizationExtension",
                "valueReference": {
                    "reference": f"Consent/{consent_id}"
                }
            }
            return extension

        return None

    def _extract_order_extension(self, in_fulfillment_of) -> JSONObject | None:
        """Extract Order extension from C-CDA inFulfillmentOf.

        Maps to: http://hl7.org/fhir/us/ccda/StructureDefinition/OrderExtension

        Represents orders that are fulfilled by this document.

        Args:
            in_fulfillment_of: C-CDA InFulfillmentOf element

        Returns:
            FHIR extension object or None
        """
        if not in_fulfillment_of or not in_fulfillment_of.order:
            return None

        order = in_fulfillment_of.order

        # Generate ServiceRequest resource ID from order identifier
        if order.id:
            from ccda_to_fhir.id_generator import generate_id_from_identifiers

            root = order.id[0].root if order.id[0].root else None
            extension_val = order.id[0].extension if order.id[0].extension else None
            service_request_id = generate_id_from_identifiers("ServiceRequest", root, extension_val)

            extension: JSONObject = {
                "url": "http://hl7.org/fhir/us/ccda/StructureDefinition/OrderExtension",
                "valueReference": {
                    "reference": f"ServiceRequest/{service_request_id}"
                }
            }
            return extension

        return None

    def _format_related_entity_display(self, related_entity) -> str | None:
        """Format a RelatedEntity for display.

        Args:
            related_entity: C-CDA RelatedEntity element

        Returns:
            Formatted display string or None
        """
        if not related_entity:
            return None

        # Try to get name from related person
        if related_entity.related_person and related_entity.related_person.name and len(related_entity.related_person.name) > 0:
            name = related_entity.related_person.name[0]
            display = self._format_name_for_display(name)
            if display:
                # Add relationship if available
                if related_entity.code and related_entity.code.display_name:
                    return f"{display} ({related_entity.code.display_name})"
                return display

        # Fallback to relationship code only
        if related_entity.code and related_entity.code.display_name:
            return related_entity.code.display_name

        return None

    def _generate_practitioner_id(self, identifiers: list[II]) -> str:
        """Generate FHIR Practitioner ID using cached UUID v4.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated UUID v4 string (cached for consistency)
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use first identifier for cache key
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("Practitioner", root, extension)

    def _convert_confidentiality(self, conf_code) -> str | None:
        """Convert confidentiality code to FHIR value.

        Args:
            conf_code: CE element with confidentiality code

        Returns:
            FHIR confidentiality code or None
        """
        if not conf_code or not conf_code.code:
            return None

        # C-CDA uses HL7 V3 Confidentiality codes (N, R, V, etc.)
        # These map directly to FHIR confidentiality codes
        return conf_code.code

    def _create_custodian_reference(self, custodian) -> JSONObject | None:
        """Create a reference to the custodian organization.

        Args:
            custodian: Custodian element from clinical document

        Returns:
            FHIR Reference or None
        """
        if not custodian or not custodian.assigned_custodian:
            return None

        if not custodian.assigned_custodian.represented_custodian_organization:
            return None

        custodian_org = custodian.assigned_custodian.represented_custodian_organization

        # Extract display name from ON object
        if custodian_org.name:
            # Handle ON (organization name) object
            if isinstance(custodian_org.name, str):
                return {"display": custodian_org.name}
            elif hasattr(custodian_org.name, "value") and custodian_org.name.value:
                return {"display": custodian_org.name.value}

        return None

    def _convert_sections(self, structured_body: StructuredBody) -> list[JSONObject]:
        """Convert C-CDA structured body to FHIR Composition sections.

        Args:
            structured_body: StructuredBody element

        Returns:
            List of FHIR section objects
        """
        sections = []

        if not structured_body.component:
            return sections

        for comp in structured_body.component:
            if not comp.section:
                continue

            section_dict = self._convert_section(comp.section)
            if section_dict:
                sections.append(section_dict)

        return sections

    def _convert_section(self, section: Section) -> JSONObject | None:
        """Convert a single C-CDA section to a FHIR Composition section.

        Args:
            section: C-CDA Section element

        Returns:
            FHIR section object or None
        """
        if not section:
            return None

        section_dict: JSONObject = {}

        # Title (optional but recommended)
        if section.title:
            section_dict["title"] = section.title

        # Code (recommended) - identifies the section type
        if section.code:
            code = self.create_codeable_concept(
                code=section.code.code,
                code_system=section.code.code_system,
                display_name=section.code.display_name,
            )
            if code:
                section_dict["code"] = code

        # Text (narrative content)
        # C-CDA sections have narrative in section.text (StrucDocText, ED type, or string)
        text_content = None
        if section.text:
            # Import StrucDocText type for checking
            from ccda_to_fhir.ccda.models.struc_doc import StrucDocText

            if isinstance(section.text, StrucDocText):
                # StrucDocText: convert structured narrative to HTML
                from ccda_to_fhir.utils.struc_doc_utils import narrative_to_html
                html_content = narrative_to_html(section.text)
                if html_content:
                    # Wrap in XHTML div with namespace
                    text_content = f'<div xmlns="http://www.w3.org/1999/xhtml">{html_content}</div>'
            elif isinstance(section.text, str):
                # Plain string
                text_content = section.text
            elif hasattr(section.text, "text") and section.text.text:
                # StrucDocText with only plain text (no structured elements)
                text_content = section.text.text
            elif hasattr(section.text, "value") and section.text.value:
                # ED type with value field
                text_content = section.text.value

        if text_content:
            narrative = self._convert_section_text(text_content)
            if narrative:
                section_dict["text"] = narrative

        # Entry - references to resources that support the section
        # We need to look up which resources belong to this section
        entries = self._get_section_entries(section)
        if entries:
            section_dict["entry"] = entries

        # Nested sections (subsections)
        if section.component:
            subsections = []
            for nested_comp in section.component:
                if nested_comp.section:
                    subsection = self._convert_section(nested_comp.section)
                    if subsection:
                        subsections.append(subsection)
            if subsections:
                section_dict["section"] = subsections

        # FHIR constraint: section must have text, entries, or subsections
        if not any(key in section_dict for key in ["text", "entry", "section"]):
            # If section is empty, add emptyReason based on nullFlavor if present
            # Per C-CDA spec, sections can have nullFlavor to indicate why they're empty
            # (e.g., Notes Section with nullFlavor instead of Note Activity entries)
            empty_reason_code = self._map_null_flavor_to_empty_reason(section.null_flavor)
            section_dict["emptyReason"] = {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/list-empty-reason",
                        "code": empty_reason_code,
                        "display": self._get_empty_reason_display(empty_reason_code),
                    }
                ]
            }

        return section_dict

    def _convert_section_text(self, text_content: str | None) -> JSONObject | None:
        """Convert section narrative text to FHIR Narrative.

        Args:
            text_content: XHTML content from section.text

        Returns:
            FHIR Narrative object or None
        """
        if not text_content:
            return None

        # FHIR Narrative has status and div
        # C-CDA text is already XHTML, but we need to ensure it's in a div
        # For now, we'll use "generated" status and wrap content in div if needed

        # Clean up the text content
        content = text_content.strip()
        if not content:
            return None

        # If content doesn't start with a tag, wrap it in a div
        if not content.startswith("<"):
            content = f"<div>{content}</div>"
        # If it's a table or list without a wrapper, wrap it
        elif content.startswith(("<table", "<list", "<paragraph")):
            content = f"<div>{content}</div>"
        # If it starts with <text>, extract the inner content
        elif content.startswith("<text"):
            # Strip the <text> wrapper
            import re
            match = re.search(r"<text[^>]*>(.*)</text>", content, re.DOTALL)
            if match:
                inner = match.group(1).strip()
                content = f"<div>{inner}</div>" if not inner.startswith("<div") else inner

        return {
            "status": "generated",
            "div": content,
        }

    def _get_section_entries(self, section: Section) -> list[JSONObject]:
        """Get resource references for a section based on the section→resource mapping.

        Args:
            section: C-CDA Section element

        Returns:
            List of FHIR References to resources in this section
        """
        entries = []
        seen_references = set()  # Track references to avoid duplicates

        if not section.template_id:
            return entries

        # Check each template ID to find matching resources
        for template in section.template_id:
            template_id = template.root
            if template_id in self.section_resource_map:
                resources = self.section_resource_map[template_id]
                for resource in resources:
                    if resource.get("resourceType") and resource.get("id"):
                        resource_type = resource["resourceType"]
                        resource_id = resource["id"]
                        reference = f"{resource_type}/{resource_id}"

                        # Only add if not already added (deduplicate)
                        if reference not in seen_references:
                            seen_references.add(reference)
                            entries.append({"reference": reference})

        return entries

    def _map_null_flavor_to_empty_reason(self, null_flavor: str | None) -> str:
        """Map C-CDA nullFlavor to FHIR emptyReason code.

        When a C-CDA section has a nullFlavor attribute instead of entries,
        this indicates why the section is empty. We map this to the appropriate
        FHIR emptyReason code from the list-empty-reason code system.

        Reference: http://terminology.hl7.org/CodeSystem/list-empty-reason

        Args:
            null_flavor: C-CDA nullFlavor code (e.g., "NASK", "UNK", "NAV")

        Returns:
            FHIR emptyReason code (defaults to "unavailable" if unmapped)
        """
        from ccda_to_fhir.constants import NULL_FLAVOR_TO_EMPTY_REASON

        if not null_flavor:
            # No nullFlavor specified, use default
            return "unavailable"

        # Look up the mapping (case-insensitive)
        null_flavor_upper = null_flavor.upper()
        return NULL_FLAVOR_TO_EMPTY_REASON.get(null_flavor_upper, "unavailable")

    def _get_empty_reason_display(self, code: str) -> str:
        """Get display text for FHIR emptyReason code.

        Args:
            code: FHIR emptyReason code

        Returns:
            Display text for the code
        """
        display_map = {
            "nilknown": "Nil Known",
            "notasked": "Not Asked",
            "withheld": "Information Withheld",
            "unavailable": "Unavailable",
            "notstarted": "Not Started",
            "closed": "Closed",
        }
        return display_map.get(code, "Unavailable")
