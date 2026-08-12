"""
ai/langflow_client.py — IBM Langflow flow endpoint client (stub).

When AI_BACKEND=langflow, this client is activated instead of GraniteClient.
Set LANGFLOW_FLOW_URL in .env to point at your Langflow flow's API endpoint.

Implemented when Langflow access is confirmed in the hackathon environment.
"""
import os
from models import SensorData, DiagnosisResult
from ai.base import AIClient


class LangflowClient(AIClient):
    """
    Delegates diagnosis to an IBM Langflow flow.
    The flow must accept sensor data and return a DiagnosisResult-shaped JSON.
    """

    def __init__(self):
        self.flow_url = os.getenv("LANGFLOW_FLOW_URL", "")

    async def diagnose(
        self,
        sensor_data: SensorData,
        context_docs: list[str],
    ) -> DiagnosisResult:
        # TODO: POST sensor_data to self.flow_url, map response to DiagnosisResult
        raise NotImplementedError("LangflowClient not yet implemented")
