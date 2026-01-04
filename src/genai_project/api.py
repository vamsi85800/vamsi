from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List
import time

from .llm import call_llm, estimate_cost, settings

app = FastAPI(title="Multi-Task Text Utility", version="0.1.0")


class QueryRequest(BaseModel):
    question: str = Field(..., example="How can I reset my password?")
    max_tokens: int = Field(None, example=8)


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    actions: List[str]


class QueryMetrics(BaseModel):
    latency_ms: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_usd: float
    model: str


class FullResponse(BaseModel):
    response: QueryResponse
    metrics: QueryMetrics


@app.post("/query", response_model=FullResponse)
async def query(req: QueryRequest):
    start = time.perf_counter()
    try:
        parsed, usage = await call_llm(req.question, max_tokens=req.max_tokens)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


    latency_ms = usage.get("latency_ms", int((time.perf_counter() - start) * 1000.0))
    cost = estimate_cost(usage)

    # Normalize parsed
    answer = str(parsed.get("answer", "")).strip()
    confidence = float(parsed.get("confidence", 0.5))
    actions = parsed.get("actions", []) if isinstance(parsed.get("actions", []), list) else []

    return {
        "response": {"answer": answer, "confidence": confidence, "actions": actions},
        "metrics": {
            "latency_ms": latency_ms,
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
            "estimated_cost_usd": cost,
            "model": settings.OPENAI_MODEL,
        },
    }
