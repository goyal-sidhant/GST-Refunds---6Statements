"""
FILE: writers/template_exporter.py

PURPOSE: Generates blank Excel templates by running the user-provided
         generator scripts from .build-docs/context/. Each script creates
         a fully formatted .xlsx with Overview, Header, data sheets, and
         Help sheet in OctaSales design language.

CONTAINS:
- export_template()  — Runs the correct generator script and saves to user path

DEPENDS ON:
- .build-docs/context/Blueprint of Custom Excel Formats/generate_stmt*_template.py
- models/statement_config.py → StatementConfig

USED BY:
- gui/main_window.py  → called when "Export Template" button is clicked

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — basic template exporter   | CR2: Export Template button         |
| 11-03-2026 | Rewritten — calls user's generators | Use existing .build-docs scripts   |
"""

# Python standard library
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# This project's modules
from models.statement_config import StatementConfig
from config.settings import PROJECT_ROOT


# Maps statement code → (script filename, output filename the script creates)
_GENERATOR_SCRIPTS: dict[str, tuple[str, str]] = {
    "S01A": ("generate_stmt1a_template.py", "GST_Refund_Stmt1A_Template.xlsx"),
    "S02":  ("generate_stmt2_template.py",  "GST_Refund_Stmt2_Template.xlsx"),
    "S03":  ("generate_stmt3_template.py",  "GST_Refund_Stmt3_Template.xlsx"),
    "S04":  ("generate_stmt4_template.py",  "GST_Refund_Stmt4_Template.xlsx"),
    "S05":  ("generate_stmt5_template.py",  "GST_Refund_Stmt5_Template.xlsx"),
    "S06":  ("generate_stmt6_template.py",  "GST_Refund_Stmt6_Template.xlsx"),
}

# Directory where the generator scripts live
_SCRIPTS_DIR: Path = (
    PROJECT_ROOT / ".build-docs" / "context" / "Blueprint of Custom Excel Formats"
)


def export_template(config: StatementConfig, output_path: str) -> dict:
    """
    WHAT:
        Generates a blank .xlsx template by running the corresponding
        generator script from .build-docs/context/. The script runs in
        a temporary directory (so its os.getcwd()-based save works),
        then the output file is moved to the user's chosen path.

    WHY ADDED:
        Users need the correct Excel template before they can prepare
        data. The generator scripts already exist and produce perfectly
        formatted templates — we just call them.

    CALLED BY:
        → gui/main_window.py → when "Export Template" button is clicked

    PARAMETERS:
        config (StatementConfig): The statement configuration.
        output_path (str):        Full file path chosen by the user.

    RETURNS:
        dict: {
            "success": bool,
            "error": str or None,
            "file_path": str or None
        }
    """
    if not output_path:
        return {"success": False, "error": "No output path provided.", "file_path": None}

    # Look up the script for this statement
    script_info = _GENERATOR_SCRIPTS.get(config.code)
    if script_info is None:
        return {
            "success": False,
            "error": f"No template generator available for statement {config.code}.",
            "file_path": None,
        }

    script_name, output_name = script_info
    script_path = _SCRIPTS_DIR / script_name

    if not script_path.exists():
        return {
            "success": False,
            "error": f"Generator script not found: {script_path}",
            "file_path": None,
        }

    try:
        # Run the generator script in a temp directory so the .xlsx
        # lands there (scripts use os.getcwd() for output path)
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=temp_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                return {
                    "success": False,
                    "error": f"Template generator failed: {error_msg}",
                    "file_path": None,
                }

            generated_file = os.path.join(temp_dir, output_name)
            if not os.path.exists(generated_file):
                return {
                    "success": False,
                    "error": f"Generator ran but output file not found: {output_name}",
                    "file_path": None,
                }

            # Ensure parent directory of user's chosen path exists
            parent_dir = os.path.dirname(output_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # Move the generated file to the user's chosen location
            shutil.move(generated_file, output_path)

        return {"success": True, "error": None, "file_path": output_path}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Template generation timed out (30 seconds). Please try again.",
            "file_path": None,
        }
    except PermissionError:
        return {
            "success": False,
            "error": f"Cannot write to '{output_path}' — the file or folder may be read-only or in use.",
            "file_path": None,
        }
    except Exception as exc:
        return {
            "success": False,
            "error": f"Unexpected error creating template: {exc}",
            "file_path": None,
        }
