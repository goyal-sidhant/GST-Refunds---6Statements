"""
FILE: models/header.py

PURPOSE: Defines the HeaderData dataclass that holds the metadata from the
         Header sheet of a custom Excel template — GSTIN, return periods,
         and order fields. This is the first data read from any template.

CONTAINS:
- HeaderData  — Dataclass holding all header-level fields

DEPENDS ON:
- Nothing (pure data structure)

USED BY:
- readers/template_reader.py  → creates HeaderData from the Header sheet
- core/header_validator.py    → validates all header fields
- core/generators/*.py        → reads header values for JSON envelope
- core/validators/*.py        → uses GSTIN for self-GSTIN comparisons

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — header data model         | Phase 0 infrastructure setup       |
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class HeaderData:
    """
    WHAT: Holds the metadata fields from the Header sheet.

    WHY ADDED:
        Every statement has a Header sheet with GSTIN and either
        return periods (S01A, S03, S05) or order fields (S06) or
        just GSTIN (S02, S04). This dataclass normalises all
        possible header fields into one structure.

    PARAMETERS:
        gstin (str):          The applicant's GSTIN from cell B2.
        from_period (str):    From Period in MM-YYYY format (or None).
        to_period (str):      To Period in MM-YYYY format (or None).
        order_no (str):       Order number for S06 (or None).
        order_date (str):     Order date in DD-MM-YYYY for S06 (or None).
        legal_name (str):     Optional legal name (S03 only, not in JSON).
    """
    gstin: str = ""
    from_period: Optional[str] = None
    to_period: Optional[str] = None
    order_no: Optional[str] = None
    order_date: Optional[str] = None
    legal_name: Optional[str] = None
