"""
FILE: core/header_validator.py

PURPOSE: Validates all header-level fields: GSTIN (format + checksum),
         return periods (format, range, ordering), and order fields (S06).
         This runs after template enforcement and before row-level validation.

CONTAINS:
- validate_header()  — Main header validation function

DEPENDS ON:
- core/gstin_validator.py        → validate_gstin() for checksum
- config/regex_patterns.py       → RETURN_PERIOD_REGEX, DATE_REGEX
- config/constants.py            → GST_INCEPTION_DATE
- config/error_messages.py       → HEADER_ERRORS
- models/header.py               → HeaderData
- models/statement_config.py     → HeaderMode
- models/validation_result.py    → ValidationResult
- utils/date_helpers.py          → parse_date_to_object()

USED BY:
- readers/template_reader.py     → called after reading header data

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — header validation         | Phase 0 infrastructure setup       |
"""

from datetime import date

from core.gstin_validator import validate_gstin
from config.regex_patterns import RETURN_PERIOD_REGEX, DATE_REGEX
from config.constants import GST_INCEPTION_DATE
from config.error_messages import HEADER_ERRORS
from models.header import HeaderData
from models.statement_config import HeaderMode
from models.validation_result import ValidationResult
from utils.date_helpers import parse_date_to_object
from utils.string_helpers import clean_string


def validate_header(
    header: HeaderData,
    header_mode: HeaderMode,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Validates all header-level fields based on the statement's header mode.
        Adds errors to the ValidationResult for any invalid field.

    WHY ADDED:
        Every statement needs GSTIN validation. Statements with periods
        (S01A, S03, S05) need period validation. S06 needs order field
        validation. This function handles all three modes.

    CALLED BY:
        → readers/template_reader.py → after reading header data

    CALLS:
        → core/gstin_validator.py → validate_gstin() for checksum
        → config/regex_patterns.py → RETURN_PERIOD_REGEX

    EDGE CASES HANDLED:
        - None or empty GSTIN → specific error message
        - GSTIN with spaces/lowercase → the external validator auto-corrects
        - Period with invalid month (e.g., 13-2026) → regex catches it
        - To Period before From Period → comparison check

    PARAMETERS:
        header (HeaderData):        The header data to validate.
        header_mode (HeaderMode):   Which fields to expect.
        result (ValidationResult):  Errors are added here.
    """
    # --- GSTIN Validation (all statements) ---
    _validate_gstin(header, result)

    # --- Period Validation (PERIODS mode: S01A, S03, S05) ---
    if header_mode == HeaderMode.PERIODS:
        _validate_periods(header, result)

    # --- Order Validation (ORDER mode: S06) ---
    if header_mode == HeaderMode.ORDER:
        _validate_order(header, result)


def _validate_gstin(header: HeaderData, result: ValidationResult) -> None:
    """
    WHAT: Validates the GSTIN from the header sheet using the external
          GSTIN validator skill (format + checksum).
    CALLED BY: validate_header() above.
    """
    gstin = clean_string(header.gstin)

    if not gstin:
        result.add_error(
            message=HEADER_ERRORS["gstin_empty"],
            sheet="Header",
            category="header",
        )
        return

    # Use the full GSTIN validator (Luhn Mod 36 checksum + structure)
    gstin_result = validate_gstin(gstin)

    if not gstin_result["valid"]:
        # Check if it's a checksum issue specifically
        components = gstin_result.get("components") or {}
        if components.get("check_digit_valid") is False:
            result.add_error(
                message=HEADER_ERRORS["gstin_checksum_failed"].format(
                    gstin=gstin,
                    expected=components.get("check_digit_expected", "?"),
                    actual=components.get("check_digit", "?"),
                ),
                sheet="Header",
                field_name="GSTIN",
                category="header",
            )
        else:
            # General format error — use first error from validator
            error_msg = gstin_result["errors"][0] if gstin_result["errors"] else "Unknown error"
            result.add_error(
                message=HEADER_ERRORS["gstin_invalid_format"].format(gstin=gstin)
                + f" Detail: {error_msg}",
                sheet="Header",
                field_name="GSTIN",
                category="header",
            )

    # Store the processed (cleaned) GSTIN back for downstream use
    if gstin_result.get("processed"):
        header.gstin = gstin_result["processed"]


def _validate_periods(header: HeaderData, result: ValidationResult) -> None:
    """
    WHAT: Validates From Period and To Period fields (MM-YYYY format).
    CALLED BY: validate_header() for PERIODS mode.
    """
    today = date.today()

    # --- From Period ---
    from_period = clean_string(header.from_period) if header.from_period else ""
    if not from_period:
        result.add_error(
            message=HEADER_ERRORS["from_period_empty"],
            sheet="Header",
            field_name="From Period",
            category="header",
        )
    elif not RETURN_PERIOD_REGEX.match(from_period):
        result.add_error(
            message=HEADER_ERRORS["period_invalid_format"].format(value=from_period),
            sheet="Header",
            field_name="From Period",
            category="header",
        )
    else:
        from_date = _period_to_date(from_period)
        if from_date and from_date < GST_INCEPTION_DATE:
            result.add_error(
                message=HEADER_ERRORS["period_before_gst"].format(value=from_period),
                sheet="Header",
                field_name="From Period",
                category="header",
            )
        if from_date and from_date > today:
            result.add_error(
                message=HEADER_ERRORS["period_future"].format(value=from_period),
                sheet="Header",
                field_name="From Period",
                category="header",
            )

    # --- To Period ---
    to_period = clean_string(header.to_period) if header.to_period else ""
    if not to_period:
        result.add_error(
            message=HEADER_ERRORS["to_period_empty"],
            sheet="Header",
            field_name="To Period",
            category="header",
        )
    elif not RETURN_PERIOD_REGEX.match(to_period):
        result.add_error(
            message=HEADER_ERRORS["period_invalid_format"].format(value=to_period),
            sheet="Header",
            field_name="To Period",
            category="header",
        )
    else:
        to_date = _period_to_date(to_period)
        if to_date and to_date < GST_INCEPTION_DATE:
            result.add_error(
                message=HEADER_ERRORS["period_before_gst"].format(value=to_period),
                sheet="Header",
                field_name="To Period",
                category="header",
            )
        if to_date and to_date > today:
            result.add_error(
                message=HEADER_ERRORS["period_future"].format(value=to_period),
                sheet="Header",
                field_name="To Period",
                category="header",
            )

    # --- Cross-check: To >= From ---
    if from_period and to_period:
        from_date = _period_to_date(from_period)
        to_date = _period_to_date(to_period)
        if from_date and to_date and to_date < from_date:
            result.add_error(
                message=HEADER_ERRORS["to_before_from"].format(
                    from_period=from_period,
                    to_period=to_period,
                ),
                sheet="Header",
                category="header",
            )


def _validate_order(header: HeaderData, result: ValidationResult) -> None:
    """
    WHAT: Validates Order Number and Order Date fields (S06 only).
    CALLED BY: validate_header() for ORDER mode.
    """
    # --- Order Number ---
    if not header.order_no or not str(header.order_no).strip():
        result.add_error(
            message=HEADER_ERRORS["order_no_empty"],
            sheet="Header",
            field_name="Order No",
            category="header",
        )

    # --- Order Date ---
    order_date_str = str(header.order_date).strip() if header.order_date else ""
    if not order_date_str:
        result.add_error(
            message=HEADER_ERRORS["order_date_empty"],
            sheet="Header",
            field_name="Order Date",
            category="header",
        )
    else:
        parsed = parse_date_to_object(order_date_str)
        if parsed is None:
            result.add_error(
                message=HEADER_ERRORS["order_date_invalid"].format(value=order_date_str),
                sheet="Header",
                field_name="Order Date",
                category="header",
            )


def _period_to_date(period_str: str) -> date | None:
    """
    WHAT: Converts MM-YYYY to the first day of that month as a date object.
    CALLED BY: _validate_periods() for date comparisons.
    RETURNS: date object or None if unparseable.
    """
    try:
        parts = period_str.split("-")
        month = int(parts[0])
        year = int(parts[1])
        return date(year, month, 1)
    except (ValueError, IndexError):
        return None
