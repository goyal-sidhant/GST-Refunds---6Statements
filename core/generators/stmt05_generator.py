"""
FILE: core/generators/stmt05_generator.py

PURPOSE: Generates the JSON data array for S05 — SEZ Supplies without Payment
         of Tax (SEZWOP). The lightest generator — each row produces exactly
         one JSON node. Two emission paths based on SB/Endorsed Invoice presence.

         Serial numbers (sno) are sequential across both Goods and Services
         sheets. Goods rows are numbered first, then Services continues.

CONTAINS:
- generate_stmt05()     — Top-level entry point
- _build_node()         — Builds one JSON node (shared for Goods and Services)

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- models/statement_config.py        → StatementConfig, SheetConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S05")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S05 JSON generator        | Phase 2: SEZ without payment       |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from utils.string_helpers import is_blank
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt05(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S05 JSON structure. Iterates over Goods
        rows first, then Services rows, assigning sequential sno numbers.
        Each row produces exactly one node (no BRC splitting like S03).

    WHY ADDED:
        S05 is the second statement being built. It's the simplest JSON
        structure — just document fields + optional SB pair.

    CALLED BY:
        → gui/main_window.py → _get_generator("S05") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. This generator
            does NOT re-validate data — it trusts the validator output. ***
        *** ASSUMPTION: sno numbering is sequential starting at 1,
            across both sheets. Goods rows first, Services continues. ***
        *** ASSUMPTION: When sbnum is blank, both sbnum and sbdt are
            OMITTED from JSON entirely (not included as empty strings).
            This matches the S05 blueprint section 6. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S05 configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1

    # Process each sheet in config order (Goods first, then Services)
    for sheet_config in config.sheets:
        sheet_name = sheet_config.name
        rows = sheets.get(sheet_name, [])
        type_flag = sheet_config.json_type_flag  # "G" or "S"

        for data_row in rows:
            has_doc = not is_blank(data_row.get_value("Doc Type"))

            if not has_doc:
                continue  # Skip empty rows

            node = _build_node(data_row, sno_counter, type_flag)
            data_array.append(node)
            sno_counter += 1

    return build_envelope(header, config, data_array)


def _build_node(
    data_row: DataRow,
    sno: int,
    type_flag: str,
) -> dict:
    """
    WHAT:
        Builds one JSON node for an S05 row. Two paths:
        Path 1 (SB provided): includes sbnum and sbdt
        Path 2 (SB blank): omits sbnum and sbdt entirely

    CALLED BY: generate_stmt05()

    EDGE CASES HANDLED:
        - SB No blank → sbnum and sbdt keys omitted from dict
        - Doc Type already in canonical form from validator

    RETURNS: dict — one JSON node.
    """
    node: dict = {
        "sno": sno,
        "docType": data_row.get_str("Doc Type"),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "type": type_flag,
    }

    # --- Path 1: SB / Endorsed Invoice provided → include sbnum + sbdt ---
    sb_no = data_row.get_str("SB / Endorsed Invoice No")
    if sb_no:
        node["sbnum"] = sb_no
        sb_date = parse_date(data_row.get_value("SB / Endorsed Invoice Date"))
        if sb_date:
            node["sbdt"] = sb_date

    # --- Path 2: SB blank → sbnum and sbdt omitted (already not in dict) ---

    return node
