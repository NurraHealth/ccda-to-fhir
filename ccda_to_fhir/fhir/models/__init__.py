"""FHIR R4B Pydantic models.

This module provides access to FHIR R4B resources using the fhir.resources library.
The fhir.resources library provides complete, validated Pydantic models for all
FHIR R4B resources and datatypes.

Documentation: https://github.com/nazrulworld/fhir.resources
"""

from __future__ import annotations

# Re-export core FHIR resources needed for C-CDA conversion
from fhir.resources.allergyintolerance import AllergyIntolerance
from fhir.resources.bundle import Bundle, BundleEntry
from fhir.resources.condition import Condition
from fhir.resources.documentreference import DocumentReference
from fhir.resources.encounter import Encounter
from fhir.resources.immunization import Immunization
from fhir.resources.medicationrequest import MedicationRequest
from fhir.resources.observation import Observation
from fhir.resources.patient import Patient
from fhir.resources.practitioner import Practitioner
from fhir.resources.procedure import Procedure

# Re-export common FHIR datatypes
from fhir.resources.address import Address
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from fhir.resources.contactpoint import ContactPoint
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier
from fhir.resources.period import Period
from fhir.resources.quantity import Quantity
from fhir.resources.reference import Reference

__all__ = [
    # Resources
    "AllergyIntolerance",
    "Bundle",
    "BundleEntry",
    "Condition",
    "DocumentReference",
    "Encounter",
    "Immunization",
    "MedicationRequest",
    "Observation",
    "Patient",
    "Practitioner",
    "Procedure",
    # Datatypes
    "Address",
    "CodeableConcept",
    "Coding",
    "ContactPoint",
    "HumanName",
    "Identifier",
    "Period",
    "Quantity",
    "Reference",
]
