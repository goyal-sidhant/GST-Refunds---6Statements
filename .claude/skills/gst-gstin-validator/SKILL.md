---
name: gst-gstin-validator
description: >
  Validates the format, structure, and checksum of a GSTIN (15-char
  alphanumeric). Use when asked to validate, verify, parse, or check
  a GST number / GSTIN / UIN. Offline structural validation only —
  does NOT check portal status or whether GSTIN is active.
---

# GST GSTIN Structural Validator

## Purpose

This skill enables Claude to perform offline structural validation of a
Goods and Services Tax Identification Number (GSTIN). It validates the
15-character format, verifies the state code against the authorised
enumerated list, checks the embedded PAN or TAN sub-structure, validates
the entity number and registration-type indicator, computes the Luhn Mod
36 check digit, and identifies non-PAN-based special registration types
(UIN, NRTP, OIDAR, Temporary IDs, etc.). This is structural validation
only — it cannot determine whether a GSTIN is currently active, cancelled,
or suspended on the GST portal.

## Legal Basis

- **CGST Act, 2017 — Section 25**: Procedure for registration. Amended by
  CGST (Amendment) Act, 2018 (No. 31 of 2018) w.e.f. 01.02.2019 vide
  Notification No. 02/2019-CT dated 29.01.2019.
- **CGST Rules, 2017 — Rule 10**: Form and manner of registration. Defines
  GSTIN character structure: (a) two characters for state code, (b) ten
  characters for PAN or TAN, (c) two characters for entity code, (d) one
  checksum character.
- **CGST Act, 2017 — Section 51**: Tax Deduction at Source (TDS). Effective
  01.10.2018 vide Notification No. 51/2018-CT dated 13.09.2018.
- **CGST Act, 2017 — Section 52**: Tax Collection at Source (TCS) by
  e-commerce operators. Effective 01.10.2018 vide Notification No.
  52/2018-CT dated 20.09.2018.
- **CGST Act, 2017 — Section 25(9)**: UIN for UN bodies, embassies,
  consulates, and other notified persons.
- **CGST Act, 2017 — Section 2(61)**: Definition of Input Service
  Distributor (ISD).
- **CGST Act, 2017 — Section 24**: Compulsory registration categories
  (NRTP, casual taxable person, ISD, e-commerce operators, etc.).
- **Income Tax Act, 1961 — Section 139A** read with **Rule 114 of the
  Income Tax Rules, 1962**: PAN format and structure.
- **Income Tax Act, 1961 — Section 203A**: TAN requirement and structure.
- **Notification No. 10/2020-CT dated 21.03.2020**: Migration of
  taxpayers from erstwhile UT of Daman & Diu (code 25) to merged UT code
  26 w.e.f. 01.08.2020.
- **Circular No. 168/24/2021-GST dated 30.12.2021**: Mechanism for
  taxpayers of erstwhile Daman & Diu to file refund claims post-merger.
- **J&K Reorganisation Act, 2019**: Creation of UT of Ladakh (state code
  38).
- **Dadra & Nagar Haveli and Daman & Diu (Merger of Union Territories)
  Act, 2019**: Merger effective 26.01.2020. Code 26 now represents the
  combined UT.
- **Notification No. 34/2023-CT dated 31.07.2023**: ECO enrollment for
  unregistered suppliers selling through e-commerce operators.

## Last Updated

- **Date:** 07-03-2026
- **Based on:** Finance Act, 2025; Notification No. 34/2023-CT dated
  31.07.2023; Circular No. 168/24/2021-GST dated 30.12.2021; all
  amendments to Section 25 of the CGST Act up to date.
- **Next review due:** After the next GST Council meeting or upon any
  notification amending Rule 10 of CGST Rules or state code list.

## Rules

### Category 1: Format Validation Rules

#### Rule 1.1 — Length must be exactly 15 characters (after pre-processing)

- **Rule:** A valid GSTIN is exactly 15 characters long. No more, no less.
  Before checking length, the validator must pre-process the input:
  (a) strip leading and trailing whitespace, (b) strip ALL internal spaces.
  If spaces were stripped, add a warning: "Spaces were removed from input.
  GSTIN should not contain spaces — please correct at source." After
  stripping spaces, if the length is not exactly 15, reject. Hyphens and
  other non-alphanumeric characters are NOT stripped — they cause rejection
  at the character-set check (Rule 1.2).
- **Legal Source:** Rule 10 of CGST Rules, 2017 — prescribes (a) 2 chars
  for state code + (b) 10 chars for PAN/TAN + (c) 2 chars for entity code
  + (d) 1 checksum char = 15 total.
- **Edge Cases:** Inputs like "27 AAPFU 0939F 1ZV" are common in copy-
  paste from PDFs and Excel. After stripping spaces → "27AAPFU0939F1ZV"
  → 15 chars → proceeds with a warning. Inputs with hyphens like
  "27-AAPFU0939F-1ZV" → hyphens are NOT stripped → fails character-set
  check with a clear error about invalid characters.
- **Example:** `"27AAPFU0939F1ZV"` → 15 chars, no spaces → passes clean.
  `" 27 AAPFU0939F 1ZV "` → stripped → "27AAPFU0939F1ZV" → passes with
  warning: "Spaces were removed from input."
  `"27AAPFU0939F1Z"` → 14 chars after stripping → fails: "GSTIN must be
  exactly 15 characters. Got 14."

#### Rule 1.2 — Only uppercase alphanumeric characters permitted (auto-correct lowercase)

- **Rule:** Every character in a GSTIN must be either a digit (0–9) or an
  uppercase letter (A–Z). If lowercase letters are found, the validator
  must convert them to uppercase and add a warning: "Lowercase characters
  were converted to uppercase. GSTIN should be in uppercase — please
  correct at source." After conversion, if any non-alphanumeric characters
  remain (hyphens, dots, slashes, etc.), reject with error: "GSTIN
  contains invalid characters: [list them]. Only digits 0–9 and letters
  A–Z are permitted."
- **Legal Source:** Rule 10 of CGST Rules, 2017. The GST portal accepts
  only uppercase alphanumeric input for GSTIN.
- **Edge Cases:** Common confusions: letter O vs digit 0, letter I vs
  digit 1, letter S vs digit 5. The validator accepts what is given after
  case-correction (it cannot guess intent), but if a PAN sub-structure
  check subsequently fails, the error message should hint at possible
  O/0 or I/1 confusion. Lowercase input is especially common when GSTINs
  are extracted from email bodies or unformatted text.
- **Example:** `"27aapfu0939f1zv"` → converted to `"27AAPFU0939F1ZV"` →
  proceeds with warning: "Lowercase characters were converted to
  uppercase." Validation continues on the uppercase version.
  `"27AAPFU0939F1Z-V"` → after case-correction still contains hyphen →
  fails: "GSTIN contains invalid characters: '-'."

#### Rule 1.3 — Regex pattern for overall structure (PAN-based GSTINs)

- **Rule:** A PAN-based GSTIN matches the pattern:
  `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}[0-9A-Z]{1}[0-9A-Z]{1}$`
  This is a loose pattern. Tighter validation of each position follows in
  subsequent rules. Non-PAN-based GSTINs (NRTP, UIN, etc.) will NOT match
  this pattern and must be handled separately (see Category 5).
- **Legal Source:** Rule 10 of CGST Rules, 2017.
- **Edge Cases:** Do NOT hardcode the 14th position as Z in the regex.
  Many online regex implementations (including GeeksforGeeks) incorrectly
  use `Z[0-9A-Z]{1}$` which rejects valid TDS (D), TCS (C), and other
  registration types. The correct 14th position is `[0-9A-Z]{1}`.
- **Example:** `"22AAAAA1234B1D5"` → TDS registration with D at position
  14 → must pass the overall pattern check.

### Category 2: State Code Validation Rules

#### Rule 2.1 — State code must be from the authorised enumerated list

- **Rule:** Positions 1–2 must form one of the following valid state/UT
  codes. This is a non-continuous series with defined gaps.

  **Valid codes (complete enumerated list):**

  | Code | State / Union Territory |
  |------|-------------------------|
  | 01   | Jammu & Kashmir |
  | 02   | Himachal Pradesh |
  | 03   | Punjab |
  | 04   | Chandigarh |
  | 05   | Uttarakhand |
  | 06   | Haryana |
  | 07   | Delhi |
  | 08   | Rajasthan |
  | 09   | Uttar Pradesh |
  | 10   | Bihar |
  | 11   | Sikkim |
  | 12   | Arunachal Pradesh |
  | 13   | Nagaland |
  | 14   | Manipur |
  | 15   | Mizoram |
  | 16   | Tripura |
  | 17   | Meghalaya |
  | 18   | Assam |
  | 19   | West Bengal |
  | 20   | Jharkhand |
  | 21   | Odisha |
  | 22   | Chhattisgarh |
  | 23   | Madhya Pradesh |
  | 24   | Gujarat |
  | 26   | Dadra & Nagar Haveli and Daman & Diu |
  | 27   | Maharashtra |
  | 29   | Karnataka |
  | 30   | Goa |
  | 31   | Lakshadweep |
  | 32   | Kerala |
  | 33   | Tamil Nadu |
  | 34   | Puducherry |
  | 35   | Andaman & Nicobar Islands |
  | 36   | Telangana |
  | 37   | Andhra Pradesh (new, post-bifurcation) |
  | 38   | Ladakh |
  | 97   | Other Territory |
  | 99   | Centre Jurisdiction / Non-Resident |

- **Legal Source:** State codes based on Indian Census 2011 framework,
  adopted for GST purposes. No standalone GST notification prescribes the
  table — codes are operationally embedded in the GST portal master data.
  Code 38 (Ladakh) added pursuant to the J&K Reorganisation Act, 2019.
  Code 26 updated pursuant to the Dadra & Nagar Haveli and Daman & Diu
  (Merger of Union Territories) Act, 2019.
- **Edge Cases:**
  - **Code 25 (Daman & Diu):** Discontinued. All taxpayers migrated to
    code 26 w.e.f. 01.08.2020 per Notification No. 10/2020-CT dated
    21.03.2020. Validator must reject code 25 and report: "State code 25
    (Daman & Diu) is discontinued. Taxpayers were migrated to code 26
    (Dadra & Nagar Haveli and Daman & Diu)."
  - **Code 28 (old undivided Andhra Pradesh):** All GSTINs migrated to
    code 37 (new Andhra Pradesh post-Telangana bifurcation). Validator
    must reject code 28 and report: "State code 28 (undivided Andhra
    Pradesh) is defunct. Use code 37 for Andhra Pradesh."
  - **Codes 39–96, 98:** Unassigned. Must be rejected.
  - **Code 00:** Invalid. Must be rejected.
  - **Code 99:** Valid — used for Non-Resident Foreign Taxpayers (NRTPs)
    and OIDAR providers. When code 99 is detected, the validator should
    switch to non-PAN-based validation logic (see Category 5).
- **Example:** `"25AAAAA1234B1Z5"` → state code 25 → rejected with
  specific message about discontinued Daman & Diu code.

### Category 3: PAN / TAN Validation Rules

#### Rule 3.1 — PAN structure validation (positions 3–12)

- **Rule:** For all PAN-based GSTINs (14th char ≠ D), positions 3–12 must
  conform to the PAN structure: `[A-Z]{5}[0-9]{4}[A-Z]{1}` — five
  uppercase letters, four digits, one uppercase letter.
- **Legal Source:** Section 139A of the Income Tax Act, 1961 read with
  Rule 114 of the Income Tax Rules, 1962.
- **Edge Cases:** The PAN structure is rigid. If the 3rd through 7th
  characters are not all letters, or the 8th through 11th are not all
  digits, or the 12th is not a letter, the GSTIN is structurally invalid.
- **Example:** PAN portion `"AAPFU0939F"` → A-A-P-F-U (5 letters) +
  0-9-3-9 (4 digits) + F (1 letter) → valid PAN structure.

#### Rule 3.2 — PAN 4th character entity type validation

- **Rule:** The 4th character of the embedded PAN (i.e., position 6 of
  the GSTIN) must be one of the following 10 valid entity type codes:

  | Char | Entity Type |
  |------|-------------|
  | C    | Company |
  | P    | Person (Individual) |
  | H    | Hindu Undivided Family (HUF) |
  | F    | Firm (Partnership) |
  | A    | Association of Persons (AOP) |
  | T    | Trust (AOP Trust) |
  | B    | Body of Individuals (BOI) |
  | L    | Local Authority |
  | J    | Artificial Juridical Person |
  | G    | Government |

- **Legal Source:** CBDT PAN structure specification under Rule 114 of
  Income Tax Rules, 1962. Confirmed from the TRACES government portal.
- **Edge Cases:** This validation applies ONLY when positions 3–12
  contain a PAN (not a TAN). When position 14 = D (TDS), positions 3–12
  may contain a TAN instead, in which case this rule is skipped. There is
  no cross-validation between the PAN entity type and any other GSTIN
  position — the entity type is informational, not structurally enforced
  within the GSTIN format.
- **Example:** GSTIN `"27AAPFU0939F1ZV"` → PAN 4th char (position 6) =
  "F" → Firm → valid.

#### Rule 3.3 — TAN structure validation (for TDS registrations)

- **Rule:** When position 14 = D (Tax Deductor under Section 51), positions
  3–12 may contain either a PAN or a TAN. The TAN structure is:
  `[A-Z]{4}[0-9]{5}[A-Z]{1}` — four uppercase letters, five digits, one
  uppercase letter.
- **Legal Source:** Section 203A of the Income Tax Act, 1961 for TAN.
  The GST portal Tax Deductor registration guide
  (tutorial.gst.gov.in) explicitly states: "TDS applicants who do not
  have a PAN can select TAN and enter their TAN."
- **Edge Cases:** The validator must first check if positions 3–12 match
  PAN format. If not, check TAN format. If neither matches, reject. TAN
  structure: first 3 chars = city/region code, 4th char = first letter of
  deductor name, next 5 = serial digits, last = check letter. The PAN
  entity-type validation (Rule 3.2) does NOT apply to TAN.
- **Example:** GSTIN `"07BLRW39567H1DX"` → position 14 = D → check TAN
  pattern: B-L-R-W (4 letters) + 3-9-5-6-7 (5 digits) + H (1 letter) →
  valid TAN structure.

### Category 4: Entity Code Validation Rules

#### Rule 4.1 — Entity number (position 13)

- **Rule:** Position 13 must be in the range `[1-9A-Z]` — digits 1
  through 9, followed by letters A through Z. Zero (0) is NOT valid.
  The value represents the sequential count of GST registrations held
  within a single state under the same PAN.
- **Legal Source:** Rule 10(c) of CGST Rules, 2017 read with Section
  25(2) of CGST Act, 2017 (multiple registrations for business verticals).
- **Edge Cases:** Values beyond "9" (i.e., A through Z) are assigned when
  an entity has more than 9 registrations in the same state — this can
  happen with multiple business verticals, SEZ units, ISD registrations,
  etc. In practice, most GSTINs have "1" at this position.
- **Example:** `"1"` at position 13 → first registration → valid.
  `"0"` at position 13 → invalid, reject.

#### Rule 4.2 — Registration type indicator (position 14)

- **Rule:** Position 14 is a system-generated character indicating the
  registration type. The following values are valid:

  | Value(s)             | Registration Type |
  |----------------------|-------------------|
  | Z                    | Default for regular, composition, casual, ISD |
  | 1–9, A, B, E–J      | Also valid for normal/composition/casual (system-generated) |
  | C                    | Tax Collector — TCS under Section 52 |
  | D                    | Tax Deductor — TDS under Section 51 |
  | S                    | May appear for ISD (per GSTZen); however, ISD registrations also use Z |

  **Complete valid set for position 14:**
  `{Z, 1, 2, 3, 4, 5, 6, 7, 8, 9, A, B, C, D, E, F, G, H, I, J, S}`

  Values NOT currently valid: `{0, K, L, M, N, O, P, Q, R, T, U, V, W, X, Y}`

- **Legal Source:** Rule 10(c) of CGST Rules, 2017 (entity code is two
  characters — positions 13 and 14 together). Section 51 for TDS (D),
  Section 52 for TCS (C). The non-Z values for normal registrations are
  system-generated by the GST portal; no specific notification documents
  their individual meanings.
- **Edge Cases:** Many online validators and regex patterns incorrectly
  hardcode position 14 as "Z". This causes valid TDS, TCS, and certain
  normal registrations to be wrongly rejected. The validator must accept
  the full valid set listed above.
- **Example:** `"D"` at position 14 → TDS registration → valid.
  `"K"` at position 14 → currently unused → reject.

### Category 5: Non-PAN-Based GSTIN Type Detection Rules

#### Rule 5.1 — Detect non-PAN-based GSTIN types by positions 13–14

- **Rule:** Before applying PAN-based validation, examine positions 13–14.
  If they match a known non-PAN-based registration type code, the GSTIN
  follows a completely different internal structure and PAN validation
  must be skipped. The validator should identify the type and report it.

  **Known non-PAN-based type codes (positions 13–14):**

  | Pos 13–14 | Type | Pos 15 | State Code |
  |-----------|------|--------|------------|
  | NF        | Non-Resident Foreign Taxpayer (NRTP) — Section 24 | T (literal, NOT check digit) | Usually state-specific or 99 |
  | UN        | UIN — UN Bodies, Embassies, Consulates — Section 25(9) | Check digit (computed) | State where entity operates |
  | ON        | Other Notified Persons | P (literal) | State-specific |
  | TR        | Tax Return Preparer | P (literal) | State-specific |
  | TM        | Temporary ID | P (literal) | State-specific |
  | OS        | OIDAR Service Provider (non-resident) | Check digit (computed) | 99 |
  | ES        | ECO Enrollment — Notification 34/2023-CT | Check digit (computed) | State-specific |
  | AR        | Advance Ruling Temporary ID | Check digit (computed) | State-specific |
  | RF        | Refund Temporary ID (unregistered persons) — Section 54, Circular 188 | Check digit (computed) | State-specific |

- **Legal Source:** Section 25(9) of CGST Act for UIN. Section 24 for
  NRTP. Notification No. 34/2023-CT for ECO enrollment. GSTZen GSTIN
  format reference table.
- **Edge Cases:**
  - NRTP GSTINs (NF at 13–14): position 15 is a literal "T", NOT a
    computed check digit. Do not attempt check digit validation.
  - Other Notified Persons (ON) and Tax Return Preparer (TR) and
    Temporary ID (TM): position 15 is a literal "P". Do not attempt
    check digit validation.
  - UIN, OIDAR (OS), ECO (ES), AR, RF: position 15 IS a computed check
    digit.
  - The internal structure of non-PAN types is: positions 1–2 = state
    code, positions 3–4 = year of registration (YY), positions 5–7 =
    country code (for NF/UN/ON) or part of serial number (for TR/TM/ES/
    AR/RF), positions 8–12 = serial number.
- **Example:** `"2717USA00046UNV"` → positions 13–14 = "UN" → UIN type
  (US Consulate, Mumbai). Report: "Recognised as UIN (UN Body / Embassy).
  Structural validation of internal components not performed."

#### Rule 5.2 — OIDAR provider detection (state code 99)

- **Rule:** When state code = 99 AND positions 13–14 do not match "NF",
  check if the GSTIN follows the OIDAR format: `99[YY][CCC][SSSSS][XX][C]`
  where YY = year, CCC = country code, SSSSS = serial, XX = service code
  (e.g., "OS" for OIDAR services), C = check digit.
- **Legal Source:** Section 24 of CGST Act read with Section 14 of IGST
  Act (OIDAR services). Registration format per GST portal.
- **Edge Cases:** Known OIDAR examples: Upwork (9923USA29044OSE), Fiverr
  (9924ISR29001OSH), GoDaddy (9917USA29016OS6). The service code at
  positions 13–14 may vary beyond "OS".
- **Example:** `"9917USA29016OS6"` → state code 99, positions 13–14 = OS
  → OIDAR provider → report type.

### Category 6: Check Digit Validation Rules

#### Rule 6.1 — Luhn Mod 36 check digit computation

- **Rule:** The 15th character of a PAN-based GSTIN is a check digit
  computed using the Luhn Mod 36 algorithm over the first 14 characters.
  The computed check digit must match the actual 15th character.

  **Algorithm (step by step):**

  1. Define the character set (36 characters):
     `"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"`
     Each character maps to its index: 0→0, 1→1, ..., 9→9, A→10, B→11,
     ..., Z→35. Total N = 36.

  2. Take the first 14 characters of the GSTIN.

  3. Initialize: `factor = 1`, `total = 0`.

  4. For each character (left to right, position 0 through 13):
     a. Look up the character's code point (index in the character set).
     b. Multiply the code point by the current `factor`.
     c. Compute the "digit": `digit = (product // N) + (product % N)`
        where `//` is integer division and `%` is modulo.
     d. Add `digit` to `total`.
     e. Toggle factor: `factor = 2 if factor == 1 else 1`.

  5. Compute the check digit index: `(N - (total % N)) % N`

  6. The check digit is the character at this index in the character set.

- **Legal Source:** Algorithm sourced from the GSTN Developer API Portal
  (developer.gstsystem.co.in). Confirmed by practitioner verification.
  No CBIC circular formally documents the algorithm.
- **Edge Cases:**
  - The check digit can be any character from 0–9 or A–Z.
  - This algorithm applies ONLY to PAN-based GSTINs and certain non-PAN
    types where position 15 is a computed check digit (UIN, OIDAR, ECO
    enrollment, AR, RF).
  - Do NOT apply check digit validation to NRTP (pos 15 = literal "T"),
    Other Notified Persons (pos 15 = literal "P"), Tax Return Preparer
    (pos 15 = literal "P"), or Temporary ID (pos 15 = literal "P").

#### Rule 6.2 — Worked example of check digit computation

- **Rule:** Demonstration using GSTIN `"27AAPFU0939F1Z"` (14 characters,
  computing the 15th).

  ```
  Character set: 0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ
  N = 36

  Pos | Char | Code Point | Factor | Product | digit (P//36 + P%36) | Running Total
  ----|------|-----------|--------|---------|----------------------|---------------
   0  |  2   |     2     |   1    |    2    |   0 + 2 = 2          |   2
   1  |  7   |     7     |   2    |   14    |   0 + 14 = 14        |  16
   2  |  A   |    10     |   1    |   10    |   0 + 10 = 10        |  26
   3  |  A   |    10     |   2    |   20    |   0 + 20 = 20        |  46
   4  |  P   |    25     |   1    |   25    |   0 + 25 = 25        |  71
   5  |  F   |    15     |   2    |   30    |   0 + 30 = 30        | 101
   6  |  U   |    30     |   1    |   30    |   0 + 30 = 30        | 131
   7  |  0   |     0     |   2    |    0    |   0 + 0 = 0          | 131
   8  |  9   |     9     |   1    |    9    |   0 + 9 = 9          | 140
   9  |  3   |     3     |   2    |    6    |   0 + 6 = 6          | 146
  10  |  9   |     9     |   1    |    9    |   0 + 9 = 9          | 155
  11  |  F   |    15     |   2    |   30    |   0 + 30 = 30        | 185
  12  |  1   |     1     |   1    |    1    |   0 + 1 = 1          | 186
  13  |  Z   |    35     |   2    |   70    |   1 + 34 = 35        | 221

  Check digit index = (36 - (221 % 36)) % 36 = (36 - (221 - 216)) % 36
                     = (36 - 5) % 36 = 31
  Character at index 31 = "V"

  Full GSTIN: 27AAPFU0939F1ZV ✓
  ```

- **Legal Source:** Algorithm from GSTN Developer API Portal.
- **Edge Cases:** Note at position 13 (char Z, code point 35): product =
  70, which exceeds 36. So digit = 70 // 36 + 70 % 36 = 1 + 34 = 35.
  This "fold-back" step is the key differentiator of Luhn Mod N from
  simple weighted sums.

## Common Errors and Pitfalls

1. **Spaces or hyphens in GSTIN:** Practitioners frequently encounter
   GSTINs entered with spaces (e.g., "27 AAPFU 0939F 1ZV") from copy-
   paste out of PDFs and Excel. The validator auto-strips spaces and
   continues validation with a warning. However, hyphens and other special
   characters (e.g., "27-AAPFU0939F-1ZV") are NOT stripped — they cause a
   hard rejection. The warning helps practitioners identify and fix data
   quality issues at source (e.g., in ERP master data).

2. **Lowercase letters:** The GST portal and all official documents use
   uppercase only. Lowercase is common when GSTINs are extracted from
   emails or unformatted text. The validator auto-converts to uppercase
   and continues validation with a warning. This prevents unnecessary
   re-runs while still flagging the data quality issue.

3. **Confusing O with 0 and I with 1:** In PAN positions (3–7 must be
   letters, 8–11 must be digits), entering digit 0 where letter O is
   expected (or vice versa) is a frequent source of e-invoice IRN
   rejections and GSTR-1 mismatches.

4. **Assuming state codes are continuous:** There are defined gaps — no
   code 25 (discontinued), no 28 (defunct), no 39–96, no 98. Validators
   that check "01 ≤ code ≤ 38" will incorrectly accept 25, 28, and will
   miss 97 and 99.

5. **Hardcoding 14th character as Z:** The most widespread validation
   error. This rejects all TDS registrations (D), TCS registrations (C),
   and certain system-generated normal registrations (1–9, A, B, E–J).
   The GeeksforGeeks regex is wrong on this point.

6. **Forgetting checksum validation:** A GSTIN can be format-correct (right
   length, valid state code, valid PAN structure) but have an incorrect
   check digit. Without checksum validation, transposition errors and
   fabricated GSTINs will pass undetected.

7. **Treating non-PAN-based GSTINs as invalid:** UIN holders (embassies,
   UN bodies), OIDAR providers (Upwork, GoDaddy), Temporary IDs, and ECO
   enrollments all have different internal structures. A validator that
   only knows PAN-based format will wrongly reject these legitimate
   registration numbers.

8. **Zero at position 13:** The entity number starts at 1, not 0. Allowing
   zero will accept structurally invalid GSTINs.

9. **Using discontinued state codes in old data:** When processing
   historical data (e.g., invoices from before August 2020), code 25
   (Daman & Diu) may appear in legitimate old records. The validator flags
   this as "discontinued" — which is correct for current validation — but
   practitioners should be aware this was once valid.

10. **Not distinguishing PAN from TAN for TDS registrations:** When
    position 14 = D, the identifier at positions 3–12 could be a TAN
    (4 letters + 5 digits + 1 letter) rather than a PAN (5 letters + 4
    digits + 1 letter). Applying PAN-only validation to TDS GSTINs will
    produce false rejections.

## Limitations

This skill does **NOT** cover the following:

- **Portal API-based status checks:** Cannot determine whether a GSTIN is
  currently Active, Cancelled, Suspended, or under Composition scheme.
  This requires a live API call to the GST portal (gst.gov.in).
- **PAN-to-name verification:** Cannot verify whether the embedded PAN
  belongs to the entity claiming the GSTIN.
- **Composition dealer identification:** Whether an entity is registered
  under the Composition scheme (Section 10) cannot be determined from the
  GSTIN structure alone — Composition GSTINs have the same format as
  Regular GSTINs.
- **Business logic for multi-state registrations:** Cannot determine
  whether a particular entity should or should not have multiple
  registrations.
- **GSTIN generation:** This is a validation-only skill. It does not
  generate new GSTINs.
- **Filing status or return history:** Cannot check GSTR-1, GSTR-3B, or
  any return filing status.
- **Full validation of non-PAN-based types:** For NRTP, UIN, OIDAR,
  Temporary IDs, etc., the validator detects and identifies the type but
  does not validate the internal structure (year, country code, serial
  number) beyond type detection.
- **Specific meaning of non-Z values at position 14:** The values 1–9,
  A, B, E–J at position 14 for normal registrations are system-generated.
  Their individual meanings are not documented by CBIC.

## Change Log

| Date       | Change                                          | Legal Basis |
|------------|-------------------------------------------------|-------------|
| 07-03-2026 | Initial version                                 | CGST Act 2017 (as amended), CGST Rules 2017 (as amended), Income Tax Act 1961 |
| 07-03-2026 | Code 25 (Daman & Diu) marked as discontinued    | Notification No. 10/2020-CT dt. 21.03.2020; Circular No. 168/24/2021-GST dt. 30.12.2021 |
| 07-03-2026 | Code 38 (Ladakh) included                       | J&K Reorganisation Act, 2019 |
| 07-03-2026 | 14th character expanded beyond Z                 | GSTZen format reference; practitioner verification |
| 07-03-2026 | TAN support for TDS registrations added          | GST Portal Tax Deductor registration guide (tutorial.gst.gov.in) |
| 07-03-2026 | Non-PAN-based types documented                   | GSTZen format table; TaxAdda GSTIN structure reference |
