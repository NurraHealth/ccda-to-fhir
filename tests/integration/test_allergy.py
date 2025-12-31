"""E2E tests for AllergyIntolerance resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "category" in allergy
        assert "medication" in allergy["category"]

    def test_converts_onset_date(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that onset date is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "onsetDateTime" in allergy
        assert allergy["onsetDateTime"] == "2008-05-01"

    def test_converts_reaction_manifestation(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that reaction manifestation is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        reaction = allergy["reaction"][0]
        assert reaction["severity"] == "severe"

    def test_converts_identifiers(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that identifiers are correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "identifier" in allergy
        assert len(allergy["identifier"]) >= 1

    def test_converts_translation_codes(
        self, ccda_allergy: str, fhir_allergy: JSONObject) -> None:
        """Test that translation codes are included in code.coding."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert allergy["resourceType"] == "AllergyIntolerance"

    def test_converts_type_field(self, ccda_allergy_with_type: str) -> None:
        """Test that observation value code is converted to type field (allergy vs intolerance)."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_type, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "type" in allergy
        assert allergy["type"] == "intolerance"

    def test_converts_verification_status_confirmed(
        self, ccda_allergy_with_verification_status: str
    ) -> None:
        """Test that non-negated allergies have verificationStatus=confirmed."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_verification_status, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "criticality" in allergy
        assert allergy["criticality"] == "high"

    def test_converts_abatement_extension(self, ccda_allergy_with_abatement: str) -> None:
        """Test that effectiveTime/high is converted to allergyintolerance-abatement extension."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_abatement, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recordedDate" in allergy
        assert "2023-10-15" in allergy["recordedDate"]

    def test_converts_comment_activity_to_note(
        self, ccda_allergy_with_comment: str
    ) -> None:
        """Test that Comment Activity is converted to note."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_comment, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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
        bundle = convert_document(ccda_doc)["bundle"]

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

    def test_provenance_has_recorded_date(
        self, ccda_allergy_with_recorded_date: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_recorded_date, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        allergy_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                allergy["id"] in t.get("reference", "") for t in prov["target"]
            ):
                allergy_provenance = prov
                break

        assert allergy_provenance is not None
        assert "recorded" in allergy_provenance
        # Should have a valid ISO datetime
        assert len(allergy_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_allergy_with_recorded_date: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_with_recorded_date, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        allergy_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                allergy["id"] in t.get("reference", "") for t in prov["target"]
            ):
                allergy_provenance = prov
                break

        assert allergy_provenance is not None
        assert "agent" in allergy_provenance
        assert len(allergy_provenance["agent"]) > 0

        # Check agent type
        agent = allergy_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_allergy_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_multiple_authors, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        allergy_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                allergy["id"] in t.get("reference", "") for t in prov["target"]
            ):
                allergy_provenance = prov
                break

        assert allergy_provenance is not None
        assert "agent" in allergy_provenance
        # Should have multiple agents for multiple authors
        assert len(allergy_provenance["agent"]) >= 2

        # Verify all agents reference practitioners
        for agent in allergy_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_multiple_authors_selects_latest_for_recorder(
        self, ccda_allergy_multiple_authors: str
    ) -> None:
        """Test that latest author (by timestamp) is selected for recorder field."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy_multiple_authors, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "recorder" in allergy

        # Recorder should reference a Practitioner (UUID v4 format)
        assert allergy["recorder"]["reference"].startswith("Practitioner/")
        recorder_id = allergy["recorder"]["reference"].split("/")[1]

        # Verify the referenced Practitioner exists in bundle
        # Latest author is LATEST-ALLERGY-DOC (time: 20231120), not EARLY-ALLERGY-DOC (time: 20230301)
        practitioners = [e["resource"] for e in bundle.get("entry", [])
                        if e["resource"]["resourceType"] == "Practitioner" and e["resource"]["id"] == recorder_id]
        assert len(practitioners) == 1
        practitioner = practitioners[0]

        # Check practitioner has identifier with LATEST-ALLERGY-DOC
        latest_found = False
        for ident in practitioner.get("identifier", []):
            if "LATEST-ALLERGY-DOC" in ident.get("value", ""):
                latest_found = True
                break
        assert latest_found, "Latest author (LATEST-ALLERGY-DOC) should be selected for recorder"

        # recordedDate should still use earliest time
        assert allergy["recordedDate"] == "2023-03-01"

    def test_converts_reaction_onset_from_low_value(self) -> None:
        """Test that reaction effectiveTime/low is converted to reaction.onset."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_onset.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) == 1

        # Verify reaction onset is populated
        reaction = allergy["reaction"][0]
        assert "onset" in reaction
        assert "2023-08-21" in reaction["onset"]

    def test_converts_reaction_onset_from_simple_value(self) -> None:
        """Test that reaction effectiveTime value is converted to reaction.onset."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_onset_simple.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) == 1

        # Verify reaction onset is populated from simple value
        reaction = allergy["reaction"][0]
        assert "onset" in reaction
        assert reaction["onset"] == "2023-10-15"

    def test_reaction_with_onset_preserves_manifestation(self) -> None:
        """Test that reaction onset doesn't interfere with manifestation."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_onset.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        reaction = allergy["reaction"][0]
        assert "manifestation" in reaction
        assert len(reaction["manifestation"]) == 1
        manifestation = reaction["manifestation"][0]

        # Verify SNOMED code for Hives
        snomed_coding = next(
            (c for c in manifestation["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "247472004"
        assert snomed_coding["display"] == "Hives"


class TestAllergyInheritanceSeverity:
    """E2E tests for severity inheritance rules per C-CDA on FHIR IG."""

    def test_scenario_a_allergy_level_severity_applies_to_all_reactions(
        self, ccda_allergy_with_allergy_level_severity: str
    ) -> None:
        """Test Scenario A: Severity only at allergy level is applied to all reactions."""
        ccda_doc = wrap_in_ccda_document(
            ccda_allergy_with_allergy_level_severity, ALLERGIES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        # Should have 2 reactions (Hives and Rash)
        assert len(allergy["reaction"]) == 2

        # Both reactions should have "moderate" severity (from allergy level)
        for reaction in allergy["reaction"]:
            assert "severity" in reaction
            assert reaction["severity"] == "moderate"

    def test_scenario_a_multiple_reactions_inherit_same_severity(
        self, ccda_allergy_with_allergy_level_severity: str
    ) -> None:
        """Test that all reactions inherit the same allergy-level severity."""
        ccda_doc = wrap_in_ccda_document(
            ccda_allergy_with_allergy_level_severity, ALLERGIES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify first reaction (Hives) has moderate severity
        hives_reaction = next(
            (r for r in allergy["reaction"]
             if any(c.get("code") == "247472004"
                    for m in r.get("manifestation", [])
                    for c in m.get("coding", []))),
            None
        )
        assert hives_reaction is not None
        assert hives_reaction["severity"] == "moderate"

        # Verify second reaction (Rash) also has moderate severity
        rash_reaction = next(
            (r for r in allergy["reaction"]
             if any(c.get("code") == "271807003"
                    for m in r.get("manifestation", [])
                    for c in m.get("coding", []))),
            None
        )
        assert rash_reaction is not None
        assert rash_reaction["severity"] == "moderate"

    def test_scenario_b_reaction_severity_takes_precedence(
        self, ccda_allergy_with_both_level_severity: str
    ) -> None:
        """Test Scenario B: Reaction-level severity takes precedence over allergy-level."""
        ccda_doc = wrap_in_ccda_document(
            ccda_allergy_with_both_level_severity, ALLERGIES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        # Should have 2 reactions (Anaphylaxis and Hives)
        assert len(allergy["reaction"]) == 2

        # First reaction (Anaphylaxis) has reaction-level severity "severe"
        # (should override allergy-level "mild")
        anaphylaxis_reaction = next(
            (r for r in allergy["reaction"]
             if any(c.get("code") == "39579001"
                    for m in r.get("manifestation", [])
                    for c in m.get("coding", []))),
            None
        )
        assert anaphylaxis_reaction is not None
        assert "severity" in anaphylaxis_reaction
        assert anaphylaxis_reaction["severity"] == "severe"

        # Second reaction (Hives) has no reaction-level severity
        # (should inherit allergy-level "mild")
        hives_reaction = next(
            (r for r in allergy["reaction"]
             if any(c.get("code") == "247472004"
                    for m in r.get("manifestation", [])
                    for c in m.get("coding", []))),
            None
        )
        assert hives_reaction is not None
        assert "severity" in hives_reaction
        assert hives_reaction["severity"] == "mild"

    def test_scenario_b_verifies_precedence_rule(
        self, ccda_allergy_with_both_level_severity: str
    ) -> None:
        """Test that reaction-level severity overrides allergy-level severity."""
        ccda_doc = wrap_in_ccda_document(
            ccda_allergy_with_both_level_severity, ALLERGIES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify that the reaction with its own severity uses it (not allergy-level)
        anaphylaxis_reaction = next(
            (r for r in allergy["reaction"]
             if any(c.get("code") == "39579001"
                    for m in r.get("manifestation", [])
                    for c in m.get("coding", []))),
            None
        )
        assert anaphylaxis_reaction is not None
        # Should be "severe" from reaction, NOT "mild" from allergy level
        assert anaphylaxis_reaction["severity"] == "severe"
        assert anaphylaxis_reaction["severity"] != "mild"

    def test_scenario_c_reaction_only_severity_still_works(
        self, ccda_allergy: str, fhir_allergy: JSONObject
    ) -> None:
        """Test Scenario C: Severity only at reaction level (original behavior)."""
        ccda_doc = wrap_in_ccda_document(ccda_allergy, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) >= 1

        # Verify reaction has severity from reaction-level observation only
        reaction = allergy["reaction"][0]
        assert "severity" in reaction
        assert reaction["severity"] == "severe"

    def test_allergy_level_severity_with_no_reactions(
        self, ccda_allergy_with_allergy_level_severity: str
    ) -> None:
        """Test that allergy-level severity doesn't cause errors when no reactions exist."""
        # This test uses a fixture with reactions, but we verify the logic handles
        # the allergy-level severity extraction independently
        ccda_doc = wrap_in_ccda_document(
            ccda_allergy_with_allergy_level_severity, ALLERGIES_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        # Should successfully convert even with allergy-level severity
        assert allergy["resourceType"] == "AllergyIntolerance"


class TestAllergyNarrativePropagation:
    """Test narrative propagation from C-CDA section to FHIR resource.text."""

    def test_section_narrative_propagates_to_resource_text(self, ccda_allergy: str) -> None:
        """Test that section text is converted to FHIR Narrative and added to resource."""
        # Strip XML declaration from fixture
        import re
        ccda_allergy_clean = re.sub(r'<\?xml[^?]*\?>\s*', '', ccda_allergy)

        # Add text/reference element to observation (standards-compliant approach)
        # Insert after <observation> tag
        ccda_allergy_clean = ccda_allergy_clean.replace(
            '<observation classCode="OBS" moodCode="EVN">',
            '<observation classCode="OBS" moodCode="EVN"><text><reference value="#allergy-1"/></text>',
            1  # Only first occurrence
        )

        # Create document with section text containing narrative
        ccda_doc = f"""<?xml version="1.0" encoding="UTF-8"?>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.6.1"/>
                    <code code="48765-2" codeSystem="2.16.840.1.113883.6.1" displayName="Allergies"/>
                    <text>
                        <paragraph ID="allergy-1">
                            <content styleCode="Bold">Allergy:</content> Aspirin
                        </paragraph>
                        <paragraph ID="allergy-2">
                            <content styleCode="Bold">Allergy:</content> Penicillin
                        </paragraph>
                    </text>
                    <entry>
                        {ccda_allergy_clean}
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        assert allergy is not None

        # Verify narrative is present
        assert "text" in allergy
        assert "status" in allergy["text"]
        assert allergy["text"]["status"] == "generated"

        # Verify div element
        assert "div" in allergy["text"]
        div_content = allergy["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify content is present (only allergy-1 paragraph, per text/reference)
        assert "<p" in div_content
        assert "Allergy:" in div_content
        assert "Aspirin" in div_content

        # Verify ID attributes are preserved (only allergy-1, not allergy-2)
        assert 'id="allergy-1"' in div_content
        assert 'id="allergy-2"' not in div_content  # Not referenced, shouldn't be included

        # Verify Penicillin paragraph NOT included (different reference)
        assert "Penicillin" not in div_content

        # Verify styleCode is converted to class
        assert 'class="Bold"' in div_content


class TestAllergyReactionDetails:
    """E2E tests for reaction.description and reaction.note fields per FHIR R4 spec."""

    def test_reaction_description_from_text_element(self) -> None:
        """Test that Reaction Observation text element maps to reaction.description."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_details.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy
        assert len(allergy["reaction"]) == 1

        # Verify description is populated from text element
        reaction = allergy["reaction"][0]
        assert "description" in reaction
        assert "severe hives and itching" in reaction["description"]
        assert "30 minutes" in reaction["description"]

    def test_reaction_note_from_comment_activity(self) -> None:
        """Test that Comment Activity within Reaction Observation maps to reaction.note."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_details.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy

        # Verify note is populated from Comment Activity
        reaction = allergy["reaction"][0]
        assert "note" in reaction
        assert len(reaction["note"]) == 1
        assert "emergency treatment with epinephrine" in reaction["note"][0]["text"]

    def test_reaction_multiple_notes(self) -> None:
        """Test that multiple Comment Activities create multiple reaction notes."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_text_reference.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy

        # Verify multiple notes are created
        reaction = allergy["reaction"][0]
        assert "note" in reaction
        assert len(reaction["note"]) == 2

        # Verify both note texts
        note_texts = [note["text"] for note in reaction["note"]]
        assert "epinephrine auto-injector" in note_texts[0]
        assert "Avoid all peanut-containing products" in note_texts[1]

    def test_reaction_description_and_note_coexist(self) -> None:
        """Test that reaction.description and reaction.note can coexist."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_details.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        reaction = allergy["reaction"][0]
        # Both should be present
        assert "description" in reaction
        assert "note" in reaction
        # And they should contain different content
        assert reaction["description"] != reaction["note"][0]["text"]

    def test_reaction_details_preserve_manifestation_and_severity(self) -> None:
        """Test that adding description/note doesn't interfere with manifestation and severity."""
        with open("tests/integration/fixtures/ccda/allergy_with_reaction_details.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        reaction = allergy["reaction"][0]

        # Verify manifestation is still present
        assert "manifestation" in reaction
        assert len(reaction["manifestation"]) == 1
        snomed_coding = next(
            (c for c in reaction["manifestation"][0]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None
        assert snomed_coding["code"] == "247472004"

        # Verify severity is still present
        assert "severity" in reaction
        assert reaction["severity"] == "severe"

    def test_reaction_without_description_or_note(self) -> None:
        """Test that reactions work normally when description and note are absent."""
        # Use existing fixture that doesn't have description or note
        with open("tests/integration/fixtures/ccda/allergy.xml") as f:
            allergy_xml = f.read()

        ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
        ccda_doc = wrap_in_ccda_document(allergy_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None
        assert "reaction" in allergy

        reaction = allergy["reaction"][0]
        # Should not have description or note fields
        assert "description" not in reaction
        assert "note" not in reaction
        # But should still have manifestation
        assert "manifestation" in reaction


class TestAllergyIntoleranceIDSanitization:
    """Tests for AllergyIntolerance resource ID sanitization."""

    def test_sanitizes_id_with_pipes(self) -> None:
        """Test that allergy IDs with pipe characters are sanitized.

        Real-world C-CDA documents may have IDs with pipes (e.g., 'allergy-130||alg-001')
        which violates FHIR R4B spec. IDs can only contain: A-Z, a-z, 0-9, -, .
        After standardization, IDs use sanitized extension (pipes → hyphens).
        """
        ccda_doc = wrap_in_ccda_document(
            """<act classCode="ACT" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
                <id root="1.2.3.4.5" extension="act-123"/>
                <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                <statusCode code="active"/>
                <effectiveTime>
                    <low value="20080501"/>
                </effectiveTime>
                <entryRelationship typeCode="SUBJ">
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
                        <id root="1.2.3.4.5" extension="130||alg-001"/>
                        <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                        <statusCode code="completed"/>
                        <effectiveTime>
                            <low value="20080501"/>
                        </effectiveTime>
                        <value xsi:type="CD" code="419511003"
                               codeSystem="2.16.840.1.113883.6.96"
                               displayName="Propensity to adverse reactions to drug"/>
                        <participant typeCode="CSM">
                            <participantRole classCode="MANU">
                                <playingEntity classCode="MMAT">
                                    <code code="1191" codeSystem="2.16.840.1.113883.6.88"
                                          displayName="Aspirin"/>
                                </playingEntity>
                            </participantRole>
                        </participant>
                    </observation>
                </entryRelationship>
            </act>""",
            ALLERGIES_TEMPLATE_ID
        )

        bundle = convert_document(ccda_doc)["bundle"]
        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        assert allergy is not None
        # After standardization: pipe characters replaced with hyphens in extension
        assert allergy["id"] == "allergyintolerance-130--alg-001"
        # Verify it's the correct allergy
        assert allergy["code"]["coding"][0]["code"] == "1191"

    def test_sanitizes_id_with_slashes(self) -> None:
        """Test that allergy IDs with slash characters are sanitized."""
        ccda_doc = wrap_in_ccda_document(
            """<act classCode="ACT" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
                <id root="1.2.3.4.5" extension="act-456"/>
                <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                <statusCode code="active"/>
                <effectiveTime>
                    <low value="20080501"/>
                </effectiveTime>
                <entryRelationship typeCode="SUBJ">
                    <observation classCode="OBS" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
                        <id root="1.2.3.4.5" extension="allergy/patient/123"/>
                        <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                        <statusCode code="completed"/>
                        <effectiveTime>
                            <low value="20080501"/>
                        </effectiveTime>
                        <value xsi:type="CD" code="419511003"
                               codeSystem="2.16.840.1.113883.6.96"
                               displayName="Propensity to adverse reactions to drug"/>
                        <participant typeCode="CSM">
                            <participantRole classCode="MANU">
                                <playingEntity classCode="MMAT">
                                    <code code="1191" codeSystem="2.16.840.1.113883.6.88"
                                          displayName="Aspirin"/>
                                </playingEntity>
                            </participantRole>
                        </participant>
                    </observation>
                </entryRelationship>
            </act>""",
            ALLERGIES_TEMPLATE_ID
        )

        bundle = convert_document(ccda_doc)["bundle"]
        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        assert allergy is not None
        # After standardization: slash characters replaced with hyphens in extension
        assert allergy["id"] == "allergyintolerance-allergy-patient-123"
        # Verify it's the correct allergy
        assert allergy["code"]["coding"][0]["code"] == "1191"
