"""Simple E2E tests for Goal resource conversion with embedded C-CDA."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

CCDA_GOAL_WEIGHT_LOSS = """<?xml version="1.0" encoding="UTF-8"?>
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
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
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
                    <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
                    <code code="61146-7" codeSystem="2.16.840.1.113883.6.1" displayName="Goals"/>
                    <title>GOALS</title>
                    <entry>
                        <observation classCode="OBS" moodCode="GOL">
                            <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
                            <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
                            <code code="289169006" codeSystem="2.16.840.1.113883.6.96" displayName="Weight loss"/>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20240115"/>
                                <high value="20240715"/>
                            </effectiveTime>
                            <author>
                                <time value="20240115"/>
                                <assignedAuthor>
                                    <id root="patient-system" extension="patient-123"/>
                                </assignedAuthor>
                            </author>
                            <!-- Target: Body weight = 160 lbs -->
                            <entryRelationship typeCode="COMP">
                                <observation classCode="OBS" moodCode="GOL">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
                                    <code code="29463-7" codeSystem="2.16.840.1.113883.6.1" displayName="Body weight"/>
                                    <value xsi:type="PQ" value="160" unit="[lb_av]"/>
                                </observation>
                            </entryRelationship>
                        </observation>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""


def test_basic_goal_conversion():
    """Test that a basic goal is converted correctly."""
    bundle = convert_document(CCDA_GOAL_WEIGHT_LOSS)["bundle"]

    # Find the Goal resource in the bundle
    goal = None
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Goal":
            goal = resource
            break

    # Basic assertions
    assert goal is not None, "Goal resource should be created"
    assert goal["lifecycleStatus"] == "active"
    assert "description" in goal
    assert goal["description"]["coding"][0]["code"] == "289169006"
    assert "subject" in goal
    assert "startDate" in goal
    assert goal["startDate"] == "2024-01-15"

    # Check target
    assert "target" in goal
    assert len(goal["target"]) == 1

    assert "detailQuantity" in goal["target"][0]
    # Value can be string or number in FHIR
    assert goal["target"][0]["detailQuantity"]["value"] in [160, "160"]
    assert goal["target"][0]["dueDate"] == "2024-07-15"

    print("✓ Basic goal conversion test passed!")


if __name__ == "__main__":
    test_basic_goal_conversion()
    print("All tests passed!")
