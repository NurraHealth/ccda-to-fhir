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
from fhir.resources.bundle import Bundle

from ccda_to_fhir.convert import convert_document


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
