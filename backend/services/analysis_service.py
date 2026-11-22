# services/analysis_service.py
# ANALYSIS SERVICE
#
# Bridges the FastAPI endpoints and the agent.
# Loads the file, calls the agent, and returns the response.

import pandas as pd
from services.file_service import load_dataframe
from tools.dataset_tool import inspect_dataset
from agent.agent import run_agent
from utils.helpers import make_json_serializable


def get_dataset_info(filename: str) -> dict:
    """
    Load a dataset and return its inspection info.
    Used by the GET /dataset/{filename} endpoint.
    """
    df = load_dataframe(filename)
    inspection = inspect_dataset(df)
    return make_json_serializable(inspection)


def analyze_question(filename: str, question: str) -> dict:
    """
    Load a dataset and run the agent to answer a question.
    Used by the POST /ask endpoint.

    Parameters:
        filename: The saved filename of the uploaded dataset.
        question: The user's natural language question.

    Returns:
        Full agent response dict.
    """
    if not question or len(question.strip()) < 3:
        return {
            "success": False,
            "error": "Question is too short. Please ask a meaningful question about your data.",
        }

    df = load_dataframe(filename)

    try:
        result = run_agent(df, question.strip())
        return make_json_serializable(result)
    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "question": question,
        }
