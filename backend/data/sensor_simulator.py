"""
sensor_simulator.py — loads fault_scenarios.json and exposes helper functions.
"""
import json
import random
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "fault_scenarios.json"

def _load() -> list[dict]:
    with open(_DATA_FILE, "r") as f:
        return json.load(f)

def get_all_scenarios() -> list[dict]:
    """Return all scenario metadata (without the raw sensor dict for list views)."""
    scenarios = _load()
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "machine_type": s["machine_type"],
            "symptom_description": s["symptom_description"],
        }
        for s in scenarios
    ]

def get_scenario(scenario_id: str) -> dict | None:
    """Return a single scenario by ID, or None if not found."""
    for s in _load():
        if s["id"] == scenario_id:
            return s
    return None

def get_random_scenario() -> dict:
    """Return a random scenario (full data including sensors)."""
    return random.choice(_load())
