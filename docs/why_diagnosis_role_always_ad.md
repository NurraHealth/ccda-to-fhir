# Encounter Diagnosis Role Detection: Evolution and Implementation

**Current Approach**: Context-based intelligent detection (since 2025-12-18)
**Previous Approach**: Always "AD" (2025-12-10 to 2025-12-18)
**Code Location**: `ccda_to_fhir/converters/encounter.py:565-666`

## Current Implementation (2025-12-18)

After initial implementation with a static default, we evolved to **intelligent context-based diagnosis role detection** that analyzes encounter characteristics to infer the appropriate role.

### Detection Logic

| Encounter Context | Diagnosis Role | Code | Rationale |
|-------------------|----------------|------|-----------|
| Has discharge disposition | Discharge diagnosis | `DD` | Discharge info indicates diagnosis documented at discharge |
| Inpatient class (IMP/ACUTE/NONAC) | Admission diagnosis | `AD` | Inpatient encounters typically document admission diagnoses |
| Emergency class (EMER) | Admission diagnosis | `AD` | Emergency diagnoses documented at presentation/admission |
| All other encounters | Billing | `billing` | Default for outpatient/ambulatory encounters |

### Implementation

```python
def _determine_diagnosis_role(self, encounter: CCDAEncounter) -> dict[str, str]:
    """Determine diagnosis role from encounter context.

    Priority order:
    1. Discharge disposition present → DD (discharge diagnosis)
    2. Inpatient/emergency class → AD (admission diagnosis)
    3. Default → billing (general documentation)
    """
    # Check for discharge disposition - indicates discharge diagnosis
    if encounter.sdtc_discharge_disposition_code:
        return {"code": "DD", "display": "Discharge diagnosis"}

    # Check encounter class for inpatient or emergency
    encounter_class = self._extract_encounter_class(encounter)

    if encounter_class in ["IMP", "ACUTE", "NONAC"]:
        return {"code": "AD", "display": "Admission diagnosis"}

    if encounter_class == "EMER":
        return {"code": "AD", "display": "Admission diagnosis"}

    # Default to billing for all other encounters
    return {"code": "billing", "display": "Billing"}
```

### Rationale for Context-Based Approach

**Why we evolved from static "AD" to intelligent detection:**

1. **Semantic Accuracy**: Different encounter types have different diagnostic purposes
   - Outpatient visits document diagnoses for billing/documentation
   - Inpatient encounters focus on admission diagnoses
   - Discharge encounters document final diagnoses

2. **Clinical Validity**: The diagnosis role reflects real-world clinical workflow
   - Admission diagnoses: Initial assessment at hospital entry
   - Discharge diagnoses: Final diagnoses after full workup
   - Billing diagnoses: General documentation for payment

3. **Interoperability**: Downstream systems can better understand diagnosis context
   - Quality reporting systems use diagnosis roles for metrics
   - Billing systems distinguish admission vs discharge for reimbursement
   - Clinical decision support systems consider diagnosis timing

4. **Standards Alignment**: While C-CDA doesn't encode roles explicitly, encounter context provides reliable signals
   - Discharge disposition strongly indicates discharge diagnosis
   - Encounter class (inpatient, emergency) indicates admission diagnosis
   - Default to billing matches common practice for ambulatory care

### Test Coverage

Four comprehensive tests validate the logic:
- `test_ambulatory_encounter_diagnosis_uses_billing_role`
- `test_inpatient_encounter_diagnosis_uses_admission_role`
- `test_emergency_encounter_diagnosis_uses_admission_role`
- `test_encounter_with_discharge_uses_discharge_diagnosis_role`

---

## Historical Context: Original "Always AD" Approach

**Decision Date**: 2025-12-10
**Superseded**: 2025-12-18
**Why Changed**: See rationale above

### Original Decision

All encounter diagnoses were created with `diagnosis.use` set to "AD" (Admission diagnosis), regardless of C-CDA context.

### Original Rationale

After thorough research into the official C-CDA on FHIR specification, we determined that mapping `entryRelationship/@typeCode` to `Encounter.diagnosis.use` is **not supported by the standard**.

Key findings that led to the "always AD" approach:

1. **C-CDA on FHIR spec provides no mapping guidance**
   - The spec focuses only on mapping the diagnosis observation to a Condition
   - No guidance exists for determining diagnosis role (AD, DD, CC, billing, etc.)
   - Reference: [C-CDA on FHIR Encounters](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html)

2. **The `diagnosis.use` binding is "Preferred" (not required)**
   - FHIR allows implementations to use any reasonable approach
   - A static default was initially considered safe

3. **`entryRelationship/@typeCode` doesn't map to diagnosis roles**
   - TypeCode values like "SUBJ" and "REFR" describe entry relationships
   - They don't encode diagnosis timing (admission, discharge, etc.)

### Why We Evolved Beyond "Always AD"

While the original approach was standards-compliant, it had limitations:

1. **Lost Semantic Information**: All diagnoses appeared as "admission" regardless of actual timing
2. **Clinical Implausibility**: Outpatient visit diagnoses labeled as "admission diagnoses"
3. **Missed Opportunities**: Encounter context provides reliable signals for diagnosis role
4. **Better Approach Available**: Context-based inference is more accurate than static default

The new approach maintains standards compliance while providing better semantic accuracy.

---

## Standards Compliance

Both approaches (static "AD" and context-based detection) are **fully compliant** with C-CDA and FHIR specifications:

### Why Static "AD" Was Compliant
- C-CDA provides no diagnosis role encoding → implementation discretion allowed ✓
- FHIR diagnosis.use has "Preferred" binding → default value acceptable ✓
- All codes from official diagnosis-role CodeSystem ✓

### Why Context-Based Detection Is Compliant
- Uses only standard encounter attributes (class, discharge disposition) ✓
- All diagnosis roles from official diagnosis-role CodeSystem ✓
- Context-based inference fills spec gap with reasonable heuristics ✓
- Verified against FHIR CodeSystem: http://terminology.hl7.org/CodeSystem/diagnosis-role ✓

### FHIR Diagnosis Role Codes (All Valid)

| Code | Display | Definition |
|------|---------|------------|
| `AD` | Admission diagnosis | "The diagnoses documented for administrative purposes as the basis for a hospital or other institutional admission" |
| `DD` | Discharge diagnosis | "The diagnoses documented for administrative purposes at the time of hospital or other institutional discharge" |
| `billing` | Billing | "The diagnosis documented for billing purposes" |
| `CC` | Chief complaint | Chief presenting complaint |
| `CM` | Comorbidity diagnosis | Comorbid conditions |
| `pre-op` | Pre-op diagnosis | Pre-operative diagnosis |
| `post-op` | Post-op diagnosis | Post-operative diagnosis |

---

## Key Learnings

1. **Standards leave implementation gaps**: C-CDA on FHIR doesn't cover every mapping scenario
2. **Context provides signals**: Encounter attributes (class, discharge disposition) reliably indicate diagnosis roles
3. **Evolution is appropriate**: Moving from simple default to intelligent detection improves quality
4. **Both approaches are valid**: Static default and context-based inference are both standards-compliant

---

## References

### FHIR Specifications
- [Encounter.diagnosis.use](http://hl7.org/fhir/R4/encounter-definitions.html#Encounter.diagnosis.use)
- [DiagnosisRole CodeSystem](http://terminology.hl7.org/CodeSystem/diagnosis-role)
- [FHIR Encounter Resource](https://hl7.org/fhir/R4B/encounter.html)

### C-CDA Specifications
- [C-CDA on FHIR Encounters](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html)
- [Encounter Diagnosis Act](https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.80.html)
- [Encounter Activity](https://cdasearch.hl7.org/examples/view/Guide%20Examples/Encounter%20Activity%20(V3)_2.16.840.1.113883.10.20.22.4.49)

### Implementation Documentation
- [Local encounter mapping](mapping/08-encounter.md#diagnosis-role-detection)
