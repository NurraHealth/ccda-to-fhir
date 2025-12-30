"""End-to-end tests for Agastha CCD conversion - Alice Newman.

Tests the conversion of a real-world Agastha CCD document (195352.xml)
to FHIR R4B resources, validating specific clinical data mappings.

Patient: Alice Newman, Female, Beaverton OR
Key Clinical Data:
- Conditions: Fever, Chronic renal transplant rejection, Essential HTN, Overweight, Hypothyroidism
- Allergies: Penicillin G, Ampicillin (both active)
- Medications: CefTRIAXone, Aranesp, Tylenol
- Immunizations: 2 completed + 1 negated with statusReason (PATOBJ)
- Procedures: Cardiac pacemaker insertion, Nebulizer therapy
- Goals: 2 resident care goals
- Observations: 17 (vital signs, labs, functional status)
- Device: Implantable cardiac pacemaker
- RelatedPerson: Contact person

Key Features Tested:
- ✅ Immunization.statusReason for negated immunizations with refusal reasons
- ✅ Device resource (cardiac pacemaker)
- ✅ Goal resources with lifecycle status
- ✅ RelatedPerson contact
- ✅ Multiple active allergies
- ✅ Chronic kidney transplant condition
"""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle
from tests.integration.helpers.codeable_concept_validators import (
    assert_allergy_clinical_status,
    assert_immunization_status_reason,
    assert_observation_category,
)
from tests.integration.helpers.quantity_validators import (
    assert_quantity_has_ucum,
)
from tests.integration.helpers.temporal_validators import (
    assert_datetime_format,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "documents"
AGASTHA_CCD = FIXTURES_DIR / "agastha_ccd.xml"


class TestAgasthaE2E:
    """Test conversion of Agastha CCD (Alice Newman) to FHIR Bundle."""

    @pytest.fixture
    def agastha_bundle(self):
        """Convert Agastha CCD to FHIR Bundle."""
        with open(AGASTHA_CCD) as f:
            xml = f.read()
        result = convert_document(xml)
        return Bundle(**result["bundle"])

    # ========================================================================
    # BUNDLE STRUCTURE
    # ========================================================================

    def test_bundle_structure(self, agastha_bundle):
        """Validate Bundle has expected structure."""
        assert agastha_bundle.type == "document"
        assert len(agastha_bundle.entry) == 48, "Bundle must contain exactly 48 resources"

        # Verify has Patient and Composition
        has_patient = any(e.resource.get_resource_type() == "Patient" for e in agastha_bundle.entry)
        has_composition = any(e.resource.get_resource_type() == "Composition" for e in agastha_bundle.entry)
        assert has_patient, "Bundle must contain Patient resource"
        assert has_composition, "Bundle must contain Composition resource"

    def test_resource_counts(self, agastha_bundle):
        """Validate exact resource counts for each type."""
        from collections import Counter
        resource_types = Counter(e.resource.get_resource_type() for e in agastha_bundle.entry)

        assert resource_types["Patient"] == 1
        assert resource_types["Composition"] == 1
        assert resource_types["Condition"] == 6
        assert resource_types["AllergyIntolerance"] == 2
        assert resource_types["MedicationStatement"] == 3
        assert resource_types["Immunization"] == 3
        assert resource_types["Procedure"] == 2
        assert resource_types["Goal"] == 2
        assert resource_types["Observation"] == 17
        assert resource_types["Device"] == 1
        assert resource_types["RelatedPerson"] == 1
        assert resource_types["DocumentReference"] == 1
        assert resource_types["DiagnosticReport"] == 1

    # ========================================================================
    # PATIENT - Alice Newman
    # ========================================================================

    def test_patient_alice_newman_demographics(self, agastha_bundle):
        """Validate patient Alice Newman has correct demographics."""
        patient = next(
            (e.resource for e in agastha_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert patient is not None, "Bundle must contain Patient"

        # Name: Alice Jones Newman
        assert len(patient.name) > 0, "Patient must have name"
        name = patient.name[0]
        assert "Alice" in name.given, "Patient given name must include 'Alice'"
        assert "Jones" in name.given, "Patient middle name must include 'Jones'"
        assert name.family == "Newman", "Patient family name must be 'Newman'"

        # Gender and birth date
        assert patient.gender == "female", "Patient gender must be 'female'"
        assert patient.birthDate is not None, "Patient must have birthDate"

    def test_patient_address_beaverton_oregon(self, agastha_bundle):
        """Validate patient address in Beaverton, Oregon."""
        patient = next(
            (e.resource for e in agastha_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert len(patient.address) > 0, "Patient must have address"
        address = patient.address[0]
        assert address.city == "Beaverton", "City must be 'Beaverton'"
        assert address.state == "OR", "State must be 'OR'"
        assert address.postalCode == "97006", "Postal code must be '97006'"

    def test_patient_has_related_person_contact(self, agastha_bundle):
        """Validate patient has RelatedPerson contact."""
        related_persons = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "RelatedPerson"
        ]

        assert len(related_persons) == 1, "Must have exactly 1 RelatedPerson"
        related_person = related_persons[0]
        assert related_person.patient is not None, "RelatedPerson must reference patient"

    # ========================================================================
    # CONDITIONS (6)
    # ========================================================================

    def test_condition_fever(self, agastha_bundle):
        """Validate Condition: Fever (SNOMED 386661006)."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        fever = next(
            (c for c in conditions
             if any(coding.code == "386661006" for coding in c.code.coding)),
            None
        )

        assert fever is not None, "Must have Fever condition"
        assert fever.clinicalStatus is not None, "Condition must have clinicalStatus"
        assert fever.subject is not None, "Condition must reference patient"

    def test_condition_chronic_renal_transplant_rejection(self, agastha_bundle):
        """Validate Condition: Chronic rejection of renal transplant (SNOMED 236578006)."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        rejection = next(
            (c for c in conditions
             if any(coding.code == "236578006" for coding in c.code.coding)),
            None
        )

        assert rejection is not None, "Must have chronic renal transplant rejection condition"

        # Verify SNOMED coding
        snomed_coding = next(
            (coding for coding in rejection.code.coding
             if coding.system == "http://snomed.info/sct"),
            None
        )
        assert snomed_coding is not None, "Must have SNOMED coding"
        assert snomed_coding.display == "Chronic rejection of renal transplant"

    def test_condition_essential_hypertension(self, agastha_bundle):
        """Validate Condition: Essential Hypertension (SNOMED 59621000)."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        htn = next(
            (c for c in conditions
             if any(coding.code == "59621000" for coding in c.code.coding)),
            None
        )

        assert htn is not None, "Must have Essential Hypertension condition"

    def test_condition_overweight(self, agastha_bundle):
        """Validate Condition: Overweight (SNOMED 238131007)."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        overweight = next(
            (c for c in conditions
             if any(coding.code == "238131007" for coding in c.code.coding)),
            None
        )

        assert overweight is not None, "Must have Overweight condition"

    def test_condition_severe_hypothyroidism(self, agastha_bundle):
        """Validate Condition: Severe Hypothyroidism (SNOMED 83986005)."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        hypothyroid = next(
            (c for c in conditions
             if any(coding.code == "83986005" for coding in c.code.coding)),
            None
        )

        assert hypothyroid is not None, "Must have Severe Hypothyroidism condition"

    def test_conditions_have_category(self, agastha_bundle):
        """Validate all Conditions have exact category CodeableConcept."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        for condition in conditions:
            assert condition.category is not None, \
                f"Condition {condition.id} must have category"
            assert len(condition.category) > 0, \
                f"Condition {condition.id} category must not be empty"

            # PHASE 1.1: Verify exact category CodeableConcept structure
            # Conditions should have either problem-list-item or encounter-diagnosis
            for category in condition.category:
                coding = category.coding[0]
                assert coding.system == "http://terminology.hl7.org/CodeSystem/condition-category", \
                    f"Condition {condition.id} category must have correct system"
                assert coding.code in ["problem-list-item", "encounter-diagnosis"], \
                    f"Condition {condition.id} category code must be valid"

    # ========================================================================
    # ALLERGIES (2)
    # ========================================================================

    def test_allergy_penicillin_g(self, agastha_bundle):
        """Validate AllergyIntolerance: Penicillin G (RxNorm 7980)."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        penicillin = next(
            (a for a in allergies
             if any(coding.code == "7980" for coding in a.code.coding)),
            None
        )

        assert penicillin is not None, "Must have Penicillin G allergy"
        assert penicillin.clinicalStatus is not None, "Allergy must have clinicalStatus"

        # PHASE 1.1: Verify exact clinicalStatus CodeableConcept structure
        assert_allergy_clinical_status(penicillin.clinicalStatus, "active")

    def test_allergy_ampicillin(self, agastha_bundle):
        """Validate AllergyIntolerance: Ampicillin (RxNorm 733)."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        ampicillin = next(
            (a for a in allergies
             if any(coding.code == "733" for coding in a.code.coding)),
            None
        )

        assert ampicillin is not None, "Must have Ampicillin allergy"

        # PHASE 1.1: Verify exact clinicalStatus CodeableConcept structure
        assert_allergy_clinical_status(ampicillin.clinicalStatus, "active")

    def test_allergies_have_patient_reference(self, agastha_bundle):
        """Validate all AllergyIntolerances reference the patient."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        for allergy in allergies:
            assert allergy.patient is not None, \
                f"Allergy {allergy.id} must reference patient"
            assert allergy.patient.reference is not None, \
                f"Allergy {allergy.id} patient reference must not be null"

    def test_allergy_reaction_manifestation_exact(self, agastha_bundle):
        """PHASE 1.2: Validate AllergyIntolerance.reaction.manifestation exact structure."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        # Find allergies with reactions
        allergies_with_reactions = [a for a in allergies if a.reaction and len(a.reaction) > 0]

        for allergy in allergies_with_reactions:
            for reaction in allergy.reaction:
                # Manifestation must exist and have CodeableConcept structure
                assert reaction.manifestation is not None, \
                    f"Allergy {allergy.id} reaction must have manifestation"
                assert len(reaction.manifestation) > 0, \
                    f"Allergy {allergy.id} reaction.manifestation must not be empty"

                # Each manifestation should have SNOMED coding
                for manifestation in reaction.manifestation:
                    assert manifestation.coding is not None, \
                        "Reaction manifestation must have coding"
                    assert len(manifestation.coding) > 0, \
                        "Reaction manifestation must have at least one coding"

                    # Find SNOMED coding (should be primary)
                    snomed_coding = next(
                        (c for c in manifestation.coding if c.system == "http://snomed.info/sct"),
                        None
                    )
                    assert snomed_coding is not None, \
                        "Reaction manifestation must have SNOMED CT coding"
                    assert snomed_coding.code is not None, \
                        "SNOMED coding must have code"
                    # CONVERTER FIXED: Display text now populated from C-CDA or terminology map
                    # Note: Display may still be None if C-CDA lacks it AND code not in our maps
                    # For now, just verify it exists when C-CDA provides it

    def test_allergy_reaction_severity_exact(self, agastha_bundle):
        """PHASE 1.2: Validate AllergyIntolerance.reaction.severity exact values."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        # Find allergies with reactions that have severity
        for allergy in allergies:
            if allergy.reaction:
                for reaction in allergy.reaction:
                    if reaction.severity:
                        # Severity must be exact value from FHIR value set
                        assert reaction.severity in ["mild", "moderate", "severe"], \
                            f"Reaction severity must be 'mild', 'moderate', or 'severe', got '{reaction.severity}'"

    def test_allergy_type_and_category_exact(self, agastha_bundle):
        """PHASE 1.2: Validate AllergyIntolerance.type and .category exact values."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        for allergy in allergies:
            # Type validation (if present)
            if allergy.type:
                assert allergy.type in ["allergy", "intolerance"], \
                    f"AllergyIntolerance.type must be 'allergy' or 'intolerance', got '{allergy.type}'"

            # Category validation (if present)
            if allergy.category:
                for category in allergy.category:
                    assert category in ["food", "medication", "environment", "biologic"], \
                        f"AllergyIntolerance.category must be valid value, got '{category}'"

    # ========================================================================
    # MEDICATIONS (3)
    # ========================================================================

    def test_medication_ceftriaxone(self, agastha_bundle):
        """Validate MedicationStatement: CefTRIAXone Sodium (RxNorm 309090)."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        ceftriaxone = next(
            (m for m in medications
             if any(coding.code == "309090" for coding in m.medicationCodeableConcept.coding)),
            None
        )

        assert ceftriaxone is not None, "Must have CefTRIAXone medication"
        assert ceftriaxone.status == "active", "CefTRIAXone must be active"

    def test_medication_aranesp(self, agastha_bundle):
        """Validate MedicationStatement: Aranesp (RxNorm 731241)."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        aranesp = next(
            (m for m in medications
             if any(coding.code == "731241" for coding in m.medicationCodeableConcept.coding)),
            None
        )

        assert aranesp is not None, "Must have Aranesp medication"
        assert aranesp.status == "active", "Aranesp must be active"

    def test_medication_tylenol(self, agastha_bundle):
        """Validate MedicationStatement: Tylenol Extra Strength (RxNorm 209459)."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        tylenol = next(
            (m for m in medications
             if any(coding.code == "209459" for coding in m.medicationCodeableConcept.coding)),
            None
        )

        assert tylenol is not None, "Must have Tylenol medication"
        assert tylenol.status == "active", "Tylenol must be active"

    def test_medications_have_subject(self, agastha_bundle):
        """Validate all MedicationStatements reference the patient."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        for med in medications:
            assert med.subject is not None, \
                f"Medication {med.id} must reference patient"

    def test_medication_dosage_route_exact(self, agastha_bundle):
        """PHASE 1.3: Validate MedicationStatement.dosage.route exact structure."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        # Find medications with dosage route
        for med in medications:
            if med.dosage:
                for dosage in med.dosage:
                    if dosage.route:
                        # Route must have CodeableConcept structure
                        assert dosage.route.coding is not None, \
                            f"Medication {med.id} dosage.route must have coding"
                        assert len(dosage.route.coding) > 0, \
                            f"Medication {med.id} dosage.route must have at least one coding"

                        # Route should have NCI Thesaurus or SNOMED system
                        route_coding = dosage.route.coding[0]
                        assert route_coding.system in [
                            "http://ncimeta.nci.nih.gov",
                            "http://snomed.info/sct"
                        ], f"Route system must be NCI Thesaurus or SNOMED, got '{route_coding.system}'"
                        assert route_coding.code is not None, "Route must have code"
                        assert route_coding.display is not None, "Route must have display"

    def test_medication_dosage_quantity_exact(self, agastha_bundle):
        """PHASE 1.3: Validate MedicationStatement.dosage.doseAndRate Quantity structure."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        # Find medications with dose quantities
        for med in medications:
            if med.dosage:
                for dosage in med.dosage:
                    if dosage.doseAndRate:
                        for dose_rate in dosage.doseAndRate:
                            if dose_rate.doseQuantity:
                                # Validate complete Quantity structure
                                # CONVERTER FIXED: Now uses strict validation
                                assert_quantity_has_ucum(
                                    dose_rate.doseQuantity,
                                    field_name=f"Medication {med.id} doseQuantity",
                                    strict_system=True
                                )

    def test_medication_dosage_timing_exact(self, agastha_bundle):
        """PHASE 1.3: Validate MedicationStatement.dosage.timing exact structure."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        # Find medications with timing
        for med in medications:
            if med.dosage:
                for dosage in med.dosage:
                    if dosage.timing and dosage.timing.repeat:
                        repeat = dosage.timing.repeat

                        # Validate frequency is integer if present
                        if repeat.frequency:
                            assert isinstance(repeat.frequency, int), \
                                f"Medication {med.id} timing.repeat.frequency must be integer"

                        # Validate period is numeric if present
                        # NOTE: FHIR libraries may use Decimal for precision
                        if repeat.period:
                            from decimal import Decimal
                            assert isinstance(repeat.period, (int, float, Decimal)), \
                                f"Medication {med.id} timing.repeat.period must be numeric"

                        # Validate periodUnit is valid UCUM temporal unit
                        if repeat.periodUnit:
                            valid_units = ["s", "min", "h", "d", "wk", "mo", "a"]
                            assert repeat.periodUnit in valid_units, \
                                f"Medication {med.id} timing.repeat.periodUnit must be valid UCUM unit, got '{repeat.periodUnit}'"

    # ========================================================================
    # IMMUNIZATIONS (3) - Including negated with statusReason
    # ========================================================================

    def test_immunizations_count(self, agastha_bundle):
        """Validate Bundle contains expected number of immunizations."""
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        assert len(immunizations) == 3, "Bundle must contain exactly 3 immunizations"

    def test_immunization_influenza_completed(self, agastha_bundle):
        """Validate Immunization: Influenza unspecified (CVX 88) - completed."""
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        influenza = next(
            (imm for imm in immunizations
             if any(coding.code == "88" for coding in imm.vaccineCode.coding)),
            None
        )

        assert influenza is not None, "Must have Influenza vaccination"
        assert influenza.status == "completed", "Influenza immunization must be completed"
        assert influenza.statusReason is None, "Completed immunization should not have statusReason"

    def test_immunization_dtap_completed(self, agastha_bundle):
        """Validate Immunization: DTaP (CVX 106) - completed."""
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        dtap = next(
            (imm for imm in immunizations
             if any(coding.code == "106" for coding in imm.vaccineCode.coding)),
            None
        )

        assert dtap is not None, "Must have DTaP vaccination"
        assert dtap.status == "completed", "DTaP immunization must be completed"
        assert dtap.statusReason is None, "Completed immunization should not have statusReason"

    def test_negated_immunization_has_status_reason(self, agastha_bundle):
        """Validate negated immunization has statusReason field - KEY FEATURE.

        The Agastha CCD has a negated immunization (Influenza vaccine CVX 166)
        with a refusal reason coded as PATOBJ (Patient objection).
        This should map to Immunization.statusReason.

        This is the primary reason we added this fixture - to test statusReason!
        """
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        # Find the negated immunization
        negated_immunizations = [imm for imm in immunizations if imm.status == "not-done"]
        assert len(negated_immunizations) == 1, "Must have exactly one negated immunization"

        negated_imm = negated_immunizations[0]

        # CRITICAL: Verify statusReason is present
        assert negated_imm.statusReason is not None, \
            "Negated immunization MUST have statusReason when refusal reason is coded"

        # PHASE 1.1: Verify exact statusReason CodeableConcept structure
        assert_immunization_status_reason(negated_imm.statusReason, "PATOBJ")

    def test_negated_immunization_vaccine_code(self, agastha_bundle):
        """Validate negated immunization has correct vaccine code (CVX 166)."""
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        negated_imm = next(imm for imm in immunizations if imm.status == "not-done")

        # Verify vaccine code
        assert negated_imm.vaccineCode is not None, "Must have vaccineCode"
        assert negated_imm.vaccineCode.coding is not None, "vaccineCode must have coding"

        # Find CVX coding
        cvx_coding = next(
            (c for c in negated_imm.vaccineCode.coding if c.system == "http://hl7.org/fhir/sid/cvx"),
            None
        )
        assert cvx_coding is not None, "Must have CVX coding"
        assert cvx_coding.code == "166", \
            f"Vaccine code must be '166' (Influenza Intradermal Quadrivalent), got '{cvx_coding.code}'"

    def test_immunizations_have_patient_reference(self, agastha_bundle):
        """Validate all Immunizations reference the patient."""
        immunizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Immunization"
        ]

        for imm in immunizations:
            assert imm.patient is not None, \
                f"Immunization {imm.id} must reference patient"

    # ========================================================================
    # PROCEDURES (2)
    # ========================================================================

    def test_procedure_cardiac_pacemaker_insertion(self, agastha_bundle):
        """Validate Procedure: Introduction of cardiac pacemaker (SNOMED 175135009)."""
        procedures = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        pacemaker = next(
            (p for p in procedures
             if any(coding.code == "175135009" for coding in p.code.coding)),
            None
        )

        assert pacemaker is not None, "Must have cardiac pacemaker insertion procedure"
        assert pacemaker.status == "completed", "Pacemaker procedure must be completed"
        assert pacemaker.subject is not None, "Procedure must reference patient"

    def test_procedure_nebulizer_therapy(self, agastha_bundle):
        """Validate Procedure: Nebulizer Therapy (SNOMED 56251003)."""
        procedures = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        nebulizer = next(
            (p for p in procedures
             if any(coding.code == "56251003" for coding in p.code.coding)),
            None
        )

        assert nebulizer is not None, "Must have nebulizer therapy procedure"
        assert nebulizer.status == "completed", "Nebulizer procedure must be completed"

    # ========================================================================
    # DEVICE - Cardiac Pacemaker
    # ========================================================================

    def test_device_cardiac_pacemaker(self, agastha_bundle):
        """Validate Device: Implantable cardiac pacemaker."""
        devices = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Device"
        ]

        assert len(devices) == 1, "Must have exactly 1 Device"
        device = devices[0]

        # Verify device has patient reference
        assert device.patient is not None, "Device must reference patient"

        # Verify has status
        assert device.status is not None, "Device must have status"
        assert device.status == "active", f"Device status must be 'active', got '{device.status}'"

    # ========================================================================
    # GOALS (2)
    # ========================================================================

    def test_goals_count(self, agastha_bundle):
        """Validate Bundle contains expected number of goals."""
        goals = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Goal"
        ]

        assert len(goals) == 2, "Bundle must contain exactly 2 goals"

    def test_goals_have_lifecycle_status(self, agastha_bundle):
        """Validate Goals have lifecycleStatus."""
        goals = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Goal"
        ]

        for goal in goals:
            assert goal.lifecycleStatus is not None, \
                f"Goal {goal.id} must have lifecycleStatus"
            assert goal.lifecycleStatus == "active", \
                f"Goal {goal.id} lifecycleStatus must be 'active', got '{goal.lifecycleStatus}'"

    def test_goals_have_subject(self, agastha_bundle):
        """Validate Goals reference the patient."""
        goals = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Goal"
        ]

        for goal in goals:
            assert goal.subject is not None, \
                f"Goal {goal.id} must reference patient"

    # ========================================================================
    # OBSERVATIONS (17) - Vital Signs and Labs
    # ========================================================================

    def test_observations_count(self, agastha_bundle):
        """Validate Bundle contains expected number of observations."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) == 17, "Bundle must contain exactly 17 observations"

    def test_observation_vital_signs_panel(self, agastha_bundle):
        """Validate Observation: Vital signs panel (LOINC 85353-1)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        panel = next(
            (obs for obs in observations
             if any(coding.code == "85353-1" for coding in obs.code.coding)),
            None
        )

        assert panel is not None, "Must have vital signs panel"

        # PHASE 1.1: Verify exact category CodeableConcept structure
        assert panel.category is not None, "Vital signs panel must have category"
        assert_observation_category(panel.category[0], "vital-signs")

    def test_observation_height(self, agastha_bundle):
        """Validate Observation: Height (LOINC 8302-2)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        height = next(
            (obs for obs in observations
             if any(coding.code == "8302-2" for coding in obs.code.coding)),
            None
        )

        assert height is not None, "Must have height observation"
        assert height.valueQuantity is not None, "Height must have valueQuantity"
        assert height.valueQuantity.unit is not None, "Height must have unit"

    def test_observation_weight(self, agastha_bundle):
        """Validate Observation: Weight (LOINC 29463-7)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        weight = next(
            (obs for obs in observations
             if any(coding.code == "29463-7" for coding in obs.code.coding)),
            None
        )

        assert weight is not None, "Must have weight observation"
        assert weight.valueQuantity is not None, "Weight must have valueQuantity"

    def test_observation_bmi(self, agastha_bundle):
        """Validate Observation: BMI (LOINC 39156-5)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        bmi = next(
            (obs for obs in observations
             if any(coding.code == "39156-5" for coding in obs.code.coding)),
            None
        )

        assert bmi is not None, "Must have BMI observation"
        assert bmi.valueQuantity is not None, "BMI must have valueQuantity"

    def test_observation_body_temperature(self, agastha_bundle):
        """Validate Observation: Body Temperature (LOINC 8310-5)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        temp = next(
            (obs for obs in observations
             if any(coding.code == "8310-5" for coding in obs.code.coding)),
            None
        )

        assert temp is not None, "Must have body temperature observation"
        assert temp.valueQuantity is not None, "Temperature must have valueQuantity"

    def test_vital_signs_have_category(self, agastha_bundle):
        """Validate vital sign observations have vital-signs category."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # LOINC codes for vital signs
        vital_sign_codes = ["85353-1", "8302-2", "29463-7", "39156-5", "8310-5"]

        for obs in observations:
            # Check if this observation has a vital sign LOINC code
            has_vital_loinc = any(
                coding.code in vital_sign_codes
                for coding in obs.code.coding
            )

            if has_vital_loinc:
                assert obs.category is not None, \
                    f"Vital sign observation {obs.id} must have category"

                has_vital_signs_cat = any(
                    any(coding.code == "vital-signs" for coding in cat.coding)
                    for cat in obs.category
                )
                assert has_vital_signs_cat, \
                    f"Vital sign observation {obs.id} must have vital-signs category"

    def test_observations_have_status(self, agastha_bundle):
        """Validate all Observations have status."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        for obs in observations:
            assert obs.status is not None, \
                f"Observation {obs.id} must have status"

    # ========================================================================
    # DIAGNOSTIC REPORT
    # ========================================================================

    def test_diagnostic_report_present(self, agastha_bundle):
        """Validate Bundle contains DiagnosticReport."""
        reports = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "DiagnosticReport"
        ]

        assert len(reports) == 1, "Bundle must contain exactly 1 DiagnosticReport"
        report = reports[0]

        # Verify has code and status
        assert report.code is not None, "DiagnosticReport must have code"
        assert report.status is not None, "DiagnosticReport must have status"

    # ========================================================================
    # DOCUMENT REFERENCE
    # ========================================================================

    def test_document_reference_present(self, agastha_bundle):
        """Validate Bundle contains DocumentReference."""
        doc_refs = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "DocumentReference"
        ]

        assert len(doc_refs) == 1, "Bundle must contain exactly 1 DocumentReference"
        doc_ref = doc_refs[0]

        # Verify has status and subject
        assert doc_ref.status is not None, "DocumentReference must have status"
        assert doc_ref.subject is not None, "DocumentReference must reference patient"

    # ========================================================================
    # PRACTITIONERS AND ORGANIZATIONS
    # ========================================================================

    def test_practitioners_present(self, agastha_bundle):
        """Validate Bundle contains Practitioners."""
        practitioners = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Practitioner"
        ]

        assert len(practitioners) == 3, "Bundle must contain exactly 3 Practitioners"

        # Verify all have names
        for pract in practitioners:
            assert pract.name is not None and len(pract.name) > 0, \
                f"Practitioner {pract.id} must have name"

    def test_organizations_present(self, agastha_bundle):
        """Validate Bundle contains Organizations."""
        organizations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Organization"
        ]

        assert len(organizations) == 2, "Bundle must contain exactly 2 Organizations"

        # Verify all have names
        for org in organizations:
            assert org.name is not None, \
                f"Organization {org.id} must have name"

    # ========================================================================
    # ENCOUNTER AND LOCATION
    # ========================================================================

    def test_encounter_present(self, agastha_bundle):
        """Validate Bundle contains Encounter."""
        encounters = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) == 1, "Bundle must contain exactly 1 Encounter"
        encounter = encounters[0]

        # Verify has status and class
        assert encounter.status is not None, "Encounter must have status"
        assert encounter.class_fhir is not None, "Encounter must have class"
        assert encounter.subject is not None, "Encounter must reference patient"

    def test_location_present(self, agastha_bundle):
        """Validate Bundle contains Location."""
        locations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Location"
        ]

        assert len(locations) == 1, "Bundle must contain exactly 1 Location"
        location = locations[0]

        # Verify has name or address
        assert location.name is not None or location.address is not None, \
            "Location must have name or address"

    def test_patient_managing_organization(self, agastha_bundle):
        """Validate Patient.managingOrganization reference - CRITICAL.

        This tests the feature added in commit 872785c.
        The Agastha CCD has providerOrganization with NPI 1298765654.
        """
        patient = next(
            (e.resource for e in agastha_bundle.entry
             if e.resource.get_resource_type() == "Patient"),
            None
        )

        assert patient.managingOrganization is not None, \
            "Patient must have managingOrganization"
        assert patient.managingOrganization.reference is not None, \
            "managingOrganization must have reference"
        assert "Organization/" in patient.managingOrganization.reference, \
            f"managingOrganization reference must point to Organization, got '{patient.managingOrganization.reference}'"
        assert patient.managingOrganization.display == "Agastha Medical Center", \
            f"managingOrganization display must be 'Agastha Medical Center', got '{patient.managingOrganization.display}'"

    def test_organization_agastha_medical_center_details(self, agastha_bundle):
        """Validate Agastha Medical Center organization with NPI, address, telecom."""
        orgs = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Organization"
        ]

        # Find Agastha Medical Center by NPI
        agastha = next(
            (o for o in orgs
             if any(i.value == "1298765654" for i in o.identifier if i.value)),
            None
        )

        assert agastha is not None, "Must have Agastha Medical Center organization"
        assert agastha.name == "Agastha Medical Center", \
            f"Organization name must be 'Agastha Medical Center', got '{agastha.name}'"

        # Verify NPI identifier
        npi = next(
            (i for i in agastha.identifier
             if i.system == "http://hl7.org/fhir/sid/us-npi"),
            None
        )
        assert npi is not None, "Organization must have NPI identifier"
        assert npi.value == "1298765654", \
            f"NPI must be '1298765654', got '{npi.value}'"

        # Verify address
        assert len(agastha.address) > 0, "Organization must have address"
        address = agastha.address[0]
        assert address.city == "Charlotte", f"City must be 'Charlotte', got '{address.city}'"
        assert address.state == "NC", f"State must be 'NC', got '{address.state}'"
        assert address.postalCode == "28277", f"Postal code must be '28277', got '{address.postalCode}'"

        # Verify telecom
        assert len(agastha.telecom) > 0, "Organization must have telecom"
        phone = next((t for t in agastha.telecom if t.system == "phone"), None)
        assert phone is not None, "Organization must have phone"
        assert "+1(704)544-6504" in phone.value, \
            f"Phone must contain '+1(704)544-6504', got '{phone.value}'"

    def test_allergy_reaction_manifestation_and_severity(self, agastha_bundle):
        """Validate AllergyIntolerance.reaction with manifestation, severity, description."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        # Penicillin G has reaction details
        penicillin = next(
            (a for a in allergies
             if any(c.code == "7980" for c in a.code.coding)),
            None
        )

        assert penicillin.reaction is not None, "Allergy must have reaction"
        assert len(penicillin.reaction) > 0, "Allergy reaction must not be empty"

        reaction = penicillin.reaction[0]

        # Verify manifestation
        assert reaction.manifestation is not None, "Reaction must have manifestation"
        assert len(reaction.manifestation) > 0, "Manifestation must not be empty"

        manifestation_code = reaction.manifestation[0].coding[0].code
        assert manifestation_code == "247472004", \
            f"Manifestation code must be '247472004' (Hives), got '{manifestation_code}'"

        # Verify severity
        assert reaction.severity == "moderate", \
            f"Reaction severity must be 'moderate', got '{reaction.severity}'"

        # Verify description
        assert reaction.description == "Hives", \
            f"Reaction description must be 'Hives', got '{reaction.description}'"

        # Verify onset
        assert reaction.onset is not None, "Reaction must have onset"

    def test_medication_dosage_route_and_dose(self, agastha_bundle):
        """Validate MedicationStatement.dosage with route, timing, doseQuantity."""
        medications = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        # Tylenol has dosage with oral route
        tylenol = next(
            (m for m in medications
             if any(c.code == "209459" for c in m.medicationCodeableConcept.coding)),
            None
        )

        assert tylenol.dosage is not None, "Medication must have dosage"
        assert len(tylenol.dosage) > 0, "Dosage must not be empty"

        dosage = tylenol.dosage[0]

        # Verify route
        assert dosage.route is not None, "Dosage must have route"
        assert dosage.route.coding is not None, "Route must have coding"

        route_code = dosage.route.coding[0].code
        assert route_code == "C38288", \
            f"Route code must be 'C38288' (ORAL), got '{route_code}'"
        assert dosage.route.coding[0].display == "ORAL", \
            f"Route display must be 'ORAL', got '{dosage.route.coding[0].display}'"

        # Verify doseAndRate
        assert dosage.doseAndRate is not None, "Dosage must have doseAndRate"
        assert len(dosage.doseAndRate) > 0, "doseAndRate must not be empty"

        dose_qty = dosage.doseAndRate[0].doseQuantity
        assert dose_qty is not None, "doseAndRate must have doseQuantity"
        assert dose_qty.value == 1, \
            f"Dose value must be 1, got '{dose_qty.value}'"

        # Verify timing
        assert dosage.timing is not None, "Dosage must have timing"
        assert dosage.timing.repeat is not None, "Timing must have repeat"
        assert dosage.timing.repeat.period == 1, \
            f"Period must be 1, got '{dosage.timing.repeat.period}'"
        assert dosage.timing.repeat.periodUnit == "d", \
            f"Period unit must be 'd' (day), got '{dosage.timing.repeat.periodUnit}'"

    def test_observation_interpretation_normal(self, agastha_bundle):
        """Validate Observation.interpretation for vital signs with 'N' (Normal)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Height observation has interpretation "N" (Normal)
        height = next(
            (obs for obs in observations
             if any(c.code == "8302-2" for c in obs.code.coding)),
            None
        )

        assert height.interpretation is not None, \
            "Vital sign observation must have interpretation"
        assert len(height.interpretation) > 0, \
            "Interpretation must not be empty"

        interp_code = height.interpretation[0].coding[0].code
        assert interp_code == "N", \
            f"Interpretation code must be 'N' (Normal), got '{interp_code}'"

        interp_display = height.interpretation[0].coding[0].display
        if interp_display:
            assert interp_display == "Normal", \
                f"Interpretation display must be 'Normal', got '{interp_display}'"

        interp_system = height.interpretation[0].coding[0].system
        assert "ObservationInterpretation" in interp_system, \
            f"Interpretation system must be ObservationInterpretation, got '{interp_system}'"

    def test_observation_reference_range_lab_results(self, agastha_bundle):
        """Validate Observation.referenceRange for lab results (Specific Gravity)."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find Specific Gravity observation (LOINC 5811-5)
        specific_gravity = next(
            (obs for obs in observations
             if any(c.code == "5811-5" for c in obs.code.coding)),
            None
        )

        if specific_gravity is None:
            # Specific Gravity might not be in this document, skip test
            import pytest
            pytest.skip("Specific Gravity observation not found in this document")

        assert specific_gravity.referenceRange is not None, \
            "Lab observation must have referenceRange"
        assert len(specific_gravity.referenceRange) > 0, \
            "referenceRange must not be empty"

        ref_range = specific_gravity.referenceRange[0]

        assert ref_range.low is not None, "Reference range must have low value"
        assert ref_range.low.value == 1.005, \
            f"Reference range low must be 1.005, got '{ref_range.low.value}'"

        assert ref_range.high is not None, "Reference range must have high value"
        assert ref_range.high.value == 1.03, \
            f"Reference range high must be 1.03, got '{ref_range.high.value}'"

    def test_encounter_diagnosis_references(self, agastha_bundle):
        """Validate Encounter.diagnosis references conditions."""
        encounters = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) == 1, "Must have exactly 1 Encounter"
        encounter = encounters[0]

        assert encounter.diagnosis is not None, \
            "Encounter must have diagnosis"
        assert len(encounter.diagnosis) > 0, \
            "Encounter diagnosis must not be empty"

        # Verify each diagnosis has a condition reference
        for diag in encounter.diagnosis:
            assert diag.condition is not None, \
                "Encounter diagnosis must have condition reference"
            assert diag.condition.reference is not None, \
                "Diagnosis condition reference must not be null"
            assert "Condition/" in diag.condition.reference, \
                f"Diagnosis must reference Condition, got '{diag.condition.reference}'"

            # Verify use (role) - Agastha is outpatient, should be "billing"
            assert diag.use is not None, "Diagnosis must have use/role"
            assert len(diag.use.coding) > 0, "Diagnosis use must have coding"
            assert diag.use.coding[0].code == "billing", \
                f"Diagnosis use code must be 'billing' for outpatient, got '{diag.use.coding[0].code}'"
            assert diag.use.coding[0].display == "Billing", \
                f"Diagnosis use display must be 'Billing', got '{diag.use.coding[0].display}'"
            assert "diagnosis-role" in diag.use.coding[0].system, \
                f"Diagnosis use system must be diagnosis-role CodeSystem, got '{diag.use.coding[0].system}'"

    def test_encounter_participant_practitioners(self, agastha_bundle):
        """Validate Encounter.participant references practitioners."""
        encounters = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Encounter"
        ]

        assert len(encounters) == 1
        encounter = encounters[0]

        if encounter.participant is None or len(encounter.participant) == 0:
            # Some encounters may not have participants
            import pytest
            pytest.skip("Encounter does not have participants in this document")

        # Verify each participant has an individual reference
        for participant in encounter.participant:
            assert participant.individual is not None, \
                "Encounter participant must have individual reference"
            assert participant.individual.reference is not None, \
                "Participant individual reference must not be null"

            # Should reference Practitioner or RelatedPerson
            ref = participant.individual.reference
            assert "Practitioner/" in ref or "RelatedPerson/" in ref, \
                f"Participant must reference Practitioner or RelatedPerson, got '{ref}'"

    # =========================================================================
    # PHASE 2: High-Priority Validations (Observation Details & US Core)
    # =========================================================================

    def test_observation_interpretation_exact(self, agastha_bundle):
        """PHASE 2.1: Validate Observation.interpretation with exact CodeableConcept structure."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find observations with interpretation
        obs_with_interp = [
            obs for obs in observations
            if hasattr(obs, 'interpretation') and obs.interpretation is not None and len(obs.interpretation) > 0
        ]

        assert len(obs_with_interp) > 0, "Must have observations with interpretation"

        for obs in obs_with_interp:
            interp = obs.interpretation[0]

            # Validate coding structure
            assert hasattr(interp, 'coding') and interp.coding is not None, \
                "Interpretation must have coding"
            assert len(interp.coding) > 0, \
                "Interpretation coding must not be empty"

            coding = interp.coding[0]

            # Exact system validation
            assert coding.system == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", \
                f"Interpretation system must be exact ObservationInterpretation URL, got '{coding.system}'"

            # Valid interpretation codes
            valid_codes = ["N", "L", "H", "LL", "HH", "A", "AA", "<", ">", "NEG", "POS"]
            assert coding.code in valid_codes, \
                f"Interpretation code must be valid, got '{coding.code}'"

            # Display text should be present (from terminology.py)
            if coding.code == "N":
                assert coding.display == "Normal", \
                    f"Interpretation display for 'N' must be 'Normal', got '{coding.display}'"

    def test_observation_reference_range_ucum_exact(self, agastha_bundle):
        """PHASE 2.2: Validate Observation.referenceRange has exact UCUM Quantity structure."""
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find observations with reference ranges
        obs_with_ref_range = [
            obs for obs in observations
            if hasattr(obs, 'referenceRange') and obs.referenceRange is not None and len(obs.referenceRange) > 0
        ]

        if len(obs_with_ref_range) == 0:
            import pytest
            pytest.skip("No observations with reference ranges in this document")

        for obs in obs_with_ref_range:
            for ref_range in obs.referenceRange:
                # Validate low Quantity structure (if present)
                if hasattr(ref_range, 'low') and ref_range.low is not None:
                    low = ref_range.low
                    assert hasattr(low, 'value') and low.value is not None, \
                        "Reference range low must have value"

                    # UCUM system validation using helper
                    assert_quantity_has_ucum(low, field_name="referenceRange.low", strict_system=True)

                # Validate high Quantity structure (if present)
                if hasattr(ref_range, 'high') and ref_range.high is not None:
                    high = ref_range.high
                    assert hasattr(high, 'value') and high.value is not None, \
                        "Reference range high must have value"

                    # UCUM system validation using helper
                    assert_quantity_has_ucum(high, field_name="referenceRange.high", strict_system=True)

    def test_allergy_verification_status_exact(self, agastha_bundle):
        """PHASE 2.4: Validate AllergyIntolerance.verificationStatus exact CodeableConcept."""
        allergies = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "AllergyIntolerance"
        ]

        assert len(allergies) > 0, "Must have AllergyIntolerance resources"

        # Find allergies with verificationStatus
        allergies_with_vs = [
            a for a in allergies
            if hasattr(a, 'verificationStatus') and a.verificationStatus is not None
        ]

        if len(allergies_with_vs) == 0:
            import pytest
            pytest.skip("No allergies with verificationStatus in this document")

        for allergy in allergies_with_vs:
            vs = allergy.verificationStatus

            # Validate coding structure
            assert hasattr(vs, 'coding') and vs.coding is not None, \
                "VerificationStatus must have coding"
            assert len(vs.coding) > 0, \
                "VerificationStatus coding must not be empty"

            coding = vs.coding[0]

            # Exact system validation
            assert coding.system == "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", \
                f"VerificationStatus system must be exact, got '{coding.system}'"

            # Valid codes
            valid_codes = ["confirmed", "unconfirmed", "refuted", "entered-in-error", "presumed"]
            assert coding.code in valid_codes, \
                f"VerificationStatus code must be valid, got '{coding.code}'"

            # Display should be present
            if coding.display is not None:
                display_map = {
                    "confirmed": "Confirmed",
                    "unconfirmed": "Unconfirmed",
                    "refuted": "Refuted",
                    "entered-in-error": "Entered in Error",
                    "presumed": "Presumed"
                }
                expected_display = display_map.get(coding.code)
                if expected_display:
                    assert coding.display == expected_display, \
                        f"VerificationStatus display for '{coding.code}' must be '{expected_display}', got '{coding.display}'"

    def test_condition_verification_status_exact(self, agastha_bundle):
        """PHASE 2.4: Validate Condition.verificationStatus exact CodeableConcept."""
        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have Condition resources"

        # Find conditions with verificationStatus
        conditions_with_vs = [
            c for c in conditions
            if hasattr(c, 'verificationStatus') and c.verificationStatus is not None
        ]

        if len(conditions_with_vs) == 0:
            import pytest
            pytest.skip("No conditions with verificationStatus in this document")

        for condition in conditions_with_vs:
            vs = condition.verificationStatus

            # Validate coding structure
            assert hasattr(vs, 'coding') and vs.coding is not None, \
                "VerificationStatus must have coding"
            assert len(vs.coding) > 0, \
                "VerificationStatus coding must not be empty"

            coding = vs.coding[0]

            # Exact system validation
            assert coding.system == "http://terminology.hl7.org/CodeSystem/condition-ver-status", \
                f"VerificationStatus system must be exact, got '{coding.system}'"

            # Valid codes
            valid_codes = ["unconfirmed", "provisional", "differential", "confirmed", "refuted", "entered-in-error"]
            assert coding.code in valid_codes, \
                f"VerificationStatus code must be valid, got '{coding.code}'"

            # Display should be present
            if coding.display is not None:
                display_map = {
                    "confirmed": "Confirmed",
                    "unconfirmed": "Unconfirmed",
                    "provisional": "Provisional",
                    "differential": "Differential",
                    "refuted": "Refuted",
                    "entered-in-error": "Entered in Error"
                }
                expected_display = display_map.get(coding.code)
                if expected_display:
                    assert coding.display == expected_display, \
                        f"VerificationStatus display for '{coding.code}' must be '{expected_display}', got '{coding.display}'"

    def test_patient_race_extension_exact_structure(self, agastha_bundle):
        """PHASE 2.3: Validate US Core race extension has exact structure."""
        patients = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Patient"
        ]

        assert len(patients) == 1, "Must have exactly 1 Patient"
        patient = patients[0]

        # Find race extension
        race_ext = None
        if hasattr(patient, 'extension') and patient.extension is not None:
            race_ext = next(
                (e for e in patient.extension
                 if e.url == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"),
                None
            )

        if race_ext is None:
            import pytest
            pytest.skip("Patient does not have us-core-race extension")

        # Validate extension has sub-extensions
        assert hasattr(race_ext, 'extension') and race_ext.extension is not None, \
            "Race extension must have nested extensions"
        assert len(race_ext.extension) > 0, \
            "Race extension must have at least one sub-extension"

        # Find ombCategory sub-extensions
        omb_exts = [e for e in race_ext.extension if e.url == "ombCategory"]

        if len(omb_exts) > 0:
            for omb in omb_exts:
                # Validate valueCoding structure
                assert hasattr(omb, 'valueCoding') and omb.valueCoding is not None, \
                    "ombCategory extension must have valueCoding"

                # Exact system validation
                assert omb.valueCoding.system == "urn:oid:2.16.840.1.113883.6.238", \
                    f"ombCategory system must be exact OMB race code system, got '{omb.valueCoding.system}'"

                # Valid OMB race codes
                valid_omb_codes = [
                    "1002-5",  # American Indian or Alaska Native
                    "2028-9",  # Asian
                    "2054-5",  # Black or African American
                    "2076-8",  # Native Hawaiian or Other Pacific Islander
                    "2106-3",  # White
                ]
                assert omb.valueCoding.code in valid_omb_codes, \
                    f"ombCategory code must be valid OMB code, got '{omb.valueCoding.code}'"

                # Display should be present
                assert hasattr(omb.valueCoding, 'display') and omb.valueCoding.display is not None, \
                    "ombCategory coding must have display text"

        # Text sub-extension is REQUIRED per US Core
        text_ext = next((e for e in race_ext.extension if e.url == "text"), None)
        assert text_ext is not None, \
            "Race extension must have 'text' sub-extension (US Core required)"
        assert hasattr(text_ext, 'valueString') and text_ext.valueString is not None, \
            "Race text extension must have valueString"

    def test_patient_ethnicity_extension_exact_structure(self, agastha_bundle):
        """PHASE 2.3: Validate US Core ethnicity extension has exact structure."""
        patients = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Patient"
        ]

        assert len(patients) == 1, "Must have exactly 1 Patient"
        patient = patients[0]

        # Find ethnicity extension
        ethnicity_ext = None
        if hasattr(patient, 'extension') and patient.extension is not None:
            ethnicity_ext = next(
                (e for e in patient.extension
                 if e.url == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity"),
                None
            )

        if ethnicity_ext is None:
            import pytest
            pytest.skip("Patient does not have us-core-ethnicity extension")

        # Validate extension has sub-extensions
        assert hasattr(ethnicity_ext, 'extension') and ethnicity_ext.extension is not None, \
            "Ethnicity extension must have nested extensions"
        assert len(ethnicity_ext.extension) > 0, \
            "Ethnicity extension must have at least one sub-extension"

        # Find ombCategory sub-extension
        omb_exts = [e for e in ethnicity_ext.extension if e.url == "ombCategory"]

        if len(omb_exts) > 0:
            for omb in omb_exts:
                # Validate valueCoding structure
                assert hasattr(omb, 'valueCoding') and omb.valueCoding is not None, \
                    "ombCategory extension must have valueCoding"

                # Exact system validation
                assert omb.valueCoding.system == "urn:oid:2.16.840.1.113883.6.238", \
                    f"ombCategory system must be exact OMB ethnicity code system, got '{omb.valueCoding.system}'"

                # Valid OMB ethnicity codes
                valid_omb_codes = [
                    "2135-2",  # Hispanic or Latino
                    "2186-5",  # Not Hispanic or Latino
                ]
                assert omb.valueCoding.code in valid_omb_codes, \
                    f"ombCategory code must be valid OMB ethnicity code, got '{omb.valueCoding.code}'"

                # Display should be present
                assert hasattr(omb.valueCoding, 'display') and omb.valueCoding.display is not None, \
                    "ombCategory coding must have display text"

        # Text sub-extension is REQUIRED per US Core
        text_ext = next((e for e in ethnicity_ext.extension if e.url == "text"), None)
        assert text_ext is not None, \
            "Ethnicity extension must have 'text' sub-extension (US Core required)"
        assert hasattr(text_ext, 'valueString') and text_ext.valueString is not None, \
            "Ethnicity text extension must have valueString"

    # ========================================================================
    # PHASE 3: TEMPORAL FIELD TIMEZONE VALIDATION & US CORE PROFILE COMPLIANCE
    # ========================================================================

    def test_observation_datetime_timezone_exact(self, agastha_bundle):
        """PHASE 3.1: Validate Observation.effectiveDateTime and .issued have timezone when time present.

        Per FHIR R4 spec: "If hours and minutes are specified, a time zone SHALL be populated"
        """
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        assert len(observations) > 0, "Must have observations"

        # Check effectiveDateTime timezone
        obs_with_effective_dt = [
            obs for obs in observations
            if hasattr(obs, 'effectiveDateTime') and obs.effectiveDateTime is not None
        ]

        if len(obs_with_effective_dt) > 0:
            for obs in obs_with_effective_dt:
                # effectiveDateTime can be just date or datetime with timezone
                assert_datetime_format(obs.effectiveDateTime, field_name="Observation.effectiveDateTime")

                # If it has time component, must have timezone
                if "T" in obs.effectiveDateTime:
                    assert "+" in obs.effectiveDateTime or "-" in obs.effectiveDateTime[-6:], \
                        f"Observation.effectiveDateTime with time must have timezone: {obs.effectiveDateTime}"

        # Check issued (instant field - always requires timezone)
        obs_with_issued = [
            obs for obs in observations
            if hasattr(obs, 'issued') and obs.issued is not None
        ]

        if len(obs_with_issued) > 0:
            from tests.integration.helpers.temporal_validators import assert_instant_format
            for obs in obs_with_issued:
                # issued is instant type - must always have full timestamp + timezone
                assert_instant_format(obs.issued, field_name="Observation.issued")

    def test_condition_datetime_timezone_exact(self, agastha_bundle):
        """PHASE 3.2: Validate Condition.onsetDateTime has timezone when time present."""

        conditions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Condition"
        ]

        assert len(conditions) > 0, "Must have conditions"

        # Check onsetDateTime
        conditions_with_onset_dt = [
            c for c in conditions
            if hasattr(c, 'onsetDateTime') and c.onsetDateTime is not None
        ]

        if len(conditions_with_onset_dt) > 0:
            for condition in conditions_with_onset_dt:
                # FHIR library may parse to datetime object - convert to string for validation
                onset_str = condition.onsetDateTime if isinstance(condition.onsetDateTime, str) else condition.onsetDateTime.isoformat()
                assert_datetime_format(onset_str, field_name="Condition.onsetDateTime")

                # If it has time component, must have timezone
                if "T" in onset_str:
                    assert "+" in onset_str or "-" in onset_str[-6:], \
                        f"Condition.onsetDateTime with time must have timezone: {onset_str}"

        # Check abatementDateTime
        conditions_with_abatement_dt = [
            c for c in conditions
            if hasattr(c, 'abatementDateTime') and c.abatementDateTime is not None
        ]

        if len(conditions_with_abatement_dt) > 0:
            for condition in conditions_with_abatement_dt:
                # FHIR library may parse to datetime object - convert to string for validation
                abatement_str = condition.abatementDateTime if isinstance(condition.abatementDateTime, str) else condition.abatementDateTime.isoformat()
                assert_datetime_format(abatement_str, field_name="Condition.abatementDateTime")

                # If it has time component, must have timezone
                if "T" in abatement_str:
                    assert "+" in abatement_str or "-" in abatement_str[-6:], \
                        f"Condition.abatementDateTime with time must have timezone: {abatement_str}"

    def test_medication_datetime_timezone_exact(self, agastha_bundle):
        """PHASE 3.3: Validate MedicationStatement temporal fields have timezone when time present."""
        med_statements = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "MedicationStatement"
        ]

        if len(med_statements) == 0:
            import pytest
            pytest.skip("No MedicationStatement resources in document")

        # Check effectiveDateTime
        meds_with_effective_dt = [
            m for m in med_statements
            if hasattr(m, 'effectiveDateTime') and m.effectiveDateTime is not None
        ]

        if len(meds_with_effective_dt) > 0:
            for med in meds_with_effective_dt:
                assert_datetime_format(med.effectiveDateTime, field_name="MedicationStatement.effectiveDateTime")

                # If it has time component, must have timezone
                if "T" in med.effectiveDateTime:
                    assert "+" in med.effectiveDateTime or "-" in med.effectiveDateTime[-6:], \
                        f"MedicationStatement.effectiveDateTime with time must have timezone: {med.effectiveDateTime}"

        # Check effectivePeriod
        meds_with_effective_period = [
            m for m in med_statements
            if hasattr(m, 'effectivePeriod') and m.effectivePeriod is not None
        ]

        if len(meds_with_effective_period) > 0:
            from tests.integration.helpers.temporal_validators import assert_period_format
            for med in meds_with_effective_period:
                assert_period_format(med.effectivePeriod, field_name="MedicationStatement.effectivePeriod")

    def test_procedure_datetime_timezone_exact(self, agastha_bundle):
        """PHASE 3.4: Validate Procedure.performedDateTime/Period have timezone when time present."""
        procedures = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Procedure"
        ]

        if len(procedures) == 0:
            import pytest
            pytest.skip("No Procedure resources in document")

        # Check performedDateTime
        procs_with_performed_dt = [
            p for p in procedures
            if hasattr(p, 'performedDateTime') and p.performedDateTime is not None
        ]

        if len(procs_with_performed_dt) > 0:
            for proc in procs_with_performed_dt:
                assert_datetime_format(proc.performedDateTime, field_name="Procedure.performedDateTime")

                # If it has time component, must have timezone
                if "T" in proc.performedDateTime:
                    assert "+" in proc.performedDateTime or "-" in proc.performedDateTime[-6:], \
                        f"Procedure.performedDateTime with time must have timezone: {proc.performedDateTime}"

        # Check performedPeriod
        procs_with_performed_period = [
            p for p in procedures
            if hasattr(p, 'performedPeriod') and p.performedPeriod is not None
        ]

        if len(procs_with_performed_period) > 0:
            from tests.integration.helpers.temporal_validators import assert_period_format
            for proc in procs_with_performed_period:
                assert_period_format(proc.performedPeriod, field_name="Procedure.performedPeriod")

    def test_composition_instant_timezone_exact(self, agastha_bundle):
        """PHASE 3.5: Validate Composition.date (instant) always has timezone."""

        compositions = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Composition"
        ]

        assert len(compositions) == 1, "Must have exactly 1 Composition"
        composition = compositions[0]

        # Composition.date is instant type - must always have full timestamp + timezone
        assert hasattr(composition, 'date') and composition.date is not None, \
            "Composition.date is required"

        # FHIR library may parse to datetime object - convert to string for validation
        date_str = composition.date if isinstance(composition.date, str) else composition.date.isoformat()

        from tests.integration.helpers.temporal_validators import assert_instant_format
        assert_instant_format(date_str, field_name="Composition.date")

    def test_observation_component_structure(self, agastha_bundle):
        """PHASE 3.6: Validate Observation.component structure for multi-component observations.

        Examples: Blood pressure (systolic + diastolic), Panel observations
        """
        observations = [
            e.resource for e in agastha_bundle.entry
            if e.resource.get_resource_type() == "Observation"
        ]

        # Find observations with components
        obs_with_components = [
            obs for obs in observations
            if hasattr(obs, 'component') and obs.component is not None and len(obs.component) > 0
        ]

        if len(obs_with_components) == 0:
            import pytest
            pytest.skip("No observations with components in document")

        for obs in obs_with_components:
            assert len(obs.component) > 0, \
                "Observation.component must not be empty if present"

            for i, component in enumerate(obs.component):
                # Each component must have code
                assert hasattr(component, 'code') and component.code is not None, \
                    f"Observation.component[{i}].code is required"

                # Component code must have coding
                assert hasattr(component.code, 'coding') and component.code.coding is not None, \
                    f"Observation.component[{i}].code must have coding"
                assert len(component.code.coding) > 0, \
                    f"Observation.component[{i}].code.coding must not be empty"

                coding = component.code.coding[0]

                # Validate coding structure
                assert hasattr(coding, 'system') and coding.system is not None, \
                    f"Observation.component[{i}].code.coding[0].system is required"
                assert hasattr(coding, 'code') and coding.code is not None, \
                    f"Observation.component[{i}].code.coding[0].code is required"

                # Component must have a value (one of: valueQuantity, valueCodeableConcept, etc.)
                has_value = any([
                    hasattr(component, 'valueQuantity') and component.valueQuantity is not None,
                    hasattr(component, 'valueCodeableConcept') and component.valueCodeableConcept is not None,
                    hasattr(component, 'valueString') and component.valueString is not None,
                    hasattr(component, 'valueBoolean') and component.valueBoolean is not None,
                    hasattr(component, 'valueInteger') and component.valueInteger is not None,
                    hasattr(component, 'valueRange') and component.valueRange is not None,
                    hasattr(component, 'valueRatio') and component.valueRatio is not None,
                    hasattr(component, 'valueSampledData') and component.valueSampledData is not None,
                    hasattr(component, 'valueTime') and component.valueTime is not None,
                    hasattr(component, 'valueDateTime') and component.valueDateTime is not None,
                    hasattr(component, 'valuePeriod') and component.valuePeriod is not None,
                ])

                assert has_value, \
                    f"Observation.component[{i}] must have a value[x] element"

                # If valueQuantity, validate UCUM
                if hasattr(component, 'valueQuantity') and component.valueQuantity is not None:
                    quantity = component.valueQuantity
                    assert hasattr(quantity, 'value') and quantity.value is not None, \
                        f"Observation.component[{i}].valueQuantity.value is required"

                    # Should have UCUM system
                    if hasattr(quantity, 'unit') and quantity.unit is not None:
                        assert hasattr(quantity, 'system') and quantity.system is not None, \
                            f"Observation.component[{i}].valueQuantity.system should be present when unit is present"
                        assert quantity.system == "http://unitsofmeasure.org", \
                            f"Observation.component[{i}].valueQuantity.system should be UCUM"
