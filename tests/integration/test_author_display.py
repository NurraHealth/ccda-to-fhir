"""Integration tests for author reference display text.

Validates that author/performer names propagate to FHIR Reference.display
across the full conversion pipeline.
"""

from __future__ import annotations

from pathlib import Path

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "ccda"

PROBLEMS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.5.1"
ALLERGIES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.6.1"
NOTES_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.65"


def _find_resources(bundle: dict, resource_type: str) -> list[dict]:
    return [
        entry["resource"]
        for entry in bundle["entry"]
        if entry["resource"]["resourceType"] == resource_type
    ]


class TestProblemRecorderDisplay:
    """Condition.recorder should have display from problem author."""

    def test_latest_author_display_on_recorder(self) -> None:
        fixture = (FIXTURES_DIR / "problem_multiple_authors.xml").read_text()
        xml = wrap_in_ccda_document(fixture, PROBLEMS_TEMPLATE_ID)
        result = convert_document(xml)
        conditions = _find_resources(result["bundle"], "Condition")
        assert len(conditions) >= 1
        recorder = conditions[0].get("recorder")
        assert recorder is not None
        assert recorder["display"] == "Latest Documenter"
        assert "urn:uuid:" in recorder["reference"]


class TestAllergyRecorderDisplay:
    """AllergyIntolerance.recorder should have display."""

    def test_author_display_on_recorder(self) -> None:
        fixture = (FIXTURES_DIR / "allergy_multiple_authors.xml").read_text()
        xml = wrap_in_ccda_document(fixture, ALLERGIES_TEMPLATE_ID)
        result = convert_document(xml)
        allergies = _find_resources(result["bundle"], "AllergyIntolerance")
        assert len(allergies) >= 1
        recorder = allergies[0].get("recorder")
        assert recorder is not None
        assert "display" in recorder
        assert "urn:uuid:" in recorder["reference"]


class TestProvenanceAgentDisplay:
    """Provenance.agent.who should have display text."""

    def test_provenance_agent_has_display(self) -> None:
        fixture = (FIXTURES_DIR / "problem_multiple_authors.xml").read_text()
        xml = wrap_in_ccda_document(fixture, PROBLEMS_TEMPLATE_ID)
        result = convert_document(xml)
        provenances = _find_resources(result["bundle"], "Provenance")
        agents_with_display = []
        for prov in provenances:
            for agent in prov.get("agent", []):
                who = agent.get("who", {})
                if who.get("display"):
                    agents_with_display.append(who)
        assert len(agents_with_display) >= 1


class TestDocumentReferenceAuthorDisplay:
    """DocumentReference.author should have display from note activity author."""

    def test_person_author_display(self) -> None:
        fixture = (FIXTURES_DIR / "note.xml").read_text()
        xml = wrap_in_ccda_document(fixture, NOTES_TEMPLATE_ID, section_code="11488-4")
        result = convert_document(xml)
        doc_refs = _find_resources(result["bundle"], "DocumentReference")
        # Filter for Note Activity DocumentReferences (not document-level)
        note_doc_refs = [
            dr
            for dr in doc_refs
            if any(c.get("code") == "34109-9" for c in dr.get("type", {}).get("coding", []))
        ]
        assert len(note_doc_refs) >= 1
        authors = note_doc_refs[0].get("author", [])
        assert len(authors) >= 1
        # The note.xml fixture has author with prefix "Dr." and family "Specialist"
        assert authors[0]["display"] == "Dr. Specialist"
