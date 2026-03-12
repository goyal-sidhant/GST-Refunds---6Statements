"""
FILE: core/validators/stmt04_validator.py

PURPOSE: Statement-specific validator for S04 — SEZ Supplies with Payment of Tax
         (SEZWP). Single "Data" sheet with Recipient GSTIN, tax fields (Taxable
         Value, IGST, Cess), and optional SB/Endorsed Invoice pair. No BRC linking.

CONTAINS:
- validate_stmt04()        — Top-level entry point
- _validate_data_row()     — Validates one row
- _validate_sb_pair()      — SB/Endorsed Invoice conditional pairing
- _validate_recipient_gstin() — Recipient GSTIN format + not-same-as-self check

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount, validate_endorsed_invoice
- core/header_validator.py      → validate_header()
- core/duplicate_detector.py    → DuplicateDetector
- core/tax_validators.py        → validate_igst_vs_taxable, validate_doc_value_vs_sum,
                                   check_implicit_rate
- core/gstin_validator.py       → validate_gstin (for recipient GSTIN)
- config/error_messages.py      → RECIPIENT_ERRORS, SHIPPING_ERRORS
- models/statement_config.py    → StatementConfig
- models/header.py              → HeaderData
- models/data_row.py            → DataRow
- models/validation_result.py   → ValidationResult
- utils/string_helpers.py       → is_blank, clean_string

USED BY:
- gui/main_window.py → called via _get_validator("S04")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S04 statement validator   | Phase 4: SEZ with payment          |
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
from core.tax_validators import (
    validate_igst_vs_taxable,
    validate_doc_value_vs_sum,
    check_implicit_rate,
)
from core.gstin_validator import validate_gstin
from config.error_messages import RECIPIENT_ERRORS, SHIPPING_ERRORS
from config.regex_patterns import GSTIN_REGEX
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number


def validate_stmt04(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S04 validation entry point. Validates the header (GSTIN only,
        no periods for v3.0), then iterates over each row in the single Data
        sheet, checking Recipient GSTIN, document fields, tax amounts, and the
        optional SB/Endorsed Invoice pair.

    WHY ADDED:
        S04 (SEZWP) is the fourth statement being built. Structurally similar
        to S02 but with Recipient GSTIN instead of BRC and SB/Endorsed Invoice
        instead of BRC linking.

    CALLED BY:
        → gui/main_window.py → _get_validator("S04") returns this function

    PARAMETERS:
        header (HeaderData): Validated header from the template.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S04 configuration from mappings.py.
        result (ValidationResult): Errors and warnings are added here.

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed. ***
        *** ASSUMPTION: Cess is OMITTED from JSON when blank (unlike S02
            which defaults to 0). Blueprint section 7 note 3. ***
    """
    # --- Step 1: Validate header (GSTIN only, no periods) ---
    validate_header(header, config.header_mode, result)

    # --- Step 2: Validate the single Data sheet ---
    sheet_config = config.sheets[0]  # S04 has exactly one sheet
    sheet_name = sheet_config.name
    rows = sheets.get(sheet_name, [])

    if not rows:
        return  # Template reader already warns about empty sheets

    # Store applicant GSTIN for recipient != self check
    applicant_gstin = header.gstin.upper() if header.gstin else ""

    dup_detector = DuplicateDetector()

    for data_row in rows:
        _validate_data_row(
            data_row, sheet_name, result, dup_detector, applicant_gstin,
        )


def _validate_data_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
    applicant_gstin: str,
) -> None:
    """
    WHAT:
        Validates one row from the Data sheet. Checks:
        1. Recipient GSTIN (valid format, != self)
        2. Doc Type, Doc No, Doc Date, Doc Value (standard fields)
        3. SB/Endorsed Invoice pair (conditional)
        4. Taxable Value, IGST (mandatory), Cess (optional)
        5. IGST <= Taxable Value
        6. Doc Value >= Taxable + IGST + Cess
        7. Implicit rate check (WARNING only)
        8. Duplicate detection

    CALLED BY: validate_stmt04()

    EDGE CASES HANDLED:
        - Empty row (no Recipient GSTIN) → skipped
        - Cess blank → not an error (optional, omitted from JSON)
        - SB No without SB Date → error
    """
    row = data_row.excel_row

    # S04 uses Recipient GSTIN as the presence indicator (not Doc Type)
    # Government VBA: autoGenSerial numbers rows where Recipient GSTIN is not blank
    has_data = not is_blank(data_row.get_value("Recipient GSTIN"))

    if not has_data:
        return  # Empty row

    # --- Recipient GSTIN ---
    _validate_recipient_gstin(
        data_row.get_value("Recipient GSTIN"), row, sheet, result, applicant_gstin,
    )

    # --- Document fields ---
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

    # Doc Value (mandatory)
    doc_value_str = validate_amount(
        data_row.get_value("Doc Value"), row, sheet, "Doc Value", result,
        error_key="doc_value_empty",
    )

    # --- SB / Endorsed Invoice pair (optional) ---
    _validate_sb_pair(data_row, row, sheet, result)

    # --- Tax fields ---
    # Taxable Value (mandatory)
    taxable_str = validate_amount(
        data_row.get_value("Taxable Value"), row, sheet, "Taxable Value", result,
        error_key="taxable_value_empty",
    )

    # IGST (mandatory)
    igst_str = validate_amount(
        data_row.get_value("IGST"), row, sheet, "IGST", result,
        error_key="igst_empty",
    )

    # Cess (optional — omitted from JSON when blank, unlike S02)
    cess_str = validate_amount(
        data_row.get_value("Cess"), row, sheet, "Cess", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )

    # --- Cross-field tax checks ---
    doc_value = to_json_number(doc_value_str) if doc_value_str else 0.0
    taxable = to_json_number(taxable_str) if taxable_str else 0.0
    igst = to_json_number(igst_str) if igst_str else 0.0
    cess = to_json_number(cess_str) if cess_str else 0.0

    if taxable > 0 and igst > 0:
        validate_igst_vs_taxable(igst, taxable, row, sheet, result)

    if doc_value > 0 and taxable > 0:
        validate_doc_value_vs_sum(doc_value, taxable, igst, cess, row, sheet, result)

    if taxable > 0 and igst > 0:
        check_implicit_rate(igst, taxable, row, sheet, result)

    # --- Duplicate detection ---
    if doc_type and doc_no and doc_date:
        dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)


def _validate_recipient_gstin(
    value: object,
    row: int,
    sheet: str,
    result: ValidationResult,
    applicant_gstin: str,
) -> None:
    """
    WHAT:
        Validates the Recipient GSTIN (SEZ unit/developer):
        1. Must not be empty
        2. Must match GSTIN regex format
        3. Must not be the same as the applicant's own GSTIN

    WHY ADDED:
        Blueprint section 7 note 2: "Recipient GSTIN must be different from
        the applicant's own GSTIN." Government VBA checks this explicitly.

    CALLED BY: _validate_data_row()
    """
    cleaned = clean_string(value)

    if not cleaned:
        result.add_error(
            message=RECIPIENT_ERRORS["recipient_gstin_empty"].format(row=row, sheet=sheet),
            sheet=sheet, row=row, field_name="Recipient GSTIN", category="document",
        )
        return

    # Format check
    if not GSTIN_REGEX.match(cleaned):
        result.add_error(
            message=(
                f"Row {row}, {sheet} Sheet: Recipient GSTIN '{cleaned}' does not "
                f"match the expected 15-character format. Please check for typos."
            ),
            sheet=sheet, row=row, field_name="Recipient GSTIN", category="document",
        )
        return

    # Must not be same as applicant
    if cleaned == applicant_gstin:
        result.add_error(
            message=RECIPIENT_ERRORS["recipient_gstin_same_as_self"].format(
                row=row, sheet=sheet, gstin=cleaned,
            ),
            sheet=sheet, row=row, field_name="Recipient GSTIN", category="document",
        )


def _validate_sb_pair(
    data_row: DataRow,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Validates the SB/Endorsed Invoice conditional pair (same logic as S05):
        - If SB No is provided → SB Date is required
        - If SB No is blank → both fields omitted from JSON
        SB Date: no GST inception lower bound, future date check applies.

    CALLED BY: _validate_data_row()

    ASSUMPTIONS:
        *** ASSUMPTION: SB Date has no lower bound (same as S05). ***
    """
    sb_no_raw = data_row.get_value("SB / Endorsed Invoice No")
    sb_date_raw = data_row.get_value("SB / Endorsed Invoice Date")

    has_no = not is_blank(sb_no_raw)
    has_date = not is_blank(sb_date_raw)

    if not has_no and not has_date:
        return

    if has_no:
        validate_endorsed_invoice(sb_no_raw, row, sheet, result)

        if not has_date:
            result.add_error(
                message=SHIPPING_ERRORS["sb_date_required"].format(row=row, sheet=sheet),
                sheet=sheet, row=row,
                field_name="SB / Endorsed Invoice Date",
                category="shipping",
            )
        else:
            validate_date(
                sb_date_raw, row, sheet, "SB / Endorsed Invoice Date", result,
                error_key_prefix="shipping_bill",
                check_gst_inception=False,
                check_future=True,
            )
