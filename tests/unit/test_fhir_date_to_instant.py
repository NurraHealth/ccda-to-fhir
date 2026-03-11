"""Tests for fhir_date_to_instant utility."""

from __future__ import annotations

from ccda_to_fhir.utils import fhir_date_to_instant


class TestFhirDateToInstant:
    def test_none_returns_none(self) -> None:
        assert fhir_date_to_instant(None) is None

    def test_empty_string_returns_none(self) -> None:
        assert fhir_date_to_instant("") is None

    def test_date_only_padded_to_midnight_utc(self) -> None:
        assert fhir_date_to_instant("2026-01-20") == "2026-01-20T00:00:00Z"

    def test_year_month_padded(self) -> None:
        assert fhir_date_to_instant("2026-01") == "2026-01-01T00:00:00Z"

    def test_year_only_padded(self) -> None:
        assert fhir_date_to_instant("2026") == "2026-01-01T00:00:00Z"

    def test_datetime_with_timezone_unchanged(self) -> None:
        assert (
            fhir_date_to_instant("2026-01-20T09:30:00-05:00")
            == "2026-01-20T09:30:00-05:00"
        )

    def test_datetime_utc_unchanged(self) -> None:
        assert (
            fhir_date_to_instant("2026-01-20T00:00:00Z")
            == "2026-01-20T00:00:00Z"
        )

    def test_datetime_without_timezone_gets_utc(self) -> None:
        assert (
            fhir_date_to_instant("2026-01-20T09:30:00")
            == "2026-01-20T09:30:00Z"
        )
