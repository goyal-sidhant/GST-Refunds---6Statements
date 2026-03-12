"""
FILE: gui/log_panel.py

PURPOSE: Scrollable log panel widget that displays processing status,
         errors, and warnings in plain English with colour coding.
         This is the main feedback area where the user sees what happened
         after clicking "Process JSON".

CONTAINS:
- LogPanel  — QTextEdit-based widget with methods to add messages

DEPENDS ON:
- gui/styles.py  → COLOURS, LOG_TEMPLATES

USED BY:
- gui/main_window.py  → embedded in the main window layout

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — log panel widget          | Phase 0 infrastructure setup       |
"""

from PyQt5.QtWidgets import QTextEdit
from PyQt5.QtCore import Qt

from gui.styles import COLOURS, LOG_TEMPLATES


class LogPanel(QTextEdit):
    """
    WHAT:
        A read-only, scrollable text area that displays processing messages
        with colour-coded severity (errors in red, warnings in amber,
        success in green, info in blue).

    WHY ADDED:
        The user needs clear, plain-English feedback after processing.
        Errors must be easy to spot (red), warnings distinguishable
        (amber), and success clearly visible (green).

    CALLED BY:
        → gui/main_window.py → creates and embeds this widget

    EDGE CASES HANDLED:
        - Very long messages → word-wrapped automatically
        - Many messages → scrollbar appears, auto-scrolls to bottom
        - HTML special characters in messages → escaped
    """

    def __init__(self, parent=None) -> None:
        """
        WHAT: Creates the log panel with read-only settings.
        """
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(True)
        self.setMinimumHeight(200)

    def clear_log(self) -> None:
        """
        WHAT: Clears all messages from the log panel.
        CALLED BY: gui/main_window.py → at the start of each new processing run.
        """
        self.clear()

    def add_info(self, message: str) -> None:
        """
        WHAT: Adds an informational message (blue text).
        CALLED BY: gui/main_window.py → status updates during processing.
        """
        html = LOG_TEMPLATES["info"].format(
            color=COLOURS["info"],
            message=_escape_html(message),
        )
        self.append(html)
        self._scroll_to_bottom()

    def add_error(self, message: str) -> None:
        """
        WHAT: Adds an error message (red text, bold ERROR prefix).
        CALLED BY: gui/main_window.py → when validation errors are found.
        """
        html = LOG_TEMPLATES["error"].format(
            color=COLOURS["error"],
            message=_escape_html(message),
        )
        self.append(html)
        self._scroll_to_bottom()

    def add_warning(self, message: str) -> None:
        """
        WHAT: Adds a warning message (amber text, bold WARNING prefix).
        CALLED BY: gui/main_window.py → when validation warnings are found.
        """
        html = LOG_TEMPLATES["warning"].format(
            color=COLOURS["warning"],
            message=_escape_html(message),
        )
        self.append(html)
        self._scroll_to_bottom()

    def add_success(self, message: str) -> None:
        """
        WHAT: Adds a success message (green text, bold SUCCESS prefix).
        CALLED BY: gui/main_window.py → when JSON is generated successfully.
        """
        html = LOG_TEMPLATES["success"].format(
            color=COLOURS["success"],
            message=_escape_html(message),
        )
        self.append(html)
        self._scroll_to_bottom()

    def add_separator(self) -> None:
        """
        WHAT: Adds a horizontal line to visually separate processing runs.
        CALLED BY: gui/main_window.py → between processing runs.
        """
        self.append(LOG_TEMPLATES["separator"])

    def show_validation_report(self, errors: list, warnings: list) -> None:
        """
        WHAT:
            Displays all validation errors and warnings from a
            ValidationResult. Errors first, then warnings, with
            a summary count at the end.

        CALLED BY:
            → gui/main_window.py → after validation completes

        PARAMETERS:
            errors (list): List of ValidationEntry objects with severity ERROR.
            warnings (list): List of ValidationEntry objects with severity WARNING.
        """
        if errors:
            self.add_info(f"Found {len(errors)} error(s):")
            for entry in errors:
                self.add_error(entry.message)

        if warnings:
            self.add_info(f"Found {len(warnings)} warning(s):")
            for entry in warnings:
                self.add_warning(entry.message)

        if not errors and not warnings:
            self.add_success("All validations passed — no errors or warnings.")

    def _scroll_to_bottom(self) -> None:
        """
        WHAT: Scrolls the log panel to show the latest message.
        """
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def _escape_html(text: str) -> str:
    """
    WHAT: Escapes HTML special characters so they display correctly.
    CALLED BY: All LogPanel add_* methods.
    RETURNS: Escaped string safe for HTML display.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
