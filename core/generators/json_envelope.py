"""
FILE: core/generators/json_envelope.py

PURPOSE: Builds the outer JSON envelope that wraps all statement data.
         Every statement type shares this same envelope structure:
         { gstin, fromFp/toFp or orderNo/orderDt, refundRsn, version, stmtXX: [...] }
         This module builds the envelope dict; statement-specific generators
         fill in the data array.

CONTAINS:
- build_envelope()  — Creates the top-level JSON dict

DEPENDS ON:
- models/header.py             → HeaderData
- models/statement_config.py   → StatementConfig, HeaderMode
- utils/date_helpers.py        → period_to_mmyyyy()

USED BY:
- core/generators/stmt03_generator.py  → wraps S03 data
- core/generators/stmt02_generator.py  → wraps S02 data
- (all other statement generators)

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — shared JSON envelope      | Phase 1 infrastructure             |
"""

from models.header import HeaderData
from models.statement_config import StatementConfig, HeaderMode
from utils.date_helpers import period_to_mmyyyy


def build_envelope(
    header: HeaderData,
    config: StatementConfig,
    data_array: list[dict],
) -> dict:
    """
    WHAT:
        Builds the top-level JSON envelope dict. The structure varies
        slightly by statement type (periods vs GSTIN-only vs order),
        but the pattern is the same.

    WHY ADDED:
        All 6 statements share the same envelope pattern. Centralising
        this avoids duplicating the envelope logic in each generator.

    CALLED BY:
        → core/generators/stmt*_generator.py → all 6 generators

    PARAMETERS:
        header (HeaderData): Validated header data from the template.
        config (StatementConfig): The statement configuration.
        data_array (list[dict]): The statement-specific data nodes.

    RETURNS:
        dict: Complete JSON structure ready for json.dump().
    """
    envelope: dict = {}

    # GSTIN is always present
    envelope["gstin"] = header.gstin

    # Period or order fields depend on header mode
    if config.header_mode == HeaderMode.PERIODS:
        envelope["fromFp"] = period_to_mmyyyy(header.from_period or "")
        envelope["toFp"] = period_to_mmyyyy(header.to_period or "")

    elif config.header_mode == HeaderMode.ORDER:
        envelope["orderNo"] = header.order_no or ""
        envelope["orderDt"] = header.order_date or ""

    # No extra fields for GSTIN_ONLY mode

    # Refund reason and version
    envelope["refundRsn"] = config.refund_reason
    envelope["version"] = config.json_version

    # Statement data array (key name varies per statement)
    envelope[config.json_statement_key] = data_array

    return envelope
