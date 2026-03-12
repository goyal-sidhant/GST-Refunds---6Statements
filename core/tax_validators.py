"""
FILE: core/tax_validators.py

PURPOSE: Tax-amount validation: mutual exclusivity (IGST XOR CGST+SGST),
         implicit rate checking (WARNING only), tax sum vs taxable value,
         and IGST <= Taxable Value constraint.

CONTAINS:
- validate_tax_mutual_exclusivity() — IGST XOR (CGST+SGST) rule
- check_implicit_rate()             — WARNING if rate doesn't match GST slab
- validate_igst_vs_taxable()        — IGST <= Taxable Value
- validate_doc_value_vs_sum()       — Doc Value >= Taxable + IGST + Cess

DEPENDS ON:
- config/constants.py          → GST_RATE_SLABS, RATE_TOLERANCE_PERCENT
- config/error_messages.py     → TAX_ERRORS, WARNINGS
- models/validation_result.py  → ValidationResult
- utils/number_helpers.py      → to_json_number()

USED BY:
- core/validators/stmt01a_validator.py → tax mutual exclusivity per type
- core/validators/stmt02_validator.py  → IGST vs taxable, implicit rate
- core/validators/stmt04_validator.py  → IGST vs taxable, implicit rate

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — tax validation functions  | Phase 0 infrastructure setup       |
"""

from config.constants import GST_RATE_SLABS, RATE_TOLERANCE_PERCENT
from config.error_messages import TAX_ERRORS, WARNINGS
from models.validation_result import ValidationResult
from utils.number_helpers import to_json_number


def validate_tax_mutual_exclusivity(
    igst: float,
    cgst: float,
    sgst: float,
    row: int,
    sheet: str,
    result: ValidationResult,
    allow_all_three: bool = False,
) -> None:
    """
    WHAT:
        Checks the IGST XOR (CGST+SGST) rule. For most supply types,
        a row must have EITHER IGST alone OR both CGST and SGST together.
        ISD (S01A) is the only exception — allows all three simultaneously.

    CALLED BY:
        → core/validators/stmt01a_validator.py → per-type dispatch

    PARAMETERS:
        igst (float): IGST amount (0 means not entered).
        cgst (float): CGST amount.
        sgst (float): SGST amount.
        row (int): Excel row number.
        sheet (str): Sheet name.
        result (ValidationResult): Errors added here.
        allow_all_three (bool): If True, skip mutual exclusivity (ISD only).
    """
    has_igst = igst > 0
    has_cgst = cgst > 0
    has_sgst = sgst > 0

    if allow_all_three:
        # ISD allows all three — just check at least one is present
        if not has_igst and not has_cgst and not has_sgst:
            result.add_error(
                message=TAX_ERRORS["no_tax_entered"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
        return

    # Standard rule: IGST XOR (CGST+SGST)
    if has_igst and (has_cgst or has_sgst):
        result.add_error(
            message=TAX_ERRORS["tax_mutual_exclusivity"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Tax", category="tax",
        )
        return

    if has_cgst and not has_sgst:
        result.add_error(
            message=TAX_ERRORS["cgst_sgst_must_pair"].format(
                row=row, sheet=sheet, present="CGST", missing="SGST",
            ),
            sheet=sheet, row=row, field_name="Tax", category="tax",
        )
        return

    if has_sgst and not has_cgst:
        result.add_error(
            message=TAX_ERRORS["cgst_sgst_must_pair"].format(
                row=row, sheet=sheet, present="SGST", missing="CGST",
            ),
            sheet=sheet, row=row, field_name="Tax", category="tax",
        )
        return

    if not has_igst and not has_cgst and not has_sgst:
        result.add_error(
            message=TAX_ERRORS["no_tax_entered"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Tax", category="tax",
        )


def check_implicit_rate(
    tax_amount: float,
    taxable_value: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Calculates (tax / taxable_value * 100) and compares against
        standard GST slabs. If no slab matches within tolerance, adds
        a WARNING (not an error — does NOT block JSON generation).

    WHY ADDED:
        Rebuild Brief Section 4: "Dynamically calculate the implied tax
        rate and flag it if it doesn't align with standard GST slabs."
        Decision: Session 1 — this is a WARNING, not a hard error.

    CALLED BY:
        → core/validators/stmt02_validator.py → for IGST on services
        → core/validators/stmt04_validator.py → for IGST on SEZ supplies

    PARAMETERS:
        tax_amount (float): The tax amount (IGST or total tax).
        taxable_value (float): The taxable value.
        row (int): Excel row number.
        sheet (str): Sheet name.
        result (ValidationResult): Warnings added here.
    """
    if taxable_value <= 0 or tax_amount <= 0:
        return  # Cannot calculate rate if either is zero/negative

    implied_rate = (tax_amount / taxable_value) * 100

    # Find the nearest standard slab
    nearest_slab = min(GST_RATE_SLABS, key=lambda slab: abs(slab - implied_rate))
    difference = abs(implied_rate - nearest_slab)

    if difference > RATE_TOLERANCE_PERCENT:
        result.add_warning(
            message=WARNINGS["implicit_rate_mismatch"].format(
                row=row,
                sheet=sheet,
                implied_rate=implied_rate,
                tax_amount=tax_amount,
                taxable_value=taxable_value,
                nearest_slab=nearest_slab,
            ),
            sheet=sheet,
            row=row,
            field_name="Tax Rate",
            category="tax",
        )


def validate_igst_vs_taxable(
    igst: float,
    taxable_value: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT: Checks that IGST amount does not exceed Taxable Value.
    CALLED BY: S02/S04 validators.
    """
    if igst > taxable_value:
        result.add_error(
            message=TAX_ERRORS["igst_exceeds_taxable"].format(
                row=row, sheet=sheet, igst=igst, taxable=taxable_value,
            ),
            sheet=sheet, row=row, field_name="IGST", category="tax",
        )


def validate_doc_value_vs_sum(
    doc_value: float,
    taxable_value: float,
    igst: float,
    cess: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT: Checks that Doc Value >= Taxable Value + IGST + Cess.
    CALLED BY: S02/S04 validators where Doc Value is separate from Taxable.
    """
    total = taxable_value + igst + cess
    if doc_value < total:
        result.add_error(
            message=TAX_ERRORS["doc_value_less_than_sum"].format(
                row=row, sheet=sheet, doc_value=doc_value, total=total,
            ),
            sheet=sheet, row=row, field_name="Doc Value", category="tax",
        )


def validate_tax_sum_vs_taxable(
    igst: float,
    cgst: float,
    sgst: float,
    taxable_value: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT: Checks that total tax (IGST + CGST + SGST) does not exceed taxable value.
    CALLED BY: S01A validator.
    """
    tax_sum = igst + cgst + sgst
    if tax_sum > taxable_value:
        result.add_error(
            message=TAX_ERRORS["tax_sum_exceeds_taxable"].format(
                row=row, sheet=sheet, tax_sum=tax_sum, taxable=taxable_value,
            ),
            sheet=sheet, row=row, field_name="Tax", category="tax",
        )
