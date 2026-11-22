# agent/tool_selector.py
# TOOL SELECTOR
#
# Decides WHICH analysis tools to use based on the user question.
# Uses keyword matching as the primary strategy.
# If LLM is available, it can refine the selection.
# This is a key part of the agentic workflow — the agent must DECIDE, not just forward.

import json
from services.llm_service import call_llm, is_llm_available


# ── Tool Registry ─────────────────────────────────────────────────────
# Each tool has a name (used in code), display name, and description.
AVAILABLE_TOOLS = {
    "dataset_tool": {
        "name": "Dataset Inspection Tool",
        "description": "Inspects dataset structure, columns, types, missing values.",
    },
    "cleaning_tool": {
        "name": "Data Cleaning Tool",
        "description": "Cleans missing values, duplicates, whitespace.",
    },
    "pandas_tool": {
        "name": "Pandas Analysis Tool",
        "description": "Performs groupby, sum, mean, filtering, sorting, time analysis.",
    },
    "statistics_tool": {
        "name": "Statistical Analysis Tool",
        "description": "Computes mean, median, std, correlation, growth rate, outliers.",
    },
    "visualization_tool": {
        "name": "Visualization Tool",
        "description": "Generates line, bar, histogram, scatter, pie charts.",
    },
    "insight_tool": {
        "name": "Insight Generation Tool",
        "description": "Generates key insights and recommendations from results.",
    },
}


def select_tools(question: str, inspection: dict) -> list:
    """
    Select which tools to use based on the question and dataset info.

    Parameters:
        question: The user's question.
        inspection: Dataset inspection result dict.

    Returns:
        A list of tool key strings, e.g. ['pandas_tool', 'visualization_tool']
    """

    # Try LLM-based selection
    if is_llm_available():
        try:
            tools = _llm_select_tools(question, inspection)
            if tools:
                return tools
        except Exception:
            pass

    # Fallback: keyword-based selection
    return _keyword_select_tools(question, inspection)


def _llm_select_tools(question: str, inspection: dict) -> list:
    """Use LLM to select tools."""
    available_names = list(AVAILABLE_TOOLS.keys())
    dataset_info = (
        f"Columns: {inspection.get('column_names', [])}, "
        f"Numeric: {inspection.get('numeric_columns', [])}, "
        f"Categories: {inspection.get('categorical_columns', [])}, "
        f"Date cols: {inspection.get('date_columns', [])}"
    )

    prompt = f"""You are an AI data analyst selecting tools to answer a question.

Question: {question}
Dataset info: {dataset_info}

Available tools: {available_names}

Always include 'dataset_tool', 'visualization_tool', and 'insight_tool'.
Return ONLY a valid JSON array of tool names from the available list.
Example: ["dataset_tool", "pandas_tool", "visualization_tool", "insight_tool"]

Selected tools:"""

    response = call_llm(prompt, max_tokens=100)
    if not response:
        return []

    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            tools = json.loads(response[start:end])
            # Validate: only include tools that actually exist
            valid_tools = [t for t in tools if t in AVAILABLE_TOOLS]
            # Always ensure visualization_tool is included
            if "visualization_tool" not in valid_tools:
                valid_tools.append("visualization_tool")
            if valid_tools:
                return valid_tools
    except Exception:
        pass
    return []


def _keyword_select_tools(question: str, inspection: dict) -> list:
    """
    Select tools using keyword rules. Works without LLM.
    Always starts with dataset_tool and ends with insight_tool.
    """
    question_lower = question.lower()
    tools = ["dataset_tool"]  # Always inspect dataset first

    has_numeric = len(inspection.get("numeric_columns", [])) > 0
    has_dates = len(inspection.get("date_columns", [])) > 0
    has_categories = len(inspection.get("categorical_columns", [])) > 0

    # ── Cleaning: always run if there are missing values ──────────
    if inspection.get("total_missing", 0) > 0 or inspection.get("duplicates", 0) > 0:
        tools.append("cleaning_tool")

    # ── Pandas analysis: almost always needed ─────────────────────
    pandas_keywords = [
        "total", "sum", "average", "mean", "highest", "lowest", "most", "least",
        "top", "bottom", "best", "worst", "by", "each", "per", "compare",
        "group", "region", "category", "product", "trend", "month", "year",
        "increase", "decrease", "decline", "rise", "fall", "why", "which",
        "how much", "revenue", "sales", "profit", "count", "number",
    ]
    if any(kw in question_lower for kw in pandas_keywords) or has_numeric:
        tools.append("pandas_tool")

    # ── Statistics: for deeper analysis questions ──────────────────
    stats_keywords = [
        "statistics", "correlation", "distribution", "spread", "std",
        "standard deviation", "outlier", "growth rate", "percentage",
        "trend", "why", "reason", "cause", "significant",
    ]
    if any(kw in question_lower for kw in stats_keywords):
        tools.append("statistics_tool")

    # ── Visualization: always generate charts for any analysis ────
    # Charts are always useful regardless of the question type.
    tools.append("visualization_tool")

    # ── If asking "why" or "reason" → deep analysis ───────────────
    if any(w in question_lower for w in ["why", "reason", "cause", "explain"]):
        if "statistics_tool" not in tools:
            tools.append("statistics_tool")

    # ── Always end with insight tool ──────────────────────────────
    tools.append("insight_tool")

    return list(dict.fromkeys(tools))  # Remove duplicates while preserving order


def get_tool_display_names(tool_keys: list) -> list:
    """Convert tool key list to display name list."""
    return [AVAILABLE_TOOLS.get(key, {}).get("name", key) for key in tool_keys]
