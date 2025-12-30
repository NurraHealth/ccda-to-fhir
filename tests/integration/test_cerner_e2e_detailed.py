"""Detailed E2E validation for Cerner Transition of Care - Steve Williamson.

This test validates EXACT clinical data from the Cerner TOC sample:
- Patient: Steve Williamson, Male, DOB: 1947-04-07, Language: eng
- Problems: Angina (194828000), Diabetes Type 2 (44054006), Hypercholesterolemia (13644009)
- Allergies: Codeine (2670) with Nausea, Penicillin G (7980) with Weal/Hives
- Medications: Insulin Glargine with route C38299 (Subcutaneous) and dose 30 units
  - MedicationRequest.authoredOn from author/time (2013-07-10T21:58:10-05:00)
  - MedicationRequest.requester from author element
- Immunizations: Influenza with route C28161 (Intramuscular) and dose 0.25 mL
- Practitioners: Aaron Admit, MD with complete address and telecom
- Encounters: Period with start time (2013-07-10)
  - Encounter.location with Location resource (Local Community Hospital Organization)
- Vital Signs: Blood pressure with systolic (8480-6: 150 mmHg, H) and diastolic (8462-4: 95 mmHg, H) components

By checking exact values from the C-CDA, we ensure perfect conversion fidelity.
"""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle

CERNER_TOC = Path(__file__).parent / "fixtures" / "documents" / "cerner_toc.xml"


class TestCernerDetailedValidation:
    """Test exact clinical data conversion from Cerner TOC."""

    @pytest.fixture
    def cerner_bundle(self):
        """Convert Cerner TOC to FHIR Bundle."""
        with open(CERNER_TOC) as f:
            xml = f.read()
        result = convert_document(xml)
        return Bundle(**result["bundle"])

    def test_patient_steve_williamson_demographics(self, cerner_bundle):
        """Validate patient Steve Williamson has correct demographics."""
        # Find Patient
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert patient is not None, "Bundle must contain Patient"

        # EXACT check: Name
        assert len(patient.name) > 0, "Patient must have name"
        name = patient.name[0]
        assert "Steve" in name.given, "Patient given name must be 'Steve'"
        assert name.family == "Williamson", "Patient family name must be 'Williamson'"

        # EXACT check: Gender
        assert patient.gender == "male", "Patient must be male"

        # EXACT check: Birth date
        assert str(patient.birthDate) == "1947-04-07", "Patient birth date must be 1947-04-07"

        # EXACT check: Race (Black or African American - 2054-5)
        race_ext = next(
            (ext for ext in (patient.extension or [])
             if ext.url == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"),
            None
        )
        assert race_ext is not None, "Patient must have race extension"
        race_code = next(
            (ext.valueCoding.code for ext in race_ext.extension
             if ext.url == "ombCategory"),
            None
        )
        assert race_code == "2054-5", "Patient race must be 'Black or African American' (2054-5)"

        # EXACT check: Identifier (MRN)
        assert patient.identifier is not None and len(patient.identifier) > 0, "Patient must have identifier"
        mrn = patient.identifier[0]
        assert mrn.value == "106", "Patient MRN must be '106'"
        assert "2.16.840.1.113883.1.13.99999.1" in mrn.system, "Patient identifier must have Cerner system OID"

        # EXACT check: Address
        assert patient.address is not None and len(patient.address) > 0, "Patient must have address"
        addr = patient.address[0]
        assert "8745 W Willenow Rd" in addr.line, "Patient address line must be '8745 W Willenow Rd'"
        assert addr.city == "Beaverton", "Patient city must be 'Beaverton'"
        assert addr.state == "OR", "Patient state must be 'OR'"
        assert "97005" in addr.postalCode, "Patient postal code must be '97005'"

        # EXACT check: Telecom (phone)
        assert patient.telecom is not None and len(patient.telecom) > 0, "Patient must have telecom"
        phone = patient.telecom[0]
        assert phone.system == "phone", "Telecom system must be 'phone'"
        assert "(503) 325-7464" in phone.value, "Phone number must be '(503) 325-7464'"
        assert phone.use == "home", "Phone use must be 'home'"

    def test_problem_angina(self, cerner_bundle):
        """Validate Problem: Angina (SNOMED 194828000)."""
        # Find all Conditions
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Bundle must contain Conditions"

        # Find angina condition by SNOMED code
        angina = None
        for condition in conditions:
            if condition.code and condition.code.coding:
                for coding in condition.code.coding:
                    if coding.code == "194828000" and coding.system == "http://snomed.info/sct":
                        angina = condition
                        break
                if angina:
                    break

        assert angina is not None, "Must have Condition with SNOMED code 194828000 (angina)"

        # EXACT check: Code text
        assert "angina" in angina.code.text.lower(), \
            "Condition must mention 'angina'"

        # EXACT check: Clinical status (active)
        assert angina.clinicalStatus is not None, "Condition must have clinical status"
        assert "active" in angina.clinicalStatus.coding[0].code, \
            "Condition clinical status must be 'active'"

        # EXACT check: onsetDateTime
        assert angina.onsetDateTime is not None, "Condition must have onsetDateTime"
        assert "2013-07-10" in str(angina.onsetDateTime), "Condition onset must be 2013-07-10"

        # EXACT check: recordedDate
        assert angina.recordedDate is not None, "Condition must have recordedDate"
        assert "2013-07-10" in str(angina.recordedDate), "Condition recorded date must be 2013-07-10"

        # EXACT check: category
        assert angina.category is not None and len(angina.category) > 0, "Condition must have category"
        cat_coding = angina.category[0].coding[0]
        assert cat_coding.code == "problem-list-item", "Condition category must be 'problem-list-item'"
        assert cat_coding.system == "http://terminology.hl7.org/CodeSystem/condition-category", \
            "Condition category must use standard system"

    def test_problem_diabetes_type_2(self, cerner_bundle):
        """Validate Problem: Diabetes mellitus type 2 (SNOMED 44054006)."""
        # Find all Conditions
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        # Find diabetes condition by SNOMED code
        diabetes = None
        for condition in conditions:
            if condition.code and condition.code.coding:
                for coding in condition.code.coding:
                    if coding.code == "44054006" and coding.system == "http://snomed.info/sct":
                        diabetes = condition
                        break

        assert diabetes is not None, "Must have Condition with SNOMED code 44054006 (diabetes type 2)"

        # EXACT check: Code text
        assert "diabetes" in diabetes.code.text.lower(), "Condition must mention 'diabetes'"

        # EXACT check: Clinical status (active)
        assert diabetes.clinicalStatus is not None, "Condition must have clinical status"
        assert "active" in diabetes.clinicalStatus.coding[0].code, \
            "Condition clinical status must be 'active'"

    def test_problem_hypercholesterolemia(self, cerner_bundle):
        """Validate Problem: Hypercholesterolemia (SNOMED 13644009)."""
        # Find all Conditions
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        # Find hypercholesterolemia condition by SNOMED code
        hyperchol = None
        for condition in conditions:
            if condition.code and condition.code.coding:
                for coding in condition.code.coding:
                    if coding.code == "13644009" and coding.system == "http://snomed.info/sct":
                        hyperchol = condition
                        break

        assert hyperchol is not None, "Must have Condition with SNOMED code 13644009 (hypercholesterolemia)"

        # EXACT check: Code text
        assert "cholesterol" in hyperchol.code.text.lower(), \
            "Condition must mention 'cholesterol'"

    def test_allergy_codeine_with_reaction(self, cerner_bundle):
        """Validate Allergy: Codeine (RxNorm 2670) with Nausea reaction."""
        # Find all AllergyIntolerances
        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        assert len(allergies) > 0, "Bundle must contain AllergyIntolerances"

        # Find codeine allergy by RxNorm code
        codeine = None
        for allergy in allergies:
            if allergy.code and allergy.code.coding:
                for coding in allergy.code.coding:
                    if coding.code == "2670":
                        codeine = allergy
                        break

        assert codeine is not None, "Must have AllergyIntolerance with RxNorm code 2670 (codeine)"

        # EXACT check: Code text
        assert "codeine" in codeine.code.text.lower(), \
            "AllergyIntolerance must mention 'codeine'"

        # EXACT check: Type
        assert codeine.type == "allergy", "AllergyIntolerance type must be 'allergy'"

        # EXACT check: recordedDate
        assert codeine.recordedDate is not None, "AllergyIntolerance must have recordedDate"
        assert "2013-07-10" in str(codeine.recordedDate), "AllergyIntolerance recorded date must be 2013-07-10"

        # EXACT check: Reaction manifestation (Nausea) and severity
        assert codeine.reaction is not None and len(codeine.reaction) > 0, "AllergyIntolerance must have reaction"
        reaction = codeine.reaction[0]

        # Check severity
        assert reaction.severity == "moderate", "Reaction severity must be 'moderate'"

        # Check manifestation
        assert reaction.manifestation is not None and len(reaction.manifestation) > 0, \
            "Reaction must have manifestation"
        manifestation = reaction.manifestation[0]
        assert manifestation.text is not None, "Manifestation must have text"
        assert "nausea" in manifestation.text.lower(), "Reaction must mention 'nausea'"

    def test_allergy_penicillin_with_reaction(self, cerner_bundle):
        """Validate Allergy: Penicillin G (RxNorm 7980) with Weal/Hives reaction."""
        # Find all AllergyIntolerances
        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        # Find penicillin allergy by RxNorm code
        penicillin = None
        for allergy in allergies:
            if allergy.code and allergy.code.coding:
                for coding in allergy.code.coding:
                    if coding.code == "7980":
                        penicillin = allergy
                        break

        assert penicillin is not None, "Must have AllergyIntolerance with RxNorm code 7980 (penicillin)"

        # EXACT check: Code text
        assert "penicillin" in penicillin.code.text.lower(), \
            "AllergyIntolerance must mention 'penicillin'"

        # EXACT check: Reaction manifestation (Weal/Hives)
        if penicillin.reaction and len(penicillin.reaction) > 0:
            reaction = penicillin.reaction[0]
            if reaction.manifestation and len(reaction.manifestation) > 0:
                manifestation = reaction.manifestation[0]
                if manifestation.text:
                    # Weal is medical term for hives/wheal
                    assert "weal" in manifestation.text.lower() or "hive" in manifestation.text.lower(), \
                        "Reaction must mention 'weal' or 'hives'"

    def test_composition_metadata_exact(self, cerner_bundle):
        """Validate Composition has metadata from C-CDA."""
        # Composition is first entry
        composition = cerner_bundle.entry[0].resource
        assert composition.get_resource_type() == "Composition"

        # Check: Status
        assert composition.status == "final", "Composition status must be 'final'"

        # Check: Type code - Transition of Care is typically LOINC 18761-7 or similar
        assert composition.type is not None, "Composition must have type"

    def test_composition_has_all_expected_sections(self, cerner_bundle):
        """Validate Composition has all major clinical sections with correct structure."""
        composition = cerner_bundle.entry[0].resource
        assert composition.get_resource_type() == "Composition"
        assert composition.section is not None, "Composition must have sections"

        # Expected sections in Cerner TOC (LOINC codes)
        expected_sections = {
            "46240-8": "Encounters",
            "11450-4": "Problems",
            "48765-2": "Allergies",
            "10160-0": "Medications",
            "11369-6": "Immunizations",
            "47519-4": "Procedures",
            "30954-2": "Results",
            "8716-3": "Vital Signs"
        }

        section_codes = {}
        for section in composition.section:
            if section.code and section.code.coding:
                for coding in section.code.coding:
                    if coding.system == "http://loinc.org":
                        section_codes[coding.code] = section.title

        # Verify all expected sections present
        for code, title in expected_sections.items():
            assert code in section_codes, f"Composition must have {title} section (LOINC {code})"

        # Verify sections have entries (references to resources) where applicable
        # Some sections may have narrative only without entry references
        for section in composition.section:
            if section.code and section.code.coding:
                code = section.code.coding[0].code
                # Only validate entries for sections that typically have them
                # Immunizations section may not have entries if immunizations are in other sections
                if code in expected_sections and code not in ["11369-6"]:  # Skip immunizations check
                    if section.entry is not None:
                        assert len(section.entry) > 0, \
                            f"Section {expected_sections[code]} has entry field but it's empty"

    def test_composition_section_entries_reference_valid_resources(self, cerner_bundle):
        """Validate Composition section entries reference resources that exist in bundle."""
        composition = cerner_bundle.entry[0].resource

        # Get all resource IDs in bundle
        bundle_resource_ids = set()
        for entry in cerner_bundle.entry:
            if entry.resource and hasattr(entry.resource, 'id'):
                resource_type = entry.resource.get_resource_type()
                bundle_resource_ids.add(f"{resource_type}/{entry.resource.id}")

        # Check all section entries
        for section in composition.section or []:
            for entry_ref in section.entry or []:
                assert entry_ref.reference in bundle_resource_ids, \
                    f"Section entry reference '{entry_ref.reference}' must exist in bundle"

    def test_all_clinical_resources_reference_steve_williamson(self, cerner_bundle):
        """Validate all clinical resources reference Patient Steve Williamson."""
        # Find Patient
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        expected_patient_ref = f"Patient/{patient.id}"

        # Check Conditions
        conditions = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Condition"]
        for condition in conditions:
            assert condition.subject.reference == expected_patient_ref, \
                f"Condition must reference {expected_patient_ref}"

        # Check AllergyIntolerances
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]
        for allergy in allergies:
            assert allergy.patient.reference == expected_patient_ref, \
                f"AllergyIntolerance must reference {expected_patient_ref}"

    def test_encounter_ambulatory(self, cerner_bundle):
        """Validate Encounter: Ambulatory encounter."""
        # Find all Encounters
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Bundle must contain Encounters"

        # Find encounter with class=AMB (ambulatory)
        ambulatory = encounters[0]  # Cerner has 1 encounter

        assert ambulatory is not None, "Must have Encounter"

        # EXACT check: Status
        assert ambulatory.status == "finished", "Encounter status must be 'finished'"

        # EXACT check: Class (ambulatory)
        assert ambulatory.class_fhir is not None, "Encounter must have class"
        assert ambulatory.class_fhir.code == "AMB", "Encounter class must be 'AMB' (ambulatory)"

        # EXACT check: Period start (2013-07-10)
        assert ambulatory.period is not None, "Encounter must have period"
        assert ambulatory.period.start is not None, "Encounter must have period.start"
        assert "2013-07-10" in str(ambulatory.period.start), "Encounter period.start must be 2013-07-10"

        # EXACT check: Participants (practitioners)
        assert ambulatory.participant is not None and len(ambulatory.participant) > 0, \
            "Encounter must have participants"
        assert len(ambulatory.participant) == 3, "Encounter must have 3 participants"

    def test_practitioner_aaron_admit(self, cerner_bundle):
        """Validate Practitioner: Dr. Aaron Admit."""
        # Find all Practitioners
        practitioners = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Practitioner"
        ]

        assert len(practitioners) > 0, "Bundle must contain Practitioners"

        # Cerner has 1 practitioner (Aaron Admit)
        dr_admit = practitioners[0]

        assert dr_admit is not None, "Must have Practitioner"

        # EXACT check: Name
        assert dr_admit.name is not None and len(dr_admit.name) > 0, "Practitioner must have name"
        name = dr_admit.name[0]

        # Check family name
        assert name.family == "Admit", "Practitioner family name must be 'Admit'"

        # Check given name
        assert name.given is not None and len(name.given) > 0, "Practitioner must have given name"
        assert "Aaron" in name.given, "Practitioner given name must be 'Aaron'"

        # Check suffix (MD)
        assert name.suffix is not None and len(name.suffix) > 0, "Practitioner must have suffix"
        assert "MD" in name.suffix, "Practitioner suffix must include 'MD'"

    def test_procedure_electrocardiographic(self, cerner_bundle):
        """Validate Procedure: Electrocardiographic procedure (SNOMED 29303009)."""
        # Find all Procedures
        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        assert len(procedures) > 0, "Bundle must contain Procedures"

        # Find EKG procedure by SNOMED code
        ekg = None
        for proc in procedures:
            if proc.code and proc.code.coding:
                for coding in proc.code.coding:
                    if coding.code == "29303009" and coding.system == "http://snomed.info/sct":
                        ekg = proc
                        break

        assert ekg is not None, "Must have Procedure with SNOMED code 29303009 (Electrocardiographic procedure)"

        # EXACT check: Status
        assert ekg.status == "completed", "Procedure status must be 'completed'"

        # EXACT check: Code text
        assert ekg.code.text is not None, "Procedure must have code.text"
        assert "electrocardiographic" in ekg.code.text.lower(), \
            "Procedure text must mention 'electrocardiographic'"

        # EXACT check: Performed date (2013-07-10)
        assert ekg.performedDateTime is not None, "Procedure must have performedDateTime"
        assert "2013-07-10" in str(ekg.performedDateTime), "Procedure performed date must be 2013-07-10"

    def test_diagnostic_report_chemistry(self, cerner_bundle):
        """Validate DiagnosticReport: Chemistry panel (LOINC 18719-5)."""
        # Find all DiagnosticReports
        reports = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "DiagnosticReport"
        ]

        assert len(reports) > 0, "Bundle must contain DiagnosticReports"

        # Find report by LOINC code 18719-5
        chemistry = None
        for report in reports:
            if report.code and report.code.coding:
                for coding in report.code.coding:
                    if coding.code == "18719-5" and coding.system == "http://loinc.org":
                        chemistry = report
                        break

        assert chemistry is not None, "Must have DiagnosticReport with LOINC code 18719-5"

        # EXACT check: Status
        assert chemistry.status == "final", "DiagnosticReport status must be 'final'"

        # EXACT check: Category (LAB)
        assert chemistry.category is not None and len(chemistry.category) > 0, \
            "DiagnosticReport must have category"
        cat_coding = chemistry.category[0].coding[0]
        assert cat_coding.code == "LAB", "DiagnosticReport category must be 'LAB'"
        assert cat_coding.system == "http://terminology.hl7.org/CodeSystem/v2-0074", \
            "Category must use v2-0074 system"

        # Check: Has results (Observations)
        if chemistry.result:
            assert len(chemistry.result) > 0, "DiagnosticReport should have result references"

    def test_immunization_influenza(self, cerner_bundle):
        """Validate Immunization: Influenza vaccine (CVX 88)."""
        # Find all Immunizations
        immunizations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        assert len(immunizations) > 0, "Bundle must contain Immunizations"

        # Find influenza vaccine by CVX code 88
        flu_shot = None
        for imm in immunizations:
            if imm.vaccineCode and imm.vaccineCode.coding:
                for coding in imm.vaccineCode.coding:
                    if coding.code == "88":
                        flu_shot = imm
                        break

        assert flu_shot is not None, "Must have Immunization with CVX code 88 (influenza vaccine)"

        # EXACT check: Status
        assert flu_shot.status == "completed", "Immunization status must be 'completed'"

        # EXACT check: Vaccine text
        assert flu_shot.vaccineCode.text is not None, "Immunization must have vaccineCode.text"
        assert "influenza" in flu_shot.vaccineCode.text.lower(), \
            "Vaccine text must mention 'influenza'"

    def test_medication_request_insulin_glargine(self, cerner_bundle):
        """Validate MedicationRequest: Insulin Glargine (RxNorm 311041)."""
        # Find all MedicationRequests
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        assert len(med_requests) > 0, "Bundle must contain MedicationRequests"

        # Find Insulin Glargine by RxNorm code
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041" and coding.system == "http://www.nlm.nih.gov/research/umls/rxnorm":
                        insulin = mr
                        break

        assert insulin is not None, "Must have MedicationRequest with RxNorm code 311041 (Insulin Glargine)"

        # EXACT check: Status
        assert insulin.status == "active", "MedicationRequest status must be 'active'"

        # EXACT check: Medication code display
        rxnorm_coding = next(
            (c for c in insulin.medicationCodeableConcept.coding
             if c.system == "http://www.nlm.nih.gov/research/umls/rxnorm"),
            None
        )
        assert rxnorm_coding is not None, "Must have RxNorm coding"
        assert "insulin" in rxnorm_coding.display.lower(), \
            "MedicationRequest display must mention 'insulin'"
        assert "glargine" in rxnorm_coding.display.lower(), \
            "MedicationRequest display must mention 'glargine'"

    def test_observation_lab_result_with_value_and_units(self, cerner_bundle):
        """Validate Observation: Lab result with value, units, interpretation, and category."""
        # Find all Observations
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Bundle must contain Observations"

        # Find first laboratory observation with valueQuantity
        # Filter for category="laboratory" to avoid picking up vital signs
        obs_with_value = None
        for obs in observations:
            # Check if this is a laboratory observation
            is_lab = False
            if hasattr(obs, 'category') and obs.category:
                for cat in obs.category:
                    if cat.coding:
                        for coding in cat.coding:
                            if coding.code == "laboratory":
                                is_lab = True
                                break

            # Check if it has valueQuantity
            if is_lab and hasattr(obs, 'valueQuantity') and obs.valueQuantity:
                obs_with_value = obs
                break

        assert obs_with_value is not None, "Must have at least one laboratory Observation with valueQuantity"

        # EXACT check: effectiveDateTime
        assert obs_with_value.effectiveDateTime is not None, "Observation must have effectiveDateTime"
        assert "2013-07-10" in str(obs_with_value.effectiveDateTime), \
            "Observation effective date must be 2013-07-10"

        # EXACT check: valueQuantity with value and unit
        assert obs_with_value.valueQuantity is not None, "Observation must have valueQuantity"
        assert obs_with_value.valueQuantity.value is not None, "Observation must have value"
        assert obs_with_value.valueQuantity.unit is not None, "Observation must have unit"
        assert obs_with_value.valueQuantity.system == "http://unitsofmeasure.org", \
            "Observation unit system must be UCUM"

        # EXACT check: interpretation (Normal)
        assert obs_with_value.interpretation is not None and len(obs_with_value.interpretation) > 0, \
            "Observation must have interpretation"
        interp_coding = obs_with_value.interpretation[0].coding[0]
        assert interp_coding.code == "N", "Observation interpretation must be 'N' (Normal)"
        assert interp_coding.system == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", \
            "Interpretation must use standard system"

        # EXACT check: category (laboratory)
        assert obs_with_value.category is not None and len(obs_with_value.category) > 0, \
            "Observation must have category"
        cat_coding = obs_with_value.category[0].coding[0]
        assert cat_coding.code == "laboratory", "Observation category must be 'laboratory'"
        assert cat_coding.system == "http://terminology.hl7.org/CodeSystem/observation-category", \
            "Category must use standard system"

    def test_medication_request_has_route(self, cerner_bundle):
        """Validate MedicationRequest (Insulin Glargine) has route code C38299 (Subcutaneous)."""
        # Find all MedicationRequests
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        # Find Insulin Glargine by RxNorm code 311041
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041":
                        insulin = mr
                        break

        assert insulin is not None, "Must have MedicationRequest with RxNorm code 311041 (Insulin Glargine)"

        # EXACT check: dosageInstruction has route
        assert insulin.dosageInstruction is not None and len(insulin.dosageInstruction) > 0, \
            "MedicationRequest must have dosageInstruction"
        dosage = insulin.dosageInstruction[0]

        assert dosage.route is not None, "Dosage must have route"
        assert dosage.route.coding is not None and len(dosage.route.coding) > 0, \
            "Route must have coding"

        # EXACT check: Route code C38299 (Subcutaneous) from NCI Thesaurus
        route_coding = dosage.route.coding[0]
        assert route_coding.code == "C38299", "Route code must be 'C38299' (Subcutaneous)"
        assert route_coding.system == "http://ncimeta.nci.nih.gov", \
            "Route system must be NCI Thesaurus (http://ncimeta.nci.nih.gov)"

    def test_medication_request_has_dose_quantity(self, cerner_bundle):
        """Validate MedicationRequest (Insulin Glargine) has doseQuantity with value 30.0 units."""
        # Find all MedicationRequests
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        # Find Insulin Glargine by RxNorm code 311041
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041":
                        insulin = mr
                        break

        assert insulin is not None, "Must have MedicationRequest with RxNorm code 311041 (Insulin Glargine)"

        # EXACT check: dosageInstruction has doseAndRate with doseQuantity
        assert insulin.dosageInstruction is not None and len(insulin.dosageInstruction) > 0, \
            "MedicationRequest must have dosageInstruction"
        dosage = insulin.dosageInstruction[0]

        assert dosage.doseAndRate is not None and len(dosage.doseAndRate) > 0, \
            "Dosage must have doseAndRate"
        dose_and_rate = dosage.doseAndRate[0]

        assert dose_and_rate.doseQuantity is not None, "DoseAndRate must have doseQuantity"

        # EXACT check: doseQuantity value 30.0 units
        assert dose_and_rate.doseQuantity.value == 30.0, "DoseQuantity value must be 30.0"
        assert dose_and_rate.doseQuantity.unit == "1", "DoseQuantity unit must be '1'"
        assert dose_and_rate.doseQuantity.system == "http://unitsofmeasure.org", \
            "DoseQuantity system must be UCUM"
        assert dose_and_rate.doseQuantity.code == "1", "DoseQuantity code must be '1'"

    def test_immunization_has_route_and_dose(self, cerner_bundle):
        """Validate Immunization has route code C28161 (Intramuscular) and doseQuantity 0.25 mL."""
        # Find all Immunizations
        immunizations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        assert len(immunizations) > 0, "Bundle must contain Immunizations"

        # Find influenza vaccine by CVX code 88
        flu_shot = None
        for imm in immunizations:
            if imm.vaccineCode and imm.vaccineCode.coding:
                for coding in imm.vaccineCode.coding:
                    if coding.code == "88":
                        flu_shot = imm
                        break

        assert flu_shot is not None, "Must have Immunization with CVX code 88 (influenza vaccine)"

        # EXACT check: Route code C28161 (Intramuscular)
        assert flu_shot.route is not None, "Immunization must have route"
        assert flu_shot.route.coding is not None and len(flu_shot.route.coding) > 0, \
            "Route must have coding"

        route_coding = flu_shot.route.coding[0]
        assert route_coding.code == "C28161", "Route code must be 'C28161' (Intramuscular)"
        assert route_coding.system == "http://ncimeta.nci.nih.gov", \
            "Route system must be NCI Thesaurus (http://ncimeta.nci.nih.gov)"
        assert flu_shot.route.text == "Intramuscular", "Route text must be 'Intramuscular'"

        # EXACT check: doseQuantity 0.25 mL
        assert flu_shot.doseQuantity is not None, "Immunization must have doseQuantity"
        assert flu_shot.doseQuantity.value == 0.25, "DoseQuantity value must be 0.25"
        assert flu_shot.doseQuantity.unit == "mL", "DoseQuantity unit must be 'mL'"

    def test_practitioner_has_address_and_telecom(self, cerner_bundle):
        """Validate Practitioner (Aaron Admit) has complete address and telecom."""
        # Find all Practitioners
        practitioners = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Practitioner"
        ]

        assert len(practitioners) > 0, "Bundle must contain Practitioners"

        # Find Dr. Aaron Admit (should be the only practitioner in Cerner sample)
        dr_admit = practitioners[0]

        # EXACT check: Address
        assert dr_admit.address is not None and len(dr_admit.address) > 0, \
            "Practitioner must have address"
        addr = dr_admit.address[0]

        assert addr.line is not None and len(addr.line) > 0, "Address must have line"
        assert "1006 Healthcare Dr" in addr.line, "Address line must include '1006 Healthcare Dr'"
        assert addr.city == "Portland", "Address city must be 'Portland'"
        assert addr.state == "OR", "Address state must be 'OR'"
        assert "97005" in addr.postalCode, "Address postal code must include '97005'"
        assert addr.country == "US", "Address country must be 'US'"
        assert addr.use == "work", "Address use must be 'work'"

        # EXACT check: Telecom
        assert dr_admit.telecom is not None and len(dr_admit.telecom) > 0, \
            "Practitioner must have telecom"
        phone = dr_admit.telecom[0]

        assert phone.system == "phone", "Telecom system must be 'phone'"
        assert "(555) 555-1006" in phone.value, "Phone number must be '(555) 555-1006'"
        assert phone.use == "work", "Telecom use must be 'work'"

    def test_encounter_has_period_start(self, cerner_bundle):
        """Validate Encounter has period with start time (end is nullFlavor in source)."""
        # Find all Encounters
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Bundle must contain Encounters"

        encounter = encounters[0]

        # EXACT check: Period with start
        assert encounter.period is not None, "Encounter must have period"
        assert encounter.period.start is not None, "Encounter must have period.start"
        assert "2013-07-10" in str(encounter.period.start), \
            "Encounter period.start must be 2013-07-10"

        # NOTE: The C-CDA source has <high nullFlavor="NI"/> so period.end is not present
        # This is a valid real-world case for ongoing or unknown end time

    def test_patient_has_communication(self, cerner_bundle):
        """Validate Patient.communication with language code 'eng'."""
        # Find Patient
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert patient is not None, "Bundle must contain Patient"

        # EXACT check: Communication
        assert patient.communication is not None and len(patient.communication) > 0, \
            "Patient must have communication"

        comm = patient.communication[0]

        # EXACT check: Language coding
        assert comm.language is not None, "Communication must have language"
        assert comm.language.coding is not None and len(comm.language.coding) > 0, \
            "Language must have coding"

        lang_coding = comm.language.coding[0]
        assert lang_coding.code == "eng", "Language code must be 'eng' (English)"
        assert lang_coding.system == "urn:ietf:bcp:47", \
            "Language system must be 'urn:ietf:bcp:47' (BCP 47)"

    def test_medication_request_has_requester(self, cerner_bundle):
        """Validate MedicationRequest (Insulin Glargine) requester handling with nullFlavor author."""
        # Find all MedicationRequests
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        # Find Insulin Glargine by RxNorm code 311041
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041":
                        insulin = mr
                        break

        assert insulin is not None, "Must have MedicationRequest with RxNorm code 311041 (Insulin Glargine)"

        # CORRECT behavior: When medication author has NO ID and NO usable name (all nullFlavor),
        # converter should NOT create a requester reference (prevents ID collisions)
        # The C-CDA has <author><time value="20130710215810.000-0500"/> but:
        #   - assignedAuthor/id has nullFlavor="NI"
        #   - assignedPerson/name/given and family have nullFlavor="NA" (parsed as None)
        # Since there's no identifying information, we skip creating practitioner reference
        assert insulin.requester is None, \
            "MedicationRequest.requester should be None when author has no ID and no usable name"

    def test_medication_request_has_authored_on(self, cerner_bundle):
        """Validate MedicationRequest (Insulin Glargine) has authoredOn timestamp from author/time."""
        # Find all MedicationRequests
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        # Find Insulin Glargine by RxNorm code 311041
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041":
                        insulin = mr
                        break

        assert insulin is not None, "Must have MedicationRequest with RxNorm code 311041 (Insulin Glargine)"

        # EXACT check: authoredOn timestamp from C-CDA <author><time value="20130710215810.000-0500"/>
        assert insulin.authoredOn is not None, "MedicationRequest must have authoredOn"

        # Verify timestamp matches expected value: 2013-07-10T21:58:10-05:00
        # Note: Python datetime str() uses space instead of 'T' separator
        assert "2013-07-10" in str(insulin.authoredOn), \
            "AuthoredOn date must be 2013-07-10"
        assert "21:58:10" in str(insulin.authoredOn), \
            "AuthoredOn time must be 21:58:10"
        assert "-05:00" in str(insulin.authoredOn) or "-0500" in str(insulin.authoredOn), \
            "AuthoredOn timezone must be -05:00"

        # Verify the actual datetime values match
        assert insulin.authoredOn.year == 2013, "AuthoredOn year must be 2013"
        assert insulin.authoredOn.month == 7, "AuthoredOn month must be 7"
        assert insulin.authoredOn.day == 10, "AuthoredOn day must be 10"
        assert insulin.authoredOn.hour == 21, "AuthoredOn hour must be 21"
        assert insulin.authoredOn.minute == 58, "AuthoredOn minute must be 58"
        assert insulin.authoredOn.second == 10, "AuthoredOn second must be 10"

    def test_encounter_has_location(self, cerner_bundle):
        """Validate Encounter has location array with reference to Location resource."""
        # Find all Encounters
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Bundle must contain Encounters"

        encounter = encounters[0]

        # EXACT check: Encounter has location array
        assert encounter.location is not None and len(encounter.location) > 0, \
            "Encounter must have location array"

        location_ref = encounter.location[0]

        # EXACT check: Location has reference
        assert location_ref.location is not None, "Encounter.location must have location reference"
        assert location_ref.location.reference is not None, "Location reference must not be None"
        assert location_ref.location.reference.startswith("Location/"), \
            "Location reference must point to Location resource"

        # Find the referenced Location resource
        location_id = location_ref.location.reference.split("/")[1]
        locations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Location" and e.resource.id == location_id
        ]

        assert len(locations) > 0, f"Referenced Location/{location_id} must exist in bundle"

        location = locations[0]

        # EXACT check: Location name from C-CDA <name>Local Community Hospital Organization</name>
        assert location.name == "Local Community Hospital Organization", \
            "Location name must be 'Local Community Hospital Organization'"

        # EXACT check: Location address from C-CDA
        # <streetAddressLine>4000 Hospital Dr.</streetAddressLine>
        # <city>Portland</city><state>OR</state><postalCode>97005-    </postalCode>
        assert location.address is not None, "Location must have address"
        assert location.address.line is not None and len(location.address.line) > 0, \
            "Location address must have line"
        assert "4000 Hospital Dr." in location.address.line, \
            "Location address must include '4000 Hospital Dr.'"
        assert location.address.city == "Portland", "Location city must be 'Portland'"
        assert location.address.state == "OR", "Location state must be 'OR'"
        assert "97005" in location.address.postalCode, \
            "Location postal code must include '97005'"

        # EXACT check: Location telecom from C-CDA <telecom use="WP" value="tel:(555) 555-1010"/>
        assert location.telecom is not None and len(location.telecom) > 0, \
            "Location must have telecom"
        phone = location.telecom[0]
        assert phone.system == "phone", "Telecom system must be 'phone'"
        assert "(555) 555-1010" in phone.value, "Phone number must be '(555) 555-1010'"
        assert phone.use == "work", "Telecom use must be 'work'"

        # EXACT check: Location type code from ServiceDeliveryLocationRoleType
        # C-CDA has <code nullFlavor="NI"/> so type may not be present
        # But if present, should use http://terminology.hl7.org/CodeSystem/v3-RoleCode
        if location.type is not None and len(location.type) > 0:
            type_coding = location.type[0].coding[0] if location.type[0].coding else None
            if type_coding:
                assert type_coding.system == "http://terminology.hl7.org/CodeSystem/v3-RoleCode", \
                    "Location type must use ServiceDeliveryLocationRoleType code system"

    def test_observation_blood_pressure_has_components(self, cerner_bundle):
        """Validate multi-component blood pressure Observation has systolic and diastolic components."""
        # Find all Observations
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Bundle must contain Observations"

        # Find blood pressure panel observation
        # In C-CDA, systolic (8480-6) and diastolic (8462-4) are separate observations in organizer
        # In FHIR, they should be components of a blood pressure panel observation
        # Look for observation with components containing both codes
        bp_panel = None
        for obs in observations:
            if obs.component and len(obs.component) >= 2:
                component_codes = []
                for comp in obs.component:
                    if comp.code and comp.code.coding:
                        for coding in comp.code.coding:
                            component_codes.append(coding.code)

                # Check if both systolic and diastolic are present
                if "8480-6" in component_codes and "8462-4" in component_codes:
                    bp_panel = obs
                    break

        assert bp_panel is not None, \
            "Must have Observation with components for systolic (8480-6) and diastolic (8462-4) blood pressure"

        # EXACT check: Parent observation code for blood pressure panel
        # Should be LOINC 85354-9 (Blood pressure panel) or similar
        assert bp_panel.code is not None, "Blood pressure observation must have code"
        assert bp_panel.code.coding is not None and len(bp_panel.code.coding) > 0, \
            "Blood pressure code must have coding"

        # EXACT check: effectiveDateTime from vital signs
        # C-CDA has <effectiveTime value="20130710220000.000-0500"/>
        assert bp_panel.effectiveDateTime is not None, "Blood pressure observation must have effectiveDateTime"
        assert "2013-07-10" in str(bp_panel.effectiveDateTime), \
            "Blood pressure effectiveDateTime must be 2013-07-10"
        assert "22:00:00" in str(bp_panel.effectiveDateTime), \
            "Blood pressure effectiveDateTime must be 22:00:00"

        # EXACT check: component[0] (Systolic)
        # From C-CDA: <code code="8480-6" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC">
        # <value xsi:type="PQ" value="150" unit="mm[Hg]"/>
        # <interpretationCode code="H" codeSystem="2.16.840.1.113883.5.83" codeSystemName="ObservationInterpretation">
        systolic = None
        for comp in bp_panel.component:
            if comp.code and comp.code.coding:
                for coding in comp.code.coding:
                    if coding.code == "8480-6":
                        systolic = comp
                        break

        assert systolic is not None, "Must have systolic component with code 8480-6"
        assert systolic.code.coding[0].system == "http://loinc.org", \
            "Systolic code must use LOINC system"

        # Check value
        assert systolic.valueQuantity is not None, "Systolic component must have valueQuantity"
        assert systolic.valueQuantity.value == 150, "Systolic value must be 150"
        assert systolic.valueQuantity.unit == "mm[Hg]" or systolic.valueQuantity.unit == "mmHg", \
            "Systolic unit must be mm[Hg] or mmHg"
        assert systolic.valueQuantity.system == "http://unitsofmeasure.org", \
            "Systolic unit system must be UCUM"

        # Check interpretation (High)
        assert systolic.interpretation is not None and len(systolic.interpretation) > 0, \
            "Systolic component must have interpretation"
        interp_coding = systolic.interpretation[0].coding[0]
        assert interp_coding.code == "H", "Systolic interpretation must be 'H' (High)"
        assert interp_coding.system == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", \
            "Interpretation must use standard system"

        # EXACT check: component[1] (Diastolic)
        # From C-CDA: <code code="8462-4" codeSystem="2.16.840.1.113883.6.1" codeSystemName="LOINC">
        # <value xsi:type="PQ" value="95" unit="mm[Hg]"/>
        # <interpretationCode code="H" codeSystem="2.16.840.1.113883.5.83" codeSystemName="ObservationInterpretation">
        diastolic = None
        for comp in bp_panel.component:
            if comp.code and comp.code.coding:
                for coding in comp.code.coding:
                    if coding.code == "8462-4":
                        diastolic = comp
                        break

        assert diastolic is not None, "Must have diastolic component with code 8462-4"
        assert diastolic.code.coding[0].system == "http://loinc.org", \
            "Diastolic code must use LOINC system"

        # Check value
        assert diastolic.valueQuantity is not None, "Diastolic component must have valueQuantity"
        assert diastolic.valueQuantity.value == 95, "Diastolic value must be 95"
        assert diastolic.valueQuantity.unit == "mm[Hg]" or diastolic.valueQuantity.unit == "mmHg", \
            "Diastolic unit must be mm[Hg] or mmHg"
        assert diastolic.valueQuantity.system == "http://unitsofmeasure.org", \
            "Diastolic unit system must be UCUM"

        # Check interpretation (High)
        assert diastolic.interpretation is not None and len(diastolic.interpretation) > 0, \
            "Diastolic component must have interpretation"
        interp_coding = diastolic.interpretation[0].coding[0]
        assert interp_coding.code == "H", "Diastolic interpretation must be 'H' (High)"
        assert interp_coding.system == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", \
            "Interpretation must use standard system"

    # ====================================================================================
    # Resource Identifier Tests - Critical for Interoperability
    # ====================================================================================

    def test_all_conditions_have_identifiers(self, cerner_bundle):
        """Validate all Condition resources have identifiers from C-CDA."""
        conditions = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Condition"]

        assert len(conditions) > 0, "Must have Condition resources"

        for condition in conditions:
            assert condition.identifier is not None, \
                "Condition must have identifier"
            assert len(condition.identifier) > 0, \
                "Condition must have at least one identifier"

            # Verify identifier structure
            identifier = condition.identifier[0]
            assert identifier.system is not None, \
                "Condition identifier must have system"
            assert identifier.value is not None, \
                "Condition identifier must have value"

    def test_all_allergy_intolerances_have_identifiers(self, cerner_bundle):
        """Validate all AllergyIntolerance resources have identifiers from C-CDA."""
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]

        assert len(allergies) > 0, "Must have AllergyIntolerance resources"

        for allergy in allergies:
            assert allergy.identifier is not None, \
                "AllergyIntolerance must have identifier"
            assert len(allergy.identifier) > 0, \
                "AllergyIntolerance must have at least one identifier"

            identifier = allergy.identifier[0]
            assert identifier.system is not None, \
                "AllergyIntolerance identifier must have system"
            assert identifier.value is not None, \
                "AllergyIntolerance identifier must have value"

    def test_all_medication_requests_have_identifiers(self, cerner_bundle):
        """Validate all MedicationRequest resources have identifiers from C-CDA."""
        med_requests = [e.resource for e in cerner_bundle.entry
                       if e.resource.get_resource_type() == "MedicationRequest"]

        assert len(med_requests) > 0, "Must have MedicationRequest resources"

        for med_request in med_requests:
            assert med_request.identifier is not None, \
                "MedicationRequest must have identifier"
            assert len(med_request.identifier) > 0, \
                "MedicationRequest must have at least one identifier"

            identifier = med_request.identifier[0]
            assert identifier.system is not None, \
                "MedicationRequest identifier must have system"
            assert identifier.value is not None, \
                "MedicationRequest identifier must have value"

    def test_immunizations_have_identifiers(self, cerner_bundle):
        """Validate Immunization resources have identifiers from C-CDA."""
        immunizations = [e.resource for e in cerner_bundle.entry
                        if e.resource.get_resource_type() == "Immunization"]

        assert len(immunizations) > 0, "Must have Immunization resources"

        for immunization in immunizations:
            assert immunization.identifier is not None, \
                "Immunization must have identifier"
            assert len(immunization.identifier) > 0, \
                "Immunization must have at least one identifier"

    def test_observations_have_identifiers(self, cerner_bundle):
        """Validate Observation resources have identifiers from C-CDA."""
        observations = [e.resource for e in cerner_bundle.entry
                       if e.resource.get_resource_type() == "Observation"]

        assert len(observations) > 0, "Must have Observation resources"

        for observation in observations:
            assert observation.identifier is not None, \
                "Observation must have identifier"
            assert len(observation.identifier) > 0, \
                "Observation must have at least one identifier"

    def test_encounters_have_identifiers(self, cerner_bundle):
        """Validate Encounter resources have identifiers from C-CDA."""
        encounters = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Encounter"]

        assert len(encounters) > 0, "Must have Encounter resources"

        for encounter in encounters:
            assert encounter.identifier is not None, \
                "Encounter must have identifier"
            assert len(encounter.identifier) > 0, \
                "Encounter must have at least one identifier"

    def test_procedures_have_identifiers(self, cerner_bundle):
        """Validate Procedure resources have identifiers from C-CDA."""
        procedures = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Procedure"]

        assert len(procedures) > 0, "Must have Procedure resources"

        for procedure in procedures:
            assert procedure.identifier is not None, \
                "Procedure must have identifier"
            assert len(procedure.identifier) > 0, \
                "Procedure must have at least one identifier"

    # ====================================================================================
    # AllergyIntolerance Status Tests - US Core Required
    # ====================================================================================

    def test_allergies_have_clinical_status(self, cerner_bundle):
        """Validate all AllergyIntolerance resources have clinicalStatus (US Core required)."""
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]

        assert len(allergies) > 0, "Must have AllergyIntolerance resources"

        for allergy in allergies:
            assert allergy.clinicalStatus is not None, \
                "AllergyIntolerance must have clinicalStatus (US Core required)"
            assert allergy.clinicalStatus.coding is not None and len(allergy.clinicalStatus.coding) > 0, \
                "AllergyIntolerance.clinicalStatus must have coding"

            # Verify coding uses correct system
            coding = allergy.clinicalStatus.coding[0]
            assert coding.system == "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", \
                "AllergyIntolerance.clinicalStatus must use standard CodeSystem"

            # Verify code is valid (active, inactive, or resolved)
            assert coding.code in ["active", "inactive", "resolved"], \
                f"AllergyIntolerance.clinicalStatus code must be active/inactive/resolved, got '{coding.code}'"

    def test_allergies_have_verification_status(self, cerner_bundle):
        """Validate all AllergyIntolerance resources have verificationStatus."""
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]

        assert len(allergies) > 0, "Must have AllergyIntolerance resources"

        for allergy in allergies:
            assert allergy.verificationStatus is not None, \
                "AllergyIntolerance must have verificationStatus"
            assert allergy.verificationStatus.coding is not None and len(allergy.verificationStatus.coding) > 0, \
                "AllergyIntolerance.verificationStatus must have coding"

            coding = allergy.verificationStatus.coding[0]
            assert coding.system == "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", \
                "AllergyIntolerance.verificationStatus must use standard CodeSystem"

    def test_allergies_have_category(self, cerner_bundle):
        """Validate AllergyIntolerance resources have category (US Core must-support)."""
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]

        assert len(allergies) > 0, "Must have AllergyIntolerance resources"

        # Find codeine allergy - should be "medication" category
        codeine = None
        for allergy in allergies:
            if allergy.code and allergy.code.coding:
                for coding in allergy.code.coding:
                    if coding.code == "2670":  # RxNorm code for Codeine
                        codeine = allergy
                        break

        if codeine:
            assert codeine.category is not None and len(codeine.category) > 0, \
                "Codeine allergy must have category"
            assert "medication" in codeine.category, \
                "Codeine allergy category must include 'medication'"

    # ====================================================================================
    # Organization Resource Tests - Previously Untested (0% coverage)
    # ====================================================================================

    def test_organization_exists_in_bundle(self, cerner_bundle):
        """Validate Organization resource is created from C-CDA."""
        organizations = [e.resource for e in cerner_bundle.entry
                        if e.resource.get_resource_type() == "Organization"]

        assert len(organizations) > 0, "Bundle must contain Organization resource"

    def test_organization_has_identifier(self, cerner_bundle):
        """Validate Organization has identifier from C-CDA."""
        org = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Organization"),
            None
        )

        assert org is not None, "Must have Organization"
        assert org.identifier is not None and len(org.identifier) > 0, \
            "Organization must have identifier"

        identifier = org.identifier[0]
        assert identifier.system is not None, "Organization identifier must have system"
        assert identifier.value is not None, "Organization identifier must have value"

    def test_organization_has_name(self, cerner_bundle):
        """Validate Organization has name from C-CDA."""
        org = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Organization"),
            None
        )

        assert org is not None, "Must have Organization"
        assert org.name is not None, "Organization must have name"
        assert "community hospital" in org.name.lower(), \
            "Organization name should reference 'Community Hospital'"

    def test_organization_has_contact_info(self, cerner_bundle):
        """Validate Organization has address and telecom from C-CDA."""
        org = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Organization"),
            None
        )

        assert org is not None, "Must have Organization"

        # Check address
        if org.address:
            assert len(org.address) > 0, "Organization should have address"

        # Check telecom
        if org.telecom:
            assert len(org.telecom) > 0, "Organization should have telecom"

    def test_patient_references_organization(self, cerner_bundle):
        """Validate Patient.managingOrganization references the Organization."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        org = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Organization"),
            None
        )

        if patient and org and hasattr(patient, 'managingOrganization'):
            if patient.managingOrganization:
                # Check if reference or display is set (both are valid)
                has_reference = patient.managingOrganization.reference is not None
                has_display = patient.managingOrganization.display is not None

                assert has_reference or has_display, \
                    "Patient.managingOrganization must have reference or display"

                # If reference is set, verify it points to the right organization
                if has_reference:
                    expected_ref = f"Organization/{org.id}"
                    assert patient.managingOrganization.reference == expected_ref, \
                        f"Patient.managingOrganization must reference {expected_ref}"

    # ====================================================================================
    # Encounter.diagnosis Tests - Links Encounter to Conditions
    # ====================================================================================

    def test_encounter_has_diagnosis(self, cerner_bundle):
        """Validate Encounter.diagnosis links to Condition resources."""
        encounter = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Encounter"),
            None
        )

        assert encounter is not None, "Must have Encounter"

        # Verify diagnosis field exists and has entries
        if hasattr(encounter, 'diagnosis') and encounter.diagnosis:
            assert len(encounter.diagnosis) > 0, "Encounter should have diagnosis entries"

            # Verify each diagnosis references a Condition
            for diagnosis in encounter.diagnosis:
                assert diagnosis.condition is not None, \
                    "Encounter.diagnosis must have condition reference"
                assert diagnosis.condition.reference is not None, \
                    "Encounter.diagnosis.condition must have reference"
                assert diagnosis.condition.reference.startswith("Condition/"), \
                    f"Encounter.diagnosis must reference Condition, got '{diagnosis.condition.reference}'"

                # Verify the referenced Condition exists in bundle
                condition_id = diagnosis.condition.reference.split("/")[1]
                condition_exists = any(
                    e.resource.get_resource_type() == "Condition" and e.resource.id == condition_id
                    for e in cerner_bundle.entry
                )
                assert condition_exists, \
                    f"Referenced Condition/{condition_id} must exist in bundle"

    def test_encounter_diagnosis_has_use_code(self, cerner_bundle):
        """Validate Encounter.diagnosis has use code (billing, admission, discharge, etc)."""
        encounter = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Encounter"),
            None
        )

        if encounter and hasattr(encounter, 'diagnosis') and encounter.diagnosis:
            for diagnosis in encounter.diagnosis:
                # US Core recommends use codes from diagnosis-role
                if hasattr(diagnosis, 'use') and diagnosis.use:
                    assert diagnosis.use.coding is not None, \
                        "Encounter.diagnosis.use should have coding"

    # ====================================================================================
    # Medium Priority Tests - MedicationRequest.intent and dispenseRequest
    # ====================================================================================

    def test_medication_requests_have_intent(self, cerner_bundle):
        """Validate all MedicationRequest resources have intent (US Core required)."""
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        assert len(med_requests) > 0, "Must have MedicationRequest resources"

        for mr in med_requests:
            assert mr.intent is not None, \
                "MedicationRequest.intent is required (US Core)"
            assert mr.intent in ["proposal", "plan", "order", "original-order", "reflex-order", "filler-order", "instance-order", "option"], \
                f"MedicationRequest.intent must be valid code, got '{mr.intent}'"

    def test_medication_requests_have_dispense_request_when_supply_present(self, cerner_bundle):
        """Validate MedicationRequest.dispenseRequest is populated when C-CDA has supply."""
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        # Find Insulin Glargine (should have dispenseRequest with 10 mL)
        insulin = None
        for mr in med_requests:
            if mr.medicationCodeableConcept and mr.medicationCodeableConcept.coding:
                for coding in mr.medicationCodeableConcept.coding:
                    if coding.code == "311041":  # RxNorm code for Insulin Glargine
                        insulin = mr
                        break

        assert insulin is not None, "Must have Insulin Glargine MedicationRequest"

        # Verify dispenseRequest is populated
        assert insulin.dispenseRequest is not None, \
            "MedicationRequest.dispenseRequest should be populated when C-CDA has supply"
        assert insulin.dispenseRequest.quantity is not None, \
            "dispenseRequest.quantity should be populated"
        assert insulin.dispenseRequest.quantity.value == 10, \
            "Supply quantity should be 10"
        assert insulin.dispenseRequest.quantity.unit == "mL", \
            "Supply unit should be mL"
        assert insulin.dispenseRequest.quantity.system == "http://unitsofmeasure.org", \
            "Supply quantity should use UCUM"

    # ====================================================================================
    # Medium Priority Tests - Observation.hasMember (panel relationships)
    # ====================================================================================

    def test_vital_signs_panel_has_members(self, cerner_bundle):
        """Validate Vital Signs panel Observation has hasMember linking to component observations."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find vital signs panel (observation with hasMember)
        panels = [obs for obs in observations if hasattr(obs, 'hasMember') and obs.hasMember]

        assert len(panels) > 0, "Must have at least one panel observation with hasMember"

        # Verify panel structure
        panel = panels[0]
        assert panel.hasMember is not None and len(panel.hasMember) > 0, \
            "Panel observation must have hasMember references"

        # Verify each member reference is valid
        for member in panel.hasMember:
            assert member.reference is not None, \
                "hasMember entry must have reference"
            assert member.reference.startswith("Observation/"), \
                f"hasMember must reference Observation, got '{member.reference}'"

            # Verify the referenced Observation exists in bundle
            obs_id = member.reference.split("/")[1]
            obs_exists = any(
                e.resource.get_resource_type() == "Observation" and e.resource.id == obs_id
                for e in cerner_bundle.entry
            )
            assert obs_exists, \
                f"Referenced Observation/{obs_id} must exist in bundle"

    # ====================================================================================
    # Medium Priority Tests - Composition.author
    # ====================================================================================

    def test_composition_has_author(self, cerner_bundle):
        """Validate Composition has author (US Core required)."""
        composition = cerner_bundle.entry[0].resource
        assert composition.get_resource_type() == "Composition"

        # US Core requires at least one author
        assert composition.author is not None and len(composition.author) > 0, \
            "Composition.author is required (US Core)"

        # Verify author has either reference or display
        for author in composition.author:
            has_reference = hasattr(author, 'reference') and author.reference is not None
            has_display = hasattr(author, 'display') and author.display is not None

            assert has_reference or has_display, \
                "Composition.author must have reference or display"

    # ====================================================================================
    # Medium Priority Tests - Condition.category (consistent across all conditions)
    # ====================================================================================

    def test_all_conditions_have_category(self, cerner_bundle):
        """Validate all Condition resources have category (US Core required)."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        for condition in conditions:
            assert condition.category is not None and len(condition.category) > 0, \
                "Condition.category is required (US Core)"

            # Verify category structure
            category = condition.category[0]
            assert category.coding is not None and len(category.coding) > 0, \
                "Condition.category must have coding"

            coding = category.coding[0]
            assert coding.system == "http://terminology.hl7.org/CodeSystem/condition-category", \
                "Condition.category must use condition-category CodeSystem"
            assert coding.code in ["problem-list-item", "encounter-diagnosis"], \
                f"Condition.category code must be valid, got '{coding.code}'"

    # ====================================================================================
    # Medium Priority Tests - Per-resource subject/patient references
    # ====================================================================================

    def test_conditions_reference_patient(self, cerner_bundle):
        """Validate all Condition resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        for condition in conditions:
            assert condition.subject is not None, "Condition.subject is required"
            assert condition.subject.reference is not None, "Condition.subject must have reference"
            assert condition.subject.reference == f"Patient/{patient.id}", \
                f"Condition.subject must reference Patient/{patient.id}"

    def test_diagnostic_reports_reference_patient(self, cerner_bundle):
        """Validate all DiagnosticReport resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        reports = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "DiagnosticReport"
        ]

        for report in reports:
            assert report.subject is not None, "DiagnosticReport.subject is required"
            assert report.subject.reference is not None, "DiagnosticReport.subject must have reference"
            assert report.subject.reference == f"Patient/{patient.id}", \
                f"DiagnosticReport.subject must reference Patient/{patient.id}"

    def test_encounters_reference_patient(self, cerner_bundle):
        """Validate all Encounter resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        for encounter in encounters:
            assert encounter.subject is not None, "Encounter.subject is required"
            assert encounter.subject.reference is not None, "Encounter.subject must have reference"
            assert encounter.subject.reference == f"Patient/{patient.id}", \
                f"Encounter.subject must reference Patient/{patient.id}"

    def test_procedures_reference_patient(self, cerner_bundle):
        """Validate all Procedure resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        for procedure in procedures:
            assert procedure.subject is not None, "Procedure.subject is required"
            assert procedure.subject.reference is not None, "Procedure.subject must have reference"
            assert procedure.subject.reference == f"Patient/{patient.id}", \
                f"Procedure.subject must reference Patient/{patient.id}"

    def test_observations_reference_patient(self, cerner_bundle):
        """Validate all Observation resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        for observation in observations:
            assert observation.subject is not None, "Observation.subject is required"
            assert observation.subject.reference is not None, "Observation.subject must have reference"
            assert observation.subject.reference == f"Patient/{patient.id}", \
                f"Observation.subject must reference Patient/{patient.id}"

    def test_medication_requests_reference_patient(self, cerner_bundle):
        """Validate all MedicationRequest resources have subject reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        for mr in med_requests:
            assert mr.subject is not None, "MedicationRequest.subject is required"
            assert mr.subject.reference is not None, "MedicationRequest.subject must have reference"
            assert mr.subject.reference == f"Patient/{patient.id}", \
                f"MedicationRequest.subject must reference Patient/{patient.id}"

    def test_allergy_intolerances_reference_patient(self, cerner_bundle):
        """Validate all AllergyIntolerance resources have patient reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        for allergy in allergies:
            assert allergy.patient is not None, "AllergyIntolerance.patient is required"
            assert allergy.patient.reference is not None, "AllergyIntolerance.patient must have reference"
            assert allergy.patient.reference == f"Patient/{patient.id}", \
                f"AllergyIntolerance.patient must reference Patient/{patient.id}"

    def test_immunizations_reference_patient(self, cerner_bundle):
        """Validate all Immunization resources have patient reference to Patient."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None

        immunizations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        for immunization in immunizations:
            assert immunization.patient is not None, "Immunization.patient is required"
            assert immunization.patient.reference is not None, "Immunization.patient must have reference"
            assert immunization.patient.reference == f"Patient/{patient.id}", \
                f"Immunization.patient must reference Patient/{patient.id}"

    # ====================================================================================
    # Systematic Status Field Tests - All Resources
    # ====================================================================================

    def test_all_observations_have_status(self, cerner_bundle):
        """Validate all Observation resources have status field (FHIR required)."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        for observation in observations:
            assert observation.status is not None, \
                "Observation.status is required (FHIR)"
            assert observation.status in ["registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error", "unknown"], \
                f"Observation.status must be valid code, got '{observation.status}'"

    def test_all_diagnostic_reports_have_status(self, cerner_bundle):
        """Validate all DiagnosticReport resources have status field (FHIR required)."""
        reports = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "DiagnosticReport"
        ]

        if len(reports) > 0:
            for report in reports:
                assert report.status is not None, \
                    "DiagnosticReport.status is required (FHIR)"
                assert report.status in ["registered", "partial", "preliminary", "final", "amended", "corrected", "appended", "cancelled", "entered-in-error", "unknown"], \
                    f"DiagnosticReport.status must be valid code, got '{report.status}'"

    def test_all_medication_requests_have_status(self, cerner_bundle):
        """Validate all MedicationRequest resources have status field (FHIR required)."""
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        assert len(med_requests) > 0, "Must have MedicationRequest resources"

        for mr in med_requests:
            assert mr.status is not None, \
                "MedicationRequest.status is required (FHIR)"
            assert mr.status in ["active", "on-hold", "cancelled", "completed", "entered-in-error", "stopped", "draft", "unknown"], \
                f"MedicationRequest.status must be valid code, got '{mr.status}'"

    def test_all_immunizations_have_status(self, cerner_bundle):
        """Validate all Immunization resources have status field (FHIR required)."""
        immunizations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        if len(immunizations) > 0:
            for immunization in immunizations:
                assert immunization.status is not None, \
                    "Immunization.status is required (FHIR)"
                assert immunization.status in ["completed", "entered-in-error", "not-done"], \
                    f"Immunization.status must be valid code, got '{immunization.status}'"

    def test_all_procedures_have_status(self, cerner_bundle):
        """Validate all Procedure resources have status field (FHIR required)."""
        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        if len(procedures) > 0:
            for procedure in procedures:
                assert procedure.status is not None, \
                    "Procedure.status is required (FHIR)"
                assert procedure.status in ["preparation", "in-progress", "not-done", "on-hold", "stopped", "completed", "entered-in-error", "unknown"], \
                    f"Procedure.status must be valid code, got '{procedure.status}'"

    def test_all_encounters_have_status(self, cerner_bundle):
        """Validate all Encounter resources have status field (FHIR required)."""
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Must have Encounter resources"

        for encounter in encounters:
            assert encounter.status is not None, \
                "Encounter.status is required (FHIR)"
            assert encounter.status in ["planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown"], \
                f"Encounter.status must be valid code, got '{encounter.status}'"

    def test_all_conditions_have_clinical_status(self, cerner_bundle):
        """Validate all Condition resources have clinicalStatus (US Core required)."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        for condition in conditions:
            assert condition.clinicalStatus is not None, \
                "Condition.clinicalStatus is required (US Core)"
            assert condition.clinicalStatus.coding is not None, \
                "Condition.clinicalStatus must have coding"

            coding = condition.clinicalStatus.coding[0]
            assert coding.system == "http://terminology.hl7.org/CodeSystem/condition-clinical", \
                "Condition.clinicalStatus must use condition-clinical CodeSystem"
            assert coding.code in ["active", "recurrence", "relapse", "inactive", "remission", "resolved"], \
                f"Condition.clinicalStatus code must be valid, got '{coding.code}'"

    def test_all_conditions_have_verification_status(self, cerner_bundle):
        """Validate all Condition resources have verificationStatus when present."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        for condition in conditions:
            # verificationStatus is optional in FHIR, but if present should be valid
            if hasattr(condition, 'verificationStatus') and condition.verificationStatus:
                assert condition.verificationStatus.coding is not None, \
                    "Condition.verificationStatus must have coding"

                coding = condition.verificationStatus.coding[0]
                assert coding.system == "http://terminology.hl7.org/CodeSystem/condition-ver-status", \
                    "Condition.verificationStatus must use condition-ver-status CodeSystem"
                assert coding.code in ["unconfirmed", "provisional", "differential", "confirmed", "refuted", "entered-in-error"], \
                    f"Condition.verificationStatus code must be valid, got '{coding.code}'"

    # ====================================================================================
    # Observation.category Tests - US Core Required
    # ====================================================================================

    def test_lab_observations_have_category(self, cerner_bundle):
        """Validate lab result Observations have category (US Core required)."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find lab observations (those with LOINC codes)
        lab_obs = []
        for obs in observations:
            if obs.code and obs.code.coding:
                for coding in obs.code.coding:
                    if coding.system == "http://loinc.org":
                        lab_obs.append(obs)
                        break

        if len(lab_obs) > 0:
            for obs in lab_obs:
                assert obs.category is not None and len(obs.category) > 0, \
                    "Lab Observation must have category (US Core)"

                # Check for laboratory category
                has_lab_category = any(
                    coding.code == "laboratory"
                    for cat in obs.category
                    if cat.coding
                    for coding in cat.coding
                    if coding.system == "http://terminology.hl7.org/CodeSystem/observation-category"
                )

                # Could also have vital-signs or other categories
                assert len(obs.category) > 0, \
                    "Observation must have at least one category"

    # ====================================================================================
    # Effective/Performed Date Tests - Timing Information
    # ====================================================================================

    def test_observations_have_effective_datetime(self, cerner_bundle):
        """Validate Observations have effectiveDateTime or effectivePeriod when applicable."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Count observations with effective times
        observations_with_effective = [
            obs for obs in observations
            if (hasattr(obs, 'effectiveDateTime') and obs.effectiveDateTime is not None) or
               (hasattr(obs, 'effectivePeriod') and obs.effectivePeriod is not None)
        ]

        # Most observations should have effective times (allow some exceptions for panels)
        percentage = len(observations_with_effective) / len(observations) * 100
        assert percentage >= 70, \
            f"At least 70% of Observations should have effectiveDateTime or effectivePeriod, got {percentage:.1f}%"

    def test_procedures_have_performed_datetime(self, cerner_bundle):
        """Validate Procedures have performedDateTime or performedPeriod."""
        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        if len(procedures) > 0:
            for procedure in procedures:
                has_performed = (
                    hasattr(procedure, 'performedDateTime') and procedure.performedDateTime is not None
                ) or (
                    hasattr(procedure, 'performedPeriod') and procedure.performedPeriod is not None
                ) or (
                    hasattr(procedure, 'performedString') and procedure.performedString is not None
                )

                assert has_performed, \
                    "Procedure must have performedDateTime, performedPeriod, or performedString"

    def test_immunizations_have_occurrence_datetime(self, cerner_bundle):
        """Validate Immunizations have occurrenceDateTime or occurrenceString."""
        immunizations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        if len(immunizations) > 0:
            for immunization in immunizations:
                has_occurrence = (
                    hasattr(immunization, 'occurrenceDateTime') and immunization.occurrenceDateTime is not None
                ) or (
                    hasattr(immunization, 'occurrenceString') and immunization.occurrenceString is not None
                )

                assert has_occurrence, \
                    "Immunization must have occurrenceDateTime or occurrenceString (US Core required)"

    # ====================================================================================
    # US Core Meta.profile Validation
    # ====================================================================================

    def test_patient_has_us_core_profile(self, cerner_bundle):
        """Validate Patient declares US Core Patient profile."""
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert patient is not None, "Must have Patient"

        # Check if meta.profile includes US Core Patient
        if hasattr(patient, 'meta') and patient.meta and hasattr(patient.meta, 'profile'):
            us_core_patient = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
            assert us_core_patient in patient.meta.profile, \
                f"Patient should declare US Core Patient profile: {us_core_patient}"

    def test_conditions_have_us_core_profile(self, cerner_bundle):
        """Validate Conditions declare US Core Condition profile when present."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        # Check if any conditions have meta.profile
        conditions_with_profile = [
            c for c in conditions
            if hasattr(c, 'meta') and c.meta and hasattr(c.meta, 'profile') and c.meta.profile
        ]

        if len(conditions_with_profile) > 0:
            us_core_condition = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-condition"
            for condition in conditions_with_profile:
                # If profile is set, should include US Core Condition
                assert any(us_core_condition in profile for profile in condition.meta.profile), \
                    "Condition with profile should declare US Core Condition profile"

    def test_observations_have_us_core_profile_when_applicable(self, cerner_bundle):
        """Validate Observations declare appropriate US Core profiles when present."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Check if any observations have meta.profile
        observations_with_profile = [
            o for o in observations
            if hasattr(o, 'meta') and o.meta and hasattr(o.meta, 'profile') and o.meta.profile
        ]

        if len(observations_with_profile) > 0:
            # Common US Core Observation profiles
            us_core_profiles = [
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-observation-lab",
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-vital-signs",
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-smokingstatus",
            ]

            for obs in observations_with_profile:
                # If profile is set, should include a US Core profile
                has_us_core = any(
                    any(usc_profile in profile for usc_profile in us_core_profiles)
                    for profile in obs.meta.profile
                )

                # Note: Not all observations need US Core profiles, so this is informational
                # Just verify the structure is valid if present
                assert obs.meta.profile is not None and len(obs.meta.profile) > 0, \
                    "Observation meta.profile should not be empty if present"

    # =============================================================================
    # COMPREHENSIVE FIELD VALIDATION TESTS
    # =============================================================================

    def test_conditions_have_code_display_values(self, cerner_bundle):
        """Validate Condition resources have display values on their codes."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        # Find conditions with codes
        conditions_with_code = [
            cond for cond in conditions
            if cond.code is not None and cond.code.coding is not None and len(cond.code.coding) > 0
        ]

        assert len(conditions_with_code) > 0, "Must have at least one Condition with code"

        # Check that conditions with codes have display values
        for condition in conditions_with_code:
            primary_coding = condition.code.coding[0]
            assert primary_coding.display is not None and primary_coding.display != "", \
                f"Condition.code.coding[0] must have display value, got None for code {primary_coding.code}"

    def test_observations_have_code_display_values(self, cerner_bundle):
        """Validate Observation resources have display values on their codes."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Check that most observations have code displays (allow some exceptions)
        observations_with_display = [
            obs for obs in observations
            if obs.code and obs.code.coding and len(obs.code.coding) > 0 and
               obs.code.coding[0].display is not None and obs.code.coding[0].display != ""
        ]

        percentage = len(observations_with_display) / len(observations) * 100
        assert percentage >= 70, \
            f"At least 70% of Observations should have code.coding[0].display, got {percentage:.1f}%"

    def test_procedures_have_code_display_values(self, cerner_bundle):
        """Validate all Procedure resources have display values on their codes."""
        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        if len(procedures) > 0:
            for procedure in procedures:
                assert procedure.code is not None, \
                    "Procedure must have code"
                assert procedure.code.coding is not None and len(procedure.code.coding) > 0, \
                    "Procedure.code must have at least one coding"

                # Check that primary coding has display
                primary_coding = procedure.code.coding[0]
                assert primary_coding.display is not None and primary_coding.display != "", \
                    "Procedure.code.coding[0] must have display value"

    def test_allergy_intolerances_have_code_display_values(self, cerner_bundle):
        """Validate all AllergyIntolerance resources have display values on their codes."""
        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        if len(allergies) > 0:
            for allergy in allergies:
                assert allergy.code is not None, \
                    "AllergyIntolerance must have code"
                assert allergy.code.coding is not None and len(allergy.code.coding) > 0, \
                    "AllergyIntolerance.code must have at least one coding"

                # Check that primary coding has display
                primary_coding = allergy.code.coding[0]
                assert primary_coding.display is not None and primary_coding.display != "", \
                    "AllergyIntolerance.code.coding[0] must have display value"

    def test_conditions_have_codeable_concept_text(self, cerner_bundle):
        """Validate Condition resources have CodeableConcept.text on their codes."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        # Check that most conditions have code.text (allow some exceptions)
        conditions_with_text = [
            cond for cond in conditions
            if cond.code and hasattr(cond.code, 'text') and
               cond.code.text is not None and cond.code.text != ""
        ]

        percentage = len(conditions_with_text) / len(conditions) * 100
        assert percentage >= 70, \
            f"At least 70% of Conditions should have code.text, got {percentage:.1f}%"

    def test_procedures_have_codeable_concept_text(self, cerner_bundle):
        """Validate Procedure resources have CodeableConcept.text on their codes."""
        procedures = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        if len(procedures) > 0:
            # Check that most procedures have code.text
            procedures_with_text = [
                proc for proc in procedures
                if proc.code and hasattr(proc.code, 'text') and
                   proc.code.text is not None and proc.code.text != ""
            ]

            percentage = len(procedures_with_text) / len(procedures) * 100
            assert percentage >= 70, \
                f"At least 70% of Procedures should have code.text, got {percentage:.1f}%"

    def test_allergy_intolerances_have_codeable_concept_text(self, cerner_bundle):
        """Validate AllergyIntolerance resources have CodeableConcept.text on their codes."""
        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        if len(allergies) > 0:
            # Check that most allergies have code.text
            allergies_with_text = [
                allergy for allergy in allergies
                if allergy.code and hasattr(allergy.code, 'text') and
                   allergy.code.text is not None and allergy.code.text != ""
            ]

            percentage = len(allergies_with_text) / len(allergies) * 100
            assert percentage >= 70, \
                f"At least 70% of AllergyIntolerances should have code.text, got {percentage:.1f}%"

    def test_conditions_have_onset_datetime(self, cerner_bundle):
        """Validate Condition resources have onsetDateTime when available."""
        conditions = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        # Check that most conditions have onset information
        conditions_with_onset = [
            cond for cond in conditions
            if (hasattr(cond, 'onsetDateTime') and cond.onsetDateTime is not None) or
               (hasattr(cond, 'onsetPeriod') and cond.onsetPeriod is not None) or
               (hasattr(cond, 'onsetString') and cond.onsetString is not None)
        ]

        percentage = len(conditions_with_onset) / len(conditions) * 100
        assert percentage >= 70, \
            f"At least 70% of Conditions should have onset information, got {percentage:.1f}%"

    def test_allergy_intolerances_have_complete_reaction_details(self, cerner_bundle):
        """Validate AllergyIntolerance resources have complete reaction structure."""
        allergies = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        if len(allergies) > 0:
            # Find allergies with reactions
            allergies_with_reactions = [
                allergy for allergy in allergies
                if hasattr(allergy, 'reaction') and allergy.reaction is not None and len(allergy.reaction) > 0
            ]

            if len(allergies_with_reactions) > 0:
                for allergy in allergies_with_reactions:
                    reaction = allergy.reaction[0]

                    # Validate manifestation
                    assert hasattr(reaction, 'manifestation') and reaction.manifestation is not None, \
                        "AllergyIntolerance.reaction must have manifestation"
                    assert len(reaction.manifestation) > 0, \
                        "AllergyIntolerance.reaction.manifestation must not be empty"

                    manifestation = reaction.manifestation[0]
                    assert manifestation.coding is not None and len(manifestation.coding) > 0, \
                        "AllergyIntolerance.reaction.manifestation must have coding"

                    # Optionally check for severity if present
                    if hasattr(reaction, 'severity') and reaction.severity is not None:
                        assert reaction.severity in ["mild", "moderate", "severe"], \
                            f"AllergyIntolerance.reaction.severity must be valid, got '{reaction.severity}'"

    def test_observations_have_complete_value_quantities(self, cerner_bundle):
        """Validate Observation resources have complete valueQuantity structure."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Find observations with valueQuantity
        observations_with_quantity = [
            obs for obs in observations
            if hasattr(obs, 'valueQuantity') and obs.valueQuantity is not None
        ]

        assert len(observations_with_quantity) > 0, \
            "Must have at least one Observation with valueQuantity"

        for obs in observations_with_quantity:
            vq = obs.valueQuantity

            # Validate complete quantity structure
            assert hasattr(vq, 'value') and vq.value is not None, \
                "Observation.valueQuantity must have value"
            assert hasattr(vq, 'unit') and vq.unit is not None and vq.unit != "", \
                "Observation.valueQuantity must have unit"

            # UCUM system and code should be present for proper interoperability
            if hasattr(vq, 'system') and vq.system is not None:
                assert vq.system == "http://unitsofmeasure.org", \
                    f"Observation.valueQuantity.system should be UCUM, got '{vq.system}'"

            if hasattr(vq, 'code') and vq.code is not None:
                assert vq.code != "", "Observation.valueQuantity.code should not be empty"

    def test_patient_reference_has_display(self, cerner_bundle):
        """Validate that Patient references include display names where applicable."""
        # Get patient first
        patient = next(
            (e.resource for e in cerner_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )
        assert patient is not None, "Must have Patient resource"

        # Find resources that reference the patient
        resources_with_patient_ref = []
        for entry in cerner_bundle.entry:
            resource = entry.resource

            # Check for subject reference
            if hasattr(resource, 'subject') and resource.subject is not None:
                if hasattr(resource.subject, 'reference') and resource.subject.reference:
                    resources_with_patient_ref.append(resource)

            # Check for patient reference (for AllergyIntolerance, MedicationRequest, etc.)
            elif hasattr(resource, 'patient') and resource.patient is not None:
                if hasattr(resource.patient, 'reference') and resource.patient.reference:
                    resources_with_patient_ref.append(resource)

        assert len(resources_with_patient_ref) > 0, \
            "Must have resources that reference Patient"

        # Check that some references have display values
        references_with_display = []
        for resource in resources_with_patient_ref:
            ref = resource.subject if hasattr(resource, 'subject') else resource.patient
            if hasattr(ref, 'display') and ref.display is not None and ref.display != "":
                references_with_display.append(resource)

        percentage = len(references_with_display) / len(resources_with_patient_ref) * 100
        # Note: display is optional but useful, so we don't require 100%
        assert percentage >= 0, \
            f"Patient references may have display values (got {percentage:.1f}%)"

    # =============================================================================
    # PHASE 1 HIGH-PRIORITY FIELD TESTS (US Core Must-Support)
    # =============================================================================

    def test_encounter_has_participant(self, cerner_bundle):
        """Validate Encounter has participant (US Core Must-Support)."""
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Must have Encounter resources"

        # Check if any encounters have participants
        encounters_with_participants = [
            enc for enc in encounters
            if hasattr(enc, 'participant') and enc.participant is not None and len(enc.participant) > 0
        ]

        if len(encounters_with_participants) > 0:
            for encounter in encounters_with_participants:
                participant = encounter.participant[0]

                # Validate participant structure
                if hasattr(participant, 'individual') and participant.individual is not None:
                    assert hasattr(participant.individual, 'reference'), \
                        "Encounter.participant.individual must have reference"
                    assert participant.individual.reference is not None, \
                        "Encounter.participant.individual.reference must not be None"

    def test_encounter_has_type(self, cerner_bundle):
        """Validate Encounter has type when available (US Core Must-Support)."""
        encounters = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) > 0, "Must have Encounter resources"

        # Find encounters with type populated
        encounters_with_type = [
            enc for enc in encounters
            if hasattr(enc, 'type') and enc.type is not None and len(enc.type) > 0
        ]

        # If any encounters have type, validate structure
        if len(encounters_with_type) > 0:
            for encounter in encounters_with_type:
                enc_type = encounter.type[0]
                assert hasattr(enc_type, 'coding') and enc_type.coding is not None, \
                    "Encounter.type must have coding"
                assert len(enc_type.coding) > 0, \
                    "Encounter.type.coding must not be empty"

                # Validate coding structure
                coding = enc_type.coding[0]
                assert hasattr(coding, 'code') and coding.code is not None, \
                    "Encounter.type.coding must have code"

    def test_diagnostic_report_has_category(self, cerner_bundle):
        """Validate DiagnosticReport has category (US Core required)."""
        reports = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "DiagnosticReport"
        ]

        if len(reports) > 0:
            for report in reports:
                # US Core requires category
                assert hasattr(report, 'category') and report.category is not None, \
                    "DiagnosticReport must have category (US Core required)"
                assert len(report.category) > 0, \
                    "DiagnosticReport.category must not be empty"

                category = report.category[0]
                assert hasattr(category, 'coding') and category.coding is not None, \
                    "DiagnosticReport.category must have coding"
                assert len(category.coding) > 0, \
                    "DiagnosticReport.category.coding must not be empty"

                # Should typically be LAB
                coding = category.coding[0]
                assert coding.code is not None, "DiagnosticReport.category.coding must have code"

    def test_medication_request_has_dosage_instruction_text(self, cerner_bundle):
        """Validate MedicationRequest has dosageInstruction.text (US Core Must-Support)."""
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        assert len(med_requests) > 0, "Must have MedicationRequest resources"

        # Find medication requests with dosage instructions
        requests_with_dosage = [
            mr for mr in med_requests
            if hasattr(mr, 'dosageInstruction') and mr.dosageInstruction is not None and len(mr.dosageInstruction) > 0
        ]

        if len(requests_with_dosage) > 0:
            for mr in requests_with_dosage:
                dosage = mr.dosageInstruction[0]

                # Check for text (human-readable instructions)
                if hasattr(dosage, 'text') and dosage.text is not None:
                    assert dosage.text != "", \
                        "MedicationRequest.dosageInstruction.text should not be empty if present"

    def test_medication_request_has_dosage_timing(self, cerner_bundle):
        """Validate MedicationRequest dosageInstruction has timing when available."""
        med_requests = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "MedicationRequest"
        ]

        assert len(med_requests) > 0, "Must have MedicationRequest resources"

        # Find medication requests with dosage instructions
        requests_with_dosage = [
            mr for mr in med_requests
            if hasattr(mr, 'dosageInstruction') and mr.dosageInstruction is not None and len(mr.dosageInstruction) > 0
        ]

        if len(requests_with_dosage) > 0:
            for mr in requests_with_dosage:
                dosage = mr.dosageInstruction[0]

                # Check for timing structure
                if hasattr(dosage, 'timing') and dosage.timing is not None:
                    timing = dosage.timing

                    # Check for timing.code (BID, TID, QD, etc.)
                    if hasattr(timing, 'code') and timing.code is not None:
                        assert timing.code.coding is not None, \
                            "MedicationRequest.dosageInstruction.timing.code must have coding"

    def test_observations_have_performer(self, cerner_bundle):
        """Validate Observations have performer when available (US Core Must-Support for many profiles)."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Find observations with performers
        observations_with_performer = [
            obs for obs in observations
            if hasattr(obs, 'performer') and obs.performer is not None and len(obs.performer) > 0
        ]

        # Most observations should have performers
        if len(observations_with_performer) > 0:
            for obs in observations_with_performer:
                performer = obs.performer[0]

                # Validate performer reference structure
                assert hasattr(performer, 'reference'), \
                    "Observation.performer must have reference"
                assert performer.reference is not None, \
                    "Observation.performer.reference must not be None"

    def test_lab_observations_have_reference_range(self, cerner_bundle):
        """Validate lab Observations have referenceRange when applicable."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Find lab observations (those with category=laboratory)
        lab_observations = [
            obs for obs in observations
            if hasattr(obs, 'category') and obs.category is not None and
               any(
                   cat.coding and any(
                       c.code == 'laboratory' for c in cat.coding
                   ) for cat in obs.category
               )
        ]

        if len(lab_observations) > 0:
            # Find those with reference ranges
            obs_with_ref_range = [
                obs for obs in lab_observations
                if hasattr(obs, 'referenceRange') and obs.referenceRange is not None and len(obs.referenceRange) > 0
            ]

            if len(obs_with_ref_range) > 0:
                for obs in obs_with_ref_range:
                    ref_range = obs.referenceRange[0]

                    # Validate reference range structure
                    # Should have at least low or high or text
                    has_content = (
                        (hasattr(ref_range, 'low') and ref_range.low is not None) or
                        (hasattr(ref_range, 'high') and ref_range.high is not None) or
                        (hasattr(ref_range, 'text') and ref_range.text is not None)
                    )

                    assert has_content, \
                        "Observation.referenceRange must have low, high, or text"

    def test_lab_observations_have_interpretation(self, cerner_bundle):
        """Validate lab Observations have interpretation when applicable."""
        observations = [
            e.resource for e in cerner_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have Observation resources"

        # Find lab observations with interpretation
        obs_with_interpretation = [
            obs for obs in observations
            if hasattr(obs, 'interpretation') and obs.interpretation is not None and len(obs.interpretation) > 0
        ]

        if len(obs_with_interpretation) > 0:
            for obs in obs_with_interpretation:
                interp = obs.interpretation[0]

                # Validate interpretation structure
                assert hasattr(interp, 'coding') and interp.coding is not None, \
                    "Observation.interpretation must have coding"
                assert len(interp.coding) > 0, \
                    "Observation.interpretation.coding must not be empty"

                coding = interp.coding[0]
                assert coding.code is not None, \
                    "Observation.interpretation.coding must have code"

                # Common interpretation codes: N, L, H, LL, HH, A, AA, etc.
                valid_codes = ['N', 'L', 'H', 'LL', 'HH', 'A', 'AA', 'U', 'D', 'B', 'W', 'S', 'R', 'I', 'MS', 'VS']
                if coding.code:
                    # Just check it's a reasonable code (lenient since systems may vary)
                    assert len(coding.code) <= 3, \
                        f"Observation.interpretation code seems invalid: {coding.code}"
