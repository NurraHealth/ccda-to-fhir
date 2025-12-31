"""E2E tests for SDOH category mapping in Social History observations."""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document

SOCIAL_HISTORY_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.17"


def _find_observation_by_loinc(bundle: JSONObject, loinc_code: str) -> JSONObject | None:
    """Find an Observation with the given LOINC code in the bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Observation":
            code = resource.get("code", {})
            for coding in code.get("coding", []):
                if coding.get("code") == loinc_code and coding.get("system") == "http://loinc.org":
                    return resource
    return None


def _create_social_history_observation(loinc_code: str, loinc_display: str, value: str = "Yes") -> str:
    """Create a C-CDA social history observation (without entry wrapper - that's added by wrap_in_ccda_document)."""
    return f"""
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
            <id root="test-obs-{loinc_code}"/>
            <code code="{loinc_code}" displayName="{loinc_display}"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="ST">{value}</value>
        </observation>
    """


class TestSDOHCategoryMapping:
    """Tests for SDOH category mapping based on LOINC codes."""

    def test_food_insecurity_hunger_vital_sign(self) -> None:
        """Test that Hunger Vital Sign (88121-9) gets food-insecurity category."""
        ccda_entry = _create_social_history_observation(
            "88121-9", "Hunger Vital Sign [HVS]", "At risk"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "88121-9")
        assert observation is not None, "Observation should be created"

        # Should have both social-history and food-insecurity categories
        categories = observation.get("category", [])
        assert len(categories) == 2, "Should have 2 categories"

        # Check social-history category
        social_history_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "social-history" for c in cat.get("coding", []))),
            None
        )
        assert social_history_cat is not None, "Should have social-history category"
        assert social_history_cat["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

        # Check food-insecurity category
        food_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "food-insecurity" for c in cat.get("coding", []))),
            None
        )
        assert food_cat is not None, "Should have food-insecurity category"
        assert food_cat["coding"][0]["system"] == "http://hl7.org/fhir/us/sdoh-clinicalcare/CodeSystem/SDOHCC-CodeSystemTemporaryCodes"
        assert food_cat["coding"][0]["display"] == "Food Insecurity"

    def test_housing_instability_worried_losing_housing(self) -> None:
        """Test that worried about losing housing (93033-9) gets housing-instability category."""
        ccda_entry = _create_social_history_observation(
            "93033-9", "Are you worried about losing your housing [PRAPARE]", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93033-9")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check housing-instability category
        housing_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "housing-instability" for c in cat.get("coding", []))),
            None
        )
        assert housing_cat is not None
        assert housing_cat["coding"][0]["display"] == "Housing Instability"

    def test_employment_status_current(self) -> None:
        """Test that employment status (67875-5) gets employment-status category."""
        ccda_entry = _create_social_history_observation(
            "67875-5", "Employment status - current", "Employed full time"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "67875-5")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check employment-status category
        employment_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "employment-status" for c in cat.get("coding", []))),
            None
        )
        assert employment_cat is not None
        assert employment_cat["coding"][0]["display"] == "Employment Status"

    def test_transportation_insecurity_lack_of_transport(self) -> None:
        """Test that lack of transportation (93030-5) gets transportation-insecurity category."""
        ccda_entry = _create_social_history_observation(
            "93030-5", "Has lack of transportation kept you from medical appointments", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93030-5")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check transportation-insecurity category
        transport_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "transportation-insecurity" for c in cat.get("coding", []))),
            None
        )
        assert transport_cat is not None
        assert transport_cat["coding"][0]["display"] == "Transportation Insecurity"

    def test_financial_insecurity_hard_to_pay(self) -> None:
        """Test that difficulty paying for basics (76513-1) gets financial-insecurity category."""
        ccda_entry = _create_social_history_observation(
            "76513-1", "How hard is it for you to pay for the very basics", "Very hard"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "76513-1")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check financial-insecurity category
        financial_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "financial-insecurity" for c in cat.get("coding", []))),
            None
        )
        assert financial_cat is not None
        assert financial_cat["coding"][0]["display"] == "Financial Insecurity"

    def test_social_connection_how_often_see_people(self) -> None:
        """Test that social connection (93029-7) gets social-connection category."""
        ccda_entry = _create_social_history_observation(
            "93029-7", "How often do you see or talk to people that you care about", "Rarely"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93029-7")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check social-connection category
        social_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "social-connection" for c in cat.get("coding", []))),
            None
        )
        assert social_cat is not None
        assert social_cat["coding"][0]["display"] == "Social Connection"

    def test_stress_level(self) -> None:
        """Test that stress level (93038-8) gets stress category."""
        ccda_entry = _create_social_history_observation(
            "93038-8", "Stress level", "High"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93038-8")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check stress category
        stress_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "stress" for c in cat.get("coding", []))),
            None
        )
        assert stress_cat is not None
        assert stress_cat["coding"][0]["display"] == "Stress"

    def test_educational_attainment_highest_level(self) -> None:
        """Test that educational attainment (82589-3) gets educational-attainment category."""
        ccda_entry = _create_social_history_observation(
            "82589-3", "Highest level of education", "High school graduate"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "82589-3")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check educational-attainment category
        education_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "educational-attainment" for c in cat.get("coding", []))),
            None
        )
        assert education_cat is not None
        assert education_cat["coding"][0]["display"] == "Educational Attainment"

    def test_veteran_status_discharged_from_armed_forces(self) -> None:
        """Test that veteran status (93034-7) gets veteran-status category."""
        ccda_entry = _create_social_history_observation(
            "93034-7", "Discharged from the U.S. Armed Forces", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93034-7")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check veteran-status category
        veteran_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "veteran-status" for c in cat.get("coding", []))),
            None
        )
        assert veteran_cat is not None
        assert veteran_cat["coding"][0]["display"] == "Veteran Status"

    def test_intimate_partner_violence_afraid_of_partner(self) -> None:
        """Test that IPV (76501-6) gets intimate-partner-violence category."""
        ccda_entry = _create_social_history_observation(
            "76501-6", "Within the last year, have you been afraid of your partner or ex-partner", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "76501-6")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check intimate-partner-violence category
        ipv_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "intimate-partner-violence" for c in cat.get("coding", []))),
            None
        )
        assert ipv_cat is not None
        assert ipv_cat["coding"][0]["display"] == "Intimate Partner Violence"

    def test_non_sdoh_loinc_gets_only_social_history_category(self) -> None:
        """Test that a social history observation without SDOH mapping gets only social-history category."""
        # Using a generic tobacco use code that's not in our SDOH mapping
        ccda_entry = _create_social_history_observation(
            "11367-0", "History of Tobacco use", "20 pack-year history"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "11367-0")
        assert observation is not None

        categories = observation.get("category", [])
        # Should only have social-history category, no SDOH category
        assert len(categories) == 1, "Should only have 1 category (social-history)"

        social_history_cat = categories[0]
        assert social_history_cat["coding"][0]["code"] == "social-history"
        assert social_history_cat["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/observation-category"

    def test_smoking_status_gets_only_social_history_category(self) -> None:
        """Test that smoking status observation gets only social-history category (not SDOH)."""
        ccda_entry = """
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.78"/>
            <id root="smoking-obs-123"/>
            <code code="72166-2" displayName="Tobacco smoking status"
                  codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201"/>
            <value xsi:type="CD" code="449868002" displayName="Current every day smoker"
                   codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        """
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "72166-2")
        assert observation is not None

        categories = observation.get("category", [])
        # Smoking status should only have social-history, not an SDOH category
        assert len(categories) == 1
        assert categories[0]["coding"][0]["code"] == "social-history"

    def test_utility_insecurity_threatened_shutoff(self) -> None:
        """Test that utility threat (96779-4) gets utility-insecurity category."""
        ccda_entry = _create_social_history_observation(
            "96779-4", "Has the electric, gas, oil, or water company threatened to shut off", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "96779-4")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check utility-insecurity category
        utility_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "utility-insecurity" for c in cat.get("coding", []))),
            None
        )
        assert utility_cat is not None
        assert utility_cat["coding"][0]["display"] == "Utility Insecurity"

    def test_incarceration_status_jail_time(self) -> None:
        """Test that incarceration (93028-9) gets incarceration-status category."""
        ccda_entry = _create_social_history_observation(
            "93028-9", "Have you spent more than 2 nights in a row in a jail, prison", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93028-9")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check incarceration-status category
        incarceration_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "incarceration-status" for c in cat.get("coding", []))),
            None
        )
        assert incarceration_cat is not None
        assert incarceration_cat["coding"][0]["display"] == "Incarceration Status"

    def test_language_access_preferred_language(self) -> None:
        """Test that preferred language (54899-0) gets language-access category."""
        ccda_entry = _create_social_history_observation(
            "54899-0", "Preferred language", "Spanish"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "54899-0")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check language-access category
        language_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "language-access" for c in cat.get("coding", []))),
            None
        )
        assert language_cat is not None
        assert language_cat["coding"][0]["display"] == "Language Status"

    def test_material_hardship_unable_to_get_necessities(self) -> None:
        """Test that material hardship (93031-3) gets material-hardship category."""
        ccda_entry = _create_social_history_observation(
            "93031-3", "Have you or any family members you live with been unable to get", "Yes"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93031-3")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check material-hardship category
        material_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "material-hardship" for c in cat.get("coding", []))),
            None
        )
        assert material_cat is not None
        assert material_cat["coding"][0]["display"] == "Material Hardship"

    def test_health_insurance_coverage_status_primary_insurance(self) -> None:
        """Test that primary insurance (76437-3) gets health-insurance-coverage-status category."""
        ccda_entry = _create_social_history_observation(
            "76437-3", "Primary insurance", "Medicare"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "76437-3")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check health-insurance-coverage-status category
        insurance_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "health-insurance-coverage-status" for c in cat.get("coding", []))),
            None
        )
        assert insurance_cat is not None
        assert insurance_cat["coding"][0]["display"] == "Health Insurance Coverage Status"

    def test_inadequate_housing_feel_safe_at_home(self) -> None:
        """Test that safety at home (93026-3) gets inadequate-housing category."""
        ccda_entry = _create_social_history_observation(
            "93026-3", "Do you feel physically and emotionally safe where you currently live", "No"
        )
        ccda_doc = wrap_in_ccda_document(ccda_entry, SOCIAL_HISTORY_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)["bundle"]

        observation = _find_observation_by_loinc(bundle, "93026-3")
        assert observation is not None

        categories = observation.get("category", [])
        assert len(categories) == 2

        # Check inadequate-housing category
        housing_cat = next(
            (cat for cat in categories
             if any(c.get("code") == "inadequate-housing" for c in cat.get("coding", []))),
            None
        )
        assert housing_cat is not None
        assert housing_cat["coding"][0]["display"] == "Inadequate Housing"
