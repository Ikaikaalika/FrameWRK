from fastapi import APIRouter, Depends
from ..models.schemas import ClassifyRequest, ClassifyResponse, SummarizeRequest, SummarizeResponse
from ..services.llm_provider import LLMProvider
from ..deps import get_llm_provider

router = APIRouter(prefix="/llm")

@router.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest, llm: LLMProvider = Depends(get_llm_provider)):
    prompt = f"Classify the following text into one of the labels: {req.labels}\nText: {req.text}\nReturn JSON with 'label' and per-label 'scores' (probabilities summing to 1)."
    out = await llm.complete_json(prompt, schema={
        "type": "object",
        "properties": {"label": {"type":"string"}, "scores": {"type":"object"}},
        "required":["label","scores"]
    })
    return ClassifyResponse(label=out.get("label","unknown"), scores=out.get("scores", {}))

@router.post("/summarize", response_model=SummarizeResponse)
async def summarize(req: SummarizeRequest, llm: LLMProvider = Depends(get_llm_provider)):
    prompt = f"Summarize clearly and concisely (no more than {req.max_tokens} tokens):\n\n{req.text}"
    out = await llm.complete_text(prompt, max_tokens=req.max_tokens)
    return SummarizeResponse(summary=out.strip())
