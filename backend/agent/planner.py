# agent/planner.py
# AGENT PLANNER
#
# The planner receives the user question and dataset information,
# then creates a step-by-step analysis plan.
# If an LLM is available, it generates a smart plan.
# If not, it uses keyword-based rules to create a reasonable plan.

import json
from services.llm_service import call_llm, is_llm_available


def create_analysis_plan(question: str, dataset_context: str) -> list:
    """
    Create an ordered list of analysis steps for the given question.

    Parameters:
        question: The user's natural language question.
        dataset_context: Short text summary of the dataset (not the full data).

    Returns:
        A list of step strings, e.g.:
        ["Inspect dataset structure", "Group revenue by category", ...]
    """

    # Try LLM-based planning first
    if is_llm_available():
        try:
            plan = _llm_plan(question, dataset_context)
            if plan and len(plan) > 0:
                return plan
        except Exception:
            pass  # Fall through to keyword-based planning

    # Fallback: keyword-based plan
    return _keyword_plan(question)


def _llm_plan(question: str, dataset_context: str) -> list:
    """Use the LLM to generate an analysis plan."""
    prompt = f"""You are an AI data analyst. Given a dataset and a user question,
create a concise analysis plan as a JSON list of steps.

Dataset Information:
{dataset_context}

User Question:
{question}

Return ONLY a valid JSON array of strings — each string is one analysis step.
Maximum 6 steps. Be specific about which columns to analyze.
Example output:
["Inspect dataset columns and types", "Calculate monthly revenue trend", "Group revenue by category", "Identify top and bottom performers", "Generate insights from results"]

Output:"""

    response = call_llm(prompt, max_tokens=300)
    if not response:
        return []

    # Extract JSON array from LLM response
    try:
        # Find the JSON array in the response
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            plan = json.loads(response[start:end])
            if isinstance(plan, list):
                return [str(step) for step in plan[:8]]
    except Exception:
        pass

    # If JSON parse fails, split by newlines
    lines = [line.strip().lstrip("0123456789.-) ") for line in response.strip().split("\n")]
    return [line for line in lines if len(line) > 5][:6]


def _keyword_plan(question: str) -> list:
    """
    Create a reasonable analysis plan based on keywords in the question.
    This works WITHOUT any LLM.
    """
    question_lower = question.lower()
    plan = ["Inspect dataset structure and columns"]

    # ── Time / trend questions ────────────────────────────────────
    if any(w in question_lower for w in ["trend", "month", "over time", "year", "period", "growth"]):
        plan.append("Identify date column for time-series analysis")
        plan.append("Calculate monthly aggregated values")
        plan.append("Compute period-over-period change")

    # ── Revenue decline / 'why' questions ─────────────────────────
    if any(w in question_lower for w in ["why", "decrease", "decline", "fall", "drop", "reduce"]):
        plan.append("Analyze values by category to find contributors to decline")
        plan.append("Analyze values by region or segment")
        plan.append("Check for unusual spikes or anomalies")
        plan.append("Identify the biggest change drivers")

    # ── Comparison / group questions ──────────────────────────────
    if any(w in question_lower for w in ["compare", "by", "region", "category", "group", "segment"]):
        plan.append("Group data by the relevant category column")
        plan.append("Compare totals and averages across groups")
        plan.append("Identify top and bottom performers")

    # ── Best / highest / top ──────────────────────────────────────
    if any(w in question_lower for w in ["best", "highest", "most", "top", "maximum"]):
        plan.append("Calculate total values grouped by category")
        plan.append("Sort and identify the highest-performing group")

    # ── Worst / lowest ────────────────────────────────────────────
    if any(w in question_lower for w in ["worst", "lowest", "least", "minimum", "bottom"]):
        plan.append("Calculate total values grouped by category")
        plan.append("Identify the lowest-performing group")

    # ── Average ───────────────────────────────────────────────────
    if any(w in question_lower for w in ["average", "mean", "typical"]):
        plan.append("Calculate mean values for relevant numeric columns")

    # ── Total / sum ───────────────────────────────────────────────
    if any(w in question_lower for w in ["total", "sum", "overall", "how much"]):
        plan.append("Calculate total (sum) of relevant numeric columns")

    # ── Distribution / spread ─────────────────────────────────────
    if any(w in question_lower for w in ["distribution", "spread", "range", "outlier"]):
        plan.append("Compute descriptive statistics (min, max, mean, std)")
        plan.append("Identify outliers using IQR method")

    # ── Insight / summary ─────────────────────────────────────────
    if any(w in question_lower for w in ["insight", "summary", "overview", "important"]):
        plan.append("Run comprehensive statistical analysis")
        plan.append("Identify top and bottom items across all categories")

    # Always end with evaluation and insights
    plan.append("Evaluate results and generate insights")
    plan.append("Create visualizations for key findings")

    # Remove duplicates while preserving order
    seen = set()
    unique_plan = []
    for step in plan:
        if step not in seen:
            seen.add(step)
            unique_plan.append(step)

    return unique_plan[:8]  # Max 8 steps
