# utils/helpers.py
# Utility functions shared across the project.
# Simple, self-contained helper functions.

import os
import re
import json
import pandas as pd
from datetime import datetime


def safe_filename(filename: str) -> str:
    """
    Convert a filename to a safe version by removing special characters.
    Example: "my file (1).xlsx" → "my_file_1.xlsx"
    """
    # Replace spaces with underscores
    name = filename.replace(" ", "_")
    # Remove characters that are not alphanumeric, underscore, hyphen, or dot
    name = re.sub(r"[^\w\-.]", "", name)
    # Add a timestamp prefix to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{timestamp}_{name}"


def get_file_extension(filename: str) -> str:
    """Return the lowercase file extension including the dot. e.g. '.csv'"""
    return os.path.splitext(filename)[1].lower()


def df_to_json_safe(df: pd.DataFrame, max_rows: int = 10) -> list:
    """
    Convert a DataFrame to a JSON-serializable list of dicts.
    Handles NaN/NaT values by converting them to None.
    Limits to max_rows rows.
    """
    # Take only the first max_rows rows
    sample = df.head(max_rows).copy()

    # Convert timestamps to strings so JSON can serialize them
    for col in sample.select_dtypes(include=["datetime64", "datetimetz"]):
        sample[col] = sample[col].astype(str)

    # Replace NaN with None (which becomes null in JSON)
    records = sample.where(pd.notna(sample), other=None).to_dict(orient="records")
    return records


def format_number(value) -> str:
    """Format a number nicely. 1234567.89 → '1,234,567.89'"""
    try:
        if isinstance(value, float):
            return f"{value:,.2f}"
        elif isinstance(value, int):
            return f"{value:,}"
        else:
            return str(value)
    except Exception:
        return str(value)


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate long text with an ellipsis."""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


def make_json_serializable(obj):
    """
    Recursively convert an object to JSON-serializable types.
    Handles numpy types, pandas Timestamps, etc.
    """
    import numpy as np

    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return str(obj)
    elif isinstance(obj, float) and (obj != obj):  # NaN check
        return None
    else:
        return obj
