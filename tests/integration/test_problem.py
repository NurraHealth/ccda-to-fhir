"""E2E tests for Condition resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

PROBLEMS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.5.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestProblemConversion:
    """E2E tests for C-CDA Problem Concern Act to FHIR Condition conversion."""

    def test_converts_problem_code(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that the problem code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "code" in condition
        snomed = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "233604007"
        assert snomed["display"] == "Pneumonia"

    def test_converts_clinical_status(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that clinical status is correctly mapped from status observation."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "clinicalStatus" in condition
        assert condition["clinicalStatus"]["coding"][0]["code"] == "recurrence"

    def test_converts_category(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that category is set to problem-list-item."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "category" in condition
        assert condition["category"][0]["coding"][0]["code"] == "problem-list-item"

    def test_converts_secondary_category_from_problem_type(
        self, ccda_problem_with_diagnosis_type: str
    ) -> None:
        """Test that problem type code (282291009=Diagnosis) creates secondary category.

        When a problem appears in the Problem List section (maps to problem-list-item)
        but has a problem type code of 282291009 (Diagnosis, maps to encounter-diagnosis),
        the Condition should have two categories:
        1. problem-list-item (from section)
        2. encounter-diagnosis (from problem type code)
        """
        ccda_doc = wrap_in_ccda_document(ccda_problem_with_diagnosis_type, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "category" in condition

        # Should have two categories
        assert len(condition["category"]) == 2

        # Extract category codes
        category_codes = [
            cat["coding"][0]["code"]
            for cat in condition["category"]
        ]

        # Should contain both problem-list-item (from section) and encounter-diagnosis (from problem type)
        assert "problem-list-item" in category_codes
        assert "encounter-diagnosis" in category_codes

        # Verify system for both categories
        for cat in condition["category"]:
            assert cat["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/condition-category"

    def test_converts_onset_date(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that onset is correctly converted (prioritizes age over date per choice type logic)."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        # Fixture contains both age and date; converter correctly prioritizes age
        assert "onsetAge" in condition
        assert condition["onsetAge"]["value"] == 65

    def test_converts_onset_age(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that age at onset is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "onsetAge" in condition
        assert condition["onsetAge"]["value"] == 65
        assert condition["onsetAge"]["unit"] == "year"

    def test_converts_recorded_date(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that author time is converted to recordedDate."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recordedDate" in condition
        assert condition["recordedDate"] == "2014-01-04"

    def test_converts_icd_translations(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that ICD-9 and ICD-10 translations are included."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "code" in condition
        icd9 = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-9-cm"),
            None
        )
        assert icd9 is not None
        assert icd9["code"] == "486"

        icd10 = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"),
            None
        )
        assert icd10 is not None
        assert icd10["code"] == "J18.9"

    def test_converts_identifiers(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "identifier" in condition
        assert condition["identifier"][0]["value"] == "545069300001"

    def test_resource_type_is_condition(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that the resource type is Condition."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert condition["resourceType"] == "Condition"

    def test_converts_abatement_date(self, ccda_condition_with_abatement: str) -> None:
        """Test that effectiveTime with low and high is converted to onsetPeriod (per choice type priority)."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_abatement, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        # Fixture contains effectiveTime with both low and high; converter correctly uses onsetPeriod
        assert "onsetPeriod" in condition
        assert condition["onsetPeriod"]["start"] == "2020-01-15"
        assert condition["onsetPeriod"]["end"] == "2020-03-20"

    def test_converts_abatement_unknown_with_data_absent_reason(
        self, ccda_condition_with_abatement_unknown: str
    ) -> None:
        """Test that effectiveTime high with nullFlavor=UNK is converted to _abatementDateTime with data-absent-reason.

        Per C-CDA on FHIR IG and FHIR R4 spec, when the abatement date is unknown but
        the condition is resolved, use the _abatementDateTime element with a
        data-absent-reason extension (valueCode: "unknown").

        Reference: http://hl7.org/fhir/extension-data-absent-reason.html
        """
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_abatement_unknown, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Should NOT have regular abatementDateTime
        assert "abatementDateTime" not in condition

        # Should have _abatementDateTime with data-absent-reason extension
        assert "_abatementDateTime" in condition
        assert "extension" in condition["_abatementDateTime"]

        extensions = condition["_abatementDateTime"]["extension"]
        assert len(extensions) == 1

        data_absent_ext = extensions[0]
        assert data_absent_ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert data_absent_ext["valueCode"] == "unknown"

        # Should have resolved clinical status (per C-CDA on FHIR IG constraint)
        assert "clinicalStatus" in condition
        assert condition["clinicalStatus"]["coding"][0]["code"] == "resolved"

    def test_converts_body_site(self, ccda_condition_with_body_site: str) -> None:
        """Test that targetSiteCode is converted to bodySite."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_body_site, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "bodySite" in condition
        assert len(condition["bodySite"]) == 1
        snomed = next(
            (c for c in condition["bodySite"][0]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "368209003"
        assert snomed["display"] == "Right arm"

    def test_converts_severity(self, ccda_condition_with_severity: str) -> None:
        """Test that Severity Observation is converted to severity."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_severity, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "severity" in condition
        snomed = next(
            (c for c in condition["severity"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "24484000"
        assert snomed["display"] == "Severe"

    def test_converts_note_from_text(self, ccda_condition_with_note: str) -> None:
        """Test that observation.text is converted to note."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_note, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "note" in condition
        assert len(condition["note"]) == 1
        assert condition["note"][0]["text"] == "Patient reports worsening symptoms at night"

    def test_converts_negation_ind_to_verification_status(
        self, ccda_condition_negated: str
    ) -> None:
        """Test that negationInd=true is converted to verificationStatus=refuted."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_negated, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "verificationStatus" in condition
        assert condition["verificationStatus"]["coding"][0]["code"] == "refuted"
        assert (
            condition["verificationStatus"]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/condition-ver-status"
        )

    def test_converts_no_known_problems_to_negated_concept_code(
        self, ccda_problem_no_known_problems: str
    ) -> None:
        """Test that negationInd=true with generic problem code maps to negated concept.

        When negationInd="true" is combined with a generic problem code (55607006, 404684003,
        or 64572001), the converter should use SNOMED CT negated concept code 160245001
        "No current problems or disability" instead of setting verificationStatus=refuted.

        This follows FHIR best practice for representing "no known problems" scenarios.
        """
        ccda_doc = wrap_in_ccda_document(ccda_problem_no_known_problems, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Should NOT have verificationStatus=refuted
        assert "verificationStatus" not in condition

        # Should have negated concept code
        assert "code" in condition
        snomed_coding = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "160245001"
        assert "No current problems" in snomed_coding.get("display", "")

    def test_converts_asserted_date_extension(
        self, ccda_condition_with_asserted_date: str
    ) -> None:
        """Test that Date of Diagnosis Act is converted to assertedDate extension."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_asserted_date, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "extension" in condition
        asserted_ext = next(
            (e for e in condition["extension"]
             if e.get("url") == "http://hl7.org/fhir/StructureDefinition/condition-assertedDate"),
            None
        )
        assert asserted_ext is not None
        assert asserted_ext["valueDateTime"] == "2019-02-20"

    def test_converts_comment_activity_to_note(
        self, ccda_condition_with_comment: str
    ) -> None:
        """Test that Comment Activity is converted to note."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_comment, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "note" in condition
        assert len(condition["note"]) == 1
        assert "Patient reports chest pain on exertion" in condition["note"][0]["text"]

    def test_converts_supporting_observations_to_evidence(
        self, ccda_condition_with_evidence: str
    ) -> None:
        """Test that supporting observations (typeCode=SPRT) are converted to evidence.detail."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_evidence, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "evidence" in condition
        assert len(condition["evidence"]) == 1
        assert "detail" in condition["evidence"][0]
        assert len(condition["evidence"][0]["detail"]) == 1
        # Verify the reference points to an Observation resource
        reference = condition["evidence"][0]["detail"][0]["reference"]
        assert reference.startswith("Observation/")
        assert "lab-result-tsh-001" in reference

    def test_converts_assessment_scale_observations_to_evidence(
        self, ccda_condition_with_assessment_scale: str
    ) -> None:
        """Test that assessment scale observations (typeCode=COMP) are converted to evidence.detail.

        Assessment Scale Observations (template 2.16.840.1.113883.10.20.22.4.69) provide
        structured evaluations (e.g., PHQ-9 depression screening, Glasgow coma scale) that
        support the diagnosis and should be referenced in Condition.evidence.detail.

        Per C-CDA on FHIR IG and FHIR R4 spec, these observations are converted to FHIR
        Observation resources and referenced to provide supporting evidence for conditions.
        """
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_assessment_scale, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "evidence" in condition, "Condition should have evidence from assessment scale"
        assert len(condition["evidence"]) == 1
        assert "detail" in condition["evidence"][0]
        assert len(condition["evidence"][0]["detail"]) == 1

        # Verify the reference points to an Observation resource
        reference = condition["evidence"][0]["detail"][0]["reference"]
        assert reference.startswith("Observation/")
        assert "assessment-phq9-001" in reference, "Should reference the PHQ-9 assessment observation"

    def test_converts_recorder_from_latest_author(
        self, ccda_problem: str, fhir_problem: JSONObject
    ) -> None:
        """Test that recorder field is populated from latest author."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recorder" in condition
        assert "reference" in condition["recorder"]
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Verify the practitioner ID is a valid UUID v4
        import uuid as uuid_module
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            raise AssertionError(f"Practitioner ID {practitioner_id} is not a valid UUID v4")

    def test_recorder_and_provenance_reference_same_practitioner(
        self, ccda_problem: str
    ) -> None:
        """Test that recorder and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recorder" in condition
        recorder_ref = condition["recorder"]["reference"]

        # Find Provenance for this condition
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this condition
        condition_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                condition["id"] in t.get("reference", "") for t in prov["target"]
            ):
                condition_provenance = prov
                break

        assert condition_provenance is not None
        # Verify Provenance agent references same practitioner
        assert "agent" in condition_provenance
        assert len(condition_provenance["agent"]) > 0
        # Latest author should be in Provenance agents
        agent_refs = [
            agent.get("who", {}).get("reference")
            for agent in condition_provenance["agent"]
        ]
        assert recorder_ref in agent_refs

    def test_provenance_has_recorded_date(
        self, ccda_problem: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        condition_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                condition["id"] in t.get("reference", "") for t in prov["target"]
            ):
                condition_provenance = prov
                break

        assert condition_provenance is not None
        assert "recorded" in condition_provenance
        # Should have a valid ISO datetime
        assert len(condition_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_problem: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        condition_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                condition["id"] in t.get("reference", "") for t in prov["target"]
            ):
                condition_provenance = prov
                break

        assert condition_provenance is not None
        assert "agent" in condition_provenance
        assert len(condition_provenance["agent"]) > 0

        # Check agent type
        agent = condition_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_problem_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_problem_multiple_authors, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        condition_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                condition["id"] in t.get("reference", "") for t in prov["target"]
            ):
                condition_provenance = prov
                break

        assert condition_provenance is not None
        assert "agent" in condition_provenance
        # Should have 3 agents: 1 from concern act + 2 from observation
        assert len(condition_provenance["agent"]) == 3

        # Verify all agents reference practitioners
        for agent in condition_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_multiple_authors_selects_latest_for_recorder(
        self, ccda_problem_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for recorder field."""
        ccda_doc = wrap_in_ccda_document(ccda_problem_multiple_authors, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recorder" in condition

        # Recorder should reference a Practitioner with UUID v4 ID
        import uuid as uuid_module
        assert "Practitioner/" in condition["recorder"]["reference"]
        practitioner_id = condition["recorder"]["reference"].split("/")[1]
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            raise AssertionError(f"Practitioner ID {practitioner_id} is not a valid UUID v4")

        # recordedDate uses earliest observation author time (not concern act author)
        # So it's 2023-06-15 (MIDDLE-DOC-456), not 2023-01-01 (EARLY-DOC-123 from concern act)
        assert condition["recordedDate"] == "2023-06-15"

    def test_narrative_propagates_from_text_reference(self) -> None:
        """Test that Condition.text narrative is generated from text/reference."""
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <text>
                        <paragraph ID="problem-narrative-1">
                            <content styleCode="Bold">Active Problem:</content>
                            Type 2 Diabetes Mellitus, diagnosed 2020, managed with metformin.
                        </paragraph>
                    </text>
                    <entry>
                        <act classCode="ACT" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                            <id root="problem-concern-123"/>
                            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20200115"/>
                            </effectiveTime>
                            <entryRelationship typeCode="SUBJ">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                                    <id root="problem-obs-456"/>
                                    <code code="55607006" displayName="Problem" codeSystem="2.16.840.1.113883.6.96"/>
                                    <text>
                                        <reference value="#problem-narrative-1"/>
                                    </text>
                                    <statusCode code="completed"/>
                                    <effectiveTime>
                                        <low value="20200115"/>
                                    </effectiveTime>
                                    <value xsi:type="CD" code="44054006" displayName="Type 2 Diabetes Mellitus"
                                           codeSystem="2.16.840.1.113883.6.96"/>
                                </observation>
                            </entryRelationship>
                        </act>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)["bundle"]

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None

        # Verify Condition has text.div with resolved narrative
        assert "text" in condition, "Condition should have .text field"
        assert "status" in condition["text"]
        assert condition["text"]["status"] == "generated"
        assert "div" in condition["text"], "Condition should have .text.div"

        div_content = condition["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify referenced content was resolved
        assert "Type 2 Diabetes Mellitus" in div_content
        assert "metformin" in div_content

        # Verify structured markup preserved
        assert "<p" in div_content  # Paragraph converted to <p>
        assert 'id="problem-narrative-1"' in div_content  # ID preserved
        assert 'class="Bold"' in div_content or "Bold" in div_content  # Style preserved


class TestCodeWhitespaceSanitization:
    """Tests for code whitespace sanitization in CodeableConcept conversion."""

    def test_sanitizes_code_with_leading_whitespace(self) -> None:
        r"""Test that codes with leading whitespace are sanitized.

        Real-world C-CDA documents may have codes with leading/trailing whitespace
        (e.g., ' R50.9' from MDIntellisys IntelleChart). FHIR requires codes match
        pattern '^[^\s]+(\s[^\s]+)*$' (no leading/trailing whitespace).
        """
        ccda_doc = wrap_in_ccda_document(
            """<act classCode="ACT" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
                <id root="1.2.3.4.5" extension="problem-123"/>
                <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                <statusCode code="active"/>
                <effectiveTime>
                    <low value="20230101"/>
                </effectiveTime>
                <entryRelationship typeCode="SUBJ">
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                        <id root="1.2.3.4.5" extension="obs-123"/>
                        <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                        <statusCode code="completed"/>
                        <effectiveTime>
                            <low value="20230101"/>
                        </effectiveTime>
                        <value xsi:type="CD" code=" R50.9" codeSystem="2.16.840.1.113883.6.90"
                               displayName=" Fever, unspecified " codeSystemName="ICD-10-CM"/>
                    </observation>
                </entryRelationship>
            </act>""",
            PROBLEMS_TEMPLATE_ID
        )

        bundle = convert_document(ccda_doc)["bundle"]
        condition = _find_resource_in_bundle(bundle, "Condition")

        assert condition is not None
        assert "code" in condition

        # Find ICD-10-CM coding
        icd10_coding = next(
            (c for c in condition["code"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/icd-10-cm"),
            None
        )

        assert icd10_coding is not None
        # Code should be sanitized (leading space removed)
        assert icd10_coding["code"] == "R50.9", f"Expected 'R50.9' but got '{icd10_coding['code']}'"
        # Display name should be sanitized (leading/trailing spaces removed)
        assert icd10_coding["display"] == "Fever, unspecified", f"Expected 'Fever, unspecified' but got '{icd10_coding['display']}'"
