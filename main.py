"""
FILE: main.py

PURPOSE: Application entry point. Creates the PyQt5 application, shows
         the main window, and starts the event loop. This file does
         nothing else — all logic lives in other modules.

CONTAINS:
- main()  — Entry point function

DEPENDS ON:
- gui/main_window.py  → MainWindow

USED BY:
- (run directly) → python main.py

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — app entry point           | Phase 0 infrastructure setup       |
"""

# Python standard library
import sys

# Third-party libraries
from PyQt5.QtWidgets import QApplication

# This project's modules
from gui.main_window import MainWindow


def main() -> None:
    """
    WHAT: Creates the PyQt5 application and shows the main window.
    CALLED BY: Script execution (if __name__ == "__main__").
    """
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
