"""
FILE: core/validators/stmt06_validator.py

PURPOSE: Statement-specific validator for S06 — Intra/Inter-State Correction
         (INTRVC). Two sheets: "Inter to Intra" and "Intra to Inter". Each row
         has Earlier tax + Correct tax + two POS fields. B2B/B2C derived from
         Recipient GSTIN presence.

CONTAINS:
- validate_stmt06()         — Top-level entry point
- _validate_row()           — Validates one row (shared for both sheets)
- _validate_recipient()     — B2B/B2C derivation and identity validation
- _validate_pos()           — Place of Supply validation against 38-code master
- _get_earlier_tax_headers() — Returns the "earlier" tax column headers for this sheet
- _get_correct_tax_headers() — Returns the "correct" tax column headers for this sheet

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount
- core/header_validator.py      → validate_header()
- core/duplicate_detector.py    → DuplicateDetector
- config/constants.py           → PLACE_OF_SUPPLY_DISPLAY_VALUES
- config/error_messages.py      → S06_ERRORS
- config/regex_patterns.py      → GSTIN_REGEX
- models/ (StatementConfig, HeaderData, DataRow, ValidationResult)
- utils/string_helpers.py       → is_blank, clean_string
- utils/number_helpers.py       → to_json_number

USED BY:
- gui/main_window.py → called via _get_validator("S06")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S06 statement validator   | Phase 6: Intra/Inter correction    |
"""

from models.statement_config import StatementConfig, SheetConfig
from models.header import HeaderData
from models.data_row import DataRow
from models.validation_result import ValidationResult
from core.header_validator import validate_header
from core.field_validators import (
    validate_doc_type,
    validate_doc_no,
    validate_date,
    validate_amount,
)
from core.duplicate_detector import DuplicateDetector
from config.constants import PLACE_OF_SUPPLY_DISPLAY_VALUES
from config.error_messages import S06_ERRORS
from config.regex_patterns import GSTIN_REGEX
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number


def validate_stmt06(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S06 validation entry point. Validates header (GSTIN +
        orderNo + orderDt), then validates each row in both sheets.
        Both sheets share the same validation logic — only the tax column
        headers differ (IGST Paid vs CGST/SGST Paid, Correct CGST/SGST vs
        Correct IGST).

    CALLED BY:
        → gui/main_window.py → _get_validator("S06") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed. ***
        *** ASSUMPTION: B2B/B2C is derived from Recipient GSTIN presence.
            GSTIN filled → B2B. GSTIN blank → B2C (Recipient Name required). ***
        *** ASSUMPTION: bCess and aCess OMITTED from JSON when blank (not
            defaulted to 0). Blueprint section 9 note 3. ***
    """
    # --- Step 1: Validate header (ORDER mode) ---
    validate_header(header, config.header_mode, result)

    # Build POS lookup set for fast validation
    pos_set = set(v.upper() for v in PLACE_OF_SUPPLY_DISPLAY_VALUES)

    # --- Step 2: Validate each sheet ---
    for sheet_config in config.sheets:
        sheet_name = sheet_config.name
        rows = sheets.get(sheet_name, [])

        if not rows:
            continue

        dup_detector = DuplicateDetector()

        for data_row in rows:
            _validate_row(data_row, sheet_name, sheet_config, result,
                          dup_detector, pos_set)


def _validate_row(
    data_row: DataRow,
    sheet: str,
    sheet_config: SheetConfig,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
    pos_set: set[str],
) -> None:
    """
    WHAT:
        Validates one row from either sheet. Checks:
        1. Recipient identity (B2B: GSTIN, B2C: Name)
        2. Doc Type, Doc No, Doc Date, Doc Value, Taxable Value
        3. Earlier tax fields (sheet-specific column headers)
        4. Earlier Cess (optional), Earlier POS (mandatory)
        5. Correct tax fields (sheet-specific column headers)
        6. Correct Cess (optional), Correct POS (mandatory)
        7. Duplicate detection

    CALLED BY: validate_stmt06()
    """
    row = data_row.excel_row

    # Row presence: check Doc Type
    if is_blank(data_row.get_value("Doc Type")):
        return  # Empty row

    # --- Recipient identity (B2B/B2C) ---
    _validate_recipient(data_row, row, sheet, result)

    # --- Standard document fields ---
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
    validate_amount(
        data_row.get_value("Taxable Value"), row, sheet, "Taxable Value", result,
        error_key="taxable_value_empty",
    )

    # --- Earlier tax fields (column headers differ by sheet) ---
    earlier_headers = _get_earlier_tax_headers(sheet_config)
    for hdr in earlier_headers:
        validate_amount(
            data_row.get_value(hdr), row, sheet, hdr, result,
            error_key="igst_empty",  # Reuse generic tax-empty message
        )

    # Earlier Cess (optional)
    validate_amount(
        data_row.get_value("Earlier Cess"), row, sheet, "Earlier Cess", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )

    # Earlier POS (mandatory)
    _validate_pos(
        data_row.get_value("Earlier POS"), row, sheet, "Earlier POS",
        result, pos_set,
    )

    # --- Correct tax fields ---
    correct_headers = _get_correct_tax_headers(sheet_config)
    for hdr in correct_headers:
        validate_amount(
            data_row.get_value(hdr), row, sheet, hdr, result,
            error_key="igst_empty",
        )

    # Correct Cess (optional)
    validate_amount(
        data_row.get_value("Correct Cess"), row, sheet, "Correct Cess", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )

    # Correct POS (mandatory)
    _validate_pos(
        data_row.get_value("Correct POS"), row, sheet, "Correct POS",
        result, pos_set,
    )

    # --- Duplicate detection ---
    if doc_type and doc_no and doc_date:
        dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)


def _validate_recipient(
    data_row: DataRow,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Validates recipient identity:
        - If Recipient GSTIN is filled → B2B (validate GSTIN format)
        - If GSTIN blank → B2C (Recipient Name must be present)
        - At least one of GSTIN or Name must exist

    WHY ADDED:
        Blueprint section 9 note 2: "B2B/B2C is derived, not entered.
        For B2C, Name must be present."

    CALLED BY: _validate_row()
    """
    gstin_raw = data_row.get_value("Recipient GSTIN")
    name_raw = data_row.get_value("Recipient Name")

    has_gstin = not is_blank(gstin_raw)
    has_name = not is_blank(name_raw)

    if not has_gstin and not has_name:
        result.add_error(
            message=S06_ERRORS["no_recipient_identity"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Recipient", category="document",
        )
        return

    if has_gstin:
        # B2B: validate GSTIN format
        cleaned = clean_string(gstin_raw)
        if not GSTIN_REGEX.match(cleaned):
            result.add_error(
                message=(
                    f"Row {row}, {sheet} Sheet: Recipient GSTIN '{cleaned}' does not "
                    f"match the expected 15-character format."
                ),
                sheet=sheet, row=row, field_name="Recipient GSTIN", category="document",
            )
    else:
        # B2C: Name is required (already confirmed has_name is True above)
        pass


def _validate_pos(
    value: object,
    row: int,
    sheet: str,
    field_name: str,
    result: ValidationResult,
    pos_set: set[str],
) -> None:
    """
    WHAT:
        Validates Place of Supply against the 38-code master list.
        Format: "XX-State Name" (e.g., "19-West Bengal").

    CALLED BY: _validate_row() — for both Earlier POS and Correct POS
    """
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        result.add_error(
            message=S06_ERRORS["pos_empty"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name=field_name, category="pos",
        )
        return

    if cleaned.upper() not in pos_set:
        result.add_error(
            message=S06_ERRORS["pos_invalid"].format(row=row, sheet=sheet, value=cleaned),
            sheet=sheet, row=row, field_name=field_name, category="pos",
        )


def _get_earlier_tax_headers(sheet_config: SheetConfig) -> list[str]:
    """
    WHAT:
        Returns the mandatory "earlier" tax column headers for the given sheet.
        Inter to Intra: ["IGST Paid"]
        Intra to Inter: ["CGST Paid", "SGST Paid"]
    CALLED BY: _validate_row()
    """
    direction = sheet_config.json_direction.get("bInt", "")
    if direction == "Inter":
        return ["IGST Paid"]
    else:
        return ["CGST Paid", "SGST Paid"]


def _get_correct_tax_headers(sheet_config: SheetConfig) -> list[str]:
    """
    WHAT:
        Returns the mandatory "correct" tax column headers for the given sheet.
        Inter to Intra: ["Correct CGST", "Correct SGST"]
        Intra to Inter: ["Correct IGST"]
    CALLED BY: _validate_row()
    """
    direction = sheet_config.json_direction.get("aInt", "")
    if direction == "Intra":
        return ["Correct CGST", "Correct SGST"]
    else:
        return ["Correct IGST"]
