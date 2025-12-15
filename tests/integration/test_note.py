"""E2E tests for DocumentReference resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

NOTES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.65"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle.

    For DocumentReference resources, specifically finds Note Activity DocumentReferences
    (those with category='clinical-note'), not document-level ones.
    """
    candidates = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            candidates.append(resource)

    if not candidates:
        return None

    # For DocumentReference, prefer Note Activity (has type code 34109-9 for "Note")
    if resource_type == "DocumentReference" and len(candidates) > 1:
        for resource in candidates:
            doc_type = resource.get("type", {})
            coding = doc_type.get("coding", [])
            for code in coding:
                # Note Activity uses LOINC code 34109-9 for "Note"
                if code.get("code") == "34109-9":
                    return resource

    return candidates[0]


class TestNoteConversion:
    """E2E tests for C-CDA Note Activity to FHIR DocumentReference conversion."""

    def test_converts_to_document_reference(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that note activity creates a DocumentReference."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["resourceType"] == "DocumentReference"

    def test_converts_type(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that note code is converted to type."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "type" in doc_ref
        loinc = next(
            (c for c in doc_ref["type"]["coding"]
             if c.get("system") == "http://loinc.org"),
            None
        )
        assert loinc is not None
        assert loinc["code"] == "34109-9"

    def test_converts_translation_codes(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that translation codes are included in type."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        codes = [c["code"] for c in doc_ref["type"]["coding"]]
        assert "11488-4" in codes

    def test_converts_status(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that status is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["status"] == "current"

    def test_converts_category(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that category is set to clinical-note."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert doc_ref["category"][0]["coding"][0]["code"] == "clinical-note"
        assert doc_ref["category"][0]["coding"][0]["system"] == "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category"

    def test_converts_date(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that author time is converted to date."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "date" in doc_ref
        assert "2016-09-08" in doc_ref["date"]

    def test_converts_content_attachment(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that text content is converted to attachment."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "content" in doc_ref
        assert len(doc_ref["content"]) == 1
        assert doc_ref["content"][0]["attachment"]["contentType"] == "application/rtf"
        assert doc_ref["content"][0]["attachment"]["data"] is not None

    def test_converts_context_period(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to context.period."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "context" in doc_ref
        assert "period" in doc_ref["context"]
        assert "2016-09-08" in doc_ref["context"]["period"]["start"]

    def test_type_text_from_display(
        self, ccda_note: str, fhir_note: JSONObject
    ) -> None:
        """Test that type.text is derived from displayName."""
        ccda_doc = wrap_in_ccda_document(ccda_note, NOTES_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "type" in doc_ref
        assert doc_ref["type"]["text"] == "Note"
