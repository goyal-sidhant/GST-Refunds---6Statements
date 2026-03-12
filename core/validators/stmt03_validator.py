"""
FILE: core/validators/stmt03_validator.py

PURPOSE: Statement-specific validator for S03 — Exports without Payment
         of Tax (EXPWOP). Validates both the Goods sheet (with shipping/
         customs fields) and the Services sheet (with mandatory BRC).
         Also handles BRC linking, duplicate detection, date ordering,
         and EGM pairing.

CONTAINS:
- validate_stmt03()         — Top-level entry point
- _validate_goods_row()     — Validates one Goods sheet row
- _validate_services_row()  — Validates one Services sheet row
- _validate_egm_pair()      — Both EGM fields must be present or both absent

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount, validate_port_code, validate_shipping_bill,
                                   validate_egm_ref, validate_brc_fields
- core/header_validator.py      → validate_header()
- core/duplicate_detector.py    → DuplicateDetector
- core/date_validators.py       → validate_sb_after_invoice, validate_egm_after_sb
- core/brc_linker.py            → BrcLinkMode, link_brc_adjacent, link_brc_group,
                                   verify_brc_coverage, verify_group_has_brc
- models/statement_config.py    → StatementConfig
- models/header.py              → HeaderData
- models/data_row.py            → DataRow
- models/validation_result.py   → ValidationResult
- utils/string_helpers.py       → is_blank
- utils/date_helpers.py         → parse_date

USED BY:
- gui/main_window.py → called via _get_validator("S03")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — S03 statement validator   | Phase 1: first statement type      |
| 12-03-2026 | BRC date must fall within period    | Realization must be in refund period|
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
    validate_port_code,
    validate_shipping_bill,
    validate_egm_ref,
    validate_brc_fields,
)
from core.duplicate_detector import DuplicateDetector
from core.date_validators import validate_sb_after_invoice, validate_egm_after_sb, validate_brc_within_period
from core.brc_linker import (
    BrcLinkMode,
    link_brc_adjacent,
    link_brc_group,
    verify_brc_coverage,
    verify_group_has_brc,
)
from utils.string_helpers import is_blank
from utils.date_helpers import parse_date


def validate_stmt03(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S03 validation entry point. Validates the header,
        then iterates over each row in the Goods and Services sheets,
        calling field validators, duplicate detector, date ordering
        checks, and BRC linking verification.

    WHY ADDED:
        S03 (EXPWOP) is the first statement being built. It has 2 data
        sheets (Goods with 14 columns, Services with 8 columns), BRC
        linking on both sheets, and Goods-specific shipping/customs fields.

    CALLED BY:
        → gui/main_window.py → _get_validator("S03") returns this function

    PARAMETERS:
        header (HeaderData): Validated header from the template.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S03 configuration from mappings.py.
        result (ValidationResult): Errors and warnings are added here.

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed (correct
            sheets exist with correct columns). This validator does not
            re-check sheet/column structure. ***
        *** ASSUMPTION: BRC linking mode is ADJACENT by default. If any
            row on a sheet has a non-empty BRC Group ID, that sheet
            switches to GROUP mode automatically. Decided in Session 1. ***
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

        is_goods = (sheet_name == "Goods")

        # Determine BRC link mode for this sheet
        brc_link_mode = _detect_brc_mode(rows)

        # Create a duplicate detector per sheet
        dup_detector = DuplicateDetector()

        for data_row in rows:
            if is_goods:
                _validate_goods_row(data_row, sheet_name, result, dup_detector, header)
            else:
                _validate_services_row(data_row, sheet_name, result, dup_detector, header)

        # --- BRC coverage verification (Services only) ---
        if sheet_config.has_brc_linking:
            if brc_link_mode == BrcLinkMode.ADJACENT:
                coverage = link_brc_adjacent(rows)
            else:
                coverage = link_brc_group(rows)
                verify_group_has_brc(rows, sheet_name, result)

            # Services require full BRC coverage; Goods do not
            verify_brc_coverage(
                rows=rows,
                coverage=coverage,
                sheet=sheet_name,
                result=result,
                is_services=(not is_goods),
                brc_link_mode=brc_link_mode,
            )


def _validate_goods_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
    header: HeaderData,
) -> None:
    """
    WHAT:
        Validates one row from the Goods sheet. Checks:
        1. Doc Type, Doc No, Doc Date, Doc Value (standard fields)
        2. Port Code, SB No, SB Date, FOB Value (shipping fields — mandatory)
        3. EGM Ref No + EGM Date (must be both present or both absent)
        4. BRC fields (optional for Goods, all-or-nothing rule)
        5. Duplicate detection
        6. Date ordering: SB Date >= Invoice Date, EGM Date >= SB Date

    CALLED BY: validate_stmt03()
    """
    row = data_row.excel_row

    # Check if this is a BRC-only row (no Doc Type but has BRC)
    has_doc = not is_blank(data_row.get_value("Doc Type"))
    has_brc = not is_blank(data_row.get_value("BRC No"))

    if not has_doc and not has_brc:
        return  # Empty row (should have been filtered by template reader)

    # --- Document fields (only if doc data present) ---
    doc_type = ""
    doc_no = ""
    doc_date = ""

    if has_doc:
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

        # --- Shipping fields (mandatory for Goods) ---
        validate_port_code(
            data_row.get_value("Port Code"), row, sheet, result,
            is_mandatory=True,
        )
        sb_no = validate_shipping_bill(
            data_row.get_value("SB No"), row, sheet, result,
            is_mandatory=True,
        )
        sb_date = validate_date(
            data_row.get_value("SB Date"), row, sheet, "SB Date", result,
            error_key_prefix="shipping_bill",
        )
        validate_amount(
            data_row.get_value("FOB Value"), row, sheet, "FOB Value", result,
            error_key="fob_value_empty",
            decimal_places=4,
        )

        # --- EGM pairing (both present or both absent) ---
        _validate_egm_pair(data_row, row, sheet, result)

        # --- Date ordering ---
        if doc_date and sb_date:
            validate_sb_after_invoice(doc_date, sb_date, row, sheet, result)

        egm_date = parse_date(data_row.get_value("EGM Date"))
        if sb_date and egm_date:
            validate_egm_after_sb(sb_date, egm_date, row, sheet, result)

        # --- Duplicate detection ---
        if doc_type and doc_no and doc_date:
            dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)

    # --- BRC fields (optional for Goods, all-or-nothing) ---
    brc_no, brc_date, brc_value = validate_brc_fields(
        brc_no=data_row.get_value("BRC No"),
        brc_date=data_row.get_value("BRC Date"),
        brc_value=data_row.get_value("BRC Value"),
        row=row,
        sheet=sheet,
        result=result,
        is_mandatory=False,
    )

    # BRC date must fall within the refund period
    if brc_date:
        validate_brc_within_period(
            brc_date, header.from_period, header.to_period, row, sheet, result,
        )

    # Duplicate BRC detection
    if brc_no:
        dup_detector.check_brc(brc_no, row, sheet, result)


def _validate_services_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
    header: HeaderData,
) -> None:
    """
    WHAT:
        Validates one row from the Services sheet. Checks:
        1. Doc Type, Doc No, Doc Date, Doc Value (standard fields)
        2. BRC fields (all-or-nothing rule; coverage checked separately)
        3. Duplicate detection
        No shipping/customs fields for Services.

    CALLED BY: validate_stmt03()
    """
    row = data_row.excel_row

    # Check if this is a BRC-only row (no Doc Type but has BRC)
    has_doc = not is_blank(data_row.get_value("Doc Type"))
    has_brc = not is_blank(data_row.get_value("BRC No"))

    if not has_doc and not has_brc:
        return  # Empty row

    # --- Document fields (only if doc data present) ---
    if has_doc:
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

        # Duplicate detection
        if doc_type and doc_no and doc_date:
            dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)

    # --- BRC fields (all-or-nothing) ---
    brc_no, brc_date, brc_value = validate_brc_fields(
        brc_no=data_row.get_value("BRC No"),
        brc_date=data_row.get_value("BRC Date"),
        brc_value=data_row.get_value("BRC Value"),
        row=row,
        sheet=sheet,
        result=result,
        is_mandatory=False,
    )

    # BRC date must fall within the refund period
    if brc_date:
        validate_brc_within_period(
            brc_date, header.from_period, header.to_period, row, sheet, result,
        )

    # Duplicate BRC detection
    if brc_no:
        dup_detector.check_brc(brc_no, row, sheet, result)


def _validate_egm_pair(
    data_row: DataRow,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Validates that EGM Ref No and EGM Date are either both present
        or both absent. If one is filled and the other is empty, that's
        an error.

    WHY ADDED:
        Government VBA spec: "EGM Ref No is mandatory if EGM Date is
        filled, and vice versa." They come as a pair.

    CALLED BY: _validate_goods_row()
    """
    egm_ref_raw = data_row.get_value("EGM Ref No")
    egm_date_raw = data_row.get_value("EGM Date")

    has_ref = not is_blank(egm_ref_raw)
    has_date = not is_blank(egm_date_raw)

    if has_ref and not has_date:
        result.add_error(
            message=(
                f"Row {row}, {sheet} Sheet: EGM Reference Number is filled but "
                f"EGM Date is empty. Both must be provided together, or leave both blank."
            ),
            sheet=sheet, row=row, field_name="EGM Date", category="shipping",
        )
    elif has_date and not has_ref:
        result.add_error(
            message=(
                f"Row {row}, {sheet} Sheet: EGM Date is filled but "
                f"EGM Reference Number is empty. Both must be provided together, or leave both blank."
            ),
            sheet=sheet, row=row, field_name="EGM Ref No", category="shipping",
        )

    # If both present, validate individually
    if has_ref and has_date:
        validate_egm_ref(egm_ref_raw, row, sheet, result, is_mandatory=True)
        # EGM Date: no GST inception check (can pre-date GST), but check future
        validate_date(
            egm_date_raw, row, sheet, "EGM Date", result,
            error_key_prefix="egm",
            check_gst_inception=False,
            check_future=True,
        )


def _detect_brc_mode(rows: list[DataRow]) -> BrcLinkMode:
    """
    WHAT:
        Auto-detects the BRC linking mode for a sheet. If any row has
        a non-empty BRC Group ID, the sheet uses GROUP mode. Otherwise,
        ADJACENT (default).

    CALLED BY: validate_stmt03() → per sheet

    RETURNS:
        BrcLinkMode: ADJACENT or GROUP.
    """
    for data_row in rows:
        group_id = data_row.get_str("BRC Group ID")
        if group_id:
            return BrcLinkMode.GROUP
    return BrcLinkMode.ADJACENT
