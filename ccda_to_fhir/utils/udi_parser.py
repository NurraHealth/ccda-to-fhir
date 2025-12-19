"""UDI (Unique Device Identifier) parser utility.

Parses UDI strings in GS1, HIBCC, and ICCBBA formats to extract device
identifiers and production identifiers per FDA UDI requirements.

Primary focus is GS1 format (most common in US).

Reference:
- FDA UDI System: https://www.fda.gov/medical-devices/unique-device-identification-system-udi-system
- GS1 Application Identifiers: https://www.gs1.org/standards/barcodes/application-identifiers
"""

from __future__ import annotations

import re
from typing import TypedDict


class UDIParsed(TypedDict, total=False):
    """Parsed UDI components."""

    device_identifier: str | None  # DI - identifies labeler and version/model
    manufacture_date: str | None  # YYYY-MM-DD format
    expiration_date: str | None  # YYYY-MM-DD format
    lot_number: str | None
    serial_number: str | None
    issuer: str | None  # Issuing agency (GS1, HIBCC, ICCBBA)


def parse_udi(udi_string: str) -> UDIParsed:
    """Parse UDI string to extract device and production identifiers.

    Supports GS1 format with application identifiers:
    - (01) - Device Identifier (DI)
    - (11) - Manufacturing date (YYMMDD)
    - (17) - Expiration date (YYMMDD)
    - (10) - Lot number
    - (21) - Serial number

    Args:
        udi_string: UDI string in GS1 format

    Returns:
        Dictionary with parsed UDI components

    Examples:
        >>> parse_udi("(01)51022222233336(11)141231(17)150707(10)A213B1(21)1234")
        {
            'device_identifier': '51022222233336',
            'manufacture_date': '2014-12-31',
            'expiration_date': '2015-07-07',
            'lot_number': 'A213B1',
            'serial_number': '1234',
            'issuer': 'http://hl7.org/fhir/NamingSystem/gs1-di'
        }
    """
    result: UDIParsed = {}

    if not udi_string:
        return result

    # Detect format based on pattern
    if udi_string.startswith("(01)") or re.search(r"\(\d{2}\)", udi_string):
        # GS1 format
        result["issuer"] = "http://hl7.org/fhir/NamingSystem/gs1-di"
        _parse_gs1(udi_string, result)
    elif udi_string.startswith("+"):
        # HIBCC format
        result["issuer"] = "http://hl7.org/fhir/NamingSystem/hibcc-di"
        _parse_hibcc(udi_string, result)
    elif udi_string.startswith("="):
        # ICCBBA format
        result["issuer"] = "http://hl7.org/fhir/NamingSystem/iccbba-di"
        _parse_iccbba(udi_string, result)
    else:
        # Unknown format - treat as device identifier only
        result["device_identifier"] = udi_string

    return result


def _parse_gs1(udi_string: str, result: UDIParsed) -> None:
    """Parse GS1 format UDI with application identifiers.

    Args:
        udi_string: UDI string in GS1 format
        result: Dictionary to populate with parsed values
    """
    # GS1 application identifier pattern: (AI)VALUE
    # AI is 2-4 digits in parentheses, VALUE continues until next (AI) or end

    # Extract Device Identifier (01)
    di_match = re.search(r"\(01\)(\d{14})", udi_string)
    if di_match:
        result["device_identifier"] = di_match.group(1)

    # Extract manufacturing date (11) - format YYMMDD
    mfg_match = re.search(r"\(11\)(\d{6})", udi_string)
    if mfg_match:
        date_str = mfg_match.group(1)
        result["manufacture_date"] = _convert_gs1_date(date_str)

    # Extract expiration date (17) - format YYMMDD
    exp_match = re.search(r"\(17\)(\d{6})", udi_string)
    if exp_match:
        date_str = exp_match.group(1)
        result["expiration_date"] = _convert_gs1_date(date_str)

    # Extract lot number (10) - variable length, ends at next AI or end of string
    lot_match = re.search(r"\(10\)([^()]+?)(?=\(|$)", udi_string)
    if lot_match:
        result["lot_number"] = lot_match.group(1)

    # Extract serial number (21) - variable length, ends at next AI or end of string
    serial_match = re.search(r"\(21\)([^()]+?)(?=\(|$)", udi_string)
    if serial_match:
        result["serial_number"] = serial_match.group(1)


def _convert_gs1_date(date_str: str) -> str:
    """Convert GS1 date format (YYMMDD) to FHIR date (YYYY-MM-DD).

    GS1 uses 2-digit year. Assume:
    - 00-49 = 2000-2049
    - 50-99 = 1950-1999

    Args:
        date_str: Date in YYMMDD format

    Returns:
        Date in YYYY-MM-DD format
    """
    if len(date_str) != 6:
        return date_str

    yy = int(date_str[0:2])
    mm = date_str[2:4]
    dd = date_str[4:6]

    # Convert 2-digit year to 4-digit year
    # Assume 00-49 = 2000-2049, 50-99 = 1950-1999
    if yy >= 50:
        yyyy = f"19{yy}"
    else:
        yyyy = f"20{yy:02d}"

    return f"{yyyy}-{mm}-{dd}"


def _parse_hibcc(udi_string: str, result: UDIParsed) -> None:
    """Parse HIBCC format UDI.

    HIBCC format is less common. Basic implementation for MVP.

    Args:
        udi_string: UDI string in HIBCC format
        result: Dictionary to populate with parsed values
    """
    # HIBCC format starts with +
    # For MVP, just extract the full string as device identifier
    # Full HIBCC parsing can be added in future if needed
    result["device_identifier"] = udi_string.lstrip("+")


def _parse_iccbba(udi_string: str, result: UDIParsed) -> None:
    """Parse ICCBBA format UDI.

    ICCBBA format is less common (used for blood and tissue products).
    Basic implementation for MVP.

    Args:
        udi_string: UDI string in ICCBBA format
        result: Dictionary to populate with parsed values
    """
    # ICCBBA format starts with =
    # For MVP, just extract the full string as device identifier
    # Full ICCBBA parsing can be added in future if needed
    result["device_identifier"] = udi_string.lstrip("=")
