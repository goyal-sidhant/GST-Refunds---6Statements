"""
FILE: models/data_row.py

PURPOSE: Defines the DataRow dataclass that holds one row of data from a
         data sheet. This is a generic container — the values are stored
         as a dict keyed by column header name. Statement-specific
         validators interpret these values according to their rules.

CONTAINS:
- DataRow  — One row of data with its sheet name and Excel row number

DEPENDS ON:
- Nothing (pure data structure)

USED BY:
- readers/template_reader.py  → creates DataRow objects from Excel rows
- core/validators/*.py        → reads field values for validation
- core/generators/*.py        → reads field values for JSON generation

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — data row model            | Phase 0 infrastructure setup       |
"""

from dataclasses import dataclass, field


@dataclass
class DataRow:
    """
    WHAT: Holds one row of data read from a data sheet.

    WHY ADDED:
        Rather than creating separate dataclasses for each of the 6
        statement types (which would mean ~15 different row classes),
        we use a generic dict-based container. The column header is the
        key, and the raw cell value is the value. Validators and
        generators access fields by header name via get_value().

    PARAMETERS:
        sheet_name (str):     Name of the sheet this row came from.
        excel_row (int):      The 1-based Excel row number (for error messages).
        values (dict):        Maps column header → raw cell value.
                              Values are whatever openpyxl returns: str, int,
                              float, datetime, or None for empty cells.
    """
    sheet_name: str
    excel_row: int
    values: dict[str, object] = field(default_factory=dict)

    def get_value(self, column_header: str) -> object:
        """
        WHAT: Returns the raw value for the given column, or None if missing.
        CALLED BY: All validators and generators that need a specific field.
        RETURNS: The raw cell value, or None.
        """
        return self.values.get(column_header)

    def get_str(self, column_header: str) -> str:
        """
        WHAT: Returns the value as a stripped string, or empty string if None.
        CALLED BY: Validators that need string-type fields (doc no, GSTIN, etc).
        RETURNS: Cleaned string value.
        """
        raw = self.values.get(column_header)
        if raw is None:
            return ""
        return str(raw).strip()

    def is_empty(self) -> bool:
        """
        WHAT: Returns True if ALL values in this row are None or blank strings.
        CALLED BY: readers/template_reader.py → skip empty rows with warning.
        RETURNS: True if the row has no meaningful data.
        """
        for value in self.values.values():
            if value is not None and str(value).strip() != "":
                return False
        return True
