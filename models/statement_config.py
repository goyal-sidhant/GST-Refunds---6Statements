"""
FILE: models/statement_config.py

PURPOSE: Defines the StatementConfig and SheetConfig dataclasses that describe
         the structure, rules, and JSON mapping for each of the 6 statement
         types. These configs drive the entire pipeline — reader, enforcer,
         validator, and generator all consume them.

CONTAINS:
- TaxMode           — Enum: how tax columns behave for a statement
- HeaderField       — Enum: which header fields a statement requires
- SheetConfig       — Describes one data sheet (name, columns, JSON type flag)
- ColumnSpec        — Describes one column (name, JSON key, data type, mandatory)
- StatementConfig   — Full configuration for one statement type

DEPENDS ON:
- Nothing (pure data structure definitions)

USED BY:
- config/mappings.py         → creates 6 StatementConfig instances
- core/template_enforcer.py  → reads column specs for enforcement
- readers/template_reader.py → reads header cells and data sheets
- core/validators/*.py       → reads validation rules
- core/generators/*.py       → reads JSON key mappings

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — config dataclasses        | Phase 0 infrastructure setup       |
"""

from dataclasses import dataclass, field
from enum import Enum


class TaxMode(Enum):
    """
    WHAT: Describes how tax columns behave for a statement type.
    USED BY: core/tax_validators.py → determines which tax rules to apply.
    """
    NONE = "none"                   # No tax columns (S03, S05)
    IGST_CESS = "igst_cess"        # IGST + optional Cess (S02, S04)
    IGST_XOR_CGST_SGST = "igst_xor_cgst_sgst"  # S01A (type-dependent)
    EARLIER_CORRECT = "earlier_correct"          # S06 (directional tax blocks)


class HeaderMode(Enum):
    """
    WHAT: Describes which header fields a statement requires.
    USED BY: readers/template_reader.py → knows which cells to read.
    """
    PERIODS = "periods"             # GSTIN + From Period + To Period (S01A, S03, S05)
    GSTIN_ONLY = "gstin_only"       # GSTIN only — no periods (S02, S04)
    ORDER = "order"                 # GSTIN + Order No + Order Date (S06)


@dataclass(frozen=True)
class ColumnSpec:
    """
    WHAT: Describes a single column in a data sheet.

    PARAMETERS:
        header (str):        Exact column header text as it appears in row 1.
        json_key (str):      JSON key name for this field, or empty string if
                             the field is not included in JSON output.
        mandatory (bool):    Whether this field is always required. Fields that
                             are conditionally required (e.g., Port Code only
                             for Goods) should be False here — the validator
                             handles the conditional logic.
        is_date (bool):      True if the field holds a date value.
        is_amount (bool):    True if the field holds a monetary/numeric value.
        decimal_places (int): Max decimal places for amount fields (default 2).
    """
    header: str
    json_key: str = ""
    mandatory: bool = True
    is_date: bool = False
    is_amount: bool = False
    decimal_places: int = 2


@dataclass(frozen=True)
class SheetConfig:
    """
    WHAT: Describes one data sheet within a statement template.

    PARAMETERS:
        name (str):              Sheet name as it appears in the workbook tab.
        columns (tuple):         Ordered tuple of ColumnSpec — defines expected
                                 columns left-to-right. Template enforcer checks
                                 this exact sequence.
        json_type_flag (str):    Value for the "type" key in JSON (e.g., "G"
                                 for Goods, "S" for Services). Empty string if
                                 no type flag is used.
        has_brc_linking (bool):  Whether BRC Adjacent/Group ID linking applies.
        json_direction (dict):   For S06 only — hardcoded bInt/aInt values
                                 derived from the sheet name. Empty dict for
                                 other statements.
    """
    name: str
    columns: tuple[ColumnSpec, ...] = ()
    json_type_flag: str = ""
    has_brc_linking: bool = False
    json_direction: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StatementConfig:
    """
    WHAT: Complete configuration for one of the 6 GST refund statement types.
          This single object drives the entire pipeline for that statement.

    WHY ADDED:
        Configuration-driven architecture means the reader, enforcer,
        validator, and generator all consume the same config object.
        Adding or modifying a statement means updating config, not
        rewriting pipeline code.

    PARAMETERS:
        code (str):             Display code (e.g., "S03", "S01A").
        display_name (str):     Human-readable name for GUI dropdown.
        refund_reason (str):    JSON envelope "refundRsn" value.
        json_version (str):     JSON envelope "version" value.
        json_statement_key (str): JSON array key (e.g., "stmt03").
        header_mode (HeaderMode): Which header fields to expect.
        header_cells (dict):    Maps field names to (column, row) positions
                                in the Header sheet. Example:
                                {"gstin": ("B", 2), "from_period": ("B", 3)}
        sheets (tuple):         Ordered tuple of SheetConfig — one per data sheet.
        tax_mode (TaxMode):     How tax columns behave.
        has_sno_on_all (bool):  Whether all JSON nodes get an sno field.
                                False for S01A outward nodes.
    """
    code: str
    display_name: str
    refund_reason: str
    json_version: str
    json_statement_key: str
    header_mode: HeaderMode
    header_cells: dict[str, tuple[str, int]]
    sheets: tuple[SheetConfig, ...]
    tax_mode: TaxMode
    has_sno_on_all: bool = True
