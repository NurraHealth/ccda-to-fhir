"""Test Composition.date fallback when effectiveTime is missing or invalid."""

import datetime

from ccda_to_fhir.convert import convert_document
from fhir.resources.R4B.bundle import Bundle


def test_composition_date_with_valid_effective_time():
    """Test that Composition.date uses effectiveTime when valid."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
        <id root="1.2.3.4.5" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Clinical Document</title>
        <effectiveTime value="20230615120000+0000"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name>
                        <given>John</given>
                        <family>Doe</family>
                    </name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20230615120000+0000"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <assignedPerson>
                    <name>
                        <given>Jane</given>
                        <family>Smith</family>
                    </name>
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
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Composition
    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None
    )

    assert composition is not None
    assert composition.date is not None
    # Should use the effectiveTime from the document
    assert isinstance(composition.date, datetime.datetime)
    assert composition.date.year == 2023
    assert composition.date.month == 6
    assert composition.date.day == 15


def test_composition_date_with_missing_effective_time():
    """Test that Composition.date uses fallback when effectiveTime missing."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <!-- No US Realm Header template since it requires effectiveTime -->
        <id root="1.2.3.4.5" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Clinical Document</title>
        <!-- NO effectiveTime -->
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name>
                        <given>John</given>
                        <family>Doe</family>
                    </name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20230615120000+0000"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <assignedPerson>
                    <name>
                        <given>Jane</given>
                        <family>Smith</family>
                    </name>
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
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Composition
    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None
    )

    assert composition is not None
    assert composition.date is not None
    # Should use current datetime as fallback
    assert isinstance(composition.date, datetime.datetime)
    # Verify it has timezone information
    assert composition.date.tzinfo is not None
    # Should be UTC
    assert composition.date.tzinfo == datetime.timezone.utc


def test_composition_date_with_invalid_effective_time():
    """Test that Composition.date uses fallback when effectiveTime is invalid."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
        <id root="1.2.3.4.5" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Clinical Document</title>
        <!-- Invalid effectiveTime -->
        <effectiveTime value="INVALID_DATE"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name>
                        <given>John</given>
                        <family>Doe</family>
                    </name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20230615120000+0000"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <assignedPerson>
                    <name>
                        <given>Jane</given>
                        <family>Smith</family>
                    </name>
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
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Composition
    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None
    )

    assert composition is not None
    assert composition.date is not None
    # Should use current datetime as fallback
    assert isinstance(composition.date, datetime.datetime)
    # Verify it has timezone information
    assert composition.date.tzinfo is not None
    # Should be UTC
    assert composition.date.tzinfo == datetime.timezone.utc


def test_composition_date_with_null_flavor_effective_time():
    """Test that Composition.date uses fallback when effectiveTime has nullFlavor."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
        <id root="1.2.3.4.5" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
        <title>Clinical Document</title>
        <!-- effectiveTime with nullFlavor -->
        <effectiveTime nullFlavor="UNK"/>
        <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
        <languageCode code="en-US"/>
        <recordTarget>
            <patientRole>
                <id root="1.2.3.4" extension="patient1"/>
                <patient>
                    <name>
                        <given>John</given>
                        <family>Doe</family>
                    </name>
                    <administrativeGenderCode code="M" codeSystem="2.16.840.1.113883.5.1"/>
                    <birthTime value="19800101"/>
                </patient>
            </patientRole>
        </recordTarget>
        <author>
            <time value="20230615120000+0000"/>
            <assignedAuthor>
                <id root="1.2.3.4" extension="author1"/>
                <assignedPerson>
                    <name>
                        <given>Jane</given>
                        <family>Smith</family>
                    </name>
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
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Composition
    composition = next(
        (e.resource for e in bundle.entry if e.resource.get_resource_type() == "Composition"),
        None
    )

    assert composition is not None
    assert composition.date is not None
    # Should use current datetime as fallback
    assert isinstance(composition.date, datetime.datetime)
    # Verify it has timezone information
    assert composition.date.tzinfo is not None
    # Should be UTC
    assert composition.date.tzinfo == datetime.timezone.utc
