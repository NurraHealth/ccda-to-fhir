"""E2E tests for Encounter resource conversion."""

from __future__ import annotations

from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from ccda_to_fhir.convert import convert_document

from .conftest import wrap_in_ccda_document

ENCOUNTERS_TEMPLATE_ID = "2.16.840.1.113883.10.20.22.2.22.1"


def _find_resource_in_bundle(bundle: JSONObject, resource_type: str) -> JSONObject | None:
    """Find a resource of the given type in a FHIR Bundle."""
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") == resource_type:
            return resource
    return None


class TestEncounterConversion:
    """E2E tests for C-CDA Encounter Activity to FHIR Encounter conversion."""

    def test_converts_identifier(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that identifier is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "identifier" in encounter
        assert len(encounter["identifier"]) == 1
        assert encounter["identifier"][0]["value"] == "urn:uuid:2a620155-9d11-439e-92b3-5d9815ff4de8"

    def test_converts_status_to_finished(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that status is always 'finished' for documented encounters."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert encounter["status"] == "finished"

    def test_converts_class_default_ambulatory(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that class defaults to ambulatory."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["code"] == "AMB"
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"

    def test_converts_type_code(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that encounter type code is correctly converted."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "type" in encounter
        assert len(encounter["type"]) == 1
        cpt = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt is not None
        assert cpt["code"] == "99213"
        assert cpt["display"] == "Office outpatient visit 15 minutes"

    def test_converts_type_text(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that type text is derived from display name."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "type" in encounter
        assert "text" in encounter["type"][0]

    def test_converts_period_start(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that effectiveTime is converted to period.start."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "period" in encounter
        assert "start" in encounter["period"]
        assert "2012-08-15" in encounter["period"]["start"]

    def test_converts_reason_code_from_diagnosis(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that encounter diagnosis is converted to diagnosis references."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        # Encounter diagnoses should be in diagnosis array, not reasonCode
        assert "diagnosis" in encounter
        assert len(encounter["diagnosis"]) == 1
        assert "condition" in encounter["diagnosis"][0]
        assert "reference" in encounter["diagnosis"][0]["condition"]
        assert encounter["diagnosis"][0]["condition"]["reference"].startswith("Condition/")
        # Should have diagnosis use/role
        assert "use" in encounter["diagnosis"][0]

    def test_resource_type_is_encounter(
        self, ccda_encounter: str, fhir_encounter: JSONObject
    ) -> None:
        """Test that the resource type is Encounter."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert encounter["resourceType"] == "Encounter"

    def test_converts_status_code_completed_to_finished(
        self, ccda_encounter_with_status_code: str
    ) -> None:
        """Test that statusCode 'completed' is converted to status 'finished'."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_status_code, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert encounter["status"] == "finished"

    def test_converts_v3_actcode_class(
        self, ccda_encounter_inpatient_v3: str
    ) -> None:
        """Test that V3 ActCode class is correctly mapped to encounter.class."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_inpatient_v3, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["code"] == "IMP"
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["display"] == "inpatient encounter"

    def test_converts_performer_function_code_to_participant(
        self, ccda_encounter_with_function_code: str
    ) -> None:
        """Test that performer functionCode is converted to participant.type with proper mapping.

        C-CDA PCP (Primary Care Provider) should map to FHIR PPRF (primary performer)
        per mapping spec docs/mapping/08-encounter.md lines 217-223.
        """
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_function_code, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "participant" in encounter
        assert len(encounter["participant"]) >= 1

        # Find participant with type
        participant_with_type = next(
            (p for p in encounter["participant"] if "type" in p),
            None
        )
        assert participant_with_type is not None
        assert len(participant_with_type["type"]) == 1

        # Check the type coding - C-CDA PCP should map to FHIR PPRF
        pcp_coding = next(
            (c for c in participant_with_type["type"][0]["coding"]
             if c.get("system") == "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"),
            None
        )
        assert pcp_coding is not None
        assert pcp_coding["code"] == "PPRF", "C-CDA PCP should map to FHIR PPRF (primary performer)"
        assert pcp_coding["display"] == "Primary Care Provider"

    def test_converts_location_participant(
        self, ccda_encounter_with_location: str
    ) -> None:
        """Test that location participant is converted to encounter.location."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_location, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "location" in encounter
        assert len(encounter["location"]) == 1

        location = encounter["location"][0]
        assert "location" in location
        assert "reference" in location["location"]
        assert location["location"]["reference"] == "Location/ROOM-101"
        assert "status" in location
        assert location["status"] == "completed"

    def test_converts_discharge_disposition(
        self, ccda_encounter_with_discharge: str
    ) -> None:
        """Test that discharge disposition is correctly mapped."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_discharge, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        assert "hospitalization" in encounter
        assert "dischargeDisposition" in encounter["hospitalization"]

        discharge_disp = encounter["hospitalization"]["dischargeDisposition"]
        assert "coding" in discharge_disp
        assert len(discharge_disp["coding"]) == 1
        assert discharge_disp["coding"][0]["code"] == "home"
        assert discharge_disp["coding"][0]["system"] == "http://terminology.hl7.org/CodeSystem/discharge-disposition"

    def test_maps_attphys_function_code(self) -> None:
        """Test that ATTPHYS function code maps to ATND (attender)."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-001"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="ATTPHYS" codeSystem="2.16.840.1.113883.5.88" displayName="Attending Physician"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                        <assignedPerson><name><given>John</given><family>Doe</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        participant = next((p for p in encounter["participant"] if "type" in p), None)
        assert participant is not None
        coding = participant["type"][0]["coding"][0]
        assert coding["code"] == "ATND", "C-CDA ATTPHYS should map to FHIR ATND (attender)"
        assert coding["display"] == "Attending Physician"

    def test_maps_admphys_function_code(self) -> None:
        """Test that ADMPHYS function code maps to ADM (admitter)."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-002"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="ADMPHYS" codeSystem="2.16.840.1.113883.5.88" displayName="Admitting Physician"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                        <assignedPerson><name><given>Jane</given><family>Smith</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        participant = next((p for p in encounter["participant"] if "type" in p), None)
        assert participant is not None
        coding = participant["type"][0]["coding"][0]
        assert coding["code"] == "ADM", "C-CDA ADMPHYS should map to FHIR ADM (admitter)"
        assert coding["display"] == "Admitting Physician"

    def test_maps_disphys_function_code(self) -> None:
        """Test that DISPHYS function code maps to DIS (discharger)."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-003"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="DISPHYS" codeSystem="2.16.840.1.113883.5.88" displayName="Discharging Physician"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                        <assignedPerson><name><given>Bob</given><family>Johnson</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        participant = next((p for p in encounter["participant"] if "type" in p), None)
        assert participant is not None
        coding = participant["type"][0]["coding"][0]
        assert coding["code"] == "DIS", "C-CDA DISPHYS should map to FHIR DIS (discharger)"
        assert coding["display"] == "Discharging Physician"

    def test_defaults_to_part_when_no_function_code(self) -> None:
        """Test that participants without functionCode default to PART (participant)."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-004"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
                        <assignedPerson><name><given>Alice</given><family>Williams</family></name></assignedPerson>
                    </assignedEntity>
                </performer>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        participant = next((p for p in encounter["participant"] if "type" in p), None)
        assert participant is not None
        coding = participant["type"][0]["coding"][0]
        assert coding["code"] == "PART", "No functionCode should default to PART (participant)"
        assert coding["display"] == "participant"

    def test_header_encounter_only(
        self, ccda_header_encounter_only: str
    ) -> None:
        """Test that header encompassingEncounter creates an Encounter resource when no body encounters exist."""
        # This is a full document, not a wrapped encounter
        bundle = convert_document(ccda_header_encounter_only)

        # Should have an Encounter resource from header
        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None, "Encounter resource should be created from header encompassingEncounter"

        # Verify identifier from header encounter ID
        assert "identifier" in encounter
        assert len(encounter["identifier"]) >= 1
        identifier = next(
            (i for i in encounter["identifier"] if "ENC-HEADER-12345" in i.get("value", "")),
            None
        )
        assert identifier is not None, "Should have identifier from header encounter"

        # Verify ID matches header encounter (lowercased for consistency)
        assert encounter["id"] == "enc-header-12345"

        # Verify status (default to finished for header encounters)
        assert encounter["status"] == "finished"

        # Verify class from translation code (AMB from V3 ActCode)
        assert "class" in encounter
        assert encounter["class"]["code"] == "AMB"
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"

        # Verify type from encounter code (CPT)
        assert "type" in encounter
        assert len(encounter["type"]) >= 1
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99213"

        # Verify period from effectiveTime
        assert "period" in encounter
        assert "start" in encounter["period"]
        assert "2023-12-01" in encounter["period"]["start"]
        assert "end" in encounter["period"]
        assert "2023-12-01" in encounter["period"]["end"]

        # Verify participants from responsibleParty and encounterParticipant
        assert "participant" in encounter
        assert len(encounter["participant"]) >= 2, "Should have responsibleParty and encounterParticipant"

        # Verify location from healthCareFacility
        assert "location" in encounter
        assert len(encounter["location"]) >= 1
        location = encounter["location"][0]
        assert "location" in location
        assert "display" in location["location"]
        assert "City Medical Center - Main Campus" in location["location"]["display"]

        # Verify discharge disposition
        assert "hospitalization" in encounter
        assert "dischargeDisposition" in encounter["hospitalization"]
        assert encounter["hospitalization"]["dischargeDisposition"]["coding"][0]["code"] == "home"

        # Verify DocumentReference.context.encounter references this encounter
        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is not None
        assert "context" in doc_ref
        assert "encounter" in doc_ref["context"]
        assert len(doc_ref["context"]["encounter"]) >= 1
        assert doc_ref["context"]["encounter"][0]["reference"] == f"Encounter/{encounter['id']}"

    def test_deduplication_prefers_body_over_header(
        self, ccda_header_and_body_encounter: str
    ) -> None:
        """Test that when header and body encounters have same ID, body version is used."""
        bundle = convert_document(ccda_header_and_body_encounter)

        # Find all Encounter resources
        encounters = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Encounter"
        ]

        # Should only have ONE encounter despite both header and body having same ID
        assert len(encounters) == 1, "Should deduplicate - only one encounter with same ID"

        encounter = encounters[0]
        # Body encounter has uppercase ID (body converter doesn't lowercase)
        assert encounter["id"] == "ENC-HEADER-12345"

        # Verify the encounter uses BODY version values, not header version
        # Body has code 99214 (25 min visit), header has 99213 (15 min visit)
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99214", "Should use body encounter code (99214), not header (99213)"
        assert "25 minutes" in cpt_coding["display"]

        # Body has class IMP (inpatient), header has AMB (ambulatory)
        assert "class" in encounter
        assert encounter["class"]["code"] == "IMP", "Should use body encounter class (IMP), not header (AMB)"

        # Body has different time range: 10:00-12:00 vs header 10:30-11:30
        assert "period" in encounter
        assert "start" in encounter["period"]
        assert "2023-12-01T10:00:00" in encounter["period"]["start"], "Should use body encounter start time"

        # Body has different performer (Jane Doe), location (Downtown ER)
        assert "participant" in encounter
        # At least one participant from body encounter
        assert len(encounter["participant"]) >= 1

        assert "location" in encounter
        # Location should be from body (LOC-BODY-001), not header (LOC-HEADER-001)
        location_ref = encounter["location"][0]["location"]["reference"]
        assert "LOC-BODY-001" in location_ref, "Should use body encounter location (LOC-BODY-001)"
