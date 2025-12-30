"""CareTeam converter: C-CDA Care Team Organizer to FHIR CareTeam resource.

Converts C-CDA Care Team Organizer (template 2.16.840.1.113883.10.20.22.4.500)
to FHIR CareTeam resource compliant with US Core CareTeam profile.

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamOrganizer.html
- FHIR: https://hl7.org/fhir/R4/careteam.html
- US Core: http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam
- Mapping: docs/mapping/17-careteam.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes
from ccda_to_fhir.id_generator import generate_id_from_identifiers
from ccda_to_fhir.types import FHIRResourceDict, JSONObject

from .base import BaseConverter
from .organization import OrganizationConverter
from .practitioner import PractitionerConverter
from .practitioner_role import PractitionerRoleConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.organizer import Organizer


class CareTeamConverter(BaseConverter["Organizer"]):
    """Convert C-CDA Care Team Organizer to FHIR CareTeam.

    Handles mapping from C-CDA Care Team Organizer template
    (2.16.840.1.113883.10.20.22.4.500) to US Core CareTeam profile.

    This converter supports:
    - Multiple care team members with roles
    - Team type/category classification
    - Team lead designation
    - Creation of referenced Practitioner, PractitionerRole, and Organization resources
    """

    # Care Team Organizer template OID
    CARE_TEAM_ORGANIZER_TEMPLATE = "2.16.840.1.113883.10.20.22.4.500"
    # Valid extensions: 2019-07-01, 2022-06-01 (both acceptable per C-CDA spec)
    CARE_TEAM_ORGANIZER_EXTENSIONS = ["2019-07-01", "2022-06-01"]

    # Care Team Member Act template OID
    CARE_TEAM_MEMBER_ACT_TEMPLATE = "2.16.840.1.113883.10.20.22.4.500.1"
    # Valid extensions: 2019-07-01, 2022-06-01 (both acceptable per C-CDA spec)
    CARE_TEAM_MEMBER_ACT_EXTENSIONS = ["2019-07-01", "2022-06-01"]

    # Care Team Type Observation template OID
    CARE_TEAM_TYPE_OBSERVATION_TEMPLATE = "2.16.840.1.113883.10.20.22.4.500.2"
    # Valid extension: 2019-07-01 (only one version per C-CDA spec)
    CARE_TEAM_TYPE_OBSERVATION_EXTENSION = "2019-07-01"

    # US Core CareTeam profile
    US_CORE_CARETEAM_PROFILE = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-careteam"

    # Status mapping: C-CDA statusCode -> FHIR status
    STATUS_MAP = {
        "active": "active",
        "completed": "inactive",
        "aborted": "inactive",
        "suspended": "suspended",
        "nullified": "entered-in-error",
        "obsolete": "inactive",
    }

    def __init__(self, patient_reference: JSONObject | None = None, **kwargs):
        """Initialize the CareTeamConverter.

        Args:
            patient_reference: Reference to Patient resource (required)
            **kwargs: Additional arguments passed to BaseConverter

        Raises:
            ValueError: If patient_reference is None
        """
        super().__init__(**kwargs)

        if not patient_reference:
            raise ValueError("patient_reference is required for CareTeam conversion")

        self.patient_reference = patient_reference

        # Registry to track created resources and avoid duplicates
        self.practitioner_registry: dict[str, str] = {}  # NPI -> Practitioner ID
        self.organization_registry: dict[str, str] = {}  # OID -> Organization ID
        self.practitioner_role_registry: dict[str, str] = {}  # Key -> PractitionerRole ID

        # Storage for created resources
        self.created_practitioners: dict[str, FHIRResourceDict] = {}  # ID -> Resource
        self.created_organizations: dict[str, FHIRResourceDict] = {}  # ID -> Resource
        self.created_practitioner_roles: dict[str, FHIRResourceDict] = {}  # ID -> Resource

        # Converters for referenced resources
        self.practitioner_converter = PractitionerConverter()
        self.organization_converter = OrganizationConverter()
        self.practitioner_role_converter = PractitionerRoleConverter()

    def convert(self, organizer: Organizer) -> FHIRResourceDict:
        """Convert Care Team Organizer to CareTeam resource.

        Args:
            organizer: C-CDA Care Team Organizer

        Returns:
            FHIR CareTeam resource as dictionary

        Raises:
            ValueError: If required elements are missing or invalid
        """
        if not organizer:
            raise ValueError("Organizer is required")

        # Validate template ID
        self._validate_template(organizer)

        # Validate required code (SHALL be LOINC 86744-0 per C-CDA)
        if not organizer.code:
            raise ValueError("Care Team Organizer code is required")
        if organizer.code.code != "86744-0" or organizer.code.code_system != "2.16.840.1.113883.6.1":
            raise ValueError(
                f"Care Team Organizer code SHALL be LOINC 86744-0, got {organizer.code.code} from {organizer.code.code_system}"
            )

        # Validate required identifier
        if not organizer.id or len(organizer.id) == 0:
            raise ValueError("Care Team Organizer identifier is required")

        # ====================================================================
        # DESIGN DECISION: Lenient effectiveTime validation
        # ====================================================================
        # C-CDA SHALL Requirement:
        #   Care Team Organizer SHALL contain exactly one [1..1] effectiveTime
        #   (Template 2.16.840.1.113883.10.20.22.4.500, line 272)
        #
        # Implementation Choice:
        #   This implementation treats effectiveTime as optional (does not enforce presence)
        #   but strictly validates structure when present (low element required).
        #
        # Rationale:
        #   - Real-world C-CDA documents often omit effectiveTime for ongoing care teams
        #   - Missing effectiveTime does not prevent meaningful FHIR resource creation
        #   - Rejecting documents would reduce interoperability with imperfect data
        #   - When missing, CareTeam.period is derived from document effectiveTime or omitted
        #
        # Trade-offs:
        #   ✓ Robustness: Accepts real-world data variations
        #   ✓ Usability: Does not block conversion for minor omissions
        #   ✗ Strict Compliance: Deviates from C-CDA SHALL requirement
        #
        # See: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamOrganizer.html
        # ====================================================================

        # Validate effectiveTime.low when effectiveTime is present
        if organizer.effective_time:
            if hasattr(organizer.effective_time, "low"):
                if not organizer.effective_time.low:
                    raise ValueError("Care Team Organizer effectiveTime.low is required when effectiveTime is present")
            elif not hasattr(organizer.effective_time, "value"):
                raise ValueError("Care Team Organizer effectiveTime must have low or value")

        careteam: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.CARETEAM,
        }

        # Add US Core profile
        careteam["meta"] = {
            "profile": [self.US_CORE_CARETEAM_PROFILE]
        }

        # Generate ID from identifiers
        careteam["id"] = self._generate_careteam_id(organizer.id)

        # Map identifiers
        identifiers = self._convert_identifiers(organizer.id)
        if identifiers:
            careteam["identifier"] = identifiers

        # Map status (required, defaults to active)
        careteam["status"] = self._map_status(organizer.status_code)

        # Map subject (required)
        careteam["subject"] = self.patient_reference

        # Map effective time to period
        if organizer.effective_time:
            period = self._convert_effective_time_to_period(organizer.effective_time)
            if period:
                careteam["period"] = period

        # Map category from team type observations
        categories = self._extract_categories(organizer)
        if categories:
            careteam["category"] = categories

        # Map participants from Care Team Member Acts (required, at least one)
        participants = self._extract_participants(organizer)
        if not participants:
            raise ValueError("CareTeam requires at least one participant (US Core requirement)")
        careteam["participant"] = participants

        # Extract managing organization from first member's organization
        managing_org_id = self._extract_managing_organization(organizer)
        if managing_org_id:
            careteam["managingOrganization"] = [{"reference": f"Organization/{managing_org_id}"}]

        # Extract narrative text from code originalText or generate from data
        narrative = self._generate_narrative(organizer, categories, participants)
        if narrative:
            careteam["text"] = narrative

        # Generate human-readable name
        careteam["name"] = self._generate_name(organizer, categories)

        return careteam

    def get_related_resources(self) -> list[FHIRResourceDict]:
        """Get all related resources created during conversion.

        Returns:
            List of Practitioner, PractitionerRole, and Organization resources
            created during CareTeam conversion
        """
        resources: list[FHIRResourceDict] = []

        # Add all created practitioners
        resources.extend(self.created_practitioners.values())

        # Add all created organizations
        resources.extend(self.created_organizations.values())

        # Add all created practitioner roles
        resources.extend(self.created_practitioner_roles.values())

        return resources

    def _validate_template(self, organizer: Organizer) -> None:
        """Validate that this is a Care Team Organizer template.

        Validates both root OID and extension date per C-CDA specification.

        Args:
            organizer: Organizer to validate

        Raises:
            ValueError: If template ID is missing or invalid
        """
        if not organizer.template_id:
            raise ValueError(
                f"Missing templateId - expected {self.CARE_TEAM_ORGANIZER_TEMPLATE} "
                f"with extension {' or '.join(self.CARE_TEAM_ORGANIZER_EXTENSIONS)}"
            )

        # Check for valid template (root + extension)
        has_valid_template = any(
            tid.root == self.CARE_TEAM_ORGANIZER_TEMPLATE and
            hasattr(tid, "extension") and
            tid.extension in self.CARE_TEAM_ORGANIZER_EXTENSIONS
            for tid in organizer.template_id
        )

        if not has_valid_template:
            # Provide helpful error message
            found_templates = [
                f"{tid.root}" + (f" extension={tid.extension}" if hasattr(tid, "extension") and tid.extension else " (no extension)")
                for tid in organizer.template_id
            ]
            raise ValueError(
                f"Invalid templateId - expected {self.CARE_TEAM_ORGANIZER_TEMPLATE} "
                f"with extension {' or '.join(self.CARE_TEAM_ORGANIZER_EXTENSIONS)}. "
                f"Found: {', '.join(found_templates)}"
            )

    def _generate_careteam_id(self, identifiers: list) -> str:
        """Generate FHIR CareTeam ID from C-CDA identifiers.

        Uses UUID v4 caching based on identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            Generated CareTeam ID
        """
        root = identifiers[0].root if identifiers and identifiers[0].root else None
        extension = identifiers[0].extension if identifiers and identifiers[0].extension else None

        return generate_id_from_identifiers("CareTeam", root, extension)

    def _convert_identifiers(self, identifiers: list | None) -> list[JSONObject]:
        """Convert C-CDA identifiers to FHIR identifiers.

        Args:
            identifiers: List of C-CDA II identifiers

        Returns:
            List of FHIR identifier objects
        """
        if not identifiers:
            return []

        fhir_identifiers: list[JSONObject] = []

        for identifier in identifiers:
            if identifier.null_flavor:
                continue

            fhir_identifier = self.create_identifier(
                root=identifier.root,
                extension=identifier.extension if hasattr(identifier, "extension") else None,
            )

            if fhir_identifier:
                fhir_identifiers.append(fhir_identifier)

        return fhir_identifiers

    def _map_status(self, status_code) -> str:
        """Map C-CDA statusCode to FHIR CareTeam status.

        ====================================================================
        DESIGN DECISION: Lenient statusCode validation
        ====================================================================
        C-CDA SHALL Requirement:
          Care Team Organizer SHALL contain exactly one [1..1] statusCode
          statusCode SHALL contain exactly one [1..1] @code from ActStatus value set
          (Template 2.16.840.1.113883.10.20.22.4.500, line 271)

        Implementation Choice:
          This implementation accepts missing statusCode and defaults to "active"
          rather than rejecting the document or raising an error.

        Rationale:
          - Real-world C-CDA documents may omit statusCode for active care teams
          - "active" is the most common and reasonable default for ongoing teams
          - Missing statusCode does not indicate invalid clinical data
          - Defaulting enables successful conversion of imperfect but usable data

        Trade-offs:
          ✓ Robustness: Handles documents with missing required elements
          ✓ Usability: Provides sensible default behavior
          ✓ Safety: "active" is conservative assumption for ongoing teams
          ✗ Strict Compliance: Deviates from C-CDA SHALL requirement

        Mapping:
          C-CDA statusCode  →  FHIR CareTeam.status
          active            →  active
          completed         →  inactive
          aborted           →  inactive
          suspended         →  suspended
          nullified         →  entered-in-error
          obsolete          →  inactive
          missing/unknown   →  active (default)

        See: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CareTeamOrganizer.html
        ====================================================================

        Args:
            status_code: C-CDA statusCode element

        Returns:
            FHIR status code
        """
        if not status_code or not status_code.code:
            return "active"  # Default to active when statusCode missing (lenient)

        ccda_status = status_code.code.lower()
        return self.STATUS_MAP.get(ccda_status, "active")

    def _convert_effective_time_to_period(self, effective_time) -> JSONObject | None:
        """Convert C-CDA effectiveTime to FHIR Period.

        Args:
            effective_time: C-CDA effectiveTime element (IVL_TS)

        Returns:
            FHIR Period or None
        """
        period: JSONObject = {}

        if hasattr(effective_time, "low") and effective_time.low:
            start = self.convert_date(effective_time.low.value)
            if start:
                period["start"] = start

        if hasattr(effective_time, "high") and effective_time.high:
            end = self.convert_date(effective_time.high.value)
            if end:
                period["end"] = end

        return period if period else None

    def _extract_categories(self, organizer: Organizer) -> list[JSONObject]:
        """Extract category from Care Team Type Observations.

        Validates both root OID and extension date per C-CDA specification.

        ====================================================================
        DESIGN DECISION: Lenient Care Team Type Observation validation
        ====================================================================
        C-CDA Specification Note:
          The C-CDA Care Team Organizer template documentation shows Care Team Type
          Observation as component with cardinality 0..* (MAY contain) per the
          specification's conformance table, though some implementations may expect
          at least one type observation for proper categorization.

        Implementation Choice:
          This implementation treats Care Team Type Observation as fully optional.
          When missing, CareTeam.category will be an empty array, and the care team
          will still be created without categorization.

        Rationale:
          - Care Team Type Observation is marked as 0..* MAY in C-CDA spec
          - Real-world documents may omit team type for generic care teams
          - Missing category does not prevent meaningful care team representation
          - US Core CareTeam profile does not require category (0..*)
          - Team members and period are more critical than categorization

        Trade-offs:
          ✓ Robustness: Accepts care teams without explicit type
          ✓ Flexibility: Works with minimal C-CDA implementations
          ✓ Standards Aligned: Follows C-CDA MAY conformance level
          ~ Discoverability: Care teams without category may be harder to filter

        When Type Observation is present:
          - Extracts LOINC codes (LA27976-2, LA27977-0, LA28865-6, etc.)
          - Validates template ID root and extension (lenient on extension)
          - Maps to CareTeam.category for FHIR US Core compliance

        See: C-CDA Care Team Organizer template documentation
        ====================================================================

        Args:
            organizer: Care Team Organizer

        Returns:
            List of FHIR CodeableConcept for categories (may be empty)
        """
        categories: list[JSONObject] = []

        if not organizer.component:
            return categories  # No components - acceptable per MAY conformance

        for component in organizer.component:
            # Look for Care Team Type Observation
            if not component.observation:
                continue

            observation = component.observation

            # Check template ID
            if not observation.template_id:
                continue

            # Validate template root and extension
            is_type_obs = any(
                tid.root == self.CARE_TEAM_TYPE_OBSERVATION_TEMPLATE and
                hasattr(tid, "extension") and
                tid.extension == self.CARE_TEAM_TYPE_OBSERVATION_EXTENSION
                for tid in observation.template_id
            )

            if not is_type_obs:
                # Check if root matches but extension is wrong/missing
                has_matching_root = any(
                    tid.root == self.CARE_TEAM_TYPE_OBSERVATION_TEMPLATE
                    for tid in observation.template_id
                )
                if has_matching_root:
                    # Log warning but continue (lenient for real-world data)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Care Team Type Observation has correct root "
                        f"{self.CARE_TEAM_TYPE_OBSERVATION_TEMPLATE} but missing or "
                        f"invalid extension (expected {self.CARE_TEAM_TYPE_OBSERVATION_EXTENSION})"
                    )
                    # Continue processing despite extension issue
                else:
                    # Different template, skip
                    continue

            # Extract value (team type code)
            if observation.value:
                type_code = observation.value
                category = self.create_codeable_concept(
                    code=type_code.code,
                    code_system=type_code.code_system,
                    display_name=type_code.display_name,
                )
                if category:
                    categories.append(category)

        return categories

    def _extract_managing_organization(self, organizer: Organizer) -> str | None:
        """Extract managing organization from Care Team Member Acts.

        Returns the organization ID from the first member who has one.

        Args:
            organizer: Care Team Organizer

        Returns:
            Organization ID or None if not found
        """
        if not organizer.component:
            return None

        for component in organizer.component:
            if not component.act:
                continue

            act = component.act

            # Check template ID
            if not act.template_id:
                continue

            # Validate template root and extension
            is_member_act = any(
                tid.root == self.CARE_TEAM_MEMBER_ACT_TEMPLATE and
                hasattr(tid, "extension") and
                tid.extension in self.CARE_TEAM_MEMBER_ACT_EXTENSIONS
                for tid in act.template_id
            )

            if not is_member_act:
                # Check if root matches but extension is wrong/missing (lenient)
                has_matching_root = any(
                    tid.root == self.CARE_TEAM_MEMBER_ACT_TEMPLATE
                    for tid in act.template_id
                )
                if not has_matching_root:
                    # Different template, skip
                    continue
                # If root matches but extension is wrong, continue anyway (lenient)

            # Extract organization from performer
            if not act.performer or len(act.performer) == 0:
                continue

            performer = act.performer[0]

            if not performer.assigned_entity:
                continue

            assigned_entity = performer.assigned_entity

            # Check for represented organization
            if assigned_entity.represented_organization:
                org = assigned_entity.represented_organization
                if org.id and len(org.id) > 0:
                    org_oid = org.id[0].root
                    # Check if we already created this organization
                    if org_oid in self.organization_registry:
                        return self.organization_registry[org_oid]
                    # Try to convert it
                    try:
                        organization = self.organization_converter.convert(org)
                        organization_id = organization.get("id", f"org-{org_oid.replace('.', '-')}")
                        self.organization_registry[org_oid] = organization_id
                        return organization_id
                    except Exception:
                        # Organization conversion failed, continue to next member
                        continue

        return None

    def _extract_participants(self, organizer: Organizer) -> list[JSONObject]:
        """Extract participants from Care Team Member Acts.

        Args:
            organizer: Care Team Organizer

        Returns:
            List of FHIR CareTeam participant objects
        """
        if not organizer.component:
            return []

        # First, identify team lead if present
        lead_id = self._identify_team_lead(organizer)

        participants: list[JSONObject] = []
        lead_participant: JSONObject | None = None

        for component in organizer.component:
            # Look for Care Team Member Act
            if not component.act:
                continue

            act = component.act

            # Check template ID
            if not act.template_id:
                continue

            # Validate template root and extension
            is_member_act = any(
                tid.root == self.CARE_TEAM_MEMBER_ACT_TEMPLATE and
                hasattr(tid, "extension") and
                tid.extension in self.CARE_TEAM_MEMBER_ACT_EXTENSIONS
                for tid in act.template_id
            )

            if not is_member_act:
                # Check if root matches but extension is wrong/missing
                has_matching_root = any(
                    tid.root == self.CARE_TEAM_MEMBER_ACT_TEMPLATE
                    for tid in act.template_id
                )
                if has_matching_root:
                    # Log warning but continue (lenient for real-world data)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Care Team Member Act has correct root "
                        f"{self.CARE_TEAM_MEMBER_ACT_TEMPLATE} but missing or "
                        f"invalid extension (expected {' or '.join(self.CARE_TEAM_MEMBER_ACT_EXTENSIONS)})"
                    )
                    # Continue processing despite extension issue
                else:
                    # Different template, skip
                    continue

            # Validate Care Team Member Act code (SHALL be LOINC 86744-0)
            # This is a C-CDA requirement, but we'll be lenient and allow conversion
            # even if code is missing or incorrect
            if act.code:
                if act.code.code != "86744-0" or act.code.code_system != "2.16.840.1.113883.6.1":
                    # Code doesn't match expected value, but continue anyway
                    pass

            # Extract participant from this member act
            if not act.performer or len(act.performer) == 0:
                continue

            performer = act.performer[0]

            if not performer.assigned_entity:
                continue

            # Create participant
            participant = self._create_participant_from_performer(
                performer, act.effective_time
            )

            if not participant:
                continue

            # Check if this is the team lead
            is_lead = False
            if lead_id and performer.assigned_entity.id:
                for entity_id in performer.assigned_entity.id:
                    if (entity_id.root == lead_id.root and
                        entity_id.extension == lead_id.extension):
                        is_lead = True
                        break

            if is_lead:
                lead_participant = participant
            else:
                participants.append(participant)

        # Place lead first if identified
        if lead_participant:
            participants.insert(0, lead_participant)

        return participants

    def _identify_team_lead(self, organizer: Organizer) -> object | None:
        """Identify team lead from participant with typeCode='PPRF'.

        Args:
            organizer: Care Team Organizer

        Returns:
            II identifier of team lead, or None
        """
        if not organizer.participant:
            return None

        for participant in organizer.participant:
            if participant.type_code == "PPRF" and participant.participant_role:
                if participant.participant_role.id:
                    return participant.participant_role.id[0]

        return None

    def _create_participant_from_performer(
        self, performer, effective_time
    ) -> JSONObject | None:
        """Create CareTeam participant from Care Team Member Act performer.

        Args:
            performer: Performer element from Care Team Member Act
            effective_time: Effective time of member participation

        Returns:
            FHIR CareTeam participant object
        """
        assigned_entity = performer.assigned_entity

        participant: JSONObject = {}

        # Map function code to role (required)
        if performer.function_code:
            role = self.create_codeable_concept(
                code=performer.function_code.code,
                code_system=performer.function_code.code_system,
                display_name=performer.function_code.display_name,
            )
            if role:
                participant["role"] = [role]

        # Create member reference (required) - prefer PractitionerRole
        if assigned_entity.id and len(assigned_entity.id) > 0:
            member_ref = self._create_member_reference(assigned_entity)
            if member_ref:
                participant["member"] = member_ref

        # Map effective time to period
        if effective_time:
            period = self._convert_effective_time_to_period(effective_time)
            if period:
                participant["period"] = period

        # Only return if we have required elements
        if "role" in participant and "member" in participant:
            return participant

        return None

    def _create_member_reference(self, assigned_entity) -> JSONObject | None:
        """Create member reference (Practitioner/PractitionerRole).

        Creates Practitioner, Organization, and PractitionerRole resources,
        then returns reference to PractitionerRole (recommended).

        Args:
            assigned_entity: AssignedEntity from performer

        Returns:
            FHIR Reference to PractitionerRole
        """
        # Extract NPI for deduplication
        npi = None
        for entity_id in assigned_entity.id:
            if entity_id.root == "2.16.840.1.113883.4.6" and entity_id.extension:
                npi = entity_id.extension
                break

        if not npi:
            # Use first identifier for ID generation
            if assigned_entity.id and len(assigned_entity.id) > 0:
                first_id = assigned_entity.id[0]
                npi = first_id.extension if first_id.extension else first_id.root
            else:
                return None

        # Check if we already created Practitioner for this NPI
        if npi in self.practitioner_registry:
            practitioner_id = self.practitioner_registry[npi]
        else:
            # Create Practitioner resource
            if assigned_entity.assigned_person:
                practitioner = self.practitioner_converter.convert(assigned_entity)
                practitioner_id = practitioner.get("id", f"practitioner-{npi}")
                self.practitioner_registry[npi] = practitioner_id
                # Store the created resource
                self.created_practitioners[practitioner_id] = practitioner
            else:
                # No person, can't create practitioner
                return None

        # Create Organization if present
        organization_id = None
        if assigned_entity.represented_organization:
            org = assigned_entity.represented_organization
            if org.id and len(org.id) > 0:
                org_oid = org.id[0].root
                if org_oid in self.organization_registry:
                    organization_id = self.organization_registry[org_oid]
                else:
                    try:
                        organization = self.organization_converter.convert(org)
                        organization_id = organization.get("id", f"org-{org_oid.replace('.', '-')}")
                        self.organization_registry[org_oid] = organization_id
                        # Store the created resource
                        self.created_organizations[organization_id] = organization
                    except Exception:
                        # Organization conversion failed, continue without it
                        pass

        # Create PractitionerRole (organization is optional per US Core)
        # Check if we already created this PractitionerRole
        role_key = f"{practitioner_id}-{organization_id if organization_id else 'none'}"
        if role_key in self.practitioner_role_registry:
            role_id = self.practitioner_role_registry[role_key]
        else:
            try:
                practitioner_role = self.practitioner_role_converter.convert(
                    assigned_entity,
                    practitioner_id=practitioner_id,
                    organization_id=organization_id,
                )
                role_id = practitioner_role.get("id", f"role-{practitioner_id}-{organization_id}")
                self.practitioner_role_registry[role_key] = role_id
                # Store the created resource
                self.created_practitioner_roles[role_id] = practitioner_role
            except Exception:
                # PractitionerRole conversion failed, fallback to Practitioner
                return {"reference": f"Practitioner/{practitioner_id}"}

        return {"reference": f"PractitionerRole/{role_id}"}

    def _generate_name(self, organizer: Organizer, categories: list[JSONObject]) -> str:
        """Generate human-readable name for the care team.

        Args:
            organizer: Care Team Organizer
            categories: Extracted categories

        Returns:
            Human-readable care team name
        """
        # Extract team type from category
        team_type = "Care Team"
        if categories and len(categories) > 0:
            category = categories[0]
            if "coding" in category and len(category["coding"]) > 0:
                display = category["coding"][0].get("display", "")
                if "longitudinal" in display.lower() or "coordination" in display.lower():
                    team_type = "Primary Care Team"
                elif "condition" in display.lower():
                    team_type = "Condition Care Team"
                elif "encounter" in display.lower():
                    team_type = "Encounter Care Team"
                elif "episode" in display.lower():
                    team_type = "Episode Care Team"
                elif "event" in display.lower():
                    team_type = "Event Care Team"

        # Try to get patient name from reference (basic approach)
        # In real implementation, would look up patient resource
        patient_name = "Patient"

        return f"{team_type} for {patient_name}"

    def _generate_narrative(
        self, organizer: Organizer, categories: list[JSONObject], participants: list[JSONObject]
    ) -> JSONObject | None:
        """Generate narrative text for the care team.

        Extracts from code/originalText or generates from structured data.

        Args:
            organizer: Care Team Organizer
            categories: Extracted categories
            participants: Extracted participants

        Returns:
            FHIR Narrative object or None
        """
        # First, try to extract originalText from code
        original_text = None
        if organizer.code and hasattr(organizer.code, "original_text"):
            if organizer.code.original_text:
                if hasattr(organizer.code.original_text, "reference"):
                    # Reference to narrative block - we can't resolve this without section context
                    pass
                elif hasattr(organizer.code.original_text, "value"):
                    original_text = organizer.code.original_text.value

        # If we have originalText, use it
        if original_text:
            div_content = f"<div xmlns='http://www.w3.org/1999/xhtml'><p>{original_text}</p></div>"
            return {"status": "generated", "div": div_content}

        # Otherwise, generate narrative from structured data
        team_name = self._generate_name(organizer, categories)

        # Build participant list
        participant_lines = []
        for i, participant in enumerate(participants[:5]):  # Limit to first 5
            role_display = "Team Member"
            if "role" in participant and participant["role"]:
                role_data = participant["role"]
                if isinstance(role_data, list) and len(role_data) > 0:
                    role_data = role_data[0]
                if "coding" in role_data and len(role_data["coding"]) > 0:
                    role_display = role_data["coding"][0].get("display", "Team Member")

            participant_lines.append(f"<li>{role_display}</li>")

        if len(participants) > 5:
            participant_lines.append(f"<li>... and {len(participants) - 5} more</li>")

        participants_html = "".join(participant_lines)

        div_content = (
            f"<div xmlns='http://www.w3.org/1999/xhtml'>"
            f"<p><b>{team_name}</b></p>"
            f"<p>Team Members:</p>"
            f"<ul>{participants_html}</ul>"
            f"</div>"
        )

        return {"status": "generated", "div": div_content}
