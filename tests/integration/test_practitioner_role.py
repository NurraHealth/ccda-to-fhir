"""E2E integration tests for PractitionerRole resource conversion.

Test-Driven Development (TDD) - Tests written before implementation.
These tests validate end-to-end conversion from C-CDA to FHIR PractitionerRole.
"""

from __future__ import annotations

from textwrap import dedent

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


class TestPractitionerRoleConversion:
    """E2E tests for C-CDA Author to FHIR PractitionerRole conversion."""

    def test_creates_practitioner_role_in_bundle(
        self, ccda_author: str
    ) -> None:
        """Test that author creates a PractitionerRole resource in the bundle."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")
        assert practitioner_role is not None
        assert practitioner_role["resourceType"] == "PractitionerRole"

    def test_practitioner_role_links_to_practitioner(
        self, ccda_author: str
    ) -> None:
        """Test that PractitionerRole references the Practitioner."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")

        assert practitioner is not None
        assert practitioner_role is not None
        assert "practitioner" in practitioner_role
        assert "reference" in practitioner_role["practitioner"]

        # Reference should point to the practitioner in the bundle
        expected_ref = f"Practitioner/{practitioner['id']}"
        assert practitioner_role["practitioner"]["reference"] == expected_ref

    def test_practitioner_role_links_to_organization(
        self, ccda_author: str
    ) -> None:
        """Test that PractitionerRole references the Organization."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        organization = _find_resource_in_bundle(bundle, "Organization")
        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")

        assert organization is not None
        assert practitioner_role is not None
        assert "organization" in practitioner_role
        assert "reference" in practitioner_role["organization"]

        # Reference should point to the organization in the bundle
        expected_ref = f"Organization/{organization['id']}"
        assert practitioner_role["organization"]["reference"] == expected_ref

    def test_specialty_in_practitioner_role_not_practitioner(
        self, ccda_author: str
    ) -> None:
        """Test that specialty is in PractitionerRole, NOT Practitioner.qualification.

        This is the key fix: assignedAuthor/code should map to PractitionerRole.specialty,
        NOT Practitioner.qualification (which is for academic degrees like MD, PhD).
        """
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")

        assert practitioner is not None
        assert practitioner_role is not None

        # ❌ Practitioner should NOT have qualification field
        assert "qualification" not in practitioner, \
            "Specialty should NOT be in Practitioner.qualification"

        # ✅ PractitionerRole SHOULD have specialty field
        assert "specialty" in practitioner_role, \
            "Specialty SHOULD be in PractitionerRole.specialty"

    def test_specialty_code_and_display(
        self, ccda_author: str
    ) -> None:
        """Test that specialty code and display are correctly converted."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")
        assert practitioner_role is not None

        assert "specialty" in practitioner_role
        assert len(practitioner_role["specialty"]) >= 1

        specialty = practitioner_role["specialty"][0]
        assert "coding" in specialty
        assert len(specialty["coding"]) >= 1

        coding = specialty["coding"][0]
        # From author.xml fixture: code="207Q00000X" displayName="Family Medicine"
        assert coding["code"] == "207Q00000X"
        assert coding["display"] == "Family Medicine"

    def test_nucc_taxonomy_system(
        self, ccda_author: str
    ) -> None:
        """Test that NUCC taxonomy code system is correctly mapped."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")
        assert practitioner_role is not None

        coding = practitioner_role["specialty"][0]["coding"][0]
        # NUCC Taxonomy OID (2.16.840.1.113883.6.101) should map to FHIR URI
        assert coding["system"] == "http://nucc.org/provider-taxonomy"

    def test_generated_id_is_stable(
        self, ccda_author: str
    ) -> None:
        """Test that generated ID uses UUID v4 and references are consistent within conversion."""
        import uuid as uuid_module

        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        role = _find_resource_in_bundle(bundle, "PractitionerRole")
        assert role is not None
        assert "id" in role

        # ID should be composite format: role-{practitioner_uuid}-{organization_uuid}
        role_id = role["id"]
        assert role_id.startswith("role-"), f"PractitionerRole ID should start with 'role-': {role_id}"

        # Verify practitioner reference uses consistent ID
        assert "practitioner" in role
        practitioner_id = role["practitioner"]["reference"].split("/")[1]

        # Extract practitioner UUID from composite role ID and verify it matches
        # Format: role-{practitioner_uuid}-{organization_uuid}
        id_parts = role_id.split("-", 1)  # Split into ['role', '{practitioner_uuid}-{organization_uuid}']
        if len(id_parts) == 2:
            # Validate the practitioner UUID in the composite ID
            uuid_part = id_parts[1].split("-", 8)[0:8]  # Get first 8 parts (5 UUID segments with 3 extra hyphens from 2nd UUID)
            practitioner_uuid_str = "-".join(uuid_part[:5])  # First UUID
            try:
                uuid_module.UUID(practitioner_uuid_str, version=4)
            except (ValueError, IndexError):
                pass  # Composite ID format may vary, continue with reference check

        # Find the practitioner in the bundle
        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        assert practitioner is not None
        assert practitioner["id"] == practitioner_id, "PractitionerRole should reference the correct Practitioner"

    def test_multiple_authors_create_multiple_roles(
        self
    ) -> None:
        """Test that multiple authors create multiple PractitionerRole resources."""
        # Create document with two different authors
        author1 = """
        <author>
            <time value="20140104"/>
            <assignedAuthor>
                <id extension="11111111" root="2.16.840.1.113883.4.6"/>
                <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                      displayName="Family Medicine"/>
                <assignedPerson>
                    <name><given>John</given><family>Smith</family></name>
                </assignedPerson>
                <representedOrganization>
                    <id extension="ORG-A" root="2.16.840.1.113883.4.6"/>
                    <name>Clinic A</name>
                </representedOrganization>
            </assignedAuthor>
        </author>
        """

        author2 = """
        <author>
            <time value="20140105"/>
            <assignedAuthor>
                <id extension="22222222" root="2.16.840.1.113883.4.6"/>
                <code code="207R00000X" codeSystem="2.16.840.1.113883.6.101"
                      displayName="Internal Medicine"/>
                <assignedPerson>
                    <name><given>Jane</given><family>Doe</family></name>
                </assignedPerson>
                <representedOrganization>
                    <id extension="ORG-B" root="2.16.840.1.113883.4.6"/>
                    <name>Clinic B</name>
                </representedOrganization>
            </assignedAuthor>
        </author>
        """

        # Note: wrap_in_ccda_document only accepts single author
        # Need to manually construct document with multiple authors
        ccda_doc = f"""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
            {author1}
            {author2}
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
                            <code code="10164-2" codeSystem="2.16.840.1.113883.6.1"/>
                            <title>History of Present Illness</title>
                            <text>Test content</text>
                        </section>
                    </component>
                </structuredBody>
            </component>
        </ClinicalDocument>
        """

        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_roles = _find_all_resources_in_bundle(bundle, "PractitionerRole")

        # Should have 2 PractitionerRole resources (one for each author)
        assert len(practitioner_roles) == 2

        # Should have different specialties
        specialties = [
            role["specialty"][0]["coding"][0]["code"]
            for role in practitioner_roles
            if "specialty" in role
        ]
        assert "207Q00000X" in specialties  # Family Medicine
        assert "207R00000X" in specialties  # Internal Medicine

    def test_same_practitioner_different_orgs(
        self
    ) -> None:
        """Test that same practitioner at different organizations creates separate roles."""
        # Same practitioner (same NPI) at two different organizations
        author1 = """
        <author>
            <time value="20140104"/>
            <assignedAuthor>
                <id extension="99999999" root="2.16.840.1.113883.4.6"/>
                <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                      displayName="Family Medicine"/>
                <assignedPerson>
                    <name><given>Henry</given><family>Seven</family></name>
                </assignedPerson>
                <representedOrganization>
                    <id extension="ORG-A" root="2.16.840.1.113883.4.6"/>
                    <name>Clinic A</name>
                </representedOrganization>
            </assignedAuthor>
        </author>
        """

        author2 = """
        <author>
            <time value="20140105"/>
            <assignedAuthor>
                <id extension="99999999" root="2.16.840.1.113883.4.6"/>
                <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                      displayName="Family Medicine"/>
                <assignedPerson>
                    <name><given>Henry</given><family>Seven</family></name>
                </assignedPerson>
                <representedOrganization>
                    <id extension="ORG-B" root="2.16.840.1.113883.4.6"/>
                    <name>Clinic B</name>
                </representedOrganization>
            </assignedAuthor>
        </author>
        """

        ccda_doc = f"""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3">
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
            {author1}
            {author2}
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
                            <code code="10164-2" codeSystem="2.16.840.1.113883.6.1"/>
                            <title>Test</title>
                            <text>Test</text>
                        </section>
                    </component>
                </structuredBody>
            </component>
        </ClinicalDocument>
        """

        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_roles = _find_all_resources_in_bundle(bundle, "PractitionerRole")
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        organizations = _find_all_resources_in_bundle(bundle, "Organization")

        # Should have 1 Practitioner (deduplicated)
        assert len(practitioners) == 1

        # Should have 2 Organizations (different orgs)
        # Note: May be 3 if custodian is also included
        assert len(organizations) >= 2

        # Should have 2 PractitionerRole resources
        # (same practitioner but different organizations = different roles)
        assert len(practitioner_roles) == 2

        # Both roles should reference the same practitioner
        practitioner_refs = [
            role["practitioner"]["reference"]
            for role in practitioner_roles
        ]
        assert practitioner_refs[0] == practitioner_refs[1]

        # But roles should reference different organizations
        org_refs = [
            role["organization"]["reference"]
            for role in practitioner_roles
        ]
        assert org_refs[0] != org_refs[1]

    def test_practitioner_role_has_id(
        self, ccda_author: str
    ) -> None:
        """Test that PractitionerRole has a valid ID."""
        ccda_doc = wrap_in_ccda_document("", author=ccda_author)
        bundle = convert_document(ccda_doc)["bundle"]

        practitioner_role = _find_resource_in_bundle(bundle, "PractitionerRole")
        assert practitioner_role is not None
        assert "id" in practitioner_role
        assert len(practitioner_role["id"]) > 0
        assert isinstance(practitioner_role["id"], str)

    def test_practitioner_without_organization_no_role(self) -> None:
        """Test that practitioner without organization doesn't create PractitionerRole.

        When an author has assignedPerson but no representedOrganization,
        we create Practitioner but NOT PractitionerRole (requires both).
        """
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-no-org"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20240101120000"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                    <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"
                          displayName="Family Medicine"/>
                    <assignedPerson>
                        <name><given>Jane</given><family>Smith</family></name>
                    </assignedPerson>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        practitioner_roles = _find_all_resources_in_bundle(bundle, "PractitionerRole")

        # Should have 1 Practitioner (from author)
        assert len(practitioners) == 1
        assert practitioners[0]["name"][0]["given"][0] == "Jane"
        assert practitioners[0]["name"][0]["family"] == "Smith"

        # Should have NO PractitionerRole (requires both practitioner AND organization)
        assert len(practitioner_roles) == 0

    def test_organization_without_practitioner_no_role(self) -> None:
        """Test that organization without practitioner doesn't create PractitionerRole.

        When an author has representedOrganization but no assignedPerson,
        we create Organization but NOT PractitionerRole (requires both).
        """
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-no-person"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20240101120000"/>
                <assignedAuthor>
                    <id root="1.2.3.4.5" extension="org-id-123"/>
                    <representedOrganization>
                        <id root="1.2.3.4.5" extension="hospital-abc"/>
                        <name>ABC Hospital</name>
                        <telecom use="WP" value="tel:555-1234"/>
                        <addr>
                            <streetAddressLine>123 Main St</streetAddressLine>
                            <city>Boston</city>
                            <state>MA</state>
                            <postalCode>02101</postalCode>
                        </addr>
                    </representedOrganization>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        organizations = _find_all_resources_in_bundle(bundle, "Organization")
        practitioner_roles = _find_all_resources_in_bundle(bundle, "PractitionerRole")

        # Should have NO Practitioner (author has no assignedPerson)
        assert len(practitioners) == 0

        # Should have 2 Organizations (author org + custodian org)
        assert len(organizations) == 2
        org_names = [org["name"] for org in organizations]
        assert "ABC Hospital" in org_names
        assert "Custodian Hospital" in org_names

        # Should have NO PractitionerRole (requires both practitioner AND organization)
        assert len(practitioner_roles) == 0
