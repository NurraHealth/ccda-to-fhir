"""Tests for C-CDA template tracking and metadata.

Verifies that conversion metadata correctly tracks processed and skipped templates.
"""

from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document


class TestTemplateTracking:
    """Tests for template processing metadata."""

    def test_tracks_processed_templates(self) -> None:
        """Test that processed templates are tracked in metadata."""
        # Create a simple C-CDA document with a problem
        ccda_xml = """<act classCode="ACT" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="1.2.3.4.5" extension="problem1"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20200101"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                    <id root="1.2.3.4.5" extension="obs1"/>
                    <code code="55607006" codeSystem="2.16.840.1.113883.6.96" displayName="Problem"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20200101"/>
                    </effectiveTime>
                    <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96" displayName="Hypertension"/>
                </observation>
            </entryRelationship>
        </act>"""

        ccda_doc = wrap_in_ccda_document(ccda_xml, TemplateIds.PROBLEM_SECTION)
        result = convert_document(ccda_doc)

        # Verify result structure
        assert "bundle" in result
        assert "metadata" in result

        # Verify bundle is valid
        bundle = result["bundle"]
        assert bundle["resourceType"] == "Bundle"

        # Verify metadata tracks processed templates
        metadata = result["metadata"]
        assert "processed_templates" in metadata
        assert "skipped_templates" in metadata
        assert "errors" in metadata

        # Should have processed the Problem Concern Act template
        processed = metadata["processed_templates"]
        assert TemplateIds.PROBLEM_CONCERN_ACT in processed
        assert processed[TemplateIds.PROBLEM_CONCERN_ACT]["count"] >= 1
        assert processed[TemplateIds.PROBLEM_CONCERN_ACT]["name"] == "Problem Concern Act"

    def test_tracks_skipped_templates(self) -> None:
        """Test that unsupported templates are tracked as skipped."""
        # Create C-CDA with an unsupported template
        ccda_xml = """<act classCode="ACT" moodCode="EVN">
            <templateId root="9.9.9.9.9.9"/>
            <id root="1.2.3.4.5" extension="unknown1"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
        </act>"""

        ccda_doc = wrap_in_ccda_document(ccda_xml, TemplateIds.PROBLEM_SECTION)
        result = convert_document(ccda_doc)

        metadata = result["metadata"]
        skipped = metadata["skipped_templates"]

        # The unsupported template should be tracked as skipped
        assert "9.9.9.9.9.9" in skipped
        assert skipped["9.9.9.9.9.9"]["count"] >= 1
        assert skipped["9.9.9.9.9.9"]["template_id"] == "9.9.9.9.9.9"

    def test_metadata_counts_multiple_occurrences(self) -> None:
        """Test that metadata counts multiple occurrences of the same template."""
        # Load a real test file with an allergy
        with open("tests/integration/fixtures/ccda/allergy_with_criticality.xml") as f:
            allergy_xml = f.read()

        ccda_doc = wrap_in_ccda_document(allergy_xml, TemplateIds.ALLERGY_SECTION)
        result = convert_document(ccda_doc)
        metadata = result["metadata"]

        # Should track at least one occurrence of Allergy Concern Act
        processed = metadata["processed_templates"]
        assert TemplateIds.ALLERGY_CONCERN_ACT in processed
        assert processed[TemplateIds.ALLERGY_CONCERN_ACT]["count"] >= 1
        assert processed[TemplateIds.ALLERGY_CONCERN_ACT]["name"] == "Allergy Concern Act"
