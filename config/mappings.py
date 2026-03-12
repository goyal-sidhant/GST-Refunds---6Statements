"""
FILE: config/mappings.py

PURPOSE: Defines the complete StatementConfig for each of the 6 GST refund
         statement types. Each config specifies sheet names, exact column
         headers, JSON key mappings, tax mode, BRC linking, and header cell
         positions. The template enforcer, reader, validator, and generator
         all consume these configs.

CONTAINS:
- STMT_01A_CONFIG  — Inverted Tax Structure (most complex: 2 sheets, 5+3 types)
- STMT_02_CONFIG   — Export Services with Payment (single sheet, BRC linking)
- STMT_03_CONFIG   — Exports without Payment (2 sheets, BRC linking)
- STMT_04_CONFIG   — SEZ with Payment (single sheet, recipient GSTIN)
- STMT_05_CONFIG   — SEZ without Payment (2 sheets, lightest)
- STMT_06_CONFIG   — Intra/Inter Correction (2 sheets, POS, Earlier/Correct)
- ALL_STATEMENTS   — Dict mapping statement code to config
- STATEMENT_CHOICES — Ordered list of (code, display_name) for GUI dropdown

DEPENDS ON:
- models/statement_config.py  → StatementConfig, SheetConfig, ColumnSpec,
                                 TaxMode, HeaderMode

USED BY:
- gui/main_window.py          → STATEMENT_CHOICES for dropdown
- readers/template_reader.py  → ALL_STATEMENTS to look up config by code
- core/template_enforcer.py   → column specs for enforcement
- core/validators/*.py        → statement-specific rules
- core/generators/*.py        → JSON key mappings

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — all 6 statement configs   | Phase 0 infrastructure setup       |
"""

from models.statement_config import (
    StatementConfig,
    SheetConfig,
    ColumnSpec,
    TaxMode,
    HeaderMode,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 01A — Inverted Tax Structure (INVITC)
# ═══════════════════════════════════════════════════════════════════════════

_S01A_INWARD_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Inward Supply Type",  json_key="istype",  mandatory=True),
    ColumnSpec(header="Supplier GSTIN",      json_key="stin",    mandatory=False),
    ColumnSpec(header="Doc Type",            json_key="idtype",  mandatory=True),
    ColumnSpec(header="Doc No",              json_key="inum",    mandatory=True),
    ColumnSpec(header="Doc Date",            json_key="idt",     mandatory=True,  is_date=True),
    ColumnSpec(header="Port Code",           json_key="portcd",  mandatory=False),
    ColumnSpec(header="Taxable Value",       json_key="val",     mandatory=True,  is_amount=True),
    ColumnSpec(header="IGST",                json_key="iamt",    mandatory=False, is_amount=True),
    ColumnSpec(header="CGST",                json_key="camt",    mandatory=False, is_amount=True),
    ColumnSpec(header="SGST",                json_key="samt",    mandatory=False, is_amount=True),
)

_S01A_OUTWARD_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Outward Supply Type", json_key="ostype",  mandatory=True),
    ColumnSpec(header="Doc Type",            json_key="odtype",  mandatory=True),
    ColumnSpec(header="Doc No",              json_key="oinum",   mandatory=False),
    ColumnSpec(header="Doc Date",            json_key="oidt",    mandatory=False, is_date=True),
    ColumnSpec(header="Taxable Value",       json_key="oval",    mandatory=True,  is_amount=True),
    ColumnSpec(header="IGST",                json_key="oiamt",   mandatory=False, is_amount=True),
    ColumnSpec(header="CGST",                json_key="ocamt",   mandatory=False, is_amount=True),
    ColumnSpec(header="SGST",                json_key="osamt",   mandatory=False, is_amount=True),
)

STMT_01A_CONFIG = StatementConfig(
    code="S01A",
    display_name="S01A — Inverted Tax Structure",
    refund_reason="INVITC",
    json_version="2.0",
    json_statement_key="stmt01A",
    header_mode=HeaderMode.PERIODS,
    header_cells={
        "gstin": ("B", 2),
        "from_period": ("B", 3),
        "to_period": ("B", 4),
    },
    sheets=(
        SheetConfig(name="Inward",  columns=_S01A_INWARD_COLUMNS),
        SheetConfig(name="Outward", columns=_S01A_OUTWARD_COLUMNS),
    ),
    tax_mode=TaxMode.IGST_XOR_CGST_SGST,
    # Outward nodes in S01A do NOT get a serial number (sno).
    has_sno_on_all=False,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 02 — Export of Services with Payment of Tax (EXPWP)
# ═══════════════════════════════════════════════════════════════════════════

_S02_DATA_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Doc Type",       json_key="docType",     mandatory=True),
    ColumnSpec(header="Doc No",         json_key="inum",        mandatory=True),
    ColumnSpec(header="Doc Date",       json_key="idt",         mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",      json_key="val",         mandatory=True,  is_amount=True),
    ColumnSpec(header="Taxable Value",  json_key="iamtTxval",   mandatory=True,  is_amount=True),
    ColumnSpec(header="IGST",           json_key="iamt",        mandatory=True,  is_amount=True),
    ColumnSpec(header="Cess",           json_key="cess",        mandatory=False, is_amount=True),
    ColumnSpec(header="BRC No",         json_key="brcfircnum",  mandatory=False),
    ColumnSpec(header="BRC Date",       json_key="brcfircdt",   mandatory=False, is_date=True),
    ColumnSpec(header="BRC Value",      json_key="brcfircval",  mandatory=False, is_amount=True),
    ColumnSpec(header="BRC Group ID",   json_key="",            mandatory=False),
)

STMT_02_CONFIG = StatementConfig(
    code="S02",
    display_name="S02 — Export Services with Payment",
    refund_reason="EXPWP",
    json_version="3.0",
    json_statement_key="stmt02",
    header_mode=HeaderMode.GSTIN_ONLY,
    header_cells={
        "gstin": ("B", 2),
    },
    sheets=(
        SheetConfig(name="Data", columns=_S02_DATA_COLUMNS, has_brc_linking=True),
    ),
    tax_mode=TaxMode.IGST_CESS,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 03 — Exports without Payment of Tax (EXPWOP)
# ═══════════════════════════════════════════════════════════════════════════

_S03_GOODS_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Doc Type",    json_key="docType",     mandatory=True),
    ColumnSpec(header="Doc No",      json_key="inum",        mandatory=True),
    ColumnSpec(header="Doc Date",    json_key="idt",         mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",   json_key="val",         mandatory=True,  is_amount=True),
    ColumnSpec(header="Port Code",   json_key="sbpcode",     mandatory=True),
    ColumnSpec(header="SB No",       json_key="sbnum",       mandatory=True),
    ColumnSpec(header="SB Date",     json_key="sbdt",        mandatory=True,  is_date=True),
    ColumnSpec(header="FOB Value",   json_key="fobValue",    mandatory=True,  is_amount=True, decimal_places=4),
    ColumnSpec(header="EGM Ref No",  json_key="egmref",      mandatory=False),
    ColumnSpec(header="EGM Date",    json_key="egmrefdt",    mandatory=False, is_date=True),
    ColumnSpec(header="BRC No",      json_key="brcfircnum",  mandatory=False),
    ColumnSpec(header="BRC Date",    json_key="brcfircdt",   mandatory=False, is_date=True),
    ColumnSpec(header="BRC Value",   json_key="brcfircval",  mandatory=False, is_amount=True),
    ColumnSpec(header="BRC Group ID",json_key="",            mandatory=False),
)

_S03_SERVICES_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Doc Type",    json_key="docType",     mandatory=True),
    ColumnSpec(header="Doc No",      json_key="inum",        mandatory=True),
    ColumnSpec(header="Doc Date",    json_key="idt",         mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",   json_key="val",         mandatory=True,  is_amount=True),
    ColumnSpec(header="BRC No",      json_key="brcfircnum",  mandatory=False),
    ColumnSpec(header="BRC Date",    json_key="brcfircdt",   mandatory=False, is_date=True),
    ColumnSpec(header="BRC Value",   json_key="brcfircval",  mandatory=False, is_amount=True),
    ColumnSpec(header="BRC Group ID",json_key="",            mandatory=False),
)

STMT_03_CONFIG = StatementConfig(
    code="S03",
    display_name="S03 — Exports without Payment",
    refund_reason="EXPWOP",
    json_version="3.0",
    json_statement_key="stmt03",
    header_mode=HeaderMode.PERIODS,
    header_cells={
        "gstin": ("B", 2),
        # Row 3 is Legal Name — NOT in JSON, skipped by reader.
        "from_period": ("B", 4),
        "to_period": ("B", 5),
    },
    sheets=(
        SheetConfig(name="Goods",    columns=_S03_GOODS_COLUMNS,    json_type_flag="G", has_brc_linking=True),
        SheetConfig(name="Services", columns=_S03_SERVICES_COLUMNS, json_type_flag="S", has_brc_linking=True),
    ),
    tax_mode=TaxMode.NONE,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 04 — SEZ Supplies with Payment of Tax (SEZWP)
# ═══════════════════════════════════════════════════════════════════════════

_S04_DATA_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Recipient GSTIN",           json_key="rGstin",   mandatory=True),
    ColumnSpec(header="Doc Type",                  json_key="docType",  mandatory=True),
    ColumnSpec(header="Doc No",                    json_key="inum",     mandatory=True),
    ColumnSpec(header="Doc Date",                  json_key="idt",      mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",                 json_key="val",      mandatory=True,  is_amount=True),
    ColumnSpec(header="SB / Endorsed Invoice No",  json_key="sbnum",   mandatory=False),
    ColumnSpec(header="SB / Endorsed Invoice Date", json_key="sbdt",   mandatory=False, is_date=True),
    ColumnSpec(header="Taxable Value",             json_key="txval",    mandatory=True,  is_amount=True),
    ColumnSpec(header="IGST",                      json_key="iamt",    mandatory=True,  is_amount=True),
    ColumnSpec(header="Cess",                      json_key="cess",    mandatory=False, is_amount=True),
)

STMT_04_CONFIG = StatementConfig(
    code="S04",
    display_name="S04 — SEZ with Payment",
    refund_reason="SEZWP",
    json_version="3.0",
    json_statement_key="stmt04",
    header_mode=HeaderMode.GSTIN_ONLY,
    header_cells={
        "gstin": ("B", 2),
    },
    sheets=(
        SheetConfig(name="Data", columns=_S04_DATA_COLUMNS),
    ),
    tax_mode=TaxMode.IGST_CESS,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 05 — SEZ Supplies without Payment of Tax (SEZWOP)
# ═══════════════════════════════════════════════════════════════════════════

_S05_DATA_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Doc Type",                  json_key="docType",  mandatory=True),
    ColumnSpec(header="Doc No",                    json_key="inum",     mandatory=True),
    ColumnSpec(header="Doc Date",                  json_key="idt",      mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",                 json_key="val",      mandatory=True,  is_amount=True),
    ColumnSpec(header="SB / Endorsed Invoice No",  json_key="sbnum",   mandatory=False),
    ColumnSpec(header="SB / Endorsed Invoice Date", json_key="sbdt",   mandatory=False, is_date=True),
)

STMT_05_CONFIG = StatementConfig(
    code="S05",
    display_name="S05 — SEZ without Payment",
    refund_reason="SEZWOP",
    json_version="2.0",
    json_statement_key="stmt05",
    header_mode=HeaderMode.PERIODS,
    header_cells={
        "gstin": ("B", 2),
        "from_period": ("B", 3),
        "to_period": ("B", 4),
    },
    sheets=(
        SheetConfig(name="Goods",    columns=_S05_DATA_COLUMNS, json_type_flag="G"),
        SheetConfig(name="Services", columns=_S05_DATA_COLUMNS, json_type_flag="S"),
    ),
    tax_mode=TaxMode.NONE,
)


# ═══════════════════════════════════════════════════════════════════════════
# STATEMENT 06 — Intra/Inter-State Correction (INTRVC)
# ═══════════════════════════════════════════════════════════════════════════

_S06_INTER_TO_INTRA_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Recipient GSTIN",  json_key="uin",      mandatory=False),
    ColumnSpec(header="Recipient Name",   json_key="",         mandatory=False),
    ColumnSpec(header="Doc Type",         json_key="docType",  mandatory=True),
    ColumnSpec(header="Doc No",           json_key="inum",     mandatory=True),
    ColumnSpec(header="Doc Date",         json_key="idt",      mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",        json_key="val",      mandatory=True,  is_amount=True),
    ColumnSpec(header="Taxable Value",    json_key="txVal",    mandatory=True,  is_amount=True),
    ColumnSpec(header="IGST Paid",        json_key="bIGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="Earlier Cess",     json_key="bCess",    mandatory=False, is_amount=True),
    ColumnSpec(header="Earlier POS",      json_key="bPOS",     mandatory=True),
    ColumnSpec(header="Correct CGST",     json_key="aCGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="Correct SGST",     json_key="aSGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="Correct Cess",     json_key="aCess",    mandatory=False, is_amount=True),
    ColumnSpec(header="Correct POS",      json_key="aPOS",     mandatory=True),
)

_S06_INTRA_TO_INTER_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(header="Recipient GSTIN",  json_key="uin",      mandatory=False),
    ColumnSpec(header="Recipient Name",   json_key="",         mandatory=False),
    ColumnSpec(header="Doc Type",         json_key="docType",  mandatory=True),
    ColumnSpec(header="Doc No",           json_key="inum",     mandatory=True),
    ColumnSpec(header="Doc Date",         json_key="idt",      mandatory=True,  is_date=True),
    ColumnSpec(header="Doc Value",        json_key="val",      mandatory=True,  is_amount=True),
    ColumnSpec(header="Taxable Value",    json_key="txVal",    mandatory=True,  is_amount=True),
    ColumnSpec(header="CGST Paid",        json_key="bCGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="SGST Paid",        json_key="bSGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="Earlier Cess",     json_key="bCess",    mandatory=False, is_amount=True),
    ColumnSpec(header="Earlier POS",      json_key="bPOS",     mandatory=True),
    ColumnSpec(header="Correct IGST",     json_key="aIGST",   mandatory=True,  is_amount=True),
    ColumnSpec(header="Correct Cess",     json_key="aCess",    mandatory=False, is_amount=True),
    ColumnSpec(header="Correct POS",      json_key="aPOS",     mandatory=True),
)

STMT_06_CONFIG = StatementConfig(
    code="S06",
    display_name="S06 — Intra/Inter Correction",
    refund_reason="INTRVC",
    json_version="2.0",
    json_statement_key="stmt06",
    header_mode=HeaderMode.ORDER,
    header_cells={
        "gstin": ("B", 2),
        "order_no": ("B", 3),
        "order_date": ("B", 4),
    },
    sheets=(
        SheetConfig(
            name="Inter to Intra",
            columns=_S06_INTER_TO_INTRA_COLUMNS,
            json_direction={"bInt": "Inter", "aInt": "Intra"},
        ),
        SheetConfig(
            name="Intra to Inter",
            columns=_S06_INTRA_TO_INTER_COLUMNS,
            json_direction={"bInt": "Intra", "aInt": "Inter"},
        ),
    ),
    tax_mode=TaxMode.EARLIER_CORRECT,
)


# ═══════════════════════════════════════════════════════════════════════════
# Lookup Tables
# ═══════════════════════════════════════════════════════════════════════════

# Maps statement code → StatementConfig for programmatic lookup.
ALL_STATEMENTS: dict[str, StatementConfig] = {
    "S01A": STMT_01A_CONFIG,
    "S02":  STMT_02_CONFIG,
    "S03":  STMT_03_CONFIG,
    "S04":  STMT_04_CONFIG,
    "S05":  STMT_05_CONFIG,
    "S06":  STMT_06_CONFIG,
}

# Ordered list for the GUI dropdown (display order matches statement numbering).
STATEMENT_CHOICES: list[tuple[str, str]] = [
    (config.code, config.display_name)
    for config in [
        STMT_01A_CONFIG,
        STMT_02_CONFIG,
        STMT_03_CONFIG,
        STMT_04_CONFIG,
        STMT_05_CONFIG,
        STMT_06_CONFIG,
    ]
]
