"""Unit tests for encounter deduplication logic.

Tests various scenarios where header encompassingEncounter and body Encounter Activity
should be deduplicated or kept separate.
"""

from ccda_to_fhir.convert import convert_document


class TestEncounterDeduplication:
    """Test encounter deduplication between header and body."""

    def test_same_id_exact_match_deduplicates(self):
        """Header and body with exact same ID should create ONE encounter."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="encounter-123"/>
      <effectiveTime value="20250822"/>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Encounters</title>
          <text>Test</text>
          <entry>
            <encounter classCode="ENC" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
              <id root="encounter-123"/>
              <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
              <effectiveTime>
                <low value="20250822120000-0500"/>
                <high value="20250822130000-0500"/>
              </effectiveTime>
            </encounter>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 1, "Should create exactly ONE encounter (deduplicated)"
        encounter = encounters[0]['resource']
        # Should have body's rich data (type code and precise times)
        assert encounter.get('type') is not None, "Should have type from body"
        # Check that we have the body's precise timestamp (not just date)
        assert 'T12:00:00' in encounter['period']['start'], "Should have precise start time from body"

    def test_same_day_different_ids_deduplicates(self):
        """Header and body on same day with different IDs should create ONE encounter."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="header-encounter-id"/>
      <effectiveTime value="20250822"/>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Encounters</title>
          <text>Test</text>
          <entry>
            <encounter classCode="ENC" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
              <id root="body-encounter-id"/>
              <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
              <effectiveTime>
                <low value="20250822120239-0500"/>
                <high value="20250822131347-0500"/>
              </effectiveTime>
            </encounter>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 1, "Should create ONE encounter (same day deduplication)"
        encounter = encounters[0]['resource']
        # Should prefer body's precise times
        assert '12:02:39' in encounter['period']['start'], "Should use body's precise start time"
        assert encounter.get('type') is not None, "Should have type from body"

    def test_different_days_creates_two_encounters(self):
        """Header and body on different days should create TWO encounters."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250815"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="header-encounter-id"/>
      <effectiveTime value="20250815"/>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Encounters</title>
          <text>Test</text>
          <entry>
            <encounter classCode="ENC" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
              <id root="body-encounter-id"/>
              <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
              <effectiveTime>
                <low value="20250822120239-0500"/>
                <high value="20250822131347-0500"/>
              </effectiveTime>
            </encounter>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 2, "Should create TWO encounters (different dates)"
        dates = {e['resource']['period']['start'][:10] for e in encounters}
        assert '2025-08-15' in dates, "Should have header encounter on 2025-08-15"
        assert '2025-08-22' in dates, "Should have body encounter on 2025-08-22"

    def test_only_header_creates_one_encounter(self):
        """Only header encompassingEncounter should create ONE encounter."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="encounter-123"/>
      <effectiveTime value="20250822"/>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Allergies</title>
          <text>None</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 1, "Should create exactly ONE encounter from header"

    def test_only_body_creates_one_encounter(self):
        """Only body Encounter Activity should create ONE encounter."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Encounters</title>
          <text>Test</text>
          <entry>
            <encounter classCode="ENC" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
              <id root="encounter-123"/>
              <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
              <effectiveTime>
                <low value="20250822120239"/>
                <high value="20250822131347"/>
              </effectiveTime>
            </encounter>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 1, "Should create exactly ONE encounter from body"

    def test_header_with_participant_merges_into_body(self):
        """Header with participant data should merge participant into body encounter."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <componentOf>
    <encompassingEncounter>
      <id root="header-enc"/>
      <effectiveTime value="20250822"/>
      <encounterParticipant typeCode="ATND">
        <assignedEntity>
          <id extension="1234567890" root="2.16.840.1.113883.4.6"/>
          <assignedPerson>
            <name><family>Cheng</family><given>Henry</given></name>
          </assignedPerson>
        </assignedEntity>
      </encounterParticipant>
    </encompassingEncounter>
  </componentOf>
  <component>
    <structuredBody>
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
          <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Encounters</title>
          <text>Test</text>
          <entry>
            <encounter classCode="ENC" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
              <id root="body-enc"/>
              <code code="99213" codeSystem="2.16.840.1.113883.6.12"/>
              <effectiveTime>
                <low value="20250822120239-0500"/>
                <high value="20250822131347-0500"/>
              </effectiveTime>
            </encounter>
          </entry>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 1, "Should create ONE encounter (merged)"
        encounter = encounters[0]['resource']

        # Should have body's precise times and type
        assert '12:02:39' in encounter['period']['start'], "Should have body's precise time"
        assert encounter.get('type') is not None, "Should have type from body"

        # Should have participant from header
        assert encounter.get('participant') is not None, "Should have participant from header"
        assert len(encounter['participant']) > 0, "Should have at least one participant"

    def test_no_encounters_creates_none(self):
        """Document with no encounters should create zero Encounter resources."""
        ccda = """<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3">
  <realmCode code="US"/>
  <typeId extension="POCD_HD000040" root="2.16.840.1.113883.1.3"/>
  <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
  <id root="test-doc"/>
  <code code="34133-9" codeSystem="2.16.840.1.113883.6.1"/>
  <title>Test</title>
  <effectiveTime value="20250822"/>
  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
  <recordTarget>
    <patientRole>
      <id root="patient-123"/>
      <patient><name><family>Test</family></name></patient>
    </patientRole>
  </recordTarget>
  <author>
    <time value="20250822"/>
    <assignedAuthor>
      <id root="author-123"/>
    </assignedAuthor>
  </author>
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="custodian-123"/>
        <name>Test Organization</name>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>
  <component>
    <structuredBody>
      <component>
        <section>
          <code code="48765-2" codeSystem="2.16.840.1.113883.6.1"/>
          <title>Allergies</title>
          <text>None</text>
        </section>
      </component>
    </structuredBody>
  </component>
</ClinicalDocument>"""

        result = convert_document(ccda)
        encounters = [e for e in result['bundle']['entry']
                     if e['resource']['resourceType'] == 'Encounter']

        assert len(encounters) == 0, "Should create zero encounters"
