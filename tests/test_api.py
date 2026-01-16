import pytest
from fastapi.testclient import TestClient

from genai_project.api import app
import genai_project.llm as llm

client = TestClient(app)


def test_query_endpoint(monkeypatch):
    async def fake_call_llm(question: str, config=None, system_prompt=None, max_tokens=None):
        # Accept optional parameters
        parsed = {"answer": "Reset your password via Settings > Security.", "confidence": 0.92, "actions": ["Send reset link", "Verify identity"]}
        usage = {"prompt_tokens": 10, "completion_tokens": 50, "total_tokens": 60, "latency_ms": 123}
        return parsed, usage

    # Patch the reference used by the API module (it imported call_llm at import-time)
    monkeypatch.setattr("genai_project.api.call_llm", fake_call_llm)

    resp = client.post("/query", json={"question": "How to reset password?"})
    assert resp.status_code == 200
    data = resp.json()
    assert "response" in data
    assert data["response"]["answer"].startswith("Reset your password")
    assert data["response"]["confidence"] == 0.92
    assert data["metrics"]["prompt_tokens"] == 10
    assert data["metrics"]["total_tokens"] == 60


def test_max_tokens_forwarded(monkeypatch):
    async def fake_call_llm(question: str, config=None, system_prompt=None, max_tokens=None):
        # Ensure the max_tokens value is forwarded from the API layer
        assert max_tokens == 8
        parsed = {"answer": "ok", "confidence": 0.5, "actions": []}
        usage = {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2, "latency_ms": 1}
        return parsed, usage

    # Patch the reference used by the API module (it imported call_llm at import-time)
    monkeypatch.setattr("genai_project.api.call_llm", fake_call_llm)

    resp = client.post("/query", json={"question": "short", "max_tokens": 8})
    assert resp.status_code == 200
    data = resp.json()
    assert data["response"]["answer"] == "ok"


def test_estimate_cost():
    config = llm.LLMConfig()
    usage = {"prompt_tokens": 1000, "completion_tokens": 500}
    cost = llm.estimate_cost(usage, config=config)
    assert cost == pytest.approx((1000/1000)*0.03 + (500/1000)*0.06, rel=1e-6)
