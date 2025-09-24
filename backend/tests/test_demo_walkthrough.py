import asyncio
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2]))

from scripts import demo_walkthrough


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        return None


class DummyClient:
    def __init__(self, base_url, timeout):
        self.base_url = base_url
        self.timeout = timeout
        self.calls = []
        self._responses = {
            ("GET", "/health"): DummyResponse({"status": "ok"}),
            ("GET", "/ops/dashboard"): DummyResponse({
                "meta": {
                    "total_surgeries": 3,
                    "total_sedation_cases": 2,
                    "at_risk_centers": 1,
                },
                "tasks": [
                    {"title": "Task A", "owner": "Ops", "due": "2025-01-01"},
                ],
                "inventory_alerts": [
                    {"item": "Kits", "location": "Austin", "status": "low"},
                ],
            }),
            ("POST", "/ops/checklist"): DummyResponse({
                "title": "Checklist",
                "checklist": ["Step 1", "Step 2"],
                "follow_up": ["Call patient"],
            }),
            ("POST", "/rag/query"): DummyResponse({
                "answer": "Do X, Y, Z.",
                "chunks": [
                    {"text": "Context snippet", "score": 0.9},
                ],
            }),
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        key = (method, url)
        if key not in self._responses:
            raise AssertionError(f"Unexpected call: {key}")
        return self._responses[key]


@pytest.mark.asyncio
async def test_run_walkthrough_makes_expected_calls(monkeypatch):
    dummy_client = DummyClient("http://test", 45.0)
    monkeypatch.setattr(demo_walkthrough, "httpx", SimpleNamespace(AsyncClient=lambda base_url, timeout: dummy_client))

    results = await demo_walkthrough.run_walkthrough("http://test")
    assert results["health"]["status"] == "ok"
    assert dummy_client.calls[0][0] == "GET"
    assert dummy_client.calls[-1][1] == "/rag/query"

    summary = demo_walkthrough.render_summary(results)
    assert "Health check" in summary
    assert "Checklist generator" in summary
    assert "RAG answer" in summary
