"""
FILE: core/generators/stmt02_generator.py

PURPOSE: Generates the JSON data array for S02 — Export of Services with Payment
         of Tax (EXPWP). Single "Data" sheet with BRC/FIRC linking and tax fields.
         Three conditional emission paths (doc-only, BRC-only, combined).

         In combined rows (both doc and BRC on same row), the BRC node is emitted
         FIRST, then the doc node — matching government VBA behaviour.

CONTAINS:
- generate_stmt02()      — Top-level entry point
- _build_doc_node()      — Document node with tax fields
- _build_brc_node()      — BRC-only node

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- models/statement_config.py        → StatementConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S02")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S02 JSON generator        | Phase 3: Export services with pay   |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from utils.string_helpers import is_blank
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt02(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S02 JSON structure. Single Data sheet with
        3 emission paths matching S03 logic but BRC node emitted FIRST in
        combined rows (per government VBA behaviour for S02).

    WHY ADDED:
        S02 is the third statement being built. It introduces tax fields
        (Taxable Value, IGST, Cess) into the JSON output.

    CALLED BY:
        → gui/main_window.py → _get_generator("S02") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. ***
        *** ASSUMPTION: Cess defaults to 0 in JSON when blank. Blueprint
            section 8 note 3: "Cess column blank → JSON 'cess': 0". ***
        *** ASSUMPTION: In combined rows (doc + BRC on same row), BRC node
            is emitted FIRST with same sno, then doc node. This matches
            government VBA order per blueprint section 8 note 7. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S02 configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1

    # S02 has exactly one sheet ("Data")
    sheet_config = config.sheets[0]
    sheet_name = sheet_config.name
    rows = sheets.get(sheet_name, [])

    for data_row in rows:
        has_doc = not is_blank(data_row.get_value("Doc Type"))
        has_brc = not is_blank(data_row.get_value("BRC No"))

        if not has_doc and not has_brc:
            continue  # Skip empty rows

        # --- Path 1: Document only (no BRC on this row) ---
        if has_doc and not has_brc:
            node = _build_doc_node(data_row, sno_counter)
            data_array.append(node)
            sno_counter += 1

        # --- Path 2: BRC only (no document on this row) ---
        elif has_brc and not has_doc:
            node = _build_brc_node(data_row, sno_counter)
            data_array.append(node)
            sno_counter += 1

        # --- Path 3: Combined (both doc and BRC on same row) ---
        # BRC node emitted FIRST, then doc node, same sno
        elif has_doc and has_brc:
            brc_node = _build_brc_node(data_row, sno_counter)
            doc_node = _build_doc_node(data_row, sno_counter)
            data_array.append(brc_node)
            data_array.append(doc_node)
            sno_counter += 1

    return build_envelope(header, config, data_array)


def _build_doc_node(
    data_row: DataRow,
    sno: int,
) -> dict:
    """
    WHAT:
        Builds a document node with tax fields for S02.
        Includes: sno, docType, inum, idt, val, iamtTxval, iamt, cess.
        Cess defaults to 0 when blank (not omitted).

    CALLED BY: generate_stmt02() → Path 1 or Path 3

    RETURNS: dict — one JSON node.
    """
    # Cess defaults to 0 if blank (blueprint note 3)
    cess_raw = data_row.get_value("Cess")
    cess_value = to_json_number(cess_raw) if not is_blank(cess_raw) else 0

    return {
        "sno": sno,
        "docType": data_row.get_str("Doc Type"),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "iamtTxval": to_json_number(data_row.get_value("Taxable Value")),
        "iamt": to_json_number(data_row.get_value("IGST")),
        "cess": cess_value,
    }


def _build_brc_node(
    data_row: DataRow,
    sno: int,
) -> dict:
    """
    WHAT:
        Builds a BRC-only node. Same structure as S03.
        Includes: sno, brcfircnum, brcfircdt, brcfircval.

    CALLED BY: generate_stmt02() → Path 2 or Path 3

    RETURNS: dict — one JSON node.
    """
    return {
        "sno": sno,
        "brcfircnum": data_row.get_str("BRC No"),
        "brcfircdt": parse_date(data_row.get_value("BRC Date")),
        "brcfircval": to_json_number(data_row.get_value("BRC Value")),
    }
