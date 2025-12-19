# C-CDA: Care Plan Document

## Overview

The Care Plan Document in C-CDA represents a consensus-driven dynamic plan that integrates a patient's and Care Team Members' prioritized concerns, goals, and planned interventions. It serves as a blueprint shared by all Care Team Members to guide patient care, reconciling and resolving conflicts between various Plans of Care proposed by multiple providers and disciplines for multiple conditions.

## Template Information

### Care Plan Document

| Attribute | Value |
|-----------|-------|
| Template ID | `2.16.840.1.113883.10.20.22.1.15` |
| Template Name | Care Plan |
| Template Version | 2015-08-01 |
| LOINC Code | 52521-2 |
| LOINC Display | Overall plan of care/advance care directives |
| Official URL | `http://hl7.org/fhir/us/ccda/StructureDefinition/Care-Plan-Document` |
| Parent Template | US Realm Header |

## Document Purpose

A Care Plan is distinct from a simple Continuity of Care Document (CCD) in that it:
- Emphasizes relationships among health concerns, goals, interventions, and outcomes
- Integrates multiple Plans of Care from different providers
- Provides a dynamic, living document updated as patient status changes
- Focuses on care coordination and shared decision-making
- Documents patient-centered prioritized concerns

## Location in Document Hierarchy

```
ClinicalDocument [Care Plan]
├── templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"
├── code (52521-2 "Overall plan of care/advance care directives")
├── title
├── recordTarget (patient)
├── author (plan author)
├── custodian
├── documentationOf (service event period)
└── component
    └── structuredBody
        ├── component [Health Concerns Section] **REQUIRED**
        ├── component [Goals Section] **REQUIRED**
        ├── component [Interventions Section] **SHOULD**
        └── component [Health Status Evaluations and Outcomes Section] **SHOULD**
```

## Required Document Elements

### ClinicalDocument Header

| Element | Description | Required |
|---------|-------------|----------|
| templateId | Care Plan template ID | Yes |
| id | Unique document identifier | Yes |
| code | LOINC 52521-2 | Yes |
| title | Document title (e.g., "Care Plan") | Yes |
| effectiveTime | Document creation timestamp | Yes |
| confidentialityCode | Document confidentiality level | Yes |
| languageCode | Document language (e.g., "en-US") | Yes |
| recordTarget | Patient information | Yes |
| author | Document author(s) | Yes (at least one) |
| custodian | Organization maintaining document | Yes |
| documentationOf | Service event with period | Should |

## XML Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ClinicalDocument xmlns="urn:hl7-org:v3" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                  xmlns:sdtc="urn:hl7-org:sdtc">

  <!-- Care Plan Document Template -->
  <templateId root="2.16.840.1.113883.10.20.22.1.15" extension="2015-08-01"/>

  <!-- Document ID -->
  <id root="2.16.840.1.113883.19.5" extension="careplan-12345"/>

  <!-- Document Code: Overall Plan of Care -->
  <code code="52521-2" codeSystem="2.16.840.1.113883.6.1"
        codeSystemName="LOINC" displayName="Overall plan of care/advance care directives"/>

  <title>Care Plan</title>

  <!-- Document creation time -->
  <effectiveTime value="20240115120000-0500"/>

  <confidentialityCode code="N" codeSystem="2.16.840.1.113883.5.25"/>

  <languageCode code="en-US"/>

  <!-- Set and version relationships -->
  <setId root="2.16.840.1.113883.19.5" extension="careplan-set-123"/>
  <versionNumber value="2"/>

  <!-- Patient Information -->
  <recordTarget>
    <patientRole>
      <id root="2.16.840.1.113883.4.1" extension="123-45-6789"/>
      <addr use="HP">
        <streetAddressLine>123 Main St</streetAddressLine>
        <city>Springfield</city>
        <state>IL</state>
        <postalCode>62701</postalCode>
      </addr>
      <telecom use="HP" value="tel:+1-217-555-1234"/>
      <patient>
        <name>
          <given>Amy</given>
          <family>Shaw</family>
        </name>
        <administrativeGenderCode code="F" codeSystem="2.16.840.1.113883.5.1"/>
        <birthTime value="19850312"/>
        <raceCode code="2106-3" codeSystem="2.16.840.1.113883.6.238"
                  displayName="White"/>
        <ethnicGroupCode code="2186-5" codeSystem="2.16.840.1.113883.6.238"
                        displayName="Not Hispanic or Latino"/>
      </patient>
    </patientRole>
  </recordTarget>

  <!-- Document Author -->
  <author>
    <time value="20240115120000-0500"/>
    <assignedAuthor>
      <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
      <code code="207Q00000X" codeSystem="2.16.840.1.113883.11.19465"
            displayName="Family Medicine"/>
      <addr>
        <streetAddressLine>123 Medical Dr</streetAddressLine>
        <city>Springfield</city>
        <state>IL</state>
        <postalCode>62701</postalCode>
      </addr>
      <telecom use="WP" value="tel:+1-217-555-5000"/>
      <assignedPerson>
        <name>
          <given>John</given>
          <family>Smith</family>
          <suffix>MD</suffix>
        </name>
      </assignedPerson>
    </assignedAuthor>
  </author>

  <!-- Custodian -->
  <custodian>
    <assignedCustodian>
      <representedCustodianOrganization>
        <id root="2.16.840.1.113883.4.6" extension="hospital-123"/>
        <name>Springfield General Hospital</name>
        <telecom use="WP" value="tel:+1-217-555-5000"/>
        <addr>
          <streetAddressLine>100 Hospital Way</streetAddressLine>
          <city>Springfield</city>
          <state>IL</state>
          <postalCode>62701</postalCode>
        </addr>
      </representedCustodianOrganization>
    </assignedCustodian>
  </custodian>

  <!-- Service Event: Care Plan Period -->
  <documentationOf>
    <serviceEvent classCode="PCPR">
      <effectiveTime>
        <low value="20240115"/>
        <high value="20240415"/>
      </effectiveTime>
      <performer typeCode="PRF">
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <code code="207Q00000X" codeSystem="2.16.840.1.113883.11.19465"
                displayName="Family Medicine"/>
          <assignedPerson>
            <name>
              <given>John</given>
              <family>Smith</family>
              <suffix>MD</suffix>
            </name>
          </assignedPerson>
        </assignedEntity>
      </performer>
    </serviceEvent>
  </documentationOf>

  <!-- Document Body -->
  <component>
    <structuredBody>

      <!-- REQUIRED: Health Concerns Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
          <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                displayName="Health concerns document"/>
          <title>HEALTH CONCERNS</title>
          <text>
            <table border="1" width="100%">
              <thead>
                <tr>
                  <th>Concern</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td ID="concern1">Respiratory insufficiency</td>
                  <td>Active</td>
                  <td>January 15, 2024</td>
                </tr>
                <tr>
                  <td ID="concern2">Current tobacco user</td>
                  <td>Active</td>
                  <td>January 15, 2024</td>
                </tr>
              </tbody>
            </table>
          </text>

          <!-- Health Concern Act Entry -->
          <entry typeCode="DRIV">
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.132" extension="2015-08-01"/>
              <id root="concern-act-123"/>
              <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Health Concern"/>
              <text>
                <reference value="#concern1"/>
              </text>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
              </effectiveTime>

              <!-- Reference to Problem Observation -->
              <entryRelationship typeCode="REFR">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.4" extension="2015-08-01"/>
                  <id root="problem-obs-456"/>
                  <code code="55607006" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Problem"/>
                  <statusCode code="completed"/>
                  <effectiveTime>
                    <low value="20240115"/>
                  </effectiveTime>
                  <value xsi:type="CD" code="409623005" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Respiratory insufficiency"/>
                </observation>
              </entryRelationship>
            </act>
          </entry>

          <entry typeCode="DRIV">
            <act classCode="ACT" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.132" extension="2015-08-01"/>
              <id root="concern-act-789"/>
              <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Health Concern"/>
              <text>
                <reference value="#concern2"/>
              </text>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
              </effectiveTime>

              <!-- Reference to Social History Observation -->
              <entryRelationship typeCode="REFR">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.78" extension="2014-06-09"/>
                  <code code="72166-2" codeSystem="2.16.840.1.113883.6.1"
                        displayName="Tobacco smoking status"/>
                  <statusCode code="completed"/>
                  <effectiveTime>
                    <low value="20240115"/>
                  </effectiveTime>
                  <value xsi:type="CD" code="449868002" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Current every day smoker"/>
                </observation>
              </entryRelationship>
            </act>
          </entry>
        </section>
      </component>

      <!-- REQUIRED: Goals Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.60" extension="2015-08-01"/>
          <code code="61146-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Goals"/>
          <title>GOALS</title>
          <text>
            <table border="1" width="100%">
              <thead>
                <tr>
                  <th>Goal</th>
                  <th>Start Date</th>
                  <th>Target Date</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td ID="goal1">Maintain oxygen saturation greater than 92%</td>
                  <td>January 15, 2024</td>
                  <td>April 15, 2024</td>
                  <td>Active</td>
                </tr>
              </tbody>
            </table>
          </text>

          <entry typeCode="DRIV">
            <observation classCode="OBS" moodCode="GOL">
              <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
              <id root="goal-obs-123"/>
              <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Oxygen saturation in Arterial blood by Pulse oximetry">
                <originalText>
                  <reference value="#goal1"/>
                </originalText>
              </code>
              <text>
                <reference value="#goal1"/>
              </text>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
                <high value="20240415"/>
              </effectiveTime>

              <!-- Target value -->
              <entryRelationship typeCode="COMP">
                <observation classCode="OBS" moodCode="GOL">
                  <templateId root="2.16.840.1.113883.10.20.22.4.121" extension="2022-06-01"/>
                  <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                        displayName="Oxygen saturation in Arterial blood by Pulse oximetry"/>
                  <value xsi:type="IVL_PQ">
                    <low value="92" unit="%"/>
                  </value>
                </observation>
              </entryRelationship>

              <!-- Link to health concern -->
              <entryRelationship typeCode="RSON">
                <observation classCode="OBS" moodCode="EVN">
                  <templateId root="2.16.840.1.113883.10.20.22.4.122"/>
                  <id root="concern-act-123"/>
                  <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"
                        displayName="Health Concern"/>
                  <value xsi:type="CD" code="409623005" codeSystem="2.16.840.1.113883.6.96"
                         displayName="Respiratory insufficiency"/>
                </observation>
              </entryRelationship>
            </observation>
          </entry>
        </section>
      </component>

      <!-- SHOULD: Interventions Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.21.2.3" extension="2015-08-01"/>
          <code code="62387-6" codeSystem="2.16.840.1.113883.6.1"
                displayName="Interventions Provided"/>
          <title>INTERVENTIONS</title>
          <text>
            <table border="1" width="100%">
              <thead>
                <tr>
                  <th>Intervention</th>
                  <th>Status</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td ID="intervention1">Oxygen therapy via nasal cannula</td>
                  <td>Planned</td>
                  <td>January 15, 2024 - April 15, 2024</td>
                </tr>
                <tr>
                  <td ID="intervention2">Elevation of head of bed</td>
                  <td>Planned</td>
                  <td>January 15, 2024 - April 15, 2024</td>
                </tr>
              </tbody>
            </table>
          </text>

          <!-- Planned Intervention -->
          <entry typeCode="DRIV">
            <act classCode="ACT" moodCode="INT">
              <templateId root="2.16.840.1.113883.10.20.22.4.131" extension="2015-08-01"/>
              <id root="intervention-act-123"/>
              <code code="362956003" codeSystem="2.16.840.1.113883.6.96"
                    displayName="Procedure/intervention (procedure)"/>
              <text>
                <reference value="#intervention1"/>
              </text>
              <statusCode code="active"/>
              <effectiveTime>
                <low value="20240115"/>
                <high value="20240415"/>
              </effectiveTime>

              <!-- Procedure Activity Act -->
              <entryRelationship typeCode="COMP">
                <act classCode="ACT" moodCode="INT">
                  <templateId root="2.16.840.1.113883.10.20.22.4.12" extension="2014-06-09"/>
                  <code code="371907003" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Oxygen administration by nasal cannula"/>
                  <statusCode code="active"/>
                  <effectiveTime>
                    <low value="20240115"/>
                    <high value="20240415"/>
                  </effectiveTime>
                </act>
              </entryRelationship>
            </act>
          </entry>
        </section>
      </component>

      <!-- SHOULD: Health Status Evaluations and Outcomes Section -->
      <component>
        <section>
          <templateId root="2.16.840.1.113883.10.20.22.2.61"/>
          <code code="11383-7" codeSystem="2.16.840.1.113883.6.1"
                displayName="Patient problem outcome"/>
          <title>HEALTH STATUS EVALUATIONS AND OUTCOMES</title>
          <text>
            <table border="1" width="100%">
              <thead>
                <tr>
                  <th>Outcome</th>
                  <th>Value</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td ID="outcome1">Oxygen saturation</td>
                  <td>95%</td>
                  <td>January 20, 2024</td>
                </tr>
              </tbody>
            </table>
          </text>

          <entry typeCode="DRIV">
            <observation classCode="OBS" moodCode="EVN">
              <templateId root="2.16.840.1.113883.10.20.22.4.144"/>
              <id root="outcome-obs-123"/>
              <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"
                    displayName="Oxygen saturation in Arterial blood by Pulse oximetry"/>
              <text>
                <reference value="#outcome1"/>
              </text>
              <statusCode code="completed"/>
              <effectiveTime value="20240120"/>
              <value xsi:type="PQ" value="95" unit="%"/>

              <!-- Link to goal being evaluated -->
              <entryRelationship typeCode="GEVL">
                <observation classCode="OBS" moodCode="GOL">
                  <id root="goal-obs-123"/>
                  <code code="59408-5" codeSystem="2.16.840.1.113883.6.1"/>
                </observation>
              </entryRelationship>
            </observation>
          </entry>
        </section>
      </component>

    </structuredBody>
  </component>
</ClinicalDocument>
```

## Section Details

### Health Concerns Section (V2) - REQUIRED

**Template ID:** `2.16.840.1.113883.10.20.22.2.58` extension `2015-08-01`

| Element | Description | Required |
|---------|-------------|----------|
| code | LOINC `75310-3` "Health concerns document" | Yes |
| title | Section title | Yes |
| text | Human-readable narrative | Yes |
| entry | Health Concern Act entries | Should (at least one) |

**Entry Template:** Health Concern Act (V3) `2.16.840.1.113883.10.20.22.4.132`

**Entry Relationships:**
- **REFR (refers to):** Problem Observations, Social History Observations, Allergies
- **SPRT (has support):** Supporting observations

### Goals Section - REQUIRED

**Template ID:** `2.16.840.1.113883.10.20.22.2.60` extension `2015-08-01`

| Element | Description | Required |
|---------|-------------|----------|
| code | LOINC `61146-7` "Goals" | Yes |
| title | Section title | Yes |
| text | Human-readable narrative | Yes |
| entry | Goal Observation entries | Should (at least one) |

**Entry Template:** Goal Observation `2.16.840.1.113883.10.20.22.4.121`

See `goals-section.md` for complete specification.

### Interventions Section (V3) - SHOULD

**Template ID:** `2.16.840.1.113883.10.20.21.2.3` extension `2015-08-01`

| Element | Description | Required |
|---------|-------------|----------|
| code | LOINC `62387-6` "Interventions Provided" | Yes |
| title | Section title | Yes |
| text | Human-readable narrative | Yes |
| entry | Intervention Act entries | May |

**Entry Template:** Intervention Act `2.16.840.1.113883.10.20.22.4.131`

**moodCode Values:**
- **INT (Intent):** Planned interventions
- **EVN (Event):** Completed interventions

**Entry Relationships:**
- **COMP (has component):** Procedure Activity Acts, Medication Activities

### Health Status Evaluations and Outcomes Section - SHOULD

**Template ID:** `2.16.840.1.113883.10.20.22.2.61`

| Element | Description | Required |
|---------|-------------|----------|
| code | LOINC `11383-7` "Patient problem outcome" | Yes |
| title | Section title | Yes |
| text | Human-readable narrative | Yes |
| entry | Outcome Observation entries | May |

**Entry Template:** Outcome Observation `2.16.840.1.113883.10.20.22.4.144`

**Entry Relationships:**
- **GEVL (evaluates goal):** Links to Goal Observations
- **RSON (has reason):** Links to Interventions

## Conformance Requirements

### Document Level
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.1.15` and extension `2015-08-01`
2. **SHALL** contain exactly one `code` with code=`52521-2` from LOINC
3. **SHALL** contain exactly one `title`
4. **SHALL** contain exactly one `effectiveTime`
5. **SHALL** contain at least one `recordTarget`
6. **SHALL** contain at least one `author`
7. **SHALL** contain exactly one `custodian`
8. **SHOULD** contain at least one `documentationOf` for service event period

### StructuredBody
1. **SHALL** contain exactly one Health Concerns Section (V2) `2.16.840.1.113883.10.20.22.2.58`
2. **SHALL** contain exactly one Goals Section `2.16.840.1.113883.10.20.22.2.60`
3. **SHOULD** contain zero or one Interventions Section (V3) `2.16.840.1.113883.10.20.21.2.3`
4. **SHOULD** contain zero or one Health Status Evaluations and Outcomes Section `2.16.840.1.113883.10.20.22.2.61`
5. **SHALL NOT** contain Plan of Treatment Section (V2) `2.16.840.1.113883.10.20.22.2.10`

**Note:** The prohibition of Plan of Treatment Section is intentional - interventions should be documented in the Interventions Section instead.

## Document Context

The Care Plan Document is used in the following contexts:
- **Chronic disease management** - Ongoing care coordination for patients with chronic conditions
- **Care transitions** - Handoff documentation between care settings
- **Care coordination** - Integration of multiple provider plans
- **Patient-centered medical home** - Comprehensive care planning
- **Accountable Care Organizations** - Population health management

**Certification Requirement:** For ONC certification, Care Plan documents must include Health Status Evaluations and Outcomes Section and Interventions Section.

## Entry Relationship Patterns

Care Plan documents use specific relationship types to link related clinical information:

| typeCode | Relationship | Usage |
|----------|--------------|-------|
| DRIV | is derived from | Entries within sections |
| REFR | refers to | Health concerns reference problems |
| SPRT | has support | Supporting observations |
| RSON | has reason | Goals/interventions reference health concerns |
| COMP | has component | Intervention acts contain procedures |
| GEVL | evaluates goal | Outcomes evaluate goals |

## Special Cases

### Longitudinal Care Plan (Multiple Versions)

Care Plans should be versioned as they are updated:

```xml
<setId root="2.16.840.1.113883.19.5" extension="careplan-set-123"/>
<versionNumber value="2"/>
```

### Multidisciplinary Authorship

Multiple authors can be documented:

```xml
<author>
  <time value="20240115120000-0500"/>
  <assignedAuthor>
    <!-- Primary care physician -->
  </assignedAuthor>
</author>
<author>
  <time value="20240115130000-0500"/>
  <assignedAuthor>
    <!-- Care coordinator -->
  </assignedAuthor>
</author>
```

### Patient as Contributor

Document patient participation:

```xml
<participant typeCode="IND">
  <associatedEntity classCode="PAT">
    <id root="2.16.840.1.113883.4.1" extension="123-45-6789"/>
    <code code="ONESELF" codeSystem="2.16.840.1.113883.5.111"
          displayName="Self"/>
    <associatedPerson>
      <name>
        <given>Amy</given>
        <family>Shaw</family>
      </name>
    </associatedPerson>
  </associatedEntity>
</participant>
```

### Empty Sections with Null Flavor

If a required section has no data:

```xml
<section nullFlavor="NI">
  <templateId root="2.16.840.1.113883.10.20.22.2.58" extension="2015-08-01"/>
  <code code="75310-3" codeSystem="2.16.840.1.113883.6.1"/>
  <title>HEALTH CONCERNS</title>
  <text>No health concerns documented</text>
</section>
```

## Related Templates

| Template ID | Template Name | Usage |
|-------------|---------------|-------|
| 2.16.840.1.113883.10.20.22.2.58 | Health Concerns Section (V2) | Document patient concerns |
| 2.16.840.1.113883.10.20.22.2.60 | Goals Section | Document care goals |
| 2.16.840.1.113883.10.20.21.2.3 | Interventions Section (V3) | Document interventions |
| 2.16.840.1.113883.10.20.22.2.61 | Health Status Evaluations and Outcomes | Document outcomes |
| 2.16.840.1.113883.10.20.22.4.132 | Health Concern Act (V3) | Health concern entry |
| 2.16.840.1.113883.10.20.22.4.121 | Goal Observation | Goal entry |
| 2.16.840.1.113883.10.20.22.4.131 | Intervention Act | Intervention entry |
| 2.16.840.1.113883.10.20.22.4.144 | Outcome Observation | Outcome entry |

## References

- [C-CDA R2.1 Care Plan Specification](https://hl7.org/ccdasearch/templates/2.16.840.1.113883.10.20.22.1.15.html)
- [C-CDA R5.0 (STU5) Care Plan](https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CarePlan.html)
- [C-CDA on FHIR Care Plan Document](https://hl7.org/fhir/us/ccda/StructureDefinition-Care-Plan-Document.html)
- [HL7 C-CDA Example: Care Plan](https://github.com/HL7/C-CDA-Examples/blob/master/Documents/Care%20Plan/Care_Plan.xml)
- [ONC HealthIT Care Plan Certification](https://www.healthit.gov/test-method/care-plan)
- [Interventions Section Example](https://build.fhir.org/ig/HL7/CDA-ccda-2.1-sd/Binary-interventions-section-example.html)
