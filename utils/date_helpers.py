"""
FILE: utils/date_helpers.py

PURPOSE: Date parsing, conversion, and calculation helpers. Handles the
         conversion between Excel date objects, DD-MM-YYYY strings, and
         MM-YYYY period strings. Also calculates financial years for
         duplicate detection (Indian FY runs April-March).

CONTAINS:
- parse_date()                — Converts various date inputs to DD-MM-YYYY string
- parse_period()              — Converts various period inputs to MM-YYYY string
- parse_date_to_object()      — Converts DD-MM-YYYY string to datetime.date
- period_to_mmyyyy()          — Converts MM-YYYY to mmyyyy (strips hyphen for JSON)
- period_to_date_range()      — Converts MM-YYYY to (first_day, last_day) date objects
- get_financial_year()        — Returns FY year for a given date/month
- get_month_from_date()       — Extracts month number from DD-MM-YYYY string
- is_date_before()            — Compares two DD-MM-YYYY date strings

DEPENDS ON:
- Nothing (uses only Python standard library)

USED BY:
- core/field_validators.py    → parse_date(), parse_date_to_object()
- core/header_validator.py    → period_to_mmyyyy()
- core/duplicate_detector.py  → get_financial_year(), get_month_from_date()
- core/date_validators.py     → is_date_before(), period_to_date_range()
- core/generators/*.py        → period_to_mmyyyy()
- readers/template_reader.py  → parse_period() for header period cells

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — date utility functions    | Phase 0 infrastructure setup       |
| 12-03-2026 | Added parse_period() for MM-YYYY    | Excel converts 04-2024 to datetime |
| 12-03-2026 | Added period_to_date_range()        | BRC date must fall within period    |
"""

import calendar
from datetime import date, datetime
from typing import Optional


def parse_date(value: object) -> str:
    """
    WHAT:
        Converts various date representations to a DD-MM-YYYY string.
        Handles: datetime objects (from openpyxl), date objects, strings
        in DD-MM-YYYY or DD/MM/YYYY format, and numeric values.

    WHY ADDED:
        openpyxl returns dates as datetime objects if the cell is formatted
        as a date, but as strings if the cell is formatted as text.
        This function normalises both to a consistent DD-MM-YYYY string.

    CALLED BY:
        → readers/template_reader.py → normalise cell values
        → core/field_validators.py → validate date fields

    EDGE CASES HANDLED:
        - None → returns empty string
        - datetime.datetime → extracts date portion
        - datetime.date → formats directly
        - String with / separators → converts to - separators
        - Already DD-MM-YYYY → returns as-is

    PARAMETERS:
        value (object): Raw cell value from openpyxl.

    RETURNS:
        str: Date in DD-MM-YYYY format, or empty string if None/unparseable.
    """
    if value is None:
        return ""

    # openpyxl returns datetime for date-formatted cells
    if isinstance(value, datetime):
        return value.strftime("%d-%m-%Y")

    if isinstance(value, date):
        return value.strftime("%d-%m-%Y")

    text = str(value).strip()
    if not text:
        return ""

    # Convert / separators to - (some users may use DD/MM/YYYY)
    text = text.replace("/", "-")

    return text


def parse_period(value: object) -> str:
    """
    WHAT:
        Converts various period representations to a MM-YYYY string.
        Handles: datetime objects (Excel auto-converts "04-2024" to a
        datetime), date objects, and plain strings.

    WHY ADDED:
        When a user types "04-2024" in an Excel cell, Excel may auto-format
        it as a date (2024-04-01 00:00:00). The reader was doing str(raw)
        which gave "2024-04-01 00:00:00" — failing the MM-YYYY regex.
        This function detects datetime objects and extracts MM-YYYY.

    CALLED BY:
        → readers/template_reader.py → _read_header() for from_period, to_period

    EDGE CASES HANDLED:
        - None → returns empty string
        - datetime.datetime → extracts month-year as MM-YYYY
        - datetime.date → formats as MM-YYYY
        - String → strips whitespace, returns as-is (regex validates later)

    PARAMETERS:
        value (object): Raw cell value from openpyxl.

    RETURNS:
        str: Period in MM-YYYY format, or empty string if None.
    """
    if value is None:
        return ""

    # Excel converts "04-2024" to datetime(2024, 4, 1) — extract MM-YYYY
    if isinstance(value, datetime):
        return value.strftime("%m-%Y")

    if isinstance(value, date):
        return value.strftime("%m-%Y")

    text = str(value).strip()
    if not text:
        return ""

    return text


def parse_date_to_object(date_str: str) -> Optional[date]:
    """
    WHAT:
        Converts a DD-MM-YYYY string to a datetime.date object.
        Returns None if the string is not a valid date.

    CALLED BY:
        → core/field_validators.py → date range and comparison checks
        → core/date_validators.py → chronological ordering

    PARAMETERS:
        date_str (str): Date string in DD-MM-YYYY format.

    RETURNS:
        date or None: Parsed date object, or None if invalid.
    """
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%d-%m-%Y").date()
    except (ValueError, TypeError):
        return None


def period_to_mmyyyy(period_str: str) -> str:
    """
    WHAT:
        Converts MM-YYYY format (with hyphen) to mmyyyy format (no hyphen)
        for JSON output. The custom templates use MM-YYYY to prevent Excel
        from stripping leading zeros; the GST portal JSON expects mmyyyy.

    CALLED BY:
        → core/generators/*.py → fromFp and toFp values in JSON envelope

    ASSUMPTIONS:
        *** ASSUMPTION: Input is already validated as MM-YYYY format by
            the header validator. This function does not re-validate. ***

    PARAMETERS:
        period_str (str): Period in MM-YYYY format (e.g., "04-2026").

    RETURNS:
        str: Period in mmyyyy format (e.g., "042026").
    """
    if not period_str:
        return ""
    return period_str.replace("-", "")


def period_to_date_range(period_str: str) -> Optional[tuple[date, date]]:
    """
    WHAT:
        Converts an MM-YYYY period string to a (first_day, last_day) tuple.
        For example, "03-2025" → (date(2025, 3, 1), date(2025, 3, 31)).

    WHY ADDED:
        BRC/FIRC dates must fall within the refund period (From → To).
        We need to compare a DD-MM-YYYY date against the boundaries of
        an MM-YYYY period. This function gives us those boundaries.

    CALLED BY:
        → core/date_validators.py → validate_brc_within_period()

    EDGE CASES HANDLED:
        - February in leap years → calendar.monthrange handles correctly
        - None or empty input → returns None
        - Invalid format → returns None

    PARAMETERS:
        period_str (str): Period in MM-YYYY format (e.g., "03-2025").

    RETURNS:
        tuple[date, date] or None: (first_day, last_day) of the month,
        or None if the input is empty or unparseable.
    """
    if not period_str:
        return None
    try:
        parts = period_str.split("-")
        month = int(parts[0])
        year = int(parts[1])
        first_day = date(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = date(year, month, last_day_num)
        return (first_day, last_day)
    except (ValueError, IndexError):
        return None


def get_financial_year(month: int, year: int) -> int:
    """
    WHAT:
        Returns the financial year start year for a given month/year.
        Indian FY runs April to March: Jan-Mar 2026 belongs to FY 2025-26.

    WHY ADDED:
        Duplicate detection keys include the financial year. The government
        VBA adjusts: if month is Jan-Mar (1-3), the FY year is previous year.

    CALLED BY:
        → core/duplicate_detector.py → builds duplicate detection keys

    PARAMETERS:
        month (int): Month number (1-12).
        year (int):  Calendar year (e.g., 2026).

    RETURNS:
        int: Financial year start year. For April 2026 → 2026.
             For January 2026 → 2025.
    """
    if month <= 3:
        return year - 1
    return year


def get_month_year_from_date(date_str: str) -> tuple[int, int]:
    """
    WHAT:
        Extracts month and year from a DD-MM-YYYY string.

    CALLED BY:
        → core/duplicate_detector.py → extracts month/year for FY calculation

    PARAMETERS:
        date_str (str): Date in DD-MM-YYYY format.

    RETURNS:
        tuple[int, int]: (month, year) or (0, 0) if unparseable.
    """
    parsed = parse_date_to_object(date_str)
    if parsed is None:
        return (0, 0)
    return (parsed.month, parsed.year)


def is_date_before(date_a: str, date_b: str) -> Optional[bool]:
    """
    WHAT:
        Returns True if date_a is strictly before date_b.
        Both dates must be in DD-MM-YYYY format.

    CALLED BY:
        → core/date_validators.py → chronological checks (SB >= Invoice)

    RETURNS:
        bool or None: True if A < B, False if A >= B, None if either is unparseable.
    """
    obj_a = parse_date_to_object(date_a)
    obj_b = parse_date_to_object(date_b)
    if obj_a is None or obj_b is None:
        return None
    return obj_a < obj_b
