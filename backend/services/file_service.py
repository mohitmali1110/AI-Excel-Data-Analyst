# services/file_service.py
# FILE SERVICE
#
# Handles file uploads: validation, saving, and reading CSV/XLSX files.

import os
import pandas as pd
from fastapi import UploadFile, HTTPException
from config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from utils.helpers import safe_filename, get_file_extension


def validate_and_save_file(file: UploadFile) -> dict:
    """
    Validate the uploaded file and save it to the uploads directory.

    Checks:
    - File extension is .csv or .xlsx
    - File size is within limit

    Returns:
        {
            "saved_filename": "...",     # The filename used on disk
            "original_filename": "...",  # Original name from user
            "file_type": "csv" or "xlsx",
            "filepath": "...",
        }
    """
    original_name = file.filename
    extension = get_file_extension(original_name)

    # Validate file type
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Only CSV and XLSX files are accepted."
        )

    # Read file content
    content = file.file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024*1024)} MB."
        )

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Save file with a safe name
    saved_name = safe_filename(original_name)
    filepath = os.path.join(UPLOAD_DIR, saved_name)

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(filepath, "wb") as f:
        f.write(content)

    return {
        "saved_filename": saved_name,
        "original_filename": original_name,
        "file_type": extension.lstrip("."),
        "filepath": filepath,
    }


def load_dataframe(filename: str) -> pd.DataFrame:
    """
    Load a saved file into a Pandas DataFrame.

    Parameters:
        filename: The saved filename (as returned by validate_and_save_file).

    Returns:
        A Pandas DataFrame.

    Raises:
        HTTPException if file not found or cannot be parsed.
    """
    filepath = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found. Please upload it again.")

    extension = get_file_extension(filename)

    try:
        if extension == ".csv":
            # Try common encodings
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV file with common encodings.")

        elif extension == ".xlsx":
            df = pd.read_excel(filepath, engine="openpyxl")

        else:
            raise ValueError(f"Unsupported file type: {extension}")

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Could not read file: {str(e)}. Make sure the file is a valid CSV or Excel file."
        )

    if df.empty:
        raise HTTPException(status_code=422, detail="The uploaded file contains no data.")

    return df


def list_uploaded_files() -> list:
    """Return a list of uploaded filenames."""
    if not os.path.exists(UPLOAD_DIR):
        return []
    return [f for f in os.listdir(UPLOAD_DIR) if get_file_extension(f) in ALLOWED_EXTENSIONS]
