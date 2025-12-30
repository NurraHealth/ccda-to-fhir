"""Simple integration test for CarePlan conversion.

This test verifies basic CarePlan resource creation from a Care Plan Document.
"""

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle


def test_care_plan_document_creates_careplan():
    """Test that a Care Plan Document creates a CarePlan resource."""

    ccda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="careplan-123"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="patient-123"/>
      <patient>
        <name><given>Amy</given><family>Shaw</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750501"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240115120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="npi-123"/>
      <assignedPerson>
        <name><given>John</given><family>Smith</family><suffix>MD</suffix></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="org-123"/>
        <name>Community Health Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <!-- Health Concerns Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                displayName="Health concerns document"/>
          <title>HEALTH CONCERNS</title>
          <text><paragraph>No active health concerns</paragraph></text>
        </section>
      </component>

      <!-- Goals Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1" displayName="Goals"/>
          <title>GOALS</title>
          <text><paragraph>Patient goals</paragraph></text>

          <entry>
            <observation classCode="OBS" moodCode="GOL">
              <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
              <id root="goal-123"/>
              <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Oxygen saturation in Arterial blood by Pulse oximetry"/>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
                <high value="20240415"/>
              </effectiveTime>
            </observation>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

    # Convert the document
    result = convert_document(ccda_xml)["bundle"]

    # Verify we got a bundle
    assert result["resourceType"] == "Bundle"
    bundle = Bundle.model_validate(result)

    # Find the CarePlan resource
    careplan_entries = [e for e in bundle.entry if type(e.resource).__name__ == "CarePlan"]
    assert len(careplan_entries) > 0, "No CarePlan resource found in bundle"

    careplan = careplan_entries[0].resource

    # Verify required fields per US Core CarePlan profile
    assert careplan.status in ["draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"]
    assert careplan.intent == "plan"
    assert careplan.category is not None and len(careplan.category) > 0
    assert careplan.subject is not None

    # Verify US Core CarePlan category
    category_codes = [coding.code for cat in careplan.category for coding in cat.coding if coding]
    assert "assess-plan" in category_codes

    # Verify the CarePlan has a period (from serviceEvent effectiveTime)
    assert careplan.period is not None
    assert careplan.period.start == "2024-01-15"
    assert careplan.period.end == "2024-04-15"

    # Verify US Core profile is referenced
    assert careplan.meta is not None
    assert careplan.meta.profile is not None
    profile_urls = [str(p) for p in careplan.meta.profile]
    assert any("us-core" in url.lower() and "careplan" in url.lower() for url in profile_urls)
