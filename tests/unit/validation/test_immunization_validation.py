"""Unit tests for Immunization validation.

Tests C-CDA conformance validation for:
- Immunization Activity (2.16.840.1.113883.10.20.22.4.52)
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import SubstanceAdministration
from ccda_to_fhir.ccda.parser import MalformedXMLError, parse_ccda_fragment


class TestImmunizationActivityValidation:
    """Tests for Immunization Activity conformance validation."""

    def test_valid_immunization_activity(self) -> None:
        """Valid Immunization Activity should pass all checks."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="88" codeSystem="2.16.840.1.113883.12.292"
                              displayName="Influenza virus vaccine"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        imm = parse_ccda_fragment(xml, SubstanceAdministration)
        assert imm is not None
        assert imm.status_code.code == "completed"
        assert imm.consumable.manufactured_product.manufactured_material.code.code == "88"

    def test_immunization_activity_missing_id(self) -> None:
        """Immunization Activity without id should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="88" codeSystem="2.16.840.1.113883.12.292"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*id"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_status_code(self) -> None:
        """Immunization Activity without statusCode should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="88" codeSystem="2.16.840.1.113883.12.292"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*statusCode"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_effective_time(self) -> None:
        """Immunization Activity without effectiveTime should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="88" codeSystem="2.16.840.1.113883.12.292"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain at least one.*effectiveTime"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_consumable(self) -> None:
        """Immunization Activity without consumable should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="SHALL contain exactly one.*consumable"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_manufactured_product(self) -> None:
        """Immunization Activity without manufacturedProduct should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="consumable SHALL contain exactly one.*manufacturedProduct"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_manufactured_material(self) -> None:
        """Immunization Activity without manufacturedMaterial should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        with pytest.raises((ValueError, MalformedXMLError), match="manufacturedProduct SHALL contain exactly one.*manufacturedMaterial"):
            parse_ccda_fragment(xml, SubstanceAdministration)

    def test_immunization_activity_missing_material_code(self) -> None:
        """Immunization Activity without manufacturedMaterial code should fail validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
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

    def test_non_immunization_activity_skips_validation(self) -> None:
        """SubstanceAdministration without Immunization Activity template should skip validation."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="1.2.3.4.5"/>
            <statusCode code="completed"/>
        </substanceAdministration>
        """
        # Should not raise validation error
        imm = parse_ccda_fragment(xml, SubstanceAdministration)
        assert imm is not None

    def test_immunization_activity_with_cvx_code(self) -> None:
        """Immunization Activity with CVX code should be valid."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="141" codeSystem="2.16.840.1.113883.12.292"
                              displayName="Influenza, seasonal, injectable"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        imm = parse_ccda_fragment(xml, SubstanceAdministration)
        assert imm is not None
        assert imm.consumable.manufactured_product.manufactured_material.code.code == "141"
        assert imm.consumable.manufactured_product.manufactured_material.code.code_system == "2.16.840.1.113883.12.292"

    def test_immunization_activity_with_negation_ind(self) -> None:
        """Immunization Activity with negationInd should be valid."""
        xml = """
        <substanceAdministration xmlns="urn:hl7-org:v3"
                                 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                                 classCode="SBADM" moodCode="EVN" negationInd="true">
            <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
            <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20200301"/>
            </effectiveTime>
            <consumable>
                <manufacturedProduct classCode="MANU">
                    <manufacturedMaterial>
                        <code code="88" codeSystem="2.16.840.1.113883.12.292"
                              displayName="Influenza virus vaccine"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </consumable>
        </substanceAdministration>
        """
        imm = parse_ccda_fragment(xml, SubstanceAdministration)
        assert imm is not None
        assert imm.negation_ind is True
