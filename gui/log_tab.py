"""
FILE: gui/log_tab.py

PURPOSE: The Processing Log tab widget. Contains the log panel that
         shows processing status, errors, warnings, and success messages,
         plus a "Back to Setup" button.

CONTAINS:
- LogTab  — QWidget for the Processing Log tab

DEPENDS ON:
- gui/log_panel.py  → LogPanel widget

USED BY:
- gui/main_window.py  → embedded as the second tab

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — extracted from main_window| CR3: Separate file per tab         |
"""

# Third-party libraries
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal

# This project's modules
from gui.log_panel import LogPanel


class LogTab(QWidget):
    """
    WHAT:
        The Processing Log tab widget. Provides:
        1. A colour-coded log panel (errors, warnings, success, info)
        2. A "Back to Setup" button

        The log panel is exposed as a public attribute so the main
        window can write messages to it directly.

    WHY ADDED:
        Separated from main_window.py for cleaner code and easier
        debugging — each tab is its own file.

    CALLED BY:
        → gui/main_window.py → adds this as the second tab
    """

    # Signal emitted when "Back to Setup" is clicked
    back_requested = pyqtSignal()

    def __init__(self, parent=None) -> None:
        """
        WHAT: Builds the Log tab layout.
        """
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        """
        WHAT: Creates the log panel and back button.
        CALLED BY: __init__()
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(8)

        # --- Log panel (public — main_window writes to it) ---
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel, 1)

        # --- Back to Setup button ---
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        back_button = QPushButton("Back to Setup")
        back_button.setObjectName("secondary_button")
        back_button.clicked.connect(self.back_requested.emit)
        back_layout.addWidget(back_button)
        back_layout.addStretch()
        layout.addLayout(back_layout)
