"""
models.py -- Pydantic models shared across the FastAPI app.
"""
from pydantic import BaseModel
from typing import Optional


# ---------------------------------------------------------------------------
# Sensor data input
# ---------------------------------------------------------------------------

class SensorReadings(BaseModel):
    rpm: float
    temperature_c: float
    vibration_mm_s: float
    pressure_bar: float
    current_amps: float
    noise_db: float


class SensorData(BaseModel):
    machine_type: str
    symptom_description: str = ""
    scenario_id: Optional[str] = None      # optional: front-end can pass the preset ID
    sensors: SensorReadings


# ---------------------------------------------------------------------------
# Diagnosis output — four logical stages
# ---------------------------------------------------------------------------

class SymptomItem(BaseModel):
    name: str
    severity: str          # low | medium | high
    description: str = ""


class FaultItem(BaseModel):
    name: str
    confidence: float      # 0.0 - 1.0
    description: str = ""


class RootCause(BaseModel):
    summary: str
    cause_chain: list[str] = []


class RepairGuidance(BaseModel):
    urgency: str           # immediate | soon | scheduled
    steps: list[str] = []


class DiagnosisResult(BaseModel):
    symptoms: list[SymptomItem] = []
    faults: list[FaultItem] = []
    root_cause: Optional[RootCause] = None
    repair_guidance: Optional[RepairGuidance] = None


# ---------------------------------------------------------------------------
# Full API response
# ---------------------------------------------------------------------------

class DiagnosisResponse(BaseModel):
    scenario_id: Optional[str] = None
    machine_type: str
    sensor_data: SensorReadings
    diagnosis: DiagnosisResult

    # Overall aggregated indicators (computed by pipeline)
    severity: str = "unknown"          # low | medium | high | critical
    overall_confidence: float = 0.0    # 0.0 - 1.0, top fault confidence

    # RAG layer output — documents retrieved and injected as context
    retrieved_knowledge: list[str] = []   # titles of retrieved documents

    # AI layer metadata
    ai_source: str = "fallback"   # "fallback" | "granite" | "langflow"
    model_used: str = "none"
    ai_backend: str = "fallback"
    rag_backend: str = "simple"
