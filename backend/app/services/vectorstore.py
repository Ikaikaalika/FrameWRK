from typing import List, Any, Dict
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from qdrant_client.http.exceptions import UnexpectedResponse
import numpy as np

logger = logging.getLogger("rag.vectorstore")

class VectorStore:
    def __init__(self, url: str, collection: str):
        self.client = QdrantClient(url=url)
        self.collection = collection

    async def ensure_collection(self, dim: int):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            logger.info("creating qdrant collection %s | dim=%d", self.collection, dim)
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE)
            )
        else:
            logger.debug("qdrant collection %s already exists", self.collection)

    async def upsert_texts(self, texts: List[str], embeddings: np.ndarray):
        points = []
        for i, text in enumerate(texts):
            payload: Dict[str, Any] = {"text": text}
            payload.update(self._extract_metadata(text))
            points.append(PointStruct(id=i, vector=embeddings[i].tolist(), payload=payload))
        logger.debug("upserting %d vectors into %s", len(points), self.collection)
        self.client.upsert(collection_name=self.collection, points=points)

    async def search(self, query_vec: np.ndarray, k: int = 5) -> List[Any]:
        try:
            res = self.client.search(
                collection_name=self.collection,
                query_vector=query_vec.tolist(),
                limit=k,
                with_payload=True,
            )
            logger.debug("qdrant search returned %d hits", len(res))
            return res
        except UnexpectedResponse as exc:
            if exc.status_code == 404:
                logger.warning("qdrant collection %s missing during search", self.collection)
                return []
            raise

    def _extract_metadata(self, text: str) -> Dict[str, Any]:
        metadata: Dict[str, Any] = {}
        for line in text.splitlines():
            if not line.strip():
                break
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            normalized = key.strip().lower()
            value = value.strip()
            match normalized:
                case "title":
                    metadata["title"] = value
                case "location":
                    metadata["location"] = value
                case "procedure stage":
                    metadata["procedure_stage"] = value
                case "risk level":
                    metadata["risk_level"] = value
        if metadata:
            logger.debug("extracted metadata %s", metadata)
        return metadata
