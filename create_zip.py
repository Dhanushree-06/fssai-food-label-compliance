"""
ZIP Package Creation Script
AI-Based Food Label Compliance Verification Platform

Packages the entire project into a clean, standalone ZIP distribution archive.
"""

import os
import zipfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRATCH_DIR = os.path.dirname(BASE_DIR)
ROOT_ZIP_PATH = os.path.join(SCRATCH_DIR, "fssai_compliance_platform.zip")
APP_ZIP_PATH = os.path.join(BASE_DIR, "fssai_compliance_platform.zip")


def create_project_zip():
    """Archives the fssai_compliance_platform folder into clean ZIP files."""
    exclude_dirs = {
        "__pycache__", ".pytest_cache", ".git", ".idea", ".vscode", "venv", "env"
    }
    exclude_exts = {".pyc", ".pyo", ".pyd"}

    print(f"Creating ZIP archive from: {BASE_DIR}")
    for out_zip in [ROOT_ZIP_PATH, APP_ZIP_PATH]:
        with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(BASE_DIR):
                # Filter out excluded directories in-place
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                for file in files:
                    if any(file.endswith(ext) for ext in exclude_exts):
                        continue
                    if file.endswith(".zip"):
                        continue
                    
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, SCRATCH_DIR)
                    zipf.write(full_path, rel_path)

        size_kb = round(os.path.getsize(out_zip) / 1024, 2)
        print(f"Generated ZIP: {out_zip} ({size_kb} KB)")

    return ROOT_ZIP_PATH


if __name__ == "__main__":
    create_project_zip()
