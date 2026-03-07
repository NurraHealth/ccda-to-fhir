"""Unit tests for section_traversal helpers."""

from __future__ import annotations

import logging
from unittest.mock import patch

from ccda_to_fhir.ccda.models.act import Act
from ccda_to_fhir.ccda.models.datatypes import CE, II
from ccda_to_fhir.ccda.models.encounter import Encounter as CDAEncounter
from ccda_to_fhir.ccda.models.observation import Observation
from ccda_to_fhir.ccda.models.organizer import Organizer
from ccda_to_fhir.ccda.models.procedure import Procedure
from ccda_to_fhir.ccda.models.section import (
    Entry,
    Section,
    SectionComponent,
    StructuredBody,
)
from ccda_to_fhir.ccda.models.substance_administration import SubstanceAdministration
from ccda_to_fhir.converters.section_traversal import (
    _has_template,
    _iter_entries,
    _iter_section_tree,
    _iter_sections,
    collect_results,
    converting,
    iter_matching_acts,
    iter_matching_encounters,
    iter_matching_observations,
    iter_matching_organizers,
    iter_matching_procedures,
    iter_matching_substance_administrations,
    scan_skipped_templates,
    track_error,
    track_processed,
    track_skipped,
)
from ccda_to_fhir.types import ConversionMetadata


TEMPLATE_A = "2.16.840.1.113883.10.20.22.4.999"
TEMPLATE_B = "2.16.840.1.113883.10.20.22.4.888"


def _make_ii(root: str) -> II:
    return II(root=root)


def _make_section(
    code: str | None = None,
    entries: list[Entry] | None = None,
    nested: list[Section] | None = None,
) -> Section:
    components = None
    if nested:
        components = [SectionComponent(section=s) for s in nested]
    return Section(
        code=CE(code=code) if code else None,
        entry=entries,
        component=components,
    )


def _make_body(*sections: Section) -> StructuredBody:
    return StructuredBody(
        component=[SectionComponent(section=s) for s in sections]
    )


def _make_metadata() -> ConversionMetadata:
    return {
        "processed_templates": {},
        "skipped_templates": {},
        "errors": [],
    }


# --- _iter_section_tree ---


class TestIterSectionTree:
    def test_single_section(self):
        section = _make_section(code="1234")
        results = list(_iter_section_tree(section))
        assert len(results) == 1
        assert results[0] == (section, "1234")

    def test_section_without_code(self):
        section = _make_section()
        results = list(_iter_section_tree(section))
        assert results[0][1] is None

    def test_nested_sections(self):
        child = _make_section(code="child")
        parent = _make_section(code="parent", nested=[child])
        results = list(_iter_section_tree(parent))
        assert len(results) == 2
        assert results[0] == (parent, "parent")
        assert results[1] == (child, "child")

    def test_deeply_nested(self):
        grandchild = _make_section(code="gc")
        child = _make_section(code="c", nested=[grandchild])
        parent = _make_section(code="p", nested=[child])
        results = list(_iter_section_tree(parent))
        assert len(results) == 3
        codes = [code for _, code in results]
        assert codes == ["p", "c", "gc"]


# --- _iter_sections ---


class TestIterSections:
    def test_empty_body(self):
        body = StructuredBody()
        assert list(_iter_sections(body)) == []

    def test_component_without_section(self):
        body = StructuredBody(component=[SectionComponent()])
        assert list(_iter_sections(body)) == []

    def test_multiple_sections(self):
        s1 = _make_section(code="A")
        s2 = _make_section(code="B")
        body = _make_body(s1, s2)
        results = list(_iter_sections(body))
        assert len(results) == 2

    def test_includes_nested(self):
        child = _make_section(code="child")
        parent = _make_section(code="parent", nested=[child])
        body = _make_body(parent)
        results = list(_iter_sections(body))
        assert len(results) == 2


# --- _iter_entries ---


class TestIterEntries:
    def test_empty_section(self):
        body = _make_body(_make_section())
        assert list(_iter_entries(body)) == []

    def test_yields_entries_with_section_context(self):
        entry = Entry(act=Act(template_id=[_make_ii(TEMPLATE_A)]))
        section = _make_section(code="1234", entries=[entry])
        body = _make_body(section)
        results = list(_iter_entries(body))
        assert len(results) == 1
        e, s, code = results[0]
        assert e is entry
        assert s is section
        assert code == "1234"

    def test_entries_from_nested_sections(self):
        entry_parent = Entry(act=Act())
        entry_child = Entry(observation=Observation())
        child = _make_section(entries=[entry_child])
        parent = _make_section(entries=[entry_parent], nested=[child])
        body = _make_body(parent)
        results = list(_iter_entries(body))
        assert len(results) == 2


# --- _has_template ---


class TestHasTemplate:
    def test_no_template_id(self):
        act = Act()
        assert _has_template(act, TEMPLATE_A) is False

    def test_no_match(self):
        act = Act(template_id=[_make_ii(TEMPLATE_B)])
        assert _has_template(act, TEMPLATE_A) is False

    def test_match(self):
        act = Act(template_id=[_make_ii(TEMPLATE_A)])
        assert _has_template(act, TEMPLATE_A) is True

    def test_match_among_multiple(self):
        act = Act(template_id=[_make_ii(TEMPLATE_B), _make_ii(TEMPLATE_A)])
        assert _has_template(act, TEMPLATE_A) is True


# --- Typed iterator functions ---


class TestIterMatchingActs:
    def test_yields_matching_acts(self):
        act = Act(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        results = list(iter_matching_acts(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is act

    def test_skips_non_matching(self):
        act = Act(template_id=[_make_ii(TEMPLATE_B)])
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        assert list(iter_matching_acts(body, TEMPLATE_A)) == []

    def test_skips_other_entry_types(self):
        obs = Observation(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(observation=obs)]))
        assert list(iter_matching_acts(body, TEMPLATE_A)) == []


class TestIterMatchingObservations:
    def test_yields_matching(self):
        obs = Observation(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(observation=obs)]))
        results = list(iter_matching_observations(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is obs


class TestIterMatchingOrganizers:
    def test_yields_matching(self):
        org = Organizer(classCode="CLUSTER", template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(organizer=org)]))
        results = list(iter_matching_organizers(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is org


class TestIterMatchingProcedures:
    def test_yields_matching(self):
        proc = Procedure(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(procedure=proc)]))
        results = list(iter_matching_procedures(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is proc


class TestIterMatchingEncounters:
    def test_yields_matching(self):
        enc = CDAEncounter(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(_make_section(entries=[Entry(encounter=enc)]))
        results = list(iter_matching_encounters(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is enc


class TestIterMatchingSubstanceAdministrations:
    def test_yields_matching(self):
        sa = SubstanceAdministration(template_id=[_make_ii(TEMPLATE_A)])
        body = _make_body(
            _make_section(entries=[Entry(substance_administration=sa)])
        )
        results = list(iter_matching_substance_administrations(body, TEMPLATE_A))
        assert len(results) == 1
        assert results[0][0] is sa


# --- collect_results ---


class TestCollectResults:
    def test_none_is_noop(self):
        resources: list[dict] = []
        collect_results(resources, None)
        assert resources == []

    def test_single_dict(self):
        resources: list[dict] = []
        collect_results(resources, {"resourceType": "Patient"})
        assert resources == [{"resourceType": "Patient"}]

    def test_list_of_dicts(self):
        resources: list[dict] = []
        collect_results(resources, [{"a": 1}, {"b": 2}])
        assert resources == [{"a": 1}, {"b": 2}]

    def test_tuple_resource_and_pending(self):
        resources: list[dict] = []
        collect_results(resources, ({"main": True}, [{"pending": True}]))
        assert resources == [{"main": True}, {"pending": True}]


# --- converting context manager ---


class TestConverting:
    def test_tracks_processed_on_success(self):
        metadata = _make_metadata()
        with converting(metadata, TEMPLATE_A, None, "test"):
            pass
        assert TEMPLATE_A in metadata["processed_templates"]
        assert metadata["processed_templates"][TEMPLATE_A]["count"] == 1

    def test_tracks_error_on_exception(self):
        metadata = _make_metadata()
        with converting(metadata, TEMPLATE_A, None, "test"):
            raise ValueError("boom")
        assert len(metadata["errors"]) == 1
        assert metadata["errors"][0]["template_id"] == TEMPLATE_A
        assert metadata["errors"][0]["error_type"] == "ValueError"
        assert metadata["errors"][0]["error_message"] == "boom"

    def test_does_not_propagate_exception(self):
        metadata = _make_metadata()
        with converting(metadata, TEMPLATE_A, None, "test"):
            raise RuntimeError("should not propagate")
        # If we get here, exception was swallowed
        assert TEMPLATE_A not in metadata["processed_templates"]

    def test_logs_error(self, caplog):
        metadata = _make_metadata()
        with caplog.at_level(logging.ERROR):
            with converting(metadata, TEMPLATE_A, None, "test thing"):
                raise ValueError("x")
        assert "Error converting test thing" in caplog.text

    def test_none_metadata_skips_tracking(self):
        # Should not raise even with None metadata
        with converting(None, TEMPLATE_A, None, "test"):
            pass

    def test_none_metadata_exception_still_logged(self, caplog):
        with caplog.at_level(logging.ERROR):
            with converting(None, TEMPLATE_A, None, "test thing"):
                raise ValueError("x")
        assert "Error converting test thing" in caplog.text

    def test_tracks_element_ids_in_error(self):
        metadata = _make_metadata()
        ids = [II(root="1.2.3", extension="456")]
        with converting(metadata, TEMPLATE_A, ids, "test"):
            raise ValueError("err")
        assert metadata["errors"][0]["entry_id"] == "1.2.3/456"

    def test_tracks_element_id_without_extension(self):
        metadata = _make_metadata()
        ids = [II(root="1.2.3")]
        with converting(metadata, TEMPLATE_A, ids, "test"):
            raise ValueError("err")
        assert metadata["errors"][0]["entry_id"] == "1.2.3/"


# --- track_processed ---


class TestTrackProcessed:
    def test_first_occurrence(self):
        metadata = _make_metadata()
        track_processed(metadata, TEMPLATE_A)
        assert metadata["processed_templates"][TEMPLATE_A]["count"] == 1

    def test_increments_count(self):
        metadata = _make_metadata()
        track_processed(metadata, TEMPLATE_A)
        track_processed(metadata, TEMPLATE_A)
        assert metadata["processed_templates"][TEMPLATE_A]["count"] == 2


# --- track_skipped ---


class TestTrackSkipped:
    def test_first_occurrence(self):
        metadata = _make_metadata()
        track_skipped(metadata, TEMPLATE_A)
        assert metadata["skipped_templates"][TEMPLATE_A]["count"] == 1

    def test_increments_count(self):
        metadata = _make_metadata()
        track_skipped(metadata, TEMPLATE_A)
        track_skipped(metadata, TEMPLATE_A)
        assert metadata["skipped_templates"][TEMPLATE_A]["count"] == 2


# --- track_error ---


class TestTrackError:
    def test_with_element_ids(self):
        metadata = _make_metadata()
        ids = [II(root="1.2.3", extension="ext")]
        track_error(metadata, TEMPLATE_A, ids, ValueError("fail"))
        assert len(metadata["errors"]) == 1
        err = metadata["errors"][0]
        assert err["template_id"] == TEMPLATE_A
        assert err["entry_id"] == "1.2.3/ext"
        assert err["error_type"] == "ValueError"
        assert err["error_message"] == "fail"

    def test_without_element_ids(self):
        metadata = _make_metadata()
        track_error(metadata, TEMPLATE_A, None, ValueError("fail"))
        assert metadata["errors"][0]["entry_id"] is None

    def test_empty_element_ids(self):
        metadata = _make_metadata()
        track_error(metadata, TEMPLATE_A, [], ValueError("fail"))
        assert metadata["errors"][0]["entry_id"] is None


# --- scan_skipped_templates ---


class TestScanSkippedTemplates:
    def test_tracks_unsupported_templates(self):
        unsupported_oid = "9.9.9.9.9"
        act = Act(template_id=[_make_ii(unsupported_oid)])
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        metadata = _make_metadata()
        scan_skipped_templates(body, metadata)
        assert unsupported_oid in metadata["skipped_templates"]

    def test_skips_supported_templates(self):
        supported_oid = "1.1.1.1.1"
        act = Act(template_id=[_make_ii(supported_oid)])
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        metadata = _make_metadata()
        with patch(
            "ccda_to_fhir.converters.section_traversal.SupportedTemplates.is_supported",
            return_value=True,
        ):
            scan_skipped_templates(body, metadata)
        assert supported_oid not in metadata["skipped_templates"]

    def test_skips_already_processed_templates(self):
        unsupported_oid = "9.9.9.9.9"
        act = Act(template_id=[_make_ii(unsupported_oid)])
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        metadata = _make_metadata()
        # Mark as already processed
        metadata["processed_templates"][unsupported_oid] = {
            "template_id": unsupported_oid,
            "name": None,
            "count": 1,
        }
        scan_skipped_templates(body, metadata)
        assert unsupported_oid not in metadata["skipped_templates"]

    def test_scans_all_entry_types(self):
        oids = [f"9.9.9.{i}" for i in range(6)]
        entries = [
            Entry(act=Act(template_id=[_make_ii(oids[0])])),
            Entry(observation=Observation(template_id=[_make_ii(oids[1])])),
            Entry(organizer=Organizer(classCode="CLUSTER", template_id=[_make_ii(oids[2])])),
            Entry(procedure=Procedure(template_id=[_make_ii(oids[3])])),
            Entry(encounter=CDAEncounter(template_id=[_make_ii(oids[4])])),
            Entry(
                substance_administration=SubstanceAdministration(
                    template_id=[_make_ii(oids[5])]
                )
            ),
        ]
        body = _make_body(_make_section(entries=entries))
        metadata = _make_metadata()
        scan_skipped_templates(body, metadata)
        for oid in oids:
            assert oid in metadata["skipped_templates"]

    def test_handles_entries_without_template_ids(self):
        act = Act()  # No template_id
        body = _make_body(_make_section(entries=[Entry(act=act)]))
        metadata = _make_metadata()
        scan_skipped_templates(body, metadata)
        assert metadata["skipped_templates"] == {}
