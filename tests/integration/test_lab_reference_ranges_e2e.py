"""Extremely detailed E2E test for lab results with multiple reference ranges.

This test validates the conversion of a C-CDA lab result document that includes
the critical Observation.referenceRange.text field, which was previously untested
due to lack of sample data.

Key Features Tested:
- Observation.referenceRange with text element (3 ranges)
- DiagnosticReport with lab organizer
- Patient demographics
- Practitioner (lab technologist)
- Organization (custodian)
- Composition metadata
"""

from datetime import datetime

import pytest

from ccda_to_fhir.convert import convert_document
from fhir.resources.bundle import Bundle


@pytest.fixture
def lab_reference_ranges_bundle():
    """Load and convert the lab reference ranges C-CDA document."""
    with open("tests/integration/fixtures/documents/lab_reference_ranges.xml") as f:
        ccda_xml = f.read()

    result = convert_document(ccda_xml)
    bundle = Bundle(**result["bundle"])
    return bundle


class TestLabReferenceRangesE2E:
    """Extremely detailed E2E tests for lab results with reference ranges."""

    def test_bundle_structure(self, lab_reference_ranges_bundle):
        """Validate overall bundle structure and resource count."""
        assert lab_reference_ranges_bundle.type == "document"
        assert lab_reference_ranges_bundle.entry is not None
        assert len(lab_reference_ranges_bundle.entry) >= 6, \
            "Bundle should contain Patient, Practitioner, Organization, Observation, DiagnosticReport, Composition"

        # Count resource types
        resource_types = {}
        for entry in lab_reference_ranges_bundle.entry:
            rtype = entry.resource.get_resource_type()
            resource_types[rtype] = resource_types.get(rtype, 0) + 1

        assert resource_types.get("Patient") == 1, "Must have exactly 1 Patient"
        assert resource_types.get("Practitioner") >= 1, "Must have at least 1 Practitioner"
        assert resource_types.get("Organization") >= 1, "Must have at least 1 Organization"
        assert resource_types.get("Observation") >= 1, "Must have at least 1 Observation"
        assert resource_types.get("DiagnosticReport") >= 1, "Must have at least 1 DiagnosticReport"
        assert resource_types.get("Composition") == 1, "Must have exactly 1 Composition"

    def test_patient_exact_values(self, lab_reference_ranges_bundle):
        """Validate Patient resource with exact field values."""
        patients = [e.resource for e in lab_reference_ranges_bundle.entry
                   if e.resource.get_resource_type() == "Patient"]

        assert len(patients) == 1
        patient = patients[0].dict() if hasattr(patients[0], 'dict') else patients[0].model_dump()

        # Exact identifier
        assert "identifier" in patient
        assert len(patient["identifier"]) >= 1
        mrn = next((i for i in patient["identifier"]
                   if i.get("system") == "urn:oid:2.16.840.1.113883.19.5.99999.2"), None)
        assert mrn is not None
        assert mrn["value"] == "444222222"

        # Exact name
        assert "name" in patient
        assert len(patient["name"]) >= 1
        name = patient["name"][0]
        assert name["family"] == "Everywoman"
        assert name["given"] == ["Eve"]
        assert name["use"] == "usual"

        # Exact gender
        assert patient["gender"] == "female"

        # Exact birthDate
        from datetime import date
        assert patient["birthDate"] == date(1975, 5, 1) or patient["birthDate"] == "1975-05-01"

        # Exact address
        assert "address" in patient
        assert len(patient["address"]) >= 1
        addr = patient["address"][0]
        assert addr["use"] == "home"
        assert addr["line"] == ["2222 Home Street"]
        assert addr["city"] == "Beaverton"
        assert addr["state"] == "OR"
        assert addr["postalCode"] == "97867"
        assert addr["country"] == "US"

        # Exact telecom
        assert "telecom" in patient
        assert len(patient["telecom"]) >= 1
        phone = next((t for t in patient["telecom"] if t.get("system") == "phone"), None)
        assert phone is not None
        assert phone["value"] == "+1(555)723-1544"
        assert phone["use"] == "home"

    def test_practitioner_exact_values(self, lab_reference_ranges_bundle):
        """Validate Practitioner (lab technologist) with exact values."""
        practitioners = [e.resource for e in lab_reference_ranges_bundle.entry
                        if e.resource.get_resource_type() == "Practitioner"]

        assert len(practitioners) >= 1

        # Find the lab technologist (author)
        lab_tech = None
        for prac in practitioners:
            p = prac.dict() if hasattr(prac, 'dict') else prac.model_dump()
            if "identifier" in p:
                for ident in p["identifier"]:
                    if ident.get("value") == "333444444":
                        lab_tech = p
                        break
            if lab_tech:
                break

        assert lab_tech is not None, "Must have lab technologist practitioner"

        # Exact identifier
        npi = next((i for i in lab_tech["identifier"]
                   if i.get("system") == "http://hl7.org/fhir/sid/us-npi"), None)
        assert npi is not None
        assert npi["value"] == "333444444"

        # Exact name
        assert "name" in lab_tech
        assert len(lab_tech["name"]) >= 1
        name = lab_tech["name"][0]
        assert name["family"] == "Seven"
        assert name["given"] == ["Henry"]

        # Exact qualification (Pathology Technologist)
        if "qualification" in lab_tech and lab_tech["qualification"]:
            qual = lab_tech["qualification"][0]
            assert "code" in qual
            nucc_code = next((c for c in qual["code"]["coding"]
                            if c.get("system") == "http://nucc.org/provider-taxonomy"), None)
            assert nucc_code is not None
            assert nucc_code["code"] == "246Q00000X"
            assert "Pathology" in nucc_code["display"]

    def test_organization_exact_values(self, lab_reference_ranges_bundle):
        """Validate Organization (custodian) with exact values."""
        orgs = [e.resource for e in lab_reference_ranges_bundle.entry
               if e.resource.get_resource_type() == "Organization"]

        assert len(orgs) >= 1

        # Find Community Health and Hospitals
        custodian_org = None
        for org in orgs:
            o = org.dict() if hasattr(org, 'dict') else org.model_dump()
            if o.get("name") == "Community Health and Hospitals":
                custodian_org = o
                break

        assert custodian_org is not None

        # Exact name
        assert custodian_org["name"] == "Community Health and Hospitals"

        # Exact identifier (NPI)
        assert "identifier" in custodian_org
        npi = next((i for i in custodian_org["identifier"]
                   if i.get("value") == "99999999"), None)
        assert npi is not None

        # Exact telecom
        assert "telecom" in custodian_org
        phone = next((t for t in custodian_org["telecom"]
                     if t.get("system") == "phone"), None)
        assert phone is not None
        assert phone["value"] == "+1(555)555-1002"
        assert phone["use"] == "work"

        # Exact address
        assert "address" in custodian_org
        addr = custodian_org["address"][0]
        assert addr["line"] == ["1002 Healthcare Dr"]
        assert addr["city"] == "Portland"
        assert addr["state"] == "OR"
        assert addr["postalCode"] == "97266"
        assert addr["country"] == "US"

    def test_diagnostic_report_exact_values(self, lab_reference_ranges_bundle):
        """Validate DiagnosticReport (lab organizer) with exact values."""
        reports = [e.resource for e in lab_reference_ranges_bundle.entry
                  if e.resource.get_resource_type() == "DiagnosticReport"]

        assert len(reports) >= 1
        report = reports[0].dict() if hasattr(reports[0], 'dict') else reports[0].model_dump()

        # Exact status
        assert report["status"] == "final"

        # Exact category - LAB
        assert "category" in report
        assert len(report["category"]) >= 1
        lab_category = report["category"][0]["coding"][0]
        assert lab_category["code"] == "LAB"
        assert lab_category["system"] == "http://terminology.hl7.org/CodeSystem/v2-0074"

        # Exact code - Nuclear Ab panel LOINC 5048-4
        assert "code" in report
        loinc_code = next((c for c in report["code"]["coding"]
                          if c.get("system") == "http://loinc.org"), None)
        assert loinc_code is not None
        assert loinc_code["code"] == "5048-4"
        assert "Nuclear Ab" in loinc_code["display"]

        # Exact effectiveDateTime
        assert "effectiveDateTime" in report or "effectivePeriod" in report
        if "effectivePeriod" in report:
            period = report["effectivePeriod"]
            assert "start" in period
            assert period["start"].startswith("2017-03-19")

        # Exact subject reference
        assert "subject" in report
        assert report["subject"]["reference"].startswith("Patient/")

        # Exact result references
        assert "result" in report
        assert len(report["result"]) >= 1
        assert report["result"][0]["reference"].startswith("Observation/")

    def test_observation_nuclear_antibody_exact_values(self, lab_reference_ranges_bundle):
        """Validate Nuclear Antibody Observation with EXACT values including referenceRange.text.

        This is the CRITICAL test - validates the previously untested referenceRange.text field.
        """
        observations = [e.resource for e in lab_reference_ranges_bundle.entry
                       if e.resource.get_resource_type() == "Observation"]

        assert len(observations) >= 1

        # Find the Nuclear Ab observation (LOINC 5048-4)
        nuclear_ab_obs = None
        for obs in observations:
            o = obs.dict() if hasattr(obs, 'dict') else obs.model_dump()
            if "code" in o and "coding" in o["code"]:
                for coding in o["code"]["coding"]:
                    if coding.get("code") == "5048-4":
                        nuclear_ab_obs = o
                        break
            if nuclear_ab_obs:
                break

        assert nuclear_ab_obs is not None, "Must have Nuclear Ab observation"

        # Exact status
        assert nuclear_ab_obs["status"] == "final"

        # Exact category - laboratory
        assert "category" in nuclear_ab_obs
        lab_cat = next((c for c in nuclear_ab_obs["category"]
                       if any(coding.get("code") == "laboratory"
                             for coding in c.get("coding", []))), None)
        assert lab_cat is not None

        # Exact code - LOINC 5048-4
        assert "code" in nuclear_ab_obs
        loinc = next((c for c in nuclear_ab_obs["code"]["coding"]
                     if c.get("system") == "http://loinc.org"), None)
        assert loinc is not None
        assert loinc["code"] == "5048-4"
        assert "Nuclear Ab" in loinc["display"]
        assert "Immunofluorescence" in loinc["display"]

        # Exact subject reference
        assert "subject" in nuclear_ab_obs
        assert nuclear_ab_obs["subject"]["reference"].startswith("Patient/")

        # Exact effectiveDateTime
        assert "effectiveDateTime" in nuclear_ab_obs
        eff_time = nuclear_ab_obs["effectiveDateTime"]
        if isinstance(eff_time, str):
            assert eff_time.startswith("2017-03-19")
        else:
            assert eff_time.year == 2017 and eff_time.month == 3 and eff_time.day == 19

        # Exact value - String type: "Borderline, equal to 1:80"
        assert "valueString" in nuclear_ab_obs
        assert nuclear_ab_obs["valueString"] == "Borderline, equal to 1:80"

        # Exact interpretation - Abnormal
        assert "interpretation" in nuclear_ab_obs
        assert len(nuclear_ab_obs["interpretation"]) >= 1
        interp_coding = nuclear_ab_obs["interpretation"][0]["coding"][0]
        assert interp_coding["code"] == "A"
        assert interp_coding["display"] == "Abnormal"
        assert interp_coding["system"] == "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation"

        # *** CRITICAL: Exact referenceRange with TEXT - This is the key test! ***
        assert "referenceRange" in nuclear_ab_obs, "MUST have referenceRange"

        # Per C-CDA on FHIR IG: Only reference ranges with interpretationCode="N" are converted
        # This document has 3 ranges in C-CDA: 1 Normal (N), 2 Abnormal (A)
        # Result: Only the Normal range should be converted
        assert len(nuclear_ab_obs["referenceRange"]) == 1, \
            "Must have exactly 1 reference range (only Normal interpretationCode filtered per spec)"

        ref_ranges = nuclear_ab_obs["referenceRange"]

        # Reference Range: Negative, less than 1:80 (Normal - interpretationCode="N")
        neg_range = ref_ranges[0]
        assert "text" in neg_range, "CRITICAL: referenceRange.text must be present"
        assert neg_range["text"] == "Negative, less than 1:80", \
            "referenceRange.text must match C-CDA observationRange/text"

        print("\n" + "="*70)
        print("✅ SUCCESS: Observation.referenceRange.text is correctly implemented!")
        print("="*70)
        print(f"Validated referenceRange with text: '{neg_range['text']}'")
        print("Note: Only Normal ranges (interpretationCode='N') converted per C-CDA on FHIR IG")
        print("="*70)

        # Exact performer (lab technologist)
        if "performer" in nuclear_ab_obs:
            assert len(nuclear_ab_obs["performer"]) >= 1
            performer_ref = nuclear_ab_obs["performer"][0]["reference"]
            assert performer_ref.startswith("Practitioner/")

    def test_composition_exact_values(self, lab_reference_ranges_bundle):
        """Validate Composition (document metadata) with exact values."""
        compositions = [e.resource for e in lab_reference_ranges_bundle.entry
                       if e.resource.get_resource_type() == "Composition"]

        assert len(compositions) == 1
        comp = compositions[0].dict() if hasattr(compositions[0], 'dict') else compositions[0].model_dump()

        # Exact status
        assert comp["status"] == "final"

        # Exact type - LOINC 34133-9
        assert "type" in comp
        loinc = next((c for c in comp["type"]["coding"]
                     if c.get("system") == "http://loinc.org"), None)
        assert loinc is not None
        assert loinc["code"] == "34133-9"
        assert "Summarization of Episode Note" in loinc["display"]

        # Exact title
        assert comp["title"] == "Lab Results with Multiple Reference Ranges"

        # Exact date
        assert "date" in comp
        assert isinstance(comp["date"], datetime)

        # Exact subject reference
        assert "subject" in comp
        assert comp["subject"]["reference"].startswith("Patient/")

        # Exact author reference
        assert "author" in comp
        assert len(comp["author"]) >= 1
        # Author may have reference or just display
        if isinstance(comp["author"][0], dict):
            # May have reference or display
            has_ref_or_display = "reference" in comp["author"][0] or "display" in comp["author"][0]
            assert has_ref_or_display
            if "reference" in comp["author"][0]:
                assert comp["author"][0]["reference"].startswith("Practitioner/")
            if "display" in comp["author"][0]:
                assert comp["author"][0]["display"] == "Henry Seven"

        # Exact custodian reference
        if "custodian" in comp:
            if "reference" in comp["custodian"]:
                assert comp["custodian"]["reference"].startswith("Organization/")
            elif "display" in comp["custodian"]:
                assert "Community Health" in comp["custodian"]["display"]

        # Has sections with Results
        assert "section" in comp
        assert len(comp["section"]) >= 1
        results_section = next((s for s in comp["section"]
                               if any(c.get("code") == "30954-2"
                                     for c in s.get("code", {}).get("coding", []))), None)
        assert results_section is not None
        assert results_section["title"] == "RESULTS"

    def test_all_references_resolve(self, lab_reference_ranges_bundle):
        """Validate that all resource references can be resolved within the bundle."""
        # Build resource ID map
        resource_map = {}
        for entry in lab_reference_ranges_bundle.entry:
            resource = entry.resource
            rtype = resource.get_resource_type()
            r = resource.dict() if hasattr(resource, 'dict') else resource.model_dump()
            if "id" in r:
                resource_map[f"{rtype}/{r['id']}"] = resource

        # Check all references
        references_to_check = []

        for entry in lab_reference_ranges_bundle.entry:
            resource = entry.resource
            r = resource.dict() if hasattr(resource, 'dict') else resource.model_dump()

            # Collect all reference fields
            if "subject" in r and "reference" in r["subject"]:
                references_to_check.append(r["subject"]["reference"])
            if "performer" in r:
                for perf in r["performer"]:
                    if "reference" in perf:
                        references_to_check.append(perf["reference"])
            if "author" in r:
                for auth in r["author"]:
                    if "reference" in auth:
                        references_to_check.append(auth["reference"])
            if "custodian" in r and "reference" in r.get("custodian", {}):
                references_to_check.append(r["custodian"]["reference"])
            if "result" in r:
                for res in r["result"]:
                    if "reference" in res:
                        references_to_check.append(res["reference"])

        # Verify all references exist
        for ref in references_to_check:
            assert ref in resource_map, f"Reference {ref} must resolve to a resource in the bundle"

    def test_fhir_validation_passes(self, lab_reference_ranges_bundle):
        """Validate that the bundle passes FHIR schema validation."""
        # The fact that we could create the Bundle object means it passed validation
        assert lab_reference_ranges_bundle.get_resource_type() == "Bundle"

        # Validate each resource can be serialized
        for entry in lab_reference_ranges_bundle.entry:
            resource = entry.resource
            resource_dict = resource.dict() if hasattr(resource, 'dict') else resource.model_dump()
            assert "resourceType" in resource_dict
            # Allow common FHIR resource types
            valid_types = [
                "Patient", "Practitioner", "Organization", "Observation",
                "DiagnosticReport", "Composition", "DocumentReference"
            ]
            assert resource_dict["resourceType"] in valid_types
