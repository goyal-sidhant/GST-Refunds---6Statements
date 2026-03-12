"""
FILE: models/validation_result.py

PURPOSE: Defines the data structures for collecting, categorising, and
         reporting validation errors and warnings. Every validator in the
         app adds its findings to a ValidationResult object, which the GUI
         then formats into plain-English messages for the user.

CONTAINS:
- ErrorSeverity      — Enum: ERROR (blocks JSON) vs WARNING (informational)
- ValidationEntry    — Single error or warning with location and message
- ValidationResult   — Collects all entries, provides summary and reporting

DEPENDS ON:
- Nothing (pure data structure)

USED BY:
- core/header_validator.py    → adds header-level errors
- core/template_enforcer.py   → adds template structure errors
- core/field_validators.py    → adds field-level errors
- core/tax_validators.py      → adds tax errors and rate warnings
- core/duplicate_detector.py  → adds duplicate errors
- core/brc_linker.py          → adds BRC coverage errors
- gui/log_panel.py            → reads entries for display

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — validation result model   | Phase 0 infrastructure setup       |
"""

from dataclasses import dataclass, field
from enum import Enum


class ErrorSeverity(Enum):
    """
    WHAT: Distinguishes blocking errors from informational warnings.
    ERROR blocks JSON generation. WARNING allows JSON but is displayed to user.
    """
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationEntry:
    """
    WHAT: A single validation finding — either an error or a warning.

    PARAMETERS:
        severity (ErrorSeverity): Whether this blocks JSON generation.
        message (str):            Plain-English message for the user.
        sheet (str):              Sheet name where the issue was found (or "Header").
        row (int):                Excel row number (0 for header-level issues).
        field (str):              Column/field name involved (optional).
        category (str):           Error category for grouping in reports
                                  (e.g., "document", "tax", "brc", "template").
    """
    severity: ErrorSeverity
    message: str
    sheet: str = ""
    row: int = 0
    field: str = ""
    category: str = "general"


@dataclass
class ValidationResult:
    """
    WHAT: Collects all validation entries (errors + warnings) from the
          entire validation pipeline for one file. Provides methods to
          check if JSON generation should proceed and to format reports.

    WHY ADDED:
        The "validate everything, then show all errors at once" pattern
        means we need a container that accumulates findings from multiple
        validators. The user fixes all issues in one pass rather than
        repeatedly re-running the tool.

    CALLED BY:
        → core/validators/*.py → add_error(), add_warning()
        → gui/main_window.py → has_errors(), format_report()
    """

    entries: list[ValidationEntry] = field(default_factory=list)

    def add_error(
        self,
        message: str,
        sheet: str = "",
        row: int = 0,
        field_name: str = "",
        category: str = "general",
    ) -> None:
        """
        WHAT: Adds a blocking error to the result.
        CALLED BY: All validators when a field fails validation.
        """
        self.entries.append(ValidationEntry(
            severity=ErrorSeverity.ERROR,
            message=message,
            sheet=sheet,
            row=row,
            field=field_name,
            category=category,
        ))

    def add_warning(
        self,
        message: str,
        sheet: str = "",
        row: int = 0,
        field_name: str = "",
        category: str = "general",
    ) -> None:
        """
        WHAT: Adds a non-blocking warning to the result.
        CALLED BY: Implicit rate checker, empty row handler.
        """
        self.entries.append(ValidationEntry(
            severity=ErrorSeverity.WARNING,
            message=message,
            sheet=sheet,
            row=row,
            field=field_name,
            category=category,
        ))

    @property
    def has_errors(self) -> bool:
        """
        WHAT: Returns True if any blocking errors exist.
        CALLED BY: gui/main_window.py → decides whether to generate JSON.
        """
        return any(e.severity == ErrorSeverity.ERROR for e in self.entries)

    @property
    def error_count(self) -> int:
        """WHAT: Returns the number of blocking errors."""
        return sum(1 for e in self.entries if e.severity == ErrorSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """WHAT: Returns the number of warnings."""
        return sum(1 for e in self.entries if e.severity == ErrorSeverity.WARNING)

    @property
    def errors(self) -> list[ValidationEntry]:
        """WHAT: Returns only blocking error entries."""
        return [e for e in self.entries if e.severity == ErrorSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationEntry]:
        """WHAT: Returns only warning entries."""
        return [e for e in self.entries if e.severity == ErrorSeverity.WARNING]

    def format_report(self) -> str:
        """
        WHAT: Formats all entries into a human-readable report string.
              Errors are listed first, then warnings. Each entry is on
              its own line with a prefix icon.

        RETURNS:
            str: Multi-line report text suitable for display in the GUI log panel.
        """
        lines: list[str] = []

        if self.has_errors:
            lines.append(f"✗ {self.error_count} error(s) found — JSON was NOT generated.\n")
            for entry in self.errors:
                lines.append(f"  ✗ {entry.message}")
        else:
            lines.append("✓ No errors found.\n")

        if self.warning_count > 0:
            lines.append(f"\n⚠ {self.warning_count} warning(s):\n")
            for entry in self.warnings:
                lines.append(f"  ⚠ {entry.message}")

        return "\n".join(lines)
