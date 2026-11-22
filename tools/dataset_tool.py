# tools/dataset_tool.py
# TOOL 1: Dataset Inspection Tool
#
# This tool examines a Pandas DataFrame and returns detailed information
# about its structure, data types, missing values, and sample data.
# It is the FIRST tool the agent runs before any analysis.

import pandas as pd
import numpy as np
from utils.helpers import df_to_json_safe, make_json_serializable


def inspect_dataset(df: pd.DataFrame) -> dict:
    """
    Inspect a DataFrame and return comprehensive information about it.

    Parameters:
        df: The uploaded dataset as a Pandas DataFrame.

    Returns:
        A dictionary with all important dataset statistics and metadata.
    """

    # ── Basic shape ───────────────────────────────────────────────
    num_rows, num_cols = df.shape

    # ── Column data types ─────────────────────────────────────────
    # Convert dtype objects to plain strings for JSON serialization
    column_dtypes = {col: str(df[col].dtype) for col in df.columns}

    # ── Missing values ────────────────────────────────────────────
    missing_counts = df.isnull().sum()
    missing_values = {col: int(count) for col, count in missing_counts.items() if count > 0}
    total_missing = int(missing_counts.sum())

    # ── Duplicate rows ────────────────────────────────────────────
    duplicate_count = int(df.duplicated().sum())

    # ── Classify columns by their type ────────────────────────────
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Detect date columns: try to parse object columns as dates
    date_columns = []
    for col in categorical_columns:
        try:
            sample = df[col].dropna().head(10)
            pd.to_datetime(sample, infer_datetime_format=True)
            date_columns.append(col)
        except Exception:
            pass

    # Also include columns that are already datetime type
    datetime_typed = df.select_dtypes(include=["datetime64", "datetimetz"]).columns.tolist()
    date_columns = list(set(date_columns + datetime_typed))

    # ── Basic statistics for numeric columns ──────────────────────
    numeric_stats = {}
    for col in numeric_columns:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            numeric_stats[col] = {
                "mean": round(float(col_data.mean()), 2),
                "min": round(float(col_data.min()), 2),
                "max": round(float(col_data.max()), 2),
                "std": round(float(col_data.std()), 2),
            }

    # ── Sample rows ───────────────────────────────────────────────
    sample_rows = df_to_json_safe(df, max_rows=10)

    # ── Column names list ──────────────────────────────────────────
    column_names = df.columns.tolist()

    result = {
        "rows": num_rows,
        "columns": num_cols,
        "column_names": column_names,
        "column_dtypes": column_dtypes,
        "missing_values": missing_values,
        "total_missing": total_missing,
        "duplicates": duplicate_count,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_columns": date_columns,
        "numeric_stats": numeric_stats,
        "sample_rows": sample_rows,
    }

    return make_json_serializable(result)


def get_dataset_context_for_llm(df: pd.DataFrame, inspection: dict) -> str:
    """
    Create a short text summary of the dataset to send to the LLM.
    We keep this SHORT to avoid sending the entire dataset to the LLM.
    The LLM gets metadata only – not the full data.
    """
    lines = [
        f"Dataset has {inspection['rows']} rows and {inspection['columns']} columns.",
        f"Columns: {', '.join(inspection['column_names'])}",
        f"Numeric columns: {', '.join(inspection['numeric_columns'])}",
        f"Categorical columns: {', '.join(inspection['categorical_columns'])}",
        f"Date columns detected: {', '.join(inspection['date_columns'])}",
        f"Missing values: {inspection['total_missing']} total",
        f"Duplicate rows: {inspection['duplicates']}",
    ]

    # Add a small sample (5 rows max)
    if inspection.get("sample_rows"):
        sample = inspection["sample_rows"][:3]
        lines.append(f"Sample data (first 3 rows): {sample}")

    return "\n".join(lines)
