"""Unit tests for MedicationRequest.requester field extraction."""

import pytest

from ccda_to_fhir.ccda.models.author import (
    Author,
    AssignedAuthor,
    AssignedPerson,
    AssignedAuthoringDevice,
)
from ccda_to_fhir.ccda.models.datatypes import CE, II, TS
from ccda_to_fhir.ccda.models.substance_administration import (
    SubstanceAdministration,
    Consumable,
    ManufacturedProduct,
    ManufacturedMaterial,
)
from ccda_to_fhir.converters.medication_request import MedicationRequestConverter


class TestMedicationRequester:
    """Test MedicationRequest.requester field extraction from latest author."""

    def create_substance_admin_with_authors(self, authors: list[Author] | None) -> SubstanceAdministration:
        """Helper to create substance administration with given authors."""
        sa = SubstanceAdministration()

        # Create proper consumable structure
        material = ManufacturedMaterial()
        material.code = CE(code="197361", code_system="2.16.840.1.113883.6.88", display_name="Aspirin")

        product = ManufacturedProduct()
        product.manufactured_material = material

        consumable = Consumable()
        consumable.manufactured_product = product

        sa.consumable = consumable
        sa.id = [II(root="1.2.3.4", extension="med-1")]
        sa.author = authors
        return sa

    def create_author(
        self,
        time: str | None,
        practitioner_ext: str | None = None,
        has_person: bool = True,
        has_device: bool = False
    ) -> Author:
        """Helper to create author with specified time and identifiers."""
        assigned_author = AssignedAuthor()
        assigned_author.id = [II(root="2.16.840.1.113883.4.6", extension=practitioner_ext)] if practitioner_ext else []

        if has_person and not has_device:
            assigned_author.assigned_person = AssignedPerson(name=[])
        elif has_device:
            assigned_author.assigned_authoring_device = AssignedAuthoringDevice(
                manufacturer_model_name="Test Device",
                software_name="Test Software"
            )

        author = Author()
        author.time = TS(value=time) if time else None
        author.assigned_author = assigned_author
        return author

    def test_single_author_with_time_creates_requester(self):
        """Test that single author with time creates requester reference."""
        author = self.create_author(time="20240115090000", practitioner_ext="DOC-001")
        sa = self.create_substance_admin_with_authors([author])

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        assert "requester" in med_request
        assert med_request["requester"]["reference"] == "Practitioner/practitioner-DOC-001"

    def test_multiple_authors_chronological_returns_latest(self):
        """Test that latest author by timestamp is used for requester."""
        authors = [
            self.create_author(time="20240101", practitioner_ext="EARLY-DOC"),
            self.create_author(time="20240201", practitioner_ext="MIDDLE-DOC"),
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
        ]
        sa = self.create_substance_admin_with_authors(authors)

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        assert "requester" in med_request
        assert med_request["requester"]["reference"] == "Practitioner/practitioner-LATEST-DOC"

    def test_author_without_time_excluded(self):
        """Test that authors without time are excluded from requester selection."""
        authors = [
            self.create_author(time=None, practitioner_ext="NO-TIME-DOC"),
            self.create_author(time="20240215", practitioner_ext="WITH-TIME-DOC"),
        ]
        sa = self.create_substance_admin_with_authors(authors)

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        assert "requester" in med_request
        assert med_request["requester"]["reference"] == "Practitioner/practitioner-WITH-TIME-DOC"

    def test_all_authors_without_time_no_requester(self):
        """Test that no requester is created if all authors lack time."""
        authors = [
            self.create_author(time=None, practitioner_ext="NO-TIME-1"),
            self.create_author(time=None, practitioner_ext="NO-TIME-2"),
        ]
        sa = self.create_substance_admin_with_authors(authors)

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        assert "requester" not in med_request

    def test_device_author_creates_device_reference(self):
        """Test that device author creates Device reference."""
        author = self.create_author(
            time="20240115",
            practitioner_ext="DEVICE-001",
            has_person=False,
            has_device=True
        )
        sa = self.create_substance_admin_with_authors([author])

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        assert "requester" in med_request
        assert med_request["requester"]["reference"] == "Device/device-DEVICE-001"

    def test_authored_on_still_uses_earliest_author(self):
        """Test that authoredOn still uses earliest author time (existing behavior)."""
        authors = [
            self.create_author(time="20240301", practitioner_ext="LATEST-DOC"),
            self.create_author(time="20240101", practitioner_ext="EARLIEST-DOC"),
        ]
        sa = self.create_substance_admin_with_authors(authors)

        converter = MedicationRequestConverter(code_system_mapper=None)
        med_request = converter.convert(sa)

        # authoredOn should still use earliest
        assert med_request.get("authoredOn") == "2024-01-01"
        # requester should use latest
        assert med_request["requester"]["reference"] == "Practitioner/practitioner-LATEST-DOC"
