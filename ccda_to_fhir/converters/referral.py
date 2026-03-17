"""Referral converter: C-CDA referral entries to FHIR ServiceRequest with referral category.

Maps C-CDA referral-coded entries (Planned Act, Planned Encounter with referral codes)
to FHIR R4B ServiceRequest resources with category = "3457005" (Patient referral).

C-CDA source templates:
  Planned Act (V2): 2.16.840.1.113883.10.20.22.4.39  (with referral codes)
  Planned Encounter (V2): 2.16.840.1.113883.10.20.22.4.40  (with non-APT/ARQ moodCodes)

FHIR target:
  US Core ServiceRequest Profile:
    https://hl7.org/fhir/us/core/StructureDefinition-us-core-servicerequest.html

Referral identification:
  An entry is considered a referral when its code is a known SNOMED referral code
  (e.g., 3457005 "Patient referral") or when it appears in a section coded with
  LOINC 42349-1 (Reason for referral).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.reference import Reference

from ccda_to_fhir.ccda.models.act import Act as CCDAAct
from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, IVL_TS, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.constants import (
    REFERRAL_SNOMED_CODES,
    SERVICE_REQUEST_MOOD_TO_INTENT,
    SERVICE_REQUEST_PRIORITY_TO_FHIR,
    SERVICE_REQUEST_STATUS_TO_FHIR,
    FHIRCodes,
    TemplateIds,
)
from ccda_to_fhir.types import (
    FHIRResourceDict,
    JSONObject,
    ReasonResult,
)

from .author_references import format_organization_display
from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import Author
    from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
    from ccda_to_fhir.ccda.models.performer import Performer
    from ccda_to_fhir.ccda.models.section import Section


# Referral category coding per SNOMED CT, typed as a proper Pydantic model
REFERRAL_CATEGORY = CodeableConcept(
    coding=[
        Coding(
            system="http://snomed.info/sct",
            code="3457005",
            display="Patient referral",
        )
    ]
)

# MoodCodes valid for referral ServiceRequests.
# Note: ARQ overlaps with AppointmentConverter.APPOINTMENT_MOOD_CODES but is
# valid here for Planned Acts (not Encounters) that carry referral codes.
# Routing in DocumentConverter ensures ARQ Encounters go to AppointmentConverter.
REFERRAL_MOOD_CODES = {"INT", "RQO", "PRP", "ARQ", "PRMS"}


class ReferralConverter(BaseConverter[CCDAAct | CCDAEncounter]):
    """Convert C-CDA referral entries to FHIR ServiceRequest with referral category.

    Handles referral-coded Planned Acts and Planned Encounters (non-appointment
    moodCodes) by mapping them to US Core ServiceRequest resources with a
    referral category.

    Reference: docs/mapping/20-referral.md
    """

    def convert(
        self, ccda_model: CCDAAct | CCDAEncounter, section: Section | None = None
    ) -> FHIRResourceDict:
        """Convert a C-CDA referral entry to a FHIR ServiceRequest (referral).

        Args:
            ccda_model: The C-CDA Planned Act or Planned Encounter element
            section: The C-CDA Section containing this entry (for narrative)

        Returns:
            FHIR ServiceRequest resource with referral category

        Raises:
            ValueError: If the entry lacks required data or has invalid moodCode
        """
        entry = ccda_model

        # Validate moodCode
        if not entry.mood_code:
            raise ValueError("Referral entry must have a moodCode attribute")

        mood_code = entry.mood_code.upper()
        if mood_code not in REFERRAL_MOOD_CODES:
            if mood_code == "EVN":
                raise ValueError(
                    "moodCode=EVN indicates completed procedure; use Procedure converter instead"
                )
            raise ValueError(
                f"Invalid moodCode '{mood_code}' for referral ServiceRequest; "
                f"expected one of {REFERRAL_MOOD_CODES}"
            )

        # Validate reference_registry (required for patient subject)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create referral ServiceRequest without patient reference."
            )

        # Build FHIR ServiceRequest
        fhir_service_request: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.SERVICE_REQUEST,
        }

        # US Core profile
        fhir_service_request["meta"] = {
            "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-servicerequest"]
        }

        # Generate ID
        if entry.id and len(entry.id) > 0:
            first_id = entry.id[0]
            fhir_service_request["id"] = self._generate_referral_id(
                first_id.root, first_id.extension
            )

        # Identifiers
        if entry.id:
            fhir_service_request["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in entry.id
                if id_elem.root
            ]

        # Status (required 1..1)
        status = self._map_status(entry.status_code)
        fhir_service_request["status"] = status

        # Intent (required 1..1)
        intent = self._map_intent(mood_code)
        fhir_service_request["intent"] = intent

        # Category (MS) - always "Patient referral" for referral ServiceRequests
        fhir_service_request["category"] = [REFERRAL_CATEGORY.model_dump(exclude_none=True)]

        # Code (required 1..1 per US Core)
        if entry.code:
            code = self.convert_code_to_codeable_concept(entry.code)
            if code:
                fhir_service_request["code"] = code.model_dump(exclude_none=True)
        # US Core requires code — fall back to referral category code if entry has no code
        if "code" not in fhir_service_request:
            fhir_service_request["code"] = REFERRAL_CATEGORY.model_dump(exclude_none=True)

        # Subject (required 1..1) - patient reference
        fhir_service_request["subject"] = (
            self.reference_registry.get_patient_reference().model_dump(exclude_none=True)
        )

        # Encounter (MS)
        encounter_ref = self.reference_registry.get_encounter_reference()
        if encounter_ref:
            fhir_service_request["encounter"] = encounter_ref.model_dump(exclude_none=True)

        # Occurrence[x] (MS) - from effectiveTime
        if entry.effective_time:
            occurrence = self._convert_occurrence(entry.effective_time)
            if occurrence:
                if isinstance(occurrence, dict) and ("start" in occurrence or "end" in occurrence):
                    fhir_service_request["occurrencePeriod"] = occurrence
                else:
                    fhir_service_request["occurrenceDateTime"] = occurrence

        # AuthoredOn (MS) - from author/time
        if entry.author:
            authored_on = self._extract_authored_on(entry.author)
            if authored_on:
                fhir_service_request["authoredOn"] = authored_on

        # Requester (MS) - from author
        if entry.author:
            requester = self._extract_requester(entry.author)
            if requester:
                fhir_service_request["requester"] = requester.model_dump(exclude_none=True)

        # Performer - from performer (practitioners + organizations)
        if entry.performer:
            performers = self._extract_performer_and_org_references(entry.performer)
            if performers:
                fhir_service_request["performer"] = [
                    p.model_dump(exclude_none=True) for p in performers
                ]

        # PerformerType - from performer assignedEntity code
        if entry.performer:
            performer_type = self._extract_performer_type(entry.performer)
            if performer_type:
                fhir_service_request["performerType"] = performer_type.model_dump(exclude_none=True)

        # doNotPerform - from negationInd (only Acts have this)
        if isinstance(entry, CCDAAct) and entry.negation_ind:
            fhir_service_request["doNotPerform"] = True

        # Priority
        if entry.priority_code:
            priority = self._map_priority(entry.priority_code)
            if priority:
                fhir_service_request["priority"] = priority

        # Reason codes (MS) - from entryRelationship
        if entry.entry_relationship:
            reasons = self._extract_reasons(entry.entry_relationship)
            if reasons.codes:
                fhir_service_request["reasonCode"] = [c.model_dump(exclude_none=True) for c in reasons.codes]
            if reasons.references:
                fhir_service_request["reasonReference"] = [
                    r.model_dump(exclude_none=True) for r in reasons.references
                ]

        # Patient instruction - from entryRelationship with Instruction template
        if entry.entry_relationship:
            patient_instruction = self._extract_patient_instruction(entry.entry_relationship)
            if patient_instruction:
                fhir_service_request["patientInstruction"] = patient_instruction

        # Notes
        notes = self.extract_notes_from_element(entry, include_comments=False)
        if notes:
            fhir_service_request["note"] = notes

        # Narrative
        narrative = self._generate_narrative(entry=entry, section=section)
        if narrative:
            fhir_service_request["text"] = narrative.model_dump(exclude_none=True)

        return fhir_service_request

    def _generate_referral_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR ServiceRequest ID for a referral."""
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("ServiceRequest", root, extension)

    def _map_status(self, status_code: CS | None) -> str:
        """Map C-CDA status code to FHIR ServiceRequest status."""
        if status_code and status_code.null_flavor:
            null_flavor_upper = status_code.null_flavor.upper()
            if null_flavor_upper == "UNK":
                return FHIRCodes.ServiceRequestStatus.UNKNOWN
            return FHIRCodes.ServiceRequestStatus.ACTIVE

        return self.map_status_code(
            status_code,
            SERVICE_REQUEST_STATUS_TO_FHIR,
            FHIRCodes.ServiceRequestStatus.ACTIVE,
        )

    def _map_intent(self, mood_code: str) -> str:
        """Map C-CDA moodCode to FHIR ServiceRequest intent."""
        return SERVICE_REQUEST_MOOD_TO_INTENT.get(mood_code, FHIRCodes.ServiceRequestIntent.ORDER)

    def _map_priority(self, priority_code: CE | None) -> str | None:
        """Map C-CDA priorityCode to FHIR ServiceRequest priority."""
        if not priority_code or not priority_code.code:
            return None
        return SERVICE_REQUEST_PRIORITY_TO_FHIR.get(priority_code.code.upper())

    def _convert_occurrence(self, effective_time: IVL_TS | TS | str) -> JSONObject | str | None:
        """Convert C-CDA effectiveTime to FHIR occurrence[x]."""
        if isinstance(effective_time, str):
            return self.convert_date(effective_time)

        if isinstance(effective_time, IVL_TS):
            if effective_time.value:
                return self.convert_date(effective_time.value)

            period: JSONObject = {}
            if effective_time.low and effective_time.low.value:
                converted = self.convert_date(str(effective_time.low.value))
                if converted:
                    period["start"] = converted
            if effective_time.high and effective_time.high.value:
                converted = self.convert_date(str(effective_time.high.value))
                if converted:
                    period["end"] = converted
            return period if period else None

        if isinstance(effective_time, TS) and effective_time.value:
            return self.convert_date(effective_time.value)

        return None

    def _extract_authored_on(self, authors: list[Author]) -> str | None:
        """Extract authoredOn from the latest author timestamp.

        Uses max() (latest) because authoredOn represents the most recent
        authoring action, unlike Appointment.created which uses the earliest.
        """
        if not authors:
            return None

        authors_with_time = [a for a in authors if a.time and a.time.value]
        if not authors_with_time:
            return None

        latest = max(authors_with_time, key=lambda a: str(a.time.value))  # type: ignore[union-attr]
        time = latest.time
        assert time is not None and time.value is not None  # guaranteed by filter
        return self.convert_date(time.value)

    def _extract_requester(self, authors: list[Author]) -> Reference | None:
        """Extract requester reference from the latest author.

        Falls back to the first author if none have timestamps.
        When the author has a representedOrganization but no assignedPerson,
        creates an Organization reference instead.
        """
        from ccda_to_fhir.converters.author_references import (
            format_organization_display,
            format_person_display,
        )

        if not authors:
            return None

        authors_with_time = [a for a in authors if a.time and a.time.value]
        if authors_with_time:
            selected = max(authors_with_time, key=lambda a: str(a.time.value))  # type: ignore[union-attr]
        else:
            # Fall back to first author when no timestamps present
            selected = authors[0]

        if not selected.assigned_author:
            return None

        assigned_author = selected.assigned_author

        # Prefer Practitioner reference when assignedPerson is present
        if assigned_author.assigned_person and assigned_author.id:
            for id_elem in assigned_author.id:
                if id_elem.root:
                    pract_id = self._generate_practitioner_id(id_elem.root, id_elem.extension)
                    display = format_person_display(assigned_author.assigned_person)
                    return Reference(reference=f"urn:uuid:{pract_id}", display=display)

        # Fall back to Organization when no assignedPerson but representedOrganization exists
        if assigned_author.represented_organization:
            org = assigned_author.represented_organization
            display = format_organization_display(org)

            # Try org's own IDs first
            if org.id:
                for id_elem in org.id:
                    if id_elem.root:
                        org_id = self._generate_organization_id(id_elem.root, id_elem.extension)
                        return Reference(reference=f"urn:uuid:{org_id}", display=display)

            # Fall back to author's ID to generate org reference (org has no ID but author does)
            if assigned_author.id:
                for id_elem in assigned_author.id:
                    if id_elem.root:
                        org_id = self._generate_organization_id(id_elem.root, id_elem.extension)
                        return Reference(reference=f"urn:uuid:{org_id}", display=display)

            # Last resort: display-only reference (no resolvable ID)
            if display:
                return Reference(display=display)

        return None

    def _extract_performer_and_org_references(
        self,
        performers: list[Performer],
    ) -> list[Reference]:
        """Extract performer references including both Practitioner and Organization.

        For each performer, creates a Practitioner reference from assignedEntity.
        Additionally, if the performer's assignedEntity has a representedOrganization,
        adds an Organization reference.

        Args:
            performers: List of C-CDA Performer elements

        Returns:
            List of Reference objects (Practitioners and Organizations)
        """
        references = self.extract_performer_references(performers)

        for performer in performers:
            if not performer or not performer.assigned_entity:
                continue

            org = performer.assigned_entity.represented_organization
            if not org:
                continue

            display = format_organization_display(org)
            added = False

            if org.id:
                for id_elem in org.id:
                    if id_elem.root:
                        org_id = self._generate_organization_id(id_elem.root, id_elem.extension)
                        references.append(
                            Reference(reference=f"urn:uuid:{org_id}", display=display)
                        )
                        added = True
                        break

            if not added and display:
                references.append(Reference(display=display))

        return references

    def _extract_performer_type(self, performers: list[Performer]) -> CodeableConcept | None:
        """Extract performerType from C-CDA performer assignedEntity code.

        Args:
            performers: List of C-CDA performer elements

        Returns:
            CodeableConcept or None
        """
        for performer in performers:
            if performer.assigned_entity and performer.assigned_entity.code:
                return self.convert_code_to_codeable_concept(performer.assigned_entity.code)
        return None

    def _extract_patient_instruction(
        self,
        entry_relationships: list[EntryRelationship],
    ) -> str | None:
        """Extract patient instruction from entryRelationships.

        Looks for Instruction Act (2.16.840.1.113883.10.20.22.4.20) with
        typeCode="SUBJ" and inversionInd="true".

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            Patient instruction text or None
        """
        for entry_rel in entry_relationships:
            if (entry_rel.type_code == "SUBJ" and entry_rel.inversion_ind) and entry_rel.act:
                act = entry_rel.act

                is_instruction = False
                if act.template_id:
                    for template in act.template_id:
                        if template.root == TemplateIds.INSTRUCTION_ACT:
                            is_instruction = True
                            break

                if is_instruction and act.text:
                    if isinstance(act.text, str):
                        return act.text
                    elif act.text.value:
                        return act.text.value

        return None

    def _extract_reasons(self, entry_relationships: list[EntryRelationship]) -> ReasonResult:
        """Extract reason codes and references from entryRelationships."""
        return self.extract_reasons_from_entry_relationships(
            entry_relationships,
            problem_template_id=TemplateIds.PROBLEM_OBSERVATION,
        )


def is_referral_code(code: CD | None) -> bool:
    """Check if a C-CDA code represents a referral.

    Args:
        code: The C-CDA code element

    Returns:
        True if the code is a known referral SNOMED code
    """
    if not code or not code.code:
        return False

    # Check main code
    if code.code_system == "2.16.840.1.113883.6.96" and code.code in REFERRAL_SNOMED_CODES:
        return True

    # Check translations
    if code.translation:
        for trans in code.translation:
            if (
                trans.code_system == "2.16.840.1.113883.6.96"
                and trans.code in REFERRAL_SNOMED_CODES
            ):
                return True

    return False
