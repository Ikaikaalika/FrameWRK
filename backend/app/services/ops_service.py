from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from .llm_provider import LLMProvider
from ..storage.db import get_conn

logger = logging.getLogger("ops.service")

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nuvia_ops.json"


@dataclass
class OpsService:
    """Utility service to provide operational intel for the demo."""

    data: Dict[str, Any]

    @classmethod
    def from_file(cls, path: Path = DATA_PATH) -> "OpsService":
        with path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return cls(data=payload)

    def dashboard(self) -> Dict[str, Any]:
        locations: List[Dict[str, Any]] = self.data.get("locations", [])
        schedule: List[Dict[str, Any]] = self.data.get("schedule", [])
        tasks: List[Dict[str, Any]] = self.data.get("tasks", [])
        inventory: List[Dict[str, Any]] = self.data.get("inventory_alerts", [])
        followups: List[Dict[str, Any]] = self.data.get("followups", [])
        sedation_trend: List[Dict[str, Any]] = self.data.get("sedation_trend", [])

        total_surgeries = sum(loc.get("surgeries_today", 0) for loc in locations)
        total_sedation = sum(loc.get("sedation_cases", 0) for loc in locations)
        at_risk_centers = [loc for loc in locations if loc.get("status") == "at-risk"]

        return {
            "meta": {
                "total_surgeries": total_surgeries,
                "total_sedation_cases": total_sedation,
                "at_risk_centers": len(at_risk_centers),
                "open_tasks": len(tasks),
            },
            "locations": locations,
            "schedule": sorted(schedule, key=lambda item: item.get("start", "")),
            "tasks": tasks,
            "inventory_alerts": inventory,
            "followups": followups,
            "sedation_trend": sedation_trend,
        }

    async def generate_checklist(self, payload: Dict[str, Any], llm: LLMProvider) -> Dict[str, Any]:
        prompt = (
            "You are the regional operations director for Nuvia Smiles. "
            "Create a concise, ordered pre-op checklist for the upcoming procedure using the details provided. "
            "Group steps as numbered items, include clinical, lab, and patient communication tasks, and finish with a short follow-up section. "
            "Respond in plain text with bullet points."
        )
        case_context = (
            f"Procedure: {payload['procedure']}\n"
            f"Location: {payload['location']}\n"
            f"Patient: {payload['patient_name']}\n"
            f"Sedation: {payload['sedation']}\n"
            f"Notes: {payload.get('notes', 'None')}"
        )

        try:
            text = await llm.complete_text(f"{prompt}\n\n{case_context}", max_tokens=320)
        except Exception:
            logger.warning("LLM checklist generation failed; using fallback")
            text = self._fallback_checklist(payload)
        else:
            if not text.strip():
                text = self._fallback_checklist(payload)

        checklist_items, follow_up = self._split_checklist(text)
        self._record_generated_tasks(payload, follow_up)

        return {
            "title": f"{payload['procedure']} prep — {payload['patient_name']}",
            "checklist": checklist_items,
            "follow_up": follow_up,
        }

    def generated_tasks(self) -> List[Dict[str, Any]]:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, patient_name, task, owner, due_at, status, created_at"
            " FROM ops_generated_tasks ORDER BY created_at DESC LIMIT 50"
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "id": row[0],
                "patient_name": row[1],
                "task": row[2],
                "owner": row[3],
                "due_at": row[4].isoformat() if row[4] else None,
                "status": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
            })
        return result

    def _fallback_checklist(self, payload: Dict[str, Any]) -> str:
        segments = [
            "1. Confirm CBCT imaging and surgical guides are ready at the operatory.",
            "2. Review medical history and sedation clearance; flag any contraindications.",
            "3. Stage implant kits, torque drivers, and backup abutments.",
            "4. Brief surgical + anesthesia team on patient-specific notes.",
            "5. Call patient to reconfirm fasting instructions and arrival time.",
            "Follow-up: Schedule 48-hour post-op wellness call and ensure pharmacy meds are queued.",
        ]
        return "\n".join(segments)

    def _split_checklist(self, raw: str) -> tuple[List[str], List[str]]:
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        checklist: List[str] = []
        follow_up: List[str] = []
        collecting_follow_up = False
        for line in lines:
            lower = line.lower()
            if "follow" in lower and "up" in lower:
                collecting_follow_up = True
                continue
            cleaned = self._clean_line(line)
            if not cleaned:
                continue
            if collecting_follow_up:
                follow_up.append(cleaned)
            else:
                checklist.append(cleaned)
        if not follow_up:
            follow_up.append("Schedule 48-hour post-op wellness check and document in CRM.")
        return checklist, follow_up

    def _clean_line(self, line: str) -> str:
        stripped = line.strip("- •")
        if stripped.startswith("**") and stripped.endswith("**"):
            return ""
        if ":" in stripped and stripped.lower().split(":", 1)[0] in {"clinical tasks", "lab tasks", "patient communication tasks", "logistical tasks"}:
            return ""
        if stripped and stripped[0].isdigit():
            parts = stripped.split(".", 1)
            if len(parts) == 2:
                stripped = parts[1].strip()
        return stripped

    def _record_generated_tasks(self, payload: Dict[str, Any], follow_up: List[str]) -> None:
        try:
            conn = get_conn()
            cur = conn.cursor()
            owner = f"{payload['location']} Ops"
            due_base = datetime.utcnow() + timedelta(hours=4)
            for idx, item in enumerate(follow_up[:3]):
                due_at = due_base + timedelta(hours=idx)
                cur.execute(
                    "INSERT INTO ops_generated_tasks (patient_name, task, owner, due_at) VALUES (%s,%s,%s,%s)",
                    (payload["patient_name"], item, owner, due_at)
                )
            conn.commit()
            cur.close()
            conn.close()
            logger.info("recorded %d follow-up tasks for %s", min(len(follow_up), 3), payload['patient_name'])
        except Exception as exc:
            logger.warning("failed to record generated tasks: %s", exc)
