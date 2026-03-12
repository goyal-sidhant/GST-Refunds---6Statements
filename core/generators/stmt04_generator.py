"""
FILE: core/generators/stmt04_generator.py

PURPOSE: Generates the JSON data array for S04 — SEZ Supplies with Payment of Tax
         (SEZWP). Single "Data" sheet with Recipient GSTIN, tax fields, and optional
         SB/Endorsed Invoice pair. Four conditional paths based on sbnum and cess
         presence. No BRC linking.

CONTAINS:
- generate_stmt04()     — Top-level entry point
- _build_node()         — Builds one JSON node with conditional sbnum/sbdt and cess

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- models/statement_config.py        → StatementConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank, clean_string
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S04")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S04 JSON generator        | Phase 4: SEZ with payment          |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt04(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S04 JSON structure. Single Data sheet, each row
        produces exactly one node. Four conditional paths based on whether
        sbnum and cess are present or blank.

    WHY ADDED:
        S04 is the fourth statement being built. Structurally similar to S02
        but with Recipient GSTIN, SB pair instead of BRC, and Cess OMITTED
        (not defaulted to 0) when blank.

    CALLED BY:
        → gui/main_window.py → _get_generator("S04") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. ***
        *** ASSUMPTION: sbnum, sbdt, and cess are OMITTED from JSON when blank.
            Blueprint section 7 note 3: "S04 OMITS sbnum/sbdt/cess from JSON
            when blank." This differs from S02 where blank cess → 0. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S04 configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1

    # S04 has exactly one sheet ("Data")
    sheet_config = config.sheets[0]
    sheet_name = sheet_config.name
    rows = sheets.get(sheet_name, [])

    for data_row in rows:
        # S04 uses Recipient GSTIN as row presence indicator
        has_data = not is_blank(data_row.get_value("Recipient GSTIN"))

        if not has_data:
            continue  # Skip empty rows

        node = _build_node(data_row, sno_counter)
        data_array.append(node)
        sno_counter += 1

    return build_envelope(header, config, data_array)


def _build_node(
    data_row: DataRow,
    sno: int,
) -> dict:
    """
    WHAT:
        Builds one JSON node for an S04 row. Four conditional paths:
        Path 1: Both SB and Cess present
        Path 2: Both SB and Cess blank
        Path 3: SB present, Cess blank
        Path 4: SB blank, Cess present

        sbnum, sbdt, and cess are OMITTED when blank (not set to 0/empty).

    CALLED BY: generate_stmt04()

    RETURNS: dict — one JSON node.
    """
    # Core fields (always present)
    node: dict = {
        "sno": sno,
        "rGstin": clean_string(data_row.get_value("Recipient GSTIN")),
        "docType": data_row.get_str("Doc Type"),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
    }

    # --- SB / Endorsed Invoice (omit if blank) ---
    sb_no = data_row.get_str("SB / Endorsed Invoice No")
    if sb_no:
        node["sbnum"] = sb_no
        sb_date = parse_date(data_row.get_value("SB / Endorsed Invoice Date"))
        if sb_date:
            node["sbdt"] = sb_date

    # Tax fields (always present)
    node["txval"] = to_json_number(data_row.get_value("Taxable Value"))
    node["iamt"] = to_json_number(data_row.get_value("IGST"))

    # --- Cess (omit if blank — differs from S02 which defaults to 0) ---
    cess_raw = data_row.get_value("Cess")
    if not is_blank(cess_raw):
        cess_value = to_json_number(cess_raw)
        if cess_value > 0:
            node["cess"] = cess_value

    return node
