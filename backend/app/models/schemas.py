from pydantic import BaseModel, Field
from typing import List, Optional

class HealthResponse(BaseModel):
    status: str

class ClassifyRequest(BaseModel):
    text: str
    labels: List[str]

class ClassifyResponse(BaseModel):
    label: str
    scores: dict

class SummarizeRequest(BaseModel):
    text: str
    max_tokens: int = 150

class SummarizeResponse(BaseModel):
    summary: str

class IngestRequest(BaseModel):
    texts: List[str]

class QueryRequest(BaseModel):
    question: str
    k: int = Field(default=5, ge=1, le=20)

class QueryResponseChunk(BaseModel):
    text: str
    score: float

class QueryResponse(BaseModel):
    answer: str
    chunks: List[QueryResponseChunk]
