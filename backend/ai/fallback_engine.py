"""
ai/fallback_engine.py -- Deterministic rule-based diagnosis engine.

Used when IBM Granite is unavailable or not yet configured.
Produces a fully structured DiagnosisResult through four logical stages:
  Stage 1 -- Symptom Detection   (sensor threshold rules)
  Stage 2 -- Fault Analysis      (symptom pattern matching against fault profiles)
  Stage 3 -- Root Cause Analysis (fault -> cause mapping)
  Stage 4 -- Repair Guidance     (cause -> action mapping)

IMPORTANT: responses carry ai_source="fallback" and model_used="rule-based-engine".
Never claims that Granite or any LLM produced the output.
"""
from __future__ import annotations

from models import (
    DiagnosisResult,
    FaultItem,
    RepairGuidance,
    RootCause,
    SensorData,
    SymptomItem,
)

# ---------------------------------------------------------------------------
# Sensor thresholds  (warn, danger)
# ---------------------------------------------------------------------------
_THRESHOLDS = {
    "vibration_mm_s":  {"warn": 7.1,  "danger": 11.0},
    "temperature_c":   {"warn": 75.0, "danger": 90.0},
    "noise_db":        {"warn": 80.0, "danger": 90.0},
    "current_amps":    {"warn": 35.0, "danger": 44.0},
    # pressure is inverted — LOW is bad
    "pressure_bar":    {"warn": 2.0,  "danger": 1.5,  "inverted": True},
}

# ---------------------------------------------------------------------------
# Stage 1 — Symptom detection rules
# Each entry: (symptom_name, severity_thresholds, description_fn)
# ---------------------------------------------------------------------------

def _detect_symptoms(s: SensorData) -> list[SymptomItem]:
    r = s.sensors
    symptoms: list[SymptomItem] = []

    # Vibration
    if r.vibration_mm_s >= _THRESHOLDS["vibration_mm_s"]["danger"]:
        symptoms.append(SymptomItem(
            name="High Vibration",
            severity="high",
            description=f"Vibration at {r.vibration_mm_s} mm/s exceeds danger threshold "
                        f"({_THRESHOLDS['vibration_mm_s']['danger']} mm/s). "
                        "Immediate investigation required.",
        ))
    elif r.vibration_mm_s >= _THRESHOLDS["vibration_mm_s"]["warn"]:
        symptoms.append(SymptomItem(
            name="Elevated Vibration",
            severity="medium",
            description=f"Vibration at {r.vibration_mm_s} mm/s exceeds warning threshold "
                        f"({_THRESHOLDS['vibration_mm_s']['warn']} mm/s).",
        ))

    # Temperature
    if r.temperature_c >= _THRESHOLDS["temperature_c"]["danger"]:
        symptoms.append(SymptomItem(
            name="Critical Overtemperature",
            severity="high",
            description=f"Temperature at {r.temperature_c}°C is critically high "
                        f"(danger threshold: {_THRESHOLDS['temperature_c']['danger']}°C).",
        ))
    elif r.temperature_c >= _THRESHOLDS["temperature_c"]["warn"]:
        symptoms.append(SymptomItem(
            name="Elevated Temperature",
            severity="medium",
            description=f"Temperature at {r.temperature_c}°C exceeds warning threshold "
                        f"({_THRESHOLDS['temperature_c']['warn']}°C).",
        ))

    # Noise
    if r.noise_db >= _THRESHOLDS["noise_db"]["danger"]:
        symptoms.append(SymptomItem(
            name="High Acoustic Noise",
            severity="high",
            description=f"Noise level at {r.noise_db} dB. Abnormal sound signature detected.",
        ))
    elif r.noise_db >= _THRESHOLDS["noise_db"]["warn"]:
        symptoms.append(SymptomItem(
            name="Elevated Noise",
            severity="medium",
            description=f"Noise level at {r.noise_db} dB above normal operating range.",
        ))

    # Current
    if r.current_amps >= _THRESHOLDS["current_amps"]["danger"]:
        symptoms.append(SymptomItem(
            name="Excessive Current Draw",
            severity="high",
            description=f"Current at {r.current_amps} A. Motor may be overloaded or winding fault present.",
        ))
    elif r.current_amps >= _THRESHOLDS["current_amps"]["warn"]:
        symptoms.append(SymptomItem(
            name="Elevated Current",
            severity="medium",
            description=f"Current at {r.current_amps} A above normal operating range.",
        ))

    # Pressure (inverted — low is bad)
    if r.pressure_bar <= _THRESHOLDS["pressure_bar"]["danger"]:
        symptoms.append(SymptomItem(
            name="Critically Low Pressure",
            severity="high",
            description=f"Pressure at {r.pressure_bar} bar is critically low "
                        f"(danger threshold: {_THRESHOLDS['pressure_bar']['danger']} bar).",
        ))
    elif r.pressure_bar <= _THRESHOLDS["pressure_bar"]["warn"]:
        symptoms.append(SymptomItem(
            name="Low Pressure",
            severity="medium",
            description=f"Pressure at {r.pressure_bar} bar below normal operating range.",
        ))

    # Operator-reported symptom text keywords
    desc_lower = s.symptom_description.lower()
    if any(w in desc_lower for w in ("grind", "grinding", "metallic", "scraping")):
        symptoms.append(SymptomItem(
            name="Metallic Grinding Noise",
            severity="high",
            description="Operator reports metallic grinding — consistent with bearing wear or metal-to-metal contact.",
        ))
    if any(w in desc_lower for w in ("rattle", "rattling", "crackling", "crackle")):
        symptoms.append(SymptomItem(
            name="Rattling / Crackling Sound",
            severity="medium",
            description="Operator reports rattling or crackling — consistent with cavitation or loose components.",
        ))
    if any(w in desc_lower for w in ("trip", "tripping", "overload", "thermal")):
        symptoms.append(SymptomItem(
            name="Thermal Overload Tripping",
            severity="high",
            description="Machine is tripping on thermal protection — heat dissipation or overloading issue.",
        ))
    if any(w in desc_lower for w in ("shake", "shaking", "wobble", "rhythmic")):
        symptoms.append(SymptomItem(
            name="Rhythmic Shaking",
            severity="medium",
            description="Machine exhibits rhythmic oscillation — consistent with rotor imbalance.",
        ))
    if any(w in desc_lower for w in ("excessive current", "tripping breaker", "breaker")):
        symptoms.append(SymptomItem(
            name="Overcurrent / Breaker Trip",
            severity="high",
            description="Electrical protection is activating — winding fault or mechanical seizure suspected.",
        ))

    # No anomalies detected
    if not symptoms:
        symptoms.append(SymptomItem(
            name="No Anomalies Detected",
            severity="low",
            description="All sensor readings are within normal operating parameters.",
        ))

    return symptoms


# ---------------------------------------------------------------------------
# Stage 2 — Fault Analysis
# Fault profiles: (name, description, required symptom names or keyword checks,
#                  base_confidence, boosters: list of (check_fn, delta))
# ---------------------------------------------------------------------------

def _analyze_faults(s: SensorData, symptom_names: set[str]) -> list[FaultItem]:
    r = s.sensors
    desc_lower = s.symptom_description.lower()
    mt_lower = s.machine_type.lower()

    candidates: list[FaultItem] = []

    # --- Bearing Degradation / Failure ---
    bearing_conf = 0.0
    if r.vibration_mm_s >= 11.0:
        bearing_conf += 0.45
    elif r.vibration_mm_s >= 7.1:
        bearing_conf += 0.25
    if r.temperature_c >= 75.0:
        bearing_conf += 0.15
    if r.noise_db >= 85.0:
        bearing_conf += 0.15
    if any(w in desc_lower for w in ("grind", "grinding", "metallic", "rough", "rumbling")):
        bearing_conf += 0.20
    if "motor" in mt_lower or "pump" in mt_lower:
        bearing_conf += 0.05
    if bearing_conf > 0:
        candidates.append(FaultItem(
            name="Bearing Degradation / Failure",
            confidence=min(round(bearing_conf, 2), 0.97),
            description="Rolling element bearing wear indicated by high vibration, "
                        "elevated temperature, and acoustic noise at bearing frequencies.",
        ))

    # --- Shaft Misalignment ---
    misalign_conf = 0.0
    if r.vibration_mm_s >= 7.1:
        misalign_conf += 0.30
    if r.current_amps >= 35.0:
        misalign_conf += 0.20
    if r.temperature_c >= 65.0:
        misalign_conf += 0.10
    if any(w in desc_lower for w in ("misalign", "vibration", "coupling", "maintenance")):
        misalign_conf += 0.25
    if "shaft" in mt_lower or "coupling" in mt_lower:
        misalign_conf += 0.10
    if misalign_conf > 0:
        candidates.append(FaultItem(
            name="Shaft Misalignment",
            confidence=min(round(misalign_conf, 2), 0.95),
            description="Shaft misalignment indicated by vibration increase and elevated "
                        "current draw, particularly after maintenance.",
        ))

    # --- Pump Cavitation ---
    cavitation_conf = 0.0
    if r.pressure_bar <= 2.0:
        cavitation_conf += 0.35
    if r.pressure_bar <= 1.5:
        cavitation_conf += 0.20
    if r.noise_db >= 85.0:
        cavitation_conf += 0.20
    if r.vibration_mm_s >= 5.0:
        cavitation_conf += 0.10
    if any(w in desc_lower for w in ("rattle", "crackling", "crackle", "cavitation", "flow")):
        cavitation_conf += 0.25
    if "pump" in mt_lower:
        cavitation_conf += 0.10
    if cavitation_conf > 0:
        candidates.append(FaultItem(
            name="Pump Cavitation",
            confidence=min(round(cavitation_conf, 2), 0.96),
            description="Cavitation indicated by low suction pressure, erratic flow, "
                        "and characteristic crackling/rattling noise.",
        ))

    # --- Overheating / Thermal Fault ---
    thermal_conf = 0.0
    if r.temperature_c >= 90.0:
        thermal_conf += 0.50
    elif r.temperature_c >= 75.0:
        thermal_conf += 0.30
    if r.pressure_bar <= 3.0:
        thermal_conf += 0.10
    if any(w in desc_lower for w in ("trip", "tripping", "overload", "thermal", "temperature", "cooling")):
        thermal_conf += 0.25
    if "compressor" in mt_lower or "motor" in mt_lower or "engine" in mt_lower:
        thermal_conf += 0.05
    if thermal_conf > 0:
        candidates.append(FaultItem(
            name="Overheating / Thermal Fault",
            confidence=min(round(thermal_conf, 2), 0.97),
            description="Machine overheating indicated by temperature above safe limit. "
                        "Cooling system or ventilation may be compromised.",
        ))

    # --- Rotor Imbalance ---
    imbalance_conf = 0.0
    if r.vibration_mm_s >= 7.1:
        imbalance_conf += 0.30
    if any(w in desc_lower for w in ("shake", "shaking", "wobble", "rhythmic", "imbalance", "balance")):
        imbalance_conf += 0.35
    if "fan" in mt_lower or "blower" in mt_lower:
        imbalance_conf += 0.15
    if imbalance_conf > 0:
        candidates.append(FaultItem(
            name="Rotor Imbalance",
            confidence=min(round(imbalance_conf, 2), 0.95),
            description="Rotor imbalance indicated by rhythmic vibration at running speed, "
                        "consistent with material build-up or lost balance weight.",
        ))

    # --- Motor Electrical Fault ---
    elec_conf = 0.0
    if r.current_amps >= 44.0:
        elec_conf += 0.55
    elif r.current_amps >= 35.0:
        elec_conf += 0.30
    if r.temperature_c >= 80.0:
        elec_conf += 0.15
    if any(w in desc_lower for w in ("current", "breaker", "trip", "electrical", "winding", "phase")):
        elec_conf += 0.25
    if "motor" in mt_lower:
        elec_conf += 0.05
    if elec_conf > 0:
        candidates.append(FaultItem(
            name="Motor Electrical Fault",
            confidence=min(round(elec_conf, 2), 0.97),
            description="Electrical fault indicated by excessive current draw. "
                        "Possible winding insulation failure, phase loss, or mechanical seizure.",
        ))

    # --- Oil Starvation / Lubrication Failure ---
    oil_conf = 0.0
    if r.temperature_c >= 90.0:
        oil_conf += 0.30
    elif r.temperature_c >= 80.0:
        oil_conf += 0.15
    if r.vibration_mm_s >= 7.0:
        oil_conf += 0.15
    if any(w in desc_lower for w in ("oil", "lubrication", "starvation", "lubricant", "gearbox")):
        oil_conf += 0.35
    if "gearbox" in mt_lower:
        oil_conf += 0.15
    if oil_conf > 0:
        candidates.append(FaultItem(
            name="Oil Starvation / Lubrication Failure",
            confidence=min(round(oil_conf, 2), 0.95),
            description="Lubrication failure indicated by high temperature and rising vibration, "
                        "consistent with oil film breakdown.",
        ))

    # Sort by confidence descending, return top 3
    candidates.sort(key=lambda f: f.confidence, reverse=True)

    # If nothing scored, return a generic low-confidence entry
    if not candidates:
        return [FaultItem(
            name="No Fault Identified",
            confidence=0.10,
            description="Sensor readings are within acceptable ranges. Continue routine monitoring.",
        )]

    return candidates[:3]


# ---------------------------------------------------------------------------
# Stage 3 — Root Cause Analysis
# ---------------------------------------------------------------------------
_ROOT_CAUSE_MAP: dict[str, tuple[str, list[str]]] = {
    "Bearing Degradation / Failure": (
        "Progressive bearing wear due to lubrication breakdown, contamination, or overloading.",
        [
            "Lubrication film deterioration under sustained load",
            "Micro-pitting and fatigue crack propagation on rolling surfaces",
            "Spalling and material loss causing vibration and heat generation",
            "Increased friction leading to thermal runaway if uncorrected",
        ],
    ),
    "Shaft Misalignment": (
        "Shaft centrelines are not co-linear, imposing cyclic bending stress on the coupling and bearings.",
        [
            "Incorrect shaft alignment during installation or post-maintenance reassembly",
            "Thermal growth of machine during warm-up shifting the alignment condition",
            "Cyclic bending load transferred to coupling elements and bearings",
            "Progressive coupling wear worsening the misalignment over time",
        ],
    ),
    "Pump Cavitation": (
        "Vapour bubble formation in the pump suction zone due to insufficient Net Positive Suction Head (NPSH).",
        [
            "Suction pressure falls below fluid vapour pressure at operating temperature",
            "Vapour bubbles form at impeller inlet and collapse violently on pressure side",
            "Implosion energy erodes impeller vane surfaces",
            "Erosion reduces hydraulic efficiency, worsening the cavitation cycle",
        ],
    ),
    "Overheating / Thermal Fault": (
        "Heat generation exceeds the machine's capacity to dissipate it through the cooling system.",
        [
            "Blocked cooling fins, clogged air filters, or failed cooling fan",
            "Operating current above rated full-load amps causing I\u00b2R losses",
            "Elevated ambient temperature reducing available cooling margin",
            "Winding insulation degradation increasing electrical resistance",
        ],
    ),
    "Rotor Imbalance": (
        "Unequal mass distribution around the rotor axis generates centrifugal force at running speed.",
        [
            "Material deposits (dust, scale, product) accumulating asymmetrically on rotor",
            "Loss of balance weight or damaged/eroded rotor blade",
            "Centrifugal force transmitted as vibration to bearings and machine structure",
            "Sustained vibration accelerating bearing fatigue and fastener loosening",
        ],
    ),
    "Motor Electrical Fault": (
        "Electrical imbalance in the motor supply or winding causing excess current and heat.",
        [
            "Phase voltage imbalance or loss causing unbalanced current distribution",
            "Winding insulation degradation leading to inter-turn short circuit",
            "Increased current draw raises I\u00b2R heat in stator windings",
            "Thermal stress progressively degrades remaining insulation",
        ],
    ),
    "Oil Starvation / Lubrication Failure": (
        "Inadequate oil film in gearbox or bearing housing allows metal-to-metal contact.",
        [
            "Oil level below minimum due to leak or failure to top up",
            "Oil pump wear reducing delivery pressure to critical surfaces",
            "Lubricant viscosity breakdown at elevated temperature",
            "Metal-to-metal contact generating friction heat and wear debris",
        ],
    ),
}

def _analyze_root_cause(top_fault: FaultItem) -> RootCause:
    entry = _ROOT_CAUSE_MAP.get(top_fault.name)
    if entry:
        return RootCause(summary=entry[0], cause_chain=entry[1])
    return RootCause(
        summary=f"Root cause analysis for '{top_fault.name}' requires detailed inspection.",
        cause_chain=["Perform physical inspection to identify specific root cause."],
    )


# ---------------------------------------------------------------------------
# Stage 4 — Repair Guidance
# ---------------------------------------------------------------------------
_REPAIR_MAP: dict[str, tuple[str, list[str]]] = {
    "Bearing Degradation / Failure": (
        "immediate",
        [
            "Stop machine if vibration exceeds 14 mm/s or temperature exceeds 95\u00b0C",
            "Collect oil or grease sample for particle count and ferrographic analysis",
            "Perform vibration spectrum analysis to confirm bearing defect frequencies",
            "Replace bearing(s) — inspect shaft and housing bore for scoring",
            "Replace worn seals to prevent re-contamination",
            "Re-lubricate with correct lubricant type and quantity per OEM specification",
            "Perform precision laser shaft alignment after bearing replacement",
            "Re-commission with vibration baseline measurement",
        ],
    ),
    "Shaft Misalignment": (
        "soon",
        [
            "Check for soft foot — correct before any alignment work",
            "Allow machine to reach operating temperature before hot alignment check",
            "Perform precision laser shaft alignment — target offset <0.05 mm, angularity <0.05 mm/100 mm",
            "Relieve any pipe strain — install flexible connections if required",
            "Inspect and replace worn coupling elements",
            "Verify alignment after first run at operating temperature",
            "Document alignment values for future reference",
        ],
    ),
    "Pump Cavitation": (
        "soon",
        [
            "Check and clean suction strainer — most common and quickest fix",
            "Verify suction isolation valve is fully open",
            "Check suction pipe for blockages, kinks, or undersized sections",
            "Reduce pump speed if VFD-equipped to operate closer to Best Efficiency Point (BEP)",
            "Increase suction tank level if available",
            "Inspect and replace shaft seal if air ingress is suspected",
            "Inspect impeller for erosion damage — replace if pitting is present",
        ],
    ),
    "Overheating / Thermal Fault": (
        "immediate",
        [
            "Allow machine to cool before inspection",
            "Clean all cooling fins, air inlet screens, and ventilation passages",
            "Verify cooling fan is operational and rotating in correct direction",
            "Confirm all three supply phases are present and balanced",
            "Measure operating current and compare to nameplate full-load amps (FLA)",
            "Test winding insulation resistance with megger (minimum 1 M\u03a9 phase-to-earth)",
            "Check overload relay setting against motor nameplate FLA",
        ],
    ),
    "Rotor Imbalance": (
        "scheduled",
        [
            "Inspect rotor for material build-up — clean fan blades and impeller thoroughly",
            "Check for missing, damaged, or loose balance weights",
            "Inspect for asymmetric blade erosion or damage",
            "Perform in-situ dynamic balancing using vibration analyser and trial weights",
            "If in-situ balancing is insufficient, remove rotor for workshop balancing",
            "Check shaft runout — replace shaft if runout exceeds 0.05 mm TIR",
            "Verify vibration level after balancing (<2.5 mm/s RMS for fans)",
        ],
    ),
    "Motor Electrical Fault": (
        "immediate",
        [
            "Measure and record supply voltage on all three phases at motor terminals",
            "Measure and compare current on all three phases — identify imbalance",
            "Perform insulation resistance test (megger) — phase-to-phase and phase-to-earth",
            "Check and tighten all terminal connections in motor junction box",
            "Verify driven machine rotates freely by hand to rule out mechanical seizure",
            "If winding fault is confirmed, arrange motor rewind or replacement",
            "Install voltage monitoring relay to detect future phase loss events",
        ],
    ),
    "Oil Starvation / Lubrication Failure": (
        "immediate",
        [
            "Check and top up oil level immediately — do not continue operating",
            "Replace oil filter — always replace filter when investigating low pressure",
            "Send oil sample for laboratory analysis (viscosity, TAN, wear metals)",
            "Flush system and replace oil if contamination or degradation is confirmed",
            "Inspect and repair source of oil loss (seals, gaskets, drain fittings)",
            "Test oil pump output pressure — replace if below OEM specification",
            "Set up oil temperature monitoring with high-temperature alarm",
        ],
    ),
}

def _generate_repair(top_fault: FaultItem) -> RepairGuidance:
    entry = _REPAIR_MAP.get(top_fault.name)
    if entry:
        return RepairGuidance(urgency=entry[0], steps=entry[1])
    return RepairGuidance(
        urgency="scheduled",
        steps=["Consult OEM maintenance manual for specific repair procedures.",
               "Schedule inspection with qualified maintenance engineer."],
    )


# ---------------------------------------------------------------------------
# Severity aggregation
# ---------------------------------------------------------------------------
def _compute_severity(symptoms: list[SymptomItem], top_confidence: float) -> str:
    high_count = sum(1 for s in symptoms if s.severity == "high")
    if high_count >= 2 or (high_count >= 1 and top_confidence >= 0.75):
        return "critical"
    if high_count == 1 or top_confidence >= 0.65:
        return "high"
    medium_count = sum(1 for s in symptoms if s.severity == "medium")
    if medium_count >= 1:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def run_fallback_diagnosis(sensor_data: SensorData) -> DiagnosisResult:
    """
    Run all four diagnostic stages deterministically from sensor data.
    Returns a fully populated DiagnosisResult.
    ai_source is set by the pipeline layer, not here.
    """
    # Stage 1
    symptoms = _detect_symptoms(sensor_data)
    symptom_names = {s.name for s in symptoms}

    # Stage 2
    faults = _analyze_faults(sensor_data, symptom_names)

    # Stage 3 & 4  (driven by top fault)
    top_fault = faults[0]
    root_cause = _analyze_root_cause(top_fault)
    repair_guidance = _generate_repair(top_fault)

    return DiagnosisResult(
        symptoms=symptoms,
        faults=faults,
        root_cause=root_cause,
        repair_guidance=repair_guidance,
    )
