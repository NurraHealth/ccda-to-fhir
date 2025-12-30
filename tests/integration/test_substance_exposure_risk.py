"""E2E tests for substanceExposureRisk extension in AllergyIntolerance resources."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestSubstanceExposureRiskExtension:
    """E2E tests for substanceExposureRisk extension.

    Per FHIR spec and C-CDA on FHIR IG, the substanceExposureRisk extension
    is used when documenting "no known allergy" to a SPECIFIC substance
    where no pre-coordinated negated concept code exists.

    This is distinct from general "no known allergies" which use negated
    concept codes (e.g., SNOMED 716186003 "No known allergy").

    Reference:
    - http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk
    - http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-allergies.html
    """

    def test_no_known_specific_substance_uses_extension(self) -> None:
        """Test that no known allergy to specific substance uses substanceExposureRisk extension."""
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        # Find the AllergyIntolerance resource
        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None, "AllergyIntolerance resource should be created"

        # Verify substanceExposureRisk extension exists
        extensions = allergy.get("extension", [])
        exposure_risk_ext = None
        for ext in extensions:
            if ext["url"] == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk":
                exposure_risk_ext = ext
                break

        assert exposure_risk_ext is not None, \
            "substanceExposureRisk extension should be present for specific substance no-known allergy"

    def test_substance_exposure_risk_has_substance_sub_extension(self) -> None:
        """Test that substanceExposureRisk extension contains substance sub-extension."""
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        # Get the substanceExposureRisk extension
        exposure_risk_ext = None
        for ext in allergy.get("extension", []):
            if ext["url"] == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk":
                exposure_risk_ext = ext
                break

        # Verify substance sub-extension
        sub_extensions = exposure_risk_ext.get("extension", [])
        substance_ext = None
        for sub_ext in sub_extensions:
            if sub_ext["url"] == "substance":
                substance_ext = sub_ext
                break

        assert substance_ext is not None, "substance sub-extension should be present"
        assert "valueCodeableConcept" in substance_ext, "substance should be a CodeableConcept"

        # Verify substance is Penicillin V
        substance_concept = substance_ext["valueCodeableConcept"]
        rxnorm_coding = None
        for coding in substance_concept.get("coding", []):
            if coding.get("system") == "http://www.nlm.nih.gov/research/umls/rxnorm":
                rxnorm_coding = coding
                break

        assert rxnorm_coding is not None, "RxNorm coding should be present"
        assert rxnorm_coding["code"] == "70618", "Should be Penicillin V code"
        assert rxnorm_coding["display"] == "Penicillin V"

    def test_substance_exposure_risk_has_exposure_risk_sub_extension(self) -> None:
        """Test that substanceExposureRisk extension contains exposureRisk sub-extension."""
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        # Get the substanceExposureRisk extension
        exposure_risk_ext = None
        for ext in allergy.get("extension", []):
            if ext["url"] == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk":
                exposure_risk_ext = ext
                break

        # Verify exposureRisk sub-extension
        sub_extensions = exposure_risk_ext.get("extension", [])
        exposure_risk_sub_ext = None
        for sub_ext in sub_extensions:
            if sub_ext["url"] == "exposureRisk":
                exposure_risk_sub_ext = sub_ext
                break

        assert exposure_risk_sub_ext is not None, "exposureRisk sub-extension should be present"
        assert "valueCodeableConcept" in exposure_risk_sub_ext, "exposureRisk should be a CodeableConcept"

        # Verify exposureRisk value
        concept = exposure_risk_sub_ext["valueCodeableConcept"]
        coding = concept["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/allerg-intol-substance-exp-risk"
        assert coding["code"] == "no-known-reaction-risk"
        assert coding["display"] == "No Known Reaction Risk"

    def test_substance_exposure_risk_omits_code_element(self) -> None:
        """Test that AllergyIntolerance.code is omitted when using substanceExposureRisk extension.

        Per FHIR spec: When substanceExposureRisk is present, the AllergyIntolerance.code
        element SHALL be omitted to prevent redundant or conflicting information.
        """
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        assert "code" not in allergy, \
            "AllergyIntolerance.code SHALL be omitted when substanceExposureRisk extension is used"

    def test_substance_exposure_risk_preserves_type_and_category(self) -> None:
        """Test that type and category are preserved when using substanceExposureRisk extension."""
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        # Type and category should still be set based on observation.value
        assert allergy.get("type") == "allergy"
        assert allergy.get("category") == ["medication"]

    def test_substance_exposure_risk_food_allergy(self) -> None:
        """Test substanceExposureRisk extension for food allergy (no known peanut allergy)."""
        with open("tests/integration/fixtures/ccda/no_known_specific_food_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify extension exists
        exposure_risk_ext = None
        for ext in allergy.get("extension", []):
            if ext["url"] == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk":
                exposure_risk_ext = ext
                break

        assert exposure_risk_ext is not None

        # Verify substance is Peanut
        sub_extensions = exposure_risk_ext.get("extension", [])
        substance_ext = None
        for sub_ext in sub_extensions:
            if sub_ext["url"] == "substance":
                substance_ext = sub_ext
                break

        substance_concept = substance_ext["valueCodeableConcept"]
        snomed_coding = None
        for coding in substance_concept.get("coding", []):
            if coding.get("system") == "http://snomed.info/sct":
                snomed_coding = coding
                break

        assert snomed_coding is not None
        assert snomed_coding["code"] == "256349002", "Should be Peanut SNOMED code"

        # Verify type and category
        assert allergy.get("type") == "allergy"
        assert allergy.get("category") == ["food"]

    def test_general_no_known_allergy_uses_negated_code_not_extension(self) -> None:
        """Test that general no known allergy uses negated concept code, not extension.

        When participant has nullFlavor="NA" (no specific substance), we should use
        the negated concept code approach (existing behavior), NOT the extension.
        """
        with open("tests/integration/fixtures/ccda/no_known_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")
        assert allergy is not None

        # Verify substanceExposureRisk extension is NOT present
        has_exposure_risk_ext = False
        for ext in allergy.get("extension", []):
            if ext["url"] == "http://hl7.org/fhir/StructureDefinition/allergyintolerance-substanceExposureRisk":
                has_exposure_risk_ext = True
                break

        assert not has_exposure_risk_ext, \
            "substanceExposureRisk extension should NOT be used for general no known allergy"

        # Verify code is present (negated concept)
        assert "code" in allergy, "AllergyIntolerance.code should be present for general no known allergy"

        # Verify it's the correct negated concept code
        snomed_coding = None
        for coding in allergy["code"].get("coding", []):
            if coding.get("system") == "http://snomed.info/sct":
                snomed_coding = coding
                break

        assert snomed_coding is not None
        assert snomed_coding["code"] == "716186003", "Should use 'No known allergy' negated concept"

    def test_substance_exposure_risk_has_confirmed_verification_status(self) -> None:
        """Test that substance exposure risk allergies have verificationStatus 'confirmed'.

        Even though this is documenting "no known allergy to X", it's a confirmed
        absence, not a refutation of a specific allergy assertion.
        """
        with open("tests/integration/fixtures/ccda/no_known_specific_substance_allergy.xml") as f:
            concern_act_xml = f.read()

        ccda_xml = wrap_in_ccda_document(concern_act_xml, ALLERGIES_TEMPLATE_ID)
        bundle = convert_document(ccda_xml)["bundle"]

        allergy = _find_resource_in_bundle(bundle, "AllergyIntolerance")

        verification_status = allergy.get("verificationStatus", {})
        coding = verification_status.get("coding", [{}])[0]
        assert coding.get("code") == "confirmed"
