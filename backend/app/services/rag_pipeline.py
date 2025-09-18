import numpy as np
import logging
from typing import List, Tuple
from .embeddings import EmbeddingsService
from .vectorstore import VectorStore
from .llm_provider import LLMProvider

logger = logging.getLogger("rag.pipeline")

class RAGPipeline:
    def __init__(self, embeddings: EmbeddingsService, store: VectorStore, llm: LLMProvider):
        self.embeddings = embeddings
        self.store = store
        self.llm = llm
        self._dim = None

    async def ensure_collection(self):
        vec = await self.embeddings.embed(["ping"])
        self._dim = vec.shape[1]
        logger.debug("ensuring vector collection with dim=%d", self._dim)
        await self.store.ensure_collection(self._dim)

    async def ingest_texts(self, texts: List[str]) -> int:
        logger.info("ingesting %d documents into RAG pipeline", len(texts))
        vecs = await self.embeddings.embed(texts)
        await self.store.upsert_texts(texts, vecs)
        logger.debug("ingestion complete")
        return len(texts)

    async def query(self, question: str, k: int = 5):
        logger.info("query received | question='%s' | k=%d", question, k)
        qvec = await self.embeddings.embed([question])
        results = await self.store.search(qvec[0], k=k)
        logger.debug("retrieved %d context chunks", len(results))
        context = "\n\n".join([f"- {r.payload.get('text','')}" for r in results])
        prompt = f"You are a helpful assistant. Use the context to answer. If unknown, say you don't know.\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        answer = await self.llm.complete_text(prompt, max_tokens=256)
        logger.debug("LLM answered query | chars=%d", len(answer))
        return answer, results
