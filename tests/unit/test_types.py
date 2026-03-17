"""Tests for FHIR element Pydantic models in types.py."""

from __future__ import annotations

import pytest
from fhir.resources.R4B.reference import Reference
from pydantic import ValidationError

from ccda_to_fhir.types import (
    DiagnosisRole,
    FHIRCodeableConcept,
    FHIRCoding,
    OperationStats,
    ReasonResult,
    RegistryStats,
    ValidationStats,
)

# ============================================================================
# FHIRCoding
# ============================================================================


class TestFHIRCoding:
    def test_system_and_code_required_together(self):
        with pytest.raises(ValueError, match="system and code must both be provided"):
            FHIRCoding(system="http://snomed.info/sct", code=None)

    def test_code_without_system_raises(self):
        with pytest.raises(ValueError, match="system and code must both be provided"):
            FHIRCoding(code="1234")

    def test_display_only_is_valid(self):
        c = FHIRCoding(display="Some display")
        assert c.display == "Some display"
        assert c.system is None
        assert c.code is None

    def test_full_coding(self):
        c = FHIRCoding(system="http://snomed.info/sct", code="1234", display="Test")
        assert c.system == "http://snomed.info/sct"
        assert c.code == "1234"
        assert c.display == "Test"

    def test_to_dict_excludes_none(self):
        c = FHIRCoding(system="http://snomed.info/sct", code="1234")
        d = c.to_dict()
        assert d == {"system": "http://snomed.info/sct", "code": "1234"}
        assert "display" not in d

    def test_to_dict_includes_display(self):
        c = FHIRCoding(system="http://snomed.info/sct", code="1234", display="Test")
        d = c.to_dict()
        assert d == {"system": "http://snomed.info/sct", "code": "1234", "display": "Test"}

    def test_frozen(self):
        c = FHIRCoding(system="http://snomed.info/sct", code="1234")
        with pytest.raises(ValidationError):
            c.code = "5678"

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            FHIRCoding(system="http://snomed.info/sct", code="1234", version="1.0")


# ============================================================================
# FHIRCodeableConcept
# ============================================================================


class TestFHIRCodeableConcept:
    def test_text_only(self):
        cc = FHIRCodeableConcept(text="Free text")
        assert cc.text == "Free text"
        assert cc.coding == []

    def test_to_dict_omits_empty_coding(self):
        cc = FHIRCodeableConcept(text="Free text")
        d = cc.to_dict()
        assert d == {"text": "Free text"}
        assert "coding" not in d

    def test_to_dict_with_codings(self):
        cc = FHIRCodeableConcept(
            coding=[FHIRCoding(system="http://snomed.info/sct", code="1234", display="Test")],
            text="Test",
        )
        d = cc.to_dict()
        assert d == {
            "coding": [{"system": "http://snomed.info/sct", "code": "1234", "display": "Test"}],
            "text": "Test",
        }

    def test_to_dict_no_text(self):
        cc = FHIRCodeableConcept(
            coding=[FHIRCoding(system="http://snomed.info/sct", code="1234")],
        )
        d = cc.to_dict()
        assert d == {"coding": [{"system": "http://snomed.info/sct", "code": "1234"}]}
        assert "text" not in d

    def test_frozen(self):
        cc = FHIRCodeableConcept(text="Test")
        with pytest.raises(ValidationError):
            cc.text = "Changed"


# ============================================================================
# Reference
# ============================================================================


class TestReference:
    """Tests for R4B Reference (replaces hand-rolled FHIRReference)."""

    def test_reference_only(self):
        r = Reference(reference="urn:uuid:abc-123")
        assert r.reference == "urn:uuid:abc-123"
        assert r.display is None

    def test_model_dump_excludes_none_display(self):
        r = Reference(reference="urn:uuid:abc-123")
        d = r.model_dump(exclude_none=True)
        assert d == {"reference": "urn:uuid:abc-123"}
        assert "display" not in d

    def test_model_dump_includes_display(self):
        r = Reference(reference="urn:uuid:abc-123", display="John Smith")
        d = r.model_dump(exclude_none=True)
        assert d == {"reference": "urn:uuid:abc-123", "display": "John Smith"}

    def test_display_only(self):
        r = Reference(display="John Smith")
        d = r.model_dump(exclude_none=True)
        assert d == {"display": "John Smith"}


# ============================================================================
# ReasonResult
# ============================================================================


class TestReasonResult:
    def test_empty_is_falsy(self):
        r = ReasonResult()
        assert not r

    def test_with_codes_is_truthy(self):
        r = ReasonResult(codes=[FHIRCodeableConcept(text="test")])
        assert r

    def test_with_references_is_truthy(self):
        r = ReasonResult(references=[Reference(reference="urn:uuid:123")])
        assert r


# ============================================================================
# DiagnosisRole
# ============================================================================


class TestDiagnosisRole:
    def test_code_and_display_required(self):
        role = DiagnosisRole(code="AD", display="Admission diagnosis")
        assert role.code == "AD"
        assert role.display == "Admission diagnosis"

    def test_frozen(self):
        role = DiagnosisRole(code="AD", display="Admission diagnosis")
        with pytest.raises(ValidationError):
            role.code = "DD"


# ============================================================================
# OperationStats
# ============================================================================


class TestOperationStats:
    def test_zero_valued_is_falsy(self):
        s = OperationStats()
        assert not s

    def test_with_count_is_truthy(self):
        s = OperationStats(count=1, total=0.5, avg=0.5, min_duration=0.5, max_duration=0.5)
        assert s

    def test_frozen(self):
        s = OperationStats()
        with pytest.raises(ValidationError):
            s.count = 1


# ============================================================================
# ValidationStats / RegistryStats (mutable)
# ============================================================================


class TestValidationStats:
    def test_defaults_to_zero(self):
        s = ValidationStats()
        assert s.validated == 0
        assert s.passed == 0
        assert s.failed == 0
        assert s.warnings == 0

    def test_mutable(self):
        s = ValidationStats()
        s.validated += 1
        s.passed += 1
        assert s.validated == 1
        assert s.passed == 1

    def test_model_copy_is_independent(self):
        s = ValidationStats()
        s.validated = 5
        copy = s.model_copy()
        s.validated = 10
        assert copy.validated == 5


class TestRegistryStats:
    def test_defaults_to_zero(self):
        s = RegistryStats()
        assert s.registered == 0
        assert s.resolved == 0
        assert s.failed == 0

    def test_mutable(self):
        s = RegistryStats()
        s.registered += 1
        assert s.registered == 1

    def test_model_copy_is_independent(self):
        s = RegistryStats()
        s.registered = 5
        copy = s.model_copy()
        s.registered = 10
        assert copy.registered == 5
