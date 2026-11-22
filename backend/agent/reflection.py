# agent/reflection.py
# TOOL 7: Result Evaluation / Reflection Module
#
# After analysis is done, the agent REFLECTS on whether the results
# are sufficient to answer the user's question.
# If not, it decides what additional analysis is needed.
# This reflection loop is the CORE of the agentic behavior.

import json
from services.llm_service import call_llm, is_llm_available


def evaluate_result(question: str, results: list, iteration: int = 1) -> dict:
    """
    Evaluate whether the current analysis results sufficiently answer the question.

    Parameters:
        question: The user's original question.
        results: List of analysis result dicts collected so far.
        iteration: Which reflection loop iteration this is (1, 2, or 3).

    Returns:
        {
            "sufficient": True/False,
            "reason": "Why the result is/isn't sufficient",
            "additional_analysis": ["analysis_type_1", ...] if not sufficient
        }
    """

    # On the 3rd loop, always say sufficient to avoid infinite loops
    if iteration >= 3:
        return {
            "sufficient": True,
            "reason": "Maximum reflection loops reached. Generating final answer from available results.",
            "additional_analysis": [],
        }

    # Check if we have any meaningful results
    if not results:
        return {
            "sufficient": False,
            "reason": "No analysis results available yet.",
            "additional_analysis": ["pandas_analysis", "statistics"],
        }

    # Filter out error results
    valid_results = [r for r in results if r and "error" not in r]
    if not valid_results:
        return {
            "sufficient": False,
            "reason": "All analysis attempts returned errors. Trying different approach.",
            "additional_analysis": ["describe_stats"],
        }

    # Try LLM-based evaluation
    if is_llm_available():
        try:
            evaluation = _llm_evaluate(question, valid_results)
            if evaluation:
                return evaluation
        except Exception:
            pass

    # Fallback: rule-based evaluation
    return _rule_based_evaluate(question, valid_results, iteration)


def _llm_evaluate(question: str, results: list) -> dict:
    """Use LLM to evaluate if results are sufficient."""

    # Prepare a compact summary of results (don't send all raw data)
    result_summary = []
    for r in results[:4]:  # Max 4 results to keep prompt short
        rtype = r.get("type", "unknown")
        summary_parts = [f"Type: {rtype}"]
        if "top_item" in r:
            summary_parts.append(f"Top: {r['top_item']}")
        if "latest_change_pct" in r:
            summary_parts.append(f"Change: {r['latest_change_pct']:.1f}%")
        if "value" in r:
            summary_parts.append(f"Value: {r['value']}")
        result_summary.append(", ".join(summary_parts))

    prompt = f"""You are an AI data analyst evaluating if analysis results sufficiently answer a question.

Question: {question}

Analysis Results Summary:
{chr(10).join(result_summary)}

Does this sufficiently answer the question? Consider:
- Is the question about "why" something happened? If so, we need category breakdowns.
- Is the question about trends? If so, we need time-series data.
- Is the question about specific numbers? If so, we need exact calculations.

Return ONLY valid JSON with this exact format:
{{"sufficient": true/false, "reason": "brief explanation", "additional_analysis": ["monthly_trend", "groupby_category"] or []}}

Note: additional_analysis options are: monthly_trend, groupby_category, groupby_region, statistics, correlation

Response:"""

    response = call_llm(prompt, max_tokens=200)
    if not response:
        return None

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            evaluation = json.loads(response[start:end])
            if "sufficient" in evaluation:
                return evaluation
    except Exception:
        pass
    return None


def _rule_based_evaluate(question: str, results: list, iteration: int) -> dict:
    """
    Rule-based reflection without LLM.
    Check if the results address the core intent of the question.
    """
    question_lower = question.lower()
    result_types = [r.get("type", "") for r in results]

    # ── "Why" questions need category breakdowns ─────────────────
    if any(w in question_lower for w in ["why", "reason", "cause"]):
        if iteration == 1:
            has_trend = any("trend" in t for t in result_types)
            has_groupby = any("groupby" in t for t in result_types)
            if not has_trend and not has_groupby:
                return {
                    "sufficient": False,
                    "reason": "Question asks 'why' but we don't have category or trend breakdown yet.",
                    "additional_analysis": ["monthly_trend", "groupby_category"],
                }

    # ── Trend questions need time-series data ─────────────────────
    if any(w in question_lower for w in ["trend", "over time", "monthly"]):
        if not any("trend" in t for t in result_types):
            return {
                "sufficient": False,
                "reason": "Question asks about trends but no time-series analysis was done.",
                "additional_analysis": ["monthly_trend"],
            }

    # ── Comparison questions need groupby ─────────────────────────
    if any(w in question_lower for w in ["compare", "each", "region", "category"]):
        if not any("groupby" in t for t in result_types):
            return {
                "sufficient": False,
                "reason": "Question asks for comparison but no groupby analysis was done.",
                "additional_analysis": ["groupby_category"],
            }

    # Default: results are sufficient
    return {
        "sufficient": True,
        "reason": f"Analysis completed with {len(results)} result(s). Sufficient to answer the question.",
        "additional_analysis": [],
    }


def get_additional_tool_actions(additional_analysis: list, inspection: dict) -> list:
    """
    Convert additional_analysis strings from reflection into actual tool actions.

    Returns a list of (analysis_type, params) tuples for the pandas tool.
    """
    numeric_cols = inspection.get("numeric_columns", [])
    categorical_cols = inspection.get("categorical_columns", [])
    date_cols = inspection.get("date_columns", [])

    from tools.pandas_tool import _pick_primary_numeric, _pick_primary_category
    primary_numeric = _pick_primary_numeric(numeric_cols)
    primary_date = date_cols[0] if date_cols else None

    actions = []

    for analysis in additional_analysis:
        if analysis == "monthly_trend" and primary_date and primary_numeric:
            actions.append(("monthly_trend", {"date_col": primary_date, "value_col": primary_numeric}))

        elif analysis == "groupby_category" and categorical_cols and primary_numeric:
            for cat_col in categorical_cols[:2]:
                actions.append(("groupby_sum", {"group_col": cat_col, "value_col": primary_numeric}))

        elif analysis == "groupby_region":
            for col in categorical_cols:
                if "region" in col.lower() or "area" in col.lower():
                    if primary_numeric:
                        actions.append(("groupby_sum", {"group_col": col, "value_col": primary_numeric}))
                    break

        elif analysis == "statistics":
            actions.append(("describe", {}))

        elif analysis == "correlation" and len(numeric_cols) >= 2:
            actions.append(("correlation", {"col1": numeric_cols[0], "col2": numeric_cols[1]}))

        elif analysis == "describe_stats":
            actions.append(("describe", {}))

    return actions
