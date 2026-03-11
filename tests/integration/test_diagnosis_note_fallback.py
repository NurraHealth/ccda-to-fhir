"""E2E test: diagnosis notes fall back to encompassingEncounter context.

When encounter narrative tables contain diagnosis notes but no matching body
encounter entry, the notes should inherit encounter reference and date from
the document header's encompassingEncounter.
"""

from __future__ import annotations

import base64

from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.types import JSONObject


def _build_ccda_with_encompassing_encounter_and_diagnosis_notes(
    *,
    include_body_encounter: bool = False,
) -> str:
    """Build a C-CDA document with:
    - encompassingEncounter in the header
    - Encounters section with diagnosis notes in the narrative table
    - Optionally, a matching body encounter entry
    """
    enc_root = "2.16.840.1.113883.19.5"
    enc_ext = "4068"

    body_encounter_entry = ""
    if include_body_encounter:
        body_encounter_entry = f"""
        <entry typeCode="DRIV">
            <encounter classCode="ENC" moodCode="EVN">
                <templateId root="2.16.840.1.113883.10.20.22.4.49"/>
                <id root="{enc_root}" extension="{enc_ext}"/>
                <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                      codeSystemName="CPT-4" displayName="Office Visit"/>
                <text><reference value="#encounter4068"/></text>
                <effectiveTime>
                    <low value="20240122120239-0500"/>
                    <high value="20240122130000-0500"/>
                </effectiveTime>
            </encounter>
        </entry>
        """

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note"
          codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20240122120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    <recordTarget>
        <patientRole>
            <id root="test-patient-id"/>
            <patient>
                <name><given>Test</given><family>Patient</family></name>
                <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
                <birthTime value="19800101"/>
            </patient>
        </patientRole>
    </recordTarget>
    <author>
        <time value="20240122120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson>
                <name><given>Test</given><family>Author</family></name>
            </assignedPerson>
        </assignedAuthor>
    </author>
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.19.5"/>
                <name>Test Organization</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    <componentOf>
        <encompassingEncounter>
            <id root="{enc_root}" extension="{enc_ext}"/>
            <effectiveTime value="20240122120239-0500"/>
            <code code="99213" codeSystem="2.16.840.1.113883.6.12"
                  displayName="Office Visit"/>
        </encompassingEncounter>
    </componentOf>
    <component>
        <structuredBody>
            <component>
                <section>
                    <templateId root="2.16.840.1.113883.10.20.22.2.22.1"/>
                    <code code="46240-8" codeSystem="2.16.840.1.113883.6.1"
                          displayName="Encounters"/>
                    <title>Encounters</title>
                    <text>
                        <table>
                            <thead>
                                <tr>
                                    <th>Encounter ID</th>
                                    <th>Diagnosis/Indication</th>
                                    <th>Diagnosis SNOMED-CT Code</th>
                                    <th>Diagnosis Note</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td><content ID="encounter4068">4068</content></td>
                                    <td>Essential hypertension</td>
                                    <td>59621000</td>
                                    <td>Blood pressure not within goal. Referred to cardiology.</td>
                                </tr>
                                <tr>
                                    <td/>
                                    <td>Type 2 diabetes mellitus</td>
                                    <td>44054006</td>
                                    <td>HbA1c improving on current regimen.</td>
                                </tr>
                            </tbody>
                        </table>
                    </text>
                    {body_encounter_entry}
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""


def _get_diagnosis_note_doc_refs(bundle: JSONObject) -> list[JSONObject]:
    """Extract diagnosis note DocumentReferences from a bundle."""
    doc_refs = []
    for entry in bundle.get("entry", []):
        resource = entry.get("resource", {})
        if resource.get("resourceType") != "DocumentReference":
            continue
        desc = resource.get("description", "")
        if isinstance(desc, str) and desc.startswith("Diagnosis Note"):
            doc_refs.append(resource)
    return doc_refs


class TestDiagnosisNoteFallbackToEncompassingEncounter:
    """E2E: diagnosis notes fall back to encompassingEncounter context."""

    def test_notes_get_encounter_ref_and_date_from_fallback(self) -> None:
        """When no body encounter matches, notes use encompassingEncounter."""
        ccda = _build_ccda_with_encompassing_encounter_and_diagnosis_notes(
            include_body_encounter=False,
        )
        bundle = convert_document(ccda)["bundle"]
        doc_refs = _get_diagnosis_note_doc_refs(bundle)

        assert len(doc_refs) == 2

        for dr in doc_refs:
            # Each note should have a date from encompassingEncounter
            assert "date" in dr, f"Missing date on {dr['description']}"

            # Each note should have encounter context from encompassingEncounter
            context = dr.get("context", {})
            enc_refs = context.get("encounter", [])
            assert len(enc_refs) == 1, f"Missing encounter ref on {dr['description']}"
            assert enc_refs[0]["reference"].startswith("urn:uuid:")

        # Verify note content
        texts = []
        for dr in doc_refs:
            data = dr["content"][0]["attachment"]["data"]
            texts.append(base64.b64decode(data).decode("utf-8"))
        assert any("Blood pressure" in t for t in texts)
        assert any("HbA1c" in t for t in texts)

    def test_notes_use_body_encounter_when_available(self) -> None:
        """When body encounter matches, notes use that instead of fallback."""
        ccda = _build_ccda_with_encompassing_encounter_and_diagnosis_notes(
            include_body_encounter=True,
        )
        bundle = convert_document(ccda)["bundle"]
        doc_refs = _get_diagnosis_note_doc_refs(bundle)

        assert len(doc_refs) == 2

        for dr in doc_refs:
            assert "date" in dr
            context = dr.get("context", {})
            enc_refs = context.get("encounter", [])
            assert len(enc_refs) == 1

    def test_all_notes_share_same_encounter_ref_on_fallback(self) -> None:
        """All diagnosis notes should reference the same encompassingEncounter."""
        ccda = _build_ccda_with_encompassing_encounter_and_diagnosis_notes(
            include_body_encounter=False,
        )
        bundle = convert_document(ccda)["bundle"]
        doc_refs = _get_diagnosis_note_doc_refs(bundle)

        assert len(doc_refs) == 2
        enc_ref_1 = doc_refs[0]["context"]["encounter"][0]["reference"]
        enc_ref_2 = doc_refs[1]["context"]["encounter"][0]["reference"]
        assert enc_ref_1 == enc_ref_2

    def test_all_notes_share_same_date_on_fallback(self) -> None:
        """All diagnosis notes should have the same date from encompassingEncounter."""
        ccda = _build_ccda_with_encompassing_encounter_and_diagnosis_notes(
            include_body_encounter=False,
        )
        bundle = convert_document(ccda)["bundle"]
        doc_refs = _get_diagnosis_note_doc_refs(bundle)

        assert len(doc_refs) == 2
        assert doc_refs[0]["date"] == doc_refs[1]["date"]
