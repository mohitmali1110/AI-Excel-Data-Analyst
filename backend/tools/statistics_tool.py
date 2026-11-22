# tools/statistics_tool.py
# TOOL 4: Statistical Analysis Tool
#
# Performs statistical calculations on the dataset using Pandas and NumPy.
# Covers: mean, median, std, correlations, percentage change, growth rate, trends.

import pandas as pd
import numpy as np
from utils.helpers import make_json_serializable


def run_statistics(df: pd.DataFrame, analysis_type: str = "full") -> dict:
    """
    Run statistical analysis on the DataFrame.

    Parameters:
        df: The dataset DataFrame.
        analysis_type: Type of stat analysis to run.

    Returns:
        A dict with calculated statistics.
    """

    numeric_df = df.select_dtypes(include=np.number)

    if numeric_df.empty:
        return {"error": "No numeric columns found for statistical analysis."}

    results = {}

    # ── Descriptive statistics ─────────────────────────────────────
    desc = numeric_df.describe().round(4)
    results["descriptive_stats"] = make_json_serializable(desc.to_dict())

    # ── Column-by-column stats ─────────────────────────────────────
    column_stats = {}
    for col in numeric_df.columns:
        col_data = numeric_df[col].dropna()
        if len(col_data) == 0:
            continue
        column_stats[col] = {
            "mean": round(float(col_data.mean()), 4),
            "median": round(float(col_data.median()), 4),
            "std": round(float(col_data.std()), 4),
            "min": round(float(col_data.min()), 4),
            "max": round(float(col_data.max()), 4),
            "range": round(float(col_data.max() - col_data.min()), 4),
            "skewness": round(float(col_data.skew()), 4),
            "count": int(col_data.count()),
        }
    results["column_stats"] = make_json_serializable(column_stats)

    # ── Correlation matrix (if more than one numeric column) ───────
    if len(numeric_df.columns) > 1:
        corr_matrix = numeric_df.corr().round(4)
        results["correlation_matrix"] = make_json_serializable(corr_matrix.to_dict())

        # Find top correlations
        top_correlations = []
        cols = numeric_df.columns.tolist()
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                corr_val = corr_matrix.iloc[i, j]
                if not np.isnan(corr_val):
                    top_correlations.append({
                        "col1": cols[i],
                        "col2": cols[j],
                        "correlation": round(float(corr_val), 4),
                    })
        # Sort by absolute correlation value
        top_correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        results["top_correlations"] = make_json_serializable(top_correlations[:5])

    return results


def calculate_growth_rate(df: pd.DataFrame, date_col: str, value_col: str) -> dict:
    """
    Calculate period-over-period growth rate.

    Groups the data by month, then calculates month-over-month % change.

    Returns a dict with growth rates per period.
    """
    try:
        temp = df.copy()
        temp[date_col] = pd.to_datetime(temp[date_col], errors="coerce")
        temp = temp.dropna(subset=[date_col])
        temp["period"] = temp[date_col].dt.to_period("M").astype(str)

        # Sum value by period
        period_data = temp.groupby("period")[value_col].sum().reset_index()
        period_data.columns = ["period", "value"]
        period_data = period_data.sort_values("period")

        # Calculate growth rate
        period_data["growth_rate_pct"] = period_data["value"].pct_change() * 100
        period_data["change"] = period_data["value"].diff()

        # Overall growth: from first period to last
        if len(period_data) >= 2:
            first_val = float(period_data.iloc[0]["value"])
            last_val = float(period_data.iloc[-1]["value"])
            overall_growth = ((last_val - first_val) / first_val * 100) if first_val != 0 else 0
        else:
            overall_growth = 0

        return {
            "period_data": make_json_serializable(period_data.to_dict(orient="records")),
            "overall_growth_pct": round(overall_growth, 2),
            "latest_growth_pct": make_json_serializable(period_data.iloc[-1]["growth_rate_pct"]) if len(period_data) > 1 else None,
        }
    except Exception as e:
        return {"error": f"Growth rate calculation failed: {str(e)}"}


def detect_outliers(df: pd.DataFrame, column: str) -> dict:
    """
    Detect outliers in a numeric column using IQR method.

    Returns count and values of outliers.
    """
    try:
        data = df[column].dropna()
        Q1 = data.quantile(0.25)
        Q3 = data.quantile(0.75)
        IQR = Q3 - Q1

        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = data[(data < lower_bound) | (data > upper_bound)]

        return {
            "column": column,
            "Q1": round(float(Q1), 2),
            "Q3": round(float(Q3), 2),
            "IQR": round(float(IQR), 2),
            "lower_bound": round(float(lower_bound), 2),
            "upper_bound": round(float(upper_bound), 2),
            "outlier_count": int(len(outliers)),
            "outlier_values": make_json_serializable(outliers.tolist()[:20]),
        }
    except Exception as e:
        return {"error": f"Outlier detection failed: {str(e)}"}


def calculate_percentage_change(old_value: float, new_value: float) -> dict:
    """Calculate percentage change between two values."""
    if old_value == 0:
        return {"change_pct": None, "direction": "N/A", "note": "Old value is zero"}
    change = new_value - old_value
    change_pct = (change / old_value) * 100
    direction = "increase" if change > 0 else "decrease" if change < 0 else "no change"
    return {
        "old_value": round(old_value, 2),
        "new_value": round(new_value, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "direction": direction,
    }
