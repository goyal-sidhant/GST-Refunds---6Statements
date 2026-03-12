# GST Refund Offline Utilities — Master Project Document

**Project:** GST Refund App — Custom Excel Templates + Python JSON Generator
**Owner:** Sidhant Goyal (Goyal Tax Services Pvt. Ltd. / Tax People)
**Session Started:** 2026-03-09
**Last Updated:** 2026-03-10 (ALL 6 TEMPLATES + BLUEPRINTS COMPLETE. S06 built with Option B — Inter to Intra / Intra to Inter split. POS dropdown added.)

---

### Additional Note: OctaSales Format Reference

`OctaSales__2_.xlsx` was provided by Sidhant as a **formatting and documentation style reference only** — NOT as a data source for integration. The following OctaSales patterns were adopted for S01A and future custom templates:
- Overview sheet with colour coding legend and sheet descriptions
- Help sheet format: Field Category | Field Name | Field Type | Description
- Colour coding: Blue (0070C0) = Mandatory, Green (00B050) = Optional, Light Blue (00B0F0) = Conditional
- Data validation dropdowns on known fixed-list columns
- Freeze panes on data sheets
**Purpose:** This document captures every decision, analysis, design choice, and open question from the project planning session. It exists so that if the context window ends, work can continue in a new chat with full context.

---

## Table of Contents

1. [Project Goal & Motivation](#1-project-goal--motivation)
2. [Source Materials Provided](#2-source-materials-provided)
3. [Phase 1: Government Format Analysis & Blueprint Creation](#3-phase-1-government-format-analysis--blueprint-creation)
4. [Phase 2: Custom Template Design (Starting Point — S03)](#4-phase-2-custom-template-design-starting-point--s03)
5. [Phase 3: Planning Custom Templates for All 6 Refunds](#5-phase-3-planning-custom-templates-for-all-6-refunds)
6. [S01A Deep Dive — Design Options Under Discussion](#6-s01a-deep-dive--design-options-under-discussion)
7. [Government Template Structural Summary (All 6)](#7-government-template-structural-summary-all-6)
8. [Design Principles Established](#8-design-principles-established)
9. [Deliverables Produced So Far](#9-deliverables-produced-so-far)
10. [Open Decisions & Next Steps](#10-open-decisions--next-steps)
11. [File Inventory](#11-file-inventory)

---

## 1. Project Goal & Motivation

Sidhant wants to build a **Python desktop app** that replaces the government's VBA-locked .xlsb offline utilities for GST refund filing. The app will:

- Accept data via **custom Excel templates** (.xlsx) designed by Sidhant — clean, lightweight, no VBA, no macros
- **Validate all data** in the Python layer (not inside the Excel sheet) — every validation rule that the government VBA performs must be replicated
- **Generate JSON files** in the exact format the GST Portal expects for upload
- Cover **all 6 refund types** that have government offline utilities

**Why this matters:**
- Government utilities are .xlsb files locked with VBA, Windows-only, macro-dependent
- The VBA code has complex lock/unlock behaviour that confuses users
- Error messages appear in an Error column inside the sheet (cluttered UX)
- No separation of concerns — data entry, validation, and JSON generation are all tangled in one Excel file
- Sidhant's approach: Excel is a pure data-entry surface, Python is the brain

**Sidhant's note on design philosophy (exact quote):**
> "There is coding in my format so all the errors shall be caught by the app instead inside the sheet itself which makes the sheet light and easy to use."

---

## 2. Source Materials Provided

### 2.1 VBA Code Exports (text files extracted from .xlsb files)

| File | Statement | Lines | Key Content |
|------|-----------|-------|-------------|
| `1772965799927_GST_REFUND_S01A_vba_code.txt` | S01A — Inverted Tax Structure | 1,601 | ThisWorkbook.cls + Module1.bas |
| `1772965799929_GST_REFUND_S02_vba_code.txt` | S02 — Export Services with Payment | 1,239 | ThisWorkbook.cls + Sheet1.cls + Module1.bas |
| `1772965799931_GST_REFUND_S03MultipleBRC_vba_code.txt` | S03 — Exports without Payment | 2,157 | ThisWorkbook.cls + Module1.bas |
| `1772965799932_GST_REFUND_S04_vba_code.txt` | S04 — SEZ with Payment | 1,292 | ThisWorkbook.cls + Module1.bas |
| `1772965799933_GST_REFUND_S05_vba_code.txt` | S05 — SEZ without Payment | 881 | ThisWorkbook.cls + Module1.bas |
| `1772965799935_GST_REFUND_S06_vba_code.txt` | S06 — Intra/Inter Correction | 2,322 | ThisWorkbook.cls + Module1.bas |

### 2.2 Format Guide (text file)

| File | Content |
|------|---------|
| `GST_Refund_File_Formats_Explained_with_Links.txt` | Field-guide covering all 6 utilities: column layouts, dropdown values, meanings, tutorial links |

### 2.3 Government Excel Templates (.xlsb files)

| File | Statement | Main Sheet | Data Start Row | Data Columns | Helper Sheets |
|------|-----------|------------|----------------|--------------|---------------|
| `GST_REFUND_S01A.xlsb` | Inverted Tax | RFD_STMT01A | Row 11 (A11:T) | 20 cols (A–T) | doctype, outwardtype, Invward type |
| `GST_REFUND_S02.xlsb` | Export Svc w/ Payment | RFD_STMT02 | Row 15 (A15:L) | 12 cols (A–L) | Sheet1 |
| `GST_REFUND_S03MultipleBRC.xlsb` | Exports w/o Payment | RFD_STMT03 | Row 13 (A13:P) | 16 cols (A–P) | Sheet3 |
| `GST_REFUND_S04.xlsb` | SEZ w/ Payment | RFD_STMT04 | Row 15 (A15:L) | 12 cols (A–L) | Sheet1 |
| `GST_REFUND_S05.xlsb` | SEZ w/o Payment | RFD_STMT05 | Row 13 (A13:I) | 9 cols (A–I) | (none) |
| `GST_REFUND_S06.xlsb` | Intra/Inter Correction | RFD_STMT06 | Row 13 (A13:V) | 22 cols (A–V) | PlaceOfSupply (38 states/UTs) |

**Common across all:** Sheet protection password = `aN*4r!U5`, max 10,000 rows, VBA author = Kayalvizhi.

### 2.4 Sidhant's Custom Template (already built for S03)

| File | Content |
|------|---------|
| `GST_Refund_Stmt3_Template.xlsx` | Custom 4-sheet template: Header, Goods (14 cols), Services (8 cols), Instructions |

### 2.5 Tutorial Pages Fetched (from tutorial.gst.gov.in)

All 6 tutorial pages were fetched and their workflow content was incorporated into the holistic blueprint files. The S06 tutorial was found via the File Reply Manual landing page, with the direct URL being: `https://tutorial.gst.gov.in/userguide/refund/tax_pain_on_intra_state_supply_manual.htm`

---

## 3. Phase 1: Government Format Analysis & Blueprint Creation

### 3.1 What Was Done

Every VBA code file was read line by line. The following was extracted for each statement:

1. **Utility identity** — file name, sheet name, JSON statement name, refund code, version
2. **Column layout** — every column with field name, mandatory/optional status, data type
3. **Conditional lock/unlock matrix** — which cells VBA locks/unlocks based on dropdown selections
4. **Tax mutual exclusivity rules** — IGST-only vs CGST+SGST logic
5. **Running totals logic** — which cells accumulate (+Invoice/DN, −CN)
6. **Duplicate detection logic** — dictionary key construction, FY adjustment for Jan-Mar
7. **Regex validation patterns** — all regex patterns with what they apply to
8. **JSON output schema** — exact JSON keys, envelope structure, conditional emission paths
9. **VBA workflow** — Validate vs Create File button flow
10. **GST Portal tutorial workflow** — step-by-step from login to ARN generation
11. **Complete error message catalog** — every unique error string categorized by type

### 3.2 Output Files Created

Six holistic `.txt` blueprint files, one per refund type. Each file has this structure:

```
Sections 1–11: Analysis (concept, format, validation, JSON schema, etc.)
Appendix A: GST Portal tutorial link + workflow
Appendix B: Full VBA code (verbatim, line-by-line)
Appendix C: Complete error message catalog (categorized)
```

**Error counts per statement:**

| Statement | Header Errors | Row-Level Errors | MsgBox Errors | Total Unique |
|-----------|--------------|------------------|---------------|-------------|
| S01A | 15 | ~70 | 8 | 93 |
| S02 | ~10 | ~45 | 7 | 62 |
| S03 | ~15 | ~85 | 8 | 108 |
| S04 | ~12 | ~65 | 8 | 85 |
| S05 | ~8 | ~28 | 5 | 41 |
| S06 | ~15 | ~52 | 8 | 75 |
| **TOTAL** | | | | **464** |

### 3.3 Key Decisions Made

| Decision | Why |
|----------|-----|
| Output as .txt, not .docx | Sidhant explicitly wanted text files. First attempt was .docx — corrected after feedback. |
| Include full VBA code verbatim | Initially omitted. Sidhant caught this: "Did I tell you to remove it?" VBA is the source of truth for app logic. |
| Include tutorial links and workflow | The portal workflow matters for understanding the end-to-end process the app plugs into. |
| Add error catalog as Appendix C | Sidhant correctly identified this as missing: "Is it not required?" For app building, the error catalog IS the validation spec. |
| Categorize errors by type | Errors grouped into: Serial Number, GSTIN/Supplier, Document Type, Document Number, Document Date, Tax Amounts, Port Code, Shipping/EGM, BRC/FIRC, FOB Value, Place of Supply, Duplicates, Numeric/Format. This maps directly to validation functions in the app. |

### 3.4 Key Technical Facts Discovered

**Version differences:**
- S02 and S04 were updated to **version 3.0** on 25-Apr-2025
- In v3.0, Return Period (From/To) fields are **commented out** in VBA — they are NOT validated and NOT included in JSON output
- S01A, S05, S06 remain at **version 2.0** — Return Periods are still active

**JSON envelope differences:**

| Statement | Has fromFp/toFp? | Has orderNo/orderDt? | refundRsn | version |
|-----------|-------------------|----------------------|-----------|---------|
| S01A | YES | No | INVITC | 2.0 |
| S02 | NO (v3.0) | No | EXPWP | 3.0 |
| S03 | YES | No | EXPWOP | 3.0 |
| S04 | NO (v3.0) | No | SEZWP | 3.0 |
| S05 | YES | No | SEZWOP | 2.0 |
| S06 | No | YES | INTRVC | 2.0 |

**Refund category grouping:**

| Category | Statements | Basis of Refund |
|----------|-----------|-----------------|
| Tax Paid refund | S02, S04 | IGST already paid on invoice — refund of that tax |
| Accumulated ITC refund | S01A, S03, S05 | No output tax paid — refund of ITC that accumulated |
| Correction/Reclassification | S06 | Difference between tax paid under wrong POS vs correct POS |

**GSTIN regex (used across all):**
```
^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z1-9A-J]{1}[0-9A-Z]{1}$
```
Note: S02 and S04 are missing the `^` anchor in their regex — likely a bug in the government code but doesn't cause issues because VBScript_RegExp tests the full string.

**FOB Value special decimal handling:**
- S03 uses `FOB_VALUE_REGEX = ^([0-9]{0,15})([.][0-9]{0,4})?$` — allows **4 decimal places**
- All other amount fields across all statements use 15+2 decimals

---

## 4. Phase 2: Custom Template Design (Starting Point — S03)

### 4.1 Sidhant's Existing Custom Template for S03

Sidhant had already built `GST_Refund_Stmt3_Template.xlsx` with this structure:

```
Sheet 1: Header
  A: Field Name | B: Value | C: Description
  Row 2: GSTIN
  Row 3: Legal Name (optional — NOT in govt format)
  Row 4: From Period (MM-YYYY)
  Row 5: To Period (MM-YYYY)

Sheet 2: Goods (14 columns)
  A: Doc Type | B: Doc No | C: Doc Date | D: Doc Value | E: Port Code |
  F: SB No | G: SB Date | H: FOB Value | I: EGM Ref No | J: EGM Date |
  K: BRC No | L: BRC Date | M: BRC Value | N: BRC Group ID

Sheet 3: Services (8 columns)
  A: Doc Type | B: Doc No | C: Doc Date | D: Doc Value |
  E: BRC No | F: BRC Date | G: BRC Value | H: BRC Group ID

Sheet 4: Instructions (49 rows of usage guidance)
```

### 4.2 Five Architectural Decisions in Sidhant's Template

| # | Decision | Rationale |
|---|----------|-----------|
| 1 | **Sheet-as-Type separation** (Goods vs Services) | Government uses G/S dropdown + VBA lock/unlock on 6 columns. Sidhant splits into two purpose-built sheets — impossible to enter Port Code for a service export. The G/S flag is implicit in the sheet name. |
| 2 | **Error column removed** | Government puts errors in Col P. Sidhant pushes all validation to the Python app. Sheet stays clean. |
| 3 | **Serial number removed** | Government auto-generates Sr. No. via `autoGenSerial()`. It's a computed field — the app handles it. |
| 4 | **Header sheet separated** | Government mixes GSTIN/Return Period into top rows of the data sheet (C4, C5, C6). Sidhant gives it a clean separate sheet. Easier to parse programmatically. |
| 5 | **BRC Group ID column added** (innovation) | Government VBA does BRC linking implicitly through row adjacency. Sidhant adds explicit linking via two modes: Adjacent (default) and Group ID. |

### 4.3 Column Mapping: Government S03 → Sidhant's Template

**Fields REMOVED from government format:**
- Sr. No. (Col A) → auto-generated by app
- G/S Flag (Col F) → implicit in sheet name
- Error (Col P) → handled by app

**Fields ADDED (not in government format):**
- BRC Group ID (Goods Col N, Services Col H) → for explicit BRC linking
- Legal Name (Header Row 3) → optional, not in govt format

**Fields MAPPED (same data, cleaner names):**
All 13 remaining government fields map one-to-one to Sidhant's columns, just shifted left due to removed columns.

### 4.4 Suggestions Given to Sidhant

1. **Add data validation dropdown on Doc Type column** — just `Invoice, Credit Note, Debit Note` — prevents typos at source, costs nothing, app still validates independently. **Sidhant accepted this suggestion.**

2. **Handle optional BRC-on-goods path** — Government JSON emits BRC keys for goods rows when provided. App must handle three paths for Goods:
   - Path 1: Goods with shipping, no BRC → customs keys only
   - Path 2: Goods with shipping AND BRC → customs keys + BRC JSON node
   - Path 3: BRC-only row on Goods sheet → BRC keys only

3. **Group ID mode edge case** — In Group ID mode, an invoice with no BRC and no Group ID should be flagged as a validation error.

### 4.5 BRC Linking Modes (from Instructions sheet)

**Mode 1: ADJACENT (Default)**
```
Run: python main.py input.xlsx
BRC on a row covers ALL invoices above it (until previous BRC)
Example:
  Row 2: Invoice SVC/001 (no BRC)     ─┐
  Row 3: Invoice SVC/002 (no BRC)      ├─ Covered by BRC on Row 4
  Row 4: Invoice SVC/003 + BRC ₹15L   ─┘
```

**Mode 2: GROUP ID**
```
Run: python main.py input.xlsx --brc-mode group
Use BRC Group ID column to explicitly link invoices
Example:
  Row 2: Invoice SVC/001, Group=GRP1 (no BRC)
  Row 3: Invoice SVC/002, Group=GRP1, BRC=FIRC001  → Covers both
```

---

## 5. Phase 3: Planning Custom Templates for All 6 Refunds

### 5.1 Complexity Tiers

| Tier | Statements | Complexity | Notes |
|------|-----------|------------|-------|
| **Tier 1 — Simple** | S02, S04, S05 | Low | Structurally straightforward, similar to S03 approach |
| **Tier 2 — Needs design discussion** | S01A | High | Inward-outward pairing in single row, 5 inward types with different field behaviour |
| **Tier 3 — Unique** | S06 | High | Earlier vs Correct comparison, B2B/B2C toggle, Inter/Intra toggle, Place of Supply |

S03 is already done (Sidhant's existing template).

### 5.2 Tier 1 Quick Assessment

**S02 (Export Services with Payment):**
- Simplest of all. Service exports only — no Goods/Services split needed.
- Columns: Doc Type, Doc No, Doc Date, Doc Value, Taxable Value, IGST, Cess, BRC No, BRC Date, BRC Value
- Custom format: Header + single Data sheet + Instructions
- Design question: keep BRC Group ID concept? (Yes — same multi-BRC logic applies)
- Note: v3.0 — Return periods NOT in JSON

**S04 (SEZ with Payment):**
- Similar to S02 but adds Recipient GSTIN (SEZ unit) and optional Shipping Bill/Endorsed Invoice
- Single sheet sufficient
- Design question: Shipping Bill is optional — keep in same row

**S05 (SEZ without Payment):**
- Lightest template — only 8 usable columns
- Has G/S flag — Sidhant's Goods/Services sheet split applies perfectly
- Goods sheet: Doc fields + Shipping Bill (no BRC — unlike S03)
- Services sheet: Just Doc fields (no BRC/FIRC at all — unlike S03)
- Very clean

### 5.3 Decision on Order of Work

**Sidhant's choice:** Start with S01A (hardest first), keep the inward-outward pairing decision open while analysing.

**Reasoning:** "hardest first, rest falls into place" — if the S01A design is robust, the simpler statements will follow naturally from the same design language.

---

## 6. S01A Deep Dive — Design Options Under Discussion

### 6.1 What Makes S01A Complex

S01A (Inverted Tax Structure) is the most complex because:

1. **Dual-sided rows** — Each row has an INWARD side (where ITC came from) and an OUTWARD side (which supply consumed it)
2. **5 inward supply types** with different field dependencies
3. **3 outward supply types** with different field dependencies
4. **Three JSON generation paths** based on which sides have data
5. **Tax mutual exclusivity** rules differ by inward type AND outward type

### 6.2 S01A Government Layout (Row 9 headers, data from Row 11)

```
INWARD SIDE (Cols A–K):
  A: Sr. No.*
  B: Type of Inward Supply* (dropdown: 5 types + Clear)
  C: GSTIN of Supplier / Self GSTIN*
  D: Type of Document* (Invoice/Bill of Entry, Debit Note, Credit Note)
  E: Document No. / Bill of Entry No.*
  F: Document Date* (dd-mm-yyyy)
  G: Port Code (conditional — only for Import of Goods)
  H: Taxable Value*
  I: Integrated Tax (IGST)
  J: Central Tax (CGST)
  K: State/UT Tax (SGST)

OUTWARD SIDE (Cols L–T):
  L: Type of Outward Supply* (dropdown: B2B, B2C-Large, B2C-Small)
  M: Type of Document*
  N: Document No.*
  O: Document Date*
  P: Taxable Value*
  Q: Integrated Tax (IGST)
  R: Central Tax (CGST)
  S: State/UT Tax (SGST)
  T: Error (VBA auto-populated)

HEADER:
  C4: GSTIN
  C5: From Return Period (mmyyyy)
  C6: To Return Period (mmyyyy)

TOTALS ROW (Row 7):
  H7: Total Inward Taxable Value
  I7: Total Inward IGST
  J7: Total Inward CGST
  K7: Total Inward SGST
  P7: Total Outward Taxable Value
  Q7: Total Outward IGST
  R7: Total Outward CGST
  S7: Total Outward SGST
```

### 6.3 Inward Supply Type Dependencies

| Type | GSTIN (C) | Port Code (G) | IGST (I) | CGST (J) | SGST (K) |
|------|-----------|---------------|----------|----------|----------|
| Import of Goods/SEZ to DTA | Auto Self GSTIN (locked) | REQUIRED (6 chars) | REQUIRED (IGST only) | LOCKED | LOCKED |
| Import of Services/SEZ to DTA | Auto Self GSTIN (locked) | LOCKED | REQUIRED (IGST only) | LOCKED | LOCKED |
| Inward supplies liable to RCM | Auto Self GSTIN (locked) | LOCKED | IGST XOR | CGST+ | SGST |
| Inward Supply from Registered Person | Supplier GSTIN (editable, must differ from self) | LOCKED | IGST XOR | CGST+ | SGST |
| Inward Supplies from ISD | ISD GSTIN (editable, must differ from self) | LOCKED | ALL THREE allowed together |

### 6.4 Outward Supply Type Dependencies

| Type | Doc No (N) | Doc Date (O) | IGST (Q) | CGST (R) | SGST (S) |
|------|-----------|-------------|----------|----------|----------|
| B2B | Editable | Editable | IGST XOR (CGST+SGST) |
| B2C-Large | Editable | Editable | REQUIRED (IGST only) | LOCKED | LOCKED |
| B2C-Small | Auto "B2COTH" | Auto "01-07-2017" (hidden) | N/A | EDITABLE | EDITABLE |

### 6.5 JSON Generation — Three Paths

```
PATH A: OUTWARD-ONLY ROW (GSTIN column is blank)
  → Only outward keys emitted
  → JSON: { ostype, odtype, oinum, oidt, oval, oiamt, ocamt, osamt }
  → NOTE: No sno in this path!

PATH B: INWARD-ONLY ROW (GSTIN has data but outward cols 14-19 all blank)
  → Only inward keys emitted
  → JSON: { sno, istype, stin, idtype, inum, idt, portcd, val, iamt, camt, samt }

PATH C: FULL PAIRED ROW (GSTIN has data AND outward doc no has data)
  → Both sides emitted in one JSON node
  → JSON: { sno, istype, stin, idtype, inum, idt, portcd, val, iamt, camt, samt,
            ostype, odtype, oinum, oidt, oval, oiamt, ocamt, osamt }
```

**Critical insight:** The government format allows PARTIAL ROWS. This means:
- A row with ONLY outward data (e.g., B2C-Small consolidated entry)
- A row with ONLY inward data (ITC proof without outward linkage)
- A row with BOTH (typical case — linking ITC to outward supply)

### 6.6 Design Options Presented

**OPTION 1: Keep paired (single Data sheet, ~19 columns)**
- One-to-one match with JSON structure
- Supports all three paths naturally
- **Con:** 19 columns is wide. No field-level guardrails while filling.

**OPTION 2: Split into Inward + Outward sheets, app pairs them**
- Clean UX — each sheet focused
- Inward: 10 cols. Outward: 9 cols.
- **Con:** Needs linking mechanism. If inward has 50 rows and outward has 40, how does app pair them? Solvable but adds complexity.

**OPTION 3: Split by Inward Supply Type (5 sheets)**
- Each sheet has ONLY columns relevant to that type
- No unused columns sitting in rows
- Sheet name = inward type (same as Goods/Services split in S03)
- Outward columns appended to each row
- **Con:** 5 sheets + Header + Instructions = 7 sheets. Most sheets might stay empty for typical clients.

**OPTION 3B: Pragmatic hybrid (2 data sheets)**
```
Inward_Domestic sheet (covers Registered Person + RCM + ISD)
  → Has: Type column, Supplier/ISD GSTIN, Doc fields, IGST, CGST, SGST
  → Plus outward columns appended

Inward_Import sheet (covers Import of Goods + Import of Services)  
  → Has: Type column (Goods/Services), Doc fields, Port Code, IGST only
  → Plus outward columns appended
```
- Split is meaningful: domestic inward has CGST+SGST, import inward is IGST-only
- 2 data sheets instead of 5, plus Header + Instructions = 4 sheets total

### 6.7 Open Question for Sidhant

> "When your clients file inverted structure refunds, which inward supply types do they actually use most frequently?"

If 90% is "Inward Supply from Registered Person" with some "Import of Goods" mixed in, Option 3B (pragmatic hybrid) makes most sense. If all 5 types are regularly used, Option 3 (full split) might be warranted.

**This question was superseded by the pairing decision below — Sidhant's practical insight made the inward type split unnecessary.**

### 6.8 DECISION MADE: Split Inward + Outward, NO Linking

**Decision:** Option 2 — Separate Inward and Outward sheets with NO linking column at any level.

**Decided by:** Sidhant, based on practical experience filing inverted structure refunds.

**Sidhant's reasoning (exact words):**
> "In my experience, the inward and outward are not connected based on the line items, rather they connected in totality, as the number of input invoices may be less but of high quantum, but there maybe small sales of lower rate of conversion or whatever process that leads to lower rate."
> "So thinking that they are connected in line to line item wise, is not appropriate."

**VBA evidence confirming Sidhant's view (12-point analysis performed):**

1. **NO linking key exists** between inward and outward — the `sno` (Sr. No.) is just a row counter from Col A, manually entered by the user. It appears in PATH B (inward-only) and PATH C (full row) but NOT in PATH A (outward-only). It is NOT a foreign key.

2. **No `autoGenSerial` function in S01A** — unlike S02/S03/S04/S05, S01A does not auto-generate serial numbers. The user manually enters them.

3. **Duplicate detection uses SEPARATE dictionaries:**
   - `DUPLICATE_REC` for inward (key = SupplierGSTIN + DocNo + FY + Month)
   - `DUPLICATE_OUTWARD_REC` for outward (key = OutwardType + DocType + DocNo + FY + Month)
   - These dictionaries are NEVER cross-referenced.

4. **Running totals accumulate INDEPENDENTLY:**
   - Inward totals: Cells H7, I7, J7, K7 (taxable value, IGST, CGST, SGST)
   - Outward totals: Cells P7, Q7, R7, S7 (taxable value, IGST, CGST, SGST)
   - No total ever references the other side.

5. **The only cross-reference (Line 1134)** is a DATA COMPLETENESS guard:
   ```vba
   If WS_DATA(rowNo, 5) = "" And WS_DATA(rowNo, 14) = "" Then
       "Either fill both inward and outward supply fields. Else leave either..."
   ```
   This prevents a row where BOTH doc numbers are blank (meaning user selected a Type dropdown but entered no actual data). It does NOT enforce pairing.

6. **The JSON format allows standalone nodes:**
   - PATH A: Outward-only node (no sno, no inward data)
   - PATH B: Inward-only node (no outward data)
   - PATH C: Combined node (both sides — but just for transport convenience)

7. **The portal refund formula is a TOTALITY formula:**
   ```
   Maximum Refund = (Turnover of inverted rated supply × Net ITC / Adjusted total turnover) - Tax payable
   ```
   This operates on AGGREGATE numbers. The portal does NOT match individual inward invoices to individual outward invoices.

8. **The Statement 1A data is SUPPORTING EVIDENCE**, not a matching schedule. It proves "here are my inward supplies" and "here are my outward supplies" — the officer verifies totals, not line-item pairing.

**Implication for app design:**
- The app reads the Inward sheet → validates all rows independently → accumulates inward totals
- The app reads the Outward sheet → validates all rows independently → accumulates outward totals
- JSON generation: the app can emit inward-only nodes, outward-only nodes, or interleave them — the portal doesn't care about row-level pairing
- No linking column, no Group ID, no row-number matching needed

### 6.9 DECISION MADE: Single Inward Sheet, Single Outward Sheet — No Further Splitting

**Decision:** One Inward sheet with a Type column. One Outward sheet with a Type column. No further splitting by supply type.

**Decided by:** Sidhant, based on target user profile and practical workflow.

**Sidhant's reasoning (exact words):**
> "The format which are being created shall be filled by people not less than having a domain knowledge of an Article Assistant in a CA Firm, thus, in my opinion, separating the inward further would result into more chaos, as looking into input segregated or outward segregated in different sheets is a task."

**Why this is the right call:**
- Target users have domain knowledge — they understand inward supply types and don't need the sheet structure to hand-hold them.
- Having input data in one sheet makes reconciliation easier — the user can scroll through all inward invoices in one view, filter/sort by type if needed.
- Having outward data in one sheet gives the same benefit for sales-side review.
- More sheets = more tabs to switch between = more confusion when reviewing totals.
- The app's Type column will serve the same purpose as the government dropdown — the validation engine knows which fields to enforce based on the Type value.

**Final S01A template structure (confirmed):**
```
Sheet 1: Header
  GSTIN, From Period (MM-YYYY), To Period (MM-YYYY)

Sheet 2: Inward
  Inward Supply Type | Supplier GSTIN | Doc Type | Doc No | Doc Date |
  Port Code | Taxable Value | IGST | CGST | SGST

Sheet 3: Outward
  Outward Supply Type | Doc Type | Doc No | Doc Date |
  Taxable Value | IGST | CGST | SGST

Sheet 4: Instructions
```

**What the app must handle per Inward Supply Type:**
- Import of Goods/SEZ to DTA → GSTIN = self (auto), Port Code = mandatory, IGST only
- Import of Services/SEZ to DTA → GSTIN = self (auto), Port Code = N/A, IGST only
- Inward supplies liable to RCM → GSTIN = self (auto), Port Code = N/A, IGST XOR CGST+SGST
- Inward Supply from Registered Person → GSTIN = supplier (mandatory, must differ from self), Port Code = N/A, IGST XOR CGST+SGST
- Inward Supplies from ISD → GSTIN = ISD (mandatory, must differ from self), Port Code = N/A, all three taxes allowed

**What the app must handle per Outward Supply Type:**
- B2B → All fields editable, IGST XOR CGST+SGST
- B2C-Large → All fields editable, IGST only (CGST+SGST locked)
- B2C-Small → Doc No auto = "B2COTH", Date auto = "01-07-2017", CGST+SGST only (no IGST)

**App-side validation note:** Since the sheet has no VBA lock/unlock, the user CAN fill Port Code for a Registered Person row or CGST for an Import row. The app MUST catch these as errors. This is by design — clean sheet, smart app.

---

## 7. Government Template Structural Summary (All 6)

### 7.1 Sheet Structure

| Statement | Sheets | Data Sheet | Header Rows | Data Start | Cols | Helper Sheets |
|-----------|--------|-----------|-------------|-----------|------|---------------|
| S01A | 5 | RFD_STMT01A | Rows 4-6 (GSTIN, From, To) | Row 11 | A:T (20) | doctype, outwardtype, Invward type |
| S02 | 3 | RFD_STMT02 | Row 6 (GSTIN only active) | Row 15 | A:L (12) | Sheet1 |
| S03 | 3 | RFD_STMT03 | Rows 6-8 (GSTIN, From, To) | Row 13 | A:P (16) | Sheet3 |
| S04 | 3 | RFD_STMT04 | Row 6 (GSTIN only active) | Row 15 | A:L (12) | Sheet1 |
| S05 | 2 | RFD_STMT05 | Rows 6-8 (GSTIN, From, To) | Row 13 | A:I (9) | (none) |
| S06 | 4 | RFD_STMT06 | Rows 5-6 (GSTIN, Order No, Order Date) | Row 13 | A:V (22) | PlaceOfSupply |

### 7.2 Dropdown Values (from helper sheets + VBA)

**Document Types (all statements):**
- Invoice (or Invoice/Bill of Entry for S01A)
- Debit Note
- Credit Note
- Clear (resets the cell)

**S01A Inward Supply Types:**
- Import of Goods/Supplies from SEZ to DTA
- Import of Services/Supplies from SEZ to DTA
- Inward supplies liable to reverse charge
- Inward Supply from Registered Person
- Inward Supplies from ISD
- Clear

**S01A Outward Supply Types:**
- B2B
- B2C-Large
- B2C-Small
- Clear

**S03/S05 Goods/Services Flag:**
- G
- S
- Clear

**S06 B2B/B2C:**
- B2B
- B2C
- Clear

**S06 Inter/Intra:**
- Inter
- Intra

**S06 Place of Supply (38 entries):**
```
01-Jammu and Kashmir, 02-Himachal Pradesh, 03-Punjab, 04-Chandigarh,
05-Uttarakhand, 06-Haryana, 07-Delhi, 08-Rajasthan, 09-Uttar Pradesh,
10-Bihar, 11-Sikkim, 12-Arunachal Pradesh, 13-Nagaland, 14-Manipur,
15-Mizoram, 16-Tripura, 17-Meghalaya, 18-Assam, 19-West Bengal,
20-Jharkhand, 21-Odisha, 22-Chattisgarh, 23-Madhya Pradesh,
24-Gujarat, 25-Daman and Diu, 26-Dadra and Nagaraveli, 27-Maharashtra,
29-Karnataka, 30-Goa, 31-Lakshadweep, 32-Kerala, 33-Tamil Nadu,
34-Puducherry, 35-Andaman and Nicobar Islands, 36-Telangana,
37-Andhra Pradesh, 38-Ladakh, 97-Other Territory
```

### 7.3 Regex Patterns Used (compiled from all VBA files)

| Pattern | Regex | Used In | Applied To |
|---------|-------|---------|-----------|
| GSTIN | `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[Z1-9A-J]{1}[0-9A-Z]{1}$` | All | GSTIN fields |
| Date | `^[0-3]{1}[0-9]{1}[-]{1}[0-1]{1}[0-9]{1}[-]{1}[0-9]{4}$` | All | dd-mm-yyyy dates |
| Return Period | `^[0-1]{1}[0-9]{1}[-]{1}[0-9]{4}$` | All | MM-YYYY input format; app strips hyphen for JSON (mmyyyy) |
| Invoice No | `^[a-zA-Z0-9\/-]{0,16}$` | All | Document numbers (max 16) |
| Serial No | `^[0-9]{0,15}$` | All | Sr. No. |
| Amount | `^([0-9]{0,15})([.][0-9]{0,2})?$` | All | Tax/value amounts (15+2) |
| FOB Value | `^([0-9]{0,15})([.][0-9]{0,4})?$` | S03 only | FOB value (15+4!) |
| Port Code | `^[a-zA-Z0-9]{6}$` | S01A, S03 | 6-char port codes |
| Shipping Bill | `^[0-9]{3,7}$` | S01A, S03 | 3-7 digit shipping numbers |
| BRC No | `^[a-zA-Z0-9]{2,30}$` | S01A, S02, S03 | BRC/FIRC numbers |
| EGM Ref | `^[a-zA-Z0-9]{1,20}$` | S03 | EGM reference numbers |

---

## 8. Design Principles Established

These principles emerged from the S03 template design and apply to ALL custom templates going forward:

| # | Principle | Rationale |
|---|-----------|-----------|
| 1 | **Sheet-as-Type** — Use separate sheets when a single dropdown drives fundamentally different column needs | Eliminates VBA lock/unlock. Prevents invalid field combinations. App knows the type from sheet name. |
| 2 | **No VBA, no macros** — .xlsx only | Templates work on any platform. No security warnings. No macro-dependent behaviour. |
| 3 | **No Error column** — All validation in the app | Keeps the sheet clean. Error messages are richer in the app (can show line numbers, suggestions, etc.). |
| 4 | **No Serial Number column** — App auto-generates | It's a computed field. Users shouldn't manage it. |
| 5 | **Header in separate sheet** — Metadata ≠ data | Clean programmatic parsing. No row-offset guessing. |
| 6 | **Instructions sheet** — Always included | In-sheet documentation. Usage notes, field specs, examples. |
| 7 | **Minimal data validations in sheet** — Only dropdowns for known fixed lists | E.g., Doc Type dropdown (Invoice/Credit Note/Debit Note). Prevents typos. App still validates independently. |
| 8 | **BRC Group ID pattern** — When linking relationships exist, provide explicit linking | Don't rely on row adjacency alone. Give users an explicit grouping mechanism. |
| 9 | **Only show columns relevant to the context** — No disabled/greyed columns | If Port Code doesn't apply to services, the Services sheet simply doesn't have a Port Code column. |
| 10 | **Field names are short and clean** — "Doc Type" not "Type of Document", "SB No" not "Shipping bill/ Bill of export/ Endorsed invoice no." | Developer-friendly. Still unambiguous. |
| 11 | **Target user = CA Article Assistant or above** — Don't over-simplify at the cost of added sheet complexity | Users have domain knowledge. They understand supply types, tax heads, and document categories. The sheet shouldn't hand-hold — it should be efficient. More sheets ≠ easier; fewer focused sheets = faster data entry and easier review. |
| 12 | **Split only when column sets are fundamentally different** — Not when the same columns apply with different validation rules | Goods vs Services (S03) = different columns → split. Five inward types (S01A) = same columns, different validation → one sheet with Type column. The app handles context-dependent validation. |

---

## 9. Deliverables Produced So Far

| # | File | Type | Status |
|---|------|------|--------|
| 1 | `GST_Refund_S01A_Inverted_Tax_Structure_COMPLETE.txt` | Govt Blueprint | ✅ Complete (2,061 lines) |
| 2 | `GST_Refund_S02_Export_Services_With_Payment_COMPLETE.txt` | Govt Blueprint | ✅ Complete (1,596 lines) |
| 3 | `GST_Refund_S03_Exports_Without_Payment_COMPLETE.txt` | Govt Blueprint | ✅ Complete (2,596 lines) |
| 4 | `GST_Refund_S04_SEZ_With_Payment_COMPLETE.txt` | Govt Blueprint | ✅ Complete (1,683 lines) |
| 5 | `GST_Refund_S05_SEZ_Without_Payment_COMPLETE.txt` | Govt Blueprint | ✅ Complete (1,201 lines) |
| 6 | `GST_Refund_S06_Intra_Inter_Correction_COMPLETE.txt` | Govt Blueprint | ✅ Complete (2,779 lines) |
| 7 | `GST_Refund_Stmt3_Template.xlsx` | Custom template (S03) | ✅ Rebuilt in OctaSales style — Overview, Header, Goods, Services, Help sheets |
| 8 | `GST_Refund_Stmt3_Blueprint.txt` | Custom Blueprint (S03) | ✅ Complete — 252 lines, 9 sections |
| 9 | `GST_Refund_Stmt1A_Template.xlsx` | Custom template (S01A) | ✅ Complete — Overview, Header, Inward, Outward, Help sheets |
| 10 | `GST_Refund_Stmt1A_Blueprint.txt` | Custom Blueprint (S01A) | ✅ Complete — developer-facing spec with validation rules, JSON spec, edge cases |
| 11 | `GST_Refund_Stmt2_Template.xlsx` | Custom template (S02) | ✅ Complete — Overview, Header, Data, Help sheets |
| 12 | `GST_Refund_Stmt2_Blueprint.txt` | Custom Blueprint (S02) | ✅ Complete — 205 lines, 8 sections |
| 13 | `GST_Refund_Stmt4_Template.xlsx` | Custom template (S04) | ✅ Complete — Overview, Header, Data, Help sheets |
| 14 | `GST_Refund_Stmt4_Blueprint.txt` | Custom Blueprint (S04) | ✅ Complete — 189 lines, 7 sections |
| 15 | `GST_Refund_Stmt5_Template.xlsx` | Custom template (S05) | ✅ Complete — Overview, Header, Goods, Services, Help sheets |
| 16 | `GST_Refund_Stmt5_Blueprint.txt` | Custom Blueprint (S05) | ✅ Complete — 236 lines, 9 sections |
| 17 | `GST_Refund_Stmt6_Template.xlsx` | Custom template (S06) | ✅ Complete — Overview, Header, Inter to Intra, Intra to Inter, Help sheets |
| 18 | `GST_Refund_Stmt6_Blueprint.txt` | Custom Blueprint (S06) | ✅ Complete — 303 lines, 9 sections |
| 19 | `GST_Refund_Project_Master.md` | Session continuity | 🔄 Living document |

**ALL 6 CUSTOM TEMPLATES AND BLUEPRINTS ARE COMPLETE.**

---

## 10. Open Decisions & Next Steps

### 10.1 Decisions Still Needed

| # | Decision | Context | Status |
|---|----------|---------|--------|
| 1 | **S01A: Keep paired rows or split sheets?** | ✅ DECIDED: Option 2 — Split into Inward + Outward sheets, NO linking at any level. Confirmed by VBA analysis (12-point evidence) and Sidhant's practical experience. | ✅ RESOLVED |
| 2 | **S01A: Should Inward sheet be further split by supply type?** | ✅ DECIDED: No. One Inward sheet with a Type column. Target users (CA article assistants+) have domain knowledge — multiple sheets creates chaos for review/reconciliation. | ✅ RESOLVED |
| 3 | **S01A: How to handle B2C-Small auto-fill?** | ✅ DECIDED: App auto-fills Doc No = "B2COTH" and Date = "01-07-2017" in the JSON when Outward Type = B2C-Small. User leaves these blank in the sheet. No user-side action needed — this is a government-mandated fixed value, not a data-entry field. | ✅ RESOLVED |
| 4 | **S01A: JSON generation from separate sheets** | ✅ DECIDED: App reads Inward sheet → emits inward-only nodes (PATH B). Reads Outward sheet → emits outward-only nodes (PATH A). Dumps both into the single `stmt01A` array. No combined nodes (PATH C) needed. No ordering logic. The array is a flat transport container — the portal reads aggregate totals, not node-level pairing. This was ALREADY established by the no-linkage decision and should never have been raised as a separate question. | ✅ RESOLVED |
| 5 | **S06: Place of Supply — dropdown in sheet or code lookup?** | ✅ DECIDED: Dropdown in sheet. 38 state/UT codes as data validation on both POS columns in both data sheets. Prevents typos at source. | ✅ RESOLVED |
| 6 | **S06: Earlier vs Correct — same row or split?** | ✅ DECIDED: Option B — Split by correction direction into two sheets: "Inter to Intra" and "Intra to Inter". 14 columns each, zero dead columns. Sheet name IS the classification direction (Principle 12 — fundamentally different column sets). B2B/B2C derived from GSTIN presence (no column needed). Correct Inter/Intra derived as opposite of Earlier (no column needed). | ✅ RESOLVED |
| 7 | **Companion .txt blueprints for custom templates** | Sidhant explicitly requested these: "text file for the custom format... which shall include things to be taken care in each file during the python coding" | 📋 AGREED — will be created after each custom template is designed |
| 8 | **File organization in app project** | Discussed earlier: `references/` folder for blueprints, `src/` for app code, project root for templates. Sidhant confirmed understanding. | ✅ AGREED in principle |

### 10.2 What's Done & What's Next

**COMPLETED:**
- ✅ All 6 government format holistic blueprints (with VBA code + error catalogs)
- ✅ All 6 custom templates (.xlsx) in unified OctaSales design language
- ✅ All 6 custom template blueprints (.txt) for app development
- ✅ Master project document (this file)

**NEXT PHASE — APP DEVELOPMENT:**
1. Build Python app for S03 first (Sidhant already has a working S03 tool — extend/refine it)
2. Extend to S01A (most complex — inward/outward split, 5 inward types, 3 outward types)
3. S02, S04 (simple, structurally similar — single data sheet each)
4. S05 (lightest — almost trivial after S03)
5. S06 (unique — two direction sheets, B2B/B2C derivation, POS validation)

### 10.3 Ongoing Commitment

This `.md` file will be updated after every prompt exchange. Sidhant's instruction:
> "Keep updating this .md file after each prompt."

---

## 11. File Inventory

### 11.1 Files in `/mnt/user-data/outputs/` (deliverables)

```
GST_Refund_S01A_Inverted_Tax_Structure_COMPLETE.txt    (95 KB, 2,061 lines)
GST_Refund_S02_Export_Services_With_Payment_COMPLETE.txt (65 KB, 1,596 lines)
GST_Refund_S03_Exports_Without_Payment_COMPLETE.txt    (105 KB, 2,596 lines)
GST_Refund_S04_SEZ_With_Payment_COMPLETE.txt           (65 KB, 1,683 lines)
GST_Refund_S05_SEZ_Without_Payment_COMPLETE.txt        (45 KB, 1,201 lines)
GST_Refund_S06_Intra_Inter_Correction_COMPLETE.txt     (180 KB, 2,779 lines)
GST_Refund_Stmt1A_Template.xlsx                        (S01A custom template)
GST_Refund_Stmt1A_Blueprint.txt                        (S01A developer blueprint)
GST_Refund_Project_Master.md                           (this file)
```

### 11.2 Files in `/mnt/user-data/uploads/` (source materials)

```
Government VBA exports:
  1772965799927_GST_REFUND_S01A_vba_code.txt
  1772965799929_GST_REFUND_S02_vba_code.txt
  1772965799931_GST_REFUND_S03MultipleBRC_vba_code.txt
  1772965799932_GST_REFUND_S04_vba_code.txt
  1772965799933_GST_REFUND_S05_vba_code.txt
  1772965799935_GST_REFUND_S06_vba_code.txt

Format guide:
  GST_Refund_File_Formats_Explained_with_Links.txt

Government .xlsb templates:
  GST_REFUND_S01A.xlsb
  GST_REFUND_S02.xlsb
  GST_REFUND_S03MultipleBRC.xlsb
  GST_REFUND_S04.xlsb
  GST_REFUND_S05.xlsb
  GST_REFUND_S06.xlsb

Sidhant's custom template:
  GST_Refund_Stmt3_Template.xlsx

Formatting reference:
  OctaSales__2_.xlsx (Octa GST Sales template — used for formatting/Help style only, NOT for data integration)

Excerpt file:
  excerpt_from_previous_claude_message.txt
```

---

*End of document. This file will be updated after each subsequent prompt.*
