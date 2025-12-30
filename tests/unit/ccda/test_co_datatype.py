"""Unit tests for CO (Coded Ordinal) data type parsing.

Tests the parsing and handling of CO (Coded Ordinal) data type,
which extends CE with ordering semantics.
"""


from ccda_to_fhir.ccda.models import CO
from ccda_to_fhir.ccda.parser import parse_ccda


def test_co_model_creation():
    """Test that CO model can be created directly."""
    co = CO(
        code="LA6752-5",
        code_system="2.16.840.1.113883.6.1",
        code_system_name="LOINC",
        display_name="Mild",
    )

    assert co.code == "LA6752-5"
    assert co.code_system == "2.16.840.1.113883.6.1"
    assert co.code_system_name == "LOINC"
    assert co.display_name == "Mild"


def test_co_inherits_from_ce():
    """Test that CO properly inherits from CE."""
    from ccda_to_fhir.ccda.models import CE

    co = CO(code="LA6752-5", code_system="2.16.840.1.113883.6.1")

    # CO should be an instance of CE (and CD)
    assert isinstance(co, CE)


def test_parse_co_in_observation_value():
    """Test parsing CO data type in observation value element."""
    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
        <title>Test Document</title>
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
                        <code code="8716-3" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Vital Signs</title>
                        <text>Severity assessment</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <code code="55284-4" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="Severity assessment"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230101"/>
                                <value xsi:type="CO" code="LA6752-5"
                                       codeSystem="2.16.840.1.113883.6.1"
                                       codeSystemName="LOINC"
                                       displayName="Mild"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    # Parse the document
    doc = parse_ccda(xml_string)

    # Navigate to the observation
    assert doc.component is not None
    assert doc.component.structured_body is not None
    assert len(doc.component.structured_body.component) > 0

    section = doc.component.structured_body.component[0].section
    assert section is not None
    assert len(section.entry) > 0

    observation = section.entry[0].observation
    assert observation is not None

    # Check the value is CO type
    assert observation.value is not None
    assert isinstance(observation.value, CO)
    assert observation.value.code == "LA6752-5"
    assert observation.value.code_system == "2.16.840.1.113883.6.1"
    assert observation.value.code_system_name == "LOINC"
    assert observation.value.display_name == "Mild"


def test_co_with_translation():
    """Test CO data type with translation elements."""
    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
        <title>Test Document</title>
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
                        <code code="8716-3" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Vital Signs</title>
                        <text>Stage assessment</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <code code="21908-9" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="Stage group"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230101"/>
                                <value xsi:type="CO" code="258215001"
                                       codeSystem="2.16.840.1.113883.6.96"
                                       displayName="Stage 2">
                                    <translation code="LA6754-1"
                                                 codeSystem="2.16.840.1.113883.6.1"
                                                 displayName="Stage II"/>
                                </value>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    doc = parse_ccda(xml_string)

    # Navigate to the observation
    section = doc.component.structured_body.component[0].section
    observation = section.entry[0].observation

    # Check the value is CO with translation
    assert isinstance(observation.value, CO)
    assert observation.value.code == "258215001"
    assert observation.value.display_name == "Stage 2"

    # Check translation
    assert observation.value.translation is not None
    assert len(observation.value.translation) == 1
    assert observation.value.translation[0].code == "LA6754-1"
    assert observation.value.translation[0].display_name == "Stage II"


def test_co_with_null_flavor():
    """Test CO data type with nullFlavor."""
    xml_string = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
        <title>Test Document</title>
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
                        <code code="8716-3" codeSystem="2.16.840.1.113883.6.1"/>
                        <title>Vital Signs</title>
                        <text>Assessment</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <code code="55284-4" codeSystem="2.16.840.1.113883.6.1"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230101"/>
                                <value xsi:type="CO" nullFlavor="UNK"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    doc = parse_ccda(xml_string)

    # Navigate to the observation
    section = doc.component.structured_body.component[0].section
    observation = section.entry[0].observation

    # Check the value is CO with nullFlavor
    assert isinstance(observation.value, CO)
    assert observation.value.null_flavor == "UNK"
    assert observation.value.code is None
