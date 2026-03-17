"""
FILE: core/field_validators.py

PURPOSE: Shared field-level validators used by all 6 statement types.
         Each function validates one type of field (date, amount, doc no,
         doc type, port code, shipping bill, EGM, BRC) and adds errors
         to the ValidationResult if invalid.

CONTAINS:
- validate_doc_type()      — Checks against allowed document types
- validate_doc_no()        — Regex check for document number format
- validate_date()          — Format, range, and future-date checks
- validate_amount()        — Regex + non-negative check with configurable decimals
- validate_port_code()     — Exactly 6 alphanumeric characters
- validate_shipping_bill() — 3-7 digits only
- validate_endorsed_invoice() — Alphanumeric with / and - (S04, S05)
- validate_egm_ref()       — 1-20 alphanumeric, no backslash/quotes
- validate_brc_fields()    — All-or-nothing BRC/FIRC field validation

DEPENDS ON:
- config/regex_patterns.py     → all regex patterns
- config/constants.py          → GST_INCEPTION_DATE, DOCUMENT_TYPES
- config/error_messages.py     → DOCUMENT_ERRORS, SHIPPING_ERRORS, BRC_ERRORS
- models/validation_result.py  → ValidationResult
- utils/date_helpers.py        → parse_date(), parse_date_to_object()
- utils/number_helpers.py      → parse_amount()
- utils/string_helpers.py      → clean_string(), is_blank()

USED BY:
- core/validators/*.py → all statement-specific validators call these

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — shared field validators   | Phase 0 infrastructure setup       |
| 17-03-2026 | validate_doc_no: float-to-int       | Excel Number-formatted cells       |
|            |   cleanup (e.g., 1234.0 → "1234")   |   return float; prevents regex fail|
"""

from datetime import date

from config.regex_patterns import (
    DOC_NO_REGEX,
    DATE_REGEX,
    AMOUNT_REGEX,
    FOB_AMOUNT_REGEX,
    PORT_CODE_REGEX,
    SHIPPING_BILL_REGEX,
    ENDORSED_INVOICE_REGEX,
    EGM_REF_REGEX,
    BRC_NO_REGEX,
)
from config.constants import GST_INCEPTION_DATE, DOCUMENT_TYPES
from config.error_messages import DOCUMENT_ERRORS, SHIPPING_ERRORS, BRC_ERRORS
from models.validation_result import ValidationResult
from utils.date_helpers import parse_date, parse_date_to_object
from utils.number_helpers import parse_amount, is_non_negative
from utils.string_helpers import clean_string, is_blank


def validate_doc_type(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> str:
    """
    WHAT: Validates document type is one of Invoice/Debit Note/Credit Note.
    RETURNS: Cleaned doc type string (or empty if invalid).
    """
    cleaned = clean_string(value)
    if not cleaned:
        result.add_error(
            message=DOCUMENT_ERRORS["doc_type_empty"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Doc Type", category="document",
        )
        return ""

    # Check against allowed values (case-insensitive comparison)
    for valid_type in DOCUMENT_TYPES:
        if cleaned == valid_type.upper():
            return valid_type  # Return the canonical form

    result.add_error(
        message=DOCUMENT_ERRORS["doc_type_invalid"].format(row=row, sheet=sheet, value=value),
        sheet=sheet, row=row, field_name="Doc Type", category="document",
    )
    return ""


def validate_doc_no(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> str:
    """
    WHAT: Validates document number format (1-16 alphanumeric, / and - allowed).
          Handles Excel numeric values (e.g., 1234.0 from Number-formatted cells).
    RETURNS: Cleaned doc number string (or empty if invalid).
    """
    cleaned = str(value).strip() if value is not None else ""
    # Handle Excel float values (e.g., 1234.0 → "1234").
    # Same pattern as validate_shipping_bill().
    if cleaned and "." in cleaned:
        try:
            cleaned = str(int(float(cleaned)))
        except (ValueError, OverflowError):
            pass
    if not cleaned:
        result.add_error(
            message=DOCUMENT_ERRORS["doc_no_empty"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Doc No", category="document",
        )
        return ""

    if not DOC_NO_REGEX.match(cleaned):
        result.add_error(
            message=DOCUMENT_ERRORS["doc_no_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name="Doc No", category="document",
        )
        return ""

    return cleaned


def validate_date(
    value: object,
    row: int,
    sheet: str,
    field_name: str,
    result: ValidationResult,
    error_key_prefix: str = "doc",
    check_gst_inception: bool = True,
    check_future: bool = True,
    to_period_date: date | None = None,
) -> str:
    """
    WHAT: Validates a date field — format, range, and optionally period bounds.

    PARAMETERS:
        value: Raw cell value.
        row: Excel row number.
        sheet: Sheet name.
        field_name: Display name for error messages.
        result: ValidationResult to add errors to.
        error_key_prefix: Prefix for error message keys (e.g., "doc", "shipping_bill").
        check_gst_inception: If True, reject dates before 01-07-2017.
        check_future: If True, reject future dates.
        to_period_date: If provided, reject dates after this date.

    RETURNS: Date string in DD-MM-YYYY format (or empty if invalid).
    """
    date_str = parse_date(value)
    if not date_str:
        # Determine which "empty" error to use based on prefix
        error_key = f"{error_key_prefix}_date_empty"
        error_dict = _get_error_dict(error_key_prefix)
        if error_key in error_dict:
            result.add_error(
                message=error_dict[error_key].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name=field_name, category="document",
            )
        return ""

    # Format check
    if not DATE_REGEX.match(date_str):
        error_key = f"{error_key_prefix}_date_invalid"
        error_dict = _get_error_dict(error_key_prefix)
        if error_key in error_dict:
            result.add_error(
                message=error_dict[error_key].format(row=row, sheet=sheet, value=date_str),
                sheet=sheet, row=row, field_name=field_name, category="document",
            )
        return ""

    # Parse to date object for range checks
    date_obj = parse_date_to_object(date_str)
    if date_obj is None:
        error_key = f"{error_key_prefix}_date_invalid"
        error_dict = _get_error_dict(error_key_prefix)
        if error_key in error_dict:
            result.add_error(
                message=error_dict[error_key].format(row=row, sheet=sheet, value=date_str),
                sheet=sheet, row=row, field_name=field_name, category="document",
            )
        return ""

    # GST inception check
    if check_gst_inception and date_obj < GST_INCEPTION_DATE:
        result.add_error(
            message=DOCUMENT_ERRORS["doc_date_before_gst"].format(row=row, sheet=sheet, value=date_str),
            sheet=sheet, row=row, field_name=field_name, category="document",
        )

    # Future date check
    if check_future and date_obj > date.today():
        error_key = f"{error_key_prefix}_date_future"
        error_dict = _get_error_dict(error_key_prefix)
        if error_key in error_dict:
            result.add_error(
                message=error_dict[error_key].format(row=row, sheet=sheet, value=date_str),
                sheet=sheet, row=row, field_name=field_name, category="document",
            )

    # Period bounds check
    if to_period_date and date_obj > to_period_date:
        result.add_error(
            message=DOCUMENT_ERRORS["doc_date_after_period"].format(row=row, sheet=sheet, value=date_str),
            sheet=sheet, row=row, field_name=field_name, category="document",
        )

    return date_str


def validate_amount(
    value: object,
    row: int,
    sheet: str,
    field_name: str,
    result: ValidationResult,
    error_key: str,
    is_mandatory: bool = True,
    decimal_places: int = 2,
) -> str:
    """
    WHAT: Validates a monetary value — format, non-negative, decimal places.
    RETURNS: Normalised amount string (or empty if invalid/blank).
    """
    amount_str = parse_amount(value)

    if not amount_str:
        if is_mandatory:
            error_dict = _get_error_dict_for_amount(error_key)
            if error_key in error_dict:
                result.add_error(
                    message=error_dict[error_key].format(row=row, sheet=sheet),
                    sheet=sheet, row=row, field_name=field_name, category="amount",
                )
        return ""

    # Regex check (use FOB regex for 4 decimal places)
    regex = FOB_AMOUNT_REGEX if decimal_places == 4 else AMOUNT_REGEX
    if not regex.match(amount_str):
        error_dict = _get_error_dict_for_amount(error_key)
        invalid_key = error_key.replace("_empty", "_invalid") if "_empty" in error_key else error_key
        if invalid_key in error_dict:
            result.add_error(
                message=error_dict[invalid_key].format(row=row, sheet=sheet, value=amount_str),
                sheet=sheet, row=row, field_name=field_name, category="amount",
            )
        return ""

    # Non-negative check
    if not is_non_negative(amount_str):
        error_dict = _get_error_dict_for_amount(error_key)
        invalid_key = error_key.replace("_empty", "_invalid") if "_empty" in error_key else error_key
        if invalid_key in error_dict:
            result.add_error(
                message=error_dict[invalid_key].format(row=row, sheet=sheet, value=amount_str),
                sheet=sheet, row=row, field_name=field_name, category="amount",
            )
        return ""

    return amount_str


def validate_port_code(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
    is_mandatory: bool = True,
) -> str:
    """
    WHAT: Validates port code — exactly 6 alphanumeric characters.
    RETURNS: Cleaned port code (or empty).
    """
    cleaned = clean_string(value)
    if not cleaned:
        if is_mandatory:
            result.add_error(
                message=SHIPPING_ERRORS["port_code_empty"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Port Code", category="shipping",
            )
        return ""

    if not PORT_CODE_REGEX.match(cleaned):
        result.add_error(
            message=SHIPPING_ERRORS["port_code_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name="Port Code", category="shipping",
        )
        return ""

    return cleaned


def validate_shipping_bill(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
    is_mandatory: bool = True,
) -> str:
    """
    WHAT: Validates shipping bill number — 3-7 digits only.
    RETURNS: Cleaned SB number (or empty).
    """
    cleaned = str(value).strip() if value is not None else ""
    # Handle float values from Excel (e.g., 1234567.0)
    if cleaned and "." in cleaned:
        try:
            cleaned = str(int(float(cleaned)))
        except (ValueError, OverflowError):
            pass

    if not cleaned:
        if is_mandatory:
            result.add_error(
                message=SHIPPING_ERRORS["shipping_bill_empty"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="SB No", category="shipping",
            )
        return ""

    if not SHIPPING_BILL_REGEX.match(cleaned):
        result.add_error(
            message=SHIPPING_ERRORS["shipping_bill_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name="SB No", category="shipping",
        )
        return ""

    return cleaned


def validate_endorsed_invoice(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> str:
    """
    WHAT: Validates SB/Endorsed Invoice number (S04, S05 — alphanumeric with / and -).
    RETURNS: Cleaned value (or empty if blank — this field is always optional).
    """
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        return ""

    if not ENDORSED_INVOICE_REGEX.match(cleaned):
        result.add_error(
            message=SHIPPING_ERRORS["sb_endorsed_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name="SB / Endorsed Invoice No", category="shipping",
        )
        return ""

    return cleaned


def validate_egm_ref(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
    is_mandatory: bool = True,
) -> str:
    """
    WHAT: Validates EGM reference number — 1-20 alphanumeric, no backslash/quotes.
    RETURNS: Cleaned EGM reference (or empty).
    """
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        if is_mandatory:
            result.add_error(
                message=SHIPPING_ERRORS["egm_ref_empty"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="EGM Ref No", category="shipping",
            )
        return ""

    if not EGM_REF_REGEX.match(cleaned):
        result.add_error(
            message=SHIPPING_ERRORS["egm_ref_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name="EGM Ref No", category="shipping",
        )
        return ""

    return cleaned


def validate_brc_fields(
    brc_no: object,
    brc_date: object,
    brc_value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
    is_mandatory: bool = False,
) -> tuple[str, str, str]:
    """
    WHAT:
        Validates BRC/FIRC fields with all-or-nothing rule: if any of
        Number, Date, Value is provided, all three must be present.

    RETURNS:
        tuple[str, str, str]: (brc_no, brc_date, brc_value) — cleaned values.
    """
    no_str = str(brc_no).strip() if brc_no is not None else ""
    date_str = parse_date(brc_date)
    value_str = parse_amount(brc_value)

    has_any = bool(no_str or date_str or value_str)
    has_all = bool(no_str and date_str and value_str)

    if not has_any:
        return ("", "", "")

    # All-or-nothing check
    if has_any and not has_all:
        result.add_error(
            message=BRC_ERRORS["brc_incomplete"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="BRC", category="brc",
        )
        return (no_str, date_str, value_str)

    # Validate BRC Number
    if no_str == "0":
        result.add_error(
            message=BRC_ERRORS["brc_no_zero"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="BRC No", category="brc",
        )
    elif not BRC_NO_REGEX.match(no_str):
        result.add_error(
            message=BRC_ERRORS["brc_no_invalid"].format(row=row, sheet=sheet, value=no_str),
            sheet=sheet, row=row, field_name="BRC No", category="brc",
        )

    # Validate BRC Date (can pre-date GST inception)
    if date_str and DATE_REGEX.match(date_str):
        date_obj = parse_date_to_object(date_str)
        if date_obj and date_obj > date.today():
            result.add_error(
                message=BRC_ERRORS["brc_date_future"].format(row=row, sheet=sheet, value=date_str),
                sheet=sheet, row=row, field_name="BRC Date", category="brc",
            )
    elif date_str:
        result.add_error(
            message=BRC_ERRORS["brc_date_invalid"].format(row=row, sheet=sheet, value=date_str),
            sheet=sheet, row=row, field_name="BRC Date", category="brc",
        )

    # Validate BRC Value
    if value_str and not is_non_negative(value_str):
        result.add_error(
            message=BRC_ERRORS["brc_value_invalid"].format(row=row, sheet=sheet, value=value_str),
            sheet=sheet, row=row, field_name="BRC Value", category="brc",
        )

    return (no_str, date_str, value_str)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _get_error_dict(prefix: str) -> dict[str, str]:
    """Returns the appropriate error dict based on field prefix."""
    if prefix in ("shipping_bill", "egm", "sb"):
        return SHIPPING_ERRORS
    return DOCUMENT_ERRORS


def _get_error_dict_for_amount(error_key: str) -> dict[str, str]:
    """Returns the appropriate error dict for an amount field error key."""
    from config.error_messages import TAX_ERRORS
    if error_key.startswith("fob_") or error_key.startswith("port_"):
        return SHIPPING_ERRORS
    if error_key.startswith("taxable_") or error_key.startswith("igst_") or error_key.startswith("cess_"):
        return TAX_ERRORS
    if error_key.startswith("brc_"):
        return BRC_ERRORS
    return DOCUMENT_ERRORS
