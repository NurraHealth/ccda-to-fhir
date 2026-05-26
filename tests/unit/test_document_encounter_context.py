"""Tests for document-level encounter context propagation."""

from ccda_to_fhir.convert import DocumentConverter
from ccda_to_fhir.types import FHIRResourceDict


def test_propagates_document_encounter_only_to_document_references() -> None:
    converter = DocumentConverter()
    resources: list[FHIRResourceDict] = [
        {"resourceType": "Encounter", "id": "encounter-1"},
        {"resourceType": "Condition", "id": "condition-1"},
        {"resourceType": "Observation", "id": "observation-1"},
        {"resourceType": "Procedure", "id": "procedure-1"},
        {"resourceType": "ServiceRequest", "id": "service-request-1"},
        {"resourceType": "MedicationRequest", "id": "medication-request-1"},
        {"resourceType": "AllergyIntolerance", "id": "allergy-1"},
        {"resourceType": "Immunization", "id": "immunization-1"},
        {"resourceType": "DiagnosticReport", "id": "diagnostic-report-1"},
        {"resourceType": "MedicationStatement", "id": "medication-statement-1"},
        {"resourceType": "MedicationDispense", "id": "medication-dispense-1"},
        {
            "resourceType": "DocumentReference",
            "id": "document-reference-1",
            "context": {
                "encounter": [
                    {
                        "reference": "urn:uuid:stale-header-encounter",
                        "display": "Office visit",
                    }
                ]
            },
        },
        {"resourceType": "Provenance", "id": "provenance-1"},
    ]

    converter._propagate_document_encounter_context(resources, "urn:uuid:encounter-1")

    clinical_resource_types = {
        "AllergyIntolerance",
        "Condition",
        "DiagnosticReport",
        "Immunization",
        "MedicationRequest",
        "Observation",
        "Procedure",
        "ServiceRequest",
    }
    for resource in resources:
        if resource["resourceType"] in clinical_resource_types:
            assert "encounter" not in resource

    context_types = {"MedicationDispense", "MedicationStatement"}
    for resource in resources:
        if resource["resourceType"] in context_types:
            assert "context" not in resource

    doc_ref = next(r for r in resources if r["resourceType"] == "DocumentReference")
    assert doc_ref["context"] == {
        "encounter": [{"reference": "urn:uuid:encounter-1", "display": "Office visit"}]
    }

    provenance = next(r for r in resources if r["resourceType"] == "Provenance")
    assert "encounter" not in provenance
    assert "context" not in provenance


def test_preserves_existing_explicit_encounter_context() -> None:
    converter = DocumentConverter()
    resources: list[FHIRResourceDict] = [
        {"resourceType": "Encounter", "id": "document-encounter"},
        {"resourceType": "Encounter", "id": "explicit-encounter"},
        {
            "resourceType": "Condition",
            "id": "condition-1",
            "encounter": {"reference": "urn:uuid:explicit-encounter"},
        },
        {
            "resourceType": "MedicationStatement",
            "id": "medication-statement-1",
            "context": {"reference": "urn:uuid:explicit-encounter"},
        },
        {
            "resourceType": "DocumentReference",
            "id": "document-reference-1",
            "context": {"encounter": [{"reference": "urn:uuid:explicit-encounter"}]},
        },
    ]

    converter._propagate_document_encounter_context(resources, "urn:uuid:document-encounter")

    condition = next(r for r in resources if r["resourceType"] == "Condition")
    assert condition["encounter"] == {"reference": "urn:uuid:explicit-encounter"}

    medication = next(r for r in resources if r["resourceType"] == "MedicationStatement")
    assert medication["context"] == {"reference": "urn:uuid:explicit-encounter"}

    doc_ref = next(r for r in resources if r["resourceType"] == "DocumentReference")
    assert doc_ref["context"] == {"encounter": [{"reference": "urn:uuid:explicit-encounter"}]}


def test_document_encounter_does_not_override_or_create_clinical_context() -> None:
    converter = DocumentConverter()
    resources: list[FHIRResourceDict] = [
        {"resourceType": "Encounter", "id": "document-encounter"},
        {
            "resourceType": "Procedure",
            "id": "historical-procedure",
            "performedDateTime": "1977-08-26",
        },
        {
            "resourceType": "Observation",
            "id": "future-result",
            "effectiveDateTime": "2026-08-15",
        },
        {
            "resourceType": "Condition",
            "id": "explicit-condition",
            "encounter": {"reference": "urn:uuid:explicit-encounter"},
        },
        {
            "resourceType": "MedicationStatement",
            "id": "explicit-medication",
            "context": {"reference": "urn:uuid:explicit-encounter"},
        },
    ]

    converter._propagate_document_encounter_context(resources, "urn:uuid:document-encounter")

    historical_procedure = next(r for r in resources if r["id"] == "historical-procedure")
    assert "encounter" not in historical_procedure

    future_result = next(r for r in resources if r["id"] == "future-result")
    assert "encounter" not in future_result

    explicit_condition = next(r for r in resources if r["id"] == "explicit-condition")
    assert explicit_condition["encounter"] == {"reference": "urn:uuid:explicit-encounter"}

    explicit_medication = next(r for r in resources if r["id"] == "explicit-medication")
    assert explicit_medication["context"] == {"reference": "urn:uuid:explicit-encounter"}
