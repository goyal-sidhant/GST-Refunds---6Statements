"""
FILE: core/duplicate_detector.py

PURPOSE: Detects duplicate documents and duplicate BRC/FIRC numbers within
         a data sheet. Duplicates are identified by a composite key that
         includes document type, number, and financial year — matching the
         government VBA's duplicate detection logic.

CONTAINS:
- DuplicateDetector  — Tracks seen documents and BRCs, reports duplicates

DEPENDS ON:
- config/error_messages.py     → DUPLICATE_ERRORS
- models/validation_result.py  → ValidationResult
- utils/date_helpers.py        → get_financial_year(), get_month_year_from_date()

USED BY:
- core/validators/*.py → creates a DuplicateDetector per sheet

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — duplicate detection       | Phase 0 infrastructure setup       |
"""

from config.error_messages import DUPLICATE_ERRORS
from models.validation_result import ValidationResult
from utils.date_helpers import get_financial_year, get_month_year_from_date


class DuplicateDetector:
    """
    WHAT:
        Tracks document and BRC numbers seen so far within a sheet.
        When a duplicate is detected, adds an error to the ValidationResult
        referencing both the current row and the row where the key was first seen.

    WHY ADDED:
        Rebuild Brief Section 5: "Ensure the tool throws an error if the user
        accidentally inputs the exact same BRC/FIRC number twice."
        Also: Government VBA uses composite keys for duplicate doc detection.

    CALLED BY:
        → core/validators/*.py → check_document(), check_brc()
    """

    def __init__(self) -> None:
        """
        WHAT: Initialises empty tracking dictionaries.
        """
        # Maps composite key → first-seen Excel row number
        self._doc_keys: dict[str, int] = {}
        self._brc_keys: dict[str, int] = {}

    def check_document(
        self,
        doc_type: str,
        doc_no: str,
        doc_date: str,
        row: int,
        sheet: str,
        result: ValidationResult,
    ) -> bool:
        """
        WHAT:
            Checks if this document has already been seen in this sheet.
            Duplicate key follows government VBA logic:
            DocType suffix + "_" + DocNo + "_" + FY

        WHY ADDED:
            Government VBA builds: last 4 chars of doc type + "_" + doc no
            + "_" + FY year (Jan-Mar adjusted). This catches cases where
            the same invoice number appears twice in the same financial year.

        CALLED BY:
            → core/validators/*.py → after validating individual fields

        PARAMETERS:
            doc_type (str): "Invoice", "Debit Note", or "Credit Note".
            doc_no (str): The document number.
            doc_date (str): The document date in DD-MM-YYYY format.
            row (int): Excel row number.
            sheet (str): Sheet name.
            result (ValidationResult): Errors added here.

        RETURNS:
            bool: True if duplicate (error added), False if unique.
        """
        if not doc_type or not doc_no or not doc_date:
            return False

        # Build the composite key matching government VBA logic
        # Government uses last 4 chars of doc type suffix for the key
        type_suffix = doc_type[-4:].upper() if len(doc_type) >= 4 else doc_type.upper()
        month, year = get_month_year_from_date(doc_date)
        fy = get_financial_year(month, year) if month > 0 else 0

        key = f"{type_suffix}_{doc_no.upper()}_{fy}"

        if key in self._doc_keys:
            first_row = self._doc_keys[key]
            result.add_error(
                message=DUPLICATE_ERRORS["duplicate_document"].format(
                    row=row,
                    sheet=sheet,
                    doc_type=doc_type,
                    doc_no=doc_no,
                    first_row=first_row,
                ),
                sheet=sheet,
                row=row,
                field_name="Doc No",
                category="duplicate",
            )
            return True

        self._doc_keys[key] = row
        return False

    def check_brc(
        self,
        brc_no: str,
        row: int,
        sheet: str,
        result: ValidationResult,
    ) -> bool:
        """
        WHAT:
            Checks if this BRC/FIRC number has already been seen.

        WHY ADDED:
            Rebuild Brief Section 5: "Duplicate BRC Validation — ensure
            the tool throws an error if the user accidentally inputs the
            exact same BRC/FIRC number twice."

        CALLED BY:
            → core/validators/stmt02_validator.py
            → core/validators/stmt03_validator.py

        PARAMETERS:
            brc_no (str): The BRC/FIRC number.
            row (int): Excel row number.
            sheet (str): Sheet name.
            result (ValidationResult): Errors added here.

        RETURNS:
            bool: True if duplicate (error added), False if unique.
        """
        if not brc_no:
            return False

        key = brc_no.upper()

        if key in self._brc_keys:
            first_row = self._brc_keys[key]
            result.add_error(
                message=DUPLICATE_ERRORS["duplicate_brc"].format(
                    row=row,
                    sheet=sheet,
                    brc_no=brc_no,
                    first_row=first_row,
                ),
                sheet=sheet,
                row=row,
                field_name="BRC No",
                category="duplicate",
            )
            return True

        self._brc_keys[key] = row
        return False
