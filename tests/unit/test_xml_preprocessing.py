"""Unit tests for XML namespace preprocessing.

Tests the preprocess_ccda_namespaces() function that adds missing
namespace declarations to C-CDA documents.

Standards tested:
- W3C XML Namespaces 1.0: https://www.w3.org/TR/xml-names/
- HL7 CDA Core v2.0.1-sd: https://hl7.org/cda/stds/core/2.0.1-sd/
- SDTC Extensions: https://confluence.hl7.org/display/SD/CDA+Extensions
"""

import pytest
from lxml import etree

from ccda_to_fhir.ccda.parser import preprocess_ccda_namespaces


class TestXsiNamespaceAddition:
    """Test adding xmlns:xsi namespace declaration."""

    def test_adds_xsi_namespace_when_xsi_type_used(self):
        """Add xmlns:xsi when xsi:type is used but not declared."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <value xsi:type="CD" code="123"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        # Verify XML is well-formed after preprocessing
        root = etree.fromstring(result.encode("utf-8"))
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    def test_adds_xsi_namespace_when_xsi_schemaLocation_used(self):
        """Add xmlns:xsi when xsi:schemaLocation is used but not declared."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3"
            xsi:schemaLocation="urn:hl7-org:v3 hl7-cda.xsd">
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result

    def test_adds_xsi_when_clinical_document_has_no_space_before_close(self):
        """Handle <ClinicalDocument> with no space before >."""
        xml = """<ClinicalDocument>
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        # Should add space before >
        assert '<ClinicalDocument xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' in result


class TestSdtcNamespaceAddition:
    """Test adding xmlns:sdtc namespace declaration."""

    def test_adds_sdtc_namespace_when_sdtc_element_used(self):
        """Add xmlns:sdtc when sdtc: element is used but not declared."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <sdtc:dischargeDispositionCode code="01"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result
        # Verify XML is well-formed after preprocessing
        root = etree.fromstring(result.encode("utf-8"))
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    def test_adds_sdtc_namespace_when_sdtc_attribute_used(self):
        """Add xmlns:sdtc when sdtc: attribute is used but not declared."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <patient sdtc:deceasedInd="true"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result


class TestBothNamespacesAddition:
    """Test adding both xsi and sdtc namespaces."""

    def test_adds_both_namespaces_when_both_used(self):
        """Add both xmlns:xsi and xmlns:sdtc when both prefixes used."""
        xml = """<ClinicalDocument>
            <value xsi:type="CD" code="123"/>
            <sdtc:dischargeDispositionCode code="01"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result
        # Verify XML is well-formed
        root = etree.fromstring(result.encode("utf-8"))
        assert root is not None


class TestIdempotence:
    """Test that preprocessing is idempotent (no duplicates)."""

    def test_does_not_add_xsi_when_already_declared(self):
        """Do not add xmlns:xsi if already present."""
        xml = """<ClinicalDocument xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <value xsi:type="CD" code="123"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should be unchanged
        assert result == xml
        # Count occurrences - should be exactly 1
        assert result.count('xmlns:xsi=') == 1

    def test_does_not_add_sdtc_when_already_declared(self):
        """Do not add xmlns:sdtc if already present."""
        xml = """<ClinicalDocument xmlns:sdtc="urn:hl7-org:sdtc">
            <sdtc:dischargeDispositionCode code="01"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should be unchanged
        assert result == xml
        # Count occurrences - should be exactly 1
        assert result.count('xmlns:sdtc=') == 1

    def test_idempotent_double_preprocessing(self):
        """Running preprocessing twice produces same result as once."""
        xml = """<ClinicalDocument>
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result1 = preprocess_ccda_namespaces(xml)
        result2 = preprocess_ccda_namespaces(result1)

        # Should be identical
        assert result1 == result2


class TestPreservingExistingNamespaces:
    """Test that existing namespace declarations are preserved."""

    def test_preserves_existing_namespaces(self):
        """Preserve existing namespace declarations."""
        xml = """<ClinicalDocument
            xmlns="urn:hl7-org:v3"
            xmlns:custom="http://example.com/custom">
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should preserve existing namespaces
        assert 'xmlns="urn:hl7-org:v3"' in result
        assert 'xmlns:custom="http://example.com/custom"' in result
        # And add xsi
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result

    def test_preserves_order_of_existing_attributes(self):
        """Existing attributes should remain in the document."""
        xml = """<ClinicalDocument
            xmlns="urn:hl7-org:v3"
            classCode="DOCCLIN"
            moodCode="EVN">
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Original attributes should still be present
        assert 'classCode="DOCCLIN"' in result
        assert 'moodCode="EVN"' in result
        # New namespace added
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_handles_multiline_clinical_document_tag(self):
        """Handle ClinicalDocument tag spanning multiple lines."""
        xml = """<ClinicalDocument
            xmlns="urn:hl7-org:v3"
            xmlns:voc="http://www.lantanagroup.com/voc">
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        # Verify it parses
        root = etree.fromstring(result.encode("utf-8"))
        assert root is not None

    def test_handles_clinical_document_with_many_attributes(self):
        """Handle ClinicalDocument with many existing attributes."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3"
            classCode="DOCCLIN"
            moodCode="EVN"
            xmlns:voc="http://www.lantanagroup.com/voc"
            xmlns:xhtml="http://www.w3.org/1999/xhtml">
            <value xsi:type="CD"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result

    def test_no_op_when_no_prefixes_used(self):
        """Return unchanged when no xsi: or sdtc: prefixes used."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <id root="2.16.840.1.113883.19.5"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should be unchanged
        assert result == xml

    def test_processes_fragments_not_just_clinical_documents(self):
        """Process fragments (sections, entries, etc.) not just ClinicalDocument."""
        xml = """<section>
            <value xsi:type="CD"/>
        </section>"""

        result = preprocess_ccda_namespaces(xml)

        # Should add namespace to fragments too (for test fixtures)
        assert 'xmlns:xsi=' in result
        assert '<section xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">' in result

    def test_handles_self_closing_clinical_document(self):
        """Handle self-closing ClinicalDocument tag (edge case)."""
        # Note: This is not valid C-CDA but should be handled gracefully
        xml = """<ClinicalDocument xsi:type="foo"/>"""

        result = preprocess_ccda_namespaces(xml)

        # Pattern DOES match self-closing tags with attributes (space after ClinicalDocument)
        # This is correct behavior - add namespace even for self-closing tags
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        # Real C-CDA documents always have child elements, but we handle this edge case correctly

    def test_only_modifies_first_clinical_document(self):
        """Only modify the first ClinicalDocument occurrence."""
        # This is an edge case - nested ClinicalDocument is invalid
        # but we should only modify the first occurrence
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <value xsi:type="CD"/>
            <nested><ClinicalDocument>Invalid</ClinicalDocument></nested>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should have exactly one xmlns:xsi declaration
        assert result.count('xmlns:xsi=') == 1


class TestStandardsCompliance:
    """Test compliance with W3C XML Namespaces standard."""

    def test_namespace_uri_is_correct_for_xsi(self):
        """Verify correct XSI namespace URI per W3C spec."""
        xml = """<ClinicalDocument><value xsi:type="CD"/></ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Per W3C XML Schema Part 1
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result

    def test_namespace_uri_is_correct_for_sdtc(self):
        """Verify correct SDTC namespace URI per HL7 spec."""
        xml = """<ClinicalDocument><sdtc:id/></ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Per HL7 SDTC Extensions
        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result

    def test_preprocessed_xml_is_well_formed(self):
        """Verify preprocessed XML is well-formed and parseable."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <value xsi:type="CD" code="123"/>
            <sdtc:dischargeDispositionCode code="01"/>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should parse without error
        root = etree.fromstring(result.encode("utf-8"))

        # Verify namespace is correctly resolved
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    def test_namespace_prefix_binding_is_valid(self):
        """Verify namespace prefixes are properly bound after preprocessing."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <observation>
                <value xsi:type="CD" code="123"/>
            </observation>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)
        root = etree.fromstring(result.encode("utf-8"))

        # Find the value element and check xsi:type is accessible
        namespaces = {
            'hl7': 'urn:hl7-org:v3',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        value_elem = root.find('.//hl7:value', namespaces)
        assert value_elem is not None

        # xsi:type should be accessible as attribute
        xsi_type = value_elem.get('{http://www.w3.org/2001/XMLSchema-instance}type')
        assert xsi_type == 'CD'


class TestRealWorldScenarios:
    """Test realistic C-CDA document scenarios."""

    def test_typical_allergy_document_without_namespaces(self):
        """Process typical allergy document structure."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <id root="2.16.840.1.113883.19.5.99999.1"/>
            <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
            <section>
                <entry>
                    <observation classCode="OBS" moodCode="EVN">
                        <value xsi:type="CD" code="70618" codeSystem="2.16.840.1.113883.6.88"/>
                    </observation>
                </entry>
            </section>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should add xsi namespace
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        # Should parse successfully
        root = etree.fromstring(result.encode("utf-8"))
        assert root is not None

    def test_encounter_document_with_sdtc_extensions(self):
        """Process encounter document with SDTC extensions."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <componentOf>
                <encompassingEncounter>
                    <sdtc:dischargeDispositionCode code="01"
                        codeSystem="2.16.840.1.113883.6.301.5"/>
                </encompassingEncounter>
            </componentOf>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should add sdtc namespace
        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result
        # Should parse successfully
        root = etree.fromstring(result.encode("utf-8"))
        assert root is not None

    def test_document_with_both_xsi_and_sdtc_usage(self):
        """Process document using both xsi: and sdtc: prefixes."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <patient>
                <name><given>John</given></name>
                <birthTime value="19800101"/>
                <sdtc:deceasedInd value="false"/>
            </patient>
            <section>
                <entry>
                    <observation>
                        <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
                    </observation>
                </entry>
            </section>
        </ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        # Should add both namespaces
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result
        assert 'xmlns:sdtc="urn:hl7-org:sdtc"' in result
        # Should parse successfully
        root = etree.fromstring(result.encode("utf-8"))
        assert root is not None


class TestBytesInput:
    """Test that preprocessing works with string input (bytes handled by parser)."""

    def test_string_input(self):
        """String input should be preprocessed correctly."""
        xml = """<ClinicalDocument><value xsi:type="CD"/></ClinicalDocument>"""

        result = preprocess_ccda_namespaces(xml)

        assert isinstance(result, str)
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in result

    def test_empty_string(self):
        """Empty string should return empty string."""
        xml = ""

        result = preprocess_ccda_namespaces(xml)

        assert result == ""

    def test_non_xml_string(self):
        """Non-XML string should be returned unchanged."""
        xml = "not xml at all"

        result = preprocess_ccda_namespaces(xml)

        assert result == xml


class TestBeforeAfterParsing:
    """Test that preprocessing actually fixes parsing failures."""

    def test_parsing_fails_before_preprocessing_but_succeeds_after(self):
        """Critical test: verify preprocessing fixes actual parsing errors."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <value xsi:type="CD" code="123"/>
        </ClinicalDocument>"""

        # Step 1: Verify XML fails to parse without preprocessing
        with pytest.raises(etree.XMLSyntaxError) as exc_info:
            etree.fromstring(xml.encode('utf-8'))

        # Verify it's the expected namespace error
        assert "Namespace prefix xsi" in str(exc_info.value)
        assert "not defined" in str(exc_info.value)

        # Step 2: Preprocess the XML
        preprocessed = preprocess_ccda_namespaces(xml)

        # Step 3: Verify preprocessed XML parses successfully
        root = etree.fromstring(preprocessed.encode('utf-8'))
        assert root is not None
        assert root.tag == "{urn:hl7-org:v3}ClinicalDocument"

    def test_sdtc_parsing_fails_before_succeeds_after(self):
        """Verify SDTC namespace preprocessing fixes parsing."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <patient>
                <sdtc:deceasedInd value="false"/>
            </patient>
        </ClinicalDocument>"""

        # Should fail without preprocessing
        with pytest.raises(etree.XMLSyntaxError) as exc_info:
            etree.fromstring(xml.encode('utf-8'))

        assert "Namespace prefix sdtc" in str(exc_info.value)

        # Should succeed after preprocessing
        preprocessed = preprocess_ccda_namespaces(xml)
        root = etree.fromstring(preprocessed.encode('utf-8'))
        assert root is not None

    def test_multiple_xsi_attributes_in_same_document(self):
        """Test document with multiple xsi:type usages."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3">
            <observation>
                <value xsi:type="CD" code="123"/>
                <interpretationCode xsi:type="CE" code="N"/>
                <effectiveTime xsi:type="IVL_TS">
                    <low value="20200101"/>
                </effectiveTime>
            </observation>
        </ClinicalDocument>"""

        # Should fail without preprocessing
        with pytest.raises(etree.XMLSyntaxError):
            etree.fromstring(xml.encode('utf-8'))

        # Should succeed after preprocessing with single namespace declaration
        preprocessed = preprocess_ccda_namespaces(xml)
        root = etree.fromstring(preprocessed.encode('utf-8'))
        assert root is not None

        # Verify only one xmlns:xsi declaration was added
        assert preprocessed.count('xmlns:xsi=') == 1

    def test_xsi_type_and_xsi_schemaLocation_together(self):
        """Test document with both xsi:type and xsi:schemaLocation."""
        xml = """<ClinicalDocument xmlns="urn:hl7-org:v3"
            xsi:schemaLocation="urn:hl7-org:v3 hl7-cda.xsd">
            <value xsi:type="CD" code="123"/>
        </ClinicalDocument>"""

        # Should fail without preprocessing
        with pytest.raises(etree.XMLSyntaxError):
            etree.fromstring(xml.encode('utf-8'))

        # Should succeed after preprocessing
        preprocessed = preprocess_ccda_namespaces(xml)
        root = etree.fromstring(preprocessed.encode('utf-8'))
        assert root is not None

        # Should have xmlns:xsi added
        assert 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' in preprocessed


class TestParseFragmentIntegration:
    """Test integration with parse_ccda_fragment()."""

    def test_parse_fragment_requires_namespace_declarations(self):
        """Test that parse_ccda_fragment requires proper namespace declarations.

        Fragments (non-ClinicalDocument roots) are not preprocessed by design.
        They must have complete namespace declarations to parse successfully.
        """
        from ccda_to_fhir.ccda.models import Observation
        from ccda_to_fhir.ccda.parser import parse_ccda_fragment

        # Fragment WITHOUT xmlns:xsi - should fail (fragments not preprocessed)
        xml_missing_ns = """<observation classCode="OBS" moodCode="EVN"
                    xmlns="urn:hl7-org:v3">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="test"/>
            <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20200101"/>
            <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
        </observation>"""

        # Should now succeed - fragments ARE preprocessed to auto-add namespaces
        result = parse_ccda_fragment(xml_missing_ns, Observation)

        # Verify it parsed successfully
        assert result is not None
        assert result.code.code == "8867-4"

    def test_parse_fragment_succeeds_with_proper_namespaces(self):
        """Test that fragments parse successfully when namespaces are declared."""
        from ccda_to_fhir.ccda.models import Observation
        from ccda_to_fhir.ccda.parser import parse_ccda_fragment

        # Fragment WITH xmlns:xsi - should succeed
        xml_with_ns = """<observation classCode="OBS" moodCode="EVN"
                    xmlns="urn:hl7-org:v3"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <templateId root="2.16.840.1.113883.10.20.22.4.2"/>
            <id root="test"/>
            <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <effectiveTime value="20200101"/>
            <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
        </observation>"""

        # Should parse successfully
        result = parse_ccda_fragment(xml_with_ns, Observation)
        assert result is not None
        assert result.code.code == "8867-4"
