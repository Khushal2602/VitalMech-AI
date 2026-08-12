"""
ai/base.py — Abstract base class for all AI client implementations.

Concrete implementations:
  GraniteClient   (granite_client.py) — IBM watsonx.ai single-call
  LangflowClient  (langflow_client.py) — IBM Langflow flow endpoint
"""
from abc import ABC, abstractmethod
from models import SensorData, DiagnosisResult


class AIClient(ABC):
    """
    All AI backends must implement this interface.
    The pipeline calls diagnose() without knowing which backend is active.
    """

    @abstractmethod
    async def diagnose(
        self,
        sensor_data: SensorData,
        context_docs: list[str],
    ) -> DiagnosisResult:
        """
        Given sensor data and RAG-retrieved context documents,
        return a structured DiagnosisResult with four sections:
        symptoms, faults, root_cause, repair_guidance.
        """
        ...
