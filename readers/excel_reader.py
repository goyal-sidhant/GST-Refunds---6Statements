"""
FILE: readers/excel_reader.py

PURPOSE: Low-level openpyxl workbook operations — opening files, reading
         specific cells, and reading rows from a sheet. This module handles
         the interaction with openpyxl directly so that higher-level modules
         (template_reader.py) don't need to know openpyxl details.

CONTAINS:
- open_workbook()     — Opens an .xlsx file with openpyxl
- read_cell()         — Reads a single cell value
- read_data_rows()    — Reads all data rows from a sheet (row 2 onward)

DEPENDS ON:
- openpyxl (third-party library)
- config/settings.py           → MAX_DATA_ROWS
- config/error_messages.py     → TEMPLATE_ERRORS

USED BY:
- readers/template_reader.py   → uses all functions to read templates

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — openpyxl reader layer     | Phase 0 infrastructure setup       |
"""

# Python standard library
import os

# Third-party libraries
import openpyxl
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

# This project's modules
from config.settings import MAX_DATA_ROWS


def open_workbook(file_path: str) -> dict:
    """
    WHAT:
        Opens an .xlsx file using openpyxl with data_only=True
        (reads calculated values, not formulae).

    WHY ADDED:
        Centralises file opening so that error handling (file not found,
        file locked, wrong format) is in one place.

    CALLED BY:
        → readers/template_reader.py → read_template()

    EDGE CASES HANDLED:
        - File does not exist → {"success": False, "error": "..."}
        - File is locked by Excel → PermissionError caught
        - File is not a valid .xlsx → openpyxl exception caught

    PARAMETERS:
        file_path (str): Full path to the .xlsx file.

    RETURNS:
        dict: {"success": bool, "error": str or None, "data": Workbook or None}
    """
    if not file_path:
        return {"success": False, "error": "No file path provided.", "data": None}

    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "data": None,
        }

    if not file_path.lower().endswith(".xlsx"):
        filename = os.path.basename(file_path)
        return {
            "success": False,
            "error": f"File '{filename}' is not an .xlsx file. Only .xlsx format is supported.",
            "data": None,
        }

    try:
        workbook = openpyxl.load_workbook(file_path, data_only=True, read_only=False)
        return {"success": True, "error": None, "data": workbook}

    except PermissionError:
        filename = os.path.basename(file_path)
        return {
            "success": False,
            "error": f"Cannot open '{filename}' — it may be open in Excel. Please close it and try again.",
            "data": None,
        }

    except Exception as exc:
        filename = os.path.basename(file_path)
        return {
            "success": False,
            "error": f"Could not read '{filename}': {exc}",
            "data": None,
        }


def read_cell(worksheet: Worksheet, column: str, row: int) -> object:
    """
    WHAT:
        Reads a single cell value from a worksheet by column letter and row number.

    CALLED BY:
        → readers/template_reader.py → reading header cells (e.g., B2, B3)

    PARAMETERS:
        worksheet (Worksheet): The openpyxl worksheet object.
        column (str): Column letter (e.g., "B").
        row (int): Row number (1-based).

    RETURNS:
        object: The cell value (str, int, float, datetime, or None).
    """
    return worksheet[f"{column}{row}"].value


def read_data_rows(
    worksheet: Worksheet,
    column_count: int,
    start_row: int = 2,
) -> list[list[object]]:
    """
    WHAT:
        Reads all data rows from a worksheet, starting at start_row,
        up to MAX_DATA_ROWS. Each row is returned as a list of cell
        values (one per column, left to right).

    WHY ADDED:
        Centralises row reading so that the max-row limit and empty-row
        detection are handled consistently for all statement types.

    CALLED BY:
        → readers/template_reader.py → reading data sheets

    PARAMETERS:
        worksheet (Worksheet): The openpyxl worksheet object.
        column_count (int): Number of columns to read per row.
        start_row (int): First data row (default 2, since row 1 is headers).

    RETURNS:
        list[list[object]]: Each inner list is one row's cell values.
    """
    rows: list[list[object]] = []
    max_row = start_row + MAX_DATA_ROWS

    for row_num in range(start_row, max_row + 1):
        row_values: list[object] = []
        for col_num in range(1, column_count + 1):
            row_values.append(worksheet.cell(row=row_num, column=col_num).value)
        rows.append(row_values)

    return rows
