import pytest

from app.services.automation_service import AutomationService


class StubRAG:
    def __init__(self, chunks):
        self.chunks = chunks

    async def query(self, question: str, k: int = 5):
        return "answer", [type("Hit", (), {"payload": {"text": chunk}}) for chunk in self.chunks]


class StubLLM:
    def __init__(self, suggestion_payload=None, implementation_payload=None):
        self.suggestion_payload = suggestion_payload or {
            "suggestions": [
                {
                    "title": "Auto-generate sedation readiness tasks",
                    "problem": "Manual tracking of kit preparation leads to misses.",
                    "automation": "Use ingestion events to auto-create task lists per location.",
                    "impact": "Reduces missed prep steps by 80%.",
                    "confidence": "high",
                }
            ]
        }
        self.implementation_payload = implementation_payload or {
            "title": "Sedation readiness automation",
            "summary": "Automate creation of sedation prep tasks per case.",
            "plan_steps": [
                "Add FastAPI endpoint emitting task payloads.",
                "Schedule worker to sync with Qdrant metadata.",
            ],
            "integrations": ["FastAPI", "Postgres"],
            "monitoring": ["Task queue error rate"],
            "rollout_notes": "Pilot at two clinics first.",
        }

    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512):
        if "automation idea".lower() in prompt.lower():
            return self.implementation_payload
        return self.suggestion_payload


@pytest.mark.asyncio
async def test_suggest_returns_normalized_items(monkeypatch):
    service = AutomationService(rag=StubRAG(["Doc A", "Doc B"]), llm=StubLLM())
    suggestions = await service.suggest("sedation readiness", count=2)
    assert suggestions[0]["title"].startswith("Auto-generate")
    assert suggestions[0]["confidence"] == "high"


@pytest.mark.asyncio
async def test_implement_persists_plan(monkeypatch):
    # Monkeypatch database connection
    records = {}

    class FakeCursor:
        def execute(self, query, params):
            records["query"] = query
            records["params"] = params
            self.result = (42, "pending", None)

        def fetchone(self):
            return self.result

        def close(self):
            records["closed_cursor"] = True

    class FakeConn:
        def cursor(self):
            return FakeCursor()

        def commit(self):
            records["committed"] = True

        def close(self):
            records["closed_conn"] = True

    monkeypatch.setattr("app.services.automation_service.get_conn", lambda: FakeConn())

    service = AutomationService(rag=StubRAG([]), llm=StubLLM())
    plan = await service.implement({"title": "Auto", "automation": "Do X"})
    assert plan["id"] == 42
    assert records["committed"] is True
