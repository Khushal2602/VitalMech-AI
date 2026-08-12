# Four-Agent Diagnostic Workflow

VitalMech divides the diagnosis into four logical agentic stages.

## 1. Symptom Detection Agent

**Input:** machine telemetry and symptom description.

**Task:** identify abnormal readings and classify their severity.

**Example:**

`High vibration + elevated temperature + high noise`

## 2. Fault Analysis Agent

**Input:** detected symptoms + retrieved RAG context.

**Task:** compare symptoms with known mechanical fault patterns and identify probable faults.

**Example:**

`Bearing degradation and failure`

## 3. Root Cause Agent

**Input:** probable fault + available evidence.

**Task:** explain the underlying physical mechanism.

**Example:**

`Bearing wear → increased friction → vibration and thermal rise`

## 4. Repair Guidance Agent

**Input:** diagnosis + root cause.

**Task:** generate actionable maintenance guidance with an urgency level.

**Example:**

`Inspect bearing → verify lubrication → replace damaged bearing`

## Current MVP Architecture

These are **logical stages**, not four separate LLM requests. The backend asks Granite for a structured response containing `symptoms`, `faults`, `root_cause`, and `repair_guidance`, then the dashboard presents these as four stages.
