"""
FILE: core/date_validators.py

PURPOSE: Validates chronological ordering of dates within a single row.
         For example: Shipping Bill date should not precede Invoice date,
         and EGM date should not precede Shipping Bill date.

CONTAINS:
- validate_date_ordering()  — Checks that date_a <= date_b

DEPENDS ON:
- config/error_messages.py     → DATE_ORDER_ERRORS
- models/validation_result.py  → ValidationResult
- utils/date_helpers.py        → is_date_before()

USED BY:
- core/validators/stmt03_validator.py → SB >= Invoice, EGM >= SB

CHANGE LOG:
| Date       | Change                              | Why                                     |
|------------|-------------------------------------|-----------------------------------------|
| 11-03-2026 | Created — chronological date checks | Rebuild Brief Section 5: new validation |
"""

from config.error_messages import DATE_ORDER_ERRORS
from models.validation_result import ValidationResult
from utils.date_helpers import is_date_before


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
