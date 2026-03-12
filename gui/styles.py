"""
FILE: gui/styles.py

PURPOSE: PyQt5 stylesheet constants for the application. All colours,
         fonts, spacing, and visual styling live here so that the look
         and feel can be changed in one place.

CONTAINS:
- MAIN_STYLESHEET    — Full application stylesheet
- COLOURS            — Named colour constants
- FONTS              — Font family and size constants

DEPENDS ON:
- (nothing — pure constants)

USED BY:
- gui/main_window.py   → applies MAIN_STYLESHEET to the app
- gui/log_panel.py     → uses COLOURS for error/warning/success highlighting
- gui/file_drop_zone.py → uses styles for the drop zone appearance

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — GUI styling constants     | Phase 0 infrastructure setup       |
"""

# --- Colour palette ---
COLOURS = {
    "background": "#F5F5F5",
    "surface": "#FFFFFF",
    "primary": "#1565C0",
    "primary_hover": "#0D47A1",
    "primary_text": "#FFFFFF",
    "text": "#212121",
    "text_secondary": "#757575",
    "border": "#E0E0E0",
    "error": "#D32F2F",
    "error_bg": "#FFEBEE",
    "warning": "#F57F17",
    "warning_bg": "#FFF8E1",
    "success": "#2E7D32",
    "success_bg": "#E8F5E9",
    "info": "#1565C0",
    "info_bg": "#E3F2FD",
    "drop_zone_border": "#90CAF9",
    "drop_zone_hover": "#E3F2FD",
    "disabled": "#BDBDBD",
}

# --- Font settings ---
FONTS = {
    "family": "Segoe UI",
    "size_normal": 10,
    "size_small": 9,
    "size_large": 12,
    "size_title": 14,
}

# --- Main application stylesheet ---
MAIN_STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLOURS["background"]};
    }}

    QLabel {{
        font-family: "{FONTS["family"]}";
        font-size: {FONTS["size_normal"]}pt;
        color: {COLOURS["text"]};
    }}

    QLabel#title_label {{
        font-size: {FONTS["size_title"]}pt;
        font-weight: bold;
        color: {COLOURS["primary"]};
    }}

    QComboBox {{
        font-family: "{FONTS["family"]}";
        font-size: {FONTS["size_normal"]}pt;
        padding: 6px 12px;
        border: 1px solid {COLOURS["border"]};
        border-radius: 4px;
        background-color: {COLOURS["surface"]};
        min-height: 20px;
    }}

    QComboBox:hover {{
        border-color: {COLOURS["primary"]};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}

    QPushButton {{
        font-family: "{FONTS["family"]}";
        font-size: {FONTS["size_normal"]}pt;
        font-weight: bold;
        padding: 8px 24px;
        border: none;
        border-radius: 4px;
        background-color: {COLOURS["primary"]};
        color: {COLOURS["primary_text"]};
        min-height: 20px;
    }}

    QPushButton:hover {{
        background-color: {COLOURS["primary_hover"]};
    }}

    QPushButton:disabled {{
        background-color: {COLOURS["disabled"]};
        color: {COLOURS["surface"]};
    }}

    QTextEdit {{
        font-family: "Consolas", "Courier New", monospace;
        font-size: {FONTS["size_small"]}pt;
        border: 1px solid {COLOURS["border"]};
        border-radius: 4px;
        background-color: {COLOURS["surface"]};
        padding: 8px;
    }}

    QGroupBox {{
        font-family: "{FONTS["family"]}";
        font-size: {FONTS["size_normal"]}pt;
        font-weight: bold;
        border: 1px solid {COLOURS["border"]};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 16px;
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
    }}

    QTabWidget::pane {{
        border: 1px solid {COLOURS["border"]};
        border-radius: 4px;
        background-color: {COLOURS["surface"]};
        padding: 12px;
    }}

    QTabBar::tab {{
        font-family: "{FONTS["family"]}";
        font-size: {FONTS["size_normal"]}pt;
        font-weight: bold;
        padding: 8px 20px;
        border: 1px solid {COLOURS["border"]};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        background-color: {COLOURS["background"]};
        color: {COLOURS["text_secondary"]};
        margin-right: 2px;
    }}

    QTabBar::tab:selected {{
        background-color: {COLOURS["surface"]};
        color: {COLOURS["primary"]};
        border-bottom: 2px solid {COLOURS["primary"]};
    }}

    QTabBar::tab:hover:!selected {{
        background-color: {COLOURS["info_bg"]};
    }}

    QPushButton#secondary_button {{
        background-color: {COLOURS["surface"]};
        color: {COLOURS["primary"]};
        border: 2px solid {COLOURS["primary"]};
    }}

    QPushButton#secondary_button:hover {{
        background-color: {COLOURS["info_bg"]};
    }}

    QPushButton#secondary_button:disabled {{
        background-color: {COLOURS["surface"]};
        color: {COLOURS["disabled"]};
        border-color: {COLOURS["disabled"]};
    }}
"""

# --- Log panel HTML templates ---
LOG_TEMPLATES = {
    "error": '<p style="color: {color}; margin: 2px 0;"><b>ERROR:</b> {message}</p>',
    "warning": '<p style="color: {color}; margin: 2px 0;"><b>WARNING:</b> {message}</p>',
    "success": '<p style="color: {color}; margin: 2px 0;"><b>SUCCESS:</b> {message}</p>',
    "info": '<p style="color: {color}; margin: 2px 0;">{message}</p>',
    "separator": '<hr style="border: 1px solid #E0E0E0; margin: 8px 0;">',
}
