# VitalMech — AI-Powered Mechanical Health & Fault Diagnosis
## Hackathon Implementation Plan (Revised)

---

## Top-Level Overview

**Goal:** Build a working demo of VitalMech — a Smart Mechanical Fault Diagnosis Agent (Problem Statement #34) for a college hackathon.

**Scope:** A React + Vite + Tailwind frontend connected to a Python FastAPI backend. The backend runs a single IBM Granite LLM call that produces structured output representing four logical diagnostic stages. A modular RAG retrieval layer injects domain knowledge into the prompt. Sensor data is simulated via preset scenarios.

**Core Architectural Decisions:**
- **Single LLM call MVP:** One Granite call returns a JSON object with four sections: symptoms, faults, root_cause, repair_guidance. The four agents are represented as logical stages in the prompt and in the UI — not as four separate API calls. This is the fastest path to a complete, debuggable demo.
- **Modular AI layer:** The Granite client is behind a thin `AIClient` interface. Langflow or Orchestrate can be wired in by swapping one module without touching agents or API routes.
- **Modular RAG layer:** The retrieval layer is behind a `Retriever` interface. MVP uses simple keyword/JSON lookup against local documents. ChromaDB + sentence-transformers can be dropped in later by implementing the same interface.
- **Configurable model ID:** The Granite model ID is read from the `.env` file. No model name is hardcoded anywhere in the application code.

**Key Constraint:** Must use IBM Granite LLM as the primary AI model (via watsonx.ai).

---

## Revised Architecture Diagram

```
Frontend (React + Vite + Tailwind)
  └── Dashboard
        ├── ScenarioSelector  →  GET /api/sensor/scenarios
        ├── SensorPanel       →  (loaded from scenario selection)
        ├── AgentTimeline     →  (4-stage visual driven by UI state)
        ├── FaultCard         →  (populated from diagnosis response)
        └── RepairGuidance    →  (populated from diagnosis response)

Backend (FastAPI)
  └── POST /api/diagnose
        └── DiagnosisPipeline
              ├── Retriever (interface)
              │     ├── [MVP]  SimpleRetriever   — keyword match on local JSON docs
              │     └── [opt]  ChromaRetriever   — ChromaDB + sentence-transformers
              └── AIClient (interface)
                    ├── [MVP]  GraniteClient     — single call to watsonx.ai
                    └── [opt]  LangflowClient    — delegates to Langflow flow endpoint
                               OrchestrateClient — delegates to Orchestrate agent
```

---

## Folder Structure

```
vitalmech/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx          # Main layout, top-level state
│   │   │   ├── ScenarioSelector.jsx   # Dropdown of 8 fault scenarios
│   │   │   ├── SensorPanel.jsx        # Sensor metric cards
│   │   │   ├── AgentTimeline.jsx      # 4-stage visual progress stepper
│   │   │   ├── FaultCard.jsx          # Symptoms + fault confidence display
│   │   │   └── RepairGuidance.jsx     # Urgency badge + repair steps
│   │   ├── hooks/
│   │   │   └── useDiagnosis.js        # Axios POST hook, loading/error state
│   │   ├── data/
│   │   │   └── sensorPresets.js       # 8 fault scenarios mirrored from backend
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js                 # includes /api proxy to localhost:8000
│   └── package.json
│
├── backend/
│   ├── main.py                        # FastAPI app, CORS, startup, routes
│   ├── pipeline.py                    # run_diagnosis() — wires retriever + AI client
│   ├── models.py                      # Pydantic: SensorData, DiagnosisResponse, etc.
│   │
│   ├── ai/
│   │   ├── base.py                    # AIClient abstract base class
│   │   ├── granite_client.py          # GraniteClient: watsonx.ai single-call impl
│   │   ├── langflow_client.py         # LangflowClient stub (wired in via env flag)
│   │   └── prompts.py                 # Single unified diagnostic prompt builder
│   │
│   ├── rag/
│   │   ├── base.py                    # Retriever abstract base class
│   │   ├── simple_retriever.py        # MVP: keyword match on knowledge JSON
│   │   └── chroma_retriever.py        # Optional: ChromaDB impl of same interface
│   │
│   ├── data/
│   │   ├── fault_scenarios.json       # 8 simulated sensor scenarios
│   │   └── sensor_simulator.py        # get_all_scenarios(), get_scenario(name)
│   │
│   ├── knowledge/
│   │   └── mechanical_faults.json     # 15 fault knowledge documents for RAG
│   │
│   └── requirements.txt
│
├── .env.example                       # WATSONX_API_KEY, PROJECT_ID, URL, MODEL_ID
├── vitalmech-plan.md
├── README.md
└── DEMO_SCRIPT.md
```

---

## Modular Interface Design

### AIClient Interface (`backend/ai/base.py`)

```
AIClient (abstract)
  └── diagnose(sensor_data: dict, context_docs: list[str]) -> DiagnosisResult
        [GraniteClient]    — single watsonx.ai call, parses JSON response
        [LangflowClient]   — POST to Langflow flow URL, maps response to DiagnosisResult
        [OrchestrateClient]— POST to Orchestrate agent endpoint, maps response
```

The active implementation is selected by the `AI_BACKEND` env var (`granite` | `langflow` | `orchestrate`). Defaults to `granite`.

### Retriever Interface (`backend/rag/base.py`)

```
Retriever (abstract)
  └── retrieve(query: str, top_k: int) -> list[str]
        [SimpleRetriever]  — loads mechanical_faults.json, scores by keyword overlap
        [ChromaRetriever]  — ChromaDB persistent store + sentence-transformer embeddings
```

The active implementation is selected by the `RAG_BACKEND` env var (`simple` | `chroma`). Defaults to `simple`.

---

## Single-Call Four-Stage Prompt Design

Rather than four chained LLM calls, one structured prompt asks Granite to act as all four logical agents and return a single JSON object:

```
System: You are VitalMech, an expert mechanical fault diagnosis AI.
        Analyze the sensor data and return ONLY a valid JSON object with
        exactly these four keys: symptoms, faults, root_cause, repair_guidance.

Context (from RAG): {retrieved_knowledge_docs}

Sensor Data: {sensor_readings}
Machine Type: {machine_type}
Reported Symptoms: {symptom_description}

Return format:
{
  "symptoms": [{"name": "...", "severity": "low|medium|high", "description": "..."}],
  "faults":   [{"name": "...", "confidence": 0.0–1.0, "description": "..."}],
  "root_cause": {"summary": "...", "cause_chain": ["...", "..."]},
  "repair_guidance": {"urgency": "immediate|soon|scheduled", "steps": ["1. ...", "2. ..."]}
}
```

The frontend AgentTimeline animates through four stages as the single API call progresses — not because four calls are made, but because each key in the response maps to one agent stage.

---

## Environment Variables (`.env.example`)

```
# IBM watsonx.ai credentials
WATSONX_API_KEY=
WATSONX_PROJECT_ID=
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Granite model ID — verify this against your IBM environment
WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2

# AI backend selection: granite | langflow | orchestrate
AI_BACKEND=granite

# Optional: Langflow endpoint (used only when AI_BACKEND=langflow)
LANGFLOW_FLOW_URL=

# RAG backend selection: simple | chroma
RAG_BACKEND=simple
```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/health` | Backend health check, returns active AI/RAG backend names |
| `GET` | `/api/sensor/scenarios` | List all 8 preset scenario names + metadata |
| `GET` | `/api/sensor/simulate` | Return sensor data for a scenario (`?scenario=bearing_failure`) |
| `POST` | `/api/diagnose` | Full diagnosis — accepts SensorData, returns DiagnosisResponse |

---

## Simulated Sensor Scenarios

| ID | Machine | Fault Injected |
|----|---------|----------------|
| `normal_operation` | Pump | None — all readings nominal |
| `bearing_failure` | Motor | High vibration 12+ mm/s, elevated temp 78°C |
| `overheating` | Compressor | High temp 95°C, low pressure |
| `cavitation` | Pump | Erratic pressure, high noise |
| `shaft_misalignment` | Shaft/Coupling | High vibration, current spike |
| `oil_starvation` | Gearbox | High temp, rising vibration |
| `imbalance` | Fan/Blower | Rhythmic vibration at RPM frequency |
| `electrical_fault` | Motor | High current draw, temp spike |

Sensor schema: `{ rpm, temperature_c, vibration_mm_s, pressure_bar, current_amps, noise_db }`

---

## Implementation Phases

### Phase 1 — Scaffold & Data (do first)
1. Create frontend with Vite + React + Tailwind, configure `/api` proxy
2. Create backend directory, virtual environment, install packages
3. Write `.env.example` and `fault_scenarios.json`
4. Verify backend starts: `uvicorn main:app --reload`
5. Verify frontend starts: `npm run dev`

### Phase 2 — RAG Layer (simple retriever) [COMPLETE]
6. Write `backend/knowledge/mechanical_faults.json` (14 documents) [x]
7. Write `backend/rag/base.py` Retriever interface [x]
8. Write `backend/rag/simple_retriever.py` BM25-inspired retriever with title boosting [x]
9. Verified retrieval with 5 test queries — all 5 passed [x]
   Retriever: `backend/verify_retriever.py`

### Phase 3 — IBM Granite Client
10. Write `backend/ai/base.py` AIClient interface
11. Write `backend/ai/granite_client.py` — IAM token fetch + watsonx.ai POST
12. Write `backend/ai/prompts.py` — unified 4-section diagnostic prompt
13. Test with a direct Python call before wiring into FastAPI

### Phase 4 — Pipeline & API
14. Write `backend/models.py` Pydantic models
15. Write `backend/pipeline.py` — compose retriever + AI client
16. Write `backend/main.py` — FastAPI app, CORS, startup, 4 endpoints
17. Test `POST /api/diagnose` via `/docs` Swagger UI with bearing_failure data

### Phase 5 — Frontend Dashboard
18. Build `Dashboard.jsx` with top-level state shape
19. Build `ScenarioSelector.jsx` + `SensorPanel.jsx`
20. Build `AgentTimeline.jsx` with animated 4-stage stepper
21. Build `FaultCard.jsx` + `RepairGuidance.jsx`
22. Wire `useDiagnosis.js` hook and test full flow end-to-end

### Phase 6 — Integration & Demo Polish
23. Test all 8 scenarios end-to-end
24. Fix any LLM response parsing or CORS issues
25. Add loading/error states to frontend
26. Write `DEMO_SCRIPT.md`

---

## What We Are NOT Building (Revised)

| Skipped Item | Reason |
|---|---|
| ChromaDB + sentence-transformers in MVP | Not required for Phase 1–5; simple retriever is sufficient; interface is ready for upgrade |
| Four separate Granite LLM calls | One structured call is faster to build, debug, and demo; expandable later |
| IBM Langflow / Orchestrate in MVP | Interface stub exists; can wire in during Phase 6 if IBM environment access is confirmed |
| Real IoT / MQTT | No hardware; preset scenarios are cleaner for demo |
| User authentication | No value for a single-session demo |
| PostgreSQL / MongoDB | No persistent storage needed |
| Docker / CI/CD | Overkill for a local hackathon demo |
| Unit tests | Out of scope for timeline |
| Mobile responsiveness | Desktop presentation only |
