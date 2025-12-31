"""E2E tests for Practitioner resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


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


class TestAuthorConversion:
    """E2E tests for C-CDA Author to FHIR Practitioner conversion."""

    def test_converts_to_practitioner(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that author creates a Practitioner."""
        # Author should be at document level, not in section content
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert practitioner["resourceType"] == "Practitioner"

    def test_converts_npi_identifier(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that NPI is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "identifier" in practitioner
        npi = next(
            (i for i in practitioner["identifier"]
             if i.get("system") == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi is not None
        assert npi["value"] == "99999999"

    def test_converts_name(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that name is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "name" in practitioner
        assert len(practitioner["name"]) >= 1
        name = practitioner["name"][0]
        assert name["family"] == "Seven"
        assert "Henry" in name["given"]

    def test_converts_name_prefix(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that name prefix is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "name" in practitioner
        name = practitioner["name"][0]
        assert "prefix" in name
        assert "Dr." in name["prefix"]

    def test_converts_name_suffix(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that name suffix is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "name" in practitioner
        name = practitioner["name"][0]
        assert "suffix" in name
        assert "MD" in name["suffix"]

    def test_converts_telecom(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that telecom is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "telecom" in practitioner
        phone = practitioner["telecom"][0]
        assert phone["system"] == "phone"
        assert phone["use"] == "work"
        assert "555-555-1002" in phone["value"]

    def test_converts_address(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that address is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert "address" in practitioner
        address = practitioner["address"][0]
        assert address["city"] == "Portland"
        assert address["state"] == "OR"
        assert address["use"] == "work"

    def test_specialty_in_practitioner_role_not_qualification(
        self, ccda_author: str, fhir_practitioner: JSONObject
    ) -> None:
        """Test that specialty is in PractitionerRole.specialty, NOT Practitioner.qualification.

        IMPORTANT: Specialty (assignedAuthor/code) should map to PractitionerRole.specialty,
        NOT Practitioner.qualification. Qualification is for academic degrees (MD, PhD), not
        functional roles (Family Medicine, Internal Medicine).

        See: docs/mapping/09-practitioner.md lines 133-160
        """
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")

        assert practitioner is not None
        assert practitioner_role is not None

        # ❌ Specialty should NOT be in Practitioner.qualification
        assert "qualification" not in practitioner, \
            "Specialty should be in PractitionerRole.specialty, NOT Practitioner.qualification"

        # ✅ Specialty SHOULD be in PractitionerRole.specialty
        assert "specialty" in practitioner_role, \
            "Specialty should be in PractitionerRole.specialty"

        # Verify the specialty values are correct (from author.xml fixture)
        specialty = practitioner_role["specialty"][0]
        assert "coding" in specialty
        coding = specialty["coding"][0]
        assert coding["code"] == "207Q00000X"
        assert coding["display"] == "Family Medicine"
        assert coding["system"] == "http://nucc.org/provider-taxonomy"


class TestOrganizationConversion:
    """E2E tests for C-CDA representedOrganization to FHIR Organization conversion."""

    def test_converts_represented_organization(
        self, ccda_author: str
    ) -> None:
        """Test that represented organization is converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        organization = _find_resource_in_bundle(bundle, "Organization")
        assert organization is not None
        assert organization["resourceType"] == "Organization"
        assert organization["name"] == "Good Health Clinic"

    def test_organization_has_identifier(
        self, ccda_author: str
    ) -> None:
        """Test that organization identifier is converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        organization = _find_resource_in_bundle(bundle, "Organization")
        assert organization is not None
        assert "identifier" in organization
        npi = next(
            (i for i in organization["identifier"]
             if i.get("system") == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi is not None
        assert npi["value"] == "12345"

    def test_organization_has_telecom(
        self, ccda_author: str
    ) -> None:
        """Test that organization telecom is converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        organization = _find_resource_in_bundle(bundle, "Organization")
        assert organization is not None
        assert "telecom" in organization
        assert organization["telecom"][0]["system"] == "phone"

    def test_organization_has_address(
        self, ccda_author: str
    ) -> None:
        """Test that organization address is converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        organization = _find_resource_in_bundle(bundle, "Organization")
        assert organization is not None
        assert "address" in organization
        assert organization["address"][0]["city"] == "Portland"
