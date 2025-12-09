# C-CDA: Immunization Activity

## Overview

Immunizations in C-CDA are documented using the Immunization Activity template within the Immunizations Section. This template records information about the administration of vaccines and immunizations to a patient.

## Template Information

| Attribute | Value |
|-----------|-------|
| Immunization Activity Template ID | `2.16.840.1.113883.10.20.22.4.52` |
| Template Version | 2015-08-01 |
| Official URL | `http://hl7.org/cda/us/ccda/StructureDefinition/ImmunizationActivity` |
| Section Template ID (entries required) | `2.16.840.1.113883.10.20.22.2.2.1` |
| Section Template ID (entries optional) | `2.16.840.1.113883.10.20.22.2.2` |
| LOINC Code | 11369-6 |
| LOINC Display | History of Immunization Narrative |

## Mood Code Support

The template supports two mood codes:
- **EVN (Event)**: Immunizations actually received
- **INT (Intent)**: Immunizations a clinician intends a patient to receive

## Location in Document

```
ClinicalDocument
└── component
    └── structuredBody
        └── component
            └── section [Immunizations Section]
                ├── templateId [@root='2.16.840.1.113883.10.20.22.2.2.1']
                ├── code [@code='11369-6']
                └── entry
                    └── substanceAdministration [Immunization Activity]
                        ├── templateId [@root='2.16.840.1.113883.10.20.22.4.52']
                        ├── consumable/manufacturedProduct/manufacturedMaterial
                        └── performer
```

## XML Structure

```xml
<section>
  <templateId root="2.16.840.1.113883.10.20.22.2.2.1" extension="2015-08-01"/>
  <code code="11369-6" codeSystem="2.16.840.1.113883.6.1"
        displayName="History of Immunization Narrative"/>
  <title>IMMUNIZATIONS</title>
  <text>
    <table>
      <thead>
        <tr><th>Vaccine</th><th>Date</th><th>Status</th></tr>
      </thead>
      <tbody>
        <tr>
          <td ID="imm1">Influenza, seasonal, injectable</td>
          <td>November 1, 2020</td>
          <td>Completed</td>
        </tr>
      </tbody>
    </table>
  </text>

  <entry typeCode="DRIV">
    <substanceAdministration classCode="SBADM" moodCode="EVN" negationInd="false">
      <templateId root="2.16.840.1.113883.10.20.22.4.52" extension="2015-08-01"/>
      <id root="e6f1ba43-c0ed-4b9b-9f12-f435d8ad8f92"/>

      <text>
        <reference value="#imm1"/>
      </text>

      <!-- Status -->
      <statusCode code="completed"/>

      <!-- Administration Date -->
      <effectiveTime value="20201101"/>

      <!-- Route of Administration -->
      <routeCode code="C28161" codeSystem="2.16.840.1.113883.3.26.1.1"
                 displayName="Intramuscular injection"/>

      <!-- Approach Site (Body Site) -->
      <approachSiteCode code="368208006" codeSystem="2.16.840.1.113883.6.96"
                        displayName="Left upper arm structure"/>

      <!-- Dose Quantity -->
      <doseQuantity value="0.5" unit="mL"/>

      <!-- Vaccine Product -->
      <consumable>
        <manufacturedProduct classCode="MANU">
          <templateId root="2.16.840.1.113883.10.20.22.4.54" extension="2014-06-09"/>
          <manufacturedMaterial>
            <!-- CVX Code -->
            <code code="140" codeSystem="2.16.840.1.113883.12.292"
                  displayName="Influenza, seasonal, injectable, preservative free">
              <originalText>
                <reference value="#imm1"/>
              </originalText>
              <!-- NDC Translation -->
              <translation code="49281-0703-55" codeSystem="2.16.840.1.113883.6.69"
                           displayName="Fluzone Quadrivalent"/>
            </code>
            <lotNumberText>AAJN11K</lotNumberText>
          </manufacturedMaterial>
          <manufacturerOrganization>
            <name>Sanofi Pasteur Inc</name>
          </manufacturerOrganization>
        </manufacturedProduct>
      </consumable>

      <!-- Performer -->
      <performer>
        <assignedEntity>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
          <addr nullFlavor="UNK"/>
          <telecom nullFlavor="UNK"/>
          <assignedPerson>
            <name>
              <given>Adam</given>
              <family>Careful</family>
              <suffix>MD</suffix>
            </name>
          </assignedPerson>
          <representedOrganization>
            <id root="2.16.840.1.113883.19.5.9999.1393"/>
            <name>Community Health and Hospitals</name>
          </representedOrganization>
        </assignedEntity>
      </performer>

      <!-- Author -->
      <author>
        <templateId root="2.16.840.1.113883.10.20.22.4.119"/>
        <time value="20201101"/>
        <assignedAuthor>
          <id root="2.16.840.1.113883.4.6" extension="1234567890"/>
        </assignedAuthor>
      </author>

      <!-- Indication (reason for immunization) -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.19" extension="2014-06-09"/>
          <id root="db734647-fc99-424c-a864-7e3cda82e704"/>
          <code code="59785-6" codeSystem="2.16.840.1.113883.6.1"
                displayName="Indication for immunization"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="195967001" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Routine immunization"/>
        </observation>
      </entryRelationship>

      <!-- Immunization Refusal Reason (if refused) -->
      <entryRelationship typeCode="RSON">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.53"/>
          <id root="..."/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="591000119102" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Vaccine refused by patient"/>
        </observation>
      </entryRelationship>

      <!-- Reaction Observation (if any) -->
      <entryRelationship typeCode="MFST" inversionInd="true">
        <observation classCode="OBS" moodCode="EVN">
          <templateId root="2.16.840.1.113883.10.20.22.4.9" extension="2014-06-09"/>
          <id root="..."/>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <statusCode code="completed"/>
          <value xsi:type="CD" code="39579001" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Anaphylaxis"/>
        </observation>
      </entryRelationship>

      <!-- Precondition (eligibility criteria checked) -->
      <precondition typeCode="PRCN">
        <criterion>
          <code code="ASSERTION" codeSystem="2.16.840.1.113883.5.4"/>
          <value xsi:type="CD" code="171279008" codeSystem="2.16.840.1.113883.6.96"
                 displayName="Immunization due"/>
        </criterion>
      </precondition>

    </substanceAdministration>
  </entry>
</section>
```

## Element Details

### substanceAdministration/@negationInd

Indicates whether the immunization was NOT given.

| Value | Description |
|-------|-------------|
| false | Immunization was administered |
| true | Immunization was NOT administered (refused, contraindicated) |

### statusCode

The status of the immunization activity.

| Code | Display | Description |
|------|---------|-------------|
| completed | Completed | Immunization was administered |
| active | Active | Immunization is in progress |
| aborted | Aborted | Immunization was stopped |
| cancelled | Cancelled | Immunization was cancelled |

### effectiveTime

When the immunization was administered.

| Format | Description |
|--------|-------------|
| value="YYYYMMDD" | Date of administration |
| value="YYYYMMDDHHMM" | Date and time |

### routeCode

How the vaccine was administered.

**Route Codes (NCI Thesaurus):**
| Code | Display |
|------|---------|
| C28161 | Intramuscular injection |
| C38299 | Subcutaneous injection |
| C38276 | Intravenous injection |
| C38284 | Nasal |
| C38288 | Oral |
| C38287 | Intradermal |

**Code System:** `2.16.840.1.113883.3.26.1.1` (NCI Thesaurus)

### approachSiteCode

Body site where vaccine was administered.

**Common Body Site Codes (SNOMED):**
| Code | Display |
|------|---------|
| 368208006 | Left upper arm structure |
| 368209003 | Right upper arm structure |
| 61396006 | Left thigh |
| 11207009 | Right thigh |
| 46862004 | Buttock structure |

### doseQuantity

Amount of vaccine administered. **SHOULD** be documented with units.

| Attribute | Description |
|-----------|-------------|
| @value | Numeric amount |
| @unit | Unit of measure (mL, mg, etc.) |

**Critical Constraint:** If doseQuantity/@unit is present, then administrationUnitCode SHALL NOT be present.

### consumable/manufacturedProduct/manufacturedMaterial

The vaccine product details.

| Element | Description |
|---------|-------------|
| code | CVX vaccine code |
| code/translation | NDC or other product codes |
| lotNumberText | Vaccine lot number |

**CVX Code System:**
| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.12.292 | `http://hl7.org/fhir/sid/cvx` | CVX (Vaccine Administered) |

**Common CVX Codes:**
| Code | Display |
|------|---------|
| 140 | Influenza, seasonal, injectable, preservative free |
| 141 | Influenza, seasonal, injectable |
| 08 | Hepatitis B vaccine |
| 10 | IPV (Polio) |
| 20 | DTaP |
| 21 | Varicella |
| 03 | MMR |
| 33 | Pneumococcal |
| 115 | Tdap |
| 207 | COVID-19, mRNA, LNP-S |
| 208 | COVID-19, mRNA, LNP-S (Pfizer) |
| 212 | COVID-19, vector-nr, rS-Ad26 (J&J) |

**NDC Code System:**
| OID | URI | Name |
|-----|-----|------|
| 2.16.840.1.113883.6.69 | `http://hl7.org/fhir/sid/ndc` | National Drug Code |

### manufacturerOrganization

The vaccine manufacturer.

| Element | Description |
|---------|-------------|
| name | Manufacturer name |

**Common Vaccine Manufacturers:**
| Name |
|------|
| Sanofi Pasteur Inc |
| Merck Sharp & Dohme Corp |
| Pfizer Inc |
| GlaxoSmithKline |
| Moderna US Inc |
| Janssen Products LP |

### performer

Who administered the vaccine.

| Element | Description |
|---------|-------------|
| assignedEntity/id | Provider identifier (NPI) |
| assignedEntity/assignedPerson/name | Provider name |
| assignedEntity/representedOrganization | Organization |

### entryRelationship[@typeCode='RSON'] (Indication)

The reason for the immunization.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.19` |
| code | 59785-6 (Indication for immunization) from LOINC |
| value | Reason code (SNOMED) |

**Common Indication Codes (SNOMED):**
| Code | Display |
|------|---------|
| 195967001 | Routine immunization |
| 171257003 | Travel immunization |
| 281657000 | Occupational immunization |
| 428119001 | Procedure required before treatment |

### Immunization Refusal Reason

When negationInd="true", documents why immunization was not given.

| Element | Description |
|---------|-------------|
| templateId | `2.16.840.1.113883.10.20.22.4.53` |
| code | ASSERTION |
| value | Refusal reason code |

**Refusal Reason Codes (SNOMED):**
| Code | Display |
|------|---------|
| 591000119102 | Vaccine refused by patient |
| 407598009 | Contraindicated |
| 183944003 | Not indicated |
| 213257006 | Declined |
| 266758009 | Immunization declined |

## Conformance Requirements

### Immunization Activity
1. **SHALL** contain exactly one `templateId` with root `2.16.840.1.113883.10.20.22.4.52`
2. **SHALL** contain exactly one `classCode` = SBADM (fixed)
3. **SHALL** contain exactly one `moodCode` (EVN or INT) - Required binding to MoodCodeEvnInt
4. **SHALL** contain at least one `id`
5. **SHALL** contain exactly one `statusCode` - Required binding to ActStatus
6. **SHALL** contain exactly one `effectiveTime`
7. **SHALL** contain exactly one `consumable`
8. `consumable` **SHALL** contain exactly one `manufacturedProduct`
9. `manufacturedProduct` **SHALL** contain exactly one `manufacturedMaterial`
10. `manufacturedMaterial` **SHALL** contain exactly one `code`
11. **SHALL** contain `negationInd` attribute (true if immunization not given)
12. **SHOULD** contain `performer`
13. **SHOULD** contain `author` participation
14. **SHOULD** contain `doseQuantity` with units
15. **MAY** contain `routeCode` - Required binding to SPL Drug Route of Administration
16. **MAY** contain `approachSiteCode` - Required binding to Body Site Value Set
17. **MAY** contain `administrationUnitCode` - Required binding to AdministrationUnitDoseForm

## Terminology Bindings

| Element | Value Set | Binding Strength |
|---------|-----------|------------------|
| moodCode | MoodCodeEvnInt | Required |
| statusCode | ActStatus | Required |
| routeCode | SPL Drug Route of Administration | Required |
| approachSiteCode | Body Site Value Set | Required |
| administrationUnitCode | AdministrationUnitDoseForm | Required |

## CDC Documentation Requirements

When available, immunization records must include:
- Administration date
- Vaccine manufacturer and lot number
- Administrator name/title and facility address
- Vaccine Information Statement (VIS) with dates

## Optional Entry Relationships

The template supports nested entries for:
- Indication observations (reason for immunization)
- Instruction observations
- Medication supply orders and dispensing records
- Adverse reaction observations
- Immunization non-given reasons (when negationInd=true)
- Substance administered act sequences

## References

- C-CDA R2.1 Implementation Guide Section 3.44 (Immunization Activity)
- C-CDA R5.0 (STU5 Ballot): https://build.fhir.org/ig/HL7/CDA-ccda/
- HL7 C-CDA Templates: http://www.hl7.org/ccdasearch/
- CVX Code Set: https://www2a.cdc.gov/vaccines/iis/iisstandards/vaccines.asp?rpt=cvx
- NDC Directory: https://www.fda.gov/drugs/drug-approvals-and-databases/national-drug-code-directory
