"""Integration tests for Device resources from entry-level authors.

This tests the scenario where devices author clinical entries (procedures, observations, etc.)
rather than just being document-level authors.
"""

from __future__ import annotations

from textwrap import dedent

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str, resource_id: str | None = None) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    if "entry" not in bundle:
        return None

    for entry in bundle["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            if resource_id is None or resource.get("id") == resource_id:
                return resource

    return None


def _find_provenance_by_target(bundle: JSONObject, target_reference: str) -> JSONObject | None:
    """Find a Provenance resource by its target reference."""
    if "entry" not in bundle:
        return None

    for entry in bundle["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == "Provenance":
            targets = resource.get("target", [])
            for target in targets:
                if target.get("reference") == target_reference:
                    return resource

    return None


def _find_all_resources_in_bundle(
    bundle: JSONObject, resource_type: str
) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    if "entry" not in bundle:
        return []

    resources = []
    for entry in bundle["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            resources.append(resource)

    return resources


def _find_device_by_identifier(bundle: JSONObject, identifier_value: str) -> JSONObject | None:
    """Find a Device resource by its identifier value."""
    devices = _find_all_resources_in_bundle(bundle, "Device")
    for device in devices:
        if "identifier" in device:
            for ident in device["identifier"]:
                if ident.get("value") == identifier_value:
                    return device
    return None


class TestDeviceEntryAuthors:
    """Test Device resource creation from entry-level device authors."""

    def test_procedure_with_device_author_creates_device_resource(self) -> None:
        """Test that a device author on a Procedure creates a Device resource in the bundle."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <title>Test Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20200301"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                    <assignedPerson>
                        <name><given>Jane</given><family>Smith</family></name>
                    </assignedPerson>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Procedures</title>
                <text>Procedures section</text>
                <entry>
                    <procedure classCode="PROC" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                        <id root="1.2.3.4.5" extension="proc-1"/>
                        <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20200301"/>
                        <author>
                            <time value="20200302"/>
                            <assignedAuthor>
                                <id root="2.16.840.1.113883.19.5" extension="DEVICE-ROBOT"/>
                                <assignedAuthoringDevice>
                                    <manufacturerModelName>da Vinci Surgical System</manufacturerModelName>
                                    <softwareName>da Vinci Xi</softwareName>
                                </assignedAuthoringDevice>
                            </assignedAuthor>
                        </author>
                    </procedure>
                </entry>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        # Should have a Device resource for the device author
        device = _find_device_by_identifier(bundle, "DEVICE-ROBOT")
        assert device is not None, "Device resource should be created for entry-level device author"

        # Validate ID is UUID v4
        import uuid as uuid_module
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            raise AssertionError(f"Device ID {device['id']} is not a valid UUID v4")

    def test_device_from_entry_has_correct_fields(self) -> None:
        """Test that Device resource from entry-level author has correct fields."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <title>Test Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20200301"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                    <assignedPerson>
                        <name><given>Jane</given><family>Smith</family></name>
                    </assignedPerson>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Procedures</title>
                <text>Procedures section</text>
                <entry>
                    <procedure classCode="PROC" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                        <id root="1.2.3.4.5" extension="proc-1"/>
                        <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20200301"/>
                        <author>
                            <time value="20200302"/>
                            <assignedAuthor>
                                <id root="2.16.840.1.113883.19.5" extension="DEVICE-ROBOT"/>
                                <assignedAuthoringDevice>
                                    <manufacturerModelName>da Vinci Surgical System</manufacturerModelName>
                                    <softwareName>da Vinci Xi</softwareName>
                                </assignedAuthoringDevice>
                            </assignedAuthor>
                        </author>
                    </procedure>
                </entry>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_device_by_identifier(bundle, "DEVICE-ROBOT")
        assert device is not None

        # Validate ID is UUID v4
        import uuid as uuid_module
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            raise AssertionError(f"Device ID {device['id']} is not a valid UUID v4")

        # Check identifier
        assert "identifier" in device
        assert device["identifier"][0]["system"] == "urn:oid:2.16.840.1.113883.19.5"
        assert device["identifier"][0]["value"] == "DEVICE-ROBOT"

        # Check device names
        assert "deviceName" in device
        assert len(device["deviceName"]) == 2

        manufacturer = [d for d in device["deviceName"] if d["type"] == "manufacturer-name"][0]
        assert manufacturer["name"] == "da Vinci Surgical System"

        model = [d for d in device["deviceName"] if d["type"] == "model-name"][0]
        assert model["name"] == "da Vinci Xi"

    def test_provenance_references_device_from_entry(self) -> None:
        """Test that Provenance correctly references the Device created from entry-level author."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <title>Test Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20200301"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                    <assignedPerson>
                        <name><given>Jane</given><family>Smith</family></name>
                    </assignedPerson>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Procedures</title>
                <text>Procedures section</text>
                <entry>
                    <procedure classCode="PROC" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                        <id root="1.2.3.4.5" extension="proc-1"/>
                        <code code="80146002" codeSystem="2.16.840.1.113883.6.96" displayName="Appendectomy"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20200301"/>
                        <author>
                            <time value="20200302"/>
                            <assignedAuthor>
                                <id root="2.16.840.1.113883.19.5" extension="DEVICE-ROBOT"/>
                                <assignedAuthoringDevice>
                                    <manufacturerModelName>da Vinci Surgical System</manufacturerModelName>
                                    <softwareName>da Vinci Xi</softwareName>
                                </assignedAuthoringDevice>
                            </assignedAuthor>
                        </author>
                    </procedure>
                </entry>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        # Check that both Device and Provenance exist
        device = _find_device_by_identifier(bundle, "DEVICE-ROBOT")
        # Find the procedure first to get its ID
        procedure = _find_resource_in_bundle(bundle, "Procedure")
        assert procedure is not None, "Procedure should exist"

        # Find Provenance by target reference (using new ID generation)
        provenance = _find_provenance_by_target(bundle, f"Procedure/{procedure['id']}")

        assert device is not None, "Device should exist"
        assert provenance is not None, "Provenance should exist"

        # Validate device ID is UUID v4
        import uuid as uuid_module
        try:
            uuid_module.UUID(device["id"], version=4)
        except ValueError:
            raise AssertionError(f"Device ID {device['id']} is not a valid UUID v4")

        # Check that Provenance correctly references the Device
        assert "agent" in provenance
        assert len(provenance["agent"]) > 0

        device_agent = [a for a in provenance["agent"] if "Device" in a.get("who", {}).get("reference", "")][0]
        expected_reference = f"Device/{device['id']}"
        assert device_agent["who"]["reference"] == expected_reference

    def test_multiple_entry_device_authors_deduplicated(self) -> None:
        """Test that same device author on multiple entries creates only one Device resource."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <title>Test Document</title>
            <effectiveTime value="20240101120000"/>
            <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
            <languageCode code="en-US"/>

            <recordTarget>
                <patientRole>
                    <id root="1.2.3.4.5" extension="patient-123"/>
                    <patient>
                        <name><given>John</given><family>Doe</family></name>
                        <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                        <birthTime value="19800101"/>
                    </patient>
                </patientRole>
            </recordTarget>

            <author>
                <time value="20200301"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.4.6" extension="999999999"/>
                    <assignedPerson>
                        <name><given>Jane</given><family>Smith</family></name>
                    </assignedPerson>
                </assignedAuthor>
            </author>

            <custodian>
                <assignedCustodian>
                    <representedCustodianOrganization>
                        <id root="1.2.3.4.5" extension="custodian-org"/>
                        <name>Custodian Hospital</name>
                    </representedCustodianOrganization>
                </assignedCustodian>
            </custodian>

            <component><structuredBody><component><section>
                <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Procedures</title>
                <text>Procedures section</text>
                <entry>
                    <procedure classCode="PROC" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                        <id root="1.2.3.4.5" extension="proc-1"/>
                        <code code="80146002" codeSystem="2.16.840.1.113883.6.96"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20200301"/>
                        <author>
                            <time value="20200302"/>
                            <assignedAuthor>
                                <id root="2.16.840.1.113883.19.5" extension="DEVICE-ROBOT"/>
                                <assignedAuthoringDevice>
                                    <manufacturerModelName>da Vinci</manufacturerModelName>
                                    <softwareName>Xi</softwareName>
                                </assignedAuthoringDevice>
                            </assignedAuthor>
                        </author>
                    </procedure>
                </entry>
                <entry>
                    <procedure classCode="PROC" moodCode="EVN">
                        <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
                        <id root="1.2.3.4.5" extension="proc-2"/>
                        <code code="80146002" codeSystem="2.16.840.1.113883.6.96"/>
                        <statusCode code="completed"/>
                        <effectiveTime value="20200303"/>
                        <author>
                            <time value="20200304"/>
                            <assignedAuthor>
                                <id root="2.16.840.1.113883.19.5" extension="DEVICE-ROBOT"/>
                                <assignedAuthoringDevice>
                                    <manufacturerModelName>da Vinci</manufacturerModelName>
                                    <softwareName>Xi</softwareName>
                                </assignedAuthoringDevice>
                            </assignedAuthor>
                        </author>
                    </procedure>
                </entry>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        # Should have exactly 1 Device resource (deduplicated)
        devices = _find_all_resources_in_bundle(bundle, "Device")
        assert len(devices) == 1

        # Validate ID is UUID v4
        import uuid as uuid_module
        try:
            uuid_module.UUID(devices[0]["id"], version=4)
        except ValueError:
            raise AssertionError(f"Device ID {devices[0]['id']} is not a valid UUID v4")

        # Verify it has the correct identifier
        assert "identifier" in devices[0]
        assert devices[0]["identifier"][0]["value"] == "DEVICE-ROBOT"
