# tools/cleaning_tool.py
# TOOL 2: Data Cleaning Tool
#
# This tool safely cleans common data problems in a DataFrame.
# It does NOT blindly delete data — instead it applies conservative fixes
# and returns a log of everything it changed.

import pandas as pd
import numpy as np
from utils.helpers import make_json_serializable


def clean_dataset(df: pd.DataFrame) -> dict:
    """
    Clean the DataFrame and return both the cleaned DataFrame and a summary
    of all cleaning actions performed.

    Parameters:
        df: The original DataFrame.

    Returns:
        {
            "cleaned_df": <cleaned DataFrame>,
            "summary": { ... cleaning actions performed ... }
        }
    """

    # Work on a copy so we don't mutate the original
    cleaned = df.copy()
    summary = {
        "duplicates_removed": 0,
        "missing_values_handled": 0,
        "columns_renamed": [],
        "whitespace_stripped": [],
        "actions_taken": [],
    }

    # ── Step 1: Strip whitespace from column names ─────────────────
    original_cols = list(cleaned.columns)
    cleaned.columns = cleaned.columns.str.strip()
    # Replace spaces in column names with underscores for safety
    cleaned.columns = cleaned.columns.str.replace(r"\s+", "_", regex=True)
    new_cols = list(cleaned.columns)
    renamed = [(old, new) for old, new in zip(original_cols, new_cols) if old != new]
    if renamed:
        summary["columns_renamed"] = renamed
        summary["actions_taken"].append(f"Renamed {len(renamed)} column(s) to remove spaces.")

    # ── Step 2: Remove exact duplicate rows ───────────────────────
    before = len(cleaned)
    cleaned = cleaned.drop_duplicates()
    removed = before - len(cleaned)
    summary["duplicates_removed"] = removed
    if removed > 0:
        summary["actions_taken"].append(f"Removed {removed} duplicate row(s).")

    # ── Step 3: Handle missing values ─────────────────────────────
    total_missing_fixed = 0

    for col in cleaned.columns:
        missing_count = cleaned[col].isnull().sum()
        if missing_count == 0:
            continue

        missing_pct = missing_count / len(cleaned)

        # Only auto-fill if missing is less than 30% (conservative approach)
        if missing_pct < 0.30:
            if cleaned[col].dtype in [np.float64, np.float32, np.int64, np.int32]:
                # Fill numeric columns with the median (more robust than mean)
                median_val = cleaned[col].median()
                cleaned[col] = cleaned[col].fillna(median_val)
                total_missing_fixed += missing_count
                summary["actions_taken"].append(
                    f"Filled {missing_count} missing value(s) in '{col}' with median ({median_val:.2f})."
                )
            elif cleaned[col].dtype == object:
                # Fill string columns with 'Unknown'
                cleaned[col] = cleaned[col].fillna("Unknown")
                total_missing_fixed += missing_count
                summary["actions_taken"].append(
                    f"Filled {missing_count} missing value(s) in '{col}' with 'Unknown'."
                )
        else:
            # Too many missing values — do not auto-fill, just report
            summary["actions_taken"].append(
                f"Column '{col}' has {missing_pct:.0%} missing values — left as-is for manual review."
            )

    summary["missing_values_handled"] = total_missing_fixed

    # ── Step 4: Strip whitespace from string column values ─────────
    stripped_cols = []
    for col in cleaned.select_dtypes(include="object").columns:
        before_vals = cleaned[col].copy()
        cleaned[col] = cleaned[col].str.strip()
        if not cleaned[col].equals(before_vals):
            stripped_cols.append(col)

    if stripped_cols:
        summary["whitespace_stripped"] = stripped_cols
        summary["actions_taken"].append(
            f"Stripped leading/trailing whitespace from {len(stripped_cols)} column(s)."
        )

    # ── Step 5: Try to parse date-like string columns ──────────────
    for col in cleaned.select_dtypes(include="object").columns:
        # Only attempt if column name contains date-like keywords
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["date", "time", "month", "year", "day"]):
            try:
                cleaned[col] = pd.to_datetime(cleaned[col], infer_datetime_format=True, errors="coerce")
                summary["actions_taken"].append(f"Converted '{col}' to datetime type.")
            except Exception:
                pass

    if not summary["actions_taken"]:
        summary["actions_taken"].append("Dataset is already clean. No changes needed.")

    return {
        "cleaned_df": cleaned,
        "summary": make_json_serializable(summary),
    }
