"""Integration tests for XML namespace preprocessing functionality.

Tests that the preprocessing function successfully fixes malformed C-CDA
documents by adding missing xmlns:xsi namespace declarations.
"""

from lxml import etree

from ccda_to_fhir.ccda.parser import parse_ccda, preprocess_ccda_namespaces


class TestPreprocessingFunctionDirectly:
    """Test preprocessing function directly with real document content."""

    def test_preprocessing_adds_namespace_to_complete_document(self):
        """Test preprocessing with actual complete C-CDA document content."""
        # Create a test document with missing xmlns:xsi
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
    <effectiveTime value="20130607000000-0000"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <patient>
                <name><given>John</given><family>Doe</family></name>
            </patient>
        </patientRole>
    </recordTarget>
    <section>
        <entry>
            <observation>
                <value xsi:type="CD" code="123"/>
            </observation>
        </entry>
    </section>
</ClinicalDocument>"""

        # Verify original is missing namespace
        assert 'xmlns:xsi=' not in xml_string

        # Preprocess
        preprocessed = preprocess_ccda_namespaces(xml_string)

        # Verify namespace was added
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in preprocessed

        # Verify it now parses
        root = etree.fromstring(preprocessed.encode("utf-8"))
        assert root is not None

    def test_preprocessing_is_transparent_for_valid_documents(self):
        """Test that preprocessing doesn't modify already-valid documents."""
        # Create a minimal valid document for testing
        xml_string = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
    <title>Test Document</title>
    <effectiveTime value="20130607000000-0000"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <recordTarget>
        <patientRole>
            <id root="2.16.840.1.113883.19.5" extension="12345"/>
            <patient>
                <name><given>John</given><family>Doe</family></name>
            </patient>
        </patientRole>
    </recordTarget>
</ClinicalDocument>"""

        # Preprocess
        preprocessed = preprocess_ccda_namespaces(xml_string)

        # Should be unchanged (idempotent)
        # Count namespace declarations
        original_xsi_count = xml_string.count('xmlns:xsi=')
        preprocessed_xsi_count = preprocessed.count('xmlns:xsi=')

        assert original_xsi_count == preprocessed_xsi_count == 1

        # Should still parse
        doc = parse_ccda(preprocessed)
        assert doc is not None
        # family is an ENXP object with a value attribute
        assert doc.record_target[0].patient_role.patient.name[0].family.value == "Doe"
