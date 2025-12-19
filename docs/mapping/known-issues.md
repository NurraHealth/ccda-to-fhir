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

### 2. Subject Cardinality Correctly Implemented ✅ RESOLVED

**Issue**: Implementation correctly handles `Composition.subject` per US Realm Header Profile cardinality 0..1 (optional).

**Impact**:
- Compliant FHIR output per profile specification
- Allows valid compositions without subject when recordTarget is absent

**Resolution** (Completed):
- ✅ Per US Realm Header Profile, `Composition.subject` has cardinality 0..1 (optional, not required)
- ✅ Composition converter creates subject when valid recordTarget exists
- ✅ Composition converter omits subject when recordTarget is absent or conversion fails (allowed per 0..1 cardinality)
- ✅ Added test coverage for both scenarios (`test_subject_present_when_recordTarget_exists`, `test_subject_absent_when_recordTarget_missing`)
- ✅ No ValueError raised for missing subject - follows profile specification

**Current Behavior**:
- When recordTarget exists and patient conversion succeeds: subject references the actual Patient resource ✅
- When recordTarget is missing: subject is omitted (allowed per 0..1 cardinality) ✅
- When patient conversion fails: subject is omitted (allowed per 0..1 cardinality) ✅
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

### 5. Provenance Resource Complete Author Tracking ✅ RESOLVED

**Issue**: Complete author tracking via Provenance resources is now fully implemented.

**Impact**:
- ✅ Multiple authors fully tracked in Provenance resources
- ✅ Complete audit trail available
- ✅ Can distinguish all authors and their temporal sequence
- ✅ Compliant with C-CDA on FHIR IG guidance

**Resolution** (Completed):
- ✅ ProvenanceConverter creates Provenance resources for all clinical resources with authors
- ✅ All authors tracked as Provenance.agent elements with proper types (author, performer, informant, etc.)
- ✅ Author time tracked in Provenance.recorded (earliest author time)
- ✅ Practitioner/Device/Organization references properly linked via agent.who and agent.onBehalfOf
- ✅ Comprehensive test coverage (20 unit tests + 37 integration tests)

**Current Behavior**:
- Resources with authors → Provenance resource created with all author information ✅
- First author time → Provenance.recorded ✅
- All authors → Provenance.agent[] array with complete information ✅
- Agent types properly mapped from C-CDA roles (AUT→author, PRF→performer, INF→informant, etc.) ✅
- Device authors → Provenance.agent.who references Device resource ✅
- Practitioner authors → Provenance.agent.who references Practitioner resource ✅
- Organization context → Provenance.agent.onBehalfOf references Organization ✅

**Official IG Guidance**:
- [FHIR Provenance](https://hl7.org/fhir/R4/provenance.html)
- [C-CDA on FHIR Known Issues - Provenance](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html)

---

### 6. Medication Status Correctly Implements Time-Aware Mapping ✅ RESOLVED

**Issue**: C-CDA "completed" status was ambiguous - could mean "prescription writing completed" or "medication course finished".

**Impact**:
- ✅ Standard-compliant FHIR output per C-CDA on FHIR IG
- ✅ Correctly distinguishes ongoing vs. finished medications
- ✅ Handles unbounded medications appropriately

**Resolution** (Completed):
- ✅ Per C-CDA on FHIR IG: C-CDA "completed" may mean "prescription writing completed" not "administration completed"
- ✅ Implementation now checks effectiveTime when statusCode="completed":
  - statusCode="completed" + future end date → FHIR `active` (prescription written but medication ongoing)
  - statusCode="completed" + no end date (unbounded) → FHIR `active` (ongoing medication)
  - statusCode="completed" + past end date → FHIR `completed` (medication course finished)
- ✅ Applied to both MedicationRequest and MedicationStatement converters
- ✅ Added comprehensive test coverage for all scenarios

**Current Behavior**:
- C-CDA `active` → FHIR `active` ✅
- C-CDA `completed` with past dates → FHIR `completed` ✅
- C-CDA `completed` with future dates or no end date → FHIR `active` ✅
- C-CDA `nullified` → FHIR `entered-in-error` ✅
- All other status codes → standard 1:1 mapping per ConceptMap ✅

**Official IG Guidance**:
- [C-CDA on FHIR Medications Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-medications.html)
- [FHIR MedicationRequest Status ValueSet](https://hl7.org/fhir/R4/valueset-medicationrequest-status.html)

---

### 7. NullFlavor Handling Now Standard-Compliant ✅ RESOLVED

**Issue**: nullFlavor handling was inconsistent across converters, with ad-hoc implementations creating ambiguity.

**Impact**:
- ✅ Standardized nullFlavor mapping per official C-CDA on FHIR IG ConceptMap
- ✅ Consistent data-absent-reason extension usage across all converters
- ✅ Clear separation between context-specific handling (allergies) and standard mapping

**Resolution** (Completed):
- ✅ Added official `NULL_FLAVOR_TO_DATA_ABSENT_REASON` mapping in constants.py per ConceptMap CF-NullFlavorDataAbsentReason
- ✅ Created centralized helper methods in BaseConverter:
  - `create_data_absent_reason_extension()` - creates FHIR extension from nullFlavor
  - `map_null_flavor_to_data_absent_reason()` - maps nullFlavor code to data-absent-reason code
- ✅ Updated all converters to use centralized approach:
  - Condition converter: Unknown abatement dates
  - Procedure converter: Missing effectiveTime
  - Immunization converter: Missing primarySource
  - Note Activity converter: Missing content
- ✅ Maintained context-specific handling where appropriate:
  - AllergyIntolerance: negated concepts for "no known allergies" (per IG guidance)
  - Composition sections: nullFlavor → emptyReason (different use case)

**Current Behavior**:
- Element-level nullFlavor → data-absent-reason extension (per CF-NullFlavorDataAbsentReason ConceptMap)
  - UNK → "unknown", ASKU → "asked-unknown", NAV → "temp-unknown", etc.
- Section-level nullFlavor → emptyReason (custom mapping for Composition sections)
- Context-specific: Allergy negations use negated concept codes (NO_KNOWN_ALLERGY, etc.)
- Per US Core: Required elements use data-absent-reason; optional elements omitted when null

**Official IG Guidance**:
- [CF-NullFlavorDataAbsentReason ConceptMap](https://build.fhir.org/ig/HL7/ccda-on-fhir/ConceptMap-CF-NullFlavorDataAbsentReason.html)
- [FHIR data-absent-reason Extension](http://hl7.org/fhir/R4/extension-data-absent-reason.html)
- [C-CDA on FHIR Mapping Issues - Null Flavors](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingIssues.html#null-flavors)

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
