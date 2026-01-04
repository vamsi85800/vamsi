import json
import re
import time
from typing import Any, Dict, List, Tuple

import httpx
try:
    # pydantic v2 moved BaseSettings to pydantic-settings package
    from pydantic import BaseSettings  # type: ignore
except Exception:
    from pydantic_settings import BaseSettings  # type: ignore


class Settings(BaseSettings):
    # OPENAI_API_KEY is optional for local tests; set via env var or GitHub secret for real runs
    OPENAI_API_KEY: str | None = None
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"
    COST_PROMPT_PER_1K: float = 0.03
    COST_COMPLETION_PER_1K: float = 0.06
    DEFAULT_MAX_TOKENS: int = 512

    class Config:
        # Avoid auto-reading .env files to keep tests simple and avoid encoding issues
        env_file = None


settings = Settings()

SYSTEM_PROMPT = (
    "You are an assistant that must respond with a single JSON object only. "
    'Given a user question, return a JSON object with keys: "answer" (short string), '
    '"confidence" (a float between 0 and 1), and "actions" (an array of short '
    'recommended action strings). Do not include any other text or explanation.'
)


def _extract_json(s: str) -> Any:
    """Try to extract JSON object from a string."""
    s = s.strip()
    # Try direct parse
    try:
        return json.loads(s)
    except Exception:
        pass
    # Try to find a {...} block
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


async def call_llm(question: str, max_tokens: int | None = None) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Call the OpenAI chat/completions endpoint and return parsed JSON and token usage.

    If `max_tokens` is provided it will be passed to the LLM to limit completion length.

    Returns:
      - parsed response (dict with keys answer, confidence, actions)
      - usage dict: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int}
    """
    url = f"{settings.OPENAI_API_BASE}/chat/completions"
    headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}

    max_tokens_value = int(max_tokens) if max_tokens is not None else int(settings.DEFAULT_MAX_TOKENS)

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens_value,
    }

    start = time.perf_counter()
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload, timeout=60.0)
    latency = (time.perf_counter() - start) * 1000.0

    resp.raise_for_status()
    body = resp.json()

    # Try to get usage from provider
    usage = body.get("usage", {})
    prompt_tokens = int(usage.get("prompt_tokens", 0))
    completion_tokens = int(usage.get("completion_tokens", 0))
    total_tokens = int(usage.get("total_tokens", prompt_tokens + completion_tokens))

    # Get the content
    content = ""
    try:
        choices = body.get("choices", [])
        if choices:
            content = choices[0].get("message", {}).get("content", "")
    except Exception:
        content = ""

    parsed = _extract_json(content)
    if parsed is None:
        # Fallback: wrap the raw text
        parsed = {"answer": content.strip(), "confidence": 0.5, "actions": []}

    usage_dict = {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "latency_ms": int(latency),
    }

    return parsed, usage_dict


def estimate_cost(usage: Dict[str, int]) -> float:
    prompt_cost = (usage.get("prompt_tokens", 0) / 1000.0) * settings.COST_PROMPT_PER_1K
    completion_cost = (usage.get("completion_tokens", 0) / 1000.0) * settings.COST_COMPLETION_PER_1K
    return round(prompt_cost + completion_cost, 8)
