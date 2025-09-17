from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List
from ..services.rag_pipeline import RAGPipeline
from ..deps import get_rag_pipeline

router = APIRouter(prefix="/rag")

class ChatTurn(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    history: List[ChatTurn] = []
    question: str
    k: int = 5

@router.post("/chat")
async def rag_chat(req: ChatRequest, rag: RAGPipeline = Depends(get_rag_pipeline)):
    history_text = "\n".join([f"{t.role}: {t.content}" for t in req.history][-8:])
    q = req.question
    answer, results = await rag.query(f"{history_text}\nuser: {q}", k=req.k)
    return {"answer": answer, "sources": [r.payload.get("text","") for r in results]}
