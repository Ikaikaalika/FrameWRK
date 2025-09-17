import os, json, httpx
from typing import Any
from .llm_provider import LLMProvider

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = os.getenv("OPENAI_MODEL","gpt-4o-mini")

    async def complete_text(self, prompt: str, max_tokens: int = 256) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages":[{"role":"user","content":prompt}], "max_tokens": max_tokens, "temperature": 0.2}
            )
            r.raise_for_status()
            data = r.json()
            return data["choices"][0]["message"]["content"]

    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "messages":[{"role":"user","content":prompt}], "max_tokens": max_tokens, "temperature": 0.0, "response_format": {"type":"json_object"}}
            )
            r.raise_for_status()
            data = r.json()
            try:
                return json.loads(data["choices"][0]["message"]["content"])
            except Exception:
                return {}
