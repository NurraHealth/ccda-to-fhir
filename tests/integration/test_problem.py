"""E2E tests for Condition resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "clinicalStatus" in condition
        assert condition["clinicalStatus"]["coding"][0]["code"] == "recurrence"

    def test_converts_category(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that category is set to problem-list-item."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "category" in condition
        assert condition["category"][0]["coding"][0]["code"] == "problem-list-item"

    def test_converts_onset_date(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that onset date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "onsetDateTime" in condition
        assert condition["onsetDateTime"] == "2012-08-06"

    def test_converts_onset_age(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that age at onset is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "onsetAge" in condition
        assert condition["onsetAge"]["value"] == 65
        assert condition["onsetAge"]["unit"] == "year"

    def test_converts_recorded_date(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that author time is converted to recordedDate."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recordedDate" in condition
        assert condition["recordedDate"] == "2014-01-04"

    def test_converts_icd_translations(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that ICD-9 and ICD-10 translations are included."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "identifier" in condition
        assert condition["identifier"][0]["value"] == "545069300001"

    def test_resource_type_is_condition(
        self, ccda_problem: str, fhir_problem: JSONObject) -> None:
        """Test that the resource type is Condition."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert condition["resourceType"] == "Condition"

    def test_converts_abatement_date(self, ccda_condition_with_abatement: str) -> None:
        """Test that effectiveTime high is converted to abatementDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_abatement, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "abatementDateTime" in condition
        assert condition["abatementDateTime"] == "2020-03-20"

    def test_converts_body_site(self, ccda_condition_with_body_site: str) -> None:
        """Test that targetSiteCode is converted to bodySite."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_body_site, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "verificationStatus" in condition
        assert condition["verificationStatus"]["coding"][0]["code"] == "refuted"
        assert (
            condition["verificationStatus"]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/condition-ver-status"
        )

    def test_converts_asserted_date_extension(
        self, ccda_condition_with_asserted_date: str
    ) -> None:
        """Test that Date of Diagnosis Act is converted to assertedDate extension."""
        ccda_doc = wrap_in_ccda_document(ccda_condition_with_asserted_date, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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

    def test_converts_recorder_from_latest_author(
        self, ccda_problem: str, fhir_problem: JSONObject
    ) -> None:
        """Test that recorder field is populated from latest author."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recorder" in condition
        assert "reference" in condition["recorder"]
        assert condition["recorder"]["reference"].startswith("Practitioner/")
        # Verify the practitioner ID matches the author's extension (99999999)
        assert "99999999" in condition["recorder"]["reference"]

    def test_recorder_and_provenance_reference_same_practitioner(
        self, ccda_problem: str
    ) -> None:
        """Test that recorder and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_problem, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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

    def test_multiple_authors_selects_latest_for_recorder(
        self, ccda_problem_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for recorder field."""
        ccda_doc = wrap_in_ccda_document(ccda_problem_multiple_authors, PROBLEMS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        condition = _find_resource_in_bundle(bundle, "Condition")
        assert condition is not None
        assert "recorder" in condition

        # Latest author is LATEST-DOC-789 (time: 20231215) from observation authors
        # Not EARLY-DOC-123 (concern act, time: 20230101) or MIDDLE-DOC-456 (time: 20230615)
        assert "LATEST-DOC-789" in condition["recorder"]["reference"]
        assert "EARLY-DOC-123" not in condition["recorder"]["reference"]
        assert "MIDDLE-DOC-456" not in condition["recorder"]["reference"]

        # recordedDate uses earliest observation author time (not concern act author)
        # So it's 2023-06-15 (MIDDLE-DOC-456), not 2023-01-01 (EARLY-DOC-123 from concern act)
        assert condition["recordedDate"] == "2023-06-15"
