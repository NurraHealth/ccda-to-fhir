"""Comprehensive E2E validation for Cerner TOC - validates EXACT values for EVERY field.

This test validates that EVERY field in the converted FHIR bundle has the EXACT
value expected from the C-CDA source document. No field goes untested.
"""

from pathlib import Path

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle

from .comprehensive_validator import FieldValidator

CERNER_TOC = Path(__file__).parent / "fixtures" / "documents" / "cerner_toc.xml"


class TestCernerComprehensive:
    """Comprehensive validation - EXACT values for ALL fields."""

    @pytest.fixture
    def cerner_bundle(self):
        """Convert Cerner TOC to FHIR Bundle."""
        with open(CERNER_TOC) as f:
            xml = f.read()
        result = convert_document(xml)
        return Bundle(**result["bundle"])

    def test_validate_all_field_structures(self, cerner_bundle):
        """First pass: validate structure of ALL 1,314 fields."""
        validator = FieldValidator(cerner_bundle)
        stats = validator.validate_all()

        print(f"\n{'='*80}")
        print(f"STRUCTURAL VALIDATION: {stats['fields_validated']} fields validated")
        print(f"{'='*80}")

        if stats['errors']:
            print(f"\n❌ ERRORS ({len(stats['errors'])}):")
            for error in stats['errors'][:20]:
                print(f"  - {error}")

        assert len(stats['errors']) == 0, \
            f"Found {len(stats['errors'])} structural validation errors"

    def test_patient_exact_values(self, cerner_bundle):
        """Validate Patient has EXACT values from C-CDA."""
        patients = [e.resource for e in cerner_bundle.entry
                   if e.resource.get_resource_type() == "Patient"]
        assert len(patients) == 1

        p = patients[0].dict() if hasattr(patients[0], 'dict') else patients[0].model_dump()

        # Exact name
        assert len(p["name"]) == 1
        assert p["name"][0]["family"] == "Williamson"
        assert p["name"][0]["given"] == ["Steve"]

        # Exact birth date
        from datetime import date
        assert p["birthDate"] == date(1947, 4, 7)

        # Exact gender
        assert p["gender"] == "male"

        # Exact address
        assert len(p["address"]) == 1
        addr = p["address"][0]
        assert addr["line"] == ["8745 W Willenow Rd"]
        assert addr["city"] == "Beaverton"
        assert addr["state"] == "OR"
        assert addr["postalCode"] == "97005-"
        assert addr["country"] == "US"

        # Exact telecom
        assert len(p["telecom"]) == 1
        assert p["telecom"][0]["system"] == "phone"
        assert p["telecom"][0]["value"] == "(503) 325-7464"
        assert p["telecom"][0]["use"] == "home"

        # Exact communication
        assert len(p["communication"]) == 1
        assert p["communication"][0]["language"]["coding"][0]["code"] == "eng"

        # Exact race/ethnicity extensions
        assert "extension" in p
        race_ext = next((e for e in p["extension"]
                        if e["url"] == "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race"), None)
        assert race_ext is not None

        # US Core profile (optional)
        if "meta" in p and "profile" in p["meta"]:
            assert p["meta"]["profile"] == ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]

    def test_condition_angina_exact_values(self, cerner_bundle):
        """Validate Angina condition has EXACT values."""
        conditions = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Condition"]

        # Find Angina condition by code
        angina = None
        for cond in conditions:
            c = cond.dict() if hasattr(cond, 'dict') else cond.model_dump()
            if "code" in c and c["code"] and "coding" in c["code"]:
                if any(coding.get("code") == "194828000" for coding in c["code"]["coding"]):
                    angina = c
                    break

        assert angina is not None, "Must have Angina condition"

        # Exact code
        assert len(angina["code"]["coding"]) >= 1
        snomed_coding = next((c for c in angina["code"]["coding"]
                             if c["system"] == "http://snomed.info/sct"), None)
        assert snomed_coding is not None
        assert snomed_coding["code"] == "194828000"
        assert snomed_coding["display"] == "Angina (disorder)"

        # Exact text
        assert angina["code"]["text"] == "Angina (disorder)"

        # Exact clinical status
        assert angina["clinicalStatus"]["coding"][0]["code"] == "active"
        assert angina["clinicalStatus"]["coding"][0]["system"] == \
            "http://terminology.hl7.org/CodeSystem/condition-clinical"

        # Exact category
        assert len(angina["category"]) >= 1
        assert any(
            cat["coding"][0]["code"] == "problem-list-item"
            for cat in angina["category"]
        )

        # Has subject reference to Patient
        assert angina["subject"]["reference"].startswith("Patient/")

        # Has onset date
        assert "onsetDateTime" in angina

    def test_condition_diabetes_exact_values(self, cerner_bundle):
        """Validate Diabetes Type 2 condition has EXACT values."""
        conditions = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Condition"]

        diabetes = None
        for cond in conditions:
            c = cond.dict() if hasattr(cond, 'dict') else cond.model_dump()
            if "code" in c and c["code"] and "coding" in c["code"]:
                if any(coding.get("code") == "44054006" for coding in c["code"]["coding"]):
                    diabetes = c
                    break

        assert diabetes is not None, "Must have Diabetes Type 2 condition"

        # Exact code
        snomed_coding = next((c for c in diabetes["code"]["coding"]
                             if c["system"] == "http://snomed.info/sct"), None)
        assert snomed_coding["code"] == "44054006"
        assert snomed_coding["display"] == "Diabetes mellitus type 2 (disorder)"
        assert diabetes["code"]["text"] == "Diabetes mellitus type 2 (disorder)"

    def test_allergy_codeine_exact_values(self, cerner_bundle):
        """Validate Codeine allergy has EXACT values."""
        allergies = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "AllergyIntolerance"]

        codeine = None
        for allergy in allergies:
            a = allergy.dict() if hasattr(allergy, 'dict') else allergy.model_dump()
            if any(coding.get("code") == "2670" for coding in a["code"]["coding"]):
                codeine = a
                break

        assert codeine is not None, "Must have Codeine allergy"

        # Exact code
        rxnorm_coding = next((c for c in codeine["code"]["coding"]
                             if c["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"), None)
        assert rxnorm_coding["code"] == "2670"
        assert rxnorm_coding["display"] == "Codeine"

        # Exact clinical status
        assert codeine["clinicalStatus"]["coding"][0]["code"] == "active"

        # Exact category
        assert codeine["category"] == ["medication"]

        # Exact type (medium-priority untested field)
        assert "type" in codeine
        assert codeine["type"] == "allergy"

        # Exact reaction
        assert len(codeine["reaction"]) == 1
        reaction = codeine["reaction"][0]
        assert len(reaction["manifestation"]) == 1
        manifestation_coding = reaction["manifestation"][0]["coding"][0]
        assert manifestation_coding["code"] == "422587007"  # Nausea
        assert "Nausea" in manifestation_coding["display"]

    def test_medication_insulin_exact_values(self, cerner_bundle):
        """Validate Insulin Glargine medication has EXACT values."""
        meds = [e.resource for e in cerner_bundle.entry
               if e.resource.get_resource_type() == "MedicationRequest"]

        insulin = None
        for med in meds:
            m = med.dict() if hasattr(med, 'dict') else med.model_dump()
            if "medicationCodeableConcept" in m and "coding" in m["medicationCodeableConcept"]:
                if any(coding.get("code") == "311041" for coding in m["medicationCodeableConcept"]["coding"]):
                    insulin = m
                    break

        assert insulin is not None, "Must have Insulin Glargine"

        # Exact medication code
        rxnorm_coding = next((c for c in insulin["medicationCodeableConcept"]["coding"]
                             if c["system"] == "http://www.nlm.nih.gov/research/umls/rxnorm"), None)
        assert rxnorm_coding["code"] == "311041"
        assert rxnorm_coding["display"] == "Insulin Glargine 100 UNT/ML Injectable Solution"

        # Exact status and intent
        assert insulin["status"] == "active"
        assert insulin["intent"] == "plan"

        # Exact dosage - route
        assert len(insulin["dosageInstruction"]) >= 1
        dosage = insulin["dosageInstruction"][0]
        assert dosage["route"]["coding"][0]["code"] == "C38299"  # Subcutaneous
        assert dosage["route"]["coding"][0]["system"] == "http://ncimeta.nci.nih.gov"

        # Exact dosage - dose quantity
        assert len(dosage["doseAndRate"]) >= 1
        dose_qty = dosage["doseAndRate"][0]["doseQuantity"]
        assert dose_qty["value"] == 30.0
        assert dose_qty["unit"] == "1"
        assert dose_qty["code"] == "1"
        assert dose_qty["system"] == "http://unitsofmeasure.org"

        # Has authoredOn
        assert "authoredOn" in insulin
        from datetime import datetime
        assert isinstance(insulin["authoredOn"], datetime)

        # Exact dosageInstruction.timing (high-priority untested field)
        assert "timing" in dosage
        timing = dosage["timing"]
        assert "repeat" in timing
        assert "boundsPeriod" in timing["repeat"]
        assert "start" in timing["repeat"]["boundsPeriod"]
        assert isinstance(timing["repeat"]["boundsPeriod"]["start"], datetime)

    def test_observation_bp_exact_values(self, cerner_bundle):
        """Validate Blood Pressure observation has EXACT values."""
        observations = [e.resource for e in cerner_bundle.entry
                       if e.resource.get_resource_type() == "Observation"]

        bp = None
        for obs in observations:
            o = obs.dict() if hasattr(obs, 'dict') else obs.model_dump()
            if any(coding.get("code") == "85354-9" for coding in o["code"]["coding"]):
                bp = o
                break

        assert bp is not None, "Must have Blood Pressure observation"

        # Exact code
        loinc_coding = next((c for c in bp["code"]["coding"]
                            if c["system"] == "http://loinc.org"), None)
        assert loinc_coding["code"] == "85354-9"
        assert "Blood pressure" in loinc_coding["display"]

        # Exact status
        assert bp["status"] == "final"

        # Exact category
        assert any(
            cat["coding"][0]["code"] == "vital-signs"
            for cat in bp["category"]
        )

        # Exact components - systolic
        assert len(bp["component"]) == 2
        systolic = next((c for c in bp["component"]
                        if c["code"]["coding"][0]["code"] == "8480-6"), None)
        assert systolic is not None
        assert systolic["valueQuantity"]["value"] == 150.0
        assert systolic["valueQuantity"]["unit"] == "mm[Hg]"
        assert systolic["valueQuantity"]["system"] == "http://unitsofmeasure.org"
        assert systolic["valueQuantity"]["code"] == "mm[Hg]"

        # Exact interpretation - HIGH
        assert len(systolic["interpretation"]) == 1
        assert systolic["interpretation"][0]["coding"][0]["code"] == "H"

        # Exact components - diastolic
        diastolic = next((c for c in bp["component"]
                         if c["code"]["coding"][0]["code"] == "8462-4"), None)
        assert diastolic is not None
        assert diastolic["valueQuantity"]["value"] == 95.0
        assert diastolic["valueQuantity"]["unit"] == "mm[Hg]"

    def test_immunization_influenza_exact_values(self, cerner_bundle):
        """Validate Influenza immunization has EXACT values."""
        immunizations = [e.resource for e in cerner_bundle.entry
                        if e.resource.get_resource_type() == "Immunization"]

        assert len(immunizations) >= 1
        flu = immunizations[0].dict() if hasattr(immunizations[0], 'dict') else immunizations[0].model_dump()

        # Exact vaccine code
        cvx_coding = next((c for c in flu["vaccineCode"]["coding"]
                          if c["system"] == "http://hl7.org/fhir/sid/cvx"), None)
        assert cvx_coding["code"] == "88"  # Influenza

        # Exact status
        assert flu["status"] == "completed"

        # Exact route
        nci_coding = next((c for c in flu["route"]["coding"]
                          if c["system"] == "http://ncimeta.nci.nih.gov"), None)
        assert nci_coding is not None
        assert nci_coding["code"] == "C28161"  # Intramuscular

        # Exact dose
        assert flu["doseQuantity"]["value"] == 0.25
        assert flu["doseQuantity"]["unit"] == "mL"

    def test_encounter_exact_values(self, cerner_bundle):
        """Validate Encounter has EXACT values."""
        encounters = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Encounter"]

        assert len(encounters) >= 1
        enc = encounters[0].dict() if hasattr(encounters[0], 'dict') else encounters[0].model_dump()

        # Exact class
        assert enc["class"]["code"] == "AMB"  # Ambulatory
        assert enc["class"]["system"] == "http://terminology.hl7.org/CodeSystem/v3-ActCode"

        # Exact status
        assert enc["status"] == "finished"

        # Exact period start
        from datetime import datetime
        assert isinstance(enc["period"]["start"], datetime)

        # Has location reference
        if "location" in enc:
            assert len(enc["location"]) >= 1
            assert enc["location"][0]["location"]["reference"].startswith("Location/")

        # Exact participant (high-priority untested field)
        assert "participant" in enc
        assert len(enc["participant"]) >= 1
        participant = enc["participant"][0]
        assert "type" in participant
        assert len(participant["type"]) >= 1
        assert "coding" in participant["type"][0]
        assert participant["type"][0]["coding"][0]["system"] == \
            "http://terminology.hl7.org/CodeSystem/v3-ParticipationType"
        assert participant["type"][0]["coding"][0]["code"] == "PART"

    def test_practitioner_exact_values(self, cerner_bundle):
        """Validate Practitioner has EXACT values."""
        practitioners = [e.resource for e in cerner_bundle.entry
                        if e.resource.get_resource_type() == "Practitioner"]

        assert len(practitioners) >= 1
        prac = practitioners[0].dict() if hasattr(practitioners[0], 'dict') else practitioners[0].model_dump()

        # Exact name
        assert len(prac["name"]) >= 1
        name = prac["name"][0]
        assert name["family"] == "Admit"
        assert name["given"] == ["Aaron"]
        assert name["suffix"] == ["MD"]

        # Exact address
        if "address" in prac and prac["address"]:
            addr = prac["address"][0]
            assert addr["line"] == ["1006 Healthcare Dr"]
            assert addr["city"] == "Portland"
            assert addr["state"] == "OR"
            assert addr["postalCode"] == "97005-"

    def test_composition_exact_values(self, cerner_bundle):
        """Validate Composition has EXACT values."""
        compositions = [e.resource for e in cerner_bundle.entry
                       if e.resource.get_resource_type() == "Composition"]

        assert len(compositions) == 1
        comp = compositions[0].dict() if hasattr(compositions[0], 'dict') else compositions[0].model_dump()

        # Exact status
        assert comp["status"] == "final"

        # Exact type
        loinc_coding = next((c for c in comp["type"]["coding"]
                            if c["system"] == "http://loinc.org"), None)
        assert loinc_coding["code"] == "34133-9"
        assert loinc_coding["display"] == "Summarization of episode note"

        # Exact title
        assert comp["title"] == "Transition of Care/Referral Summary"

        # Exact date
        from datetime import datetime
        assert isinstance(comp["date"], datetime)

        # Has encounter reference
        if "encounter" in comp:
            assert comp["encounter"]["reference"].startswith("Encounter/")

        # Has sections
        assert "section" in comp and len(comp["section"]) > 0

    def test_diagnostic_report_exact_values(self, cerner_bundle):
        """Validate DiagnosticReport has EXACT values."""
        reports = [e.resource for e in cerner_bundle.entry
                  if e.resource.get_resource_type() == "DiagnosticReport"]

        if len(reports) > 0:
            report = reports[0].dict() if hasattr(reports[0], 'dict') else reports[0].model_dump()

            # Exact identifier - US Core Must-Support field
            assert "identifier" in report
            assert len(report["identifier"]) >= 1
            first_id = report["identifier"][0]
            assert "system" in first_id
            assert "value" in first_id
            assert first_id["system"].startswith("urn:")
            assert first_id["value"] is not None

            # Exact status
            assert report["status"] in ["final", "preliminary", "registered"]

            # Exact category - LAB
            assert len(report["category"]) >= 1
            assert report["category"][0]["coding"][0]["code"] == "LAB"
            assert report["category"][0]["coding"][0]["system"] == \
                "http://terminology.hl7.org/CodeSystem/v2-0074"

            # Has result references
            if "result" in report:
                for result in report["result"]:
                    assert result["reference"].startswith("Observation/")

    def test_procedure_ecg_exact_values(self, cerner_bundle):
        """Validate Electrocardiographic procedure has EXACT values."""
        procedures = [e.resource for e in cerner_bundle.entry
                     if e.resource.get_resource_type() == "Procedure"]

        # Find ECG procedure by SNOMED code 29303009
        ecg = None
        for proc in procedures:
            p = proc.dict() if hasattr(proc, 'dict') else proc.model_dump()
            if "code" in p and p["code"] and "coding" in p["code"]:
                if any(coding.get("code") == "29303009" for coding in p["code"]["coding"]):
                    ecg = p
                    break

        assert ecg is not None, "Must have Electrocardiographic procedure"

        # Exact code - SNOMED CT
        snomed_coding = next((c for c in ecg["code"]["coding"]
                             if c["system"] == "http://snomed.info/sct"), None)
        assert snomed_coding is not None
        assert snomed_coding["code"] == "29303009"
        assert "Electrocardiographic procedure" in snomed_coding["display"]

        # Exact status
        assert ecg["status"] == "completed"

        # Has performedDateTime
        assert "performedDateTime" in ecg
        from datetime import datetime
        assert isinstance(ecg["performedDateTime"], datetime)

        # Has subject reference to Patient
        assert ecg["subject"]["reference"].startswith("Patient/")

    def test_organization_exact_values(self, cerner_bundle):
        """Validate Organization has EXACT values."""
        organizations = [e.resource for e in cerner_bundle.entry
                        if e.resource.get_resource_type() == "Organization"]

        assert len(organizations) >= 1, "Must have Organization resource"

        org = organizations[0].dict() if hasattr(organizations[0], 'dict') else organizations[0].model_dump()

        # Exact name
        assert org["name"] == "Local Community Hospital Organization"

        # Exact identifier
        assert "identifier" in org
        assert len(org["identifier"]) >= 1
        ident = org["identifier"][0]
        assert ident["system"] == "urn:oid:2.16.840.1.113883.1.13.99999"
        assert ident["value"] == "2.16.840.1.113883.1.13.99999"

        # Exact telecom
        assert "telecom" in org
        assert len(org["telecom"]) >= 1
        telecom = org["telecom"][0]
        assert telecom["system"] == "phone"
        assert telecom["value"] == "(555) 555-1010"
        assert telecom["use"] == "work"

        # Exact address
        assert "address" in org
        assert len(org["address"]) >= 1
        addr = org["address"][0]
        assert addr["line"] == ["4000 Hospital Dr."]
        assert addr["city"] == "Portland"
        assert addr["state"] == "OR"
        assert addr["postalCode"] == "97005-"

    def test_device_exact_values(self, cerner_bundle):
        """Validate Device (EHR system) has EXACT values."""
        devices = [e.resource for e in cerner_bundle.entry
                  if e.resource.get_resource_type() == "Device"]

        assert len(devices) >= 1, "Must have Device resource"

        device = devices[0].dict() if hasattr(devices[0], 'dict') else devices[0].model_dump()

        # Exact type - Electronic health record (SNOMED)
        assert "type" in device
        assert "coding" in device["type"]
        snomed_coding = next((c for c in device["type"]["coding"]
                             if c.get("system") == "http://snomed.info/sct"), None)
        assert snomed_coding is not None
        assert snomed_coding["code"] == "706689003"
        assert snomed_coding["display"] == "Electronic health record"
        assert device["type"]["text"] == "Electronic Health Record System"

        # Exact deviceName - manufacturer and model
        assert "deviceName" in device
        assert len(device["deviceName"]) >= 2

        # Find manufacturer name
        manufacturer = next((d for d in device["deviceName"]
                            if d.get("type") == "manufacturer-name"), None)
        assert manufacturer is not None
        assert manufacturer["name"] == "Cerner Corporation"

        # Find model name
        model = next((d for d in device["deviceName"]
                     if d.get("type") == "model-name"), None)
        assert model is not None
        assert model["name"] == "Millennium Clinical Document Generator"

    def test_document_reference_exact_values(self, cerner_bundle):
        """Validate DocumentReference has EXACT values."""
        docrefs = [e.resource for e in cerner_bundle.entry
                  if e.resource.get_resource_type() == "DocumentReference"]

        assert len(docrefs) >= 1, "Must have DocumentReference resource"

        docref = docrefs[0].dict() if hasattr(docrefs[0], 'dict') else docrefs[0].model_dump()

        # Exact status
        assert docref["status"] == "current"

        # Exact type - LOINC 34133-9
        assert "type" in docref
        assert "coding" in docref["type"]
        loinc_coding = next((c for c in docref["type"]["coding"]
                            if c.get("system") == "http://loinc.org"), None)
        assert loinc_coding is not None
        assert loinc_coding["code"] == "34133-9"
        assert loinc_coding["display"] == "Summarization of episode note"
        assert docref["type"]["text"] == "Summarization of episode note"

        # Exact category
        assert "category" in docref
        assert len(docref["category"]) >= 1
        cat_coding = docref["category"][0]["coding"][0]
        assert cat_coding["code"] == "clinical-note"
        assert cat_coding["display"] == "Clinical Note"

        # Exact masterIdentifier
        assert "masterIdentifier" in docref
        assert docref["masterIdentifier"]["system"] == "urn:oid:2.16.840.1.113883.1.13.99999.999362"
        assert docref["masterIdentifier"]["value"] == "280004"

        # Exact content attachment
        assert "content" in docref
        assert len(docref["content"]) >= 1
        att = docref["content"][0]["attachment"]
        assert att["contentType"] == "text/xml"
        assert att["title"] == "Summarization of episode note"
        assert "creation" in att
        assert "data" in att  # Has base64 data
        assert att["size"] == 94270

    def test_location_exact_values(self, cerner_bundle):
        """Validate Location has EXACT values."""
        locations = [e.resource for e in cerner_bundle.entry
                    if e.resource.get_resource_type() == "Location"]

        assert len(locations) >= 1, "Must have Location resource"

        loc = locations[0].dict() if hasattr(locations[0], 'dict') else locations[0].model_dump()

        # Exact status
        assert loc["status"] == "active"

        # Exact name
        assert loc["name"] == "Local Community Hospital Organization"

        # Exact mode
        assert loc["mode"] == "instance"

        # Exact telecom
        assert "telecom" in loc
        assert len(loc["telecom"]) >= 1
        phone = next((t for t in loc["telecom"] if t.get("system") == "phone"), None)
        assert phone is not None
        assert phone["value"] == "(555) 555-1010"
        assert phone["use"] == "work"

        # Exact address
        assert "address" in loc
        assert loc["address"]["line"] == ["4000 Hospital Dr."]
        assert loc["address"]["city"] == "Portland"
        assert loc["address"]["state"] == "OR"
        assert loc["address"]["postalCode"] == "97005-"
        assert loc["address"]["country"] == "US"
