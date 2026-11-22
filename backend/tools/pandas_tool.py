# tools/pandas_tool.py
# TOOL 3: Pandas Analysis Tool
#
# This tool performs the ACTUAL data analysis using Pandas.
# The LLM tells us WHAT to analyze; this tool does the real calculation.
# Results are never invented — they are computed from the real data.

import pandas as pd
import numpy as np
from utils.helpers import make_json_serializable


def run_pandas_analysis(df: pd.DataFrame, analysis_type: str, params: dict) -> dict:
    """
    Execute a specific Pandas analysis based on analysis_type.

    Parameters:
        df: The dataset DataFrame.
        analysis_type: What kind of analysis to run (e.g., 'groupby_sum').
        params: Parameters for the analysis (e.g., column names).

    Returns:
        A dict with the analysis results.
    """

    analysis_type = analysis_type.lower().strip()
    result = {}

    try:
        # ── Group by a column and aggregate ───────────────────────
        if analysis_type == "groupby_sum":
            group_col = params.get("group_col")
            value_col = params.get("value_col")
            if group_col and value_col and group_col in df.columns and value_col in df.columns:
                grouped = df.groupby(group_col)[value_col].sum().reset_index()
                grouped.columns = [group_col, f"total_{value_col}"]
                result = {
                    "type": "groupby_sum",
                    "group_col": group_col,
                    "value_col": value_col,
                    "data": make_json_serializable(grouped.to_dict(orient="records")),
                    "top_item": make_json_serializable(grouped.loc[grouped[f"total_{value_col}"].idxmax()].to_dict()),
                    "bottom_item": make_json_serializable(grouped.loc[grouped[f"total_{value_col}"].idxmin()].to_dict()),
                }

        elif analysis_type == "groupby_mean":
            group_col = params.get("group_col")
            value_col = params.get("value_col")
            if group_col and value_col and group_col in df.columns and value_col in df.columns:
                grouped = df.groupby(group_col)[value_col].mean().reset_index()
                grouped.columns = [group_col, f"avg_{value_col}"]
                result = {
                    "type": "groupby_mean",
                    "group_col": group_col,
                    "value_col": value_col,
                    "data": make_json_serializable(grouped.to_dict(orient="records")),
                }

        elif analysis_type == "groupby_count":
            group_col = params.get("group_col")
            value_col = params.get("value_col", df.columns[0])
            if group_col and group_col in df.columns:
                grouped = df.groupby(group_col)[value_col].count().reset_index()
                grouped.columns = [group_col, "count"]
                result = {
                    "type": "groupby_count",
                    "group_col": group_col,
                    "data": make_json_serializable(grouped.to_dict(orient="records")),
                }

        # ── Time series analysis ───────────────────────────────────
        elif analysis_type == "monthly_trend":
            date_col = params.get("date_col")
            value_col = params.get("value_col")
            if date_col and value_col and date_col in df.columns and value_col in df.columns:
                temp = df.copy()
                # Try to parse the date column
                temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
                temp = temp.dropna(subset=[date_col])
                temp["month"] = temp[date_col].dt.to_period("M").astype(str)
                monthly = temp.groupby("month")[value_col].sum().reset_index()
                monthly.columns = ["month", f"total_{value_col}"]

                # Calculate month-over-month change
                monthly["change"] = monthly[f"total_{value_col}"].diff()
                monthly["change_pct"] = monthly[f"total_{value_col}"].pct_change() * 100

                result = {
                    "type": "monthly_trend",
                    "date_col": date_col,
                    "value_col": value_col,
                    "data": make_json_serializable(monthly.to_dict(orient="records")),
                    "latest_month": monthly.iloc[-1]["month"] if len(monthly) > 0 else None,
                    "latest_value": make_json_serializable(monthly.iloc[-1][f"total_{value_col}"]) if len(monthly) > 0 else None,
                    "prev_value": make_json_serializable(monthly.iloc[-2][f"total_{value_col}"]) if len(monthly) > 1 else None,
                    "latest_change_pct": make_json_serializable(monthly.iloc[-1]["change_pct"]) if len(monthly) > 1 else None,
                }

        # ── Simple column aggregations ─────────────────────────────
        elif analysis_type == "column_sum":
            col = params.get("column")
            if col and col in df.columns:
                result = {
                    "type": "column_sum",
                    "column": col,
                    "value": make_json_serializable(df[col].sum()),
                }

        elif analysis_type == "column_mean":
            col = params.get("column")
            if col and col in df.columns:
                result = {
                    "type": "column_mean",
                    "column": col,
                    "value": make_json_serializable(df[col].mean()),
                }

        elif analysis_type == "column_max":
            col = params.get("column")
            if col and col in df.columns:
                max_val = df[col].max()
                max_idx = df[col].idxmax()
                result = {
                    "type": "column_max",
                    "column": col,
                    "value": make_json_serializable(max_val),
                    "row": make_json_serializable(df.loc[max_idx].to_dict()),
                }

        elif analysis_type == "column_min":
            col = params.get("column")
            if col and col in df.columns:
                min_val = df[col].min()
                min_idx = df[col].idxmin()
                result = {
                    "type": "column_min",
                    "column": col,
                    "value": make_json_serializable(min_val),
                    "row": make_json_serializable(df.loc[min_idx].to_dict()),
                }

        elif analysis_type == "value_counts":
            col = params.get("column")
            if col and col in df.columns:
                vc = df[col].value_counts().head(15)
                result = {
                    "type": "value_counts",
                    "column": col,
                    "data": make_json_serializable(
                        [{"value": k, "count": v} for k, v in vc.items()]
                    ),
                }

        elif analysis_type == "top_n":
            sort_col = params.get("sort_col")
            n = params.get("n", 5)
            if sort_col and sort_col in df.columns:
                top = df.nlargest(int(n), sort_col)
                result = {
                    "type": "top_n",
                    "sort_col": sort_col,
                    "n": n,
                    "data": make_json_serializable(top.to_dict(orient="records")),
                }

        elif analysis_type == "filter_compare":
            # Compare two groups in the data
            group_col = params.get("group_col")
            value_col = params.get("value_col")
            if group_col and value_col and group_col in df.columns and value_col in df.columns:
                comparison = df.groupby(group_col)[value_col].agg(["sum", "mean", "count"]).reset_index()
                comparison.columns = [group_col, "total", "average", "count"]
                result = {
                    "type": "filter_compare",
                    "group_col": group_col,
                    "value_col": value_col,
                    "data": make_json_serializable(comparison.to_dict(orient="records")),
                }

        elif analysis_type == "correlation":
            col1 = params.get("col1")
            col2 = params.get("col2")
            if col1 and col2 and col1 in df.columns and col2 in df.columns:
                corr = df[col1].corr(df[col2])
                result = {
                    "type": "correlation",
                    "col1": col1,
                    "col2": col2,
                    "correlation": make_json_serializable(corr),
                    "interpretation": interpret_correlation(corr),
                }

        # ── Full describe (fallback for general questions) ─────────
        elif analysis_type == "describe":
            numeric_df = df.select_dtypes(include=np.number)
            if not numeric_df.empty:
                desc = numeric_df.describe().round(2)
                result = {
                    "type": "describe",
                    "data": make_json_serializable(desc.to_dict()),
                }

        if not result:
            # If nothing matched, return a simple describe as fallback
            numeric_df = df.select_dtypes(include=np.number)
            if not numeric_df.empty:
                desc = numeric_df.describe().round(2)
                result = {
                    "type": "describe_fallback",
                    "message": f"Analysis type '{analysis_type}' not fully matched. Showing descriptive stats.",
                    "data": make_json_serializable(desc.to_dict()),
                }

    except Exception as e:
        result = {"error": f"Pandas analysis failed: {str(e)}", "type": analysis_type}

    return result


def interpret_correlation(corr: float) -> str:
    """Turn a correlation number into a human-readable description."""
    if corr is None or (isinstance(corr, float) and corr != corr):
        return "Could not calculate"
    abs_corr = abs(corr)
    direction = "positive" if corr >= 0 else "negative"
    if abs_corr >= 0.8:
        strength = "very strong"
    elif abs_corr >= 0.6:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "very weak"
    return f"{strength} {direction} correlation"


def auto_analyze(df: pd.DataFrame, question: str, inspection: dict) -> list:
    """
    Automatically decide what Pandas analyses to run based on the question
    and dataset columns. This is the FALLBACK when no LLM is available.

    Returns a list of analysis result dicts.
    """
    question_lower = question.lower()
    results = []

    numeric_cols = inspection.get("numeric_columns", [])
    categorical_cols = inspection.get("categorical_columns", [])
    date_cols = inspection.get("date_columns", [])

    # Pick the primary numeric column (prefer Revenue, Sales, Amount, etc.)
    primary_numeric = _pick_primary_numeric(numeric_cols)
    primary_category = _pick_primary_category(categorical_cols)
    primary_date = date_cols[0] if date_cols else None

    # ── Trend / time questions ────────────────────────────────────
    if any(w in question_lower for w in ["trend", "month", "time", "over time", "decrease", "increase", "growth"]):
        if primary_date and primary_numeric:
            r = run_pandas_analysis(df, "monthly_trend", {"date_col": primary_date, "value_col": primary_numeric})
            results.append(r)

    # ── Highest / best / top ──────────────────────────────────────
    if any(w in question_lower for w in ["highest", "most", "top", "best", "maximum", "max"]):
        if primary_category and primary_numeric:
            r = run_pandas_analysis(df, "groupby_sum", {"group_col": primary_category, "value_col": primary_numeric})
            results.append(r)
        elif primary_numeric:
            r = run_pandas_analysis(df, "column_max", {"column": primary_numeric})
            results.append(r)

    # ── Lowest / worst / minimum ──────────────────────────────────
    if any(w in question_lower for w in ["lowest", "least", "bottom", "worst", "minimum", "min"]):
        if primary_category and primary_numeric:
            r = run_pandas_analysis(df, "groupby_sum", {"group_col": primary_category, "value_col": primary_numeric})
            results.append(r)
        elif primary_numeric:
            r = run_pandas_analysis(df, "column_min", {"column": primary_numeric})
            results.append(r)

    # ── Average / mean ────────────────────────────────────────────
    if any(w in question_lower for w in ["average", "mean", "avg"]):
        if primary_numeric:
            r = run_pandas_analysis(df, "column_mean", {"column": primary_numeric})
            results.append(r)

    # ── Total / sum ───────────────────────────────────────────────
    if any(w in question_lower for w in ["total", "sum", "overall"]):
        if primary_numeric:
            r = run_pandas_analysis(df, "column_sum", {"column": primary_numeric})
            results.append(r)

    # ── Category / region / group comparison ──────────────────────
    if any(w in question_lower for w in ["category", "region", "group", "by", "compare", "each"]):
        if primary_category and primary_numeric:
            r = run_pandas_analysis(df, "groupby_sum", {"group_col": primary_category, "value_col": primary_numeric})
            results.append(r)

    # ── Why / reason (deeper analysis) ───────────────────────────
    if any(w in question_lower for w in ["why", "reason", "cause", "explain"]):
        # Run analysis by every categorical column
        for cat_col in categorical_cols[:3]:  # Limit to first 3 categories
            if primary_numeric:
                r = run_pandas_analysis(df, "groupby_sum", {"group_col": cat_col, "value_col": primary_numeric})
                results.append(r)
        if primary_date and primary_numeric:
            r = run_pandas_analysis(df, "monthly_trend", {"date_col": primary_date, "value_col": primary_numeric})
            results.append(r)

    # ── Distribution / histogram ──────────────────────────────────
    if any(w in question_lower for w in ["distribution", "spread", "histogram"]):
        if primary_numeric:
            r = run_pandas_analysis(df, "describe", {})
            results.append(r)

    # ── Fallback: always run a describe if nothing matched ────────
    if not results:
        r = run_pandas_analysis(df, "describe", {})
        results.append(r)
        if primary_category and primary_numeric:
            r2 = run_pandas_analysis(df, "groupby_sum", {"group_col": primary_category, "value_col": primary_numeric})
            results.append(r2)

    return results


def _pick_primary_numeric(numeric_cols: list) -> str:
    """Pick the most relevant numeric column for analysis."""
    preferred = ["revenue", "sales", "amount", "price", "profit", "income", "quantity", "value"]
    for pref in preferred:
        for col in numeric_cols:
            if pref in col.lower():
                return col
    return numeric_cols[0] if numeric_cols else None


def _pick_primary_category(categorical_cols: list) -> str:
    """Pick the most relevant categorical column."""
    preferred = ["category", "region", "product", "type", "segment", "department"]
    for pref in preferred:
        for col in categorical_cols:
            if pref in col.lower():
                return col
    return categorical_cols[0] if categorical_cols else None
