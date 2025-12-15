"""E2E tests for Procedure resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

PROCEDURES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.7.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestProcedureConversion:
    """E2E tests for C-CDA Procedure Activity to FHIR Procedure conversion."""

    def test_converts_procedure_code(
        self, ccda_procedure: str, fhir_procedure: JSONObject
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
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "completed"

    def test_converts_performed_date(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to performedDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performedDateTime" in procedure
        assert procedure["performedDateTime"] == "2012-08-06"

    def test_converts_identifiers(
        self, ccda_procedure: str, fhir_procedure: JSONObject
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
        self, ccda_procedure: str, fhir_procedure: JSONObject
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
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that code text is populated from displayName."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        assert procedure["code"]["text"] == "Excision of appendix"

    def test_resource_type_is_procedure(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that the resource type is Procedure."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["resourceType"] == "Procedure"

    def test_converts_body_site(self, ccda_procedure_with_body_site: str) -> None:
        """Test that targetSiteCode is converted to bodySite."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_body_site, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "bodySite" in procedure
        assert len(procedure["bodySite"]) >= 1
        body_site = procedure["bodySite"][0]
        snomed_coding = next(
            (c for c in body_site["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "71854001"
        assert snomed_coding["display"] == "Colon structure"

    def test_converts_performer(self, ccda_procedure_with_performer: str) -> None:
        """Test that performer is converted to performer.actor."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_performer, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performer" in procedure
        assert len(procedure["performer"]) >= 1
        performer = procedure["performer"][0]
        assert "actor" in performer
        assert "reference" in performer["actor"]
        assert "Practitioner/" in performer["actor"]["reference"]

    def test_converts_location(self, ccda_procedure_with_location: str) -> None:
        """Test that LOC participant is converted to location."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_location, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "location" in procedure
        assert "reference" in procedure["location"]
        assert "Location/" in procedure["location"]["reference"]
        # Display is optional but should include location name if present
        if "display" in procedure["location"]:
            assert procedure["location"]["display"] == "Operating Room 1"

    def test_converts_reason_code(self, ccda_procedure_with_reason: str) -> None:
        """Test that RSON entryRelationship is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_reason, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "reasonCode" in procedure
        assert len(procedure["reasonCode"]) >= 1
        reason = procedure["reasonCode"][0]
        icd10_coding = next(
            (c for c in reason["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"),
            None
        )
        assert icd10_coding is not None
        assert icd10_coding["code"] == "K51.90"

    def test_converts_author_to_recorder(self, ccda_procedure_with_author: str) -> None:
        """Test that author is converted to recorder."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure
        assert "reference" in procedure["recorder"]
        assert "Practitioner/" in procedure["recorder"]["reference"]

    def test_converts_outcome(self, ccda_procedure_with_outcome: str) -> None:
        """Test that OUTC entryRelationship is converted to outcome."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_outcome, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "outcome" in procedure
        snomed_coding = next(
            (c for c in procedure["outcome"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "385669000"
        assert snomed_coding["display"] == "Successful"

    def test_converts_complications(self, ccda_procedure_with_complications: str) -> None:
        """Test that COMP entryRelationship is converted to complication."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_complications, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "complication" in procedure
        assert len(procedure["complication"]) >= 1
        complication = procedure["complication"][0]
        snomed_coding = next(
            (c for c in complication["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "50417007"

    def test_converts_followup(self, ccda_procedure_with_followup: str) -> None:
        """Test that SPRT entryRelationship is converted to followUp."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_followup, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "followUp" in procedure
        assert len(procedure["followUp"]) >= 1
        followup = procedure["followUp"][0]
        snomed_coding = next(
            (c for c in followup["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "308273005"

    def test_converts_notes(self, ccda_procedure_with_notes: str) -> None:
        """Test that text and Comment Activity are converted to note."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_notes, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "note" in procedure
        assert len(procedure["note"]) >= 1
        # Check that at least one note contains text from procedure/text
        has_text_note = any(
            "Laparoscopic approach" in note.get("text", "")
            for note in procedure["note"]
        )
        # Check that at least one note contains Comment Activity text
        has_comment_note = any(
            "Three ports used" in note.get("text", "")
            for note in procedure["note"]
        )
        assert has_text_note or has_comment_note

    def test_multiple_authors_selects_latest_for_recorder(
        self, ccda_procedure_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for recorder field."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_multiple_authors, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure

        # Latest author is LATEST-PROC-DOC (time: 20231106153000)
        # Not EARLY-PROC-DOC (time: 20231105100000)
        assert "LATEST-PROC-DOC" in procedure["recorder"]["reference"]
        assert "EARLY-PROC-DOC" not in procedure["recorder"]["reference"]
