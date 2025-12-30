"""Unit tests for MedicationDispense converter."""

import pytest

from ccda_to_fhir.ccda.models.author import AssignedAuthor, Author
from ccda_to_fhir.ccda.models.author import AssignedPerson as AuthorAssignedPerson
from ccda_to_fhir.ccda.models.datatypes import CE, CS, II, INT, IVL_INT, IVL_TS, PQ, TS
from ccda_to_fhir.ccda.models.performer import AssignedEntity, Performer
from ccda_to_fhir.ccda.models.substance_administration import (
    ManufacturedMaterial,
    ManufacturedProduct,
)
from ccda_to_fhir.ccda.models.supply import Supply
from ccda_to_fhir.converters.medication_dispense import MedicationDispenseConverter


def create_minimal_dispense() -> Supply:
    """Create minimal valid medication dispense for testing."""
    dispense = Supply()
    dispense.class_code = "SPLY"
    dispense.mood_code = "EVN"  # Event (dispense), not INT (order)
    dispense.template_id = [
        II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
    ]
    dispense.id = [II(root="dispense-456")]
    # Per C-CDA spec: statusCode is fixed to "completed"
    dispense.status_code = CS(code="completed")
    # Actual status comes from code element (FHIR value set)
    dispense.code = CE(
        code="completed",
        code_system="2.16.840.1.113883.4.642.3.1312",
        display_name="Completed",
    )
    # Add effectiveTime to satisfy US Core constraint for completed status
    dispense.effective_time = IVL_TS(value="20200301143000-0500")

    # Product (medication)
    material = ManufacturedMaterial()
    material.code = CE(
        code="314076",
        code_system="2.16.840.1.113883.6.88",
        display_name="Lisinopril 10 MG Oral Tablet",
    )
    product = ManufacturedProduct()
    product.manufactured_material = material
    dispense.product = product

    return dispense


class TestMedicationDispenseConverter:
    """Test MedicationDispense converter basic mappings."""

    def test_basic_conversion(self, mock_reference_registry):
        """Test basic medication dispense conversion."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert result["resourceType"] == "MedicationDispense"
        assert "id" in result
        assert result["status"] == "completed"
        assert "medicationCodeableConcept" in result
        assert result["medicationCodeableConcept"]["coding"][0]["code"] == "314076"

    def test_identifier_mapping(self, mock_reference_registry):
        """Test identifier mapping from supply.id."""
        dispense = create_minimal_dispense()
        dispense.id = [
            II(root="2.16.840.1.113883.19.5", extension="dispense-123"),
            II(root="1.2.3.4", extension="alt-id"),
        ]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "identifier" in result
        assert len(result["identifier"]) == 2
        # The value is just the extension, not the full OID
        assert result["identifier"][0]["value"] == "dispense-123"
        assert result["identifier"][1]["value"] == "alt-id"

    def test_status_mapping(self, mock_reference_registry):
        """Test status code mapping from supply.code element.

        Per C-CDA spec: statusCode is fixed to "completed",
        actual status comes from code element using FHIR value set.
        """
        # Test direct FHIR codes (preferred per C-CDA spec)
        fhir_test_cases = [
            "completed",
            "in-progress",
            "stopped",
            "cancelled",
            "on-hold",
            "preparation",
            "entered-in-error",
            "declined",
            "unknown",
        ]

        for fhir_status in fhir_test_cases:
            dispense = create_minimal_dispense()
            # statusCode is always "completed" per C-CDA spec
            dispense.status_code = CS(code="completed")
            # Actual status in code element
            dispense.code = CE(
                code=fhir_status,
                code_system="2.16.840.1.113883.4.642.3.1312",
                display_name=fhir_status.title(),
            )

            converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
            result = converter.convert(dispense)

            assert result["status"] == fhir_status, f"Failed for FHIR code {fhir_status}"

        # Test legacy ActStatus codes (backwards compatibility)
        legacy_test_cases = [
            ("completed", "completed"),
            ("active", "in-progress"),
            ("aborted", "stopped"),
            ("cancelled", "cancelled"),
            ("held", "on-hold"),
            ("new", "preparation"),
            ("nullified", "entered-in-error"),
        ]

        for legacy_code, expected_fhir in legacy_test_cases:
            dispense = create_minimal_dispense()
            dispense.status_code = CS(code="completed")
            dispense.code = CE(
                code=legacy_code,
                code_system="2.16.840.1.113883.5.14",  # ActStatus
                display_name=legacy_code.title(),
            )

            converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
            result = converter.convert(dispense)

            assert result["status"] == expected_fhir, f"Failed for legacy code {legacy_code}"

    def test_medication_code_mapping(self, mock_reference_registry):
        """Test medication code mapping with RxNorm."""
        dispense = create_minimal_dispense()
        material = ManufacturedMaterial()
        material.code = CE(
            code="314076",
            code_system="2.16.840.1.113883.6.88",  # RxNorm OID
            display_name="Lisinopril 10 MG Oral Tablet",
        )
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "medicationCodeableConcept" in result
        coding = result["medicationCodeableConcept"]["coding"][0]
        assert coding["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
        assert coding["code"] == "314076"
        assert coding["display"] == "Lisinopril 10 MG Oral Tablet"

    def test_medication_code_with_translation(self, mock_reference_registry):
        """Test medication code with NDC translation."""
        dispense = create_minimal_dispense()
        material = ManufacturedMaterial()
        material.code = CE(
            code="314076",
            code_system="2.16.840.1.113883.6.88",
            display_name="Lisinopril 10 MG Oral Tablet",
            translation=[
                CE(
                    code="00591-3772-01",
                    code_system="2.16.840.1.113883.6.69",  # NDC OID
                    display_name="Lisinopril 10mg Tab",
                )
            ],
        )
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "medicationCodeableConcept" in result
        codings = result["medicationCodeableConcept"]["coding"]
        assert len(codings) == 2
        assert codings[0]["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
        assert codings[1]["system"] == "http://hl7.org/fhir/sid/ndc"
        assert codings[1]["code"] == "00591-3772-01"

    def test_quantity_mapping(self, mock_reference_registry):
        """Test quantity mapping with UCUM units."""
        dispense = create_minimal_dispense()
        dispense.quantity = PQ(value="30", unit="{tbl}")

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "quantity" in result
        assert result["quantity"]["value"] == 30
        assert result["quantity"]["unit"] == "{tbl}"  # Unit is code, not display name
        assert result["quantity"]["system"] == "http://unitsofmeasure.org"
        assert result["quantity"]["code"] == "{tbl}"


class TestMedicationDispenseTiming:
    """Test timing/effectiveTime mappings."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_single_timestamp_maps_to_when_handed_over(self, mock_reference_registry):
        """Test single effectiveTime maps to whenHandedOver."""
        dispense = create_minimal_dispense()
        dispense.effective_time = IVL_TS(value="20200301143000-0500")

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"

    def test_period_maps_to_when_prepared_and_handed_over(self, mock_reference_registry):
        """Test IVL_TS period maps to whenPrepared and whenHandedOver."""
        dispense = create_minimal_dispense()
        dispense.effective_time = IVL_TS(
            low=TS(value="20200301090000-0500"), high=TS(value="20200301143000-0500")
        )

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T09:00:00-05:00"
        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"

    def test_missing_effective_time(self, mock_reference_registry):
        """Test handling of missing effectiveTime."""
        dispense = create_minimal_dispense()
        # Remove effective_time to test missing scenario
        dispense.effective_time = None

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should not have timing fields
        assert "whenHandedOver" not in result
        assert "whenPrepared" not in result
        # Status should be changed to in-progress due to missing whenHandedOver
        # (semantically more accurate than "unknown" - indicates medication ready for pickup)
        assert result["status"] == "in-progress"

    def test_when_handed_over_after_when_prepared_is_valid(self, mock_reference_registry):
        """Test FHIR invariant mdd-1: whenHandedOver after whenPrepared is valid."""
        dispense = create_minimal_dispense()
        # whenPrepared at 9:00 AM, whenHandedOver at 2:30 PM (valid)
        dispense.effective_time = IVL_TS(
            low=TS(value="20200301090000-0500"), high=TS(value="20200301143000-0500")
        )

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Both timestamps should be present and unchanged
        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T09:00:00-05:00"
        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"

    def test_when_handed_over_equals_when_prepared_is_valid(self, mock_reference_registry):
        """Test FHIR invariant mdd-1: whenHandedOver equal to whenPrepared is valid."""
        dispense = create_minimal_dispense()
        # Both at same time (edge case, but valid per mdd-1: whenHandedOver >= whenPrepared)
        dispense.effective_time = IVL_TS(
            low=TS(value="20200301090000-0500"), high=TS(value="20200301090000-0500")
        )

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Both timestamps should be present and unchanged
        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T09:00:00-05:00"
        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T09:00:00-05:00"

    def test_when_handed_over_before_when_prepared_triggers_mdd1_violation(self, caplog, mock_reference_registry):
        """Test FHIR invariant mdd-1: whenHandedOver before whenPrepared is invalid.

        Per FHIR invariant mdd-1: "whenHandedOver cannot be before whenPrepared"
        FHIRPath: whenHandedOver.empty() or whenPrepared.empty() or whenHandedOver >= whenPrepared

        When this violation occurs, the converter should:
        1. Log a warning
        2. Remove whenHandedOver to maintain FHIR validity
        """
        dispense = create_minimal_dispense()
        # whenPrepared at 2:30 PM, whenHandedOver at 9:00 AM (INVALID - handed over before prepared!)
        dispense.effective_time = IVL_TS(
            low=TS(value="20200301143000-0500"), high=TS(value="20200301090000-0500")
        )

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        with caplog.at_level("WARNING"):
            result = converter.convert(dispense)

        # whenPrepared should remain
        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T14:30:00-05:00"

        # whenHandedOver should be removed due to mdd-1 violation
        assert "whenHandedOver" not in result

        # Should have logged a warning about mdd-1 violation
        assert any("mdd-1 violation" in record.message for record in caplog.records)
        assert any("2020-03-01T09:00:00-05:00" in record.message for record in caplog.records)
        assert any("2020-03-01T14:30:00-05:00" in record.message for record in caplog.records)

    def test_only_when_prepared_does_not_trigger_mdd1(self, mock_reference_registry):
        """Test FHIR invariant mdd-1: only whenPrepared present does not violate invariant.

        Per FHIR invariant mdd-1, if whenHandedOver is empty, the constraint is satisfied.
        """
        dispense = create_minimal_dispense()
        # Only low (whenPrepared), no high (whenHandedOver)
        dispense.effective_time = IVL_TS(low=TS(value="20200301090000-0500"))

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Only whenPrepared should be present
        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T09:00:00-05:00"
        assert "whenHandedOver" not in result

    def test_only_when_handed_over_does_not_trigger_mdd1(self, mock_reference_registry):
        """Test FHIR invariant mdd-1: only whenHandedOver present does not violate invariant.

        Per FHIR invariant mdd-1, if whenPrepared is empty, the constraint is satisfied.
        """
        dispense = create_minimal_dispense()
        # Single value (whenHandedOver only)
        dispense.effective_time = IVL_TS(value="20200301143000-0500")

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Only whenHandedOver should be present
        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"
        assert "whenPrepared" not in result


class TestMedicationDispenseType:
    """Test dispense type inference from repeatNumber."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_repeat_number_1_maps_to_first_fill(self, mock_reference_registry):
        """Test repeatNumber=1 maps to first fill (FF)."""
        dispense = create_minimal_dispense()
        dispense.repeat_number = IVL_INT(low=INT(value=1))

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "type" in result
        coding = result["type"]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType"
        assert coding["code"] == "FF"
        assert coding["display"] == "First Fill"

    def test_repeat_number_2_maps_to_refill(self, mock_reference_registry):
        """Test repeatNumber>1 maps to refill (RF)."""
        dispense = create_minimal_dispense()
        dispense.repeat_number = IVL_INT(low=INT(value=2))

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "type" in result
        coding = result["type"]["coding"][0]
        assert coding["code"] == "RF"
        assert coding["display"] == "Refill"

    def test_no_repeat_number_no_type(self, mock_reference_registry):
        """Test missing repeatNumber does not set type."""
        dispense = create_minimal_dispense()
        # No repeat_number set

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "type" not in result

    def test_days_supply_extraction(self, mock_reference_registry):
        """Test days supply extraction from nested Days Supply template."""
        from ccda_to_fhir.ccda.models.observation import EntryRelationship

        dispense = create_minimal_dispense()

        # Create nested Days Supply
        days_supply_supply = Supply()
        days_supply_supply.template_id = [
            II(root="2.16.840.1.113883.10.20.37.3.10", extension="2017-08-01")
        ]
        days_supply_supply.quantity = PQ(value="30", unit="d")

        # Add as entry relationship
        entry_rel = EntryRelationship()
        entry_rel.type_code = "COMP"
        entry_rel.supply = days_supply_supply

        dispense.entry_relationship = [entry_rel]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "daysSupply" in result
        assert result["daysSupply"]["value"] == 30
        assert result["daysSupply"]["unit"] == "d"
        assert result["daysSupply"]["system"] == "http://unitsofmeasure.org"
        assert result["daysSupply"]["code"] == "d"


class TestMedicationDispensePerformer:
    """Test performer (pharmacy/pharmacist) mapping."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_performer_with_person_creates_practitioner(self, mock_reference_registry):
        """Test performer with assignedPerson creates Practitioner reference."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )

        dispense = create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization
        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "performer" in result
        assert len(result["performer"]) >= 1
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Practitioner/")

    def test_performer_with_only_organization_creates_organization_performer(self, mock_reference_registry):
        """Test performer with only representedOrganization (no assignedPerson) creates Organization reference."""
        from ccda_to_fhir.ccda.models.performer import RepresentedOrganization
        from ccda_to_fhir.converters.references import ReferenceRegistry

        dispense = create_minimal_dispense()

        # Create assignedEntity with ONLY representedOrganization (no assignedPerson)
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]

        # representedOrganization only
        org = RepresentedOrganization()
        org.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        org.name = ["Community Pharmacy"]
        assigned_entity.represented_organization = org

        # Explicitly ensure no assigned_person
        # (no assigned_entity.assigned_person = ...)

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        # Set up registry with patient reference
        registry = ReferenceRegistry()
        registry.register_resource({"resourceType": "Patient", "id": "test-patient"})

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have performer entry with Organization reference
        assert "performer" in result
        assert len(result["performer"]) >= 1
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Organization/")

        # Should have function code
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"

        # Should have created Organization resource in registry
        org_ref = result["performer"][0]["actor"]["reference"]
        org_id = org_ref.split("/")[1]
        assert registry.has_resource("Organization", org_id)

    def test_performer_with_both_person_and_organization(self, mock_reference_registry):
        """Test performer with both assignedPerson and representedOrganization creates Practitioner performer."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        dispense = create_minimal_dispense()

        # Create assignedEntity with BOTH assignedPerson and representedOrganization
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        org = RepresentedOrganization()
        org.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        org.name = ["Community Pharmacy"]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        # Set up registry with patient reference
        registry = ReferenceRegistry()
        registry.register_resource({"resourceType": "Patient", "id": "test-patient"})

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have performer entry with Practitioner reference (person takes precedence)
        assert "performer" in result
        assert len(result["performer"]) >= 1
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Practitioner/")

        # Should also have location (from representedOrganization)
        assert "location" in result
        assert result["location"]["reference"].startswith("Location/")

    def test_author_creates_performer_with_packager_function(self, mock_reference_registry):
        """Test author creates performer entry with packager function."""
        dispense = create_minimal_dispense()

        assigned_author = AssignedAuthor()
        assigned_author.id = [
            II(root="2.16.840.1.113883.4.6", extension="9876543210")
        ]
        assigned_author.assigned_person = AuthorAssignedPerson()

        author = Author()
        author.time = TS(value="20200301143000-0500")
        author.assigned_author = assigned_author

        dispense.author = [author]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "performer" in result
        # Should have performer entry with packager function
        packager_performers = [
            p for p in result["performer"]
            if "function" in p and p["function"]["coding"][0]["code"] == "packager"
        ]
        assert len(packager_performers) >= 1


class TestMedicationDispenseCategory:
    """Test category inference."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_default_category_community(self, mock_reference_registry):
        """Test default category is community."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "category" in result
        coding = result["category"]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/medicationdispense-category"
        assert coding["code"] == "community"
        assert coding["display"] == "Community"


class TestMedicationDispenseUSCoreProfile:
    """Test US Core MedicationDispense profile compliance."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_us_core_profile_in_meta(self, mock_reference_registry):
        """Test US Core profile is included in meta.profile."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        assert "meta" in result
        assert "profile" in result["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense" in result["meta"]["profile"]

    def test_required_elements_present(self, mock_reference_registry):
        """Test all US Core required elements are present."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # US Core SHALL elements
        assert "status" in result
        assert "medicationCodeableConcept" in result or "medicationReference" in result
        assert "subject" in result


class TestMedicationDispenseValidation:
    """Test validation and error handling."""

    def test_missing_product_raises_error(self, mock_reference_registry):
        """Test that missing product raises ValueError."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )
        # No product set

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)

        with pytest.raises(ValueError, match="product"):
            converter.convert(dispense)

    def test_invalid_mood_code_raises_error(self, mock_reference_registry):
        """Test that moodCode != EVN raises error."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "INT"  # Intent, not event
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)

        with pytest.raises(ValueError, match="moodCode"):
            converter.convert(dispense)

    def test_completed_without_when_handed_over_sets_in_progress(self, mock_reference_registry):
        """Test US Core constraint: completed status requires whenHandedOver.

        When status is 'completed' but whenHandedOver is missing, status is changed
        to 'in-progress' (ready for pickup) which is more semantically accurate than
        'unknown' per FHIR status definitions.
        """
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )
        # No effective_time set

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should adjust status to 'in-progress' per US Core constraint
        # in-progress = "dispensed product is ready for pickup" (FHIR spec)
        assert result["status"] == "in-progress"
        assert "whenHandedOver" not in result


class TestMedicationDispenseWithRegistry:
    """Integration tests with ReferenceRegistry."""

    def test_context_populated_when_encounter_registered(self, mock_reference_registry):
        """Test that context is populated when encounter exists in registry."""
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry with patient and encounter
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        encounter = {
            "resourceType": "Encounter",
            "id": "encounter-abc",
        }

        registry.register_resource(patient)
        registry.register_resource(encounter)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create minimal dispense
        dispense = create_minimal_dispense()

        result = converter.convert(dispense)

        # Should have context reference
        assert "context" in result
        assert result["context"] == {"reference": "Encounter/encounter-abc"}

    def test_context_not_populated_when_no_encounter(self, mock_reference_registry):
        """Test that context is not populated when no encounter in registry."""
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry with only patient (no encounter)
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }

        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create minimal dispense
        dispense = create_minimal_dispense()

        result = converter.convert(dispense)

        # Should NOT have context reference
        assert "context" not in result

    def test_subject_uses_registry_patient(self, mock_reference_registry):
        """Test that subject references patient from registry."""
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry with patient
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-xyz",
        }

        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create minimal dispense
        dispense = create_minimal_dispense()

        result = converter.convert(dispense)

        # Should reference the patient from registry
        assert result["subject"] == {"reference": "Patient/patient-xyz"}


class TestMedicationDispensePharmacyLocation:
    """Test pharmacy Location resource creation."""

    def create_minimal_dispense(self) -> Supply:
        """Create minimal valid medication dispense."""
        dispense = Supply()
        dispense.class_code = "SPLY"
        dispense.mood_code = "EVN"
        dispense.template_id = [
            II(root="2.16.840.1.113883.10.20.22.4.18", extension="2014-06-09")
        ]
        dispense.id = [II(root="dispense-456")]
        dispense.status_code = CS(code="completed")
        dispense.code = CE(
            code="completed",
            code_system="2.16.840.1.113883.4.642.3.1312",
            display_name="Completed",
        )
        dispense.effective_time = IVL_TS(value="20200301143000-0500")

        material = ManufacturedMaterial()
        material.code = CE(code="314076", code_system="2.16.840.1.113883.6.88")
        product = ManufacturedProduct()
        product.manufactured_material = material
        dispense.product = product

        return dispense

    def test_location_created_when_represented_organization_present(self, mock_reference_registry):
        """Test Location resource created for representedOrganization."""
        from ccda_to_fhir.ccda.models.datatypes import AD, TEL
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense with pharmacy organization
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization (pharmacy)
        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        org.addr = [AD(
            street_address_line=["123 Pharmacy Lane"],
            city="Boston",
            state="MA",
            postal_code="02101"
        )]
        org.telecom = [TEL(value="tel:(555)555-1000", use="WP")]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Should have location reference
        assert "location" in result
        assert "reference" in result["location"]
        assert result["location"]["reference"].startswith("Location/")

        # Location resource should be in registry
        location_id = result["location"]["reference"].split("/")[1]
        assert registry.has_resource("Location", location_id)

        # Get the Location resource from registry
        location = registry.get_resource("Location", location_id)
        assert location is not None
        assert location["resourceType"] == "Location"
        assert location["name"] == "Community Pharmacy"
        assert location["status"] == "active"
        assert location["mode"] == "instance"

        # Check type is PHARM
        assert "type" in location
        assert len(location["type"]) == 1
        coding = location["type"][0]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
        assert coding["code"] == "PHARM"
        assert coding["display"] == "Pharmacy"

        # Check address
        assert "address" in location
        assert location["address"]["line"] == ["123 Pharmacy Lane"]
        assert location["address"]["city"] == "Boston"
        assert location["address"]["state"] == "MA"
        assert location["address"]["postalCode"] == "02101"

        # Check telecom
        assert "telecom" in location
        assert len(location["telecom"]) == 1
        assert location["telecom"][0]["system"] == "phone"
        assert location["telecom"][0]["value"] == "(555)555-1000"
        assert location["telecom"][0]["use"] == "work"

    def test_location_includes_identifiers_from_organization(self, mock_reference_registry):
        """Test Location.identifier populated from organization identifiers (US Core Must Support)."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense with pharmacy organization that has identifiers
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization with identifiers (NPI and custom identifier)
        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        org.id = [
            II(root="2.16.840.1.113883.4.6", extension="1234567890"),  # NPI
            II(root="1.2.3.4.5.6", extension="PHARM-001"),  # Custom identifier
        ]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Get the Location resource from registry
        location_id = result["location"]["reference"].split("/")[1]
        location = registry.get_resource("Location", location_id)

        # Verify identifiers are populated (US Core Must Support)
        assert "identifier" in location, "Location.identifier missing (US Core Must Support violation)"
        assert len(location["identifier"]) == 2

        # Check first identifier (NPI - OID mapped to FHIR URI)
        id1 = location["identifier"][0]
        assert "system" in id1
        assert "value" in id1
        assert id1["value"] == "1234567890"
        assert id1["system"] == "http://hl7.org/fhir/sid/us-npi"

        # Check second identifier (custom OID - becomes urn:oid:)
        id2 = location["identifier"][1]
        assert "system" in id2
        assert "value" in id2
        assert id2["value"] == "PHARM-001"
        assert id2["system"] == "urn:oid:1.2.3.4.5.6"

    def test_location_not_created_without_represented_organization(self, mock_reference_registry):
        """Test Location not created when representedOrganization is absent."""
        from ccda_to_fhir.ccda.models.performer import AssignedPerson
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense WITHOUT pharmacy organization
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()
        # No represented_organization

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Should NOT have location reference
        assert "location" not in result

    def test_location_not_created_without_organization_name(self, mock_reference_registry):
        """Test Location not created when organization lacks name."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense with pharmacy organization WITHOUT name
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization without name
        org = RepresentedOrganization()
        # No name field
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Should NOT have location reference (name is required)
        assert "location" not in result

    def test_location_not_created_without_registry(self, mock_reference_registry):
        """Test that MedicationDispense conversion requires reference registry.

        Since reference_registry is now required for FHIR compliance,
        attempting to convert without it should raise ValueError.
        """
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )

        # Create converter WITHOUT registry (None)
        converter = MedicationDispenseConverter(reference_registry=None)

        # Create dispense with pharmacy organization
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization
        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        # Should raise ValueError when registry is missing
        with pytest.raises(ValueError, match="reference_registry is required"):
            converter.convert(dispense)

    def test_location_reused_for_same_organization(self, mock_reference_registry):
        """Test same Location resource reused for same organization."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create first dispense
        dispense1 = self.create_minimal_dispense()
        dispense1.id = [II(root="dispense-1")]

        assigned_entity1 = AssignedEntity()
        assigned_entity1.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity1.assigned_person = AssignedPerson()

        org1 = RepresentedOrganization()
        org1.id = [II(root="org-123", extension="pharmacy-1")]
        org1.name = ["Community Pharmacy"]
        assigned_entity1.represented_organization = org1

        performer1 = Performer()
        performer1.assigned_entity = assigned_entity1

        dispense1.performer = [performer1]

        result1 = converter.convert(dispense1)

        # Create second dispense with SAME organization
        dispense2 = self.create_minimal_dispense()
        dispense2.id = [II(root="dispense-2")]

        assigned_entity2 = AssignedEntity()
        assigned_entity2.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity2.assigned_person = AssignedPerson()

        org2 = RepresentedOrganization()
        org2.id = [II(root="org-123", extension="pharmacy-1")]  # SAME ID
        org2.name = ["Community Pharmacy"]
        assigned_entity2.represented_organization = org2

        performer2 = Performer()
        performer2.assigned_entity = assigned_entity2

        dispense2.performer = [performer2]

        result2 = converter.convert(dispense2)

        # Both should reference the SAME Location resource
        assert result1["location"]["reference"] == result2["location"]["reference"]

    def test_location_with_multiple_address_lines(self, mock_reference_registry):
        """Test Location address with multiple street lines."""
        from ccda_to_fhir.ccda.models.datatypes import AD
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense with pharmacy organization
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization with multiple address lines
        org = RepresentedOrganization()
        org.name = ["Downtown Pharmacy"]
        org.addr = [AD(
            street_address_line=["Suite 200", "456 Main Street"],
            city="Springfield",
            state="IL",
            postal_code="62701"
        )]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Get the Location resource
        location_id = result["location"]["reference"].split("/")[1]
        location = registry.get_resource("Location", location_id)

        # Check address has multiple lines
        assert "address" in location
        assert location["address"]["line"] == ["Suite 200", "456 Main Street"]
        assert location["address"]["city"] == "Springfield"

    def test_location_with_minimal_organization_info(self, mock_reference_registry):
        """Test Location created with minimal organization info (name only)."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()

        patient = {
            "resourceType": "Patient",
            "id": "patient-123",
        }
        registry.register_resource(patient)

        # Create converter with registry
        converter = MedicationDispenseConverter(reference_registry=registry)

        # Create dispense with minimal pharmacy organization (name only)
        dispense = self.create_minimal_dispense()

        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        # representedOrganization with only name
        org = RepresentedOrganization()
        org.name = ["Pharmacy Express"]
        # No address, telecom, or other fields
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity

        dispense.performer = [performer]

        result = converter.convert(dispense)

        # Should have location reference
        assert "location" in result

        # Get the Location resource
        location_id = result["location"]["reference"].split("/")[1]
        location = registry.get_resource("Location", location_id)

        # Check minimal required fields
        assert location["resourceType"] == "Location"
        assert location["name"] == "Pharmacy Express"
        assert location["status"] == "active"
        assert location["mode"] == "instance"

        # Optional fields should not be present
        assert "address" not in location
        assert "telecom" not in location


class TestPerformerFunction:
    """Test performer function determination and mapping."""

    def test_performer_with_function_code_pcp_maps_to_finalchecker(self, mock_reference_registry):
        """Test performer with PCP functionCode maps to finalchecker."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
        )

        dispense = create_minimal_dispense()

        # Create performer with functionCode="PCP"
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        assigned_entity.assigned_person = AssignedPerson()

        performer = Performer()
        performer.function_code = CE(
            code="PCP",
            code_system="2.16.840.1.113883.5.88",
            display_name="Primary Care Physician"
        )
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should have performer with finalchecker function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"

    def test_performer_with_function_code_packpharm_maps_to_packager(self, mock_reference_registry):
        """Test performer with PACKPHARM functionCode maps to packager."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
        )

        dispense = create_minimal_dispense()

        # Create performer with functionCode="PACKPHARM" (local extension)
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        assigned_entity.assigned_person = AssignedPerson()

        performer = Performer()
        performer.function_code = CE(
            code="PACKPHARM",
            code_system="2.16.840.1.113883.5.88",
            display_name="Packaging Pharmacist"
        )
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should have performer with packager function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "packager"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Packager"

    def test_performer_without_function_code_defaults_to_finalchecker(self, mock_reference_registry):
        """Test performer without functionCode defaults to finalchecker."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
        )

        dispense = create_minimal_dispense()

        # Create performer without functionCode
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        assigned_entity.assigned_person = AssignedPerson()

        performer = Performer()
        # No function_code set
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should have performer with default finalchecker function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"

    def test_author_without_function_code_defaults_to_packager(self, mock_reference_registry):
        """Test author performer without functionCode defaults to packager."""
        from ccda_to_fhir.ccda.models.author import (
            AssignedAuthor,
            Author,
        )
        from ccda_to_fhir.ccda.models.author import AssignedPerson as AuthorAssignedPerson

        dispense = create_minimal_dispense()

        # Create author without functionCode
        assigned_author = AssignedAuthor()
        assigned_author.id = [II(root="2.16.840.1.113883.4.6", extension="9999999999")]
        assigned_author.assigned_person = AuthorAssignedPerson()

        author = Author()
        author.assigned_author = assigned_author
        dispense.author = [author]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should have author performer with packager function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "packager"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Packager"

    def test_author_with_function_code_uses_mapped_function(self, mock_reference_registry):
        """Test author with functionCode uses mapped function."""
        from ccda_to_fhir.ccda.models.author import (
            AssignedAuthor,
            Author,
        )
        from ccda_to_fhir.ccda.models.author import AssignedPerson as AuthorAssignedPerson

        dispense = create_minimal_dispense()

        # Create author with functionCode="ADMPHYS" (should map to finalchecker)
        assigned_author = AssignedAuthor()
        assigned_author.id = [II(root="2.16.840.1.113883.4.6", extension="9999999999")]
        assigned_author.assigned_person = AuthorAssignedPerson()

        author = Author()
        author.function_code = CE(
            code="ADMPHYS",
            code_system="2.16.840.1.113883.5.88",
            display_name="Admitting Physician"
        )
        author.assigned_author = assigned_author
        dispense.author = [author]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should have author performer with finalchecker function (mapped from ADMPHYS)
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"

    def test_performer_with_unknown_function_code_uses_default(self, mock_reference_registry):
        """Test performer with unknown functionCode falls back to default."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
        )

        dispense = create_minimal_dispense()

        # Create performer with unknown functionCode
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="1234567890")]
        assigned_entity.assigned_person = AssignedPerson()

        performer = Performer()
        performer.function_code = CE(
            code="UNKNOWN_CODE",
            code_system="2.16.840.1.113883.5.88",
            display_name="Unknown Role"
        )
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=mock_reference_registry)
        result = converter.convert(dispense)

        # Should fall back to default finalchecker function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"

    def test_organization_performer_without_function_code_defaults_to_finalchecker(self, mock_reference_registry):
        """Test organization performer without functionCode defaults to finalchecker."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            Performer,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()
        patient = {"resourceType": "Patient", "id": "patient-123"}
        registry.register_resource(patient)

        dispense = create_minimal_dispense()

        # Create organization performer without functionCode
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="ORG-001")]

        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        org.id = [II(root="1.2.3.4", extension="PHARM-001")]
        assigned_entity.represented_organization = org

        performer = Performer()
        # No function_code set
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have organization performer with default finalchecker function
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"
        # Verify it's an organization reference
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Organization/")

    def test_organization_performer_with_function_code_uses_mapped_function(self, mock_reference_registry):
        """Test organization performer with functionCode uses mapped function."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            Performer,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()
        patient = {"resourceType": "Patient", "id": "patient-123"}
        registry.register_resource(patient)

        dispense = create_minimal_dispense()

        # Create organization performer with functionCode="PHARM"
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="ORG-001")]

        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        org.id = [II(root="1.2.3.4", extension="PHARM-001")]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.function_code = CE(
            code="PHARM",
            code_system="2.16.840.1.113883.5.88",
            display_name="Pharmacist"
        )
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have organization performer with finalchecker function (mapped from PHARM)
        assert "performer" in result
        assert len(result["performer"]) == 1
        assert "function" in result["performer"][0]
        assert result["performer"][0]["function"]["coding"][0]["code"] == "finalchecker"
        assert result["performer"][0]["function"]["coding"][0]["display"] == "Final Checker"
        # Verify it's an organization reference
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Organization/")


class TestLocationManagingOrganization:
    """Test Location.managingOrganization population."""

    def test_location_includes_managing_organization_reference(self, mock_reference_registry):
        """Test Location created with managingOrganization reference to pharmacy Organization."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()
        patient = {"resourceType": "Patient", "id": "patient-123"}
        registry.register_resource(patient)

        dispense = create_minimal_dispense()

        # Create performer with representedOrganization
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="9876543210")]
        assigned_entity.assigned_person = AssignedPerson()

        org = RepresentedOrganization()
        org.name = ["Community Pharmacy"]
        org.id = [II(root="1.2.3.4", extension="PHARM-001")]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have location reference
        assert "location" in result
        location_id = result["location"]["reference"].split("/")[1]

        # Get the Location resource
        location = registry.get_resource("Location", location_id)

        # Should have managingOrganization
        assert "managingOrganization" in location
        assert "reference" in location["managingOrganization"]
        org_ref = location["managingOrganization"]["reference"]
        assert org_ref.startswith("Organization/")

        # Verify the Organization exists
        org_id = org_ref.split("/")[1]
        organization = registry.get_resource("Organization", org_id)
        assert organization is not None
        assert organization["resourceType"] == "Organization"
        assert organization["name"] == "Community Pharmacy"

    def test_location_managing_organization_with_organization_performer(self, mock_reference_registry):
        """Test Location managingOrganization when performer is an Organization."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            Performer,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()
        patient = {"resourceType": "Patient", "id": "patient-123"}
        registry.register_resource(patient)

        dispense = create_minimal_dispense()

        # Create organization performer (no assignedPerson)
        assigned_entity = AssignedEntity()
        assigned_entity.id = [II(root="2.16.840.1.113883.4.6", extension="ORG-123")]

        org = RepresentedOrganization()
        org.name = ["Pharmacy Corp"]
        org.id = [II(root="1.2.3.4.5", extension="ORG-456")]
        assigned_entity.represented_organization = org

        performer = Performer()
        performer.assigned_entity = assigned_entity
        dispense.performer = [performer]

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have both performer and location
        assert "performer" in result
        assert "location" in result

        # Get performer Organization ID
        performer_org_ref = result["performer"][0]["actor"]["reference"]
        performer_org_id = performer_org_ref.split("/")[1]

        # Get Location managingOrganization ID
        location_id = result["location"]["reference"].split("/")[1]
        location = registry.get_resource("Location", location_id)
        managing_org_ref = location["managingOrganization"]["reference"]
        managing_org_id = managing_org_ref.split("/")[1]

        # They should reference the same Organization
        assert performer_org_id == managing_org_id

        # Verify the Organization exists and is correct
        organization = registry.get_resource("Organization", managing_org_id)
        assert organization["name"] == "Pharmacy Corp"

    def test_location_managing_organization_reuses_existing_organization(self, mock_reference_registry):
        """Test Location managingOrganization references existing Organization if already created."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedEntity,
            AssignedPerson,
            Performer,
            RepresentedOrganization,
        )
        from ccda_to_fhir.converters.references import ReferenceRegistry

        # Create registry
        registry = ReferenceRegistry()
        patient = {"resourceType": "Patient", "id": "patient-123"}
        registry.register_resource(patient)

        dispense = create_minimal_dispense()

        # Create two performers with the same representedOrganization
        org = RepresentedOrganization()
        org.name = ["Shared Pharmacy"]
        org.id = [II(root="1.2.3.4", extension="SHARED-001")]

        # First performer - practitioner at pharmacy
        assigned_entity1 = AssignedEntity()
        assigned_entity1.id = [II(root="2.16.840.1.113883.4.6", extension="PRACT-001")]
        assigned_entity1.assigned_person = AssignedPerson()
        assigned_entity1.represented_organization = org

        performer1 = Performer()
        performer1.assigned_entity = assigned_entity1

        # Second performer - organization only
        assigned_entity2 = AssignedEntity()
        assigned_entity2.id = [II(root="2.16.840.1.113883.4.6", extension="SHARED-001")]
        assigned_entity2.represented_organization = org

        performer2 = Performer()
        performer2.assigned_entity = assigned_entity2

        dispense.performer = [performer1, performer2]

        converter = MedicationDispenseConverter(reference_registry=registry)
        result = converter.convert(dispense)

        # Should have location
        assert "location" in result
        location_id = result["location"]["reference"].split("/")[1]
        location = registry.get_resource("Location", location_id)

        # Should have managingOrganization
        assert "managingOrganization" in location
        managing_org_id = location["managingOrganization"]["reference"].split("/")[1]

        # Get second performer's organization reference
        org_performer_id = result["performer"][1]["actor"]["reference"].split("/")[1]

        # Should be the same Organization (reused, not duplicated)
        assert managing_org_id == org_performer_id

        # Verify the Organization exists and was created
        organization = registry.get_resource("Organization", managing_org_id)
        assert organization is not None
        assert organization["resourceType"] == "Organization"
        assert organization["name"] == "Shared Pharmacy"
