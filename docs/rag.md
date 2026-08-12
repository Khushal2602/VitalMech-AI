# RAG in VitalMech

## What is RAG?

**RAG = Retrieval-Augmented Generation.**

Instead of relying only on information learned during model training, the application retrieves relevant documents from its own knowledge base and supplies them as context to the model during inference.

## VitalMech RAG Flow

```text
Sensor Data + Symptom Description
              ↓
      Diagnostic Query
              ↓
       SimpleRetriever
              ↓
   Top 3 Relevant Documents
              ↓
   Retrieved Mechanical Context
              ↓
        IBM Granite
              ↓
      Structured Diagnosis
```

## Current Retriever

`SimpleRetriever` uses a local JSON knowledge base and a BM25-inspired keyword scoring approach with title boosting. It returns the most relevant documents for the diagnostic query.

The current knowledge base contains **14 mechanical fault documents**.

## Why RAG is useful here

Mechanical fault diagnosis depends on domain-specific relationships between symptoms, operating conditions, causes, and maintenance actions. RAG gives Granite relevant project-specific context instead of requiring every detail to be generated from the model's general knowledge alone.

## Alternative

The repository also contains `ChromaRetriever`, allowing a vector-database approach to be evaluated later without changing the retriever interface used by the pipeline.
