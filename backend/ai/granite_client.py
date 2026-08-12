"""
ai/granite_client.py -- IBM Granite via watsonx.ai (Phase 3).

Single-call implementation:
  1. Exchange API key for an IAM Bearer token (cached until expiry).
  2. POST a structured diagnostic prompt to the watsonx.ai text generation endpoint.
  3. Parse the JSON response into a DiagnosisResult.

Credentials are read exclusively from environment variables -- never hardcoded.
"""
import json
import os
import re
import time

import httpx
from dotenv import load_dotenv

from ai.base import AIClient
from ai.prompts import SYSTEM_PROMPT, build_user_prompt
from models import DiagnosisResult, FaultItem, RepairGuidance, RootCause, SensorData, SymptomItem

load_dotenv()

# IBM IAM token endpoint -- never changes
_IAM_URL = "https://iam.cloud.ibm.com/identity/token"


class GraniteClient(AIClient):
    """
    IBM Granite client -- one structured call per diagnosis request.

    Token management:
      - IAM tokens are valid for ~1 hour (3600 s).
      - We refresh proactively when fewer than 5 minutes remain.
      - The token itself is never logged or returned to callers.
    """

    def __init__(self):
        self._api_key: str = os.getenv("WATSONX_API_KEY", "")
        self._project_id: str = os.getenv("WATSONX_PROJECT_ID", "")
        self._base_url: str = os.getenv(
            "WATSONX_URL", "https://us-south.ml.cloud.ibm.com"
        ).rstrip("/")
        self.model_id: str = os.getenv("WATSONX_MODEL_ID", "")

        # IAM token cache
        self._token: str | None = None
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Internal: IAM token management
    # ------------------------------------------------------------------

    def _token_is_valid(self) -> bool:
        """Return True if the cached token has >5 minutes remaining."""
        return self._token is not None and time.time() < (self._token_expiry - 300)

    def _fetch_iam_token(self) -> str:
        """
        Exchange the API key for a short-lived IAM Bearer token.
        Raises RuntimeError on failure -- error message never includes the key.
        """
        response = httpx.post(
            _IAM_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": self._api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"IAM token fetch failed: HTTP {response.status_code} -- "
                f"{response.text[:200]}"
            )
        data = response.json()
        self._token = data["access_token"]
        # IBM IAM tokens are valid for 'expires_in' seconds from issue time
        self._token_expiry = time.time() + int(data.get("expires_in", 3600))
        return self._token

    def _get_token(self) -> str:
        """Return a valid IAM token, refreshing if necessary."""
        if not self._token_is_valid():
            self._fetch_iam_token()
        return self._token  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal: watsonx.ai inference
    # ------------------------------------------------------------------

    def _inference_url(self) -> str:
        return f"{self._base_url}/ml/v1/text/generation?version=2023-05-29"

    def _call(self, system_prompt: str, user_prompt: str, max_tokens: int = 600) -> str:
        """
        POST to the watsonx.ai text generation endpoint.
        Returns the generated text string.
        Raises RuntimeError on non-200 response.
        """
        token = self._get_token()

        # Granite instruct format: combine system + user into a single input string
        combined_input = (
            f"<|system|>\n{system_prompt}\n"
            f"<|user|>\n{user_prompt}\n"
            f"<|assistant|>\n"
        )

        payload = {
            "model_id": self.model_id,
            "input": combined_input,
            "parameters": {
                "decoding_method": "greedy",
                "max_new_tokens": max_tokens,
                "temperature": 0.3,
                "repetition_penalty": 1.1,
                "stop_sequences": ["<|user|>", "<|system|>"],
            },
            "project_id": self._project_id,
        }

        response = httpx.post(
            self._inference_url(),
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=60,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"watsonx.ai inference failed: HTTP {response.status_code} -- "
                f"{response.text[:400]}"
            )

        data = response.json()
        try:
            return data["results"][0]["generated_text"].strip()
        except (KeyError, IndexError) as exc:
            raise RuntimeError(
                f"Unexpected watsonx.ai response shape: {str(data)[:300]}"
            ) from exc

    # ------------------------------------------------------------------
    # Internal: response parsing
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        Extract and parse a JSON object from the model's raw output.
        Handles cases where the model wraps JSON in markdown code fences.
        """
        # Strip markdown code fences if present
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if fenced:
            text = fenced.group(1)

        # Find the first {...} block in the output
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            text = brace_match.group(0)

        return json.loads(text)

    @staticmethod
    def _parse_diagnosis(raw: dict) -> DiagnosisResult:
        """
        Map the raw JSON dict from Granite into a DiagnosisResult Pydantic model.
        Handles both the full 4-key schema and partial/malformed responses gracefully.
        """
        symptoms = [
            SymptomItem(
                name=s.get("name", "Unknown"),
                severity=s.get("severity", "medium"),
                description=s.get("description", ""),
            )
            for s in raw.get("symptoms", [])
            if isinstance(s, dict)
        ]

        faults = [
            FaultItem(
                name=f.get("name", "Unknown"),
                confidence=float(f.get("confidence", 0.5)),
                description=f.get("description", ""),
            )
            for f in raw.get("faults", [])
            if isinstance(f, dict)
        ]

        rc_raw = raw.get("root_cause")
        root_cause = None
        if isinstance(rc_raw, dict):
            root_cause = RootCause(
                summary=rc_raw.get("summary", ""),
                cause_chain=rc_raw.get("cause_chain", []),
            )

        rg_raw = raw.get("repair_guidance")
        repair_guidance = None
        if isinstance(rg_raw, dict):
            repair_guidance = RepairGuidance(
                urgency=rg_raw.get("urgency", "soon"),
                steps=rg_raw.get("steps", []),
            )

        return DiagnosisResult(
            symptoms=symptoms,
            faults=faults,
            root_cause=root_cause,
            repair_guidance=repair_guidance,
        )

    # ------------------------------------------------------------------
    # Public interface (AIClient)
    # ------------------------------------------------------------------

    async def diagnose(
        self,
        sensor_data: SensorData,
        context_docs: list[str],
    ) -> DiagnosisResult:
        """
        Run a single Granite inference call and return a structured DiagnosisResult.
        Raises RuntimeError if the API call or response parsing fails.
        """
        if not self._api_key:
            raise RuntimeError("WATSONX_API_KEY is not set in environment.")
        if not self._project_id:
            raise RuntimeError("WATSONX_PROJECT_ID is not set in environment.")
        if not self.model_id:
            raise RuntimeError("WATSONX_MODEL_ID is not set in environment.")

        user_prompt = build_user_prompt(sensor_data, context_docs)
        raw_text = self._call(SYSTEM_PROMPT, user_prompt, max_tokens=800)
        raw_json = self._extract_json(raw_text)
        return self._parse_diagnosis(raw_json)

    # ------------------------------------------------------------------
    # Synchronous helper for connectivity testing only
    # ------------------------------------------------------------------

    def call_sync(self, system_prompt: str, user_prompt: str, max_tokens: int = 300) -> str:
        """
        Synchronous wrapper around _call() -- used by test_granite.py only.
        The full diagnosis pipeline uses the async diagnose() method instead.
        """
        if not self._api_key:
            raise RuntimeError("WATSONX_API_KEY is not set in environment.")
        if not self._project_id:
            raise RuntimeError("WATSONX_PROJECT_ID is not set in environment.")
        if not self.model_id:
            raise RuntimeError("WATSONX_MODEL_ID is not set in environment.")
        return self._call(system_prompt, user_prompt, max_tokens)
