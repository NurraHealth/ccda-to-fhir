"""Integration tests for Patient Referral Act (template .140) conversion.

Tests end-to-end conversion of C-CDA Patient Referral Act entries
(2.16.840.1.113883.10.20.22.4.140) to FHIR ServiceRequest resources
with referral category.

This template is distinct from Planned Act (.39) and is used by EHRs like
Athena to represent referrals in the "Reason for Referral" section.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

# ============================================================================
# Test C-CDA Documents
# ============================================================================

CCDA_PATIENT_REFERRAL_ACT = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="pra-doc-001"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Patient Referral Act Test</title>
    <effectiveTime value="20260120120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5.99999" extension="patient-pra-001"/>
            <patient>
                <name><given>Alice</given><family>Johnson</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19650315"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20260120120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
            <assignedPerson><name><given>Maria</given><family>Santos</family></name></assignedPerson>
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
            <!-- Reason for Referral Section (LOINC 42349-1) -->
            <component>
                <section>
                    <templateId extension="2014-06-09" root="1.3.6.1.4.1.19376.1.5.3.1.3.1"/>
                    <code code="42349-1" codeSystem="2.16.840.1.113883.6.1"
                          codeSystemName="LOINC" displayName="Reason for Referral"/>
                    <title>Reason for Referral</title>
                    <text>Referral entries.</text>
                    <entry>
                        <!--Patient Referral Act-->
                        <act classCode="PCPR" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.140"/>
                            <id root="e348b06b-6e2f-4737-880f-53a9d8e93ed1"/>
                            <code code="308476000" codeSystem="2.16.840.1.113883.6.96"
                                  codeSystemName="SNOMED CT" displayName="Referral to gastroenterologist"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20260120170317-0500"/>
                            <entryRelationship typeCode="RSON">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId extension="2023-05-01" root="2.16.840.1.113883.10.20.22.4.19"/>
                                    <id root="6f349b6f-a1db-4543-b7d2-663f138942ac"/>
                                    <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
                                          codeSystemName="SNOMED CT" displayName="Clinical finding"/>
                                    <statusCode code="completed"/>
                                    <value code="275978004" codeSystem="2.16.840.1.113883.6.96"
                                           codeSystemName="SNOMED CT"
                                           displayName="Screening for malignant neoplasm of colon"
                                           xsi:type="CD"/>
                                </observation>
                            </entryRelationship>
                        </act>
                    </entry>
                    <entry>
                        <!--Patient Referral Act-->
                        <act classCode="PCPR" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.140"/>
                            <id root="2abacc90-f90c-4c00-9c50-afb7ae838641"/>
                            <code code="444831000124102" codeSystem="2.16.840.1.113883.6.96"
                                  codeSystemName="SNOMED CT" displayName="Referral for physical therapy"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20260120165545-0500"/>
                            <entryRelationship typeCode="RSON">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId extension="2023-05-01" root="2.16.840.1.113883.10.20.22.4.19"/>
                                    <id root="ff7cf4f5-3d3d-4952-bf4e-b7130594037c"/>
                                    <code code="404684003" codeSystem="2.16.840.1.113883.6.96"
                                          codeSystemName="SNOMED CT" displayName="Clinical finding"/>
                                    <statusCode code="completed"/>
                                    <value code="16003671000119101" codeSystem="2.16.840.1.113883.6.96"
                                           codeSystemName="SNOMED CT"
                                           displayName="Tendinitis of left rotator cuff"
                                           xsi:type="CD"/>
                                </observation>
                            </entryRelationship>
                        </act>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""

CCDA_MIXED_REFERRAL_TEMPLATES = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="mixed-pra-doc"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Mixed Referral Templates</title>
    <effectiveTime value="20260120120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5.99999" extension="patient-mixed-001"/>
            <patient>
                <name><given>Bob</given><family>Smith</family></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19700501"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20260120120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
            <assignedPerson><name><given>Dr</given><family>Author</family></name></assignedPerson>
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
            <!-- Plan of Treatment with Planned Act referral -->
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of Treatment"/>
                    <title>Plan of Treatment</title>
                    <text>Plan of treatment referral.</text>
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.39" extension="2022-06-01"/>
                            <id root="planned-act-ref-001"/>
                            <code code="3457005" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Patient referral"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20260201"/>
                        </act>
                    </entry>
                </section>
            </component>
            <!-- Reason for Referral with Patient Referral Act -->
            <component>
                <section>
                    <templateId extension="2014-06-09" root="1.3.6.1.4.1.19376.1.5.3.1.3.1"/>
                    <code code="42349-1" codeSystem="2.16.840.1.113883.6.1" displayName="Reason for Referral"/>
                    <title>Reason for Referral</title>
                    <text>Patient referral act entry.</text>
                    <entry>
                        <act classCode="PCPR" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.140"/>
                            <id root="patient-ref-act-001"/>
                            <code code="308476000" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Referral to gastroenterologist"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20260115"/>
                        </act>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""


# ============================================================================
# Tests
# ============================================================================


class TestPatientReferralActConversion:
    """Test Patient Referral Act (template .140) → FHIR ServiceRequest."""

    def test_basic_referral_act_produces_service_requests(self):
        """Patient Referral Act entries convert to ServiceRequest with referral category."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]
        entries = bundle.get("entry", [])

        service_requests = [
            e["resource"] for e in entries if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        assert len(service_requests) == 2

    def test_referral_category_present(self):
        """Each ServiceRequest has referral category (SNOMED 3457005)."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            categories = sr.get("category", [])
            referral_codings = [
                coding
                for cat in categories
                for coding in cat.get("coding", [])
                if coding.get("code") == "3457005"
            ]
            assert len(referral_codings) > 0, (
                f"ServiceRequest missing referral category: {sr.get('code', {})}"
            )

    def test_referral_codes_preserved(self):
        """SNOMED referral codes from the C-CDA are preserved in ServiceRequest.code."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        codes = {
            sr["code"]["coding"][0]["code"]
            for sr in service_requests
            if sr.get("code", {}).get("coding")
        }
        assert "308476000" in codes, "Missing gastroenterologist referral code"
        assert "444831000124102" in codes, "Missing physical therapy referral code"

    def test_referral_display_text(self):
        """Referral display text is preserved from C-CDA code displayName."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        displays = {
            sr["code"]["coding"][0]["display"]
            for sr in service_requests
            if sr.get("code", {}).get("coding")
        }
        assert "Referral to gastroenterologist" in displays
        assert "Referral for physical therapy" in displays

    def test_status_mapped(self):
        """C-CDA statusCode=active maps to FHIR status=active."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            assert sr["status"] == "active"

    def test_intent_from_mood_code(self):
        """C-CDA moodCode=INT maps to FHIR intent=plan."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            assert sr["intent"] == "plan"

    def test_us_core_profile(self):
        """ServiceRequests have US Core ServiceRequest profile."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            profiles = sr.get("meta", {}).get("profile", [])
            assert any("us-core-servicerequest" in p for p in profiles), (
                "ServiceRequest missing US Core profile"
            )

    def test_subject_reference(self):
        """Each ServiceRequest references the patient."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            assert "subject" in sr, "ServiceRequest missing subject"
            assert "reference" in sr["subject"], "Subject missing reference"

    def test_template_not_in_skipped(self):
        """Patient Referral Act template should not appear in skipped_templates."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        metadata = result["metadata"]

        skipped = metadata.get("skipped_templates", [])
        assert "2.16.840.1.113883.10.20.22.4.140" not in skipped, (
            "Patient Referral Act should be processed, not skipped"
        )

    def test_reason_codes_extracted(self):
        """Indication entryRelationships produce reasonCode on ServiceRequest."""
        result = convert_document(CCDA_PATIENT_REFERRAL_ACT)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        # At least one SR should have reasonCode from the indication
        srs_with_reasons = [sr for sr in service_requests if sr.get("reasonCode")]
        assert len(srs_with_reasons) > 0, "Expected at least one ServiceRequest with reasonCode"


class TestMixedReferralTemplates:
    """Test documents with both Planned Act (.39) and Patient Referral Act (.140) referrals."""

    def test_both_templates_produce_referrals(self):
        """Both Planned Act and Patient Referral Act entries produce ServiceRequests."""
        result = convert_document(CCDA_MIXED_REFERRAL_TEMPLATES)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        assert len(service_requests) == 2, (
            f"Expected 2 ServiceRequests (1 Planned Act + 1 Patient Referral Act), "
            f"got {len(service_requests)}"
        )

    def test_all_have_referral_category(self):
        """ServiceRequests from both templates have referral category."""
        result = convert_document(CCDA_MIXED_REFERRAL_TEMPLATES)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        for sr in service_requests:
            categories = sr.get("category", [])
            has_referral = any(
                coding.get("code") == "3457005"
                for cat in categories
                for coding in cat.get("coding", [])
            )
            assert has_referral, f"ServiceRequest missing referral category: {sr.get('code')}"

    def test_distinct_identifiers(self):
        """Each ServiceRequest has unique identifiers."""
        result = convert_document(CCDA_MIXED_REFERRAL_TEMPLATES)
        bundle = result["bundle"]

        service_requests = [
            e["resource"]
            for e in bundle["entry"]
            if e["resource"]["resourceType"] == "ServiceRequest"
        ]
        ids = [sr["id"] for sr in service_requests]
        assert len(set(ids)) == len(ids), f"Duplicate ServiceRequest IDs: {ids}"
