"""Coverage converter.

Converts C-CDA Coverage Activity / Policy Activity to FHIR Coverage resource.

C-CDA Structure:
  Payers Section (2.16.840.1.113883.10.20.22.2.18)
    └─ Coverage Activity (Act, template .60) — outer container
         └─ entryRelationship[COMP]
              ├─ sequenceNumber — maps to Coverage.order
              └─ Policy Activity (Act, template .61) — insurance details
                   ├─ id — Coverage.identifier
                   ├─ code — Coverage.type
                   ├─ statusCode — Coverage.status
                   ├─ effectiveTime — Coverage.period (fallback)
                   ├─ performer[PAYOR] (.87) — Coverage.payor (→ Organization)
                   ├─ performer[GUAR] (.88) — not mapped (guarantor info)
                   ├─ participant[COV] (.89) — Coverage.subscriberId, relationship,
                   │                           subscriber, period (from time)
                   └─ participant[HLD] (.90) — Coverage.policyHolder

Reference:
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-CoverageActivity.html
- C-CDA: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-PolicyActivity.html
- FHIR: https://hl7.org/fhir/R4B/coverage.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ccda_to_fhir.constants import FHIRCodes, TemplateIds
from ccda_to_fhir.id_generator import generate_id, generate_id_from_identifiers
from ccda_to_fhir.logging_config import get_logger
from ccda_to_fhir.types import FHIRResourceDict

from .base import BaseConverter
from .organization import OrganizationConverter

if TYPE_CHECKING:
    from ccda_to_fhir.ccda.models.act import Act
    from ccda_to_fhir.ccda.models.datatypes import IVL_TS
    from ccda_to_fhir.ccda.models.participant import Participant
    from ccda_to_fhir.ccda.models.performer import Performer

    from .references import ReferenceRegistry

logger = get_logger(__name__)

# C-CDA status code → FHIR Coverage.status
_STATUS_MAP = {
    "completed": "active",
    "active": "active",
    "suspended": "cancelled",
    "aborted": "cancelled",
}

# C-CDA relationship code → FHIR Coverage.relationship coding
_RELATIONSHIP_MAP = {
    "SELF": {"code": "self", "display": "Self"},
    "SPOUSE": {"code": "spouse", "display": "Spouse"},
    "CHILD": {"code": "child", "display": "Child"},
    "STPCHLD": {"code": "child", "display": "Child"},
    "PARENT": {"code": "parent", "display": "Parent"},
    "DOMPART": {"code": "common", "display": "Common Law Spouse"},
    "FAMMEMB": {"code": "other", "display": "Other"},
    "OTHER": {"code": "other", "display": "Other"},
}


def convert_coverage_activity(
    act: Act,
    *,
    reference_registry: ReferenceRegistry | None = None,
    code_system_mapper=None,
) -> list[FHIRResourceDict]:
    """Convert a Coverage Activity Act to FHIR Coverage + Organization resources.

    A single Coverage Activity may contain multiple Policy Activities via
    entryRelationship[COMP], each producing one Coverage resource.

    Args:
        act: The Coverage Activity Act (template .60)
        reference_registry: Registry for tracking generated resources
        code_system_mapper: Code system mapper for OID→URI

    Returns:
        List of FHIR resources (Coverage + payor Organization resources)
    """
    converter = CoverageConverter(
        code_system_mapper=code_system_mapper,
        reference_registry=reference_registry,
    )
    return converter.convert(act)


class CoverageConverter(BaseConverter["Act"]):
    """Convert C-CDA Coverage Activity to FHIR Coverage resources."""

    def convert(self, ccda_model: Act) -> list[FHIRResourceDict]:  # type: ignore[override]
        """Convert Coverage Activity to Coverage + Organization resources.

        Args:
            ccda_model: The Coverage Activity Act (template .60)

        Returns:
            List of FHIR resources
        """
        resources: list[FHIRResourceDict] = []
        act = ccda_model

        if not act.entry_relationship:
            return resources

        for er in act.entry_relationship:
            if er.type_code != "COMP" or not er.act:
                continue

            policy_act = er.act
            # Verify this is a Policy Activity
            if not _has_template(policy_act, TemplateIds.POLICY_ACTIVITY):
                continue

            coverage, related = self._convert_policy_activity(
                policy_act, sequence_number=er.sequence_number
            )
            if coverage:
                resources.append(coverage)
                resources.extend(related)

        return resources

    def _convert_policy_activity(
        self,
        policy: Act,
        sequence_number: int | None = None,
    ) -> tuple[FHIRResourceDict | None, list[FHIRResourceDict]]:
        """Convert a single Policy Activity to a Coverage resource.

        Args:
            policy: The Policy Activity Act (template .61)
            sequence_number: Coverage order from entryRelationship.sequenceNumber

        Returns:
            Tuple of (Coverage resource, list of related Organization resources)
        """
        related: list[FHIRResourceDict] = []

        coverage: FHIRResourceDict = {
            "resourceType": FHIRCodes.ResourceTypes.COVERAGE,
        }

        # Generate ID from policy identifiers
        if policy.id and len(policy.id) > 0:
            first_id = policy.id[0]
            coverage["id"] = generate_id_from_identifiers(
                "Coverage",
                first_id.root,
                first_id.extension,
            )
            # Map identifiers
            identifiers = self.convert_identifiers(policy.id)
            if identifiers:
                coverage["identifier"] = identifiers
        else:
            coverage["id"] = generate_id()

        # Status
        if policy.status_code and policy.status_code.code:
            status_code = policy.status_code.code
            mapped = _STATUS_MAP.get(status_code)
            if mapped:
                coverage["status"] = mapped
            else:
                logger.warning("Unmapped Coverage statusCode '%s', defaulting to 'active'", status_code)
                coverage["status"] = "active"
        else:
            coverage["status"] = "active"

        # Type from policy code (insurance type)
        if policy.code and policy.code.code:
            coverage_type = self.create_codeable_concept(
                code=policy.code.code,
                code_system=policy.code.code_system,
                display_name=policy.code.display_name,
            )
            if coverage_type:
                coverage["type"] = coverage_type

        # Order from sequenceNumber
        if sequence_number is not None:
            coverage["order"] = sequence_number

        # Period from policy effectiveTime (may be overridden by COV participant time)
        if policy.effective_time:
            period = self._convert_period(policy.effective_time)
            if period:
                coverage["period"] = period

        # Process performers (PAYOR, GUAR)
        if policy.performer:
            for performer in policy.performer:
                self._process_performer(performer, coverage, related)

        # Process participants (COV, HLD)
        if policy.participant:
            for participant in policy.participant:
                self._process_participant(participant, coverage)

        # Beneficiary — reference to the document's patient
        if self.reference_registry:
            patient_ref = self.reference_registry.get_patient_reference()
            coverage["beneficiary"] = patient_ref
            # payor is required in FHIR Coverage — default to patient if no PAYOR performer
            if "payor" not in coverage:
                coverage["payor"] = [patient_ref]
        else:
            coverage["beneficiary"] = {"reference": "Patient/unknown"}
            if "payor" not in coverage:
                coverage["payor"] = [{"reference": "Patient/unknown"}]

        return coverage, related

    def _convert_period(self, effective_time: IVL_TS) -> FHIRResourceDict | None:
        """Convert IVL_TS to FHIR Period.

        Args:
            effective_time: C-CDA IVL_TS element

        Returns:
            FHIR Period dict or None
        """
        period: FHIRResourceDict = {}

        if effective_time.value:
            # Single point in time
            start = self.convert_date(effective_time.value)
            if start:
                period["start"] = start
        if effective_time.low and effective_time.low.value:
            start = self.convert_date(effective_time.low.value)
            if start:
                period["start"] = start
        if effective_time.high and effective_time.high.value:
            end = self.convert_date(effective_time.high.value)
            if end:
                period["end"] = end

        return period if period else None

    def _process_performer(
        self,
        performer: Performer,
        coverage: FHIRResourceDict,
        related: list[FHIRResourceDict],
    ) -> None:
        """Extract payor organization from PAYOR performer.

        Args:
            performer: Performer element
            coverage: Coverage resource being built
            related: List to append Organization resources to
        """
        if not performer.assigned_entity:
            return

        # Identify PAYOR performer by templateId (.87) first, fall back to code
        if not self._is_payor_performer(performer):
            if self._is_guarantor_performer(performer):
                logger.debug("Guarantor performer (.88) present but not mapped to FHIR Coverage")
            return

        assigned = performer.assigned_entity
        org_converter = OrganizationConverter(
            code_system_mapper=self.code_system_mapper,
        )

        # Try representedOrganization first, fall back to assignedEntity itself
        if assigned.represented_organization:
            org = org_converter.convert(assigned.represented_organization)
            if org:
                if not org.get("id"):
                    org["id"] = generate_id()
                related.append(org)
                coverage["payor"] = [
                    {"reference": f"urn:uuid:{org['id']}"}
                ]
        elif assigned.id:
            # Create minimal Organization from assignedEntity
            org_id = generate_id_from_identifiers(
                "Organization",
                assigned.id[0].root,
                assigned.id[0].extension,
            )
            minimal_org: FHIRResourceDict = {
                "resourceType": FHIRCodes.ResourceTypes.ORGANIZATION,
                "id": org_id,
                "active": True,
            }
            identifiers = self.convert_identifiers(assigned.id)
            if identifiers:
                minimal_org["identifier"] = identifiers
            related.append(minimal_org)
            coverage["payor"] = [
                {"reference": f"urn:uuid:{org_id}"}
            ]

    @staticmethod
    def _is_payor_performer(performer: Performer) -> bool:
        """Check if a performer is a PAYOR by templateId (.87) or code."""
        if performer.template_id:
            if any(t.root == TemplateIds.PAYER_PERFORMER for t in performer.template_id):
                return True
        if performer.assigned_entity and performer.assigned_entity.code:
            code = performer.assigned_entity.code.code
            return code.upper() == "PAYOR" if code else False
        return False

    @staticmethod
    def _is_guarantor_performer(performer: Performer) -> bool:
        """Check if a performer is a GUARANTOR by templateId (.88) or code."""
        if performer.template_id:
            if any(t.root == TemplateIds.GUARANTOR_PERFORMER for t in performer.template_id):
                return True
        if performer.assigned_entity and performer.assigned_entity.code:
            code = performer.assigned_entity.code.code
            return code.upper() == "GUAR" if code else False
        return False

    def _process_participant(
        self,
        participant: Participant,
        coverage: FHIRResourceDict,
    ) -> None:
        """Extract subscriber/policyHolder info from COV/HLD participants.

        Args:
            participant: Participant element
            coverage: Coverage resource being built
        """
        if not participant.participant_role:
            return

        role = participant.participant_role

        if participant.type_code == "COV":
            # Covered party — extract member ID and relationship
            if role.id:
                for identifier in role.id:
                    if identifier.extension:
                        coverage["subscriberId"] = identifier.extension
                        break

            # Relationship code (SELF, SPOUSE, CHILD, etc.)
            relationship_code: str | None = None
            if role.code and role.code.code:
                relationship_code = role.code.code.upper()
                rel = _RELATIONSHIP_MAP.get(relationship_code)
                if not rel:
                    logger.warning("Unmapped relationship code '%s', defaulting to 'other'", relationship_code)
                    rel = _RELATIONSHIP_MAP["OTHER"]
                coverage["relationship"] = {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/subscriber-relationship",
                        **rel,
                    }],
                }

            # When relationship is SELF, subscriber is the patient (beneficiary)
            if relationship_code == "SELF" and self.reference_registry:
                coverage["subscriber"] = self.reference_registry.get_patient_reference()

            # COV participant time is the coverage period (preferred over policy effectiveTime)
            if participant.time:
                period = self._convert_period(participant.time)
                if period:
                    coverage["period"] = period

        elif participant.type_code == "HLD":
            # Policy holder
            if role.id:
                first = role.id[0]
                value = first.extension or first.root
                if not value:
                    return
                ident: FHIRResourceDict = {}
                if first.root:
                    ident["system"] = self.map_oid_to_uri(first.root)
                ident["value"] = value
                coverage["policyHolder"] = {"identifier": ident}


def _has_template(act: Act, template_id: str) -> bool:
    """Check if an Act has a specific template ID."""
    if not act.template_id:
        return False
    return any(t.root == template_id for t in act.template_id)
