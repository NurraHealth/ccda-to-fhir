# Procedure Mapping: C-CDA Procedure Activity ↔ FHIR Procedure

This document provides detailed mapping guidance between C-CDA Procedure Activity templates and FHIR `Procedure` resource.

## Overview

| C-CDA | FHIR |
|-------|------|
| Procedure Activity Procedure (`2.16.840.1.113883.10.20.22.4.14`) | `Procedure` |
| Procedure Activity Observation (`2.16.840.1.113883.10.20.22.4.13`) | `Procedure` |
| Procedure Activity Act (`2.16.840.1.113883.10.20.22.4.12`) | `Procedure` |
| Section: Procedures (LOINC `47519-4`) | — |

## C-CDA to FHIR Mapping

### Core Element Mappings

| C-CDA Path | FHIR Path | Transform |
|------------|-----------|-----------|
| `@negationInd="true"` | `Procedure.status` | Set to `not-done` |
| `procedure/id` | `Procedure.identifier` | ID → Identifier |
| `procedure/code` | `Procedure.code` | CodeableConcept |
| `procedure/statusCode` | `Procedure.status` | [Status ConceptMap](#status-mapping) |
| `procedure/effectiveTime/@value` | `Procedure.performedDateTime` | Date conversion |
| `procedure/effectiveTime/low` | `Procedure.performedPeriod.start` | Date conversion |
| `procedure/effectiveTime/high` | `Procedure.performedPeriod.end` | Date conversion |
| `procedure/targetSiteCode` | `Procedure.bodySite` | CodeableConcept |
| `procedure/performer/assignedEntity` | `Procedure.performer.actor` | Reference(Practitioner) |
| `procedure/participant[@typeCode='LOC']` | `Procedure.location` | Reference(Location) |
| `procedure/author` | `Procedure.recorder` + Provenance | Reference(Practitioner) |
| `entryRelationship[@typeCode='RSON']/observation/value` | `Procedure.reasonCode` | CodeableConcept |
| `entryRelationship[@typeCode='RSON']/observation` | `Procedure.reasonReference` | Reference(Condition) |
| Comment Activity `text` | `Procedure.note` | Annotation |

### Status Mapping

**C-CDA:**
```xml
<statusCode code="completed"/>
```

**Procedure Status ConceptMap:**

| C-CDA statusCode | FHIR status |
|------------------|-------------|
| `completed` | `completed` |
| `active` | `in-progress` |
| `aborted` | `stopped` |
| `cancelled` | `not-done` |
| `held` | `on-hold` |
| `new` | `preparation` |
| `suspended` | `on-hold` |

**FHIR:**
```json
{
  "status": "completed"
}
```

### Negation Handling

When `@negationInd="true"`:

**C-CDA:**
```xml
<procedure classCode="PROC" moodCode="EVN" negationInd="true">
  <templateId root="2.16.840.1.113883.10.20.22.4.14"/>
  <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
        displayName="Colonoscopy"/>
  <statusCode code="completed"/>
</procedure>
```

**FHIR:**
```json
{
  "status": "not-done",
  "code": {
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "73761001",
      "display": "Colonoscopy"
    }]
  }
}
```

### Procedure Code Mapping

**C-CDA:**
```xml
<code code="73761001" codeSystem="2.16.840.1.113883.6.96"
      displayName="Colonoscopy">
  <originalText>
    <reference value="#proc1"/>
  </originalText>
  <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
               displayName="Colonoscopy, diagnostic"/>
</code>
```

**FHIR:**
```json
{
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "73761001",
        "display": "Colonoscopy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "45378",
        "display": "Colonoscopy, diagnostic"
      }
    ],
    "text": "Colonoscopy"
  }
}
```

### Effective Time Mapping

#### Single Point in Time

**C-CDA:**
```xml
<effectiveTime value="20200315103000-0500"/>
```

**FHIR:**
```json
{
  "performedDateTime": "2020-03-15T10:30:00-05:00"
}
```

#### Time Period

**C-CDA:**
```xml
<effectiveTime>
  <low value="20200315103000-0500"/>
  <high value="20200315120000-0500"/>
</effectiveTime>
```

**FHIR:**
```json
{
  "performedPeriod": {
    "start": "2020-03-15T10:30:00-05:00",
    "end": "2020-03-15T12:00:00-05:00"
  }
}
```

#### Missing Effective Time

If `effectiveTime` is not provided, include data-absent-reason extension:

**FHIR:**
```json
{
  "_performedDateTime": {
    "extension": [{
      "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
      "valueCode": "unknown"
    }]
  }
}
```

### Body Site Mapping

**C-CDA:**
```xml
<targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                displayName="Colon structure">
  <qualifier>
    <name code="272741003" codeSystem="2.16.840.1.113883.6.96"
          displayName="Laterality"/>
    <value code="7771000" codeSystem="2.16.840.1.113883.6.96"
           displayName="Left"/>
  </qualifier>
</targetSiteCode>
```

**FHIR:**
```json
{
  "bodySite": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "71854001",
      "display": "Colon structure"
    }],
    "text": "Left colon"
  }]
}
```

### Performer Mapping

**C-CDA:**
```xml
<performer>
  <assignedEntity>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
    <code code="207RG0100X" codeSystem="2.16.840.1.113883.6.101"
          displayName="Gastroenterology"/>
    <assignedPerson>
      <name>
        <given>John</given>
        <family>Surgeon</family>
        <suffix>MD</suffix>
      </name>
    </assignedPerson>
    <representedOrganization>
      <name>City Hospital</name>
    </representedOrganization>
  </assignedEntity>
</performer>
```

**FHIR:**
```json
{
  "performer": [{
    "actor": {
      "reference": "Practitioner/practitioner-surgeon"
    },
    "onBehalfOf": {
      "reference": "Organization/org-hospital"
    }
  }]
}
```

**Notes:**
- Avoid using `onBehalfOf` when actor is already a PractitionerRole that includes organization
- Create separate Practitioner and Organization resources as needed

### Location Mapping

**C-CDA:**
```xml
<participant typeCode="LOC">
  <participantRole classCode="SDLOC">
    <id root="2.16.840.1.113883.19.5" extension="OR-1"/>
    <code code="22232009" codeSystem="2.16.840.1.113883.6.96"
          displayName="Hospital"/>
    <playingEntity classCode="PLC">
      <name>Operating Room 1</name>
    </playingEntity>
  </participantRole>
</participant>
```

**FHIR:**
```json
{
  "location": {
    "reference": "Location/location-or1",
    "display": "Operating Room 1"
  }
}
```

### Reason Code Mapping

**C-CDA:**
```xml
<entryRelationship typeCode="RSON">
  <observation classCode="OBS" moodCode="EVN">
    <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
    <value xsi:type="CD" code="237602007" codeSystem="2.16.840.1.113883.6.96"
           displayName="Metabolic syndrome"/>
  </observation>
</entryRelationship>
```

**FHIR:**
```json
{
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "237602007",
      "display": "Metabolic syndrome"
    }]
  }]
}
```

**Alternative: Reference to Condition**

If the indication references a converted Problem Observation:

```json
{
  "reasonReference": [{
    "reference": "Condition/condition-metabolic-syndrome"
  }]
}
```

### Author and Provenance

**C-CDA:**
```xml
<author>
  <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
  <time value="20200315"/>
  <assignedAuthor>
    <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
  </assignedAuthor>
</author>
```

**FHIR Procedure:**
```json
{
  "recorder": {
    "reference": "Practitioner/practitioner-example"
  }
}
```

**FHIR Provenance:**
```json
{
  "resourceType": "Provenance",
  "target": [{"reference": "Procedure/procedure-example"}],
  "recorded": "2020-03-15T00:00:00Z",
  "agent": [{
    "type": {
      "coding": [{
        "system": "http://terminology.hl7.org/CodeSystem/provenance-participant-type",
        "code": "author"
      }]
    },
    "who": {"reference": "Practitioner/practitioner-example"}
  }]
}
```

## FHIR to C-CDA Mapping

### Reverse Mappings

| FHIR Path | C-CDA Path | Notes |
|-----------|------------|-------|
| `Procedure.identifier` | `procedure/id` | Identifier → ID |
| `Procedure.status: not-done` | `@negationInd="true"` | Set negation indicator |
| `Procedure.status` | `procedure/statusCode` | Reverse status map |
| `Procedure.code` | `procedure/code` | CodeableConcept → CD |
| `Procedure.performedDateTime` | `procedure/effectiveTime/@value` | Date format |
| `Procedure.performedPeriod` | `procedure/effectiveTime/low,high` | Period format |
| `Procedure.bodySite` | `procedure/targetSiteCode` | CodeableConcept → CD |
| `Procedure.performer.actor` | `procedure/performer/assignedEntity` | Create performer |
| `Procedure.performer.onBehalfOf` | `performer/assignedEntity/representedOrganization` | Organization |
| `Procedure.location` | `participant[@typeCode='LOC']` | Create participant |
| `Procedure.recorder` | `procedure/author` | Create author |
| `Procedure.reasonCode` | `entryRelationship[@typeCode='RSON']` | Create indication |
| `Procedure.note` | Comment Activity | Create nested act |

### FHIR Status to CDA

| FHIR status | CDA statusCode | Additional |
|-------------|----------------|------------|
| `completed` | `completed` | — |
| `in-progress` | `active` | — |
| `stopped` | `aborted` | — |
| `not-done` | `cancelled` | or `negationInd="true"` |
| `on-hold` | `suspended` | — |
| `preparation` | `new` | — |
| `entered-in-error` | — | Do not convert |
| `unknown` | — | Use nullFlavor |

## Complete Example

### C-CDA Input

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.7.1"/>
  <code code="47519-4" codeSystem="2.16.840.1.113883.6.1"/>
  <title>PROCEDURES</title>
  <entry typeCode="DRIV">
    <procedure classCode="PROC" moodCode="EVN">
      <templateId root="2.16.840.1.113883.10.20.22.4.14" extension="2014-06-09"/>
      <id root="d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"/>
      <code code="73761001" codeSystem="2.16.840.1.113883.6.96"
            displayName="Colonoscopy">
        <translation code="45378" codeSystem="2.16.840.1.113883.6.12"
                     displayName="Colonoscopy, diagnostic"/>
      </code>
      <statusCode code="completed"/>
      <effectiveTime value="20200315103000-0500"/>
      <targetSiteCode code="71854001" codeSystem="2.16.840.1.113883.6.96"
                      displayName="Colon structure"/>
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <assignedPerson>
            <name><given>John</given><family>Surgeon</family></name>
          </assignedPerson>
        </assignedEntity>
      </performer>
      <author>
        <time value="20200315"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <value xsi:type="CD" code="68496003" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Polyp of colon"/>
        </observation>
      </entryRelationship>
    </procedure>
  </entry>
</section>
```

### FHIR Output

```json
{
  "resourceType": "Procedure",
  "id": "procedure-colonoscopy",
  "meta": {
    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure"]
  },
  "identifier": [{
    "system": "urn:ietf:rfc:3986",
    "value": "urn:uuid:d68b7e32-7810-4f5b-9cc2-acd54b0fd85d"
  }],
  "status": "completed",
  "code": {
    "coding": [
      {
        "system": "http://snomed.info/sct",
        "code": "73761001",
        "display": "Colonoscopy"
      },
      {
        "system": "http://www.ama-assn.org/go/cpt",
        "code": "45378",
        "display": "Colonoscopy, diagnostic"
      }
    ],
    "text": "Colonoscopy"
  },
  "subject": {
    "reference": "Patient/patient-example"
  },
  "performedDateTime": "2020-03-15T10:30:00-05:00",
  "recorder": {
    "reference": "Practitioner/practitioner-surgeon"
  },
  "performer": [{
    "actor": {
      "reference": "Practitioner/practitioner-surgeon"
    }
  }],
  "bodySite": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "71854001",
      "display": "Colon structure"
    }]
  }],
  "reasonCode": [{
    "coding": [{
      "system": "http://snomed.info/sct",
      "code": "68496003",
      "display": "Polyp of colon"
    }]
  }]
}
```

## References

- [C-CDA on FHIR Procedures Mapping](http://build.fhir.org/ig/HL7/ccda-on-fhir/CF-procedures.html)
- [US Core Procedure Profile](http://hl7.org/fhir/us/core/StructureDefinition/us-core-procedure)
- [C-CDA Procedure Activity Procedure](http://www.hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.4.14.html)
