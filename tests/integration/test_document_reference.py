"""E2E tests for DocumentReference behavior in converted bundles.

The library does NOT produce a ClinicalDocument-level DocumentReference.
That is the consumer's responsibility (e.g. pointing to a stored copy via URL).

NoteActivity DocumentReferences with legitimately embedded content
(PDFs, images via representation="B64") are tested in test_note.py.
"""

from __future__ import annotations

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject

from .conftest import wrap_in_ccda_document


def _find_all_resources(bundle: JSONObject, resource_type: str) -> list[JSONObject]:
    """Find all resources of the given type in a FHIR Bundle."""
    return [
        entry["resource"]
        for entry in bundle.get("entry", [])
        if entry.get("resource", {}).get("resourceType") == resource_type
    ]


class TestNoClinicalDocumentDocumentReference:
    """Verify the library does not produce a ClinicalDocument-level DocumentReference.

    The ClinicalDocument IS the source document — the library should not
    re-embed it as base64 or create a contentless DocumentReference for it.
    The consumer (e.g. webapp) creates its own DocumentReference pointing
    to wherever it stored the original XML.
    """

    def test_no_document_reference_from_minimal_ccda(self) -> None:
        """Minimal C-CDA should not produce any DocumentReference."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc)["bundle"]

        doc_refs = _find_all_resources(bundle, "DocumentReference")
        assert len(doc_refs) == 0

    def test_no_clinical_document_document_reference_from_real_fixture(self) -> None:
        """Real C-CDA fixture (athena CCD) should not produce a ClinicalDocument DR.

        The athena CCD has a Note Activity entry plus narrative-only clinical
        sections (HPI, PE, ROS, Reason for Visit), so we expect 5 clinical-note
        DocumentReferences but no ClinicalDocument-level one.
        """
        with open("tests/integration/fixtures/documents/athena_ccd.xml") as f:
            xml = f.read()
        bundle = convert_document(xml)["bundle"]

        doc_refs = _find_all_resources(bundle, "DocumentReference")
        # NoteActivity + narrative sections, not ClinicalDocument-level
        assert len(doc_refs) == 5
        # Verify all are clinical-note category, not ClinicalDocument DR
        for dr in doc_refs:
            category_codes = [
                coding.get("code")
                for cat in dr.get("category", [])
                for coding in cat.get("coding", [])
            ]
            assert "clinical-note" in category_codes
