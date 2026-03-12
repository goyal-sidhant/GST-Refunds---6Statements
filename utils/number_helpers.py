"""
FILE: utils/number_helpers.py

PURPOSE: Numeric value parsing and formatting helpers. Handles conversion
         between Excel cell values (which may be int, float, or string)
         and the formats needed for validation and JSON output.

CONTAINS:
- parse_amount()       — Converts cell value to a string for regex validation
- to_json_number()     — Converts validated amount to float for JSON output
- is_non_negative()    — Checks if a numeric string represents a non-negative value

DEPENDS ON:
- Nothing (uses only Python standard library)

USED BY:
- core/field_validators.py  → parse_amount() for amount validation
- core/tax_validators.py    → to_json_number() for rate calculation
- core/generators/*.py      → to_json_number() for JSON value output

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — number utility functions  | Phase 0 infrastructure setup       |
"""

from typing import Optional
from decimal import Decimal, InvalidOperation


def parse_amount(value: object) -> str:
    """
    WHAT:
        Converts a raw cell value to a numeric string suitable for
        regex validation. Handles int, float, Decimal, and string inputs.
        Strips whitespace and trailing zeros after decimal point.

    WHY ADDED:
        openpyxl returns numbers as int or float depending on cell format.
        The regex validators expect a string like "1234.56" or "1234".
        This function normalises all numeric types to such a string.

    CALLED BY:
        → core/field_validators.py → validate_amount()

    EDGE CASES HANDLED:
        - None → returns empty string
        - Integer (e.g., 1000) → "1000"
        - Float (e.g., 1000.50) → "1000.5"
        - String with spaces → stripped
        - Negative values → preserved (validation catches them)

    PARAMETERS:
        value (object): Raw cell value from openpyxl.

    RETURNS:
        str: Normalised numeric string, or empty string if None/blank.
    """
    if value is None:
        return ""

    if isinstance(value, (int, float)):
        # Convert to Decimal to avoid floating-point representation issues
        # e.g., 1000.1 might become "1000.0999999..." as float
        try:
            decimal_val = Decimal(str(value))
            # Remove trailing zeros but keep at least the integer part
            normalised = decimal_val.normalize()
            result = str(normalised)
            # Decimal.normalize() may produce "1E+3" for 1000 — fix that
            if "E" in result or "e" in result:
                result = str(decimal_val.quantize(Decimal(1))) if decimal_val == int(decimal_val) else f"{decimal_val:f}"
            return result
        except (InvalidOperation, ValueError):
            return str(value).strip()

    text = str(value).strip()
    return text


def to_json_number(value: object) -> float:
    """
    WHAT:
        Converts a validated amount value to a float for JSON output.
        The GST portal JSON expects numeric values as floats, not strings.

    CALLED BY:
        → core/generators/*.py → all monetary values in JSON nodes

    ASSUMPTIONS:
        *** ASSUMPTION: The value has already been validated by
            field_validators.validate_amount(). This function does
            not re-validate. ***

    PARAMETERS:
        value (object): A validated numeric value (string, int, or float).

    RETURNS:
        float: The numeric value as a Python float.
    """
    if value is None or str(value).strip() == "":
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def is_non_negative(amount_str: str) -> bool:
    """
    WHAT: Checks if a numeric string represents a non-negative value (>= 0).
    CALLED BY: core/field_validators.py → validate_amount()
    RETURNS: True if the value is >= 0, False otherwise.
    """
    if not amount_str:
        return True  # Empty is handled separately as "missing"
    try:
        return float(amount_str) >= 0
    except ValueError:
        return False
