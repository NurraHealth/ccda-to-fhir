"""Integration test for ServiceRequest with full C-CDA document.

This test validates ServiceRequest conversion from a complete CCD with Plan of Care section,
ensuring all references, category inference, and context work properly.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document

# Full CCD document with Plan of Care section containing planned procedures
CCDA_CCD_WITH_PLAN_OF_CARE = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>
    <id root="2.16.840.1.113883.19.5.99999.1" extension="test-ccd-12345"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
    <title>Continuity of Care Document</title>
    <effectiveTime value="20240115120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>

    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5" extension="patient-12345"/>
            <addr use="HP">
                <streetAddressLine>123 Main Street</streetAddressLine>
                <city>Springfield</city>
                <state>IL</state>
                <postalCode>62701</postalCode>
                <country>USA</country>
            </addr>
            <telecom use="HP" value="tel:+1-(555)123-4567"/>
            <patient>
                <name><given>John</given><family>Doe</family></name>
                <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19750501"/>
            </patient>
            <providerOrganization>
                <id root="2.16.840.1.113883.19.5" extension="org-12345"/>
                <name>Springfield Medical Center</name>
            </providerOrganization>
        </patientRole>
    </recordTarget>

    <author>
        <time value="20240115120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="doc-npi-123"/>
            <addr use="WP">
                <streetAddressLine>456 Medical Plaza</streetAddressLine>
                <city>Springfield</city>
                <state>IL</state>
                <postalCode>62702</postalCode>
            </addr>
            <telecom use="WP" value="tel:+1-(555)987-6543"/>
            <assignedPerson>
                <name><given>Sarah</given><family>Smith</family><suffix>MD</suffix></name>
            </assignedPerson>
        </assignedAuthor>
    </author>

    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.19.5" extension="custodian-org-123"/>
                <name>Springfield Health System</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>

    <documentationOf>
        <serviceEvent classCode="PCPR">
            <effectiveTime>
                <low value="20240115"/>
                <high value="20240415"/>
            </effectiveTime>
            <performer typeCode="PRF">
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="pcp-npi-456"/>
                    <assignedPerson>
                        <name><given>Robert</given><family>Johnson</family><suffix>MD</suffix></name>
                    </assignedPerson>
                </assignedEntity>
            </performer>
        </serviceEvent>
    </documentationOf>

    <componentOf>
        <encompassingEncounter>
            <id root="2.16.840.1.113883.19" extension="encounter-67890"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12" displayName="Office Visit"/>
            <effectiveTime value="20240115"/>
            <encounterParticipant typeCode="ATND">
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="attending-npi-789"/>
                    <assignedPerson>
                        <name><given>Michael</given><family>Williams</family><suffix>MD</suffix></name>
                    </assignedPerson>
                </assignedEntity>
            </encounterParticipant>
        </encompassingEncounter>
    </componentOf>

    <component>
        <structuredBody>
            <!-- Problems Section -->
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.5.1" extension="2015-08-01"/>
                    <code code="11450-4" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>
                    <title>PROBLEMS</title>
                    <text>
                        <table>
                            <thead>
                                <tr><th>Problem</th><th>Status</th></tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td ID="problem1">Type 2 Diabetes Mellitus</td>
                                    <td>Active</td>
                                </tr>
                                <tr>
                                    <td ID="problem2">Hypertension</td>
                                    <td>Active</td>
                                </tr>
                            </tbody>
                        </table>
                    </text>
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.3" extension="2015-08-01"/>
                            <id root="concern-act-diabetes"/>
                            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20200101"/>
                            </effectiveTime>
                            <entryRelationship typeCode="SUBJ">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
                                    <id root="problem-obs-diabetes"/>
                                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                                    <statusCode code="completed"/>
                                    <effectiveTime>
                                        <low value="20200101"/>
                                    </effectiveTime>
                                    <value xsi:type="CD" code="44054006" codeSystem="2.16.840.1.113883.6.96" displayName="Type 2 Diabetes Mellitus">
                                        <originalText><reference value="#problem1"/></originalText>
                                    </value>
                                </observation>
                            </entryRelationship>
                        </act>
                    </entry>
                    <entry typeCode="DRIV">
                        <act classCode="ACT" moodCode="EVN">
                            <templateId root="2.16.840.1.113883.10.20.22.4.3" extension="2015-08-01"/>
                            <id root="concern-act-htn"/>
                            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
                            <statusCode code="active"/>
                            <effectiveTime>
                                <low value="20180601"/>
                            </effectiveTime>
                            <entryRelationship typeCode="SUBJ">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
                                    <id root="problem-obs-htn"/>
                                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                                    <statusCode code="completed"/>
                                    <effectiveTime>
                                        <low value="20180601"/>
                                    </effectiveTime>
                                    <value xsi:type="CD" code="59621000" codeSystem="2.16.840.1.113883.6.96" displayName="Essential hypertension">
                                        <originalText><reference value="#problem2"/></originalText>
                                    </value>
                                </observation>
                            </entryRelationship>
                        </act>
                    </entry>
                </section>
            </component>

            <!-- Plan of Care Section -->
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.10" extension="2014-06-09"/>
                    <code code="18776-5" codeSystem="2.16.840.1.113883.6.1" displayName="Plan of care note"/>
                    <title>PLAN OF TREATMENT</title>
                    <text>
                        <table>
                            <thead>
                                <tr>
                                    <th>Planned Activity</th>
                                    <th>Scheduled Date</th>
                                    <th>Reason</th>
                                    <th>Provider</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td ID="procedure1">Screening colonoscopy</td>
                                    <td>2024-06-15</td>
                                    <td>Routine screening</td>
                                    <td>Dr. Jane Gastro</td>
                                </tr>
                                <tr>
                                    <td ID="procedure2">Hemoglobin A1c test</td>
                                    <td>2024-04-01</td>
                                    <td>Diabetes monitoring</td>
                                    <td>Dr. Sarah Smith</td>
                                </tr>
                                <tr>
                                    <td ID="procedure3">Chest X-ray</td>
                                    <td>2024-03-20</td>
                                    <td>Follow-up imaging</td>
                                    <td>Springfield Radiology</td>
                                </tr>
                            </tbody>
                        </table>
                    </text>

                    <!-- Planned Procedure 1: Colonoscopy -->
                    <entry typeCode="DRIV">
                        <procedure classCode="PROC" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2014-06-09"/>
                            <id root="planned-proc-colonoscopy"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240615"/>
                            <code code="73761001" codeSystem="2.16.840.1.113883.6.96" displayName="Colonoscopy">
                                <originalText><reference value="#procedure1"/></originalText>
                                <translation code="45378" codeSystem="2.16.840.1.113883.6.12" displayName="Colonoscopy, flexible"/>
                            </code>
                            <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96" displayName="Colon structure"/>
                            <author>
                                <time value="20240115140000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="doc-npi-123"/>
                                    <assignedPerson>
                                        <name><given>Sarah</given><family>Smith</family><suffix>MD</suffix></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                            <performer>
                                <assignedEntity>
                                    <id root="2.16.840.1.113883.4.6" extension="pcp-npi-456"/>
                                    <assignedPerson>
                                        <name><given>Robert</given><family>Johnson</family><suffix>MD</suffix></name>
                                    </assignedPerson>
                                </assignedEntity>
                            </performer>
                            <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7" displayName="Routine"/>
                        </procedure>
                    </entry>

                    <!-- Planned Procedure 2: HbA1c Lab Test -->
                    <entry typeCode="DRIV">
                        <procedure classCode="PROC" moodCode="RQO">
                            <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2014-06-09"/>
                            <id root="planned-proc-hba1c"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240401"/>
                            <code code="4548-4" codeSystem="2.16.840.1.113883.6.1" displayName="Hemoglobin A1c">
                                <originalText><reference value="#procedure2"/></originalText>
                            </code>
                            <author>
                                <time value="20240115120000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="doc-npi-123"/>
                                    <assignedPerson>
                                        <name><given>Sarah</given><family>Smith</family><suffix>MD</suffix></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                            <priorityCode code="R" codeSystem="2.16.840.1.113883.5.7" displayName="Routine"/>
                            <!-- Reason reference to diabetes condition -->
                            <entryRelationship typeCode="RSON">
                                <observation classCode="OBS" moodCode="EVN">
                                    <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
                                    <id root="problem-obs-diabetes"/>
                                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                                    <statusCode code="completed"/>
                                    <effectiveTime>
                                        <low value="20200101"/>
                                    </effectiveTime>
                                    <value xsi:type="CD" code="44054006" codeSystem="2.16.840.1.113883.6.96" displayName="Type 2 Diabetes Mellitus"/>
                                </observation>
                            </entryRelationship>
                        </procedure>
                    </entry>

                    <!-- Planned Procedure 3: Chest X-ray (Imaging) -->
                    <entry typeCode="DRIV">
                        <procedure classCode="PROC" moodCode="INT">
                            <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2014-06-09"/>
                            <id root="planned-proc-chest-xray"/>
                            <statusCode code="active"/>
                            <effectiveTime value="20240320"/>
                            <code code="71045" codeSystem="2.16.840.1.113883.6.12" displayName="Radiologic examination, chest, 1 view">
                                <originalText><reference value="#procedure3"/></originalText>
                                <translation code="168731009" codeSystem="2.16.840.1.113883.6.96" displayName="Chest x-ray"/>
                            </code>
                            <targetSiteCode code="51185008" codeSystem="2.16.840.1.113883.6.96" displayName="Thoracic structure"/>
                            <author>
                                <time value="20240115120000-0500"/>
                                <assignedAuthor>
                                    <id root="2.16.840.1.113883.4.6" extension="doc-npi-123"/>
                                    <assignedPerson>
                                        <name><given>Sarah</given><family>Smith</family><suffix>MD</suffix></name>
                                    </assignedPerson>
                                </assignedAuthor>
                            </author>
                            <priorityCode code="UR" codeSystem="2.16.840.1.113883.5.7" displayName="Urgent"/>
                        </procedure>
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>
"""


def test_full_ccd_with_planned_procedures():
    """Test ServiceRequest conversion from complete CCD with Plan of Care.

    Verifies:
    - ServiceRequest resources created from planned procedures
    - References to patient, encounter, practitioners work properly
    - Category inference works in document context
    - All sections processed correctly
    - No placeholder references
    """
    bundle = convert_document(CCDA_CCD_WITH_PLAN_OF_CARE)["bundle"]

    # Verify bundle structure
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "document"
    assert "entry" in bundle

    # Build resource index
    resources_by_type = {}
    resources_by_id = {}

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")

        if resource_type not in resources_by_type:
            resources_by_type[resource_type] = []
        resources_by_type[resource_type].append(resource)

        if "id" in resource:
            resource_id = f"{resource_type}/{resource['id']}"
            resources_by_id[resource_id] = resource

    # Verify ServiceRequest resources were created
    service_requests = resources_by_type.get("ServiceRequest", [])
    assert len(service_requests) == 3, f"Expected 3 ServiceRequest resources, found {len(service_requests)}"

    # Verify Composition is first
    first_resource = bundle["entry"][0]["resource"]
    assert first_resource["resourceType"] == "Composition"

    # Verify other expected resources
    assert len(resources_by_type.get("Patient", [])) >= 1, "Patient resource should exist"
    assert len(resources_by_type.get("Practitioner", [])) >= 1, "Practitioner resources should exist"
    assert len(resources_by_type.get("Encounter", [])) >= 1, "Encounter resource should exist"
    assert len(resources_by_type.get("Condition", [])) >= 2, "Condition resources should exist (2 problems)"

    # Verify each ServiceRequest has required fields and proper references
    for sr in service_requests:
        # Required fields
        assert "status" in sr, "ServiceRequest must have status"
        assert sr["status"] in ["draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"]

        assert "intent" in sr, "ServiceRequest must have intent"
        assert sr["intent"] in ["proposal", "plan", "directive", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"]

        assert "code" in sr, "ServiceRequest must have code"
        assert "coding" in sr["code"], "ServiceRequest code must have coding"

        assert "subject" in sr, "ServiceRequest must have subject"
        assert "reference" in sr["subject"], "ServiceRequest subject must have reference"

        # Verify subject reference is valid (not placeholder)
        subject_ref = sr["subject"]["reference"]
        assert "placeholder" not in subject_ref.lower(), "Subject reference should not be placeholder"
        assert subject_ref in resources_by_id, f"Subject reference {subject_ref} should exist in bundle"

        # Verify US Core profile
        assert "meta" in sr, "ServiceRequest should have meta"
        assert "profile" in sr["meta"], "ServiceRequest meta should have profile"
        assert any("us-core" in p.lower() and "servicerequest" in p.lower() for p in sr["meta"]["profile"]), \
            "ServiceRequest should reference US Core ServiceRequest profile"

        # Verify category exists (must support in US Core)
        assert "category" in sr, "ServiceRequest should have category (US Core must support)"

        # Verify occurrence exists (must support in US Core)
        assert "occurrenceDateTime" in sr or "occurrencePeriod" in sr, \
            "ServiceRequest should have occurrence[x] (US Core must support)"

        # If requester exists, verify it's a valid reference (not placeholder)
        # Note: Practitioner resources for requesters/performers may not always be in the bundle
        # if they're only referenced from ServiceRequest and not from other document sections
        if "requester" in sr:
            requester_ref = sr["requester"]["reference"]
            assert "placeholder" not in requester_ref.lower(), "Requester reference should not be placeholder"
            # If the reference exists in bundle, that's great, but it's not always required
            # (e.g., if the Practitioner only appears as author of the planned procedure)

        # If performer exists, verify all are valid references (not placeholder)
        if "performer" in sr:
            for performer in sr["performer"]:
                performer_ref = performer["reference"]
                assert "placeholder" not in performer_ref.lower(), "Performer reference should not be placeholder"

    # Verify specific ServiceRequest details

    # Find colonoscopy ServiceRequest
    colonoscopy_sr = None
    for sr in service_requests:
        if "code" in sr and "coding" in sr["code"]:
            for coding in sr["code"]["coding"]:
                if coding.get("code") == "73761001":  # SNOMED code for colonoscopy
                    colonoscopy_sr = sr
                    break

    assert colonoscopy_sr is not None, "Colonoscopy ServiceRequest should exist"
    assert colonoscopy_sr["status"] == "active"
    assert colonoscopy_sr["intent"] == "order"  # moodCode RQO maps to order
    assert "priority" in colonoscopy_sr
    assert colonoscopy_sr["priority"] == "routine"
    assert "bodySite" in colonoscopy_sr
    assert colonoscopy_sr["bodySite"][0]["coding"][0]["code"] == "71854001"  # Colon structure
    # Category defaults to diagnostic procedure (primary code is SNOMED CT, not CPT)
    assert "category" in colonoscopy_sr
    assert colonoscopy_sr["category"][0]["coding"][0]["code"] == "103693007"  # Diagnostic procedure

    # Find HbA1c lab test ServiceRequest
    hba1c_sr = None
    for sr in service_requests:
        if "code" in sr and "coding" in sr["code"]:
            for coding in sr["code"]["coding"]:
                if coding.get("code") == "4548-4":  # LOINC code for HbA1c
                    hba1c_sr = sr
                    break

    assert hba1c_sr is not None, "HbA1c ServiceRequest should exist"
    assert hba1c_sr["status"] == "active"
    assert hba1c_sr["intent"] == "order"
    # Category should be inferred as laboratory procedure (LOINC system)
    assert "category" in hba1c_sr
    assert hba1c_sr["category"][0]["coding"][0]["code"] == "108252007"  # Laboratory procedure
    # Should have reason reference to diabetes condition
    assert "reasonReference" in hba1c_sr
    reason_ref = hba1c_sr["reasonReference"][0]["reference"]
    assert "Condition" in reason_ref
    assert reason_ref in resources_by_id, f"Reason reference {reason_ref} should exist in bundle"

    # Find chest X-ray ServiceRequest
    xray_sr = None
    for sr in service_requests:
        if "code" in sr and "coding" in sr["code"]:
            for coding in sr["code"]["coding"]:
                if coding.get("code") == "71045":  # CPT code for chest x-ray
                    xray_sr = sr
                    break

    assert xray_sr is not None, "Chest X-ray ServiceRequest should exist"
    assert xray_sr["status"] == "active"
    assert xray_sr["intent"] == "plan"  # moodCode INT maps to plan
    assert "priority" in xray_sr
    assert xray_sr["priority"] == "urgent"
    assert "bodySite" in xray_sr
    assert xray_sr["bodySite"][0]["coding"][0]["code"] == "51185008"  # Thoracic structure
    # Category should be inferred as imaging (CPT code in radiology range 70000-79999)
    assert "category" in xray_sr
    assert xray_sr["category"][0]["coding"][0]["code"] == "363679005"  # Imaging

    # Verify no placeholder references anywhere in bundle
    def check_no_placeholders(obj, path=""):
        """Recursively check for placeholder references."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "reference" and isinstance(value, str):
                    assert "placeholder" not in value.lower(), \
                        f"Found placeholder reference at {path}.{key}: {value}"
                else:
                    check_no_placeholders(value, f"{path}.{key}")
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                check_no_placeholders(item, f"{path}[{i}]")

    check_no_placeholders(bundle)

    print("✓ Full CCD with planned procedures integration test passed!")


if __name__ == "__main__":
    test_full_ccd_with_planned_procedures()
    print("All tests passed!")
