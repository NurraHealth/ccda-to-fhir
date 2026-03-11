"""Integration tests for DocumentReference encounter display text.

Validates that encompassingEncounter code.displayName propagates to
DocumentReference.context.encounter[].display per FHIR Reference type.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def _get_doc_refs(bundle: dict) -> list[dict]:
    """Extract all DocumentReference resources from a bundle."""
    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == "DocumentReference"
    ]


class TestEncounterDisplayFromCode:
    """NIST Ambulatory has encompassingEncounter with code displayName='Pneumonia'."""

    def test_nist_encounter_context_extraction(self) -> None:
        """Verify the encounter code.displayName is available in the conversion.

        NIST Ambulatory has no narrative sections or note activities, but the
        encompassingEncounter has code displayName='Pneumonia'. We validate
        that the conversion itself doesn't fail and that the encounter is created.
        """
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        # Should have an Encounter resource from encompassingEncounter
        encounters = [
            entry["resource"]
            for entry in bundle["entry"]
            if entry["resource"]["resourceType"] == "Encounter"
        ]
        assert len(encounters) >= 1


class TestEncounterDisplayFromParticipantSpecialty:
    """Athena CCD has encompassingEncounter without code but with participant specialty."""

    def test_athena_display_falls_back_to_participant_specialty(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        doc_refs = _get_doc_refs(bundle)
        assert len(doc_refs) >= 1

        for dr in doc_refs:
            if "context" not in dr or "encounter" not in dr["context"]:
                continue
            for enc_ref in dr["context"]["encounter"]:
                assert enc_ref.get("display") == "Family Medicine", (
                    f"Expected participant specialty fallback display, got: {enc_ref}"
                )


class TestEncounterDisplayEndToEnd:
    """End-to-end test using a minimal C-CDA with code on encompassingEncounter.

    This constructs a minimal C-CDA document with:
    - An encompassingEncounter with code displayName
    - A narrative section (HPI) to produce a DocumentReference
    And validates the display propagates to context.encounter[].display.
    """

    MINIMAL_CCDA = """\
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-id"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summary"/>
  <title>Test Document</title>
  <effectiveTime value="20260101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19" extension="patient-1"/>
      <addr><city>Test</city></addr>
      <telecom value="tel:555-1234"/>
      <patient>
        <name><given>Test</given><family>Patient</family></name>
        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20260101"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="auth-1"/>
      <assignedPerson><name><given>Dr</given><family>Test</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="2.16.840.1.113883.19" extension="enc-test-1"/>
      <code code="99213" codeSystem="2.16.840.1.113883.6.12"
            codeSystemName="CPT" displayName="Office or other outpatient visit"/>
      <effectiveTime value="20260101"/>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="1.3.6.1.4.1.19376.1.5.3.1.3.4"/>
          <code code="10164-2" codeSystem="2.16.840.1.113883.6.1"
                codeSystemName="LOINC" displayName="History of Present Illness"/>
          <title>History of Present Illness</title>
          <text>Patient presents with chest pain for 2 days.</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

    def test_display_on_narrative_section_doc_ref(self) -> None:
        result = convert_document(self.MINIMAL_CCDA)
        bundle = result["bundle"]

        doc_refs = _get_doc_refs(bundle)
        assert len(doc_refs) >= 1, "Expected at least one DocumentReference from HPI"

        hpi_refs = [
            dr for dr in doc_refs
            if dr.get("type", {}).get("coding", [{}])[0].get("code") == "10164-2"
        ]
        assert len(hpi_refs) == 1, "Expected exactly one HPI DocumentReference"

        hpi = hpi_refs[0]
        assert "context" in hpi, "HPI DocumentReference must have context"
        assert "encounter" in hpi["context"], "context must have encounter"

        enc_ref = hpi["context"]["encounter"][0]
        assert enc_ref["reference"].startswith("urn:uuid:"), (
            f"Encounter reference must be urn:uuid format: {enc_ref}"
        )
        assert enc_ref["display"] == "Office or other outpatient visit", (
            f"Expected display from encompassingEncounter code, got: {enc_ref}"
        )

    def test_display_absent_without_code_or_participant(self) -> None:
        """When encompassingEncounter has no code and no participants, display should be absent."""
        xml_no_code = self.MINIMAL_CCDA.replace(
            '<code code="99213" codeSystem="2.16.840.1.113883.6.12"\n'
            '            codeSystemName="CPT" displayName="Office or other outpatient visit"/>',
            "",
        )
        result = convert_document(xml_no_code)
        bundle = result["bundle"]

        doc_refs = _get_doc_refs(bundle)
        hpi_refs = [
            dr for dr in doc_refs
            if dr.get("type", {}).get("coding", [{}])[0].get("code") == "10164-2"
        ]
        assert len(hpi_refs) == 1

        enc_ref = hpi_refs[0]["context"]["encounter"][0]
        assert "display" not in enc_ref, (
            f"Without code or participants, display should be absent: {enc_ref}"
        )

    def test_display_falls_back_to_participant_specialty(self) -> None:
        """When no code but participant has specialty, display uses specialty."""
        xml_with_participant = self.MINIMAL_CCDA.replace(
            '<code code="99213" codeSystem="2.16.840.1.113883.6.12"\n'
            '            codeSystemName="CPT" displayName="Office or other outpatient visit"/>',
            "",
        ).replace(
            "<effectiveTime value=\"20260101\"/>\n    </encompassingEncounter>",
            '<effectiveTime value="20260101"/>\n'
            '      <encounterParticipant typeCode="ATND">\n'
            "        <assignedEntity>\n"
            '          <code code="207Q00000X" codeSystem="2.16.840.1.113883.6.101"\n'
            '                codeSystemName="NUCC" displayName="Family Medicine"/>\n'
            "        </assignedEntity>\n"
            "      </encounterParticipant>\n"
            "    </encompassingEncounter>",
        )
        result = convert_document(xml_with_participant)
        bundle = result["bundle"]

        doc_refs = _get_doc_refs(bundle)
        hpi_refs = [
            dr for dr in doc_refs
            if dr.get("type", {}).get("coding", [{}])[0].get("code") == "10164-2"
        ]
        assert len(hpi_refs) == 1

        enc_ref = hpi_refs[0]["context"]["encounter"][0]
        assert enc_ref["display"] == "Family Medicine", (
            f"Expected participant specialty fallback, got: {enc_ref}"
        )
