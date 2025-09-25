import json
import logging
from typing import Any, Dict, List

from psycopg2.extras import Json

from .rag_pipeline import RAGPipeline
from .llm_provider import LLMProvider
from ..storage.db import get_conn

logger = logging.getLogger("ops.automation")


class AutomationService:
    def __init__(self, rag: RAGPipeline, llm: LLMProvider):
        self.rag = rag
        self.llm = llm

    async def suggest(self, focus: str, count: int = 3) -> List[Dict[str, Any]]:
        question = (
            f"Identify automation opportunities that would improve {focus} workflows"
        )
        _, results = await self.rag.query(question, k=max(5, count + 2))
        context_chunks = [r.payload.get("text", "") for r in results if r.payload.get("text")]
        context = "\n\n---\n\n".join(context_chunks)
        prompt = (
            "You are the automation architect for Nuvia Smiles' operations team."
            " Use the provided context to propose concrete automations that reduce"
            " manual effort, improve visibility, or cut failure rates. Focus area:"
            f" {focus}. Return JSON with a 'suggestions' array containing {count}"
            " items. Each item must include: title, problem, automation, impact,"
            " and confidence (high/medium/low). Keep titles concise."
            "\n\nContext:\n"
            f"{context if context else 'No additional context provided.'}"
        )
        schema = {
            "type": "object",
            "properties": {
                "suggestions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "problem": {"type": "string"},
                            "automation": {"type": "string"},
                            "impact": {"type": "string"},
                            "confidence": {"type": "string"},
                        },
                        "required": ["title", "problem", "automation", "impact"],
                    },
                }
            },
            "required": ["suggestions"],
        }
        try:
            data = await self.llm.complete_json(prompt, schema=schema, max_tokens=512)
            candidates = data.get("suggestions", []) if isinstance(data, dict) else []
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Automation suggestion JSON generation failed: %s", exc)
            candidates = []

        suggestions: List[Dict[str, Any]] = []
        for item in candidates:
            suggestions.append(
                {
                    "title": item.get("title", "Automation Idea"),
                    "problem": item.get("problem", ""),
                    "automation": item.get("automation", ""),
                    "impact": item.get("impact", ""),
                    "confidence": item.get("confidence", "medium").lower(),
                }
            )
        if not suggestions:
            logger.info("Falling back to generic automation suggestions for focus=%s", focus)
            suggestions = [
                {
                    "title": f"Automation for {focus.title()}",
                    "problem": f"Manual effort remains high for {focus} workflows.",
                    "automation": "Introduce workflow triggers that auto-generate tasks and notifications based on runbook templates.",
                    "impact": "Reduces coordinator load and improves handoff speed.",
                    "confidence": "medium",
                }
            ]
        return suggestions[:count]

    async def implement(self, suggestion: Dict[str, Any]) -> Dict[str, Any]:
        prompt = (
            "You are an AI automation engineer. Given the approved automation idea"
            " below, produce a concrete implementation plan that a devops team can"
            " execute. Use components available in this stack (FastAPI, Qdrant,"
            " Postgres, Next.js, Ollama/OpenAI). Return JSON with: title, summary,"
            " plan_steps (array of step descriptions), integrations (array of"
            " systems touched), monitoring (array of metrics or alerts), and"
            " rollout_notes (string)."
            "\n\nAutomation Idea (JSON):\n"
            f"{json.dumps(suggestion)}"
        )
        schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "summary": {"type": "string"},
                "plan_steps": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "integrations": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "monitoring": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "rollout_notes": {"type": "string"},
            },
            "required": ["title", "summary", "plan_steps"],
        }
        try:
            plan = await self.llm.complete_json(prompt, schema=schema, max_tokens=600)
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Automation implementation JSON generation failed: %s", exc)
            plan = {
                "title": suggestion.get("title", "Automation Blueprint"),
                "summary": suggestion.get("automation", ""),
                "plan_steps": [
                    "Design workflow schema.",
                    "Implement FastAPI endpoint for automation triggers.",
                    "Schedule background job to interact with Qdrant/Postgres.",
                    "Add monitoring hooks and dashboard widgets.",
                ],
                "integrations": ["FastAPI", "Postgres"],
                "monitoring": ["Task creation latency", "Error rate"],
                "rollout_notes": "Fallback plan generated without LLM context.",
            }

        record = self._record_blueprint(plan)
        return record

    def _record_blueprint(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO ops_automation_blueprints (title, summary, implementation_plan) "
            "VALUES (%s, %s, %s) RETURNING id, status, created_at",
            (
                plan.get("title", "Automation Blueprint"),
                plan.get("summary", ""),
                Json(plan),
            ),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {
            "id": row[0],
            "title": plan.get("title", "Automation Blueprint"),
            "status": row[1],
            "implementation_plan": plan,
            "created_at": row[2].isoformat() if row[2] else None,
        }
