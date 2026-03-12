"""
VBA Project Password Reset & Code Extraction Tool
===================================================
Resets the VBA project password in .xlsm / .xlsb / .xlam files to "123"
and extracts all VBA source code into a single organized text file.

Usage:
    python vba_password_reset.py                          (GUI file picker)
    python vba_password_reset.py input.xlsm               (CLI mode)
    python vba_password_reset.py input.xlsb -o output.xlsb (CLI with custom output)
    python vba_password_reset.py input.xlsm --no-extract   (skip code extraction)

Dependencies:
    pip install oletools

How it works:
    1. Treats the Excel file as a ZIP archive
    2. Locates xl/vbaProject.bin inside it
    3. Finds the DPB= password hash and replaces it with hash for "123"
    4. Writes the modified file as a new Excel file (same extension)
    5. Extracts all VBA code (modules, classes, forms, ThisWorkbook, Sheets)
       into a single text file saved alongside the output

After running, open the output file and enter "123" as the VBA password.
Then go to VBA Editor > Tools > VBA Project Properties > Protection
and uncheck "Lock project for viewing" to remove the password permanently.

Author : Adv. Sidhant Goyal / Goyal Tax Services Pvt. Ltd.
"""

import zipfile
import sys
import os
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

try:
    from oletools.olevba import VBA_Parser, TYPE_OLE, TYPE_OpenXML, TYPE_Word2003_XML, TYPE_MHTML
    OLETOOLS_AVAILABLE = True
except ImportError:
    OLETOOLS_AVAILABLE = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Known DPB hash corresponding to password "123"
KNOWN_HASH_123 = (
    "0A08A6B1B6CEB6CE4932B7CE4B63A66D37B84BA3D4BAD58A6B495254585A5D3D675777675D"
)

# Supported file extensions (all ZIP-based Office Open XML with VBA)
SUPPORTED_EXTENSIONS = (".xlsm", ".xlsb", ".xlam")

# File type filter for tkinter dialogs
FILE_TYPES = [
    ("Excel Macro-Enabled Files", "*.xlsm *.xlsb *.xlam"),
    ("Excel Macro-Enabled Workbook", "*.xlsm"),
    ("Excel Binary Workbook", "*.xlsb"),
    ("Excel Add-In", "*.xlam"),
    ("All Files", "*.*"),
]

# VBA object type labels for the text file
VBA_TYPE_LABELS = {
    "Module":       "Standard Module",
    "Class":        "Class Module",
    "MSForm":       "UserForm",
    "Document":     "Document Object (ThisWorkbook / Sheet)",
}

# Separator used in the extracted text file
SEP_MAJOR = "=" * 80
SEP_MINOR = "-" * 80


# ---------------------------------------------------------------------------
# Core Logic — Password Reset
# ---------------------------------------------------------------------------

def find_vba_bin_path(zip_ref: zipfile.ZipFile) -> str | None:
    """Locate the vbaProject.bin inside the zip (handles case variations)."""
    for name in zip_ref.namelist():
        if name.lower().endswith("vbaproject.bin"):
            return name
    return None


def reset_vba_password(vba_bin_data: bytes) -> bytes:
    """
    Find the DPB= line in vbaProject.bin and replace the hash
    with the known hash for password "123".
    """

    # Locate DPB= in the binary (case-insensitive scan)
    dpb_markers = [b"DPB=", b"dpb=", b"Dpb="]
    dpb_offset = -1

    for marker in dpb_markers:
        dpb_offset = vba_bin_data.find(marker)
        if dpb_offset != -1:
            break

    if dpb_offset == -1:
        raise ValueError(
            "Could not find 'DPB=' in vbaProject.bin.\n"
            "The VBA project may not be password-protected, "
            "or uses a different protection scheme."
        )

    # Find the opening and closing quotes after DPB=
    marker_len = 4  # len("DPB=")
    quote_start = vba_bin_data.find(b'"', dpb_offset + marker_len)
    if quote_start == -1:
        raise ValueError("Malformed DPB entry: no opening quote found.")

    quote_end = vba_bin_data.find(b'"', quote_start + 1)
    if quote_end == -1:
        raise ValueError("Malformed DPB entry: no closing quote found.")

    # Extract the original hash and prepare replacement
    original_hash = vba_bin_data[quote_start + 1 : quote_end]
    original_len = len(original_hash)
    new_hash = KNOWN_HASH_123.encode("ascii")

    print(f"  Found DPB= at byte offset {dpb_offset}")
    print(f"  Original hash length : {original_len} bytes")
    print(f"  New hash length      : {len(new_hash)} bytes")

    # Pad or trim to match original length exactly
    if len(new_hash) < original_len:
        new_hash = new_hash + b"0" * (original_len - len(new_hash))
        print(f"  Padded new hash to {len(new_hash)} bytes (added trailing zeros)")
    elif len(new_hash) > original_len:
        new_hash = new_hash[:original_len]
        print(
            f"  WARNING: Truncated new hash to {original_len} bytes. "
            "Result may not work correctly."
        )

    # Build the modified binary
    modified = (
        vba_bin_data[: quote_start + 1]
        + new_hash
        + vba_bin_data[quote_end:]
    )

    # Sanity check: file size must not change
    if len(modified) != len(vba_bin_data):
        raise RuntimeError(
            f"FATAL: Binary size mismatch! Original={len(vba_bin_data)}, "
            f"Modified={len(modified)}. Aborting to prevent file corruption."
        )

    return modified


# ---------------------------------------------------------------------------
# Core Logic — VBA Code Extraction
# ---------------------------------------------------------------------------

def extract_vba_code(file_path: str, txt_output_path: str) -> bool:
    """
    Extract all VBA source code from the Excel file using oletools.
    Writes a single text file with each module/object clearly labelled.

    Returns True if extraction succeeded, False otherwise.
    """

    if not OLETOOLS_AVAILABLE:
        print("\n  WARNING: 'oletools' is not installed. Skipping VBA extraction.")
        print("           Install it with:  pip install oletools")
        return False

    print(f"\n[VBA Extract] Parsing VBA project from: {Path(file_path).name}")

    try:
        vba_parser = VBA_Parser(file_path)
    except Exception as e:
        print(f"  ERROR: Could not parse VBA project: {e}")
        return False

    if not vba_parser.detect_vba_macros():
        print("  No VBA macros detected in the file.")
        vba_parser.close()
        return False

    # Collect all VBA modules
    modules_found = []
    for (filename, stream_path, vba_filename, vba_code) in vba_parser.extract_macros():
        raw_code = vba_code if vba_code else ""

        # Strip Attribute lines — these are internal VBA metadata
        # (e.g. Attribute VB_Name, VB_Exposed, VB_Base, VB_Creatable, etc.)
        # They never appear in the VBA Editor and are not user-written code.
        # We keep the raw code for classification but store cleaned code for output.
        cleaned_lines = [
            line for line in raw_code.splitlines()
            if not line.strip().startswith("Attribute ")
        ]
        # Remove leading/trailing blank lines left behind after stripping
        while cleaned_lines and not cleaned_lines[0].strip():
            cleaned_lines.pop(0)
        while cleaned_lines and not cleaned_lines[-1].strip():
            cleaned_lines.pop()

        cleaned_code = "\n".join(cleaned_lines)

        modules_found.append({
            "filename":     filename,
            "stream_path":  stream_path,
            "vba_filename": vba_filename,
            "vba_code_raw": raw_code,          # raw (used for classification)
            "vba_code":     cleaned_code,       # cleaned (used for output)
            "is_empty":     len(cleaned_code.strip()) == 0,
        })

    vba_parser.close()

    if not modules_found:
        print("  No VBA modules found.")
        return False

    # Classify modules by guessing type from stream path and raw content
    def classify_module(mod: dict) -> str:
        sp = mod["stream_path"].lower()
        vf = mod["vba_filename"].lower()
        raw = mod["vba_code_raw"]

        if "thisworkbook" in vf:
            return "Document"
        if "sheet" in vf and ("VB_Creatable = False" in raw
                              or "0{00020820" in raw):
            return "Document"
        if "userform" in sp or ".frm" in vf:
            return "MSForm"
        if "class" in sp or "VB_Creatable" in raw:
            if "VB_PredeclaredId = False" in raw:
                return "Class"
        # Check Attribute VB_Base for document-type objects
        if 'Attribute VB_Base = "0{00020820' in raw:
            return "Document"
        if 'Attribute VB_Base = "0{00020819' in raw:
            return "Document"
        # Default: standard module
        return "Module"

    # Build the text file content
    source_name = Path(file_path).name
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(SEP_MAJOR)
    lines.append(f"  VBA CODE EXTRACTION")
    lines.append(f"  Source   : {source_name}")
    lines.append(f"  Exported : {timestamp}")
    lines.append(f"  Modules  : {len(modules_found)} total "
                 f"({sum(1 for m in modules_found if not m['is_empty'])} with code, "
                 f"{sum(1 for m in modules_found if m['is_empty'])} empty)")
    lines.append(SEP_MAJOR)
    lines.append("")

    # --- Table of Contents ---
    lines.append("  TABLE OF CONTENTS")
    lines.append(SEP_MINOR)
    for i, mod in enumerate(modules_found, 1):
        mod_type = classify_module(mod)
        type_label = VBA_TYPE_LABELS.get(mod_type, mod_type)
        status = "" if not mod["is_empty"] else "  [empty]"
        lines.append(f"  {i:>3}. {mod['vba_filename']:<40} ({type_label}){status}")
    lines.append(SEP_MINOR)
    lines.append("")
    lines.append("")

    # --- Module Code Blocks (only modules with actual code) ---
    code_index = 0
    for i, mod in enumerate(modules_found, 1):
        if mod["is_empty"]:
            continue  # TOC already marks these as [empty] — no need to repeat

        code_index += 1
        mod_type = classify_module(mod)
        type_label = VBA_TYPE_LABELS.get(mod_type, mod_type)

        lines.append(SEP_MAJOR)
        lines.append(f"  [{code_index}] {mod['vba_filename']}")
        lines.append(f"  Type        : {type_label}")
        lines.append(f"  Stream Path : {mod['stream_path']}")
        lines.append(SEP_MAJOR)
        lines.append("")
        lines.append(mod["vba_code"])
        lines.append("")
        lines.append("")

    # --- Footer ---
    modules_with_code = sum(1 for m in modules_found if not m["is_empty"])
    lines.append(SEP_MAJOR)
    lines.append(f"  END OF VBA EXTRACTION")
    lines.append(f"  {modules_with_code} module(s) with code exported")
    lines.append(f"  {len(modules_found) - modules_with_code} empty module(s) listed in TOC only")
    lines.append(SEP_MAJOR)

    # Write the text file
    txt_content = "\n".join(lines)
    try:
        with open(txt_output_path, "w", encoding="utf-8") as f:
            f.write(txt_content)
        print(f"  Extracted {len(modules_found)} modules -> {Path(txt_output_path).name}")
        return True
    except Exception as e:
        print(f"  ERROR writing text file: {e}")
        return False


# ---------------------------------------------------------------------------
# Main Processing Pipeline
# ---------------------------------------------------------------------------

def process_file(input_path: str, output_path: str, extract: bool = True) -> dict:
    """
    Main pipeline: reset password + optionally extract VBA code.
    Returns a dict with status info for the GUI messagebox.
    """

    result = {
        "success": False,
        "output_path": output_path,
        "txt_path": None,
        "extract_ok": False,
        "error": None,
    }

    input_path = os.path.abspath(input_path)
    output_path = os.path.abspath(output_path)
    result["output_path"] = output_path

    if not os.path.isfile(input_path):
        result["error"] = f"File not found: {input_path}"
        print(f"ERROR: {result['error']}")
        return result

    ext = Path(input_path).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        print(f"WARNING: Expected {'/'.join(SUPPORTED_EXTENSIONS)}, got '{ext}'. "
              "Proceeding anyway...")

    print(f"\n{'='*60}")
    print(f"  VBA Project Password Reset & Code Extraction Tool")
    print(f"{'='*60}")
    print(f"  Input  : {input_path}")
    print(f"  Output : {output_path}")
    print()

    # ── Step 1: Open as ZIP and locate vbaProject.bin ──
    print("[1/5] Opening file as ZIP archive...")
    try:
        with zipfile.ZipFile(input_path, "r") as zin:
            vba_path = find_vba_bin_path(zin)
            if vba_path is None:
                result["error"] = ("No vbaProject.bin found inside the archive.\n"
                                   "This file may not contain VBA macros.")
                print(f"ERROR: {result['error']}")
                return result

            print(f"       Found: {vba_path}")

            # ── Step 2: Read and modify vbaProject.bin ──
            print(f"\n[2/5] Reading and patching {vba_path}...")
            vba_data = zin.read(vba_path)
            modified_vba = reset_vba_password(vba_data)
            print("       Password hash replaced successfully.")

            # ── Step 3: Rebuild the ZIP with the modified bin ──
            print(f"\n[3/5] Rebuilding archive -> {Path(output_path).name}...")
            with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zout:
                for item in zin.namelist():
                    if item == vba_path:
                        zout.writestr(item, modified_vba)
                    else:
                        zout.writestr(item, zin.read(item))

    except zipfile.BadZipFile:
        result["error"] = "Not a valid ZIP-based Excel file."
        print(f"ERROR: {result['error']}")
        return result
    except (ValueError, RuntimeError) as e:
        result["error"] = str(e)
        print(f"ERROR: {e}")
        return result

    result["success"] = True
    print("\n[4/5] Password reset complete.")

    # ── Step 4: Extract VBA code ──
    if extract:
        # Text file goes in the same folder as the output Excel file
        txt_path = str(Path(output_path).parent / f"{Path(output_path).stem}_vba_code.txt")
        result["txt_path"] = txt_path

        print(f"\n[5/5] Extracting VBA code...")
        # We extract from the ORIGINAL file (it's readable even with password
        # for code extraction via oletools), but we can also use the unlocked
        # output — either works since oletools reads the binary stream directly.
        extract_ok = extract_vba_code(output_path, txt_path)
        result["extract_ok"] = extract_ok

        if not extract_ok and OLETOOLS_AVAILABLE:
            # Fallback: try extracting from the original file
            print("  Retrying extraction from original file...")
            extract_ok = extract_vba_code(input_path, txt_path)
            result["extract_ok"] = extract_ok
    else:
        print("\n[5/5] VBA extraction skipped (--no-extract).")

    # ── Summary ──
    out_name = Path(output_path).name
    print(f"\n{'='*60}")
    print(f"  RESULTS")
    print(f"{'='*60}")
    print(f"  Unlocked file : {out_name}")
    if result["extract_ok"] and result["txt_path"]:
        print(f"  VBA code file : {Path(result['txt_path']).name}")
    print(f"\n  Next steps:")
    print(f"  1. Open '{out_name}' in Excel")
    print(f"  2. Go to Developer > Visual Basic (or Alt+F11)")
    print(f"  3. When prompted for VBA password, enter: 123")
    print(f"  4. To remove password permanently:")
    print(f"     Tools > VBA Project Properties > Protection")
    print(f"     Uncheck 'Lock project for viewing' > OK > Save")
    print(f"{'='*60}\n")

    return result


# ---------------------------------------------------------------------------
# GUI Mode (tkinter file dialogs)
# ---------------------------------------------------------------------------

def get_default_output(input_path: str) -> str:
    """Generate default output filename: <stem>_unlocked.<ext>"""
    p = Path(input_path)
    return str(p.parent / f"{p.stem}_unlocked{p.suffix}")


def run_gui():
    """Launch file picker dialogs and process the file."""

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    # ── Select input file ──
    input_path = filedialog.askopenfilename(
        title="Select the VBA-protected Excel file",
        filetypes=FILE_TYPES,
    )

    if not input_path:
        print("No input file selected. Exiting.")
        root.destroy()
        return

    print(f"Selected input: {input_path}")

    # Suggest default output name
    default_output = get_default_output(input_path)
    input_ext = Path(input_path).suffix.lower()

    ext_filter_map = {
        ".xlsm": [("Excel Macro-Enabled Workbook", "*.xlsm"), ("All Files", "*.*")],
        ".xlsb": [("Excel Binary Workbook", "*.xlsb"), ("All Files", "*.*")],
        ".xlam": [("Excel Add-In", "*.xlam"), ("All Files", "*.*")],
    }
    save_filetypes = ext_filter_map.get(input_ext, FILE_TYPES)

    # ── Select output file ──
    output_path = filedialog.asksaveasfilename(
        title="Save unlocked file as...",
        initialfile=Path(default_output).name,
        initialdir=str(Path(input_path).parent),
        defaultextension=input_ext,
        filetypes=save_filetypes,
    )

    if not output_path:
        print("No output file selected. Exiting.")
        root.destroy()
        return

    print(f"Selected output: {output_path}")

    # ── Process ──
    result = process_file(input_path, output_path, extract=True)

    # ── Show result dialog ──
    if result["success"]:
        msg_parts = [
            f"Unlocked file saved to:\n{result['output_path']}",
            f"\nOpen it in Excel and enter password: 123",
        ]
        if result["extract_ok"] and result["txt_path"]:
            msg_parts.append(
                f"\nVBA code extracted to:\n{Path(result['txt_path']).name}"
            )
        elif not OLETOOLS_AVAILABLE:
            msg_parts.append(
                "\nVBA code extraction skipped.\n"
                "Install oletools for this feature:\n"
                "  pip install oletools"
            )
        msg_parts.append(
            "\nTo remove password permanently:\n"
            "VBA Editor > Tools > Project Properties >\n"
            "Protection > Uncheck 'Lock project for viewing'"
        )
        messagebox.showinfo(
            "VBA Password Reset - Success",
            "\n".join(msg_parts),
        )
    else:
        messagebox.showerror(
            "VBA Password Reset - Error",
            f"Failed to process the file.\n\n{result.get('error', 'Unknown error')}\n\n"
            "Check the console output for details.",
        )

    root.destroy()


# ---------------------------------------------------------------------------
# CLI Mode (argparse)
# ---------------------------------------------------------------------------

def run_cli():
    """Parse command-line arguments and process the file."""

    parser = argparse.ArgumentParser(
        description="Reset VBA project password in Excel files to '123' and extract VBA code.",
        epilog=(
            "Supported formats: .xlsm, .xlsb, .xlam\n"
            "Requires: pip install oletools (for VBA extraction)\n"
            "After running, open the output file and enter '123' as the VBA password."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_file",
        nargs="?",
        default=None,
        help="Path to the password-protected Excel file (omit for GUI mode)",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <input>_unlocked.<ext>)",
        default=None,
    )
    parser.add_argument(
        "--no-extract",
        action="store_true",
        help="Skip VBA code extraction (only reset password)",
    )
    args = parser.parse_args()

    # No input file → launch GUI
    if args.input_file is None:
        run_gui()
        return

    # CLI mode
    if args.output is None:
        args.output = get_default_output(args.input_file)

    result = process_file(args.input_file, args.output, extract=not args.no_extract)
    if not result["success"]:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_cli()