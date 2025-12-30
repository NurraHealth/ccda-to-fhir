"""Unit tests for Encounter validation.

Tests C-CDA conformance validation for:
- Encounter Activity (2.16.840.1.113883.10.20.22.4.49)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import Encounter
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestEncounterActivityValidation:
    """Tests for Encounter Activity conformance validation."""

    def test_valid_encounter_activity(self) -> None:
        """Valid Encounter Activity should pass all checks."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office or other outpatient visit"/>
            <effectiveTime>
                <low value="20200301090000"/>
                <high value="20200301100000"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert enc.code.code == "99213"
        assert enc.effective_time.low.value == "20200301090000"

    def test_encounter_activity_missing_id(self) -> None:
        """Encounter Activity without id should fail validation."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office visit"/>
            <effectiveTime>
                <low value="20200301090000"/>
            </effectiveTime>
        </encounter>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Encounter)

    def test_encounter_activity_without_code(self) -> None:
        """Encounter Activity without code should pass validation.

        C-CDA spec says code is SHALL (1..1), but real-world documents from
        OpenVista CareVue and other EHR systems often omit the encounter code.
        Parser relaxes validation to handle real-world documents.
        """
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <effectiveTime>
                <low value="20200301090000"/>
            </effectiveTime>
        </encounter>
        """
        encounter = parse_ccda_fragment(xml, Encounter)
        assert encounter is not None
        # code is optional in real-world documents
        assert encounter.code is None

    def test_encounter_activity_missing_effective_time(self) -> None:
        """Encounter Activity without effectiveTime should fail validation."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office visit"/>
        </encounter>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, Encounter)

    def test_non_encounter_activity_skips_validation(self) -> None:
        """Encounter without Encounter Activity template should skip validation."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
        </encounter>
        """
        # Should not raise validation error
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None

    def test_encounter_activity_with_multiple_ids(self) -> None:
        """Encounter Activity with multiple ids should be valid."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office visit"/>
            <effectiveTime>
                <low value="20200301090000"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert len(enc.id) == 2

    def test_encounter_activity_with_cpt_code(self) -> None:
        """Encounter Activity with CPT code should be valid."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office or other outpatient visit, established"/>
            <effectiveTime>
                <low value="20200301"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert enc.code.code == "99213"
        assert enc.code.code_system == "2.16.840.1.113883.6.12"

    def test_encounter_activity_with_act_code(self) -> None:
        """Encounter Activity with ActCode should be valid."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="AMB" codeSystem="2.16.840.1.113883.5.4"
                  displayName="Ambulatory"/>
            <effectiveTime>
                <low value="20200301"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert enc.code.code == "AMB"
        assert enc.code.code_system == "2.16.840.1.113883.5.4"

    def test_encounter_activity_with_effective_time_low_only(self) -> None:
        """Encounter Activity with only low effectiveTime should be valid."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="AMB" codeSystem="2.16.840.1.113883.5.4"
                  displayName="Ambulatory"/>
            <effectiveTime>
                <low value="20200301"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert enc.effective_time.low.value == "20200301"
        assert enc.effective_time.high is None

    def test_encounter_activity_with_status_code(self) -> None:
        """Encounter Activity with statusCode should be valid."""
        xml = """
        <encounter xmlns="urn:hl7-org:v3"
                   classCode="ENC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
            <id root="2a620155-9d11-439e-92b3-5d9815ff4de8"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20200301"/>
            </effectiveTime>
        </encounter>
        """
        enc = parse_ccda_fragment(xml, Encounter)
        assert enc is not None
        assert enc.status_code.code == "completed"
