"""Unit tests for author name deduplication (#78).

Validates that format_person_display deduplicates the family name when
it already appears in the given name (Athena-style names).
"""

from __future__ import annotations

from ccda_to_fhir.ccda.models.datatypes import ENXP, PN, AssignedPerson
from ccda_to_fhir.converters.author_references import (
    _family_in_given,
    format_person_display,
)


class TestFamilyInGiven:
    """Tests for the _family_in_given helper."""

    def test_family_present_case_insensitive(self) -> None:
        assert _family_in_given("Doe", ["John Doe, MD"]) is True

    def test_family_present_uppercase(self) -> None:
        assert _family_in_given("CHENG", ["HENRY CHENG, MD"]) is True

    def test_family_not_present(self) -> None:
        assert _family_in_given("Smith", ["John Doe, MD"]) is False

    def test_empty_given(self) -> None:
        assert _family_in_given("Doe", []) is False

    def test_family_in_multiple_given_parts(self) -> None:
        assert _family_in_given("Doe", ["John", "Doe"]) is True

    def test_short_family_not_substring_matched(self) -> None:
        """'An' should not match 'Diane' — word boundary prevents false positive."""
        assert _family_in_given("An", ["Diane"]) is False

    def test_family_as_word_boundary_match(self) -> None:
        """'An' should match when it appears as a standalone word."""
        assert _family_in_given("An", ["Li An"]) is True


class TestFormatPersonDisplayDeduplication:
    """Tests that format_person_display deduplicates family from given."""

    def test_athena_style_given_contains_family(self) -> None:
        """<given>John Doe, MD</given><family>Doe</family> -> 'John Doe, MD'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="John Doe, MD")],
            family=ENXP(value="Doe"),
        )])
        result = format_person_display(person)
        assert result == "John Doe, MD"

    def test_athena_style_uppercase_family(self) -> None:
        """<given>HENRY CHENG, MD</given><family>Cheng</family> -> 'HENRY CHENG, MD'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="HENRY CHENG, MD")],
            family=ENXP(value="Cheng"),
        )])
        result = format_person_display(person)
        assert result == "HENRY CHENG, MD"

    def test_normal_name_not_deduplicated(self) -> None:
        """<given>Henry</given><family>Doe</family> -> 'Henry Doe'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="Henry")],
            family=ENXP(value="Doe"),
        )])
        result = format_person_display(person)
        assert result == "Henry Doe"

    def test_normal_name_with_suffix(self) -> None:
        """<given>Henry</given><family>Doe</family><suffix>MD</suffix> -> 'Henry Doe MD'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="Henry")],
            family=ENXP(value="Doe"),
            suffix=[ENXP(value="MD")],
        )])
        result = format_person_display(person)
        assert result == "Henry Doe MD"

    def test_given_only(self) -> None:
        """<given>John</given> -> 'John'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="John")],
        )])
        result = format_person_display(person)
        assert result == "John"

    def test_different_family_name_not_in_given(self) -> None:
        """<given>Mary Johnson</given><family>Fonseca</family> -> 'Mary Johnson Fonseca'"""
        person = AssignedPerson(name=[PN(
            given=[ENXP(value="Mary Johnson")],
            family=ENXP(value="Fonseca"),
        )])
        result = format_person_display(person)
        assert result == "Mary Johnson Fonseca"
