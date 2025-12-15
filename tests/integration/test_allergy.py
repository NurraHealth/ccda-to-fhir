"""E2E tests for AllergyIntolerance resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestAllergyConversion:
    """E2E tests for C-CDA Allergy Concern Act to FHIR AllergyIntolerance conversion."""

    def test_converts_allergy_code(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that the allergen code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "code" in allergy
        rxnorm_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm_coding is not None
        assert rxnorm_coding["code"] == "1191"
        assert rxnorm_coding["display"] == "Aspirin"

    def test_converts_clinical_status(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that clinical status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "clinicalStatus" in allergy
        assert allergy["clinicalStatus"]["coding"][0]["code"] == "active"
        assert allergy["clinicalStatus"]["coding"][0]["system"] == \
            "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"

    def test_converts_category(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that category is correctly determined."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "category" in allergy
        assert "medication" in allergy["category"]

    def test_converts_onset_date(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that onset date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "onsetDateTime" in allergy
        assert allergy["onsetDateTime"] == "2008-05-01"

    def test_converts_reaction_manifestation(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that reaction manifestation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) >= 1
        reaction = allergy["reaction"][0]
        assert "manifestation" in reaction

        snomed_coding = next(
            (c for c in reaction["manifestation"][0]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "247472004"
        assert snomed_coding["display"] == "Wheal"

    def test_converts_reaction_severity(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that reaction severity is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        reaction = allergy["reaction"][0]
        assert reaction["severity"] == "severe"

    def test_converts_identifiers(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "identifier" in allergy
        assert len(allergy["identifier"]) >= 1

    def test_converts_translation_codes(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that translation codes are included in code.coding."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "code" in allergy
        snomed_coding = next(
            (c for c in allergy["code"]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "293586001"

    def test_resource_type_is_allergy_intolerance(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that the resource type is AllergyIntolerance."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert allergy["resourceType"] == "AllergyIntolerance"

    def test_converts_type_field(self, ccda_allergy_with_type: str) -> None:
        """Test that observation value code is converted to type field (allergy vs intolerance)."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_type, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "type" in allergy
        assert allergy["type"] == "intolerance"

    def test_converts_verification_status_confirmed(
        self, ccda_allergy_with_verification_status: str
    ) -> None:
        """Test that non-negated allergies have verificationStatus=confirmed."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_verification_status, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "verificationStatus" in allergy
        assert allergy["verificationStatus"]["coding"][0]["code"] == "confirmed"
        assert (
            allergy["verificationStatus"]["coding"][0]["system"]
            == "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification"
        )

    def test_converts_criticality(self, ccda_allergy_with_criticality: str) -> None:
        """Test that Criticality Observation is converted to criticality field."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_criticality, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "criticality" in allergy
        assert allergy["criticality"] == "high"

    def test_converts_abatement_extension(self, ccda_allergy_with_abatement: str) -> None:
        """Test that effectiveTime/high is converted to allergyintolerance-abatement extension."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_abatement, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "extension" in allergy
        abatement_ext = next(
            (e for e in allergy["extension"]
             if e.get("url") == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-abatement"),
            None
        )
        assert abatement_ext is not None
        assert abatement_ext["valueDateTime"] == "2023-09-10"

    def test_converts_recorded_date(self, ccda_allergy_with_recorded_date: str) -> None:
        """Test that author/time is converted to recordedDate."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_recorded_date, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recordedDate" in allergy
        assert "2023-10-15" in allergy["recordedDate"]

    def test_converts_comment_activity_to_note(
        self, ccda_allergy_with_comment: str
    ) -> None:
        """Test that Comment Activity is converted to note."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_comment, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "note" in allergy
        assert len(allergy["note"]) == 1
        assert "severe nausea and vomiting" in allergy["note"][0]["text"]

    def test_converts_recorder_from_latest_author(
        self, ccda_allergy_with_recorded_date: str
    ) -> None:
        """Test that recorder field is populated from latest author."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_recorded_date, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recorder" in allergy
        assert "reference" in allergy["recorder"]
        assert allergy["recorder"]["reference"].startswith("Practitioner/")

    def test_recorder_and_provenance_reference_same_practitioner(
        self, ccda_allergy_with_recorded_date: str
    ) -> None:
        """Test that recorder and Provenance both reference the same Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_recorded_date, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recorder" in allergy
        recorder_ref = allergy["recorder"]["reference"]

        # Find Provenance for this allergy
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this allergy
        allergy_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                allergy["id"] in t.get("reference", "") for t in prov["target"]
            ):
                allergy_provenance = prov
                break

        assert allergy_provenance is not None
        # Verify Provenance agent references same practitioner
        assert "agent" in allergy_provenance
        assert len(allergy_provenance["agent"]) > 0
        # Latest author should be in Provenance agents
        agent_refs = [
            agent.get("who", {}).get("reference")
            for agent in allergy_provenance["agent"]
        ]
        assert recorder_ref in agent_refs

    def test_multiple_authors_selects_latest_for_recorder(
        self, ccda_allergy_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for recorder field."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_multiple_authors, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recorder" in allergy

        # Latest author is LATEST-ALLERGY-DOC (time: 20231120)
        # Not EARLY-ALLERGY-DOC (time: 20230301)
        assert "LATEST-ALLERGY-DOC" in allergy["recorder"]["reference"]
        assert "EARLY-ALLERGY-DOC" not in allergy["recorder"]["reference"]

        # recordedDate should still use earliest time
        assert allergy["recordedDate"] == "2023-03-01"
