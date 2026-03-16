"""Integration tests for Appointment conversion.

Tests end-to-end conversion of C-CDA Planned Encounter entries with
appointment moodCodes to FHIR Appointment resources.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

# ============================================================================
# Test C-CDA Documents
# ============================================================================

CCDA_BASIC_APPOINTMENT = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="appt-doc-001"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Appointment Test Document</title>
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
                    <text>Follow-up appointment scheduled.</text>
                    <entry typeCode="DRIV">
                        <encounter classCode="ENC" moodCode="APT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.40" extension="2022-06-01"/>
                            <id root="appt-id-001"/>
                            <code code="185389009" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Follow-up visit"/>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20240715100000-0500"/>
                                <high value="20240715110000-0500"/>
                            </effectiveTime>
                            <performer>
                                <assignedEntity>
                                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                                    <assignedPerson>
                                        <name><given>Sarah</given><family>Smith</family></name>
                                    </assignedPerson>
                                </assignedEntity>
                            </performer>
                            <author>
                                <time value="20240601140000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                                    <assignedPerson>
                                        <name><given>Dr</given><family>Author</family></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                        </encounter>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""

CCDA_APPOINTMENT_REQUEST = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5" extension="appt-doc-002"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Appointment Request Test</title>
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
                    <text>Consultation requested.</text>
                    <entry typeCode="DRIV">
                        <encounter classCode="ENC" moodCode="ARQ">
                            <templateId root="2.16.840.1.113883.10.20.22.4.40" extension="2022-06-01"/>
                            <id root="appt-id-002"/>
                            <code code="11429006" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Consultation"/>
                            <statusCode code="new"/>
                            <effectiveTime value="20240801"/>
                            <priorityCode code="UR" codeSystem="2.16.840.1.113883.5.7"
                                          displayName="Urgent"/>
                        </encounter>
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


class TestBasicAppointment:
    """Test basic appointment conversion end-to-end."""

    def test_appointment_in_bundle(self):
        """Planned Encounter with APT moodCode should produce Appointment."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appointments = _find_resources(bundle, "Appointment")
        assert len(appointments) == 1

    def test_appointment_status_booked(self):
        """APT + active → booked."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert appt["status"] == "booked"

    def test_appointment_has_start_end(self):
        """effectiveTime low/high → start/end."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert "start" in appt
        assert "end" in appt

    def test_appointment_has_service_type(self):
        """Encounter code → serviceType."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert "serviceType" in appt
        assert appt["serviceType"][0]["coding"][0]["code"] == "185389009"

    def test_appointment_has_participant(self):
        """Should have at least patient and performer participants."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert "participant" in appt
        assert len(appt["participant"]) >= 2

    def test_appointment_has_created(self):
        """Author time → created."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert "created" in appt

    def test_no_service_request_for_apt(self):
        """APT encounter should NOT produce a ServiceRequest."""
        result = convert_document(CCDA_BASIC_APPOINTMENT)
        bundle = result["bundle"]
        service_requests = _find_resources(bundle, "ServiceRequest")
        assert len(service_requests) == 0


class TestAppointmentRequest:
    """Test appointment request (ARQ) conversion."""

    def test_arq_produces_appointment(self):
        """ARQ moodCode should produce Appointment."""
        result = convert_document(CCDA_APPOINTMENT_REQUEST)
        bundle = result["bundle"]
        appointments = _find_resources(bundle, "Appointment")
        assert len(appointments) == 1

    def test_arq_status_proposed(self):
        """ARQ + new → proposed."""
        result = convert_document(CCDA_APPOINTMENT_REQUEST)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert appt["status"] == "proposed"

    def test_arq_has_priority(self):
        """priorityCode UR → priority 2."""
        result = convert_document(CCDA_APPOINTMENT_REQUEST)
        bundle = result["bundle"]
        appt = _find_resources(bundle, "Appointment")[0]
        assert appt["priority"] == 2
