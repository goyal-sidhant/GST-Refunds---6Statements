"""
FILE: core/generators/stmt01a_generator.py

PURPOSE: Generates the JSON data array for S01A — Inverted Tax Structure (INVITC).
         Two sheets: Inward (with sno) and Outward (without sno).
         Inward rows with import/RCM types get self GSTIN auto-filled.
         B2C-Small outward rows get auto-filled Doc No and Doc Date.
         All blank tax fields default to 0 in JSON.

CONTAINS:
- generate_stmt01a()         — Top-level entry point
- _build_inward_node()       — Builds one Inward JSON node (with sno)
- _build_outward_node()      — Builds one Outward JSON node (no sno)

DEPENDS ON:
- core/generators/json_envelope.py  → build_envelope()
- config/constants.py               → INWARD_SELF_GSTIN_TYPES, OUTWARD_CGST_SGST_ONLY_TYPE,
                                       B2C_SMALL_DOC_NO, B2C_SMALL_DOC_DATE
- models/statement_config.py        → StatementConfig
- models/header.py                  → HeaderData
- models/data_row.py                → DataRow
- utils/string_helpers.py           → is_blank, clean_string
- utils/number_helpers.py           → to_json_number
- utils/date_helpers.py             → parse_date

USED BY:
- gui/main_window.py → called via _get_generator("S01A")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S01A JSON generator       | Phase 5: Inverted Tax Structure    |
| 17-03-2026 | Map "Invoice" → "Invoice/Bill of    | Govt VBA S01A uses "Invoice/Bill   |
|            |   Entry" for idtype and odtype       |   of Entry" in JSON output         |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from core.generators.json_envelope import build_envelope
from config.constants import (
    INWARD_SELF_GSTIN_TYPES,
    OUTWARD_CGST_SGST_ONLY_TYPE,
    B2C_SMALL_DOC_NO,
    B2C_SMALL_DOC_DATE,
    INVOICE,
    INVOICE_BOE,
)
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number
from utils.date_helpers import parse_date


def generate_stmt01a(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
) -> dict:
    """
    WHAT:
        Generates the complete S01A JSON structure. Emits all Inward nodes
        first (with sequential sno), then all Outward nodes (without sno).

    WHY ADDED:
        S01A is the fifth statement being built and the most complex.
        The generator handles auto-fill logic for self GSTIN, B2C-Small
        fixed values, and the no-sno Outward exception.

    CALLED BY:
        → gui/main_window.py → _get_generator("S01A") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Validation has already passed. ***
        *** ASSUMPTION: All blank IGST/CGST/SGST → 0 in JSON (not omitted).
            Blueprint section 8 note 5. ***
        *** ASSUMPTION: Outward nodes have NO sno field. Blueprint section 5
            note: "Outward-only nodes do NOT have sno." ***
        *** ASSUMPTION: Import types / RCM auto-fill self GSTIN. If user
            entered something for these types, override with self GSTIN.
            Blueprint section 8 note 3. ***

    PARAMETERS:
        header (HeaderData): Validated header data.
        sheets (dict): Maps sheet name → list of DataRow objects.
        config (StatementConfig): S01A configuration.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    data_array: list[dict] = []
    sno_counter = 1
    applicant_gstin = header.gstin.upper() if header.gstin else ""

    # --- Inward nodes first (with sno) ---
    inward_rows = sheets.get("Inward", [])
    for data_row in inward_rows:
        if is_blank(data_row.get_value("Inward Supply Type")):
            continue

        node = _build_inward_node(data_row, sno_counter, applicant_gstin)
        data_array.append(node)
        sno_counter += 1

    # --- Outward nodes second (no sno) ---
    outward_rows = sheets.get("Outward", [])
    for data_row in outward_rows:
        if is_blank(data_row.get_value("Outward Supply Type")):
            continue

        node = _build_outward_node(data_row)
        data_array.append(node)

    return build_envelope(header, config, data_array)


def _build_inward_node(
    data_row: DataRow,
    sno: int,
    applicant_gstin: str,
) -> dict:
    """
    WHAT:
        Builds one Inward JSON node. Includes sno.
        Import types / RCM: auto-fills stin with applicant's own GSTIN.
        All blank tax fields default to 0.

    CALLED BY: generate_stmt01a()

    RETURNS: dict — one JSON node.
    """
    supply_type = str(data_row.get_value("Inward Supply Type")).strip()

    # Determine supplier GSTIN
    if supply_type in INWARD_SELF_GSTIN_TYPES:
        # Auto-fill with self GSTIN (override any user entry)
        supplier_gstin = applicant_gstin
    else:
        supplier_gstin = clean_string(data_row.get_value("Supplier GSTIN"))

    # Port Code: include only if present (empty string if blank)
    port_code = clean_string(data_row.get_value("Port Code"))

    # S01A uses "Invoice/Bill of Entry" — map "Invoice" for safety.
    doc_type = data_row.get_str("Doc Type")
    if doc_type == INVOICE:
        doc_type = INVOICE_BOE

    return {
        "sno": sno,
        "istype": supply_type,
        "stin": supplier_gstin,
        "idtype": doc_type,
        "inum": data_row.get_str("Doc No"),
        "idt": parse_date(data_row.get_value("Doc Date")),
        "portcd": port_code,
        "val": to_json_number(data_row.get_value("Taxable Value")),
        "iamt": _tax_or_zero(data_row.get_value("IGST")),
        "camt": _tax_or_zero(data_row.get_value("CGST")),
        "samt": _tax_or_zero(data_row.get_value("SGST")),
    }


def _build_outward_node(
    data_row: DataRow,
) -> dict:
    """
    WHAT:
        Builds one Outward JSON node. NO sno field.
        B2C-Small: auto-fills oinum="B2COTH", oidt="01-07-2017".
        All blank tax fields default to 0.

    CALLED BY: generate_stmt01a()

    RETURNS: dict — one JSON node (no sno key).
    """
    supply_type = str(data_row.get_value("Outward Supply Type")).strip()
    is_b2c_small = (supply_type == OUTWARD_CGST_SGST_ONLY_TYPE)

    # Doc No and Doc Date: auto-fill for B2C-Small
    if is_b2c_small:
        doc_no = B2C_SMALL_DOC_NO
        doc_date = B2C_SMALL_DOC_DATE
    else:
        doc_no = data_row.get_str("Doc No")
        doc_date = parse_date(data_row.get_value("Doc Date"))

    # S01A uses "Invoice/Bill of Entry" — map "Invoice" for safety.
    doc_type = data_row.get_str("Doc Type")
    if doc_type == INVOICE:
        doc_type = INVOICE_BOE

    return {
        "ostype": supply_type,
        "odtype": doc_type,
        "oinum": doc_no,
        "oidt": doc_date,
        "oval": to_json_number(data_row.get_value("Taxable Value")),
        "oiamt": _tax_or_zero(data_row.get_value("IGST")),
        "ocamt": _tax_or_zero(data_row.get_value("CGST")),
        "osamt": _tax_or_zero(data_row.get_value("SGST")),
    }


def _tax_or_zero(value: object) -> float:
    """
    WHAT: Returns the numeric value, or 0 if blank.
          S01A empty tax → 0 in JSON (not omitted).
    CALLED BY: _build_inward_node(), _build_outward_node()
    """
    if is_blank(value):
        return 0
    return to_json_number(value)
