# agent/agent.py
# MAIN AGENT
#
# This is the heart of the agentic AI system.
# It orchestrates the complete workflow:
#   1. Understand the question
#   2. Inspect dataset
#   3. Plan the analysis
#   4. Select tools
#   5. Execute tools (Python/Pandas)
#   6. Reflect on results
#   7. Re-plan if necessary (max 3 loops)
#   8. Generate final answer

import pandas as pd
from datetime import datetime

from tools.dataset_tool import inspect_dataset, get_dataset_context_for_llm
from tools.cleaning_tool import clean_dataset
from tools.pandas_tool import run_pandas_analysis, auto_analyze
from tools.statistics_tool import run_statistics, calculate_growth_rate
from tools.visualization_tool import auto_generate_charts
from tools.insight_tool import generate_insights
from agent.planner import create_analysis_plan
from agent.tool_selector import select_tools, get_tool_display_names
from agent.reflection import evaluate_result, get_additional_tool_actions
from services.llm_service import generate_final_answer
from utils.helpers import make_json_serializable
from config import MAX_REFLECTION_LOOPS


def run_agent(df: pd.DataFrame, question: str) -> dict:
    """
    Run the complete agentic analysis workflow.

    Parameters:
        df: The uploaded dataset as a Pandas DataFrame.
        question: The user's natural language question.

    Returns:
        A complete response dict with answer, insights, charts, etc.
    """

    # ── Track agent steps (shown in frontend) ────────────────────
    agent_steps = []
    all_analysis_results = []  # Accumulate all Pandas results here

    def log_step(step_name: str, status: str = "completed", detail: str = ""):
        """Helper to log each agent step."""
        agent_steps.append({
            "step": step_name,
            "status": status,
            "detail": detail,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
        })
        print(f"[Agent] {step_name} -> {status}")

    # ════════════════════════════════════════════════════════════
    # ── STEP 1: DATASET INSPECTION
    # ════════════════════════════════════════════════════════════
    log_step("Dataset Inspection", "completed", "Analyzing structure, columns, types, missing values")
    inspection = inspect_dataset(df)

    # If no date columns detected by inspection, try parsing each object column
    if not inspection.get("date_columns"):
        for col in df.select_dtypes(include="object").columns:
            try:
                parsed = pd.to_datetime(df[col], format="mixed", dayfirst=False, errors="coerce")
                if parsed.notna().sum() > len(df) * 0.5:  # More than 50% parsed
                    inspection["date_columns"].append(col)
            except Exception:
                pass

    dataset_context = get_dataset_context_for_llm(df, inspection)

    # ════════════════════════════════════════════════════════════
    # STEP 2: DATA CLEANING
    # ════════════════════════════════════════════════════════════
    log_step("Data Cleaning", "completed", "Fixing missing values and duplicates")
    clean_result = clean_dataset(df)
    cleaned_df = clean_result["cleaned_df"]
    cleaning_summary = clean_result["summary"]

    # ════════════════════════════════════════════════════════════
    # STEP 3: UNDERSTAND QUESTION & PLAN
    # ════════════════════════════════════════════════════════════
    log_step("Question Understanding", "completed", f"Processing: '{question}'")
    plan = create_analysis_plan(question, dataset_context)
    log_step("Analysis Planning", "completed", f"Created {len(plan)}-step plan")

    # ════════════════════════════════════════════════════════════
    # STEP 4: SELECT TOOLS
    # ════════════════════════════════════════════════════════════
    selected_tool_keys = select_tools(question, inspection)
    tool_display_names = get_tool_display_names(selected_tool_keys)
    log_step("Tool Selection", "completed", f"Selected: {', '.join(tool_display_names)}")

    # ════════════════════════════════════════════════════════════
    # STEP 5: EXECUTE TOOLS (First Pass)
    # ════════════════════════════════════════════════════════════
    log_step("Python/Pandas Analysis", "in_progress", "Running analysis with selected tools")

    if "pandas_tool" in selected_tool_keys:
        pandas_results = auto_analyze(cleaned_df, question, inspection)
        all_analysis_results.extend(pandas_results)

    if "statistics_tool" in selected_tool_keys:
        stats_result = run_statistics(cleaned_df)
        all_analysis_results.append({"type": "statistics", "data": stats_result})

        # Also try growth rate if date column exists
        date_cols = inspection.get("date_columns", [])
        numeric_cols = inspection.get("numeric_columns", [])
        if date_cols and numeric_cols:
            from tools.pandas_tool import _pick_primary_numeric
            primary_num = _pick_primary_numeric(numeric_cols)
            if primary_num:
                growth = calculate_growth_rate(cleaned_df, date_cols[0], primary_num)
                if "error" not in growth:
                    all_analysis_results.append({"type": "growth_rate", "data": growth})

    log_step("Python/Pandas Analysis", "completed", f"Generated {len(all_analysis_results)} result(s)")

    # ════════════════════════════════════════════════════════════
    # STEP 6: REFLECTION LOOP (Core Agentic Feature)
    # ════════════════════════════════════════════════════════════
    reflection_log = []
    final_reflection = None

    for loop_num in range(1, MAX_REFLECTION_LOOPS + 1):
        log_step(f"Reflection Loop {loop_num}", "in_progress", "Evaluating if results answer the question")

        evaluation = evaluate_result(question, all_analysis_results, iteration=loop_num)
        reflection_log.append({
            "loop": loop_num,
            "sufficient": evaluation["sufficient"],
            "reason": evaluation["reason"],
            "additional_analysis": evaluation.get("additional_analysis", []),
        })
        final_reflection = evaluation

        log_step(
            f"Reflection Loop {loop_num}",
            "completed",
            f"Sufficient: {evaluation['sufficient']} — {evaluation['reason']}"
        )

        # If results are sufficient, stop the loop
        if evaluation["sufficient"]:
            break

        # If not sufficient, run additional analysis
        additional_actions = get_additional_tool_actions(
            evaluation.get("additional_analysis", []),
            inspection,
        )

        if not additional_actions:
            break  # Nothing more to do

        log_step(f"Additional Analysis (Loop {loop_num})", "in_progress",
                 f"Running {len(additional_actions)} additional analysis step(s)")

        for analysis_type, params in additional_actions:
            r = run_pandas_analysis(cleaned_df, analysis_type, params)
            if "error" not in r:
                all_analysis_results.append(r)

        log_step(f"Additional Analysis (Loop {loop_num})", "completed",
                 f"Added {len(additional_actions)} more result(s)")

    # ════════════════════════════════════════════════════════════
    # STEP 7: GENERATE INSIGHTS
    # ════════════════════════════════════════════════════════════
    log_step("Insight Generation", "in_progress", "Extracting key findings from results")

    # Filter to only valid analysis results (not stats metadata)
    valid_results = [r for r in all_analysis_results if r and "error" not in r and r.get("type") not in ("statistics", "growth_rate")]

    insight_data = generate_insights(question, valid_results, inspection)
    insights = insight_data["insights"]
    recommendations = insight_data["recommendations"]
    key_findings = insight_data["key_findings"]

    log_step("Insight Generation", "completed", f"Generated {len(insights)} insights")

    # ════════════════════════════════════════════════════════════
    # STEP 8: GENERATE CHARTS
    # ════════════════════════════════════════════════════════════
    charts = []
    if "visualization_tool" in selected_tool_keys:
        log_step("Chart Generation", "in_progress", "Creating visualizations")
        try:
            charts = auto_generate_charts(cleaned_df, valid_results, inspection)
            log_step("Chart Generation", "completed", f"Created {len(charts)} chart(s)")
        except Exception as e:
            log_step("Chart Generation", "completed", f"Chart generation had issues: {str(e)}")

    # ════════════════════════════════════════════════════════════
    # STEP 9: GENERATE FINAL ANSWER
    # ════════════════════════════════════════════════════════════
    log_step("Final Answer Generation", "in_progress", "Composing final response")

    final_answer = generate_final_answer(question, valid_results, insights, dataset_context)

    log_step("Final Answer Generation", "completed", "Response ready")

    # ════════════════════════════════════════════════════════════
    # COMPOSE FINAL RESPONSE
    # ════════════════════════════════════════════════════════════
    response = {
        "success": True,
        "question": question,
        "plan": plan,
        "tools_used": tool_display_names,
        "agent_steps": agent_steps,
        "cleaning_summary": cleaning_summary,
        "analysis_results": make_json_serializable(valid_results[:8]),  # Cap to avoid huge responses
        "reflection_log": reflection_log,
        "reflection": final_reflection["reason"] if final_reflection else "Analysis complete.",
        "answer": final_answer,
        "insights": insights,
        "key_findings": key_findings,
        "recommendations": recommendations,
        "charts": [make_json_serializable(c) for c in charts if "error" not in c],
    }

    return response
