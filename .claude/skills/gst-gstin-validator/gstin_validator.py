"""
gstin_validator.py — Offline structural validator for Indian GSTIN.

Validates format, state code, PAN/TAN sub-structure, entity code,
registration-type indicator, Luhn Mod 36 check digit, and detects
non-PAN-based special registration types (UIN, NRTP, OIDAR, etc.).

Legal basis: CGST Act 2017 (as amended), CGST Rules 2017 — Rule 10,
Income Tax Act 1961 — Section 139A / Rule 114, Section 203A (TAN).

Author : Adv. Sidhant Goyal / Goyal Tax Services Pvt. Ltd.
Version: 1.0.0
Date   : 07-03-2026
"""

import re
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CHAR_SET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
CHAR_TO_CODE = {ch: idx for idx, ch in enumerate(CHAR_SET)}
MOD = len(CHAR_SET)  # 36

# Complete enumerated state code dictionary — Rule 2.1
# Based on Indian Census 2011, adopted for GST. No standalone notification.
STATE_CODES: dict[str, str] = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    # 25 — Daman & Diu: DISCONTINUED per Notification No. 10/2020-CT
    "26": "Dadra & Nagar Haveli and Daman & Diu",
    "27": "Maharashtra",
    # 28 — old undivided Andhra Pradesh: DEFUNCT, migrated to 37
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh",
    "97": "Other Territory",
    "99": "Centre Jurisdiction / Non-Resident",
}

# Discontinued / defunct codes with specific messages
DISCONTINUED_CODES: dict[str, str] = {
    "25": (
        "State code 25 (Daman & Diu) is discontinued. Taxpayers were "
        "migrated to code 26 (Dadra & Nagar Haveli and Daman & Diu) "
        "per Notification No. 10/2020-CT dt. 21.03.2020."
    ),
    "28": (
        "State code 28 (undivided Andhra Pradesh) is defunct. All GSTINs "
        "have been migrated to code 37 (Andhra Pradesh, post-bifurcation)."
    ),
}

# Valid PAN 4th character entity types — Rule 3.2
# Source: CBDT / TRACES, Rule 114 of Income Tax Rules 1962
PAN_ENTITY_TYPES: dict[str, str] = {
    "C": "Company",
    "P": "Person (Individual)",
    "H": "Hindu Undivided Family (HUF)",
    "F": "Firm (Partnership)",
    "A": "Association of Persons (AOP)",
    "T": "Trust (AOP Trust)",
    "B": "Body of Individuals (BOI)",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government",
}

# Valid 14th character values — Rule 4.2
# Z + digits 1-9 + letters A, B, C, D, E, F, G, H, I, J, S
VALID_POS14 = set("Z123456789ABCDEFGHIJS")

# Non-PAN-based GSTIN type codes at positions 13–14 — Rule 5.1
# Maps (pos13 + pos14) -> (type_name, is_check_digit_computed)
NON_PAN_TYPE_CODES: dict[str, tuple[str, bool]] = {
    "NF": ("Non-Resident Foreign Taxpayer (NRTP) — Section 24", False),
    "UN": ("UIN — UN Body / Embassy / Consulate — Section 25(9)", True),
    "ON": ("Other Notified Person", False),
    "TR": ("Tax Return Preparer", False),
    "TM": ("Temporary ID", False),
    "OS": ("OIDAR Service Provider (Non-Resident)", True),
    "ES": ("ECO Enrollment — Notification 34/2023-CT", True),
    "AR": ("Advance Ruling Temporary ID", True),
    "RF": ("Refund Temporary ID (Unregistered Person) — Section 54", True),
}


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def compute_check_digit(first_14: str) -> str:
    """Compute Luhn Mod 36 check digit for the first 14 characters of a GSTIN.

    Algorithm sourced from GSTN Developer API Portal
    (developer.gstsystem.co.in).

    Parameters
    ----------
    first_14 : str
        First 14 characters of the GSTIN (uppercase, alphanumeric).

    Returns
    -------
    str
        Single character (0-9 or A-Z) representing the check digit.

    Raises
    ------
    ValueError
        If input contains invalid characters or is not 14 chars long.
    """
    if len(first_14) != 14:
        raise ValueError(
            f"Expected 14 characters for check digit computation, got {len(first_14)}."
        )

    factor = 1
    total = 0

    for ch in first_14:
        code_point = CHAR_TO_CODE.get(ch)
        if code_point is None:
            raise ValueError(f"Invalid character '{ch}' for check digit computation.")
        product = factor * code_point
        digit = (product // MOD) + (product % MOD)
        total += digit
        factor = 2 if factor == 1 else 1

    check_index = (MOD - (total % MOD)) % MOD
    return CHAR_SET[check_index]


def validate_state_code(code: str) -> dict:
    """Validate positions 1–2 as a GST state code.

    Parameters
    ----------
    code : str
        Two-character state code.

    Returns
    -------
    dict
        Keys: valid (bool), state_name (str or None), error (str or None).
    """
    if code in STATE_CODES:
        return {"valid": True, "state_name": STATE_CODES[code], "error": None}

    if code in DISCONTINUED_CODES:
        return {"valid": False, "state_name": None, "error": DISCONTINUED_CODES[code]}

    return {
        "valid": False,
        "state_name": None,
        "error": f"State code '{code}' is not a valid GST state/UT code.",
    }


def validate_pan_structure(pan: str) -> dict:
    """Validate 10-character PAN structure: [A-Z]{5}[0-9]{4}[A-Z]{1}.

    Also validates the 4th character as a valid entity type.

    Parameters
    ----------
    pan : str
        10-character PAN string.

    Returns
    -------
    dict
        Keys: valid (bool), entity_type (str or None), error (str or None).
    """
    if not re.match(r"^[A-Z]{5}[0-9]{4}[A-Z]$", pan):
        return {
            "valid": False,
            "entity_type": None,
            "error": (
                f"PAN '{pan}' does not match expected structure "
                "[A-Z]{{5}}[0-9]{{4}}[A-Z]. Check for O/0 or I/1 confusion."
            ),
        }

    fourth_char = pan[3]
    if fourth_char not in PAN_ENTITY_TYPES:
        return {
            "valid": False,
            "entity_type": None,
            "error": (
                f"PAN 4th character '{fourth_char}' is not a valid entity type. "
                f"Valid types: {', '.join(sorted(PAN_ENTITY_TYPES.keys()))}."
            ),
        }

    return {
        "valid": True,
        "entity_type": PAN_ENTITY_TYPES[fourth_char],
        "error": None,
    }


def validate_tan_structure(tan: str) -> dict:
    """Validate 10-character TAN structure: [A-Z]{4}[0-9]{5}[A-Z]{1}.

    Parameters
    ----------
    tan : str
        10-character TAN string.

    Returns
    -------
    dict
        Keys: valid (bool), error (str or None).
    """
    if re.match(r"^[A-Z]{4}[0-9]{5}[A-Z]$", tan):
        return {"valid": True, "error": None}

    return {
        "valid": False,
        "error": (
            f"TAN '{tan}' does not match expected structure "
            "[A-Z]{{4}}[0-9]{{5}}[A-Z]."
        ),
    }


def validate_entity_number(char: str) -> dict:
    """Validate position 13 — entity number [1-9A-Z]. Zero is invalid.

    Parameters
    ----------
    char : str
        Single character at position 13.

    Returns
    -------
    dict
        Keys: valid (bool), error (str or None).
    """
    if re.match(r"^[1-9A-Z]$", char):
        return {"valid": True, "error": None}

    if char == "0":
        return {
            "valid": False,
            "error": "Entity number (position 13) is '0'. Valid range is 1-9 then A-Z. Zero is not permitted.",
        }

    return {
        "valid": False,
        "error": f"Entity number (position 13) '{char}' is invalid. Valid range: 1-9, A-Z.",
    }


# ---------------------------------------------------------------------------
# Main Validation Function
# ---------------------------------------------------------------------------

def validate_gstin(gstin: Union[str, None]) -> dict:
    """Validate the format, structure, and checksum of a GSTIN.

    Performs offline structural validation only. Does NOT check portal
    status (active/cancelled/suspended).

    Parameters
    ----------
    gstin : str or None
        The GSTIN string to validate.

    Returns
    -------
    dict
        {
            "input": str or None — the raw input as received,
            "processed": str or None — cleaned version used for validation,
            "valid": bool — overall validity,
            "gstin_type": str — detected registration type,
            "components": dict or None — breakdown of GSTIN components,
            "errors": list[str] — hard errors that make the GSTIN invalid,
            "warnings": list[str] — soft issues auto-corrected during pre-processing,
        }
    """
    result = {
        "input": gstin,
        "processed": None,
        "valid": False,
        "gstin_type": "Unknown",
        "components": None,
        "errors": [],
        "warnings": [],
    }

    # --- Edge case: None or non-string input ---
    if gstin is None:
        result["errors"].append("Input is None. A GSTIN string is required.")
        return result

    if not isinstance(gstin, str):
        result["errors"].append(
            f"Input is of type {type(gstin).__name__}. Expected a string."
        )
        return result

    # --- Pre-processing: strip spaces (Rule 1.1) ---
    raw = gstin
    stripped = raw.strip()
    if " " in stripped:
        result["warnings"].append(
            "Spaces were removed from input. "
            "GSTIN should not contain spaces — please correct at source."
        )
        stripped = stripped.replace(" ", "")

    # --- Pre-processing: convert to uppercase (Rule 1.2) ---
    if stripped != stripped.upper():
        result["warnings"].append(
            "Lowercase characters were converted to uppercase. "
            "GSTIN should be in uppercase — please correct at source."
        )
        stripped = stripped.upper()

    result["processed"] = stripped

    # --- Rule 1.2: Check for non-alphanumeric characters ---
    invalid_chars = set(ch for ch in stripped if ch not in CHAR_TO_CODE)
    if invalid_chars:
        result["errors"].append(
            f"GSTIN contains invalid characters: {sorted(invalid_chars)}. "
            "Only digits 0-9 and letters A-Z are permitted."
        )
        return result

    # --- Rule 1.1: Length check ---
    if len(stripped) != 15:
        result["errors"].append(
            f"GSTIN must be exactly 15 characters. Got {len(stripped)}."
        )
        return result

    gstin_clean = stripped

    # --- Rule 5.1: Detect non-PAN-based types by positions 13–14 ---
    pos13_14 = gstin_clean[12:14]

    if pos13_14 in NON_PAN_TYPE_CODES:
        type_name, has_check_digit = NON_PAN_TYPE_CODES[pos13_14]
        result["gstin_type"] = type_name
        result["valid"] = True  # Recognised type — format accepted

        # Validate state code even for non-PAN types
        sc = gstin_clean[0:2]
        sc_result = validate_state_code(sc)
        if not sc_result["valid"]:
            result["errors"].append(sc_result["error"])
            result["valid"] = False

        result["components"] = {
            "state_code": sc,
            "state_name": sc_result.get("state_name"),
            "type_code": pos13_14,
            "type_description": type_name,
            "check_digit_computed": has_check_digit,
            "note": (
                "Non-PAN-based registration. Internal structure "
                "(year, country code, serial) not validated."
            ),
        }

        # If this type has a computed check digit, verify it
        if has_check_digit:
            expected_cd = compute_check_digit(gstin_clean[:14])
            actual_cd = gstin_clean[14]
            if expected_cd != actual_cd:
                result["errors"].append(
                    f"Check digit mismatch. Expected '{expected_cd}', "
                    f"found '{actual_cd}'."
                )
                result["valid"] = False

        return result

    # --- From here on: PAN-based GSTIN validation ---

    # --- Rule 2.1: State code validation ---
    state_code = gstin_clean[0:2]
    sc_result = validate_state_code(state_code)
    if not sc_result["valid"]:
        result["errors"].append(sc_result["error"])

    # --- Rules 3.1, 3.2, 3.3: PAN / TAN validation ---
    pan_tan_portion = gstin_clean[2:12]
    pos14 = gstin_clean[13]
    identifier_type = None
    entity_type = None

    if pos14 == "D":
        # TDS registration — can be PAN or TAN
        pan_result = validate_pan_structure(pan_tan_portion)
        if pan_result["valid"]:
            identifier_type = "PAN"
            entity_type = pan_result["entity_type"]
        else:
            tan_result = validate_tan_structure(pan_tan_portion)
            if tan_result["valid"]:
                identifier_type = "TAN"
                entity_type = None  # TAN has no entity type
            else:
                result["errors"].append(
                    f"Position 14 is 'D' (TDS). Positions 3-12 must be a valid "
                    f"PAN or TAN. PAN check: {pan_result['error']} "
                    f"TAN check: {tan_result['error']}"
                )
    else:
        # Non-TDS registration — must be PAN
        pan_result = validate_pan_structure(pan_tan_portion)
        if pan_result["valid"]:
            identifier_type = "PAN"
            entity_type = pan_result["entity_type"]
        else:
            result["errors"].append(pan_result["error"])

    # --- Rule 4.1: Entity number (position 13) ---
    pos13 = gstin_clean[12]
    en_result = validate_entity_number(pos13)
    if not en_result["valid"]:
        result["errors"].append(en_result["error"])

    # --- Rule 4.2: Registration type indicator (position 14) ---
    if pos14 not in VALID_POS14:
        result["errors"].append(
            f"Position 14 '{pos14}' is not a valid registration type indicator. "
            f"Valid values: Z, 1-9, A, B, C, D, E-J, S."
        )

    # Determine registration type description
    reg_type_desc = "Regular / Composition / Casual Taxpayer"
    if pos14 == "D":
        reg_type_desc = "Tax Deductor (TDS) — Section 51"
    elif pos14 == "C":
        reg_type_desc = "Tax Collector (TCS) — Section 52"
    elif pos14 == "S":
        reg_type_desc = "Input Service Distributor (ISD) / Other"

    result["gstin_type"] = reg_type_desc

    # --- Rule 6.1: Check digit validation ---
    expected_check_digit = compute_check_digit(gstin_clean[:14])
    actual_check_digit = gstin_clean[14]
    check_digit_valid = expected_check_digit == actual_check_digit

    if not check_digit_valid:
        result["errors"].append(
            f"Check digit mismatch. Position 15 is '{actual_check_digit}', "
            f"expected '{expected_check_digit}' (Luhn Mod 36)."
        )

    # --- Build components ---
    result["components"] = {
        "state_code": state_code,
        "state_name": sc_result.get("state_name"),
        "pan_or_tan": pan_tan_portion,
        "identifier_type": identifier_type,
        "entity_type": entity_type,
        "entity_number": pos13,
        "registration_type_code": pos14,
        "registration_type": reg_type_desc,
        "check_digit": actual_check_digit,
        "check_digit_expected": expected_check_digit,
        "check_digit_valid": check_digit_valid,
    }

    # --- Final validity ---
    result["valid"] = len(result["errors"]) == 0

    return result


# ---------------------------------------------------------------------------
# Unit Tests
# ---------------------------------------------------------------------------

def run_tests():
    """Run unit tests covering every rule in the SKILL.md."""

    passed = 0
    failed = 0
    total = 0

    def assert_test(name: str, condition: bool, detail: str = ""):
        nonlocal passed, failed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✓ {name}")
        else:
            failed += 1
            print(f"  ✗ {name} — {detail}")

    print("=" * 70)
    print("GSTIN Validator — Unit Tests")
    print("=" * 70)

    # ------ Edge Cases: None, empty, wrong type ------
    print("\n--- Edge Cases: Input Type ---")

    r = validate_gstin(None)
    assert_test("None input rejected", not r["valid"])

    r = validate_gstin("")
    assert_test("Empty string rejected", not r["valid"])

    r = validate_gstin(12345678901234)
    assert_test("Integer input rejected", not r["valid"])

    r = validate_gstin(["27AAPFU0939F1ZV"])
    assert_test("List input rejected", not r["valid"])

    # ------ Rule 1.1: Space stripping ------
    print("\n--- Rule 1.1: Space Handling ---")

    r = validate_gstin("27AAPFU0939F1ZV")
    assert_test("Clean GSTIN — no warnings", r["valid"] and len(r["warnings"]) == 0)

    r = validate_gstin(" 27AAPFU0939F1ZV ")
    assert_test(
        "Leading/trailing spaces stripped",
        r["valid"] and r["processed"] == "27AAPFU0939F1ZV",
    )

    r = validate_gstin("27 AAPFU 0939F 1ZV")
    assert_test(
        "Internal spaces stripped with warning",
        r["valid"]
        and r["processed"] == "27AAPFU0939F1ZV"
        and any("Spaces" in w for w in r["warnings"]),
    )

    r = validate_gstin("27AAPFU0939F1Z")
    assert_test(
        "14 chars rejected",
        not r["valid"] and any("15 characters" in e for e in r["errors"]),
    )

    r = validate_gstin("27AAPFU0939F1ZVX")
    assert_test(
        "16 chars rejected",
        not r["valid"] and any("15 characters" in e for e in r["errors"]),
    )

    # ------ Rule 1.2: Lowercase handling ------
    print("\n--- Rule 1.2: Lowercase Handling ---")

    r = validate_gstin("27aapfu0939f1zv")
    assert_test(
        "Lowercase auto-corrected with warning",
        r["valid"]
        and r["processed"] == "27AAPFU0939F1ZV"
        and any("Lowercase" in w for w in r["warnings"]),
    )

    r = validate_gstin("27AAPFU0939F1Z-V")
    assert_test(
        "Hyphen rejected as invalid character",
        not r["valid"] and any("invalid characters" in e for e in r["errors"]),
    )

    r = validate_gstin("27AAPFU0939F1Z.V")
    assert_test(
        "Dot rejected as invalid character",
        not r["valid"] and any("invalid characters" in e for e in r["errors"]),
    )

    # ------ Rule 2.1: State codes ------
    print("\n--- Rule 2.1: State Code Validation ---")

    r = validate_gstin("19AAPFU0939F1ZV")
    # Need to compute check digit for state 19
    cd = compute_check_digit("19AAPFU0939F1Z")
    test_gstin = "19AAPFU0939F1Z" + cd
    r = validate_gstin(test_gstin)
    assert_test(
        "Code 19 (West Bengal) valid",
        r["valid"] and r["components"]["state_name"] == "West Bengal",
    )

    cd = compute_check_digit("38AAPFU0939F1Z")
    test_gstin = "38AAPFU0939F1Z" + cd
    r = validate_gstin(test_gstin)
    assert_test(
        "Code 38 (Ladakh) valid",
        r["valid"] and r["components"]["state_name"] == "Ladakh",
    )

    cd = compute_check_digit("97AAPFU0939F1Z")
    test_gstin = "97AAPFU0939F1Z" + cd
    r = validate_gstin(test_gstin)
    assert_test(
        "Code 97 (Other Territory) valid",
        r["valid"] and r["components"]["state_name"] == "Other Territory",
    )

    r = validate_gstin("25AAPFU0939F1ZV")
    assert_test(
        "Code 25 (Daman & Diu) rejected as discontinued",
        not r["valid"] and any("discontinued" in e for e in r["errors"]),
    )

    r = validate_gstin("28AAPFU0939F1ZV")
    assert_test(
        "Code 28 (old AP) rejected as defunct",
        not r["valid"] and any("defunct" in e for e in r["errors"]),
    )

    r = validate_gstin("00AAPFU0939F1ZV")
    assert_test(
        "Code 00 rejected",
        not r["valid"] and any("not a valid" in e for e in r["errors"]),
    )

    r = validate_gstin("50AAPFU0939F1ZV")
    assert_test(
        "Code 50 (unassigned) rejected",
        not r["valid"] and any("not a valid" in e for e in r["errors"]),
    )

    # ------ Rules 3.1, 3.2: PAN validation ------
    print("\n--- Rules 3.1, 3.2: PAN Structure ---")

    cd = compute_check_digit("27AAPFU0939F1Z")
    r = validate_gstin("27AAPFU0939F1Z" + cd)
    assert_test(
        "Valid PAN with entity type F (Firm)",
        r["valid"] and r["components"]["entity_type"] == "Firm (Partnership)",
    )

    cd = compute_check_digit("27AACCA1234B1Z")
    r = validate_gstin("27AACCA1234B1Z" + cd)
    assert_test(
        "PAN 4th char 'C' → Company",
        r["valid"] and r["components"]["entity_type"] == "Company",
    )

    r = validate_gstin("27AA1FU0939F1ZV")
    assert_test(
        "Digit in PAN letter position rejected",
        not r["valid"]
        and any("PAN" in e and "structure" in e for e in r["errors"]),
    )

    # ------ Rule 3.3: TAN for TDS ------
    print("\n--- Rule 3.3: TAN for TDS Registrations ---")

    # Build a TDS GSTIN with TAN: 4 letters + 5 digits + 1 letter
    tan_portion = "BLRW39567H"  # valid TAN structure
    first_14 = "07" + tan_portion + "1D"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "TDS with valid TAN accepted",
        r["valid"] and r["components"]["identifier_type"] == "TAN",
    )

    # TDS with valid PAN instead of TAN
    pan_portion = "AAACG1234H"
    first_14 = "07" + pan_portion + "1D"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "TDS with valid PAN also accepted",
        r["valid"] and r["components"]["identifier_type"] == "PAN",
    )

    # TDS with invalid identifier (neither PAN nor TAN)
    bad_portion = "1234567890"
    first_14 = "07" + bad_portion + "1D"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "TDS with invalid PAN/TAN rejected",
        not r["valid"] and any("TDS" in e or "PAN" in e for e in r["errors"]),
    )

    # ------ Rule 4.1: Entity number (position 13) ------
    print("\n--- Rule 4.1: Entity Number ---")

    first_14 = "27AAPFU0939F1Z"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test("Entity number '1' valid", r["valid"])

    first_14 = "27AAPFU0939FAZ"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test("Entity number 'A' (10th registration) valid", r["valid"])

    first_14 = "27AAPFU0939F0Z"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "Entity number '0' rejected",
        not r["valid"] and any("Zero" in e or "'0'" in e for e in r["errors"]),
    )

    # ------ Rule 4.2: Registration type (position 14) ------
    print("\n--- Rule 4.2: Registration Type Indicator ---")

    # Test C (TCS)
    first_14 = "27AAPFU0939F1C"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "Position 14 'C' (TCS) valid",
        r["valid"] and "TCS" in r["gstin_type"],
    )

    # Test D (TDS) — already covered above

    # Test numeric value at position 14
    first_14 = "27AAPFU0939F15"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test("Position 14 digit '5' valid", r["valid"])

    # Test letter in E-J range
    first_14 = "27AAPFU0939F1G"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test("Position 14 'G' valid", r["valid"])

    # Test invalid value K
    first_14 = "27AAPFU0939F1K"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        "Position 14 'K' rejected",
        not r["valid"]
        and any("registration type" in e.lower() for e in r["errors"]),
    )

    # ------ Rule 5.1: Non-PAN-based types ------
    print("\n--- Rule 5.1: Non-PAN Type Detection ---")

    # UIN example
    r = validate_gstin("2717USA00046UNV")
    assert_test(
        "UIN detected (US Consulate Mumbai)",
        "UIN" in r["gstin_type"] and r["components"]["type_code"] == "UN",
    )

    # NRTP example — pos 15 is literal T, no check digit
    r = validate_gstin("0717IND00001NFT")
    assert_test(
        "NRTP detected",
        "NRTP" in r["gstin_type"],
    )

    # Temporary ID
    r = validate_gstin("072500001678TMP")
    assert_test(
        "Temporary ID detected",
        "Temporary" in r["gstin_type"],
    )

    # ------ Rule 6.1: Check digit ------
    print("\n--- Rule 6.1: Check Digit Validation ---")

    r = validate_gstin("27AAPFU0939F1ZV")
    assert_test(
        "Correct check digit V accepted",
        r["valid"] and r["components"]["check_digit_valid"],
    )

    r = validate_gstin("27AAPFU0939F1ZA")
    assert_test(
        "Wrong check digit A rejected",
        not r["valid"]
        and any("Check digit mismatch" in e for e in r["errors"]),
    )

    # Test with a known real-looking pattern
    first_14 = "29AAGCB7383J1Z"
    cd = compute_check_digit(first_14)
    r = validate_gstin(first_14 + cd)
    assert_test(
        f"Computed check digit '{cd}' validates correctly",
        r["valid"],
    )

    # ------ Combined: spaces + lowercase + valid GSTIN ------
    print("\n--- Combined Pre-processing ---")

    r = validate_gstin(" 27 aapfu 0939f 1zv ")
    assert_test(
        "Spaces + lowercase auto-corrected, GSTIN valid",
        r["valid"]
        and r["processed"] == "27AAPFU0939F1ZV"
        and len(r["warnings"]) == 2,
    )

    # ------ Check digit algorithm: worked example from SKILL.md ------
    print("\n--- Worked Example Verification ---")

    cd = compute_check_digit("27AAPFU0939F1Z")
    assert_test(
        "Worked example: 27AAPFU0939F1Z → check digit = V",
        cd == "V",
        f"Got '{cd}' instead of 'V'",
    )

    # ------ Additional known GSTINs for cross-verification ------
    print("\n--- Additional Cross-Verification ---")

    cd = compute_check_digit("27AASCS2460H1Z")
    r = validate_gstin("27AASCS2460H1Z" + cd)
    assert_test(f"27AASCS2460H1Z{cd} is valid", r["valid"])

    cd = compute_check_digit("29AAGCB7383J1Z")
    r = validate_gstin("29AAGCB7383J1Z" + cd)
    assert_test(f"29AAGCB7383J1Z{cd} is valid", r["valid"])

    # ------ Summary ------
    print("\n" + "=" * 70)
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        success = run_tests()
        sys.exit(0 if success else 1)

    elif len(sys.argv) > 1:
        gstin_input = sys.argv[1]
        result = validate_gstin(gstin_input)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        print("Usage:")
        print("  python gstin_validator.py <GSTIN>    — Validate a single GSTIN")
        print("  python gstin_validator.py --test     — Run unit tests")
        print()
        print("Example:")
        print("  python gstin_validator.py 27AAPFU0939F1ZV")
