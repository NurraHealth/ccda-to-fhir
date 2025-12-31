"""Integration tests for informant mapping (Practitioner vs RelatedPerson logic).

Tests verify correct mapping of C-CDA informants to FHIR Practitioner or RelatedPerson
based on whether informant has assignedEntity (Practitioner) or relatedEntity (RelatedPerson).
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.convert import convert_document


class TestInformantPractitionerMapping:
    """Test mapping of informant.assignedEntity to Practitioner."""

    def test_informant_with_assigned_entity_creates_practitioner(self, sample_ccda_with_practitioner_informant):
        """Test that informant with assignedEntity creates Practitioner resource."""
        bundle = convert_document(sample_ccda_with_practitioner_informant)["bundle"]

        # Find Practitioner resources
        practitioners = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "Practitioner"]

        # Should have at least one practitioner from informant
        assert len(practitioners) >= 1

        # Verify practitioner has expected structure
        practitioner = practitioners[0]["resource"]
        assert "identifier" in practitioner
        assert "name" in practitioner

    def test_informant_practitioner_has_correct_identifiers(self, sample_ccda_with_practitioner_informant):
        """Test that informant practitioner has correct NPI identifier."""
        bundle = convert_document(sample_ccda_with_practitioner_informant)["bundle"]

        practitioners = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "Practitioner"]
        practitioner = practitioners[0]["resource"]

        # Verify identifier system for NPI
        npi_identifier = next(
            (id for id in practitioner.get("identifier", [])
             if id.get("system") == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi_identifier is not None
        assert "value" in npi_identifier


class TestInformantRelatedPersonMapping:
    """Test mapping of informant.relatedEntity to RelatedPerson."""

    def test_informant_with_related_entity_creates_related_person(self, sample_ccda_with_related_person_informant):
        """Test that informant with relatedEntity creates RelatedPerson resource."""
        bundle = convert_document(sample_ccda_with_related_person_informant)["bundle"]

        # Find RelatedPerson resources
        related_persons = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "RelatedPerson"]

        # Should have exactly one related person from informant
        assert len(related_persons) == 1

        related_person = related_persons[0]["resource"]
        assert "patient" in related_person
        assert "relationship" in related_person

    def test_related_person_has_patient_reference(self, sample_ccda_with_related_person_informant):
        """Test that RelatedPerson has correct patient reference."""
        bundle = convert_document(sample_ccda_with_related_person_informant)["bundle"]

        related_persons = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "RelatedPerson"]
        related_person = related_persons[0]["resource"]

        # Verify patient reference exists and has correct format
        assert "patient" in related_person
        assert "reference" in related_person["patient"]
        assert related_person["patient"]["reference"].startswith("Patient/")

        # Verify referenced patient exists in bundle
        patient_id = related_person["patient"]["reference"].split("/")[1]
        patients = [r for r in bundle["entry"]
                   if r["resource"]["resourceType"] == "Patient"
                   and r["resource"]["id"] == patient_id]
        assert len(patients) == 1

    def test_related_person_has_relationship_code(self, sample_ccda_with_mother_informant):
        """Test that RelatedPerson has relationship code (e.g., MTH for Mother)."""
        bundle = convert_document(sample_ccda_with_mother_informant)["bundle"]

        related_persons = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "RelatedPerson"]
        related_person = related_persons[0]["resource"]

        # Verify relationship exists
        assert "relationship" in related_person
        assert len(related_person["relationship"]) > 0

        # Verify relationship has coding with MTH code
        relationship = related_person["relationship"][0]
        assert "coding" in relationship

        mth_coding = next(
            (c for c in relationship["coding"] if c.get("code") == "MTH"),
            None
        )
        assert mth_coding is not None
        assert mth_coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-RoleCode"

    def test_related_person_has_name(self, sample_ccda_with_mother_informant):
        """Test that RelatedPerson has name from relatedPerson.name."""
        bundle = convert_document(sample_ccda_with_mother_informant)["bundle"]

        related_persons = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "RelatedPerson"]
        related_person = related_persons[0]["resource"]

        # Verify name exists
        assert "name" in related_person
        assert len(related_person["name"]) > 0

        name = related_person["name"][0]
        assert "family" in name or "given" in name

    def test_related_person_converts_non_standard_code_system(self, sample_ccda_with_snomed_relationship_code):
        """Test that RelatedPerson properly converts non-standard code system OIDs.

        Regression test for BUG-004: RelatedPersonConverter called non-existent
        _convert_oid_to_uri() method. Should use map_oid_to_uri() from BaseConverter.
        """
        bundle = convert_document(sample_ccda_with_snomed_relationship_code)["bundle"]

        related_persons = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "RelatedPerson"]
        assert len(related_persons) == 1

        related_person = related_persons[0]["resource"]

        # Verify relationship exists with SNOMED code
        assert "relationship" in related_person
        assert len(related_person["relationship"]) > 0

        relationship = related_person["relationship"][0]
        assert "coding" in relationship

        # Should have converted SNOMED CT OID to proper URI
        snomed_coding = next(
            (c for c in relationship["coding"] if c.get("code") == "444301002"),
            None
        )
        assert snomed_coding is not None
        # OID 2.16.840.1.113883.6.96 should map to http://snomed.info/sct
        assert snomed_coding["system"] == "http://snomed.info/sct"
        assert snomed_coding["display"] == "Caregiver"


class TestInformantDeduplication:
    """Test deduplication logic for informants."""

    def test_same_practitioner_as_author_and_informant_not_duplicated(
        self, sample_ccda_with_same_practitioner_as_author_and_informant
    ):
        """Test that same practitioner appearing as both author and informant is not duplicated."""
        bundle = convert_document(sample_ccda_with_same_practitioner_as_author_and_informant)["bundle"]

        practitioners = [r for r in bundle["entry"] if r["resource"]["resourceType"] == "Practitioner"]

        # Should only have one practitioner (deduplicated)
        # Count practitioners with the same identifier
        npi_practitioners = {}
        for p in practitioners:
            for identifier in p["resource"].get("identifier", []):
                if identifier.get("system") == "http://hl7.org/fhir/sid/us-npi":
                    npi = identifier["value"]
                    npi_practitioners[npi] = npi_practitioners.get(npi, 0) + 1

        # Each NPI should appear only once
        for npi, count in npi_practitioners.items():
            assert count == 1, f"NPI {npi} appears {count} times, expected 1"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_ccda_with_practitioner_informant() -> str:
    """C-CDA document with informant having assignedEntity (practitioner)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5" extension="DOC001"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary of Episode Note"/>
  <title>Summary of Episode Note</title>
  <effectiveTime value="20240101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="PAT123"/>
      <patient>
        <name><given>Jane</given><family>Doe</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240101120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>John</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>

  <informant>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
      <assignedPerson><name><given>Mary</given><family>Informant</family></name></assignedPerson>
    </assignedEntity>
  </informant>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="ORG001"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problem List</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""


@pytest.fixture
def sample_ccda_with_related_person_informant() -> str:
    """C-CDA document with informant having relatedEntity (related person)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5" extension="DOC002"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary of Episode Note"/>
  <title>Summary of Episode Note</title>
  <effectiveTime value="20240101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="PAT456"/>
      <patient>
        <name><given>Bob</given><family>Patient</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19900615"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240101120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>John</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>

  <informant>
    <relatedEntity classCode="PRS">
      <code code="SPS" codeSystem="2.16.840.1.113883.5.111" displayName="Spouse"/>
      <relatedPerson><name><given>Alice</given><family>Patient</family></name></relatedPerson>
    </relatedEntity>
  </informant>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="ORG001"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problem List</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""


@pytest.fixture
def sample_ccda_with_mother_informant() -> str:
    """C-CDA document with informant being mother (MTH relationship code)."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5" extension="DOC003"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary of Episode Note"/>
  <title>Summary of Episode Note</title>
  <effectiveTime value="20240101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="PAT789"/>
      <patient>
        <name><given>Child</given><family>Patient</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="20200101"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240101120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>Dr.</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>

  <informant>
    <relatedEntity classCode="PRS">
      <code code="MTH" codeSystem="2.16.840.1.113883.5.111" displayName="Mother"/>
      <relatedPerson><name><given>Martha</given><family>Ross</family></name></relatedPerson>
    </relatedEntity>
  </informant>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="ORG001"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problem List</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""


@pytest.fixture
def sample_ccda_with_same_practitioner_as_author_and_informant() -> str:
    """C-CDA document where same practitioner appears as both author and informant."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5" extension="DOC004"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary of Episode Note"/>
  <title>Summary of Episode Note</title>
  <effectiveTime value="20240101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="PAT999"/>
      <patient>
        <name><given>Test</given><family>Patient</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19851010"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240101120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="SAME-NPI-123"/>
      <assignedPerson><name><given>Dr.</given><family>Smith</family></name></assignedPerson>
    </assignedAuthor>
  </author>

  <informant>
    <assignedEntity>
      <id root="2.16.840.1.113883.4.6" extension="SAME-NPI-123"/>
      <assignedPerson><name><given>Dr.</given><family>Smith</family></name></assignedPerson>
    </assignedEntity>
  </informant>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="ORG001"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problem List</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""


@pytest.fixture
def sample_ccda_with_snomed_relationship_code() -> str:
    """C-CDA document with informant using non-standard code system (SNOMED CT).

    This tests BUG-004 fix: RelatedPersonConverter must properly convert
    code system OIDs to FHIR URIs using map_oid_to_uri().
    """
    return """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5" extension="DOC005"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary of Episode Note"/>
  <title>Summary of Episode Note</title>
  <effectiveTime value="20240101120000"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="PAT555"/>
      <patient>
        <name><given>Elderly</given><family>Patient</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19400301"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240101120000"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <assignedPerson><name><given>Dr.</given><family>Jones</family></name></assignedPerson>
    </assignedAuthor>
  </author>

  <informant>
    <relatedEntity classCode="PRS">
      <!-- Using SNOMED CT code system instead of v3-RoleCode -->
      <code code="444301002" codeSystem="2.16.840.1.113883.6.96" displayName="Caregiver"/>
      <relatedPerson><name><given>Sarah</given><family>Caregiver</family></name></relatedPerson>
    </relatedEntity>
  </informant>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="ORG001"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problem List</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
"""
