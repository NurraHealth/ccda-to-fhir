"""E2E tests for Procedure resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

PROCEDURES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.7.1"


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestProcedureConversion:
    """E2E tests for C-CDA Procedure Activity to FHIR Procedure conversion."""

    def test_converts_procedure_code(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that procedure code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        snomed = next(
            (c for c in procedure["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "80146002"
        assert snomed["display"] == "Excision of appendix"

    def test_converts_status(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "completed"

    def test_converts_performed_date(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that effectiveTime is converted to performedDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performedDateTime" in procedure
        assert procedure["performedDateTime"] == "2012-08-06"

    def test_converts_identifiers(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "identifier" in procedure
        assert len(procedure["identifier"]) == 2
        assert procedure["identifier"][0]["value"] == "545069400001"

    def test_converts_icd10_translation(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that ICD-10 PCS translation is included."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        icd10 = next(
            (c for c in procedure["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"),
            None
        )
        assert icd10 is not None
        assert icd10["code"] == "0DBJ4ZZ"

    def test_converts_code_text(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that code text is populated from displayName."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        assert procedure["code"]["text"] == "Excision of appendix"

    def test_resource_type_is_procedure(
        self, ccda_procedure: str, fhir_procedure: dict[str, Any]
    ) -> None:
        """Test that the resource type is Procedure."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["resourceType"] == "Procedure"
