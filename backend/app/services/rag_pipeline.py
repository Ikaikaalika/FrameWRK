import numpy as np
from typing import List, Tuple
from .embeddings import EmbeddingsService
from .vectorstore import VectorStore
from .llm_provider import LLMProvider

class RAGPipeline:
    def __init__(self, embeddings: EmbeddingsService, store: VectorStore, llm: LLMProvider):
        self.embeddings = embeddings
        self.store = store
        self.llm = llm
        self._dim = None

    async def ensure_collection(self):
        vec = await self.embeddings.embed(["ping"])
        self._dim = vec.shape[1]
        await self.store.ensure_collection(self._dim)

    async def ingest_texts(self, texts: List[str]) -> int:
        vecs = await self.embeddings.embed(texts)
        await self.store.upsert_texts(texts, vecs)
        return len(texts)

    async def query(self, question: str, k: int = 5):
        qvec = await self.embeddings.embed([question])
        results = await self.store.search(qvec[0], k=k)
        context = "\n\n".join([f"- {r.payload.get('text','')}" for r in results])
        prompt = f"You are a helpful assistant. Use the context to answer. If unknown, say you don't know.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        answer = await self.llm.complete_text(prompt, max_tokens=256)
        return answer, results
