"""Integration test for CarePlan with interventions and outcomes.

Tests the end-to-end conversion of a Care Plan Document that includes
Interventions Section and Outcomes Section, verifying that:
1. Intervention acts are converted to Procedure resources
2. Outcome observations are converted to Observation resources
3. Outcomes are properly linked to interventions via GEVL entryRelationships
4. CarePlan.activity references are created correctly
"""

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle


def test_careplan_with_interventions_and_outcomes_full_integration():
    """Test full end-to-end CarePlan with interventions and outcomes."""

    ccda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="careplan-with-outcomes-integration"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan with Interventions and Outcomes</title>
  <effectiveTime value="20240115120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="patient-integration-test"/>
      <patient>
        <name><given>Test</given><family>Patient</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19750501"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240115120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="npi-integration"/>
      <assignedPerson>
        <name><given>Test</given><family>Doctor</family><suffix>MD</suffix></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="org-integration"/>
        <name>Test Hospital</name>
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
      <!-- Health Concerns Section (required) -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                displayName="Health concerns document"/>
          <title>HEALTH CONCERNS</title>
          <text><paragraph>Respiratory insufficiency</paragraph></text>
        </section>
      </component>

      <!-- Goals Section (required) -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1" displayName="Goals"/>
          <title>GOALS</title>
          <text><paragraph>Maintain oxygen saturation greater than 92%</paragraph></text>

          <entry>
            <observation classCode="OBS" moodCode="GOL">
              <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
              <id root="goal-obs-integration-123"/>
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

      <!-- Interventions Section with GEVL link to outcome -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"
                displayName="Interventions Provided"/>
          <title>INTERVENTIONS</title>
          <text><paragraph>Oxygen therapy via nasal cannula</paragraph></text>

          <!-- Intervention Act with GEVL link to outcome -->
          <entry>
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-act-integration-123"/>
              <code code="362956003" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Procedure/intervention (procedure)"/>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
                <high value="20240415"/>
              </effectiveTime>

              <!-- GEVL: Outcome that evaluates this intervention -->
              <entryRelationship typeCode="GEVL">
                <observation classCode="OBS" moodCode="EVN">
                  <id root="outcome-obs-integration-456"/>
                  <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                        displayName="Oxygen saturation"/>
                </observation>
              </entryRelationship>

              <!-- COMP: The actual procedure being performed -->
              <entryRelationship typeCode="COMP">
                <procedure classCode="PROC" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2014-06-09"/>
                  <id root="procedure-integration-789"/>
                  <code code="371907003" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Oxygen administration by nasal cannula"/>
                  <statusCode code="active"/>
                  <effectiveTime>
                    <low value="20240115"/>
                  </effectiveTime>
                </procedure>
              </entryRelationship>
            </act>
          </entry>
        </section>
      </component>

      <!-- Health Status Evaluations and Outcomes Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
          <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Patient problem outcome"/>
          <title>HEALTH STATUS EVALUATIONS AND OUTCOMES</title>
          <text><paragraph>Oxygen saturation measured at 95%</paragraph></text>

          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
              <id root="outcome-obs-integration-456"/>
              <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Oxygen saturation in Arterial blood by Pulse oximetry"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240120"/>
              <value xsi:type="PQ" value="95" unit="%"/>
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

    # Find all resource types
    careplan_entries = [e for e in bundle.entry if type(e.resource).__name__ == "CarePlan"]
    procedure_entries = [e for e in bundle.entry if type(e.resource).__name__ == "Procedure"]
    observation_entries = [e for e in bundle.entry if type(e.resource).__name__ == "Observation"]

    # Verify resources were created
    assert len(careplan_entries) > 0, "CarePlan resource should exist"
    assert len(procedure_entries) > 0, "Procedure resource(s) should exist from intervention"
    assert len(observation_entries) > 0, "Observation resource(s) should exist from outcome"

    careplan = careplan_entries[0].resource

    # Verify CarePlan has activities
    assert careplan.activity is not None, "CarePlan should have activities"
    assert len(careplan.activity) >= 1, "CarePlan should have at least one activity"

    # Verify activity has reference to Procedure
    activity = careplan.activity[0]
    assert activity.reference is not None, "Activity should have reference to intervention"
    assert str(activity.reference.reference).startswith("Procedure/"), \
        f"Activity should reference Procedure, got: {activity.reference.reference}"

    # Verify the referenced Procedure exists in bundle
    procedure_ids = [f"Procedure/{e.resource.id}" for e in procedure_entries]
    assert str(activity.reference.reference) in procedure_ids, \
        f"Referenced procedure {activity.reference.reference} should exist in bundle"

    # Verify activity has outcomeReference
    assert activity.outcomeReference is not None, "Activity should have outcomeReference"
    assert len(activity.outcomeReference) == 1, "Activity should have exactly 1 outcome"

    # Verify outcomeReference points to Observation
    outcome_ref = str(activity.outcomeReference[0].reference)
    assert outcome_ref.startswith("Observation/"), \
        f"Outcome reference should point to Observation, got: {outcome_ref}"

    # Verify the referenced Observation exists in bundle
    observation_ids = [f"Observation/{e.resource.id}" for e in observation_entries]
    assert outcome_ref in observation_ids, \
        f"Referenced observation {outcome_ref} should exist in bundle"


def test_careplan_with_multiple_interventions_different_outcomes():
    """Test CarePlan with multiple interventions each having different outcomes."""

    ccda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="careplan-multi-int-out"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="patient-multi"/>
      <patient>
        <name><given>Multi</given><family>Test</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240115120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="npi-multi"/>
      <assignedPerson>
        <name><given>Jane</given><family>Doe</family><suffix>MD</suffix></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="org-multi"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20240115"/>
      </effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
          <title>HEALTH CONCERNS</title>
          <text><paragraph>None</paragraph></text>
        </section>
      </component>

      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"/>
          <title>GOALS</title>
          <text><paragraph>Goals</paragraph></text>
        </section>
      </component>

      <!-- Interventions Section with two interventions -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"/>
          <title>INTERVENTIONS</title>
          <text><paragraph>Multiple interventions</paragraph></text>

          <!-- First intervention with outcome-A -->
          <entry>
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-A"/>
              <code code="410000000" codeSystem="2.16.840.1.113883.6.96"/>
              <statusCode code="active"/>

              <entryRelationship typeCode="GEVL">
                <observation classCode="OBS" moodCode="EVN">
                  <id root="outcome-A"/>
                </observation>
              </entryRelationship>

              <entryRelationship typeCode="COMP">
                <procedure classCode="PROC" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.41"/>
                  <id root="procedure-A"/>
                  <code code="1000001" codeSystem="2.16.840.1.113883.6.96"/>
                  <statusCode code="active"/>
                </procedure>
              </entryRelationship>
            </act>
          </entry>

          <!-- Second intervention with outcome-B -->
          <entry>
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-B"/>
              <code code="420000000" codeSystem="2.16.840.1.113883.6.96"/>
              <statusCode code="active"/>

              <entryRelationship typeCode="GEVL">
                <observation classCode="OBS" moodCode="EVN">
                  <id root="outcome-B"/>
                </observation>
              </entryRelationship>

              <entryRelationship typeCode="COMP">
                <procedure classCode="PROC" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.41"/>
                  <id root="procedure-B"/>
                  <code code="2000002" codeSystem="2.16.840.1.113883.6.96"/>
                  <statusCode code="active"/>
                </procedure>
              </entryRelationship>
            </act>
          </entry>
        </section>
      </component>

      <!-- Outcomes Section with two outcomes -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
          <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"/>
          <title>OUTCOMES</title>
          <text><paragraph>Outcomes</paragraph></text>

          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
              <id root="outcome-A"/>
              <code code="1111-1" codeSystem="2.16.840.1.113883.6.1"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240120"/>
              <value xsi:type="PQ" value="90" unit="%"/>
            </observation>
          </entry>

          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
              <id root="outcome-B"/>
              <code code="2222-2" codeSystem="2.16.840.1.113883.6.1"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240121"/>
              <value xsi:type="PQ" value="85" unit="%"/>
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
    assert len(careplan_entries) > 0

    careplan = careplan_entries[0].resource

    # Verify CarePlan has activities
    assert careplan.activity is not None
    assert len(careplan.activity) == 2, "Should have 2 activities (one for each intervention)"

    # Verify both activities have outcomeReferences
    for i, activity in enumerate(careplan.activity):
        assert activity.outcomeReference is not None, f"Activity {i} should have outcomeReference"
        assert len(activity.outcomeReference) == 1, f"Activity {i} should have exactly 1 outcome"

    # Verify outcomes are different for each activity
    outcome_ref_1 = str(careplan.activity[0].outcomeReference[0].reference)
    outcome_ref_2 = str(careplan.activity[1].outcomeReference[0].reference)
    assert outcome_ref_1 != outcome_ref_2, "Each activity should have a different outcome"


def test_careplan_intervention_without_outcome():
    """Test CarePlan with intervention that has no outcome (no GEVL)."""

    ccda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="careplan-no-outcome"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Care Plan</title>
  <effectiveTime value="20240115120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="patient-no-out"/>
      <patient>
        <name><given>Test</given><family>Patient</family></name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19800101"/>
      </patient>
    </patientRole>
  </recordTarget>

  <author>
    <time value="20240115120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="npi-no-out"/>
      <assignedPerson>
        <name><given>Test</given><family>Doctor</family></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="org-no-out"/>
        <name>Test Hospital</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime><low value="20240115"/></effectiveTime>
    </serviceEvent>
  </documentationOf>

  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
          <title>HEALTH CONCERNS</title>
          <text><paragraph>None</paragraph></text>
        </section>
      </component>

      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"/>
          <title>GOALS</title>
          <text><paragraph>Goals</paragraph></text>
        </section>
      </component>

      <!-- Intervention without GEVL (no outcome) -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"/>
          <title>INTERVENTIONS</title>
          <text><paragraph>Intervention without outcome</paragraph></text>

          <entry>
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-no-outcome"/>
              <code code="123000" codeSystem="2.16.840.1.113883.6.96"/>
              <statusCode code="active"/>

              <!-- No GEVL entryRelationship - no outcome -->

              <entryRelationship typeCode="COMP">
                <procedure classCode="PROC" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.41"/>
                  <id root="procedure-no-outcome"/>
                  <code code="999000" codeSystem="2.16.840.1.113883.6.96"/>
                  <statusCode code="active"/>
                </procedure>
              </entryRelationship>
            </act>
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
    assert len(careplan_entries) > 0

    careplan = careplan_entries[0].resource

    # Verify CarePlan has activities
    assert careplan.activity is not None
    assert len(careplan.activity) >= 1

    # Verify activity has NO outcomeReference (no GEVL in intervention)
    activity = careplan.activity[0]
    assert activity.outcomeReference is None, "Activity should NOT have outcomeReference when no GEVL relationship"
