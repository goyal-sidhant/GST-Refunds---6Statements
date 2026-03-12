"""
FILE: config/error_messages.py

PURPOSE: All user-facing error and warning message templates in plain English.
         Messages are written for Article Assistants with no coding experience.
         Every message tells the user WHAT went wrong and HOW to fix it in
         their Excel file. Templates use {placeholders} for dynamic values.

CONTAINS:
- HEADER_ERRORS              — GSTIN, period, and order field errors
- TEMPLATE_ERRORS            — Column mismatch and sheet structure errors
- DOCUMENT_ERRORS            — Doc type, number, date, value errors
- TAX_ERRORS                 — Tax amount and rate-related errors
- SHIPPING_ERRORS            — Port code, shipping bill, EGM errors
- BRC_ERRORS                 — BRC/FIRC linking and field errors
- DUPLICATE_ERRORS           — Duplicate document and BRC errors
- DATE_ORDER_ERRORS          — Chronological date ordering errors
- SUPPLY_TYPE_ERRORS         — S01A inward/outward type-specific errors
- S06_ERRORS                 — S06-specific (POS, B2B/B2C, correction) errors
- WARNINGS                   — Non-blocking warnings (rate check, empty rows)

DEPENDS ON:
- Nothing (pure string templates)

USED BY:
- core/header_validator.py       → HEADER_ERRORS
- core/template_enforcer.py      → TEMPLATE_ERRORS
- core/field_validators.py       → DOCUMENT_ERRORS
- core/tax_validators.py         → TAX_ERRORS, WARNINGS
- core/duplicate_detector.py     → DUPLICATE_ERRORS
- core/date_validators.py        → DATE_ORDER_ERRORS
- core/brc_linker.py             → BRC_ERRORS
- core/validators/*.py           → statement-specific messages

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — all messages for 6 stmts  | Phase 0 infrastructure setup       |
"""


# ---------------------------------------------------------------------------
# Header / Envelope Errors
# ---------------------------------------------------------------------------

HEADER_ERRORS: dict[str, str] = {
    "gstin_empty": (
        "GSTIN is missing from the Header sheet. "
        "Please enter your 15-character GSTIN in cell B2."
    ),
    "gstin_invalid_format": (
        "GSTIN '{gstin}' does not match the expected format. "
        "A valid GSTIN is 15 characters: 2 digits (state code) + "
        "10 characters (PAN) + 1 entity number + 1 registration type + "
        "1 check digit. Please check for typos."
    ),
    "gstin_checksum_failed": (
        "GSTIN '{gstin}' has an invalid check digit. "
        "The last character should be '{expected}' but found '{actual}'. "
        "This usually means a typing error somewhere in the GSTIN. "
        "Please verify the GSTIN against your registration certificate."
    ),
    "from_period_empty": (
        "From Period is missing from the Header sheet. "
        "Please enter the starting period in MM-YYYY format (e.g., 04-2026) in cell B3."
    ),
    "to_period_empty": (
        "To Period is missing from the Header sheet. "
        "Please enter the ending period in MM-YYYY format (e.g., 06-2026) in cell B4."
    ),
    "period_invalid_format": (
        "'{value}' is not a valid period format. "
        "Please use MM-YYYY format (e.g., 04-2026 for April 2026). "
        "The month must be 01-12."
    ),
    "period_before_gst": (
        "Period '{value}' is before 01-07-2017 (GST inception date). "
        "GST refund claims cannot include periods before GST was introduced."
    ),
    "period_future": (
        "Period '{value}' is in the future. "
        "You cannot claim refunds for a period that has not yet ended."
    ),
    "to_before_from": (
        "To Period '{to_period}' is before From Period '{from_period}'. "
        "The ending period cannot be earlier than the starting period."
    ),
    "order_no_empty": (
        "Order Number is missing from the Header sheet. "
        "Please enter the ruling/order reference number in cell B3."
    ),
    "order_date_empty": (
        "Order Date is missing from the Header sheet. "
        "Please enter the order date in DD-MM-YYYY format in cell B4."
    ),
    "order_date_invalid": (
        "Order Date '{value}' is not a valid date. "
        "Please use DD-MM-YYYY format (e.g., 15-03-2026)."
    ),
}

# ---------------------------------------------------------------------------
# Template Structure Errors
# ---------------------------------------------------------------------------

TEMPLATE_ERRORS: dict[str, str] = {
    "wrong_extension": (
        "File '{filename}' is not an Excel file. "
        "Only .xlsx files are supported. Please save your file as .xlsx format."
    ),
    "file_not_found": (
        "File not found: '{filepath}'. "
        "Please check the file path and try again."
    ),
    "file_locked": (
        "Cannot open '{filename}' — it may be open in Excel. "
        "Please close the file in Excel and try again."
    ),
    "sheet_missing": (
        "Expected sheet '{sheet_name}' not found in the workbook. "
        "Your file has these sheets: {found_sheets}. "
        "Please use the correct template for Statement {stmt_type}."
    ),
    "header_sheet_missing": (
        "The 'Header' sheet is missing from your file. "
        "Please use the correct template which includes a Header sheet."
    ),
    "column_mismatch": (
        "Column mismatch on sheet '{sheet_name}'. "
        "Expected column {position} to be '{expected}' but found '{found}'. "
        "Please do not rename, reorder, or delete columns in the template."
    ),
    "column_missing": (
        "Sheet '{sheet_name}' is missing required column '{column_name}'. "
        "Expected {expected_count} columns but found {found_count}. "
        "Please use the original unmodified template."
    ),
    "empty_sheet": (
        "Sheet '{sheet_name}' has no data rows. "
        "Please enter at least one row of data before processing."
    ),
}

# ---------------------------------------------------------------------------
# Document Field Errors
# ---------------------------------------------------------------------------

DOCUMENT_ERRORS: dict[str, str] = {
    "doc_type_empty": (
        "Row {row}, {sheet} Sheet: Document Type is empty. "
        "Please select Invoice, Debit Note, or Credit Note from the dropdown."
    ),
    "doc_type_invalid": (
        "Row {row}, {sheet} Sheet: '{value}' is not a valid Document Type. "
        "Please select Invoice, Debit Note, or Credit Note from the dropdown."
    ),
    "doc_no_empty": (
        "Row {row}, {sheet} Sheet: Document Number is empty. "
        "Please enter the invoice/note number (up to 16 characters)."
    ),
    "doc_no_invalid": (
        "Row {row}, {sheet} Sheet: Document Number '{value}' contains invalid characters. "
        "Only letters, numbers, forward slash (/), and hyphen (-) are allowed, "
        "maximum 16 characters."
    ),
    "doc_date_empty": (
        "Row {row}, {sheet} Sheet: Document Date is empty. "
        "Please enter the date in DD-MM-YYYY format."
    ),
    "doc_date_invalid": (
        "Row {row}, {sheet} Sheet: '{value}' is not a valid date. "
        "Please use DD-MM-YYYY format (e.g., 15-03-2026)."
    ),
    "doc_date_before_gst": (
        "Row {row}, {sheet} Sheet: Document Date {value} is before 01-07-2017. "
        "GST documents cannot have a date before GST inception."
    ),
    "doc_date_future": (
        "Row {row}, {sheet} Sheet: Document Date {value} is in the future. "
        "Please enter a date on or before today."
    ),
    "doc_date_after_period": (
        "Row {row}, {sheet} Sheet: Document Date {value} is after the To Period. "
        "The document date must fall within the return period range."
    ),
    "doc_value_empty": (
        "Row {row}, {sheet} Sheet: Document Value is empty. "
        "Please enter the total invoice/note value."
    ),
    "doc_value_invalid": (
        "Row {row}, {sheet} Sheet: Document Value '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 2 decimal places."
    ),
}

# ---------------------------------------------------------------------------
# Tax Amount Errors
# ---------------------------------------------------------------------------

TAX_ERRORS: dict[str, str] = {
    "taxable_value_empty": (
        "Row {row}, {sheet} Sheet: Taxable Value is empty. "
        "Please enter the taxable value of the supply."
    ),
    "taxable_value_invalid": (
        "Row {row}, {sheet} Sheet: Taxable Value '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 2 decimal places."
    ),
    "igst_exceeds_taxable": (
        "Row {row}, {sheet} Sheet: IGST amount ({igst}) exceeds "
        "the Taxable Value ({taxable}). IGST cannot be more than the taxable value."
    ),
    "doc_value_less_than_sum": (
        "Row {row}, {sheet} Sheet: Document Value ({doc_value}) is less than "
        "Taxable Value + IGST + Cess ({total}). "
        "The total invoice value must be at least the sum of these amounts."
    ),
    "tax_mutual_exclusivity": (
        "Row {row}, {sheet} Sheet: You have entered both IGST and CGST/SGST. "
        "For this supply type, you must enter EITHER IGST alone "
        "OR both CGST and SGST together — not all three. "
        "Please clear the incorrect tax column(s) in your Excel file."
    ),
    "cgst_sgst_must_pair": (
        "Row {row}, {sheet} Sheet: CGST and SGST must be entered together. "
        "You have entered {present} but not {missing}. "
        "Please enter both CGST and SGST, or clear both and use IGST instead."
    ),
    "no_tax_entered": (
        "Row {row}, {sheet} Sheet: No tax amount entered. "
        "Please enter either IGST, or both CGST and SGST."
    ),
    "igst_not_allowed": (
        "Row {row}, {sheet} Sheet: IGST is not allowed for this supply type. "
        "Please clear the IGST column and enter CGST + SGST instead."
    ),
    "cgst_sgst_not_allowed": (
        "Row {row}, {sheet} Sheet: CGST/SGST are not allowed for this supply type. "
        "Please clear the CGST and SGST columns and enter IGST only."
    ),
    "igst_empty": (
        "Row {row}, {sheet} Sheet: IGST amount is empty. "
        "IGST is mandatory for this statement type. Please enter the IGST amount paid."
    ),
    "igst_invalid": (
        "Row {row}, {sheet} Sheet: IGST amount '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 2 decimal places."
    ),
    "cess_invalid": (
        "Row {row}, {sheet} Sheet: Cess amount '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 2 decimal places."
    ),
    "tax_sum_exceeds_taxable": (
        "Row {row}, {sheet} Sheet: Total tax ({tax_sum}) exceeds "
        "the Taxable Value ({taxable}). "
        "The sum of IGST + CGST + SGST cannot exceed the taxable value."
    ),
}

# ---------------------------------------------------------------------------
# Shipping / Port / EGM Errors
# ---------------------------------------------------------------------------

SHIPPING_ERRORS: dict[str, str] = {
    "port_code_empty": (
        "Row {row}, {sheet} Sheet: Port Code is empty. "
        "Port Code is mandatory for goods exports. "
        "Please enter the 6-character port code (e.g., INBOM4)."
    ),
    "port_code_invalid": (
        "Row {row}, {sheet} Sheet: Port Code '{value}' is not valid. "
        "Must be exactly 6 alphanumeric characters (e.g., INBOM4)."
    ),
    "port_code_not_allowed": (
        "Row {row}, {sheet} Sheet: Port Code should be blank for this supply type. "
        "Port Code is only required for 'Import of Goods/Supplies from SEZ to DTA'. "
        "Please clear the Port Code cell."
    ),
    "shipping_bill_empty": (
        "Row {row}, {sheet} Sheet: Shipping Bill Number is empty. "
        "Shipping Bill is mandatory for goods exports. "
        "Please enter the 3-7 digit shipping bill number."
    ),
    "shipping_bill_invalid": (
        "Row {row}, {sheet} Sheet: Shipping Bill Number '{value}' is not valid. "
        "Must be 3-7 digits only (no letters). Example: 1234567."
    ),
    "shipping_bill_date_empty": (
        "Row {row}, {sheet} Sheet: Shipping Bill Date is empty. "
        "Please enter the shipping bill date in DD-MM-YYYY format."
    ),
    "shipping_bill_date_invalid": (
        "Row {row}, {sheet} Sheet: Shipping Bill Date '{value}' is not valid. "
        "Please use DD-MM-YYYY format."
    ),
    "shipping_bill_date_future": (
        "Row {row}, {sheet} Sheet: Shipping Bill Date {value} is in the future. "
        "Please enter a date on or before today."
    ),
    "fob_value_empty": (
        "Row {row}, {sheet} Sheet: FOB Value is empty. "
        "Free On Board value is mandatory for goods exports."
    ),
    "fob_value_invalid": (
        "Row {row}, {sheet} Sheet: FOB Value '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 4 decimal places."
    ),
    "egm_ref_empty": (
        "Row {row}, {sheet} Sheet: EGM Reference Number is empty. "
        "Please enter the Export General Manifest reference (1-20 characters)."
    ),
    "egm_ref_invalid": (
        "Row {row}, {sheet} Sheet: EGM Reference '{value}' is not valid. "
        "Must be 1-20 alphanumeric characters. "
        "Backslash (\\) and double quotes (\") are not allowed."
    ),
    "egm_date_empty": (
        "Row {row}, {sheet} Sheet: EGM Date is empty. "
        "Please enter the EGM date in DD-MM-YYYY format."
    ),
    "egm_date_invalid": (
        "Row {row}, {sheet} Sheet: EGM Date '{value}' is not valid. "
        "Please use DD-MM-YYYY format."
    ),
    "sb_endorsed_invalid": (
        "Row {row}, {sheet} Sheet: SB/Endorsed Invoice Number '{value}' is not valid. "
        "Must contain only letters, numbers, forward slash (/), and hyphen (-)."
    ),
    "sb_date_required": (
        "Row {row}, {sheet} Sheet: You entered an SB/Endorsed Invoice Number "
        "but the Date is missing. Please enter the date or remove the number."
    ),
}

# ---------------------------------------------------------------------------
# BRC / FIRC Errors
# ---------------------------------------------------------------------------

BRC_ERRORS: dict[str, str] = {
    "brc_incomplete": (
        "Row {row}, {sheet} Sheet: BRC/FIRC details are incomplete. "
        "If you enter any BRC/FIRC field (Number, Date, or Value), "
        "all three must be filled. Please complete or clear all BRC fields."
    ),
    "brc_no_invalid": (
        "Row {row}, {sheet} Sheet: BRC/FIRC Number '{value}' is not valid. "
        "Must be 2-30 alphanumeric characters."
    ),
    "brc_no_zero": (
        "Row {row}, {sheet} Sheet: BRC/FIRC Number cannot be '0'. "
        "Please enter the actual BRC/FIRC number."
    ),
    "brc_date_invalid": (
        "Row {row}, {sheet} Sheet: BRC/FIRC Date '{value}' is not valid. "
        "Please use DD-MM-YYYY format."
    ),
    "brc_date_future": (
        "Row {row}, {sheet} Sheet: BRC/FIRC Date {value} is in the future. "
        "Please enter a date on or before today."
    ),
    "brc_value_invalid": (
        "Row {row}, {sheet} Sheet: BRC/FIRC Value '{value}' is not valid. "
        "Must be a non-negative number with up to 15 digits and 2 decimal places."
    ),
    "brc_coverage_missing": (
        "{sheet} Sheet: The following service invoice(s) are not covered by any "
        "BRC/FIRC: {rows}. Every service export invoice must be linked to a "
        "BRC/FIRC. Please add BRC details or use the BRC Group ID column."
    ),
    "group_id_missing": (
        "Row {row}, {sheet} Sheet: BRC Group ID is required in Group ID linking mode. "
        "Every invoice must have either a BRC entry or a Group ID. "
        "Please enter a Group ID or switch to Adjacent linking mode."
    ),
    "group_id_no_brc": (
        "{sheet} Sheet: BRC Group ID '{group_id}' has no corresponding BRC/FIRC entry. "
        "Every group must contain at least one row with BRC details. "
        "Please add BRC data to one of the rows in group '{group_id}'."
    ),
}

# ---------------------------------------------------------------------------
# Duplicate Errors
# ---------------------------------------------------------------------------

DUPLICATE_ERRORS: dict[str, str] = {
    "duplicate_document": (
        "Row {row}, {sheet} Sheet: Duplicate document — "
        "{doc_type} '{doc_no}' already appears in Row {first_row}. "
        "Each document number must be unique within the same financial year. "
        "Please check for accidental duplicate entries."
    ),
    "duplicate_brc": (
        "Row {row}, {sheet} Sheet: Duplicate BRC/FIRC Number '{brc_no}' — "
        "this number already appears in Row {first_row}. "
        "Each BRC/FIRC number should be used only once. "
        "Please check for accidental duplicate entries."
    ),
}

# ---------------------------------------------------------------------------
# Chronological Date Order Errors
# ---------------------------------------------------------------------------

DATE_ORDER_ERRORS: dict[str, str] = {
    "sb_before_invoice": (
        "Row {row}, {sheet} Sheet: Shipping Bill Date ({sb_date}) is before "
        "the Invoice Date ({inv_date}). A shipping bill is normally issued "
        "on or after the invoice date. Please verify both dates."
    ),
    "egm_before_sb": (
        "Row {row}, {sheet} Sheet: EGM Date ({egm_date}) is before "
        "the Shipping Bill Date ({sb_date}). The Export General Manifest "
        "is filed after the shipping bill. Please verify both dates."
    ),
}

# ---------------------------------------------------------------------------
# S01A Supply Type Errors
# ---------------------------------------------------------------------------

SUPPLY_TYPE_ERRORS: dict[str, str] = {
    "inward_type_empty": (
        "Row {row}, Inward Sheet: Inward Supply Type is empty. "
        "Please select a type from the dropdown."
    ),
    "inward_type_invalid": (
        "Row {row}, Inward Sheet: '{value}' is not a valid Inward Supply Type. "
        "Please select from the dropdown list."
    ),
    "outward_type_empty": (
        "Row {row}, Outward Sheet: Outward Supply Type is empty. "
        "Please select B2B, B2C-Large, or B2C-Small from the dropdown."
    ),
    "outward_type_invalid": (
        "Row {row}, Outward Sheet: '{value}' is not a valid Outward Supply Type. "
        "Please select B2B, B2C-Large, or B2C-Small from the dropdown."
    ),
    "supplier_gstin_empty": (
        "Row {row}, Inward Sheet: Supplier GSTIN is required for "
        "'{supply_type}'. Please enter the supplier's 15-character GSTIN."
    ),
    "supplier_gstin_same_as_self": (
        "Row {row}, Inward Sheet: Supplier GSTIN '{gstin}' is the same as "
        "your own GSTIN. For '{supply_type}', the supplier must be a "
        "different registered person. Please correct the GSTIN."
    ),
    "b2c_small_doc_not_blank": (
        "Row {row}, Outward Sheet: For B2C-Small, leave Document Number and "
        "Document Date blank. The app will auto-fill these with the "
        "government-mandated values."
    ),
}

# ---------------------------------------------------------------------------
# S04 Recipient GSTIN Errors
# ---------------------------------------------------------------------------

RECIPIENT_ERRORS: dict[str, str] = {
    "recipient_gstin_empty": (
        "Row {row}, {sheet} Sheet: Recipient GSTIN is empty. "
        "Please enter the SEZ unit/developer's 15-character GSTIN."
    ),
    "recipient_gstin_same_as_self": (
        "Row {row}, {sheet} Sheet: Recipient GSTIN '{gstin}' is the same as "
        "your own GSTIN. The recipient must be a different person. "
        "Please correct the GSTIN."
    ),
}

# ---------------------------------------------------------------------------
# S06 Specific Errors
# ---------------------------------------------------------------------------

S06_ERRORS: dict[str, str] = {
    "pos_empty": (
        "Row {row}, {sheet} Sheet: Place of Supply is empty. "
        "Please select a state/UT from the dropdown (e.g., '19-West Bengal')."
    ),
    "pos_invalid": (
        "Row {row}, {sheet} Sheet: '{value}' is not a valid Place of Supply. "
        "Please select from the dropdown list of 38 states/UTs."
    ),
    "no_recipient_identity": (
        "Row {row}, {sheet} Sheet: Neither Recipient GSTIN nor Recipient Name "
        "is provided. Please enter at least one — GSTIN for B2B supplies, "
        "or Name for B2C supplies."
    ),
    "b2c_name_empty": (
        "Row {row}, {sheet} Sheet: Recipient Name is required for B2C supplies "
        "(when GSTIN is blank). Please enter the recipient's name."
    ),
}

# ---------------------------------------------------------------------------
# Warnings (non-blocking — JSON generation still proceeds)
# ---------------------------------------------------------------------------

WARNINGS: dict[str, str] = {
    "implicit_rate_mismatch": (
        "Row {row}, {sheet} Sheet: The implied tax rate is {implied_rate:.2f}% "
        "(Tax {tax_amount} on Taxable Value {taxable_value}). "
        "This does not match any standard GST slab ({nearest_slab}% is closest). "
        "Please verify the tax amount is correct."
    ),
    "empty_row_skipped": (
        "{sheet} Sheet: Row {row} is completely empty and was skipped."
    ),
    "empty_rows_summary": (
        "{sheet} Sheet: {count} empty row(s) were skipped: {rows}."
    ),
}
