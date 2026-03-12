"""
FILE: core/validators/stmt05_validator.py

PURPOSE: Statement-specific validator for S05 — SEZ Supplies without Payment
         of Tax (SEZWOP). Validates both Goods and Services sheets which have
         identical 6-column structures. The lightest validator — no BRC, no tax
         columns, no port code, no EGM, no FOB.

CONTAINS:
- validate_stmt05()        — Top-level entry point
- _validate_data_row()     — Validates one row (shared logic for both sheets)
- _validate_sb_pair()      — SB/Endorsed Invoice conditional pairing

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount, validate_endorsed_invoice
- core/header_validator.py      → validate_header()
- core/duplicate_detector.py    → DuplicateDetector
- models/statement_config.py    → StatementConfig
- models/header.py              → HeaderData
- models/data_row.py            → DataRow
- models/validation_result.py   → ValidationResult
- utils/string_helpers.py       → is_blank

USED BY:
- gui/main_window.py → called via _get_validator("S05")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S05 statement validator   | Phase 2: SEZ without payment       |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from models.validation_result import ValidationResult
from core.header_validator import validate_header
from core.field_validators import (
    validate_doc_type,
    validate_doc_no,
    validate_date,
    validate_amount,
    validate_endorsed_invoice,
)
from core.duplicate_detector import DuplicateDetector
from config.error_messages import SHIPPING_ERRORS
from utils.string_helpers import is_blank


def validate_stmt05(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S05 validation entry point. Validates the header,
        then iterates over each row in the Goods and Services sheets.
        Both sheets have identical column structure (6 columns), so the
        same _validate_data_row() function is used for both.

    WHY ADDED:
        S05 (SEZWOP) is the second statement being built, and the lightest
        of all 6 — only Doc Type, Doc No, Doc Date, Doc Value, and an
        optional SB/Endorsed Invoice pair.

    CALLED BY:
        → gui/main_window.py → _get_validator("S05") returns this function

    PARAMETERS:
        header (HeaderData): Validated header from the template.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S05 configuration from mappings.py.
        result (ValidationResult): Errors and warnings are added here.

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed (correct
            sheets exist with correct columns). This validator does not
            re-check sheet/column structure. ***
        *** ASSUMPTION: Goods and Services sheets use identical validation
            logic. The only difference is the JSON "type" flag ("G"/"S"),
            which is handled by the generator, not the validator. ***
    """
    # --- Step 1: Validate header ---
    validate_header(header, config.header_mode, result)

    # --- Step 2: Validate each data sheet ---
    for sheet_config in config.sheets:
        sheet_name = sheet_config.name
        rows = sheets.get(sheet_name, [])

        if not rows:
            # Template reader already warns about empty sheets
            continue

        # Create a duplicate detector per sheet (independent per sheet)
        dup_detector = DuplicateDetector()

        for data_row in rows:
            _validate_data_row(data_row, sheet_name, result, dup_detector)


def _validate_data_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
) -> None:
    """
    WHAT:
        Validates one row from either Goods or Services sheet. Checks:
        1. Doc Type, Doc No, Doc Date, Doc Value (mandatory fields)
        2. SB/Endorsed Invoice No + Date (conditional pair)
        3. Duplicate detection

    WHY ADDED:
        Both S05 sheets have identical 6-column structure, so one
        function handles both. This avoids code duplication.

    CALLED BY: validate_stmt05() → per row

    EDGE CASES HANDLED:
        - Empty rows → skipped silently (no doc type and no SB No)
        - SB No without SB Date → error (date is required when no is given)
        - SB Date without SB No → allowed (blueprint says date is conditional
          on no, but not vice versa; however we skip orphan dates per govt VBA)
    """
    row = data_row.excel_row

    has_doc = not is_blank(data_row.get_value("Doc Type"))

    if not has_doc:
        return  # Empty row (should have been filtered by template reader)

    # --- Document fields (all mandatory) ---
    doc_type = validate_doc_type(
        data_row.get_value("Doc Type"), row, sheet, result,
    )
    doc_no = validate_doc_no(
        data_row.get_value("Doc No"), row, sheet, result,
    )
    doc_date = validate_date(
        data_row.get_value("Doc Date"), row, sheet, "Doc Date", result,
        error_key_prefix="doc",
    )
    validate_amount(
        data_row.get_value("Doc Value"), row, sheet, "Doc Value", result,
        error_key="doc_value_empty",
    )

    # --- SB / Endorsed Invoice pair (optional, but date required if no given) ---
    _validate_sb_pair(data_row, row, sheet, result)

    # --- Duplicate detection ---
    if doc_type and doc_no and doc_date:
        dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)


def _validate_sb_pair(
    data_row: DataRow,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Validates the SB/Endorsed Invoice conditional pair:
        - If SB No is provided → SB Date is required
        - If SB No is blank → both fields are omitted from JSON
        SB No is validated with the endorsed invoice regex (alphanumeric + / and -).
        SB Date cannot be in the future. No GST inception lower bound per govt VBA
        (the check is commented out in the government code).

    WHY ADDED:
        S05 blueprint note 6: "SB Date is required only when SB No is provided.
        Cannot be future. No lower bound."

    CALLED BY: _validate_data_row()

    ASSUMPTIONS:
        *** ASSUMPTION: SB Date has no lower bound (can pre-date 01-07-2017).
            This matches government VBA where the SB Date inception check is
            commented out. Decided based on S05 Blueprint note 6. ***
    """
    sb_no_raw = data_row.get_value("SB / Endorsed Invoice No")
    sb_date_raw = data_row.get_value("SB / Endorsed Invoice Date")

    has_no = not is_blank(sb_no_raw)
    has_date = not is_blank(sb_date_raw)

    if not has_no and not has_date:
        return  # Both blank — fine, both omitted from JSON

    if has_no:
        # Validate SB No format (alphanumeric + / and -)
        validate_endorsed_invoice(sb_no_raw, row, sheet, result)

        # SB Date is required when SB No is provided
        if not has_date:
            result.add_error(
                message=SHIPPING_ERRORS["sb_date_required"].format(row=row, sheet=sheet),
                sheet=sheet, row=row,
                field_name="SB / Endorsed Invoice Date",
                category="shipping",
            )
        else:
            # Validate SB Date: no GST inception check, but check future
            validate_date(
                sb_date_raw, row, sheet, "SB / Endorsed Invoice Date", result,
                error_key_prefix="shipping_bill",
                check_gst_inception=False,
                check_future=True,
            )

    # ASSUMPTION: If date is provided but no is blank, we silently ignore.
    # The government VBA only enforces "date required if no is given",
    # not the reverse. An orphan date is unusual but not an error.
