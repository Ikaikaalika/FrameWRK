import os, httpx, numpy as np
from typing import List

class EmbeddingsService:
    def __init__(self, provider: str, model: str, openai_key: str | None, ollama_base: str):
        self.provider = provider
        self.model = model
        self.openai_key = openai_key
        self.ollama_base = ollama_base.rstrip("/")

    async def embed(self, texts: List[str]) -> np.ndarray:
        if self.provider == "openai" and self.openai_key:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post("https://api.openai.com/v1/embeddings",
                    headers={"Authorization": f"Bearer {self.openai_key}"},
                    json={"model": self.model, "input": texts}
                )
                r.raise_for_status()
                data = r.json()
                return np.array([item["embedding"] for item in data["data"]], dtype="float32")
        # fallback: ollama embeddings via /api/embeddings
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{self.ollama_base}/api/embeddings",
                json={"model": os.getenv("OLLAMA_EMBED_MODEL","nomic-embed-text"), "prompt": texts if len(texts)>1 else texts[0]}
            )
            r.raise_for_status()
            data = r.json()
            vecs = data.get("embeddings") or [data.get("embedding")]
            return np.array(vecs, dtype="float32")
