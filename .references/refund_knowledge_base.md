# GST Refund — Knowledge Base

This file documents the business rules and legal context behind the
validations in this tool. It exists so that future developers (human
or AI) understand WHY a validation exists, not just WHAT it checks.

---

## 1. BRC/FIRC Date Must Fall Within the Refund Period

### Rule
The BRC/FIRC (Bank Realisation Certificate / Foreign Inward Remittance
Certificate) date must fall within the From Period and To Period of the
refund application.

### Legal Basis
Refund of IGST on export of services is available in the period in which
the foreign exchange is **realized** (received), not in the period when
the invoice was raised.

### Example
- Invoice raised in FY 2022-23 (say, 15-Jan-2023)
- Foreign exchange realized in FY 2024-25 (say, 20-Aug-2024)
- Refund is eligible in FY 2024-25, not FY 2022-23
- If the refund application covers From: 04-2024 To: 03-2025,
  the BRC date of 20-08-2024 falls within the period — valid
- A BRC date of 31-12-2025 would NOT fall within this period — error

### Affected Statements
- **S03 (EXPWOP)** — has BRC fields + From/To Period in header
- **S02 (EXPWP)** — has BRC fields but NO From/To Period (GSTIN-only
  header, version 3.0), so this check cannot be applied to S02

### Validation Added
`core/date_validators.py → validate_brc_within_period()`
Called from `core/validators/stmt03_validator.py` after BRC field validation.

---

## 2. Invoice Date vs BRC/FIRC Date — No Constraint

The invoice date and BRC/FIRC date have NO chronological relationship.
An invoice can be raised years before the BRC date (the invoice is the
billing event; the BRC is the realization event). The tool does NOT
check whether BRC date >= Invoice date, because that is not a rule.

---

## 3. BRC/FIRC Date Can Pre-Date GST Inception

The BRC/FIRC date is NOT checked against 01-07-2017 (GST inception).
While unlikely in practice, a realization certificate from before GST
inception is not technically invalid — the tool only checks it against
the refund period and against the future date.

---

*Last updated: 12-Mar-2026*
*Added by: Adv. Sidhant Goyal + Claude Code during real-world testing*
