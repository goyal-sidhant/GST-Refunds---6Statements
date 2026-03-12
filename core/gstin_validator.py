"""
FILE: core/gstin_validator.py

PURPOSE: Thin wrapper that imports the validate_gstin() function from the
         external GSTIN validator skill at .claude/skills/gst-gstin-validator/.
         This avoids duplicating 500+ lines of Luhn Mod 36 checksum logic.

CONTAINS:
- validate_gstin()  — Re-exported from the external skill module

DEPENDS ON:
- .claude/skills/gst-gstin-validator/gstin_validator.py → the actual validator

USED BY:
- core/header_validator.py    → validates the applicant's GSTIN
- core/validators/stmt01a_validator.py → validates supplier/ISD GSTINs
- core/validators/stmt04_validator.py  → validates recipient GSTIN
- core/validators/stmt06_validator.py  → validates recipient GSTIN (B2B)

CHANGE LOG:
| Date       | Change                              | Why                                      |
|------------|-------------------------------------|------------------------------------------|
| 11-03-2026 | Created — import wrapper            | Decision: import from skill, don't copy  |
"""

# Python standard library
import sys
from pathlib import Path

from config.settings import GSTIN_VALIDATOR_PATH


def _ensure_skill_on_path() -> None:
    """
    WHAT: Adds the GSTIN validator skill directory to sys.path if not
          already present, so we can import from it.
    CALLED BY: Module-level code below (runs once at import time).
    """
    skill_dir = str(GSTIN_VALIDATOR_PATH)
    if skill_dir not in sys.path:
        sys.path.insert(0, skill_dir)


# Add the skill directory to the Python path at import time.
_ensure_skill_on_path()

# Now import the actual validator function.
# This gives us validate_gstin(gstin: str) -> dict with keys:
#   input, processed, valid, gstin_type, components, errors, warnings
try:
    from gstin_validator import validate_gstin  # type: ignore[import-untyped]
except ImportError as import_error:
    # If the skill file is missing, provide a clear error message rather
    # than letting the app crash with an obscure ImportError.
    def validate_gstin(gstin: object) -> dict:
        """
        WHAT: Fallback when the GSTIN validator skill is not found.
        RETURNS: Always returns invalid with an error explaining the issue.
        """
        return {
            "input": gstin,
            "processed": None,
            "valid": False,
            "gstin_type": "Unknown",
            "components": None,
            "errors": [
                f"GSTIN validator skill not found at: {GSTIN_VALIDATOR_PATH}. "
                f"Original error: {import_error}"
            ],
            "warnings": [],
        }
