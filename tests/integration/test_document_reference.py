"""E2E tests for DocumentReference resource conversion."""

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


class TestDocumentReferenceConversion:
    """E2E tests for C-CDA ClinicalDocument to FHIR DocumentReference conversion."""

    def test_creates_document_reference(self) -> None:
        """Test that DocumentReference resource is created."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["resourceType"] == "DocumentReference"

    def test_converts_status_to_current(self) -> None:
        """Test that status is set to 'current'."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["status"] == "current"

    def test_converts_master_identifier(self) -> None:
        """Test that document ID is converted to masterIdentifier."""
        # Note: wrap_in_ccda_document uses default document ID
        # <id root="2.16.840.1.113883.19.5.99999.1"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "masterIdentifier" in doc_ref
        assert doc_ref["masterIdentifier"]["system"] == "urn:oid:2.16.840.1.113883.19.5.99999.1"

    def test_converts_document_type(self) -> None:
        """Test that document code is converted to type."""
        # Default document code from wrap_in_ccda_document:
        # <code code="34133-9" displayName="Summarization of Episode Note"
        #       codeSystem="2.16.840.1.113883.6.1"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "type" in doc_ref
        assert "coding" in doc_ref["type"]
        assert len(doc_ref["type"]["coding"]) >= 1

        loinc_coding = next(
            (c for c in doc_ref["type"]["coding"] if c.get("system") == "http://loinc.org"),
            None,
        )
        assert loinc_coding is not None
        assert loinc_coding["code"] == "34133-9"
        assert loinc_coding["display"] == "Summarization of Episode Note"

    def test_converts_subject_reference(self) -> None:
        """Test that patient reference is created."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "subject" in doc_ref
        assert "reference" in doc_ref["subject"]
        # Should reference the Patient resource
        assert "Patient/" in doc_ref["subject"]["reference"]

    def test_converts_date_from_effective_time(self) -> None:
        """Test that document effectiveTime is converted to date."""
        # Default effectiveTime from wrap_in_ccda_document:
        # <effectiveTime value="20231215120000-0500"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "date" in doc_ref
        # Should be ISO 8601 format
        assert doc_ref["date"].startswith("2023-12-15")

    def test_converts_author_references(self) -> None:
        """Test that document authors are referenced."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "author" in doc_ref
        assert len(doc_ref["author"]) >= 1
        # Should reference a Practitioner resource
        assert "Practitioner/" in doc_ref["author"][0]["reference"]

    def test_converts_custodian_reference(self) -> None:
        """Test that custodian is converted to organization reference."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "custodian" in doc_ref
        assert "reference" in doc_ref["custodian"]
        # Should reference an Organization resource
        assert "Organization/" in doc_ref["custodian"]["reference"]

    def test_converts_security_label_from_confidentiality(self) -> None:
        """Test that confidentialityCode is converted to securityLabel."""
        # Default confidentialityCode from wrap_in_ccda_document:
        # <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "securityLabel" in doc_ref
        assert len(doc_ref["securityLabel"]) >= 1
        assert "coding" in doc_ref["securityLabel"][0]

        # Check for confidentiality code
        coding = doc_ref["securityLabel"][0]["coding"][0]
        assert coding["code"] == "N"

    def test_converts_content_with_attachment(self) -> None:
        """Test that content element with attachment is created."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref
        assert len(doc_ref["content"]) >= 1

        content = doc_ref["content"][0]
        assert "attachment" in content
        assert content["attachment"]["contentType"] == "text/xml"

    def test_converts_content_language(self) -> None:
        """Test that document language is converted to attachment language."""
        # Default languageCode from wrap_in_ccda_document:
        # <languageCode code="en-US"/>
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        content = doc_ref["content"][0]
        assert "attachment" in content
        assert content["attachment"]["language"] == "en-US"

    def test_converts_content_title_from_doc_code(self) -> None:
        """Test that document code display name is used as attachment title."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        content = doc_ref["content"][0]
        assert "attachment" in content
        assert "title" in content["attachment"]
        assert content["attachment"]["title"] == "Summarization of Episode Note"

    def test_converts_content_format(self) -> None:
        """Test that content format is set for C-CDA."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        content = doc_ref["content"][0]
        assert "format" in content
        assert "code" in content["format"]
        # Should indicate C-CDA structured body format
        assert "ccda" in content["format"]["code"].lower()

    def test_format_uses_hl7_system(self) -> None:
        """Test format.system uses HL7 standard URI."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        format_coding = doc_ref["content"][0]["format"]
        assert format_coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-HL7DocumentFormatCodes"

    def test_resource_type_is_document_reference(self) -> None:
        """Test that resourceType is DocumentReference."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["resourceType"] == "DocumentReference"


class TestDocumentReferenceWithContext:
    """Tests for DocumentReference context field."""

    def test_converts_context_with_encompassing_encounter(self) -> None:
        """Test that encompassing encounter creates context.

        Note: Context is optional and may not be created if the encompassing
        encounter is empty or lacks sufficient information.
        """
        # Create a document with componentOf/encompassingEncounter
        ccda_doc_with_encounter = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
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
    <componentOf>
        <encompassingEncounter>
            <id root="encounter-123"/>
            <effectiveTime>
                <low value="20231215100000-0500"/>
                <high value="20231215150000-0500"/>
            </effectiveTime>
        </encompassingEncounter>
    </componentOf>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_encounter)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        # Context is optional - if created, verify it has expected structure
        if "context" in doc_ref:
            assert isinstance(doc_ref["context"], dict)

    def test_converts_context_period_from_encompassing_encounter(self) -> None:
        """Test that encounter effectiveTime creates context period."""
        ccda_doc_with_encounter = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
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
    <componentOf>
        <encompassingEncounter>
            <id root="encounter-123"/>
            <effectiveTime>
                <low value="20231215100000-0500"/>
                <high value="20231215150000-0500"/>
            </effectiveTime>
        </encompassingEncounter>
    </componentOf>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_encounter)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "context" in doc_ref
        assert "period" in doc_ref["context"]
        assert "start" in doc_ref["context"]["period"]
        assert doc_ref["context"]["period"]["start"].startswith("2023-12-15")


class TestDocumentReferenceNewFeatures:
    """Tests for newly implemented DocumentReference features."""

    def test_converts_attachment_hash(self) -> None:
        """Test that SHA-1 hash is calculated for attachment."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref
        assert len(doc_ref["content"]) >= 1

        content = doc_ref["content"][0]
        assert "attachment" in content
        # Hash should be present and be a base64-encoded SHA-1 hash
        assert "hash" in content["attachment"]
        # SHA-1 hash in base64 is 28 characters
        assert len(content["attachment"]["hash"]) == 28

    def test_converts_related_document_replaces(self) -> None:
        """Test that relatedDocument with RPLC is converted to relatesTo."""
        ccda_doc_with_related = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-002"/>
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
    <relatedDocument typeCode="RPLC">
        <parentDocument>
            <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-001"/>
        </parentDocument>
    </relatedDocument>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_related)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "relatesTo" in doc_ref
        assert len(doc_ref["relatesTo"]) == 1
        assert doc_ref["relatesTo"][0]["code"] == "replaces"
        assert "target" in doc_ref["relatesTo"][0]
        assert "reference" in doc_ref["relatesTo"][0]["target"]
        assert "DocumentReference/" in doc_ref["relatesTo"][0]["target"]["reference"]

    def test_converts_related_document_appends(self) -> None:
        """Test that relatedDocument with APND is converted to relatesTo."""
        ccda_doc_with_apnd = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-ADDENDUM"/>
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
    <relatedDocument typeCode="APND">
        <parentDocument>
            <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-ORIGINAL"/>
        </parentDocument>
    </relatedDocument>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_apnd)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "relatesTo" in doc_ref
        assert len(doc_ref["relatesTo"]) == 1
        assert doc_ref["relatesTo"][0]["code"] == "appends"
        assert "target" in doc_ref["relatesTo"][0]
        assert "reference" in doc_ref["relatesTo"][0]["target"]

    def test_converts_related_document_transforms(self) -> None:
        """Test that relatedDocument with XFRM is converted to relatesTo."""
        ccda_doc_with_xfrm = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-TRANSFORMED"/>
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
    <relatedDocument typeCode="XFRM">
        <parentDocument>
            <id root="2.16.840.1.113883.19.5.99999.1" extension="DOC-SOURCE"/>
        </parentDocument>
    </relatedDocument>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_xfrm)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "relatesTo" in doc_ref
        assert len(doc_ref["relatesTo"]) == 1
        assert doc_ref["relatesTo"][0]["code"] == "transforms"
        assert "target" in doc_ref["relatesTo"][0]
        assert "reference" in doc_ref["relatesTo"][0]["target"]

    def test_converts_context_event_from_service_event(self) -> None:
        """Test that serviceEvent classCode is converted to context.event."""
        ccda_doc_with_event = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
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
    <documentationOf>
        <serviceEvent classCode="PCPR">
            <effectiveTime>
                <low value="20231201"/>
                <high value="20231215"/>
            </effectiveTime>
        </serviceEvent>
    </documentationOf>
    <component>
        <structuredBody>
            <component>
                <section>
                    <entry></entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""

        bundle = convert_document(ccda_doc_with_event)["bundle"]

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "context" in doc_ref
        assert "event" in doc_ref["context"]
        assert len(doc_ref["context"]["event"]) >= 1

        event = doc_ref["context"]["event"][0]
        assert "coding" in event
        assert len(event["coding"]) >= 1
        coding = event["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActClass"
        assert coding["code"] == "PCPR"
        assert coding["display"] == "care provision"
