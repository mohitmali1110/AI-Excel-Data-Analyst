# main.py
# FastAPI Backend – Main Application Entry Point
#
# Provides these endpoints:
#   POST /upload        → Upload CSV/XLSX file
#   GET  /dataset/{filename} → Get dataset info
#   POST /ask           → Ask a question (runs the AI agent)
#   GET  /charts/{filename}  → Serve generated chart images

import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import APP_TITLE, APP_VERSION, CHARTS_DIR, UPLOAD_DIR
from services.file_service import validate_and_save_file, load_dataframe
from services.analysis_service import get_dataset_info, analyze_question
from tools.dataset_tool import inspect_dataset
from utils.helpers import make_json_serializable, df_to_json_safe

# ── Create FastAPI app ────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Agentic AI-powered Excel and CSV data analyst",
)

# ── CORS: Allow React frontend (running on Vite default port) ─────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve generated chart images as static files ──────────────────
os.makedirs(CHARTS_DIR, exist_ok=True)
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")


# ── Pydantic model for the /ask request body ──────────────────────
class QuestionRequest(BaseModel):
    filename: str     # The saved filename returned by /upload
    question: str     # The user's natural language question


# ════════════════════════════════════════════════════════════════
# ENDPOINT 1: Health Check
# ════════════════════════════════════════════════════════════════
@app.get("/")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "running",
        "app": APP_TITLE,
        "version": APP_VERSION,
        "message": "AI Excel Data Analyst API is ready!",
    }


# ════════════════════════════════════════════════════════════════
# ENDPOINT 2: Upload File
# POST /upload
# ════════════════════════════════════════════════════════════════
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV or XLSX file.

    Returns dataset information including:
    - filename (use this in subsequent /ask requests)
    - row/column counts
    - column names, data types, missing values
    - preview of first 10 rows
    """
    # Validate and save the file
    file_info = validate_and_save_file(file)
    saved_filename = file_info["saved_filename"]

    # Load and inspect the dataset
    df = load_dataframe(saved_filename)
    inspection = inspect_dataset(df)

    # Build response
    response = {
        "success": True,
        "message": f"File '{file_info['original_filename']}' uploaded successfully.",
        "filename": saved_filename,
        "original_filename": file_info["original_filename"],
        "file_type": file_info["file_type"],
        # ── Dataset overview ──────────────────────────────────
        "rows": inspection["rows"],
        "columns": inspection["columns"],
        "column_names": inspection["column_names"],
        "column_dtypes": inspection["column_dtypes"],
        "missing_values": inspection["missing_values"],
        "total_missing": inspection["total_missing"],
        "duplicates": inspection["duplicates"],
        "numeric_columns": inspection["numeric_columns"],
        "categorical_columns": inspection["categorical_columns"],
        "date_columns": inspection["date_columns"],
        "numeric_stats": inspection["numeric_stats"],
        # ── Preview rows ──────────────────────────────────────
        "preview": inspection["sample_rows"],
    }

    return make_json_serializable(response)


# ════════════════════════════════════════════════════════════════
# ENDPOINT 3: Get Dataset Info
# GET /dataset/{filename}
# ════════════════════════════════════════════════════════════════
@app.get("/dataset/{filename}")
def get_dataset(filename: str):
    """
    Get full dataset information for an already-uploaded file.
    """
    try:
        info = get_dataset_info(filename)
        return {"success": True, **info}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════════════════════════
# ENDPOINT 4: Ask Question (Runs the AI Agent)
# POST /ask
# ════════════════════════════════════════════════════════════════
@app.post("/ask")
def ask_question(request: QuestionRequest):
    """
    Run the AI agent to answer a question about the uploaded dataset.

    The agent workflow:
    1. Loads the dataset
    2. Inspects it
    3. Creates an analysis plan
    4. Selects tools (Dataset Tool, Pandas Tool, Stats Tool, etc.)
    5. Executes Python/Pandas analysis
    6. Reflects on whether results are sufficient
    7. Re-plans if needed (max 3 loops)
    8. Generates final answer + insights + charts

    Returns the complete agent response.
    """
    try:
        result = analyze_question(request.filename, request.question)
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"Agent encountered an error: {str(e)}",
                "question": request.question,
            }
        )


# ════════════════════════════════════════════════════════════════
# ENDPOINT 5: List Uploaded Files
# GET /files
# ════════════════════════════════════════════════════════════════
@app.get("/files")
def list_files():
    """Return a list of all uploaded files."""
    from services.file_service import list_uploaded_files
    files = list_uploaded_files()
    return {"files": files}
