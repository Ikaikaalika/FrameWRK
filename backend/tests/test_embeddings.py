import numpy as np
import pytest
import httpx

from app.services.embeddings import EmbeddingsService


class FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=None)

    def json(self):
        return self._json


class FakeAsyncClient:
    def __init__(self, responses):
        self._responses = responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, *args, **kwargs):
        if not self._responses:
            raise AssertionError("Unexpected HTTP call")
        next_response = self._responses.pop(0)
        if isinstance(next_response, Exception):
            raise next_response
        return next_response


class ClientFactory:
    def __init__(self, context_responses):
        self._contexts = context_responses

    def __call__(self, *args, **kwargs):
        responses = self._contexts.pop(0)
        return FakeAsyncClient(list(responses))


@pytest.mark.asyncio
async def test_embed_uses_openai_when_available(monkeypatch):
    responses = ClientFactory([
        [
            FakeResponse({
                "data": [
                    {"embedding": [0.1, 0.2, 0.3]},
                    {"embedding": [0.4, 0.5, 0.6]},
                ]
            })
        ]
    ])
    monkeypatch.setattr("httpx.AsyncClient", responses)

    svc = EmbeddingsService(provider="openai", model="text-embedding", openai_key="test", ollama_base="http://ollama")
    texts = ["doc one", "doc two"]
    vecs = await svc.embed(texts)

    assert vecs.shape == (2, 3)
    assert np.allclose(vecs[0], np.array([0.1, 0.2, 0.3], dtype="float32"))


@pytest.mark.asyncio
async def test_embed_falls_back_to_hash_when_providers_fail(monkeypatch):
    responses = ClientFactory([
        [httpx.HTTPError("openai boom")],
        [httpx.HTTPError("ollama boom")],
    ])
    monkeypatch.setattr("httpx.AsyncClient", responses)

    svc = EmbeddingsService(provider="openai", model="text-embedding", openai_key="test", ollama_base="http://ollama")
    texts = ["Sedation kit ready", "Inventory low"]
    vecs = await svc.embed(texts)

    assert vecs.shape == (2, 768)
    norms = np.linalg.norm(vecs, axis=1)
    assert pytest.approx(norms[0], rel=1e-6) == 1.0
    assert pytest.approx(norms[1], rel=1e-6) == 1.0


def test_hash_embed_is_deterministic():
    svc = EmbeddingsService(provider="hash", model="na", openai_key=None, ollama_base="http://ollama")
    a = svc._hash_embed(["Sedation follow-up call"], dim=32)
    b = svc._hash_embed(["Sedation follow-up call"], dim=32)
    assert np.allclose(a, b)
    assert a.shape == (1, 32)
