import numpy as np
import pytest
from types import SimpleNamespace
import httpx

from app.services.vectorstore import VectorStore
from qdrant_client.http.exceptions import UnexpectedResponse


@pytest.mark.asyncio
async def test_ensure_collection_creates_when_missing():
    store = VectorStore(url="http://test", collection="demo")

    created = {}

    class FakeClient:
        def get_collections(self):
            return SimpleNamespace(collections=[SimpleNamespace(name="other")])

        def create_collection(self, collection_name, vectors_config):
            created["collection"] = collection_name
            created["size"] = vectors_config.size

    store.client = FakeClient()
    await store.ensure_collection(384)

    assert created == {"collection": "demo", "size": 384}


@pytest.mark.asyncio
async def test_ensure_collection_skips_when_exists():
    store = VectorStore(url="http://test", collection="demo")

    class FakeClient:
        def __init__(self):
            self.created = False

        def get_collections(self):
            return SimpleNamespace(collections=[SimpleNamespace(name="demo")])

        def create_collection(self, *args, **kwargs):
            self.created = True

    fake = FakeClient()
    store.client = fake
    await store.ensure_collection(256)

    assert fake.created is False


@pytest.mark.asyncio
async def test_upsert_adds_metadata_from_text():
    store = VectorStore(url="http://test", collection="demo")

    captured = {}

    class FakeClient:
        def upsert(self, collection_name, points):
            captured["collection_name"] = collection_name
            captured["points"] = points

    store.client = FakeClient()

    texts = [
        "Title: Sedation Checklist\nLocation: Salt Lake City\nProcedure Stage: Pre-Op\nRisk Level: High\n\nEnsure monitors are calibrated.",
        "Simple note without metadata"
    ]
    embeddings = np.ones((2, 4), dtype="float32")

    await store.upsert_texts(texts, embeddings)

    assert captured["collection_name"] == "demo"
    assert captured["points"][0].payload["title"] == "Sedation Checklist"
    assert captured["points"][0].payload["location"] == "Salt Lake City"
    assert captured["points"][0].payload["procedure_stage"] == "Pre-Op"
    assert captured["points"][0].payload["risk_level"] == "High"
    assert captured["points"][1].payload == {"text": "Simple note without metadata"}


@pytest.mark.asyncio
async def test_search_returns_empty_on_missing_collection():
    store = VectorStore(url="http://test", collection="demo")

    class FakeClient:
        def search(self, *args, **kwargs):
            raise UnexpectedResponse(404, "Not Found", b"", httpx.Headers())

    store.client = FakeClient()

    results = await store.search(np.zeros(4, dtype="float32"), k=3)

    assert results == []
