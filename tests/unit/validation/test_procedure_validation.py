"""Unit tests for Procedure validation.

Tests C-CDA conformance validation for:
- Procedure Activity Procedure (2.16.840.1.113883.10.20.22.4.14)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import Procedure
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestProcedureActivityProcedureValidation:
    """Tests for Procedure Activity Procedure conformance validation."""

    def test_valid_procedure_activity(self) -> None:
        """Valid Procedure Activity Procedure should pass all checks."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Laparoscopic appendectomy"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150301"/>
        </procedure>
        """
        proc = parse_ccda_fragment(xml, Procedure)
        assert proc is not None
        assert proc.status_code.code == "completed"
        assert proc.code.code == "6025007"

    def test_procedure_activity_missing_id(self) -> None:
        """Procedure Activity Procedure without id should fail validation."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Laparoscopic appendectomy"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150301"/>
        </procedure>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, Procedure)

    def test_procedure_activity_missing_code(self) -> None:
        """Procedure Activity Procedure without code should fail validation."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <statusCode code="completed"/>
            <effectiveTime value="20150301"/>
        </procedure>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, Procedure)

    def test_procedure_activity_missing_status_code(self) -> None:
        """Procedure Activity Procedure without statusCode should fail validation."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Laparoscopic appendectomy"/>
            <effectiveTime value="20150301"/>
        </procedure>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, Procedure)

    def test_non_procedure_activity_skips_validation(self) -> None:
        """Procedure without Procedure Activity template should skip validation."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <statusCode code="completed"/>
        </procedure>
        """
        # Should not raise validation error
        proc = parse_ccda_fragment(xml, Procedure)
        assert proc is not None

    def test_procedure_activity_with_multiple_ids(self) -> None:
        """Procedure Activity Procedure with multiple ids should be valid."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <id root="a1b2c3d4-e5f6-7890-abcd-ef1234567890"/>
            <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Laparoscopic appendectomy"/>
            <statusCode code="completed"/>
        </procedure>
        """
        proc = parse_ccda_fragment(xml, Procedure)
        assert proc is not None
        assert len(proc.id) == 2

    def test_procedure_activity_with_different_status_codes(self) -> None:
        """Procedure Activity Procedure with various status codes should be valid."""
        statuses = ["active", "completed", "aborted", "cancelled"]

        for status in statuses:
            xml = f"""
            <procedure xmlns="urn:hl7-org:v3"
                       classCode="PROC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
                <code code="6025007" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Laparoscopic appendectomy"/>
                <statusCode code="{status}"/>
            </procedure>
            """
            proc = parse_ccda_fragment(xml, Procedure)
            assert proc is not None
            assert proc.status_code.code == status

    def test_procedure_activity_with_snomed_code(self) -> None:
        """Procedure Activity Procedure with SNOMED CT code should be valid."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <code code="80146002" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Appendectomy"/>
            <statusCode code="completed"/>
        </procedure>
        """
        proc = parse_ccda_fragment(xml, Procedure)
        assert proc is not None
        assert proc.code.code == "80146002"
        assert proc.code.code_system == "2.16.840.1.113883.6.96"

    def test_procedure_activity_with_loinc_code(self) -> None:
        """Procedure Activity Procedure with LOINC code should be valid."""
        xml = """
        <procedure xmlns="urn:hl7-org:v3"
                   classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
            <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
            <code code="24627-2" codeSystem="2.16.840.1.113883.6.1"
                  displayName="Chest X-ray"/>
            <statusCode code="completed"/>
        </procedure>
        """
        proc = parse_ccda_fragment(xml, Procedure)
        assert proc is not None
        assert proc.code.code == "24627-2"
        assert proc.code.code_system == "2.16.840.1.113883.6.1"
