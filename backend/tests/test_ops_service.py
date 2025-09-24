import pytest

from app.services.ops_service import OpsService


def build_service():
    return OpsService(data={"locations": [], "schedule": [], "tasks": [], "inventory_alerts": [], "followups": [], "sedation_trend": []})


def test_split_checklist_extracts_follow_up():
    svc = build_service()
    raw = """1. Confirm imaging is loaded\n- Verify sedation kit in operatory\nFollow-up:\n- Call patient next morning\n• Update CRM"""
    checklist, follow_up = svc._split_checklist(raw)

    assert checklist == ["Confirm imaging is loaded", "Verify sedation kit in operatory"]
    assert follow_up == ["Call patient next morning", "Update CRM"]


@pytest.mark.asyncio
async def test_generate_checklist_uses_llm_response(monkeypatch):
    svc = build_service()
    recorded = {}

    async def fake_complete_text(prompt, max_tokens):
        return "1. Stage implant kits.\n2. Review sedation plan.\nFollow-up:\n- Schedule 48-hour call."

    def fake_record(payload, follow_up):
        recorded["payload"] = payload
        recorded["follow_up"] = follow_up

    monkeypatch.setattr(svc, "_record_generated_tasks", fake_record)

    class FakeLLM:
        async def complete_text(self, prompt, max_tokens=320):
            return await fake_complete_text(prompt, max_tokens)

    payload = {
        "patient_name": "Jane Doe",
        "procedure": "Full Arch",
        "location": "Salt Lake City",
        "sedation": "IV Moderate",
        "notes": "Check blood pressure"
    }

    result = await svc.generate_checklist(payload, FakeLLM())

    assert result["title"].startswith("Full Arch prep — Jane Doe")
    assert result["checklist"] == ["Stage implant kits.", "Review sedation plan."]
    assert result["follow_up"] == ["Schedule 48-hour call."]
    assert recorded["payload"]["patient_name"] == "Jane Doe"
    assert recorded["follow_up"] == ["Schedule 48-hour call."]


@pytest.mark.asyncio
async def test_generate_checklist_falls_back_on_error(monkeypatch):
    svc = build_service()

    async def boom(prompt, max_tokens):
        raise RuntimeError("llm down")

    called = {}

    def fake_fallback(payload):
        called["payload"] = payload
        return "1. Prep operatory.\nFollow-up:\n- Confirm meds ready."

    def fake_record(payload, follow_up):
        called["follow_up"] = follow_up

    monkeypatch.setattr(svc, "_fallback_checklist", fake_fallback)
    monkeypatch.setattr(svc, "_record_generated_tasks", fake_record)

    class FailingLLM:
        async def complete_text(self, prompt, max_tokens=320):
            return await boom(prompt, max_tokens)

    payload = {
        "patient_name": "Alex Smith",
        "procedure": "Implant",
        "location": "Phoenix",
        "sedation": "Oral",
    }

    result = await svc.generate_checklist(payload, FailingLLM())

    assert called["payload"]["patient_name"] == "Alex Smith"
    assert result["checklist"] == ["Prep operatory."]
    assert result["follow_up"] == ["Confirm meds ready."]
    assert called["follow_up"] == ["Confirm meds ready."]
