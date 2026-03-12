"""
FILE: gui/setup_tab.py

PURPOSE: The Setup tab widget. Contains the statement type dropdown,
         Export Template button, file drag-and-drop zone, and Process
         JSON button. Emits signals when the user interacts — the main
         window listens and orchestrates the pipeline.

CONTAINS:
- SetupTab  — QWidget for the Setup tab

DEPENDS ON:
- gui/file_drop_zone.py   → FileDropZone widget
- config/mappings.py      → STATEMENT_CHOICES

USED BY:
- gui/main_window.py  → embedded as the first tab

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
    QLabel,
    QComboBox,
    QPushButton,
)
from PyQt5.QtCore import pyqtSignal

# This project's modules
from gui.file_drop_zone import FileDropZone
from config.mappings import STATEMENT_CHOICES


class SetupTab(QWidget):
    """
    WHAT:
        The Setup tab widget. Provides:
        1. Statement type dropdown (S01A–S06)
        2. Export Blank Template button
        3. Drag-and-drop file zone
        4. Process JSON button

        Emits signals for the main window to handle the actual logic.

    WHY ADDED:
        Separated from main_window.py for cleaner code and easier
        debugging — each tab is its own file.

    CALLED BY:
        → gui/main_window.py → adds this as the first tab
    """

    # Signals emitted to main window
    process_requested = pyqtSignal()
    export_requested = pyqtSignal()
    statement_changed = pyqtSignal()
    file_selected = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        """
        WHAT: Builds the Setup tab layout and connects internal signals.
        """
        super().__init__(parent)
        self._build_ui()
        self._connect_internal_signals()

    def _build_ui(self) -> None:
        """
        WHAT: Creates all widgets and arranges them in the tab layout.
        CALLED BY: __init__()
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(14)

        # --- Statement type selector row ---
        selector_layout = QHBoxLayout()
        selector_label = QLabel("Statement Type:")
        self._statement_combo = QComboBox()
        self._statement_combo.addItem("-- Select Statement Type --", "")
        for code, display_name in STATEMENT_CHOICES:
            self._statement_combo.addItem(display_name, code)
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self._statement_combo, 1)
        layout.addLayout(selector_layout)

        # --- Export Template button row ---
        export_layout = QHBoxLayout()
        export_layout.addStretch()
        self._export_button = QPushButton("Export Blank Template")
        self._export_button.setObjectName("secondary_button")
        self._export_button.setEnabled(False)
        self._export_button.setToolTip(
            "Save a blank Excel template for the selected statement type"
        )
        export_layout.addWidget(self._export_button)
        export_layout.addStretch()
        layout.addLayout(export_layout)

        # --- File drop zone ---
        self._drop_zone = FileDropZone()
        layout.addWidget(self._drop_zone, 1)

        # --- Process button ---
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self._process_button = QPushButton("Process JSON")
        self._process_button.setEnabled(False)
        button_layout.addWidget(self._process_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _connect_internal_signals(self) -> None:
        """
        WHAT: Connects widget signals to internal handlers and outgoing signals.
        CALLED BY: __init__()
        """
        self._statement_combo.currentIndexChanged.connect(self._on_statement_changed)
        self._drop_zone.file_selected.connect(self._on_file_selected)
        self._process_button.clicked.connect(self.process_requested.emit)
        self._export_button.clicked.connect(self.export_requested.emit)

    # --- Internal handlers ---

    def _on_statement_changed(self, index: int) -> None:
        """
        WHAT: Resets drop zone, updates button states, emits signal.
        """
        self._drop_zone.clear_file()
        has_statement = bool(self._statement_combo.currentData())
        self._export_button.setEnabled(has_statement)
        self._update_process_button()
        self.statement_changed.emit()

    def _on_file_selected(self, file_path: str) -> None:
        """
        WHAT: Updates Process button state and emits signal.
        """
        self._update_process_button()
        self.file_selected.emit(file_path)

    def _update_process_button(self) -> None:
        """
        WHAT: Enables Process button only when both statement and file are selected.
        """
        has_statement = bool(self._statement_combo.currentData())
        has_file = bool(self._drop_zone.get_file_path())
        self._process_button.setEnabled(has_statement and has_file)

    # --- Public accessors (used by main_window) ---

    def get_statement_code(self) -> str:
        """
        WHAT: Returns the currently selected statement code (e.g. "S03").
        RETURNS: Statement code string, or empty string if nothing selected.
        """
        return self._statement_combo.currentData() or ""

    def get_file_path(self) -> str:
        """
        WHAT: Returns the currently selected file path.
        RETURNS: Full file path, or empty string if no file selected.
        """
        return self._drop_zone.get_file_path()

    def set_process_enabled(self, enabled: bool) -> None:
        """
        WHAT: Enables or disables the Process button (used during processing).
        CALLED BY: gui/main_window.py → during pipeline execution.
        """
        self._process_button.setEnabled(enabled)
