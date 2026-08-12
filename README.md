# VitalMech — AI-Powered Mechanical Fault Diagnosis

> **Problem Statement #34 — Smart Mechanical Fault Diagnosis Agent**

VitalMech is an AI-powered mechanical fault diagnosis platform that analyzes simulated machine telemetry, retrieves relevant mechanical knowledge using **Retrieval-Augmented Generation (RAG)**, and uses **IBM Granite** to produce structured diagnostic results, root-cause analysis, and repair guidance.

## Problem

Mechanical systems such as motors, pumps, compressors, gearboxes, and related equipment can develop faults that are difficult to diagnose quickly. Manual inspection and experience-based troubleshooting can cause delayed detection, increased downtime, and inefficient repair decisions.

## Solution

VitalMech follows a knowledge-grounded diagnostic workflow:

```text
Machine Telemetry
      ↓
Symptom Detection
      ↓
RAG Knowledge Retrieval
      ↓
IBM Granite Reasoning
      ↓
Fault Analysis
      ↓
Root Cause Identification
      ↓
Repair Guidance
      ↓
React Dashboard
```

The four diagnostic stages are implemented as **logical agentic stages** in the current MVP. They are represented in the prompt, backend response schema, and dashboard workflow; the current implementation uses a single structured Granite inference call rather than four independent LLM calls.

## Key Features

- **Four-stage agentic workflow:** Symptom Detection, Fault Analysis, Root Cause, Repair Guidance
- **RAG knowledge retrieval:** local mechanical fault knowledge base with 14 documents
- **IBM Granite:** model inference through IBM watsonx.ai
- **Multi-sensor analysis:** RPM, temperature, vibration, pressure, current, and noise
- **8 simulated fault scenarios** for demonstration and testing
- **Deterministic fallback engine** when Granite credentials/inference are unavailable
- **Interactive React dashboard** with sensor readings, diagnosis, agent timeline, and repair guidance
- **Modular AI and RAG interfaces** for future Langflow, Orchestrate, or vector-retrieval integrations

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 19 + Vite + Tailwind CSS |
| Backend | Python 3.11+ + FastAPI + Uvicorn |
| Foundation Model | IBM Granite via watsonx.ai |
| AI Development | IBM Bob |
| RAG | SimpleRetriever; optional Chroma retriever |
| Knowledge Base | 14 mechanical fault documents (JSON) |
| Sensor Data | 8 simulated fault scenarios |
| HTTP Client | HTTPX |

## Project Structure

```text
VitalMech/
├── backend/
│   ├── ai/
│   │   ├── base.py
│   │   ├── fallback_engine.py
│   │   ├── granite_client.py
│   │   ├── langflow_client.py
│   │   └── prompts.py
│   ├── data/
│   │   ├── fault_scenarios.json
│   │   └── sensor_simulator.py
│   ├── knowledge/
│   │   └── mechanical_faults.json
│   ├── rag/
│   │   ├── base.py
│   │   ├── chroma_retriever.py
│   │   └── simple_retriever.py
│   ├── main.py
│   ├── models.py
│   ├── pipeline.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── hooks/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── package-lock.json
│
├── docs/
├── screenshots/
├── presentation/
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## RAG Pipeline

**RAG (Retrieval-Augmented Generation)** retrieves relevant mechanical knowledge before the model generates a diagnosis.

```text
Sensor Data + Symptoms
        ↓
Diagnostic Query
        ↓
SimpleRetriever
        ↓
Top Relevant Fault Documents
        ↓
Context + Sensor Data
        ↓
IBM Granite
        ↓
Structured Diagnosis
```

The current MVP uses a local JSON knowledge base and a keyword/BM25-inspired `SimpleRetriever`. A Chroma-based retriever is included as an alternative implementation.

Read more: [`docs/rag.md`](docs/rag.md)

## Four Diagnostic Agents

| Agent | Responsibility | Output |
|---|---|---|
| Symptom Detection Agent | Identifies abnormal sensor patterns | Symptoms and severity |
| Fault Analysis Agent | Matches symptoms with retrieved fault knowledge | Probable fault(s) |
| Root Cause Agent | Determines the likely physical cause | Root cause and cause chain |
| Repair Guidance Agent | Converts diagnosis into maintenance actions | Urgency and repair steps |

Read more: [`docs/agent-workflow.md`](docs/agent-workflow.md)

## System Architecture

The backend uses two modular interfaces:

- `AIClient` — currently backed by `GraniteClient`; a `LangflowClient` stub is also present.
- `Retriever` — currently backed by `SimpleRetriever`; a `ChromaRetriever` implementation is also present.

Read more: [`docs/architecture.md`](docs/architecture.md)

## Setup

### Prerequisites

- Python 3.11+
- Node.js and npm
- IBM watsonx.ai credentials for Granite inference

### 1. Configure environment

From the repository root:

```bash
cp .env.example backend/.env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example backend/.env
```

Then fill in the IBM credentials in `backend/.env`.

**Never commit `backend/.env` or any real API key.**

### 2. Backend

```bash
cd backend
python -m venv venv
```

Windows:

```powershell
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the API:

```bash
uvicorn main:app --reload --port 8000
```

API documentation: `http://localhost:8000/docs`

### 3. Frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The dashboard is normally available at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check active AI/RAG backend |
| GET | `/api/sensor/scenarios` | List simulated scenarios |
| GET | `/api/sensor/simulate` | Generate scenario sensor data |
| POST | `/api/diagnose` | Run the full diagnosis pipeline |

## Simulated Scenarios

The current dataset contains eight scenarios:

- Normal operation
- Bearing failure
- Overheating
- Cavitation
- Shaft misalignment
- Oil starvation
- Imbalance
- Electrical fault

## Example Diagnosis

Example input:

```text
RPM: 1740
Temperature: 78°C
Vibration: 14.3 mm/s
Pressure: 4.1 bar
Current: 24 A
Noise: 89 dB
```

The workflow can detect high vibration, elevated temperature, and high noise, retrieve relevant bearing/motor knowledge, and produce a structured fault, root cause, and repair recommendation.

## Current Limitations

- Sensor telemetry is simulated rather than collected from physical equipment.
- The knowledge base is limited to the included mechanical fault documents.
- The four agents are logical stages in the current MVP, not four independent autonomous model calls.
- Real-world deployment requires validation against representative machine data and qualified engineering procedures.

## Future Scope

- Live IoT telemetry through MQTT/Kafka
- Historical degradation tracking and predictive time-series models
- OBD-II/CAN integration for vehicles
- Multimodal diagnostics using acoustic and thermal data
- Automated maintenance alerts

## Documentation

- [`docs/architecture.md`](docs/architecture.md) — system architecture
- [`docs/agent-workflow.md`](docs/agent-workflow.md) — four diagnostic stages
- [`docs/rag.md`](docs/rag.md) — RAG pipeline
- [`docs/setup.md`](docs/setup.md) — setup and troubleshooting
- [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md) — concise presentation/demo flow

## Security

API keys and project credentials must remain in local environment files. The repository intentionally excludes `.env` files through `.gitignore`.

## License

MIT License. See [`LICENSE`](LICENSE).
