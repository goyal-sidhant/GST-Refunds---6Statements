"""
FILE: config/regex_patterns.py

PURPOSE: All regular expression patterns used for field validation across
         the 6 statement types. Patterns are compiled once at import time
         for performance. Each pattern is documented with its source
         (government VBA reference) and what it validates.

CONTAINS:
- GSTIN_REGEX               — 15-character GSTIN format check
- DATE_REGEX                — dd-mm-yyyy date format
- RETURN_PERIOD_REGEX       — MM-YYYY period format (custom template format)
- DOC_NO_REGEX              — 1-16 alphanumeric document number
- AMOUNT_REGEX              — Up to 15 digits + 2 decimal places
- FOB_AMOUNT_REGEX          — Up to 15 digits + 4 decimal places (S03 only)
- PORT_CODE_REGEX           — Exactly 6 alphanumeric characters
- SHIPPING_BILL_REGEX       — 3-7 digits only
- ENDORSED_INVOICE_REGEX    — Alphanumeric with / and - (S04, S05)
- EGM_REF_REGEX             — 1-20 alphanumeric (no backslash, no quotes)
- BRC_NO_REGEX              — 2-30 alphanumeric characters

DEPENDS ON:
- Nothing (pure regex definitions)

USED BY:
- core/field_validators.py   → all field-level validation
- core/header_validator.py   → GSTIN and period validation
- core/validators/*.py       → statement-specific field checks

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — all patterns for 6 stmts  | Phase 0 infrastructure setup       |
"""

import re


# ---------------------------------------------------------------------------
# GSTIN Format
# ---------------------------------------------------------------------------

# Government VBA regex for GSTIN validation (structural format check only).
# Positions: 2 digits (state) + 5 letters + 4 digits + 1 letter + [1-9A-Z] + [Z1-9A-J] + [0-9A-Z]
# Note: Checksum validation is handled separately by the GSTIN validator skill.
# Source: All 6 government VBA files use this pattern.
GSTIN_REGEX: re.Pattern = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z1-9A-J]{1}[0-9A-Z]{1}$"
)

# ---------------------------------------------------------------------------
# Date Formats
# ---------------------------------------------------------------------------

# Date format: dd-mm-yyyy (used for all date fields across all statements).
# Source: Government VBA date validation regex.
DATE_REGEX: re.Pattern = re.compile(
    r"^[0-3][0-9]-[0-1][0-9]-[0-9]{4}$"
)

# Return period format: MM-YYYY (custom template format).
# The custom templates use MM-YYYY with a hyphen to prevent Excel from
# stripping leading zeros (e.g., "04-2026" instead of "042026").
# The app strips the hyphen when generating JSON (→ "042026").
# Decision: Rebuild Brief Section 6 — format changed from MMYYYY to MM-YYYY.
RETURN_PERIOD_REGEX: re.Pattern = re.compile(
    r"^[0-1][0-9]-[0-9]{4}$"
)

# ---------------------------------------------------------------------------
# Document Number
# ---------------------------------------------------------------------------

# Document/invoice number: 1-16 alphanumeric characters, / and - allowed.
# Source: Government VBA — ^[a-zA-Z0-9\/-]{0,16}$ (we enforce minimum 1).
DOC_NO_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9/\-]{1,16}$"
)

# ---------------------------------------------------------------------------
# Amounts (Monetary Values)
# ---------------------------------------------------------------------------

# Standard amount format: up to 15 digits before decimal, up to 2 after.
# Source: Government VBA — ^([0-9]{0,15})([.][0-9]{0,2})?$
AMOUNT_REGEX: re.Pattern = re.compile(
    r"^[0-9]{0,15}(\.[0-9]{0,2})?$"
)

# FOB Value format: up to 15 digits before decimal, up to 4 after.
# UNIQUE to S03 — FOB Value is the only field with 4 decimal places.
# Source: Government S03 VBA — ^([0-9]{0,15})([.][0-9]{0,4})?$
FOB_AMOUNT_REGEX: re.Pattern = re.compile(
    r"^[0-9]{0,15}(\.[0-9]{0,4})?$"
)

# ---------------------------------------------------------------------------
# Port / Shipping / EGM (Goods export evidence)
# ---------------------------------------------------------------------------

# Port code: exactly 6 alphanumeric characters.
# Source: Government VBA — ^[a-zA-Z0-9]{6}$
PORT_CODE_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9]{6}$"
)

# Shipping Bill number: 3-7 digits only (no letters).
# Source: Government S03 VBA — ^[0-9]{3,7}$
SHIPPING_BILL_REGEX: re.Pattern = re.compile(
    r"^[0-9]{3,7}$"
)

# SB / Endorsed Invoice number for S04, S05: alphanumeric with / and -.
# S04 and S05 use a more flexible format than S03's digits-only shipping bill.
# SEZ endorsement numbers may contain letters.
# Source: S05 blueprint — ^[a-zA-Z0-9\/-]+$
ENDORSED_INVOICE_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9/\-]+$"
)

# EGM Reference number: 1-20 alphanumeric characters.
# Cannot contain backslash (\) or double quotes (").
# Source: Government S03 VBA — ^[a-zA-Z0-9]{1,20}$
EGM_REF_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9]{1,20}$"
)

# ---------------------------------------------------------------------------
# BRC / FIRC (Banking evidence for services)
# ---------------------------------------------------------------------------

# BRC/FIRC number: 2-30 alphanumeric characters.
# Source: Government VBA — ^[a-zA-Z0-9]{2,30}$
BRC_NO_REGEX: re.Pattern = re.compile(
    r"^[a-zA-Z0-9]{2,30}$"
)
