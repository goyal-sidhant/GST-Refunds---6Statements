"""
FILE: core/generators/stmt03_generator.py

PURPOSE: Generates the JSON data array for S03 — Exports without Payment
         of Tax (EXPWOP). Handles the 3 conditional emission paths:
         Path 1: Document-only (no BRC on row) → 1 node
         Path 2: BRC-only (no document on row) → 1 node
         Path 3: Combined (both doc and BRC on same row) → 2 nodes, same sno

         Serial numbers (sno) are sequential across both Goods and Services
         sheets. Goods rows are numbered first, then Services continues.

CONTAINS:
- generate_stmt03()          — Top-level entry point
- _build_goods_doc_node()    — Goods document node (with shipping fields)
- _build_services_doc_node() — Services document node (no shipping fields)
- _build_brc_node()          — BRC-only node
- _process_sheet_rows()      — Iterates rows and emits nodes

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- models/statement_config.py        → StatementConfig, SheetConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S03")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — S03 JSON generator        | Phase 1: first statement type      |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from utils.string_helpers import is_blank
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt03(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S03 JSON structure. Iterates over Goods
        rows first, then Services rows, assigning sequential sno numbers.
        Uses the 3-path conditional emission logic from the government VBA.

    WHY ADDED:
        S03 is the first statement being built. The JSON output must
        exactly match the structure the GST Portal expects.

    CALLED BY:
        → gui/main_window.py → _get_generator("S03") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. This generator
            does NOT re-validate data — it trusts the validator output.
            Invalid/missing fields will produce empty strings or 0.0 in
            the JSON, which the portal will reject. ***
        *** ASSUMPTION: sno numbering is sequential starting at 1,
            across both sheets. Goods rows first, Services continues. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S03 configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1

    # Process each sheet in config order (Goods first, then Services)
    for sheet_config in config.sheets:
        sheet_name = sheet_config.name
        rows = sheets.get(sheet_name, [])
        is_goods = (sheet_name == "Goods")
        type_flag = sheet_config.json_type_flag  # "G" or "S"

        for data_row in rows:
            has_doc = not is_blank(data_row.get_value("Doc Type"))
            has_brc = not is_blank(data_row.get_value("BRC No"))

            if not has_doc and not has_brc:
                continue  # Skip empty rows

            # --- Path 1: Document only (no BRC on this row) ---
            if has_doc and not has_brc:
                if is_goods:
                    node = _build_goods_doc_node(data_row, sno_counter, type_flag)
                else:
                    node = _build_services_doc_node(data_row, sno_counter, type_flag)
                data_array.append(node)
                sno_counter += 1

            # --- Path 2: BRC only (no document on this row) ---
            elif has_brc and not has_doc:
                node = _build_brc_node(data_row, sno_counter)
                data_array.append(node)
                sno_counter += 1

            # --- Path 3: Combined (both doc and BRC on same row) ---
            elif has_doc and has_brc:
                # Emit TWO nodes with the SAME sno
                if is_goods:
                    doc_node = _build_goods_doc_node(data_row, sno_counter, type_flag)
                else:
                    doc_node = _build_services_doc_node(data_row, sno_counter, type_flag)
                brc_node = _build_brc_node(data_row, sno_counter)

                data_array.append(doc_node)
                data_array.append(brc_node)
                sno_counter += 1

    return build_envelope(header, config, data_array)


def _build_goods_doc_node(
    data_row: DataRow,
    sno: int,
    type_flag: str,
) -> dict:
    """
    WHAT:
        Builds a Goods document node with shipping/customs fields.
        Includes: sno, docType, inum, idt, val, type, sbpcode, sbnum,
        sbdt, fobValue, and optionally egmref + egmrefdt.

    CALLED BY: generate_stmt03() → Path 1 or Path 3 (Goods)

    EDGE CASES HANDLED:
        - EGM fields: only included if both present (already validated)
        - FOB Value: 4 decimal places preserved by to_json_number()

    RETURNS: dict — one JSON node.
    """
    node: dict = {
        "sno": sno,
        "docType": _doc_type_to_json(data_row.get_str("Doc Type")),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "type": type_flag,
        "sbpcode": data_row.get_str("Port Code").upper(),
        "sbnum": _clean_sb_no(data_row.get_value("SB No")),
        "sbdt": parse_date(data_row.get_value("SB Date")),
        "fobValue": to_json_number(data_row.get_value("FOB Value")),
    }

    # EGM fields: include only if both present
    egm_ref = data_row.get_str("EGM Ref No")
    egm_date = parse_date(data_row.get_value("EGM Date"))
    if egm_ref and egm_date:
        node["egmref"] = egm_ref
        node["egmrefdt"] = egm_date

    return node


def _build_services_doc_node(
    data_row: DataRow,
    sno: int,
    type_flag: str,
) -> dict:
    """
    WHAT:
        Builds a Services document node — no shipping/customs fields.
        Includes: sno, docType, inum, idt, val, type.

    CALLED BY: generate_stmt03() → Path 1 or Path 3 (Services)

    RETURNS: dict — one JSON node.
    """
    return {
        "sno": sno,
        "docType": _doc_type_to_json(data_row.get_str("Doc Type")),
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "val": to_json_number(data_row.get_value("Doc Value")),
        "type": type_flag,
    }


def _build_brc_node(
    data_row: DataRow,
    sno: int,
) -> dict:
    """
    WHAT:
        Builds a BRC-only node. Includes: sno, brcfircnum, brcfircdt,
        brcfircval.

    CALLED BY: generate_stmt03() → Path 2 or Path 3

    RETURNS: dict — one JSON node.
    """
    return {
        "sno": sno,
        "brcfircnum": data_row.get_str("BRC No"),
        "brcfircdt": parse_date(data_row.get_value("BRC Date")),
        "brcfircval": to_json_number(data_row.get_value("BRC Value")),
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _doc_type_to_json(doc_type: str) -> str:
    """
    WHAT: Converts validated doc type to JSON format.
          Government JSON uses exact casing: "Invoice", "Debit Note", "Credit Note".
    CALLED BY: _build_goods_doc_node(), _build_services_doc_node()
    RETURNS: JSON-formatted doc type string.
    """
    # The canonical forms from validate_doc_type() already match
    # ("Invoice", "Debit Note", "Credit Note")
    return doc_type


def _clean_sb_no(value: object) -> str:
    """
    WHAT: Cleans shipping bill number — handles Excel float-to-int conversion.
          Excel may store "1234567" as 1234567.0.
    CALLED BY: _build_goods_doc_node()
    RETURNS: Clean string (digits only).
    """
    if value is None:
        return ""
    text = str(value).strip()
    if "." in text:
        try:
            text = str(int(float(text)))
        except (ValueError, OverflowError):
            pass
    return text
