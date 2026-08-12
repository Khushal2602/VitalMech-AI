"""
list_models.py -- Discover available foundation models in the Watsonx project.

Makes ONE read-only API call to GET /ml/v1/foundation_model_specs
No inference, no text generation, no token consumption.
API key is never printed.

Run from backend/ directory:
    python list_models.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import httpx
from dotenv import load_dotenv

load_dotenv()

SEP = "-" * 70


def mask(value: str, show: int = 4) -> str:
    if not value or len(value) <= show:
        return "[NOT SET]"
    return value[:show] + "*" * min(len(value) - show, 36)


def fetch_iam_token(api_key: str) -> str:
    """Exchange API key for IAM Bearer token. Key never printed."""
    resp = httpx.post(
        "https://iam.cloud.ibm.com/identity/token",
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"IAM token fetch failed: HTTP {resp.status_code} -- {resp.text[:300]}"
        )
    return resp.json()["access_token"]


def main():
    print(SEP)
    print("VitalMech -- Watsonx Foundation Model Discovery")
    print("Read-only listing request. No inference. API key never printed.")
    print(SEP)

    api_key    = os.getenv("WATSONX_API_KEY", "")
    project_id = os.getenv("WATSONX_PROJECT_ID", "")
    base_url   = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com").rstrip("/")

    print(f"\n[CONFIG]")
    print(f"  WATSONX_URL        : {base_url}")
    print(f"  WATSONX_API_KEY    : {mask(api_key)} (masked)")
    print(f"  WATSONX_PROJECT_ID : {mask(project_id)} (masked)")

    if not api_key:
        print("\n[FAIL] WATSONX_API_KEY is not set.")
        sys.exit(1)

    # Step 1: IAM token
    print("\n[STEP 1] Fetching IAM token (no inference)...")
    try:
        token = fetch_iam_token(api_key)
        print("[OK] IAM token obtained.")
    except Exception as exc:
        print(f"[FAIL] {exc}")
        sys.exit(1)

    # Step 2: List foundation model specs (read-only, no credits consumed)
    print("\n[STEP 2] Calling GET /ml/v1/foundation_model_specs ...")
    url = f"{base_url}/ml/v1/foundation_model_specs?version=2023-05-29&limit=200"
    if project_id:
        url += f"&project_id={project_id}"

    try:
        resp = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=20,
        )
    except Exception as exc:
        print(f"[FAIL] HTTP request error: {exc}")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[FAIL] API returned HTTP {resp.status_code}")
        print(f"       Response: {resp.text[:500]}")
        sys.exit(1)

    print(f"[OK] HTTP {resp.status_code}")

    # Step 3: Parse and filter Granite models
    data = resp.json()
    all_models = data.get("resources", [])
    print(f"\n[INFO] Total foundation models returned: {len(all_models)}")

    granite_models = [
        m for m in all_models
        if "granite" in m.get("model_id", "").lower()
    ]

    print(f"[INFO] IBM Granite models found: {len(granite_models)}")

    if not granite_models:
        print("\n[WARN] No Granite models found in the response.")
        print("       All available model IDs:")
        for m in sorted(all_models, key=lambda x: x.get("model_id", "")):
            print(f"         {m.get('model_id', '[no id]')}")
        sys.exit(0)

    # Step 4: Print Granite models
    print(f"\n{SEP}")
    print("AVAILABLE IBM GRANITE MODELS")
    print(SEP)

    instruct_models = []
    for m in sorted(granite_models, key=lambda x: x.get("model_id", "")):
        mid   = m.get("model_id", "[unknown]")
        label = m.get("label", m.get("name", ""))
        tasks = [t.get("id", "") for t in m.get("tasks", [])]
        langs = m.get("supported_languages", [])
        limit = m.get("token_limits", {})
        max_out = limit.get("max_output_tokens", "?")
        max_in  = limit.get("max_input_tokens",  "?")

        print(f"\n  Model ID  : {mid}")
        if label:
            print(f"  Label     : {label}")
        if tasks:
            print(f"  Tasks     : {', '.join(tasks)}")
        print(f"  Max input : {max_in} tokens")
        print(f"  Max output: {max_out} tokens")

        # Collect instruct-capable models for recommendation
        is_instruct = (
            "instruct" in mid.lower() or
            "text_generation" in tasks or
            "generation" in " ".join(tasks).lower()
        )
        if is_instruct:
            instruct_models.append(mid)

    print(f"\n{SEP}")
    sys.exit(0)


if __name__ == "__main__":
    main()
