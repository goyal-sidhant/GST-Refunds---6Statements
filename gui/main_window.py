"""
FILE: gui/main_window.py

PURPOSE: Main application window. Creates the tabbed layout, wires up
         signals from the Setup and Log tabs, and orchestrates the full
         pipeline: read template → validate → generate JSON → write file.

CONTAINS:
- MainWindow  — The single PyQt5 main window for the application

DEPENDS ON:
- gui/styles.py              → MAIN_STYLESHEET
- gui/setup_tab.py           → SetupTab widget
- gui/log_tab.py             → LogTab widget
- config/settings.py         → APP_NAME, APP_VERSION
- config/mappings.py         → ALL_STATEMENTS
- readers/template_reader.py → read_template()
- writers/json_writer.py     → write_json()
- writers/template_exporter.py → export_template()
- models/validation_result.py → ValidationResult

USED BY:
- main.py  → creates and shows this window

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — single-tab main window    | Phase 0 infrastructure setup       |
| 11-03-2026 | Refactored to multi-tab layout      | CR1: Dedicated tabs for expansion  |
| 11-03-2026 | Added Export Template button         | CR2: UX — users need the format    |
| 11-03-2026 | Split tabs into separate files       | CR3: Easier debugging per tab      |
"""

# Python standard library
import os
from pathlib import Path

# Third-party libraries
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QFileDialog,
    QTabWidget,
)
from PyQt5.QtCore import Qt

# This project's modules
from gui.styles import MAIN_STYLESHEET
from gui.setup_tab import SetupTab
from gui.log_tab import LogTab
from config.settings import APP_NAME, APP_VERSION
from config.mappings import ALL_STATEMENTS
from readers.template_reader import read_template
from writers.json_writer import write_json
from writers.template_exporter import export_template
from models.validation_result import ValidationResult


# Tab index constants (avoid magic numbers)
_TAB_SETUP = 0
_TAB_LOG = 1


class MainWindow(QMainWindow):
    """
    WHAT:
        The main application window with two tabs:
        1. Setup tab — statement type dropdown, Export Template button,
           file drag-and-drop zone, and Process JSON button.
        2. Processing Log tab — colour-coded log showing status, errors,
           warnings, and success messages.

        When the user clicks "Process JSON", the app automatically
        switches to the Processing Log tab to show real-time feedback.

    WHY ADDED:
        A tabbed layout separates setup from output, keeps the interface
        clean, and leaves room for future expansion (e.g., a Settings
        tab, a Help tab, or a Report tab).

    CALLED BY:
        → main.py → creates and shows this window
    """

    def __init__(self) -> None:
        """
        WHAT: Sets up the window layout and connects signals.
        """
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(750, 620)
        self.resize(850, 720)

        # Apply global stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Build the UI
        self._build_ui()

        # Connect tab signals to main window handlers
        self._connect_signals()

    def _build_ui(self) -> None:
        """
        WHAT: Creates the title, tab widget, and embeds the two tab widgets.
        CALLED BY: __init__()
        """
        # Central widget and main layout
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(12)

        # --- Title ---
        title_label = QLabel(APP_NAME)
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)

        # --- Tab widget ---
        self._tabs = QTabWidget()
        main_layout.addWidget(self._tabs, 1)

        # Create and add tabs
        self._setup_tab = SetupTab()
        self._log_tab = LogTab()
        self._tabs.addTab(self._setup_tab, "Setup")
        self._tabs.addTab(self._log_tab, "Processing Log")

    def _connect_signals(self) -> None:
        """
        WHAT: Connects signals from the two tabs to main window handlers.
        CALLED BY: __init__()
        """
        self._setup_tab.process_requested.connect(self._on_process_clicked)
        self._setup_tab.export_requested.connect(self._on_export_clicked)
        self._log_tab.back_requested.connect(self._on_back_clicked)

    # --- Signal handlers ---

    def _on_back_clicked(self) -> None:
        """
        WHAT: Switches back to the Setup tab.
        """
        self._tabs.setCurrentIndex(_TAB_SETUP)

    def _on_export_clicked(self) -> None:
        """
        WHAT:
            Called when the user clicks "Export Blank Template".
            Generates a blank .xlsx template for the selected statement
            type and saves it via a "Save As" dialog.
        """
        statement_code = self._setup_tab.get_statement_code()
        if not statement_code:
            return

        config = ALL_STATEMENTS.get(statement_code)
        if not config:
            return

        # Default filename
        default_name = f"GST_Refund_{statement_code}_Template.xlsx"

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Blank Template",
            default_name,
            "Excel Files (*.xlsx)",
        )

        if not output_path:
            return

        log = self._log_tab.log_panel
        result = export_template(config, output_path)

        if result["success"]:
            log.clear_log()
            log.add_success(f"Blank template saved: {result['file_path']}")
            log.add_info(
                "Fill in the Header sheet and data sheet(s), then come back "
                "to Setup, drop the file, and click Process JSON."
            )
            self._tabs.setCurrentIndex(_TAB_LOG)
        else:
            log.clear_log()
            log.add_error(result["error"])
            self._tabs.setCurrentIndex(_TAB_LOG)

    def _on_process_clicked(self) -> None:
        """
        WHAT:
            Called when the user clicks "Process JSON". Switches to the
            Processing Log tab, then runs the full pipeline:
            read → validate → generate → write.

        EDGE CASES HANDLED:
            - No statement selected → should not happen (button disabled)
            - No file selected → should not happen (button disabled)
            - Template read fails → errors shown in log
            - Validation fails → errors shown in log, no JSON generated
            - JSON write fails → error shown in log
        """
        # Get selected statement code and file path from the setup tab
        statement_code = self._setup_tab.get_statement_code()
        if not statement_code:
            return

        file_path = self._setup_tab.get_file_path()
        if not file_path:
            return

        # Get statement config
        config = ALL_STATEMENTS.get(statement_code)
        if not config:
            self._log_tab.log_panel.add_error(
                f"Unknown statement type: {statement_code}"
            )
            return

        log = self._log_tab.log_panel

        # Switch to the log tab so user sees real-time feedback
        log.clear_log()
        self._tabs.setCurrentIndex(_TAB_LOG)

        log.add_info(f"Processing: {config.display_name}")
        log.add_info(f"File: {os.path.basename(file_path)}")
        log.add_separator()

        # Disable Process button during processing
        self._setup_tab.set_process_enabled(False)

        # --- Step 1: Read template ---
        log.add_info("Step 1: Reading template...")
        validation_result = ValidationResult()
        read_output = read_template(file_path, config, validation_result)

        if not read_output["success"]:
            log.add_error("Template reading failed.")
            log.show_validation_report(
                validation_result.errors, validation_result.warnings,
            )
            self._setup_tab.set_process_enabled(True)
            return

        log.add_info("Template read successfully.")

        # --- Step 2: Validate ---
        log.add_info("Step 2: Validating data...")

        validator_func = self._get_validator(statement_code)
        if validator_func:
            validator_func(
                header=read_output["header"],
                sheets=read_output["sheets"],
                config=config,
                result=validation_result,
            )
        else:
            log.add_warning(
                f"No validator implemented yet for {statement_code}. "
                f"Skipping validation."
            )

        # Show validation results
        log.show_validation_report(
            validation_result.errors, validation_result.warnings,
        )

        # If there are errors, stop here (no JSON generated)
        if validation_result.has_errors:
            log.add_separator()
            log.add_error(
                f"JSON NOT generated — {validation_result.error_count} "
                f"error(s) must be fixed first."
            )
            self._setup_tab.set_process_enabled(True)
            return

        # --- Step 3: Generate JSON ---
        log.add_separator()
        log.add_info("Step 3: Generating JSON...")

        generator_func = self._get_generator(statement_code)
        if not generator_func:
            log.add_warning(
                f"No JSON generator implemented yet for {statement_code}."
            )
            self._setup_tab.set_process_enabled(True)
            return

        json_data = generator_func(
            header=read_output["header"],
            sheets=read_output["sheets"],
            config=config,
        )

        # --- Step 4: Write JSON file ---
        log.add_info("Step 4: Writing JSON file...")

        output_path = self._get_output_path(file_path, statement_code)
        if not output_path:
            log.add_info("File save cancelled by user.")
            self._setup_tab.set_process_enabled(True)
            return

        write_result = write_json(json_data, output_path)

        if write_result["success"]:
            log.add_separator()
            log.add_success(
                f"JSON file saved successfully!\n"
                f"Location: {write_result['file_path']}"
            )
        else:
            log.add_error(f"Failed to save JSON: {write_result['error']}")

        self._setup_tab.set_process_enabled(True)

    # --- Helper methods ---

    def _get_output_path(self, input_path: str, statement_code: str) -> str:
        """
        WHAT:
            Opens a "Save As" dialog so the user can choose where to
            save the JSON file. Default filename is based on the input
            file name with _JSON suffix.

        PARAMETERS:
            input_path (str): The original .xlsx file path.
            statement_code (str): e.g. "S03"

        RETURNS:
            str: The chosen output path, or empty string if cancelled.
        """
        input_name = Path(input_path).stem
        default_name = f"{input_name}_{statement_code}_output.json"

        # Use the input file's directory as the default save location
        default_dir = str(Path(input_path).parent)

        output_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            os.path.join(default_dir, default_name),
            "JSON Files (*.json)",
        )
        return output_path

    def _get_validator(self, statement_code: str):
        """
        WHAT:
            Returns the validate function for the given statement code.
            Returns None if the validator hasn't been built yet.

        CALLED BY: _on_process_clicked()

        RETURNS:
            Callable or None.
        """
        # Validators are imported here to avoid circular imports and to
        # allow incremental development (not all validators exist yet).
        try:
            if statement_code == "S01A":
                from core.validators.stmt01a_validator import validate_stmt01a
                return validate_stmt01a
            elif statement_code == "S02":
                from core.validators.stmt02_validator import validate_stmt02
                return validate_stmt02
            elif statement_code == "S03":
                from core.validators.stmt03_validator import validate_stmt03
                return validate_stmt03
            elif statement_code == "S04":
                from core.validators.stmt04_validator import validate_stmt04
                return validate_stmt04
            elif statement_code == "S05":
                from core.validators.stmt05_validator import validate_stmt05
                return validate_stmt05
            elif statement_code == "S06":
                from core.validators.stmt06_validator import validate_stmt06
                return validate_stmt06
        except ImportError:
            return None

        return None

    def _get_generator(self, statement_code: str):
        """
        WHAT:
            Returns the generate function for the given statement code.
            Returns None if the generator hasn't been built yet.

        CALLED BY: _on_process_clicked()

        RETURNS:
            Callable or None.
        """
        try:
            if statement_code == "S01A":
                from core.generators.stmt01a_generator import generate_stmt01a
                return generate_stmt01a
            elif statement_code == "S02":
                from core.generators.stmt02_generator import generate_stmt02
                return generate_stmt02
            elif statement_code == "S03":
                from core.generators.stmt03_generator import generate_stmt03
                return generate_stmt03
            elif statement_code == "S04":
                from core.generators.stmt04_generator import generate_stmt04
                return generate_stmt04
            elif statement_code == "S05":
                from core.generators.stmt05_generator import generate_stmt05
                return generate_stmt05
            elif statement_code == "S06":
                from core.generators.stmt06_generator import generate_stmt06
                return generate_stmt06
        except ImportError:
            return None

        return None
