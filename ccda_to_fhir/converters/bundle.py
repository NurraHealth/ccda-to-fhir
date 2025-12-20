"""Bundle assembly utilities for converting C-CDA documents to FHIR Bundles."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject


def create_bundle(
    resources: list[JSONObject],
    bundle_type: str = "document",
    bundle_id: str | None = None,
) -> FHIRResourceDict:
    """Create a FHIR Bundle from a list of resources.

    Args:
        resources: List of FHIR resources (as dicts)
        bundle_type: Type of bundle (document, collection, searchset, transaction)
        bundle_id: Optional bundle ID (generated if not provided)

    Returns:
        FHIR Bundle as a dict
    """
    if bundle_id is None:
        from ccda_to_fhir.id_generator import generate_id
        bundle_id = generate_id()

    bundle: JSONObject = {
        "resourceType": "Bundle",
        "id": bundle_id,
        "type": bundle_type,
        "entry": [],
    }

    # Add resources as bundle entries
    for resource in resources:
        entry: JSONObject = {
            "resource": resource,
        }

        # For document bundles, the first entry should have fullUrl with composition
        # For other bundle types, add fullUrl for all resources
        if resource.get("resourceType") and resource.get("id"):
            resource_type = resource["resourceType"]
            resource_id = resource["id"]
            entry["fullUrl"] = f"urn:uuid:{resource_id}"

        bundle["entry"].append(entry)

    return bundle


def create_document_bundle(
    composition: JSONObject,
    resources: list[JSONObject],
    bundle_id: str | None = None,
) -> FHIRResourceDict:
    """Create a FHIR document Bundle with a Composition.

    A document bundle must have a Composition as the first entry,
    followed by all resources referenced by the Composition.

    Args:
        composition: The Composition resource
        resources: List of other FHIR resources
        bundle_id: Optional bundle ID

    Returns:
        FHIR document Bundle as a dict
    """
    # Ensure Composition is first
    all_resources = [composition] + resources

    bundle = create_bundle(all_resources, bundle_type="document", bundle_id=bundle_id)

    # Set timestamp
    import datetime

    bundle["timestamp"] = datetime.datetime.utcnow().isoformat() + "Z"

    return bundle


def create_collection_bundle(
    resources: list[JSONObject],
    bundle_id: str | None = None,
) -> FHIRResourceDict:
    """Create a FHIR collection Bundle.

    A collection bundle is used when converting C-CDA documents without
    creating a full Composition resource.

    Args:
        resources: List of FHIR resources
        bundle_id: Optional bundle ID

    Returns:
        FHIR collection Bundle as a dict
    """
    return create_bundle(resources, bundle_type="collection", bundle_id=bundle_id)
