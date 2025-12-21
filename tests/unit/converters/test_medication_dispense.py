"""Unit tests for MedicationDispense converter."""

import pytest

from ccda_to_fhir.ccda.models.author import Author, AssignedAuthor
from ccda_to_fhir.ccda.models.author import AssignedPerson as AuthorAssignedPerson
from ccda_to_fhir.ccda.models.datatypes import CE, CS, II, INT, IVL_INT, IVL_TS, PQ, TS
from ccda_to_fhir.ccda.models.performer import Performer, AssignedEntity
from ccda_to_fhir.ccda.models.supply import Supply
from ccda_to_fhir.ccda.models.substance_administration import (
    Consumable,
    ManufacturedMaterial,
    ManufacturedProduct,
)
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

    def test_basic_conversion(self):
        """Test basic medication dispense conversion."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert result["resourceType"] == "MedicationDispense"
        assert "id" in result
        assert result["status"] == "completed"
        assert "medicationCodeableConcept" in result
        assert result["medicationCodeableConcept"]["coding"][0]["code"] == "314076"

    def test_identifier_mapping(self):
        """Test identifier mapping from supply.id."""
        dispense = create_minimal_dispense()
        dispense.id = [
            II(root="2.16.840.1.113883.19.5", extension="dispense-123"),
            II(root="1.2.3.4", extension="alt-id"),
        ]

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "identifier" in result
        assert len(result["identifier"]) == 2
        # The value is just the extension, not the full OID
        assert result["identifier"][0]["value"] == "dispense-123"
        assert result["identifier"][1]["value"] == "alt-id"

    def test_status_mapping(self):
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

            converter = MedicationDispenseConverter()
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

            converter = MedicationDispenseConverter()
            result = converter.convert(dispense)

            assert result["status"] == expected_fhir, f"Failed for legacy code {legacy_code}"

    def test_medication_code_mapping(self):
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

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "medicationCodeableConcept" in result
        coding = result["medicationCodeableConcept"]["coding"][0]
        assert coding["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
        assert coding["code"] == "314076"
        assert coding["display"] == "Lisinopril 10 MG Oral Tablet"

    def test_medication_code_with_translation(self):
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

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "medicationCodeableConcept" in result
        codings = result["medicationCodeableConcept"]["coding"]
        assert len(codings) == 2
        assert codings[0]["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"
        assert codings[1]["system"] == "http://hl7.org/fhir/sid/ndc"
        assert codings[1]["code"] == "00591-3772-01"

    def test_quantity_mapping(self):
        """Test quantity mapping with UCUM units."""
        dispense = create_minimal_dispense()
        dispense.quantity = PQ(value="30", unit="{tbl}")

        converter = MedicationDispenseConverter()
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

    def test_single_timestamp_maps_to_when_handed_over(self):
        """Test single effectiveTime maps to whenHandedOver."""
        dispense = create_minimal_dispense()
        dispense.effective_time = IVL_TS(value="20200301143000-0500")

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"

    def test_period_maps_to_when_prepared_and_handed_over(self):
        """Test IVL_TS period maps to whenPrepared and whenHandedOver."""
        dispense = create_minimal_dispense()
        dispense.effective_time = IVL_TS(
            low=TS(value="20200301090000-0500"), high=TS(value="20200301143000-0500")
        )

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "whenPrepared" in result
        assert result["whenPrepared"] == "2020-03-01T09:00:00-05:00"
        assert "whenHandedOver" in result
        assert result["whenHandedOver"] == "2020-03-01T14:30:00-05:00"

    def test_missing_effective_time(self):
        """Test handling of missing effectiveTime."""
        dispense = create_minimal_dispense()
        # Remove effective_time to test missing scenario
        dispense.effective_time = None

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        # Should not have timing fields
        assert "whenHandedOver" not in result
        assert "whenPrepared" not in result
        # Status should be changed to unknown due to missing whenHandedOver
        assert result["status"] == "unknown"


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

    def test_repeat_number_1_maps_to_first_fill(self):
        """Test repeatNumber=1 maps to first fill (FF)."""
        dispense = create_minimal_dispense()
        dispense.repeat_number = IVL_INT(low=INT(value=1))

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "type" in result
        coding = result["type"]["coding"][0]
        assert coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType"
        assert coding["code"] == "FF"
        assert coding["display"] == "First Fill"

    def test_repeat_number_2_maps_to_refill(self):
        """Test repeatNumber>1 maps to refill (RF)."""
        dispense = create_minimal_dispense()
        dispense.repeat_number = IVL_INT(low=INT(value=2))

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "type" in result
        coding = result["type"]["coding"][0]
        assert coding["code"] == "RF"
        assert coding["display"] == "Refill"

    def test_no_repeat_number_no_type(self):
        """Test missing repeatNumber does not set type."""
        dispense = create_minimal_dispense()
        # No repeat_number set

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "type" not in result

    def test_days_supply_extraction(self):
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

        converter = MedicationDispenseConverter()
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

    def test_performer_with_person_creates_practitioner(self):
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

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "performer" in result
        assert len(result["performer"]) >= 1
        assert "actor" in result["performer"][0]
        assert result["performer"][0]["actor"]["reference"].startswith("Practitioner/")

    def test_author_creates_performer_with_packager_function(self):
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

        converter = MedicationDispenseConverter()
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

    def test_default_category_community(self):
        """Test default category is community."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter()
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

    def test_us_core_profile_in_meta(self):
        """Test US Core profile is included in meta.profile."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        assert "meta" in result
        assert "profile" in result["meta"]
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationdispense" in result["meta"]["profile"]

    def test_required_elements_present(self):
        """Test all US Core required elements are present."""
        dispense = create_minimal_dispense()

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        # US Core SHALL elements
        assert "status" in result
        assert "medicationCodeableConcept" in result or "medicationReference" in result
        assert "subject" in result


class TestMedicationDispenseValidation:
    """Test validation and error handling."""

    def test_missing_product_raises_error(self):
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

        converter = MedicationDispenseConverter()

        with pytest.raises(ValueError, match="product"):
            converter.convert(dispense)

    def test_invalid_mood_code_raises_error(self):
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

        converter = MedicationDispenseConverter()

        with pytest.raises(ValueError, match="moodCode"):
            converter.convert(dispense)

    def test_completed_without_when_handed_over_sets_unknown(self):
        """Test US Core constraint: completed status requires whenHandedOver."""
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

        converter = MedicationDispenseConverter()
        result = converter.convert(dispense)

        # Should adjust status to 'unknown' per US Core constraint
        assert result["status"] == "unknown"
        assert "whenHandedOver" not in result


class TestMedicationDispenseWithRegistry:
    """Integration tests with ReferenceRegistry."""

    def test_context_populated_when_encounter_registered(self):
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

    def test_context_not_populated_when_no_encounter(self):
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

    def test_subject_uses_registry_patient(self):
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

    def test_location_created_when_represented_organization_present(self):
        """Test Location resource created for representedOrganization."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.ccda.models.datatypes import AD, TEL
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

    def test_location_not_created_without_represented_organization(self):
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

    def test_location_not_created_without_organization_name(self):
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

    def test_location_not_created_without_registry(self):
        """Test Location not created when no reference registry."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )

        # Create converter WITHOUT registry
        converter = MedicationDispenseConverter()

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

        result = converter.convert(dispense)

        # Should NOT have location reference (no registry to register Location)
        assert "location" not in result

    def test_location_reused_for_same_organization(self):
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

    def test_location_with_multiple_address_lines(self):
        """Test Location address with multiple street lines."""
        from ccda_to_fhir.ccda.models.performer import (
            AssignedPerson,
            RepresentedOrganization,
        )
        from ccda_to_fhir.ccda.models.datatypes import AD
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

    def test_location_with_minimal_organization_info(self):
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
