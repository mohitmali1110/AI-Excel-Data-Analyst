# config.py
# Central configuration file for the backend.
# All settings are read from environment variables or have safe defaults.

import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# ── LLM Configuration ──────────────────────────────────────────────
# Uses Ollama running locally — 100% free, no API key required.
# Make sure Ollama is installed and the model is pulled:
#   https://ollama.com/download
#   ollama pull llama3.2
LLM_API_KEY = os.getenv("LLM_API_KEY", "ollama")    # Ollama ignores this but httpx needs a value
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")      # Free local model via Ollama
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")  # Ollama OpenAI-compat endpoint

# ── File Upload Configuration ───────────────────────────────────────
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
CHARTS_DIR = os.path.join(os.path.dirname(__file__), "generated_charts")
SAMPLE_DATA_DIR = os.path.join(os.path.dirname(__file__), "sample_data")

# Maximum upload size in bytes (20 MB)
MAX_FILE_SIZE = 20 * 1024 * 1024

# Allowed file extensions
ALLOWED_EXTENSIONS = {".csv", ".xlsx"}

# ── Agent Configuration ─────────────────────────────────────────────
# Maximum number of reflection/re-planning loops before stopping
MAX_REFLECTION_LOOPS = 3

# Number of rows to send as sample to the LLM (to avoid token overflow)
LLM_SAMPLE_ROWS = 5

# ── App Configuration ───────────────────────────────────────────────
APP_TITLE = "AI Excel Data Analyst"
APP_VERSION = "1.0.0"

# Create required directories on startup
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(SAMPLE_DATA_DIR, exist_ok=True)
