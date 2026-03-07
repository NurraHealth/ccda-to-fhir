"""Unit tests for CoverageConverter."""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import AD, CE, CS, II, IVL_TS, ON, TEL, TS
from ccda_to_fhir.ccda.models.entry_relationship import EntryRelationship
from ccda_to_fhir.ccda.models.participant import Participant, ParticipantRole
from ccda_to_fhir.ccda.models.performer import (
    AssignedEntity,
    Performer,
    RepresentedOrganization,
)
from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.converters.coverage import CoverageConverter, convert_coverage_activity
from ccda_to_fhir.converters.references import ReferenceRegistry


@pytest.fixture
def reference_registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "patient-123"})
    return reg


@pytest.fixture
def converter(reference_registry) -> CoverageConverter:
    return CoverageConverter(reference_registry=reference_registry)


@pytest.fixture
def payor_performer() -> Performer:
    return Performer(
        type_code="PRF",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.87")],
        assigned_entity=AssignedEntity(
            id=[II(root="1728b8aa-11b5-43bf-92c6-5f8f5cd0cb00", extension="70322")],
            code=CE(
                code="PAYOR",
                code_system="2.16.840.1.113883.5.110",
                display_name="Invoice Payor",
            ),
            represented_organization=RepresentedOrganization(
                name=[ON(value="BLUE CROSS BLUE SHIELD")],
                telecom=[TEL(value="tel: (877) 842-3210", use="WP")],
                addr=[AD(
                    use="WP",
                    street_address_line=["PO BOX 31362"],
                    city="SALT LAKE CITY",
                    state="UT",
                    postal_code="84131-0362",
                )],
            ),
        ),
    )


@pytest.fixture
def guarantor_performer() -> Performer:
    return Performer(
        type_code="PRF",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.88")],
        assigned_entity=AssignedEntity(
            id=[II(root="bd7a9d62-609b-4fbe-a542-13b776758b64")],
            code=CE(
                code="GUAR",
                code_system="2.16.840.1.113883.5.110",
                display_name="Guarantor",
            ),
        ),
    )


@pytest.fixture
def cov_participant() -> Participant:
    return Participant(
        type_code="COV",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.89")],
        participant_role=ParticipantRole(
            id=[II(root="381e9f0c-ad3c-4b00-bc33-bba6c90386d0", extension="928489131")],
            code=CE(
                code="SELF",
                code_system="2.16.840.1.113883.5.111",
                display_name="self",
            ),
        ),
    )


@pytest.fixture
def hld_participant() -> Participant:
    return Participant(
        type_code="HLD",
        template_id=[II(root="2.16.840.1.113883.10.20.22.4.90")],
        participant_role=ParticipantRole(
            id=[II(root="b38d9bca-28ab-4980-b602-3308a6cec5b3")],
        ),
    )


@pytest.fixture
def policy_activity(payor_performer, guarantor_performer, cov_participant, hld_participant) -> Act:
    return Act(
        class_code="ACT",
        mood_code="EVN",
        template_id=[
            II(root="2.16.840.1.113883.10.20.22.4.61", extension="2023-05-01"),
            II(root="2.16.840.1.113883.10.20.22.4.61"),
        ],
        id=[II(root="e9af786d-a9b0-4eb0-834f-d2d64961bdd7", extension="BC123456789")],
        code=CE(
            code="OT",
            code_system="2.16.840.1.113883.6.255.1336",
            display_name="Other",
        ),
        status_code=CS(code="completed"),
        performer=[payor_performer, guarantor_performer],
        participant=[cov_participant, hld_participant],
    )


@pytest.fixture
def coverage_activity(policy_activity) -> Act:
    return Act(
        class_code="ACT",
        mood_code="EVN",
        template_id=[
            II(root="2.16.840.1.113883.10.20.22.4.60", extension="2023-05-01"),
            II(root="2.16.840.1.113883.10.20.22.4.60"),
        ],
        id=[II(root="7de6c58e-b197-4b93-8379-df1b01659622")],
        code=CE(code="48768-6", code_system="2.16.840.1.113883.6.1"),
        status_code=CS(code="completed"),
        entry_relationship=[
            EntryRelationship(
                type_code="COMP",
                sequence_number=1,
                act=policy_activity,
            )
        ],
    )


def _make_policy(
    *,
    status: str = "completed",
    policy_id: list[II] | None = None,
    code: CE | None = None,
    performers: list[Performer] | None = None,
    participants: list[Participant] | None = None,
    effective_time: IVL_TS | None = None,
) -> Act:
    """Helper to build a minimal Policy Activity Act."""
    return Act(
        class_code="ACT",
        mood_code="EVN",
        template_id=[II(root=TemplateIds.POLICY_ACTIVITY)],
        id=policy_id if policy_id is not None else [II(root="test-root")],
        code=code,
        status_code=CS(code=status),
        performer=performers,
        participant=participants,
        effective_time=effective_time,
    )


def _wrap_in_coverage_activity(
    *policy_acts: Act,
    sequence_numbers: list[int | None] | None = None,
) -> Act:
    """Wrap one or more Policy Activities in a Coverage Activity."""
    ers = []
    for i, policy in enumerate(policy_acts):
        seq = sequence_numbers[i] if sequence_numbers else None
        ers.append(EntryRelationship(
            type_code="COMP",
            sequence_number=seq,
            act=policy,
        ))
    return Act(
        template_id=[II(root=TemplateIds.COVERAGE_ACTIVITY)],
        status_code=CS(code="completed"),
        entry_relationship=ers,
    )


class TestCoverageConverter:
    def test_produces_coverage_and_organization(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        types = [r["resourceType"] for r in result]
        assert "Coverage" in types
        assert "Organization" in types

    def test_coverage_fields(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert coverage["status"] == "active"
        assert coverage["order"] == 1
        assert coverage["subscriberId"] == "928489131"
        assert coverage["type"]["coding"][0]["code"] == "OT"
        assert "id" in coverage

    def test_coverage_relationship_self(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert "relationship" in coverage
        coding = coverage["relationship"]["coding"][0]
        assert coding["code"] == "self"
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/subscriber-relationship"

    def test_payor_references_organization(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        org = next(r for r in result if r["resourceType"] == "Organization")

        assert len(coverage["payor"]) == 1
        assert coverage["payor"][0]["reference"] == f"urn:uuid:{org['id']}"

    def test_organization_name(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        org = next(r for r in result if r["resourceType"] == "Organization")

        assert org["name"] == "BLUE CROSS BLUE SHIELD"

    def test_beneficiary_references_patient(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert coverage["beneficiary"]["reference"] == "urn:uuid:patient-123"

    def test_subscriber_set_when_self(self, converter, coverage_activity):
        """When relationship is SELF, subscriber references the patient."""
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert "subscriber" in coverage
        assert coverage["subscriber"]["reference"] == "urn:uuid:patient-123"

    def test_policy_holder_root_only_omits_system(self, converter, coverage_activity):
        """When HLD has only root (no extension), root is value and system is omitted."""
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert "policyHolder" in coverage
        ident = coverage["policyHolder"]["identifier"]
        # root is used as value, so system must be omitted to avoid duplication
        assert "system" not in ident
        assert ident["value"] == "b38d9bca-28ab-4980-b602-3308a6cec5b3"

    def test_policy_holder_with_root_and_extension(self, converter):
        """When HLD has both root and extension, system is mapped from root."""
        policy = _make_policy(participants=[Participant(
            type_code="HLD",
            participant_role=ParticipantRole(
                id=[II(root="2.16.840.1.113883.4.1", extension="HLD-54321")],
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        ident = coverage["policyHolder"]["identifier"]
        assert "system" in ident
        assert ident["value"] == "HLD-54321"

    def test_policy_holder_no_root_omits_system(self, converter):
        """When HLD participant has no root OID, system key is omitted."""
        policy = _make_policy(participants=[Participant(
            type_code="HLD",
            participant_role=ParticipantRole(
                id=[II(root=None, extension="HLD-EXT-123")],
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "system" not in coverage["policyHolder"]["identifier"]
        assert coverage["policyHolder"]["identifier"]["value"] == "HLD-EXT-123"

    def test_payor_identified_by_template_id_without_code(self, converter):
        """PAYOR performer identified by templateId .87 even without code."""
        payor = Performer(
            type_code="PRF",
            template_id=[II(root=TemplateIds.PAYER_PERFORMER)],
            assigned_entity=AssignedEntity(
                id=[II(root="payor-oid", extension="12345")],
                represented_organization=RepresentedOrganization(
                    name=[ON(value="AETNA")],
                ),
            ),
        )
        policy = _make_policy(performers=[payor])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        org = next((r for r in result if r["resourceType"] == "Organization"), None)
        assert org is not None
        assert org["name"] == "AETNA"
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "payor" in coverage

    def test_cov_participant_time_overrides_policy_effective_time(self, converter):
        """COV participant time takes priority over policy effectiveTime for period."""
        policy = _make_policy(
            effective_time=IVL_TS(
                low=TS(value="20200101"),
                high=TS(value="20201231"),
            ),
            participants=[Participant(
                type_code="COV",
                participant_role=ParticipantRole(
                    id=[II(root="member-root", extension="M999")],
                    code=CE(code="SELF", code_system="2.16.840.1.113883.5.111"),
                ),
                time=IVL_TS(
                    low=TS(value="20210601"),
                    high=TS(value="20220531"),
                ),
            )],
        )
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        # COV participant time should win
        assert "2021" in coverage["period"]["start"]
        assert "2022" in coverage["period"]["end"]

    def test_subscriber_not_set_for_non_self(self, converter):
        """When relationship is not SELF, subscriber is not set."""
        policy = _make_policy(participants=[Participant(
            type_code="COV",
            participant_role=ParticipantRole(
                id=[II(root="member-root", extension="DEP001")],
                code=CE(code="CHILD", code_system="2.16.840.1.113883.5.111"),
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "subscriber" not in coverage
        assert coverage["relationship"]["coding"][0]["code"] == "child"

    def test_empty_entry_relationships(self, converter):
        act = Act(
            template_id=[II(root=TemplateIds.COVERAGE_ACTIVITY)],
            status_code=CS(code="completed"),
        )
        result = converter.convert(act)
        assert result == []

    def test_no_payor_defaults_to_patient(self, converter):
        """When no PAYOR performer exists, payor defaults to patient."""
        policy = _make_policy()
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        # payor should default to patient reference
        assert coverage["payor"][0]["reference"] == "urn:uuid:patient-123"


class TestMultiplePolicyActivities:
    def test_multiple_policies_produce_multiple_coverages(self, converter):
        """Each Policy Activity in a Coverage Activity produces its own Coverage."""
        policy1 = _make_policy(
            policy_id=[II(root="policy-1-root", extension="POL-001")],
        )
        policy2 = _make_policy(
            policy_id=[II(root="policy-2-root", extension="POL-002")],
        )
        act = _wrap_in_coverage_activity(policy1, policy2, sequence_numbers=[1, 2])
        result = converter.convert(act)
        coverages = [r for r in result if r["resourceType"] == "Coverage"]
        assert len(coverages) == 2
        assert coverages[0]["order"] == 1
        assert coverages[1]["order"] == 2
        # IDs should differ
        assert coverages[0]["id"] != coverages[1]["id"]

    def test_non_comp_entry_relationships_skipped(self, converter):
        """Only COMP entryRelationships produce Coverage resources."""
        policy = _make_policy()
        act = Act(
            template_id=[II(root=TemplateIds.COVERAGE_ACTIVITY)],
            status_code=CS(code="completed"),
            entry_relationship=[
                EntryRelationship(type_code="RSON", act=policy),
            ],
        )
        result = converter.convert(act)
        assert result == []


class TestStatusMapping:
    @pytest.mark.parametrize("ccda_status,fhir_status", [
        ("completed", "active"),
        ("active", "active"),
        ("suspended", "cancelled"),
        ("aborted", "cancelled"),
        ("nullified", "entered-in-error"),
    ])
    def test_status_mapping(self, converter, ccda_status, fhir_status):
        policy = _make_policy(status=ccda_status)
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["status"] == fhir_status

    def test_unknown_status_defaults_to_active(self, converter, caplog):
        """Unrecognized status codes default to active with a warning."""
        policy = _make_policy(status="obsolete")
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["status"] == "active"
        assert "Unmapped Coverage statusCode" in caplog.text

    def test_missing_status_defaults_to_active(self, converter):
        policy = Act(
            template_id=[II(root=TemplateIds.POLICY_ACTIVITY)],
            id=[II(root="test-root")],
        )
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["status"] == "active"


class TestRelationshipCodes:
    @pytest.mark.parametrize("ccda_code,fhir_code", [
        ("SELF", "self"),
        ("SPOUSE", "spouse"),
        ("CHILD", "child"),
        ("STPCHLD", "child"),
        ("PARENT", "parent"),
        ("DOMPART", "common"),
        ("FAMMEMB", "other"),
        ("OTHER", "other"),
    ])
    def test_relationship_mapping(self, converter, ccda_code, fhir_code):
        policy = _make_policy(participants=[Participant(
            type_code="COV",
            participant_role=ParticipantRole(
                id=[II(root="member-root", extension="M001")],
                code=CE(code=ccda_code, code_system="2.16.840.1.113883.5.111"),
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["relationship"]["coding"][0]["code"] == fhir_code

    def test_unknown_relationship_defaults_to_other(self, converter, caplog):
        """Unrecognized relationship codes fall back to 'other' with warning."""
        policy = _make_policy(participants=[Participant(
            type_code="COV",
            participant_role=ParticipantRole(
                id=[II(root="member-root", extension="M001")],
                code=CE(code="NEPHEW", code_system="2.16.840.1.113883.5.111"),
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["relationship"]["coding"][0]["code"] == "other"
        assert "Unmapped relationship code" in caplog.text

    def test_case_insensitive_relationship(self, converter):
        """Relationship codes should be case-insensitive."""
        policy = _make_policy(participants=[Participant(
            type_code="COV",
            participant_role=ParticipantRole(
                id=[II(root="member-root", extension="M001")],
                code=CE(code="self", code_system="2.16.840.1.113883.5.111"),
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["relationship"]["coding"][0]["code"] == "self"
        assert "subscriber" in coverage


class TestPayorOrganizationFallback:
    def test_payor_from_assigned_entity_without_represented_org(self, converter):
        """When no representedOrganization, create minimal Organization from assignedEntity."""
        payor = Performer(
            type_code="PRF",
            template_id=[II(root=TemplateIds.PAYER_PERFORMER)],
            assigned_entity=AssignedEntity(
                id=[II(root="payor-oid", extension="12345")],
                # No represented_organization
            ),
        )
        policy = _make_policy(performers=[payor])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        org = next((r for r in result if r["resourceType"] == "Organization"), None)
        assert org is not None
        assert "identifier" in org
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert coverage["payor"][0]["reference"] == f"urn:uuid:{org['id']}"

    def test_payor_case_insensitive_code(self, converter):
        """PAYOR code check should be case-insensitive."""
        payor = Performer(
            type_code="PRF",
            assigned_entity=AssignedEntity(
                id=[II(root="payor-oid")],
                code=CE(code="Payor", code_system="2.16.840.1.113883.5.110"),
                represented_organization=RepresentedOrganization(
                    name=[ON(value="CIGNA")],
                ),
            ),
        )
        policy = _make_policy(performers=[payor])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        org = next((r for r in result if r["resourceType"] == "Organization"), None)
        assert org is not None
        assert org["name"] == "CIGNA"


class TestGuarantorPerformer:
    def test_guarantor_logged_not_mapped(self, converter, caplog):
        """Guarantor performer (.88) is logged but not mapped."""
        import logging
        with caplog.at_level(logging.DEBUG, logger="ccda_to_fhir.converters.coverage"):
            guarantor = Performer(
                type_code="PRF",
                template_id=[II(root=TemplateIds.GUARANTOR_PERFORMER)],
                assigned_entity=AssignedEntity(
                    id=[II(root="guar-oid")],
                    code=CE(code="GUAR", code_system="2.16.840.1.113883.5.110"),
                ),
            )
            policy = _make_policy(performers=[guarantor])
            act = _wrap_in_coverage_activity(policy)
            result = converter.convert(act)
            # No Organization should be created from guarantor
            orgs = [r for r in result if r["resourceType"] == "Organization"]
            assert len(orgs) == 0
            assert "Guarantor performer" in caplog.text


class TestMissingOptionalFields:
    def test_no_code_omits_type(self, converter):
        """When policy has no code, Coverage.type is omitted."""
        policy = _make_policy(code=None)
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "type" not in coverage

    def test_no_sequence_number_omits_order(self, converter):
        """When no sequenceNumber, Coverage.order is omitted."""
        policy = _make_policy()
        act = Act(
            template_id=[II(root=TemplateIds.COVERAGE_ACTIVITY)],
            status_code=CS(code="completed"),
            entry_relationship=[EntryRelationship(
                type_code="COMP",
                # No sequence_number
                act=policy,
            )],
        )
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "order" not in coverage

    def test_no_participants_omits_subscriber_and_relationship(self, converter):
        """When no participants, subscriberId and relationship are omitted."""
        policy = _make_policy()
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "subscriberId" not in coverage
        assert "relationship" not in coverage
        assert "subscriber" not in coverage
        assert "policyHolder" not in coverage

    def test_no_effective_time_omits_period(self, converter):
        """When no effectiveTime, Coverage.period is omitted."""
        policy = _make_policy()
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "period" not in coverage

    def test_policy_without_id_gets_generated_uuid(self, converter):
        """When policy has no id elements, Coverage still gets a generated id."""
        policy = Act(
            template_id=[II(root=TemplateIds.POLICY_ACTIVITY)],
            status_code=CS(code="completed"),
            # No id field
        )
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "id" in coverage
        assert "identifier" not in coverage

    def test_hld_with_empty_ii_omits_policy_holder(self, converter):
        """When HLD participant has II with no root and no extension, policyHolder is omitted."""
        policy = _make_policy(participants=[Participant(
            type_code="HLD",
            participant_role=ParticipantRole(
                id=[II(root=None, extension=None)],
            ),
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "policyHolder" not in coverage

    def test_cov_without_participant_role_skipped(self, converter):
        """COV participant without participantRole is safely skipped."""
        policy = _make_policy(participants=[Participant(
            type_code="COV",
            # No participant_role
        )])
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "subscriberId" not in coverage
        assert "relationship" not in coverage


class TestWithoutReferenceRegistry:
    def test_coverage_omits_beneficiary_without_registry(self, caplog):
        """Without reference_registry, Coverage lacks beneficiary and payor."""
        converter = CoverageConverter()
        policy = _make_policy()
        act = _wrap_in_coverage_activity(policy)
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")
        assert "beneficiary" not in coverage
        assert "payor" not in coverage
        assert "No reference registry" in caplog.text


class TestConvertCoverageActivityFunction:
    def test_function_delegates_to_converter(self, reference_registry, coverage_activity):
        result = convert_coverage_activity(
            coverage_activity,
            reference_registry=reference_registry,
        )
        assert any(r["resourceType"] == "Coverage" for r in result)
