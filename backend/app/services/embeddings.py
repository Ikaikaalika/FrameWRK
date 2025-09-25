import os
import logging
from collections import Counter
import httpx
import numpy as np
from typing import List

logger = logging.getLogger("rag.embeddings")

class EmbeddingsService:
    def __init__(self, provider: str, model: str, openai_key: str | None, ollama_base: str):
        self.provider = provider
        self.model = model
        self.openai_key = openai_key
        self.ollama_base = ollama_base.rstrip("/")

    async def embed(self, texts: List[str]) -> np.ndarray:
        logger.debug("embedding %d texts using provider=%s", len(texts), self.provider)
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
                    embeddings = np.array([item["embedding"] for item in data["data"]], dtype="float32")
                    logger.debug("openai embedding success | dim=%d", embeddings.shape[1])
                    return embeddings
            except httpx.HTTPError as exc:
                logger.warning("openai embedding failed, falling back to ollama/hash: %s", exc)

        # Try Ollama (works great on macOS) and fall back to a deterministic hashing embed if it's unavailable.
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                model = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
                vectors: list[list[float]] = []
                for text in texts:
                    r = await client.post(
                        f"{self.ollama_base}/api/embeddings",
                        json={
                            "model": model,
                            "prompt": text
                        }
                    )
                    r.raise_for_status()
                    data = r.json()
                    vec = data.get("embedding") or (data.get("embeddings") or [])[0]
                    if vec is None:
                        raise ValueError("ollama embeddings response missing vector")
                    vectors.append(vec)
                embeddings = np.array(vectors, dtype="float32")
                logger.debug("ollama embedding success | dim=%d", embeddings.shape[1])
                return embeddings
        except httpx.HTTPError as exc:
            logger.warning("ollama embedding failed, using hash fallback: %s", exc)
            return self._hash_embed(texts)

    def _hash_embed(self, texts: List[str], dim: int = 768) -> np.ndarray:
        """Produce deterministic bag-of-words embeddings as an offline fallback."""
        logger.debug("hash embedding fallback | texts=%d | dim=%d", len(texts), dim)
        vectors = np.zeros((len(texts), dim), dtype="float32")
        for i, text in enumerate(texts):
            counts = Counter(text.lower().split())
            for token, freq in counts.items():
                vectors[i, hash(token) % dim] += freq
            norm = np.linalg.norm(vectors[i])
            if norm:
                vectors[i] /= norm
        return vectors
