# genai_project

A basic Python project scaffold for GenAI work.

## Multi-Task Text Utility

This project contains a small FastAPI service which accepts a customer-support question, calls an OpenAI LLM to produce a concise JSON answer with a confidence and recommended actions, and returns per-request metrics (latency, token usage, and estimated USD cost).

## Setup

1. Create a virtual environment:

```
python -m venv .venv
```

2. Activate it:

- Windows: `\.venv\Scripts\Activate.ps1` (PowerShell)
- Unix: `source .venv/bin/activate`

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Copy `.env.example` to `.env` and set your `OPENAI_API_KEY` and optional values:

```
cp .env.example .env
# then edit .env and set OPENAI_API_KEY
```

## Running the API

Start the server with uvicorn:

```
uvicorn genai_project.api:app --reload --port 8000
```

## Usage examples

POST /query

Request JSON:

```json
{ "question": "How do I reset my password?" }
```

Curl example:

```bash
curl -X POST http://localhost:8000/query -H "Content-Type: application/json" -d '{"question":"How do I reset my password?"}'
```

Response JSON (example):

```json
{
  "response": {
    "answer": "You can reset your password from Settings → Security.",
    "confidence": 0.9,
    "actions": ["Send reset link", "Verify identity"]
  },
  "metrics": {
    "latency_ms": 120,
    "prompt_tokens": 40,
    "completion_tokens": 60,
    "total_tokens": 100,
    "estimated_cost_usd": 0.006,
    "model": "gpt-4o-mini"
  }
}
```

## Tests

Run tests:

```
pytest -q
```

## Env / config

See `.env.example` for required keys (notably `OPENAI_API_KEY`).

**CI note:** If you add `OPENAI_API_KEY` as a repository Secret in GitHub (Settings → Secrets), the CI workflow will run a real smoke test that calls the OpenAI API — this will incur API usage and costs. The smoke test sends a very short prompt and sets `max_tokens=8` to limit cost. If the secret is not set, the CI will skip the real smoke test.

---

## Windows helper scripts (run the server without changing execution policy)

If you're on Windows and PowerShell script execution is restricted, use the included helper scripts which avoid requiring PowerShell activation:

- PowerShell (recommended):

  1. Open PowerShell in the project root.
  2. Run (allowing script for this process only):
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; .\scripts\run.ps1
     ```
  3. This script will create `.venv` if missing, install dependencies, and start the server.

- cmd.exe (no PowerShell change required):

  1. Open Command Prompt in the project root.
  2. Run:
     ```cmd
     .\scripts\run.bat
     ```

Both scripts use the venv Python directly and will not permanently change system policies. Use `Ctrl+C` to stop the server when running in the foreground.

