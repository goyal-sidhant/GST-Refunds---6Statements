"""
FILE: core/date_validators.py

PURPOSE: Validates chronological ordering of dates within a single row,
         and cross-checks dates against the refund period boundaries.
         For example: Shipping Bill date should not precede Invoice date,
         EGM date should not precede Shipping Bill date, and BRC/FIRC
         date must fall within the From Period → To Period range.

CONTAINS:
- validate_sb_after_invoice()     — Checks SB Date >= Invoice Date
- validate_egm_after_sb()         — Checks EGM Date >= SB Date
- validate_brc_within_period()    — Checks BRC Date within From–To Period

DEPENDS ON:
- config/error_messages.py     → DATE_ORDER_ERRORS
- models/validation_result.py  → ValidationResult
- utils/date_helpers.py        → is_date_before()

USED BY:
- core/validators/stmt03_validator.py → SB >= Invoice, EGM >= SB, BRC within period

CHANGE LOG:
| Date       | Change                              | Why                                     |
|------------|-------------------------------------|-----------------------------------------|
| 11-03-2026 | Created — chronological date checks | Rebuild Brief Section 5: new validation |
| 12-03-2026 | Added BRC within period check       | BRC date must fall within refund period  |
"""

from config.error_messages import DATE_ORDER_ERRORS
from models.validation_result import ValidationResult
from utils.date_helpers import is_date_before, parse_date_to_object, period_to_date_range


def validate_sb_after_invoice(
    invoice_date: str,
    sb_date: str,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Checks that Shipping Bill Date is on or after Invoice Date.
        A shipping bill is issued when goods are exported, which must
        be after (or on the same day as) the invoice.

    WHY ADDED:
        Rebuild Brief Section 5: "Chronological Date Checks — a Shipping
        Bill date cannot logically precede an Invoice Date."

    CALLED BY:
        → core/validators/stmt03_validator.py → Goods sheet validation

    PARAMETERS:
        invoice_date (str): Document date in DD-MM-YYYY format.
        sb_date (str): Shipping bill date in DD-MM-YYYY format.
        row (int): Excel row number.
        sheet (str): Sheet name.
        result (ValidationResult): Errors added here.
    """
    if not invoice_date or not sb_date:
        return

    is_before = is_date_before(sb_date, invoice_date)
    if is_before is True:
        result.add_error(
            message=DATE_ORDER_ERRORS["sb_before_invoice"].format(
                row=row, sheet=sheet, sb_date=sb_date, inv_date=invoice_date,
            ),
            sheet=sheet,
            row=row,
            field_name="SB Date",
            category="date_order",
        )


def validate_egm_after_sb(
    sb_date: str,
    egm_date: str,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Checks that EGM Date is on or after Shipping Bill Date.
        The Export General Manifest is filed after the shipping bill.

    WHY ADDED:
        Rebuild Brief Section 5: "An EGM date cannot logically precede
        a Shipping Bill date."

    CALLED BY:
        → core/validators/stmt03_validator.py → Goods sheet validation

    PARAMETERS:
        sb_date (str): Shipping bill date in DD-MM-YYYY format.
        egm_date (str): EGM date in DD-MM-YYYY format.
        row (int): Excel row number.
        sheet (str): Sheet name.
        result (ValidationResult): Errors added here.
    """
    if not sb_date or not egm_date:
        return

    is_before = is_date_before(egm_date, sb_date)
    if is_before is True:
        result.add_error(
            message=DATE_ORDER_ERRORS["egm_before_sb"].format(
                row=row, sheet=sheet, egm_date=egm_date, sb_date=sb_date,
            ),
            sheet=sheet,
            row=row,
            field_name="EGM Date",
            category="date_order",
        )


def validate_brc_within_period(
    brc_date: str,
    from_period: str,
    to_period: str,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Checks that a BRC/FIRC date falls within the refund period
        (From Period start → To Period end). Refund eligibility for
        service exports is based on when the foreign exchange was
        realized (BRC/FIRC date), not when the invoice was raised.

    WHY ADDED:
        User found that a BRC date of 31-12-2025 was accepted when the
        refund To Period was 03-2025 — the tool should have flagged this.
        LEGAL: Refund of IGST on export of services is available in the
        period in which the foreign exchange is realized.

    CALLED BY:
        → core/validators/stmt03_validator.py → after BRC field validation

    EDGE CASES HANDLED:
        - Empty brc_date → silently returns (BRC not provided)
        - Empty from_period or to_period → silently returns (header invalid,
          already caught by header_validator)
        - Unparseable dates → silently returns (format errors already caught)

    PARAMETERS:
        brc_date (str): BRC/FIRC date in DD-MM-YYYY format.
        from_period (str): Refund From Period in MM-YYYY format.
        to_period (str): Refund To Period in MM-YYYY format.
        row (int): Excel row number.
        sheet (str): Sheet name.
        result (ValidationResult): Errors added here.
    """
    if not brc_date or not from_period or not to_period:
        return

    brc_date_obj = parse_date_to_object(brc_date)
    if brc_date_obj is None:
        return

    # From Period → first day of that month
    from_range = period_to_date_range(from_period)
    if from_range is not None:
        from_start = from_range[0]
        if brc_date_obj < from_start:
            result.add_error(
                message=DATE_ORDER_ERRORS["brc_before_from_period"].format(
                    row=row, sheet=sheet, brc_date=brc_date, from_period=from_period,
                ),
                sheet=sheet,
                row=row,
                field_name="BRC Date",
                category="date_order",
            )

    # To Period → last day of that month
    to_range = period_to_date_range(to_period)
    if to_range is not None:
        to_end = to_range[1]
        if brc_date_obj > to_end:
            result.add_error(
                message=DATE_ORDER_ERRORS["brc_after_to_period"].format(
                    row=row, sheet=sheet, brc_date=brc_date, to_period=to_period,
                ),
                sheet=sheet,
                row=row,
                field_name="BRC Date",
                category="date_order",
            )
