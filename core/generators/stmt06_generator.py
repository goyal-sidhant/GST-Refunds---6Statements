"""
FILE: core/generators/stmt06_generator.py

PURPOSE: Generates the JSON data array for S06 — Intra/Inter-State Correction
         (INTRVC). Two sheets with direction-specific tax keys. B2B/B2C derived
         from Recipient GSTIN presence. bCess/aCess omitted when blank.

CONTAINS:
- generate_stmt06()                — Top-level entry point
- _build_inter_to_intra_node()     — Node for Inter→Intra sheet
- _build_intra_to_inter_node()     — Node for Intra→Inter sheet
- _derive_inv_type()               — B2B/B2C from GSTIN presence

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- models/statement_config.py        → StatementConfig, SheetConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank, clean_string
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S06")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S06 JSON generator        | Phase 6: Intra/Inter correction    |
"""

from models.statement_config import StatementConfig, SheetConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt06(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S06 JSON structure. Iterates "Inter to Intra"
        rows first, then "Intra to Inter" rows, with sequential sno across
        both sheets. Each row produces exactly one node.

    WHY ADDED:
        S06 is the final statement. It's unique: ORDER header mode, B2B/B2C
        derived, POS fields, direction-specific tax keys, bCess/aCess omitted.

    CALLED BY:
        → gui/main_window.py → _get_generator("S06") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. ***
        *** ASSUMPTION: bCess and aCess OMITTED from JSON when blank. ***
        *** ASSUMPTION: JSON key mapping follows mappings.py column specs:
            Inter to Intra: bIGST, aCGST, aSGST
            Intra to Inter: bCGST, bSGST, aIGST
            If the government portal requires different key names, this
            mapping will need adjustment. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S06 configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1

    for sheet_config in config.sheets:
        sheet_name = sheet_config.name
        rows = sheets.get(sheet_name, [])
        is_inter_to_intra = (sheet_config.json_direction.get("bInt") == "Inter")

        for data_row in rows:
            if is_blank(data_row.get_value("Doc Type")):
                continue  # Skip empty rows

            if is_inter_to_intra:
                node = _build_inter_to_intra_node(
                    data_row, sno_counter, sheet_config,
                )
            else:
                node = _build_intra_to_inter_node(
                    data_row, sno_counter, sheet_config,
                )

            data_array.append(node)
            sno_counter += 1

    return build_envelope(header, config, data_array)


def _build_inter_to_intra_node(
    data_row: DataRow,
    sno: int,
    sheet_config: SheetConfig,
) -> dict:
    """
    WHAT:
        Builds one node for Inter→Intra sheet.
        Earlier = Inter (IGST Paid → bIGST). Correct = Intra (CGST+SGST → aCGST+aSGST).
        bInt="Inter", aInt="Intra".

    CALLED BY: generate_stmt06()

    RETURNS: dict — one JSON node.
    """
    node: dict = {
        "sno": sno,
        "invType": _derive_inv_type(data_row),
        "uin": clean_string(data_row.get_value("Recipient GSTIN")),
        "docType": data_row.get_str("Doc Type"),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "txVal": to_json_number(data_row.get_value("Taxable Value")),
        "bInt": sheet_config.json_direction["bInt"],
        "bIGST": to_json_number(data_row.get_value("IGST Paid")),
    }

    # Earlier Cess (omit if blank)
    b_cess_raw = data_row.get_value("Earlier Cess")
    if not is_blank(b_cess_raw):
        node["bCess"] = to_json_number(b_cess_raw)

    node["bPOS"] = str(data_row.get_value("Earlier POS")).strip()
    node["aInt"] = sheet_config.json_direction["aInt"]
    node["aCGST"] = to_json_number(data_row.get_value("Correct CGST"))
    node["aSGST"] = to_json_number(data_row.get_value("Correct SGST"))

    # Correct Cess (omit if blank)
    a_cess_raw = data_row.get_value("Correct Cess")
    if not is_blank(a_cess_raw):
        node["aCess"] = to_json_number(a_cess_raw)

    node["aPOS"] = str(data_row.get_value("Correct POS")).strip()

    return node


def _build_intra_to_inter_node(
    data_row: DataRow,
    sno: int,
    sheet_config: SheetConfig,
) -> dict:
    """
    WHAT:
        Builds one node for Intra→Inter sheet.
        Earlier = Intra (CGST+SGST Paid → bCGST+bSGST). Correct = Inter (IGST → aIGST).
        bInt="Intra", aInt="Inter".

    CALLED BY: generate_stmt06()

    RETURNS: dict — one JSON node.
    """
    node: dict = {
        "sno": sno,
        "invType": _derive_inv_type(data_row),
        "uin": clean_string(data_row.get_value("Recipient GSTIN")),
        "docType": data_row.get_str("Doc Type"),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "txVal": to_json_number(data_row.get_value("Taxable Value")),
        "bInt": sheet_config.json_direction["bInt"],
        "bCGST": to_json_number(data_row.get_value("CGST Paid")),
        "bSGST": to_json_number(data_row.get_value("SGST Paid")),
    }

    # Earlier Cess (omit if blank)
    b_cess_raw = data_row.get_value("Earlier Cess")
    if not is_blank(b_cess_raw):
        node["bCess"] = to_json_number(b_cess_raw)

    node["bPOS"] = str(data_row.get_value("Earlier POS")).strip()
    node["aInt"] = sheet_config.json_direction["aInt"]
    node["aIGST"] = to_json_number(data_row.get_value("Correct IGST"))

    # Correct Cess (omit if blank)
    a_cess_raw = data_row.get_value("Correct Cess")
    if not is_blank(a_cess_raw):
        node["aCess"] = to_json_number(a_cess_raw)

    node["aPOS"] = str(data_row.get_value("Correct POS")).strip()

    return node


def _derive_inv_type(data_row: DataRow) -> str:
    """
    WHAT: Derives B2B/B2C from Recipient GSTIN presence.
          GSTIN filled → "B2B". Blank → "B2C".
    CALLED BY: _build_inter_to_intra_node(), _build_intra_to_inter_node()
    RETURNS: "B2B" or "B2C".
    """
    gstin = data_row.get_value("Recipient GSTIN")
    if not is_blank(gstin):
        return "B2B"
    return "B2C"
