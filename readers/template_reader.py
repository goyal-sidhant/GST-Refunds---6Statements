"""
FILE: readers/template_reader.py

PURPOSE: High-level template reading orchestrator. Takes a file path and a
         StatementConfig, opens the workbook, enforces the template structure,
         reads the header sheet, and reads all data rows into DataRow objects.
         This is the single entry point for reading any of the 6 statement
         templates.

CONTAINS:
- read_template()  — Main function: file → (HeaderData, dict of DataRow lists)

DEPENDS ON:
- readers/excel_reader.py       → open_workbook(), read_cell(), read_data_rows()
- core/template_enforcer.py     → enforce_template()
- models/statement_config.py    → StatementConfig, SheetConfig
- models/header.py              → HeaderData
- models/data_row.py            → DataRow
- models/validation_result.py   → ValidationResult
- config/error_messages.py      → TEMPLATE_ERRORS, WARNINGS
- utils/date_helpers.py         → parse_date()

USED BY:
- gui/main_window.py  → the main processing pipeline calls this first

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — template reading pipeline | Phase 0 infrastructure setup       |
| 12-03-2026 | Empty sheet → warning not error     | Valid to file only Goods or Services |
| 12-03-2026 | Use parse_period() for period cells  | Excel converts MM-YYYY to datetime |
"""

from readers.excel_reader import open_workbook, read_cell, read_data_rows
from core.template_enforcer import enforce_template
from models.statement_config import StatementConfig, HeaderMode
from models.header import HeaderData
from models.data_row import DataRow
from models.validation_result import ValidationResult
from config.error_messages import TEMPLATE_ERRORS, WARNINGS
from utils.date_helpers import parse_date, parse_period


def read_template(
    file_path: str,
    config: StatementConfig,
    result: ValidationResult,
) -> dict:
    """
    WHAT:
        Reads a custom Excel template for a specific statement type.
        Performs template enforcement (strict column check), reads header
        data, and reads all data rows from each data sheet.

    WHY ADDED:
        This is the single entry point for the entire reading phase.
        The GUI calls this function, then passes the output to the
        statement-specific validator.

    CALLED BY:
        → gui/main_window.py → on "Process JSON" button click

    CALLS:
        → readers/excel_reader.py → open_workbook(), read_cell(), read_data_rows()
        → core/template_enforcer.py → enforce_template()

    EDGE CASES HANDLED:
        - File not found, locked, or wrong format → error in result
        - Template mismatch (wrong columns) → error in result
        - Empty data sheets → warning in result
        - Empty rows within data → skipped with warning

    PARAMETERS:
        file_path (str):          Full path to the .xlsx template file.
        config (StatementConfig): The statement configuration to enforce.
        result (ValidationResult): Errors and warnings are added here.

    RETURNS:
        dict: {
            "success": bool,
            "header": HeaderData or None,
            "sheets": dict[str, list[DataRow]] — sheet name → list of data rows,
        }
    """
    # --- Open the workbook ---
    open_result = open_workbook(file_path)
    if not open_result["success"]:
        result.add_error(
            message=open_result["error"],
            category="template",
        )
        return {"success": False, "header": None, "sheets": {}}

    workbook = open_result["data"]

    # --- Enforce template structure ---
    is_valid = enforce_template(workbook, config, result)
    if not is_valid:
        workbook.close()
        return {"success": False, "header": None, "sheets": {}}

    # --- Read header data ---
    header = _read_header(workbook, config)

    # --- Read data sheets ---
    sheets_data: dict[str, list[DataRow]] = {}

    for sheet_config in config.sheets:
        worksheet = workbook[sheet_config.name]
        column_count = len(sheet_config.columns)
        raw_rows = read_data_rows(worksheet, column_count)

        data_rows: list[DataRow] = []
        empty_row_numbers: list[int] = []

        for row_idx, raw_row in enumerate(raw_rows):
            excel_row = row_idx + 2  # Row 1 is headers, data starts at row 2

            # Build values dict keyed by column header
            values: dict[str, object] = {}
            for col_idx, col_spec in enumerate(sheet_config.columns):
                raw_value = raw_row[col_idx] if col_idx < len(raw_row) else None
                # Convert date cells to DD-MM-YYYY strings
                if col_spec.is_date and raw_value is not None:
                    raw_value = parse_date(raw_value)
                values[col_spec.header] = raw_value

            data_row = DataRow(
                sheet_name=sheet_config.name,
                excel_row=excel_row,
                values=values,
            )

            # Skip completely empty rows (but track them for warning)
            if data_row.is_empty():
                empty_row_numbers.append(excel_row)
                continue

            data_rows.append(data_row)

        # Warn about empty rows that were skipped
        if empty_row_numbers:
            # Only report the first contiguous block of empty rows at the end
            # (after last data row). Don't warn about trailing empty rows.
            # But DO warn about gaps in the middle.
            if data_rows:
                last_data_row = max(r.excel_row for r in data_rows)
                mid_empty = [r for r in empty_row_numbers if r < last_data_row]
                if mid_empty:
                    result.add_warning(
                        message=WARNINGS["empty_rows_summary"].format(
                            sheet=sheet_config.name,
                            count=len(mid_empty),
                            rows=", ".join(str(r) for r in mid_empty[:10])
                            + ("..." if len(mid_empty) > 10 else ""),
                        ),
                        sheet=sheet_config.name,
                        category="general",
                    )

        sheets_data[sheet_config.name] = data_rows

    # --- Check if ALL sheets are empty (error) vs SOME empty (warning) ---
    sheets_with_data = [name for name, rows in sheets_data.items() if rows]
    empty_sheets = [name for name, rows in sheets_data.items() if not rows]

    if not sheets_with_data:
        # ALL sheets are empty — this is an error, nothing to process
        result.add_error(
            message=TEMPLATE_ERRORS["all_sheets_empty"],
            category="template",
        )
    elif empty_sheets:
        # SOME sheets are empty — just a warning, the non-empty ones will be processed
        for sheet_name in empty_sheets:
            result.add_warning(
                message=WARNINGS["empty_sheet_skipped"].format(sheet_name=sheet_name),
                sheet=sheet_name,
                category="general",
            )

    workbook.close()
    return {"success": True, "header": header, "sheets": sheets_data}


def _read_header(workbook: object, config: StatementConfig) -> HeaderData:
    """
    WHAT: Reads header-level fields from the Header sheet based on the
          statement's header_cells configuration.
    CALLED BY: read_template() above.
    RETURNS: Populated HeaderData object.
    """
    header_sheet = workbook["Header"]
    header = HeaderData()

    # GSTIN is always present
    gstin_cell = config.header_cells.get("gstin")
    if gstin_cell:
        header.gstin = str(read_cell(header_sheet, gstin_cell[0], gstin_cell[1]) or "").strip()

    # Return periods (S01A, S03, S05)
    if config.header_mode == HeaderMode.PERIODS:
        from_cell = config.header_cells.get("from_period")
        if from_cell:
            raw = read_cell(header_sheet, from_cell[0], from_cell[1])
            # Excel may auto-convert "04-2024" to datetime — parse_period handles this
            header.from_period = parse_period(raw)

        to_cell = config.header_cells.get("to_period")
        if to_cell:
            raw = read_cell(header_sheet, to_cell[0], to_cell[1])
            # Excel may auto-convert "04-2024" to datetime — parse_period handles this
            header.to_period = parse_period(raw)

    # Order fields (S06)
    if config.header_mode == HeaderMode.ORDER:
        order_no_cell = config.header_cells.get("order_no")
        if order_no_cell:
            raw = read_cell(header_sheet, order_no_cell[0], order_no_cell[1])
            header.order_no = str(raw).strip() if raw is not None else ""

        order_date_cell = config.header_cells.get("order_date")
        if order_date_cell:
            raw = read_cell(header_sheet, order_date_cell[0], order_date_cell[1])
            header.order_date = parse_date(raw) if raw is not None else ""

    # S03 has Legal Name at B3 (not in JSON, just for reference)
    if config.code == "S03":
        raw = read_cell(header_sheet, "B", 3)
        header.legal_name = str(raw).strip() if raw is not None else ""

    return header
