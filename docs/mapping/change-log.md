# Change Log: C-CDA to FHIR Mapping Implementation

This document tracks changes to the C-CDA to FHIR mapping implementation and documentation.

## Format

Each version entry includes:
- **Version number** and date
- **Added**: New features and mappings
- **Changed**: Modifications to existing mappings
- **Fixed**: Bug fixes and corrections
- **Documentation**: Documentation updates

---

## Version 0.2.0 (2025-12-16)

### Added

**Mapping Documentation**
- Added `10-notes.md`: Note Activity → DocumentReference mapping
- Added `11-social-history.md`: Social history observations → Observation/Patient extensions mapping
- Added `12-vital-signs.md`: Vital Signs → Observation mapping with special handling for blood pressure and pulse oximetry components
- Added `terminology-maps.md`: Comprehensive concept maps for all value set translations
- Added `known-issues.md`: Documentation of current limitations and known issues
- Added this change log

**Implementation Features**
- Legal authenticator mapping: ClinicalDocument.legalAuthenticator → Composition.attester with mode="legal"
- Practitioner extraction from legal authenticator
- Comprehensive test coverage for legal authenticator mapping including edge cases

**Planning Documentation**
- Added `c-cda-fhir-compliance-plan.md`: 6-week roadmap for achieving full C-CDA on FHIR IG compliance

### Changed

- Renamed `09-practitioner.md` → `09-participations.md` to align with official HL7 C-CDA on FHIR IG terminology

### Documentation

- Updated `00-overview.md` with references to new supplementary documentation
- All mapping documentation now matches official HL7 C-CDA on FHIR IG structure (12 clinical domain mappings + overview + terminology maps + change log + known issues)

---

## Version 0.1.0 (Initial Implementation)

### Added

**Core Converters**
- Patient converter: recordTarget/patientRole → Patient
- Composition converter: ClinicalDocument → Composition
- Condition converter: Problem Concern Act/Problem Observation → Condition
- AllergyIntolerance converter: Allergy Concern Act/Allergy Observation → AllergyIntolerance
- Observation converter: Result Observation → Observation
- DiagnosticReport converter: Result Organizer → DiagnosticReport
- Procedure converter: Procedure Activity → Procedure
- Immunization converter: Immunization Activity → Immunization
- MedicationRequest converter: Medication Activity → MedicationRequest
- Encounter converter: Encounter Activity → Encounter
- Practitioner converter: assignedEntity/assignedPerson → Practitioner
- PractitionerRole converter: assignedEntity with code → PractitionerRole
- Organization converter: representedOrganization → Organization
- Device converter: assignedAuthoringDevice → Device

**Base Infrastructure**
- BaseConverter abstract class with shared conversion utilities
- ReferenceRegistry for resource deduplication and reference management
- C-CDA model classes using fhir.resources library for FHIR R4B models
- Bundle creation with proper resource ordering
- OID to URI translation for common code systems
- Date/time conversion with precision preservation
- Identifier mapping with root/extension handling
- Name, address, and telecom mapping
- CodeableConcept and Coding conversion
- Quantity and Range conversion

**Validation**
- C-CDA schema validation using lxml
- Integration with official C-CDA schemas
- Basic FHIR resource validation

**Testing**
- Comprehensive integration test suite covering all converters
- Unit tests for base conversion utilities
- Test fixtures for common C-CDA patterns
- Helper functions for test data generation

**Mapping Documentation**
- `00-overview.md`: General mapping guidance, data type mappings, implementation considerations
- `01-patient.md`: Patient demographic mapping
- `02-condition.md`: Problem list and encounter diagnoses mapping
- `03-allergy-intolerance.md`: Allergy and intolerance mapping
- `04-observation.md`: Laboratory results, vital signs, and social history observations
- `05-procedure.md`: Procedure activity mapping
- `06-immunization.md`: Immunization activity mapping
- `07-medication-request.md`: Medication activity mapping
- `08-encounter.md`: Encounter activity mapping
- `09-practitioner.md`: Participation elements (author, performer, informant, etc.) mapping

### Implementation Notes

**Scope**
- Unidirectional mapping: C-CDA → FHIR only
- Based on HL7 C-CDA on FHIR Implementation Guide v2.0.0-ballot
- Targets FHIR R4B
- Focuses on C-CDA R2.1

**Architecture Decisions**
- Used Python with lxml for C-CDA parsing
- Used fhir.resources library for FHIR model generation
- Implemented reference registry pattern for resource deduplication
- Separated converters by FHIR resource type rather than C-CDA template
- Created comprehensive mapping documentation alongside implementation

**Known Limitations (at v0.1.0)**
- No FHIR → C-CDA reverse mapping
- Missing C-CDA on FHIR participant extensions (7 extensions)
- Custodian cardinality not enforced (should be 1..1)
- Subject cardinality not enforced (should be 1..1)
- No professional or personal attester slices (only legal)
- Limited support for contained resources
- No support for external document references
- No Provenance resource generation for complete author tracking
- DocumentReference, Provenance, and NoteActivity converters extend beyond official IG scope

---

## Planned Changes

See `c-cda-fhir-compliance-plan.md` for detailed roadmap.

### Version 0.3.0 (Planned)

**Critical Compliance Fixes**
- Implement Composition.custodian cardinality enforcement (1..1)
- Implement Composition.subject cardinality enforcement (1..1)

**Standard Extensions**
- Data Enterer extension (`http://hl7.org/fhir/ccda/StructureDefinition/DataEntererExtension`)
- Informant extension (`http://hl7.org/fhir/ccda/StructureDefinition/InformantExtension`)
- Information Recipient extension (`http://hl7.org/fhir/ccda/StructureDefinition/InformationRecipientExtension`)
- Participant extension (`http://hl7.org/fhir/ccda/StructureDefinition/ParticipantExtension`)
- Performer extension (`http://hl7.org/fhir/ccda/StructureDefinition/PerformerExtension`)
- Authorization extension (`http://hl7.org/fhir/ccda/StructureDefinition/AuthorizationExtension`)
- In Fulfillment Of Order extension (`http://hl7.org/fhir/ccda/StructureDefinition/InFulfillmentOfOrderExtension`)

**Attester Slicing**
- Professional attester (from authenticator)
- Personal attester (from participant with typeCode)

**Enhanced Testing**
- FHIR Validator integration for profile compliance
- Additional edge case coverage
- Performance benchmarking

### Future Versions

**FHIR → C-CDA Mapping**
- Reverse mapping implementation
- Template ID assignment logic
- Required element defaulting

**Advanced Features**
- Provenance resource generation
- Contained resource support
- External reference resolution
- Section narrative generation
- Advanced error handling and reporting

---

## Migration Guide

### From 0.1.0 to 0.2.0

**Breaking Changes**
- None

**Deprecations**
- None

**New Features**
- Legal authenticator is now mapped to Composition.attester
- Additional mapping documentation available for Notes, Social History, and Vital Signs

**Recommended Actions**
1. Review new mapping documentation for comprehensive guidance
2. Validate that legal authenticator mappings meet your requirements
3. Review compliance plan for upcoming changes in 0.3.0

---

## References

- [HL7 C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/)
- [HL7 C-CDA R2.1 Specification](http://www.hl7.org/implement/standards/product_brief.cfm?product_id=492)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [US Core Implementation Guide](http://hl7.org/fhir/us/core/)
