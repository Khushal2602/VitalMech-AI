"""
test_granite.py -- Phase 3A: IBM Granite connectivity test.

Sends ONE small inference request to IBM Granite via watsonx.ai.
Verifies:
  - IAM token can be obtained
  - watsonx.ai inference endpoint responds
  - Response can be parsed as the expected JSON structure

SECURITY RULES enforced in this script:
  - API key is NEVER printed, logged, or included in any output.
  - Only the model ID and endpoint URL are reported.
  - The script exits after exactly ONE inference call.

Run from the backend/ directory:
    python test_granite.py
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

SEP = "-" * 70

# ------------------------------------------------------------------
# Minimal single-shot prompt -- keeps token usage low
# ------------------------------------------------------------------
SYSTEM = (
    "You are a mechanical fault diagnosis AI. "
    "Respond with ONLY a valid JSON object. No explanation, no markdown."
)

USER = """Machine: Induction Motor
Temperature: 78 C
Vibration: 14.3 mm/s
RPM: 1740
Noise: 89 dB
Symptom: High vibration and metallic noise

Return ONLY this JSON structure (no other text):
{
  "fault": "<most likely fault name>",
  "confidence": <0.0 to 1.0>,
  "reason": "<one sentence explanation>"
}"""


def mask(value: str, show: int = 4) -> str:
    """Return a masked version of a sensitive string for safe display."""
    if not value or len(value) <= show:
        return "[NOT SET]"
    return value[:show] + "*" * (len(value) - show)


def main():
    print(SEP)
    print("VitalMech -- Phase 3A: IBM Granite Connectivity Test")
    print("ONE inference call only. API key is never printed.")
    print(SEP)

    # ------------------------------------------------------------------
    # 1. Check environment variables are set
    # ------------------------------------------------------------------
    api_key    = os.getenv("WATSONX_API_KEY", "")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")
    base_url   = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")
    model_id   = os.getenv("WATSONX_MODEL_ID", "")

    print("\n[CONFIG]")
    print(f"  WATSONX_URL      : {base_url}")
    print(f"  WATSONX_MODEL_ID : {model_id if model_id else '[NOT SET]'}")
    print(f"  WATSONX_API_KEY  : {mask(api_key)} (masked)")
    print(f"  WATSONX_PROJECT_ID: {mask(project_id)} (masked)")

    missing = []
    if not api_key:
        missing.append("WATSONX_API_KEY")
    if not project_id:
        missing.append("WATSONX_PROJECT_ID")
    if not model_id:
        missing.append("WATSONX_MODEL_ID")

    if missing:
        print(f"\n[FAIL] Missing required environment variables: {missing}")
        print("       Set them in backend/.env and re-run.")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 2. Import GraniteClient (validates no import errors first)
    # ------------------------------------------------------------------
    try:
        from ai.granite_client import GraniteClient
    except Exception as exc:
        print(f"\n[FAIL] Could not import GraniteClient: {exc}")
        sys.exit(1)

    client = GraniteClient()
    print(f"\n[OK] GraniteClient instantiated. Model: {client.model_id}")

    # ------------------------------------------------------------------
    # 3. Fetch IAM token (no inference yet)
    # ------------------------------------------------------------------
    print("\n[STEP 1] Fetching IAM Bearer token...")
    try:
        client._fetch_iam_token()
        print("[OK] IAM token obtained successfully (token not printed).")
    except Exception as exc:
        print(f"[FAIL] IAM token fetch failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 4. Single inference call
    # ------------------------------------------------------------------
    print("\n[STEP 2] Sending ONE inference request to watsonx.ai...")
    print(f"         Endpoint: {client._inference_url()}")
    print(f"         Model:    {client.model_id}")
    print(f"         Max new tokens: 150")

    raw_text = None
    try:
        raw_text = client.call_sync(SYSTEM, USER, max_tokens=150)
        print("[OK] Inference call succeeded.")
    except Exception as exc:
        print(f"[FAIL] Inference call failed: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 5. Report raw generated text (safe -- no credentials in output)
    # ------------------------------------------------------------------
    print("\n[STEP 3] Raw generated text from Granite:")
    print("         " + raw_text.replace("\n", "\n         "))

    # ------------------------------------------------------------------
    # 6. Parse JSON response
    # ------------------------------------------------------------------
    print("\n[STEP 4] Parsing JSON response...")
    from ai.granite_client import GraniteClient as _GC  # already imported, reuse
    import re

    parsed = None
    parse_error = None

    # Try to extract JSON from the raw text
    try:
        fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if fenced:
            json_str = fenced.group(1)
        else:
            brace = re.search(r"\{.*\}", raw_text, re.DOTALL)
            json_str = brace.group(0) if brace else raw_text
        parsed = json.loads(json_str)
    except Exception as exc:
        parse_error = str(exc)

    if parsed is None:
        print(f"[WARN] Could not parse JSON from response: {parse_error}")
        print("       Raw text was printed above -- check model output format.")
    else:
        print("[OK] JSON parsed successfully.")
        print("\n[RESULT] Parsed response:")
        print(f"  fault      : {parsed.get('fault', '[missing]')}")
        print(f"  confidence : {parsed.get('confidence', '[missing]')}")
        print(f"  reason     : {parsed.get('reason', '[missing]')}")

        # Validate expected keys
        expected_keys = {"fault", "confidence", "reason"}
        present_keys  = set(parsed.keys())
        missing_keys  = expected_keys - present_keys
        extra_keys    = present_keys - expected_keys

        if missing_keys:
            print(f"\n  [WARN] Missing expected keys: {missing_keys}")
        if extra_keys:
            print(f"  [INFO] Extra keys returned (acceptable): {extra_keys}")
        if not missing_keys:
            print("\n  [OK] All expected keys present in response.")

    # ------------------------------------------------------------------
    # 7. Summary
    # ------------------------------------------------------------------
    print(f"\n{SEP}")
    print("CONNECTIVITY TEST SUMMARY")
    print(f"  Model used      : {client.model_id}")
    print(f"  IAM token       : OK")
    print(f"  Inference call  : OK (1 call made, 0 retries)")
    print(f"  JSON parsed     : {'OK' if parsed else 'WARN -- see above'}")
    print(f"  API key exposed : NO")
    print(f"  Additional calls: NONE")
    print(SEP)

    sys.exit(0 if parsed and not ({"fault","confidence","reason"} - set(parsed.keys())) else 1)


if __name__ == "__main__":
    main()
