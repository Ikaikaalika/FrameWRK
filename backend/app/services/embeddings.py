import os
from collections import Counter
import httpx
import numpy as np
from typing import List

class EmbeddingsService:
    def __init__(self, provider: str, model: str, openai_key: str | None, ollama_base: str):
        self.provider = provider
        self.model = model
        self.openai_key = openai_key
        self.ollama_base = ollama_base.rstrip("/")

    async def embed(self, texts: List[str]) -> np.ndarray:
        if self.provider == "openai" and self.openai_key:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    r = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {self.openai_key}"},
                        json={"model": self.model, "input": texts}
                    )
                    r.raise_for_status()
                    data = r.json()
                    return np.array([item["embedding"] for item in data["data"]], dtype="float32")
            except httpx.HTTPError:
                pass

        # Try Ollama (works great on macOS) and fall back to a deterministic hashing embed if it's unavailable.
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.post(
                    f"{self.ollama_base}/api/embeddings",
                    json={
                        "model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
                        "prompt": texts if len(texts) > 1 else texts[0]
                    }
                )
                r.raise_for_status()
                data = r.json()
                vecs = data.get("embeddings") or [data.get("embedding")]
                return np.array(vecs, dtype="float32")
        except httpx.HTTPError:
            return self._hash_embed(texts)

    def _hash_embed(self, texts: List[str], dim: int = 256) -> np.ndarray:
        """Produce deterministic bag-of-words embeddings as an offline fallback."""
        vectors = np.zeros((len(texts), dim), dtype="float32")
        for i, text in enumerate(texts):
            counts = Counter(text.lower().split())
            for token, freq in counts.items():
                vectors[i, hash(token) % dim] += freq
            norm = np.linalg.norm(vectors[i])
            if norm:
                vectors[i] /= norm
        return vectors
