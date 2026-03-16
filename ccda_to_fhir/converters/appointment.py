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

from ccda_to_fhir.ccda.models.datatypes import IVL_TS, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.constants import (
    APPOINTMENT_MOOD_TO_STATUS,
    APPOINTMENT_STATUS_TO_FHIR,
    FHIRCodes,
)
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter


class AppointmentConverter(BaseConverter[CCDAEncounter]):
    """Convert C-CDA Planned Encounter to FHIR Appointment resource.

    Handles Planned Encounter (V2) entries with moodCode APT or ARQ.
    These represent booked or requested appointments respectively.

    Reference: docs/mapping/19-appointment.md
    """

    # moodCodes that indicate an appointment (vs a planned encounter → ServiceRequest)
    APPOINTMENT_MOOD_CODES = {"APT", "ARQ"}

    def convert(self, ccda_model: CCDAEncounter, section=None) -> FHIRResourceDict:
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

        # Status (required)
        status = self._map_status(encounter.status_code, mood_code)
        fhir_appointment["status"] = status

        # ServiceType - from encounter code
        if encounter.code:
            service_type = self.convert_code_to_codeable_concept(encounter.code)
            if service_type:
                fhir_appointment["serviceType"] = [service_type.to_dict()]

        # Start / End - from effectiveTime
        if encounter.effective_time:
            start, end = self._convert_timing(encounter.effective_time)
            if start:
                fhir_appointment["start"] = start
            if end:
                fhir_appointment["end"] = end

        # Created (order date) - from first author time
        if encounter.author:
            created = self._extract_created(encounter.author)
            if created:
                fhir_appointment["created"] = created

        # Priority - from priorityCode (unsigned int in FHIR)
        if encounter.priority_code:
            priority = self._map_priority(encounter.priority_code)
            if priority is not None:
                fhir_appointment["priority"] = priority

        # Participant (required 1..*) - patient + performers
        participants = self._build_participants(encounter)
        if not participants:
            raise ValueError(
                "Appointment must have at least one participant. "
                "Ensure reference_registry has a patient reference."
            )
        fhir_appointment["participant"] = participants

        # Reason - from entryRelationship indications
        if encounter.entry_relationship:
            reasons = self._extract_reason_codes(encounter.entry_relationship)
            if reasons:
                fhir_appointment["reasonCode"] = reasons

        # Notes → comment (Appointment uses a single comment string)
        notes = self.extract_notes_from_element(encounter, include_comments=False)
        if notes:
            fhir_appointment["comment"] = notes[0].get("text", "")

        # Narrative
        narrative = self._generate_narrative(entry=encounter, section=section)
        if narrative:
            fhir_appointment["text"] = narrative

        return fhir_appointment

    def _generate_appointment_id(self, root: str | None, extension: str | None) -> str:
        """Generate a FHIR Appointment ID from C-CDA identifiers."""
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        return generate_id_from_identifiers("Appointment", root, extension)

    def _map_status(self, status_code, mood_code: str) -> str:
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

    def _extract_created(self, authors: list) -> str | None:
        """Extract created date from authors (earliest author timestamp).

        Per FHIR Appointment.created: the date that the appointment was initially
        created. This corresponds to the order/submit date.

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

        earliest = min(authors_with_time, key=lambda a: a.time.value)
        return self.convert_date(earliest.time.value)

    def _map_priority(self, priority_code) -> int | None:
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

    def _build_participants(self, encounter: CCDAEncounter) -> list[JSONObject]:
        """Build FHIR Appointment.participant list.

        Per FHIR R4B, participant is required (1..*) and must include at least
        the patient. Additional participants come from performers and locations.

        Args:
            encounter: The C-CDA encounter element

        Returns:
            List of FHIR Appointment.participant objects
        """
        participants: list[JSONObject] = []

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

        # Performer participants (providers)
        if encounter.performer:
            performer_refs = self.extract_performer_references(encounter.performer)
            for ref in performer_refs:
                participants.append(
                    {
                        "actor": ref.to_dict(),
                        "required": "required",
                        "status": "accepted",
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
                                        "status": "accepted",
                                    }
                                )
                                break

        return participants

    def _get_location_display(self, participant_role) -> str | None:
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

    def _extract_reason_codes(self, entry_relationships: list) -> list[JSONObject]:
        """Extract reason codes from entry relationships.

        Args:
            entry_relationships: List of C-CDA entry relationship elements

        Returns:
            List of FHIR CodeableConcept dicts
        """
        reasons: list[JSONObject] = []
        for entry_rel in entry_relationships:
            if entry_rel.type_code == "RSON" and entry_rel.observation:
                obs = entry_rel.observation
                if obs.value:
                    code = self.convert_code_to_codeable_concept(obs.value)
                    if code:
                        reasons.append(code.to_dict())
        return reasons
