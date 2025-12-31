"""Code system OID to FHIR URI mapping utilities."""

from __future__ import annotations


class CodeSystemMapper:
    """Maps C-CDA OIDs to FHIR canonical URIs.

    This class provides bidirectional mapping between C-CDA OID-based code systems
    and FHIR canonical URIs as specified in the HL7 C-CDA on FHIR Implementation Guide.
    """

    # Standard OID to URI mappings from HL7 specifications
    OID_TO_URI = {
        # Code Systems
        "2.16.840.1.113883.6.1": "http://loinc.org",  # LOINC
        "2.16.840.1.113883.6.96": "http://snomed.info/sct",  # SNOMED CT
        "2.16.840.1.113883.6.88": "http://www.nlm.nih.gov/research/umls/rxnorm",  # RxNorm
        "2.16.840.1.113883.6.90": "http://hl7.org/fhir/sid/icd-10-cm",  # ICD-10-CM
        "2.16.840.1.113883.6.103": "http://hl7.org/fhir/sid/icd-9-cm",  # ICD-9-CM
        "2.16.840.1.113883.6.4": "http://hl7.org/fhir/sid/icd-10",  # ICD-10
        "2.16.840.1.113883.6.69": "http://hl7.org/fhir/sid/ndc",  # NDC
        "2.16.840.1.113883.6.12": "http://www.ama-assn.org/go/cpt",  # CPT
        "2.16.840.1.113883.12.292": "http://hl7.org/fhir/sid/cvx",  # CVX (Vaccines)
        "2.16.840.1.113883.3.26.1.1": "http://ncimeta.nci.nih.gov",  # NCI Thesaurus

        # Identifiers
        "2.16.840.1.113883.4.1": "http://hl7.org/fhir/sid/us-ssn",  # US SSN
        "2.16.840.1.113883.4.6": "http://hl7.org/fhir/sid/us-npi",  # US NPI

        # HL7 V3 Code Systems
        "2.16.840.1.113883.5.1": "http://terminology.hl7.org/CodeSystem/v3-AdministrativeGender",
        "2.16.840.1.113883.5.2": "http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
        "2.16.840.1.113883.5.4": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "2.16.840.1.113883.5.6": "http://terminology.hl7.org/CodeSystem/v3-ActClass",
        "2.16.840.1.113883.5.8": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
        "2.16.840.1.113883.5.25": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
        "2.16.840.1.113883.5.60": "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityMode",
        "2.16.840.1.113883.5.61": "http://terminology.hl7.org/CodeSystem/v3-LanguageAbilityProficiency",
        "2.16.840.1.113883.5.83": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
        "2.16.840.1.113883.5.88": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",  # ParticipationFunction → v3-RoleCode
        "2.16.840.1.113883.5.111": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
        "2.16.840.1.113883.5.140": "http://terminology.hl7.org/CodeSystem/v3-TribalEntityUS",  # Tribal Entity US
        "2.16.840.1.113883.5.1063": "http://terminology.hl7.org/CodeSystem/v3-ObservationValue",

        # CDC Race and Ethnicity
        "2.16.840.1.113883.6.238": "urn:oid:2.16.840.1.113883.6.238",  # CDC Race/Ethnicity (keep as OID)

        # CDC NHSN Healthcare Service Location (HSLOC)
        "2.16.840.1.113883.6.259": "https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html",

        # NUCC Provider Taxonomy
        "2.16.840.1.113883.6.101": "http://nucc.org/provider-taxonomy",

        # HL7 V2 Tables
        "2.16.840.1.113883.12.112": "http://terminology.hl7.org/CodeSystem/discharge-disposition",
        "2.16.840.1.113883.12.292": "http://hl7.org/fhir/sid/cvx",

        # FHIR CodeSystems (for when C-CDA uses FHIR codes)
        # Note: Some C-CDA documents incorrectly use ValueSet OIDs as codeSystem
        # We map both the ValueSet OID and CodeSystem canonical URI for compatibility
        "2.16.840.1.113883.4.642.3.273": "http://terminology.hl7.org/CodeSystem/goal-priority",  # Goal Priority (R4B ValueSet OID)
        "2.16.840.1.113883.4.642.3.275": "http://terminology.hl7.org/CodeSystem/goal-priority",  # Goal Priority (legacy/test OID)
        "2.16.840.1.113883.4.642.3.251": "http://terminology.hl7.org/CodeSystem/goal-achievement",  # Goal Achievement (legacy/test OID)
        "2.16.840.1.113883.4.642.3.1374": "http://terminology.hl7.org/CodeSystem/goal-achievement",  # Goal Achievement (R4B ValueSet OID)
        "2.16.840.1.113883.5.1076": "http://terminology.hl7.org/CodeSystem/v3-ReligiousAffiliation",  # Religious Affiliation
        "2.16.840.1.113883.4.642.4.2038": "http://hl7.org/fhir/sex-parameter-for-clinical-use",  # Sex Parameter for Clinical Use
    }

    def __init__(self, custom_mappings: dict[str, str] | None = None):
        """Initialize the code system mapper.

        Args:
            custom_mappings: Optional additional OID to URI mappings to add
        """
        self.mappings = self.OID_TO_URI.copy()
        if custom_mappings:
            self.mappings.update(custom_mappings)

        # Create reverse mapping for URI to OID
        self.uri_to_oid = {uri: oid for oid, uri in self.mappings.items()}

    def oid_to_uri(self, oid: str) -> str:
        """Convert an OID to a FHIR canonical URI.

        Per FHIR R4B Terminologies specification:
        "If a URI is defined here, it SHALL be used in preference to any other identifying mechanisms."
        https://hl7.org/fhir/R4B/terminologies-systems.html

        Per C-CDA on FHIR IG:
        "For OIDs that have no URI equivalent is known, add the urn:oid: prefix to OID"
        https://build.fhir.org/ig/HL7/ccda-on-fhir/mappingGuidance.html

        Args:
            oid: The OID to convert (e.g., "2.16.840.1.113883.6.1")

        Returns:
            The FHIR canonical URI (e.g., "http://loinc.org")
            If the OID is not found, returns "urn:oid:{oid}"
        """
        if not oid:
            return ""

        # If already a URI (starts with http/https), return as-is
        if oid.startswith('http://') or oid.startswith('https://'):
            return oid

        # Check for known mapping
        if oid in self.mappings:
            return self.mappings[oid]

        # Unknown OID - return with urn:oid: prefix per C-CDA on FHIR IG
        return f"urn:oid:{oid}"

    def oid_to_identifier_system(self, oid: str) -> str | None:
        """Convert an OID to a system URI for use in Identifier.system.

        Unlike oid_to_uri(), this method returns urn:oid: format for unmapped OIDs
        because Identifier.system allows urn:oid: format (unlike Coding.system).

        Per FHIR R4B:
        - Coding.system: SHALL use canonical URI when it exists (urn:oid: NOT acceptable)
        - Identifier.system: urn:oid: format IS acceptable and widely used

        Args:
            oid: The OID to convert (e.g., "2.16.840.1.113883.19.5")

        Returns:
            The FHIR canonical URI if known, otherwise urn:oid:{oid}
        """
        if not oid:
            return None

        # Check for known mapping - prefer canonical URI
        if oid in self.mappings:
            return self.mappings[oid]

        # Unknown OID - return urn:oid: format (acceptable for Identifier.system)
        return f"urn:oid:{oid}"

    def uri_to_oid(self, uri: str) -> str:
        """Convert a FHIR canonical URI to an OID.

        Args:
            uri: The FHIR canonical URI

        Returns:
            The OID, or the URI if no mapping exists
        """
        if not uri:
            return ""

        # Check for urn:oid: prefix
        if uri.startswith("urn:oid:"):
            return uri[8:]  # Remove "urn:oid:" prefix

        # Check for known reverse mapping
        if uri in self.uri_to_oid:
            return self.uri_to_oid[uri]

        # Return URI as-is if no mapping found
        return uri

    def add_mapping(self, oid: str, uri: str) -> None:
        """Add a custom OID to URI mapping.

        Args:
            oid: The OID
            uri: The FHIR canonical URI
        """
        self.mappings[oid] = uri
        self.uri_to_oid[uri] = oid
