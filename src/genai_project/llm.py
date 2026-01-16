import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .prompts import SYSTEM_PROMPT


class LLMConfig:
    """Configuration for LLM client."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        cost_prompt_per_1k: float = 0.03,
        cost_completion_per_1k: float = 0.06,
        default_max_tokens: int = 512,
    ):
        # Get API key from parameter or environment variable
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base
        self.model = model
        self.cost_prompt_per_1k = cost_prompt_per_1k
        self.cost_completion_per_1k = cost_completion_per_1k
        self.default_max_tokens = default_max_tokens


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


async def call_llm(
    question: str,
    config: Optional[LLMConfig] = None,
    system_prompt: str = SYSTEM_PROMPT,
    max_tokens: Optional[int] = None,
) -> Tuple[Dict[str, Any], Dict[str, int]]:
    """Call the OpenAI chat/completions endpoint and return parsed JSON and token usage.

    Args:
        question: The user question to ask the LLM.
        config: LLMConfig instance. If None, creates one from environment variables.
        system_prompt: System prompt to use. Defaults to SYSTEM_PROMPT.
        max_tokens: Optional max tokens limit for completion.

    Returns:
      - parsed response (dict with keys answer, confidence, actions)
      - usage dict: {'prompt_tokens': int, 'completion_tokens': int, 'total_tokens': int, 'latency_ms': int}
    """
    if config is None:
        config = LLMConfig()
    
    url = f"{config.api_base}/chat/completions"
    headers = {"Authorization": f"Bearer {config.api_key}"}

    max_tokens_value = int(max_tokens) if max_tokens is not None else int(config.default_max_tokens)

    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
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


def estimate_cost(usage: Dict[str, int], config: Optional[LLMConfig] = None) -> float:
    """Estimate the cost of the LLM call based on token usage.
    
    Args:
        usage: Dictionary with keys 'prompt_tokens' and 'completion_tokens'.
        config: LLMConfig instance. If None, creates one from environment variables.
    
    Returns:
        Estimated cost in USD.
    """
    if config is None:
        config = LLMConfig()
    
    prompt_cost = (usage.get("prompt_tokens", 0) / 1000.0) * config.cost_prompt_per_1k
    completion_cost = (usage.get("completion_tokens", 0) / 1000.0) * config.cost_completion_per_1k
    return round(prompt_cost + completion_cost, 8)
