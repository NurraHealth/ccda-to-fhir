"""C-CDA to FHIR converters."""

from __future__ import annotations

from .allergy_intolerance import (
    AllergyIntoleranceConverter,
    convert_allergy_concern_act,
)
from .careteam import CareTeamConverter
from .composition import CompositionConverter
from .condition import ConditionConverter, convert_problem_concern_act
from .device import DeviceConverter
from .diagnostic_report import DiagnosticReportConverter
from .encounter import EncounterConverter
from .immunization import ImmunizationConverter
from .location import LocationConverter
from .medication_dispense import MedicationDispenseConverter
from .medication_request import MedicationRequestConverter, convert_medication_activity
from .medication_statement import MedicationStatementConverter, convert_medication_statement
from .note_activity import NoteActivityConverter, convert_note_activity
from .observation import ObservationConverter
from .organization import OrganizationConverter
from .patient import PatientConverter
from .practitioner import PractitionerConverter
from .practitioner_role import PractitionerRoleConverter
from .procedure import ProcedureConverter
from .provenance import ProvenanceConverter
from .service_request import ServiceRequestConverter

__all__ = [
    "PatientConverter",
    "ConditionConverter",
    "convert_problem_concern_act",
    "AllergyIntoleranceConverter",
    "convert_allergy_concern_act",
    "CareTeamConverter",
    "MedicationRequestConverter",
    "convert_medication_activity",
    "MedicationStatementConverter",
    "convert_medication_statement",
    "NoteActivityConverter",
    "convert_note_activity",
    "MedicationDispenseConverter",
    "ImmunizationConverter",
    "ObservationConverter",
    "DeviceConverter",
    "DiagnosticReportConverter",
    "CompositionConverter",
    "ProcedureConverter",
    "ServiceRequestConverter",
    "EncounterConverter",
    "LocationConverter",
    "PractitionerConverter",
    "PractitionerRoleConverter",
    "OrganizationConverter",
    "ProvenanceConverter",
]
