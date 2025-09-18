import json
import re
import httpx
from typing import Any
from .llm_provider import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete_text(self, prompt: str, max_tokens: int = 256) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": 0.2},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return data.get("response", "")
        except Exception:
            return self._fallback_text(prompt, max_tokens)

    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512) -> dict[str, Any]:
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\nReturn valid minified JSON only.",
            "stream": False,
            "format": "json",
            "options": {"num_predict": max_tokens, "temperature": 0.0},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                r = await client.post(f"{self.base_url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                content = data.get("response", "{}").strip()
                parsed = json.loads(content or "{}")
                if isinstance(parsed, dict):
                    label = parsed.get("label")
                    scores = parsed.get("scores")
                    if label and (not isinstance(scores, dict) or not scores):
                        parsed["scores"] = self._scores_from_prompt(prompt, label)
                return parsed
        except Exception:
            return self._fallback_json(prompt)

    def _fallback_text(self, prompt: str, max_tokens: int) -> str:
        if "Context:" in prompt and "Question:" in prompt:
            context_part = prompt.split("Context:", 1)[1].split("Question:", 1)[0]
            snippets = [ln.strip("- ") for ln in context_part.splitlines() if ln.strip()]
            if snippets:
                answer = " ".join(snippets)[: max_tokens * 4]
                return f"Based on the context: {answer}".strip()
        if "Summarize" in prompt:
            body = prompt.splitlines()[-1]
            sentences = re.split(r"(?<=[.!?])\s+", body)
            return " ".join(sentences[:2])[: max_tokens * 4]
        return prompt[: max_tokens * 4]

    def _fallback_json(self, prompt: str) -> dict[str, Any]:
        labels = []
        text = ""
        if "labels:" in prompt:
            after = prompt.split("labels:", 1)[1]
            raw = after.split("\n", 1)[0].strip().strip("[]")
            labels = [lbl.strip().strip("'\"") for lbl in raw.split(",") if lbl.strip()]
        if "Text:" in prompt:
            after = prompt.split("Text:", 1)[1]
            text = after.split("\n", 1)[0].strip()
        if not labels:
            labels = ["unknown"]
        words = re.findall(r"\w+", text.lower())
        scores = {}
        for label in labels:
            key = label.lower()
            scores[label] = max(words.count(key), 0) + 1.0
        total = sum(scores.values()) or len(labels)
        scores = {label: val / total for label, val in scores.items()}
        top = max(scores, key=scores.get)
        return {"label": top, "scores": scores}

    def _scores_from_prompt(self, prompt: str, chosen: str) -> dict[str, float]:
        labels = []
        if "labels:" in prompt:
            after = prompt.split("labels:", 1)[1]
            raw = after.split("\n", 1)[0].strip().strip("[]")
            labels = [lbl.strip().strip("'\"") for lbl in raw.split(",") if lbl.strip()]
        if not labels:
            labels = [chosen]
        base = {label: 0.0 for label in labels}
        if chosen in base:
            base[chosen] = 1.0
        elif labels:
            base[labels[0]] = 1.0
        return base
