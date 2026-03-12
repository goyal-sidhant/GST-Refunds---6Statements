"""
FILE: utils/string_helpers.py

PURPOSE: Shared string manipulation helpers used across the application.
         All functions are pure (no side effects) and handle None gracefully.

CONTAINS:
- clean_string()          — Strips whitespace and converts to uppercase
- clean_string_preserve()  — Strips whitespace only (preserves case)
- is_blank()              — Checks if a value is None or blank
- safe_str()              — Converts any value to string safely

DEPENDS ON:
- Nothing (pure utility functions)

USED BY:
- core/field_validators.py    → clean_string() for GSTIN, doc numbers
- core/header_validator.py    → clean_string() for header values
- readers/template_reader.py  → safe_str() for cell value conversion

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — string utility functions  | Phase 0 infrastructure setup       |
"""

from typing import Optional


def clean_string(value: object) -> str:
    """
    WHAT: Strips whitespace and converts to uppercase.
    CALLED BY: core/field_validators.py, core/header_validator.py
    RETURNS: Cleaned uppercase string, or empty string if input is None.
    """
    if value is None:
        return ""
    return str(value).strip().upper()


def clean_string_preserve(value: object) -> str:
    """
    WHAT: Strips whitespace but preserves original case.
    CALLED BY: readers/template_reader.py for fields where case matters.
    RETURNS: Stripped string, or empty string if input is None.
    """
    if value is None:
        return ""
    return str(value).strip()


def is_blank(value: object) -> bool:
    """
    WHAT: Returns True if value is None or a blank/whitespace-only string.
    CALLED BY: Multiple validators to check if optional fields are empty.
    RETURNS: True if the value has no meaningful content.
    """
    if value is None:
        return True
    return str(value).strip() == ""


def safe_str(value: object) -> str:
    """
    WHAT: Converts any value to a string safely, returning empty string for None.
    CALLED BY: readers/template_reader.py for cell value normalisation.
    RETURNS: String representation of value, or empty string.
    """
    if value is None:
        return ""
    return str(value)
