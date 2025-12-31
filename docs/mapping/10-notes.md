# Notes Mapping: C-CDA Note Activity ↔ FHIR DocumentReference

This document provides detailed mapping guidance between C-CDA Note Activity and FHIR `DocumentReference` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Note Activity (`2.16.840.1.113883.10.20.22.4.202`) | `DocumentReference` |
| Section: Various note sections | Category: `clinical-note` |
| Template: Note Activity | US Core DocumentReference Profile |

**Reference:** [C-CDA on FHIR Notes Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-notes.html)

**Scope:** Clinical notes may exist standalone or within document sections. This mapping creates separate DocumentReference resources for note entries.

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `act/id` | `DocumentReference.identifier` | ID → Identifier |
| `act/code` | `DocumentReference.type` | CodeableConcept (prefer translation if available) |
| `act/code/@code="34109-9"` | `DocumentReference.type` | Default: Note (LOINC 34109-9) |
| — | `DocumentReference.status` | Fixed: `current` |
| — | `DocumentReference.category` | Fixed: `clinical-note` |
| — | `DocumentReference.docStatus` | Fixed: `final` |
| `act/text/@mediaType` | `DocumentReference.content.attachment.contentType` | Media type from text element |
| `act/text/text()` | `DocumentReference.content.attachment.data` | Base64-encoded content |
| `act/text/reference/@value` | `DocumentReference.content.attachment` | Referenced narrative |
| `act/effectiveTime` | `DocumentReference.context.period` | Date/time conversion |
| `act/author` | `DocumentReference.author` | Reference(Practitioner) |
| `act/author/time` | `DocumentReference.date` | Author timestamp |
| `entryRelationship` or encounter | `DocumentReference.context.encounter` | Reference(Encounter) |
| `act/reference/externalDocument/id` | `DocumentReference.relatesTo.target` | External document reference |

### Status Mapping

**C-CDA:**
```xml
<act classCode="ACT" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
  <code code="34109-9" displayName="Note" codeSystem="2.16.840.1.113883.6.1"/>
  <statusCode code="completed"/>
  ...
</act>
```

**FHIR:**
```json
{
  "status": "current",
  "docStatus": "final"
}
```

**Mapping:**
- C-CDA `statusCode="completed"` → FHIR `status="current"` and `docStatus="final"`
- C-CDA `statusCode="active"` → FHIR `status="current"` and `docStatus="preliminary"`

### Type and Category

**C-CDA:**
```xml
<code code="34109-9" displayName="Note" codeSystem="2.16.840.1.113883.6.1">
  <translation code="11488-4" displayName="Consultation note"
               codeSystem="2.16.840.1.113883.6.1"/>
</code>
```

**FHIR:**
```json
{
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "11488-4",
        "display": "Consultation note"
      },
      {
        "system": "http://loinc.org",
        "code": "34109-9",
        "display": "Note"
      }
    ]
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ]
}
```

**Mapping Notes:**
- Prefer `code/translation` for `type` if available (more specific note type)
- Fallback to `code` if no translation exists
- `category` is always `clinical-note` for Note Activity entries

### Content Attachment

#### Embedded Text Content

**C-CDA:**
```xml
<text mediaType="text/plain">
  Patient presents with acute chest pain. Physical exam reveals...
</text>
```

**FHIR:**
```json
{
  "content": [
    {
      "attachment": {
        "contentType": "text/plain",
        "data": "UGF0aWVudCBwcmVzZW50cyB3aXRoIGFjdXRlIGNoZXN0IHBhaW4uIFBoeXNpY2FsIGV4YW0gcmV2ZWFscy4uLg=="
      }
    }
  ]
}
```

**Transform:**
1. Extract `@mediaType` → `contentType`
2. Extract text content
3. Base64-encode → `data`

#### Referenced Text Content

**C-CDA:**
```xml
<text>
  <reference value="#note-text-1"/>
</text>
```

**FHIR:**
```json
{
  "content": [
    {
      "attachment": {
        "contentType": "text/html",
        "data": "[base64-encoded XHTML from referenced section]"
      }
    }
  ]
}
```

**Transform:**
1. Resolve reference to narrative text in section
2. Convert CDA narrative to XHTML
3. Determine content type:
   - Minimal markup (only `<content>`, `<paragraph>`) → `text/plain`
   - Complex markup (`<table>`, `<list>`, formatting) → `text/html`
4. Base64-encode

### Context Period

**C-CDA:**
```xml
<effectiveTime>
  <low value="20200315120000-0500"/>
  <high value="20200315133000-0500"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "context": {
    "period": {
      "start": "2020-03-15T12:00:00-05:00",
      "end": "2020-03-15T13:30:00-05:00"
    }
  }
}
```

**Mapping:**
- `effectiveTime/low` → `context.period.start`
- `effectiveTime/high` → `context.period.end`
- Single `effectiveTime/@value` → both start and end

### Author Mapping

**C-CDA:**
```xml
<author>
  <time value="20200315120000-0500"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <assignedPerson>
      <name>
        <given>John</given>
        <family>Smith</family>
      </name>
    </assignedPerson>
  </assignedAuthor>
</author>
```

**FHIR:**
```json
{
  "author": [
    {
      "reference": "Practitioner/npi-1234567890"
    }
  ],
  "date": "2020-03-15T12:00:00-05:00"
}
```

**Mapping:**
- Extract author's `assignedAuthor` → Create Practitioner resource
- Generate Practitioner ID from `id` (prefer NPI)
- Reference in `DocumentReference.author`
- `author/time` → `DocumentReference.date`

### Encounter Context

**C-CDA:**
```xml
<entryRelationship typeCode="COMP">
  <encounter classCode="ENC" moodCode="EVN">
    <id root="2.16.840.1.113883.19" extension="encounter-123"/>
    ...
  </encounter>
</entryRelationship>
```

**FHIR:**
```json
{
  "context": {
    "encounter": [
      {
        "reference": "Encounter/encounter-123"
      }
    ]
  }
}
```

**Mapping:**
- If note has related encounter via `entryRelationship`
- Or from encompassing encounter at document level
- Create reference to Encounter resource

### Related Documents

**C-CDA:**
```xml
<reference typeCode="REFR">
  <externalDocument>
    <id root="2.16.840.1.113883.19.5" extension="doc-456"/>
    <code code="18842-5" displayName="Discharge Summary"
          codeSystem="2.16.840.1.113883.6.1"/>
  </externalDocument>
</reference>
```

**FHIR:**
```json
{
  "relatesTo": [
    {
      "code": "replaces",
      "target": {
        "identifier": {
          "system": "urn:oid:2.16.840.1.113883.19.5",
          "value": "doc-456"
        }
      }
    }
  ]
}
```

**Relationship Codes:**
| C-CDA typeCode | FHIR relatesTo.code |
|----------------|---------------------|
| RPLC (replaces) | `replaces` |
| APND (appends) | `appends` |
| XFRM (transforms) | `transforms` |
| REFR (refers to) | Uses `context.related` instead |

## US Core DocumentReference Compliance

This mapping aligns with [US Core DocumentReference Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-documentreference.html).

**Required Elements:**
- ✅ `status` - Always `current`
- ✅ `type` - From C-CDA code
- ✅ `category` - Fixed to `clinical-note`
- ✅ `subject` - Reference to Patient
- ✅ `content.attachment.contentType` - From C-CDA text/@mediaType
- ✅ `content.attachment.data` or `url` - Base64-encoded text

**Must Support Elements:**
- ✅ `identifier` - From C-CDA id
- ✅ `date` - From author/time
- ✅ `author` - From author/assignedAuthor
- ✅ `context.encounter` - From related encounter
- ✅ `context.period` - From effectiveTime

## Common Note Types

### Consultation Note

**C-CDA:**
```xml
<code code="11488-4" displayName="Consultation note" codeSystem="2.16.840.1.113883.6.1"/>
```

**US Core Category:** `clinical-note`

### Progress Note

**C-CDA:**
```xml
<code code="11506-3" displayName="Progress note" codeSystem="2.16.840.1.113883.6.1"/>
```

**US Core Category:** `clinical-note`

### Procedure Note

**C-CDA:**
```xml
<code code="28570-0" displayName="Procedure note" codeSystem="2.16.840.1.113883.6.1"/>
```

**US Core Category:** `clinical-note`

### Discharge Summary

**C-CDA:**
```xml
<code code="18842-5" displayName="Discharge Summary" codeSystem="2.16.840.1.113883.6.1"/>
```

**US Core Category:** `clinical-note`

## Narrative Content Handling

### Simple Text (Plain Text)

When note text contains only simple content:

**C-CDA:**
```xml
<text mediaType="text/plain">
  Patient is a 45-year-old male with history of hypertension.
  Currently on lisinopril 10mg daily.
</text>
```

**FHIR:**
```json
{
  "content": [
    {
      "attachment": {
        "contentType": "text/plain",
        "data": "UGF0aWVudCBpcyBhIDQ1LXllYXItb2xkIG1hbGUgd2l0aCBoaXN0b3J5IG9mIGh5cGVydGVuc2lvbi4KQ3VycmVudGx5IG9uIGxpc2lub3ByaWwgMTBtZyBkYWlseS4="
      }
    }
  ]
}
```

### Structured Narrative (XHTML)

When note text contains rich markup:

**C-CDA:**
```xml
<text>
  <table>
    <thead>
      <tr><th>System</th><th>Findings</th></tr>
    </thead>
    <tbody>
      <tr><td>Cardiovascular</td><td>Regular rate and rhythm</td></tr>
      <tr><td>Respiratory</td><td>Clear to auscultation</td></tr>
    </tbody>
  </table>
</text>
```

**FHIR:**
```json
{
  "content": [
    {
      "attachment": {
        "contentType": "text/html",
        "data": "[base64-encoded XHTML table]"
      }
    }
  ]
}
```

## Implementation Notes

### Note Location in C-CDA

Notes can appear in several contexts:

1. **Within Section Entries** (most common)
   ```xml
   <section>
     <code code="29299-5" displayName="Reason for visit"/>
     <entry>
       <act classCode="ACT" moodCode="EVN">
         <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
         <!-- Note Activity -->
       </act>
     </entry>
   </section>
   ```

2. **Standalone in Document Body**
   Less common but valid

3. **As Section Narrative Only**
   Some notes exist only as `section/text` without Note Activity template
   → These remain in Composition.section.text, not extracted as DocumentReference

### When to Create DocumentReference

Create DocumentReference resource when:
- ✅ Entry uses Note Activity template (2.16.840.1.113883.10.20.22.4.202)
- ✅ Note has structured metadata (author, time, type)
- ✅ Note represents a discrete clinical document

Do NOT create DocumentReference when:
- ❌ Note is only section narrative without Note Activity template
- ❌ Note is just a comment/annotation on another entry (use Annotation instead)
- ❌ Text is part of another resource's narrative

### Deduplication

Multiple sections may reference the same note:
- Use note `id` to deduplicate
- Create only one DocumentReference per unique note
- Reference from multiple Composition sections if needed

## Edge Cases

### Note Without Explicit Author

**C-CDA:**
```xml
<act classCode="ACT" moodCode="EVN">
  <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
  <code code="34109-9"/>
  <!-- No author element -->
  <text>Note text here</text>
</act>
```

**FHIR:**
```json
{
  "author": [
    {
      "display": "Unknown Author"
    }
  ]
}
```

Use document-level author or placeholder if entry has no author.

### Note Without Content

**C-CDA:**
```xml
<act classCode="ACT" moodCode="EVN">
  <code code="34109-9"/>
  <!-- No text element -->
</act>
```

**Action:** Skip creating DocumentReference - content is required per US Core.

### Mixed Content Types

**C-CDA:**
```xml
<text>
  Plain text followed by <content>structured</content> content.
</text>
```

**FHIR:** Choose `text/html` when any markup present, preserve all content.

## Example: Complete Consultation Note

### C-CDA

```xml
<entry>
  <act classCode="ACT" moodCode="EVN">
    <templateId root="2.16.840.1.113883.10.20.22.4.202"/>
    <id root="1.2.3.4.5" extension="note-789"/>
    <code code="11488-4" displayName="Consultation note" codeSystem="2.16.840.1.113883.6.1"/>
    <statusCode code="completed"/>
    <effectiveTime>
      <low value="20200315120000-0500"/>
      <high value="20200315133000-0500"/>
    </effectiveTime>
    <text mediaType="text/plain">
      Cardiology consultation for evaluation of chest pain.

      Patient is a 52-year-old male presenting with episodic chest pressure
      over the past 2 weeks. Pain is non-radiating, lasts 5-10 minutes,
      and resolves with rest.

      Assessment: Likely stable angina
      Plan: Stress test ordered, continue aspirin and statin
    </text>
    <author>
      <time value="20200315133000-0500"/>
      <assignedAuthor>
        <id root="2.16.840.1.113883.4.6" extension="9876543210"/>
        <assignedPerson>
          <name>
            <prefix>Dr.</prefix>
            <given>Sarah</given>
            <family>Cardiology</family>
          </name>
        </assignedPerson>
      </assignedAuthor>
    </author>
    <entryRelationship typeCode="COMP">
      <encounter classCode="ENC" moodCode="EVN">
        <id root="2.16.840.1.113883.19" extension="enc-456"/>
      </encounter>
    </entryRelationship>
  </act>
</entry>
```

### FHIR

```json
{
  "resourceType": "DocumentReference",
  "id": "note-789",
  "identifier": [
    {
      "system": "urn:oid:1.2.3.4.5",
      "value": "note-789"
    }
  ],
  "status": "current",
  "docStatus": "final",
  "type": {
    "coding": [
      {
        "system": "http://loinc.org",
        "code": "11488-4",
        "display": "Consultation note"
      }
    ]
  },
  "category": [
    {
      "coding": [
        {
          "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
          "code": "clinical-note",
          "display": "Clinical Note"
        }
      ]
    }
  ],
  "subject": {
    "reference": "Patient/patient-123"
  },
  "date": "2020-03-15T13:30:00-05:00",
  "author": [
    {
      "reference": "Practitioner/npi-9876543210"
    }
  ],
  "content": [
    {
      "attachment": {
        "contentType": "text/plain",
        "data": "Q2FyZGlvbG9neSBjb25zdWx0YXRpb24gZm9yIGV2YWx1YXRpb24gb2YgY2hlc3QgcGFpbi4KCkJhdGllbnQgaXMgYSA1Mi15ZWFyLW9sZCBtYWxlIHByZXNlbnRpbmcgd2l0aCBlcGlzb2RpYyBjaGVzdCBwcmVzc3VyZQpvdmVyIHRoZSBwYXN0IDIgd2Vla3MuIFBhaW4gaXMgbm9uLXJhZGlhdGluZywgbGFzdHMgNS0xMCBtaW51dGVzLAphbmQgcmVzb2x2ZXMgd2l0aCByZXN0LgoKQXNzZXNzbWVudDogTGlrZWx5IHN0YWJsZSBhbmdpbmEKUGxhbjogU3RyZXNzIHRlc3Qgb3JkZXJlZCwgY29udGludWUgYXNwaXJpbiBhbmQgc3RhdGlu"
      }
    }
  ],
  "context": {
    "encounter": [
      {
        "reference": "Encounter/enc-456"
      }
    ],
    "period": {
      "start": "2020-03-15T12:00:00-05:00",
      "end": "2020-03-15T13:30:00-05:00"
    }
  }
}
```

## References

- [C-CDA on FHIR Notes Mapping](https://build.fhir.org/ig/HL7/ccda-on-fhir/CF-notes.html)
- [C-CDA Note Activity Template](https://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.202.html)
- [US Core DocumentReference Profile](http://hl7.org/fhir/us/core/StructureDefinition-us-core-documentreference.html)
- [FHIR DocumentReference Resource](http://hl7.org/fhir/R4/documentreference.html)

## Related Mappings

- See [09-practitioner.md](09-practitioner.md) for author mapping details
- See [08-encounter.md](08-encounter.md) for encounter context
