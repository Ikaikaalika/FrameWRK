import os, json, httpx
from typing import Any
from .llm_provider import LLMProvider

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.model = os.getenv("ANTHROPIC_MODEL","claude-3-5-sonnet-latest")

    async def complete_text(self, prompt: str, max_tokens: int = 256) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.base_url}/v1/messages",
                headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01"},
                json={"model": self.model, "max_tokens": max_tokens, "messages": [{"role":"user","content":prompt}], "temperature": 0.2}
            )
            r.raise_for_status()
            data = r.json()
            return "".join([blk["text"] for blk in data["content"] if blk["type"]=="text"])

    async def complete_json(self, prompt: str, schema: dict, max_tokens: int = 512) -> dict[str, Any]:
        sys = "Return a JSON object ONLY that validates the provided JSON Schema."
        txt = await self.complete_text(f"{sys}\nSchema:\n{json.dumps(schema)}\nUser:\n{prompt}", max_tokens=max_tokens)
        try:
            return json.loads(txt)
        except Exception:
            return {}
