"""
main.py -- FastAPI application entry point.

Routes:
  GET  /api/health               -- backend health check
  GET  /api/sensor/scenarios     -- list all preset scenarios
  GET  /api/sensor/simulate      -- return sensor data for a named or random scenario
  POST /api/diagnose             -- four-stage diagnosis pipeline (fallback or Granite)
"""
import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models import SensorData, DiagnosisResponse
from pipeline import run_diagnosis
from data.sensor_simulator import get_all_scenarios, get_scenario, get_random_scenario

load_dotenv()

app = FastAPI(
    title="VitalMech API",
    description="AI-Powered Mechanical Fault Diagnosis — IBM Granite backend",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS — allow the Vite dev server
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/api/health")
def health():
    """Backend health check — returns active configuration."""
    return {
        "status": "ok",
        "ai_backend": os.getenv("AI_BACKEND", "granite"),
        "rag_backend": os.getenv("RAG_BACKEND", "simple"),
        "model_id": os.getenv("WATSONX_MODEL_ID", "not-configured"),
        "watsonx_url": os.getenv("WATSONX_URL", "not-configured"),
    }


@app.get("/api/sensor/scenarios")
def list_scenarios():
    """Return metadata for all 8 preset fault scenarios."""
    return {"scenarios": get_all_scenarios()}


@app.get("/api/sensor/simulate")
def simulate_sensor(
    scenario: str = Query(
        default=None,
        description="Scenario ID (e.g. bearing_failure). Omit for a random scenario.",
    )
):
    """Return full sensor data for a named or random scenario."""
    if scenario:
        data = get_scenario(scenario)
        if data is None:
            raise HTTPException(
                status_code=404,
                detail=f"Scenario '{scenario}' not found. "
                       f"Available: {[s['id'] for s in get_all_scenarios()]}",
            )
        return data
    return get_random_scenario()


@app.post("/api/diagnose", response_model=DiagnosisResponse)
def diagnose(sensor_data: SensorData):
    """
    Run the four-stage diagnosis pipeline.

    Input (JSON body):
      machine_type        : string
      symptom_description : string (optional)
      scenario_id         : string (optional preset ID, e.g. "bearing_failure")
      sensors             : { rpm, temperature_c, vibration_mm_s,
                               pressure_bar, current_amps, noise_db }

    Response includes:
      diagnosis           : symptoms / faults / root_cause / repair_guidance
      severity            : low | medium | high | critical
      overall_confidence  : 0.0 - 1.0
      retrieved_knowledge : RAG document titles used as context
      ai_source           : "fallback" | "granite"
    """
    try:
        return run_diagnosis(sensor_data)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
