"""Pytest configuration and shared fixtures for integration tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from ccda_to_fhir.constants import CCDACodes, TemplateIds

# NOTE: Conversion tests are skipped until converter is implemented
# from ccda_to_fhir.convert import convert_document

# Skip conversion integration tests until the new converter is implemented
# Validation integration tests can run independently
SKIP_REASON = "Integration tests skipped until C-CDA Pydantic -> FHIR Pydantic pipeline is implemented"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Skip conversion tests (but allow validation tests)."""
    for item in items:
        # Only skip conversion tests, not validation tests
        if "/integration/" in str(item.fspath) and "conversion" in str(item.fspath):
            item.add_marker(pytest.mark.skip(reason=SKIP_REASON))

FIXTURES_DIR = Path(__file__).parent / "fixtures"
CCDA_FIXTURES_DIR = FIXTURES_DIR / "ccda"
FHIR_FIXTURES_DIR = FIXTURES_DIR / "fhir"


# Default minimal C-CDA components
DEFAULT_PATIENT = """
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
    """

DEFAULT_AUTHOR = """
    <author>
        <time value="20231215120000-0500"/>
        <assignedAuthor>
            <id root="2.16.840.1.113883.4.6" extension="999999999"/>
            <assignedPerson>
                <name><given>Test</given><family>Author</family></name>
            </assignedPerson>
        </assignedAuthor>
    </author>
    """

DEFAULT_CUSTODIAN = """
    <custodian>
        <assignedCustodian>
            <representedCustodianOrganization>
                <id root="2.16.840.1.113883.19.5"/>
                <name>Test Organization</name>
            </representedCustodianOrganization>
        </assignedCustodian>
    </custodian>
    """


def wrap_in_ccda_document(
    section_content: str,
    section_template_id: str | None = None,
    section_code: str | None = None,
    patient: str | None = None,
    author: str | None = None,
    custodian: str | None = None,
    legal_authenticator: str | None = None,
    authenticator: str | None = None,
    data_enterer: str | None = None,
    informant: str | None = None,
    information_recipient: str | None = None,
    participant: str | None = None,
    documentation_of: str | None = None,
    authorization: str | None = None,
    in_fulfillment_of: str | None = None,
) -> str:
    """Create a minimal valid C-CDA document for testing.

    This helper creates a complete C-CDA document with the provided content
    and sensible defaults for required elements.

    Args:
        section_content: The C-CDA content to wrap (e.g., act, observation, etc.)
        section_template_id: Optional section template ID
        section_code: Optional section LOINC code
        patient: Patient/recordTarget XML. Uses default minimal patient if not provided.
        author: Author XML. Uses default minimal author if not provided.
        custodian: Custodian XML. Uses default minimal custodian if not provided.
        legal_authenticator: Legal authenticator XML. Optional.
        authenticator: Authenticator XML. Optional.
        data_enterer: Data enterer XML. Optional.
        informant: Informant XML. Optional.
        information_recipient: InformationRecipient XML. Optional.
        participant: Participant XML. Optional.
        documentation_of: DocumentationOf XML. Optional.
        authorization: Authorization XML. Optional.
        in_fulfillment_of: InFulfillmentOf XML. Optional.
    """
    # Strip XML declaration if present in section_content
    import re
    section_content = re.sub(r'<\?xml[^?]*\?>\s*', '', section_content)

    # Use defaults if not provided
    patient_xml = patient if patient is not None else DEFAULT_PATIENT
    author_xml = author if author is not None else DEFAULT_AUTHOR
    custodian_xml = custodian if custodian is not None else DEFAULT_CUSTODIAN
    legal_auth_xml = legal_authenticator if legal_authenticator is not None else ""
    authenticator_xml = authenticator if authenticator is not None else ""
    data_enterer_xml = data_enterer if data_enterer is not None else ""
    informant_xml = informant if informant is not None else ""
    information_recipient_xml = information_recipient if information_recipient is not None else ""
    participant_xml = participant if participant is not None else ""
    documentation_of_xml = documentation_of if documentation_of is not None else ""
    authorization_xml = authorization if authorization is not None else ""
    in_fulfillment_of_xml = in_fulfillment_of if in_fulfillment_of is not None else ""

    # Strip XML declarations from all parameters
    patient_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', patient_xml)
    author_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', author_xml)
    custodian_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', custodian_xml)
    legal_auth_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', legal_auth_xml)
    authenticator_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', authenticator_xml)
    data_enterer_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', data_enterer_xml)
    informant_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', informant_xml)
    information_recipient_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', information_recipient_xml)
    participant_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', participant_xml)
    documentation_of_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', documentation_of_xml)
    authorization_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', authorization_xml)
    in_fulfillment_of_xml = re.sub(r'<\?xml[^?]*\?>\s*', '', in_fulfillment_of_xml)

    section_template = ""
    if section_template_id:
        section_template = f'<templateId root="{section_template_id}"/>'

    section_code_elem = ""
    if section_code:
        section_code_elem = f'<code code="{section_code}" codeSystem="2.16.840.1.113883.6.1"/>'
    elif section_template_id == TemplateIds.PROBLEM_SECTION:
        # Default to Problems section code if using Problems template
        section_code_elem = f'<code code="{CCDACodes.PROBLEM_LIST}" codeSystem="2.16.840.1.113883.6.1" displayName="Problem List"/>'
    elif section_template_id == TemplateIds.ALLERGY_SECTION:
        # Default to Allergies section code if using Allergies template
        section_code_elem = f'<code code="{CCDACodes.ALLERGIES_SECTION}" codeSystem="2.16.840.1.113883.6.1" displayName="Allergies and adverse reactions"/>'

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:sdtc="urn:hl7-org:sdtc" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    <realmCode code="US"/>
    <typeId root="2.16.840.1.113883.1.3" extension="POCD_HD000040"/>
    <templateId root="2.16.840.1.113883.10.20.22.1.1"/>
    <id root="2.16.840.1.113883.19.5.99999.1"/>
    <code code="34133-9" displayName="Summarization of Episode Note" codeSystem="2.16.840.1.113883.6.1"/>
    <effectiveTime value="20231215120000-0500"/>
    <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>
    <languageCode code="en-US"/>
    {patient_xml}
    {author_xml}
    {data_enterer_xml}
    {informant_xml}
    {custodian_xml}
    {information_recipient_xml}
    {legal_auth_xml}
    {authenticator_xml}
    {participant_xml}
    {in_fulfillment_of_xml}
    {documentation_of_xml}
    {authorization_xml}
    <component>
        <structuredBody>
            <component>
                <section>
                    {section_template}
                    {section_code_elem}
                    <entry>
                        {section_content}
                    </entry>
                </section>
            </component>
        </structuredBody>
    </component>
</ClinicalDocument>"""


# @pytest.fixture
# def converter() -> type:
#     """Provide the convert_document function for integration tests."""
#     return convert_document


@pytest.fixture
def ccda_patient() -> str:
    """Load C-CDA patient fixture."""
    return (CCDA_FIXTURES_DIR / "patient.xml").read_text()


@pytest.fixture
def fhir_patient() -> dict[str, Any]:
    """Load expected FHIR patient fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "patient.json").read_text())


@pytest.fixture
def ccda_allergy() -> str:
    """Load C-CDA allergy fixture."""
    return (CCDA_FIXTURES_DIR / "allergy.xml").read_text()


@pytest.fixture
def fhir_allergy() -> dict[str, Any]:
    """Load expected FHIR allergy fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "allergy.json").read_text())


@pytest.fixture
def ccda_problem() -> str:
    """Load C-CDA problem fixture."""
    return (CCDA_FIXTURES_DIR / "problem.xml").read_text()


@pytest.fixture
def fhir_problem() -> dict[str, Any]:
    """Load expected FHIR problem/condition fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "problem.json").read_text())


@pytest.fixture
def ccda_immunization() -> str:
    """Load C-CDA immunization fixture."""
    return (CCDA_FIXTURES_DIR / "immunization.xml").read_text()


@pytest.fixture
def fhir_immunization() -> dict[str, Any]:
    """Load expected FHIR immunization fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "immunization.json").read_text())


@pytest.fixture
def ccda_medication() -> str:
    """Load C-CDA medication fixture."""
    return (CCDA_FIXTURES_DIR / "medication.xml").read_text()


@pytest.fixture
def fhir_medication() -> dict[str, Any]:
    """Load expected FHIR medication request fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "medication.json").read_text())


@pytest.fixture
def ccda_medication_bedtime_hs() -> str:
    """Load C-CDA medication with EIVL_TS bedtime (HS) timing."""
    return (CCDA_FIXTURES_DIR / "medication_bedtime_hs.xml").read_text()


@pytest.fixture
def ccda_medication_before_breakfast_acm() -> str:
    """Load C-CDA medication with EIVL_TS before breakfast (ACM) timing."""
    return (CCDA_FIXTURES_DIR / "medication_before_breakfast_acm.xml").read_text()


@pytest.fixture
def ccda_medication_with_offset() -> str:
    """Load C-CDA medication with EIVL_TS and offset timing."""
    return (CCDA_FIXTURES_DIR / "medication_with_offset.xml").read_text()


@pytest.fixture
def ccda_medication_pivl_eivl_combined() -> str:
    """Load C-CDA medication with combined PIVL_TS and EIVL_TS timing."""
    return (CCDA_FIXTURES_DIR / "medication_pivl_eivl_combined.xml").read_text()


@pytest.fixture
def ccda_medication_dispense_no_product_code() -> str:
    """C-CDA Medication Dispense with nullFlavor product code (tests fallback)."""
    return """
<substanceAdministration classCode="SBADM" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.16" extension="2014-06-09"/>
    <id root="medication-activity-test"/>
    <statusCode code="completed"/>
    <effectiveTime xsi:type="IVL_TS">
        <low value="20100101"/>
    </effectiveTime>
    <doseQuantity value="1"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
            <manufacturedMaterial>
                <code code="197454" codeSystem="2.16.840.1.113883.6.88" displayName="Lisinopril 10 MG Oral Tablet">
                    <originalText>Lisinopril 10mg</originalText>
                </code>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
    <entryRelationship typeCode="REFR">
        <supply classCode="SPLY" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.18" extension="2014-06-09"/>
            <id root="dispense-no-code-test"/>
            <statusCode code="completed"/>
            <effectiveTime value="20100115"/>
            <quantity value="30"/>
            <product>
                <manufacturedProduct classCode="MANU">
                    <templateId root="2.16.840.1.113883.10.20.22.4.23" extension="2014-06-09"/>
                    <manufacturedMaterial>
                        <code nullFlavor="UNK"/>
                    </manufacturedMaterial>
                </manufacturedProduct>
            </product>
        </supply>
    </entryRelationship>
</substanceAdministration>
    """


@pytest.fixture
def ccda_procedure() -> str:
    """Load C-CDA procedure fixture."""
    return (CCDA_FIXTURES_DIR / "procedure.xml").read_text()


@pytest.fixture
def fhir_procedure() -> dict[str, Any]:
    """Load expected FHIR procedure fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "procedure.json").read_text())


@pytest.fixture
def ccda_procedure_with_body_site() -> str:
    """Load C-CDA procedure with body site."""
    return (CCDA_FIXTURES_DIR / "procedure_with_body_site.xml").read_text()


@pytest.fixture
def ccda_procedure_with_performer() -> str:
    """Load C-CDA procedure with performer."""
    return (CCDA_FIXTURES_DIR / "procedure_with_performer.xml").read_text()


@pytest.fixture
def ccda_procedure_with_location() -> str:
    """Load C-CDA procedure with location participant."""
    return (CCDA_FIXTURES_DIR / "procedure_with_location.xml").read_text()


@pytest.fixture
def ccda_procedure_with_reason() -> str:
    """Load C-CDA procedure with reason code."""
    return (CCDA_FIXTURES_DIR / "procedure_with_reason.xml").read_text()


@pytest.fixture
def ccda_procedure_with_reason_reference() -> str:
    """Load C-CDA procedure with inline Problem Observation (creates reasonCode)."""
    return (CCDA_FIXTURES_DIR / "procedure_with_reason_reference.xml").read_text()


@pytest.fixture
def ccda_procedure_with_problem_reference() -> str:
    """Load C-CDA document with Problems section and Procedure referencing it (creates reasonReference)."""
    return (CCDA_FIXTURES_DIR / "procedure_with_problem_reference.xml").read_text()


@pytest.fixture
def ccda_pregnancy_intention() -> str:
    """Load C-CDA pregnancy intention observation."""
    return (CCDA_FIXTURES_DIR / "pregnancy_intention.xml").read_text()


@pytest.fixture
def ccda_procedure_with_author() -> str:
    """Load C-CDA procedure with author/recorder."""
    return (CCDA_FIXTURES_DIR / "procedure_with_author.xml").read_text()


@pytest.fixture
def ccda_procedure_with_author_and_organization() -> str:
    """Load C-CDA procedure with author that has representedOrganization."""
    return (CCDA_FIXTURES_DIR / "procedure_with_author_and_organization.xml").read_text()


@pytest.fixture
def ccda_procedure_with_outcome() -> str:
    """Load C-CDA procedure with outcome."""
    return (CCDA_FIXTURES_DIR / "procedure_with_outcome.xml").read_text()


@pytest.fixture
def ccda_procedure_with_complications() -> str:
    """Load C-CDA procedure with complications."""
    return (CCDA_FIXTURES_DIR / "procedure_with_complications.xml").read_text()


@pytest.fixture
def ccda_procedure_with_followup() -> str:
    """Load C-CDA procedure with follow-up instructions."""
    return (CCDA_FIXTURES_DIR / "procedure_with_followup.xml").read_text()


@pytest.fixture
def ccda_procedure_with_notes() -> str:
    """Load C-CDA procedure with notes (text and Comment Activity)."""
    return (CCDA_FIXTURES_DIR / "procedure_with_notes.xml").read_text()


@pytest.fixture
def ccda_procedure_observation() -> str:
    """Load C-CDA Procedure Activity Observation fixture."""
    return (CCDA_FIXTURES_DIR / "procedure_observation.xml").read_text()


@pytest.fixture
def ccda_procedure_observation_with_details() -> str:
    """Load C-CDA Procedure Activity Observation with full details."""
    return (CCDA_FIXTURES_DIR / "procedure_observation_with_details.xml").read_text()


@pytest.fixture
def ccda_result() -> str:
    """Load C-CDA result/lab fixture."""
    return (CCDA_FIXTURES_DIR / "result.xml").read_text()


@pytest.fixture
def ccda_result_with_author() -> str:
    """Load C-CDA result with author/recorder."""
    return (CCDA_FIXTURES_DIR / "result_with_author.xml").read_text()


@pytest.fixture
def ccda_result_multiple_authors() -> str:
    """Load C-CDA result with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "result_multiple_authors.xml").read_text()


@pytest.fixture
def fhir_result() -> dict[str, Any]:
    """Load expected FHIR diagnostic report fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "result.json").read_text())


@pytest.fixture
def ccda_encounter() -> str:
    """Load C-CDA encounter fixture."""
    return (CCDA_FIXTURES_DIR / "encounter.xml").read_text()


@pytest.fixture
def fhir_encounter() -> dict[str, Any]:
    """Load expected FHIR encounter fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "encounter.json").read_text())


@pytest.fixture
def ccda_encounter_with_status_code() -> str:
    """Load C-CDA encounter with statusCode."""
    return (CCDA_FIXTURES_DIR / "encounter_with_status_code.xml").read_text()


@pytest.fixture
def ccda_encounter_inpatient_v3() -> str:
    """Load C-CDA encounter with V3 ActCode class."""
    return (CCDA_FIXTURES_DIR / "encounter_inpatient_v3.xml").read_text()


@pytest.fixture
def ccda_encounter_with_function_code() -> str:
    """Load C-CDA encounter with performer functionCode."""
    return (CCDA_FIXTURES_DIR / "encounter_with_function_code.xml").read_text()


@pytest.fixture
def ccda_encounter_with_location() -> str:
    """Load C-CDA encounter with location participant."""
    return (CCDA_FIXTURES_DIR / "encounter_with_location.xml").read_text()


@pytest.fixture
def ccda_encounter_location_with_time_period() -> str:
    """Load C-CDA encounter with location participant with complete time period."""
    return (CCDA_FIXTURES_DIR / "encounter_location_with_time_period.xml").read_text()


@pytest.fixture
def ccda_encounter_location_active() -> str:
    """Load C-CDA encounter with location participant with only start time (active)."""
    return (CCDA_FIXTURES_DIR / "encounter_location_active.xml").read_text()


@pytest.fixture
def ccda_encounter_location_no_time_in_progress() -> str:
    """Load C-CDA encounter with location participant without time (in-progress encounter)."""
    return (CCDA_FIXTURES_DIR / "encounter_location_no_time_in_progress.xml").read_text()


@pytest.fixture
def ccda_encounter_location_planned() -> str:
    """Load C-CDA encounter with location participant (planned encounter)."""
    return (CCDA_FIXTURES_DIR / "encounter_location_planned.xml").read_text()


@pytest.fixture
def ccda_encounter_with_discharge() -> str:
    """Load C-CDA encounter with discharge disposition."""
    return (CCDA_FIXTURES_DIR / "encounter_with_discharge.xml").read_text()


@pytest.fixture
def ccda_encounter_with_author() -> str:
    """Load C-CDA encounter with author/recorder."""
    return (CCDA_FIXTURES_DIR / "encounter_with_author.xml").read_text()


@pytest.fixture
def ccda_encounter_multiple_authors() -> str:
    """Load C-CDA encounter with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "encounter_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_encounter_with_reason_reference() -> str:
    """Load C-CDA encounter with inline Problem Observation (creates reasonCode)."""
    return (CCDA_FIXTURES_DIR / "encounter_with_reason_reference.xml").read_text()


@pytest.fixture
def ccda_encounter_with_problem_reference() -> str:
    """Load C-CDA document with Problems section and Encounter referencing it (creates reasonReference)."""
    return (CCDA_FIXTURES_DIR / "encounter_with_problem_reference.xml").read_text()


@pytest.fixture
def ccda_header_encounter_only() -> str:
    """Load C-CDA document with header encompassingEncounter only (no body encounters)."""
    return (CCDA_FIXTURES_DIR / "header_encounter_only.xml").read_text()


@pytest.fixture
def ccda_header_and_body_encounter() -> str:
    """Load C-CDA document with both header and body encounters with duplicate ID."""
    return (CCDA_FIXTURES_DIR / "header_and_body_encounter.xml").read_text()


@pytest.fixture
def ccda_note() -> str:
    """Load C-CDA note fixture."""
    return (CCDA_FIXTURES_DIR / "note.xml").read_text()


@pytest.fixture
def fhir_note() -> dict[str, Any]:
    """Load expected FHIR document reference fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "note.json").read_text())


@pytest.fixture
def ccda_vital_signs() -> str:
    """Load C-CDA vital signs fixture."""
    return (CCDA_FIXTURES_DIR / "vital_signs.xml").read_text()


@pytest.fixture
def fhir_vital_signs() -> dict[str, Any]:
    """Load expected FHIR vital signs observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "vital_signs.json").read_text())


@pytest.fixture
def ccda_smoking_status() -> str:
    """Load C-CDA smoking status fixture."""
    return (CCDA_FIXTURES_DIR / "smoking_status.xml").read_text()


@pytest.fixture
def ccda_smoking_status_with_author() -> str:
    """Load C-CDA smoking status with author."""
    return (CCDA_FIXTURES_DIR / "smoking_status_with_author.xml").read_text()


@pytest.fixture
def ccda_smoking_status_multiple_authors() -> str:
    """Load C-CDA smoking status with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "smoking_status_multiple_authors.xml").read_text()


@pytest.fixture
def fhir_smoking_status() -> dict[str, Any]:
    """Load expected FHIR smoking status observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "smoking_status.json").read_text())


@pytest.fixture
def ccda_pregnancy() -> str:
    """Load C-CDA pregnancy observation fixture."""
    return (CCDA_FIXTURES_DIR / "pregnancy.xml").read_text()


@pytest.fixture
def ccda_pregnancy_no_edd() -> str:
    """Load C-CDA pregnancy observation without EDD fixture."""
    return (CCDA_FIXTURES_DIR / "pregnancy_no_edd.xml").read_text()


@pytest.fixture
def ccda_pregnancy_loinc() -> str:
    """Load C-CDA pregnancy observation with LOINC code (C-CDA 4.0+)."""
    return (CCDA_FIXTURES_DIR / "pregnancy_loinc.xml").read_text()


@pytest.fixture
def fhir_pregnancy() -> dict[str, Any]:
    """Load expected FHIR pregnancy observation fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "pregnancy.json").read_text())


@pytest.fixture
def ccda_pregnancy_with_gestational_age() -> str:
    """Load C-CDA pregnancy observation with gestational age component."""
    return (CCDA_FIXTURES_DIR / "pregnancy_with_gestational_age.xml").read_text()


@pytest.fixture
def ccda_pregnancy_with_lmp() -> str:
    """Load C-CDA pregnancy observation with last menstrual period component."""
    return (CCDA_FIXTURES_DIR / "pregnancy_with_lmp.xml").read_text()


@pytest.fixture
def ccda_pregnancy_comprehensive() -> str:
    """Load C-CDA pregnancy observation with all components (EDD, LMP, gestational age)."""
    return (CCDA_FIXTURES_DIR / "pregnancy_comprehensive.xml").read_text()


@pytest.fixture
def ccda_author() -> str:
    """Load C-CDA author fixture."""
    return (CCDA_FIXTURES_DIR / "author.xml").read_text()


@pytest.fixture
def fhir_practitioner() -> dict[str, Any]:
    """Load expected FHIR practitioner fixture."""
    return json.loads((FHIR_FIXTURES_DIR / "practitioner.json").read_text())


# Condition test fixtures for untested features
@pytest.fixture
def ccda_condition_with_abatement() -> str:
    """Load C-CDA condition with abatement date."""
    return (CCDA_FIXTURES_DIR / "condition_with_abatement.xml").read_text()


@pytest.fixture
def ccda_condition_with_abatement_unknown() -> str:
    """Load C-CDA condition with unknown abatement date (nullFlavor=UNK)."""
    return (CCDA_FIXTURES_DIR / "condition_with_abatement_unknown.xml").read_text()


@pytest.fixture
def ccda_condition_with_body_site() -> str:
    """Load C-CDA condition with body site."""
    return (CCDA_FIXTURES_DIR / "condition_with_body_site.xml").read_text()


@pytest.fixture
def ccda_condition_with_severity() -> str:
    """Load C-CDA condition with severity."""
    return (CCDA_FIXTURES_DIR / "condition_with_severity.xml").read_text()


@pytest.fixture
def ccda_condition_with_note() -> str:
    """Load C-CDA condition with note from text element."""
    return (CCDA_FIXTURES_DIR / "condition_with_note.xml").read_text()


@pytest.fixture
def ccda_condition_negated() -> str:
    """Load C-CDA condition with negationInd=true."""
    return (CCDA_FIXTURES_DIR / "condition_negated.xml").read_text()


@pytest.fixture
def ccda_problem_no_known_problems() -> str:
    """Load C-CDA problem with negationInd=true and generic problem code (no known problems)."""
    return (CCDA_FIXTURES_DIR / "problem_no_known_problems.xml").read_text()


@pytest.fixture
def ccda_condition_with_asserted_date() -> str:
    """Load C-CDA condition with Date of Diagnosis (assertedDate extension)."""
    return (CCDA_FIXTURES_DIR / "condition_with_asserted_date.xml").read_text()


@pytest.fixture
def ccda_condition_with_comment() -> str:
    """Load C-CDA condition with Comment Activity."""
    return (CCDA_FIXTURES_DIR / "condition_with_comment.xml").read_text()


@pytest.fixture
def ccda_condition_with_evidence() -> str:
    """Load C-CDA condition with supporting observations (evidence)."""
    return (CCDA_FIXTURES_DIR / "condition_with_evidence.xml").read_text()


@pytest.fixture
def ccda_condition_with_assessment_scale() -> str:
    """Load C-CDA condition with assessment scale observation (typeCode=COMP)."""
    return (CCDA_FIXTURES_DIR / "condition_with_assessment_scale.xml").read_text()


# AllergyIntolerance test fixtures for untested features
@pytest.fixture
def ccda_allergy_with_type() -> str:
    """Load C-CDA allergy with type field (allergy vs intolerance)."""
    return (CCDA_FIXTURES_DIR / "allergy_with_type.xml").read_text()


@pytest.fixture
def ccda_allergy_with_verification_status() -> str:
    """Load C-CDA allergy with verification status (confirmed)."""
    return (CCDA_FIXTURES_DIR / "allergy_with_verification_status.xml").read_text()


@pytest.fixture
def ccda_allergy_with_criticality() -> str:
    """Load C-CDA allergy with Criticality Observation."""
    return (CCDA_FIXTURES_DIR / "allergy_with_criticality.xml").read_text()


@pytest.fixture
def ccda_allergy_with_abatement() -> str:
    """Load C-CDA allergy with abatement extension (effectiveTime/high)."""
    return (CCDA_FIXTURES_DIR / "allergy_with_abatement.xml").read_text()


@pytest.fixture
def ccda_allergy_with_recorded_date() -> str:
    """Load C-CDA allergy with author/time for recordedDate."""
    return (CCDA_FIXTURES_DIR / "allergy_with_recorded_date.xml").read_text()


@pytest.fixture
def ccda_allergy_with_comment() -> str:
    """Load C-CDA allergy with Comment Activity."""
    return (CCDA_FIXTURES_DIR / "allergy_with_comment.xml").read_text()


# New fixtures for recent edge case coverage
@pytest.fixture
def ccda_medication_negated() -> str:
    """Load C-CDA medication with negationInd=true."""
    return (CCDA_FIXTURES_DIR / "medication_negated.xml").read_text()


@pytest.fixture
def ccda_immunization_negated() -> str:
    """Load C-CDA immunization with negationInd=true."""
    return (CCDA_FIXTURES_DIR / "immunization_negated.xml").read_text()


@pytest.fixture
def ccda_immunization_multiple_authors() -> str:
    """Load C-CDA immunization with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "immunization_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_immunization_planned() -> str:
    """Load C-CDA planned immunization (moodCode='INT')."""
    return (CCDA_FIXTURES_DIR / "immunization_planned.xml").read_text()


@pytest.fixture
def ccda_immunization_with_comment() -> str:
    """Load C-CDA immunization with Comment Activity."""
    return (CCDA_FIXTURES_DIR / "immunization_with_comment.xml").read_text()


@pytest.fixture
def ccda_immunization_with_supporting_observations() -> str:
    """Load C-CDA immunization with SPRT/COMP entry relationships."""
    return (CCDA_FIXTURES_DIR / "immunization_with_supporting_observations.xml").read_text()


@pytest.fixture
def ccda_immunization_no_vaccine_code() -> str:
    """C-CDA Immunization with nullFlavor vaccine code (tests fallback)."""
    return """
<substanceAdministration classCode="SBADM" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.52" extension="2015-08-01"/>
    <id root="immunization-no-code-test"/>
    <statusCode code="completed"/>
    <effectiveTime value="20100815"/>
    <consumable>
        <manufacturedProduct classCode="MANU">
            <templateId root="2.16.840.1.113883.10.20.22.4.54" extension="2014-06-09"/>
            <manufacturedMaterial>
                <code nullFlavor="UNK"/>
            </manufacturedMaterial>
        </manufacturedProduct>
    </consumable>
</substanceAdministration>
    """


@pytest.fixture
def ccda_observation_ivl_pq() -> str:
    """Load C-CDA observation with IVL_PQ value."""
    return (CCDA_FIXTURES_DIR / "observation_ivl_pq.xml").read_text()


@pytest.fixture
def ccda_procedure_negated() -> str:
    """Load C-CDA procedure with negationInd=true."""
    return (CCDA_FIXTURES_DIR / "procedure_negated.xml").read_text()


@pytest.fixture
def ccda_problem_multiple_authors() -> str:
    """Load C-CDA problem with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "problem_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_problem_with_diagnosis_type() -> str:
    """Load C-CDA problem with diagnosis type code (282291009) for secondary category testing."""
    return (CCDA_FIXTURES_DIR / "problem_with_diagnosis_type.xml").read_text()


@pytest.fixture
def ccda_allergy_multiple_authors() -> str:
    """Load C-CDA allergy with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "allergy_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_allergy_with_allergy_level_severity() -> str:
    """Load C-CDA allergy with severity at allergy level only (Scenario A)."""
    return (CCDA_FIXTURES_DIR / "allergy_with_allergy_level_severity.xml").read_text()


@pytest.fixture
def ccda_allergy_with_both_level_severity() -> str:
    """Load C-CDA allergy with severity at both allergy and reaction levels (Scenario B)."""
    return (CCDA_FIXTURES_DIR / "allergy_with_both_level_severity.xml").read_text()


@pytest.fixture
def ccda_medication_multiple_authors() -> str:
    """Load C-CDA medication with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "medication_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_medication_with_start_date() -> str:
    """Load C-CDA medication with IVL_TS start date only (boundsPeriod.start)."""
    return (CCDA_FIXTURES_DIR / "medication_with_start_date.xml").read_text()


@pytest.fixture
def ccda_medication_with_start_end_dates() -> str:
    """Load C-CDA medication with IVL_TS start and end dates (boundsPeriod)."""
    return (CCDA_FIXTURES_DIR / "medication_with_start_end_dates.xml").read_text()


@pytest.fixture
def ccda_medication_bounds_period_with_frequency() -> str:
    """Load C-CDA medication with IVL_TS boundsPeriod and PIVL_TS frequency."""
    return (CCDA_FIXTURES_DIR / "medication_bounds_period_with_frequency.xml").read_text()


@pytest.fixture
def ccda_medication_with_sig() -> str:
    """Load C-CDA medication with free text sig (dosageInstruction.text)."""
    return (CCDA_FIXTURES_DIR / "medication_with_sig.xml").read_text()


@pytest.fixture
def ccda_medication_with_sig_and_patient_instruction() -> str:
    """Load C-CDA medication with both free text sig and patient instruction."""
    return (CCDA_FIXTURES_DIR / "medication_with_sig_and_patient_instruction.xml").read_text()


@pytest.fixture
def ccda_procedure_multiple_authors() -> str:
    """Load C-CDA procedure with multiple authors at different times."""
    return (CCDA_FIXTURES_DIR / "procedure_multiple_authors.xml").read_text()


@pytest.fixture
def ccda_procedure_activity_act() -> str:
    """Load C-CDA Procedure Activity Act fixture."""
    return (CCDA_FIXTURES_DIR / "procedure_activity_act.xml").read_text()


@pytest.fixture
def ccda_procedure_no_effective_time() -> str:
    """Load C-CDA procedure without effectiveTime (tests data-absent-reason extension)."""
    return (CCDA_FIXTURES_DIR / "procedure_no_effective_time.xml").read_text()


@pytest.fixture
def ccda_goal_weight_loss() -> str:
    """C-CDA Goal Observation for weight loss with quantity target."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="db734647-fc99-424c-a864-7e3cda82e703"/>
    <code code="289169006" codeSystem="2.16.840.1.113883.6.96" displayName="Weight loss"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
        <high value="20240715"/>
    </effectiveTime>
    <author>
        <time value="20240115"/>
        <assignedAuthor>
            <id root="patient-system" extension="patient-123"/>
        </assignedAuthor>
    </author>
    <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
            <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
            <code code="29463-7" codeSystem="2.16.840.1.113883.6.1" displayName="Body weight"/>
            <value xsi:type="PQ" value="160" unit="[lb_av]"/>
        </observation>
    </entryRelationship>
</observation>
    """


@pytest.fixture
def ccda_goal_with_priority() -> str:
    """C-CDA Goal Observation with priority preference."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-priority-test"/>
    <code code="289169006" codeSystem="2.16.840.1.113883.6.96" displayName="Weight loss"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
    <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.143"/>
            <code code="225773000" codeSystem="2.16.840.1.113883.6.96" displayName="Preference"/>
            <value xsi:type="CD" code="high-priority"
                   codeSystem="2.16.840.1.113883.4.642.3.275"
                   displayName="High Priority"/>
        </observation>
    </entryRelationship>
</observation>
    """


@pytest.fixture
def ccda_goal_with_progress() -> str:
    """C-CDA Goal Observation with progress/achievement status."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-progress-test"/>
    <code code="289169006" codeSystem="2.16.840.1.113883.6.96" displayName="Weight loss"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
    <entryRelationship typeCode="REFR">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.110"/>
            <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
            <value xsi:type="CD" code="in-progress"
                   codeSystem="2.16.840.1.113883.4.642.3.251"
                   displayName="In Progress"/>
        </observation>
    </entryRelationship>
</observation>
    """


@pytest.fixture
def ccda_goal_with_health_concern() -> str:
    """C-CDA Goal Observation with health concern reference."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-concern-test"/>
    <code code="289169006" codeSystem="2.16.840.1.113883.6.96" displayName="Weight loss"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
    <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
            <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
            <id root="condition-obesity-123"/>
            <code code="75310-3" codeSystem="2.16.840.1.113883.6.1" displayName="Health Concern"/>
            <value xsi:type="CD" code="414915002" codeSystem="2.16.840.1.113883.6.96" displayName="Obesity"/>
        </observation>
    </entryRelationship>
</observation>
    """


@pytest.fixture
def ccda_goal_blood_pressure() -> str:
    """C-CDA Goal Observation with range target (blood pressure)."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-bp-test"/>
    <code code="85354-9" codeSystem="2.16.840.1.113883.6.1" displayName="Blood pressure panel"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
    <entryRelationship typeCode="COMP">
        <observation classCode="OBS" moodCode="GOL">
            <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
            <code code="8480-6" codeSystem="2.16.840.1.113883.6.1" displayName="Systolic blood pressure"/>
            <value xsi:type="IVL_PQ">
                <high value="140" unit="mm[Hg]"/>
            </value>
        </observation>
    </entryRelationship>
</observation>
    """


@pytest.fixture
def ccda_goal_qualitative() -> str:
    """C-CDA Goal Observation without measurable target (qualitative)."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-qualitative-test"/>
    <code code="713458007" codeSystem="2.16.840.1.113883.6.96" displayName="Improving functional status"/>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
</observation>
    """


@pytest.fixture
def ccda_goal_narrative_only() -> str:
    """C-CDA Goal with nullFlavor code and narrative text only (tests fallback)."""
    return """
<observation classCode="OBS" moodCode="GOL">
    <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
    <id root="goal-narrative-test"/>
    <code nullFlavor="UNK"/>
    <text>
        <reference value="#goal-narrative-123"/>
    </text>
    <statusCode code="active"/>
    <effectiveTime>
        <low value="20240115"/>
    </effectiveTime>
</observation>
    """
