import json, httpx
from typing import Any
from .llm_provider import LLMProvider

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://ollama:11434", model: str = "llama3.1"):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete_text(self, prompt: str, max_tokens: int = 256) -> str:
        payload = {"model": self.model, "prompt": prompt, "options": {"num_predict": max_tokens, "temperature": 0.2}}
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(f"{self.base_url}/api/generate", json=payload)
            r.raise_for_status()
            text = ""
            for line in r.text.splitlines():
                try:
                    obj = json.loads(line)
                    text += obj.get("response","")
                except Exception:
                    pass
            return text

    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512) -> dict[str, Any]:
        sys = "Return only valid minified JSON for the user's request."
        txt = await self.complete_text(f"{sys}\n{prompt}", max_tokens=max_tokens)
        try:
            return json.loads(txt.strip())
        except Exception:
            return {}
