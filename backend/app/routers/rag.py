from fastapi import APIRouter, Depends
from ..models.schemas import IngestRequest, QueryRequest, QueryResponse, QueryResponseChunk
from ..services.rag_pipeline import RAGPipeline
from ..deps import get_rag_pipeline

router = APIRouter(prefix="/rag")

@router.post("/ingest")
async def ingest(req: IngestRequest, rag: RAGPipeline = Depends(get_rag_pipeline)):
    await rag.ensure_collection()
    count = await rag.ingest_texts(req.texts)
    return {"ingested": count}

@router.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest, rag: RAGPipeline = Depends(get_rag_pipeline)):
    answer, results = await rag.query(req.question, k=req.k)
    return QueryResponse(
        answer=answer,
        chunks=[QueryResponseChunk(text=r.payload.get("text",""), score=r.score) for r in results]
    )
