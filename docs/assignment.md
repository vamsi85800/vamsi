# Assignment: Multi-Task Text Utility

This service demonstrates a small FastAPI application that:

- Accepts a question from a support agent or UI
- Calls an OpenAI LLM to produce a concise JSON response with keys:
  - `answer`: short text
  - `confidence`: 0-1 float
  - `actions`: array of short recommended actions
- Returns per-request metrics to monitor usage:
  - latency (ms), tokens, estimated USD cost

See `README.md` for setup and usage examples.
