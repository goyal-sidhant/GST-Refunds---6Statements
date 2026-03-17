"""
FILE: config/constants.py

PURPOSE: All fixed values used across the application — tax rates, date limits,
         length constraints, state codes, dropdown values, and document types.
         NO business logic lives here; only raw constants that logic files
         reference by name.

CONTAINS:
- GST_INCEPTION_DATE        — Earliest valid date for GST documents
- GST_RATE_SLABS            — Standard GST rate slabs for implicit rate checking
- RATE_TOLERANCE_PERCENT    — Tolerance for implicit rate comparison
- MAX_MANTISSA_DIGITS       — Maximum digits before decimal point
- MAX_DECIMAL_PLACES        — Default decimal places for amounts
- FOB_DECIMAL_PLACES        — FOB-specific 4 decimal places (S03 only)
- DOCUMENT_TYPES            — Valid document type values
- B2C_SMALL_DOC_NO          — Auto-filled doc number for B2C-Small (S01A)
- B2C_SMALL_DOC_DATE        — Auto-filled doc date for B2C-Small (S01A)
- INWARD_SUPPLY_TYPES       — S01A inward supply type dropdown values
- OUTWARD_SUPPLY_TYPES      — S01A outward supply type dropdown values
- PLACE_OF_SUPPLY_CODES     — 38 state/UT codes for S06 POS validation

DEPENDS ON:
- Nothing (pure constants)

USED BY:
- core/field_validators.py   → date limits, amount limits
- core/tax_validators.py     → GST_RATE_SLABS, RATE_TOLERANCE_PERCENT
- core/validators/*.py       → document types, supply types, POS codes
- config/mappings.py         → references these constants in statement configs
- config/regex_patterns.py   → references length constants

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — all constants for 6 stmts | Phase 0 infrastructure setup       |
"""

from datetime import date


# ---------------------------------------------------------------------------
# Date Limits
# ---------------------------------------------------------------------------

# GST was introduced on 01-07-2017. No GST document can pre-date this.
# Legal basis: Section 1(3) CGST Act 2017 — appointed day.
GST_INCEPTION_DATE: date = date(2017, 7, 1)

# ---------------------------------------------------------------------------
# Tax Rate Validation
# ---------------------------------------------------------------------------

# Standard GST rate slabs (percentage).
# Used by implicit rate checker to flag mismatches.
# Legal basis: Notification No. 1/2017-CT(Rate) and amendments.
GST_RATE_SLABS: tuple[float, ...] = (0.0, 0.1, 0.25, 1.0, 1.5, 3.0, 5.0, 6.0, 7.5, 12.0, 18.0, 28.0)

# Tolerance for implicit rate comparison (in percentage points).
# If (tax / taxable_value * 100) differs from the nearest standard slab
# by more than this amount, a WARNING is raised.
# Decision: Session 1 — implicit rate check is a WARNING, not an error.
RATE_TOLERANCE_PERCENT: float = 0.5

# ---------------------------------------------------------------------------
# Amount / Numeric Constraints
# ---------------------------------------------------------------------------

# Maximum digits before the decimal point (government VBA limit).
MAX_MANTISSA_DIGITS: int = 15

# Default decimal places for monetary amounts (15,2 format).
MAX_DECIMAL_PLACES: int = 2

# FOB Value in S03 allows 4 decimal places (unique exception).
# Government regex: ^([0-9]{0,15})([.][0-9]{0,4})?$
FOB_DECIMAL_PLACES: int = 4

# ---------------------------------------------------------------------------
# String Length Constraints
# ---------------------------------------------------------------------------

# GSTIN is always exactly 15 characters.
GSTIN_LENGTH: int = 15

# Document number: 1-16 alphanumeric characters (with / and - allowed).
DOC_NO_MAX_LENGTH: int = 16

# Port code: exactly 6 alphanumeric characters.
PORT_CODE_LENGTH: int = 6

# Shipping Bill number: 3-7 digits.
SHIPPING_BILL_MIN_LENGTH: int = 3
SHIPPING_BILL_MAX_LENGTH: int = 7

# EGM Reference: 1-20 alphanumeric characters.
EGM_REF_MAX_LENGTH: int = 20

# BRC/FIRC number: 2-30 alphanumeric characters.
BRC_NO_MIN_LENGTH: int = 2
BRC_NO_MAX_LENGTH: int = 30

# Recipient Name (S06 B2C): max 200 characters.
RECIPIENT_NAME_MAX_LENGTH: int = 200

# ---------------------------------------------------------------------------
# Document Types (shared across all 6 statements)
# ---------------------------------------------------------------------------

# Valid document type values for the "Doc Type" column.
# S01A uses "Invoice/Bill of Entry" (government VBA, S01A blueprint line 960).
# S02–S06 use "Invoice" (confirmed in each government VBA).
DOCUMENT_TYPES: tuple[str, ...] = (
    "Invoice", "Invoice/Bill of Entry", "Debit Note", "Credit Note",
)

# Document types that represent the original supply.
# Credit Notes and Debit Notes are adjustments.
CREDIT_NOTE: str = "Credit Note"
DEBIT_NOTE: str = "Debit Note"
INVOICE: str = "Invoice"
# S01A-specific: government VBA dropdown and JSON use this exact string.
INVOICE_BOE: str = "Invoice/Bill of Entry"

# ---------------------------------------------------------------------------
# S01A — Inward Supply Types
# ---------------------------------------------------------------------------

# Dropdown values for the "Inward Supply Type" column on the Inward sheet.
# These must match exactly what the custom S01A template has.
INWARD_SUPPLY_TYPES: tuple[str, ...] = (
    "Import of Goods/Supplies from SEZ to DTA",
    "Import of Services/Supplies from SEZ to DTA",
    "Inward supplies liable to reverse charge",
    "Inward Supply from Registered Person",
    "Inward Supplies from ISD",
)

# Inward types that require the GSTIN to be the applicant's own GSTIN
# (self-GSTIN auto-filled by the app in JSON).
INWARD_SELF_GSTIN_TYPES: tuple[str, ...] = (
    "Import of Goods/Supplies from SEZ to DTA",
    "Import of Services/Supplies from SEZ to DTA",
    "Inward supplies liable to reverse charge",
)

# Inward types that require a different supplier/ISD GSTIN.
INWARD_DIFFERENT_GSTIN_TYPES: tuple[str, ...] = (
    "Inward Supply from Registered Person",
    "Inward Supplies from ISD",
)

# Inward type that requires Port Code.
INWARD_PORT_CODE_REQUIRED_TYPE: str = "Import of Goods/Supplies from SEZ to DTA"

# Inward types that ONLY allow IGST (no CGST/SGST).
INWARD_IGST_ONLY_TYPES: tuple[str, ...] = (
    "Import of Goods/Supplies from SEZ to DTA",
    "Import of Services/Supplies from SEZ to DTA",
)

# Inward type that allows ALL three taxes simultaneously (IGST + CGST + SGST).
# This is unique to ISD — all others use IGST XOR (CGST+SGST).
INWARD_ALL_TAX_ALLOWED_TYPE: str = "Inward Supplies from ISD"

# Inward type that restricts Doc Type to Invoice/Bill of Entry only (no DN/CN).
# Government VBA (S01A blueprint line 960) validates exactly "Invoice/Bill of Entry".
INWARD_INVOICE_ONLY_TYPE: str = "Import of Goods/Supplies from SEZ to DTA"

# ---------------------------------------------------------------------------
# S01A — Outward Supply Types
# ---------------------------------------------------------------------------

# Dropdown values for the "Outward Supply Type" column on the Outward sheet.
OUTWARD_SUPPLY_TYPES: tuple[str, ...] = ("B2B", "B2C-Large", "B2C-Small")

# B2C-Small auto-fill values (user leaves Doc No and Date blank).
# Government VBA specification: fixed values for consolidated B2C-Small entry.
B2C_SMALL_DOC_NO: str = "B2COTH"
B2C_SMALL_DOC_DATE: str = "01-07-2017"

# Outward type that only allows IGST (no CGST/SGST).
OUTWARD_IGST_ONLY_TYPE: str = "B2C-Large"

# Outward type that only allows CGST+SGST (no IGST).
OUTWARD_CGST_SGST_ONLY_TYPE: str = "B2C-Small"

# ---------------------------------------------------------------------------
# S06 — Place of Supply Codes
# ---------------------------------------------------------------------------

# 38 state/UT codes used for Place of Supply validation in S06.
# Format: "XX-State Name" where XX is the 2-digit code.
# Source: Government VBA PlaceOfSupply helper sheet.
# Note: Code 28 (old undivided AP) is deliberately absent.
PLACE_OF_SUPPLY_CODES: dict[str, str] = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman and Diu",
    "26": "Dadra and Nagaraveli",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
}

# Full POS display values (e.g., "19-West Bengal") for dropdown matching.
PLACE_OF_SUPPLY_DISPLAY_VALUES: tuple[str, ...] = tuple(
    f"{code}-{name}" for code, name in sorted(PLACE_OF_SUPPLY_CODES.items())
)

# ---------------------------------------------------------------------------
# JSON Envelope Constants
# ---------------------------------------------------------------------------

# Refund reason codes (one per statement type).
REFUND_REASON_S01A: str = "INVITC"
REFUND_REASON_S02: str = "EXPWP"
REFUND_REASON_S03: str = "EXPWOP"
REFUND_REASON_S04: str = "SEZWP"
REFUND_REASON_S05: str = "SEZWOP"
REFUND_REASON_S06: str = "INTRVC"

# JSON version strings.
JSON_VERSION_2_0: str = "2.0"
JSON_VERSION_3_0: str = "3.0"
