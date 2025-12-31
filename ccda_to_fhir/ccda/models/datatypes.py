"""C-CDA/HL7 V3 data type models.

These models represent the core HL7 V3 data types used in C-CDA documents.
Reference: http://www.hl7.org/implement/standards/product_brief.cfm?product_id=264
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CDAModel(BaseModel):
    """Base class for all C-CDA models with common configuration."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="ignore",  # C-CDA XML may have extra attributes we don't need
        validate_assignment=True,
    )


# -----------------------------------------------------------------------------
# Simple Data Types
# -----------------------------------------------------------------------------


class ST(CDAModel):
    """Character String (ST).

    Plain text content without markup.
    """

    value: str | None = Field(default=None, alias="_text")


class BL(CDAModel):
    """Boolean (BL).

    A binary value indicating true or false.
    """

    value: bool | None = None


class INT(CDAModel):
    """Integer Number (INT).

    A whole number.
    """

    value: int | None = None


class REAL(CDAModel):
    """Real Number (REAL).

    A decimal number.
    """

    value: float | None = None


# -----------------------------------------------------------------------------
# Identifier Types
# -----------------------------------------------------------------------------


class II(CDAModel):
    """Instance Identifier (II).

    An identifier that uniquely identifies an instance of an object.
    In C-CDA, identifiers typically have a root (OID or UUID) and optionally
    an extension.

    Must contain either root or nullFlavor.
    """

    root: str | None = None
    extension: str | None = None
    assigning_authority_name: str | None = Field(default=None, alias="assigningAuthorityName")
    displayable: bool | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


# -----------------------------------------------------------------------------
# Coded Types
# -----------------------------------------------------------------------------


class CD(CDAModel):
    """Concept Descriptor (CD).

    A reference to a concept defined in a code system.
    This is the base type for coded values in C-CDA.
    """

    code: str | None = None
    code_system: str | None = Field(default=None, alias="codeSystem")
    code_system_name: str | None = Field(default=None, alias="codeSystemName")
    code_system_version: str | None = Field(default=None, alias="codeSystemVersion")
    display_name: str | None = Field(default=None, alias="displayName")
    original_text: ED | None = Field(default=None, alias="originalText")
    translation: list[CD] | None = None
    qualifier: list[CR] | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class CE(CD):
    """Coded with Equivalents (CE).

    A coded value that may have translations to other code systems.
    Functionally equivalent to CD in most C-CDA usage.
    """

    pass


class CO(CE):
    """Coded Ordinal (CO).

    Extends CE with ordering semantics. Used for coded values that have
    an inherent ordering, such as:
    - Severity scales (mild, moderate, severe)
    - Stage classifications (stage I, II, III, IV)
    - Rankings or grades

    Implementation Note:
    Per HL7 V3 spec, CO extends CV (Coded Value). However, in this implementation,
    CO extends CE to support translation elements commonly found in C-CDA documents.
    This pragmatic approach aligns with real-world C-CDA usage while maintaining
    semantic ordering. Structurally identical to CE but semantically implies ordering.

    Example:
        <value xsi:type="CO" code="LA6752-5" codeSystem="2.16.840.1.113883.6.1"
               displayName="Mild" codeSystemName="LOINC"/>
    """

    pass


class CV(CD):
    """Coded Value (CV).

    A coded value with a single code system.
    """

    pass


class CS(CDAModel):
    """Coded Simple (CS).

    A simple coded value from a fixed vocabulary (no code system specified).
    """

    code: str | None = None
    display_name: str | None = Field(default=None, alias="displayName")
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class CR(CDAModel):
    """Concept Role (CR).

    A concept qualifier specifying a name-value pair.
    """

    name: CV | None = None
    value: CD | None = None


# -----------------------------------------------------------------------------
# Encapsulated Data Types
# -----------------------------------------------------------------------------


class ED(CDAModel):
    """Encapsulated Data (ED).

    Data that is primarily intended for human interpretation or further
    machine processing (like images or rich text).
    """

    media_type: str | None = Field(default=None, alias="mediaType")
    language: str | None = None
    charset: str | None = None
    compression: str | None = None
    representation: str | None = None
    value: str | None = Field(default=None, alias="_text")
    reference: TEL | None = None


class TELReference(CDAModel):
    """Reference element within text content.

    Used to reference narrative text by ID.
    """

    value: str | None = None


# -----------------------------------------------------------------------------
# Quantity Types
# -----------------------------------------------------------------------------


class PQ(CDAModel):
    """Physical Quantity (PQ).

    A dimensioned quantity expressing the result of a measurement.
    """

    value: float | str | None = None
    unit: str | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")
    translation: list[PQ] | None = None


class PPD_PQ(PQ):
    """Parametric Probability Distribution of Physical Quantity (PPD<PQ>).

    Extends PQ with statistical distribution parameters. Used to express
    uncertainty or variability in measurements, commonly in medication
    timing specifications.

    Example: "Every 5±1 hours" would be:
        <period xsi:type="PPD_PQ" value="5.00" unit="h">
          <standardDeviation value="1.00" unit="h"/>
        </period>

    Note: When converting to FHIR, the statistical parameters (standardDeviation,
    distributionType) are typically lost as FHIR Timing does not support
    probability distributions. The base value and unit are preserved.
    """

    standard_deviation: PQ | None = Field(default=None, alias="standardDeviation")
    distribution_type: str | None = Field(default=None, alias="distributionType")


class RTO(CDAModel):
    """Ratio (RTO).

    A ratio of two quantities.
    """

    numerator: PQ | None = None
    denominator: PQ | None = None


class MO(CDAModel):
    """Monetary Amount (MO).

    A monetary value.
    """

    value: float | None = None
    currency: str | None = None


# -----------------------------------------------------------------------------
# Time Types
# -----------------------------------------------------------------------------


class TS(CDAModel):
    """Point in Time (TS).

    A timestamp representing a point in time.
    Format: YYYYMMDDHHMMSS.UUUU[+|-ZZzz]
    """

    value: str | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class IVL_TS(CDAModel):
    """Interval of Time (IVL<TS>).

    A time interval with optional low and high bounds.
    """

    value: str | None = None  # For point-in-time (effectiveTime with just @value)
    low: TS | None = None
    high: TS | None = None
    center: TS | None = None
    width: PQ | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")
    operator: str | None = None  # I (intersect), A (union), etc.


class PIVL_TS(CDAModel):
    """Periodic Interval of Time (PIVL<TS>).

    A time interval that recurs periodically.
    Period can be:
    - PQ: Simple physical quantity (e.g., "every 6 hours")
    - IVL_PQ: Interval range (e.g., "every 4-6 hours")
    - PPD_PQ: With probability distribution (e.g., "every 5±1 hours")
    """

    phase: IVL_TS | None = None
    period: PQ | IVL_PQ | PPD_PQ | None = None
    alignment: str | None = None
    institution_specified: bool | None = Field(default=None, alias="institutionSpecified")
    operator: str | None = None


class EIVL_TS(CDAModel):
    """Event-Related Interval (EIVL<TS>).

    A time interval related to an event (e.g., before meals).
    """

    event: CE | None = None
    offset: PQ | IVL_PQ | PPD_PQ | None = None
    operator: str | None = None


class SXCM_TS(CDAModel):
    """Set Component of Time (SXCM<TS>).

    A component of a set of times, with an optional operator.
    """

    value: str | None = None
    operator: str | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class GTS(CDAModel):
    """General Timing Specification (GTS).

    A complex timing specification that can be a single interval or
    a set of intervals.
    """

    # Can contain IVL_TS, PIVL_TS, or EIVL_TS components
    pass


# -----------------------------------------------------------------------------
# Interval of Physical Quantity
# -----------------------------------------------------------------------------


class IVL_PQ(CDAModel):
    """Interval of Physical Quantity (IVL<PQ>).

    A range of physical quantities.
    Can be expressed as an interval (low/high) or as a single value.
    """

    # Single value (shorthand for low=high=value)
    value: str | None = None

    # Interval bounds
    low: PQ | None = None
    high: PQ | None = None
    center: PQ | None = None
    width: PQ | None = None
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class IVL_INT(CDAModel):
    """Interval of Integer (IVL<INT>).

    A range of integers.
    """

    low: INT | None = None
    high: INT | None = None


# -----------------------------------------------------------------------------
# Telecommunication Address
# -----------------------------------------------------------------------------


class TEL(CDAModel):
    """Telecommunication Address (TEL).

    A telephone number, email address, or URL.
    Value format: scheme:address (e.g., tel:+1-555-555-1234, mailto:x@y.com)
    """

    value: str | None = None
    use: str | None = None  # HP (primary home), WP (work), MC (mobile), etc.
    use_period: IVL_TS | None = Field(default=None, alias="usablePeriod")
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


# -----------------------------------------------------------------------------
# Address Types
# -----------------------------------------------------------------------------


class AD(CDAModel):
    """Postal Address (AD).

    A mailing address with geographic and street-level components.
    """

    use: str | None = None  # H (home), HP (primary home), WP (work), TMP (temporary), BAD
    is_not_ordered: bool | None = Field(default=None, alias="isNotOrdered")

    # Geographic components
    country: str | None = None
    state: str | None = None
    county: str | None = None
    city: str | None = None
    postal_code: str | None = Field(default=None, alias="postalCode")
    census_tract: str | None = Field(default=None, alias="censusTract")
    precinct: str | None = None

    # Street components
    street_address_line: list[str] | None = Field(default=None, alias="streetAddressLine")
    house_number: str | None = Field(default=None, alias="houseNumber")
    street_name: str | None = Field(default=None, alias="streetName")
    street_name_base: str | None = Field(default=None, alias="streetNameBase")
    street_name_type: str | None = Field(default=None, alias="streetNameType")
    direction: str | None = None
    additional_locator: str | None = Field(default=None, alias="additionalLocator")

    # Unit/building components
    unit_id: str | None = Field(default=None, alias="unitID")
    unit_type: str | None = Field(default=None, alias="unitType")

    # Delivery components
    delivery_address_line: str | None = Field(default=None, alias="deliveryAddressLine")
    delivery_mode: str | None = Field(default=None, alias="deliveryMode")
    post_box: str | None = Field(default=None, alias="postBox")
    care_of: str | None = Field(default=None, alias="careOf")

    # Timing
    useable_period: IVL_TS | None = Field(default=None, alias="useablePeriod")
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


# -----------------------------------------------------------------------------
# Name Types
# -----------------------------------------------------------------------------


class ENXP(CDAModel):
    """Entity Name Part (ENXP).

    A part of a name with optional qualifier.
    """

    value: str | None = Field(default=None, alias="_text")
    qualifier: str | None = None  # AC (academic), CL (callme/nickname), etc.


class EN(CDAModel):
    """Entity Name (EN).

    A name for an entity (person, organization, place).
    """

    use: str | None = None  # L (legal), OR (official record), P (pseudonym), etc.
    prefix: list[ENXP] | None = None
    given: list[ENXP] | None = None
    family: ENXP | None = None
    suffix: list[ENXP] | None = None
    delimiter: list[str] | None = None
    valid_time: IVL_TS | None = Field(default=None, alias="validTime")
    null_flavor: str | None = Field(default=None, alias="nullFlavor")


class PN(EN):
    """Person Name (PN).

    A name for a person.
    """

    pass


class ON(EN):
    """Organization Name (ON).

    A name for an organization.
    """

    value: str | None = Field(default=None, alias="_text")


class TN(EN):
    """Trivial Name (TN).

    A simple string name without parts.
    """

    value: str | None = Field(default=None, alias="_text")


# -----------------------------------------------------------------------------
# Update forward references
# -----------------------------------------------------------------------------

CD.model_rebuild()
ED.model_rebuild()
