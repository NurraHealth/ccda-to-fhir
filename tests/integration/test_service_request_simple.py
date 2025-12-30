"""Simple E2E tests for ServiceRequest resource conversion with embedded C-CDA."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

CCDA_PLANNED_COLONOSCOPY = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <id root="test-doc-id"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Test Document</title>
    <effectiveTime value="20240115120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>

    <recordTarget>
        <patientRole>
            <id root="test-patient-id" extension="patient-123"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19700501"/>
            </patient>
        </patientRole>
    </recordTarget>

    <author>
        <time value="20240115"/>
        <assignedAuthor>
            <id root="test-author-id" extension="author-123"/>
            <assignedPerson>
                <name><given>Test</given><family>Author</family></name>
            </assignedPerson>
        </assignedAuthor>
    </author>

    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="test-org-id"/>
                <name>Test Organization</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>

    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of care note"/>
                    <title>PLAN OF TREATMENT</title>
                    <entry typeCode="DRIV">
                        <procedure classCode="PROC" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2022-06-01"/>
                            <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240613"/>
                            <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
                                  displayName="Colonoscopy">
                                <originalText>Screening colonoscopy</originalText>
                                <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
                                           displayName="Colonoscopy, flexible"/>
                            </code>
                            <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                                          displayName="Colon structure"/>
                            <performer>
                                <assignedEntity>
                                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                                    <assignedPerson>
                                        <name><given>John</given><family>Gastro</family></name>
                                    </assignedPerson>
                                </assignedEntity>
                            </performer>
                            <author>
                                <time value="20240115140000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                                    <assignedPerson>
                                        <name><given>Sarah</given><family>Smith</family></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                            <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7" displayName="Routine"/>
                        </procedure>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""


def test_basic_service_request_conversion():
    """Test that a basic planned procedure is converted to ServiceRequest."""
    bundle = convert_document(CCDA_PLANNED_COLONOSCOPY)["bundle"]

    # Find the ServiceRequest resource in the bundle
    service_request = None
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "ServiceRequest":
            service_request = resource
            break

    # Basic assertions
    assert service_request is not None, "ServiceRequest resource should be created"
    assert service_request["status"] == "active"
    assert service_request["intent"] == "order"  # moodCode RQO maps to order

    # Check code
    assert "code" in service_request
    assert service_request["code"]["coding"][0]["code"] == "73761001"
    assert service_request["code"]["coding"][0]["system"] == "http://snomed.info/sct"
    assert service_request["code"]["text"] == "Screening colonoscopy"

    # Check subject reference
    assert "subject" in service_request
    assert "Patient" in service_request["subject"]["reference"]

    # Check occurrence
    assert "occurrenceDateTime" in service_request
    assert service_request["occurrenceDateTime"] == "2024-06-13"

    # Check priority
    assert service_request["priority"] == "routine"

    # Check bodySite
    assert "bodySite" in service_request
    assert service_request["bodySite"][0]["coding"][0]["code"] == "71854001"

    print("✓ Basic ServiceRequest conversion test passed!")


if __name__ == "__main__":
    test_basic_service_request_conversion()
    print("All tests passed!")
