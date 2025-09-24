"""Bootstrap the offline demo experience.

Run inside the backend container (or with PYTHONPATH=backend) to:
1. Ensure the Qdrant collection exists and ingest the bundled seed/mock docs.
2. Pre-populate Postgres with demo API logs and generated tasks so the UI is lively.

Usage:
  docker compose exec backend bash -lc "python scripts/offline_bootstrap.py"
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

# When executed outside the container make sure backend/ is on PYTHONPATH.
try:  # pragma: no cover - only used in ad-hoc CLI runs.
    from app.deps import get_rag_pipeline
    from app.storage.db import get_conn
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Unable to import backend modules. Run with PYTHONPATH=backend or inside the backend container."
    ) from exc

SUPPORTED_EXTS = {".md", ".txt", ".json"}
SCRIPT_ROOT = Path(__file__).resolve().parent
DOC_DIRS = [SCRIPT_ROOT / "seed_docs", SCRIPT_ROOT / "mock_docs"]

DEMO_GENERATED_TASKS = [
    {
        "patient_name": "Demo Patient — Sedation Review",
        "task": "[Demo] Confirm IV sedation kit restocked before 7am",
        "owner": "Phoenix Ops",
        "due_at": "2025-09-18T06:45:00",
    },
    {
        "patient_name": "Demo Patient — Inventory",
        "task": "[Demo] Stage titanium bars and backup abutments",
        "owner": "Austin Ops",
        "due_at": "2025-09-18T07:15:00",
    },
    {
        "patient_name": "Demo Patient — Follow-up",
        "task": "[Demo] Schedule 48-hour wellness call",
        "owner": "Salt Lake City Concierge",
        "due_at": "2025-09-18T19:00:00",
    },
]

DEMO_REQUEST_LOGS = [
    {
        "route": "http://localhost:8000/ops/dashboard",
        "request_json": None,
        "response_json": {"status": 200},
        "created_at": "2025-09-18T06:15:00",
    },
    {
        "route": "http://localhost:8000/rag/query",
        "request_json": {"question": "How do we prep IV sedation?", "k": 3},
        "response_json": {"status": 200},
        "created_at": "2025-09-18T06:17:00",
    },
    {
        "route": "http://localhost:8000/ops/generated-tasks",
        "request_json": None,
        "response_json": {"status": 200},
        "created_at": "2025-09-18T06:20:00",
    },
]


def _collect_texts(directories: Iterable[Path]) -> list[str]:
    texts: list[str] = []
    for directory in directories:
        if not directory.exists():
            continue
        for file_path in directory.rglob("*"):
            if file_path.suffix.lower() in SUPPORTED_EXTS and file_path.is_file():
                texts.append(file_path.read_text(encoding="utf-8"))
    return texts


async def _ensure_rag_pipeline() -> None:
    pipeline = get_rag_pipeline()
    await pipeline.ensure_collection()
    texts = _collect_texts(DOC_DIRS)
    if texts:
        await pipeline.ingest_texts(texts)


def _parse_iso(ts: str) -> datetime:
    value = datetime.fromisoformat(ts)
    if value.tzinfo is None:
        return value
    return value.astimezone(None).replace(tzinfo=None)


def _seed_database() -> None:
    conn = get_conn()
    cur = conn.cursor()

    for task in DEMO_GENERATED_TASKS:
        cur.execute(
            "SELECT 1 FROM ops_generated_tasks WHERE task = %s AND patient_name = %s",
            (task["task"], task["patient_name"]),
        )
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO ops_generated_tasks (patient_name, task, owner, due_at) VALUES (%s, %s, %s, %s)",
            (
                task["patient_name"],
                task["task"],
                task["owner"],
                _parse_iso(task["due_at"]),
            ),
        )

    for log in DEMO_REQUEST_LOGS:
        cur.execute(
            "SELECT 1 FROM api_logs WHERE route = %s AND created_at = %s",
            (log["route"], _parse_iso(log["created_at"])),
        )
        if cur.fetchone():
            continue
        cur.execute(
            "INSERT INTO api_logs (route, request_json, response_json, created_at) VALUES (%s, %s, %s, %s)",
            (
                log["route"],
                json.dumps(log["request_json"]) if log["request_json"] is not None else None,
                json.dumps(log["response_json"]) if log["response_json"] is not None else None,
                _parse_iso(log["created_at"]),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


async def main() -> None:
    await _ensure_rag_pipeline()
    _seed_database()
    print("Offline demo bootstrap complete: RAG collection ready and Postgres seeded.")


if __name__ == "__main__":
    asyncio.run(main())
