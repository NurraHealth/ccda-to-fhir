# Why Encounter.diagnosis.use is Always "AD" (Admission Diagnosis)

**Decision Date**: 2025-12-10
**Code Location**: `ccda_to_fhir/converters/encounter.py:516-520`

## Decision

All encounter diagnoses are created with `diagnosis.use` set to "AD" (Admission diagnosis), regardless of C-CDA `entryRelationship/@typeCode` values.

## Rationale

After thorough research into the official C-CDA on FHIR specification, we determined that mapping `entryRelationship/@typeCode` to `Encounter.diagnosis.use` is **not supported by the standard**.

### Key Findings

1. **C-CDA on FHIR spec provides no mapping guidance**
   - The spec focuses only on mapping the diagnosis observation to a Condition
   - No guidance exists for determining diagnosis role (AD, DD, CC, billing, etc.)
   - Reference: [C-CDA on FHIR Encounters](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html)

2. **Encounter Diagnosis mapping documentation states "No Mappings Found"**
   - Official HL7 mappings for Encounter Diagnosis don't cover diagnosis.use
   - Reference: [StructureDefinition Mappings](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-EncounterDiagnosis-mappings.html)

3. **The `diagnosis.use` binding is "Preferred" (not required)**
   - FHIR allows implementations to use a consistent default value
   - Defaulting to "AD" is acceptable and safe

4. **Our mapping documentation shows example, not derivation**
   - Local docs show `diagnosis.use: "AD"` as an example output
   - No guidance on HOW to determine the value from C-CDA elements
   - Reference: [Our encounter mapping](mapping/08-encounter.md#diagnosis-mapping)

## Current Implementation

```python
# Default to "AD" (admission diagnosis)
# NOTE: C-CDA on FHIR spec provides no guidance for mapping
# entryRelationship/@typeCode to Encounter.diagnosis.use.
# The binding is "Preferred" (not required), so defaulting to
# AD is a safe, conservative approach.
# See: https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-encounters.html
diagnosis["use"] = {
    "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
        "code": "AD",
        "display": "Admission diagnosis"
    }]
}
```

## Alternative Considered (Rejected)

Inferring diagnosis role from C-CDA context:

| C-CDA Context | Proposed Code | Why Rejected |
|---------------|---------------|--------------|
| `entryRelationship[@typeCode="SUBJ"]` with admission context | `AD` | No spec mapping; context detection unreliable |
| `entryRelationship[@typeCode="SUBJ"]` with discharge context | `DD` | No spec mapping; would require encounter type analysis |
| `entryRelationship[@typeCode="REFR"]` | `CC` | No spec mapping; typeCode semantics don't align with diagnosis role |
| `act[@classCode="BILLING"]` | `billing` | Rare in practice; no spec support |

### Problems with Inferred Mapping

1. **No authoritative source**: C-CDA typeCode values don't have documented mappings to FHIR diagnosis role codes
2. **Context ambiguity**: Determining "admission" vs "discharge" context requires heuristics
3. **Complexity without benefit**: Most systems don't distinguish diagnosis roles at this level
4. **Risk of incorrect semantics**: Mapping typeCode → diagnosis.use could create false implications

## Verification

Verified against official specifications on 2025-12-15:
- ✅ C-CDA on FHIR Implementation Guide confirms no diagnosis.use mapping
- ✅ HL7 StructureDefinition confirms "No Mappings Found"
- ✅ Local mapping documentation shows example only, no derivation
- ✅ Code comment accurately reflects spec limitations

## Additional Notes

The `diagnosis.use` field is primarily useful for:
- Billing systems that need to distinguish admission vs discharge diagnoses
- Quality reporting that tracks diagnosis timing

Since C-CDA doesn't reliably encode this distinction, and the FHIR binding is "Preferred" (not required), using a consistent default is the most honest and interoperable approach.
