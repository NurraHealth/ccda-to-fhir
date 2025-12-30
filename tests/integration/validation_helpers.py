"""Validation helpers for testing FHIR bundle conversion correctness.

Instead of exact JSON matching, these functions validate that the converted
FHIR bundles have the correct structure and content properties.
"""

from __future__ import annotations


def assert_no_placeholder_references(bundle: dict) -> None:
    """Verify no resources reference placeholder IDs.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any placeholder references are found
    """
    placeholders = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Check all reference fields
        refs = _extract_all_references(resource)
        for field_path, ref in refs:
            if "placeholder" in ref.lower():
                placeholders.append(
                    f"{resource_type}/{resource_id} -> {field_path}: {ref}"
                )

    assert not placeholders, (
        f"Found {len(placeholders)} placeholder reference(s):\n" +
        "\n".join(f"  - {p}" for p in placeholders)
    )


def assert_all_references_resolve(bundle: dict) -> None:
    """Verify all references point to resources in the bundle.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any references don't resolve
    """
    # Build set of available resource IDs
    resource_ids = set()
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if "resourceType" in resource and "id" in resource:
            ref = f"{resource['resourceType']}/{resource['id']}"
            resource_ids.add(ref)

    # Check all references resolve
    broken_refs = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        refs = _extract_all_references(resource)
        for field_path, ref in refs:
            # Skip urn: references (bundle-internal)
            if ref.startswith("urn:"):
                continue

            if ref not in resource_ids:
                broken_refs.append(
                    f"{resource_type}/{resource_id} -> {field_path}: {ref}"
                )

    assert not broken_refs, (
        f"Found {len(broken_refs)} broken reference(s):\n" +
        "\n".join(f"  - {r}" for r in broken_refs)
    )


def assert_all_required_fields_present(bundle: dict) -> None:
    """Verify all resources have critical FHIR fields.

    This validates the most critical required fields. Some FHIR fields
    have alternatives (e.g., MedicationStatement can have medicationCodeableConcept
    OR medicationReference), so we check for the most common required ones.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any critical fields are missing
    """
    # Define critical required fields per resource type
    # Note: Some fields have alternatives (checked separately)
    required_fields = {
        "Patient": ["id"],
        "Condition": ["id", "subject"],
        "AllergyIntolerance": ["id", "patient"],
        "MedicationStatement": ["id", "subject", "status"],  # medication* checked separately
        "Procedure": ["id", "subject", "status"],
        "Observation": ["id", "subject", "status"],  # code often missing in organizer obs
        "Composition": ["id", "status", "type", "subject", "date", "title"],
    }

    missing_fields = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        if resource_type in required_fields:
            for field in required_fields[resource_type]:
                if field not in resource:
                    missing_fields.append(
                        f"{resource_type}/{resource_id} missing '{field}'"
                    )

    assert not missing_fields, (
        f"Found {len(missing_fields)} missing required field(s):\n" +
        "\n".join(f"  - {m}" for m in missing_fields)
    )


def assert_no_empty_codes(bundle: dict) -> None:
    """Verify no resources have empty code elements.

    Some resources have alternatives (e.g., MedicationStatement can have
    medicationReference instead of medicationCodeableConcept). This validates
    that critical clinical resources have proper coding.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any empty codes are found
    """
    empty_codes = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Condition, AllergyIntolerance, Procedure always need codes
        if resource_type in ["Condition", "AllergyIntolerance", "Procedure"]:
            code = resource.get("code")

            if not code:
                empty_codes.append(f"{resource_type}/{resource_id} has no code")
            elif code == {}:
                empty_codes.append(f"{resource_type}/{resource_id} has empty code {{}}")
            elif isinstance(code, dict):
                # Check that code has at least 'coding' or 'text'
                if not code.get("coding") and not code.get("text"):
                    empty_codes.append(
                        f"{resource_type}/{resource_id} code has no coding or text"
                    )

        # MedicationStatement needs medication* (CodeableConcept OR Reference)
        elif resource_type == "MedicationStatement":
            has_medication = (
                resource.get("medicationCodeableConcept") or
                resource.get("medicationReference")
            )
            if not has_medication:
                empty_codes.append(
                    f"{resource_type}/{resource_id} has no medication* field"
                )

        # Observations: skip organizer observations (hasMember present)
        # Only validate leaf observations
        elif resource_type == "Observation":
            # Skip organizer observations
            if resource.get("hasMember"):
                continue

            code = resource.get("code")
            if not code or code == {}:
                empty_codes.append(f"{resource_type}/{resource_id} has no/empty code")
            elif isinstance(code, dict):
                if not code.get("coding") and not code.get("text"):
                    empty_codes.append(
                        f"{resource_type}/{resource_id} code has no coding or text"
                    )

    assert not empty_codes, (
        f"Found {len(empty_codes)} empty code(s):\n" +
        "\n".join(f"  - {c}" for c in empty_codes)
    )


def count_resources_by_type(bundle: dict, resource_type: str) -> int:
    """Count resources of a specific type in the bundle.

    Args:
        bundle: FHIR Bundle to count
        resource_type: Resource type to count (e.g., "Condition")

    Returns:
        Number of resources of that type
    """
    count = 0
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            count += 1
    return count


def get_resource_summary(bundle: dict) -> dict[str, int]:
    """Get a summary of resource counts by type.

    Args:
        bundle: FHIR Bundle to summarize

    Returns:
        Dictionary mapping resource type to count
    """
    summary = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        if resource_type:
            summary[resource_type] = summary.get(resource_type, 0) + 1
    return summary


def _extract_all_references(obj: dict | list, path: str = "") -> list[tuple[str, str]]:
    """Recursively extract all reference values from a resource.

    Args:
        obj: Dictionary or list to search
        path: Current path (for error reporting)

    Returns:
        List of (field_path, reference_value) tuples
    """
    refs = []

    if isinstance(obj, dict):
        # Check if this dict is a Reference
        if "reference" in obj and isinstance(obj["reference"], str):
            refs.append((path, obj["reference"]))

        # Recurse into all values
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            refs.extend(_extract_all_references(value, new_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            refs.extend(_extract_all_references(item, new_path))

    return refs


def assert_no_duplicate_section_references(bundle: dict) -> None:
    """Verify Composition sections don't have duplicate entry references.

    Per FHIR spec, each resource should appear once in section entries.
    Duplicates can occur when sections have multiple template IDs and
    resources are mapped to multiple template IDs.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any section has duplicate references
    """
    composition = None
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Composition":
            composition = resource
            break

    if not composition:
        return  # No composition, nothing to check

    duplicate_sections = []

    for section in composition.get("section", []):
        entries = section.get("entry", [])
        if not entries:
            continue

        refs = [e["reference"] for e in entries]
        unique_refs = set(refs)

        if len(refs) != len(unique_refs):
            section_title = section.get("title", "Unknown")
            section_code = section.get("code", {}).get("coding", [{}])[0].get("code", "N/A")
            duplicates = len(refs) - len(unique_refs)

            duplicate_sections.append(
                f"Section '{section_title}' (code: {section_code}): "
                f"{len(refs)} entries, {len(unique_refs)} unique ({duplicates} duplicates)"
            )

    assert not duplicate_sections, (
        f"Found {len(duplicate_sections)} section(s) with duplicate references:\n" +
        "\n".join(f"  - {s}" for s in duplicate_sections)
    )


def assert_valid_fhir_ids(bundle: dict) -> None:
    r"""Verify all resource IDs comply with FHIR R4 specification.

    Per FHIR R4: Resource.id must be:
    - Max 64 characters
    - Only contain: [A-Za-z0-9\-\.]
    - Case sensitive but recommend lowercase for consistency

    References:
    - http://hl7.org/fhir/R4/datatypes.html#id
    - https://www.hl7.org/fhir/R4/resource-definitions.html#Resource.id

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any resource IDs violate FHIR spec
    """
    import re

    invalid_ids = []
    fhir_id_pattern = re.compile(r'^[A-Za-z0-9\-\.]+$')

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType", "Unknown")
        resource_id = resource.get("id")

        if not resource_id:
            # ID is optional in bundles, skip
            continue

        # Check 1: Length <= 64 characters
        if len(resource_id) > 64:
            invalid_ids.append(
                f"{resource_type}/{resource_id}: "
                f"Length {len(resource_id)} exceeds 64-character limit"
            )

        # Check 2: Valid characters only [A-Za-z0-9\-\.]
        if not fhir_id_pattern.match(resource_id):
            invalid_ids.append(
                f"{resource_type}/{resource_id}: "
                f"Contains invalid characters (must match [A-Za-z0-9\\-\\.])"
            )

    assert not invalid_ids, (
        f"Found {len(invalid_ids)} FHIR ID violation(s):\n" +
        "\n".join(f"  - {i}" for i in invalid_ids)
    )


def assert_references_point_to_correct_types(bundle: dict) -> None:
    """Verify references point to correct resource types per FHIR spec.

    For example, Condition.subject must reference Patient or Group, not Practitioner.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any references point to incorrect resource types
    """
    # Build resource index
    resources_by_id = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if "resourceType" in resource and "id" in resource:
            ref = f"{resource['resourceType']}/{resource['id']}"
            resources_by_id[ref] = resource

    # Define expected reference types per FHIR spec
    reference_rules = {
        "Condition.subject": ["Patient", "Group"],
        "Condition.encounter": ["Encounter"],
        "Condition.recorder": ["Practitioner", "PractitionerRole", "Patient", "RelatedPerson"],
        "Condition.asserter": ["Practitioner", "PractitionerRole", "Patient", "RelatedPerson"],
        "AllergyIntolerance.patient": ["Patient"],
        "AllergyIntolerance.encounter": ["Encounter"],
        "AllergyIntolerance.recorder": ["Practitioner", "PractitionerRole", "Patient", "RelatedPerson"],
        "MedicationStatement.subject": ["Patient", "Group"],
        "MedicationStatement.informationSource": ["Practitioner", "PractitionerRole", "Patient", "RelatedPerson", "Organization"],
        "MedicationRequest.subject": ["Patient", "Group"],
        "MedicationRequest.requester": ["Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device"],
        "MedicationRequest.encounter": ["Encounter"],
        "MedicationDispense.subject": ["Patient", "Group"],
        "MedicationDispense.performer.actor": ["Practitioner", "PractitionerRole", "Organization", "Patient", "Device", "RelatedPerson"],
        "MedicationDispense.location": ["Location"],
        "Observation.subject": ["Patient", "Group", "Device", "Location"],
        "Observation.encounter": ["Encounter"],
        "Observation.performer": ["Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "CareTeam"],
        "DiagnosticReport.subject": ["Patient", "Group", "Device", "Location"],
        "DiagnosticReport.encounter": ["Encounter"],
        "DiagnosticReport.performer": ["Practitioner", "PractitionerRole", "Organization", "CareTeam"],
        "Procedure.subject": ["Patient", "Group"],
        "Procedure.encounter": ["Encounter"],
        "Procedure.performer.actor": ["Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device"],
        "Procedure.location": ["Location"],
        "Immunization.patient": ["Patient"],
        "Immunization.encounter": ["Encounter"],
        "Immunization.performer.actor": ["Practitioner", "PractitionerRole", "Organization"],
        "Encounter.subject": ["Patient", "Group"],
        "Encounter.participant.individual": ["Practitioner", "PractitionerRole", "RelatedPerson"],
        "Encounter.location.location": ["Location"],
        "DocumentReference.subject": ["Patient", "Practitioner", "Group", "Device"],
        "Composition.subject": ["Patient", "Practitioner", "Group", "Device"],
        "Composition.author": ["Practitioner", "PractitionerRole", "Device", "Patient", "RelatedPerson", "Organization"],
        "Composition.encounter": ["Encounter"],
        "CareTeam.subject": ["Patient", "Group"],
        "CareTeam.encounter": ["Encounter"],
        "CareTeam.participant.member": ["Practitioner", "PractitionerRole", "RelatedPerson", "Patient", "Organization", "CareTeam"],
        "Location.managingOrganization": ["Organization"],
    }

    type_mismatches = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Check specific reference fields based on rules
        for rule_path, allowed_types in reference_rules.items():
            rule_type, rule_field = rule_path.split(".", 1) if "." in rule_path else (rule_path, None)

            if resource_type != rule_type:
                continue

            # Extract reference value
            ref_value = _get_nested_value(resource, rule_field)

            if not ref_value:
                continue

            # Handle arrays and single references
            refs_to_check = []
            if isinstance(ref_value, list):
                for item in ref_value:
                    if isinstance(item, dict) and "reference" in item:
                        refs_to_check.append(item["reference"])
            elif isinstance(ref_value, dict) and "reference" in ref_value:
                refs_to_check.append(ref_value["reference"])

            # Check each reference
            for ref in refs_to_check:
                # Skip urn: and # references
                if ref.startswith("urn:") or ref.startswith("#"):
                    continue

                # Extract referenced resource type
                if "/" in ref:
                    ref_type = ref.split("/")[0]

                    if ref_type not in allowed_types:
                        type_mismatches.append(
                            f"{resource_type}/{resource_id} -> {rule_field}: {ref} "
                            f"(expected {' or '.join(allowed_types)}, got {ref_type})"
                        )

    assert not type_mismatches, (
        f"Found {len(type_mismatches)} reference type mismatch(es):\n" +
        "\n".join(f"  - {m}" for m in type_mismatches)
    )


def _get_nested_value(obj: dict, path: str) -> any:
    """Get nested value from dict using dot notation.

    Args:
        obj: Dictionary to search
        path: Dot-separated path (e.g., "subject" or "performer.actor")

    Returns:
        Value at path, or None if not found
    """
    if not path:
        return None

    parts = path.split(".")
    current = obj

    for part in parts:
        if not isinstance(current, dict):
            return None
        current = current.get(part)
        if current is None:
            return None

    return current


def assert_valid_code_systems(bundle: dict) -> None:
    """Verify all code.system URIs are valid.

    Per C-CDA on FHIR IG, code systems should use canonical URIs when available,
    and urn:oid: format for unmapped OIDs.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any code systems have invalid URI format
    """
    import re

    # Valid URI patterns per FHIR and C-CDA on FHIR IG:
    # - http://... or https://... (canonical URIs)
    # - urn:oid:... (for unmapped OIDs per C-CDA on FHIR IG)
    # - urn:uuid:... (for temporary/local systems)
    # - urn:ietf:... (for IETF standards like BCP 47 language codes)
    valid_uri_pattern = re.compile(r'^(https?://|urn:(oid|uuid|ietf):)')
    invalid_systems = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Extract all CodeableConcept elements
        codes = _extract_all_codes(resource)

        for code_path, code in codes:
            for coding in code.get("coding", []):
                system = coding.get("system")

                if not system:
                    continue

                # Check if system URI matches valid pattern
                if not valid_uri_pattern.match(system):
                    invalid_systems.append(
                        f"{resource_type}/{resource_id} -> {code_path}: "
                        f"Invalid code system URI '{system}' (must be http://, https://, urn:oid:, urn:uuid:, or urn:ietf:)"
                    )

    assert not invalid_systems, (
        f"Found {len(invalid_systems)} invalid code system URI(s):\n" +
        "\n".join(f"  - {s}" for s in invalid_systems)
    )


def _extract_all_codes(obj: dict | list, path: str = "") -> list[tuple[str, dict]]:
    """Recursively extract all CodeableConcept elements from a resource.

    Args:
        obj: Dictionary or list to search
        path: Current path (for error reporting)

    Returns:
        List of (field_path, CodeableConcept_dict) tuples
    """
    codes = []

    if isinstance(obj, dict):
        # Check if this dict is a CodeableConcept (has 'coding' or 'text')
        if "coding" in obj or ("text" in obj and "reference" not in obj):
            # Likely a CodeableConcept
            if "coding" in obj:
                codes.append((path, obj))

        # Recurse into all values
        for key, value in obj.items():
            # Skip certain non-code fields
            if key in ["id", "resourceType", "reference", "display", "url", "valueString"]:
                continue

            new_path = f"{path}.{key}" if path else key
            codes.extend(_extract_all_codes(value, new_path))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            codes.extend(_extract_all_codes(item, new_path))

    return codes


def assert_chronological_dates(bundle: dict) -> None:
    """Verify dates are chronologically consistent.

    Checks:
    - onset <= abatement (Condition)
    - whenPrepared <= whenHandedOver (MedicationDispense)
    - No future dates in past-tense contexts

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any chronological violations are found
    """
    from datetime import datetime

    violations = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Condition: onset vs abatement
        if resource_type == "Condition":
            onset = resource.get("onsetDateTime")
            abatement = resource.get("abatementDateTime")

            if onset and abatement:
                if onset > abatement:
                    violations.append(
                        f"{resource_type}/{resource_id}: "
                        f"onsetDateTime ({onset}) after abatementDateTime ({abatement})"
                    )

        # MedicationDispense: whenPrepared vs whenHandedOver
        elif resource_type == "MedicationDispense":
            prepared = resource.get("whenPrepared")
            handed_over = resource.get("whenHandedOver")

            if prepared and handed_over:
                if prepared > handed_over:
                    violations.append(
                        f"{resource_type}/{resource_id}: "
                        f"whenPrepared ({prepared}) after whenHandedOver ({handed_over})"
                    )

        # Check for future dates in completed/past status
        if resource_type in ["Condition", "Procedure", "Observation", "Immunization"]:
            status = resource.get("status")
            if status in ["completed", "final", "amended", "corrected"]:
                # Check effective/performed dates
                date_field = None
                if "effectiveDateTime" in resource:
                    date_field = "effectiveDateTime"
                elif "performedDateTime" in resource:
                    date_field = "performedDateTime"
                elif "occurrenceDateTime" in resource:
                    date_field = "occurrenceDateTime"

                if date_field:
                    date_value = resource.get(date_field)
                    if date_value:
                        try:
                            # Parse date and check if future
                            date_obj = datetime.fromisoformat(date_value.replace("Z", "+00:00"))
                            now = datetime.now(date_obj.tzinfo)

                            # Allow small tolerance (1 day) for timezone issues
                            if (date_obj - now).days > 1:
                                violations.append(
                                    f"{resource_type}/{resource_id}: "
                                    f"{date_field} ({date_value}) is in future but status is '{status}'"
                                )
                        except (ValueError, AttributeError):
                            # Invalid date format - will be caught by other validators
                            pass

    assert not violations, (
        f"Found {len(violations)} chronological date violation(s):\n" +
        "\n".join(f"  - {v}" for v in violations)
    )


def assert_us_core_must_support(bundle: dict) -> None:
    """Verify US Core Must Support elements are populated.

    Per US Core: "Must be supported if the data is present in the sending system"

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any Must Support elements are missing
    """
    missing_elements = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # Patient Must Support
        if resource_type == "Patient":
            # All these should be present if we're converting from C-CDA
            if not resource.get("identifier"):
                missing_elements.append(f"Patient/{resource_id}: missing identifier")
            if not resource.get("name"):
                missing_elements.append(f"Patient/{resource_id}: missing name")
            if not resource.get("gender"):
                missing_elements.append(f"Patient/{resource_id}: missing gender")

        # Condition Must Support
        elif resource_type == "Condition":
            if not resource.get("category"):
                missing_elements.append(f"Condition/{resource_id}: missing category")
            # clinicalStatus OR verificationStatus required
            if not resource.get("clinicalStatus") and not resource.get("verificationStatus"):
                missing_elements.append(
                    f"Condition/{resource_id}: missing both clinicalStatus and verificationStatus"
                )

        # AllergyIntolerance Must Support
        elif resource_type == "AllergyIntolerance":
            # clinicalStatus OR verificationStatus required
            if not resource.get("clinicalStatus") and not resource.get("verificationStatus"):
                missing_elements.append(
                    f"AllergyIntolerance/{resource_id}: missing both clinicalStatus and verificationStatus"
                )

        # MedicationRequest Must Support
        elif resource_type == "MedicationRequest":
            if not resource.get("status"):
                missing_elements.append(f"MedicationRequest/{resource_id}: missing status")
            if not resource.get("intent"):
                missing_elements.append(f"MedicationRequest/{resource_id}: missing intent")
            # medication[x] is required
            has_medication = (
                resource.get("medicationCodeableConcept") or
                resource.get("medicationReference")
            )
            if not has_medication:
                missing_elements.append(f"MedicationRequest/{resource_id}: missing medication[x]")

        # MedicationDispense Must Support
        elif resource_type == "MedicationDispense":
            if resource.get("status") == "completed" and not resource.get("whenHandedOver"):
                missing_elements.append(
                    f"MedicationDispense/{resource_id}: missing whenHandedOver (required when status=completed)"
                )

        # Observation Must Support
        elif resource_type == "Observation":
            if not resource.get("category"):
                missing_elements.append(f"Observation/{resource_id}: missing category")
            # US Core STU6.1 constraint us-core-2:
            # value[x] OR dataAbsentReason OR component OR hasMember required
            has_value = any(k.startswith("value") for k in resource.keys())
            has_data_absent = "dataAbsentReason" in resource
            has_component = resource.get("component")
            has_has_member = resource.get("hasMember")

            if not (has_value or has_data_absent or has_component or has_has_member):
                missing_elements.append(
                    f"Observation/{resource_id}: missing value[x], dataAbsentReason, component, and hasMember"
                )

        # Procedure Must Support
        elif resource_type == "Procedure":
            if not resource.get("status"):
                missing_elements.append(f"Procedure/{resource_id}: missing status")
            # performed[x] is Must Support
            # Accept either performedDateTime/performedPeriod OR _performedDateTime extension
            has_performed = any(k.startswith("performed") for k in resource.keys()) or "_performedDateTime" in resource
            if not has_performed:
                missing_elements.append(f"Procedure/{resource_id}: missing performed[x]")

    assert not missing_elements, (
        f"Found {len(missing_elements)} missing US Core Must Support element(s):\n" +
        "\n".join(f"  - {e}" for e in missing_elements)
    )


def assert_fhir_invariants(bundle: dict) -> None:
    """Verify FHIR business rule invariants are satisfied.

    Checks key invariants:
    - obs-6: Observation must have value[x] OR dataAbsentReason OR component
    - con-4: entered-in-error Condition should have minimal data

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any invariants are violated
    """
    violations = []

    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id", "unknown")

        # obs-6: Observation value[x] OR dataAbsentReason OR component OR hasMember
        # Extended by US Core STU6.1 constraint us-core-2 to include hasMember
        if resource_type == "Observation":
            has_value = any(k.startswith("value") for k in resource.keys())
            has_data_absent = "dataAbsentReason" in resource
            has_component = resource.get("component")
            has_has_member = resource.get("hasMember")

            if not (has_value or has_data_absent or has_component or has_has_member):
                violations.append(
                    f"Observation/{resource_id}: obs-6 invariant violation - "
                    "must have value[x] OR dataAbsentReason OR component OR hasMember"
                )

            # Check components also satisfy this rule
            if has_component:
                for i, comp in enumerate(resource.get("component", [])):
                    comp_has_value = any(k.startswith("value") for k in comp.keys())
                    comp_has_absent = "dataAbsentReason" in comp

                    if not (comp_has_value or comp_has_absent):
                        violations.append(
                            f"Observation/{resource_id}: component[{i}] obs-7 invariant violation - "
                            "must have value[x] OR dataAbsentReason"
                        )

        # con-4: entered-in-error Condition minimal data
        elif resource_type == "Condition":
            verification_status = resource.get("verificationStatus", {})
            status_code = None

            for coding in verification_status.get("coding", []):
                if coding.get("code") == "entered-in-error":
                    status_code = "entered-in-error"
                    break

            if status_code == "entered-in-error":
                # Should not have clinicalStatus
                if resource.get("clinicalStatus"):
                    violations.append(
                        f"Condition/{resource_id}: con-3 invariant violation - "
                        "entered-in-error should not have clinicalStatus"
                    )

    assert not violations, (
        f"Found {len(violations)} FHIR invariant violation(s):\n" +
        "\n".join(f"  - {v}" for v in violations)
    )


def assert_composition_sections_valid(bundle: dict) -> None:
    """Verify Composition sections reference correct resource types.

    Checks:
    - Problems section (11450-4) → Condition
    - Allergies section (48765-2) → AllergyIntolerance
    - Medications section (10160-0) → MedicationStatement/MedicationRequest
    - etc.

    Args:
        bundle: FHIR Bundle to validate

    Raises:
        AssertionError: If any sections contain incorrect resource types
    """
    # Build resource index
    resources_by_id = {}
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if "resourceType" in resource and "id" in resource:
            ref = f"{resource['resourceType']}/{resource['id']}"
            resources_by_id[ref] = resource

    # Map section codes to expected resource types
    section_rules = {
        "11450-4": ["Condition"],  # Problems
        "48765-2": ["AllergyIntolerance"],  # Allergies
        "10160-0": ["MedicationStatement", "MedicationRequest", "MedicationDispense", "Medication"],  # Medications
        "47519-4": ["Procedure"],  # Procedures
        "11369-6": ["Immunization"],  # Immunizations
        "8716-3": ["Observation"],  # Vital Signs
        "30954-2": ["DiagnosticReport", "Observation"],  # Results
        "29762-2": ["Observation"],  # Social History
        "46240-8": ["Encounter"],  # Encounters
        "46239-0": ["CareTeam"],  # Care Team
        "61146-7": ["Goal"],  # Goals
    }

    section_violations = []

    # Find Composition
    composition = None
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Composition":
            composition = resource
            break

    if not composition:
        return  # No composition, nothing to check

    for section in composition.get("section", []):
        section_title = section.get("title", "Unknown")

        # Get section code
        section_code = None
        for coding in section.get("code", {}).get("coding", []):
            section_code = coding.get("code")
            if section_code:
                break

        if not section_code or section_code not in section_rules:
            continue

        expected_types = section_rules[section_code]

        for entry_ref in section.get("entry", []):
            ref = entry_ref.get("reference", "")

            # Skip urn: references
            if ref.startswith("urn:") or ref.startswith("#"):
                continue

            if "/" in ref:
                ref_type = ref.split("/")[0]

                if ref_type not in expected_types:
                    section_violations.append(
                        f"Section '{section_title}' (code: {section_code}): "
                        f"references {ref} (expected {' or '.join(expected_types)})"
                    )

    assert not section_violations, (
        f"Found {len(section_violations)} composition section violation(s):\n" +
        "\n".join(f"  - {v}" for v in section_violations)
    )
