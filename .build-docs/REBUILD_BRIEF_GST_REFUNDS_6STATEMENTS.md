# Rebuild Brief: GST_REFUNDS_6STATEMENTS

# Date: 2026-03-10

# Author: Adv. Sidhant Goyal

---

## 1. WHAT THIS TOOL DOES

This tool acts as a holistic, centralized generator for preparing the JSON files required for all 6 GST refund statement types (S01A, S02, S03, S04, S05, S06). While it currently serves as a JSON generator that feeds strictly off pre-defined Custom Excel formats, it is being built with a pipeline goal: to evolve into a full compliance engine capable of cross-analyzing input data against GSTR-1 and GSTR-2B data (from the GST Portal, Octa GST, or raw JSON). Ultimately, the application will process refund documents directly in accordance with Section 54 and Rule 89 (read with Circulars 125 & 135) to output perfectly compliant JSON payloads for the portal.

---

## 2. WHO USES THIS AND HOW

- **Primary user:** Article Assistants at CA firms who possess negligible knowledge of the GST refund intricacies and zero coding experience.
- **Technical comfort:** Extremely low. The tool must operate via simple clicks, basic data adjustments, and feature a highly guided, error-proof UI.
- **Data Intake:** Clients provide raw data. Article Assistants fill this data into specific, pre-defined Custom Excel templates. The tool then ingests these completed templates.
- **Error Handling Goal:** The tool must act as a guardrail. If an Article Assistant makes a data entry error, the tool must explicitly explain exactly what went wrong and exactly how to fix it within their Excel template.

---

## 3. FEATURE DECISIONS

| Feature                         | Decision      | Notes                                                                                                                                                                                                                                                                               |
| :------------------------------ | :------------ | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Excel Format Enforcement**    | **STRICT**    | The custom Excel templates (e.g., specific columns in S01A, S02, S03) are meticulously designed. The tool must rigidly enforce this mapping. If any column is missing, renamed, or reordered, the tool must immediately reject the file and notify the user to repair the template. |
| **BRC Linking Modes (S02/S03)** | **KEEP BOTH** | Both Adjacent Mode and Group ID Mode were purposefully designed to provide simplicity across different client data scenarios. Both must remain fully supported.                                                                                                                     |

---

## 4. NEW FEATURES TO ADD

| New Feature                   | What it should do                                                                                                                                                                                              | Why I need it                                                                                                                                        | Priority  |
| :---------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------------------------------------------------------------------------------- | :-------- |
| **Reporting & Review**        | **NONE.** The tool should act as a black-box trust engine. No PDF/JSON previews or technical reports are needed.                                                                                               | The Supervisor/CA will review the data strictly by looking at the Excel file populated by the Article Assistant, not by reading JSON or app reports. | MUST HAVE |
| **Batch Processing**          | **BANNED.** The tool must forcefully process exactly one client/file at a time.                                                                                                                                | GST refunds are a complex subject. Processing them one-by-one is the safest approach to prevent catastrophic cross-client errors.                    | MUST HAVE |
| **GSTIN Checksum Validation** | The tool must directly import and use the existing Python code from the `.claude/skills/gst-gstin-validator` skill to mathematically verify GSTINs. Do not rewrite this logic from scratch (avoid redundancy). | To catch subtle typos in GSTINs (e.g., swapping a 1 for an I) that standard regex cannot catch, preventing portal upload rejections.                 | MUST HAVE |
| **Implicit Rate Checking**    | The tool will dynamically calculate the implied tax rate `(Tax Amount / Taxable Value) * 100` and flag it if it doesn't align with standard GST slabs (5%, 12%, 18%, 28%).                                     | To catch manual data entry typos where an Article Assistant enters incorrect tax amounts compared to the taxable value.                              | MUST HAVE |

---

## 5. BUSINESS RULES — KEEP / CHANGE / ADD

### Rules to KEEP exactly as-is:

- All business rules documented in the Project Audit and the Context Blueprints (Government & Custom) are to be kept exactly as they are.

### Rules to ADD (Missing from original):

- **Duplicate BRC Validation:** Ensure the tool throws an error if the user accidentally inputs the exact same BRC/FIRC number twice for the same logical grouping.
- **Chronological Date Checks:** Validate logical timelines (e.g., a Shipping Bill date cannot logically precede an Invoice Date; an EGM date cannot logically precede a Shipping Bill date).

### Rules to FIX:

- **Double Validation Bug:** Ensure that logic checking (e.g., Services row BRC validation) only executes once so that a single user mistake generates exactly one clear error message, preventing confusing console duplication.

---

## 6. EDGE CASES

### Must handle:

- **Empty Rows:** The tool must elegantly skip completely empty rows in the Excel data. However, to prevent silent failures, it MUST provide an informational warning/message to the user explicitly stating which row numbers were skipped for being bare.
- **Return Period Formatting Bug (042026 vs 42026):** To prevent Excel from quietly converting text to numbers and stripping the leading zero in MMYYYY formats, the rule is **now updated to MM-YYYY**. This will be enforced strictly via the Custom Excel templates themselves (formatted as text or custom date), and the code will simply expect that exact string (e.g., 04-2026).

---

## 7. DESIGN PREFERENCES

- **Framework:** The UI must be rebuilt as a clean, professional Graphical User Interface (GUI) using **PyQt5**.
- **Interface style:** It must completely ditch the CLI/terminal approach.

---

## 8. WHAT I LEARNED

**Guiding Principle:** **Value accuracy with speed.**
The tool must be fast, but never at the expense of correct legal output. If the user (the Article Assistant) does something wrong, the tool must not just crash or display a generic "Error"—it must explain _exactly_ what they did wrong and _exactly_ how to fix it directly in their Excel template.

---

## 9. PARKING LOT

| Idea                           | When it came up | Priority | Status                         |
| :----------------------------- | :-------------- | :------- | :----------------------------- |
| Any new legal logic discovered | During Q&A      | Med      | Pending Future Modular Updates |

---

## 10. IMPLEMENTATION CONCEPTS (For CLAUDE)

While the explicit folder structure and module architecture are left entirely up to **CLAUDE's** best judgment during the coding phase, the following technical concepts must be integrated into the rebuild:

- **Strict Execution Parsers:** The application must contain a strict "guardrail" mechanism that checks the incoming Excel file headers against the predefined custom blueprints before processing. If columns are missing or manipulated, execution halts instantly.
- **Mathematical Validators:** Beyond regex, the codebase should natively implement mathematical checks (like the implicit rate checks `(Tax / Value * 100)`). For GSTIN checksum validation, directly import and utilize the existing python file from the `gstin-validator` skill.
- **Isolating Business Logic:** The validation rules for the 6 different statement types (and their distinct JSON schemas, like S01A v2.0 vs S02 v3.0) must be heavily isolated from one another so that an update to Statement 3 does not accidentally break Statement 1A.
- **PyQt5 GUI Structure:** The CLI is to be replaced with a PyQt5 window featuring the following specific components:
  - A dropdown menu to select the Statement Type (1A, 2, 3, 4, 5, 6).
  - A large, clear drag-and-drop zone for the Article Assistant to drop their Excel file.
  - A primary "Process JSON" action button.
  - A prominent status/log area that outputs plain-English, actionable errors (e.g., _"Row 14 on Goods Sheet: Tax amount of ₹180 on a Taxable Value of ₹1000 calculates to an 18% rate, but you entered it in the 12% IGST column. Please fix in Excel."_).

---
