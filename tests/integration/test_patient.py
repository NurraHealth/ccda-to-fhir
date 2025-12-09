"""E2E tests for Patient resource conversion."""

from __future__ import annotations

from typing import Any

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: dict[str, Any], resource_type: str) -> dict[str, Any] | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestPatientConversion:
    """E2E tests for C-CDA recordTarget to FHIR Patient conversion."""

    def test_converts_patient_name(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that patient name is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "name" in patient
        assert len(patient["name"]) >= 1
        name = patient["name"][0]
        assert name["family"] == "Jones"
        assert name["given"] == ["Myra"]

    def test_converts_patient_gender(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that administrative gender is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["gender"] == "female"

    def test_converts_birth_date(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that birthTime is converted to birthDate."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["birthDate"] == "1947-05-01"

    def test_converts_address(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that address is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "address" in patient
        assert len(patient["address"]) >= 1
        address = patient["address"][0]
        assert address["city"] == "Beaverton"
        assert address["state"] == "OR"
        assert address["postalCode"] == "97006"
        assert address["line"] == ["1357 Amber Drive"]
        assert address["use"] == "home"

    def test_converts_telecom(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that telecom is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "telecom" in patient
        assert len(patient["telecom"]) >= 1
        telecom = patient["telecom"][0]
        assert telecom["system"] == "phone"
        assert telecom["use"] == "mobile"
        assert "+1(565)867-5309" in telecom["value"]

    def test_converts_marital_status(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that marital status is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "maritalStatus" in patient
        assert patient["maritalStatus"]["coding"][0]["code"] == "M"
        assert patient["maritalStatus"]["coding"][0]["display"] == "Married"

    def test_converts_race_extension(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that race is converted to US Core race extension."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient
        race_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"),
            None
        )
        assert race_ext is not None

        # Check ombCategory
        omb_cat = next(
            (e for e in race_ext["extension"] if e["url"] == "ombCategory"),
            None
        )
        assert omb_cat is not None
        assert omb_cat["valueCoding"]["code"] == "2106-3"
        assert omb_cat["valueCoding"]["display"] == "White"

    def test_converts_ethnicity_extension(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that ethnicity is converted to US Core ethnicity extension."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient
        eth_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"),
            None
        )
        assert eth_ext is not None

        # Check ombCategory
        omb_cat = next(
            (e for e in eth_ext["extension"] if e["url"] == "ombCategory"),
            None
        )
        assert omb_cat is not None
        assert omb_cat["valueCoding"]["code"] == "2135-2"
        assert omb_cat["valueCoding"]["display"] == "Hispanic or Latino"

    def test_converts_guardian_to_contact(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that guardian is converted to Patient.contact."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "contact" in patient
        assert len(patient["contact"]) >= 1
        contact = patient["contact"][0]

        # Check name
        assert contact["name"]["family"] == "Betterhalf"
        assert "Boris" in contact["name"]["given"]

        # Check relationship includes GUARD
        relationship_codes = []
        for rel in contact["relationship"]:
            for coding in rel.get("coding", []):
                relationship_codes.append(coding.get("code"))
        assert "GUARD" in relationship_codes

    def test_converts_language_communication(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that languageCommunication is converted."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "communication" in patient
        assert len(patient["communication"]) >= 1
        comm = patient["communication"][0]
        assert comm["language"]["coding"][0]["code"] == "en"
        assert comm["preferred"] is True

    def test_converts_deceased_indicator(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that sdtc:deceasedInd is converted to deceasedBoolean."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["deceasedBoolean"] is False

    def test_converts_birthplace_extension(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that birthplace is converted to patient-birthPlace extension."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient
        bp_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-birthPlace"),
            None
        )
        assert bp_ext is not None
        assert bp_ext["valueAddress"]["city"] == "Beaverton"
        assert bp_ext["valueAddress"]["state"] == "OR"

    def test_converts_religion_extension(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that religiousAffiliationCode is converted to patient-religion extension."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient
        religion_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-religion"),
            None
        )
        assert religion_ext is not None
        assert religion_ext["valueCodeableConcept"]["coding"][0]["code"] == "1013"

    def test_converts_identifier(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that patient ID is converted to identifier."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "identifier" in patient
        assert len(patient["identifier"]) >= 1
        # The identifier should contain the root UUID
        identifier = patient["identifier"][0]
        assert "068F3166-5721-4D69-94ED-8278FF035B8A".lower() in identifier.get("system", "").lower() or \
               "068F3166-5721-4D69-94ED-8278FF035B8A".lower() in identifier.get("value", "").lower()

    def test_resource_type_is_patient(
        self, ccda_patient: str, fhir_patient: dict[str, Any]
    ) -> None:
        """Test that the resource type is Patient."""
        ccda_doc = wrap_in_ccda_document(ccda_patient)
        bundle = convert_document(ccda_doc)

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["resourceType"] == "Patient"
