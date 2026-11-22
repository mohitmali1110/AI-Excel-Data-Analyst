# tools/insight_tool.py
# TOOL 6: Insight Generation Tool
#
# Receives ACTUAL computed results from Pandas analysis tools,
# and generates human-readable key findings, insights, and recommendations.
# The LLM (if available) helps make the text natural.
# But numbers always come from Python — never invented.

from utils.helpers import make_json_serializable, format_number


def generate_insights(question: str, analysis_results: list, inspection: dict) -> dict:
    """
    Generate insights and recommendations from actual analysis results.

    Parameters:
        question: The user's original question.
        analysis_results: List of result dicts from Pandas/Stats tools.
        inspection: Dataset inspection result (has column info, etc.).

    Returns:
        {
            "insights": [...list of insight strings...],
            "recommendations": [...list of recommendation strings...],
            "key_findings": {...},
        }
    """
    insights = []
    recommendations = []
    key_findings = {}

    for result in analysis_results:
        if not result or "error" in result:
            continue

        rtype = result.get("type", "")

        # ── Monthly trend insights ────────────────────────────────
        if rtype == "monthly_trend":
            data = result.get("data", [])
            latest_change = result.get("latest_change_pct")
            latest_value = result.get("latest_value")
            prev_value = result.get("prev_value")
            value_col = result.get("value_col", "value")
            label = value_col.replace("_", " ").title()

            if latest_change is not None:
                direction = "increased" if latest_change > 0 else "decreased"
                abs_change = abs(round(latest_change, 1))
                insights.append(
                    f"{label} {direction} by {abs_change}% in the latest period "
                    f"(from {format_number(prev_value)} to {format_number(latest_value)})."
                )
                key_findings["latest_trend"] = {
                    "direction": direction,
                    "change_pct": round(latest_change, 2),
                    "latest_value": latest_value,
                    "prev_value": prev_value,
                }

                if latest_change < -10:
                    recommendations.append(
                        f"Investigate the significant drop in {label}. "
                        f"Check if there are seasonal factors, supply issues, or competition changes."
                    )
                elif latest_change > 10:
                    recommendations.append(
                        f"Capitalize on the positive growth trend in {label}. "
                        f"Consider what drove this growth and replicate the strategy."
                    )

            if data and len(data) >= 3:
                values = [row.get(f"total_{value_col}", row.get(value_col, 0)) for row in data]
                if values:
                    peak_idx = values.index(max(values))
                    peak_period = data[peak_idx].get("month", "unknown")
                    insights.append(
                        f"Peak {label} was in {peak_period}: {format_number(max(values))}."
                    )

        # ── Groupby sum insights ──────────────────────────────────
        elif rtype == "groupby_sum":
            top_item = result.get("top_item", {})
            bottom_item = result.get("bottom_item", {})
            group_col = result.get("group_col", "group")
            value_col = result.get("value_col", "value")
            data = result.get("data", [])

            agg_col = f"total_{value_col}"
            label = value_col.replace("_", " ").title()
            group_label = group_col.replace("_", " ").title()

            if top_item:
                top_name = top_item.get(group_col, "Unknown")
                top_val = top_item.get(agg_col, 0)
                insights.append(
                    f"'{top_name}' is the top {group_label} with total {label} of {format_number(top_val)}."
                )
                key_findings[f"top_{group_col}"] = {"name": top_name, "value": top_val}
                recommendations.append(
                    f"Study the strategy of '{top_name}' to understand what drives its performance."
                )

            if bottom_item:
                bottom_name = bottom_item.get(group_col, "Unknown")
                bottom_val = bottom_item.get(agg_col, 0)
                insights.append(
                    f"'{bottom_name}' has the lowest {label} of {format_number(bottom_val)}."
                )
                recommendations.append(
                    f"Investigate '{bottom_name}' — it may need targeted attention or resources."
                )

            # Calculate concentration (what % does top group hold?)
            if data and len(data) > 1:
                all_values = [row.get(agg_col, 0) for row in data]
                total = sum(all_values)
                if total > 0 and top_item:
                    top_pct = (top_item.get(agg_col, 0) / total) * 100
                    insights.append(
                        f"'{top_item.get(group_col)}' accounts for {round(top_pct, 1)}% of total {label}."
                    )

        # ── Groupby mean insights ─────────────────────────────────
        elif rtype == "groupby_mean":
            data = result.get("data", [])
            group_col = result.get("group_col", "group")
            value_col = result.get("value_col", "value")
            if data:
                avg_col = f"avg_{value_col}"
                sorted_data = sorted(data, key=lambda x: x.get(avg_col, 0), reverse=True)
                if sorted_data:
                    best = sorted_data[0]
                    insights.append(
                        f"'{best.get(group_col)}' has the highest average {value_col.replace('_', ' ')} "
                        f"of {format_number(best.get(avg_col, 0))}."
                    )

        # ── Column stats insights ─────────────────────────────────
        elif rtype == "column_sum":
            col = result.get("column", "value")
            val = result.get("value", 0)
            insights.append(f"Total {col.replace('_', ' ').title()}: {format_number(val)}.")
            key_findings[f"total_{col}"] = val

        elif rtype == "column_mean":
            col = result.get("column", "value")
            val = result.get("value", 0)
            insights.append(f"Average {col.replace('_', ' ').title()}: {format_number(val)}.")
            key_findings[f"average_{col}"] = val

        elif rtype == "column_max":
            col = result.get("column", "value")
            val = result.get("value", 0)
            insights.append(f"Maximum {col.replace('_', ' ').title()}: {format_number(val)}.")

        elif rtype == "column_min":
            col = result.get("column", "value")
            val = result.get("value", 0)
            insights.append(f"Minimum {col.replace('_', ' ').title()}: {format_number(val)}.")

        # ── Correlation insights ──────────────────────────────────
        elif rtype == "correlation":
            col1 = result.get("col1")
            col2 = result.get("col2")
            corr = result.get("correlation")
            interpretation = result.get("interpretation", "")
            if col1 and col2 and corr is not None:
                insights.append(
                    f"There is a {interpretation} ({round(corr, 3)}) between "
                    f"'{col1}' and '{col2}'."
                )
                if abs(corr) > 0.6:
                    recommendations.append(
                        f"The relationship between '{col1}' and '{col2}' is significant. "
                        f"Consider monitoring both together."
                    )

    # ── General recommendations if we have few ────────────────────
    if len(recommendations) < 2:
        recommendations.append(
            "Monitor key metrics regularly to spot trends early and make data-driven decisions."
        )
        recommendations.append(
            "Consider segmenting data by time period to understand seasonal patterns."
        )

    # ── FALLBACK: Generate insights from descriptive stats if none found ──
    # This activates when the dataset has no categorical/revenue columns
    # (e.g., a numeric-only dataset like URL features or sensor data)
    if len(insights) == 0:
        for result in analysis_results:
            if not result or "error" in result:
                continue
            rtype = result.get("type", "")

            # Extract from describe / describe_fallback
            if rtype in ("describe", "describe_fallback"):
                data = result.get("data", {})
                # data is { "col_name": {"mean": x, "std": y, ...} }
                for col, stats in list(data.items())[:5]:
                    if col == "count":
                        continue
                    mean_val = stats.get("mean")
                    std_val = stats.get("std")
                    max_val = stats.get("max")
                    min_val = stats.get("min")
                    if mean_val is not None:
                        insights.append(
                            f"{col.replace('_', ' ').title()}: mean = {format_number(mean_val)}, "
                            f"range = [{format_number(min_val)} – {format_number(max_val)}]."
                        )
                    if std_val is not None and mean_val is not None and mean_val != 0:
                        cv = abs(std_val / mean_val) * 100
                        if cv > 50:
                            insights.append(
                                f"{col.replace('_', ' ').title()} has high variability "
                                f"(CV = {round(cv, 1)}%) — values are spread widely."
                            )

            # Extract from statistics dict (run_statistics output)
            elif rtype == "statistics":
                col_stats = result.get("data", {}).get("column_stats", {})
                for col, stats in list(col_stats.items())[:4]:
                    mean_val = stats.get("mean")
                    max_val = stats.get("max")
                    min_val = stats.get("min")
                    if mean_val is not None:
                        insights.append(
                            f"{col.replace('_', ' ').title()}: average = {format_number(mean_val)}, "
                            f"max = {format_number(max_val)}, min = {format_number(min_val)}."
                        )
                        key_findings[f"avg_{col}"] = mean_val

                top_corr = result.get("data", {}).get("top_correlations", [])
                for corr_entry in top_corr[:2]:
                    c1 = corr_entry.get("col1", "")
                    c2 = corr_entry.get("col2", "")
                    cv = corr_entry.get("correlation", 0)
                    if abs(cv) > 0.5:
                        insights.append(
                            f"'{c1}' and '{c2}' have a {abs(round(cv, 2))} correlation — "
                            f"they move {'together' if cv > 0 else 'in opposite directions'}."
                        )
                        recommendations.append(
                            f"Investigate the relationship between '{c1}' and '{c2}' further."
                        )

        # If still no insights, produce a generic dataset summary
        if len(insights) == 0:
            numeric_cols = inspection.get("numeric_columns", [])
            cat_cols = inspection.get("categorical_columns", [])
            insights.append(
                f"Dataset contains {inspection.get('rows', 0):,} rows and "
                f"{inspection.get('columns', 0)} columns."
            )
            if numeric_cols:
                insights.append(f"Numeric columns available: {', '.join(numeric_cols[:5])}.")
            if cat_cols:
                insights.append(f"Categorical columns available: {', '.join(cat_cols[:5])}.")
            if inspection.get("total_missing", 0) > 0:
                insights.append(
                    f"Dataset has {inspection['total_missing']} missing values — "
                    f"consider imputation before modeling."
                )
            recommendations.append(
                "Try asking specific questions like 'what is the average [column name]?' "
                "or 'show distribution of [column name]'."
            )

    # Deduplicate insights and recommendations
    insights = list(dict.fromkeys(insights))
    recommendations = list(dict.fromkeys(recommendations))

    return {
        "insights": insights[:8],          # Cap at 8 insights
        "recommendations": recommendations[:5],  # Cap at 5 recommendations
        "key_findings": make_json_serializable(key_findings),
    }

