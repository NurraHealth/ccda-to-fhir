"""Unit tests for build_author_references and _build_device_org_fallback_refs."""

from __future__ import annotations

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    AssignedPerson,
    Author,
    RepresentedOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import ENXP, II, PN
from ccda_to_fhir.converters.author_references import (
    _build_device_org_fallback_refs,
    build_author_references,
)


def _make_person_author(npi: str = "1234567890") -> Author:
    return Author(
        assigned_author=AssignedAuthor(
            id=[II(root="2.16.840.1.113883.4.6", extension=npi)],
            assigned_person=AssignedPerson(
                name=[PN(given=[ENXP(value="Dr")], family=ENXP(value="Smith"))],
            ),
        ),
    )


def _make_device_author(
    root: str = "2.16.840.1.113883.3.564",
    org_root: str | None = "org-root",
    org_ext: str | None = None,
) -> Author:
    org = None
    if org_root is not None:
        org = RepresentedOrganization(
            id=[II(root=org_root, extension=org_ext)],
            name=["Test Org"],
        )
    return Author(
        assigned_author=AssignedAuthor(
            id=[II(root=root)],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="Test EHR",
                software_name="Doc Engine",
            ),
            represented_organization=org,
        ),
    )


# ============================================================================
# build_author_references
# ============================================================================


class TestBuildAuthorReferences:
    def test_empty_list(self) -> None:
        assert build_author_references([]) == []

    def test_person_author_creates_practitioner_ref(self) -> None:
        refs = build_author_references([_make_person_author()])
        assert len(refs) == 1
        assert refs[0].reference.startswith("urn:uuid:")

    def test_multiple_person_authors(self) -> None:
        refs = build_author_references([_make_person_author("111"), _make_person_author("222")])
        assert len(refs) == 2
        assert refs[0].reference != refs[1].reference

    def test_device_author_creates_device_ref(self) -> None:
        refs = build_author_references([_make_device_author(org_root=None)])
        assert len(refs) == 1
        assert refs[0].reference.startswith("urn:uuid:")

    def test_device_author_with_org_creates_both_refs(self) -> None:
        refs = build_author_references([_make_device_author()])
        assert len(refs) == 2
        assert refs[0].reference != refs[1].reference

    def test_no_fallback_when_person_exists(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                assigned_person=AssignedPerson(
                    name=[PN(given=[ENXP(value="Dr")], family=ENXP(value="Smith"))],
                ),
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
        assert len(refs) == 1

    def test_skip_without_assigned_author(self) -> None:
        author = Author()
        assert build_author_references([author]) == []

    def test_device_without_id_skipped(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                assigned_authoring_device=AssignedAuthoringDevice(
                    manufacturer_model_name="Test EHR",
                ),
            ),
        )
        assert build_author_references([author]) == []

    def test_organization_without_org_id_skipped(self) -> None:
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.3.564")],
                represented_organization=RepresentedOrganization(
                    name=["Test Org"],
                ),
            ),
        )
        assert build_author_references([author]) == []

    def test_mixed_person_and_device_authors(self) -> None:
        refs = build_author_references([_make_person_author(), _make_device_author()])
        # 1 Practitioner + 1 Device + 1 Organization = 3
        assert len(refs) == 3

    def test_deterministic_ids(self) -> None:
        refs1 = build_author_references([_make_person_author()])
        refs2 = build_author_references([_make_person_author()])
        assert refs1[0].reference == refs2[0].reference

    def test_org_only_fallback(self) -> None:
        """Author with only representedOrganization (no device, no person)."""
        author = Author(
            assigned_author=AssignedAuthor(
                id=[II(root="2.16.840.1.113883.3.564")],
                represented_organization=RepresentedOrganization(
                    id=[II(root="org-uuid", extension="12345")],
                    name=["Test Medical Group"],
                ),
            ),
        )
        refs = build_author_references([author])
        assert len(refs) == 1
        assert refs[0].reference.startswith("urn:uuid:")


# ============================================================================
# _build_device_org_fallback_refs
# ============================================================================


class TestBuildDeviceOrgFallbackRefs:
    def test_device_only(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="device-root")],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="EHR",
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1

    def test_org_only(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="some-root")],
            represented_organization=RepresentedOrganization(
                id=[II(root="org-root")],
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 1

    def test_both_device_and_org(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="device-root")],
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="EHR",
            ),
            represented_organization=RepresentedOrganization(
                id=[II(root="org-root")],
            ),
        )
        refs = _build_device_org_fallback_refs(assigned)
        assert len(refs) == 2

    def test_empty_when_nothing(self) -> None:
        assigned = AssignedAuthor()
        assert _build_device_org_fallback_refs(assigned) == []

    def test_device_without_assigned_id(self) -> None:
        assigned = AssignedAuthor(
            assigned_authoring_device=AssignedAuthoringDevice(
                manufacturer_model_name="EHR",
            ),
        )
        assert _build_device_org_fallback_refs(assigned) == []

    def test_org_without_own_id(self) -> None:
        assigned = AssignedAuthor(
            id=[II(root="some-root")],
            represented_organization=RepresentedOrganization(
                name=["Org Name"],
            ),
        )
        assert _build_device_org_fallback_refs(assigned) == []
