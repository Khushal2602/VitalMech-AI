"""
ai/prompts.py — Unified diagnostic prompt builder for IBM Granite.

One structured prompt returns a JSON object with four keys:
  symptoms, faults, root_cause, repair_guidance

This keeps the full prompt logic in one place, separate from the HTTP client.
"""
import json
from models import SensorData


SYSTEM_PROMPT = """You are VitalMech, an expert AI system for mechanical fault diagnosis.
You analyze industrial machine sensor data and provide structured diagnostic assessments.

You will be given:
1. Machine sensor readings (RPM, temperature, vibration, pressure, current, noise)
2. Relevant knowledge context retrieved from a mechanical fault database
3. The machine type and reported symptoms

You MUST respond with ONLY a valid JSON object — no explanation, no markdown, no extra text.
The JSON must have exactly these four keys: symptoms, faults, root_cause, repair_guidance.

Response format:
{
  "symptoms": [
    {"name": "string", "severity": "low|medium|high", "description": "string"}
  ],
  "faults": [
    {"name": "string", "confidence": 0.0, "description": "string"}
  ],
  "root_cause": {
    "summary": "string",
    "cause_chain": ["string", "string"]
  },
  "repair_guidance": {
    "urgency": "immediate|soon|scheduled",
    "steps": ["string", "string"]
  }
}"""


# Maximum characters to include per retrieved document.
# Full docs are ~2000 chars; 500 chars captures fault name, symptoms, and
# key sensor thresholds without exhausting the model's useful input window.
_MAX_DOC_CHARS = 500


def build_user_prompt(sensor_data: SensorData, context_docs: list[str]) -> str:
    """Build the user-facing prompt that includes sensor data and RAG context."""
    sensors = sensor_data.sensors

    # Truncate each doc to keep total context within a useful token budget
    trimmed = [d[:_MAX_DOC_CHARS].rstrip() + ("..." if len(d) > _MAX_DOC_CHARS else "")
               for d in context_docs]
    context_block = "\n---\n".join(trimmed) if trimmed else "No additional context available."

    sensor_block = (
        f"RPM: {sensors.rpm} | Temp: {sensors.temperature_c}C | "
        f"Vibration: {sensors.vibration_mm_s} mm/s | Pressure: {sensors.pressure_bar} bar | "
        f"Current: {sensors.current_amps} A | Noise: {sensors.noise_db} dB"
    )

    return f"""KNOWLEDGE CONTEXT (retrieved):
{context_block}

MACHINE: {sensor_data.machine_type}
SYMPTOMS REPORTED: {sensor_data.symptom_description}
SENSOR READINGS: {sensor_block}

Return ONLY the JSON diagnosis object."""
