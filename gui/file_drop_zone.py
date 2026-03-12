"""
FILE: gui/file_drop_zone.py

PURPOSE: Drag-and-drop widget for .xlsx files. The user can either drag
         a file onto this zone or click to open a file browser dialog.
         Emits a signal with the selected file path.

CONTAINS:
- FileDropZone  — QLabel-based drag-and-drop widget

DEPENDS ON:
- gui/styles.py          → COLOURS
- config/settings.py     → SUPPORTED_EXTENSIONS

USED BY:
- gui/main_window.py  → embedded in the main window layout

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — file drop zone widget     | Phase 0 infrastructure setup       |
"""

import os

from PyQt5.QtWidgets import QLabel, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

from gui.styles import COLOURS
from config.settings import SUPPORTED_EXTENSIONS


class FileDropZone(QLabel):
    """
    WHAT:
        A rectangular zone where the user can drag-and-drop an .xlsx file
        or click to open a file browser. When a valid file is selected,
        emits the file_selected signal with the full file path.

    WHY ADDED:
        Drag-and-drop is the easiest way for non-technical users to
        select a file. Click-to-browse is the fallback.

    CALLED BY:
        → gui/main_window.py → creates and connects to file_selected signal
    """

    # Signal emitted when a valid file is selected or dropped
    file_selected = pyqtSignal(str)

    # Display text
    _DEFAULT_TEXT = "Drag and drop your .xlsx template here\n\nor click to browse"
    _FILE_LOADED_TEXT = "File loaded:\n{filename}\n\nDrag another file or click to change"

    def __init__(self, parent=None) -> None:
        """
        WHAT: Creates the drop zone with drag-and-drop enabled.
        """
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(True)
        self.setMinimumHeight(120)
        self.setCursor(Qt.PointingHandCursor)
        self._current_file: str = ""
        self._apply_default_style()
        self.setText(self._DEFAULT_TEXT)

    def get_file_path(self) -> str:
        """
        WHAT: Returns the currently selected file path.
        CALLED BY: gui/main_window.py → when Process button is clicked.
        RETURNS: Full file path, or empty string if no file selected.
        """
        return self._current_file

    def clear_file(self) -> None:
        """
        WHAT: Resets the drop zone to its initial state.
        CALLED BY: gui/main_window.py → when statement type changes.
        """
        self._current_file = ""
        self._apply_default_style()
        self.setText(self._DEFAULT_TEXT)

    # --- Drag-and-drop event handlers ---

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        WHAT: Accepts the drag if it contains a file URL.
        """
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and self._is_valid_extension(urls[0].toLocalFile()):
                event.acceptProposedAction()
                self._apply_hover_style()
                return
        event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """
        WHAT: Restores normal style when drag leaves the zone.
        """
        if self._current_file:
            self._apply_loaded_style()
        else:
            self._apply_default_style()

    def dropEvent(self, event: QDropEvent) -> None:
        """
        WHAT: Processes the dropped file — validates extension and emits signal.
        """
        urls = event.mimeData().urls()
        if urls:
            file_path = urls[0].toLocalFile()
            if self._is_valid_extension(file_path):
                self._set_file(file_path)
                event.acceptProposedAction()
                return
        event.ignore()

    def mousePressEvent(self, event) -> None:
        """
        WHAT: Opens a file browser dialog when the zone is clicked.
        """
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "Select Excel Template",
                "",
                "Excel Files (*.xlsx)",
            )
            if file_path:
                self._set_file(file_path)

    # --- Internal helpers ---

    def _set_file(self, file_path: str) -> None:
        """
        WHAT: Updates the display and emits the file_selected signal.
        """
        self._current_file = file_path
        filename = os.path.basename(file_path)
        self.setText(self._FILE_LOADED_TEXT.format(filename=filename))
        self._apply_loaded_style()
        self.file_selected.emit(file_path)

    def _is_valid_extension(self, file_path: str) -> bool:
        """
        WHAT: Checks if the file has a supported extension (.xlsx).
        RETURNS: True if valid, False otherwise.
        """
        _, ext = os.path.splitext(file_path)
        return ext.lower() in SUPPORTED_EXTENSIONS

    def _apply_default_style(self) -> None:
        """
        WHAT: Applies the default (no file) visual style.
        """
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {COLOURS["drop_zone_border"]};
                border-radius: 8px;
                background-color: {COLOURS["surface"]};
                color: {COLOURS["text_secondary"]};
                font-size: 11pt;
                padding: 20px;
            }}
        """)

    def _apply_hover_style(self) -> None:
        """
        WHAT: Applies the hover (file being dragged over) visual style.
        """
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {COLOURS["primary"]};
                border-radius: 8px;
                background-color: {COLOURS["drop_zone_hover"]};
                color: {COLOURS["primary"]};
                font-size: 11pt;
                padding: 20px;
            }}
        """)

    def _apply_loaded_style(self) -> None:
        """
        WHAT: Applies the loaded (file selected) visual style.
        """
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {COLOURS["success"]};
                border-radius: 8px;
                background-color: {COLOURS["success_bg"]};
                color: {COLOURS["success"]};
                font-size: 11pt;
                padding: 20px;
            }}
        """)
