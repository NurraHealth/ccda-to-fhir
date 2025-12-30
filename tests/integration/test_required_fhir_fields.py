"""Test that FHIR resources always have required fields populated.

Regression test for BUG-003: Missing required FHIR fields in generated resources.
Tests ensure all required fields per FHIR R4B spec are present even when C-CDA
input is minimal or has missing optional data.
"""

from pathlib import Path

import pytest

from ccda_to_fhir import convert_document
from fhir.resources.bundle import Bundle
from tests.integration.conftest import wrap_in_ccda_document


def test_composition_has_all_required_fields():
    """Test that Composition always has required fields populated.

    Required fields per FHIR Composition:
    - status (1..1)
    - type (1..1)
    - date (1..1)
    - author (1..*)
    - title (1..1)
    """
    # Use minimal C-CDA with potentially missing data
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.2" extension="2015-08-01"/>
        <id root="1.2.3.4" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Clinical Document</title>
        <effectiveTime value="20231201120000+0500"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name><given>John</given><family>Doe</family></name>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20231201"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <assignedPerson>
                    <name><given>Dr. Jane</given><family>Smith</family></name>
                </assignedPerson>
            </assignedAuthor>
        </author>
        <custodian>
            <assignedCustodian>
                <representedCustodianOrganization>
                    <id root="1.2.3.4" extension="org1"/>
                    <name>Test Hospital</name>
                </representedCustodianOrganization>
            </assignedCustodian>
        </custodian>
        <component>
            <structuredBody>
                <component>
                    <section>
                        <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Problems</title>
                        <text>No known problems</text>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)  # Should not raise validation error

    # Find Composition resource
    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None,
    )

    assert composition is not None, "Bundle should contain Composition"

    # Required fields per FHIR Composition
    assert composition.status is not None, "Composition.status is required"
    assert composition.type is not None, "Composition.type is required"
    assert composition.date is not None, "Composition.date is required"
    assert composition.author is not None, "Composition.author is required"
    assert len(composition.author) > 0, "Composition.author must have at least one entry"
    assert composition.title is not None, "Composition.title is required"


def test_composition_with_missing_author_person():
    """Test Composition creation when author has no assignedPerson.

    Ensures converter uses "Unknown Author" fallback when author lacks
    assignedPerson element.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Document</title>
        <effectiveTime value="20231201"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name><given>John</given><family>Doe</family></name>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20231201"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <!-- No assignedPerson - converter should use "Unknown Author" -->
            </assignedAuthor>
        </author>
        <custodian>
            <assignedCustodian>
                <representedCustodianOrganization>
                    <id root="1.2.3.4"/>
                    <name>Test Hospital</name>
                </representedCustodianOrganization>
            </assignedCustodian>
        </custodian>
        <component>
            <structuredBody></structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None,
    )

    # Should still have all required fields with defaults
    assert composition.status is not None
    assert composition.type is not None
    assert composition.date is not None
    assert composition.author is not None
    assert len(composition.author) > 0  # Should have fallback author
    assert composition.title is not None


def test_diagnostic_report_has_required_fields(ccda_result):
    """Test that DiagnosticReport always has required fields.

    Required fields per FHIR DiagnosticReport:
    - status (1..1)
    - code (1..1)
    - subject (1..1)
    """
    # Wrap the result organizer fragment in a full C-CDA document
    xml = wrap_in_ccda_document(
        ccda_result,
        section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
        section_code="30954-2"
    )

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find DiagnosticReport resource
    diagnostic_report = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "DiagnosticReport"),
        None,
    )

    if diagnostic_report:  # Only test if DiagnosticReport was created
        # Required fields per FHIR DiagnosticReport
        assert diagnostic_report.status is not None, "DiagnosticReport.status is required"
        assert diagnostic_report.code is not None, "DiagnosticReport.code is required"
        assert diagnostic_report.subject is not None, "DiagnosticReport.subject is required"


def test_diagnostic_report_with_minimal_organizer():
    """Test DiagnosticReport creation with minimal C-CDA Result Organizer.

    This test ensures the converter handles Result Organizers that have minimal
    data and either creates a valid DiagnosticReport with all required fields
    or raises a clear error.
    """
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
        <title>Clinical Document</title>
        <effectiveTime value="20231201"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name><given>John</given><family>Doe</family></name>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20231201"/>
            <assignedAuthor>
                <id root="1.2.3.4"/>
                <assignedPerson>
                    <name><given>Dr.</given><family>Smith</family></name>
                </assignedPerson>
            </assignedAuthor>
        </author>
        <custodian>
            <assignedCustodian>
                <representedCustodianOrganization>
                    <id root="1.2.3.4"/>
                    <name>Test Hospital</name>
                </representedCustodianOrganization>
            </assignedCustodian>
        </custodian>
        <component>
            <structuredBody>
                <component>
                    <section>
                        <templateId root="2.16.840.1.113883.10.20.22.2.3.1"/>
                        <code code="30954-2" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Results</title>
                        <text>Test results</text>
                        <entry>
                            <organizer classCode="BATTERY" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.1"/>
                                <id root="1.2.3.4" extension="organizer1"/>
                                <code code="43789-2" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="CBC W Auto Differential panel"/>
                                <statusCode code="completed"/>
                                <component>
                                    <observation classCode="OBS" moodCode="EVN">
                                        <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                        <id root="1.2.3.4" extension="obs1"/>
                                        <code code="718-7" codeSystem="2.16.840.1.113883.6.1"
                                              displayName="Hemoglobin"/>
                                        <statusCode code="completed"/>
                                        <effectiveTime value="20231201"/>
                                        <value xsi:type="PQ" value="13.5" unit="g/dL"
                                               xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"/>
                                    </observation>
                                </component>
                            </organizer>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find DiagnosticReport
    diagnostic_report = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "DiagnosticReport"),
        None,
    )

    # Should have created DiagnosticReport with all required fields
    assert diagnostic_report is not None, "Should create DiagnosticReport from Result Organizer"
    assert diagnostic_report.status is not None
    assert diagnostic_report.code is not None  # This is the critical test for BUG-003
    assert diagnostic_report.subject is not None


def test_observation_has_required_fields(ccda_result):
    """Test that Observation always has required fields.

    Required fields per FHIR Observation:
    - status (1..1)
    - code (1..1)
    - subject (1..1)
    """
    # Wrap the result organizer fragment in a full C-CDA document
    xml = wrap_in_ccda_document(
        ccda_result,
        section_template_id="2.16.840.1.113883.10.20.22.2.3.1",
        section_code="30954-2"
    )

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Observation resources
    observations = [
        e.resource for e in bundle.entry if e.resource.get_resource_type() == "Observation"
    ]

    assert len(observations) > 0, "Should have at least one Observation"

    for obs in observations:
        # Required fields per FHIR Observation
        assert obs.status is not None, "Observation.status is required"
        assert obs.code is not None, "Observation.code is required"
        assert obs.subject is not None, "Observation.subject is required"


def test_observation_with_missing_code_raises_error():
    """Test that Observation with missing code raises clear error at parse time.

    When an observation lacks a required code element, the C-CDA parser should
    raise a MalformedXMLError during parsing, preventing invalid data from
    reaching the FHIR converter.
    """
    from ccda_to_fhir.ccda.parser import MalformedXMLError

    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
        <title>Clinical Document</title>
        <effectiveTime value="20231201"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name><given>John</given><family>Doe</family></name>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20231201"/>
            <assignedAuthor>
                <id root="1.2.3.4"/>
                <assignedPerson>
                    <name><given>Dr.</given><family>Smith</family></name>
                </assignedPerson>
            </assignedAuthor>
        </author>
        <custodian>
            <assignedCustodian>
                <representedCustodianOrganization>
                    <id root="1.2.3.4"/>
                    <name>Test Hospital</name>
                </representedCustodianOrganization>
            </assignedCustodian>
        </custodian>
        <component>
            <structuredBody>
                <component>
                    <section>
                        <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                        <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Social History</title>
                        <text>Social history observations</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <!-- Missing code - should raise parse error -->
                                <statusCode code="completed"/>
                                <effectiveTime value="20231201"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    # Should raise MalformedXMLError for missing code (caught at parse time)
    with pytest.raises(MalformedXMLError, match="code"):
        convert_document(xml)


def test_all_resources_in_bundle_are_valid():
    """Test that all resources in a converted bundle are valid FHIR resources.

    This is a comprehensive test that validates the entire bundle can be
    successfully parsed by fhir.resources, ensuring all required fields
    are present across all resource types.
    """
    # Use a comprehensive fixture
    fixture_path = Path(__file__).parent / "fixtures" / "ccda" / "header_and_body_encounter.xml"
    with open(fixture_path) as f:
        xml = f.read()

    bundle_dict = convert_document(xml)["bundle"]

    # This should not raise any validation errors
    bundle = Bundle(**bundle_dict)

    # Verify bundle has entries
    assert bundle.entry is not None
    assert len(bundle.entry) > 0

    # Verify each resource has required resourceType
    for entry in bundle.entry:
        assert entry.resource is not None
        resource_type = entry.resource.get_resource_type()
        assert resource_type is not None
        assert isinstance(resource_type, str)
        assert len(resource_type) > 0
