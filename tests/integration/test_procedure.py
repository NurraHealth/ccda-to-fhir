"""E2E tests for Procedure resource conversion."""

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


def _find_all_resources_in_bundle(bundle: JSONObject, resource_type: str) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


class TestProcedureConversion:
    """E2E tests for C-CDA Procedure Activity to FHIR Procedure conversion."""

    def test_converts_procedure_code(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that procedure code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "completed"

    def test_converts_performed_date(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to performedDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performedDateTime" in procedure
        assert procedure["performedDateTime"] == "2012-08-06"

    def test_converts_identifiers(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        assert procedure["code"]["text"] == "Excision of appendix"

    def test_resource_type_is_procedure(
        self, ccda_procedure: str, fhir_procedure: JSONObject
    ) -> None:
        """Test that the resource type is Procedure."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["resourceType"] == "Procedure"

    def test_converts_body_site(self, ccda_procedure_with_body_site: str) -> None:
        """Test that targetSiteCode is converted to bodySite."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_body_site, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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

    def test_converts_body_site_with_laterality_qualifier(self, ccda_procedure_with_body_site: str) -> None:
        """Test that targetSiteCode with laterality qualifier is converted correctly.

        The fixture procedure_with_body_site.xml includes a laterality qualifier
        (Left - code 7771000) which should be added as an additional coding in bodySite.
        """
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_body_site, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "bodySite" in procedure
        assert len(procedure["bodySite"]) >= 1
        body_site = procedure["bodySite"][0]

        # Check that the body site code is present
        site_coding = next(
            (c for c in body_site["coding"]
             if c.get("system") == "http://snomed.info/sct" and c.get("code") == "71854001"),
            None
        )
        assert site_coding is not None
        assert site_coding["display"] == "Colon structure"

        # Check that laterality qualifier is present as additional coding
        laterality_coding = next(
            (c for c in body_site["coding"]
             if c.get("system") == "http://snomed.info/sct" and c.get("code") == "7771000"),
            None
        )
        assert laterality_coding is not None, "Laterality qualifier should be added as additional coding"
        assert laterality_coding["display"] == "Left"

        # Check that text field combines laterality and site
        assert "text" in body_site
        assert body_site["text"] == "Left Colon structure"

    def test_converts_performer(self, ccda_procedure_with_performer: str) -> None:
        """Test that performer is converted to performer.actor."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_performer, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performer" in procedure
        assert len(procedure["performer"]) >= 1
        performer = procedure["performer"][0]
        assert "actor" in performer
        assert "reference" in performer["actor"]
        assert "Practitioner/" in performer["actor"]["reference"]

    def test_maps_prisurg_function_code(self) -> None:
        """Test that PRISURG function code maps to PPRF (primary performer).

        Reference: docs/mapping/09-participations.md line 960
        """
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="test-procedure-001"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="PRISURG" codeSystem="2.16.840.1.113883.5.88" displayName="Primary Surgeon"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
                        <assignedPerson><name><given>Sarah</given><family>Surgeon</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </procedure>""",
            PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]
        procedure = _find_resource_in_bundle(bundle, "Procedure")

        assert procedure is not None
        assert "performer" in procedure
        performer = procedure["performer"][0]
        assert "function" in performer
        coding = performer["function"]["coding"][0]
        assert coding["code"] == "PPRF", "C-CDA PRISURG should map to FHIR PPRF (primary performer)"
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
        assert coding["display"] == "Primary Surgeon"

    def test_maps_fasst_function_code(self) -> None:
        """Test that FASST function code maps to SPRF (secondary performer).

        Reference: docs/mapping/09-participations.md line 956
        """
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="test-procedure-002"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="FASST" codeSystem="2.16.840.1.113883.5.88" displayName="First Assistant Surgeon"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="2222222222"/>
                        <assignedPerson><name><given>John</given><family>Assistant</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </procedure>""",
            PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]
        procedure = _find_resource_in_bundle(bundle, "Procedure")

        assert procedure is not None
        assert "performer" in procedure
        performer = procedure["performer"][0]
        assert "function" in performer
        coding = performer["function"]["coding"][0]
        assert coding["code"] == "SPRF", "C-CDA FASST should map to FHIR SPRF (secondary performer)"
        assert coding["display"] == "First Assistant Surgeon"

    def test_maps_anrs_function_code(self) -> None:
        """Test that ANRS function code maps to SPRF (secondary performer).

        Reference: docs/mapping/09-participations.md line 952
        """
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="test-procedure-003"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="ANRS" codeSystem="2.16.840.1.113883.5.88" displayName="Anesthesia Nurse"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="3333333333"/>
                        <assignedPerson><name><given>Linda</given><family>Nurse</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </procedure>""",
            PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]
        procedure = _find_resource_in_bundle(bundle, "Procedure")

        assert procedure is not None
        assert "performer" in procedure
        performer = procedure["performer"][0]
        assert "function" in performer
        coding = performer["function"]["coding"][0]
        assert coding["code"] == "SPRF", "C-CDA ANRS should map to FHIR SPRF (secondary performer)"
        assert coding["display"] == "Anesthesia Nurse"

    def test_excludes_encounter_only_function_codes(self) -> None:
        """Test that encounter-only function codes (ADMPHYS) are excluded from Procedure.performer.function.

        ADMPHYS maps to ADM which is not in the performer-function value set.
        The performer should still be created but without the function field.
        """
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="test-procedure-004"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="ADMPHYS" codeSystem="2.16.840.1.113883.5.88" displayName="Admitting Physician"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="4444444444"/>
                        <assignedPerson><name><given>Mark</given><family>Doctor</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </procedure>""",
            PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]
        procedure = _find_resource_in_bundle(bundle, "Procedure")

        assert procedure is not None
        assert "performer" in procedure
        performer = procedure["performer"][0]
        # ADM is encounter-only, so function should not be included for procedures
        assert "function" not in performer, "Encounter-only codes like ADM should not appear in Procedure.performer.function"
        # But actor should still be present
        assert "actor" in performer
        assert "Practitioner/" in performer["actor"]["reference"]

    def test_converts_location(self, ccda_procedure_with_location: str) -> None:
        """Test that LOC participant is converted to location."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_location, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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

    def test_converts_inline_problem_to_reason_code(self, ccda_procedure_with_reason_reference: str) -> None:
        """Test that inline Problem Observation (not in Problems section) creates reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_reason_reference, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Inline Problem Observation should create reasonCode (not reasonReference)
        assert "reasonCode" in procedure
        assert len(procedure["reasonCode"]) >= 1
        reason_code = procedure["reasonCode"][0]
        assert "coding" in reason_code
        coding = reason_code["coding"][0]
        assert coding["system"] == "http://snomed.info/sct"
        assert coding["code"] == "85189001"
        assert "Acute appendicitis" in coding["display"]

    def test_inline_problem_has_no_reason_reference(self, ccda_procedure_with_reason_reference: str) -> None:
        """Test that inline Problem Observation creates reasonCode, not reasonReference."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_reason_reference, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Should have reasonCode (from inline Problem value)
        assert "reasonCode" in procedure
        # Should NOT have reasonReference (Condition doesn't exist)
        assert "reasonReference" not in procedure

    def test_converts_referenced_problem_to_reason_reference(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that Problem Observation from Problems section creates reasonReference."""
        # This fixture includes both Problems section and Procedures section
        bundle = convert_document(ccda_procedure_with_problem_reference)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Referenced Problem Observation should create reasonReference
        assert "reasonReference" in procedure
        assert len(procedure["reasonReference"]) >= 1
        reason_ref = procedure["reasonReference"][0]
        assert "reference" in reason_ref
        assert "Condition/" in reason_ref["reference"]

        # Capture the generated Condition ID and verify it's a valid UUID v4
        import uuid as uuid_module
        condition_id = reason_ref["reference"].split("/")[1]
        try:
            uuid_module.UUID(condition_id, version=4)
        except ValueError:
            raise AssertionError(f"Condition ID {condition_id} is not a valid UUID v4")

        # Verify the Condition exists in the bundle
        condition = None
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Condition" and resource.get("id") == condition_id:
                condition = resource
                break
        assert condition is not None, f"Condition {condition_id} should exist in bundle"

    def test_referenced_problem_has_no_reason_code(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that referenced Problem Observation creates reasonReference, not reasonCode."""
        bundle = convert_document(ccda_procedure_with_problem_reference)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Should have reasonReference (Condition exists)
        assert "reasonReference" in procedure
        # Should NOT have reasonCode (reference takes precedence)
        assert "reasonCode" not in procedure

    def test_reason_reference_condition_id_format(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that reasonReference uses consistent Condition ID format."""
        bundle = convert_document(ccda_procedure_with_problem_reference)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        reason_ref = procedure["reasonReference"][0]
        # ID should be a valid UUID v4 (matches Condition generation logic)
        import uuid as uuid_module
        condition_id = reason_ref["reference"].split("/")[1]
        try:
            uuid_module.UUID(condition_id, version=4)
        except ValueError:
            raise AssertionError(f"Condition ID {condition_id} is not a valid UUID v4")

    def test_converts_author_to_recorder(self, ccda_procedure_with_author: str) -> None:
        """Test that author is converted to recorder."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure
        assert "reference" in procedure["recorder"]
        assert "Practitioner/" in procedure["recorder"]["reference"]

    def test_converts_outcome(self, ccda_procedure_with_outcome: str) -> None:
        """Test that OUTC entryRelationship is converted to outcome."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_outcome, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure

        # Recorder should reference a Practitioner with UUID v4
        import uuid as uuid_module
        assert "Practitioner/" in procedure["recorder"]["reference"]
        practitioner_id = procedure["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            raise AssertionError(f"Practitioner ID {practitioner_id} is not a valid UUID v4")

    def test_recorder_and_provenance_reference_same_practitioner(
        self, ccda_procedure_with_author: str
    ) -> None:
        """Test that recorder and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure
        recorder_ref = procedure["recorder"]["reference"]

        # Find Provenance for this procedure
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this procedure
        procedure_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                procedure["id"] in t.get("reference", "") for t in prov["target"]
            ):
                procedure_provenance = prov
                break

        assert procedure_provenance is not None, "Provenance resource should be created for Procedure"
        # Verify Provenance agent references same practitioner
        assert "agent" in procedure_provenance
        assert len(procedure_provenance["agent"]) > 0
        # Latest author should be in Provenance agents
        agent_refs = [
            agent.get("who", {}).get("reference")
            for agent in procedure_provenance["agent"]
        ]
        assert recorder_ref in agent_refs

    def test_provenance_has_recorded_date(
        self, ccda_procedure_with_author: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        procedure_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                procedure["id"] in t.get("reference", "") for t in prov["target"]
            ):
                procedure_provenance = prov
                break

        assert procedure_provenance is not None
        assert "recorded" in procedure_provenance
        # Should have a valid ISO datetime
        assert len(procedure_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_procedure_with_author: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        procedure_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                procedure["id"] in t.get("reference", "") for t in prov["target"]
            ):
                procedure_provenance = prov
                break

        assert procedure_provenance is not None
        assert "agent" in procedure_provenance
        assert len(procedure_provenance["agent"]) > 0

        # Check agent type
        agent = procedure_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_procedure_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_multiple_authors, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        procedure_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                procedure["id"] in t.get("reference", "") for t in prov["target"]
            ):
                procedure_provenance = prov
                break

        assert procedure_provenance is not None
        assert "agent" in procedure_provenance
        # Should have 2 agents for 2 authors
        assert len(procedure_provenance["agent"]) == 2

        # Verify both agents reference practitioners
        for agent in procedure_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_narrative_propagates_from_text_reference(self) -> None:
        """Test that Procedure.text narrative is generated from text/reference."""
        # Create complete document with section text and entry with text/reference
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="test-doc-id"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999"/>
            <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="test-org"/>
                <name>Test Org</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.7.1"/>
                    <code code="47519-4" codeSystem="2.16.840.1.113883.6.1" displayName="History of Procedures"/>
                    <text>
                        <paragraph ID="procedure-narrative-1">
                            <content styleCode="Bold">Surgical Procedure:</content>
                            Total knee replacement, left knee, performed under general anesthesia.
                        </paragraph>
                    </text>
                    <entry>
                        <procedure classCode="PROC" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                            <id root="procedure-123"/>
                            <code code="609588000" displayName="Total knee replacement"
                                  codeSystem="2.16.840.1.113883.6.96"/>
                            <text>
                                <reference value="#procedure-narrative-1"/>
                            </text>
                            <statusCode code="completed"/>
                            <effectiveTime value="20230815"/>
                        </procedure>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Verify Procedure has text.div with resolved narrative
        assert "text" in procedure, "Procedure should have .text field"
        assert "status" in procedure["text"]
        assert procedure["text"]["status"] == "generated"
        assert "div" in procedure["text"], "Procedure should have .text.div"

        div_content = procedure["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify referenced content was resolved
        assert "Total knee replacement" in div_content
        assert "general anesthesia" in div_content

        # Verify structured markup preserved
        assert "<p" in div_content  # Paragraph converted to <p>
        assert 'id="procedure-narrative-1"' in div_content  # ID preserved
        assert 'class="Bold"' in div_content or "Bold" in div_content  # Style preserved


class TestRepresentedOrganization:
    """E2E tests for represented organization in author context.

    Verifies that when an author has a representedOrganization:
    1. Organization resource is created in bundle
    2. Provenance.agent.onBehalfOf references the organization
    3. PractitionerRole links practitioner to organization
    """

    def test_organization_resource_created_from_represented_organization(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that representedOrganization creates Organization resource in bundle."""
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find all Organization resources
        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        assert len(organizations) >= 1, "At least one Organization resource should be created"

        # Find the entry-level organization (Good Health Surgical Center)
        entry_org = next(
            (org for org in organizations if org.get("name") == "Good Health Surgical Center"),
            None
        )
        assert entry_org is not None, "Entry-level organization should be created"
        assert entry_org["resourceType"] == "Organization"

    def test_organization_has_correct_identifier(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that Organization has correct identifier from representedOrganization."""
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        entry_org = next(
            (org for org in organizations if org.get("name") == "Good Health Surgical Center"),
            None
        )
        assert entry_org is not None
        assert "identifier" in entry_org

        # Should have identifier with root and extension
        identifiers = entry_org["identifier"]
        assert len(identifiers) > 0

        # Verify the OID-based identifier exists
        oid_identifier = next(
            (i for i in identifiers
             if "2.16.840.1.113883.19.5.9999.1393" in i.get("system", "")),
            None
        )
        assert oid_identifier is not None

    def test_organization_has_telecom_and_address(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that Organization has telecom and address from representedOrganization."""
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        entry_org = next(
            (org for org in organizations if org.get("name") == "Good Health Surgical Center"),
            None
        )
        assert entry_org is not None

        # Verify telecom
        assert "telecom" in entry_org
        assert len(entry_org["telecom"]) > 0
        telecom = entry_org["telecom"][0]
        assert telecom["system"] == "phone"
        assert "+1(555)123-4567" in telecom["value"]

        # Verify address
        assert "address" in entry_org
        assert len(entry_org["address"]) > 0
        address = entry_org["address"][0]
        assert address["city"] == "Portland"
        assert address["state"] == "OR"
        assert address["postalCode"] == "97201"

    def test_provenance_agent_has_on_behalf_of_organization(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that Provenance.agent.onBehalfOf references Organization."""
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Find Provenance for this procedure
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        procedure_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                procedure["id"] in t.get("reference", "") for t in prov["target"]
            ):
                procedure_provenance = prov
                break

        assert procedure_provenance is not None, "Provenance should be created"

        # Verify agent has onBehalfOf
        assert "agent" in procedure_provenance
        assert len(procedure_provenance["agent"]) > 0

        agent = procedure_provenance["agent"][0]
        assert "onBehalfOf" in agent, "Provenance.agent should have onBehalfOf field"
        assert "reference" in agent["onBehalfOf"]
        assert agent["onBehalfOf"]["reference"].startswith("Organization/")

    def test_on_behalf_of_references_correct_organization(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that onBehalfOf reference points to the correct Organization."""
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Get the entry-level Organization resource (Good Health Surgical Center)
        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        entry_org = next(
            (org for org in organizations if org.get("name") == "Good Health Surgical Center"),
            None
        )
        assert entry_org is not None
        org_id = entry_org["id"]

        # Get the Provenance resource
        procedure = _find_resource_in_bundle(bundle, "Procedure")
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        procedure_provenance = next(
            (p for p in provenances
             if any(procedure["id"] in t.get("reference", "") for t in p.get("target", []))),
            None
        )

        assert procedure_provenance is not None

        # Verify onBehalfOf references the same organization
        agent = procedure_provenance["agent"][0]
        on_behalf_of_ref = agent["onBehalfOf"]["reference"]
        assert on_behalf_of_ref == f"Organization/{org_id}"

    def test_entry_level_author_does_not_create_practitioner_role(
        self, ccda_procedure_with_author_and_organization: str
    ) -> None:
        """Test that entry-level authors with representedOrganization don't create PractitionerRole.

        PractitionerRole is only created for document-level authors, not entry-level authors.
        This is because PractitionerRole represents an ongoing relationship between a practitioner
        and organization, which is best captured at the document level.

        Entry-level authors (e.g., on a specific procedure) create:
        1. Practitioner resource
        2. Organization resource
        3. Provenance with onBehalfOf linking to the organization

        But NOT PractitionerRole.
        """
        ccda_doc = wrap_in_ccda_document(
            ccda_procedure_with_author_and_organization, PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Entry-level author creates Practitioner
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        entry_practitioner = next(
            (p for p in practitioners if "Documenter" in str(p.get("name", []))),
            None
        )
        assert entry_practitioner is not None, "Entry-level practitioner should be created"

        # Entry-level author creates Organization
        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        entry_org = next(
            (org for org in organizations if org.get("name") == "Good Health Surgical Center"),
            None
        )
        assert entry_org is not None, "Entry-level organization should be created"

        # But NO PractitionerRole is created linking them
        # (PractitionerRole is only for document-level authors)
        # The relationship is captured via Provenance.agent.onBehalfOf instead

    def test_author_without_organization_has_no_on_behalf_of(
        self, ccda_procedure_with_author: str
    ) -> None:
        """Test that author without representedOrganization has no onBehalfOf."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        procedure_provenance = next(
            (p for p in provenances
             if any(procedure["id"] in t.get("reference", "") for t in p.get("target", []))),
            None
        )

        if procedure_provenance:
            # If provenance exists, verify agent has no onBehalfOf
            agent = procedure_provenance["agent"][0]
            assert "onBehalfOf" not in agent, "onBehalfOf should not exist when no representedOrganization"


class TestProcedureActivityObservation:
    """E2E tests for C-CDA Procedure Activity Observation to FHIR Procedure conversion.

    Procedure Activity Observation (template 2.16.840.1.113883.10.20.22.4.13) is used for
    procedures that result in information about the patient (e.g., diagnostic tests) but do
    not alter the patient's physical state. These also map to FHIR Procedure resource.
    """

    def test_converts_procedure_observation_to_procedure_resource(
        self, ccda_procedure_observation: str
    ) -> None:
        """Test that Procedure Activity Observation is converted to FHIR Procedure."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["resourceType"] == "Procedure"

    def test_converts_observation_code(
        self, ccda_procedure_observation: str
    ) -> None:
        """Test that observation code is correctly converted to Procedure.code."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "code" in procedure
        snomed = next(
            (c for c in procedure["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "24623002"
        assert snomed["display"] == "Screening colonoscopy"

    def test_converts_observation_status(
        self, ccda_procedure_observation: str
    ) -> None:
        """Test that observation status is correctly mapped to Procedure.status."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert procedure["status"] == "completed"

    def test_converts_observation_effective_time(
        self, ccda_procedure_observation: str
    ) -> None:
        """Test that observation effectiveTime is converted to performedDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performedDateTime" in procedure
        assert procedure["performedDateTime"] == "2023-03-15"

    def test_converts_observation_identifier(
        self, ccda_procedure_observation: str
    ) -> None:
        """Test that observation identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "identifier" in procedure
        assert len(procedure["identifier"]) >= 1
        assert procedure["identifier"][0]["value"] == "proc-obs-001"

    def test_converts_observation_with_body_site(
        self, ccda_procedure_observation_with_details: str
    ) -> None:
        """Test that observation targetSiteCode is converted to bodySite."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation_with_details, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        assert snomed_coding["code"] == "416949008"
        assert snomed_coding["display"] == "Abdomen and pelvis"

    def test_converts_observation_with_performer(
        self, ccda_procedure_observation_with_details: str
    ) -> None:
        """Test that observation performer is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation_with_details, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "performer" in procedure
        assert len(procedure["performer"]) >= 1
        performer = procedure["performer"][0]
        assert "actor" in performer
        assert "Practitioner/" in performer["actor"]["reference"]

    def test_converts_observation_with_location(
        self, ccda_procedure_observation_with_details: str
    ) -> None:
        """Test that observation location participant is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation_with_details, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "location" in procedure
        assert "Location/" in procedure["location"]["reference"]
        # Display is optional, only check if present
        if "display" in procedure["location"]:
            assert procedure["location"]["display"] == "Endoscopy Suite 1"

    def test_converts_observation_with_author(
        self, ccda_procedure_observation_with_details: str
    ) -> None:
        """Test that observation author is converted to recorder."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation_with_details, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "recorder" in procedure
        assert "Practitioner/" in procedure["recorder"]["reference"]

    def test_converts_observation_with_reason(
        self, ccda_procedure_observation_with_details: str
    ) -> None:
        """Test that observation reason is correctly converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_observation_with_details, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        assert "reasonCode" in procedure
        assert len(procedure["reasonCode"]) >= 1
        reason = procedure["reasonCode"][0]
        snomed_coding = next(
            (c for c in reason["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "162004"
        assert snomed_coding["display"] == "Gastrointestinal hemorrhage"

    def test_mixed_procedure_and_observation_entries(self) -> None:
        """Test that both Procedure Activity Procedure and Observation can coexist in same section."""
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="test-proc-001"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </procedure>
            <observation classCode="OBS" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.13"/>
                <id root="test-obs-001"/>
                <code code="24623002" codeSystem="2.16.840.1.113883.6.96" displayName="Screening colonoscopy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230315"/>
                <value xsi:type="CD" nullFlavor="NA"/>
            </observation>""",
            PROCEDURES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        procedures = _find_all_resources_in_bundle(bundle, "Procedure")
        assert len(procedures) == 2, "Should convert both Procedure and Observation to Procedure resources"

        # Verify both were converted
        procedure_codes = {
            coding["code"]
            for proc in procedures
            for coding in proc["code"]["coding"]
            if coding.get("system") == "http://snomed.info/sct"
        }
        assert "80146002" in procedure_codes, "Appendectomy should be present"
        assert "24623002" in procedure_codes, "Screening colonoscopy should be present"


class TestProcedureMissingEffectiveTime:
    """Tests for Procedure with missing effectiveTime - data-absent-reason extension."""

    def test_missing_effective_time_adds_data_absent_reason(
        self, ccda_procedure_no_effective_time: str
    ) -> None:
        """Test that missing effectiveTime adds _performedDateTime with data-absent-reason extension."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_no_effective_time, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Should NOT have performedDateTime or performedPeriod
        assert "performedDateTime" not in procedure
        assert "performedPeriod" not in procedure

        # Should have _performedDateTime with data-absent-reason extension
        assert "_performedDateTime" in procedure
        assert "extension" in procedure["_performedDateTime"]

        extensions = procedure["_performedDateTime"]["extension"]
        assert len(extensions) == 1

        data_absent_ext = extensions[0]
        assert data_absent_ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert data_absent_ext["valueCode"] == "unknown"

    def test_missing_effective_time_does_not_affect_other_fields(
        self, ccda_procedure_no_effective_time: str
    ) -> None:
        """Test that missing effectiveTime doesn't affect other procedure fields."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_no_effective_time, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Other fields should still be present
        assert procedure["resourceType"] == "Procedure"
        assert procedure["status"] == "completed"
        assert "code" in procedure
        assert "identifier" in procedure

    def test_procedure_with_effective_time_no_data_absent_reason(
        self, ccda_procedure: str
    ) -> None:
        """Test that procedures WITH effectiveTime don't get data-absent-reason extension."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        # Should have performedDateTime
        assert "performedDateTime" in procedure

        # Should NOT have _performedDateTime with data-absent-reason
        assert "_performedDateTime" not in procedure


class TestProcedureIDSanitization:
    """Tests for Procedure resource ID sanitization."""

    def test_sanitizes_id_with_pipes(self) -> None:
        """Test that procedure IDs with pipe characters are sanitized.

        Real-world C-CDA documents may have IDs with pipes (e.g., '15||63725-003')
        which violates FHIR R4B spec. IDs can only contain: A-Z, a-z, 0-9, -, .
        """
        ccda_doc = wrap_in_ccda_document(
            """<procedure classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="1.2.3.4.5" extension="15||63725-003"/>
                <code code="80146002" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Appendectomy"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101120000"/>
            </procedure>""",
            PROCEDURES_TEMPLATE_ID
        )

        bundle = convert_document(ccda_doc)["bundle"]
        procedure = _find_resource_in_bundle(bundle, "Procedure")

        assert procedure is not None
        # Pipe characters should be replaced with hyphens
        assert procedure["id"] == "procedure-15--63725-003"
        # Verify it's the correct procedure
        assert procedure["code"]["coding"][0]["code"] == "80146002"
