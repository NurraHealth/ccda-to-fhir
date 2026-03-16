"""Unit tests for Referral converter.

Tests C-CDA referral entries to FHIR ServiceRequest (referral category) conversion
following:
- HL7 C-CDA R2.1 Planned Act / Planned Encounter templates
- US Core ServiceRequest Profile
- SNOMED CT referral codes
"""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from ccda_to_fhir.ccda.models.act import Act as CCDAAct
from ccda_to_fhir.ccda.models.author import AssignedAuthor, Author
from ccda_to_fhir.ccda.models.datatypes import CD, CE, CS, II, IVL_TS, TS
from ccda_to_fhir.ccda.models.encounter import Encounter as CCDAEncounter
from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer
from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.converters.references import ReferenceRegistry
from ccda_to_fhir.converters.referral import ReferralConverter, is_referral_code
from ccda_to_fhir.types import FHIRReference

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_reference_registry() -> ReferenceRegistry:
    """Create a mock reference registry."""
    registry = Mock(spec=ReferenceRegistry)
    registry.get_patient_reference = Mock(
        return_value=FHIRReference(reference="urn:uuid:a1b2c3d4-e5f6-7890-abcd-ef1234567890")
    )
    registry.get_encounter_reference = Mock(return_value=None)
    registry.has_resource = Mock(return_value=True)
    return registry


@pytest.fixture
def basic_referral_act() -> CCDAAct:
    """Basic referral as a Planned Act with referral SNOMED code."""
    return CCDAAct(
        class_code="ACT",
        mood_code="RQO",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.39")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="ref-001")],
        code=CD(
            code="3457005",
            code_system="2.16.840.1.113883.6.96",
            display_name="Patient referral",
        ),
        status_code=CS(code="active"),
    )


@pytest.fixture
def referral_with_details() -> CCDAAct:
    """Referral with full details: author, performer, effective time."""
    return CCDAAct(
        class_code="ACT",
        mood_code="RQO",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.39")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="ref-002")],
        code=CD(
            code="306206005",
            code_system="2.16.840.1.113883.6.96",
            display_name="Referral to service",
        ),
        status_code=CS(code="active"),
        effective_time=IVL_TS(
            low=TS(value="20240601"),
            high=TS(value="20240901"),
        ),
        priority_code=CE(
            code="R",
            code_system="2.16.840.1.113883.5.7",
            display_name="Routine",
        ),
        author=[
            Author(
                time=TS(value="20240501140000-0500"),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                ),
            )
        ],
        performer=[
            Performer(
                assigned_entity=AssignedEntity(
                    id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
                ),
            )
        ],
    )


@pytest.fixture
def referral_encounter() -> CCDAEncounter:
    """Referral as a Planned Encounter with referral code and INT moodCode."""
    return CCDAEncounter(
        class_code="ENC",
        mood_code="INT",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.40")],
        id=[II(root="2.16.840.1.113883.19.5.99999", extension="ref-003")],
        code=CD(
            code="3457005",
            code_system="2.16.840.1.113883.6.96",
            display_name="Patient referral",
        ),
        status_code=CS(code="active"),
        effective_time=IVL_TS(low=TS(value="20240601")),
    )


# ============================================================================
# MoodCode Validation Tests
# ============================================================================


class TestMoodCodeValidation:
    """Test moodCode validation for referral conversion."""

    @pytest.mark.parametrize("mood_code", ["INT", "RQO", "PRP", "ARQ", "PRMS"])
    def test_valid_mood_codes_accepted(self, mood_code, mock_reference_registry):
        """All planned moodCodes should be accepted."""
        act = CCDAAct(
            class_code="ACT",
            mood_code=mood_code,
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["resourceType"] == FHIRCodes.ResourceTypes.SERVICE_REQUEST

    def test_evn_mood_code_rejected(self, mock_reference_registry):
        """EVN moodCode should be rejected with clear message."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="EVN",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="Procedure converter"):
            converter.convert(act)

    def test_missing_mood_code_rejected(self, mock_reference_registry):
        """Missing moodCode should raise."""
        act = CCDAAct(
            class_code="ACT",
            mood_code=None,
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        with pytest.raises(ValueError, match="must have a moodCode"):
            converter.convert(act)


# ============================================================================
# Referral Category Tests
# ============================================================================


class TestReferralCategory:
    """Test that referral ServiceRequests always have referral category."""

    def test_referral_category_present(self, basic_referral_act, mock_reference_registry):
        """Category should contain Patient referral SNOMED code."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "category" in result
        category = result["category"][0]
        assert category["coding"][0]["code"] == "3457005"
        assert category["coding"][0]["display"] == "Patient referral"
        assert category["coding"][0]["system"] == "http://snomed.info/sct"


# ============================================================================
# US Core Profile Tests
# ============================================================================


class TestUSCoreProfile:
    """Test US Core ServiceRequest profile compliance."""

    def test_us_core_profile_set(self, basic_referral_act, mock_reference_registry):
        """Must have US Core ServiceRequest profile."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "meta" in result
        assert "us-core-servicerequest" in result["meta"]["profile"][0]

    def test_required_fields_present(self, basic_referral_act, mock_reference_registry):
        """Required US Core fields: status, intent, subject."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "status" in result
        assert "intent" in result
        assert "subject" in result

    def test_subject_is_patient_reference(self, basic_referral_act, mock_reference_registry):
        """Subject must be a Patient reference."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert result["subject"]["reference"].startswith("urn:uuid:")


# ============================================================================
# Status Mapping Tests
# ============================================================================


class TestStatusMapping:
    """Test status code mapping."""

    def test_active_maps_to_active(self, basic_referral_act, mock_reference_registry):
        """active → active."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert result["status"] == "active"

    def test_completed_maps_to_completed(self, mock_reference_registry):
        """completed → completed."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="RQO",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="completed"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["status"] == "completed"

    def test_cancelled_maps_to_revoked(self, mock_reference_registry):
        """cancelled → revoked."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="RQO",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="cancelled"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["status"] == "revoked"

    def test_null_flavor_unk_maps_to_unknown(self, mock_reference_registry):
        """nullFlavor UNK → unknown."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="RQO",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(null_flavor="UNK"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["status"] == "unknown"


# ============================================================================
# Intent Mapping Tests
# ============================================================================


class TestIntentMapping:
    """Test moodCode to intent mapping."""

    def test_rqo_maps_to_order(self, basic_referral_act, mock_reference_registry):
        """RQO → order."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert result["intent"] == "order"

    def test_int_maps_to_plan(self, mock_reference_registry):
        """INT → plan."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="INT",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["intent"] == "plan"

    def test_prp_maps_to_proposal(self, mock_reference_registry):
        """PRP → proposal."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="PRP",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert result["intent"] == "proposal"


# ============================================================================
# Occurrence Tests
# ============================================================================


class TestOccurrence:
    """Test effectiveTime to occurrence[x] mapping."""

    def test_period_occurrence(self, referral_with_details, mock_reference_registry):
        """effectiveTime with low+high → occurrencePeriod."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_with_details)
        assert "occurrencePeriod" in result
        assert "start" in result["occurrencePeriod"]
        assert "end" in result["occurrencePeriod"]

    def test_datetime_occurrence(self, mock_reference_registry):
        """effectiveTime with value → occurrenceDateTime."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="RQO",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(value="20240615"),
        )
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(act)
        assert "occurrenceDateTime" in result

    def test_no_effective_time(self, basic_referral_act, mock_reference_registry):
        """No effectiveTime → no occurrence."""
        basic_referral_act.effective_time = None
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "occurrenceDateTime" not in result
        assert "occurrencePeriod" not in result


# ============================================================================
# AuthoredOn Tests
# ============================================================================


class TestAuthoredOn:
    """Test author time to authoredOn mapping."""

    def test_authored_on_present(self, referral_with_details, mock_reference_registry):
        """Author time → authoredOn."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_with_details)
        assert "authoredOn" in result

    def test_no_author_no_authored_on(self, basic_referral_act, mock_reference_registry):
        """No author → no authoredOn."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "authoredOn" not in result


# ============================================================================
# Performer Tests
# ============================================================================


class TestPerformer:
    """Test performer to FHIR performer mapping."""

    def test_performer_present(self, referral_with_details, mock_reference_registry):
        """Performer entries → FHIR performer references."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_with_details)
        assert "performer" in result
        assert len(result["performer"]) > 0

    def test_no_performer(self, basic_referral_act, mock_reference_registry):
        """No performer → no performer field."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "performer" not in result


# ============================================================================
# Priority Tests
# ============================================================================


class TestPriority:
    """Test priorityCode mapping."""

    def test_routine_priority(self, referral_with_details, mock_reference_registry):
        """R → routine."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_with_details)
        assert result["priority"] == "routine"

    def test_no_priority(self, basic_referral_act, mock_reference_registry):
        """No priorityCode → no priority field."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "priority" not in result


# ============================================================================
# Code Tests
# ============================================================================


class TestCode:
    """Test code conversion."""

    def test_code_present(self, basic_referral_act, mock_reference_registry):
        """Code should be converted to FHIR CodeableConcept."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "code" in result
        assert result["code"]["coding"][0]["code"] == "3457005"

    def test_referral_to_service_code(self, referral_with_details, mock_reference_registry):
        """Referral to service code should convert correctly."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_with_details)
        assert result["code"]["coding"][0]["code"] == "306206005"


# ============================================================================
# Encounter Input Tests (Planned Encounter as referral)
# ============================================================================


class TestEncounterInput:
    """Test referral conversion from Planned Encounter entries."""

    def test_encounter_referral(self, referral_encounter, mock_reference_registry):
        """Planned Encounter with referral code → ServiceRequest (referral)."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(referral_encounter)
        assert result["resourceType"] == "ServiceRequest"
        assert result["category"][0]["coding"][0]["code"] == "3457005"


# ============================================================================
# is_referral_code Tests
# ============================================================================


class TestIsReferralCode:
    """Test the is_referral_code helper function."""

    def test_patient_referral_code(self):
        """SNOMED 3457005 is a referral code."""
        code = CD(code="3457005", code_system="2.16.840.1.113883.6.96")
        assert is_referral_code(code) is True

    def test_referral_to_service_code(self):
        """SNOMED 306206005 is a referral code."""
        code = CD(code="306206005", code_system="2.16.840.1.113883.6.96")
        assert is_referral_code(code) is True

    def test_non_referral_code(self):
        """Non-referral SNOMED code should return False."""
        code = CD(code="80146002", code_system="2.16.840.1.113883.6.96")
        assert is_referral_code(code) is False

    def test_none_code(self):
        """None code should return False."""
        assert is_referral_code(None) is False

    def test_non_snomed_code(self):
        """Non-SNOMED code should return False even with matching code value."""
        code = CD(code="3457005", code_system="2.16.840.1.113883.6.1")
        assert is_referral_code(code) is False

    def test_referral_in_translation(self):
        """Referral code in translation should be detected."""
        code = CD(
            code="99999",
            code_system="2.16.840.1.113883.6.12",
            translation=[
                CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            ],
        )
        assert is_referral_code(code) is True

    def test_null_code_value(self):
        """Code with null value should return False."""
        code = CD(code=None, code_system="2.16.840.1.113883.6.96")
        assert is_referral_code(code) is False


# ============================================================================
# Missing Registry Tests
# ============================================================================


class TestMissingRegistry:
    """Test behavior when reference_registry is missing."""

    def test_no_registry_raises(self):
        """Missing registry should raise ValueError."""
        act = CCDAAct(
            class_code="ACT",
            mood_code="RQO",
            id=[II(root="test")],
            code=CD(code="3457005", code_system="2.16.840.1.113883.6.96"),
            status_code=CS(code="active"),
        )
        converter = ReferralConverter()
        with pytest.raises(ValueError, match="reference_registry is required"):
            converter.convert(act)


# ============================================================================
# ID Generation Tests
# ============================================================================


class TestIDGeneration:
    """Test referral ServiceRequest ID generation."""

    def test_id_generated(self, basic_referral_act, mock_reference_registry):
        """ID should be generated from C-CDA identifier."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "id" in result
        assert isinstance(result["id"], str)

    def test_identifiers_preserved(self, basic_referral_act, mock_reference_registry):
        """C-CDA identifiers should be preserved."""
        converter = ReferralConverter(reference_registry=mock_reference_registry)
        result = converter.convert(basic_referral_act)
        assert "identifier" in result
        assert len(result["identifier"]) > 0
