# C-CDA on FHIR Compliance Implementation Plan

**Status**: Planning
**Created**: 2025-12-16
**Priority**: High - Standards Compliance

---

## Executive Summary

This document outlines a comprehensive plan to achieve 100% compliance with the [HL7 C-CDA on FHIR Implementation Guide v2.0.0](https://build.fhir.org/ig/HL7/ccda-on-fhir/). Our analysis identified critical gaps in document-level converters, particularly the Composition resource which is missing required C-CDA on FHIR extensions and proper cardinality enforcement.

**Current State**: 5/9 converters fully compliant, 1/9 partially compliant, 3/9 non-standard extensions
**Target State**: 100% compliance with official HL7 C-CDA on FHIR specification

---

## Table of Contents

1. [Critical Compliance Fixes](#1-critical-compliance-fixes)
2. [Standard Extensions Implementation](#2-standard-extensions-implementation)
3. [Non-Standard Converter Documentation](#3-non-standard-converter-documentation)
4. [Testing & Validation](#4-testing--validation)
5. [Documentation Updates](#5-documentation-updates)
6. [Timeline & Dependencies](#6-timeline--dependencies)

---

## 1. Critical Compliance Fixes

### 1.1 Composition Custodian Cardinality Enforcement

**Priority**: CRITICAL
**Spec Reference**: [CCDA-on-FHIR-US-Realm-Header](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
**Cardinality**: 1..1 (REQUIRED)
**Current State**: Optional (0..1)
**File**: `ccda_to_fhir/converters/composition.py:156-159`

#### Issue Description

The C-CDA on FHIR US Realm Header profile mandates that Composition.custodian is REQUIRED (1..1 cardinality). Our current implementation treats it as optional.

**Current Code (Lines 156-159):**
```python
# Custodian (optional) - organization maintaining the composition
if clinical_document.custodian:
    custodian_ref = self._create_custodian_reference(clinical_document.custodian)
    if custodian_ref:
        composition["custodian"] = custodian_ref
```

#### Implementation Steps

**Step 1.1.1**: Modify custodian extraction to enforce presence
- **File**: `ccda_to_fhir/converters/composition.py`
- **Lines**: 156-159
- **Action**: Change from optional to required with fallback

```python
# Custodian - REQUIRED (1..1) - organization maintaining the composition
# Per C-CDA on FHIR US Realm Header: http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html
if clinical_document.custodian:
    custodian_ref = self._create_custodian_reference(clinical_document.custodian)
    if custodian_ref:
        composition["custodian"] = custodian_ref
    else:
        # Fallback if extraction fails
        composition["custodian"] = {"display": "Unknown Custodian Organization"}
else:
    # C-CDA requires custodian, but if missing use placeholder to maintain FHIR validity
    logger.warning("Missing required custodian in C-CDA document")
    composition["custodian"] = {"display": "Unknown Custodian Organization"}
```

**Step 1.1.2**: Update ClinicalDocument validation
- **File**: `ccda_to_fhir/ccda/models/clinical_document.py`
- **Lines**: 546-550
- **Action**: Verify validator already enforces custodian presence (it does at line 546-550)
- **Note**: C-CDA validation already enforces this; we're ensuring FHIR output is also compliant

**Step 1.1.3**: Add test for missing custodian handling
- **File**: `tests/integration/test_composition.py`
- **Test Name**: `test_custodian_required_with_fallback`
- **Action**: Create test that verifies fallback behavior

```python
def test_custodian_required_with_fallback(self) -> None:
    """Test that custodian is always present even if C-CDA is malformed."""
    # Note: This test is theoretical - valid C-CDA always has custodian
    # But we should handle edge cases gracefully
    ccda_doc = wrap_in_ccda_document("", custodian=None)
    bundle = convert_document(ccda_doc)

    composition = _find_resource_in_bundle(bundle, "Composition")
    assert composition is not None
    # Should have custodian field even with fallback
    assert "custodian" in composition
```

**References**:
- [FHIR Composition.custodian](http://hl7.org/fhir/R4/composition-definitions.html#Composition.custodian)
- [C-CDA US Realm Header](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
- [C-CDA Custodian Requirements](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=492)

---

### 1.2 Composition Subject Cardinality Enforcement

**Priority**: CRITICAL
**Spec Reference**: [CCDA-on-FHIR-US-Realm-Header](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
**Cardinality**: 1..1 (REQUIRED)
**Current State**: "SHOULD be present" (treated as optional)
**File**: `ccda_to_fhir/converters/composition.py:112-115`

#### Issue Description

The C-CDA on FHIR US Realm Header requires Composition.subject with cardinality 1..1. Current code comment says "SHOULD be present" which is incorrect per spec.

**Current Code (Lines 112-115):**
```python
# Subject - patient reference (SHOULD be present)
if clinical_document.record_target and len(clinical_document.record_target) > 0:
    subject_ref = self._create_subject_reference(clinical_document.record_target[0])
    if subject_ref:
        composition["subject"] = subject_ref
```

#### Implementation Steps

**Step 1.2.1**: Update subject extraction to enforce presence
- **File**: `ccda_to_fhir/converters/composition.py`
- **Lines**: 112-121
- **Action**: Add mandatory subject with fallback

```python
# Subject - patient reference REQUIRED (1..1)
# Per C-CDA on FHIR US Realm Header: http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html
if clinical_document.record_target and len(clinical_document.record_target) > 0:
    subject_ref = self._create_subject_reference(clinical_document.record_target[0])
    if subject_ref:
        composition["subject"] = subject_ref
    else:
        # Fallback if reference creation fails
        logger.warning("Failed to create patient reference, using placeholder")
        composition["subject"] = {"reference": "Patient/unknown"}
else:
    # C-CDA requires recordTarget, but if missing use placeholder
    logger.error("Missing required recordTarget in C-CDA document")
    composition["subject"] = {"reference": "Patient/unknown"}
```

**Step 1.2.2**: Update `_create_subject_reference` to be more robust
- **File**: `ccda_to_fhir/converters/composition.py`
- **Lines**: 220-233
- **Current Issue**: Returns placeholder reference, should generate from patient ID if available

```python
def _create_subject_reference(self, record_target) -> JSONObject:
    """Create a reference to the patient (subject).

    Args:
        record_target: RecordTarget element from clinical document

    Returns:
        FHIR Reference (never None - always returns at least placeholder)
    """
    if not record_target or not record_target.patient_role:
        return {"reference": "Patient/unknown"}

    # Generate patient ID from identifiers if available
    patient_role = record_target.patient_role
    if patient_role.id:
        # Use first identifier to generate ID
        patient_id = self._generate_patient_id(patient_role.id)
        return {"reference": f"Patient/{patient_id}"}

    # Fallback to placeholder
    return {"reference": "Patient/unknown"}

def _generate_patient_id(self, identifiers: list[II]) -> str:
    """Generate patient ID from C-CDA identifiers.

    Prefers MRN or SSN, falls back to first available identifier.
    """
    from ccda_to_fhir.constants import CodeSystemOIDs

    # Prefer MRN (Medical Record Number)
    for identifier in identifiers:
        if identifier.extension and identifier.root:
            # Check for common MRN OIDs or use extension
            return identifier.extension.replace(" ", "-").replace(".", "-")

    return "unknown"
```

**Step 1.2.3**: Add tests for subject enforcement
- **File**: `tests/integration/test_composition.py`
- **Tests**:
  - `test_subject_required`
  - `test_subject_from_patient_id`

**References**:
- [FHIR Composition.subject](http://hl7.org/fhir/R4/composition-definitions.html#Composition.subject)
- [C-CDA recordTarget](https://hl7.org/cda/stds/ccda/draft1/StructureDefinition-2.16.840.1.113883.10.20.22.1.1.html)

---

## 2. Standard Extensions Implementation

### 2.1 C-CDA on FHIR Participant Extensions

**Priority**: HIGH
**Spec Reference**: [CCDA-on-FHIR-US-Realm-Header Extensions](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
**Required Extensions**: 7 total
**Current State**: 0/7 implemented

#### Overview

The C-CDA on FHIR US Realm Header profile defines 7 required extensions to capture C-CDA participant information that doesn't map directly to Composition base elements:

1. **Data Enterer** (`dataEnterer`)
2. **Informant** (`informant`)
3. **Information Recipient** (`informationRecipient`)
4. **Participant** (`participant`)
5. **Performer** (`performer`)
6. **Authorization** (`authorization`)
7. **In Fulfillment Of Order** (`inFulfillmentOf`)

---

### 2.1.1 Data Enterer Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer`
**C-CDA Element**: `ClinicalDocument/dataEnterer`
**Type**: Extension with nested sub-extensions
**Cardinality**: 0..1

#### Structure

```
Composition.extension:data-enterer
├── url: "http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer"
├── extension[0]: time
│   ├── url: "time"
│   └── valueDateTime: converted from dataEnterer/time/@value
└── extension[1]: party
    ├── url: "party"
    └── valueReference: Reference(Practitioner)
```

#### Implementation Steps

**Step 2.1.1.1**: Create extension extraction method
- **File**: `ccda_to_fhir/converters/composition.py`
- **Location**: After `_extract_attester` method (~line 400)
- **Method**: `_extract_data_enterer_extension`

```python
def _extract_data_enterer_extension(
    self, data_enterer: DataEnterer
) -> JSONObject | None:
    """Extract Data Enterer extension from C-CDA dataEnterer.

    Maps to: http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer

    Args:
        data_enterer: C-CDA DataEnterer element

    Returns:
        FHIR extension object or None
    """
    if not data_enterer:
        return None

    extension: JSONObject = {
        "url": "http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer",
        "extension": []
    }

    # Time sub-extension
    if data_enterer.time and data_enterer.time.value:
        time_str = self.convert_date(data_enterer.time.value)
        if time_str:
            extension["extension"].append({
                "url": "time",
                "valueDateTime": time_str
            })

    # Party sub-extension (Reference to Practitioner)
    if data_enterer.assigned_entity and data_enterer.assigned_entity.id:
        practitioner_id = self._generate_practitioner_id(data_enterer.assigned_entity.id)
        if practitioner_id:
            extension["extension"].append({
                "url": "party",
                "valueReference": {
                    "reference": f"Practitioner/{practitioner_id}"
                }
            })

    # Only return if we have at least one sub-extension
    if extension["extension"]:
        return extension

    return None
```

**Step 2.1.1.2**: Add data enterer extraction to convert()
- **File**: `ccda_to_fhir/converters/composition.py`
- **Location**: After attester extraction (~line 94)

```python
# Extensions array for C-CDA on FHIR participant extensions
extensions = []

# Data Enterer extension
if clinical_document.data_enterer:
    data_enterer_ext = self._extract_data_enterer_extension(clinical_document.data_enterer)
    if data_enterer_ext:
        extensions.append(data_enterer_ext)

# Add all extensions to composition if any exist
if extensions:
    composition["extension"] = extensions
```

**Step 2.1.1.3**: Extract data enterer practitioner in convert.py
- **File**: `ccda_to_fhir/convert.py`
- **Location**: After legal_authenticator extraction (~line 382)

```python
# Convert Practitioner from dataEnterer
if ccda_doc.data_enterer and ccda_doc.data_enterer.assigned_entity:
    try:
        practitioner = self.practitioner_converter.convert(
            ccda_doc.data_enterer.assigned_entity
        )
        if self._validate_resource(practitioner):
            resources.append(practitioner)
            self.reference_registry.register_resource(practitioner)
    except Exception as e:
        logger.warning(
            f"Error converting data enterer practitioner: {e}",
            exc_info=True,
            extra={"error_type": type(e).__name__}
        )
```

**Step 2.1.1.4**: Add tests
- **File**: `tests/integration/test_composition.py`
- **Test**: `test_data_enterer_extension`

```python
def test_data_enterer_extension(self) -> None:
    """Test that dataEnterer maps to Data-Enterer extension."""
    ccda_doc = wrap_in_ccda_document(
        "",
        data_enterer="""
        <dataEnterer>
            <time value="20200315120000-0500"/>
            <assignedEntity>
                <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
                <assignedPerson>
                    <name>
                        <given>Ellen</given>
                        <family>Enter</family>
                    </name>
                </assignedPerson>
            </assignedEntity>
        </dataEnterer>
        """
    )
    bundle = convert_document(ccda_doc)

    composition = _find_resource_in_bundle(bundle, "Composition")
    assert composition is not None

    # Should have extension array
    assert "extension" in composition

    # Find Data Enterer extension
    data_enterer_ext = next(
        (ext for ext in composition["extension"]
         if ext.get("url") == "http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer"),
        None
    )
    assert data_enterer_ext is not None

    # Should have sub-extensions
    sub_extensions = {ext["url"]: ext for ext in data_enterer_ext["extension"]}

    # Verify time
    assert "time" in sub_extensions
    assert sub_extensions["time"]["valueDateTime"] == "2020-03-15T12:00:00-05:00"

    # Verify party reference
    assert "party" in sub_extensions
    assert sub_extensions["party"]["valueReference"]["reference"].startswith("Practitioner/")
```

**Step 2.1.1.5**: Update test helper to support dataEnterer
- **File**: `tests/integration/conftest.py`
- **Function**: `wrap_in_ccda_document`
- **Add parameter**: `data_enterer: str | None = None`

**References**:
- [C-CDA DataEnterer](https://hl7.org/cda/stds/ccda/draft1/StructureDefinition-DataEnterer.html)
- [CCDA-on-FHIR-Data-Enterer Extension](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-Data-Enterer.html)

---

### 2.1.2 Informant Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Informant`
**C-CDA Element**: `ClinicalDocument/informant`
**Type**: Extension with nested sub-extensions
**Cardinality**: 0..*

#### Structure

C-CDA informant can be either a healthcare provider (assignedEntity) or a related person (relatedEntity):

```
Composition.extension:informant
├── url: "http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Informant"
└── extension[0]: party
    ├── url: "party"
    └── valueReference: Reference(Practitioner | RelatedPerson | Patient)
```

#### Implementation Steps

**Step 2.1.2.1**: Create extension extraction method
- **File**: `ccda_to_fhir/converters/composition.py`
- **Method**: `_extract_informant_extensions`

```python
def _extract_informant_extensions(
    self, informants: list[Informant]
) -> list[JSONObject]:
    """Extract Informant extensions from C-CDA informants.

    Maps to: http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Informant

    Informants can be:
    - Healthcare providers (assignedEntity) → Practitioner
    - Related persons (relatedEntity) → RelatedPerson
    - Patient themselves (relatedEntity with code) → Patient

    Args:
        informants: List of C-CDA Informant elements

    Returns:
        List of FHIR extension objects
    """
    extensions = []

    if not informants:
        return extensions

    for informant in informants:
        extension: JSONObject = {
            "url": "http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Informant",
            "extension": []
        }

        # Healthcare provider informant (assignedEntity)
        if informant.assigned_entity and informant.assigned_entity.id:
            practitioner_id = self._generate_practitioner_id(informant.assigned_entity.id)
            if practitioner_id:
                extension["extension"].append({
                    "url": "party",
                    "valueReference": {
                        "reference": f"Practitioner/{practitioner_id}"
                    }
                })

        # Related person informant (relatedEntity)
        elif informant.related_entity:
            # For MVP, create display-only reference
            # TODO: Implement full RelatedPerson resource creation
            display = self._format_related_entity_display(informant.related_entity)
            if display:
                extension["extension"].append({
                    "url": "party",
                    "valueReference": {
                        "display": display
                    }
                })

        # Only add if we have at least one sub-extension
        if extension["extension"]:
            extensions.append(extension)

    return extensions

def _format_related_entity_display(self, related_entity) -> str | None:
    """Format related entity for display reference.

    Args:
        related_entity: RelatedEntity element

    Returns:
        Formatted display string or None
    """
    if not related_entity:
        return None

    # Try to get name
    if related_entity.related_person and related_entity.related_person.name:
        name = related_entity.related_person.name[0]
        display = self._format_name_for_display(name)

        # Add relationship if available
        if related_entity.code and related_entity.code.display_name:
            display = f"{display} ({related_entity.code.display_name})"

        return display

    return None
```

**Step 2.1.2.2**: Add to composition convert()
```python
# Informant extensions
if clinical_document.informant:
    informant_exts = self._extract_informant_extensions(clinical_document.informant)
    extensions.extend(informant_exts)
```

**Step 2.1.2.3**: Extract informant practitioners in convert.py
```python
# Convert Practitioners from informants
if ccda_doc.informant:
    for informant in ccda_doc.informant:
        if informant.assigned_entity:
            try:
                practitioner = self.practitioner_converter.convert(informant.assigned_entity)
                if self._validate_resource(practitioner):
                    resources.append(practitioner)
                    self.reference_registry.register_resource(practitioner)
            except Exception as e:
                logger.warning(
                    f"Error converting informant practitioner: {e}",
                    exc_info=True
                )
```

**Step 2.1.2.4**: Add tests for both informant types

**References**:
- [C-CDA Informant](https://hl7.org/cda/stds/ccda/draft1/StructureDefinition-Informant.html)
- [CCDA-on-FHIR-Informant Extension](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-Informant.html)

---

### 2.1.3 Information Recipient Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Information-Recipient`
**C-CDA Element**: `ClinicalDocument/informationRecipient`
**Cardinality**: 0..*

#### Implementation Steps

**Step 2.1.3.1**: Create extension extraction method
```python
def _extract_information_recipient_extensions(
    self, recipients: list[InformationRecipient]
) -> list[JSONObject]:
    """Extract Information Recipient extensions.

    Maps to: http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Information-Recipient
    """
    # Implementation similar to informant
    # Maps to Practitioner or Organization references
```

---

### 2.1.4 Participant Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Participant`
**C-CDA Element**: `ClinicalDocument/participant`
**Cardinality**: 0..*

Captures support persons, insurance providers, and other participants.

---

### 2.1.5 Performer Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Performer`
**C-CDA Element**: `ClinicalDocument/documentationOf/serviceEvent/performer`
**Cardinality**: 0..*

Note: This is different from entry-level performers (Procedure.performer, etc.)

---

### 2.1.6 Authorization Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Authorization`
**C-CDA Element**: `ClinicalDocument/authorization`
**Cardinality**: 0..*

Maps consent authorizations.

---

### 2.1.7 In Fulfillment Of Order Extension

**Extension URL**: `http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-In-Fulfillment-Of`
**C-CDA Element**: `ClinicalDocument/inFulfillmentOf`
**Cardinality**: 0..*

Maps order references that the document fulfills.

---

### 2.2 Attester Slices Implementation

**Priority**: MEDIUM
**Spec Reference**: [CCDA-on-FHIR-US-Realm-Header Attesters](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
**Required Slices**: 3 total
**Current State**: 1/3 implemented (legal only)

#### Overview

C-CDA on FHIR defines three attester slices:
1. **Legal Attester** (mode="legal") - ✅ Already implemented
2. **Professional Attester** (mode="professional") - ❌ Not implemented
3. **Personal Attester** (mode="personal") - ❌ Not implemented

#### Implementation Steps

**Step 2.2.1**: Add authenticator → professional attester mapping
- **File**: `ccda_to_fhir/converters/composition.py`
- **C-CDA Element**: `ClinicalDocument/authenticator` (can be 0..*)

```python
# Professional attesters from authenticators
if clinical_document.authenticator:
    for authenticator in clinical_document.authenticator:
        attester = self._extract_professional_attester(authenticator)
        if attester:
            if "attester" not in composition:
                composition["attester"] = []
            composition["attester"].append(attester)

def _extract_professional_attester(self, authenticator: Authenticator) -> JSONObject | None:
    """Extract professional attester from C-CDA authenticator.

    Args:
        authenticator: C-CDA Authenticator element

    Returns:
        FHIR attester with mode="professional"
    """
    if not authenticator:
        return None

    attester: JSONObject = {
        "mode": "professional"
    }

    # Extract time
    if authenticator.time and authenticator.time.value:
        time_str = self.convert_date(authenticator.time.value)
        if time_str:
            attester["time"] = time_str

    # Extract party reference
    if authenticator.assigned_entity and authenticator.assigned_entity.id:
        practitioner_id = self._generate_practitioner_id(authenticator.assigned_entity.id)
        if practitioner_id:
            attester["party"] = {
                "reference": f"Practitioner/{practitioner_id}"
            }

    return attester
```

**Step 2.2.2**: Extract authenticator practitioners in convert.py

**Step 2.2.3**: Add tests for professional attesters

**Step 2.2.4**: Document personal attester slice
- Note: C-CDA doesn't have a direct "personal attester" element
- May need to map from specific participant types or leave unimplemented
- Document decision in mapping docs

---

## 3. Non-Standard Converter Documentation

### 3.1 Create Mapping Documentation for Non-Standard Converters

**Priority**: MEDIUM
**Purpose**: Clearly identify and document converters that extend beyond official C-CDA on FHIR IG

#### Converters Requiring Documentation

1. **DocumentReference** - Not in official IG
2. **Provenance** - Mentioned but no guidance
3. **NoteActivity** - Not in official IG

---

### 3.1.1 DocumentReference Converter Documentation

**File**: Create `docs/mapping/10-document-reference.md`

**Content Outline**:
```markdown
# DocumentReference Mapping: C-CDA ClinicalDocument → FHIR DocumentReference

⚠️ **NON-STANDARD EXTENSION**: This mapping is NOT part of the official [HL7 C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/).

## Rationale

While the C-CDA on FHIR IG uses Composition for document metadata, some systems prefer DocumentReference for:
- Consistency with FHIR document reference patterns
- Integration with document management systems
- US Core DocumentReference compliance

## Official C-CDA on FHIR Pattern

Per the official IG, C-CDA documents should use:
- **Composition**: Primary document metadata and structure
- **Bundle**: Document packaging (type="document")
- Composition is sufficient for most use cases

## Our Extension

This converter creates a DocumentReference alongside Composition to support:
- Systems that query for documents via DocumentReference
- Workflows expecting DocumentReference.content.attachment
- US Core DocumentReference profile compliance

## Mapping Details

[Include full mapping table]

## Usage Guidance

Consider using this converter when:
- Integrating with document management systems expecting DocumentReference
- Supporting US Core DocumentReference queries
- Need base64-encoded original XML in attachment

Consider NOT using when:
- Strict C-CDA on FHIR IG compliance required
- Storage/bandwidth constraints (avoid duplication)

## Configuration

[Document how to enable/disable this converter]
```

---

### 3.1.2 Provenance Converter Documentation

**File**: Create `docs/mapping/11-provenance.md`

**Content Outline**:
```markdown
# Provenance Mapping: C-CDA Author → FHIR Provenance

⚠️ **EXTENSION WITHOUT OFFICIAL GUIDANCE**: The C-CDA on FHIR IG explicitly states it "does not provide definitive CDA ↔ FHIR guidance on when resource attributes vs. dedicated Provenance resources should be used."

## C-CDA on FHIR Official Stance

Per the [mapping guidance](https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html):
> This publication does not provide definitive CDA ↔ FHIR guidance on when resource attributes vs. dedicated Provenance resources should be used.

## Our Implementation Decision

We create Provenance resources for detailed author tracking in addition to resource-level .author fields.

## When Provenance is Created

[Document exact conditions]

## When to Use Resource.author Instead

[Provide guidance]

## Configuration

[How to enable/disable provenance generation]
```

---

### 3.1.3 NoteActivity Converter Documentation

**File**: Create `docs/mapping/12-note-activity.md`

**Content Outline**:
```markdown
# Note Activity Mapping: C-CDA Note Activity → FHIR DocumentReference

⚠️ **NON-STANDARD EXTENSION**: This mapping is NOT part of the official C-CDA on FHIR IG.

## C-CDA Template

Template ID: 2.16.840.1.113883.10.20.22.4.202 (Note Activity)

## Standard Pattern vs Our Extension

**Standard C-CDA on FHIR Pattern**: Notes remain embedded in Composition.section.text

**Our Extension**: Extract notes as separate DocumentReference resources

## Rationale

Creating DocumentReference for notes supports:
- US Core Clinical Notes requirements
- Granular note queries and versioning
- Note-level provenance tracking

## Trade-offs

**Advantages**:
- Better note lifecycle management
- US Core compliance
- Structured note metadata

**Disadvantages**:
- Deviates from C-CDA on FHIR pattern
- Potential duplication (note in both section.text and DocumentReference)
- May confuse consumers expecting standard pattern

## Usage Guidance

[When to use this converter]
```

---

### 3.2 Add Configuration Options

**File**: Create `ccda_to_fhir/config.py`

**Purpose**: Allow users to enable/disable non-standard converters

```python
"""C-CDA to FHIR conversion configuration."""

from dataclasses import dataclass


@dataclass
class ConversionConfig:
    """Configuration for C-CDA to FHIR conversion.

    Controls which converters are enabled and conversion behavior.
    """

    # Standard converters (always enabled)
    enable_standard_converters: bool = True

    # Non-standard extensions (can be disabled for strict compliance)
    enable_document_reference: bool = True
    enable_provenance: bool = True
    enable_note_activity: bool = True

    # Compliance options
    enforce_ccda_on_fhir_compliance: bool = False  # Strict mode

    # Validation options
    validate_resources: bool = True
    fail_on_validation_error: bool = False

    def is_strict_mode(self) -> bool:
        """Check if running in strict C-CDA on FHIR compliance mode."""
        return self.enforce_ccda_on_fhir_compliance

    def get_enabled_extensions(self) -> list[str]:
        """Get list of enabled non-standard converters."""
        extensions = []
        if self.enable_document_reference:
            extensions.append("DocumentReference")
        if self.enable_provenance:
            extensions.append("Provenance")
        if self.enable_note_activity:
            extensions.append("NoteActivity")
        return extensions


# Default configuration
DEFAULT_CONFIG = ConversionConfig()

# Strict C-CDA on FHIR compliance configuration
STRICT_COMPLIANCE_CONFIG = ConversionConfig(
    enable_document_reference=False,
    enable_provenance=False,
    enable_note_activity=False,
    enforce_ccda_on_fhir_compliance=True,
    fail_on_validation_error=True
)
```

**Integration**:
- Update `convert.py` to accept `config: ConversionConfig` parameter
- Skip non-standard converters when disabled
- Add CLI flag: `--strict` to use STRICT_COMPLIANCE_CONFIG

---

## 4. Testing & Validation

### 4.1 Compliance Test Suite

**File**: Create `tests/compliance/test_ccda_on_fhir_compliance.py`

**Purpose**: Dedicated tests verifying C-CDA on FHIR IG compliance

```python
"""C-CDA on FHIR Implementation Guide compliance tests.

These tests verify our implementation matches the official HL7 C-CDA on FHIR IG.
Reference: https://build.fhir.org/ig/HL7/ccda-on-fhir/
"""

import pytest
from ccda_to_fhir.convert import convert_document
from ccda_to_fhir.config import STRICT_COMPLIANCE_CONFIG


class TestCompositionCompliance:
    """Test Composition resource compliance with C-CDA on FHIR US Realm Header."""

    def test_custodian_required_cardinality(self):
        """Verify Composition.custodian has 1..1 cardinality."""
        # Test implementation

    def test_subject_required_cardinality(self):
        """Verify Composition.subject has 1..1 cardinality."""
        # Test implementation

    def test_data_enterer_extension(self):
        """Verify Data-Enterer extension structure."""
        # Test implementation

    def test_informant_extension(self):
        """Verify Informant extension structure."""
        # Test implementation

    # ... more extension tests

    def test_legal_attester_mode(self):
        """Verify legal attester has mode='legal'."""
        # Test implementation

    def test_professional_attester_mode(self):
        """Verify professional attester has mode='professional'."""
        # Test implementation


class TestStrictModeCompliance:
    """Test strict C-CDA on FHIR compliance mode."""

    def test_no_non_standard_resources_in_strict_mode(self):
        """Verify non-standard resources not created in strict mode."""
        ccda_doc = wrap_in_ccda_document("")
        bundle = convert_document(ccda_doc, config=STRICT_COMPLIANCE_CONFIG)

        # Should NOT have DocumentReference (non-standard)
        doc_ref = _find_resource_in_bundle(bundle, "DocumentReference")
        assert doc_ref is None

        # Should NOT have Provenance (unclear guidance)
        provenance = _find_resource_in_bundle(bundle, "Provenance")
        assert provenance is None

    def test_composition_extensions_present(self):
        """Verify all required C-CDA on FHIR extensions present."""
        # Test implementation
```

---

### 4.2 FHIR Validator Integration

**Priority**: HIGH
**Purpose**: Use official FHIR validator to verify output

#### Implementation Steps

**Step 4.2.1**: Add FHIR validator dependency
```bash
# Add to pyproject.toml
fhir-validator = "^0.2.0"  # Or use Java-based validator
```

**Step 4.2.2**: Create validation helper
**File**: Create `ccda_to_fhir/validation.py`

```python
"""FHIR resource validation using official validator."""

import subprocess
import json
from pathlib import Path


def validate_against_profile(
    resource: dict,
    profile_url: str,
    validator_jar: Path | None = None
) -> tuple[bool, list[str]]:
    """Validate FHIR resource against a profile.

    Uses official HL7 FHIR Validator (Java-based).
    Download from: https://github.com/hapifhir/org.hl7.fhir.core/releases

    Args:
        resource: FHIR resource as dict
        profile_url: Profile URL to validate against
        validator_jar: Path to validator JAR file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    # Implementation using subprocess to call Java validator
```

**Step 4.2.3**: Add validation tests
```python
def test_composition_validates_against_us_realm_header():
    """Verify Composition validates against US Realm Header profile."""
    ccda_doc = wrap_in_ccda_document("")
    bundle = convert_document(ccda_doc)
    composition = _find_resource_in_bundle(bundle, "Composition")

    is_valid, errors = validate_against_profile(
        composition,
        "http://hl7.org/fhir/us/ccda/StructureDefinition/CCDA-on-FHIR-US-Realm-Header"
    )

    assert is_valid, f"Validation errors: {errors}"
```

---

### 4.3 Test Data Coverage

**File**: Create test data for all C-CDA participant types

**Test Files to Create**:
1. `tests/fixtures/ccda/full_header_all_participants.xml` - Complete C-CDA with all participant types
2. `tests/fixtures/ccda/minimal_compliant.xml` - Minimal C-CDA meeting all required fields
3. `tests/fixtures/ccda/edge_cases/` - Directory with edge case documents

---

## 5. Documentation Updates

### 5.1 Update Main Mapping Documentation

**File**: `docs/mapping/00-overview.md`

**Additions**:
```markdown
## Compliance with C-CDA on FHIR

This library implements the [HL7 C-CDA on FHIR Implementation Guide v2.0.0](https://build.fhir.org/ig/HL7/ccda-on-fhir/).

### Standard Mappings

The following mappings are part of the official C-CDA on FHIR specification:

1. Patient (01-patient.md) ✅
2. Problems/Conditions (02-condition.md) ✅
3. Allergies (03-allergy-intolerance.md) ✅
[... list all standard mappings]

### Non-Standard Extensions

The following converters are **NOT** part of the official HL7 C-CDA on FHIR IG and represent our extensions:

1. DocumentReference (10-document-reference.md) ⚠️ NON-STANDARD
2. Provenance (11-provenance.md) ⚠️ UNCLEAR GUIDANCE
3. NoteActivity (12-note-activity.md) ⚠️ NON-STANDARD

These can be disabled using configuration options for strict C-CDA on FHIR compliance.
```

---

### 5.2 Create Compliance Documentation

**File**: Create `docs/ccda-on-fhir-compliance.md`

**Content**:
```markdown
# C-CDA on FHIR Implementation Guide Compliance

## Overview

This document describes our adherence to the [HL7 C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/).

## Compliance Status

### Fully Compliant Converters

| Converter | Spec Reference | Status |
|-----------|---------------|---------|
| DiagnosticReport | [CF-results.html](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html) | ✅ 100% |
| Patient | [CF-patient.html](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-patient.html) | ✅ 100% |
[... complete table]

### Extensions Beyond Specification

[Document non-standard converters and rationale]

## Configuration

### Strict Compliance Mode

For strict adherence to C-CDA on FHIR IG:

\`\`\`python
from ccda_to_fhir import convert_document
from ccda_to_fhir.config import STRICT_COMPLIANCE_CONFIG

bundle = convert_document(ccda_xml, config=STRICT_COMPLIANCE_CONFIG)
\`\`\`

### Custom Configuration

[Examples of custom config]

## Validation

[How to validate output against C-CDA on FHIR profiles]

## Known Limitations

[Document any known deviations or unimplemented features]
```

---

### 5.3 Update README

**File**: `README.md`

**Add section**:
```markdown
## Standards Compliance

This library implements the [HL7 C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/).

- ✅ All documented C-CDA on FHIR mappings implemented
- ✅ US Realm Header profile compliance
- ✅ Configurable strict mode for specification adherence
- ⚠️ Some optional extensions beyond specification (can be disabled)

See [docs/ccda-on-fhir-compliance.md](docs/ccda-on-fhir-compliance.md) for details.
```

---

## 6. Timeline & Dependencies

### Phase 1: Critical Fixes (Week 1)
**Duration**: 5 days
**Dependencies**: None

- [ ] 1.1 Composition Custodian Cardinality (1 day)
- [ ] 1.2 Composition Subject Cardinality (1 day)
- [ ] Tests for Phase 1 (1 day)
- [ ] Code review and refinement (1 day)
- [ ] Documentation updates (1 day)

**Deliverable**: Composition meets minimum C-CDA on FHIR requirements

---

### Phase 2: Standard Extensions (Week 2-3)
**Duration**: 10 days
**Dependencies**: Phase 1 complete

- [ ] 2.1.1 Data Enterer Extension (2 days)
- [ ] 2.1.2 Informant Extension (2 days)
- [ ] 2.1.3 Information Recipient Extension (1 day)
- [ ] 2.1.4 Participant Extension (1 day)
- [ ] 2.1.5 Performer Extension (1 day)
- [ ] 2.1.6 Authorization Extension (1 day)
- [ ] 2.1.7 In Fulfillment Of Order Extension (1 day)
- [ ] Tests for all extensions (1 day)

**Deliverable**: Full C-CDA on FHIR extension support

---

### Phase 3: Attester Slices (Week 3)
**Duration**: 3 days
**Dependencies**: Phase 1 complete

- [ ] 2.2.1 Professional Attester (authenticator) (1 day)
- [ ] 2.2.2 Practitioner extraction for authenticators (0.5 day)
- [ ] 2.2.3 Tests (0.5 day)
- [ ] 2.2.4 Document personal attester decision (1 day)

**Deliverable**: Complete attester slice implementation

---

### Phase 4: Non-Standard Documentation (Week 4)
**Duration**: 5 days
**Dependencies**: Phases 1-3 complete

- [ ] 3.1.1 DocumentReference documentation (1 day)
- [ ] 3.1.2 Provenance documentation (1 day)
- [ ] 3.1.3 NoteActivity documentation (1 day)
- [ ] 3.2 Configuration system (1 day)
- [ ] Integration and testing (1 day)

**Deliverable**: Clear documentation of extensions, configuration options

---

### Phase 5: Testing & Validation (Week 5)
**Duration**: 5 days
**Dependencies**: All previous phases

- [ ] 4.1 Compliance test suite (2 days)
- [ ] 4.2 FHIR validator integration (1 day)
- [ ] 4.3 Test data coverage (1 day)
- [ ] Integration testing (1 day)

**Deliverable**: Comprehensive validation of compliance

---

### Phase 6: Documentation (Week 5-6)
**Duration**: 3 days
**Dependencies**: All previous phases

- [ ] 5.1 Update main mapping docs (1 day)
- [ ] 5.2 Create compliance documentation (1 day)
- [ ] 5.3 Update README and user guides (1 day)

**Deliverable**: Complete, accurate documentation

---

### Total Estimated Duration: 6 weeks

**Critical Path**:
Phase 1 → Phase 2 → Phase 5 → Phase 6

**Parallel Work**:
- Phase 3 can run parallel to Phase 2 (weeks 2-3)
- Phase 4 can start after Phase 1 (week 2+)

---

## Risk Assessment

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Extension structure doesn't match spec | High | Low | Validate against official profiles early |
| Breaking changes to existing API | High | Medium | Maintain backward compatibility, add deprecation warnings |
| Performance impact from extensions | Medium | Low | Profile and optimize if needed |
| Test data insufficient | Medium | Medium | Use real-world C-CDA samples |

### Process Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Spec interpretation unclear | Medium | Medium | Consult HL7 community, reference implementations |
| Scope creep | Medium | High | Stick to defined phases, park additional ideas |
| Timeline overrun | Low | Medium | Buffer in estimate, prioritize critical fixes |

---

## Success Criteria

1. **Compliance**: All Composition resources validate against C-CDA on FHIR US Realm Header profile
2. **Extensions**: All 7 required participant extensions implemented
3. **Attesters**: All 3 attester slices implemented or documented
4. **Testing**: >95% test coverage for new code
5. **Validation**: Resources pass official FHIR validator
6. **Documentation**: Clear distinction between standard and non-standard converters
7. **Configuration**: Users can enable strict compliance mode
8. **No Regressions**: All existing tests continue to pass

---

## References

### Specifications
- [C-CDA on FHIR Implementation Guide](https://build.fhir.org/ig/HL7/ccda-on-fhir/)
- [C-CDA on FHIR US Realm Header](http://hl7.org/fhir/us/ccda/StructureDefinition-CCDA-on-FHIR-US-Realm-Header.html)
- [FHIR R4 Composition](http://hl7.org/fhir/R4/composition.html)
- [FHIR R4 Bundle](http://hl7.org/fhir/R4/bundle.html)

### Mapping Pages
- [Results Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-results.html)
- [Patient Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-patient.html)
- [Problems Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-problems.html)
- [Participation Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-participation.html)
- [Mapping Index](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-index.html)

### Tools
- [FHIR Validator](https://github.com/hapifhir/org.hl7.fhir.core/releases)
- [C-CDA Validator](https://www.healthit.gov/topic/certification/2015-edition-cures-update-test-method/2015-edition-cures-update-ccda-validator)

### Reference Implementations
- [SRDC cda2fhir](https://github.com/srdc/cda2fhir)
- [HL7 ccda-to-fhir mappings](https://github.com/HL7/ccda-to-fhir)

---

## Appendix A: Extension URLs

All C-CDA on FHIR extension URLs for reference:

```
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Data-Enterer
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Informant
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Information-Recipient
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Participant
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Performer
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-Authorization
http://hl7.org/fhir/ccda/StructureDefinition/CCDA-on-FHIR-In-Fulfillment-Of
```

---

## Appendix B: Code Locations Quick Reference

| Task | File | Approximate Line |
|------|------|-----------------|
| Custodian enforcement | composition.py | 156-159 |
| Subject enforcement | composition.py | 112-115 |
| Extension array initialization | composition.py | ~94 |
| Data enterer extraction | composition.py | New method |
| Legal authenticator (existing) | composition.py | 89-93, 339-376 |
| Professional attester | composition.py | New method |
| Practitioner extraction | convert.py | 367-381 |
| Configuration system | config.py | New file |
| Compliance tests | tests/compliance/ | New directory |

---

**Document Version**: 1.0
**Last Updated**: 2025-12-16
**Next Review**: After Phase 1 completion
