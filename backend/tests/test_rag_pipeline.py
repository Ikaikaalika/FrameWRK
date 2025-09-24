import numpy as np
import pytest
from types import SimpleNamespace

from app.services.rag_pipeline import RAGPipeline


class StubEmbeddings:
    def __init__(self):
        self.calls = []
        self.responses = {}

    def set_response(self, texts, array):
        self.responses[tuple(texts)] = array

    async def embed(self, texts):
        key = tuple(texts)
        self.calls.append(key)
        if key in self.responses:
            return self.responses[key]
        # default deterministic shape based on length
        return np.ones((len(texts), 3), dtype="float32")


class StubStore:
    def __init__(self):
        self.ensure_dims = []
        self.ingested = []
        self.search_results = []

    async def ensure_collection(self, dim):
        self.ensure_dims.append(dim)

    async def upsert_texts(self, texts, embeddings):
        self.ingested.append((texts, embeddings))

    async def search(self, query_vec, k):
        self.last_search = {"query_vec": query_vec.tolist(), "k": k}
        return self.search_results


class StubLLM:
    def __init__(self, response="Stub answer"):
        self.response = response
        self.calls = []

    async def complete_text(self, prompt, max_tokens=256):
        self.calls.append({"prompt": prompt, "max_tokens": max_tokens})
        return self.response

    async def complete_json(self, prompt, schema, max_tokens=512):
        raise NotImplementedError


@pytest.mark.asyncio
async def test_ensure_collection_uses_embedding_dimension():
    embeddings = StubEmbeddings()
    embeddings.set_response(("ping",), np.ones((1, 5), dtype="float32"))
    store = StubStore()
    llm = StubLLM()
    pipeline = RAGPipeline(embeddings=embeddings, store=store, llm=llm)

    await pipeline.ensure_collection()

    assert store.ensure_dims == [5]
    assert embeddings.calls[0] == ("ping",)


@pytest.mark.asyncio
async def test_ingest_texts_embeds_and_persists():
    embeddings = StubEmbeddings()
    embeddings.set_response(("doc1", "doc2"), np.array([[1, 0, 0], [0, 1, 0]], dtype="float32"))
    store = StubStore()
    llm = StubLLM()
    pipeline = RAGPipeline(embeddings=embeddings, store=store, llm=llm)

    count = await pipeline.ingest_texts(["doc1", "doc2"])

    assert count == 2
    assert len(store.ingested) == 1
    texts, vecs = store.ingested[0]
    assert list(texts) == ["doc1", "doc2"]
    assert vecs.shape == (2, 3)


@pytest.mark.asyncio
async def test_query_ranks_snippets_by_keyword_match():
    embeddings = StubEmbeddings()
    embeddings.set_response(("What sedation protocols ensure inventory readiness?",), np.array([[0.1, 0.2, 0.3]], dtype="float32"))
    store = StubStore()
    store.search_results = [
        SimpleNamespace(
            payload={
                "title": "Sedation Safety",
                "location": "Salt Lake City",
                "procedure_stage": "Pre-Op",
                "risk_level": "High",
                "text": "Sedation protocols require sedation review and inventory readiness checks.",
            },
            score=0.82,
        ),
        SimpleNamespace(
            payload={
                "title": "Inventory Tracking",
                "text": "Inventory levels and reorder points overview.",
            },
            score=0.75,
        ),
    ]
    llm = StubLLM(response="All good")
    pipeline = RAGPipeline(embeddings=embeddings, store=store, llm=llm)

    answer, results = await pipeline.query("What sedation protocols ensure inventory readiness?", k=2)

    assert answer == "All good"
    assert results == store.search_results
    assert store.last_search["k"] == 2

    prompt = llm.calls[0]["prompt"]
    context_section = prompt.split("Context:\n", 1)[1]
    snippet_block = context_section.split("\n\nQuestion:", 1)[0]
    assert "Snippet 1" in snippet_block
    assert "Sedation protocols require" in snippet_block
    assert snippet_block.index("Sedation protocols") < snippet_block.index("Inventory levels")
