"""
test_pipeline_granite.py -- Phase 3B: Granite + RAG pipeline integration test.

Calls run_diagnosis() directly (no HTTP, no uvicorn) with the bearing_failure
scenario. Makes exactly ONE Granite inference call.

Run from backend/ directory:
    python test_pipeline_granite.py

SECURITY: API key is never printed.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

SEP = "-" * 70


def mask(v: str, show: int = 4) -> str:
    if not v or len(v) <= show:
        return "[NOT SET]"
    return v[:show] + "*" * min(len(v) - show, 36)


def main():
    import os
    print(SEP)
    print("VitalMech -- Phase 3B: Granite + RAG Pipeline Integration Test")
    print("Scenario: bearing_failure | ONE Granite call | API key never printed")
    print(SEP)

    # Show active config (no secrets)
    print("\n[CONFIG]")
    print(f"  AI_BACKEND       : {os.getenv('AI_BACKEND', 'granite')}")
    print(f"  RAG_BACKEND      : {os.getenv('RAG_BACKEND', 'simple')}")
    print(f"  WATSONX_MODEL_ID : {os.getenv('WATSONX_MODEL_ID', '[NOT SET]')}")
    print(f"  WATSONX_API_KEY  : {mask(os.getenv('WATSONX_API_KEY', ''))}")
    print(f"  WATSONX_PROJECT_ID: {mask(os.getenv('WATSONX_PROJECT_ID', ''))}")

    # Build bearing_failure sensor data (matches the preset exactly)
    from models import SensorData, SensorReadings
    sensor_data = SensorData(
        scenario_id="bearing_failure",
        machine_type="Induction Motor",
        symptom_description="Unusual grinding noise reported by operator. Machine running rough.",
        sensors=SensorReadings(
            rpm=1740,
            temperature_c=78,
            vibration_mm_s=14.3,
            pressure_bar=4.1,
            current_amps=24,
            noise_db=89,
        ),
    )

    # Step 1: show RAG retrieval before calling the pipeline
    print("\n[STEP 1] RAG retrieval (SimpleRetriever)...")
    from rag.simple_retriever import SimpleRetriever
    from pipeline import _build_rag_query
    retriever = SimpleRetriever()
    query = _build_rag_query(sensor_data)
    print(f"  RAG query: \"{query}\"")
    scored = retriever.retrieve_scored(query, top_k=3)
    print(f"  Retrieved {len(scored)} document(s):")
    for i, doc in enumerate(scored, 1):
        print(f"    [{i}] {doc.title}  (score: {doc.score})")

    # Step 2: show the exact prompt that will be sent to Granite
    print("\n[STEP 2] Prompt preview (first 600 chars)...")
    from ai.prompts import SYSTEM_PROMPT, build_user_prompt
    context_docs = [d.content for d in scored]
    user_prompt = build_user_prompt(sensor_data, context_docs)
    preview = (SYSTEM_PROMPT[:200] + "...") + "\n\n--- USER ---\n" + user_prompt[:400] + "..."
    for line in preview.splitlines():
        print(f"  {line}")

    # Step 3: run the full pipeline (exactly one Granite call inside)
    print("\n[STEP 3] Running diagnosis pipeline (ONE Granite inference call)...")
    from pipeline import run_diagnosis
    try:
        response = run_diagnosis(sensor_data)
    except Exception as exc:
        print(f"[FAIL] Pipeline raised exception: {exc}")
        sys.exit(1)

    # Step 4: report results
    print(f"\n[STEP 4] Pipeline result:")
    print(f"  ai_source         : {response.ai_source}")
    print(f"  model_used        : {response.model_used}")
    print(f"  severity          : {response.severity}")
    print(f"  overall_confidence: {response.overall_confidence}")
    print(f"  fallback_used     : {response.ai_source == 'fallback'}")

    print(f"\n  Retrieved knowledge:")
    for doc in response.retrieved_knowledge:
        print(f"    - {doc}")

    d = response.diagnosis
    print(f"\n  Symptoms ({len(d.symptoms)}):")
    for s in d.symptoms:
        print(f"    [{s.severity.upper()}] {s.name}")

    print(f"\n  Faults ({len(d.faults)}):")
    for f in d.faults:
        print(f"    {f.name}  ({round(f.confidence * 100)}%)")

    if d.root_cause:
        print(f"\n  Root cause summary:")
        print(f"    {d.root_cause.summary}")
        print(f"  Cause chain ({len(d.root_cause.cause_chain)} steps):")
        for i, c in enumerate(d.root_cause.cause_chain, 1):
            print(f"    {i}. {c}")

    if d.repair_guidance:
        print(f"\n  Repair urgency: {d.repair_guidance.urgency.upper()}")
        print(f"  Repair steps ({len(d.repair_guidance.steps)}):")
        for i, step in enumerate(d.repair_guidance.steps, 1):
            txt = step.replace("\u00b0", "°").replace("\u03a9", "Ohm")
            print(f"    {i}. {txt[:100]}")

    # Summary
    print(f"\n{SEP}")
    granite_ok = response.ai_source == "granite"
    print("INTEGRATION TEST SUMMARY")
    print(f"  Granite used        : {'YES' if granite_ok else 'NO -- fallback was used'}")
    print(f"  RAG retrieved       : {len(response.retrieved_knowledge)} documents")
    print(f"  Symptoms returned   : {len(d.symptoms)}")
    print(f"  Faults returned     : {len(d.faults)}")
    print(f"  Root cause present  : {'YES' if d.root_cause else 'NO'}")
    print(f"  Repair steps present: {'YES' if d.repair_guidance and d.repair_guidance.steps else 'NO'}")
    print(f"  API key exposed     : NO")
    print(f"  Additional calls    : NONE")
    print(SEP)

    sys.exit(0)


if __name__ == "__main__":
    main()
