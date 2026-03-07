"""Integration tests for Coverage conversion.

Tests end-to-end conversion of C-CDA Payers sections to FHIR Coverage
resources, including negative tests for documents without payers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ccda_to_fhir.constants import TemplateIds
from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

DOCUMENTS_DIR = Path(__file__).parent / "fixtures" / "documents"


def _find_resources(bundle: dict[str, Any], resource_type: str) -> list[dict[str, Any]]:
    """Find all resources of a given type in a FHIR Bundle."""
    return [
        entry["resource"]
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == resource_type
    ]


# -- Payers section XML fixture for integration tests --
# NOTE: wrap_in_ccda_document adds the outer <entry> wrapper
PAYERS_SECTION_XML = """
<act classCode="ACT" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.60" extension="2023-05-01"/>
  <templateId root="2.16.840.1.113883.10.20.22.4.60"/>
  <id root="a9b0c1d2-e3f4-5678-9abc-def012345678"/>
  <code code="48768-6" codeSystem="2.16.840.1.113883.6.1"
        codeSystemName="LOINC" displayName="Payment sources"/>
  <statusCode code="completed"/>
  <entryRelationship typeCode="COMP">
    <sequenceNumber value="1"/>
    <act classCode="ACT" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.61" extension="2023-05-01"/>
      <templateId root="2.16.840.1.113883.10.20.22.4.61"/>
      <id root="b1c2d3e4-f5a6-7890-bcde-f01234567890" extension="INS-99887766"/>
      <code code="HIP" codeSystem="2.16.840.1.113883.6.255.1336"
            displayName="Health Insurance Plan Policy"/>
      <statusCode code="completed"/>
      <effectiveTime>
        <low value="20230101"/>
        <high value="20251231"/>
      </effectiveTime>
      <performer typeCode="PRF">
        <templateId root="2.16.840.1.113883.10.20.22.4.87"/>
        <assignedEntity>
          <id root="c2d3e4f5-a6b7-8901-cdef-0123456789ab" extension="BCBS001"/>
          <code code="PAYOR" codeSystem="2.16.840.1.113883.5.110"/>
          <representedOrganization>
            <name>Blue Cross Blue Shield</name>
            <telecom value="tel:+18005551234" use="WP"/>
            <addr use="WP">
              <streetAddressLine>123 Insurance Ave</streetAddressLine>
              <city>Chicago</city>
              <state>IL</state>
              <postalCode>60601</postalCode>
            </addr>
          </representedOrganization>
        </assignedEntity>
      </performer>
      <participant typeCode="COV">
        <templateId root="2.16.840.1.113883.10.20.22.4.89"/>
        <time>
          <low value="20230101"/>
          <high value="20251231"/>
        </time>
        <participantRole>
          <id root="d3e4f5a6-b7c8-9012-def0-123456789abc" extension="MEM-12345"/>
          <code code="SELF" codeSystem="2.16.840.1.113883.5.111"
                displayName="Self"/>
        </participantRole>
      </participant>
      <participant typeCode="HLD">
        <templateId root="2.16.840.1.113883.10.20.22.4.90"/>
        <participantRole>
          <id root="e4f5a6b7-c8d9-0123-ef01-23456789abcd" extension="HLD-54321"/>
        </participantRole>
      </participant>
    </act>
  </entryRelationship>
</act>
"""


class TestCoverageEndToEnd:
    """Test full C-CDA → FHIR conversion of payers section."""

    def test_payers_section_produces_coverage(self) -> None:
        """Payers section with Coverage Activity produces Coverage + Organization."""
        ccda_doc = wrap_in_ccda_document(
            PAYERS_SECTION_XML,
            section_template_id=TemplateIds.PAYERS_SECTION,
            section_code="48768-6",
        )
        bundle = convert_document(ccda_doc)["bundle"]

        coverages = _find_resources(bundle, "Coverage")
        assert len(coverages) == 1

        coverage = coverages[0]
        assert coverage["status"] == "active"
        assert coverage["subscriberId"] == "MEM-12345"
        assert coverage["order"] == 1
        assert coverage["type"]["coding"][0]["code"] == "HIP"
        assert coverage["relationship"]["coding"][0]["code"] == "self"
        assert "subscriber" in coverage
        assert "beneficiary" in coverage
        assert "payor" in coverage
        assert "period" in coverage
        assert "2023" in coverage["period"]["start"]
        assert "2025" in coverage["period"]["end"]
        assert "policyHolder" in coverage

        # Payor organization should exist
        orgs = _find_resources(bundle, "Organization")
        payor_ref = coverage["payor"][0]["reference"]
        payor_org = next(
            (o for o in orgs if f"urn:uuid:{o['id']}" == payor_ref),
            None,
        )
        assert payor_org is not None
        assert "Blue Cross" in payor_org.get("name", "")

    def test_coverage_references_resolve(self) -> None:
        """All Coverage references (beneficiary, payor, subscriber) resolve."""
        ccda_doc = wrap_in_ccda_document(
            PAYERS_SECTION_XML,
            section_template_id=TemplateIds.PAYERS_SECTION,
            section_code="48768-6",
        )
        bundle = convert_document(ccda_doc)["bundle"]

        resources_by_id: dict[str, dict] = {}
        for entry in bundle["entry"]:
            r = entry["resource"]
            if "id" in r:
                resources_by_id[f"urn:uuid:{r['id']}"] = r

        coverage = _find_resources(bundle, "Coverage")[0]

        # beneficiary must resolve to Patient
        assert coverage["beneficiary"]["reference"] in resources_by_id

        # payor must resolve to Organization
        payor_ref = coverage["payor"][0]["reference"]
        assert payor_ref in resources_by_id
        assert resources_by_id[payor_ref]["resourceType"] == "Organization"

        # subscriber (SELF) must resolve to Patient
        assert coverage["subscriber"]["reference"] in resources_by_id

    def test_composition_includes_payers_section(self) -> None:
        """Composition should include a section referencing Coverage resources."""
        ccda_doc = wrap_in_ccda_document(
            PAYERS_SECTION_XML,
            section_template_id=TemplateIds.PAYERS_SECTION,
            section_code="48768-6",
        )
        bundle = convert_document(ccda_doc)["bundle"]

        composition = _find_resources(bundle, "Composition")[0]
        section_entries = []
        for section in composition.get("section", []):
            for entry_ref in section.get("entry", []):
                section_entries.append(entry_ref["reference"])

        coverages = _find_resources(bundle, "Coverage")
        for cov in coverages:
            assert f"urn:uuid:{cov['id']}" in section_entries


class TestNoCoverageWhenPayersAbsent:
    """Test that documents without payers sections produce no Coverage resources."""

    def test_empty_document_no_coverage(self) -> None:
        """Minimal C-CDA document without any sections produces no Coverage."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        coverages = _find_resources(bundle, "Coverage")
        assert len(coverages) == 0, "Empty document should not produce Coverage resources"

    def test_document_with_other_sections_no_coverage(self) -> None:
        """Document with non-payer sections produces no Coverage."""
        # Use a procedure section (simpler XML requirements than allergy)
        procedure_xml = """
        <procedure classCode="PROC" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.14" extension="2014-06-09"/>
            <id root="test-proc-id"/>
            <code code="274025005" codeSystem="2.16.840.1.113883.6.96"
                  displayName="Colonic polypectomy"/>
            <statusCode code="completed"/>
            <effectiveTime value="20230601"/>
        </procedure>
        """
        ccda_doc = wrap_in_ccda_document(
            procedure_xml,
            section_template_id=TemplateIds.PROCEDURES_SECTION,
            section_code="47519-4",
        )
        bundle = convert_document(ccda_doc)["bundle"]

        coverages = _find_resources(bundle, "Coverage")
        assert len(coverages) == 0, "Document without payers section should not produce Coverage"

        # But it should still produce procedure resources
        procedures = _find_resources(bundle, "Procedure")
        assert len(procedures) >= 1

    def test_real_document_without_payers_no_coverage(self) -> None:
        """Real C-CDA documents without payers sections produce no Coverage."""
        # agastha_ccd.xml is known to not have a payers section
        agastha_path = DOCUMENTS_DIR / "agastha_ccd.xml"
        if not agastha_path.exists():
            pytest.skip("agastha_ccd.xml fixture not available")

        ccda_xml = agastha_path.read_text()
        bundle = convert_document(ccda_xml)["bundle"]

        coverages = _find_resources(bundle, "Coverage")
        assert len(coverages) == 0, (
            f"agastha_ccd.xml has no payers section but produced {len(coverages)} Coverage resources"
        )

    def test_empty_payers_section_no_coverage(self) -> None:
        """Payers section with no entries produces no Coverage."""
        # Empty section - no <entry> elements
        ccda_doc = wrap_in_ccda_document(
            "",
            section_template_id=TemplateIds.PAYERS_SECTION,
            section_code="48768-6",
        )
        bundle = convert_document(ccda_doc)["bundle"]

        coverages = _find_resources(bundle, "Coverage")
        assert len(coverages) == 0, "Empty payers section should not produce Coverage"
