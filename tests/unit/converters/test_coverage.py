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

    def test_policy_holder_identifier(self, converter, coverage_activity):
        result = converter.convert(coverage_activity)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        assert "policyHolder" in coverage
        assert "identifier" in coverage["policyHolder"]

    def test_empty_entry_relationships(self, converter):
        act = Act(
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.60")],
            status_code=CS(code="completed"),
        )
        result = converter.convert(act)
        assert result == []

    def test_no_payor_defaults_to_patient(self, converter):
        """When no PAYOR performer exists, payor defaults to patient."""
        policy = Act(
            class_code="ACT",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.61")],
            id=[II(root="test-root")],
            status_code=CS(code="completed"),
        )
        act = Act(
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.60")],
            status_code=CS(code="completed"),
            entry_relationship=[
                EntryRelationship(type_code="COMP", act=policy)
            ],
        )
        result = converter.convert(act)
        coverage = next(r for r in result if r["resourceType"] == "Coverage")

        # payor should default to patient reference
        assert coverage["payor"][0]["reference"] == "urn:uuid:patient-123"


class TestConvertCoverageActivityFunction:
    def test_function_delegates_to_converter(self, reference_registry, coverage_activity):
        result = convert_coverage_activity(
            coverage_activity,
            reference_registry=reference_registry,
        )
        assert any(r["resourceType"] == "Coverage" for r in result)
