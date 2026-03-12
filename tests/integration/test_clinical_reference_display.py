"""Integration tests for display text on clinical resource references.

Validates that Observation, Condition, and Medication references include
display text when the source C-CDA provides displayName attributes.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def _find_resources(bundle: dict, resource_type: str) -> list[dict]:
    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == resource_type
    ]


class TestEncounterDiagnosisConditionDisplay:
    """Encounter.diagnosis.condition references should include display from observation value."""

    def test_nist_encounter_diagnosis_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        encounters = _find_resources(bundle, "Encounter")
        has_diagnosis_display = False
        for enc in encounters:
            for diag in enc.get("diagnosis", []):
                condition_ref = diag.get("condition", {})
                if "display" in condition_ref:
                    has_diagnosis_display = True
                    assert isinstance(condition_ref["display"], str)
                    assert len(condition_ref["display"]) > 0

        assert has_diagnosis_display, "Expected at least one encounter diagnosis with display text"

    def test_athena_encounter_diagnosis_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        encounters = _find_resources(bundle, "Encounter")
        has_diagnosis_display = False
        for enc in encounters:
            for diag in enc.get("diagnosis", []):
                condition_ref = diag.get("condition", {})
                if "display" in condition_ref:
                    has_diagnosis_display = True
                    assert isinstance(condition_ref["display"], str)
                    assert len(condition_ref["display"]) > 0

        # Athena CCD has encounters with diagnoses that have displayName
        assert has_diagnosis_display, "Expected at least one encounter diagnosis with display text"


class TestDiagnosticReportResultDisplay:
    """DiagnosticReport.result references should include display from observation code."""

    def test_nist_diagnostic_report_result_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        reports = _find_resources(bundle, "DiagnosticReport")
        has_result_display = False
        for report in reports:
            for result_ref in report.get("result", []):
                if "display" in result_ref:
                    has_result_display = True
                    assert isinstance(result_ref["display"], str)
                    assert len(result_ref["display"]) > 0

        if reports:
            assert has_result_display, (
                "Expected at least one DiagnosticReport result with display text"
            )

    def test_athena_diagnostic_report_result_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "athena_ccd.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        reports = _find_resources(bundle, "DiagnosticReport")
        has_result_display = False
        for report in reports:
            for result_ref in report.get("result", []):
                if "display" in result_ref:
                    has_result_display = True
                    assert isinstance(result_ref["display"], str)
                    assert len(result_ref["display"]) > 0

        if reports:
            assert has_result_display, (
                "Expected at least one DiagnosticReport result with display text"
            )


class TestMedicationReferenceDisplay:
    """MedicationRequest.medicationReference should include display from medication code."""

    def test_nist_medication_reference_has_display(self) -> None:
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        med_requests = _find_resources(bundle, "MedicationRequest")
        has_med_display = False
        for req in med_requests:
            med_ref = req.get("medicationReference", {})
            if isinstance(med_ref, dict) and "display" in med_ref:
                has_med_display = True
                assert isinstance(med_ref["display"], str)
                assert len(med_ref["display"]) > 0

        if med_requests:
            # Only assert if there are medication requests with medicationReference
            med_refs_exist = any("medicationReference" in req for req in med_requests)
            if med_refs_exist:
                assert has_med_display, (
                    "Expected at least one medicationReference with display text"
                )


class TestReasonReferenceDisplay:
    """Procedure/ServiceRequest reasonReference to Conditions should include display."""

    def test_nist_reason_reference_display_format(self) -> None:
        """Validate display format on reasonReference when present.

        NIST ambulatory doc may not have reasonReference with display;
        unit tests cover this path. This validates no empty/invalid displays leak through.
        """
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        for resource_type in ("Procedure", "ServiceRequest"):
            resources = _find_resources(bundle, resource_type)
            for resource in resources:
                for reason_ref in resource.get("reasonReference", []):
                    if "display" in reason_ref:
                        assert isinstance(reason_ref["display"], str)
                        assert len(reason_ref["display"]) > 0


class TestConditionEvidenceDisplay:
    """Condition.evidence.detail references should include display from supporting observation."""

    def test_conditions_evidence_display_format(self) -> None:
        """Validate display format on evidence detail when present.

        NIST ambulatory doc may not have condition evidence with display;
        unit tests cover this path. This validates no empty/invalid displays leak through.
        """
        xml = (DOCUMENTS_DIR / "nist_ambulatory.xml").read_text()
        result = convert_document(xml)
        bundle = result["bundle"]

        conditions = _find_resources(bundle, "Condition")
        for condition in conditions:
            for evidence in condition.get("evidence", []):
                for detail in evidence.get("detail", []):
                    if "display" in detail:
                        assert isinstance(detail["display"], str)
                        assert len(detail["display"]) > 0


class TestCarePlanOutcomeDisplay:
    """CarePlan outcomeReference should include display from outcome observation code."""

    def test_careplan_outcome_reference_has_display(self) -> None:
        """Test that outcomeReference includes display when outcome observation has displayName."""
        ccda_xml = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>
  <id root="2.16.840.1.113883.19.5.99999.1" extension="careplan-display-test"/>
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        displayName="Overall plan of care/advance care directives"/>
  <title>Care Plan with Outcome Display</title>
  <effectiveTime value="20240115120000-0500"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>

  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.19.5" extension="patient-display-test"/>
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
      <id root="2.16.840.1.113883.4.6" extension="npi-display-test"/>
      <assignedPerson>
        <name><given>Test</given><family>Doctor</family><suffix>MD</suffix></name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.19.5" extension="org-display-test"/>
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
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
          <title>HEALTH CONCERNS</title>
          <text><paragraph>Hypertension management</paragraph></text>
        </section>
      </component>

      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"/>
          <title>GOALS</title>
          <text><paragraph>Blood pressure below 140/90</paragraph></text>
        </section>
      </component>

      <!-- Interventions with GEVL link to outcome -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"
                displayName="Interventions Provided"/>
          <title>INTERVENTIONS</title>
          <text><paragraph>Blood pressure monitoring</paragraph></text>

          <entry>
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-bp-display"/>
              <code code="362956003" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Procedure/intervention (procedure)"/>
              <statusCode code="active"/>

              <entryRelationship typeCode="GEVL">
                <observation classCode="OBS" moodCode="EVN">
                  <id root="outcome-bp-display"/>
                  <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"
                        displayName="Blood pressure panel with all children optional"/>
                </observation>
              </entryRelationship>

              <entryRelationship typeCode="COMP">
                <procedure classCode="PROC" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.41" extension="2014-06-09"/>
                  <id root="procedure-bp-display"/>
                  <code code="46973005" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Blood pressure taking"/>
                  <statusCode code="active"/>
                </procedure>
              </entryRelationship>
            </act>
          </entry>
        </section>
      </component>

      <!-- Outcomes Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
          <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Patient problem outcome"/>
          <title>HEALTH STATUS EVALUATIONS AND OUTCOMES</title>
          <text><paragraph>Blood pressure measured at 130/85</paragraph></text>

          <entry>
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
              <id root="outcome-bp-display"/>
              <code code="85354-9" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Blood pressure panel with all children optional"/>
              <statusCode code="completed"/>
              <effectiveTime value="20240120"/>
              <value xsi:type="PQ" value="130" unit="mm[Hg]"/>
            </observation>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda_xml)
        bundle = result["bundle"]

        careplans = _find_resources(bundle, "CarePlan")
        assert len(careplans) > 0, "Expected CarePlan resource"

        careplan = careplans[0]
        has_outcome_display = False
        for activity in careplan.get("activity", []):
            for outcome_ref in activity.get("outcomeReference", []):
                if "display" in outcome_ref:
                    has_outcome_display = True
                    assert (
                        outcome_ref["display"] == "Blood pressure panel with all children optional"
                    )

        assert has_outcome_display, "Expected outcomeReference with display text"
