# C-CDA to FHIR Converter - Comprehensive Stress Test Report

**Generated:** /Users/ramin/work/nurra/c-cda-to-fhir

## Executive Summary

- **Total C-CDA Files Tested:** 828
- **Successful Conversions:** 0
- **Failed Conversions:** 828
- **Success Rate:** 0.00%
- **Total FHIR Resources Created:** 0
- **Average Conversion Time:** 4.5ms

## Error Analysis

### Errors by Type

- **MalformedXMLError**: 507 files
- **ValueError**: 140 files
- **AttributeError**: 104 files
- **ValidationError**: 40 files
- **UnknownTypeError**: 37 files

### Errors by Pattern

- **Document fragment (not full ClinicalDocument)**: 224 files
- **XML namespace issue**: 198 files
- **FHIR validation error**: 116 files
- **Missing attribute/method**: 104 files
- **Other**: 101 files
- **Missing required C-CDA field**: 78 files
- **Missing identifiers**: 7 files

### Sample Errors by Type


#### MalformedXMLError

**File:** `C-CDA-Examples/Allergies/Allergy to food egg/Allergy to food egg(C-CDA2.1).xml`
**Error:** Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 76, column 147 (<string>, line 76)

**File:** `C-CDA-Examples/Allergies/Allergy to latex/Allergy to specific substance latex(C-CDA2.1).xml`
**Error:** Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 76, column 177 (<string>, line 76)

**File:** `C-CDA-Examples/Allergies/Allergy to specific drug Codeine/Allergy to specific drug Codeine(C-CDA2.1).xml`
**Error:** Invalid XML syntax: Namespace prefix xsi for type on value is not defined, line 126, column 69 (<string>, line 126)


#### ValueError

**File:** `C-CDA-Examples/Documents/Transfer Summary/Transfer_Summary.xml`
**Error:** Invalid templateId - expected 2.16.840.1.113883.10.20.22.4.32

**File:** `ccda-samples/Allscripts FollowMyHealth/Inpatient Summary-rebeccalarson.xml`
**Error:** Location name is required (playingEntity/name)

**File:** `ccda-samples/Amrita/Adirondack_Susanne_808080_CCD_201709180916.xml`
**Error:** Location name is required (playingEntity/name)


#### AttributeError

**File:** `C-CDA-Examples/Documents/CCD/CCD 2/CCD.xml`
**Error:** 'Composition' object has no attribute 'resource_type'

**File:** `C-CDA-Examples/Documents/Care Plan/Care_Plan.xml`
**Error:** 'Composition' object has no attribute 'resource_type'

**File:** `C-CDA-Examples/Documents/Diagnostic Imaging Report/Diagnostic_Imaging_Report.xml`
**Error:** 'Composition' object has no attribute 'resource_type'


#### ValidationError

**File:** `ccda-samples/360 Oncology/Jeremy_Bates_health_summary.xml`
**Error:** 2 validation errors for Bundle
entry.9.resource.context.period.end
  Value error, Datetime must be timezone aware if it has a time component. [type=value_error, input_value='2015-07-22T23:00:00', inpu

**File:** `ccda-samples/Advanced Technologies Group/SLI_CCD_b2Cecilia_ATG_ATGEHR_10162017.xml`
**Error:** 1 validation error for Bundle
entry.0.resource.date
  Value for the field 'date' is required. [type=model_field_validation.missing, input_value=None, input_type=NoneType]

**File:** `ccda-samples/Advanced Technologies Group/SLI_CCD_b2MyraJones_ATG_ATGEHR_10162017.xml`
**Error:** 1 validation error for Bundle
entry.0.resource.date
  Value for the field 'date' is required. [type=model_field_validation.missing, input_value=None, input_type=NoneType]


#### UnknownTypeError

**File:** `ccda-samples/360 Oncology/Alice_Newman_health_summary Delegate.xml`
**Error:** Unknown xsi:type 'CO' for element 'value'. This may indicate a new data type that needs to be added to the parser.

**File:** `ccda-samples/Allscripts FollowMyHealth/Discharge Summary-rebeccaangles.xml`
**Error:** Unknown xsi:type 'CO' for element 'value'. This may indicate a new data type that needs to be added to the parser.

**File:** `ccda-samples/Allscripts FollowMyHealth/Inpatient Referral Summary-lindsaypitt.xml`
**Error:** Unknown xsi:type 'CO' for element 'value'. This may indicate a new data type that needs to be added to the parser.


## US Core Profile Compliance

No successful conversions to analyze.


## CCDA on FHIR Mapping Compliance

No successful conversions to analyze.


## Recommendations

### Priority Fixes

1. **Document fragment (not full ClinicalDocument)** (224 files, 27.1% of failures)
2. **XML namespace issue** (198 files, 23.9% of failures)
3. **FHIR validation error** (116 files, 14.0% of failures)
4. **Missing attribute/method** (104 files, 12.6% of failures)
5. **Other** (101 files, 12.2% of failures)