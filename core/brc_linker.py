"""
FILE: core/brc_linker.py

PURPOSE: Implements BRC/FIRC linking logic for statements that support it
         (S02, S03). Two modes: Adjacent (default) and Group ID.
         Adjacent: BRC on a row covers all invoices above it until the
         previous BRC. Group ID: explicit linking via a Group ID column.
         After linking, verifies that every service invoice is covered.

CONTAINS:
- BrcLinkMode        — Enum for Adjacent vs Group ID
- link_brc_adjacent() — Links BRC to invoices by row proximity
- link_brc_group()    — Links BRC to invoices by Group ID
- verify_brc_coverage() — Ensures every required invoice has BRC coverage

DEPENDS ON:
- config/error_messages.py     → BRC_ERRORS
- models/data_row.py           → DataRow
- models/validation_result.py  → ValidationResult

USED BY:
- core/validators/stmt02_validator.py → link and verify
- core/validators/stmt03_validator.py → link and verify (Services sheet)

CHANGE LOG:
| Date       | Change                              | Why                                     |
|------------|-------------------------------------|-----------------------------------------|
| 11-03-2026 | Created — BRC linking logic         | Phase 0 infrastructure setup            |
"""

from enum import Enum

from config.error_messages import BRC_ERRORS
from models.data_row import DataRow
from models.validation_result import ValidationResult


class BrcLinkMode(Enum):
    """
    WHAT: The two BRC linking modes supported by the app.
    ADJACENT is the default (matches government VBA behaviour).
    GROUP requires explicit BRC Group ID column.
    """
    ADJACENT = "adjacent"
    GROUP = "group"


def link_brc_adjacent(
    rows: list[DataRow],
    brc_no_col: str = "BRC No",
) -> dict[int, int]:
    """
    WHAT:
        In Adjacent mode, a BRC on a row covers all invoice rows above it
        up to (but not including) the previous BRC row. Returns a mapping
        of invoice row → BRC row.

    WHY ADDED:
        Project Master Section 4.5: "Mode 1: ADJACENT (Default) — BRC on
        a row covers ALL invoices above it until previous BRC."

    CALLED BY:
        → core/validators/stmt02_validator.py
        → core/validators/stmt03_validator.py

    PARAMETERS:
        rows (list[DataRow]): Data rows from a single sheet.
        brc_no_col (str): Column header name for BRC Number.

    RETURNS:
        dict[int, int]: Maps each invoice's excel_row to the excel_row
        of the BRC that covers it. Uncovered rows are not in the dict.
    """
    coverage: dict[int, int] = {}

    # Walk backwards through rows. When we find a BRC, assign it to all
    # uncovered invoice rows above until we hit another BRC.
    pending_invoice_rows: list[int] = []

    for data_row in reversed(rows):
        brc_value = data_row.get_str(brc_no_col)

        if brc_value:
            # This row has a BRC — it covers all pending invoices
            for inv_row in pending_invoice_rows:
                coverage[inv_row] = data_row.excel_row
            # The BRC row itself is also covered (covers itself)
            coverage[data_row.excel_row] = data_row.excel_row
            pending_invoice_rows = []
        else:
            pending_invoice_rows.append(data_row.excel_row)

    return coverage


def link_brc_group(
    rows: list[DataRow],
    brc_no_col: str = "BRC No",
    group_id_col: str = "BRC Group ID",
) -> dict[int, int]:
    """
    WHAT:
        In Group ID mode, invoices are linked to BRC via explicit Group IDs.
        Each group must have exactly one row with BRC details.

    CALLED BY:
        → core/validators/stmt02_validator.py
        → core/validators/stmt03_validator.py

    PARAMETERS:
        rows (list[DataRow]): Data rows from a single sheet.
        brc_no_col (str): Column header name for BRC Number.
        group_id_col (str): Column header name for BRC Group ID.

    RETURNS:
        dict[int, int]: Maps each invoice's excel_row to the excel_row
        of the BRC that covers it.
    """
    coverage: dict[int, int] = {}

    # First pass: find the BRC row for each group
    group_brc_row: dict[str, int] = {}
    for data_row in rows:
        group_id = data_row.get_str(group_id_col)
        brc_value = data_row.get_str(brc_no_col)
        if group_id and brc_value:
            group_brc_row[group_id] = data_row.excel_row

    # Second pass: assign coverage
    for data_row in rows:
        group_id = data_row.get_str(group_id_col)
        brc_value = data_row.get_str(brc_no_col)

        if brc_value:
            # Row has its own BRC — covers itself
            coverage[data_row.excel_row] = data_row.excel_row
        elif group_id and group_id in group_brc_row:
            # Row is in a group that has a BRC
            coverage[data_row.excel_row] = group_brc_row[group_id]

    return coverage


def verify_brc_coverage(
    rows: list[DataRow],
    coverage: dict[int, int],
    sheet: str,
    result: ValidationResult,
    is_services: bool = True,
    brc_link_mode: BrcLinkMode = BrcLinkMode.ADJACENT,
    group_id_col: str = "BRC Group ID",
    doc_type_col: str = "Doc Type",
) -> None:
    """
    WHAT:
        Verifies that every invoice row that requires BRC coverage
        actually has it. For services, BRC is mandatory. For goods,
        BRC is optional.

    WHY ADDED:
        Services exports must have BRC proof of payment received.
        Without BRC coverage, the portal will reject the filing.

    CALLED BY:
        → core/validators/stmt02_validator.py
        → core/validators/stmt03_validator.py

    PARAMETERS:
        rows: Data rows from the sheet.
        coverage: Output from link_brc_adjacent() or link_brc_group().
        sheet: Sheet name.
        result: ValidationResult to add errors to.
        is_services: If True, uncovered rows are errors.
        brc_link_mode: Current linking mode.
        group_id_col: Column header for Group ID.
        doc_type_col: Column header for Doc Type.
    """
    if not is_services:
        return  # BRC is optional for goods

    uncovered_rows: list[int] = []
    for data_row in rows:
        # Skip BRC-only rows (no doc type = BRC-only entry)
        if not data_row.get_str(doc_type_col):
            continue

        if data_row.excel_row not in coverage:
            uncovered_rows.append(data_row.excel_row)

            # In Group ID mode, also check for missing Group ID
            if brc_link_mode == BrcLinkMode.GROUP:
                group_id = data_row.get_str(group_id_col)
                if not group_id:
                    result.add_error(
                        message=BRC_ERRORS["group_id_missing"].format(
                            row=data_row.excel_row, sheet=sheet,
                        ),
                        sheet=sheet,
                        row=data_row.excel_row,
                        field_name="BRC Group ID",
                        category="brc",
                    )

    if uncovered_rows:
        result.add_error(
            message=BRC_ERRORS["brc_coverage_missing"].format(
                sheet=sheet,
                rows=", ".join(str(r) for r in uncovered_rows),
            ),
            sheet=sheet,
            category="brc",
        )


def verify_group_has_brc(
    rows: list[DataRow],
    sheet: str,
    result: ValidationResult,
    brc_no_col: str = "BRC No",
    group_id_col: str = "BRC Group ID",
) -> None:
    """
    WHAT:
        In Group ID mode, verifies that every Group ID has at least one
        row with BRC details. A group without any BRC is an error.

    CALLED BY:
        → core/validators/stmt02_validator.py
        → core/validators/stmt03_validator.py
    """
    groups_seen: set[str] = set()
    groups_with_brc: set[str] = set()

    for data_row in rows:
        group_id = data_row.get_str(group_id_col)
        brc_value = data_row.get_str(brc_no_col)
        if group_id:
            groups_seen.add(group_id)
            if brc_value:
                groups_with_brc.add(group_id)

    for group_id in groups_seen - groups_with_brc:
        result.add_error(
            message=BRC_ERRORS["group_id_no_brc"].format(
                sheet=sheet, group_id=group_id,
            ),
            sheet=sheet,
            field_name="BRC Group ID",
            category="brc",
        )
