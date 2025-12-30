"""E2E tests for Composition resource conversion."""

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


class TestCompositionConversion:
    """E2E tests for C-CDA ClinicalDocument to FHIR Composition conversion."""

    def test_bundle_has_composition_as_first_entry(self) -> None:
        """Test that Composition is the first entry in a document bundle."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        assert bundle["type"] == "document"
        assert len(bundle["entry"]) > 0
        assert bundle["entry"][0]["resource"]["resourceType"] == "Composition"

    def test_creates_composition_resource(self) -> None:
        """Test that Composition resource is created."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert composition["resourceType"] == "Composition"

    def test_converts_status_to_final(self) -> None:
        """Test that status is set to 'final'.

        Note: Per C-CDA on FHIR spec, legalAuthenticator maps to Composition.attester,
        not Composition.status. There is no official guidance for inferring status from
        authentication state, so we default to 'final' for all documents.
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert composition["status"] == "final"

    def test_converts_identifier(self) -> None:
        """Test that document ID is converted to identifier."""
        # wrap_in_ccda_document uses default document ID
        # <id root="2.16.840.1.113883.19.5.99999.1"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "identifier" in composition
        assert composition["identifier"]["system"] == "urn:oid:2.16.840.1.113883.19.5.99999.1"

    def test_converts_document_type(self) -> None:
        """Test that document code is converted to type."""
        # Default document code from wrap_in_ccda_document:
        # <code code="34133-9" displayName="Summarization of Episode Note"
        #       codeSystem="2.16.840.1.113883.6.1"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "type" in composition
        assert "coding" in composition["type"]
        assert len(composition["type"]["coding"]) >= 1

        loinc_coding = next(
            (c for c in composition["type"]["coding"] if c.get("system") == "http://loinc.org"),
            None,
        )
        assert loinc_coding is not None
        assert loinc_coding["code"] == "34133-9"
        assert loinc_coding["display"] == "Summarization of Episode Note"

    def test_converts_subject_reference(self) -> None:
        """Test that patient reference is created."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "subject" in composition
        assert "reference" in composition["subject"]
        # Should reference the Patient resource
        assert "Patient/" in composition["subject"]["reference"]

    def test_converts_date_from_effective_time(self) -> None:
        """Test that document effectiveTime is converted to date."""
        # Default effectiveTime from wrap_in_ccda_document:
        # <effectiveTime value="20231215120000-0500"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "date" in composition
        # Should be ISO 8601 format
        assert composition["date"].startswith("2023-12-15")

    def test_converts_author_references(self) -> None:
        """Test that document authors are referenced."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "author" in composition
        assert len(composition["author"]) >= 1
        # Should have a reference or display
        assert "reference" in composition["author"][0] or "display" in composition["author"][0]

    def test_converts_title(self) -> None:
        """Test that title is set."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "title" in composition
        assert len(composition["title"]) > 0

    def test_converts_confidentiality(self) -> None:
        """Test that confidentiality code is converted."""
        # Default confidentialityCode from wrap_in_ccda_document:
        # <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "confidentiality" in composition
        assert composition["confidentiality"] == "N"

    def test_converts_custodian_reference(self) -> None:
        """Test that custodian is converted to organization reference."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "custodian" in composition
        # Should have a reference or display
        assert "reference" in composition["custodian"] or "display" in composition["custodian"]

    def test_resource_type_is_composition(self) -> None:
        """Test that resourceType is Composition."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert composition["resourceType"] == "Composition"

    def test_converts_legal_authenticator_to_attester(self) -> None:
        """Test that legalAuthenticator maps to Composition.attester."""
        ccda_doc = wrap_in_ccda_document(
            "",
            legal_authenticator="""
            <legalAuthenticator>
                <time value="20200301"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                    <assignedPerson>
                        <name>
                            <given>Adam</given>
                            <family>Careful</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </legalAuthenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have attester array
        assert "attester" in composition
        assert len(composition["attester"]) == 1

        attester = composition["attester"][0]

        # Mode should be "legal"
        assert attester["mode"] == "legal"

        # Should have time
        assert "time" in attester
        assert attester["time"] == "2020-03-01"

        # Should reference practitioner
        assert "party" in attester
        assert attester["party"]["reference"].startswith("Practitioner/")

        # Capture the generated UUID and verify it's consistent
        import uuid as uuid_module
        practitioner_id = attester["party"]["reference"].split("/")[1]

        # Validate UUID v4 format
        try:
            uuid_module.UUID(practitioner_id, version=4)
        except ValueError:
            raise AssertionError(f"Practitioner ID {practitioner_id} is not a valid UUID v4")

        # Find the legal authenticator's practitioner using the captured ID
        legal_auth_practitioner = None
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Practitioner" and resource.get("id") == practitioner_id:
                legal_auth_practitioner = resource
                break

        assert legal_auth_practitioner is not None, f"Practitioner {practitioner_id} should exist in bundle"
        assert "identifier" in legal_auth_practitioner
        # Verify NPI identifier
        npi_identifier = next(
            (id for id in legal_auth_practitioner["identifier"]
             if id.get("system") == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi_identifier is not None
        assert npi_identifier["value"] == "1234567890"

    def test_converts_legal_authenticator_without_time(self) -> None:
        """Test that legalAuthenticator without time still creates attester."""
        ccda_doc = wrap_in_ccda_document(
            "",
            legal_authenticator="""
            <legalAuthenticator>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9999999999"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Smith</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </legalAuthenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "attester" in composition

        attester = composition["attester"][0]
        assert attester["mode"] == "legal"
        # Should NOT have time when not provided
        assert "time" not in attester
        # Should still have party reference
        assert "party" in attester

    def test_converts_legal_authenticator_without_assigned_entity(self) -> None:
        """Test that legalAuthenticator without assignedEntity does not create attester.

        Per US Realm Header Profile, legal_attester.party is REQUIRED (1..1 cardinality).
        If we cannot create a party reference, we should not create the attester at all
        to ensure strict profile compliance.
        """
        ccda_doc = wrap_in_ccda_document(
            "",
            legal_authenticator="""
            <legalAuthenticator>
                <time value="20200301"/>
                <signatureCode code="S"/>
            </legalAuthenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        # Should NOT have attester field when party cannot be created
        assert "attester" not in composition

    def test_no_attester_without_legal_authenticator(self) -> None:
        """Test that no attester is created when legalAuthenticator is absent."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        # Should NOT have attester field
        assert "attester" not in composition

    def test_converts_authenticator_to_professional_attester(self) -> None:
        """Test that authenticator maps to Composition.attester with mode='professional'."""
        ccda_doc = wrap_in_ccda_document(
            "",
            authenticator="""
            <authenticator>
                <time value="20200302"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Resident</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </authenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have attester array
        assert "attester" in composition
        assert len(composition["attester"]) == 1

        attester = composition["attester"][0]

        # Mode should be "professional"
        assert attester["mode"] == "professional"

        # Should have time
        assert "time" in attester
        assert attester["time"] == "2020-03-02"

        # Should reference practitioner
        assert "party" in attester
        assert attester["party"]["reference"].startswith("Practitioner/")

    def test_converts_multiple_authenticators_to_professional_attesters(self) -> None:
        """Test that multiple authenticators create multiple professional attesters."""
        ccda_doc = wrap_in_ccda_document(
            "",
            authenticator="""
            <authenticator>
                <time value="20200302"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Resident</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </authenticator>
            <authenticator>
                <time value="20200303"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="6666666666"/>
                    <assignedPerson>
                        <name>
                            <given>Bob</given>
                            <family>Intern</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </authenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have attester array with 2 professional attesters
        assert "attester" in composition
        assert len(composition["attester"]) == 2

        # Both should be professional mode
        assert composition["attester"][0]["mode"] == "professional"
        assert composition["attester"][1]["mode"] == "professional"

        # Different times
        assert composition["attester"][0]["time"] == "2020-03-02"
        assert composition["attester"][1]["time"] == "2020-03-03"

    def test_converts_both_legal_and_professional_attesters(self) -> None:
        """Test that both legalAuthenticator and authenticator create respective attesters."""
        ccda_doc = wrap_in_ccda_document(
            "",
            legal_authenticator="""
            <legalAuthenticator>
                <time value="20200301"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                    <assignedPerson>
                        <name>
                            <given>Adam</given>
                            <family>Careful</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </legalAuthenticator>
            """,
            authenticator="""
            <authenticator>
                <time value="20200302"/>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Resident</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </authenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have attester array with both legal and professional
        assert "attester" in composition
        assert len(composition["attester"]) == 2

        # Find legal and professional attesters
        legal_attester = next((a for a in composition["attester"] if a["mode"] == "legal"), None)
        professional_attester = next((a for a in composition["attester"] if a["mode"] == "professional"), None)

        assert legal_attester is not None
        assert legal_attester["time"] == "2020-03-01"

        assert professional_attester is not None
        assert professional_attester["time"] == "2020-03-02"

    def test_converts_authenticator_without_time(self) -> None:
        """Test that authenticator without time still creates professional attester."""
        ccda_doc = wrap_in_ccda_document(
            "",
            authenticator="""
            <authenticator>
                <signatureCode code="S"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                    <assignedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Resident</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </authenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "attester" in composition

        attester = composition["attester"][0]
        assert attester["mode"] == "professional"
        # Should NOT have time when not provided
        assert "time" not in attester
        # Should still have party reference
        assert "party" in attester

    def test_converts_authenticator_without_assigned_entity(self) -> None:
        """Test that authenticator without assignedEntity does not create attester.

        Per US Realm Header Profile, professional_attester.party is REQUIRED (1..1 cardinality).
        If we cannot create a party reference, we should not create the attester at all
        to ensure strict profile compliance.
        """
        ccda_doc = wrap_in_ccda_document(
            "",
            authenticator="""
            <authenticator>
                <time value="20200302"/>
                <signatureCode code="S"/>
            </authenticator>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        # Should NOT have attester field when party cannot be created
        assert "attester" not in composition

    def test_custodian_missing_fails(self) -> None:
        """Test that CompositionConverter fails fast when custodian is missing.

        Per US Realm Header Profile, Composition.custodian has cardinality 1..1 (required).
        The Composition converter should raise ValueError (fail-fast approach, no placeholders).

        Note: This tests the converter directly since convert_document() catches these errors
        and creates a collection bundle instead of propagating them.
        """
        import pytest

        from ccda_to_fhir.ccda.parser import parse_ccda
        from ccda_to_fhir.converters.composition import CompositionConverter
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Document without custodian (non-US Realm Header to bypass parse-time validation)
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.2.3.4.5"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
    <!-- NO CUSTODIAN - should trigger fail-fast -->
    <component>
        <structuredBody>
            <component>
                <section>
                    <title>Test Section</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        # Parse document
        parsed = parse_ccda(ccda_doc)

        # Create reference registry and register a patient (so subject validation passes)
        registry = ReferenceRegistry()
        registry.register_resource({"resourceType": "Patient", "id": "test-patient"})

        # Test CompositionConverter directly
        converter = CompositionConverter(reference_registry=registry)

        # Should raise ValueError with clear message about custodian
        with pytest.raises(ValueError, match="Cannot create Composition without custodian"):
            converter.convert(parsed)

    def test_subject_present_when_recordTarget_exists(self) -> None:
        """Test that subject is present when valid recordTarget exists.

        Per US Realm Header Profile, Composition.subject has cardinality 0..1 (optional).
        When recordTarget exists with valid patient data, patient conversion should succeed
        and subject should reference the actual Patient resource.

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html
        """
        # Document has valid recordTarget with patient data
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <title>Test Section</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Subject should be present when recordTarget exists (0..1 cardinality)
        assert "subject" in composition, "Composition.subject should be present when recordTarget exists"

        # Should reference the actual Patient resource
        assert "reference" in composition["subject"]
        assert composition["subject"]["reference"].startswith("Patient/")

        # Verify the actual Patient resource exists in the bundle
        patient = _find_resource_in_bundle(bundle, "Patient")
        assert patient is not None, "Patient resource must exist in bundle"
        assert "id" in patient
        assert patient["name"][0]["given"] == ["Test"]
        assert patient["name"][0]["family"] == "Patient"

    def test_subject_absent_when_recordTarget_missing(self) -> None:
        """Test that Composition can be created without subject when recordTarget is absent.

        Per US Realm Header Profile, Composition.subject has cardinality 0..1 (optional).
        While most C-CDA documents have recordTarget, the profile allows compositions
        without a subject. The conversion should succeed and simply omit the subject field.

        Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html
        """
        # Document without recordTarget - subject should be optional
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="1.2.3.4.5"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
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
                    <title>Test Section</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert composition["resourceType"] == "Composition"
        # Subject should be absent when recordTarget is missing (0..1 cardinality allows absence)
        assert "subject" not in composition


class TestCompositionSections:
    """Tests for Composition section creation."""

    def test_creates_sections_from_structured_body(self) -> None:
        """Test that sections are created from structured body."""
        # Create a document with a problem section
        ccda_doc_with_section = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Problems</title>
                    <text>Problem section narrative</text>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_section)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        assert len(composition["section"]) >= 1

    def test_section_has_title(self) -> None:
        """Test that section title is converted."""
        ccda_doc_with_section = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Problems</title>
                    <text>Problem section narrative</text>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_section)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        assert len(composition["section"]) >= 1
        assert composition["section"][0]["title"] == "Problems"

    def test_section_has_code(self) -> None:
        """Test that section code is converted."""
        ccda_doc_with_section = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Problems</title>
                    <text>Problem section narrative</text>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_section)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        assert len(composition["section"]) >= 1

        section = composition["section"][0]
        assert "code" in section
        assert "coding" in section["code"]

        loinc_coding = next(
            (c for c in section["code"]["coding"] if c.get("system") == "http://loinc.org"),
            None,
        )
        assert loinc_coding is not None
        assert loinc_coding["code"] == "11450-4"

    def test_section_has_text(self) -> None:
        """Test that section text/narrative is converted."""
        ccda_doc_with_section = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Problems</title>
                    <text>Problem section narrative</text>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_section)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        assert len(composition["section"]) >= 1

        section = composition["section"][0]
        assert "text" in section
        assert "status" in section["text"]
        assert "div" in section["text"]
        assert "Problem section narrative" in section["text"]["div"]

    def test_section_has_structured_narrative(self) -> None:
        """Test that section with structured StrucDocText (paragraphs, tables) is converted."""
        ccda_doc_with_structured_section = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>Problems</title>
                    <text>
                        <paragraph ID="p1">
                            <content styleCode="Bold">Active Problems:</content>
                        </paragraph>
                        <table>
                            <tbody>
                                <tr ID="prob-1">
                                    <td>Hypertension</td>
                                    <td>Active since 2020</td>
                                </tr>
                                <tr ID="prob-2">
                                    <td>Type 2 Diabetes</td>
                                    <td>Controlled</td>
                                </tr>
                            </tbody>
                        </table>
                    </text>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_structured_section)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        assert len(composition["section"]) >= 1

        section = composition["section"][0]

        # Verify narrative structure exists
        assert "text" in section
        assert "status" in section["text"]
        assert section["text"]["status"] == "generated"
        assert "div" in section["text"]

        div_content = section["text"]["div"]

        # Verify XHTML namespace
        assert 'xmlns="http://www.w3.org/1999/xhtml"' in div_content

        # Verify paragraph with ID and styled content
        assert '<p' in div_content
        assert 'id="p1"' in div_content
        assert 'class="Bold"' in div_content
        assert 'Active Problems:' in div_content

        # Verify table structure
        assert '<table' in div_content
        assert '<tbody>' in div_content
        assert '<tr' in div_content
        assert 'id="prob-1"' in div_content
        assert '<td>' in div_content
        assert 'Hypertension' in div_content
        assert 'Type 2 Diabetes' in div_content


class TestEmptySectionsWithNullFlavor:
    """Tests for empty sections with nullFlavor mapped to emptyReason.

    Per C-CDA spec, sections can have nullFlavor instead of entries to indicate
    why they're empty. For example, Notes Section can have nullFlavor instead of
    Note Activity entries. These map to FHIR Composition.section.emptyReason.

    Reference: C-CDA Notes Section (2.16.840.1.113883.10.20.22.2.65)
    Reference: http://terminology.hl7.org/CodeSystem/list-empty-reason
    """

    def test_empty_section_with_nask_maps_to_notasked(self) -> None:
        """Test that NASK nullFlavor maps to 'notasked' emptyReason."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                <section nullFlavor="NASK">
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "section" in composition
        section = composition["section"][0]

        # Should have emptyReason
        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "notasked"
        assert section["emptyReason"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/list-empty-reason"
        assert section["emptyReason"]["coding"][0]["display"] == "Not Asked"

    def test_empty_section_with_unk_maps_to_unavailable(self) -> None:
        """Test that UNK nullFlavor maps to 'unavailable' emptyReason.

        UNK (unknown) means we don't know if items exist, which is semantically
        different from nilknown (confirmed no items after investigation).
        Conservative mapping to 'unavailable'.
        """
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                <section nullFlavor="UNK">
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        section = composition["section"][0]

        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "unavailable"
        assert section["emptyReason"]["coding"][0]["display"] == "Unavailable"

    def test_empty_section_with_nav_maps_to_unavailable(self) -> None:
        """Test that NAV nullFlavor maps to 'unavailable' emptyReason."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                <section nullFlavor="NAV">
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        section = composition["section"][0]

        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "unavailable"
        assert section["emptyReason"]["coding"][0]["display"] == "Unavailable"

    def test_empty_section_with_msk_maps_to_withheld(self) -> None:
        """Test that MSK nullFlavor maps to 'withheld' emptyReason."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                <section nullFlavor="MSK">
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        section = composition["section"][0]

        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "withheld"
        assert section["emptyReason"]["coding"][0]["display"] == "Information Withheld"

    def test_empty_section_without_nullflavor_defaults_to_unavailable(self) -> None:
        """Test that empty section without nullFlavor defaults to 'unavailable'."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        section = composition["section"][0]

        # Should still have emptyReason (default to unavailable)
        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "unavailable"
        assert section["emptyReason"]["coding"][0]["display"] == "Unavailable"

    def test_nullflavor_mapping_case_insensitive(self) -> None:
        """Test that nullFlavor mapping is case-insensitive."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
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
                <section nullFlavor="nask">
                    <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
                    <code code="29299-5" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for visit"/>
                    <title>Notes</title>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        section = composition["section"][0]

        # Should map lowercase "nask" to "notasked"
        assert "emptyReason" in section
        assert section["emptyReason"]["coding"][0]["code"] == "notasked"


class TestParticipantExtensions:
    """Tests for C-CDA on FHIR participant extensions.

    Tests the implementation of seven required participant extensions per C-CDA on FHIR IG:
    1. DataEnterer
    2. Informant
    3. InformationRecipient
    4. Participant
    5. Performer
    6. Authorization
    7. InFulfillmentOfOrder (Order)

    Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participations.html
    """

    def test_data_enterer_extension(self) -> None:
        """Test that dataEnterer maps to DataEnterer extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200301"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
                    <assignedPerson>
                        <name>
                            <given>Data</given>
                            <family>Entry</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have extension array
        assert "extension" in composition
        assert len(composition["extension"]) >= 1

        # Find DataEnterer extension
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None
        assert "valueReference" in data_enterer_ext
        assert data_enterer_ext["valueReference"]["reference"].startswith("Practitioner/")

    def test_informant_extension_with_assigned_entity(self) -> None:
        """Test that informant with assignedEntity maps to Informant extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            informant="""
            <informant>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="2222222222"/>
                    <assignedPerson>
                        <name>
                            <given>Info</given>
                            <family>Source</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </informant>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Informant extension
        assert "extension" in composition
        informant_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/InformantExtension"),
            None
        )
        assert informant_ext is not None
        assert "valueReference" in informant_ext
        assert informant_ext["valueReference"]["reference"].startswith("Practitioner/")

    def test_informant_extension_with_related_entity(self) -> None:
        """Test that informant with relatedEntity maps to Informant extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            informant="""
            <informant>
                <relatedEntity classCode="PRS">
                    <code code="MTH" codeSystem="2.16.840.1.113883.5.111" displayName="Mother"/>
                    <relatedPerson>
                        <name>
                            <given>Martha</given>
                            <family>Ross</family>
                        </name>
                    </relatedPerson>
                </relatedEntity>
            </informant>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Informant extension
        assert "extension" in composition
        informant_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/InformantExtension"),
            None
        )
        assert informant_ext is not None
        assert "valueReference" in informant_ext
        # Should have display with name and relationship
        assert "display" in informant_ext["valueReference"]
        assert "Martha Ross" in informant_ext["valueReference"]["display"]

    def test_information_recipient_extension(self) -> None:
        """Test that informationRecipient maps to InformationRecipient extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            information_recipient="""
            <informationRecipient>
                <intendedRecipient>
                    <id root="2.16.840.1.113883.4.6" extension="3333333333"/>
                    <informationRecipient>
                        <name>
                            <given>John</given>
                            <family>Recipient</family>
                        </name>
                    </informationRecipient>
                </intendedRecipient>
            </informationRecipient>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find InformationRecipient extension
        assert "extension" in composition
        recipient_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/InformationRecipientExtension"),
            None
        )
        assert recipient_ext is not None
        assert "valueReference" in recipient_ext
        # Should have display with recipient name
        assert "display" in recipient_ext["valueReference"]
        assert "John Recipient" in recipient_ext["valueReference"]["display"]

    def test_participant_extension(self) -> None:
        """Test that participant maps to Participant extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            participant="""
            <participant typeCode="IND">
                <associatedEntity classCode="NOK">
                    <code code="GUARD" codeSystem="2.16.840.1.113883.5.111" displayName="Guardian"/>
                    <id root="2.16.840.1.113883.19.5" extension="4444444444"/>
                    <associatedPerson>
                        <name>
                            <given>Jane</given>
                            <family>Guardian</family>
                        </name>
                    </associatedPerson>
                </associatedEntity>
            </participant>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Participant extension
        assert "extension" in composition
        participant_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/ParticipantExtension"),
            None
        )
        assert participant_ext is not None
        assert "valueReference" in participant_ext
        # Should have display with participant name
        assert "display" in participant_ext["valueReference"]
        assert "Jane Guardian" in participant_ext["valueReference"]["display"]

    def test_performer_extension(self) -> None:
        """Test that documentationOf/serviceEvent/performer maps to Performer extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            documentation_of="""
            <documentationOf>
                <serviceEvent classCode="PCPR">
                    <effectiveTime>
                        <low value="20200101"/>
                        <high value="20200301"/>
                    </effectiveTime>
                    <performer typeCode="PRF">
                        <functionCode code="PCP" codeSystem="2.16.840.1.113883.5.88" displayName="Primary Care Provider"/>
                        <assignedEntity>
                            <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                            <assignedPerson>
                                <name>
                                    <given>Primary</given>
                                    <family>Doctor</family>
                                </name>
                            </assignedPerson>
                        </assignedEntity>
                    </performer>
                </serviceEvent>
            </documentationOf>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Performer extension
        assert "extension" in composition
        performer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/PerformerExtension"),
            None
        )
        assert performer_ext is not None
        assert "valueReference" in performer_ext
        assert performer_ext["valueReference"]["reference"].startswith("Practitioner/")

    def test_authorization_extension(self) -> None:
        """Test that authorization maps to Authorization extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            authorization="""
            <authorization>
                <consent>
                    <id root="2.16.840.1.113883.19.5" extension="CONSENT-001"/>
                    <code code="425691002" codeSystem="2.16.840.1.113883.6.96" displayName="Consent given for electronic record sharing"/>
                    <statusCode code="completed"/>
                </consent>
            </authorization>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Authorization extension
        assert "extension" in composition
        auth_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/AuthorizationExtension"),
            None
        )
        assert auth_ext is not None
        assert "valueReference" in auth_ext
        assert auth_ext["valueReference"]["reference"].startswith("Consent/")

    def test_order_extension(self) -> None:
        """Test that inFulfillmentOf maps to Order extension."""
        ccda_doc = wrap_in_ccda_document(
            "",
            in_fulfillment_of="""
            <inFulfillmentOf>
                <order>
                    <id root="2.16.840.1.113883.19.5" extension="ORDER-12345"/>
                    <code code="24610-8" codeSystem="2.16.840.1.113883.6.1" displayName="Radiology Report"/>
                    <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7" displayName="Routine"/>
                </order>
            </inFulfillmentOf>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Order extension
        assert "extension" in composition
        order_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/OrderExtension"),
            None
        )
        assert order_ext is not None
        assert "valueReference" in order_ext
        assert order_ext["valueReference"]["reference"].startswith("ServiceRequest/")

    def test_multiple_extensions_in_same_document(self) -> None:
        """Test that multiple participant extensions can coexist in the same document."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="1111111111"/>
                    <assignedPerson>
                        <name><given>Data</given><family>Entry</family></name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """,
            informant="""
            <informant>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="2222222222"/>
                    <assignedPerson>
                        <name><given>Info</given><family>Source</family></name>
                    </assignedPerson>
                </assignedEntity>
            </informant>
            """,
            information_recipient="""
            <informationRecipient>
                <intendedRecipient>
                    <id root="2.16.840.1.113883.4.6" extension="3333333333"/>
                    <informationRecipient>
                        <name><given>John</given><family>Recipient</family></name>
                    </informationRecipient>
                </intendedRecipient>
            </informationRecipient>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have all three extensions
        assert "extension" in composition
        assert len(composition["extension"]) >= 3

        # Check for DataEnterer
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None

        # Check for Informant
        informant_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/InformantExtension"),
            None
        )
        assert informant_ext is not None

        # Check for InformationRecipient
        recipient_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/InformationRecipientExtension"),
            None
        )
        assert recipient_ext is not None


class TestBundleStructure:
    """Tests for FHIR document Bundle structure and metadata."""

    def test_bundle_has_identifier(self) -> None:
        """Test that Bundle.identifier is present and correct.

        Per FHIR document spec, Bundle.identifier should match the document identifier.
        Reference: https://hl7.org/fhir/R4/documents.html
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        assert "identifier" in bundle
        assert bundle["identifier"]["system"] == "urn:oid:2.16.840.1.113883.19.5.99999.1"

    def test_bundle_has_timestamp(self) -> None:
        """Test that Bundle.timestamp is present and correct.

        Per FHIR document spec, Bundle.timestamp should be the document creation time.
        Reference: https://hl7.org/fhir/R4/documents.html
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        assert "timestamp" in bundle
        # Default timestamp from wrap_in_ccda_document: 20231215120000-0500
        assert bundle["timestamp"].startswith("2023-12-15")
        # Verify it's a valid ISO 8601 datetime
        assert "T" in bundle["timestamp"]

    def test_bundle_identifier_matches_composition_identifier(self) -> None:
        """Test that Bundle.identifier matches Composition.identifier.

        Both should be derived from the same ClinicalDocument/id element.
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Both should have the same identifier
        assert "identifier" in bundle
        assert "identifier" in composition
        assert bundle["identifier"]["system"] == composition["identifier"]["system"]

    def test_bundle_timestamp_matches_composition_date(self) -> None:
        """Test that Bundle.timestamp matches Composition.date.

        Both should be derived from the same ClinicalDocument/effectiveTime element.
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Both should have the same timestamp/date
        assert "timestamp" in bundle
        assert "date" in composition
        assert bundle["timestamp"] == composition["date"]

    def test_bundle_type_is_document(self) -> None:
        """Test that Bundle.type is 'document'.

        Document bundles must have type='document'.
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        assert bundle["type"] == "document"

    def test_bundle_has_all_required_fields(self) -> None:
        """Test that Bundle has all required fields for a FHIR document.

        Required fields per FHIR R4 document spec:
        - resourceType
        - type (must be 'document')
        - entry (with Composition as first entry)
        - identifier (document identifier)
        - timestamp (document timestamp)
        """
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        # Check all required fields
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "document"
        assert "entry" in bundle
        assert len(bundle["entry"]) > 0
        assert "identifier" in bundle
        assert "timestamp" in bundle


class TestBundleEdgeCases:
    """Edge case tests for Bundle timestamp and identifier handling."""

    def test_bundle_timestamp_absent_when_effective_time_lacks_timezone(self) -> None:
        """Bundle.timestamp should be omitted when effectiveTime lacks timezone.

        FHIR instant type requires timezone. When C-CDA effectiveTime has time
        but no timezone, Bundle.timestamp is omitted per FHIR spec.
        """
        from ccda_to_fhir.ccda.parser import parse_ccda

        ccda_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20231215120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="12345"/>
      <patient>
        <name><given>John</given><family>Doe</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20231215120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>Jane</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
</ClinicalDocument>
'''

        ccda_doc = parse_ccda(ccda_xml)
        bundle = convert_document(ccda_doc)["bundle"]

        # Bundle.timestamp is optional (0..1), should be omitted when timezone missing
        assert "timestamp" not in bundle

    def test_bundle_timestamp_present_with_timezone(self) -> None:
        """Bundle.timestamp should be present when effectiveTime has timezone."""
        # Default wrap_in_ccda_document includes timezone
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        assert "timestamp" in bundle
        # Verify it's a valid instant (has timezone)
        assert "T" in bundle["timestamp"]
        assert ("+" in bundle["timestamp"] or "-" in bundle["timestamp"])

    def test_bundle_identifier_without_extension_uses_system_only(self) -> None:
        """Bundle.identifier should have system when extension is absent.

        Per FHIR, Identifier can have system-only (unusual but valid).
        """
        from ccda_to_fhir.ccda.parser import parse_ccda

        ccda_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20231215120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="12345"/>
      <patient>
        <name><given>John</given><family>Doe</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20231215120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>Jane</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
</ClinicalDocument>
'''

        ccda_doc = parse_ccda(ccda_xml)
        bundle = convert_document(ccda_doc)["bundle"]

        assert "identifier" in bundle
        assert "system" in bundle["identifier"]
        # No extension in document ID, so no value field expected
        assert "value" not in bundle["identifier"]

    def test_bundle_timestamp_format_is_valid_instant(self) -> None:
        """Bundle.timestamp should be valid FHIR instant format."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        if "timestamp" in bundle:
            timestamp = bundle["timestamp"]
            # FHIR instant format: YYYY-MM-DDThh:mm:ss+zz:zz
            import re
            instant_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
            assert re.match(instant_pattern, timestamp), f"Invalid instant format: {timestamp}"
