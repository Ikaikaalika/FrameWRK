#!/usr/bin/env python3
"""Guided CLI walkthrough for the AI Ops Runbook Hub demo.

This script calls the running FastAPI backend to showcase:
1. Health check
2. Ops dashboard snapshot
3. Checklist generation
4. RAG question/answer with cited context

Usage:
    python scripts/demo_walkthrough.py --base http://localhost:8000

Run this after `docker compose up -d` (and `scripts/offline_bootstrap.py` for
pre-seeded data). It prints a concise summary you can narrate live.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from textwrap import indent
from typing import Any, Dict, List

import httpx

DEFAULT_BASE = "http://localhost:8000"
OPS_CHECKLIST_PAYLOAD = {
    "patient_name": "Demo Patient",
    "procedure": "Full Arch Immediate Load",
    "location": "Salt Lake City Surgery Center",
    "sedation": "IV Moderate",
    "notes": "Focus on sedation readiness."
}
RAG_DEMO_QUESTION = "How do we prep IV sedation for tomorrow's cases?"


async def _fetch(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> httpx.Response:
    response = await client.request(method, url, **kwargs)
    response.raise_for_status()
    return response


def _format_dashboard(meta: Dict[str, Any], tasks: List[Dict[str, Any]], inventory: List[Dict[str, Any]]) -> str:
    lines = [
        f"Total surgeries today: {meta.get('total_surgeries', 0)}",
        f"Sedation cases: {meta.get('total_sedation_cases', 0)}",
        f"At-risk centers: {meta.get('at_risk_centers', 0)}",
    ]
    if tasks:
        lines.append("Top tasks:")
        for task in tasks[:3]:
            lines.append(f"  • {task['title']} (owner: {task['owner']}, due: {task['due']})")
    if inventory:
        lines.append("Inventory alerts:")
        for alert in inventory[:2]:
            lines.append(f"  • {alert['item']} @ {alert['location']} (status: {alert['status']})")
    return "\n".join(lines)


def _format_checklist(checklist: Dict[str, Any]) -> str:
    lines = [checklist.get("title", "Checklist")]
    lines.append("Checklist items:")
    for idx, item in enumerate(checklist.get("checklist", []), start=1):
        lines.append(f"  {idx}. {item}")
    follow = checklist.get("follow_up", [])
    if follow:
        lines.append("Follow-up:")
        for item in follow:
            lines.append(f"  • {item}")
    return "\n".join(lines)


def _format_rag_answer(answer: str, snippets: List[Dict[str, Any]]) -> str:
    snippet_lines = []
    for idx, chunk in enumerate(snippets[:3], start=1):
        summary = chunk.get("text", "")
        snippet_lines.append(f"Snippet {idx} (score={chunk.get('score', 0):.2f}):\n{indent(summary.strip(), '    ')}")
    context_block = "\n".join(snippet_lines) if snippet_lines else "No snippets returned."
    return f"Answer:\n{indent(answer.strip(), '  ')}\n\nContext:\n{context_block}"


async def run_walkthrough(base_url: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(base_url=base_url, timeout=45.0) as client:
        health = (await _fetch(client, "GET", "/health")).json()
        dashboard = (await _fetch(client, "GET", "/ops/dashboard")).json()
        checklist = (await _fetch(client, "POST", "/ops/checklist", json=OPS_CHECKLIST_PAYLOAD)).json()
        rag_resp = (await _fetch(client, "POST", "/rag/query", json={"question": RAG_DEMO_QUESTION, "k": 3})).json()

    return {
        "health": health,
        "dashboard": dashboard,
        "checklist": checklist,
        "rag": rag_resp,
    }


def render_summary(results: Dict[str, Any]) -> str:
    sections = []
    sections.append("✅ Health check: " + json.dumps(results["health"]))

    dash = results["dashboard"]
    sections.append("📊 Ops dashboard snapshot:\n" + indent(_format_dashboard(dash.get("meta", {}), dash.get("tasks", []), dash.get("inventory_alerts", [])), "  "))

    sections.append("📝 Checklist generator:\n" + indent(_format_checklist(results["checklist"]), "  "))

    rag = results["rag"]
    sections.append("💬 RAG answer:\n" + indent(_format_rag_answer(rag.get("answer", ""), rag.get("chunks", [])), "  "))

    return "\n\n".join(sections)


async def async_main(base_url: str) -> None:
    results = await run_walkthrough(base_url)
    print(render_summary(results))


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an end-to-end API walkthrough for demo prep.")
    parser.add_argument("--base", default=DEFAULT_BASE, help=f"Backend base URL (default: {DEFAULT_BASE})")
    args = parser.parse_args()

    try:
        asyncio.run(async_main(args.base))
    except httpx.HTTPError as exc:
        raise SystemExit(f"Demo walkthrough failed: {exc}") from exc


if __name__ == "__main__":
    main()
