from __future__ import annotations

from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None

class TestImmunizationNegation:
    def test_converts_negated_immunization_reason(
        self, ccda_immunization_negated: str
    ) -> None:
        """Test that negated immunization converts refusal reason to statusReason."""
        ccda_doc = wrap_in_ccda_document(ccda_immunization_negated, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"

        # Verify reason is mapped to statusReason, not reasonCode
        assert "statusReason" in immunization
        assert "reasonCode" not in immunization

        # Verify the reason content
        reason = immunization["statusReason"]
        coding = reason["coding"][0]
        assert coding["code"] == "PATOBJ"
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActReason"

    def test_medical_precaution_refusal_reason(self) -> None:
        """Test MEDPREC (medical precaution) refusal reason maps to statusReason."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="MEDPREC" codeSystem="2.16.840.1.113883.5.8" displayName="Medical precaution"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        assert immunization["statusReason"]["coding"][0]["code"] == "MEDPREC"

    def test_immunity_refusal_reason(self) -> None:
        """Test IMMUNE (already immune) refusal reason maps to statusReason."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f93"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="IMMUNE" codeSystem="2.16.840.1.113883.5.8" displayName="Immunity"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        assert immunization["statusReason"]["coding"][0]["code"] == "IMMUNE"

    def test_refusal_reason_in_observation_value(self) -> None:
        """Test refusal reason in observation.value (instead of observation.code) maps correctly."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f94"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="59037007" codeSystem="2.16.840.1.113883.6.96" displayName="Refusal reason"/>
            <value xsi:type="CD" code="RELIG" codeSystem="2.16.840.1.113883.5.8" displayName="Religious objection"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        # Should find RELIG in observation.value, not the generic code in observation.code
        assert immunization["statusReason"]["coding"][0]["code"] == "RELIG"

    def test_out_of_stock_refusal_reason(self) -> None:
        """Test OSTOCK (out of stock) refusal reason maps to statusReason."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f95"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="OSTOCK" codeSystem="2.16.840.1.113883.5.8" displayName="Product out of stock"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        assert immunization["statusReason"]["coding"][0]["code"] == "OSTOCK"

    def test_multiple_refusal_reasons_uses_first(self) -> None:
        """Test that multiple refusal reasons uses the first one for statusReason."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f96"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="PATOBJ" codeSystem="2.16.840.1.113883.5.8" displayName="Patient objection"/>
        </observation>
    </entryRelationship>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
            <code code="RELIG" codeSystem="2.16.840.1.113883.5.8" displayName="Religious objection"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        # Should use the first refusal reason (PATOBJ)
        assert immunization["statusReason"]["coding"][0]["code"] == "PATOBJ"

    def test_refusal_reason_without_template_but_valid_code(self) -> None:
        """Test that refusal reason is recognized by code even without template ID."""
        ccda_entry = """
<substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="true">
    <templateId root="2.16.840.1.113883.10.20.22.4.52"/>
    <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f97"/>
    <statusCode code="completed"/>
    <effectiveTime value="20130815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54"/>
            <manufacturedMaterial>
                <code code="140" codeSystem="2.16.840.1.113883.12.292" displayName="Influenza vaccine"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <code code="VACSAF" codeSystem="2.16.840.1.113883.5.8" displayName="Vaccine safety concerns"/>
        </observation>
    </entryRelationship>
</substanceAdministration>
"""
        ccda_doc = wrap_in_ccda_document(ccda_entry, TemplateIds.IMMUNIZATIONS_SECTION)
        bundle = convert_document(ccda_doc)["bundle"]

        immunization = _find_resource_in_bundle(bundle, "Immunization")
        assert immunization is not None
        assert immunization["status"] == "not-done"
        assert "statusReason" in immunization
        # Should recognize VACSAF as a refusal reason by code, even without template
        assert immunization["statusReason"]["coding"][0]["code"] == "VACSAF"
