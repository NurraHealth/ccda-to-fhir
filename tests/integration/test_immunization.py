"""E2E tests for Immunization resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

IMMUNIZATIONS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.2.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestImmunizationConversion:
    """E2E tests for C-CDA Immunization Activity to FHIR Immunization conversion."""

    def test_converts_vaccine_code(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that vaccine code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "vaccineCode" in immunization
        cvx = next(
            (c for c in immunization["vaccineCode"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/cvx"),
            None
        )
        assert cvx is not None
        assert cvx["code"] == "88"
        assert cvx["display"] == "Influenza virus vaccine"

    def test_converts_status_completed(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that completed immunization has correct status."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "completed"

    def test_converts_occurrence_date(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to occurrenceDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "occurrenceDateTime" in immunization
        assert immunization["occurrenceDateTime"] == "2010-08-15"

    def test_converts_dose_quantity(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that dose quantity is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "doseQuantity" in immunization
        assert immunization["doseQuantity"]["value"] == 60
        assert immunization["doseQuantity"]["unit"] == "ug"

    def test_converts_lot_number(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that lot number is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["lotNumber"] == "1"

    def test_converts_manufacturer(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that manufacturer organization is converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "manufacturer" in immunization
        assert immunization["manufacturer"]["display"] == "Health LS - Immuno Inc."

    def test_converts_route(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that route code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "route" in immunization
        assert immunization["route"]["coding"][0]["code"] == "C28161"

    def test_converts_site(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that approach site is converted to site."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "site" in immunization
        assert immunization["site"]["coding"][0]["code"] == "700022004"

    def test_converts_reason_code(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "reasonCode" in immunization
        assert immunization["reasonCode"][0]["coding"][0]["code"] == "195967001"

    def test_converts_dose_number(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that repeat number is converted to protocolApplied.doseNumber."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "protocolApplied" in immunization
        assert immunization["protocolApplied"][0]["doseNumberPositiveInt"] == 1

    def test_converts_ndc_translation(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that NDC translation codes are included."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "vaccineCode" in immunization
        ndc = next(
            (c for c in immunization["vaccineCode"]["coding"]
             if c.get("system") == "http://hl7.org/fhir/sid/ndc"),
            None
        )
        assert ndc is not None
        assert ndc["code"] == "49281-0422-50"

    def test_resource_type_is_immunization(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that the resource type is Immunization."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["resourceType"] == "Immunization"

    def test_provenance_has_recorded_date(
        self, ccda_immunization: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        immun_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                immunization["id"] in t.get("reference", "") for t in prov["target"]
            ):
                immun_provenance = prov
                break

        assert immun_provenance is not None
        assert "recorded" in immun_provenance
        # Should have a valid ISO datetime
        assert len(immun_provenance["recorded"]) > 0

    def test_provenance_agent_has_correct_type(
        self, ccda_immunization: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        immun_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                immunization["id"] in t.get("reference", "") for t in prov["target"]
            ):
                immun_provenance = prov
                break

        assert immun_provenance is not None
        assert "agent" in immun_provenance
        assert len(immun_provenance["agent"]) > 0

        # Check agent type
        agent = immun_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_immunization_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_multiple_authors, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        immun_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                immunization["id"] in t.get("reference", "") for t in prov["target"]
            ):
                immun_provenance = prov
                break

        assert immun_provenance is not None
        assert "agent" in immun_provenance
        # Should have multiple agents for multiple authors
        assert len(immun_provenance["agent"]) >= 2

        # Verify all agents reference practitioners
        for agent in immun_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_primary_source_omitted_when_not_available(
        self, ccda_immunization: str
    ) -> None:
        """Test that primarySource is omitted when not available.

        Per FHIR R4B spec, primarySource is optional (0..1 cardinality).
        C-CDA has no equivalent concept, so the field should be omitted
        rather than using data-absent-reason.
        """
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # US Core STU6+ makes primarySource optional (0..1, Must Support)
        # Should omit when C-CDA has no equivalent data
        assert "primarySource" not in immunization
        assert "_primarySource" not in immunization

    def test_reaction_creates_observation_reference(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction creates a reference to an Observation resource."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Should have reaction with detail reference (not manifestation)
        assert "reaction" in immunization
        assert len(immunization["reaction"]) > 0
        reaction = immunization["reaction"][0]

        # FHIR R4 Immunization.reaction only has detail, date, and reported
        # Should NOT have manifestation (that's only for AllergyIntolerance)
        assert "detail" in reaction
        assert "manifestation" not in reaction

        # Detail should be a reference
        assert "reference" in reaction["detail"]
        assert reaction["detail"]["reference"].startswith("Observation/")

    def test_reaction_observation_created_in_bundle(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction Observation resource is created in the bundle."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Get reaction reference
        reaction = immunization["reaction"][0]
        observation_ref = reaction["detail"]["reference"]
        observation_id = observation_ref.replace("Observation/", "")

        # Find the Observation in the bundle
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]

        # Should have at least one observation for the reaction
        reaction_observation = None
        for obs in observations:
            if obs.get("id") == observation_id:
                reaction_observation = obs
                break

        assert reaction_observation is not None
        assert reaction_observation["resourceType"] == "Observation"
        assert reaction_observation["status"] == "final"

    def test_reaction_observation_has_correct_code(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction Observation has the correct code from C-CDA value."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Get reaction observation ID
        reaction = immunization["reaction"][0]
        observation_id = reaction["detail"]["reference"].replace("Observation/", "")

        # Find the observation
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
            and entry.get("resource", {}).get("id") == observation_id
        ]

        assert len(observations) == 1
        observation = observations[0]

        # Should have code from C-CDA reaction value (247472004 = Wheal)
        assert "code" in observation
        assert "coding" in observation["code"]
        assert observation["code"]["coding"][0]["code"] == "247472004"
        assert observation["code"]["coding"][0]["display"] == "Wheal"

    def test_reaction_observation_has_value_codeable_concept(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction Observation has valueCodeableConcept."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Get reaction observation
        reaction = immunization["reaction"][0]
        observation_id = reaction["detail"]["reference"].replace("Observation/", "")

        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
            and entry.get("resource", {}).get("id") == observation_id
        ]

        observation = observations[0]

        # Should have valueCodeableConcept
        assert "valueCodeableConcept" in observation
        assert observation["valueCodeableConcept"]["coding"][0]["code"] == "247472004"

    def test_reaction_has_date_from_effective_time(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction includes date from effectiveTime."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Reaction should have date
        reaction = immunization["reaction"][0]
        assert "date" in reaction
        assert reaction["date"] == "2008-05-01"

    def test_reaction_observation_has_effective_date_time(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction Observation has effectiveDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Get reaction observation
        reaction = immunization["reaction"][0]
        observation_id = reaction["detail"]["reference"].replace("Observation/", "")

        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
            and entry.get("resource", {}).get("id") == observation_id
        ]

        observation = observations[0]

        # Should have effectiveDateTime
        assert "effectiveDateTime" in observation
        assert observation["effectiveDateTime"] == "2008-05-01"

    def test_converts_comment_activity_to_note(
        self, ccda_immunization_with_comment: str
    ) -> None:
        """Test that Comment Activity is converted to Immunization.note."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_with_comment, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Should have note from Comment Activity
        assert "note" in immunization
        assert len(immunization["note"]) > 0

        # Check note content
        note = immunization["note"][0]
        assert "text" in note
        assert note["text"] == "Patient tolerated the vaccine well. No immediate adverse reactions observed."

    def test_supporting_observations_create_separate_resources(
        self, ccda_immunization_with_supporting_observations: str
    ) -> None:
        """Test that SPRT entry relationships create separate Observation resources."""
        ccda_doc = wrap_in_ccda_document(
            ccda_immunization_with_supporting_observations, IMMUNIZATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Find all observations in the bundle
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]

        # Should have at least 2 supporting observations (SPRT) and 1 complication (COMP)
        assert len(observations) >= 3

        # Check that we have supporting observations with correct codes
        supporting_codes = [
            obs["code"]["coding"][0]["code"]
            for obs in observations
            if "code" in obs and "coding" in obs["code"]
        ]

        # Should include antibody titer (22600-1) and immunity test (94661-0)
        assert "22600-1" in supporting_codes  # Influenza virus A Ab [Titer]
        assert "94661-0" in supporting_codes  # SARS-CoV-2 stimulated gamma interferon

    def test_component_observations_create_separate_resources(
        self, ccda_immunization_with_supporting_observations: str
    ) -> None:
        """Test that COMP entry relationships create separate Observation resources for complications."""
        ccda_doc = wrap_in_ccda_document(
            ccda_immunization_with_supporting_observations, IMMUNIZATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Find all observations in the bundle
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]

        # Should have complication observation
        complication_obs = None
        for obs in observations:
            if "code" in obs and "coding" in obs["code"]:
                for coding in obs["code"]["coding"]:
                    # Injection site infection: 40983000
                    if "valueCodeableConcept" in obs:
                        value_codings = obs["valueCodeableConcept"].get("coding", [])
                        for value_coding in value_codings:
                            if value_coding.get("code") == "40983000":
                                complication_obs = obs
                                break

        assert complication_obs is not None
        assert complication_obs["status"] == "final"

    def test_supporting_observation_has_correct_structure(
        self, ccda_immunization_with_supporting_observations: str
    ) -> None:
        """Test that supporting observations have correct FHIR structure."""
        ccda_doc = wrap_in_ccda_document(
            ccda_immunization_with_supporting_observations, IMMUNIZATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find observations with LOINC code 22600-1 (Influenza virus A Ab [Titer])
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]

        titer_obs = None
        for obs in observations:
            if "code" in obs and "coding" in obs["code"]:
                for coding in obs["code"]["coding"]:
                    if coding.get("code") == "22600-1":
                        titer_obs = obs
                        break

        assert titer_obs is not None
        assert titer_obs["resourceType"] == "Observation"
        assert titer_obs["status"] == "final"

        # Should have code from observation.code
        assert "code" in titer_obs
        assert titer_obs["code"]["coding"][0]["code"] == "22600-1"
        assert "Influenza" in titer_obs["code"]["coding"][0]["display"]

        # Should have value (PQ value="1" unit=":{titer}")
        assert "valueQuantity" in titer_obs
        assert titer_obs["valueQuantity"]["value"] == 1

        # Should have interpretation code (POS = Positive)
        assert "interpretation" in titer_obs
        assert titer_obs["interpretation"][0]["coding"][0]["code"] == "POS"

    def test_component_observation_has_correct_structure(
        self, ccda_immunization_with_supporting_observations: str
    ) -> None:
        """Test that component observations (complications) have correct FHIR structure."""
        ccda_doc = wrap_in_ccda_document(
            ccda_immunization_with_supporting_observations, IMMUNIZATIONS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find observations with value code 40983000 (Injection site infection)
        observations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]

        infection_obs = None
        for obs in observations:
            if "valueCodeableConcept" in obs and "coding" in obs["valueCodeableConcept"]:
                for coding in obs["valueCodeableConcept"]["coding"]:
                    if coding.get("code") == "40983000":
                        infection_obs = obs
                        break

        assert infection_obs is not None
        assert infection_obs["resourceType"] == "Observation"
        assert infection_obs["status"] == "final"

        # Should have code (Problem: 55607006)
        assert "code" in infection_obs
        assert infection_obs["code"]["coding"][0]["code"] == "55607006"

        # Should have value (Injection site infection: 40983000)
        assert "valueCodeableConcept" in infection_obs
        assert infection_obs["valueCodeableConcept"]["coding"][0]["code"] == "40983000"
        assert "infection" in infection_obs["valueCodeableConcept"]["coding"][0]["display"].lower()

    def test_vaccine_code_required_when_null_flavor(self, ccda_immunization_no_vaccine_code: str) -> None:
        """Test that Immunization without vaccineCode is not created.

        Per FHIR R4B spec and user code review, vaccineCode is required (1..1 cardinality).
        When C-CDA consumable has nullFlavor code, the Immunization should not be created
        rather than using data-absent-reason (which violates FHIR spec).

        This ensures strict validation and FHIR compliance.
        """
        ccda_doc = wrap_in_ccda_document(ccda_immunization_no_vaccine_code, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        # Immunization should NOT be created when vaccine code is missing
        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is None, (
            "Immunization should not be created when vaccineCode is missing. "
            "vaccineCode is required (1..1 cardinality) per FHIR R4B spec."
        )

    def test_performer_creates_proper_reference(self) -> None:
        """Test that performer.actor creates proper Reference, not display-only object.

        Per FHIR R4B spec, Immunization.performer.actor is required (1..1) and must be
        a Reference to Practitioner, PractitionerRole, or Organization.
        This test ensures we create proper references from assignedEntity.id.
        """
        ccda_immunization_with_performer = """
            <substanceAdministration classCode="SBADM" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.52" extension="2015-08-01"/>
                <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
                <statusCode code="completed"/>
                <effectiveTime value="20101214"/>
                <consumable>
                    <manufacturedProduct classCode="MANU">
                        <templateId root="2.16.840.1.113883.10.20.22.4.54" extension="2014-06-09"/>
                        <manufacturedMaterial>
                            <code code="88" codeSystem="2.16.840.1.113883.12.292"
                                  displayName="Influenza virus vaccine"/>
                        </manufacturedMaterial>
                    </manufacturedProduct>
                </consumable>
                <performer typeCode="PRF">
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                        <code code="163W00000X" codeSystem="2.16.840.1.113883.6.101"
                              displayName="Registered Nurse"/>
                        <assignedPerson>
                            <name>
                                <given>Jane</given>
                                <family>Nurse</family>
                            </name>
                        </assignedPerson>
                    </assignedEntity>
                </performer>
            </substanceAdministration>
        """
        ccda_doc = wrap_in_ccda_document(ccda_immunization_with_performer, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "performer" in immunization
        assert len(immunization["performer"]) == 1

        performer = immunization["performer"][0]

        # Verify actor is a proper Reference, not just display
        assert "actor" in performer
        assert "reference" in performer["actor"]
        assert performer["actor"]["reference"].startswith("Practitioner/")

        # Verify function is set to Administering Provider
        assert "function" in performer
        assert performer["function"]["coding"][0]["code"] == "AP"
        assert performer["function"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/v2-0443"
