"""FHIR R4B Pydantic models.

This module provides access to FHIR R4B resources using the fhir.resources library.
The fhir.resources library provides complete, validated Pydantic models for all
FHIR R4B resources and datatypes.

Documentation: https://github.com/nazrulworld/fhir.resources
"""

from __future__ import annotations

# Re-export common FHIR datatypes
from fhir.resources.R4B.address import Address

# Re-export core FHIR resources needed for C-CDA conversion
from fhir.resources.R4B.allergyintolerance import AllergyIntolerance
from fhir.resources.R4B.bundle import Bundle, BundleEntry
from fhir.resources.R4B.codeableconcept import CodeableConcept
from fhir.resources.R4B.coding import Coding
from fhir.resources.R4B.composition import Composition
from fhir.resources.R4B.condition import Condition
from fhir.resources.R4B.contactpoint import ContactPoint
from fhir.resources.R4B.device import Device
from fhir.resources.R4B.diagnosticreport import DiagnosticReport
from fhir.resources.R4B.documentreference import DocumentReference
from fhir.resources.R4B.encounter import Encounter
from fhir.resources.R4B.humanname import HumanName
from fhir.resources.R4B.identifier import Identifier
from fhir.resources.R4B.immunization import Immunization
from fhir.resources.R4B.location import Location
from fhir.resources.R4B.medicationrequest import MedicationRequest
from fhir.resources.R4B.observation import Observation
from fhir.resources.R4B.organization import Organization
from fhir.resources.R4B.patient import Patient
from fhir.resources.R4B.period import Period
from fhir.resources.R4B.practitioner import Practitioner
from fhir.resources.R4B.practitionerrole import PractitionerRole
from fhir.resources.R4B.procedure import Procedure
from fhir.resources.R4B.provenance import Provenance
from fhir.resources.R4B.quantity import Quantity
from fhir.resources.R4B.range import Range
from fhir.resources.R4B.reference import Reference

__all__ = [
    # Resources
    "AllergyIntolerance",
    "Bundle",
    "BundleEntry",
    "Composition",
    "Condition",
    "Device",
    "DiagnosticReport",
    "DocumentReference",
    "Encounter",
    "Immunization",
    "Location",
    "MedicationRequest",
    "Observation",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Procedure",
    "Provenance",
    # Datatypes
    "Address",
    "CodeableConcept",
    "Coding",
    "ContactPoint",
    "HumanName",
    "Identifier",
    "Period",
    "Quantity",
    "Range",
    "Reference",
]
