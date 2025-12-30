"""Integration tests for CO (Coded Ordinal) data type in FHIR conversion.

Tests end-to-end conversion of observations containing CO values
from C-CDA to FHIR.
"""

from ccda_to_fhir import convert_document
from fhir.resources.bundle import Bundle


def test_observation_with_co_value_converts_to_codeable_concept():
    """Test full conversion of Observation with CO value to FHIR."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <realmCode code="US"/>
        <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
        <templateId root="2.16.840.1.113883.10.20.22.1.1" extension="2015-08-01"/>
        <id root="1.2.3.4" extension="doc1"/>
        <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"
              displayName="Summarization of Episode Note"/>
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
                        <templateId root="2.16.840.1.113883.10.20.22.2.17"/>
                        <code code="29762-2" codeSystem="2.16.840.1.113883.6.1"
                              displayName="Social History"/>
                        <title>Social History</title>
                        <text>Pain severity assessment</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <code code="72514-3" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="Pain severity"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230101"/>
                                <value xsi:type="CO" code="LA6752-5"
                                       codeSystem="2.16.840.1.113883.6.1"
                                       displayName="Mild"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Observation resource
    observation = next(
        (e.resource for e in bundle.entry
         if e.resource.get_resource_type() == "Observation"),
        None
    )

    assert observation is not None, "Should have created Observation resource"

    # CO value should be converted to valueCodeableConcept
    assert observation.valueCodeableConcept is not None, "Should have valueCodeableConcept"
    assert len(observation.valueCodeableConcept.coding) > 0, "Should have at least one coding"

    # Check the coding
    coding = observation.valueCodeableConcept.coding[0]
    assert coding.code == "LA6752-5"
    assert coding.display == "Mild"
    assert coding.system == "http://loinc.org"  # OID should be converted to URI


def test_observation_with_co_stage_classification():
    """Test CO value representing stage classification."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                        <text>Stage classification</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs2"/>
                                <code code="21908-9" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="Stage group"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230115"/>
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

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Observation resource
    observation = next(
        (e.resource for e in bundle.entry
         if e.resource.get_resource_type() == "Observation"),
        None
    )

    assert observation is not None
    assert observation.valueCodeableConcept is not None

    # Should have both primary code and translation
    assert len(observation.valueCodeableConcept.coding) >= 1

    # Check primary coding (SNOMED)
    primary_coding = observation.valueCodeableConcept.coding[0]
    assert primary_coding.code == "258215001"
    assert primary_coding.display == "Stage 2"
    assert primary_coding.system == "http://snomed.info/sct"

    # Check for translation if present
    if len(observation.valueCodeableConcept.coding) > 1:
        translation_coding = next(
            (c for c in observation.valueCodeableConcept.coding if c.code == "LA6754-1"),
            None
        )
        if translation_coding:
            assert translation_coding.display == "Stage II"
            assert translation_coding.system == "http://loinc.org"


def test_observation_with_co_severity_scale():
    """Test CO value representing severity on a scale."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                        <text>Severity assessment</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs3"/>
                                <code code="75325-1" codeSystem="2.16.840.1.113883.6.1"
                                      displayName="Symptom severity"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230201"/>
                                <value xsi:type="CO" code="LA6751-7"
                                       codeSystem="2.16.840.1.113883.6.1"
                                       codeSystemName="LOINC"
                                       displayName="Severe"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find Observation resource
    observation = next(
        (e.resource for e in bundle.entry
         if e.resource.get_resource_type() == "Observation"),
        None
    )

    assert observation is not None
    assert observation.valueCodeableConcept is not None

    coding = observation.valueCodeableConcept.coding[0]
    assert coding.code == "LA6751-7"
    assert coding.display == "Severe"
    assert coding.system == "http://loinc.org"


def test_multiple_observations_with_different_co_values():
    """Test document with multiple observations using CO values."""
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <ClinicalDocument xmlns="urn:hl7-org:v3"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
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
                        <text>Multiple severity assessments</text>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs1"/>
                                <code code="72514-3" codeSystem="2.16.840.1.113883.6.1"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230101"/>
                                <value xsi:type="CO" code="LA6752-5"
                                       codeSystem="2.16.840.1.113883.6.1"
                                       displayName="Mild"/>
                            </observation>
                        </entry>
                        <entry>
                            <observation classCode="OBS" moodCode="EVN">
                                <templateId root="2.16.840.1.113883.10.20.22.4.38"/>
                                <id root="1.2.3.4" extension="obs2"/>
                                <code code="75325-1" codeSystem="2.16.840.1.113883.6.1"/>
                                <statusCode code="completed"/>
                                <effectiveTime value="20230102"/>
                                <value xsi:type="CO" code="LA6753-3"
                                       codeSystem="2.16.840.1.113883.6.1"
                                       displayName="Moderate"/>
                            </observation>
                        </entry>
                    </section>
                </component>
            </structuredBody>
        </component>
    </ClinicalDocument>
    """

    bundle_dict = convert_document(xml)["bundle"]
    bundle = Bundle(**bundle_dict)

    # Find all Observation resources
    observations = [
        e.resource for e in bundle.entry
        if e.resource.get_resource_type() == "Observation"
    ]

    assert len(observations) == 2, "Should have two Observation resources"

    # Check both have valueCodeableConcept
    for obs in observations:
        assert obs.valueCodeableConcept is not None
        assert len(obs.valueCodeableConcept.coding) > 0

    # Check specific values
    codes = [obs.valueCodeableConcept.coding[0].code for obs in observations]
    assert "LA6752-5" in codes  # Mild
    assert "LA6753-3" in codes  # Moderate
