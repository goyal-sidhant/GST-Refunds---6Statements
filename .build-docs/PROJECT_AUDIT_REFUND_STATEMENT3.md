# PROJECT AUDIT: GST Refund Statement 3 Generator

**Audit Date:** 2026-03-06
**Auditor:** Claude Opus 4.6 (Project Archaeology v2.0)
**Project Root:** `Refund-Statement3/`
**Additional Context:** HANDOVER.md (Feb 21, 2026), FILE_INDEX.md (Feb 21, 2026)

---

## SECTION 1: EXECUTIVE SUMMARY

This tool generates JSON files for GST Refund Statement 3 (EXPWOP — Export Without Payment of Tax) filings on the Indian GST portal. It replaces the government's clunky VBA-based `.xlsb` tool with a more reliable, automated Python solution. It takes export invoice data from Excel (.xlsx), government binary Excel (.xlsb), or CSV files, validates every field against the exact rules from the government's own VBA tool, and produces a JSON file in the precise format the GST portal expects for upload. It is built for Sidhant's GST consultancy practice — he handles complex compliance for exporter clients, including services companies that need EXPWOP refunds. The core technology stack is Python, using pandas for file reading, openpyxl for Excel template generation, pyxlsb for reading government .xlsb files, and tkinter for native file picker dialogs (no web framework or complex UI). The project appears **complete and production-ready** — it has been tested against Sidhant's real .xlsb file (149 entries matched the expected output). There are dead-code remnants (defined but never-called functions and error messages) representing features planned but not yet wired up, and future features like GUI interface, PDF generation, and batch processing are documented as "NOT STARTED" in the HANDOVER.

---

## SECTION 2: PROJECT STRUCTURE MAP

```
Refund-Statement3/
├── .git/                              [TOOLING] Git repository metadata
├── .gitignore                         [CONFIG]  Ignores __pycache__, venv, IDE, *.json, temp Excel files
├── README.md                          [DOCS]    Comprehensive usage guide and format documentation
├── HANDOVER.md                        [DOCS]    Development context handover (untracked, added post-git)
├── FILE_INDEX.md                      [DOCS]    File-by-file behavior descriptions (untracked, added post-git)
├── config.py                          [CORE]    All constants, regex patterns, column mappings, error messages
├── create_template.py                 [UTIL]    Standalone tool to generate a blank Excel input template
├── main.py                            [CORE]    Entry point — CLI parsing, orchestration of read→validate→generate
│
├── models/                            [CORE]    Data classes (Python dataclasses)
│   ├── __init__.py                              Re-exports Header, GoodsEntry, ServicesEntry, ValidationError/Result
│   ├── header.py                                Header dataclass (GSTIN, periods)
│   ├── goods_entry.py                           GoodsEntry dataclass (document + shipping bill + EGM + BRC)
│   ├── services_entry.py                        ServicesEntry dataclass (document + BRC, no shipping/EGM)
│   └── validation_error.py                      ValidationError, ValidationResult, ErrorSeverity, ErrorCategory
│
├── readers/                           [CORE]    File input parsers
│   ├── __init__.py                              Re-exports ExcelReader, CSVReader, XLSBReader
│   ├── excel_reader.py                          Reads .xlsx files (3 sheets: Header, Goods, Services)
│   ├── xlsb_reader.py                           Reads government .xlsb format (single sheet, fixed layout)
│   └── csv_reader.py                            Reads CSV files (3 files in a directory)
│
├── validators/                        [CORE]    Validation logic
│   ├── __init__.py                              Re-exports all validator functions
│   ├── header_validator.py                      GSTIN and return period validation
│   ├── goods_validator.py                       Goods-specific validation (shipping bill, EGM, port code)
│   ├── services_validator.py                    Services-specific validation (BRC handling)
│   └── document_validator.py                    Shared validation (doc type/no/date/value, BRC details)
│
├── generators/                        [CORE]    JSON output
│   ├── __init__.py                              Re-exports JSONGenerator
│   └── json_generator.py                        Produces the final Statement 3 JSON structure
│
└── utils/                             [UTIL]    Helper functions
    ├── __init__.py                              Re-exports all utility functions
    ├── date_utils.py                            Date parsing, period conversion, Excel date handling
    └── number_utils.py                          Decimal parsing, value validation, GSTIN checksum
```

**Entry Point:** `main.py` — run with `python main.py` (or `python main.py input.xlsx`).
**Secondary Entry Point:** `create_template.py` — run standalone to generate a blank Excel input template.

### Files Removed from Distribution (Per HANDOVER.md Section 8)

| File | Reason |
|------|--------|
| `test_basic.py` | Development test file, removed from distribution zip |
| `test_comparison.py` | Development test file, removed from distribution zip |
| `test_xlsb.py` | Development test file, removed from distribution zip |
| `__pycache__/` | Auto-generated bytecode |

> Sidhant asked "Why are there test files?" and they were removed. No test suite currently exists in the project.

### Dead Code Inventory

**Dead Utility Functions** (defined and re-exported in `__init__.py` but never called by any other code):

| Function | File | Line |
|----------|------|------|
| `is_date_valid_format()` | `utils/date_utils.py` | 110 |
| `is_date_within_period()` | `utils/date_utils.py` | 159 |
| `format_date_for_json()` | `utils/date_utils.py` | 206 |
| `is_zero()` | `utils/number_utils.py` | 104 |
| `get_mantissa_decimal_lengths()` | `utils/number_utils.py` | 121 |
| `format_value_for_json()` | `utils/number_utils.py` | 146 |
| `clean_numeric_string()` | `utils/number_utils.py` | 166 |

**Dead Model Methods** (defined but never called):

| Method | File | Line |
|--------|------|------|
| `Header.to_json_dict()` | `models/header.py` | 37 |
| `ValidationError.to_dict()` | `models/validation_error.py` | 53 |

**Dead Error Messages** (defined in `config.py` ERROR_MESSAGES but never referenced by any validator):

| Key | Line | Message |
|-----|------|---------|
| `services_shipping_present` | 206 | "Shipping Bill details should not be entered for Services" |
| `group_id_missing` | 214 | "BRC Group ID is required when using Group ID linking mode" |
| `group_id_no_brc` | 215 | "BRC Group ID {group_id} has no corresponding BRC/FIRC entry" |
| `duplicate_brc` | 211 | "Duplicate BRC/FIRC Number: {brc_no} already exists in Row {row}" |

**Dead Enum Members** (defined but never used anywhere):

| Member | File | Line |
|--------|------|------|
| `ErrorCategory.DUPLICATE` | `models/validation_error.py` | 21 |
| `ErrorCategory.LINKING` | `models/validation_error.py` | 22 |

**Unused Import:**

| Import | File | Line |
|--------|------|------|
| `excel_date_to_string` | `readers/csv_reader.py` | 22 |

> CSVReader imports `excel_date_to_string` but never calls it — CSV dates are plain strings, not Excel date objects.

---

## SECTION 3: FEATURE INVENTORY

### F1: Excel File Input (.xlsx)

- **What it does:** Reads an Excel workbook with three sheets (Header, Goods, Services) and converts them into internal data structures.
- **Where it lives:** `readers/excel_reader.py` (class `ExcelReader`)
- **Input → Output:** `.xlsx` file → `Header` object + lists of `GoodsEntry` and `ServicesEntry`
- **User interaction:** Pass file path as argument or select via file picker dialog
- **Concrete trace:** User provides an Excel file with a "Header" sheet containing `GSTIN=19AAECM7422R1ZS`, `From Period=012025`, `To Period=032025`, and a "Goods" sheet with one row: `Invoice, EXP/001, 01-12-2024, 100000, INBOM4, 1234567, 05-12-2024, 95000.50, EGM2024001, 06-12-2024`.
  1. `ExcelReader.read()` opens the file with `pd.ExcelFile`.
  2. `_find_sheet()` searches sheet names case-insensitively for "header", "goods", "services".
  3. For the Header sheet, `_read_header_sheet()` iterates rows looking for key-value pairs, matching field names against `HEADER_COLUMNS` config (e.g., "GSTIN" matches `gstin`).
  4. For the Goods sheet, `_find_header_row()` searches the first 10 rows for a row where at least 3 cell values match known column names. Then `_create_column_map()` maps internal names (like `doc_type`) to column indices.
  5. Each data row after the header becomes a `GoodsEntry` via `_create_goods_entry()`, which calls `_get_cell_value()`, `_get_date_value()`, and `_get_decimal_value()` for each field.
  6. Output: `reader.header = Header(gstin='19AAECM7422R1ZS', from_period='012025', to_period='032025')`, `reader.goods_entries = [GoodsEntry(source_row=2, doc_type='Invoice', doc_no='EXP/001', ...)]`.

### F2: Government .xlsb File Input

- **What it does:** Reads the government-provided GST_REFUND_S03.xlsb file, which has a single sheet with fixed row/column positions for header data and a mixed Goods+Services data table.
- **Where it lives:** `readers/xlsb_reader.py` (class `XLSBReader`)
- **Input → Output:** `.xlsb` file → `Header` + `GoodsEntry[]` + `ServicesEntry[]`
- **User interaction:** Same as F1 — pass as argument or file picker
- **Concrete trace:** User provides the government `.xlsb` file (tested with `GST_REFUND_S03MultipleBRC.xlsb` per HANDOVER.md Section 13: GSTIN 19AAECM7422R1ZS, period 012025-032025, 141 services entries + 8 BRC entries).
  1. `XLSBReader.read()` opens with `pd.read_excel(engine='pyxlsb', sheet_name='RFD_STMT03')`.
  2. Header data extracted from fixed positions: GSTIN at row 5 column 3, periods at rows 6-7 column 3.
  3. `_format_period()` handles leading zero loss: `.xlsb` stores `012025` as `12025` → padded to `012025` via `str().zfill(6)`.
  4. Data rows start at row 12 (0-indexed). Column 5 indicates 'G' (goods) or 'S' (services).
  5. `_get_non_disabled_value()` returns `None` for "DISABLED" cells (government tool writes "DISABLED" in shipping bill columns for services rows).
  6. `_format_date()` handles both string dates and Excel serial numbers using `datetime(1899, 12, 30)` epoch.
  7. In the real test: 141 services entries + 8 BRC entries → 149 total JSON entries matched expected output.

### F3: CSV File Input

- **What it does:** Reads three separate CSV files (header.csv, goods.csv, services.csv) from a directory.
- **Where it lives:** `readers/csv_reader.py` (class `CSVReader`)
- **Input → Output:** Directory path → `Header` + `GoodsEntry[]` + `ServicesEntry[]`
- **User interaction:** `--csv-dir ./data` argument or folder picker dialog
- **Design rationale (from HANDOVER Decision 2):** CSV format enables automation pipelines for clients who generate data programmatically.
- **Concrete trace:** User provides a directory containing `header.csv` and `services.csv`.
  1. `CSVReader.read()` constructs paths from `directory / 'header.csv'`, etc.
  2. Header CSV read as key-value pairs (column 0 = field name, column 1 = value). Encoding: `utf-8-sig` (handles BOM from Windows Excel exports).
  3. Goods CSV: first row = headers, mapped via `_create_column_map()`. Data rows from index 1. Empty rows skipped.
  4. If goods.csv doesn't exist, `self.goods_entries` stays empty (no error).
  5. Output: Only services entries populated, goods entries remain `[]`.

### F4: Comprehensive Validation

- **What it does:** Validates every field against the exact rules from the government's VBA validation tool. Produces a structured error report. All errors collected before any are shown — users fix everything in one pass (HANDOVER Decision 3).
- **Where it lives:** `validators/header_validator.py`, `validators/goods_validator.py`, `validators/services_validator.py`, `validators/document_validator.py`
- **Input → Output:** Data objects → `ValidationResult` containing all errors
- **User interaction:** Automatic after file read; can be used standalone with `--validate-only`
- **Concrete trace:** Input has GSTIN `19AAECM7422R1ZN` (invalid checksum) and one goods entry with doc_date `25-12-2030` (future date).
  1. `validate_header()` calls `validate_gstin()`:
     - Not empty ✓. `GSTIN_PATTERN` matches ✓. `validate_gstin_checksum('19AAECM7422R1ZN')` → computes weighted sum, expected checksum doesn't match 'N' → error "GSTIN checksum validation failed".
  2. `validate_goods_entries()` calls `validate_single_goods_entry()`:
     - `validate_doc_date('25-12-2030', ...)`:
       - `DATE_PATTERN` matches ✓. `parse_date_ddmmyyyy()` → `date(2030, 12, 25)` ✓. `is_before_gst_inception()` → False ✓. `is_future_date()` → True (Dec 2030 > March 2026) → error "Document Date cannot be a future date".
  3. `result.generate_report()` produces formatted output with HEADER ERRORS and GOODS SHEET ERRORS sections, plus SUMMARY line.

### F5: JSON Generation (Statement 3 Format)

- **What it does:** Converts validated data into the exact JSON structure required by the GST portal for Statement 3 uploads. Document and BRC entries share the same `sno` when linked.
- **Where it lives:** `generators/json_generator.py` (class `JSONGenerator`)
- **Input → Output:** Header + GoodsEntries + ServicesEntries → JSON file
- **User interaction:** Automatic after validation passes; output path via `-o` flag or "Save As" dialog
- **JSON structure (from HANDOVER Section 5):**
  ```json
  {
    "gstin": "19AAECM7422R1ZS",
    "fromFp": "012025",
    "toFp": "032025",
    "refundRsn": "EXPWOP",
    "version": "3.0",
    "stmt03": [
      {"sno": 1, "docType": "Invoice", "inum": "SVC/001", "idt": "15-12-2024", "val": 500000, "type": "S"},
      {"sno": 1, "brcfircnum": "FIRC2024001", "brcfircdt": "25-12-2024", "brcfircval": 750000}
    ]
  }
  ```
- **Concrete trace:** 2 goods entries (one with BRC) + 2 services entries in adjacent mode.
  1. `generate()` starts with `current_sno = 0`.
  2. Goods entry 1 (no BRC): `current_sno=1`, adds doc JSON `{'sno': 1, 'type': 'G', ...}`.
  3. Goods entry 2 (with BRC): `current_sno=2`, adds doc JSON + BRC JSON both with `sno=2`.
  4. Services via `_process_services_adjacent(start_sno=2)`: increments from sno=3.
  5. Final JSON wraps everything with header fields and `stmt03` array.

### F6: BRC Linking — Adjacent Mode (Default)

- **What it does:** Links BRC/FIRC payment records to invoices based on row position. A BRC on a row covers all invoices above it until the previous BRC. This matches how the government tool works (HANDOVER Decision 1).
- **Where it lives:** `generators/json_generator.py`, method `_process_services_adjacent()`
- **Design rationale (from HANDOVER):** This mode was implemented because it mirrors the government tool's behavior. Sidhant also wanted a "leak-proof" alternative (Group ID mode), stating "Option B is leak-proof."
- **Concrete trace:** 3 services entries: SVC/001 (no BRC), SVC/002 (no BRC), SVC/003 (with BRC ₹15L).
  1. SVC/001: `sno=1`, doc JSON added, no BRC.
  2. SVC/002: `sno=2`, doc JSON added, no BRC.
  3. SVC/003: `sno=3`, doc JSON added, BRC JSON added with `sno=3`.
  4. The BRC with `sno=3` is associated with the last document. The GST portal interprets this as covering preceding un-BRC'd invoices.

### F7: BRC Linking — Group ID Mode

- **What it does:** Explicitly links invoices to their BRC using a `brc_group_id` column, allowing non-adjacent grouping. Sidhant called this "leak-proof" (HANDOVER Decision 1).
- **Where it lives:** `generators/json_generator.py`, method `_process_services_group_id()`
- **Input → Output:** ServicesEntry list with group IDs → stmt03 JSON with grouped BRC
- **Concrete trace:** 4 entries: SVC/001 (group=GRP1, no BRC), SVC/002 (group=GRP1, BRC=FIRC001), SVC/003 (group=GRP2, no BRC), SVC/004 (group=GRP2, BRC=FIRC002).
  1. First pass: assigns `sno`, collects `group_to_entries` and `group_brc_info`.
  2. Second pass: outputs doc JSONs; when entry is LAST in its group, outputs group's BRC JSON with that entry's sno.
  3. Result: doc(sno=1), doc(sno=2), BRC(sno=2, FIRC001), doc(sno=3), doc(sno=4), BRC(sno=4, FIRC002).

### F8: Excel Template Generator

- **What it does:** Creates a formatted Excel template (.xlsx) with Header, Goods, Services, and Instructions sheets, pre-styled with headers, borders, and sample data. Instructions were moved to a separate sheet per Sidhant's request (HANDOVER Decision 7).
- **Where it lives:** `create_template.py` (function `create_template()`)
- **Input → Output:** Nothing → `.xlsx` file with 4 sheets
- **User interaction:** Run `python create_template.py`, select save location via dialog

### F9: Interactive File Picker

- **What it does:** When no arguments are provided, shows a menu letting the user choose Excel file or CSV folder, then opens native OS file/folder picker dialogs. Added because Sidhant requested GUI file selection when running without arguments (HANDOVER Decision 6).
- **Where it lives:** `main.py`, functions `open_file_dialog()`, `open_folder_dialog()`, `save_file_dialog()`
- **User interaction:** Run `python main.py` with no arguments

---

## SECTION 4: DATA FLOW

```
USER INPUT
    │
    ├─ Excel (.xlsx) ──→ ExcelReader.read() ──→ pandas.read_excel() ──→ DataFrame
    │                                                                      │
    ├─ Govt (.xlsb)  ──→ XLSBReader.read() ──→ pandas.read_excel(        │
    │                         engine='pyxlsb') ──→ DataFrame              │
    │                                                                      │
    └─ CSV files     ──→ CSVReader.read() ──→ csv.reader() ──→ Lists      │
                                                                           │
                                                                           ▼
                                                               ┌─────────────────────┐
                                                               │   DATA STRUCTURES    │
                                                               │  Header object       │
                                                               │  GoodsEntry[]        │
                                                               │  ServicesEntry[]     │
                                                               └──────────┬──────────┘
                                                                          │
                                                                          ▼
                                                               ┌─────────────────────┐
                                                               │    VALIDATION        │
                                                               │  validate_header()   │
                                                               │  validate_goods()    │
                                                               │  validate_services() │
                                                               └──────────┬──────────┘
                                                                          │
                                                         ┌────────────────┴────────────────┐
                                                         │                                 │
                                                    Has Errors?                      No Errors
                                                         │                                 │
                                                         ▼                                 ▼
                                               ┌──────────────────┐             ┌──────────────────┐
                                               │  Error Report     │             │  JSONGenerator    │
                                               │  (printed to      │             │  .generate()      │
                                               │   console, exit 1)│             │  .save_to_file()  │
                                               └──────────────────┘             └────────┬─────────┘
                                                                                         │
                                                                                         ▼
                                                                              ┌──────────────────┐
                                                                              │  Statement_3.json │
                                                                              │  (GST portal      │
                                                                              │   upload format)   │
                                                                              └──────────────────┘
```

**Data transformations at each step:**

1. **File Read** → Strings/numbers in cells are converted to Python types. Dates are converted from Excel serial numbers to `dd-mm-yyyy` strings. Values are converted to `Decimal` objects. All string fields are stripped and cleaned in `__post_init__`.

2. **Validation** → Data is checked against regex patterns and business rules. No data modification occurs — validation is read-only. A `ValidationResult` accumulates all errors.

3. **JSON Generation** → `Decimal` values are converted to `float` via `float()`. Date strings pass through as-is (already in `dd-mm-yyyy`). Serial numbers (`sno`) are assigned sequentially. The BRC linking logic determines which BRC entries to output and what `sno` they share with documents.

---

## SECTION 5: BUSINESS RULES AND DOMAIN LOGIC

### 5.1 GSTIN Validation

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| GSTIN is mandatory | `if not gstin:` → error | `validators/header_validator.py:46-48` |
| GSTIN pattern: 2 digits + 5 letters + 4 digits + 1 letter + [1-9A-Z] + [Z1-9A-J] + [0-9A-Z] | `GSTIN_PATTERN.match()` | `config.py:19`, `validators/header_validator.py:54` |
| GSTIN checksum: weighted sum of first 14 chars, mod 36, must match 15th char | `validate_gstin_checksum()` | `utils/number_utils.py:186-234` |
| Checksum algorithm: even positions ×1, odd positions ×2, each result → quotient + remainder ÷ 36, sum, checksum = (36 - sum%36) % 36 | See implementation | `utils/number_utils.py:218-232` |

> **HANDOVER confirms:** "Tested with user's sample data, passed" (Section 4, Open Assumptions).

### 5.2 Return Period Validation

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| Both From and To periods are mandatory | Empty check | `validators/header_validator.py:134-136` |
| Format: MMYYYY (6 digits, MM = 01-12) | `RETURN_PERIOD_PATTERN.match()` + month range check | `config.py:22`, `validators/header_validator.py:141,154` |
| Cannot be before July 2017 (GST inception) | `period_date < GST_INCEPTION_DATE` | `config.py:12`, `validators/header_validator.py:159-162` |
| Cannot be in the future | `period_date > date.today()` | `validators/header_validator.py:165-168` |
| To Period cannot be before From Period | `to_date < from_date` (end-of-month for To, start-of-month for From) | `validators/header_validator.py:98-106` |

### 5.3 Document Validation (Shared by Goods and Services)

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| Doc Type must be "Invoice", "Credit Note", or "Debit Note" | `doc_type not in VALID_DOC_TYPES` | `config.py:59`, `validators/document_validator.py:60` |
| Doc No: 1-16 alphanumeric characters, `/` and `-` allowed | `INVOICE_NUMBER_PATTERN = r'^[a-zA-Z0-9\/-]{1,16}$'` | `config.py:28` |
| Doc No cannot be only zeros or special characters | `INVALID_INVOICE_PATTERN = r'^[0\/-]+$'` | `config.py:31` |
| Doc Date format: dd-mm-yyyy | `DATE_PATTERN` + `parse_date_ddmmyyyy()` | `config.py:25`, `validators/document_validator.py:134-142` |
| Doc Date cannot be before 01-07-2017 | `is_before_gst_inception()` | `validators/document_validator.py:145-147` |
| Doc Date cannot be in the future | `is_future_date()` | `validators/document_validator.py:150-152` |
| Doc Date cannot be after To Return Period | `is_date_after_period()` | `validators/document_validator.py:155-157` |
| Doc Value: mandatory, non-negative, max 15 digits + 2 decimal places | `is_valid_value(val, 15, 2)` | `validators/document_validator.py:180-200` |

> **HANDOVER Decision 4 confirms:** Invoice Number max length error message was specifically updated per Sidhant's request to read "More than 16 characters not permitted".

### 5.4 Goods-Specific Rules

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| Port Code: mandatory, exactly 6 alphanumeric | `PORT_CODE_PATTERN = r'^[a-zA-Z0-9]{6}$'` | `config.py:34`, `validators/goods_validator.py:161-168` |
| Shipping Bill No: mandatory, 3-7 digits only | `SHIPPING_BILL_PATTERN = r'^[0-9]{3,7}$'` | `config.py:37`, `validators/goods_validator.py:171-178` |
| Shipping Bill Date: mandatory, dd-mm-yyyy, not future | Date validation sequence | `validators/goods_validator.py:181-195` |
| FOB Value: mandatory, non-negative, max 15 digits + 4 decimal places | `is_valid_value(val, 15, 4)` | `validators/goods_validator.py:198-213` |
| EGM Ref No: mandatory, 1-20 alphanumeric, no backslash, no double quotes | `EGM_REF_PATTERN` + special char checks | `config.py:40`, `validators/goods_validator.py:238-255` |
| EGM Date: mandatory, dd-mm-yyyy, not future | Date validation | `validators/goods_validator.py:258-272` |
| BRC/FIRC: **optional** for goods (proof of export via Shipping Bill) | `is_mandatory=False` | `validators/goods_validator.py:137` |

> **HANDOVER Decision 5 explains why:** For goods exports, the Shipping Bill is the proof of export (the goods physically left the country). BRC/FIRC (bank remittance certificate proving payment) is additional but optional because the government already has the shipping bill records.

### 5.5 Services-Specific Rules

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| No shipping bill or EGM fields | Services data model has no shipping bill fields | `models/services_entry.py` |
| BRC/FIRC: **optional per row** (can be on a different row via linking) | `is_mandatory=False` | `validators/services_validator.py:116` |
| BRC-only rows allowed (rare edge case) | `is_brc_only()` check → validates BRC with `is_mandatory=True` | `validators/services_validator.py:120-130` |

> **CRITICAL BUSINESS CONTEXT (from HANDOVER Decision 5):** Sidhant corrected an initial misunderstanding: "Refund can only be claimed AFTER payment is received." For services, BRC/FIRC is the ONLY proof of export (there's no shipping bill). Every services invoice MUST have a corresponding BRC — but one BRC can cover multiple invoices. The code allows individual rows to have no BRC because the BRC linking mechanism (adjacent or group mode) assigns BRC coverage across rows.

### 5.6 BRC/FIRC Validation

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| If any BRC field is present, all three (number, date, value) are required | `has_any = bool(brc_no or brc_date or ...)` | `validators/document_validator.py:227` |
| BRC Number: 2-30 alphanumeric characters | `BRC_NUMBER_PATTERN = r'^[a-zA-Z0-9]{2,30}$'` | `config.py:43` |
| BRC Number cannot be "0" | `brc_no == '0'` check | `validators/document_validator.py:244` |
| BRC Date: dd-mm-yyyy, not future | Date validation | `validators/document_validator.py:255-266` |
| BRC Value: non-negative, max 15 digits + 2 decimal places | `is_valid_value(val, 15, 2)` | `validators/document_validator.py:272-283` |

### 5.7 Duplicate Detection

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| Duplicate documents detected within same financial year | Key: `{doc_type}_{doc_no}_{financial_year}` | `validators/goods_validator.py:94-115`, `validators/services_validator.py:77-98` |
| Financial year: April-March (month >= 4 → same year, month < 4 → year - 1) | `fy_year = year if month >= 4 else year - 1` | `validators/goods_validator.py:97` |
| Goods and Services have **separate** duplicate tracking | Each has its own `seen_docs` dict | `validators/goods_validator.py:54`, `validators/services_validator.py:37` |

> BRC duplicate detection is NOT implemented despite having an error message defined (`duplicate_brc` in config.py:211).

### 5.8 JSON Output Format

| Rule | Implementation | File:Line |
|------|---------------|-----------|
| Version: "3.0" | `JSON_VERSION = "3.0"` | `config.py:124` |
| Refund reason: "EXPWOP" | `REFUND_REASON = "EXPWOP"` | `config.py:125` |
| Goods entries use type: "G" | Hardcoded in `GoodsEntry.to_doc_json()` | `models/goods_entry.py:104` |
| Services entries use type: "S" | Hardcoded in `ServicesEntry.to_doc_json()` | `models/services_entry.py:94` |
| BRC is a separate JSON object sharing `sno` with its document | `to_brc_json()` returns `{'sno': self.sno, ...}` | `models/goods_entry.py:122-127` |
| Serial numbers sequential, goods first then services | `current_sno` incremented per entry | `generators/json_generator.py:66-88` |

### 5.9 Hardcoded Constants

| Constant | Value | Purpose | File:Line |
|----------|-------|---------|-----------|
| `GST_INCEPTION_DATE` | `date(2017, 7, 1)` | No document before this date | `config.py:12` |
| `MAX_MANTISSA_DIGITS` | 15 | Max digits before decimal | `config.py:108` |
| `MAX_DECIMAL_DIGITS_VALUE` | 2 | Decimal places for doc/BRC values | `config.py:109` |
| `MAX_DECIMAL_DIGITS_FOB` | 4 | Decimal places for FOB value | `config.py:110` |
| `MAX_INVOICE_LENGTH` | 16 | Max invoice number characters | `config.py:111` |
| `MIN_BRC_LENGTH` / `MAX_BRC_LENGTH` | 2 / 30 | BRC number length range | `config.py:112-113` |
| `MIN_SB_LENGTH` / `MAX_SB_LENGTH` | 3 / 7 | Shipping bill number length | `config.py:114-115` |
| `PORT_CODE_LENGTH` | 6 | Port code exact length | `config.py:116` |
| `MIN_EGM_LENGTH` / `MAX_EGM_LENGTH` | 1 / 20 | EGM reference length range | `config.py:117-118` |
| Header row search depth | 10 | Max rows to search for column headers | `readers/excel_reader.py:250` |
| Header row match threshold | 3 | Min column name matches to identify header row | `readers/excel_reader.py:258` |

---

## SECTION 6: EDGE CASES AND DEFENSIVE CODE

### 6.1 Handled Edge Cases

| Edge Case | How Handled | File:Line |
|-----------|-------------|-----------|
| Empty rows in data sheets | `is_empty()` checks — row skipped if no doc/BRC fields set | `models/goods_entry.py:78-83` |
| NaN/blank cells in Excel | `pd.isna(value)` checks return `None` | `readers/excel_reader.py:361` |
| Excel date as serial number | `excel_date_to_string()` converts float → datetime → dd-mm-yyyy | `utils/date_utils.py:224-261` |
| Excel date as datetime object | `isinstance(excel_value, datetime)` → `.strftime()` | `utils/date_utils.py:244-245` |
| Date with `/` separator | `.replace('/', '-')` in `__post_init__` and parsers | `models/goods_entry.py:60` |
| Floating-point integers (e.g., `100000.0`) | `float.is_integer()` → convert to `int` then `str` | `readers/excel_reader.py:404-405` |
| Thousand separators in values | `str_value.replace(',', '')` | `utils/number_utils.py:32` |
| BOM in CSV files | `encoding='utf-8-sig'` handles BOM transparently | `readers/csv_reader.py:123` |
| .xlsb leading zero loss in periods | `str(int(float(value))).zfill(6)` pads to 6 digits | `readers/xlsb_reader.py:180-182` |
| .xlsb "DISABLED" cells | `_get_non_disabled_value()` returns `None` for 'DISABLED' | `readers/xlsb_reader.py:265-270` |
| .xlsb "Clear" in doc type | Skipped: `if doc_type == 'Clear': continue` | `readers/xlsb_reader.py:199` |
| File not found | Check `path.exists()` before opening | `readers/excel_reader.py:59-61` |
| Wrong file extension | Check suffix against allowed values | `readers/excel_reader.py:64-66` |
| Missing sheet in Excel | Logged but optional (goods/services sheets optional) | `readers/excel_reader.py:85-86` |
| Column headers not found | Searches first 10 rows, needs 3+ matches | `readers/excel_reader.py:249-261` |
| tkinter not available | `ImportError` caught, falls back to CLI message | `main.py:64-68` |
| Case-insensitive sheet/column names | `.lower()` comparison throughout | `readers/excel_reader.py:118,283` |
| Column index beyond row length | `col_idx >= len(row)` → returns `None` | `readers/excel_reader.py:357-358` |
| Keyboard interrupt during input | `except (EOFError, KeyboardInterrupt)` | `main.py:230-232` |
| Output directory doesn't exist | `path.parent.mkdir(parents=True, exist_ok=True)` | `generators/json_generator.py:260` |
| Empty string vs None for values | Checks `value is None or value == ''` | `validators/document_validator.py:180` |

### 6.2 Problems Encountered During Development (from HANDOVER Section 7)

| Problem | Root Cause | Fix |
|---------|-----------|-----|
| Return period "012025" read as 12025 | Excel stores as number, pandas reads as int, leading zero lost | `str(int(float(value))).zfill(6)` in `xlsb_reader.py:180-182` |
| BRC number "HKO250205002" vs expected "HKO2502050002" | **Data discrepancy in source .xlsb file**, not a parsing bug | Documented as data quality issue |
| Excel dates come as serial numbers (e.g., 45678) | Excel's internal date representation | `excel_date_to_string()` converts using epoch `1899-12-30` |
| "DISABLED" values in .xlsb for services rows | Government tool writes "DISABLED" in shipping bill columns for services | `_get_non_disabled_value()` returns `None` |

### Overall Rating: **ROBUST**

The validation layer is comprehensive — it matches the government VBA tool's rules closely. Date handling covers multiple input formats. File reading handles missing sheets, wrong extensions, and encoding. The error reporting is structured and informative. Real-world testing with 149 entries validated the entire pipeline.

---

## SECTION 7: EDGE CASES NOT HANDLED (GAPS AND VULNERABILITIES)

### 7.1 Missing Validations

| Gap | Risk | Severity | Context from HANDOVER |
|-----|------|----------|----------------------|
| **No BRC duplicate detection** | Same BRC number can appear multiple times without warning | Medium | Error message `duplicate_brc` exists but is never used |
| **No Group ID mode validation** | Entries in group mode aren't validated for having group IDs or BRC | High | Error messages `group_id_missing` and `group_id_no_brc` exist but never used |
| **No end-to-end BRC coverage check for services** | Services entries with no BRC coverage from any row (not linked via adjacent or group mode) would produce JSON without BRC, which the portal may reject | Medium | HANDOVER confirms BRC is mandatory for services but current code allows uncovered invoices |
| **No shipping bill presence check for services** | If services entry somehow had SB fields, they'd be silently ignored | Low | Error message `services_shipping_present` defined but never used |
| **Cross-sheet duplicate detection missing** | Same invoice number in both Goods and Services sheets not flagged | Low | Separate `seen_docs` dicts per sheet |
| **No chronological date checks** | SB date vs doc date, EGM date vs SB date, BRC date vs doc date — no logical ordering enforced | Low | Government tool may not enforce this either |
| **No BRC date validation** | BRC Date cannot be outside the period of refund being filed as the refund of Export of Service which is based on BRC is applicable based on the foreign currency remittance date and not on the basis of the invoice date against which the remittance has been received | High | (This missing validation is added manually by the user)

### 7.2 Double Validation Bug

**File:** `validators/services_validator.py:108-130`

When a services row has BRC details but no document (`is_brc_only()` returns True), the BRC is validated TWICE:
1. Line 108: `if entry.has_brc():` → True → validates with `is_mandatory=False`
2. Line 120: `if entry.is_brc_only():` → True → validates again with `is_mandatory=True`

Since `is_brc_only()` implies `has_brc()`, both blocks execute. For invalid BRC data, each error message appears in the report **twice**.

### 7.3 Silent Logic Issues

| Issue | Details | File:Line |
|-------|---------|-----------|
| `Header.to_json_dict()` has hardcoded values diverging from config | `refundRsn: 'EXPWOP'` and `version: '3.0'` hardcoded while `JSONGenerator` uses constants from config. Not currently a bug because `to_json_dict()` is dead code. | `models/header.py:46-47` |
| `doc_value=0` treated as valid | Zero-value invoice accepted — unlikely to be valid but not caught | `validators/document_validator.py:180-200` |
| Decimal → float precision loss in JSON | Values converted via `float()` for JSON output. For max 15 digits + 2 decimals, IEEE 754 can lose sub-cent precision in rare cases | `models/goods_entry.py:103,108` |

### 7.4 Deferred Features (from HANDOVER)

| Feature | Status | HANDOVER Reference |
|---------|--------|-------------------|
| BRC-only rows for Goods | Deferred | Sidhant: "I haven't encountered such a row, will change logic afterwards if needed" (Section 3) |
| GUI interface | Not started | Section 9: future enhancement |
| PDF generation | Not started | Section 9: mentioned as planned |
| Batch processing for multiple files | Not started | Section 9: mentioned as planned |
| `requirements.txt` | Not created | HANDOVER Question 2 |
| Comprehensive test suite | Tests written but removed | HANDOVER Section 8: removed from distribution |
| Proper logging | Not implemented | HANDOVER Question 4: currently uses print statements only |

### 7.5 Scenario-Based Failure Analysis

| Scenario | What Breaks |
|----------|-------------|
| **Working directory different from project** | `sys.path.insert()` in each file handles this — should work |
| **Network drive disconnect mid-write** | Partial/corrupt JSON file left with no cleanup |
| **Two instances write same output file** | Last writer wins, no file locking |
| **Python 3.7-3.8** | `list[ValidationError]` type hint syntax fails (needs 3.9+) |
| **openpyxl not installed** | Only `create_template.py` fails; main tool works for .xlsb and CSV |
| **pyxlsb not installed** | Only .xlsb reading fails; .xlsx and CSV work |

---

## SECTION 8: DESIGN DECISIONS (INFERRED)

> Decisions D1-D8 are now **confirmed** by HANDOVER.md rather than merely inferred.

### D1: Python + CLI + tkinter Dialogs
**Confidence: HIGH — CONFIRMED by HANDOVER**
CLI-first with optional file pickers (HANDOVER Decision 6: Sidhant requested GUI file selection when running without arguments). "GUI can be added later as an enhancement" (HANDOVER, Rejected Approaches). The tool must be offline — "No external APIs or network calls needed" (HANDOVER Section 8).

### D2: Pandas for File Reading (not openpyxl directly)
**Confidence: HIGH — CONFIRMED by HANDOVER**
The key reason is **pyxlsb support**: "`.xlsb` support lets users work directly with govt tool output" (HANDOVER Decision 2). Pandas provides `pd.read_excel(engine='pyxlsb')` which is the simplest way to read .xlsb in Python. Using pandas for ALL formats keeps the API consistent. The tradeoff is heavier dependency (~30MB) but avoids two different reading approaches.

### D3: Flexible Column Mapping
**Confidence: HIGH — CONFIRMED by HANDOVER**
HANDOVER Decision 2 confirms `.xlsx` template "allows copy-paste" and "avoids Excel date formatting issues." The flexible column mapping lets users paste data from Tally, government tools, or other accounting software with varying column headers.

### D4: Validate-All-Then-Report (not fail-fast)
**Confidence: HIGH — CONFIRMED by HANDOVER**
HANDOVER Decision 3: "Validate ALL data FIRST, collect ALL errors, then show comprehensive report. Users prefer to fix all errors in one pass rather than iteratively."

### D5: Separate Goods and Services Models
**Confidence: HIGH — CONFIRMED by HANDOVER**
HANDOVER, Rejected Approaches: "Single-sheet Excel template rejected — our template uses separate sheets for clarity and to match conceptual data structure." Goods have shipping bill/EGM fields; Services don't. The data models mirror this distinction.

### D6: Two BRC Linking Modes
**Confidence: HIGH — CONFIRMED by HANDOVER**
HANDOVER Decision 1: Adjacent mode "matches how the government tool works." Group ID mode added because Sidhant said "Option B is leak-proof." He wanted BOTH options available.

### D7: Dataclasses with `__post_init__` Cleanup
**Confidence: HIGH**
Using dataclasses provides type safety and self-documentation. `__post_init__` normalizes data on creation (strip, uppercase, convert `/` to `-`) so downstream code can assume clean data.

### D8: Decimal for Monetary Values
**Confidence: HIGH**
Data model stores values as `Decimal` objects, avoiding float precision during validation. Only at JSON serialization are they converted to `float`. Correct approach for financial data.

### Pattern Consistency Analysis

| Pattern | Files Following | Files Breaking | Assessment |
|---------|----------------|----------------|------------|
| `sys.path.insert(0, ...)` at file top | All submodule `.py` files | Model files, utils (don't need it) | **Consistent** — only files that need cross-package imports use it |
| tkinter graceful `try/except ImportError` | `main.py:64,131`, `create_template.py:43` | None | **Consistent** |
| `_errors` list + `@property errors` in readers | All 3 readers | None | **Consistent** |
| `__post_init__` cleanup in dataclasses | All 3 data models | None | **Consistent** |
| Re-export with `__all__` in `__init__.py` | All 5 packages | None | **Consistent** |
| Callback `add_error` in validators | `goods_validator.py`, `services_validator.py` using `document_validator.py` | None | **Consistent** |

### Re-Export / API Pattern Note

All five packages use `__init__.py` re-exports with explicit `__all__` lists. The `utils/__init__.py` is the largest, re-exporting 18 functions from 2 modules. Adding a new utility function requires updating: (1) the module file, (2) the `__init__.py` import, (3) the `__all__` list — three places.

---

## SECTION 9: DEPENDENCIES AND ENVIRONMENT

### External Libraries

| Library | Version (from HANDOVER) | Purpose | Required By |
|---------|------------------------|---------|-------------|
| `pandas` | >= 1.5.0 | Excel/CSV reading, DataFrame processing | `excel_reader.py`, `xlsb_reader.py`, `csv_reader.py` |
| `openpyxl` | >= 3.0.0 | Excel template generation, pandas .xlsx engine | `create_template.py`, implicitly by pandas |
| `pyxlsb` | >= 1.0.10 | Government .xlsb binary Excel reading | `xlsb_reader.py` via `pd.read_excel(engine='pyxlsb')` |

> **Documentation gap:** No `requirements.txt` file exists. HANDOVER.md Section 5 lists version ranges but they were never written to a requirements file.

### Standard Library Dependencies

`tkinter`, `argparse`, `json`, `csv`, `pathlib`, `dataclasses`, `decimal`, `datetime`, `calendar`, `re`, `enum`, `typing`, `sys`, `os`

### Python Version

Requires **Python 3.9+** due to `list[ValidationError]` type hint syntax in `validation_error.py:71`.

### OS-Specific Dependencies

None. Cross-platform. tkinter ships with standard Python on Windows/macOS/Linux. HANDOVER confirms: "Must work on Windows (user's environment)" (Section 8).

### File System Assumptions

- Input files must be local (pandas reads from file path, not stream)
- Output directory created if it doesn't exist (`mkdir(parents=True)`)
- No hardcoded paths (the only hardcoded path `/mnt/user-data/outputs` was removed in commit c7c02d9)

### Setup Steps (Fresh Machine)

```bash
# 1. Install Python 3.9+
# 2. Install dependencies
pip install pandas openpyxl pyxlsb

# 3. Run the tool
python main.py                    # Interactive mode
python main.py input.xlsx         # Direct mode
python create_template.py         # Generate blank template
```

---

## SECTION 10: UI/INTERFACE DOCUMENTATION

### 10.1 Command-Line Interface

| Argument | Type | Description |
|----------|------|-------------|
| `excel_file` | Positional, optional | Path to .xlsx or .xlsb input file |
| `--csv-dir` | Option | Directory containing CSV files |
| `-o, --output` | Option | Output JSON file path |
| `--validate-only` | Flag | Only validate, don't generate JSON |
| `--brc-mode` | Choice: `adjacent`/`group` | BRC linking mode (default: adjacent) |
| `--pretty` | Flag | Pretty-print JSON output |
| `-v, --verbose` | Flag | Verbose output |

### 10.2 Interactive Mode (No Arguments)

```
============================================================
GST REFUND STATEMENT 3 GENERATOR
============================================================

No input file specified. Opening file picker...

Select input type:
  1. Excel file (.xlsx or .xlsb)
  2. CSV folder (containing header.csv, goods.csv, services.csv)
  3. Exit

Enter choice (1/2/3): _
```

### 10.3 File Picker Dialogs

Three native OS dialogs:
1. **Open File** — Filters: Excel (*.xlsx *.xlsb *.xls), CSV (*.csv), All. Title: "Select GST Refund Statement 3 Input File".
2. **Open Folder** — Title: "Select folder containing CSV files".
3. **Save As** — Filter: JSON (*.json), All. Default: `{input_stem}_Statement3.json`. Title: "Save Statement 3 JSON As".

All use `root.attributes('-topmost', True)` to appear in front.

### 10.4 User Context (from HANDOVER Section 8)

- Sidhant is NOT a coder — technical concepts must be explained simply
- Prefers conversational explanations over Q&A
- Appreciates when assumptions are stated explicitly
- Tool must work on Windows (his environment)

---

## SECTION 11: RECONSTRUCTION BLUEPRINT

### 11.1 Foundation

1. Set up Python 3.9+ project with virtual environment
2. Create `requirements.txt`: `pandas>=1.5.0`, `openpyxl>=3.0.0`, `pyxlsb>=1.0.10`
3. Create project structure with 5 packages: `models/`, `readers/`, `validators/`, `generators/`, `utils/`
4. Create `config.py` with all regex patterns, column mappings, and constants

### 11.2 Core Logic Build Order

```
1.  config.py (constants, patterns, error messages)
2.  utils/date_utils.py + utils/number_utils.py
3.  models/header.py, goods_entry.py, services_entry.py
4.  models/validation_error.py
5.  validators/document_validator.py (shared validation)
6.  validators/header_validator.py
7.  validators/goods_validator.py
8.  validators/services_validator.py
9.  readers/excel_reader.py
10. readers/xlsb_reader.py
11. readers/csv_reader.py
12. generators/json_generator.py
13. main.py
14. create_template.py
```

### 11.3 Feature Priority

| Priority | Feature | Rationale |
|----------|---------|-----------|
| **Essential** | Excel reader (F1) | Primary input method |
| **Essential** | Validation (F4) | Core value — prevents bad uploads |
| **Essential** | JSON generation (F5) | Primary output |
| **Essential** | Adjacent BRC linking (F6) | Most common use case, matches govt tool |
| **High** | .xlsb reader (F2) | Government format interop |
| **High** | Template generator (F8) | Makes data entry practical |
| **Medium** | Group ID BRC linking (F7) | "Leak-proof" per Sidhant |
| **Medium** | CSV reader (F3) | Automation use case |
| **Medium** | File picker dialogs (F9) | UX convenience |
| **Future** | GUI interface | Per HANDOVER roadmap |
| **Future** | PDF generation | Per HANDOVER roadmap |
| **Future** | Batch processing | Per HANDOVER roadmap |

### 11.4 Known Improvements

> **Constraint:** These respect the design decisions confirmed in Section 8 and the HANDOVER.

| # | Improvement | What to Change | Effort |
|---|-------------|---------------|--------|
| 1 | **Fix double BRC validation bug** | In `services_validator.py:108`, change `if entry.has_brc():` block and `if entry.is_brc_only():` block to `elif` so BRC-only rows validate once | SIMPLE |
| 2 | **Add `requirements.txt`** | Create file with versions from HANDOVER: `pandas>=1.5.0`, `openpyxl>=3.0.0`, `pyxlsb>=1.0.10` | SIMPLE |
| 3 | **Wire up BRC duplicate detection** | Track `seen_brcs` dict in validators, use existing `duplicate_brc` error message | SIMPLE |
| 4 | **Wire up Group ID mode validation** | When `brc_mode == GROUP_ID`, check all entries have group IDs and every group has a BRC. Use existing `group_id_missing` and `group_id_no_brc` messages. Requires passing `brc_mode` to validators. | MODERATE |
| 5 | **Remove dead code** | Delete 7 unused utility functions, 2 unused model methods, 4 unused error messages, 2 unused enum members, 1 unused import | SIMPLE |
| 6 | **Add chronological date validation** | Check SB date >= doc date, EGM date >= SB date, BRC date >= doc date | SIMPLE |
| 7 | **Add test suite** | Recreate tests that were removed (HANDOVER Section 8 confirms tests existed but were removed from distribution) | MODERATE |

### 11.5 Estimated Complexity (AI-Assisted Rebuild)

| Feature | Complexity |
|---------|-----------|
| config.py (patterns, mappings, messages) | MODERATE |
| Data models (3 dataclasses) | SIMPLE |
| Validation framework (error classes) | SIMPLE |
| Document/Header validation | MODERATE |
| Goods validation (SB, EGM, port code) | MODERATE |
| Services validation | SIMPLE |
| Excel reader (flexible columns) | MODERATE |
| XLSB reader (fixed layout) | MODERATE |
| CSV reader | SIMPLE |
| JSON generator + adjacent BRC | MODERATE |
| Group ID BRC linking | COMPLEX |
| CLI + file dialogs | SIMPLE |
| Template generator | SIMPLE |

### 11.6 Suggested Skills

| Skill | Description | Reusable For |
|-------|-------------|-------------|
| **GST Validation** | All GST regex patterns, GSTIN checksum, date rules (inception, future, period), value format rules | Any GST-related tool |
| **Flexible Excel Reader** | Header-row search, column mapping, type-aware cell extraction | Any "read user Excel with varying formats" task |
| **Structured Validation Pipeline** | ValidationError + ValidationResult + callback-based validators + category-based reporting | Any data validation tool |
| **BRC/Invoice Linking** | Adjacent-mode and group-ID-mode linking algorithms | Payment-to-invoice matching scenarios |

---

## SECTION 12: CHANGELOG ARCHAEOLOGY (FROM GIT HISTORY)

> Only one branch exists: `main`. Both commits are on `main`. No feature branches.

### 12A. Complete Development Timeline

#### Phase 1: Complete Application Build (Single Commit)

**Commit `c029ecc` — 2025-12-20 15:51:34 +0530 — Branch: main**
**"Initial Commit"**

- **What changed:** The entire application — 24 files, 4,319 lines. Every source file, every model, every reader, every validator, every utility, the generator, the CLI, the template generator, the README, and the .gitignore.
- **Why it changed:** Complete project built through AI-assisted conversations (README: "Built with Claude for Sidhant's GST practice"). The codebase was developed before version control was initialized. HANDOVER.md (dated Feb 21, 2026) documents the full development conversation context.
- **What it reveals:**
  - The project was mature and well-structured before being committed.
  - Dead code (unused functions, error messages) was written for planned features not yet wired up.
  - `.gitignore` ignores `*.json` (but not `sample_*.json`) — the tool was already generating JSON during development.
  - `create_template.py` had a hardcoded output path `/mnt/user-data/outputs` — a cloud IDE path (the conversation platform where the tool was built).
  - HANDOVER Section 13 confirms real-world testing: the tool matched 149 entries from Sidhant's actual `.xlsb` file.

#### Phase 2: Local Deployment Fix

**Commit `c7c02d9` — 2025-12-20 23:07:19 +0530 — Branch: main**
**"Add save file dialog for template generation"**

- **What changed:** `create_template.py` modified:
  1. **Added:** `save_file_dialog()` function (37 lines) — tkinter "Save As" dialog with ImportError handling.
  2. **Changed:** `if __name__ == '__main__'` block — replaced hardcoded cloud path (`/mnt/user-data/outputs`) with interactive save dialog. Moved the print statement from inside `create_template()` to the `__main__` block.
- **Why it changed:** When Sidhant deployed to his Windows machine, `create_template.py` failed or saved to a nonexistent path. The fix adds the same dialog pattern already used in `main.py`.
- **What it reveals:** Classic cloud-to-local deployment issue. The 7-hour gap (15:51 → 23:07) suggests same-day discovery and fix.

#### Phase 3: Post-Git Documentation (Untracked)

**HANDOVER.md and FILE_INDEX.md** — dated February 21, 2026 (two months after git commits)

These files were added to the project directory but never committed. They provide the complete development context that was lost when the AI conversation ended, including:
- All design decisions with reasoning
- Rejected approaches
- Problems encountered and resolutions
- User preferences and constraints
- Real-world test results
- Planned future features
- Open questions

### 12B. File Evolution Map

| File | Created | Changed | Notes |
|------|---------|---------|-------|
| `main.py` | c029ecc | Never | Had file picker and save dialogs from initial commit |
| `config.py` | c029ecc | Never | All 217 lines stable. Dead error messages = planned features |
| `create_template.py` | c029ecc | c7c02d9 | Cloud path removed, save dialog added |
| `generators/json_generator.py` | c029ecc | Never | Both BRC modes present from start |
| `models/*.py` | c029ecc | Never | All 4 model files stable |
| `readers/*.py` | c029ecc | Never | All 3 reader files stable |
| `validators/*.py` | c029ecc | Never | All 4 validator files stable. Double validation bug present since start |
| `utils/*.py` | c029ecc | Never | All utils including dead functions present from start |
| `HANDOVER.md` | Untracked | N/A | Added ~Feb 21, 2026, never committed |
| `FILE_INDEX.md` | Untracked | N/A | Added ~Feb 21, 2026, never committed |

### 12C. Logic and Rule Evolution

All business rules were present in the initial commit and haven't changed. They were reverse-engineered from the government's VBA tool (config.py:3: "Based on government's GST_REFUND_S03MultipleBRC.xlsb validation rules"). No rules were discovered through trial-and-error — they came from the government specification.

**One critical correction from HANDOVER:** Sidhant corrected the understanding of BRC for services — "Refund can only be claimed AFTER payment is received" (not optional). This understanding shaped the design but the code allows per-row optionality because BRC linking handles coverage across rows.

### 12D. Edge Cases Discovered in Production

| Issue | Discovery | Fix | Commit |
|-------|-----------|-----|--------|
| Cloud path in `create_template.py` | First run on Sidhant's Windows machine | Save dialog added | c7c02d9 |
| Return period leading zeros lost from .xlsb | During development | `zfill(6)` padding | Present in c029ecc |
| "DISABLED" values in .xlsb | During development | `_get_non_disabled_value()` | Present in c029ecc |
| Excel serial number dates | During development | `excel_date_to_string()` | Present in c029ecc |
| BRC number data discrepancy | During testing | Documented as data quality issue, not a bug | N/A |

### 12E. Abandoned Approaches and Reversals

| What Was Tried | What Replaced It | Commit |
|---------------|------------------|--------|
| Hardcoded cloud output path (`/mnt/user-data/outputs`) | Interactive save dialog | c7c02d9 |
| Test files in distribution | Tests removed at Sidhant's request | Between c029ecc and c7c02d9 (tests not in either commit, removed before initial commit) |

From HANDOVER (Rejected Approaches):
- **Mandatory BRC per services row** → Rejected because adjacent mode covers invoices across rows
- **Single-sheet Excel template** → Rejected for clarity; separate sheets match data structure
- **GUI-first design** → Rejected; CLI-first with optional dialogs preferred for automation

### 12F. Dependency Evolution

No `requirements.txt` exists. Dependencies stable since initial commit:
- `pandas` — for all file reading
- `openpyxl` — for template generation + pandas engine
- `pyxlsb` — for government .xlsb format

HANDOVER specifies versions: `pandas>=1.5.0`, `openpyxl>=3.0.0`, `pyxlsb>=1.0.10` — but these were never written to a requirements file.

---

## SELF-CONSISTENCY REVIEW

### Check 1: Cross-Section Contradictions

- **Section 8 vs Section 11:** Section 11 does NOT recommend replacing pandas (respects D2). Improvements focus on wiring up existing dead code and fixing bugs. ✓
- **Section 3 (F4: validation works) vs Section 7 (gaps):** Section 3 describes validation as working for implemented rules. Section 7 identifies rules that exist as error messages but aren't wired up. These are complementary, not contradictory. ✓
- **Section 12B ("never changed") vs current code:** All "never changed" files verified. Only `create_template.py` changed (correctly documented). ✓
- **Section 2 (dead code) vs Section 7 (gaps):** Dead error messages correspond exactly to missing validations. ✓
- **Section 5 (BRC rules) vs HANDOVER:** HANDOVER confirms BRC is mandatory for services overall, but the code allows per-row optionality because linking handles coverage. Section 5 now reflects this distinction with HANDOVER context. ✓

### Check 2: Feature Verification

All 9 features (F1-F9) verified through concrete traces. F2 additionally verified against HANDOVER test data (149 entries).

### Check 3: Shared State Verification

- **Write path:** Readers → `self.header`, `self.goods_entries`, `self.services_entries`
- **Read path:** `main.py` → validators and generator
- **Consistency:** All three readers use same attribute names and types. All validators and generator accept same model types. ✓

### Check 4: Pattern Consistency

All 6 patterns (sys.path, tkinter, _errors, __post_init__, re-exports, callbacks) verified consistent across all files.

### Check 5: Corrections

- [Corrected during self-review — originally stated design decisions were "inferred", but HANDOVER.md provides explicit confirmation for D1-D6. Updated Section 8 confidence levels from MEDIUM/HIGH to all HIGH-CONFIRMED.]

---

*Audit completed 2026-03-06. Document generated by Claude Opus 4.6.*
*Additional context sources: HANDOVER.md (Feb 21, 2026), FILE_INDEX.md (Feb 21, 2026)*
