# VitalMech Demo Script

## 1. Select a Scenario

Choose a simulated mechanical scenario from the dashboard.

## 2. Show Sensor Telemetry

Point out RPM, temperature, vibration, pressure, current, and noise.

## 3. Trigger Diagnosis

Run the diagnosis request.

## 4. Explain the Workflow

> The system first detects abnormal symptoms, retrieves relevant mechanical knowledge using RAG, sends the sensor data and retrieved context to IBM Granite, and presents the result through four logical diagnostic stages.

## 5. Explain the Four Stages

- Symptom Detection — what is abnormal?
- Fault Analysis — what fault is most probable?
- Root Cause — why did it happen?
- Repair Guidance — what should maintenance personnel do?

## 6. Show the Dashboard Result

Highlight the fault, severity, retrieved knowledge, root cause, and repair steps.

## 7. Be Precise About the MVP

The current implementation uses one structured Granite inference call representing the four logical stages. Do not describe it as four independent LLM calls.
