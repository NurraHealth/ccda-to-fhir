"""Integration tests for Referral conversion.

Tests end-to-end conversion of C-CDA referral entries to FHIR ServiceRequest
resources with referral category.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

# ============================================================================
# Test C-CDA Documents
# ============================================================================

CCDA_BASIC_REFERRAL = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="ref-doc-001"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Referral Test Document</title>
    <effectiveTime value="20240615120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5.99999" extension="patient-001"/>
            <patient>
                <name><given>John</given><family>Doe</family></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20240615120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
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
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of Treatment"/>
                    <title>Plan of Treatment</title>
                    <text>Referral to cardiology.</text>
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.39" extension="2022-06-01"/>
                            <id root="referral-id-001"/>
                            <code code="3457005" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Patient referral">
                                <originalText>Referral to cardiology for chest pain evaluation</originalText>
                            </code>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20240701"/>
                            </effectiveTime>
                            <author>
                                <time value="20240615140000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                                    <assignedPerson>
                                        <name><given>Dr</given><family>Author</family></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                            <performer>
                                <assignedEntity>
                                    <id root="2.16.840.1.113883.4.6" extension="5555555555"/>
                                    <assignedPerson>
                                        <name><given>Dr</given><family>Cardiologist</family></name>
                                    </assignedPerson>
                                </assignedEntity>
                            </performer>
                        </act>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""

CCDA_REFERRAL_ENCOUNTER = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="ref-doc-002"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Referral via Encounter Test</title>
    <effectiveTime value="20240615120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5.99999" extension="patient-002"/>
            <patient>
                <name><given>Jane</given><family>Smith</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19900315"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20240615120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
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
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of Treatment"/>
                    <title>Plan of Treatment</title>
                    <text>Referral to psychiatry planned.</text>
                    <entry typeCode="DRIV">
                        <encounter classCode="ENC" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.40" extension="2022-06-01"/>
                            <id root="referral-enc-001"/>
                            <code code="3457005" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Patient referral"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240801"/>
                        </encounter>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""

CCDA_MIXED_ENTRIES = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="mixed-doc-001"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Mixed Appointment and Referral Test</title>
    <effectiveTime value="20240615120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5.99999" extension="patient-003"/>
            <patient>
                <name><given>Bob</given><family>Jones</family></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19700501"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20240615120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
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
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of Treatment"/>
                    <title>Plan of Treatment</title>
                    <text>Appointment and referral.</text>
                    <!-- Appointment entry -->
                    <entry typeCode="DRIV">
                        <encounter classCode="ENC" moodCode="APT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.40" extension="2022-06-01"/>
                            <id root="mixed-appt-001"/>
                            <code code="185389009" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Follow-up visit"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240720"/>
                        </encounter>
                    </entry>
                    <!-- Referral entry -->
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.39" extension="2022-06-01"/>
                            <id root="mixed-ref-001"/>
                            <code code="306206005" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Referral to service"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240801"/>
                        </act>
                    </entry>
                    <!-- Non-referral planned act (should NOT become a referral) -->
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.39" extension="2022-06-01"/>
                            <id root="mixed-planned-001"/>
                            <code code="80146002" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Appendectomy"/>
                            <statusCode code="active"/>
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


def _find_resources(bundle: dict, resource_type: str) -> list[dict]:
    """Find all resources of a given type in a FHIR Bundle."""
    return [
        entry["resource"]
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == resource_type
    ]


class TestBasicReferral:
    """Test basic referral conversion end-to-end."""

    def test_referral_in_bundle(self):
        """Referral-coded Planned Act should produce exactly one ServiceRequest."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        # Exactly 1 referral ServiceRequest (no duplicates)
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) == 1

    def test_referral_has_category(self):
        """Referral ServiceRequest should have referral category."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) >= 1
        sr = referral_srs[0]
        assert sr["category"][0]["coding"][0]["display"] == "Patient referral"

    def test_referral_has_us_core_profile(self):
        """Should have US Core ServiceRequest profile."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) >= 1
        sr = referral_srs[0]
        assert "us-core-servicerequest" in sr["meta"]["profile"][0]

    def test_referral_status_active(self):
        """active → active."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) >= 1
        assert referral_srs[0]["status"] == "active"

    def test_referral_intent_order(self):
        """RQO → order."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) >= 1
        assert referral_srs[0]["intent"] == "order"

    def test_referral_has_authored_on(self):
        """Author time → authoredOn."""
        result = convert_document(CCDA_BASIC_REFERRAL)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(referral_srs) >= 1
        assert "authoredOn" in referral_srs[0]


class TestReferralEncounter:
    """Test referral via Planned Encounter (non-appointment moodCode)."""

    def test_encounter_referral_produces_service_request(self):
        """INT encounter with referral code → ServiceRequest (not Appointment)."""
        result = convert_document(CCDA_REFERRAL_ENCOUNTER)
        bundle = result["bundle"]
        appointments = _find_resources(bundle, "Appointment")
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(appointments) == 0
        assert len(referral_srs) >= 1


class TestMixedEntries:
    """Test document with both appointment and referral entries."""

    def test_appointment_and_referral_both_present(self):
        """Mixed doc should produce both Appointment and referral ServiceRequest."""
        result = convert_document(CCDA_MIXED_ENTRIES)
        bundle = result["bundle"]
        appointments = _find_resources(bundle, "Appointment")
        service_requests = _find_resources(bundle, "ServiceRequest")
        referral_srs = [
            sr
            for sr in service_requests
            if any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(appointments) == 1
        assert len(referral_srs) >= 1

    def test_non_referral_act_not_converted_as_referral(self):
        """Non-referral Planned Act should not get referral category."""
        result = convert_document(CCDA_MIXED_ENTRIES)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        # The non-referral planned act (Appendectomy) should be a ServiceRequest
        # but without referral category
        non_referral_srs = [
            sr
            for sr in service_requests
            if not any(
                cat.get("coding", [{}])[0].get("code") == "3457005"
                for cat in sr.get("category", [])
            )
        ]
        assert len(non_referral_srs) >= 1
