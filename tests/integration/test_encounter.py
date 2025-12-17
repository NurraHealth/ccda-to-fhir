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

    def test_maps_anest_function_code(self) -> None:
        """Test that ANEST function code maps to SPRF (secondary performer).

        ANEST (anesthesist) is not in FHIR v3-ParticipationType, so it maps to SPRF.
        Reference: docs/mapping/09-participations.md line 953
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-005"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="ANEST" codeSystem="2.16.840.1.113883.5.88" displayName="Anesthesist"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="9999999999"/>
                        <assignedPerson><name><given>Emily</given><family>Brown</family></name></assignedPerson>
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
        assert coding["code"] == "SPRF", "C-CDA ANEST should map to FHIR SPRF (secondary performer)"
        assert coding["display"] == "Anesthesist"

    def test_maps_rndphys_function_code(self) -> None:
        """Test that RNDPHYS function code maps to ATND (attender).

        Reference: docs/mapping/09-participations.md line 961
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-006"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
                <performer>
                    <functionCode code="RNDPHYS" codeSystem="2.16.840.1.113883.5.88" displayName="Rounding Physician"/>
                    <assignedEntity>
                        <id root="2.16.840.1.113883.4.6" extension="8888888888"/>
                        <assignedPerson><name><given>Michael</given><family>Davis</family></name></assignedPerson>
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
        assert coding["code"] == "ATND", "C-CDA RNDPHYS should map to FHIR ATND (attender)"
        assert coding["display"] == "Rounding Physician"

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

    def test_provenance_created_for_encounter_with_author(
        self, ccda_encounter_with_author: str
    ) -> None:
        """Test that Provenance resource is created for Encounter with author."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_author, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None

        # Find Provenance for this encounter
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]

        # Find Provenance that targets this encounter
        encounter_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                encounter["id"] in t.get("reference", "") for t in prov["target"]
            ):
                encounter_provenance = prov
                break

        assert encounter_provenance is not None, "Provenance resource should be created for Encounter"
        # Verify Provenance has recorded date
        assert "recorded" in encounter_provenance
        # Verify Provenance has agents
        assert "agent" in encounter_provenance
        assert len(encounter_provenance["agent"]) > 0

    def test_provenance_agent_references_practitioner(
        self, ccda_encounter_with_author: str
    ) -> None:
        """Test that Provenance agent references Practitioner."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_author, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        encounter_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                encounter["id"] in t.get("reference", "") for t in prov["target"]
            ):
                encounter_provenance = prov
                break

        assert encounter_provenance is not None
        # Verify agent references practitioner
        agent = encounter_provenance["agent"][0]
        assert "who" in agent
        assert "reference" in agent["who"]
        assert agent["who"]["reference"].startswith("Practitioner/")

    def test_provenance_agent_has_author_type(
        self, ccda_encounter_with_author: str
    ) -> None:
        """Test that Provenance agent has type 'author'."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_author, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        encounter_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                encounter["id"] in t.get("reference", "") for t in prov["target"]
            ):
                encounter_provenance = prov
                break

        assert encounter_provenance is not None
        agent = encounter_provenance["agent"][0]
        assert "type" in agent
        assert "coding" in agent["type"]
        assert len(agent["type"]["coding"]) > 0
        assert agent["type"]["coding"][0]["code"] == "author"

    def test_multiple_authors_creates_multiple_provenance_agents(
        self, ccda_encounter_multiple_authors: str
    ) -> None:
        """Test that multiple authors create multiple Provenance agents."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_multiple_authors, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None

        # Find Provenance
        provenances = [
            entry["resource"]
            for entry in bundle.get("entry", [])
            if entry.get("resource", {}).get("resourceType") == "Provenance"
        ]
        encounter_provenance = None
        for prov in provenances:
            if prov.get("target") and any(
                encounter["id"] in t.get("reference", "") for t in prov["target"]
            ):
                encounter_provenance = prov
                break

        assert encounter_provenance is not None
        assert "agent" in encounter_provenance
        # Should have 2 agents for 2 authors
        assert len(encounter_provenance["agent"]) == 2

        # Verify both agents reference practitioners
        for agent in encounter_provenance["agent"]:
            assert "who" in agent
            assert "reference" in agent["who"]
            assert agent["who"]["reference"].startswith("Practitioner/")

    def test_converts_inline_problem_to_reason_code(self, ccda_encounter_with_reason_reference: str) -> None:
        """Test that inline Problem Observation (not in Problems section) creates reasonCode."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_reason_reference, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        # Inline Problem Observation should create reasonCode (not reasonReference)
        assert "reasonCode" in encounter
        assert len(encounter["reasonCode"]) >= 1
        reason_code = encounter["reasonCode"][0]
        assert "coding" in reason_code
        coding = reason_code["coding"][0]
        assert coding["system"] == "http://snomed.info/sct"
        assert coding["code"] == "59621000"
        assert "Essential hypertension" in coding["display"]

    def test_inline_problem_has_no_reason_reference(self, ccda_encounter_with_reason_reference: str) -> None:
        """Test that inline Problem Observation creates reasonCode, not reasonReference."""
        ccda_doc = wrap_in_ccda_document(ccda_encounter_with_reason_reference, ENCOUNTERS_TEMPLATE_ID)
        bundle = convert_document(ccda_doc)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        # Should have reasonCode (from inline Problem value)
        assert "reasonCode" in encounter
        # Should NOT have reasonReference (Condition doesn't exist)
        assert "reasonReference" not in encounter

    def test_converts_referenced_problem_to_reason_reference(self, ccda_encounter_with_problem_reference: str) -> None:
        """Test that Problem Observation from Problems section creates reasonReference."""
        # This fixture includes both Problems section and Encounters section
        bundle = convert_document(ccda_encounter_with_problem_reference)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        # Referenced Problem Observation should create reasonReference
        assert "reasonReference" in encounter
        assert len(encounter["reasonReference"]) >= 1
        reason_ref = encounter["reasonReference"][0]
        assert "reference" in reason_ref
        assert "Condition/" in reason_ref["reference"]
        # Should reference the Condition created from Problems section
        assert "condition-problem-hypertension-001" in reason_ref["reference"]

    def test_referenced_problem_has_no_reason_code(self, ccda_encounter_with_problem_reference: str) -> None:
        """Test that referenced Problem Observation creates reasonReference, not reasonCode."""
        bundle = convert_document(ccda_encounter_with_problem_reference)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None
        # Should have reasonReference (Condition exists)
        assert "reasonReference" in encounter
        # Should NOT have reasonCode (reference takes precedence)
        assert "reasonCode" not in encounter

    def test_reason_reference_condition_id_format(self, ccda_encounter_with_problem_reference: str) -> None:
        """Test that reasonReference uses consistent Condition ID format."""
        bundle = convert_document(ccda_encounter_with_problem_reference)

        encounter = _find_resource_in_bundle(bundle, "Encounter")
        assert encounter is not None

        reason_ref = encounter["reasonReference"][0]
        # ID should match condition.py generation logic: condition-{extension}
        assert reason_ref["reference"] == "Condition/condition-problem-hypertension-001"

    def test_cpt_outpatient_code_maps_to_ambulatory(self) -> None:
        """Test that CPT outpatient codes (99201-99215) map to AMB (ambulatory).

        Per C-CDA on FHIR IG specification (docs/mapping/08-encounter.md lines 77-86),
        CPT codes in the outpatient range should map to V3 ActCode AMB.
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-amb"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12" displayName="Office outpatient visit 15 minutes"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["code"] == "AMB", "CPT 99213 (outpatient) should map to AMB"
        assert encounter["class"]["display"] == "ambulatory"

        # CPT code should still appear in type
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99213"

    def test_cpt_inpatient_code_maps_to_inpatient(self) -> None:
        """Test that CPT inpatient codes (99221-99223) map to IMP (inpatient encounter).

        Per C-CDA on FHIR IG specification (docs/mapping/08-encounter.md lines 77-86),
        CPT codes in the initial hospital care range should map to V3 ActCode IMP.
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-imp"/>
                <code code="99221" codeSystem="2.16.840.1.113883.6.12" displayName="Initial hospital care"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["code"] == "IMP", "CPT 99221 (inpatient) should map to IMP"
        assert encounter["class"]["display"] == "inpatient encounter"

        # CPT code should still appear in type
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99221"

    def test_cpt_emergency_code_maps_to_emergency(self) -> None:
        """Test that CPT emergency codes (99281-99285) map to EMER (emergency).

        Per C-CDA on FHIR IG specification (docs/mapping/08-encounter.md lines 77-86),
        CPT codes in the emergency department range should map to V3 ActCode EMER.
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-emer"/>
                <code code="99283" codeSystem="2.16.840.1.113883.6.12" displayName="Emergency department visit"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["code"] == "EMER", "CPT 99283 (emergency) should map to EMER"
        assert encounter["class"]["display"] == "emergency"

        # CPT code should still appear in type
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99283"

    def test_cpt_home_visit_code_maps_to_home_health(self) -> None:
        """Test that CPT home visit codes (99341-99350) map to HH (home health).

        Per C-CDA on FHIR IG specification (docs/mapping/08-encounter.md lines 77-86),
        CPT codes in the home visit range should map to V3 ActCode HH.
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-hh"/>
                <code code="99345" codeSystem="2.16.840.1.113883.6.12" displayName="Home visit"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["code"] == "HH", "CPT 99345 (home visit) should map to HH"
        assert encounter["class"]["display"] == "home health"

        # CPT code should still appear in type
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99345"

    def test_cpt_code_outside_mapped_ranges_defaults_to_ambulatory(self) -> None:
        """Test that CPT codes outside known ranges default to ambulatory.

        CPT codes that don't fall into the mapped ranges (99201-99215, 99221-99223,
        99281-99285, 99341-99350) should default to ambulatory per the fallback logic.
        """
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-unmapped"/>
                <code code="99499" codeSystem="2.16.840.1.113883.6.12" displayName="Unlisted service"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        assert encounter["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"
        assert encounter["class"]["code"] == "AMB", "Unmapped CPT codes should default to AMB"

        # CPT code should still appear in type
        assert "type" in encounter
        cpt_coding = next(
            (c for c in encounter["type"][0]["coding"]
             if c.get("system") == "http://www.ama-assn.org/go/cpt"),
            None
        )
        assert cpt_coding is not None
        assert cpt_coding["code"] == "99499"

    def test_cpt_boundary_code_99215_maps_to_ambulatory(self) -> None:
        """Test boundary code 99215 (last in outpatient range) maps to AMB."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-99215"/>
                <code code="99215" codeSystem="2.16.840.1.113883.6.12" displayName="Office outpatient visit 40 minutes"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["class"]["code"] == "AMB", "CPT 99215 (boundary) should map to AMB"

    def test_cpt_boundary_code_99223_maps_to_inpatient(self) -> None:
        """Test boundary code 99223 (last in inpatient range) maps to IMP."""
        ccda_doc = wrap_in_ccda_document(
            """<encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="test-encounter-cpt-99223"/>
                <code code="99223" codeSystem="2.16.840.1.113883.6.12" displayName="Initial hospital care"/>
                <statusCode code="completed"/>
                <effectiveTime value="20230101"/>
            </encounter>""",
            ENCOUNTERS_TEMPLATE_ID
        )
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["class"]["code"] == "IMP", "CPT 99223 (boundary) should map to IMP"

    def test_header_encounter_cpt_outpatient_maps_to_ambulatory(self) -> None:
        """Test that header encounter with CPT outpatient code (no translation) maps to AMB."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-001"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test Document</title>
  <effectiveTime value="20230101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="test-patient"/>
      <patient><name><given>Test</given><family>Patient</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20230101"/>
    <assignedAuthor>
      <id root="test-author"/>
      <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="test-org"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="test-header-enc" extension="ENC-CPT-AMB"/>
      <code code="99213" codeSystem="2.16.840.1.113883.6.12" displayName="Office outpatient visit"/>
      <effectiveTime>
        <low value="20230101103000-0500"/>
        <high value="20230101110000-0500"/>
      </effectiveTime>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problems</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["id"] == "enc-cpt-amb"
        assert "class" in encounter
        assert encounter["class"]["code"] == "AMB", "Header CPT 99213 should map to AMB"
        assert encounter["class"]["display"] == "ambulatory"

    def test_header_encounter_cpt_inpatient_maps_to_inpatient(self) -> None:
        """Test that header encounter with CPT inpatient code (no translation) maps to IMP."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-002"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test Document</title>
  <effectiveTime value="20230101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="test-patient"/>
      <patient><name><given>Test</given><family>Patient</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20230101"/>
    <assignedAuthor>
      <id root="test-author"/>
      <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="test-org"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="test-header-enc" extension="ENC-CPT-IMP"/>
      <code code="99221" codeSystem="2.16.840.1.113883.6.12" displayName="Initial hospital care"/>
      <effectiveTime>
        <low value="20230101103000-0500"/>
        <high value="20230101110000-0500"/>
      </effectiveTime>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problems</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["id"] == "enc-cpt-imp"
        assert "class" in encounter
        assert encounter["class"]["code"] == "IMP", "Header CPT 99221 should map to IMP"
        assert encounter["class"]["display"] == "inpatient encounter"

    def test_header_encounter_cpt_emergency_maps_to_emergency(self) -> None:
        """Test that header encounter with CPT emergency code (no translation) maps to EMER."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-003"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test Document</title>
  <effectiveTime value="20230101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="test-patient"/>
      <patient><name><given>Test</given><family>Patient</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20230101"/>
    <assignedAuthor>
      <id root="test-author"/>
      <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="test-org"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="test-header-enc" extension="ENC-CPT-EMER"/>
      <code code="99283" codeSystem="2.16.840.1.113883.6.12" displayName="Emergency department visit"/>
      <effectiveTime>
        <low value="20230101103000-0500"/>
        <high value="20230101110000-0500"/>
      </effectiveTime>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problems</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["id"] == "enc-cpt-emer"
        assert "class" in encounter
        assert encounter["class"]["code"] == "EMER", "Header CPT 99283 should map to EMER"
        assert encounter["class"]["display"] == "emergency"

    def test_header_encounter_cpt_home_visit_maps_to_home_health(self) -> None:
        """Test that header encounter with CPT home visit code (no translation) maps to HH."""
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-004"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test Document</title>
  <effectiveTime value="20230101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="test-patient"/>
      <patient><name><given>Test</given><family>Patient</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20230101"/>
    <assignedAuthor>
      <id root="test-author"/>
      <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="test-org"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="test-header-enc" extension="ENC-CPT-HH"/>
      <code code="99345" codeSystem="2.16.840.1.113883.6.12" displayName="Home visit"/>
      <effectiveTime>
        <low value="20230101103000-0500"/>
        <high value="20230101110000-0500"/>
      </effectiveTime>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problems</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert encounter["id"] == "enc-cpt-hh"
        assert "class" in encounter
        assert encounter["class"]["code"] == "HH", "Header CPT 99345 should map to HH"
        assert encounter["class"]["display"] == "home health"

    def test_header_encounter_translation_takes_precedence_over_cpt(self) -> None:
        """Test that explicit V3 ActCode translation takes precedence over CPT mapping.

        Per C-CDA on FHIR IG specification, explicit V3 ActCode translations should be
        preferred over automatic CPT to ActCode mapping.
        """
        ccda_doc = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc-005"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test Document</title>
  <effectiveTime value="20230101"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <languageCode code="en-US"/>
  <recordTarget>
    <patientRole>
      <id root="test-patient"/>
      <patient><name><given>Test</given><family>Patient</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20230101"/>
    <assignedAuthor>
      <id root="test-author"/>
      <assignedPerson><name><given>Test</given><family>Author</family></name></assignedPerson>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="test-org"/>
        <name>Test Org</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="test-header-enc" extension="ENC-CPT-WITH-TRANSLATION"/>
      <code code="99221" codeSystem="2.16.840.1.113883.6.12" displayName="Initial hospital care">
        <translation code="EMER" codeSystem="2.16.840.1.113883.5.4" displayName="Emergency"/>
      </code>
      <effectiveTime>
        <low value="20230101103000-0500"/>
        <high value="20230101110000-0500"/>
      </effectiveTime>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.5.1"/>
          <code code="11450-4" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Problems</title>
          <text>No problems</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""
        bundle = convert_document(ccda_doc)
        encounter = _find_resource_in_bundle(bundle, "Encounter")

        assert encounter is not None
        assert "class" in encounter
        # CPT 99221 would normally map to IMP, but explicit translation is EMER
        # Translation should take precedence
        assert encounter["class"]["code"] == "EMER", "Explicit translation EMER should take precedence over CPT mapping (IMP)"
        assert encounter["class"]["display"] == "Emergency"
