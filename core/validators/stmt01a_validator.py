"""
FILE: core/validators/stmt01a_validator.py

PURPOSE: Statement-specific validator for S01A — Inverted Tax Structure (INVITC).
         The most complex validator — two sheets (Inward + Outward) with 5 inward
         supply types and 3 outward supply types, each with different rules for
         Supplier GSTIN, Port Code, and tax mutual exclusivity.

CONTAINS:
- validate_stmt01a()            — Top-level entry point
- _validate_inward_row()        — Validates one Inward sheet row (type-specific)
- _validate_outward_row()       — Validates one Outward sheet row (type-specific)
- _validate_inward_type()       — Validates Inward Supply Type dropdown value
- _validate_outward_type()      — Validates Outward Supply Type dropdown value
- _validate_inward_gstin()      — Type-specific GSTIN rules (self/other/mandatory)
- _validate_inward_port_code()  — Port Code required for Import of Goods only
- _validate_inward_tax()        — Type-specific tax mutual exclusivity
- _validate_outward_tax()       — Type-specific outward tax rules

DEPENDS ON:
- core/field_validators.py      → validate_doc_type, validate_doc_no, validate_date,
                                   validate_amount, validate_port_code
- core/header_validator.py      → validate_header()
- core/tax_validators.py        → validate_tax_mutual_exclusivity, validate_tax_sum_vs_taxable,
                                   check_implicit_rate
- core/gstin_validator.py       → validate_gstin (for supplier GSTIN)
- core/duplicate_detector.py    → DuplicateDetector
- config/constants.py           → INWARD_SUPPLY_TYPES, OUTWARD_SUPPLY_TYPES,
                                   INWARD_SELF_GSTIN_TYPES, INWARD_DIFFERENT_GSTIN_TYPES,
                                   INWARD_PORT_CODE_REQUIRED_TYPE, INWARD_IGST_ONLY_TYPES,
                                   INWARD_ALL_TAX_ALLOWED_TYPE, INWARD_INVOICE_ONLY_TYPE,
                                   OUTWARD_IGST_ONLY_TYPE, OUTWARD_CGST_SGST_ONLY_TYPE,
                                   B2C_SMALL_DOC_NO
- config/error_messages.py      → SUPPLY_TYPE_ERRORS, TAX_ERRORS, SHIPPING_ERRORS
- config/regex_patterns.py      → GSTIN_REGEX
- models/ (StatementConfig, HeaderData, DataRow, ValidationResult)
- utils/string_helpers.py       → is_blank, clean_string
- utils/number_helpers.py       → to_json_number
- utils/date_helpers.py         → get_financial_year, get_month_year_from_date

USED BY:
- gui/main_window.py → called via _get_validator("S01A")

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 12-03-2026 | Created — S01A statement validator   | Phase 5: Inverted Tax Structure    |
"""

from models.statement_config import StatementConfig
from models.header import HeaderData
from models.data_row import DataRow
from models.validation_result import ValidationResult
from core.header_validator import validate_header
from core.field_validators import (
    validate_doc_type,
    validate_doc_no,
    validate_date,
    validate_amount,
    validate_port_code,
)
from core.tax_validators import (
    validate_tax_mutual_exclusivity,
    validate_tax_sum_vs_taxable,
    check_implicit_rate,
)
from core.gstin_validator import validate_gstin
from config.constants import (
    INWARD_SUPPLY_TYPES,
    OUTWARD_SUPPLY_TYPES,
    INWARD_SELF_GSTIN_TYPES,
    INWARD_DIFFERENT_GSTIN_TYPES,
    INWARD_PORT_CODE_REQUIRED_TYPE,
    INWARD_IGST_ONLY_TYPES,
    INWARD_ALL_TAX_ALLOWED_TYPE,
    INWARD_INVOICE_ONLY_TYPE,
    OUTWARD_IGST_ONLY_TYPE,
    OUTWARD_CGST_SGST_ONLY_TYPE,
)
from config.error_messages import SUPPLY_TYPE_ERRORS, TAX_ERRORS, SHIPPING_ERRORS
from config.regex_patterns import GSTIN_REGEX
from utils.string_helpers import is_blank, clean_string
from utils.number_helpers import to_json_number
from utils.date_helpers import get_financial_year, get_month_year_from_date


def validate_stmt01a(
    header: HeaderData,
    sheets: dict[str, list[DataRow]],
    config: StatementConfig,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Top-level S01A validation entry point. Validates the header (GSTIN +
        return periods), then validates each row in the Inward sheet (with
        type-specific rules for 5 supply types) and the Outward sheet (with
        type-specific rules for 3 supply types).

    WHY ADDED:
        S01A (INVITC) is the most complex of the 6 statements — 5 inward
        supply types each with different GSTIN, Port Code, and tax rules,
        plus 3 outward types with B2C-Small auto-fill logic.

    CALLED BY:
        → gui/main_window.py → _get_validator("S01A") returns this function

    ASSUMPTIONS:
        *** ASSUMPTION: Template enforcement has already passed. ***
        *** ASSUMPTION: Import types auto-fill self GSTIN in the generator,
            NOT the validator. The validator just checks that the GSTIN rules
            are met (blank or self for import types, different for Registered
            Person / ISD). ***
        *** ASSUMPTION: Inward duplicate key uses Supplier GSTIN + Doc No +
            FY + Month (matching govt VBA). Outward uses Outward Type + Doc
            Type suffix + Doc No + FY + Month. B2C-Small excluded. ***
    """
    # --- Step 1: Validate header ---
    validate_header(header, config.header_mode, result)

    applicant_gstin = header.gstin.upper() if header.gstin else ""

    # --- Step 2: Validate Inward sheet ---
    inward_rows = sheets.get("Inward", [])
    if inward_rows:
        inward_dup = _InwardDuplicateDetector()
        for data_row in inward_rows:
            _validate_inward_row(
                data_row, "Inward", result, inward_dup, applicant_gstin,
            )

    # --- Step 3: Validate Outward sheet ---
    outward_rows = sheets.get("Outward", [])
    if outward_rows:
        outward_dup = _OutwardDuplicateDetector()
        for data_row in outward_rows:
            _validate_outward_row(
                data_row, "Outward", result, outward_dup,
            )


# ==========================================================================
# Inward Row Validation
# ==========================================================================

def _validate_inward_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: "_InwardDuplicateDetector",
    applicant_gstin: str,
) -> None:
    """
    WHAT:
        Validates one Inward sheet row. Applies type-specific rules for GSTIN,
        Port Code, and tax mutual exclusivity based on the Inward Supply Type.

    CALLED BY: validate_stmt01a()
    """
    row = data_row.excel_row

    # Row presence: check Inward Supply Type
    supply_type_raw = data_row.get_value("Inward Supply Type")
    if is_blank(supply_type_raw):
        return  # Empty row

    # --- Validate Inward Supply Type ---
    supply_type = _validate_inward_type(supply_type_raw, row, sheet, result)
    if not supply_type:
        return  # Invalid type — cannot apply type-specific rules

    # --- Type-specific GSTIN rules ---
    _validate_inward_gstin(
        data_row.get_value("Supplier GSTIN"),
        supply_type, row, sheet, result, applicant_gstin,
    )

    # --- Doc Type (Import of Goods restricts to Invoice only) ---
    doc_type = validate_doc_type(
        data_row.get_value("Doc Type"), row, sheet, result,
    )
    if doc_type and supply_type == INWARD_INVOICE_ONLY_TYPE:
        if doc_type != "Invoice":
            result.add_error(
                message=(
                    f"Row {row}, {sheet} Sheet: For '{supply_type}', only 'Invoice' "
                    f"is allowed as Document Type (not '{doc_type}'). This represents "
                    f"a Bill of Entry."
                ),
                sheet=sheet, row=row, field_name="Doc Type", category="document",
            )

    # --- Doc No, Doc Date ---
    doc_no = validate_doc_no(
        data_row.get_value("Doc No"), row, sheet, result,
    )
    doc_date = validate_date(
        data_row.get_value("Doc Date"), row, sheet, "Doc Date", result,
        error_key_prefix="doc",
    )

    # --- Port Code (type-specific) ---
    _validate_inward_port_code(
        data_row.get_value("Port Code"), supply_type, row, sheet, result,
    )

    # --- Taxable Value (mandatory) ---
    taxable_str = validate_amount(
        data_row.get_value("Taxable Value"), row, sheet, "Taxable Value", result,
        error_key="taxable_value_empty",
    )

    # --- Tax amounts (conditional on type) ---
    igst_str = validate_amount(
        data_row.get_value("IGST"), row, sheet, "IGST", result,
        error_key="igst_empty",
        is_mandatory=False,
    )
    cgst_str = validate_amount(
        data_row.get_value("CGST"), row, sheet, "CGST", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )
    sgst_str = validate_amount(
        data_row.get_value("SGST"), row, sheet, "SGST", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )

    igst = to_json_number(igst_str) if igst_str else 0.0
    cgst = to_json_number(cgst_str) if cgst_str else 0.0
    sgst = to_json_number(sgst_str) if sgst_str else 0.0
    taxable = to_json_number(taxable_str) if taxable_str else 0.0

    # Type-specific tax mutual exclusivity
    _validate_inward_tax(supply_type, igst, cgst, sgst, row, sheet, result)

    # Tax sum <= Taxable Value
    if taxable > 0:
        validate_tax_sum_vs_taxable(igst, cgst, sgst, taxable, row, sheet, result)

    # Implicit rate check (WARNING) — use total tax
    total_tax = igst + cgst + sgst
    if taxable > 0 and total_tax > 0:
        check_implicit_rate(total_tax, taxable, row, sheet, result)

    # --- Duplicate detection ---
    supplier_gstin = clean_string(data_row.get_value("Supplier GSTIN"))
    if doc_no and doc_date:
        dup_detector.check(supplier_gstin, doc_no, doc_date, row, sheet, result)


def _validate_inward_type(
    value: object, row: int, sheet: str, result: ValidationResult,
) -> str:
    """
    WHAT: Validates Inward Supply Type against allowed values.
    RETURNS: Matched supply type string (or empty if invalid).
    """
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        result.add_error(
            message=SUPPLY_TYPE_ERRORS["inward_type_empty"].format(row=row),
            sheet=sheet, row=row, field_name="Inward Supply Type", category="supply_type",
        )
        return ""

    # Case-insensitive match
    for valid_type in INWARD_SUPPLY_TYPES:
        if cleaned.upper() == valid_type.upper():
            return valid_type  # Return canonical form

    result.add_error(
        message=SUPPLY_TYPE_ERRORS["inward_type_invalid"].format(row=row, value=cleaned),
        sheet=sheet, row=row, field_name="Inward Supply Type", category="supply_type",
    )
    return ""


def _validate_inward_gstin(
    value: object,
    supply_type: str,
    row: int,
    sheet: str,
    result: ValidationResult,
    applicant_gstin: str,
) -> None:
    """
    WHAT:
        Type-specific GSTIN validation for inward rows:
        - Import types / RCM: blank or self GSTIN (auto-filled in generator)
        - Registered Person / ISD: mandatory, must differ from self
    CALLED BY: _validate_inward_row()
    """
    cleaned = clean_string(value)

    if supply_type in INWARD_SELF_GSTIN_TYPES:
        # Import / RCM: supplier GSTIN should be blank or self.
        # Generator will auto-fill with self GSTIN. No error needed.
        return

    if supply_type in INWARD_DIFFERENT_GSTIN_TYPES:
        # Registered Person / ISD: GSTIN is mandatory and must differ from self
        if not cleaned:
            result.add_error(
                message=SUPPLY_TYPE_ERRORS["supplier_gstin_empty"].format(
                    row=row, supply_type=supply_type,
                ),
                sheet=sheet, row=row, field_name="Supplier GSTIN", category="document",
            )
            return

        if not GSTIN_REGEX.match(cleaned):
            result.add_error(
                message=(
                    f"Row {row}, {sheet} Sheet: Supplier GSTIN '{cleaned}' does not "
                    f"match the expected 15-character format."
                ),
                sheet=sheet, row=row, field_name="Supplier GSTIN", category="document",
            )
            return

        if cleaned == applicant_gstin:
            result.add_error(
                message=SUPPLY_TYPE_ERRORS["supplier_gstin_same_as_self"].format(
                    row=row, gstin=cleaned, supply_type=supply_type,
                ),
                sheet=sheet, row=row, field_name="Supplier GSTIN", category="document",
            )


def _validate_inward_port_code(
    value: object,
    supply_type: str,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Port Code is mandatory for "Import of Goods/Supplies from SEZ to DTA"
        and must be BLANK for all other inward types.
    CALLED BY: _validate_inward_row()
    """
    cleaned = clean_string(value)

    if supply_type == INWARD_PORT_CODE_REQUIRED_TYPE:
        # Port Code mandatory
        validate_port_code(value, row, sheet, result, is_mandatory=True)
    else:
        # Port Code must be blank
        if cleaned:
            result.add_error(
                message=SHIPPING_ERRORS["port_code_not_allowed"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Port Code", category="shipping",
            )


def _validate_inward_tax(
    supply_type: str,
    igst: float,
    cgst: float,
    sgst: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Type-specific tax rules for inward rows:
        - Import types: IGST only (CGST/SGST present → error)
        - ISD: all three allowed simultaneously
        - Registered Person / RCM: IGST XOR (CGST+SGST)
    CALLED BY: _validate_inward_row()
    """
    if supply_type in INWARD_IGST_ONLY_TYPES:
        # IGST only — CGST or SGST present → error
        if cgst > 0 or sgst > 0:
            result.add_error(
                message=TAX_ERRORS["cgst_sgst_not_allowed"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
        if igst <= 0:
            result.add_error(
                message=TAX_ERRORS["no_tax_entered"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
    elif supply_type == INWARD_ALL_TAX_ALLOWED_TYPE:
        # ISD: all three allowed, at least one must be present
        validate_tax_mutual_exclusivity(
            igst, cgst, sgst, row, sheet, result, allow_all_three=True,
        )
    else:
        # Standard: IGST XOR (CGST+SGST)
        validate_tax_mutual_exclusivity(
            igst, cgst, sgst, row, sheet, result, allow_all_three=False,
        )


# ==========================================================================
# Outward Row Validation
# ==========================================================================

def _validate_outward_row(
    data_row: DataRow,
    sheet: str,
    result: ValidationResult,
    dup_detector: "_OutwardDuplicateDetector",
) -> None:
    """
    WHAT:
        Validates one Outward sheet row. Applies type-specific rules:
        - B2B: IGST XOR (CGST+SGST), doc fields mandatory
        - B2C-Large: IGST only, doc fields mandatory
        - B2C-Small: CGST+SGST only, doc no/date blank (auto-filled in generator)

    CALLED BY: validate_stmt01a()
    """
    row = data_row.excel_row

    supply_type_raw = data_row.get_value("Outward Supply Type")
    if is_blank(supply_type_raw):
        return  # Empty row

    # --- Validate Outward Supply Type ---
    supply_type = _validate_outward_type(supply_type_raw, row, sheet, result)
    if not supply_type:
        return

    is_b2c_small = (supply_type == OUTWARD_CGST_SGST_ONLY_TYPE)

    # --- Doc Type ---
    doc_type = validate_doc_type(
        data_row.get_value("Doc Type"), row, sheet, result,
    )

    # --- Doc No and Doc Date ---
    if is_b2c_small:
        # B2C-Small: Doc No and Doc Date should be blank (auto-filled in generator)
        doc_no_raw = data_row.get_value("Doc No")
        doc_date_raw = data_row.get_value("Doc Date")
        if not is_blank(doc_no_raw) or not is_blank(doc_date_raw):
            result.add_warning(
                message=SUPPLY_TYPE_ERRORS["b2c_small_doc_not_blank"].format(row=row),
                sheet=sheet, row=row, field_name="Doc No", category="supply_type",
            )
        doc_no = ""
        doc_date = ""
    else:
        # B2B / B2C-Large: Doc No and Doc Date mandatory
        doc_no = validate_doc_no(
            data_row.get_value("Doc No"), row, sheet, result,
        )
        doc_date = validate_date(
            data_row.get_value("Doc Date"), row, sheet, "Doc Date", result,
            error_key_prefix="doc",
        )

    # --- Taxable Value (mandatory) ---
    taxable_str = validate_amount(
        data_row.get_value("Taxable Value"), row, sheet, "Taxable Value", result,
        error_key="taxable_value_empty",
    )

    # --- Tax amounts ---
    igst_str = validate_amount(
        data_row.get_value("IGST"), row, sheet, "IGST", result,
        error_key="igst_empty",
        is_mandatory=False,
    )
    cgst_str = validate_amount(
        data_row.get_value("CGST"), row, sheet, "CGST", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )
    sgst_str = validate_amount(
        data_row.get_value("SGST"), row, sheet, "SGST", result,
        error_key="cess_invalid",
        is_mandatory=False,
    )

    igst = to_json_number(igst_str) if igst_str else 0.0
    cgst = to_json_number(cgst_str) if cgst_str else 0.0
    sgst = to_json_number(sgst_str) if sgst_str else 0.0
    taxable = to_json_number(taxable_str) if taxable_str else 0.0

    # Type-specific tax rules
    _validate_outward_tax(supply_type, igst, cgst, sgst, row, sheet, result)

    # Tax sum <= Taxable Value
    if taxable > 0:
        validate_tax_sum_vs_taxable(igst, cgst, sgst, taxable, row, sheet, result)

    # Implicit rate check (WARNING)
    total_tax = igst + cgst + sgst
    if taxable > 0 and total_tax > 0:
        check_implicit_rate(total_tax, taxable, row, sheet, result)

    # --- Duplicate detection (B2C-Small excluded) ---
    if not is_b2c_small and doc_type and doc_no and doc_date:
        dup_detector.check(supply_type, doc_type, doc_no, doc_date, row, sheet, result)


def _validate_outward_type(
    value: object, row: int, sheet: str, result: ValidationResult,
) -> str:
    """
    WHAT: Validates Outward Supply Type against allowed values.
    RETURNS: Matched supply type string (or empty if invalid).
    """
    cleaned = str(value).strip() if value is not None else ""
    if not cleaned:
        result.add_error(
            message=SUPPLY_TYPE_ERRORS["outward_type_empty"].format(row=row),
            sheet=sheet, row=row, field_name="Outward Supply Type", category="supply_type",
        )
        return ""

    for valid_type in OUTWARD_SUPPLY_TYPES:
        if cleaned.upper() == valid_type.upper():
            return valid_type

    result.add_error(
        message=SUPPLY_TYPE_ERRORS["outward_type_invalid"].format(row=row, value=cleaned),
        sheet=sheet, row=row, field_name="Outward Supply Type", category="supply_type",
    )
    return ""


def _validate_outward_tax(
    supply_type: str,
    igst: float,
    cgst: float,
    sgst: float,
    row: int,
    sheet: str,
    result: ValidationResult,
) -> None:
    """
    WHAT:
        Type-specific tax rules for outward rows:
        - B2B: IGST XOR (CGST+SGST)
        - B2C-Large: IGST only (CGST/SGST → error)
        - B2C-Small: CGST+SGST only (IGST → error)
    CALLED BY: _validate_outward_row()
    """
    if supply_type == OUTWARD_IGST_ONLY_TYPE:
        # B2C-Large: IGST only
        if cgst > 0 or sgst > 0:
            result.add_error(
                message=TAX_ERRORS["cgst_sgst_not_allowed"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
        if igst <= 0:
            result.add_error(
                message=TAX_ERRORS["no_tax_entered"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
    elif supply_type == OUTWARD_CGST_SGST_ONLY_TYPE:
        # B2C-Small: CGST+SGST only
        if igst > 0:
            result.add_error(
                message=TAX_ERRORS["igst_not_allowed"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
        if cgst <= 0 and sgst <= 0:
            result.add_error(
                message=TAX_ERRORS["no_tax_entered"].format(row=row, sheet=sheet),
                sheet=sheet, row=row, field_name="Tax", category="tax",
            )
    else:
        # B2B: standard IGST XOR (CGST+SGST)
        validate_tax_mutual_exclusivity(
            igst, cgst, sgst, row, sheet, result, allow_all_three=False,
        )


# ==========================================================================
# Duplicate Detectors (S01A uses different key structures than other stmts)
# ==========================================================================

class _InwardDuplicateDetector:
    """
    WHAT:
        Inward duplicate key = Supplier GSTIN + "_" + Doc No + "_" + FY + "_" + Month.
        Matches government VBA logic for S01A inward.

    WHY ADDED:
        S01A inward duplicate key differs from other statements — it includes
        the Supplier GSTIN (because the same doc no from different suppliers
        is valid).
    """

    def __init__(self) -> None:
        self._keys: dict[str, int] = {}

    def check(
        self,
        supplier_gstin: str,
        doc_no: str,
        doc_date: str,
        row: int,
        sheet: str,
        result: ValidationResult,
    ) -> bool:
        if not doc_no or not doc_date:
            return False

        gstin_part = supplier_gstin.upper() if supplier_gstin else "SELF"
        month, year = get_month_year_from_date(doc_date)
        fy = get_financial_year(month, year) if month > 0 else 0

        key = f"{gstin_part}_{doc_no.upper()}_{fy}_{month:02d}"

        if key in self._keys:
            first_row = self._keys[key]
            result.add_error(
                message=(
                    f"Row {row}, {sheet} Sheet: Duplicate inward document — "
                    f"Doc No '{doc_no}' from this supplier already appears "
                    f"in Row {first_row}."
                ),
                sheet=sheet, row=row, field_name="Doc No", category="duplicate",
            )
            return True

        self._keys[key] = row
        return False


class _OutwardDuplicateDetector:
    """
    WHAT:
        Outward duplicate key = Outward Type + "_" + DocType suffix + "_" +
        Doc No + "_" + FY + "_" + Month. B2C-Small excluded.
        Government VBA: DN/CN mapped to "NOTE" in the key.
    """

    def __init__(self) -> None:
        self._keys: dict[str, int] = {}

    def check(
        self,
        supply_type: str,
        doc_type: str,
        doc_no: str,
        doc_date: str,
        row: int,
        sheet: str,
        result: ValidationResult,
    ) -> bool:
        if not doc_no or not doc_date:
            return False

        # Government VBA maps DN/CN to "NOTE" in the duplicate key
        doc_type_key = "NOTE" if doc_type in ("Debit Note", "Credit Note") else doc_type.upper()

        month, year = get_month_year_from_date(doc_date)
        fy = get_financial_year(month, year) if month > 0 else 0

        key = f"{supply_type.upper()}_{doc_type_key}_{doc_no.upper()}_{fy}_{month:02d}"

        if key in self._keys:
            first_row = self._keys[key]
            result.add_error(
                message=(
                    f"Row {row}, {sheet} Sheet: Duplicate outward document — "
                    f"{supply_type} / {doc_type} '{doc_no}' already appears "
                    f"in Row {first_row}."
                ),
                sheet=sheet, row=row, field_name="Doc No", category="duplicate",
            )
            return True

        self._keys[key] = row
        return False
