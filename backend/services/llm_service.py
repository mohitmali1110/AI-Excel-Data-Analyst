# services/llm_service.py
# LLM SERVICE
#
# Automatically connects to Ollama (free, local LLM runner).
# On startup it queries Ollama for all installed models, ranks them by
# capability, and picks the best one — no API key, no manual config needed.
#
# Install Ollama : https://ollama.com/download
# Pull a model  : ollama pull llama3.2   (or mistral, gemma2, phi4, etc.)

import httpx
import json
from config import LLM_BASE_URL

# ── Model preference ranking ────────────────────────────────────────────────
# The service walks this list and picks the first model that is actually
# installed on the user's machine.
_MODEL_PREFERENCE = [
    # Llama 3.x (best general reasoning)
    "llama3.3", "llama3.2", "llama3.1", "llama3",
    # Mistral family
    "mistral-large", "mistral-nemo", "mistral",
    # Gemma 2
    "gemma2:27b", "gemma2:9b", "gemma2", "gemma",
    # Qwen 2.5
    "qwen2.5:72b", "qwen2.5:32b", "qwen2.5:14b", "qwen2.5:7b", "qwen2.5", "qwen2",
    # Phi (lightweight but capable)
    "phi4", "phi3.5", "phi3",
    # Llama 2 as last-resort fallback
    "llama2:13b", "llama2:7b", "llama2",
]

# ── Runtime cache (query Ollama only once per process) ──────────────────────
_cached_model: str | None = None
_ollama_checked: bool = False


def _ollama_base() -> str:
    """Return Ollama's native base URL (strips /v1 if present)."""
    return LLM_BASE_URL.rstrip("/").removesuffix("/v1")


def _fetch_installed_models() -> list[str]:
    """
    Call Ollama's  GET /api/tags  to discover installed models.
    Returns a list of model name strings (e.g. ["llama3.2:latest", "mistral:latest"]).
    Returns [] if Ollama is unreachable or has no models.
    """
    try:
        url = _ollama_base() + "/api/tags"
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            models = [m["name"] for m in data.get("models", [])]
            if models:
                print(f"[LLM Service] Ollama is running. Installed models: {models}")
            else:
                print("[LLM Service] Ollama is running but no models are installed.")
                print("[LLM Service]   -> Pull one with:  ollama pull llama3.2")
            return models
    except Exception as e:
        print(f"[LLM Service] Cannot reach Ollama at {_ollama_base()}: {e}")
        print("[LLM Service]   -> Download Ollama from: https://ollama.com/download")
        return []


def _pick_best_model(installed: list[str]) -> str | None:
    """
    Given installed model names from Ollama, return the highest-ranked one
    according to _MODEL_PREFERENCE.  Falls back to the first installed model
    if nothing in the preference list is found.
    """
    if not installed:
        return None

    # Build a lookup keyed by base name (strip ":latest" / tag suffixes)
    installed_map = {name.split(":")[0].lower(): name for name in installed}

    for preferred in _MODEL_PREFERENCE:
        if preferred.lower() in installed_map:
            chosen = installed_map[preferred.lower()]
            print(f"[LLM Service] [OK] Auto-selected model: '{chosen}'")
            return chosen

    # Nothing matched — use whatever is there
    chosen = installed[0]
    print(f"[LLM Service] [WARN] No preferred model found. Using: '{chosen}'")
    return chosen


def _resolve_model() -> str | None:
    """
    Ask Ollama which models are installed, pick the best one, and cache
    the result for the lifetime of the process.
    """
    global _cached_model, _ollama_checked

    if _ollama_checked:
        return _cached_model  # Return cached result (even if None)

    _ollama_checked = True
    installed = _fetch_installed_models()
    _cached_model = _pick_best_model(installed)
    return _cached_model


# ── Public API ──────────────────────────────────────────────────────────────

def is_llm_available() -> bool:
    """Returns True if Ollama is running and at least one model is installed."""
    return _resolve_model() is not None


def get_active_model() -> str | None:
    """Return the name of the model that will be used, or None."""
    return _resolve_model()


def call_llm(prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
    """
    Send a prompt to the best available Ollama model and return the response.

    Parameters:
        prompt:      The prompt text to send.
        max_tokens:  Maximum tokens in the response.
        temperature: 0.0 = deterministic, 1.0 = creative.

    Returns:
        Response text string, or None if Ollama is unavailable.
    """
    model = _resolve_model()
    if not model:
        return None

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert data analyst AI assistant. "
                    "You analyze datasets and provide accurate, data-driven insights. "
                    "Never invent numerical results — always base your answers on provided data."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": False,
    }

    try:
        url = LLM_BASE_URL.rstrip("/") + "/chat/completions"
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[LLM Service] API call failed (model={model}): {e}")
        return None


def generate_final_answer(
    question: str,
    analysis_results: list,
    insights: list,
    dataset_context: str,
) -> str:
    """
    Ask the LLM to compose a final natural language answer using the ACTUAL
    analysis results.  The LLM receives computed numbers — it does NOT invent them.

    Returns the answer string, or a fallback answer if Ollama is unavailable.
    """
    if not is_llm_available():
        return _fallback_answer(question, analysis_results, insights)

    # Prepare a compact results summary
    results_text = []
    for r in analysis_results[:5]:
        if r and "error" not in r:
            rtype = r.get("type", "")
            if rtype == "monthly_trend":
                change = r.get("latest_change_pct")
                if change is not None:
                    results_text.append(f"- Monthly trend: {change:.1f}% change in latest period")
            elif rtype == "groupby_sum":
                top = r.get("top_item", {})
                group = r.get("group_col", "group")
                value = r.get("value_col", "value")
                if top:
                    results_text.append(
                        f"- Top {group}: {top.get(group)} with {top.get(f'total_{value}', 'N/A')}"
                    )
            elif rtype == "column_sum":
                results_text.append(f"- Total {r.get('column')}: {r.get('value')}")
            elif rtype == "column_mean":
                results_text.append(f"- Average {r.get('column')}: {r.get('value')}")

    prompt = f"""You are an expert data analyst. Based on ACTUAL computed analysis results,
write a clear, concise answer to the user's question.

User Question: {question}

Computed Results (use ONLY these numbers):
{chr(10).join(results_text) if results_text else "General analysis completed."}

Key Insights:
{chr(10).join(f"- {i}" for i in insights[:5])}

Write a clear answer in 3-4 sentences. Use the actual numbers provided above.
Do NOT invent any numbers. Be specific and actionable."""

    response = call_llm(prompt, max_tokens=400, temperature=0.4)
    if response:
        return response

    return _fallback_answer(question, analysis_results, insights)


def _fallback_answer(question: str, analysis_results: list, insights: list) -> str:
    """
    Generate a simple answer without LLM, using the computed results directly.
    Used when Ollama is not running or has no models installed.
    """
    answer_parts = ["Based on the analysis of your dataset:"]
    seen_parts = set()

    for r in analysis_results[:3]:
        if not r or "error" in r:
            continue
        rtype = r.get("type", "")

        if rtype == "monthly_trend":
            change = r.get("latest_change_pct")
            value_col = r.get("value_col", "values")
            if change is not None:
                direction = "increased" if change > 0 else "decreased"
                bullet = (
                    f"* {value_col.replace('_', ' ').title()} {direction} by "
                    f"{abs(round(change, 1))}% in the latest period."
                )
                if bullet not in seen_parts:
                    seen_parts.add(bullet)
                    answer_parts.append(bullet)

        elif rtype == "groupby_sum":
            top = r.get("top_item", {})
            group_col = r.get("group_col", "group")
            value_col = r.get("value_col", "value")
            if top:
                agg_col = f"total_{value_col}"
                bullet = (
                    f"* '{top.get(group_col)}' leads with the highest "
                    f"{value_col.replace('_', ' ')}: {top.get(agg_col, 'N/A')}."
                )
                if bullet not in seen_parts:
                    seen_parts.add(bullet)
                    answer_parts.append(bullet)

        elif rtype == "column_mean":
            col = r.get("column", "value")
            val = r.get("value", 0)
            bullet = f"* Average {col.replace('_', ' ')}: {round(val, 2)}"
            if bullet not in seen_parts:
                seen_parts.add(bullet)
                answer_parts.append(bullet)

        elif rtype == "column_sum":
            col = r.get("column", "value")
            val = r.get("value", 0)
            bullet = f"* Total {col.replace('_', ' ')}: {round(val, 2)}"
            if bullet not in seen_parts:
                seen_parts.add(bullet)
                answer_parts.append(bullet)

    if len(answer_parts) == 1:
        if insights:
            answer_parts.append(insights[0])
        else:
            answer_parts.append("Analysis completed. Please see the insights and charts below.")

    return "\n".join(answer_parts)


def generate_plan_with_llm(question: str, context: str) -> str:
    """Simple wrapper used by planner.py."""
    return call_llm(
        f"Dataset context:\n{context}\n\nQuestion: {question}\n\nCreate analysis plan:",
        max_tokens=300,
    )
