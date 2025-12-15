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
