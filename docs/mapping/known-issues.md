# Known Issues: C-CDA to FHIR Mapping

This document tracks known limitations, edge cases, and unresolved challenges in the C-CDA to FHIR mapping implementation.

## Overview

This is a living document that captures known issues, ambiguities, and limitations in the current implementation. Issues are categorized by severity and area of impact.

**Issue Status Legend**:
- 🔴 **Critical**: Affects compliance or data integrity
- 🟡 **Moderate**: Affects functionality or usability
- 🟢 **Minor**: Edge case or cosmetic issue
- 📋 **Planned**: Fix scheduled in upcoming release
- 🤔 **Under Review**: Requires further analysis or community input

---

## Critical Issues

### 1. Custodian Cardinality Not Enforced ✅ RESOLVED

**Issue**: US Realm Header Profile requires `Composition.custodian` with cardinality 1..1, but implementation didn't enforce this.

**Impact**:
- Non-compliant FHIR output when C-CDA document lacks custodian
- Validation failures against US Core profiles

**Resolution** (Completed):
- ✅ C-CDA parser validates custodian for US Realm Header documents (template 2.16.840.1.113883.10.20.22.1.1) via Pydantic `@model_validator`
- ✅ Documents claiming US Realm Header conformance will fail at parse time if custodian is missing
- ✅ Composition converter now enforces fail-fast: raises `ValueError` if custodian missing or extraction fails
- ✅ No placeholder organizations created - all failures are explicit errors
- ✅ Added test coverage: `test_custodian_missing_fails`

**Current Behavior**:
- US Realm Header documents: Validated at parse-time (will fail if custodian missing)
- When custodian exists and extraction succeeds: references actual Organization resource
- When custodian is missing: raises ValueError (parse-time validation should prevent this)
- When custodian extraction fails: raises ValueError with clear error message
- No placeholder/unknown organization resources - all Organizations are real conversions from C-CDA data

**Official IG Guidance**: [US Realm Header Profile](https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-CF-usrealmheader.html)

---

### 2. Subject Cardinality Not Enforced ✅ RESOLVED

**Issue**: US Realm Header Profile requires `Composition.subject` with cardinality 1..1, but implementation didn't enforce this.

**Impact**:
- Non-compliant FHIR output when patient reference cannot be created
- Validation failures against US Core profiles

**Resolution** (Completed):
- ✅ Composition converter now validates that `subject` is present before creating Composition
- ✅ Raises `ValueError` if recordTarget is missing (should be caught by C-CDA validation for US Realm Header docs)
- ✅ Raises `ValueError` if patient conversion fails despite recordTarget existing
- ✅ Added test coverage for subject cardinality enforcement (`test_subject_required_always_present`)

**Current Behavior**:
- When recordTarget exists and patient conversion succeeds: subject references the actual Patient resource
- When recordTarget is missing: raises ValueError (US Realm Header validation should prevent this)
- When patient conversion fails: raises ValueError with clear error message
- No placeholder/unknown patient resources are created - all Patient resources are real conversions from C-CDA data

**Official IG Guidance**: [US Realm Header Profile - Composition.subject](https://hl7.org/fhir/us/ccda/2016Sep/StructureDefinition-ccda-us-realm-header-composition.html)

---

### 3. Missing C-CDA on FHIR Participant Extensions ✅ RESOLVED

**Issue**: Seven required participant extensions from C-CDA on FHIR IG were not implemented:
1. DataEnterer
2. Informant
3. InformationRecipient
4. Participant
5. Performer
6. Authorization
7. InFulfillmentOfOrder (Order)

**Resolution** (Completed):
- ✅ All seven participant extensions now implemented in `CompositionConverter`
- ✅ DataEnterer: Maps to `DataEntererExtension` with Practitioner/PractitionerRole reference
- ✅ Informant: Maps to `InformantExtension` - supports both assignedEntity (practitioner) and relatedEntity (family member)
- ✅ InformationRecipient: Maps to `InformationRecipientExtension` with Practitioner reference
- ✅ Participant: Maps to `ParticipantExtension` with reference to associated persons/caregivers
- ✅ Performer: Maps to `PerformerExtension` from documentationOf/serviceEvent/performer
- ✅ Authorization: Maps to `AuthorizationExtension` with Consent resource reference
- ✅ Order: Maps to `OrderExtension` (from inFulfillmentOf) with ServiceRequest reference
- ✅ Added comprehensive test coverage for all extensions

**Current Behavior**:
- All document-level participants are now preserved in FHIR Composition extensions
- Extensions follow official C-CDA on FHIR IG v2.0.0 structure definitions
- Multiple participants of the same type are supported (e.g., multiple informants)
- Display-only references used where actual resource conversion not yet implemented (e.g., RelatedPerson)

**Official IG Guidance**: [C-CDA on FHIR Participations](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participations.html)

---

## Moderate Issues

### 4. Attester Slicing Incomplete ✅ RESOLVED

**Issue**: Only legal attester was implemented. Professional and personal attester slices were missing.

**Impact**:
- Could not map `authenticator` (professional attester)
- Could not map certain `participant` elements (personal attester)
- Partial compliance with US Realm Header Profile

**Resolution** (Completed):
- ✅ Legal attester from `legalAuthenticator` → `Composition.attester` with mode="legal"
- ✅ Professional attester from `authenticator` → `Composition.attester` with mode="professional"
- ✅ Multiple authenticators supported (0..* cardinality per US Realm Header Profile)
- ✅ Both legal and professional attesters can coexist in same document
- ✅ Added comprehensive test coverage for all attester scenarios
- ℹ️  Personal attester slice (mode="personal") supported by profile but not commonly used in C-CDA documents

**Current Behavior**:
- `legalAuthenticator` → `Composition.attester` with mode="legal" ✅
- `authenticator` → `Composition.attester` with mode="professional" ✅
- Personal attestation → Supported by profile structure but no standard C-CDA source element

**Note on Personal Attestation**:
Per US Realm Header Profile, personal attestation (mode="personal") references Patient or RelatedPerson. In standard C-CDA documents, there is no common element representing a patient or family member attesting to document accuracy in a personal capacity. The `participant` element is used for support persons, not attestation. If needed in the future, this could be populated from specific participant elements with appropriate typeCode.

**Official IG Guidance**: [US Realm Header Profile - Attester Slicing](https://build.fhir.org/ig/HL7/ccda-on-fhir/StructureDefinition-US-Realm-Header.html)

---

### 5. Provenance Resource Not Generated 🟡

**Issue**: Complete author tracking via Provenance resources is not implemented.

**Impact**:
- Multiple authors only partially tracked
- Full audit trail not available
- Cannot distinguish original author from last editor

**Current Behavior**:
- First author time → Resource's `recordedDate`
- Last author → Resource's author/recorder reference
- Middle authors → Lost

**Workaround**:
- Extract author information from individual resources
- Track Practitioner resources created from authors

**Planned Fix**: Future version - Generate Provenance resources for complete author tracking

**Reference**: [FHIR Provenance](https://hl7.org/fhir/R4/provenance.html)

---

### 6. Medication Status Ambiguity 🟡 🤔

**Issue**: Unclear whether completed medications should map to `completed` or `active` status in FHIR.

**Background**:
- C-CDA "completed" can mean "patient finished the course" or "this was taken historically"
- FHIR MedicationRequest.status `completed` means "request fulfilled"
- FHIR MedicationRequest.status `active` often used for "medication the patient is/was on"

**Current Behavior**:
- C-CDA `completed` → FHIR `completed`
- C-CDA `active` → FHIR `active`

**Community Variance**:
- Some implementers map all historical medications to `active`
- Others use `completed` for finished courses
- No clear consensus in C-CDA on FHIR IG

**Recommendation**: Document your organization's policy in implementation guide

**Reference**: [HL7 C-CDA on FHIR Known Issues - Medications](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html#medications)

---

### 7. NullFlavor Handling Inconsistency 🟡

**Issue**: Some nullFlavor values map to data-absent-reason, others to specific codes, creating ambiguity.

**Examples**:
- NullFlavor="UNK" on allergy substance → Should create "unknown allergy" or use data-absent-reason?
- NullFlavor="NA" on observation value → data-absent-reason or omit observation?

**Current Behavior**:
- Most nullFlavors → data-absent-reason extension
- Context-specific handling for allergies, problems
- Inconsistent across different converters

**Impact**:
- Semantics may differ slightly across resource types
- Round-trip conversion may not preserve exact nullFlavor

**Workaround**: Review nullFlavor handling for your specific use case

**Reference**: [HL7 C-CDA on FHIR Known Issues - Null Flavors](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html#null-flavors)

---

### 8. Document-Level Status Codes 🟡 🤔

**Issue**: Unclear whether draft/preliminary status codes should be mapped for resources extracted from finalized documents.

**Background**:
- C-CDA documents are almost always status="completed" (finalized)
- Resources within may have different status (active, completed, etc.)
- Question: Can a "preliminary" medication appear in a "completed" document?

**Current Behavior**:
- Map C-CDA status codes directly regardless of document status
- Document status → Composition.status only

**Impact**:
- May create FHIR resources with statuses uncommon in document exchange
- Unclear if draft resources should appear in final documents

**Recommendation**: Validate that resource statuses are appropriate for document-based exchange

**Reference**: [HL7 C-CDA on FHIR Known Issues](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html)

---

## Minor Issues

### 9. No Known Allergies Representation 🟢

**Issue**: Multiple valid approaches for representing "no known allergies" - unclear which is preferred.

**Options**:
1. AllergyIntolerance with code 716186003 "No known allergy"
2. AllergyIntolerance with negated substance + verificationStatus="refuted"
3. List resource indicating absence of allergies
4. Composition section.emptyReason

**Current Behavior**: Uses approach #1 (AllergyIntolerance with negated code)

**Impact**: Minimal - all approaches are valid, but implementers may expect different patterns

**Reference**: [HL7 C-CDA on FHIR Known Issues - Absent Allergies](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html#absent-allergies)

---

### 10. Timezone Handling for Partial Dates 🟢

**Issue**: When C-CDA timestamp lacks timezone but includes time component, unclear how to infer timezone.

**Example**:
- C-CDA: `<time value="20230515143000"/>` (no timezone)
- FHIR requires timezone for dateTime precision > day

**Current Behavior**:
- Uses system timezone or UTC as default
- May not reflect actual timezone of event

**Workaround**:
- Configure timezone for facility/organization
- Use document metadata to infer timezone

**Impact**: Minimal - timestamps still accurately order events, though absolute time may be off by hours

---

### 11. Reference Range Multiple Interpretations 🟢

**Issue**: C-CDA allows multiple reference ranges with different interpretation codes, but FHIR expects "normal" ranges.

**Current Behavior**:
- Only maps reference range with interpretationCode="N" (normal)
- Other ranges (therapeutic, critical) are dropped

**Impact**:
- Loses therapeutic range information
- Loses critical value thresholds

**Workaround**: Use observation extensions for additional ranges

**Reference**: [CF-results.html](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html)

---

### 12. Contained Resources Not Supported 🟢

**Issue**: Implementation always creates top-level resources in Bundle, never uses contained resources.

**Impact**:
- Larger bundles (more resources)
- May not match some implementers' expectations for tightly-coupled data

**Current Behavior**: All resources are Bundle entries

**Workaround**: Post-process bundle to contain resources if needed

**Planned Fix**: Optional contained resource mode in future version

---

### 13. Section Narrative Not Propagated 🟢

**Issue**: C-CDA section text/narrative is not mapped to FHIR resource Narrative.

**Example**:
```xml
<section>
  <text>
    <table>
      <tbody>
        <tr><td>Penicillin</td><td>Hives</td></tr>
      </tbody>
    </table>
  </text>
  <entry>
    <!-- Structured allergy data -->
  </entry>
</section>
```

**Current Behavior**:
- Structured entry data → FHIR resource ✅
- Section text → Not mapped to resource ❌
- Section text → Remains in Composition.section.text ✅

**Impact**:
- Narrative text only visible in Composition, not in individual resources
- Resources lack human-readable narrative

**Workaround**: Access narrative from Composition.section.text

---

## Non-Standard Converters

### 14. DocumentReference Converter Beyond IG Scope 🟡

**Issue**: DocumentReference converter extends beyond official C-CDA on FHIR IG scope.

**Background**:
- Official IG focuses on Composition for document representation
- Our implementation also creates DocumentReference for additional use cases

**Current Behavior**: Creates both Composition and DocumentReference for C-CDA documents

**Impact**:
- Additional resource in bundle
- Not strictly necessary for compliance
- May confuse implementers expecting IG-compliant output only

**Status**: Documented as extension in compliance plan

---

### 15. Provenance Converter Beyond IG Scope 🟢

**Issue**: Provenance converter planned but not part of core C-CDA on FHIR IG.

**Background**: Official IG recommends Provenance but doesn't define required mappings

**Current Status**: Not yet implemented

**Impact**: None currently - future consideration

---

### 16. NoteActivity Converter Beyond IG Scope 🟢

**Issue**: NoteActivity converter planned but not part of official C-CDA on FHIR IG.

**Background**: Note Activity maps to DocumentReference per official IG, but we may extend this

**Current Status**: Documented in mapping guides

**Impact**: None - aligns with IG recommendations

---

## Edge Cases

### 17. Empty Sections Handling 🟢

**Issue**: How to represent C-CDA sections with no entries.

**Current Behavior**:
- Section included in Composition with no entries
- Uses section.emptyReason if nullFlavor present

**Impact**: Minimal

---

### 18. Duplicate Resource Deduplication 🟢

**Issue**: Same practitioner/organization appearing multiple times may create duplicate resources.

**Current Behavior**:
- ReferenceRegistry deduplicates based on identifier
- Works for most cases but may miss duplicates with different identifiers

**Impact**: Occasional duplicate resources in bundle

**Workaround**: Post-processing deduplication

---

### 19. Translation vs Original Code Preference 🟢

**Issue**: When C-CDA has both original code and translations, unclear which should be primary in FHIR.

**Current Behavior**:
- Original code → first coding
- Translations → additional codings

**Impact**: Minimal - all codes preserved, just order varies

---

## Reporting Issues

Found a new issue? Please report it:

1. **GitHub Issues**: [Create an issue](https://github.com/your-org/c-cda-to-fhir/issues)
2. **Include**:
   - Minimal C-CDA example demonstrating the issue
   - Expected FHIR output
   - Actual FHIR output
   - Relevant IG references

---

## References

- [HL7 C-CDA on FHIR Known Issues](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html)
- [C-CDA on FHIR Mapping Background](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingBackground.html)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [US Core Implementation Guide](http://hl7.org/fhir/us/core/)
