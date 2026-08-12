"""
pipeline.py -- DiagnosisPipeline: wires Retriever + AI client together.

Phase 4 implementation:
  1. Build a diagnostic query string from sensor data and symptoms.
  2. Call SimpleRetriever to fetch top-3 relevant knowledge documents.
  3. Run the active AI backend (fallback engine or Granite when configured).
  4. Aggregate results into a DiagnosisResponse.

AI backend selection (AI_BACKEND env var):
  "granite"  -- GraniteClient (requires WATSONX credentials; falls back if not configured)
  "fallback" -- FallbackEngine (deterministic rules, always available)
  anything else -- FallbackEngine

The fallback engine is ALWAYS available and clearly labelled in the response.
"""
import asyncio
import os

from dotenv import load_dotenv

from ai.fallback_engine import run_fallback_diagnosis, _compute_severity
from models import DiagnosisResponse, DiagnosisResult, SensorData
from rag.simple_retriever import SimpleRetriever, ScoredDocument

load_dotenv()

# Module-level retriever instance (loaded once at import time)
_retriever = SimpleRetriever()


def _build_rag_query(sensor_data: SensorData) -> str:
    """
    Build a keyword-rich diagnostic query for the retriever.
    Combines machine type, symptom text, and any obviously anomalous sensor labels.
    """
    r = sensor_data.sensors
    parts: list[str] = []

    # Machine type always included
    parts.append(sensor_data.machine_type)

    # Free-text symptom description (most discriminating)
    if sensor_data.symptom_description.strip():
        parts.append(sensor_data.symptom_description)

    # Append labels for sensors that are clearly outside normal range
    if r.vibration_mm_s >= 7.1:
        parts.append("high vibration")
    if r.temperature_c >= 75.0:
        parts.append("high temperature overheating")
    if r.noise_db >= 80.0:
        parts.append("high noise")
    if r.current_amps >= 35.0:
        parts.append("high current electrical fault")
    if r.pressure_bar <= 2.0:
        parts.append("low pressure cavitation")

    return " ".join(parts)


def _run_granite(
    sensor_data: SensorData, context_docs: list[str]
) -> tuple["DiagnosisResult | None", str]:
    """
    Attempt a Granite inference call.
    Returns (DiagnosisResult, "") on success.
    Returns (None, reason_string) on any failure so the caller can log why
    the fallback was triggered without silently hiding errors.
    """
    api_key    = os.getenv("WATSONX_API_KEY", "")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")
    model_id   = os.getenv("WATSONX_MODEL_ID", "")

    if not api_key or not project_id or not model_id:
        missing = [k for k, v in {
            "WATSONX_API_KEY": api_key,
            "WATSONX_PROJECT_ID": project_id,
            "WATSONX_MODEL_ID": model_id,
        }.items() if not v]
        return None, f"Missing env vars: {missing}"

    try:
        from ai.granite_client import GraniteClient
        client = GraniteClient()
        result = asyncio.run(client.diagnose(sensor_data, context_docs))
        return result, ""
    except Exception as exc:
        return None, str(exc)


def run_diagnosis(sensor_data: SensorData) -> DiagnosisResponse:
    """
    Full four-stage diagnosis pipeline.

    Returns a DiagnosisResponse with:
      - diagnosis       : four-stage structured result
      - severity        : aggregated severity level
      - overall_confidence : top fault confidence
      - retrieved_knowledge : titles of RAG documents used
      - ai_source       : "fallback" | "granite"
    """
    ai_backend_env = os.getenv("AI_BACKEND", "granite").lower()
    rag_backend = os.getenv("RAG_BACKEND", "simple")
    model_id = os.getenv("WATSONX_MODEL_ID", "none")

    # ------------------------------------------------------------------
    # RAG: retrieve relevant knowledge documents
    # ------------------------------------------------------------------
    rag_query = _build_rag_query(sensor_data)
    scored_docs: list[ScoredDocument] = _retriever.retrieve_scored(rag_query, top_k=3)
    context_docs: list[str] = [d.content for d in scored_docs]
    retrieved_titles: list[str] = [d.title for d in scored_docs]

    # ------------------------------------------------------------------
    # AI: run diagnosis
    # ------------------------------------------------------------------
    result: "DiagnosisResult | None" = None
    ai_source = "fallback"
    used_model = "rule-based-engine"
    granite_error = ""

    if ai_backend_env == "granite":
        granite_result, granite_error = _run_granite(sensor_data, context_docs)
        if granite_result is not None:
            result = granite_result
            ai_source = "granite"
            used_model = model_id
        # else: granite_error holds the reason; fallback runs below

    if result is None:
        result = run_fallback_diagnosis(sensor_data)
        ai_source = "fallback"
        used_model = "rule-based-engine"

    # ------------------------------------------------------------------
    # Aggregate severity and top confidence
    # ------------------------------------------------------------------
    top_confidence = result.faults[0].confidence if result.faults else 0.0
    severity = _compute_severity(result.symptoms, top_confidence)

    return DiagnosisResponse(
        scenario_id=sensor_data.scenario_id,
        machine_type=sensor_data.machine_type,
        sensor_data=sensor_data.sensors,
        diagnosis=result,
        severity=severity,
        overall_confidence=round(top_confidence, 2),
        retrieved_knowledge=retrieved_titles,
        ai_source=ai_source,
        model_used=used_model,
        ai_backend=ai_backend_env,
        rag_backend=rag_backend,
    )
