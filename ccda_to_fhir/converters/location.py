"""Location converter: C-CDA Service Delivery Location to FHIR Location resource.

Converts C-CDA Service Delivery Location (template 2.16.840.1.113883.10.20.22.4.32)
to FHIR Location resource compliant with US Core Location profile.

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ServiceDeliveryLocation.html
- FHIR: https://hl7.org/fhir/R4B/location.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition/us-core-location
- Mapping: docs/mapping/16-location.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import ADDRESS_USE_MAP, TELECOM_USE_MAP, FHIRCodes
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.datatypes import AD, CE, II, TEL
    from ccda_to_fhir.ccda.models.participant import ParticipantRole


class LocationConverter(BaseConverter["ParticipantRole"]):
    """Convert C-CDA Service Delivery Location to FHIR Location.

    Handles mapping from C-CDA Service Delivery Location template
    (2.16.840.1.113883.10.20.22.4.32) to US Core Location profile.
    """

    # Service Delivery Location template OID
    SERVICE_DELIVERY_LOCATION_TEMPLATE = "2.16.840.1.113883.10.20.22.4.32"

    # US Core Location profile
    US_CORE_LOCATION_PROFILE = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-location"

    def convert(self, participant_role: ParticipantRole) -> FHIRResourceDict:
        """Convert Service Delivery Location to Location resource.

        Args:
            participant_role: C-CDA ParticipantRole with classCode='SDLOC'

        Returns:
            FHIR Location resource as dictionary

        Raises:
            ValueError: If required elements are missing or invalid
        """
        # Validate classCode (fundamental requirement)
        self._validate_class_code(participant_role)

        # Note: Template ID validation is intentionally lenient to handle real-world
        # C-CDA documents that may omit or use non-standard template IDs.
        # The classCode="SDLOC" validation above is sufficient to identify
        # Service Delivery Location elements.

        location: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.LOCATION,
        }

        # Add US Core profile
        location["meta"] = {
            "profile": [self.US_CORE_LOCATION_PROFILE]
        }

        # Map name first (needed for synthetic ID generation)
        name = self._extract_name(participant_role)
        location["name"] = name

        # Map address early (needed for synthetic ID generation)
        address = None
        if participant_role.addr:
            address = self._convert_address(participant_role.addr)

        # Generate ID from identifiers, or create synthetic ID if missing
        if participant_role.id:
            location["id"] = self._generate_location_id(participant_role.id)
        else:
            # Generate synthetic ID from name and address for locations without explicit IDs
            # This handles real-world C-CDA documents that omit location IDs
            location["id"] = self._generate_synthetic_location_id(name, address)

        # Map identifiers (NPI, CLIA, NAIC, etc.)
        identifiers = self._convert_identifiers(participant_role.id)
        if identifiers:
            location["identifier"] = identifiers

        # Map status (default: active)
        location["status"] = "active"

        # Map mode (instance for specific locations, kind for location types)
        location["mode"] = self._determine_mode(participant_role.code)

        # Map type (facility type - optional per FHIR R4B)
        if participant_role.code:
            location_type = self._convert_type(participant_role.code)
            if location_type:
                location["type"] = [location_type]
        else:
            # Log C-CDA spec violation (code is required per C-CDA, but we accept it for real-world compatibility)
            from ccda_to_fhir.logging_config import get_logger
            logger = get_logger(__name__)
            logger.warning(
                "Missing participantRole/code (required by C-CDA spec). "
                "Omitting Location.type. May indicate C-CDA data quality issue."
            )

        # Map physicalType (physical form of location - inferred from type code)
        physical_type = self._infer_physical_type(participant_role.code)
        if physical_type:
            location["physicalType"] = physical_type

        # Map telecom (phone, fax, email)
        if participant_role.telecom:
            telecom_list = self._convert_telecom(participant_role.telecom)
            if telecom_list:
                location["telecom"] = telecom_list

        # Add address to location if it exists (already extracted above for ID generation)
        if address:
            location["address"] = address

        # Map managingOrganization (US Core Must Support)
        managing_org = self._get_managing_organization_reference(participant_role)
        if managing_org:
            location["managingOrganization"] = managing_org

        return location

    def _validate_class_code(self, participant_role: ParticipantRole) -> None:
        """Validate that classCode is SDLOC (Service Delivery Location).

        Args:
            participant_role: ParticipantRole to validate

        Raises:
            ValueError: If classCode is not SDLOC
        """
        if participant_role.class_code != "SDLOC":
            raise ValueError(
                f"Cannot convert ParticipantRole to Location: classCode '{participant_role.class_code}' "
                f"is not 'SDLOC' (Service Delivery Location). ParticipantRole with this classCode represents "
                f"a different type of entity (e.g., MANU=Manufactured Product) and should not be converted to Location."
            )

    def _generate_location_id(self, identifiers: list[II]) -> str:
        """Generate FHIR Location ID from C-CDA identifiers.

        Uses standard ID generation with hashing for consistency across all converters.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated Location ID
        """
        # Use first valid identifier
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return self.generate_resource_id(
            root=root,
            extension=extension,
            resource_type="location"
        )

    def _generate_synthetic_location_id(self, name: str, address: JSONObject | None) -> str:
        """Generate synthetic FHIR Location ID from name and address.

        Used when C-CDA location participant has no explicit ID element.
        Creates a deterministic ID based on location characteristics.

        Args:
            name: Location name
            address: FHIR address object (if available)

        Returns:
            Generated synthetic Location ID
        """
        import hashlib

        # Build a unique string from available identifying information
        id_parts = [name]

        if address:
            if "city" in address:
                id_parts.append(address["city"])
            if "state" in address:
                id_parts.append(address["state"])
            if "line" in address and address["line"]:
                # Use first line
                id_parts.append(address["line"][0])

        # Create deterministic hash
        combined = "|".join(id_parts)
        hash_value = hashlib.sha256(combined.encode()).hexdigest()[:16]

        return f"location-{hash_value}"

    def _convert_identifiers(self, identifiers: list[II] | None) -> list[JSONObject]:
        """Convert C-CDA identifiers to FHIR identifiers with special handling.

        Special OID mappings:
        - 2.16.840.1.113883.4.6 → http://hl7.org/fhir/sid/us-npi (NPI)
        - 2.16.840.1.113883.4.7 → urn:oid:... (CLIA)
        - 2.16.840.1.113883.6.300 → urn:oid:... (NAIC)
        - Others → urn:oid:...

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            List of FHIR identifier objects
        """
        if not identifiers:
            return []

        fhir_identifiers: list[JSONObject] = []

        for identifier in identifiers:
            # Skip nullFlavor identifiers (handled separately if needed)
            if identifier.null_flavor:
                # Optional: Include nullFlavor representation
                fhir_identifiers.append({
                    "system": "http://terminology.hl7.org/CodeSystem/v3-NullFlavor",
                    "value": identifier.null_flavor
                })
                continue

            if not identifier.root:
                continue

            fhir_identifier = self.create_identifier(
                root=identifier.root,
                extension=identifier.extension
            )

            if fhir_identifier:
                fhir_identifiers.append(fhir_identifier)

        return fhir_identifiers

    def _extract_name(self, participant_role: ParticipantRole) -> str:
        """Extract facility name with fallback strategies.

        Attempts to extract location name using the following priority:
        1. playingEntity/name (preferred, from C-CDA)
        2. "Location at {address}" (if address available)
        3. "Location {id}" (if identifier available)
        4. "Unknown Location" (final fallback)

        This ensures compatibility with real-world C-CDA documents that may
        omit location names while still creating valid FHIR Location resources.

        Args:
            participant_role: C-CDA ParticipantRole

        Returns:
            Facility name string (never None)
        """
        # Strategy 1: Try playingEntity/name (preferred)
        if participant_role.playing_entity and participant_role.playing_entity.name:
            names = participant_role.playing_entity.name

            # Handle single name (string)
            if isinstance(names, str):
                return names

            # Handle list of names
            if isinstance(names, list) and len(names) > 0:
                first_name = names[0]

                # Handle string in list
                if isinstance(first_name, str):
                    return first_name

                # Handle ON (OrganizationName) object
                if hasattr(first_name, "value") and first_name.value:
                    return first_name.value

                # Fallback to string representation
                name_str = str(first_name) if first_name else None
                if name_str:
                    return name_str

        # Strategy 2: Fallback to address
        if participant_role.addr:
            addr_parts = []
            for addr in participant_role.addr:
                # Extract street address (first line only)
                if addr.street_address_line and len(addr.street_address_line) > 0:
                    street = addr.street_address_line[0]
                    # Handle string or object with value attribute
                    if isinstance(street, str):
                        addr_parts.append(street)
                    elif hasattr(street, "value") and street.value:
                        addr_parts.append(street.value)

                # Extract city
                if addr.city:
                    if isinstance(addr.city, str):
                        addr_parts.append(addr.city)
                    elif hasattr(addr.city, "value") and addr.city.value:
                        addr_parts.append(addr.city.value)

            if addr_parts:
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.info(
                    "Location name missing (playingEntity/name not found). "
                    f"Using address-based fallback: 'Location at {', '.join(addr_parts)}'"
                )
                return f"Location at {', '.join(addr_parts)}"

        # Strategy 3: Fallback to ID
        if participant_role.id and len(participant_role.id) > 0:
            first_id = participant_role.id[0]
            if first_id.extension:
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.info(
                    "Location name missing (playingEntity/name and address not found). "
                    f"Using ID-based fallback: 'Location {first_id.extension}'"
                )
                return f"Location {first_id.extension}"
            elif first_id.root:
                # Use last segment of OID for readability
                root_parts = first_id.root.split(".")
                fallback_name = f"Location {root_parts[-1]}"
                from ccda_to_fhir.logging_config import get_logger
                logger = get_logger(__name__)
                logger.info(
                    "Location name missing (playingEntity/name and address not found). "
                    f"Using ID-based fallback: '{fallback_name}'"
                )
                return fallback_name

        # Strategy 4: Final fallback
        from ccda_to_fhir.logging_config import get_logger
        logger = get_logger(__name__)
        logger.warning(
            "Location name missing (no name, address, or ID found). "
            "Using generic fallback: 'Unknown Location'. "
            "This may indicate incomplete C-CDA data."
        )
        return "Unknown Location"

    def _convert_type(self, code: CE) -> JSONObject:
        """Convert facility type code to FHIR Location.type CodeableConcept.

        Supports multiple code systems:
        - HSLOC: 2.16.840.1.113883.6.259 → https://www.cdc.gov/nhsn/cdaportal/terminology/codesystem/hsloc.html
        - SNOMED CT: 2.16.840.1.113883.6.96 → http://snomed.info/sct
        - RoleCode: 2.16.840.1.113883.5.111 → http://terminology.hl7.org/CodeSystem/v3-RoleCode
        - CMS POS: URL → same URL

        Args:
            code: C-CDA CE (CodedElement) with facility type

        Returns:
            FHIR CodeableConcept for Location.type
        """
        if not code or not code.code:
            return {}

        codeable_concept: JSONObject = {}
        codings: list[JSONObject] = []

        # Primary coding
        if code.code and code.code_system:
            primary_coding = self._create_coding(code)
            if primary_coding:
                codings.append(primary_coding)

        # Translation codings
        if hasattr(code, "translation") and code.translation:
            for trans in code.translation:
                trans_coding = self._create_coding(trans)
                if trans_coding:
                    codings.append(trans_coding)

        if codings:
            codeable_concept["coding"] = codings

        # Original text
        if hasattr(code, "original_text") and code.original_text:
            codeable_concept["text"] = code.original_text

        return codeable_concept

    def _create_coding(self, code: CE) -> JSONObject:
        """Create a FHIR Coding from C-CDA CE.

        Args:
            code: C-CDA CodedElement

        Returns:
            FHIR Coding object
        """
        if not code.code:
            return {}

        coding: JSONObject = {}

        # Map code system OID to FHIR URI
        if code.code_system:
            coding["system"] = self.map_oid_to_uri(code.code_system)

        coding["code"] = code.code

        if code.display_name:
            coding["display"] = code.display_name

        return coding

    def _convert_telecom(self, telecoms: list[TEL] | TEL) -> list[JSONObject]:
        """Convert C-CDA telecom to FHIR ContactPoint.

        Parses URI schemes (tel:, fax:, mailto:, http:) and maps to FHIR system codes.

        Args:
            telecoms: List of C-CDA TEL or single TEL

        Returns:
            List of FHIR ContactPoint objects
        """
        fhir_telecom: list[JSONObject] = []

        # Normalize to list
        telecom_list = telecoms if isinstance(telecoms, list) else [telecoms]

        for telecom in telecom_list:
            if not telecom.value:
                continue

            contact_point: JSONObject = {}

            # Parse value (tel:+1..., mailto:..., fax:..., http://...)
            value = telecom.value
            if value.startswith("tel:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value[4:]  # Remove "tel:" prefix
            elif value.startswith("mailto:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.EMAIL
                contact_point["value"] = value[7:]  # Remove "mailto:" prefix
            elif value.startswith("fax:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.FAX
                contact_point["value"] = value[4:]  # Remove "fax:" prefix
            elif value.startswith("http:") or value.startswith("https:"):
                contact_point["system"] = FHIRCodes.ContactPointSystem.URL
                contact_point["value"] = value
            else:
                # Unknown format, store as-is (assume phone if no prefix)
                contact_point["system"] = FHIRCodes.ContactPointSystem.PHONE
                contact_point["value"] = value

            # Map use code (HP = home, WP = work, etc.)
            if telecom.use:
                fhir_use = TELECOM_USE_MAP.get(telecom.use)
                if fhir_use:
                    contact_point["use"] = fhir_use

            if contact_point:
                fhir_telecom.append(contact_point)

        return fhir_telecom

    def _convert_address(self, addresses: list[AD] | AD) -> JSONObject:
        """Convert C-CDA address to FHIR Address.

        Note: Location.address is 0..1 (single address), not array.
        If multiple addresses provided, uses the first one.

        Args:
            addresses: List of C-CDA AD or single AD

        Returns:
            FHIR Address object (or empty dict if no valid address)
        """
        # Normalize to list
        addr_list = addresses if isinstance(addresses, list) else [addresses]

        if not addr_list:
            return {}

        # Use first address
        addr = addr_list[0]
        fhir_address: JSONObject = {}

        # Street address lines
        if addr.street_address_line:
            fhir_address["line"] = addr.street_address_line

        # City
        if addr.city:
            fhir_address["city"] = addr.city if isinstance(addr.city, str) else addr.city[0]

        # State
        if addr.state:
            fhir_address["state"] = addr.state if isinstance(addr.state, str) else addr.state[0]

        # Postal code
        if addr.postal_code:
            fhir_address["postalCode"] = (
                addr.postal_code if isinstance(addr.postal_code, str) else addr.postal_code[0]
            )

        # Country
        if addr.country:
            fhir_address["country"] = addr.country if isinstance(addr.country, str) else addr.country[0]

        # Map use code (HP = home, WP = work, TMP = temp, etc.)
        if addr.use:
            fhir_use = ADDRESS_USE_MAP.get(addr.use)
            if fhir_use:
                fhir_address["use"] = fhir_use

        return fhir_address if fhir_address else {}

    def _infer_physical_type(self, location_code: CE) -> JSONObject | None:
        """Infer physical type from location type code.

        Maps C-CDA location codes to FHIR location-physical-type codes.
        Uses http://terminology.hl7.org/CodeSystem/location-physical-type

        Per FHIR R4 specification, physicalType describes the physical form
        of the location (e.g., building, room, vehicle, road).

        Args:
            location_code: The C-CDA location type code (participantRole/code)

        Returns:
            FHIR CodeableConcept for physicalType or None if cannot infer

        Examples:
            >>> # Hospital location
            >>> code = CE(code="1061-3", code_system="2.16.840.1.113883.6.259")
            >>> physical_type = self._infer_physical_type(code)
            >>> # Returns: {"coding": [{"system": "...", "code": "bu", "display": "Building"}]}
            >>>
            >>> # Patient's residence
            >>> code = CE(code="PTRES", code_system="2.16.840.1.113883.5.111")
            >>> physical_type = self._infer_physical_type(code)
            >>> # Returns: {"coding": [{"system": "...", "code": "ho", "display": "House"}]}
        """
        if not location_code or not hasattr(location_code, 'code') or not location_code.code:
            return None

        # Mapping from C-CDA location codes to FHIR physicalType codes
        # Key: (code_system, code) → (physical_type_code, display)

        # HSLOC codes (2.16.840.1.113883.6.259)
        hsloc_map = {
            '1061-3': ('bu', 'Building'),  # Hospital
            '1116-5': ('bu', 'Building'),  # Ambulatory Surgical Center
            '1117-3': ('bu', 'Building'),  # Ambulatory Primary Care Clinic
            '1118-1': ('wa', 'Ward'),      # Emergency Department
            '1160-1': ('bu', 'Building'),  # Urgent Care Center
            '1200-7': ('bu', 'Building'),  # Long Term Care
            '1242-9': ('bu', 'Building'),  # Outpatient Clinic

            # Wards and units
            '1021-7': ('wa', 'Ward'),      # Critical Care Unit
            '1023-3': ('wa', 'Ward'),      # Inpatient Medical Ward
            '1024-1': ('wa', 'Ward'),      # Inpatient Surgical Ward
            '1025-8': ('wa', 'Ward'),      # Inpatient Pediatric Ward
            '1026-6': ('wa', 'Ward'),      # Inpatient Obstetric Ward
            '1027-4': ('wa', 'Ward'),      # Inpatient Psychiatric Ward
            '1028-2': ('wa', 'Ward'),      # Rehabilitation Unit
            '1029-0': ('wa', 'Ward'),      # Labor and Delivery
            '1033-2': ('wa', 'Ward'),      # Pediatric Critical Care
            '1034-0': ('wa', 'Ward'),      # Neonatal Critical Care (NICU)
            '1035-7': ('wa', 'Ward'),      # Burn Unit

            # Rooms and specific areas
            '1108-2': ('ro', 'Room'),      # Operating Room
            '1250-2': ('area', 'Area'),    # Pharmacy
            '1251-0': ('area', 'Area'),    # Radiology
            '1252-8': ('area', 'Area'),    # Laboratory
        }

        # RoleCode v3 codes (2.16.840.1.113883.5.111)
        rolecode_map = {
            'PTRES': ('ho', 'House'),      # Patient's Residence
            'AMB': ('ve', 'Vehicle'),      # Ambulance
            'HOSP': ('bu', 'Building'),    # Hospital
            'PHARM': ('bu', 'Building'),   # Pharmacy
            'COMM': ('bu', 'Building'),    # Community Location
            'SCHOOL': ('bu', 'Building'),  # School
            'WORK': ('bu', 'Building'),    # Work Site
        }

        # SNOMED CT codes (2.16.840.1.113883.6.96)
        snomed_map = {
            '22232009': ('bu', 'Building'),     # Hospital
            '225728007': ('wa', 'Ward'),        # Accident and Emergency department
            '309904001': ('wa', 'Ward'),        # Intensive care unit
            '309905002': ('wa', 'Ward'),        # Coronary care unit
            '309939001': ('wa', 'Ward'),        # Palliative care unit
            '309914001': ('ro', 'Room'),        # Operating theater
            '225746001': ('ro', 'Room'),        # Patient room
            '702871004': ('area', 'Area'),      # Infusion clinic
        }

        # Determine which mapping to use based on code system
        physical_type_code = None
        display = None

        code_system = location_code.code_system if hasattr(location_code, 'code_system') else None
        code_value = location_code.code

        if code_system == '2.16.840.1.113883.6.259':  # HSLOC
            if code_value in hsloc_map:
                physical_type_code, display = hsloc_map[code_value]
        elif code_system == '2.16.840.1.113883.5.111':  # RoleCode
            if code_value in rolecode_map:
                physical_type_code, display = rolecode_map[code_value]
        elif code_system == '2.16.840.1.113883.6.96':  # SNOMED CT
            if code_value in snomed_map:
                physical_type_code, display = snomed_map[code_value]

        # If no mapping found, return None (field will be omitted)
        if not physical_type_code:
            return None

        # Return FHIR CodeableConcept structure
        return {
            "coding": [{
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": physical_type_code,
                "display": display
            }]
        }

    def _determine_mode(self, location_code: CE) -> str:
        """Determine location mode (instance vs kind).

        Per FHIR R4 specification:
        - instance: Specific location (Room 123, specific hospital)
        - kind: Type of location (patient's home, ambulance)

        Location codes representing types/classes rather than specific instances
        should use mode "kind". Examples include patient homes, ambulances, and
        other non-facility-specific locations.

        Args:
            location_code: The C-CDA location type code (participantRole/code)

        Returns:
            "instance" or "kind"

        Examples:
            >>> # Specific hospital location
            >>> code = CE(code="1061-3", code_system="2.16.840.1.113883.6.259")
            >>> mode = self._determine_mode(code)
            >>> # Returns: "instance"
            >>>
            >>> # Patient's home (generic location type)
            >>> code = CE(code="PTRES", code_system="2.16.840.1.113883.5.111")
            >>> mode = self._determine_mode(code)
            >>> # Returns: "kind"
        """
        if not location_code or not hasattr(location_code, 'code') or not location_code.code:
            # Default to instance when code is missing
            return "instance"

        # Codes that represent types/classes rather than specific instances
        # These should use mode "kind" per FHIR specification
        kind_codes = {
            'PTRES',   # Patient's Residence - represents any patient home, not a specific address
            'AMB',     # Ambulance - represents a type of vehicle, not a specific ambulance
            'WORK',    # Work Site - represents any workplace
            'SCHOOL',  # School - represents any school
        }

        code_value = location_code.code

        if code_value in kind_codes:
            return "kind"

        # All other codes represent specific instances (hospitals, rooms, clinics, etc.)
        return "instance"

    def _get_managing_organization_reference(
        self,
        participant_role: ParticipantRole
    ) -> JSONObject | None:
        """Extract managing organization reference from location's scoping entity.

        The managing organization is the organization responsible for the provisioning
        and upkeep of the location. This is extracted from participantRole/scopingEntity,
        which represents the organization that owns or manages the location.

        Per US Core Location profile, managingOrganization is a Must Support element.

        Args:
            participant_role: C-CDA ParticipantRole with potential scopingEntity

        Returns:
            Organization reference dict or None if no managing organization found

        Examples:
            >>> # Location with scoping organization
            >>> ref = self._get_managing_organization_reference(participant_role)
            >>> # Returns: {"reference": "Organization/org-123"}
            >>>
            >>> # Location without scoping organization
            >>> ref = self._get_managing_organization_reference(participant_role)
            >>> # Returns: None
        """
        # Check if scoping entity exists
        if not participant_role.scoping_entity:
            return None

        scoping_entity = participant_role.scoping_entity

        # Extract organization ID from scoping entity identifiers
        if not scoping_entity.id or len(scoping_entity.id) == 0:
            return None

        # Generate organization ID from identifiers
        org_id = self._generate_organization_id(scoping_entity.id)

        # Check if Organization resource exists in registry
        # Only create reference if the Organization has been registered
        if self.reference_registry and self.reference_registry.has_resource("Organization", org_id):
            return {"reference": f"Organization/{org_id}"}

        # If no Organization resource exists in registry, don't create dangling reference
        # The organization may be created later or may not be relevant
        return None

    def _generate_organization_id(self, identifiers: list[II]) -> str:
        """Generate FHIR Organization ID from C-CDA identifiers.

        Uses the same logic as OrganizationConverter to ensure consistent IDs.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated Organization ID
        """
        from ccda_to_fhir.id_generator import generate_id_from_identifiers

        # Use cached UUID v4 generator for organization identifiers
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("Organization", root, extension)
