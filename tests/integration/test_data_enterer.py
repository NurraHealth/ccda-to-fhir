"""E2E tests for Data Enterer participation handling.

Per C-CDA on FHIR IG v2.0.0, the DataEntererExtension is a simple extension
with valueReference only (no time or party sub-extensions).

Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-DataEntererExtension.html
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


def _find_all_resources_in_bundle(bundle: JSONObject, resource_type: str) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    resources = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)
    return resources


class TestDataEntererConversion:
    """E2E tests for C-CDA dataEnterer to FHIR Composition extension and Practitioner conversion.

    Per official C-CDA on FHIR IG v2.0.0, the extension is a simple extension with
    valueReference only. The C-CDA dataEnterer/time is intentionally not captured
    in the extension per the official specification.
    """

    def test_data_enterer_extension_presence(self) -> None:
        """Test that dataEnterer creates DataEntererExtension on Composition."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should have extension array
        assert "extension" in composition

        # Find Data Enterer extension (correct URL per official spec)
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None

    def test_data_enterer_extension_is_simple_extension(self) -> None:
        """Test that DataEntererExtension is a simple extension (not complex).

        Per official spec, this is a simple extension with valueReference only,
        not a complex extension with sub-extensions.
        """
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Data Enterer extension
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None

        # Should be simple extension (has valueReference, not extension array)
        assert "valueReference" in data_enterer_ext
        assert "extension" not in data_enterer_ext

    def test_data_enterer_extension_value_reference(self) -> None:
        """Test that DataEntererExtension has valueReference to Practitioner."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Data Enterer extension
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None

        # Verify valueReference structure
        assert "valueReference" in data_enterer_ext
        assert "reference" in data_enterer_ext["valueReference"]
        assert data_enterer_ext["valueReference"]["reference"].startswith("Practitioner/")

    def test_data_enterer_practitioner_created(self) -> None:
        """Test that dataEnterer creates Practitioner resource."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find data enterer practitioner
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")

        # Should have at least the data enterer practitioner (plus default author)
        assert len(practitioners) >= 2

        # Find the data enterer practitioner by NPI identifier
        data_enterer_practitioner = next(
            (p for p in practitioners
             if any(id.get("value") == "9876543210" for id in p.get("identifier", []))),
            None
        )
        assert data_enterer_practitioner is not None

        # Verify name
        assert "name" in data_enterer_practitioner
        assert len(data_enterer_practitioner["name"]) > 0
        name = data_enterer_practitioner["name"][0]
        assert name.get("given") == ["Ellen"]
        assert name.get("family") == "Enter"

    def test_data_enterer_practitioner_npi_identifier(self) -> None:
        """Test that dataEnterer practitioner has NPI identifier."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find data enterer practitioner
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")

        # Find the data enterer practitioner by NPI identifier
        data_enterer_practitioner = next(
            (p for p in practitioners
             if any(id.get("value") == "9876543210" for id in p.get("identifier", []))),
            None
        )
        assert data_enterer_practitioner is not None

        # Verify NPI identifier
        assert "identifier" in data_enterer_practitioner
        npi_identifier = next(
            (id for id in data_enterer_practitioner["identifier"]
             if id.get("system") == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi_identifier is not None
        assert npi_identifier["value"] == "9876543210"

    def test_data_enterer_extension_reference_matches_practitioner(self) -> None:
        """Test that extension valueReference matches created Practitioner ID."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Find Data Enterer extension
        data_enterer_ext = next(
            (ext for ext in composition["extension"]
             if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
            None
        )
        assert data_enterer_ext is not None

        # Get valueReference
        reference = data_enterer_ext["valueReference"]["reference"]

        # Find data enterer practitioner
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        data_enterer_practitioner = next(
            (p for p in practitioners
             if any(id.get("value") == "9876543210" for id in p.get("identifier", []))),
            None
        )
        assert data_enterer_practitioner is not None

        # Verify reference matches
        expected_reference = f"Practitioner/{data_enterer_practitioner['id']}"
        assert reference == expected_reference

    def test_data_enterer_with_address_and_telecom(self) -> None:
        """Test that dataEnterer with address and telecom creates complete Practitioner."""
        ccda_doc = wrap_in_ccda_document(
            "",
            data_enterer="""
            <dataEnterer>
                <time value="20200315120000-0500"/>
                <assignedEntity>
                    <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                    <addr>
                        <streetAddressLine>123 Data Entry Lane</streetAddressLine>
                        <city>Springfield</city>
                        <state>IL</state>
                        <postalCode>62701</postalCode>
                    </addr>
                    <telecom use="WP" value="tel:+1(555)123-4567"/>
                    <assignedPerson>
                        <name>
                            <given>Ellen</given>
                            <family>Enter</family>
                        </name>
                    </assignedPerson>
                </assignedEntity>
            </dataEnterer>
            """
        )
        bundle = convert_document(ccda_doc)["bundle"]

        # Find data enterer practitioner
        practitioners = _find_all_resources_in_bundle(bundle, "Practitioner")
        data_enterer_practitioner = next(
            (p for p in practitioners
             if any(id.get("value") == "9876543210" for id in p.get("identifier", []))),
            None
        )
        assert data_enterer_practitioner is not None

        # Verify address
        assert "address" in data_enterer_practitioner
        assert len(data_enterer_practitioner["address"]) > 0
        address = data_enterer_practitioner["address"][0]
        assert address.get("line") == ["123 Data Entry Lane"]
        assert address.get("city") == "Springfield"
        assert address.get("state") == "IL"
        assert address.get("postalCode") == "62701"

        # Verify telecom
        assert "telecom" in data_enterer_practitioner
        assert len(data_enterer_practitioner["telecom"]) > 0
        telecom = data_enterer_practitioner["telecom"][0]
        assert telecom.get("system") == "phone"
        assert telecom.get("value") == "+1(555)123-4567"
        assert telecom.get("use") == "work"

    def test_no_data_enterer_no_extension(self) -> None:
        """Test that absence of dataEnterer doesn't create extension."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None

        # Should not have Data Enterer extension
        if "extension" in composition:
            data_enterer_ext = next(
                (ext for ext in composition["extension"]
                 if ext.get("url") == "http://hl7.org/fhir/us/ccda/StructureDefinition/DataEntererExtension"),
                None
            )
            assert data_enterer_ext is None
