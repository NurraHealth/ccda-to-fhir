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

    def test_converts_inline_problem_to_reason_code(self, ccda_procedure_with_reason_reference: str) -> None:
        """Test that inline Problem Observation (not in Problems section) creates reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_reason_reference, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Should have reasonCode (from inline Problem value)
        assert "reasonCode" in procedure
        # Should NOT have reasonReference (Condition doesn't exist)
        assert "reasonReference" not in procedure

    def test_converts_referenced_problem_to_reason_reference(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that Problem Observation from Problems section creates reasonReference."""
        # This fixture includes both Problems section and Procedures section
        bundle = convert_document(ccda_procedure_with_problem_reference)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Referenced Problem Observation should create reasonReference
        assert "reasonReference" in procedure
        assert len(procedure["reasonReference"]) >= 1
        reason_ref = procedure["reasonReference"][0]
        assert "reference" in reason_ref
        assert "Condition/" in reason_ref["reference"]
        # Should reference the Condition created from Problems section
        assert "condition-problem-appendicitis-001" in reason_ref["reference"]

    def test_referenced_problem_has_no_reason_code(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that referenced Problem Observation creates reasonReference, not reasonCode."""
        bundle = convert_document(ccda_procedure_with_problem_reference)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None
        # Should have reasonReference (Condition exists)
        assert "reasonReference" in procedure
        # Should NOT have reasonCode (reference takes precedence)
        assert "reasonCode" not in procedure

    def test_reason_reference_condition_id_format(self, ccda_procedure_with_problem_reference: str) -> None:
        """Test that reasonReference uses consistent Condition ID format."""
        bundle = convert_document(ccda_procedure_with_problem_reference)

        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None

        reason_ref = procedure["reasonReference"][0]
        # ID should match condition.py generation logic: condition-{extension}
        assert reason_ref["reference"] == "Condition/condition-problem-appendicitis-001"

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

    def test_recorder_and_provenance_reference_same_practitioner(
        self, ccda_procedure_with_author: str
    ) -> None:
        """Test that recorder and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_procedure_with_author, PROCEDURES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
