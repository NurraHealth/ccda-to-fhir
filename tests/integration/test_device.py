"""E2E integration tests for Device resource conversion.

Test-Driven Development (TDD) - Tests written before implementation.
These tests validate end-to-end conversion from C-CDA to FHIR Device.
"""

from __future__ import annotations

from textwrap import dedent

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    if "entry" not in bundle:
        return None

    for entry in bundle["entry"]:
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
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


class TestDeviceConversion:
    """E2E tests for C-CDA device author to FHIR Device conversion."""

    # ============================================================================
    # A. End-to-End Conversion (2 tests)
    # ============================================================================

    def test_creates_device_in_bundle(self) -> None:
        """Test that device author creates a Device resource in the bundle."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert device is not None

    def test_device_has_correct_resource_type(self) -> None:
        """Test that Device resource has correct resourceType."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert device["resourceType"] == "Device"

    # ============================================================================
    # B. Field Mapping Validation (3 tests)
    # ============================================================================

    def test_device_identifier_mapping(self) -> None:
        """Test that C-CDA id maps to Device.identifier with correct system/value."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert "identifier" in device
        assert len(device["identifier"]) == 1
        assert device["identifier"][0]["system"] == "urn:oid:2.16.840.1.113883.19.5"
        assert device["identifier"][0]["value"] == "DEVICE-001"

    def test_device_name_mapping_manufacturer_and_software(self) -> None:
        """Test that both manufacturerModelName and softwareName map to deviceName."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert "deviceName" in device
        assert len(device["deviceName"]) == 2

        # Check manufacturer name
        manufacturer_names = [
            dn for dn in device["deviceName"]
            if dn.get("type") == "manufacturer-name"
        ]
        assert len(manufacturer_names) == 1
        assert manufacturer_names[0]["name"] == "Epic EHR"

        # Check software/model name
        model_names = [
            dn for dn in device["deviceName"]
            if dn.get("type") == "model-name"
        ]
        assert len(model_names) == 1
        assert model_names[0]["name"] == "Epic 2020"

    def test_device_id_generation_stable(self) -> None:
        """Test that same device appears once (deduplication works)."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
                </assignedAuthor>
            </author>

            <author>
                <time value="20200302"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        devices = _find_all_resources_in_bundle(bundle, "Device")
        # Should have only 1 device (deduplicated)
        assert len(devices) == 1

        # Validate device ID is UUID v4
        import uuid as uuid_module
        device_id = devices[0]["id"]
        try:
            uuid_module.UUID(device_id, version=4)
        except ValueError:
            raise AssertionError(f"Device ID {device_id} is not a valid UUID v4")

        # Verify device has correct identifier
        assert "identifier" in devices[0]
        assert devices[0]["identifier"][0]["value"] == "DEVICE-001"

    # ============================================================================
    # C. Composition Integration (2 tests)
    # ============================================================================

    def test_composition_author_includes_device(self) -> None:
        """Test that Composition.author contains device display reference."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition is not None
        assert "author" in composition
        assert len(composition["author"]) == 1
        assert "display" in composition["author"][0]

    def test_composition_author_display_format(self) -> None:
        """Test that device author display has format 'Manufacturer (Software)'."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        composition = _find_resource_in_bundle(bundle, "Composition")
        assert composition["author"][0]["display"] == "Epic EHR (Epic 2020)"

    # ============================================================================
    # D. Edge Cases (1 test)
    # ============================================================================

    def test_device_and_person_author_both_in_bundle(self) -> None:
        """Test document with both human and device authors."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-mixed"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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

            <author>
                <time value="20200301"/>
                <assignedAuthor>
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        # Should have both Practitioner and Device
        practitioner = _find_resource_in_bundle(bundle, "Practitioner")
        device = _find_resource_in_bundle(bundle, "Device")

        assert practitioner is not None
        assert device is not None

        # Composition should have 2 authors
        composition = _find_resource_in_bundle(bundle, "Composition")
        assert len(composition["author"]) == 2

    # ============================================================================
    # E. Type and Version Fields (2 tests)
    # ============================================================================

    def test_device_has_ehr_type_code(self) -> None:
        """Test that EHR Device has SNOMED CT type code 706689003."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Epic EHR</manufacturerModelName>
                        <softwareName>Epic 2020</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert "type" in device
        assert "coding" in device["type"]
        assert len(device["type"]["coding"]) == 1
        assert device["type"]["coding"][0]["system"] == "http://snomed.info/sct"
        assert device["type"]["coding"][0]["code"] == "706689003"
        assert device["type"]["coding"][0]["display"] == "Electronic health record"
        assert device["type"]["text"] == "Electronic Health Record System"

    def test_device_version_extraction_from_software_name(self) -> None:
        """Test that version is extracted from softwareName and has proper structure."""
        ccda_xml = dedent("""<?xml version="1.0" encoding="UTF-8"?>
        <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <realmCode code="US"/>
            <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
            <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
            <id root="1.2.3.4.5" extension="test-doc-device"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1" displayName="Summarization of Episode Note"/>
            <title>C-CDA Document</title>
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
                    <id root="2.16.840.1.113883.19.5" extension="DEVICE-001"/>
                    <assignedAuthoringDevice>
                        <manufacturerModelName>Cerner Millennium</manufacturerModelName>
                        <softwareName>Cerner version 2020.1.5</softwareName>
                    </assignedAuthoringDevice>
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
                <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
                <title>Allergies</title>
                <text>No known allergies</text>
            </section></component></structuredBody></component>
        </ClinicalDocument>""")

        bundle = convert_document(ccda_xml)["bundle"]

        device = _find_resource_in_bundle(bundle, "Device")
        assert "version" in device
        assert len(device["version"]) == 1

        # Verify full CodeableConcept structure for type
        assert "type" in device["version"][0]
        assert "coding" in device["version"][0]["type"]
        assert len(device["version"][0]["type"]["coding"]) == 1
        assert device["version"][0]["type"]["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/device-version-type"
        assert device["version"][0]["type"]["coding"][0]["code"] == "software"
        assert device["version"][0]["type"]["coding"][0]["display"] == "Software Version"
        assert device["version"][0]["type"]["text"] == "software"

        # Verify version value
        assert device["version"][0]["value"] == "2020.1.5"
