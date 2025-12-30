"""Unit tests for Act validation.

Tests C-CDA conformance validation for:
- Problem Concern Act (2.16.840.1.113883.10.20.22.4.3)
- Allergy Concern Act (2.16.840.1.113883.10.20.22.4.30)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import Act
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestProblemConcernActValidation:
    """Tests for Problem Concern Act conformance validation."""

    def test_valid_problem_concern_act(self) -> None:
        """Valid Problem Concern Act should pass all checks."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                    <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20100301"/>
                    </effectiveTime>
                    <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.code.code == "CONC"
        assert act.status_code.code == "active"

    def test_valid_completed_problem_concern_act_with_high(self) -> None:
        """Valid completed Problem Concern Act with high should pass."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
                <high value="20230301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                    <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20100301"/>
                    </effectiveTime>
                    <value xsi:type="CD" code="I10" codeSystem="2.16.840.1.113883.6.90"/>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.status_code.code == "completed"
        assert act.effective_time.high is not None

    def test_problem_concern_act_missing_id(self) -> None:
        """Problem Concern Act without id should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Act)

    def test_problem_concern_act_missing_code(self) -> None:
        """Problem Concern Act without code should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Act)

    def test_problem_concern_act_with_loinc_code(self) -> None:
        """Problem Concern Act with LOINC code 48765-2 should pass validation.

        SDWG supports both CONC and 48765-2 for concern acts.
        Ref: C-CDA Examples comment: "SDWG supports 48765-2 or CONC in the code element"
        """
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="48765-2" displayName="Allergies, Adverse Reactions, Alerts"
                  codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.code.code == "48765-2"

    def test_problem_concern_act_missing_status_code(self) -> None:
        """Problem Concern Act without statusCode should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Act)

    def test_problem_concern_act_missing_effective_time(self) -> None:
        """Problem Concern Act without effectiveTime should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, Act)

    def test_problem_concern_act_missing_effective_time_low(self) -> None:
        """Problem Concern Act without effectiveTime/low should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <high value="20230301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="effectiveTime SHALL contain low"):
            parse_ccda_fragment(xml, Act)

    def test_problem_concern_act_completed_without_high(self) -> None:
        """Completed Problem Concern Act without effectiveTime/high should pass.

        Per C-CDA IG, effectiveTime.high is optional (0..1 cardinality) even when
        statusCode is completed. Official C-CDA Examples show completed concerns
        without high element.
        """
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.status_code.code == "completed"
        # effectiveTime.high is optional, even when completed
        assert act.effective_time.high is None

    def test_problem_concern_act_missing_entry_relationship(self) -> None:
        """Problem Concern Act without entryRelationship should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*entryRelationship"):
            parse_ccda_fragment(xml, Act)


class TestAllergyConcernActValidation:
    """Tests for Allergy Concern Act conformance validation."""

    def test_valid_allergy_concern_act(self) -> None:
        """Valid Allergy Concern Act should pass all checks."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
                    <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20100301"/>
                    </effectiveTime>
                    <value xsi:type="CD" code="419511003" codeSystem="2.16.840.1.113883.6.96"/>
                    <participant typeCode="CSM">
                        <participantRole classCode="MANU">
                            <playingEntity classCode="MMAT">
                                <code code="70618" codeSystem="2.16.840.1.113883.6.88"/>
                            </playingEntity>
                        </participantRole>
                    </participant>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.code.code == "CONC"

    def test_allergy_concern_act_missing_id(self) -> None:
        """Allergy Concern Act without id should fail validation."""
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Act)

    def test_allergy_concern_act_with_loinc_code(self) -> None:
        """Allergy Concern Act with LOINC code 48765-2 should pass validation.

        SDWG supports both CONC and 48765-2 for concern acts.
        Ref: C-CDA Examples comment: "SDWG supports 48765-2 or CONC in the code element"
        """
        xml = """
        <act xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
             classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="48765-2" displayName="Allergies, Adverse Reactions, Alerts"
                  codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.7"/>
                    <id root="4adc1020-7b14-11db-9fe1-0800200c9a66"/>
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20100301"/>
                    </effectiveTime>
                    <value xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                           xsi:type="CD" code="419511003" codeSystem="2.16.840.1.113883.6.96"/>
                    <participant typeCode="CSM">
                        <participantRole classCode="MANU">
                            <playingEntity classCode="MMAT">
                                <code code="70618" codeSystem="2.16.840.1.113883.6.88"/>
                            </playingEntity>
                        </participantRole>
                    </participant>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.code.code == "48765-2"

    def test_allergy_concern_act_completed_requires_high(self) -> None:
        """Completed Allergy Concern Act without high should fail (CONF:1198-10085)."""
        xml = """
        <act xmlns="urn:hl7-org:v3" classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
                <!-- Missing high - should fail per CONF:1198-10085 -->
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                </observation>
            </entryRelationship>
        </act>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain high.*CONF:1198-10085"):
            parse_ccda_fragment(xml, Act)

    def test_allergy_concern_act_completed_with_high(self) -> None:
        """Completed Allergy Concern Act with high should pass (CONF:1198-10085)."""
        xml = """
        <act xmlns="urn:hl7-org:v3" classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.30"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
                <high value="20150615"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                </observation>
            </entryRelationship>
        </act>
        """
        act = parse_ccda_fragment(xml, Act)
        assert act is not None
        assert act.status_code.code == "completed"
        assert act.effective_time.high is not None
        assert act.effective_time.high.value == "20150615"
