"""
FILE: config/settings.py

PURPOSE: Application-level settings — name, version, default paths, and
         environment configuration. These are values that may change between
         deployments but are NOT business rules.

CONTAINS:
- APP_NAME, APP_VERSION     — Displayed in GUI title bar
- DEFAULT_OUTPUT_DIR        — Where JSON files are saved by default
- GSTIN_VALIDATOR_PATH      — Path to the external GSTIN validator skill

DEPENDS ON:
- Nothing (root-level settings)

USED BY:
- gui/main_window.py        → window title, default save location
- core/gstin_validator.py    → locates the external validator module
- writers/json_writer.py     → default output directory

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — initial app settings      | Phase 0 infrastructure setup       |
"""

# Python standard library
import os
from pathlib import Path


# ---------------------------------------------------------------------------
# Application Identity
# ---------------------------------------------------------------------------

APP_NAME: str = "GST Refund JSON Generator"
APP_VERSION: str = "1.0.0"

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Project root is two levels up from this file (config/settings.py → project root)
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent

# Default output directory for generated JSON files.
# Users can change this via the GUI; this is just the starting default.
DEFAULT_OUTPUT_DIR: Path = PROJECT_ROOT / "output"

# Path to the external GSTIN validator skill.
# This file is maintained separately and imported at runtime to avoid
# duplicating 500+ lines of validation logic.
# Decision: Session 1 — import from .claude/skills/ rather than copying.
GSTIN_VALIDATOR_PATH: Path = PROJECT_ROOT / ".claude" / "skills" / "gst-gstin-validator"

# ---------------------------------------------------------------------------
# File Handling
# ---------------------------------------------------------------------------

# Supported input file extensions (lowercase, with dot)
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".xlsx",)

# Maximum rows to read from a data sheet (matches government VBA limit)
MAX_DATA_ROWS: int = 10_000
