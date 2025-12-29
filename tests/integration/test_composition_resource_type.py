"""Test that Composition objects have resource_type accessible.

Regression test for BUG-001: Composition.resource_type AttributeError
This bug was discovered during stress testing where 104 files (25% of real issues)
failed because the stress test tried to access resource.resource_type which doesn't exist.

The correct way to get the resource type is: resource.get_resource_type()
"""

from pathlib import Path

from ccda_to_fhir import convert_document
from fhir.resources.bundle import Bundle


def test_composition_has_get_resource_type_method():
    """Test that Composition objects have get_resource_type() method."""
    # Use existing working full C-CDA document
    fixture_path = (
        Path(__file__).parent / "fixtures" / "ccda" / "header_and_body_encounter.xml"
    )
    with open(fixture_path) as f:
        xml = f.read()

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Composition resource
    composition_entry = next(
        (e for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None,
    )

    assert composition_entry is not None, "Bundle should contain Composition"
    assert hasattr(
        composition_entry.resource, "get_resource_type"
    ), "Resource should have get_resource_type method"
    assert (
        composition_entry.resource.get_resource_type() == "Composition"
    ), "get_resource_type() should return 'Composition'"


def test_all_fhir_resources_have_get_resource_type():
    """Test that all FHIR resources in bundle have get_resource_type() method."""
    # Use a fixture with multiple resource types
    fixture_path = Path(__file__).parent / "fixtures" / "ccda" / "procedure_with_problem_reference.xml"
    with open(fixture_path) as f:
        xml = f.read()

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # All resources should have get_resource_type() method
    resource_types = set()
    for entry in bundle.entry:
        resource = entry.resource

        # Should have get_resource_type method
        assert hasattr(
            resource, "get_resource_type"
        ), f"Resource {resource.__class__.__name__} should have get_resource_type method"

        # Should return a string
        resource_type = resource.get_resource_type()
        assert isinstance(
            resource_type, str
        ), f"get_resource_type() should return string, got {type(resource_type)}"

        # Should be one of expected types
        assert resource_type in {
            "Patient",
            "Composition",
            "Condition",
            "Organization",
            "Practitioner",
            "PractitionerRole",
            "DocumentReference",
            "AllergyIntolerance",
            "MedicationRequest",
            "Observation",
            "Procedure",
            "Immunization",
            "Encounter",
            "DiagnosticReport",
            "Medication",
            "Device",
            "Location",
            "Provenance",
            "Goal",
            "ServiceRequest",
            "CareTeam",
            "RelatedPerson",
            "MedicationStatement",
        }, f"Unexpected resource type: {resource_type}"

        resource_types.add(resource_type)

    # Should have at least Patient and Composition
    assert "Patient" in resource_types, "Bundle should contain Patient"
    assert "Composition" in resource_types, "Bundle should contain Composition"


def test_resource_type_matches_class_name():
    """Test that get_resource_type() matches the resource class name."""
    fixture_path = Path(__file__).parent / "fixtures" / "ccda" / "encounter_with_problem_reference.xml"
    with open(fixture_path) as f:
        xml = f.read()

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    for entry in bundle.entry:
        resource = entry.resource
        resource_type = resource.get_resource_type()
        class_name = resource.__class__.__name__

        # Resource type should match class name
        assert (
            resource_type == class_name
        ), f"Resource type '{resource_type}' should match class name '{class_name}'"
