"""Comprehensive tests for C-CDA XML parser.

Tests cover:
- Basic XML parsing
- Namespace handling
- Attribute parsing and camelCase to snake_case conversion
- xsi:type polymorphism
- Recursive nested structures
- List aggregation for repeated elements
- Error handling
- Real fixture parsing
"""

from __future__ import annotations

import pytest

from ccda_to_fhir.ccda.models import (
    AD,
    BL,
    CD,
    CE,
    II,
    IVL_TS,
    PN,
    PQ,
    TS,
    Act,
    Observation,
    Organizer,
    Patient,
    RecordTarget,
)
from ccda_to_fhir.ccda.parser import (
    MalformedXMLError,
    UnknownTypeError,
    _strip_namespace,
    _to_snake_case,
    parse_ccda_fragment,
)


class TestHelperFunctions:
    """Test internal helper functions."""

    def test_strip_namespace(self) -> None:
        """Test namespace stripping from XML tags."""
        assert _strip_namespace("{urn:hl7-org:v3}ClinicalDocument") == "ClinicalDocument"
        assert _strip_namespace("{http://example.com}tag") == "tag"
        assert _strip_namespace("nonamespace") == "nonamespace"

    def test_to_snake_case(self) -> None:
        """Test camelCase to snake_case conversion."""
        assert _to_snake_case("classCode") == "class_code"
        assert _to_snake_case("moodCode") == "mood_code"
        assert _to_snake_case("administrativeGenderCode") == "administrative_gender_code"
        assert _to_snake_case("lowercase") == "lowercase"
        assert _to_snake_case("ID") == "i_d"


class TestBasicParsing:
    """Test basic XML element parsing."""

    def test_parse_simple_identifier(self) -> None:
        """Test parsing a simple II (Instance Identifier)."""
        xml = '<id root="2.16.840.1.113883.19.5" extension="12345" xmlns="urn:hl7-org:v3"/>'
        ii = parse_ccda_fragment(xml, II)

        assert ii.root == "2.16.840.1.113883.19.5"
        assert ii.extension == "12345"

    def test_parse_identifier_without_extension(self) -> None:
        """Test parsing II with only root (no extension)."""
        xml = '<id root="2.16.840.1.113883.19.5" xmlns="urn:hl7-org:v3"/>'
        ii = parse_ccda_fragment(xml, II)

        assert ii.root == "2.16.840.1.113883.19.5"
        assert ii.extension is None

    def test_parse_coded_element(self) -> None:
        """Test parsing CE (Coded Element)."""
        xml = '''<code code="F" codeSystem="2.16.840.1.113883.5.1"
                      displayName="Female" xmlns="urn:hl7-org:v3"/>'''
        ce = parse_ccda_fragment(xml, CE)

        assert ce.code == "F"
        assert ce.code_system == "2.16.840.1.113883.5.1"
        assert ce.display_name == "Female"

    def test_parse_timestamp(self) -> None:
        """Test parsing TS (Timestamp)."""
        xml = '<birthTime value="19470501" xmlns="urn:hl7-org:v3"/>'
        ts = parse_ccda_fragment(xml, TS)

        assert ts.value == "19470501"

    def test_parse_boolean(self) -> None:
        """Test parsing BL (Boolean)."""
        xml = '<value value="true" xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="BL"/>'
        bl = parse_ccda_fragment(xml, BL)

        assert bl.value is True


class TestNamespaceHandling:
    """Test XML namespace handling."""

    def test_parse_with_default_namespace(self) -> None:
        """Test parsing with default HL7 namespace."""
        xml = '''<id root="123" xmlns="urn:hl7-org:v3"/>'''
        ii = parse_ccda_fragment(xml, II)
        assert ii.root == "123"

    def test_parse_with_sdtc_namespace(self) -> None:
        """Test parsing elements with SDTC namespace."""
        xml = '''
        <patient xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
            <sdtc:deceasedInd value="false"/>
        </patient>
        '''
        patient = parse_ccda_fragment(xml, Patient)
        assert patient.sdtc_deceased_ind is False


class TestPolymorphicValues:
    """Test xsi:type polymorphism in value elements."""

    def test_parse_pq_value(self) -> None:
        """Test parsing PQ (Physical Quantity) with xsi:type."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"/>
            <statusCode code="completed"/>
            <value xsi:type="PQ" value="80" unit="/min"/>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        assert obs.code is not None
        assert obs.code.code == "8867-4"
        assert isinstance(obs.value, PQ)
        assert obs.value.value == "80"
        assert obs.value.unit == "/min"

    def test_parse_cd_value(self) -> None:
        """Test parsing CD (Concept Descriptor) with xsi:type."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <statusCode code="completed"/>
            <value xsi:type="CD" code="419511003" codeSystem="2.16.840.1.113883.6.96"
                   displayName="Propensity to adverse reactions to drug"/>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        assert isinstance(obs.value, CD)
        assert obs.value.code == "419511003"
        assert obs.value.display_name == "Propensity to adverse reactions to drug"

    def test_parse_ivl_ts_value(self) -> None:
        """Test parsing IVL_TS (Interval of Time) with xsi:type."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <statusCode code="completed"/>
            <effectiveTime xsi:type="IVL_TS">
                <low value="20080501"/>
                <high value="20090501"/>
            </effectiveTime>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        assert isinstance(obs.effective_time, IVL_TS)
        assert obs.effective_time.low is not None
        assert obs.effective_time.low.value == "20080501"
        assert obs.effective_time.high is not None
        assert obs.effective_time.high.value == "20090501"

    def test_unknown_xsi_type_raises_error(self) -> None:
        """Test that unknown xsi:type raises UnknownTypeError."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <value xsi:type="UNKNOWN_TYPE" value="test"/>
        </observation>
        '''
        with pytest.raises(UnknownTypeError) as exc_info:
            parse_ccda_fragment(xml, Observation)

        assert "UNKNOWN_TYPE" in str(exc_info.value)
        assert exc_info.value.xsi_type == "UNKNOWN_TYPE"


class TestNestedStructures:
    """Test parsing recursive nested structures."""

    def test_parse_person_name(self) -> None:
        """Test parsing PN (Person Name) with nested parts."""
        xml = '''
        <name use="L" xmlns="urn:hl7-org:v3">
            <given>Myra</given>
            <family>Jones</family>
        </name>
        '''
        pn = parse_ccda_fragment(xml, PN)

        assert pn.use == "L"
        assert pn.family is not None
        assert "Jones" in str(pn.family)
        assert pn.given is not None
        assert len(pn.given) == 1
        assert "Myra" in str(pn.given[0])

    def test_parse_address(self) -> None:
        """Test parsing AD (Address) with nested components."""
        xml = '''
        <addr use="H" xmlns="urn:hl7-org:v3">
            <streetAddressLine>1357 Amber Drive</streetAddressLine>
            <city>Beaverton</city>
            <state>OR</state>
            <postalCode>97006</postalCode>
        </addr>
        '''
        ad = parse_ccda_fragment(xml, AD)

        assert ad.use == "H"
        assert ad.street_address_line is not None
        assert len(ad.street_address_line) == 1
        assert ad.street_address_line[0] == "1357 Amber Drive"
        assert ad.city == "Beaverton"
        assert ad.state == "OR"
        assert ad.postal_code == "97006"

    def test_parse_nested_observations_in_act(self) -> None:
        """Test parsing Act with nested EntryRelationship and Observation."""
        xml = '''
        <act classCode="ACT" moodCode="EVN" xmlns="urn:hl7-org:v3"
             xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <templateId root="2.16.840.1.113883.10.20.22.4.3"/>
            <id root="36e3e930-7b14-11db-9fe1-0800200c9a66"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <entryRelationship typeCode="SUBJ">
                <observation classCode="OBS" moodCode="EVN">
                    <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
                    <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
                    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
                    <statusCode code="completed"/>
                    <effectiveTime>
                        <low value="20100301"/>
                    </effectiveTime>
                    <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"/>
                </observation>
            </entryRelationship>
        </act>
        '''
        act = parse_ccda_fragment(xml, Act)

        assert act.code is not None
        assert act.code.code == "CONC"
        assert act.entry_relationship is not None
        assert len(act.entry_relationship) == 1

        entry_rel = act.entry_relationship[0]
        assert entry_rel.type_code == "SUBJ"
        assert entry_rel.observation is not None
        assert entry_rel.observation.code is not None
        assert entry_rel.observation.code.code == "ASSERTION"


class TestListAggregation:
    """Test aggregation of repeated XML elements into lists."""

    def test_parse_multiple_identifiers(self) -> None:
        """Test parsing multiple <id> elements into a list."""
        xml = '''
        <act classCode="ACT" moodCode="EVN" xmlns="urn:hl7-org:v3">
            <id root="1.2.3.4" extension="1"/>
            <id root="5.6.7.8" extension="2"/>
            <code code="CONC" codeSystem="2.16.840.1.113883.5.6"/>
            <statusCode code="active"/>
        </act>
        '''
        act = parse_ccda_fragment(xml, Act)

        assert act.id is not None
        assert len(act.id) == 2
        assert act.id[0].root == "1.2.3.4"
        assert act.id[0].extension == "1"
        assert act.id[1].root == "5.6.7.8"
        assert act.id[1].extension == "2"

    def test_parse_multiple_template_ids(self) -> None:
        """Test parsing multiple <templateId> elements."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <templateId root="2.16.840.1.113883.10.20.22.4.4"/>
            <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
            <id root="ab1791b0-5c71-11db-b0de-0800200c9a66"/>
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <statusCode code="completed"/>
            <effectiveTime>
                <low value="20100301"/>
            </effectiveTime>
            <value xsi:type="CD" code="38341003" codeSystem="2.16.840.1.113883.6.96"/>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        assert obs.template_id is not None
        assert len(obs.template_id) == 2
        assert obs.template_id[0].root == "2.16.840.1.113883.10.20.22.4.4"
        assert obs.template_id[0].extension is None
        assert obs.template_id[1].extension == "2015-08-01"

    def test_parse_organizer_with_components(self) -> None:
        """Test parsing Organizer with multiple components."""
        xml = '''
        <organizer classCode="CLUSTER" moodCode="EVN" xmlns="urn:hl7-org:v3"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
            <templateId root="2.16.840.1.113883.10.20.22.4.26"/>
            <id root="c6f88320-67ad-11db-bd13-0800200c9a66"/>
            <code code="46680005" codeSystem="2.16.840.1.113883.6.96"/>
            <statusCode code="completed"/>
            <effectiveTime value="20231201120000"/>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8867-4" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <value xsi:type="PQ" value="80" unit="/min"/>
                </observation>
            </component>
            <component>
                <observation classCode="OBS" moodCode="EVN">
                    <code code="8480-6" codeSystem="2.16.840.1.113883.6.1"/>
                    <statusCode code="completed"/>
                    <value xsi:type="PQ" value="120" unit="mm[Hg]"/>
                </observation>
            </component>
        </organizer>
        '''
        organizer = parse_ccda_fragment(xml, Organizer)

        assert organizer.class_code == "CLUSTER"
        assert organizer.component is not None
        assert len(organizer.component) == 2

        # First component
        comp1 = organizer.component[0]
        assert comp1.observation is not None
        assert comp1.observation.code is not None
        assert comp1.observation.code.code == "8867-4"
        assert isinstance(comp1.observation.value, PQ)
        assert comp1.observation.value.value == "80"

        # Second component
        comp2 = organizer.component[1]
        assert comp2.observation is not None
        assert comp2.observation.code.code == "8480-6"
        assert isinstance(comp2.observation.value, PQ)
        assert comp2.observation.value.value == "120"


class TestAttributeConversion:
    """Test attribute parsing and name conversion."""

    def test_class_code_conversion(self) -> None:
        """Test that classCode is converted to class_code."""
        xml = '<observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3"><code code="TEST" codeSystem="1.2.3"/><statusCode code="completed"/></observation>'
        obs = parse_ccda_fragment(xml, Observation)

        assert obs.class_code == "OBS"
        assert obs.mood_code == "EVN"

    def test_multiple_word_attribute_conversion(self) -> None:
        """Test conversion of multi-word attributes."""
        xml = '''
        <entryRelationship typeCode="SUBJ" inversionInd="true"
                           contextConductionInd="true" xmlns="urn:hl7-org:v3">
            <observation classCode="OBS" moodCode="EVN">
                <code code="TEST" codeSystem="1.2.3"/>
                <statusCode code="completed"/>
            </observation>
        </entryRelationship>
        '''
        from ccda_to_fhir.ccda.models import EntryRelationship

        entry_rel = parse_ccda_fragment(xml, EntryRelationship)

        assert entry_rel.type_code == "SUBJ"
        assert entry_rel.inversion_ind is True
        assert entry_rel.context_conduction_ind is True


class TestRealFixtures:
    """Test parsing real C-CDA fixtures."""

    def test_parse_patient_fixture(self) -> None:
        """Test parsing real patient recordTarget fixture."""
        from pathlib import Path

        fixture_path = Path(__file__).parent.parent / "integration" / "fixtures" / "ccda" / "patient.xml"
        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        xml = fixture_path.read_text()
        record_target = parse_ccda_fragment(xml, RecordTarget)

        # Verify structure
        assert record_target.patient_role is not None

        patient_role = record_target.patient_role
        assert patient_role.id is not None
        assert len(patient_role.id) >= 1
        assert patient_role.id[0].root == "068F3166-5721-4D69-94ED-8278FF035B8A"

        # Verify patient
        assert patient_role.patient is not None
        patient = patient_role.patient

        # Name
        assert patient.name is not None
        assert len(patient.name) >= 1
        name = patient.name[0]
        assert name.use == "L"
        assert name.given is not None
        assert "Myra" in str(name.given[0])
        assert "Jones" in str(name.family)

        # Gender
        assert patient.administrative_gender_code is not None
        assert patient.administrative_gender_code.code == "F"

        # Birth date
        assert patient.birth_time is not None
        assert patient.birth_time.value == "19470501"

        # Deceased
        assert patient.sdtc_deceased_ind is False

        # Race and ethnicity
        assert patient.race_code is not None
        assert patient.race_code.code == "2106-3"
        assert patient.sdtc_race_code is not None
        assert len(patient.sdtc_race_code) >= 1

        # Guardian
        assert patient.guardian is not None
        assert len(patient.guardian) >= 1
        guardian = patient.guardian[0]
        assert guardian.code is not None
        assert guardian.code.code == "FTH"

        # Language
        assert patient.language_communication is not None
        assert len(patient.language_communication) >= 1
        lang = patient.language_communication[0]
        assert lang.language_code is not None
        assert lang.language_code.code == "en"
        assert lang.preference_ind is True

    def test_parse_allergy_fixture(self) -> None:
        """Test parsing real allergy concern act fixture."""
        from pathlib import Path

        fixture_path = Path(__file__).parent.parent / "integration" / "fixtures" / "ccda" / "allergy.xml"
        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        xml = fixture_path.read_text()
        act = parse_ccda_fragment(xml, Act)

        # Verify Allergy Concern Act structure
        assert act.class_code == "ACT"
        assert act.mood_code == "EVN"
        assert act.template_id is not None
        assert any(tid.root == "2.16.840.1.113883.10.20.22.4.30" for tid in act.template_id)

        # Verify status
        assert act.status_code is not None
        assert act.status_code.code == "active"

        # Verify nested Allergy Intolerance Observation
        assert act.entry_relationship is not None
        assert len(act.entry_relationship) >= 1

        allergy_obs = act.entry_relationship[0].observation
        assert allergy_obs is not None
        assert allergy_obs.template_id is not None
        assert any(tid.root == "2.16.840.1.113883.10.20.22.4.7" for tid in allergy_obs.template_id)

        # Verify allergen in participant
        assert allergy_obs.participant is not None
        assert len(allergy_obs.participant) >= 1
        participant = allergy_obs.participant[0]
        assert participant.participant_role is not None
        assert participant.participant_role.playing_entity is not None
        assert participant.participant_role.playing_entity.code is not None
        assert participant.participant_role.playing_entity.code.code == "1191"  # Aspirin

        # Verify nested reaction observation
        assert allergy_obs.entry_relationship is not None
        assert len(allergy_obs.entry_relationship) >= 1
        reaction_entry = allergy_obs.entry_relationship[0]
        assert reaction_entry.observation is not None
        assert reaction_entry.observation.value is not None
        assert isinstance(reaction_entry.observation.value, CD)

    def test_parse_vital_signs_fixture(self) -> None:
        """Test parsing real vital signs organizer fixture."""
        from pathlib import Path

        fixture_path = Path(__file__).parent.parent / "integration" / "fixtures" / "ccda" / "vital_signs.xml"
        if not fixture_path.exists():
            pytest.skip(f"Fixture not found: {fixture_path}")

        xml = fixture_path.read_text()
        organizer = parse_ccda_fragment(xml, Organizer)

        # Verify Vital Signs Organizer structure
        assert organizer.class_code == "CLUSTER"
        assert organizer.mood_code == "EVN"
        assert organizer.template_id is not None
        assert any(tid.root == "2.16.840.1.113883.10.20.22.4.26" for tid in organizer.template_id)

        # Verify organizer code
        assert organizer.code is not None
        assert organizer.code.code == "46680005"

        # Verify status
        assert organizer.status_code is not None
        assert organizer.status_code.code == "completed"

        # Verify components
        assert organizer.component is not None
        assert len(organizer.component) >= 3  # Heart rate, systolic, diastolic

        # Check heart rate observation
        hr_component = organizer.component[0]
        assert hr_component.observation is not None
        hr_obs = hr_component.observation
        assert hr_obs.code is not None
        assert hr_obs.code.code == "8867-4"  # Heart rate LOINC
        assert isinstance(hr_obs.value, PQ)
        assert hr_obs.value.value == "80"
        assert hr_obs.value.unit == "/min"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_xml_raises_error(self) -> None:
        """Test that invalid XML raises MalformedXMLError."""
        xml = "<invalid><xml>"
        with pytest.raises(MalformedXMLError):
            parse_ccda_fragment(xml, II)

    def test_empty_xml_raises_error(self) -> None:
        """Test that empty XML raises error."""
        xml = ""
        with pytest.raises(MalformedXMLError):
            parse_ccda_fragment(xml, II)

    def test_missing_required_attributes(self) -> None:
        """Test parsing with missing attributes (should still work with Pydantic defaults)."""
        xml = '<observation xmlns="urn:hl7-org:v3"><code code="TEST" codeSystem="1.2.3"/><statusCode code="completed"/></observation>'
        obs = parse_ccda_fragment(xml, Observation)

        # Should use defaults from model
        assert obs.class_code == "OBS"
        assert obs.mood_code == "EVN"

    def test_unknown_child_elements_ignored(self) -> None:
        """Test that unknown child elements are ignored (extra='ignore')."""
        xml = '''
        <id root="123" xmlns="urn:hl7-org:v3">
            <unknownElement>This should be ignored</unknownElement>
        </id>
        '''
        ii = parse_ccda_fragment(xml, II)

        assert ii.root == "123"
        # Should not raise error, unknown elements ignored


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_null_flavor_attribute(self) -> None:
        """Test parsing elements with nullFlavor."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3">
            <id nullFlavor="NI"/>
            <code code="TEST" codeSystem="1.2.3"/>
            <statusCode code="completed"/>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        assert obs.id is not None
        assert len(obs.id) == 1
        assert obs.id[0].null_flavor == "NI"

    def test_text_content_in_elements(self) -> None:
        """Test parsing elements with text content."""
        xml = '<text xmlns="urn:hl7-org:v3">This is narrative text content</text>'
        from ccda_to_fhir.ccda.models import ED

        ed = parse_ccda_fragment(xml, ED)
        # Text content handling depends on ED model structure
        # This test documents current behavior

    def test_empty_list_when_no_elements(self) -> None:
        """Test that missing repeated elements result in None (not empty list)."""
        xml = '''
        <observation classCode="OBS" moodCode="EVN" xmlns="urn:hl7-org:v3">
            <code code="TEST" codeSystem="1.2.3"/>
            <statusCode code="completed"/>
        </observation>
        '''
        obs = parse_ccda_fragment(xml, Observation)

        # No template_id elements, should be None
        assert obs.template_id is None
