"""Unit tests for display text in author/performer references.

Tests the shared display formatting functions and verifies that all reference
builders include display text when source data is available.
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
    RepresentedOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import ENXP, II, ON, PN
from ccda_to_fhir.converters.author_references import (
    _build_device_org_fallback_refs,
    build_author_references,
    format_device_display,
    format_organization_display,
    format_person_display,
)


# ============================================================================
# format_person_display
# ============================================================================


class TestFormatPersonDisplay:
    def test_given_and_family(self) -> None:
        person = AssignedPerson(
            name=[PN(given=[ENXP(value="Jane")], family=ENXP(value="Doe"))]
        )
        assert format_person_display(person) == "Jane Doe"

    def test_multiple_given_names(self) -> None:
        person = AssignedPerson(
            name=[PN(given=[ENXP(value="Jane"), ENXP(value="Marie")], family=ENXP(value="Doe"))]
        )
        assert format_person_display(person) == "Jane Marie Doe"

    def test_family_only(self) -> None:
        person = AssignedPerson(
            name=[PN(family=ENXP(value="Smith"))]
        )
        assert format_person_display(person) == "Smith"

    def test_given_only(self) -> None:
        person = AssignedPerson(
            name=[PN(given=[ENXP(value="Alice")])]
        )
        assert format_person_display(person) == "Alice"

    def test_none_person(self) -> None:
        assert format_person_display(None) is None

    def test_empty_name_list(self) -> None:
        person = AssignedPerson(name=[])
        assert format_person_display(person) is None

    def test_no_name(self) -> None:
        person = AssignedPerson()
        assert format_person_display(person) is None

    def test_name_with_empty_values(self) -> None:
        person = AssignedPerson(
            name=[PN(given=[ENXP(value=None)], family=ENXP(value=None))]
        )
        assert format_person_display(person) is None

    def test_uses_first_name_entry(self) -> None:
        person = AssignedPerson(
            name=[
                PN(given=[ENXP(value="First")], family=ENXP(value="Name")),
                PN(given=[ENXP(value="Second")], family=ENXP(value="Name")),
            ]
        )
        assert format_person_display(person) == "First Name"


# ============================================================================
# format_device_display
# ============================================================================


class TestFormatDeviceDisplay:
    def test_manufacturer_and_software(self) -> None:
        device = AssignedAuthoringDevice(
            manufacturer_model_name="Epic EHR",
            software_name="ClinDoc",
        )
        assert format_device_display(device) == "Epic EHR (ClinDoc)"

    def test_manufacturer_only(self) -> None:
        device = AssignedAuthoringDevice(manufacturer_model_name="Epic EHR")
        assert format_device_display(device) == "Epic EHR"

    def test_software_only(self) -> None:
        device = AssignedAuthoringDevice(software_name="ClinDoc")
        assert format_device_display(device) == "ClinDoc"

    def test_none_device(self) -> None:
        assert format_device_display(None) is None

    def test_empty_device(self) -> None:
        device = AssignedAuthoringDevice()
        assert format_device_display(device) is None


# ============================================================================
# format_organization_display
# ============================================================================


class TestFormatOrganizationDisplay:
    def test_string_name(self) -> None:
        org = RepresentedOrganization(
            id=[II(root="org-root")],
            name=["Good Health Hospital"],
        )
        assert format_organization_display(org) == "Good Health Hospital"

    def test_on_name(self) -> None:
        org = RepresentedOrganization(
            id=[II(root="org-root")],
            name=[ON(value="Memorial Clinic")],
        )
        assert format_organization_display(org) == "Memorial Clinic"

    def test_none_org(self) -> None:
        assert format_organization_display(None) is None

    def test_empty_name_list(self) -> None:
        org = RepresentedOrganization(id=[II(root="org-root")], name=[])
        assert format_organization_display(org) is None

    def test_no_name(self) -> None:
        org = RepresentedOrganization(id=[II(root="org-root")])
        assert format_organization_display(org) is None

    def test_empty_string_name(self) -> None:
        org = RepresentedOrganization(id=[II(root="org-root")], name=[""])
        assert format_organization_display(org) is None

    def test_on_with_no_value(self) -> None:
        org = RepresentedOrganization(
            id=[II(root="org-root")],
            name=[ON(value=None)],
        )
        assert format_organization_display(org) is None


# ============================================================================
# build_author_references - display text
# ============================================================================


class TestBuildAuthorReferencesDisplay:
    def test_person_author_includes_display(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(
                    name=[PN(given=[ENXP(value="Sarah")], family=ENXP(value="Connor"))],
                ),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 1
        assert refs[0]["display"] == "Sarah Connor"

    def test_person_author_without_name_omits_display(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 1
        assert "display" not in refs[0]

    def test_device_author_includes_display(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.3.564")],
                assigned_authoring_device=AssignedAuthoringDevice(
                    manufacturer_model_name="Epic",
                    software_name="Hyperspace",
                ),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 1
        assert refs[0]["display"] == "Epic (Hyperspace)"

    def test_org_author_includes_display(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="some-root")],
                represented_organization=RepresentedOrganization(
                    id=[II(root="org-root")],
                    name=["Good Health Hospital"],
                ),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 1
        assert refs[0]["display"] == "Good Health Hospital"

    def test_device_and_org_both_have_display(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.3.564")],
                assigned_authoring_device=AssignedAuthoringDevice(
                    manufacturer_model_name="Test EHR",
                ),
                represented_organization=RepresentedOrganization(
                    id=[II(root="org-root")],
                    name=["Test Org"],
                ),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 2
        assert refs[0]["display"] == "Test EHR"
        assert refs[1]["display"] == "Test Org"

    def test_mixed_person_and_device_all_have_display(self) -> None:
        person_author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="111")],
                assigned_person=AssignedPerson(
                    name=[PN(given=[ENXP(value="Dr")], family=ENXP(value="Smith"))],
                ),
            ),
        )
        device_author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.3.564")],
                assigned_authoring_device=AssignedAuthoringDevice(
                    manufacturer_model_name="Test EHR",
                    software_name="Doc Engine",
                ),
                represented_organization=RepresentedOrganization(
                    id=[II(root="org-root")],
                    name=["Test Org"],
                ),
            ),
        )
        refs = build_author_references([person_author, device_author])
        assert len(refs) == 3
        assert refs[0]["display"] == "Dr Smith"
        assert refs[1]["display"] == "Test EHR (Doc Engine)"
        assert refs[2]["display"] == "Test Org"


# ============================================================================
# _build_device_org_fallback_refs - display text
# ============================================================================


class TestDeviceOrgFallbackRefsDisplay:
    def test_device_ref_includes_display(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="device-root")],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="EHR System",
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1
        assert refs[0]["display"] == "EHR System"

    def test_org_ref_includes_display(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="some-root")],
            represented_organization=RepresentedOrganization(
                id=[II(root="org-root")],
                name=["Springfield Hospital"],
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1
        assert refs[0]["display"] == "Springfield Hospital"

    def test_device_without_name_omits_display(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="device-root")],
            assigned_authoring_device=AssignedAuthoringDevice(),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1
        assert "display" not in refs[0]

    def test_org_without_name_omits_display(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="some-root")],
            represented_organization=RepresentedOrganization(
                id=[II(root="org-root")],
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1
        assert "display" not in refs[0]
