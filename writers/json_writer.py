"""
FILE: writers/json_writer.py

PURPOSE: Writes validated data as a JSON file with proper encoding and
         formatting. This is the final step in the pipeline: after reading
         the template and validating data, the generator builds a dict,
         and this module writes it to disk.

CONTAINS:
- write_json()  — Writes a Python dict to a .json file

DEPENDS ON:
- (Python standard library only — json, os)

USED BY:
- gui/main_window.py  → after generator produces the JSON dict

CHANGE LOG:
| Date       | Change                              | Why                                |
|------------|-------------------------------------|------------------------------------|
| 11-03-2026 | Created — JSON file writer          | Phase 0 infrastructure setup       |
"""

# Python standard library
import json
import os


def write_json(
    data: dict,
    output_path: str,
) -> dict:
    """
    WHAT:
        Writes a Python dictionary to a .json file with UTF-8 encoding
        and 2-space indentation. Creates parent directories if they
        don't exist.

    WHY ADDED:
        Every statement pipeline ends by writing a JSON file that can
        be uploaded to the GST Portal. This centralises file writing
        so that encoding and formatting are consistent across all 6
        statement types.

    CALLED BY:
        → gui/main_window.py → after generator produces the JSON dict

    EDGE CASES HANDLED:
        - Output directory doesn't exist → created automatically
        - File path is empty → returns error
        - Disk full or permission denied → caught and reported
        - Data is not serialisable → caught and reported

    PARAMETERS:
        data (dict):        The complete JSON structure to write.
        output_path (str):  Full path for the output .json file.

    RETURNS:
        dict: {
            "success": bool,
            "error": str or None,
            "file_path": str or None — the path written to, if successful
        }
    """
    if not output_path:
        return {"success": False, "error": "No output path provided.", "file_path": None}

    if not data:
        return {"success": False, "error": "No data to write.", "file_path": None}

    # Ensure parent directory exists
    parent_dir = os.path.dirname(output_path)
    if parent_dir:
        try:
            os.makedirs(parent_dir, exist_ok=True)
        except OSError as exc:
            return {
                "success": False,
                "error": f"Cannot create output folder: {exc}",
                "file_path": None,
            }

    try:
        with open(output_path, "w", encoding="utf-8") as json_file:
            json.dump(data, json_file, indent=2, ensure_ascii=False)

        return {"success": True, "error": None, "file_path": output_path}

    except PermissionError:
        return {
            "success": False,
            "error": f"Cannot write to '{output_path}' — the file or folder may be read-only or in use.",
            "file_path": None,
        }

    except TypeError as exc:
        return {
            "success": False,
            "error": f"Data contains values that cannot be saved as JSON: {exc}",
            "file_path": None,
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Unexpected error writing JSON file: {exc}",
            "file_path": None,
        }
