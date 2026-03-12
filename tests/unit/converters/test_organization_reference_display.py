"""Unit tests for display text in organization references.

Tests that custodian, payor, managingOrganization, and owner references
include display text when source data provides organization names.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor
from ccda_to_fhir.ccda.models.author import RepresentedOrganization as AuthorRepresentedOrganization
from ccda_to_fhir.ccda.models.clinical_document import (
    AssignedCustodian,
    Custodian,
    CustodianOrganization,
)
from ccda_to_fhir.ccda.models.datatypes import CE, CS, II, ON
from ccda_to_fhir.ccda.models.participant import ParticipantRole, ScopingEntity
from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer
from ccda_to_fhir.ccda.models.performer import RepresentedOrganization
from ccda_to_fhir.converters.references import ReferenceRegistry


# ============================================================================
# Fixtures
# ============================================================================


def _make_registry() -> ReferenceRegistry:
    reg = ReferenceRegistry()
    reg.register_resource({"resourceType": "Patient", "id": "test-patient"})
    return reg


@pytest.fixture
def registry() -> ReferenceRegistry:
    return _make_registry()


# ============================================================================
# composition.py: _create_custodian_reference
# ============================================================================


class TestCustodianReferenceDisplay:
    """Tests for display text on Composition.custodian reference."""

    def _make_converter(self, registry: ReferenceRegistry | None = None):
        from ccda_to_fhir.converters.composition import CompositionConverter

        return CompositionConverter(reference_registry=registry)

    def _registry_with_org(self, root: str, extension: str | None = None) -> ReferenceRegistry:
        """Create a registry with a pre-registered Organization matching the given IDs."""
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        reg = _make_registry()
        org_id = generate_id_from_identifiers("Organization", root, extension)
        reg.register_resource({"resourceType": "Organization", "id": org_id})
        return reg

    def test_custodian_includes_display_from_on(self) -> None:
        registry = self._registry_with_org("2.16.840.1.113883.4.6", "1234567890")
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    name=ON(value="Good Health Clinic"),
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert ref["display"] == "Good Health Clinic"
        assert "reference" in ref

    def test_custodian_includes_display_from_string_name(self) -> None:
        registry = self._registry_with_org("1.2.3")
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="1.2.3")],
                    name="Community Hospital",
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert ref["display"] == "Community Hospital"

    def test_custodian_no_display_when_name_missing(self) -> None:
        registry = self._registry_with_org("1.2.3")
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="1.2.3")],
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert "display" not in ref
        assert "reference" in ref

    def test_custodian_reference_uri_from_ids(self) -> None:
        registry = self._registry_with_org("2.16.840.1.113883.4.6", "9876543210")
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="2.16.840.1.113883.4.6", extension="9876543210")],
                    name=ON(value="Test Org"),
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert ref["reference"].startswith("urn:uuid:")

    def test_custodian_no_reference_when_org_not_in_registry(self) -> None:
        """Reference URI should be omitted when Organization is not in the registry."""
        registry = _make_registry()  # no Organization registered
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="9.9.9.9")],
                    name=ON(value="Unknown Org"),
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert "reference" not in ref
        assert ref["display"] == "Unknown Org"

    def test_custodian_no_reference_without_registry(self) -> None:
        """Reference URI should be omitted when no registry is available."""
        converter = self._make_converter()  # no registry
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="1.2.3")],
                    name=ON(value="Display Only Org"),
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert "reference" not in ref
        assert ref["display"] == "Display Only Org"

    def test_custodian_empty_on_value_yields_no_display(self) -> None:
        """Empty ON.value should not produce a display field."""
        registry = self._registry_with_org("1.2.3")
        converter = self._make_converter(registry)
        custodian = Custodian(
            assigned_custodian=AssignedCustodian(
                represented_custodian_organization=CustodianOrganization(
                    id=[II(root="1.2.3")],
                    name=ON(value=""),
                )
            )
        )
        ref = converter._create_custodian_reference(custodian)
        assert ref is not None
        assert "display" not in ref
        assert "reference" in ref


# ============================================================================
# coverage.py: _process_performer (payor reference)
# ============================================================================


class TestPayorReferenceDisplay:
    """Tests for display text on Coverage.payor reference."""

    def _make_converter(self, registry: ReferenceRegistry):
        from ccda_to_fhir.converters.coverage import CoverageConverter

        return CoverageConverter(reference_registry=registry)

    def test_payor_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.constants import TemplateIds
        from ccda_to_fhir.converters.coverage import CoverageConverter

        converter = CoverageConverter(reference_registry=registry)

        org = RepresentedOrganization(
            id=[II(root="2.16.840.1.113883.4.6", extension="PAYOR-001")],
            name=[ON(value="Acme Insurance Co")],
        )
        assigned = AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="PAYOR-001")],
            represented_organization=org,
        )
        performer = Performer(
            template_id=[II(root=TemplateIds.PAYER_PERFORMER)],
            assigned_entity=assigned,
        )

        coverage: dict = {"resourceType": "Coverage"}
        related: list = []
        converter._process_performer(performer, coverage, related)

        assert "payor" in coverage
        payor_ref = coverage["payor"][0]
        assert payor_ref["display"] == "Acme Insurance Co"
        assert "reference" in payor_ref

    def test_payor_no_display_when_org_name_missing(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.constants import TemplateIds
        from ccda_to_fhir.converters.coverage import CoverageConverter

        converter = CoverageConverter(reference_registry=registry)

        org = RepresentedOrganization(
            id=[II(root="1.2.3.4", extension="NO-NAME")],
        )
        assigned = AssignedEntity(
            id=[II(root="1.2.3.4", extension="NO-NAME")],
            represented_organization=org,
        )
        performer = Performer(
            template_id=[II(root=TemplateIds.PAYER_PERFORMER)],
            assigned_entity=assigned,
        )

        coverage: dict = {"resourceType": "Coverage"}
        related: list = []
        converter._process_performer(performer, coverage, related)

        assert "payor" in coverage
        payor_ref = coverage["payor"][0]
        assert "display" not in payor_ref


# ============================================================================
# device.py: _extract_ehr_device_owner, _extract_device_owner
# ============================================================================


class TestDeviceOwnerReferenceDisplay:
    """Tests for display text on Device.owner reference."""

    def test_ehr_device_owner_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.device import DeviceConverter

        org = AuthorRepresentedOrganization(
            id=[II(root="1.2.3.4", extension="HOSP-1")],
            name=[ON(value="General Hospital")],
        )
        # Register the Organization so the converter finds it
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "HOSP-1")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        assigned = AssignedAuthor(
            id=[II(root="1.2.3.4.5", extension="DEV-1")],
            represented_organization=org,
        )

        converter = DeviceConverter(reference_registry=registry)
        ref = converter._extract_ehr_device_owner(assigned)

        assert ref is not None
        assert ref.display == "General Hospital"
        assert ref.reference == f"urn:uuid:{org_id}"

    def test_ehr_device_owner_no_display_when_name_missing(
        self, registry: ReferenceRegistry
    ) -> None:
        from ccda_to_fhir.converters.device import DeviceConverter
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        org = AuthorRepresentedOrganization(
            id=[II(root="1.2.3.4", extension="HOSP-2")],
        )
        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "HOSP-2")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        assigned = AssignedAuthor(
            id=[II(root="1.2.3.4.5", extension="DEV-2")],
            represented_organization=org,
        )

        converter = DeviceConverter(reference_registry=registry)
        ref = converter._extract_ehr_device_owner(assigned)

        assert ref is not None
        assert ref.display is None

    def test_product_device_owner_includes_display(
        self, registry: ReferenceRegistry
    ) -> None:
        from ccda_to_fhir.converters.device import DeviceConverter
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        scoping = ScopingEntity(
            id=[II(root="1.2.3.4", extension="MFG-1")],
            desc="Medtronic Inc",
        )
        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "MFG-1")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.3.3719", extension="(01)123456")],
            scoping_entity=scoping,
        )

        converter = DeviceConverter(reference_registry=registry)
        ref = converter._extract_device_owner(participant_role)

        assert ref is not None
        assert ref.display == "Medtronic Inc"

    def test_product_device_owner_no_display_when_desc_missing(
        self, registry: ReferenceRegistry
    ) -> None:
        from ccda_to_fhir.converters.device import DeviceConverter
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        scoping = ScopingEntity(
            id=[II(root="1.2.3.4", extension="MFG-2")],
        )
        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "MFG-2")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        participant_role = ParticipantRole(
            id=[II(root="2.16.840.1.113883.3.3719", extension="(01)999999")],
            scoping_entity=scoping,
        )

        converter = DeviceConverter(reference_registry=registry)
        ref = converter._extract_device_owner(participant_role)

        assert ref is not None
        assert ref.display is None


# ============================================================================
# location.py: _get_managing_organization_reference
# ============================================================================


class TestLocationManagingOrgDisplay:
    """Tests for display text on Location.managingOrganization reference."""

    def test_managing_org_includes_display(self, registry: ReferenceRegistry) -> None:
        from ccda_to_fhir.converters.location import LocationConverter
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        scoping = ScopingEntity(
            id=[II(root="1.2.3.4", extension="ORG-1")],
            desc="Good Health Hospital",
        )
        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "ORG-1")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        participant_role = ParticipantRole(
            class_code="SDLOC",
            scoping_entity=scoping,
        )

        converter = LocationConverter(reference_registry=registry)
        ref = converter._get_managing_organization_reference(participant_role)

        assert ref is not None
        assert ref.display == "Good Health Hospital"
        assert ref.reference == f"urn:uuid:{org_id}"

    def test_managing_org_no_display_when_desc_missing(
        self, registry: ReferenceRegistry
    ) -> None:
        from ccda_to_fhir.converters.location import LocationConverter
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        scoping = ScopingEntity(
            id=[II(root="1.2.3.4", extension="ORG-2")],
        )
        org_id = generate_id_from_identifiers("Organization", "1.2.3.4", "ORG-2")
        registry.register_resource({"resourceType": "Organization", "id": org_id})

        participant_role = ParticipantRole(
            class_code="SDLOC",
            scoping_entity=scoping,
        )

        converter = LocationConverter(reference_registry=registry)
        ref = converter._get_managing_organization_reference(participant_role)

        assert ref is not None
        assert ref.display is None


# ============================================================================
# medication_dispense.py: _create_pharmacy_location (managingOrganization)
# ============================================================================


class TestMedicationDispenseLocationOrgDisplay:
    """Tests for display text on MedicationDispense Location.managingOrganization."""

    def test_pharmacy_location_managing_org_includes_display(
        self, registry: ReferenceRegistry
    ) -> None:
        from ccda_to_fhir.converters.medication_dispense import MedicationDispenseConverter

        org = RepresentedOrganization(
            id=[II(root="2.16.840.1.113883.4.6", extension="PHARM-001")],
            name=[ON(value="Community Pharmacy")],
        )

        converter = MedicationDispenseConverter(reference_registry=registry)
        location_ref = converter._create_pharmacy_location(org)

        assert location_ref is not None

        # Find the registered Location resource by looking through all resources
        location = registry.get_resource("Location", location_ref.replace("urn:uuid:", ""))

        assert location is not None
        managing_org = location["managingOrganization"]
        assert managing_org["display"] == "Community Pharmacy"


# ============================================================================
# careteam.py: managingOrganization
# ============================================================================


class TestCareTeamManagingOrgDisplay:
    """Tests for display text on CareTeam.managingOrganization reference."""

    def _make_organizer(self, org_name: str | None = "Good Health Clinic"):
        from ccda_to_fhir.ccda.models.act import Act
        from ccda_to_fhir.ccda.models.datatypes import CD, IVL_TS, TS
        from ccda_to_fhir.ccda.models.organizer import Organizer, OrganizerComponent as Component
        from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer

        org_names = [ON(value=org_name)] if org_name else None
        org = RepresentedOrganization(
            id=[II(root="1.2.3.4", extension="ORG-CT")],
            name=org_names,
        )

        from ccda_to_fhir.ccda.models.datatypes import ENXP, PN
        from ccda_to_fhir.ccda.models.performer import AssignedPerson

        person = AssignedPerson(
            name=[PN(given=[ENXP(value="Jane")], family=ENXP(value="Smith"))]
        )

        assigned_entity = AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
            code=CE(
                code="163WP0218X",
                code_system="2.16.840.1.113883.6.101",
                display_name="Physician",
            ),
            assigned_person=person,
            represented_organization=org,
        )

        member_act = Act(
            class_code="PCPR",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500.1", extension="2022-06-01")],
            code=CD(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            performer=[Performer(
                assigned_entity=assigned_entity,
                function_code=CE(
                    code="PCP",
                    code_system="2.16.840.1.113883.5.88",
                    display_name="Primary Care Provider",
                ),
            )],
            effective_time=IVL_TS(low=TS(value="20230101")),
        )

        organizer = Organizer(
            class_code="CLUSTER",
            mood_code="EVN",
            template_id=[II(root="2.16.840.1.113883.10.20.22.4.500", extension="2022-06-01")],
            id=[II(root="1.2.3.4.5", extension="CT-1")],
            code=CD(code="86744-0", code_system="2.16.840.1.113883.6.1"),
            status_code=CS(code="active"),
            effective_time=IVL_TS(low=TS(value="20230101")),
            component=[Component(act=member_act)],
        )
        return organizer

    def test_managing_org_includes_display(self) -> None:
        from ccda_to_fhir.converters.careteam import CareTeamConverter

        patient_ref = {"reference": "urn:uuid:test-patient"}
        converter = CareTeamConverter(patient_reference=patient_ref)

        organizer = self._make_organizer(org_name="Good Health Clinic")
        result = converter.convert(organizer)

        assert "managingOrganization" in result
        managing_org = result["managingOrganization"][0]
        assert managing_org["display"] == "Good Health Clinic"
        assert "reference" in managing_org

    def test_managing_org_no_display_when_name_missing(self) -> None:
        from ccda_to_fhir.converters.careteam import CareTeamConverter

        patient_ref = {"reference": "urn:uuid:test-patient"}
        converter = CareTeamConverter(patient_reference=patient_ref)

        organizer = self._make_organizer(org_name=None)
        result = converter.convert(organizer)

        assert "managingOrganization" in result
        managing_org = result["managingOrganization"][0]
        assert "display" not in managing_org


# ============================================================================
# practitioner_role.py: organization reference
# ============================================================================


class TestPractitionerRoleOrgDisplay:
    """Tests for display text on PractitionerRole.organization reference."""

    def test_org_reference_includes_display(self) -> None:
        from ccda_to_fhir.converters.practitioner_role import PractitionerRoleConverter

        org = RepresentedOrganization(
            id=[II(root="1.2.3.4", extension="ORG-PR")],
            name=[ON(value="Family Practice Associates")],
        )
        assigned = AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="9999999")],
            represented_organization=org,
        )

        converter = PractitionerRoleConverter()
        result = converter.convert(
            assigned, practitioner_id="prac-123", organization_id="org-456"
        )

        assert "organization" in result
        assert result["organization"]["display"] == "Family Practice Associates"
        assert result["organization"]["reference"] == "urn:uuid:org-456"

    def test_org_reference_no_display_when_no_represented_org(self) -> None:
        from ccda_to_fhir.converters.practitioner_role import PractitionerRoleConverter

        assigned = AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="8888888")],
        )

        converter = PractitionerRoleConverter()
        result = converter.convert(
            assigned, practitioner_id="prac-456", organization_id="org-789"
        )

        assert "organization" in result
        assert "display" not in result["organization"]
        assert result["organization"]["reference"] == "urn:uuid:org-789"

    def test_org_reference_no_display_when_org_has_no_name(self) -> None:
        from ccda_to_fhir.converters.practitioner_role import PractitionerRoleConverter

        org = RepresentedOrganization(
            id=[II(root="1.2.3.4", extension="ORG-NONAME")],
        )
        assigned = AssignedEntity(
            id=[II(root="2.16.840.1.113883.4.6", extension="7777777")],
            represented_organization=org,
        )

        converter = PractitionerRoleConverter()
        result = converter.convert(
            assigned, practitioner_id="prac-789", organization_id="org-000"
        )

        assert "organization" in result
        assert "display" not in result["organization"]
