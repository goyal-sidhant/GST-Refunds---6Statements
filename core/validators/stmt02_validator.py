"""
FILE: core/validators/stmt02_validator.py

PURPOSE: Statement-specific validator for S02 — Export of Services with Payment
         of Tax (EXPWP). Single "Data" sheet with 11 columns including tax fields
         (Taxable Value, IGST, Cess) and BRC/FIRC linking.

CONTAINS:
- validate_stmt02()        — Top-level entry point
- _validate_data_row()     — Validates one row (doc fields + tax + BRC)

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount, validate_brc_fields
- core/header_validator.py      → validate_header()
- core/duplicate_detector.py    → DuplicateDetector
- core/tax_validators.py        → validate_igst_vs_taxable, validate_doc_value_vs_sum,
                                   check_implicit_rate
- core/brc_linker.py            → BrcLinkMode, link_brc_adjacent, link_brc_group,
                                   verify_brc_coverage, verify_group_has_brc
- models/statement_config.py    → StatementConfig
- models/header.py              → HeaderData
- models/data_row.py            → DataRow
- models/validation_result.py   → ValidationResult
- utils/string_helpers.py       → is_blank
- utils/number_helpers.py       → to_json_number

USED BY:
- gui/main_window.py → called via _get_validator("S02")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S02 statement validator   | Phase 3: Export services with pay   |
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
    validate_brc_fields,
)
from core.duplicate_detector import DuplicateDetector
from core.tax_validators import (
    validate_igst_vs_taxable,
    validate_doc_value_vs_sum,
    check_implicit_rate,
)
from core.brc_linker import (
    BrcLinkMode,
    link_brc_adjacent,
    link_brc_group,
    verify_brc_coverage,
    verify_group_has_brc,
)
from utils.string_helpers import is_blank
from utils.number_helpers import to_json_number


def validate_stmt02(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S02 validation entry point. Validates the header (GSTIN only,
        no periods for v3.0), then iterates over each row in the single Data
        sheet, checking document fields, tax amounts, and BRC/FIRC linking.

    WHY ADDED:
        S02 (EXPWP) is the third statement being built. It adds tax validation
        (IGST + Cess) and BRC linking on a single-sheet layout.

    CALLED BY:
        → gui/main_window.py → _get_validator("S02") returns this function

    PARAMETERS:
        header (HeaderData): Validated header from the template.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S02 configuration from mappings.py.
        result (ValidationResult): Errors and warnings are added here.

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed. ***
        *** ASSUMPTION: BRC linking mode is ADJACENT by default. If any row
            has a non-empty BRC Group ID, the sheet switches to GROUP mode
            automatically. Same logic as S03. ***
        *** ASSUMPTION: Cess defaults to 0 in JSON (handled by generator),
            but the validator treats blank cess as valid (not an error). ***
    """
    # --- Step 1: Validate header (GSTIN only, no periods) ---
    validate_header(header, config.header_mode, result)

    # --- Step 2: Validate the single Data sheet ---
    sheet_config = config.sheets[0]  # S02 has exactly one sheet
    sheet_name = sheet_config.name
    rows = sheets.get(sheet_name, [])

    if not rows:
        return  # Template reader already warns about empty sheets

    # Determine BRC link mode
    brc_link_mode = _detect_brc_mode(rows)

    # Create duplicate detectors
    dup_detector = DuplicateDetector()

    for data_row in rows:
        _validate_data_row(data_row, sheet_name, result, dup_detector)

    # --- BRC coverage verification ---
    # S02 is export services — every invoice should be covered by BRC
    if sheet_config.has_brc_linking:
        if brc_link_mode == BrcLinkMode.ADJACENT:
            coverage = link_brc_adjacent(rows)
        else:
            coverage = link_brc_group(rows)
            verify_group_has_brc(rows, sheet_name, result)

        verify_brc_coverage(
            rows=rows,
            coverage=coverage,
            sheet=sheet_name,
            result=result,
            is_services=True,
            brc_link_mode=brc_link_mode,
        )


def _validate_data_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: DuplicateDetector,
) -> None:
    """
    WHAT:
        Validates one row from the Data sheet. Checks:
        1. Doc Type, Doc No, Doc Date, Doc Value (standard doc fields)
        2. Taxable Value, IGST (mandatory), Cess (optional)
        3. IGST <= Taxable Value
        4. Doc Value >= Taxable Value + IGST + Cess
        5. Implicit rate check (WARNING only)
        6. BRC fields (all-or-nothing rule)
        7. Duplicate detection (doc + BRC)

    CALLED BY: validate_stmt02()

    EDGE CASES HANDLED:
        - BRC-only row (no Doc Type but has BRC) → validates BRC only
        - Empty row (no doc, no BRC) → skipped
        - Cess blank → treated as 0 for cross-checks
    """
    row = data_row.excel_row

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

        # Doc Value (mandatory)
        doc_value_str = validate_amount(
            data_row.get_value("Doc Value"), row, sheet, "Doc Value", result,
            error_key="doc_value_empty",
        )

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

        # Cess (optional — blank is fine, defaults to 0 in JSON)
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

        # IGST must not exceed Taxable Value
        if taxable > 0 and igst > 0:
            validate_igst_vs_taxable(igst, taxable, row, sheet, result)

        # Doc Value >= Taxable Value + IGST + Cess
        if doc_value > 0 and taxable > 0:
            validate_doc_value_vs_sum(doc_value, taxable, igst, cess, row, sheet, result)

        # Implicit rate check (WARNING only — does not block JSON)
        if taxable > 0 and igst > 0:
            check_implicit_rate(igst, taxable, row, sheet, result)

        # --- Duplicate detection ---
        if doc_type and doc_no and doc_date:
            dup_detector.check_document(doc_type, doc_no, doc_date, row, sheet, result)

    # --- BRC fields (all-or-nothing rule) ---
    brc_no, brc_date, brc_value = validate_brc_fields(
        brc_no=data_row.get_value("BRC No"),
        brc_date=data_row.get_value("BRC Date"),
        brc_value=data_row.get_value("BRC Value"),
        row=row,
        sheet=sheet,
        result=result,
        is_mandatory=False,
    )

    # Duplicate BRC detection
    if brc_no:
        dup_detector.check_brc(brc_no, row, sheet, result)


def _detect_brc_mode(rows: list[DataRow]) -> BrcLinkMode:
    """
    WHAT: Auto-detects BRC linking mode. If any row has a non-empty
          BRC Group ID, uses GROUP mode. Otherwise ADJACENT.
    CALLED BY: validate_stmt02()
    RETURNS: BrcLinkMode.ADJACENT or BrcLinkMode.GROUP.
    """
    for data_row in rows:
        group_id = data_row.get_str("BRC Group ID")
        if group_id:
            return BrcLinkMode.GROUP
    return BrcLinkMode.ADJACENT
