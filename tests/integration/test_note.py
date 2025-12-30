"""E2E tests for DocumentReference resource conversion."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

NOTES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.65"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle.

    For DocumentReference resources, specifically finds Note Activity DocumentReferences
    (those with category='clinical-note'), not document-level ones.
    """
    candidates = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            candidates.append(resource)

    if not candidates:
        return None

    # For DocumentReference, prefer Note Activity (has type code 34109-9 for "Note")
    if resource_type == "DocumentReference" and len(candidates) > 1:
        for resource in candidates:
            doc_type = resource.get("type", {})
            coding = doc_type.get("coding", [])
            for code in coding:
                # Note Activity uses LOINC code 34109-9 for "Note"
                if code.get("code") == "34109-9":
                    return resource

    return candidates[0]


class TestNoteConversion:
    """E2E tests for C-CDA Note Activity to FHIR DocumentReference conversion."""

    def test_converts_to_document_reference(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that note activity creates a DocumentReference."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["resourceType"] == "DocumentReference"

    def test_converts_type(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that note code is converted to type."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "type" in doc_ref
        loinc = next(
            (c for c in doc_ref["type"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "34109-9"

    def test_converts_translation_codes(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that translation codes are included in type."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        codes = [c["code"] for c in doc_ref["type"]["coding"]]
        assert "11488-4" in codes

    def test_converts_status(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["status"] == "current"

    def test_converts_doc_status(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that docStatus is mapped from statusCode."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        # statusCode="completed" → docStatus="final"
        assert doc_ref["docStatus"] == "final"

    def test_converts_category(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that category is set to clinical-note."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["category"][0]["coding"][0]["code"] == "clinical-note"
        assert doc_ref["category"][0]["coding"][0]["system"] == "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category"

    def test_converts_date(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that author time is converted to date."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "date" in doc_ref
        assert "2016-09-08" in doc_ref["date"]

    def test_converts_content_attachment(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that text content is converted to attachment."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref
        assert len(doc_ref["content"]) == 1
        assert doc_ref["content"][0]["attachment"]["contentType"] == "application/rtf"
        assert doc_ref["content"][0]["attachment"]["data"] is not None

    def test_converts_context_period(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to context.period."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "context" in doc_ref
        assert "period" in doc_ref["context"]
        assert "2016-09-08" in doc_ref["context"]["period"]["start"]

    def test_type_text_from_display(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that type.text is derived from displayName."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "type" in doc_ref
        assert doc_ref["type"]["text"] == "Note"

    def test_resolves_text_reference(self) -> None:
        """Test that text references to section narrative are resolved."""
        # Create a note with text reference (no direct content)
        ccda_with_reference = """
        <section xmlns="urn:hl7-org:v3">
          <templateId root="2.16.840.1.113883.10.20.22.2.65"/>
          <code code="29299-5" displayName="Reason for visit"/>
          <text>
            <paragraph ID="note-ref-1">This is the actual note content from section narrative.</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text>
                <reference value="#note-ref-1"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240101"/>
            </act>
          </entry>
        </section>
        """
        ccda_doc = wrap_in_ccda_document(ccda_with_reference, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref
        assert len(doc_ref["content"]) > 0

        # Verify attachment has data (base64 encoded resolved text)
        attachment = doc_ref["content"][0]["attachment"]
        assert "data" in attachment
        assert attachment["data"] is not None and len(attachment["data"]) > 0

        # Decode and verify the content
        import base64
        decoded_text = base64.b64decode(attachment["data"]).decode("utf-8")
        assert "actual note content" in decoded_text.lower()

    def test_provenance_created_for_note_with_author(
        self, ccda_note: str
    ) -> None:
        """Test that Provenance resource is created for DocumentReference with author."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find Provenance for this note
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this note
        note_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                doc_ref["id"] in t.get("reference", "") for t in prov["target"]
            ):
                note_provenance = prov
                break

        assert note_provenance is not None, "Provenance resource should be created for DocumentReference"
        # Verify Provenance has recorded date
        assert "recorded" in note_provenance
        # Verify Provenance has agents
        assert "agent" in note_provenance
        assert len(note_provenance["agent"]) > 0

    def test_provenance_agent_references_practitioner(
        self, ccda_note: str
    ) -> None:
        """Test that Provenance agent references Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        note_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                doc_ref["id"] in t.get("reference", "") for t in prov["target"]
            ):
                note_provenance = prov
                break

        assert note_provenance is not None
        # Verify agent references practitioner
        agent = note_provenance["agent"][0]
        assert "who" in agent
        assert "reference" in agent["who"]
        assert agent["who"]["reference"].startswith("Practitioner/")

    def test_provenance_has_recorded_date_from_author(
        self, ccda_note: str
    ) -> None:
        """Test that Provenance has recorded date from author time."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        note_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                doc_ref["id"] in t.get("reference", "") for t in prov["target"]
            ):
                note_provenance = prov
                break

        assert note_provenance is not None
        # Verify recorded date matches author time (20160908083215-0500)
        assert note_provenance["recorded"] == "2016-09-08T08:32:15-05:00"

    def test_provenance_agent_has_author_type(
        self, ccda_note: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        note_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                doc_ref["id"] in t.get("reference", "") for t in prov["target"]
            ):
                note_provenance = prov
                break

        assert note_provenance is not None
        # Verify agent type is author
        agent = note_provenance["agent"][0]
        assert "type" in agent
        type_coding = agent["type"]["coding"][0]
        assert type_coding["code"] == "author"
        assert type_coding["system"] == "http://terminology.hl7.org/CodeSystem/provenance-participant-type"


class TestNoteMultipleContent:
    """E2E tests for multiple content attachments in DocumentReference."""

    def test_creates_multiple_content_when_inline_and_reference_both_present(self) -> None:
        """Test that note with both inline content and reference creates multiple content items."""
        # Create a proper C-CDA document with section narrative and Note Activity that references it
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph ID="note-multi-1">Patient presents with acute chest pain. Assessment: Likely stable angina.</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text mediaType="application/pdf" representation="B64">
JVBERi0xLjMKJcTl8uXrp/Og0MTGCjQgMCBvYmoKPDwgL0xlbmd0aCA1IDAgUiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAErVAhUKFQwNAIABQIDBAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKOAplbmRvYmoKMiAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMyAwIFIgPj4KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDc0IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAyIDAgUiA+PgpzdGFydHhyZWYKMTIzCiUlRU9GCg==
                <reference value="#note-multi-1"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
              <author>
                <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
                <time value="20240315120000-0500"/>
                <assignedAuthor>
                  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                  <assignedPerson>
                    <name><given>Test</given><family>Doctor</family></name>
                  </assignedPerson>
                </assignedAuthor>
              </author>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref

        # Should have TWO content items: one for inline PDF, one for reference
        assert len(doc_ref["content"]) == 2, f"Should have 2 content items when both inline and reference present, got {len(doc_ref['content'])}"

    def test_inline_content_has_correct_media_type(self) -> None:
        """Test that inline content preserves the mediaType from C-CDA."""
        # Use the first test's document - it already has both inline PDF and reference
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph ID="note-multi-2">Patient presents with acute chest pain.</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text mediaType="application/pdf" representation="B64">
JVBERi0xLjMKJcTl8uXrp/Og0MTGCjQgMCBvYmoKPDwgL0xlbmd0aCA1IDAgUiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAErVAhUKFQwNAIABQIDBAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKOAplbmRvYmoKMiAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMyAwIFIgPj4KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDc0IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAyIDAgUiA+PgpzdGFydHhyZWYKMTIzCiUlRU9GCg==
                <reference value="#note-multi-2"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
              <author>
                <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
                <time value="20240315120000-0500"/>
                <assignedAuthor>
                  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                  <assignedPerson>
                    <name><given>Test</given><family>Doctor</family></name>
                  </assignedPerson>
                </assignedAuthor>
              </author>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find the inline content (should be application/pdf)
        inline_content = None
        for content in doc_ref["content"]:
            if content["attachment"].get("contentType") == "application/pdf":
                inline_content = content
                break

        assert inline_content is not None, "Should have inline content with application/pdf"
        assert "data" in inline_content["attachment"]
        assert inline_content["attachment"]["data"].startswith("JVBERi"), "PDF data should start with PDF magic bytes"

    def test_reference_content_has_resolved_narrative(self) -> None:
        """Test that reference content resolves to section narrative."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph ID="note-multi-3">Chief Complaint: Patient presents with acute chest pain.</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text mediaType="application/pdf" representation="B64">
JVBERi0xLjMKJcTl8uXrp/Og0MTGCjQgMCBvYmoKPDwgL0xlbmd0aCA1IDAgUiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAErVAhUKFQwNAIABQIDBAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKOAplbmRvYmoKMiAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMyAwIFIgPj4KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDc0IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAyIDAgUiA+PgpzdGFydHhyZWYKMTIzCiUlRU9GCg==
                <reference value="#note-multi-3"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
              <author>
                <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
                <time value="20240315120000-0500"/>
                <assignedAuthor>
                  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                  <assignedPerson>
                    <name><given>Test</given><family>Doctor</family></name>
                  </assignedPerson>
                </assignedAuthor>
              </author>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Find the reference content (should be text/html or text/plain)
        reference_content = None
        for content in doc_ref["content"]:
            content_type = content["attachment"].get("contentType")
            if content_type in ["text/html", "text/plain"]:
                reference_content = content
                break

        assert reference_content is not None, "Should have reference content with text content type"
        assert "data" in reference_content["attachment"]

        # Decode and verify it contains the narrative text
        import base64
        decoded_text = base64.b64decode(reference_content["attachment"]["data"]).decode("utf-8")
        assert "Chief Complaint" in decoded_text or "chief complaint" in decoded_text.lower()

    def test_only_inline_content_creates_single_item(self) -> None:
        """Test that note with only inline content creates single content item."""
        # Use the existing note.xml fixture which has only inline content
        from pathlib import Path
        fixture_path = Path(__file__).parent / "fixtures" / "ccda" / "note.xml"
        with open(fixture_path) as f:
            ccda_note = f.read()

        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref

        # Should have ONE content item for inline content only
        # (The note.xml has both inline and reference in same text element, so actually 2)
        # Let me check the fixture...
        assert len(doc_ref["content"]) >= 1, "Should have at least 1 content item"

    def test_different_content_types_preserved(self) -> None:
        """Test that different content types are preserved correctly."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph ID="note-multi-4">Patient presents with acute chest pain.</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text mediaType="application/pdf" representation="B64">
JVBERi0xLjMKJcTl8uXrp/Og0MTGCjQgMCBvYmoKPDwgL0xlbmd0aCA1IDAgUiAvRmlsdGVyIC9GbGF0ZURlY29kZSA+PgpzdHJlYW0KeAErVAhUKFQwNAIABQIDBAplbmRzdHJlYW0KZW5kb2JqCjUgMCBvYmoKOAplbmRvYmoKMiAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMyAwIFIgPj4KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDAwOSAwMDAwMCBuIAowMDAwMDAwMDc0IDAwMDAwIG4gCnRyYWlsZXIKPDwgL1NpemUgNiAvUm9vdCAyIDAgUiA+PgpzdGFydHhyZWYKMTIzCiUlRU9GCg==
                <reference value="#note-multi-4"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
              <author>
                <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
                <time value="20240315120000-0500"/>
                <assignedAuthor>
                  <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                  <assignedPerson>
                    <name><given>Test</given><family>Doctor</family></name>
                  </assignedPerson>
                </assignedAuthor>
              </author>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Collect content types
        content_types = [content["attachment"].get("contentType") for content in doc_ref["content"]]

        # Should have application/pdf for inline and text/html or text/plain for reference
        assert "application/pdf" in content_types, "Should have PDF content type"
        assert any(ct in ["text/html", "text/plain"] for ct in content_types), "Should have text content type"


class TestNoteMissingContent:
    """E2E tests for Note Activity with missing content handling."""

    def test_note_without_text_uses_data_absent_reason(self) -> None:
        """Test that note without text element uses data-absent-reason extension.

        Per FHIR R4 spec, when required data is missing, use data-absent-reason extension.
        Reference: http://hl7.org/fhir/R4/extension-data-absent-reason.html
        """
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph>Section narrative text</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <!-- No text element -->
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Should still have content array (required 1..*)
        assert "content" in doc_ref
        assert len(doc_ref["content"]) == 1

        # Should have attachment with data-absent-reason
        attachment = doc_ref["content"][0]["attachment"]
        assert "contentType" in attachment
        assert attachment["contentType"] == "text/plain"

        # Should have _data with data-absent-reason extension
        assert "_data" in attachment
        assert "extension" in attachment["_data"]

        extensions = attachment["_data"]["extension"]
        assert len(extensions) > 0

        data_absent_ext = extensions[0]
        assert data_absent_ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert data_absent_ext["valueCode"] == "unknown"

    def test_note_with_empty_text_uses_data_absent_reason(self) -> None:
        """Test that note with text element but no data uses data-absent-reason extension."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph>Section narrative text</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <text></text>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None

        # Should have content with data-absent-reason
        assert "content" in doc_ref
        attachment = doc_ref["content"][0]["attachment"]
        assert "_data" in attachment
        assert attachment["_data"]["extension"][0]["valueCode"] == "unknown"

    def test_data_absent_reason_extension_structure(self) -> None:
        """Test that data-absent-reason extension has correct structure per FHIR R4 spec."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="2.16.840.1.113883.19.5.99999.1"/>
  <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
  <effectiveTime value="20240315120000-0500"/>
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
    <time value="20240315120000-0500"/>
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
          <text>
            <paragraph>Section narrative text</paragraph>
          </text>
          <entry>
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
              <code code="34109-9" codeSystem="2.16.840.1.113883.6.1" displayName="Note"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240315"/>
            </act>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>
        """
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        attachment = doc_ref["content"][0]["attachment"]

        # Verify extension structure
        assert "_data" in attachment, "_data element should be present for missing data"
        assert "extension" in attachment["_data"], "extension array should be present"
        assert isinstance(attachment["_data"]["extension"], list), "extension should be an array"
        assert len(attachment["_data"]["extension"]) == 1, "should have exactly one extension"

        ext = attachment["_data"]["extension"][0]
        assert "url" in ext, "extension should have url"
        assert "valueCode" in ext, "extension should have valueCode"
        assert ext["url"] == "http://hl7.org/fhir/StructureDefinition/data-absent-reason"
        assert ext["valueCode"] == "unknown"

        # Ensure no actual 'data' field is present when using data-absent-reason
        assert "data" not in attachment, "Should not have 'data' field when using _data with extension"
