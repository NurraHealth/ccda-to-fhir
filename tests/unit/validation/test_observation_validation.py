"""Unit tests for Observation validation.

Tests C-CDA conformance validation for:
- Problem Observation (2.16.840.1.113883.10.20.22.4.4)
- Allergy Intolerance Observation (2.16.840.1.113883.10.20.22.4.7)
- Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27)
- Result Observation (2.16.840.1.113883.10.20.22.4.2)
- Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import Observation
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestProblemObservationValidation:
    """Tests for Problem Observation conformance validation."""

    def test_valid_problem_observation(self) -> None:
        """Valid Problem Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Problem"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"
                   displayName="Essential hypertension"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.code.code == "55607006"
        assert obs.status_code.code == "completed"

    def test_problem_observation_missing_id(self) -> None:
        """Problem Observation without id should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_missing_code(self) -> None:
        """Problem Observation without code should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <statusCode code="completed"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_missing_status_code(self) -> None:
        """Problem Observation without statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_invalid_status_code(self) -> None:
        """Problem Observation with statusCode != 'completed' should fail."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="active"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="statusCode SHALL be 'completed'"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_missing_effective_time(self) -> None:
        """Problem Observation without effectiveTime should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_missing_effective_time_low(self) -> None:
        """Problem Observation without effectiveTime/low should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <high value="20230301"/>
            </effectiveTime>
            <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="effectiveTime SHALL contain low"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_missing_value(self) -> None:
        """Problem Observation without value should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*value"):
            parse_ccda_fragment(xml, Observation)

    def test_problem_observation_wrong_value_type(self) -> None:
        """Problem Observation with wrong value type should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="PQ" value="120" unit="mmHg"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="value SHALL have xsi:type of CD or CE"):
            parse_ccda_fragment(xml, Observation)

    def test_non_problem_observation_skips_validation(self) -> None:
        """Observation without Problem template ID should skip validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.999"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        # Should not raise validation error
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None


class TestAllergyObservationValidation:
    """Tests for Allergy Intolerance Observation conformance validation."""

    def test_valid_allergy_observation(self) -> None:
        """Valid Allergy Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
            <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <value xsi:type="CD" code="419511003" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Propensity to adverse reaction to drug"/>
            <participant typeCode="CSM">
                <participantRole classCode="MANU">
                    <playingEntity classCode="MMAT">
                        <code code="70618" codeSystem="2.16.840.1.113883.6.88"
                              displayName="Penicillin"/>
                    </playingEntity>
                </participantRole>
            </participant>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.code.code == "ASSERTION"
        assert len(obs.participant) == 1

    def test_allergy_observation_missing_participant(self) -> None:
        """Allergy Observation without participant should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
            <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <statusCode code="completed"/>
            <effectiveTime><low value="20100301"/></effectiveTime>
            <value xsi:type="CD" code="419511003" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*participant"):
            parse_ccda_fragment(xml, Observation)


class TestVitalSignObservationValidation:
    """Tests for Vital Sign Observation conformance validation."""

    def test_valid_vital_sign_observation(self) -> None:
        """Valid Vital Sign Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
            <id root="c6f88321-67ad-11db-bd13-0800200c9a66"/>
            <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Systolic blood pressure"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.code.code == "8480-6"
        assert obs.value.value == "120"

    def test_vital_sign_observation_wrong_value_type(self) -> None:
        """Vital Sign Observation with non-PQ value should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
            <id root="c6f88321-67ad-11db-bd13-0800200c9a66"/>
            <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <value xsi:type="CD" code="123" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="value SHALL be PQ"):
            parse_ccda_fragment(xml, Observation)


class TestResultObservationValidation:
    """Tests for Result Observation conformance validation."""

    def test_valid_result_observation(self) -> None:
        """Valid Result Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
            <code code="33914-3" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Estimated GFR"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="PQ" value="60" unit="mL/min"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.code.code == "33914-3"

    def test_result_observation_missing_status_code(self) -> None:
        """Result Observation without statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
            <code code="33914-3" codeSystem="2.16.840.1.113883.6.1"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="PQ" value="60" unit="mL/min"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Observation)


class TestSmokingStatusObservationValidation:
    """Tests for Smoking Status Observation conformance validation."""

    def test_valid_smoking_status_observation(self) -> None:
        """Valid Smoking Status Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
            <id root="9b56c25d-9104-45ee-9fa4-e0f3afaa01c1"/>
            <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Tobacco smoking status"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="CD" code="449868002" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Current every day smoker"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.code.code == "72166-2"

    def test_smoking_status_observation_wrong_status_code(self) -> None:
        """Smoking Status Observation with wrong statusCode should fail."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
            <id root="9b56c25d-9104-45ee-9fa4-e0f3afaa01c1"/>
            <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="active"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="CD" code="449868002" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="statusCode SHALL be 'completed'"):
            parse_ccda_fragment(xml, Observation)

    def test_smoking_status_observation_wrong_value_type(self) -> None:
        """Smoking Status Observation with wrong value type should fail."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
            <id root="9b56c25d-9104-45ee-9fa4-e0f3afaa01c1"/>
            <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="PQ" value="1" unit="1"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="value SHALL have xsi:type of CD or CE"):
            parse_ccda_fragment(xml, Observation)


class TestSocialHistoryObservationValidation:
    """Tests for Social History Observation conformance validation."""

    def test_valid_social_history_observation(self) -> None:
        """Valid Social History Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="160476009" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Social history"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="CD" code="445281000124101" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Nutrition impairment"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.status_code.code == "completed"

    def test_social_history_observation_missing_code(self) -> None:
        """Social History Observation without code should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Observation)

    def test_social_history_observation_missing_status_code(self) -> None:
        """Social History Observation without statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="160476009" codeSystem="2.16.840.1.113883.6.96"/>
            <effectiveTime value="20231201"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Observation)

    def test_social_history_observation_wrong_status_code(self) -> None:
        """Social History Observation with wrong statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="160476009" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="active"/>
            <effectiveTime value="20231201"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="statusCode SHALL be 'completed'"):
            parse_ccda_fragment(xml, Observation)

    def test_social_history_observation_missing_effective_time(self) -> None:
        """Social History Observation without effectiveTime should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="160476009" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, Observation)

    def test_non_social_history_observation_skips_validation(self) -> None:
        """Observation without Social History template should skip validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <code code="160476009" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None


class TestFamilyHistoryObservationValidation:
    """Tests for Family History Observation conformance validation."""

    def test_valid_family_history_observation(self) -> None:
        """Valid Family History Observation should pass all checks."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <id root="f1e2d3c4-b5a6-9876-fedc-ba9876543210"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Problem">
                <translation code="75323-6" codeSystem="2.16.840.1.113883.6.1"
                             displayName="Condition"/>
            </code>
            <statusCode code="completed"/>
            <effectiveTime value="1967"/>
            <value xsi:type="CD" code="22298006" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Myocardial infarction"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
        assert obs.status_code.code == "completed"
        assert obs.value.code == "22298006"

    def test_family_history_observation_missing_id(self) -> None:
        """Family History Observation without id should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="22298006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Observation)

    def test_family_history_observation_missing_code(self) -> None:
        """Family History Observation without code should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <id root="f1e2d3c4-b5a6-9876-fedc-ba9876543210"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="22298006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Observation)

    def test_family_history_observation_missing_status_code(self) -> None:
        """Family History Observation without statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <id root="f1e2d3c4-b5a6-9876-fedc-ba9876543210"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <value xsi:type="CD" code="22298006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Observation)

    def test_family_history_observation_wrong_status_code(self) -> None:
        """Family History Observation with wrong statusCode should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <id root="f1e2d3c4-b5a6-9876-fedc-ba9876543210"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="active"/>
            <value xsi:type="CD" code="22298006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="statusCode SHALL be 'completed'"):
            parse_ccda_fragment(xml, Observation)

    def test_family_history_observation_missing_value(self) -> None:
        """Family History Observation without value should fail validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.46"/>
            <id root="f1e2d3c4-b5a6-9876-fedc-ba9876543210"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
        </observation>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*value"):
            parse_ccda_fragment(xml, Observation)

    def test_non_family_history_observation_skips_validation(self) -> None:
        """Observation without Family History template should skip validation."""
        xml = """
        <observation xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     classCode="OBS" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        obs = parse_ccda_fragment(xml, Observation)
        assert obs is not None
