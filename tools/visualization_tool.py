# tools/visualization_tool.py
# TOOL 5: Visualization Tool
#
# Generates charts using Matplotlib and saves them as PNG images.
# Returns the file path so the frontend can display them.
# Chart type is auto-selected based on data characteristics.

import os
import uuid
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Use non-interactive backend (no GUI window needed)
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle

from config import CHARTS_DIR
from utils.helpers import make_json_serializable

# Use a clean style
plt.rcParams.update({
    "figure.facecolor": "#1a1a2e",
    "axes.facecolor": "#16213e",
    "axes.edgecolor": "#4a4a8a",
    "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#c0c0c0",
    "ytick.color": "#c0c0c0",
    "text.color": "#e0e0e0",
    "grid.color": "#2a2a5a",
    "grid.alpha": 0.5,
})

CHART_COLORS = ["#6c63ff", "#f9ca24", "#ff6b6b", "#48dbfb", "#ff9ff3", "#54a0ff", "#5f27cd", "#01abc2"]


def generate_chart(df: pd.DataFrame, chart_type: str, params: dict) -> dict:
    """
    Generate a chart and save it as a PNG file.

    Parameters:
        df: The dataset DataFrame.
        chart_type: 'bar', 'line', 'histogram', 'scatter', 'boxplot', 'pie'
        params: Column names and other chart parameters.

    Returns:
        dict with chart metadata including the filename.
    """
    os.makedirs(CHARTS_DIR, exist_ok=True)

    # Create a unique filename for this chart
    chart_id = str(uuid.uuid4())[:8]
    filename = f"chart_{chart_type}_{chart_id}.png"
    filepath = os.path.join(CHARTS_DIR, filename)

    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        title = params.get("title", f"{chart_type.capitalize()} Chart")

        # ── Bar Chart ──────────────────────────────────────────────
        if chart_type == "bar":
            x_col = params.get("x_col")
            y_col = params.get("y_col")
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                data = df[[x_col, y_col]].dropna()
                # If many categories, take top 15
                if len(data) > 15:
                    data = data.nlargest(15, y_col)
                bars = ax.bar(
                    data[x_col].astype(str),
                    data[y_col],
                    color=CHART_COLORS[:len(data)],
                    edgecolor="#333",
                )
                ax.set_xlabel(x_col, fontsize=11)
                ax.set_ylabel(y_col, fontsize=11)
                ax.set_title(title, fontsize=14, pad=15)
                plt.xticks(rotation=45, ha="right")
                ax.grid(axis="y", alpha=0.4)

        # ── Line Chart ─────────────────────────────────────────────
        elif chart_type == "line":
            x_col = params.get("x_col")
            y_col = params.get("y_col")
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                data = df[[x_col, y_col]].dropna().sort_values(x_col)
                ax.plot(
                    data[x_col].astype(str),
                    data[y_col],
                    color=CHART_COLORS[0],
                    linewidth=2.5,
                    marker="o",
                    markersize=6,
                )
                ax.fill_between(
                    range(len(data)),
                    data[y_col],
                    alpha=0.15,
                    color=CHART_COLORS[0],
                )
                ax.set_xlabel(x_col, fontsize=11)
                ax.set_ylabel(y_col, fontsize=11)
                ax.set_title(title, fontsize=14, pad=15)
                step = max(1, len(data) // 8)
                ax.set_xticks(range(0, len(data), step))
                ax.set_xticklabels(
                    [str(v) for i, v in enumerate(data[x_col]) if i % step == 0],
                    rotation=45, ha="right"
                )
                ax.grid(alpha=0.4)

        # ── Histogram ──────────────────────────────────────────────
        elif chart_type == "histogram":
            col = params.get("column")
            if col and col in df.columns:
                data = df[col].dropna()
                ax.hist(data, bins=20, color=CHART_COLORS[0], edgecolor="#333", alpha=0.85)
                ax.set_xlabel(col, fontsize=11)
                ax.set_ylabel("Frequency", fontsize=11)
                ax.set_title(title, fontsize=14, pad=15)
                ax.grid(axis="y", alpha=0.4)

        # ── Scatter Plot ────────────────────────────────────────────
        elif chart_type == "scatter":
            x_col = params.get("x_col")
            y_col = params.get("y_col")
            if x_col and y_col and x_col in df.columns and y_col in df.columns:
                data = df[[x_col, y_col]].dropna()
                ax.scatter(data[x_col], data[y_col], color=CHART_COLORS[0], alpha=0.6, s=40)
                ax.set_xlabel(x_col, fontsize=11)
                ax.set_ylabel(y_col, fontsize=11)
                ax.set_title(title, fontsize=14, pad=15)
                ax.grid(alpha=0.4)

        # ── Box Plot ────────────────────────────────────────────────
        elif chart_type == "boxplot":
            cols = params.get("columns", [])
            cols = [c for c in cols if c in df.columns]
            if cols:
                data = df[cols].dropna()
                bp = ax.boxplot(
                    [data[c].values for c in cols],
                    patch_artist=True,
                    notch=False,
                )
                for patch, color in zip(bp["boxes"], CHART_COLORS):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                ax.set_xticklabels(cols, rotation=45, ha="right")
                ax.set_title(title, fontsize=14, pad=15)
                ax.grid(axis="y", alpha=0.4)

        # ── Pie Chart ───────────────────────────────────────────────
        elif chart_type == "pie":
            label_col = params.get("label_col")
            value_col = params.get("value_col")
            if label_col and value_col and label_col in df.columns and value_col in df.columns:
                data = df[[label_col, value_col]].dropna()
                data = data.nlargest(8, value_col)
                wedges, texts, autotexts = ax.pie(
                    data[value_col],
                    labels=data[label_col].astype(str),
                    colors=CHART_COLORS[:len(data)],
                    autopct="%1.1f%%",
                    startangle=90,
                )
                for text in texts:
                    text.set_color("#e0e0e0")
                for autotext in autotexts:
                    autotext.set_color("#e0e0e0")
                ax.set_title(title, fontsize=14, pad=15)

        plt.tight_layout()
        plt.savefig(filepath, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)

        return {
            "chart_type": chart_type,
            "title": title,
            "filename": filename,
            "filepath": filepath,
            "url": f"/charts/{filename}",  # URL the frontend uses to fetch this image
        }

    except Exception as e:
        plt.close("all")
        return {"error": f"Chart generation failed: {str(e)}", "chart_type": chart_type}


def auto_generate_charts(df: pd.DataFrame, analysis_results: list, inspection: dict) -> list:
    """
    Automatically decide what charts to generate based on analysis results and dataset structure.

    Returns a list of chart metadata dicts.
    """
    charts = []
    numeric_cols = inspection.get("numeric_columns", [])
    categorical_cols = inspection.get("categorical_columns", [])
    date_cols = inspection.get("date_columns", [])

    # Pick primary columns
    from tools.pandas_tool import _pick_primary_numeric, _pick_primary_category
    primary_numeric = _pick_primary_numeric(numeric_cols)
    primary_category = _pick_primary_category(categorical_cols)
    primary_date = date_cols[0] if date_cols else None

    for result in analysis_results:
        if not result or "error" in result:
            continue

        rtype = result.get("type", "")

        # ── Monthly trend → Line chart ────────────────────────────
        if rtype == "monthly_trend":
            data = result.get("data", [])
            if data:
                trend_df = pd.DataFrame(data)
                value_col = [c for c in trend_df.columns if c != "month"][0] if len(trend_df.columns) > 1 else None
                if value_col:
                    chart = generate_chart(
                        trend_df, "line",
                        {
                            "x_col": "month",
                            "y_col": value_col,
                            "title": f"Monthly {value_col.replace('total_', '').replace('_', ' ').title()} Trend",
                        }
                    )
                    if "error" not in chart:
                        charts.append(chart)

        # ── Group by sum → Bar chart ──────────────────────────────
        elif rtype == "groupby_sum":
            data = result.get("data", [])
            group_col = result.get("group_col")
            value_col = result.get("value_col")
            if data and group_col and value_col:
                grouped_df = pd.DataFrame(data)
                agg_col = f"total_{value_col}"
                if agg_col in grouped_df.columns:
                    chart = generate_chart(
                        grouped_df, "bar",
                        {
                            "x_col": group_col,
                            "y_col": agg_col,
                            "title": f"{value_col.replace('_', ' ').title()} by {group_col.replace('_', ' ').title()}",
                        }
                    )
                    if "error" not in chart:
                        charts.append(chart)

        # ── Value counts → Bar chart ──────────────────────────────
        elif rtype == "value_counts":
            data = result.get("data", [])
            col = result.get("column")
            if data and col:
                vc_df = pd.DataFrame(data)
                chart = generate_chart(
                    vc_df, "bar",
                    {
                        "x_col": "value",
                        "y_col": "count",
                        "title": f"Distribution of {col.replace('_', ' ').title()}",
                    }
                )
                if "error" not in chart:
                    charts.append(chart)

    # ── ROBUST FALLBACK: Always generate at least 2-3 charts ──────────────
    # This runs for ANY dataset, including numeric-only ones (no categories).
    numeric_cols_all = inspection.get("numeric_columns", [])

    # Histogram for the primary numeric column
    if primary_numeric and not any(
        c.get("title", "").startswith(f"Distribution of {primary_numeric.replace('_', ' ').title()}")
        for c in charts
    ):
        if len(charts) < 3:
            chart = generate_chart(
                df, "histogram",
                {
                    "column": primary_numeric,
                    "title": f"Distribution of {primary_numeric.replace('_', ' ').title()}",
                }
            )
            if "error" not in chart:
                charts.append(chart)

    # Add histograms for additional numeric columns if still need more charts
    for col in numeric_cols_all:
        if len(charts) >= 3:
            break
        if col == primary_numeric:
            continue
        chart = generate_chart(
            df, "histogram",
            {
                "column": col,
                "title": f"Distribution of {col.replace('_', ' ').title()}",
            }
        )
        if "error" not in chart:
            charts.append(chart)

    # Scatter plot between the top 2 numeric columns (great for correlation viz)
    if len(charts) < 2 and len(numeric_cols_all) >= 2:
        chart = generate_chart(
            df, "scatter",
            {
                "x_col": numeric_cols_all[0],
                "y_col": numeric_cols_all[1],
                "title": (
                    f"{numeric_cols_all[0].replace('_',' ').title()} vs "
                    f"{numeric_cols_all[1].replace('_',' ').title()}"
                ),
            }
        )
        if "error" not in chart:
            charts.append(chart)

    return charts

