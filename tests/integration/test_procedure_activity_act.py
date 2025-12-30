"""Tests for Procedure Activity Act template conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

PROCEDURES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.7.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestProcedureActivityAct:
    """Tests for C-CDA Procedure Activity Act (2.16.840.1.113883.10.20.22.4.12) conversion."""

    def test_converts_procedure_activity_act_to_procedure(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that Procedure Activity Act is converted to FHIR Procedure."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["resourceType"] == "Procedure"

    def test_converts_procedure_activity_act_code(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that procedure code from Act is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure

        # Check for SNOMED code
        snomed = next(
            (c for c in procedure["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "274025005"
        assert snomed["display"] == "Colonic polypectomy"

    def test_converts_procedure_activity_act_status(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that status code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "completed"

    def test_converts_procedure_activity_act_effective_time(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that effectiveTime is correctly converted to performedDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performedDateTime" in procedure
        # Note: effectiveTime value="20110203" should convert to a date
        assert procedure["performedDateTime"].startswith("2011-02-03")

    def test_converts_procedure_activity_act_identifier(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that procedure identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "identifier" in procedure
        assert len(procedure["identifier"]) > 0

        # Check first identifier
        identifier = procedure["identifier"][0]
        assert "system" in identifier
        assert "value" in identifier

    def test_converts_procedure_activity_act_performer(
        self, ccda_procedure_activity_act: str
    ) -> None:
        """Test that performer is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_activity_act, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performer" in procedure
        assert len(procedure["performer"]) > 0

        # Check performer has actor reference
        performer = procedure["performer"][0]
        assert "actor" in performer
        assert "reference" in performer["actor"]
        assert performer["actor"]["reference"].startswith("Practitioner/")
