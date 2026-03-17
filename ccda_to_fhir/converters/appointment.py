"""Appointment converter: C-CDA Planned Encounter to FHIR Appointment resource.

Maps C-CDA Planned Encounter (V2) template entries with appointment-related
moodCodes (APT, ARQ) to FHIR R4B Appointment resources.

C-CDA source template:
  Planned Encounter (V2): 2.16.840.1.113883.10.20.22.4.40

FHIR target:
  Appointment: https://hl7.org/fhir/R4B/appointment.html

Per HL7 C-CDA R2.1, Planned Encounter entries use the Encounter class
(classCode=ENC) with future-oriented moodCodes:
  - APT: Appointment (confirmed booking)
  - ARQ: Appointment request (proposed/pending)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.ccda.models.datatypes import CE, CS, IVL_TS, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.constants import (
    APPOINTMENT_MOOD_TO_STATUS,
    APPOINTMENT_STATUS_TO_FHIR,
    FHIRCodes,
    TemplateIds,
)
from ccda_to_fhir.types import (
    FHIRReference,
    FHIRResourceDict,
    JSONObject,
    ReasonResult,
)

from .author_references import format_organization_display
from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.author import Author
    from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
    from ccda_to_fhir.ccda.models.participant import ParticipantRole
    from ccda_to_fhir.ccda.models.section import Section


class AppointmentConverter(BaseConverter[CCDAEncounter]):
    """Convert C-CDA Planned Encounter to FHIR Appointment resource.

    Handles Planned Encounter (V2) entries with moodCode APT or ARQ.
    These represent booked or requested appointments respectively.

    Reference: docs/mapping/19-appointment.md
    """

    # moodCodes that indicate an appointment (vs a planned encounter → ServiceRequest)
    APPOINTMENT_MOOD_CODES = {"APT", "ARQ"}

    def convert(
        self, ccda_model: CCDAEncounter, section: Section | None = None
    ) -> FHIRResourceDict:
        """Convert a C-CDA Planned Encounter to a FHIR Appointment resource.

        Args:
            ccda_model: The C-CDA Planned Encounter element
            section: The C-CDA Section containing this encounter (for narrative)

        Returns:
            FHIR Appointment resource as a dictionary

        Raises:
            ValueError: If the encounter lacks required data or has invalid moodCode
        """
        encounter = ccda_model

        # Validate moodCode
        if not encounter.mood_code:
            raise ValueError("Planned Encounter must have a moodCode attribute")

        mood_code = encounter.mood_code.upper()
        if mood_code not in self.APPOINTMENT_MOOD_CODES:
            raise ValueError(
                f"moodCode='{mood_code}' is not an appointment moodCode; "
                f"expected one of {self.APPOINTMENT_MOOD_CODES}"
            )

        # Validate reference_registry (required for patient participant)
        if not self.reference_registry:
            raise ValueError(
                "reference_registry is required. "
                "Cannot create Appointment without patient reference."
            )

        # Build FHIR Appointment resource
        fhir_appointment: JSONObject = {
            "resourceType": FHIRCodes.ResourceTypes.APPOINTMENT,
        }

        # Generate ID from encounter identifier
        if encounter.id and len(encounter.id) > 0:
            first_id = encounter.id[0]
            fhir_appointment["id"] = self._generate_appointment_id(
                first_id.root, first_id.extension
            )

        # Identifiers
        if encounter.id:
            fhir_appointment["identifier"] = [
                self.create_identifier(id_elem.root, id_elem.extension)
                for id_elem in encounter.id
                if id_elem.root
            ]

        # Status (required 1..1)
        status = self._map_status(encounter.status_code, mood_code)
        fhir_appointment["status"] = status

        # ServiceType (0..*) - from encounter code
        if encounter.code:
            service_type = self.convert_code_to_codeable_concept(encounter.code)
            if service_type:
                fhir_appointment["serviceType"] = [service_type.to_dict()]

        # Description (0..1) - from code displayName or originalText
        if encounter.code:
            description = self._extract_description(encounter.code)
            if description:
                fhir_appointment["description"] = description

        # Start / End - from effectiveTime
        # Per FHIR constraint app-1: either both start and end, or neither
        if encounter.effective_time:
            start, end = self._convert_timing(encounter.effective_time)
            if start and end:
                fhir_appointment["start"] = start
                fhir_appointment["end"] = end
                # minutesDuration - calculate when both start and end present
                duration = self._calculate_minutes_duration(start, end)
                if duration is not None:
                    fhir_appointment["minutesDuration"] = duration
            elif start and status in ("proposed", "cancelled", "waitlist"):
                # app-3: only proposed/cancelled/waitlist can omit end
                fhir_appointment["start"] = start

        # Created (0..1) - from first author time
        if encounter.author:
            created = self._extract_created(encounter.author)
            if created:
                fhir_appointment["created"] = created

        # Priority (0..1) - from priorityCode (unsigned int in FHIR, iCal scale)
        if encounter.priority_code:
            priority = self._map_priority(encounter.priority_code)
            if priority is not None:
                fhir_appointment["priority"] = priority

        # Participant (required 1..*)
        participants = self._build_participants(encounter, mood_code)
        fhir_appointment["participant"] = participants

        # ReasonCode / ReasonReference (0..*) - from entryRelationship indications
        if encounter.entry_relationship:
            reasons = self._extract_reasons(encounter.entry_relationship)
            if reasons.codes:
                fhir_appointment["reasonCode"] = [c.to_dict() for c in reasons.codes]
            if reasons.references:
                fhir_appointment["reasonReference"] = [r.to_dict() for r in reasons.references]

        # Comment (0..1) - Appointment uses a single comment string, not note[]
        notes = self.extract_notes_from_element(encounter, include_comments=False)
        if notes:
            fhir_appointment["comment"] = notes[0].get("text", "")

        # Narrative
        narrative = self._generate_narrative(entry=encounter, section=section)
        if narrative:
            fhir_appointment["text"] = narrative.model_dump(exclude_none=True)

        return fhir_appointment

    def _generate_appointment_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Appointment ID from C-CDA identifiers."""
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Appointment", root, extension)

    def _map_status(self, status_code: CS | None, mood_code: str) -> str:
        """Map C-CDA status and moodCode to FHIR Appointment status.

        The status is derived from a combination of:
        1. Explicit statusCode mapping (if present)
        2. MoodCode hint (APT → booked, ARQ → proposed)

        Args:
            status_code: The C-CDA status code
            mood_code: The C-CDA moodCode (APT or ARQ)

        Returns:
            FHIR Appointment status code
        """
        # Default from moodCode
        default_status = APPOINTMENT_MOOD_TO_STATUS.get(
            mood_code, FHIRCodes.AppointmentStatus.PROPOSED
        )

        if not status_code:
            return default_status

        # Check nullFlavor
        if status_code.null_flavor:
            return default_status

        if not status_code.code:
            return default_status

        code = status_code.code.lower()
        return APPOINTMENT_STATUS_TO_FHIR.get(code, default_status)

    def _convert_timing(self, effective_time: IVL_TS | TS | str) -> tuple[str | None, str | None]:
        """Convert C-CDA effectiveTime to FHIR start/end instants.

        Args:
            effective_time: The C-CDA effectiveTime

        Returns:
            Tuple of (start, end) datetime strings
        """
        if isinstance(effective_time, str):
            converted = self.convert_date(effective_time)
            return converted, None

        if isinstance(effective_time, IVL_TS):
            # IVL_TS with direct value = point-in-time
            if effective_time.value:
                return self.convert_date(effective_time.value), None

            # IVL_TS with low/high = period
            start = None
            end = None

            if effective_time.low and effective_time.low.value:
                start = self.convert_date(str(effective_time.low.value))

            if effective_time.high and effective_time.high.value:
                end = self.convert_date(str(effective_time.high.value))

            return start, end

        if isinstance(effective_time, TS) and effective_time.value:
            return self.convert_date(effective_time.value), None

        return None, None

    def _extract_created(self, authors: list[Author]) -> str | None:
        """Extract created date from authors (earliest author timestamp).

        Per FHIR Appointment.created: the date that the appointment was initially
        created. This corresponds to the order/submit date.
        Uses min() (earliest) because "created" represents when the appointment
        was first entered, not when it was last modified.

        Args:
            authors: List of C-CDA author elements

        Returns:
            FHIR dateTime string or None
        """
        if not authors:
            return None

        authors_with_time = [a for a in authors if a.time and a.time.value]
        if not authors_with_time:
            return None

        earliest = min(authors_with_time, key=lambda a: str(a.time.value))  # type: ignore[union-attr]
        time = earliest.time
        assert time is not None and time.value is not None  # guaranteed by filter
        return self.convert_date(time.value)

    def _map_priority(self, priority_code: CE | None) -> int | None:
        """Map C-CDA priorityCode to FHIR Appointment priority (unsigned int).

        Per FHIR R4B: 0 = undefined, lower number = higher priority.
        iCal: 1-4 = high, 5 = normal, 6-9 = low.

        Args:
            priority_code: The C-CDA priorityCode

        Returns:
            Integer priority or None
        """
        if not priority_code or not priority_code.code:
            return None

        code = priority_code.code.upper()
        mapping = {
            "EM": 1,  # Emergency → high
            "UR": 2,  # Urgent → high
            "A": 3,  # ASAP → high
            "R": 5,  # Routine → normal
            "EL": 7,  # Elective → low
        }
        return mapping.get(code)

    def _build_participants(self, encounter: CCDAEncounter, mood_code: str) -> list[JSONObject]:
        """Build FHIR Appointment.participant list.

        Per FHIR R4B, participant is required (1..*) and must include at least
        the patient. Additional participants come from performers and locations.

        For confirmed appointments (APT), all participants get status "accepted".
        For appointment requests (ARQ), non-patient participants get "needs-action"
        since the appointment is not yet confirmed.

        Args:
            encounter: The C-CDA encounter element
            mood_code: The C-CDA moodCode (APT or ARQ)

        Returns:
            List of FHIR Appointment.participant objects (always non-empty)

        Raises:
            ValueError: If no participants can be built (spec requires 1..*)
        """
        participants: list[JSONObject] = []
        # ARQ = request, providers haven't accepted yet
        provider_status = "accepted" if mood_code == "APT" else "needs-action"

        # Patient participant (required)
        if self.reference_registry:
            patient_ref = self.reference_registry.get_patient_reference()
            if patient_ref:
                participants.append(
                    {
                        "actor": patient_ref.to_dict(),
                        "required": "required",
                        "status": "accepted",
                    }
                )

        # Performer participants (providers + organizations)
        if encounter.performer:
            for performer in encounter.performer:
                if not performer or not performer.assigned_entity:
                    continue

                entity = performer.assigned_entity

                # Practitioner participant
                if entity.id:
                    root, extension = self.select_preferred_identifier(entity.id)
                    if root:
                        pract_id = self._generate_practitioner_id(root, extension)
                        from .author_references import format_person_display

                        display = format_person_display(entity.assigned_person)
                        participant_entry: JSONObject = {
                            "actor": FHIRReference(
                                reference=f"urn:uuid:{pract_id}", display=display
                            ).to_dict(),
                            "required": "required",
                            "status": provider_status,
                        }
                        # Add participant type from assignedEntity code (specialty/role)
                        if entity.code:
                            ptype = self.convert_code_to_codeable_concept(entity.code)
                            if ptype:
                                participant_entry["type"] = [ptype.to_dict()]
                        participants.append(participant_entry)

                # Organization participant (from representedOrganization)
                org = entity.represented_organization
                if org:
                    org_display = format_organization_display(org)
                    org_ref: FHIRReference | None = None

                    # Try org's own IDs
                    if org.id:
                        for id_elem in org.id:
                            if id_elem.root:
                                org_id = self._generate_organization_id(
                                    id_elem.root, id_elem.extension
                                )
                                org_ref = FHIRReference(
                                    reference=f"urn:uuid:{org_id}", display=org_display
                                )
                                break

                    # Fall back to entity's ID for org reference
                    if not org_ref and entity.id:
                        for id_elem in entity.id:
                            if id_elem.root:
                                org_id = self._generate_organization_id(
                                    id_elem.root, id_elem.extension
                                )
                                org_ref = FHIRReference(
                                    reference=f"urn:uuid:{org_id}", display=org_display
                                )
                                break

                    # Last resort: display-only
                    if not org_ref and org_display:
                        org_ref = FHIRReference(display=org_display)

                    if org_ref:
                        participants.append(
                            {
                                "actor": org_ref.to_dict(),
                                "required": "information-only",
                                "status": provider_status,
                            }
                        )

        # Location participants (from participant with LOC typeCode)
        if encounter.participant:
            for part in encounter.participant:
                if part.type_code == "LOC" and part.participant_role:
                    role = part.participant_role
                    if role.id:
                        for id_elem in role.id:
                            if id_elem.root:
                                loc_id = self._generate_location_id(id_elem.root, id_elem.extension)
                                participants.append(
                                    {
                                        "actor": {
                                            "reference": f"urn:uuid:{loc_id}",
                                            "display": self._get_location_display(role),
                                        },
                                        "required": "information-only",
                                        "status": provider_status,
                                    }
                                )
                                break

        if not participants:
            raise ValueError(
                "Appointment must have at least one participant (FHIR 1..*). "
                "Ensure reference_registry has a patient reference."
            )

        return participants

    def _get_location_display(self, participant_role: ParticipantRole) -> str | None:
        """Extract display name from participant role for location."""
        if participant_role.playing_entity and participant_role.playing_entity.name:
            names = participant_role.playing_entity.name
            if names and len(names) > 0:
                name = names[0]
                if isinstance(name, str):
                    return name
                if hasattr(name, "value") and name.value:
                    return name.value
        return None

    def _extract_reasons(self, entry_relationships: list[EntryRelationship]) -> ReasonResult:
        """Extract reason codes and references from entryRelationships.

        Delegates to base class method for consistent handling across converters,
        producing both reasonCode and reasonReference when a Problem Observation
        matches a Condition in the bundle.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            ReasonResult with codes and references lists
        """
        return self.extract_reasons_from_entry_relationships(
            entry_relationships,
            problem_template_id=TemplateIds.PROBLEM_OBSERVATION,
        )

    def _extract_description(self, code: CE) -> str | None:
        """Extract appointment description from C-CDA code element.

        Uses displayName first, falls back to originalText.

        Args:
            code: The C-CDA code element

        Returns:
            Description string or None
        """
        if code.display_name:
            return code.display_name
        if code.original_text:
            text = code.original_text
            if isinstance(text, str):
                return text
            if hasattr(text, "value") and text.value:
                return text.value
        return None

    def _calculate_minutes_duration(self, start: str, end: str) -> int | None:
        """Calculate duration in minutes between start and end datetimes.

        Args:
            start: FHIR dateTime string
            end: FHIR dateTime string

        Returns:
            Duration in minutes (positive integer) or None if unable to calculate
        """
        from datetime import datetime

        try:
            # Parse ISO 8601 datetime strings
            start_dt = datetime.fromisoformat(start)
            end_dt = datetime.fromisoformat(end)
            delta = end_dt - start_dt
            minutes = int(delta.total_seconds() // 60)
            return minutes if minutes > 0 else None
        except (ValueError, TypeError):
            return None
