# Why Composition.status is Always "final"

**Decision Date**: 2025-12-10
**Code Location**: `ccda_to_fhir/converters/composition.py:81-87`

## Decision

All FHIR Composition resources are created with `status: "final"`, regardless of C-CDA authentication elements (`legalAuthenticator`, `authenticator`).

## Rationale

After thorough research into the official C-CDA on FHIR specification, we determined that using `legalAuthenticator` to infer `Composition.status` is **not supported by the standard**.

### Key Findings

1. **Per C-CDA on FHIR spec**: `legalAuthenticator` maps to `Composition.attester` (not `status`)
   - Reference: [C-CDA on FHIR Participation Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participations.html)
   - Reference: [Our mapping documentation](mapping/09-practitioner.md#legal-authenticator-mapping)

2. **No official guidance exists** for inferring `status` from authentication state
   - The C-CDA on FHIR spec explicitly states it "does not provide definitive CDA ↔ FHIR guidance" on authentication/provenance mappings
   - Reference: [C-CDA on FHIR Mapping Guidance](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html)

3. **Defaulting to "final" is the safer approach** for completed documents
   - C-CDA documents in production systems are typically completed and signed
   - Using "final" prevents incorrect downstream assumptions about document state

## Current Implementation

```python
# Status - REQUIRED (preliminary | final | amended | entered-in-error)
# Default to "final" for completed documents
# NOTE: C-CDA legalAuthenticator maps to Composition.attester (not status) per
# C-CDA on FHIR spec. There is no official guidance for inferring status from
# authentication state. Using "final" as default is the safest approach.
# See: https://build.fhir.org/ig/HL7/ccda-on-fhir/
composition["status"] = FHIRCodes.CompositionStatus.FINAL
```

## Alternative Considered (Rejected)

Inferring status from authentication elements:

| C-CDA Element | Proposed FHIR Status | Why Rejected |
|---------------|---------------------|--------------|
| `legalAuthenticator` present | `final` | Not supported by spec; legalAuthenticator maps to attester |
| `authenticator` present only | `preliminary` | No spec guidance; unclear semantics |
| Neither present | `preliminary` | Unreliable; many valid documents lack these elements |

## Verification

Verified against official specifications on 2025-12-15:
- ✅ C-CDA on FHIR Implementation Guide confirms no status mapping
- ✅ Local mapping documentation confirms legalAuthenticator → Composition.attester
- ✅ Code comment accurately reflects spec limitations
