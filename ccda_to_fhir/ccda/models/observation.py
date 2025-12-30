"""C-CDA Observation models.

Observations represent clinical findings, measurements, and assertions.
Used for problems, allergies, vital signs, lab results, social history, etc.

Reference: https://build.fhir.org/ig/HL7/CDA-ccda/StructureDefinition-ProblemObservation.html
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import Field, model_validator

from .author import Author
from .datatypes import (
    AD,
    BL,
    CD,
    CE,
    CS,
    ED,
    EIVL_TS,
    EN,
    II,
    INT,
    IVL_INT,
    IVL_PQ,
    IVL_TS,
    MO,
    ON,
    PIVL_TS,
    PN,
    PQ,
    REAL,
    RTO,
    ST,
    TEL,
    TN,
    TS,
    CDAModel,
)
from .participant import Participant
from .performer import Performer

if TYPE_CHECKING:
    from .act import Act
    from .clinical_document import Informant
    from .encounter import Encounter
    from .organizer import Organizer
    from .procedure import Procedure
    from .substance_administration import Precondition, SubstanceAdministration
    from .supply import Supply


class ReferenceRange(CDAModel):
    """Reference range for an observation value.

    Defines the normal or expected range for a measurement.
    """

    type_code: str | None = Field(default="REFV", alias="typeCode")
    observation_range: ObservationRange | None = Field(default=None, alias="observationRange")


class ObservationRange(CDAModel):
    """Range specification for reference values."""

    class_code: str | None = Field(default="OBS", alias="classCode")
    mood_code: str | None = Field(default="EVN.CRT", alias="moodCode")
    code: CE | None = None
    text: ED | None = None
    # Value can be various types per HL7 V3 spec
    value: (
        CD
        | CE
        | CS
        | ST
        | ED
        | BL
        | INT
        | REAL
        | PQ
        | MO
        | IVL_PQ
        | IVL_INT
        | IVL_TS
        | TS
        | PIVL_TS
        | EIVL_TS
        | RTO
        | II
        | TEL
        | AD
        | EN
        | PN
        | TN
        | ON
        | None
    ) = None
    interpretation_code: CE | None = Field(default=None, alias="interpretationCode")


class EntryRelationship(CDAModel):
    """Relationship between clinical entries.

    Links observations to related observations, acts, or other entries.
    Common type codes:
    - SUBJ: Subject of (e.g., problem observation subject of concern act)
    - MFST: Manifestation of (e.g., reaction manifestation of allergy)
    - REFR: Refers to (e.g., status observation)
    - COMP: Component of (e.g., vital sign component of organizer)
    - RSON: Reason for (e.g., reason for procedure)
    - CAUS: Cause of
    """

    type_code: str | None = Field(default=None, alias="typeCode")
    inversion_ind: bool | None = Field(default=None, alias="inversionInd")
    context_conduction_ind: bool | None = Field(default=None, alias="contextConductionInd")
    negation_ind: bool | None = Field(default=None, alias="negationInd")
    sequence_number: int | None = Field(default=None, alias="sequenceNumber")

    # The related clinical statement (one of these will be present)
    observation: Observation | None = None
    act: Act | None = None
    procedure: Procedure | None = None
    substance_administration: SubstanceAdministration | None = Field(
        default=None, alias="substanceAdministration"
    )
    supply: Supply | None = None
    encounter: Encounter | None = None
    organizer: Organizer | None = None


class Observation(CDAModel):
    """Clinical observation.

    Represents a clinical finding, measurement, or assertion.
    Base model for:
    - Problem Observation (2.16.840.1.113883.10.20.22.4.4)
    - Allergy Intolerance Observation (2.16.840.1.113883.10.20.22.4.7)
    - Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27)
    - Result Observation (2.16.840.1.113883.10.20.22.4.2)
    - Social History Observation (2.16.840.1.113883.10.20.22.4.38)
    - Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78)
    - Reaction Observation (2.16.840.1.113883.10.20.22.4.9)
    - Severity Observation (2.16.840.1.113883.10.20.22.4.8)
    - Problem Status Observation (2.16.840.1.113883.10.20.22.4.6)
    - And many more...
    """

    # Fixed structural attributes
    class_code: str | None = Field(default="OBS", alias="classCode")
    mood_code: str | None = Field(default="EVN", alias="moodCode")

    # Negation indicator (true = "did not occur" or "not present")
    negation_ind: bool | None = Field(default=None, alias="negationInd")

    # Template IDs identifying the observation type
    template_id: list[II] | None = Field(default=None, alias="templateId")

    # Unique identifiers
    id: list[II] | None = None

    # Observation type code (e.g., ASSERTION, LOINC code, SNOMED code)
    # Per C-CDA spec, observation.code uses CD datatype (supports complex terminologies)
    # Accept CE for backward compatibility (CE is a restriction of CD)
    code: CD | CE | None = None

    # Derivation expression (for calculated values)
    derivation_expr: ED | None = Field(default=None, alias="derivationExpr")

    # Narrative text reference
    text: ED | None = None

    # Status code (typically "completed")
    status_code: CS | None = Field(default=None, alias="statusCode")

    # Effective time (when the observation applies)
    effective_time: IVL_TS | None = Field(default=None, alias="effectiveTime")

    # Priority code
    priority_code: CE | None = Field(default=None, alias="priorityCode")

    # Repeat number (for recurring observations)
    repeat_number: IVL_INT | None = Field(default=None, alias="repeatNumber")

    # Language code
    language_code: CS | None = Field(default=None, alias="languageCode")

    # Observation value - can be various types per HL7 V3 spec:
    # - CD/CE/CS (coded value for diagnoses, status)
    # - PQ (physical quantity for measurements)
    # - ST (string)
    # - INT (integer)
    # - REAL (decimal)
    # - IVL_PQ (range of quantities)
    # - BL (boolean)
    # - TS/IVL_TS (timestamps and intervals)
    # - etc.
    # The xsi:type attribute in XML determines the actual type
    value: (
        CD
        | CE
        | CS
        | ST
        | ED
        | BL
        | INT
        | REAL
        | PQ
        | MO
        | IVL_PQ
        | IVL_INT
        | IVL_TS
        | TS
        | PIVL_TS
        | EIVL_TS
        | RTO
        | II
        | TEL
        | AD
        | EN
        | PN
        | TN
        | ON
        | None
    ) = None

    # Interpretation code (e.g., H for high, L for low, N for normal)
    interpretation_code: list[CE] | None = Field(default=None, alias="interpretationCode")

    # Method code (how the observation was made)
    method_code: list[CE] | None = Field(default=None, alias="methodCode")

    # Target site code (anatomical location)
    # Per CDA spec, targetSiteCode uses CD (Concept Descriptor) datatype
    target_site_code: list[CD] | None = Field(default=None, alias="targetSiteCode")

    # Participants (e.g., consumable substance for allergies)
    participant: list[Participant] | None = None

    # Authors
    author: list[Author] | None = None

    # Performers
    performer: list[Performer] | None = None

    # Informants
    informant: list[Informant] | None = None

    # Entry relationships (to related observations, status, severity, etc.)
    entry_relationship: list[EntryRelationship] | None = Field(
        default=None, alias="entryRelationship"
    )

    # Reference ranges
    reference_range: list[ReferenceRange] | None = Field(default=None, alias="referenceRange")

    # Preconditions
    precondition: list[Precondition] | None = None

    def _has_template(self, template_id: str, extension: str | None = None) -> bool:
        """Check if this observation has a specific template ID.

        Args:
            template_id: The template ID root to check for
            extension: Optional template extension to match

        Returns:
            True if template ID is present, False otherwise
        """
        if not self.template_id:
            return False

        for tid in self.template_id:
            if tid.root == template_id:
                if extension is None or tid.extension == extension:
                    return True
        return False

    @model_validator(mode='after')
    def validate_problem_observation(self) -> Observation:
        """Validate Problem Observation template (2.16.840.1.113883.10.20.22.4.4).

        Reference: docs/ccda/observation-problem.md

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode with code="completed"
        4. SHALL contain exactly one [1..1] effectiveTime
           - SHALL contain low
           - SHALL contain high if problem is resolved
        5. SHALL contain exactly one [1..1] value with xsi:type="CD"
        6. SHOULD contain zero or one [0..1] targetSiteCode
        7. SHOULD contain zero or more [0..*] author

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        # Only validate if this is a Problem Observation
        if not self._has_template("2.16.840.1.113883.10.20.22.4.4"):
            return self

        # 1. SHALL contain at least one id
        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "SHALL contain at least one [1..*] id"
            )

        # 2. SHALL contain exactly one code
        if not self.code:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "SHALL contain exactly one [1..1] code"
            )

        # 3. SHALL contain exactly one statusCode with code="completed"
        if not self.status_code:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "SHALL contain exactly one [1..1] statusCode"
            )
        if self.status_code.code != "completed":
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        # 4. SHALL contain exactly one effectiveTime
        if not self.effective_time:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        # 4a. effectiveTime SHALL contain low
        if not self.effective_time.low:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "effectiveTime SHALL contain low element"
            )

        # 5. SHALL contain exactly one value
        if not self.value:
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                "SHALL contain exactly one [1..1] value"
            )

        # 5a. value SHALL be CD or CE type
        if not isinstance(self.value, (CD, CE)):
            raise ValueError(
                "Problem Observation (2.16.840.1.113883.10.20.22.4.4): "
                f"value SHALL have xsi:type of CD or CE, found {type(self.value).__name__}"
            )

        return self

    @model_validator(mode='after')
    def validate_allergy_observation(self) -> Observation:
        """Validate Allergy Intolerance Observation (2.16.840.1.113883.10.20.22.4.7).

        Reference: docs/ccda/observation-allergy-intolerance.md

        Conformance requirements:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode with code="completed"
        4. SHALL contain exactly one [1..1] effectiveTime
        5. SHALL contain exactly one [1..1] value with xsi:type="CD"
        6. SHALL contain exactly one [1..1] participant (the allergen)

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.7"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain exactly one [1..1] statusCode"
            )
        if self.status_code.code != "completed":
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.effective_time:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.value:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain exactly one [1..1] value"
            )
        if not isinstance(self.value, (CD, CE)):
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                f"value SHALL have xsi:type of CD or CE, found {type(self.value).__name__}"
            )

        if not self.participant or len(self.participant) == 0:
            raise ValueError(
                "Allergy Observation (2.16.840.1.113883.10.20.22.4.7): "
                "SHALL contain exactly one [1..1] participant (allergen)"
            )

        return self

    @model_validator(mode='after')
    def validate_vital_sign_observation(self) -> Observation:
        """Validate Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27).

        Reference: docs/ccda/observation-vital-signs.md

        Conformance requirements:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code (LOINC vital sign code)
        3. SHALL contain exactly one [1..1] statusCode with code="completed"
        4. SHALL contain exactly one [1..1] effectiveTime
        5. SHALL contain exactly one [1..1] value with xsi:type="PQ"

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.27"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                "SHALL contain exactly one [1..1] statusCode"
            )
        if self.status_code.code != "completed":
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.effective_time:
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.value:
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                "SHALL contain exactly one [1..1] value"
            )

        # Vital signs MUST have PQ (physical quantity) value
        if not isinstance(self.value, PQ):
            raise ValueError(
                "Vital Sign Observation (2.16.840.1.113883.10.20.22.4.27): "
                f"value SHALL be PQ (Physical Quantity), found {type(self.value).__name__}"
            )

        return self

    @model_validator(mode='after')
    def validate_result_observation(self) -> Observation:
        """Validate Result Observation (2.16.840.1.113883.10.20.22.4.2).

        Reference: docs/ccda/observation-results.md

        Conformance requirements:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode
        4. SHALL contain exactly one [1..1] effectiveTime
        5. SHALL contain exactly one [1..1] value

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.2"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Result Observation (2.16.840.1.113883.10.20.22.4.2): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Result Observation (2.16.840.1.113883.10.20.22.4.2): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Result Observation (2.16.840.1.113883.10.20.22.4.2): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        if not self.effective_time:
            raise ValueError(
                "Result Observation (2.16.840.1.113883.10.20.22.4.2): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.value:
            raise ValueError(
                "Result Observation (2.16.840.1.113883.10.20.22.4.2): "
                "SHALL contain exactly one [1..1] value"
            )

        return self

    @model_validator(mode='after')
    def validate_smoking_status_observation(self) -> Observation:
        """Validate Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78).

        Reference: docs/ccda/observation-smoking-status.md

        Conformance requirements:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode with code="completed"
        4. SHALL contain exactly one [1..1] effectiveTime
        5. SHALL contain exactly one [1..1] value with xsi:type="CD"

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.78"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                "SHALL contain exactly one [1..1] statusCode"
            )
        if self.status_code.code != "completed":
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.effective_time:
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        if not self.value:
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                "SHALL contain exactly one [1..1] value"
            )

        if not isinstance(self.value, (CD, CE)):
            raise ValueError(
                "Smoking Status Observation (2.16.840.1.113883.10.20.22.4.78): "
                f"value SHALL have xsi:type of CD or CE, found {type(self.value).__name__}"
            )

        return self

    @model_validator(mode='after')
    def validate_social_history_observation(self) -> Observation:
        """Validate Social History Observation (2.16.840.1.113883.10.20.22.4.38).

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain exactly one [1..1] code
        2. SHALL contain exactly one [1..1] statusCode (code="completed")
        3. SHALL contain exactly one [1..1] effectiveTime

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.38"):
            return self

        if not self.code:
            raise ValueError(
                "Social History Observation (2.16.840.1.113883.10.20.22.4.38): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Social History Observation (2.16.840.1.113883.10.20.22.4.38): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        if self.status_code.code != "completed":
            raise ValueError(
                "Social History Observation (2.16.840.1.113883.10.20.22.4.38): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.effective_time:
            raise ValueError(
                "Social History Observation (2.16.840.1.113883.10.20.22.4.38): "
                "SHALL contain exactly one [1..1] effectiveTime"
            )

        return self

    @model_validator(mode='after')
    def validate_family_history_observation(self) -> Observation:
        """Validate Family History Observation (2.16.840.1.113883.10.20.22.4.46).

        Conformance requirements from C-CDA R2.1:
        1. SHALL contain at least one [1..*] id
        2. SHALL contain exactly one [1..1] code
        3. SHALL contain exactly one [1..1] statusCode (code="completed")
        4. SHALL contain exactly one [1..1] value

        Raises:
            ValueError: If any SHALL requirement is violated
        """
        if not self._has_template("2.16.840.1.113883.10.20.22.4.46"):
            return self

        if not self.id or len(self.id) == 0:
            raise ValueError(
                "Family History Observation (2.16.840.1.113883.10.20.22.4.46): "
                "SHALL contain at least one [1..*] id"
            )

        if not self.code:
            raise ValueError(
                "Family History Observation (2.16.840.1.113883.10.20.22.4.46): "
                "SHALL contain exactly one [1..1] code"
            )

        if not self.status_code:
            raise ValueError(
                "Family History Observation (2.16.840.1.113883.10.20.22.4.46): "
                "SHALL contain exactly one [1..1] statusCode"
            )

        if self.status_code.code != "completed":
            raise ValueError(
                "Family History Observation (2.16.840.1.113883.10.20.22.4.46): "
                f"statusCode SHALL be 'completed', found '{self.status_code.code}'"
            )

        if not self.value:
            raise ValueError(
                "Family History Observation (2.16.840.1.113883.10.20.22.4.46): "
                "SHALL contain exactly one [1..1] value"
            )

        return self
