"""E2E tests for Encounter resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

ENCOUNTERS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.22.1"


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestEncounterConversion:
    """E2E tests for C-CDA Encounter Activity to FHIR Encounter conversion."""

    def test_converts_identifier(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "identifier" in encounter
        assert len(encounter["identifier"]) == 1
        assert encounter["identifier"][0]["value"] == "urn:uuid:2a620155-9d11-439e-92b3-5d9815ff4de8"

    def test_converts_status_to_finished(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that status is always 'finished' for documented encounters."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert encounter["status"] == "finished"

    def test_converts_class_default_ambulatory(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that class defaults to ambulatory."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["code"] == "AMB"
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"

    def test_converts_type_code(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that encounter type code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "type" in encounter
        assert len(encounter["type"]) == 1
        cpt = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt is not None
        assert cpt["code"] == "99213"
        assert cpt["display"] == "Office outpatient visit 15 minutes"

    def test_converts_type_text(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that type text is derived from display name."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "type" in encounter
        assert "text" in encounter["type"][0]

    def test_converts_period_start(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that effectiveTime is converted to period.start."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "period" in encounter
        assert "start" in encounter["period"]
        assert "2012-08-15" in encounter["period"]["start"]

    def test_converts_reason_code_from_diagnosis(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that encounter diagnosis is converted to reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "reasonCode" in encounter
        assert len(encounter["reasonCode"]) == 1
        snomed = next(
            (c for c in encounter["reasonCode"][0]["coding"]
             if c.get("system") == "http://snomed.info/sct"),
            None
        )
        assert snomed is not None
        assert snomed["code"] == "233604007"
        assert snomed["display"] == "Pneumonia"

    def test_resource_type_is_encounter(
        self, ccda_encounter: str, fhir_encounter: dict[str, Any]
    ) -> None:
        """Test that the resource type is Encounter."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert encounter["resourceType"] == "Encounter"
