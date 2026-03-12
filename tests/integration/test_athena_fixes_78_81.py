"""E2E tests for Athena CCD fixes #78, #79, #80, #81.

Validates the four fixes against the real athena_ccd.xml fixture:
- #78: Author name deduplication (family not duplicated in display)
- #79: Encounter display fallback from participant specialty
- #80: Procedure.recorder and Encounter.participant display text
- #81: Diagnosis notes get fallback encounter/date from encompassingEncounter
"""

from __future__ import annotations

from .conftest import convert_athena_bundle, resources_by_type


class TestNameDeduplication:
    """#78: Author name deduplication in display text."""

    def test_no_duplicated_family_in_practitioner_name(self) -> None:
        """Practitioner names should not have duplicated family names.

        The athena_ccd.xml has performers like:
        <given>John Doe, MD</given><family>Doe</family>
        Which should produce "John Doe, MD" not "John Doe, MD Doe".
        """
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        practitioners = by_type.get("Practitioner", [])
        assert len(practitioners) >= 1

        for prac in practitioners:
            if "name" not in prac:
                continue
            for name in prac["name"]:
                text = name.get("text", "")
                family = name.get("family", "")
                given_list = name.get("given", [])
                given_text = " ".join(given_list)

                # If given already contains family, the full text should not
                # repeat it. E.g. "John Doe, MD Doe" would be a bug.
                if family and family.upper() in given_text.upper():
                    if text:
                        # Count occurrences of family name
                        count = text.upper().count(family.upper())
                        assert count <= 1, f"Family name '{family}' duplicated in text '{text}'"

    def test_author_display_not_duplicated(self) -> None:
        """DocumentReference author display should not duplicate family names."""
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        doc_refs = by_type.get("DocumentReference", [])

        for dr in doc_refs:
            for author_ref in dr.get("author", []):
                display = author_ref.get("display", "")
                if not display:
                    continue
                # "John Doe, MD Doe" would be a bug - family appearing twice
                words = display.split()
                # Check no consecutive duplicate words (simple heuristic)
                for i in range(len(words) - 1):
                    if words[i].rstrip(",").upper() == words[i + 1].upper():
                        raise AssertionError(
                            f"Possible duplicated name in author display: '{display}'"
                        )


class TestEncounterDisplayFallback:
    """#79: Encounter display from participant specialty when no code."""

    def test_doc_refs_have_encounter_display(self) -> None:
        """DocumentReferences should have encounter display from participant specialty.

        The athena_ccd.xml has encompassingEncounter without code but with
        encounterParticipant having code displayName="Family Medicine".
        """
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        doc_refs = by_type.get("DocumentReference", [])

        refs_with_display = 0
        for dr in doc_refs:
            context = dr.get("context", {})
            for enc_ref in context.get("encounter", []):
                if "display" in enc_ref:
                    assert enc_ref["display"] == "Family Medicine visit"
                    refs_with_display += 1

        assert refs_with_display >= 1, "Expected at least one encounter ref with fallback display"


class TestRecorderAndParticipantDisplay:
    """#80: Procedure.recorder and Encounter.participant display."""

    def test_encounter_participants_have_display(self) -> None:
        """Encounter.participant.individual should include display."""
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        encounters = by_type.get("Encounter", [])
        assert len(encounters) >= 1

        participants_with_display = 0
        for enc in encounters:
            for participant in enc.get("participant", []):
                individual = participant.get("individual", {})
                if "display" in individual:
                    participants_with_display += 1
                    assert isinstance(individual["display"], str)
                    assert len(individual["display"]) > 0

        assert participants_with_display >= 1, (
            "Expected at least one encounter participant with display"
        )

    def test_procedure_recorder_has_display(self) -> None:
        """Procedure.recorder should include display when practitioner name available."""
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        procedures = by_type.get("Procedure", [])

        recorders_with_display = 0
        for proc in procedures:
            recorder = proc.get("recorder")
            if recorder and "display" in recorder:
                recorders_with_display += 1
                assert isinstance(recorder["display"], str)
                assert len(recorder["display"]) > 0

        # Not all procedures have recorders, so just check at least one has display
        if any(proc.get("recorder") for proc in procedures):
            assert recorders_with_display >= 1, (
                "Expected at least one procedure recorder with display"
            )


class TestDiagnosisNoteFallback:
    """#81: Diagnosis notes get fallback encounter/date."""

    def test_all_diagnosis_notes_have_encounter(self) -> None:
        """All diagnosis notes should have encounter reference (from fallback)."""
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        doc_refs = by_type.get("DocumentReference", [])

        diagnosis_notes = [
            dr for dr in doc_refs if "Diagnosis Note" in str(dr.get("description", ""))
        ]

        if not diagnosis_notes:
            return  # No diagnosis notes in fixture

        notes_without_encounter = []
        for note in diagnosis_notes:
            context = note.get("context", {})
            if not context.get("encounter"):
                notes_without_encounter.append(note.get("description", "unknown"))

        assert len(notes_without_encounter) == 0, (
            f"Diagnosis notes missing encounter reference: {notes_without_encounter}"
        )

    def test_all_diagnosis_notes_have_date(self) -> None:
        """All diagnosis notes should have date (from fallback if needed)."""
        bundle = convert_athena_bundle()
        by_type = resources_by_type(bundle)
        doc_refs = by_type.get("DocumentReference", [])

        diagnosis_notes = [
            dr for dr in doc_refs if "Diagnosis Note" in str(dr.get("description", ""))
        ]

        if not diagnosis_notes:
            return

        notes_without_date = []
        for note in diagnosis_notes:
            if "date" not in note:
                notes_without_date.append(note.get("description", "unknown"))

        assert len(notes_without_date) == 0, f"Diagnosis notes missing date: {notes_without_date}"
