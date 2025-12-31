"""Unit tests for SubstanceAdministration validation.

Tests C-CDA conformance validation for:
- Medication Activity (2.16.840.1.113883.10.20.22.4.16)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import SubstanceAdministration
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestMedicationActivityValidation:
    """Tests for Medication Activity conformance validation."""

    def test_valid_medication_activity(self) -> None:
        """Valid Medication Activity should pass all checks."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="314076" codeSystem="2.16.840.1.113883.6.88"
                              displayName="Lisinopril 10 MG Oral Tablet"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        med = parse_ccda_fragment(xml, SubstanceAdministration)
        assert med is not None
        assert med.status_code.code == "active"

    def test_medication_activity_missing_id(self) -> None:
        """Medication Activity without id should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="314076" codeSystem="2.16.840.1.113883.6.88"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_status_code(self) -> None:
        """Medication Activity without statusCode should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="314076" codeSystem="2.16.840.1.113883.6.88"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_effective_time(self) -> None:
        """Medication Activity without effectiveTime should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="314076" codeSystem="2.16.840.1.113883.6.88"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*effectiveTime"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_dose_quantity(self, caplog) -> None:
        """Medication Activity without doseQuantity should log warning (lenient for Cerner/Epic)."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="314076" codeSystem="2.16.840.1.113883.6.88"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        # Should parse successfully but log warning
        result = parse_ccda_fragment(xml, SubstanceAdministration)
        assert result is not None
        assert "doseQuantity" in caplog.text

    def test_medication_activity_missing_consumable(self) -> None:
        """Medication Activity without consumable should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*consumable"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_manufactured_product(self) -> None:
        """Medication Activity without manufacturedProduct should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="consumable SHALL contain exactly one.*manufacturedProduct"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_manufactured_material(self) -> None:
        """Medication Activity without manufacturedMaterial should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="manufacturedProduct SHALL contain exactly one.*manufacturedMaterial"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_medication_activity_missing_material_code(self) -> None:
        """Medication Activity without manufacturedMaterial code should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="2.16.840.1.113883.10.20.22.4.16"/>
            <id root="cdbd33f0-6cde-11db-9fe1-0800200c9a66"/>
            <statusCode code="active"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <doseQuantity value="1" unit="{tbl}"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="manufacturedMaterial SHALL contain exactly one.*code"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_non_medication_activity_skips_validation(self) -> None:
        """SubstanceAdministration without Medication Activity template should skip validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="INT">
            <templateId root="1.2.3.4.5"/>
            <statusCode code="active"/>
        </substanceAdministration>
        """
        # Should not raise validation error
        med = parse_ccda_fragment(xml, SubstanceAdministration)
        assert med is not None
