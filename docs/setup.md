# Setup and Troubleshooting

## Backend

```bash
cd backend
python -m venv venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

## Environment

Copy the root `.env.example` to `backend/.env` and provide valid IBM watsonx.ai credentials.

Important variables include:

- `WATSONX_API_KEY`
- `WATSONX_PROJECT_ID`
- `WATSONX_URL`
- `WATSONX_MODEL_ID`
- `AI_BACKEND`
- `RAG_BACKEND`

## Fallback Mode

If Granite credentials are missing or a Granite request fails, the backend can fall back to its deterministic rule-based engine. The API response identifies the source as `fallback` when this happens.

## Security

Never commit `backend/.env`, API keys, IAM tokens, or other credentials.
