"""E2E tests for Immunization resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "completed"

    def test_converts_occurrence_date(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to occurrenceDateTime."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "occurrenceDateTime" in immunization
        assert immunization["occurrenceDateTime"] == "2010-08-15"

    def test_converts_dose_quantity(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that dose quantity is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["lotNumber"] == "1"

    def test_converts_manufacturer(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that manufacturer organization is converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "manufacturer" in immunization
        assert immunization["manufacturer"]["display"] == "Health LS - Immuno Inc."

    def test_converts_route(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that route code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "route" in immunization
        assert immunization["route"]["coding"][0]["code"] == "C28161"

    def test_converts_site(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that approach site is converted to site."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "site" in immunization
        assert immunization["site"]["coding"][0]["code"] == "700022004"

    def test_converts_reason_code(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that indication is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "reasonCode" in immunization
        assert immunization["reasonCode"][0]["coding"][0]["code"] == "195967001"

    def test_converts_dose_number(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that repeat number is converted to protocolApplied.doseNumber."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert "protocolApplied" in immunization
        assert immunization["protocolApplied"][0]["doseNumberPositiveInt"] == 1

    def test_converts_ndc_translation(
        self, ccda_immunization: str, fhir_immunization: JSONObject
    ) -> None:
        """Test that NDC translation codes are included."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["resourceType"] == "Immunization"

    def test_provenance_has_recorded_date(
        self, ccda_immunization: str
    ) -> None:
        """Test that Provenance has a recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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

    def test_primary_source_has_data_absent_reason_extension(
        self, ccda_immunization: str
    ) -> None:
        """Test that primarySource uses data-absent-reason extension."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None

        # Should have _primarySource with data-absent-reason extension
        assert "_primarySource" in immunization
        assert "extension" in immunization["_primarySource"]
        extensions = immunization["_primarySource"]["extension"]
        assert len(extensions) > 0

        # Check extension URL and value
        data_absent_ext = extensions[0]
        assert data_absent_ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert data_absent_ext["valueCode"] == "unsupported"

        # Should NOT have primarySource field directly
        assert "primarySource" not in immunization

    def test_reaction_creates_observation_reference(
        self, ccda_immunization: str
    ) -> None:
        """Test that reaction creates a reference to an Observation resource."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization, IMMUNIZATIONS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
        bundle = convert_document(ccda_doc)

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
