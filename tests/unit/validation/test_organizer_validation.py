"""Unit tests for Organizer validation.

Tests C-CDA conformance validation for:
- Vital Signs Organizer (2.16.840.1.113883.10.20.22.4.26)
- Result Organizer (2.16.840.1.113883.10.20.22.4.1)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import Organizer
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestVitalSignsOrganizerValidation:
    """Tests for Vital Signs Organizer conformance validation."""

    def test_valid_vital_signs_organizer(self) -> None:
        """Valid Vital Signs Organizer should pass all checks."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Vital signs"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.27"/>
                    <id root="c6f88321-67ad-11db-bd13-0800200c9a66"/>
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"
                          displayName="Systolic blood pressure"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231201120000"/>
                    <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
                </observation>
            </component>
        </organizer>
        """
        organizer = parse_ccda_fragment(xml, Organizer)
        assert organizer is not None
        assert organizer.code.code == "46680005"
        assert organizer.status_code.code == "completed"

    def test_vital_signs_organizer_missing_id(self) -> None:
        """Vital Signs Organizer without id should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Organizer)

    def test_vital_signs_organizer_missing_code(self) -> None:
        """Vital Signs Organizer without code should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Organizer)

    def test_vital_signs_organizer_missing_status_code(self) -> None:
        """Vital Signs Organizer without statusCode should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Organizer)

    def test_vital_signs_organizer_wrong_status_code(self) -> None:
        """Vital Signs Organizer with wrong statusCode should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="active"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="statusCode SHALL be 'completed'"):
            parse_ccda_fragment(xml, Organizer)

    def test_vital_signs_organizer_missing_effective_time(self) -> None:
        """Vital Signs Organizer without effectiveTime should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*effectiveTime"):
            parse_ccda_fragment(xml, Organizer)

    def test_vital_signs_organizer_missing_component(self) -> None:
        """Vital Signs Organizer without component should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*component"):
            parse_ccda_fragment(xml, Organizer)


class TestResultOrganizerValidation:
    """Tests for Result Organizer conformance validation."""

    def test_valid_result_organizer(self) -> None:
        """Valid Result Organizer should pass all checks."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="BATTERY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
            <code code="24331-1" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Lipid panel"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                    <id root="107c2dc0-67a5-11db-bd13-0800200c9a66"/>
                    <code code="2093-3" codeSystem="2.16.840.1.113883.6.1"
                          displayName="Cholesterol"/>
                    <statusCode code="completed"/>
                    <effectiveTime value="20231201"/>
                    <value xsi:type="PQ" value="186" unit="mg/dL"/>
                </observation>
            </component>
        </organizer>
        """
        organizer = parse_ccda_fragment(xml, Organizer)
        assert organizer is not None
        assert organizer.code.code == "24331-1"

    def test_result_organizer_missing_id(self) -> None:
        """Result Organizer without id should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="BATTERY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <code code="24331-1" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="2093-3" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Organizer)

    def test_result_organizer_missing_code(self) -> None:
        """Result Organizer without code should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="BATTERY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
            <statusCode code="completed"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="2093-3" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Organizer)

    def test_result_organizer_missing_status_code(self) -> None:
        """Result Organizer without statusCode should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="BATTERY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
            <code code="24331-1" codeSystem="2.16.840.1.113883.6.1"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="2093-3" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
            </component>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Organizer)

    def test_result_organizer_missing_component(self) -> None:
        """Result Organizer without component should fail validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="BATTERY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
            <id root="7d5a02b0-67a4-11db-bd13-0800200c9a66"/>
            <code code="24331-1" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
        </organizer>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*component"):
            parse_ccda_fragment(xml, Organizer)

    def test_non_result_organizer_skips_validation(self) -> None:
        """Organizer without Result Organizer template should skip validation."""
        xml = """
        <organizer xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   classCode="CLUSTER" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
        </organizer>
        """
        # Should not raise validation error
        organizer = parse_ccda_fragment(xml, Organizer)
        assert organizer is not None
