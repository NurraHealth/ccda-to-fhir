"""Unit tests for Procedure.recorder display text (#80).

Validates that Procedure.recorder includes display from person/device name.
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models.author import (
    AssignedAuthor,
    AssignedAuthoringDevice,
    Author,
)
from ccda_to_fhir.ccda.models.datatypes import ENXP, II, PN, TS, AssignedPerson
from ccda_to_fhir.converters.procedure import ProcedureConverter
from ccda_to_fhir.id_generator import reset_id_cache


@pytest.fixture(autouse=True)
def _reset_ids():  # pyright: ignore[reportUnusedFunction]
    reset_id_cache()
    yield
    reset_id_cache()


class TestProcedureRecorderDisplay:
    def test_recorder_has_person_display(self) -> None:
        """Procedure.recorder should include display from assignedPerson name."""
        authors = [
            Author(
                time=TS(value="20240122"),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(
                        name=[
                            PN(
                                given=[ENXP(value="Henry")],
                                family=ENXP(value="Doe"),
                            )
                        ]
                    ),
                ),
            )
        ]
        converter = ProcedureConverter()
        recorder = converter._extract_recorder(authors)

        assert recorder is not None
        assert recorder.reference.startswith("urn:uuid:")
        assert recorder.display == "Henry Doe"

    def test_recorder_has_device_display(self) -> None:
        """Procedure.recorder should include display from device name."""
        authors = [
            Author(
                time=TS(value="20240122"),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.19", extension="dev-1")],
                    assigned_authoring_device=AssignedAuthoringDevice(
                        manufacturer_model_name="Athena",
                        software_name="athenaCollector",
                    ),
                ),
            )
        ]
        converter = ProcedureConverter()
        recorder = converter._extract_recorder(authors)

        assert recorder is not None
        assert recorder.reference.startswith("urn:uuid:")
        assert recorder.display == "Athena (athenaCollector)"

    def test_recorder_no_name_omits_display(self) -> None:
        """When person has no name, display should be absent."""
        authors = [
            Author(
                time=TS(value="20240122"),
                assigned_author=AssignedAuthor(
                    id=[II(root="2.16.840.1.113883.4.6", extension="1234567890")],
                    assigned_person=AssignedPerson(name=[]),
                ),
            )
        ]
        converter = ProcedureConverter()
        recorder = converter._extract_recorder(authors)

        assert recorder is not None
        assert recorder.display is None
