from datetime import datetime
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.main import app as fastapi_app
from app.deps import get_ops_service, get_llm_provider, get_rag_pipeline, get_automation_service


class FakeCursor:
    def __init__(self, db):
        self.db = db

    def execute(self, query, params=None):
        self.db["queries"].append((query, params))

    def fetchall(self):
        return self.db.get("rows", [])

    def close(self):
        self.db["closed_cursors"] += 1


class FakeConn:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return FakeCursor(self.db)

    def commit(self):
        self.db["commits"] += 1

    def close(self):
        self.db["closed_conns"] += 1


class FakeOpsService:
    def __init__(self):
        self.checklist_calls = []

    def dashboard(self):
        return {
            "meta": {
                "total_surgeries": 2,
                "total_sedation_cases": 1,
                "at_risk_centers": 0,
                "open_tasks": 1,
            },
            "locations": [],
            "schedule": [],
            "tasks": [],
            "inventory_alerts": [],
            "followups": [],
            "sedation_trend": [],
        }

    async def generate_checklist(self, payload, llm):
        self.checklist_calls.append(payload)
        return {"title": "Checklist", "checklist": ["Step"], "follow_up": ["Call"]}

    def generated_tasks(self):
        return [
            {
                "id": 1,
                "patient_name": "Jane Doe",
                "task": "Call patient",
                "owner": "Ops",
                "due_at": "2024-01-01T00:00:00",
                "status": "open",
                "created_at": "2023-12-31T00:00:00",
            }
        ]


class FakeLLM:
    async def complete_text(self, prompt, max_tokens=256):
        return "ok"

    async def complete_json(self, prompt, schema, max_tokens=512):
        return {"label": "ok", "scores": {"ok": 1.0}}


class FakePipeline:
    def __init__(self):
        self.ingest_calls = []
        self.query_calls = []
        self.ensure_called = 0

    async def ensure_collection(self):
        self.ensure_called += 1

    async def ingest_texts(self, texts):
        self.ingest_calls.append(list(texts))
        return len(texts)

    async def query(self, question, k=5):
        self.query_calls.append({"question": question, "k": k})
        results = [SimpleNamespace(payload={"text": "Context chunk"}, score=0.9)]
        return "answer", results


class FakeAutomationService:
    def __init__(self):
        self.approved = []

    async def suggest(self, focus: str, count: int = 3):
        return [
            {
                "title": "Automate sedation prep",
                "problem": "Manual checklist creation",
                "automation": "Use FastAPI job to create tasks",
                "impact": "Reduces prep time",
                "confidence": "high",
            }
        ][:count]

    async def implement(self, suggestion):
        self.approved.append(suggestion)
        return {
            "id": 7,
            "title": suggestion.get("title", "Automation"),
            "status": "pending",
            "implementation_plan": {"plan_steps": ["Step"]},
            "created_at": None,
        }


@pytest.fixture
def client(monkeypatch):
    fake_db = {"queries": [], "rows": [], "commits": 0, "closed_conns": 0, "closed_cursors": 0}

    def fake_get_conn():
        return FakeConn(fake_db)

    monkeypatch.setattr("app.main.get_conn", fake_get_conn)
    monkeypatch.setattr("app.routers.admin.get_conn", fake_get_conn)

    ops_service = FakeOpsService()
    pipeline = FakePipeline()
    llm = FakeLLM()
    automation_service = FakeAutomationService()

    fastapi_app.router.on_startup.clear()
    fastapi_app.dependency_overrides[get_ops_service] = lambda: ops_service
    fastapi_app.dependency_overrides[get_llm_provider] = lambda: llm
    fastapi_app.dependency_overrides[get_rag_pipeline] = lambda: pipeline
    fastapi_app.dependency_overrides[get_automation_service] = lambda: automation_service

    with TestClient(fastapi_app) as test_client:
        yield test_client, ops_service, pipeline, fake_db, automation_service

    fastapi_app.dependency_overrides.clear()


def test_ops_dashboard_endpoint(client):
    test_client, *_ = client
    resp = test_client.get("/ops/dashboard")
    assert resp.status_code == 200
    body = resp.json()
    assert body["meta"]["total_surgeries"] == 2


def test_ops_checklist_endpoint(client):
    test_client, ops_service, _, _, _ = client
    resp = test_client.post(
        "/ops/checklist",
        json={
            "patient_name": "Jane Doe",
            "procedure": "Full Arch",
            "location": "Salt Lake City",
            "sedation": "IV Moderate",
            "notes": "Check vitals",
        },
    )
    assert resp.status_code == 200
    assert ops_service.checklist_calls[0]["patient_name"] == "Jane Doe"
    assert resp.json()["checklist"] == ["Step"]


def test_op_generated_tasks_endpoint(client):
    test_client, *_ = client
    resp = test_client.get("/ops/generated-tasks")
    assert resp.status_code == 200
    assert resp.json()[0]["task"] == "Call patient"


def test_rag_ingest_and_query(client):
    test_client, _, pipeline, _, _ = client
    ingest = test_client.post("/rag/ingest", json={"texts": ["hello", "world"]})
    assert ingest.status_code == 200
    assert pipeline.ensure_called == 1
    assert pipeline.ingest_calls == [["hello", "world"]]

    query = test_client.post("/rag/query", json={"question": "hi", "k": 1})
    assert query.status_code == 200
    assert pipeline.query_calls[0]["question"] == "hi"
    assert query.json()["chunks"][0]["text"] == "Context chunk"


def test_admin_logs_endpoint(client):
    test_client, _, _, fake_db, _ = client
    fake_db["rows"] = [
        (1, "http://test/route", datetime(2024, 1, 1, 12, 0, 0))
    ]
    resp = test_client.get("/admin/logs")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["items"][0]["route"] == "http://test/route"
    assert payload["limit"] == 50


def test_automation_endpoints(client):
    test_client, *_ = client
    suggest = test_client.post(
        "/ops/automation/suggest",
        json={"focus": "sedation readiness", "count": 1},
    )
    assert suggest.status_code == 200
    body = suggest.json()
    assert body["suggestions"][0]["title"] == "Automate sedation prep"

    approve = test_client.post(
        "/ops/automation/implement",
        json={
            "title": "Automate sedation prep",
            "problem": "Manual",
            "automation": "Use FastAPI job",
            "impact": "Less work",
        },
    )
    assert approve.status_code == 200
    assert approve.json()["id"] == 7
