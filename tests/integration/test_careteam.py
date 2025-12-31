"""Integration tests for CareTeam extraction from C-CDA documents."""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document


class TestCareTeamExtraction:
    """Test CareTeam resource extraction from Care Teams Section."""

    @pytest.fixture
    def careteam_document(self):
        """Load example C-CDA document with Care Teams Section."""
        fixture_path = Path(__file__).parent / "fixtures" / "documents" / "careteam_example.xml"
        return fixture_path.read_text()

    def test_extracts_careteam_from_care_teams_section(self, careteam_document):
        """Test that CareTeam resource is extracted from Care Teams Section."""
        bundle = convert_document(careteam_document)["bundle"]

        # Find CareTeam resources
        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        # Should extract exactly 1 CareTeam
        assert len(careteams) == 1, f"Expected 1 CareTeam, found {len(careteams)}"

    def test_careteam_has_required_fields(self, careteam_document):
        """Test that CareTeam has US Core required fields."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # US Core required fields
        assert "status" in careteam, "CareTeam must have status"
        assert careteam["status"] == "active"

        assert "subject" in careteam, "CareTeam must have subject"
        assert "reference" in careteam["subject"]
        assert careteam["subject"]["reference"].startswith("Patient/")

        assert "participant" in careteam, "CareTeam must have participants"
        assert len(careteam["participant"]) >= 1, "CareTeam must have at least one participant"

        # Check participant structure
        for participant in careteam["participant"]:
            assert "role" in participant, "Participant must have role"
            assert "member" in participant, "Participant must have member"
            assert "reference" in participant["member"]

    def test_careteam_extracts_multiple_participants(self, careteam_document):
        """Test that multiple team members are extracted as participants."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # Document has 2 team members
        assert len(careteam["participant"]) == 2, "Expected 2 participants"

        # Check that participants have different members
        member_refs = [p["member"]["reference"] for p in careteam["participant"]]
        assert len(set(member_refs)) == 2, "Participants should reference different members"

    def test_careteam_creates_practitioner_resources(self, careteam_document):
        """Test that Practitioner resources are created for team members."""
        bundle = convert_document(careteam_document)["bundle"]

        practitioners = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Practitioner"
        ]

        # Should create Practitioner resources for team members
        assert len(practitioners) >= 2, "Should create Practitioners for team members"

        # Check practitioner names
        practitioner_names = []
        for pract in practitioners:
            if pract.get("name"):
                name = pract["name"][0]
                if "family" in name:
                    full_name = f"{name.get('given', [''])[0]} {name['family']}"
                    practitioner_names.append(full_name)

        # Should include team members from document
        assert any("Johnson" in name for name in practitioner_names), "Should have Dr. Johnson"
        assert any("Smith" in name for name in practitioner_names), "Should have Jane Smith"

    def test_careteam_creates_practitioner_role_resources(self, careteam_document):
        """Test that PractitionerRole resources are created for team members."""
        bundle = convert_document(careteam_document)["bundle"]

        practitioner_roles = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "PractitionerRole"
        ]

        # Should create PractitionerRole resources
        assert len(practitioner_roles) >= 2, "Should create PractitionerRoles for team members"

        # Check that roles reference practitioners
        for role in practitioner_roles:
            assert "practitioner" in role, "PractitionerRole must reference Practitioner"
            assert "reference" in role["practitioner"]
            assert role["practitioner"]["reference"].startswith("Practitioner/")

    def test_careteam_participant_references_practitioner_role(self, careteam_document):
        """Test that CareTeam participants reference PractitionerRole (US Core recommendation)."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # Participants should reference PractitionerRole
        for participant in careteam["participant"]:
            member_ref = participant["member"]["reference"]
            assert member_ref.startswith("PractitionerRole/"), \
                f"Participant should reference PractitionerRole, got {member_ref}"

    def test_careteam_has_managing_organization(self, careteam_document):
        """Test that CareTeam has managing organization extracted."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # Should have managing organization
        assert "managingOrganization" in careteam, "CareTeam should have managing organization"
        assert len(careteam["managingOrganization"]) > 0

        org_ref = careteam["managingOrganization"][0]["reference"]
        assert org_ref.startswith("Organization/"), f"Should reference Organization, got {org_ref}"

        # Verify Organization resource exists
        organizations = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Organization"
        ]

        org_id = org_ref.split("/")[1]
        assert any(org.get("id") == org_id for org in organizations), \
            "Referenced Organization should exist in bundle"

    def test_careteam_team_lead_is_first_participant(self, careteam_document):
        """Test that team lead (typeCode='PPRF') is placed first in participants list."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # First participant should be the team lead (PCP - Primary Care Physician)
        first_participant = careteam["participant"][0]

        # Check role is PCP
        role_coding = first_participant["role"][0]["coding"][0]
        assert role_coding["code"] == "PCP", "First participant should be team lead (PCP)"

    def test_careteam_has_period_from_effective_time(self, careteam_document):
        """Test that CareTeam period is extracted from effectiveTime."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # Should have period from effectiveTime
        assert "period" in careteam, "CareTeam should have period"
        assert "start" in careteam["period"], "Period should have start date"
        assert careteam["period"]["start"] == "2024-01-01"

    def test_careteam_has_us_core_profile(self, careteam_document):
        """Test that CareTeam includes US Core profile in meta."""
        bundle = convert_document(careteam_document)["bundle"]

        careteams = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "CareTeam"
        ]

        careteam = careteams[0]

        # Should have US Core profile
        assert "meta" in careteam, "CareTeam should have meta"
        assert "profile" in careteam["meta"], "Meta should have profile"

        profiles = careteam["meta"]["profile"]
        us_core_profile = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam"
        assert us_core_profile in profiles, "Should include US Core CareTeam profile"

    def test_bundle_has_valid_references(self, careteam_document):
        """Test that all references in bundle are valid."""
        bundle = convert_document(careteam_document)["bundle"]

        # Collect all resource IDs
        resource_ids = set()
        for entry in bundle.get("entry", []):
            resource = entry.get("resource", {})
            resource_type = resource.get("resourceType")
            resource_id = resource.get("id")
            if resource_type and resource_id:
                resource_ids.add(f"{resource_type}/{resource_id}")

        # Check all references
        def check_references(obj, path=""):
            if isinstance(obj, dict):
                if "reference" in obj and isinstance(obj["reference"], str):
                    ref = obj["reference"]
                    # Skip external references (http, urn)
                    if not ref.startswith("http") and not ref.startswith("urn"):
                        assert ref in resource_ids, \
                            f"Broken reference at {path}: {ref} not in bundle"

                for key, value in obj.items():
                    check_references(value, f"{path}.{key}" if path else key)

            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_references(item, f"{path}[{i}]")

        check_references(bundle)
