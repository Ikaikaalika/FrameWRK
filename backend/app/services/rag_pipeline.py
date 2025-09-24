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
        keywords = {token for token in question.lower().split() if len(token) > 3}
        snippet_bundle = []
        for r in results:
            meta_bits = []
            if title := r.payload.get("title"):
                meta_bits.append(f"Title: {title}")
            if location := r.payload.get("location"):
                meta_bits.append(f"Location: {location}")
            if stage := r.payload.get("procedure_stage"):
                meta_bits.append(f"Stage: {stage}")
            if risk := r.payload.get("risk_level"):
                meta_bits.append(f"Risk: {risk}")
            header = " | ".join(meta_bits)
            text = r.payload.get("text", "")
            snippet_text = f"{header}\n{text}" if header else text
            lower_text = snippet_text.lower()
            match_score = sum(1 for kw in keywords if kw in lower_text)
            snippet_bundle.append((match_score, snippet_text))

        snippet_bundle.sort(key=lambda item: item[0], reverse=True)
        snippets = [f"Snippet {idx + 1} (score={score}):\n{text}" for idx, (score, text) in enumerate(snippet_bundle)]
        context = "\n\n".join(snippets)
        prompt = (
            "You are Nuvia Smiles' operations co-pilot. Respond using only the provided context. "
            "If at least one context snippet is provided, craft the best grounded summary you can. "
            "Only respond with 'I don't know' when the context list is empty. "
            "Prefer concise checklists with numbered steps when listing actions, and highlight sedation or inventory risks explicitly."
            "Always prioritize information from Snippet 1 unless it is irrelevant."
            "\n\nContext:\n{context}\n\nQuestion: {question}\nAnswer:"
        ).format(context=context, question=question)
        answer = await self.llm.complete_text(prompt, max_tokens=256)
        logger.debug("LLM answered query | chars=%d", len(answer))
        return answer, results
