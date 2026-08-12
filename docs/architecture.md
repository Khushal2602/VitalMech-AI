# VitalMech Architecture

## High-Level Flow

```text
                    Machine Telemetry
                           │
                           ▼
                ┌─────────────────────┐
                │ Symptom Detection   │
                │   Logical Stage     │
                └──────────┬──────────┘
                           │
                           ▼
                  RAG Knowledge Base
                           │
                           ▼
                ┌─────────────────────┐
                │   IBM Granite       │
                │   via watsonx.ai    │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │   Fault Analysis    │
                │   Logical Stage     │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │    Root Cause       │
                │   Logical Stage     │
                └──────────┬──────────┘
                           │
                           ▼
                ┌─────────────────────┐
                │  Repair Guidance    │
                │   Logical Stage     │
                └──────────┬──────────┘
                           │
                           ▼
                    React Dashboard
```

## Backend Components

### `pipeline.py`

Coordinates the diagnosis request. It builds a retrieval query, retrieves the top three knowledge documents, calls the selected AI backend, and aggregates the final response.

### AI layer

- `base.py` — common AI client interface
- `granite_client.py` — IBM Granite/watsonx.ai implementation
- `fallback_engine.py` — deterministic fallback diagnosis
- `langflow_client.py` — Langflow integration stub
- `prompts.py` — diagnostic prompt construction

### RAG layer

- `base.py` — retriever interface
- `simple_retriever.py` — local keyword/BM25-inspired retrieval
- `chroma_retriever.py` — alternative Chroma-based retriever

### Data

- `fault_scenarios.json` — eight simulated machine scenarios
- `mechanical_faults.json` — 14 mechanical knowledge documents

## Important Implementation Detail

The current MVP represents the four agents as **logical stages** in a single structured Granite diagnosis call. This is intentionally different from four independent LLM calls and should be described accurately in technical demonstrations.
