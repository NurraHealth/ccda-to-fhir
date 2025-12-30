"""E2E tests for Patient resource conversion."""

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


class TestPatientConversion:
    """E2E tests for C-CDA recordTarget to FHIR Patient conversion."""

    def test_converts_patient_name(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that patient name is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "name" in patient
        assert len(patient["name"]) >= 1
        name = patient["name"][0]
        assert name["family"] == "Jones"
        assert name["given"] == ["Myra"]

    def test_converts_patient_gender(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that administrative gender is correctly mapped."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["gender"] == "female"

    def test_converts_birth_date(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that birthTime is converted to birthDate."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["birthDate"] == "1947-05-01"

    def test_converts_address(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that address is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that telecom is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "telecom" in patient
        assert len(patient["telecom"]) >= 1
        telecom = patient["telecom"][0]
        assert telecom["system"] == "phone"
        assert telecom["use"] == "mobile"
        assert "+1(565)867-5309" in telecom["value"]

    def test_converts_marital_status(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that marital status is correctly converted."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "maritalStatus" in patient
        assert patient["maritalStatus"]["coding"][0]["code"] == "M"
        assert patient["maritalStatus"]["coding"][0]["display"] == "Married"

    def test_converts_race_extension(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that race is converted to US Core race extension."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that ethnicity is converted to US Core ethnicity extension."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that guardian is converted to Patient.contact."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that languageCommunication is converted."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "communication" in patient
        assert len(patient["communication"]) >= 1
        comm = patient["communication"][0]
        assert comm["language"]["coding"][0]["code"] == "en"
        assert comm["preferred"] is True

    def test_skips_communication_without_language(self) -> None:
        """Test that communication entries without languageCode are skipped.

        FHIR R4B requires Patient.communication.language (1..1 cardinality).
        When C-CDA languageCommunication has nullFlavor or missing languageCode,
        the entry should be skipped rather than creating invalid FHIR.
        """
        ccda_patient = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><given>Test</given><family>Patient</family></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                    <languageCommunication>
                        <languageCode nullFlavor="UNK"/>
                        <preferenceInd value="true"/>
                    </languageCommunication>
                    <languageCommunication>
                        <preferenceInd value="false"/>
                    </languageCommunication>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        # Should have no communication entries since both lack valid language codes
        assert "communication" not in patient or len(patient.get("communication", [])) == 0

    def test_converts_deceased_indicator(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that sdtc:deceasedInd is converted to deceasedBoolean."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["deceasedBoolean"] is False

    def test_converts_deceased_indicator_true(self) -> None:
        """Test that sdtc:deceasedInd='true' is converted to deceasedBoolean: true."""
        ccda_patient = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><given>Test</given><family>Patient</family></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                    <sdtc:deceasedInd xmlns:sdtc="urn:hl7-org:sdtc" value="true"/>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["deceasedBoolean"] is True
        # Should not have deceasedDateTime
        assert "deceasedDateTime" not in patient

    def test_converts_deceased_time(self) -> None:
        """Test that sdtc:deceasedTime is converted to deceasedDateTime."""
        ccda_patient = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><given>Test</given><family>Patient</family></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                    <sdtc:deceasedTime xmlns:sdtc="urn:hl7-org:sdtc" value="20200315"/>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["deceasedDateTime"] == "2020-03-15"
        # Should not have deceasedBoolean
        assert "deceasedBoolean" not in patient

    def test_deceased_time_takes_precedence_over_indicator(self) -> None:
        """Test that when both deceasedTime and deceasedInd are present, deceasedDateTime is used."""
        ccda_patient = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><given>Test</given><family>Patient</family></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                    <sdtc:deceasedInd xmlns:sdtc="urn:hl7-org:sdtc" value="true"/>
                    <sdtc:deceasedTime xmlns:sdtc="urn:hl7-org:sdtc" value="20200315"/>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        # Should use deceasedDateTime, not deceasedBoolean
        assert patient["deceasedDateTime"] == "2020-03-15"
        assert "deceasedBoolean" not in patient

    def test_no_deceased_field_when_not_present(self) -> None:
        """Test that no deceased field is added when neither deceasedInd nor deceasedTime are present."""
        ccda_patient = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><given>Test</given><family>Patient</family></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        # Should not have any deceased field
        assert "deceasedBoolean" not in patient
        assert "deceasedDateTime" not in patient

    def test_converts_birthplace_extension(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that birthplace is converted to patient-birthPlace extension."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that religiousAffiliationCode is converted to patient-religion extension."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

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
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that patient ID is converted to identifier."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "identifier" in patient
        assert len(patient["identifier"]) >= 1
        # The identifier should contain the root UUID
        identifier = patient["identifier"][0]
        assert "068F3166-5721-4D69-94ED-8278FF035B8A".lower() in identifier.get("system", "").lower() or \
               "068F3166-5721-4D69-94ED-8278FF035B8A".lower() in identifier.get("value", "").lower()

    def test_resource_type_is_patient(
        self, ccda_patient: str, fhir_patient: JSONObject) -> None:
        """Test that the resource type is Patient."""
        ccda_doc = wrap_in_ccda_document("", patient=ccda_patient)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert patient["resourceType"] == "Patient"

    def test_converts_birth_sex_extension_female(self) -> None:
        """Test that birth sex observation maps to Patient.extension (female)."""
        birth_sex_observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
            <code code="76689-9" displayName="Sex assigned at birth"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="F" displayName="Female"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            birth_sex_observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have us-core-birthsex extension
        assert "extension" in patient
        birthsex_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
            None
        )
        assert birthsex_ext is not None
        assert birthsex_ext["valueCode"] == "F"

        # Should NOT create a separate Observation resource for birth sex
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        birth_sex_observations = [
            obs for obs in observations
            if obs.get("code", {}).get("coding", [{}])[0].get("code") == "76689-9"
        ]
        assert len(birth_sex_observations) == 0, "Birth sex should NOT create an Observation resource"

    def test_converts_birth_sex_extension_male(self) -> None:
        """Test that birth sex observation maps to Patient.extension (male)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
            <code code="76689-9" displayName="Sex assigned at birth"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="M" displayName="Male"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        birthsex_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
            None
        )
        assert birthsex_ext is not None
        assert birthsex_ext["valueCode"] == "M"

    def test_converts_birth_sex_extension_unknown(self) -> None:
        """Test that birth sex observation maps to Patient.extension (unknown)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
            <code code="76689-9" displayName="Sex assigned at birth"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="UNK" displayName="Unknown"
                   codeSystem="2.16.840.1.113883.5.1"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        birthsex_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
            None
        )
        assert birthsex_ext is not None
        assert birthsex_ext["valueCode"] == "UNK"

    def test_converts_gender_identity_extension_male(self) -> None:
        """Test that gender identity observation maps to Patient.extension (identifies as male)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="76691-5" displayName="Gender identity"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="446151000124109"
                   displayName="Identifies as male"
                   codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have us-core-genderIdentity extension
        assert "extension" in patient
        gender_id_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
            None
        )
        assert gender_id_ext is not None
        assert "valueCodeableConcept" in gender_id_ext
        coding = gender_id_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "446151000124109"
        assert coding["system"] == "http://snomed.info/sct"
        assert "Identifies as male" in coding["display"]

        # Should NOT create a separate Observation resource for gender identity
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        gender_identity_observations = [
            obs for obs in observations
            if obs.get("code", {}).get("coding", [{}])[0].get("code") == "76691-5"
        ]
        assert len(gender_identity_observations) == 0, "Gender identity should NOT create an Observation resource"

    def test_converts_gender_identity_extension_female(self) -> None:
        """Test that gender identity observation maps to Patient.extension (identifies as female)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="76691-5" displayName="Gender identity"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="446141000124107"
                   displayName="Identifies as female"
                   codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        gender_id_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
            None
        )
        assert gender_id_ext is not None
        coding = gender_id_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "446141000124107"
        assert "Identifies as female" in coding["display"]

    def test_converts_gender_identity_extension_non_conforming(self) -> None:
        """Test that gender identity observation maps to Patient.extension (non-conforming)."""
        observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="76691-5" displayName="Gender identity"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="446131000124102"
                   displayName="Identifies as non-conforming"
                   codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        gender_id_ext = next(
            (e for e in patient.get("extension", [])
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
            None
        )
        assert gender_id_ext is not None
        coding = gender_id_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "446131000124102"

    def test_converts_both_birth_sex_and_gender_identity(self) -> None:
        """Test that both birth sex and gender identity are correctly mapped to Patient extensions."""
        # Custom document with multiple entries - wrap_in_ccda_document only supports single entry
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient-id" extension="test-patient-id"/>
            <patient>
                <name><family>Patient</family><given>Test</given></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson><name><family>Author</family><given>Test</given></name></assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                <name>Test Hospital</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                    <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"/>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.200"/>
                            <code code="76689-9" displayName="Sex assigned at birth"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="F" displayName="Female"
                                   codeSystem="2.16.840.1.113883.5.1"/>
                        </observation>
                    </entry>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <code code="76691-5" displayName="Gender identity"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="446151000124109"
                                   displayName="Identifies as male"
                                   codeSystem="2.16.840.1.113883.6.96"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None
        assert "extension" in patient

        # Check birth sex extension
        birthsex_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
            None
        )
        assert birthsex_ext is not None
        assert birthsex_ext["valueCode"] == "F"

        # Check gender identity extension
        gender_id_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
            None
        )
        assert gender_id_ext is not None
        coding = gender_id_ext["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "446151000124109"

        # Verify NO Observation resources created for birth sex or gender identity
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        social_history_obs_codes = set()
        for obs in observations:
            if obs.get("code", {}).get("coding"):
                for coding in obs["code"]["coding"]:
                    social_history_obs_codes.add(coding.get("code"))

        assert "76689-9" not in social_history_obs_codes, "Birth sex should be extension only"
        assert "76691-5" not in social_history_obs_codes, "Gender identity should be extension only"

    def test_no_birth_sex_or_gender_identity_when_not_present(self) -> None:
        """Test that birth sex and gender identity extensions are not added when observations are absent."""
        ccda_doc = wrap_in_ccda_document("")  # No social history section
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Check that birth sex extension is not present
        if "extension" in patient:
            birthsex_ext = next(
                (e for e in patient["extension"]
                 if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-birthsex"),
                None
            )
            assert birthsex_ext is None

            # Check that gender identity extension is not present
            gender_id_ext = next(
                (e for e in patient["extension"]
                 if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-genderIdentity"),
                None
            )
            assert gender_id_ext is None

    def test_converts_birth_time_extension(self) -> None:
        """Test that birthTime with time component creates patient-birthTime extension on _birthDate."""
        # Custom patient with time component in birthTime (with timezone)
        patient_xml = """
        <recordTarget>
            <patientRole>
                <id root="test-patient-id"/>
                <patient>
                    <name><family>Test</family><given>Patient</given></name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19750501103022-0500"/>
                </patient>
            </patientRole>
        </recordTarget>
        """
        ccda_doc = wrap_in_ccda_document("", patient=patient_xml)
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have birthDate
        assert "birthDate" in patient
        assert patient["birthDate"] == "1975-05-01"

        # Should have _birthDate with patient-birthTime extension
        assert "_birthDate" in patient
        assert "extension" in patient["_birthDate"]
        birth_time_ext = next(
            (e for e in patient["_birthDate"]["extension"]
             if e["url"] == "http://hl7.org/fhir/StructureDefinition/patient-birthTime"),
            None
        )
        assert birth_time_ext is not None
        assert "valueDateTime" in birth_time_ext
        # Should include full timestamp
        assert "1975-05-01" in birth_time_ext["valueDateTime"]
        assert "10:30:22" in birth_time_ext["valueDateTime"]

    def test_converts_tribal_affiliation_extension_by_template(self) -> None:
        """Test that tribal affiliation observation maps to Patient.extension (template ID match)."""
        tribal_affiliation_observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.506" extension="2023-05-01"/>
            <code code="95370-3" displayName="Tribal affiliation"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="170" displayName="Navajo Nation, Arizona, New Mexico, &amp; Utah"
                   codeSystem="2.16.840.1.113883.5.140"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            tribal_affiliation_observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have us-core-tribal-affiliation extension
        assert "extension" in patient
        tribal_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation"),
            None
        )
        assert tribal_ext is not None
        assert "extension" in tribal_ext

        # Check tribalAffiliation sub-extension
        tribal_affiliation_sub = next(
            (e for e in tribal_ext["extension"]
             if e["url"] == "tribalAffiliation"),
            None
        )
        assert tribal_affiliation_sub is not None
        assert "valueCodeableConcept" in tribal_affiliation_sub
        coding = tribal_affiliation_sub["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "170"
        assert coding["display"] == "Navajo Nation, Arizona, New Mexico, & Utah"
        # Per FHIR R4B: CodeSystem canonical URI, not OID format
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-TribalEntityUS"

        # Should NOT create a separate Observation resource for tribal affiliation
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        tribal_observations = [
            obs for obs in observations
            if obs.get("code", {}).get("coding", [{}])[0].get("code") == "95370-3"
        ]
        assert len(tribal_observations) == 0, "Tribal affiliation should NOT create an Observation resource"

    def test_converts_tribal_affiliation_extension_by_loinc(self) -> None:
        """Test that tribal affiliation observation maps to Patient.extension (LOINC code match)."""
        tribal_affiliation_observation = """
        <observation classCode="OBS" moodCode="EVN">
            <code code="95370-3" displayName="Tribal affiliation"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="40" displayName="Cherokee Nation"
                   codeSystem="2.16.840.1.113883.5.140"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            tribal_affiliation_observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have us-core-tribal-affiliation extension
        assert "extension" in patient
        tribal_ext = next(
            (e for e in patient["extension"]
             if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation"),
            None
        )
        assert tribal_ext is not None

        # Check tribalAffiliation sub-extension
        tribal_affiliation_sub = next(
            (e for e in tribal_ext["extension"]
             if e["url"] == "tribalAffiliation"),
            None
        )
        assert tribal_affiliation_sub is not None
        coding = tribal_affiliation_sub["valueCodeableConcept"]["coding"][0]
        assert coding["code"] == "40"
        assert coding["display"] == "Cherokee Nation"

    def test_converts_multiple_tribal_affiliations(self) -> None:
        """Test that multiple tribal affiliation observations create multiple extensions."""
        tribal_affiliations = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.506" extension="2023-05-01"/>
            <code code="95370-3" displayName="Tribal affiliation"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="170" displayName="Navajo Nation, Arizona, New Mexico, &amp; Utah"
                   codeSystem="2.16.840.1.113883.5.140"/>
        </observation>
        """
        # Create a document with two tribal affiliation entries
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient-id"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20231215120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson>
                <name><given>Test</given><family>Author</family></name>
            </assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.19.5"/>
                <name>Test Organization</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                    <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"/>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.506" extension="2023-05-01"/>
                            <code code="95370-3" displayName="Tribal affiliation"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="170" displayName="Navajo Nation, Arizona, New Mexico, &amp; Utah"
                                   codeSystem="2.16.840.1.113883.5.140"/>
                        </observation>
                    </entry>
                    <entry>
                        <observation classCode="OBS" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.506" extension="2023-05-01"/>
                            <code code="95370-3" displayName="Tribal affiliation"
                                  codeSystem="2.16.840.1.113883.6.1"/>
                            <statusCode code="completed"/>
                            <value xsi:type="CD" code="40" displayName="Cherokee Nation"
                                   codeSystem="2.16.840.1.113883.5.140"/>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Should have multiple us-core-tribal-affiliation extensions
        assert "extension" in patient
        tribal_exts = [
            e for e in patient["extension"]
            if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation"
        ]
        assert len(tribal_exts) == 2, "Should have 2 tribal affiliation extensions"

        # Check that both tribes are present
        tribe_codes = set()
        for tribal_ext in tribal_exts:
            tribal_affiliation_sub = next(
                (e for e in tribal_ext["extension"]
                 if e["url"] == "tribalAffiliation"),
                None
            )
            assert tribal_affiliation_sub is not None
            coding = tribal_affiliation_sub["valueCodeableConcept"]["coding"][0]
            tribe_codes.add(coding["code"])

        assert "170" in tribe_codes  # Navajo Nation, Arizona, New Mexico, & Utah
        assert "40" in tribe_codes  # Cherokee Nation

    def test_tribal_affiliation_no_observation_resource(self) -> None:
        """Test that tribal affiliation does NOT create separate Observation resources."""
        tribal_affiliation_observation = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.506" extension="2023-05-01"/>
            <code code="95370-3" displayName="Tribal affiliation"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="170" displayName="Navajo Nation, Arizona, New Mexico, &amp; Utah"
                   codeSystem="2.16.840.1.113883.5.140"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(
            tribal_affiliation_observation,
            section_template_id="2.16.840.1.113883.10.20.22.2.17",
            section_code="29762-2"
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Check that no Observation resource was created
        observations = [
            entry["resource"] for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Observation"
        ]
        assert len(observations) == 0, "Tribal affiliation should NOT create any Observation resources"

    def test_no_tribal_affiliation_when_not_present(self) -> None:
        """Test that tribal affiliation extension is not added when observation is absent."""
        ccda_doc = wrap_in_ccda_document("")  # No social history section
        bundle = convert_document(ccda_doc)["bundle"]

        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None

        # Check that tribal affiliation extension is not present
        if "extension" in patient:
            tribal_ext = next(
                (e for e in patient["extension"]
                 if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-tribal-affiliation"),
                None
            )
            assert tribal_ext is None, "Tribal affiliation extension should not be present when observation is absent"
